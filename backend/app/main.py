from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    delete,
    func,
    select,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import text

APP_VERSION = "v0.3.0"
DEFAULT_WORKSPACE_ID = "w1"
DEFAULT_OWNER_ID = "adrian"
SEED_PATH = Path(__file__).with_name("seed_state.json")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/workos.db")
SECRET_KEY = os.getenv("SECRET_KEY", "thing-planner-workos-local-dev-secret")
TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", "24"))

metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("email", String(255), nullable=False, unique=True),
    Column("display_name", String(255), nullable=False),
    Column("initials", String(16), nullable=False, default="U"),
    Column("avatar", String(32), nullable=False, default="purple"),
    Column("title", String(255), nullable=True),
    Column("password_hash", String(255), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

workspaces = Table(
    "workspaces",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("name", String(255), nullable=False),
    Column("initials", String(16), nullable=False, default="W"),
    Column("owner_user_id", String(64), ForeignKey("users.id"), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

workspace_members = Table(
    "workspace_members",
    metadata,
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), primary_key=True),
    Column("user_id", String(64), ForeignKey("users.id"), primary_key=True),
    Column("role", String(64), nullable=False, default="Member"),
    Column("permissions", JSON, nullable=False, default=list),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

spaces = Table(
    "spaces",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("icon", String(32), nullable=False, default="👥"),
    Column("is_private", Boolean, nullable=False, default=False),
    Column("sort_order", Integer, nullable=False, default=0),
)

folders = Table(
    "folders",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("space_id", String(64), ForeignKey("spaces.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("icon", String(32), nullable=False, default="📁"),
    Column("sort_order", Integer, nullable=False, default=0),
)

lists = Table(
    "lists",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("folder_id", String(64), ForeignKey("folders.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("icon", String(32), nullable=False, default="☑"),
    Column("kind", String(64), nullable=False, default="project"),
    Column("sort_order", Integer, nullable=False, default=0),
)

task_statuses = Table(
    "task_statuses",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("name", String(64), nullable=False),
    Column("color", String(32), nullable=False, default="gray"),
    Column("sort_order", Integer, nullable=False, default=0),
    UniqueConstraint("workspace_id", "name", name="uq_status_workspace_name"),
)

tasks = Table(
    "tasks",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("list_id", String(64), ForeignKey("lists.id"), nullable=False),
    Column("parent_task_id", String(64), ForeignKey("tasks.id"), nullable=True),
    Column("name", String(500), nullable=False),
    Column("assignee_id", String(64), ForeignKey("users.id"), nullable=True),
    Column("created_by", String(64), ForeignKey("users.id"), nullable=True),
    Column("due", String(32), nullable=True),
    Column("start", String(32), nullable=True),
    Column("priority", String(32), nullable=False, default="Normal"),
    Column("status", String(64), nullable=False, default="TO DO"),
    Column("description", Text, nullable=False, default=""),
    Column("estimate", Float, nullable=False, default=0),
    Column("tracked", Float, nullable=False, default=0),
    Column("billable", Boolean, nullable=False, default=False),
    Column("tags", JSON, nullable=False, default=list),
    Column("progress", Integer, nullable=False, default=0),
    Column("duration", Integer, nullable=False, default=1),
    Column("critical", Boolean, nullable=False, default=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

task_comments = Table(
    "task_comments",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("task_id", String(64), ForeignKey("tasks.id"), nullable=False),
    Column("by_user_id", String(64), ForeignKey("users.id"), nullable=True),
    Column("by_name", String(255), nullable=False),
    Column("text", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

custom_fields = Table(
    "custom_fields",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("type", String(64), nullable=False),
    Column("scope", String(64), nullable=False, default="workspace"),
    Column("options", JSON, nullable=False, default=list),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

custom_field_values = Table(
    "custom_field_values",
    metadata,
    Column("task_id", String(64), ForeignKey("tasks.id"), primary_key=True),
    Column("field_id", String(64), ForeignKey("custom_fields.id"), primary_key=True),
    Column("value", JSON, nullable=True),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

notifications = Table(
    "notifications",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("user_id", String(64), ForeignKey("users.id"), nullable=True),
    Column("type", String(64), nullable=False),
    Column("title", String(500), nullable=False),
    Column("source", String(128), nullable=False),
    Column("read", Boolean, nullable=False, default=False),
    Column("tab", String(64), nullable=False, default="Primary"),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

dashboards = Table(
    "dashboards",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("is_private", Boolean, nullable=False, default=False),
    Column("favorite", Boolean, nullable=False, default=False),
    Column("config", JSON, nullable=False, default=dict),
)

forms = Table(
    "forms",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("description", Text, nullable=False, default=""),
    Column("submissions", Integer, nullable=False, default=0),
    Column("favorite", Boolean, nullable=False, default=False),
    Column("schema", JSON, nullable=False, default=dict),
)

docs = Table(
    "docs",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("title", String(255), nullable=False),
    Column("kind", String(128), nullable=False),
    Column("owner", String(255), nullable=False),
    Column("updated", String(64), nullable=False),
    Column("linked_tasks", Integer, nullable=False, default=0),
    Column("content", Text, nullable=False, default=""),
)

goals = Table(
    "goals",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("owner", String(255), nullable=False),
    Column("progress", Integer, nullable=False, default=0),
    Column("status", String(64), nullable=False, default="On Track"),
)

automations = Table(
    "automations",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("category", String(128), nullable=False),
    Column("enabled", Boolean, nullable=False, default=True),
    Column("trigger", String(255), nullable=False),
    Column("action", String(255), nullable=False),
)

activity_logs = Table(
    "activity_logs",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("actor_user_id", String(64), ForeignKey("users.id"), nullable=True),
    Column("event_type", String(128), nullable=False),
    Column("entity_type", String(128), nullable=False),
    Column("entity_id", String(128), nullable=False),
    Column("summary", String(500), nullable=False),
    Column("metadata", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

sessions = Table(
    "sessions",
    metadata,
    Column("id", String(128), primary_key=True),
    Column("user_id", String(64), ForeignKey("users.id"), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

engine = create_engine(DATABASE_URL, future=True, pool_pre_ping=True)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def make_id(prefix: str = "id") -> str:
    return f"{prefix}{int(datetime.now().timestamp() * 1000)}{secrets.token_hex(2)}"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64decode_url(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        method, salt, expected = stored.split("$", 2)
        if method != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()
        return hmac.compare_digest(digest, expected)
    except Exception:
        return False


def sign_token(user: Dict[str, Any]) -> str:
    header = {"alg": "HS256", "typ": "JWT-lite"}
    payload = {
        "sub": user["id"],
        "email": user["email"],
        "name": user["display_name"],
        "exp": int((utc_now() + timedelta(hours=TOKEN_HOURS)).timestamp()),
    }
    encoded_header = b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{encoded_header}.{encoded_payload}.{b64url(signature)}"


def decode_token(token: str) -> Dict[str, Any]:
    try:
        encoded_header, encoded_payload, encoded_signature = token.split(".")
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected = b64url(hmac.new(SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(expected, encoded_signature):
            raise ValueError("bad signature")
        payload = json.loads(b64decode_url(encoded_payload))
        if int(payload.get("exp", 0)) < int(utc_now().timestamp()):
            raise ValueError("expired")
        return payload
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token") from exc


def public_user(row: Any) -> Dict[str, Any]:
    m = dict(row._mapping if hasattr(row, "_mapping") else row)
    m.pop("password_hash", None)
    return m


def log_event(conn, event_type: str, entity_type: str, entity_id: str, summary: str, actor: Optional[str] = None, extra: Optional[dict] = None) -> None:
    conn.execute(activity_logs.insert().values(
        id=make_id("log"),
        workspace_id=DEFAULT_WORKSPACE_ID,
        actor_user_id=actor,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        summary=summary,
        metadata=extra or {},
        created_at=utc_now(),
    ))


class LoginPayload(BaseModel):
    email: str = "echofoxx@gmail.com"
    password: str = "thingplanner"


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
    description="v0.3 normalized database, demo auth, audit logs, custom fields, and API foundation for Thing Planner WorkOS.",
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
    ensure_seed_data()


def get_current_user(authorization: Optional[str] = Header(default=None)) -> Optional[Dict[str, Any]]:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Expected Bearer token")
    payload = decode_token(token)
    with engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.id == payload["sub"])).first()
        if not row:
            raise HTTPException(status_code=401, detail="User not found")
        return public_user(row)


def load_seed_state() -> Dict[str, Any]:
    with SEED_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data["version"] = "0.3.0"
    return data


def seed_users(conn, state: Dict[str, Any]) -> None:
    demo_hash = hash_password("thingplanner")
    member_rows = []
    for member in state.get("members", []):
        user_id = member.get("id") or make_id("u")
        email = "echofoxx@gmail.com" if user_id == "adrian" else f"{user_id}@example.local"
        member_rows.append({
            "id": user_id,
            "email": email,
            "display_name": member.get("name", user_id.title()),
            "initials": member.get("initials", user_id[:2].upper()),
            "avatar": member.get("avatar", "purple"),
            "title": member.get("role", "Member"),
            "password_hash": demo_hash if user_id == "adrian" else hash_password("demo"),
            "created_at": utc_now(),
        })
    if not member_rows:
        member_rows.append({
            "id": DEFAULT_OWNER_ID,
            "email": "echofoxx@gmail.com",
            "display_name": "Adrian Francis",
            "initials": "AF",
            "avatar": "purple",
            "title": "Workspace Owner",
            "password_hash": demo_hash,
            "created_at": utc_now(),
        })
    conn.execute(users.insert(), member_rows)


def ensure_seed_data() -> None:
    metadata.create_all(engine)
    with engine.begin() as conn:
        existing = conn.execute(select(func.count()).select_from(users)).scalar_one()
        if existing:
            return
        state = load_seed_state()
        seed_users(conn, state)
        workspace = state.get("workspace", {})
        conn.execute(workspaces.insert().values(
            id=DEFAULT_WORKSPACE_ID,
            name=workspace.get("name", "Adrian Francis's Workspace"),
            initials=workspace.get("initials", "A"),
            owner_user_id=DEFAULT_OWNER_ID,
            created_at=utc_now(),
        ))
        for member in state.get("members", []):
            conn.execute(workspace_members.insert().values(
                workspace_id=DEFAULT_WORKSPACE_ID,
                user_id=member["id"],
                role=member.get("role", "Member"),
                permissions=default_permissions(member.get("role", "Member")),
                created_at=utc_now(),
            ))
        status_colors = {"TO DO": "gray", "IN PROGRESS": "blue", "BLOCKED": "red", "DONE": "green"}
        for order, status_name in enumerate(["TO DO", "IN PROGRESS", "BLOCKED", "DONE"]):
            conn.execute(task_statuses.insert().values(id=f"st{order+1}", workspace_id=DEFAULT_WORKSPACE_ID, name=status_name, color=status_colors[status_name], sort_order=order))
        for s_order, space in enumerate(state.get("spaces", [])):
            conn.execute(spaces.insert().values(id=space["id"], workspace_id=DEFAULT_WORKSPACE_ID, name=space.get("name", "Space"), icon=space.get("icon", "👥"), is_private=False, sort_order=s_order))
            for f_order, folder in enumerate(space.get("folders", [])):
                conn.execute(folders.insert().values(id=folder["id"], space_id=space["id"], name=folder.get("name", "Folder"), icon=folder.get("icon", "📁"), sort_order=f_order))
                for l_order, item in enumerate(folder.get("lists", [])):
                    conn.execute(lists.insert().values(id=item["id"], folder_id=folder["id"], name=item.get("name", "List"), icon=item.get("icon", "☑"), kind=item.get("kind", "project"), sort_order=l_order))
        for task in state.get("tasks", []):
            upsert_task_row(conn, task, actor=DEFAULT_OWNER_ID, log=False)
            for comment in task.get("comments", []):
                conn.execute(task_comments.insert().values(
                    id=make_id("c"), task_id=task["id"], by_user_id=None, by_name=comment.get("by", "Adrian Francis"),
                    text=comment.get("text", ""), created_at=parse_or_now(comment.get("created_at")),
                ))
        for n in state.get("notifications", []):
            conn.execute(notifications.insert().values(
                id=n.get("id", make_id("n")), workspace_id=DEFAULT_WORKSPACE_ID, user_id=DEFAULT_OWNER_ID,
                type=n.get("type", "info"), title=n.get("title", "Notification"), source=n.get("source", "System"),
                read=bool(n.get("read", False)), tab=n.get("tab", "Primary"), created_at=utc_now(),
            ))
        for d in state.get("dashboards", []):
            conn.execute(dashboards.insert().values(id=d.get("id", make_id("d")), workspace_id=DEFAULT_WORKSPACE_ID, name=d.get("name", "Dashboard"), is_private=bool(d.get("private", False)), favorite=bool(d.get("favorite", False)), config={"cards": []}))
        for form in state.get("forms", []):
            conn.execute(forms.insert().values(id=form.get("id", make_id("form")), workspace_id=DEFAULT_WORKSPACE_ID, name=form.get("name", "Form"), description=form.get("description", ""), submissions=int(form.get("submissions", 0)), favorite=bool(form.get("favorite", False)), schema={"fields": []}))
        for doc in state.get("docs", []):
            conn.execute(docs.insert().values(id=doc.get("id", make_id("doc")), workspace_id=DEFAULT_WORKSPACE_ID, title=doc.get("title", "Doc"), kind=doc.get("kind", "Doc"), owner=doc.get("owner", "Adrian Francis"), updated=doc.get("updated", "Today"), linked_tasks=int(doc.get("linkedTasks", 0)), content=""))
        for goal in state.get("goals", []):
            conn.execute(goals.insert().values(id=goal.get("id", make_id("g")), workspace_id=DEFAULT_WORKSPACE_ID, name=goal.get("name", "Goal"), owner=goal.get("owner", "Adrian Francis"), progress=int(goal.get("progress", 0)), status=goal.get("status", "On Track")))
        for auto in state.get("automations", []):
            conn.execute(automations.insert().values(id=auto.get("id", make_id("a")), workspace_id=DEFAULT_WORKSPACE_ID, name=auto.get("name", "Automation"), category=auto.get("category", "Projects"), enabled=bool(auto.get("enabled", True)), trigger=auto.get("trigger", "Task updated"), action=auto.get("action", "Notify owner")))
        seed_custom_fields(conn)
        log_event(conn, "seed", "workspace", DEFAULT_WORKSPACE_ID, "Seeded normalized v0.3.0 workspace", DEFAULT_OWNER_ID, {"version": APP_VERSION})


def default_permissions(role: str) -> List[str]:
    role_l = role.lower()
    if "owner" in role_l or "admin" in role_l:
        return ["workspace:admin", "task:write", "dashboard:write", "automation:write", "audit:read", "auth:manage"]
    if "lead" in role_l:
        return ["task:write", "dashboard:write", "automation:write"]
    return ["task:write", "comment:write", "dashboard:read"]


def seed_custom_fields(conn) -> None:
    field_rows = [
        {"id": "cf_health", "name": "Project Health", "type": "dropdown", "options": ["On Track", "At Risk", "Blocked"]},
        {"id": "cf_client", "name": "Client / Stakeholder", "type": "text", "options": []},
        {"id": "cf_budget", "name": "Budget Impact", "type": "money", "options": []},
        {"id": "cf_ai_summary", "name": "AI Summary", "type": "ai", "options": []},
    ]
    for row in field_rows:
        conn.execute(custom_fields.insert().values(id=row["id"], workspace_id=DEFAULT_WORKSPACE_ID, name=row["name"], type=row["type"], scope="workspace", options=row["options"], created_at=utc_now()))


def parse_or_now(value: Optional[str]) -> datetime:
    if not value:
        return utc_now()
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return utc_now()


def upsert_task_row(conn, task: Dict[str, Any], actor: Optional[str] = None, log: bool = True) -> None:
    task_id = task.get("id") or make_id("t")
    values = {
        "id": task_id,
        "workspace_id": DEFAULT_WORKSPACE_ID,
        "list_id": task.get("projectId") or task.get("list_id") or "p1",
        "parent_task_id": task.get("parent_task_id"),
        "name": task.get("name", "Untitled task"),
        "assignee_id": task.get("assignee") or task.get("assignee_id"),
        "created_by": task.get("created_by") or actor,
        "due": task.get("due"),
        "start": task.get("start") or task.get("due"),
        "priority": task.get("priority", "Normal"),
        "status": task.get("status", "TO DO"),
        "description": task.get("description", ""),
        "estimate": float(task.get("estimate") or 0),
        "tracked": float(task.get("tracked") or 0),
        "billable": bool(task.get("billable", False)),
        "tags": task.get("tags") or [],
        "progress": int(task.get("progress") or 0),
        "duration": int(task.get("duration") or 1),
        "critical": bool(task.get("critical", False)),
        "created_at": parse_or_now(task.get("created_at")),
        "updated_at": utc_now(),
    }
    existing = conn.execute(select(tasks.c.id).where(tasks.c.id == task_id)).first()
    if existing:
        conn.execute(tasks.update().where(tasks.c.id == task_id).values(**{k: v for k, v in values.items() if k not in ["id", "created_at"]}))
        if log:
            log_event(conn, "task.updated", "task", task_id, f"Updated task: {values['name']}", actor, {"status": values["status"]})
    else:
        conn.execute(tasks.insert().values(**values))
        if log:
            log_event(conn, "task.created", "task", task_id, f"Created task: {values['name']}", actor, {"status": values["status"]})


def serialize_state() -> Dict[str, Any]:
    ensure_seed_data()
    with engine.begin() as conn:
        workspace_row = conn.execute(select(workspaces).where(workspaces.c.id == DEFAULT_WORKSPACE_ID)).first()
        member_rows = conn.execute(
            select(users.c.id, users.c.display_name, users.c.initials, users.c.avatar, workspace_members.c.role)
            .join(workspace_members, users.c.id == workspace_members.c.user_id)
            .where(workspace_members.c.workspace_id == DEFAULT_WORKSPACE_ID)
            .order_by(users.c.display_name)
        ).all()
        space_rows = conn.execute(select(spaces).where(spaces.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(spaces.c.sort_order)).all()
        folder_rows = conn.execute(select(folders).order_by(folders.c.sort_order)).all()
        list_rows = conn.execute(select(lists).order_by(lists.c.sort_order)).all()
        task_rows = conn.execute(select(tasks).where(tasks.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(tasks.c.created_at)).all()
        comment_rows = conn.execute(select(task_comments).order_by(task_comments.c.created_at)).all()
        notification_rows = conn.execute(select(notifications).where(notifications.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(notifications.c.created_at.desc())).all()
        dashboard_rows = conn.execute(select(dashboards).where(dashboards.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        form_rows = conn.execute(select(forms).where(forms.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        doc_rows = conn.execute(select(docs).where(docs.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        goal_rows = conn.execute(select(goals).where(goals.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        automation_rows = conn.execute(select(automations).where(automations.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        custom_field_rows = conn.execute(select(custom_fields).where(custom_fields.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()

    comments_by_task: Dict[str, List[Dict[str, Any]]] = {}
    for c in comment_rows:
        cm = c._mapping
        comments_by_task.setdefault(cm["task_id"], []).append({"by": cm["by_name"], "text": cm["text"], "created_at": cm["created_at"].isoformat()})

    folders_by_space: Dict[str, List[Dict[str, Any]]] = {}
    for fr in folder_rows:
        f = fr._mapping
        lists_for_folder = []
        for lr in list_rows:
            l = lr._mapping
            if l["folder_id"] == f["id"]:
                lists_for_folder.append({"id": l["id"], "name": l["name"], "icon": l["icon"], "kind": l["kind"]})
        folders_by_space.setdefault(f["space_id"], []).append({"id": f["id"], "name": f["name"], "icon": f["icon"], "lists": lists_for_folder})

    workspace = workspace_row._mapping if workspace_row else {"name": "Workspace", "initials": "W"}
    return {
        "module": "home",
        "view": "list",
        "selectedProject": "p1",
        "helper": True,
        "aiPromo": True,
        "version": "0.3.0",
        "workspace": {"name": workspace["name"], "initials": workspace["initials"]},
        "members": [
            {"id": r.id, "name": r.display_name, "initials": r.initials, "avatar": r.avatar, "role": r.role}
            for r in member_rows
        ],
        "spaces": [
            {"id": r.id, "name": r.name, "icon": r.icon, "folders": folders_by_space.get(r.id, [])}
            for r in space_rows
        ],
        "tasks": [
            {
                "id": r.id,
                "projectId": r.list_id,
                "name": r.name,
                "assignee": r.assignee_id or "adrian",
                "due": r.due or "",
                "priority": r.priority,
                "status": r.status,
                "comments": comments_by_task.get(r.id, []),
                "estimate": r.estimate,
                "tracked": r.tracked,
                "billable": r.billable,
                "tags": r.tags or [],
                "progress": r.progress,
                "description": r.description,
                "start": r.start or r.due or "",
                "duration": r.duration,
                "critical": r.critical,
            }
            for r in task_rows
        ],
        "notifications": [
            {"id": r.id, "type": r.type, "title": r.title, "source": r.source, "read": r.read, "tab": r.tab}
            for r in notification_rows
        ],
        "dashboards": [{"id": r.id, "name": r.name, "private": r.is_private, "favorite": r.favorite} for r in dashboard_rows],
        "forms": [{"id": r.id, "name": r.name, "description": r.description, "submissions": r.submissions, "favorite": r.favorite} for r in form_rows],
        "docs": [{"id": r.id, "title": r.title, "kind": r.kind, "owner": r.owner, "updated": r.updated, "linkedTasks": r.linked_tasks} for r in doc_rows],
        "goals": [{"id": r.id, "name": r.name, "owner": r.owner, "progress": r.progress, "status": r.status} for r in goal_rows],
        "automations": [{"id": r.id, "name": r.name, "category": r.category, "enabled": r.enabled, "trigger": r.trigger, "action": r.action} for r in automation_rows],
        "customFields": [{"id": r.id, "name": r.name, "type": r.type, "scope": r.scope, "options": r.options or []} for r in custom_field_rows],
    }


def apply_state_to_normalized_tables(state: Dict[str, Any], actor: Optional[str] = None) -> None:
    with engine.begin() as conn:
        if "workspace" in state:
            conn.execute(workspaces.update().where(workspaces.c.id == DEFAULT_WORKSPACE_ID).values(name=state["workspace"].get("name", "Workspace"), initials=state["workspace"].get("initials", "W")))
        for task in state.get("tasks", []):
            upsert_task_row(conn, task, actor=actor, log=False)
            conn.execute(delete(task_comments).where(task_comments.c.task_id == task.get("id")))
            for comment in task.get("comments", []):
                conn.execute(task_comments.insert().values(
                    id=make_id("c"),
                    task_id=task.get("id"),
                    by_user_id=None,
                    by_name=comment.get("by", "Adrian Francis"),
                    text=comment.get("text", ""),
                    created_at=parse_or_now(comment.get("created_at")),
                ))
        if "notifications" in state:
            conn.execute(delete(notifications).where(notifications.c.workspace_id == DEFAULT_WORKSPACE_ID))
            for n in state.get("notifications", []):
                conn.execute(notifications.insert().values(
                    id=n.get("id", make_id("n")), workspace_id=DEFAULT_WORKSPACE_ID, user_id=DEFAULT_OWNER_ID,
                    type=n.get("type", "info"), title=n.get("title", "Notification"), source=n.get("source", "System"),
                    read=bool(n.get("read", False)), tab=n.get("tab", "Primary"), created_at=utc_now(),
                ))
        log_event(conn, "state.synced", "workspace", DEFAULT_WORKSPACE_ID, "Synchronized frontend state into normalized tables", actor, {"task_count": len(state.get("tasks", []))})


@app.get("/api/health")
def health() -> Dict[str, Any]:
    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
            table_counts = {
                "users": conn.execute(select(func.count()).select_from(users)).scalar_one(),
                "tasks": conn.execute(select(func.count()).select_from(tasks)).scalar_one(),
                "comments": conn.execute(select(func.count()).select_from(task_comments)).scalar_one(),
                "custom_fields": conn.execute(select(func.count()).select_from(custom_fields)).scalar_one(),
                "activity_logs": conn.execute(select(func.count()).select_from(activity_logs)).scalar_one(),
            }
        db_ok = True
    except SQLAlchemyError:
        db_ok = False
        table_counts = {}
    return {
        "status": "ok" if db_ok else "degraded",
        "version": APP_VERSION,
        "database": engine.dialect.name,
        "schema": "normalized",
        "auth": "enabled",
        "workspace_id": DEFAULT_WORKSPACE_ID,
        "tables": table_counts,
        "timestamp": utc_now().isoformat(),
    }


@app.post("/api/auth/login")
def login(payload: LoginPayload) -> Dict[str, Any]:
    with engine.begin() as conn:
        row = conn.execute(select(users).where(users.c.email == payload.email.lower())).first()
        if not row or not verify_password(payload.password, row.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        user = public_user(row)
        token = sign_token(user)
        session_id = make_id("sess")
        conn.execute(sessions.insert().values(id=session_id, user_id=user["id"], expires_at=utc_now() + timedelta(hours=TOKEN_HOURS), created_at=utc_now()))
        log_event(conn, "auth.login", "user", user["id"], f"{user['display_name']} signed in", user["id"], {})
    return {"ok": True, "token": token, "user": user, "expires_in_hours": TOKEN_HOURS}


@app.post("/api/auth/demo-login")
def demo_login() -> Dict[str, Any]:
    return login(LoginPayload(email="echofoxx@gmail.com", password="thingplanner"))


@app.get("/api/auth/me")
def auth_me(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    if not current_user:
        raise HTTPException(status_code=401, detail="Not signed in")
    return {"user": current_user}


@app.get("/api/schema")
def api_schema() -> Dict[str, Any]:
    return {
        "version": APP_VERSION,
        "schema": "normalized",
        "core_entities": [
            "users", "workspaces", "workspace_members", "spaces", "folders", "lists", "task_statuses", "tasks",
            "task_comments", "custom_fields", "custom_field_values", "notifications", "dashboards", "forms",
            "docs", "goals", "automations", "activity_logs", "sessions",
        ],
        "compatibility": "The /api/state endpoint serializes normalized tables into the v0.1/v0.2 frontend state shape.",
    }


@app.get("/api/workspaces/current")
def api_workspace() -> Dict[str, Any]:
    state = serialize_state()
    return {"workspace": state["workspace"], "members": state["members"], "spaces": state["spaces"], "customFields": state["customFields"]}


@app.get("/api/members")
def api_members() -> Dict[str, Any]:
    with engine.begin() as conn:
        rows = conn.execute(select(users.c.id, users.c.email, users.c.display_name, users.c.initials, users.c.avatar, users.c.title)).all()
    return {"members": [dict(r._mapping) for r in rows]}


@app.get("/api/permissions")
def api_permissions() -> Dict[str, Any]:
    with engine.begin() as conn:
        rows = conn.execute(select(workspace_members)).all()
    return {"workspace_id": DEFAULT_WORKSPACE_ID, "members": [dict(r._mapping) for r in rows]}


@app.get("/api/activity")
def api_activity(limit: int = 50) -> Dict[str, Any]:
    with engine.begin() as conn:
        rows = conn.execute(select(activity_logs).order_by(activity_logs.c.created_at.desc()).limit(limit)).all()
    return {"activity": [dict(r._mapping) for r in rows]}


@app.get("/api/state")
def api_get_state() -> Dict[str, Any]:
    return {"state": serialize_state()}


@app.put("/api/state")
def api_put_state(payload: StatePayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    apply_state_to_normalized_tables(payload.state, actor=actor)
    return {"ok": True, "state": serialize_state(), "updated_at": utc_now().isoformat()}


@app.post("/api/reset")
def api_reset() -> Dict[str, Any]:
    metadata.drop_all(engine)
    metadata.create_all(engine)
    ensure_seed_data()
    return {"ok": True, "state": serialize_state()}


@app.get("/api/tasks")
def api_tasks(projectId: Optional[str] = None, status_filter: Optional[str] = None, assignee: Optional[str] = None) -> Dict[str, Any]:
    state = serialize_state()
    task_list = state.get("tasks", [])
    if projectId:
        task_list = [t for t in task_list if t.get("projectId") == projectId]
    if status_filter:
        task_list = [t for t in task_list if t.get("status") == status_filter]
    if assignee:
        task_list = [t for t in task_list if t.get("assignee") == assignee]
    return {"tasks": task_list}


@app.post("/api/tasks")
def api_create_task(payload: TaskPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    task = payload.model_dump()
    task.update({
        "id": make_id("t"),
        "comments": [],
        "progress": 0,
        "start": task.get("due", "2026-07-12"),
        "duration": 2,
        "critical": task.get("priority") in ["Urgent", "High"],
    })
    with engine.begin() as conn:
        upsert_task_row(conn, task, actor=actor, log=True)
    return {"ok": True, "task": task}


@app.patch("/api/tasks/{task_id}")
def api_patch_task(task_id: str, payload: TaskPatch, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        row = conn.execute(select(tasks).where(tasks.c.id == task_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        fields = dict(payload.fields)
        allowed = {"name", "list_id", "parent_task_id", "assignee_id", "due", "start", "priority", "status", "description", "estimate", "tracked", "billable", "tags", "progress", "duration", "critical"}
        normalized: Dict[str, Any] = {}
        for k, v in fields.items():
            nk = {"projectId": "list_id", "assignee": "assignee_id"}.get(k, k)
            if nk in allowed:
                normalized[nk] = v
        if normalized.get("status") == "DONE":
            normalized["progress"] = 100
        normalized["updated_at"] = utc_now()
        conn.execute(tasks.update().where(tasks.c.id == task_id).values(**normalized))
        log_event(conn, "task.updated", "task", task_id, f"Updated task: {row.name}", actor, {"fields": list(normalized.keys())})
    return {"ok": True, "task": next(t for t in serialize_state()["tasks"] if t["id"] == task_id)}


@app.delete("/api/tasks/{task_id}")
def api_delete_task(task_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        row = conn.execute(select(tasks).where(tasks.c.id == task_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        conn.execute(delete(task_comments).where(task_comments.c.task_id == task_id))
        conn.execute(delete(custom_field_values).where(custom_field_values.c.task_id == task_id))
        conn.execute(delete(tasks).where(tasks.c.id == task_id))
        log_event(conn, "task.deleted", "task", task_id, f"Deleted task: {row.name}", actor, {})
    return {"ok": True, "deleted": task_id}


@app.post("/api/tasks/{task_id}/comments")
def api_add_comment(task_id: str, payload: CommentPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    by_name = current_user["display_name"] if current_user else payload.by
    with engine.begin() as conn:
        row = conn.execute(select(tasks.c.id, tasks.c.name).where(tasks.c.id == task_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        comment = {"id": make_id("c"), "task_id": task_id, "by_user_id": actor, "by_name": by_name, "text": payload.text, "created_at": utc_now()}
        conn.execute(task_comments.insert().values(**comment))
        log_event(conn, "comment.created", "task", task_id, f"Commented on task: {row.name}", actor, {})
    return {"ok": True, "comment": {"by": by_name, "text": payload.text, "created_at": comment["created_at"].isoformat()}}


@app.get("/api/custom-fields")
def api_custom_fields() -> Dict[str, Any]:
    with engine.begin() as conn:
        rows = conn.execute(select(custom_fields).where(custom_fields.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
    return {"custom_fields": [dict(r._mapping) for r in rows]}


@app.post("/api/forms/project-intake")
def api_project_intake(payload: IntakePayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    task = {
        "id": make_id("t"),
        "projectId": "p1",
        "name": f"Intake: {payload.project_name}",
        "assignee": "adrian",
        "due": "2026-07-15",
        "priority": payload.priority,
        "status": "TO DO",
        "comments": [],
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
    with engine.begin() as conn:
        upsert_task_row(conn, task, actor=actor, log=True)
        conn.execute(task_comments.insert().values(
            id=make_id("c"), task_id=task["id"], by_user_id=actor, by_name="Intake Agent",
            text=f"Submitted by {payload.requester} / {payload.department}.", created_at=utc_now(),
        ))
        conn.execute(forms.update().where(forms.c.id == "form1").values(submissions=forms.c.submissions + 1))
    return {"ok": True, "task": task}


@app.get("/api/reports/summary")
def api_report_summary() -> Dict[str, Any]:
    state = serialize_state()
    task_list = state.get("tasks", [])
    open_tasks = [t for t in task_list if t.get("status") != "DONE"]
    blocked = [t for t in task_list if t.get("status") == "BLOCKED"]
    billable_hours = sum(float(t.get("tracked") or 0) for t in task_list if t.get("billable"))
    by_status: Dict[str, int] = {}
    by_assignee: Dict[str, int] = {}
    for task in task_list:
        by_status[task.get("status", "Unknown")] = by_status.get(task.get("status", "Unknown"), 0) + 1
        by_assignee[task.get("assignee", "unassigned")] = by_assignee.get(task.get("assignee", "unassigned"), 0) + 1
    return {
        "total_tasks": len(task_list),
        "open_tasks": len(open_tasks),
        "blocked_tasks": len(blocked),
        "billable_hours": billable_hours,
        "by_status": by_status,
        "by_assignee": by_assignee,
        "schema": "normalized",
    }


@app.post("/api/ai/project-summary")
def api_ai_summary() -> Dict[str, Any]:
    state = serialize_state()
    task_list = state.get("tasks", [])
    blocked = [t for t in task_list if t.get("status") == "BLOCKED"]
    critical_open = [t for t in task_list if t.get("critical") and t.get("status") != "DONE"]
    due_soon = [t for t in task_list if t.get("status") != "DONE"][:4]
    health = "At Risk" if blocked or len(critical_open) >= 2 else "On Track"
    return {
        "summary": "The workspace is API-backed with normalized tasks, comments, custom fields, activity logs, and demo authentication. Watch blocked or critical-path work before expanding automations.",
        "health": health,
        "blockers": [t.get("name") for t in blocked],
        "next_actions": [
            "Validate normalized table writes from List and Board views",
            "Move dashboard cards from derived frontend state to report endpoints",
            "Add real role enforcement for workspace members",
            "Prepare v0.4 dashboard builder and custom report engine",
        ],
        "sources": [t.get("name") for t in due_soon],
    }
