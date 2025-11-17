"""
Unit tests for test utilities
"""

import pytest
import requests
from unittest.mock import patch, MagicMock
from utils.test_utils import (
    check_service_health, 
    wait_for_service,
    get_docker_client,
    check_container_running,
    run_docker_command,
    get_container_logs,
    get_active_services,
    validate_environment,
    TestConstants
)


class TestTestConstants:
    """Test constants are properly defined"""
    
    def test_constants_exist(self):
        """Test that constants are defined"""
        assert hasattr(TestConstants, 'N8N_INTERNAL_URL')
        assert hasattr(TestConstants, 'OPEN_WEBUI_INTERNAL_URL')
        assert hasattr(TestConstants, 'REQUEST_TIMEOUT')


class TestServiceHealthChecks:
    """Test service health check functions"""
    
    @patch('tests.utils.test_utils.requests.get')
    def test_check_service_health_success(self, mock_get):
        """Test service health check with success response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        result = check_service_health("http://test.com")
        assert result is True
    
    @patch('tests.utils.test_utils.requests.get')
    def test_check_service_health_with_auth_error(self, mock_get):
        """Test service health check with authentication error"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response
        
        result = check_service_health("http://test.com")
        assert result is True
        
    @patch('tests.utils.test_utils.requests.get')
    def test_check_service_health_timeout(self, mock_get):
        """Test service health check with timeout"""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = check_service_health("http://test.com")
        assert result is False


class TestDockerClient:
    """Test Docker-related functions"""
    
    @patch('tests.utils.test_utils.docker.from_env')
    def test_get_docker_client_success(self, mock_from_env):
        """Test successful Docker client retrieval"""
        mock_client = MagicMock()
        mock_from_env.return_value = mock_client
        
        client = get_docker_client()
        assert client == mock_client
        
    @patch('tests.utils.test_utils.docker.from_env')
    def test_get_docker_client_failure(self, mock_from_env):
        """Test Docker client retrieval failure"""
        mock_from_env.side_effect = Exception("Docker not available")
        
        client = get_docker_client()
        assert client is None


class TestContainerOperations:
    """Test container-specific operations"""
    
    @patch('tests.utils.test_utils.get_docker_client')
    def test_check_container_running_true(self, mock_get_client):
        """Test checking if a running container exists"""
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.status = 'running'
        
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client
        
        result = check_container_running("test_container")
        assert result is True
        mock_client.containers.get.assert_called_once_with("test_container")
        
    @patch('tests.utils.test_utils.get_docker_client')
    def test_check_container_running_false(self, mock_get_client):
        """Test checking if a non-running container exists"""
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.status = 'exited'
        
        mock_client.containers.get.return_value = mock_container
        mock_get_client.return_value = mock_client
        
        result = check_container_running("test_container")
        assert result is False


class TestRunDockerCommand:
    """Test Docker command execution"""
    
    @patch('tests.utils.test_utils.subprocess.run')
    def test_run_docker_command_success(self, mock_run):
        """Test successful Docker command execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "success"
        mock_result.stderr = ""
        mock_run.return_value = mock_result
        
        returncode, stdout, stderr = run_docker_command("docker ps")
        assert returncode == 0
        assert stdout == "success"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])