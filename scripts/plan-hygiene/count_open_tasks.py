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

**Cross-corpus dedup for issues (added 2026-08-21)**: the plans-side aggregator exclusion
above has no equivalent for `plans/active/issues/*.md` — an issue whose finding has been
extracted verbatim into a plan (the corpus-wide "EXTRACTED -> <path>" annotation convention
used by /ag-closeout-audit and /na-eligibility-audit) keeps its own `- [ ]` checkbox intact
(only an annotation is added nearby, the checkbox itself is never converted or removed), so
the issue's copy was silently counted as "still open" even when a satellite/batch plan
elsewhere already carries the same item. Because that plan-side copy is itself
aggregator-excluded from the deduped plans headline, the raw combination (deduped plans +
raw issues) was NOT actually double-counting the common case (extraction into a
satellite/batch doc) -- but it WAS blind to two real gaps: (a) an issue extracted into a
NON-aggregator-named plan (a "master" plan or any other regular plan) would count in BOTH
corpora with zero suppression, and (b) an extraction marker whose target no longer exists
(a stale/dangling pointer) gave false confidence that the item was tracked elsewhere when
nothing actually was. `find_covered_checkboxes()` below resolves every extraction/duplicate
marker's target path against the live corpus (plans/active, plans/active/issues, and
plans/archive/** as a fallback for already-graduated batches) and only excludes a checkbox
from the deduped issues count when the target FILE PROVABLY EXISTS -- a marker whose target
is missing/renamed leaves the checkbox counted as open (and is reported separately as a
dangling-marker finding, since that is itself a real corpus-hygiene gap). The same applies
to a whole doc flagged `status: superseded` with a resolvable `superseded_by:` target: every
open checkbox in it is excluded (the work is tracked at the superseding doc), again only
when that target is provably real.

For a blocked-vs-dispatchable split of any of these open todos, use the sibling
`count_operator_blocking_todos.py` (classifies by live `BLOCKED-*`/`[OPERATOR]` markers) --
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
# Deliberately applied to plans/active/*.md only -- verified by inspection that
# plans/active/issues/*.md filenames containing these substrings (e.g. "batch",
# "consolidat") are domain terms ("a batch of capture rows", "manifest consolidator
# cron"), not rollup docs; reusing this filter there would wrongly exclude genuine
# standalone issues.
AGGREGATOR_MARKERS = ("master", "batch", "consolidat", "closeout", "satellite")

OPEN_RE = re.compile(r"^\s*- \[ \]")
DONE_RE = re.compile(r"^\s*- \[[xX]\]")
HEADING_RE = re.compile(r"^#{1,6}\s")

# A checkbox "block" runs from its own line to (but not including) the next
# checkbox or heading line. Within that block, a marker of this shape means the
# item's work has been handed off elsewhere -- capture the referenced path.
MARKER_RE = re.compile(
    r"(?:EXTRACTED|DUPLICATE OF|SUPERSEDED BY)\b[^\n]{0,300}?"
    r"[`']?((?:/|plans/|codex/)?[\w./-]+\.md)[`']?",
    re.IGNORECASE,
)


@dataclass
class PlanStats:
    path: Path
    assigned_vm: str
    status: str
    execution_scope: str
    superseded_by: str
    is_aggregator: bool
    open_count: int
    done_count: int
    open_lines: list[tuple[int, str]] = field(default_factory=list)  # (line_no, marker_target_or_empty)
    text: str = ""


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


def _checkbox_blocks(text: str) -> list[tuple[int, bool, str]]:
    """Split text into (line_no, is_open, block_text) for every checkbox line, where
    block_text spans from the checkbox line to the next checkbox/heading (exclusive)."""
    lines = text.splitlines()
    blocks: list[tuple[int, bool, str]] = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        is_open = bool(OPEN_RE.match(line))
        is_done = bool(DONE_RE.match(line))
        if is_open or is_done:
            j = i + 1
            block_lines = [line]
            while (
                j < n and not OPEN_RE.match(lines[j]) and not DONE_RE.match(lines[j]) and not HEADING_RE.match(lines[j])
            ):
                block_lines.append(lines[j])
                j += 1
            blocks.append((i + 1, is_open, "\n".join(block_lines)))
            i = j
        else:
            i += 1
    return blocks


def _resolve_target(pm_root: Path, raw: str) -> Path | None:
    """Try to resolve a marker's captured path against the live corpus. Returns the
    resolved Path if a real file exists, else None.

    Handles two shapes seen in the corpus: an EXTRACTED/DUPLICATE-OF/SUPERSEDED-BY
    marker's captured path (already `.md`-suffixed, per MARKER_RE), and a bare doc
    slug with no extension (the `superseded_by:` frontmatter convention observed
    2026-08-21, e.g. `dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20` with no
    `.md`) -- `.md` is appended here when missing so both resolve through the same
    search-root logic."""
    candidate = raw.strip().strip("`'\"[]")
    candidate = candidate.lstrip("/")
    if candidate and not candidate.endswith(".md"):
        candidate = f"{candidate}.md"
    name = Path(candidate).name

    search_roots = [
        pm_root / candidate,
        pm_root / "plans" / "active" / candidate,
        pm_root / "plans" / "active" / "issues" / candidate,
        pm_root / "plans" / "active" / name,
        pm_root / "plans" / "active" / "issues" / name,
    ]
    for p in search_roots:
        if p.is_file():
            return p

    # Fallback: the target may have already graduated to plans/archive/** under the
    # same basename (a common shape once a satellite batch or superseding doc is
    # itself archived) -- do a bounded basename search rather than a full glob.
    archive_root = pm_root / "plans" / "archive"
    if archive_root.is_dir():
        for hit in archive_root.rglob(name):
            if hit.is_file():
                return hit
    return None


def find_covered_checkboxes(text: str, pm_root: Path) -> tuple[int, list[tuple[int, str]]]:
    """Return (covered_count, [(line_no, resolved_target_str), ...]) -- open checkboxes
    whose block carries an EXTRACTED/DUPLICATE-OF/SUPERSEDED-BY marker resolving to a
    real, existing file elsewhere in the corpus."""
    covered: list[tuple[int, str]] = []
    for line_no, is_open, block in _checkbox_blocks(text):
        if not is_open:
            continue
        m = MARKER_RE.search(block)
        if not m:
            continue
        target = _resolve_target(pm_root, m.group(1))
        if target is not None:
            covered.append((line_no, str(target.relative_to(pm_root))))
    return len(covered), covered


def find_dangling_markers(text: str, pm_root: Path) -> list[tuple[int, str]]:
    """Open checkboxes carrying an EXTRACTED/DUPLICATE-OF/SUPERSEDED-BY marker whose
    target does NOT resolve to a real file -- a stale pointer, itself a hygiene finding."""
    dangling: list[tuple[int, str]] = []
    for line_no, is_open, block in _checkbox_blocks(text):
        if not is_open:
            continue
        m = MARKER_RE.search(block)
        if not m:
            continue
        target = _resolve_target(pm_root, m.group(1))
        if target is None:
            dangling.append((line_no, m.group(1)))
    return dangling


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
    superseded_by = fm.get("superseded_by") or ""
    name = path.name.lower()
    is_aggregator = check_aggregator and any(marker in name for marker in AGGREGATOR_MARKERS)
    open_count = sum(1 for ln in text.splitlines() if OPEN_RE.match(ln))
    done_count = sum(1 for ln in text.splitlines() if DONE_RE.match(ln))
    return PlanStats(
        path, assigned_vm, status, execution_scope, superseded_by, is_aggregator, open_count, done_count, text=text
    )


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
    Deliberately no aggregator exclusion -- the real ingester has none."""
    return s.assigned_vm == "planning" and s.status not in ("draft", "superseded") and s.execution_scope != "local-only"


def _parse_superseded_by_targets(raw: str) -> list[str]:
    """Parse a `superseded_by:` frontmatter value into one or more candidate target
    strings. The corpus convention observed 2026-08-21 is a single bare doc slug (no
    `.md` extension) wrapped in a YAML flow-list, e.g. `[some_slug]` -- this also
    tolerates a bare scalar, a full `.md` path, and a multi-item list, since
    `parse_frontmatter` only strips outer quotes, not brackets or comma-lists."""
    value = raw.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [p.strip().strip("'\"") for p in value.split(",") if p.strip().strip("'\"")]


def _whole_doc_superseded_open(s: PlanStats, pm_root: Path) -> int:
    """If this doc is status:superseded with a resolvable superseded_by target, its
    entire open count is covered elsewhere -- return that count (0 if not applicable)."""
    if s.status != "superseded" or not s.superseded_by:
        return 0
    for candidate in _parse_superseded_by_targets(s.superseded_by):
        if _resolve_target(pm_root, candidate) is not None:
            return s.open_count
    return 0


def summarise(stats: list[PlanStats], issue_stats: list[PlanStats], pm_root: Path) -> dict:
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

    # planning-assigned open INCLUDING aggregators -- AO dispatches these too, so this
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

    # --- Cross-corpus dedup for issues (2026-08-21) ---
    issues_covered_by_marker = 0
    issues_covered_by_supersede = 0
    dangling_markers: list[dict] = []
    covered_detail: list[dict] = []
    for s in issue_stats:
        whole_doc_covered = _whole_doc_superseded_open(s, pm_root)
        if whole_doc_covered:
            issues_covered_by_supersede += whole_doc_covered
            covered_detail.append(
                {"doc": str(s.path.relative_to(pm_root)), "covered": whole_doc_covered, "via": "superseded_by"}
            )
            continue  # whole doc already fully accounted for; don't also scan its markers
        n_covered, hits = find_covered_checkboxes(s.text, pm_root)
        if n_covered:
            issues_covered_by_marker += n_covered
            covered_detail.append(
                {
                    "doc": str(s.path.relative_to(pm_root)),
                    "covered": n_covered,
                    "via": "extraction_marker",
                    "targets": sorted({t for _, t in hits}),
                }
            )
        for line_no, target in find_dangling_markers(s.text, pm_root):
            dangling_markers.append({"doc": str(s.path.relative_to(pm_root)), "line": line_no, "target": target})

    issues_open_deduped = issues_open - issues_covered_by_marker - issues_covered_by_supersede
    total_open_deduped = dedup_open + issues_open_deduped

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
        "cross_corpus_dedup": {
            "issues_covered_by_extraction_marker": issues_covered_by_marker,
            "issues_covered_by_supersede": issues_covered_by_supersede,
            "issues_open_deduped": issues_open_deduped,
            "total_open_deduped": total_open_deduped,
            "dangling_marker_count": len(dangling_markers),
            "dangling_markers": dangling_markers,
            "covered_detail": covered_detail,
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
    ap.add_argument(
        "--show-dangling", action="store_true", help="print every dangling extraction-marker finding (human mode)"
    )
    args = ap.parse_args()

    if not (args.pm_root / "plans" / "active").is_dir():
        print(f"error: no plans/active under {args.pm_root}", file=sys.stderr)
        return 2

    stats = collect(args.pm_root)
    issue_stats = collect_issues(args.pm_root)
    result = summarise(stats, issue_stats, args.pm_root)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    r = result
    print("Open-task count -- active plan corpus")
    print(f"  plans scanned:            {r['plans_scanned']}")
    print(f"  aggregator plans excluded:{r['aggregators_excluded']:>5}  (master/batch/consolidated/closeout/satellite)")
    print()
    print(f"  ALL active-plan open:     {r['all_active_open']:>5}   (done: {r['all_active_done']})")
    print(f"  DEDUPED open (plans-only headline): {r['deduped_open']:>5}   (done: {r['deduped_done']})")
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
    print(f"  Planning-assigned open INCL aggregators (~ AO dispatch pool, plans only): {_planning_incl_agg}")
    print()
    print(f"  Issues scanned: {r['issues_scanned']}  (plans/active/issues/*.md)")
    print(f"    ALL issues open (raw):   {r['issues_all_open']}   (done: {r['issues_all_done']})")
    print("    Issues open by assigned_vm (raw):")
    for vm, n in r["issues_open_by_assigned_vm"].items():
        print(f"      {vm:<10} {n:>5}")
    print()
    cc = r["cross_corpus_dedup"]
    print("  Cross-corpus dedup (issues already covered by a plan elsewhere):")
    _cov_marker = cc["issues_covered_by_extraction_marker"]
    _cov_supersede = cc["issues_covered_by_supersede"]
    print(f"    covered via EXTRACTED/DUPLICATE-OF marker (target resolves):  {_cov_marker}")
    print(f"    covered via status:superseded + superseded_by (target resolves): {_cov_supersede}")
    print(f"    issues open, DEDUPED:                                        {cc['issues_open_deduped']}")
    print(
        f"    dangling markers (target does NOT resolve -- still counted open, flagged): {cc['dangling_marker_count']}"
    )
    if args.show_dangling and cc["dangling_markers"]:
        for d in cc["dangling_markers"]:
            print(f"      {d['doc']}:{d['line']} -> '{d['target']}' (not found)")
    print()
    print("  " + "=" * 70)
    print(f"  TOTAL OPEN, DEDUPED ACROSS PLANS + ISSUES:  {cc['total_open_deduped']}")
    print("  (= deduped plans headline + issues open with covered items subtracted)")
    print("  " + "=" * 70)
    print()
    proxy = r["ao_backlog_proxy"]
    print("  AO_BACKLOG_PROXY (mirrors regen_backlog_from_plan.py's real ingestion gate -- NO aggregator")
    print("  exclusion; assigned_vm==planning, status not draft/superseded, execution_scope != local-only):")
    print(f"    plans_open:  {proxy['plans_open']:>5}")
    print(f"    issues_open: {proxy['issues_open']:>5}")
    print(f"    TOTAL:       {proxy['total_open']:>5}")
    print("  This is the number to quote for 'how big is the AO backlog' -- not the deduped headline above.")
    print("  Note: assigned_vm=planning is what the AO backlog dispatches; NA/missing are not dispatched.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
