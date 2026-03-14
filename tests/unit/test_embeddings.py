"""Unit tests for the Embedding Store (in-memory cosine similarity)."""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _sqlite_in_memory(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///")
    import backend.database.models as db
    db._engine = None
    db._SessionLocal = None
    yield
    db._engine = None
    db._SessionLocal = None


class TestChunking:
    def test_chunk_text_short(self):
        from backend.knowledge.embeddings import _chunk_text
        chunks = _chunk_text("hello world", chunk_size=100)
        assert chunks == ["hello world"]

    def test_chunk_text_splits(self):
        from backend.knowledge.embeddings import _chunk_text
        text = "a" * 300
        chunks = _chunk_text(text, chunk_size=100, overlap=20)
        assert len(chunks) == 4
        assert all(len(c) <= 100 for c in chunks)

    def test_chunk_text_empty(self):
        from backend.knowledge.embeddings import _chunk_text
        assert _chunk_text("") == []
        assert _chunk_text(None) == []


class TestCosineSimilarity:
    def test_identical_vectors(self):
        from backend.knowledge.embeddings import _cosine_similarity
        assert _cosine_similarity([1, 0, 0], [1, 0, 0]) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        from backend.knowledge.embeddings import _cosine_similarity
        assert _cosine_similarity([1, 0], [0, 1]) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        from backend.knowledge.embeddings import _cosine_similarity
        assert _cosine_similarity([1, 0], [-1, 0]) == pytest.approx(-1.0)

    def test_zero_vector(self):
        from backend.knowledge.embeddings import _cosine_similarity
        assert _cosine_similarity([0, 0], [1, 1]) == 0.0


class TestEmbeddingStore:
    def test_index_stores_embeddings(self):
        from unittest.mock import AsyncMock, patch
        from backend.database.models import Document, Embedding, get_session, init_db
        from backend.knowledge.embeddings import EmbeddingStore

        init_db()
        Session = get_session()
        with Session() as session:
            doc = Document(source="test", doc_type="code", title="test.py", content="print('hello world')", external_id="test.py")
            session.add(doc)
            session.commit()
            doc_id = doc.doc_id

        store = EmbeddingStore()
        mock_vectors = [[0.1, 0.2, 0.3]]

        async def run():
            with patch("backend.knowledge.embeddings.get_embeddings", return_value=mock_vectors):
                n = await store.index_document(doc_id, "print('hello world')")
                assert n == 1

        import asyncio
        asyncio.run(run())

        with Session() as session:
            embs = session.query(Embedding).filter(Embedding.doc_id == doc_id).all()
            assert len(embs) == 1
            assert embs[0].embedding == [0.1, 0.2, 0.3]

    def test_search_returns_ranked_results(self):
        from unittest.mock import patch
        from backend.database.models import Document, Embedding, get_session, init_db
        from backend.knowledge.embeddings import EmbeddingStore

        init_db()
        Session = get_session()

        with Session() as session:
            doc1 = Document(source="test", doc_type="code", title="auth.py", content="auth code", external_id="auth.py")
            doc2 = Document(source="test", doc_type="code", title="db.py", content="database code", external_id="db.py")
            session.add_all([doc1, doc2])
            session.commit()
            d1_id, d2_id = doc1.doc_id, doc2.doc_id

        with Session() as session:
            session.add(Embedding(doc_id=d1_id, chunk_index=0, chunk_text="auth code", embedding=[1.0, 0.0, 0.0]))
            session.add(Embedding(doc_id=d2_id, chunk_index=0, chunk_text="db code", embedding=[0.0, 1.0, 0.0]))
            session.commit()

        store = EmbeddingStore()

        async def run():
            with patch("backend.knowledge.embeddings.get_embeddings", return_value=[[0.9, 0.1, 0.0]]):
                results = await store.search("authentication")
                assert len(results) == 2
                assert results[0]["title"] == "auth.py"  # closer to [1,0,0]
                assert results[0]["score"] > results[1]["score"]

        import asyncio
        asyncio.run(run())
