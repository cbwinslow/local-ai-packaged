"""
Agentic Knowledge RAG Graph
A FastAPI service that provides knowledge graph and RAG capabilities
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Knowledge RAG Graph",
    description="Knowledge graph and RAG service for the Local AI Package",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class Document(BaseModel):
    id: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = {}

class Query(BaseModel):
    text: str
    filters: Dict[str, Any] = {}
    limit: int = 10

class GraphNode(BaseModel):
    id: str
    type: str
    properties: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = {}

# Global variables for connections
neo4j_driver = None
postgres_conn = None
qdrant_client = None
ollama_client = None

@app.on_event("startup")
async def startup_event():
    """Initialize connections to external services"""
    global neo4j_driver, postgres_conn, qdrant_client, ollama_client
    
    try:
        # Initialize Neo4j connection
        from neo4j import GraphDatabase
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        neo4j_auth = os.getenv("NEO4J_AUTH", "neo4j/password").split("/")
        neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_auth[0], neo4j_auth[1]))
        logger.info("Connected to Neo4j")
        
        # Initialize PostgreSQL connection
        import psycopg2
        postgres_url = os.getenv("POSTGRES_URL", "postgresql://postgres:password@postgres:5432/postgres")
        postgres_conn = psycopg2.connect(postgres_url)
        logger.info("Connected to PostgreSQL")
        
        # Initialize Qdrant client
        from qdrant_client import QdrantClient
        qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
        qdrant_client = QdrantClient(url=qdrant_url)
        logger.info("Connected to Qdrant")
        
        # Initialize Ollama client
        import ollama
        ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
        ollama_client = ollama.Client(host=ollama_url)
        logger.info("Connected to Ollama")
        
    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up connections"""
    global neo4j_driver, postgres_conn, qdrant_client
    
    if neo4j_driver:
        neo4j_driver.close()
    if postgres_conn:
        postgres_conn.close()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Agentic Knowledge RAG Graph service is running",
        "status": "healthy",
        "services": {
            "neo4j": neo4j_driver is not None,
            "postgres": postgres_conn is not None,
            "qdrant": qdrant_client is not None,
            "ollama": ollama_client is not None
        }
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "status": "healthy",
        "services": {}
    }
    
    # Check Neo4j
    try:
        with neo4j_driver.session() as session:
            session.run("RETURN 1")
        health_status["services"]["neo4j"] = "healthy"
    except Exception as e:
        health_status["services"]["neo4j"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Qdrant
    try:
        collections = qdrant_client.get_collections()
        health_status["services"]["qdrant"] = "healthy"
    except Exception as e:
        health_status["services"]["qdrant"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Ollama
    try:
        models = ollama_client.list()
        health_status["services"]["ollama"] = "healthy"
    except Exception as e:
        health_status["services"]["ollama"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status

@app.post("/documents/")
async def add_document(document: Document):
    """Add a document to the knowledge base"""
    try:
        # This is a placeholder implementation
        # In a real implementation, you would:
        # 1. Generate embeddings for the document
        # 2. Store the document in Qdrant
        # 3. Extract entities and relationships
        # 4. Store the graph structure in Neo4j
        
        document_id = document.id or f"doc_{hash(document.content)}"
        
        return {
            "message": "Document added successfully",
            "document_id": document_id,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error adding document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query/")
async def query_knowledge_base(query: Query):
    """Query the knowledge base using RAG"""
    try:
        # This is a placeholder implementation
        # In a real implementation, you would:
        # 1. Generate embeddings for the query
        # 2. Search for similar documents in Qdrant
        # 3. Retrieve relevant graph context from Neo4j
        # 4. Generate a response using Ollama
        
        return {
            "query": query.text,
            "results": [
                {
                    "content": "This is a placeholder response. In a real implementation, this would be generated using RAG.",
                    "relevance_score": 0.95,
                    "source_documents": ["doc_1", "doc_2"],
                    "graph_context": []
                }
            ],
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/nodes")
async def get_graph_nodes(node_type: Optional[str] = None, limit: int = 100):
    """Get nodes from the knowledge graph"""
    try:
        # Placeholder implementation
        return {
            "nodes": [],
            "count": 0,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error getting graph nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/graph/edges")
async def get_graph_edges(source: Optional[str] = None, target: Optional[str] = None, limit: int = 100):
    """Get edges from the knowledge graph"""
    try:
        # Placeholder implementation
        return {
            "edges": [],
            "count": 0,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error getting graph edges: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )