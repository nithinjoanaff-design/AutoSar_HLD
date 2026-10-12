"""
embeddings.py
-------------
Generates text embeddings using Sentence Transformers (all-MiniLM-L6-v2 by default).
Falls back to a deterministic mock embedding in test/offline environments.
"""

from __future__ import annotations

import hashlib
import logging
import os
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)

# Default model name – overridable via env var
DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


class MockEmbedder:
    """
    Deterministic mock embedder for offline/unit test use.
    Produces 384-dimensional vectors derived from text hash.
    Clearly labelled – do not use for production retrieval quality.
    """

    DIMENSION = 384

    def encode(
        self,
        texts: List[str],
        batch_size: int = 32,
        show_progress_bar: bool = False,
        normalize_embeddings: bool = True,
    ) -> np.ndarray:
        vectors = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            # Repeat digest bytes to fill 384 floats
            arr = np.frombuffer(digest * (self.DIMENSION // len(digest) + 1), dtype=np.uint8)
            arr = arr[: self.DIMENSION].astype(np.float32) / 255.0 - 0.5
            if normalize_embeddings:
                norm = np.linalg.norm(arr)
                if norm > 0:
                    arr = arr / norm
            vectors.append(arr)
        return np.stack(vectors)


class EmbeddingModel:
    """
    Wrapper around a Sentence Transformers model.
    Falls back to MockEmbedder if model cannot be loaded.

    Parameters
    ----------
    model_name : str
        HuggingFace model identifier.
    use_mock : bool
        Force mock mode (useful in tests without internet access).
    """

    def __init__(self, model_name: str = DEFAULT_MODEL, use_mock: bool = False) -> None:
        self.model_name = model_name
        self._model = None
        self._is_mock = False

        if use_mock:
            logger.info("Mock embedder enabled by caller.")
            self._model = MockEmbedder()
            self._is_mock = True
        else:
            self._load_model()

    def _load_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            logger.info("Loading embedding model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            self._is_mock = False
            logger.info("Embedding model loaded successfully.")
        except ImportError:
            logger.warning(
                "sentence-transformers is not installed. Falling back to mock embedder. "
                "Run: pip install sentence-transformers"
            )
            self._model = MockEmbedder()
            self._is_mock = True
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not load embedding model '%s': %s. Falling back to mock embedder.",
                self.model_name,
                exc,
            )
            self._model = MockEmbedder()
            self._is_mock = True

    @property
    def is_mock(self) -> bool:
        return self._is_mock

    @property
    def dimension(self) -> int:
        if self._is_mock:
            return MockEmbedder.DIMENSION
        # SentenceTransformer exposes get_sentence_embedding_dimension()
        try:
            return self._model.get_sentence_embedding_dimension()  # type: ignore[union-attr]
        except Exception:  # noqa: BLE001
            return 384

    def encode(self, texts: List[str], normalize: bool = True) -> np.ndarray:
        """
        Encode a list of strings into embedding vectors.

        Parameters
        ----------
        texts : list of str
        normalize : bool
            Normalize to unit length (recommended for cosine similarity with FAISS IndexFlatIP).

        Returns
        -------
        np.ndarray of shape (len(texts), dimension)
        """
        if not texts:
            return np.zeros((0, self.dimension), dtype=np.float32)

        try:
            vectors = self._model.encode(  # type: ignore[union-attr]
                texts,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=normalize,
            )
            return np.array(vectors, dtype=np.float32)
        except Exception as exc:  # noqa: BLE001
            logger.error("Embedding error: %s. Returning zero vectors.", exc)
            return np.zeros((len(texts), self.dimension), dtype=np.float32)
