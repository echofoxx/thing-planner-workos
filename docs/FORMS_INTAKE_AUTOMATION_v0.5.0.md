# Forms + Intake Automation Engine v0.5.0

## Purpose

The v0.5.0 Forms engine makes intake operational. A form submission is no longer just a record; it becomes an actionable workflow that can create tasks, run AI analysis, notify owners, update dashboards, and maintain automation history.

## Form processing lifecycle

```text
Form submitted
  -> Validate / normalize fields
  -> AI intake analysis
  -> Create mapped task
  -> Add AI comment
  -> Notify recommended owner
  -> Record automation runs
  -> Refresh reports / analytics
```

## Core entities

| Entity | Purpose |
|---|---|
| `forms` | Stores form name, description, favorite flag, submission count, and schema. |
| `form_submissions` | Stores each response, AI analysis, status, and created task reference. |
| `automations` | Stores enabled workflow rules and templates. |
| `automation_runs` | Stores historical execution records for traceability. |
| `tasks` | Receives work created from mapped form submissions. |
| `notifications` | Receives intake routing notifications. |
| `activity_logs` | Stores audit trail for form and automation activity. |

## Project Intake schema

The seeded `form1` schema includes:

- Project name
- Requester
- Department
- Priority
- Business objective
- Desired due date

Field mappings:

| Form field | Target |
|---|---|
| `project_name` | `task.name` |
| `priority` | `task.priority` |
| `department` | `task.tags` and routing logic |
| `business_objective` | `task.description` |
| `desired_due_date` | `task.due` |

## AI intake analysis

The current AI function is a deterministic local stub designed for demo and development. It returns:

- classification
- delivery risk
- duplicate risk
- recommended owner
- summary
- recommended next steps
- whether a business objective was detected

Future versions should replace the stub with a provider abstraction that can call local Ollama or an OpenAI-compatible endpoint.

## Automation chain

The default Project Intake chain is:

1. `auto_intake_classify`
2. `auto_intake_task`
3. `auto_intake_notify`
4. `auto_intake_dashboard`

Each enabled automation writes an `automation_runs` record.

## Frontend behavior

The Forms module now includes:

- Forms command center KPI cards.
- Template grid.
- Latest submissions table.
- Form builder with field mappings.
- Automation chain panel.
- API-backed submission with local fallback.

The More / Automations module now includes:

- automation cards
- enable/pause toggles
- manual test run
- run history table
