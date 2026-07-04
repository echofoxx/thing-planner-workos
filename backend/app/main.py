from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, JSON, MetaData, String, Table, create_engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

APP_VERSION = "v0.2.0"
DEFAULT_STATE_ID = "default"
SEED_PATH = Path(__file__).with_name("seed_state.json")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/workos.db")

metadata = MetaData()
state_snapshots = Table(
    "state_snapshots",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("data", JSON, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)

class StatePayload(BaseModel):
    state: Dict[str, Any] = Field(default_factory=dict)

class TaskPayload(BaseModel):
    projectId: str = "p1"
    name: str
    assignee: str = "adrian"
    due: str = "2026-07-12"
    priority: str = "Normal"
    status: str = "TO DO"
    description: str = ""
    estimate: float = 1
    tracked: float = 0
    billable: bool = False
    tags: List[str] = Field(default_factory=lambda: ["New"])

class TaskPatch(BaseModel):
    fields: Dict[str, Any] = Field(default_factory=dict)

class CommentPayload(BaseModel):
    by: str = "Adrian Francis"
    text: str

class IntakePayload(BaseModel):
    project_name: str
    requester: str = "Adrian Francis"
    department: str = "Product"
    priority: str = "Normal"
    description: str = ""

app = FastAPI(
    title="Thing Planner WorkOS API",
    version=APP_VERSION,
    description="v0.2 production data layer foundation for Thing Planner WorkOS.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup() -> None:
    metadata.create_all(engine)
    ensure_seed_state()


def load_seed_state() -> Dict[str, Any]:
    with SEED_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = "0.2.0"
    return data


def ensure_seed_state() -> None:
    with engine.begin() as conn:
        existing = conn.execute(select(state_snapshots.c.id).where(state_snapshots.c.id == DEFAULT_STATE_ID)).first()
        if existing is None:
            conn.execute(state_snapshots.insert().values(id=DEFAULT_STATE_ID, data=load_seed_state(), updated_at=utc_now()))


def get_state() -> Dict[str, Any]:
    ensure_seed_state()
    with engine.begin() as conn:
        row = conn.execute(select(state_snapshots.c.data).where(state_snapshots.c.id == DEFAULT_STATE_ID)).first()
        if not row:
            raise HTTPException(status_code=404, detail="Workspace state not found")
        return dict(row[0])


def put_state(state: Dict[str, Any]) -> Dict[str, Any]:
    state = dict(state or {})
    state["version"] = "0.2.0"
    now = utc_now()
    with engine.begin() as conn:
        if engine.dialect.name == "postgresql":
            stmt = pg_insert(state_snapshots).values(id=DEFAULT_STATE_ID, data=state, updated_at=now)
            stmt = stmt.on_conflict_do_update(
                index_elements=[state_snapshots.c.id],
                set_={"data": state, "updated_at": now},
            )
            conn.execute(stmt)
        else:
            existing = conn.execute(select(state_snapshots.c.id).where(state_snapshots.c.id == DEFAULT_STATE_ID)).first()
            if existing:
                conn.execute(
                    state_snapshots.update().where(state_snapshots.c.id == DEFAULT_STATE_ID).values(data=state, updated_at=now)
                )
            else:
                conn.execute(state_snapshots.insert().values(id=DEFAULT_STATE_ID, data=state, updated_at=now))
    return state


def task_index(state: Dict[str, Any], task_id: str) -> int:
    tasks = state.setdefault("tasks", [])
    for idx, task in enumerate(tasks):
        if task.get("id") == task_id:
            return idx
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


def make_id(prefix: str = "t") -> str:
    return f"{prefix}{int(datetime.now().timestamp() * 1000)}"

@app.get("/api/health")
def health() -> Dict[str, Any]:
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except SQLAlchemyError:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "version": APP_VERSION,
        "database": engine.dialect.name,
        "state_id": DEFAULT_STATE_ID,
        "timestamp": utc_now().isoformat(),
    }

@app.get("/api/state")
def api_get_state() -> Dict[str, Any]:
    return {"state": get_state()}

@app.put("/api/state")
def api_put_state(payload: StatePayload) -> Dict[str, Any]:
    state = put_state(payload.state)
    return {"ok": True, "state": state, "updated_at": utc_now().isoformat()}

@app.post("/api/reset")
def api_reset() -> Dict[str, Any]:
    state = put_state(load_seed_state())
    return {"ok": True, "state": state}

@app.get("/api/tasks")
def api_tasks(projectId: Optional[str] = None) -> Dict[str, Any]:
    state = get_state()
    tasks = state.get("tasks", [])
    if projectId:
        tasks = [t for t in tasks if t.get("projectId") == projectId]
    return {"tasks": tasks}

@app.post("/api/tasks")
def api_create_task(payload: TaskPayload) -> Dict[str, Any]:
    state = get_state()
    task = payload.model_dump()
    task.update({
        "id": make_id("t"),
        "comments": [],
        "progress": 0,
        "start": task.get("due", "2026-07-12"),
        "duration": 2,
        "critical": task.get("priority") in ["Urgent", "High"],
    })
    state.setdefault("tasks", []).append(task)
    put_state(state)
    return {"ok": True, "task": task}

@app.patch("/api/tasks/{task_id}")
def api_patch_task(task_id: str, payload: TaskPatch) -> Dict[str, Any]:
    state = get_state()
    idx = task_index(state, task_id)
    state["tasks"][idx].update(payload.fields)
    if payload.fields.get("status") == "DONE":
        state["tasks"][idx]["progress"] = 100
    put_state(state)
    return {"ok": True, "task": state["tasks"][idx]}

@app.delete("/api/tasks/{task_id}")
def api_delete_task(task_id: str) -> Dict[str, Any]:
    state = get_state()
    idx = task_index(state, task_id)
    task = state["tasks"].pop(idx)
    put_state(state)
    return {"ok": True, "deleted": task}

@app.post("/api/tasks/{task_id}/comments")
def api_add_comment(task_id: str, payload: CommentPayload) -> Dict[str, Any]:
    state = get_state()
    idx = task_index(state, task_id)
    comment = payload.model_dump()
    comment["created_at"] = utc_now().isoformat()
    state["tasks"][idx].setdefault("comments", []).append(comment)
    put_state(state)
    return {"ok": True, "comment": comment, "task": state["tasks"][idx]}

@app.post("/api/forms/project-intake")
def api_project_intake(payload: IntakePayload) -> Dict[str, Any]:
    state = get_state()
    task = {
        "id": make_id("t"),
        "projectId": "p1",
        "name": f"Intake: {payload.project_name}",
        "assignee": "adrian",
        "due": "2026-07-15",
        "priority": payload.priority,
        "status": "TO DO",
        "comments": [{"by": "Intake Agent", "text": f"Submitted by {payload.requester} / {payload.department}."}],
        "estimate": 2,
        "tracked": 0,
        "billable": False,
        "tags": ["Intake", payload.department],
        "progress": 0,
        "description": payload.description,
        "start": "2026-07-12",
        "duration": 2,
        "critical": payload.priority in ["Urgent", "High"],
    }
    state.setdefault("tasks", []).append(task)
    put_state(state)
    return {"ok": True, "task": task}

@app.get("/api/reports/summary")
def api_report_summary() -> Dict[str, Any]:
    state = get_state()
    tasks = state.get("tasks", [])
    open_tasks = [t for t in tasks if t.get("status") != "DONE"]
    blocked = [t for t in tasks if t.get("status") == "BLOCKED"]
    billable_hours = sum(float(t.get("tracked") or 0) for t in tasks if t.get("billable"))
    by_status: Dict[str, int] = {}
    for task in tasks:
        by_status[task.get("status", "Unknown")] = by_status.get(task.get("status", "Unknown"), 0) + 1
    return {
        "total_tasks": len(tasks),
        "open_tasks": len(open_tasks),
        "blocked_tasks": len(blocked),
        "billable_hours": billable_hours,
        "by_status": by_status,
    }

@app.post("/api/ai/project-summary")
def api_ai_summary() -> Dict[str, Any]:
    state = get_state()
    tasks = state.get("tasks", [])
    blocked = [t for t in tasks if t.get("status") == "BLOCKED"]
    due_soon = [t for t in tasks if t.get("status") != "DONE"][:4]
    return {
        "summary": "Project 1 is moving, but critical workflow and intake automation should be watched closely.",
        "health": "At Risk" if blocked else "On Track",
        "blockers": [t.get("name") for t in blocked],
        "next_actions": [
            "Unblock form field mapping",
            "Validate dashboard card schema",
            "Review Gantt critical path",
            "Prepare production demo script",
        ],
        "sources": [t.get("name") for t in due_soon],
    }
