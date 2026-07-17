#!/usr/bin/env python3
# Epic: github_actions_ci_cost_reduction_2026_07_15 (born there; general-purpose thereafter)
# Lifecycle: KEEP — recurring triage tool. The operator directed reading Slack directly
#   ("you can directly check the slack channels yourself... use that token", 2026-07-17).
# Why this exists: read-only download of a Slack channel's recent history so alert triage
#   ("is something broken?") can be done from a terminal, with the raw JSON kept locally for
#   grep/re-analysis. Re-run it fresh each time — its answer has a date on it.
#
# Auth: GCP Secret Manager `SLACK_ALERTS_READER_BOT_TOKEN` (bot must be a member of the
#   channel). The token never touches disk or argv — resolved in-process via gcloud ADC.
#
# TRAPS learned building this (do not re-learn):
#   * Carrier posts (notify-slack.yml) put the REAL content in Block Kit `blocks`, not in
#     `text` — `text` holds only the ":x: CRITICAL — <workflow>" headline. Always render
#     blocks[].section.text/fields + context elements, and fall back to attachments.
#   * conversations.history is newest-first and paginates via response_metadata.next_cursor;
#     sort by ts after collecting.
#
# Usage: slack-read-channel.py [channel=ci-failures] [hours=24] [--json-only]
#   Raw dump: ./slack-<channel>-<hours>h.json in the CWD.
import json
import subprocess
import sys
import time
import urllib.parse
import urllib.request

args = [a for a in sys.argv[1:] if not a.startswith("--")]
CHANNEL = args[0] if len(args) > 0 else "ci-failures"
HOURS = float(args[1]) if len(args) > 1 else 24.0
JSON_ONLY = "--json-only" in sys.argv

tok = subprocess.run(
    [
        "gcloud",
        "secrets",
        "versions",
        "access",
        "latest",
        "--secret=SLACK_ALERTS_READER_BOT_TOKEN",
        "--project=central-element-323112",
    ],
    capture_output=True,
    text=True,
    check=True,
).stdout.strip()


def api(method: str, **params):
    req = urllib.request.Request(
        f"https://slack.com/api/{method}?{urllib.parse.urlencode(params)}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    if not data.get("ok"):
        sys.exit(f"Slack API {method} error: {data.get('error')}")
    return data


chans, cursor = {}, ""
while True:
    d = api("conversations.list", limit=200, types="public_channel,private_channel", cursor=cursor)
    chans.update({c["name"]: c["id"] for c in d.get("channels", [])})
    cursor = (d.get("response_metadata") or {}).get("next_cursor", "")
    if not cursor:
        break
if CHANNEL not in chans:
    sys.exit(f"channel {CHANNEL!r} not visible to the reader bot; visible: {', '.join(sorted(chans))}")

oldest = time.time() - HOURS * 3600
msgs, cursor = [], ""
while True:
    d = api("conversations.history", channel=chans[CHANNEL], oldest=f"{oldest:.6f}", limit=200, cursor=cursor)
    msgs.extend(d.get("messages", []))
    if not d.get("has_more"):
        break
    cursor = (d.get("response_metadata") or {}).get("next_cursor", "")
msgs.sort(key=lambda m: float(m["ts"]))

out = f"slack-{CHANNEL}-{int(HOURS)}h.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(msgs, f, indent=2, ensure_ascii=False)
print(f"{len(msgs)} messages -> {out}", file=sys.stderr)
if JSON_ONLY:
    sys.exit(0)


def render(m) -> str:
    parts = []
    for b in m.get("blocks", []) or []:
        if b.get("type") == "section":
            t = b.get("text") or {}
            if t.get("text"):
                parts.append(t["text"])
            parts.extend(f["text"] for f in b.get("fields", []) or [] if f.get("text"))
        elif b.get("type") == "context":
            parts.extend(e["text"] for e in b.get("elements", []) or [] if e.get("text"))
    if not parts:
        parts = [m.get("text") or ""] + [
            a.get("text") or a.get("fallback") or "" for a in m.get("attachments", []) or []
        ]
    return " ⏐ ".join(" ".join(p.split()) for p in parts if p.strip())


for m in msgs:
    ts = time.strftime("%m-%d %H:%M", time.gmtime(float(m["ts"])))
    print(f"{ts}Z | {render(m)[:400]}")
