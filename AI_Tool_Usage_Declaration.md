# AI-Tool Usage Declaration
**AUTOSAR HLD Intelligence & Traceability Assistant** | Tool disclosure table | Editable student verification form

### Student and project details

| Field | Student to complete |
| :--- | :--- |
| **University** | SASTRA Deemed University (confirm if required) |
| **Student name** | ____________________________________________ |
| **Register number** | ____________________________________________ |
| **Project title** | AUTOSAR HLD Intelligence & Traceability Assistant |
| **Date** | ____________________________________________ |

---

### Tool-use disclosure

List every AI tool and pre-trained model used in the project, including tools used for coding assistance. The rows below are a draft based on the project context available at preparation time. Verify each row, change any inaccurate details, add missing tools, and remove any tool that you did not use. “Verified by student” must describe checks you personally performed; it must not be treated as pre-certified.

| AI model / tool | Purpose | Artifact affected | Verified by student |
| :--- | :--- | :--- | :--- |
| **Ollama + deepseek-r1:1.5b** *(or Qwen2.5:3B)* | Local language-model inference for RAG responses. | Generated answers in the AUTOSAR HLD Assistant. | Verify using known-answer questions, cited HLD chunks, contradiction cases, and saved RAG reports. Record final test references: __________________ |
| **Sentence Transformers (all-MiniLM-L6-v2) & Cross-Encoder (ms-marco-MiniLM-L-6-v2)** | Dense vector embeddings and cross-encoder re-ranking for semantic retrieval. | Document/query embeddings, FAISS retrieval index, and candidate ranking. | Verify model/config consistency, vector dimensions, retrieval results, and index rebuild procedure. Record evidence: __________________ |
| **ChatGPT / OpenAI assistant** | Planning, explanation, documentation drafting and/or coding assistance where actually used. | Specify each actual artifact affected, e.g. report text, prompts, tests, or code: __________________ | Compare with repository and test outputs; manually review factual claims and edit before submission. Confirm exact use: __________________ |
| **Antigravity coding assistant** | Coding assistance, architecture refactoring, re-ranker integration, batch runners, or test iteration. | Source modules (`src/`), test suite (`tests/`), `start_app.bat`, `stop_app.bat`, `app.py`. | Read and understand all assisted code; run relevant tests; record command/output: `pytest tests/` (78/78 passed). |
| **Other AI tools / pretrained models** | Add each remaining tool/model actually used. | Artifact affected: __________________ | How the student verified it: __________________ |

---

### Student attestation

I confirm that the disclosure above is complete and accurate to the best of my knowledge. I have reviewed the AI-assisted or model-generated outputs used in the submission and remain responsible for their correctness. I have not represented unverified AI output as confirmed fact and have not fabricated results. I can explain the submitted implementation and the role played by each declared tool/model.

> **Required student action:** Edit the draft tool rows to match actual usage. In particular, confirm whether ChatGPT and Antigravity affected code, tests, or report writing, and identify the exact artifacts. Do not sign until the table is accurate.

---

### Signature

| Student name (print) | Signature | Date |
| :--- | :--- | :--- |
| __________________________ | __________________________ | __________________ |

*The instructor’s instruction PDF requires every student to sign the AI-tool usage declaration and shows these columns: AI Model/Tool, Purpose, Artifact affected, Verified by student. It does not provide an official declaration template or exact wording.*
