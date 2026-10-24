# Master Incident Specification — INC-2026-1042

> **SYNTHETIC. DATASET-MAINTAINER ONLY. CONTAINS THE ANSWER KEY.**
> This file must never be ingested into the TraceIQ knowledge base. Ingest only `dataset/raw/`.

## 1. System

ShopSphere — fictional e-commerce platform.

| Service | Role |
|---|---|
| api-gateway | Public entry point. Routes `/checkout` to order-service. |
| order-service | Creates orders; calls inventory-service and payment-service. Retries any non-2xx payment response up to 3 times (backoff 200 / 400 / 800 ms). |
| payment-service | Validates payment requests (library: schemaguard) and charges them. |
| inventory-service | Reserves stock. |
| PostgreSQL (`postgres`) | Orders, payments, inventory tables. |
| Redis (`redis`) | Session cache and payment idempotency cache. |

Six core components. No external payment processor is modelled as a service.

## 2. Actual root cause (the answer)

1. payment-service **2.4.0** upgraded its request-validation library **schemaguard from 2.8.4 to 3.0.1**.
2. schemaguard **3.0.0** changed `allow_aliases` to default to **false** (it was effectively true in 2.x). Field aliases are no longer resolved unless enabled.
3. The Payment API spec v2.0 says the legacy field `card_token` is a **deprecated alias** of `payment_method_token` and is accepted until 2027-03-31.
4. payment-service 2.4.0 did not set `allow_aliases: true`.
5. order-service's **checkout** flow still sends the legacy `card_token` field (schema variant `v1-legacy`). Migration ticket **ORD-552** was not done.
6. On 2.4.0, `card_token` is ignored as an unknown field, so the required field `payment_method_token` is missing → payment-service returns **HTTP 422** with application error **PAY-401** ("Request validation failed").
7. order-service's **subscription-renewal** flow already sends `payment_method_token` (variant `v2`) and keeps working.
8. order-service retries every 422 three times, which multiplies failing calls and raises order-service payment-call latency to about 1.4–1.5 s (p50/p95). payment-service itself does NOT get slower.

**Status of the root cause in the evidence:**
- *Confirmed:* legacy `card_token` requests fail on 2.4.0 and pass on 2.3.1 (logs, payment_requests, staging reproduction in handover, recovery after rollback).
- *Inferred (strong, not formally confirmed):* the mechanism is the schemaguard 3.0 alias default. Needs WEB-001 + DOC-004 + DOC-002 + REC-001. The handover says the `allow_aliases: true` fix has **not yet been tested**.

## 3. Timeline (UTC, 2026-10-23)

| Time | Event | Main sources |
|---|---|---|
| 09:30–09:34 | Go/no-go meeting for 2.4.0 | TRN-001 |
| 09:47:05 | Unrelated single PAY-504 processor timeout (background noise) | REC-001 LOG-0004 |
| 10:02:00 | Deploy started, payment-service 2.3.1 → 2.4.0, production | REC-003 EVT-001 |
| 10:03:10 | 2.4.0 instance starts; logs `validator=schemaguard 3.0.1` | REC-001 LOG-0007 |
| 10:04:30 | Deploy completed, status succeeded | REC-003 EVT-002 |
| 10:05:00 | Post-deploy health check passed | REC-003 EVT-003 |
| 10:05:12 | First PAY-401 | REC-001 LOG-0009 |
| 10:09:00 | Alert: payment failure rate above 5 % | REC-003 EVT-004 |
| 10:11:47 | Error captured in screenshot (trc-5a10c4) | IMG-002 |
| 10:15:00 | Incident INC-2026-1042 opened | REC-003 EVT-005 |
| 10:18 | Initial report written (wrongly suspects credentials) | DOC-005 |
| 10:20–10:44 | Incident call; competing hypotheses | TRN-002 |
| 11:10:00 | Rollback started 2.4.0 → 2.3.1 | REC-003 EVT-006 |
| 11:13:40 | Rollback completed | REC-003 EVT-007 |
| 11:15 onward | Error rate back to ~0 % | REC-002 |
| 12:00 | Handover to evening on-call | TRN-003 |

## 4. Expected vs observed behaviour

| | Expected (DOC-002 spec v2.0) | Observed on 2.4.0 |
|---|---|---|
| Request with `card_token` | Accepted (deprecated alias) | Rejected, HTTP 422, PAY-401 |
| Request with `payment_method_token` | Accepted | Accepted (HTTP 201) |
| PAY-401 meaning | Request validation failed (HTTP 422) | Same |

## 5. Numbers (per 5-minute bucket, approximate)

- Orders needing payment: ~600 per bucket. Checkout (v1-legacy) ≈ 78 %, renewal (v2) ≈ 22 %.
- After deploy: order-level failure ≈ 78 %. payment-service attempt-level error rate ≈ 93 % (because each failed order makes 4 attempts).
- order-service payment-call p95: ~230 ms before → ~1,490 ms during → back to ~230 ms after.
- payment-service p95: ~180 ms before → ~140 ms during (rejections are fast).

## 6. Intentional contradictions

1. DOC-002 says `card_token` is accepted until 2027-03-31; observed behaviour on 2.4.0 rejects it.
2. DOC-004 says "no breaking changes to the public payment API are expected"; observed behaviour breaks legacy clients.
3. DOC-005 suspects an authentication / credential problem (reading PAY-401 as HTTP 401). DOC-002 maps PAY-401 to HTTP 422; logs show 422; TRN-002 says no secret rotation since 2026-10-09.
4. TRN-001: Arjun believes "aliases still work" in 2.4.0; WEB-001 says aliases are off by default in schemaguard 3.0.

## 7. Competing hypotheses (in TRN-002)

- H1 Credential / API-key problem — rejected (status 422 not 401; no rotation).
- H2 Redis / database slowness — not supported (payment-service latency fell; Redis flat per verbal check).
- H3 Request schema mismatch (legacy `card_token`) — supported.
- Side argument: whose fault (order-service late migration vs payment-service breaking the alias) — not settled.

## 8. Unknown facts (deliberately absent)

- Who approved the 2.4.0 production deploy (no approval record).
- Exact number of unique customers affected.
- Revenue / monetary loss.
- What payload the staging smoke suite sends (never checked).
- Whether `allow_aliases: true` alone fixes the issue (not tested).
- Full contents of the payment-service 2.4.0 config file.
- The exact cause of the 09:47 PAY-504 timeout.

## 9. Evidence needed for each conclusion

| Conclusion | Evidence |
|---|---|
| Failures started after 2.4.0 deploy | REC-003 EVT-001/002, REC-001 LOG-0009, REC-002 rows, IMG-001, IMG-004 |
| Only legacy `card_token` requests fail | REC-004, REC-001 |
| PAY-401 is a validation error, not auth | DOC-002 §5, REC-001, IMG-002, WEB-003 |
| 2.4.0 changed the validator | DOC-004, REC-001 LOG-0007 |
| schemaguard 3.0 turned aliases off | WEB-001 |
| Spec promised alias support | DOC-002 §4 |
| Latency rise caused by retries | DOC-001 §4, REC-002, REC-001 retry logs |
| Rollback restored service | REC-003 EVT-006/007, REC-002, REC-004 |
