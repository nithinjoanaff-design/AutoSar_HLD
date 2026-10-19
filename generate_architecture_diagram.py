"""
generate_architecture_diagram.py
---------------------------------
Generates an architecture diagram image for the AUTOSAR HLD Assistant project.
Saved to: Documentation/architecture_diagram.png
"""

import os

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

def draw_box(ax, x, y, w, h, label, sublabel="", color="#1e3a5f", text_color="white", fontsize=9):
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle="round,pad=0.02",
                         facecolor=color, edgecolor="#00D2FF", linewidth=1.5)
    ax.add_patch(box)
    cx, cy = x + w / 2, y + h / 2
    if sublabel:
        ax.text(cx, cy + 0.018, label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=text_color)
        ax.text(cx, cy - 0.018, sublabel, ha="center", va="center",
                fontsize=fontsize - 1.5, color="#a0c4d8", style="italic")
    else:
        ax.text(cx, cy, label, ha="center", va="center",
                fontsize=fontsize, fontweight="bold", color=text_color)

def draw_arrow(ax, x1, y1, x2, y2, color="#00D2FF"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5))

def main():
    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor("#0B111E")
    ax.set_facecolor("#0B111E")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Title
    ax.text(0.5, 0.96, "AUTOSAR HLD Intelligence & Traceability Assistant",
            ha="center", va="center", fontsize=14, fontweight="bold", color="#00D2FF")
    ax.text(0.5, 0.925, "System Architecture Overview",
            ha="center", va="center", fontsize=10, color="#a0c4d8")

    # ── Row 1: Input ──
    draw_box(ax, 0.03, 0.80, 0.20, 0.07, "PDF Upload", "Streamlit UI (Tab 1)", color="#0d2137")
    draw_box(ax, 0.40, 0.80, 0.20, 0.07, "User Query", "Streamlit UI (Tab 2)", color="#0d2137")
    draw_box(ax, 0.77, 0.80, 0.20, 0.07, "AI Summary", "Streamlit UI (Tab 3)", color="#0d2137")

    # ── Row 2: Processing ──
    draw_box(ax, 0.03, 0.64, 0.20, 0.07, "pdf_processor.py", "PyMuPDF page extraction", color="#152033")
    draw_box(ax, 0.03, 0.54, 0.20, 0.07, "chunker.py", "800 char / 150 overlap", color="#152033")
    draw_box(ax, 0.03, 0.44, 0.20, 0.07, "embeddings.py", "all-MiniLM-L6-v2 (384d)", color="#152033")
    draw_box(ax, 0.03, 0.34, 0.20, 0.07, "vector_store.py", "FAISS IndexFlatIP", color="#152033")

    # ── Row 2: Retrieval ──
    draw_box(ax, 0.40, 0.64, 0.20, 0.07, "vector_store.py", "Top-15 FAISS search", color="#152033")
    draw_box(ax, 0.40, 0.54, 0.20, 0.07, "reranker.py", "CrossEncoder → Top-5", color="#152033")
    draw_box(ax, 0.40, 0.44, 0.20, 0.07, "llm_provider.py", "deepseek-r1:1.5b (Ollama)", color="#152033")
    draw_box(ax, 0.40, 0.34, 0.20, 0.07, "Safety Guards", "Harmful Blocker + Not-Found", color="#1a0a0a")

    # ── Row 2: Summary ──
    draw_box(ax, 0.77, 0.64, 0.20, 0.07, "rag_pipeline.py", "summarize_document()", color="#152033")
    draw_box(ax, 0.77, 0.54, 0.20, 0.07, "llm_provider.py", "SUMMARY_PROMPT", color="#152033")

    # ── Row 3: Output ──
    draw_box(ax, 0.03, 0.20, 0.20, 0.07, "FAISS Index", "data/faiss_index/", color="#0a1a10")
    draw_box(ax, 0.40, 0.20, 0.20, 0.07, "3-Section Answer", "Summary + Breakdown + Citations", color="#0a1a10")
    draw_box(ax, 0.77, 0.20, 0.20, 0.07, "AI Architecture", "Document Summary Output", color="#0a1a10")

    # ── Arrows: Left column (indexing flow) ──
    for y_src, y_dst in [(0.80, 0.71), (0.64, 0.61), (0.54, 0.51), (0.44, 0.41), (0.34, 0.27)]:
        draw_arrow(ax, 0.13, y_src, 0.13, y_dst)

    # ── Arrows: Middle column (query flow) ──
    for y_src, y_dst in [(0.80, 0.71), (0.64, 0.61), (0.54, 0.51), (0.44, 0.41), (0.34, 0.27)]:
        draw_arrow(ax, 0.50, y_src, 0.50, y_dst)

    # ── Arrows: Right column (summary flow) ──
    for y_src, y_dst in [(0.80, 0.71), (0.64, 0.61), (0.54, 0.27)]:
        draw_arrow(ax, 0.87, y_src, 0.87, y_dst)

    # ── Cross-link: FAISS index feeds into retrieval ──
    draw_arrow(ax, 0.23, 0.375, 0.40, 0.375)
    ax.text(0.315, 0.385, "vector search", ha="center", fontsize=7, color="#a0c4d8")

    # ── Legend ──
    legend_items = [
        mpatches.Patch(color="#0d2137", label="Streamlit UI Layer"),
        mpatches.Patch(color="#152033", label="Processing / ML Layer"),
        mpatches.Patch(color="#0a1a10", label="Output / Storage Layer"),
        mpatches.Patch(color="#1a0a0a", label="Safety Guard"),
    ]
    ax.legend(handles=legend_items, loc="lower left", fontsize=8,
              facecolor="#0B111E", edgecolor="#00D2FF", labelcolor="white",
              bbox_to_anchor=(0.01, 0.01))

    os.makedirs("Documentation", exist_ok=True)
    out_path = "Documentation/architecture_diagram.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close()
    print(f"Saved: {out_path}")

if __name__ == "__main__":
    if HAS_MPL:
        main()
    else:
        print("matplotlib not installed. Run: pip install matplotlib")
