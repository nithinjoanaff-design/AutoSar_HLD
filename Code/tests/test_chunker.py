"""
test_chunker.py
---------------
Tests for text chunking, overlap, and metadata preservation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.chunker import TextChunk, TextChunker
from src.pdf_processor import PageRecord


def make_page(text: str, page_num: int = 1, doc_name: str = "test.pdf") -> PageRecord:
    return PageRecord(doc_name=doc_name, page_number=page_num, text=text)


class TestChunkerBasics:

    def test_invalid_chunk_size_raises(self):
        with pytest.raises(ValueError):
            TextChunker(chunk_size=0)

    def test_negative_overlap_raises(self):
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, overlap=-1)

    def test_overlap_ge_chunk_size_raises(self):
        with pytest.raises(ValueError):
            TextChunker(chunk_size=100, overlap=100)

    def test_empty_page_produces_no_chunks(self):
        chunker = TextChunker()
        result = chunker.chunk_pages([make_page("")])
        assert result == []

    def test_whitespace_only_page_produces_no_chunks(self):
        chunker = TextChunker()
        result = chunker.chunk_pages([make_page("   \n\t  ")])
        assert result == []

    def test_short_text_produces_single_chunk(self):
        chunker = TextChunker(chunk_size=800, overlap=150)
        text = "Hello AUTOSAR world."
        result = chunker.chunk_pages([make_page(text)])
        assert len(result) == 1
        assert "AUTOSAR" in result[0].text

    def test_no_empty_chunks_produced(self):
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "A" * 200
        result = chunker.chunk_pages([make_page(text)])
        for chunk in result:
            assert chunk.text.strip()


class TestChunkMetadata:

    def test_chunk_id_format(self):
        chunker = TextChunker(chunk_size=800, overlap=150)
        page = make_page("Some text here for AUTOSAR.", doc_name="hld.pdf", page_num=3)
        chunks = chunker.chunk_pages([page])
        assert chunks[0].chunk_id == "hld.pdf_p3_c0"

    def test_doc_name_preserved(self):
        chunker = TextChunker()
        page = make_page("Text content", doc_name="my_hld.pdf")
        chunks = chunker.chunk_pages([page])
        assert all(c.doc_name == "my_hld.pdf" for c in chunks)

    def test_page_number_preserved(self):
        chunker = TextChunker()
        page = make_page("Text content", page_num=7)
        chunks = chunker.chunk_pages([page])
        assert all(c.page_number == 7 for c in chunks)

    def test_multiple_pages_tracked(self):
        chunker = TextChunker(chunk_size=800, overlap=150)
        pages = [
            make_page("Page one content about LightingManager.", page_num=1),
            make_page("Page two content about DoorLockController.", page_num=2),
        ]
        chunks = chunker.chunk_pages(pages)
        page_nums = {c.page_number for c in chunks}
        assert 1 in page_nums
        assert 2 in page_nums


class TestChunkOverlap:

    def test_overlap_creates_multiple_chunks(self):
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "A" * 200
        chunks = chunker.chunk_pages([make_page(text)])
        assert len(chunks) > 1

    def test_chunk_size_respected(self):
        chunker = TextChunker(chunk_size=100, overlap=20)
        text = "X" * 500
        chunks = chunker.chunk_pages([make_page(text)])
        for chunk in chunks:
            assert len(chunk.text) <= 100

    def test_chunk_ids_sequential(self):
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "B" * 300
        chunks = chunker.chunk_pages([make_page(text)])
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_id.endswith(f"_c{i}")
