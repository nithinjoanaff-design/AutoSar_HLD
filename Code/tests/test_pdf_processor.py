"""
test_pdf_processor.py
---------------------
Tests for PDF text extraction, validation, and metadata preservation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pdf_processor import PDFProcessor, DocumentResult


class TestPDFProcessorValidation:
    """Test file validation and error handling."""

    def test_empty_bytes_returns_error(self, pdf_processor):
        result = pdf_processor.process_bytes(b"", "empty.pdf")
        assert not result.success
        assert result.error is not None
        assert "empty" in result.error.lower()

    def test_invalid_pdf_header_returns_error(self, pdf_processor):
        result = pdf_processor.process_bytes(b"This is not a PDF file", "bad.pdf")
        assert not result.success
        assert result.error is not None

    def test_missing_file_returns_error(self, pdf_processor):
        result = pdf_processor.process_file("/nonexistent/path/file.pdf")
        assert not result.success
        assert result.error is not None

    def test_doc_name_preserved(self, pdf_processor, synthetic_pdf_bytes):
        result = pdf_processor.process_bytes(synthetic_pdf_bytes, "my_document.pdf")
        assert result.doc_name == "my_document.pdf"


class TestPDFProcessorExtraction:
    """Test successful text extraction."""

    def test_success_on_valid_pdf(self, pdf_processor, synthetic_pdf_bytes):
        result = pdf_processor.process_bytes(synthetic_pdf_bytes, "test.pdf")
        assert result.success, f"Processing failed: {result.error}"

    def test_extractable_pages_positive(self, pdf_processor, synthetic_pdf_bytes):
        result = pdf_processor.process_bytes(synthetic_pdf_bytes, "test.pdf")
        assert result.extractable_pages > 0

    def test_total_pages_reported(self, pdf_processor, synthetic_pdf_bytes):
        result = pdf_processor.process_bytes(synthetic_pdf_bytes, "test.pdf")
        assert result.total_pages > 0

    def test_pages_contain_text(self, pdf_processor, synthetic_pdf_bytes):
        result = pdf_processor.process_bytes(synthetic_pdf_bytes, "test.pdf")
        for page in result.pages:
            assert page.text.strip()

    def test_page_numbers_are_one_based(self, pdf_processor, synthetic_pdf_bytes):
        result = pdf_processor.process_bytes(synthetic_pdf_bytes, "test.pdf")
        assert all(p.page_number >= 1 for p in result.pages)

    def test_page_doc_name_matches(self, pdf_processor, synthetic_pdf_bytes):
        result = pdf_processor.process_bytes(synthetic_pdf_bytes, "my.pdf")
        for page in result.pages:
            assert page.doc_name == "my.pdf"

    def test_char_count_computed(self, pdf_processor, synthetic_pdf_bytes):
        result = pdf_processor.process_bytes(synthetic_pdf_bytes, "test.pdf")
        for page in result.pages:
            assert page.char_count == len(page.text)

    def test_autosar_content_extracted(self, pdf_processor, synthetic_pdf_bytes):
        """AUTOSAR domain terms should appear in extracted text."""
        result = pdf_processor.process_bytes(synthetic_pdf_bytes, "test.pdf")
        all_text = " ".join(p.text for p in result.pages).lower()
        assert any(term in all_text for term in ["autosar", "bcm", "swc", "component", "signal"])
