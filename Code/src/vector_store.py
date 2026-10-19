"""
vector_store.py
---------------
Manages FAISS vector index construction, persistence, and similarity search.
Stores chunk metadata alongside the index for citation retrieval.
"""

from __future__ import annotations

import json
import logging
import os
import pickle
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.chunker import TextChunk
from src.embeddings import EmbeddingModel

logger = logging.getLogger(__name__)

INDEX_FILE = "index.faiss"
META_FILE = "metadata.pkl"
CONFIG_FILE = "config.json"


class VectorStore:
    """
    FAISS-backed vector store for text chunk retrieval.

    Uses IndexFlatIP (inner product = cosine similarity when embeddings are normalized).

    Parameters
    ----------
    embedding_model : EmbeddingModel
    index_dir : str or Path
        Directory for persisting the FAISS index and metadata.
    """

    def __init__(
        self,
        embedding_model: EmbeddingModel,
        index_dir: str | Path = "data/faiss_index",
    ) -> None:
        self.embedding_model = embedding_model
        self.index_dir = Path(index_dir)
        self._index = None          # faiss.IndexFlatIP
        self._chunks: List[TextChunk] = []
        self._doc_names: List[str] = []

    # ------------------------------------------------------------------
    # Building the index
    # ------------------------------------------------------------------

    def build_index(self, chunks: List[TextChunk]) -> None:
        """
        Encode all chunks and build a FAISS index.

        Parameters
        ----------
        chunks : list of TextChunk
        """
        try:
            import faiss  # type: ignore
        except ImportError:
            raise RuntimeError(
                "faiss-cpu is not installed. Run: pip install faiss-cpu"
            )

        if not chunks:
            raise ValueError("Cannot build index from empty chunk list.")

        texts = [c.text for c in chunks]
        logger.info("Encoding %d chunks for indexing …", len(texts))
        vectors = self.embedding_model.encode(texts, normalize=True)

        dim = vectors.shape[1]
        index = faiss.IndexFlatIP(dim)
        index.add(vectors)  # type: ignore[arg-type]

        self._index = index
        self._chunks = list(chunks)
        self._doc_names = sorted({c.doc_name for c in chunks})
        logger.info(
            "FAISS index built: %d vectors, dim=%d, docs=%s",
            index.ntotal,
            dim,
            self._doc_names,
        )

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Persist the FAISS index and chunk metadata to disk."""
        try:
            import faiss  # type: ignore
        except ImportError:
            raise RuntimeError("faiss-cpu is not installed.")

        if self._index is None:
            raise RuntimeError("No index to save. Call build_index first.")

        self.index_dir.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self._index, str(self.index_dir / INDEX_FILE))

        # Convert chunks to primitive dicts before saving to avoid class-identity pickling errors
        chunk_dicts = [
            c.to_dict()
            if hasattr(c, "to_dict")
            else {
                "chunk_id": getattr(c, "chunk_id", ""),
                "doc_name": getattr(c, "doc_name", ""),
                "page_number": getattr(c, "page_number", 1),
                "text": getattr(c, "text", ""),
                "char_start": getattr(c, "char_start", 0),
                "char_end": getattr(c, "char_end", 0),
            }
            if not isinstance(c, dict)
            else c
            for c in self._chunks
        ]

        with open(self.index_dir / META_FILE, "wb") as f:
            pickle.dump(chunk_dicts, f)

        config = {
            "model_name": self.embedding_model.model_name,
            "is_mock": self.embedding_model.is_mock,
            "chunk_count": len(self._chunks),
            "doc_names": self._doc_names,
        }
        with open(self.index_dir / CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        logger.info("Index saved to %s", self.index_dir)

    def load(self) -> bool:
        """
        Load persisted index and metadata.

        Returns
        -------
        bool
            True if loaded successfully, False otherwise.
        """
        try:
            import faiss  # type: ignore
        except ImportError:
            logger.error("faiss-cpu not installed.")
            return False

        idx_path = self.index_dir / INDEX_FILE
        meta_path = self.index_dir / META_FILE

        if not idx_path.exists() or not meta_path.exists():
            logger.info("No persisted index found at %s", self.index_dir)
            return False

        try:
            self._index = faiss.read_index(str(idx_path))
            with open(meta_path, "rb") as f:
                raw_chunks = pickle.load(f)

            from src.chunker import TextChunk

            reconstructed_chunks = []
            for item in raw_chunks:
                if isinstance(item, dict):
                    reconstructed_chunks.append(TextChunk.from_dict(item))
                else:
                    reconstructed_chunks.append(
                        TextChunk(
                            chunk_id=getattr(item, "chunk_id", ""),
                            doc_name=getattr(item, "doc_name", ""),
                            page_number=getattr(item, "page_number", 1),
                            text=getattr(item, "text", ""),
                            char_start=getattr(item, "char_start", 0),
                            char_end=getattr(item, "char_end", 0),
                        )
                    )

            self._chunks = reconstructed_chunks
            self._doc_names = sorted({c.doc_name for c in self._chunks})
            logger.info(
                "Index loaded: %d chunks, docs=%s",
                len(self._chunks),
                self._doc_names,
            )
            return True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to load index: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(
        self, query: str, top_k: int = 5
    ) -> List[Dict]:
        """
        Find the top-k most similar chunks for a query string.

        Parameters
        ----------
        query : str
        top_k : int

        Returns
        -------
        list of dict with keys: chunk_id, doc_name, page_number, text, score
        """
        if self._index is None or self._index.ntotal == 0:
            logger.warning("Search called on empty index.")
            return []

        q_vec = self.embedding_model.encode([query], normalize=True)
        k = min(top_k, self._index.ntotal)

        scores, indices = self._index.search(q_vec, k)  # type: ignore[arg-type]

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            chunk = self._chunks[idx]
            results.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "doc_name": chunk.doc_name,
                    "page_number": chunk.page_number,
                    "text": chunk.text,
                    "score": float(score),
                }
            )

        return results

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_ready(self) -> bool:
        return self._index is not None and self._index.ntotal > 0

    @property
    def chunk_count(self) -> int:
        return len(self._chunks)

    @property
    def indexed_documents(self) -> List[str]:
        return list(self._doc_names)

    def clear(self) -> None:
        """Reset the index and metadata."""
        self._index = None
        self._chunks = []
        self._doc_names = []
