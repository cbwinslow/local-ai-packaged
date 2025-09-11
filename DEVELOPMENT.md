# Development Guide

This document outlines the development workflow, coding standards, and contribution guidelines for the Local AI Package.

## Table of Contents
1. [Development Environment](#development-environment)
2. [Coding Standards](#coding-standards)
3. [Git Workflow](#git-workflow)
4. [Testing](#testing)
5. [Documentation](#documentation)
6. [Code Review Process](#code-review-process)
7. [Release Process](#release-process)

## Development Environment

### Prerequisites
- Python 3.10
- UV package manager
- Docker and Docker Compose
- Node.js 18+ (for frontend development)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/coleam00/local-ai-packaged.git
   cd local-ai-packaged
   ```

2. **Set up Python environment**
   ```bash
   uv venv .venv --python=3.10
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements-dev.txt
   ```

3. **Set up pre-commit hooks**
   ```bash
   pre-commit install
   ```

## Coding Standards

### Python
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints for all function parameters and return values
- Keep functions small and focused (max 50 lines)
- Write docstrings for all public functions and classes
- Use absolute imports

### JavaScript/TypeScript
- Follow [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- Use TypeScript for all new code
- Prefer functional components with hooks
- Use ESLint and Prettier for code formatting

### Git Commit Messages
- Use the [Conventional Commits](https://www.conventionalcommits.org/) specification
- Format: `type(scope): description`
- Types: feat, fix, docs, style, refactor, test, chore
- Example: `feat(auth): add Google OAuth integration`

## Git Workflow

### Branching Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches
- `release/*`: Release preparation branches

### Workflow
1. Create a new branch from `develop`
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit them
   ```bash
   git add .
   git commit -m "feat(component): add new feature"
   ```

3. Push your changes and create a pull request
   ```bash
   git push -u origin feature/your-feature-name
   ```

## Testing

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_module.py

# Run with coverage
uv run pytest --cov=src tests/
```

### Writing Tests
- Write unit tests for all new functionality
- Use the `pytest` framework
- Follow the Arrange-Act-Assert pattern
- Use fixtures for common test data
- Mock external dependencies

## Documentation

### Code Documentation
- Document all public APIs with docstrings
- Use Google-style docstrings for Python
- Use JSDoc for JavaScript/TypeScript

### Updating Documentation
1. Update inline documentation in the code
2. Update relevant sections in the docs directory
3. Update README.md if necessary
4. Update CHANGELOG.md for user-facing changes

## Code Review Process

1. Create a pull request from your feature branch to `develop`
2. Request review from at least one other developer
3. Address all review comments
4. Ensure all tests pass
5. Get approval from at least one reviewer
6. Rebase on the latest `develop` if needed
7. Squash and merge the PR

## Release Process

1. Create a release branch from `develop`
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b release/vX.Y.Z
   ```

2. Update version numbers and changelog
   - Update `__version__` in `src/__init__.py`
   - Update `CHANGELOG.md` with release notes

3. Create a pull request to merge into `main`
   ```bash
   git add .
   git commit -m "chore(release): prepare vX.Y.Z"
   git push -u origin release/vX.Y.Z
   ```

4. After PR is merged, create a GitHub release
   - Tag the release with `vX.Y.Z`
   - Attach release notes from CHANGELOG.md
   - Publish the release

5. Merge changes back to develop
   ```bash
   git checkout develop
   git merge --no-ff main
   git push origin develop
   ```

## Troubleshooting

### Common Issues

**Dependency Conflicts**
```bash
# Clean up environment
uv pip freeze | xargs uv pip uninstall -y
uv pip install -r requirements.txt
```

**Database Issues**
```bash
# Reset the test database
docker-compose -f docker-compose.test.yml down -v
docker-compose -f docker-compose.test.yml up -d
```

**Linting Issues**
```bash
# Auto-format Python code
uv run black .

# Auto-format JavaScript/TypeScript
uv run eslint --fix .
```

For additional help, check the [troubleshooting guide](TROUBLESHOOTING.md) or open an issue.
