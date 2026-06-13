#!/usr/bin/env python3
"""Minimal unlock-set engine + demand-weighted gap report (Wave-2 #1).

Reads the committed capability manifest, computes the minimal unlock set
(``unlock_distance`` + typed missing pieces) for every blocked edge, and emits:

  * ``openapi/capability-unlock-report.json`` — machine payload (roadmap ranked
    closest-first + impossible negatives + summary).
  * ``openapi/capability-unlock-report.md`` — the demand-weighted gap report
    (blocked edges ranked by ``unlock_distance`` ASC = highest-leverage first;
    demand is a documented placeholder 0 until the wizard demand counts land).

With ``--emit-todos`` it ALSO appends, for the N closest-to-unlock edges,
canonical ``- [ ] [SCRIPT] P2.`` roadmap todos into the gap tracker
(``plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md``) —
dedup-idempotent, reusing ``emit_capability_gap_todos.py``'s append pattern.

The engine is decoupled from the registry walk: it reads the already-generated
manifest JSON, so it runs anywhere (no ``.venv-workspace``) and is deterministic
(two runs are byte-identical).

Usage:
    python generate_capability_unlock_report.py [--manifest PATH] [--output-dir PATH]
                                                [--emit-todos] [--top-n N] [--tracker PATH]
                                                [--dry-run]

SSOT: plans/active/capability_wizard_and_manifest_2026_06_11.md Wave-2 #1.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import cast

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _capability_unlock import (
    UnlockEntry,
    build_report,
    build_todo_lines,
    compute_unlock_entries,
    load_manifest_edges,
    render_markdown,
)

_PM_ROOT = _SCRIPT_DIR.parent.parent
_WORKSPACE_ROOT = _PM_ROOT.parent

#: Canonical section heading in the gap tracker (created if absent; never duplicated).
_SECTION_HEADING = "## Closest-to-unlock roadmap (auto-emitted)"

#: Default number of closest-to-unlock edges to emit as roadmap todos.
_DEFAULT_TOP_N = 15


def _resolve_manifest(manifest_arg: str | None, workspace_arg: str | None) -> Path:
    if manifest_arg:
        return Path(manifest_arg)
    workspace_root = Path(workspace_arg) if workspace_arg else _WORKSPACE_ROOT
    return workspace_root / "unified-api-contracts" / "openapi" / "capability-manifest.json"


def _line_is_duplicate(line: str, existing: list[str]) -> bool:
    stripped = line.strip()
    return any(el.strip() == stripped for el in existing)


def _find_section_index(lines: list[str], heading: str) -> int:
    for i, line in enumerate(lines):
        if line.strip() == heading:
            return i
    return -1


def emit_roadmap_todos(
    entries: list[UnlockEntry],
    tracker_path: Path,
    top_n: int,
    dry_run: bool = False,
) -> list[str]:
    """Append the N closest-to-unlock roadmap todos to the tracker, dedup-idempotent.

    Mirrors ``emit_capability_gap_todos.py``: find/create the canonical section,
    skip any line already present (exact stripped match), insert the rest.
    """
    new_todos = build_todo_lines(entries, top_n)
    if not new_todos:
        logger.info("No roadmap todos to emit (no unlockable blocked edges)")
        return []

    tracker_lines = tracker_path.read_text().splitlines(keepends=True) if tracker_path.exists() else []
    section_idx = _find_section_index(tracker_lines, _SECTION_HEADING)

    pending = [t for t in new_todos if not _line_is_duplicate(t, tracker_lines)]
    if not pending:
        logger.info("All roadmap todos already present — nothing to emit (idempotent)")
        return []

    if section_idx == -1:
        block: list[str] = [
            "\n",
            f"{_SECTION_HEADING}\n",
            "\n",
            "*Auto-emitted by `scripts/openapi/generate_capability_unlock_report.py --emit-todos`.*\n",
            "*The N blocked edges closest to available (lowest `unlock_distance`) — the*\n",
            "*highest-leverage roadmap items. Dedup-idempotent on re-run.*\n",
            "\n",
        ]
        block.extend(f"{t}\n" for t in pending)
        block.append("\n")
        if not dry_run:
            with open(tracker_path, "a") as fh:
                fh.writelines(block)
        logger.info("Appended %d roadmap todo(s) under new section in %s", len(pending), tracker_path)
    else:
        end_idx = len(tracker_lines)
        for i in range(section_idx + 1, len(tracker_lines)):
            if tracker_lines[i].startswith("## ") or tracker_lines[i].startswith("# "):
                end_idx = i
                break
        insert_at = end_idx
        while insert_at > section_idx + 1 and tracker_lines[insert_at - 1].strip() == "":
            insert_at -= 1
        new_lines = [f"{t}\n" for t in pending]
        if not dry_run:
            updated = tracker_lines[:insert_at] + new_lines + tracker_lines[insert_at:]
            tracker_path.write_text("".join(updated))
        logger.info("Inserted %d roadmap todo(s) into section '%s'", len(pending), _SECTION_HEADING)

    return pending


def main() -> int:
    parser = argparse.ArgumentParser(description="Capability minimal-unlock-set engine + demand-weighted gap report")
    parser.add_argument("--manifest", default=None, help="Path to capability-manifest.json (default: sibling UAC)")
    parser.add_argument("--workspace-root", default=None, help="Workspace root (default: PM's parent)")
    parser.add_argument("--output-dir", default=None, help="Where to write the report (default: UAC openapi/)")
    parser.add_argument("--emit-todos", action="store_true", help="Append closest-to-unlock roadmap todos to tracker")
    parser.add_argument("--top-n", type=int, default=_DEFAULT_TOP_N, help="Number of closest-to-unlock edges to emit")
    parser.add_argument("--tracker", default=None, help="Gap-tracker markdown path (default: PM plans/active/issues/…)")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be emitted without writing tracker")
    args = parser.parse_args()

    manifest_arg = cast("str | None", args.manifest)
    workspace_arg = cast("str | None", args.workspace_root)
    output_arg = cast("str | None", args.output_dir)
    tracker_arg = cast("str | None", args.tracker)
    top_n = int(cast("int", args.top_n))
    emit = bool(cast("object", args.emit_todos))
    dry_run = bool(cast("object", args.dry_run))

    manifest_path = _resolve_manifest(manifest_arg, workspace_arg)
    if not manifest_path.exists():
        logger.error("Manifest not found: %s (run generate_capability_manifest.py first)", manifest_path)
        return 1

    raw = cast("dict[str, object]", json.loads(manifest_path.read_text()))
    manifest_commit = str(raw.get("generated_from_commit", "unknown"))
    edges = load_manifest_edges(manifest_path)
    entries = compute_unlock_entries(edges)

    output_dir = Path(output_arg) if output_arg else manifest_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    report = build_report(manifest_commit, entries)
    json_path = output_dir / "capability-unlock-report.json"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    logger.info("Wrote %s", json_path)

    md_path = output_dir / "capability-unlock-report.md"
    md_path.write_text(render_markdown(manifest_commit, entries))
    logger.info("Wrote %s", md_path)

    summary = cast("dict[str, object]", report["summary"])
    roadmap_n = int(cast("int", summary["roadmap_edges"]))
    impossible_n = int(cast("int", summary["impossible_edges"]))

    emitted: list[str] = []
    if emit:
        tracker_path = (
            Path(tracker_arg)
            if tracker_arg
            else _PM_ROOT / "plans" / "active" / "issues" / "capability_wizard_gap_discovery_2026_06_11.md"
        )
        emitted = emit_roadmap_todos(entries, tracker_path, top_n, dry_run=dry_run)

    print("\n" + "=" * 60)
    print("CAPABILITY UNLOCK REPORT — SUMMARY")
    print("=" * 60)
    print(f"manifest commit:       {manifest_commit}")
    print(f"blocked edges total:   {summary['blocked_edges_total']}")
    print(f"roadmap edges:         {roadmap_n}")
    print(f"impossible edges:      {impossible_n}")
    print(f"distance histogram:    {summary['unlock_distance_histogram']}")
    print(f"missing-piece counts:  {summary['missing_piece_counts']}")
    if emit:
        print(f"roadmap todos emitted: {len(emitted)} (top_n={top_n}, dry_run={dry_run})")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
