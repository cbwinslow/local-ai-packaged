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

### Setting Up the Environment for Development
A crucial step for setting up the development environment is creating the `.env` file with all the necessary secrets and configuration. This project has a streamlined process for this.

1.  **Understand the Template**: The file `.env.example` is the template for all required environment variables. It is the source of truth for what the application needs.

2.  **Populate the `.env` file**: The primary script for creating your `.env` file is `scripts/populate-env-from-bitwarden.sh`. This script is a wrapper that calls a more advanced Python script (`scripts/populate_secrets.py`) to handle the logic.

3.  **Execution for Agents**: As an agent, you likely do not have access to the user's Bitwarden vault. Therefore, you should always use the `--generate-missing` flag. This will populate the `.env` file by generating new, random secrets for internal services, and it will insert placeholders for external API keys that you may need to ask the user for.

    **Example command to set up the environment:**
    ```bash
    # Make sure the script is executable
    chmod +x scripts/populate-env-from-bitwarden.sh

    # Run the script to generate the .env file
    ./scripts/populate-env-from-bitwarden.sh --generate-missing
    ```

4.  **Manual Intervention**: After the script runs, the `.env` file will be created. If the task requires external API keys (e.g., `OPENAI_API_KEY`), you will need to inform the user that they must manually edit the `.env` file to add these keys. The script will have inserted a placeholder like `BITWARDEN_SECRET_MISSING_OPENAI_API_KEY` to make this clear.
