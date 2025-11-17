"""
Basic smoke test for the Local AI Package
"""

import pytest
from utils.test_utils import validate_environment


def test_basic_system_validation():
    """Basic test to validate system environment"""
    env_status = validate_environment()
    print(f"Environment status: {env_status}")
    
    # We should have Docker available
    assert env_status['docker_available'], "Docker should be available"
    
    # We should have some services running
    assert len(env_status['active_services']) > 0, "At least one service should be active"
    
    print(f"✓ System validation passed with {len(env_status['active_services'])} active services")


def test_core_services_running():
    """Test that core services are running"""
    env_status = validate_environment()
    
    # Check if core services are running
    core_services_present = sum([
        env_status.get('n8n_running', False),
        env_status.get('open_webui_running', False),
        env_status.get('ollama_running', False),
        env_status.get('flowise_running', False)
    ])
    
    # At least 2 core services should be running
    assert core_services_present >= 2, f"At least 2 core services should be running, only {core_services_present} found"
    
    print(f"✓ Found {core_services_present} core services running")


if __name__ == "__main__":
    test_basic_system_validation()
    test_core_services_running()
    print("✓ All smoke tests passed!")