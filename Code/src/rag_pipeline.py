"""
rag_pipeline.py
---------------
Orchestrates the full RAG workflow: document processing → chunking →
embedding → indexing → similarity retrieval → cross-encoder re-ranking →
structured answer generation.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.chunker import TextChunk, TextChunker
from src.embeddings import EmbeddingModel
from src.llm_provider import LLMProvider
from src.pdf_processor import DocumentResult, PDFProcessor
from src.reranker import ReRanker
from src.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    End-to-end RAG pipeline for AUTOSAR HLD document analysis.
    Incorporates a Cross-Encoder Re-Ranking model to refine candidate chunks
    and produce high-precision, structured engineering answers.

    Parameters
    ----------
    chunk_size : int
    chunk_overlap : int
    top_k : int
        Number of final re-ranked chunks to pass to the answer generator.
    initial_retrieval_k : int
        Number of candidate chunks to retrieve from vector search before re-ranking.
    index_dir : str
        Directory for persisting FAISS index.
    use_mock_embeddings : bool
        Force mock embeddings and mock re-ranker (for offline testing).
    """

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 150,
        top_k: int = 5,
        initial_retrieval_k: Optional[int] = None,
        index_dir: str = "data/faiss_index",
        use_mock_embeddings: bool = False,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.top_k = top_k
        self.initial_retrieval_k = initial_retrieval_k or max(top_k * 3, 12)

        self.pdf_processor = PDFProcessor()
        self.chunker = TextChunker(chunk_size=chunk_size, overlap=chunk_overlap)
        self.embedder = EmbeddingModel(use_mock=use_mock_embeddings)
        self.vector_store = VectorStore(
            embedding_model=self.embedder, index_dir=index_dir
        )
        self.reranker = ReRanker(use_mock=use_mock_embeddings)
        self.llm = LLMProvider()

        self._doc_results: Dict[str, DocumentResult] = {}
        self._all_chunks: List[TextChunk] = []

    # ------------------------------------------------------------------
    # Document ingestion
    # ------------------------------------------------------------------

    def process_uploaded_files(
        self, files: List[Tuple[bytes, str]]
    ) -> List[DocumentResult]:
        """
        Process a list of (bytes, filename) tuples.

        Returns
        -------
        list of DocumentResult
        """
        results = []
        new_chunks: List[TextChunk] = []

        for data, name in files:
            result = self.pdf_processor.process_bytes(data, name)
            self._doc_results[name] = result
            results.append(result)

            if result.success and not result.is_text_empty:
                chunks = self.chunker.chunk_pages(result.pages)
                new_chunks.extend(chunks)
                logger.info(
                    "Processed '%s': %d pages, %d chunks.",
                    name,
                    result.extractable_pages,
                    len(chunks),
                )
            else:
                logger.warning("Skipping '%s': %s", name, result.error or "no text")

        if new_chunks:
            # Merge with any existing chunks from previous uploads
            self._all_chunks.extend(new_chunks)
            self.vector_store.build_index(self._all_chunks)
            self.vector_store.save()

        return results

    def process_file_path(self, path: str) -> DocumentResult:
        """Process a PDF from disk path (used in tests)."""
        result = self.pdf_processor.process_file(path)
        name = Path(path).name
        self._doc_results[name] = result

        if result.success and not result.is_text_empty:
            chunks = self.chunker.chunk_pages(result.pages)
            self._all_chunks.extend(chunks)
            self.vector_store.build_index(self._all_chunks)

        return result

    # ------------------------------------------------------------------
    # Query with Re-ranking & Structured Answer Generation
    # ------------------------------------------------------------------

    def query(self, question: str) -> Dict:
        """
        Answer a question using indexed documents with two-stage retrieval:
        1. Vector similarity search retrieves candidate chunks.
        2. Cross-Encoder re-ranker scores and re-orders candidates.
        3. Structured answer generation synthesizes the response.

        Parameters
        ----------
        question : str

        Returns
        -------
        dict with keys:
            answer, mode, citations, retrieved_chunks, initial_candidates_count, provider
        """
        if not self.vector_store.is_ready:
            return {
                "answer": (
                    "⚠️ No documents have been indexed yet. "
                    "Please upload and process PDF documents first."
                ),
                "mode": "no_index",
                "citations": [],
                "retrieved_chunks": [],
                "provider": "none",
            }

        # Step 1: Initial vector retrieval (broad candidate pool)
        candidate_k = min(self.initial_retrieval_k, self.vector_store.chunk_count)
        initial_candidates = self.vector_store.search(question, top_k=candidate_k)

        if not initial_candidates:
            return self.llm.answer(question, [])

        # Step 2: Cross-Encoder Re-Ranking
        reranker = getattr(self, "reranker", None)
        if reranker is None:
            self.reranker = ReRanker()
            reranker = self.reranker

        reranked_chunks = reranker.rerank(
            query=question,
            chunks=initial_candidates,
            top_k=self.top_k,
        )

        # Step 3: Structured Answer Synthesis
        result = self.llm.answer(question, reranked_chunks)
        result["retrieved_chunks"] = reranked_chunks
        result["initial_candidates_count"] = len(initial_candidates)
        result["reranker_model"] = getattr(reranker, "model_name", "cross-encoder")
        result["reranker_is_mock"] = getattr(reranker, "is_mock", False)

        return result

    def summarize_document(self, doc_name: str) -> Optional[str]:
        """
        Generate an AI-powered architectural executive summary of a document
        using the configured LLM.
        """
        doc_result = self._doc_results.get(doc_name)
        if not doc_result or not doc_result.pages:
            return None

        # Sample leading pages to form context for the LLM
        text_samples = []
        for p in doc_result.pages[:12]:
            text_samples.append(f"--- Page {p.page_number} ---\n{p.text}")
        context = "\n\n".join(text_samples)

        return self.llm.summarize_document(context, doc_name)

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def load_existing_index(self) -> bool:
        """Try to load a previously saved index. Returns True on success."""
        return self.vector_store.load()

    def clear_index(self) -> None:
        """Reset the pipeline state."""
        self.vector_store.clear()
        self._doc_results.clear()
        self._all_chunks.clear()

    @property
    def is_ready(self) -> bool:
        return self.vector_store.is_ready

    @property
    def indexed_documents(self) -> List[str]:
        return self.vector_store.indexed_documents

    @property
    def chunk_count(self) -> int:
        return self.vector_store.chunk_count

    @property
    def doc_results(self) -> Dict[str, DocumentResult]:
        return self._doc_results
