# 🤖 AGENTS.md — TraceIQ System Context & Contributor Guide

> **This document is the single source of truth for AI agents (Antigravity, Cursor, Copilot, Claude, ChatGPT) and human collaborators working on TraceIQ.**
> It provides the full problem statement, architecture blueprint, environment setup commands, data schemas, evaluation benchmarks, and strict engineering guidelines.

---

## 🎯 1. Project Overview & Problem Statement

### The Problem
During production outages (e.g. payment service failures, checkout downtime), engineering teams spend critical hours jumping between fragmented systems:
1. Documentation & Runbooks (PDF / Markdown)
2. External Release Notes & Changelogs (Webpages / HTML)
3. Monitoring Dashboards & Latency Spikes (Images / PNGs)
4. War-Room Meeting Conversations (Audio Transcripts)
5. Microservice Logs & Deployment Events (Structured JSON / CSV)

Traditional RAG tools fail because they only parse single documents, strip away exact location metadata, struggle with exact technical error codes (e.g. `PAY-401`), mix up conflicting historical documentation, and hallucinate answers when evidence is missing.

### The Solution: TraceIQ
**TraceIQ** is a multimodal, evidence-grounded incident investigator that:
- Ingests all **5 required evidence types** into **MongoDB Atlas**.
- Retains exact source coordinates (`Page #`, `Line #`, `Timestamp`).
- Employs **Hybrid Search (Reciprocal Rank Fusion)**: combining semantic vector search (`$vectorSearch`) with exact full-text keyword search.
- Reconstructs a chronological incident timeline.
- Detects conflicting documentation (e.g. Redis vs in-memory cache).
- Performs **Evidence-Based Abstention** on ungrounded or speculative requests.
- Presents results in a calm, warm, Gemini-style chat console with transparent reasoning steps.

> **Start here:** [`docs/TraceIQ_PRD.pdf`](docs/TraceIQ_PRD.pdf) is the current product and build plan (v2). Where this file disagrees with the PRD or the code, the PRD and the code win.

---

## 🏗️ 2. Repository Architecture & Layout

```text
Transfinitte_RAG/
├── .gitignore                      # Git ignore rules (.venv, node_modules, .next, .env)
├── .github/
│   └── pull_request_template.md    # Standardized PR template with pre-filled checklists
├── AGENTS.md                       # This comprehensive collaborator & AI agent handbook
├── README.md                       # High-level product overview & demo quickstart
├── learn_documents/                # Educational guide series for beginners & judges
│   ├── 01_what_is_rag_and_traceiq.md
│   ├── 02_architecture_and_deep_dive.md
│   ├── 03_codebase_tour_and_file_guide.md
│   └── 04_the_four_judge_evaluation_tests.md
│
├── backend/                        # Python FastAPI backend service
│   ├── .venv/                      # Isolated virtualenv (do not commit)
│   ├── requirements.txt            # Python dependencies (FastAPI, LangChain, PyMongo)
│   ├── app/
│   │   ├── main.py                 # FastAPI server entrypoint, CORS & routes
│   │   ├── config.py               # Pydantic Settings (MongoDB URI, OpenAI keys)
│   │   ├── core/
│   │   │   └── database.py         # PyMongo / Motor MongoDB Atlas client
│   │   ├── models/
│   │   │   └── schemas.py          # Data models: Citation, TimelineEvent, InvestigationReport
│   │   ├── api/
│   │   │   ├── routes_ingest.py    # Multi-source document & log ingestion
│   │   │   ├── routes_investigate.py # Cross-source investigation query endpoint
│   │   │   └── routes_eval.py      # Ground-truth evaluation runner
│   │   ├── ingestion/
│   │   │   ├── chunking.py         # Location-preserving text chunker
│   │   │   └── parsers/            # PDF, HTML, OCR, Transcript & Log parsers
│   │   ├── retrieval/
│   │   │   ├── vector_search.py    # MongoDB Atlas $vectorSearch aggregation
│   │   │   ├── hybrid_search.py    # Reciprocal Rank Fusion (vector + keyword search)
│   │   │   └── temporal_filter.py  # Timestamp & version-aware filtering
│   │   └── reasoning/
│   │       ├── investigator.py     # LangChain LLM synthesis & root-cause reasoning
│   │       └── abstention.py       # Evidence-based abstention detection
│   ├── synthetic_data/             # Evidence pack for e-commerce payment incident
│   │   ├── documents/              # Runbooks, architecture specs, API schemas
│   │   ├── webpages/               # Gateway v2.4.0 release notes & changelogs
│   │   ├── images/                 # Grafana error spike & latency metric graphs
│   │   ├── transcripts/            # War-room meeting audio & text transcripts
│   │   └── structured_records/     # Microservice JSON logs & deployment timeline
│   └── tests/
│       ├── ground_truth.json       # 4 evaluation test benchmarks for hackathon judges
│       └── test_retrieval.py       # Automated citation precision tests
│
└── frontend/                       # Next.js 16 (App Router) + TypeScript + Tailwind CSS
    ├── package.json                # Frontend dependencies (lucide-react, tailwindcss v4)
    ├── tsconfig.json
    └── src/
        ├── app/
        │   ├── layout.tsx          # HTML root layout
        │   ├── page.tsx            # Main investigator chat dashboard
        │   └── globals.css         # Claymorphic light theme styling tokens
        ├── components/
        │   ├── Header.tsx          # Brand badge, Atlas status & evidence pack trigger
        │   ├── ChatInput.tsx       # Floating claymorphic input & 4 quick-test pills
        │   ├── ChatMessage.tsx     # Assistant card with timeline, citations & banners
        │   ├── ThinkingAccordion.tsx # ChatGPT-style collapsible reasoning accordion
        │   ├── CitationCard.tsx    # Interactive citation cards with exact location
        │   ├── CitationModal.tsx   # Deep inspection modal for extracted passages
        │   └── UploadDrawer.tsx    # Multi-source evidence upload & demo pack loader
        └── lib/
            ├── types.ts            # TypeScript interfaces
            └── mockInvestigation.ts# Ground-truth mock dataset for standalone testing
```

---

## 💻 3. Setting Up on a New PC (Windows / macOS / Linux)

### Prerequisites
- **Git** (v2.30+)
- **Python** (v3.10+ recommended)
- **Node.js** (v18+ or v20+) and **npm**
- **MongoDB Atlas Cluster** (Free Tier M0 or local MongoDB 7.0+)

### Step 1: Clone the Repository
```bash
git clone https://github.com/CodingTJ1507/RAG_Transfinitte.git
cd RAG_Transfinitte
```

### Step 2: Backend Setup
```bash
cd backend

# 1. Create a Python virtual environment
python -m venv .venv

# 2. Activate the virtual environment
# Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# Windows (CMD):
.\.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

# 3. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Create your environment configuration (.env)
# Create a .env file inside the `backend/` folder:
```

#### `backend/.env`
Copy [`backend/.env.example`](backend/.env.example) to `backend/.env` and set `MONGODB_URI` and
`GEMINI_API_KEY`. The app uses Gemini (`gemini-2.5-flash`, `gemini-embedding-001` at 768
dimensions). Every setting is described in the README.

```bash
# 5. Start the FastAPI backend
uvicorn app.main:app --reload --port 8000
```
- API Docs will be live at: `http://localhost:8000/docs`
- Healthcheck endpoint: `http://localhost:8000/health`

### Step 3: Frontend Setup
Open a new terminal window:
```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Start Next.js development server
npm run dev
```
- Web Application will be live at: `http://localhost:3000`

---

## 🗄️ 4. MongoDB Atlas Vector Search Index Configuration

Both indexes live on the `chunks` collection and are defined in
[`backend/scripts/vector_search_index.json`](backend/scripts/vector_search_index.json) (768 dims, cosine)
and [`backend/scripts/atlas_search_index.json`](backend/scripts/atlas_search_index.json) (BM25).
Create them from `backend/` with `python -m scripts.manage_vector_index --create`.

---

## 🧪 5. The 4 Judge Evaluation Benchmarks

The test set is the 20 questions in
[`backend/synthetic_data/evaluation/questions.json`](backend/synthetic_data/evaluation/questions.json)
with expected sources in `expected_sources.json` (run `GET /api/eval/benchmark`). The four demo questions:

| ID | Category | Query | Expectation |
| :--- | :--- | :--- | :--- |
| **Q05** | Cross-source | *"Why did payment requests start failing after the latest deployment? Reconstruct the timeline, identify the most likely cause, explain the evidence, and recommend the next diagnostic step."* | Timeline 10:02 deploy to 10:05:12 first PAY-401; legacy `card_token` rejected after schemaguard 3.0; cause marked as inference; cites logs, request records, release notes, schemaguard notes, spec, handover. |
| **Q06** | Exact lookup | *"Is PAY-401 an authentication error?"* | No: the spec maps PAY-401 to HTTP 422 validation failure; logs and screenshot show 422. |
| **Q15** | Conflicting evidence | *"The initial report blames a credential problem. Is that still the best explanation?"* | No: the 10:18 report was early; no key rotation since 2026-10-09; status 422 means validation. |
| **Q17** | Unanswerable | *"Which person approved the payment-service 2.4.0 production deploy?"* | Abstain: there is no approval record; must not name anyone. |

The full product and build plan, including the junior task cards, is
[`docs/TraceIQ_PRD.pdf`](docs/TraceIQ_PRD.pdf).

---

## 📋 6. Strict Guidelines for AI Agents & Collaborators

When contributing code or documentation to this repository, **strictly adhere to these 5 rules**:

### 🚨 Rule 1: Never Push Directly to `main`
- **Always branch off** from `main`:
  - `feat/<feature-name>` for new features
  - `fix/<bug-name>` for bug fixes
  - `docs/<doc-name>` for documentation updates
- **Always generate a pre-filled Pull Request link** with Title, Description, Changes, Concepts, and Verification details pre-encoded so the repository maintainer only has to click to open the PR.

### 📌 Rule 2: Location-Preserving Ingestion
- When chunking documents, transcripts, or logs, **never discard metadata**.
- Every chunk must preserve:
  - `source_id` (e.g. `doc-runbook-18`)
  - `source_type` (`document` | `webpage` | `image` | `transcript` | `structured_record`)
  - `location` (`Page 14`, `Line 804`, `Timestamp 10:14:32`)
  - `snippet` (the exact source text chunk)

### 🛡️ Rule 3: Evidence Grounding & Abstention
- The LLM must never generate claims without citing a retrieved chunk.
- If the retrieved evidence is empty or does not support the premise, the system **must invoke abstention** (`is_abstention: true`) rather than generating plausible fiction.

### 🎨 Rule 4: Frontend Theme Integrity
- The frontend uses a **calm, warm, Gemini-style layout** (alabaster and oatmeal tones, sidebar, pill input, muted citation badges). Keep it; do not redesign.
- **Avoid**: dark sci-fi themes, loud neon glowing borders, or generic AI chat templates.
- **Maintain**: the ChatGPT/DeepSeek-style collapsible `ThinkingAccordion`, clickable `CitationCard`s, and `CitationModal` inspector.

### 🗣️ Rule 5: Transparent Communication & Explanations
- Before starting a significant task, outline the approach.
- After completing every milestone, pause and explain what was accomplished, why technical choices were made, and provide the exact PR link.
