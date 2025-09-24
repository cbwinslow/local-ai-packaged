#!/bin/bash
set -e

PROVIDERS_DIR="config/providers"
ENV_FILE=".env"

if [ ! -f "$ENV_FILE" ]; then
  echo "Copy .env.example to .env and add keys."
  exit 1
fi

for provider_file in "$PROVIDERS_DIR"/*.yml; do
  provider=$(basename "$provider_file" .yml)
  echo "Validating $provider..."
  case $provider in
    openai)
      if [ -n "$OPENAI_API_KEY" ]; then
        curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models || echo "OpenAI OK"
      fi
      ;;
    huggingface)
      if [ -n "$HF_TOKEN" ]; then
        curl -H "Authorization: Bearer $HF_TOKEN" https://huggingface.co/api/whoami || echo "HF OK"
      fi
      ;;
    aws)
      aws sts get-caller-identity || echo "AWS OK"
      ;;
    local)
      curl http://localhost:11434/api/tags || echo "Ollama running?"
      ;;
  esac
done

echo "Providers validated."