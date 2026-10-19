# Project Synopsis
## AUTOSAR HLD Intelligence & Traceability Assistant Using RAG

### 1. Project Title & Domain
- **Project Title:** AUTOSAR HLD Intelligence & Traceability Assistant Using Retrieval-Augmented Generation (RAG)
- **Domain:** Automotive Software Engineering / Natural Language Processing & Applied AI
- **Application Scope:** Automotive Electronic Control Unit (ECU) High-Level Design (HLD) Document Analysis, Component & Interface Traceability, and Architecture Verification

---

### 2. Problem Statement
Automotive software engineering based on the AUTOSAR (AUTomotive Open System ARchitecture) standard involves extensive, multi-hundred-page High-Level Design (HLD) specifications detailing Software Components (SWCs), ports, interfaces, CAN/LIN/Ethernet communication signals, Basic Software (BSW) stacks, and functional execution flows. 

Manual analysis of these HLD documents suffers from:
1. **High Cognitive Burden & Time Inefficiency:** Systems engineers spend excessive hours manually locating signal definitions, component interactions, and execution sequences across dense PDF specifications.
2. **Traceability & Verification Gaps:** Identifying cross-module dependencies and specification omissions (e.g., missing recovery behaviors, unmapped ports) is error-prone.
3. **Risk of Hallucinations with Generic LLMs:** Conventional LLMs frequently hallucinate automotive signal names, port identifiers, and invalid page references when queried without strict factual grounding.

---

### 3. Proposed Solution
The **AUTOSAR HLD Intelligence & Traceability Assistant** is an offline-capable, engineering-grade web application powered by **Two-Stage Retrieval-Augmented Generation (RAG)**. It ingests automotive HLD PDF documents, generates semantic embeddings, indexes technical passages via FAISS, re-ranks retrieved evidence through a Cross-Encoder model, and synthesizes accurate, evidence-backed architectural answers accompanied by strict source-page citations.

The solution ensures:
- **Zero Hallucination of Citations:** Citations and summary tables undergo programmatic validation against retrieved ground-truth chunks before rendering.
- **Privacy & IP Protection:** Supports completely offline local inference via Ollama (`deepseek-r1:1.5b`), ensuring proprietary automotive architectures never leave the local machine.
- **Dual Operating Modes:** Operates in full LLM-driven mode or 100% offline extractive synthesis mode (requiring zero API keys or GPU resources).

---

### 4. System Architecture & Methodology
The system follows a modular 6-stage engineering pipeline:
1. **Document Ingestion & Validation (`src/pdf_processor.py`):** Page-by-page text extraction via PyMuPDF (`fitz`), preserving document filenames, page numbers, text coverage statistics, and empty/scanned PDF detection.
2. **Provenance-Preserving Chunking (`src/chunker.py`):** Configurable character chunking (800 characters with 150-character overlap) storing chunk IDs, document names, and page coordinates.
3. **Dense Semantic Embeddings (`src/embeddings.py`):** 384-dimensional dense vectors generated using `all-MiniLM-L6-v2` (Sentence Transformers).
4. **Vector Search & Indexing (`src/vector_store.py`):** Inner Product similarity search powered by FAISS CPU (`IndexFlatIP`) with dictionary-based metadata persistence.
5. **Two-Stage Re-Ranking (`src/reranker.py`):** Cross-Encoder re-ranking (`ms-marco-MiniLM-L-6-v2`) computes deep query-passage cross-attention scores to promote the highest-relevance technical passages over initial vector top-K candidates.
6. **Constrained Synthesis & Verification (`src/llm_provider.py`):** 
   - Prompts the configured LLM (Ollama `deepseek-r1:1.5b`, OpenRouter, OpenAI, or Anthropic) for a strict 3-section response:
     - `💡 Executive Summary`
     - `🏗️ Architectural Breakdown`
     - `📑 Evidence & Citations Summary`
   - Strips internal reasoning traces (`<think> ... </think>`).
   - Programmatically validates and replaces any placeholder document names or page references with verified ground-truth chunk provenance.

---

### 5. Key Features & Modules
- **Interactive Engineering Q&A:** Natural language architectural queries with expandable raw passage inspection (`🔍 View Retrieved Chunks`) and citation badges.
- **Heuristic Architecture Analyzer (`src/architecture_analyzer.py`):** Deterministic extraction of candidate Software Components (SWCs), ports, signals, BSW layers, and dependency statements.
- **Document Comparator (`src/document_comparator.py`):** Side-by-side architectural diffing across multiple HLD revisions.
- **Structured Findings CSV Export:** Exportable tabular architecture reports for peer engineering reviews.
- **1-Click Windows Deployment:** Dedicated `start_app.bat` and `stop_app.bat` scripts managing Ollama, Python backend, Streamlit frontend, and automated browser launch.

---

### 6. Implementation & Technology Stack
- **Programming Language:** Python 3.11
- **User Interface:** Streamlit (v1.50)
- **PDF Extraction:** PyMuPDF (`fitz` v1.23+)
- **Embeddings:** Sentence Transformers (`all-MiniLM-L6-v2`)
- **Vector Database:** FAISS CPU (`faiss-cpu` v1.7.4+)
- **Re-Ranking Model:** Cross-Encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`)
- **Local LLM Engine:** Ollama (`deepseek-r1:1.5b`)
- **Cloud LLM Support:** OpenRouter API, OpenAI, Anthropic
- **Data & Testing:** pandas, pytest (78 automated test cases, 100% passing)

---

### 7. Evaluation & Validation Results
- **Automated Test Suite:** 78 unit and integration tests passing (`pytest tests/`) validating PDF parsing, chunking, vector indexing, citation integrity, re-ranking, and reasoning stripping.
- **10-Question Automotive Evaluation Benchmark (`evaluate.py`):** Tested across component identification, interface mapping, CAN signals, functional sequences, missing specifications, and unsupported/out-of-scope queries with verified relevance metrics.
