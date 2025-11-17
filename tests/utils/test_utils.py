"""
Test utilities for Local AI Package
"""

import os
import time
import docker
import requests
from typing import Dict, Any, Optional
import subprocess
import json


class TestConstants:
    """Constants used across tests"""
    
    # Services endpoints
    N8N_INTERNAL_URL = "http://n8n:5678"
    N8N_EXTERNAL_URL = "http://localhost:5678"  # When accessible
    
    OPEN_WEBUI_INTERNAL_URL = "http://open-webui:8080"
    OPEN_WEBUI_EXTERNAL_URL = "http://localhost:8080"
    
    FLOWISE_INTERNAL_URL = "http://flowise:3001"
    FLOWISE_EXTERNAL_URL = "http://localhost:3001"
    
    OLLAMA_INTERNAL_URL = "http://ollama:11434"
    OLLAMA_EXTERNAL_URL = "http://localhost:11434"
    
    # Domain-based endpoints (for when Caddy is available)
    N8N_DOMAIN_URL = "https://n8n.cloudcurio.cc"
    OPEN_WEBUI_DOMAIN_URL = "https://openwebui.cloudcurio.cc"
    FLOWISE_DOMAIN_URL = "https://flowise.cloudcurio.cc"
    OLLAMA_DOMAIN_URL = "https://ollama.cloudcurio.cc"
    
    # Timeout settings
    REQUEST_TIMEOUT = 30
    CONTAINER_STARTUP_TIMEOUT = 120


def check_service_health(url: str, timeout: int = 10) -> bool:
    """Check if a service is responsive"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code in [200, 401, 403]  # Various valid responses
    except:
        return False


def wait_for_service(url: str, timeout: int = 60) -> bool:
    """Wait for a service to become available"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if check_service_health(url):
            return True
        time.sleep(2)
    return False


def get_docker_client():
    """Get Docker client instance"""
    try:
        return docker.from_env()
    except:
        return None


def check_container_running(service_name: str) -> bool:
    """Check if a specific container is running"""
    client = get_docker_client()
    if not client:
        return False
    
    try:
        container = client.containers.get(service_name)
        return container.status == 'running'
    except:
        return False


def run_docker_command(cmd: str) -> tuple:
    """Run a docker command and return output"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def get_container_logs(service_name: str, lines: int = 50) -> str:
    """Get recent logs from a container"""
    client = get_docker_client()
    if not client:
        return ""
    
    try:
        container = client.containers.get(service_name)
        logs = container.logs(tail=lines).decode('utf-8')
        return logs
    except:
        return ""


def get_active_services() -> list:
    """Get list of active local-ai containers"""
    client = get_docker_client()
    if not client:
        return []
    
    try:
        containers = client.containers.list()
        active_services = []
        for container in containers:
            if 'localai' in container.name.lower() or \
               'n8n' in container.name.lower() or \
               'open-webui' in container.name.lower() or \
               'ollama' in container.name.lower() or \
               'flowise' in container.name.lower() or \
               'supabase' in container.name.lower():
                active_services.append(container.name)
        return active_services
    except:
        return []


def validate_environment() -> Dict[str, Any]:
    """Validate the test environment"""
    env_status = {
        'docker_available': get_docker_client() is not None,
        'services_running': len(get_active_services()) > 0,
        'n8n_running': check_container_running('n8n'),
        'open_webui_running': check_container_running('open-webui'),
        'ollama_running': check_container_running('ollama'),
        'flowise_running': check_container_running('flowise'),
        'active_services': get_active_services()
    }
    return env_status