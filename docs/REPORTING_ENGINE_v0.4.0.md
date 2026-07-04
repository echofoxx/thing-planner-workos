# Reporting Engine v0.4.0

The v0.4 reporting engine turns dashboards into interactive work surfaces instead of passive charts.

## Concepts

- **Dashboard**: A collection of report cards.
- **Report Card**: A KPI, chart, AI summary, or table connected to source work.
- **Report Dataset**: A server-derived rollup of tasks, blockers, billable time, team productivity, status counts, and risks.
- **Drill-down**: A source-record query behind a metric.
- **Report Action**: An operation that updates the source task directly from the dashboard.

## Supported Metrics

- `open_tasks`
- `blocked_tasks`
- `billable_hours`
- `project_health`
- `by_status`
- `by_assignee`
- `by_priority`
- `task_table`

## Supported Actions

- `set_status`
- `assign`
- `set_due`
- `toggle_billable`
- `add_comment`
- `create_followup`

## Future Enhancements

- Saved filters per card.
- Drag-resize dashboard layout persistence.
- Export to PDF/PNG/CSV.
- Scheduled executive reports.
- AI-written weekly status reports.
- Dashboard permissions and sharing.
- Goal/OKR and sprint-specific report cards.
