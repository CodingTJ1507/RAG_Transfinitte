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
- Presents results in a light, tactile **Claymorphic chat console** with ChatGPT-style thinking transparency.

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

#### `backend/.env` Schema:
```ini
# MongoDB Atlas Connection
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=traceiq_db
MONGODB_VECTOR_INDEX=traceiq_vector_index

# LLM & Embedding Model API Keys
OPENAI_API_KEY=your-openai-api-key-here
LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small

# Server Settings
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

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

In MongoDB Atlas, create a Search Index on the `chunks` collection:
- **Database**: `traceiq_db`
- **Collection**: `chunks`
- **Index Name**: `traceiq_vector_index`
- **Index Definition (JSON)**:
> Note: For Google Gemini (`models/text-embedding-004`), use `"numDimensions": 768`. For OpenAI (`text-embedding-3-small`), use `1536`.
```json
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 768,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "source_type"
    },
    {
      "type": "filter",
      "path": "service"
    },
    {
      "type": "filter",
      "path": "version"
    }
  ]
}
```

---

## 🧪 5. The 4 Judge Evaluation Benchmarks

All AI agents and contributors must ensure that the pipeline satisfies the ground-truth benchmarks in [`backend/tests/ground_truth.json`](backend/tests/ground_truth.json):

| Test ID | Category | Query | Ground-Truth Expectation |
| :--- | :--- | :--- | :--- |
| **`TEST-01-CROSS-SOURCE`** | Cross-Source Reasoning | *"Why did payment failures begin after yesterday's deployment?"* | Must connect deployment time (10:02 AM), log errors (10:07 AM), release notes v2.4.0 (breaking `idempotency_key`), API spec mismatch, and transcript remarks with clickable citations for every claim. |
| **`TEST-02-EXACT-LOOKUP`** | Exact Keyword Search | *"Find every occurrence of error code PAY-401 and compare the affected versions."* | Must use exact text matching to identify 48 matches in version 2.4.0 and 0 matches in version 2.3.9 without hallucinating similar codes. |
| **`TEST-03-CONFLICTING-EVIDENCE`** | Contradiction Reasoning | *"The runbook says the service uses Redis, but the latest architecture diagram shows an in-memory cache. Which is correct?"* | Must identify direct contradiction between Runbook v1.8 and Diagram v2.2, inspect date metadata, and flag the ambiguity rather than guessing. |
| **`TEST-04-UNANSWERABLE`** | Evidence-Based Abstention | *"Which engineer secretly caused the outage, and what exact line of code did they change?"* | Must decline to speculate on personal intent or blame. Explicitly state that logs/specs lack commit blame records and specify needed audit logs. |

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
- The frontend uses a **light, tactile Claymorphic aesthetic** (soft 3D pillowy shadows, inset input fields, clean notes/paper tone).
- **Avoid**: dark sci-fi themes, loud neon glowing borders, or generic AI chat templates.
- **Maintain**: the ChatGPT/DeepSeek-style collapsible `ThinkingAccordion`, clickable `CitationCard`s, and `CitationModal` inspector.

### 🗣️ Rule 5: Transparent Communication & Explanations
- Before starting a significant task, outline the approach.
- After completing every milestone, pause and explain what was accomplished, why technical choices were made, and provide the exact PR link.
