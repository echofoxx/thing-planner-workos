# Visual Collaboration Engine v0.9.0

The Visual Collaboration Engine turns Whiteboards into a connected execution surface.

## Core concepts

| Concept | Purpose |
|---|---|
| Whiteboard | Top-level visual workspace for brainstorming and planning |
| Whiteboard Object | Sticky note, task card, doc card, decision card, or future shape |
| Edge | Relationship between two visual objects |
| Canvas Card | Live planning block linked to work objects such as dashboards, forms, docs, or Gantt |
| Mind Map Node | Hierarchical concept node linked to modules, views, or actions |

## User workflows

### 1. Brainstorm to execution

1. Add sticky notes to the board.
2. Select a sticky note.
3. Convert it to a task.
4. Open the task drawer and assign owner, due date, priority, comments, and status.

### 2. Map work relationships

1. Use objects and relationship edges to show how ideas connect.
2. Link visual objects to tasks or docs.
3. Use AI summary to identify missing owners, stale ideas, and blockers.

### 3. Canvas command center

1. Open Canvas mode.
2. Add live cards.
3. Link cards to dashboard, form, docs, project, or Gantt.
4. Use cards as an executive planning board.

### 4. Mind map planning

1. Open Mind Map mode.
2. Review the hierarchy from WorkOS root to modules and feature nodes.
3. Click linked nodes to jump to modules or views.

## API endpoints

- `GET /api/whiteboards`
- `GET /api/whiteboards/{whiteboard_id}`
- `POST /api/whiteboards`
- `POST /api/whiteboards/{whiteboard_id}/objects`
- `POST /api/whiteboards/{whiteboard_id}/canvas-cards`
- `POST /api/whiteboards/{whiteboard_id}/mind-map-nodes`
- `POST /api/whiteboards/{whiteboard_id}/ai-summary`

## Next improvements

- Drag/drop object movement with persisted coordinates.
- Object resizing.
- Shape and connector creation UI.
- Real-time cursors and multiplayer editing.
- AI-generated whiteboard from a prompt.
- AI-generated task dependency graph.
- Export board to PNG/PDF.
