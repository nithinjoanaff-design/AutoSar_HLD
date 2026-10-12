"""
test_vector_store.py
--------------------
Tests for FAISS index construction, save/load, and similarity search.
Uses mock embedder – no internet/model download required.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chunker import TextChunk
from src.embeddings import EmbeddingModel, MockEmbedder
from src.vector_store import VectorStore


def make_chunk(text: str, doc: str = "test.pdf", page: int = 1, idx: int = 0) -> TextChunk:
    return TextChunk(
        chunk_id=f"{doc}_p{page}_c{idx}",
        doc_name=doc,
        page_number=page,
        text=text,
        char_start=0,
        char_end=len(text),
    )


SAMPLE_CHUNKS = [
    make_chunk("The LightingManager SWC controls exterior lighting via ExteriorLightPort.", doc="hld.pdf", page=1, idx=0),
    make_chunk("DoorLockController depends on KeyFobSignalReceiver for authentication.", doc="hld.pdf", page=2, idx=0),
    make_chunk("WindowController implements anti-pinch detection using motor current.", doc="hld.pdf", page=3, idx=0),
    make_chunk("The RTE maps ports to CAN bus signals and the virtual function bus VFB.", doc="hld.pdf", page=4, idx=0),
    make_chunk("ClimateControlModule communicates with TemperatureSensor via SPI.", doc="hld.pdf", page=5, idx=0),
]


class TestEmbeddingModel:

    def test_mock_embedder_dimension(self):
        model = EmbeddingModel(use_mock=True)
        assert model.dimension == 384

    def test_mock_embedder_output_shape(self):
        model = EmbeddingModel(use_mock=True)
        vecs = model.encode(["hello world", "AUTOSAR SWC"])
        assert vecs.shape == (2, 384)

    def test_mock_embedder_deterministic(self):
        model = EmbeddingModel(use_mock=True)
        v1 = model.encode(["deterministic text"])
        v2 = model.encode(["deterministic text"])
        np.testing.assert_array_equal(v1, v2)

    def test_mock_embedder_different_texts_differ(self):
        model = EmbeddingModel(use_mock=True)
        v1 = model.encode(["LightingManager"])
        v2 = model.encode(["DoorLockController"])
        assert not np.allclose(v1, v2)

    def test_mock_embedder_empty_input(self):
        model = EmbeddingModel(use_mock=True)
        result = model.encode([])
        assert result.shape[0] == 0

    def test_is_mock_flag(self):
        model = EmbeddingModel(use_mock=True)
        assert model.is_mock is True


class TestVectorStore:

    def test_build_index_creates_ready_store(self, mock_vector_store):
        assert mock_vector_store.is_ready

    def test_chunk_count_correct(self, mock_vector_store, text_chunks):
        assert mock_vector_store.chunk_count == len(text_chunks)

    def test_indexed_documents_populated(self, mock_vector_store):
        assert len(mock_vector_store.indexed_documents) > 0

    def test_search_returns_results(self, mock_vector_store):
        results = mock_vector_store.search("lighting component", top_k=3)
        assert len(results) > 0

    def test_search_result_has_required_keys(self, mock_vector_store):
        results = mock_vector_store.search("door lock signal", top_k=1)
        assert len(results) >= 1
        r = results[0]
        assert "chunk_id" in r
        assert "doc_name" in r
        assert "page_number" in r
        assert "text" in r
        assert "score" in r

    def test_search_top_k_limit(self, mock_vector_store):
        results = mock_vector_store.search("AUTOSAR component", top_k=2)
        assert len(results) <= 2

    def test_citation_metadata_propagated(self, mock_vector_store):
        """doc_name and page_number must flow correctly through to search results."""
        results = mock_vector_store.search("component interface", top_k=5)
        for r in results:
            assert isinstance(r["page_number"], int)
            assert r["page_number"] >= 1
            assert isinstance(r["doc_name"], str)
            assert r["doc_name"].endswith(".pdf")

    def test_empty_index_search_returns_empty(self, mock_embedder, tmp_path):
        vs = VectorStore(embedding_model=mock_embedder, index_dir=tmp_path / "empty")
        assert not vs.is_ready
        results = vs.search("anything")
        assert results == []

    def test_build_empty_chunks_raises(self, mock_embedder, tmp_path):
        vs = VectorStore(embedding_model=mock_embedder, index_dir=tmp_path / "err")
        with pytest.raises((ValueError, Exception)):
            vs.build_index([])

    def test_save_and_reload(self, mock_embedder, text_chunks, tmp_path):
        """Index saved and reloaded should return same search results."""
        vs1 = VectorStore(embedding_model=mock_embedder, index_dir=tmp_path / "save_test")
        vs1.build_index(text_chunks)
        vs1.save()

        vs2 = VectorStore(embedding_model=mock_embedder, index_dir=tmp_path / "save_test")
        loaded = vs2.load()
        assert loaded
        assert vs2.is_ready
        assert vs2.chunk_count == vs1.chunk_count

    def test_clear_resets_store(self, mock_embedder, text_chunks, tmp_path):
        vs = VectorStore(embedding_model=mock_embedder, index_dir=tmp_path / "clear_test")
        vs.build_index(text_chunks)
        assert vs.is_ready
        vs.clear()
        assert not vs.is_ready
        assert vs.chunk_count == 0
