#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""SIT-gate stuck detector — pages when a repo has posted `SIT GATE BLOCK <repo>` on N+
CONSECUTIVE `ldr-to-main-promote-fleet.yml` ticks.

Root finding (`issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md`
[DEVOPS] P3): the SIT-gate treadmill (a repo's LDR tree racing the whole-workspace SIT digest so
it never lands on a `sit_validated_tree` that matches) is currently only OBSERVABLE via
`promotion_lag_monitor.py`'s branch-pair lag alert — which reads as generic latency, not a stuck
gate with a specific, nameable cause. `promotion_lag_monitor.py` cannot say WHY a pair is lagging
(it only compares branch content); this detector reads the actual `SIT GATE BLOCK <repo>: ...`
log lines `ldr_to_main_fleet_promote.sh` emits per tick (the ONE signal that distinguishes a
SIT-gate block from the script's many OTHER `_done BLOCKED` reasons — Tier-A CI red, provenance,
merge conflict, ...) and pages only once the SAME repo has been SIT-gate-blocked on the
`--threshold` most-recent CONSECUTIVE ticks, i.e. a standing treadmill, not a single slow tick.

**Constraint (source todo): implemented as a standalone detector — never edits
`ldr-to-main-promote-fleet.yml` itself** (that workflow already carries unrelated in-flight work
gated on an unmade direction ruling; this reads its run history from the outside instead).

A block→revalidate→PASS cycle self-silences by construction: the streak is always counted from
the NEWEST tick backward, so the moment a repo's most recent tick is not a `SIT GATE BLOCK` line,
its streak is 0 regardless of how long the prior streak ran.

Stdlib + `gh` only. Prints a human report; with `--slack` prints it Slack-ready and writes
`stuck=true|false` to `$GITHUB_OUTPUT` (if set) for the calling workflow to gate on. Exit 1 if any
repo is stuck (so a required-check/alert can gate), else exit 0.

Usage:
    sit_gate_stuck_detector.py [--repo IggyIkenna/unified-trading-pm]
                                [--workflow-file ldr-to-main-promote-fleet.yml]
                                [--threshold 3] [--lookback 8] [--slack]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from typing import cast

WORKFLOW_FILE = "ldr-to-main-promote-fleet.yml"

# Matches the exact log lines `ldr_to_main_fleet_promote.sh` emits (both SIT-gate call sites):
#   "SIT GATE BLOCK $REPO: in breaking_pending — awaiting SIT-green on staging before LDR→main"
#   "SIT GATE BLOCK $REPO: ${BREAKING}-delta not SIT-validated on this tree (...)"
# Repo names never contain whitespace/colons, so `\S+` up to the colon is exact — and matching
# anywhere in the text (not line-anchored) tolerates the job-name/step-name/timestamp prefix
# `gh run view --log` puts before each line.
_SIT_GATE_BLOCK_RE = re.compile(r"SIT GATE BLOCK (\S+):")


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


def fetch_run_log(repo: str, run_id: object) -> str | None:
    """Full run log text (every job/step) for one promote-fleet tick, or None on a fetch failure.

    None is DISTINCT from an empty-but-fetched log: a transient `gh` error must never be read as
    "this tick had no SIT GATE BLOCK line" — that would silently break/reset a genuine streak.
    Callers exclude a None tick from the history entirely rather than treat it as a clean tick.
    """
    proc = subprocess.run(
        ["gh", "run", "view", str(run_id), "--repo", repo, "--log"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


def parse_blocked_repos(log_text: str) -> set[str]:
    """Every repo this tick's log names in a `SIT GATE BLOCK <repo>:` line. Pure string parsing —
    no ordering/threshold logic here."""
    return set(_SIT_GATE_BLOCK_RE.findall(log_text))


def repo_streak(tick_blocked_sets: list[set[str]], repo: str) -> int:
    """Consecutive-from-the-newest-tick count of `repo` appearing in `tick_blocked_sets`
    (newest-first). Stops at the first tick that does NOT block `repo` — a
    block-revalidate-PASS cycle always ends the streak at 0 the moment the pass tick is the
    newest one, by construction, regardless of how long the prior block streak ran."""
    streak = 0
    for blocked in tick_blocked_sets:
        if repo in blocked:
            streak += 1
        else:
            break
    return streak


def stuck_repos(tick_blocked_sets: list[set[str]], threshold: int) -> dict[str, int]:
    """Repos whose trailing SIT-gate-block streak has reached `threshold`.

    Mirrors `promote_fleet_startup_failure_monitor.is_stuck`'s insufficient-history guard: with
    fewer than `threshold` ticks of history, no repo can be confirmed stuck yet, even if every
    tick present blocked it.
    """
    if len(tick_blocked_sets) < threshold:
        return {}
    candidates: set[str] = set()
    for blocked in tick_blocked_sets:
        candidates |= blocked
    out: dict[str, int] = {}
    for repo in candidates:
        streak = repo_streak(tick_blocked_sets, repo)
        if streak >= threshold:
            out[repo] = streak
    return out


def build_report(fleet_repo: str, findings: dict[str, int], threshold: int, newest_run_url: str | None) -> str:
    """`findings` maps repo -> its confirmed trailing SIT-gate-block streak (the caller only
    includes an entry once `stuck_repos` has already confirmed it meets `threshold`)."""
    if not findings:
        return f"sit-gate stuck detector: healthy (no repo has {threshold}+ consecutive `SIT GATE BLOCK` ticks)."
    lines = [
        f":rotating_light: *SIT GATE STUCK* — {len(findings)} repo(s) posted {threshold}+ consecutive "
        f"`SIT GATE BLOCK` verdicts on `{WORKFLOW_FILE}` (a stuck gate, not promotion-lag latency):"
    ]
    for repo in sorted(findings):
        lines.append(f"  • `{repo}` — {findings[repo]} straight SIT-gate-blocked tick(s)")
    if newest_run_url:
        lines.append(f"  → latest tick: {newest_run_url}")
    lines.append(
        f"  → check {fleet_repo}'s `sit-gate/fleet-green` status + `sit_validated_tree` — see "
        "issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md for the moving-tree race"
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
    parser.add_argument("--workflow-file", default=WORKFLOW_FILE)
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--lookback", type=int, default=8, help="How many recent completed runs to inspect")
    parser.add_argument("--slack", action="store_true", help="Print a Slack-ready report block")
    args = parser.parse_args()

    runs = fetch_recent_runs(cast(str, args.repo), cast(str, args.workflow_file), cast(int, args.lookback))
    tick_blocked_sets: list[set[str]] = []
    for r in runs:
        log_text = fetch_run_log(cast(str, args.repo), r.get("id"))
        if log_text is None:
            print(
                f"   … skip run {r.get('id')}: log fetch failed (excluded, not treated as a clean tick)",
                file=sys.stderr,
            )
            continue
        tick_blocked_sets.append(parse_blocked_repos(log_text))

    findings = stuck_repos(tick_blocked_sets, cast(int, args.threshold))

    newest_url = None
    if runs and isinstance(runs[0].get("html_url"), str):
        newest_url = cast(str, runs[0]["html_url"])

    report = build_report(cast(str, args.repo), findings, cast(int, args.threshold), newest_url)
    print(report)
    _write_github_output("stuck", "true" if findings else "false")
    # Worst-repo streak, exposed so the caller can fold it into notify-slack.yml's dedup_key
    # (sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md): a flat dedup_key +
    # cooldown_min suppressed a repost even while the streak was measurably worsening (4->6) —
    # the condition never got quieter, the alert just went silent. Folding max_streak into the
    # key means a NEW worse (or better) value is a "new" key that bypasses the cooldown, while a
    # truly flat streak still dedupes normally.
    _write_github_output("max_streak", str(max(findings.values())) if findings else "0")
    if args.slack:
        print("---SLACK---")
        print(report)

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
