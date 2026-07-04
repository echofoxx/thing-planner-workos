# Thing Planner WorkOS v0.3.0

Thing Planner WorkOS is an independently branded, ClickUp-style project/work management platform prototype. v0.3.0 upgrades the full-stack foundation from a single JSON state snapshot into a normalized database model with demo authentication, workspace membership, custom fields, activity logs, and a compatibility API that keeps the current UI working.

## What is new in v0.3.0

- Normalized FastAPI + SQLAlchemy backend schema.
- PostgreSQL-backed relational tables for users, workspaces, members, hierarchy, tasks, comments, dashboards, forms, docs, goals, automations, custom fields, notifications, activity logs, and sessions.
- Demo authentication flow.
- Demo account: `echofoxx@gmail.com` / `thingplanner`.
- Lightweight bearer token support for local prototype use.
- `/api/state` compatibility endpoint now serializes/deserializes normalized tables.
- `/api/schema` endpoint documents the normalized model.
- `/api/activity` endpoint exposes audit/activity events.
- `/api/permissions` endpoint exposes workspace role/permission seed data.
- `/api/custom-fields` endpoint exposes custom field definitions.
- Health endpoint now reports schema, auth status, and table counts.
- Frontend now shows v0.3 Data/Auth status badges.
- More module now includes normalized data and demo auth cards.
- Release docs for auth and database schema.

## What is preserved from v0.2.0

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
- PostgreSQL Docker Compose mode.
- SQLite fallback compose mode.
- LocalStorage fallback if the API is offline.

## Run with Docker Compose, PostgreSQL mode

From PowerShell:

```powershell
cd C:\docker
Expand-Archive -Force "$env:USERPROFILE\Downloads\thing-planner-workos-v0.3.0.zip" "C:\docker\thing-planner-workos-v0.3.0"
cd C:\docker\thing-planner-workos-v0.3.0\thing-planner-workos-v0.3.0
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

## Demo authentication

The frontend automatically requests demo auth when the API is online. You can also test directly:

```powershell
Invoke-RestMethod -Method POST http://localhost:8099/api/auth/demo-login
```

Manual login payload:

```json
{
  "email": "echofoxx@gmail.com",
  "password": "thingplanner"
}
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Backend/database/auth/schema status |
| POST | `/api/auth/login` | Demo login with email/password |
| POST | `/api/auth/demo-login` | One-click demo auth |
| GET | `/api/auth/me` | Current bearer-token user |
| GET | `/api/schema` | Normalized schema description |
| GET | `/api/workspaces/current` | Workspace, members, hierarchy, custom fields |
| GET | `/api/members` | Workspace member list |
| GET | `/api/permissions` | Role and permission seed data |
| GET | `/api/activity` | Activity/audit feed |
| GET | `/api/custom-fields` | Custom field definitions |
| GET | `/api/state` | Load complete UI-compatible workspace state from normalized tables |
| PUT | `/api/state` | Sync UI state back into normalized tables |
| POST | `/api/reset` | Reset database and reseed normalized tables |
| GET | `/api/tasks` | List tasks, optionally filtered by project/status/assignee |
| POST | `/api/tasks` | Create task |
| PATCH | `/api/tasks/{task_id}` | Update task fields |
| DELETE | `/api/tasks/{task_id}` | Delete task |
| POST | `/api/tasks/{task_id}/comments` | Add comment |
| POST | `/api/forms/project-intake` | Create task from intake form |
| GET | `/api/reports/summary` | Dashboard summary metrics |
| POST | `/api/ai/project-summary` | AI summary stub |

## Data model status

v0.3.0 introduces normalized database tables while maintaining compatibility with the existing SPA. The next releases can progressively move each UI module away from full-state sync and onto dedicated backend endpoints.

Key normalized entities:

```text
users, workspaces, workspace_members, spaces, folders, lists, task_statuses,
tasks, task_comments, custom_fields, custom_field_values, notifications,
dashboards, forms, docs, goals, automations, activity_logs, sessions
```

## GitHub update commands

From inside this release folder:

```powershell
git status
git add .
git commit -m "Release Thing Planner WorkOS v0.3.0"
git push origin main
git tag -f v0.3.0
git push origin v0.3.0 --force
```

## Recommended next release: v0.4.0

v0.4.0 should focus on the dashboard/reporting engine:

- Normalized dashboard cards.
- Saved report filters.
- Server-side report endpoints.
- Drill-down records.
- Editable dashboard actions.
- Dashboard card layout persistence.
- AI report summary cards.
- Export-ready executive dashboard views.

## Important product note

This project is independently branded. It intentionally avoids using ClickUp logos, protected assets, product identity, or exact brand copy. The UX pattern is inspired by modern work management tools and your screenshots, but the product should continue as its own WorkOS.
