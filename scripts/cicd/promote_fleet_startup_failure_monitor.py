#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Promote-fleet startup-failure monitor — pages when `ldr-to-main-promote-fleet.yml` or
`ldr-to-main-promote.yml` post 3+ CONSECUTIVE `startup_failure` runs, OR when either has a run
stuck in `status: queued` for an extended period.

Root incident #1 (2026-07-30, RESOLVED 2026-07-31 —
`plans/archive/issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md`): both
workflows returned `conclusion: startup_failure` / `jobs: []` on EVERY tick for ~10h+ (a GitHub
Actions account-level billing wall), silently blocking LDR->main promotion for the ENTIRE
`promotion_model: ldr_main` fleet. Nothing paged at the time — the outage was noticed only as a
side-effect of an unrelated task. `promotion_lag_monitor.py` cannot catch this failure class
either: a `startup_failure` run never even reaches a job, so it has no branch-pair compare state
to key off (that monitor's whole signal).

The cheapest honest signal that needs no VM/billing-API access (both `check-suites`/billing REST
endpoints are 403 for the available PAT): N+ CONSECUTIVE `startup_failure` conclusions on the
MOST-RECENT completed runs of either workflow. A single `startup_failure` is noise (a transient
runner-provisioning blip that GitHub itself sometimes emits); 3 in a row with nothing else in
between is a standing outage, not latency.

Root incident #2 (2026-08-07 —
`plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md`): a
`schedule`-triggered run of `ldr-to-main-promote-fleet.yml` fired against a STALE workflow-file
version on `main` (schedule/push triggers always run the DEFAULT-branch copy of the file) that
still requested a dead `[self-hosted, glue]` runner pool with zero registered runners. That run
sat `status: queued` FOREVER — never reaching `completed`, so root-incident-#1's own
consecutive-`startup_failure` check could never see it — and because
`concurrency.cancel-in-progress: false` tracks exactly one "currently claiming the group" run, it
permanently occupied the workflow's single concurrency slot: every later, correctly-specced
trigger (including `workflow_dispatch`) just queued behind it and got superseded by the next
arrival, forever, without ever getting a turn. This monitor reported `success` throughout that
entire ~2-hour+ livelock — zero coverage — until found by manual investigation
(`gh run cancel <id>`). The added signal here: any run of either workflow sitting `status: queued`
longer than `--queued-threshold-min` is flagged, independent of whether it ever reaches
`completed` — a structurally separate check from the streak above.

False-positive found 2026-08-08 (same day this hardening first shipped): an 8-day-old orphaned
run (created 2026-07-30, GitHub's own `cancel`/`force-cancel` endpoints both refuse it with
"Cannot cancel a workflow re-run that has not yet queued" — a GitHub-side inconsistency on
ancient run records) kept re-firing this alert every tick, even though 10/10 of the workflow's
MOST RECENT runs were `success` — i.e. the concurrency slot has clearly cycled through many
runs since, so this old record isn't actually occupying anything; it's a stale, unkillable API
artifact, not a live blocker. Fix: a queued run only counts as genuinely stuck if NO newer run of
the same workflow has reached a terminal (`completed`) state since it started queuing — if one
has, the "single waiter slot" has demonstrably moved on and this one is orphaned, not blocking.

Stdlib + `gh` only. Prints a human report; with `--slack` prints it Slack-ready and writes
`stuck=true|false` to `$GITHUB_OUTPUT` (if set) for the calling workflow to gate on. Exit 1 if
either workflow is startup_failure-stuck OR zombie-queued (so a required-check/alert can gate),
else exit 0.

Usage:
    promote_fleet_startup_failure_monitor.py [--repo IggyIkenna/unified-trading-pm]
                                              [--threshold 3] [--per-page 10]
                                              [--queued-threshold-min 30]
                                              [--now-iso 2026-08-07T12:00:00Z] [--slack]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from typing import cast

WORKFLOW_FILES = ("ldr-to-main-promote-fleet.yml", "ldr-to-main-promote.yml")

STARTUP_FAILURE = "startup_failure"

# Both target workflows use `concurrency: {cancel-in-progress: false}` on a 15-min schedule
# cadence (see the two workflow files' own comments) — a run genuinely still waiting for a busy
# hosted-runner pool should clear within a tick or two. 30 min gives real cold-starts/busy periods
# ample headroom while still catching the livelock class well before it compounds into hours (the
# source incident ran 340+ min before being found manually).
DEFAULT_QUEUED_THRESHOLD_MIN = 30.0


def _run_gh_json(args: list[str]) -> object:
    """Run `gh api <args>` and parse the JSON response. Raises on a non-zero exit."""
    proc = subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {' '.join(args)} failed (rc={proc.returncode}): {proc.stderr.strip()}")
    return cast("object", json.loads(proc.stdout))


def fetch_recent_runs(repo: str, workflow_file: str, per_page: int) -> list[dict[str, object]]:
    """Fetch the most recent COMPLETED runs of `workflow_file`, newest-first (GitHub's default order)."""
    body = _run_gh_json([f"repos/{repo}/actions/workflows/{workflow_file}/runs?status=completed&per_page={per_page}"])
    if not isinstance(body, dict):
        return []
    runs = cast("object", body.get("workflow_runs") or [])
    if not isinstance(runs, list):
        return []
    return [r for r in cast("list[object]", runs) if isinstance(r, dict)]


def fetch_queued_runs(repo: str, workflow_file: str, per_page: int) -> list[dict[str, object]]:
    """Fetch the runs of `workflow_file` currently sitting in `status=queued` (newest-first).

    A queued run never appears in `fetch_recent_runs` above (that fetch is scoped to
    `status=completed`) — this is the structurally separate query the zombie-queued check needs.
    """
    body = _run_gh_json([f"repos/{repo}/actions/workflows/{workflow_file}/runs?status=queued&per_page={per_page}"])
    if not isinstance(body, dict):
        return []
    runs = cast("object", body.get("workflow_runs") or [])
    if not isinstance(runs, list):
        return []
    return [r for r in cast("list[object]", runs) if isinstance(r, dict)]


def parse_iso(ts: object) -> dt.datetime | None:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def stuck_queued_runs(
    runs: list[dict[str, object]],
    threshold_min: float,
    now: dt.datetime,
    completed_runs: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    """Pure decision: which of `runs` (already filtered to `status=queued` by the caller) have been
    sitting queued longer than `threshold_min`. Each returned dict is the original run dict plus an
    injected `_age_min` key (rounded minutes) for reporting.

    A run with no parseable `created_at` is skipped rather than treated as stuck (fail-safe: never
    page on a malformed/missing timestamp).

    `completed_runs` (2026-08-08 false-positive fix) — same-workflow runs already known to have
    reached `status=completed` (the caller's `fetch_recent_runs` result). A queued run is excluded
    if any completed run is NEWER (`created_at` after the queued run's own `created_at`): that
    proves the single `cancel-in-progress: false` waiter slot has been claimed and released by at
    least one later trigger, so THIS queued run is an orphaned/superseded record — not the one
    actually occupying the slot — even though GitHub's own API still reports it as `queued` and may
    refuse to cancel it. `completed_runs` defaults to `None`, in which case every queued run is
    judged on age alone (unchanged from before this parameter existed).
    """
    newest_completed_at: dt.datetime | None = None
    for c in completed_runs or []:
        c_at = parse_iso(c.get("created_at"))
        if c_at is not None and (newest_completed_at is None or c_at > newest_completed_at):
            newest_completed_at = c_at

    stuck: list[dict[str, object]] = []
    for run in runs:
        queued_since = parse_iso(run.get("created_at"))
        if queued_since is None:
            continue
        age_min = (now - queued_since).total_seconds() / 60.0
        if age_min <= threshold_min:
            continue
        if newest_completed_at is not None and newest_completed_at > queued_since:
            continue
        stuck.append({**run, "_age_min": round(age_min, 1)})
    return stuck


def leading_run_of(runs: list[dict[str, object]], conclusion: str) -> list[dict[str, object]]:
    """Return the leading (most-recent-first) prefix of `runs` that all share `conclusion`,
    stopping at the first run whose conclusion differs. Pure — no threshold logic here."""
    out: list[dict[str, object]] = []
    for r in runs:
        if r.get("conclusion") == conclusion:
            out.append(r)
        else:
            break
    return out


def is_stuck(runs: list[dict[str, object]], threshold: int, conclusion: str = STARTUP_FAILURE) -> bool:
    """True when the `threshold` most-recent runs ALL share `conclusion` — a standing outage, not
    a single transient blip. `runs` shorter than `threshold` can never qualify (insufficient
    history), even if every run present matches."""
    if len(runs) < threshold:
        return False
    return len(leading_run_of(runs, conclusion)) >= threshold


def build_report(
    repo: str,
    findings: dict[str, list[dict[str, object]]],
    threshold: int,
    queued_stuck: dict[str, list[dict[str, object]]] | None = None,
    queued_threshold_min: float = DEFAULT_QUEUED_THRESHOLD_MIN,
) -> str:
    """`findings` maps workflow_file -> its leading same-conclusion run streak (the caller only
    includes an entry once `is_stuck` has already confirmed it meets `threshold`).

    `queued_stuck` (2026-08-07 hardening, root incident #2 above) maps workflow_file -> the runs
    of it the caller has already confirmed (via `stuck_queued_runs`) are sitting `status=queued`
    longer than `queued_threshold_min` — a structurally separate signal from `findings`, additive
    to it: either, both, or neither may be non-empty on a given tick.
    """
    queued_stuck = queued_stuck or {}
    if not findings and not queued_stuck:
        return (
            f"promote-fleet startup-failure monitor: healthy "
            f"(no workflow has {threshold}+ consecutive `{STARTUP_FAILURE}` runs, "
            f"no run queued > {queued_threshold_min:g}m)."
        )
    lines: list[str] = []
    if findings:
        lines.append(
            f":rotating_light: *PROMOTE WORKFLOW STUCK* — {len(findings)} workflow(s) posted "
            f"{threshold}+ consecutive `{STARTUP_FAILURE}` runs (LDR->main promotion is likely blocked fleet-wide):"
        )
        for wf, streak in findings.items():
            newest = streak[0]
            url = newest.get("html_url")
            link = f"<{url}|latest run>" if url else "latest run"
            lines.append(f"  • `{wf}` — {len(streak)} straight `{STARTUP_FAILURE}` runs, {link}")
        lines.append(
            f"  → check the GitHub Actions billing/spending-limit page for {repo} "
            f"(this exact signature was an account-level billing wall, 2026-07-30/31 precedent)"
        )
    if queued_stuck:
        total = sum(len(v) for v in queued_stuck.values())
        lines.append(
            f":rotating_light: *PROMOTE WORKFLOW ZOMBIE-QUEUED* — {total} run(s) stuck in `queued` > "
            f"{queued_threshold_min:g}m, permanently occupying the single `cancel-in-progress: false` "
            f"concurrency slot (every later trigger just queues behind it and is superseded, "
            f"never getting a turn — the 2026-08-07 2h+ livelock shape):"
        )
        for wf, runs in queued_stuck.items():
            for run in runs:
                url = run.get("html_url")
                link = f"<{url}|run {run.get('id')}>" if url else f"run {run.get('id')}"
                lines.append(f"  • `{wf}` — {link}, queued {run.get('_age_min')}m (event={run.get('event')})")
        lines.append(
            "  → likely a `schedule`-triggered run using a stale workflow-file version on `main` "
            "requesting a runner pool with zero registered runners; cancel it (`gh run cancel <id>`) "
            "then re-dispatch — see "
            "plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md"
        )
    return "\n".join(lines)


def _write_github_output(name: str, value: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default="IggyIkenna/unified-trading-pm")
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--per-page", type=int, default=10)
    parser.add_argument(
        "--queued-threshold-min",
        type=float,
        default=DEFAULT_QUEUED_THRESHOLD_MIN,
        help="Minutes a run may sit status=queued before it's flagged as zombie-queued",
    )
    parser.add_argument("--now-iso", default=None, help="Override 'now' (testing/determinism)")
    parser.add_argument("--slack", action="store_true", help="Print a Slack-ready report block")
    args = parser.parse_args()

    now = parse_iso(args.now_iso) if args.now_iso else dt.datetime.now(dt.UTC)
    if now is None:
        print(f"invalid --now-iso: {args.now_iso!r}", file=sys.stderr)
        return 2

    findings: dict[str, list[dict[str, object]]] = {}
    queued_stuck: dict[str, list[dict[str, object]]] = {}
    for wf in WORKFLOW_FILES:
        runs = fetch_recent_runs(args.repo, wf, args.per_page)
        if is_stuck(runs, args.threshold):
            findings[wf] = leading_run_of(runs, STARTUP_FAILURE)

        queued_runs = fetch_queued_runs(args.repo, wf, args.per_page)
        stuck_q = stuck_queued_runs(queued_runs, args.queued_threshold_min, now, completed_runs=runs)
        if stuck_q:
            queued_stuck[wf] = stuck_q

    report = build_report(args.repo, findings, args.threshold, queued_stuck, args.queued_threshold_min)
    print(report)
    stuck = bool(findings) or bool(queued_stuck)
    _write_github_output("stuck", "true" if stuck else "false")
    if args.slack:
        print("---SLACK---")
        print(report)

    return 1 if stuck else 0


if __name__ == "__main__":
    sys.exit(main())
