"""Generate PDF, Markdown and HTML evidence for INC-2026-1042 (synthetic)."""
import hashlib, json
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

RAW = Path(__file__).resolve().parents[2] / "dataset" / "raw"
DOCS, WEB = RAW / "documents", RAW / "webpages"
ss = getSampleStyleSheet()
H1, H2, BODY = ss["Title"], ss["Heading2"], ss["BodyText"]
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8, textColor=colors.grey)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.5, leading=10.5)

def table(rows, widths):
    data = [[Paragraph(str(c), CELL) for c in r] for r in rows]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dde4ee")),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                           ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    return t

def build(name, title, meta, blocks):
    def footer(c, d):
        c.setFont("Helvetica", 8); c.setFillColor(colors.grey)
        c.drawString(2 * cm, 1.2 * cm, f"ShopSphere Engineering - {title} - FICTIONAL / SYNTHETIC")
        c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {d.page}")
    story = [Paragraph(title, H1), Paragraph(meta, SMALL), Spacer(1, 8)]
    for b in blocks:
        if isinstance(b, str):
            story.append(Paragraph(b[3:], H2) if b.startswith("## ") else Paragraph(b, BODY))
        else:
            story.append(b)
        story.append(Spacer(1, 4))
    SimpleDocTemplate(str(DOCS / name), pagesize=A4, title=title, author="ShopSphere Engineering (fictional)",
                      leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2 * cm
                      ).build(story, onFirstPage=footer, onLaterPages=footer)

# ---------- DOC-001 architecture_overview.pdf ----------
build("architecture_overview.pdf", "ShopSphere Architecture Overview",
      "Document version 1.3 | Last updated 2026-09-02 | Owner: Platform Team", [
    "## 1. Purpose",
    "This document explains how the ShopSphere e-commerce platform is built. It covers the core services, how a "
    "checkout flows through them, and how failures between services are handled. It is written for new developers.",
    "## 2. Core Services",
    table([["Service", "Version (2026-09)", "What it does", "Talks to"],
           ["api-gateway", "1.9.2", "Public entry point. Routes /checkout and /orders.", "order-service, redis"],
           ["order-service", "5.7.0", "Creates orders. Reserves stock, then asks for payment.", "inventory-service, payment-service, postgres"],
           ["payment-service", "2.3.1", "Validates payment requests and records payments.", "postgres, redis"],
           ["inventory-service", "3.2.0", "Reserves and releases stock.", "postgres"],
           ["postgres", "15.6", "Main database (orders, payments, inventory tables).", "-"],
           ["redis", "7.2.4", "Session cache and payment idempotency-key cache.", "-"]],
          [3.2, 2.6, 6.2, 5.0]),
    "## 3. Checkout Payment Flow",
    "1) The customer submits checkout to api-gateway. 2) api-gateway forwards it to order-service. "
    "3) order-service reserves stock with inventory-service. 4) order-service sends POST /v2/payments to payment-service. "
    "5) payment-service validates the request body, checks the idempotency key in redis, and writes the payment to postgres. "
    "6) order-service marks the order PAID or PAYMENT_FAILED.",
    "order-service sends payments from two flows: the <b>checkout</b> flow (customer orders) and the "
    "<b>subscription-renewal</b> flow (scheduled monthly renewals). The two flows build the payment request "
    "with separate code.",
    "## 4. Retry Behaviour Between Services",
    "order-service retries a failed payment call up to <b>3 times</b> with exponential backoff of <b>200 ms, 400 ms and 800 ms</b>. "
    "A call is treated as failed when payment-service returns any non-2xx status. Retries reuse the same idempotency key, "
    "so a retried payment can never be charged twice. Because of the waits, an order whose payment fails on every attempt "
    "takes roughly 1.4 seconds or more before order-service gives up.",
    table([["Setting", "Value"], ["max_retries", "3"], ["backoff", "200 ms, 400 ms, 800 ms"],
           ["retry_on", "any non-2xx response"], ["timeout per attempt", "3000 ms"]], [6, 8]),
    "## 5. Data Stores",
    "postgres holds the orders, payments and inventory tables. redis holds web sessions (used by api-gateway) and "
    "payment idempotency keys (used by payment-service, kept for 24 hours). Neither data store is called directly by the customer.",
    "## 6. Monitoring",
    "Each service exports request count, error count and latency percentiles (p50, p95, p99) every 5 minutes. "
    "The alert PaymentFailureRateHigh fires when the payment failure rate stays above 5% for 5 minutes.",
])

# ---------- DOC-002 payment_api_specification.pdf ----------
build("payment_api_specification.pdf", "Payment API Specification v2.0",
      "Spec version 2.0 | Published 2026-08-14 | Owner: Payments Team | Applies to payment-service 2.x", [
    "## 1. Overview",
    "payment-service exposes one endpoint for creating payments. All clients (currently only order-service) must "
    "send JSON bodies that follow the payment-request/2.0 schema described here.",
    "## 2. Endpoint",
    "<b>POST /v2/payments</b> - Content-Type: application/json. A successful payment returns <b>HTTP 201 Created</b> "
    "with the payment_id.",
    "## 3. Request Fields (schema payment-request/2.0)",
    table([["Field", "Type", "Required", "Description"],
           ["order_id", "string", "yes", "ShopSphere order ID, e.g. ORD-88213."],
           ["amount_minor", "integer", "yes", "Amount in minor units (cents). 4999 = 49.99."],
           ["currency", "string", "yes", "ISO 4217 code, e.g. EUR."],
           ["payment_method_token", "string", "yes", "Token for the customer's payment method. Never a raw card number."],
           ["idempotency_key", "string", "yes", "Unique per order. Reused on retries."],
           ["customer_ref", "string", "no", "Optional customer reference."]],
          [4.2, 2, 2, 8.8]),
    "Example body: {\"order_id\": \"ORD-10001\", \"amount_minor\": 4999, \"currency\": \"EUR\", "
    "\"payment_method_token\": \"pm_tok_example\", \"idempotency_key\": \"idem-ORD-10001\"}",
    PageBreak(),
    "## 4. Deprecated Fields",
    "Version 1 of the API used the field name <b>card_token</b>. In schema payment-request/2.0, <b>card_token</b> is a "
    "<b>deprecated alias</b> of <b>payment_method_token</b>. If a request contains card_token and no payment_method_token, "
    "payment-service treats card_token as payment_method_token. The alias will be <b>accepted until 2027-03-31</b>. "
    "Clients should move to payment_method_token before that date.",
    table([["Deprecated field", "Replaced by", "Accepted until"], ["card_token", "payment_method_token", "2027-03-31"]], [5, 5, 5]),
    "## 5. Error Codes",
    "Errors return a JSON body with error_code, message and trace_id.",
    table([["Error code", "HTTP status", "Meaning"],
           ["PAY-400", "400 Bad Request", "Body is not valid JSON."],
           ["PAY-401", "422 Unprocessable Entity", "Request validation failed (for example a required field is missing or has the wrong type)."],
           ["PAY-402", "402 Payment Required", "Payment was declined."],
           ["PAY-409", "409 Conflict", "Idempotency key reused with a different body."],
           ["PAY-504", "504 Gateway Timeout", "Payment processor did not respond in time."]],
          [2.6, 4.2, 10.2]),
    "## 6. Change History",
    table([["Version", "Date", "Change"], ["1.0", "2025-03-10", "First version. Field card_token."],
           ["2.0", "2026-08-14", "Renamed card_token to payment_method_token. card_token kept as deprecated alias."]],
          [2, 3, 12]),
])

# ---------- DOC-003 deployment_runbook.pdf ----------
build("deployment_runbook.pdf", "Payment Service Deployment Runbook",
      "Runbook version 3.1 | Last reviewed 2026-07-30 | Owner: SRE Team", [
    "## 1. Scope",
    "Use this runbook when deploying payment-service to production and when payment errors rise after a deploy. "
    "Everything in Section 4 is read-only and safe to run during an incident.",
    "## 2. Pre-Deployment Checklist",
    table([["#", "Check", "Who"],
           ["P1", "Release notes reviewed in the go/no-go meeting.", "Release manager"],
           ["P2", "Staging smoke tests passed.", "Service owner"],
           ["P3", "Confirm every client sends request fields that the new version accepts (check dependency upgrades too).", "Service owner"],
           ["P4", "Confirm whether the release contains database migrations.", "Service owner"],
           ["P5", "On-call SRE is aware of the deploy window.", "Release manager"]],
          [1.2, 12, 3.8]),
    "## 3. Post-Deployment Monitoring",
    "Watch the payment dashboard for 15 minutes after the rollout completes. The /healthz check only proves the process is up; "
    "it does not send payment requests. If the payment failure rate stays above <b>5% for 10 minutes</b>, start rollback evaluation (Section 5).",
    "## 4. Safe Diagnostic Checks (read-only)",
    table([["#", "Check", "What it tells you"],
           ["D1", "Group recent errors by error_code and service version.", "Whether errors started with the new version."],
           ["D2", "Compare one failing request with one succeeding request (fields present, client flow).", "Whether only some request shapes fail."],
           ["D3", "Look up the error_code in the Payment API Specification.", "What the error actually means. Do not guess from the number."],
           ["D4", "Read the running config with GET /internal/config (read-only).", "Whether a setting differs between versions."],
           ["D5", "Reproduce in staging with the same request body.", "Confirms the failure without touching production."],
           ["D6", "Check data-store latency (redis, postgres) on the infra dashboard.", "Rules data stores in or out."]],
          [1.2, 8.3, 7.5]),
    "## 5. Rollback Considerations",
    "Rollback is done by re-running the deploy pipeline with the previous version. It needs approval from the incident "
    "commander. Before rolling back, check that the release has no database migrations (if it does, contact the Payments Team first). "
    "After rollback, confirm recovery on the dashboard for at least 5 minutes.",
    "## 6. Do Not",
    "Do not edit production config by hand. Do not restart redis or postgres to 'see if it helps'. Do not replay failed "
    "payments without their original idempotency keys.",
])

# ---------- DOC-004 release_notes_2_4_0.md ----------
(DOCS / "release_notes_2_4_0.md").write_text("""# payment-service 2.4.0 Release Notes

- **Release date:** 2026-10-21
- **Previous version:** 2.3.1
- **Owner:** Payments Team

## Summary

Version 2.4.0 is a maintenance release. It updates dependencies, improves error messages, and adds request metrics.

## Changes

### Dependency updates

- Upgraded request-validation library **schemaguard** from 2.8.4 to 3.0.1.
- Upgraded HTTP framework to the latest patch version.

### Request handling

- Request schema handling aligned with Payment API v2 (schema `payment-request/2.0`).
- Validation error messages now list every failing field instead of only the first one.

### Observability

- New metric `payment_validation_failures_total`, labelled by error code.

## Compatibility

- No breaking changes to the public payment API are expected.
- No database migrations.

## Known Issues

- None at release time.
""")

# ---------- Webpages ----------
def page(fname, title, site, body):
    WEB.joinpath(fname).write_text(f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{title}</title>
<meta name="description" content="Fictional page for a synthetic training dataset."></head>
<body>
<header><p>{site} &mdash; fictional site for training data</p></header>
<main>
<h1>{title}</h1>
{body}
</main>
<footer><p>This page is fictional and is not official documentation for any real product.</p></footer>
</body>
</html>
""")

page("dependency_release_notes.html", "schemaguard 3.0 Release Notes", "schemaguard.example", """
<p>Published 2026-09-15. Applies to schemaguard 3.0.0 and 3.0.1.</p>
<h2 id="overview">Overview</h2>
<p>schemaguard is a JSON request-validation library. Version 3.0 is a major release with breaking changes. Read this page before upgrading from 2.x.</p>
<h2 id="breaking-changes">Breaking Changes in 3.0.0</h2>
<p><strong>Field aliases are now opt-in.</strong> In 2.x, aliases declared in a schema were always resolved. In 3.0, the setting <code>allow_aliases</code> defaults to <code>false</code>. Aliases are ignored unless you set <code>allow_aliases: true</code> in the validator config.</p>
<p><strong>Unknown fields.</strong> Fields not defined in the schema are ignored and reported in the error message as &quot;unrecognized field ... ignored&quot;. An ignored alias does not count as its target field, so a required target field will be reported as missing.</p>
<p><strong>Error messages.</strong> Validation errors now list every failing field.</p>
<p><strong>Python.</strong> Python 3.10 or newer is required.</p>
<h2 id="migration">Migrating from 2.x</h2>
<p>If any of your clients still send aliased field names, add <code>allow_aliases: true</code> to your validator config before upgrading, or move those clients to the new names first.</p>
<h2 id="3-0-1">3.0.1 (2026-09-29)</h2>
<p>Bug fix: date-time fields with a trailing &quot;Z&quot; were rejected on some platforms. No behaviour changes to aliases.</p>
""")

page("payment_validation_troubleshooting.html", "Troubleshooting Payment Request Validation Errors", "devnotes.example", """
<p>Published 2026-05-03. General guide. Not about any specific company.</p>
<h2 id="what-it-means">What a validation error means</h2>
<p>A validation error means the server read your request but the body did not match the schema it expects. The server never tried to charge the payment. Retrying the same body will fail the same way.</p>
<h2 id="common-causes">Common causes</h2>
<p>The most common causes are: a renamed field that one client still sends with the old name, a missing required field, a wrong type (for example the amount sent as a string), and a library upgrade on the server that changed how the schema is applied.</p>
<h2 id="how-to-check">How to check</h2>
<p>Put one failing request next to one working request and compare the field names. If only one client or one code path fails, the problem is usually that client's request shape, not the network or the database. Check the server's dependency changelog when errors begin right after a deploy.</p>
<h2 id="retries">A note on retries</h2>
<p>Validation errors are not temporary. Clients that retry them only add load and delay. Many teams retry only on 5xx responses and timeouts.</p>
""")

page("http_error_reference.html", "HTTP Status Codes: 4xx Reference", "httpref.example", """
<p>Published 2025-11-20. General reference.</p>
<h2 id="400">400 Bad Request</h2>
<p>The server could not parse the request, for example invalid JSON.</p>
<h2 id="401">401 Unauthorized</h2>
<p>The request has no valid credentials. The client should send or refresh its credentials. This status is about authentication, not about the request body.</p>
<h2 id="403">403 Forbidden</h2>
<p>The client is known but is not allowed to do this action.</p>
<h2 id="409">409 Conflict</h2>
<p>The request conflicts with the current state, for example a reused idempotency key with a different body.</p>
<h2 id="422">422 Unprocessable Content</h2>
<p>The body was parsed but failed validation, for example a required field is missing. Older documents call this status &quot;Unprocessable Entity&quot;.</p>
<h2 id="app-codes">Application error codes are not HTTP statuses</h2>
<p>Many APIs return their own codes such as &quot;ABC-401&quot;. The number inside such a code is chosen by the API owner and does not have to match an HTTP status. Always check the HTTP status line and the API&#39;s own error table.</p>
""")

srcs = [("WEB-001", "schemaguard 3.0 Release Notes", "https://schemaguard.example/releases/3.0", "dependency_release_notes.html", "2026-09-15T00:00:00Z", "3.0.1"),
        ("WEB-002", "Troubleshooting Payment Request Validation Errors", "https://devnotes.example/payments/request-validation-errors", "payment_validation_troubleshooting.html", "2026-05-03T00:00:00Z", "1.0"),
        ("WEB-003", "HTTP Status Codes: 4xx Reference", "https://httpref.example/status/4xx", "http_error_reference.html", "2025-11-20T00:00:00Z", "1.0")]
(WEB / "sources.json").write_text(json.dumps([{
    "source_id": s, "title": t, "canonical_url": u, "local_file_path": f"raw/webpages/{f}", "source_type": "webpage",
    "published_at": p, "version": v, "content_hash": "sha256:" + hashlib.sha256((WEB / f).read_bytes()).hexdigest(),
    "fictional": True} for s, t, u, f, p, v in srcs], indent=2) + "\n")
print("documents + webpages ok")
