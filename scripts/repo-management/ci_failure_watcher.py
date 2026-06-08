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
# statusCheckRollup conclusions are UPPERCASE. A BLOCKED PR is escalatable as a CI failure
# ONLY when a required check actually FAILED (not merely pending / a transient staging-lock).
_FAIL_CONCLUSIONS_UPPER = {"FAILURE", "TIMED_OUT", "STARTUP_FAILURE"}
_STUCK_STATES = {"CONFLICTING", "DIRTY", "BLOCKED"}

# Heads that are part of the promotion contract (LDR -> staging -> main). A stuck PR
# off one of these is a wedged promotion even without auto-merge enabled. Random stale
# feature/chore branches are NOT paged unless they have auto-merge ON (the plan's core
# "auto-merge-stuck is a PR state" case) — otherwise the channel fills with abandoned PRs.
_PROMOTION_HEADS = {"live-defi-rollout", "staging"}

# Stuck states the orchestrator can RESOLVE as a merge_conflict wall (the `escalate`
# agent rebases/resolves on live-defi-rollout). BLOCKED is a gate/review wall — it is
# paged but never auto-escalated as a conflict (there is nothing to resolve).
_CONFLICT_STATES = {"CONFLICTING", "DIRTY"}
# Idempotency marker: a PR carrying this label has already been handed off, so the
# */15m cron must not re-dispatch it every tick.
_ESCALATION_LABEL = "escalation-dispatched"
# escalate-to-orchestrator.yml lives in the PM repo and is fired via repository_dispatch.
_PM_DISPATCH_REPO = "unified-trading-pm"


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
                "number,title,mergeStateStatus,isDraft,autoMergeRequest,createdAt,headRefName,url,statusCheckRollup",
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
            rollup = pr.get("statusCheckRollup") or []
            failed_check = any(
                isinstance(c, dict) and (c.get("conclusion") in _FAIL_CONCLUSIONS_UPPER or c.get("state") == "FAILURE")
                for c in rollup
            )
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
                    "failed_check": failed_check,
                }
            )
    return stuck


def detect_resolved_prs(repo: str, resolved_hours: float, now: _dt.datetime) -> list[dict]:
    """Return promotion PRs that recently MERGED or CLOSED — the bookend for a previously
    open/stuck/failing promotion PR.

    A FAILING promotion PR posts an open alert (detect_stuck_prs + the transition alerts);
    when it finally merges/closes, the open alert is left dangling ("is it still broken?").
    This emits a closing "resolved / no longer relevant" bookend so the channel reflects the
    PR's terminal state. Stateless: we look at PRs into a promotion base whose head is a
    promotion head (LDR/staging) that reached a terminal state within the recent window
    (matched to the cron cadence so each resolution is reported once).
    """
    resolved: list[dict] = []
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
                "closed",
                "--limit",
                "30",
                "--json",
                "number,title,state,merged,closedAt,headRefName,url",
            ]
        )
        if not isinstance(prs, list):
            continue
        for pr in prs:
            # Only promotion-contract PRs (same gate as detect_stuck_prs) so random closed
            # feature branches don't post resolved-bookends.
            if pr.get("headRefName") not in _PROMOTION_HEADS:
                continue
            closed_at = pr.get("closedAt")
            if not closed_at:
                continue
            age_h = (now - _parse_ts(closed_at)).total_seconds() / 3600.0
            if age_h < 0 or age_h > resolved_hours:
                continue  # outside the recent window → already reported (or not yet)
            resolved.append(
                {
                    "repo": repo,
                    "base": base,
                    "number": pr["number"],
                    "title": pr.get("title") or "",
                    "head": pr.get("headRefName") or "",
                    "merged": bool(pr.get("merged")),
                    "url": pr.get("url") or "",
                }
            )
    return resolved


def build_report(
    transitions: list[dict], stuck: list[dict], resolved: list[dict] | None = None
) -> tuple[bool, str, str]:
    """Return (alert, severity, mrkdwn_report)."""
    resolved = resolved or []
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
    if resolved:
        lines.append(f":ballot_box_with_check: *{len(resolved)} promotion PR(s) RESOLVED (merged/closed):*")
        for r in resolved:
            verb = "merged" if r["merged"] else "closed"
            lines.append(f"  • `{r['repo']}` #{r['number']} {r['head']}→{r['base']} {verb} <{r['url']}|PR>")

    alert = bool(failing or stuck)  # recoveries/resolutions alone post as INFO, not a page
    severity = "CRITICAL" if (failing or stuck) else "INFO"
    report = "\n".join(lines) if lines else "No CI transitions, stuck PRs, or resolutions detected."
    return (alert or bool(recovered) or bool(resolved)), severity, report


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


def conflict_prs_to_escalate(stuck: list[dict], already_escalated: set[tuple[str, int]]) -> list[dict]:
    """Pure selector: which stuck PRs are merge-conflict walls not yet handed off.

    A PR qualifies iff its ``state`` is a conflict (``CONFLICTING``/``DIRTY`` — a
    wall the ``escalate`` agent can resolve) AND ``(repo, number)`` is not already in
    ``already_escalated`` (the idempotency set, derived from the PR label). No IO — the
    label set is injected so this is unit-testable without ``gh``/network.
    """
    out: list[dict] = []
    for s in stuck:
        if s.get("state") not in _CONFLICT_STATES:
            continue
        if (s.get("repo"), int(s.get("number", 0))) in already_escalated:
            continue
        out.append(s)
    return out


def blocked_failing_prs_to_escalate(stuck: list[dict], already_escalated: set[tuple[str, int]]) -> list[dict]:
    """Pure selector: BLOCKED stuck PRs with a FAILED required check → escalate as sit_failure.

    With human approvals at 0 fleet-wide, a BLOCKED promotion PR is (almost always) blocked by a
    failing required check (quality-gates-v2 RED) — which the orchestrator's escalate agent CAN
    triage + fix on live-defi-rollout, unlike a transient staging-lock (``failed_check`` False)
    that clears itself. Guarded on ``failed_check`` so a pending lock never spawns a worker. No IO
    — the label set is injected so this is unit-testable.
    """
    out: list[dict] = []
    for s in stuck:
        if s.get("state") != "BLOCKED" or not s.get("failed_check"):
            continue
        if (s.get("repo"), int(s.get("number", 0))) in already_escalated:
            continue
        out.append(s)
    return out


def _pr_has_escalation_label(repo: str, number: int) -> bool:
    """True if the PR already carries ``_ESCALATION_LABEL`` (best-effort; False on error)."""
    data = gh_json(["pr", "view", str(number), "--repo", f"{ORG}/{repo}", "--json", "labels"])
    if not isinstance(data, dict):
        return False
    labels = data.get("labels")
    if not isinstance(labels, list):
        return False
    return any(isinstance(lbl, dict) and lbl.get("name") == _ESCALATION_LABEL for lbl in labels)


def _dispatch_escalation(s: dict) -> bool:
    """Fire escalate-to-orchestrator for one conflict-stuck PR (dispatch only).

    Returns True iff the repository_dispatch POST was ACCEPTED by GitHub (NOT that a worker
    spawned). The ``_ESCALATION_LABEL`` idempotency marker is applied DOWNSTREAM by
    escalate-to-orchestrator.yml ONLY when /api/escalate confirms a spawn (200 + escalation_id);
    a 503/no-slot leaves the PR unlabelled so the next cron tick re-dispatches (retry until a
    slot frees). The orchestrator's ``escalate`` agent then resolves the conflict on
    live-defi-rollout (see escalate-to-orchestrator.yml + server/escalation.py).
    """
    repo = s["repo"]
    number = int(s["number"])
    is_conflict = s.get("state") in _CONFLICT_STATES
    wall_type = "merge_conflict" if is_conflict else "sit_failure"
    if is_conflict:
        context = (
            f"Promotion PR {repo}#{number} ({s.get('head')}→{s.get('base')}) has been "
            f"{s.get('state')} for {s.get('age_min')}m and cannot auto-merge. Resolve the merge "
            f"conflict on live-defi-rollout, push, and let quality-gates-v2 re-gate it."
        )
    else:
        context = (
            f"Promotion PR {repo}#{number} ({s.get('head')}→{s.get('base')}) has been BLOCKED for "
            f"{s.get('age_min')}m by a FAILED required check (quality-gates-v2 RED). Read the failing "
            f"gate log, fix the root cause on live-defi-rollout, push, and let quality-gates-v2 re-gate."
        )
    payload = {
        "event_type": "escalate-to-orchestrator",
        "client_payload": {
            "repo": repo,
            "pr_number": number,
            "wall_type": wall_type,
            "context": context,
            "authoring_slot": "ci",
        },
    }
    proc = subprocess.run(
        ["gh", "api", f"repos/{ORG}/{_PM_DISPATCH_REPO}/dispatches", "--input", "-"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(f"  ! escalate dispatch failed for {repo}#{number}: {proc.stderr.strip()[:200]}", file=sys.stderr)
        return False
    # NOTE: do NOT label the PR here. A successful `repository_dispatch` only means GitHub
    # ACCEPTED the event — NOT that the orchestrator spawned a worker. The actual spawn
    # confirmation happens downstream in escalate-to-orchestrator.yml (POST /api/escalate →
    # 200 + escalation_id == confirmed; 503/no-id == no free slot, RETRYABLE). The
    # `_ESCALATION_LABEL` idempotency marker is therefore applied by that workflow ONLY on a
    # CONFIRMED spawn, so a capacity failure leaves the PR UNLABELLED and the next */15m tick
    # re-dispatches (the "escalate after X minutes until a slot frees" behaviour). Labelling
    # here on dispatch-accepted was the no-retry bug: a 503 still suppressed all future ticks.
    # SSOT: cicd_contract_hardening_2026_06_01 § "Auto-remediation pipeline gaps".
    print(f"  -> dispatched {repo}#{number} ({s.get('state')}) to orchestrator ({wall_type}); awaiting spawn-confirm")
    return True


def escalate_stuck_prs(stuck: list[dict], *, dry_run: bool = True) -> list[dict]:
    """Hand each conflict-stuck promotion PR to the orchestrator (idempotent via label).

    Returns the PRs dispatched (in ``dry_run``, the PRs that WOULD be dispatched — used
    by the report/tests). The label check happens per-candidate so a non-conflict stuck
    PR (e.g. BLOCKED) never triggers a ``gh`` call.
    """
    dispatched: list[dict] = []
    # Conflict-stuck (CONFLICTING/DIRTY) → merge_conflict; BLOCKED-with-failed-check → sit_failure.
    # Both reuse the same per-PR label idempotency. _dispatch_escalation derives the wall_type from state.
    candidates = conflict_prs_to_escalate(stuck, already_escalated=set()) + blocked_failing_prs_to_escalate(
        stuck, already_escalated=set()
    )
    for s in candidates:
        repo, number = s["repo"], int(s["number"])
        if _pr_has_escalation_label(repo, number):
            continue  # already handed off — don't re-dispatch
        if not dry_run and not _dispatch_escalation(s):
            continue  # dispatch failed — don't claim it
        dispatched.append(s)
    return dispatched


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
    parser.add_argument(
        "--resolved-hours",
        type=float,
        default=0.5,
        help="Report a promotion PR merged/closed within this many hours as a 'resolved' "
        "bookend (closes a dangling FAILING/stuck alert). Matched to the */15m cron so each "
        "resolution posts once. Set 0 to disable.",
    )
    parser.add_argument("--now", help="Override 'now' (ISO8601) for deterministic testing.")
    parser.add_argument(
        "--escalate",
        action="store_true",
        help="Hand conflict-stuck (CONFLICTING/DIRTY) promotion PRs to the orchestrator via "
        "escalate-to-orchestrator (idempotent per PR label). Default OFF — only the cron passes "
        "it, so --repo/--now diagnostic runs never dispatch.",
    )
    args = parser.parse_args()

    repos = [args.repo] if args.repo else REPOS
    now = _parse_ts(args.now) if args.now else _dt.datetime.now(_dt.UTC)

    transitions: list[dict] = []
    stuck: list[dict] = []
    resolved: list[dict] = []
    for repo in repos:
        for branch in WATCHED_BRANCHES:
            transitions.extend(detect_transitions(repo, branch, args.limit, now, args.fresh_hours))
        stuck.extend(detect_stuck_prs(repo, args.stuck_minutes, now))
        if args.resolved_hours > 0:
            resolved.extend(detect_resolved_prs(repo, args.resolved_hours, now))

    alert, severity, report = build_report(transitions, stuck, resolved)
    print(report)
    write_github_output(alert, severity, report)

    # Close the loop: hand merge-conflict-stuck promotion PRs to the orchestrator
    # (resolve) rather than only paging. Idempotent per PR label so the */15m cron does
    # not re-dispatch. Disabling auto-merge on a DIRTY PR is pointless (operator note) —
    # the lever is resolution, gated by the REQUIRED quality-gates-v2 check.
    if args.escalate and stuck:
        escalate_stuck_prs(stuck, dry_run=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
