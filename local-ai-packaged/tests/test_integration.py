import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from agentic_knowledge_rag_graph.query import rag_query  # Updated import

client = TestClient(app)

@patch('agentic_knowledge_rag_graph.query.rag_query')
def test_integration_rag(mock_rag):
    mock_response = {"query": "test", "analysis": "Integrated response"}
    mock_rag.return_value = mock_response
    
    r = client.post("/rag/query", json={"query": "integration test"})
    assert r.status_code == 200
    data = r.json()
    assert data["analysis"] == "Integrated response"

@patch('agentic_knowledge_rag_graph.ingestion.ingest_documents')
def test_integration_ingest(mock_ingest):
    mock_ingest.return_value = "Integrated ingest success"
    
    r = client.post("/rag/ingest", json={"file_path": "test.txt"})
    assert r.status_code == 200
    data = r.json()
    assert "success" in data["status"]