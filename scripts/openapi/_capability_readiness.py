"""Per-edge operational-maturity (readiness) annotation pass (Wave-2 #2).

Stamps every capability edge that originates from a strategy ``archetype`` node
with an operational-maturity tier — one of::

    backtest-only | shadow-observed | staging-proven | live-proven

"Available" (the capability graph says the system *can* express the edge) is a
different answer from "ever ran" (the edge has operational evidence).  This pass
resolves the latter from on-host, committed, deterministic evidence and folds it
into ``CapabilityEdge.readiness`` (and a sibling readiness report).

Maturity → C/D/B gate mapping (``plans/PLAN_FORMAT.md`` § "3-Tier Readiness Model")
-----------------------------------------------------------------------------------
The PLAN_FORMAT readiness gates are the SSOT for "how proven is this":

  * ``backtest-only``   ← C-tier only (code exists / unit-tested; no deployment
    or live observation).  The HONEST default when no operational evidence
    exists on-host.
  * ``shadow-observed`` ← ~D2 (CI/mock e2e or a declared shadow-mode run; observed
    but not staging-proven).
  * ``staging-proven``  ← D3 (staging integration / SIT — *real* service + API
    calls in a staging environment): a ``LIVE_CLUSTER_REGISTRY`` row at
    ``EnvironmentTier.STAGING`` owns the archetype.
  * ``live-proven``     ← D5 / B-tier (production-deployed + operationally
    proven): a ``LIVE_CLUSTER_REGISTRY`` row at ``EnvironmentTier.PROD`` owns
    the archetype.

Evidence source (on-host, committed, deterministic)
---------------------------------------------------
The single real maturity signal that exists on-host is the **live-cluster
registry** (``unified_api_contracts.canonical.crosscutting.live_cluster_registry
.LIVE_CLUSTER_REGISTRY``).  Each row declares a long-lived live deployment with
an ``environment_tier`` (STAGING / PROD) and the ``archetype_owners`` it serves.
A PROD-tier owner ⇒ ``live-proven``; a STAGING-tier owner (no PROD) ⇒
``staging-proven``.  The chosen cluster's ``name`` is cited as the evidence so
every non-``backtest-only`` stamp names its source (auditable).

There is **no populated shadow ledger or deployments registry on-host**: the
``shadow_mode`` flag on ``AllocationDirective`` is a runtime schema field with
no committed run records, and ``deployments_registry.py`` is a *GCS-backed*
runtime table (written by VMs at run time), not a committed-in-repo evidence
source.  So ``shadow-observed`` is reachable only via an explicit, committed
override (see ``READINESS_OVERRIDES``) — never inferred — and absent any
evidence an archetype defaults HONESTLY to ``backtest-only`` (we never claim
``live-proven`` without a cited registry row).

The pass is deterministic (registry is a static tuple; tiers resolved by a
fixed precedence) → two runs are byte-identical.

SSOT: ``plans/active/capability_wizard_and_manifest_2026_06_11.md`` Wave-2 #2.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from unified_api_contracts import (
    LIVE_CLUSTER_REGISTRY,
    EnvironmentTier,
    LiveClusterSpec,
)
from unified_api_contracts.internal.architecture_v2.capability_manifest import (
    CapabilityEdge,
    CapabilityNode,
    CapabilityNodeKind,
)

# ---------------------------------------------------------------------------
# Readiness tier vocabulary (closed set) + tier ordering
# ---------------------------------------------------------------------------

#: Code exists / unit-tested only — the honest default with no operational evidence.
READINESS_BACKTEST_ONLY = "backtest-only"
#: Observed in a shadow/mock run (D2-ish) — only via an explicit committed override.
READINESS_SHADOW_OBSERVED = "shadow-observed"
#: Staging integration proven (D3) — a STAGING-tier live-cluster row owns the archetype.
READINESS_STAGING_PROVEN = "staging-proven"
#: Production-deployed + operationally proven (D5/B) — a PROD-tier row owns the archetype.
READINESS_LIVE_PROVEN = "live-proven"

#: Closed, ordered set (least → most proven). Index used for "best tier wins".
READINESS_TIERS: tuple[str, ...] = (
    READINESS_BACKTEST_ONLY,
    READINESS_SHADOW_OBSERVED,
    READINESS_STAGING_PROVEN,
    READINESS_LIVE_PROVEN,
)
_TIER_RANK: dict[str, int] = {tier: i for i, tier in enumerate(READINESS_TIERS)}

#: The C/D/B gate (``plans/PLAN_FORMAT.md`` § 3-Tier Readiness Model) each tier maps to.
READINESS_TO_GATE: dict[str, str] = {
    READINESS_BACKTEST_ONLY: "C2",
    READINESS_SHADOW_OBSERVED: "D2",
    READINESS_STAGING_PROVEN: "D3",
    READINESS_LIVE_PROVEN: "D5",
}

#: Explicit, committed maturity overrides keyed by archetype node_id (UPPERCASE).
#: This is the ONLY route to ``shadow-observed`` — it must be a deliberate,
#: reviewed entry citing real evidence (a shadow-run record / paper-trade log),
#: never inferred.  Empty today: no committed shadow-run evidence exists on-host.
#: Shape: ``{archetype_node_id: (tier, evidence_citation)}``.
READINESS_OVERRIDES: dict[str, tuple[str, str]] = {}


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReadinessVerdict:
    """The resolved maturity tier for one archetype + its cited evidence."""

    archetype_id: str
    readiness: str
    #: Cited evidence source (cluster name / override note); empty for backtest-only.
    evidence: str
    #: The PLAN_FORMAT C/D/B gate this tier maps to.
    gate: str

    def to_dict(self) -> dict[str, str]:
        return {
            "archetype_id": self.archetype_id,
            "readiness": self.readiness,
            "evidence": self.evidence,
            "gate": self.gate,
        }


def _tier_for_env(env: EnvironmentTier) -> str | None:
    """Map a live-cluster environment tier to a readiness tier (None = no signal)."""
    if env == EnvironmentTier.PROD:
        return READINESS_LIVE_PROVEN
    if env == EnvironmentTier.STAGING:
        return READINESS_STAGING_PROVEN
    # DEV (or any future non-prod/non-staging tier) is not positive live evidence.
    return None


def build_live_cluster_index(
    registry: tuple[LiveClusterSpec, ...] = LIVE_CLUSTER_REGISTRY,
) -> dict[str, tuple[str, str]]:
    """Map each archetype owner → its BEST (most-proven) tier + cited cluster name.

    Keys are UPPERCASED archetype ids (the registry stores lowercase
    ``archetype_owners`` like ``carry_staked_basis``; the manifest archetype
    node_ids are uppercase ``StrategyArchetype`` values like
    ``CARRY_STAKED_BASIS``) so the lookup matches the manifest node_ids.

    Deterministic: a static tuple iterated in declaration order; on a tier tie
    the first-declared cluster name is cited (stable).
    """
    best: dict[str, tuple[str, str]] = {}
    for spec in registry:
        tier = _tier_for_env(spec.environment_tier)
        if tier is None:
            continue
        for owner in spec.archetype_owners:
            key = owner.upper()
            prev = best.get(key)
            if prev is None or _TIER_RANK[tier] > _TIER_RANK[prev[0]]:
                best[key] = (tier, spec.name)
    return best


def resolve_archetype_readiness(
    archetype_ids: list[str],
    cluster_index: dict[str, tuple[str, str]] | None = None,
    overrides: dict[str, tuple[str, str]] | None = None,
) -> dict[str, ReadinessVerdict]:
    """Resolve a ``ReadinessVerdict`` for every archetype id.

    Precedence (highest wins): an explicit committed ``overrides`` entry, then
    the live-cluster registry evidence, then the HONEST ``backtest-only``
    default.  An override never DOWNGRADES below the registry-derived tier (we
    never hide a genuine live-proven behind a stale shadow override) — the
    most-proven of (override, registry) wins, citing that side's evidence.
    """
    idx = build_live_cluster_index() if cluster_index is None else cluster_index
    ovr = READINESS_OVERRIDES if overrides is None else overrides
    out: dict[str, ReadinessVerdict] = {}
    for arch in archetype_ids:
        tier = READINESS_BACKTEST_ONLY
        evidence = ""
        registry_hit = idx.get(arch)
        if registry_hit is not None:
            tier, cluster_name = registry_hit
            evidence = f"live_cluster_registry:{cluster_name}"
        override_hit = ovr.get(arch)
        if override_hit is not None:
            ovr_tier, ovr_evidence = override_hit
            # Most-proven wins; override only takes effect if it's >= registry tier.
            if _TIER_RANK[ovr_tier] > _TIER_RANK[tier]:
                tier, evidence = ovr_tier, ovr_evidence
        out[arch] = ReadinessVerdict(
            archetype_id=arch,
            readiness=tier,
            evidence=evidence,
            gate=READINESS_TO_GATE[tier],
        )
    return out


def annotate_edges_with_readiness(
    nodes: list[CapabilityNode],
    edges: list[CapabilityEdge],
    cluster_index: dict[str, tuple[str, str]] | None = None,
    overrides: dict[str, tuple[str, str]] | None = None,
) -> tuple[list[CapabilityEdge], dict[str, ReadinessVerdict]]:
    """Fold readiness onto every edge whose ``from_node_id`` is an archetype.

    Returns ``(new_edges, verdicts)``.  ``new_edges`` is a fresh list (frozen
    pydantic models are replaced, never mutated) — edges not originating from an
    archetype are returned unchanged.  Additive only: ``status`` / ``gap_type``
    are never touched, so this can NEVER flip an edge available→not_available.
    """
    archetype_ids = sorted(n.node_id for n in nodes if n.kind == CapabilityNodeKind.ARCHETYPE)
    verdicts = resolve_archetype_readiness(archetype_ids, cluster_index=cluster_index, overrides=overrides)

    new_edges: list[CapabilityEdge] = []
    for edge in edges:
        verdict = verdicts.get(edge.from_node_id)
        if verdict is None:
            new_edges.append(edge)
            continue
        new_edges.append(replace_readiness(edge, verdict.readiness))
    return new_edges, verdicts


def replace_readiness(edge: CapabilityEdge, readiness: str) -> CapabilityEdge:
    """Return a copy of ``edge`` with ``readiness`` set (frozen-model safe)."""
    return edge.model_copy(update={"readiness": readiness})


# ---------------------------------------------------------------------------
# Report rendering (sibling readiness report — JSON + markdown)
# ---------------------------------------------------------------------------


def tier_distribution(verdicts: dict[str, ReadinessVerdict]) -> dict[str, int]:
    """Count archetypes per readiness tier (every tier present, zero-filled)."""
    counts = Counter(v.readiness for v in verdicts.values())
    return {tier: int(counts.get(tier, 0)) for tier in READINESS_TIERS}


def build_readiness_report(
    manifest_commit: str | None,
    verdicts: dict[str, ReadinessVerdict],
) -> dict[str, object]:
    """Assemble the deterministic JSON readiness payload."""
    ordered = [verdicts[k].to_dict() for k in sorted(verdicts)]
    return {
        "manifest_commit": manifest_commit or "unknown",
        "readiness_tiers": list(READINESS_TIERS),
        "readiness_to_gate": dict(sorted(READINESS_TO_GATE.items())),
        "evidence_model": (
            "live_cluster_registry (PROD→live-proven, STAGING→staging-proven); "
            "absent evidence → backtest-only (honest default); shadow-observed "
            "only via committed override (none on-host today)"
        ),
        "tier_distribution": tier_distribution(verdicts),
        "archetypes": ordered,
    }


def _section(title: str, lines: list[str]) -> list[str]:
    out = [f"## {title} ({len(lines)})", ""]
    out.extend(lines if lines else ["_none_"])
    out.append("")
    return out


def render_readiness_markdown(
    manifest_commit: str | None,
    verdicts: dict[str, ReadinessVerdict],
) -> str:
    """Render the per-archetype readiness report as deterministic markdown."""
    dist = tier_distribution(verdicts)
    out: list[str] = [
        "# Capability readiness report — per-edge operational maturity (Wave-2 #2)",
        "",
        "Operational-maturity tier for every strategy archetype, folded onto each",
        "archetype-originating edge in `capability-manifest.json` as `readiness`.",
        "Regenerated by `scripts/openapi/generate_capability_manifest.py` (the",
        "readiness pass) — deterministic (two runs are byte-identical).",
        "",
        '"Available" (the graph says the system *can* do it) is a different answer',
        'from "ever ran". This report answers the latter, from on-host evidence.',
        "",
        "**Evidence**: the live-cluster registry (`LIVE_CLUSTER_REGISTRY`) is the only",
        "real on-host maturity signal — a PROD-tier row owning an archetype ⇒",
        "`live-proven`, a STAGING-tier row ⇒ `staging-proven`. Absent evidence ⇒",
        "`backtest-only` (the honest default — never an over-claim). `shadow-observed`",
        "is reachable only via a committed override (none on-host today). Each",
        "non-`backtest-only` stamp cites its evidence source.",
        "",
        "**Maturity → C/D/B gate** (`plans/PLAN_FORMAT.md` § 3-Tier Readiness Model):",
        "`backtest-only`→C2, `shadow-observed`→D2, `staging-proven`→D3, `live-proven`→D5.",
        "",
        f"Manifest commit: `{manifest_commit or 'unknown'}`",
        "",
    ]

    dist_lines = [f"- `{tier}` (gate {READINESS_TO_GATE[tier]}): **{dist[tier]}**" for tier in READINESS_TIERS]
    out.extend(_section("Tier distribution", dist_lines))

    # Proven (non-backtest-only) archetypes, most-proven first, each citing evidence.
    proven = [v for v in verdicts.values() if v.readiness != READINESS_BACKTEST_ONLY]
    proven.sort(key=lambda v: (-_TIER_RANK[v.readiness], v.archetype_id))
    proven_lines = [
        f"- `{v.archetype_id}` — **{v.readiness}** (gate {v.gate}) — evidence: `{v.evidence}`" for v in proven
    ]
    out.extend(_section("Operationally-proven archetypes (cited)", proven_lines))

    # backtest-only archetypes (the honest majority).
    backtest = sorted(v.archetype_id for v in verdicts.values() if v.readiness == READINESS_BACKTEST_ONLY)
    backtest_lines = [f"- `{a}`" for a in backtest]
    out.extend(_section("Backtest-only archetypes (no operational evidence on-host)", backtest_lines))

    return "\n".join(out) + "\n"
