"""
pdf_processor.py
----------------
Handles PDF file validation, text extraction page by page using PyMuPDF,
and metadata preservation.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PageRecord:
    """Holds extracted text and metadata for a single PDF page."""
    doc_name: str
    page_number: int        # 1-based
    text: str
    char_count: int = field(init=False)

    def __post_init__(self) -> None:
        self.char_count = len(self.text)


@dataclass
class DocumentResult:
    """Result of processing a single PDF document."""
    doc_name: str
    pages: List[PageRecord]
    total_pages: int
    extractable_pages: int
    warnings: List[str]
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def is_text_empty(self) -> bool:
        return self.extractable_pages == 0


class PDFProcessor:
    """
    Extracts text from PDF files page by page using PyMuPDF.
    Does not require an LLM or any external service.
    """

    MIN_TEXT_CHARS = 10  # pages with fewer chars are considered non-extractable

    def process_file(self, file_path: str | Path) -> DocumentResult:
        """
        Process a PDF file on disk.

        Parameters
        ----------
        file_path : str or Path
            Path to the PDF file.

        Returns
        -------
        DocumentResult
        """
        path = Path(file_path)
        doc_name = path.name

        if not path.exists():
            return DocumentResult(
                doc_name=doc_name,
                pages=[],
                total_pages=0,
                extractable_pages=0,
                warnings=[],
                error=f"File not found: {file_path}",
            )

        try:
            raw = path.read_bytes()
        except OSError as exc:
            return DocumentResult(
                doc_name=doc_name,
                pages=[],
                total_pages=0,
                extractable_pages=0,
                warnings=[],
                error=f"Cannot read file: {exc}",
            )

        return self._process_bytes(raw, doc_name)

    def process_bytes(self, data: bytes, doc_name: str) -> DocumentResult:
        """Process a PDF from raw bytes (e.g. from Streamlit uploader)."""
        if not data:
            return DocumentResult(
                doc_name=doc_name,
                pages=[],
                total_pages=0,
                extractable_pages=0,
                warnings=[],
                error="Uploaded file is empty.",
            )
        return self._process_bytes(data, doc_name)

    def _process_bytes(self, data: bytes, doc_name: str) -> DocumentResult:
        try:
            import pymupdf as fitz  # PyMuPDF (preferred import, no deprecation warning)
        except ImportError:
            return DocumentResult(
                doc_name=doc_name,
                pages=[],
                total_pages=0,
                extractable_pages=0,
                warnings=[],
                error="PyMuPDF (fitz) is not installed. Run: pip install pymupdf",
            )

        # Validate PDF header
        if not data[:5] == b"%PDF-":
            return DocumentResult(
                doc_name=doc_name,
                pages=[],
                total_pages=0,
                extractable_pages=0,
                warnings=[],
                error="File does not appear to be a valid PDF (missing PDF header).",
            )

        try:
            doc = fitz.open(stream=data, filetype="pdf")
        except Exception as exc:  # noqa: BLE001
            return DocumentResult(
                doc_name=doc_name,
                pages=[],
                total_pages=0,
                extractable_pages=0,
                warnings=[],
                error=f"PyMuPDF could not open document: {exc}",
            )

        total_pages = doc.page_count
        pages: List[PageRecord] = []
        warnings: List[str] = []
        extractable = 0

        for idx in range(total_pages):
            try:
                page = doc[idx]
                text = page.get_text("text")  # type: ignore[attr-defined]
                text = text.strip()
                page_num = idx + 1

                if len(text) >= self.MIN_TEXT_CHARS:
                    extractable += 1
                    pages.append(PageRecord(doc_name=doc_name, page_number=page_num, text=text))
                else:
                    warnings.append(
                        f"Page {page_num} has minimal extractable text (<{self.MIN_TEXT_CHARS} chars). "
                        "It may be an image-only page requiring OCR."
                    )
            except Exception as exc:  # noqa: BLE001
                warnings.append(f"Page {idx + 1}: extraction error – {exc}")

        doc.close()

        if extractable == 0 and total_pages > 0:
            warnings.append(
                "No text could be extracted from any page. This document may be scanned "
                "or image-based and requires OCR preprocessing."
            )

        return DocumentResult(
            doc_name=doc_name,
            pages=pages,
            total_pages=total_pages,
            extractable_pages=extractable,
            warnings=warnings,
        )
