#!/bin/bash

# Local AI Packaged Project Backup Script
# This script creates a backup of all essential configuration files and service information

echo "Starting Local AI Packaged project backup..."

# Create backup directory
BACKUP_DIR="project_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Backup directory created: $BACKUP_DIR"

# Copy essential configuration files
cp .env docker-compose.yml Caddyfile "$BACKUP_DIR/"

# Copy configuration directories if they exist
for dir in n8n neo4j searxng; do
  if [ -d "$dir" ]; then
    cp -r "$dir" "$BACKUP_DIR/"
    echo "Copied $dir configuration"
  fi
done

# Save current running services information
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep -E "(n8n|ollama|open-webui|qdrant|neo4j|flowise|searxng|postgres|redis|clickhouse|minio|supabase|langfuse|caddy)" > "$BACKUP_DIR/current_services.txt"

# Create backup information file
cat > "$BACKUP_DIR/backup_info.txt" << EOF
Local AI Packaged Project Backup
Created on: $(date)

This backup contains:
- .env configuration file with secrets
- docker-compose.yml orchestration file  
- Caddyfile reverse proxy configuration
- Service configuration directories (n8n, neo4j, searxng)
- Current running services status

To restore this backup:
1. Copy the files back to your project directory
2. Update .env with your actual secrets if needed
3. Run 'docker compose up -d' to start services
EOF

echo "Backup completed successfully!"
echo "Backup location: $BACKUP_DIR"
echo ""
echo "Contents:"
ls -la "$BACKUP_DIR"