# Thing Planner WorkOS v0.6.0

**Thing Planner WorkOS** is an AI-native project management/work operating system prototype inspired by modern all-in-one productivity platforms. It includes a ClickUp-style workspace shell, tasks, boards, dashboards, reports, forms, automations, docs, planner, AI assistant, and a normalized API/data foundation.

## v0.6.0 release theme

**Planner + AI Scheduling Engine**

v0.6.0 makes the Planner operational. The app can generate a priority-based daily schedule from tasks, due dates, estimates, critical-path flags, calendar events, focus blocks, and working-hour preferences.

## What changed in v0.6.0

- New normalized planner database tables:
  - `calendar_events`
  - `planner_blocks`
  - `planner_preferences`
- New Planner API endpoints:
  - `GET /api/planner`
  - `POST /api/planner/plan-my-day`
  - `GET /api/planner/events`
  - `POST /api/planner/events`
  - `POST /api/planner/tasks/{task_id}/schedule`
  - `POST /api/planner/focus-blocks`
  - `DELETE /api/planner/blocks/{block_id}`
- AI daily scheduling engine:
  - ranks work by priority, due date, critical path, blocked status, and progress
  - creates AI-generated time blocks
  - excludes blocked work unless preferences allow it
  - respects working hours, lunch, existing meetings, and focus blocks
  - creates risk warnings for overdue, blocked, or under-planned work
- Planner UI upgrades:
  - day selector and week strip
  - Priority Queue with one-click scheduling
  - Today timeline with meetings, focus, task blocks, and AI blocks
  - AI delay watch panel
  - planner KPI cards
  - Add focus block
  - Add meeting
  - Clear AI schedule
  - API-backed planner sync with local fallback
- More page data-layer cards now include schedule objects.
- `/api/state` now serializes planner events, planner blocks, and planner preferences into the frontend state.

## What was already included

- ClickUp-style UI shell:
  - purple global navigation rail
  - contextual sidebars
  - top search and AI bar
  - Spaces, Home, Forms, Dashboards, Planner, AI, Docs, Goals, Teams, Whiteboards, and More modules
- Task and project management:
  - Spaces / folders / project lists
  - List, Board, Calendar, Gantt, and Table views
  - Task drawer
  - comments, assignees, statuses, priorities, tags, estimates, tracked time, billable flag
- v0.2+ API/data layer:
  - FastAPI backend
  - PostgreSQL Docker service
  - SQLite fallback compose file
  - `/api/state` compatibility layer
- v0.3+ normalized database/auth foundation:
  - users, workspaces, members, spaces, folders, lists, task statuses, tasks, comments, custom fields, notifications, dashboards, forms, docs, goals, automations, sessions, activity logs
  - demo login with bearer token
- v0.4+ reporting engine:
  - report cards
  - server-side dashboard dataset
  - drill-down records
  - dashboard actions that update tasks
- v0.5 forms/intake automation:
  - form submissions
  - automation runs
  - connected Project Intake form
  - AI intake analysis stub
  - automatic task creation from form submissions

## Demo login

```text
Email: echofoxx@gmail.com
Password: thingplanner
```

The frontend auto-runs demo auth when the API is available.

## Run with PostgreSQL

```powershell
cd C:\docker
Expand-Archive -Force "$env:USERPROFILE\Downloads\thing-planner-workos-v0.6.0.zip" "C:\docker\thing-planner-workos-v0.6.0"
cd C:\docker\thing-planner-workos-v0.6.0\thing-planner-workos-v0.6.0
docker compose up --build -d
```

Open the app:

```text
http://localhost:8098
```

API health:

```text
http://localhost:8099/api/health
```

API docs:

```text
http://localhost:8098/api/docs
```

## SQLite fallback

Use this if you want a simpler local backend without PostgreSQL:

```powershell
docker compose -f docker-compose.sqlite.yml up --build -d
```

## Key v0.6 Planner API endpoints

```text
GET    /api/planner
POST   /api/planner/plan-my-day
GET    /api/planner/events
POST   /api/planner/events
POST   /api/planner/tasks/{task_id}/schedule
POST   /api/planner/focus-blocks
DELETE /api/planner/blocks/{block_id}
```

## Existing API endpoints

### Forms

```text
GET  /api/forms
GET  /api/forms/{form_id}
PUT  /api/forms/{form_id}/schema
POST /api/forms/{form_id}/submissions
GET  /api/forms/{form_id}/submissions
GET  /api/forms/{form_id}/analytics
POST /api/forms/project-intake
```

### Automations

```text
GET   /api/automations
POST  /api/automations
PATCH /api/automations/{automation_id}/toggle
POST  /api/automations/run
GET   /api/automations/templates
```

### Reporting

```text
GET  /api/reports/dashboard
GET  /api/reports/drilldown
POST /api/reports/actions
GET  /api/reports/cards
POST /api/reports/cards
```

## Suggested GitHub update

Use your clean repo folder:

```powershell
cd C:\docker\thing-planner-workos-git
```

Copy the v0.6.0 files into the repo:

```powershell
robocopy `
  "C:\docker\thing-planner-workos-v0.6.0\thing-planner-workos-v0.6.0" `
  "C:\docker\thing-planner-workos-git" `
  /MIR `
  /XD .git .venv __pycache__ `
  /XF *.pyc
```

Commit and tag:

```powershell
git status
git add .
git commit -m "Release Thing Planner WorkOS v0.6.0"
git push origin main

git tag -f v0.6.0
git push origin v0.6.0 --force
```

## Validation performed

- `python3 -m py_compile backend/app/main.py`
- `node --check assets/app.js`
- FastAPI SQLite smoke test against health, schema, planner, plan-my-day, focus block creation, frontend JavaScript syntax, and prior API compatibility.

## Next recommended build

**v0.7.0 Gantt + Dependency / Critical Path Engine**

Recommended scope:

- normalized task dependency table
- Gantt API endpoints
- dependency editor
- critical path calculation
- baseline dates
- AI delay propagation
- reschedule dependent work
- portfolio timeline rollup
