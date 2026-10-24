#!/usr/bin/env python3
"""Validate the TraceIQ synthetic incident dataset (INC-2026-1042).

Usage:  python scripts/validate_dataset.py [path/to/dataset]
Exit code 0 = all critical checks passed, 1 = at least one critical check failed.
Uses only the Python standard library. If pypdf or pdfplumber is installed, PDF page
locators are also checked; otherwise that part is reported as SKIP.
"""
import csv, json, re, sys, zipfile
from datetime import datetime
from pathlib import Path

DS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "dataset"
RAW = DS / "raw"
SERVICES = {"api-gateway", "order-service", "payment-service", "inventory-service", "postgres", "redis"}
PAY_VERSIONS = {"2.3.1", "2.4.0"}
ERROR_CODES = {"PAY-400": 400, "PAY-401": 422, "PAY-402": 402, "PAY-409": 409, "PAY-504": 504}
TYPES = {"document", "webpage", "image", "transcript", "structured"}
results = []

def check(name, ok, detail="", critical=True):
    tag = "PASS" if ok else ("FAIL" if critical else "WARN")
    results.append((tag, name)); print(f"[{tag}] {name}" + (f" -- {detail}" if detail else ""))
    return ok

def load(p): return json.loads((DS / p).read_text())

# 1, 2, 10, 11 -- manifest ------------------------------------------------
manifest = load("metadata/source_manifest.json")["sources"]
ids = [s["source_id"] for s in manifest]
by_id = {s["source_id"]: s for s in manifest}
missing = [s["file_path"] for s in manifest if not (DS / s["file_path"]).is_file()]
check("1. Every manifest file exists", not missing, ", ".join(missing))
dups = sorted({i for i in ids if ids.count(i) > 1})
check("2. Source IDs are unique", not dups, ", ".join(dups))
not_raw = [s["source_id"] for s in manifest if not s["file_path"].startswith("raw/")]
on_disk = {p.relative_to(DS).as_posix() for p in RAW.rglob("*") if p.is_file()}
unlisted = sorted(on_disk - {s["file_path"] for s in manifest} - {"raw/webpages/sources.json"})
check("10. Every source maps to a file in raw/ and every raw file is in the manifest",
      not not_raw and not unlisted, f"outside raw: {not_raw}; unlisted: {unlisted}")
types = {s["source_type"] for s in manifest}
check("11. All five source types present", TYPES <= types, f"found {sorted(types)}")
leaks = [p for p in on_disk if any(k in p for k in ("answer_key", "incident_spec", "claims_ledger", "questions"))]
check("Answer key is not inside raw/", not leaks, ", ".join(leaks))

# 3 -- JSON parses ---------------------------------------------------------
bad_json = []
for p in list(DS.rglob("*.json")):
    try: json.loads(p.read_text())
    except Exception as e: bad_json.append(f"{p.name}: {e}")
check("3. All JSON files parse", not bad_json, "; ".join(bad_json))

logs = load("raw/structured/application_logs.json")["records"]
events = load("raw/structured/deployment_events.json")["events"]
reqs = load("raw/structured/payment_requests.json")["records"]
deps = load("raw/structured/service_dependencies.json")

# 4 -- CSV -----------------------------------------------------------------
COLS = ["row_id", "timestamp", "service", "version", "metric_scope", "request_count", "error_count",
        "error_rate_pct", "latency_p50_ms", "latency_p95_ms", "latency_p99_ms"]
rows, csv_err = [], []
with open(RAW / "structured/metrics.csv", newline="") as f:
    r = csv.DictReader(f)
    if r.fieldnames != COLS: csv_err.append(f"columns {r.fieldnames}")
    for row in r:
        rows.append(row)
        try:
            req, err = int(row["request_count"]), int(row["error_count"])
            if not (0 <= err <= req): csv_err.append(f"{row['row_id']} error_count > request_count")
            if abs(float(row["error_rate_pct"]) - round(100 * err / req, 1)) > 0.11: csv_err.append(f"{row['row_id']} bad error_rate_pct")
            if not int(row["latency_p50_ms"]) <= int(row["latency_p95_ms"]) <= int(row["latency_p99_ms"]): csv_err.append(f"{row['row_id']} percentiles out of order")
        except ValueError as e: csv_err.append(f"{row.get('row_id')}: {e}")
check("4. metrics.csv has expected columns and valid rows", not csv_err and len(rows) > 0, "; ".join(csv_err[:5]))

# 5 -- timestamps ----------------------------------------------------------
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{3})?Z$")
def parse(s): return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S")
bad_ts = []
def walk(o, where):
    if isinstance(o, dict):
        for k, v in o.items():
            if k in ("timestamp", "received_at", "published_at", "created_at", "recording_start") and v is not None:
                if not (isinstance(v, str) and ISO.match(v)): bad_ts.append(f"{where}:{k}={v}")
                else: parse(v)
            else: walk(v, where)
    elif isinstance(o, list):
        for x in o: walk(x, where)
for p in DS.rglob("*.json"): walk(json.loads(p.read_text()), p.name)
for row in rows:
    if not ISO.match(row["timestamp"]): bad_ts.append(f"metrics:{row['row_id']}")
check("5. Machine-readable timestamps are ISO 8601 UTC", not bad_ts, "; ".join(bad_ts[:5]))
order_ok = all(parse(a["timestamp"]) <= parse(b["timestamp"]) for seq in (logs, events) for a, b in zip(seq, seq[1:]))
check("5b. Logs and deployment events are in time order", order_ok)
ev = {e["event_type"]: parse(e["timestamp"]) for e in events}
first_401 = min(parse(l["timestamp"]) for l in logs if l["error_code"] == "PAY-401")
chrono = ev["deploy_started"] < ev["deploy_completed"] < first_401 < ev["alert_triggered"] < ev["incident_opened"] < ev["rollback_started"] < ev["rollback_completed"]
late_401 = [l["log_id"] for l in logs if l["error_code"] == "PAY-401" and parse(l["timestamp"]) > ev["rollback_completed"]]
check("5c. Incident chronology is possible (deploy < first PAY-401 < alert < incident < rollback)", chrono and not late_401, f"late PAY-401: {late_401}")

# 6 -- services and versions -----------------------------------------------
svc_found = {l["service"] for l in logs} | {e["service"] for e in events} | {r["service"] for r in rows} \
    | {s["name"] for s in deps["services"]} | {d[k] for d in deps["dependencies"] for k in ("upstream", "downstream")} \
    | {s for m in manifest for s in m["services"]}
ver_bad = [l["log_id"] for l in logs if l["service"] == "payment-service" and l["version"] not in PAY_VERSIONS]
ver_bad += [e["event_id"] for e in events if e["old_version"] not in PAY_VERSIONS or e["new_version"] not in PAY_VERSIONS]
ver_bad += [r["record_id"] for r in reqs if r["payment_service_version"] not in PAY_VERSIONS]
ver_bad += [r["row_id"] for r in rows if r["service"] == "payment-service" and r["version"] not in PAY_VERSIONS | {"mixed"}]
text_files = [p for p in RAW.rglob("*") if p.suffix in (".md", ".html", ".vtt", ".txt")]
for p in text_files:
    for v in re.findall(r"payment-service[ \w]{0,12}?(\d+\.\d+\.\d+)", p.read_text()):
        if v not in PAY_VERSIONS: ver_bad.append(f"{p.name}:{v}")
for p in text_files + [DS / "metadata/incident_spec.md"]:
    for v in re.findall(r"(\d+\.\d+\.\d+)\s*(?:->|→|to)\s*(\d+\.\d+\.\d+)", p.read_text()):
        if set(v) <= {"2.3.1", "2.4.0", "2.8.4", "3.0.1"} and set(v) not in ({"2.3.1", "2.4.0"}, {"2.8.4", "3.0.1"}): ver_bad.append(f"{p.name}:{v}")
names_text = " ".join(p.read_text() for p in text_files)
odd = sorted(set(re.findall(r"\b(payment[-_ ]svc|payments-service|order[-_]svc|paymentservice)\b", names_text, re.I)))
check("6. Service names and payment-service versions are consistent",
      svc_found <= SERVICES and not ver_bad and not odd, f"unknown services {sorted(svc_found - SERVICES)}; bad versions {ver_bad[:5]}; odd names {odd}")
dep_events = [e for e in events if e["event_type"] == "deploy_started"]
check("6b. Main deploy is 2.3.1 -> 2.4.0 in production",
      len(dep_events) == 1 and dep_events[0]["old_version"] == "2.3.1" and dep_events[0]["new_version"] == "2.4.0" and dep_events[0]["environment"] == "production")

# 6c -- dependency graph has no cycles
graph = {}
for d in deps["dependencies"]: graph.setdefault(d["upstream"], []).append(d["downstream"])
def cyclic(n, stack, seen):
    if n in stack: return True
    if n in seen: return False
    seen.add(n); stack.add(n)
    r = any(cyclic(m, stack, seen) for m in graph.get(n, [])); stack.discard(n); return r
check("6c. Service dependency graph has no cycles", not any(cyclic(n, set(), set()) for n in graph))

# 7 -- error codes ---------------------------------------------------------
code_bad = []
for p in list(RAW.rglob("*")):
    if p.is_file() and p.suffix in (".md", ".html", ".vtt", ".txt", ".json", ".csv"):
        code_bad += [f"{p.name}:{c}" for c in set(re.findall(r"PAY-\d{3}", p.read_text())) if c not in ERROR_CODES]
for rec in logs + reqs:
    c = rec.get("error_code")
    if c and rec.get("http_status") and ERROR_CODES.get(c) != rec["http_status"]:
        code_bad.append(f"{rec.get('log_id') or rec.get('record_id')}: {c} with HTTP {rec['http_status']}")
with zipfile.ZipFile(RAW / "documents/incident_initial_report.docx") as z: docx_xml = z.read("word/document.xml").decode()
code_bad += [f"docx:{c}" for c in set(re.findall(r"PAY-\d{3}", docx_xml)) if c not in ERROR_CODES]
check("7. Error codes are consistent (PAY-401 always HTTP 422)", not code_bad, "; ".join(code_bad[:5]))
check("7b. Incident ID is consistent", all(s["incident_id"] == "INC-2026-1042" for s in manifest)
      and not set(re.findall(r"INC-\d{4}-\d{4}", names_text + docx_xml)) - {"INC-2026-1042"})

# locator verification -----------------------------------------------------
pdf_text = {}
try:
    from pypdf import PdfReader
    def pages(path): return [p.extract_text() or "" for p in PdfReader(str(path)).pages]
except ImportError:
    try:
        import pdfplumber
        def pages(path):
            with pdfplumber.open(str(path)) as d: return [p.extract_text() or "" for p in d.pages]
    except ImportError:
        pages = None
log_ids = {l["log_id"] for l in logs}; evt_ids = {e["event_id"] for e in events}
req_ids = {r["record_id"] for r in reqs}; row_ids = {r["row_id"] for r in rows}
dep_ids = {d["dependency_id"] for d in deps["dependencies"]}
cues = {}
for sid in ("TRN-001", "TRN-002"):
    blocks = (DS / by_id[sid]["file_path"]).read_text().split("\n\n")
    if not blocks[0].startswith("WEBVTT"): cues[sid] = None; continue
    cues[sid] = {}
    for b in blocks:
        ln = b.strip().split("\n")
        if len(ln) >= 3 and "-->" in ln[1]:
            m = re.match(r"<v ([^>]+)>", ln[2]); cues[sid][ln[0]] = (ln[1].split(" --> ")[0], m.group(1) if m else None)
check("WebVTT files have valid header and cues", all(cues.values()))
manual, pdf_skipped = [], False

def verify(loc):
    sid, L = loc["source_id"], loc["locator"]
    if sid not in by_id: return f"unknown source {sid}"
    path = DS / by_id[sid]["file_path"]
    if "page" in L:
        global pdf_skipped
        if pages is None: pdf_skipped = True; return None
        pt = pdf_text.setdefault(sid, pages(path))
        if L["page"] > len(pt) or L["section"] not in pt[L["page"] - 1]: return f"{sid} p{L['page']} lacks '{L['section']}'"
    elif "html_id" in L:
        t = path.read_text()
        if f'id="{L["html_id"]}"' not in t or L["heading"] not in t: return f"{sid} lacks #{L['html_id']}"
    elif "heading" in L:
        t = docx_xml if path.suffix == ".docx" else path.read_text()
        if L["heading"] not in t: return f"{sid} lacks heading '{L['heading']}'"
    elif "cue_id" in L:
        c = cues[sid].get(L["cue_id"])
        if not c or c != (L["start"], L["speaker"]): return f"{sid} {L['cue_id']} mismatch"
    elif "section" in L:
        if L["section"] not in path.read_text(): return f"{sid} lacks section '{L['section']}'"
    elif "visible_text" in L:
        manual.append(f"{sid}: '{L['visible_text']}'"); return None
    else:
        (key, vals), = L.items()
        pool = {"log_id": log_ids, "event_id": evt_ids, "record_id": req_ids, "row_id": row_ids, "dependency_id": dep_ids}[key]
        bad = [v for v in vals if v not in pool]
        if bad: return f"{sid} missing {bad}"
    return None

# 9 -- claims --------------------------------------------------------------
claims = load("metadata/claims_ledger.json")["claims"]
cl_ids = {c["claim_id"] for c in claims}
bad = []
for c in claims:
    bad += [f"{c['claim_id']}: unknown {s}" for s in c["supporting_source_ids"] if s not in by_id]
    if set(c["supporting_source_ids"]) != {l["source_id"] for l in c["relevant_locations"]}: bad.append(f"{c['claim_id']}: ids/locations differ")
    bad += [f"{c['claim_id']}: {e}" for e in map(verify, c["relevant_locations"]) if e]
check("9. Every claim references existing sources and real locations", not bad, "; ".join(bad[:5]))
multi = sum(len(c["supporting_source_ids"]) > 1 for c in claims)
uncertain = sum(c["status"] in ("contradicted", "inferred", "unknown") for c in claims)
check("9b. Claims ledger size and mix (>=12 claims, >=5 multi-source, >=2 uncertain)",
      len(claims) >= 12 and multi >= 5 and uncertain >= 2, f"{len(claims)} claims, {multi} multi-source, {uncertain} uncertain")

# 8, 12 -- evaluation ------------------------------------------------------
qs = load("evaluation/questions.json")["questions"]
exp = {e["question_id"]: e for e in load("evaluation/expected_sources.json")["expected_sources"]}
key = {a["question_id"]: a for a in load("evaluation/answer_key.json")["answers"]}
bad8 = [f"{q['question_id']}:{s}" for q in qs for s in q["expected_source_ids"] if s not in by_id]
bad8 += [f"{q['question_id']}:{c}" for q in qs for c in q["expected_claim_ids"] if c not in cl_ids]
check("8. Every evaluation question references existing sources and claims", not bad8, "; ".join(bad8))
cats = {}
for q in qs: cats[q["category"]] = cats.get(q["category"], 0) + 1
want = {"single_source": 4, "cross_source": 6, "timeline": 3, "conflicting_evidence": 3, "unanswerable": 4}
check("8b. 20 questions with the required category split", len(qs) == 20 and cats == want, str(cats))
bad12 = []
ctype = {c["claim_id"]: c for c in claims}
for q in qs:
    qid = q["question_id"]; e = exp.get(qid)
    if not e or qid not in key: bad12.append(f"{qid}: missing expected_sources/answer_key"); continue
    covered = {l["source_id"] for l in e["supporting_locations"]}
    if set(q["expected_source_ids"]) - covered: bad12.append(f"{qid}: no location for {sorted(set(q['expected_source_ids']) - covered)}")
    bad12 += [f"{qid}: {x}" for x in map(verify, e["supporting_locations"]) if x]
    if q["category"] == "cross_source" and len({by_id[s]['source_type'] for s in q["expected_source_ids"]}) < 2:
        bad12.append(f"{qid}: cross-source question uses one source type")
    if q["abstention_required"] != (q["category"] == "unanswerable"): bad12.append(f"{qid}: abstention flag mismatch")
    if q["abstention_required"] and any(ctype[c]["status"] != "unknown" for c in q["expected_claim_ids"]):
        bad12.append(f"{qid}: unanswerable question linked to a non-unknown claim")
    if not q["abstention_required"] and not q["expected_claim_ids"]: bad12.append(f"{qid}: answerable question has no claims")
three = sum(len({by_id[s]["source_type"] for s in q["expected_source_ids"]}) >= 3 for q in qs)
check("12. Expected source locations exist and support each answer", not bad12 and three >= 2,
      "; ".join(bad12[:5]) + f" | questions using >=3 source types: {three}")

# images and binary files --------------------------------------------------
img_bad = [s["file_path"] for s in manifest if s["format"] == "png" and (DS / s["file_path"]).read_bytes()[:8] != b"\x89PNG\r\n\x1a\n"]
img_bad += [s["file_path"] for s in manifest if s["format"] == "pdf" and (DS / s["file_path"]).read_bytes()[:5] != b"%PDF-"]
check("Binary files have valid PNG / PDF signatures and DOCX opens", not img_bad and "<w:body>" in docx_xml, ", ".join(img_bad))

if pdf_skipped: print("[SKIP] PDF page locators not checked (install pypdf or pdfplumber to enable)")
print(f"[INFO] {len(set(manual))} image locators need visual review (cannot be automated without OCR):")
for m in sorted(set(manual)): print("       -", m)
fails = sum(t == "FAIL" for t, _ in results)
print(f"\nSUMMARY: {len(results) - fails} passed, {fails} failed")
sys.exit(1 if fails else 0)
