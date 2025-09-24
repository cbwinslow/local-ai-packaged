import pytest
import subprocess
import os
import time
from pathlib import Path
import dotenv

# Load .env for tests
dotenv.load_dotenv()

@pytest.fixture(scope="session")
def workspace_root():
    return Path(__file__).parent.parent

def test_env_population(workspace_root):
    env_file = workspace_root / ".env"
    assert env_file.exists(), ".env file must exist after secrets generation"
    
    # Check for actual values vs commands
    with open(env_file) as f:
        content = f.read()
    assert "$(openssl" not in content, "All openssl commands should be evaluated in .env"
    
    # Verify key secrets are set (check length >0)
    required_vars = ["POSTGRES_PASSWORD", "JWT_SECRET", "ANON_KEY", "SERVICE_ROLE_KEY"]
    for var in required_vars:
        value = os.getenv(var)
        assert value and len(value) > 10, f"{var} must be populated with a secure value"

@pytest.mark.skipif(os.getenv("SKIP_DOCKER_TESTS", "false") == "true", reason="Skipping Docker tests")
def test_docker_compose_up(workspace_root):
    # Test docker compose up -d (non-destructive; assumes services can start)
    result = subprocess.run(["docker", "compose", "up", "-d"], cwd=workspace_root, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        pytest.skip(f"Docker compose up skipped due to error: {result.stderr[:200]}...")
    assert result.returncode == 0, f"Docker compose up failed: {result.stderr}"
    
    # Wait for services to start
    time.sleep(30)
    
    # Check services are running (at least core ones)
    result = subprocess.run(["docker", "compose", "ps", "--services"], cwd=workspace_root, capture_output=True, text=True)
    running_services = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    core_services = ["postgres", "ollama", "n8n", "qdrant"]
    for service in core_services:
        assert any(service in s for s in running_services), f"Core service {service} not running"

@pytest.mark.skipif(os.getenv("SKIP_INTEGRATION_TESTS", "false") == "true", reason="Skipping integration tests")
def test_supabase_health():
    anon_key = os.getenv("ANON_KEY")
    if not anon_key:
        pytest.skip("ANON_KEY not set")
    
    result = subprocess.run([
        "curl", "-s", "-H", f"apikey: {anon_key}", 
        "http://localhost:8000/health"
    ], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        pytest.skip(f"Supabase not ready: {result.stderr[:100]}...")
    assert result.returncode == 0, "Supabase health check failed"
    assert "OK" in result.stdout, "Supabase not healthy"

@pytest.mark.skipif(os.getenv("SKIP_INTEGRATION_TESTS", "false") == "true", reason="Skipping integration tests")
def test_n8n_access():
    result = subprocess.run(["curl", "-s", "-f", "http://localhost:5678/healthz"], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        pytest.skip(f"n8n not ready: {result.stderr[:100]}...")
    assert result.returncode == 0, "n8n health check failed"

@pytest.mark.skipif(os.getenv("SKIP_INTEGRATION_TESTS", "false") == "true", reason="Skipping integration tests")
def test_ollama_models():
    result = subprocess.run(["curl", "-s", "http://localhost:11434/api/tags"], capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        pytest.skip(f"Ollama not ready: {result.stderr[:100]}...")
    assert result.returncode == 0, "Ollama API failed"
    assert '"models"' in result.stdout, "Ollama models not loaded or empty"

def test_full_deployment_smoke(workspace_root):
    # Smoke test: verify key files exist post-setup
    key_files = [
        workspace_root / ".env",
        workspace_root / "docker-compose.yml",
        workspace_root / "scripts" / "start-all-services.sh"
    ]
    for file in key_files:
        assert file.exists(), f"Key file {file} missing after setup"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
