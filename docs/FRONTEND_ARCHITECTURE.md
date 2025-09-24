# Frontend Architecture

## Overview

The frontend is a Next.js 14 application using the App Router, serving as the unified dashboard for the Local AI Package. It integrates Supabase for authentication, realtime data, and storage, Neo4j for graph queries/visualization, and backend services for RAG search, workflows, and metrics. The architecture supports legislative analysis features like advanced search, dashboards, and workflow triggers.

Built with TypeScript, Tailwind CSS, and React components for responsive UI. Focuses on accessibility, performance, and seamless integration with the backend stack.

For services, see [Services](services.md). For deployment, see [Deployment](deployment.md).

## Table of Contents

1. [Key Integrations](#key-integrations)
2. [Project Structure](#project-structure)
3. [Pages and Routing](#pages-and-routing)
4. [Components](#components)
5. [API Routes](#api-routes)
6. [Authentication Flow](#authentication-flow)
7. [Data Fetching and State Management](#data-fetching-and-state-management)
8. [Testing](#testing)
9. [Deployment and Configuration](#deployment-and-configuration)

## Key Integrations

- **Supabase**: Auth (SessionProvider), Realtime subscriptions (live updates for queries/results), Storage (document uploads for ingestion), Database (user data, query history via REST/RPC).
- **Neo4j**: Driver for Cypher queries; vis-network/Recharts for graph visualization (e.g., bill-sponsor relationships).
- **Backend Services**: Axios calls to agentic-rag API (RAG queries), n8n webhooks (workflow triggers), ingestion supervisor (status).
- **Third-Party**: React Query (TanStack Query) for caching/fetching, Framer Motion for animations, Tailwind for styling.

Dependencies in frontend/package.json: next, react, @supabase/supabase-js, neo4j-driver, @tanstack/react-query, axios, framer-motion.

## Project Structure

```
frontend/
├── Dockerfile
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
├── package.json
├── src/
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx  # Root layout with providers
│   │   ├── page.tsx  # Landing page
│   │   ├── dashboard/
│   │   │   ├── page.tsx
│   │   │   └── components/  # Dashboard-specific
│   │   ├── search/
│   │   │   └── page.tsx
│   │   ├── workflows/
│   │   │   └── page.tsx
│   │   ├── api/
│   │   │   ├── search/
│   │   │   │   └── route.ts  # Proxy to RAG API
│   │   │   └── workflows/
│   │   │       └── route.ts  # n8n triggers
│   │   └── auth/
│   │       └── callback/
│   │           └── route.ts  # Supabase auth
│   ├── components/
│   │   ├── ui/  # Reusable (Button, Modal, Card)
│   │   ├── dashboard/  # MetricsChart, GraphViewer
│   │   ├── search/  # SearchInput, ResultsList
│   │   └── workflows/  # WorkflowList, TriggerModal
│   ├── lib/
│   │   ├── supabase.ts  # Client init
│   │   ├── neo4j.ts  # Driver connection
│   │   └── utils.ts  # Helpers (auth, queries)
│   └── hooks/
│       └── useAuth.ts  # Custom auth hook
└── public/  # Static assets
```

## Pages and Routing (App Router)

Uses Next.js App Router for server-side rendering and API routes.

- **/** (page.tsx): Landing page with auth guard; redirects to /dashboard if logged in.
- **/dashboard** (dashboard/page.tsx): Unified dashboard with tabs (metrics, graphs, workflows). Fetches realtime data from Supabase.
- **/search** (search/page.tsx): Advanced RAG search; autocomplete, results with snippets/graph viz.
- **/workflows** (workflows/page.tsx): List/trigger n8n workflows; status polling.
- **/auth** (auth/page.tsx): Supabase auth UI (sign in/up).
- **/api/**: Server-side API proxies (e.g., /api/search/route.ts → agentic-rag:8000).

Routing: File-based (app/[slug]/page.tsx). Middleware for auth (middleware.ts).

## Components

Reusable in `src/components/`; shadcn/ui style with Tailwind.

### UI Components (ui/)
- **Button, Card, Modal**: Base UI from shadcn.
- **Input, Table**: Forms and data display.

### Feature Components

| Component | Location | Description | Dependencies |
|-----------|----------|-------------|--------------|
| **SearchInput** | search/SearchInput.tsx | Search bar with debounce/autocomplete (Supabase edge function). | React Query |
| **ResultsList** | search/ResultsList.tsx | Displays RAG results (text snippets, sources). | Axios |
| **GraphViewer** | dashboard/GraphViewer.tsx | Interactive Neo4j graph (vis-network); entities/relations. | neo4j-driver, vis-network |
| **MetricsChart** | dashboard/MetricsChart.tsx | Recharts for CPU/DB metrics (from Supabase). | Recharts |
| **WorkflowList** | workflows/WorkflowList.tsx | Lists n8n workflows; trigger buttons. | Axios |
| **TriggerModal** | workflows/TriggerModal.tsx | Modal for workflow params (e.g., bill ID). | Framer Motion |

Global: ThemeProvider, Toast (notifications), ErrorBoundary.

## API Routes

Server-side endpoints in `src/app/api/` (route.ts files).

- **/api/search/route.ts** (POST): Proxy to agentic-rag /rag/query; body: {query, sessionId}.
  ```typescript
  import { NextRequest, NextResponse } from 'next/server';
  import { createClient } from '@/lib/supabase';

  export async function POST(request: NextRequest) {
    const body = await request.json();
    const supabase = createClient();
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });

    const response = await fetch('http://agentic-rag:8000/rag/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return NextResponse.json(await response.json());
  }
  ```

- **/api/workflows/route.ts** (POST): Triggers n8n webhook; body: {workflowId, params}.
- **/api/auth/callback/route.ts**: Supabase auth callback.

All routes: Auth check (Supabase), error handling, CORS.

## Authentication Flow

Uses Supabase Auth with NextAuth provider.

1. **Sign In**: /auth/signin → Supabase signInWithPassword/email.
2. **Session**: SessionProvider in layout.tsx; useSession hook.
3. **Protected Routes**: Middleware redirects unauth to /auth.
4. **Realtime**: Subscribe to user-specific channels (e.g., query updates).
5. **Role-Based**: Check user roles in Supabase (admin for workflows).

Example hook (`hooks/useAuth.ts`):
```typescript
import { useSupabaseClient } from '@supabase/auth-helpers-react';

export function useAuth() {
  const supabase = useSupabaseClient();
  const [session, setSession] = useState(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => setSession(session));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => setSession(session));
    return () => subscription.unsubscribe();
  }, []);

  return { session };
}
```

## Data Fetching and State Management

- **React Query**: Caching for API calls (queries/mutations); infinite queries for pagination.
  - Example: useQuery for dashboard metrics (key: ['metrics'], fetcher: supabase.from('metrics').select()).
- **Realtime**: Supabase subscriptions for live updates (e.g., ingestion status).
- **Context**: AuthContext for user session.
- **Zustand** (optional): Local state for UI (e.g., search filters).

Optimizations: Server Components for initial load, Client for interactivity; suspense for loading.

## Testing

- **Unit (Jest)**: Components (e.g., `npm test -- src/components/ui/Button.test.tsx`).
  - Coverage: 80%+; run `npm test -- --coverage`.
- **E2E (Playwright)**: Flows (login, search, workflow trigger).
  - Config: playwright.config.ts; run `npx playwright test`.
- **Integration**: API routes with supabase-mock.

Example Jest test:
```typescript
import { render, screen } from '@testing-library/react';
import SearchInput from './SearchInput';

test('renders search input', () => {
  render(<SearchInput />);
  expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
});
```

## Deployment and Configuration

- **Build**: `docker build -t frontend .` (Dockerfile with multi-stage for prod).
- **Env Vars**: NEXT_PUBLIC_SUPABASE_URL/ANON_KEY, NEXTAUTH_SECRET, DATABASE_URL in .env.
- **Proxy**: Traefik/Caddy routes to 3000; public: FRONTEND_HOSTNAME=yourdomain.com.
- **Performance**: Image optimization (next/image), code splitting, lazy loading.

See [Deployment](deployment.md) for Docker/Compose setup.

This architecture ensures a responsive, secure frontend for AI-driven analysis.