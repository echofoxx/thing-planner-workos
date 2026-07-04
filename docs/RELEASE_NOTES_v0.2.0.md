# Release Notes - Thing Planner WorkOS v0.2.0

## Release theme

Production Data Layer Foundation.

## Highlights

- Added FastAPI backend.
- Added PostgreSQL Docker service.
- Added SQLite fallback compose file.
- Added durable workspace state API.
- Added task CRUD endpoints.
- Added comments, intake, report, and AI summary endpoints.
- Added frontend API hydration and sync.
- Added API connection badge in top bar.
- Added Data Layer Status cards under More.
- Preserved the v0.1.0 ClickUp-style UI foundation.

## Known limitations

- State is persisted as JSON in v0.2.0. Normalized relational schema is planned for v0.3.0.
- Authentication is not yet enforced.
- AI endpoint is a deterministic product stub, not connected to a model provider yet.
- Frontend still performs most changes locally and syncs the full state to the API.
- Real-time collaboration is not active yet.

## Upgrade from v0.1.0

Use the v0.2.0 ZIP as a new project folder. v0.1.0 localStorage data does not auto-migrate because the storage key changed from `thing-planner-workos-v010-state` to `thing-planner-workos-v020-state`.
