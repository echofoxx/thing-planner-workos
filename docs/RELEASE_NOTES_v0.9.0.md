# Release Notes — Thing Planner WorkOS v0.9.0

## Release theme

**Whiteboards + Canvas / Mind Map Engine**

v0.9.0 adds the first operational visual collaboration layer to Thing Planner WorkOS.

## Added

- Whiteboards module with board selection and visual KPIs.
- Sticky notes, task cards, doc cards, object-to-object relationship edges.
- Canvas planning mode with live cards linked to projects, dashboards, forms, docs, and Gantt.
- Mind map mode for project/module hierarchy and feature decomposition.
- Convert selected sticky note to a task.
- Link selected visual object to an existing task.
- AI visual summary for board-level action items and risks.
- Local fallback behavior when the API is offline.
- Normalized FastAPI/SQLAlchemy tables for visual collaboration.
- New `/api/whiteboards` endpoint family.
- `/api/state` serialization of whiteboards, objects, canvas cards, and mind-map nodes.
- `/api/health` visual collaboration table counts.

## Validation completed

- Backend Python syntax check.
- Frontend JavaScript syntax check.
- FastAPI SQLite smoke test for:
  - health
  - schema
  - state
  - whiteboards list
  - whiteboard detail
  - whiteboard AI summary
  - adding a whiteboard object
  - existing Docs/Knowledge hub endpoint

## Known limitations

- Visual objects are click/select based; full drag-and-drop canvas editing is not yet implemented.
- Canvas cards are operational prototypes, not live chart widgets yet.
- AI summaries are deterministic stubs, ready to be wired to a model provider.
- No real-time multi-user cursors yet.

## Recommended next release

**v1.0.0 Production Demo Hardening** with onboarding, release-quality docs, screenshots, migration-safe database startup, test scripts, and final UI polish.
