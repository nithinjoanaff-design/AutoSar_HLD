"""
test_reranker.py
----------------
Unit tests for the Cross-Encoder re-ranking model and fallback lexical re-ranker.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reranker import FallbackLexicalReranker, ReRanker


SAMPLE_CANDIDATE_CHUNKS = [
    {
        "chunk_id": "doc_p1_c0",
        "doc_name": "bcm_hld.pdf",
        "page_number": 1,
        "text": "General overview of the vehicle electronics and power distribution system.",
        "score": 0.82,
    },
    {
        "chunk_id": "doc_p2_c0",
        "doc_name": "bcm_hld.pdf",
        "page_number": 2,
        "text": "The LightingManager SWC controls exterior lighting functions via ExteriorLightPort.",
        "score": 0.75,
    },
    {
        "chunk_id": "doc_p3_c0",
        "doc_name": "bcm_hld.pdf",
        "page_number": 3,
        "text": "DoorLockController manages keyless entry and lock status signals on CAN bus.",
        "score": 0.70,
    },
    {
        "chunk_id": "doc_p4_c0",
        "doc_name": "bcm_hld.pdf",
        "page_number": 4,
        "text": "Microcontroller clock configuration and watchdog timer parameters.",
        "score": 0.65,
    },
]


class TestReRanker:

    def test_reranker_mock_initialization(self):
        reranker = ReRanker(use_mock=True)
        assert reranker.is_mock is True

    def test_empty_chunks_returns_empty(self):
        reranker = ReRanker(use_mock=True)
        results = reranker.rerank("What is LightingManager?", [], top_k=3)
        assert results == []

    def test_rerank_preserves_attributes(self):
        reranker = ReRanker(use_mock=True)
        results = reranker.rerank("What is LightingManager?", SAMPLE_CANDIDATE_CHUNKS, top_k=2)
        assert len(results) == 2
        for r in results:
            assert "rerank_score" in r
            assert "initial_rank" in r
            assert "rerank_rank" in r
            assert "text" in r
            assert "doc_name" in r
            assert "page_number" in r

    def test_rerank_promotes_relevant_chunk(self):
        """LightingManager chunk was originally at rank 2; re-ranking should promote it to rank 1."""
        reranker = ReRanker(use_mock=True)
        results = reranker.rerank("How does LightingManager work?", SAMPLE_CANDIDATE_CHUNKS, top_k=3)
        assert len(results) > 0
        top_chunk = results[0]
        assert "LightingManager" in top_chunk["text"]
        assert top_chunk["rerank_rank"] == 1
        assert top_chunk["initial_rank"] == 2

    def test_top_k_respected(self):
        reranker = ReRanker(use_mock=True)
        results = reranker.rerank("Query", SAMPLE_CANDIDATE_CHUNKS, top_k=2)
        assert len(results) == 2

    def test_rerank_scores_descending(self):
        reranker = ReRanker(use_mock=True)
        results = reranker.rerank("LightingManager ExteriorLightPort", SAMPLE_CANDIDATE_CHUNKS, top_k=4)
        scores = [r["rerank_score"] for r in results]
        assert scores == sorted(scores, reverse=True)


class TestFallbackLexicalReranker:

    def test_lexical_reranker_exact_match(self):
        reranker = FallbackLexicalReranker()
        pairs = [
            ("DoorLockController", "The DoorLockController manages central locking."),
            ("DoorLockController", "Unrelated discussion about air conditioning."),
        ]
        scores = reranker.predict(pairs)
        assert len(scores) == 2
        assert scores[0] > scores[1]
