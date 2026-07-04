# Docs + Knowledge / Wiki Engine v0.8.0

## Purpose

The v0.8.0 knowledge engine turns project documentation into a connected execution layer. Docs are no longer isolated notes. They can be linked to tasks, decisions, versions, AI summaries, and knowledge search.

## Core objects

- **Doc**: top-level document such as project charter, SOP wiki, decision log, or notes.
- **Doc Page**: nested page content within a doc.
- **Doc Version**: snapshot of doc/page content after updates.
- **Doc Task Link**: traceability link from doc/page to source task.
- **Doc Decision**: structured decision record with decision, rationale, owner, and status.

## User workflows

### Create project knowledge

1. Open Docs.
2. Click New Doc.
3. Add context, decisions, and action items.
4. Save the doc.
5. Link the doc to the top active task.

### Capture decisions

1. Open a project doc or decision log.
2. Click `+ Decision`.
3. The system records the decision and creates an automation run entry.

### Generate AI doc summary

1. Open a doc.
2. Click AI Summary.
3. The system summarizes content, linked task count, decisions, risk, action items, and sources.

## API behavior

The Docs API supports full create/read/update workflows plus traceability actions. The Knowledge API provides search and hub-level summary records.

## Next improvements

- Rich block editor with slash commands.
- Nested page tree editing.
- File attachments and image embeds.
- True vector search over docs/tasks/comments.
- Protected/verified page permissions enforcement.
- AI citations into task/doc/comment source records.
