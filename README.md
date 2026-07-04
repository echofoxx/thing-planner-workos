# Thing Planner WorkOS v0.5.0

**Thing Planner WorkOS** is an AI-native project management/work operating system prototype inspired by modern all-in-one productivity platforms. It includes a ClickUp-style workspace shell, tasks, boards, dashboards, reports, forms, automations, docs, planner, AI assistant, and a normalized API/data foundation.

## v0.5.0 release theme

**Forms + Intake Automation Engine**

v0.5.0 makes Forms operational. Form submissions now create mapped tasks, run AI intake analysis, notify owners, record automation run history, and feed dashboard/reporting data.

## What is included

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
  - normalized `form_submissions`
  - normalized `automation_runs`
  - form schemas and field mappings
  - connected Project Intake form
  - AI intake analysis stub
  - automatic task creation
  - intake comments and owner notifications
  - automation templates
  - automation run history
  - form analytics by department, priority, and duplicate watch

## Demo login

```text
Email: echofoxx@gmail.com
Password: thingplanner
```

The frontend auto-runs demo auth when the API is available.

## Run with PostgreSQL

```powershell
cd C:\docker
Expand-Archive -Force "$env:USERPROFILE\Downloads\thing-planner-workos-v0.5.0.zip" "C:\docker\thing-planner-workos-v0.5.0"
cd C:\docker\thing-planner-workos-v0.5.0\thing-planner-workos-v0.5.0
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

## Key v0.5 API endpoints

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

Copy the v0.5.0 files into the repo:

```powershell
robocopy `
  "C:\docker\thing-planner-workos-v0.5.0\thing-planner-workos-v0.5.0" `
  "C:\docker\thing-planner-workos-git" `
  /MIR `
  /XD .git .venv __pycache__ `
  /XF *.pyc
```

Commit and tag:

```powershell
git status
git add .
git commit -m "Release Thing Planner WorkOS v0.5.0"
git push origin main

git tag -f v0.5.0
git push origin v0.5.0 --force
```

## Validation performed

- `python3 -m py_compile backend/app/main.py`
- `node --check assets/app.js`
- FastAPI SQLite smoke test against health, state, forms, submissions, analytics, automations, templates, reports, login, form submission, and manual automation run.

## Next recommended build

**v0.6.0 Planner + AI Scheduling Engine**

Recommended scope:

- calendar event model
- planner database tables
- task time-blocking
- working hours and capacity preferences
- AI daily plan endpoint
- schedule conflict detection
- auto-reschedule suggestions
- planner UI upgrades
