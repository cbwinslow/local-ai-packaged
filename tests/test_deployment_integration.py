import pytest
import subprocess
import time
import os
from pathlib import Path

@pytest.fixture(scope="session")
def workspace_root():
    return Path(__file__).parent.parent

@pytest.mark.integration
def test_postgres_connection(workspace_root):
    password = os.getenv("POSTGRES_PASSWORD")
    if not password:
        pytest.skip("POSTGRES_PASSWORD not set")

    # Check if container exists
    result = subprocess.run(["docker", "ps", "--filter", "name=postgres", "--format", "table"], capture_output=True, text=True)
    if "postgres" not in result.stdout:
        pytest.skip("Postgres container not running")

    result = subprocess.run([
        "docker", "exec", "postgres", "psql", "-U", "postgres", "-c", "SELECT 1;"
    ], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, "Postgres connection failed"

@pytest.mark.integration
def test_rabbitmq_queue(workspace_root):
    user = os.getenv("RABBITMQ_USER")
    passw = os.getenv("RABBITMQ_PASSWORD")
    if not user or not passw:
        pytest.skip("RabbitMQ creds not set")
    
    result = subprocess.run([
        "docker", "exec", "rabbitmq", "rabbitmqctl", "list_queues"
    ], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, "RabbitMQ queue check failed"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
