#!/usr/bin/env python3
# Epic: orchestrator_master
# Lifecycle: durable tooling (Human Fleet Phase 5 — ao_human_fleet_integration_2026_08_15.md)
# Delete-when: never (standing per-operator plan/task activity view)
"""Git-log-derived "plans created" / "tasks completed" activity view, split by operator.

Resolved design (ao_human_fleet_integration_2026_08_15.md, Phase 5, 2026-08-16 "classification
reconciliation") after two rejected approaches: self-declared role_group per heartbeat can't
honestly classify a mixed session, and classifying by file path wrongly buckets a
checkbox-flip-with-evidence commit (task execution) the same as a plan-authoring commit.

Classifies each `unified-trading-pm` commit touching `plans/`:
  - TASK COMPLETED  = the commit's net checkbox delta shows more `- [ ]` -> `- [x]` flips than
                       new opens (by construction tied to closing a named todo — matches this
                       workspace's own "Commit + Push + Flip" hard rule, no new convention).
  - PLAN CREATED/UPDATED = touches plans/ but flips no checkbox (drafting, adding open todos,
                       Progress Log notes).
Deliberately does NOT touch token/spend counts — git commits carry no token data. That is
Phase 2's already-built job (ao-usage-push.py -> AO's TaskUsageRow, role_group=human/
planning-human); this script stays a pure git-log classifier, one lane only.

Operator identity: derived from commit author email domain (gmail.com -> ikenna,
odum-research.com -> harsh per this workspace's commit-attribution convention,
/codex/05-infrastructure/per-tab-worktrees.md), never a new tagging scheme.

Pure stdlib + git subprocess calls, read-only. No network, no cloud.

Usage:
    python scripts/plan-hygiene/plan_task_activity.py [--pm-root <path>] [--since <date>] [--json]
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

OPEN_RE = re.compile(r"^\s*-\s*\[ \]", re.MULTILINE)
DONE_RE = re.compile(r"^\s*-\s*\[[xX]\]", re.MULTILINE)

_OPERATOR_BY_DOMAIN = {
    "gmail.com": "ikenna",
    "odum-research.com": "harsh",
}


def _operator_from_email(email: str) -> str:
    domain = email.rsplit("@", 1)[-1].lower() if "@" in email else email
    return _OPERATOR_BY_DOMAIN.get(domain, email)


@dataclass
class CommitEvent:
    sha: str
    operator: str
    when: str
    kind: str  # "task_completed" | "plan_updated"
    flips: int
    files: list[str] = field(default_factory=list)


def _run(args: list[str], cwd: Path) -> str:
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    return result.stdout if result.returncode == 0 else ""


def _checkbox_counts(text: str) -> tuple[int, int]:
    return len(OPEN_RE.findall(text)), len(DONE_RE.findall(text))


def _plan_files_touched(sha: str, pm_root: Path) -> list[str]:
    out = _run(["git", "show", "--name-only", "--pretty=format:", sha], cwd=pm_root)
    return [line for line in out.splitlines() if line.startswith("plans/") and line.endswith(".md")]


def _flips_for_file(sha: str, path: str, pm_root: Path) -> int:
    old = _run(["git", "show", f"{sha}^:{path}"], cwd=pm_root)
    new = _run(["git", "show", f"{sha}:{path}"], cwd=pm_root)
    old_open, old_done = _checkbox_counts(old)
    new_open, new_done = _checkbox_counts(new)
    # A genuine flip decreases open-count and increases done-count together — min() guards
    # against noise from an unrelated addition of already-done items landing in the same commit.
    return max(0, min(old_open - new_open, new_done - old_done))


def collect_events(pm_root: Path, since: str | None) -> list[CommitEvent]:
    log_args = ["git", "log", "--format=%H%x1f%ae%x1f%ai", "--", "plans/"]
    if since:
        log_args.insert(2, f"--since={since}")
    log = _run(log_args, cwd=pm_root)
    events: list[CommitEvent] = []
    for line in log.splitlines():
        if not line.strip():
            continue
        sha, email, when = line.split("\x1f")
        files = _plan_files_touched(sha, pm_root)
        if not files:
            continue
        total_flips = sum(_flips_for_file(sha, f, pm_root) for f in files)
        kind = "task_completed" if total_flips > 0 else "plan_updated"
        events.append(
            CommitEvent(
                sha=sha[:10],
                operator=_operator_from_email(email),
                when=when,
                kind=kind,
                flips=total_flips,
                files=files,
            )
        )
    return events


def summarize(events: list[CommitEvent]) -> dict[str, dict[str, int]]:
    by_operator: dict[str, dict[str, int]] = defaultdict(lambda: {"tasks_completed": 0, "plans_updated": 0})
    for e in events:
        if e.kind == "task_completed":
            by_operator[e.operator]["tasks_completed"] += 1
        else:
            by_operator[e.operator]["plans_updated"] += 1
    return dict(by_operator)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pm-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--since", default=None, help="git --since date filter, e.g. '2026-08-01'")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    events = collect_events(args.pm_root, args.since)
    summary = summarize(events)

    if args.json:
        print(json.dumps({"summary": summary, "events": [e.__dict__ for e in events]}, indent=2))
        return 0

    print(f"Plan/task activity — {len(events)} commit(s) touching plans/\n")
    for operator, counts in sorted(summary.items()):
        print(f"  {operator}: {counts['tasks_completed']} task(s) completed, {counts['plans_updated']} plan update(s)")
    print()
    for e in events[:20]:
        label = "TASK COMPLETED" if e.kind == "task_completed" else "plan updated"
        print(f"  {e.sha}  {e.operator:<10} {label:<15} {e.when}")
    if len(events) > 20:
        print(f"  ... and {len(events) - 20} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
