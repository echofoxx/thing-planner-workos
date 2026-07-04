# Database Schema Additions v0.5.0

v0.5.0 extends the normalized schema added in v0.3.0 and v0.4.0.

## New tables

### `form_submissions`

Stores form responses and their generated work products.

| Column | Type | Purpose |
|---|---|---|
| `id` | string | Submission ID. |
| `form_id` | string | Linked form. |
| `workspace_id` | string | Workspace scope. |
| `requester` | string | Requesting person. |
| `department` | string | Department / routing field. |
| `priority` | string | Requested or derived priority. |
| `payload` | JSON | Raw normalized form response. |
| `ai_analysis` | JSON | AI classification and routing output. |
| `created_task_id` | string | Task created from the submission. |
| `status` | string | Processing status. |
| `created_at` | datetime | Creation timestamp. |

### `automation_runs`

Stores automation execution history.

| Column | Type | Purpose |
|---|---|---|
| `id` | string | Run ID. |
| `automation_id` | string | Automation rule/template that ran. |
| `workspace_id` | string | Workspace scope. |
| `trigger` | string | Trigger that started the run. |
| `source_type` | string | Source object type. |
| `source_id` | string | Source object ID. |
| `status` | string | Run status. |
| `summary` | string | Human-readable result. |
| `details` | JSON | Run metadata. |
| `created_at` | datetime | Run timestamp. |

## Updated compatibility state

`/api/state` now serializes:

- `formSubmissions`
- `automationRuns`
- form `schema`

This preserves the frontend compatibility layer while the backend moves toward normalized APIs.
