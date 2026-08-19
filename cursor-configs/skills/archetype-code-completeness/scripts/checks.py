#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Per-hook code-completeness checks for the archetype-code-completeness skill.

/plans/epics/system_readiness_master.md § W1: "Archetype readiness is CODE
completeness, not data availability." The existing `strategy — archetype
half` leg in readiness-state-dump uses `satisfying_archetypes()`, which
answers "which archetypes can this venue's DATA satisfy" -- a DATA question.
This module answers a different one: "are this archetype's code paths and
hooks complete for batch / paper / live" -- independent of any venue's data.

Same Verdict vocabulary and proxy discipline as readiness-state-dump's
checks.py (deliberately reused, not reinvented -- see that module's
docstring for the full policy statement):

  "ready"      -- a real machine check ran and passed.
  "not_ready"  -- a real machine check ran and failed -- a genuine negative
                  is always reportable.
  "unverified" -- no real check exists yet, the only signal is a capability
                  proxy that doesn't confirm the property being asked about,
                  OR (new tier below) a DATED AGENT AUDIT: a human/agent read
                  the source and recorded a judgment because no clean
                  registry lookup exists. An agent-audit note is honestly
                  still "unverified" (not a machine fact), but it is
                  distinguished in evidence text from a bare "no check
                  exists" so a reader knows *why* -- see AGENT_AUDIT_DATE.

Four hooks, per the task's own framing (factory registration, param-schema
registration, allocator-rank registration, mode-specific dispatch), plus one
mode-invariant catalog hook discovered during research (an archetype with no
target_universe.TARGET_UNIVERSE entry cannot be replayed in paper OR
batch-rerun, and is the concrete check paper_run_handler.py itself performs):

  engine_factory         -- ARCHETYPE_ENGINE_REGISTRY membership + the lazy
                             import actually resolving (factory.py). Mode-
                             invariant: V2EngineOrchestrator is the SHARED
                             engine-build spine for batch, paper AND live
                             (paper_run_handler.py / batch_rerun.py module
                             docstrings both cite it explicitly).
  param_schema           -- PARAM_SCHEMA_REGISTRY membership, keyed by
                             archetype.value (param_schema.py). Mode-
                             invariant: an engine with no schema runs with
                             unvalidated params in every mode alike.
  target_universe_catalog -- specs_for_archetype(archetype) non-empty
                             (target_universe/catalog.py). Mode-invariant:
                             paper_run_handler.py raises ValueError when this
                             is empty; batch-rerun and execution-service's
                             rebalance recommender both read the same
                             catalog.
  allocator_rank          -- a dedicated per-archetype AllocatorArchetype
                             `<VALUE>_RANK` member registered in
                             ALLOCATOR_ARCHETYPE_REGISTRY (portfolio_
                             allocator/archetypes.py). NEVER reported
                             not_ready on absence -- 8 of AllocatorArchetype's
                             16 members are GENERIC (FIXED/PNL_WEIGHTED/...)
                             and legitimately apply to any archetype; static
                             analysis cannot tell whether a given archetype's
                             live/paper client config actually points at a
                             generic allocator instead. Absence is reported
                             `unverified`, not `not_ready` -- this is a
                             deliberate departure from the readiness-state-
                             dump proxy asymmetry (documented here, not
                             there, because it's a genuinely different shape
                             of evidence, not an oversight).
  batch_dispatch (BATCH)  -- STRATEGY_TYPE_TO_SLOT reverse-lookup
                             (archetype_slot_resolver.py) -- the
                             `--operation batch` CLI path. A miss here is
                             `unverified`, not `not_ready`: batch_rerun.py's
                             separate paper-manifest-replay path (same
                             machinery as PAPER's dispatch below) can also
                             satisfy batch for the DeFi carry/yield family,
                             and this check cannot cleanly confirm that
                             second path -- see paper_dispatch.
  paper_dispatch (PAPER)  -- membership in one of paper_run_handler.py's 9
                             named tick-loader frozensets. A miss is a DATED
                             AGENT AUDIT (2026-08-19): read paper_run_handler.py
                             directly -- an archetype absent from all 9 sets
                             falls through to a silent generic perp-basis
                             loader (~line 2239) that assumes
                             `perp_venue`/`perp_instrument` config keys
                             exist. Not proven broken (may be intentionally
                             generic), not proven working either -- flagged
                             `unverified` with the audit citation rather than
                             guessed either way.
  live_topology_gate (LIVE) -- topology_enforcement.load_topology_requirements
                             (archetype.value) resolving cleanly. A real
                             gate: service_entry.py's
                             `_enforce_archetype_topology_from_env` calls
                             this unconditionally at live boot, and
                             FileNotFoundError/ValueError there crashes boot
                             -- a missing/malformed archetype doc is genuine
                             `not_ready` for live, not a proxy.

LIVE mode's per-archetype dispatch below the shared orchestrator (i.e.
whatever cascade_subscriber.py itself does with an already-built engine
instance) was NOT independently traced in the 2026-08-19 research pass this
module is built from -- grepping cascade_subscriber.py and service_entry.py
for StrategyArchetype/ARCHETYPE_ENGINE_REGISTRY/STRATEGY_TYPE_TO_SLOT found
zero references, consistent with live reusing the shared engine_factory leg
above and adding no further per-archetype registry of its own, but this is
an absence-of-evidence conclusion, not a positive confirmation. Recorded
here as a standing DATED AGENT AUDIT note rather than silently assumed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

VerdictState = Literal["ready", "not_ready", "unverified"]

# Every dated agent-audit note in this module is stamped with the date the
# underlying source was actually read -- re-date it (and re-verify the
# claim) if the cited source file changes materially after this date.
AGENT_AUDIT_DATE = "2026-08-19"

LIVE_DISPATCH_AGENT_AUDIT_NOTE: str = (
    f"AGENT AUDIT ({AGENT_AUDIT_DATE}): cascade_subscriber.py and service_entry.py were grepped for "
    "StrategyArchetype/ARCHETYPE_ENGINE_REGISTRY/STRATEGY_TYPE_TO_SLOT/V2EngineOrchestrator references and none "
    "were found -- consistent with live reusing engine_factory's shared V2EngineOrchestrator spine (as "
    "paper_run_handler.py and batch_rerun.py's own module docstrings claim for live) and adding no further "
    "per-archetype registry of its own, but this is an absence-of-evidence read, not a positive confirmation. "
    "A future increment should read cascade_subscriber.py in full to confirm."
)


@dataclass(frozen=True)
class Verdict:
    state: VerdictState
    evidence: str


# ---------------------------------------------------------------------------
# Mode-invariant hooks
# ---------------------------------------------------------------------------
def engine_factory(archetype_value: str, in_registry: bool, resolves: bool, resolve_error: str | None) -> Verdict:
    """ARCHETYPE_ENGINE_REGISTRY membership -- the master gate for all 3 modes."""
    if not in_registry:
        return Verdict("not_ready", "absent from factory.ARCHETYPE_ENGINE_REGISTRY -- no v2 engine class at all")
    if not resolves:
        return Verdict(
            "not_ready",
            f"present in ARCHETYPE_ENGINE_REGISTRY but the lazy import/getattr failed: {resolve_error} "
            "-- registered but broken",
        )
    return Verdict("ready", "ARCHETYPE_ENGINE_REGISTRY entry present and the engine class resolves")


def param_schema(archetype_value: str, has_schema: bool, is_baselined_gap: bool) -> Verdict:
    """PARAM_SCHEMA_REGISTRY membership, keyed by archetype.value."""
    if has_schema:
        return Verdict("ready", "PARAM_SCHEMA_REGISTRY entry present")
    if is_baselined_gap:
        return Verdict(
            "not_ready",
            "no PARAM_SCHEMA_REGISTRY entry -- a known, tracked gap in param_schema.py's "
            "_SCHEMA_COVERAGE_BASELINE_MISSING_SCHEMA shrinking ratchet (not a new regression)",
        )
    return Verdict(
        "not_ready",
        "no PARAM_SCHEMA_REGISTRY entry, and NOT in the baselined-gap set -- a NEW regression per "
        "param_schema.check_archetype_schema_coverage()",
    )


def target_universe_catalog(archetype_value: str, spec_count: int) -> Verdict:
    """specs_for_archetype(archetype) non-empty -- the real instance catalog paper/batch/execution read."""
    if spec_count > 0:
        return Verdict("ready", f"target_universe.specs_for_archetype() returns {spec_count} instance spec(s)")
    return Verdict(
        "not_ready",
        "target_universe.specs_for_archetype() returns zero specs -- paper_run_handler.py raises ValueError "
        "on this condition; no rollout instance exists for this archetype in any mode",
    )


def allocator_rank(archetype_value: str, dedicated_rank_member: str | None) -> Verdict:
    """Dedicated `<VALUE>_RANK` AllocatorArchetype member. NEVER not_ready -- see module docstring."""
    if dedicated_rank_member is not None:
        return Verdict(
            "ready",
            f"AllocatorArchetype.{dedicated_rank_member} registered in ALLOCATOR_ARCHETYPE_REGISTRY "
            "(dedicated per-archetype rank allocator)",
        )
    return Verdict(
        "unverified",
        f"no AllocatorArchetype.{archetype_value}_RANK member -- may legitimately rely on one of the 8 generic "
        "allocators (FIXED/PNL_WEIGHTED/SHARPE_WEIGHTED/RISK_PARITY/KELLY/MIN_CVAR/REGIME_AWARE/MANUAL); which "
        "one is actually configured per venue/client is not statically derivable from this registry",
    )


# ---------------------------------------------------------------------------
# Mode-specific hooks
# ---------------------------------------------------------------------------
def batch_dispatch(archetype_value: str, in_slot_resolver: bool) -> Verdict:
    """STRATEGY_TYPE_TO_SLOT reverse-lookup -- the `--operation batch` CLI path."""
    if in_slot_resolver:
        return Verdict(
            "ready",
            "a STRATEGY_TYPE_TO_SLOT entry resolves to this archetype -- batch_handler.py's "
            "--operation batch CLI path can dispatch it",
        )
    return Verdict(
        "unverified",
        "no STRATEGY_TYPE_TO_SLOT entry resolves to this archetype -- batch_rerun.py's separate "
        "paper-manifest-replay path (shared machinery with PAPER's dispatch leg) may still cover it; not "
        "independently confirmable by a clean registry lookup",
    )


def paper_dispatch(archetype_value: str, in_named_frozenset: bool, frozenset_name: str | None) -> Verdict:
    """Membership in one of paper_run_handler.py's 9 named tick-loader frozensets."""
    if in_named_frozenset:
        return Verdict(
            "ready",
            f"explicit tick-loader dispatch clause in paper_run_handler.py ({frozenset_name}) covers this archetype",
        )
    return Verdict(
        "unverified",
        f"AGENT AUDIT ({AGENT_AUDIT_DATE}): no archetype-specific tick-loader dispatch clause in "
        "paper_run_handler.py's 9 named frozensets -- falls through to the generic perp-basis loader "
        "(~line 2239) which assumes perp_venue/perp_instrument config keys exist. Not proven broken (may be "
        "intentionally generic for non-DeFi-carry archetypes) and not proven working -- verify manually before "
        "relying on paper mode for this archetype.",
    )


def live_topology_gate(archetype_value: str, resolves: bool, error: str | None) -> Verdict:
    """topology_enforcement.load_topology_requirements() resolving -- service_entry.py calls this
    unconditionally at live boot; a failure here crashes boot, so it's a real gate, not a proxy."""
    if resolves:
        return Verdict(
            "ready",
            "topology_enforcement.load_topology_requirements() resolves the archetype doc's "
            f"topology_requirements frontmatter cleanly. {LIVE_DISPATCH_AGENT_AUDIT_NOTE}",
        )
    return Verdict(
        "not_ready",
        f"topology_enforcement.load_topology_requirements() fails: {error} -- "
        "service_entry.py's _enforce_archetype_topology_from_env calls this unconditionally at live boot, "
        "so this crashes live startup for this archetype today",
    )


LEG_ORDER_MODE_INVARIANT: tuple[str, ...] = (
    "engine_factory",
    "param_schema",
    "target_universe_catalog",
    "allocator_rank",
)
MODE_SPECIFIC_LEG: dict[str, str] = {
    "BATCH": "batch_dispatch",
    "PAPER": "paper_dispatch",
    "LIVE": "live_topology_gate",
}


def rollup(legs: dict[str, Verdict]) -> Verdict:
    """Same policy as readiness-state-dump's checks.rollup(): any not_ready dominates; all-ready is ready;
    otherwise (no failures, some unverified) is unverified."""
    states = {v.state for v in legs.values()}
    if "not_ready" in states:
        failing = sorted(k for k, v in legs.items() if v.state == "not_ready")
        return Verdict("not_ready", f"failing legs: {failing}")
    if states == {"ready"}:
        return Verdict("ready", "all legs ready")
    unverified = sorted(k for k, v in legs.items() if v.state == "unverified")
    return Verdict("unverified", f"no failing legs, but unverified: {unverified}")
