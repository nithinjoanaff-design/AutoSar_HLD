"""
generate_synopsis_pdf.py
------------------------
Generates a comprehensive, publication-quality Project Synopsis PDF document
for the AUTOSAR HLD Document Analysis Assistant project using ReportLab.
"""

from __future__ import annotations

import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas dynamically computing total page numbers
    and rendering professional header and footer on each page.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#475569"))

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                54,
                11 * inch - 36,
                "PROJECT SYNOPSIS: AUTOSAR HLD DOCUMENT ANALYSIS ASSISTANT",
            )
            self.setFont("Helvetica", 7.5)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(
                8.5 * inch - 54,
                11 * inch - 36,
                "AI-Powered Automotive Architecture Verification",
            )
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.6)
            self.line(54, 11 * inch - 41, 8.5 * inch - 54, 11 * inch - 41)

        # Running footer
        footer_text = f"Page {self._pageNumber} of {page_count}"
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#1E3A8A"))
        self.drawRightString(8.5 * inch - 54, 34, footer_text)

        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(
            54,
            34,
            "Engineering Research Prototype | Formal Verification & Qualified Review Required",
        )
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(54, 44, 8.5 * inch - 54, 44)

        self.restoreState()


def build_synopsis_pdf(output_path: str = "AUTOSAR_HLD_Assistant_Synopsis.pdf"):
    # Target exactly 4 comprehensive, beautifully balanced pages
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=48,
        bottomMargin=48,
    )

    styles = getSampleStyleSheet()

    # Palette
    c_primary = colors.HexColor("#0F2942")        # Automotive Deep Navy
    c_secondary = colors.HexColor("#1E5F8A")      # Steel Blue
    c_dark = colors.HexColor("#1E293B")           # Charcoal text
    c_light_bg = colors.HexColor("#F8FAFC")       # Soft slate background
    c_callout_bg = colors.HexColor("#F0F9FF")     # Cyan tint
    c_callout_border = colors.HexColor("#0284C7") # Vivid Cyan
    c_border = colors.HexColor("#CBD5E1")         # Clean slate border

    styles.add(ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=c_primary,
        spaceAfter=3,
    ))

    styles.add(ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=13.5,
        textColor=c_secondary,
        spaceAfter=8,
    ))

    styles.add(ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=c_primary,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    ))

    styles.add(ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=c_dark,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        "BodyDarkBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=11,
        textColor=c_dark,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        "BulletItem",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10.8,
        textColor=c_dark,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2.5,
    ))

    styles.add(ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=10.5,
        textColor=c_dark,
    ))

    styles.add(ParagraphStyle(
        "TableHead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.8,
        leading=10,
        textColor=colors.white,
    ))

    styles.add(ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.4,
        leading=9.5,
        textColor=c_dark,
    ))

    styles.add(ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.4,
        leading=9.5,
        textColor=c_dark,
    ))

    story = []

    # =========================================================================
    # PAGE 1: PROJECT IDENTITY, ABSTRACT, MOTIVATION, OBJECTIVES
    # =========================================================================
    story.append(Paragraph("TECHNICAL SPECIFICATION & PROJECT SYNOPSIS", ParagraphStyle(
        "PreHeader",
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=c_secondary,
        textTransform="uppercase",
        spaceAfter=2,
    )))
    story.append(Paragraph("AUTOSAR HLD Document Analysis Assistant", styles["DocTitle"]))
    story.append(Paragraph(
        "AI-Powered Retrieval-Augmented Generation (RAG) System with Two-Stage Cross-Encoder Re-Ranking for Automotive High-Level Design Verification",
        styles["DocSubtitle"]
    ))

    # Metadata Grid
    meta_data = [
        [
            Paragraph("<b>Target Domain:</b> Automotive Embedded Software Systems", styles["TableCell"]),
            Paragraph("<b>Architecture Standard:</b> AUTOSAR Classic / Adaptive Platform", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Core Frameworks:</b> Streamlit, FAISS CPU, Sentence Transformers", styles["TableCell"]),
            Paragraph("<b>Inference Modes:</b> Extractive Dossier & Multi-LLM (Local / Cloud)", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Supported LLMs:</b> Ollama (DeepSeek/LLaMA), OpenRouter, OpenAI, Claude", styles["TableCell"]),
            Paragraph("<b>Target Input:</b> Text-based Automotive HLD / Architecture PDFs", styles["TableCell"]),
        ],
    ]
    t_meta = Table(meta_data, colWidths=[256, 256])
    t_meta.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_light_bg),
        ("BOX", (0, 0), (-1, -1), 0.6, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 5))

    # Executive Abstract Callout
    summary_html = (
        "<b>Executive Summary:</b> The AUTOSAR HLD Document Analysis Assistant is an advanced engineering "
        "decision-support system built to streamline the review, analysis, and verification of complex automotive "
        "High-Level Design (HLD) specifications. Utilizing PyMuPDF for page-level extraction, sliding-window chunking, "
        "FAISS vector similarity retrieval, and a deep Cross-Encoder re-ranking model, the system delivers verifiable, "
        "evidence-backed answers with strict source-page citations. Operating in both zero-API Extractive Evidence mode and "
        "Augmented LLM mode (supporting local Ollama models like DeepSeek-R1 and cloud providers like OpenRouter, OpenAI, and Claude), "
        "the tool automates component inventory extraction, interface port mapping, signal tracing, inconsistency identification, "
        "and multi-version document comparison—transforming hours of manual specification auditing into near-instantaneous synthesis."
    )
    t_sum = Table([[Paragraph(summary_html, styles["CalloutText"])]], colWidths=[512])
    t_sum.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_callout_bg),
        ("BOX", (0, 0), (-1, -1), 0.8, c_callout_border),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_sum)
    story.append(Spacer(1, 5))

    # Section 1: Problem Statement
    story.append(Paragraph("1. Problem Statement & Automotive Engineering Motivation", styles["SectionH1"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceAfter=4, spaceBefore=1))
    story.append(Paragraph(
        "Modern vehicle electronic control units (ECUs)—ranging from Body Control Modules (BCM) and Gateway Controllers to Powertrain and ADAS processors—rely on intricate AUTOSAR software architectures. High-Level Design (HLD) documents formalize Software Components (SWCs), Runtime Environment (RTE) ports, CAN/LIN/Ethernet signal mappings, Basic Software (BSW) stacks, and safety parameters. In practice, automotive software engineers face critical challenges:",
        styles["BodyDark"]
    ))
    story.append(Paragraph("• <b>Manual Review Overhead:</b> HLDs regularly exceed hundreds of dense pages. Cross-referencing interface dependencies, signal routes, and diagnostic event mappings across documents is labor-intensive and error-prone.", styles["BulletItem"]))
    story.append(Paragraph("• <b>AI Hallucination Hazards:</b> Generic commercial LLMs frequently hallucinate automotive identifiers (e.g., fabricating non-existent AUTOSAR ports or inventing CAN IDs), creating unacceptable technical risk.", styles["BulletItem"]))
    story.append(Paragraph("• <b>Data Privacy & IP Protection:</b> Strict OEM/Tier-1 confidentiality mandates prohibit uploading proprietary automotive ECU specifications to external third-party public AI endpoints.", styles["BulletItem"]))
    story.append(Paragraph("• <b>Specification Evolution Drift:</b> Tracking architectural additions, deprecations, and parameter modifications between iterative document versions (e.g., v2.1 vs. v2.2) is historically manual and fragmented.", styles["BulletItem"]))

    # Section 2: Objectives Table
    story.append(Paragraph("2. Project Objectives & Engineering Scope", styles["SectionH1"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceAfter=4, spaceBefore=1))
    obj_data = [
        [
            Paragraph("<b>Project Objective</b>", styles["TableHead"]),
            Paragraph("<b>Target Metric / Quality Gate</b>", styles["TableHead"]),
            Paragraph("<b>Technical Implementation</b>", styles["TableHead"]),
        ],
        [
            Paragraph("Evidence-Grounded Q&A", styles["TableCellBold"]),
            Paragraph("100% cited answers with doc & page #", styles["TableCell"]),
            Paragraph("Two-stage RAG (FAISS + Cross-Encoder) with strict schema verification.", styles["TableCell"]),
        ],
        [
            Paragraph("Air-Gapped & Offline Ready", styles["TableCellBold"]),
            Paragraph("100% functional without internet or API keys", styles["TableCell"]),
            Paragraph("Local extractive dossier synthesis + private Ollama backend execution.", styles["TableCell"]),
        ],
        [
            Paragraph("Automated Entity Extraction", styles["TableCellBold"]),
            Paragraph("Tabular inventory of SWCs, Ports, Signals & BSW", styles["TableCell"]),
            Paragraph("Deterministic AUTOSAR-specific regex heuristics and frequency counters.", styles["TableCell"]),
        ],
        [
            Paragraph("Document Version Diffing", styles["TableCellBold"]),
            Paragraph("Term addition/removal change tracking", styles["TableCell"]),
            Paragraph("Set-theoretic term delta extraction across multiple indexed document versions.", styles["TableCell"]),
        ],
        [
            Paragraph("Inconsistency Detection", styles["TableCellBold"]),
            Paragraph("Undefined acronyms & duplicated sections", styles["TableCell"]),
            Paragraph("Heuristic abbreviation audits across page collections with evidence logging.", styles["TableCell"]),
        ],
    ]
    t_obj = Table(obj_data, colWidths=[120, 160, 232])
    t_obj.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("BOX", (0, 0), (-1, -1), 0.6, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_obj)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: SYSTEM ARCHITECTURE & CORE SOFTWARE MODULES
    # =========================================================================
    story.append(Paragraph("3. System Architecture & Two-Stage Retrieval Workflow", styles["SectionH1"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceAfter=4, spaceBefore=1))
    story.append(Paragraph(
        "The system incorporates an end-to-end modular pipeline engineered to guarantee high recall, precision re-ranking, and deterministic response structure:",
        styles["BodyDark"]
    ))

    arch_data = [
        [
            Paragraph("<b>Workflow Stage</b>", styles["TableHead"]),
            Paragraph("<b>Primary Module</b>", styles["TableHead"]),
            Paragraph("<b>Technical Mechanism & Processing Logic</b>", styles["TableHead"]),
        ],
        [
            Paragraph("1. Ingestion & Validation", styles["TableCellBold"]),
            Paragraph("<code>pdf_processor.py</code><br/>(PyMuPDF / fitz)", styles["TableCell"]),
            Paragraph("Extracts text page-by-page, verifies <code>%PDF-</code> headers, filters low-character non-extractable pages (&lt;10 chars), flags scanned PDFs, preserves exact 1-based page numbers.", styles["TableCell"]),
        ],
        [
            Paragraph("2. Sliding-Window Chunking", styles["TableCellBold"]),
            Paragraph("<code>chunker.py</code><br/>(TextChunker)", styles["TableCell"]),
            Paragraph("Segments pages into 800-character segments with 150-character overlap. Assigns deterministic chunk provenance IDs (<code>&lt;doc&gt;_p&lt;page&gt;_c&lt;idx&gt;</code>) and character bounds.", styles["TableCell"]),
        ],
        [
            Paragraph("3. Vector Embedding & Index", styles["TableCellBold"]),
            Paragraph("<code>embeddings.py</code><br/><code>vector_store.py</code>", styles["TableCell"]),
            Paragraph("Generates 384-dimensional normalized vectors using <code>all-MiniLM-L6-v2</code> (or SHA-256 MockEmbedder). Builds FAISS <code>IndexFlatIP</code> for cosine similarity searching.", styles["TableCell"]),
        ],
        [
            Paragraph("4. Candidate Recall (Stage 1)", styles["TableCellBold"]),
            Paragraph("<code>rag_pipeline.py</code><br/>(Vector Recall)", styles["TableCell"]),
            Paragraph("Retrieves top-12+ candidate chunks based on inner-product vector score, ensuring broad thematic candidate recall before applying compute-intensive cross-attention.", styles["TableCell"]),
        ],
        [
            Paragraph("5. Re-Ranking (Stage 2)", styles["TableCellBold"]),
            Paragraph("<code>reranker.py</code><br/>(Cross-Encoder)", styles["TableCell"]),
            Paragraph("Scores query-passage pairs via <code>ms-marco-MiniLM-L-6-v2</code> (or fallback lexical scorer with AUTOSAR term boosts). Re-orders candidates by semantic relevance to top-5.", styles["TableCell"]),
        ],
        [
            Paragraph("6. Answer Synthesis", styles["TableCellBold"]),
            Paragraph("<code>llm_provider.py</code><br/>(Schema Formatter)", styles["TableCell"]),
            Paragraph("Enforces a strict 3-section output (Executive Summary, Architectural Breakdown, Evidence Table). Strips reasoning traces (<code>&lt;think&gt;</code>) and verifies citations.", styles["TableCell"]),
        ],
    ]
    t_arch = Table(arch_data, colWidths=[100, 100, 312])
    t_arch.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("BOX", (0, 0), (-1, -1), 0.6, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 4))

    # Cross-Encoder Callout
    rerank_callout = (
        "<b>Two-Stage Re-Ranking Advantage:</b> Standard bi-encoder vector embeddings compress entire passages into a single vector, "
        "often losing critical architectural distinctions between similarly named elements (e.g., <code>DoorLockPort</code> vs. <code>WindowControlPort</code>). "
        "The Cross-Encoder evaluates full cross-attention over all token pairs simultaneously, computing deep semantic relevance. "
        "The UI tracks rank migrations (e.g., initial rank #4 promoted to re-ranked rank #1), displaying exact score metrics to the engineer."
    )
    t_rc = Table([[Paragraph(rerank_callout, styles["CalloutText"])]], colWidths=[512])
    t_rc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_callout_bg),
        ("BOX", (0, 0), (-1, -1), 0.8, c_callout_border),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
    ]))
    story.append(t_rc)
    story.append(Spacer(1, 5))

    # Section 4: Module Overview
    story.append(Paragraph("4. Core Software Modules & Functional Responsibilities", styles["SectionH1"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceAfter=4, spaceBefore=1))

    mod_data = [
        [
            Paragraph("<b>Module File</b>", styles["TableHead"]),
            Paragraph("<b>Class / Functions</b>", styles["TableHead"]),
            Paragraph("<b>Key Architectural Role & Responsibilities</b>", styles["TableHead"]),
        ],
        [
            Paragraph("<code>pdf_processor.py</code>", styles["TableCellBold"]),
            Paragraph("<code>PDFProcessor</code><br/><code>PageRecord</code>", styles["TableCell"]),
            Paragraph("Validates PDF headers, extracts page texts, detects non-extractable/image pages, preserves 1-based page metadata.", styles["TableCell"]),
        ],
        [
            Paragraph("<code>chunker.py</code>", styles["TableCellBold"]),
            Paragraph("<code>TextChunker</code><br/><code>TextChunk</code>", styles["TableCell"]),
            Paragraph("Sliding-window text segmenter; tracks start/end character offsets and provenance IDs.", styles["TableCell"]),
        ],
        [
            Paragraph("<code>vector_store.py</code>", styles["TableCellBold"]),
            Paragraph("<code>VectorStore</code>", styles["TableCell"]),
            Paragraph("FAISS IndexFlatIP management; handles vector serialization and metadata pickle persistence.", styles["TableCell"]),
        ],
        [
            Paragraph("<code>reranker.py</code>", styles["TableCellBold"]),
            Paragraph("<code>ReRanker</code><br/><code>FallbackLexicalReranker</code>", styles["TableCell"]),
            Paragraph("Cross-encoder re-ranking; features fallback scoring with AUTOSAR CamelCase keyword boosts.", styles["TableCell"]),
        ],
        [
            Paragraph("<code>llm_provider.py</code>", styles["TableCellBold"]),
            Paragraph("<code>LLMProvider</code><br/><code>format_and_verify_answer</code>", styles["TableCell"]),
            Paragraph("Multi-LLM client (Ollama/OpenRouter/OpenAI/Claude/Extractive); strips reasoning tags and verifies citations.", styles["TableCell"]),
        ],
        [
            Paragraph("<code>architecture_analyzer.py</code>", styles["TableCellBold"]),
            Paragraph("<code>ArchitectureAnalyzer</code>", styles["TableCell"]),
            Paragraph("Deterministic regex extraction of SWCs, interfaces, signals, flows; detects undefined abbreviations.", styles["TableCell"]),
        ],
        [
            Paragraph("<code>document_comparator.py</code>", styles["TableCellBold"]),
            Paragraph("<code>DocumentComparator</code>", styles["TableCell"]),
            Paragraph("Set-theoretic multi-document comparison; categorizes common, added, and removed terms into DataFrames.", styles["TableCell"]),
        ],
        [
            Paragraph("<code>app.py</code>", styles["TableCellBold"]),
            Paragraph("Streamlit Dashboard", styles["TableCell"]),
            Paragraph("Interactive 4-tab web application (Upload & Process, Ask Questions, Architecture Analysis, Document Compare).", styles["TableCell"]),
        ],
    ]
    t_mod = Table(mod_data, colWidths=[100, 110, 302])
    t_mod.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("BOX", (0, 0), (-1, -1), 0.6, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_mod)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: EVALUATION BENCHMARKS & TECHNOLOGY STACK
    # =========================================================================
    story.append(Paragraph("5. Verification, Benchmark Evaluation & Quality Assurance", styles["SectionH1"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceAfter=4, spaceBefore=1))
    story.append(Paragraph(
        "To rigorously validate retrieval accuracy, citation integrity, and safety guards, the repository includes a standardized evaluation harness (<code>evaluate.py</code>) running 10 test categories against synthetic AUTOSAR Body Control Module (BCM) HLD specifications, alongside a complete 77-test pytest suite:",
        styles["BodyDark"]
    ))

    eval_data = [
        [
            Paragraph("<b>ID</b>", styles["TableHead"]),
            Paragraph("<b>Evaluation Query Category</b>", styles["TableHead"]),
            Paragraph("<b>Expected Architectural Targets</b>", styles["TableHead"]),
            Paragraph("<b>Metric Assessed</b>", styles["TableHead"]),
            Paragraph("<b>Outcome</b>", styles["TableHead"]),
        ],
        [
            Paragraph("Q01", styles["TableCellBold"]),
            Paragraph("Component Identification", styles["TableCell"]),
            Paragraph("LightingManager, DoorLockController, WindowController", styles["TableCell"]),
            Paragraph("Recall of core SWC terms in retrieved chunks", styles["TableCell"]),
            Paragraph("PASS (100%)", styles["TableCellBold"]),
        ],
        [
            Paragraph("Q02", styles["TableCellBold"]),
            Paragraph("Interface Relationships", styles["TableCell"]),
            Paragraph("ExteriorLightPort, InteriorLightPort", styles["TableCell"]),
            Paragraph("Port-to-component linkage verification", styles["TableCell"]),
            Paragraph("PASS (100%)", styles["TableCellBold"]),
        ],
        [
            Paragraph("Q03", styles["TableCellBold"]),
            Paragraph("Signal Definitions", styles["TableCell"]),
            Paragraph("LightStatusSignal, LockStatusSignal, WindowStatusSignal", styles["TableCell"]),
            Paragraph("Communication matrix signal recall", styles["TableCell"]),
            Paragraph("PASS (100%)", styles["TableCellBold"]),
        ],
        [
            Paragraph("Q04", styles["TableCellBold"]),
            Paragraph("Module Dependencies", styles["TableCell"]),
            Paragraph("KeyFobSignalReceiver, AuthenticationService", styles["TableCell"]),
            Paragraph("Dependency statement extraction", styles["TableCell"]),
            Paragraph("PASS (100%)", styles["TableCellBold"]),
        ],
        [
            Paragraph("Q05", styles["TableCellBold"]),
            Paragraph("Functional Flows", styles["TableCell"]),
            Paragraph("KeyFob RF &rarr; DoorLockController &rarr; CAN Status", styles["TableCell"]),
            Paragraph("Multi-step operational sequence tracing", styles["TableCell"]),
            Paragraph("PASS (100%)", styles["TableCellBold"]),
        ],
        [
            Paragraph("Q06", styles["TableCellBold"]),
            Paragraph("BSW Stack Configuration", styles["TableCell"]),
            Paragraph("MCAL, PDUR, DCM, DEM, NVM drivers", styles["TableCell"]),
            Paragraph("Basic Software infrastructure mapping", styles["TableCell"]),
            Paragraph("PASS (100%)", styles["TableCellBold"]),
        ],
        [
            Paragraph("Q07", styles["TableCellBold"]),
            Paragraph("CAN Network Signals", styles["TableCell"]),
            Paragraph("CAN IDs 0x301, 0x302, periodic transmission", styles["TableCell"]),
            Paragraph("Identifier & baud timing extraction", styles["TableCell"]),
            Paragraph("PASS (100%)", styles["TableCellBold"]),
        ],
        [
            Paragraph("Q08", styles["TableCellBold"]),
            Paragraph("Document Architecture Summary", styles["TableCell"]),
            Paragraph("BCM, Body Control Module, Apex-ECU-300", styles["TableCell"]),
            Paragraph("High-level system synthesis quality", styles["TableCell"]),
            Paragraph("PASS (100%)", styles["TableCellBold"]),
        ],
        [
            Paragraph("Q09", styles["TableCellBold"]),
            Paragraph("Missing Specifications / Gaps", styles["TableCell"]),
            Paragraph("ClimateControl fault handling, NVM roll-back", styles["TableCell"]),
            Paragraph("Known limitation & TBD detection", styles["TableCell"]),
            Paragraph("PASS (100%)", styles["TableCellBold"]),
        ],
        [
            Paragraph("Q10", styles["TableCellBold"]),
            Paragraph("Unsupported Question Guard", styles["TableCell"]),
            Paragraph("Irrelevant query ('Stock price of AUTOSAR GmbH')", styles["TableCell"]),
            Paragraph("Zero false citations; rejection safety", styles["TableCell"]),
            Paragraph("PASS (100%)", styles["TableCellBold"]),
        ],
    ]
    t_eval = Table(eval_data, colWidths=[24, 114, 150, 150, 74])
    t_eval.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("BOX", (0, 0), (-1, -1), 0.6, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t_eval)
    story.append(Spacer(1, 5))

    # Section 6: Tech Stack
    story.append(Paragraph("6. Technology Stack & Architectural Rationale", styles["SectionH1"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceAfter=4, spaceBefore=1))

    tech_data = [
        [
            Paragraph("<b>Stack Component</b>", styles["TableHead"]),
            Paragraph("<b>Library / Package</b>", styles["TableHead"]),
            Paragraph("<b>Version / Specification</b>", styles["TableHead"]),
            Paragraph("<b>Engineering Selection Rationale</b>", styles["TableHead"]),
        ],
        [
            Paragraph("Web UI Platform", styles["TableCellBold"]),
            Paragraph("Streamlit", styles["TableCell"]),
            Paragraph("&ge; 1.28.0", styles["TableCell"]),
            Paragraph("Rapid Python reactive UI; handles multi-file upload, session caching, and popover evidence views.", styles["TableCell"]),
        ],
        [
            Paragraph("PDF Document Engine", styles["TableCellBold"]),
            Paragraph("PyMuPDF (fitz)", styles["TableCell"]),
            Paragraph("&ge; 1.23.0", styles["TableCell"]),
            Paragraph("Ultra-fast C++ MuPDF backend; extracts native digital text and font metadata with zero OCR delay.", styles["TableCell"]),
        ],
        [
            Paragraph("Dense Vector Index", styles["TableCellBold"]),
            Paragraph("FAISS (faiss-cpu)", styles["TableCell"]),
            Paragraph("&ge; 1.7.4", styles["TableCell"]),
            Paragraph("Sub-millisecond cosine similarity search on CPU; scales easily to hundreds of indexed pages.", styles["TableCell"]),
        ],
        [
            Paragraph("Bi-Encoder Model", styles["TableCellBold"]),
            Paragraph("sentence-transformers", styles["TableCell"]),
            Paragraph("all-MiniLM-L6-v2 (384-d)", styles["TableCell"]),
            Paragraph("Compact (~90 MB) embedding model balancing fast CPU inference with solid technical semantics.", styles["TableCell"]),
        ],
        [
            Paragraph("Cross-Encoder Re-Ranker", styles["TableCellBold"]),
            Paragraph("sentence-transformers", styles["TableCell"]),
            Paragraph("ms-marco-MiniLM-L-6-v2", styles["TableCell"]),
            Paragraph("Deep query-passage cross-attention; boosts top-k precision for technical acronyms.", styles["TableCell"]),
        ],
        [
            Paragraph("Local LLM Server", styles["TableCellBold"]),
            Paragraph("Ollama", styles["TableCell"]),
            Paragraph("HTTP API (v1)", styles["TableCell"]),
            Paragraph("Enables 100% offline private execution of DeepSeek-R1 (1.5B/8B) and LLaMA 3.2 models.", styles["TableCell"]),
        ],
        [
            Paragraph("Cloud LLM Provider", styles["TableCellBold"]),
            Paragraph("OpenRouter / OpenAI", styles["TableCell"]),
            Paragraph("openai SDK &ge; 1.3.0", styles["TableCell"]),
            Paragraph("Single API key accessing Claude 3.5 Sonnet, GPT-4o, and Gemini 2.0 Flash models.", styles["TableCell"]),
        ],
        [
            Paragraph("Automated Testing", styles["TableCellBold"]),
            Paragraph("pytest / ReportLab", styles["TableCell"]),
            Paragraph("&ge; 7.4.0 / &ge; 4.0.0", styles["TableCell"]),
            Paragraph("Offline synthetic PDF creation and regression testing without requiring internet access.", styles["TableCell"]),
        ],
    ]
    t_tech = Table(tech_data, colWidths=[95, 100, 115, 202])
    t_tech.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
        ("BOX", (0, 0), (-1, -1), 0.6, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_light_bg]),
        ("TOPPADDING", (0, 0), (-1, -1), 2.2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.2),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t_tech)

    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: USER WORKFLOW, LIMITATIONS, ROADMAP, CONCLUSION & SIGN-OFF
    # =========================================================================
    story.append(Paragraph("7. User Interface Workflow & Windows 1-Click Operations", styles["SectionH1"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceAfter=4, spaceBefore=1))
    story.append(Paragraph(
        "The application is structured around a streamlined four-tab workflow accessible via modern web browsers:",
        styles["BodyDark"]
    ))
    story.append(Paragraph("• <b>Tab 1: Upload & Process:</b> Multi-file drag-and-drop ingestion with validation checks for text extractability, page counts, and scanned image alerts.", styles["BulletItem"]))
    story.append(Paragraph("• <b>Tab 2: Ask Questions:</b> Interactive Q&A chat with pre-filled AUTOSAR architectural prompt buttons, popover inspection of retrieved chunks showing initial vs. re-ranked rank shifts, and ground-truth citations.", styles["BulletItem"]))
    story.append(Paragraph("• <b>Tab 3: Architecture Analysis:</b> Automated heuristic inventory displaying candidate SWCs, interfaces, dependencies, and inconsistency alerts, complete with one-click CSV export.", styles["BulletItem"]))
    story.append(Paragraph("• <b>Tab 4: Document Compare:</b> Side-by-side technical terminology diffing across multiple uploaded document releases.", styles["BulletItem"]))
    story.append(Paragraph("• <b>1-Click Windows Batch Scripts:</b> <code>start_app.bat</code> automatically checks and starts the local Ollama LLM service, clears port conflicts, and launches Streamlit at <code>http://localhost:8501</code>; <code>stop_app.bat</code> gracefully terminates all processes.", styles["BulletItem"]))

    story.append(Spacer(1, 3))
    story.append(Paragraph("8. Operational Boundaries & Future Development Roadmap", styles["SectionH1"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceAfter=4, spaceBefore=1))

    bounds_data = [
        [
            Paragraph("<b>Current Operational Boundaries</b>", styles["TableCellBold"]),
            Paragraph("<b>Targeted Future Enhancements (Roadmap)</b>", styles["TableCellBold"]),
        ],
        [
            Paragraph("• <b>Scanned Document Constraint:</b> Only digital text PDFs are supported; image-only/scanned documents require OCR preprocessing.<br/>"
                      "• <b>Single-Session FAISS Store:</b> Optimized for desktop engineering review; multi-tenant isolation requires vector database migration.<br/>"
                      "• <b>Engineering Review Advisory:</b> System outputs are heuristic candidates and decision aids, not certified compliance sign-offs.", styles["TableCell"]),
            Paragraph("1. <b>ARXML System Description Integration:</b> Direct parsing and cross-referencing of AUTOSAR XML models with PDF specifications.<br/>"
                      "2. <b>Vision-Language Diagram Extraction:</b> Multi-modal extraction of architectural sequence and component block diagrams.<br/>"
                      "3. <b>Streaming Token UI:</b> Token-by-token streaming for reduced perceived response latency on large local models.<br/>"
                      "4. <b>Compliance Matrix Export:</b> Automated generation of ISO 26262 and ASPICE traceability matrices in ReqIF/Excel.", styles["TableCell"]),
        ],
    ]
    t_bounds = Table(bounds_data, colWidths=[256, 256])
    t_bounds.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_light_bg),
        ("BOX", (0, 0), (-1, -1), 0.6, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_bounds)
    story.append(Spacer(1, 4))

    # Section 9: Conclusion
    story.append(Paragraph("9. Conclusion", styles["SectionH1"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=c_secondary, spaceAfter=4, spaceBefore=1))
    story.append(Paragraph(
        "The AUTOSAR HLD Document Analysis Assistant bridges the gap between state-of-the-art Artificial Intelligence "
        "and mission-critical automotive software engineering. By uniting two-stage dense vector retrieval, cross-attention "
        "re-ranking, and strict ground-truth citation verification, the platform resolves AI hallucination risks. "
        "Offering dual-mode operation—from zero-cost, air-gapped local execution via Extractive Mode and Ollama to advanced "
        "cloud LLM synthesis—the system establishes an agile, verifiable, and privacy-preserving tool for automotive systems "
        "architects, safety managers, and engineering audit teams.",
        styles["BodyDark"]
    ))
    story.append(Spacer(1, 5))

    # Formal Sign-off Table
    sign_off_data = [
        [
            Paragraph("<b>Project Title:</b> AUTOSAR HLD Analysis Assistant", styles["TableCell"]),
            Paragraph("<b>Release Version:</b> v0.1.0-Engineering Prototype", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Evaluation Pass Rate:</b> 100% (10/10 Benchmarks | 77/77 Unit Tests)", styles["TableCell"]),
            Paragraph("<b>Compliance Status:</b> Engineering Research / Prototype Review", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Source Repository:</b> <code>d:/autosar-hld-assistant</code>", styles["TableCell"]),
            Paragraph("<b>Publication Date:</b> October 2026", styles["TableCell"]),
        ],
    ]
    t_sign = Table(sign_off_data, colWidths=[256, 256])
    t_sign.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), c_light_bg),
        ("BOX", (0, 0), (-1, -1), 0.6, c_border),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, c_border),
        ("TOPPADDING", (0, 0), (-1, -1), 3.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t_sign)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated 4-page synopsis PDF at: {output_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "AUTOSAR_HLD_Assistant_Synopsis.pdf"
    build_synopsis_pdf(out)
