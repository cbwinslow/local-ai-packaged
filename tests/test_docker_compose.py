#!/usr/bin/env python3
"""
Test Docker Compose Configuration
Tests all Docker Compose files for syntax, security, and best practices
"""

import pytest
import yaml
import os
import subprocess
from pathlib import Path

class TestDockerCompose:
    """Test Docker Compose configurations"""
    
    @pytest.fixture
    def project_root(self):
        """Get project root directory"""
        return Path(__file__).parent.parent
    
    @pytest.fixture
    def compose_files(self, project_root):
        """Get all Docker Compose files"""
        compose_files = []
        for pattern in ["docker-compose*.yml", "docker-compose*.yaml"]:
            compose_files.extend(project_root.glob(pattern))
        return compose_files
    
    def test_compose_files_exist(self, compose_files):
        """Test that Docker Compose files exist"""
        assert len(compose_files) > 0, "No Docker Compose files found"
        
        # Check for main compose file
        main_compose = any(f.name == "docker-compose.yml" for f in compose_files)
        assert main_compose, "Main docker-compose.yml not found"
    
    def test_compose_syntax(self, compose_files, project_root):
        """Test Docker Compose file syntax"""
        # Create minimal .env for testing
        env_file = project_root / ".env"
        if not env_file.exists():
            with open(env_file, "w") as f:
                f.write("POSTGRES_PASSWORD=test\n")
                f.write("JWT_SECRET=test\n")
                f.write("ANON_KEY=test\n")
                f.write("SERVICE_ROLE_KEY=test\n")
                f.write("N8N_ENCRYPTION_KEY=test\n")
                f.write("N8N_USER_MANAGEMENT_JWT_SECRET=test\n")
                f.write("ENCRYPTION_KEY=test\n")
                f.write("NEXTAUTH_SECRET=test\n")
                f.write("MINIO_ROOT_PASSWORD=test\n")
                f.write("CLICKHOUSE_PASSWORD=test\n")
                f.write("LANGFUSE_SALT=test\n")
                f.write("NEO4J_AUTH=neo4j/test\n")
                f.write("FLOWISE_USERNAME=test\n")
                f.write("FLOWISE_PASSWORD=test\n")
                f.write("GITHUB_TOKEN=test\n")
        
        for compose_file in compose_files:
            # Skip files that might not be standalone
            if "traefik" in compose_file.name or "mcp" in compose_file.name:
                continue
                
            try:
                result = subprocess.run(
                    ["docker", "compose", "-f", str(compose_file), "config", "-q"],
                    cwd=project_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                pytest.fail(f"Docker Compose syntax error in {compose_file.name}: {e.stderr}")
    
    def test_compose_yaml_structure(self, compose_files):
        """Test YAML structure of Docker Compose files"""
        for compose_file in compose_files:
            with open(compose_file, 'r') as f:
                try:
                    data = yaml.safe_load(f)
                    assert isinstance(data, dict), f"Invalid YAML structure in {compose_file.name}"
                    
                    # Check for required top-level keys
                    if "services" not in data and "include" not in data:
                        pytest.fail(f"No 'services' or 'include' section found in {compose_file.name}")
                        
                except yaml.YAMLError as e:
                    pytest.fail(f"YAML syntax error in {compose_file.name}: {e}")
    
    def test_service_security(self, compose_files):
        """Test Docker Compose services for security best practices"""
        security_issues = []
        
        for compose_file in compose_files:
            with open(compose_file, 'r') as f:
                try:
                    data = yaml.safe_load(f)
                    if not isinstance(data, dict) or "services" not in data:
                        continue
                        
                    for service_name, service_config in data["services"].items():
                        if not isinstance(service_config, dict):
                            continue
                            
                        # Check for privileged containers
                        if service_config.get("privileged", False):
                            security_issues.append(f"{compose_file.name}: Service '{service_name}' runs as privileged")
                        
                        # Check for host network mode
                        if service_config.get("network_mode") == "host":
                            security_issues.append(f"{compose_file.name}: Service '{service_name}' uses host networking")
                        
                        # Check for hardcoded secrets in environment
                        env_vars = service_config.get("environment", [])
                        if isinstance(env_vars, list):
                            for env_var in env_vars:
                                if isinstance(env_var, str) and "=" in env_var:
                                    key, value = env_var.split("=", 1)
                                    if any(sensitive in key.lower() for sensitive in ["password", "secret", "key", "token"]):
                                        if not value.startswith("${") and value not in ["", "placeholder"]:
                                            security_issues.append(f"{compose_file.name}: Hardcoded secret in {service_name}.{key}")
                        
                        # Check for volume binds to sensitive paths
                        volumes = service_config.get("volumes", [])
                        for volume in volumes:
                            if isinstance(volume, str) and ":" in volume:
                                host_path = volume.split(":")[0]
                                if host_path.startswith("/"):
                                    sensitive_paths = ["/etc", "/var/run/docker.sock", "/proc", "/sys"]
                                    for sensitive_path in sensitive_paths:
                                        if host_path.startswith(sensitive_path):
                                            security_issues.append(f"{compose_file.name}: Service '{service_name}' mounts sensitive path {host_path}")
                
                except yaml.YAMLError:
                    continue  # Skip files with YAML errors (tested elsewhere)
        
        if security_issues:
            pytest.fail(f"Security issues found:\n" + "\n".join(security_issues))
    
    def test_health_checks(self, compose_files):
        """Test that critical services have health checks"""
        critical_services = ["postgres", "db", "redis", "ollama", "n8n"]
        missing_health_checks = []
        
        for compose_file in compose_files:
            with open(compose_file, 'r') as f:
                try:
                    data = yaml.safe_load(f)
                    if not isinstance(data, dict) or "services" not in data:
                        continue
                        
                    for service_name, service_config in data["services"].items():
                        if not isinstance(service_config, dict):
                            continue
                            
                        # Check if this is a critical service
                        is_critical = any(critical in service_name.lower() for critical in critical_services)
                        
                        if is_critical and "healthcheck" not in service_config:
                            missing_health_checks.append(f"{compose_file.name}: Service '{service_name}' missing health check")
                
                except yaml.YAMLError:
                    continue
        
        # This is a warning, not a failure
        if missing_health_checks:
            print("Warning: Missing health checks:\n" + "\n".join(missing_health_checks))
    
    def test_network_configuration(self, compose_files):
        """Test network configuration"""
        for compose_file in compose_files:
            with open(compose_file, 'r') as f:
                try:
                    data = yaml.safe_load(f)
                    if not isinstance(data, dict):
                        continue
                    
                    # Check if networks are properly defined
                    if "services" in data:
                        services_with_networks = []
                        for service_name, service_config in data["services"].items():
                            if isinstance(service_config, dict) and "networks" in service_config:
                                services_with_networks.append(service_name)
                        
                        # If services use networks, networks section should exist
                        if services_with_networks and "networks" not in data:
                            pytest.fail(f"{compose_file.name}: Services use networks but no networks section defined")
                
                except yaml.YAMLError:
                    continue

if __name__ == "__main__":
    pytest.main([__file__])