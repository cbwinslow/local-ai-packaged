import os
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from neo4j import GraphDatabase
from supabase import create_client, Client
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from langchain.llms import Ollama
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.graphs import Neo4jGraph
import uvicorn
from sentence_transformers import SentenceTransformer  # Assuming added dep, but for basic, use placeholder

app = FastAPI(title="Agentic RAG Backend")

# Env vars
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:POSTGRES_PASSWORD@postgres:5432/postgres")
SUPABASE_URL = os.getenv("SUPABASE_URL")  # If using Supabase client
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")

# Connections
try:
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    graph = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USER, password=NEO4J_PASSWORD)
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    qdrant_client = QdrantClient(url=QDRANT_URL)
    llm = Ollama(model=OLLAMA_MODEL)
    # Placeholder embedding model
    embedder = SentenceTransformer('all-MiniLM-L6-v2')  # Note: Add to requirements if needed
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Failed to initialize connections: {str(e)}")

# Sample prompts from agents.md description
ENTITY_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["text"],
    template="Extract key entities (persons, organizations, locations, legislation) from the following legislative text and output as JSON: {text}"
)

FACT_CHECKING_PROMPT = PromptTemplate(
    input_variables=["statement", "context"],
    template="Fact-check the statement '{statement}' against the context '{context}' and provide verification."
)

class SimpleKGPipeline:
    def __init__(self, llm):
        self.llm = llm
        self.entity_chain = LLMChain(llm=llm, prompt=ENTITY_EXTRACTION_PROMPT)

    def build_graph(self, text: str, doc_id: str):
        try:
            entities_json = self.entity_chain.run(text=text)
            # Parse JSON (placeholder)
            entities = eval(entities_json)  # Insecure, use json.loads in prod
            with neo4j_driver.session() as session:
                for entity in entities.get('entities', []):
                    session.run("CREATE (n:Entity {name: $name, type: $type, doc_id: $doc_id})", 
                                name=entity['name'], type=entity['type'], doc_id=doc_id)
                # Simple relations (placeholder)
                session.run("MATCH (a:Entity), (b:Entity) WHERE a.doc_id = $doc_id AND b.doc_id = $doc_id CREATE (a)-[:RELATED_TO]->(b)", doc_id=doc_id)
            return entities
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"KG build failed: {str(e)}")

kg_pipeline = SimpleKGPipeline(llm)

class IngestRequest(BaseModel):
    text: str
    metadata: Dict[str, Any] = {}

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class Response(BaseModel):
    result: str
    sources: List[str] = []

@app.post("/ingest", response_model=Response)
async def ingest(request: IngestRequest):
    try:
        doc_id = str(uuid.uuid4())
        # Build KG
        entities = kg_pipeline.build_graph(request.text, doc_id)
        
        # Embed and store in Qdrant
        embedding = embedder.encode(request.text).tolist()
        qdrant_client.recreate_collection(
            collection_name="documents",
            vectors_config=VectorParams(size=len(embedding), distance=Distance.COSINE)
        )
        qdrant_client.upsert(
            collection_name="documents",
            points=[PointStruct(id=doc_id, vector=embedding, payload={"text": request.text, "entities": str(entities)})]
        )
        
        # Store in Supabase
        data = {"id": doc_id, "text": request.text, "metadata": request.metadata}
        supabase.table("documents").insert(data).execute()
        
        return Response(result=f"Ingested document {doc_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")

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
        
        # Supabase retrieve (placeholder)
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
        
        # Fact-check if needed (placeholder)
        if "fact-check" in request.query.lower():
            fact_chain = LLMChain(llm=llm, prompt=FACT_CHECKING_PROMPT)
            fact_result = fact_chain.run(statement=request.query, context=full_context)
            result += f"\nFact-check: {fact_result}"
        
        return Response(result=result, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

def main():
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()