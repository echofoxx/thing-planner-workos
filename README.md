# Thing Planner WorkOS v0.9.4 Functional Release

Thing Planner WorkOS is a local-first, API-backed project/work operating system prototype with a ClickUp-style workspace shell, Spaces, tasks, boards, dashboards, reports, forms, automations, planner, Gantt scheduling, docs, knowledge, teams, goals, clips, whiteboards, canvas planning, and mind maps.

This v0.9.4 package is a functional verification release over v0.9.3. Every backend endpoint, every frontend module render, all 550+ inline UI handlers, and the full frontend-to-backend state sync path were exercised in automated tests, and one confirmed defect was fixed.

## What was verified and fixed in v0.9.4

**Fixed:**

- Upgrade module: the three plan cards (AI Plus, Automation Pro, Enterprise) threw a JavaScript SyntaxError on click. Their onclick actions embedded double quotes inside a double-quoted HTML attribute, truncating the handler to `upgradePlanDemo(`. Quote nesting corrected; all three cards now invoke the upgrade flow.
- Rolled version labels, page title, storage/auth token keys (with legacy v0.9.1–v0.9.3 migration), and API status text to v0.9.4.

**Verified functional by automated test:**

- Backend: 47-check API smoke suite across auth, tasks, comments, forms, submissions, analytics, automations, planner, reports, Gantt, docs, and state — all endpoint groups pass against a fresh SQLite database.
- State persistence: frontend-shaped `/api/state` PUT round-trip persists new tasks (including tasks referencing brand-new frontend-created lists), spaces/folders/lists, members, goals, form submissions, automations, notifications, comments, and whiteboards into normalized tables with zero integrity errors.
- Frontend: all 15 modules and all 5 Spaces views render headlessly; 559 real click/change event dispatches across every module produce zero handler crashes (after the Upgrade fix).
- Workflows: add task, status update, task drawer, comments, planner plan-my-day, focus blocks, AI response, form intake submission, automation creation from template, goal creation, doc creation from template, whiteboard tabs, and localStorage persistence all mutate state correctly in local mode.
- Full stack: live browser-equivalent session against the running API confirmed bootstrap/hydration, demo auth, debounced UI-to-backend state sync, doc creation through the API, planner scheduling through the API, and form submission persistence — with zero server errors.


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
cd C:/docker/thing-planner-workos-v0.9.4-functional
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
cd C:/docker/thing-planner-workos-v0.9.4-functional
docker compose -f docker-compose.sqlite.yml up --build -d
```

Open `http://localhost:8098`.

## Demo auth

The app attempts demo auth automatically when the API is reachable. The demo account is:

- Email: `echofoxx@gmail.com`
- Password: local demo password managed by the seeded API

The UI uses a bearer token stored under the v0.9.4 token key and migrates older v0.9.1/v0.9.2/v0.9.3 local storage where available.

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
