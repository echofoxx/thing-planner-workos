# Database Schema v0.6.0 Additions

v0.6.0 adds planner and scheduling persistence to the normalized backend.

## calendar_events

Stores meetings, focus events, synced calendar events, and task-linked calendar items.

Important columns:

- `id`
- `workspace_id`
- `title`
- `kind`
- `start_at`
- `end_at`
- `source`
- `task_id`
- `owner_id`
- `color`
- `metadata_json`

## planner_blocks

Stores generated or manual time blocks.

Important columns:

- `id`
- `workspace_id`
- `task_id`
- `title`
- `owner_id`
- `start_at`
- `end_at`
- `block_type`
- `status`
- `score`
- `reason`

## planner_preferences

Stores workspace scheduling preferences.

Important columns:

- `workspace_id`
- `workday_start`
- `workday_end`
- `lunch_start`
- `lunch_end`
- `focus_block_minutes`
- `auto_schedule_blocked`
