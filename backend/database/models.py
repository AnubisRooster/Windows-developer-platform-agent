"""
SQLAlchemy ORM models for the Windows Developer Platform Agent backend.

All models support PostgreSQL and SQLite. Uses pathlib where appropriate.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


# Use JSON for cross-database compatibility (SQLite + PostgreSQL)
JsonType = JSON


class Event(Base):
    """Incoming webhook and internal events."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String(64), nullable=False, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    payload = Column(JsonType)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed = Column(Boolean, default=False, nullable=False)


class WorkflowRun(Base):
    """Workflow execution records."""

    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_name = Column(String(128), nullable=False, index=True)
    trigger_event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    result = Column(JsonType)


class ToolOutput(Base):
    """Tool execution outputs for conversation context."""

    __tablename__ = "tool_outputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_name = Column(String(128), nullable=False, index=True)
    input_data = Column(JsonType)
    output_data = Column(JsonType)
    conversation_id = Column(String(128), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class AgentMemory(Base):
    """Persistent key-value memory for the agent."""

    __tablename__ = "agent_memory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(256), nullable=False, unique=True, index=True)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgentConversation(Base):
    """Conversation messages for persistence and context."""

    __tablename__ = "agent_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(128), nullable=False, index=True)
    role = Column(String(32), nullable=False)
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class AgentLog(Base):
    """Structured agent logs."""

    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(16), nullable=False, index=True)
    message = Column(Text)
    module = Column(String(128), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    meta = Column(JsonType)


class CachedSummary(Base):
    """Cache for summarized content."""

    __tablename__ = "cached_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(64), nullable=False, index=True)
    source_id = Column(String(256), nullable=False, index=True)
    summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    __table_args__ = (Index("ix_cached_summaries_source", "source_type", "source_id"),)


def _get_database_url() -> str:
    """Get database URL from env with SQLite fallback."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    # Default: SQLite in project data dir
    base = Path(__file__).resolve().parent.parent.parent
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "agent.db"
    return f"sqlite:///{db_path.as_posix()}"


_engine = None
_SessionLocal = None


def get_engine():
    """Get or create SQLAlchemy engine."""
    global _engine
    if _engine is None:
        url = _get_database_url()
        _engine = create_engine(
            url,
            echo=os.environ.get("SQL_ECHO", "").lower() == "true",
            connect_args={"check_same_thread": False} if "sqlite" in url else {},
        )
    return _engine


def get_session() -> sessionmaker[Session]:
    """Get session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        Base.metadata.create_all(engine)
        _SessionLocal = sessionmaker(engine, expire_on_commit=False, autoflush=False)
    return _SessionLocal


def init_db() -> None:
    """Initialize database and create tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Database initialized")
