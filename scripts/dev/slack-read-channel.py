#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# (born under github_actions_ci_cost_reduction_2026_07_15; general-purpose thereafter)
# Recurring triage tool. The operator directed reading Slack directly
#   ("you can directly check the slack channels yourself... use that token", 2026-07-17).
# Why this exists: read-only download of a Slack channel's recent history so alert triage
#   ("is something broken?") can be done from a terminal, with the raw JSON kept locally for
#   grep/re-analysis. Re-run it fresh each time — its answer has a date on it.
#
# Auth: GCP Secret Manager `SLACK_ALERTS_READER_BOT_TOKEN` (bot must be a member of the
#   channel). The token never touches disk or argv — resolved in-process.
#   Pinned to a specific identity, not "whichever account happens to be ambient" (2026-08-11
#   hardening — see /codex/05-infrastructure/agent-slack-read-access.md): tries, in order,
#   (1) `--account=unified-trading-sa@<active-gcloud-project>.iam.gserviceaccount.com` — a real,
#   directly-authenticated local credential on every host this matters on (AO's `ubuntu` worker
#   user; the operator's laptop, via a service-account key activated 2026-08-11 specifically to
#   dodge the org's human-reauth policy, which blocks plain ADC non-interactively); (2) plain
#   ambient `gcloud` default, for any host that hasn't been migrated to the pinned account yet;
#   (3) the `SLACK_ALERTS_READER_BOT_TOKEN` env var, for the case every gcloud path fails (no
#   gcloud binary, `PERMISSION_DENIED` on `secretmanager.versions.access`, or a stale-token
#   reauth prompt that can't run non-interactively — confirmed 2026-07-24,
#   plan_health_tests_leak_real_slack_alerts_2026_07_24.md). Ambient ADC alone was the ORIGINAL
#   design and is deliberately no longer the primary path: on a multi-account host (the AO VM's
#   `ubuntu` user has 5+ configured accounts across per-slot configs) "whichever one is active"
#   can silently change out from under a scheduled job if any interactive session on that same
#   OS user runs `gcloud config set account`/`gcloud auth login` — pinning removes that
#   footgun.
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
#   Degraded-path auth: SLACK_ALERTS_READER_BOT_TOKEN=<token> python3 slack-read-channel.py ...
import json
import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request

args = [a for a in sys.argv[1:] if not a.startswith("--")]
CHANNEL = args[0] if len(args) > 0 else "ci-failures"
HOURS = float(args[1]) if len(args) > 1 else 24.0
JSON_ONLY = "--json-only" in sys.argv

# Pinned identity first (see header): a real, directly-authenticated service-account
# credential every migrated host already carries, so a scheduled job's Slack-read can't be
# silently broken by an unrelated interactive session switching the ambient gcloud account.
# Project comes from the active gcloud config (never hardcoded — same rule the original ambient
# call always followed; only the ACCOUNT is pinned, not the project).
_PINNED_SA_ACCOUNT_NAME = "unified-trading-sa"


def _pinned_sa_email() -> str | None:
    try:
        project = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return f"{_PINNED_SA_ACCOUNT_NAME}@{project}.iam.gserviceaccount.com" if project else None


def _try_gcloud(extra_args: list[str]) -> str | None:
    base_args = ["gcloud", "secrets", "versions", "access", "latest", "--secret=SLACK_ALERTS_READER_BOT_TOKEN"]
    try:
        return subprocess.run(
            [*base_args, *extra_args],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


_pinned_email = _pinned_sa_email()
tok = _try_gcloud([f"--account={_pinned_email}"]) if _pinned_email else None
if tok is None:
    # Pinned account not locally configured on this host yet (or project unresolved) — fall
    # back to whatever's ambient.
    tok = _try_gcloud([])
if tok is None:
    # Degraded path: every gcloud path failed (no gcloud binary, PERMISSION_DENIED on
    # secretmanager.versions.access, or a stale-token reauth prompt that can't run
    # non-interactively). Never silently substitute an empty string — an env var is the
    # documented secondary source, never a default.
    tok = os.environ.get("SLACK_ALERTS_READER_BOT_TOKEN", "")  # noqa: qg-empty-fallback — env var legitimately absent; checked via `if not tok` immediately below
    if not tok:
        sys.exit(
            f"gcloud failed to resolve SLACK_ALERTS_READER_BOT_TOKEN as both {_pinned_email!r} and the "
            "ambient default account, and no SLACK_ALERTS_READER_BOT_TOKEN env var is set as a "
            "fallback. Either activate the pinned SA locally (see "
            "/codex/05-infrastructure/agent-slack-read-access.md), fix ambient gcloud auth, or "
            "supply the token directly: "
            "SLACK_ALERTS_READER_BOT_TOKEN=<token> python3 scripts/dev/slack-read-channel.py ..."
        )


def api(method: str, **params):
    req = urllib.request.Request(
        f"https://slack.com/api/{method}?{urllib.parse.urlencode(params)}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:  # nosec B310 — scheme is fixed https
        data = json.load(r)
    if not data.get("ok"):
        sys.exit(f"Slack API {method} error: {data.get('error')}")
    return data


chans, cursor = {}, ""
while True:
    d = api("conversations.list", limit=200, types="public_channel,private_channel", cursor=cursor)
    chans.update({c["name"]: c["id"] for c in d["channels"]})
    cursor = (d.get("response_metadata") or {}).get("next_cursor") or ""
    if not cursor:
        break
if CHANNEL not in chans:
    sys.exit(f"channel {CHANNEL!r} not visible to the reader bot; visible: {', '.join(sorted(chans))}")

oldest = time.time() - HOURS * 3600
msgs, cursor = [], ""
while True:
    d = api("conversations.history", channel=chans[CHANNEL], oldest=f"{oldest:.6f}", limit=200, cursor=cursor)
    msgs.extend(d["messages"])
    if not d.get("has_more"):
        break
    cursor = (d.get("response_metadata") or {}).get("next_cursor") or ""
msgs.sort(key=lambda m: float(m["ts"]))

out = f"slack-{CHANNEL}-{int(HOURS)}h.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(msgs, f, indent=2, ensure_ascii=False)
print(f"{len(msgs)} messages -> {out}", file=sys.stderr)
if JSON_ONLY:
    sys.exit(0)


def render(m) -> str:
    parts = []
    for b in m.get("blocks") or []:
        if b.get("type") == "section":
            t = b.get("text") or {}
            if t.get("text"):
                parts.append(t["text"])
            parts.extend(f["text"] for f in b.get("fields") or [] if f.get("text"))
        elif b.get("type") == "context":
            parts.extend(e["text"] for e in b.get("elements") or [] if e.get("text"))
    if not parts:
        parts = [m.get("text") or ""] + [a.get("text") or a.get("fallback") or "" for a in m.get("attachments") or []]
    return " ⏐ ".join(" ".join(p.split()) for p in parts if p.strip())


for m in msgs:
    ts = time.strftime("%m-%d %H:%M", time.gmtime(float(m["ts"])))
    print(f"{ts}Z | {render(m)[:400]}")
