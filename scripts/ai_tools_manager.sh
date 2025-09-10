#!/bin/bash

# AI Tools Manager
# A simple CLI to manage AI tools and services

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose could not be found. Please install it first."
    exit 1
fi

# Function to display help
show_help() {
    echo "AI Tools Manager"
    echo "Usage: $0 [command] [service]"
    echo ""
    echo "Commands:"
    echo "  start [service]   Start all services or a specific service"
    echo "  stop [service]    Stop all services or a specific service"
    echo "  restart [service] Restart all services or a specific service"
    echo "  status            Show status of all services"
    echo "  logs [service]    Show logs for all services or a specific service"
    echo "  setup             Run initial setup for all services"
    echo "  help              Show this help message"
    echo ""
    echo "Available services:"
    echo "  graphite       - Metrics and monitoring dashboard"
    echo "  libsql         - mcp-memory-libsql service"
    echo "  neo4j          - Neo4j database for mcp-neo4j-agent-memory"
    echo "  crewai         - CrewAI agent orchestration"
    echo "  letta          - Letta memory system"
    echo "  falkor         - Falkor database"
    echo "  graphrag       - GraphRAG-SDK service"
    echo "  llama          - Llama Stack"
    echo "  crawl4ai       - MCP Crawl4AI RAG"
    echo "  all            - All services (default)"
}

# Function to run docker-compose command
run_compose() {
    local cmd=$1
    local service=$2
    
    if [ "$service" == "all" ] || [ -z "$service" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.override.ai-tools.yml $cmd
    else
        docker-compose -f docker-compose.yml -f docker-compose.override.ai-tools.yml $cmd $service
    fi
}

# Function to show service status
show_status() {
    echo -e "${YELLOW}=== Service Status ===${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.override.ai-tools.yml ps
}

# Function to show service logs
show_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.override.ai-tools.yml logs -f
    else
        docker-compose -f docker-compose.yml -f docker-compose.override.ai-tools.yml logs -f $service
    fi
}

# Function to run initial setup
run_setup() {
    echo -e "${GREEN}Running initial setup...${NC}"
    
    # Create necessary directories
    echo "Creating directories..."
    mkdir -p {graphite/{data,logs},libsql_data,neo4j/{data,logs},crewai/{agents,tasks},letta_data,falkor_data,graphrag_data,llama_data,crawl4ai_data}
    
    # Set permissions
    echo "Setting permissions..."
    chmod -R 777 {graphite,libsql_data,neo4j,letta_data,falkor_data,graphrag_data,llama_data,crawl4ai_data}
    
    # Pull latest images
    echo -e "\n${GREEN}Pulling latest images...${NC}"
    docker-compose -f docker-compose.yml -f docker-compose.override.ai-tools.yml pull
    
    echo -e "\n${GREEN}Setup complete!${NC}"
    echo "You can now start the services using: $0 start"
}

# Main script logic
case "$1" in
    start)
        run_compose "up -d" "$2"
        ;;
    stop)
        run_compose "stop" "$2"
        ;;
    restart)
        run_compose "restart" "$2"
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "$2"
        ;;
    setup)
        run_setup
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

exit 0
