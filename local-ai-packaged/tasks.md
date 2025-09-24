# Project Tasks

## Documentation
- **Task: Audit and document codebase structure**  
  Description: Review empty dirs (e.g., agentic-knowledge-rag-graph/), add README sections for setup/arch.  
  Assignee: Team  
  Status: TODO  
  Dependencies: None  
  Effort: 2 hours  

- **Task: Generate API docs with Swagger**  
  Description: Add /docs endpoint in FastAPI main.py, integrate with CI.  
  Assignee: Backend  
  Status: TODO  
  Dependencies: Backend stubs  
  Effort: 3 hours  

- **Task: Create onboarding guide**  
  Description: Update README.md with install steps, env setup, first-run.  
  Assignee: Team  
  Status: TODO  
  Dependencies: Docker Compose  
  Effort: 4 hours  

- **Task: Document provider integrations**  
  Description: Write providers.md with YAML examples, validation script.  
  Assignee: DevOps  
  Status: TODO  
  Dependencies: config/providers/  
  Effort: 2 hours  

## CI/CD
- **Task: Set up .github/workflows/ci.yml**  
  Description: Lint/test/build on PRs (pre-commit, pytest, vitest, Docker build).  
  Assignee: DevOps  
  Status: TODO  
  Dependencies: Makefile  
  Effort: 4 hours  

- **Task: Implement cd.yml for staging/prod deploys**  
  Description: Buildx multi-arch, push to GHCR, kubectl apply for k3s.  
  Assignee: DevOps  
  Status: TODO  
  Dependencies: ci.yml  
  Effort: 5 hours  

- **Task: Add security.yml for scans**  
  Description: CodeQL for SAST, Trivy for images/deps.  
  Assignee: DevOps  
  Status: TODO  
  Dependencies: ci.yml  
  Effort: 3 hours  

- **Task: Configure release.yml for versioning**  
  Description: Semantic-release, changelog, tag docs update.  
  Assignee: DevOps  
  Status: TODO  
  Dependencies: cd.yml  
  Effort: 3 hours  

- **Task: Extend Makefile with CI/CD targets**  
  Description: make ci-local (offline tests), make deploy-staging.  
  Assignee: DevOps  
  Status: TODO  
  Dependencies: Dockerfiles  
  Effort: 2 hours  

## Backend Enhancements
- **Task: Populate agentic-knowledge-rag-graph/ with main.py stubs**  
  Description: FastAPI app with /rag/query, /ingest endpoints; integrate LangChain/Neo4j.  
  Assignee: Backend  
  Status: TODO  
  Dependencies: pyproject.toml  
  Effort: 6 hours  

- **Task: Add dynamic provider loading in main.py**  
  Description: Pydantic models for configs, fallback to Ollama.  
  Assignee: Backend  
  Status: TODO  
  Dependencies: config/providers/  
  Effort: 4 hours  

- **Task: Implement RAG pipeline tests (pytest)**  
  Description: Unit tests for query/ingest, mock Neo4j/Qdrant.  
  Assignee: Backend  
  Status: TODO  
  Dependencies: main.py  
  Effort: 4 hours  

## Frontend Polish
- **Task: Set up build scripts in package.json**  
  Description: Add optimize, preview targets for Next.js.  
  Assignee: Frontend  
  Status: TODO  
  Dependencies: None  
  Effort: 2 hours  

- **Task: Add Storybook for components**  
  Description: Setup for GraphViewer/MetricsChart, integrate in CI.  
  Assignee: Frontend  
  Status: TODO  
  Dependencies: package.json  
  Effort: 5 hours  

- **Task: E2E tests with Playwright**  
  Description: Test dashboard/search flows, integrate with CI.  
  Assignee: Frontend  
  Status: TODO  
  Dependencies: playwright.config.ts  
  Effort: 4 hours  

## Integrations
- **Task: Create config/providers/ with YAML files**  
  Description: openai.yml (API key, model), huggingface.yml (endpoints), aws.yml (S3 bucket).  
  Assignee: DevOps  
  Status: TODO  
  Dependencies: None  
  Effort: 3 hours  

- **Task: Develop setup-providers.sh**  
  Description: Validate connections (curl for APIs), set env vars.  
  Assignee: DevOps  
  Status: TODO  
  Dependencies: config/providers/  
  Effort: 2 hours  

- **Task: Integrate OpenAI/HF in RAG chains**  
  Description: Update main.py for provider swaps via env.  
  Assignee: Backend  
  Status: TODO  
  Dependencies: main.py  
  Effort: 4 hours  

- **Task: Add AWS/GCP for dataset storage**  
  Description: S3 upload in ingest endpoint, local fallback.  
  Assignee: Backend  
  Status: TODO  
  Dependencies: Integrations  
  Effort: 5 hours  

## Custom GitHub Actions
- **Task: Create .github/actions/setup-python-env**  
  Description: action.yml for Poetry install, pre-commit run.  
  Assignee: DevOps  
  Status: TODO  
  Dependencies: None  
  Effort: 2 hours  

- **Task: Build .github/actions/build-rag-pipeline**  
  Description: Smoke tests for LangChain/Neo4j.  
  Assignee: Backend  
  Status: TODO  
  Dependencies: Backend tests  
  Effort: 3 hours  

- **Task: Develop .github/actions/deploy-frontend**  
  Description: Next.js build to Vercel preview.  
  Assignee: Frontend  
  Status: TODO  
  Dependencies: package.json  
  Effort: 3 hours  

- **Task: Create .github/actions/scan-knowledge-graph**  
  Description: Cypher validation for Neo4j schema.  
  Assignee: Backend  
  Status: TODO  
  Effort: 3 hours  

- **Task: Implement .github/actions/integrate-ai-provider**  
  Description: Env-based swaps (OpenAI to Ollama).  
  Assignee: DevOps  
  Status: TODO  
  Dependencies: Providers  
  Effort: 2 hours  

- **Task: Build .github/actions/generate-docs**  
  Description: Swagger/Storybook build.  
  Assignee: Team  
  Status: TODO  
  Effort: 3 hours  

- **Task: Create .github/actions/backup-secrets**  
  Description: Encrypt .env to GH Secrets.  
  Assignee: DevOps  
  Status: TODO  
  Effort: 2 hours  

- **Task: Develop .github/actions/notify-team**  
  Description: Slack notifications on failures.  
  Assignee: DevOps  
  Status: TODO  
  Effort: 2 hours  