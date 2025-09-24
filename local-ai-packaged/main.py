from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# New imports for /query
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_ollama import OllamaLLM, OllamaEmbeddings  # Local LLM/embeddings
from supabase import create_client, Client
from qdrant_client import QdrantClient
from langchain_community.graphs import Neo4jGraph
from neo4j import GraphDatabase

from agentic_knowledge_rag_graph.ingestion import ingest_documents  # Existing
from agentic_knowledge_rag_graph.query import rag_query  # Existing

load_dotenv()

app = FastAPI(title="Local AI Packaged Backend", version="1.0.0")

# Add CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5  # New for /query

# New: Response model
class Response(BaseModel):
    result: str
    sources: list[str]

# New: Initialize clients for /query (global)
qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
neo4j_driver = GraphDatabase.driver(
    "bolt://neo4j:7687",
    auth=("neo4j", os.getenv("NEO4J_PASSWORD", "password"))
)
graph = Neo4jGraph(driver=neo4j_driver)
llm = OllamaLLM(model="llama3.1")  # Local Ollama
embedder = OllamaEmbeddings(model="llama3.1")
supabase: Client = create_client(os.getenv("NEXT_PUBLIC_SUPABASE_URL"), os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY"))

# New: FACT_CHECKING_PROMPT
FACT_CHECKING_PROMPT = PromptTemplate(
    input_variables=["statement", "context"],
    template="Fact-check the statement '{statement}' against context: {context}. Respond with verified facts or corrections."
)

class QueryRequest(BaseModel):  # Existing, extended
    query: str
    file_path: str = None  # Optional for ingestion

@app.get("/")
def read_root():
    return {"message": "Local AI Packaged Backend - Full RAG ready!"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "services": "RAG pipeline active"}

@app.post("/rag/ingest")
def ingest_endpoint(request: QueryRequest):
    if not request.file_path:
        raise HTTPException(status_code=400, detail="file_path required for ingestion")
    try:
        result = ingest_documents(request.file_path)
        return {"status": "success", "message": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/query")
def rag_endpoint(request: QueryRequest):
    if not request.query:
        raise HTTPException(status_code=400, detail="query required")
    try:
        response = rag_query(request.query)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# New /query endpoint
@app.post("/query", response_model=Response)
async def query(request: QueryRequest):
    try:
        # Qdrant similarity search
        search_result = qdrant_client.search(
            collection_name="documents",
            query_vector=embedder.encode(request.query).tolist(),
            limit=request.top_k
        )
        contexts = [hit.payload['text'] for hit in search_result]
        sources = [str(hit.id) for hit in search_result]
        
        # Neo4j query (Text2Cypher placeholder)
        cypher_template = PromptTemplate(
            input_variables=["query"],
            template="Generate Cypher query for: {query}"
        )
        cypher_chain = LLMChain(llm=llm, prompt=cypher_template)
        cypher_query = cypher_chain.run(query=request.query)
        neo4j_results = graph.query(cypher_query)
        kg_context = str(neo4j_results)
        
        # Supabase retrieve
        supa_result = supabase.table("documents").select("*").eq("id", sources[0] if sources else "").execute()
        supa_context = str(supa_result.data) if supa_result.data else ""
        
        # RAG with Ollama
        rag_prompt = PromptTemplate(
            input_variables=["query", "context"],
            template="Answer the query '{query}' using the following context: {context}. For legislative analysis, fact-check if needed."
        )
        rag_chain = LLMChain(llm=llm, prompt=rag_prompt)
        full_context = " ".join(contexts + [kg_context, supa_context])
        result = rag_chain.run(query=request.query, context=full_context)
        
        # Fact-check if needed
        if "fact-check" in request.query.lower():
            fact_chain = LLMChain(llm=llm, prompt=FACT_CHECKING_PROMPT)
            fact_result = fact_chain.run(statement=request.query, context=full_context)
            result += f"\nFact-check: {fact_result}"
        
        return Response(result=result, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)