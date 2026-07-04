# Build Plan

## Product goal

Build an AI-native WorkOS for project management that combines tasks, projects, docs, dashboards, forms, planner, whiteboards, goals, reports, automations, AI agents, and collaboration.

## Build sequence

1. Preserve the v0.1 front-end shell.
2. Add a backend API and PostgreSQL schema.
3. Replace localStorage with API persistence.
4. Add auth and workspace membership.
5. Harden task management.
6. Add custom fields and form persistence.
7. Add dashboard card persistence and query engine.
8. Add automation event bus.
9. Add AI/RAG service.
10. Add integrations and enterprise admin.

## Core data entities

- users
- workspaces
- workspace_members
- roles
- permissions
- spaces
- folders
- lists
- views
- tasks
- subtasks
- comments
- attachments
- activity
- dependencies
- custom_fields
- custom_field_values
- forms
- form_submissions
- dashboards
- dashboard_cards
- docs
- doc_pages
- automations
- automation_runs
- ai_agents
- ai_agent_runs
- notifications
- goals
- time_entries
- integrations
- webhooks
- audit_logs

## Recommended production stack

- Frontend: React + Vite, TypeScript, Tailwind CSS, shadcn-style components, DnD Kit, TanStack Table
- API: FastAPI or NestJS
- Database: PostgreSQL
- Cache/jobs: Redis
- Files: MinIO or S3
- Search: Meilisearch/OpenSearch
- AI/RAG: Qdrant + OpenAI-compatible provider + optional Ollama
- Realtime: WebSockets
- Deployment: Docker Compose first, Kubernetes later
