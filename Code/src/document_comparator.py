"""
document_comparator.py
----------------------
Compares terminology, components, and terms extracted from two or more documents.
Identifies additions, removals, and possible changes.
Results are labelled as potential differences, not confirmed design defects.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Set, Tuple

import pandas as pd

from src.architecture_analyzer import ArchitectureAnalyzer
from src.pdf_processor import PageRecord

logger = logging.getLogger(__name__)


class DocumentComparator:
    """
    Compares two documents by their extracted technical terms and components.

    Parameters
    ----------
    pages_a : list of PageRecord
        Pages from document A.
    pages_b : list of PageRecord
        Pages from document B.
    """

    def __init__(self, pages_a: List[PageRecord], pages_b: List[PageRecord]) -> None:
        self.analyzer_a = ArchitectureAnalyzer(pages_a)
        self.analyzer_b = ArchitectureAnalyzer(pages_b)
        self.doc_a = pages_a[0].doc_name if pages_a else "Document A"
        self.doc_b = pages_b[0].doc_name if pages_b else "Document B"

    def compare_components(self) -> pd.DataFrame:
        """
        Compare extracted component terms between the two documents.

        Returns
        -------
        pd.DataFrame with columns: Term, Status, Doc A Pages, Doc B Pages, Note
        """
        comps_a = {c["name"]: c for c in self.analyzer_a.extract_components()}
        comps_b = {c["name"]: c for c in self.analyzer_b.extract_components()}

        all_terms = set(comps_a.keys()) | set(comps_b.keys())
        rows = []

        for term in sorted(all_terms):
            in_a = term in comps_a
            in_b = term in comps_b

            if in_a and in_b:
                status = "Present in Both"
                pages_a_str = ", ".join(str(p) for p in comps_a[term]["pages"][:3])
                pages_b_str = ", ".join(str(p) for p in comps_b[term]["pages"][:3])
            elif in_a:
                status = "Only in Doc A (Possible Removal)"
                pages_a_str = ", ".join(str(p) for p in comps_a[term]["pages"][:3])
                pages_b_str = "—"
            else:
                status = "Only in Doc B (Possible Addition)"
                pages_a_str = "—"
                pages_b_str = ", ".join(str(p) for p in comps_b[term]["pages"][:3])

            rows.append(
                {
                    "Term": term,
                    "Status": status,
                    f"{self.doc_a} Pages": pages_a_str,
                    f"{self.doc_b} Pages": pages_b_str,
                    "Note": "Text-based difference – potential change, not confirmed defect",
                }
            )

        return pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["Term", "Status", f"{self.doc_a} Pages", f"{self.doc_b} Pages", "Note"]
        )

    def get_summary(self) -> Dict:
        """Return a textual comparison summary."""
        comps_a = set(c["name"] for c in self.analyzer_a.extract_components())
        comps_b = set(c["name"] for c in self.analyzer_b.extract_components())

        only_a = comps_a - comps_b
        only_b = comps_b - comps_a
        common = comps_a & comps_b

        return {
            "doc_a": self.doc_a,
            "doc_b": self.doc_b,
            "common_count": len(common),
            "only_a_count": len(only_a),
            "only_b_count": len(only_b),
            "only_a_sample": sorted(only_a)[:10],
            "only_b_sample": sorted(only_b)[:10],
            "common_sample": sorted(common)[:10],
        }
