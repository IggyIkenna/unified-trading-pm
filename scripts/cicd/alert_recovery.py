#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Shared state-diffed alert-recovery helper for GHA standing-condition CI monitors.

Several PM workflows (fix-approval-timeout, ldr-docs-gate, freeze-deferred-build-replay,
promote-fleet-startup-failure-monitor, ruleset-drift-alert, sit-gate-stuck-detector) page a
standing bad condition via notify-slack.yml's dedup_key + cooldown, but never announced an
explicit RESOLVED bookend once the condition cleared — the gap flagged in
issues/glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md's "Still open"
P3 item. Rather than re-derive the prev-tick-vs-this-tick diff per workflow (as
cloud-build-failure-watcher.yml / stale-build-watcher.yml each do inline in bash), this is the
ONE tested implementation every affected workflow's YAML calls, paired with an `actions/cache`
state file (mirrors branch-health.yml's `.lag-state.json` pattern).

CLI usage (one call per tick, after the workflow has computed this tick's alert bool):
    python3 scripts/cicd/alert_recovery.py --state-file .foo-alert-state.json --current true
Reads the previous tick's persisted alert bool from --state-file (missing/corrupt -> False,
never a false recovery), computes the transition, OVERWRITES --state-file with the current
tick's value for the next run's diff, and prints `recovered=true|false` to stdout — callers
redirect that straight into $GITHUB_OUTPUT.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_prev_alert(state_file: Path) -> bool:
    """Best-effort: a missing/corrupt state file reads as "no prior alert" — never a false recovery."""
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return bool(data.get("alert", False))


def compute_recovery(prev_alert: bool, current_alert: bool) -> bool:
    """A transition-only recovery: the prior tick alerted and this tick doesn't."""
    return prev_alert and not current_alert


def write_state(state_file: Path, current_alert: bool) -> None:
    state_file.write_text(json.dumps({"alert": current_alert}), encoding="utf-8")


def _parse_bool(value: str) -> bool:
    return value.strip().lower() == "true"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-file", required=True, type=Path)
    parser.add_argument("--current", required=True, help="'true' or 'false' — this tick's alert state")
    args = parser.parse_args()

    current_alert = _parse_bool(args.current)
    prev_alert = read_prev_alert(args.state_file)
    recovered = compute_recovery(prev_alert, current_alert)
    write_state(args.state_file, current_alert)
    print(f"recovered={'true' if recovered else 'false'}")


if __name__ == "__main__":
    main()
