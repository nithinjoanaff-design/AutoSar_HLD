"""
llm_provider.py
---------------
Abstracts LLM access and human-friendly structured answer generation.
Supports OpenRouter, Ollama (Local & Cloud), OpenAI, Anthropic, and
structured extractive-evidence mode.
API keys and endpoints are read exclusively from environment variables – never hardcoded.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ── Human-Friendly System & Prompt Templates ──────────────────────────────────

SYSTEM_PROMPT = """You are a senior AUTOSAR software architecture specialist and automotive systems engineer.
Answer questions about automotive High-Level Design (HLD) specifications accurately, clearly, and concisely.

CRITICAL RULES:
1. Output ONLY the final answer. NEVER output internal thoughts, monologues, or reasoning traces.
2. Base all statements strictly on the provided document evidence passages.
3. For all citations and tables, you MUST cite the EXACT document filename (e.g., bcm_hld.pdf) and exact page number from the evidence. Never write placeholders like '[Document Name]'.
4. Provide ONLY the 3 requested sections: Executive Summary, Architectural Breakdown, and Evidence & Citations Summary."""

STRUCTURED_ANSWER_PROMPT = """Document Evidence Passages:
{context}

---
Question: {question}

Instructions:
Provide a clear, human-friendly architectural response using EXACTLY these 3 sections. Do not include any internal thoughts:

### 💡 Executive Summary
[Direct, clear explanation answering the question based on the evidence passages above. Cite specific facts inline using the real document filename and page number.]

### 🏗️ Architectural Breakdown
- **Software Components / Modules:** [Components identified and their responsibilities]
- **Interfaces & Ports:** [Provided and required ports/interfaces identified]
- **Signals & Messages:** [Signals, datatypes, or CAN IDs identified]
- **Functional Flows & Dependencies:** [Sequences, flows, or module dependencies identified]

### 📑 Evidence & Citations Summary
| # | Document | Page | Key Supported Architecture Fact |
|---|---|---|---|
[Table citing the exact Document filename and Page number for each evidence passage used]
"""

SUMMARY_PROMPT = """Document Title / Context: {doc_name}

Text Excerpts from Document:
{context}

---
Instructions:
Write an executive architectural summary of this AUTOSAR High-Level Design (HLD) document in a clear, human-friendly, and professional tone.
Output only the summary with these sections:
1. **Executive Overview**: High-level purpose of the ECU/system and platform.
2. **Key Software Components**: Main SWCs identified and their functional responsibilities.
3. **Communication & Bus Architecture**: Interfaces, bus types (CAN/LIN/Ethernet), and signal handling.
4. **Basic Software (BSW) & OS Stack**: Configured BSW layers, diagnostics, memory, or RTOS.
"""


def strip_reasoning_trace(text: str) -> str:
    """Completely strip all LLM reasoning traces (<think>, <details>, etc.)."""
    if not text:
        return ""
    # Strip <think>...</think> completely
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Strip any dangling/unclosed <think> tag if output was cut off
    text = re.sub(r"<think>.*", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"</think>", "", text, flags=re.IGNORECASE)
    # Strip any <details> tags and reasoning headers
    text = re.sub(r"<details.*?</details>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"</?details.*?>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</?summary.*?>", "", text, flags=re.IGNORECASE)
    # Strip any lines like "Alright, so I'm trying to..." at start if outside think tags
    return text.strip()


def build_verified_citations_table(chunks: List[Dict]) -> str:
    """Build a 100% verified Evidence & Citations table directly from retrieved chunks."""
    rows = []
    for i, chunk in enumerate(chunks, 1):
        doc = chunk.get("doc_name", "Unknown Document")
        page = chunk.get("page_number", 1)
        raw_text = re.sub(r"\s+", " ", chunk.get("text", "")).strip()
        first_sentence = re.split(r"(?<=[.!?])\s+", raw_text)[0].strip()
        if len(first_sentence) < 15 and len(raw_text) > 20:
            first_sentence = raw_text[:110]
        first_sentence = first_sentence[:110].replace("|", "-").strip()
        if not first_sentence.endswith((".", "…", "...")):
            first_sentence += "..."
        rows.append(f"| {i} | `{doc}` | Page {page} | {first_sentence} |")

    return (
        "| # | Document | Page | Key Supported Architecture Fact |\n"
        "|---|---|---|---|\n"
        + "\n".join(rows)
    )


def format_and_verify_answer(raw_answer: str, chunks: List[Dict]) -> str:
    """
    Ensure the answer contains strictly the 3 required sections:
    1. Executive Summary
    2. Architectural Breakdown
    3. Evidence & Citations Summary (with verified document names and page numbers)
    Completely removes all reasoning traces (<think>, <details>) and disclaimers.
    """
    clean_text = strip_reasoning_trace(raw_answer)

    # Remove any trailing extra sections (Engineering Notes, Limitations, Disclaimers, etc.)
    clean_text = re.split(
        r"###\s*.*?(?:Engineering Notes|Verification|Limitations|Disclaimers|Notice)",
        clean_text,
        flags=re.IGNORECASE,
    )[0].strip()

    verified_table = build_verified_citations_table(chunks)

    # Check if a citations/summary table exists in clean_text
    table_match = re.search(
        r"(###\s*.*?(?:Evidence|Citations|Summary Table|Table).*?\n)([\s\S]*?)(?=(?:###|$))",
        clean_text,
        flags=re.IGNORECASE,
    )

    if table_match:
        table_header = "### 📑 Evidence & Citations Summary\n"
        table_content = table_match.group(2).strip()
        lines = [ln.strip() for ln in table_content.splitlines() if ln.strip().startswith("|")]
        data_rows = [
            ln for ln in lines
            if not ln.startswith("|---") and "Document" not in ln and "Page" not in ln and not ln.startswith("| #")
        ]

        if not data_rows or any("[document name]" in r.lower() or "[docname]" in r.lower() or "document name" in r.lower() for r in data_rows):
            # Replace placeholder table with ground-truth verified table
            clean_text = clean_text[: table_match.start()] + f"{table_header}{verified_table}"
        else:
            # Reconcile each row with actual ground truth chunks to guarantee right page and doc name
            fixed_rows = []
            for idx, row in enumerate(data_rows):
                cols = [c.strip() for c in row.split("|")[1:-1]]
                if len(cols) >= 3 and idx < len(chunks):
                    true_doc = chunks[idx].get("doc_name", cols[1])
                    true_page = chunks[idx].get("page_number", cols[2])
                    fact = cols[3] if len(cols) >= 4 else cols[-1]
                    fixed_rows.append(f"| {idx + 1} | `{true_doc}` | Page {true_page} | {fact} |")
                else:
                    fixed_rows.append(row)

            if fixed_rows:
                fixed_table = (
                    "| # | Document | Page | Key Supported Architecture Fact |\n"
                    "|---|---|---|---|\n"
                    + "\n".join(fixed_rows)
                )
                clean_text = clean_text[: table_match.start()] + f"{table_header}{fixed_table}"
            else:
                clean_text = clean_text[: table_match.start()] + f"{table_header}{verified_table}"
    else:
        # Append verified table if table was missing
        clean_text = f"{clean_text}\n\n### 📑 Evidence & Citations Summary\n{verified_table}"

    # Ensure clean header naming for the first two sections
    clean_text = re.sub(
        r"^###\s*.*?(?:Direct Answer|Executive Summary|Summary).*?$",
        "### 💡 Executive Summary",
        clean_text,
        count=1,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    clean_text = re.sub(
        r"###\s*.*?(?:Architectural Breakdown|Architecture Breakdown).*?$",
        "### 🏗️ Architectural Breakdown",
        clean_text,
        count=1,
        flags=re.MULTILINE | re.IGNORECASE,
    )

    # Double-check: strip any stray reasoning traces one final time
    clean_text = strip_reasoning_trace(clean_text)

    return clean_text.strip()


def build_context(retrieved_chunks: List[Dict]) -> str:
    """Format retrieved and re-ranked chunks with explicit ground-truth document and page metadata."""
    parts = []
    for i, chunk in enumerate(retrieved_chunks, 1):
        doc_name = chunk.get("doc_name", "Unknown Document")
        page_num = chunk.get("page_number", "?")
        rerank_score = chunk.get("rerank_score")
        score_info = f" (Re-rank Score: {rerank_score:.3f})" if rerank_score is not None else ""
        parts.append(
            f"=== EVIDENCE PASSAGE [{i}] ===\n"
            f"DOCUMENT FILENAME: {doc_name}\n"
            f"PAGE NUMBER: {page_num}{score_info}\n"
            f"TEXT CONTENT:\n{chunk.get('text', '')}"
        )
    return "\n\n".join(parts)


class LLMProvider:
    """
    Provides human-friendly structured answer generation via configurable LLM backends:
    - OpenRouter (free & commercial models across OpenAI, Anthropic, Meta, Google, Mistral)
    - Ollama (Local or Cloud/Remote instance)
    - OpenAI
    - Anthropic
    - Structured extractive synthesis when no LLM is configured ("none")
    """

    def __init__(self) -> None:
        self.provider = os.getenv("LLM_PROVIDER", "none").lower().strip()
        self._client = None
        self._model = None
        self._init_client()

    def _init_client(self) -> None:
        if self.provider == "openrouter":
            self._init_openrouter()
        elif self.provider == "ollama":
            self._init_ollama()
        elif self.provider == "openai":
            self._init_openai()
        elif self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "none":
            logger.info("LLM_PROVIDER=none – running in structured extractive evidence mode.")
        else:
            logger.warning(
                "Unknown LLM_PROVIDER '%s'. Running in structured extractive evidence mode.",
                self.provider,
            )
            self.provider = "none"

    def _init_openrouter(self) -> None:
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            logger.warning("OPENROUTER_API_KEY not set. Falling back to extractive mode.")
            self.provider = "none"
            return
        try:
            import openai  # type: ignore

            base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
            self._model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")
            default_headers = {
                "HTTP-Referer": os.getenv("OPENROUTER_SITE_URL", "https://github.com/autosar-hld-assistant"),
                "X-Title": os.getenv("OPENROUTER_APP_NAME", "AUTOSAR HLD Assistant"),
            }
            self._client = openai.OpenAI(
                api_key=api_key,
                base_url=base_url,
                default_headers=default_headers,
            )
            logger.info("OpenRouter client initialized with model: %s", self._model)
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
            self.provider = "none"
        except Exception as exc:  # noqa: BLE001
            logger.error("OpenRouter init error: %s", exc)
            self.provider = "none"

    def _init_ollama(self) -> None:
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        api_key = os.getenv("OLLAMA_API_KEY", "ollama").strip() or "ollama"
        self._model = os.getenv("OLLAMA_MODEL", "deepseek-r1:1.5b")
        try:
            import openai  # type: ignore

            self._client = openai.OpenAI(
                base_url=base_url,
                api_key=api_key,
            )
            logger.info("Ollama client initialized at %s with model: %s", base_url, self._model)
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
            self.provider = "none"
        except Exception as exc:  # noqa: BLE001
            logger.error("Ollama init error: %s", exc)
            self.provider = "none"

    def _init_openai(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. Falling back to extractive mode.")
            self.provider = "none"
            return
        try:
            import openai  # type: ignore

            self._client = openai.OpenAI(api_key=api_key)
            self._model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
            logger.info("OpenAI client initialized with model: %s", self._model)
        except ImportError:
            logger.error("openai package not installed. Run: pip install openai")
            self.provider = "none"
        except Exception as exc:  # noqa: BLE001
            logger.error("OpenAI init error: %s", exc)
            self.provider = "none"

    def _init_anthropic(self) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set. Falling back to extractive mode.")
            self.provider = "none"
            return
        try:
            import anthropic as ant  # type: ignore

            self._client = ant.Anthropic(api_key=api_key)
            self._model = os.getenv("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
            logger.info("Anthropic client initialized with model: %s", self._model)
        except ImportError:
            logger.error("anthropic package not installed. Run: pip install anthropic")
            self.provider = "none"
        except Exception as exc:  # noqa: BLE001
            logger.error("Anthropic init error: %s", exc)
            self.provider = "none"

    @property
    def is_configured(self) -> bool:
        return self.provider not in ("none",)

    def answer(self, question: str, retrieved_chunks: List[Dict]) -> Dict:
        """
        Generate a human-friendly structured answer given a question and re-ranked context chunks.

        Returns
        -------
        dict with keys:
            answer : str
            mode   : "llm" | "extractive" | "no_results"
            citations : list of {doc_name, page_number}
            provider : str
        """
        citations = [
            {"doc_name": c["doc_name"], "page_number": c["page_number"]}
            for c in retrieved_chunks
        ]
        # Deduplicate citations preserving order
        seen = set()
        unique_citations = []
        for c in citations:
            key = (c["doc_name"], c["page_number"])
            if key not in seen:
                seen.add(key)
                unique_citations.append(c)

        if not retrieved_chunks:
            return {
                "answer": (
                    "### ⚠️ No Relevant Evidence Found\n\n"
                    "No relevant passages were found in the indexed documents for this query. "
                    "Please ensure the appropriate AUTOSAR HLD documents are uploaded and processed."
                ),
                "mode": "no_results",
                "citations": [],
                "provider": self.provider,
            }

        if not self.is_configured:
            return self._structured_extractive_answer(question, retrieved_chunks, unique_citations)

        if self.provider in ("openrouter", "ollama", "openai"):
            return self._openai_compatible_answer(question, retrieved_chunks, unique_citations)
        elif self.provider == "anthropic":
            return self._anthropic_answer(question, retrieved_chunks, unique_citations)

        return self._structured_extractive_answer(question, retrieved_chunks, unique_citations)

    def _openai_compatible_answer(
        self, question: str, chunks: List[Dict], citations: List[Dict]
    ) -> Dict:
        context = build_context(chunks)
        prompt = STRUCTURED_ANSWER_PROMPT.format(context=context, question=question)

        try:
            max_tokens = 2500 if "deepseek" in str(self._model).lower() else 1600
            response = self._client.chat.completions.create(  # type: ignore[union-attr]
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=max_tokens,
            )
            raw_answer = response.choices[0].message.content or ""
            clean_answer = format_and_verify_answer(raw_answer, chunks)

            return {
                "answer": clean_answer,
                "mode": "llm",
                "citations": citations,
                "provider": f"{self.provider}/{self._model}",
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("%s API error: %s. Falling back to extractive mode.", self.provider.title(), exc)
            return self._structured_extractive_answer(question, chunks, citations)

    def _anthropic_answer(
        self, question: str, chunks: List[Dict], citations: List[Dict]
    ) -> Dict:
        context = build_context(chunks)
        prompt = STRUCTURED_ANSWER_PROMPT.format(context=context, question=question)

        try:
            response = self._client.messages.create(  # type: ignore[union-attr]
                model=self._model,
                max_tokens=1600,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
            )
            raw_answer = response.content[0].text
            clean_answer = format_and_verify_answer(raw_answer, chunks)

            return {
                "answer": clean_answer,
                "mode": "llm",
                "citations": citations,
                "provider": f"anthropic/{self._model}",
            }
        except Exception as exc:  # noqa: BLE001
            logger.error("Anthropic API error: %s. Falling back to extractive mode.", exc)
            return self._structured_extractive_answer(question, chunks, citations)

    def summarize_document(self, text_context: str, doc_name: str) -> Optional[str]:
        """
        Generate an executive document architecture summary using the configured LLM.
        Returns None if no LLM is configured or if an error occurs.
        """
        if not self.is_configured:
            return None

        prompt = SUMMARY_PROMPT.format(doc_name=doc_name, context=text_context[:8000])

        try:
            if self.provider in ("openrouter", "ollama", "openai"):
                max_tokens = 2000 if "deepseek" in str(self._model).lower() else 1200
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=max_tokens,
                )
                raw_summary = response.choices[0].message.content or ""
                return strip_reasoning_trace(raw_summary)
            elif self.provider == "anthropic":
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=1200,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}],
                )
                raw_summary = response.content[0].text
                return strip_reasoning_trace(raw_summary)
        except Exception as exc:  # noqa: BLE001
            logger.error("Error generating LLM summary: %s", exc)
            return None
        return None

    def _structured_extractive_answer(
        self, question: str, chunks: List[Dict], citations: List[Dict]
    ) -> Dict:
        """
        Synthesize a direct, friendly, and properly structured engineering answer
        from the top re-ranked passages when no external LLM is configured.
        Contains strictly: Executive Summary, Architectural Breakdown, Evidence & Citations Summary.
        """
        all_text = " ".join(c["text"] for c in chunks)

        # 1. Extract architectural entities present in top chunks
        components = sorted(
            set(
                re.findall(
                    r"\b([A-Z][a-zA-Z0-9]+(?:Manager|Controller|Module|Handler|Monitor|Gateway|Receiver|Actuator|Sensor))\b",
                    all_text,
                )
            )
        )
        interfaces = sorted(
            set(
                re.findall(
                    r"\b([A-Za-z0-9_]*(?:Port|Interface|ServicePort))\b",
                    all_text,
                )
            )
        )
        signals = sorted(
            set(
                re.findall(
                    r"\b([A-Za-z0-9_]*(?:Signal|Sig|Msg|Cmd))\b",
                    all_text,
                )
            )
        )
        bsw_stack = sorted(
            set(
                re.findall(
                    r"\b(RTE|MCAL|BSW|OS|CANIF|PDUR|COM|DEM|DCM|NVM|WDG|SPI|PWM|ADC|DIO|CAN|LIN|Ethernet)\b",
                    all_text,
                )
            )
        )

        # 2. Extract key relevant sentences matching the query
        q_words = [w.lower() for w in re.findall(r"\w+", question) if len(w) > 2]
        scored_sentences = []
        for chunk in chunks:
            raw_sents = re.split(r"(?<=[.!?])\s+", chunk["text"])
            for s in raw_sents:
                clean_s = s.strip()
                clean_s = re.sub(r"\s+", " ", clean_s)
                if len(clean_s) > 25:
                    match_count = sum(1 for w in q_words if w in clean_s.lower())
                    if match_count > 0:
                        scored_sentences.append(
                            (match_count, chunk["doc_name"], chunk["page_number"], clean_s)
                        )

        # Deduplicate sentences while preserving highest score
        seen_sents = set()
        unique_scored_sents = []
        for item in sorted(scored_sentences, key=lambda x: x[0], reverse=True):
            normalized = item[3].lower()[:60]
            if normalized not in seen_sents:
                seen_sents.add(normalized)
                unique_scored_sents.append(item)

        # 3. Formulate the Direct Answer
        if unique_scored_sents:
            primary_points = [
                f"{item[3]} **[{item[1]}, Page {item[2]}]**"
                for item in unique_scored_sents[:4]
            ]
            direct_answer_body = "\n\n".join(primary_points)
        else:
            top_c = chunks[0]
            clean_snippet = re.sub(r"\s+", " ", top_c["text"][:350].strip())
            direct_answer_body = (
                f"{clean_snippet} **[{top_c['doc_name']}, Page {top_c['page_number']}]**"
            )

        # 4. Extract functional flows / sequence if present
        flow_sentences = [
            re.sub(r"\s+", " ", s.strip())
            for s in re.split(r"(?<=[.!?])\s+", all_text)
            if any(k in s.lower() for k in ("sequence", "flow", "step", "trigger", "initialization", "startup", "callback"))
            and len(s.strip()) > 30
        ]
        flow_summary = ""
        if flow_sentences:
            flow_points = "\n".join(f"- {s[:160]}..." if len(s) > 160 else f"- {s}" for s in flow_sentences[:3])
            flow_summary = f"\n\n**Functional Flows & Sequences:**\n{flow_points}"

        # 5. Extract dependencies if present
        dep_sentences = [
            re.sub(r"\s+", " ", s.strip())
            for s in re.split(r"(?<=[.!?])\s+", all_text)
            if any(k in s.lower() for k in ("depends on", "uses", "interfaces with", "communicates with", "provides", "requires"))
            and len(s.strip()) > 25
        ]
        dep_summary = ""
        if dep_sentences:
            dep_points = "\n".join(f"- {s[:160]}..." if len(s) > 160 else f"- {s}" for s in dep_sentences[:3])
            dep_summary = f"\n\n**Dependencies & Interactions:**\n{dep_points}"

        # 6. Format Key Architectural Elements
        comp_str = ", ".join(f"`{c}`" for c in components[:8]) if components else "_None explicitly detected in retrieved passages_"
        iface_str = ", ".join(f"`{i}`" for i in interfaces[:8]) if interfaces else "_None explicitly detected_"
        sig_str = ", ".join(f"`{s}`" for s in signals[:8]) if signals else "_None explicitly detected_"
        bsw_str = ", ".join(f"`{b}`" for b in bsw_stack[:8]) if bsw_stack else "_None explicitly detected_"

        # 7. Build Ground-Truth Verified Citations Table
        verified_matrix_table = build_verified_citations_table(chunks)

        # 8. Assemble Clean, Proper Answer with strictly the 3 sections
        answer = (
            "### 💡 Executive Summary (Extractive Synthesis)\n"
            f"{direct_answer_body}\n\n"
            "### 🏗️ Architectural Breakdown\n"
            f"- **Software Components / Modules:** {comp_str}\n"
            f"- **Interfaces & Ports:** {iface_str}\n"
            f"- **Signals & CAN Messages:** {sig_str}\n"
            f"- **BSW & Infrastructure Layers:** {bsw_str}"
            f"{flow_summary}"
            f"{dep_summary}\n\n"
            "### 📑 Evidence & Citations Summary\n"
            f"{verified_matrix_table}"
        )

        return {
            "answer": answer,
            "mode": "extractive",
            "citations": citations,
            "provider": "none",
        }
