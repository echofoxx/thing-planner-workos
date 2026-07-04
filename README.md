# Thing Planner WorkOS v0.2.0

Thing Planner WorkOS is an independently branded, ClickUp-style project/work management platform prototype. v0.2.0 moves the v0.1 workspace shell into a real full-stack foundation with a FastAPI backend, PostgreSQL-backed persistence, API documentation, and frontend API sync while preserving the polished WorkOS UI.

## What is new in v0.2.0

- FastAPI backend under `/backend`.
- PostgreSQL service in `docker-compose.yml`.
- SQLite fallback compose file for lightweight local testing.
- Persistent workspace state through `/api/state`.
- Task CRUD endpoints under `/api/tasks`.
- Comment endpoint under `/api/tasks/{task_id}/comments`.
- Project intake endpoint under `/api/forms/project-intake`.
- Report endpoint under `/api/reports/summary`.
- AI summary stub endpoint under `/api/ai/project-summary`.
- API health/status endpoint under `/api/health`.
- OpenAPI docs proxied at `/api/docs`.
- Frontend API status pill showing connected/offline mode.
- Frontend syncs workspace changes to the backend when Docker Compose is running.
- LocalStorage fallback still works when the API is offline.
- Data Layer Status cards under **More**.

## What is preserved from v0.1.0

- Purple global app rail.
- Context sidebars.
- Home / Inbox.
- Spaces hierarchy.
- Project task List, Board, Calendar, Gantt, and Table views.
- Task drawer.
- Dashboard templates and actionable reports.
- Forms template page and project intake builder.
- AI assistant page.
- Planner, automations, docs, goals, teams, clips, and whiteboard starter modules.

## Run with Docker Compose, PostgreSQL mode

From PowerShell:

```powershell
cd C:\docker
Expand-Archive -Force "$env:USERPROFILE\Downloads\thing-planner-workos-v0.2.0.zip" "C:\docker\thing-planner-workos-v0.2.0"
cd C:\docker\thing-planner-workos-v0.2.0\thing-planner-workos-v0.2.0
docker compose up --build -d
```

Open the app:

```text
http://localhost:8098
```

Open the API directly:

```text
http://localhost:8099/api/health
```

Open API docs through the web proxy:

```text
http://localhost:8098/api/docs
```

## Run with SQLite fallback instead of PostgreSQL

```powershell
docker compose -f docker-compose.sqlite.yml up --build -d
```

This runs the same API but persists to a Docker volume-backed SQLite database.

## Run frontend only

Open `index.html` directly or host it with:

```bash
python3 -m http.server 8098
```

The app will run in local fallback mode and will show `API offline - local mode` in the top bar.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Backend/database status |
| GET | `/api/state` | Load complete workspace state |
| PUT | `/api/state` | Save complete workspace state |
| POST | `/api/reset` | Reset backend seed data |
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create task |
| PATCH | `/api/tasks/{task_id}` | Update task fields |
| DELETE | `/api/tasks/{task_id}` | Delete task |
| POST | `/api/tasks/{task_id}/comments` | Add comment |
| POST | `/api/forms/project-intake` | Create task from intake form |
| GET | `/api/reports/summary` | Dashboard summary metrics |
| POST | `/api/ai/project-summary` | AI summary stub |

## Data model status

v0.2.0 uses a durable `state_snapshots` table to persist the full workspace JSON state. This is intentionally simple so the prototype can evolve quickly. The API already exposes task-level endpoints so the next release can progressively normalize the data model into dedicated tables for users, workspaces, spaces, folders, lists, tasks, comments, dashboards, forms, automations, docs, and AI agents.

## Recommended next release: v0.3.0

v0.3.0 should normalize the database and add real authentication:

- Workspace/user/member tables.
- Task/comment/custom field tables.
- JWT/session authentication.
- User invite flow.
- Role-based permissions.
- API-backed forms and dashboards.
- Migration scripts.
- Better API error handling.
- Seed data loader.
- GitHub repo release workflow.

## Important product note

This project is independently branded. It intentionally avoids using ClickUp logos, protected assets, product identity, or exact brand copy. The UX pattern is inspired by modern work management tools and your screenshots, but the product should continue as its own WorkOS.
