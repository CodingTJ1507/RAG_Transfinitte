"""Generate WebVTT transcripts and the handover note (synthetic)."""
from pathlib import Path
OUT = Path(__file__).resolve().parents[2] / "dataset" / "raw" / "transcripts"

def t(s):
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}.000"

def vtt(name, note, cues):
    lines = ["WEBVTT", "", "NOTE", *note, ""]
    for i, (start, dur, spk, text) in enumerate(cues, 1):
        lines += [f"cue-{i:03d}", f"{t(start)} --> {t(start + dur)}", f"<v {spk}>{text}", ""]
    (OUT / name).write_text("\n".join(lines))

vtt("deployment_meeting.vtt", [
    "Meeting: payment-service 2.4.0 go/no-go",
    "Recording start: 2026-10-23T09:30:00Z (cue times are offsets from this start)",
    "Participants: Maya Chen (release manager), Arjun Rao (payment-service developer),",
    "Lena Fischer (order-service developer), Tom Okafor (on-call SRE)",
    "Fictional people and synthetic content."], [
    (5, 14, "Maya Chen", "This is the go/no-go for payment-service 2.4.0. The plan is to start the deploy at 10:02."),
    (21, 25, "Arjun Rao", "It is a maintenance release. The main change is the schemaguard upgrade from 2.8.4 to 3.0.1, plus better error messages and a new metric. No database migrations."),
    (48, 6, "Tom Okafor", "Any change to the API that clients see?"),
    (55, 22, "Arjun Rao", "No. The public API stays the same. Old field aliases still work, so nothing should change for clients."),
    (80, 20, "Lena Fischer", "Just flagging: the order-service checkout flow still sends card_token. Moving it to payment_method_token is ticket ORD-552, planned for next sprint. The renewal flow already uses payment_method_token."),
    (101, 18, "Arjun Rao", "That is fine. card_token is a supported alias until March 2027 according to the spec."),
    (123, 10, "Tom Okafor", "Did the staging smoke tests cover the checkout flow?"),
    (135, 17, "Arjun Rao", "Smoke tests passed. I think the suite uses the renewal payload, but I have not checked."),
    (154, 6, "Tom Okafor", "Can we check that before we deploy?"),
    (161, 15, "Maya Chen", "We are short on time. Arjun, can you look at it afterwards? Let's not block on it."),
    (178, 20, "Maya Chen", "Plan: deploy at 10:02, Tom watches the dashboard for 15 minutes, and we roll back by the runbook if needed."),
    (200, 8, "Tom Okafor", "OK. I will be watching the payment dashboard."),
])

vtt("incident_discussion.vtt", [
    "Meeting: INC-2026-1042 incident call",
    "Recording start: 2026-10-23T10:20:00Z (cue times are offsets from this start)",
    "Participants: Tom Okafor (incident commander), Priya Nair (platform engineer),",
    "Arjun Rao (payment-service developer), Lena Fischer (order-service developer), Maya Chen (release manager)",
    "Fictional people and synthetic content."], [
    (4, 15, "Tom Okafor", "Let's start. Payments have been failing since about 10:05. The alert fired at 10:09. Priya's first report suspects a credential problem."),
    (20, 14, "Priya Nair", "Yes. PAY-401 sounded like unauthorized, so I guessed an expired or rotated API key."),
    (35, 16, "Priya Nair", "Update: I checked the secret store. The order-service key was last rotated on October 9. Nothing changed today."),
    (52, 17, "Arjun Rao", "Also, the HTTP status on these errors is 422, not 401. In our spec PAY-401 means request validation failed. The code name is confusing."),
    (70, 16, "Priya Nair", "OK, then credentials are probably not it. I would still keep it open until we know more."),
    (88, 16, "Tom Okafor", "Second idea: is something slow in redis or postgres? The order-service p95 jumped to about one and a half seconds."),
    (105, 18, "Tom Okafor", "I'm looking at the infra dashboard now. Redis p95 is flat at around 2 milliseconds and postgres looks normal."),
    (125, 24, "Lena Fischer", "The latency is on our side. order-service retries any non-2xx three times, with 200, 400 and 800 millisecond waits. That is about 1.4 seconds per failed order. payment-service itself got faster, because rejections are quick."),
    (150, 24, "Arjun Rao", "The payment-service logs say: required field payment_method_token is missing, unrecognized field card_token ignored. So checkout requests that send card_token fail. Renewal requests pass."),
    (175, 14, "Lena Fischer", "But the spec says card_token is an alias until 2027. So 2.4.0 broke the contract."),
    (190, 11, "Arjun Rao", "Or checkout should have moved months ago. ORD-552 has been open since August."),
    (202, 12, "Tom Okafor", "We are not deciding blame now. What changed in 2.4.0 that could touch aliases?"),
    (215, 14, "Arjun Rao", "Really only the schemaguard upgrade. I don't know yet if 3.0 changed how aliases work. I'll read their changelog."),
    (230, 7, "Maya Chen", "Could it be a difference in the config file?"),
    (238, 9, "Arjun Rao", "Possibly. I have not compared the configs yet."),
    (250, 28, "Tom Okafor", "Actions. Arjun: reproduce in staging with a card_token body. Lena: confirm from the request records which flows fail. Decision: if checkout is still failing at 11:00 we roll back. The release notes say no database migrations, so rollback should be safe."),
    (280, 7, "Lena Fischer", "I would rather roll back now."),
    (288, 10, "Tom Okafor", "Understood. We give Arjun until 11:00. Next update in the incident channel."),
])

(OUT / "engineering_handover.txt").write_text("""INCIDENT HANDOVER NOTE - INC-2026-1042
Fictional people and synthetic content.

From:    Tom Okafor (day on-call, incident commander)
To:      Sam Weber (evening on-call)
Written: 2026-10-23 12:00 UTC

STATUS
Mitigated. payment-service rolled back from 2.4.0 to 2.3.1. I approved the rollback as
incident commander at about 11:05 UTC. Rollback started 11:10 and finished 11:13:40.
Payment failure rate has been about 0% since 11:15. Alert resolved at 11:30.

VERIFIED
- Failures started at 10:05:12 UTC, right after the 2.4.0 rollout (10:02 to 10:04:30).
- Only checkout requests that send card_token failed (HTTP 422, PAY-401).
  Renewal requests that send payment_method_token kept working.
  Lena confirmed this from the payment request records.
- Staging reproduction by Arjun at 10:52 UTC: a checkout body with card_token returns
  422 / PAY-401 on 2.4.0. The same body returns 201 on 2.3.1.
- No credential rotation since 2026-10-09 (Priya checked the secret store).

NOT VERIFIED / STILL OPEN
- Arjun thinks schemaguard 3.0 stopped resolving field aliases by default
  (setting allow_aliases). This matches the schemaguard changelog, but nobody has
  tested 2.4.0 with allow_aliases: true yet. We have not compared the full 2.4.0 config.
- Why the staging smoke tests did not catch this. Nobody has checked which payload
  the smoke suite sends.
- Number of affected customers and lost revenue. Not calculated. Finance not involved yet.
- No formal sign-off was recorded for the 2.4.0 deploy, and I could not find an
  approval record on pipeline run PIPE-7781.

NEXT STEPS
1. Do NOT redeploy 2.4.0 until a fix is tested.
2. Payments team: test 2.4.0 with allow_aliases: true in staging.
3. Orders team: finish ORD-552 (checkout sends payment_method_token).
4. Idea from Lena, not agreed yet: order-service should not retry 4xx responses.
5. Postmortem booked for 2026-10-26.
""")
print("transcripts ok")
