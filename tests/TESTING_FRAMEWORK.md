# Testing Framework for Local AI Package

## Test Structure

```
tests/
├── unit/               # Unit tests for individual functions/modules
│   ├── test_utils_unit.py
│   └── ...
├── integration/        # Integration tests for service interactions
│   ├── test_service_integration.py
│   └── ...
├── e2e/              # End-to-end tests for complete workflows
│   ├── test_e2e_workflows.py
│   └── ...
├── utils/            # Test utilities and helpers
│   └── test_utils.py
├── requirements.txt  # Test dependencies
└── conftest.py      # Pytest configuration
```

## Running Tests

### Prerequisites
```bash
pip install -r tests/requirements.txt
```

### Running Specific Test Types

**Unit Tests:**
```bash
pytest tests/unit/ -v
```

**Integration Tests:**
```bash
pytest tests/integration/ -v
```

**End-to-End Tests:**
```bash
pytest tests/e2e/ -v
```

**All Tests:**
```bash
pytest tests/ -v
```

### Running with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Running Specific Markers
```bash
# Run only integration tests
pytest -m integration

# Run only e2e tests  
pytest -m e2e

# Run slow tests
pytest -m slow
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Individual function testing
- Utility functions
- Component-specific tests
- Fast execution, minimal dependencies

### Integration Tests (`tests/integration/`)
- Multi-service interactions
- Docker container communication
- API endpoint testing
- Service health checks
- Data flow verification

### End-to-End Tests (`tests/e2e/`)
- Complete workflow testing
- Full stack verification
- User journey simulation
- Long-running availability tests
- Multi-service coordination

## Available Test Markers

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.e2e` - End-to-end tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.docker` - Tests requiring Docker
- `@pytest.mark.api` - API-specific tests
- `@pytest.mark.auth` - Authentication tests
- `@pytest.mark.database` - Database tests
- `@pytest.mark.ai_model` - AI model tests

## Test Utilities

The `utils/test_utils.py` module provides:

- Service health checks
- Docker container management
- Wait and retry mechanisms
- Environment validation
- Constants and configuration

## Test Configuration

Test settings are in `pytest.ini`:
- Strict marker enforcement
- Coverage configuration
- Timeout settings
- Test discovery patterns

## Continuous Integration

For CI/CD integration, use:
```bash
pytest tests/ --junitxml=report.xml --cov=. --cov-report=term-missing
```

## Test Development Guidelines

1. **Use descriptive test names**: `test_[feature]_[condition]_[expected_result]`
2. **Follow Arrange-Act-Assert pattern**
3. **Use appropriate markers**
4. **Handle service dependencies gracefully**
5. **Include meaningful assertions**
6. **Add comprehensive docstrings**

## Skip Logic

Tests automatically skip when:
- Required services are not running
- Dependencies are missing
- Timeout conditions are met
- Environment requirements are not met