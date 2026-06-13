"""Unit tests for the minimal-unlock-set engine (Wave-2 #1).

Pins:
  - unlock_distance is computed correctly for known blocked-edge shapes
    (logical_dead_end → None/impossible; missing_registry/has_leg → leg-spec;
    needs_code_scan → code-scan; partial caveat → typed piece).
  - The ranking is closest-first (unlock_distance ASC; impossible last).
  - compute_unlock_entries() is deterministic across two runs.
  - The report payload counts add up and demand is the documented placeholder 0.
  - Real committed manifest: every roadmap entry has distance == len(pieces)
    and every impossible entry has distance None.

Plan: plans/active/capability_wizard_and_manifest_2026_06_11.md Wave-2 #1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure the scripts/openapi helpers are on the path for direct import.
_SCRIPTS_OPENAPI = Path(__file__).resolve().parent.parent.parent / "scripts" / "openapi"
if str(_SCRIPTS_OPENAPI) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_OPENAPI))

from _capability_unlock import (
    PIECE_CODE_SCAN,
    PIECE_CONFIG,
    PIECE_EXTRACTION,
    PIECE_IMPOSSIBLE,
    PIECE_LEG_SPEC,
    PIECE_REGISTRY,
    build_report,
    build_todo_lines,
    compute_unlock_entries,
    render_markdown,
)

_MANIFEST = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "unified-api-contracts"
    / "openapi"
    / "capability-manifest.json"
)


def _fixture_edges() -> list[dict[str, object]]:
    """A small hand-built edge set covering each blocked-edge shape."""
    return [
        # logical dead-end → impossible (distance None)
        {
            "from_node_id": "archetype:A",
            "to_node_id": "execution_algo:TWAP",
            "relation": "uses_algo",
            "status": "not_available",
            "gap_type": "logical_dead_end",
            "reason": "TWAP not valid for this archetype.",
        },
        # explicit negative (no gap_type) → impossible
        {
            "from_node_id": "collateral:binance",
            "to_node_id": "collateral_asset:stETH",
            "relation": "accepts_collateral",
            "status": "not_available",
            "gap_type": None,
            "reason": "binance rejects stETH.",
        },
        # missing_registry on has_leg → leg-spec (distance 1)
        {
            "from_node_id": "ARCH_B",
            "to_node_id": "ARCH_B",
            "relation": "has_leg:legs",
            "status": "not_registered",
            "gap_type": "missing_registry",
            "reason": "ARCH_B has no leg structure in ARCHETYPE_LEG_STRUCTURES yet.",
        },
        # missing_registry generic → registry-entry (distance 1)
        {
            "from_node_id": "data_source:foo",
            "to_node_id": "data_source:foo",
            "relation": "supports_mode:live",
            "status": "not_registered",
            "gap_type": "missing_registry",
            "reason": "live-mode capability for foo not yet codified in a UAC registry.",
        },
        # needs_code_scan → code-scan (distance 1)
        {
            "from_node_id": "gap_registry:sim_assumptions",
            "to_node_id": "gap_registry:sim_assumptions",
            "relation": "registry_gap",
            "status": "not_registered",
            "gap_type": "needs_code_scan",
            "reason": "Simulation assumptions registry is honest-empty — needs_code_scan.",
        },
        # missing_extraction → extraction (distance 1)
        {
            "from_node_id": "min_data_to_run:feature_lookback",
            "to_node_id": "min_data_to_run:feature_lookback",
            "relation": "min_data_to_run",
            "status": "partial",
            "gap_type": "missing_extraction",
            "reason": "ML training-window factor pending extraction.",
        },
        # partial caveat (no gap_type) → typed config piece
        {
            "from_node_id": "ARB",
            "to_node_id": "venue:cme",
            "relation": "supports",
            "status": "partial",
            "gap_type": None,
            "reason": "Cross-product routing policy not declared in UAC (gap #10).",
        },
        # an available edge — must NOT appear in unlock entries
        {
            "from_node_id": "ARB",
            "to_node_id": "venue:binance",
            "relation": "supports",
            "status": "available",
            "gap_type": None,
            "reason": None,
        },
    ]


def test_unlock_distance_per_known_shape() -> None:
    entries = compute_unlock_entries(_fixture_edges())
    by_key = {e.edge_key(): e for e in entries}

    # available edge is excluded.
    assert "ARB|supports|venue:binance" not in by_key

    # logical_dead_end and explicit negative → impossible, distance None.
    dead = by_key["archetype:A|uses_algo|execution_algo:TWAP"]
    assert dead.unlock_distance is None
    assert dead.missing_pieces == (PIECE_IMPOSSIBLE,)
    neg = by_key["collateral:binance|accepts_collateral|collateral_asset:stETH"]
    assert neg.unlock_distance is None
    assert neg.missing_pieces == (PIECE_IMPOSSIBLE,)

    # leg / registry / code-scan / extraction / config → distance 1, correct piece.
    assert by_key["ARCH_B|has_leg:legs|ARCH_B"].missing_pieces == (PIECE_LEG_SPEC,)
    assert by_key["data_source:foo|supports_mode:live|data_source:foo"].missing_pieces == (PIECE_REGISTRY,)
    assert by_key["gap_registry:sim_assumptions|registry_gap|gap_registry:sim_assumptions"].missing_pieces == (
        PIECE_CODE_SCAN,
    )
    assert by_key[
        "min_data_to_run:feature_lookback|min_data_to_run|min_data_to_run:feature_lookback"
    ].missing_pieces == (PIECE_EXTRACTION,)
    assert by_key["ARB|supports|venue:cme"].missing_pieces == (PIECE_CONFIG,)

    # every roadmap entry's distance equals its piece count.
    for e in entries:
        if e.unlock_distance is not None:
            assert e.unlock_distance == len(e.missing_pieces)


def test_ranking_is_closest_first() -> None:
    entries = compute_unlock_entries(_fixture_edges())
    # All non-impossible (distance 1) come before all impossible (None).
    seen_impossible = False
    for e in entries:
        if e.unlock_distance is None:
            seen_impossible = True
        else:
            # once we've seen an impossible entry, no roadmap entry may follow.
            assert not seen_impossible, "roadmap entry appeared after an impossible one — not closest-first"
    # within distance, sorted by edge_key (stable).
    roadmap_keys = [e.edge_key() for e in entries if e.unlock_distance is not None]
    assert roadmap_keys == sorted(roadmap_keys)


def test_determinism() -> None:
    e1 = compute_unlock_entries(_fixture_edges())
    e2 = compute_unlock_entries(_fixture_edges())
    assert [x.to_dict() for x in e1] == [x.to_dict() for x in e2]


def test_report_counts_add_up_and_demand_placeholder() -> None:
    entries = compute_unlock_entries(_fixture_edges())
    report = build_report("test-sha", entries)
    summary = report["summary"]
    assert isinstance(summary, dict)
    assert summary["blocked_edges_total"] == summary["roadmap_edges"] + summary["impossible_edges"]
    roadmap = report["roadmap"]
    assert isinstance(roadmap, list)
    # demand is the documented placeholder 0 on every roadmap row.
    for row in roadmap:
        assert isinstance(row, dict)
        assert row["demand"] == 0
        assert row["unlock_distance"] is not None


def test_todo_lines_are_closest_first_and_skip_impossible() -> None:
    entries = compute_unlock_entries(_fixture_edges())
    lines = build_todo_lines(entries, top_n=10)
    # Impossible edges are never emitted as roadmap todos.
    assert all("execution_algo:TWAP" not in line for line in lines)
    assert all(line.startswith("- [ ] [SCRIPT] P2.") for line in lines)
    # number of todos == number of roadmap entries (≤ top_n).
    roadmap = [e for e in entries if e.unlock_distance is not None]
    assert len(lines) == len(roadmap)


def test_real_manifest_invariants() -> None:
    """Against the committed manifest: distances are coherent + ranking holds."""
    if not _MANIFEST.exists():
        return  # manifest not generated in this environment — skip silently
    raw = json.loads(_MANIFEST.read_text())
    edges = raw["edges"]
    entries = compute_unlock_entries(edges)
    assert entries, "committed manifest produced no blocked edges"
    # Invariant: roadmap distance == piece count; impossible → None.
    for e in entries:
        if PIECE_IMPOSSIBLE in e.missing_pieces:
            assert e.unlock_distance is None
        else:
            assert e.unlock_distance == len(e.missing_pieces)
    # Ranking: impossible entries are strictly last.
    distances = [(e.unlock_distance is None) for e in entries]
    assert distances == sorted(distances), "impossible entries must rank last"
    # The markdown renders without error and is non-empty.
    md = render_markdown("sha", entries)
    assert md.startswith("# Capability unlock report")
