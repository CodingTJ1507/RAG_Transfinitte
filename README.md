# 🕵️‍♂️ TraceIQ — The Evidence-Grounded Engineering Investigator

> **Multimodal, evidence-grounded incident investigation agent for complex software systems.**
> Built with **MongoDB Atlas (Vector Search + Hybrid Search)**, **LangChain**, **FastAPI**, and **Next.js**.

---

## 🎯 Project Overview

When a critical production failure strikes (e.g. payment gateway outages, API latency spikes), engineers waste hours jumping between disparate systems:
1. **Architecture docs & runbooks** (Markdown / PDF)
2. **Release notes & changelogs** (Webpages / HTML)
3. **Monitoring dashboards & latency spikes** (Images / Screenshots)
4. **War-room incident discussions** (Transcripts)
5. **Microservice logs & deployment records** (Structured JSON / CSV)

**TraceIQ** bridges this fragmentation. Instead of querying isolated tools, TraceIQ ingests all five evidence types into MongoDB Atlas, executes **hybrid semantic + keyword retrieval**, builds a cross-source timeline, flags contradictions, and synthesizes an evidence-backed incident report with exact citations.

---

## 🏗️ Repository & Directory Architecture

```text
Transfinitte_RAG/
├── .gitignore                      # Python, Node, Next.js, and environment ignore rules
├── README.md                       # Comprehensive project & architecture guide
│
├── backend/                        # Python FastAPI backend service
│   ├── .venv/                      # Python virtual environment (LangChain, MongoDB, FastAPI)
│   ├── .env.example                # MongoDB Atlas URI, OpenAI keys, port configurations
│   ├── requirements.txt            # Python dependencies
│   │
│   ├── app/
│   │   ├── main.py                 # FastAPI application entrypoint & middleware
│   │   ├── config.py               # Pydantic environment & database settings
│   │   ├── core/
│   │   │   └── database.py         # MongoDB Atlas connection manager (PyMongo / Motor)
│   │   ├── models/
│   │   │   └── schemas.py          # Data models: Source, Citation, Timeline, Report
│   │   ├── api/
│   │   │   ├── routes_ingest.py    # Multi-source document & log ingestion endpoints
│   │   │   ├── routes_investigate.py # Cross-source reasoning & query endpoint
│   │   │   └── routes_eval.py      # Ground-truth evaluation & benchmark routes
│   │   ├── ingestion/
│   │   │   ├── chunking.py         # Location-preserving chunking (page, timestamp, line)
│   │   │   └── parsers/            # Source parsers (PDF, HTML, OCR/Vision, Transcripts, JSON)
│   │   ├── retrieval/
│   │   │   ├── vector_search.py    # MongoDB Atlas $vectorSearch aggregation
│   │   │   ├── hybrid_search.py    # Reciprocal Rank Fusion (RRF): vector + exact keyword
│   │   │   └── temporal_filter.py  # Timestamp & version-aware filtering
│   │   └── reasoning/
│   │       ├── investigator.py     # LangChain cross-source synthesis & root-cause reasoning
│   │       ├── graph_builder.py    # Incident timeline & dependency evidence graph
│   │       └── abstention.py       # Evidence-based abstention (detecting unanswerable claims)
│   │
│   ├── synthetic_data/             # Benchmark evidence pack (E-commerce payment incident)
│   │   ├── documents/              # Runbooks, architecture specifications, API schemas
│   │   ├── webpages/               # Release notes (v2.4.0) and changelogs
│   │   ├── images/                 # Grafana monitoring dashboard error spikes
│   │   ├── transcripts/            # Incident war-room transcripts
│   │   └── structured_records/     # Microservice JSON logs & deployment timeline
│   │
│   └── tests/
│       ├── ground_truth.json       # 4 evaluation test benchmarks for hackathon judges
│       └── test_retrieval.py       # Automated retrieval & citation precision tests
│
└── frontend/                       # Modern Next.js TypeScript web application
    ├── src/
    │   ├── app/                    # Next.js App Router (Layout & Pages)
    │   ├── components/             # UI Components (Timeline, Citation drawer, Evidence graph)
    │   └── lib/                    # API clients and state helpers
    ├── package.json
    ├── tailwind.config.ts
    └── tsconfig.json
```

---

## 🔬 Multi-Source Evidence Schema

All ingested items are stored together in MongoDB Atlas across collections:

| Collection | Role |
| :--- | :--- |
| **`sources`** | Raw source files, source type, version metadata, and origin |
| **`chunks`** | Extracted text chunks, embeddings (`text-embedding-3-small`), and exact location markers (page, timestamp, line) |
| **`events`** | Structured timestamped logs, deployments, and alerts |
| **`investigations`** | Stored queries, evidence graphs, confidence scores, and citation links |

---

## 🧪 4 Judge Evaluation Benchmarks

Defined in [`backend/tests/ground_truth.json`](backend/tests/ground_truth.json):

1. **Test 1 — Cross-Source Reasoning (`TEST-01-CROSS-SOURCE`)**:
   - *Query*: "Why did payment failures begin after the deployment?"
   - *Outcome*: Synthesize deployment log (10:02 AM), log spike (10:07 AM), release notes v2.4.0 (field change), and transcript discussion into a single root cause with citations.
2. **Test 2 — Exact Technical Lookup (`TEST-02-EXACT-LOOKUP`)**:
   - *Query*: "Find every occurrence of error code PAY-401 and compare the affected versions."
   - *Outcome*: Exact keyword filtering + version comparison without semantic hallucination.
3. **Test 3 — Conflicting Evidence (`TEST-03-CONFLICTING-EVIDENCE`)**:
   - *Query*: "The runbook says the service uses Redis, but the latest architecture diagram shows an in-memory cache. Which is correct?"
   - *Outcome*: Disclose conflict, inspect version timestamps, and flag ambiguity rather than guessing.
4. **Test 4 — Evidence-Based Abstention (`TEST-04-UNANSWERABLE`)**:
   - *Query*: "Which engineer secretly caused the outage, and what exact line of code did they change?"
   - *Outcome*: Gracefully abstain; explain that evidence does not support attribution and specify missing artifacts needed.

---

## 🚀 Quickstart Guide

### 1. Backend Setup
```bash
# Navigate to backend and activate virtual environment
cd backend
.\.venv\Scripts\activate   # Windows (or source .venv/bin/activate on Unix)

# Copy environment template and fill in MongoDB & OpenAI credentials
copy .env.example .env

# Run FastAPI backend
uvicorn app.main:app --reload --port 8000
```
Backend API will be running at: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm run dev
```
Frontend UI will be running at: `http://localhost:3000`

---

## 🔗 Connecting Your GitHub Repository

When you share your remote GitHub repository URL, run:
```bash
git remote add origin <YOUR_GITHUB_REPO_URL>
git branch -M main
git push -u origin main
```
