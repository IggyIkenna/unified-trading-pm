"""Capability manifest reader helpers for the prospectus generator.

Reads capability-manifest.json and provides per-archetype queries:
  - venue categories + instrument types from ARCHETYPE_CAPABILITY_REGISTRY edges
  - execution algos
  - risk surface (KillSwitchReason x RiskGateLayer)
  - treasury split per venue category
  - fund-flow mermaid graph

All data is returned as plain dicts/lists (no Pydantic) to keep the generator
importable from any host without the full service venvs.

Plan: plans/active/capability_wizard_and_manifest_2026_06_11.md Phase 3
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Manifest loader
# ---------------------------------------------------------------------------


def load_manifest(uac_root: Path) -> dict:  # type: ignore[type-arg]
    """Load the capability manifest JSON from UAC openapi/."""
    path = uac_root / "openapi" / "capability-manifest.json"
    if not path.exists():
        logger.warning("Capability manifest not found at %s", path)
        return {}
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Per-archetype queries
# ---------------------------------------------------------------------------


def get_archetype_edges(manifest: dict, archetype_id: str) -> list[dict]:  # type: ignore[type-arg]
    """Return all edges whose source is the archetype node."""
    edges = manifest.get("edges", [])
    return [e for e in edges if e.get("source") == archetype_id]


def get_venue_category_edges(manifest: dict, archetype_id: str) -> list[dict]:  # type: ignore[type-arg]
    """Return edges: archetype -> venue_category or archetype -> instrument_type."""
    edges = get_archetype_edges(manifest, archetype_id)
    # Also edges where target is a venue or instrument_type node
    nodes_by_id: dict[str, dict] = {n["node_id"]: n for n in manifest.get("nodes", [])}  # type: ignore[type-arg]
    result = []
    for e in edges:
        target = nodes_by_id.get(e.get("target", ""), {})
        kind = target.get("kind", "")
        if kind in ("venue", "instrument_type"):
            result.append(e)
    return result


def get_capability_cells_for_archetype(manifest: dict, archetype_id: str) -> list[dict]:  # type: ignore[type-arg]
    """Return capability cell edges from the manifest for the archetype.

    These are edges from the ARCHETYPE_CAPABILITY_REGISTRY extraction:
    nodes with kind='archetype' -> nodes with kind='instrument_type'
    via edge relationship='has_capability'.
    """
    edges = manifest.get("edges", [])
    return [e for e in edges if e.get("source") == archetype_id and e.get("relationship") == "has_capability"]


def get_risk_edges(manifest: dict) -> list[dict]:  # type: ignore[type-arg]
    """Return all risk surface edges (kill switch / risk gate)."""
    edges = manifest.get("edges", [])
    nodes_by_id: dict[str, dict] = {n["node_id"]: n for n in manifest.get("nodes", [])}  # type: ignore[type-arg]
    result = []
    for e in edges:
        src_kind = nodes_by_id.get(e.get("source", ""), {}).get("kind", "")
        tgt_kind = nodes_by_id.get(e.get("target", ""), {}).get("kind", "")
        if src_kind in ("kill_switch", "risk_gate") or tgt_kind in ("kill_switch", "risk_gate"):
            result.append(e)
    return result


def get_treasury_split(manifest: dict, venue_categories: list[str]) -> list[dict]:  # type: ignore[type-arg]
    """Return treasury split policy edges relevant to the archetype's venue categories."""
    edges = manifest.get("edges", [])
    nodes_by_id: dict[str, dict] = {n["node_id"]: n for n in manifest.get("nodes", [])}  # type: ignore[type-arg]
    result = []
    for e in edges:
        tgt = nodes_by_id.get(e.get("target", ""), {})
        if tgt.get("kind") == "wallet":
            meta = tgt.get("metadata", {})
            ag = meta.get("asset_group", "")
            # Map venue category to asset_group
            mapping = {
                "CEFI": "cefi",
                "DEFI": "defi",
                "SPORTS": "sports",
                "TRADFI": "tradfi",
                "PREDICTION": "prediction",
            }
            for cat in venue_categories:
                if mapping.get(cat, "").lower() == ag.lower():
                    result.append({"edge": e, "wallet_node": tgt})
                    break
    return result


def get_execution_algos(manifest: dict) -> list[dict]:  # type: ignore[type-arg]
    """Return all execution algo nodes from the manifest."""
    nodes = manifest.get("nodes", [])
    return [n for n in nodes if n.get("kind") == "execution_algo"]


def get_leg_structure(manifest: dict, archetype_id: str) -> list[dict]:  # type: ignore[type-arg]
    """Return the per-leg restriction rows for an archetype (F22).

    Reads the leg nodes/edges emitted by ``extract_leg_structures``. Each row:
    ``{leg_id, role, required, instrument_types, venues, constraints}``. Empty
    list when the archetype has no leg structure (honest gap — the caller renders
    a gap line). Uses the canonical edge keys ``from_node_id``/``to_node_id``/
    ``relation`` (NOT ``source``/``target`` — those legacy keys are absent from
    ``to_canonical_dict`` output).
    """
    edges = manifest.get("edges", [])
    nodes_by_id: dict[str, dict] = {n["node_id"]: n for n in manifest.get("nodes", [])}  # type: ignore[type-arg]

    # leg nodes for this archetype (node_id prefix leg:<archetype>:)
    leg_prefix = f"leg:{archetype_id}:"
    leg_node_ids = sorted(nid for nid in nodes_by_id if nid.startswith(leg_prefix))

    rows: list[dict] = []  # type: ignore[type-arg]
    for leg_node_id in leg_node_ids:
        node = nodes_by_id[leg_node_id]
        meta = node.get("metadata", {})
        instrument_types: list[str] = []
        venues: list[str] = []
        constraints: list[dict[str, str]] = []
        for e in edges:
            if e.get("from_node_id") != leg_node_id:
                continue
            rel = str(e.get("relation", ""))
            tgt = str(e.get("to_node_id", ""))
            if rel == "trades_instrument" and tgt.startswith("instrument_type:"):
                instrument_types.append(tgt.split(":", 1)[1])
            elif rel == "supports" and tgt.startswith("venue:"):
                venues.append(tgt.split(":", 1)[1])
            elif rel.startswith("leg_constraint:"):
                constraints.append({"relation": rel, "reason": str(e.get("reason") or "")})
        rows.append(
            {
                "leg_id": leg_node_id.split(":", 2)[2],
                "role": str(meta.get("role", "")),
                "required": str(meta.get("required", "")),
                "execution_coupling": str(meta.get("execution_coupling", "")),
                "instrument_types": sorted(instrument_types),
                "venues": sorted(venues),
                "constraints": constraints,
            }
        )
    return rows


def get_manifest_provenance(manifest: dict) -> dict[str, str]:  # type: ignore[type-arg]
    """Return manifest_version + generated_from_commit."""
    return {
        "manifest_version": manifest.get("manifest_version", "unknown"),
        "generated_from_commit": manifest.get("generated_from_commit") or "unknown",
    }


# ---------------------------------------------------------------------------
# Fund-flow mermaid helpers
# ---------------------------------------------------------------------------

_VENUE_CATEGORY_TO_ASSET_GROUP: dict[str, str] = {
    "CEFI": "cefi",
    "DEFI": "defi",
    "SPORTS": "sports",
    "TRADFI": "tradfi",
    "PREDICTION": "prediction",
    "CROSS_CATEGORY": "defi",  # default to defi for cross-category
}


def _treasury_hot_split(asset_group: str) -> tuple[int, int]:
    """Return (treasury_pct, hot_pct) for an asset group.

    Source: TREASURY_SPLIT_POLICIES in UAC collateral_registry.py.
    DeFi 20/80, CeFi 0/100, Sports 0/100, rest unknown → 0/100.
    """
    mapping = {
        "defi": (20, 80),
        "cefi": (0, 100),
        "sports": (0, 100),
        "tradfi": (0, 100),
        "prediction": (0, 100),
    }
    return mapping.get(asset_group, (0, 100))


def _is_staked_basis_archetype(archetype_id: str) -> bool:
    """True if the archetype involves staking/LST legs."""
    staked_archetypes = {
        "CARRY_STAKED_BASIS",
        "CARRY_STAKED_BASIS_DATED",
        "CARRY_RECURSIVE_STAKED",
        "YIELD_STAKING_SIMPLE",
    }
    return archetype_id in staked_archetypes


def _has_defi_legs(venue_categories: list[str]) -> bool:
    return "DEFI" in venue_categories


def build_fund_flow_mermaid(
    archetype_id: str,
    venue_categories: list[str],
    capability_cells: list[dict],  # type: ignore[type-arg]
) -> str:
    """Build a mermaid flowchart for fund flow.

    Uses:
    - TREASURY_SPLIT_POLICIES for the treasury/hot split per venue category
    - capability cells to determine which legs exist
    - archetype family to infer staked/LST legs for staked-basis archetypes

    Machine-derived: treasury/hot split from collateral_registry.py SSOT.
    """
    lines: list[str] = ["```mermaid", "flowchart TD"]

    # Determine primary asset group
    primary_ag = "cefi"
    if "DEFI" in venue_categories:
        primary_ag = "defi"
    elif "SPORTS" in venue_categories:
        primary_ag = "sports"
    elif "TRADFI" in venue_categories:
        primary_ag = "tradfi"
    elif "PREDICTION" in venue_categories:
        primary_ag = "prediction"

    t_pct, h_pct = _treasury_hot_split(primary_ag)

    # Core wallet nodes
    lines.append('    CLIENT["Client Capital"]')
    lines.append(f'    TREASURY["Treasury Wallet\\n{t_pct}% AUM"]')
    lines.append(f'    HOT["Hot/Trading Wallet\\n{h_pct}% AUM"]')
    lines.append("    CLIENT --> TREASURY")
    lines.append("    CLIENT --> HOT")

    # Staked-basis specific leg structure
    is_staked = _is_staked_basis_archetype(archetype_id)

    if is_staked and "DEFI" in venue_categories:
        lines.append('    SPOT_DEX["Spot DEX\\n(UNISWAP_V3 / JUPITER)"]')
        lines.append('    STAKING["Staking Protocol\\n(LIDO / JITO / MARINADE)"]')
        lines.append('    LST["LST Asset\\n(stETH / JitoSOL / mSOL)"]')
        lines.append('    CEFI_VENUE["CeFi Perp Venue\\n(DERIBIT / DRIFT / BYBIT)"]')
        lines.append('    PERP_SHORT["Short Perp Position"]')
        lines.append("    HOT --> SPOT_DEX")
        lines.append("    SPOT_DEX --> STAKING")
        lines.append("    STAKING --> LST")
        lines.append("    LST --> CEFI_VENUE")
        lines.append("    CEFI_VENUE --> PERP_SHORT")
        lines.append("    PERP_SHORT -. funding yield .-> HOT")
        lines.append("    LST -. staking yield .-> HOT")
    elif archetype_id == "CARRY_RECURSIVE_BORROW_LENDING_ONLY":
        lines.append('    LENDING_PROTO["Lending Protocol\\n(AAVE / COMPOUND)"]')
        lines.append('    LST_COLLATERAL["LST Collateral"]')
        lines.append('    BORROW_LOOP["Borrow-Lend Loop"]')
        lines.append("    HOT --> LENDING_PROTO")
        lines.append("    HOT --> LST_COLLATERAL")
        lines.append("    LST_COLLATERAL --> LENDING_PROTO")
        lines.append("    LENDING_PROTO --> BORROW_LOOP")
        lines.append("    BORROW_LOOP -. net yield .-> HOT")
    elif "DEFI" in venue_categories and "LP" in str(capability_cells):
        lines.append('    DEX_POOL["DEX Pool\\n(UNISWAP_V3 / CURVE)"]')
        lines.append('    LP_TOKEN["LP Position"]')
        lines.append("    HOT --> DEX_POOL")
        lines.append("    DEX_POOL --> LP_TOKEN")
        lines.append("    LP_TOKEN -. fee yield .-> HOT")
    elif "CEFI" in venue_categories:
        lines.append('    CEFI["CeFi Exchange\\n(BINANCE / BYBIT / OKX)"]')
        lines.append('    POSITION["Trading Position"]')
        lines.append("    HOT --> CEFI")
        lines.append("    CEFI --> POSITION")
        lines.append("    POSITION -. PnL .-> HOT")
    elif "SPORTS" in venue_categories:
        lines.append('    EXCHANGE["Betting Exchange\\n(BETFAIR / SPORTRADAR)"]')
        lines.append('    BET["Back/Lay Position"]')
        lines.append("    HOT --> EXCHANGE")
        lines.append("    EXCHANGE --> BET")
        lines.append("    BET -. settlement .-> HOT")
    elif "PREDICTION" in venue_categories:
        lines.append('    PRED_MKT["Prediction Market\\n(POLYMARKET / KALSHI)"]')
        lines.append('    OUTCOME_SHARE["Outcome Share"]')
        lines.append("    HOT --> PRED_MKT")
        lines.append("    PRED_MKT --> OUTCOME_SHARE")
        lines.append("    OUTCOME_SHARE -. settlement .-> HOT")
    elif "TRADFI" in venue_categories:
        lines.append('    BROKER["TradFi Broker\\n(IBKR / INTERACTIVE_BROKERS)"]')
        lines.append('    POSITION["Trading Position"]')
        lines.append("    HOT --> BROKER")
        lines.append("    BROKER --> POSITION")
        lines.append("    POSITION -. PnL .-> HOT")
    else:
        lines.append('    VENUE["Trading Venue"]')
        lines.append("    HOT --> VENUE")

    lines.append("```")
    return "\n".join(lines)
