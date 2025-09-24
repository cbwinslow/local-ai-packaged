import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_query_endpoint():
    response = client.post(
        "/query",
        json={"query": "test"}
    )
    assert response.status_code == 200
    assert "response" in response.json()