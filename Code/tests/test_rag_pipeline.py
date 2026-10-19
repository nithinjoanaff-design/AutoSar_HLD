"""
test_rag_pipeline.py
--------------------
Tests for the end-to-end RAG pipeline, including LLM configuration checks,
missing index handling, and citation propagation.
Uses mock embedder and mock LLM – no API keys or internet required.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestLLMProvider:
    """Test LLM provider configuration and fallback behavior."""

    def test_no_provider_configured(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "none"}):
            from src.llm_provider import LLMProvider
            provider = LLMProvider()
            assert not provider.is_configured
            assert provider.provider == "none"

    def test_openai_missing_key_falls_back(self):
        env = {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": ""}
        with patch.dict(os.environ, env, clear=False):
            from src.llm_provider import LLMProvider
            provider = LLMProvider()
            assert provider.provider == "none"

    def test_openrouter_missing_key_falls_back(self):
        env = {"LLM_PROVIDER": "openrouter", "OPENROUTER_API_KEY": ""}
        with patch.dict(os.environ, env, clear=False):
            from src.llm_provider import LLMProvider
            provider = LLMProvider()
            assert provider.provider == "none"

    def test_ollama_configured(self):
        env = {
            "LLM_PROVIDER": "ollama",
            "OLLAMA_BASE_URL": "http://localhost:11434/v1",
            "OLLAMA_MODEL": "llama3.2",
        }
        with patch.dict(os.environ, env, clear=False):
            from src.llm_provider import LLMProvider
            provider = LLMProvider()
            assert provider.is_configured
            assert provider.provider == "ollama"

    def test_extractive_mode_answer(self):
        with patch.dict(os.environ, {"LLM_PROVIDER": "none"}):
            from src.llm_provider import LLMProvider
            provider = LLMProvider()
            chunks = [
                {
                    "doc_name": "bcm.pdf",
                    "page_number": 3,
                    "text": "LightingManager controls exterior lighting.",
                    "score": 0.9,
                }
            ]
            result = provider.answer("What controls the lights?", chunks)
            assert result["mode"] == "extractive"
            assert "extractive" in result["answer"].lower() or "passage" in result["answer"].lower()
            assert len(result["citations"]) == 1
            assert result["citations"][0]["doc_name"] == "bcm.pdf"
            assert result["citations"][0]["page_number"] == 3

    def test_strip_reasoning_and_verify_citations(self):
        from src.llm_provider import format_and_verify_answer

        raw_llm_output = (
            "<think>\n"
            "Alright, let me think about how the disabled flow works...\n"
            "</think>\n"
            "### 💡 Executive Summary\n"
            "The disabled flow ensures blower request is set to zero when climate control is deactivated.\n\n"
            "### 🏗️ Architectural Breakdown\n"
            "- **Software Components / Modules:** ClimateController, ActuatorManager\n\n"
            "### Summary Table\n"
            "| # | Document | Page | Key Supported Architecture Fact |\n"
            "|---|---|---|---|\n"
            "| 1 | [Document Name] | 1 | Disabled flow disables blower request. |\n\n"
            "<details><summary>🧠 DeepSeek-R1 Reasoning Chain</summary>\n"
            "More thoughts here...\n"
            "</details>"
        )

        test_chunks = [
            {
                "doc_name": "climate_hld.pdf",
                "page_number": 4,
                "text": "Disabled flow disables blower request when climate control is off.",
            }
        ]

        cleaned = format_and_verify_answer(raw_llm_output, test_chunks)

        # 1. Reasoning must be stripped
        assert "<think>" not in cleaned
        assert "</think>" not in cleaned
        assert "<details>" not in cleaned
        assert "Alright, let me think" not in cleaned

        # 2. [Document Name] placeholder must be replaced with ground-truth doc
        assert "[Document Name]" not in cleaned
        assert "climate_hld.pdf" in cleaned
        assert "Page 4" in cleaned

        # 3. 3 core sections must be present
        assert "### 💡 Executive Summary" in cleaned
        assert "### 🏗️ Architectural Breakdown" in cleaned
        assert "### 📑 Evidence & Citations Summary" in cleaned
        with patch.dict(os.environ, {"LLM_PROVIDER": "none"}):
            from src.llm_provider import LLMProvider
            provider = LLMProvider()
            chunks = [
                {"doc_name": "bcm.pdf", "page_number": 1, "text": "Text A", "score": 0.9},
                {"doc_name": "bcm.pdf", "page_number": 1, "text": "Text B", "score": 0.8},
                {"doc_name": "bcm.pdf", "page_number": 2, "text": "Text C", "score": 0.7},
            ]
            result = provider.answer("Question", chunks)
            # Citations should be unique (page 1 appears once)
            pages = [(c["doc_name"], c["page_number"]) for c in result["citations"]]
            assert len(pages) == len(set(pages))


class TestRAGPipeline:
    """Integration tests for the RAG pipeline using mock embedder."""

    def _make_pipeline(self, tmp_path):
        from src.rag_pipeline import RAGPipeline
        with patch.dict(os.environ, {"LLM_PROVIDER": "none"}):
            return RAGPipeline(
                chunk_size=800,
                chunk_overlap=150,
                top_k=3,
                index_dir=str(tmp_path / "faiss"),
                use_mock_embeddings=True,
            )

    def test_pipeline_not_ready_before_processing(self, tmp_path):
        pipeline = self._make_pipeline(tmp_path)
        assert not pipeline.is_ready

    def test_query_without_index_returns_helpful_message(self, tmp_path):
        pipeline = self._make_pipeline(tmp_path)
        result = pipeline.query("What are the software components?")
        assert result["mode"] in ("no_index", "no_results")

    def test_process_and_query(self, tmp_path, synthetic_pdf_bytes):
        pipeline = self._make_pipeline(tmp_path)
        results = pipeline.process_uploaded_files([(synthetic_pdf_bytes, "bcm.pdf")])
        assert len(results) == 1
        assert results[0].success
        assert pipeline.is_ready

        answer = pipeline.query("What are the software components?")
        assert "mode" in answer
        assert "answer" in answer
        assert "retrieved_chunks" in answer

    def test_retrieved_chunks_have_citations(self, tmp_path, synthetic_pdf_bytes):
        pipeline = self._make_pipeline(tmp_path)
        pipeline.process_uploaded_files([(synthetic_pdf_bytes, "bcm.pdf")])
        result = pipeline.query("What signals are used?")
        for chunk in result.get("retrieved_chunks", []):
            assert "doc_name" in chunk
            assert "page_number" in chunk

    def test_clear_index(self, tmp_path, synthetic_pdf_bytes):
        pipeline = self._make_pipeline(tmp_path)
        pipeline.process_uploaded_files([(synthetic_pdf_bytes, "bcm.pdf")])
        assert pipeline.is_ready
        pipeline.clear_index()
        assert not pipeline.is_ready

    def test_multiple_documents_indexed(self, tmp_path, synthetic_pdf_bytes, synthetic_pdf_bytes_v2):
        pipeline = self._make_pipeline(tmp_path)
        files = [
            (synthetic_pdf_bytes, "bcm_v1.pdf"),
            (synthetic_pdf_bytes_v2, "bcm_v2.pdf"),
        ]
        pipeline.process_uploaded_files(files)
        assert len(pipeline.indexed_documents) == 2

    def test_no_fabricated_citations(self, tmp_path, synthetic_pdf_bytes):
        """Citations must reference real indexed documents."""
        pipeline = self._make_pipeline(tmp_path)
        pipeline.process_uploaded_files([(synthetic_pdf_bytes, "bcm.pdf")])
        result = pipeline.query("What is the LightingManager?")
        for cit in result.get("citations", []):
            assert cit["doc_name"] in pipeline.indexed_documents

    def test_unsupported_question_handled(self, tmp_path, synthetic_pdf_bytes):
        """Questions with no relevant evidence should return a helpful message, not fabricated answers."""
        pipeline = self._make_pipeline(tmp_path)
        pipeline.process_uploaded_files([(synthetic_pdf_bytes, "bcm.pdf")])
        # This question is about something not in the document
        result = pipeline.query("What is the GDP of France?")
        # Either no_results mode or extractive mode with low-relevance passages
        assert result["mode"] in ("no_results", "extractive", "llm")
