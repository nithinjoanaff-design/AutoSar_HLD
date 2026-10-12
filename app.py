"""
app.py
------
AUTOSAR HLD Document Analysis Assistant – Streamlit Web Application
"""

from __future__ import annotations

import io
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Ensure src is importable when running from project root
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Page configuration ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AUTOSAR HLD Assistant",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Lazy imports with error handling ─────────────────────────────────────────

@st.cache_resource(show_spinner="Loading AI components…")
def get_pipeline():
    """Create and cache the RAG pipeline (loads embedding model once)."""
    from src.rag_pipeline import RAGPipeline

    chunk_size = int(os.getenv("CHUNK_SIZE", "800"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "150"))
    top_k = int(os.getenv("TOP_K_RESULTS", "5"))
    index_dir = os.getenv("INDEX_DIR", "data/faiss_index")

    pipeline = RAGPipeline(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        top_k=top_k,
        index_dir=index_dir,
    )
    if not hasattr(pipeline, "reranker") or pipeline.reranker is None:
        from src.reranker import ReRanker
        pipeline.reranker = ReRanker()

    # Try to reload previously saved index
    if pipeline.load_existing_index():
        st.session_state["index_loaded"] = True

    return pipeline


# ── Session state initialisation ─────────────────────────────────────────────

def init_session_state():
    defaults = {
        "chat_history": [],
        "doc_results": {},
        "index_loaded": False,
        "processing_done": False,
        "analysis_cache": {},
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


init_session_state()

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/94/AUTOSAR_Logo.svg/240px-AUTOSAR_Logo.svg.png", width=120)
    st.title("🚗 AUTOSAR HLD\nAssistant")
    st.caption("v0.1.0 – Engineering Prototype")
    st.divider()

    pipeline = get_pipeline()

    # LLM status
    llm_provider = getattr(pipeline.llm, "provider", os.getenv("LLM_PROVIDER", "none")).lower()
    llm_model = getattr(pipeline.llm, "_model", None)
    if llm_provider == "none":
        st.info("🔍 **Mode:** Structured Extractive Evidence\n\nNo LLM configured. Set `LLM_PROVIDER` in `.env` (OpenRouter, Ollama, OpenAI, Anthropic).", icon="ℹ️")
    else:
        model_str = f"\n\n`{llm_model}`" if llm_model else ""
        st.success(f"🤖 **Mode:** LLM ({llm_provider.upper()}){model_str}", icon="✅")

    # Re-ranker status
    reranker = getattr(pipeline, "reranker", None)
    if reranker is None:
        from src.reranker import ReRanker
        pipeline.reranker = ReRanker()
        reranker = pipeline.reranker

    reranker_model = getattr(reranker, "model_name", "cross-encoder")
    is_mock_reranker = getattr(reranker, "is_mock", False)
    mock_tag = " (Fallback / Lexical)" if is_mock_reranker else " (Cross-Encoder)"
    st.info(f"⚡ **Re-ranker:** Active{mock_tag}\n\n`{reranker_model.split('/')[-1]}`", icon="⚡")

    st.divider()

    # Index status
    if pipeline.is_ready:
        st.success(f"✅ Index ready\n\n**Docs:** {len(pipeline.indexed_documents)}\n\n**Chunks:** {pipeline.chunk_count}")
        st.write("**Indexed documents:**")
        for d in pipeline.indexed_documents:
            st.write(f"• {d}")
    else:
        st.warning("⚠️ No documents indexed yet.\n\nUpload PDFs and click **Process Documents**.")

    st.divider()

    # Reset
    if st.button("🗑️ Clear Index & Reset", use_container_width=True):
        if st.session_state.get("confirm_clear"):
            pipeline.clear_index()
            st.session_state.clear()
            st.cache_resource.clear()
            st.rerun()
        else:
            st.session_state["confirm_clear"] = True
            st.warning("Click again to confirm reset.")

    if st.session_state.get("confirm_clear"):
        if st.button("✅ Yes, Reset Everything", use_container_width=True, type="primary"):
            pipeline.clear_index()
            st.session_state.clear()
            st.cache_resource.clear()
            st.rerun()


# ── Main content ──────────────────────────────────────────────────────────────

st.title("🚗 AUTOSAR HLD Document Analysis Assistant")
st.caption(
    "Upload AUTOSAR High-Level Design PDF documents and ask questions about software "
    "components, interfaces, signals, and architecture. "
    "**This is an engineering prototype. Do not use for official certification.**"
)

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab_upload, tab_qa, tab_analysis, tab_compare = st.tabs(
    ["📄 Upload & Process", "💬 Ask Questions", "🔍 Architecture Analysis", "📊 Document Compare"]
)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: Upload & Process
# ══════════════════════════════════════════════════════════════════════════════

with tab_upload:
    st.header("Upload AUTOSAR HLD Documents")
    st.info(
        "Upload one or more PDF documents. Scanned (image-only) PDFs require OCR preprocessing "
        "and cannot be processed directly by this tool."
    )

    uploaded_files = st.file_uploader(
        "Select PDF files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload AUTOSAR HLD PDF documents (text-based, not scanned).",
    )

    if uploaded_files:
        st.write(f"**{len(uploaded_files)} file(s) selected:**")
        for f in uploaded_files:
            st.write(f"• {f.name} ({f.size / 1024:.1f} KB)")

        if st.button("⚙️ Process Documents", type="primary", use_container_width=True):
            files_data = [(f.read(), f.name) for f in uploaded_files]

            with st.spinner("Processing PDFs and building index…"):
                try:
                    results = pipeline.process_uploaded_files(files_data)
                    st.session_state["doc_results"] = {
                        r.doc_name: r for r in results
                    }
                    st.session_state["processing_done"] = True
                    st.session_state["analysis_cache"] = {}  # invalidate cache
                except Exception as exc:
                    st.error(f"Processing error: {exc}")
                    logger.exception("Processing error")

    # Show results
    if st.session_state.get("processing_done") or st.session_state.get("index_loaded"):
        doc_results = st.session_state.get("doc_results", {})

        if doc_results:
            st.divider()
            st.subheader("Processing Results")

            for name, result in doc_results.items():
                with st.expander(f"📄 {name}", expanded=True):
                    if result.error:
                        st.error(f"❌ Error: {result.error}")
                    else:
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Pages", result.total_pages)
                        col2.metric("Extractable Pages", result.extractable_pages)
                        col3.metric("Text Coverage", f"{result.extractable_pages / max(result.total_pages, 1) * 100:.0f}%")

                        if result.is_text_empty:
                            st.warning(
                                "⚠️ No extractable text found. This document may be scanned or image-based. "
                                "OCR preprocessing is required before it can be analysed."
                            )

                        if result.warnings:
                            st.warning("**Processing Warnings:**")
                            for w in result.warnings[:5]:
                                st.write(f"• {w}")

        if pipeline.is_ready:
            st.success(
                f"✅ **Index ready:** {pipeline.chunk_count} chunks from "
                f"{len(pipeline.indexed_documents)} document(s)."
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: Ask Questions
# ══════════════════════════════════════════════════════════════════════════════

with tab_qa:
    st.header("Ask Architecture Questions")

    if not pipeline.is_ready:
        st.warning("⚠️ Please upload and process documents first (Upload & Process tab).")
    else:
        # Render helper for assistant response with button to view retrieved chunks
        def render_assistant_response(entry, key_prefix="hist"):
            st.markdown(entry["answer"])

            retrieved_chunks = entry.get("retrieved_chunks", [])
            citations = entry.get("citations", [])

            col1, col2, col3 = st.columns([1.8, 1.2, 2.0])

            if retrieved_chunks:
                with col1:
                    with st.popover(f"🔍 View Retrieved Chunks ({len(retrieved_chunks)})", use_container_width=True):
                        st.markdown("### 🔎 Retrieved & Re-Ranked Source Chunks")
                        st.caption(f"Inspection view of the top {len(retrieved_chunks)} evidence passages sorted by re-ranking score.")
                        for i, chunk in enumerate(retrieved_chunks, 1):
                            rerank_score = chunk.get("rerank_score")
                            init_rank = chunk.get("initial_rank", i)
                            score_label = f"Score: {rerank_score:.3f}" if rerank_score is not None else f"Cosine: {chunk.get('score', 0):.3f}"
                            rank_change = f"Initial: #{init_rank} ➔ Re-ranked: #{i}" if init_rank != i else f"Rank: #{i}"
                            st.markdown(
                                f"**[{i}] `{chunk['doc_name']}` | Page {chunk['page_number']}**  \n"
                                f"🏷️ `{rank_change}` | 🎯 `{score_label}`"
                            )
                            st.code(chunk["text"], language="text")
                            st.divider()

            if citations:
                with col2:
                    with st.popover(f"📚 Citations ({len(citations)})", use_container_width=True):
                        st.markdown("### 📚 Source Citations")
                        for cit in citations:
                            st.write(f"• **{cit['doc_name']}**, Page {cit['page_number']}")

            mode_badge = {
                "llm": "🤖 LLM Structured Answer",
                "extractive": "📄 Extractive Evidence (Re-ranked)",
                "no_results": "⚠️ No matching passages",
                "error": "❌ LLM error",
                "no_index": "⚠️ Index not ready",
            }.get(entry.get("mode", ""), "")
            if mode_badge:
                with col3:
                    st.caption(f"*{mode_badge}*")

        # Chat history display
        for idx, entry in enumerate(st.session_state["chat_history"]):
            with st.chat_message("user"):
                st.write(entry["question"])
            with st.chat_message("assistant"):
                render_assistant_response(entry, key_prefix=f"hist_{idx}")

        # Question input
        example_questions = [
            "What are the main software components in this document?",
            "What interfaces or ports are defined?",
            "Describe the functional flows mentioned in the document.",
            "What signals or messages are exchanged between components?",
            "Are there any dependencies between components?",
            "Summarize the document architecture.",
        ]

        st.write("**Example questions:**")
        cols = st.columns(3)
        for i, q in enumerate(example_questions):
            if cols[i % 3].button(q, key=f"eq_{i}", use_container_width=True):
                st.session_state["prefill_question"] = q

        question = st.chat_input("Ask a question about your AUTOSAR documents…")
        prefill = st.session_state.pop("prefill_question", None)
        if prefill and not question:
            question = prefill

        if question:
            with st.chat_message("user"):
                st.write(question)

            with st.chat_message("assistant"):
                with st.spinner("Searching documents & re-ranking passages…"):
                    result = pipeline.query(question)

                render_assistant_response(result, key_prefix="latest")

            # Save to history
            st.session_state["chat_history"].append(
                {
                    "question": question,
                    "answer": result["answer"],
                    "citations": result.get("citations", []),
                    "retrieved_chunks": result.get("retrieved_chunks", []),
                    "mode": result.get("mode", ""),
                }
            )

        if st.session_state["chat_history"] and st.button("🗑️ Clear Chat History"):
            st.session_state["chat_history"] = []
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: Architecture Analysis
# ══════════════════════════════════════════════════════════════════════════════

with tab_analysis:
    st.header("Architecture Analysis")
    st.info(
        "All findings below are **heuristic candidates** derived from text pattern analysis. "
        "They require engineering review before being treated as verified architecture facts."
    )

    if not pipeline.is_ready:
        st.warning("⚠️ Please upload and process documents first.")
    else:
        from src.architecture_analyzer import ArchitectureAnalyzer

        # Select document to analyse
        docs = pipeline.indexed_documents
        selected_doc = st.selectbox("Select document for analysis:", docs)

        if selected_doc and selected_doc not in st.session_state["analysis_cache"]:
            # Re-extract pages for the selected document
            doc_result = pipeline.doc_results.get(selected_doc)
            if doc_result and doc_result.pages:
                analyzer = ArchitectureAnalyzer(doc_result.pages)
                st.session_state["analysis_cache"][selected_doc] = analyzer
            else:
                # Try to reconstruct from chunks
                st.warning(
                    "Document pages not available in session. "
                    "Re-upload the document to enable analysis."
                )
                analyzer = None
        else:
            analyzer = st.session_state["analysis_cache"].get(selected_doc)

        if analyzer:
            # Summary
            st.subheader("📋 Document Summary")

            if "ai_summary_cache" not in st.session_state:
                st.session_state["ai_summary_cache"] = {}

            if pipeline.llm.is_configured:
                col_sum1, col_sum2 = st.columns([3, 1])
                with col_sum1:
                    st.caption(f"Connected to LLM: `{pipeline.llm.provider.upper()}` – Generate an in-depth architectural synthesis.")
                with col_sum2:
                    btn_label = "🔄 Refresh AI Summary" if selected_doc in st.session_state["ai_summary_cache"] else "🤖 Generate AI Summary"
                    if st.button(btn_label, use_container_width=True):
                        with st.spinner("Synthesizing architecture overview with LLM…"):
                            ai_sum = pipeline.summarize_document(selected_doc)
                            if ai_sum:
                                st.session_state["ai_summary_cache"][selected_doc] = ai_sum
                                st.rerun()

                if selected_doc in st.session_state["ai_summary_cache"]:
                    st.markdown("#### 🤖 AI Architecture Executive Summary")
                    st.markdown(st.session_state["ai_summary_cache"][selected_doc])
                    st.divider()

            st.markdown(analyzer.generate_summary())

            st.divider()

            # Component inventory
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🔧 Candidate Components")
                comps = analyzer.extract_components()
                if comps:
                    comp_df = pd.DataFrame(comps)
                    comp_df["pages_str"] = comp_df["pages"].apply(
                        lambda ps: ", ".join(str(p) for p in ps[:5])
                    )
                    st.dataframe(
                        comp_df[["name", "category", "frequency", "pages_str"]].rename(
                            columns={
                                "name": "Term",
                                "category": "Category",
                                "frequency": "Frequency",
                                "pages_str": "Pages",
                            }
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No candidate components identified.")

            with col2:
                st.subheader("🔌 Candidate Interfaces / Terms")
                ifaces = analyzer.extract_interfaces()
                if ifaces:
                    iface_df = pd.DataFrame(ifaces)
                    iface_df["pages_str"] = iface_df["pages"].apply(
                        lambda ps: ", ".join(str(p) for p in ps[:5])
                    )
                    st.dataframe(
                        iface_df[["name", "category", "count", "pages_str"]].rename(
                            columns={
                                "name": "Term",
                                "category": "Category",
                                "count": "Count",
                                "pages_str": "Pages",
                            }
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                else:
                    st.info("No candidate interfaces identified.")

            st.divider()

            # Dependencies
            st.subheader("🔗 Candidate Dependencies")
            deps = analyzer.extract_dependencies()
            if deps:
                for dep in deps[:10]:
                    st.write(f"• **Page {dep['page_number']}:** {dep['description']}")
            else:
                st.info("No dependency statements identified.")

            st.divider()

            # Functional flows
            st.subheader("⚡ Functional Flow References")
            flows = analyzer.extract_functional_flows()
            if flows:
                for flow in flows[:10]:
                    st.write(f"• **Page {flow['page_number']}:** {flow['description']}")
            else:
                st.info("No functional flow references identified.")

            st.divider()

            # Inconsistency candidates
            st.subheader("⚠️ Potential Inconsistencies / Missing Information")
            incons = analyzer.find_inconsistencies()
            if incons:
                for inc in incons:
                    with st.expander(f"⚠️ {inc['finding'][:80]}"):
                        st.write(f"**Category:** {inc['category']}")
                        st.write(f"**Evidence:** {inc['supporting_evidence']}")
                        st.write(f"**Status:** {inc['review_status']}")
            else:
                st.success("✅ No obvious inconsistencies detected by heuristics.")

            st.divider()

            # Findings table and CSV export
            st.subheader("📊 Complete Findings Table")
            findings_df = analyzer.build_findings_dataframe()
            st.dataframe(findings_df, use_container_width=True, hide_index=True)

            csv_data = findings_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇️ Download Findings as CSV",
                data=csv_data,
                file_name=f"findings_{selected_doc.replace('.pdf', '')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: Document Comparison
# ══════════════════════════════════════════════════════════════════════════════

with tab_compare:
    st.header("Document Comparison")
    st.info(
        "Compare two documents by their extracted technical terms. "
        "Differences are labelled as **potential changes**, not confirmed design defects."
    )

    if not pipeline.is_ready:
        st.warning("⚠️ Please upload and process documents first.")
    elif len(pipeline.indexed_documents) < 2:
        st.info(
            "Upload at least two documents to use the comparison feature. "
            f"Currently indexed: **{', '.join(pipeline.indexed_documents)}**"
        )
    else:
        from src.document_comparator import DocumentComparator

        docs = pipeline.indexed_documents
        col_a, col_b = st.columns(2)
        doc_a_name = col_a.selectbox("Document A:", docs, index=0)
        doc_b_name = col_b.selectbox("Document B:", docs, index=min(1, len(docs) - 1))

        if doc_a_name == doc_b_name:
            st.warning("Please select two different documents to compare.")
        else:
            res_a = pipeline.doc_results.get(doc_a_name)
            res_b = pipeline.doc_results.get(doc_b_name)

            if res_a and res_b and res_a.pages and res_b.pages:
                comparator = DocumentComparator(res_a.pages, res_b.pages)
                summary = comparator.get_summary()

                col1, col2, col3 = st.columns(3)
                col1.metric("Common Terms", summary["common_count"])
                col2.metric(f"Only in {doc_a_name[:20]}…", summary["only_a_count"])
                col3.metric(f"Only in {doc_b_name[:20]}…", summary["only_b_count"])

                st.subheader("Comparison Table")
                comp_df = comparator.compare_components()
                st.dataframe(comp_df, use_container_width=True, hide_index=True)

                csv_data = comp_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Download Comparison CSV",
                    data=csv_data,
                    file_name="document_comparison.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.warning(
                    "Document pages not available for one or both selected documents. "
                    "Re-upload the documents to enable comparison."
                )

# ── Footer ────────────────────────────────────────────────────────────────────

st.divider()
st.caption(
    "⚠️ **Disclaimer:** This tool is an engineering prototype for research assistance only. "
    "It does not constitute official AUTOSAR compliance analysis. "
    "All findings require qualified engineering review."
)
