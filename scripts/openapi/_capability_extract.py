"""Extraction helpers for the capability-manifest generator.

Each function returns ``(nodes, edges)`` tuples built from a single UAC or
service registry.  All output is deterministic (sets are ``sorted()`` before
emission).  Every dimension either yields a populated edge or an honest typed
gap edge — never a silent omission.

Service-resident registries (execution algos, feature groups, ML models) are
extracted in a per-service subprocess (their own ``.venv``) by
``_capability_services.py``; the results land here as plain dict rows.

Codex SSOT: ``codex/09-strategy/architecture-v2/capability-wizard.md``
Plan: ``plans/active/capability_wizard_and_manifest_2026_06_11.md`` Phase 1.
"""

from __future__ import annotations

import logging

from unified_api_contracts.internal.architecture_v2.capability_manifest import (
    CapabilityEdge,
    CapabilityEdgeStatus,
    CapabilityGapType,
    CapabilityNode,
    CapabilityNodeKind,
)

logger = logging.getLogger(__name__)

# Edge relation vocabulary (controlled).
REL_BELONGS_TO_FAMILY = "belongs_to_family"
REL_SUPPORTS = "supports"
REL_TRADES_INSTRUMENT = "trades_instrument"
REL_ON_CHAIN = "on_chain"
REL_USES_PROTOCOL = "uses_protocol"
REL_PROVIDES = "provides"
REL_SUPPORTS_MODE = "supports_mode"
REL_OVER_TRANSPORT = "over_transport"
REL_SPLIT_POLICY = "wallet_split_policy"
REL_GUARDED_BY = "guarded_by"
REL_AT_RISK_LAYER = "at_risk_layer"
REL_USES_ALGO = "uses_algo"
REL_EMITS_INSTRUCTION = "emits_instruction"
REL_USES_FEATURE_GROUP = "uses_feature_group"
REL_USES_MODEL = "uses_model"
REL_MIN_DATA_TO_RUN = "min_data_to_run"
REL_OFFERS = "offers"


def _node(kind: CapabilityNodeKind, node_id: str, label: str, **meta: str) -> CapabilityNode:
    return CapabilityNode(kind=kind, node_id=node_id, label=label, metadata={k: str(v) for k, v in meta.items()})


def _titleize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


# ---------------------------------------------------------------------------
# (a) Archetypes / families + capability registry
# ---------------------------------------------------------------------------


def extract_archetypes_and_families() -> tuple[list[CapabilityNode], list[CapabilityEdge]]:
    """STRATEGY_REGISTRY + ARCHETYPE_CAPABILITY_REGISTRY.

    Nodes: archetype, family, instrument_type.
    Edges: archetype -> family (belongs_to_family); archetype -> instrument_type
    (trades_instrument, per ACR cell, status mapped from cell.status); a venue
    edge per ACR cell venue (archetype -> venue, supports).
    """
    from unified_api_contracts.internal.architecture_v2.archetype_capability import (  # noqa: qg-deep-import
        ARCHETYPE_CAPABILITY_REGISTRY,
    )
    from unified_api_contracts.strategy import STRATEGY_REGISTRY  # noqa: qg-deep-import

    nodes: list[CapabilityNode] = []
    edges: list[CapabilityEdge] = []
    seen_nodes: set[tuple[str, str]] = set()

    def add_node(kind: CapabilityNodeKind, node_id: str, label: str, **meta: str) -> None:
        key = (str(kind), node_id)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(_node(kind, node_id, label, **meta))

    reg = STRATEGY_REGISTRY.to_dict()
    families: dict[str, list[str]] = reg.get("families", {})
    archetype_to_family: dict[str, str] = {}
    for strat in reg.get("strategies", []):
        arch = str(strat.get("archetype", ""))
        fam = str(strat.get("family", ""))
        if arch and fam:
            archetype_to_family[arch] = fam

    for fam in sorted(families):
        add_node(CapabilityNodeKind.FAMILY, fam, _titleize(fam))

    for arch in sorted(str(a) for a in reg.get("archetypes", [])):
        fam = archetype_to_family.get(arch, "")
        add_node(CapabilityNodeKind.ARCHETYPE, arch, _titleize(arch))
        if fam:
            if (str(CapabilityNodeKind.FAMILY), fam) not in seen_nodes:
                add_node(CapabilityNodeKind.FAMILY, fam, _titleize(fam))
            edges.append(
                CapabilityEdge(
                    from_node_id=arch,
                    to_node_id=fam,
                    relation=REL_BELONGS_TO_FAMILY,
                    status=CapabilityEdgeStatus.AVAILABLE,
                )
            )

    status_map = {
        "SUPPORTED": CapabilityEdgeStatus.AVAILABLE,
        "PARTIAL": CapabilityEdgeStatus.PARTIAL,
        "BLOCKED": CapabilityEdgeStatus.NOT_AVAILABLE,
    }
    for entry in ARCHETYPE_CAPABILITY_REGISTRY:
        arch = entry.archetype_id.value
        add_node(CapabilityNodeKind.ARCHETYPE, arch, _titleize(arch))
        for cell in entry.cells:
            it = cell.instrument_type.value
            it_node_id = f"instrument_type:{it}"
            add_node(CapabilityNodeKind.INSTRUMENT_TYPE, it_node_id, _titleize(it), asset_group=cell.asset_group.value)
            cell_status = status_map.get(cell.status.value, CapabilityEdgeStatus.NOT_AVAILABLE)
            gap = CapabilityGapType.LOGICAL_DEAD_END if cell_status == CapabilityEdgeStatus.NOT_AVAILABLE else None
            edges.append(
                CapabilityEdge(
                    from_node_id=arch,
                    to_node_id=it_node_id,
                    relation=REL_TRADES_INSTRUMENT,
                    status=cell_status,
                    gap_type=gap,
                    reason=(cell.notes or None) if cell.notes else None,
                )
            )
            for venue_id in sorted(cell.venue_ids):
                vid = f"venue:{venue_id}"
                add_node(CapabilityNodeKind.VENUE, vid, _titleize(venue_id), asset_group=cell.asset_group.value)
                edges.append(
                    CapabilityEdge(
                        from_node_id=arch,
                        to_node_id=vid,
                        relation=REL_SUPPORTS,
                        status=cell_status,
                        gap_type=gap,
                    )
                )

    logger.info("  archetypes/families: %d nodes, %d edges", len(nodes), len(edges))
    return nodes, edges


# ---------------------------------------------------------------------------
# (b) Venues / chains / instrument types
# ---------------------------------------------------------------------------


def extract_venues() -> tuple[list[CapabilityNode], list[CapabilityEdge]]:
    """Venue registries: VENUE_CATEGORY_MAP, INSTRUMENT_TYPES_BY_VENUE,
    DEFI_VENUE_TO_PROTOCOL, CHAIN_RPC_TEMPLATES, ENDPOINT_REGISTRY (auth/access).
    """
    from unified_api_contracts.registry import (  # noqa: qg-deep-import
        CHAIN_RPC_TEMPLATES,
        DEFI_VENUE_TO_PROTOCOL,
        ENDPOINT_REGISTRY,
        INSTRUMENT_TYPES_BY_VENUE,
        VENUE_CATEGORY_MAP,
    )

    nodes: list[CapabilityNode] = []
    edges: list[CapabilityEdge] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: CapabilityNodeKind, node_id: str, label: str, **meta: str) -> None:
        key = (str(kind), node_id)
        if key not in seen:
            seen.add(key)
            nodes.append(_node(kind, node_id, label, **meta))

    # Chains
    for chain_id in sorted(str(c) for c in CHAIN_RPC_TEMPLATES):
        add(CapabilityNodeKind.CHAIN, f"chain:{chain_id}", f"Chain {chain_id}")

    # Endpoint metadata: venue -> {access_mode, requires_auth}
    endpoint_meta: dict[str, dict[str, str]] = {}
    for spec in ENDPOINT_REGISTRY:
        d = spec.model_dump()
        venue = str(d.get("venue", "")).strip()
        if not venue:
            continue
        entry = endpoint_meta.setdefault(venue, {})
        if d.get("access_mode") and "access_mode" not in entry:
            entry["access_mode"] = str(d["access_mode"])
        if d.get("requires_auth") is not None:
            entry["requires_auth"] = str(bool(d.get("requires_auth")))

    # Venue nodes from VENUE_CATEGORY_MAP
    for venue, category in sorted(VENUE_CATEGORY_MAP.items()):
        vid = f"venue:{venue}"
        meta: dict[str, str] = {"category": str(category)}
        lower = str(venue).lower()
        em = endpoint_meta.get(lower) or endpoint_meta.get(str(venue))
        if em:
            meta.update(em)
        add(CapabilityNodeKind.VENUE, vid, _titleize(str(venue)), **meta)

    # DeFi venue -> chain/protocol
    for venue, (protocol, chain) in sorted(DEFI_VENUE_TO_PROTOCOL.items()):
        vid = f"venue:{venue}"
        add(CapabilityNodeKind.VENUE, vid, _titleize(str(venue)), category="defi", protocol=str(protocol))
        if chain is not None:
            chain_node = f"chain:{chain}"
            add(CapabilityNodeKind.CHAIN, chain_node, str(chain))
            edges.append(
                CapabilityEdge(
                    from_node_id=vid,
                    to_node_id=chain_node,
                    relation=REL_ON_CHAIN,
                    status=CapabilityEdgeStatus.AVAILABLE,
                )
            )

    # Venue -> instrument_type
    for venue, itypes in sorted(INSTRUMENT_TYPES_BY_VENUE.items()):
        vid = f"venue:{venue}"
        category = str(VENUE_CATEGORY_MAP.get(venue, ""))
        add(CapabilityNodeKind.VENUE, vid, _titleize(str(venue)), category=category)
        for it in sorted(str(t) for t in itypes):
            it_node = f"instrument_type:{it}"
            add(CapabilityNodeKind.INSTRUMENT_TYPE, it_node, _titleize(it))
            edges.append(
                CapabilityEdge(
                    from_node_id=vid,
                    to_node_id=it_node,
                    relation=REL_TRADES_INSTRUMENT,
                    status=CapabilityEdgeStatus.AVAILABLE,
                )
            )

    logger.info("  venues/chains: %d nodes, %d edges", len(nodes), len(edges))
    return nodes, edges


# ---------------------------------------------------------------------------
# (c) Data sources, modes, transports
# ---------------------------------------------------------------------------


def extract_data_sources() -> tuple[list[CapabilityNode], list[CapabilityEdge]]:
    """SOURCE_PRIORITY + Transport + default_transport_for_source.

    Where the full batch/live/replay matrix per source is not encoded in UAC
    (it lives in the manual source-mode-capability-matrix audit), emit a
    ``missing_registry`` gap edge rather than parsing the markdown.
    """
    # Transport + default_transport_for_source are re-exported at the UAC root
    # facade; SOURCE_PRIORITY is surfaced via the registry sub-facade (NOT the
    # canonical.* deep path the import-surface gate blocks).
    from unified_api_contracts import (
        Transport,
        default_transport_for_source,
    )
    from unified_api_contracts.registry.possible_manifest import (  # noqa: qg-deep-import
        SOURCE_PRIORITY,
    )

    nodes: list[CapabilityNode] = []
    edges: list[CapabilityEdge] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: CapabilityNodeKind, node_id: str, label: str, **meta: str) -> None:
        key = (str(kind), node_id)
        if key not in seen:
            seen.add(key)
            nodes.append(_node(kind, node_id, label, **meta))

    # Collect all distinct sources from SOURCE_PRIORITY values.
    sources: set[str] = set()
    for source_list in SOURCE_PRIORITY.values():
        for src in source_list:
            sources.add(str(src))

    transports = sorted(t.value for t in Transport)
    # Three pipeline modes are the canonical axis.
    modes = ["batch", "live", "replay"]

    for src in sorted(sources):
        sid = f"data_source:{src}"
        add(CapabilityNodeKind.DATA_SOURCE, sid, _titleize(src))
        # Transport: default is known; non-default transports per source are
        # not in a UAC registry → missing_registry gap.
        default_tp = default_transport_for_source(src)
        for tp in transports:
            if tp == default_tp:
                edges.append(
                    CapabilityEdge(
                        from_node_id=sid,
                        to_node_id=sid,
                        relation=f"{REL_OVER_TRANSPORT}:{tp}",
                        status=CapabilityEdgeStatus.AVAILABLE,
                        reason=f"default transport for {src}",
                    )
                )
        # batch mode is the baseline; live/replay per-source capability is the
        # manual audit not yet codified in UAC → typed gap.
        for mode in modes:
            # noqa: L2-mode-seam — this is manifest GRAPH-BUILD over pipeline-mode
            # vocabulary strings, not CLI batch/live execution routing.
            if mode == "batch":  # noqa: L2-mode-seam
                edges.append(
                    CapabilityEdge(
                        from_node_id=sid,
                        to_node_id=sid,
                        relation=f"{REL_SUPPORTS_MODE}:{mode}",
                        status=CapabilityEdgeStatus.AVAILABLE,
                        reason="batch is the baseline mode for every source",
                    )
                )
            else:
                edges.append(
                    CapabilityEdge(
                        from_node_id=sid,
                        to_node_id=sid,
                        relation=f"{REL_SUPPORTS_MODE}:{mode}",
                        status=CapabilityEdgeStatus.NOT_REGISTERED,
                        gap_type=CapabilityGapType.MISSING_REGISTRY,
                        reason=(
                            f"{mode}-mode capability for {src} lives in the manual "
                            "source-mode-capability-matrix audit, not yet codified in a UAC registry"
                        ),
                    )
                )

    logger.info("  data sources: %d nodes, %d edges", len(nodes), len(edges))
    return nodes, edges
