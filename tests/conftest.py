"""
Pytest configuration for Local AI Package tests
"""

import pytest
import sys
from pathlib import Path

# Add the tests directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def pytest_configure(config):
    """Configure pytest settings"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "docker: marks tests as requiring Docker"
    )
    config.addinivalue_line(
        "markers", "api: marks tests as API tests"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests as authentication tests"
    )
    config.addinivalue_line(
        "markers", "database: marks tests as database tests"
    )
    config.addinivalue_line(
        "markers", "ai_model: marks tests as AI model tests"
    )


@pytest.fixture(scope="session")
def docker_client():
    """Shared Docker client fixture"""
    import docker
    try:
        client = docker.from_env()
        yield client
        # Cleanup if needed
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")


@pytest.fixture(scope="session")
def active_services():
    """Get list of active services before running tests"""
    from utils.test_utils import get_active_services
    return get_active_services()


@pytest.fixture(scope="session")
def test_constants():
    """Provide test constants"""
    from utils.test_utils import TestConstants
    return TestConstants()


@pytest.fixture(autouse=True)
def skip_if_no_service(request, active_services):
    """Automatically skip tests if required services are not available"""
    # Check if test has specific service requirements
    service_marker = request.node.get_closest_marker("service_required")
    if service_marker:
        required_service = service_marker.args[0] if service_marker.args else None
        if required_service and required_service not in active_services:
            pytest.skip(f"Required service {required_service} not running")


@pytest.fixture
def wait_for_service():
    """Provide service wait utility"""
    from utils.test_utils import wait_for_service
    return wait_for_service


@pytest.fixture
def check_service_health():
    """Provide service health check utility"""
    from utils.test_utils import check_service_health
    return check_service_health