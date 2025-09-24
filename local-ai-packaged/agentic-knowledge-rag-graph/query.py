import os
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Qdrant
from langchain_openai import ChatOpenAI  # Or Ollama for local
from langchain_community.graphs import Neo4jGraph
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
from dotenv import load_dotenv
from crewai import Agent, Task, Crew  # For agentic RAG

load_dotenv()

# Clients (reuse from ingestion)
qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
neo4j_driver = GraphDatabase.driver(
    "bolt://neo4j:7687",
    auth=("neo4j", os.getenv("NEO4J_PASSWORD", "password"))
)
graph = Neo4jGraph(driver=neo4j_driver)

llm = ChatOpenAI(model="gpt-3.5-turbo")  # Or Ollama(model="llama2")

def setup_retriever(collection_name: str = "legislation_docs"):
    """Setup Qdrant retriever."""
    embeddings = OpenAIEmbeddings()  # Match ingestion
    vectorstore = Qdrant(
        client=qdrant_client,
        collection_name=collection_name,
        embeddings=embeddings
    )
    return vectorstore.as_retriever(search_kwargs={"k": 5})

def rag_query(query: str, collection_name: str = "legislation_docs"):
    """Hybrid RAG: Retrieve from Qdrant, query Neo4j KG, use CrewAI for analysis."""
    retriever = setup_retriever(collection_name)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever
    )
    
    # Vector response
    vector_response = qa_chain.run(query)
    
    # Graph query (Cypher for KG)
    graph_response = graph.query(
        "MATCH (n:Document) WHERE n.content CONTAINS $query_term RETURN n.entities LIMIT 10",
        query_term=query
    )
    
    # CrewAI agent for legal analysis (stub; expand with tools)
    analyst = Agent(
        role="Legal Analyst",
        goal="Analyze legislative query using retrieved data",
        backstory="Expert in bills and regulations",
        llm=llm,
        verbose=True
    )
    task = Task(
        description=f"Analyze: {query} with data: {vector_response} and entities: {graph_response}",
        agent=analyst
    )
    crew = Crew(agents=[analyst], tasks=[task])
    agent_response = crew.kickoff()
    
    return {
        "query": query,
        "vector_retrieval": vector_response,
        "graph_entities": graph_response,
        "analysis": agent_response
    }