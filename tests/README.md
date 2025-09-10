# Testing Framework for Government Data Pipeline

This directory contains the testing framework for the government data pipeline, including utilities for testing AI services, tracking API rate limits, and generating test data.

## Directory Structure

```
tests/
├── test_utils.py          # Core test utilities for AI services
├── test_ai_services.py    # Unit tests for AI service diagnostics
├── gov_apis.py           # Government API documentation and rate limit tracker
├── generate_test_data.py  # Script to generate mock test data
└── test_data/            # Generated test data files
    ├── bills.json        # Mock bill data (Congress API format)
    ├── regulations.json  # Mock regulation data (Regulations.gov format)
    └── spending.json     # Mock spending data (USAspending format)
```

## Test Utilities

The `test_utils.py` module provides base classes for testing AI services like LocalAI and Ollama. It includes:

- `AIDiagnostics`: Base class for AI service diagnostics
- `LocalAIDiagnostics`: Implementation for LocalAI service
- `OllamaDiagnostics`: Implementation for Ollama service
- `ServiceHealth`: Dataclass for service health status
- `run_diagnostics()`: Function to run comprehensive diagnostics

## Government API Tracker

The `gov_apis.py` module documents various government API endpoints and their rate limits, and provides a `GovAPITracker` class to help respect those limits.

### Supported APIs

- **GovInfo Bulk Data**: No rate limit, but be considerate of server load
- **ProPublica Congress API**: 5 requests per second (API key required)
- **Regulations.gov API**: 1,000 requests per minute (API key required)
- **Federal Register API**: 10 requests per second (API key required)
- **USAspending API**: 60 requests per minute

## Test Data Generation

The `generate_test_data.py` script generates realistic mock data for testing:

- **Bills**: Simulates data from the Congress API
- **Regulations**: Simulates data from Regulations.gov
- **Spending**: Simulates data from USAspending

### Generating Test Data

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install faker
   ```

3. Run the data generator:
   ```bash
   python tests/generate_test_data.py
   ```

   This will create a `test_data` directory with JSON files containing the generated data.

## Running Tests

To run the unit tests:

```bash
# Run all tests
python -m pytest tests/

# Run a specific test file
python -m pytest tests/test_ai_services.py -v
```

## Example Usage

### Checking AI Service Health

```python
from test_utils import run_diagnostics

# Check LocalAI health
localai_results = run_diagnostics(
    service_url="http://localhost:8080",
    service_type="localai"
)
print(json.dumps(localai_results, indent=2))

# Check Ollama health
ollama_results = run_diagnostics(
    service_url="http://localhost:11434",
    service_type="ollama"
)
```

### Tracking API Rate Limits

```python
from gov_apis import GovAPITracker

# Initialize the tracker
tracker = GovAPITracker()

# Get an endpoint
endpoint = tracker.get_endpoint("ProPublica Congress API")

# Record a request (this will enforce rate limits)
tracker.record_request("ProPublica Congress API")

# Make your API request here
# response = requests.get(...)
```

## Best Practices

1. **Respect Rate Limits**: Always use the `GovAPITracker` to respect API rate limits
2. **Use Mock Data**: Generate and use test data during development to avoid unnecessary API calls
3. **Handle Errors**: Implement proper error handling for API requests
4. **Logging**: Use the built-in logging to track API usage and errors
5. **Secure Credentials**: Never commit API keys or sensitive information to version control

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
