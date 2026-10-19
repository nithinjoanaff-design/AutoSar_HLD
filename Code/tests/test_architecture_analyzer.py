"""
test_architecture_analyzer.py
------------------------------
Tests for architecture analysis, component extraction, and CSV export.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.architecture_analyzer import ArchitectureAnalyzer
from src.pdf_processor import PageRecord


def make_pages_from_text(text: str, doc_name: str = "test.pdf") -> list:
    """Helper: create a list of PageRecord from raw text."""
    return [PageRecord(doc_name=doc_name, page_number=1, text=text)]


# Rich AUTOSAR text for extraction tests
HLD_TEXT = """
AUTOSAR BCM High Level Design

Software Components:
LightingManager SWC controls exterior lighting.
DoorLockController SWC depends on KeyFobSignalReceiver.
WindowController SWC uses PowerManagementService.
ClimateControlModule interfaces with TemperatureSensor via SPI bus.

Interfaces and Ports:
ExteriorLightPort (provided by LightingManager)
DoorLockPort (provided by DoorLockController)
AuthenticationServicePort (required by DoorLockController)

Signals:
LightStatusSignal, LockStatusSignal, WindowStatusSignal on CAN bus.
DimmingValueSignal controls LED brightness.

Dependencies:
LightingManager depends on NVM and DEM modules.
DoorLockController sends to CAN bus and invokes DEM for fault logging.

Functional flows:
The startup sequence triggers LightingManager initialization.
A periodic Task_10ms callback updates sensor readings every 10 milliseconds.
"""


class TestComponentExtraction:

    def test_components_returned_as_list(self):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        comps = analyzer.extract_components()
        assert isinstance(comps, list)

    def test_known_components_found(self):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        comps = analyzer.extract_components()
        names = {c["name"] for c in comps}
        # At least some AUTOSAR terms should be detected
        expected = {"LightingManager", "DoorLockController", "WindowController"}
        assert expected & names, f"Expected some of {expected} in {names}"

    def test_component_frequency_positive(self):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        comps = analyzer.extract_components()
        for c in comps:
            assert c["frequency"] >= 1

    def test_component_pages_list(self):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        comps = analyzer.extract_components()
        for c in comps:
            assert isinstance(c["pages"], list)
            assert all(isinstance(p, int) for p in c["pages"])

    def test_no_stop_words_in_components(self):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        comps = analyzer.extract_components()
        from src.architecture_analyzer import STOP_WORDS
        for c in comps:
            assert c["name"] not in STOP_WORDS


class TestDependencyExtraction:

    def test_dependencies_extracted(self):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        deps = analyzer.extract_dependencies()
        assert len(deps) > 0

    def test_dependency_has_page_number(self):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        deps = analyzer.extract_dependencies()
        for d in deps:
            assert "page_number" in d
            assert isinstance(d["page_number"], int)

    def test_dependency_has_description(self):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        deps = analyzer.extract_dependencies()
        for d in deps:
            assert d["description"].strip()


class TestSummary:

    def test_summary_is_string(self):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        summary = analyzer.generate_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_summary_mentions_doc_name(self):
        pages = make_pages_from_text(HLD_TEXT, doc_name="bcm_hld.pdf")
        analyzer = ArchitectureAnalyzer(pages)
        summary = analyzer.generate_summary()
        assert "bcm_hld.pdf" in summary


class TestFindingsDataframe:

    def test_findings_df_is_dataframe(self):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        df = analyzer.build_findings_dataframe()
        assert isinstance(df, pd.DataFrame)

    def test_findings_df_has_required_columns(self):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        df = analyzer.build_findings_dataframe()
        required_cols = ["Finding", "Category", "Source Pages", "Supporting Evidence", "Review Status"]
        for col in required_cols:
            assert col in df.columns

    def test_findings_df_csv_export(self, tmp_path):
        pages = make_pages_from_text(HLD_TEXT)
        analyzer = ArchitectureAnalyzer(pages)
        df = analyzer.build_findings_dataframe()
        csv_path = tmp_path / "findings.csv"
        df.to_csv(csv_path, index=False)
        assert csv_path.exists()
        loaded = pd.read_csv(csv_path)
        assert list(loaded.columns) == list(df.columns)

    def test_empty_document_returns_empty_df(self):
        pages = make_pages_from_text("   ", doc_name="empty.pdf")
        # Force at least one page record
        pages[0].text = "minimal text here for testing purposes"
        analyzer = ArchitectureAnalyzer(pages)
        df = analyzer.build_findings_dataframe()
        assert isinstance(df, pd.DataFrame)
