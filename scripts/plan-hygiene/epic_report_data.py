#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: durable tooling (per-epic data feed for /plan-reconcile's HTML-artifact phase)
# Delete-when: never (standing epic-scoped counting entrypoint)
"""Gather one epic's real report data for /plan-reconcile's HTML-artifact-generation phase.

`count_open_tasks.py` has NO per-epic scoping flag (confirmed by reading its CLI args before
writing this script — it only takes `--pm-root`/`--json` and always sweeps the whole corpus).
This script scopes the SAME dedup counting methodology (aggregator-plan exclusion via
`AGGREGATOR_MARKERS`, the same open/done checkbox regexes) down to a single epic's child-doc
set, so a generated HTML report's headline numbers agree with what `count_open_tasks.py` would
show if summed only over that epic's docs.

"Child of an epic" means frontmatter `parent_epic: <slug>` — the docspec.py-aligned,
registry-driven definition (`rg "^parent_epic: <slug>$" plans/active/*.md
plans/active/issues/*.md`, replicated here via a direct frontmatter parse rather than a
subprocess grep). This is NEVER `regenerate_active_plan_inventory.py`'s filename-substring
"orphan" heuristic — see
/plans/active/epic_taxonomy_restructure_and_html_reconcile_2026_08_18.md's Why section for the
measured 3-of-4 false-positive rate that makes that script's logic wrong for this purpose.

The epic-slug registry is the same set `docspec.py`'s `load_registries()` uses: every
`plans/epics/*.md` filename stem except README.md (no separate allowlist to keep in sync, so
this script never drifts from what `parent_epic` frontmatter is actually validated against).

Usage:
    python scripts/plan-hygiene/epic_report_data.py --epic <slug> [--pm-root <path>] [--json]

An unrecognized --epic fails loudly and lists every valid slug — it never silently falls back
to treating the argument as something else.

Pure stdlib, read-only. No network, no cloud.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Mirrors count_open_tasks.py's AGGREGATOR_MARKERS exactly. Kept as a separate literal, not an
# import, so this stays a single self-contained script per script-homes.md's lifecycle-marker
# convention — if the two ever drift, that's a same-turn fix-both-places finding.
AGGREGATOR_MARKERS = ("master", "batch", "consolidat", "closeout", "satellite")

# Identical to count_open_tasks.py's OPEN_RE/DONE_RE (dash-only, not the star-bullet-inclusive
# variant SKILL.md's Phase 2 sweep uses) — deliberately, so this script's counts reconcile
# exactly against count_open_tasks.py's methodology rather than a different, stricter one.
OPEN_RE = re.compile(r"^\s*- \[ \]")
DONE_RE = re.compile(r"^\s*- \[[xX]\]")
OPERATOR_TAG_RE = re.compile(r"\[OPERATOR\]|BLOCKED-OPERATOR", re.IGNORECASE)


def parse_frontmatter(text: str) -> dict[str, str]:
    """Return a flat {key: value} for the leading YAML frontmatter block (simple scalars only).

    Identical logic to count_open_tasks.py's parser (kept local, not imported, for the same
    single-file-tooling reason noted above).
    """
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
            value = re.sub(r"\s+#.*$", "", value)
            out[m.group(1)] = value.strip().strip("'\"")
    return out


def load_epic_registry(pm_root: Path) -> set[str]:
    """Every plans/epics/*.md stem except README.md — the same set docspec.py's
    load_registries() (scripts/docs/docspec.py) builds for `parent_epic` validation."""
    epics_dir = pm_root / "plans" / "epics"
    if not epics_dir.is_dir():
        return set()
    return {p.stem for p in epics_dir.glob("*.md") if p.name != "README.md"}


@dataclass
class ChildDoc:
    path: Path
    doc_type: str  # "plan" | "issue"
    title: str
    status: str
    assigned_vm: str
    is_aggregator: bool
    open_count: int
    done_count: int
    operator_lines: list[str] = field(default_factory=list)


def scan_child(path: Path, *, doc_type: str, check_aggregator: bool) -> ChildDoc:
    text = path.read_text(encoding="utf-8", errors="replace")
    fm = parse_frontmatter(text)
    title = fm.get("title") or path.stem
    # parse_frontmatter only handles simple scalars (same limitation as count_open_tasks.py's
    # parser) — a multi-line YAML block-scalar title (`title: >-`) leaves just the block
    # indicator here; fall back to the filename stem rather than print a bare ">-".
    if title.strip(" -") in ("", ">", "|"):
        title = path.stem
    status = (fm.get("status") or "missing").lower()
    assigned_vm = (fm.get("assigned_vm") or "missing").lower()
    if assigned_vm == "human-planning":
        assigned_vm = "planning"
    name = path.name.lower()
    is_aggregator = check_aggregator and any(marker in name for marker in AGGREGATOR_MARKERS)
    lines = text.splitlines()
    open_count = sum(1 for ln in lines if OPEN_RE.match(ln))
    done_count = sum(1 for ln in lines if DONE_RE.match(ln))
    operator_lines = [ln.strip() for ln in lines if OPEN_RE.match(ln) and OPERATOR_TAG_RE.search(ln)]
    return ChildDoc(path, doc_type, title, status, assigned_vm, is_aggregator, open_count, done_count, operator_lines)


def find_children(pm_root: Path, slug: str) -> list[ChildDoc]:
    """Docs whose frontmatter `parent_epic` == slug exactly, across plans/active/*.md and
    plans/active/issues/*.md — mirrors `rg "^parent_epic: <slug>$"` against those two globs."""
    out: list[ChildDoc] = []
    active_dir = pm_root / "plans" / "active"
    for p in sorted(active_dir.glob("*.md")):
        if p.name == "INDEX.md" or p.name.startswith("_"):
            continue
        fm = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
        if fm.get("parent_epic") == slug:
            out.append(scan_child(p, doc_type="plan", check_aggregator=True))

    issues_dir = active_dir / "issues"
    if issues_dir.is_dir():
        for p in sorted(issues_dir.glob("*.md")):
            fm = parse_frontmatter(p.read_text(encoding="utf-8", errors="replace"))
            if fm.get("parent_epic") == slug:
                out.append(scan_child(p, doc_type="issue", check_aggregator=False))

    return out


def summarise(pm_root: Path, slug: str, children: list[ChildDoc]) -> dict:
    plans = [c for c in children if c.doc_type == "plan"]
    issues = [c for c in children if c.doc_type == "issue"]
    dedup = [c for c in children if not c.is_aggregator]  # issues are never aggregators

    operator_items = [
        {"doc": str(c.path.relative_to(pm_root)), "line": ln} for c in children for ln in c.operator_lines
    ]

    return {
        "epic_slug": slug,
        "plan_children_count": len(plans),
        "issue_children_count": len(issues),
        "aggregator_plan_count": sum(1 for c in plans if c.is_aggregator),
        "all_open": sum(c.open_count for c in children),
        "all_done": sum(c.done_count for c in children),
        "deduped_open": sum(c.open_count for c in dedup),
        "deduped_done": sum(c.done_count for c in dedup),
        "operator_item_count": len(operator_items),
        "operator_items": operator_items,
        "children": [
            {
                "path": str(c.path.relative_to(pm_root)),
                "doc_type": c.doc_type,
                "title": c.title,
                "status": c.status,
                "assigned_vm": c.assigned_vm,
                "is_aggregator": c.is_aggregator,
                "open_count": c.open_count,
                "done_count": c.done_count,
                "operator_lines": c.operator_lines,
            }
            for c in children
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    default_root = Path(__file__).resolve().parents[2]
    ap.add_argument("--epic", required=True, help="epic slug (matches a plans/epics/<slug>.md filename stem)")
    ap.add_argument("--pm-root", type=Path, default=default_root, help="unified-trading-pm repo root")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = ap.parse_args()

    if not (args.pm_root / "plans" / "active").is_dir():
        print(f"error: no plans/active under {args.pm_root}", file=sys.stderr)
        return 2

    registry = load_epic_registry(args.pm_root)
    if args.epic not in registry:
        print(f"error: '{args.epic}' is not a known epic slug under plans/epics/*.md", file=sys.stderr)
        print("valid slugs:", file=sys.stderr)
        for slug in sorted(registry):
            print(f"  {slug}", file=sys.stderr)
        return 2

    children = find_children(args.pm_root, args.epic)
    result = summarise(args.pm_root, args.epic, children)

    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    r = result
    print(f"Epic report data — {r['epic_slug']}")
    print(
        f"  plan children:      {r['plan_children_count']:>5}"
        f"  (aggregator-excluded from dedup: {r['aggregator_plan_count']})"
    )
    print(f"  issue children:     {r['issue_children_count']:>5}")
    print()
    print(f"  ALL open:           {r['all_open']:>5}   (done: {r['all_done']})")
    print(f"  DEDUPED open (headline): {r['deduped_open']:>5}   (done: {r['deduped_done']})")
    print()
    print(f"  [OPERATOR]-tagged open items: {r['operator_item_count']}")
    for item in r["operator_items"]:
        print(f"    {item['doc']}: {item['line']}")
    print()
    print("  Children:")
    for c in r["children"]:
        agg = " [AGGREGATOR]" if c["is_aggregator"] else ""
        print(f"    [{c['doc_type']}] {c['path']}{agg}")
        print(
            f"        title={c['title']!r} status={c['status']} assigned_vm={c['assigned_vm']}"
            f" open={c['open_count']} done={c['done_count']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
