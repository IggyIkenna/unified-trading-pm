#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# cron_liveness_watchdog.py — off-GHA dead-man's-switch for the GHA cron monitors.
#
# PROBLEM: every monitor in this repo (ci-health, branch-health, sit-debounce-trigger,
# ldr-ci-monitor) is ITSELF a GHA cron — so a GHA-wide
# outage (Actions billing wall, org-disable) silences the alarms too. This script
# runs OFF GitHub Actions on the always-up orchestrator VM (planning,
# i-0c9b283b31d6b5ca7, EIP 13.113.200.22) and alerts Slack when any watched cron's
# last successful run is older than its expected interval x STALE_MULTIPLIER.
#
# Install on the VM (idempotent):
#   bash scripts/dev/install-cron-liveness-watchdog.sh
#
# Run manually:
#   GH_TOKEN=<pat> SLACK_CI_WEBHOOK_URL=<url> python3 scripts/repo-management/cron_liveness_watchdog.py
#   python3 scripts/repo-management/cron_liveness_watchdog.py --dry-run
#
# Plan: L1583 (cicd_consolidated_remaining_2026_06_24.md)
# SSOT: codex/08-workflows/ci-cd-flow.md § "External liveness watchdog"

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import urllib.error
import urllib.request

ORG = "IggyIkenna"
PM_REPO = f"{ORG}/unified-trading-pm"

# How many interval-periods of silence trigger an alert. At 3x the interval, one cron
# can fail twice (e.g. Actions transient) before we page — balancing FP rate vs MTTD.
STALE_MULTIPLIER = 3

# Workflows watched by this DMS — the ones that must NOT go silently dark.
# interval_min MUST match the cron cadence in the workflow file (verified at write time).
# Sprawl-consolidation 2026-06-27:
#   ci-failure-watcher.yml → ci-health.yml (renamed)
#   sit-starvation-detector.yml → folded into sit-debounce-trigger.yml (deleted)
#   promotion-lag-monitor.yml → folded into branch-health.yml (deleted)
WATCHED_WORKFLOWS: list[dict[str, object]] = [
    {
        "workflow": "ci-health.yml",
        "label": "ci-health",
        "interval_min": 15,
    },
    {
        "workflow": "branch-health.yml",
        "label": "branch-health",
        "interval_min": 30,
    },
    {
        "workflow": "sit-debounce-trigger.yml",
        "label": "sit-debounce-trigger",
        "interval_min": 5,
    },
    {
        "workflow": "ldr-ci-monitor.yml",
        "label": "ldr-ci-monitor",
        "interval_min": 60,
    },
]


def _now_utc() -> _dt.datetime:
    return _dt.datetime.now(_dt.UTC)


def _parse_ts(s: str) -> _dt.datetime:
    # Replace trailing Z with +00:00 so fromisoformat() returns a tz-aware datetime
    # on all Python 3.x versions (3.11+ accepts Z directly; the replace() is safe everywhere).
    return _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))


def gh_json(args: list[str]) -> list[dict[str, object]] | dict[str, object] | None:
    try:
        proc = subprocess.run(
            ["gh", *args],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            return None
        return json.loads(proc.stdout)
    except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
        return None


def check_workflow_liveness(wf: dict[str, object], now: _dt.datetime) -> dict[str, object] | None:
    """Return a stale record if the workflow's last successful run is too old, else None."""
    label = wf["label"]
    workflow = wf["workflow"]
    interval_min = wf["interval_min"]
    staleness_threshold = interval_min * STALE_MULTIPLIER

    runs = gh_json(
        [
            "run",
            "list",
            "--repo",
            PM_REPO,
            "--workflow",
            workflow,
            "--status",
            "completed",
            "--limit",
            "10",
            "--json",
            "databaseId,conclusion,createdAt,updatedAt,url",
        ]
    )
    if runs is None:
        # gh error (could be network or token) — emit a diagnostic stale record so we know
        # the watchdog itself was partially degraded, rather than silently passing.
        return {
            "label": label,
            "workflow": workflow,
            "interval_min": interval_min,
            "age_min": None,
            "threshold_min": staleness_threshold,
            "url": "",
            "reason": "gh-api-error (could not list runs — check GH_TOKEN scope/rate limit)",
        }

    if not isinstance(runs, list):
        return {
            "label": label,
            "workflow": workflow,
            "interval_min": interval_min,
            "age_min": None,
            "threshold_min": staleness_threshold,
            "url": "",
            "reason": "gh-unexpected-response",
        }

    # Find the most recent successfully concluded run.
    last_success: dict[str, object] | None = None
    for r in runs:
        if not isinstance(r, dict):
            continue
        if r.get("conclusion") == "success":
            last_success = r
            break

    if last_success is None:
        return {
            "label": label,
            "workflow": workflow,
            "interval_min": interval_min,
            "age_min": None,
            "threshold_min": staleness_threshold,
            "url": "",
            "reason": f"no successful run found in last {len(runs)} completed run(s)",
        }

    ts_str = last_success.get("updatedAt") or last_success.get("createdAt") or ""
    if not ts_str:
        return {
            "label": label,
            "workflow": workflow,
            "interval_min": interval_min,
            "age_min": None,
            "threshold_min": staleness_threshold,
            "url": last_success.get("url") or "",
            "reason": "timestamp missing on last successful run",
        }

    try:
        ts = _parse_ts(ts_str)
    except ValueError:
        return None

    age_min = int((now - ts).total_seconds() / 60)
    if age_min < staleness_threshold:
        return None  # healthy

    return {
        "label": label,
        "workflow": workflow,
        "interval_min": interval_min,
        "age_min": age_min,
        "threshold_min": staleness_threshold,
        "url": last_success.get("url") or "",
        "reason": (
            f"last success {age_min}m ago (threshold {staleness_threshold}m = {interval_min}m x {STALE_MULTIPLIER})"
        ),
    }


def build_alert_message(stale: list[dict[str, object]]) -> str:
    lines = [
        ":rotating_light: *OFF-GHA CRON LIVENESS WATCHDOG — stale GHA monitor(s) detected.*",
        "One or more monitoring crons have not completed successfully within their expected window.",
        "Possible causes: GHA billing/spending-limit wall, org-level Actions disable, workflow error.",
        "IMMEDIATE CHECK: https://www.githubstatus.com/ + GitHub → Settings → Billing & plans.",
        "",
        f"*{len(stale)} stale cron(s):*",
    ]
    for s in stale:
        age_str = f"{s['age_min']}m ago" if s["age_min"] is not None else "unknown age"
        url_part = f" <{s['url']}|last run>" if s.get("url") else ""
        lines.append(f"  • `{s['label']}` (every {s['interval_min']}m) — last success: {age_str}{url_part}")
        lines.append(f"      ↳ {s['reason']}")
    return "\n".join(lines)


def post_slack(message: str, webhook_url: str, *, dry_run: bool = False) -> bool:
    """POST message to Slack incoming webhook. Returns True on success."""
    if dry_run:
        print("[dry-run] would POST to Slack:")
        print(message)
        return True
    payload = json.dumps({"text": message}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310 — webhook_url is always HTTPS (Slack), validated by caller env-check; no user-controlled schemes
            return resp.status == 200
    except urllib.error.URLError as exc:
        print(f"[cron-liveness-watchdog] Slack POST failed: {exc}")
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Off-GHA dead-man's-switch for GHA cron monitors (L1583)")
    parser.add_argument("--dry-run", action="store_true", help="Check liveness but do not POST to Slack")
    parser.add_argument(
        "--stale-multiplier",
        type=int,
        default=STALE_MULTIPLIER,
        help=f"Alert when last success is older than interval x N (default {STALE_MULTIPLIER})",
    )
    args = parser.parse_args()

    stale_multiplier = args.stale_multiplier
    now = _now_utc()

    stale: list[dict[str, object]] = []
    for wf in WATCHED_WORKFLOWS:
        wf_with_mult = dict(wf)
        result = check_workflow_liveness(wf_with_mult, now)
        if result is not None:
            # Override with runtime multiplier
            result["threshold_min"] = wf["interval_min"] * stale_multiplier
            stale.append(result)
        else:
            print(f"[ok] {wf['label']}: healthy (last success within {wf['interval_min'] * stale_multiplier}m)")

    if not stale:
        print("[cron-liveness-watchdog] all monitored crons healthy — no alert.")
        return 0

    message = build_alert_message(stale)
    print(f"[cron-liveness-watchdog] ALERT — {len(stale)} stale cron(s):\n{message}")

    webhook_url = os.environ.get("SLACK_CI_WEBHOOK_URL") or os.environ.get("SLACK_WEBHOOK_URL") or ""
    if not webhook_url:
        print("[cron-liveness-watchdog] no SLACK_CI_WEBHOOK_URL set — printed alert above but did NOT post to Slack.")
        if not args.dry_run:
            return 1  # non-zero so cron log shows failure when unconfigured
        return 0

    ok = post_slack(message, webhook_url, dry_run=args.dry_run)
    if not ok and not args.dry_run:
        print("[cron-liveness-watchdog] Slack POST failed.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
