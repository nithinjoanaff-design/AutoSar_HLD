"""
architecture_analyzer.py
-------------------------
Performs deterministic pattern-based and LLM-assisted analysis of AUTOSAR HLD documents.
All heuristic findings are clearly labelled as requiring engineering review.
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set

import pandas as pd

from src.pdf_processor import PageRecord

logger = logging.getLogger(__name__)

# ── AUTOSAR-specific regex patterns ──────────────────────────────────────────

# Component name patterns: CamelCase or UPPER_CASE identifiers
COMPONENT_PATTERN = re.compile(
    r"\b([A-Z][a-zA-Z0-9]{2,}(?:_[A-Za-z0-9]+)*|[A-Z]{2,}(?:_[A-Z0-9]+){1,})\b"
)

# Interface/port patterns
INTERFACE_PATTERN = re.compile(
    r"\b(I[A-Z][a-zA-Z0-9]+|[A-Za-z][A-Za-z0-9]*(?:Interface|Port|Signal|Service|Runnable|"
    r"SWC|SWComponent|Component|Module|Manager|Handler|Controller|Monitor|Sensor|"
    r"Actuator|Gateway|Bus|CAN|LIN|FlexRay|Ethernet|AUTOSAR|BSW|RTE|OS|"
    r"ECU|MCAL|PDUR|COM|DCM|DEM|FIM|NVM|Mem|Flash|Eeprom|Watchdog|SPI|I2C|"
    r"UART|PWM|ADC|DIO|ICU|GPT|MCU|PORT))\b"
)

# Signal patterns
SIGNAL_PATTERN = re.compile(
    r"\b([A-Za-z][A-Za-z0-9_]*(?:Signal|Sig|Msg|Message|Data|Value|Status|Cmd|Request|Response|Ack|Nack))\b",
    re.IGNORECASE,
)

# Dependency patterns
DEPENDENCY_KEYWORDS = re.compile(
    r"\b(depends on|uses|calls|invokes|sends to|receives from|connected to|interfaces with|"
    r"communicates with|provides|requires|implements)\b",
    re.IGNORECASE,
)

# Functional flow patterns
FLOW_KEYWORDS = re.compile(
    r"\b(flow|sequence|process|step|trigger|event|callback|notification|"
    r"initialization|startup|shutdown|periodic|cyclic|on-demand)\b",
    re.IGNORECASE,
)

# Common AUTOSAR stop words to filter
STOP_WORDS: Set[str] = {
    "The", "This", "That", "For", "And", "With", "From", "Into", "Upon",
    "When", "Where", "Which", "Each", "Some", "Will", "Can", "May",
    "Are", "Is", "Be", "As", "At", "Of", "In", "On", "By",
    "It", "Its", "To", "An", "A", "I", "If", "Or", "Not", "Has",
    "Have", "Had", "Was", "Were", "Been", "Being", "Do", "Does",
    "Did", "Does", "Shall", "Should", "Must", "Would", "Could",
    "All", "Any", "Both", "Few", "More", "Most", "Other", "Such",
    "Own", "Same", "So", "Than", "Then", "Too", "Very", "Just",
    "But", "Now", "How", "What", "There", "Their", "They",
    "PDF", "Page", "Figure", "Table", "Section", "Note",
}

MIN_TERM_LENGTH = 3
MIN_TERM_COUNT = 2  # appear at least twice to be a candidate


class ArchitectureAnalyzer:
    """
    Analyzes AUTOSAR HLD document content for components, interfaces,
    signals, dependencies, and potential inconsistencies.

    All findings are candidates requiring engineering review.
    """

    def __init__(self, pages: List[PageRecord]) -> None:
        self.pages = pages
        self._full_text = "\n".join(p.text for p in pages)
        self._page_texts = {p.page_number: p.text for p in pages}
        self._doc_name = pages[0].doc_name if pages else "Unknown"

    # ------------------------------------------------------------------
    # Component extraction
    # ------------------------------------------------------------------

    def extract_components(self) -> List[Dict]:
        """
        Extract candidate component names using regex heuristics.
        Returns list of dicts: {name, frequency, pages, category}.
        """
        name_pages: Dict[str, Set[int]] = defaultdict(set)
        name_count: Counter = Counter()

        for page in self.pages:
            matches = COMPONENT_PATTERN.findall(page.text)
            for match in matches:
                term = match.strip()
                if (
                    len(term) >= MIN_TERM_LENGTH
                    and term not in STOP_WORDS
                    and not term.isdigit()
                ):
                    name_count[term] += 1
                    name_pages[term].add(page.page_number)

        results = []
        for name, count in name_count.most_common(50):
            if count >= MIN_TERM_COUNT:
                results.append(
                    {
                        "name": name,
                        "frequency": count,
                        "pages": sorted(name_pages[name]),
                        "category": self._classify_term(name),
                    }
                )

        return results

    def _classify_term(self, term: str) -> str:
        """Heuristically classify a term into AUTOSAR category."""
        tl = term.lower()
        if any(k in tl for k in ("interface", "port", "rport", "pport")):
            return "Interface/Port"
        if any(k in tl for k in ("signal", "sig", "msg", "message")):
            return "Signal/Message"
        if any(k in tl for k in ("swc", "component", "module", "manager", "handler")):
            return "Software Component"
        if any(k in tl for k in ("service", "provider", "consumer")):
            return "Service"
        if any(k in tl for k in ("bus", "can", "lin", "ethernet", "flexray")):
            return "Communication Bus"
        if any(k in tl for k in ("bsw", "rte", "os", "mcal", "pdur", "com")):
            return "AUTOSAR Layer"
        if any(k in tl for k in ("ecu", "mcu", "sensor", "actuator", "gateway")):
            return "Hardware/ECU"
        return "Technical Term"

    # ------------------------------------------------------------------
    # Interface extraction
    # ------------------------------------------------------------------

    def extract_interfaces(self) -> List[Dict]:
        """Extract candidate interface/port/signal references."""
        found: Dict[str, Dict] = {}

        for page in self.pages:
            matches = INTERFACE_PATTERN.findall(page.text)
            for match in matches:
                term = match.strip()
                if (
                    len(term) >= 4
                    and term not in STOP_WORDS
                    and not term.isdigit()
                ):
                    if term not in found:
                        found[term] = {"name": term, "pages": set(), "count": 0}
                    found[term]["pages"].add(page.page_number)
                    found[term]["count"] += 1

        results = []
        for item in sorted(found.values(), key=lambda x: -x["count"]):
            if item["count"] >= MIN_TERM_COUNT:
                results.append(
                    {
                        "name": item["name"],
                        "count": item["count"],
                        "pages": sorted(item["pages"]),
                        "category": self._classify_term(item["name"]),
                    }
                )

        return results[:40]  # limit to top 40

    # ------------------------------------------------------------------
    # Dependency extraction
    # ------------------------------------------------------------------

    def extract_dependencies(self) -> List[Dict]:
        """Find sentences containing dependency keywords."""
        deps = []
        seen = set()

        for page in self.pages:
            sentences = re.split(r"(?<=[.!?])\s+", page.text)
            for sentence in sentences:
                if DEPENDENCY_KEYWORDS.search(sentence):
                    clean = sentence.strip()[:300]
                    if clean and clean not in seen:
                        seen.add(clean)
                        deps.append(
                            {
                                "description": clean,
                                "page_number": page.page_number,
                                "doc_name": page.doc_name,
                            }
                        )

        return deps[:30]

    # ------------------------------------------------------------------
    # Functional flows
    # ------------------------------------------------------------------

    def extract_functional_flows(self) -> List[Dict]:
        """Find sentences describing functional flows."""
        flows = []
        seen = set()

        for page in self.pages:
            sentences = re.split(r"(?<=[.!?])\s+", page.text)
            for sentence in sentences:
                if FLOW_KEYWORDS.search(sentence):
                    clean = sentence.strip()[:300]
                    if clean and clean not in seen and len(clean) > 30:
                        seen.add(clean)
                        flows.append(
                            {
                                "description": clean,
                                "page_number": page.page_number,
                                "doc_name": page.doc_name,
                            }
                        )

        return flows[:20]

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def generate_summary(self) -> str:
        """Generate a basic document summary from extracted metadata."""
        total_pages = len(self.pages)
        total_chars = sum(p.char_count for p in self.pages)
        components = self.extract_components()
        interfaces = self.extract_interfaces()

        top_components = [c["name"] for c in components[:10]]
        top_interfaces = [i["name"] for i in interfaces[:10]]

        summary_lines = [
            f"**Document:** {self._doc_name}",
            f"**Pages analyzed:** {total_pages}",
            f"**Total characters extracted:** {total_chars:,}",
            "",
            f"**Top candidate components ({len(top_components)} shown):**",
            ", ".join(top_components) if top_components else "_None identified_",
            "",
            f"**Top candidate technical terms ({len(top_interfaces)} shown):**",
            ", ".join(top_interfaces) if top_interfaces else "_None identified_",
            "",
            "_Note: All findings are heuristic candidates requiring engineering review._",
        ]

        return "\n".join(summary_lines)

    # ------------------------------------------------------------------
    # Inconsistency candidates
    # ------------------------------------------------------------------

    def find_inconsistencies(self) -> List[Dict]:
        """
        Identify potential inconsistencies using heuristics.
        Returns list of finding dicts.
        """
        findings = []

        # Check for undefined/unexplained abbreviations
        abbr_pattern = re.compile(r"\b([A-Z]{2,6})\b")
        abbr_counts: Counter = Counter()
        abbr_pages: Dict[str, Set[int]] = defaultdict(set)

        for page in self.pages:
            for match in abbr_pattern.finditer(page.text):
                abbr = match.group(1)
                if abbr not in STOP_WORDS and len(abbr) >= 2:
                    abbr_counts[abbr] += 1
                    abbr_pages[abbr].add(page.page_number)

        # Abbreviations appearing multiple times without apparent definition
        defined = set()
        for page in self.pages:
            # Look for "XYZ (Full Name)" or "Full Name (XYZ)" patterns
            defs = re.findall(r"\b([A-Z]{2,6})\s*\(", page.text)
            defs += re.findall(r"\(([A-Z]{2,6})\)", page.text)
            defined.update(defs)

        for abbr, count in abbr_counts.most_common(20):
            if abbr not in defined and count >= 3:
                findings.append(
                    {
                        "finding": f"Abbreviation '{abbr}' used {count}× without apparent definition",
                        "category": "Possible Missing Definition",
                        "source_pages": sorted(abbr_pages[abbr])[:5],
                        "supporting_evidence": f"Term appears {count} times across pages: "
                        + ", ".join(str(p) for p in sorted(abbr_pages[abbr])[:5]),
                        "review_status": "Requires Engineering Review",
                    }
                )

        # Duplicate section headings
        heading_pattern = re.compile(r"^(\d+\.?\d*\s+[A-Z][^\n]{5,60})$", re.MULTILINE)
        heading_counts: Counter = Counter()
        for page in self.pages:
            for m in heading_pattern.finditer(page.text):
                heading = m.group(1).strip()
                heading_counts[heading] += 1

        for heading, count in heading_counts.items():
            if count > 1:
                findings.append(
                    {
                        "finding": f"Heading '{heading[:50]}' appears {count}× – possible duplicate section",
                        "category": "Possible Duplicate Section",
                        "source_pages": [],
                        "supporting_evidence": f"Heading repeated {count} times in document.",
                        "review_status": "Requires Engineering Review",
                    }
                )

        return findings[:20]

    # ------------------------------------------------------------------
    # Findings table
    # ------------------------------------------------------------------

    def build_findings_dataframe(self) -> pd.DataFrame:
        """Build a DataFrame of all findings for display and CSV export."""
        rows = []

        for comp in self.extract_components()[:20]:
            rows.append(
                {
                    "Finding": f"Candidate Component: {comp['name']}",
                    "Category": comp["category"],
                    "Source Pages": ", ".join(str(p) for p in comp["pages"][:5]),
                    "Supporting Evidence": f"Appears {comp['frequency']}× in document",
                    "Review Status": "Candidate – Requires Verification",
                }
            )

        for dep in self.extract_dependencies()[:10]:
            rows.append(
                {
                    "Finding": f"Dependency Reference: {dep['description'][:80]}",
                    "Category": "Dependency",
                    "Source Pages": str(dep["page_number"]),
                    "Supporting Evidence": dep["description"],
                    "Review Status": "Candidate – Requires Verification",
                }
            )

        for inc in self.find_inconsistencies():
            rows.append(
                {
                    "Finding": inc["finding"],
                    "Category": inc["category"],
                    "Source Pages": ", ".join(str(p) for p in inc["source_pages"]),
                    "Supporting Evidence": inc["supporting_evidence"],
                    "Review Status": inc["review_status"],
                }
            )

        return pd.DataFrame(rows) if rows else pd.DataFrame(
            columns=["Finding", "Category", "Source Pages", "Supporting Evidence", "Review Status"]
        )
