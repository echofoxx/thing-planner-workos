# Database Schema Additions — v0.7.0

v0.7.0 adds three normalized tables to support Gantt planning.

## `task_dependencies`

Stores task-to-task dependency links.

Key fields:

- `id`
- `workspace_id`
- `predecessor_task_id`
- `successor_task_id`
- `dependency_type`
- `lag_days`
- `critical`
- `created_at`
- `updated_at`

## `gantt_baselines`

Stores snapshots of project schedule plans.

Key fields:

- `id`
- `workspace_id`
- `list_id`
- `name`
- `task_snapshots`
- `created_at`

## `gantt_risk_alerts`

Stores current schedule risk findings.

Key fields:

- `id`
- `workspace_id`
- `list_id`
- `task_id`
- `level`
- `title`
- `recommendation`
- `metadata_json`
- `created_at`

## Compatibility

The `/api/state` compatibility layer now serializes:

- `taskDependencies`
- `ganttBaselines`
- `ganttRiskAlerts`
