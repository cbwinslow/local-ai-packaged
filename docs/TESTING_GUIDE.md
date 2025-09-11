# Testing Guide

This guide covers the comprehensive testing strategy for the Local AI Package.

## Overview

The Local AI Package includes a multi-layered testing approach:

- **Unit Tests**: Test individual components and functions
- **Integration Tests**: Test service interactions and workflows
- **Security Tests**: Validate security configurations and secrets
- **Infrastructure Tests**: Validate Docker and Terraform configurations
- **Smoke Tests**: Basic functionality verification

## Quick Start

```bash
# Run all tests
python scripts/run-tests.py

# Run specific test categories
python scripts/run-tests.py --category unit
python scripts/run-tests.py --category integration
python scripts/run-tests.py --category security

# Run tests with coverage
python scripts/run-tests.py --coverage

# Generate HTML report
python scripts/run-tests.py --html-report
```

## Test Categories

### Unit Tests
```bash
python scripts/run-tests.py --category unit
```

Tests individual functions and classes:
- Configuration parsing
- Utility functions
- Data processing
- API endpoints

### Integration Tests
```bash
python scripts/run-tests.py --category integration
```

Tests service interactions:
- Database connections
- API integrations
- Workflow orchestration
- Service communication

### Security Tests
```bash
python scripts/run-tests.py --category security
```

Tests security aspects:
- Secret generation quality
- Environment variable security
- Container security configurations
- Access control validation

### Docker Tests
```bash
python scripts/run-tests.py --category docker
```

Tests Docker configurations:
- Compose file syntax
- Service definitions
- Network configurations
- Volume mappings
- Health checks

### Terraform Tests
```bash
python scripts/run-tests.py --category terraform
```

Tests infrastructure as code:
- Terraform syntax validation
- Resource configuration
- Security best practices
- Output definitions

### Smoke Tests
```bash
python scripts/run-tests.py --category smoke
```

Basic functionality tests:
- Service availability
- Configuration loading
- Essential workflows

## Test Configuration

### Pytest Configuration

Tests are configured in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["-v", "--tb=short", "--color=yes"]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
    "security: marks tests as security-related",
    "docker: marks tests that require Docker",
    "terraform: marks tests that require Terraform CLI",
    "network: marks tests that require network access",
    "unit: marks tests as unit tests",
    "smoke: marks tests as smoke tests"
]
```

### Test Markers

Use markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_configuration_parsing():
    """Test configuration parsing logic"""
    pass

@pytest.mark.integration
@pytest.mark.slow
def test_database_connection():
    """Test database connection and queries"""
    pass

@pytest.mark.security
def test_secret_generation():
    """Test secret generation quality"""
    pass
```

## Writing Tests

### Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── test_docker_compose.py   # Docker configuration tests
├── test_secrets.py          # Security and secrets tests
├── test_terraform.py        # Terraform configuration tests
├── test_ai_services.py      # AI service tests
├── test_utils.py           # Utility function tests
└── integration/
    ├── __init__.py
    └── test_service_manager.py  # Integration tests
```

### Fixtures

Common fixtures in `conftest.py`:

```python
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    """Get project root directory"""
    return Path(__file__).parent.parent

@pytest.fixture
def temp_env_file(tmp_path):
    """Create temporary .env file"""
    env_file = tmp_path / ".env"
    env_file.write_text("TEST_VAR=test_value\n")
    return env_file
```

### Test Examples

#### Unit Test Example

```python
def test_secret_generation():
    """Test that secrets are generated with proper entropy"""
    from scripts.generate_secrets import generate_secret
    
    secret = generate_secret(32)
    assert len(secret) == 64  # 32 bytes = 64 hex chars
    assert all(c in '0123456789abcdef' for c in secret.lower())
```

#### Integration Test Example

```python
@pytest.mark.integration
def test_service_communication():
    """Test that services can communicate"""
    # Setup test services
    # Test actual communication
    # Verify responses
    pass
```

#### Security Test Example

```python
@pytest.mark.security
def test_no_hardcoded_secrets():
    """Ensure no hardcoded secrets in configuration"""
    config_files = glob.glob("**/*.yml", recursive=True)
    for file in config_files:
        content = Path(file).read_text()
        assert "password123" not in content.lower()
        assert "secret123" not in content.lower()
```

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Pull requests
- Pushes to main branch
- Scheduled runs (nightly)

Configuration in `.github/workflows/ci.yml`:

```yaml
- name: Run tests
  run: |
    python scripts/run-tests.py --category all --coverage --html-report
```

### Test Reports

Test reports are generated in multiple formats:
- **Console output**: Real-time test results
- **HTML report**: `reports/pytest-report.html`
- **Coverage report**: `reports/coverage/`
- **JUnit XML**: For CI integration

## Performance Testing

### Load Testing

Use pytest-benchmark for performance tests:

```python
def test_configuration_loading_performance(benchmark):
    """Test configuration loading performance"""
    result = benchmark(load_configuration, "config.yml")
    assert result is not None
```

### Memory Testing

Monitor memory usage:

```python
import psutil
import pytest

def test_memory_usage():
    """Test that operations don't leak memory"""
    process = psutil.Process()
    initial_memory = process.memory_info().rss
    
    # Perform operations
    perform_heavy_operation()
    
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Allow for some memory increase but not excessive
    assert memory_increase < 100 * 1024 * 1024  # 100MB limit
```

## Test Data Management

### Test Fixtures

Use temporary directories for test data:

```python
@pytest.fixture
def sample_data(tmp_path):
    """Create sample test data"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    (data_dir / "sample.txt").write_text("test content")
    return data_dir
```

### Database Testing

Use test databases:

```python
@pytest.fixture
def test_database():
    """Setup test database"""
    # Create test database
    # Populate with test data
    yield database_connection
    # Cleanup
```

## Coverage Requirements

### Coverage Targets

- **Overall coverage**: 70% minimum
- **Core modules**: 85% minimum
- **Security modules**: 95% minimum

### Coverage Reports

Generate coverage reports:

```bash
# Terminal report
python scripts/run-tests.py --coverage

# HTML report
python scripts/run-tests.py --coverage --html-report

# XML report (for CI)
pytest --cov=. --cov-report=xml
```

## Debugging Tests

### Running Individual Tests

```bash
# Run specific test file
pytest tests/test_secrets.py -v

# Run specific test function
pytest tests/test_secrets.py::test_secret_generation -v

# Run with debugging
pytest tests/test_secrets.py::test_secret_generation -v -s --pdb
```

### Test Debugging Tips

1. Use `pytest -s` to see print statements
2. Use `pytest --pdb` to drop into debugger on failures
3. Use `pytest -x` to stop on first failure
4. Use `pytest --lf` to run only last failed tests

## Best Practices

### Test Organization

1. **One test per function**: Keep tests focused
2. **Descriptive names**: Use clear test function names
3. **Test isolation**: Tests should not depend on each other
4. **Mock external dependencies**: Use mocks for external services

### Test Data

1. **Use fixtures**: Share common test setup
2. **Temporary files**: Use `tmp_path` for file operations
3. **Clean up**: Ensure tests clean up after themselves
4. **Realistic data**: Use realistic test data

### Performance

1. **Mark slow tests**: Use `@pytest.mark.slow`
2. **Parallel execution**: Use `pytest-xdist` for faster runs
3. **Skip expensive tests**: Skip tests that require external resources
4. **Cache test data**: Cache expensive test data generation

## Troubleshooting

### Common Issues

1. **Import errors**: Check PYTHONPATH and module structure
2. **Permission errors**: Ensure proper file permissions
3. **Resource conflicts**: Use unique temporary directories
4. **External dependencies**: Mock or skip tests requiring external services

### Environment Issues

1. **Missing dependencies**: Install test dependencies
2. **Docker not available**: Skip Docker-related tests
3. **Network issues**: Skip network-dependent tests
4. **Permission issues**: Run with appropriate permissions

### CI/CD Issues

1. **Timeout errors**: Increase test timeouts
2. **Resource limits**: Reduce parallel test execution
3. **Environment differences**: Use containerized testing
4. **Flaky tests**: Identify and fix non-deterministic tests