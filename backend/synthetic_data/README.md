# TraceIQ Synthetic Incident Dataset

This folder contains the requested dataset subset for incident `INC-2026-1042`.

## Evidence folders

| Source folder | Destination folder | Contents |
|---|---|---|
| `raw/documents/` | `documents/` | PDFs and other incident reference documents |
| `raw/images/` | `images/` | PNG dashboards, screenshots, and diagrams |
| `raw/structured/` | `structured_records/` | JSON logs and records, plus CSV metrics |
| `raw/transcripts/` | `transcripts/` | WebVTT recordings and a handover note |
| `raw/webpages/` | `webpages/` | HTML pages and their `sources.json` index |

The supporting `metadata/`, `evaluation/`, and `scripts/` folders are copied from
the source dataset. The original `traceiq_dataset` files are left unchanged. All
five document files are included, and the copied source manifest records their
destination paths, formats, and SHA-256 hashes.

The copied generation and validation scripts expect the source dataset's original
directory layout. They are included for reference and are not configured to generate
or validate this reorganized subset.
