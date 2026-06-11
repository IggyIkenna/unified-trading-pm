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

from unified_api_contracts.internal.architecture_v2.capability_manifest import (
    CapabilityEdge,
    CapabilityEdgeStatus,
    CapabilityGapType,
    CapabilityNode,
    CapabilityNodeKind,
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


def _node(kind: CapabilityNodeKind, node_id: str, label: str, **meta: str) -> CapabilityNode:
    return CapabilityNode(kind=kind, node_id=node_id, label=label, metadata={k: str(v) for k, v in meta.items()})


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
        add(CapabilityNodeKind.CUSTODY_PROVIDER, node_id, label, registry=dim, entry_count=str(count))
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
        nodes.append(
            _node(CapabilityNodeKind.CUSTODY_PROVIDER, f"risk_layer:{layer}", f"Risk Gate: {_titleize(layer)}")
        )
    for reason in reasons:
        nodes.append(
            _node(CapabilityNodeKind.CUSTODY_PROVIDER, f"kill_switch:{reason}", f"Kill Switch: {_titleize(reason)}")
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
        nodes.append(_node(CapabilityNodeKind.CUSTODY_PROVIDER, node_id, label, registry=dim))
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
    ml_body = (
        "    from ml_service.training.ml.model_registry import ModelVariantConfig\n"
        "    fields = sorted(getattr(ModelVariantConfig, 'model_fields', {}).keys())\n"
        "    out = {'ok': True, 'variant_fields': fields}\n"
    )
    res = _run_service_probe(workspace_root, "ml-service", ml_body, "ml_models")
    ml_ok = bool(res.get("ok"))
    if ml_ok:
        nodes.append(
            _node(
                CapabilityNodeKind.ML_MODEL,
                "ml_model:variant_config",
                "ML Model Variant Config",
                variant_fields=",".join(
                    str(f) for f in res.get("variant_fields", []) if isinstance(res.get("variant_fields"), list)
                ),
            )
        )
        logger.info("  ml models: variant config extracted")
    else:
        gap_node_edge("ml_models", "ML model registry", str(res.get("error", "unknown")))
        logger.warning("  ml models GAP: %s", res.get("error"))

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
                    "feature-group lookbacks unavailable (features-service import gap) — "
                    "min-data-to-run not derivable"
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
