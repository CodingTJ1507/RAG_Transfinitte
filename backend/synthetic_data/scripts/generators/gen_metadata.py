"""Generate source_manifest.json, claims_ledger.json and evaluation files (synthetic)."""
import hashlib, json
from pathlib import Path

DS = Path(__file__).resolve().parents[2] / "dataset"
INC = "INC-2026-1042"

def dump(p, o):
    (DS / p).write_text(json.dumps(o, indent=2, ensure_ascii=False) + "\n")

# ---------------- source manifest ----------------
S = [
 ("DOC-001", "ShopSphere Architecture Overview", "document", "pdf", "raw/documents/architecture_overview.pdf", "2026-09-02T09:00:00Z", "1.3",
  ["api-gateway", "order-service", "payment-service", "inventory-service", "postgres", "redis"], ["architecture", "retries", "payment-flow"],
  "Services, checkout payment flow, and order-service retry policy."),
 ("DOC-002", "Payment API Specification v2.0", "document", "pdf", "raw/documents/payment_api_specification.pdf", "2026-08-14T09:00:00Z", "2.0",
  ["payment-service", "order-service"], ["api", "schema", "error-codes", "deprecation"],
  "Expected payment request fields, deprecated card_token alias, and error code table."),
 ("DOC-003", "Payment Service Deployment Runbook", "document", "pdf", "raw/documents/deployment_runbook.pdf", "2026-07-30T09:00:00Z", "3.1",
  ["payment-service"], ["runbook", "diagnostics", "rollback"], "Pre-deploy checklist, safe diagnostic checks and rollback considerations."),
 ("DOC-004", "payment-service 2.4.0 Release Notes", "document", "md", "raw/documents/release_notes_2_4_0.md", "2026-10-21T09:00:00Z", "2.4.0",
  ["payment-service"], ["release-notes", "dependencies"], "Changes in payment-service 2.4.0, including the schemaguard upgrade."),
 ("DOC-005", "Initial Incident Report INC-2026-1042", "document", "docx", "raw/documents/incident_initial_report.docx", "2026-10-23T10:18:00Z", "1",
  ["payment-service", "order-service"], ["incident", "initial-report", "hypothesis"], "First responder report written at 10:18 UTC. Contains an early, unverified hypothesis."),
 ("WEB-001", "schemaguard 3.0 Release Notes", "webpage", "html", "raw/webpages/dependency_release_notes.html", "2026-09-15T00:00:00Z", "3.0.1",
  [], ["dependency", "library", "breaking-changes"], "Fictional library release notes: alias resolution became opt-in in 3.0."),
 ("WEB-002", "Troubleshooting Payment Request Validation Errors", "webpage", "html", "raw/webpages/payment_validation_troubleshooting.html", "2026-05-03T00:00:00Z", "1.0",
  [], ["troubleshooting", "validation", "background"], "General background article. Not specific to ShopSphere."),
 ("WEB-003", "HTTP Status Codes: 4xx Reference", "webpage", "html", "raw/webpages/http_error_reference.html", "2025-11-20T00:00:00Z", "1.0",
  [], ["http", "status-codes", "background"], "General reference on 401 vs 422 and application error codes."),
 ("IMG-001", "Payments Monitoring Dashboard", "image", "png", "raw/images/monitoring_dashboard.png", "2026-10-23T12:00:00Z", "1",
  ["payment-service", "order-service"], ["metrics", "dashboard", "latency", "error-rate"], "Failure rate and p95 latency, 09:30-11:55 UTC, with deploy and rollback markers."),
 ("IMG-002", "Payment Error Screenshot", "image", "png", "raw/images/payment_error_screenshot.png", "2026-10-23T10:11:47Z", "1",
  ["order-service", "payment-service"], ["error", "screenshot", "PAY-401"], "order-service debug console showing a 422 PAY-401 response for req-1107."),
 ("IMG-003", "Service Architecture Diagram", "image", "png", "raw/images/service_architecture_diagram.png", "2026-10-23T12:00:00Z", "1",
  ["api-gateway", "order-service", "payment-service", "inventory-service", "postgres", "redis"], ["architecture", "dependencies"], "Boxes and arrows for the six core components."),
 ("IMG-004", "Deployment Timeline", "image", "png", "raw/images/deployment_timeline.png", "2026-10-23T12:00:00Z", "1",
  ["payment-service"], ["timeline", "deployment", "rollback"], "Timeline of deploy, first error, alert, incident, rollback."),
 ("TRN-001", "Deployment Go/No-Go Meeting", "transcript", "vtt", "raw/transcripts/deployment_meeting.vtt", "2026-10-23T09:30:00Z", "1",
  ["payment-service", "order-service"], ["meeting", "pre-deploy"], "Go/no-go meeting for 2.4.0 (starts 09:30 UTC)."),
 ("TRN-002", "Incident Discussion Call", "transcript", "vtt", "raw/transcripts/incident_discussion.vtt", "2026-10-23T10:20:00Z", "1",
  ["payment-service", "order-service", "redis", "postgres"], ["incident", "hypotheses"], "Incident call with competing hypotheses (starts 10:20 UTC)."),
 ("TRN-003", "Engineering Handover Note", "transcript", "txt", "raw/transcripts/engineering_handover.txt", "2026-10-23T12:00:00Z", "1",
  ["payment-service", "order-service"], ["handover", "status", "open-questions"], "Day-to-evening on-call handover: verified facts and open items."),
 ("REC-001", "Application Logs", "structured", "json", "raw/structured/application_logs.json", "2026-10-23T12:00:00Z", "1",
  ["api-gateway", "order-service", "payment-service", "redis"], ["logs", "errors", "traces"], "30 log records, 09:41-11:21 UTC, keyed by log_id."),
 ("REC-002", "Service Metrics", "structured", "csv", "raw/structured/metrics.csv", "2026-10-23T12:00:00Z", "1",
  ["payment-service", "order-service"], ["metrics", "latency", "error-rate"], "5-minute buckets 09:30-11:55 UTC, keyed by row_id."),
 ("REC-003", "Deployment Events", "structured", "json", "raw/structured/deployment_events.json", "2026-10-23T12:00:00Z", "1",
  ["payment-service"], ["deployment", "rollback", "alerts"], "Deploy, alert, incident and rollback events, keyed by event_id."),
 ("REC-004", "Payment Request Records", "structured", "json", "raw/structured/payment_requests.json", "2026-10-23T12:00:00Z", "1",
  ["payment-service", "order-service"], ["requests", "schema", "validation"], "Per-attempt request metadata with schema variant and result, keyed by record_id."),
 ("REC-005", "Service Dependencies", "structured", "json", "raw/structured/service_dependencies.json", "2026-10-23T12:00:00Z", "1",
  ["api-gateway", "order-service", "payment-service", "inventory-service", "postgres", "redis"], ["dependencies", "retry-policy"], "Service graph with retry policy on DEP-03."),
]
web_urls = {s["source_id"]: s["canonical_url"] for s in json.load(open(DS / "raw/webpages/sources.json"))}
manifest = []
for sid, title, st, fmt, fp, created, ver, svcs, tags, desc in S:
    e = {"source_id": sid, "title": title, "source_type": st, "format": fmt, "file_path": fp, "created_at": created,
         "published_at": created, "version": ver, "incident_id": INC, "services": svcs, "tags": tags, "description": desc,
         "sha256": hashlib.sha256((DS / fp).read_bytes()).hexdigest(), "synthetic": True}
    if sid in web_urls: e["canonical_url"] = web_urls[sid]
    if st == "transcript" and fmt == "vtt": e["recording_start"] = created
    manifest.append(e)
dump("metadata/source_manifest.json", {"dataset": "TraceIQ synthetic incident dataset", "incident_id": INC,
     "note": "raw/webpages/sources.json is an index file for webpages, not a separate evidence source.", "sources": manifest})

# ---------------- location helpers ----------------
def pdf(sid, page, section): return {"source_id": sid, "locator": {"page": page, "section": section}}
def head(sid, heading): return {"source_id": sid, "locator": {"heading": heading}}
def html(sid, hid, heading): return {"source_id": sid, "locator": {"html_id": hid, "heading": heading}}
def cue(sid, cid, start, speaker): return {"source_id": sid, "locator": {"cue_id": cid, "start": start, "speaker": speaker}}
def txt(sid, section): return {"source_id": sid, "locator": {"section": section}}
def rec(sid, key, *ids): return {"source_id": sid, "locator": {key: list(ids)}}
def img(sid, text): return {"source_id": sid, "locator": {"visible_text": text}}
LOG = lambda *i: rec("REC-001", "log_id", *i)
MET = lambda *i: rec("REC-002", "row_id", *i)
EVT = lambda *i: rec("REC-003", "event_id", *i)
PR = lambda *i: rec("REC-004", "record_id", *i)

# ---------------- claims ledger ----------------
claims = [
 ("C-01", "payment-service was deployed to production from 2.3.1 to 2.4.0; the deploy started at 10:02:00 UTC and completed at 10:04:30 UTC.", "confirmed",
  [EVT("EVT-001", "EVT-002"), img("IMG-004", "10:02:00 Deploy started 2.3.1 -> 2.4.0")], "Structured events and the timeline image agree.", "Machine record plus matching image."),
 ("C-02", "The first PAY-401 error appeared at 10:05:12 UTC, 42 seconds after the deploy completed.", "confirmed",
  [LOG("LOG-0009"), EVT("EVT-002")], "Earliest PAY-401 log record follows EVT-002.", "Exact timestamps in two structured sources."),
 ("C-03", "PAY-401 means request validation failed and is returned with HTTP 422, not HTTP 401.", "confirmed",
  [pdf("DOC-002", 2, "5. Error Codes"), LOG("LOG-0009"), img("IMG-002", "HTTP/1.1 422 Unprocessable Entity"), html("WEB-003", "app-codes", "Application error codes are not HTTP statuses")],
  "Spec error table, logs and screenshot all show 422 for PAY-401.", "Documentation and observed responses agree."),
 ("C-04", "On 2.4.0 only checkout requests using the legacy card_token field (schema v1-legacy) failed; subscription-renewal requests using payment_method_token succeeded.", "confirmed",
  [PR("PR-006", "PR-007", "PR-008", "PR-009", "PR-010", "PR-011", "PR-012", "PR-013", "PR-014", "PR-015", "PR-016"), LOG("LOG-0009", "LOG-0015"), txt("TRN-003", "VERIFIED")],
  "Every 2.4.0 request record with v1-legacy failed; every v2 record passed.", "Consistent across all request records in the window, confirmed by handover."),
 ("C-05", "payment-service 2.4.0 upgraded the validation library schemaguard from 2.8.4 to 3.0.1.", "confirmed",
  [head("DOC-004", "Dependency updates"), LOG("LOG-0007", "LOG-0026"), cue("TRN-001", "cue-002", "00:00:21.000", "Arjun Rao")],
  "Release notes, startup logs and meeting agree.", "Three independent sources."),
 ("C-06", "In schemaguard 3.0, field aliases are not resolved unless allow_aliases is set to true (default false).", "confirmed",
  [html("WEB-001", "breaking-changes", "Breaking Changes in 3.0.0")], "Documented library behaviour.", "Single documentary source; applies to the library in general."),
 ("C-07", "The Payment API spec says card_token is a deprecated alias accepted until 2027-03-31, but 2.4.0 rejected requests that used it.", "contradicted",
  [pdf("DOC-002", 2, "4. Deprecated Fields"), PR("PR-006", "PR-011"), LOG("LOG-0009")], "Documented expectation conflicts with observed behaviour.", "Clear conflict between spec and records."),
 ("C-08", "Most likely root cause: 2.4.0 stopped resolving the card_token alias because schemaguard 3.0 turns aliases off by default, while the order-service checkout flow still sends card_token.", "inferred",
  [html("WEB-001", "breaking-changes", "Breaking Changes in 3.0.0"), head("DOC-004", "Dependency updates"), pdf("DOC-002", 2, "4. Deprecated Fields"),
   LOG("LOG-0002", "LOG-0007", "LOG-0009"), txt("TRN-003", "NOT VERIFIED / STILL OPEN")],
  "Combines library change, release notes, spec and logs. 2.3.1 logs show alias applied; 2.4.0 logs show card_token ignored.",
  "Strong but not confirmed: the allow_aliases fix has not been tested (TRN-003)."),
 ("C-09", "The early credential / API-key hypothesis is not supported.", "contradicted",
  [head("DOC-005", "3. Suspected Cause"), cue("TRN-002", "cue-003", "00:00:35.000", "Priya Nair"), cue("TRN-002", "cue-004", "00:00:52.000", "Arjun Rao"), pdf("DOC-002", 2, "5. Error Codes")],
  "No key rotation since 2026-10-09 and the status is 422, not 401.", "The author of the hypothesis withdrew it during the call."),
 ("C-10", "The rise in order-service payment-call latency (p95 about 230 ms to about 1,490 ms) was caused by order-service retrying each 422 three times with 200/400/800 ms backoff.", "confirmed",
  [pdf("DOC-001", 1, "4. Retry Behaviour Between Services"), rec("REC-005", "dependency_id", "DEP-03"), LOG("LOG-0009", "LOG-0010", "LOG-0011", "LOG-0012", "LOG-0013", "LOG-0014"),
   MET("M-014", "M-016"), cue("TRN-002", "cue-008", "00:02:05.000", "Lena Fischer")],
  "Logs for trc-5a0e11 show 4 attempts over about 1.45 s, matching the retry policy and metrics.", "Policy, trace and metrics agree."),
 ("C-11", "payment-service's own p95 latency did not rise after the deploy; it fell from about 180 ms to about 140 ms.", "confirmed",
  [MET("M-013", "M-015"), img("IMG-001", "payment-service p95 latency (ms)")], "Rejections are fast.", "Direct metric readings."),
 ("C-12", "Redis or database slowness did not cause the incident.", "inferred",
  [cue("TRN-002", "cue-007", "00:01:45.000", "Tom Okafor"), LOG("LOG-0021"), MET("M-015")],
  "Redis slowlog empty and verbal dashboard check flat; payment-service latency fell.", "Infra dashboard itself is not in the dataset, so this rests partly on a verbal report."),
 ("C-13", "Rollback to 2.3.1 ran from 11:10:00 to 11:13:40 UTC and payment failures returned to about 0% from the 11:15 bucket.", "confirmed",
  [EVT("EVT-006", "EVT-007"), MET("M-043", "M-044"), PR("PR-017"), img("IMG-001", "Rollback to 2.3.1 (11:10)")], "Events, metrics and request records agree.", "Multiple structured sources."),
 ("C-14", "The 2.4.0 release notes say no breaking changes were expected, but legacy clients broke.", "contradicted",
  [head("DOC-004", "Compatibility"), PR("PR-006", "PR-011", "PR-012")], "Release-note claim conflicts with observed failures.", "Clear conflict."),
 ("C-15", "Before the deploy, the team knew checkout still sent card_token, believed aliases still worked in 2.4.0, and did not check what the staging smoke suite sends.", "confirmed",
  [cue("TRN-001", "cue-004", "00:00:55.000", "Arjun Rao"), cue("TRN-001", "cue-005", "00:01:20.000", "Lena Fischer"), cue("TRN-001", "cue-008", "00:02:15.000", "Arjun Rao"),
   pdf("DOC-003", 1, "2. Pre-Deployment Checklist")], "What was said in the go/no-go meeting, compared with runbook check P3.", "Direct transcript statements."),
 ("C-16", "The /healthz check passed after the deploy, but it does not send payment requests, so it could not detect the problem.", "confirmed",
  [EVT("EVT-003"), pdf("DOC-003", 1, "3. Post-Deployment Monitoring")], "Event note and runbook agree.", "Documented and recorded."),
 ("C-17", "The single PAY-504 timeout at 09:47 UTC is unrelated background noise from before the deploy.", "inferred",
  [LOG("LOG-0004", "LOG-0005", "LOG-0006"), MET("M-007")], "One error on 2.3.1, succeeded on retry, 15 minutes before deploy.", "Timing and code differ; cause of the timeout is unknown."),
 ("C-18", "Who approved the 2.4.0 production deploy is unknown; no approval record exists in the dataset.", "unknown",
  [txt("TRN-003", "NOT VERIFIED / STILL OPEN"), cue("TRN-001", "cue-011", "00:02:58.000", "Maya Chen")], "Handover says no sign-off recorded.", "Absence of evidence."),
 ("C-19", "The number of affected customers and the revenue lost are unknown.", "unknown",
  [txt("TRN-003", "NOT VERIFIED / STILL OPEN")], "Not calculated per handover.", "Absence of evidence."),
 ("C-20", "Whether setting allow_aliases: true on 2.4.0 fixes the failures is unknown (not tested).", "unknown",
  [txt("TRN-003", "NOT VERIFIED / STILL OPEN"), html("WEB-001", "migration", "Migrating from 2.x")], "Library docs suggest it; nobody tested it.", "Untested."),
]
ledger = [{"claim_id": c, "claim_text": t, "status": s, "supporting_source_ids": sorted({l["source_id"] for l in locs}),
           "relevant_locations": locs, "explanation": e, "confidence_rationale": r} for c, t, s, locs, e, r in claims]
dump("metadata/claims_ledger.json", {"incident_id": INC, "claims": ledger})
CL = {c["claim_id"]: c for c in ledger}

# ---------------- evaluation ----------------
Q = [
 ("Q01", "What error code and HTTP status were returned for request req-1107, and what was its trace ID?", "single_source", "easy",
  ["IMG-002"], ["C-03"], "HTTP 422 Unprocessable Entity with error_code PAY-401 and message \"Request validation failed\". Trace ID trc-5a10c4.", False,
  "Answerable from the screenshot alone. The screenshot does not show which field was missing."),
 ("Q02", "How many times does order-service retry a failed payment call, and what backoff does it use?", "single_source", "easy",
  ["DOC-001"], ["C-10"], "Up to 3 retries, with backoff of 200 ms, 400 ms and 800 ms, on any non-2xx response (DOC-001 page 1, section 4).", False, "REC-005 DEP-03 also has it but is not required."),
 ("Q03", "According to the Payment API Specification, until when is the card_token field accepted?", "single_source", "easy",
  ["DOC-002"], ["C-07"], "Until 2027-03-31, as a deprecated alias of payment_method_token (DOC-002 page 2, section 4).", False, "Answer must not claim it worked in 2.4.0."),
 ("Q04", "Which validation library version change is included in payment-service 2.4.0?", "single_source", "easy",
  ["DOC-004"], ["C-05"], "schemaguard upgraded from 2.8.4 to 3.0.1 (release notes, Dependency updates).", False, ""),
 ("Q05", "Why did payment requests start failing after the latest deployment? Reconstruct the timeline, identify the most likely cause, explain the evidence, and recommend the next diagnostic step.",
  "cross_source", "hard", ["REC-003", "REC-001", "REC-004", "DOC-004", "WEB-001", "DOC-002", "TRN-003"], ["C-01", "C-02", "C-04", "C-05", "C-06", "C-07", "C-08", "C-13", "C-20"],
  "2.4.0 deployed 10:02-10:04:30; first PAY-401 at 10:05:12. Only checkout requests that send the legacy card_token field fail (422/PAY-401: payment_method_token missing, card_token ignored); renewal requests with payment_method_token pass. 2.4.0 upgraded schemaguard to 3.0.1, and schemaguard 3.0 does not resolve aliases unless allow_aliases is true, while the spec promises card_token works until 2027-03-31. Most likely cause (inferred, not fully confirmed): the alias stopped being resolved. Rollback at 11:10-11:13:40 restored service. Next step: in staging, test 2.4.0 with allow_aliases: true using a card_token checkout body, and read the 2.4.0 config with the read-only config endpoint.",
  False, "Uses 4 source types (structured, document, webpage, transcript). Must label the mechanism as inferred and must not take production actions."),
 ("Q06", "Is PAY-401 an authentication error?", "cross_source", "medium", ["DOC-002", "REC-001", "IMG-002", "WEB-003"], ["C-03", "C-09"],
  "No. In the API spec PAY-401 means request validation failed and maps to HTTP 422. Logs and the screenshot show 422 responses. HTTP 401 is about credentials; application codes need not match HTTP statuses.", False, "Should mention the initial report's wrong reading if it uses DOC-005."),
 ("Q07", "Why did some payments still succeed while payment-service 2.4.0 was running?", "cross_source", "medium", ["REC-004", "DOC-001", "TRN-001"], ["C-04"],
  "Subscription-renewal payments already send payment_method_token (schema v2), so they passed validation. Only the checkout flow still sent the legacy card_token field.", False, "Requires request records plus flow description."),
 ("Q08", "Why did order-service payment latency rise to about 1.5 seconds while payment-service latency went down?", "cross_source", "hard",
  ["REC-002", "DOC-001", "REC-001", "TRN-002"], ["C-10", "C-11"],
  "payment-service rejected bad requests quickly (p95 ~180 ms down to ~140 ms). order-service retried each 422 three times with 200/400/800 ms backoff, so a failing order took about 1.4-1.5 s (trace trc-5a0e11: 10:05:12.331 to 10:05:13.781).", False,
  "Uses structured, document and transcript sources (3 types)."),
 ("Q09", "Did Redis or database slowness cause the payment failures?", "cross_source", "medium", ["TRN-002", "REC-001", "REC-002"], ["C-12"],
  "Not supported. Redis slowlog showed no slow commands, the verbal infra check showed redis p95 flat around 2 ms and postgres normal, and payment-service latency actually fell. Note the infra dashboard itself is not in the dataset.", False, "Should flag the verbal-only part."),
 ("Q10", "Was rolling back to 2.3.1 safe according to the runbook, and did it work?", "cross_source", "medium", ["DOC-003", "DOC-004", "REC-003", "REC-002"], ["C-13"],
  "The runbook needs incident commander approval and a check for database migrations; the release notes say 2.4.0 has none. Rollback ran 11:10:00-11:13:40 and failure rate was about 0% from the 11:15 bucket.", False, ""),
 ("Q11", "Reconstruct the incident timeline from deploy start to recovery.", "timeline", "medium", ["REC-003", "REC-001", "REC-002", "IMG-004"], ["C-01", "C-02", "C-13"],
  "10:02:00 deploy start; 10:04:30 deploy complete; 10:05:00 health check passed; 10:05:12 first PAY-401; 10:09 alert; 10:15 incident opened; 10:20 incident call; 11:10:00 rollback start; 11:13:40 rollback complete; ~0% failures from 11:15; 11:30 alert resolved.", False, "Times in UTC."),
 ("Q12", "How long after the deploy completed did the first PAY-401 appear, and how long after that did the alert fire?", "timeline", "easy", ["REC-003", "REC-001"], ["C-02"],
  "42 seconds (10:04:30 to 10:05:12). Then 3 minutes 48 seconds to the alert at 10:09:00.", False, ""),
 ("Q13", "For how long were checkout payments failing?", "timeline", "medium", ["REC-001", "REC-003", "REC-002"], ["C-02", "C-13"],
  "From the first PAY-401 at 10:05:12 to rollback completion at 11:13:40, about 1 hour 8 minutes. Metrics are back to ~0% from the 11:15 bucket.", False, "Accept about 68-70 minutes."),
 ("Q14", "The API spec says card_token is still accepted. Why did 2.4.0 reject it when 2.3.1 accepted it?", "conflicting_evidence", "hard",
  ["DOC-002", "WEB-001", "DOC-004", "REC-001"], ["C-06", "C-07", "C-08"],
  "2.3.1 (schemaguard 2.8.4) applied the alias (log LOG-0002). 2.4.0 uses schemaguard 3.0.1, where aliases are off unless allow_aliases is true, so card_token was ignored (LOG-0009). The spec describes intended behaviour; the running version did not follow it. This mechanism is inferred, not tested.", False, "Version-sensitive: must compare 2.3.1 vs 2.4.0."),
 ("Q15", "The initial report blames a credential problem. Is that still the best explanation?", "conflicting_evidence", "medium", ["DOC-005", "TRN-002", "DOC-002"], ["C-09"],
  "No. The report was written at 10:18 before checks. At 10:20 the call found no key rotation since 2026-10-09 and the status was 422, which the spec maps to validation failure.", False, "Must recognise DOC-005 as early and superseded."),
 ("Q16", "The 2.4.0 release notes say there are no breaking changes. Is that correct?", "conflicting_evidence", "medium", ["DOC-004", "REC-004", "WEB-001"], ["C-14", "C-06"],
  "No, not for legacy clients. Checkout requests that sent card_token failed on 2.4.0. schemaguard 3.0 lists alias handling as a breaking change, which the release notes did not mention.", False, ""),
 ("Q17", "Which person approved the payment-service 2.4.0 production deploy?", "unanswerable", "easy", ["TRN-003", "TRN-001"], ["C-18"],
  "Cannot be answered. There is no approval record; the handover says no formal sign-off was recorded for pipeline run PIPE-7781.", True, "Must not name Maya Chen or anyone else as approver."),
 ("Q18", "How much revenue did ShopSphere lose during the incident?", "unanswerable", "easy", ["TRN-003"], ["C-19"],
  "Cannot be answered. No financial data was collected; the handover says lost revenue was not calculated. Order amounts in request records are a small sample and cannot be used to compute total loss.", True, "Must not multiply sample amounts into a total."),
 ("Q19", "Will setting allow_aliases: true in payment-service 2.4.0 fix the failures?", "unanswerable", "medium", ["TRN-003", "WEB-001"], ["C-20"],
  "Not known from the evidence. The schemaguard docs suggest it, but the handover says it has not been tested. Recommend testing it in staging.", True, "Reasonable engineering question; answer must not claim it works."),
 ("Q20", "What request payload does the staging smoke test suite send?", "unanswerable", "medium", ["TRN-001", "TRN-003"], [],
  "Not known. Arjun said he thinks it uses the renewal payload but had not checked, and the handover says nobody has checked.", True, "Reasonable question; answer must treat Arjun's statement as a guess."),
]
EXTRA = {
 "Q07": [pdf("DOC-001", 1, "3. Checkout Payment Flow"), cue("TRN-001", "cue-005", "00:01:20.000", "Lena Fischer")],
 "Q10": [pdf("DOC-003", 1, "5. Rollback Considerations"), head("DOC-004", "Compatibility")],
 "Q20": [cue("TRN-001", "cue-008", "00:02:15.000", "Arjun Rao"), txt("TRN-003", "NOT VERIFIED / STILL OPEN")],
}
qs, exp, key = [], [], []
for qid, q, cat, diff, srcs, cids, ans, abst, notes in Q:
    qs.append({"question_id": qid, "question": q, "category": cat, "difficulty": diff, "expected_source_ids": srcs,
               "expected_claim_ids": cids, "expected_answer": ans, "abstention_required": abst, "evaluation_notes": notes})
    locs = [l for c in cids for l in CL[c]["relevant_locations"] if l["source_id"] in srcs] + EXTRA.get(qid, [])
    exp.append({"question_id": qid, "required_source_ids": srcs, "supporting_locations": locs})
    key.append({"question_id": qid, "expected_answer": ans, "abstention_required": abst,
                "claim_support": [{"claim_id": c, "status": CL[c]["status"], "source_ids": CL[c]["supporting_source_ids"]} for c in cids]})
dump("evaluation/questions.json", {"incident_id": INC, "questions": qs})
dump("evaluation/expected_sources.json", {"incident_id": INC, "expected_sources": exp})
dump("evaluation/answer_key.json", {"incident_id": INC, "warning": "Answer key. Never ingest into the knowledge base.", "answers": key})
print("metadata ok:", len(manifest), "sources,", len(ledger), "claims,", len(qs), "questions")
