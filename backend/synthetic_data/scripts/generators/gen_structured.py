"""Generate structured records for INC-2026-1042 (synthetic). Deterministic."""
import csv, json, random
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "dataset" / "raw" / "structured"
ROOT.mkdir(parents=True, exist_ok=True)
random.seed(1042)

def ts(h, m, s=0, ms=0):
    return datetime(2026, 10, 23, h, m, s, ms * 1000, tzinfo=timezone.utc)

def iso(dt):
    if dt.microsecond:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.") + f"{dt.microsecond // 1000:03d}Z"
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def dump(name, obj):
    (ROOT / name).write_text(json.dumps(obj, indent=2) + "\n")

DEPLOY_START, DEPLOY_DONE = ts(10, 2), ts(10, 4, 30)
ROLLBACK_START, ROLLBACK_DONE = ts(11, 10), ts(11, 13, 40)

# ---------------- application_logs.json ----------------
V1_MSG = ("Request validation failed: required field 'payment_method_token' is missing; "
          "unrecognized field 'card_token' ignored (schema=payment-request/2.0)")
logs = []
def log(t, sev, svc, ver, trace, msg, code=None, **extra):
    rec = {"log_id": f"LOG-{len(logs)+1:04d}", "timestamp": iso(t), "severity": sev,
           "service": svc, "version": ver, "trace_id": trace, "error_code": code, "message": msg}
    rec.update(extra)
    logs.append(rec)

log(ts(9, 41, 2, 118), "INFO", "api-gateway", "1.9.2", "trc-3b71e0", "POST /checkout routed to order-service", http_status=202)
log(ts(9, 41, 2, 205), "DEBUG", "payment-service", "2.3.1", "trc-3b71e0",
    "Field alias applied: card_token -> payment_method_token (schema=payment-request/2.0)", request_id="req-1001")
log(ts(9, 41, 2, 291), "INFO", "payment-service", "2.3.1", "trc-3b71e0", "Payment captured", request_id="req-1001", http_status=201)
log(ts(9, 47, 5, 640), "ERROR", "payment-service", "2.3.1", "trc-41c9d2",
    "Payment processor did not respond within 3000 ms", code="PAY-504", request_id="req-1004", http_status=504)
log(ts(9, 47, 6, 12), "WARN", "order-service", "5.7.0", "trc-41c9d2",
    "Payment call returned 504; retry 1 of 3 scheduled in 200 ms", request_id="req-1004")
log(ts(9, 47, 6, 301), "INFO", "payment-service", "2.3.1", "trc-41c9d2", "Payment captured", request_id="req-1004", http_status=201)
log(ts(10, 3, 10, 450), "INFO", "payment-service", "2.4.0", None,
    "payment-service 2.4.0 started; validator=schemaguard 3.0.1; schema=payment-request/2.0; instance=pay-7d9f-2")
log(ts(10, 4, 31, 2), "INFO", "payment-service", "2.4.0", None, "Rollout complete: 4/4 instances healthy on 2.4.0")
log(ts(10, 5, 12, 331), "ERROR", "payment-service", "2.4.0", "trc-5a0e11", V1_MSG,
    code="PAY-401", request_id="req-1101", http_status=422)
log(ts(10, 5, 12, 340), "WARN", "order-service", "5.7.0", "trc-5a0e11",
    "Payment call returned 422; retry 1 of 3 scheduled in 200 ms", request_id="req-1101")
log(ts(10, 5, 12, 552), "ERROR", "payment-service", "2.4.0", "trc-5a0e11", V1_MSG,
    code="PAY-401", request_id="req-1101", http_status=422, attempt=2)
log(ts(10, 5, 12, 961), "ERROR", "payment-service", "2.4.0", "trc-5a0e11", V1_MSG,
    code="PAY-401", request_id="req-1101", http_status=422, attempt=3)
log(ts(10, 5, 13, 774), "ERROR", "payment-service", "2.4.0", "trc-5a0e11", V1_MSG,
    code="PAY-401", request_id="req-1101", http_status=422, attempt=4)
log(ts(10, 5, 13, 781), "ERROR", "order-service", "5.7.0", "trc-5a0e11",
    "Payment failed after 3 retries (last status 422, error_code PAY-401); order ORD-88213 marked PAYMENT_FAILED",
    code="PAY-401", request_id="req-1101")
log(ts(10, 5, 40, 87), "INFO", "payment-service", "2.4.0", "trc-5a1f02",
    "Payment captured", request_id="req-1102", http_status=201)
log(ts(10, 6, 3, 412), "ERROR", "payment-service", "2.4.0", "trc-5a2b77", V1_MSG,
    code="PAY-401", request_id="req-1103", http_status=422)
log(ts(10, 9, 0, 0), "WARN", "payment-service", "2.4.0", None,
    "Alert PaymentFailureRateHigh firing: failure rate 93.8% over 5m (threshold 5%)")
log(ts(10, 11, 47, 203), "ERROR", "payment-service", "2.4.0", "trc-5a10c4", V1_MSG,
    code="PAY-401", request_id="req-1107", http_status=422)
log(ts(10, 11, 47, 210), "INFO", "order-service", "5.7.0", "trc-5a10c4",
    "Debug console captured response for request req-1107 (status 422)", request_id="req-1107")
log(ts(10, 12, 30, 640), "INFO", "payment-service", "2.4.0", "trc-5a3c90",
    "Payment captured", request_id="req-1108", http_status=201)
log(ts(10, 14, 2, 115), "INFO", "redis", "7.2.4", None, "Slowlog: 0 commands over 10 ms in last 5m")
log(ts(10, 26, 41, 902), "ERROR", "payment-service", "2.4.0", "trc-5b77a3", V1_MSG,
    code="PAY-401", request_id="req-1112", http_status=422)
log(ts(10, 41, 18, 77), "ERROR", "payment-service", "2.4.0", "trc-5c0412", V1_MSG,
    code="PAY-401", request_id="req-1115", http_status=422)
log(ts(10, 58, 9, 330), "INFO", "payment-service", "2.4.0", "trc-5c9d31",
    "Payment captured", request_id="req-1116", http_status=201)
log(ts(11, 10, 0, 0), "INFO", "payment-service", "2.4.0", None, "Rollback initiated by deploy tool: 2.4.0 -> 2.3.1")
log(ts(11, 12, 44, 509), "INFO", "payment-service", "2.3.1", None,
    "payment-service 2.3.1 started; validator=schemaguard 2.8.4; schema=payment-request/2.0; instance=pay-6c1a-1")
log(ts(11, 13, 41, 15), "INFO", "payment-service", "2.3.1", None, "Rollout complete: 4/4 instances healthy on 2.3.1")
log(ts(11, 16, 22, 418), "DEBUG", "payment-service", "2.3.1", "trc-6a0f55",
    "Field alias applied: card_token -> payment_method_token (schema=payment-request/2.0)", request_id="req-1201")
log(ts(11, 16, 22, 497), "INFO", "payment-service", "2.3.1", "trc-6a0f55", "Payment captured", request_id="req-1201", http_status=201)
log(ts(11, 21, 5, 230), "INFO", "order-service", "5.7.0", "trc-6a3e08",
    "Order ORD-89102 paid; payment latency 214 ms", request_id="req-1203")
for r in logs:
    r.setdefault("request_id", None); r.setdefault("http_status", None)
assert logs[3]["error_code"] == "PAY-504" and logs[6]["log_id"] == "LOG-0007" and logs[8]["timestamp"].startswith("2026-10-23T10:05:12")
dump("application_logs.json", {"incident_id": "INC-2026-1042", "environment": "production",
                                "timezone": "UTC", "records": logs})

# ---------------- metrics.csv ----------------
rows, rid = [], 1
t = ts(9, 30)
while t <= ts(11, 55):
    orders = 600 + random.randint(-30, 30)
    after_deploy = t >= ts(10, 5) and t < ts(11, 10)
    if t == ts(11, 10):   # rollback finished at 11:13:40, so this bucket is partly bad
        fail_share = 0.78 * (3.67 / 5)
    elif after_deploy:
        fail_share = 0.78 + random.uniform(-0.015, 0.015)
    else:
        fail_share = 0.0
    failed_orders = round(orders * fail_share)
    baseline_err = 1 if t == ts(9, 45) else 0          # the single PAY-504 at 09:47
    attempts = orders + failed_orders * 3 + baseline_err
    pay_errors = failed_orders * 4 + baseline_err
    if fail_share > 0.5:
        p_lat = (12 + random.randint(0, 3), 138 + random.randint(0, 6), 226 + random.randint(0, 9))
        o_lat = (1438 + random.randint(0, 12), 1484 + random.randint(0, 14), 1552 + random.randint(0, 20))
    elif fail_share > 0:
        p_lat = (31, 152, 241); o_lat = (612, 1471, 1540)
    else:
        p_lat = (84 + random.randint(0, 4), 176 + random.randint(0, 8), 255 + random.randint(0, 12))
        o_lat = (138 + random.randint(0, 6), 226 + random.randint(0, 9), 318 + random.randint(0, 14))
    if t == ts(9, 45):
        p_lat = (p_lat[0], p_lat[1], 3010); o_lat = (o_lat[0], o_lat[1], 3290)
    pay_ver = "2.4.0" if ts(10, 5) <= t < ts(11, 10) else ("2.3.1" if t < ts(10, 0) or t >= ts(11, 15) else "mixed")
    rows.append({"row_id": f"M-{rid:03d}", "timestamp": iso(t), "service": "payment-service", "version": pay_ver,
                 "metric_scope": "payment_attempts", "request_count": attempts, "error_count": pay_errors,
                 "error_rate_pct": round(100 * pay_errors / attempts, 1),
                 "latency_p50_ms": p_lat[0], "latency_p95_ms": p_lat[1], "latency_p99_ms": p_lat[2]}); rid += 1
    rows.append({"row_id": f"M-{rid:03d}", "timestamp": iso(t), "service": "order-service", "version": "5.7.0",
                 "metric_scope": "orders_payment_outcome", "request_count": orders, "error_count": failed_orders + 0,
                 "error_rate_pct": round(100 * failed_orders / orders, 1),
                 "latency_p50_ms": o_lat[0], "latency_p95_ms": o_lat[1], "latency_p99_ms": o_lat[2]}); rid += 1
    t += timedelta(minutes=5)
with open(ROOT / "metrics.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

# ---------------- deployment_events.json ----------------
def ev(i, t, etype, old, new, status, note, **kw):
    d = {"event_id": f"EVT-{i:03d}", "timestamp": iso(t), "event_type": etype, "service": "payment-service",
         "old_version": old, "new_version": new, "environment": "production", "status": status,
         "incident_id": kw.pop("incident_id", None), "note": note}
    d.update(kw); return d
events = [
    ev(1, DEPLOY_START, "deploy_started", "2.3.1", "2.4.0", "in_progress",
       "Rolling deploy of 4 instances started by deploy pipeline run PIPE-7781.", pipeline_run="PIPE-7781"),
    ev(2, DEPLOY_DONE, "deploy_completed", "2.3.1", "2.4.0", "succeeded",
       "All 4 instances running 2.4.0.", pipeline_run="PIPE-7781"),
    ev(3, ts(10, 5), "health_check", "2.4.0", "2.4.0", "passed",
       "GET /healthz returned 200 on 4/4 instances. Health check does not send payment requests."),
    ev(4, ts(10, 9), "alert_triggered", "2.4.0", "2.4.0", "firing",
       "PaymentFailureRateHigh: failure rate above 5% for 5 minutes."),
    ev(5, ts(10, 15), "incident_opened", "2.4.0", "2.4.0", "open",
       "Incident opened for elevated payment failures.", incident_id="INC-2026-1042"),
    ev(6, ROLLBACK_START, "rollback_started", "2.4.0", "2.3.1", "in_progress",
       "Rollback to previous version started by deploy pipeline run PIPE-7790.",
       incident_id="INC-2026-1042", pipeline_run="PIPE-7790"),
    ev(7, ROLLBACK_DONE, "rollback_completed", "2.4.0", "2.3.1", "succeeded",
       "All 4 instances running 2.3.1.", incident_id="INC-2026-1042", pipeline_run="PIPE-7790"),
    ev(8, ts(11, 30), "alert_resolved", "2.3.1", "2.3.1", "resolved",
       "PaymentFailureRateHigh resolved.", incident_id="INC-2026-1042"),
]
dump("deployment_events.json", {"incident_id": "INC-2026-1042", "events": events})

# ---------------- payment_requests.json ----------------
LEGACY = ["order_id", "amount_minor", "currency", "card_token", "idempotency_key"]
V2 = ["order_id", "amount_minor", "currency", "payment_method_token", "idempotency_key"]
reqs = []
def rq(rid, trace, t, flow, ver, status, code, result, attempt=1, amount=4999, order=None):
    variant = "v1-legacy" if flow == "checkout" else "v2"
    reqs.append({"request_id": rid, "trace_id": trace, "received_at": iso(t), "client_service": "order-service",
                 "client_flow": flow, "schema_variant": variant,
                 "fields_present": LEGACY if variant == "v1-legacy" else V2,
                 "payment_service_version": ver, "attempt": attempt, "http_status": status,
                 "error_code": code, "validation_result": result,
                 "order_id": order, "amount_minor": amount, "currency": "EUR"})
OK, BAD = "passed", "failed_missing_required_field:payment_method_token"
rq("req-1001", "trc-3b71e0", ts(9, 41, 2, 205), "checkout", "2.3.1", 201, None, "passed_with_alias", order="ORD-87990")
rq("req-1002", "trc-3b8a14", ts(9, 43, 51, 20), "subscription_renewal", "2.3.1", 201, None, OK, amount=999, order="ORD-88001")
rq("req-1003", "trc-3c0277", ts(9, 52, 17, 830), "checkout", "2.3.1", 201, None, "passed_with_alias", amount=12850, order="ORD-88044")
rq("req-1004", "trc-41c9d2", ts(9, 47, 5, 640), "checkout", "2.3.1", 504, "PAY-504", "passed_with_alias", amount=2599, order="ORD-88019")
rq("req-1004", "trc-41c9d2", ts(9, 47, 6, 301), "checkout", "2.3.1", 201, None, "passed_with_alias", attempt=2, amount=2599, order="ORD-88019")
for a, t_ in enumerate([ts(10, 5, 12, 331), ts(10, 5, 12, 552), ts(10, 5, 12, 961), ts(10, 5, 13, 774)], 1):
    rq("req-1101", "trc-5a0e11", t_, "checkout", "2.4.0", 422, "PAY-401", BAD, attempt=a, amount=7450, order="ORD-88213")
rq("req-1102", "trc-5a1f02", ts(10, 5, 40, 87), "subscription_renewal", "2.4.0", 201, None, OK, amount=999, order="ORD-88216")
rq("req-1103", "trc-5a2b77", ts(10, 6, 3, 412), "checkout", "2.4.0", 422, "PAY-401", BAD, amount=3200, order="ORD-88219")
rq("req-1107", "trc-5a10c4", ts(10, 11, 47, 203), "checkout", "2.4.0", 422, "PAY-401", BAD, amount=1899, order="ORD-88251")
rq("req-1108", "trc-5a3c90", ts(10, 12, 30, 640), "subscription_renewal", "2.4.0", 201, None, OK, amount=1499, order="ORD-88260")
rq("req-1112", "trc-5b77a3", ts(10, 26, 41, 902), "checkout", "2.4.0", 422, "PAY-401", BAD, amount=5600, order="ORD-88402")
rq("req-1115", "trc-5c0412", ts(10, 41, 18, 77), "checkout", "2.4.0", 422, "PAY-401", BAD, amount=899, order="ORD-88577")
rq("req-1116", "trc-5c9d31", ts(10, 58, 9, 330), "subscription_renewal", "2.4.0", 201, None, OK, amount=999, order="ORD-88690")
rq("req-1201", "trc-6a0f55", ts(11, 16, 22, 418), "checkout", "2.3.1", 201, None, "passed_with_alias", amount=4200, order="ORD-89088")
rq("req-1202", "trc-6a1b90", ts(11, 18, 47, 15), "subscription_renewal", "2.3.1", 201, None, OK, amount=999, order="ORD-89095")
rq("req-1203", "trc-6a3e08", ts(11, 21, 5, 16), "checkout", "2.3.1", 201, None, "passed_with_alias", amount=15990, order="ORD-89102")
reqs.sort(key=lambda r: r["received_at"])
for i, r in enumerate(reqs, 1):
    r["record_id"] = f"PR-{i:03d}"
reqs = [{"record_id": r.pop("record_id"), **r} for r in reqs]
dump("payment_requests.json", {"incident_id": "INC-2026-1042",
     "note": "Synthetic request metadata only. Token values and card data are never stored.", "records": reqs})

# ---------------- service_dependencies.json ----------------
deps = {
    "system": "ShopSphere",
    "services": [
        {"name": "api-gateway", "type": "service", "version": "1.9.2"},
        {"name": "order-service", "type": "service", "version": "5.7.0"},
        {"name": "payment-service", "type": "service", "version": "2.3.1",
         "version_note": "Version after rollback at 2026-10-23T11:13:40Z. Ran 2.4.0 from 10:04:30Z to 11:13:40Z."},
        {"name": "inventory-service", "type": "service", "version": "3.2.0"},
        {"name": "postgres", "type": "database", "version": "15.6"},
        {"name": "redis", "type": "cache", "version": "7.2.4"},
    ],
    "dependencies": [
        {"dependency_id": "DEP-01", "upstream": "api-gateway", "downstream": "order-service", "protocol": "HTTP", "purpose": "Route /checkout and /orders"},
        {"dependency_id": "DEP-02", "upstream": "order-service", "downstream": "inventory-service", "protocol": "HTTP", "purpose": "Reserve stock"},
        {"dependency_id": "DEP-03", "upstream": "order-service", "downstream": "payment-service", "protocol": "HTTP", "purpose": "POST /v2/payments",
         "retry_policy": {"max_retries": 3, "backoff_ms": [200, 400, 800], "retry_on": "any non-2xx response"}},
        {"dependency_id": "DEP-04", "upstream": "order-service", "downstream": "postgres", "protocol": "SQL", "purpose": "orders table"},
        {"dependency_id": "DEP-05", "upstream": "payment-service", "downstream": "postgres", "protocol": "SQL", "purpose": "payments table"},
        {"dependency_id": "DEP-06", "upstream": "payment-service", "downstream": "redis", "protocol": "RESP", "purpose": "Idempotency-key cache"},
        {"dependency_id": "DEP-07", "upstream": "inventory-service", "downstream": "postgres", "protocol": "SQL", "purpose": "inventory table"},
        {"dependency_id": "DEP-08", "upstream": "api-gateway", "downstream": "redis", "protocol": "RESP", "purpose": "Session cache"},
    ],
    "note": "upstream calls downstream. Graph has no cycles.",
}
dump("service_dependencies.json", deps)
print("structured ok:", len(logs), "logs,", len(rows), "metric rows,", len(events), "events,", len(reqs), "requests")
