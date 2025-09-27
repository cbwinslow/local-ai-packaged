"""
Enhanced Agentic Knowledge RAG Graph
A comprehensive FastAPI service that provides advanced knowledge graph and RAG capabilities
"""

import os
import logging
import asyncio
import json
import secrets
import string
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union, Annotated
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import (
    FastAPI, HTTPException, Depends, Query as QueryParam, 
    BackgroundTasks, Request, status, Header, Security
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader, APIKeyQuery, APIKeyCookie
from pydantic import BaseModel, Field, validator
import uvicorn
import httpx
from supabase import create_client, Client as SupabaseClient

# API Key Security
API_KEY_NAME = "X-API-Key"
api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)

# Initialize Supabase client
def get_supabase() -> SupabaseClient:
    """
    Create and return a Supabase client configured from environment variables.
    
    Reads SUPABASE_URL and SUPABASE_SERVICE_KEY from the environment and returns a connected SupabaseClient.
    
    Returns:
        SupabaseClient: A client configured with SUPABASE_URL and SUPABASE_SERVICE_KEY.
    
    Raises:
        RuntimeError: If SUPABASE_URL or SUPABASE_SERVICE_KEY is not set in the environment.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_key:
        raise RuntimeError("Missing Supabase configuration")
    return create_client(supabase_url, supabase_key)

# API Key Validation
async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    api_key_cookie: str = Security(api_key_cookie),
    supabase: SupabaseClient = Depends(get_supabase)
) -> str:
    # Check API key in query params, headers, or cookies
    """
    Validate an API key supplied via query parameter, header, or cookie and return it if it exists and is active.
    
    Parameters:
        api_key_query (str): API key provided as a query parameter.
        api_key_header (str): API key provided in an HTTP header.
        api_key_cookie (str): API key provided in a cookie.
    
    Returns:
        str: The validated API key.
    
    Raises:
        HTTPException: 403 Forbidden if no API key is provided or if the provided key is not found or not active.
    """
    api_key = api_key_query or api_key_header or api_key_cookie
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )
    
    # Verify API key in Supabase
    result = supabase.table('api_keys') \
        .select('*') \
        .eq('key', api_key) \
        .eq('is_active', True) \
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key"
        )
    
    return api_key

# Audit Logging
async def log_audit_event(
    request: Request,
    action: str,
    resource_type: str,
    resource_id: str = None,
    metadata: dict = None,
    user_id: str = None
):
    """
    Record an audit event to the Supabase `audit_logs` table.
    
    Parameters:
        request (Request): Incoming HTTP request used to extract client IP and User-Agent.
        action (str): Action name or verb describing the event (e.g., "create_api_key", "query").
        resource_type (str): Type of resource acted upon (e.g., "api_key", "document").
        resource_id (str, optional): Identifier of the resource related to the event.
        metadata (dict, optional): Arbitrary additional data to store with the event.
        user_id (str, optional): Identifier of the user who performed the action.
    
    Notes:
        - The function persists an audit record with fields for action, resource type/id, metadata,
          client IP, user agent, and user ID.
        - Errors during logging are caught and emitted to the module logger; they are not propagated.
    """
    try:
        # Get client IP and user agent
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent')
        
        # Insert audit log
        supabase = get_supabase()
        supabase.table('audit_logs').insert({
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'metadata': metadata or {},
            'ip_address': client_host,
            'user_agent': user_agent,
            'user_id': user_id
        }).execute()
    except Exception as e:
        logger.error(f"Failed to log audit event: {str(e)}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic Models
class APIKeyCreate(BaseModel):
    name: str
    expires_at: Optional[datetime] = None
    scopes: List[str] = Field(default_factory=list)

class APIKeyResponse(APIKeyCreate):
    key: str
    created_at: datetime
    last_used_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True

class Document(BaseModel):
    id: Optional[str] = None
    content: str
    title: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

class Query(BaseModel):
    text: str
    filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(default=10, ge=1, le=100)
    include_graph_context: bool = True
    use_vector_search: bool = True

class GraphNode(BaseModel):
    id: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    labels: List[str] = Field(default_factory=list)

class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    weight: Optional[float] = None

class RAGResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    graph_context: List[Dict[str, Any]]
    confidence: float
    processing_time: float
    request_id: Optional[str] = None

class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
    services: Dict[str, str]
    version: str = "1.0.0"

# Global variables for connections
connections = {
    "neo4j_driver": None,
    "postgres_conn": None,
    "qdrant_client": None,
    "ollama_client": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Provide a FastAPI lifespan context that initializes external connections on startup and cleans them up on shutdown.
    
    This async context manager awaits initialize_connections() before yielding control to the application, and awaits cleanup_connections() after the application shutdown sequence completes.
    
    Parameters:
        app (FastAPI): The FastAPI application instance for which this lifespan is applied.
    """
    await initialize_connections()
    yield
    await cleanup_connections()

# Initialize FastAPI app with lifespan
# API Key Generation
def generate_api_key(prefix: str = "sk_", length: int = 32) -> str:
    """
    Generate an API key composed of a fixed prefix followed by a random sequence of characters.
    
    Parameters:
    	prefix (str): String to prepend to the generated key.
    	length (int): Number of random characters to append after the prefix.
    
    Returns:
    	api_key (str): The generated key consisting of `prefix` + `length` random characters drawn from ASCII letters, digits, and the characters `- . _ ~`.
    """
    alphabet = string.ascii_letters + string.digits + "-._~"
    random_chars = ''.join(secrets.choice(alphabet) for _ in range(length))
    return f"{prefix}{random_chars}"

app = FastAPI(
    title="Agentic Knowledge RAG Graph",
    description="Enhanced knowledge graph and RAG service with API key authentication",
    version="1.1.0",
    docs_url="/docs" if os.getenv("ENVIRONMENT") != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") != "production" else None,
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def initialize_connections():
    """
    Establishes and registers connections to external services (Neo4j, PostgreSQL, Qdrant, Ollama).
    
    Attempts to create clients/drivers and stores successful connections in the module-level `connections` dictionary.
    After connecting, invokes `setup_data_structures()` to prepare required collections, indexes, and schemas.
    Individual connection failures are logged as warnings; a failure during the overall initialization is logged as an error.
    """
    global connections
    
    try:
        # Initialize Neo4j connection
        try:
            from neo4j import GraphDatabase
            neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
            neo4j_auth = os.getenv("NEO4J_AUTH", "neo4j/password").split("/")
            connections["neo4j_driver"] = GraphDatabase.driver(
                neo4j_uri, 
                auth=(neo4j_auth[0], neo4j_auth[1])
            )
            # Test connection
            with connections["neo4j_driver"].session() as session:
                session.run("RETURN 1")
            logger.info("✅ Connected to Neo4j")
        except Exception as e:
            logger.warning(f"⚠️  Neo4j connection failed: {e}")
        
        # Initialize PostgreSQL connection
        try:
            import psycopg2
            postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:password@postgres:5432/postgres")
            connections["postgres_conn"] = psycopg2.connect(postgres_url)
            logger.info("✅ Connected to PostgreSQL")
        except Exception as e:
            logger.warning(f"⚠️  PostgreSQL connection failed: {e}")
        
        # Initialize Qdrant client
        try:
            from qdrant_client import QdrantClient
            qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
            connections["qdrant_client"] = QdrantClient(url=qdrant_url)
            # Test connection
            connections["qdrant_client"].get_collections()
            logger.info("✅ Connected to Qdrant")
        except Exception as e:
            logger.warning(f"⚠️  Qdrant connection failed: {e}")
        
        # Initialize Ollama client
        try:
            import ollama
            ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
            connections["ollama_client"] = ollama.Client(host=ollama_url)
            # Test connection
            connections["ollama_client"].list()
            logger.info("✅ Connected to Ollama")
        except Exception as e:
            logger.warning(f"⚠️  Ollama connection failed: {e}")
        
        # Initialize collections and schemas
        await setup_data_structures()
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize connections: {e}")

async def cleanup_connections():
    """
    Close and release active external database connections stored in the module-level `connections` dictionary.
    
    Closes the Neo4j driver and PostgreSQL connection in `connections` if they are present; leaves other entries unchanged.
    """
    global connections
    
    if connections["neo4j_driver"]:
        connections["neo4j_driver"].close()
    if connections["postgres_conn"]:
        connections["postgres_conn"].close()

async def setup_data_structures():
    """
    Ensure required persistent structures exist for Qdrant and Neo4j.
    
    Creates a Qdrant collection named "documents" configured for 384‑dim cosine vectors if it does not already exist, and creates Neo4j uniqueness constraints for Document.id and Entity.id plus indexes on Document.title and Entity.name. Failures during individual provider setups are logged and do not raise.
    """
    try:
        # Create Qdrant collection if it doesn't exist
        if connections["qdrant_client"]:
            try:
                from qdrant_client.models import Distance, VectorParams
                collections = connections["qdrant_client"].get_collections()
                collection_names = [c.name for c in collections.collections]
                
                if "documents" not in collection_names:
                    connections["qdrant_client"].create_collection(
                        collection_name="documents",
                        vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                    )
                    logger.info("✅ Created Qdrant collection: documents")
            except Exception as e:
                logger.warning(f"⚠️  Failed to set up Qdrant collection: {e}")
        
        # Create Neo4j constraints and indexes
        if connections["neo4j_driver"]:
            try:
                with connections["neo4j_driver"].session() as session:
                    # Create constraints
                    session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE")
                    session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE")
                    # Create indexes
                    session.run("CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.title)")
                    session.run("CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.name)")
                    logger.info("✅ Set up Neo4j constraints and indexes")
            except Exception as e:
                logger.warning(f"⚠️  Failed to set up Neo4j structures: {e}")
                
    except Exception as e:
        logger.error(f"❌ Failed to set up data structures: {e}")

def get_neo4j_driver():
    """
    Provide the active Neo4j driver connection or raise an HTTP 503 if unavailable.
    
    Returns:
        The active Neo4j driver instance.
    
    Raises:
        HTTPException: Raised with status code 503 when the Neo4j driver is not connected.
    """
    if not connections["neo4j_driver"]:
        raise HTTPException(status_code=503, detail="Neo4j service unavailable")
    return connections["neo4j_driver"]

def get_qdrant_client():
    """
    Provide the active Qdrant client connection for dependency injection.
    
    Returns:
        The connected Qdrant client instance.
    
    Raises:
        HTTPException: with status code 503 when the Qdrant service is unavailable.
    """
    if not connections["qdrant_client"]:
        raise HTTPException(status_code=503, detail="Qdrant service unavailable")
    return connections["qdrant_client"]

def get_ollama_client():
    """Dependency to get Ollama client"""
    if not connections["ollama_client"]:
        raise HTTPException(status_code=503, detail="Ollama service unavailable")
    return connections["ollama_client"]

@app.get("/", response_model=Dict[str, Any])
async def root():
    """
    Return basic service status, availability of external integrations, and primary endpoint paths.
    
    Returns:
        dict: Service overview containing:
            - message (str): Human-readable service status message.
            - status (str): Overall service health ("healthy" or "degraded").
            - version (str): Service version string.
            - services (dict): Booleans indicating whether each external service is connected: keys "neo4j", "postgres", "qdrant", "ollama".
            - endpoints (dict): Paths for primary API endpoints: "health", "documents", "query", "graph", and "collections".
    """
    return {
        "message": "Agentic Knowledge RAG Graph service is running",
        "status": "healthy",
        "version": "1.0.0",
        "services": {
            "neo4j": connections["neo4j_driver"] is not None,
            "postgres": connections["postgres_conn"] is not None,
            "qdrant": connections["qdrant_client"] is not None,
            "ollama": connections["ollama_client"] is not None
        },
        "endpoints": {
            "health": "/health",
            "documents": "/documents/",
            "query": "/query/",
            "graph": "/graph/",
            "collections": "/collections/"
        }
    }

@app.get("/health", response_model=HealthStatus)
async def health_check():
    """
    Perform a comprehensive health check of external services and return an aggregated status.
    
    Checks Neo4j, Qdrant, Ollama, and PostgreSQL for connectivity and basic responsiveness, and marks overall status as "healthy" or "degraded" when any service check fails.
    
    Returns:
        dict: Aggregated health information with keys:
            - status (str): "healthy" or "degraded".
            - timestamp (datetime): Time when the check was performed.
            - services (dict): Per-service statuses keyed by service name; values are
              "healthy", "not_connected", or "unhealthy: <error_excerpt>" (first 50 chars).
            - version (str): Service version identifier.
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(),
        "services": {},
        "version": "1.0.0"
    }
    
    # Check Neo4j
    try:
        if connections["neo4j_driver"]:
            with connections["neo4j_driver"].session() as session:
                result = session.run("RETURN 1 as test")
                result.single()
            health_status["services"]["neo4j"] = "healthy"
        else:
            health_status["services"]["neo4j"] = "not_connected"
    except Exception as e:
        health_status["services"]["neo4j"] = f"unhealthy: {str(e)[:50]}"
        health_status["status"] = "degraded"
    
    # Check Qdrant
    try:
        if connections["qdrant_client"]:
            collections = connections["qdrant_client"].get_collections()
            health_status["services"]["qdrant"] = "healthy"
        else:
            health_status["services"]["qdrant"] = "not_connected"
    except Exception as e:
        health_status["services"]["qdrant"] = f"unhealthy: {str(e)[:50]}"
        health_status["status"] = "degraded"
    
    # Check Ollama
    try:
        if connections["ollama_client"]:
            models = connections["ollama_client"].list()
            health_status["services"]["ollama"] = "healthy"
        else:
            health_status["services"]["ollama"] = "not_connected"
    except Exception as e:
        health_status["services"]["ollama"] = f"unhealthy: {str(e)[:50]}"
        health_status["status"] = "degraded"
    
    # Check PostgreSQL
    try:
        if connections["postgres_conn"]:
            cursor = connections["postgres_conn"].cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            health_status["services"]["postgres"] = "healthy"
        else:
            health_status["services"]["postgres"] = "not_connected"
    except Exception as e:
        health_status["services"]["postgres"] = f"unhealthy: {str(e)[:50]}"
        health_status["status"] = "degraded"
    
    return health_status

@app.post("/api-keys/", response_model=APIKeyResponse)
async def create_api_key(
    key_data: APIKeyCreate,
    request: Request,
    current_user_id: str = Depends(get_api_key)
):
    """
    Create a new API key and persist it to Supabase.
    
    Parameters:
        key_data (APIKeyCreate): Desired API key name, optional expiration, and scopes.
        request (Request): Incoming HTTP request (used for audit logging).
    
    Returns:
        dict: Metadata for the created API key including the generated `key` (returned only at creation), `name`, `scopes`, `expires_at`, `created_at`, `last_used_at` (null), and `is_active`.
    """
    try:
        # Generate a new API key
        api_key = generate_api_key()
        expires_at = key_data.expires_at or (datetime.utcnow() + timedelta(days=90)).isoformat()
        
        # Store in Supabase
        supabase = get_supabase()
        result = supabase.table('api_keys').insert({
            'key': api_key,
            'name': key_data.name,
            'user_id': current_user_id,
            'scopes': key_data.scopes,
            'expires_at': expires_at,
            'is_active': True
        }).execute()
        
        # Log the creation
        await log_audit_event(
            request=request,
            action="api_key.create",
            resource_type="api_key",
            resource_id=result.data[0]['id'],
            user_id=current_user_id
        )
        
        return {
            **key_data.dict(),
            'key': api_key,  # Only shown once at creation
            'created_at': datetime.utcnow().isoformat(),
            'last_used_at': None,
            'is_active': True
        }
        
    except Exception as e:
        logger.error(f"Failed to create API key: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create API key"
        )

@app.post("/documents/", response_model=Dict[str, Any])
async def add_document(
    document: Document,
    background_tasks: BackgroundTasks,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Ingests a document into the knowledge base, persists its metadata to Neo4j when available, and schedules background embedding processing.
    
    If the incoming document has no `id`, a fallback id is generated from the document content. When a Neo4j driver is connected, the document's metadata (title, content, metadata, tags, timestamps) is persisted. An asynchronous background task is scheduled to generate and store embeddings for the document.
    
    Parameters:
        document (Document): Document payload containing optional `id`, `content`, optional `title`, `metadata`, and `tags`.
        background_tasks (BackgroundTasks): FastAPI BackgroundTasks instance used to schedule embedding generation.
    
    Returns:
        dict: A status object with keys:
            - `id`: the provided document id or the generated fallback id,
            - `status`: processing status string (always `"processing"` on success),
            - `message`: human-readable status message.
    
    Raises:
        HTTPException: Raises a 500 HTTPException if an unexpected error occurs while adding the document.
    """
    try:
        import time
        start_time = time.time()
        
        document_id = document.id or f"doc_{abs(hash(document.content))}"
        
        # Store in Neo4j if available
        if connections["neo4j_driver"]:
            try:
                with connections["neo4j_driver"].session() as session:
                    session.run(
                        """
                        MERGE (d:Document {id: $id})
                        SET d.title = $title,
                            d.content = $content,
                            d.metadata = $metadata,
                            d.tags = $tags,
                            d.created_at = datetime(),
                            d.updated_at = datetime()
                        """,
                        id=document.id,
                        title=document.title or "Untitled",
                        content=document.content,
                        metadata=document.metadata,
                        tags=document.tags
                    )
            except Exception as e:
                logger.warning(f"Failed to store in Neo4j: {e}")
        
        # Add background task to generate embeddings and store in Qdrant
        background_tasks.add_task(
            process_document_embeddings,
            document.id,
            document.content,
            document.metadata or {}
        )
        
        processing_time = time.time() - start_time
        
        return {
            "id": document.id,
            "status": "processing",
            "message": "Document is being processed"
        }
        
    except Exception as e:
        logger.error(f"Error adding document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_document_embeddings(document_id: str, content: str, metadata: Dict[str, Any]):
    """
    Generate an embedding for a document and upsert it into the Qdrant "documents" collection when available.
    
    Creates a 384-dimensional embedding (mocked) and attempts to store it as a Point in the "documents" Qdrant collection with payload containing the document content and metadata. On success logs an informational message; on Qdrant failures logs a warning; on unexpected errors logs an error.
    
    Parameters:
        document_id (str): Unique identifier for the document; used as the vector point id.
        content (str): Raw document content to include in the stored payload.
        metadata (Dict[str, Any]): Arbitrary metadata to include in the stored payload.
    """
    try:
        # This would generate embeddings using a sentence transformer or Ollama
        # For now, we'll use a mock embedding
        import numpy as np
        embedding = np.random.rand(384).tolist()  # Mock 384-dimensional embedding
        
        if connections["qdrant_client"]:
            try:
                from qdrant_client.models import PointStruct
                
                connections["qdrant_client"].upsert(
                    collection_name="documents",
                    points=[
                        PointStruct(
                            id=document_id,
                            vector=embedding,
                            payload={
                                "content": content,
                                "metadata": metadata
                            }
                        )
                    ]
                )
                logger.info(f"✅ Processed embeddings for document: {document_id}")
            except Exception as e:
                logger.warning(f"Failed to store in Qdrant: {e}")
    except Exception as e:
        logger.error(f"❌ Failed to process embeddings for {document_id}: {e}")

@app.post("/query/", response_model=RAGResponse)
async def query_knowledge_base(
    query: Query,
    request: Request,
    api_key: str = Depends(get_api_key)
):
    """
    Execute a retrieval-augmented generation (RAG) search and return a consolidated answer.
    
    Performs optional vector similarity search (Qdrant) and graph-context retrieval (Neo4j) based on the provided Query, attempts to generate a refined answer via Ollama if available, and records audit events for the request and completion. The returned RAGResponse contains the original query text, the produced answer, retrieved sources, graph context, a confidence score, processing time, and a request identifier.
    
    Parameters:
        query (Query): Query payload containing the search text, filters, result limit, and flags for vector and graph context.
        request (Request): FastAPI request object used for audit logging and extracting client information.
    
    Returns:
        RAGResponse: Aggregated response including `query`, `answer`, `sources`, `graph_context`, `confidence`, `processing_time`, and `request_id`.
    
    Raises:
        HTTPException: Raised with status 500 on unexpected processing errors.
    """
    try:
        import time
        start_time = datetime.now()
        request_id = str(uuid4())
        
        # Log the query
        await log_audit_event(
            request=request,
            action="query.execute",
            resource_type="query",
            resource_id=request_id,
            metadata={
                "query_text": query.text,
                "filters": query.filters,
                "include_graph_context": query.include_graph_context
            },
            user_id=api_key  # Or extract user ID from API key
        )
        
        sources = []
        graph_context = []
        
        # Vector search in Qdrant (mock implementation)
        if query.use_vector_search and connections["qdrant_client"]:
            try:
                # In a real implementation, generate embeddings for the query
                import numpy as np
                query_embedding = np.random.rand(384).tolist()  # Mock embedding
                
                search_results = connections["qdrant_client"].search(
                    collection_name="documents",
                    query_vector=query_embedding,
                    limit=query.limit
                )
                
                for result in search_results:
                    sources.append({
                        "id": result.id,
                        "content": result.payload.get("content", ""),
                        "score": result.score,
                        "metadata": result.payload.get("metadata", {})
                    })
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        
        # Graph context retrieval
        if query.include_graph_context and connections["neo4j_driver"]:
            try:
                with connections["neo4j_driver"].session() as session:
                    # Simple graph query - in production, this would be more sophisticated
                    result = session.run(
                        """
                        MATCH (d:Document)
                        WHERE d.content CONTAINS $query_text
                        RETURN d.id, d.title, d.content, d.tags
                        LIMIT $limit
                        """,
                        query_text=query.text,
                        limit=query.limit
                    )
                    
                    for record in result:
                        graph_context.append({
                            "id": record["d.id"],
                            "title": record["d.title"],
                            "content": record["d.content"][:200] + "...",
                            "tags": record["d.tags"]
                        })
            except Exception as e:
                logger.warning(f"Graph query failed: {e}")
        
        # Generate answer using Ollama (mock implementation)
        answer = f"Based on the available information, I can provide this response to '{query.text}': [This would be a generated answer based on the retrieved sources and graph context]"
        
        if connections["ollama_client"]:
            try:
                # In a real implementation, this would use the retrieved context
                response = connections["ollama_client"].generate(
                    model="qwen2.5:7b-instruct-q4_K_M",
                    prompt=f"Answer this question based on the provided context: {query.text}\n\nContext: {sources[:3]}",
                    stream=False
                )
                answer = response.get("response", answer)
            except Exception as e:
                logger.warning(f"Ollama generation failed: {e}")
        
        processing_time = time.time() - start_time
        
        response = RAGResponse(
            query=query.text,
            answer=answer,
            sources=sources,
            graph_context=graph_context,
            confidence=0.85,  # Mock confidence score
            processing_time=processing_time,
            request_id=request_id
        )
        
        # Log successful response
        await log_audit_event(
            request=request,
            action="query.complete",
            resource_type="query",
            resource_id=request_id,
            metadata={
                "processing_time": processing_time,
                "sources_count": len(sources),
                "graph_nodes_count": len(graph_context.get("nodes", [])),
                "graph_edges_count": len(graph_context.get("edges", []))
            },
            user_id=api_key  # Or extract user ID from API key
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/nodes", response_model=Dict[str, Any])
async def get_graph_nodes(
    node_type: Optional[str] = QueryParam(None),
    limit: int = QueryParam(100, ge=1, le=1000)
):
    """
    Retrieve nodes from the Neo4j knowledge graph, optionally filtered by node label.
    
    Parameters:
        node_type (Optional[str]): If provided, only nodes with this label are returned.
        limit (int): Maximum number of nodes to return (1–1000).
    
    Returns:
        dict: {
            "nodes": List[dict] — each node has keys:
                "id" (str): node identifier,
                "labels" (List[str]): node labels,
                "properties" (dict): node properties;
            "count" (int): number of nodes returned,
            "status" (str): "success" or "neo4j_unavailable"
        }
    
    Raises:
        HTTPException: with status code 500 if an unexpected error occurs while querying the graph.
    """
    try:
        if not connections["neo4j_driver"]:
            return {"nodes": [], "count": 0, "status": "neo4j_unavailable"}
            
        with connections["neo4j_driver"].session() as session:
            if node_type:
                query_str = f"""
                MATCH (n:{node_type})
                RETURN n
                LIMIT $limit
                """
            else:
                query_str = """
                MATCH (n)
                RETURN n, labels(n) as labels
                LIMIT $limit
                """
            
            result = session.run(query_str, limit=limit)
            
            nodes = []
            for record in result:
                node = record["n"]
                node_labels = record.get("labels", list(node.labels))
                nodes.append({
                    "id": node.get("id", str(node.id)),
                    "labels": node_labels,
                    "properties": dict(node)
                })
            
            return {
                "nodes": nodes,
                "count": len(nodes),
                "status": "success"
            }
    except Exception as e:
        logger.error(f"Error getting graph nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/collections/", response_model=Dict[str, Any])
async def list_collections():
    """
    Return a summary of Qdrant collections available to the service.
    
    If the Qdrant client is not connected, returns an empty collections list and status "qdrant_unavailable".
    Otherwise returns a list of collections with each entry containing:
    - name: collection name
    - vectors_count: number of vectors in the collection (0 if not available)
    
    Returns:
        dict: {
            "collections": List[{"name": str, "vectors_count": int}],
            "status": str  # "success" or "qdrant_unavailable"
        }
    
    Raises:
        HTTPException: with status_code 500 if an unexpected error occurs while listing collections.
    """
    try:
        if not connections["qdrant_client"]:
            return {"collections": [], "status": "qdrant_unavailable"}
            
        collections = connections["qdrant_client"].get_collections()
        return {
            "collections": [
                {
                    "name": col.name,
                    "vectors_count": getattr(col, 'vectors_count', 0)
                }
                for col in collections.collections
            ],
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )