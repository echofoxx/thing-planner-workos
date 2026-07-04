# Database Schema Additions — v0.8.0

v0.8.0 adds four normalized tables for the Docs + Knowledge / Wiki Engine.

## doc_pages

Stores nested pages within docs.

Key fields:

- `id`
- `doc_id`
- `workspace_id`
- `parent_page_id`
- `title`
- `page_type`
- `content`
- `sort_order`
- `protected`
- `verified`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

## doc_versions

Stores version snapshots for docs/pages.

Key fields:

- `id`
- `doc_id`
- `page_id`
- `workspace_id`
- `version_number`
- `title`
- `content`
- `created_by`
- `created_at`

## doc_task_links

Stores traceability links between docs/pages and tasks.

Key fields:

- `id`
- `doc_id`
- `page_id`
- `task_id`
- `workspace_id`
- `relation`
- `created_at`

Unique constraint:

- `doc_id`, `task_id`, `relation`

## doc_decisions

Stores structured decision records.

Key fields:

- `id`
- `doc_id`
- `workspace_id`
- `title`
- `decision`
- `rationale`
- `owner`
- `status`
- `created_at`
