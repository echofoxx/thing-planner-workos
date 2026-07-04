# Thing Planner WorkOS v0.5.0 Release Notes

## Release theme

**Forms + Intake Automation Engine**

v0.5.0 turns Forms from a prototype page into a connected intake workflow. Form responses can now create mapped tasks, run AI intake analysis, trigger automation chains, write automation run history, notify owners, and feed dashboard/reporting data.

## Added

- Normalized `form_submissions` table.
- Normalized `automation_runs` table.
- Form schema storage with field mappings and automation chains.
- AI intake analysis helper for classification, duplicate risk, delivery risk, and recommended owner.
- Connected Project Intake submission endpoint.
- Form analytics endpoint by department, priority, and duplicate watch.
- Automation templates endpoint.
- Automation list/run/toggle endpoints.
- Form submission processing pipeline:
  1. Capture response.
  2. Analyze with AI stub.
  3. Create mapped task.
  4. Add AI intake comment.
  5. Notify recommended owner.
  6. Record automation run history.
- Frontend Forms Command Center.
- Form builder with field-to-task mapping view.
- Intake automation chain panel.
- Latest submissions table.
- More / Automations page with automation run history.
- API health counts for forms, submissions, and automation runs.

## New API endpoints

- `GET /api/forms`
- `GET /api/forms/{form_id}`
- `PUT /api/forms/{form_id}/schema`
- `POST /api/forms/{form_id}/submissions`
- `GET /api/forms/{form_id}/submissions`
- `GET /api/forms/{form_id}/analytics`
- `POST /api/forms/project-intake`
- `GET /api/automations`
- `POST /api/automations`
- `PATCH /api/automations/{automation_id}/toggle`
- `POST /api/automations/run`
- `GET /api/automations/templates`

## Validation performed

- Backend Python syntax validation.
- Frontend JavaScript syntax validation using `node --check`.
- FastAPI endpoint smoke test with SQLite:
  - health
  - state
  - forms
  - form detail
  - submissions
  - analytics
  - automations
  - templates
  - reports dashboard
  - demo login
  - form submission
  - manual automation run

## Next recommended release

**v0.6.0 Planner + AI Scheduling Engine**

Recommended scope:

- Planner database tables.
- Calendar event model.
- Task time-blocking.
- Working hours and capacity preferences.
- AI daily plan endpoint.
- Schedule conflict detection.
- Auto-reschedule suggestions.
- Calendar page upgrades.
