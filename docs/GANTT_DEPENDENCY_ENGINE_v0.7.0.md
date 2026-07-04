# Gantt Dependency Engine — v0.7.0

## Purpose

The v0.7 Gantt engine gives Thing Planner WorkOS a real project planning layer. It supports dependencies, critical path, baseline snapshots, and schedule-risk analysis.

## Core concepts

### Task dependency

A dependency links a predecessor task to a successor task.

Current dependency type support:

```text
FS = finish-to-start
```

Each dependency can include lag days and a critical flag.

### Critical path

The engine computes the longest dependency chain by task duration. Explicitly critical tasks are also included in the returned critical-path set.

### Delay propagation

When a task is rescheduled from the Gantt view, the backend can cascade successor start/due dates so dependent work no longer starts before predecessor work finishes.

### Risk alerts

The engine flags:

- dependency conflicts
- blocked critical-path tasks
- overdue open tasks
- low progress near due date on critical work

When `/api/gantt` or `/api/gantt/recalculate` runs with alert persistence, the current alert set is stored in `gantt_risk_alerts`.

## Frontend behavior

The Gantt tab now includes:

- KPI cards
- date-scaled Gantt bars
- critical-path styling
- blocked-task styling
- inline date/duration controls
- dependency editor
- AI delay watch
- baseline capture
- API-backed refresh with local fallback
