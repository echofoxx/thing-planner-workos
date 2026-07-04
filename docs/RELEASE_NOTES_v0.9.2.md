# Thing Planner WorkOS v0.9.2 Release Notes

## Theme

API startup hotfix for v0.9.1.

## Fixed

- Fixed PostgreSQL `ForeignKeyViolation` during API startup when `ensure_default_whiteboard_data()` recorded `auto_visual_seed` in `automation_runs` before the corresponding automation existed in `automations`.
- Hardened `record_automation_run()` so future system automation IDs are automatically registered before inserting run history.
- Preserves the cleaned v0.9.1 UI: nine primary rail modules, compact connection/auth pills, no distracting promo/helper popups.

## Validation

- Python syntax check passed.
- FastAPI import smoke test is expected to pass in Docker with PostgreSQL because the missing automation record is now created before the run history insert.
