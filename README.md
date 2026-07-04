# Thing Planner WorkOS v0.9.3 Functional Release

Thing Planner WorkOS is a local-first, API-backed project/work operating system prototype with a ClickUp-style workspace shell, Spaces, tasks, boards, dashboards, reports, forms, automations, planner, Gantt scheduling, docs, knowledge, teams, goals, clips, whiteboards, canvas planning, and mind maps.

This v0.9.3 package is a functional hardening pass over the attached v0.9.2 build. The goal of this release is to remove partially wired behavior, make the primary workflows actually change state, and ensure frontend-created work can persist through the backend API.

## What was fixed in v0.9.3

- Updated stale v0.9.1/v0.9.2 labels, storage keys, auth token keys, page title, and API status text to v0.9.3.
- Removed duplicate older JavaScript function definitions that were silently overriding or confusing feature behavior.
- Disabled the distracting helper/promo popups by default, including after API hydration.
- Replaced placeholder actions with functional demo actions for Spaces, project lists, report cards, form builder fields, AI form improvements, automation templates, weekly planning, AI agent creation, team standups, goals, clips, invites, upgrades, and new automations.
- Reworked the Spaces tree so it renders dynamic spaces, folders, and lists instead of only hard-coded Project 1 / Project 2 links.
- Fixed Canvas/Mind Map navigation so linked list/project/view cards open the relevant module or view.
- Hardened `/api/state` persistence so frontend-created members, spaces, folders, lists, dashboards, goals, forms, submissions, automations, automation runs, tasks, comments, notifications, and whiteboards sync into normalized tables without foreign-key errors.
- Added a backend safeguard so new frontend project/list IDs are created before tasks reference them.
- Improved frontend API sync so failed `/api/state` saves are detected instead of silently appearing successful.

## Primary modules

The top rail intentionally focuses on the nine primary modules:

1. Home
2. Spaces
3. Planner
4. AI
5. Teams
6. Docs
7. Dashboard
8. Whiteboard
9. Forms

Additional modules such as Automations, Goals, Clips, Invite, and Upgrade remain available through the app shell and internal routes, but they are no longer distracting primary rail items.

## Running with Docker + PostgreSQL

```powershell
cd C:/docker/thing-planner-workos-v0.9.3-functional
docker compose up --build -d
```

Open:

- Web app: `http://localhost:8098`
- API: `http://localhost:8099/api/health`
- API docs: `http://localhost:8099/docs`

The web container proxies `/api/*` to the FastAPI service. The top bar should move from local/offline mode to API connected once the API is ready.

## Running with Docker + SQLite fallback

Use this when you want a lighter local demo without PostgreSQL:

```powershell
cd C:/docker/thing-planner-workos-v0.9.3-functional
docker compose -f docker-compose.sqlite.yml up --build -d
```

Open `http://localhost:8098`.

## Demo auth

The app attempts demo auth automatically when the API is reachable. The demo account is:

- Email: `echofoxx@gmail.com`
- Password: local demo password managed by the seeded API

The UI uses a bearer token stored under the v0.9.3 token key and migrates older v0.9.1/v0.9.2 local storage where available.

## Functional validation completed

Validated in the sandbox with:

- `python -m py_compile backend/app/main.py`
- `node --check assets/app.js`
- FastAPI TestClient smoke tests against SQLite for:
  - `/api/health`
  - `/api/state`
  - `/api/tasks`
  - `/api/forms`
  - `/api/planner`
  - `/api/gantt`
  - `/api/docs`
  - `/api/whiteboards`
  - `/api/reports/dashboard`
  - `/api/knowledge/hub`
  - task create / update / comment
  - form intake submission
  - planner event creation
  - Gantt dependency creation
  - `/api/state` PUT with a dynamically created Space/List/Task
- Frontend Node VM smoke test across Home, Spaces, Planner, AI, Teams, Docs, Dashboard, Whiteboard, Forms, More/Automations, Goals, Clips, Invite, Upgrade, and List/Board/Calendar/Gantt/Table views.

Docker/PostgreSQL was not executed inside the sandbox environment, but the API was tested through FastAPI using SQLite and the Docker compose files remain wired for PostgreSQL and SQLite modes.

## Suggested next release: v1.0.0 production readiness

Recommended next steps:

- Add Playwright end-to-end tests against the Docker stack.
- Add real RBAC enforcement for workspace roles and guest access.
- Replace demo invite/upgrade flows with real email/billing or admin workflows.
- Add database migrations instead of metadata auto-create for production.
- Add structured seed/version migration so old local state and old database rows are upgraded predictably.
- Add CI checks for Python compile, JS syntax, API smoke tests, and frontend smoke tests.
- Split the large frontend script into modules once the functional demo stabilizes.
