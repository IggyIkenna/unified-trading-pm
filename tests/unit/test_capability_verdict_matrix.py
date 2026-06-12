"""Unit tests for the exhaustive capability verdict matrix generator (Phase 6A).

Pins:
  - Every cell gets an explicit verdict (available | blocked | not_registered) —
    no absent cells; counts add up.
  - All 57 archetypes appear as blocks.
  - not_registered archetypes (no leg structure) are explicit blocks.
  - Impossible algo combinations are BLOCKED (operator requirement).
  - Determinism: build_matrix() is byte-stable across two runs.

Plan: plans/active/capability_wizard_and_manifest_2026_06_11.md Phase 6A.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure the scripts/openapi helpers are on the path for direct import.
_SCRIPTS_OPENAPI = Path(__file__).resolve().parent.parent.parent / "scripts" / "openapi"
if str(_SCRIPTS_OPENAPI) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_OPENAPI))

os.environ.setdefault("CLOUD_PROVIDER", "local")
os.environ.setdefault("CLOUD_MOCK_MODE", "true")
os.environ.setdefault("DISABLE_AUTH", "true")
os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project")

from generate_capability_verdict_matrix import build_matrix


def test_all_57_archetypes_are_blocks() -> None:
    matrix, _ = build_matrix()
    blocks = matrix["archetypes"]
    assert isinstance(blocks, list)
    archetypes = {b["archetype"] for b in blocks}  # type: ignore[index]
    assert len(archetypes) == 57


def test_counts_add_up_and_no_absent_cells() -> None:
    matrix, counts = build_matrix()
    assert counts["total_cells"] == counts["available"] + counts["blocked"] + counts["not_registered"]
    assert counts["total_cells"] > 0
    # The matrix summary mirrors the returned counts.
    assert matrix["summary"] == counts


def test_not_registered_archetypes_are_explicit_blocks() -> None:
    matrix, _ = build_matrix()
    nr = {b["archetype"]: b for b in matrix["archetypes"] if b.get("not_registered")}  # type: ignore[union-attr]
    # The 6 genuinely-underivable archetypes (Phase 6A).
    assert "ARBITRAGE_MEV_SANDWICH" in nr
    assert "PORTFOLIO_RISK_PARITY" in nr
    assert "VOL_0DTE_PIN_RISK" in nr
    for block in nr.values():
        assert block["gap_type"] == "missing_registry"
        assert str(block["reason"]).strip()
        assert block["cell_count"] > 0


def test_impossible_algo_combinations_are_blocked() -> None:
    """A pure-staking archetype must BLOCK TWAP etc. (only BENCHMARK_FILL valid)."""

    matrix, _ = build_matrix()
    by_arch = {b["archetype"]: b for b in matrix["archetypes"]}  # type: ignore[union-attr]
    yss = by_arch["YIELD_STAKING_SIMPLE"]
    assert yss["not_registered"] is False
    # Its valid algo set is only BENCHMARK_FILL → every cell blocks the others.
    assert yss["valid_algos"] == ["BENCHMARK_FILL"]
    assert yss["blocked_count"] > 0
    # Spot-check a cell: TWAP must be in blocked_algos.
    cells = yss["cells"]
    assert cells, "YIELD_STAKING_SIMPLE has no cells"
    blocked_keys = {ba["algo"] for c in cells for ba in c["blocked_algos"]}  # type: ignore[index]
    assert "TWAP" in blocked_keys
    assert "BENCHMARK_FILL" not in blocked_keys  # always valid


def test_determinism() -> None:
    m1, _ = build_matrix()
    m2, _ = build_matrix()
    assert json.dumps(m1, sort_keys=True, default=str) == json.dumps(m2, sort_keys=True, default=str)
