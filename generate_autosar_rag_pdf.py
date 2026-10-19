import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

def create_autosar_rag_qa_pdf(filename="AUTOSAR_RAG_Project_Interview_Guide.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=HexColor('#000000'),
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'DocH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=HexColor('#000000'),
        spaceBefore=10,
        spaceAfter=4
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=HexColor('#000000'),
        spaceBefore=8,
        spaceAfter=3
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=HexColor('#111111'),
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=HexColor('#111111'),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=3
    )

    arrow_style = ParagraphStyle(
        'DocArrow',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=15,
        alignment=TA_CENTER,
        textColor=HexColor('#222222'),
        spaceBefore=2,
        spaceAfter=2
    )

    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11.5,
        textColor=HexColor('#00FF66')
    )

    code_title_style = ParagraphStyle(
        'CodeTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=HexColor('#00D2FF')
    )

    def make_code_box(title, code_str):
        formatted_code = code_str.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
        content = [
            Paragraph(f"<b>&lt;/&gt; Python &mdash; {title}</b>", code_title_style),
            Spacer(1, 4),
            Paragraph(formatted_code, code_style)
        ]
        t = Table([[content]], colWidths=[500])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), HexColor('#181818')),
            ('LEFTPADDING', (0,0), (-1,-1), 10),
            ('RIGHTPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('BOX', (0,0), (-1,-1), 0.5, HexColor('#333333')),
        ]))
        return t

    story = []

    # Title
    story.append(Paragraph("Project RAG", title_style))
    story.append(Paragraph("Project Introduction", h1_style))
    story.append(Paragraph(
        'My project is <b>"AUTOSAR HLD Intelligence &amp; Traceability Assistant &ndash; Retrieval-Augmented Generation (RAG) System."</b> '
        'The objective is to provide accurate, grounded architectural answers and component traceability from uploaded automotive High-Level Design (HLD) PDF documents using RAG. '
        'The system uses RAG to retrieve relevant specification passages from the uploaded HLD document and generate accurate, verified answers with source citations. '
        'We developed this to overcome the limitation of normal generic LLMs, which give incorrect, hallucinated, or ungrounded answers when technical automotive information is not present in their training data or when proprietary confidential documents are analyzed.',
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Problem Statement", h1_style))
    story.append(Paragraph("<b>Interviewer: What problem does your project solve?</b>", h2_style))
    story.append(Paragraph(
        'Automotive HLD documents follow strict AUTOSAR standards and span hundreds of pages detailing Software Components (SWCs), ports, interfaces, CAN signals, and Basic Software (BSW) stacks. '
        'Traditional Large Language Models depend only on their pre-trained knowledge. They cannot know proprietary information from newly uploaded automotive documents, and they frequently hallucinate signal names, port identifiers, or fake page references. '
        'Our project solves this by allowing automotive engineers to upload their own HLD PDFs and get verified, evidence-based answers directly from the document content with exact source-page citations.',
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("What is your contribution in the project?", h1_style))
    story.append(Paragraph(
        'My contribution was mainly in implementing the end-to-end RAG pipeline, document preprocessing with page-level provenance, vector database creation using FAISS, two-stage Cross-Encoder re-ranking, and response verification with reasoning-trace stripping.',
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Document Preprocessing", h1_style))
    story.append(Paragraph("&bull; Extracting text page-by-page from automotive PDF files using PyMuPDF (fitz).", bullet_style))
    story.append(Paragraph("&bull; Removing excessive whitespace and validating extractable text coverage.", bullet_style))
    story.append(Paragraph("&bull; Splitting multi-page automotive specifications into smaller semantic chunks.", bullet_style))
    story.append(Paragraph("&bull; Creating overlapping chunks while preserving document name and page number metadata.", bullet_style))
    story.append(Spacer(1, 3))

    story.append(Paragraph("Why is this needed?", h2_style))
    story.append(Paragraph(
        'An automotive HLD PDF may contain hundreds of pages with dense tables and architecture diagrams.<br/>'
        'The LLM cannot directly search through the entire document efficiently due to context-window limits.<br/>'
        'So we divide the document into smaller meaningful sections (chunks) before encoding and indexing them.',
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("2. Document Chunking", h1_style))
    story.append(Paragraph('We divide the document text into smaller pieces called <b>chunks</b>.', body_style))
    story.append(Paragraph("Why?", h2_style))
    story.append(Paragraph(
        '"LLMs cannot efficiently process very large documents at once, so we split the text into smaller meaningful sections with provenance metadata."',
        body_style
    ))
    story.append(Paragraph("Project values:", h2_style))
    story.append(Paragraph("&bull; <b>Chunk Size = 800 characters</b> (captures full AUTOSAR signal &amp; port interaction blocks)", bullet_style))
    story.append(Paragraph("&bull; <b>Overlap = 150 characters</b>", bullet_style))
    story.append(Paragraph('The overlap ensures that critical automotive context (such as port connections split across lines) is not lost between consecutive chunks.', body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("3. Embedding Generation", h1_style))
    story.append(Paragraph(
        'We convert every text chunk into dense numerical vectors called embeddings using the <b>sentence-transformers/all-MiniLM-L6-v2</b> embedding model.',
        body_style
    ))
    story.append(Paragraph("Why?", h2_style))
    story.append(Paragraph(
        '"Computers and search indexes cannot understand text directly, so embeddings represent the semantic meaning of technical text numerically in a 384-dimensional vector space."',
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("4. Vector Database Creation &mdash; FAISS", h1_style))
    story.append(Paragraph("FAISS Vector Database", h2_style))
    story.append(Paragraph('"All normalized chunk embeddings are indexed in a <b>FAISS (Facebook AI Similarity Search)</b> vector database."', body_style))
    story.append(Paragraph("Why?", h2_style))
    story.append(Paragraph(
        '"When an engineer asks an architecture question, FAISS quickly finds the most similar chunks using inner product cosine similarity in milliseconds without searching the entire document linearly."',
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("5. Re-Ranking Optimization &mdash; Cross-Encoder", h1_style))
    story.append(Paragraph(
        'I implemented two-stage retrieval using a <b>Cross-Encoder re-ranker (cross-encoder/ms-marco-MiniLM-L-6-v2)</b> to re-score candidate chunks instead of relying solely on bi-encoder vector similarity.',
        body_style
    ))
    story.append(Paragraph("Parameters Used:", h2_style))
    story.append(Paragraph("&bull; Initial FAISS Candidate Pool: <b>k = 15 chunks</b>", bullet_style))
    story.append(Paragraph("&bull; Re-ranked Top Evidence Chunks: <b>top_k = 5 chunks</b>", bullet_style))
    story.append(Paragraph("&bull; Similarity Metric: <b>Cosine Inner Product (IndexFlatIP)</b>", bullet_style))
    story.append(Paragraph("Why Cross-Encoder?", h2_style))
    story.append(Paragraph(
        'FAISS uses bi-encoders which compute embeddings independently. The Cross-Encoder scores query and passage simultaneously through full cross-attention layers, eliminating false-positive lexical matches and boosting technical retrieval precision.',
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("6. Prompt Engineering &amp; Output Structure", h1_style))
    story.append(Paragraph(
        'I designed structured system prompts that instruct the LLM to answer strictly from the retrieved document evidence and format answers into three clean sections:',
        body_style
    ))
    story.append(Paragraph("&bull; <b>Executive Summary</b> &mdash; High-level direct explanation of the architectural query.", bullet_style))
    story.append(Paragraph("&bull; <b>Architectural Breakdown</b> &mdash; Components, Interfaces &amp; Ports, Signals, and Functional Flows.", bullet_style))
    story.append(Paragraph("&bull; <b>Evidence &amp; Citations Summary</b> &mdash; Grounded table linking facts to document filenames and page numbers.", bullet_style))
    story.append(Paragraph("Why?", h2_style))
    story.append(Paragraph(
        'LLMs sometimes use their own pre-trained knowledge and hallucinate automotive facts. Strict prompt framing and programmatic post-verification eliminate hallucinations.',
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("7. Reasoning Trace Stripping &amp; Citation Verification", h1_style))
    story.append(Paragraph(
        'Local reasoning models (such as DeepSeek-R1) output internal chain-of-thought traces inside <i>&lt;think&gt; ... &lt;/think&gt;</i> blocks. '
        'I built a post-processing cleaner that completely strips internal reasoning from the frontend display while programmatically validating document names and page numbers against retrieved chunks.',
        body_style
    ))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Technologies Used", h1_style))
    story.append(Paragraph("What technologies did you use?", h2_style))
    story.append(Paragraph("&bull; <b>Python 3.11</b> &mdash; Core programming language.", bullet_style))
    story.append(Paragraph("&bull; <b>Streamlit</b> &mdash; Web dashboard framework providing interactive multi-tab engineering UI.", bullet_style))
    story.append(Paragraph("&bull; <b>PyMuPDF (fitz)</b> &mdash; Fast, accurate page-by-page PDF text and metadata extraction.", bullet_style))
    story.append(Paragraph("&bull; <b>Sentence Transformers</b> &mdash; Used for generating dense text embeddings (all-MiniLM-L6-v2).", bullet_style))
    story.append(Paragraph("&bull; <b>FAISS CPU</b> &mdash; Vector database for sub-millisecond semantic similarity search.", bullet_style))
    story.append(Paragraph("&bull; <b>Cross-Encoder</b> &mdash; Deep neural re-ranking model (ms-marco-MiniLM-L-6-v2) for evidence precision.", bullet_style))
    story.append(Paragraph("&bull; <b>Ollama (Local LLM)</b> &mdash; Provides 100% private, offline inference using deepseek-r1:1.5b.", bullet_style))
    story.append(Paragraph("&bull; <b>OpenRouter / OpenAI API</b> &mdash; Optional cloud LLM integration for high-throughput synthesis.", bullet_style))
    story.append(Paragraph("&bull; <b>pandas</b> &mdash; Structured architecture findings extraction and CSV export.", bullet_style))
    story.append(Paragraph("&bull; <b>pytest</b> &mdash; Comprehensive automated test suite (78 tests passing).", bullet_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Complete Workflow", h1_style))
    workflow_steps = [
        "PDF Upload (Streamlit UI)",
        "&darr;",
        "Text Extraction (PyMuPDF &mdash; page-by-page metadata preservation)",
        "&darr;",
        "Chunking (800 chars, 150 overlap, chunk ID &amp; page coordinates)",
        "&darr;",
        "Embeddings (Sentence Transformers all-MiniLM-L6-v2 &mdash; 384 dimensions)",
        "&darr;",
        "FAISS Indexing (IndexFlatIP &mdash; persistent cosine vector index)",
        "&darr;",
        "User Question (Natural language architectural query)",
        "&darr;",
        "FAISS Candidate Recall (Top-15 most similar chunks retrieved)",
        "&darr;",
        "Cross-Encoder Re-Ranking (Top-5 high-relevance evidence passages selected)",
        "&darr;",
        "LLM Generation (Ollama deepseek-r1:1.5b / Extractive synthesis mode)",
        "&darr;",
        "Post-Processing (Strip reasoning traces + verify ground-truth page citations)",
        "&darr;",
        "Final Verified Output (Executive Summary + Architectural Breakdown + Citations Table)"
    ]
    for step in workflow_steps:
        if step == "&darr;":
            story.append(Paragraph("&darr;", arrow_style))
        else:
            story.append(Paragraph(f"<b>{step}</b>", bullet_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("What are Embeddings?", h1_style))
    story.append(Paragraph("Embeddings are dense numerical vector representations of text that capture semantic meaning in high-dimensional vector space.", body_style))
    story.append(Spacer(1, 3))

    story.append(Paragraph("Why deepseek-r1:1.5b / Ollama?", h1_style))
    story.append(Paragraph("Ollama with deepseek-r1:1.5b provides:", body_style))
    story.append(Paragraph("&bull; <b>100% Local &amp; Private:</b> Confidential automotive HLD architectures never leave the laptop.", bullet_style))
    story.append(Paragraph("&bull; <b>High Reasoning Capability:</b> Strong technical reasoning for cross-module dependencies and port tracing.", bullet_style))
    story.append(Paragraph("&bull; <b>Zero API Costs:</b> Runs efficiently on standard consumer CPU laptops without cloud tokens.", bullet_style))
    story.append(Spacer(1, 3))

    story.append(Paragraph("How did you evaluate the system?", h1_style))
    story.append(Paragraph("We evaluated the system using:", body_style))
    story.append(Paragraph("&bull; <b>Retrieval Relevance:</b> Proportion of domain-expected terms found in retrieved candidate passages.", bullet_style))
    story.append(Paragraph("&bull; <b>Citation Correctness:</b> Programmatic verification ensuring 100% of cited page numbers match actual source text.", bullet_style))
    story.append(Paragraph("&bull; <b>Automated Test Suite:</b> 78 automated unit and integration tests across all modules via pytest (100% pass rate).", bullet_style))
    story.append(Paragraph("&bull; <b>10-Question Benchmark (evaluate.py):</b> Evaluated component extraction, interface mapping, CAN signals, and unsupported query handling.", bullet_style))
    story.append(Spacer(1, 3))

    story.append(Paragraph("Challenges Faced", h1_style))
    story.append(Paragraph("What challenges did you face?", h2_style))
    story.append(Paragraph("&bull; Multi-hundred-page technical PDFs with complex formatting and tables.", bullet_style))
    story.append(Paragraph("&bull; Vector similarity false positives where lexical matches lacked true architectural relevance (solved via Cross-Encoder).", bullet_style))
    story.append(Paragraph("&bull; Small LLM models outputting reasoning monologues (&lt;think&gt;) and placeholder citations (solved via programmatic post-verification).", bullet_style))
    story.append(Paragraph("&bull; Ensuring 100% functionality without paid APIs (solved via offline extractive mode).", bullet_style))
    story.append(Spacer(1, 3))

    story.append(Paragraph("Future Scope", h1_style))
    story.append(Paragraph("What is the future scope?", h2_style))
    story.append(Paragraph("&bull; Hybrid Search combining dense semantic embeddings with sparse BM25 keyword matching.", bullet_style))
    story.append(Paragraph("&bull; Native OCR ingestion for scanned legacy automotive engineering blueprints.", bullet_style))
    story.append(Paragraph("&bull; ARXML (AUTOSAR XML) direct parsing alongside PDF specifications.", bullet_style))
    story.append(Spacer(1, 6))

    story.append(Paragraph("CODES SYNTAX", title_style))
    story.append(Paragraph("1. Load &amp; Extract PDF (PyMuPDF)", h1_style))
    code_1 = (
        "import fitz # PyMuPDF\n"
        "doc = fitz.open(stream=pdf_bytes, filetype='pdf')\n"
        "for page_num in range(len(doc)):\n"
        "    page = doc[page_num]\n"
        "    text = page.get_text('text')\n"
        "    pages.append(PageRecord(page_number=page_num + 1, text=text))"
    )
    story.append(make_code_box("PDF Extraction", code_1))
    story.append(Paragraph("<b>Interview Answer:</b> <i>\"I used PyMuPDF (fitz) to extract text page-by-page while preserving exact document names and page numbers for source citations.\"</i>", body_style))
    story.append(Spacer(1, 5))

    story.append(Paragraph("2. Document Chunking", h1_style))
    code_2 = (
        "chunk_size = 800\n"
        "overlap = 150\n"
        "start = 0\n"
        "while start < len(page_text):\n"
        "    end = min(start + chunk_size, len(page_text))\n"
        "    chunk = TextChunk(chunk_id=f'{doc_name}_p{page}_c{idx}', text=page_text[start:end])\n"
        "    chunks.append(chunk)\n"
        "    start += (chunk_size - overlap)"
    )
    story.append(make_code_box("Chunking with Overlap", code_2))
    story.append(Paragraph("<b>Interview Answer:</b> <i>\"I split large automotive HLD documents into 800-character chunks with 150-character overlap to preserve cross-sentence architectural context.\"</i>", body_style))
    story.append(Spacer(1, 5))

    story.append(Paragraph("3. Generate Dense Embeddings", h1_style))
    code_3 = (
        "from sentence_transformers import SentenceTransformer\n"
        "model = SentenceTransformer('all-MiniLM-L6-v2')\n"
        "embeddings = model.encode(texts, normalize_embeddings=True)\n"
        "# Generates 384-dimensional unit-normalized dense vectors"
    )
    story.append(make_code_box("Sentence Transformers Embeddings", code_3))
    story.append(Paragraph("<b>Interview Answer:</b> <i>\"I converted text chunks into 384-dimensional dense vectors using all-MiniLM-L6-v2 with L2-normalization for cosine distance.\"</i>", body_style))
    story.append(Spacer(1, 5))

    story.append(Paragraph("4. Create FAISS Vector Index", h1_style))
    code_4 = (
        "import faiss\n"
        "dim = embeddings.shape[1] # 384\n"
        "index = faiss.IndexFlatIP(dim) # Inner Product similarity\n"
        "index.add(embeddings)\n"
        "scores, indices = index.search(query_vector, top_k=15)"
    )
    story.append(make_code_box("FAISS Vector Index", code_4))
    story.append(Paragraph("<b>Interview Answer:</b> <i>\"I stored the embeddings in a FAISS IndexFlatIP vector database to perform sub-millisecond cosine similarity search over candidate chunks.\"</i>", body_style))
    story.append(Spacer(1, 5))

    story.append(Paragraph("5. Cross-Encoder Re-Ranking", h1_style))
    code_5 = (
        "from sentence_transformers import CrossEncoder\n"
        "reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')\n"
        "pairs = [[query, chunk['text']] for chunk in candidate_chunks]\n"
        "scores = reranker.predict(pairs)\n"
        "ranked_chunks = [c for _, c in sorted(zip(scores, candidate_chunks), reverse=True)][:5]"
    )
    story.append(make_code_box("Cross-Encoder Re-Ranking", code_5))
    story.append(Paragraph("<b>Interview Answer:</b> <i>\"I implemented two-stage retrieval using a Cross-Encoder to compute full query-passage cross-attention and re-rank the top 5 most relevant passages.\"</i>", body_style))
    story.append(Spacer(1, 5))

    story.append(Paragraph("6. LLM Generation &amp; Citation Verification", h1_style))
    code_6 = (
        "import openai\n"
        "client = openai.OpenAI(base_url='http://localhost:11434/v1', api_key='ollama')\n"
        "res = client.chat.completions.create(\n"
        "    model='deepseek-r1:1.5b',\n"
        "    messages=[{'role': 'system', 'content': SYSTEM_PROMPT}, {'role': 'user', 'content': prompt}]\n"
        ")\n"
        "clean_answer = format_and_verify_answer(res.choices[0].message.content, verified_chunks)"
    )
    story.append(make_code_box("LLM Inference & Citation Verification", code_6))
    story.append(Paragraph("<b>Interview Answer:</b> <i>\"I sent the re-ranked passages to a local Ollama LLM (deepseek-r1:1.5b), stripped reasoning traces (&lt;think&gt;), and programmatically verified source-page citations.\"</i>", body_style))

    doc.build(story)
    print(f"Generated {filename} successfully.")

if __name__ == '__main__':
    create_autosar_rag_qa_pdf()
