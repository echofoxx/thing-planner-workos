# Thing Planner WorkOS v0.4.0

Thing Planner WorkOS is an independently branded, ClickUp-style project/work management platform prototype. **v0.4.0** upgrades the product from a normalized data/auth foundation into a **dashboard and reporting engine** where reports are connected to source tasks and can update work directly from dashboard cards.

## What is new in v0.4.0

- v0.4 dashboard/reporting engine.
- Server-side report dataset endpoint: `/api/reports/dashboard`.
- Server-side report summary endpoint with filters: `/api/reports/summary`.
- Drill-down endpoint: `/api/reports/drilldown`.
- Report card registry endpoint: `/api/reports/cards`.
- Report action endpoint: `/api/reports/actions`.
- New normalized `report_cards` table.
- Default seeded report cards:
  - Open Tasks
  - Blocked Work
  - Billable Hours
  - Project Health
  - Work by Status
  - Team Productivity
  - Actionable Work Table
- Dashboard report filters for All Work, Project 1, and Project 2.
- Dashboard cards now support drill-down into source records.
- Actionable report tables allow users to update status, owner, due date, billable flag, and open source tasks.
- Risk and blocker action queue.
- AI Project Health card tied to live task data.
- Report API fallback: if the API is offline, the frontend derives reports locally.
- Health endpoint now reports `reporting-v0.4` schema and report card table counts.

## What is preserved from v0.3.0

- FastAPI backend.
- PostgreSQL Docker service.
- SQLite fallback compose file.
- Normalized SQLAlchemy schema.
- Demo authentication.
- Demo account: `echofoxx@gmail.com` / `thingplanner`.
- Workspace members and permissions seed model.
- `/api/state` compatibility endpoint.
- Task CRUD API.
- Comments API.
- Project intake API.
- Activity logs.
- Custom fields.
- Frontend localStorage fallback.
- Purple ClickUp-style global rail and contextual sidebars.
- Spaces, List, Board, Calendar, Gantt, and Table views.
- Forms, AI, planner, docs, goals, whiteboards, teams, clips, and automation starter modules.

## Run with Docker Compose, PostgreSQL mode

From PowerShell:

```powershell
cd C:\docker
Expand-Archive -Force "$env:USERPROFILE\Downloads\thing-planner-workos-v0.4.0.zip" "C:\docker\thing-planner-workos-v0.4.0"
cd C:\docker\thing-planner-workos-v0.4.0\thing-planner-workos-v0.4.0
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

## Reporting API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/reports/summary` | Derived report metrics with optional project/status/assignee/tag filters |
| GET | `/api/reports/dashboard` | Dashboard metadata, report cards, live dataset, and supported actions |
| GET | `/api/reports/drilldown?metric=blocked_tasks` | Source task records behind a metric |
| GET | `/api/reports/cards` | Report card definitions for a dashboard |
| POST | `/api/reports/cards` | Create a new report card |
| POST | `/api/reports/actions` | Apply a dashboard action to a source task |

Supported report actions:

- `set_status`
- `assign`
- `set_due`
- `toggle_billable`
- `add_comment`
- `create_followup`

Example report action:

```json
{
  "task_id": "t5",
  "action": "set_status",
  "value": "IN PROGRESS"
}
```

## Other API endpoints

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
| POST | `/api/ai/project-summary` | AI summary stub |

## Data model status

v0.4.0 keeps the v0.3 normalized schema and adds reporting structures.

Key normalized entities:

```text
users, workspaces, workspace_members, spaces, folders, lists, task_statuses,
tasks, task_comments, custom_fields, custom_field_values, notifications,
dashboards, report_cards, forms, docs, goals, automations, activity_logs, sessions
```

## GitHub update commands

Use a clean working repo folder such as:

```powershell
C:\docker\thing-planner-workos-git
```

Copy the v0.4.0 files into that clean repo, then run:

```powershell
git status
git add .
git commit -m "Release Thing Planner WorkOS v0.4.0"
git push origin main
git tag -f v0.4.0
git push origin v0.4.0 --force
```

## Recommended next release: v0.5.0

v0.5.0 should focus on **forms and intake automation**:

- Normalized form builder tables.
- Form field schema editor.
- Submission records.
- Field-to-task mapping.
- Conditional logic.
- Public form submission page.
- AI form classification.
- Intake dashboards.
- Form-triggered automations.

## Important product note

This project is independently branded. It intentionally avoids using ClickUp logos, protected assets, product identity, or exact brand copy. The UX pattern is inspired by modern work management tools and your screenshots, but the product should continue as its own WorkOS.
