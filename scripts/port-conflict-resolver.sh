#!/bin/bash

# ========================================================================================
# Local AI Package - Port Conflict Resolution System
# ========================================================================================
# This script detects and resolves port conflicts in Docker Compose configurations
# It can automatically remap conflicting ports and update configurations
# ========================================================================================

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
COMPOSE_FILES=(
    "docker-compose.yml"
    "docker-compose.traefik.yml"
    "docker-compose.monitoring.yml"
    "docker-compose.mcp.yml"
    "supabase/docker/docker-compose.yml"
)

OVERRIDE_FILES=(
    "docker-compose.override.private.yml"
    "docker-compose.override.public.yml"
    "config/docker-compose.override.private.yml"
    "config/docker-compose.override.public.yml"
    "config/docker-compose.override.ai-tools.yml"
)

# Port ranges for different environments
declare -A PORT_RANGES=(
    ["private_start"]=9001
    ["private_end"]=9999
    ["public_start"]=80
    ["public_end"]=443
    ["internal_start"]=3000
    ["internal_end"]=8999
)

# Service port mappings
declare -A DEFAULT_PORTS=(
    ["traefik"]=80,443
    ["supabase-kong"]=8000
    ["supabase-studio"]=3000
    ["n8n"]=5678
    ["flowise"]=3001
    ["open-webui"]=8080
    ["qdrant"]=6333,6334
    ["neo4j"]=7474,7687
    ["langfuse-web"]=3000
    ["clickhouse"]=8123,9000
    ["minio"]=9000,9001
    ["postgres"]=5432
    ["redis"]=6379
    ["searxng"]=8080
    ["grafana"]=3000
    ["prometheus"]=9090
    ["frontend"]=3000
    ["agentic-rag"]=8000
    ["dashboard"]=3000
)

# Check if port is in use
check_port() {
    local port=$1
    if command -v netstat >/dev/null 2>&1; then
        netstat -tuln | grep -q ":${port} "
    elif command -v ss >/dev/null 2>&1; then
        ss -tuln | grep -q ":${port} "
    elif command -v lsof >/dev/null 2>&1; then
        lsof -i ":${port}" >/dev/null 2>&1
    else
        # Fallback: try to bind to the port
        if command -v nc >/dev/null 2>&1; then
            ! nc -z localhost "$port" 2>/dev/null
        else
            # Last resort: use Docker to check
            ! docker run --rm -p "${port}:${port}" alpine:latest sh -c "sleep 1" >/dev/null 2>&1
        fi
    fi
}

# Find available port in range
find_available_port() {
    local start=$1
    local end=$2
    local exclude_ports=${3:-""}
    
    for ((port=start; port<=end; port++)); do
        if [[ "$exclude_ports" =~ $port ]]; then
            continue
        fi
        if ! check_port "$port"; then
            echo "$port"
            return 0
        fi
    done
    return 1
}

# Extract ports from docker-compose file
extract_ports() {
    local file=$1
    if [[ ! -f "$file" ]]; then
        return 0
    fi
    
    # Use yq if available, otherwise use grep/awk
    if command -v yq >/dev/null 2>&1; then
        yq eval '.services[].ports[]' "$file" 2>/dev/null | grep -E "^[0-9]+" | cut -d':' -f1 | sort -n | uniq
    else
        # Fallback to grep/awk parsing
        grep -E "^\s*-\s*[\"']?[0-9]+:" "$file" | awk -F':' '{gsub(/[^0-9]/, "", $1); print $1}' | sort -n | uniq
    fi
}

# Scan for port conflicts
scan_port_conflicts() {
    echo -e "${BLUE}🔍 Scanning for port conflicts...${NC}"
    
    local all_ports=()
    local conflicts=()
    local file_ports=()
    
    # Collect all defined ports
    for file in "${COMPOSE_FILES[@]}" "${OVERRIDE_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            echo "  📄 Scanning $file"
            while IFS= read -r port; do
                if [[ -n "$port" && "$port" =~ ^[0-9]+$ ]]; then
                    all_ports+=("$port")
                    file_ports+=("$file:$port")
                fi
            done < <(extract_ports "$file")
        fi
    done
    
    # Check for duplicates in configuration
    local sorted_ports=($(printf '%s\n' "${all_ports[@]}" | sort -n))
    local prev_port=""
    for port in "${sorted_ports[@]}"; do
        if [[ "$port" == "$prev_port" ]]; then
            conflicts+=("$port")
        fi
        prev_port="$port"
    done
    
    # Check for system conflicts
    local system_conflicts=()
    for port in "${sorted_ports[@]}"; do
        if check_port "$port"; then
            system_conflicts+=("$port")
        fi
    done
    
    # Report conflicts
    if [[ ${#conflicts[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Configuration conflicts found:${NC}"
        printf '%s\n' "${conflicts[@]}" | sort -n | uniq | while read -r port; do
            echo -e "  🔥 Port $port used in multiple files:"
            printf '%s\n' "${file_ports[@]}" | grep ":$port$" | sed 's/^/    /'
        done
    fi
    
    if [[ ${#system_conflicts[@]} -gt 0 ]]; then
        echo -e "${YELLOW}⚠️  System conflicts (ports already in use):${NC}"
        printf '%s\n' "${system_conflicts[@]}" | sort -n | uniq | while read -r port; do
            echo "  🚧 Port $port"
        done
    fi
    
    if [[ ${#conflicts[@]} -eq 0 && ${#system_conflicts[@]} -eq 0 ]]; then
        echo -e "${GREEN}✅ No port conflicts detected${NC}"
        return 0
    else
        return 1
    fi
}

# Resolve conflicts automatically
resolve_conflicts() {
    local environment=${1:-"private"}
    
    echo -e "${BLUE}🔧 Resolving port conflicts for $environment environment...${NC}"
    
    case "$environment" in
        "private")
            local start_port=${PORT_RANGES["private_start"]}
            local end_port=${PORT_RANGES["private_end"]}
            ;;
        "public")
            local start_port=${PORT_RANGES["public_start"]}
            local end_port=${PORT_RANGES["public_end"]}
            ;;
        *)
            echo -e "${RED}❌ Unknown environment: $environment${NC}"
            return 1
            ;;
    esac
    
    # Create override file for the environment
    local override_file="docker-compose.override.${environment}.generated.yml"
    
    cat > "$override_file" << EOF
# Auto-generated port conflict resolution for $environment environment
# Generated on $(date)
# This file resolves port conflicts by remapping services to available ports

version: '3.8'

services:
EOF

    local used_ports=()
    local remapped_count=0
    
    # Process each service
    for service in "${!DEFAULT_PORTS[@]}"; do
        local service_ports="${DEFAULT_PORTS[$service]}"
        IFS=',' read -ra ports <<< "$service_ports"
        
        local new_ports=()
        local service_needs_remapping=false
        
        for port in "${ports[@]}"; do
            if check_port "$port" || [[ " ${used_ports[*]} " =~ " ${port} " ]]; then
                # Find alternative port
                local new_port
                if new_port=$(find_available_port "$start_port" "$end_port" "${used_ports[*]}"); then
                    new_ports+=("${new_port}:${port}")
                    used_ports+=("$new_port")
                    service_needs_remapping=true
                    echo -e "  🔄 $service: $port → $new_port"
                    ((remapped_count++))
                else
                    echo -e "${RED}❌ No available ports in range for service $service${NC}"
                    new_ports+=("${port}:${port}")
                fi
            else
                new_ports+=("${port}:${port}")
                used_ports+=("$port")
            fi
        done
        
        # Add service to override file if remapping needed
        if [[ "$service_needs_remapping" == true ]]; then
            cat >> "$override_file" << EOF
  $service:
    ports:
EOF
            for port_mapping in "${new_ports[@]}"; do
                echo "      - \"$port_mapping\"" >> "$override_file"
            done
            echo "" >> "$override_file"
        fi
    done
    
    if [[ "$remapped_count" -gt 0 ]]; then
        echo -e "${GREEN}✅ Generated $override_file with $remapped_count port remappings${NC}"
        echo -e "${YELLOW}⚠️  Include this file in your docker-compose command:${NC}"
        echo "  docker-compose -f docker-compose.yml -f $override_file up"
    else
        rm -f "$override_file"
        echo -e "${GREEN}✅ No port remapping needed${NC}"
    fi
}

# Create environment-specific override files
create_override_files() {
    echo -e "${BLUE}🏗️  Creating environment-specific override files...${NC}"
    
    # Private environment (development)
    cat > "docker-compose.override.private.yml" << 'EOF'
# Private environment override - binds all services to localhost
# Use for local development with full port access

version: '3.8'

services:
  # Traefik reverse proxy
  traefik:
    ports:
      - "127.0.0.1:80:80"
      - "127.0.0.1:443:443"
      - "127.0.0.1:8080:8080"  # Traefik dashboard

  # Supabase services
  kong:
    ports:
      - "127.0.0.1:8000:8000"
  
  studio:
    ports:
      - "127.0.0.1:3001:3000"
  
  # AI services with unique ports
  n8n:
    ports:
      - "127.0.0.1:5678:5678"
  
  flowise:
    ports:
      - "127.0.0.1:3002:3001"
  
  open-webui:
    ports:
      - "127.0.0.1:8081:8080"
  
  # Databases
  qdrant:
    ports:
      - "127.0.0.1:6333:6333"
      - "127.0.0.1:6334:6334"
  
  neo4j:
    ports:
      - "127.0.0.1:7474:7474"
      - "127.0.0.1:7687:7687"
  
  postgres:
    ports:
      - "127.0.0.1:5432:5432"
  
  redis:
    ports:
      - "127.0.0.1:6379:6379"
  
  clickhouse:
    ports:
      - "127.0.0.1:8123:8123"
      - "127.0.0.1:9000:9000"
  
  # Storage
  minio:
    ports:
      - "127.0.0.1:9001:9000"
      - "127.0.0.1:9002:9001"
  
  # Monitoring
  grafana:
    ports:
      - "127.0.0.1:3003:3000"
  
  prometheus:
    ports:
      - "127.0.0.1:9090:9090"
  
  # Search
  searxng:
    ports:
      - "127.0.0.1:8082:8080"
  
  # Applications
  langfuse-web:
    ports:
      - "127.0.0.1:3004:3000"
  
  frontend:
    ports:
      - "127.0.0.1:3005:3000"
  
  agentic-rag:
    ports:
      - "127.0.0.1:8001:8000"
  
  dashboard:
    ports:
      - "127.0.0.1:3006:3000"
EOF

    # Public environment (production)
    cat > "docker-compose.override.public.yml" << 'EOF'
# Public environment override - only exposes necessary ports
# Use for production deployment with Traefik handling routing

version: '3.8'

services:
  # Only expose Traefik ports for public access
  traefik:
    ports:
      - "80:80"
      - "443:443"
    # Remove dashboard exposure in production
    command:
      - "--api.dashboard=false"
      - "--api.insecure=false"

  # All other services use internal networking only
  # Traefik routes traffic based on labels
  kong:
    expose:
      - "8000"
  
  studio:
    expose:
      - "3000"
  
  n8n:
    expose:
      - "5678"
  
  flowise:
    expose:
      - "3001"
  
  open-webui:
    expose:
      - "8080"
  
  langfuse-web:
    expose:
      - "3000"
  
  frontend:
    expose:
      - "3000"
  
  agentic-rag:
    expose:
      - "8000"
  
  searxng:
    expose:
      - "8080"
  
  grafana:
    expose:
      - "3000"
EOF

    echo -e "${GREEN}✅ Created docker-compose.override.private.yml${NC}"
    echo -e "${GREEN}✅ Created docker-compose.override.public.yml${NC}"
}

# Generate port documentation
generate_port_docs() {
    local output_file="docs/PORT_REFERENCE.md"
    mkdir -p "$(dirname "$output_file")"
    
    cat > "$output_file" << 'EOF'
# Port Reference Guide

This document provides a comprehensive reference for all ports used in the Local AI Package.

## Port Allocation Strategy

### Private Environment (Development)
- **Range**: 9001-9999 (configurable)
- **Binding**: 127.0.0.1 (localhost only)
- **Purpose**: Local development with direct port access

### Public Environment (Production)
- **Exposed Ports**: 80, 443 only
- **Routing**: Traefik reverse proxy handles all routing
- **Purpose**: Production deployment with SSL termination

## Service Port Mappings

### Core Infrastructure
| Service | Internal Port | Private External | Public Access |
|---------|---------------|------------------|---------------|
| Traefik | 80, 443, 8080 | 80, 443, 8080 | 80, 443 |

### Supabase Stack
| Service | Internal Port | Private External | Public Access |
|---------|---------------|------------------|---------------|
| Kong (API Gateway) | 8000 | 8000 | /supabase |
| Studio (Dashboard) | 3000 | 3001 | /studio |
| PostgreSQL | 5432 | 5432 | Internal only |

### AI Services
| Service | Internal Port | Private External | Public Access |
|---------|---------------|------------------|---------------|
| N8N | 5678 | 5678 | /n8n |
| Flowise | 3001 | 3002 | /flowise |
| Open WebUI | 8080 | 8081 | /openwebui |
| Langfuse | 3000 | 3004 | /langfuse |

### Databases
| Service | Internal Port | Private External | Public Access |
|---------|---------------|------------------|---------------|
| Qdrant | 6333, 6334 | 6333, 6334 | Internal only |
| Neo4j | 7474, 7687 | 7474, 7687 | /neo4j |
| ClickHouse | 8123, 9000 | 8123, 9000 | Internal only |
| Redis/Valkey | 6379 | 6379 | Internal only |

### Storage
| Service | Internal Port | Private External | Public Access |
|---------|---------------|------------------|---------------|
| MinIO | 9000, 9001 | 9001, 9002 | Internal only |

### Monitoring
| Service | Internal Port | Private External | Public Access |
|---------|---------------|------------------|---------------|
| Grafana | 3000 | 3003 | /grafana |
| Prometheus | 9090 | 9090 | Internal only |

### Search & Discovery
| Service | Internal Port | Private External | Public Access |
|---------|---------------|------------------|---------------|
| SearXNG | 8080 | 8082 | /searxng |

### Applications
| Service | Internal Port | Private External | Public Access |
|---------|---------------|------------------|---------------|
| Frontend | 3000 | 3005 | / |
| Agentic RAG | 8000 | 8001 | /agentic |
| Dashboard | 3000 | 3006 | /dashboard |

## Usage Examples

### Start in Private Mode
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.private.yml up
```

### Start in Public Mode
```bash
docker-compose -f docker-compose.yml -f docker-compose.override.public.yml up
```

### Check for Conflicts
```bash
./scripts/port-conflict-resolver.sh scan
```

### Auto-resolve Conflicts
```bash
./scripts/port-conflict-resolver.sh resolve private
```

## Troubleshooting

### Port Already in Use
If you encounter "port already in use" errors:

1. Check what's using the port:
   ```bash
   lsof -i :PORT_NUMBER
   ```

2. Use the automatic conflict resolver:
   ```bash
   ./scripts/port-conflict-resolver.sh resolve private
   ```

3. Manually specify alternative ports in your override file

### Service Not Accessible
If a service isn't accessible:

1. Verify the service is running:
   ```bash
   docker-compose ps
   ```

2. Check port mapping:
   ```bash
   docker-compose port SERVICE_NAME
   ```

3. Test connectivity:
   ```bash
   curl http://localhost:PORT
   ```

### Traefik Routing Issues
For Traefik routing problems in public mode:

1. Check Traefik dashboard (private mode only):
   http://localhost:8080

2. Verify service labels in docker-compose files

3. Check DNS/hostname configuration
EOF

    echo -e "${GREEN}✅ Generated port documentation: $output_file${NC}"
}

# Main function
main() {
    local action=${1:-"scan"}
    
    case "$action" in
        "scan")
            scan_port_conflicts
            ;;
        "resolve")
            local environment=${2:-"private"}
            resolve_conflicts "$environment"
            ;;
        "create-overrides")
            create_override_files
            ;;
        "docs")
            generate_port_docs
            ;;
        "all")
            scan_port_conflicts
            create_override_files
            generate_port_docs
            echo -e "${GREEN}✅ Complete port conflict analysis and resolution setup${NC}"
            ;;
        *)
            echo "Usage: $0 {scan|resolve [private|public]|create-overrides|docs|all}"
            echo ""
            echo "Commands:"
            echo "  scan              - Scan for port conflicts"
            echo "  resolve [env]     - Automatically resolve conflicts for environment"
            echo "  create-overrides  - Create environment-specific override files"
            echo "  docs              - Generate port reference documentation"
            echo "  all               - Run all operations"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"