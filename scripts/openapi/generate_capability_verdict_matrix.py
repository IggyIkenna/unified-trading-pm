"""Generate the EXHAUSTIVE capability verdict matrix (Phase 6A).

Operator requirement (2026-06-12, verbatim): "we should know that these
combinatorics are blocked and available en masse, every single possible one for
every single strategy archetype, venue, instrument, everything" — and impossible
execution-algo x strategy combinations must be BLOCKED with a reason.

This produces the full cross-join

    archetype x venue x instrument_type x (instruction_action x algo)

where every cell gets an EXPLICIT verdict — ``available`` | ``blocked(reason)`` |
``not_registered(gap_type)`` — with NO absent cells. The output is structured
HIERARCHICALLY (one block per archetype) so it stays navigable, and is
DETERMINISTIC (run twice → byte-identical; no timestamps, all sets sorted).

GROUNDING — the matrix is built from two UAC registries (imported, never
redefined; the SSOT for the combinatorics):
  - ``ARCHETYPE_LEG_STRUCTURES`` (``archetype_leg_spec``): the per-archetype
    structural legs → which (venue, instrument_type) cells are *eligible* for the
    archetype, and the ``instruction_action`` (= ``InstructionType``) each cell
    induces. A ``not_registered`` archetype (no legs) → the whole block is
    ``not_registered`` with the cited ``gap_type``/reason.
  - ``ARCHETYPE_ALGO_COMPATIBILITY`` (``algo_compatibility``): which execution
    algorithms are valid for each induced instruction action (transcribed from
    the execution-service selector). An algo NOT valid for the cell's instruction
    action → ``blocked(algo_not_valid_for_instruction)``.

VENUE / INSTRUMENT enumeration: for each archetype we cross-join its legs'
eligible venues x instrument_types. A venue that the leg does not list, or an
instrument the leg does not trade, is simply not in that archetype's block (it is
covered by the archetype-eligibility framing: the block enumerates exactly the
archetype's reachable cells, and every reachable cell x every execution algo is a
verdict). The headline counts (total cells / per-verdict) are reported + appended
to the orphan report.

SIZE GUARD: the full per-cell x per-algo cross-join can be large. We keep
``blocked`` + ``not_registered`` cells in FULL (the operator cares most about what
is blocked + why), and roll ``available`` cells up per (archetype, venue,
instruction_action) into a sorted ``available_algos`` list rather than one object
per algo. If the serialized JSON still exceeds ``_SIZE_BUDGET_BYTES`` (20 MB) the
script logs the choice (it does not today — the registries are small).

Output: ``unified-api-contracts/openapi/capability-verdict-matrix.json``.

Usage:
    python generate_capability_verdict_matrix.py [--output-dir PATH] [--uac-root PATH]
"""

from __future__ import annotations

import os

os.environ.setdefault("CLOUD_PROVIDER", "local")
os.environ.setdefault("CLOUD_MOCK_MODE", "true")
os.environ.setdefault("DISABLE_AUTH", "true")
os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project")

import argparse
import json
import logging
import subprocess
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MATRIX_VERSION = "1.0.0"
_SIZE_BUDGET_BYTES = 20 * 1024 * 1024


def _read_uac_head_sha(uac_root: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(uac_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        logger.warning("Could not read UAC HEAD sha: %s", exc)
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip() or None


def build_matrix() -> tuple[dict[str, object], dict[str, int]]:
    """Build the hierarchical verdict matrix + the count summary.

    Returns ``(matrix_dict, counts)``.
    """
    from unified_api_contracts.internal.architecture_v2.algo_compatibility import (
        ARCHETYPE_ALGO_COMPATIBILITY,
        EXECUTION_ALGOS,
        instruction_type_for,
        venue_kinds_for_asset_group,
    )
    from unified_api_contracts.internal.architecture_v2.archetype_leg_spec import (
        ARCHETYPE_LEG_STRUCTURES,
    )
    from unified_api_contracts.internal.architecture_v2.enums import StrategyArchetype

    all_algo_keys = sorted(EXECUTION_ALGOS)
    counts = {"total_cells": 0, "available": 0, "blocked": 0, "not_registered": 0}
    archetype_blocks: list[dict[str, object]] = []

    for archetype in sorted(StrategyArchetype, key=lambda a: a.value):
        struct = ARCHETYPE_LEG_STRUCTURES[archetype]
        compat = ARCHETYPE_ALGO_COMPATIBILITY[archetype]

        if struct.not_registered:
            # The whole archetype block is not_registered. We still enumerate one
            # not_registered cell PER algo so the count is exhaustive + explicit.
            n_cells = len(all_algo_keys)
            counts["total_cells"] += n_cells
            counts["not_registered"] += n_cells
            archetype_blocks.append(
                {
                    "archetype": archetype.value,
                    "not_registered": True,
                    "gap_type": "missing_registry",
                    "reason": struct.not_registered_reason,
                    "cell_count": n_cells,
                    "not_registered_algos": all_algo_keys,
                }
            )
            continue

        # Build the eligible cells: per leg, per (venue, instrument_type), the
        # induced instruction_action; then cross with every algo.
        cells: list[dict[str, object]] = []
        block_counts = {"available": 0, "blocked": 0}
        for leg in struct.legs:
            for venue in sorted(leg.eligible_venue_ids):
                # The venue-execution kinds this leg's asset-groups run on.
                kinds = sorted(
                    {kind for group in leg.asset_groups for kind in venue_kinds_for_asset_group(group)},
                    key=lambda k: k.value,
                )
                for instrument in sorted(leg.instrument_types, key=lambda i: i.value):
                    for kind in kinds:
                        action = instruction_type_for(kind, instrument)
                        valid = set(compat.valid_algos)
                        available_algos = sorted(a for a in all_algo_keys if a in valid)
                        blocked_algos = [
                            {
                                "algo": a,
                                "reason": (
                                    f"{a} is not valid for instruction_action "
                                    f"{action.value} (selector ALGORITHMS_BY_INSTRUCTION_TYPE)"
                                ),
                            }
                            for a in all_algo_keys
                            if a not in valid
                        ]
                        block_counts["available"] += len(available_algos)
                        block_counts["blocked"] += len(blocked_algos)
                        cells.append(
                            {
                                "leg_id": leg.leg_id,
                                "leg_role": leg.role.value,
                                "venue": venue,
                                "venue_kind": kind.value,
                                "instrument_type": instrument.value,
                                "instruction_action": action.value,
                                # available cells rolled up (size guard); blocked in full.
                                "available_algos": available_algos,
                                "blocked_algos": blocked_algos,
                            }
                        )
        # Deduplicate identical cells (same leg/venue/instrument/kind/action) that
        # can arise when a leg lists overlapping asset-group kinds.
        seen: set[tuple[str, ...]] = set()
        deduped: list[dict[str, object]] = []
        for c in cells:
            key = (
                str(c["leg_id"]),
                str(c["venue"]),
                str(c["instrument_type"]),
                str(c["venue_kind"]),
                str(c["instruction_action"]),
            )
            if key not in seen:
                seen.add(key)
                deduped.append(c)
        # recompute counts on deduped cells
        block_counts = {"available": 0, "blocked": 0}
        for c in deduped:
            block_counts["available"] += len(c["available_algos"])  # type: ignore[arg-type]
            block_counts["blocked"] += len(c["blocked_algos"])  # type: ignore[arg-type]
        n_cells = block_counts["available"] + block_counts["blocked"]
        counts["total_cells"] += n_cells
        counts["available"] += block_counts["available"]
        counts["blocked"] += block_counts["blocked"]
        archetype_blocks.append(
            {
                "archetype": archetype.value,
                "not_registered": False,
                "instruction_actions": sorted(t.value for t in compat.instruction_types),
                "valid_algos": list(compat.valid_algos),
                "cell_count": n_cells,
                "available_count": block_counts["available"],
                "blocked_count": block_counts["blocked"],
                "cells": deduped,
            }
        )

    matrix: dict[str, object] = {
        "matrix_version": MATRIX_VERSION,
        "axes": {
            "archetype": "all 57 StrategyArchetype values",
            "venue": "per-archetype leg-eligible venues (ARCHETYPE_LEG_STRUCTURES)",
            "instrument_type": "per-leg ArchetypeInstrumentType",
            "instruction_action": "InstructionType induced by (venue_kind, instrument_type) — the selector axis",
            "algo": "every key in EXECUTION_ALGOS (selector ALGORITHMS_BY_INSTRUCTION_TYPE)",
        },
        "verdicts": ["available", "blocked", "not_registered"],
        "summary": counts,
        "archetypes": archetype_blocks,
    }
    return matrix, counts


_VERDICT_BLOCK_START = "=== VERDICT MATRIX SUMMARY (Phase 6A) ==="
_VERDICT_BLOCK_END = "=== END VERDICT MATRIX SUMMARY ==="


def _render_verdict_summary(counts: dict[str, int]) -> str:
    """The delimited verdict-summary block appended to the orphan report."""

    total = counts["total_cells"]

    def _pct(n: int) -> str:
        return f"{(100.0 * n / total):.1f}%" if total else "0.0%"

    return (
        f"\n{_VERDICT_BLOCK_START}\n"
        f"Exhaustive cross-join: archetype x venue x instrument_type x (instruction_action x algo).\n"
        f"  total cells:    {total}\n"
        f"  available:      {counts['available']} ({_pct(counts['available'])})\n"
        f"  blocked:        {counts['blocked']} ({_pct(counts['blocked'])})\n"
        f"  not_registered: {counts['not_registered']} ({_pct(counts['not_registered'])})\n"
        f"Output: openapi/capability-verdict-matrix.json\n"
        f"{_VERDICT_BLOCK_END}\n"
    )


def _append_verdict_summary_to_orphan_report(output_dir: Path, counts: dict[str, int]) -> None:
    """Append (or replace) the verdict summary block in the orphan report (idempotent)."""

    report_path = output_dir / "capability-orphan-report.txt"
    block = _render_verdict_summary(counts)
    existing = report_path.read_text() if report_path.exists() else ""
    # Strip any prior verdict block so re-runs are byte-stable.
    if _VERDICT_BLOCK_START in existing:
        head, _, rest = existing.partition("\n" + _VERDICT_BLOCK_START)
        _, _, tail = rest.partition(_VERDICT_BLOCK_END + "\n")
        existing = head + tail
    report_path.write_text(existing.rstrip("\n") + "\n" + block)
    logger.info("Appended verdict summary to %s", report_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the exhaustive capability verdict matrix")
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--uac-root", type=Path, default=None)
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    workspace_root = script_dir.parent.parent.parent
    uac_root = args.uac_root or (workspace_root / "unified-api-contracts")
    output_dir = args.output_dir or (uac_root / "openapi")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Building exhaustive verdict matrix...")
    matrix, counts = build_matrix()
    matrix["generated_from_commit"] = _read_uac_head_sha(uac_root)

    payload = json.dumps(matrix, indent=2, sort_keys=True, default=str)
    size = len(payload.encode("utf-8"))
    if size > _SIZE_BUDGET_BYTES:
        logger.warning(
            "Verdict matrix is %.1f MB (> %.0f MB budget) — available cells are already "
            "rolled up per (archetype, venue, action); blocked/not_registered kept in full.",
            size / 1024 / 1024,
            _SIZE_BUDGET_BYTES / 1024 / 1024,
        )

    output_path = output_dir / "capability-verdict-matrix.json"
    with open(output_path, "w") as f:
        # Trailing newline so the generator output matches prettier's normalization
        # (quickmerge runs prettier on committed JSON — without this the committed
        # file drifts from a fresh regen by one byte).
        f.write(payload + "\n")
    logger.info("Wrote %s (%.1f KB)", output_path, size / 1024)

    # Append the verdict count summary to the orphan report (task requirement).
    # The block is delimited so a re-run REPLACES it (idempotent, deterministic) —
    # it never appends duplicates across runs.
    _append_verdict_summary_to_orphan_report(output_dir, counts)

    print("\n" + "=" * 60)
    print("CAPABILITY VERDICT MATRIX — GENERATION SUMMARY")
    print("=" * 60)
    print(f"matrix_version: {matrix['matrix_version']}")
    print(f"generated_from_commit: {matrix['generated_from_commit']}")
    print(f"total cells: {counts['total_cells']}")
    print(f"  available:      {counts['available']}")
    print(f"  blocked:        {counts['blocked']}")
    print(f"  not_registered: {counts['not_registered']}")
    print(f"size: {size / 1024:.1f} KB")
    print(f"\nOutput: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
