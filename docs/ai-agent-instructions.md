# AI Agent Instructions for Local AI Packaged Project

This file dictates the behavior and actions of the AI coding agent (me) when working on this codebase. It ensures consistent, verbose error handling and logging to maintain transparency and aid debugging. Follow these rules strictly for all interactions.

## General Actions
- **Project Focus**: Always prioritize the self-hosted AI platform's goals: privacy-focused RAG for legislative data, Docker orchestration, and offline capabilities. Reference architecture from copilot-instructions.md (e.g., n8n workflows, Supabase auth, Ollama LLMs).
- **Code Changes**: Make small, focused edits using insert_edit_into_file. Use comments like "// ...existing code..." to preserve context. Test changes immediately with relevant tools (e.g., pytest for Python, npm test for frontend).
- **Tool Usage**: Prefer project tools (uv for Python deps, docker compose for services). For errors, explain verbosely in responses, then log to errors.md.
- **Workflows**: Before edits, run health-check.sh. After, validate with pytest/npm test. If services fail, suggest restarts (e.g., ./scripts/start-all-services.sh).
- **Conventions**: Use uv venv for Python (3.10); no direct pip. Env vars from .env (never commit). Git: feature branches, Conventional Commits.
- **Verification**: After any change, rerun affected tests and health check. If errors occur, follow error handling below.

## Error Handling Protocol
For every error encountered (from tools, runs, or analysis):
1. **Verbose Explanation**: In your response, explain the error in detail: what it is, why it happened (based on output/context), impact on project, and step-by-step solution. Be educational—assume user is learning.
2. **Log to errors.md**: Append (no deletions/overrides) to docs/errors.md with this exact structure:
   - **Error Number**: Sequential (e.g., #001).
   - **Description**: Brief summary of the error message/output.
   - **Timestamp**: Current date/time (e.g., 2025-09-24 05:00:00).
   - **Program/Context**: Tool/command/file where it occurred (e.g., "docker compose up -d in start-all-services.sh").
   - **Meaning/Why**: Detailed analysis of cause (e.g., missing dep, port conflict, syntax error).
   - **Solution**: Actionable steps to fix (e.g., "Install via uv pip install <pkg>; rerun command").
3. **Implementation**: After logging, implement the solution using tools (e.g., run_in_terminal for installs). Rerun the failing command/test to verify.
4. **Microgoals Update**: If part of a task (e.g., testing), update any ongoing microgoals list in response.
5. **Escalation**: If unresolvable, suggest user input (e.g., "Provide logs for further analysis").

## Error Logging Format (Append to docs/errors.md)
Use Markdown for readability. Example entry:
```
### Error #001
**Description**: "Module not found: Can't resolve 'lucide-react'" during npm build.

**Timestamp**: 2025-09-24 04:13:00

**Program/Context**: Frontend build in Dockerfile (npm run build).

**Meaning/Why**: The lucide-react package is imported in src/app/docs/page.tsx but not listed in package.json dependencies. This causes webpack to fail compilation, blocking Docker image build and service startup.

**Solution**:
1. Run `cd frontend && npm install lucide-react`.
2. Rebuild: `docker compose build frontend`.
3. Rerun start script: `./scripts/start-all-services.sh`.
4. Verify: `npm test` in frontend should pass.
```

## Maintenance
- Update this file if new patterns emerge (e.g., add sections for new services).
- Log all errors here—no skipping. This ensures a cumulative knowledge base for troubleshooting.

Follow these to keep the project stable and productive.
