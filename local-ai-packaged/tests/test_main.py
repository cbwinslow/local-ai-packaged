import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
from rag.query import rag_query  # Import for mocking

client = TestClient(app)

def test_read_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["message"] == "Local AI Packaged Backend - Full RAG ready!"

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"

def test_rag_ingest():
    with patch('rag.ingestion.ingest_documents') as mock_ingest:
        mock_ingest.return_value = "Ingested 5 chunks"
        r = client.post("/rag/ingest", json={"query": "ignore", "file_path": "test.txt"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "success"

def test_rag_query():
    with patch('rag.query.rag_query') as mock_query:
        mock_response = {"query": "test", "analysis": "Mock analysis"}
        mock_query.return_value = mock_response
        r = client.post("/rag/query", json={"query": "test query"})
        assert r.status_code == 200
        data = r.json()
        assert data["query"] == "test query"
        assert "analysis" in data