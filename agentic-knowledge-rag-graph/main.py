"""
Enhanced Agentic Knowledge RAG Graph
A comprehensive FastAPI service that provides advanced knowledge graph and RAG capabilities
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query as QueryParam, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models
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
    """Initialize and cleanup connections"""
    await initialize_connections()
    yield
    await cleanup_connections()

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="Agentic Knowledge RAG Graph",
    description="Enhanced knowledge graph and RAG service for Local AI Package",
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
    """Initialize connections to external services"""
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
    """Clean up connections"""
    global connections
    
    if connections["neo4j_driver"]:
        connections["neo4j_driver"].close()
    if connections["postgres_conn"]:
        connections["postgres_conn"].close()

async def setup_data_structures():
    """Set up initial data structures"""
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
    """Dependency to get Neo4j driver"""
    if not connections["neo4j_driver"]:
        raise HTTPException(status_code=503, detail="Neo4j service unavailable")
    return connections["neo4j_driver"]

def get_qdrant_client():
    """Dependency to get Qdrant client"""
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
    """Root endpoint with service information"""
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
    """Detailed health check"""
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

@app.post("/documents/", response_model=Dict[str, Any])
async def add_document(
    document: Document,
    background_tasks: BackgroundTasks
):
    """Add a document to the knowledge base"""
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
                        id=document_id,
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
            document_id,
            document.content,
            document.metadata
        )
        
        processing_time = time.time() - start_time
        
        return {
            "message": "Document added successfully",
            "document_id": document_id,
            "status": "success",
            "processing_time": processing_time
        }
    except Exception as e:
        logger.error(f"Error adding document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_document_embeddings(document_id: str, content: str, metadata: Dict[str, Any]):
    """Background task to process document embeddings"""
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
async def query_knowledge_base(query: Query):
    """Query the knowledge base using RAG"""
    try:
        import time
        start_time = time.time()
        
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
        
        return RAGResponse(
            query=query.text,
            answer=answer,
            sources=sources,
            graph_context=graph_context,
            confidence=0.85,  # Mock confidence score
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/nodes", response_model=Dict[str, Any])
async def get_graph_nodes(
    node_type: Optional[str] = QueryParam(None),
    limit: int = QueryParam(100, ge=1, le=1000)
):
    """Get nodes from the knowledge graph"""
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
    """List available Qdrant collections"""
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