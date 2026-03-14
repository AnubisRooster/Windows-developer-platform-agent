"""
SQLAlchemy ORM models for the Developer AI Platform.

Includes: Event Store, Workflow Runs, Tool Outputs, Agent State,
Knowledge Graph (nodes + edges), Document Store, and Embedding Store (pgvector).
All models support PostgreSQL (primary) and SQLite (fallback).
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


def _new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


JsonType = JSON


# ---------------------------------------------------------------------------
# Event Store
# ---------------------------------------------------------------------------

class Event(Base):
    """Standardized event from any webhook or internal source."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False, unique=True, default=_new_uuid, index=True)
    source = Column(String(64), nullable=False, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    actor = Column(String(256), nullable=True)
    payload = Column(JsonType)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        Index("ix_events_source_type", "source", "event_type"),
    )


# ---------------------------------------------------------------------------
# Workflow Engine
# ---------------------------------------------------------------------------

class WorkflowRun(Base):
    """Workflow execution records."""

    __tablename__ = "workflow_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String(64), nullable=False, unique=True, default=_new_uuid, index=True)
    workflow_name = Column(String(128), nullable=False, index=True)
    trigger_event_id = Column(String(64), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="pending")
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    result = Column(JsonType)
    actions_log = Column(JsonType)


# ---------------------------------------------------------------------------
# Tool Outputs
# ---------------------------------------------------------------------------

class ToolOutput(Base):
    """Tool execution outputs for conversation context and audit."""

    __tablename__ = "tool_outputs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_name = Column(String(128), nullable=False, index=True)
    input_data = Column(JsonType)
    output_data = Column(JsonType)
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)
    conversation_id = Column(String(128), nullable=True, index=True)
    duration_ms = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Agent State
# ---------------------------------------------------------------------------

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
    tool_calls = Column(JsonType, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class AgentLog(Base):
    """Structured agent logs for all events, workflows, and decisions."""

    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(16), nullable=False, index=True)
    category = Column(String(64), nullable=False, default="general", index=True)
    message = Column(Text)
    module = Column(String(128), nullable=True)
    event_id = Column(String(64), nullable=True, index=True)
    workflow_run_id = Column(String(64), nullable=True, index=True)
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


# ---------------------------------------------------------------------------
# Knowledge Graph
# ---------------------------------------------------------------------------

class KnowledgeNode(Base):
    """Node in the engineering knowledge graph."""

    __tablename__ = "knowledge_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String(64), nullable=False, unique=True, default=_new_uuid, index=True)
    node_type = Column(String(64), nullable=False, index=True)
    name = Column(String(512), nullable=False)
    external_id = Column(String(512), nullable=True, index=True)
    source = Column(String(64), nullable=True, index=True)
    properties = Column(JsonType)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_kn_type_name", "node_type", "name"),
        UniqueConstraint("node_type", "external_id", name="uq_kn_type_extid"),
    )


class KnowledgeEdge(Base):
    """Edge (relationship) in the engineering knowledge graph."""

    __tablename__ = "knowledge_edges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    edge_type = Column(String(64), nullable=False, index=True)
    source_node_id = Column(String(64), ForeignKey("knowledge_nodes.node_id"), nullable=False, index=True)
    target_node_id = Column(String(64), ForeignKey("knowledge_nodes.node_id"), nullable=False, index=True)
    properties = Column(JsonType)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    source_node = relationship("KnowledgeNode", foreign_keys=[source_node_id])
    target_node = relationship("KnowledgeNode", foreign_keys=[target_node_id])

    __table_args__ = (
        Index("ix_ke_src_tgt", "source_node_id", "target_node_id"),
        Index("ix_ke_type_src", "edge_type", "source_node_id"),
        UniqueConstraint("edge_type", "source_node_id", "target_node_id", name="uq_ke_edge"),
    )


# ---------------------------------------------------------------------------
# Document Store (Repository Intelligence)
# ---------------------------------------------------------------------------

class Document(Base):
    """Ingested document from any source (code, PR, Jira, Confluence, Jenkins)."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(String(64), nullable=False, unique=True, default=_new_uuid, index=True)
    source = Column(String(64), nullable=False, index=True)
    doc_type = Column(String(64), nullable=False, index=True)
    title = Column(String(1024), nullable=True)
    content = Column(Text, nullable=True)
    external_id = Column(String(512), nullable=True, index=True)
    external_url = Column(String(1024), nullable=True)
    metadata_ = Column("metadata", JsonType)
    indexed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("ix_docs_source_type", "source", "doc_type"),
        UniqueConstraint("source", "doc_type", "external_id", name="uq_doc_source_ext"),
    )


# ---------------------------------------------------------------------------
# Embedding Store (pgvector)
# ---------------------------------------------------------------------------

class Embedding(Base):
    """Vector embedding for semantic search. Uses pgvector on PostgreSQL, JSON array on SQLite."""

    __tablename__ = "embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False, default=0)
    chunk_text = Column(Text, nullable=True)
    embedding = Column(JsonType, nullable=True)
    model = Column(String(128), nullable=True)
    dimensions = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", foreign_keys=[doc_id], primaryjoin="Embedding.doc_id == Document.doc_id")

    __table_args__ = (
        UniqueConstraint("doc_id", "chunk_index", name="uq_emb_doc_chunk"),
    )


# ---------------------------------------------------------------------------
# Database Initialization
# ---------------------------------------------------------------------------

_engine = None
_SessionLocal = None


def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "").strip()
    if url:
        return url
    base = Path(__file__).resolve().parent.parent.parent
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "platform.db"
    return f"sqlite:///{db_path.as_posix()}"


def get_engine():
    global _engine
    if _engine is None:
        url = _get_database_url()
        kwargs: dict[str, Any] = {
            "echo": os.environ.get("SQL_ECHO", "").lower() == "true",
        }
        if "sqlite" in url:
            kwargs["connect_args"] = {"check_same_thread": False}
            if url in ("sqlite:///", "sqlite:///:memory:", "sqlite://"):
                kwargs["poolclass"] = StaticPool
        else:
            kwargs["pool_pre_ping"] = True
        _engine = create_engine(url, **kwargs)

        if "postgresql" in url:
            try:
                from sqlalchemy import text
                with _engine.connect() as conn:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                    conn.commit()
                logger.info("pgvector extension enabled")
            except Exception:
                logger.debug("pgvector extension not available, using JSON fallback for embeddings")

    return _engine


def get_session() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        Base.metadata.create_all(engine)
        _SessionLocal = sessionmaker(engine, expire_on_commit=False, autoflush=False)
    return _SessionLocal


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Database initialized with all platform tables")
