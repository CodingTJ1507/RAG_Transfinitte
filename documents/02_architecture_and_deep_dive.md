# 🔬 Chapter 2: Technical Architecture & Deep Dive

---

## 1. High-Level System Architecture

TraceIQ is built as a modular system with four core stages:

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        1. INGESTION & PARSING                          │
│                                                                        │
│   PDF / Markdown        Web HTML           Images         Transcripts  │
│   (pypdf)             (BeautifulSoup)     (Vision/OCR)    (JSON/Text)  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     2. LOCATION-PRESERVING CHUNKING                    │
│                                                                        │
│   Text chunks generated while strictly preserving:                    │
│   - Source ID & Title                                                  │
│   - Page numbers, video/audio timestamps, line numbers                 │
│   - Service name & version metadata (e.g., v2.3.9 vs v2.4.0)          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    3. MONGODB ATLAS UNIFIED STORAGE                    │
│                                                                        │
│   Collection: sources   --> Original metadata and file origins         │
│   Collection: chunks    --> Text chunk + 1536-dim Embedding + Loc     │
│   Collection: events    --> Structured log events with exact time      │
└───────────────────┬────────────────────────────────┬───────────────────┘
                    │                                │
                    ▼                                ▼
       [Atlas $vectorSearch]             [Full-Text / Exact Match]
       (Semantic Meaning)                (Codes: PAY-401, v2.4.0)
                    │                                │
                    └────────────────┬───────────────┘
                                     │
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  4. HYBRID RERANKING (RRF) & SYNTHESIS                 │
│                                                                        │
│   Reciprocal Rank Fusion (RRF) blends semantic & keyword rank          │
│   LangChain orchestrates LLM to extract:                               │
│   - Incident Timeline & Likely Root Cause                              │
│   - Supporting Citations & Conflicting Evidence                        │
│   - Evidence-based Abstention if unanswerable                          │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     5. NEXT.JS INVESTIGATOR UI                         │
│                                                                        │
│   Interactive Incident Timeline  |  Evidence Graph                     │
│   Source Inspector Drawer        |  One-Click Citation Jumper          │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. What is an Embedding?

Computers cannot inherently understand words; they only understand numbers.

An **Embedding Model** (such as OpenAI's `text-embedding-3-small`) reads a chunk of text and translates its semantic meaning into a list of numbers (a vector), typically 1,536 numbers long:

```python
# Example representation of an embedding vector:
[0.0124, -0.0451, 0.8291, ..., 0.0039]  # 1536 numbers
```

- Phrases with similar meanings end up close together in mathematical space:
  - *"payment gateway failure"* and *"checkout HTTP 500 error"* have high similarity (~0.89).
  - *"lunch menu cafeteria"* and *"database connection pool"* have very low similarity (~0.12).

---

## 3. MongoDB Vector Search vs Keyword Search

Neither Vector Search nor Keyword Search is enough on its own:

### Why Vector Search Alone Isn't Enough
- **Strength**: Understands synonyms and concepts. Searching *"why did payments break"* will find *"credit card processing rejected"*.
- **Weakness**: Completely blind to exact alphanumeric codes. If you search for error code `PAY-401`, a vector search might return `ERR-502` because both are "error codes".

### Why Keyword Search Alone Isn't Enough
- **Strength**: Finds exact tokens (`PAY-401`, `v2.4.0`, `192.168.1.1`).
- **Weakness**: Completely misses conceptual matches if the exact keyword isn't present in the document.

### The Solution: Hybrid Search with Reciprocal Rank Fusion (RRF)
TraceIQ runs **both** searches simultaneously in MongoDB Atlas:
1. Vector Search returns Top-10 candidates based on conceptual similarity.
2. Exact Text Search returns Top-10 candidates matching exact codes.
3. **Reciprocal Rank Fusion (RRF)** combines their ranks using the formula:
   $$\text{RRF Score} = \frac{1}{60 + \text{Rank}_{\text{vector}}} + \frac{1}{60 + \text{Rank}_{\text{keyword}}}$$
This guarantees that results matching *both* meaning and exact identifiers appear right at the top.

---

## 4. Why We Chose This Tech Stack

- **FastAPI (Python)**: The industry standard for AI backends. Python has native support for LangChain, NumPy, PyPDF, and ML libraries, while FastAPI provides high-speed asynchronous endpoints with automatic OpenAPI documentation (`/docs`).
- **LangChain**: A framework that manages prompts, document splitters, and output parsers, keeping your business logic clean and modular.
- **MongoDB Atlas**: Unifies original documents, structured log events, chunks, and vector embeddings in a single database. You don't need a separate vector database (like Pinecone) plus a relational database — MongoDB handles both.
- **Next.js (React + TypeScript)**: Delivers a responsive, server-rendered incident investigation console with rich components for timelines and citation drawers.
