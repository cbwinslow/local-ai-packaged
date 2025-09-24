import pytest
import os
from pathlib import Path
import yaml  # For config files if YAML used

def test_secret_lengths():
    # Validate secret lengths for security
    secrets = {
        "POSTGRES_PASSWORD": 32,
        "JWT_SECRET": 64,
        "ANON_KEY": 100,  # Approx for JWT
        "SERVICE_ROLE_KEY": 100,
        "N8N_ENCRYPTION_KEY": 64,
    }
    for var, min_len in secrets.items():
        value = os.getenv(var)
        assert value, f"{var} not set"
        assert len(value) >= min_len, f"{var} too short (min {min_len})"

def test_docker_compose_syntax(workspace_root):
    compose_file = workspace_root / "docker-compose.yml"
    assert compose_file.exists(), "docker-compose.yml missing"
    # Basic YAML validation
    with open(compose_file) as f:
        yaml.safe_load(f)
    print("docker-compose.yml syntax valid")

@pytest.mark.skipif(os.getenv("SKIP_INTEGRATION_TESTS", "false") == "true", reason="Skipping integration tests")
def test_env_consistency():
    # Check required vars for services
    required = {
        "supabase": ["ANON_KEY", "SERVICE_ROLE_KEY", "POSTGRES_PASSWORD"],
        "n8n": ["N8N_ENCRYPTION_KEY"],
        "ollama": [],  # No secrets
    }
    for service, vars_ in required.items():
        for var in vars_:
            assert os.getenv(var), f"{service} missing {var}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
