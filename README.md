# Thing Planner WorkOS v0.9.2

**Thing Planner WorkOS** is an AI-native project management/work operating system prototype inspired by modern all-in-one productivity platforms. It includes a ClickUp-style workspace shell, tasks, boards, dashboards, reports, forms, automations, planner, Gantt, docs, wiki, decisions, AI assistant, whiteboards, canvas planning, mind maps, and a normalized API/data foundation.

## v0.9.2 release theme

## Critical fix

- Fixes PostgreSQL startup failure: `automation_runs.automation_id` referenced `auto_visual_seed` before that automation existed.
- `record_automation_run()` now guarantees missing system/visual automations are created before recording run history.
- This should clear the browser top-bar state from `API offline / local mode` and `Demo auth pending` once Docker services are running.


**UI Cleanup + Connected Functional Shell**

v0.9.2 is an API startup hotfix release. It keeps the v0.9.1 cleaned-up UI and fixes the PostgreSQL foreign-key startup crash caused by visual-collaboration automation run seeding before the visual automation records existed.

## What changed in v0.9.2

## v0.9.2 API startup hotfix

- Global rail now shows exactly the top 9 primary modules:
  - Home
  - Spaces
  - Planner
  - AI
  - Teams
  - Docs
  - Dashboard
  - Whiteboard
  - Forms
- Removed distracting promo banner and feedback popups from the default workspace.
- Removed lower Invite/Upgrade rail buttons from the primary navigation.
- Reworked the top bar status badges into compact connection pills.
- Added API reconnect behavior with retries while Docker services start.
- Added fallback API discovery for `/api`, `localhost:8099/api`, and `127.0.0.1:8099/api`.
- Demo auth now auto-runs when the API is reachable and shows a signed-in state.
- Quick Add Task no longer opens a browser prompt; it creates a task and opens the task drawer.
- Gantt baseline capture no longer opens a prompt; it creates a timestamped baseline automatically.
- Sidebar plus buttons now perform useful actions instead of placeholder popups where possible.

## v0.9.0 visual collaboration changes retained

- New normalized visual collaboration tables:
  - `whiteboards`
  - `whiteboard_objects`
  - `whiteboard_edges`
  - `canvas_cards`
  - `mind_map_nodes`
- New Whiteboard API endpoints:
  - `GET /api/whiteboards`
  - `GET /api/whiteboards/{whiteboard_id}`
  - `POST /api/whiteboards`
  - `POST /api/whiteboards/{whiteboard_id}/objects`
  - `POST /api/whiteboards/{whiteboard_id}/canvas-cards`
  - `POST /api/whiteboards/{whiteboard_id}/mind-map-nodes`
  - `POST /api/whiteboards/{whiteboard_id}/ai-summary`
- Whiteboards module upgrades:
  - Board list with selected-board switching
  - Visual KPI cards for objects, edges, canvas cards, and mind-map nodes
  - Interactive visual workspace tabs: Whiteboard, Canvas, Mind Map
  - Sticky notes, task cards, doc cards, and relationship edges
  - Select visual object, link object to task, and convert sticky note to task
  - Canvas cards linked to project/list, dashboard, form, doc, and Gantt work
  - Mind map view for the WorkOS module hierarchy and feature breakdown
  - AI visual summary with action items and risk prompts
  - Local fallback mode when the API is offline
- `/api/state` now serializes whiteboards, objects, canvas cards, and mind maps into the frontend state.
- `/api/health` now reports visual collaboration table counts.

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
- v0.8 Docs/knowledge:
  - docs, wiki pages, versions, decision records, linked-task records, AI document summaries, and knowledge search

## Demo login

```text
Email: echofoxx@gmail.com
Password: thingplanner
```

The frontend auto-runs demo auth when the API is available.

## Run with PostgreSQL

```powershell
cd C:\docker
Expand-Archive -Force "$env:USERPROFILE\Downloads\thing-planner-workos-v0.9.2.zip" "C:\docker\thing-planner-workos-v0.9.2"
cd C:\docker\thing-planner-workos-v0.9.2\thing-planner-workos-v0.9.2
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

Copy v0.9.2 into the repo:

```powershell
robocopy `
  "C:\docker\thing-planner-workos-v0.9.2\thing-planner-workos-v0.9.2" `
  "C:\docker\thing-planner-workos-git" `
  /MIR `
  /XD .git .venv __pycache__ `
  /XF *.pyc
```

Commit and tag:

```powershell
git status
git add .
git commit -m "Release Thing Planner WorkOS v0.9.2 API startup hotfix"
git push origin main

git tag -f v0.9.2
git push origin v0.9.2 --force
```

## Recommended next build

**v1.0.0 Production Demo Hardening**

Recommended scope:

- polished auth/login page and workspace onboarding
- migration-safe database startup
- API error handling and validation pass
- full release documentation and screenshots
- seeded executive demo workspace
- GitHub Actions / local smoke-test script
- production Docker compose cleanup
- UI polish and bug sweep across all modules
