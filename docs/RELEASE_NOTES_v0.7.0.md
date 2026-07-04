# Release Notes — Thing Planner WorkOS v0.7.0

## Release theme

**Gantt + Dependency / Critical Path Engine**

v0.7.0 turns the Gantt tab from a visual placeholder into an actionable project-planning surface.

## Highlights

- Normalized task dependency model.
- Critical path calculation from dependency chains and explicit critical flags.
- Dependency conflict detection.
- Delay propagation and dependent-task cascade rescheduling.
- Gantt baseline capture.
- AI delay watch panel.
- API-backed Gantt sync with local fallback.
- Automation run history for recalculation and dependency-aware schedule updates.

## New backend endpoints

```text
GET    /api/gantt
GET    /api/gantt/critical-path
POST   /api/gantt/dependencies
DELETE /api/gantt/dependencies/{dependency_id}
POST   /api/gantt/tasks/{task_id}/schedule
POST   /api/gantt/recalculate
POST   /api/gantt/baselines
```

## New tables

```text
task_dependencies
gantt_baselines
gantt_risk_alerts
```

## Validation

- Python backend syntax validated.
- Frontend JavaScript syntax validated.
- SQLite smoke test passed for health, schema, state, Gantt, critical path, baseline creation, recalculation, and task schedule cascade.
