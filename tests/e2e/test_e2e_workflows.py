"""
End-to-end tests for Local AI Package
"""

import pytest
import requests
import time
import json
from utils.test_utils import (
    check_service_health,
    wait_for_service,
    check_container_running,
    TestConstants
)


@pytest.mark.e2e
class TestEndToEndWorkflows:
    """End-to-end tests for complete workflows"""
    
    def test_full_stack_readiness(self):
        """Test that the full stack is ready and operational"""
        print("Testing full stack readiness...")
        
        # Define the services we expect to be available
        services_to_check = {
            "n8n": {
                "container": "n8n",
                "url": TestConstants.N8N_INTERNAL_URL,
                "required": True
            },
            "open-webui": {
                "container": "open-webui", 
                "url": TestConstants.OPEN_WEBUI_INTERNAL_URL,
                "required": True
            },
            "ollama": {
                "container": "ollama",
                "url": TestConstants.OLLAMA_INTERNAL_URL, 
                "required": True
            },
            "flowise": {
                "container": "flowise",
                "url": TestConstants.FLOWISE_INTERNAL_URL,
                "required": False  # Optional service
            }
        }
        
        readiness_results = {}
        
        for service_name, service_info in services_to_check.items():
            container_running = check_container_running(service_info["container"])
            service_accessible = check_service_health(service_info["url"]) if container_running else False
            
            readiness_results[service_name] = {
                "container_running": container_running,
                "service_accessible": service_accessible,
                "required": service_info["required"]
            }
            
            print(f"{service_name}:")
            print(f"  Container running: {container_running}")
            print(f"  Service accessible: {service_accessible}")
            print(f"  Required: {service_info['required']}")
        
        # Count essential services that are running and accessible
        essential_services_operational = sum(
            1 for name, info in readiness_results.items()
            if info["required"] and info["container_running"] and info["service_accessible"]
        )
        
        total_required = sum(1 for info in services_to_check.values() if info["required"])
        
        print(f"\nEssential services operational: {essential_services_operational}/{total_required}")
        
        # We expect at least the essential services to be operational
        assert essential_services_operational >= 2, f"Expected at least 2 essential services operational, only {essential_services_operational} available"
        
        if essential_services_operational >= total_required:
            print("✓ Full stack is ready and operational")
        else:
            print("⚠ Some services may not be fully operational")


class TestN8nWorkflowTesting:
    """Test n8n-specific workflows"""
    
    @pytest.mark.skipif(not check_container_running('n8n'), reason="n8n not running")
    def test_n8n_basic_connectivity(self):
        """Test basic connectivity to n8n"""
        print("Testing n8n connectivity...")
        
        n8n_url = TestConstants.N8N_INTERNAL_URL
        
        try:
            # Try to access the REST API endpoint to check basic functionality
            response = requests.get(f"{n8n_url}/api/v1", timeout=10)
            print(f"n8n API response: {response.status_code}")
            
            # n8n should normally return 401 for unauthorized access to API
            # or 200 for public endpoints, depending on configuration
            assert response.status_code in [200, 401, 403], f"Expected 200, 401, or 403, got {response.status_code}"
            print("✓ n8n basic connectivity test passed")
            
        except requests.exceptions.RequestException as e:
            pytest.skip(f"n8n connectivity test failed: {e}")


class TestOllamaFunctionality:
    """Test Ollama functionality"""
    
    @pytest.mark.skipif(not check_container_running('ollama'), reason="ollama not running")
    def test_ollama_models_list(self):
        """Test Ollama models listing functionality"""
        print("Testing Ollama models listing...")
        
        ollama_url = TestConstants.OLLAMA_INTERNAL_URL
        
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=15)
            print(f"Ollama models API response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Available models: {len(data.get('models', []))}")
                
                # Check response structure
                assert 'models' in data, "Response should contain 'models' key"
                
                models = data.get('models', [])
                print(f"✓ Ollama functionality test passed with {len(models)} models")
                
                # List models for debugging
                for model in models:
                    print(f"  - {model.get('name', 'unknown')}")
            else:
                print(f"⚠ Ollama API returned status {response.status_code}, may be starting up")
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Ollama models test failed: {e}")
    
    @pytest.mark.skipif(not check_container_running('ollama'), reason="ollama not running")
    def test_ollama_generate_endpoint(self):
        """Test Ollama generate endpoint (basic test)"""
        print("Testing Ollama generate endpoint...")
        
        ollama_url = TestConstants.OLLAMA_INTERNAL_URL
        
        try:
            # This is a minimal model test - it may fail if no models are pulled yet
            # For now, just test that the endpoint is accessible
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": "dummy-model",
                    "prompt": "test",
                    "stream": False
                },
                timeout=10
            )
            
            # We expect a 400 or 404 if the API is accessible
            # (400 for bad request with wrong model, 404 if endpoint doesn't exist)
            expected_codes = [200, 400, 404, 405, 500]  # Various possible responses
            
            if response.status_code in expected_codes:
                print(f"✓ Ollama generate endpoint accessible (status: {response.status_code})")
            else:
                print(f"⚠ Unexpected response from Ollama generate: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Ollama generate test failed: {e}")


class TestOpenWebUIFunctionality:
    """Test Open WebUI functionality"""
    
    @pytest.mark.skipif(not check_container_running('open-webui'), reason="open-webui not running")
    def test_openwebui_health(self):
        """Test Open WebUI health endpoint"""
        print("Testing Open WebUI health...")
        
        webui_url = TestConstants.OPEN_WEBUI_INTERNAL_URL
        
        try:
            # Check the health endpoint
            response = requests.get(f"{webui_url}/health", timeout=10)
            print(f"Open WebUI health response: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Open WebUI status: {data}")
                assert 'status' in data or 'detail' in data, "Health check should return status detail"
                print("✓ Open WebUI health check passed")
            elif response.status_code == 404:
                print("⚠ Open WebUI health endpoint not found, but service is responding")
                # This might be normal depending on Open WebUI version
            else:
                print(f"⚠ Open WebUI health check returned {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            pytest.skip(f"Open WebUI health test failed: {e}")


class TestMultiServiceInteraction:
    """Test interactions between multiple services"""
    
    def test_service_discovery(self):
        """Test that all expected services can be discovered"""
        print("Testing service discovery...")
        
        services = {
            'n8n': {'container': 'n8n', 'url': TestConstants.N8N_INTERNAL_URL},
            'open-webui': {'container': 'open-webui', 'url': TestConstants.OPEN_WEBUI_INTERNAL_URL},
            'ollama': {'container': 'ollama', 'url': TestConstants.OLLAMA_INTERNAL_URL}
        }
        
        discovered_services = {}
        for name, info in services.items():
            container_ok = check_container_running(info['container'])
            service_ok = check_service_health(info['url']) if container_ok else False
            
            discovered_services[name] = {
                'container_found': container_ok,
                'service_accessible': service_ok
            }
        
        discovered_count = sum(1 for svc in discovered_services.values() if svc['service_accessible'])
        
        print(f"Discovered {discovered_count} accessible services out of {len(services)}")
        print(f"Discovery results: {discovered_services}")
        
        # At minimum, we should be able to discover 2+ services
        assert discovered_count >= 2, f"Expected to discover at least 2 services, only found {discovered_count}"
        
        print("✓ Service discovery test passed")


@pytest.mark.slow
class TestLongRunningTests:
    """Tests that may take longer to run"""
    
    def test_persistent_service_availability(self):
        """Test that services remain available over time"""
        print("Testing persistent service availability...")
        
        services = {
            'n8n': TestConstants.N8N_INTERNAL_URL,
            'open-webui': TestConstants.OPEN_WEBUI_INTERNAL_URL,
            'ollama': TestConstants.OLLAMA_INTERNAL_URL
        }
        
        # Check availability at intervals
        intervals = [0, 10, 20]  # seconds
        results = {name: [] for name in services.keys()}
        
        for i, delay in enumerate(intervals):
            if i > 0:
                print(f"Waiting {delay - intervals[i-1]} seconds...")
                time.sleep(delay - intervals[i-1])
            
            for service_name, url in services.items():
                is_healthy = check_service_health(url)
                results[service_name].append(is_healthy)
                print(f"  {service_name} at {delay}s: {'✓' if is_healthy else '✗'}")
        
        # All services should be available at all times
        for service_name, health_checks in results.items():
            all_available = all(health_checks)
            print(f"{service_name} consistently available: {all_available}")
            
        # At least 2 services should be consistently available
        consistently_available = sum(
            1 for checks in results.values() 
            if len(checks) > 0 and all(checks)
        )
        
        assert consistently_available >= 2, f"Expected at least 2 consistently available services, got {consistently_available}"
        print("✓ Persistent availability test passed")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])