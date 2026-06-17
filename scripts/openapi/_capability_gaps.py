"""Gap-registry + risk-surface + service-resident extraction helpers.

Covers plan items (d) gap registries, (e) risk surface, (f) service-resident
registries (execution algos / feature groups / ML models) via per-service
subprocess imports.

Every honest-empty registry emits explicit ``not_registered`` edges so the
manifest never silently omits a dimension; the seeded TREASURY_SPLIT_POLICIES
become real wallet-policy nodes/edges.

Codex SSOT: ``codex/09-strategy/architecture-v2/capability-wizard.md``
Plan: ``plans/active/capability_wizard_and_manifest_2026_06_11.md`` Phase 1.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import cast

from unified_api_contracts.internal.architecture_v2.capability_manifest import (
    CapabilityEdge,
    CapabilityEdgeStatus,
    CapabilityGapType,
    CapabilityNode,
    CapabilityNodeKind,
    ParamSchemaSpec,
)

logger = logging.getLogger(__name__)

REL_SPLIT_POLICY = "wallet_split_policy"
REL_GUARDED_BY = "guarded_by"
REL_AT_RISK_LAYER = "at_risk_layer"
REL_USES_ALGO = "uses_algo"
REL_USES_FEATURE_GROUP = "uses_feature_group"
REL_USES_MODEL = "uses_model"
REL_MIN_DATA_TO_RUN = "min_data_to_run"
REL_NOT_REGISTERED = "registry_gap"
REL_ACCEPTS_COLLATERAL = "accepts_collateral"
REL_OFFERS_SHARE_CLASS = "offers_share_class"
REL_SIGNS_FOR = "signs_for"


def _node(kind: CapabilityNodeKind, node_id: str, label: str, **meta: str) -> CapabilityNode:
    return CapabilityNode(kind=kind, node_id=node_id, label=label, metadata={k: str(v) for k, v in meta.items()})


def _as_str_list(value: object) -> list[str]:
    """Coerce a probe-dict value (typed ``object``) into a sorted ``list[str]``.

    The service probe returns ``dict[str, object]``; a list value (model types,
    target types, variant fields) is narrowed + stringified here so callers get
    a concretely-typed ``list[str]`` with no ``Any`` leaking out.
    """
    if not isinstance(value, list):
        return []
    items: list[str] = [str(item) for item in value]
    return sorted(items)


def _titleize(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").title()


# ---------------------------------------------------------------------------
# (d) Gap registries — honest-empty registries emit explicit not_registered
# ---------------------------------------------------------------------------


def extract_gap_registries() -> tuple[list[CapabilityNode], list[CapabilityEdge]]:
    """Six gap registries + the seeded treasury split policies.

    Honest-empty registries (collateral, fees, sim assumptions, fund
    structures, order semantics, trading agent) each emit one explicit
    ``not_registered`` edge so the dimension is present.  TREASURY_SPLIT_POLICIES
    (seeded) become real wallet-policy nodes/edges; OFFERED_FUND_STRUCTURES /
    VENUE_ORDER_SEMANTICS etc. are populated where they contain entries.
    """
    from unified_api_contracts.internal.architecture_v2.collateral_registry import (  # noqa: qg-deep-import
        BROKER_REGISTRY,
        COLLATERAL_REGISTRY,
        TREASURY_SPLIT_POLICIES,
    )
    from unified_api_contracts.internal.architecture_v2.custody_surfaces import (  # noqa: qg-deep-import
        OFFERED_SIGNING_SURFACES,
    )
    from unified_api_contracts.internal.architecture_v2.fees_registry import FEES_REGISTRY  # noqa: qg-deep-import
    from unified_api_contracts.internal.architecture_v2.fund_structures import (  # noqa: qg-deep-import
        OFFERED_FUND_STRUCTURES,
    )
    from unified_api_contracts.internal.architecture_v2.order_semantics import (  # noqa: qg-deep-import
        VENUE_ORDER_SEMANTICS,
    )
    from unified_api_contracts.internal.architecture_v2.simulation_assumptions import (  # noqa: qg-deep-import
        SIM_ASSUMPTIONS_REGISTRY,
    )
    from unified_api_contracts.internal.architecture_v2.trading_agent_capability import (  # noqa: qg-deep-import
        TRADING_AGENT_CAPABILITIES,
    )

    nodes: list[CapabilityNode] = []
    edges: list[CapabilityEdge] = []
    seen: set[tuple[str, str]] = set()

    def add(kind: CapabilityNodeKind, node_id: str, label: str, **meta: str) -> None:
        key = (str(kind), node_id)
        if key not in seen:
            seen.add(key)
            nodes.append(_node(kind, node_id, label, **meta))

    # Seeded: treasury split policies -> wallet nodes/edges.
    for policy in sorted(TREASURY_SPLIT_POLICIES, key=lambda p: p.asset_group):
        ag = policy.asset_group
        treasury_id = f"wallet:{ag}:treasury"
        hot_id = f"wallet:{ag}:hot"
        add(
            CapabilityNodeKind.WALLET,
            treasury_id,
            f"{_titleize(ag)} Treasury",
            asset_group=ag,
            tier="treasury",
            treasury_pct=str(policy.treasury_pct),
        )
        add(
            CapabilityNodeKind.WALLET,
            hot_id,
            f"{_titleize(ag)} Hot",
            asset_group=ag,
            tier="hot",
            hot_pct=str(policy.hot_pct),
        )
        edges.append(
            CapabilityEdge(
                from_node_id=treasury_id,
                to_node_id=hot_id,
                relation=REL_SPLIT_POLICY,
                status=CapabilityEdgeStatus.AVAILABLE,
                reason=(
                    f"{ag}: {policy.treasury_pct}% treasury / {policy.hot_pct}% hot "
                    "(wallet-hierarchy-and-capital-flow.md)"
                ),
            )
        )

    # Collateral backfill (2026-06-12): when COLLATERAL_REGISTRY is populated,
    # emit per-venue collateral nodes + per-asset accepts-collateral edges so the
    # manifest/wizard carries the actual haircut/LTV metadata (not just a
    # count). Each edge's metadata holds the sourced numerics + citation.
    for policy in sorted(COLLATERAL_REGISTRY, key=lambda p: p.venue_id):
        coll_node = f"collateral:{policy.venue_id}"
        kind_meta = policy.venue_kind.value if policy.venue_kind is not None else ""
        add(
            CapabilityNodeKind.COLLATERAL_POLICY,
            coll_node,
            f"Collateral: {_titleize(policy.venue_id)}",
            venue_id=policy.venue_id,
            venue_kind=kind_meta,
            maintenance_margin=("" if policy.maintenance_margin is None else str(policy.maintenance_margin)),
            max_ltv=("" if policy.max_ltv is None else str(policy.max_ltv)),
            source_of_truth=policy.source_of_truth,
        )
        for ah in sorted(policy.accepted_collateral, key=lambda a: a.asset):
            asset_node = f"collateral_asset:{ah.asset}"
            add(CapabilityNodeKind.INSTRUMENT_TYPE, asset_node, f"Collateral Asset: {ah.asset}", asset=ah.asset)
            status = CapabilityEdgeStatus.AVAILABLE if ah.accepted else CapabilityEdgeStatus.NOT_AVAILABLE
            meta_bits = [f"haircut={ah.haircut_pct}%"]
            if ah.max_ltv is not None:
                meta_bits.append(f"max_ltv={ah.max_ltv}")
            if ah.liquidation_threshold is not None:
                meta_bits.append(f"liq_threshold={ah.liquidation_threshold}")
            edges.append(
                CapabilityEdge(
                    from_node_id=coll_node,
                    to_node_id=asset_node,
                    relation=REL_ACCEPTS_COLLATERAL,
                    status=status,
                    reason=(
                        f"{policy.venue_id} {'accepts' if ah.accepted else 'rejects'} {ah.asset} "
                        f"({', '.join(meta_bits)}) — {ah.source_note}"
                    ),
                )
            )

    # Honest-empty / partial registries: one explicit edge per dimension.
    gap_specs: list[tuple[str, int, str, str]] = [
        ("collateral", len(COLLATERAL_REGISTRY), "Collateral policies", "per-venue haircut/LTV backfill"),
        ("broker", len(BROKER_REGISTRY), "TradFi brokers", "broker capability code-scan backfill"),
        ("fees", len(FEES_REGISTRY), "Fee schedules", "per-venue fee tier backfill"),
        (
            "sim_assumptions",
            len(SIM_ASSUMPTIONS_REGISTRY),
            "Simulation assumptions",
            "needs_code_scan of backtest runner (finding F11)",
        ),
        ("fund_structure", len(OFFERED_FUND_STRUCTURES), "Fund structures", "offered fund-structure backfill"),
        (
            "order_semantics",
            len(VENUE_ORDER_SEMANTICS),
            "Venue order semantics",
            "per-adapter order-semantics honor matrix code-scan",
        ),
        (
            "trading_agent",
            len(TRADING_AGENT_CAPABILITIES),
            "Trading-agent capabilities",
            "LLM/agent capability declaration backfill",
        ),
    ]
    for dim, count, label, reason in gap_specs:
        node_id = f"gap_registry:{dim}"
        add(CapabilityNodeKind.GAP_REGISTRY, node_id, label, registry=dim, entry_count=str(count))
        if count == 0:
            gap = (
                CapabilityGapType.NEEDS_CODE_SCAN
                if "needs_code_scan" in reason or "code-scan" in reason
                else CapabilityGapType.MISSING_REGISTRY
            )
            edges.append(
                CapabilityEdge(
                    from_node_id=node_id,
                    to_node_id=node_id,
                    relation=REL_NOT_REGISTERED,
                    status=CapabilityEdgeStatus.NOT_REGISTERED,
                    gap_type=gap,
                    reason=f"{label} registry is honest-empty — {reason}",
                )
            )
        else:
            edges.append(
                CapabilityEdge(
                    from_node_id=node_id,
                    to_node_id=node_id,
                    relation=REL_NOT_REGISTERED,
                    status=CapabilityEdgeStatus.AVAILABLE,
                    reason=f"{label}: {count} entries registered",
                )
            )

    # F50: OFFERED_FUND_STRUCTURES -> one FUND_STRUCTURE node per offering, with
    # share-class / cadence metadata + per-share-class offers_share_class edges.
    # (Previously the registry produced only a single mis-kinded gap_registry
    # node; the manifest had 0 fund_structure-kind nodes despite POOLED + SMA
    # being populated.)
    for offering in sorted(OFFERED_FUND_STRUCTURES, key=lambda o: o.kind.value):
        fs_id = f"fund_structure:{offering.kind.value}"
        add(
            CapabilityNodeKind.FUND_STRUCTURE,
            fs_id,
            f"Fund Structure: {_titleize(offering.kind.value)}",
            structure_kind=offering.kind.value,
            share_classes=",".join(sorted(sc.value for sc in offering.share_classes)),
            subscription_cadence=",".join(sorted(c.value for c in offering.subscription_cadence)),
            redemption_cadence=",".join(sorted(c.value for c in offering.redemption_cadence)),
            rebalance_cadence=",".join(sorted(c.value for c in offering.rebalance_cadence)),
            supports_daily_withdraw_deposit=str(offering.supports_daily_withdraw_deposit).lower(),
            notes=offering.notes,
        )
        for sc in sorted(offering.share_classes, key=lambda s: s.value):
            edges.append(
                CapabilityEdge(
                    from_node_id=fs_id,
                    to_node_id=f"share_class:{sc.value}",
                    relation=REL_OFFERS_SHARE_CLASS,
                    status=CapabilityEdgeStatus.AVAILABLE,
                    reason=f"{offering.kind.value} offers share class {sc.value}",
                )
            )
            add(
                CapabilityNodeKind.INSTRUMENT_TYPE,
                f"share_class:{sc.value}",
                f"Share Class: {sc.value}",
                share_class=sc.value,
            )

    # F49: OFFERED_SIGNING_SURFACES -> one SIGNING_SURFACE node per real signing
    # surface (CLOUD_KMS_ENCRYPTED / COPPER_MPC / FIREBLOCKS_MPC), with status +
    # asset-group scope. These are the genuine custody/signing nodes the manifest
    # was missing entirely while `custody_provider` was abused as a catch-all.
    # A signs_for edge per asset_group records the scope (out-of-scope surfaces
    # have no asset_groups → no edges, only the node, which is honest).
    for surface_policy in sorted(OFFERED_SIGNING_SURFACES, key=lambda p: p.surface.value):
        surf_id = f"signing_surface:{surface_policy.surface.value}"
        add(
            CapabilityNodeKind.SIGNING_SURFACE,
            surf_id,
            f"Signing Surface: {_titleize(surface_policy.surface.value)}",
            surface=surface_policy.surface.value,
            status=surface_policy.status.value,
            asset_groups=",".join(sorted(surface_policy.asset_groups)),
            source=surface_policy.source_note,
        )
        for ag in sorted(surface_policy.asset_groups):
            edges.append(
                CapabilityEdge(
                    from_node_id=surf_id,
                    to_node_id=f"signing_surface:{surface_policy.surface.value}",
                    relation=f"{REL_SIGNS_FOR}:{ag}",
                    status=CapabilityEdgeStatus.AVAILABLE,
                    reason=(f"{surface_policy.surface.value} signs for {ag} ({surface_policy.status.value})"),
                )
            )

    logger.info("  gap registries: %d nodes, %d edges", len(nodes), len(edges))
    return nodes, edges


# ---------------------------------------------------------------------------
# (e) Risk surface — KillSwitchReason x RiskGateLayer
# ---------------------------------------------------------------------------


def extract_risk_surface() -> tuple[list[CapabilityNode], list[CapabilityEdge]]:
    """KillSwitchReason + RiskGateLayer enums → risk nodes + generic
    archetype-availability is left to the archetype edges; here we emit the
    risk vocabulary and the cross-product of kill-switch reasons at risk layers
    (generic availability — per-archetype derivation is a backfill).
    """
    from unified_api_contracts.internal.architecture_v2.enums import (  # noqa: qg-deep-import
        KillSwitchReason,
        RiskGateLayer,
    )

    nodes: list[CapabilityNode] = []
    edges: list[CapabilityEdge] = []

    layers = sorted(layer.value for layer in RiskGateLayer)
    reasons = sorted(reason.value for reason in KillSwitchReason)

    for layer in layers:
        nodes.append(_node(CapabilityNodeKind.RISK_GATE_LAYER, f"risk_layer:{layer}", f"Risk Gate: {_titleize(layer)}"))
    for reason in reasons:
        nodes.append(
            _node(CapabilityNodeKind.KILL_SWITCH_REASON, f"kill_switch:{reason}", f"Kill Switch: {_titleize(reason)}")
        )

    # Generic availability: every kill-switch reason is guarded across all
    # risk layers (the per-archetype refinement is a derived backfill).
    for reason in reasons:
        for layer in layers:
            edges.append(
                CapabilityEdge(
                    from_node_id=f"kill_switch:{reason}",
                    to_node_id=f"risk_layer:{layer}",
                    relation=REL_AT_RISK_LAYER,
                    status=CapabilityEdgeStatus.AVAILABLE,
                )
            )

    logger.info("  risk surface: %d nodes, %d edges", len(nodes), len(edges))
    return nodes, edges


# ---------------------------------------------------------------------------
# (f) Service-resident registries — per-service venv subprocess
# ---------------------------------------------------------------------------

_SERVICE_PROBE = r"""
import json, sys
out = {{"ok": False}}
try:
{body}
except Exception as e:  # noqa: BLE001 — probe must report failure as a typed gap
    out = {{"ok": False, "error": "{kind}: " + type(e).__name__ + ": " + str(e)[:200]}}
sys.stdout.write(json.dumps(out))
"""


def _run_service_probe(workspace_root: Path, repo: str, body: str, kind: str) -> dict[str, object]:
    """Run a probe in the repo's own ``.venv`` (the generator-family idiom).

    Returns the parsed JSON dict, or ``{"ok": False, "error": ...}`` on any
    failure — the manifest still generates and records a typed gap.
    """
    venv_python = workspace_root / repo / ".venv" / "bin" / "python"
    if not venv_python.exists():
        return {"ok": False, "error": f"{kind}: no .venv at {venv_python}"}
    script = _SERVICE_PROBE.format(body=body, kind=kind)
    env = {
        "CLOUD_PROVIDER": "local",
        "CLOUD_MOCK_MODE": "true",
        "DISABLE_AUTH": "true",
        "GCP_PROJECT_ID": "mock-project",
        "GOOGLE_CLOUD_PROJECT": "mock-project",
        "ENVIRONMENT": "development",
        "PUBSUB_EMULATOR_HOST": "localhost:8085",
        "STORAGE_EMULATOR_HOST": "http://localhost:4443",
        "BIGQUERY_EMULATOR_HOST": "localhost:9050",
        "API_KEY": "mock-api-key",
        "PYTHONPATH": str(workspace_root / repo),
        "PATH": "/usr/bin:/bin",
        "HOME": str(workspace_root),
    }
    try:
        proc = subprocess.run(
            [str(venv_python), "-c", script],
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"{kind}: import probe timed out (180s)"}
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()
        return {"ok": False, "error": f"{kind}: exit {proc.returncode}: {tail[-1] if tail else 'no stderr'}"}
    # The probe prints exactly one JSON object on the last stdout line.
    line = (proc.stdout or "").strip().splitlines()
    if not line:
        return {"ok": False, "error": f"{kind}: empty stdout"}
    try:
        return json.loads(line[-1])
    except json.JSONDecodeError:
        return {"ok": False, "error": f"{kind}: unparseable probe output"}


def _archetype_model_edges(
    target_model_types: dict[str, set[str]],
    target_asset_groups: dict[str, set[str]],
) -> list[CapabilityEdge]:
    """Derive archetype→ml_model ``uses_model`` edges, SIGNAL-grounded (F53).

    For each archetype, map its REAL per-cell ``signal_variants`` → ML
    target_types (UAC ``SIGNAL_VARIANT_ML_TARGETS``) → the model types trainable
    for those targets (ml-service registry), domain-gated to the cell's asset
    group. So a carry/arb archetype whose signals are deterministic
    (basis/staking_yield) gets NO edges, and a swing archetype gets only the
    swing/direction model targets — not every model in its asset group.
    """
    from unified_api_contracts.internal.architecture_v2.archetype_capability import (  # noqa: qg-deep-import
        ARCHETYPE_CAPABILITY_REGISTRY,
        CoverageStatus,
    )
    from unified_api_contracts.internal.architecture_v2.ml_signal_targets import (  # noqa: qg-deep-import
        ml_targets_for_signal,
    )

    edges: list[CapabilityEdge] = []
    for entry in ARCHETYPE_CAPABILITY_REGISTRY:
        arch_node = entry.archetype_id.value
        mt_supported: dict[str, bool] = {}
        mt_targets: dict[str, set[str]] = {}
        mt_signals: dict[str, set[str]] = {}
        mt_ags: dict[str, set[str]] = {}
        for cell in entry.cells:
            if cell.status == CoverageStatus.BLOCKED:
                continue
            ag = cell.asset_group.value.lower()
            supported = cell.status == CoverageStatus.SUPPORTED
            for signal in cell.signal_variants:
                for target in ml_targets_for_signal(signal):
                    if ag not in target_asset_groups.get(target, set()):
                        continue  # domain gate: target not trained in this cell's asset group
                    for model_type in target_model_types.get(target, set()):
                        mt_supported[model_type] = mt_supported.get(model_type, False) or supported
                        mt_targets.setdefault(model_type, set()).add(target)
                        mt_signals.setdefault(model_type, set()).add(signal)
                        mt_ags.setdefault(model_type, set()).add(ag)
        for model_type in sorted(mt_targets):
            status = CapabilityEdgeStatus.AVAILABLE if mt_supported[model_type] else CapabilityEdgeStatus.PARTIAL
            sigs = sorted(mt_signals[model_type])
            tgts = sorted(mt_targets[model_type])
            ags = sorted(mt_ags[model_type])
            edges.append(
                CapabilityEdge(
                    from_node_id=arch_node,
                    to_node_id=f"ml_model:{model_type}",
                    relation=REL_USES_MODEL,
                    status=status,
                    reason=f"signals {','.join(sigs[:4])} → targets {','.join(tgts[:4])} ({','.join(ags)})",
                )
            )
    return edges


def extract_service_registries(workspace_root: Path) -> tuple[list[CapabilityNode], list[CapabilityEdge]]:
    """Execution algos + feature groups (with lookback) + ML models.

    Each source is imported in its own service ``.venv`` subprocess.  Any
    unimportable source yields a typed ``missing_extraction`` gap edge naming
    the failure — the manifest still generates and says so honestly.

    Min-data-to-run derived edges (feature lookback x ML training window) are
    emitted only where both feature lookbacks AND an ML training window are
    available; the ML training window is a runtime config (no static registry
    constant) → that derivation is a typed ``missing_extraction`` gap.
    """
    nodes: list[CapabilityNode] = []
    edges: list[CapabilityEdge] = []

    def gap_node_edge(dim: str, label: str, error: str) -> None:
        node_id = f"service_registry:{dim}"
        nodes.append(_node(CapabilityNodeKind.GAP_REGISTRY, node_id, label, registry=dim))
        edges.append(
            CapabilityEdge(
                from_node_id=node_id,
                to_node_id=node_id,
                relation=REL_NOT_REGISTERED,
                status=CapabilityEdgeStatus.NOT_REGISTERED,
                gap_type=CapabilityGapType.MISSING_EXTRACTION,
                reason=error,
            )
        )

    # --- execution algos ---
    exec_body = (
        "    from execution_service.algorithms.registry import ExecAlgorithmRegistry\n"
        "    reg = ExecAlgorithmRegistry()\n"
        "    out = {'ok': True, 'algos': sorted(str(a) for a in reg.list_algorithms())}\n"
    )
    res = _run_service_probe(workspace_root, "execution-service", exec_body, "execution_algos")
    if res.get("ok"):
        algos = res.get("algos", [])
        if isinstance(algos, list):
            for algo in sorted(str(a) for a in algos):
                aid = f"execution_algo:{algo}"
                nodes.append(_node(CapabilityNodeKind.EXECUTION_ALGO, aid, _titleize(algo)))
        logger.info("  execution algos: %d", len(algos) if isinstance(algos, list) else 0)
    else:
        gap_node_edge("execution_algos", "Execution algorithms", str(res.get("error", "unknown")))
        logger.warning("  execution algos GAP: %s", res.get("error"))

    # --- feature groups (with max lookback period) ---
    feat_body = (
        "    from features_service.delta_one.app.features.registry import build_full_registry\n"
        "    specs = build_full_registry()\n"
        "    groups = {}\n"
        "    for s in specs:\n"
        "        p = s.period if isinstance(getattr(s, 'period', None), int) else 0\n"
        "        groups[s.group] = max(groups.get(s.group, 0), p or 0)\n"
        "    out = {'ok': True, 'groups': groups}\n"
    )
    res = _run_service_probe(workspace_root, "features-service", feat_body, "feature_groups")
    feature_groups: dict[str, int] = {}
    if res.get("ok"):
        raw = res.get("groups", {})
        if isinstance(raw, dict):
            feature_groups = {str(k): int(v) for k, v in raw.items()}
        for grp in sorted(feature_groups):
            gid = f"feature_group:{grp}"
            nodes.append(
                _node(
                    CapabilityNodeKind.FEATURE_GROUP,
                    gid,
                    _titleize(grp),
                    max_lookback_bars=str(feature_groups[grp]),
                )
            )
        logger.info("  feature groups: %d", len(feature_groups))
    else:
        gap_node_edge("feature_groups", "Feature groups", str(res.get("error", "unknown")))
        logger.warning("  feature groups GAP: %s", res.get("error"))

    # --- ML models ---
    # F53: walk the ml-service model registry. VALID_MODEL_TYPES is the static,
    # enumerable model-type registry (lightgbm/xgboost/catboost/random_forest/
    # huber/poisson_glm/ridge/ensemble); VALID_TARGET_TYPES is the prediction-
    # target registry. Both are real, importable constants — emit one ml_model
    # node per model type (not just the single variant_config). ModelVariantConfig
    # fields are also carried so the wizard's "which ML model" dimension is real.
    # F53 residual: the ml-service ``model_variant_registry`` exposes the
    # per-(asset_group, target_type) trainable variants (SSOT-derived from the
    # SportsMLPresets families / DEFI_TARGET_BUILDERS / technical target subset).
    # We pull it alongside VALID_MODEL_TYPES so the exporter can derive real
    # archetype→model ``uses_model`` edges (below) instead of leaving them a gap.
    ml_body = (
        "    from ml_service.training.ml.config_schema import VALID_MODEL_TYPES, VALID_TARGET_TYPES\n"
        "    from ml_service.training.ml.model_registry import ModelVariantConfig\n"
        "    from ml_service.training.ml.model_variant_registry import (\n"
        "        model_variants, model_types_for_target, asset_groups_for_target)\n"
        "    from ml_service.training.app.core.defi_target_generator import DEFI_TARGET_BUILDERS\n"
        "    fields = sorted(getattr(ModelVariantConfig, 'model_fields', {}).keys())\n"
        "    variants = [\n"
        "        {'asset_group': v.asset_group, 'target_type': v.target_type,\n"
        "         'model_types': list(v.model_types), 'source': v.model_types_source}\n"
        "        for v in model_variants()\n"
        "    ]\n"
        "    flat_targets = sorted(set(VALID_TARGET_TYPES) | set(DEFI_TARGET_BUILDERS.keys()))\n"
        "    target_model_types = {t: list(model_types_for_target(t)) for t in flat_targets}\n"
        "    target_asset_groups = {t: list(asset_groups_for_target(t)) for t in flat_targets}\n"
        "    out = {'ok': True, 'model_types': sorted(VALID_MODEL_TYPES),\n"
        "           'target_types': sorted(VALID_TARGET_TYPES), 'variant_fields': fields,\n"
        "           'model_variants': variants,\n"
        "           'target_model_types': target_model_types,\n"
        "           'target_asset_groups': target_asset_groups}\n"
    )
    res = _run_service_probe(workspace_root, "ml-service", ml_body, "ml_models")
    ml_model_count = 0
    # asset_group → {model_types}, plus flat target → {model_types}/{asset_groups}.
    ag_to_model_types: dict[str, set[str]] = {}
    target_model_types: dict[str, set[str]] = {}
    target_asset_groups: dict[str, set[str]] = {}

    def _parse_str_set_map(value: object) -> dict[str, set[str]]:
        out: dict[str, set[str]] = {}
        if isinstance(value, dict):
            for k, v in cast("dict[str, object]", value).items():
                if isinstance(v, list):
                    out[str(k)] = {str(item) for item in cast("list[object]", v)}
        return out

    if res.get("ok"):
        model_types = _as_str_list(res.get("model_types", []))  # noqa: qg-empty-fallback (typed list narrow)
        target_types = _as_str_list(res.get("target_types", []))  # noqa: qg-empty-fallback (typed list narrow)
        variant_fields = ",".join(_as_str_list(res.get("variant_fields", [])))  # noqa: qg-empty-fallback
        target_model_types = {k.strip(): v for k, v in _parse_str_set_map(res.get("target_model_types")).items()}
        target_asset_groups = {
            k.strip(): {a.strip().lower() for a in v}
            for k, v in _parse_str_set_map(res.get("target_asset_groups")).items()
        }
        # model_type → {asset_groups it is trainable for} (registry-derived node metadata).
        model_to_ags: dict[str, set[str]] = {}
        variants_raw = res.get("model_variants")
        if isinstance(variants_raw, list):
            for raw in variants_raw:
                if not isinstance(raw, dict):
                    continue
                variant = cast("dict[str, object]", raw)
                ag = str(variant.get("asset_group", "")).strip().lower()
                mts = variant.get("model_types")
                if not ag or not isinstance(mts, list):
                    continue
                typed_mts = {str(m) for m in cast("list[object]", mts)}
                ag_to_model_types.setdefault(ag, set()).update(typed_mts)
                for mt in typed_mts:
                    model_to_ags.setdefault(mt, set()).add(ag)
        for model_type in model_types:
            serving = sorted(model_to_ags.get(model_type, set()))
            nodes.append(
                _node(
                    CapabilityNodeKind.ML_MODEL,
                    f"ml_model:{model_type}",
                    f"ML Model: {_titleize(model_type)}",
                    model_type=model_type,
                    target_types=",".join(target_types),
                    variant_fields=variant_fields,
                    serves_asset_groups=",".join(serving),
                )
            )
        ml_model_count = len(model_types)
        logger.info(
            "  ml models: %d model types, %d asset_groups with variants",
            ml_model_count,
            len(ag_to_model_types),
        )
    else:
        gap_node_edge("ml_models", "ML model registry", str(res.get("error", "unknown")))
        logger.warning("  ml models GAP: %s", res.get("error"))

    # --- archetype → ml_model uses_model edges (F53, signal-grounded) ---
    if target_model_types:
        model_edges = _archetype_model_edges(target_model_types, target_asset_groups)
        edges.extend(model_edges)
        logger.info("  archetype→model uses_model edges (signal-grounded): %d", len(model_edges))

    # --- min-data-to-run derived edges ---
    # Feature lookback IS available; the ML training window is a runtime config
    # with no static registry constant → typed missing_extraction gap.
    if feature_groups:
        max_lookback = max(feature_groups.values())
        deepest = sorted(g for g, p in feature_groups.items() if p == max_lookback)[0] if max_lookback else ""
        node_id = "min_data_to_run:feature_lookback"
        nodes.append(
            _node(
                CapabilityNodeKind.FEATURE_GROUP,
                node_id,
                "Min Data To Run (feature lookback)",
                max_feature_lookback_bars=str(max_lookback),
                deepest_group=deepest,
            )
        )
        # Feature-lookback component IS derivable.
        edges.append(
            CapabilityEdge(
                from_node_id=node_id,
                to_node_id=node_id,
                relation=REL_MIN_DATA_TO_RUN,
                status=CapabilityEdgeStatus.PARTIAL,
                gap_type=CapabilityGapType.MISSING_EXTRACTION,
                reason=(
                    f"feature-lookback component derived (max {max_lookback} bars, group {deepest}); "
                    "ML training-window factor is a runtime config with no static registry constant — "
                    "full min-data-to-run = feature_lookback x training_window pending ML training-window extraction"
                ),
            )
        )
    else:
        edges.append(
            CapabilityEdge(
                from_node_id="min_data_to_run:feature_lookback",
                to_node_id="min_data_to_run:feature_lookback",
                relation=REL_MIN_DATA_TO_RUN,
                status=CapabilityEdgeStatus.NOT_REGISTERED,
                gap_type=CapabilityGapType.MISSING_EXTRACTION,
                reason=(
                    "feature-group lookbacks unavailable (features-service import gap) — min-data-to-run not derivable"
                ),
            )
        )
        nodes.append(
            _node(
                CapabilityNodeKind.FEATURE_GROUP,
                "min_data_to_run:feature_lookback",
                "Min Data To Run (feature lookback)",
            )
        )

    logger.info("  service registries: %d nodes, %d edges", len(nodes), len(edges))
    return nodes, edges


def extract_algo_compatibility() -> tuple[list[CapabilityNode], list[CapabilityEdge]]:
    """Archetype → execution-algorithm compatibility edges (Phase 6A).

    From the UAC ``ARCHETYPE_ALGO_COMPATIBILITY`` registry (which transcribes the
    execution-service selector). For every (archetype, algo) pair we emit a
    ``uses_algo`` edge with an explicit status:

      - ``available`` — the algo is VALID for the archetype's instruction action(s).
      - ``not_available`` — the algo is BLOCKED (impossible combination): not valid
        for any of the archetype's instruction types (reason carries the selector
        basis). This is exactly the impossible-combo blocking the operator
        required (e.g. TWAP on a pure-staking archetype → not_available).
      - ``not_registered`` — the archetype has no leg structure (no algos derivable).

    Each ``execution_algo`` node carries ``implemented`` (the ghost-algorithm
    honesty flag). The ``SELECTOR_CONTRADICTIONS`` are emitted as
    ``execution_algo`` finding nodes so the manifest carries the code-vs-docs
    discrepancies the operator wants surfaced.
    """
    from unified_api_contracts.internal.architecture_v2.algo_compatibility import (  # noqa: qg-deep-import
        ARCHETYPE_ALGO_COMPATIBILITY,
        EXECUTION_ALGOS,
        SELECTOR_CONTRADICTIONS,
    )

    nodes: list[CapabilityNode] = []
    edges: list[CapabilityEdge] = []

    # Execution-algo nodes (with implemented flag — the ghost-algorithm honesty).
    for key in sorted(EXECUTION_ALGOS):
        algo = EXECUTION_ALGOS[key]
        nodes.append(
            _node(
                CapabilityNodeKind.EXECUTION_ALGO,
                f"execution_algo:{key}",
                _titleize(key),
                implemented=str(algo.implemented).lower(),
                note=algo.note,
            )
        )

    # Per-archetype algo verdict edges.
    for archetype in sorted(ARCHETYPE_ALGO_COMPATIBILITY, key=lambda a: a.value):
        compat = ARCHETYPE_ALGO_COMPATIBILITY[archetype]
        # Archetype nodes are emitted with the RAW archetype value as node_id
        # (_capability_extract.add_node) — NOT an "archetype:" prefix. The prefix
        # form dangled every uses_algo edge (0 connected); use the raw id.
        arch_node = archetype.value
        for key in sorted(EXECUTION_ALGOS):
            algo_node = f"execution_algo:{key}"
            if compat.not_registered:
                edges.append(
                    CapabilityEdge(
                        from_node_id=arch_node,
                        to_node_id=algo_node,
                        relation=REL_USES_ALGO,
                        status=CapabilityEdgeStatus.NOT_REGISTERED,
                        gap_type=CapabilityGapType.MISSING_REGISTRY,
                        reason=f"archetype has no leg structure: {compat.not_registered_reason}",
                    )
                )
            elif key in compat.valid_algos:
                edges.append(
                    CapabilityEdge(
                        from_node_id=arch_node,
                        to_node_id=algo_node,
                        relation=REL_USES_ALGO,
                        status=CapabilityEdgeStatus.AVAILABLE,
                        reason=compat.reason_for(key),
                    )
                )
            else:
                edges.append(
                    CapabilityEdge(
                        from_node_id=arch_node,
                        to_node_id=algo_node,
                        relation=REL_USES_ALGO,
                        status=CapabilityEdgeStatus.NOT_AVAILABLE,
                        gap_type=CapabilityGapType.LOGICAL_DEAD_END,
                        reason=compat.reason_for(key),
                    )
                )

    # Selector contradictions → finding nodes (code-vs-docs, operator wants caught).
    for contradiction in SELECTOR_CONTRADICTIONS:
        nodes.append(
            _node(
                CapabilityNodeKind.EXECUTION_ALGO,
                f"selector_contradiction:{contradiction.slug}",
                f"Selector contradiction: {contradiction.slug}",
                summary=contradiction.summary,
                citation=contradiction.citation,
            )
        )

    logger.info("  algo compatibility: %d nodes, %d edges", len(nodes), len(edges))
    return nodes, edges


# ---------------------------------------------------------------------------
# (g) Per-archetype flat PARAM SCHEMA — sourced from the strategy-service engine
#     SSOT (Phase C). The wizard renders numeric/enum param forms from this.
# ---------------------------------------------------------------------------

# Relation marker for the gap edge emitted when the strategy-service probe fails.
REL_PARAM_SCHEMA_GAP = "param_schema_gap"

_PARAM_SCHEMA_ALLOWED_TYPES: frozenset[str] = frozenset({"int", "float", "decimal", "str", "enum", "bool"})


def extract_param_schema(
    workspace_root: Path,
) -> tuple[dict[str, list[ParamSchemaSpec]], list[CapabilityNode], list[CapabilityEdge]]:
    """Per-archetype flat config PARAM SCHEMA, sourced from the engine SSOT.

    Probes ``strategy_service.engine.strategies.v2.param_schema``
    ``build_param_schema_registry()`` in strategy-service's OWN ``.venv`` (the same
    subprocess idiom as :func:`extract_service_registries`) — so the schema comes
    from each engine's actual ``*_param(params, "<name>", <default>)`` default
    surface (Phase B inventory), never re-typed by hand in the exporter. Returns
    ``(param_schema, nodes, edges)``: ``param_schema`` keyed by archetype node_id
    (``StrategyArchetype`` value), plus an honest ``not_registered`` gap node/edge
    when the probe is unavailable (the manifest still generates without it).
    """
    body = (
        "    from strategy_service.engine.strategies.v2.param_schema import build_param_schema_registry\n"
        "    out = {'ok': True, 'param_schema': build_param_schema_registry()}\n"
    )
    res = _run_service_probe(workspace_root, "strategy-service", body, "param_schema")

    if not res.get("ok"):
        node_id = "service_registry:param_schema"
        gap_node = _node(
            CapabilityNodeKind.GAP_REGISTRY,
            node_id,
            "Archetype param schema",
            registry="param_schema",
        )
        gap_edge = CapabilityEdge(
            from_node_id=node_id,
            to_node_id=node_id,
            relation=REL_PARAM_SCHEMA_GAP,
            status=CapabilityEdgeStatus.NOT_REGISTERED,
            gap_type=CapabilityGapType.MISSING_EXTRACTION,
            reason=str(res.get("error", "param_schema probe unavailable")),
        )
        logger.warning("  param schema GAP: %s", res.get("error"))
        return {}, [gap_node], [gap_edge]

    raw = res.get("param_schema", {})
    param_schema: dict[str, list[ParamSchemaSpec]] = {}
    total_params = 0
    if isinstance(raw, dict):
        for archetype, rows in cast("dict[str, object]", raw).items():
            if not isinstance(rows, list):
                continue
            specs: list[ParamSchemaSpec] = []
            for row in cast("list[object]", rows):
                if not isinstance(row, dict):
                    continue
                rd = cast("dict[str, object]", row)
                ptype = str(rd.get("type", "str"))
                if ptype not in _PARAM_SCHEMA_ALLOWED_TYPES:
                    logger.warning("  param schema: %s.%s bad type %s", archetype, rd.get("name"), ptype)
                    continue
                default_raw = rd.get("default")
                units_raw = rd.get("units")
                min_raw = rd.get("min")
                max_raw = rd.get("max")
                source_raw = rd.get("source")
                enum_raw = rd.get("enum_values", [])
                specs.append(
                    ParamSchemaSpec(
                        name=str(rd.get("name", "")),
                        type=ptype,
                        default=None if default_raw is None else str(default_raw),
                        required=bool(rd.get("required", False)),
                        units=None if units_raw is None else str(units_raw),
                        enum_values=[str(v) for v in cast("list[object]", enum_raw)]
                        if isinstance(enum_raw, list)
                        else [],
                        min=None if min_raw is None else str(min_raw),
                        max=None if max_raw is None else str(max_raw),
                        source=None if source_raw is None else str(source_raw),
                    )
                )
            if specs:
                param_schema[str(archetype)] = specs
                total_params += len(specs)

    logger.info("  param schema: %d archetypes, %d params", len(param_schema), total_params)
    return param_schema, [], []
