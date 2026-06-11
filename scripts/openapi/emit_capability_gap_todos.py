#!/usr/bin/env python3
"""Escalation emitter — append needs_code_scan todos to the gap tracker.

Reads the capability manifest, finds ``needs_code_scan`` gap edges WITHOUT an
``agent_annotation``, and appends canonical
``- [ ] [AGENT] P2. …`` todos (target repo named + cold-start context) under
the ``## Escalated needs_code_scan (auto-emitted)`` section in the gap tracker:

    plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md

Idempotent on re-run: deduplicates against existing lines; will not append a
todo that is already present (exact match on the manifest edge reason text).

Usage:
    python emit_capability_gap_todos.py [--manifest PATH] [--tracker PATH]

The default manifest path is the canonical output location in UAC.
The default tracker path is relative to the PM repo root.

SSOT: plans/active/capability_wizard_and_manifest_2026_06_11.md Phase 5.
Plan: unified-trading-pm/plans/active/capability_wizard_and_manifest_2026_06_11.md
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_SCRIPT_DIR = Path(__file__).resolve().parent
_PM_ROOT = _SCRIPT_DIR.parent.parent
_WORKSPACE_ROOT = _PM_ROOT.parent

# Canonical section heading (created if absent; never duplicated)
_SECTION_HEADING = "## Escalated needs_code_scan (auto-emitted)"

# Target repo where the code-scan should be conducted + context for cold-start
_REPO_CONTEXT: dict[str, dict[str, str]] = {
    "gap_registry:sim_assumptions": {
        "repo": "strategy-service",
        "context": (
            "SIM_ASSUMPTIONS_REGISTRY backfill: scan "
            "strategy_service/engine/backtest/runner.py + "
            "strategy_service/engine/strategies/v2/base.py for matching/fill/predicate "
            "assumptions; populate unified_api_contracts/internal/architecture_v2/"
            "simulation_assumptions.py SIM_ASSUMPTIONS_REGISTRY"
        ),
    },
    "gap_registry:broker": {
        "repo": "unified-api-contracts",
        "context": (
            "BROKER_REGISTRY + COLLATERAL_REGISTRY backfill: scan each perp-venue "
            "execution adapter for accepted_perp_collateral declarations; populate "
            "unified_api_contracts/internal/architecture_v2/collateral_registry.py "
            "BROKER_REGISTRY and COLLATERAL_REGISTRY for all CeFi perp venues"
        ),
    },
    "gap_registry:order_semantics": {
        "repo": "execution-service",
        "context": (
            "VENUE_ORDER_SEMANTICS backfill: scan each venue execution adapter for "
            "TIF (FOK/IOC/post-only), make/take, ref-pricing mode, multi-leg delta "
            "ownership; populate unified_api_contracts/internal/architecture_v2/"
            "order_semantics.py VENUE_ORDER_SEMANTICS"
        ),
    },
}

_DEFAULT_REPO_CONTEXT = {
    "repo": "unified-api-contracts",
    "context": "Code-scan required; target repo + context to be determined by reviewer",
}


def _load_manifest(manifest_path: Path) -> list[dict]:
    """Load capability manifest edges from JSON."""
    if not manifest_path.exists():
        logger.error("Manifest not found at %s", manifest_path)
        sys.exit(1)
    with open(manifest_path) as fh:
        data = json.load(fh)
    edges = data.get("edges", [])  # noqa: qg-empty-fallback
    if not isinstance(edges, list):
        logger.error("Manifest 'edges' is not a list")
        sys.exit(1)
    return edges


def _find_unannotated_code_scan_edges(edges: list[dict]) -> list[dict]:
    """Return edges with gap_type == needs_code_scan and agent_annotation == null."""
    result = []
    for edge in edges:
        if edge.get("gap_type") == "needs_code_scan" and edge.get("agent_annotation") is None:
            result.append(edge)
    return result


def _build_todo_line(edge: dict) -> str:
    """Build the canonical todo line for a needs_code_scan edge."""
    from_node = edge.get("from_node_id", "")  # noqa: qg-empty-fallback
    reason = (edge.get("reason") or "").strip()
    ctx = _REPO_CONTEXT.get(from_node, _DEFAULT_REPO_CONTEXT)
    repo = ctx["repo"]
    context = ctx["context"]
    return (
        f"- [ ] [AGENT] P2. **{from_node}** — {reason}. "
        f"Target repo: `{repo}`. "
        f"Cold-start context: {context}. "
        f"(auto-emitted by emit_capability_gap_todos.py)"
    )


def _load_tracker(tracker_path: Path) -> list[str]:
    """Load the gap tracker markdown as a list of lines."""
    if not tracker_path.exists():
        logger.warning("Tracker not found at %s — will create empty tracker", tracker_path)
        return []
    with open(tracker_path) as fh:
        return fh.readlines()


def _find_section_index(lines: list[str], heading: str) -> int:
    """Return the line index of the section heading, or -1 if not found."""
    for i, line in enumerate(lines):
        if line.strip() == heading:
            return i
    return -1


def _line_is_duplicate(line: str, existing_lines: list[str]) -> bool:
    """Return True if a stripped version of the line already appears in existing_lines."""
    stripped = line.strip()
    return any(el.strip() == stripped for el in existing_lines)


def emit_todos(
    manifest_path: Path,
    tracker_path: Path,
    dry_run: bool = False,
) -> list[str]:
    """Main logic.  Returns list of todo lines that were (or would be) appended."""
    edges = _load_manifest(manifest_path)
    unannotated = _find_unannotated_code_scan_edges(edges)

    if not unannotated:
        logger.info("No unannotated needs_code_scan edges — nothing to emit")
        return []

    logger.info("Found %d unannotated needs_code_scan edge(s)", len(unannotated))

    tracker_lines = _load_tracker(tracker_path)

    section_idx = _find_section_index(tracker_lines, _SECTION_HEADING)

    # Collect lines to append (dedup against existing)
    new_todos: list[str] = []
    for edge in unannotated:
        todo = _build_todo_line(edge)
        if _line_is_duplicate(todo, tracker_lines):
            logger.info("  SKIP (duplicate): %s", todo[:80])
            continue
        new_todos.append(todo)

    if not new_todos:
        logger.info("All todos already present — nothing to emit (idempotent)")
        return []

    now_str = datetime.now(UTC).strftime("%Y-%m-%d")

    if section_idx == -1:
        # Section absent — append it at the end of the file
        logger.info("Section '%s' not found — appending at end of file", _SECTION_HEADING)
        insertion_lines: list[str] = [
            "\n",
            f"{_SECTION_HEADING}\n",
            "\n",
            f"*Auto-emitted {now_str} by `scripts/openapi/emit_capability_gap_todos.py`.*\n",
            "*Dedup-idempotent on re-run.  Only edges with `needs_code_scan` gap_type and no*\n",
            "*`agent_annotation` appear here.  Once annotated, edge drops off on next emit run.*\n",
            "\n",
        ]
        for todo in new_todos:
            insertion_lines.append(f"{todo}\n")
        insertion_lines.append("\n")

        if not dry_run:
            with open(tracker_path, "a") as fh:
                fh.writelines(insertion_lines)
            logger.info("Appended %d todo(s) to %s", len(new_todos), tracker_path)
    else:
        # Section exists — find the end of the section (next heading or EOF)
        end_idx = len(tracker_lines)
        for i in range(section_idx + 1, len(tracker_lines)):
            if tracker_lines[i].startswith("## ") or tracker_lines[i].startswith("# "):
                end_idx = i
                break

        # Insert new todos before the section end
        insert_at = end_idx
        # Back up past trailing blank lines to place todos cleanly
        while insert_at > section_idx + 1 and tracker_lines[insert_at - 1].strip() == "":
            insert_at -= 1

        new_lines: list[str] = []
        for todo in new_todos:
            new_lines.append(f"{todo}\n")

        if not dry_run:
            updated = tracker_lines[:insert_at] + new_lines + tracker_lines[insert_at:]
            with open(tracker_path, "w") as fh:
                fh.writelines(updated)
            logger.info("Inserted %d todo(s) into section '%s'", len(new_todos), _SECTION_HEADING)

    return new_todos


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit needs_code_scan escalation todos into the gap tracker")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to capability-manifest.json (default: UAC openapi/)",
    )
    parser.add_argument(
        "--tracker",
        type=Path,
        default=None,
        help="Path to the gap tracker markdown (default: PM plans/active/issues/…)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be appended without writing",
    )
    args = parser.parse_args()

    uac_root = _WORKSPACE_ROOT / "unified-api-contracts"
    manifest_path = args.manifest or (uac_root / "openapi" / "capability-manifest.json")
    tracker_path = args.tracker or (
        _PM_ROOT / "plans" / "active" / "issues" / "capability_wizard_gap_discovery_2026_06_11.md"
    )

    todos = emit_todos(manifest_path, tracker_path, dry_run=args.dry_run)

    print("\n" + "=" * 60)
    print("ESCALATION EMITTER — SUMMARY")
    print("=" * 60)
    print(f"manifest:      {manifest_path}")
    print(f"tracker:       {tracker_path}")
    print(f"dry_run:       {args.dry_run}")
    print(f"todos emitted: {len(todos)}")
    if todos:
        print("\nEmitted todos:")
        for t in todos:
            print(f"  {t}")
    else:
        print("(nothing new — all already present or no unannotated edges)")
    print("=" * 60)


if __name__ == "__main__":
    main()
