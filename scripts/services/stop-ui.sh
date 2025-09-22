#!/bin/bash\ncommand="docker compose -f docker-compose.traefik.yml -f docker-compose.yml down frontend dashboard agentic-rag"\n$command
