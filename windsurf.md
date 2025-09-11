# Windsurf Repository Guide

This document provides comprehensive instructions for working with the Windsurf repository.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Development Workflow](#development-workflow)
- [Project Structure](#project-structure)
- [Common Commands](#common-commands)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- Python 3.10
- Docker and Docker Compose
- UV package manager
- Git

## Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd local-ai-packaged
```

### 2. Set Up Python Environment
```bash
# Install UV if not already installed
curl -sSf https://astral.sh/uv/install.sh | sh

# Create and activate virtual environment
uv venv .venv --python=3.10
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the example environment file and update with your values:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Development Workflow

### Branching Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Feature branches
- `bugfix/*`: Bug fix branches

### Making Changes
1. Create a new branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests: `uv run pytest`
4. Commit changes: `git commit -m "Description of changes"`
5. Push to remote: `git push origin feature/your-feature-name`
6. Create a pull request

## Project Structure

```
.
├── .github/              # GitHub workflows and templates
├── agentic-knowledge-rag-graph/  # RAG graph implementation
├── config/               # Configuration files
├── dashboard/            # Dashboard frontend
├── db/                   # Database migrations and models
├── docs/                 # Documentation
├── flowise/              # Flowise configurations
├── n8n/                  # n8n workflows
├── n8n-tool-workflows/   # n8n tool configurations
├── reports/              # Generated reports
├── scripts/              # Utility scripts
├── services/             # Backend services
├── tests/                # Test files
├── tools/                # Development tools
└── traefik/             # Traefik configuration
```

## Common Commands

### Development
```bash
# Start all services
docker-compose up -d

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run flake8
```

### Database
```bash
# Run migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "Description of changes"
```

## Troubleshooting

### Database Connection Issues
- Ensure PostgreSQL is running
- Verify credentials in `.env`
- Check if the database exists and is accessible

### Dependency Issues
- Delete `.venv` and recreate it
- Run `uv pip install -r requirements.txt`

### Service Issues
- Check logs: `docker-compose logs <service-name>`
- Restart services: `docker-compose restart`
