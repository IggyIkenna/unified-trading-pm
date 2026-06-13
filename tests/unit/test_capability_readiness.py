"""Unit tests for the per-edge readiness annotation pass (Wave-2 #2).

Pins:
  - Known live-cluster-owned archetypes resolve to the right tier from real
    evidence (carry_staked_basis / arbitrage_price_dispersion → live-proven,
    cited by a PROD-tier LIVE_CLUSTER_REGISTRY row).
  - An archetype with NO evidence defaults HONESTLY to backtest-only — the pass
    never over-claims (no live-proven without a cited registry row).
  - STAGING-only owners → staging-proven; PROD beats STAGING (best-tier wins).
  - The C/D/B gate mapping is total over the closed tier set.
  - Readiness is ADDITIVE: annotating never mutates status/gap_type and never
    flips an edge's availability (regression-safe).
  - Determinism: resolution + report rendering are byte-stable across two runs.

Plan: plans/active/capability_wizard_and_manifest_2026_06_11.md Wave-2 #2.
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

from _capability_readiness import (
    READINESS_BACKTEST_ONLY,
    READINESS_LIVE_PROVEN,
    READINESS_SHADOW_OBSERVED,
    READINESS_STAGING_PROVEN,
    READINESS_TIERS,
    READINESS_TO_GATE,
    annotate_edges_with_readiness,
    build_live_cluster_index,
    build_readiness_report,
    render_readiness_markdown,
    resolve_archetype_readiness,
    tier_distribution,
)
from unified_api_contracts.internal.architecture_v2.capability_manifest import (
    CapabilityEdge,
    CapabilityEdgeStatus,
    CapabilityNode,
    CapabilityNodeKind,
)

# A small hand-built node/edge fixture (no registry walk needed).
_KNOWN_LIVE = "CARRY_STAKED_BASIS"  # owned by a PROD-tier strategy cluster
_KNOWN_LIVE_2 = "ARBITRAGE_PRICE_DISPERSION"
_NO_EVIDENCE = "ARBITRAGE_MEV_SANDWICH"  # never owned by a live cluster


def _arch(node_id: str) -> CapabilityNode:
    return CapabilityNode(kind=CapabilityNodeKind.ARCHETYPE, node_id=node_id, label=node_id.title())


def _edge(from_id: str, to_id: str, relation: str = "supports") -> CapabilityEdge:
    return CapabilityEdge(
        from_node_id=from_id,
        to_node_id=to_id,
        relation=relation,
        status=CapabilityEdgeStatus.AVAILABLE,
    )


def test_known_live_archetypes_resolve_live_proven_with_cited_evidence() -> None:
    verdicts = resolve_archetype_readiness([_KNOWN_LIVE, _KNOWN_LIVE_2])
    for arch in (_KNOWN_LIVE, _KNOWN_LIVE_2):
        v = verdicts[arch]
        assert v.readiness == READINESS_LIVE_PROVEN
        # Every non-backtest-only stamp NAMES its evidence source.
        assert v.evidence.startswith("live_cluster_registry:"), v.evidence
        assert v.evidence.strip() != "live_cluster_registry:"
        assert v.gate == READINESS_TO_GATE[READINESS_LIVE_PROVEN]


def test_absent_evidence_defaults_to_backtest_only_never_overclaims() -> None:
    verdicts = resolve_archetype_readiness([_NO_EVIDENCE])
    v = verdicts[_NO_EVIDENCE]
    assert v.readiness == READINESS_BACKTEST_ONLY
    # The honest default carries NO evidence claim.
    assert v.evidence == ""
    assert v.gate == READINESS_TO_GATE[READINESS_BACKTEST_ONLY]


def test_staging_only_owner_resolves_staging_proven_and_prod_beats_staging() -> None:
    # Synthetic index: one archetype only-STAGING, one with BOTH (PROD must win).
    idx = {
        "ONLY_STAGING": (READINESS_STAGING_PROVEN, "strategy-live-foo"),
        "BOTH_TIERS": (READINESS_LIVE_PROVEN, "strategy-live-bar"),
    }
    verdicts = resolve_archetype_readiness(["ONLY_STAGING", "BOTH_TIERS"], cluster_index=idx)
    assert verdicts["ONLY_STAGING"].readiness == READINESS_STAGING_PROVEN
    assert verdicts["BOTH_TIERS"].readiness == READINESS_LIVE_PROVEN


def test_real_cluster_index_only_yields_staging_or_live() -> None:
    idx = build_live_cluster_index()
    assert idx, "live-cluster registry produced no archetype owners"
    for tier, name in idx.values():
        assert tier in (READINESS_STAGING_PROVEN, READINESS_LIVE_PROVEN)
        assert name  # cited cluster name is non-empty


def test_committed_override_can_set_shadow_observed_but_never_downgrades() -> None:
    idx = {"LIVE_ARCH": (READINESS_LIVE_PROVEN, "strategy-live-x")}
    overrides = {
        "BACKTEST_ARCH": (READINESS_SHADOW_OBSERVED, "shadow_ledger:run-123"),
        "LIVE_ARCH": (READINESS_SHADOW_OBSERVED, "shadow_ledger:run-456"),  # must NOT downgrade
    }
    verdicts = resolve_archetype_readiness(["BACKTEST_ARCH", "LIVE_ARCH"], cluster_index=idx, overrides=overrides)
    # An override is the only route to shadow-observed.
    assert verdicts["BACKTEST_ARCH"].readiness == READINESS_SHADOW_OBSERVED
    assert verdicts["BACKTEST_ARCH"].evidence == "shadow_ledger:run-123"
    # A stale shadow override never hides a genuine live-proven (best-tier wins).
    assert verdicts["LIVE_ARCH"].readiness == READINESS_LIVE_PROVEN


def test_gate_mapping_total_over_closed_tier_set() -> None:
    assert set(READINESS_TO_GATE) == set(READINESS_TIERS)
    assert len(READINESS_TIERS) == 4


def test_annotation_is_additive_never_flips_availability() -> None:
    nodes = [_arch(_KNOWN_LIVE), _arch(_NO_EVIDENCE)]
    edges = [
        _edge(_KNOWN_LIVE, "perp"),
        _edge(_NO_EVIDENCE, "spot"),
        _edge("venue:binance", "ethereum"),  # non-archetype edge — untouched
    ]
    orig_status = [(e.from_node_id, e.to_node_id, e.status, e.gap_type) for e in edges]
    new_edges, verdicts = annotate_edges_with_readiness(nodes, edges)

    assert len(new_edges) == len(edges)
    # status/gap_type are IDENTICAL before/after — pure additive metadata.
    new_status = [(e.from_node_id, e.to_node_id, e.status, e.gap_type) for e in new_edges]
    assert new_status == orig_status

    by_from = {e.from_node_id: e for e in new_edges}
    assert by_from[_KNOWN_LIVE].readiness == READINESS_LIVE_PROVEN
    assert by_from[_NO_EVIDENCE].readiness == READINESS_BACKTEST_ONLY
    # A non-archetype edge gets no readiness stamp (left None).
    assert by_from["venue:binance"].readiness is None
    assert set(verdicts) == {_KNOWN_LIVE, _NO_EVIDENCE}


def test_tier_distribution_zero_fills_all_tiers() -> None:
    verdicts = resolve_archetype_readiness([_KNOWN_LIVE, _NO_EVIDENCE])
    dist = tier_distribution(verdicts)
    assert set(dist) == set(READINESS_TIERS)
    assert dist[READINESS_LIVE_PROVEN] == 1
    assert dist[READINESS_BACKTEST_ONLY] == 1
    assert dist[READINESS_SHADOW_OBSERVED] == 0


def test_determinism_resolution_and_report() -> None:
    archs = [_KNOWN_LIVE, _KNOWN_LIVE_2, _NO_EVIDENCE]
    v1 = resolve_archetype_readiness(archs)
    v2 = resolve_archetype_readiness(archs)
    r1 = build_readiness_report("deadbeef", v1)
    r2 = build_readiness_report("deadbeef", v2)
    assert json.dumps(r1, sort_keys=True, default=str) == json.dumps(r2, sort_keys=True, default=str)
    assert render_readiness_markdown("deadbeef", v1) == render_readiness_markdown("deadbeef", v2)
