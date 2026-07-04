# Release Notes — Thing Planner WorkOS v0.8.0

## Theme

Docs + Knowledge / Wiki Engine.

## Highlights

- Added normalized doc pages, versions, task links, and decisions.
- Added Docs API and Knowledge Search API.
- Upgraded the Docs UI into a three-panel workbench: doc list, editor, and insights.
- Added AI document summary stub with source-aware linked tasks and decision counts.
- Added structured decisions with automation run history.
- Added local fallback behavior so Docs continue to work without the API.

## New API endpoints

- `GET /api/docs`
- `GET /api/docs/{doc_id}`
- `POST /api/docs`
- `PATCH /api/docs/{doc_id}`
- `POST /api/docs/{doc_id}/links`
- `POST /api/docs/{doc_id}/decisions`
- `POST /api/docs/{doc_id}/ai-summary`
- `GET /api/knowledge/search?q=...`
- `GET /api/knowledge/hub`

## Validation

Validated with:

- Python syntax check
- JavaScript syntax check
- FastAPI SQLite smoke test for health, schema, state, docs, doc detail, knowledge search, knowledge hub, AI doc summary, doc create, doc patch, doc-task link, and decision capture.
