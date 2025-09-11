# AI Agent Guidelines

This document provides guidelines and instructions for AI agents working with this repository.

## Environment Setup

1. **Python Version**: Use Python 3.10
2. **Package Manager**: Use `uv` for dependency management
3. **Virtual Environment**: Always work within a virtual environment

## Workflow

### Before Making Changes
1. Check the current state of the repository
2. Review open issues and TODOs
3. Create a new branch for your changes

### Making Changes
1. Make small, focused changes
2. Test your changes locally
3. Document your changes
4. Update the TODO list as needed

### After Making Changes
1. Run tests
2. Update documentation
3. Create a pull request with a clear description

## Best Practices

- **Code Style**: Follow PEP 8 guidelines
- **Documentation**: Update relevant documentation when making changes
- **Environment**: Keep environment-specific configurations in `.env` files
- **Secrets**: Never commit secrets or sensitive information
- **Dependencies**: Keep dependencies up to date and document any additions

## Common Tasks

### Setting Up the Environment
```bash
# Install uv if not already installed
curl -sSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv .venv --python=3.10
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### Running Tests
```bash
uv run pytest
```

### Updating Dependencies
```bash
uv pip install package-name
uv pip freeze > requirements.txt
```
