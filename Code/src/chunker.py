"""
chunker.py
----------
Splits page-level text records into overlapping chunks suitable for embedding.
Each chunk carries full provenance metadata (doc_name, page_number, chunk_id).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from src.pdf_processor import PageRecord

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    """A text segment with full provenance metadata."""
    chunk_id: str          # globally unique: "<doc_name>_p<page>_c<idx>"
    doc_name: str
    page_number: int
    text: str
    char_start: int        # character offset within original page text
    char_end: int

    def to_dict(self) -> dict:
        """Convert chunk to a primitive serializable dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "doc_name": self.doc_name,
            "page_number": self.page_number,
            "text": self.text,
            "char_start": self.char_start,
            "char_end": self.char_end,
        }

    @classmethod
    def from_dict(cls, data: dict) -> TextChunk:
        """Construct TextChunk instance from dictionary."""
        return cls(
            chunk_id=str(data.get("chunk_id", "")),
            doc_name=str(data.get("doc_name", "")),
            page_number=int(data.get("page_number", 1)),
            text=str(data.get("text", "")),
            char_start=int(data.get("char_start", 0)),
            char_end=int(data.get("char_end", 0)),
        )


class TextChunker:
    """
    Splits PageRecord text into overlapping chunks.

    Parameters
    ----------
    chunk_size : int
        Target maximum characters per chunk (default 800).
    overlap : int
        Characters of overlap between consecutive chunks (default 150).
    """

    def __init__(self, chunk_size: int = 800, overlap: int = 150) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive.")
        if overlap < 0:
            raise ValueError("overlap must be non-negative.")
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size.")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_pages(self, pages: List[PageRecord]) -> List[TextChunk]:
        """
        Chunk all pages from a document.

        Parameters
        ----------
        pages : list of PageRecord

        Returns
        -------
        list of TextChunk
        """
        chunks: List[TextChunk] = []
        for page in pages:
            page_chunks = self._chunk_page(page)
            chunks.extend(page_chunks)
        logger.debug("Produced %d chunks from %d pages.", len(chunks), len(pages))
        return chunks

    def _chunk_page(self, page: PageRecord) -> List[TextChunk]:
        text = page.text
        if not text or not text.strip():
            return []

        chunks: List[TextChunk] = []
        step = self.chunk_size - self.overlap
        start = 0
        idx = 0

        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:  # skip empty chunks
                chunk_id = f"{page.doc_name}_p{page.page_number}_c{idx}"
                chunks.append(
                    TextChunk(
                        chunk_id=chunk_id,
                        doc_name=page.doc_name,
                        page_number=page.page_number,
                        text=chunk_text,
                        char_start=start,
                        char_end=end,
                    )
                )
                idx += 1

            start += step

        return chunks
