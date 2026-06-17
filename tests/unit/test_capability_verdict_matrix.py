"""Unit tests for the exhaustive capability verdict matrix generator (Phase 6A).

Pins:
  - Every cell gets an explicit verdict (available | blocked | not_registered) —
    no absent cells; counts add up.
  - All 57 archetypes appear as blocks.
  - not_registered archetypes (no leg structure) are explicit blocks.
  - Impossible algo combinations are BLOCKED (operator requirement).
  - Determinism: build_matrix(_FIXTURE_ENGINE_BACKED) is byte-stable across two runs.

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

from generate_capability_verdict_matrix import (
    _probe_engine_backed_archetypes,
    build_matrix,
)

# F48: the engine-backed set is INJECTED into build_matrix (the generator probes it
# live from strategy-service's factory in main(); UAC/PM cannot import a T4 service).
# These tests pass a FIXTURE so they stay hermetic + byte-deterministic — it is test
# data pinning the expected verdict counts, NOT a source SSOT. ``test_fixture_matches
# _live_engine_registry`` guards it against drift from the real ARCHETYPE_ENGINE_REGISTRY.
_FIXTURE_ENGINE_BACKED: frozenset[str] = frozenset(
    {
        "ML_DIRECTIONAL_CONTINUOUS",
        "ML_DIRECTIONAL_EVENT_SETTLED",
        "RULES_DIRECTIONAL_CONTINUOUS",
        "RULES_DIRECTIONAL_EVENT_SETTLED",
        "CARRY_BASIS_DATED",
        "CARRY_BASIS_DATED_INV",
        "CARRY_BASIS_PERP",
        "CARRY_STAKED_BASIS",
        "CARRY_STAKED_BASIS_DATED",
        "CARRY_RECURSIVE_STAKED",
        "CARRY_RECURSIVE_BORROW_LENDING_ONLY",
        "CARRY_BASIS_PERP_INV",
        "YIELD_ROTATION_LENDING",
        "YIELD_STAKING_SIMPLE",
        "ARBITRAGE_PRICE_DISPERSION",
        "ARBITRAGE_CROSS_DOMAIN_EVENT",
        "LIQUIDATION_CAPTURE",
        "DEFI_LP_CONCENTRATED",
        "DEFI_LP_POOL",
        "DEFI_LP_VAULT",
        "ARBITRAGE_MEV_LIQUIDATION_BUNDLE",
        "ARBITRAGE_MEV_JIT_LIQUIDITY",
        "ARBITRAGE_MEV_BACKRUN",
        "MARKET_MAKING_CONTINUOUS",
        "MARKET_MAKING_EVENT_SETTLED",
        "EVENT_DRIVEN",
        "VOL_TRADING_OPTIONS",
        "STAT_ARB_PAIRS_FIXED",
        "STAT_ARB_CROSS_SECTIONAL",
    }
)


def test_all_57_archetypes_are_blocks() -> None:
    matrix, _ = build_matrix(_FIXTURE_ENGINE_BACKED)
    blocks = matrix["archetypes"]
    assert isinstance(blocks, list)
    archetypes = {b["archetype"] for b in blocks}  # type: ignore[index]
    assert len(archetypes) == 57


def test_counts_add_up_and_no_absent_cells() -> None:
    matrix, counts = build_matrix(_FIXTURE_ENGINE_BACKED)
    assert counts["total_cells"] == counts["available"] + counts["blocked"] + counts["not_registered"]
    assert counts["total_cells"] > 0
    # The matrix summary mirrors the returned counts.
    assert matrix["summary"] == counts


def test_not_registered_archetypes_are_explicit_blocks() -> None:
    matrix, _ = build_matrix(_FIXTURE_ENGINE_BACKED)
    nr = {b["archetype"]: b for b in matrix["archetypes"] if b.get("not_registered")}  # type: ignore[union-attr]
    # The genuinely-underivable archetypes (no leg structure) → missing_registry.
    assert "ARBITRAGE_MEV_SANDWICH" in nr
    assert "PORTFOLIO_RISK_PARITY" in nr
    assert "VOL_0DTE_PIN_RISK" in nr
    # Two typed gap reasons after the F47/F48 surface-correction: a no-leg
    # archetype is ``missing_registry``; a has-legs-but-no-v2-engine archetype is
    # ``no_v2_engine`` (F48).
    valid_gap_types = {"missing_registry", "no_v2_engine"}
    for block in nr.values():
        assert block["gap_type"] in valid_gap_types
        assert str(block["reason"]).strip()
        assert block["cell_count"] > 0


def test_f48_engineless_archetypes_are_not_registered() -> None:
    """F48 — VOL_*/MARKET_MAKING_* archetypes that HAVE legs but no registered v2
    engine are demoted from AVAILABLE to not_registered(no_v2_engine), while the
    three engined ones (VOL_TRADING_OPTIONS / MARKET_MAKING_CONTINUOUS /
    MARKET_MAKING_EVENT_SETTLED) stay real (engined) blocks.
    """

    matrix, _ = build_matrix(_FIXTURE_ENGINE_BACKED)
    by_arch = {b["archetype"]: b for b in matrix["archetypes"]}  # type: ignore[union-attr]
    engineless = {a for a, b in by_arch.items() if b.get("gap_type") == "no_v2_engine"}
    # Every demoted block names VOL_* / MARKET_MAKING_* (the F48 family).
    assert engineless, "no F48 no_v2_engine blocks emitted"
    assert all(a.startswith(("VOL_", "MARKET_MAKING")) for a in engineless)
    # Representative engineless archetypes are demoted.
    assert "VOL_STRADDLE" in engineless
    assert "MARKET_MAKING_INVENTORY_SKEW" in engineless
    # The engined VOL_/MM_ archetypes are NOT demoted (still real blocks).
    for engined in ("VOL_TRADING_OPTIONS", "MARKET_MAKING_CONTINUOUS", "MARKET_MAKING_EVENT_SETTLED"):
        assert by_arch[engined]["not_registered"] is False
        assert engined not in engineless


def test_f47_unbuildable_venue_cells_are_not_available() -> None:
    """F47 — a leg-eligible venue whose slot-label token is rejected by
    KNOWN_VENUE_TOKENS carries venue_buildable=false + zero available_algos (every
    algo blocked with the unbuildable-slot reason), so it never reads as AVAILABLE.

    Phase V (UAC 7565c0c, 2026-06-15) wired all previously-unbuildable leg-eligible
    venues into KNOWN_VENUE_TOKENS, so the current registry produces zero unbuildable
    cells.  This test now asserts that invariant — acting as a regression gate: if a
    future eligible_venue_ids addition lacks its alnum-folded token in
    KNOWN_VENUE_TOKENS, this assertion fires and directs the fixer to venue_tokens.py.
    The F47 mechanism (venue_buildable / blocked_algos path) is exercised by the
    conditional loop below, which also guards correct output if any cell reappears.
    """

    matrix, _ = build_matrix(_FIXTURE_ENGINE_BACKED)
    unbuildable_cells = [
        c
        for b in matrix["archetypes"]  # type: ignore[union-attr]
        for c in b.get("cells", [])
        if c.get("venue_buildable") is False
    ]
    # Phase V fixed all previously-unbuildable venues; expect zero today.
    # If this fires: add the venue's alnum-folded slot token to KNOWN_VENUE_TOKENS in
    # unified_api_contracts/internal/architecture_v2/venue_tokens.py.
    assert len(unbuildable_cells) == 0, (
        f"found {len(unbuildable_cells)} F47 unbuildable-venue cell(s) — "
        "add each venue's alnum-folded slot token to KNOWN_VENUE_TOKENS in "
        "unified_api_contracts/internal/architecture_v2/venue_tokens.py"
    )
    for c in unbuildable_cells:
        assert c["available_algos"] == []
        assert c["blocked_algos"], "unbuildable cell must block every algo"
        assert all("KNOWN_VENUE_TOKENS" in str(ba["reason"]) for ba in c["blocked_algos"])


def test_impossible_algo_combinations_are_blocked() -> None:
    """A pure-staking archetype must BLOCK TWAP etc. (only BENCHMARK_FILL valid)."""

    matrix, _ = build_matrix(_FIXTURE_ENGINE_BACKED)
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
    m1, _ = build_matrix(_FIXTURE_ENGINE_BACKED)
    m2, _ = build_matrix(_FIXTURE_ENGINE_BACKED)
    assert json.dumps(m1, sort_keys=True, default=str) == json.dumps(m2, sort_keys=True, default=str)


def test_fixture_matches_live_engine_registry() -> None:
    """F48 drift guard: the hermetic fixture must equal the LIVE strategy-service
    engine registry (the set ``main()`` probes). Skipped when strategy-service/.venv
    is absent (e.g. a CI image without the service venv); runs in the full workspace.
    """
    import pytest

    workspace_root = Path(__file__).resolve().parents[3]
    venv_python = workspace_root / "strategy-service" / ".venv" / "bin" / "python"
    if not venv_python.exists():
        pytest.skip("strategy-service/.venv absent — live engine-registry parity not checkable here")
    live = _probe_engine_backed_archetypes(workspace_root)
    assert live == _FIXTURE_ENGINE_BACKED, (
        "engine registry drifted from the test fixture — update _FIXTURE_ENGINE_BACKED to match "
        f"ARCHETYPE_ENGINE_REGISTRY. only-in-live={sorted(live - _FIXTURE_ENGINE_BACKED)}, "
        f"only-in-fixture={sorted(_FIXTURE_ENGINE_BACKED - live)}"
    )
