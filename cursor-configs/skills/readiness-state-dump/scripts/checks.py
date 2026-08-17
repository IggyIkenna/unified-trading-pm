#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Per-leg readiness checks for the readiness-state-dump skill.

Readiness is DERIVED, never declared (operator ruling 2026-08-16,
/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md). Every
function here returns a Verdict whose state is one of:

  "ready"      -- a real machine check ran and passed.
  "not_ready"  -- a real machine check ran and failed (a genuine negative is
                  always reportable, even where a POSITIVE can't be confirmed
                  -- "structurally cannot" is itself real evidence).
  "unverified" -- no real check exists yet, OR the only signal available is a
                  CAPABILITY proxy (the code path/registry entry exists) that
                  does not confirm the property actually being asked about
                  (real operation / a verified working rail / observed
                  consumption). Per CLAUDE.md: "a row count, an exit code, a
                  green test, 'the connector exists' are all proxies" -- a
                  proxy is never allowed to produce a silent "ready".

This asymmetry (proxy-presence -> unverified, proxy-absence -> not_ready) is
deliberate: absence of a capability is still hard evidence of non-readiness,
but presence of a capability is not hard evidence of operation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

VerdictState = Literal["ready", "not_ready", "unverified"]


@dataclass(frozen=True)
class Verdict:
    state: VerdictState
    evidence: str


# ---------------------------------------------------------------------------
# Step 1 -- Declared (mode-invariant: a registration fact, not a per-mode one)
# ---------------------------------------------------------------------------
def declared(venue: str, declared_venues: frozenset[str]) -> Verdict:
    if venue in declared_venues:
        return Verdict("ready", "present in UAC VENUE_DATA_TYPE_CAPABILITIES")
    return Verdict("not_ready", "absent from VENUE_DATA_TYPE_CAPABILITIES")


# ---------------------------------------------------------------------------
# instruments-service -- reference data resolves (Layer-1 expected_tuples)
# ---------------------------------------------------------------------------
def instruments_service_refdata(layer1_venue_block: dict | None) -> Verdict:
    if layer1_venue_block is None:
        return Verdict(
            "unverified",
            "no Layer-1 by_venue entry for this venue in coverage.json "
            "(this venue's asset_group may not have been measured, or the venue is genuinely absent from the IS catalogue)",
        )
    expected = layer1_venue_block.get("expected_tuples", 0)
    if expected > 0:
        return Verdict("ready", f"Layer-1 expected_tuples={expected} (IS catalogue enumerated real instruments for this venue)")
    return Verdict("not_ready", "Layer-1 expected_tuples=0 for this venue (IS catalogue enumerated nothing)")


# ---------------------------------------------------------------------------
# market-tick-data-service -- captured for every observed declared data_type
# ---------------------------------------------------------------------------
def mtds_captured(venue_data_type_cells: list[tuple[str, int, int]]) -> Verdict:
    """``venue_data_type_cells``: list of (data_type, captured_count, reachable_denominator)."""
    if not venue_data_type_cells:
        return Verdict("unverified", "no coverage.json shard cells observed for this venue")
    missing = [dt for dt, captured, denom in venue_data_type_cells if captured == 0 and denom > 0]
    if not missing:
        return Verdict("ready", f"captured>0 for all {len(venue_data_type_cells)} observed data_types")
    return Verdict("not_ready", f"zero captured for data_types with a non-zero denominator: {sorted(missing)}")


# ---------------------------------------------------------------------------
# market-data-processing-service -- raw shard consumed into something derived
# (MDPS_DERIVABLE_DATA_TYPES membership is a CAPABILITY proxy, not observed
# consumption -- see module docstring on the proxy-asymmetry policy.)
# ---------------------------------------------------------------------------
def mdps_consumed(venue_data_types: frozenset[str], mdps_derivable: frozenset[str]) -> Verdict:
    if not venue_data_types:
        return Verdict("unverified", "no declared data_types for this venue")
    derivable = venue_data_types & mdps_derivable
    if not derivable:
        return Verdict("not_ready", f"none of this venue's data_types are in MDPS_DERIVABLE_DATA_TYPES: {sorted(venue_data_types)}")
    return Verdict(
        "unverified",
        f"data_types derivable by MDPS per MDPS_DERIVABLE_DATA_TYPES: {sorted(derivable)} "
        "(capability only -- real per-shard MDPS manifest consumption is not read by this pass)",
    )


# ---------------------------------------------------------------------------
# features-service -- does a feature group consume this venue's data
# (reuses unified_api_contracts.internal.architecture_v2.venue_strategy_consumability
#  -- FEATURE_REQUIRED_INPUTS is an authoritative SSOT declaration, not a proxy,
#  so this is a real ready/not_ready check, same tier as `declared` above.)
# ---------------------------------------------------------------------------
def features_consumed(venue_data_types: frozenset[str], orphaned: frozenset[str]) -> Verdict:
    if not venue_data_types:
        return Verdict("unverified", "no declared data_types for this venue")
    consumed = venue_data_types - orphaned
    if consumed:
        note = f"; {len(orphaned)}/{len(venue_data_types)} data_types orphaned" if orphaned else ""
        return Verdict("ready", f"consumed by >=1 feature_group's FEATURE_REQUIRED_INPUTS: {sorted(consumed)}{note}")
    return Verdict("not_ready", f"all {len(venue_data_types)} data_types orphaned -- no feature_group requires any of them")


# ---------------------------------------------------------------------------
# strategy-service -- archetype registration half (real SSOT: ARCHETYPE_FEATURE_GROUPS)
# ---------------------------------------------------------------------------
def strategy_archetype_registered(satisfying_archetype_names: frozenset[str]) -> Verdict:
    if satisfying_archetype_names:
        return Verdict("ready", f"satisfying archetypes: {sorted(satisfying_archetype_names)}")
    return Verdict("not_ready", "no declared archetype's full FEATURE_REQUIRED_INPUTS set is satisfiable from this venue's data_types")


# ---------------------------------------------------------------------------
# strategy-service -- position-adapter half, mode-aware
# (reuses strategy_service.position.position_interface.capabilities.
#  position_read_mode_availability -- a real, audited per-(venue,mode) table.)
# ---------------------------------------------------------------------------
def strategy_position_adapter(venue: str, mode: str, mode_status: str | None) -> Verdict:
    if mode_status is None:
        return Verdict("unverified", f"position_read_mode_availability({venue!r}) could not be resolved for mode={mode}")
    if mode_status == "deployed":
        return Verdict("ready", f"position_read_mode_availability({venue!r}).{mode.lower()} = deployed")
    if mode_status == "wired":
        return Verdict("unverified", f"position_read_mode_availability({venue!r}).{mode.lower()} = wired (code path exists, unverified for this venue)")
    return Verdict("not_ready", f"position_read_mode_availability({venue!r}).{mode.lower()} = none")


def strategy_leg(archetype_verdict: Verdict, adapter_verdict: Verdict) -> Verdict:
    """AND of both halves -- 'both, not either' per the task's explicit framing."""
    states = {archetype_verdict.state, adapter_verdict.state}
    if "not_ready" in states:
        return Verdict("not_ready", f"archetype={archetype_verdict.state} ({archetype_verdict.evidence}); position_adapter={adapter_verdict.state} ({adapter_verdict.evidence})")
    if states == {"ready"}:
        return Verdict("ready", f"archetype={archetype_verdict.evidence}; position_adapter={adapter_verdict.evidence}")
    return Verdict("unverified", f"archetype={archetype_verdict.state}; position_adapter={adapter_verdict.state}")


# ---------------------------------------------------------------------------
# execution-service -- transfers (VENUE_WALLET_CAPABILITIES presence is a
# CAPABILITY proxy: it declares wallet structure/custody, not a proven rail.)
# ---------------------------------------------------------------------------
def execution_transfers(venue: str, wallet_capability_venues: frozenset[str]) -> Verdict:
    if venue in wallet_capability_venues:
        return Verdict("unverified", f"{venue} present in VENUE_WALLET_CAPABILITIES (wallet structure declared -- a working rail is not independently verified by this pass)")
    return Verdict("not_ready", f"{venue} absent from VENUE_WALLET_CAPABILITIES -- no transfer rail declared")


# ---------------------------------------------------------------------------
# execution-service -- instruction adaptor coverage (no check wired yet)
# ---------------------------------------------------------------------------
def execution_instruction() -> Verdict:
    return Verdict(
        "unverified",
        "no per-venue InstructionActionV2-adaptor-coverage check is wired in this pass -- "
        "execution-service/execution_service/v2/policy_resolver.py is the real registry a future increment should read",
    )


LEG_ORDER: tuple[str, ...] = (
    "declared",
    "instruments_service",
    "market_tick_data",
    "market_data_processing",
    "features",
    "strategy",
    "execution_transfers",
    "execution_instruction",
)


def rollup(legs: dict[str, Verdict]) -> Verdict:
    states = {v.state for v in legs.values()}
    if "not_ready" in states:
        failing = sorted(k for k, v in legs.items() if v.state == "not_ready")
        return Verdict("not_ready", f"failing legs: {failing}")
    if states == {"ready"}:
        return Verdict("ready", "all legs ready")
    unverified = sorted(k for k, v in legs.items() if v.state == "unverified")
    return Verdict("unverified", f"no failing legs, but unverified: {unverified}")
