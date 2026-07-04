# Database Schema v0.4.0

v0.4.0 preserves the v0.3 normalized schema and adds `report_cards`.

## New Table

```text
report_cards
- id
- dashboard_id
- workspace_id
- title
- card_type
- metric
- filters
- layout
- config
- created_at
- updated_at
```

## Existing Core Tables

```text
users
workspaces
workspace_members
spaces
folders
lists
task_statuses
tasks
task_comments
custom_fields
custom_field_values
notifications
dashboards
forms
docs
goals
automations
activity_logs
sessions
```

## Compatibility

The `/api/state` endpoint remains compatible with the v0.1-v0.4 frontend state shape while the reporting API exposes derived server-side rollups.
