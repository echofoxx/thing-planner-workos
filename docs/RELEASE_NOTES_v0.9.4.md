# Thing Planner WorkOS v0.9.4 Release Notes

## BLUF

v0.9.4 is a functional verification release. A four-layer automated audit (backend API, state persistence, frontend render/handler sweep, full-stack integration) found the application substantially functional, with one confirmed defect: the three Upgrade plan cards crashed on click due to broken HTML attribute quoting. The defect is fixed and every layer now passes clean.

## Defect fixed

**Upgrade module plan cards non-functional (SyntaxError on click).**

- Location: `assets/app.js`, `renderUpgradeMain()`.
- Cause: the `templateCard()` helper interpolates its action argument into `onclick="${action}"`. The three plan card actions were written as `upgradePlanDemo("AI Plus")` etc. — the embedded double quotes terminated the HTML attribute early, so the browser received `onclick="upgradePlanDemo("` and threw `Unexpected token '}'` on every click of AI Plus, Automation Pro, and Enterprise.
- Fix: quote nesting inverted to `upgradePlanDemo('AI Plus')` so the attribute stays intact. Verified by real click dispatch in a headless DOM: all three cards now execute the upgrade flow and mutate subscription state.
- Note: the sidebar Upgrade button (`onclick="upgradePlanDemo('Enterprise')"`) was already correct; only the three template cards were affected.

## Version hygiene

- `STORAGE_KEY` / `AUTH_TOKEN_KEY` rolled to `thing-planner-workos-v094-*`; legacy migration now covers v0.9.1, v0.9.2, and v0.9.3 keys so existing local state and tokens carry forward.
- Page title, `APP_VERSION`, seed/state version fields, API status text, and visual collaboration labels rolled to v0.9.4.

## Verification detail

### Layer 1 — Backend API smoke (47 checks)

Fresh SQLite database, demo auth. All endpoint groups pass: health, login/me, schema, workspace, members, permissions, activity, state GET/PUT, tasks CRUD + comments, custom fields, forms/schema/submissions/analytics, project intake, automations create/toggle/run, planner (plan-my-day, events, task schedule, focus blocks), reports (summary, dashboard, drilldown, cards, actions), Gantt (dataset, critical path, dependencies add/remove, schedule, recalculate, baselines), docs CRUD + links + decisions + AI summary, knowledge, whiteboards. Zero 500s in server logs.

### Layer 2 — State persistence round-trip

Simulated a frontend session mutating state exactly as the UI does, then `PUT /api/state` and re-read. Persisted correctly into normalized tables: new task with comment, new space → folder → list tree, a task referencing the brand-new list (list-creation safeguard confirmed working), new member, goal, form submission, automation, notification, and whiteboard. No foreign-key or integrity errors.

### Layer 3 — Headless frontend sweep

App executed in a real DOM (jsdom) in local/offline mode:

- All 15 modules render (home, spaces, planner, ai, teams, docs, dashboards, whiteboard, forms, automations, goals, clips, invite, upgrade, more).
- All 5 Spaces views render (list, board, calendar, gantt, table).
- 559 real click/change event dispatches across every `[onclick]`/`[onchange]` element in every module: zero handler crashes after the fix (before the fix: the 3 Upgrade cards crashed).
- Static analysis: all 95 handler-referenced functions resolve to defined functions; no duplicate top-level function definitions; no toast-only placeholder functions remain.
- Workflow assertions all pass: addTaskFromInput, updateTask status, openTask drawer, addComment, planMyDay, addFocusBlock, runAI response render, submitFormDemo, useAutomationTemplate, createGoalDemo, createDocFromTemplate, whiteboard tab switching, localStorage persistence.

### Layer 4 — Full-stack integration

Frontend loaded headlessly against the live FastAPI backend:

- API bootstrap, health detection, and state hydration (8 seeded tasks) confirmed.
- Demo auth token acquired and used on authorized calls.
- UI-created task persisted to the backend through the debounced `/api/state` sync.
- Doc creation, planner plan-my-day, and form submission all round-tripped through the API and persisted.
- Zero server errors across the session.

## Known non-blocking observations

- `data/seed.json` is not referenced by the frontend (dead asset; `backend/app/seed_state.json` is the live seed). Harmless — retained for reference.
- `runAI()` renders responses into the AI panel but does not append to `state.aiMessages`; response history is session-scoped. Cosmetic, not a functional break.
- Docker Compose PostgreSQL runtime and browser-based E2E were not executable in the audit sandbox; however, the schema uses only Postgres-compatible constructs (standard SQLAlchemy types, `SELECT 1` health probe) and the SQLite path is fully exercised.

## Deployment

Unchanged from v0.9.3:

```powershell
cd C:/docker/thing-planner-workos-v0.9.4-functional
docker compose up --build -d          # PostgreSQL
docker compose -f docker-compose.sqlite.yml up --build -d   # SQLite fallback
```

Web `http://localhost:8098` • API `http://localhost:8099/api/health` • Docs `http://localhost:8099/docs`
