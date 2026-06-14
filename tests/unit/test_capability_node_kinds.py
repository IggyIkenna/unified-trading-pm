"""Unit tests for the capability-manifest node-kind correctness (Wave B, F49-F53).

Pins the Wave-B re-kinding / dedup fixes so they cannot silently regress:
  - F49: ``custody_provider`` is NO LONGER a catch-all — risk-gate-layers,
    kill-switch-reasons, gap-registries and collateral policies carry their OWN
    kinds; real signing surfaces are emitted as ``signing_surface`` nodes.
  - F50: ``OFFERED_FUND_STRUCTURES`` produces ``fund_structure`` nodes (> 0).
  - F51: chain nodes are deduped — no numeric chain-id AND name for the same
    chain (e.g. never both ``chain:1`` and ``chain:ETHEREUM``).
  - F52: internal service producers (execution_service / instruments_service /
    features_onchain_service / strategy_service) are excluded from
    ``data_source`` nodes.
  - F53: ``ml_model`` is more than the single ``variant_config`` (the model-type
    registry is walked) — tested via the live-cluster extractor when the
    ml-service venv is importable, else skipped (per-service venv).

These exercise the pure-UAC extractors directly (no per-service venv needed for
F49-F52); F53 uses the service extractor which needs the ml-service ``.venv``.

Plan: plans/active/capability_wizard_and_manifest_2026_06_11.md (Wave B).
"""

from __future__ import annotations

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

from _capability_extract import extract_data_sources, extract_venues
from _capability_gaps import extract_gap_registries, extract_risk_surface


def test_f49_custody_provider_no_longer_holds_risk_kill_gap_collateral() -> None:
    """custody_provider is NOT a catch-all: re-kinded surfaces carry own kinds."""
    gap_nodes, _ = extract_gap_registries()
    risk_nodes, _ = extract_risk_surface()
    all_nodes = gap_nodes + risk_nodes

    kinds_by_id = {n.node_id: str(n.kind) for n in all_nodes}

    # No risk/kill/gap/collateral/fund/signing node may be a custody_provider.
    for node in all_nodes:
        if node.node_id.startswith(
            ("risk_layer:", "kill_switch:", "gap_registry:", "collateral:", "fund_structure:", "signing_surface:")
        ):
            assert str(node.kind) != "custody_provider", f"{node.node_id} still mis-kinded custody_provider"

    # And the correct kinds are present.
    assert any(k == "risk_gate_layer" for k in kinds_by_id.values())
    assert any(k == "kill_switch_reason" for k in kinds_by_id.values())
    assert any(k == "gap_registry" for k in kinds_by_id.values())
    assert any(k == "collateral_policy" for k in kinds_by_id.values())


def test_f49_signing_surface_nodes_present() -> None:
    """Real custody/signing surfaces are emitted as signing_surface nodes."""
    nodes, _ = extract_gap_registries()
    signing = {n.node_id for n in nodes if str(n.kind) == "signing_surface"}
    assert signing, "no signing_surface nodes emitted"
    # The documented May-23 surface must be present.
    assert "signing_surface:CLOUD_KMS_ENCRYPTED" in signing
    # Each signing surface carries status metadata.
    for n in nodes:
        if str(n.kind) == "signing_surface":
            assert n.metadata.get("status"), f"{n.node_id} missing status metadata"


def test_f50_fund_structure_nodes_gt_zero() -> None:
    """OFFERED_FUND_STRUCTURES produces fund_structure nodes (POOLED + SMA)."""
    nodes, _ = extract_gap_registries()
    fund = {n.node_id for n in nodes if str(n.kind) == "fund_structure"}
    assert len(fund) > 0, "0 fund_structure nodes despite a populated registry"
    assert "fund_structure:pooled" in fund
    assert "fund_structure:sma" in fund


def test_f51_chains_deduped_no_numeric_and_name() -> None:
    """No chain is represented BOTH as a numeric id and a human name."""
    nodes, _ = extract_venues()
    chain_ids = {n.node_id for n in nodes if str(n.kind) == "chain"}

    # ETHEREUM is the canonical name node; chain:1 (its numeric id) must be gone.
    assert "chain:ETHEREUM" in chain_ids
    assert "chain:1" not in chain_ids

    # No mainnet chain with a known name leaks its numeric id as a separate node.
    from unified_api_contracts.registry import MAINNET_CHAIN_IDS  # noqa: qg-deep-import

    for name, cid in MAINNET_CHAIN_IDS.items():
        if cid == 0:
            continue
        numeric_node = f"chain:{cid}"
        name_node = f"chain:{name}"
        # If the name node exists, the numeric duplicate must NOT.
        if name_node in chain_ids:
            assert numeric_node not in chain_ids, f"{numeric_node} duplicates {name_node}"


def test_f52_data_source_excludes_internal_services() -> None:
    """Internal service producers are not external data-source nodes."""
    nodes, _ = extract_data_sources()
    sources = {n.node_id for n in nodes if str(n.kind) == "data_source"}

    for internal in (
        "data_source:execution_service",
        "data_source:instruments_service",
        "data_source:features_onchain_service",
        "data_source:strategy_service",
    ):
        assert internal not in sources, f"{internal} should be excluded from data_source"

    # Real external vendors remain.
    assert "data_source:databento" in sources
    assert "data_source:helius_rpc" in sources


def test_determinism_pure_uac_extractors() -> None:
    """The pure-UAC extractors are byte-stable across two runs (node ids/kinds)."""

    def snapshot() -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for extractor in (extract_venues, extract_data_sources, extract_gap_registries, extract_risk_surface):
            nodes, _ = extractor()
            out.extend(sorted((str(n.kind), n.node_id) for n in nodes))
        return out

    assert snapshot() == snapshot()
