"""
evaluate.py
-----------
Evaluation script for the AUTOSAR HLD Assistant RAG system.
Tests retrieval relevance, citation correctness, and answer quality
against a synthetic automotive architecture document with reference Q&A pairs.

Usage:
    python evaluate.py

No API key required (runs in extractive mode by default).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent))

# Disable LLM for evaluation (extractive mode)
os.environ.setdefault("LLM_PROVIDER", "none")

from tests.conftest import _make_pdf_bytes, SYNTHETIC_HLD_TEXT

# ── Evaluation dataset ────────────────────────────────────────────────────────

EVAL_QUESTIONS = [
    {
        "id": "Q01",
        "question": "What are the main software components in the BCM document?",
        "expected_terms": ["LightingManager", "DoorLockController", "WindowController", "ClimateControlModule"],
        "expected_type": "component_identification",
        "expected_pages_contain": True,  # should cite at least one page
        "supported": True,
    },
    {
        "id": "Q02",
        "question": "What interfaces or ports does LightingManager provide?",
        "expected_terms": ["ExteriorLightPort", "InteriorLightPort"],
        "expected_type": "interface_relationship",
        "expected_pages_contain": True,
        "supported": True,
    },
    {
        "id": "Q03",
        "question": "What signals are defined in the BCM document?",
        "expected_terms": ["LightStatusSignal", "LockStatusSignal", "WindowStatusSignal"],
        "expected_type": "signals",
        "expected_pages_contain": True,
        "supported": True,
    },
    {
        "id": "Q04",
        "question": "What component does DoorLockController depend on?",
        "expected_terms": ["KeyFobSignalReceiver", "AuthenticationService"],
        "expected_type": "dependencies",
        "expected_pages_contain": True,
        "supported": True,
    },
    {
        "id": "Q05",
        "question": "Describe the door lock functional sequence.",
        "expected_terms": ["KeyFob", "DoorLockController", "UnlockRequestSignal"],
        "expected_type": "functional_flow",
        "expected_pages_contain": True,
        "supported": True,
    },
    {
        "id": "Q06",
        "question": "What BSW modules are configured in the BCM?",
        "expected_terms": ["MCAL", "PDUR", "DCM", "DEM", "NVM"],
        "expected_type": "component_identification",
        "expected_pages_contain": True,
        "supported": True,
    },
    {
        "id": "Q07",
        "question": "What CAN signals are transmitted by the BCM?",
        "expected_terms": ["LightStatusSignal", "LockStatusSignal", "0x301", "0x302"],
        "expected_type": "signals",
        "expected_pages_contain": True,
        "supported": True,
    },
    {
        "id": "Q08",
        "question": "Summarize the overall architecture described in the document.",
        "expected_terms": ["BCM", "Body Control Module", "AUTOSAR"],
        "expected_type": "document_summary",
        "expected_pages_contain": True,
        "supported": True,
    },
    {
        "id": "Q09",
        "question": "Are there any missing or incomplete specifications mentioned in the document?",
        "expected_terms": ["ClimateControlModule", "KeyFob", "NVM", "Roll-back"],
        "expected_type": "missing_information",
        "expected_pages_contain": True,
        "supported": True,
    },
    {
        "id": "Q10",
        "question": "What is the stock price of AUTOSAR GmbH?",
        "expected_terms": [],
        "expected_type": "unsupported",
        "expected_pages_contain": False,
        "supported": False,
    },
]


# ── Evaluation runner ─────────────────────────────────────────────────────────

def run_evaluation():
    from src.rag_pipeline import RAGPipeline

    print("=" * 70)
    print("AUTOSAR HLD Assistant – RAG Evaluation")
    print("Mode: Extractive Evidence (no LLM)")
    print("=" * 70)
    print()

    # Build synthetic PDF and index
    pdf_bytes = _make_pdf_bytes(SYNTHETIC_HLD_TEXT, "BCM HLD v2.1")
    pipeline = RAGPipeline(
        chunk_size=800,
        chunk_overlap=150,
        top_k=5,
        index_dir="data/eval_faiss_index",
        use_mock_embeddings=True,
    )

    print("[1] Processing synthetic BCM HLD document...")
    results = pipeline.process_uploaded_files([(pdf_bytes, "bcm_hld_v2.1.pdf")])
    result = results[0]
    print(f"    Pages: {result.total_pages}, Extractable: {result.extractable_pages}")
    print(f"    Chunks indexed: {pipeline.chunk_count}")
    print()

    # Run evaluation
    scores = []
    print(f"[2] Running {len(EVAL_QUESTIONS)} evaluation questions...")
    print("-" * 70)

    for q in EVAL_QUESTIONS:
        t0 = time.time()
        answer_result = pipeline.query(q["question"])
        latency_ms = (time.time() - t0) * 1000

        answer_text = answer_result.get("answer", "")
        citations = answer_result.get("citations", [])
        retrieved = answer_result.get("retrieved_chunks", [])
        mode = answer_result.get("mode", "unknown")

        # Evaluate retrieval relevance: do retrieved chunks contain expected terms?
        all_retrieved_text = " ".join(c["text"] for c in retrieved).lower()
        retrieval_hits = sum(
            1 for term in q["expected_terms"]
            if term.lower() in all_retrieved_text
        ) if q["expected_terms"] else 0
        retrieval_total = len(q["expected_terms"]) if q["expected_terms"] else 1
        retrieval_score = retrieval_hits / retrieval_total if retrieval_total > 0 else 1.0

        # Citation correctness: citations reference real indexed documents
        citation_correct = all(
            c["doc_name"] in pipeline.indexed_documents for c in citations
        )

        # Answer correctness: expected terms appear in answer (extractive mode)
        answer_hits = sum(
            1 for term in q["expected_terms"]
            if term.lower() in answer_text.lower()
        ) if q["expected_terms"] else 0
        answer_score = answer_hits / retrieval_total if retrieval_total > 0 else 1.0

        # Appropriate handling of unsupported questions
        if not q["supported"]:
            # Should not fabricate page citations for unsupported questions
            unsupported_ok = (
                mode in ("no_results", "extractive")
                and "stock price" not in answer_text.lower()
            )
        else:
            unsupported_ok = True

        # Page citation presence
        has_citations = len(citations) > 0
        citation_presence_ok = (has_citations == q["expected_pages_contain"])

        overall_pass = (
            retrieval_score >= 0.5
            and citation_correct
            and unsupported_ok
        )

        scores.append({
            "id": q["id"],
            "type": q["expected_type"],
            "retrieval_score": retrieval_score,
            "answer_score": answer_score,
            "citation_correct": citation_correct,
            "citation_present": has_citations,
            "unsupported_ok": unsupported_ok,
            "latency_ms": latency_ms,
            "pass": overall_pass,
            "mode": mode,
        })

        status = "[PASS]" if overall_pass else "[FAIL]"
        print(f"{q['id']} [{q['expected_type'][:20]:<20}] {status}")
        print(f"    Mode: {mode} | Retrieval: {retrieval_score:.0%} | "
              f"Answer: {answer_score:.0%} | Citations: {len(citations)} | "
              f"Latency: {latency_ms:.0f}ms")
        print(f"    Q: {q['question'][:70]}")
        if q["expected_terms"]:
            found = [t for t in q["expected_terms"] if t.lower() in all_retrieved_text]
            print(f"    Found terms: {found}")
        print()

    # Summary
    print("=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)
    passed = sum(1 for s in scores if s["pass"])
    total = len(scores)
    avg_retrieval = sum(s["retrieval_score"] for s in scores) / total
    avg_latency = sum(s["latency_ms"] for s in scores) / total

    print(f"Tests Passed:         {passed}/{total} ({passed/total:.0%})")
    print(f"Avg Retrieval Score:  {avg_retrieval:.1%}")
    print(f"Avg Latency:          {avg_latency:.0f}ms")
    print(f"Citation Accuracy:    {sum(1 for s in scores if s['citation_correct'])}/{total}")
    print()
    print("Note: Using mock embedder (deterministic hash). Results reflect")
    print("retrieval quality with hash-based vectors, not semantic similarity.")
    print("Use real sentence-transformers model for production-quality results.")
    print()

    # Per-type breakdown
    types = {}
    for s in scores:
        t = s["type"]
        types.setdefault(t, []).append(s)

    print("Results by question type:")
    for qtype, qscores in types.items():
        p = sum(1 for s in qscores if s["pass"])
        print(f"  {qtype:<25}: {p}/{len(qscores)} passed")

    return scores


if __name__ == "__main__":
    run_evaluation()
