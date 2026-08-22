#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Glue-pool runner-health monitor — pages when fewer than `--min-online` `glue`-labelled
self-hosted runners are `online`.

Incident (2026-08-06, `issues/fleet_promoter_glue_runner_stall_2026_08_06.md`): the LDR→main fleet
promoter stalled 3+ hours because the `glue` pool ran at 25% capacity (2 of 4 runners online, one of
them busy) — every `*/5` schedule event queued a run that cancelled its queued predecessor before
any runner picked it up, so ZERO promotions completed fleet-wide. The existing
`glue-pool-starvation-monitor` catches "`glue` jobs queued while nothing is in progress", but a
DEPLETED pool never queues — the scheduler just keeps cancelling, so no job ever sits. This monitor
closes that gap at the cheapest honest signal: count the `glue`-labelled runners that are actually
`online` right now.

Scope: the `glue`/`glue-writer` pools are repo-scoped to `unified-trading-pm` (a personal account
can't register org runners — see scripts/self-hosted-runners/setup-glue-runners.sh), so
`repos/{repo}/actions/runners` is the only surface needed. `glue-writer` runners are deliberately
EXCLUDED (disjoint label, its own pool, out of scope — see setup-glue-runners.sh's "labels are
DISJOINT on purpose" note); label lists are matched by EXACT string membership so `glue-writer`
never satisfies a `glue` check.

MUST run on a GitHub-hosted runner, never `glue` itself — a dead-man-switch that ran on the pool it
watches would go dark exactly when it is needed (the same failure-independence rule applied to the
other monitors — see scripts/self-hosted-runners/classify-glue-workflows.sh KEEP_MONITORS).

FAIL-CLOSED: a query failure (token permission / API error) is treated as a page, never silence —
the original incident was exactly a monitor that went dark when the pool was sick, so the monitor
itself failing must surface too.

Stdlib + `gh` only. Prints a human report; with `--slack` prints it Slack-ready and writes
`low_online=true|false` to `$GITHUB_OUTPUT` (if set) for the calling workflow to gate on. Exit 1 if
the online `glue`-runner count is below the threshold OR the runner API could not be queried (both
page), else exit 0.

Usage:
    glue_runner_health_monitor.py [--repo IggyIkenna/unified-trading-pm] [--min-online 3]
                                  [--slack]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from typing import cast

GLUE_LABEL = "glue"


def _run_gh_json(args: list[str]) -> object:
    """Run `gh api <args>` and parse the JSON response. Raises on a non-zero exit."""
    proc = subprocess.run(["gh", "api", *args], capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"gh api {' '.join(args)} failed (rc={proc.returncode}): {proc.stderr.strip()}")
    return cast("object", json.loads(proc.stdout))


def fetch_runners(repo: str) -> list[dict[str, object]]:
    """Fetch the self-hosted runners registered to `repo` (per_page 100; the pool is tiny)."""
    body = _run_gh_json([f"repos/{repo}/actions/runners?per_page=100"])
    if not isinstance(body, dict):
        return []
    runners = cast("object", body.get("runners") or [])
    if not isinstance(runners, list):
        return []
    return [r for r in cast("list[object]", runners) if isinstance(r, dict)]


def is_glue_runner(runner: dict[str, object]) -> bool:
    """True iff the runner's `labels` include exactly `glue` (never `glue-writer`)."""
    labels = runner.get("labels")
    if not isinstance(labels, list):
        return False
    names = [lbl.get("name") for lbl in labels if isinstance(lbl, dict)]
    return GLUE_LABEL in names


def count_online_glue_runners(runners: list[dict[str, object]]) -> int:
    """Count `glue` runners whose GitHub-reported status is `online`."""
    return sum(1 for r in runners if is_glue_runner(r) and r.get("status") == "online")


def offline_glue_runner_names(runners: list[dict[str, object]]) -> list[str]:
    """Names of `glue` runners that are NOT currently online (registered but down)."""
    return [str(r["name"]) for r in runners if is_glue_runner(r) and r.get("status") != "online" and r.get("name")]


def build_report(online: int, offline: list[str], min_online: int, total: int) -> str:
    """Human/Slack-ready summary of `glue` pool health."""
    if online >= min_online:
        return f"glue runner pool healthy: {online} online (threshold {min_online})."
    lines = [
        f":rotating_light: *glue runner pool depleted* — only {online}/{total} `glue` runner(s) "
        f"online (need ≥ {min_online}):",
    ]
    if offline:
        lines.append("  • offline: " + ", ".join(offline))
    else:
        lines.append("  • no registered `glue` runner is offline — the pool itself may have shrunk.")
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
    parser.add_argument("--min-online", type=int, default=3, help="Alert when online glue runners < this")
    parser.add_argument("--slack", action="store_true", help="Print a Slack-ready report block")
    args = parser.parse_args()

    if args.min_online < 1:
        print(f"invalid --min-online: {args.min_online} (must be ≥ 1)", file=sys.stderr)
        return 2

    try:
        runners = fetch_runners(args.repo)
    except RuntimeError as exc:
        # FAIL-CLOSED: the monitor is blind, which is its own incident class — page.
        report = (
            ":rotating_light: *glue runner-health monitor could not query the runner API* — the "
            "dead-man-switch is blind. Check this workflow's token/permissions immediately.\n  "
            f"{exc}"
        )
        print(report)
        _write_github_output("low_online", "true")
        if args.slack:
            print("---SLACK---")
            print(report)
        return 1

    online = count_online_glue_runners(runners)
    offline = offline_glue_runner_names(runners)
    total = online + len(offline)
    report = build_report(online, offline, args.min_online, total)

    print(report)
    low = online < args.min_online
    _write_github_output("low_online", "true" if low else "false")
    if args.slack:
        print("---SLACK---")
        print(report)

    return 1 if low else 0


if __name__ == "__main__":
    sys.exit(main())
