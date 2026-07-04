# Planner + AI Scheduling Engine v0.6.0

The v0.6.0 Planner turns tasks, calendar events, working hours, focus preferences, and task metadata into a daily execution plan.

## Scheduling inputs

- task priority
- due date
- critical-path flag
- blocked status
- progress
- time estimate
- assignee
- calendar events
- focus blocks
- workday preferences
- lunch window

## Scheduling outputs

- AI-generated planner blocks
- protected focus blocks
- meeting timeline
- delay/risk warnings
- daily planner metrics

## Current scheduling rules

- Urgent and High priority tasks rank above Normal and Low.
- Overdue and near-due work receives a score boost.
- Critical-path tasks receive a score boost.
- Blocked tasks are excluded by default.
- Work is placed only inside working hours.
- Lunch, meetings, and existing protected blocks reduce available slots.

## Local fallback

If the API is offline, the frontend generates a local demo schedule and persists it to LocalStorage.
