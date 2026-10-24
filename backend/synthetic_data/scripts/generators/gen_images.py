"""Generate the four PNG evidence images from the structured records (synthetic)."""
import csv, json
from datetime import datetime
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageDraw, ImageFont

RAW = Path(__file__).resolve().parents[2] / "dataset" / "raw"
IMG = RAW / "images"
P = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
rows = list(csv.DictReader(open(RAW / "structured" / "metrics.csv")))
events = json.load(open(RAW / "structured" / "deployment_events.json"))["events"]
EV = {e["event_type"]: P(e["timestamp"]) for e in events}

# ---------- IMG-001 monitoring_dashboard.png ----------
def series(svc, col):
    r = [x for x in rows if x["service"] == svc]
    return [P(x["timestamp"]) for x in r], [float(x[col]) for x in r]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 7.5), sharex=True)
fig.suptitle("ShopSphere Payments Dashboard - 2026-10-23 (UTC, 5-minute buckets) - SYNTHETIC", fontsize=13)
for svc, lbl, st in [("payment-service", "payment-service: failed payment attempts (%)", "-"),
                     ("order-service", "order-service: orders with failed payment (%)", "--")]:
    x, y = series(svc, "error_rate_pct"); a1.plot(x, y, st, marker="o", ms=3, label=lbl)
a1.set_ylabel("Failure rate (%)"); a1.set_ylim(0, 100); a1.axhline(5, color="grey", lw=0.8, ls=":")
a1.text(P("2026-10-23T09:31:00Z"), 7, "alert threshold 5%", fontsize=8, color="grey")
for svc, lbl, st in [("payment-service", "payment-service p95 latency (ms)", "-"),
                     ("order-service", "order-service p95 payment-call latency (ms)", "--")]:
    x, y = series(svc, "latency_p95_ms"); a2.plot(x, y, st, marker="o", ms=3, label=lbl)
a2.set_ylabel("p95 latency (ms)"); a2.set_ylim(0, 1800)
for ax in (a1, a2):
    ax.axvline(EV["deploy_started"], color="red", lw=1.2)
    ax.axvline(EV["rollback_started"], color="green", lw=1.2)
    ax.grid(alpha=0.3); ax.legend(loc="upper right", fontsize=8)
a1.text(EV["deploy_started"], 102, " Deploy 2.4.0 (10:02)", color="red", fontsize=9)
a1.text(EV["rollback_started"], 102, " Rollback to 2.3.1 (11:10)", color="green", fontsize=9)
a2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M")); a2.set_xlabel("Time (UTC)")
fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(IMG / "monitoring_dashboard.png", dpi=110); plt.close(fig)

# ---------- IMG-002 payment_error_screenshot.png ----------
W, H = 1100, 560
im = Image.new("RGB", (W, H), "#1e1f24"); d = ImageDraw.Draw(im)
mono = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 17)
bold = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
d.rectangle([0, 0, W, 44], fill="#2d2f36")
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]): d.ellipse([16 + i * 26, 14, 32 + i * 26, 30], fill=c)
d.text((110, 12), "order-service debug console  |  production  |  SYNTHETIC DATA", font=bold, fill="#d0d0d0")
lines = [("#8ab4f8", "2026-10-23T10:11:47.203Z  request req-1107  (order ORD-88251)"),
         ("#d0d0d0", "> POST http://payment-service/v2/payments"),
         ("#d0d0d0", "> Content-Type: application/json"),
         ("#d0d0d0", "> Idempotency-Key: idem-ORD-88251"),
         ("#d0d0d0", ""),
         ("#ff6b6b", "< HTTP/1.1 422 Unprocessable Entity"),
         ("#d0d0d0", "< Content-Type: application/json"),
         ("#d0d0d0", "<"),
         ("#e6db74", "{"),
         ("#e6db74", '  "error_code": "PAY-401",'),
         ("#e6db74", '  "message": "Request validation failed",'),
         ("#e6db74", '  "trace_id": "trc-5a10c4"'),
         ("#e6db74", "}"),
         ("#d0d0d0", ""),
         ("#9aa0a6", "retry 1 of 3 scheduled in 200 ms ...  (request body hidden by console privacy setting)")]
for i, (c, s) in enumerate(lines): d.text((24, 66 + i * 30), s, font=mono, fill=c)
im.save(IMG / "payment_error_screenshot.png")

# ---------- IMG-003 service_architecture_diagram.png ----------
deps = json.load(open(RAW / "structured" / "service_dependencies.json"))
pos = {"api-gateway": (1.6, 5.0), "order-service": (5.2, 5.0), "inventory-service": (9.2, 6.4),
       "payment-service": (9.2, 2.6), "postgres": (12.8, 4.6), "redis": (5.2, 1.0)}
ver = {s["name"]: s["version"] for s in deps["services"]}
fig, ax = plt.subplots(figsize=(14, 7)); ax.set_xlim(0, 14.4); ax.set_ylim(0, 7.4); ax.axis("off")
ax.set_title("ShopSphere Service Architecture (arrow = caller to callee) - SYNTHETIC", fontsize=13)
BW, BH = 2.7, 0.95
def clip(a, b):
    (x1, y1), (x2, y2) = a, b; dx, dy = x2 - x1, y2 - y1
    k = min((BW / 2 + 0.08) / abs(dx) if dx else 9e9, (BH / 2 + 0.08) / abs(dy) if dy else 9e9)
    return x1 + dx * k, y1 + dy * k
for n, (x, y) in pos.items():
    fc = "#fde2c8" if n in ("postgres", "redis") else "#d6e4f5"
    ax.add_patch(FancyBboxPatch((x - BW / 2, y - BH / 2), BW, BH, boxstyle="round,pad=0.05", fc=fc, ec="#333"))
    sub = "v2.3.1 (ran 2.4.0 10:04-11:13 UTC)" if n == "payment-service" else f"v{ver[n]}"
    ax.text(x, y + 0.1, n, ha="center", fontsize=11, weight="bold"); ax.text(x, y - 0.27, sub, ha="center", fontsize=8)
for dep in deps["dependencies"]:
    a, b = pos[dep["upstream"]], pos[dep["downstream"]]
    ax.annotate("", xy=clip(b, a), xytext=clip(a, b), arrowprops=dict(arrowstyle="->", lw=1.3, color="#444"))
    lbl = dep["purpose"] + (" (3 retries)" if "retry_policy" in dep else "")
    ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + (0.72 if dep["dependency_id"] == "DEP-01" else 0.15), lbl, ha="center", fontsize=8, color="#222",
            bbox=dict(fc="white", ec="none", alpha=0.85))
ax.text(0.2, 0.3, "Blue = service, orange = data store. Labels show dependency purpose.", fontsize=8, color="#555")
fig.savefig(IMG / "service_architecture_diagram.png", dpi=110, bbox_inches="tight"); plt.close(fig)

# ---------- IMG-004 deployment_timeline.png ----------
items = [(EV["deploy_started"], "10:02:00 Deploy started 2.3.1 -> 2.4.0", "red"),
         (EV["deploy_completed"], "10:04:30 Deploy completed", "red"),
         (P("2026-10-23T10:05:12Z"), "10:05:12 First PAY-401 error", "black"),
         (EV["alert_triggered"], "10:09:00 Alert PaymentFailureRateHigh", "darkorange"),
         (EV["incident_opened"], "10:15:00 Incident INC-2026-1042 opened", "purple"),
         (EV["rollback_started"], "11:10:00 Rollback started 2.4.0 -> 2.3.1", "green"),
         (EV["rollback_completed"], "11:13:40 Rollback completed", "green"),
         (EV["alert_resolved"], "11:30:00 Alert resolved", "darkorange")]
fig, ax = plt.subplots(figsize=(13, 5.4))
ax.axhline(0, color="#555", lw=2)
for i, (t_, lbl, c) in enumerate(items):
    h = [1.9, 1.2, -0.8, -1.5, -2.2, 1.6, -0.9, -1.6][i]
    ax.plot([t_, t_], [0, h], color=c, lw=1); ax.plot(t_, 0, "o", color=c)
    ax.text(t_, h + (0.08 if h > 0 else -0.25), lbl, fontsize=8.5, color=c, ha="left")
ax.set_ylim(-2.8, 2.5); ax.set_yticks([])
ax.set_xlim(P("2026-10-23T09:55:00Z"), P("2026-10-23T11:45:00Z"))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M")); ax.set_xlabel("Time (UTC), 2026-10-23")
ax.set_title("payment-service Deployment Timeline - production - SYNTHETIC", fontsize=12)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
fig.tight_layout(); fig.savefig(IMG / "deployment_timeline.png", dpi=110); plt.close(fig)
print("images ok")
