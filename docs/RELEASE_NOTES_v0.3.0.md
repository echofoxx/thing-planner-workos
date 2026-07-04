# Thing Planner WorkOS v0.3.0 Release Notes

## Release theme

v0.3.0 turns the v0.2 snapshot persistence layer into a normalized production-style data foundation with demo authentication, workspace membership, custom fields, activity logs, and compatibility APIs for the existing ClickUp-inspired UI shell.

## Added

- Normalized SQLAlchemy schema for users, workspaces, members, spaces, folders, lists, task statuses, tasks, comments, custom fields, notifications, dashboards, forms, docs, goals, automations, activity logs, and sessions.
- Demo authentication endpoints:
  - `POST /api/auth/login`
  - `POST /api/auth/demo-login`
  - `GET /api/auth/me`
- Demo user seeded as `echofoxx@gmail.com` with password `thingplanner`.
- Lightweight signed bearer token implementation using HMAC SHA-256.
- Workspace/member endpoints:
  - `GET /api/workspaces/current`
  - `GET /api/members`
  - `GET /api/permissions`
- Schema and audit endpoints:
  - `GET /api/schema`
  - `GET /api/activity`
- Custom field endpoint:
  - `GET /api/custom-fields`
- `/api/state` compatibility serializer that now reads/writes normalized tables instead of a single JSON snapshot.
- Activity logging for seed, login, task creation, task updates, task deletion, comments, and state sync.
- Frontend v0.3 API/auth badges in the top bar.
- Data/Auth status cards under the More module.
- README update with v0.3 install, API, auth, and GitHub commands.

## Changed

- Backend version changed from `v0.2.0` to `v0.3.0`.
- Persistent data model moved from `state_snapshots` to normalized relational tables.
- Frontend local storage key changed to `thing-planner-workos-v030-state` to avoid stale v0.2 cache collisions.
- Health endpoint now reports schema, auth mode, and table counts.

## Compatibility

The existing SPA still works through `/api/state`. This keeps the UI stable while allowing the backend to evolve into production-grade CRUD endpoints.

## Next release target

v0.4.0 should focus on the dashboard/reporting engine: normalized dashboard cards, saved filters, server-side report endpoints, drill-down records, and editable dashboard actions.
