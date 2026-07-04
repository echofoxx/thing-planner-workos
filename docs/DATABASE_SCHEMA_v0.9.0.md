# Database Schema v0.9.0

v0.9.0 adds visual collaboration tables on top of the v0.8 Docs/Knowledge schema.

## New tables

### `whiteboards`

Stores top-level visual workspaces.

Key fields:

- `id`
- `workspace_id`
- `name`
- `icon`
- `owner`
- `favorite`
- `updated`
- `metadata_json`
- `created_at`
- `updated_at`

### `whiteboard_objects`

Stores visual objects such as sticky notes, task cards, doc cards, and future shapes.

Key fields:

- `id`
- `whiteboard_id`
- `workspace_id`
- `object_type`
- `text`
- `color`
- `x`, `y`, `w`, `h`
- `task_id`
- `doc_id`
- `metadata_json`

### `whiteboard_edges`

Stores relationships between visual objects.

Key fields:

- `id`
- `whiteboard_id`
- `workspace_id`
- `from_object_id`
- `to_object_id`
- `label`
- `metadata_json`

### `canvas_cards`

Stores card-based visual planning blocks.

Key fields:

- `id`
- `whiteboard_id`
- `workspace_id`
- `title`
- `kind`
- `metric`
- `x`, `y`
- `linked_type`
- `linked_id`
- `config`

### `mind_map_nodes`

Stores mind map hierarchy nodes.

Key fields:

- `id`
- `whiteboard_id`
- `workspace_id`
- `parent_node_id`
- `label`
- `kind`
- `linked_type`
- `linked_id`
- `sort_order`
- `metadata_json`

## Compatibility

`/api/state` serializes the new normalized visual tables back into the frontend state as:

```json
{
  "selectedWhiteboard": "wb1",
  "visualTab": "whiteboard",
  "whiteboards": []
}
```

This preserves the prototype's fast UI flow while preparing the data model for production persistence.
