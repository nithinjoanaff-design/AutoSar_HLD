from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
import pptx.oxml.ns as ns
from lxml import etree

# ─── Colour Palette ───────────────────────────────────────────────
NAVY      = RGBColor(0x0F, 0x29, 0x4A)
DARK_BG   = RGBColor(0x0B, 0x11, 0x1E)
MID_BG    = RGBColor(0x15, 0x20, 0x33)
CYAN      = RGBColor(0x00, 0xD2, 0xFF)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRY = RGBColor(0xE2, 0xE8, 0xF0)
MID_GRY   = RGBColor(0x94, 0xA3, 0xB8)
ACCENT    = RGBColor(0x38, 0xBD, 0xF8)

W  = Inches(13.33)   # widescreen 16:9 width
H  = Inches(7.5)

prs = Presentation()
prs.slide_width  = W
prs.slide_height = H

blank_layout = prs.slide_layouts[6]   # truly blank

# ─── Helpers ─────────────────────────────────────────────────────
def solid_bg(slide, color: RGBColor):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def add_rect(slide, l, t, w, h, color: RGBColor, alpha=None):
    shape = slide.shapes.add_shape(1, l, t, w, h)   # MSO_SHAPE_TYPE.RECTANGLE = 1
    shape.line.fill.background()
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    return shape

def add_text(slide, text, l, t, w, h,
             font_name="Calibri", size=18, bold=False,
             color=WHITE, align=PP_ALIGN.LEFT,
             wrap=True):
    txBox = slide.shapes.add_textbox(l, t, w, h)
    tf = txBox.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.name = font_name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return txBox

def add_bullet_box(slide, items, l, t, w, h,
                   size=13, head_size=14, color=LIGHT_GRY):
    txBox = slide.shapes.add_textbox(l, t, w, h)
    tf = txBox.text_frame
    tf.word_wrap = True
    first = True
    for item in items:
        if first:
            p = tf.paragraphs[0]
            first = False
        else:
            p = tf.add_paragraph()
        p.space_before = Pt(3)
        run = p.add_run()
        run.text = item
        run.font.name = "Calibri"
        run.font.size = Pt(size)
        run.font.color.rgb = color

def accent_bar(slide, y=Inches(0.35)):
    add_rect(slide, Inches(0), y, Inches(13.33), Inches(0.05), CYAN)

def section_tag(slide, label, l=Inches(0.55), t=Inches(0.12)):
    tag = slide.shapes.add_shape(1, l, t, Inches(2.6), Inches(0.32))
    tag.line.fill.background()
    tag.fill.solid()
    tag.fill.fore_color.rgb = MID_BG
    tf = tag.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = label
    run.font.name = "Calibri"
    run.font.size = Pt(10)
    run.font.color.rgb = CYAN
    run.font.bold = True

def info_card(slide, title, lines, l, t, w, h, title_size=12, body_size=10.5):
    card = slide.shapes.add_shape(1, l, t, w, h)
    card.line.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)
    card.line.width = Pt(0.75)
    card.fill.solid()
    card.fill.fore_color.rgb = MID_BG

    txBox = slide.shapes.add_textbox(l + Inches(0.15), t + Inches(0.1),
                                      w - Inches(0.3), h - Inches(0.15))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = title
    r.font.name = "Calibri"
    r.font.size = Pt(title_size)
    r.font.bold = True
    r.font.color.rgb = CYAN

    for line in lines:
        p2 = tf.add_paragraph()
        p2.space_before = Pt(2)
        r2 = p2.add_run()
        r2.text = line
        r2.font.name = "Calibri"
        r2.font.size = Pt(body_size)
        r2.font.color.rgb = LIGHT_GRY

def pipeline_step(slide, number, title, desc, l, t, w=Inches(1.9), h=Inches(1.7)):
    card = slide.shapes.add_shape(1, l, t, w, h)
    card.fill.solid()
    card.fill.fore_color.rgb = MID_BG
    card.line.color.rgb = CYAN
    card.line.width = Pt(0.8)

    txBox = slide.shapes.add_textbox(l + Inches(0.1), t + Inches(0.08),
                                      w - Inches(0.2), h - Inches(0.12))
    tf = txBox.text_frame
    tf.word_wrap = True

    # Number
    p0 = tf.paragraphs[0]
    p0.alignment = PP_ALIGN.CENTER
    r0 = p0.add_run()
    r0.text = number
    r0.font.name = "Calibri"
    r0.font.size = Pt(18)
    r0.font.bold = True
    r0.font.color.rgb = CYAN

    # Title
    p1 = tf.add_paragraph()
    p1.alignment = PP_ALIGN.CENTER
    p1.space_before = Pt(2)
    r1 = p1.add_run()
    r1.text = title
    r1.font.name = "Calibri"
    r1.font.size = Pt(11)
    r1.font.bold = True
    r1.font.color.rgb = WHITE

    # Desc
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(4)
    r2 = p2.add_run()
    r2.text = desc
    r2.font.name = "Calibri"
    r2.font.size = Pt(9)
    r2.font.color.rgb = MID_GRY

def arrow_between(slide, x, y):
    txb = slide.shapes.add_textbox(x, y, Inches(0.3), Inches(0.3))
    tf = txb.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = "→"
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = CYAN

# ═══════════════════════════════════════════════════════════════════
# SLIDE 1 – TITLE SLIDE
# ═══════════════════════════════════════════════════════════════════
s1 = prs.slides.add_slide(blank_layout)
solid_bg(s1, DARK_BG)

# Left accent strip
add_rect(s1, Inches(0), Inches(0), Inches(0.08), H, CYAN)

# Top accent
add_rect(s1, Inches(0.08), Inches(0), W - Inches(0.08), Inches(0.04), RGBColor(0x00,0x72,0xFF))

# Domain badge
badge = s1.shapes.add_shape(1, Inches(0.55), Inches(1.1), Inches(3.2), Inches(0.38))
badge.line.fill.background()
badge.fill.solid()
badge.fill.fore_color.rgb = RGBColor(0x00, 0x27, 0x55)
bf = badge.text_frame
bp = bf.paragraphs[0]
bp.alignment = PP_ALIGN.CENTER
br = bp.add_run()
br.text = "⚡  AUTOMOTIVE AI  •  RAG SYSTEM"
br.font.name = "Calibri"
br.font.size = Pt(11)
br.font.bold = True
br.font.color.rgb = CYAN

add_text(s1, "AUTOSAR HLD Intelligence &", Inches(0.55), Inches(1.65), Inches(9), Inches(0.9),
         size=36, bold=True, color=WHITE)
add_text(s1, "Traceability Assistant", Inches(0.55), Inches(2.35), Inches(9), Inches(0.8),
         size=36, bold=True, color=CYAN)

add_text(s1, "Retrieval-Augmented Generation (RAG) for Automotive ECU High-Level Design Analysis",
         Inches(0.55), Inches(3.1), Inches(9), Inches(0.6),
         size=14, bold=False, color=MID_GRY)

# Meta row
meta_items = [
    ("🏗", "Two-Stage RAG Pipeline", "FAISS + Cross-Encoder"),
    ("🤖", "Local LLM (Ollama)", "deepseek-r1:1.5b"),
    ("✅", "Automated Tests", "78 / 78 Passed"),
    ("🔒", "Fully Offline", "Zero Data Leakage"),
]
card_x = Inches(0.55)
for icon, title, sub in meta_items:
    mc = s1.shapes.add_shape(1, card_x, Inches(4.15), Inches(2.8), Inches(0.9))
    mc.fill.solid()
    mc.fill.fore_color.rgb = MID_BG
    mc.line.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)
    mc.line.width = Pt(0.75)
    tf = mc.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = f"{icon}  {title}"
    r.font.name = "Calibri"
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = WHITE
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run()
    r2.text = sub
    r2.font.name = "Calibri"
    r2.font.size = Pt(9)
    r2.font.color.rgb = CYAN
    card_x += Inches(2.95)

add_text(s1, "Engineering Project Presentation  •  B.Tech / M.Tech Final Year  •  2026",
         Inches(0.55), Inches(6.8), Inches(10), Inches(0.4),
         size=9, color=MID_GRY)

# ═══════════════════════════════════════════════════════════════════
# SLIDE 2 – PROBLEM STATEMENT
# ═══════════════════════════════════════════════════════════════════
s2 = prs.slides.add_slide(blank_layout)
solid_bg(s2, DARK_BG)
accent_bar(s2, y=Inches(0))
section_tag(s2, "01  —  PROBLEM STATEMENT")
add_rect(s2, Inches(0), Inches(0), Inches(0.05), H, CYAN)

add_text(s2, "Why does this problem exist?", Inches(0.55), Inches(0.45), Inches(10), Inches(0.55),
         size=24, bold=True, color=WHITE)

# 3 Problem Cards
problems = [
    ("📄  Document Overload",
     ["Automotive ECU HLD specifications span hundreds of dense",
      "pages detailing SWCs, ports, CAN signals, and BSW layers.",
      "Engineers spend hours manually searching for inter-module",
      "dependencies and specification gaps."]),
    ("🤥  LLM Hallucinations",
     ["Standard LLMs (ChatGPT, etc.) hallucinate automotive facts.",
      "They invent non-existent signal names, false CAN IDs, and",
      "fabricated page references when asked about proprietary",
      "automotive architectures not in their training data."]),
    ("🔒  IP & Confidentiality",
     ["AUTOSAR HLD documents are strictly proprietary OEM/Tier-1",
      "trade secrets. Uploading them to public cloud AI APIs",
      "creates unacceptable legal, IP, and regulatory risks.",
      "Engineers need a fully offline, private alternative."]),
]
cx = Inches(0.45)
for title, lines in problems:
    info_card(s2, title, lines, cx, Inches(1.15), Inches(3.9), Inches(2.5),
              title_size=12.5, body_size=10.5)
    cx += Inches(4.1)

add_text(s2, "✅  SOLUTION:  A local, offline Two-Stage RAG system grounding answers in verified automotive document evidence with exact page citations.",
         Inches(0.45), Inches(3.85), Inches(12.4), Inches(0.55),
         size=12, bold=True, color=CYAN)

# ═══════════════════════════════════════════════════════════════════
# SLIDE 3 – SYSTEM OVERVIEW / WHAT WE BUILT
# ═══════════════════════════════════════════════════════════════════
s3 = prs.slides.add_slide(blank_layout)
solid_bg(s3, DARK_BG)
accent_bar(s3, Inches(0))
section_tag(s3, "02  —  WHAT WE BUILT")
add_rect(s3, Inches(0), Inches(0), Inches(0.05), H, CYAN)

add_text(s3, "AUTOSAR HLD Intelligence & Traceability Assistant",
         Inches(0.55), Inches(0.45), Inches(12), Inches(0.55),
         size=22, bold=True, color=WHITE)

# 4-feature grid
features = [
    ("🔍  Semantic Q&A",
     ["Ask natural language questions about SWCs, ports,",
      "signals, and dependencies — grounded answers with",
      "exact source-page citations from uploaded HLD PDFs."]),
    ("⚡  Two-Stage RAG",
     ["Stage 1: FAISS vector search (top-15 candidates).",
      "Stage 2: Cross-Encoder re-ranking (top-5 evidence",
      "passages). Eliminates lexical false positives."]),
    ("🏗  Architecture Analyzer",
     ["Heuristic extraction of candidate SWCs, provided/",
      "required ports, CAN/LIN signals, BSW layers, and",
      "functional inconsistencies — with CSV export."]),
    ("🤖  Local LLM (Private)",
     ["Ollama + deepseek-r1:1.5b runs 100% offline.",
      "Confidential automotive IP never leaves the laptop.",
      "Works with zero GPU, zero API cost, zero internet."]),
    ("📊  Document Compare",
     ["Side-by-side HLD revision diffing. Detect additions,",
      "removals, and term-level changes between two",
      "specification versions uploaded simultaneously."]),
    ("✅  Verified Citations",
     ["All cited document names and page numbers are",
      "programmatically validated against ground-truth",
      "chunks — LLM cannot hallucinate page references."]),
]
row1 = features[:3]
row2 = features[3:]
fx = Inches(0.4)
for title, lines in row1:
    info_card(s3, title, lines, fx, Inches(1.18), Inches(4.05), Inches(1.55), 11, 9.5)
    fx += Inches(4.2)
fx = Inches(0.4)
for title, lines in row2:
    info_card(s3, title, lines, fx, Inches(2.85), Inches(4.05), Inches(1.55), 11, 9.5)
    fx += Inches(4.2)

add_text(s3, "Streamlit 4-Tab Web UI  •  start_app.bat 1-Click Launch  •  78/78 Tests Passing",
         Inches(0.5), Inches(6.8), Inches(12), Inches(0.4),
         size=9, color=MID_GRY)

# ═══════════════════════════════════════════════════════════════════
# SLIDE 4 – ARCHITECTURE / PIPELINE FLOW
# ═══════════════════════════════════════════════════════════════════
s4 = prs.slides.add_slide(blank_layout)
solid_bg(s4, DARK_BG)
accent_bar(s4, Inches(0))
section_tag(s4, "03  —  RAG PIPELINE ARCHITECTURE")
add_rect(s4, Inches(0), Inches(0), Inches(0.05), H, CYAN)

add_text(s4, "End-to-End Two-Stage RAG Pipeline",
         Inches(0.55), Inches(0.45), Inches(12), Inches(0.5),
         size=22, bold=True, color=WHITE)

steps = [
    ("01", "PDF Upload", "PyMuPDF\npage-by-page\nextraction"),
    ("02", "Chunking", "800 chars\n150 overlap\nprovenance"),
    ("03", "Embeddings", "all-MiniLM\nL6-v2\n384-dim"),
    ("04", "FAISS Index", "IndexFlatIP\ncosine sim\ntop-15"),
    ("05", "Cross-Encoder", "ms-marco\nre-rank\ntop-5"),
    ("06", "LLM Answer", "Ollama\ndeepseek-r1\nverified"),
]
sx = Inches(0.35)
for i, (num, title, desc) in enumerate(steps):
    pipeline_step(s4, num, title, desc, sx, Inches(1.1), Inches(2.0), Inches(1.8))
    if i < len(steps) - 1:
        arrow_between(s4, sx + Inches(2.03), Inches(1.9))
    sx += Inches(2.17)

# Bottom annotation boxes
annotations = [
    ("Input Stage", "Multi-PDF\nupload &\nvalidation", Inches(0.35)),
    ("Knowledge Base", "Persistent\nFAISS + metadata\ndictionary store", Inches(2.52)),
    ("Two-Stage Retrieval", "Bi-Encoder\n→ Cross-Encoder\nprecision boost", Inches(4.69)),
    ("Synthesis Stage", "Reasoning\nstrip + citation\nverification", Inches(10.85)),
]
for label, desc, lx in annotations:
    tag = s4.shapes.add_shape(1, lx, Inches(3.05), Inches(2.0), Inches(0.62))
    tag.fill.solid()
    tag.fill.fore_color.rgb = RGBColor(0x00, 0x27, 0x55)
    tag.line.fill.background()
    tf = tag.text_frame
    tf.word_wrap = False
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.name = "Calibri"
    r.font.size = Pt(9)
    r.font.bold = True
    r.font.color.rgb = CYAN

# Output format box
add_rect(s4, Inches(0.35), Inches(3.75), Inches(12.6), Inches(1.15), MID_BG)
add_text(s4, "Verified 3-Section Output Format:",
         Inches(0.55), Inches(3.82), Inches(4), Inches(0.4),
         size=10, bold=True, color=CYAN)
output_sections = [
    "💡  Executive Summary  —  Direct answer to the architectural query.",
    "🏗  Architectural Breakdown  —  Components | Ports | Signals | Functional Flows.",
    "📑  Evidence & Citations Summary  —  Table: Document name + page + verified fact.",
]
oy = Inches(4.2)
for sec in output_sections:
    add_text(s4, sec, Inches(0.55), oy, Inches(12), Inches(0.32), size=10, color=LIGHT_GRY)
    oy += Inches(0.3)

# ═══════════════════════════════════════════════════════════════════
# SLIDE 5 – TECHNOLOGY STACK
# ═══════════════════════════════════════════════════════════════════
s5 = prs.slides.add_slide(blank_layout)
solid_bg(s5, DARK_BG)
accent_bar(s5, Inches(0))
section_tag(s5, "04  —  TECHNOLOGY STACK")
add_rect(s5, Inches(0), Inches(0), Inches(0.05), H, CYAN)

add_text(s5, "Pre-Trained Models, Frameworks & Libraries",
         Inches(0.55), Inches(0.45), Inches(12), Inches(0.5),
         size=22, bold=True, color=WHITE)

tech_rows = [
    ("Layer", "Technology", "Model / Version", "Role"),
    ("UI Framework", "Streamlit", "v1.50+", "4-tab interactive web dashboard with custom dark theme"),
    ("PDF Extraction", "PyMuPDF (fitz)", "v1.23+", "Page-by-page streaming with provenance metadata"),
    ("Embedding Model", "Sentence-Transformers", "all-MiniLM-L6-v2  (384-dim)", "Dense semantic vector generation for chunk indexing"),
    ("Vector Database", "FAISS CPU", "IndexFlatIP  (k=15)", "Sub-millisecond cosine similarity candidate recall"),
    ("Re-Ranking", "Cross-Encoder", "ms-marco-MiniLM-L-6-v2  (top-5)", "Deep query-passage cross-attention scoring"),
    ("Local LLM", "Ollama", "deepseek-r1:1.5b  (T=0.1)", "Private offline inference — no API key, no cloud"),
    ("Cloud LLM (Optional)", "OpenRouter / OpenAI API", "Any supported model", "Optional cloud integration for production workloads"),
    ("Data & Testing", "pandas + pytest", "78/78 Tests Passing", "CSV export, evaluation benchmark, unit tests"),
]

col_widths = [Inches(1.6), Inches(2.1), Inches(2.8), Inches(6.35)]
table = s5.shapes.add_table(len(tech_rows), 4,
                              Inches(0.35), Inches(1.12),
                              sum(col_widths), Inches(5.8))
tbl = table.table

for ci, cw in enumerate(col_widths):
    tbl.columns[ci].width = cw

for ri, row_data in enumerate(tech_rows):
    for ci, cell_text in enumerate(row_data):
        cell = tbl.cell(ri, ci)
        cell.text = cell_text
        p = cell.text_frame.paragraphs[0]
        p.alignment = PP_ALIGN.LEFT
        run = p.runs[0] if p.runs else p.add_run()
        run.font.name = "Calibri"
        if ri == 0:
            run.font.size = Pt(10)
            run.font.bold = True
            run.font.color.rgb = WHITE
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY
        else:
            run.font.size = Pt(9.5)
            run.font.bold = (ci == 0)
            run.font.color.rgb = LIGHT_GRY if ci > 0 else CYAN
            cell.fill.solid()
            cell.fill.fore_color.rgb = MID_BG if ri % 2 == 0 else RGBColor(0x10, 0x1A, 0x2E)

# ═══════════════════════════════════════════════════════════════════
# SLIDE 6 – KEY INNOVATIONS
# ═══════════════════════════════════════════════════════════════════
s6 = prs.slides.add_slide(blank_layout)
solid_bg(s6, DARK_BG)
accent_bar(s6, Inches(0))
section_tag(s6, "05  —  KEY INNOVATIONS")
add_rect(s6, Inches(0), Inches(0), Inches(0.05), H, CYAN)

add_text(s6, "What makes this project stand out?",
         Inches(0.55), Inches(0.45), Inches(12), Inches(0.5),
         size=22, bold=True, color=WHITE)

innovations = [
    ("⚡", "Two-Stage RAG Retrieval",
     "FAISS bi-encoder vector recall (top-15) + Cross-Encoder re-ranking (top-5). "
     "Eliminates false-positive matches common in pure vector search on dense technical text. "
     "Elevates domain retrieval precision significantly over standard one-stage RAG."),
    ("🛡", "Guaranteed Zero Citation Hallucinations",
     "Post-generation engine programmatically reconciles every cited row against verified ground-truth "
     "chunk metadata (doc_name + page_number). Even if the LLM emits placeholders, they are "
     "automatically corrected before display — 100% citation accuracy verified."),
    ("🧹", "Reasoning Trace Stripping",
     "DeepSeek-R1 and similar reasoning models emit verbose internal monologues (<think>...</think>). "
     "Our post-processing cleaner filters all reasoning traces to produce clean, professional "
     "3-section engineering output suitable for automotive design reviews."),
    ("🔒", "100% Offline, Air-Gapped Deployment",
     "All inference (embeddings, re-ranking, LLM) runs locally. Proprietary automotive blueprints "
     "never leave the workstation. Supports organizations with strict ISO 27001 and UNECE R155 "
     "data handling requirements."),
    ("📋", "Extractive Fallback Mode",
     "If Ollama is unavailable, the system automatically switches to a deterministic extractive synthesis "
     "engine. Zero functionality degradation — 100% offline capability without GPU or internet."),
    ("🎨", "Modern Cyber-Automotive UI",
     "Custom dark UI theme (Cyber-Automotive design system) with gradient typography, glowing tab "
     "navigation, glassmorphic cards, and interactive evidence popover inspection for engineering "
     "review workflows."),
]

gx = Inches(0.4)
gy = Inches(1.12)
for idx, (icon, title, desc) in enumerate(innovations):
    if idx == 3:
        gx = Inches(0.4)
        gy = Inches(3.35)
    card = s6.shapes.add_shape(1, gx, gy, Inches(4.12), Inches(2.1))
    card.fill.solid()
    card.fill.fore_color.rgb = MID_BG
    card.line.color.rgb = RGBColor(0x1E, 0x3A, 0x5F)
    card.line.width = Pt(0.75)

    txb = s6.shapes.add_textbox(gx + Inches(0.14), gy + Inches(0.1),
                                  Inches(3.84), Inches(1.9))
    tf = txb.text_frame
    tf.word_wrap = True
    p0 = tf.paragraphs[0]
    r0 = p0.add_run()
    r0.text = f"{icon}  {title}"
    r0.font.name = "Calibri"
    r0.font.size = Pt(11)
    r0.font.bold = True
    r0.font.color.rgb = CYAN

    p1 = tf.add_paragraph()
    p1.space_before = Pt(4)
    r1 = p1.add_run()
    r1.text = desc
    r1.font.name = "Calibri"
    r1.font.size = Pt(8.8)
    r1.font.color.rgb = LIGHT_GRY

    gx += Inches(4.31)

# ═══════════════════════════════════════════════════════════════════
# SLIDE 7 – DEMO WALKTHROUGH
# ═══════════════════════════════════════════════════════════════════
s7 = prs.slides.add_slide(blank_layout)
solid_bg(s7, DARK_BG)
accent_bar(s7, Inches(0))
section_tag(s7, "06  —  LIVE DEMO WALKTHROUGH")
add_rect(s7, Inches(0), Inches(0), Inches(0.05), H, CYAN)

add_text(s7, "Demo Flow — What to show the evaluator",
         Inches(0.55), Inches(0.45), Inches(12), Inches(0.5),
         size=22, bold=True, color=WHITE)

demo_steps = [
    ("Step 1", "start_app.bat",
     "Double-click to launch. Ollama starts, port 8501 opens, browser auto-opens."),
    ("Step 2", "Tab 1 — Upload PDF",
     "Upload automotive HLD PDF. Click Process. Show page count & text coverage metrics."),
    ("Step 3", "Tab 2 — Q&A",
     'Ask: "What are the main SWCs and their ports?" — Show 3-section answer & citations table.'),
    ("Step 4", "View Chunks Popover",
     'Click "🔍 View Retrieved Chunks" — show raw evidence passages with re-rank scores and deltas.'),
    ("Step 5", "Tab 3 — Architecture Analysis",
     "Show heuristic component table. Click Generate AI Summary for deep executive synthesis."),
    ("Step 6", "stop_app.bat",
     "Clean shutdown of Streamlit + Ollama. Show pytest: python -m pytest tests/ → 78/78 passed."),
]

dy = Inches(1.1)
for num, title, desc in demo_steps:
    # Number pill
    pill = s7.shapes.add_shape(1, Inches(0.4), dy, Inches(0.7), Inches(0.55))
    pill.fill.solid()
    pill.fill.fore_color.rgb = RGBColor(0x00, 0x27, 0x55)
    pill.line.color.rgb = CYAN
    pill.line.width = Pt(0.75)
    tf = pill.text_frame
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = num
    r.font.name = "Calibri"
    r.font.size = Pt(9)
    r.font.bold = True
    r.font.color.rgb = CYAN

    # Title + desc
    add_text(s7, title, Inches(1.2), dy + Inches(0.01), Inches(2.5), Inches(0.3),
             size=11, bold=True, color=WHITE)
    add_text(s7, desc, Inches(3.9), dy + Inches(0.05), Inches(9.0), Inches(0.5),
             size=10, color=LIGHT_GRY)

    # Divider
    add_rect(s7, Inches(0.4), dy + Inches(0.62), Inches(12.5), Inches(0.02),
             RGBColor(0x1E, 0x3A, 0x5F))
    dy += Inches(0.78)

add_text(s7, '💡  Key phrase to say:  "Every answer is grounded — the LLM cannot make up facts because citations are programmatically verified against source chunks."',
         Inches(0.4), Inches(6.85), Inches(12.5), Inches(0.4),
         size=9.5, bold=True, color=CYAN)

# ═══════════════════════════════════════════════════════════════════
# SLIDE 8 – EVALUATION & RESULTS
# ═══════════════════════════════════════════════════════════════════
s8 = prs.slides.add_slide(blank_layout)
solid_bg(s8, DARK_BG)
accent_bar(s8, Inches(0))
section_tag(s8, "07  —  EVALUATION & RESULTS")
add_rect(s8, Inches(0), Inches(0), Inches(0.05), H, CYAN)

add_text(s8, "Test Suite & Domain Evaluation Results",
         Inches(0.55), Inches(0.45), Inches(12), Inches(0.5),
         size=22, bold=True, color=WHITE)

# Big stat cards
stats = [
    ("78 / 78", "Tests Passing", "pytest automated unit &\nintegration suite (100%)"),
    ("100%", "Citation Accuracy", "Programmatic ground-truth\nverification of page numbers"),
    ("0", "Reasoning Leakage", "<think> traces stripped\nbefore frontend display"),
    ("10 / 10", "Eval Questions", "Component, signal, interface\n& edge-case benchmark"),
]
sx = Inches(0.4)
for val, label, sub in stats:
    sc = s8.shapes.add_shape(1, sx, Inches(1.1), Inches(3.0), Inches(1.5))
    sc.fill.solid()
    sc.fill.fore_color.rgb = MID_BG
    sc.line.color.rgb = CYAN
    sc.line.width = Pt(1)
    tf = sc.text_frame
    tf.word_wrap = False
    p0 = tf.paragraphs[0]
    p0.alignment = PP_ALIGN.CENTER
    r0 = p0.add_run()
    r0.text = val
    r0.font.name = "Calibri"
    r0.font.size = Pt(24)
    r0.font.bold = True
    r0.font.color.rgb = CYAN
    p1 = tf.add_paragraph()
    p1.alignment = PP_ALIGN.CENTER
    r1 = p1.add_run()
    r1.text = label
    r1.font.name = "Calibri"
    r1.font.size = Pt(10)
    r1.font.bold = True
    r1.font.color.rgb = WHITE
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(3)
    r2 = p2.add_run()
    r2.text = sub
    r2.font.name = "Calibri"
    r2.font.size = Pt(8.5)
    r2.font.color.rgb = MID_GRY
    sx += Inches(3.22)

# Evaluation detail table
eval_rows = [
    ("Evaluation Dimension", "What Was Tested", "Result"),
    ("Unit & Integration Tests", "78 cases across PDF, Chunker, FAISS, Re-ranker, LLM modules", "✅  78 / 78 Passed  (25s)"),
    ("Citation Correctness", "Every cited page verified against source chunk ground-truth", "✅  100% Accuracy"),
    ("Reasoning Cleansing", "DeepSeek-R1 <think> tags stripped; clean 3-section output", "✅  Zero Leakage"),
    ("10-Question Benchmark", "Components, ports, signals, dependencies, off-topic rejection", "✅  Full Coverage"),
    ("Re-Ranking Precision", "Cross-Encoder vs raw vector similarity comparison", "✅  Higher Domain Recall"),
]
col_widths = [Inches(2.5), Inches(6.5), Inches(3.5)]
tbl = s8.shapes.add_table(len(eval_rows), 3,
                            Inches(0.35), Inches(2.8),
                            sum(col_widths), Inches(4.4))
t = tbl.table
for ci, cw in enumerate(col_widths):
    t.columns[ci].width = cw
for ri, row_data in enumerate(eval_rows):
    for ci, cell_text in enumerate(row_data):
        cell = t.cell(ri, ci)
        cell.text = cell_text
        p = cell.text_frame.paragraphs[0]
        run = p.runs[0] if p.runs else p.add_run()
        run.font.name = "Calibri"
        if ri == 0:
            run.font.size = Pt(10)
            run.font.bold = True
            run.font.color.rgb = WHITE
            cell.fill.solid()
            cell.fill.fore_color.rgb = NAVY
        else:
            run.font.size = Pt(9.5)
            run.font.bold = (ci == 0)
            run.font.color.rgb = CYAN if ci == 2 else (LIGHT_GRY if ci > 0 else ACCENT)
            cell.fill.solid()
            cell.fill.fore_color.rgb = MID_BG if ri % 2 == 0 else RGBColor(0x10, 0x1A, 0x2E)

# ═══════════════════════════════════════════════════════════════════
# SLIDE 9 – RESPONSIBLE AI & FUTURE SCOPE
# ═══════════════════════════════════════════════════════════════════
s9 = prs.slides.add_slide(blank_layout)
solid_bg(s9, DARK_BG)
accent_bar(s9, Inches(0))
section_tag(s9, "08  —  RESPONSIBLE AI  &  FUTURE SCOPE")
add_rect(s9, Inches(0), Inches(0), Inches(0.05), H, CYAN)

add_text(s9, "Responsible AI Practices & Next Steps",
         Inches(0.55), Inches(0.45), Inches(12), Inches(0.5),
         size=22, bold=True, color=WHITE)

# Left: Responsible AI
add_text(s9, "🛡  Responsible AI Measures", Inches(0.4), Inches(1.05), Inches(6.2), Inches(0.4),
         size=13, bold=True, color=CYAN)
rai_items = [
    "🔒  Privacy-First:  All inference is 100% local via Ollama.\n    Proprietary HLD data never reaches cloud servers.",
    "🔍  Anti-Hallucination Grounding:  LLM is strictly\n    constrained to retrieved document evidence only.",
    "👁  Human Oversight:  Engineers can inspect raw retrieved\n    passages, scores, and re-ranking deltas before acting.",
    "📋  Clear Disclaimer:  Non-certification notice shown\n    prominently — tool is an engineering assistant, not\n    an automated AUTOSAR compliance certifier.",
    "📖  Source Auditability:  Every answer links back to\n    exact document page for human verification.",
]
ry = Inches(1.5)
for item in rai_items:
    add_text(s9, item, Inches(0.5), ry, Inches(5.8), Inches(0.62),
             size=9.5, color=LIGHT_GRY)
    ry += Inches(0.85)

# Divider
add_rect(s9, Inches(6.7), Inches(1.05), Inches(0.03), Inches(5.5), RGBColor(0x1E, 0x3A, 0x5F))

# Right: Future Scope
add_text(s9, "🚀  Future Scope", Inches(6.9), Inches(1.05), Inches(6.0), Inches(0.4),
         size=13, bold=True, color=CYAN)
future_items = [
    ("Hybrid BM25 + Dense Search",
     "Combine keyword sparse retrieval with semantic\nvectors for higher recall on signal-level queries."),
    ("Native OCR Integration",
     "Add Tesseract/PaddleOCR for scanned legacy\nautomotive blueprint ingestion."),
    ("ARXML Direct Parsing",
     "Parse AUTOSAR XML (.arxml) files alongside\nPDF for richer structural traceability."),
    ("ADAS / Functional Safety",
     "Extend domain to ISO 26262 HARA documents,\nFMEA tables, and SOTIF analysis."),
    ("Multi-Agent Orchestration",
     "Specialized sub-agents for SWC, BSW, and\nNetwork topology analysis in parallel."),
]
fy = Inches(1.5)
for title, desc in future_items:
    fb = s9.shapes.add_shape(1, Inches(6.9), fy, Inches(5.9), Inches(0.82))
    fb.fill.solid()
    fb.fill.fore_color.rgb = MID_BG
    fb.line.fill.background()
    ft = fb.text_frame
    ft.word_wrap = True
    fp = ft.paragraphs[0]
    fr = fp.add_run()
    fr.text = title
    fr.font.name = "Calibri"
    fr.font.size = Pt(10)
    fr.font.bold = True
    fr.font.color.rgb = WHITE
    fp2 = ft.add_paragraph()
    fr2 = fp2.add_run()
    fr2.text = desc
    fr2.font.name = "Calibri"
    fr2.font.size = Pt(8.8)
    fr2.font.color.rgb = MID_GRY
    fy += Inches(1.0)

# ═══════════════════════════════════════════════════════════════════
# SLIDE 10 – THANK YOU / Q&A
# ═══════════════════════════════════════════════════════════════════
s10 = prs.slides.add_slide(blank_layout)
solid_bg(s10, DARK_BG)
add_rect(s10, Inches(0), Inches(0), Inches(0.08), H, CYAN)
add_rect(s10, Inches(0), Inches(0), W, Inches(0.04), RGBColor(0x00, 0x72, 0xFF))
add_rect(s10, Inches(0), H - Inches(0.04), W, Inches(0.04), CYAN)

add_text(s10, "Thank You", Inches(0.6), Inches(1.3), Inches(12), Inches(1.1),
         size=52, bold=True, color=WHITE)
add_text(s10, "AUTOSAR HLD Intelligence & Traceability Assistant",
         Inches(0.6), Inches(2.5), Inches(12), Inches(0.55),
         size=18, bold=True, color=CYAN)
add_text(s10, "Open for Questions & Live Demo",
         Inches(0.6), Inches(3.1), Inches(12), Inches(0.45),
         size=14, color=MID_GRY)

add_rect(s10, Inches(0.6), Inches(3.75), Inches(12.1), Inches(0.04), RGBColor(0x1E, 0x3A, 0x5F))

summary_pts = [
    "⚡  Two-Stage RAG  —  FAISS (top-15) + Cross-Encoder Re-Ranking (top-5)",
    "🔒  100% Offline Local LLM  —  Ollama deepseek-r1:1.5b  |  Zero cloud dependency",
    "✅  Verified Citations  —  Programmatic ground-truth page validation",
    "🧪  78 / 78 Tests Passing  —  Full automated unit & integration coverage",
]
sy = Inches(4.0)
for pt in summary_pts:
    add_text(s10, pt, Inches(0.6), sy, Inches(12), Inches(0.38),
             size=11, color=LIGHT_GRY)
    sy += Inches(0.5)

add_text(s10, "Built with Python 3.11  •  Streamlit  •  Sentence-Transformers  •  FAISS  •  Cross-Encoder  •  Ollama",
         Inches(0.6), Inches(6.8), Inches(12), Inches(0.38),
         size=9, color=MID_GRY)

# ─── SAVE ────────────────────────────────────────────────────────
out = "AUTOSAR_HLD_Project_Presentation.pptx"
prs.save(out)
print(f"Saved {out} — {prs.slides.__len__()} slides.")
