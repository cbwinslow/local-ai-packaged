#!/bin/bash\ncommand="docker compose -f docker-compose.traefik.yml -f docker-compose.yml up -d frontend dashboard agentic-rag"\n$command
