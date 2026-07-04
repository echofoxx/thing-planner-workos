# v0.3.0 Data Layer Design
> v0.3.0 update: the backend now uses normalized relational tables with demo authentication and /api/state compatibility serialization. See `DATABASE_SCHEMA_v0.3.0.md` and `AUTH_v0.3.0.md`.


## Purpose

v0.3.0 adds the first backend service for Thing Planner WorkOS. The intent is to move from a static LocalStorage prototype to a full-stack application while avoiding a heavy data migration too early.

## Current approach

The backend stores the complete workspace state as JSON in a `state_snapshots` table.

```text
state_snapshots
  id          string primary key
  data        json/jsonb
  updated_at  timestamp
```

This allows the existing frontend to stay mostly intact while adding durable persistence, API docs, and a clean path to normalize the schema later.

## Why this is useful now

- Fast to implement.
- Low migration risk.
- Preserves the prototype UX.
- Lets the frontend hydrate from the API.
- Allows task-level endpoints to be introduced incrementally.
- Supports PostgreSQL now and SQLite fallback for local testing.

## v0.3 normalization target

```text
workspaces
users
workspace_members
spaces
folders
lists
tasks
task_assignees
task_comments
task_activity
custom_fields
custom_field_values
dashboards
dashboard_cards
forms
form_fields
form_submissions
automations
automation_runs
docs
doc_pages
ai_agents
ai_agent_runs
audit_logs
```

## API-first direction

The frontend should gradually stop writing full-state snapshots and instead use dedicated endpoints:

- `POST /api/tasks`
- `PATCH /api/tasks/{task_id}`
- `POST /api/tasks/{task_id}/comments`
- `POST /api/forms/project-intake`
- `GET /api/reports/summary`
- future `/api/dashboards`, `/api/forms`, `/api/docs`, `/api/automations`, `/api/agents`
