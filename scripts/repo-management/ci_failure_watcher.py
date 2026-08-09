#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
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
import hashlib
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

# ── Re-nag cadence (Phase 5) ───────────────────────────────────────────────────
# A still-OPEN condition must RE-SURFACE on a cadence matched to its expected MTTR — not
# page-once (an alert that got buried under newer messages and was never acted on must nag
# again). The shared carrier (notify-slack.yml) owns the re-fire: each per-condition
# `dedup_key` is suppressed within `cooldown_min` and RE-ARMS (re-posts) once that elapses
# AND the watcher still re-detects it. So the deliberately-stateless watcher just emits the
# CURRENT open set every */15 tick and the carrier paces the re-nag from the GCS ledger (the
# per-condition last-posted state). SSOT: alert_quality_overhaul_2026_06_18.md § Phase 5.
RENAG_STUCK_PR_MIN = 20  # wedged promotion PR — fast MTTR, high urgency (operator: 15-20m)
RENAG_FLEET_FROZEN_MIN = 20  # GitHub Actions billing block freezes ALL CI — same urgency band
RENAG_WORKFLOW_FAIL_MIN = 60  # a failing workflow / QG-red typically ~1h to fix (operator)
BOOKEND_COOLDOWN_MIN = 5  # recovered/resolved bookends — distinct key + short cooldown so a
# closure is never swallowed by an open-condition cooldown
# A failure older than this is treated as known/abandoned (not re-surfaced) — bounds the
# stateless current-failing detector the way --fresh-hours bounds the flip detector.
RENAG_FAIL_WINDOW_HOURS = 6.0
# ── Flap suppression (N-tick debounce, plan L1573) ───────────────────────────────
# A workflow that oscillates FEATURE_GREEN ↔ FAILING rapidly (flaky tests, intermittent
# infra) should not page on every individual flip. We inspect the last FLAP_DETECT_RUNS
# completed runs per workflow and count fail↔success state transitions. When that count
# reaches FLAP_TRANSITION_THRESHOLD the workflow is "flapping" — per-flip alerts are
# downgraded from CRITICAL/RENAG_WORKFLOW_FAIL_MIN to WARNING/RENAG_FLAPPING_MIN so the
# channel is not flooded, while a distinct "flapping" alert key still surfaces the pattern.
FLAP_DETECT_RUNS = 5  # inspect this many recent completed runs per workflow
FLAP_TRANSITION_THRESHOLD = 3  # ≥ this many fail↔success flips in that window = "flapping"
RENAG_FLAPPING_MIN = 240  # re-nag cooldown for flapping workflows (4 h)
# ── Self-hosted glue-runner starvation (CI cost reduction B1) ─────────────────────
# Once PM's glue workflows run on the self-hosted pools, a dead VM becomes SILENT: GitHub keeps
# ACCEPTING the dispatches, the jobs just sit `queued`, and NOTHING here would notice — the other
# detectors watch for FAILURES, and a queued job is not a failure until GitHub kills it at 24 h.
# That window loses ci_status transitions → stale Firestore → blocked promotes (MAIN_GREEN is the
# dep-on-main gate staging-to-main.yml STAGE 1.8 reads).
#
# NOTE this is a CORRECTNESS alarm, not a cost one: queue time is FREE (GitHub bills execution
# minutes on HOSTED runners, and a self-hosted-labelled job never lands on billed hardware), so a
# dead VM is the cheapest possible state. The urgency is data loss at 24 h, nothing else.
#
# This detector lives HERE rather than in its own workflow on purpose: ci-health is already
# KEEP-M hosted (it must NOT run on the box it watches) and already crons */15, so the check is a
# step in an ALREADY-BILLED job (~$0). A standalone watchdog would cost ~$52/mo at */5 or ~$17/mo
# at */15 (per-job 1-min minimum) — a third of the saving this whole plan exists to capture.
# SSOT: /plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md.
GLUE_QUEUED_ALERT_MIN = 10  # operator 2026-07-16: a glue job queued longer than this pages
RENAG_GLUE_STARVED_MIN = 15  # operator 2026-07-16: page LOUDLY every 15 min until it is fixed
# The two pools' distinguishing labels. DISJOINT by design — `glue-writer` deliberately does NOT
# carry `glue`, because runner label matching is a subset test and a writer carrying both would
# also match `runs-on: [self-hosted, glue]` and steal the movers' jobs.
_GLUE_LABELS = frozenset({"glue", "glue-writer"})
# A head commit carrying either marker tells GitHub Actions to skip push+pull_request runs for
# that SHA — so close+reopen never re-fires v2; the recovery must be a workflow_dispatch instead.
# GitHub's full CI-suppression token set (substring match ANYWHERE in the message — even a
# descriptive mention suppresses: incident 2026-06-10, a manual recovery commit titled
# "advance past [skip ci] bump head" itself got zero push/pull_request runs).
_SKIP_CI_MARKERS = ("[skip ci]", "[ci skip]", "[no ci]", "[skip actions]", "[actions skip]")
# Subject marker of our own recovery commits — never stack a second recovery on one.
_RECOVERY_MARKER = "ci: re-fire quality-gates-v2"
# Hidden marker posted on a PR when we close+reopen to recover a v2=`action_required` strand.
# Unlike the v2-never-reported case (v2 becomes permanently PRESENT after reopen → no loop), an
# `action_required` head can RE-conclude `action_required` on the re-fired run, so this marker
# bounds the retries to ~1 per `_ACTION_REQ_RECOVER_WINDOW_MIN` (no every-tick thrash).
_ACTION_REQ_MARKER = "<!-- ci-watcher:action-required-recovery -->"
_ACTION_REQ_RECOVER_WINDOW_MIN = 40
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

# Workflows whose failure is BY DESIGN (a controlled non-zero exit that signals an
# expected state, not a broken build). Suppress from both the flip detector and the
# re-nag detector — paging on these is false-positive noise.
#
# "Staging Lock Check": exits 1 when staging is locked (SIT running). This is the
# correct signal that prevents auto-merge while SIT holds the lock. The exit-1 path
# is guarded by an explicit `LOCKED=true` check; genuine script errors (curl failure)
# are soft-exited at 0 (assumes unlocked). Paging this as a CI failure would fire on
# every SIT cycle — operator-confirmed as pure noise (WS-G contract_hardening #7).
_BY_DESIGN_FAIL_WORKFLOWS: frozenset[str] = frozenset({"Staging Lock Check"})

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


def _is_flapping(wf_runs: list[dict], threshold: int) -> bool:
    """True if `wf_runs` (newest-first, already sorted) shows rapid fail↔success oscillation.

    Counts conclusion-state transitions in the window. A high count means the workflow is
    oscillating rather than in a stable new state. Requires ≥ 3 runs — with fewer, a single
    genuine flip (1 transition) could meet a threshold of 1, causing false flap-suppress.
    """
    if len(wf_runs) < 3:
        return False
    transitions = sum(
        1
        for i in range(len(wf_runs) - 1)
        if (wf_runs[i].get("conclusion") in _FAIL_CONCLUSIONS)
        != (wf_runs[i + 1].get("conclusion") in _FAIL_CONCLUSIONS)
    )
    return transitions >= threshold


def detect_transitions(
    repo: str,
    branch: str,
    limit: int,
    now: _dt.datetime,
    fresh_hours: float,
    flap_detect_runs: int = FLAP_DETECT_RUNS,
    flap_threshold: int = FLAP_TRANSITION_THRESHOLD,
) -> list[dict]:
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
        if workflow_name in _BY_DESIGN_FAIL_WORKFLOWS:
            continue  # by-design failure — never page (e.g. Staging Lock Check exits 1 when locked)
        wf_runs.sort(key=lambda r: _parse_ts(r["createdAt"]), reverse=True)
        latest = wf_runs[0]
        if _parse_ts(latest["createdAt"]) < fresh_cutoff:
            continue  # current state is stale (no run within the window) — not a *new* flip
        prev = wf_runs[1] if len(wf_runs) > 1 else None
        latest_failed = latest.get("conclusion") in _FAIL_CONCLUSIONS
        prev_failed = bool(prev) and prev.get("conclusion") in _FAIL_CONCLUSIONS
        is_flapping = _is_flapping(wf_runs[:flap_detect_runs], flap_threshold)

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
                    "run_id": latest.get("databaseId"),
                    "head_sha": sha,
                    "pusher_name": pusher_name,
                    "pusher_role": pusher_role,
                    "flapping": is_flapping,
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
                    "run_id": latest.get("databaseId"),
                    "head_sha": sha,
                    "pusher_name": pusher_name,
                    "pusher_role": pusher_role,
                    "flapping": is_flapping,
                }
            )
    return transitions


def detect_currently_failing(
    repo: str,
    branch: str,
    limit: int,
    now: _dt.datetime,
    window_hours: float,
    flap_detect_runs: int = FLAP_DETECT_RUNS,
    flap_threshold: int = FLAP_TRANSITION_THRESHOLD,
) -> list[dict]:
    """Workflows whose LATEST completed run on ``branch`` is a failure, within ``window_hours``.

    Unlike :func:`detect_transitions` (which fires once on the failure→failure FLIP and then
    goes quiet — the gap that let a buried QG-red alert never re-surface), this reports the
    CURRENT failing set on EVERY tick so the carrier can RE-NAG a still-red workflow on its
    ``cooldown_min``. The window bounds re-nagging to live concerns: a failure whose latest run
    is older than ``window_hours`` is treated as known/abandoned and not re-surfaced (the
    stateless analogue of ``--fresh-hours`` for the flip detector). Records share the shape of a
    ``failing`` transition (plus ``age_min``) so :func:`enrich_failure_reasons` and the alert-line
    builder are reused. Stateless — the carrier's GCS ledger is the per-condition last-posted state.
    """
    cutoff = now - _dt.timedelta(hours=window_hours)
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

    failing: list[dict] = []
    for workflow_name, wf_runs in by_workflow.items():
        if workflow_name in _BY_DESIGN_FAIL_WORKFLOWS:
            continue  # by-design failure — never re-nag (e.g. Staging Lock Check exits 1 when locked)
        wf_runs.sort(key=lambda r: _parse_ts(r["createdAt"]), reverse=True)
        latest = wf_runs[0]
        latest_ts = _parse_ts(latest["createdAt"])
        if latest_ts < cutoff:
            continue  # latest run too old — known/abandoned, not a live concern to re-nag
        if latest.get("conclusion") not in _FAIL_CONCLUSIONS:
            continue  # currently green (or non-failing) — nothing to surface
        sha = latest.get("headSha") or ""
        pusher_name, pusher_role = classify_pusher(repo, sha)
        failing.append(
            {
                "kind": "failing",
                "repo": repo,
                "branch": branch,
                "workflow": workflow_name,
                "conclusion": latest.get("conclusion"),
                "url": latest.get("url") or "",
                "run_id": latest.get("databaseId"),
                "head_sha": sha,
                "pusher_name": pusher_name,
                "pusher_role": pusher_role,
                "age_min": int((now - latest_ts).total_seconds() / 60.0),
                "flapping": _is_flapping(wf_runs[:flap_detect_runs], flap_threshold),
            }
        )
    return failing


# Rollup conclusions/states that mean "this check is not the problem" — anything else (a fail
# conclusion, ACTION_REQUIRED, or no conclusion/state reported yet at all) counts as blocking for
# `_blocking_check_names` below. Deliberately narrow (an allow-list of the clean states) so an
# unrecognised/future GitHub conclusion value defaults to "blocking" rather than being silently
# treated as fine.
_SUCCESS_LIKE_CONCLUSIONS = {"SUCCESS", "NEUTRAL", "SKIPPED"}


def _blocking_check_names(rollup: list) -> list[str]:
    """Pure: names/contexts of the ``statusCheckRollup`` entries that are NOT a clean success —
    i.e. the check(s) actually driving the PR's stuck ``mergeStateStatus`` (a failure,
    ``action_required``, a pending commit status, or a check that has not reported a conclusion at
    all yet — the never-draining-QUEUED-check symptom of glue-runner starvation). Feeds
    ``_blocking_signature`` so escalation idempotency can be scoped to WHICH check(s) are blocking a
    PR right now, not just "this PR was escalated at some point in its history" (see
    ``_pr_escalation_suppressed``).
    """
    names: list[str] = []
    for c in rollup:
        if not isinstance(c, dict):
            continue
        name = str(c.get("name") or c.get("context") or "")
        if not name:
            continue
        conclusion = str(c.get("conclusion") or "").upper()
        state = str(c.get("state") or "").upper()
        if conclusion:
            if conclusion not in _SUCCESS_LIKE_CONCLUSIONS:
                names.append(name)
            continue
        if state:
            if state not in _SUCCESS_LIKE_CONCLUSIONS:
                names.append(name)
            continue
        # CheckRun with neither a conclusion nor a state yet (still QUEUED/IN_PROGRESS) — a
        # never-draining check blocks the merge exactly like a failure does.
        names.append(name)
    return sorted(set(names))


def _blocking_signature(state: str, blocking_checks: list[str]) -> str:
    """Pure: a short deterministic signature identifying the CURRENT reason a PR is stuck — its
    ``mergeStateStatus`` plus which check(s) are actually blocking it. Two stuck-PR snapshots with
    the same signature are "the same reason"; a changed signature means the PR is now blocked for
    something new, and the ``escalation-dispatched`` label from an earlier, different reason must
    not suppress it (see ``_pr_escalation_suppressed``). Not a security use of sha1 — a short,
    stable dedup key over a small, low-cardinality input.
    """
    raw = f"{state}:{','.join(sorted(blocking_checks))}"
    return hashlib.sha1(raw.encode(), usedforsecurity=False).hexdigest()[:10]


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
            # v2 PRESENT but concluded `action_required` (NOT success, NOT a FAIL conclusion) — the
            # 2026-06-17 finding (promotion_queue_conflict_wall_pileup): the required check is neither
            # green nor red, so the PR is BLOCKED with auto-merge armed but unable to fire, and the
            # v2-absent recovery never triggers (v2 IS present). A fresh `pull_request` run (close+reopen)
            # concludes `success` (verified live: 5/5 PRs today). action_required is intermittent — the
            # SAME head went success then action_required — so the auto-recover bounds its retries.
            v2_action_required = any(
                isinstance(c, dict)
                and "quality-gates-v2" in str(c.get("name") or c.get("context") or "")
                and str(c.get("conclusion") or "").upper() == "ACTION_REQUIRED"
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
            merge_state = pr.get("mergeStateStatus") or ""
            blocking_checks = _blocking_check_names(rollup)
            stuck.append(
                {
                    "repo": repo,
                    "base": base,
                    "number": pr["number"],
                    "title": pr.get("title") or "",
                    "head": pr.get("headRefName") or "",
                    "state": merge_state,
                    "auto_merge": pr.get("autoMergeRequest") is not None,
                    "age_min": int(age_min),
                    "url": pr.get("url") or "",
                    "failed_check": failed_check,
                    "v2_present": v2_present,
                    "v2_action_required": v2_action_required,
                    "head_message": head_message,
                    "head_oid": head_oid,
                    # L1581: ZERO check runs on the staging head — no CI of ANY kind fired (not
                    # just v2-absent but completely dark). Distinct from not-v2_present: here
                    # statusCheckRollup is empty, meaning nothing validated the head commit.
                    # Could be billing exhaustion, skip-ci suppression fleet-wide, or a fresh
                    # head pushed before CI had a chance to attach. Always more severe than a
                    # mere "v2 absent" since the PR could auto-merge with zero validation.
                    "zero_checks": len(rollup) == 0,
                    # Which check(s) are actually blocking THIS PR right now — the escalation
                    # idempotency signature (2026-08-07: a permanent presence-only label check
                    # silently suppressed re-paging when the blocking reason changed; see
                    # _pr_escalation_suppressed).
                    "blocking_signature": _blocking_signature(str(merge_state), blocking_checks),
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


def detect_superseded_prs(repo: str) -> list[dict]:
    """Open LDR→{base} promote PRs whose CONTENT is already fully in the base — superseded by a
    prior merge/rebase/squash (D3, ldr_trunk_promotion_decoupling_2026_06_10 — Level-3 cleanup).

    The drain rebases/squashes, so staging/main SHAs differ from the LDR commits and a SHA-membership
    check never matches. Use the compare API's changed-file count instead: **0 changed files in
    `{base}...live-defi-rollout` ⇒ the trunk content is already in base ⇒ the open promote PR has
    nothing left to promote ⇒ it is stale** (e.g. a later quickmerge incorporated the same commits).
    Content equivalence, not commit identity.
    """
    out: list[dict] = []
    for base in PROMOTION_BASES:
        prs = gh_json(
            [
                "pr",
                "list",
                "--repo",
                f"{ORG}/{repo}",
                "--base",
                base,
                "--head",
                "live-defi-rollout",
                "--state",
                "open",
                "--limit",
                "30",
                "--json",
                "number,title,url,createdAt",
            ]
        )
        if not isinstance(prs, list):
            continue
        for pr in prs:
            cmp = gh_json(["api", f"repos/{ORG}/{repo}/compare/{base}...live-defi-rollout"])
            if not isinstance(cmp, dict):
                continue
            files = cmp.get("files")
            if isinstance(files, list) and len(files) == 0:  # content already in base → superseded
                out.append(
                    {
                        "repo": repo,
                        "base": base,
                        "number": pr.get("number"),
                        "title": pr.get("title") or "",
                        "url": pr.get("url") or "",
                    }
                )
    return out


def close_superseded_prs(superseded: list[dict], *, dry_run: bool = False) -> list[dict]:
    """Close stale promote PRs (content already in base). Idempotent — a closed PR drops out of the
    open-PR list next tick; comments first so the closure is auditable."""
    closed: list[dict] = []
    for pr in superseded:
        repo, number, base = pr["repo"], pr.get("number"), pr["base"]
        if number is None:
            continue
        if dry_run:
            print(f"  [dry-run] would close superseded {repo}#{number} (LDR→{base}: content already in {base})")
            closed.append(pr)
            continue
        body = (
            f":broom: Auto-closing this LDR→{base} promote PR — its content is already in `{base}` "
            f"(0 changed files in `{base}...live-defi-rollout`), so it is superseded/stale (a later "
            f"quickmerge/rebase incorporated the same content). No action needed."
        )
        subprocess.run(
            ["gh", "pr", "comment", str(number), "--repo", f"{ORG}/{repo}", "--body", body],
            capture_output=True,
            text=True,
        )
        ok = (
            subprocess.run(
                ["gh", "pr", "close", str(number), "--repo", f"{ORG}/{repo}"], capture_output=True, text=True
            ).returncode
            == 0
        )
        if ok:
            print(f"  closed superseded {repo}#{number} (LDR→{base}: content already in {base})")
            closed.append(pr)
    return closed


def _run_is_billing_block(repo: str, run_id: int) -> bool:
    """True if a failed run's first job failed at setup with the billing annotation.

    Cheap signature first (a job with ZERO steps = it never started → "Set up job"
    failure), then confirm via the check-run annotation text so we don't false-positive
    on other startup failures. Network errors → False (never raises, never pages wrongly).

    Annotation reads can be PERMANENTLY unavailable (2026-06-10): the ``/check-runs/{id}/
    annotations`` REST endpoint 403s for fine-grained PATs — GitHub's token picker offers
    no "Checks" permission at all, so this is not grantable. When annotations are
    unreadable we fall back to the STRUCTURAL run-level signature: billing exhaustion
    fails EVERY job at setup, so a failed run where ALL jobs (≥1) have zero steps is
    treated as billing-blocked. Slightly weaker (a total runner outage could mimic it)
    but the alternative was detection silently disabled (annotations 403 → always False).
    """
    jobs = gh_json(["api", f"repos/{ORG}/{repo}/actions/runs/{run_id}/jobs"])
    if not isinstance(jobs, dict):
        return False
    job_list = jobs.get("jobs")
    if not isinstance(job_list, list) or not job_list:
        return False
    zero_step_jobs = 0
    annotations_readable = False
    for job in job_list:
        if not isinstance(job, dict):
            continue
        steps = job.get("steps")
        # 0 steps == the job never reached its first real step (setup-phase failure).
        if isinstance(steps, list) and len(steps) > 0:
            continue
        zero_step_jobs += 1
        job_id = job.get("id")
        if not job_id:
            continue
        anns = gh_json(["api", f"repos/{ORG}/{repo}/check-runs/{job_id}/annotations"])
        if isinstance(anns, list):
            annotations_readable = True
            messages = [(a.get("message") or "") for a in anns if isinstance(a, dict)]
            if _annotation_is_billing(messages):
                return True
    # Annotations unreadable (fine-grained-PAT 403 class) + EVERY job died at setup
    # → structural billing signature.
    return not annotations_readable and zero_step_jobs == len(job_list)


def detect_stale_quarantine(now: _dt.datetime, stale_min: int = 120) -> list[dict]:
    """Alert on repos stuck in promotion_quarantine for longer than ``stale_min`` minutes.

    The quarantine auto-clears on next successful promotion (staging-to-main.yml). This
    detector re-nags when a repo is STILL quarantined after ``stale_min`` — it surfaces
    the deadlock signature: a repo that failed promotion 3+ times and hasn't recovered.
    Uses the local ``workspace-manifest.json`` checkout (always present in CI context).
    Returns [] gracefully on read/parse errors.
    """
    try:
        with open("workspace-manifest.json") as fh:
            manifest = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return []

    quarantine: dict[str, dict[str, object]] = manifest.get("promotion_quarantine") or {}
    if not quarantine:
        return []

    cutoff = now - _dt.timedelta(minutes=stale_min)
    stale: list[dict] = []
    for repo, entry in quarantine.items():
        since_raw = entry.get("since")
        if not since_raw or not isinstance(since_raw, str):
            continue
        try:
            since_ts = _parse_ts(since_raw)
        except ValueError:
            continue
        if since_ts >= cutoff:
            continue  # recent quarantine — not yet stale
        attempts = entry.get("attempts", "?")
        since_human = since_ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        age_min = int((now - since_ts).total_seconds() / 60.0)
        stale.append(
            {
                "kind": "stale_quarantine",
                "repo": repo,
                "since": since_human,
                "attempts": attempts,
                "age_min": age_min,
            }
        )
    return stale


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


def _glue_runner_counts() -> dict[str, tuple[int, int]]:
    """``{label: (online, idle)}`` for each glue pool label. Best-effort → zeros on any gh error.

    NOTE the two GitHub payloads disagree on shape and it is easy to get wrong: the *runners* API
    returns ``labels`` as a list of OBJECTS (``{id, name, type}``), while the *jobs* API returns
    ``labels`` as a list of plain STRINGS. This reads the object form; ``detect_glue_starvation``
    reads the string form.
    """
    # fromkeys shares ONE value object across keys — safe here only because tuples are immutable.
    counts: dict[str, tuple[int, int]] = dict.fromkeys(sorted(_GLUE_LABELS), (0, 0))
    payload = gh_json(["api", f"/repos/{ORG}/{_PM_DISPATCH_REPO}/actions/runners"])
    if not isinstance(payload, dict):
        return counts
    runners = payload.get("runners")
    if not isinstance(runners, list):
        return counts
    for label in list(counts):
        online = 0
        idle = 0
        for runner in runners:
            if not isinstance(runner, dict):
                continue
            names = {str(item.get("name")) for item in (runner.get("labels") or []) if isinstance(item, dict)}
            if label not in names:
                continue
            if runner.get("status") == "online":
                online += 1
                if not runner.get("busy"):
                    idle += 1
        counts[label] = (online, idle)
    return counts


def detect_glue_starvation(
    repos: list[str], now: _dt.datetime, queued_minutes: int = GLUE_QUEUED_ALERT_MIN
) -> dict | None:
    """Detect self-hosted glue jobs QUEUED and not draining (the VM is down, or the pool is wedged).

    A single global condition (one alert, not one per job) — the whole pool shares one fate. Returns
    None when nothing is starved, which is the overwhelmingly common case and costs one gh `run list`
    call PER FLEET REPO (the per-run job lookups only happen once something is already queued past
    the threshold in some repo).

    Detects on QUEUED-AGE rather than "0 runners online" deliberately, so it also catches a WEDGED
    pool (runners online but not picking work) — a dead VM is only one of the ways this breaks. The
    runner counts go into the message so whoever gets paged can tell the two apart immediately.

    Scans every entry in ``repos`` (the fleet list) — NOT just ``unified-trading-pm``. That PM-only
    scoping was correct while PM was the only repo whose OWN workflows referenced
    ``runs-on: [self-hosted, glue]``, but ``image-build-validate.yml`` was extracted out of PM into
    the public ``unified-trading-ci`` repo on 2026-08-06 and is now invoked BY every fleet repo's
    promotion PRs via `workflow_call`. A reusable workflow's runner matching resolves against the
    CALLING repo's own run queue (the run itself is created in the caller), not the reusable
    workflow's host repo — so a glue-labelled job triggered from ANY fleet repo's promotion PR
    surfaces in THAT repo's `run list`, never PM's. A PM-only scan would silently miss every one of
    those repos' stuck jobs. SSOT: plans/active/issues/
    image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md. Jobs are confirmed by
    LABEL before paging — a HOSTED job queueing on GitHub's own capacity is not our outage and must
    never page.
    """
    cutoff = now - _dt.timedelta(minutes=queued_minutes)
    stale: list[tuple[str, dict]] = []
    for repo in repos:
        runs = gh_json(
            [
                "run",
                "list",
                "--repo",
                f"{ORG}/{repo}",
                "--status",
                "queued",
                "--limit",
                "50",
                "--json",
                "databaseId,createdAt,workflowName,url",
            ]
        )
        if not isinstance(runs, list):
            continue
        for r in runs:
            if isinstance(r, dict) and r.get("createdAt") and _parse_ts(r["createdAt"]) < cutoff:
                stale.append((repo, r))
    if not stale:
        return None

    starved: list[dict] = []
    for repo, run in stale:
        payload = gh_json(["api", f"/repos/{ORG}/{repo}/actions/runs/{run['databaseId']}/jobs"])
        if not isinstance(payload, dict):
            continue
        jobs = payload.get("jobs")
        if not isinstance(jobs, list):
            continue
        for job in jobs:
            if not isinstance(job, dict) or job.get("status") != "queued":
                continue
            # jobs API: labels are plain strings (cf. the runners API's objects).
            labels = {str(x) for x in (job.get("labels") or [])}
            if labels & _GLUE_LABELS:
                starved.append(
                    {
                        "repo": repo,
                        "workflow": run.get("workflowName") or "?",
                        "url": run.get("url") or "",
                        "age_min": int((now - _parse_ts(run["createdAt"])).total_seconds() // 60),
                    }
                )
                break  # one starved job is enough to indict the run
    if not starved:
        return None

    counts = _glue_runner_counts()
    total_online = sum(online for online, _ in counts.values())
    if total_online == 0:
        diagnosis = "0 runners ONLINE → the glue VM is down or the runner service is stopped."
    else:
        diagnosis = "runners ARE online but jobs are not draining → the pool is wedged or saturated."
    return {
        "count": len(starved),
        "oldest_min": max(s["age_min"] for s in starved),
        "url": next((s["url"] for s in starved if s["url"]), ""),
        "workflows": ", ".join(sorted({str(s["workflow"]) for s in starved})[:5]),
        "repos": ", ".join(sorted({str(s["repo"]) for s in starved})[:5]),
        "runner_state": " · ".join(
            f"{label} {online} online/{idle} idle" for label, (online, idle) in sorted(counts.items())
        ),
        "diagnosis": diagnosis,
    }


def _log_failed_excerpt(repo: str, run_id: int, *, max_lines: int = 10, max_chars: int = 500) -> str:
    """Best-effort tail of a run's failed-step logs — the actionable error lines.

    `gh run view --log-failed` streams only the failed steps' logs; we keep the last
    non-blank lines (where the actual error usually is), strip the leading
    `<job>\\t<step>\\t<ts>` prefixes gh prepends, and truncate hard so a Slack body never
    balloons. Returns "" on any error (never raises — enrichment is additive).
    """
    if not run_id:
        return ""
    proc = subprocess.run(
        ["gh", "run", "view", str(run_id), "--repo", f"{ORG}/{repo}", "--log-failed"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0 or not proc.stdout:
        return ""
    cleaned: list[str] = []
    for raw_line in proc.stdout.splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        # gh prefixes each line with "<job>\t<step>\t<iso-ts> ". Drop it for readability.
        parts = line.split("\t")
        cleaned.append(parts[-1].strip() if len(parts) >= 3 else line)
    tail = "\n".join(cleaned[-max_lines:])
    return tail[-max_chars:] if len(tail) > max_chars else tail


def failure_reason(repo: str, run_id: int) -> dict:
    """Resolve WHY a run failed: the failed job(s)/step(s) + a short log excerpt.

    Turns an ad-hoc "<workflow> (failure)" line into an actionable one. Best-effort —
    any gh/network failure yields empty fields and the alert still posts (just without
    the extra reason). Network-doing; the pure rendering lives in build_report.
    """
    reason: dict = {"failed_jobs": [], "log_excerpt": ""}
    if not run_id:
        return reason
    data = gh_json(["run", "view", str(run_id), "--repo", f"{ORG}/{repo}", "--json", "jobs"])
    if isinstance(data, dict):
        for job in data.get("jobs") or []:
            if not isinstance(job, dict) or job.get("conclusion") not in _FAIL_CONCLUSIONS:
                continue
            name = job.get("name") or "?"
            failed_step = next(
                (
                    s.get("name")
                    for s in (job.get("steps") or [])
                    if isinstance(s, dict) and s.get("conclusion") in _FAIL_CONCLUSIONS
                ),
                None,
            )
            reason["failed_jobs"].append(f"{name} → {failed_step}" if failed_step else str(name))
    reason["log_excerpt"] = _log_failed_excerpt(repo, run_id)
    return reason


def enrich_failure_reasons(transitions: list[dict]) -> None:
    """Attach `failed_jobs` + `log_excerpt` to each `failing` transition (in place).

    Only failing transitions are enriched (recoveries need no reason); each is rare, so
    the extra gh calls are bounded. Mutates the dicts so build_report can render them.
    """
    for t in transitions:
        if t.get("kind") != "failing":
            continue
        reason = failure_reason(t["repo"], t.get("run_id") or 0)
        t["failed_jobs"] = reason["failed_jobs"]
        t["log_excerpt"] = reason["log_excerpt"]


def build_report(
    transitions: list[dict],
    stuck: list[dict],
    resolved: list[dict] | None = None,
    billing: dict | None = None,
) -> tuple[bool, str, str]:
    """Return (alert, severity, mrkdwn_report)."""
    resolved = resolved or []
    failing = [t for t in transitions if t["kind"] == "failing" and not t.get("flapping")]
    recovered = [t for t in transitions if t["kind"] == "recovered" and not t.get("flapping")]
    flapping = [t for t in transitions if t.get("flapping")]

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
            # Reason, not ad-hoc: which job/step failed + a short log excerpt (N1).
            failed_jobs = t.get("failed_jobs") or []
            if failed_jobs:
                lines.append(f"      ↳ failed: {', '.join(failed_jobs[:4])}")
            excerpt = t.get("log_excerpt") or ""
            if excerpt:
                lines.append(f"      ```{excerpt}```")
    if recovered:
        lines.append(f":white_check_mark: *{len(recovered)} workflow(s) RECOVERED:*")
        for t in recovered:
            pusher = f"👤 pushed by {t['pusher_name']} [{t['pusher_role']}]"
            lines.append(f"  • `{t['repo']}`@`{t['branch']}` — {t['workflow']} <{t['url']}|run>  {pusher}")
    if stuck:
        # Error-pointer standard (alert_quality_audit_2026_06_18): header = WHAT + number; each line
        # carries the load-bearing facts (repo / PR# / state / age / auto-merge) + the ONE correct
        # deep-link — the PR itself is the GitHub-authoritative surface for a wedged promotion. The
        # `stuck` list reaching here is already the NEW (not-yet-handed-off) subset (main() filters
        # out PRs carrying the escalation-dispatched label), so this no longer re-pages a PR a worker
        # already owns. State is named so it self-classifies: CONFLICTING/DIRTY = a merge wall;
        # BLOCKED = a failed/missing required check.
        lines.append(f":hourglass_flowing_sand: *{len(stuck)} promotion PR(s) STUCK (wedged, not yet handed off):*")
        for s in stuck:
            am = "auto-merge ON" if s["auto_merge"] else "auto-merge OFF"
            zero_tag = " :no_entry: ZERO CHECK RUNS" if s.get("zero_checks") else ""
            lines.append(
                f"  • `{s['repo']}` #{s['number']} {s['head']}→{s['base']} — "
                f"{s['state']} {s['age_min']}m, {am}{zero_tag} → <{s['url']}|open PR>"
            )
    if resolved:
        lines.append(f":ballot_box_with_check: *{len(resolved)} promotion PR(s) RESOLVED (merged/closed):*")
        for r in resolved:
            verb = "merged" if r["merged"] else "closed"
            lines.append(f"  • `{r['repo']}` #{r['number']} {r['head']}→{r['base']} {verb} <{r['url']}|PR>")
    if flapping:
        lines.append(
            f":zap: *{len(flapping)} workflow(s) FLAPPING (oscillating fail↔success — "
            f"alert rate-limited to {RENAG_FLAPPING_MIN}m):*"
        )
        for t in flapping:
            lines.append(
                f"  • `{t['repo']}`@`{t['branch']}` — {t['workflow']} ({t.get('conclusion')}) "
                f"<{t.get('url')}|run>  👤 {t.get('pusher_name', '?')} [{t.get('pusher_role', '?')}]"
            )

    alert = bool(failing or stuck or billing)  # recoveries/resolutions alone post as INFO, not a page
    severity = "CRITICAL" if (failing or stuck or billing) else "INFO"
    report = "\n".join(lines) if lines else "No CI transitions, stuck PRs, or resolutions detected."
    return (alert or bool(recovered) or bool(resolved) or bool(flapping)), severity, report


def _wf_slug(name: str) -> str:
    """Stable, dedup-key-safe slug for a workflow name (lowercase alnum, dashes elsewhere)."""
    return "".join(c if c.isalnum() else "-" for c in str(name).lower()).strip("-") or "wf"


def build_alert_items(
    currently_failing: list[dict],
    recovered: list[dict],
    stuck: list[dict],
    resolved: list[dict] | None = None,
    billing: dict | None = None,
    stale_quarantine: list[dict] | None = None,
    glue_starvation: dict | None = None,
) -> list[dict]:
    """Per-condition alert items for the carrier's matrix notify (Phase 5 re-nag).

    Each item is ``{key, severity, cooldown_min, message, url}``: ``key`` is the stable
    ``dedup_key`` the carrier re-arms on, ``cooldown_min`` the severity-scaled re-nag cadence
    (see the ``RENAG_*`` constants). Pure (no IO) → unit-testable. ``ci-failure-watcher.yml``
    fans each item to ``notify-slack.yml`` with its own ``dedup_key``+``cooldown_min``, so each
    open condition re-pages independently on its own MTTR clock and a recovered/resolved bookend
    fires once on a distinct short-cooldown key. SSOT: alert_quality_overhaul_2026_06_18 § Phase 5.
    """
    items: list[dict] = []
    if billing:
        # Fleet frozen — ONE unmissable line, fast re-nag (it blocks everything).
        items.append(
            {
                "key": "ci-billing-block",
                "severity": "CRITICAL",
                "cooldown_min": RENAG_FLEET_FROZEN_MIN,
                "url": billing.get("url") or "",
                "message": (
                    ":rotating_light: *GitHub Actions BILLING BLOCK — all CI is FROZEN fleet-wide.* "
                    "Every job fails at 'Set up job' (spending limit / failed payment). "
                    "FIX: GitHub → Settings → Billing & plans (raise the Actions spending limit). "
                    f"Evidence: `{billing.get('repo')}` {billing.get('workflow')} <{billing.get('url')}|run>."
                ),
            }
        )
    for t in currently_failing:
        if t.get("flapping"):
            # Flapping workflow: downgrade to WARNING with a long cooldown so the channel
            # is not flooded by a flaky oscillation, while the pattern still surfaces once
            # every RENAG_FLAPPING_MIN minutes under a distinct "ci-flap:" key.
            items.append(
                {
                    "key": f"ci-flap:{t['repo']}:{t['branch']}:{_wf_slug(t['workflow'])}",
                    "severity": "WARNING",
                    "cooldown_min": RENAG_FLAPPING_MIN,
                    "url": t.get("url") or "",
                    "message": (
                        f":zap: *CI FLAPPING ({t.get('age_min', 0)}m)* — `{t['repo']}`@`{t['branch']}` "
                        f"{t['workflow']} oscillating fail↔success (≥{FLAP_TRANSITION_THRESHOLD} "
                        f"transitions in last {FLAP_DETECT_RUNS} runs) <{t.get('url')}|run>  "
                        f"👤 {t.get('pusher_name', '?')} [{t.get('pusher_role', '?')}]"
                    ),
                }
            )
            continue
        line = (
            f":x: *CI FAILING ({t.get('age_min', 0)}m)* — `{t['repo']}`@`{t['branch']}` "
            f"{t['workflow']} ({t.get('conclusion')}) <{t.get('url')}|run>  "
            f"👤 {t.get('pusher_name', '?')} [{t.get('pusher_role', '?')}]"
        )
        failed_jobs = t.get("failed_jobs") or []
        if failed_jobs:
            line += f"\n      ↳ failed: {', '.join(failed_jobs[:4])}"
        excerpt = t.get("log_excerpt") or ""
        if excerpt:
            line += f"\n      ```{excerpt}```"
        items.append(
            {
                "key": f"ci-fail:{t['repo']}:{t['branch']}:{_wf_slug(t['workflow'])}",
                "severity": "CRITICAL",
                "cooldown_min": RENAG_WORKFLOW_FAIL_MIN,
                "url": t.get("url") or "",
                "message": line,
            }
        )
    for s in stuck:
        am = "auto-merge ON" if s.get("auto_merge") else "auto-merge OFF"
        if s.get("zero_checks"):
            # L1581: staging head has ZERO check runs — all CI is dark (not just v2-absent,
            # but nothing validated the head commit). Use a distinct dedup key so this alert
            # re-nags independently from the generic stuck-pr path and is actionable on its
            # own MTTR clock. CRITICAL: the PR could auto-merge with zero validation.
            items.append(
                {
                    "key": f"zero-checks:{s['repo']}:{s['number']}",
                    "severity": "CRITICAL",
                    "cooldown_min": RENAG_WORKFLOW_FAIL_MIN,
                    "url": s.get("url") or "",
                    "message": (
                        f":no_entry: *STAGING HEAD — ZERO CHECK RUNS ({s.get('age_min')}m)* — "
                        f"`{s['repo']}` #{s['number']} {s.get('head')}→{s.get('base')} "
                        f"has NO CI attached at all (statusCheckRollup empty). "
                        f"Possible causes: billing exhaustion, global CI suppression, or a brand-new head "
                        f"that predates Actions attachment. {am}. "
                        f"FIX: verify Actions quota → then close+reopen the PR to re-trigger CI. "
                        f"→ <{s.get('url')}|open PR>"
                    ),
                }
            )
        else:
            items.append(
                {
                    "key": f"stuck-pr:{s['repo']}:{s['number']}",
                    "severity": "CRITICAL",
                    "cooldown_min": RENAG_STUCK_PR_MIN,
                    "url": s.get("url") or "",
                    "message": (
                        f":hourglass_flowing_sand: *PROMOTION PR STUCK ({s.get('age_min')}m)* — "
                        f"`{s['repo']}` #{s['number']} {s.get('head')}→{s.get('base')} "
                        f"{s.get('state')}, {am} → <{s.get('url')}|open PR>"
                    ),
                }
            )
    for t in recovered:
        items.append(
            {
                "key": f"ci-recovered:{t['repo']}:{t['branch']}:{_wf_slug(t['workflow'])}",
                "severity": "INFO",
                "cooldown_min": BOOKEND_COOLDOWN_MIN,
                "url": t.get("url") or "",
                "message": (
                    f":white_check_mark: *CI RECOVERED* — `{t['repo']}`@`{t['branch']}` "
                    f"{t['workflow']} <{t.get('url')}|run>"
                ),
            }
        )
    for r in resolved or []:
        verb = "merged" if r.get("merged") else "closed"
        items.append(
            {
                "key": f"resolved-pr:{r['repo']}:{r['number']}",
                "severity": "INFO",
                "cooldown_min": BOOKEND_COOLDOWN_MIN,
                "url": r.get("url") or "",
                "message": (
                    f":ballot_box_with_check: *PROMOTION PR RESOLVED* — `{r['repo']}` #{r['number']} "
                    f"{r.get('head')}→{r.get('base')} {verb} <{r.get('url')}|PR>"
                ),
            }
        )
    for q in stale_quarantine or []:
        items.append(
            {
                "key": f"stale-quarantine:{q['repo']}",
                "severity": "WARNING",
                "cooldown_min": RENAG_STUCK_PR_MIN,
                "url": "",
                "message": (
                    f":warning: *PROMOTION QUARANTINE stale ({q['age_min']}m)* — `{q['repo']}` "
                    f"has been quarantined since {q['since']} after {q['attempts']} consecutive "
                    f"promotion failures. Check `workspace-manifest.json::promotion_quarantine` — "
                    f"the quarantine auto-clears on next successful promotion."
                ),
            }
        )
    if glue_starvation:
        # One line for the whole pool — every starved job shares one root cause, so per-job items
        # would be pure noise. CRITICAL + a 15-min re-nag: silent until GitHub kills the jobs at 24h,
        # and by then the ci_status transitions are gone.
        items.append(
            {
                "key": "glue-runners-starved",
                "severity": "CRITICAL",
                "cooldown_min": RENAG_GLUE_STARVED_MIN,
                "url": glue_starvation.get("url") or "",
                "message": (
                    f":rotating_light: *Self-hosted GLUE runners are NOT draining* — "
                    f"{glue_starvation.get('count')} job(s) queued in "
                    f"`{glue_starvation.get('repos') or _PM_DISPATCH_REPO}`, oldest "
                    f"*{glue_starvation.get('oldest_min')}m*. {glue_starvation.get('diagnosis')} "
                    f"Runners: {glue_starvation.get('runner_state')}. "
                    f"Waiting: {glue_starvation.get('workflows')}. "
                    f"GitHub KILLS a queued job at *24h* → ci_status transitions LOST → stale "
                    f"Firestore → blocked promotes (MAIN_GREEN is the dep-on-main gate). "
                    f"FIX: start the VM, then `systemctl restart 'github-glue-runner@glue-*'` / "
                    f"`@writer-*`; verify `setup-glue-runners.sh status`. ROLLBACK: flip the "
                    f"affected `runs-on` back to `ubuntu-latest`. "
                    f"<{glue_starvation.get('url')}|queued run>"
                ),
            }
        )
    return items


def write_github_output(alert: bool, severity: str, report: str, alert_items: list[dict] | None = None) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    with open(out_path, "a", encoding="utf-8") as fh:
        fh.write(f"alert={'true' if alert else 'false'}\n")
        fh.write(f"severity={severity}\n")
        fh.write("report<<__RPT__\n")
        fh.write(report + "\n")
        fh.write("__RPT__\n")
        # Per-condition alert items for the matrix notify (Phase 5). Compact single-line JSON
        # (messages embed \n, which JSON escapes — so the value stays one line). Default '[]'
        # so the workflow's `alerts != '[]'` guard skips notify when nothing is open.
        fh.write(f"alerts={json.dumps(alert_items or [], separators=(',', ':'), ensure_ascii=False)}\n")


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


# Hidden marker comment encoding the blocking-reason signature (`_blocking_signature`) an
# escalation was dispatched for. Deliberately NOT a change to the `_ESCALATION_LABEL` string
# itself — other consumers (agent-runner.yml, the conflict-resolution/dep-update-conflict flow)
# key off that exact label for their OWN, unrelated, presence-only dedup and must not be affected.
_ESCALATION_REASON_PREFIX = "<!-- ci-watcher:escalation-reason:"


def _escalation_reason_marker(signature: str) -> str:
    """The exact hidden marker comment text encoding one blocking-reason ``signature``."""
    return f"{_ESCALATION_REASON_PREFIX}{signature} -->"


def _pr_escalation_suppressed(repo: str, number: int, signature: str) -> bool:
    """True if this stuck PR should stay suppressed — already handed off FOR ITS CURRENT
    BLOCKING REASON (``signature``), not merely "carries the label at some point in its history".

    The ``escalation-dispatched`` label is a coarse, PERMANENT marker (applied once, on confirmed
    spawn, and never removed) — treating label presence alone as "already handled forever" means a
    PR escalated+fixed for reason A silently stops paging/escalating when it later becomes blocked
    for an UNRELATED reason B. Measured 2026-08-07:
    ``batch-live-reconciliation-service#315`` was correctly escalated+labelled for a RUNS_ON
    workflow-yaml bug, fixed — then became blocked again for an unrelated dead-glue-runner
    stuck-QUEUED check, and the watcher stayed silent solely because the label was still present.

    Fix: gate suppression on the label PLUS a reason-signature marker comment (posted by
    ``_post_escalation_reason_marker`` at dispatch time) matching the CURRENT ``signature``.
    Grandfathered: a labelled PR with NO reason-marker comment at all (escalated before this
    per-reason tracking existed, or via the label-only ``agent-runner.yml`` path used for
    non-CI-watcher wall types) stays suppressed unconditionally — so shipping this fix cannot
    itself trigger a re-page/re-escalate storm across every PR that already carries the label.
    Once a PR has gone through THIS mechanism at least once, a later signature MISMATCH re-arms
    it. Best-effort: any gh/read error → False (a PR we can't read stays PAGEABLE /
    re-escalatable — mirrors the label-presence check's prior fail-open convention).
    """
    data = gh_json(["pr", "view", str(number), "--repo", f"{ORG}/{repo}", "--json", "labels,comments"])
    if not isinstance(data, dict):
        return False
    labels = data.get("labels")
    has_label = isinstance(labels, list) and any(
        isinstance(lbl, dict) and lbl.get("name") == _ESCALATION_LABEL for lbl in labels
    )
    if not has_label:
        return False
    reason_bodies = [
        str(c.get("body") or "")
        for c in (data.get("comments") or [])
        if isinstance(c, dict) and _ESCALATION_REASON_PREFIX in str(c.get("body") or "")
    ]
    if not reason_bodies:
        return True  # grandfathered legacy/non-reason-tracked label — unchanged old behaviour
    marker = _escalation_reason_marker(signature)
    return any(marker in body for body in reason_bodies)


def _post_escalation_reason_marker(repo: str, number: int, signature: str) -> None:
    """Best-effort, DEDUPED: record ``signature`` as a hidden marker comment on this PR so a LATER
    escalation for a DIFFERENT reason is not silently suppressed by the permanent, presence-only
    ``_ESCALATION_LABEL`` — see ``_pr_escalation_suppressed``. Deduped against existing comments
    (not one post per retry tick): a PR parked in the 503/no-headroom retry loop is a dispatch
    candidate every ``*/15`` tick until a slot frees, and each retry reaches this same call.
    """
    marker = _escalation_reason_marker(signature)
    data = gh_json(["pr", "view", str(number), "--repo", f"{ORG}/{repo}", "--json", "comments"])
    if isinstance(data, dict):
        for c in data.get("comments") or []:
            if isinstance(c, dict) and marker in str(c.get("body") or ""):
                return  # already recorded for this exact reason — don't re-comment every tick
    subprocess.run(
        [
            "gh",
            "pr",
            "comment",
            str(number),
            "--repo",
            f"{ORG}/{repo}",
            "--body",
            f"{marker}\n🔖 ci-failure-watcher: escalating for the CURRENT blocking reason "
            "(mergeStateStatus + the failing/queued required check(s)). This marker scopes the "
            "`escalation-dispatched` idempotency label to THIS reason — a later escalation for a "
            "DIFFERENT reason will re-page/re-escalate instead of staying silently suppressed.",
        ],
        capture_output=True,
        text=True,
    )


def stuck_prs_to_page(stuck: list[dict], already_escalated: set[tuple[str, int]]) -> list[dict]:
    """Pure: the subset of stuck PRs that should PAGE Slack — i.e. NOT already handed off.

    Gates the stuck-PR Slack line on the ``escalation-dispatched`` label
    (alert_quality_audit_2026_06_18): once a stuck PR has been handed to a worker, its lifecycle
    is owned by that worker + the agent-orchestrator server (S4 pages RESOLVED/ABANDONED), so the
    */15 watcher must NOT re-page it every tick (the operator's repeated-"stuck PR" complaint).
    A stuck PR with no escalation label is still NEW → page it. No IO (the label set is injected),
    so this is unit-testable without ``gh``/network.
    """
    return [s for s in stuck if (s.get("repo"), int(s.get("number", 0))) not in already_escalated]


def _already_escalated_set(stuck: list[dict]) -> set[tuple[str, int]]:
    """IO wrapper: derive the identity set of stuck PRs still suppressed FOR THEIR CURRENT
    blocking reason (see ``_pr_escalation_suppressed`` — label presence alone is no longer
    sufficient; a PR whose blocking reason has changed since it was labelled is NOT in this set).

    Bounded: at most one ``gh`` call per stuck PR, and the stuck list is already tiny (promotion
    PRs past the stuck threshold).
    """
    out: set[tuple[str, int]] = set()
    for s in stuck:
        repo, number = str(s.get("repo") or ""), int(s.get("number", 0))
        signature = str(s.get("blocking_signature") or "")
        if repo and number and _pr_escalation_suppressed(repo, number, signature):
            out.add((repo, number))
    return out


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
    #
    # DO record the reason signature here (unlike the label, this is safe to write eagerly): it
    # is additive bookkeeping consumed only by `_pr_escalation_suppressed`, deduped so a PR parked
    # in the 503-retry loop gets exactly one marker comment, not one per tick (2026-08-07 fix).
    signature = str(s.get("blocking_signature") or "")
    if signature:
        _post_escalation_reason_marker(repo, number, signature)
    print(f"  -> dispatched {repo}#{number} ({s.get('state')}) to orchestrator ({wall_type}); awaiting spawn-confirm")
    return True


def escalate_stuck_prs(stuck: list[dict], *, dry_run: bool = True) -> list[dict]:
    """Hand each conflict-stuck promotion PR to the orchestrator (idempotent per blocking reason).

    Returns the PRs dispatched (in ``dry_run``, the PRs that WOULD be dispatched — used
    by the report/tests). The suppression check happens per-candidate so a non-conflict stuck
    PR (e.g. BLOCKED) never triggers a ``gh`` call.
    """
    dispatched: list[dict] = []
    # Conflict-stuck (CONFLICTING/DIRTY) → merge_conflict; BLOCKED-with-failed-check → sit_failure.
    # Both reuse the same per-PR reason-scoped idempotency. _dispatch_escalation derives the
    # wall_type from state.
    candidates = conflict_prs_to_escalate(stuck, already_escalated=set()) + blocked_failing_prs_to_escalate(
        stuck, already_escalated=set()
    )
    for s in candidates:
        repo, number = s["repo"], int(s["number"])
        signature = str(s.get("blocking_signature") or "")
        if _pr_escalation_suppressed(repo, number, signature):
            continue  # already handled FOR THIS REASON — don't re-dispatch
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


def _close_reopen_pr(repo: str, number: int) -> bool:
    """Close then reopen a PR to re-fire its ``pull_request`` event (the v2 re-trigger). Returns
    True only if BOTH succeeded.

    RE-ARMS auto-merge afterwards. **Closing a PR DISARMS auto-merge and reopening does NOT restore
    it** (measured 2026-07-16: unified-trading-library#583 and instruments-service#812 both read
    ``autoMerge=true`` before a close+reopen and ``autoMerge=false`` after; both then sat CLEAN —
    every check green, nothing to do — and simply never merged until auto-merge was re-armed by
    hand). Without this, EVERY recovery signature below "succeeds" into a green PR that never
    merges: the deadlock changes shape from BLOCKED to CLEAN-but-inert and stops being detected at
    all (``_STUCK_STATES`` has no CLEAN), which is strictly worse than not recovering. The fleet
    promote bot does not save us either — it only arms inside its ``gh pr create`` branch, so an
    already-open PR is never re-armed.
    """
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
        # SQUASH + delete-branch mirrors the fleet promote bot's own arm (LDR carries backmerge
        # merge commits, so rebase-merge is structurally impossible). Best-effort + LOUD: a failed
        # re-arm leaves a recoverable CLEAN PR rather than a silent inert one.
        _arm = subprocess.run(
            [
                "gh",
                "pr",
                "merge",
                str(number),
                "--repo",
                f"{ORG}/{repo}",
                "--auto",
                "--squash",
            ],
            capture_output=True,
            text=True,
        )
        if _arm.returncode != 0:
            print(
                f"  ! {repo}#{number}: close+reopen OK but auto-merge RE-ARM failed "
                f"({(_arm.stderr or '').strip()[:120]}) — merge manually or the PR sits CLEAN+inert",
                file=sys.stderr,
            )
    return closed and reopened


def _v2_failure_is_stale(repo: str, head_oid: str) -> bool:
    """True when the PR's FAILED ``quality-gates-v2`` has since been disproved on the SAME head sha.

    The poison-window deadlock (measured 2026-07-16). A transient breakage in a DEPENDENCY reds
    every repo's gate for a few minutes; any promote PR whose ``pull_request`` v2 happens to run
    inside that window concludes FAILURE and is then stranded FOREVER:

      * the dep breakage is fixed minutes later, so the content is green again;
      * ``workflow_dispatch`` re-runs on the exact head DO conclude success, but a dispatch run's
        check suite is not associated with the PR, so the required context keeps the stale FAILURE
        (already documented for the ``[skip ci]`` path above — same root, different trigger);
      * ``auto_recover_stuck_prs`` skips any PR with a ``failed_check`` (left for the escalate
        path, correctly — a genuinely-red PR must not be re-fired in a loop);
      * so nothing self-heals and the repo silently stops promoting.

    Real trace: PM commit 2eb232971 (12:43) broke a plan cross-reference → the fatal, non-slice-gated
    ``run_validators`` check failed lint-codex in EVERY repo that cloned PM's LDR. The fleet promote
    bot's 12:45 PRs (unified-trading-library#583, instruments-service#812) ran v2 inside that window
    → FAILURE. slot-6 fixed the ref by ~13:00 and a 13:00 dispatch on the identical head concluded
    success — yet both PRs sat BLOCKED with auto-merge armed for 3.5h, surfacing only as anonymous
    "PROMOTION LAG". 17 minutes of breakage cost hours of fleet-wide stall.

    The discriminator is content, not time: ask whether a LATER v2 run on this exact head sha
    concluded success. If yes the tree is proven green and only the PR-context check is stale →
    deterministically recoverable by re-firing ``pull_request`` (close+reopen). If no such run
    exists we return False and the PR stays on the escalate path, so a genuinely-failing PR is
    never re-fired. Same-sha comparison means this cannot mistake a later FIX-commit's green for
    this head's.
    """
    if not head_oid:
        return False
    runs = gh_json(
        [
            "run",
            "list",
            "--repo",
            f"{ORG}/{repo}",
            "--workflow",
            "quality-gates-v2.yml",
            "--limit",
            "40",
            "--json",
            "headSha,status,conclusion",
        ]
    )
    if not isinstance(runs, list):
        return False
    for r in runs:
        if not isinstance(r, dict):
            continue
        if str(r.get("headSha") or "") != head_oid:
            continue
        if str(r.get("status") or "") != "completed":
            continue
        if str(r.get("conclusion") or "").lower() == "success":
            return True  # this exact tree passed v2 → the PR's failed check is stale
    return False


def _recently_action_recovered(repo: str, number: int, *, now: _dt.datetime | None = None) -> bool:
    """True if we posted an ``action_required``-recovery marker comment on this PR within the
    bound window — so a deterministically-``action_required`` head is not close+reopened every
    tick (the v2-never-reported case can't loop because v2 becomes permanently present after
    reopen; ``action_required`` can re-conclude ``action_required``, so it needs this bound)."""
    data = gh_json(["pr", "view", str(number), "--repo", f"{ORG}/{repo}", "--json", "comments"])
    if not isinstance(data, dict):
        return False
    ref = now or _dt.datetime.now(_dt.UTC)
    cutoff = ref - _dt.timedelta(minutes=_ACTION_REQ_RECOVER_WINDOW_MIN)
    for comment in data.get("comments") or []:
        if not isinstance(comment, dict) or _ACTION_REQ_MARKER not in str(comment.get("body") or ""):
            continue
        try:
            if _parse_ts(str(comment.get("createdAt") or "")) >= cutoff:
                return True
        except ValueError:
            continue
    return False


def auto_recover_stuck_prs(stuck: list[dict], *, dry_run: bool = False) -> list[dict]:
    """Deterministically recover three promotion-PR deadlocks (no worker needed).

    A promotion PR sits BLOCKED with auto-merge armed but unable to fire when the required
    quality-gates-v2 check is non-green for a reason that is NOT a live content failure. THREE such
    signatures (all gated to BLOCKED; a genuinely-failing PR is still left for the escalate path —
    signature (3) is the only one that touches a failed_check, and only after PROVING the failure
    has been disproved on the identical head sha):

      (1) v2 NEVER reported (``v2_present`` False) — the v2-never-fired deadlock (head pushed by
          a token that suppresses the pull_request event). Deterministic → recover.
      (2) v2 PRESENT but concluded ``action_required`` (``v2_action_required`` True) — the
          2026-06-17 finding: the required check is neither green nor red, the v2-absent path
          never triggers (v2 IS present), and the PR strands. A fresh ``pull_request`` run
          concludes ``success`` (verified live 5/5). Intermittent (the same head went success
          then action_required), so its retries are BOUNDED by a marker comment (see below).

    Recovery MECHANISM by head-commit kind:
      - default (head pushed by a workflow-suppressing token, message clean) → close+reopen,
        which re-fires the ``pull_request`` event. For (1) v2 then appears in the rollup so the
        next tick won't re-fire (no loop). For (2) the re-fired run can re-conclude
        ``action_required`` (unlike (1) it does NOT become permanently present), so we post a
        ``_ACTION_REQ_MARKER`` comment and skip if one is within
        ``_ACTION_REQ_RECOVER_WINDOW_MIN`` — bounding it to ~1 retry/window (no every-tick thrash).
      - CI-suppression-token head (``[skip ci]``/``[ci skip]``/… anywhere in the message — the
        semver bump / dep pin / a manual recovery commit that merely MENTIONS the token) →
        close+reopen is INEFFECTIVE (the re-fired pull_request is equally suppressed) and a
        ``workflow_dispatch`` run does NOT satisfy the PR's required check (its check suite is
        not associated with the PR — verified live 2026-06-10: 3x green dispatch runs on the
        exact head SHA, PR stayed BLOCKED). Recover by SUPERSEDING the head with an empty
        clean-message commit (same tree) via the git-data API → real push/pull_request runs
        fire and count. The new head changes the PR head SHA, so the next tick sees v2
        in-flight/green (no loop); a head already carrying our recovery marker is never
        stacked with a second recovery commit. (A ``v2_action_required`` head ran v2 → it is
        never CI-suppressed, so it always takes the close+reopen path.)
      - STALE-failure head (signature 3) → close+reopen; the re-fired pull_request concludes
        success (the dep breakage is gone), which clears failed_check so the next tick skips it.

    EVERY path re-arms auto-merge — see ``_close_reopen_pr``: closing DISARMS auto-merge and
    reopening does NOT restore it, so an un-re-armed "recovery" merely converts BLOCKED into
    CLEAN-but-inert — which no detector looks for (``_STUCK_STATES`` has no CLEAN).
    """
    recovered: list[dict] = []
    for s in stuck:
        v2_action_required = bool(s.get("v2_action_required"))
        if s.get("state") != "BLOCKED":
            continue
        # Signature (3) — STALE failure (poison-window). A failed_check normally means "genuinely
        # red → escalate path owns it", and that stays true. The ONE exception is a failure the
        # same head sha has since DISPROVED with a green v2: the content is proven fine and only
        # the PR-context check is stale, so re-firing is deterministic, not a retry-loop. Checked
        # BEFORE the failed_check bail-out, and only for promotion heads, so it can never re-fire
        # a genuinely-failing PR. See _v2_failure_is_stale for the measured 3.5h trace.
        stale_failure = False
        if s.get("failed_check"):
            if s.get("head") not in _PROMOTION_HEADS:
                continue
            if not _v2_failure_is_stale(s["repo"], s.get("head_oid") or ""):
                continue  # genuinely red → leave it for escalation (unchanged behaviour)
            stale_failure = True
        # v2 PRESENT + NOT action_required + NOT a stale failure → in-flight / genuinely
        # green-pending; recovering would loop. v2 ABSENT, action_required, or stale-failed →
        # recoverable.
        if s.get("v2_present") and not v2_action_required and not stale_failure:
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
        if v2_action_required and not skip_ci_head:
            # Signature (2): bound the retries (the re-fired run can re-conclude action_required).
            if _recently_action_recovered(repo, number):
                print(
                    f"  action_required {repo}#{number}: close+reopened within "
                    f"{_ACTION_REQ_RECOVER_WINDOW_MIN}m already — leaving the in-flight v2 (bounded)"
                )
                continue
            if _close_reopen_pr(repo, number):
                subprocess.run(
                    [
                        "gh",
                        "pr",
                        "comment",
                        str(number),
                        "--repo",
                        f"{ORG}/{repo}",
                        "--body",
                        f"{_ACTION_REQ_MARKER}\n♻️ ci-failure-watcher: `quality-gates-v2` concluded "
                        "`action_required` (not a content failure, not a fork-approval) → close+reopen to "
                        "re-fire a `pull_request` v2 run (proven recovery 2026-06-17). Bounded to ~1 "
                        f"retry / {_ACTION_REQ_RECOVER_WINDOW_MIN}m.",
                    ],
                    capture_output=True,
                    text=True,
                )
                print(
                    f"  auto-recovered {repo}#{number}: close+reopen → fresh pull_request v2 "
                    "(v2 concluded action_required; bounded)"
                )
                recovered.append(s)
            continue
        if stale_failure and not skip_ci_head:
            # Signature (3): the identical head already passed v2 — only the PR-context check is
            # stale. close+reopen re-fires `pull_request`; it concludes success (the dep breakage
            # that caused the original red is long gone) and the re-armed auto-merge then fires.
            # Cannot loop: a re-fired green makes failed_check falsy, so the next tick skips it.
            if _close_reopen_pr(repo, number):
                subprocess.run(
                    [
                        "gh",
                        "pr",
                        "comment",
                        str(number),
                        "--repo",
                        f"{ORG}/{repo}",
                        "--body",
                        "♻️ ci-failure-watcher: `quality-gates-v2` FAILED on this head, but a later v2 run on the "
                        "**same head SHA** concluded `success` — a transient DEPENDENCY breakage red-lined the "
                        "original `pull_request` run and the content has been green since. A `workflow_dispatch` "
                        "green does not satisfy the PR's required context, so close+reopen re-fires it "
                        "(auto-merge re-armed).",
                    ],
                    capture_output=True,
                    text=True,
                )
                print(
                    f"  auto-recovered {repo}#{number}: close+reopen → fresh pull_request v2 "
                    "(STALE failure — same head sha already passed v2)"
                )
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
        if _close_reopen_pr(repo, number):
            print(f"  auto-recovered {repo}#{number}: close+reopen → quality-gates-v2 re-fired (v2-never-reported)")
            recovered.append(s)
    return recovered


def _write_firestore_ci_watcher(
    transitions: list[dict],
    stuck: list[dict],
    now_iso: str,
    project_id: str,
) -> None:
    try:  # noqa: fallback-import — Firestore is an optional extra, only needed for the best-effort ledger write
        from google.api_core.exceptions import GoogleAPICallError  # noqa: imports-inside-functions
        from google.cloud import (  # noqa: TID251, RUF100, I001  # noqa: imports-inside-functions  # noqa: cloud-sdk-direct
            firestore,
        )

        client = firestore.Client(project=project_id)
        trans_by_repo: dict[str, list[dict]] = {}
        stuck_by_repo: dict[str, list[dict]] = {}
        for t in transitions:
            repo = str(t.get("repo", ""))  # noqa: qg-empty-fallback
            if repo:
                trans_by_repo.setdefault(repo, []).append({k: v for k, v in t.items() if k != "repo"})
        for s in stuck:
            repo = str(s.get("repo", ""))  # noqa: qg-empty-fallback
            if repo:
                stuck_by_repo.setdefault(repo, []).append({k: v for k, v in s.items() if k != "repo"})
        for repo in set(trans_by_repo) | set(stuck_by_repo):
            doc_ref = client.collection("repo_state").document(repo)
            doc_ref.set(
                {
                    "ci_watcher": {
                        "transitions": trans_by_repo.get(repo, []),
                        "stuck": stuck_by_repo.get(repo, []),
                        "checked_at": now_iso,
                    }
                },
                merge=True,
            )
    except (ImportError, GoogleAPICallError) as exc:  # Firestore unavailable → best-effort write; but make it VISIBLE
        print(f"::warning ::ci-failure-watcher Firestore write failed — ledger may be stale: {exc}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="Watch a single repo instead of the full fleet.")
    parser.add_argument("--limit", type=int, default=25, help="Recent runs to inspect per repo/branch.")
    parser.add_argument("--stuck-minutes", type=int, default=30, help="Age before an un-mergeable PR is 'stuck'.")
    parser.add_argument(
        "--glue-queued-minutes",
        type=int,
        default=GLUE_QUEUED_ALERT_MIN,
        help="Age before a QUEUED self-hosted glue job pages (the VM is down or the pool is wedged).",
    )
    parser.add_argument(
        "--fresh-hours",
        type=float,
        default=2.0,
        help="Only alert on a transition whose latest run is within this many hours "
        "(stateless guard against re-paging ancient dead workflows). Cron is */15m.",
    )
    parser.add_argument(
        "--fail-window-hours",
        type=float,
        default=RENAG_FAIL_WINDOW_HOURS,
        help="Re-nag (Phase 5): re-surface a workflow whose LATEST run is failing and within this "
        "many hours, every tick, so the carrier re-pages it on RENAG_WORKFLOW_FAIL_MIN. Wider than "
        "--fresh-hours (the flip guard) so a persistently-red QG keeps nagging until fixed; bounded "
        "so an ancient/abandoned failure is not re-surfaced forever.",
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
        "--flap-detect-runs",
        type=int,
        default=FLAP_DETECT_RUNS,
        help="Number of recent completed runs to inspect when detecting a flapping workflow "
        "(oscillating fail↔success). Larger values give a longer history window.",
    )
    parser.add_argument(
        "--flap-threshold",
        type=int,
        default=FLAP_TRANSITION_THRESHOLD,
        help="Minimum number of fail↔success transitions in the --flap-detect-runs window "
        "before a workflow is classified as 'flapping' and downgraded to WARNING.",
    )
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
    parser.add_argument(
        "--close-superseded",
        action="store_true",
        help="Auto-close stale LDR→staging/main promote PRs whose content is already in base (0 "
        "changed files in base...live-defi-rollout — superseded by a later quickmerge/rebase). "
        "Level-3 cleanup of the LDR-trunk model. Default OFF — only the cron passes it.",
    )
    args = parser.parse_args()

    repos = [args.repo] if args.repo else REPOS
    now = _parse_ts(args.now) if args.now else _dt.datetime.now(_dt.UTC)

    # Global, account-level: scan first (short-circuits on first hit) so a billing outage
    # is surfaced as ONE alert above the per-workflow failures it would otherwise spam.
    billing = detect_billing_block(repos, now, args.fresh_hours)
    stale_quarantine = detect_stale_quarantine(now)
    # Self-hosted glue pools — scanned across the WHOLE FLEET (not just unified-trading-pm): a
    # glue-labelled reusable-workflow job resolves its runner queue against the CALLING repo, so a
    # starved job triggered from any fleet repo's promotion PR surfaces in THAT repo's run list, not
    # PM's (2026-08-06 image-build-validate.yml extraction to unified-trading-ci). Costs one gh call
    # per fleet repo when nothing is queued, which is the normal state. MUST stay in this hosted
    # watcher: a check for "is the glue VM dead?" that itself ran on the glue VM would queue behind
    # the very outage it exists to report.
    glue_starvation = detect_glue_starvation(repos, now, args.glue_queued_minutes)

    transitions: list[dict] = []
    currently_failing: list[dict] = []
    stuck: list[dict] = []
    resolved: list[dict] = []
    superseded: list[dict] = []
    for repo in repos:
        for branch in WATCHED_BRANCHES:
            transitions.extend(
                detect_transitions(
                    repo,
                    branch,
                    args.limit,
                    now,
                    args.fresh_hours,
                    args.flap_detect_runs,
                    args.flap_threshold,
                )
            )
            # Phase 5: current-failing set (not just flips) so a still-red workflow re-nags.
            currently_failing.extend(
                detect_currently_failing(
                    repo,
                    branch,
                    args.limit,
                    now,
                    args.fail_window_hours,
                    args.flap_detect_runs,
                    args.flap_threshold,
                )
            )
        stuck.extend(detect_stuck_prs(repo, args.stuck_minutes, now))
        if args.resolved_hours > 0:
            resolved.extend(detect_resolved_prs(repo, args.resolved_hours, now))
        if args.close_superseded:
            superseded.extend(detect_superseded_prs(repo))

    enrich_failure_reasons(transitions)  # N1: failed job/step + log excerpt (consolidated log report)
    enrich_failure_reasons(currently_failing)  # same reason enrichment for the per-condition re-nag items

    # Gate the stuck-PR Slack line on the escalation-dispatched label + reason signature
    # (alert_quality_audit_2026_06_18; reason-scoping added 2026-08-07): PAGE only stuck PRs not
    # yet handed off FOR THEIR CURRENT BLOCKING REASON — a worker + the server (S4) own an escalated
    # PR's lifecycle for that reason, so re-paging it every */15 tick is the operator's "stuck PR"
    # repeat noise; but a PR blocked again for an UNRELATED reason after its label was applied must
    # still page (see _pr_escalation_suppressed). The FULL `stuck` list still drives auto-recover +
    # escalate below (those have their own per-PR idempotency). Skip the label/comment lookups
    # entirely on a diagnostic run (--repo/--now without the cron's escalate), so a hand-run never
    # burns gh calls and the page shows everything.
    stuck_to_page = stuck_prs_to_page(stuck, _already_escalated_set(stuck)) if (args.escalate and stuck) else stuck
    alert, severity, report = build_report(transitions, stuck_to_page, resolved, billing)
    print(report)
    # Per-condition items drive the matrix notify (Phase 5 re-nag). The failing items come from
    # the CURRENT-failing set (re-nag every tick via the carrier cooldown), not the one-shot
    # flip; recovered/resolved bookends come from the flip/terminal detectors.
    recovered = [t for t in transitions if t.get("kind") == "recovered"]
    alert_items = build_alert_items(
        currently_failing, recovered, stuck_to_page, resolved, billing, stale_quarantine, glue_starvation
    )
    write_github_output(alert, severity, report, alert_items)

    # Firestore write-through — best-effort; never blocks the watcher on SDK/credential absence.
    gcp_project = os.environ.get("GCP_PROJECT_ID")
    if gcp_project:
        _write_firestore_ci_watcher(transitions, stuck, now.isoformat(), gcp_project)

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
    if args.close_superseded and superseded:
        close_superseded_prs(superseded, dry_run=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
