import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings  # Or use OllamaEmbeddings for local
from langchain_community.graphs import Neo4jGraph
from qdrant_client import QdrantClient
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
qdrant_client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
neo4j_driver = GraphDatabase.driver(
    "bolt://neo4j:7687",
    auth=("neo4j", os.getenv("NEO4J_PASSWORD", "password"))
)
graph = Neo4jGraph(driver=neo4j_driver)

embeddings = OpenAIEmbeddings()  # Replace with OllamaEmbeddings(model="llama2") for local

def ingest_documents(file_path: str, collection_name: str = "legislation_docs"):
    """Ingest text documents: split, embed to Qdrant, extract entities to Neo4j KG."""
    loader = TextLoader(file_path)
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(documents)
    
    # Vector store in Qdrant
    vectorstore = Qdrant.from_documents(
        documents=splits,
        embedding=embeddings,
        url=os.getenv("QDRANT_URL"),
        collection_name=collection_name
    )
    
    # Simple entity extraction stub (expand with CrewAI agent)
    for doc in splits:
        # TODO: Use CrewAI for advanced NER (e.g., bills, legislators)
        entities = {"text": doc.page_content[:100], "entities": ["bill_X", "legislator_Y"]}  # Placeholder
        graph.query("CREATE (n:Document {content: $content, entities: $entities})", 
                    content=entities["text"], entities=entities["entities"])
    
    return f"Ingested {len(splits)} chunks to Qdrant/Neo4j."