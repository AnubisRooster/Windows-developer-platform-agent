"""
SQLAlchemy models and database utilities.
Uses pathlib for paths; DATABASE_URL with SQLite fallback.
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import UTC, datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()
_engine = None
_SessionLocal = None


class Event(Base):
    """Persisted event from EventBus."""

    __tablename__ = "events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), index=True)
    source = Column(String(32))
    event_type = Column(String(128))
    payload = Column(Text)  # JSON string
    timestamp = Column(DateTime, default=lambda: datetime.now(UTC))
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class WorkflowRun(Base):
    """Record of a workflow execution."""

    __tablename__ = "workflow_runs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_name = Column(String(128))
    trigger_event_id = Column(String(64))
    status = Column(String(32))  # running, success, failed
    started_at = Column(DateTime, default=lambda: datetime.now(UTC))
    finished_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)


class CachedSummary(Base):
    """Cached summary (e.g. PR summary, page summary)."""

    __tablename__ = "cached_summaries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(256), unique=True, index=True)
    summary = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ToolOutputModel(Base):
    """Persisted tool output from Orchestrator (DB model; avoids conflict with orchestrator.ToolOutput)."""

    __tablename__ = "tool_outputs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_name = Column(String(128))
    success = Column(Integer)  # 0/1 for SQLite
    result = Column(Text)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))


class ChatSession(Base):
    """A chat session. Each new chat starts a fresh session (clean context window)."""

    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, index=True)
    title = Column(String(256), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    messages = relationship("ChatMessage", back_populates="session", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """A single message in a chat session (long-term memory)."""

    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("chat_sessions.session_id"), index=True)
    role = Column(String(16))  # user, assistant, system
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    session = relationship("ChatSession", back_populates="messages")


def _get_data_dir() -> Path:
    """Data directory for DB and config. CLAW_DATA_DIR or ./data."""
    env_dir = os.environ.get("CLAW_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.cwd() / "data"


def get_engine():
    """Get SQLAlchemy engine from DATABASE_URL or SQLite fallback."""
    global _engine
    if _engine is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            data_dir = _get_data_dir()
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "platform.db"
            url = f"sqlite:///{db_path}"
        kwargs: dict = {"echo": False}
        if url in ("sqlite:///", "sqlite:///:memory:"):
            kwargs["poolclass"] = StaticPool
            kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(url, **kwargs)
        Base.metadata.create_all(_engine)
    return _engine


def get_session() -> Session:
    """Get a new database session."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal()


def persist_tool_output(tool_name: str, success: bool, result: str | dict, error: str | None = None) -> None:
    """Persist a tool output to the database. Use with orchestrator.ToolOutput."""
    session = get_session()
    try:
        result_str = str(result) if not isinstance(result, str) else result
        row = ToolOutputModel(
            tool_name=tool_name,
            success=1 if success else 0,
            result=result_str,
            error=error,
        )
        session.add(row)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
