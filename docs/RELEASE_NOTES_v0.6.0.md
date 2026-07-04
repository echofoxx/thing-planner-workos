# Release Notes — Thing Planner WorkOS v0.6.0

## Release theme

Planner + AI Scheduling Engine.

## Highlights

- Added database-backed calendar events, planner blocks, and planner preferences.
- Added AI schedule generation through `/api/planner/plan-my-day`.
- Added task scheduling endpoint and focus block endpoint.
- Added Planner UI timeline, priority queue, risk watch, week strip, and scheduling actions.
- Added API/local fallback behavior for planning workflows.
- Added planner state serialization through `/api/state`.

## New backend tables

- `calendar_events`
- `planner_blocks`
- `planner_preferences`

## New API endpoints

```text
GET    /api/planner
POST   /api/planner/plan-my-day
GET    /api/planner/events
POST   /api/planner/events
POST   /api/planner/tasks/{task_id}/schedule
POST   /api/planner/focus-blocks
DELETE /api/planner/blocks/{block_id}
```

## Validation

- Python syntax check passed.
- Frontend JavaScript syntax check passed.
- SQLite smoke test passed for planner health/schema/schedule/focus flows.
