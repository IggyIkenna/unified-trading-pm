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
# A head commit carrying either marker tells GitHub Actions to skip push+pull_request runs for
# that SHA — so close+reopen never re-fires v2; the recovery must be a workflow_dispatch instead.
# GitHub's full CI-suppression token set (substring match ANYWHERE in the message — even a
# descriptive mention suppresses: incident 2026-06-10, a manual recovery commit titled
# "advance past [skip ci] bump head" itself got zero push/pull_request runs).
_SKIP_CI_MARKERS = ("[skip ci]", "[ci skip]", "[no ci]", "[skip actions]", "[actions skip]")
# Subject marker of our own recovery commits — never stack a second recovery on one.
_RECOVERY_MARKER = "ci: re-fire quality-gates-v2"
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

# GitHub Actions BILLING / spending-limit block. When the account's Actions spend is
# exhausted, EVERY job fleet-wide fails at "Set up job" with ZERO steps and a check-run
# annotation carrying one of these phrases. It looks like a normal failure to the
# transition detector but is a SINGLE account-level outage that freezes ALL CI (incident
# 2026-06-08: the whole promotion pipeline silently wedged for ~hours). We detect the
# signature and emit ONE unmissable alert pointing at the operator fix, instead of N noisy
# per-workflow "started failing" lines. SSOT: cicd_contract_hardening_2026_06_01.md
# § "Auto-remediation pipeline gaps" (billing P0).
_BILLING_PHRASES = (
    "spending limit",
    "account payments have failed",
    "recent account payments",
    "billing & plans",
)


def _annotation_is_billing(messages: list[str]) -> bool:
    """Pure: True if any check-run annotation message is the Actions billing-block text.

    Network-free so it is unit-testable. Case-insensitive substring match against the
    known GitHub spending-limit / failed-payment phrasing.
    """
    blob = " ".join(m for m in messages if m).lower()
    return any(p in blob for p in _BILLING_PHRASES)


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
                "number,title,mergeStateStatus,isDraft,autoMergeRequest,createdAt,headRefName,url,statusCheckRollup,commits",
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
            # Is the required quality-gates-v2 check present in the rollup at all? When it is
            # ABSENT (never reported) the PR is BLOCKED on an "expected" check — the v2-never-fired
            # deadlock (promote PR head pushed by a token that suppresses pull_request). That case
            # is deterministically auto-recoverable (close+reopen re-fires pull_request → v2 runs).
            v2_present = any(
                isinstance(c, dict) and "quality-gates-v2" in str(c.get("name") or c.get("context") or "")
                for c in rollup
            )
            # The head commit message decides the auto-recovery MECHANISM (see auto_recover_stuck_prs):
            # a `[skip ci]` head suppresses BOTH push and pull_request, so close+reopen cannot re-fire
            # v2 — and a workflow_dispatch run is NOT associated with the PR, so its green does NOT
            # satisfy the required check (verified live 2026-06-10: 3x green dispatch runs on the
            # exact head SHA, PR stayed BLOCKED). The only working lever is superseding the head with
            # a fresh clean-message EMPTY commit. `commits` is PR-ordered; the head is last.
            commits = pr.get("commits") or []
            head_message = ""
            head_oid = ""
            if commits and isinstance(commits[-1], dict):
                _last = commits[-1]
                head_message = f"{_last.get('messageHeadline') or ''}\n{_last.get('messageBody') or ''}".strip()
                head_oid = _last.get("oid") or ""
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
                    "v2_present": v2_present,
                    "head_message": head_message,
                    "head_oid": head_oid,
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
                # NOTE: `merged` is NOT a valid `gh pr list` JSON field (it 404s the whole query →
                # resolved bookends silently never fired). Use `mergedAt` (non-null ⟺ merged).
                "number,title,state,mergedAt,closedAt,headRefName,url",
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
                    "merged": bool(pr.get("mergedAt")),
                    "url": pr.get("url") or "",
                }
            )
    return resolved


def _run_is_billing_block(repo: str, run_id: int) -> bool:
    """True if a failed run's first job failed at setup with the billing annotation.

    Cheap signature first (a job with ZERO steps = it never started → "Set up job"
    failure), then confirm via the check-run annotation text so we don't false-positive
    on other startup failures. Network errors → False (never raises, never pages wrongly).
    """
    jobs = gh_json(["api", f"repos/{ORG}/{repo}/actions/runs/{run_id}/jobs"])
    if not isinstance(jobs, dict):
        return False
    job_list = jobs.get("jobs")
    if not isinstance(job_list, list):
        return False
    for job in job_list:
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        # 0 steps == the job never reached its first real step (setup-phase failure).
        if isinstance(steps, list) and len(steps) > 0:
            continue
        job_id = job.get("id")
        if not job_id:
            continue
        anns = gh_json(["api", f"repos/{ORG}/{repo}/check-runs/{job_id}/annotations"])
        messages = [(a.get("message") or "") for a in anns if isinstance(a, dict)] if isinstance(anns, list) else []
        if _annotation_is_billing(messages):
            return True
    return False


def detect_billing_block(repos: list[str], now: _dt.datetime, fresh_hours: float) -> dict | None:
    """Detect the account-level GitHub Actions billing/spending-limit outage.

    Billing exhaustion fails EVERY job fleet-wide, so this is a single global condition —
    we scan repos' most-recent failed runs and SHORT-CIRCUIT on the first billing-signature
    match, returning ONE alert record (not one per repo/workflow). Bounded to runs within
    ``fresh_hours`` so a long-resolved outage doesn't re-page. Returns None when CI is
    billing-healthy. Best-effort: any gh error is swallowed (returns None).
    """
    cutoff = now - _dt.timedelta(hours=fresh_hours)
    for repo in repos:
        runs = gh_json(
            [
                "run",
                "list",
                "--repo",
                f"{ORG}/{repo}",
                "--limit",
                "8",
                "--json",
                "databaseId,conclusion,status,createdAt,url,workflowName",
            ]
        )
        if not isinstance(runs, list):
            continue
        for run in runs:
            if run.get("status") != "completed" or run.get("conclusion") not in _FAIL_CONCLUSIONS:
                continue
            if _parse_ts(run["createdAt"]) < cutoff:
                continue
            if _run_is_billing_block(repo, int(run["databaseId"])):
                return {
                    "repo": repo,
                    "workflow": run.get("workflowName") or "",
                    "url": run.get("url") or "",
                }
    return None


def build_report(
    transitions: list[dict],
    stuck: list[dict],
    resolved: list[dict] | None = None,
    billing: dict | None = None,
) -> tuple[bool, str, str]:
    """Return (alert, severity, mrkdwn_report)."""
    resolved = resolved or []
    failing = [t for t in transitions if t["kind"] == "failing"]
    recovered = [t for t in transitions if t["kind"] == "recovered"]

    lines: list[str] = []
    if billing:
        # One unmissable, operator-actionable line. Billing exhaustion freezes ALL CI, so
        # surface it ABOVE the noisy per-workflow failures it causes.
        lines.append(
            ":rotating_light: *GitHub Actions BILLING BLOCK — all CI is FROZEN fleet-wide.* "
            "Every job fails at 'Set up job' (spending limit / failed payment). "
            "FIX: GitHub → Settings → Billing & plans (raise the Actions spending limit). "
            f"Evidence: `{billing['repo']}` {billing['workflow']} <{billing['url']}|run>."
        )
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

    alert = bool(failing or stuck or billing)  # recoveries/resolutions alone post as INFO, not a page
    severity = "CRITICAL" if (failing or stuck or billing) else "INFO"
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
        failed_check = s.get("failed_check") or "quality-gates-v2"
        context = (
            f"Promotion PR {repo}#{number} ({s.get('head')}→{s.get('base')}) has been BLOCKED for "
            f"{s.get('age_min')}m by a FAILED required check ({failed_check}). Read the failing gate "
            f"log FIRST to classify: (A) a genuine code/test/lint/type break → fix the root cause on "
            f"live-defi-rollout, push, let it re-gate; OR (B) a STALE-STAGING-WORKFLOW failure — the "
            f"failing step is a workflow-DEFINITION error (actionlint/yaml/a step referencing something "
            f"already removed or fixed on live-defi-rollout) OR the required check is MISSING (a "
            f"[skip ci] head reported zero check runs). For (B) the fix is NOT on live-defi-rollout (it "
            f"is already correct there) — the PR base branch ({s.get('base')}) carries a stale copy of "
            f"the workflow. Re-roll the workflow from the PM SSOT to {s.get('base')} "
            f"(scripts/workflow-templates/ → rollout-workflow-templates.sh), or re-trigger the check on "
            f"the PR head (`gh workflow run quality-gates-v2.yml --ref <head>`); do NOT 'fix' "
            f"live-defi-rollout for a (B) failure."
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


def _refire_v2_with_empty_commit(repo: str, branch: str, head_sha: str) -> bool:
    """Supersede a CI-suppressed promotion-branch head with an EMPTY clean-message commit.

    Pure git-data API (no clone): read the head commit's tree, create a commit with the SAME
    tree on top of it, fast-forward the branch ref. The new head's message carries no
    suppression token, so the ref update fires real ``push`` + ``pull_request`` runs whose
    quality-gates-v2 check IS associated with the PR — the only re-trigger that satisfies the
    required check (close+reopen and workflow_dispatch both verified ineffective, 2026-06-10).
    Same-tree means the suppressed content itself finally gets a counting CI validation.
    Requires the PAT to bypass the staging push ruleset (repo-admin bypass — true for GH_PAT).
    """
    head = gh_json(["api", f"repos/{ORG}/{repo}/git/commits/{head_sha}"])
    tree = (head.get("tree") or {}).get("sha") if isinstance(head, dict) else None
    if not tree:
        return False
    msg = (
        f"{_RECOVERY_MARKER} — supersede CI-suppressed head so the required check can report\n\n"
        "The prior head commit carried a CI-suppression token, so quality-gates-v2 never reported\n"
        "on it and the promotion PR was permanently BLOCKED (required context missing).\n"
        "close+reopen re-fires pull_request — equally suppressed on such a head; a\n"
        "workflow_dispatch run is not associated with the PR, so its green does not satisfy the\n"
        "required check (both verified live 2026-06-10). Empty commit, same tree: the suppressed\n"
        "content gets a real, counting CI run.\n"
        "Plan: semver_version_bump_skip_ci_promotion_block_2026_06_09."
    )
    new = gh_json(
        [
            "api",
            f"repos/{ORG}/{repo}/git/commits",
            "-f",
            f"message={msg}",
            "-f",
            f"tree={tree}",
            "-f",
            f"parents[]={head_sha}",
        ]
    )
    new_sha = new.get("sha") if isinstance(new, dict) else None
    if not new_sha:
        return False
    res = gh_json(["api", "-X", "PATCH", f"repos/{ORG}/{repo}/git/refs/heads/{branch}", "-f", f"sha={new_sha}"])
    return isinstance(res, dict) and (res.get("object") or {}).get("sha") == new_sha


def auto_recover_stuck_prs(stuck: list[dict], *, dry_run: bool = False) -> list[dict]:
    """Deterministically recover a v2-NEVER-REPORTED promotion-PR deadlock (no worker needed).

    A promotion PR sits BLOCKED forever when the required quality-gates-v2 check never reported
    on its head SHA. Gated to the EXACT deadlock signature — BLOCKED + no failed check + v2
    ABSENT from the rollup — so it never touches a genuinely-failing PR (v2 ran red → escalate
    instead) or one whose v2 is in-flight (v2 present). Better than escalating a deterministic
    deadlock to a busy orchestrator.

    TWO mechanisms by head-commit kind (both within the same gate):
      - default (head pushed by a workflow-suppressing token, message clean) → close+reopen,
        which re-fires the ``pull_request`` event. Once reopened, v2 appears in the rollup, so
        the next tick won't re-fire (no loop).
      - CI-suppression-token head (``[skip ci]``/``[ci skip]``/… anywhere in the message — the
        semver bump / dep pin / a manual recovery commit that merely MENTIONS the token) →
        close+reopen is INEFFECTIVE (the re-fired pull_request is equally suppressed) and a
        ``workflow_dispatch`` run does NOT satisfy the PR's required check (its check suite is
        not associated with the PR — verified live 2026-06-10: 3x green dispatch runs on the
        exact head SHA, PR stayed BLOCKED). Recover by SUPERSEDING the head with an empty
        clean-message commit (same tree) via the git-data API → real push/pull_request runs
        fire and count. The new head changes the PR head SHA, so the next tick sees v2
        in-flight/green (no loop); a head already carrying our recovery marker is never
        stacked with a second recovery commit.
    """
    recovered: list[dict] = []
    for s in stuck:
        if s.get("state") != "BLOCKED" or s.get("failed_check") or s.get("v2_present"):
            continue
        if s.get("head") not in _PROMOTION_HEADS:
            continue
        repo, number, head = s["repo"], int(s["number"]), s["head"]
        head_message = (s.get("head_message") or "").lower()
        if _RECOVERY_MARKER in head_message:
            # We already superseded this head once and its v2 hasn't reported yet (in-flight,
            # or it failed → the failed_check/escalate paths own it). Never stack recoveries.
            continue
        skip_ci_head = any(m in head_message for m in _SKIP_CI_MARKERS)
        if dry_run:
            recovered.append(s)
            continue
        if skip_ci_head:
            head_oid = s.get("head_oid") or ""
            if head_oid and _refire_v2_with_empty_commit(repo, head, head_oid):
                print(
                    f"  auto-recovered {repo}#{number}: superseded CI-suppressed head {head_oid[:8]} on {head} "
                    f"with an empty clean commit → push/pull_request v2 fires and counts"
                )
                recovered.append(s)
            else:
                print(
                    f"  ! auto-recover {repo}#{number}: empty-commit re-fire failed "
                    f"(head_oid={head_oid[:8] or 'MISSING'}) — will retry next tick",
                    file=sys.stderr,
                )
            continue
        closed = (
            subprocess.run(
                ["gh", "pr", "close", str(number), "--repo", f"{ORG}/{repo}"], capture_output=True, text=True
            ).returncode
            == 0
        )
        reopened = (
            subprocess.run(
                ["gh", "pr", "reopen", str(number), "--repo", f"{ORG}/{repo}"], capture_output=True, text=True
            ).returncode
            == 0
        )
        if closed and reopened:
            print(f"  auto-recovered {repo}#{number}: close+reopen → quality-gates-v2 re-fired (v2-never-reported)")
            recovered.append(s)
    return recovered


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
    parser.add_argument(
        "--auto-recover",
        action="store_true",
        help="Deterministically recover the v2-never-reported promotion-PR deadlock by close+reopen "
        "(no worker needed). Runs BEFORE --escalate so the mechanical deadlock is fixed in-band and "
        "only genuine conflicts/failures escalate. Default OFF — only the cron passes it.",
    )
    args = parser.parse_args()

    repos = [args.repo] if args.repo else REPOS
    now = _parse_ts(args.now) if args.now else _dt.datetime.now(_dt.UTC)

    # Global, account-level: scan first (short-circuits on first hit) so a billing outage
    # is surfaced as ONE alert above the per-workflow failures it would otherwise spam.
    billing = detect_billing_block(repos, now, args.fresh_hours)

    transitions: list[dict] = []
    stuck: list[dict] = []
    resolved: list[dict] = []
    for repo in repos:
        for branch in WATCHED_BRANCHES:
            transitions.extend(detect_transitions(repo, branch, args.limit, now, args.fresh_hours))
        stuck.extend(detect_stuck_prs(repo, args.stuck_minutes, now))
        if args.resolved_hours > 0:
            resolved.extend(detect_resolved_prs(repo, args.resolved_hours, now))

    alert, severity, report = build_report(transitions, stuck, resolved, billing)
    print(report)
    write_github_output(alert, severity, report)

    # Close the loop: hand merge-conflict-stuck promotion PRs to the orchestrator
    # (resolve) rather than only paging. Idempotent per PR label so the */15m cron does
    # not re-dispatch. Disabling auto-merge on a DIRTY PR is pointless (operator note) —
    # the lever is resolution, gated by the REQUIRED quality-gates-v2 check.
    # Auto-recover the deterministic v2-never-reported deadlock FIRST (close+reopen re-fires v2);
    # then escalate only what's left genuinely conflicting/failing to the orchestrator.
    if args.auto_recover and stuck:
        auto_recover_stuck_prs(stuck, dry_run=False)
    if args.escalate and stuck:
        escalate_stuck_prs(stuck, dry_run=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
