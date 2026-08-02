#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: durable tooling (SSOT for the deduped open-task count)
# Delete-when: never (standing metric; invoked by the /open-task-count skill)
"""Count tracked plan tasks across the active corpus, deduped and split by dispatch target.

The headline number is the DEDUPED OPEN task count: open `- [ ]` checkboxes in
`plans/active/*.md`, EXCLUDING aggregator plans (master / batch / consolidated /
closeout / satellite) whose todos duplicate the primary plans they roll up. It also
breaks the deduped-open set down by `assigned_vm` (planning = AO-dispatched, NA =
not dispatched, other/missing), which explains any gap versus the live AO backlog.

Usage:
    python scripts/plan-hygiene/count_open_tasks.py [--pm-root <path>] [--json]

Pure stdlib, read-only. No network, no cloud.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Filename substrings that mark a plan as an aggregator/roll-up whose todos
# duplicate the primary plans it references (excluded from the deduped count).
AGGREGATOR_MARKERS = ("master", "batch", "consolidat", "closeout", "satellite")

OPEN_RE = re.compile(r"^\s*- \[ \]")
DONE_RE = re.compile(r"^\s*- \[[xX]\]")


@dataclass
class PlanStats:
    path: Path
    assigned_vm: str
    status: str
    is_aggregator: bool
    open_count: int
    done_count: int


@dataclass
class Totals:
    open: int = 0
    done: int = 0
    plans: int = 0
    by_vm: dict[str, int] = field(default_factory=dict)


def parse_frontmatter(text: str) -> dict[str, str]:
    """Return a flat {key: value} for the leading YAML frontmatter block (simple scalars only)."""
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    out: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if m:
            value = m.group(2)
            # strip trailing inline comments (e.g. `assigned_vm: na # local execution`)
            value = re.sub(r"\s+#.*$", "", value)
            out[m.group(1)] = value.strip().strip("'\"")
    return out


def scan_plan(path: Path) -> PlanStats:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    assigned_vm = (fm.get("assigned_vm") or "missing").lower()
    if assigned_vm in ("", "missing"):
        assigned_vm = "missing"
    # legacy alias
    if assigned_vm == "human-planning":
        assigned_vm = "planning"
    status = (fm.get("status") or "missing").lower()
    name = path.name.lower()
    is_aggregator = any(marker in name for marker in AGGREGATOR_MARKERS)
    open_count = sum(1 for ln in text.splitlines() if OPEN_RE.match(ln))
    done_count = sum(1 for ln in text.splitlines() if DONE_RE.match(ln))
    return PlanStats(path, assigned_vm, status, is_aggregator, open_count, done_count)


def collect(pm_root: Path) -> list[PlanStats]:
    active = sorted((pm_root / "plans" / "active").glob("*.md"))
    return [scan_plan(p) for p in active if p.name != "INDEX.md" and not p.name.startswith("_")]


def summarise(stats: list[PlanStats]) -> dict:
    all_open = sum(s.open_count for s in stats)
    all_done = sum(s.done_count for s in stats)
    dedup = [s for s in stats if not s.is_aggregator]
    dedup_open = sum(s.open_count for s in dedup)
    dedup_done = sum(s.done_count for s in dedup)

    by_vm: dict[str, int] = {}
    by_vm_active: dict[str, int] = {}
    for s in dedup:
        by_vm[s.assigned_vm] = by_vm.get(s.assigned_vm, 0) + s.open_count
        if s.status not in ("draft", "complete", "archived"):
            by_vm_active[s.assigned_vm] = by_vm_active.get(s.assigned_vm, 0) + s.open_count

    # planning-assigned open INCLUDING aggregators — AO dispatches these too, so this
    # reconciles against the live AO backlog better than the deduped figure.
    planning_incl_aggregators = sum(
        s.open_count for s in stats if s.assigned_vm == "planning" and s.status not in ("draft", "complete", "archived")
    )

    return {
        "plans_scanned": len(stats),
        "aggregators_excluded": sum(1 for s in stats if s.is_aggregator),
        "all_active_open": all_open,
        "all_active_done": all_done,
        "deduped_open": dedup_open,
        "deduped_done": dedup_done,
        "deduped_open_by_assigned_vm": dict(sorted(by_vm.items(), key=lambda kv: -kv[1])),
        "deduped_open_by_assigned_vm_active_status_only": dict(sorted(by_vm_active.items(), key=lambda kv: -kv[1])),
        "planning_open_incl_aggregators_active": planning_incl_aggregators,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    default_root = Path(__file__).resolve().parents[2]
    ap.add_argument(
        "--pm-root",
        type=Path,
        default=default_root,
        help="unified-trading-pm repo root (default: inferred from script location)",
    )
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    if not (args.pm_root / "plans" / "active").is_dir():
        print(f"error: no plans/active under {args.pm_root}", file=sys.stderr)
        return 2

    stats = collect(args.pm_root)
    result = summarise(stats)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    r = result
    print("Open-task count — active plan corpus")
    print(f"  plans scanned:            {r['plans_scanned']}")
    print(f"  aggregator plans excluded:{r['aggregators_excluded']:>5}  (master/batch/consolidated/closeout/satellite)")
    print()
    print(f"  ALL active-plan open:     {r['all_active_open']:>5}   (done: {r['all_active_done']})")
    print(f"  DEDUPED open (headline):  {r['deduped_open']:>5}   (done: {r['deduped_done']})")
    print()
    print("  Deduped open by dispatch target (assigned_vm):")
    for vm, n in r["deduped_open_by_assigned_vm"].items():
        print(f"    {vm:<10} {n:>5}")
    print()
    print("  Deduped open, active-status plans only (excludes draft/complete):")
    for vm, n in r["deduped_open_by_assigned_vm_active_status_only"].items():
        print(f"    {vm:<10} {n:>5}")
    print()
    _planning_incl_agg = r["planning_open_incl_aggregators_active"]
    print(f"  Planning-assigned open INCL aggregators (≈ AO dispatch pool): {_planning_incl_agg}")
    print("  Note: assigned_vm=planning is what the AO backlog dispatches; NA/missing are not dispatched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
