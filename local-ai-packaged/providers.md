# AI Provider Integrations

## Setup
1. Copy .env.example to .env, add keys (e.g., OPENAI_API_KEY).
2. Run `./scripts/setup-providers.sh` to validate.
3. In main.py, load via `yaml.safe_load(open('config/providers/{provider}.yml'))`.

## Supported Providers
- **OpenAI**: LLM/completions; fallback to Ollama for privacy.
- **Hugging Face**: Embeddings/models; use for HF Hub downloads.
- **AWS**: S3 for datasets; local fallback for offline.
- **Local (Ollama)**: Default for self-hosted.

Dynamic swap: Set `LLM_PROVIDER=openai` in env; backend handles via Pydantic.