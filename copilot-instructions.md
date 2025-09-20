# Copilot Instructions for Local AI Packaged

This repository hosts the local-ai-packaged project. GitHub Copilot and similar tools should follow these guidelines when contributing code or documentation.

## Project Conventions
- **Language & Runtime:** Python 3.10. Use the `uv` package manager and work within the existing virtual environment.
- **Code Style:** Follow PEP 8 and include type hints where practical.
- **Documentation:** Update relevant Markdown files and docstrings when behavior changes.
- **Secrets:** Never commit secrets or credentials.

## Workflow Expectations
1. Keep changes small and focused.
2. Run `pre-commit run --files <changed files>` before committing.
3. Execute `uv run pytest` and ensure tests pass.
4. Include a concise summary in commit messages.

## Pull Requests
- Reference related issues.
- Ensure the PR description outlines testing steps and any follow-up tasks.
- CoderabbitAI and other review bots are enabled; allow them to complete reviews before merging.

## Helpful Context
- Service configurations live under `supabase`, `traefik`, and `monitoring`.
- Frontend code is in `frontend` and Python services in `services`.
- Workflows reside in `.github/workflows`.


## Automation
- TODO comments are converted to GitHub issues via a scheduled workflow.
- New issues and pull requests are added to the project board automatically.
- Stale issues and pull requests close after extended inactivity.

By adhering to these instructions, Copilot can generate contributions aligned with repository standards.
