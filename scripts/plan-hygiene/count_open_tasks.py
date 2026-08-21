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

**`ao_backlog_proxy` (added 2026-08-03)**: the deduped/aggregator-excluded number above
is deliberately NOT what the live AO backlog size reconciles against — verified against
`agent-orchestrator/server/regen_backlog_from_plan.py`'s real per-doc ingestion gate
(`_plan_contributes_briefs`), which has NO aggregator-name exclusion at all: a
`*_satellite_ao_dispatch_batch3_finalize.md` plan tagged `assigned_vm: planning` is
ingested exactly like any primary plan. `ao_backlog_proxy` mirrors that real gate instead
(`assigned_vm == planning` AND `status` not in `{draft, superseded}` AND
`execution_scope != local-only`, NO aggregator exclusion) across BOTH `plans/active/*.md`
AND `plans/active/issues/*.md` (the prior version of this script only scanned the former —
issues were invisible to it entirely). Confirmed 2026-08-03 against the live backlog
(`/check-agent-orchestrator`: 549 queued + 10 dispatched + 34 blocked = 593 open) — this
field's ~634 reconciles within the expected margin (live state is cumulative/non-pruning
and reads an LDR git snapshot, so exact equality isn't expected); the old deduped headline
(~80) does not and should never be quoted as an AO-backlog-size estimate.

For a blocked-vs-dispatchable split of any of these open todos, use the sibling
`count_operator_blocking_todos.py` (classifies by live `BLOCKED-*`/`[OPERATOR]` markers) —
not duplicated here to avoid two copies of that regex drifting apart.

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
# Deliberately applied to plans/active/*.md only — verified by inspection that
# plans/active/issues/*.md filenames containing these substrings (e.g. "batch",
# "consolidat") are domain terms ("a batch of capture rows", "manifest consolidator
# cron"), not rollup docs; reusing this filter there would wrongly exclude genuine
# standalone issues.
AGGREGATOR_MARKERS = ("master", "batch", "consolidat", "closeout", "satellite")

OPEN_RE = re.compile(r"^\s*- \[ \]")
DONE_RE = re.compile(r"^\s*- \[[xX]\]")


@dataclass
class PlanStats:
    path: Path
    assigned_vm: str
    status: str
    execution_scope: str
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


def scan_plan(path: Path, *, check_aggregator: bool) -> PlanStats:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    assigned_vm = (fm.get("assigned_vm") or "missing").lower()
    if assigned_vm in ("", "missing"):
        assigned_vm = "missing"
    # legacy alias
    if assigned_vm == "human-planning":
        assigned_vm = "planning"
    status = (fm.get("status") or "missing").lower()
    execution_scope = (fm.get("execution_scope") or "").lower()
    name = path.name.lower()
    is_aggregator = check_aggregator and any(marker in name for marker in AGGREGATOR_MARKERS)
    open_count = sum(1 for ln in text.splitlines() if OPEN_RE.match(ln))
    done_count = sum(1 for ln in text.splitlines() if DONE_RE.match(ln))
    return PlanStats(path, assigned_vm, status, execution_scope, is_aggregator, open_count, done_count)


def collect(pm_root: Path) -> list[PlanStats]:
    active = sorted((pm_root / "plans" / "active").glob("*.md"))
    return [scan_plan(p, check_aggregator=True) for p in active if p.name != "INDEX.md" and not p.name.startswith("_")]


def collect_issues(pm_root: Path) -> list[PlanStats]:
    issues_dir = pm_root / "plans" / "active" / "issues"
    if not issues_dir.is_dir():
        return []
    return [scan_plan(p, check_aggregator=False) for p in sorted(issues_dir.glob("*.md"))]


def _ao_ingestible(s: PlanStats) -> bool:
    """Mirrors regen_backlog_from_plan.py's _plan_contributes_briefs doc-level gate.
    Deliberately no aggregator exclusion — the real ingester has none."""
    return s.assigned_vm == "planning" and s.status not in ("draft", "superseded") and s.execution_scope != "local-only"


def summarise(stats: list[PlanStats], issue_stats: list[PlanStats]) -> dict:
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

    issues_open = sum(s.open_count for s in issue_stats)
    issues_done = sum(s.done_count for s in issue_stats)
    issues_by_vm: dict[str, int] = {}
    for s in issue_stats:
        issues_by_vm[s.assigned_vm] = issues_by_vm.get(s.assigned_vm, 0) + s.open_count

    ao_backlog_proxy_plans = sum(s.open_count for s in stats if _ao_ingestible(s))
    ao_backlog_proxy_issues = sum(s.open_count for s in issue_stats if _ao_ingestible(s))

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
        "issues_scanned": len(issue_stats),
        "issues_all_open": issues_open,
        "issues_all_done": issues_done,
        "issues_open_by_assigned_vm": dict(sorted(issues_by_vm.items(), key=lambda kv: -kv[1])),
        "ao_backlog_proxy": {
            "plans_open": ao_backlog_proxy_plans,
            "issues_open": ao_backlog_proxy_issues,
            "total_open": ao_backlog_proxy_plans + ao_backlog_proxy_issues,
        },
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
    issue_stats = collect_issues(args.pm_root)
    result = summarise(stats, issue_stats)

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
    print(f"  Planning-assigned open INCL aggregators (≈ AO dispatch pool, plans only): {_planning_incl_agg}")
    print()
    print(f"  Issues scanned: {r['issues_scanned']}  (plans/active/issues/*.md)")
    print(f"    ALL issues open: {r['issues_all_open']}   (done: {r['issues_all_done']})")
    print("    Issues open by assigned_vm:")
    for vm, n in r["issues_open_by_assigned_vm"].items():
        print(f"      {vm:<10} {n:>5}")
    print()
    proxy = r["ao_backlog_proxy"]
    print("  AO_BACKLOG_PROXY (mirrors regen_backlog_from_plan.py's real ingestion gate — NO aggregator")
    print("  exclusion; assigned_vm==planning, status not draft/superseded, execution_scope != local-only):")
    print(f"    plans_open:  {proxy['plans_open']:>5}")
    print(f"    issues_open: {proxy['issues_open']:>5}")
    print(f"    TOTAL:       {proxy['total_open']:>5}")
    print("  This is the number to quote for 'how big is the AO backlog' — not the deduped headline above.")
    print("  Note: assigned_vm=planning is what the AO backlog dispatches; NA/missing are not dispatched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
