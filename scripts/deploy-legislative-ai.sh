#!/bin/bash
set -e  # Exit on error

# Configurable variables
PROJECT_DIR="$(pwd)"
ENV_FILE="$PROJECT_DIR/.env"
REPO_URL="https://github.com/coleam00/local-ai-packaged.git"
GOVINFO_SAMPLE_URL="https://www.govinfo.gov/bulkdata/BILLS/118/HR/HR1.xml"
USE_GPU="${USE_GPU:-false}"
RABBITMQ_USER="guest"
RABBITMQ_PASS="guest"  # Change in production
GRAYLOG_PASSWORD="admin"  # Change in production
OPENSEARCH_PASSWORD="admin"  # Change in production

echo "Starting deployment of extended Self-hosted AI Package for Legislative Analysis..."

# 1. Check prerequisites
echo "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo >&2 "Docker is required but not installed."; exit 1; }
# Check for Docker Compose v2
if ! docker compose version >/dev/null 2>&1; then
  echo >&2 "Docker Compose v2 is required. Install via 'sudo apt install docker-compose-plugin' or equivalent."
  exit 1
fi
command -v python3 >/dev/null 2>&1 || { echo >&2 "Python3 is required but not installed."; exit 1; }
command -v git >/dev/null 2>&1 || { echo >&2 "Git is required but not installed."; exit 1; }
if [ "$USE_GPU" = "true" ]; then
  command -v nvidia-smi >/dev/null 2>&1 || { echo >&2 "NVIDIA GPU is selected but nvidia-smi not found. Install NVIDIA drivers/CUDA."; exit 1; }
fi

# 2. Clone or update repo
if [ ! -d "$PROJECT_DIR" ]; then
  echo "Cloning repository..."
  git clone -b stable $REPO_URL .
else
  echo "Updating repository..."
  git pull
fi

# 3. Prepare .env with Bitwarden secrets (repeatable, no regeneration)
echo "Preparing .env file from Bitwarden..."

# Check if migration needed (if .env lacks critical secrets)
if [ ! -f .env ] || ! grep -q "POSTGRES_PASSWORD=" .env || [ "${#POSTGRES_PASSWORD}" -lt 64 ]; then
    echo "⚠️  Skipping Bitwarden migration for development - using existing .env"
    echo "For production, run: ./scripts/migrate-secrets-to-bitwarden.sh"
    source .env
else
    if [ -f scripts/populate-env-from-bitwarden.sh ]; then
        echo "🔐 Populating secrets from Bitwarden..."
        ./scripts/populate-env-from-bitwarden.sh
    else
        echo "⚠️  Bitwarden population script not found. Using existing .env"
    fi
fi

# Populate .env from Bitwarden if script exists
if [ -f scripts/populate-env-from-bitwarden.sh ]; then
    echo "🔐 Populating secrets from Bitwarden..."
    ./scripts/populate-env-from-bitwarden.sh
else
    echo "⚠️  Bitwarden population script not found. Using existing .env"
    cp .env.example .env 2>/dev/null || true
fi

# Source the populated .env
source .env

# Validate critical secrets exist (non-placeholder)
if [[ "$POSTGRES_PASSWORD" == *"your_"* ]] || [[ "$JWT_SECRET" == *"your_"* ]]; then
    echo "❌ Critical secrets missing in .env. Run: ./scripts/populate-env-from-bitwarden.sh"
    exit 1
fi

echo "✅ Secrets validated. Using Bitwarden-managed credentials."
# Extensions (use Bitwarden values if available, fallback to defaults)
echo "RABBITMQ_DEFAULT_USER=${RABBITMQ_USER:-guest}" >> .env
echo "RABBITMQ_DEFAULT_PASS=${RABBITMQ_PASS:-guest}" >> .env
echo "GRAYLOG_PASSWORD=${GRAYLOG_PASSWORD:-admin}" >> .env
echo "OPENSEARCH_PASSWORD=${OPENSEARCH_PASSWORD:-admin}" >> .env
echo "LOCALAI_API_KEY=${LOCALAI_API_KEY:-$(openssl rand -hex 32)}" >> .env  # Generate if not in Bitwarden

# 4. Extend docker-compose.yml with OLK stack, RabbitMQ, LocalAI
echo "Creating extensions.yml for new services..."
cat > extensions.yml << 'EOF'
volumes:
  prometheus_data:
  grafana_data:
  loki_data:
  opensearch_data:
  graylog_data:
  rabbitmq_data:
  localai_data:

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    expose:
      - 9090
    volumes:
      - prometheus_data:/prometheus
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:9090/-/healthy"]
      interval: 30s
      timeout: 10s
      retries: 3

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    expose:
      - 3000
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin  # Change in prod
    depends_on:
      - prometheus
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  loki:
    image: grafana/loki:latest
    container_name: loki
    restart: unless-stopped
    expose:
      - 3100
    volumes:
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3100/ready"]
      interval: 30s
      timeout: 10s
      retries: 3

  opensearch:
    image: opensearchproject/opensearch:latest
    container_name: opensearch
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
      - plugins.security.ssl.http.enabled=false
      - plugins.security.disabled=true  # For local; enable in prod
    ulimits:
      memlock: -1
    volumes:
      - opensearch_data:/usr/share/opensearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health?wait_for_status=green&timeout=1s"]
      interval: 30s
      timeout: 10s
      retries: 3

  graylog:
    image: graylog/graylog:latest
    container_name: graylog
    restart: unless-stopped
    expose:
      - 9000
      - 12201/udp  # GELF input
    environment:
      - GRAYLOG_PASSWORD_SECRET=$(generate_secret | base64)
      - GRAYLOG_ROOT_PASSWORD_SHA2=$(echo -n "$GRAYLOG_PASSWORD" | sha256sum | awk '{print $1}')
      - GRAYLOG_HTTP_EXTERNAL_URI=http://localhost:9000/
      - GRAYLOG_ELASTICSEARCH_HOSTS=http://opensearch:9200
    depends_on:
      - opensearch
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/api/system"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 1G

  rabbitmq:
    image: rabbitmq:3-management
    container_name: rabbitmq
    restart: unless-stopped
    expose:
      - 5672
      - 15672  # Management UI
    environment:
      - RABBITMQ_DEFAULT_USER=$RABBITMQ_USER
      - RABBITMQ_DEFAULT_PASS=$RABBITMQ_PASS
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "status"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          memory: 512M

  localai:
    image: quay.io/go-skynet/local-ai:latest
    container_name: localai
    restart: unless-stopped
    expose:
      - 8080
    volumes:
      - localai_data:/build/models
    environment:
      - API_KEY=${LOCALAI_API_KEY}
    command: --models-path /build/models --debug
    depends_on:
      - rabbitmq  # For orchestration triggers
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF

# Add include to docker-compose.yml if not present
if ! grep -q "extensions.yml" docker-compose.yml; then
  sed -i '/include:/a\  - ./extensions.yml' docker-compose.yml
fi

# Create prometheus.yml for metrics (scrape n8n, LocalAI, etc.)
cat > prometheus.yml << 'EOF'
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'n8n'
    static_configs:
      - targets: ['n8n:5678']
  - job_name: 'localai'
    static_configs:
      - targets: ['localai:8080']
  - job_name: 'rabbitmq'
    static_configs:
      - targets: ['rabbitmq:15672']
EOF

# 5. Update Caddyfile for new services
echo "Updating Caddyfile..."
cat >> Caddyfile << 'EOF'

# Prometheus
:8009 {
  reverse_proxy prometheus:9090
}

# Grafana
:8010 {
  reverse_proxy grafana:3000
}

# Loki
:8011 {
  reverse_proxy loki:3100
}

# OpenSearch
:8012 {
  reverse_proxy opensearch:9200
}

# Graylog
:8013 {
  reverse_proxy graylog:9000
}

# RabbitMQ Management
:8014 {
  reverse_proxy rabbitmq:15672
}

# LocalAI
:8015 {
  reverse_proxy localai:8080
}
EOF

# 6. Update docker-compose.override.private.yml for private ports
echo "Updating override file..."
cat >> docker-compose.override.private.yml << 'EOF'
  prometheus:
    ports:
      - 127.0.0.1:9090:9090
  grafana:
    ports:
      - 127.0.0.1:3000:3000  # Adjust if conflict
  loki:
    ports:
      - 127.0.0.1:3100:3100
  opensearch:
    ports:
      - 127.0.0.1:9200:9200
  graylog:
    ports:
      - 127.0.0.1:9000:9000
      - 127.0.0.1:12201:12201/udp
  rabbitmq:
    ports:
      - 127.0.0.1:5672:5672
      - 127.0.0.1:15672:15672
  localai:
    ports:
      - 127.0.0.1:8080:8080
EOF

# 7. DB and Queue Init
echo "Initializing DB and queues..."
PROFILE="${USE_GPU:+gpu-nvidia}"
# Ensure .env is sourced for start_services
export $(grep -v '^#' .env | xargs)
python3 start_services.py --profile $PROFILE --environment private  # Starts base services
docker compose up -d prometheus grafana loki opensearch graylog rabbitmq localai  # Start extensions
sleep 20  # Wait for Supabase and RabbitMQ
# Legislative schema
docker exec -i supabase-db psql -U postgres -d postgres -c "
CREATE SCHEMA IF NOT EXISTS legislative;
CREATE TABLE IF NOT EXISTS legislative.bills (
  id SERIAL PRIMARY KEY,
  title TEXT,
  text XML,
  fetched_at TIMESTAMP DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS legislative.votes (
  id SERIAL PRIMARY KEY,
  bill_id INTEGER REFERENCES legislative.bills(id),
  politician TEXT,  -- Anonymize in prod
  vote TEXT
);
CREATE TABLE IF NOT EXISTS ai_agents (
  id SERIAL PRIMARY KEY,
  name TEXT,
  status TEXT,
  deployed_at TIMESTAMP DEFAULT NOW()
);
"
# RabbitMQ queues for agent comms
docker exec rabbitmq rabbitmqadmin -u $RABBITMQ_USER -p $RABBITMQ_PASS declare queue name=legislative-ingestion durable=true
docker exec rabbitmq rabbitmqadmin -u $RABBITMQ_USER -p $RABBITMQ_PASS declare queue name=agent-orchestration durable=true
docker exec rabbitmq rabbitmqadmin -u $RABBITMQ_USER -p $RABBITMQ_PASS declare queue name=monitoring-events durable=true

# 8. Ethical log sanitization (example filter for Graylog input)
echo "Configuring log sanitization (manual step: Add PII filter in Graylog UI at http://localhost:8013)"

# 9. Test deployment
echo "Testing deployment..."
sleep 10
# Sample ingestion trigger (assume n8n webhook; simulate with curl)
curl -X POST http://localhost:5678/webhook/legislative-ingest \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"$GOVINFO_SAMPLE_URL\"}" || echo "n8n webhook not set; manual test needed"
# Check DB
docker exec supabase-db psql -U postgres -d postgres -c "SELECT COUNT(*) FROM legislative.bills;"
# Deploy sample sub-agent via LocalAI (triggered by RabbitMQ message)
docker exec rabbitmq rabbitmqadmin -u $RABBITMQ_USER -p $RABBITMQ_PASS publish routing_key=agent-orchestration payload='{"action": "deploy", "model": "llama3", "data_source": "govinfo"}'
curl -X POST http://localhost:8015/v1/models/apply \
  -H "Authorization: Bearer ${LOCALAI_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"model_url": "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"}'  # Example load model for sub-agent
# Check monitoring
curl http://localhost:8009/api/v1/query?query=up  # Prometheus
echo "Access Grafana at http://localhost:8010 (admin/admin), Graylog at http://localhost:8013 (admin/$GRAYLOG_PASSWORD)"
echo "RabbitMQ UI at http://localhost:8014 ($RABBITMQ_USER:$RABBITMQ_PASS)"
echo "LocalAI at http://localhost:8015"

echo "Deployment complete. For ethical usage: Sanitize politician names in logs/DB for privacy. Efficiency: Monitor resource usage in Grafana. Security: Change all passwords and enable SSL."