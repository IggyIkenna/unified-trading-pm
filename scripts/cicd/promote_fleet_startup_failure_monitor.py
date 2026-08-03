#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Promote-fleet startup-failure monitor — pages when `ldr-to-main-promote-fleet.yml` or
`ldr-to-main-promote.yml` post 3+ CONSECUTIVE `startup_failure` runs.

Root incident (2026-07-30, RESOLVED 2026-07-31 —
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

Stdlib + `gh` only. Prints a human report; with `--slack` prints it Slack-ready and writes
`stuck=true|false` to `$GITHUB_OUTPUT` (if set) for the calling workflow to gate on. Exit 1 if
either workflow is stuck (so a required-check/alert can gate), else exit 0.

Usage:
    promote_fleet_startup_failure_monitor.py [--repo IggyIkenna/unified-trading-pm]
                                              [--threshold 3] [--per-page 10] [--slack]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import cast

WORKFLOW_FILES = ("ldr-to-main-promote-fleet.yml", "ldr-to-main-promote.yml")

STARTUP_FAILURE = "startup_failure"


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


def build_report(repo: str, findings: dict[str, list[dict[str, object]]], threshold: int) -> str:
    """`findings` maps workflow_file -> its leading same-conclusion run streak (the caller only
    includes an entry once `is_stuck` has already confirmed it meets `threshold`)."""
    if not findings:
        return (
            f"promote-fleet startup-failure monitor: healthy "
            f"(no workflow has {threshold}+ consecutive `{STARTUP_FAILURE}` runs)."
        )
    lines = [
        f":rotating_light: *PROMOTE WORKFLOW STUCK* — {len(findings)} workflow(s) posted "
        f"{threshold}+ consecutive `{STARTUP_FAILURE}` runs (LDR->main promotion is likely blocked fleet-wide):"
    ]
    for wf, streak in findings.items():
        newest = streak[0]
        url = newest.get("html_url")
        link = f"<{url}|latest run>" if url else "latest run"
        lines.append(f"  • `{wf}` — {len(streak)} straight `{STARTUP_FAILURE}` runs, {link}")
    lines.append(
        f"  → check the GitHub Actions billing/spending-limit page for {repo} "
        f"(this exact signature was an account-level billing wall, 2026-07-30/31 precedent)"
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
    parser.add_argument("--slack", action="store_true", help="Print a Slack-ready report block")
    args = parser.parse_args()

    findings: dict[str, list[dict[str, object]]] = {}
    for wf in WORKFLOW_FILES:
        runs = fetch_recent_runs(args.repo, wf, args.per_page)
        if is_stuck(runs, args.threshold):
            findings[wf] = leading_run_of(runs, STARTUP_FAILURE)

    report = build_report(args.repo, findings, args.threshold)
    print(report)
    _write_github_output("stuck", "true" if findings else "false")
    if args.slack:
        print("---SLACK---")
        print(report)

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
