# Frontend Architecture for Enhanced Features

## Overview
The frontend is built with Next.js 14 using the App Router. It integrates Supabase for auth, realtime DB, and storage, and Neo4j for graph queries. Existing dashboard uses Pages Router for monitoring; new features will extend frontend for unified UX.
f
## Key Integrations
- **Supabase**: Auth (SessionProvider), Realtime (subscriptions for live updates), Storage (file uploads for documents), DB (user data, query history).
- **Neo4j**: Driver for Cypher queries; visualizations using vis-network or Recharts for graph data.
- **Backend Services**: API calls to ingestion supervisor, agentic RAG graph, congress.gov client, n8n workflows.
- **Third-party**: Axios for HTTP, React Query for data fetching/caching, Framer Motion for animations.

## Feature Architecture

### 1. Advanced Search (RAG-based)
- **Page**: `/search` - Search bar with autocomplete (Supabase edge functions or local).
- **Flow**:
  1. User inputs query → Auth check → Send to RAG API (agentic-knowledge-rag-graph/main.py endpoint).
  2. Integrate Neo4j query for entity graph context (e.g., `MATCH (n:Entity)-[r]->(m) WHERE n.name CONTAINS $query RETURN n,r,m`).
  3. Display results: Text snippets from Supabase, graph viz of relations.
  4. Realtime: Subscribe to ingestion updates for fresh data.
- **Components**: SearchInput, ResultsList, GraphViz (using neo4j lib + vis-network).
- **Optimizations**: Debounced search, caching with React Query.

### 2. Data Dashboards
- **Page**: `/dashboard` - Extends existing monitoring; add tabs for RAG metrics, graph stats.
- **Flow**:
  1. Fetch realtime metrics from Supabase (e.g., query counts, storage usage).
  2. Neo4j queries for graph health (node count, relationship density).
  3. Visualizations: Recharts for charts, vis-network for interactive graph explorer.
  4. Auth-protected; role-based views (admin vs user).
- **Components**: DashboardLayout, MetricsChart, GraphExplorer.
- **Optimizations**: Server Components for initial data, Client for interactivity; lazy loading.

### 3. Automated Workflows
- **Page**: `/workflows` - List of n8n workflows, trigger UI.
- **Flow**:
  1. Fetch available workflows from n8n API.
  2. User selects/triggers → POST to n8n webhook with params (e.g., document URL for ingestion).
  3. Status polling via Supabase realtime or WebSockets.
  4. Integrate with Neo4j: Post-workflow, update graph with new entities.
- **Components**: WorkflowList, TriggerModal, StatusTracker.
- **Optimizations**: Toast notifications for feedback, error handling with retries.

### 4. Accessibility & UX Improvements
- **Global**: ARIA labels on forms/icons, keyboard navigation (focus management), semantic HTML.
- **Responsive**: Tailwind classes ensure mobile-first (grid/flex layouts).
- **Performance**: Image optimization (Next Image), code splitting, suspense boundaries.
- **UI Patterns**: Consistent theming, loading skeletons, error boundaries.

## Pages & Components Structure
- **Pages** (App Router):
  - `/` : Landing (existing, add auth guard).
  - `/search` : Advanced search page.
  - `/dashboard` : Unified dashboard (merge with existing).
  - `/workflows` : Workflow management.
  - `/auth` : Supabase auth UI.
- **Components** (`src/components/`):
  - ui/ : Reusable (Button, Card, Modal).
  - Search/ : SearchInput, ResultsCard.
  - Dashboard/ : MetricsCard, GraphViewer.
  - Workflows/ : WorkflowCard, TriggerButton.
- **API Routes** (`src/app/api/`): Proxies for backend (e.g., /api/rag-query).

## Scalability & Best Practices
- **State Management**: React Context for auth, Zustand for UI state if needed.
- **Error Handling**: Global error page, try-catch in queries.
- **Testing**: Add unit tests for components, e2e with Playwright.
- **Deployment**: Dockerized, env vars for configs.

Run `npm install` for new deps (neo4j-driver, @tanstack/react-query, vis-network). Update .env with NEO4J_URI, etc.