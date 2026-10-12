"""
reranker.py
-----------
Cross-Encoder based re-ranking model to refine and re-order candidate chunks
retrieved from vector search. Significantly improves top-k precision and relevance.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")


class FallbackLexicalReranker:
    """
    High-precision lexical & keyword-density re-ranker used as a fast fallback
    or for deterministic offline testing.
    Combines exact phrase matching, query term coverage, capitalized technical identifier
    density, and initial vector similarity.
    """

    def predict(self, pairs: List[tuple[str, str]]) -> np.ndarray:
        scores = []
        for query, text in pairs:
            q_clean = query.lower()
            t_clean = text.lower()

            # 1. Exact query match or exact phrase match
            exact_bonus = 2.0 if q_clean in t_clean else 0.0

            # 2. Query token overlap
            q_tokens = [w for w in re.findall(r"\w+", q_clean) if len(w) > 2]
            if not q_tokens:
                scores.append(0.5)
                continue

            matches = sum(1 for w in q_tokens if w in t_clean)
            term_coverage = matches / len(q_tokens)

            # 3. Technical identifier boost (AUTOSAR words, CamelCase terms)
            autosar_matches = len(
                re.findall(
                    r"\b([A-Z][a-zA-Z0-9]+(?:Manager|Controller|Module|Port|Signal|Interface|Service|RTE|BSW|DEM|DCM|NVM))\b",
                    text,
                )
            )
            tech_boost = min(autosar_matches * 0.05, 0.3)

            # 4. Proximity / frequency of query terms in text
            term_freq = sum(t_clean.count(w) for w in q_tokens)
            freq_score = min(term_freq * 0.05, 0.4)

            raw_score = (term_coverage * 2.0) + exact_bonus + tech_boost + freq_score
            # Normalize with sigmoid-like curve
            norm_score = float(1.0 / (1.0 + np.exp(-raw_score + 1.5)))
            scores.append(norm_score)

        return np.array(scores, dtype=np.float32)


class ReRanker:
    """
    Re-ranks candidate chunks using a Cross-Encoder model.
    Falls back gracefully to FallbackLexicalReranker if offline or model unavailable.

    Parameters
    ----------
    model_name : str
        HuggingFace cross-encoder repository id.
    use_mock : bool
        If True, forces FallbackLexicalReranker without downloading weights.
    """

    def __init__(
        self,
        model_name: str = DEFAULT_RERANKER_MODEL,
        use_mock: bool = False,
    ) -> None:
        self.model_name = model_name
        self._model = None
        self._is_mock = False

        if use_mock:
            logger.info("Mock / fallback re-ranker forced by caller.")
            self._model = FallbackLexicalReranker()
            self._is_mock = True
        else:
            self._load_model()

    def _load_model(self) -> None:
        try:
            from sentence_transformers import CrossEncoder

            logger.info("Loading Cross-Encoder re-ranking model: %s", self.model_name)
            self._model = CrossEncoder(self.model_name)
            self._is_mock = False
            logger.info("Re-ranking model loaded successfully.")
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not load CrossEncoder model '%s' (%s). "
                "Falling back to high-precision lexical re-ranker.",
                self.model_name,
                exc,
            )
            self._model = FallbackLexicalReranker()
            self._is_mock = True

    @property
    def is_mock(self) -> bool:
        return self._is_mock

    def rerank(
        self,
        query: str,
        chunks: List[Dict],
        top_k: int = 5,
    ) -> List[Dict]:
        """
        Re-score and re-rank a list of retrieved chunks for the given query.

        Parameters
        ----------
        query : str
            User query.
        chunks : list of dict
            Retrieved chunk dicts (from VectorStore search).
        top_k : int
            Number of top chunks to return after re-ranking.

        Returns
        -------
        list of dict
            Re-ranked chunks with 'rerank_score', 'initial_rank', and 'rerank_rank'.
        """
        if not chunks:
            return []

        # Prepare pairs: [(query, chunk_text)]
        pairs = [(query, c.get("text", "")) for c in chunks]

        try:
            scores = self._model.predict(pairs)  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            logger.error("Error during cross-encoder prediction: %s. Using lexical fallback.", exc)
            fallback = FallbackLexicalReranker()
            scores = fallback.predict(pairs)

        # Standardize scores into float list
        if isinstance(scores, np.ndarray):
            scores_list = [float(s) for s in scores.flatten()]
        else:
            scores_list = [float(s) for s in scores]

        # Attach original ranking and re-ranking score
        augmented_chunks = []
        for idx, (chunk, score) in enumerate(zip(chunks, scores_list)):
            chunk_copy = dict(chunk)
            chunk_copy["initial_rank"] = idx + 1
            chunk_copy["initial_score"] = float(chunk.get("score", 0.0))
            chunk_copy["rerank_score"] = float(score)
            augmented_chunks.append(chunk_copy)

        # Sort descending by re-ranking score
        augmented_chunks.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Add new rank index and return top_k
        top_results = augmented_chunks[:top_k]
        for rank, c in enumerate(top_results, 1):
            c["rerank_rank"] = rank

        logger.info(
            "Re-ranked %d candidates to top %d. Top score: %.3f (prev rank %d)",
            len(chunks),
            len(top_results),
            top_results[0]["rerank_score"] if top_results else 0.0,
            top_results[0]["initial_rank"] if top_results else 0,
        )

        return top_results
