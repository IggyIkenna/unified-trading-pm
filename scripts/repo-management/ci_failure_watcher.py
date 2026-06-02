#!/usr/bin/env python3
"""Cross-repo CI failure → recovery transition watcher + auto-merge-stuck PR poller.

Antidote to the silent-rot that hid the whole CI/CD promotion breakage for months
(see plans/active/cicd_contract_hardening_2026_06_01.md § "Ordered unified backlog").

Two independent detectors, both STATELESS (no persisted state file — we derive
transitions from GitHub's own run history, and PR-stuck from live PR state):

1. Workflow transition alerts. For every repo in the canonical fleet list, on every
   watched branch, for EVERY workflow (not just Quality Gates), compare the two most
   recent COMPLETED runs:
     - success/none  -> failure   ==>  "started failing"   (CRITICAL)
     - failure       -> success   ==>  "recovered"         (INFO)
   Steady-state failures (failure -> failure) are NOT re-alerted — only transitions,
   to keep the channel signal-dense.

2. Auto-merge-stuck poller. Auto-merge-stuck is a *PR state*, not a `workflow_run`
   failure, so the transition detector alone misses it. We list open PRs into the
   integration/promotion branches and flag any that have sat CONFLICTING / DIRTY /
   BLOCKED longer than --stuck-minutes.

The wrapping workflow (.github/workflows/ci-failure-watcher.yml) reads the `alert`
and `report` GITHUB_OUTPUT values and fans out to notify-slack.yml (#ci-failures).
Exit code is always 0 — alerting is driven by the `alert` output, never by exit
status, so a transient gh hiccup never silently fails the watcher itself.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import subprocess
import sys

# Reuse the canonical fleet list so this stays in lock-step with the rulesets
# (pin_branch_protection_rulesets.py is the SSOT for which repos carry gates).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pin_branch_protection_rulesets import ORG, REPOS

# ── Push-author attribution ────────────────────────────────────────────────────
# Operator-approved 2026-06-02 (cicd_contract_hardening_2026_06_01.md line ~264).
#
# Classification rule (pure function over author/committer/message — testable without network):
#   automation  = committer is "github-actions[bot]" or "GitHub"
#   background-agent = commit message contains "Co-Authored-By: Claude"
#   human       = author name in {iggyikenna, cosmictrader} (case-insensitive)
#   unknown     = anything else
#
# The gh-api call is cached per sha so each sha is looked up at most once per run.
# Safe default: ("unknown", "unknown") on any error — NEVER raises, NEVER fails the watcher.

_HUMAN_NAMES = {"iggyikenna", "cosmictrader"}
_AUTOMATION_COMMITTERS = {"github-actions[bot]", "github"}

_commit_cache: dict[str, tuple[str, str]] = {}


def _classify_commit_data(author: str, committer: str, message: str) -> tuple[str, str]:
    """Classify a commit's pusher from raw git metadata.

    Pure function — testable without network calls.

    Returns:
        (name, role) where role is one of: "human", "background-agent", "automation", "unknown"
    """
    committer_lc = committer.strip().lower()
    author_lc = author.strip().lower()

    if committer_lc in _AUTOMATION_COMMITTERS:
        return (author.strip() or committer.strip(), "automation")

    if "co-authored-by: claude" in message.lower():
        return (author.strip() or "agent", "background-agent")

    if author_lc in _HUMAN_NAMES:
        return (author.strip(), "human")

    return (author.strip() or "unknown", "unknown")


def classify_pusher(repo: str, sha: str) -> tuple[str, str]:
    """Look up commit metadata from GitHub and classify the pusher.

    Returns:
        (name, role) — safe default ("unknown", "unknown") on any gh/network error.

    Caches results per sha so multiple alert lines for the same commit share one API call.
    """
    if not sha:
        return ("unknown", "unknown")
    cache_key = f"{repo}:{sha}"
    if cache_key in _commit_cache:
        return _commit_cache[cache_key]

    result = gh_json(
        [
            "api",
            f"repos/{ORG}/{repo}/commits/{sha}",
            "--jq",
            "{author:.commit.author.name,committer:.commit.committer.name,message:.commit.message}",
        ]
    )
    if not isinstance(result, dict):
        _commit_cache[cache_key] = ("unknown", "unknown")
        return ("unknown", "unknown")

    author = result.get("author") or ""
    committer = result.get("committer") or ""
    message = result.get("message") or ""
    classified = _classify_commit_data(author, committer, message)
    _commit_cache[cache_key] = classified
    return classified


# Branches where remote CI actually runs. live-defi-rollout has NO remote CI
# (CLAUDE.md § "CI Verification After Every Push") so watching it is pointless.
WATCHED_BRANCHES = ["main", "staging"]

# Bases that promotion PRs target — used by the auto-merge-stuck poller.
PROMOTION_BASES = ["staging", "main"]

_FAIL_CONCLUSIONS = {"failure", "startup_failure", "timed_out"}
_STUCK_STATES = {"CONFLICTING", "DIRTY", "BLOCKED"}

# Heads that are part of the promotion contract (LDR -> staging -> main). A stuck PR
# off one of these is a wedged promotion even without auto-merge enabled. Random stale
# feature/chore branches are NOT paged unless they have auto-merge ON (the plan's core
# "auto-merge-stuck is a PR state" case) — otherwise the channel fills with abandoned PRs.
_PROMOTION_HEADS = {"live-defi-rollout", "staging"}


def gh_json(args: list[str]) -> list[dict] | dict | None:
    """Run a gh command expecting JSON on stdout; return parsed value or None."""
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        print(f"  ! gh {' '.join(args)} -> rc={proc.returncode}: {proc.stderr.strip()[:200]}", file=sys.stderr)
        return None
    out = proc.stdout.strip()
    if not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        print(f"  ! JSON parse failed for gh {' '.join(args)}: {exc}", file=sys.stderr)
        return None


def _parse_ts(value: str) -> _dt.datetime:
    # GitHub timestamps are RFC3339 with a trailing Z.
    return _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


def detect_transitions(repo: str, branch: str, limit: int, now: _dt.datetime, fresh_hours: float) -> list[dict]:
    """Return one transition record per workflow that just flipped state on `branch`.

    Only flips whose *latest* run is within `fresh_hours` count: the detector is
    stateless (it reads run history, not a saved cursor), so without a recency guard
    a workflow that last ran months ago and failed would re-page on EVERY poll forever.
    Bounding to recent runs means a genuine new failure pages once (the poll right after
    it happens) then goes quiet, and ancient dead workflows never page at all.
    """
    fresh_cutoff = now - _dt.timedelta(hours=fresh_hours)
    runs = gh_json(
        [
            "run",
            "list",
            "--repo",
            f"{ORG}/{repo}",
            "--branch",
            branch,
            "--limit",
            str(limit),
            "--json",
            "workflowName,conclusion,status,createdAt,url,databaseId,event,headSha",
        ]
    )
    if not isinstance(runs, list):
        return []

    by_workflow: dict[str, list[dict]] = {}
    for run in runs:
        if run.get("status") != "completed":
            continue  # ignore in-flight runs; only completed runs have a conclusion
        by_workflow.setdefault(run["workflowName"], []).append(run)

    transitions: list[dict] = []
    for workflow_name, wf_runs in by_workflow.items():
        wf_runs.sort(key=lambda r: _parse_ts(r["createdAt"]), reverse=True)
        latest = wf_runs[0]
        if _parse_ts(latest["createdAt"]) < fresh_cutoff:
            continue  # current state is stale (no run within the window) — not a *new* flip
        prev = wf_runs[1] if len(wf_runs) > 1 else None
        latest_failed = latest.get("conclusion") in _FAIL_CONCLUSIONS
        prev_failed = bool(prev) and prev.get("conclusion") in _FAIL_CONCLUSIONS

        if latest_failed and not prev_failed:
            sha = latest.get("headSha") or ""
            pusher_name, pusher_role = classify_pusher(repo, sha)
            transitions.append(
                {
                    "kind": "failing",
                    "repo": repo,
                    "branch": branch,
                    "workflow": workflow_name,
                    "conclusion": latest.get("conclusion"),
                    "url": latest.get("url") or "",
                    "pusher_name": pusher_name,
                    "pusher_role": pusher_role,
                }
            )
        elif not latest_failed and latest.get("conclusion") == "success" and prev_failed:
            sha = latest.get("headSha") or ""
            pusher_name, pusher_role = classify_pusher(repo, sha)
            transitions.append(
                {
                    "kind": "recovered",
                    "repo": repo,
                    "branch": branch,
                    "workflow": workflow_name,
                    "conclusion": "success",
                    "url": latest.get("url") or "",
                    "pusher_name": pusher_name,
                    "pusher_role": pusher_role,
                }
            )
    return transitions


def detect_stuck_prs(repo: str, stuck_minutes: int, now: _dt.datetime) -> list[dict]:
    """Return open PRs into promotion bases that have been un-mergeable too long."""
    stuck: list[dict] = []
    for base in PROMOTION_BASES:
        prs = gh_json(
            [
                "pr",
                "list",
                "--repo",
                f"{ORG}/{repo}",
                "--base",
                base,
                "--state",
                "open",
                "--limit",
                "30",
                "--json",
                "number,title,mergeStateStatus,isDraft,autoMergeRequest,createdAt,headRefName,url",
            ]
        )
        if not isinstance(prs, list):
            continue
        for pr in prs:
            if pr.get("isDraft"):
                continue
            if pr.get("mergeStateStatus") not in _STUCK_STATES:
                continue
            has_auto_merge = pr.get("autoMergeRequest") is not None
            is_promotion = pr.get("headRefName") in _PROMOTION_HEADS
            if not (has_auto_merge or is_promotion):
                continue  # stale abandoned branch with no auto-merge — not the promotion contract
            age_min = (now - _parse_ts(pr["createdAt"])).total_seconds() / 60.0
            if age_min < stuck_minutes:
                continue
            stuck.append(
                {
                    "repo": repo,
                    "base": base,
                    "number": pr["number"],
                    "title": pr.get("title") or "",
                    "head": pr.get("headRefName") or "",
                    "state": pr.get("mergeStateStatus"),
                    "auto_merge": pr.get("autoMergeRequest") is not None,
                    "age_min": int(age_min),
                    "url": pr.get("url") or "",
                }
            )
    return stuck


def build_report(transitions: list[dict], stuck: list[dict]) -> tuple[bool, str, str]:
    """Return (alert, severity, mrkdwn_report)."""
    failing = [t for t in transitions if t["kind"] == "failing"]
    recovered = [t for t in transitions if t["kind"] == "recovered"]

    lines: list[str] = []
    if failing:
        lines.append(f":x: *{len(failing)} workflow(s) STARTED FAILING:*")
        for t in failing:
            pusher = f"👤 pushed by {t['pusher_name']} [{t['pusher_role']}]"
            lines.append(
                f"  • `{t['repo']}`@`{t['branch']}` — {t['workflow']} ({t['conclusion']}) <{t['url']}|run>  {pusher}"
            )
    if recovered:
        lines.append(f":white_check_mark: *{len(recovered)} workflow(s) RECOVERED:*")
        for t in recovered:
            pusher = f"👤 pushed by {t['pusher_name']} [{t['pusher_role']}]"
            lines.append(f"  • `{t['repo']}`@`{t['branch']}` — {t['workflow']} <{t['url']}|run>  {pusher}")
    if stuck:
        lines.append(f":hourglass_flowing_sand: *{len(stuck)} promotion PR(s) STUCK (auto-merge wedged):*")
        for s in stuck:
            am = "auto-merge ON" if s["auto_merge"] else "auto-merge OFF"
            lines.append(
                f"  • `{s['repo']}` #{s['number']} {s['head']}→{s['base']} — "
                f"{s['state']} for {s['age_min']}m, {am} <{s['url']}|PR>"
            )

    alert = bool(failing or stuck)  # recoveries alone post as INFO, not a page
    severity = "CRITICAL" if (failing or stuck) else "INFO"
    report = "\n".join(lines) if lines else "No CI transitions or stuck PRs detected."
    return (alert or bool(recovered)), severity, report


def write_github_output(alert: bool, severity: str, report: str) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as fh:
        fh.write(f"alert={'true' if alert else 'false'}\n")
        fh.write(f"severity={severity}\n")
        fh.write("report<<__RPT__\n")
        fh.write(report + "\n")
        fh.write("__RPT__\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="Watch a single repo instead of the full fleet.")
    parser.add_argument("--limit", type=int, default=25, help="Recent runs to inspect per repo/branch.")
    parser.add_argument("--stuck-minutes", type=int, default=30, help="Age before an un-mergeable PR is 'stuck'.")
    parser.add_argument(
        "--fresh-hours",
        type=float,
        default=2.0,
        help="Only alert on a transition whose latest run is within this many hours "
        "(stateless guard against re-paging ancient dead workflows). Cron is */15m.",
    )
    parser.add_argument("--now", help="Override 'now' (ISO8601) for deterministic testing.")
    args = parser.parse_args()

    repos = [args.repo] if args.repo else REPOS
    now = _parse_ts(args.now) if args.now else _dt.datetime.now(_dt.UTC)

    transitions: list[dict] = []
    stuck: list[dict] = []
    for repo in repos:
        for branch in WATCHED_BRANCHES:
            transitions.extend(detect_transitions(repo, branch, args.limit, now, args.fresh_hours))
        stuck.extend(detect_stuck_prs(repo, args.stuck_minutes, now))

    alert, severity, report = build_report(transitions, stuck)
    print(report)
    write_github_output(alert, severity, report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
