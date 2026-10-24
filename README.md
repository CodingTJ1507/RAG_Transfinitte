# TraceIQ

TraceIQ is an evidence-grounded engineering incident investigation application. It
indexes a focused, fictional payment-service incident collection and answers questions
with source-backed findings, exact locators, timelines, conflict handling, and explicit
abstention.

The implementation follows the supplied
[`MongoDB_RAG_Architecture_Reference.pdf`](./MongoDB_RAG_Architecture_Reference.pdf).

## Architecture

The implementation follows the MongoDB RAG architecture reference's modular layers:

| Layer | Location | Responsibility |
|---|---|---|
| Ingestion | `backend/app/ingestion/` | Parse PDF, DOCX, Markdown, HTML, VTT, text, JSON, CSV, and image metadata while retaining structural locators; recursively split oversized evidence units. |
| Services | `backend/app/services/` | Gemini text embeddings, Gemini grounded generation and independent citation verification, and idempotent dataset ingestion. |
| Core | `backend/app/core/` | MongoDB Atlas connections, operational indexes, collection access, and vector/Atlas Search readiness. |
| Retrieval | `backend/app/retrieval/` | Filtered Atlas ANN vector search, Atlas Search BM25, exact identifier lookup, and Reciprocal Rank Fusion (RRF). |
| Reasoning and API | `backend/app/reasoning/`, `backend/app/api/` | Query normalization/decomposition, evidence registry, grounded claims, post-generation verification, abstention, evaluation, and FastAPI endpoints. |

### Query and ingestion flow

1. Ingestion reads `backend/synthetic_data/metadata/source_manifest.json`, validates
   source paths and hashes, parses content into evidence units, and preserves page,
   heading, cue, row, event, log, and record locators.
2. Structured evidence units remain intact when possible. Oversized units use
   LangChain's recursive character splitter with a tiktoken-based 500-token target and
   60-token overlap. Each chunk has a deterministic ID and SHA-256 content hash.
3. Gemini generates `RETRIEVAL_DOCUMENT` embeddings. MongoDB upserts chunks by
deterministic chunk ID (derived from source version, locator, position, and content
hash), preserving repeated passages at distinct source locations. It stores text,
content hashes, embeddings, timestamps, identifiers, source metadata, and locators
together.
4. Investigation normalizes common abbreviations and decomposes multi-part queries.
   For each query it independently retrieves from Atlas Vector Search, Atlas Search
   BM25, and indexed exact identifier fields, then combines the ranked lists with RRF
   (`k=60`). Supported incident, source-type, version, owner, and time filters are
   applied at retrieval time.
5. A structured evidence registry is passed to Gemini as untrusted evidence. The
   generated answer claims cite only retrieved chunk IDs. A separate Gemini verifier
   checks each cited claim against the cited text; unsupported or contradicted claims
   are not presented as verified answers. Missing or unverifiable evidence causes
   structured abstention.
6. The frontend calls FastAPI only; MongoDB credentials and the Gemini key stay on the
   backend.

MongoDB stores original source metadata, chunks, embeddings, stable source/chunk IDs,
and ingestion run records in the configured database. Atlas Vector Search uses ANN
cosine search; Atlas Search provides lexical BM25 retrieval; application-level RRF is
used as a compatible fallback instead of requiring a particular Atlas `$rankFusion`
deployment.

## Requirements and configuration

- Python 3.10 or newer.
- Node.js compatible with the locked Next.js 16 release.
- MongoDB Atlas with Vector Search and Atlas Search enabled.
- A Google Gemini API key with access to the configured generation and embedding
  models.

### Backend

From the repository root in PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend\.env` with real credentials. Keep `.env` private and untracked.

| Variable | Purpose |
|---|---|
| `MONGODB_URI` | Atlas connection string |
| `MONGODB_DATABASE` | Database name |
| `MONGODB_SOURCE_COLLECTION` | Source metadata collection |
| `MONGODB_CHUNK_COLLECTION` | Chunk and embedding collection |
| `MONGODB_VECTOR_INDEX` | Atlas Vector Search index name |
| `MONGODB_SEARCH_INDEX` | Atlas Search BM25 index name |
| `GEMINI_API_KEY` | Gemini key for embeddings, answer generation, and citation verification |
| `LLM_MODEL` | Gemini generation model; default `gemini-2.5-flash` |
| `EMBEDDING_MODEL` | Gemini embedding model; default `gemini-embedding-001` |
| `EMBEDDING_DIMENSIONS` | Gemini vector size and Atlas index dimension; default 768 |
| `EMBEDDING_BATCH_SIZE` | Maximum texts per Gemini embedding request |
| `DATASET_DIR` | Optional dataset root; defaults to `backend/synthetic_data` |
| `CHUNK_SIZE`, `CHUNK_OVERLAP` | Token-based recursive chunking settings |
| `RETRIEVAL_CANDIDATE_LIMIT`, `FINAL_EVIDENCE_LIMIT` | Candidate and final evidence limits |
| `MAX_SOURCE_FILE_BYTES` | Maximum source file size accepted by ingestion |
| `REQUEST_TIMEOUT_SECONDS` | Database/provider request timeout |
| `SEARCH_INDEX_TIMEOUT_SECONDS` | How long to wait for Atlas search indexes to become queryable; default 90 (keep it under the UI's 120 s request timeout) |
| `CORS_ORIGINS` | Comma-separated frontend origins |

The vector dimensions are pinned with the embedding model. Changing model or
dimensions requires recreating the Atlas vector index and re-embedding all chunks;
vectors from different models or dimensions must not be mixed in the active index.

### Atlas indexes

Create both the Vector Search and BM25 Atlas Search indexes on the chunks collection:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m scripts.manage_vector_index --create
```

Run it as a module (`-m`) from `backend`, so Python can find the `app` package. It waits
up to `SEARCH_INDEX_TIMEOUT_SECONDS` (default 90) for both indexes to become queryable;
if it times out, run it again.

The vector and Atlas Search definitions are documented in
[`backend/scripts/vector_search_index.json`](backend/scripts/vector_search_index.json)
and [`backend/scripts/atlas_search_index.json`](backend/scripts/atlas_search_index.json).
Index creation is repeat-safe by configured index name. Check `/ready` or rerun the
script without `--create` to inspect index readiness and vector dimensions.

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
`GET /health` reports process liveness. `GET /ready` reports MongoDB, both Atlas
indexes, Gemini configuration, and dataset readiness.

Use **Import / refresh dataset** in the UI or call the APIs:

```powershell
Invoke-RestMethod -Method Post http://localhost:8000/api/ingest/batch
Invoke-RestMethod -Method Post http://localhost:8000/api/investigate/ `
  -ContentType 'application/json' `
  -Body '{"query":"Why did some payments fail after the 2.4.0 deployment?","incident_id":"INC-2026-1042"}'
Invoke-RestMethod 'http://localhost:8000/api/ingest/sources?incident_id=INC-2026-1042'
```

## Evaluation

The local labeled benchmark includes exact-identifier, semantic, multi-source,
conflicting-source, and unanswerable questions. It reports Hit Rate@k, Recall@k,
Precision@k, MRR, and nDCG@k for retrieval. Use:

```powershell
Invoke-RestMethod 'http://localhost:8000/api/eval/benchmark?top_k=10'
```

To also call Gemini for generation, citation verification, and abstention checks:

```powershell
Invoke-RestMethod 'http://localhost:8000/api/eval/benchmark?top_k=10&generate_answers=true'
```

Answer evaluation adds citation validity, abstention match, and verified-claim
faithfulness. This is a project benchmark, not a substitute for comparing RAGAS,
DeepEval, or production feedback/tracing tools on a larger human-labeled set.

## Explain vector search

With the backend database available and the demo evidence imported, run from
`backend`:

```powershell
python -m scripts.explain_vector_search "Why did payment requests start failing?" --top-k 10 --incident INC-2026-1042 --num-candidates 150 300 600
```

The script embeds the question once, saves each Atlas `executionStats` response
under `backend/eval_results/`, and prints wall time, result count, chunk IDs,
and the fraction of the largest candidate count's results also returned by
each smaller candidate count. Compare the measurements before changing the
candidate-count default.

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

Backend tests and dataset validation use local deterministic fixtures and do not make
live Gemini or MongoDB requests. The benchmark endpoint requires a populated Atlas
database and configured Atlas indexes.

## API

- `POST /api/ingest/batch`: idempotently import the built-in dataset; accepts an optional `incident_id`.
- `POST /api/ingest/upload`: validate, parse, embed, and index one supported evidence file.
- `GET /api/ingest/sources?incident_id=...`: list ingested sources.
- `GET /api/ingest/runs/{run_id}`: fetch an ingestion summary.
- `POST /api/investigate/`: investigate with optional incident, source-type, time,
  version, and owner filters.
- `GET /api/eval/benchmark`: run retrieval evaluation; optional
  `generate_answers=true` adds Gemini-backed verification.
- `GET /health`, `GET /ready`: liveness and dependency readiness.

## Limitations and architectural choices

- **Image understanding:** image bytes are validated and indexed by manifest
  descriptions only; OCR/visual chart understanding is not enabled.
- **Durable orchestration:** ingestion is repeat-safe and can be retried via its API.
  Temporal is not introduced for this small, local evidence pack; add a durable
  workflow engine if ingestion becomes long-running or event-driven.
- **Reranking:** no cross-encoder or LLM reranker is enabled yet. Compare retrieval
  metrics first and only add latency/cost if evaluation shows a measurable gain.
- **Citation verification:** Gemini independently evaluates whether the cited text
  entails each generated claim. This is a model-based verifier, not a formal proof or
  a calibrated NLI classifier; measure false acceptance/rejection against human labels.
- **Evaluation frameworks:** current metrics use the repository's fixed golden set.
  Integrate RAGAS/DeepEval and production tracing/feedback after selecting a representative
  human-annotated evaluation set.
- **Live services:** Atlas/Gemini requests have not been exercised in this environment.
  Configure credentials, create matching Atlas indexes, ingest the evidence pack, and
  run the benchmark before relying on production behavior.
