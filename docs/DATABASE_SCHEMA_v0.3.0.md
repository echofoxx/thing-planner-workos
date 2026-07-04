# Thing Planner WorkOS v0.3.0 Database Schema

v0.3.0 introduces normalized tables while preserving the original frontend state shape through `/api/state`.

## Core tables

| Table | Purpose |
|---|---|
| `users` | Workspace users and demo authentication identities |
| `workspaces` | Top-level tenant/workspace records |
| `workspace_members` | User membership, role, and permission list |
| `spaces` | Major workspace areas, teams, departments, portfolios |
| `folders` | Grouping layer under spaces |
| `lists` | Projects, task lists, docs, and execution containers |
| `task_statuses` | Workspace-level workflow statuses |
| `tasks` | Main work item records |
| `task_comments` | Comments linked to tasks |
| `custom_fields` | Workspace custom field definitions |
| `custom_field_values` | Custom field values by task |
| `notifications` | Inbox/notification records |
| `dashboards` | Dashboard records and card config placeholder |
| `forms` | Form definitions and submission count placeholder |
| `docs` | Docs/wiki/decision records |
| `goals` | Goal/OKR records |
| `automations` | Automation templates and enabled state |
| `activity_logs` | Audit/activity feed |
| `sessions` | Demo auth session records |

## Compatibility strategy

The UI still sends and receives a single state object. The backend now serializes normalized rows into that object and decomposes incoming state syncs back into normalized task/comment/notification rows.

This allows the next releases to move one module at a time from compatibility state sync to dedicated API endpoints.
