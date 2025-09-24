.PHONY: all build test lint deploy ci-local deploy-staging clean validate e2e health ansible-deploy ansible-monitor ansible-backup ansible-config ansible-ai-agent ansible-site

# Local AI Packaged Makefile - Full Targets

# Env validation
validate:
	./scripts/validate_env.sh

# Build Docker images
build:
	docker-compose build

# Run tests (unit + E2E)
test: validate
	docker-compose run backend pytest
	docker-compose run frontend npm test
	docker-compose run frontend npm run e2e

# Lint code
lint:
	pre-commit run --all-files

# Deploy with Docker Compose
deploy:
	docker-compose up -d

# Local CI (validate/lint/test/build)
ci-local: validate lint test
	docker build -t local-ai-backend:latest .
	docker build -f frontend/Dockerfile -t local-ai-frontend:latest ./frontend

# Deploy to staging K8s
deploy-staging:
	kubectl apply -f k8s/

# Clean services/volumes
clean:
	docker-compose down -v

# E2E tests
e2e:
	docker-compose up -d frontend backend
	docker-compose run frontend npm run e2e
	docker-compose down

# Health check
health:
	./scripts/health-check.sh

# Ansible Targets (bare-metal/prod)
ansible-deploy:
	ansible-playbook -i ansible/inventory.ini ansible/playbooks/deploy.yml

ansible-monitor:
	ansible-playbook -i ansible/inventory.ini ansible/playbooks/monitor.yml

ansible-backup:
	ansible-playbook -i ansible/inventory.ini ansible/playbooks/backup.yml

ansible-config:
	ansible-playbook -i ansible/inventory.ini ansible/playbooks/config.yml

ansible-ai-agent:
	ansible-playbook -i ansible/inventory.ini ansible/playbooks/ai-agent.yml

# Full Ansible site playbook
ansible-site:
	ansible-playbook -i ansible/inventory.ini ansible/site.yml

# Default: all
all: validate build test