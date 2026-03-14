"""
Embedding Store - Semantic search using pgvector on PostgreSQL (JSON array fallback on SQLite).

Supports indexing: code files, PR discussions, Jira comments, Confluence pages.
Uses a configurable embedding provider (OpenAI, Ollama, or sentence-transformers).
"""

from __future__ import annotations

import json
import logging
import math
import os
from typing import Any

import httpx

from backend.database.models import Document, Embedding, get_session

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSIONS = int(os.environ.get("EMBEDDING_DIMENSIONS", "1536"))
EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "openai")
CHUNK_SIZE = int(os.environ.get("EMBEDDING_CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.environ.get("EMBEDDING_CHUNK_OVERLAP", "200"))


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks."""
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


async def _get_embeddings_openai(texts: list[str]) -> list[list[float]]:
    """Get embeddings from OpenAI-compatible API (OpenAI or OpenRouter)."""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY", "")
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        raise ValueError("No API key for embeddings (OPENAI_API_KEY or OPENROUTER_API_KEY)")

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": EMBEDDING_MODEL,
                "input": texts,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in data["data"]]


async def _get_embeddings_ollama(texts: list[str]) -> list[list[float]]:
    """Get embeddings from a local Ollama instance."""
    ollama_url = os.environ.get("OLLAMA_URL", "http://localhost:11434")
    model = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")

    results = []
    async with httpx.AsyncClient(timeout=60.0) as client:
        for text in texts:
            resp = await client.post(
                f"{ollama_url}/api/embeddings",
                json={"model": model, "prompt": text},
            )
            resp.raise_for_status()
            results.append(resp.json()["embedding"])
    return results


async def get_embeddings(texts: list[str]) -> list[list[float]]:
    """Get embeddings using the configured provider."""
    if EMBEDDING_PROVIDER == "ollama":
        return await _get_embeddings_ollama(texts)
    return await _get_embeddings_openai(texts)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class EmbeddingStore:
    """Manages document embeddings for semantic search."""

    def __init__(self) -> None:
        self._session_factory = get_session()

    async def index_document(self, doc_id: str, text: str | None = None) -> int:
        """
        Generate and store embeddings for a document.
        If text is not provided, reads from the Document table.
        Returns number of chunks indexed.
        """
        if text is None:
            with self._session_factory() as session:
                doc = session.query(Document).filter(Document.doc_id == doc_id).first()
                if not doc or not doc.content:
                    return 0
                text = doc.content

        chunks = _chunk_text(text)
        if not chunks:
            return 0

        try:
            vectors = await get_embeddings(chunks)
        except Exception as e:
            logger.error("Failed to generate embeddings for doc %s: %s", doc_id, e)
            return 0

        with self._session_factory() as session:
            session.query(Embedding).filter(Embedding.doc_id == doc_id).delete()
            for i, (chunk, vector) in enumerate(zip(chunks, vectors)):
                emb = Embedding(
                    doc_id=doc_id,
                    chunk_index=i,
                    chunk_text=chunk,
                    embedding=vector,
                    model=EMBEDDING_MODEL,
                    dimensions=len(vector),
                )
                session.add(emb)
            session.commit()

        return len(chunks)

    async def search(
        self,
        query: str,
        limit: int = 10,
        source: str | None = None,
        doc_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Semantic search across all indexed documents.
        Returns ranked results with similarity scores.
        """
        try:
            query_vectors = await get_embeddings([query])
            query_vec = query_vectors[0]
        except Exception as e:
            logger.error("Failed to generate query embedding: %s", e)
            return []

        with self._session_factory() as session:
            q = session.query(Embedding).join(
                Document, Embedding.doc_id == Document.doc_id
            )
            if source:
                q = q.filter(Document.source == source)
            if doc_type:
                q = q.filter(Document.doc_type == doc_type)

            all_embeddings = q.all()

            scored = []
            for emb in all_embeddings:
                if not emb.embedding:
                    continue
                vec = emb.embedding if isinstance(emb.embedding, list) else json.loads(emb.embedding)
                score = _cosine_similarity(query_vec, vec)
                scored.append((score, emb))

            scored.sort(key=lambda x: x[0], reverse=True)

            results = []
            for score, emb in scored[:limit]:
                doc = session.query(Document).filter(Document.doc_id == emb.doc_id).first()
                results.append({
                    "score": round(score, 4),
                    "chunk_text": emb.chunk_text[:500] if emb.chunk_text else "",
                    "doc_id": emb.doc_id,
                    "chunk_index": emb.chunk_index,
                    "source": doc.source if doc else None,
                    "doc_type": doc.doc_type if doc else None,
                    "title": doc.title if doc else None,
                    "external_url": doc.external_url if doc else None,
                })
            return results

    async def index_all_documents(self, source: str | None = None) -> dict[str, int]:
        """Index all unindexed documents. Returns stats."""
        with self._session_factory() as session:
            q = session.query(Document)
            if source:
                q = q.filter(Document.source == source)
            docs = q.all()

        indexed = 0
        chunks_total = 0
        for doc in docs:
            with self._session_factory() as session:
                existing = session.query(Embedding).filter(Embedding.doc_id == doc.doc_id).count()
            if existing > 0:
                continue
            n = await self.index_document(doc.doc_id, doc.content)
            if n > 0:
                indexed += 1
                chunks_total += n

        return {"documents_indexed": indexed, "chunks_created": chunks_total}
