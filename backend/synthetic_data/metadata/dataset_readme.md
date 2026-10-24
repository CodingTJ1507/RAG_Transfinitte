# TraceIQ Synthetic Incident Dataset — INC-2026-1042

**Everything here is fictional.** ShopSphere, every person, every website (`*.example`) and every number
are made up for learning. No real payment data, card numbers, credentials or personal data are included.

## What it is

One small incident for practising RAG: payment requests to the fictional ShopSphere platform start failing
after `payment-service` is upgraded from 2.3.1 to 2.4.0 on 2026-10-23 (UTC). The evidence is spread over
20 files of five types. No single file gives the full answer — you have to connect them.

## Folders

| Folder | Ingest it? | Contents |
|---|---|---|
| `raw/documents/` | YES | 3 PDFs, 1 Markdown, 1 DOCX (DOC-001 … DOC-005) |
| `raw/webpages/` | YES | 3 HTML pages (WEB-001 … WEB-003). `sources.json` is an index of these pages, not extra evidence |
| `raw/images/` | YES | 4 PNGs (IMG-001 … IMG-004) |
| `raw/transcripts/` | YES | 2 WebVTT + 1 text note (TRN-001 … TRN-003) |
| `raw/structured/` | YES | 4 JSON + 1 CSV (REC-001 … REC-005) |
| `metadata/` | **NO** | `incident_spec.md` (the answer), `source_manifest.json`, `claims_ledger.json`, this README |
| `evaluation/` | **NO** | `questions.json`, `expected_sources.json`, `answer_key.json` |

Only ingest `raw/`. `metadata/` and `evaluation/` contain the answers.

## How to cite inside each file type

| Type | Locator used in claims and answers |
|---|---|
| PDF | page number + numbered section heading (e.g. page 2, "4. Deprecated Fields") |
| Markdown / DOCX | heading text |
| HTML | element `id` + heading text |
| WebVTT | cue id (`cue-005`), start offset, speaker. Real time = `recording_start` in the NOTE block + offset |
| Text note | section label (`VERIFIED`, `NOT VERIFIED / STILL OPEN`, …) |
| JSON | `log_id`, `event_id`, `record_id`, `dependency_id` |
| CSV | `row_id` (one row per service per 5-minute bucket; bucket timestamp = bucket start) |
| PNG | visible label text |

## Notes for users

- `metrics.csv` has two scopes. `payment_attempts` counts every call to payment-service (retries included).
  `orders_payment_outcome` counts orders. That is why payment-service shows ~93% errors while ~78% of orders fail.
- The initial report (DOC-005) was written early and contains a wrong guess. That is on purpose.
- WEB-002 and WEB-003 are general background, not incident evidence.

## Regenerate

Needs Python 3.10+, `reportlab`, `matplotlib`, `Pillow`, and Node.js with the `docx` package.

```bash
pip install reportlab matplotlib pillow pypdf
npm install docx
./scripts/generate_all.sh
```

Generation is deterministic (fixed random seed), so you get the same data each time.
File hashes for PDFs/PNGs can differ slightly between library versions.

## Validate

```bash
python scripts/validate_dataset.py          # or: python scripts/validate_dataset.py path/to/dataset
```

Uses only the standard library. If `pypdf` or `pdfplumber` is installed it also checks PDF page numbers.
Exit code 0 = pass, 1 = fail.

**Not automated:** image content. The script checks that PNGs are valid files, but someone must look at the
images to confirm the labels listed under `[INFO]` are visible and readable.
