# ========================================================================================
# Local AI Package - Makefile
# ========================================================================================
# Provides convenient shortcuts for common operations
# ========================================================================================

.PHONY: help setup start stop restart health backup restore clean lint test docs

# Default target
help: ## Show this help message
	@echo "Local AI Package - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make setup          # Complete initial setup"
	@echo "  make start           # Start all services"
	@echo "  make health          # Check system health"
	@echo "  make backup          # Create backup"
	@echo "  make clean           # Clean everything"

# Setup and Installation
setup: ## Complete initial setup with secrets generation
	@echo "🚀 Setting up Local AI Package..."
	@./scripts/generate-secrets.sh
	@echo "✅ Setup complete! Run 'make start' to launch services."

setup-dev: ## Setup development environment with dependencies
	@echo "🛠️  Setting up development environment..."
	@pip install uv
	@uv sync --dev
	@pre-commit install
	@./scripts/generate-secrets.sh
	@echo "✅ Development environment ready!"

# Service Management
start: ## Start all services (CPU profile, private environment)
	@echo "🚀 Starting Local AI Package..."
	@./scripts/start-all-services.sh --profile cpu --environment private

start-gpu: ## Start with NVIDIA GPU acceleration
	@echo "🚀 Starting Local AI Package with GPU acceleration..."
	@./scripts/start-all-services.sh --profile gpu-nvidia --environment private

start-gpu-amd: ## Start with AMD GPU acceleration
	@echo "🚀 Starting Local AI Package with AMD GPU acceleration..."
	@./scripts/start-all-services.sh --profile gpu-amd --environment private

start-public: ## Start in public/production mode
	@echo "🚀 Starting Local AI Package in public mode..."
	@./scripts/start-all-services.sh --profile cpu --environment public

stop: ## Stop all services
	@echo "🛑 Stopping Local AI Package..."
	@docker-compose --project-name localai down

restart: ## Restart all services
	@echo "🔄 Restarting Local AI Package..."
	@make stop
	@sleep 5
	@make start

# Health and Monitoring
health: ## Run comprehensive health check
	@echo "🔍 Running health check..."
	@./scripts/health-check.sh

status: ## Show service status
	@echo "📊 Service Status:"
	@docker-compose ps

logs: ## Show logs for all services
	@echo "📋 Service Logs:"
	@docker-compose logs --tail=50 -f

logs-service: ## Show logs for specific service (usage: make logs-service SERVICE=n8n)
	@echo "📋 Logs for $(SERVICE):"
	@docker-compose logs --tail=100 -f $(SERVICE)

# Data Operations
ingest: ## Run full data ingestion
	@echo "📊 Starting data ingestion..."
	@python scripts/government-data-ingestion.py --mode full

ingest-congress: ## Ingest Congress data only
	@echo "🏛️ Ingesting Congress data..."
	@python scripts/government-data-ingestion.py --mode congress

ingest-declassified: ## Ingest declassified documents
	@echo "🔒 Ingesting declassified documents..."
	@python scripts/government-data-ingestion.py --mode declassified

# Backup and Recovery
backup: ## Create full backup
	@echo "💾 Creating backup..."
	@./scripts/backup-restore.sh backup

backup-configs: ## Backup configurations only
	@echo "💾 Backing up configurations..."
	@./scripts/backup-restore.sh backup --include configs

backup-databases: ## Backup databases only
	@echo "💾 Backing up databases..."
	@./scripts/backup-restore.sh backup --include databases

list-backups: ## List available backups
	@echo "📋 Available backups:"
	@./scripts/backup-restore.sh list

restore: ## Restore from backup (usage: make restore BACKUP=backup_20240101)
	@echo "🔄 Restoring from backup $(BACKUP)..."
	@./scripts/backup-restore.sh restore --backup-name $(BACKUP)

cleanup-backups: ## Clean old backups (30 days retention)
	@echo "🧹 Cleaning old backups..."
	@./scripts/backup-restore.sh cleanup --retention-days 30

# Maintenance
update: ## Update Docker images
	@echo "🔄 Updating Docker images..."
	@docker-compose pull
	@echo "✅ Images updated. Run 'make restart' to apply updates."

clean: ## Stop services and clean Docker resources
	@echo "🧹 Cleaning Docker resources..."
	@docker-compose --project-name localai down -v --remove-orphans
	@docker system prune -f
	@echo "✅ Cleanup complete!"

clean-all: ## Clean everything including images and volumes
	@echo "🧹 Deep cleaning all Docker resources..."
	@docker-compose --project-name localai down -v --remove-orphans
	@docker system prune -a -f --volumes
	@echo "✅ Deep cleanup complete!"

reset: ## Reset everything and restart fresh
	@echo "🔄 Resetting Local AI Package..."
	@make clean-all
	@make setup
	@make start

# Development
lint: ## Run code linting
	@echo "🔍 Running code linting..."
	@python -m black scripts/ --line-length 127
	@python -m isort scripts/ --profile black --line-length 127
	@python -m flake8 scripts/ --max-line-length=127 --ignore=E203,W503

lint-check: ## Check code formatting without changing files
	@echo "🔍 Checking code formatting..."
	@python -m black scripts/ --line-length 127 --check
	@python -m isort scripts/ --profile black --line-length 127 --check-only
	@python -m flake8 scripts/ --max-line-length=127 --ignore=E203,W503

test: ## Run tests
	@echo "🧪 Running tests..."
	@python -m pytest tests/ -v

test-coverage: ## Run tests with coverage report
	@echo "🧪 Running tests with coverage..."
	@python -m pytest tests/ --cov=scripts --cov-report=html --cov-report=term

# Troubleshooting
diagnose: ## Run comprehensive system diagnostics
	@echo "🔍 Running system diagnostics..."
	@./scripts/port-conflict-resolver.sh scan
	@./scripts/health-check.sh
	@echo "📋 Docker system info:"
	@docker system df
	@echo "📋 Docker compose services:"
	@docker-compose ps -a

fix-ports: ## Resolve port conflicts
	@echo "🔧 Resolving port conflicts..."
	@./scripts/port-conflict-resolver.sh resolve private

fix-permissions: ## Fix file permissions
	@echo "🔧 Fixing file permissions..."
	@chmod +x scripts/*.sh
	@chmod 600 .env* 2>/dev/null || true

# Documentation
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@echo "Documentation available:"
	@echo "  📖 README: README_COMPREHENSIVE.md"
	@echo "  🐳 Docker: docs/docker-optimization-plan.md"
	@echo "  📊 Monitoring: docs/COMPREHENSIVE-REPOSITORY-DOCUMENTATION.md"
	@echo "  🔌 Ports: docs/PORT_REFERENCE.md"

docs-serve: ## Serve documentation locally
	@echo "📚 Serving documentation..."
	@python -m http.server 8000 --directory docs/

# Environment Management
env-template: ## Create .env from template
	@echo "⚙️ Creating .env from template..."
	@cp .env.template .env
	@echo "✅ .env created. Edit the file and run 'make setup' to generate secrets."

env-validate: ## Validate environment configuration
	@echo "✅ Validating environment configuration..."
	@python -c "
import os
from pathlib import Path
env_file = Path('.env')
if not env_file.exists():
    print('❌ .env file not found')
    exit(1)
required_vars = ['POSTGRES_PASSWORD', 'JWT_SECRET', 'N8N_ENCRYPTION_KEY']
with open('.env') as f:
    content = f.read()
missing = [var for var in required_vars if f'{var}=' not in content or f'{var}=your-' in content]
if missing:
    print(f'❌ Missing variables: {missing}')
    exit(1)
print('✅ Environment configuration is valid')
"

# Quick Actions
quick-start: ## Quick start for first-time users
	@echo "🚀 Quick Start - Local AI Package"
	@echo "1. Setting up environment..."
	@make setup
	@echo "2. Starting services..."
	@make start
	@echo "3. Running health check..."
	@sleep 60
	@make health
	@echo ""
	@echo "🎉 Local AI Package is ready!"
	@echo "📱 Access the dashboard: http://localhost:3006"
	@echo "🌐 Frontend application: http://localhost:3000"
	@echo "🔄 N8N workflows: http://localhost:5678"

demo: ## Start demo with sample data
	@echo "🎬 Starting demo environment..."
	@make start
	@echo "⏳ Waiting for services to initialize..."
	@sleep 90
	@echo "📊 Running sample data ingestion..."
	@python scripts/government-data-ingestion.py --mode congress &
	@echo "🎉 Demo environment ready!"
	@echo "Visit http://localhost:3006 to explore the platform"

# Version and Info
version: ## Show version information
	@echo "Local AI Package v2.0.0"
	@echo "Components:"
	@echo "  🐳 Docker: $(shell docker --version 2>/dev/null || echo 'Not available')"
	@echo "  🐍 Python: $(shell python --version 2>/dev/null || echo 'Not available')"
	@echo "  📦 UV: $(shell uv --version 2>/dev/null || echo 'Not available')"

info: ## Show system information
	@echo "Local AI Package - System Information"
	@echo "===================================="
	@echo "🖥️  OS: $(shell uname -s)"
	@echo "🏗️  Architecture: $(shell uname -m)"
	@echo "💾 Disk space: $(shell df -h . | tail -1 | awk '{print $$4}') available"
	@echo "🧠 Memory: $(shell free -h 2>/dev/null | grep '^Mem:' | awk '{print $$7}' || echo 'N/A') available"
	@echo "🐳 Docker: $(shell docker --version 2>/dev/null || echo 'Not installed')"
	@echo "📁 Project directory: $(shell pwd)"
	@echo "📊 Services running: $(shell docker-compose ps --services --filter status=running 2>/dev/null | wc -l)"

# Aliases for convenience
build: start ## Alias for start
run: start ## Alias for start
deploy: start-public ## Alias for start-public
up: start ## Alias for start
down: stop ## Alias for stop
ps: status ## Alias for status