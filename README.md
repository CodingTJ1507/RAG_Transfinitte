# TraceIQ

TraceIQ is an evidence-grounded engineering incident investigation application. It
indexes a focused, fictional payment-service incident collection and answers questions
with source-backed findings, locators, timelines, conflicts, and explicit abstention.

## Current implementation

- Manifest-driven parsing for PDF, HTML, VTT, text/Markdown, JSON, CSV, and image
  metadata.
- Deterministic chunks that preserve page, cue, row, event, log, and record locators.
- MongoDB source/chunk persistence, OpenAI embeddings, Atlas Vector Search, exact
  identifier matching, MongoDB text search, and Reciprocal Rank Fusion.
- FastAPI routes for dataset ingestion, source listing, investigation, readiness, and
  retrieval evaluation.
- Next.js investigation UI for importing the collection, applying filters, asking
  questions, inspecting citations, and viewing abstention/conflict/timeline output.
- Dataset-based evaluation files are authoritative. The legacy test fixture was
  corrected to point to incident `INC-2026-1042`; the evaluation fixtures live under
  `backend/synthetic_data/evaluation/`.

Image content is **not OCR analyzed**. Images are validated and indexed using manifest
metadata only; citations disclose this limitation. Configure OCR/vision before relying
on text or chart interpretation from images.

## Architecture and data flow

1. `POST /api/ingest/batch` discovers sources from the dataset's
   `metadata/source_manifest.json`; the webpage index file is not ingested as a source.
2. Parsers extract text or structured records and preserve their source locators.
3. Deterministic chunk IDs plus SHA-256 source hashes support safe repeat ingestion.
4. OpenAI creates real embeddings; MongoDB stores source metadata and chunks.
5. Atlas Vector Search and MongoDB lexical/exact identifier retrieval run over the
   same filters. Reciprocal Rank Fusion combines results.
6. Evidence is deduplicated and passed to the configured LLM as untrusted data.
7. Generated chunk references are validated against the retrieved evidence. Timeline
   items and UI citations are constructed from retrieved records rather than invented.
8. The frontend calls FastAPI only; no database credentials or LLM keys go to the browser.

MongoDB collections:

- `sources`: one manifest source per `source_id`.
- `chunks`: location-preserving text/record chunks and embeddings.
- `ingestion_runs`: ingestion summaries.

## Prerequisites

- Python 3.10 or newer (the current environment was Python 3.13).
- Node.js compatible with the locked Next.js 16 release (the current environment was
  Node 24).
- MongoDB Atlas cluster with Vector Search enabled for semantic retrieval.
- OpenAI API key for embeddings and answer generation.
- Network access from the backend to MongoDB Atlas and OpenAI.

Unit tests and dataset validation do not require live MongoDB or LLM credentials.
Live ingestion and investigations do.

## Setup

### Backend

In PowerShell from the repository root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend\.env` with real values. Do not commit this file.

| Variable | Purpose |
|---|---|
| `MONGODB_URI` | Atlas connection string |
| `MONGODB_DATABASE` | Database name |
| `MONGODB_SOURCE_COLLECTION` | Source metadata collection |
| `MONGODB_CHUNK_COLLECTION` | Chunk and embedding collection |
| `MONGODB_VECTOR_INDEX` | Atlas Vector Search index name |
| `OPENAI_API_KEY` | OpenAI API key; required for live embeddings and answers |
| `LLM_MODEL` | Chat model name |
| `EMBEDDING_MODEL` | Embedding model used for both chunks and queries |
| `EMBEDDING_DIMENSIONS` | Must match the embedding model and Atlas index (1536 by default) |
| `EMBEDDING_BATCH_SIZE` | Maximum texts per embedding request |
| `DATASET_DIR` | Optional dataset root; defaults to `backend/synthetic_data` |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | Deterministic word-based chunking limits |
| `RETRIEVAL_CANDIDATE_LIMIT`, `FINAL_EVIDENCE_LIMIT` | Retrieval sizes |
| `MAX_SOURCE_FILE_BYTES` | Maximum source file size accepted by dataset parsing |
| `REQUEST_TIMEOUT_SECONDS` | MongoDB and provider timeout |
| `CORS_ORIGINS` | Comma-separated frontend origins |

### Atlas vector index

The ingestion route creates ordinary MongoDB indexes. Atlas Vector Search also needs
the vector index configured on the `chunks` collection. Create and verify it with:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python scripts/manage_vector_index.py --create
```

The exact index definition is in
[`backend/scripts/vector_search_index.json`](backend/scripts/vector_search_index.json).
If `EMBEDDING_DIMENSIONS` changes, the Atlas vector index definition must use that same
dimension and the existing chunk vectors must be re-embedded before switching models.
The script requires a reachable Atlas cluster and appropriate database privileges.

### Frontend

```powershell
cd frontend
npm ci
```

Optional `frontend/.env.local`:

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Run the application

Start FastAPI in one terminal:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Start Next.js in another:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:3000`; API docs are at `http://localhost:8000/docs`.
`GET /health` checks process liveness. `GET /ready` separately reports MongoDB,
vector-index, LLM configuration, and dataset readiness.

In the UI, select **Import / refresh dataset**, then submit a question. Equivalent
requests:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/ingest/batch
Invoke-RestMethod -Method Post http://localhost:8000/api/investigate/ `
  -ContentType 'application/json' `
  -Body '{"query":"Why did some payments fail after the 2.4.0 deployment?","incident_id":"INC-2026-1042"}'
Invoke-RestMethod 'http://localhost:8000/api/ingest/sources?incident_id=INC-2026-1042'
```

The evaluation endpoint retrieves actual evidence and reports Recall@k, MRR, hit
rate, and pass rate:

```powershell
Invoke-RestMethod 'http://localhost:8000/api/eval/benchmark?top_k=10'
```

Add `&generate_answers=true` to also run LLM generation and check abstention and
retrieved-chunk citation references. This makes provider calls for the selected
questions and is not a deterministic answer-quality judge.

## Tests and dataset validation

From the repository root:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m unittest discover -s tests -v
python scripts\validate_synthetic_data.py synthetic_data
```

Frontend checks:

```powershell
cd frontend
npm run lint
npm run build
```

Core backend tests use local deterministic data and do not contact MongoDB or OpenAI.
Dataset validation checks source files and evaluation consistency; it does not measure
live retrieval or generated-answer quality.

## API outline

- `POST /api/ingest/batch`: idempotently import the built-in dataset.
- `GET /api/ingest/sources?incident_id=...`: list processed sources.
- `GET /api/ingest/runs/{run_id}`: fetch an ingestion summary.
- `POST /api/investigate/`: query with optional incident, source-type, time, and version filters.
- `GET /api/eval/benchmark`: run retrieval metrics against dataset evaluation questions.
- `GET /health`, `GET /ready`: liveness and dependency readiness.

## Known limitations and troubleshooting

- **Image OCR:** not implemented. Images are searchable by manifest description only.
- **MongoDB Atlas Vector Search:** a live Atlas URI, compatible index and dimensions
  are required; local MongoDB alone cannot provide the Atlas vector stage used here.
- **LLM/embedding calls:** require a valid `OPENAI_API_KEY`, provider access, and model
  availability. Missing provider configuration causes explicit service errors.
- **Citation semantic support:** source/chunk identity is validated against retrieved
  evidence, but semantic entailment is not independently verified by a second judge.
- **Text chunking:** uses deterministic word-based boundaries, not a tokenizer-aware
  splitter. Logical source records/cues/rows remain separate units.
- **Evaluation:** retrieval metrics are executable; generated-answer evaluation checks
  abstention and citation references but does not claim answer correctness metrics.
- **Dataset regeneration:** copied generation scripts expect their original nested
  dataset layout. They are included as source reference and are not configured to
  regenerate the reorganized `backend/synthetic_data` tree.
- **Readiness:** database or Atlas index failure is reported separately from a running
  API process. Check URI/network access, Atlas index name/type/dimensions, OpenAI key,
  CORS origin, and frontend API URL when a stage fails.
