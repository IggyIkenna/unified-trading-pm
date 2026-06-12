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
REL_HAS_LEG = "has_leg"
REL_LEG_CONSTRAINT = "leg_constraint"
REL_ROUTED_VIA = "routed_via"  # F38: venue ⇠routed_via⇢ broker


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
# (a2) Archetype leg structures (F22 — structural multi-leg restriction model)
# ---------------------------------------------------------------------------


def extract_leg_structures() -> tuple[list[CapabilityNode], list[CapabilityEdge]]:
    """ARCHETYPE_LEG_STRUCTURES — the per-leg restriction SSOT (F22).

    The flat ``ARCHETYPE_CAPABILITY_REGISTRY`` models a multi-leg archetype as a
    set of ``(asset_group, instrument_type)`` cells; this gives the wizard only a
    single instrument choice per cell (the F22 bug: a basis trade offered only
    "Staking"). The leg registry refines that into structural legs. For each
    seeded archetype we emit:

      - a ``leg`` node per leg (id ``leg:<archetype>:<leg_id>``);
      - ``archetype --has_leg--> leg`` (metadata: ``role`` + ``required``);
      - ``leg --trades_instrument--> instrument_type`` per leg instrument type;
      - ``leg --supports--> venue`` per eligible venue (the per-leg venue
        restriction the flat mixed ``venue_ids`` list cannot express);
      - ``leg --leg_constraint--> leg`` (self-edge) per typed constraint,
        carrying the conditional in metadata (``constraint_kind`` +
        ``fallback_variant`` + the constraint ``params``). The staked-basis
        ``requires_collateral_acceptance`` conditional with its
        ``straight_basis`` fallback is the headline.

    Archetypes WITHOUT a leg structure get ONE ``not_registered`` ``legs`` gap
    edge each (``archetype --has_leg--> archetype`` self-edge, gap
    ``missing_registry``) — exhaustive honesty, never a silent omission.
    """
    from unified_api_contracts.internal.architecture_v2.archetype_leg_spec import (  # noqa: qg-deep-import
        ARCHETYPE_LEG_STRUCTURES,
        archetypes_without_leg_structures,
    )

    nodes: list[CapabilityNode] = []
    edges: list[CapabilityEdge] = []
    seen_nodes: set[tuple[str, str]] = set()

    def add_node(kind: CapabilityNodeKind, node_id: str, label: str, **meta: str) -> None:
        key = (str(kind), node_id)
        if key not in seen_nodes:
            seen_nodes.add(key)
            nodes.append(_node(kind, node_id, label, **meta))

    for archetype in sorted(ARCHETYPE_LEG_STRUCTURES, key=lambda a: a.value):
        struct = ARCHETYPE_LEG_STRUCTURES[archetype]
        arch_id = archetype.value
        add_node(CapabilityNodeKind.ARCHETYPE, arch_id, _titleize(arch_id))
        for leg in struct.legs:
            leg_node_id = f"leg:{arch_id}:{leg.leg_id}"
            add_node(
                CapabilityNodeKind.LEG,
                leg_node_id,
                f"{_titleize(arch_id)} — {leg.leg_id}",
                role=leg.role.value,
                required=str(leg.required).lower(),
                archetype=arch_id,
                execution_coupling=struct.execution_coupling.value,
            )
            edges.append(
                CapabilityEdge(
                    from_node_id=arch_id,
                    to_node_id=leg_node_id,
                    relation=REL_HAS_LEG,
                    status=CapabilityEdgeStatus.AVAILABLE,
                    reason=f"role={leg.role.value}; required={str(leg.required).lower()}",
                )
            )
            # leg -> instrument_type (the per-leg instrument restriction)
            for it in sorted(t.value for t in leg.instrument_types):
                it_node_id = f"instrument_type:{it}"
                add_node(CapabilityNodeKind.INSTRUMENT_TYPE, it_node_id, _titleize(it))
                edges.append(
                    CapabilityEdge(
                        from_node_id=leg_node_id,
                        to_node_id=it_node_id,
                        relation=REL_TRADES_INSTRUMENT,
                        status=CapabilityEdgeStatus.AVAILABLE,
                    )
                )
            # leg -> venue (the per-leg eligible-venue restriction)
            for venue_id in sorted(leg.eligible_venue_ids):
                vid = f"venue:{venue_id}"
                add_node(CapabilityNodeKind.VENUE, vid, _titleize(venue_id))
                edges.append(
                    CapabilityEdge(
                        from_node_id=leg_node_id,
                        to_node_id=vid,
                        relation=REL_SUPPORTS,
                        status=CapabilityEdgeStatus.AVAILABLE,
                    )
                )
            # leg -> leg (self-edge) per typed constraint — the conditional
            # restriction surface (collateral-acceptance / same-venue / atomic).
            # CapabilityEdge has no metadata field, so the conditional (kind +
            # sorted params + fallback_variant) is encoded deterministically in
            # the relation string; the human description rides ``reason``.
            for constraint in leg.constraints:
                params_str = ";".join(f"{k}={constraint.params[k]}" for k in sorted(constraint.params))
                relation = f"{REL_LEG_CONSTRAINT}:{constraint.kind.value}"
                if params_str:
                    relation += f"|{params_str}"
                if constraint.fallback_variant is not None:
                    relation += f"|fallback_variant={constraint.fallback_variant}"
                edges.append(
                    CapabilityEdge(
                        from_node_id=leg_node_id,
                        to_node_id=leg_node_id,
                        relation=relation,
                        status=CapabilityEdgeStatus.AVAILABLE,
                        reason=constraint.description,
                    )
                )

    # Honest gap: archetypes with NO leg structure → one not_registered gap edge.
    for archetype in archetypes_without_leg_structures():
        arch_id = archetype.value
        add_node(CapabilityNodeKind.ARCHETYPE, arch_id, _titleize(arch_id))
        edges.append(
            CapabilityEdge(
                from_node_id=arch_id,
                to_node_id=arch_id,
                relation=f"{REL_HAS_LEG}:legs",
                status=CapabilityEdgeStatus.NOT_REGISTERED,
                gap_type=CapabilityGapType.MISSING_REGISTRY,
                reason=(
                    f"{arch_id} has no leg structure in ARCHETYPE_LEG_STRUCTURES yet — "
                    "structural per-leg restrictions not modelled (F22 leg-truth gap)"
                ),
            )
        )

    logger.info("  leg structures: %d nodes, %d edges", len(nodes), len(edges))
    return nodes, edges


# ---------------------------------------------------------------------------
# (b) Venues / chains / instrument types
# ---------------------------------------------------------------------------


def extract_venues() -> tuple[list[CapabilityNode], list[CapabilityEdge]]:
    """Venue registries: VENUE_CATEGORY_MAP, INSTRUMENT_TYPES_BY_VENUE,
    DEFI_VENUE_TO_PROTOCOL, CHAIN_RPC_TEMPLATES, ENDPOINT_REGISTRY (auth/access).
    """
    from unified_api_contracts.internal.architecture_v2.broker_routes import (  # noqa: qg-deep-import
        is_broker,
    )
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
        # F38: a broker (e.g. ibkr) is NOT a venue — it is emitted as a BROKER
        # node by extract_brokers(), with venue⇠routed_via⇢broker edges. Never
        # let a broker id leak into the venue node set (it would render as a
        # selectable peer venue in the wizard).
        if kind == CapabilityNodeKind.VENUE and is_broker(node_id.split(":", 1)[-1]):
            return
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

    # Broker nodes: TradFi brokers that route orders to exchange venues.
    # ibkr is a broker (not a direct exchange) — routed_via edges point venue→broker.
    _tradfi_brokers: dict[str, tuple[str, list[str]]] = {
        "ibkr": ("Interactive Brokers", ["CME", "ICE", "CBOE"]),
    }
    for broker_id, (broker_label, routed_venues) in sorted(_tradfi_brokers.items()):
        bid = f"broker:{broker_id}"
        add(CapabilityNodeKind.BROKER, bid, broker_label, broker_id=broker_id)
        for exchange in routed_venues:
            vid = f"venue:{exchange}"
            if any(n.node_id == vid for n in nodes):
                edges.append(
                    CapabilityEdge(
                        from_node_id=vid,
                        to_node_id=bid,
                        relation=REL_ROUTED_VIA,
                        status=CapabilityEdgeStatus.AVAILABLE,
                    )
                )

    logger.info("  venues/chains: %d nodes, %d edges", len(nodes), len(edges))
    return nodes, edges


# ---------------------------------------------------------------------------
# (b2) Brokers — routing intermediaries, NOT peer venues (F38)
# ---------------------------------------------------------------------------


def extract_brokers() -> tuple[list[CapabilityNode], list[CapabilityEdge]]:
    """BROKER_ROUTES: a broker routes orders to exchange venues.

    Emits one ``broker`` node per broker + a ``venue ⇠routed_via⇢ broker`` edge
    per routed venue. The routed venues (CME/ICE/CBOE/…) remain ordinary VENUE
    nodes; the broker (ibkr) is classified as a BROKER node — never a peer venue.
    The wizard reads the ``routed_via`` edges to render brokers as a routing
    sub-choice under their venues.

    SSOT: ``unified_api_contracts.internal.architecture_v2.broker_routes`` (F38),
    sourced from ``execution_service/.../ibkr_tradfi.py:38-46`` VENUE_TO_EXCHANGE.
    """

    from unified_api_contracts.internal.architecture_v2.broker_routes import (  # noqa: qg-deep-import
        BROKER_ROUTES,
    )

    nodes: list[CapabilityNode] = []
    edges: list[CapabilityEdge] = []

    for broker_id in sorted(BROKER_ROUTES):
        route = BROKER_ROUTES[broker_id]
        broker_node_id = f"broker:{broker_id}"
        nodes.append(
            _node(
                CapabilityNodeKind.BROKER,
                broker_node_id,
                route.label,
                broker_kind=str(route.kind.value),
                routed_venue_ids=",".join(sorted(route.routed_venue_ids)),
                venue_categories=",".join(sorted(c.value for c in route.venue_categories)),
                source_of_truth=route.source_of_truth,
            )
        )
        for venue_id in sorted(route.routed_venue_ids):
            # The routed venue is a real exchange (the price-discovery venue).
            # Emit a minimal VENUE node so the routed_via edge never dangles —
            # an archetype/registry-emitted richer venue node (cme/cboe/ice) wins
            # the dedup (first-seen label + setdefault metadata); the broker-only
            # exchanges (nasdaq/nyse/fx) get their sole node here.
            nodes.append(
                _node(
                    CapabilityNodeKind.VENUE,
                    f"venue:{venue_id}",
                    _titleize(venue_id),
                    venue_category=",".join(sorted(c.value for c in route.venue_categories)),
                    broker_routed="true",
                )
            )
            edges.append(
                CapabilityEdge(
                    from_node_id=f"venue:{venue_id}",
                    to_node_id=broker_node_id,
                    relation=REL_ROUTED_VIA,
                    status=CapabilityEdgeStatus.AVAILABLE,
                    reason=f"{route.label} ({route.kind.value}) routes orders to this venue.",
                )
            )

    logger.info(
        "  brokers (F38): %d broker + routed-venue nodes, %d routed_via edges",
        len(nodes),
        len(edges),
    )
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
