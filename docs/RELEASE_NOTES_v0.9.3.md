# Thing Planner WorkOS v0.9.3 Functional Hardening

## Purpose

v0.9.3 turns the v0.9.2 partially connected shell into a more functional local/API-backed demo.

## Fixes

- Updated stale v0.9.1 labels, title, storage keys, and API fallback text to v0.9.3.
- Removed remaining feedback/promo popups from default and API-hydrated state.
- Replaced placeholder actions with functional local/API-synced actions for spaces, projects, report cards, form fields, AI form improvements, automation templates, weekly planning, team standups, AI agent creation, goals, clips, invites, upgrades, and automation creation.
- Removed duplicate older frontend function definitions and reworked the Spaces tree to render dynamic spaces/folders/lists instead of hard-coded Project 1 / Project 2 only.
- Added dynamic project-name lookup and first-project fallback.
- Improved Canvas/Mind Map link routing for project lists and views.
- Hardened backend `/api/state` sync so frontend-created members, spaces, lists, dashboards, goals, forms, submissions, automations, automation runs, tasks, comments, notifications, and whiteboards can persist without foreign-key errors.
- Added safeguards so frontend-created project/list IDs are created in the normalized database before tasks reference them.

## Validation

- Python compile check passed.
- Node syntax check passed.
- FastAPI smoke tests passed for health, state, auth, tasks, forms, planner, reports, Gantt, docs, knowledge, whiteboards, and AI summary endpoints.
- Frontend render/action smoke test passed across Home, Spaces, Forms, Planner, AI, Teams, Docs, Dashboard, Whiteboard, More/Automations, Goals, Clips, Invite, Upgrade, and List/Board/Calendar/Gantt/Table views.

## Known validation gap

Full Docker Compose PostgreSQL runtime was not executed in the sandbox. The API was validated with FastAPI TestClient and SQLite, and the compose files remain wired for PostgreSQL and SQLite runtime modes.
