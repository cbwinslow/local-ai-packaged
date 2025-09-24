#!/bin/bash
# Incremental Deployment Script for Local AI Packaged
# Implements the iterative process from docs/incremental-deployment.md
# Run from project root: bash scripts/incremental-deployment.sh
# Logs errors to docs/errors.md (append-only). Exits on failure; retry failed iteration.

set -e  # Exit on error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ERRORS_MD="$PROJECT_ROOT/docs/errors.md"
LOG_FILE="$PROJECT_ROOT/logs/incremental-deployment-$(date +%Y%m%d_%H%M%S).log"

# Ensure errors.md exists
touch "$ERRORS_MD"

log_error() {
  local error_num=$(grep -c '^### Error #' "$ERRORS_MD" 2>/dev/null || echo 0)
  local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  local desc="$1"
  local context="$2"
  local meaning="$3"
  local solution="$4"
  
  cat >> "$ERRORS_MD" << EOF

### Error #$(($error_num + 1))
**Description**: $desc

**Timestamp**: $timestamp

**Program/Context**: $context

**Meaning/Why**: $meaning

**Solution**:
$solution
EOF
  echo "Logged error #$((error_num + 1)) to $ERRORS_MD"
  exit 1
}

echo "Starting Incremental Deployment from $PROJECT_ROOT" | tee -a "$LOG_FILE"
echo "Log: $LOG_FILE"

# Iteration 1: Environment Setup
echo "=== Iteration 1: Environment Setup ===" | tee -a "$LOG_FILE"
cd "$PROJECT_ROOT"

# Step 1: Generate secrets
echo "Generating secrets..." | tee -a "$LOG_FILE"
if ! ./scripts/enhanced-generate-secrets.sh; then
  log_error "Secrets generation failed" "./scripts/enhanced-generate-secrets.sh" "Script exited non-zero; possible openssl missing" "Install openssl: sudo apt install openssl; rerun."
fi

# Step 2: Validate .env
echo "Validating .env..." | tee -a "$LOG_FILE"
if grep -q '\$(openssl' .env; then
  log_error ".env has placeholders" ".env validation" "Placeholders like \$(openssl not replaced; generation incomplete" "Rerun ./scripts/enhanced-generate-secrets.sh"
fi
if ! grep -q "POSTGRES_PASSWORD=" .env; then
  log_error ".env missing POSTGRES_PASSWORD" ".env validation" "Key var not populated" "Rerun generation script."
fi
echo "✅ .env validated" | tee -a "$LOG_FILE"

# Step 3: Create venv
echo "Creating venv..." | tee -a "$LOG_FILE"
uv venv .venv --python=3.10
source .venv/bin/activate
uv pip install -r requirements.txt
echo "✅ Venv setup complete" | tee -a "$LOG_FILE"

# Iteration 2: Dependency Installation
echo "=== Iteration 2: Dependency Installation ===" | tee -a "$LOG_FILE"
source .venv/bin/activate

# Backend deps
echo "Installing backend deps..." | tee -a "$LOG_FILE"
uv pip install pytest pytest-cov python-dotenv pyyaml requests pytest-mock

# Frontend deps
cd frontend
npm install
npm install lucide-react @testing-library/jest-dom @testing-library/react @testing-library/user-event jest jest-environment-jsdom
cd ..
echo "✅ Backend deps installed" | tee -a "$LOG_FILE"

# Docker deps (rebuild frontend)
echo "Rebuilding frontend Docker..." | tee -a "$LOG_FILE"
docker compose build --no-cache frontend
if [ $? -ne 0 ]; then
  log_error "Frontend build failed" "docker compose build frontend" "npm run build error in Dockerfile" "Check logs: docker compose logs frontend; fix TS in src/app/dashboard/page.tsx if needed."
fi
echo "✅ Frontend deps installed" | tee -a "$LOG_FILE"

# Iteration 3: Port Clearing and Partial Service Startup
echo "=== Iteration 3: Port Clearing and Partial Startup ===" | tee -a "$LOG_FILE"
# Kill ports
echo "Clearing ports..." | tee -a "$LOG_FILE"
sudo fuser -k 5432/tcp 6379/tcp 3000/tcp 5678/tcp 11434/tcp 6333/tcp 7474/tcp 9000/tcp 8080/tcp || true

# Reset
echo "Resetting Docker..." | tee -a "$LOG_FILE"
docker compose down -v

# Start core
echo "Starting core services (Postgres, Redis)..." | tee -a "$LOG_FILE"
docker compose up -d postgres redis
sleep 30

# Verify core
if ! docker compose ps | grep -q "postgres.*Up"; then
  log_error "Postgres not up" "docker compose up postgres" "Container status not Up" "Check logs: docker compose logs postgres; rerun down -v."
fi
if ! docker compose ps | grep -q "redis.*Up"; then
  log_error "Redis not up" "docker compose up redis" "Container status not Up" "Check logs: docker compose logs redis."
fi
echo "✅ Core services up" | tee -a "$LOG_FILE"

# Iteration 4: Full Service Startup
echo "=== Iteration 4: Full Service Startup ===" | tee -a "$LOG_FILE"
./scripts/start-all-services.sh || docker compose up -d --build
sleep 60

# Check status
if ! docker compose ps | grep -q "Up" | grep -q -v "0/0"; then
  log_error "Services not up" "docker compose up" "Not all containers Up" "Check logs: docker compose logs; fix env in .env."
fi
echo "✅ Full startup complete" | tee -a "$LOG_FILE"

# Iteration 5: Test Validation
echo "=== Iteration 5: Test Validation ===" | tee -a "$LOG_FILE"
source .venv/bin/activate

# Backend
pytest tests/ -v
if [ $? -ne 0 ]; then
  log_error "Pytest failed" "pytest tests/" "Tests failed (e.g., integration skips)" "Rerun Iteration 4; check services."
fi

# Frontend
cd frontend
npm test
if [ $? -ne 0 ]; then
  log_error "npm test failed" "npm test" "Jest errors (e.g., render fail)" "Rerun npm install; check mocks in __tests__."
fi
cd ..

# Coverage
pytest --cov=tests --cov-report=term-missing
echo "✅ Tests passed" | tee -a "$LOG_FILE"

# Iteration 6: Health Check and Final Validation
echo "=== Iteration 6: Health Check and Final Validation ===" | tee -a "$LOG_FILE"
./scripts/health-check.sh --check-all
if [ $? -ne 0 ]; then
  log_error "Health check failed" "./scripts/health-check.sh" "Services unhealthy (e.g., Traefik down)" "Check logs: docker compose logs traefik; rerun Iteration 4."
fi

# End-to-end curl
curl -s -H "apikey: $ANON_KEY" http://localhost:8000/health | grep "OK" > /dev/null && echo "✅ Supabase OK" || log_error "Supabase curl failed" "curl localhost:8000/health" "No OK response" "Wait 60s; rerun health check."
curl -s -f http://localhost:5678/healthz > /dev/null && echo "✅ n8n OK" || log_error "n8n curl failed" "curl localhost:5678/healthz" "Connection refused" "Check n8n logs."

# Reports
./scripts/generate_reports.py || echo "Reports optional; skipping."

echo "🎉 Deployment complete! All iterations passed." | tee -a "$LOG_FILE"
echo "Access: http://localhost:3000 (frontend), http://localhost:8000 (Supabase)." | tee -a "$LOG_FILE"
