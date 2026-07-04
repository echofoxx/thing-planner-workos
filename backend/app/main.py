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

APP_VERSION = "v0.9.3"
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

report_cards = Table(
    "report_cards",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("dashboard_id", String(64), ForeignKey("dashboards.id"), nullable=False),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("title", String(255), nullable=False),
    Column("card_type", String(64), nullable=False, default="kpi"),
    Column("metric", String(128), nullable=False, default="open_tasks"),
    Column("filters", JSON, nullable=False, default=dict),
    Column("layout", JSON, nullable=False, default=dict),
    Column("config", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
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

form_submissions = Table(
    "form_submissions",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("form_id", String(64), ForeignKey("forms.id"), nullable=False),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("requester", String(255), nullable=False),
    Column("department", String(255), nullable=False, default="Product"),
    Column("priority", String(32), nullable=False, default="Normal"),
    Column("payload", JSON, nullable=False, default=dict),
    Column("ai_analysis", JSON, nullable=False, default=dict),
    Column("created_task_id", String(64), ForeignKey("tasks.id"), nullable=True),
    Column("status", String(64), nullable=False, default="Processed"),
    Column("created_at", DateTime(timezone=True), nullable=False),
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

# v0.8 Docs + Knowledge / Wiki Engine tables
doc_pages = Table(
    "doc_pages",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("doc_id", String(64), ForeignKey("docs.id"), nullable=False),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("parent_page_id", String(64), ForeignKey("doc_pages.id"), nullable=True),
    Column("title", String(255), nullable=False),
    Column("page_type", String(64), nullable=False, default="page"),
    Column("content", Text, nullable=False, default=""),
    Column("sort_order", Integer, nullable=False, default=0),
    Column("protected", Boolean, nullable=False, default=False),
    Column("verified", Boolean, nullable=False, default=False),
    Column("created_by", String(64), ForeignKey("users.id"), nullable=True),
    Column("updated_by", String(64), ForeignKey("users.id"), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

doc_versions = Table(
    "doc_versions",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("doc_id", String(64), ForeignKey("docs.id"), nullable=False),
    Column("page_id", String(64), ForeignKey("doc_pages.id"), nullable=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("version_number", Integer, nullable=False, default=1),
    Column("title", String(255), nullable=False),
    Column("content", Text, nullable=False, default=""),
    Column("created_by", String(64), ForeignKey("users.id"), nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

doc_task_links = Table(
    "doc_task_links",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("doc_id", String(64), ForeignKey("docs.id"), nullable=False),
    Column("page_id", String(64), ForeignKey("doc_pages.id"), nullable=True),
    Column("task_id", String(64), ForeignKey("tasks.id"), nullable=False),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("relation", String(64), nullable=False, default="references"),
    Column("created_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("doc_id", "task_id", "relation", name="uq_doc_task_relation"),
)

doc_decisions = Table(
    "doc_decisions",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("doc_id", String(64), ForeignKey("docs.id"), nullable=False),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("title", String(500), nullable=False),
    Column("decision", Text, nullable=False),
    Column("rationale", Text, nullable=False, default=""),
    Column("owner", String(255), nullable=False, default="Adrian Francis"),
    Column("status", String(64), nullable=False, default="Accepted"),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


# v0.9 Visual Collaboration / Whiteboards + Canvas + Mind Maps tables
whiteboards = Table(
    "whiteboards",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("icon", String(32), nullable=False, default="✎"),
    Column("owner", String(255), nullable=False, default="Adrian Francis"),
    Column("favorite", Boolean, nullable=False, default=False),
    Column("updated", String(64), nullable=False, default="Today"),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

whiteboard_objects = Table(
    "whiteboard_objects",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("whiteboard_id", String(64), ForeignKey("whiteboards.id"), nullable=False),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("object_type", String(64), nullable=False, default="sticky"),
    Column("text", Text, nullable=False, default=""),
    Column("color", String(32), nullable=False, default="yellow"),
    Column("x", Integer, nullable=False, default=80),
    Column("y", Integer, nullable=False, default=80),
    Column("w", Integer, nullable=False, default=180),
    Column("h", Integer, nullable=False, default=120),
    Column("task_id", String(64), ForeignKey("tasks.id"), nullable=True),
    Column("doc_id", String(64), ForeignKey("docs.id"), nullable=True),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

whiteboard_edges = Table(
    "whiteboard_edges",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("whiteboard_id", String(64), ForeignKey("whiteboards.id"), nullable=False),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("from_object_id", String(64), nullable=False),
    Column("to_object_id", String(64), nullable=False),
    Column("label", String(128), nullable=False, default="relates"),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

canvas_cards = Table(
    "canvas_cards",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("whiteboard_id", String(64), ForeignKey("whiteboards.id"), nullable=False),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("title", String(255), nullable=False),
    Column("kind", String(128), nullable=False, default="Card"),
    Column("metric", String(128), nullable=False, default=""),
    Column("x", Integer, nullable=False, default=80),
    Column("y", Integer, nullable=False, default=80),
    Column("linked_type", String(64), nullable=False, default="module"),
    Column("linked_id", String(128), nullable=False, default="spaces"),
    Column("config", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

mind_map_nodes = Table(
    "mind_map_nodes",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("whiteboard_id", String(64), ForeignKey("whiteboards.id"), nullable=False),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("parent_node_id", String(64), nullable=True),
    Column("label", String(255), nullable=False),
    Column("kind", String(64), nullable=False, default="module"),
    Column("linked_type", String(64), nullable=True),
    Column("linked_id", String(128), nullable=True),
    Column("sort_order", Integer, nullable=False, default=0),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
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

automation_runs = Table(
    "automation_runs",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("automation_id", String(64), ForeignKey("automations.id"), nullable=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("trigger", String(255), nullable=False),
    Column("source_type", String(128), nullable=False),
    Column("source_id", String(128), nullable=False),
    Column("status", String(64), nullable=False, default="success"),
    Column("summary", String(500), nullable=False),
    Column("details", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


calendar_events = Table(
    "calendar_events",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("title", String(500), nullable=False),
    Column("kind", String(64), nullable=False, default="meeting"),
    Column("start_at", String(64), nullable=False),
    Column("end_at", String(64), nullable=False),
    Column("source", String(128), nullable=False, default="manual"),
    Column("task_id", String(64), ForeignKey("tasks.id"), nullable=True),
    Column("owner_id", String(64), ForeignKey("users.id"), nullable=True),
    Column("color", String(32), nullable=False, default="blue"),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

planner_blocks = Table(
    "planner_blocks",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("task_id", String(64), ForeignKey("tasks.id"), nullable=True),
    Column("title", String(500), nullable=False),
    Column("owner_id", String(64), ForeignKey("users.id"), nullable=True),
    Column("start_at", String(64), nullable=False),
    Column("end_at", String(64), nullable=False),
    Column("block_type", String(64), nullable=False, default="task"),
    Column("status", String(64), nullable=False, default="planned"),
    Column("score", Float, nullable=False, default=0),
    Column("reason", Text, nullable=False, default=""),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

planner_preferences = Table(
    "planner_preferences",
    metadata,
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), primary_key=True),
    Column("workday_start", String(16), nullable=False, default="08:30"),
    Column("workday_end", String(16), nullable=False, default="17:00"),
    Column("lunch_start", String(16), nullable=False, default="12:00"),
    Column("lunch_end", String(16), nullable=False, default="13:00"),
    Column("focus_block_minutes", Integer, nullable=False, default=90),
    Column("auto_schedule_blocked", Boolean, nullable=False, default=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)


task_dependencies = Table(
    "task_dependencies",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("predecessor_task_id", String(64), ForeignKey("tasks.id"), nullable=False),
    Column("successor_task_id", String(64), ForeignKey("tasks.id"), nullable=False),
    Column("dependency_type", String(32), nullable=False, default="FS"),
    Column("lag_days", Integer, nullable=False, default=0),
    Column("critical", Boolean, nullable=False, default=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    UniqueConstraint("predecessor_task_id", "successor_task_id", name="uq_task_dependency_pair"),
)

gantt_baselines = Table(
    "gantt_baselines",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("list_id", String(64), ForeignKey("lists.id"), nullable=False),
    Column("name", String(255), nullable=False),
    Column("task_snapshots", JSON, nullable=False, default=list),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

gantt_risk_alerts = Table(
    "gantt_risk_alerts",
    metadata,
    Column("id", String(64), primary_key=True),
    Column("workspace_id", String(64), ForeignKey("workspaces.id"), nullable=False),
    Column("list_id", String(64), ForeignKey("lists.id"), nullable=False),
    Column("task_id", String(64), ForeignKey("tasks.id"), nullable=True),
    Column("level", String(32), nullable=False, default="medium"),
    Column("title", String(500), nullable=False),
    Column("recommendation", Text, nullable=False, default=""),
    Column("metadata_json", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False),
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


class ReportActionPayload(BaseModel):
    task_id: str
    action: str
    value: Optional[Any] = None
    comment: Optional[str] = None


class ReportCardPayload(BaseModel):
    dashboard_id: str = "d1"
    title: str
    card_type: str = "kpi"
    metric: str = "open_tasks"
    filters: Dict[str, Any] = Field(default_factory=dict)
    layout: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)


class IntakePayload(BaseModel):
    project_name: str
    requester: str = "Adrian Francis"
    department: str = "Product"
    priority: str = "Normal"
    description: str = ""
    desired_due_date: Optional[str] = None
    business_objective: str = ""


class FormSubmissionPayload(BaseModel):
    form_id: str = "form1"
    fields: Dict[str, Any] = Field(default_factory=dict)


class FormSchemaPayload(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    form_schema: Dict[str, Any] = Field(default_factory=dict, alias="schema")


class AutomationPayload(BaseModel):
    name: str
    category: str = "Automate Projects"
    trigger: str = "Form submitted"
    action: str = "Create task"
    enabled: bool = True


class AutomationRunPayload(BaseModel):
    automation_id: Optional[str] = None
    trigger: str = "manual"
    source_type: str = "workspace"
    source_id: str = DEFAULT_WORKSPACE_ID
    details: Dict[str, Any] = Field(default_factory=dict)


class PlannerSchedulePayload(BaseModel):
    date: Optional[str] = None
    owner_id: str = DEFAULT_OWNER_ID
    mode: str = "balanced"
    regenerate: bool = True


class CalendarEventPayload(BaseModel):
    title: str
    kind: str = "meeting"
    start_at: str
    end_at: str
    source: str = "manual"
    task_id: Optional[str] = None
    owner_id: str = DEFAULT_OWNER_ID
    color: str = "blue"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskSchedulePayload(BaseModel):
    date: str
    start_time: str
    duration_minutes: int = 60
    owner_id: str = DEFAULT_OWNER_ID
    reason: str = "Manual schedule from Planner"


class FocusBlockPayload(BaseModel):
    date: str
    start_time: str = "10:00"
    duration_minutes: int = 90
    title: str = "Focus block"
    owner_id: str = DEFAULT_OWNER_ID
    reason: str = "Protected focus time"


class GanttDependencyPayload(BaseModel):
    predecessor_task_id: str
    successor_task_id: str
    dependency_type: str = "FS"
    lag_days: int = 0
    critical: bool = False


class GanttSchedulePayload(BaseModel):
    start: Optional[str] = None
    due: Optional[str] = None
    duration: Optional[int] = None
    cascade: bool = True
    reason: str = "Manual Gantt schedule update"


class GanttBaselinePayload(BaseModel):
    project_id: str = "p1"
    name: str = "Baseline"


class DocPayload(BaseModel):
    title: str = "Untitled Doc"
    kind: str = "Doc"
    owner: str = "Adrian Francis"
    content: str = ""
    verified: bool = False
    protected: bool = False


class DocPatchPayload(BaseModel):
    title: Optional[str] = None
    kind: Optional[str] = None
    content: Optional[str] = None
    verified: Optional[bool] = None
    protected: Optional[bool] = None


class DocLinkPayload(BaseModel):
    task_id: str
    relation: str = "references"


class DecisionPayload(BaseModel):
    title: str = "Decision"
    decision: str
    rationale: str = ""
    owner: str = "Adrian Francis"
    status: str = "Accepted"



class WhiteboardPayload(BaseModel):
    name: str = "New Whiteboard"
    icon: str = "✎"
    favorite: bool = False
    objects: List[Dict[str, Any]] = Field(default_factory=list)
    edges: List[Dict[str, Any]] = Field(default_factory=list)
    canvas_cards: List[Dict[str, Any]] = Field(default_factory=list)
    mind_map: Dict[str, Any] = Field(default_factory=dict)


class WhiteboardObjectPayload(BaseModel):
    object_type: str = "sticky"
    text: str = "New idea"
    color: str = "yellow"
    x: int = 80
    y: int = 80
    w: int = 180
    h: int = 120
    task_id: Optional[str] = None
    doc_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CanvasCardPayload(BaseModel):
    title: str = "Live Work Card"
    kind: str = "Task Rollup"
    metric: str = ""
    x: int = 80
    y: int = 80
    linked_type: str = "dashboard"
    linked_id: str = "d1"
    config: Dict[str, Any] = Field(default_factory=dict)


class MindMapNodePayload(BaseModel):
    parent_node_id: Optional[str] = None
    label: str = "New Node"
    kind: str = "feature"
    linked_type: Optional[str] = None
    linked_id: Optional[str] = None
    sort_order: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


app = FastAPI(
    title="Thing Planner WorkOS API",
    version=APP_VERSION,
    description="v0.9.3 functional hardening: connected workspace shell, persistent UI actions, API/state sync, planner, docs, Gantt, forms, and visual collaboration.",
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
    ensure_default_report_cards()
    ensure_default_planner_data()
    ensure_default_gantt_data()
    ensure_default_docs_data()
    ensure_default_whiteboard_data()


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
    data["version"] = "0.9.3"
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
        dashboard_ids: List[str] = []
        for d in state.get("dashboards", []):
            dashboard_id = d.get("id", make_id("d"))
            dashboard_ids.append(dashboard_id)
            conn.execute(dashboards.insert().values(id=dashboard_id, workspace_id=DEFAULT_WORKSPACE_ID, name=d.get("name", "Dashboard"), is_private=bool(d.get("private", False)), favorite=bool(d.get("favorite", False)), config={"cards": []}))
        if dashboard_ids:
            default_cards = [
                ("rc_open", "Open Tasks", "kpi", "open_tasks", {}, {"x": 0, "y": 0, "w": 3, "h": 1}),
                ("rc_blocked", "Blocked Work", "kpi", "blocked_tasks", {}, {"x": 3, "y": 0, "w": 3, "h": 1}),
                ("rc_billable", "Billable Hours", "kpi", "billable_hours", {}, {"x": 6, "y": 0, "w": 3, "h": 1}),
                ("rc_health", "Project Health", "ai", "project_health", {}, {"x": 9, "y": 0, "w": 3, "h": 1}),
                ("rc_status", "Work by Status", "chart", "by_status", {}, {"x": 0, "y": 1, "w": 6, "h": 3}),
                ("rc_assignee", "Team Productivity", "chart", "by_assignee", {}, {"x": 6, "y": 1, "w": 6, "h": 3}),
                ("rc_tasks", "Actionable Work Table", "table", "task_table", {}, {"x": 0, "y": 4, "w": 12, "h": 4}),
            ]
            for cid, title, ctype, metric, filters, layout in default_cards:
                conn.execute(report_cards.insert().values(
                    id=cid, dashboard_id=dashboard_ids[0], workspace_id=DEFAULT_WORKSPACE_ID, title=title,
                    card_type=ctype, metric=metric, filters=filters, layout=layout, config={},
                    created_at=utc_now(), updated_at=utc_now(),
                ))
        default_form_schemas = {
            "form1": {
                "mode": "task_intake",
                "target_project_id": "p1",
                "apply_template": "Project Kickoff",
                "ai_analysis": True,
                "field_mappings": {"project_name": "task.name", "priority": "task.priority", "department": "task.tags", "business_objective": "task.description"},
                "fields": [
                    {"id": "project_name", "label": "Project name", "type": "short_text", "required": True},
                    {"id": "requester", "label": "Requester", "type": "short_text", "required": True},
                    {"id": "department", "label": "Department", "type": "dropdown", "options": ["Product", "Engineering", "Marketing", "Operations", "Finance"]},
                    {"id": "priority", "label": "Priority", "type": "dropdown", "options": ["Normal", "High", "Urgent"]},
                    {"id": "business_objective", "label": "Business objective", "type": "long_text"},
                    {"id": "desired_due_date", "label": "Desired due date", "type": "date"}
                ],
                "automation_chain": ["auto_intake_classify", "auto_intake_task", "auto_intake_notify"]
            },
            "form2": {
                "mode": "service_request",
                "target_project_id": "p2",
                "ai_analysis": True,
                "field_mappings": {"request": "task.name", "severity": "task.priority"},
                "fields": [
                    {"id": "request", "label": "Request", "type": "short_text", "required": True},
                    {"id": "requester", "label": "Requester", "type": "short_text", "required": True},
                    {"id": "severity", "label": "Severity", "type": "dropdown", "options": ["Normal", "High", "Urgent"]}
                ],
                "automation_chain": ["auto_intake_classify", "auto_intake_task"]
            }
        }
        for form in state.get("forms", []):
            fid = form.get("id", make_id("form"))
            conn.execute(forms.insert().values(id=fid, workspace_id=DEFAULT_WORKSPACE_ID, name=form.get("name", "Form"), description=form.get("description", ""), submissions=int(form.get("submissions", 0)), favorite=bool(form.get("favorite", False)), schema=default_form_schemas.get(fid, {"fields": []})))
        for doc in state.get("docs", []):
            conn.execute(docs.insert().values(id=doc.get("id", make_id("doc")), workspace_id=DEFAULT_WORKSPACE_ID, title=doc.get("title", "Doc"), kind=doc.get("kind", "Doc"), owner=doc.get("owner", "Adrian Francis"), updated=doc.get("updated", "Today"), linked_tasks=int(doc.get("linkedTasks", 0)), content=""))
        for goal in state.get("goals", []):
            conn.execute(goals.insert().values(id=goal.get("id", make_id("g")), workspace_id=DEFAULT_WORKSPACE_ID, name=goal.get("name", "Goal"), owner=goal.get("owner", "Adrian Francis"), progress=int(goal.get("progress", 0)), status=goal.get("status", "On Track")))
        for auto in state.get("automations", []):
            conn.execute(automations.insert().values(id=auto.get("id", make_id("a")), workspace_id=DEFAULT_WORKSPACE_ID, name=auto.get("name", "Automation"), category=auto.get("category", "Projects"), enabled=bool(auto.get("enabled", True)), trigger=auto.get("trigger", "Task updated"), action=auto.get("action", "Notify owner")))
        intake_autos = [
            {"id": "auto_intake_classify", "name": "AI classify new intake", "category": "AI & Automation", "trigger": "Form submitted", "action": "Analyze request, classify department, priority, and duplicate risk"},
            {"id": "auto_intake_task", "name": "Create kickoff task from form", "category": "Automate Projects", "trigger": "Form submitted", "action": "Create mapped task with owner, due date, and tags"},
            {"id": "auto_intake_notify", "name": "Notify project owner on intake", "category": "Automate Scheduling", "trigger": "Intake task created", "action": "Notify owner and add intake comment"},
            {"id": "auto_intake_dashboard", "name": "Update intake dashboard metrics", "category": "Reporting", "trigger": "Submission processed", "action": "Refresh form analytics and dashboard summary"},
        ]
        for auto in intake_autos:
            exists = conn.execute(select(automations.c.id).where(automations.c.id == auto["id"])).first()
            if not exists:
                conn.execute(automations.insert().values(workspace_id=DEFAULT_WORKSPACE_ID, enabled=True, **auto))
        seed_custom_fields(conn)
        log_event(conn, "seed", "workspace", DEFAULT_WORKSPACE_ID, "Seeded normalized v0.8.0 Docs + Knowledge workspace", DEFAULT_OWNER_ID, {"version": APP_VERSION})


def default_doc_content(title: str, kind: str) -> str:
    if "Charter" in title:
        return """# Project Charter

## BLUF
Thing Planner WorkOS is an AI-native project management command center that connects tasks, dashboards, forms, planner blocks, Gantt dependencies, and knowledge.

## Outcomes
- Deliver a production-demo workspace shell.
- Keep every project artifact linked back to tasks.
- Use AI summaries for executive updates and blockers.

## Success Measures
- Dashboard cards can update source work.
- Intake submissions create traceable tasks.
- Gantt dependencies flag schedule risk.
"""
    if "SOP" in title or "Wiki" in title:
        return """# Team SOP Wiki

## Standard workflow
1. Capture requests through Forms.
2. Convert approved requests into tasks and linked docs.
3. Track delivery through List, Board, Calendar, Gantt, and Dashboard views.
4. Review AI risk watch and update blocked tasks daily.

## Working agreements
- Every decision belongs in the Decision Log.
- Every dashboard KPI should drill into source records.
- Critical-path blockers must have an owner and due date.
"""
    if "Decision" in title:
        return """# Decision Log

## Decisions
- Use PostgreSQL as the production data layer with SQLite fallback for demos.
- Keep the UI ClickUp-inspired while using independent product identity and assets.
- Prioritize actionable dashboards before advanced chat features.

## Open items
- Choose final product name.
- Decide whether AI actions execute automatically or require approval.
"""
    return f"# {title}\n\nUse this doc to capture notes, decisions, context, and action items linked to your project work.\n"


def ensure_default_docs_data() -> None:
    """Create v0.8 wiki pages, versions, links, decisions, and doc automations if missing."""
    metadata.create_all(engine)
    with engine.begin() as conn:
        doc_rows = conn.execute(select(docs).where(docs.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        if not doc_rows:
            defaults = [
                ("doc1", "Project Charter", "Project Plan", "Adrian Francis"),
                ("doc2", "Team SOP Wiki", "Wiki", "Mira Chen"),
                ("doc3", "Decision Log", "Decisions", "Adrian Francis"),
            ]
            for doc_id, title, kind, owner in defaults:
                conn.execute(docs.insert().values(
                    id=doc_id, workspace_id=DEFAULT_WORKSPACE_ID, title=title, kind=kind, owner=owner,
                    updated="Today", linked_tasks=0, content=default_doc_content(title, kind),
                ))
            doc_rows = conn.execute(select(docs).where(docs.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()

        for row in doc_rows:
            doc = row._mapping
            content = doc.get("content") or default_doc_content(doc["title"], doc["kind"])
            if not doc.get("content"):
                conn.execute(docs.update().where(docs.c.id == doc["id"]).values(content=content, updated="Today"))
            page_exists = conn.execute(select(doc_pages.c.id).where(doc_pages.c.doc_id == doc["id"])).first()
            if not page_exists:
                root_page_id = f"page_{doc['id']}_root"
                conn.execute(doc_pages.insert().values(
                    id=root_page_id, doc_id=doc["id"], workspace_id=DEFAULT_WORKSPACE_ID, parent_page_id=None,
                    title=doc["title"], page_type="root", content=content, sort_order=0,
                    protected=doc["kind"].lower() in ["wiki", "decisions"], verified=doc["kind"].lower() in ["wiki", "project plan"],
                    created_by=DEFAULT_OWNER_ID, updated_by=DEFAULT_OWNER_ID, created_at=utc_now(), updated_at=utc_now(),
                ))
                conn.execute(doc_versions.insert().values(
                    id=make_id("ver"), doc_id=doc["id"], page_id=root_page_id, workspace_id=DEFAULT_WORKSPACE_ID,
                    version_number=1, title=doc["title"], content=content, created_by=DEFAULT_OWNER_ID, created_at=utc_now(),
                ))

        existing_links = conn.execute(select(func.count()).select_from(doc_task_links).where(doc_task_links.c.workspace_id == DEFAULT_WORKSPACE_ID)).scalar_one()
        if existing_links == 0:
            defaults = [("doc1", "t4", "governs"), ("doc1", "t5", "informs"), ("doc2", "t5", "procedure"), ("doc3", "t2", "decision-source")]
            for doc_id, task_id, relation in defaults:
                task_exists = conn.execute(select(tasks.c.id).where(tasks.c.id == task_id)).first()
                doc_exists = conn.execute(select(docs.c.id).where(docs.c.id == doc_id)).first()
                if task_exists and doc_exists:
                    conn.execute(doc_task_links.insert().values(
                        id=make_id("dtl"), doc_id=doc_id, page_id=f"page_{doc_id}_root", task_id=task_id,
                        workspace_id=DEFAULT_WORKSPACE_ID, relation=relation, created_at=utc_now(),
                    ))
            update_doc_link_counts(conn)

        existing_decisions = conn.execute(select(func.count()).select_from(doc_decisions).where(doc_decisions.c.workspace_id == DEFAULT_WORKSPACE_ID)).scalar_one()
        if existing_decisions == 0:
            decisions = [
                ("Use actionable dashboards", "Dashboard cards must allow users to update source work without switching tools.", "This keeps reports operational instead of read-only."),
                ("Keep traceable AI", "AI-generated summaries should cite source tasks, docs, and activity.", "Traceability improves trust and enables enterprise review."),
                ("Prioritize Docs v0.8", "Docs, wiki pages, decisions, and task links become the knowledge layer for WorkOS.", "The next phase needs shared knowledge connected to execution."),
            ]
            for title, decision, rationale in decisions:
                conn.execute(doc_decisions.insert().values(
                    id=make_id("dec"), doc_id="doc3", workspace_id=DEFAULT_WORKSPACE_ID, title=title,
                    decision=decision, rationale=rationale, owner="Adrian Francis", status="Accepted", created_at=utc_now(),
                ))

        for auto in [
            {"id": "auto_doc_decision", "name": "Decision added to wiki", "category": "Knowledge", "trigger": "Decision captured", "action": "Link decision to source task and notify project owner"},
            {"id": "auto_doc_ai_summary", "name": "AI summarize stale docs", "category": "AI & Automation", "trigger": "Doc updated", "action": "Generate AI summary, action items, and linked task recommendations"},
        ]:
            exists = conn.execute(select(automations.c.id).where(automations.c.id == auto["id"])).first()
            if not exists:
                conn.execute(automations.insert().values(workspace_id=DEFAULT_WORKSPACE_ID, enabled=True, **auto))


def update_doc_link_counts(conn) -> None:
    doc_rows = conn.execute(select(docs.c.id).where(docs.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
    for doc in doc_rows:
        count = conn.execute(select(func.count()).select_from(doc_task_links).where(doc_task_links.c.doc_id == doc.id)).scalar_one()
        conn.execute(docs.update().where(docs.c.id == doc.id).values(linked_tasks=int(count), updated="Today"))


def markdown_excerpt(content: str, words: int = 26) -> str:
    text = " ".join((content or "").replace("#", " ").replace("-", " ").split())
    pieces = text.split()[:words]
    return " ".join(pieces) + ("..." if len(text.split()) > words else "")


def ai_doc_summary(doc: Dict[str, Any], linked_tasks: List[Dict[str, Any]], decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
    content = doc.get("content") or ""
    blocked = [t for t in linked_tasks if t.get("status") == "BLOCKED"]
    action_items = []
    if blocked:
        action_items.append(f"Resolve blocker: {blocked[0]['name']}")
    if "decision" in doc.get("kind", "").lower() or decisions:
        action_items.append("Review open decisions and confirm owners before the next status report")
    if not action_items:
        action_items.append("Link this doc to at least one active task to keep knowledge connected to delivery")
    return {
        "title": doc.get("title"),
        "summary": markdown_excerpt(content, 44) or f"{doc.get('title')} captures shared context for project execution.",
        "linkedTaskCount": len(linked_tasks),
        "decisionCount": len(decisions),
        "risk": "medium" if blocked else "low",
        "actionItems": action_items,
        "sources": [t.get("name") for t in linked_tasks[:4]] + [d.get("title") for d in decisions[:2]],
    }


def serialize_doc_bundle(conn, doc_id: str) -> Dict[str, Any]:
    doc_row = conn.execute(select(docs).where(docs.c.id == doc_id)).first()
    if not doc_row:
        raise HTTPException(status_code=404, detail="Doc not found")
    doc = dict(doc_row._mapping)
    page_rows = conn.execute(select(doc_pages).where(doc_pages.c.doc_id == doc_id).order_by(doc_pages.c.sort_order, doc_pages.c.created_at)).all()
    link_rows = conn.execute(select(doc_task_links, tasks.c.name, tasks.c.status, tasks.c.assignee_id, tasks.c.due).join(tasks, doc_task_links.c.task_id == tasks.c.id).where(doc_task_links.c.doc_id == doc_id)).all()
    decision_rows = conn.execute(select(doc_decisions).where(doc_decisions.c.doc_id == doc_id).order_by(doc_decisions.c.created_at.desc())).all()
    version_rows = conn.execute(select(doc_versions).where(doc_versions.c.doc_id == doc_id).order_by(doc_versions.c.version_number.desc()).limit(5)).all()
    pages = [dict(r._mapping) for r in page_rows]
    linked = []
    for r in link_rows:
        m = r._mapping
        linked.append({"id": m["id"], "taskId": m["task_id"], "taskName": m["name"], "status": m["status"], "assignee": m["assignee_id"], "due": m["due"], "relation": m["relation"]})
    decisions_list = [{"id": r.id, "title": r.title, "decision": r.decision, "rationale": r.rationale, "owner": r.owner, "status": r.status, "createdAt": r.created_at.isoformat()} for r in decision_rows]
    content = doc.get("content") or (pages[0].get("content", "") if pages else "")
    return {
        "id": doc["id"], "title": doc["title"], "kind": doc["kind"], "owner": doc["owner"], "updated": doc["updated"],
        "linkedTasks": doc["linked_tasks"], "content": content,
        "pages": [{"id": p["id"], "title": p["title"], "pageType": p["page_type"], "content": p["content"], "protected": p["protected"], "verified": p["verified"], "updatedAt": p["updated_at"].isoformat()} for p in pages],
        "linkedTaskRecords": linked,
        "decisions": decisions_list,
        "versions": [{"id": r.id, "versionNumber": r.version_number, "title": r.title, "createdAt": r.created_at.isoformat()} for r in version_rows],
        "aiSummary": ai_doc_summary({**doc, "content": content}, [{"name": t["taskName"], "status": t["status"]} for t in linked], decisions_list),
    }

def ensure_default_planner_data() -> None:
    """Create planner preferences and demo meetings if they do not exist."""
    metadata.create_all(engine)
    today = utc_now().date().isoformat()
    with engine.begin() as conn:
        pref_exists = conn.execute(select(planner_preferences.c.workspace_id).where(planner_preferences.c.workspace_id == DEFAULT_WORKSPACE_ID)).first()
        if not pref_exists:
            conn.execute(planner_preferences.insert().values(
                workspace_id=DEFAULT_WORKSPACE_ID, workday_start="08:30", workday_end="17:00",
                lunch_start="12:00", lunch_end="13:00", focus_block_minutes=90,
                auto_schedule_blocked=False, updated_at=utc_now(),
            ))
        auto_exists = conn.execute(select(automations.c.id).where(automations.c.id == "auto_ai_schedule")).first()
        if not auto_exists:
            conn.execute(automations.insert().values(
                id="auto_ai_schedule", workspace_id=DEFAULT_WORKSPACE_ID, name="AI daily schedule",
                category="Automate Scheduling", enabled=True, trigger="Plan my day",
                action="Generate priority-based schedule blocks and planner risk warnings",
            ))
        existing_events = conn.execute(select(func.count()).select_from(calendar_events).where(calendar_events.c.workspace_id == DEFAULT_WORKSPACE_ID)).scalar_one()
        if existing_events == 0:
            defaults = [
                ("ce_standup", "Daily standup", "meeting", "09:00", "09:30", "blue"),
                ("ce_focus", "Protected deep work", "focus", "10:00", "11:30", "purple"),
                ("ce_stakeholder", "Stakeholder sync", "meeting", "13:30", "14:15", "blue"),
                ("ce_triage", "Project risk triage", "meeting", "15:30", "16:00", "orange"),
            ]
            for event_id, title, kind, start_time, end_time, color in defaults:
                conn.execute(calendar_events.insert().values(
                    id=event_id, workspace_id=DEFAULT_WORKSPACE_ID, title=title, kind=kind,
                    start_at=f"{today}T{start_time}:00", end_at=f"{today}T{end_time}:00",
                    source="seed", task_id=None, owner_id=DEFAULT_OWNER_ID, color=color,
                    metadata_json={"demo": True}, created_at=utc_now(), updated_at=utc_now(),
                ))


def ensure_default_report_cards() -> None:
    metadata.create_all(engine)
    with engine.begin() as conn:
        dashboard = conn.execute(select(dashboards.c.id).where(dashboards.c.workspace_id == DEFAULT_WORKSPACE_ID)).first()
        if not dashboard:
            conn.execute(dashboards.insert().values(id="d1", workspace_id=DEFAULT_WORKSPACE_ID, name="Executive PMO Dashboard", is_private=False, favorite=True, config={"cards": []}))
            dashboard_id = "d1"
        else:
            dashboard_id = dashboard.id
        existing_cards = conn.execute(select(func.count()).select_from(report_cards).where(report_cards.c.dashboard_id == dashboard_id)).scalar_one()
        if existing_cards:
            return
        default_cards = [
            ("rc_open", "Open Tasks", "kpi", "open_tasks", {}, {"x": 0, "y": 0, "w": 3, "h": 1}),
            ("rc_blocked", "Blocked Work", "kpi", "blocked_tasks", {}, {"x": 3, "y": 0, "w": 3, "h": 1}),
            ("rc_billable", "Billable Hours", "kpi", "billable_hours", {}, {"x": 6, "y": 0, "w": 3, "h": 1}),
            ("rc_health", "Project Health", "ai", "project_health", {}, {"x": 9, "y": 0, "w": 3, "h": 1}),
            ("rc_status", "Work by Status", "chart", "by_status", {}, {"x": 0, "y": 1, "w": 6, "h": 3}),
            ("rc_assignee", "Team Productivity", "chart", "by_assignee", {}, {"x": 6, "y": 1, "w": 6, "h": 3}),
            ("rc_tasks", "Actionable Work Table", "table", "task_table", {}, {"x": 0, "y": 4, "w": 12, "h": 4}),
        ]
        for cid, title, ctype, metric, filters, layout in default_cards:
            conn.execute(report_cards.insert().values(
                id=cid, dashboard_id=dashboard_id, workspace_id=DEFAULT_WORKSPACE_ID, title=title,
                card_type=ctype, metric=metric, filters=filters, layout=layout, config={},
                created_at=utc_now(), updated_at=utc_now(),
            ))


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


def ensure_list_exists(conn, list_id: str) -> None:
    """Ensure frontend-created project/list IDs have matching normalized rows before task upsert."""
    if not list_id:
        return
    if conn.execute(select(lists.c.id).where(lists.c.id == list_id)).first():
        return
    space_id = "s_frontend"
    folder_id = "f_frontend"
    if not conn.execute(select(spaces.c.id).where(spaces.c.id == space_id)).first():
        conn.execute(spaces.insert().values(id=space_id, workspace_id=DEFAULT_WORKSPACE_ID, name="Frontend-created Space", icon="👥", is_private=False, sort_order=999))
    if not conn.execute(select(folders.c.id).where(folders.c.id == folder_id)).first():
        conn.execute(folders.insert().values(id=folder_id, space_id=space_id, name="Projects", icon="📁", sort_order=999))
    conn.execute(lists.insert().values(id=list_id, folder_id=folder_id, name=list_id, icon="☑", kind="project", sort_order=999))

def upsert_task_row(conn, task: Dict[str, Any], actor: Optional[str] = None, log: bool = True) -> None:
    task_id = task.get("id") or make_id("t")
    list_id = task.get("projectId") or task.get("list_id") or "p1"
    ensure_list_exists(conn, list_id)
    values = {
        "id": task_id,
        "workspace_id": DEFAULT_WORKSPACE_ID,
        "list_id": list_id,
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
        form_submission_rows = conn.execute(select(form_submissions).where(form_submissions.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(form_submissions.c.created_at.desc())).all()
        doc_rows = conn.execute(select(docs).where(docs.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        goal_rows = conn.execute(select(goals).where(goals.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        automation_rows = conn.execute(select(automations).where(automations.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        automation_run_rows = conn.execute(select(automation_runs).where(automation_runs.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(automation_runs.c.created_at.desc()).limit(20)).all()
        custom_field_rows = conn.execute(select(custom_fields).where(custom_fields.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        calendar_event_rows = conn.execute(select(calendar_events).where(calendar_events.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(calendar_events.c.start_at)).all()
        planner_block_rows = conn.execute(select(planner_blocks).where(planner_blocks.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(planner_blocks.c.start_at)).all()
        pref_row = conn.execute(select(planner_preferences).where(planner_preferences.c.workspace_id == DEFAULT_WORKSPACE_ID)).first()
        dependency_rows = conn.execute(select(task_dependencies).where(task_dependencies.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        baseline_rows = conn.execute(select(gantt_baselines).where(gantt_baselines.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(gantt_baselines.c.created_at.desc()).limit(10)).all()
        gantt_alert_rows = conn.execute(select(gantt_risk_alerts).where(gantt_risk_alerts.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(gantt_risk_alerts.c.created_at.desc()).limit(20)).all()
        doc_page_rows = conn.execute(select(doc_pages).where(doc_pages.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(doc_pages.c.sort_order, doc_pages.c.created_at)).all()
        doc_link_rows = conn.execute(select(doc_task_links).where(doc_task_links.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        doc_decision_rows = conn.execute(select(doc_decisions).where(doc_decisions.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()

    comments_by_task: Dict[str, List[Dict[str, Any]]] = {}
    for c in comment_rows:
        cm = c._mapping
        comments_by_task.setdefault(cm["task_id"], []).append({"by": cm["by_name"], "text": cm["text"], "created_at": cm["created_at"].isoformat()})

    doc_pages_by_doc: Dict[str, List[Any]] = {}
    for pr in doc_page_rows:
        doc_pages_by_doc.setdefault(pr.doc_id, []).append(pr)
    doc_links_by_doc: Dict[str, List[Any]] = {}
    for lr in doc_link_rows:
        doc_links_by_doc.setdefault(lr.doc_id, []).append(lr)
    doc_decisions_by_doc: Dict[str, List[Any]] = {}
    for dr in doc_decision_rows:
        doc_decisions_by_doc.setdefault(dr.doc_id, []).append(dr)

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
        "selectedWhiteboard": "wb1",
        "visualTab": "whiteboard",
        "helper": False,
        "aiPromo": False,
        "version": "0.9.3",
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
        "forms": [{"id": r.id, "name": r.name, "description": r.description, "submissions": r.submissions, "favorite": r.favorite, "schema": r.schema or {}} for r in form_rows],
        "formSubmissions": [{"id": r.id, "formId": r.form_id, "requester": r.requester, "department": r.department, "priority": r.priority, "payload": r.payload or {}, "aiAnalysis": r.ai_analysis or {}, "createdTaskId": r.created_task_id, "status": r.status, "createdAt": r.created_at.isoformat()} for r in form_submission_rows],
        "docs": [{
            "id": r.id,
            "title": r.title,
            "kind": r.kind,
            "owner": r.owner,
            "updated": r.updated,
            "linkedTasks": r.linked_tasks,
            "content": r.content or (doc_pages_by_doc.get(r.id, [None])[0].content if doc_pages_by_doc.get(r.id) else ""),
            "pages": [{"id": p.id, "title": p.title, "pageType": p.page_type, "protected": p.protected, "verified": p.verified, "content": p.content} for p in doc_pages_by_doc.get(r.id, [])],
            "decisionCount": len(doc_decisions_by_doc.get(r.id, [])),
            "linkCount": len(doc_links_by_doc.get(r.id, [])),
        } for r in doc_rows],
        "knowledgeStats": {
            "docs": len(doc_rows),
            "pages": len(doc_page_rows),
            "linkedTasks": len(doc_link_rows),
            "decisions": len(doc_decision_rows),
            "verifiedPages": sum(1 for p in doc_page_rows if p.verified),
        },
        "goals": [{"id": r.id, "name": r.name, "owner": r.owner, "progress": r.progress, "status": r.status} for r in goal_rows],
        "automations": [{"id": r.id, "name": r.name, "category": r.category, "enabled": r.enabled, "trigger": r.trigger, "action": r.action} for r in automation_rows],
        "automationRuns": [{"id": r.id, "automationId": r.automation_id, "trigger": r.trigger, "sourceType": r.source_type, "sourceId": r.source_id, "status": r.status, "summary": r.summary, "details": r.details or {}, "createdAt": r.created_at.isoformat()} for r in automation_run_rows],
        "customFields": [{"id": r.id, "name": r.name, "type": r.type, "scope": r.scope, "options": r.options or []} for r in custom_field_rows],
        "calendarEvents": [{"id": r.id, "title": r.title, "kind": r.kind, "startAt": r.start_at, "endAt": r.end_at, "source": r.source, "taskId": r.task_id, "ownerId": r.owner_id, "color": r.color, "metadata": r.metadata_json or {}} for r in calendar_event_rows],
        "plannerBlocks": [{"id": r.id, "taskId": r.task_id, "title": r.title, "ownerId": r.owner_id, "startAt": r.start_at, "endAt": r.end_at, "blockType": r.block_type, "status": r.status, "score": r.score, "reason": r.reason} for r in planner_block_rows],
        "plannerPreferences": dict(pref_row._mapping) if pref_row else {"workspace_id": DEFAULT_WORKSPACE_ID, "workday_start": "08:30", "workday_end": "17:00", "lunch_start": "12:00", "lunch_end": "13:00", "focus_block_minutes": 90, "auto_schedule_blocked": False},
        "taskDependencies": [serialize_dependency(r) for r in dependency_rows],
        "ganttBaselines": [{"id": r.id, "projectId": r.list_id, "name": r.name, "taskSnapshots": r.task_snapshots or [], "createdAt": r.created_at.isoformat()} for r in baseline_rows],
        "ganttRiskAlerts": [{"id": r.id, "projectId": r.list_id, "taskId": r.task_id, "level": r.level, "title": r.title, "recommendation": r.recommendation, "metadata": r.metadata_json or {}, "createdAt": r.created_at.isoformat()} for r in gantt_alert_rows],
        "whiteboards": serialize_whiteboards(),
    }



def sync_whiteboards_from_state(conn, boards: List[Dict[str, Any]], actor: Optional[str] = None) -> None:
    if boards is None:
        return
    conn.execute(delete(mind_map_nodes).where(mind_map_nodes.c.workspace_id == DEFAULT_WORKSPACE_ID))
    conn.execute(delete(canvas_cards).where(canvas_cards.c.workspace_id == DEFAULT_WORKSPACE_ID))
    conn.execute(delete(whiteboard_edges).where(whiteboard_edges.c.workspace_id == DEFAULT_WORKSPACE_ID))
    conn.execute(delete(whiteboard_objects).where(whiteboard_objects.c.workspace_id == DEFAULT_WORKSPACE_ID))
    conn.execute(delete(whiteboards).where(whiteboards.c.workspace_id == DEFAULT_WORKSPACE_ID))
    now = utc_now()
    for board in boards:
        bid = board.get("id") or make_id("wb")
        conn.execute(whiteboards.insert().values(
            id=bid, workspace_id=DEFAULT_WORKSPACE_ID, name=board.get("name", "Whiteboard"), icon=board.get("icon", "✎"),
            owner=board.get("owner", "Adrian Francis"), favorite=bool(board.get("favorite", False)), updated=board.get("updated", "Today"),
            metadata_json=board.get("metadata", {}), created_at=now, updated_at=now,
        ))
        for obj in board.get("objects", []):
            conn.execute(whiteboard_objects.insert().values(
                id=obj.get("id") or make_id("wbo"), whiteboard_id=bid, workspace_id=DEFAULT_WORKSPACE_ID,
                object_type=obj.get("type", obj.get("objectType", "sticky")), text=obj.get("text", ""), color=obj.get("color", "yellow"),
                x=int(obj.get("x", 80)), y=int(obj.get("y", 80)), w=int(obj.get("w", 180)), h=int(obj.get("h", 120)),
                task_id=obj.get("taskId"), doc_id=obj.get("docId"), metadata_json=obj.get("metadata", {}), created_at=now, updated_at=now,
            ))
        for edge in board.get("edges", []):
            conn.execute(whiteboard_edges.insert().values(
                id=edge.get("id") or make_id("edge"), whiteboard_id=bid, workspace_id=DEFAULT_WORKSPACE_ID,
                from_object_id=edge.get("from"), to_object_id=edge.get("to"), label=edge.get("label", "relates"),
                metadata_json=edge.get("metadata", {}), created_at=now,
            ))
        for card in board.get("canvasCards", []):
            conn.execute(canvas_cards.insert().values(
                id=card.get("id") or make_id("cc"), whiteboard_id=bid, workspace_id=DEFAULT_WORKSPACE_ID,
                title=card.get("title", "Canvas Card"), kind=card.get("kind", "Card"), metric=card.get("metric", ""),
                x=int(card.get("x", 80)), y=int(card.get("y", 80)), linked_type=card.get("linkedType", "module"), linked_id=card.get("linkedId", "spaces"),
                config=card.get("config", {}), created_at=now, updated_at=now,
            ))
        mm = board.get("mindMap", {})
        root = mm.get("root", {"id": f"mm_{bid}_root", "label": board.get("name", "Whiteboard"), "kind": "root"})
        conn.execute(mind_map_nodes.insert().values(
            id=root.get("id", f"mm_{bid}_root"), whiteboard_id=bid, workspace_id=DEFAULT_WORKSPACE_ID, parent_node_id=None,
            label=root.get("label", board.get("name", "Whiteboard")), kind=root.get("kind", "root"), linked_type=None, linked_id=None,
            sort_order=0, metadata_json=root.get("metadata", {}), created_at=now, updated_at=now,
        ))
        for idx, node in enumerate(mm.get("nodes", []), start=1):
            conn.execute(mind_map_nodes.insert().values(
                id=node.get("id") or make_id("mm"), whiteboard_id=bid, workspace_id=DEFAULT_WORKSPACE_ID, parent_node_id=node.get("parent"),
                label=node.get("label", "Node"), kind=node.get("kind", "feature"), linked_type=node.get("linkedType"), linked_id=node.get("linkedId"),
                sort_order=idx, metadata_json=node.get("metadata", {}), created_at=now, updated_at=now,
            ))
    log_event(conn, "whiteboards.synced", "workspace", DEFAULT_WORKSPACE_ID, "Synchronized frontend whiteboard state", actor, {"board_count": len(boards)})

def sync_members_from_state(conn, member_state: List[Dict[str, Any]]) -> None:
    if not isinstance(member_state, list):
        return
    for member in member_state:
        user_id = member.get("id") or make_id("u")
        values = {
            "id": user_id,
            "email": "echofoxx@gmail.com" if user_id == DEFAULT_OWNER_ID else f"{user_id}@example.local",
            "display_name": member.get("name") or member.get("display_name") or user_id.title(),
            "initials": member.get("initials") or user_id[:2].upper(),
            "avatar": member.get("avatar") or "purple",
            "title": member.get("role") or member.get("title") or "Member",
            "password_hash": hash_password("thingplanner" if user_id == DEFAULT_OWNER_ID else "demo"),
            "created_at": utc_now(),
        }
        if conn.execute(select(users.c.id).where(users.c.id == user_id)).first():
            conn.execute(users.update().where(users.c.id == user_id).values(display_name=values["display_name"], initials=values["initials"], avatar=values["avatar"], title=values["title"]))
        else:
            conn.execute(users.insert().values(**values))
        if conn.execute(select(workspace_members.c.user_id).where((workspace_members.c.workspace_id == DEFAULT_WORKSPACE_ID) & (workspace_members.c.user_id == user_id))).first():
            conn.execute(workspace_members.update().where((workspace_members.c.workspace_id == DEFAULT_WORKSPACE_ID) & (workspace_members.c.user_id == user_id)).values(role=values["title"], permissions=default_permissions(values["title"])))
        else:
            conn.execute(workspace_members.insert().values(workspace_id=DEFAULT_WORKSPACE_ID, user_id=user_id, role=values["title"], permissions=default_permissions(values["title"]), created_at=utc_now()))


def sync_spaces_from_state(conn, space_state: List[Dict[str, Any]]) -> None:
    if not isinstance(space_state, list):
        return
    for s_order, space in enumerate(space_state):
        sid = space.get("id") or make_id("s")
        if conn.execute(select(spaces.c.id).where(spaces.c.id == sid)).first():
            conn.execute(spaces.update().where(spaces.c.id == sid).values(name=space.get("name", "Space"), icon=space.get("icon", "👥"), sort_order=s_order))
        else:
            conn.execute(spaces.insert().values(id=sid, workspace_id=DEFAULT_WORKSPACE_ID, name=space.get("name", "Space"), icon=space.get("icon", "👥"), is_private=bool(space.get("private", False)), sort_order=s_order))
        for f_order, folder in enumerate(space.get("folders", []) or []):
            fid = folder.get("id") or make_id("f")
            if conn.execute(select(folders.c.id).where(folders.c.id == fid)).first():
                conn.execute(folders.update().where(folders.c.id == fid).values(space_id=sid, name=folder.get("name", "Folder"), icon=folder.get("icon", "📁"), sort_order=f_order))
            else:
                conn.execute(folders.insert().values(id=fid, space_id=sid, name=folder.get("name", "Folder"), icon=folder.get("icon", "📁"), sort_order=f_order))
            for l_order, item in enumerate(folder.get("lists", []) or []):
                lid = item.get("id") or make_id("p")
                if conn.execute(select(lists.c.id).where(lists.c.id == lid)).first():
                    conn.execute(lists.update().where(lists.c.id == lid).values(folder_id=fid, name=item.get("name", "List"), icon=item.get("icon", "☑"), kind=item.get("kind", "project"), sort_order=l_order))
                else:
                    conn.execute(lists.insert().values(id=lid, folder_id=fid, name=item.get("name", "List"), icon=item.get("icon", "☑"), kind=item.get("kind", "project"), sort_order=l_order))


def sync_dashboards_from_state(conn, dashboard_state: List[Dict[str, Any]]) -> None:
    if not isinstance(dashboard_state, list):
        return
    for dash in dashboard_state:
        did = dash.get("id") or make_id("d")
        values = {"workspace_id": DEFAULT_WORKSPACE_ID, "name": dash.get("name", "Dashboard"), "is_private": bool(dash.get("private", False)), "favorite": bool(dash.get("favorite", False)), "config": dash.get("config", {}) or {}}
        if conn.execute(select(dashboards.c.id).where(dashboards.c.id == did)).first():
            conn.execute(dashboards.update().where(dashboards.c.id == did).values(**values))
        else:
            conn.execute(dashboards.insert().values(id=did, **values))


def sync_goals_from_state(conn, goal_state: List[Dict[str, Any]]) -> None:
    if not isinstance(goal_state, list):
        return
    for goal in goal_state:
        gid = goal.get("id") or make_id("g")
        values = {"workspace_id": DEFAULT_WORKSPACE_ID, "name": goal.get("name", "Goal"), "owner": goal.get("owner", "Adrian Francis"), "progress": int(goal.get("progress") or 0), "status": goal.get("status", "On Track")}
        if conn.execute(select(goals.c.id).where(goals.c.id == gid)).first():
            conn.execute(goals.update().where(goals.c.id == gid).values(**values))
        else:
            conn.execute(goals.insert().values(id=gid, **values))


def sync_forms_from_state(conn, form_state: List[Dict[str, Any]], submission_state: List[Dict[str, Any]]) -> None:
    if isinstance(form_state, list):
        for form in form_state:
            fid = form.get("id") or make_id("form")
            values = {"workspace_id": DEFAULT_WORKSPACE_ID, "name": form.get("name", "Form"), "description": form.get("description", ""), "submissions": int(form.get("submissions") or 0), "favorite": bool(form.get("favorite", False)), "schema": form.get("schema", {}) or {}}
            if conn.execute(select(forms.c.id).where(forms.c.id == fid)).first():
                conn.execute(forms.update().where(forms.c.id == fid).values(**values))
            else:
                conn.execute(forms.insert().values(id=fid, **values))
    if isinstance(submission_state, list):
        for sub in submission_state:
            fid = sub.get("formId") or sub.get("form_id") or "form1"
            if not conn.execute(select(forms.c.id).where(forms.c.id == fid)).first():
                conn.execute(forms.insert().values(id=fid, workspace_id=DEFAULT_WORKSPACE_ID, name="Imported Form", description="", submissions=0, favorite=False, schema={}))
            sid = sub.get("id") or make_id("sub")
            values = {"form_id": fid, "workspace_id": DEFAULT_WORKSPACE_ID, "requester": sub.get("requester", "Adrian Francis"), "department": sub.get("department", "Product"), "priority": sub.get("priority", "Normal"), "payload": sub.get("payload", {}) or {}, "ai_analysis": sub.get("aiAnalysis", {}) or sub.get("ai_analysis", {}) or {}, "created_task_id": sub.get("createdTaskId") or sub.get("created_task_id"), "status": sub.get("status", "Processed"), "created_at": parse_or_now(sub.get("createdAt") or sub.get("created_at"))}
            if conn.execute(select(form_submissions.c.id).where(form_submissions.c.id == sid)).first():
                conn.execute(form_submissions.update().where(form_submissions.c.id == sid).values(**values))
            else:
                conn.execute(form_submissions.insert().values(id=sid, **values))


def sync_automations_from_state(conn, automation_state: List[Dict[str, Any]], run_state: List[Dict[str, Any]]) -> None:
    if isinstance(automation_state, list):
        for auto in automation_state:
            aid = auto.get("id") or make_id("auto")
            values = {"workspace_id": DEFAULT_WORKSPACE_ID, "name": auto.get("name", "Automation"), "category": auto.get("category", "Automate Projects"), "trigger": auto.get("trigger", "manual"), "action": auto.get("action", "Record run"), "enabled": bool(auto.get("enabled", True))}
            if conn.execute(select(automations.c.id).where(automations.c.id == aid)).first():
                conn.execute(automations.update().where(automations.c.id == aid).values(**values))
            else:
                conn.execute(automations.insert().values(id=aid, **values))
    if isinstance(run_state, list):
        for run in run_state[:50]:
            rid = run.get("id") or make_id("run")
            aid = run.get("automationId") or run.get("automation_id")
            if aid and not conn.execute(select(automations.c.id).where(automations.c.id == aid)).first():
                conn.execute(automations.insert().values(id=aid, workspace_id=DEFAULT_WORKSPACE_ID, name=aid.replace("_", " ").title(), category="Imported", trigger=run.get("trigger", "manual"), action="Imported from frontend state", enabled=True))
            values = {"automation_id": aid, "workspace_id": DEFAULT_WORKSPACE_ID, "trigger": run.get("trigger", "manual"), "source_type": run.get("sourceType") or run.get("source_type") or "workspace", "source_id": run.get("sourceId") or run.get("source_id") or DEFAULT_WORKSPACE_ID, "status": run.get("status", "success"), "summary": run.get("summary", "Automation run"), "details": run.get("details", {}) or {}, "created_at": parse_or_now(run.get("createdAt") or run.get("created_at"))}
            if conn.execute(select(automation_runs.c.id).where(automation_runs.c.id == rid)).first():
                conn.execute(automation_runs.update().where(automation_runs.c.id == rid).values(**values))
            else:
                conn.execute(automation_runs.insert().values(id=rid, **values))

def apply_state_to_normalized_tables(state: Dict[str, Any], actor: Optional[str] = None) -> None:
    with engine.begin() as conn:
        if "workspace" in state:
            conn.execute(workspaces.update().where(workspaces.c.id == DEFAULT_WORKSPACE_ID).values(name=state["workspace"].get("name", "Workspace"), initials=state["workspace"].get("initials", "W")))
        sync_members_from_state(conn, state.get("members", []))
        sync_spaces_from_state(conn, state.get("spaces", []))
        sync_dashboards_from_state(conn, state.get("dashboards", []))
        sync_goals_from_state(conn, state.get("goals", []))
        sync_forms_from_state(conn, state.get("forms", []), state.get("formSubmissions", []))
        sync_automations_from_state(conn, state.get("automations", []), state.get("automationRuns", []))
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
        if "whiteboards" in state:
            sync_whiteboards_from_state(conn, state.get("whiteboards", []), actor=actor)
        if "notifications" in state:
            conn.execute(delete(notifications).where(notifications.c.workspace_id == DEFAULT_WORKSPACE_ID))
            for n in state.get("notifications", []):
                conn.execute(notifications.insert().values(
                    id=n.get("id", make_id("n")), workspace_id=DEFAULT_WORKSPACE_ID, user_id=DEFAULT_OWNER_ID,
                    type=n.get("type", "info"), title=n.get("title", "Notification"), source=n.get("source", "System"),
                    read=bool(n.get("read", False)), tab=n.get("tab", "Primary"), created_at=utc_now(),
                ))
        log_event(conn, "state.synced", "workspace", DEFAULT_WORKSPACE_ID, "Synchronized frontend state into normalized tables", actor, {"task_count": len(state.get("tasks", []))})



# ---- v0.9 Visual Collaboration helpers ----
def default_whiteboard_payload() -> Dict[str, Any]:
    return {
        "id": "wb1", "name": "Launch Planning Board", "icon": "✎", "owner": "Adrian Francis", "favorite": True, "updated": "Today",
        "objects": [
            {"id": "wbo1", "type": "sticky", "text": "Project idea\n\nAI turns this into a project plan.", "color": "yellow", "x": 72, "y": 86, "w": 180, "h": 126},
            {"id": "wbo2", "type": "sticky", "text": "Dashboard card\n\nLive KPI with task drill-down.", "color": "blue", "x": 330, "y": 164, "w": 184, "h": 126, "taskId": "t4"},
            {"id": "wbo3", "type": "sticky", "text": "Form intake\n\nCentralize requests and trigger workflows.", "color": "pink", "x": 562, "y": 92, "w": 190, "h": 126, "taskId": "t5"},
            {"id": "wbo4", "type": "sticky", "text": "Automation\n\nEscalate blocked work automatically.", "color": "green", "x": 790, "y": 236, "w": 190, "h": 126},
            {"id": "wbo5", "type": "task", "text": "Campaign dashboard wireframe", "color": "purple", "x": 314, "y": 356, "w": 248, "h": 96, "taskId": "t4"},
            {"id": "wbo6", "type": "doc", "text": "Project Charter", "color": "white", "x": 90, "y": 310, "w": 220, "h": 92, "docId": "doc1"},
        ],
        "edges": [
            {"id": "edge1", "from": "wbo1", "to": "wbo2", "label": "plan"},
            {"id": "edge2", "from": "wbo2", "to": "wbo3", "label": "insight"},
            {"id": "edge3", "from": "wbo3", "to": "wbo4", "label": "trigger"},
            {"id": "edge4", "from": "wbo1", "to": "wbo6", "label": "document"},
            {"id": "edge5", "from": "wbo2", "to": "wbo5", "label": "work item"},
        ],
        "canvasCards": [
            {"id": "cc1", "title": "Execution Hub", "kind": "Project", "metric": "8 tasks", "x": 40, "y": 40, "linkedType": "list", "linkedId": "p1"},
            {"id": "cc2", "title": "AI Risk Watch", "kind": "AI Card", "metric": "2 risks", "x": 322, "y": 46, "linkedType": "dashboard", "linkedId": "d1"},
            {"id": "cc3", "title": "Intake Flow", "kind": "Form", "metric": "3 submissions", "x": 606, "y": 48, "linkedType": "form", "linkedId": "form1"},
            {"id": "cc4", "title": "Knowledge Base", "kind": "Docs", "metric": "3 docs", "x": 178, "y": 250, "linkedType": "doc", "linkedId": "doc1"},
            {"id": "cc5", "title": "Critical Path", "kind": "Gantt", "metric": "3 critical tasks", "x": 486, "y": 250, "linkedType": "gantt", "linkedId": "p1"},
        ],
        "mindMap": {
            "root": {"id": "mm-root", "label": "Thing Planner WorkOS", "kind": "root"},
            "nodes": [
                {"id": "mm-tasks", "parent": "mm-root", "label": "Tasks & Projects", "kind": "module", "linkedType": "module", "linkedId": "spaces"},
                {"id": "mm-reports", "parent": "mm-root", "label": "Reports & Dashboards", "kind": "module", "linkedType": "module", "linkedId": "dashboards"},
                {"id": "mm-ai", "parent": "mm-root", "label": "AI Agents", "kind": "module", "linkedType": "module", "linkedId": "ai"},
                {"id": "mm-forms", "parent": "mm-root", "label": "Forms + Intake", "kind": "module", "linkedType": "module", "linkedId": "forms"},
                {"id": "mm-docs", "parent": "mm-root", "label": "Docs + Decisions", "kind": "module", "linkedType": "module", "linkedId": "docs"},
                {"id": "mm-gantt", "parent": "mm-tasks", "label": "Critical Path", "kind": "feature", "linkedType": "view", "linkedId": "gantt"},
                {"id": "mm-board", "parent": "mm-tasks", "label": "Kanban Board", "kind": "feature", "linkedType": "view", "linkedId": "board"},
                {"id": "mm-ai-summary", "parent": "mm-ai", "label": "Status Reports", "kind": "feature", "linkedType": "action", "linkedId": "ai-summary"},
                {"id": "mm-submissions", "parent": "mm-forms", "label": "Task Creation", "kind": "feature", "linkedType": "action", "linkedId": "form-task"},
                {"id": "mm-decisions", "parent": "mm-docs", "label": "Decision Records", "kind": "feature", "linkedType": "action", "linkedId": "decisions"},
            ]
        },
    }


def ensure_default_whiteboard_data() -> None:
    metadata.create_all(engine)
    with engine.begin() as conn:
        existing = conn.execute(select(func.count()).select_from(whiteboards).where(whiteboards.c.workspace_id == DEFAULT_WORKSPACE_ID)).scalar_one()
        if existing:
            return
        seed = default_whiteboard_payload()
        now = utc_now()
        conn.execute(whiteboards.insert().values(
            id=seed["id"], workspace_id=DEFAULT_WORKSPACE_ID, name=seed["name"], icon=seed["icon"], owner=seed["owner"],
            favorite=seed["favorite"], updated=seed["updated"], metadata_json={}, created_at=now, updated_at=now,
        ))
        for obj in seed["objects"]:
            conn.execute(whiteboard_objects.insert().values(
                id=obj["id"], whiteboard_id=seed["id"], workspace_id=DEFAULT_WORKSPACE_ID, object_type=obj.get("type", "sticky"), text=obj.get("text", ""),
                color=obj.get("color", "yellow"), x=int(obj.get("x", 80)), y=int(obj.get("y", 80)), w=int(obj.get("w", 180)), h=int(obj.get("h", 120)),
                task_id=obj.get("taskId"), doc_id=obj.get("docId"), metadata_json=obj.get("metadata", {}), created_at=now, updated_at=now,
            ))
        for edge in seed["edges"]:
            conn.execute(whiteboard_edges.insert().values(
                id=edge["id"], whiteboard_id=seed["id"], workspace_id=DEFAULT_WORKSPACE_ID, from_object_id=edge["from"], to_object_id=edge["to"],
                label=edge.get("label", "relates"), metadata_json={}, created_at=now,
            ))
        for card in seed["canvasCards"]:
            conn.execute(canvas_cards.insert().values(
                id=card["id"], whiteboard_id=seed["id"], workspace_id=DEFAULT_WORKSPACE_ID, title=card["title"], kind=card.get("kind", "Card"),
                metric=card.get("metric", ""), x=int(card.get("x", 80)), y=int(card.get("y", 80)), linked_type=card.get("linkedType", "module"),
                linked_id=card.get("linkedId", "spaces"), config=card.get("config", {}), created_at=now, updated_at=now,
            ))
        root = seed["mindMap"]["root"]
        conn.execute(mind_map_nodes.insert().values(
            id=root["id"], whiteboard_id=seed["id"], workspace_id=DEFAULT_WORKSPACE_ID, parent_node_id=None, label=root["label"], kind=root.get("kind", "root"),
            linked_type=None, linked_id=None, sort_order=0, metadata_json={}, created_at=now, updated_at=now,
        ))
        for idx, node in enumerate(seed["mindMap"].get("nodes", []), start=1):
            conn.execute(mind_map_nodes.insert().values(
                id=node["id"], whiteboard_id=seed["id"], workspace_id=DEFAULT_WORKSPACE_ID, parent_node_id=node.get("parent"), label=node["label"],
                kind=node.get("kind", "module"), linked_type=node.get("linkedType"), linked_id=node.get("linkedId"), sort_order=idx,
                metadata_json={}, created_at=now, updated_at=now,
            ))
        record_automation_run(conn, "auto_visual_seed", "Visual workspace seeded", "whiteboard", seed["id"], "Seeded v0.9 visual collaboration board", {"objects": len(seed["objects"]), "cards": len(seed["canvasCards"])})
        log_event(conn, "whiteboard.seeded", "whiteboard", seed["id"], "Seeded visual collaboration workspace", DEFAULT_OWNER_ID, {})


def serialize_whiteboards(conn=None) -> List[Dict[str, Any]]:
    should_close = conn is None
    context = engine.begin() if should_close else None
    if should_close:
        conn = context.__enter__()
    try:
        wb_rows = conn.execute(select(whiteboards).where(whiteboards.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(whiteboards.c.created_at)).all()
        obj_rows = conn.execute(select(whiteboard_objects).where(whiteboard_objects.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        edge_rows = conn.execute(select(whiteboard_edges).where(whiteboard_edges.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        card_rows = conn.execute(select(canvas_cards).where(canvas_cards.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        node_rows = conn.execute(select(mind_map_nodes).where(mind_map_nodes.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(mind_map_nodes.c.sort_order)).all()
        objects_by_wb: Dict[str, List[Any]] = {}
        edges_by_wb: Dict[str, List[Any]] = {}
        cards_by_wb: Dict[str, List[Any]] = {}
        nodes_by_wb: Dict[str, List[Any]] = {}
        for row in obj_rows: objects_by_wb.setdefault(row.whiteboard_id, []).append(row)
        for row in edge_rows: edges_by_wb.setdefault(row.whiteboard_id, []).append(row)
        for row in card_rows: cards_by_wb.setdefault(row.whiteboard_id, []).append(row)
        for row in node_rows: nodes_by_wb.setdefault(row.whiteboard_id, []).append(row)
        boards: List[Dict[str, Any]] = []
        for wb in wb_rows:
            nodes = nodes_by_wb.get(wb.id, [])
            root = next((n for n in nodes if not n.parent_node_id), None)
            boards.append({
                "id": wb.id, "name": wb.name, "icon": wb.icon, "owner": wb.owner, "favorite": wb.favorite, "updated": wb.updated,
                "objects": [{"id": o.id, "type": o.object_type, "text": o.text, "color": o.color, "x": o.x, "y": o.y, "w": o.w, "h": o.h, "taskId": o.task_id, "docId": o.doc_id, "metadata": o.metadata_json or {}} for o in objects_by_wb.get(wb.id, [])],
                "edges": [{"id": e.id, "from": e.from_object_id, "to": e.to_object_id, "label": e.label, "metadata": e.metadata_json or {}} for e in edges_by_wb.get(wb.id, [])],
                "canvasCards": [{"id": c.id, "title": c.title, "kind": c.kind, "metric": c.metric, "x": c.x, "y": c.y, "linkedType": c.linked_type, "linkedId": c.linked_id, "config": c.config or {}} for c in cards_by_wb.get(wb.id, [])],
                "mindMap": {
                    "root": {"id": root.id if root else "mm-root", "label": root.label if root else wb.name, "kind": root.kind if root else "root"},
                    "nodes": [{"id": n.id, "parent": n.parent_node_id, "label": n.label, "kind": n.kind, "linkedType": n.linked_type, "linkedId": n.linked_id, "metadata": n.metadata_json or {}} for n in nodes if n.parent_node_id],
                },
            })
        return boards
    finally:
        if should_close and context is not None:
            context.__exit__(None, None, None)


def whiteboard_ai_summary(board: Dict[str, Any]) -> Dict[str, Any]:
    objects = board.get("objects", [])
    edges = board.get("edges", [])
    cards = board.get("canvasCards", [])
    linked_tasks = [o for o in objects if o.get("taskId")]
    return {
        "summary": f"{board.get('name', 'Whiteboard')} has {len(objects)} objects, {len(edges)} mapped relationships, {len(cards)} live canvas cards, and {len(linked_tasks)} linked tasks. Convert unlinked ideas into tasks and keep canvas cards tied to dashboards, forms, Gantt, and Docs.",
        "actions": [
            "Convert unlinked sticky notes into tasks or decision records.",
            "Use Canvas cards as a live executive planning board.",
            "Review mind-map branches for missing owners, due dates, or source docs.",
        ],
        "risks": ["Unlinked visual ideas can become stale if not converted into source work."],
        "sourceObjectIds": [o.get("id") for o in objects[:5]],
    }

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
                "report_cards": conn.execute(select(func.count()).select_from(report_cards)).scalar_one(),
                "forms": conn.execute(select(func.count()).select_from(forms)).scalar_one(),
                "form_submissions": conn.execute(select(func.count()).select_from(form_submissions)).scalar_one(),
                "automation_runs": conn.execute(select(func.count()).select_from(automation_runs)).scalar_one(),
                "calendar_events": conn.execute(select(func.count()).select_from(calendar_events)).scalar_one(),
                "planner_blocks": conn.execute(select(func.count()).select_from(planner_blocks)).scalar_one(),
                "task_dependencies": conn.execute(select(func.count()).select_from(task_dependencies)).scalar_one(),
                "gantt_baselines": conn.execute(select(func.count()).select_from(gantt_baselines)).scalar_one(),
                "gantt_risk_alerts": conn.execute(select(func.count()).select_from(gantt_risk_alerts)).scalar_one(),
                "doc_pages": conn.execute(select(func.count()).select_from(doc_pages)).scalar_one(),
                "doc_versions": conn.execute(select(func.count()).select_from(doc_versions)).scalar_one(),
                "doc_task_links": conn.execute(select(func.count()).select_from(doc_task_links)).scalar_one(),
                "doc_decisions": conn.execute(select(func.count()).select_from(doc_decisions)).scalar_one(),
                "whiteboards": conn.execute(select(func.count()).select_from(whiteboards)).scalar_one(),
                "whiteboard_objects": conn.execute(select(func.count()).select_from(whiteboard_objects)).scalar_one(),
                "whiteboard_edges": conn.execute(select(func.count()).select_from(whiteboard_edges)).scalar_one(),
                "canvas_cards": conn.execute(select(func.count()).select_from(canvas_cards)).scalar_one(),
                "mind_map_nodes": conn.execute(select(func.count()).select_from(mind_map_nodes)).scalar_one(),
            }
        db_ok = True
    except SQLAlchemyError:
        db_ok = False
        table_counts = {}
    return {
        "status": "ok" if db_ok else "degraded",
        "version": APP_VERSION,
        "database": engine.dialect.name,
        "schema": "visual-collaboration-v0.9",
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
            "docs", "goals", "automations", "automation_runs", "activity_logs", "sessions", "report_cards", "form_submissions",
            "calendar_events", "planner_blocks", "planner_preferences", "task_dependencies", "gantt_baselines", "gantt_risk_alerts",
            "doc_pages", "doc_versions", "doc_task_links", "doc_decisions",
            "whiteboards", "whiteboard_objects", "whiteboard_edges", "canvas_cards", "mind_map_nodes",
        ],
        "compatibility": "The /api/state endpoint serializes normalized tables into the v0.1-v0.9 frontend state shape. v0.9 adds Whiteboards, Canvas, Mind Maps, visual objects, edges, live canvas cards, and AI visual summaries on top of Docs, Gantt, planner, reporting, forms, automations, and auth.",
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




def analyze_intake(fields: Dict[str, Any]) -> Dict[str, Any]:
    priority = str(fields.get("priority") or "Normal")
    objective = str(fields.get("business_objective") or fields.get("description") or "")
    project_name = str(fields.get("project_name") or fields.get("name") or "New request")
    duplicate_risk = "low"
    if any(word in project_name.lower() for word in ["dashboard", "intake", "automation"]):
        duplicate_risk = "medium"
    risk = "high" if priority == "Urgent" else "medium" if priority == "High" else "low"
    recommended_owner = "mira" if str(fields.get("department") or "").lower() in ["product", "operations"] else "tom"
    return {
        "classification": "Project Intake",
        "risk": risk,
        "duplicate_risk": duplicate_risk,
        "recommended_owner": recommended_owner,
        "summary": f"AI classified '{project_name}' as project intake with {risk} delivery risk.",
        "recommended_next_steps": [
            "Create kickoff task",
            "Confirm owner and desired due date",
            "Add business objective to the project description",
            "Review duplicate risk before project approval",
        ],
        "business_objective_detected": bool(objective.strip()),
    }


def record_automation_run(conn, automation_id: Optional[str], trigger: str, source_type: str, source_id: str, summary: str, details: Optional[dict] = None) -> None:
    """Record an automation/system run without crashing startup if seed data references a new automation id.

    v0.9.1 introduced visual-collaboration automation run history before the related
    automation definitions were seeded. PostgreSQL correctly enforced the FK from
    automation_runs.automation_id -> automations.id, which caused API startup to fail.
    This helper now guarantees the referenced automation exists before writing the run.
    """
    safe_automation_id = automation_id
    if automation_id:
        existing = conn.execute(select(automations.c.id).where(automations.c.id == automation_id)).first()
        if not existing:
            display_name = automation_id.replace("auto_", "").replace("_", " ").title()
            category = "Visual Collaboration" if automation_id.startswith("auto_visual") else "System"
            conn.execute(automations.insert().values(
                id=automation_id,
                workspace_id=DEFAULT_WORKSPACE_ID,
                name=display_name[:255],
                category=category[:128],
                enabled=True,
                trigger=(trigger or "System event")[:255],
                action=(summary or "Record automation activity")[:255],
            ))
    conn.execute(automation_runs.insert().values(
        id=make_id("run"),
        automation_id=safe_automation_id,
        workspace_id=DEFAULT_WORKSPACE_ID,
        trigger=trigger,
        source_type=source_type,
        source_id=source_id,
        status="success",
        summary=summary,
        details=details or {},
        created_at=utc_now(),
    ))


def process_form_submission(conn, form_id: str, fields: Dict[str, Any], actor: str) -> Dict[str, Any]:
    form_row = conn.execute(select(forms).where(forms.c.id == form_id)).first()
    if not form_row:
        raise HTTPException(status_code=404, detail=f"Form {form_id} not found")
    schema = form_row.schema or {}
    ai_analysis = analyze_intake(fields)
    project_name = str(fields.get("project_name") or fields.get("name") or fields.get("request") or "New intake request")
    requester = str(fields.get("requester") or "Adrian Francis")
    department = str(fields.get("department") or "Product")
    priority = str(fields.get("priority") or fields.get("severity") or "Normal")
    target_project_id = schema.get("target_project_id") or "p1"
    task = {
        "id": make_id("t"),
        "projectId": target_project_id,
        "name": f"Intake: {project_name}" if not project_name.lower().startswith("intake:") else project_name,
        "assignee": ai_analysis.get("recommended_owner") or "adrian",
        "due": str(fields.get("desired_due_date") or "2026-07-15"),
        "priority": priority,
        "status": "TO DO",
        "comments": [],
        "estimate": 2 if priority == "Normal" else 4,
        "tracked": 0,
        "billable": False,
        "tags": ["Intake", "AI", department],
        "progress": 0,
        "description": str(fields.get("business_objective") or fields.get("description") or "Created from connected form intake."),
        "start": str(fields.get("desired_due_date") or "2026-07-12"),
        "duration": 2 if priority == "Normal" else 3,
        "critical": priority in ["Urgent", "High"],
    }
    upsert_task_row(conn, task, actor=actor, log=True)
    submission_id = make_id("sub")
    conn.execute(form_submissions.insert().values(
        id=submission_id,
        form_id=form_id,
        workspace_id=DEFAULT_WORKSPACE_ID,
        requester=requester,
        department=department,
        priority=priority,
        payload=fields,
        ai_analysis=ai_analysis,
        created_task_id=task["id"],
        status="Processed",
        created_at=utc_now(),
    ))
    conn.execute(forms.update().where(forms.c.id == form_id).values(submissions=forms.c.submissions + 1))
    conn.execute(task_comments.insert().values(
        id=make_id("c"), task_id=task["id"], by_user_id=actor, by_name="AI Intake Agent",
        text=f"{ai_analysis['summary']} Recommended owner: {ai_analysis['recommended_owner']}. Duplicate risk: {ai_analysis['duplicate_risk']}.", created_at=utc_now(),
    ))
    notification_id = make_id("n")
    conn.execute(notifications.insert().values(
        id=notification_id, workspace_id=DEFAULT_WORKSPACE_ID, user_id=task["assignee"], type="form", title=f"New intake routed: {project_name}",
        source="Forms", read=False, tab="Primary", created_at=utc_now(),
    ))
    chain = schema.get("automation_chain") or ["auto_intake_classify", "auto_intake_task", "auto_intake_notify"]
    for auto_id in chain:
        auto_row = conn.execute(select(automations).where(automations.c.id == auto_id)).first()
        if auto_row and auto_row.enabled:
            record_automation_run(conn, auto_id, auto_row.trigger, "form_submission", submission_id, f"{auto_row.name}: {auto_row.action}", {"task_id": task["id"], "form_id": form_id})
    log_event(conn, "form.submitted", "form", form_id, f"Processed form submission: {project_name}", actor, {"submission_id": submission_id, "task_id": task["id"]})
    return {"submission_id": submission_id, "task": task, "ai_analysis": ai_analysis, "automation_chain": chain}


@app.get("/api/forms")
def api_forms() -> Dict[str, Any]:
    with engine.begin() as conn:
        form_rows = conn.execute(select(forms).where(forms.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
    return {"forms": [{"id": r.id, "name": r.name, "description": r.description, "submissions": r.submissions, "favorite": r.favorite, "schema": r.schema or {}} for r in form_rows]}


@app.get("/api/forms/{form_id}")
def api_form_detail(form_id: str) -> Dict[str, Any]:
    with engine.begin() as conn:
        row = conn.execute(select(forms).where(forms.c.id == form_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Form {form_id} not found")
        submission_count = conn.execute(select(func.count()).select_from(form_submissions).where(form_submissions.c.form_id == form_id)).scalar_one()
    return {"form": {"id": row.id, "name": row.name, "description": row.description, "submissions": submission_count, "favorite": row.favorite, "schema": row.schema or {}}}


@app.put("/api/forms/{form_id}/schema")
def api_update_form_schema(form_id: str, payload: FormSchemaPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        row = conn.execute(select(forms).where(forms.c.id == form_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Form {form_id} not found")
        values = {"schema": payload.form_schema or row.schema or {}}
        if payload.name:
            values["name"] = payload.name
        if payload.description is not None:
            values["description"] = payload.description
        conn.execute(forms.update().where(forms.c.id == form_id).values(**values))
        log_event(conn, "form.schema.updated", "form", form_id, f"Updated form schema: {payload.name or row.name}", actor, {})
    return {"ok": True, "form": api_form_detail(form_id)["form"]}


@app.post("/api/forms/{form_id}/submissions")
def api_submit_form(form_id: str, payload: FormSubmissionPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        result = process_form_submission(conn, form_id, payload.fields, actor)
    return {"ok": True, **result, "state": serialize_state()}


@app.get("/api/forms/{form_id}/submissions")
def api_form_submissions(form_id: str) -> Dict[str, Any]:
    with engine.begin() as conn:
        rows = conn.execute(select(form_submissions).where(form_submissions.c.form_id == form_id).order_by(form_submissions.c.created_at.desc())).all()
    return {"submissions": [{"id": r.id, "formId": r.form_id, "requester": r.requester, "department": r.department, "priority": r.priority, "payload": r.payload or {}, "aiAnalysis": r.ai_analysis or {}, "createdTaskId": r.created_task_id, "status": r.status, "createdAt": r.created_at.isoformat()} for r in rows]}


@app.get("/api/forms/{form_id}/analytics")
def api_form_analytics(form_id: str) -> Dict[str, Any]:
    with engine.begin() as conn:
        rows = conn.execute(select(form_submissions).where(form_submissions.c.form_id == form_id)).all()
    by_department: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}
    duplicate_watch = 0
    for r in rows:
        by_department[r.department] = by_department.get(r.department, 0) + 1
        by_priority[r.priority] = by_priority.get(r.priority, 0) + 1
        if (r.ai_analysis or {}).get("duplicate_risk") in ["medium", "high"]:
            duplicate_watch += 1
    return {"form_id": form_id, "total": len(rows), "by_department": by_department, "by_priority": by_priority, "duplicate_watch": duplicate_watch, "ai_summary": f"{len(rows)} submissions processed; {duplicate_watch} should be reviewed for duplicate or related work."}


@app.get("/api/automations/templates")
def api_automation_templates() -> Dict[str, Any]:
    return {"templates": [
        {"name": "AI classify new intake", "category": "AI & Automation", "trigger": "Form submitted", "action": "Analyze request and recommend owner/priority"},
        {"name": "Create kickoff task", "category": "Automate Projects", "trigger": "Form submitted", "action": "Create task using field mappings"},
        {"name": "Notify project owner", "category": "Automate Scheduling", "trigger": "Intake task created", "action": "Notify assignee and add comment"},
        {"name": "Refresh intake dashboard", "category": "Reporting", "trigger": "Submission processed", "action": "Update form analytics and cards"},
        {"name": "Escalate urgent intake", "category": "Automate Projects", "trigger": "Priority equals Urgent", "action": "Create risk and notify owner"},
    ]}


@app.get("/api/automations")
def api_automations() -> Dict[str, Any]:
    with engine.begin() as conn:
        rows = conn.execute(select(automations).where(automations.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        run_rows = conn.execute(select(automation_runs).where(automation_runs.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(automation_runs.c.created_at.desc()).limit(50)).all()
    return {"automations": [{"id": r.id, "name": r.name, "category": r.category, "enabled": r.enabled, "trigger": r.trigger, "action": r.action} for r in rows], "runs": [{"id": r.id, "automationId": r.automation_id, "trigger": r.trigger, "sourceType": r.source_type, "sourceId": r.source_id, "status": r.status, "summary": r.summary, "details": r.details or {}, "createdAt": r.created_at.isoformat()} for r in run_rows]}


@app.post("/api/automations")
def api_create_automation(payload: AutomationPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    auto = {"id": make_id("a"), "workspace_id": DEFAULT_WORKSPACE_ID, "name": payload.name, "category": payload.category, "enabled": payload.enabled, "trigger": payload.trigger, "action": payload.action}
    with engine.begin() as conn:
        conn.execute(automations.insert().values(**auto))
        log_event(conn, "automation.created", "automation", auto["id"], f"Created automation: {payload.name}", actor, {})
    return {"ok": True, "automation": {k: v for k, v in auto.items() if k != "workspace_id"}}


@app.patch("/api/automations/{automation_id}/toggle")
def api_toggle_automation(automation_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        row = conn.execute(select(automations).where(automations.c.id == automation_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Automation {automation_id} not found")
        enabled = not bool(row.enabled)
        conn.execute(automations.update().where(automations.c.id == automation_id).values(enabled=enabled))
        log_event(conn, "automation.toggled", "automation", automation_id, f"{'Enabled' if enabled else 'Paused'} automation: {row.name}", actor, {})
    return {"ok": True, "automation_id": automation_id, "enabled": enabled, "state": serialize_state()}


@app.post("/api/automations/run")
def api_run_automation(payload: AutomationRunPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        summary = f"Manual automation run for {payload.source_type}:{payload.source_id}"
        record_automation_run(conn, payload.automation_id, payload.trigger, payload.source_type, payload.source_id, summary, payload.details)
        log_event(conn, "automation.run", payload.source_type, payload.source_id, summary, actor, payload.details)
    return {"ok": True, "state": serialize_state()}


@app.post("/api/forms/project-intake")
def api_project_intake(payload: IntakePayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    fields = payload.model_dump()
    fields["project_name"] = payload.project_name
    with engine.begin() as conn:
        result = process_form_submission(conn, "form1", fields, actor)
    return {"ok": True, **result, "state": serialize_state()}




# -----------------------------
# v0.6 Planner + AI Scheduling
# -----------------------------
def parse_iso_datetime(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        dt = datetime.fromisoformat(value + "+00:00")
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def combine_date_time(day: str, time_value: str) -> datetime:
    return datetime.fromisoformat(f"{day}T{time_value}:00").replace(tzinfo=timezone.utc)


def to_iso_minute(dt: datetime) -> str:
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt.replace(second=0, microsecond=0).isoformat(timespec="minutes") + ":00"


def serialize_calendar_event(row: Any) -> Dict[str, Any]:
    return {
        "id": row.id,
        "title": row.title,
        "kind": row.kind,
        "startAt": row.start_at,
        "endAt": row.end_at,
        "source": row.source,
        "taskId": row.task_id,
        "ownerId": row.owner_id,
        "color": row.color,
        "metadata": row.metadata_json or {},
    }


def serialize_planner_block(row: Any) -> Dict[str, Any]:
    return {
        "id": row.id,
        "taskId": row.task_id,
        "title": row.title,
        "ownerId": row.owner_id,
        "startAt": row.start_at,
        "endAt": row.end_at,
        "blockType": row.block_type,
        "status": row.status,
        "score": row.score,
        "reason": row.reason,
    }


def task_priority_score(task_row: Any, plan_day: str) -> float:
    base = {"Urgent": 100, "High": 75, "Normal": 45, "Low": 20}.get(task_row.priority, 35)
    try:
        due = datetime.fromisoformat((task_row.due or plan_day) + "T00:00:00")
        day = datetime.fromisoformat(plan_day + "T00:00:00")
        days_until_due = (due - day).days
        if days_until_due < 0:
            base += 35
        elif days_until_due <= 1:
            base += 25
        elif days_until_due <= 3:
            base += 12
    except Exception:
        base += 0
    if task_row.critical:
        base += 18
    if task_row.status == "BLOCKED":
        base -= 50
    if task_row.progress and task_row.progress > 50:
        base += 5
    return max(base, 0)


def occupied_intervals_for_day(events: List[Any], blocks: List[Any], day: str) -> List[tuple[datetime, datetime]]:
    intervals: List[tuple[datetime, datetime]] = []
    for item in list(events) + list(blocks):
        start_value = getattr(item, "start_at", None)
        end_value = getattr(item, "end_at", None)
        if not start_value or not str(start_value).startswith(day):
            continue
        try:
            intervals.append((parse_iso_datetime(str(start_value)), parse_iso_datetime(str(end_value))))
        except Exception:
            continue
    intervals.sort(key=lambda x: x[0])
    return intervals


def free_intervals(day: str, prefs: Any, occupied: List[tuple[datetime, datetime]]) -> List[tuple[datetime, datetime]]:
    work_start = combine_date_time(day, getattr(prefs, "workday_start", "08:30"))
    work_end = combine_date_time(day, getattr(prefs, "workday_end", "17:00"))
    lunch_start = combine_date_time(day, getattr(prefs, "lunch_start", "12:00"))
    lunch_end = combine_date_time(day, getattr(prefs, "lunch_end", "13:00"))
    intervals = sorted(occupied + [(lunch_start, lunch_end)], key=lambda x: x[0])
    cursor = work_start
    free: List[tuple[datetime, datetime]] = []
    for start, end in intervals:
        if end <= work_start or start >= work_end:
            continue
        start = max(start, work_start)
        end = min(end, work_end)
        if start > cursor:
            free.append((cursor, start))
        if end > cursor:
            cursor = end
    if cursor < work_end:
        free.append((cursor, work_end))
    return [(s, e) for s, e in free if (e - s).total_seconds() >= 30 * 60]


def build_ai_schedule(conn, payload: PlannerSchedulePayload) -> Dict[str, Any]:
    ensure_default_planner_data()
    plan_day = payload.date or utc_now().date().isoformat()
    pref = conn.execute(select(planner_preferences).where(planner_preferences.c.workspace_id == DEFAULT_WORKSPACE_ID)).first()
    if not pref:
        conn.execute(planner_preferences.insert().values(workspace_id=DEFAULT_WORKSPACE_ID, workday_start="08:30", workday_end="17:00", lunch_start="12:00", lunch_end="13:00", focus_block_minutes=90, auto_schedule_blocked=False, updated_at=utc_now()))
        pref = conn.execute(select(planner_preferences).where(planner_preferences.c.workspace_id == DEFAULT_WORKSPACE_ID)).first()
    if payload.regenerate:
        conn.execute(delete(planner_blocks).where(planner_blocks.c.workspace_id == DEFAULT_WORKSPACE_ID).where(planner_blocks.c.block_type == "ai_task").where(planner_blocks.c.start_at.like(f"{plan_day}%")))
    events_rows = conn.execute(select(calendar_events).where(calendar_events.c.workspace_id == DEFAULT_WORKSPACE_ID).where(calendar_events.c.start_at.like(f"{plan_day}%")).order_by(calendar_events.c.start_at)).all()
    existing_blocks = conn.execute(select(planner_blocks).where(planner_blocks.c.workspace_id == DEFAULT_WORKSPACE_ID).where(planner_blocks.c.start_at.like(f"{plan_day}%")).where(planner_blocks.c.block_type != "ai_task").order_by(planner_blocks.c.start_at)).all()
    task_rows = conn.execute(select(tasks).where(tasks.c.workspace_id == DEFAULT_WORKSPACE_ID).where(tasks.c.status != "DONE")).all()
    candidates = []
    for row in task_rows:
        if row.status == "BLOCKED" and not pref.auto_schedule_blocked:
            continue
        candidates.append((task_priority_score(row, plan_day), row))
    candidates.sort(key=lambda x: x[0], reverse=True)
    free = free_intervals(plan_day, pref, occupied_intervals_for_day(events_rows, existing_blocks, plan_day))
    created = []
    cursor_slots = list(free)
    block_minutes = int(getattr(pref, "focus_block_minutes", 90) or 90)
    if payload.regenerate:
        for score, task_row in candidates:
            if not cursor_slots:
                break
            needed = max(30, min(block_minutes, int((task_row.estimate or 1) * 60)))
            for idx, (slot_start, slot_end) in enumerate(list(cursor_slots)):
                available = int((slot_end - slot_start).total_seconds() // 60)
                if available < 30:
                    continue
                duration = min(needed, available)
                end = slot_start + timedelta(minutes=duration)
                reason_bits = [f"priority {task_row.priority}"]
                if task_row.critical:
                    reason_bits.append("critical path")
                if task_row.due:
                    reason_bits.append(f"due {task_row.due}")
                block_id = make_id("pb")
                conn.execute(planner_blocks.insert().values(
                    id=block_id, workspace_id=DEFAULT_WORKSPACE_ID, task_id=task_row.id, title=task_row.name,
                    owner_id=task_row.assignee_id or payload.owner_id, start_at=to_iso_minute(slot_start), end_at=to_iso_minute(end),
                    block_type="ai_task", status="planned", score=float(score), reason="AI scheduled from " + ", ".join(reason_bits),
                    created_at=utc_now(), updated_at=utc_now(),
                ))
                created.append(block_id)
                if (slot_end - end).total_seconds() >= 30 * 60:
                    cursor_slots[idx] = (end, slot_end)
                else:
                    cursor_slots.pop(idx)
                break
    block_rows = conn.execute(select(planner_blocks).where(planner_blocks.c.workspace_id == DEFAULT_WORKSPACE_ID).where(planner_blocks.c.start_at.like(f"{plan_day}%")).order_by(planner_blocks.c.start_at)).all()
    event_rows = conn.execute(select(calendar_events).where(calendar_events.c.workspace_id == DEFAULT_WORKSPACE_ID).where(calendar_events.c.start_at.like(f"{plan_day}%")).order_by(calendar_events.c.start_at)).all()
    risks = []
    overdue_count = 0
    blocked_count = 0
    for _, task_row in candidates:
        if task_row.due and task_row.due < plan_day:
            overdue_count += 1
        if task_row.status == "BLOCKED":
            blocked_count += 1
    if overdue_count:
        risks.append({"level": "high", "title": f"{overdue_count} overdue tasks need attention", "recommendation": "Schedule recovery work or renegotiate due dates."})
    if blocked_count:
        risks.append({"level": "medium", "title": f"{blocked_count} blocked tasks excluded from schedule", "recommendation": "Resolve blockers before AI can schedule execution time."})
    if len(created) < min(3, len(candidates)):
        risks.append({"level": "medium", "title": "Limited free time available", "recommendation": "Add focus blocks or move lower priority meetings."})
    return {
        "date": plan_day,
        "events": [serialize_calendar_event(r) for r in event_rows],
        "blocks": [serialize_planner_block(r) for r in block_rows],
        "risks": risks,
        "metrics": {
            "scheduledBlocks": len(block_rows),
            "aiScheduled": len(created),
            "meetings": len(event_rows),
            "freeSlotsRemaining": len(cursor_slots),
            "candidateTasks": len(candidates),
        },
        "preferences": dict(pref._mapping),
    }


@app.get("/api/planner")
def api_planner(date: Optional[str] = None) -> Dict[str, Any]:
    ensure_default_planner_data()
    plan_day = date or utc_now().date().isoformat()
    with engine.begin() as conn:
        # Build a read-only view without regenerating by setting regenerate False.
        return build_ai_schedule(conn, PlannerSchedulePayload(date=plan_day, regenerate=False))


@app.post("/api/planner/plan-my-day")
def api_plan_my_day(payload: PlannerSchedulePayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        data = build_ai_schedule(conn, payload)
        log_event(conn, "planner.ai_schedule.generated", "workspace", DEFAULT_WORKSPACE_ID, f"AI generated schedule for {data['date']}", actor, data["metrics"])
        record_automation_run(conn, "auto_ai_schedule", "Plan my day", "planner", data["date"], f"Generated {data['metrics']['aiScheduled']} AI schedule blocks", data["metrics"])
    return {"ok": True, **data, "state": serialize_state()}


@app.get("/api/planner/events")
def api_planner_events(date: Optional[str] = None) -> Dict[str, Any]:
    ensure_default_planner_data()
    with engine.begin() as conn:
        query = select(calendar_events).where(calendar_events.c.workspace_id == DEFAULT_WORKSPACE_ID)
        if date:
            query = query.where(calendar_events.c.start_at.like(f"{date}%"))
        rows = conn.execute(query.order_by(calendar_events.c.start_at)).all()
    return {"events": [serialize_calendar_event(r) for r in rows]}


@app.post("/api/planner/events")
def api_create_planner_event(payload: CalendarEventPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    event_id = make_id("ce")
    with engine.begin() as conn:
        conn.execute(calendar_events.insert().values(
            id=event_id, workspace_id=DEFAULT_WORKSPACE_ID, title=payload.title, kind=payload.kind,
            start_at=payload.start_at, end_at=payload.end_at, source=payload.source, task_id=payload.task_id,
            owner_id=payload.owner_id, color=payload.color, metadata_json=payload.metadata,
            created_at=utc_now(), updated_at=utc_now(),
        ))
        log_event(conn, "planner.event.created", "calendar_event", event_id, f"Created planner event: {payload.title}", actor, {})
        row = conn.execute(select(calendar_events).where(calendar_events.c.id == event_id)).first()
    return {"ok": True, "event": serialize_calendar_event(row), "state": serialize_state()}


@app.post("/api/planner/tasks/{task_id}/schedule")
def api_schedule_task(task_id: str, payload: TaskSchedulePayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    start = combine_date_time(payload.date, payload.start_time)
    end = start + timedelta(minutes=payload.duration_minutes)
    with engine.begin() as conn:
        task_row = conn.execute(select(tasks).where(tasks.c.id == task_id)).first()
        if not task_row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        block_id = make_id("pb")
        conn.execute(planner_blocks.insert().values(
            id=block_id, workspace_id=DEFAULT_WORKSPACE_ID, task_id=task_id, title=task_row.name,
            owner_id=payload.owner_id, start_at=to_iso_minute(start), end_at=to_iso_minute(end),
            block_type="task", status="planned", score=task_priority_score(task_row, payload.date), reason=payload.reason,
            created_at=utc_now(), updated_at=utc_now(),
        ))
        conn.execute(tasks.update().where(tasks.c.id == task_id).values(start=payload.date, updated_at=utc_now()))
        log_event(conn, "planner.task.scheduled", "task", task_id, f"Scheduled task: {task_row.name}", actor, {"start": to_iso_minute(start), "end": to_iso_minute(end)})
        block = conn.execute(select(planner_blocks).where(planner_blocks.c.id == block_id)).first()
    return {"ok": True, "block": serialize_planner_block(block), "state": serialize_state()}


@app.post("/api/planner/focus-blocks")
def api_create_focus_block(payload: FocusBlockPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    start = combine_date_time(payload.date, payload.start_time)
    end = start + timedelta(minutes=payload.duration_minutes)
    block_id = make_id("pb")
    with engine.begin() as conn:
        conn.execute(planner_blocks.insert().values(
            id=block_id, workspace_id=DEFAULT_WORKSPACE_ID, task_id=None, title=payload.title,
            owner_id=payload.owner_id, start_at=to_iso_minute(start), end_at=to_iso_minute(end),
            block_type="focus", status="protected", score=0, reason=payload.reason,
            created_at=utc_now(), updated_at=utc_now(),
        ))
        log_event(conn, "planner.focus.created", "planner_block", block_id, f"Created focus block: {payload.title}", actor, {})
        block = conn.execute(select(planner_blocks).where(planner_blocks.c.id == block_id)).first()
    return {"ok": True, "block": serialize_planner_block(block), "state": serialize_state()}


@app.delete("/api/planner/blocks/{block_id}")
def api_delete_planner_block(block_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        row = conn.execute(select(planner_blocks).where(planner_blocks.c.id == block_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Planner block {block_id} not found")
        conn.execute(delete(planner_blocks).where(planner_blocks.c.id == block_id))
        log_event(conn, "planner.block.deleted", "planner_block", block_id, f"Removed planner block: {row.title}", actor, {})
    return {"ok": True, "state": serialize_state()}


def task_matches_filters(task: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    if not filters:
        return True
    if filters.get("projectId") and task.get("projectId") != filters["projectId"]:
        return False
    if filters.get("status") and task.get("status") != filters["status"]:
        return False
    if filters.get("assignee") and task.get("assignee") != filters["assignee"]:
        return False
    if filters.get("priority") and task.get("priority") != filters["priority"]:
        return False
    if filters.get("billable") is not None and bool(task.get("billable")) != bool(filters["billable"]):
        return False
    tag = filters.get("tag")
    if tag and tag not in task.get("tags", []):
        return False
    return True


def compute_report_dataset(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    state = serialize_state()
    members_by_id = {m.get("id"): m for m in state.get("members", [])}
    all_tasks = state.get("tasks", [])
    filtered = [t for t in all_tasks if task_matches_filters(t, filters or {})]
    done = [t for t in filtered if t.get("status") == "DONE"]
    open_tasks = [t for t in filtered if t.get("status") != "DONE"]
    blocked = [t for t in filtered if t.get("status") == "BLOCKED"]
    tracked_hours = sum(float(t.get("tracked") or 0) for t in filtered)
    billable_hours = sum(float(t.get("tracked") or 0) for t in filtered if t.get("billable"))
    estimate_hours = sum(float(t.get("estimate") or 0) for t in filtered)
    by_status: Dict[str, int] = {}
    by_assignee: Dict[str, Dict[str, Any]] = {}
    by_priority: Dict[str, int] = {}
    for task in filtered:
        status_name = task.get("status", "Unknown")
        by_status[status_name] = by_status.get(status_name, 0) + 1
        priority = task.get("priority", "Normal")
        by_priority[priority] = by_priority.get(priority, 0) + 1
        assignee = task.get("assignee", "unassigned")
        member = members_by_id.get(assignee, {"name": assignee, "initials": "?"})
        bucket = by_assignee.setdefault(assignee, {"id": assignee, "name": member.get("name", assignee), "tasks": 0, "done": 0, "tracked": 0.0, "estimate": 0.0})
        bucket["tasks"] += 1
        bucket["tracked"] += float(task.get("tracked") or 0)
        bucket["estimate"] += float(task.get("estimate") or 0)
        if task.get("status") == "DONE":
            bucket["done"] += 1
    health = "At Risk" if blocked or len([t for t in open_tasks if t.get("critical")]) >= 2 else "On Track"
    completion = round((len(done) / len(filtered)) * 100) if filtered else 0
    utilization = round((tracked_hours / estimate_hours) * 100) if estimate_hours else 0
    return {
        "schema": "visual-collaboration-v0.9",
        "generated_at": utc_now().isoformat(),
        "filters": filters or {},
        "summary": {
            "total_tasks": len(filtered),
            "open_tasks": len(open_tasks),
            "completed_tasks": len(done),
            "blocked_tasks": len(blocked),
            "billable_hours": round(billable_hours, 2),
            "tracked_hours": round(tracked_hours, 2),
            "estimate_hours": round(estimate_hours, 2),
            "completion_pct": completion,
            "utilization_pct": utilization,
            "health": health,
        },
        "by_status": by_status,
        "by_assignee": list(by_assignee.values()),
        "by_priority": by_priority,
        "work_table": filtered,
        "blockers": blocked,
        "risks": [t for t in filtered if t.get("status") == "BLOCKED" or (t.get("critical") and t.get("status") != "DONE")],
        "forms": state.get("forms", []),
        "goals": state.get("goals", []),
    }

@app.get("/api/reports/summary")
def api_report_summary(projectId: Optional[str] = None, status_filter: Optional[str] = None, assignee: Optional[str] = None, tag: Optional[str] = None) -> Dict[str, Any]:
    filters = {k: v for k, v in {"projectId": projectId, "status": status_filter, "assignee": assignee, "tag": tag}.items() if v}
    return compute_report_dataset(filters)


@app.get("/api/reports/dashboard")
def api_report_dashboard(dashboard_id: str = "d1", projectId: Optional[str] = None) -> Dict[str, Any]:
    filters = {"projectId": projectId} if projectId else {}
    dataset = compute_report_dataset(filters)
    with engine.begin() as conn:
        dashboard = conn.execute(select(dashboards).where(dashboards.c.id == dashboard_id)).first()
        card_rows = conn.execute(select(report_cards).where(report_cards.c.dashboard_id == dashboard_id).order_by(report_cards.c.created_at)).all()
    cards = [dict(row._mapping) for row in card_rows]
    return {
        "dashboard": {"id": dashboard_id, "name": dashboard.name if dashboard else "Executive PMO Dashboard"},
        "cards": cards,
        "dataset": dataset,
        "editable_actions": ["set_status", "assign", "set_due", "add_comment", "toggle_billable", "create_followup"],
    }


@app.get("/api/reports/drilldown")
def api_report_drilldown(metric: str, projectId: Optional[str] = None) -> Dict[str, Any]:
    filters = {"projectId": projectId} if projectId else {}
    dataset = compute_report_dataset(filters)
    tasks_for_metric = dataset["work_table"]
    if metric == "open_tasks":
        tasks_for_metric = [t for t in tasks_for_metric if t.get("status") != "DONE"]
    elif metric == "blocked_tasks":
        tasks_for_metric = [t for t in tasks_for_metric if t.get("status") == "BLOCKED"]
    elif metric == "billable_hours":
        tasks_for_metric = [t for t in tasks_for_metric if t.get("billable")]
    elif metric.startswith("status:"):
        target = metric.split(":", 1)[1]
        tasks_for_metric = [t for t in tasks_for_metric if t.get("status") == target]
    return {"metric": metric, "count": len(tasks_for_metric), "tasks": tasks_for_metric}


@app.get("/api/reports/cards")
def api_report_cards(dashboard_id: str = "d1") -> Dict[str, Any]:
    with engine.begin() as conn:
        rows = conn.execute(select(report_cards).where(report_cards.c.dashboard_id == dashboard_id).order_by(report_cards.c.created_at)).all()
    return {"cards": [dict(row._mapping) for row in rows]}


@app.post("/api/reports/cards")
def api_create_report_card(payload: ReportCardPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    card = {
        "id": make_id("rc"), "dashboard_id": payload.dashboard_id, "workspace_id": DEFAULT_WORKSPACE_ID,
        "title": payload.title, "card_type": payload.card_type, "metric": payload.metric,
        "filters": payload.filters, "layout": payload.layout, "config": payload.config,
        "created_at": utc_now(), "updated_at": utc_now(),
    }
    with engine.begin() as conn:
        conn.execute(report_cards.insert().values(**card))
        log_event(conn, "report.card.created", "dashboard", payload.dashboard_id, f"Created report card: {payload.title}", actor, {"metric": payload.metric})
    return {"ok": True, "card": {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in card.items()}}


@app.post("/api/reports/actions")
def api_report_action(payload: ReportActionPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        row = conn.execute(select(tasks).where(tasks.c.id == payload.task_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Task {payload.task_id} not found")
        if payload.action == "set_status":
            values = {"status": str(payload.value), "updated_at": utc_now()}
            if payload.value == "DONE":
                values["progress"] = 100
            conn.execute(tasks.update().where(tasks.c.id == payload.task_id).values(**values))
        elif payload.action == "assign":
            conn.execute(tasks.update().where(tasks.c.id == payload.task_id).values(assignee_id=str(payload.value), updated_at=utc_now()))
        elif payload.action == "set_due":
            conn.execute(tasks.update().where(tasks.c.id == payload.task_id).values(due=str(payload.value), updated_at=utc_now()))
        elif payload.action == "toggle_billable":
            conn.execute(tasks.update().where(tasks.c.id == payload.task_id).values(billable=not bool(row.billable), updated_at=utc_now()))
        elif payload.action == "add_comment":
            conn.execute(task_comments.insert().values(id=make_id("c"), task_id=payload.task_id, by_user_id=actor, by_name=current_user["display_name"] if current_user else "Report Action", text=payload.comment or str(payload.value or "Dashboard follow-up"), created_at=utc_now()))
        elif payload.action == "create_followup":
            followup = {
                "id": make_id("t"), "projectId": row.list_id, "name": f"Follow up: {row.name}", "assignee": actor,
                "due": row.due or "2026-07-15", "priority": "High", "status": "TO DO", "comments": [],
                "estimate": 1, "tracked": 0, "billable": bool(row.billable), "tags": ["Follow-up", "Report"],
                "progress": 0, "description": payload.comment or "Created from a report drill-down action.", "start": row.start or row.due or "2026-07-12", "duration": 1, "critical": False,
            }
            upsert_task_row(conn, followup, actor=actor, log=True)
        else:
            raise HTTPException(status_code=400, detail="Unsupported report action")
        log_event(conn, "report.action", "task", payload.task_id, f"Dashboard action {payload.action} applied to task: {row.name}", actor, {"value": payload.value})
    return {"ok": True, "state": serialize_state(), "dataset": compute_report_dataset()}



# v0.7 Gantt + Dependency / Critical Path Engine

def parse_date_only(value: Optional[str]) -> datetime:
    if not value:
        return utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
    text_value = str(value)[:10]
    try:
        return datetime.fromisoformat(text_value).replace(tzinfo=timezone.utc)
    except ValueError:
        return utc_now().replace(hour=0, minute=0, second=0, microsecond=0)


def date_only(value: datetime) -> str:
    return value.date().isoformat()


def task_finish_date(row: Any) -> datetime:
    start = parse_date_only(getattr(row, "start", None) or getattr(row, "due", None))
    duration = max(1, int(getattr(row, "duration", 1) or 1))
    return start + timedelta(days=duration)


def serialize_dependency(row: Any) -> Dict[str, Any]:
    r = row._mapping if hasattr(row, "_mapping") else row
    return {
        "id": r["id"],
        "predecessorId": r["predecessor_task_id"],
        "successorId": r["successor_task_id"],
        "type": r["dependency_type"],
        "lagDays": r["lag_days"],
        "critical": bool(r["critical"]),
        "createdAt": r["created_at"].isoformat() if hasattr(r["created_at"], "isoformat") else str(r["created_at"]),
    }


def ensure_default_gantt_data() -> None:
    """Seed dependency links, a baseline, and an automation for v0.7 Gantt demos."""
    metadata.create_all(engine)
    default_dependencies = [
        ("dep_t1_t4", "t1", "t4", "FS", 0, False),
        ("dep_t2_t5", "t2", "t5", "FS", 1, True),
        ("dep_t4_t5", "t4", "t5", "FS", 0, True),
        ("dep_t5_t3", "t5", "t3", "FS", 0, True),
        ("dep_t7_t8", "t7", "t8", "FS", 0, False),
    ]
    with engine.begin() as conn:
        for dep_id, pred, succ, dep_type, lag, is_critical in default_dependencies:
            exists = conn.execute(select(task_dependencies.c.id).where(task_dependencies.c.id == dep_id)).first()
            if not exists:
                pred_exists = conn.execute(select(tasks.c.id).where(tasks.c.id == pred)).first()
                succ_exists = conn.execute(select(tasks.c.id).where(tasks.c.id == succ)).first()
                if pred_exists and succ_exists:
                    conn.execute(task_dependencies.insert().values(
                        id=dep_id, workspace_id=DEFAULT_WORKSPACE_ID, predecessor_task_id=pred,
                        successor_task_id=succ, dependency_type=dep_type, lag_days=lag,
                        critical=is_critical, created_at=utc_now(), updated_at=utc_now(),
                    ))
        auto_exists = conn.execute(select(automations.c.id).where(automations.c.id == "auto_gantt_delay_watch")).first()
        if not auto_exists:
            conn.execute(automations.insert().values(
                id="auto_gantt_delay_watch", workspace_id=DEFAULT_WORKSPACE_ID,
                name="AI Gantt delay watch", category="Automate Scheduling", enabled=True,
                trigger="Dependency or due date changes", action="Recalculate critical path, flag conflicts, and suggest schedule recovery",
            ))
        for list_id, baseline_id in [("p1", "baseline_p1_v080"), ("p2", "baseline_p2_v080")]:
            exists = conn.execute(select(gantt_baselines.c.id).where(gantt_baselines.c.id == baseline_id)).first()
            if not exists:
                task_rows = conn.execute(select(tasks).where(tasks.c.list_id == list_id).order_by(tasks.c.start, tasks.c.due)).all()
                snapshots = [{"taskId": r.id, "name": r.name, "start": r.start, "due": r.due, "duration": r.duration, "status": r.status} for r in task_rows]
                conn.execute(gantt_baselines.insert().values(
                    id=baseline_id, workspace_id=DEFAULT_WORKSPACE_ID, list_id=list_id,
                    name="Initial v0.7 baseline", task_snapshots=snapshots, created_at=utc_now(),
                ))


def compute_critical_path(task_rows: List[Any], dep_rows: List[Any]) -> List[str]:
    task_by_id = {r.id: r for r in task_rows}
    successors: Dict[str, List[str]] = {tid: [] for tid in task_by_id}
    for dep in dep_rows:
        if dep.predecessor_task_id in task_by_id and dep.successor_task_id in task_by_id:
            successors.setdefault(dep.predecessor_task_id, []).append(dep.successor_task_id)
    memo: Dict[str, tuple] = {}
    visiting: set = set()
    def best_chain(task_id: str):
        if task_id in memo:
            return memo[task_id]
        if task_id in visiting:
            return (0, [task_id])
        visiting.add(task_id)
        row = task_by_id[task_id]
        duration = max(1, int(row.duration or 1))
        best_len = duration
        best_path = [task_id]
        for succ in successors.get(task_id, []):
            succ_len, succ_path = best_chain(succ)
            if duration + succ_len > best_len:
                best_len = duration + succ_len
                best_path = [task_id] + succ_path
        visiting.discard(task_id)
        memo[task_id] = (best_len, best_path)
        return memo[task_id]
    best = (0, [])
    for task_id in task_by_id:
        chain = best_chain(task_id)
        if chain[0] > best[0]:
            best = chain
    explicit = [r.id for r in task_rows if bool(r.critical)]
    return list(dict.fromkeys(best[1] + explicit))


def compute_gantt_dataset(project_id: str = "p1", persist_alerts: bool = False) -> Dict[str, Any]:
    ensure_default_gantt_data()
    with engine.begin() as conn:
        task_rows = conn.execute(select(tasks).where(tasks.c.list_id == project_id).order_by(tasks.c.start, tasks.c.due, tasks.c.name)).all()
        task_ids = [r.id for r in task_rows]
        dep_rows = []
        if task_ids:
            all_deps = conn.execute(select(task_dependencies).where(task_dependencies.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
            dep_rows = [d for d in all_deps if d.predecessor_task_id in task_ids and d.successor_task_id in task_ids]
        baselines = conn.execute(select(gantt_baselines).where(gantt_baselines.c.list_id == project_id).order_by(gantt_baselines.c.created_at.desc())).all()
        critical_path = compute_critical_path(task_rows, dep_rows)
        task_by_id = {r.id: r for r in task_rows}
        earliest = min([parse_date_only(r.start or r.due) for r in task_rows], default=parse_date_only(None))
        latest = max([task_finish_date(r) for r in task_rows], default=earliest + timedelta(days=7))
        today = utc_now().replace(hour=0, minute=0, second=0, microsecond=0)
        risks: List[Dict[str, Any]] = []
        conflict_count = 0
        for dep in dep_rows:
            pred = task_by_id.get(dep.predecessor_task_id)
            succ = task_by_id.get(dep.successor_task_id)
            if pred and succ:
                required_start = task_finish_date(pred) + timedelta(days=int(dep.lag_days or 0))
                actual_start = parse_date_only(succ.start or succ.due)
                if actual_start < required_start and succ.status != "DONE":
                    conflict_count += 1
                    risks.append({
                        "level": "high" if dep.critical or succ.id in critical_path else "medium",
                        "taskId": succ.id,
                        "title": f"Dependency conflict: {succ.name} starts before {pred.name} can finish",
                        "recommendation": f"Move {succ.name} to {date_only(required_start)} or reduce predecessor duration.",
                        "metadata": {"dependencyId": dep.id, "requiredStart": date_only(required_start), "actualStart": date_only(actual_start)},
                    })
        for row in task_rows:
            start = parse_date_only(row.start or row.due)
            finish = task_finish_date(row)
            if row.status == "BLOCKED" and row.id in critical_path:
                risks.append({"level": "high", "taskId": row.id, "title": f"Critical path task is blocked: {row.name}", "recommendation": "Escalate blocker, assign recovery owner, and re-run dependency cascade.", "metadata": {"status": row.status}})
            if row.status != "DONE" and row.due and parse_date_only(row.due) < today:
                risks.append({"level": "high", "taskId": row.id, "title": f"Overdue task threatens schedule: {row.name}", "recommendation": "Update due date, mark blocked, or schedule recovery work in Planner.", "metadata": {"due": row.due}})
            if row.status != "DONE" and row.id in critical_path and row.progress < 50 and (parse_date_only(row.due or date_only(finish)) - today).days <= 3:
                risks.append({"level": "medium", "taskId": row.id, "title": f"Low progress on near-term critical task: {row.name}", "recommendation": "Add focused work block or split remaining work into subtasks.", "metadata": {"progress": row.progress, "due": row.due}})
        if persist_alerts:
            conn.execute(delete(gantt_risk_alerts).where(gantt_risk_alerts.c.list_id == project_id))
            for risk in risks[:20]:
                conn.execute(gantt_risk_alerts.insert().values(
                    id=make_id("gr"), workspace_id=DEFAULT_WORKSPACE_ID, list_id=project_id,
                    task_id=risk.get("taskId"), level=risk.get("level", "medium"),
                    title=risk.get("title", "Schedule risk"), recommendation=risk.get("recommendation", ""),
                    metadata_json=risk.get("metadata", {}), created_at=utc_now(),
                ))
        dependencies_by_task = {tid: {"predecessors": [], "successors": []} for tid in task_ids}
        for dep in dep_rows:
            dependencies_by_task.setdefault(dep.predecessor_task_id, {"predecessors": [], "successors": []})["successors"].append(dep.successor_task_id)
            dependencies_by_task.setdefault(dep.successor_task_id, {"predecessors": [], "successors": []})["predecessors"].append(dep.predecessor_task_id)
        serialized_tasks = []
        total_days = max(1, (latest - earliest).days + 1)
        for row in task_rows:
            start = parse_date_only(row.start or row.due)
            finish = task_finish_date(row)
            serialized_tasks.append({
                "id": row.id, "projectId": row.list_id, "name": row.name, "assignee": row.assignee_id,
                "status": row.status, "priority": row.priority, "start": date_only(start), "due": row.due,
                "end": date_only(finish), "duration": int(row.duration or 1), "progress": int(row.progress or 0),
                "critical": bool(row.critical) or row.id in critical_path,
                "criticalPath": row.id in critical_path,
                "blocked": row.status == "BLOCKED",
                "predecessors": dependencies_by_task.get(row.id, {}).get("predecessors", []),
                "successors": dependencies_by_task.get(row.id, {}).get("successors", []),
                "offsetDays": max(0, (start - earliest).days),
                "widthDays": max(1, (finish - start).days),
                "timelineDays": total_days,
            })
        return {
            "ok": True,
            "projectId": project_id,
            "timeline": {"start": date_only(earliest), "end": date_only(latest), "days": total_days},
            "tasks": serialized_tasks,
            "dependencies": [serialize_dependency(d) for d in dep_rows],
            "criticalPath": critical_path,
            "risks": risks,
            "baselines": [{"id": r.id, "projectId": r.list_id, "name": r.name, "taskSnapshots": r.task_snapshots or [], "createdAt": r.created_at.isoformat()} for r in baselines],
            "metrics": {
                "taskCount": len(task_rows), "dependencyCount": len(dep_rows), "criticalTasks": len(critical_path),
                "riskCount": len(risks), "conflictCount": conflict_count, "endDate": date_only(latest),
                "blockedCritical": len([r for r in task_rows if r.status == "BLOCKED" and r.id in critical_path]),
            },
        }


def cascade_successor_dates(conn, task_id: str, visited: Optional[set] = None) -> int:
    visited = visited or set()
    if task_id in visited:
        return 0
    visited.add(task_id)
    changed = 0
    deps = conn.execute(select(task_dependencies).where(task_dependencies.c.predecessor_task_id == task_id)).all()
    for dep in deps:
        pred = conn.execute(select(tasks).where(tasks.c.id == dep.predecessor_task_id)).first()
        succ = conn.execute(select(tasks).where(tasks.c.id == dep.successor_task_id)).first()
        if not pred or not succ:
            continue
        required_start = task_finish_date(pred) + timedelta(days=int(dep.lag_days or 0))
        actual_start = parse_date_only(succ.start or succ.due)
        if actual_start < required_start:
            duration = max(1, int(succ.duration or 1))
            new_due = required_start + timedelta(days=duration)
            conn.execute(tasks.update().where(tasks.c.id == succ.id).values(start=date_only(required_start), due=date_only(new_due), updated_at=utc_now()))
            changed += 1 + cascade_successor_dates(conn, succ.id, visited)
    return changed


@app.get("/api/gantt")
def api_gantt(project_id: str = "p1", persist_alerts: bool = True) -> Dict[str, Any]:
    return compute_gantt_dataset(project_id, persist_alerts=persist_alerts)


@app.get("/api/gantt/critical-path")
def api_gantt_critical_path(project_id: str = "p1") -> Dict[str, Any]:
    data = compute_gantt_dataset(project_id, persist_alerts=False)
    return {"projectId": project_id, "criticalPath": data["criticalPath"], "tasks": [t for t in data["tasks"] if t["criticalPath"]], "metrics": data["metrics"], "risks": data["risks"]}


@app.post("/api/gantt/dependencies")
def api_create_dependency(payload: GanttDependencyPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    if payload.predecessor_task_id == payload.successor_task_id:
        raise HTTPException(status_code=400, detail="A task cannot depend on itself")
    dep_id = make_id("dep")
    with engine.begin() as conn:
        pred = conn.execute(select(tasks).where(tasks.c.id == payload.predecessor_task_id)).first()
        succ = conn.execute(select(tasks).where(tasks.c.id == payload.successor_task_id)).first()
        if not pred or not succ:
            raise HTTPException(status_code=404, detail="Predecessor or successor task not found")
        existing = conn.execute(select(task_dependencies).where(task_dependencies.c.predecessor_task_id == payload.predecessor_task_id).where(task_dependencies.c.successor_task_id == payload.successor_task_id)).first()
        if existing:
            raise HTTPException(status_code=409, detail="Dependency already exists")
        conn.execute(task_dependencies.insert().values(
            id=dep_id, workspace_id=DEFAULT_WORKSPACE_ID,
            predecessor_task_id=payload.predecessor_task_id, successor_task_id=payload.successor_task_id,
            dependency_type=payload.dependency_type, lag_days=payload.lag_days, critical=payload.critical,
            created_at=utc_now(), updated_at=utc_now(),
        ))
        log_event(conn, "gantt.dependency.created", "task_dependency", dep_id, f"Linked {pred.name} -> {succ.name}", actor, {"type": payload.dependency_type, "lag_days": payload.lag_days})
    return compute_gantt_dataset(pred.list_id, persist_alerts=True)


@app.delete("/api/gantt/dependencies/{dependency_id}")
def api_delete_dependency(dependency_id: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        dep = conn.execute(select(task_dependencies).where(task_dependencies.c.id == dependency_id)).first()
        if not dep:
            raise HTTPException(status_code=404, detail=f"Dependency {dependency_id} not found")
        succ = conn.execute(select(tasks).where(tasks.c.id == dep.successor_task_id)).first()
        project_id = succ.list_id if succ else "p1"
        conn.execute(delete(task_dependencies).where(task_dependencies.c.id == dependency_id))
        log_event(conn, "gantt.dependency.deleted", "task_dependency", dependency_id, "Removed Gantt dependency", actor, {})
    return compute_gantt_dataset(project_id, persist_alerts=True)


@app.post("/api/gantt/tasks/{task_id}/schedule")
def api_gantt_schedule_task(task_id: str, payload: GanttSchedulePayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        row = conn.execute(select(tasks).where(tasks.c.id == task_id)).first()
        if not row:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        duration = int(payload.duration or row.duration or 1)
        start = parse_date_only(payload.start or row.start or row.due)
        due = parse_date_only(payload.due) if payload.due else start + timedelta(days=duration)
        conn.execute(tasks.update().where(tasks.c.id == task_id).values(start=date_only(start), due=date_only(due), duration=duration, updated_at=utc_now()))
        cascaded = cascade_successor_dates(conn, task_id) if payload.cascade else 0
        log_event(conn, "gantt.task.schedule", "task", task_id, f"Gantt schedule updated for task: {row.name}", actor, {"start": date_only(start), "due": date_only(due), "duration": duration, "cascade": payload.cascade, "cascaded": cascaded})
        record_automation_run(conn, "auto_gantt_delay_watch", "Dependency schedule changed", "task", task_id, f"Recalculated Gantt and cascaded {cascaded} dependent task(s)", {"reason": payload.reason})
    return compute_gantt_dataset(row.list_id, persist_alerts=True) | {"state": serialize_state()}


@app.post("/api/gantt/recalculate")
def api_gantt_recalculate(project_id: str = "p1", current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    data = compute_gantt_dataset(project_id, persist_alerts=True)
    with engine.begin() as conn:
        log_event(conn, "gantt.recalculated", "list", project_id, f"Recalculated critical path for {project_id}", actor, data.get("metrics", {}))
        record_automation_run(conn, "auto_gantt_delay_watch", "Manual Gantt recalculation", "list", project_id, f"Found {data['metrics']['riskCount']} schedule risk(s) and {data['metrics']['conflictCount']} dependency conflict(s)", data.get("metrics", {}))
    return data


@app.post("/api/gantt/baselines")
def api_create_gantt_baseline(payload: GanttBaselinePayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        task_rows = conn.execute(select(tasks).where(tasks.c.list_id == payload.project_id).order_by(tasks.c.start, tasks.c.due)).all()
        if not task_rows:
            raise HTTPException(status_code=404, detail=f"Project {payload.project_id} has no tasks")
        baseline_id = make_id("base")
        snapshots = [{"taskId": r.id, "name": r.name, "start": r.start, "due": r.due, "duration": r.duration, "status": r.status, "progress": r.progress} for r in task_rows]
        conn.execute(gantt_baselines.insert().values(id=baseline_id, workspace_id=DEFAULT_WORKSPACE_ID, list_id=payload.project_id, name=payload.name, task_snapshots=snapshots, created_at=utc_now()))
        log_event(conn, "gantt.baseline.created", "gantt_baseline", baseline_id, f"Created baseline {payload.name}", actor, {"project_id": payload.project_id, "tasks": len(snapshots)})
    return compute_gantt_dataset(payload.project_id, persist_alerts=True)


@app.get("/api/docs")
def api_docs() -> Dict[str, Any]:
    ensure_default_docs_data()
    ensure_default_whiteboard_data()
    with engine.begin() as conn:
        rows = conn.execute(select(docs).where(docs.c.workspace_id == DEFAULT_WORKSPACE_ID).order_by(docs.c.title)).all()
        bundles = [serialize_doc_bundle(conn, r.id) for r in rows]
    return {
        "ok": True,
        "docs": bundles,
        "stats": {
            "docs": len(bundles),
            "pages": sum(len(d.get("pages", [])) for d in bundles),
            "linkedTasks": sum(len(d.get("linkedTaskRecords", [])) for d in bundles),
            "decisions": sum(len(d.get("decisions", [])) for d in bundles),
            "verifiedPages": sum(len([p for p in d.get("pages", []) if p.get("verified")]) for d in bundles),
        },
    }


@app.get("/api/docs/{doc_id}")
def api_get_doc(doc_id: str) -> Dict[str, Any]:
    ensure_default_docs_data()
    ensure_default_whiteboard_data()
    with engine.begin() as conn:
        return {"ok": True, "doc": serialize_doc_bundle(conn, doc_id)}


@app.post("/api/docs")
def api_create_doc(payload: DocPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    doc_id = make_id("doc")
    page_id = make_id("page")
    content = payload.content or f"# {payload.title}\n\nCapture notes, decisions, context, and action items here. Link it to tasks to keep knowledge connected to delivery.\n"
    with engine.begin() as conn:
        conn.execute(docs.insert().values(
            id=doc_id, workspace_id=DEFAULT_WORKSPACE_ID, title=payload.title, kind=payload.kind, owner=payload.owner,
            updated="Today", linked_tasks=0, content=content,
        ))
        conn.execute(doc_pages.insert().values(
            id=page_id, doc_id=doc_id, workspace_id=DEFAULT_WORKSPACE_ID, parent_page_id=None, title=payload.title,
            page_type="root", content=content, sort_order=0, protected=payload.protected, verified=payload.verified,
            created_by=actor, updated_by=actor, created_at=utc_now(), updated_at=utc_now(),
        ))
        conn.execute(doc_versions.insert().values(
            id=make_id("ver"), doc_id=doc_id, page_id=page_id, workspace_id=DEFAULT_WORKSPACE_ID,
            version_number=1, title=payload.title, content=content, created_by=actor, created_at=utc_now(),
        ))
        log_event(conn, "doc.created", "doc", doc_id, f"Created doc: {payload.title}", actor, {"kind": payload.kind})
        bundle = serialize_doc_bundle(conn, doc_id)
    return {"ok": True, "doc": bundle, "state": serialize_state()}


@app.patch("/api/docs/{doc_id}")
def api_update_doc(doc_id: str, payload: DocPatchPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        doc_row = conn.execute(select(docs).where(docs.c.id == doc_id)).first()
        if not doc_row:
            raise HTTPException(status_code=404, detail="Doc not found")
        root_page = conn.execute(select(doc_pages).where(doc_pages.c.doc_id == doc_id).order_by(doc_pages.c.sort_order)).first()
        values = {}
        if payload.title is not None:
            values["title"] = payload.title
        if payload.kind is not None:
            values["kind"] = payload.kind
        if payload.content is not None:
            values["content"] = payload.content
        if values:
            values["updated"] = "Today"
            conn.execute(docs.update().where(docs.c.id == doc_id).values(**values))
        if root_page and (payload.title is not None or payload.content is not None or payload.verified is not None or payload.protected is not None):
            page_values = {"updated_by": actor, "updated_at": utc_now()}
            if payload.title is not None:
                page_values["title"] = payload.title
            if payload.content is not None:
                page_values["content"] = payload.content
            if payload.verified is not None:
                page_values["verified"] = payload.verified
            if payload.protected is not None:
                page_values["protected"] = payload.protected
            conn.execute(doc_pages.update().where(doc_pages.c.id == root_page.id).values(**page_values))
            latest_version = conn.execute(select(func.max(doc_versions.c.version_number)).where(doc_versions.c.doc_id == doc_id)).scalar() or 0
            conn.execute(doc_versions.insert().values(
                id=make_id("ver"), doc_id=doc_id, page_id=root_page.id, workspace_id=DEFAULT_WORKSPACE_ID,
                version_number=int(latest_version) + 1, title=payload.title or doc_row.title,
                content=payload.content if payload.content is not None else root_page.content, created_by=actor, created_at=utc_now(),
            ))
        log_event(conn, "doc.updated", "doc", doc_id, f"Updated doc: {payload.title or doc_row.title}", actor, {})
        bundle = serialize_doc_bundle(conn, doc_id)
    return {"ok": True, "doc": bundle, "state": serialize_state()}


@app.post("/api/docs/{doc_id}/links")
def api_link_doc_task(doc_id: str, payload: DocLinkPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        doc = conn.execute(select(docs).where(docs.c.id == doc_id)).first()
        task = conn.execute(select(tasks).where(tasks.c.id == payload.task_id)).first()
        if not doc or not task:
            raise HTTPException(status_code=404, detail="Doc or task not found")
        exists = conn.execute(select(doc_task_links).where(doc_task_links.c.doc_id == doc_id).where(doc_task_links.c.task_id == payload.task_id).where(doc_task_links.c.relation == payload.relation)).first()
        if not exists:
            page = conn.execute(select(doc_pages.c.id).where(doc_pages.c.doc_id == doc_id).order_by(doc_pages.c.sort_order)).first()
            conn.execute(doc_task_links.insert().values(
                id=make_id("dtl"), doc_id=doc_id, page_id=page.id if page else None, task_id=payload.task_id,
                workspace_id=DEFAULT_WORKSPACE_ID, relation=payload.relation, created_at=utc_now(),
            ))
            update_doc_link_counts(conn)
            log_event(conn, "doc.task.linked", "doc", doc_id, f"Linked doc to task: {task.name}", actor, {"task_id": payload.task_id, "relation": payload.relation})
        bundle = serialize_doc_bundle(conn, doc_id)
    return {"ok": True, "doc": bundle, "state": serialize_state()}


@app.post("/api/docs/{doc_id}/decisions")
def api_add_decision(doc_id: str, payload: DecisionPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        doc = conn.execute(select(docs).where(docs.c.id == doc_id)).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Doc not found")
        decision_id = make_id("dec")
        conn.execute(doc_decisions.insert().values(
            id=decision_id, doc_id=doc_id, workspace_id=DEFAULT_WORKSPACE_ID, title=payload.title, decision=payload.decision,
            rationale=payload.rationale, owner=payload.owner, status=payload.status, created_at=utc_now(),
        ))
        record_automation_run(conn, "auto_doc_decision", "Decision captured", "doc", doc_id, f"Captured decision: {payload.title}", {"decision_id": decision_id})
        log_event(conn, "doc.decision.created", "doc_decision", decision_id, f"Captured decision: {payload.title}", actor, {"doc_id": doc_id})
        bundle = serialize_doc_bundle(conn, doc_id)
    return {"ok": True, "doc": bundle, "state": serialize_state()}


@app.post("/api/docs/{doc_id}/ai-summary")
def api_doc_ai_summary(doc_id: str) -> Dict[str, Any]:
    ensure_default_docs_data()
    ensure_default_whiteboard_data()
    with engine.begin() as conn:
        bundle = serialize_doc_bundle(conn, doc_id)
        summary = bundle.get("aiSummary", {})
        record_automation_run(conn, "auto_doc_ai_summary", "Doc AI summary requested", "doc", doc_id, f"Generated AI summary for {bundle.get('title')}", {"risk": summary.get("risk"), "linked_tasks": summary.get("linkedTaskCount")})
    return {"ok": True, "summary": summary, "doc": bundle}


@app.get("/api/knowledge/search")
def api_knowledge_search(q: str = "", kind: str = "all") -> Dict[str, Any]:
    ensure_default_docs_data()
    ensure_default_whiteboard_data()
    query = q.strip().lower()
    results = []
    with engine.begin() as conn:
        rows = conn.execute(select(docs).where(docs.c.workspace_id == DEFAULT_WORKSPACE_ID)).all()
        for r in rows:
            bundle = serialize_doc_bundle(conn, r.id)
            haystack = " ".join([bundle.get("title", ""), bundle.get("kind", ""), bundle.get("content", ""), " ".join(d.get("title", "") + " " + d.get("decision", "") for d in bundle.get("decisions", []))]).lower()
            if kind != "all" and bundle.get("kind", "").lower() != kind.lower():
                continue
            if not query or query in haystack:
                results.append({
                    "id": bundle["id"], "title": bundle["title"], "kind": bundle["kind"], "owner": bundle["owner"],
                    "excerpt": markdown_excerpt(bundle.get("content", ""), 34),
                    "linkedTasks": len(bundle.get("linkedTaskRecords", [])), "decisions": len(bundle.get("decisions", [])),
                    "score": 1.0 if query and query in bundle.get("title", "").lower() else 0.72,
                })
    return {"ok": True, "query": q, "results": results, "count": len(results)}


@app.get("/api/knowledge/hub")
def api_knowledge_hub() -> Dict[str, Any]:
    ensure_default_docs_data()
    ensure_default_whiteboard_data()
    docs_payload = api_docs()
    return {
        "ok": True,
        "stats": docs_payload["stats"],
        "recent": docs_payload["docs"][:5],
        "decisions": [d for doc in docs_payload["docs"] for d in doc.get("decisions", [])][:10],
        "recommendations": [
            "Link every project doc to at least one active task.",
            "Capture decisions as structured records so dashboards and AI can reference them.",
            "Use protected wiki pages for SOPs and verified knowledge articles.",
        ],
    }



@app.get("/api/whiteboards")
def api_whiteboards() -> Dict[str, Any]:
    ensure_default_whiteboard_data()
    boards = serialize_whiteboards()
    return {"ok": True, "whiteboards": boards, "stats": {"boards": len(boards), "objects": sum(len(b.get("objects", [])) for b in boards), "edges": sum(len(b.get("edges", [])) for b in boards), "canvasCards": sum(len(b.get("canvasCards", [])) for b in boards), "mindMapNodes": sum(len(b.get("mindMap", {}).get("nodes", [])) + 1 for b in boards)}}


@app.get("/api/whiteboards/{whiteboard_id}")
def api_whiteboard_detail(whiteboard_id: str) -> Dict[str, Any]:
    ensure_default_whiteboard_data()
    boards = serialize_whiteboards()
    board = next((b for b in boards if b["id"] == whiteboard_id), None)
    if not board:
        raise HTTPException(status_code=404, detail="Whiteboard not found")
    return {"ok": True, "whiteboard": board, "summary": whiteboard_ai_summary(board)}


@app.post("/api/whiteboards")
def api_create_whiteboard(payload: WhiteboardPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    board = {"id": make_id("wb"), "name": payload.name, "icon": payload.icon, "owner": current_user.get("display_name", "Adrian Francis") if current_user else "Adrian Francis", "favorite": payload.favorite, "updated": "Now", "objects": payload.objects, "edges": payload.edges, "canvasCards": payload.canvas_cards, "mindMap": payload.mind_map or {"root": {"id": "root", "label": payload.name, "kind": "root"}, "nodes": []}}
    with engine.begin() as conn:
        existing = serialize_whiteboards(conn)
        sync_whiteboards_from_state(conn, [board] + existing, actor=actor)
        record_automation_run(conn, "auto_visual_board_created", "Whiteboard created", "whiteboard", board["id"], f"Created visual board: {payload.name}", {})
    return {"ok": True, "whiteboard": board, "whiteboards": serialize_whiteboards(), "state": serialize_state()}


@app.post("/api/whiteboards/{whiteboard_id}/objects")
def api_add_whiteboard_object(whiteboard_id: str, payload: WhiteboardObjectPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        board = conn.execute(select(whiteboards).where(whiteboards.c.id == whiteboard_id)).first()
        if not board:
            raise HTTPException(status_code=404, detail="Whiteboard not found")
        oid = make_id("wbo")
        conn.execute(whiteboard_objects.insert().values(
            id=oid, whiteboard_id=whiteboard_id, workspace_id=DEFAULT_WORKSPACE_ID, object_type=payload.object_type, text=payload.text, color=payload.color,
            x=payload.x, y=payload.y, w=payload.w, h=payload.h, task_id=payload.task_id, doc_id=payload.doc_id, metadata_json=payload.metadata,
            created_at=utc_now(), updated_at=utc_now(),
        ))
        conn.execute(whiteboards.update().where(whiteboards.c.id == whiteboard_id).values(updated="Now", updated_at=utc_now()))
        log_event(conn, "whiteboard.object.created", "whiteboard_object", oid, f"Added {payload.object_type} to whiteboard", actor, {"whiteboard_id": whiteboard_id})
    return {"ok": True, "whiteboards": serialize_whiteboards(), "state": serialize_state()}


@app.post("/api/whiteboards/{whiteboard_id}/canvas-cards")
def api_add_canvas_card(whiteboard_id: str, payload: CanvasCardPayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        board = conn.execute(select(whiteboards).where(whiteboards.c.id == whiteboard_id)).first()
        if not board:
            raise HTTPException(status_code=404, detail="Whiteboard not found")
        cid = make_id("cc")
        conn.execute(canvas_cards.insert().values(
            id=cid, whiteboard_id=whiteboard_id, workspace_id=DEFAULT_WORKSPACE_ID, title=payload.title, kind=payload.kind, metric=payload.metric,
            x=payload.x, y=payload.y, linked_type=payload.linked_type, linked_id=payload.linked_id, config=payload.config,
            created_at=utc_now(), updated_at=utc_now(),
        ))
        conn.execute(whiteboards.update().where(whiteboards.c.id == whiteboard_id).values(updated="Now", updated_at=utc_now()))
        log_event(conn, "canvas.card.created", "canvas_card", cid, f"Added canvas card: {payload.title}", actor, {"whiteboard_id": whiteboard_id})
    return {"ok": True, "whiteboards": serialize_whiteboards(), "state": serialize_state()}


@app.post("/api/whiteboards/{whiteboard_id}/mind-map-nodes")
def api_add_mind_map_node(whiteboard_id: str, payload: MindMapNodePayload, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)) -> Dict[str, Any]:
    actor = current_user["id"] if current_user else DEFAULT_OWNER_ID
    with engine.begin() as conn:
        board = conn.execute(select(whiteboards).where(whiteboards.c.id == whiteboard_id)).first()
        if not board:
            raise HTTPException(status_code=404, detail="Whiteboard not found")
        nid = make_id("mm")
        conn.execute(mind_map_nodes.insert().values(
            id=nid, whiteboard_id=whiteboard_id, workspace_id=DEFAULT_WORKSPACE_ID, parent_node_id=payload.parent_node_id,
            label=payload.label, kind=payload.kind, linked_type=payload.linked_type, linked_id=payload.linked_id, sort_order=payload.sort_order,
            metadata_json=payload.metadata, created_at=utc_now(), updated_at=utc_now(),
        ))
        conn.execute(whiteboards.update().where(whiteboards.c.id == whiteboard_id).values(updated="Now", updated_at=utc_now()))
        log_event(conn, "mind_map.node.created", "mind_map_node", nid, f"Added mind map node: {payload.label}", actor, {"whiteboard_id": whiteboard_id})
    return {"ok": True, "whiteboards": serialize_whiteboards(), "state": serialize_state()}


@app.post("/api/whiteboards/{whiteboard_id}/ai-summary")
def api_whiteboard_ai_summary(whiteboard_id: str) -> Dict[str, Any]:
    ensure_default_whiteboard_data()
    boards = serialize_whiteboards()
    board = next((b for b in boards if b["id"] == whiteboard_id), None)
    if not board:
        raise HTTPException(status_code=404, detail="Whiteboard not found")
    summary = whiteboard_ai_summary(board)
    with engine.begin() as conn:
        record_automation_run(conn, "auto_visual_ai_summary", "Whiteboard AI summary", "whiteboard", whiteboard_id, f"Generated visual summary for {board.get('name')}", {"objects": len(board.get("objects", [])), "cards": len(board.get("canvasCards", []))})
    return {"ok": True, "summary": summary, "whiteboard": board, "whiteboards": boards}

@app.post("/api/ai/project-summary")
def api_ai_summary() -> Dict[str, Any]:
    state = serialize_state()
    task_list = state.get("tasks", [])
    blocked = [t for t in task_list if t.get("status") == "BLOCKED"]
    critical_open = [t for t in task_list if t.get("critical") and t.get("status") != "DONE"]
    due_soon = [t for t in task_list if t.get("status") != "DONE"][:4]
    health = "At Risk" if blocked or len(critical_open) >= 2 else "On Track"
    return {
        "summary": "The workspace now includes a v0.9 Visual Collaboration engine with whiteboards, connected objects, canvas cards, mind maps, and AI visual summaries on top of Docs, Gantt, planner, reporting, forms, automations, and the normalized data layer.",
        "health": health,
        "blockers": [t.get("name") for t in blocked],
        "next_actions": [
            "Validate normalized table writes from List and Board views",
            "Move dashboard cards from derived frontend state to report endpoints",
            "Add real role enforcement for workspace members",
            "Use v0.9 visual summaries to convert ideas into tasks, decisions, canvas cards, and linked project risks",
        ],
        "sources": [t.get("name") for t in due_soon],
    }
