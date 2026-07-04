# Release Notes — Thing Planner WorkOS v0.4.0

## Release Theme

Dashboard and reporting engine.

## New Capabilities

- Added normalized `report_cards` table.
- Added dashboard report dataset endpoint.
- Added drill-down endpoint for source task records.
- Added report action endpoint to modify source tasks from dashboard cards.
- Added report cards endpoint for listing and creating cards.
- Added dashboard filters for All Work, Project 1, and Project 2.
- Added local fallback reporting engine in the frontend.
- Added live KPI cards, AI health card, status drill-down, team productivity rollup, billable hours rollup, and risk/blocker queue.
- Added API health reporting for `reporting-v0.4` schema.

## API Added

- `GET /api/reports/dashboard`
- `GET /api/reports/summary`
- `GET /api/reports/drilldown`
- `GET /api/reports/cards`
- `POST /api/reports/cards`
- `POST /api/reports/actions`

## Validated

- Python backend syntax.
- JavaScript syntax.
- FastAPI test client validation for report endpoints.
- SQLite API validation for report cards and report actions.

## Next Release Recommendation

v0.5.0 should focus on normalized forms, submissions, field mapping, conditional logic, and form-triggered automations.
