# Thing Planner WorkOS v0.8.0

**Thing Planner WorkOS** is an AI-native project management/work operating system prototype inspired by modern all-in-one productivity platforms. It includes a ClickUp-style workspace shell, tasks, boards, dashboards, reports, forms, automations, planner, Gantt, docs, wiki, decisions, AI assistant, and a normalized API/data foundation.

## v0.8.0 release theme

**Docs + Knowledge / Wiki Engine**

v0.8.0 turns Docs from placeholders into an operational knowledge layer. The app now supports normalized docs, wiki pages, version history, structured decision records, task-linked knowledge, knowledge search, and AI document summaries.

## What changed in v0.8.0

- New normalized knowledge tables:
  - `doc_pages`
  - `doc_versions`
  - `doc_task_links`
  - `doc_decisions`
- New Docs and Knowledge API endpoints:
  - `GET /api/docs`
  - `GET /api/docs/{doc_id}`
  - `POST /api/docs`
  - `PATCH /api/docs/{doc_id}`
  - `POST /api/docs/{doc_id}/links`
  - `POST /api/docs/{doc_id}/decisions`
  - `POST /api/docs/{doc_id}/ai-summary`
  - `GET /api/knowledge/search?q=...`
  - `GET /api/knowledge/hub`
- Docs module upgrades:
  - Knowledge command center KPI cards
  - Docs/wiki/decision search
  - Doc list and editor workbench
  - Markdown-style editing area
  - Page tabs and version history panel
  - Linked-task insight panel
  - Structured decisions panel
  - AI document brief modal
  - Local fallback mode when API is offline
- Knowledge automation support:
  - `auto_doc_decision`
  - `auto_doc_ai_summary`
  - automation run records when decisions are captured or AI summaries are generated
- `/api/state` now serializes doc content, pages, decision counts, link counts, and knowledge stats into the frontend state.
- `/api/health` now reports Docs/Knowledge table counts.

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
- v0.7 Gantt/dependencies:
  - dependencies
  - critical path calculation
  - schedule risk alerts
  - baselines
  - dependency-aware rescheduling

## Demo login

```text
Email: echofoxx@gmail.com
Password: thingplanner
```

The frontend auto-runs demo auth when the API is available.

## Run with PostgreSQL

```powershell
cd C:\docker
Expand-Archive -Force "$env:USERPROFILE\Downloads\thing-planner-workos-v0.8.0.zip" "C:\docker\thing-planner-workos-v0.8.0"
cd C:\docker\thing-planner-workos-v0.8.0\thing-planner-workos-v0.8.0
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

## SQLite fallback mode

```powershell
docker compose -f docker-compose.sqlite.yml up --build -d
```

## GitHub release workflow

Use your clean repo folder:

```powershell
cd C:\docker\thing-planner-workos-git
```

Copy v0.8.0 into the repo:

```powershell
robocopy `
  "C:\docker\thing-planner-workos-v0.8.0\thing-planner-workos-v0.8.0" `
  "C:\docker\thing-planner-workos-git" `
  /MIR `
  /XD .git .venv __pycache__ `
  /XF *.pyc
```

Commit and tag:

```powershell
git status
git add .
git commit -m "Release Thing Planner WorkOS v0.8.0"
git push origin main

git tag -f v0.8.0
git push origin v0.8.0 --force
```

## Recommended next build

**v0.9.0 Whiteboards + Canvas / Mind Map Engine**

Recommended scope:

- persistent whiteboards
- sticky notes, shapes, connectors, and embedded task cards
- convert sticky note to task
- canvas cards linked to dashboards, goals, docs, and Gantt tasks
- mind map view for task hierarchy and project breakdown
- AI whiteboard summary and action-plan generation
