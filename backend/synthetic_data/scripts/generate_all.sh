#!/usr/bin/env bash
# Rebuild every artifact from scratch, then validate. Run from the project root.
set -euo pipefail
cd "$(dirname "$0")/generators"
python3 gen_structured.py      # step 3: records first (they fix the facts)
python3 gen_documents.py       # step 4: PDFs, Markdown, HTML, sources.json
node gen_report_docx.js        # step 4: DOCX (needs: npm install docx)
python3 gen_transcripts.py     # step 5
python3 gen_images.py          # step 6
python3 gen_metadata.py        # steps 7-8: manifest, claims, evaluation
cd ../.. && python3 scripts/validate_dataset.py
