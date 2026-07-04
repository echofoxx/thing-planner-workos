# Thing Planner WorkOS v0.7.0

**Thing Planner WorkOS** is an AI-native project management/work operating system prototype inspired by modern all-in-one productivity platforms. It includes a ClickUp-style workspace shell, tasks, boards, dashboards, reports, forms, automations, docs, planner, AI assistant, and a normalized API/data foundation.

## v0.7.0 release theme

**Gantt + Dependency / Critical Path Engine**

v0.7.0 makes the Gantt view operational. The app now supports normalized task dependencies, critical-path calculation, schedule-risk analysis, baseline snapshots, and dependency-aware rescheduling/cascade logic.

## What changed in v0.7.0

- New normalized Gantt database tables:
  - `task_dependencies`
  - `gantt_baselines`
  - `gantt_risk_alerts`
- New Gantt API endpoints:
  - `GET /api/gantt?project_id=p1`
  - `GET /api/gantt/critical-path?project_id=p1`
  - `POST /api/gantt/dependencies`
  - `DELETE /api/gantt/dependencies/{dependency_id}`
  - `POST /api/gantt/tasks/{task_id}/schedule`
  - `POST /api/gantt/recalculate?project_id=p1`
  - `POST /api/gantt/baselines`
- Critical path engine:
  - computes longest dependency chain
  - includes explicitly marked critical tasks
  - flags critical blocked work
  - calculates timeline range and projected finish date
- Delay and dependency analysis:
  - detects successors scheduled before predecessor finish date
  - accounts for lag days
  - creates risk alerts for conflicts, overdue work, and blocked critical-path tasks
  - stores risk alerts when Gantt is recalculated
- Dependency-aware scheduling:
  - reschedule task start/duration from the Gantt row
  - optional cascade to dependent successors
  - one-click `+1d` shift
  - automation run history for schedule recalculation
- Gantt UI upgrades:
  - v0.7 Gantt command center
  - Gantt KPI cards
  - date-scaled task bars
  - critical-path bar styling
  - blocked task styling
  - dependency editor
  - AI delay watch panel
  - baseline capture button
  - API-backed sync with local fallback
- `/api/state` now serializes dependencies, baselines, and Gantt risk alerts into the frontend state.
- `/api/health` now reports Gantt table counts.

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
- v0.6 planner/scheduling:
  - calendar events
  - planner blocks
  - working-hour preferences
  - AI daily schedule generation
  - focus blocks and meetings

## Demo login

```text
Email: echofoxx@gmail.com
Password: thingplanner
```

The frontend auto-runs demo auth when the API is available.

## Run with PostgreSQL

```powershell
cd C:\docker
Expand-Archive -Force "$env:USERPROFILE\Downloads\thing-planner-workos-v0.7.0.zip" "C:\docker\thing-planner-workos-v0.7.0"
cd C:\docker\thing-planner-workos-v0.7.0\thing-planner-workos-v0.7.0
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

## Key v0.7 Gantt API endpoints

```text
GET    /api/gantt
GET    /api/gantt/critical-path
POST   /api/gantt/dependencies
DELETE /api/gantt/dependencies/{dependency_id}
POST   /api/gantt/tasks/{task_id}/schedule
POST   /api/gantt/recalculate
POST   /api/gantt/baselines
```

## Existing API endpoints

### Planner

```text
GET    /api/planner
POST   /api/planner/plan-my-day
GET    /api/planner/events
POST   /api/planner/events
POST   /api/planner/tasks/{task_id}/schedule
POST   /api/planner/focus-blocks
DELETE /api/planner/blocks/{block_id}
```

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

Copy the v0.7.0 files into the repo:

```powershell
robocopy `
  "C:\docker\thing-planner-workos-v0.7.0\thing-planner-workos-v0.7.0" `
  "C:\docker\thing-planner-workos-git" `
  /MIR `
  /XD .git .venv __pycache__ `
  /XF *.pyc
```

Commit and tag:

```powershell
git status
git add .
git commit -m "Release Thing Planner WorkOS v0.7.0"
git push origin main

git tag -f v0.7.0
git push origin v0.7.0 --force
```

## Validation performed

- `python3 -m py_compile backend/app/main.py`
- `node --check assets/app.js`
- FastAPI SQLite smoke test against health, schema, state, Gantt dataset, critical path, recalculation, baseline creation, task rescheduling/cascade, and prior API compatibility.

## Next recommended build

**v0.8.0 Docs + Knowledge / Wiki Engine**

Recommended scope:

- normalized doc pages and blocks
- linked docs/tasks/decisions
- rich project docs UI
- SOP/wiki mode
- AI doc summary/action items
- searchable knowledge hub
- protected docs and decision log
