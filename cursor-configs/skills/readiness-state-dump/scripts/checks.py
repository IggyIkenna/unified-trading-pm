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
            "no Layer-1 by_venue entry for this venue in coverage.json (this venue's asset_group may not have "
            "been measured, or the venue is genuinely absent from the IS catalogue)",
        )
    expected = layer1_venue_block.get("expected_tuples", 0)
    if expected > 0:
        return Verdict(
            "ready",
            f"Layer-1 expected_tuples={expected} (IS catalogue enumerated real instruments for this venue)",
        )
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
# market-tick-data-service -- LIVE feed leg (system_readiness_master.md W1,
# 2026-08-19 P0: market data is a two-feed question, batch + live, not three
# -- paper always consumes the live feed per paper-batch-live-reconciliation.md
# § 0, so this SAME verdict is reused for both the PAPER and LIVE rows; only
# BATCH keeps the separate coverage.json-observed verdict above.
# WS_FEED_CONNECTOR_FACTORIES membership is a CAPABILITY proxy: a registered
# connector class doesn't confirm the live feed is actually flowing.)
# ---------------------------------------------------------------------------
def mtds_live_feed(venue: str, live_registered_venues: frozenset[str]) -> Verdict:
    if venue in live_registered_venues:
        return Verdict(
            "unverified",
            f"{venue} present in MTDS WS_FEED_CONNECTOR_FACTORIES (a live WSFeedConnector is registered -- "
            "actual data flow is not independently verified by this pass)",
        )
    return Verdict("not_ready", f"{venue} absent from MTDS WS_FEED_CONNECTOR_FACTORIES -- no live connector wired")


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
        return Verdict(
            "not_ready",
            f"none of this venue's data_types are in MDPS_DERIVABLE_DATA_TYPES: {sorted(venue_data_types)}",
        )
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
        return Verdict(
            "ready",
            f"consumed by >=1 feature_group's FEATURE_REQUIRED_INPUTS: {sorted(consumed)}{note}",
        )
    return Verdict(
        "not_ready",
        f"all {len(venue_data_types)} data_types orphaned -- no feature_group requires any of them",
    )


# ---------------------------------------------------------------------------
# strategy-service -- archetype registration half (real SSOT: ARCHETYPE_FEATURE_GROUPS)
# ---------------------------------------------------------------------------
def strategy_archetype_registered(satisfying_archetype_names: frozenset[str]) -> Verdict:
    if satisfying_archetype_names:
        return Verdict("ready", f"satisfying archetypes: {sorted(satisfying_archetype_names)}")
    return Verdict(
        "not_ready",
        "no declared archetype's full FEATURE_REQUIRED_INPUTS set is satisfiable from this venue's data_types",
    )


# ---------------------------------------------------------------------------
# strategy-service -- position-adapter half, mode-aware
# (reuses strategy_service.position.position_interface.capabilities.
#  position_read_mode_availability -- a real, audited per-(venue,mode) table.)
# ---------------------------------------------------------------------------
def strategy_position_adapter(venue: str, mode: str, mode_status: str | None) -> Verdict:
    base_ref = f"position_read_mode_availability({venue!r})"
    if mode_status is None:
        return Verdict("unverified", f"{base_ref} could not be resolved for mode={mode}")
    ref = f"{base_ref}.{mode.lower()}"
    if mode_status == "deployed":
        return Verdict("ready", f"{ref} = deployed")
    if mode_status == "wired":
        return Verdict("unverified", f"{ref} = wired (code path exists, unverified for this venue)")
    return Verdict("not_ready", f"{ref} = none")


# ---------------------------------------------------------------------------
# strategy-service -- archetype CODE-completeness half (W1's archetype capability
# axis across batch/paper/live). Distinct from strategy_archetype_registered above:
# that one asks "which archetypes can this VENUE'S DATA satisfy"
# (satisfying_archetypes); this one asks "of those, is any actually WIRED for this
# mode" -- factory registration, param schema, target-universe catalog, allocator
# rank and the mode-specific dispatch hook.
#
# Consumes the archetype-code-completeness skill's own output rather than
# re-deriving it (the plan's explicit instruction), so the two dumps can never
# disagree about whether an archetype is code-complete.
#
# The composition is a real AND with teeth: a venue whose only data-satisfiable
# archetype is not wired for LIVE is not live-ready, however good its data is.
# ---------------------------------------------------------------------------
def strategy_archetype_code_complete(
    satisfying_archetype_names: frozenset[str],
    mode: str,
    archetype_states: dict[str, dict[str, str]] | None,
) -> Verdict:
    """``archetype_states``: {MODE: {archetype_name: state}} from the archetype dump."""
    if archetype_states is None:
        return Verdict("unverified", "archetype code-completeness probe unavailable -- no per-mode wiring check ran")
    by_mode = archetype_states.get(mode)
    if not by_mode:
        return Verdict("unverified", f"archetype code-completeness probe returned no rows for mode={mode}")
    if not satisfying_archetype_names:
        return Verdict(
            "not_ready",
            "no archetype's FEATURE_REQUIRED_INPUTS is satisfiable from this venue, so no archetype can run here "
            "regardless of how complete its code is",
        )

    code_ready = sorted(a for a in satisfying_archetype_names if by_mode.get(a) == "ready")
    if code_ready:
        return Verdict("ready", f"data-satisfiable AND code-complete for mode={mode}: {code_ready}")

    detail = {a: by_mode.get(a, "unknown-to-probe") for a in sorted(satisfying_archetype_names)}
    if any(v == "unknown-to-probe" for v in detail.values()):
        return Verdict(
            "unverified",
            f"no satisfying archetype is code-complete for mode={mode}, and at least one is absent from the "
            f"archetype dump entirely: {detail}",
        )
    return Verdict(
        "not_ready",
        f"every archetype this venue's data satisfies is incomplete in code for mode={mode}: {detail}",
    )


def strategy_leg(archetype_verdict: Verdict, adapter_verdict: Verdict) -> Verdict:
    """AND of both halves -- 'both, not either' per the task's explicit framing."""
    states = {archetype_verdict.state, adapter_verdict.state}
    if "not_ready" in states:
        return Verdict(
            "not_ready",
            f"archetype={archetype_verdict.state} ({archetype_verdict.evidence}); "
            f"position_adapter={adapter_verdict.state} ({adapter_verdict.evidence})",
        )
    if states == {"ready"}:
        return Verdict("ready", f"archetype={archetype_verdict.evidence}; position_adapter={adapter_verdict.evidence}")
    return Verdict("unverified", f"archetype={archetype_verdict.state}; position_adapter={adapter_verdict.state}")


# ---------------------------------------------------------------------------
# execution-service -- orders / fills / trades / account balance
# (system_readiness_master.md W1, 2026-08-19 P0: the four execution-service-
# owned surfaces in the six-surface readiness table). The one real per-venue
# signal available for all four is execution-service's own order-adapter
# registry (execution_service.trade_execution.factory.get_supported_venues(),
# read via the _execution_order_capability_probe.py subprocess -- BaseCLOBAdapter's
# place_order/get_fills/get_account_state/get_positions are abstract methods,
# so wherever an adapter is registered all four are implemented by
# construction). `orders` additionally layers the UAC capability registry's
# per-env place_order declaration on top, since that is the one operation with
# real mode-aware supported/not-supported data (see the probe's docstring).
# ---------------------------------------------------------------------------
def _execution_probe_row(venue: str, probe: dict[str, dict] | None) -> dict | None:
    if probe is None:
        return None
    return probe.get(venue)


def execution_orders(venue: str, mode: str, probe: dict[str, dict] | None) -> Verdict:
    row = _execution_probe_row(venue, probe)
    if row is None:
        return Verdict("unverified", "execution-service order-capability probe unavailable for this venue")
    if not row.get("adapter_present"):
        return Verdict(
            "not_ready", f"{venue} absent from execution-service get_supported_venues() -- no order adapter registered"
        )
    if mode == "BATCH":
        return Verdict(
            "unverified",
            "order adapter registered, but BATCH never invokes a real adapter (simulated fills) -- no real "
            "check exists for batch order capability",
        )
    env = "testnet" if mode == "PAPER" else "mainnet"
    supported = row.get("place_order", {}).get(env)
    ref = f"UAC validate_operation(place_order, env={env})"
    if supported is True:
        return Verdict("ready", f"{ref} = supported")
    if supported is False:
        return Verdict("not_ready", f"{ref} = NOT supported")
    return Verdict("unverified", f"order adapter registered, but {ref} has no capability declaration")


def _execution_adapter_capability_leg(venue: str, probe: dict[str, dict] | None, real_method: str) -> Verdict:
    """Shared proxy for fills/trades/account_balance -- BaseCLOBAdapter's abstract
    methods are implemented by construction wherever an adapter is registered, so
    adapter presence is the one real (mode-invariant) signal available; presence
    does not confirm the method has ever actually been called against the venue."""
    row = _execution_probe_row(venue, probe)
    if row is None:
        return Verdict("unverified", "execution-service order-capability probe unavailable for this venue")
    if row.get("adapter_present"):
        return Verdict(
            "unverified",
            f"{venue} has a registered execution-service adapter (BaseCLOBAdapter.{real_method}() implemented "
            "by construction) -- real observed operation is not verified by this pass",
        )
    return Verdict(
        "not_ready", f"{venue} absent from execution-service get_supported_venues() -- no adapter, no {real_method}()"
    )


def execution_fills(venue: str, probe: dict[str, dict] | None) -> Verdict:
    return _execution_adapter_capability_leg(venue, probe, "get_fills")


def execution_trades(venue: str, probe: dict[str, dict] | None) -> Verdict:
    # execution-service has no distinct trades-vs-fills method -- get_fills() is
    # the one account-trade-history read; a historical "trades tape" concept
    # exists downstream at the ledger layer (InstructionLedger, UTL
    # ledger/materialize.py), not as a per-venue-mode adapter capability.
    return _execution_adapter_capability_leg(venue, probe, "get_fills")


def execution_account_balance(venue: str, probe: dict[str, dict] | None) -> Verdict:
    return _execution_adapter_capability_leg(venue, probe, "get_account_state")


# ---------------------------------------------------------------------------
# execution-service -- transfers (VENUE_WALLET_CAPABILITIES presence is a
# CAPABILITY proxy: it declares wallet structure/custody, not a proven rail.)
# ---------------------------------------------------------------------------
def execution_transfers(venue: str, wallet_capability_venues: frozenset[str]) -> Verdict:
    if venue in wallet_capability_venues:
        return Verdict(
            "unverified",
            f"{venue} present in VENUE_WALLET_CAPABILITIES (wallet structure declared -- a working rail "
            "is not independently verified by this pass)",
        )
    return Verdict("not_ready", f"{venue} absent from VENUE_WALLET_CAPABILITIES -- no transfer rail declared")


# ---------------------------------------------------------------------------
# execution-service -- instruction-path coverage, REAL and per-venue-per-mode.
#
# WIRED 2026-08-20 -- `execution_service.readiness.instruction_path` (shipped
# execution-service@b70d2edb16 the same day the comment below was written)
# IS the per-venue instruction-path registry that comment said didn't exist:
# a real check reading trade_execution.factory / defi_instruction_routes /
# sports_execution.routing, exactly like execution_orders' UAC capability
# check. See _execution_instruction_path_probe.py for the cross-venv wiring.
#
# `InstructionPathStatus` is three-way per mode: "none" (no handler resolves
# at all -- not_ready), "wired" (a real handler resolves, but not for every
# action this venue routes in the OTHER modes -- e.g. BATCH lacks a
# settlement handler for WITHDRAW/REPAY on a lending venue that routes them
# LIVE -- unverified, a real but incomplete positive, never claimed "ready"),
# "deployed" (a real handler resolves for every action this venue routes --
# ready). This mirrors the module's own CLAIM <= MEASUREMENT stance: "wired"
# is a genuine finding, not a downgrade to hide.
# ---------------------------------------------------------------------------
def execution_instruction(venue: str, mode: str, probe: dict[str, dict] | None) -> Verdict:
    if probe is None:
        return Verdict(
            "unverified",
            "execution-service instruction-path probe unavailable for this venue "
            "(execution_service.readiness.instruction_path)",
        )
    row = probe.get(venue)
    if row is None:
        return Verdict("unverified", "execution-service instruction-path probe returned no row for this venue")
    # Distinguish "the probe measured this mode and it's genuinely none" from "this mode was
    # never asked about" -- InstructionPathAvailability only models batch/paper/live (added
    # 2026-08-20, MANUAL mode): a plain `.get(mode.lower(), "none")` would silently claim a
    # REAL NEGATIVE ("not_ready", a measured route absence) for a mode the probe never had a
    # field for at all, overclaiming past what was measured.
    _absent = object()
    status = row.get(mode.lower(), _absent)
    if status is _absent:
        return Verdict(
            "unverified",
            f"execution-service instruction-path probe has no '{mode.lower()}' field for this venue "
            "(InstructionPathAvailability models batch/paper/live only)",
        )
    # "detail" is always populated -- row came from asdict(InstructionPathAvailability),
    # whose "detail" field always has a real value (default or computed), never absent.
    detail = row["detail"]
    if status == "deployed":
        return Verdict("ready", detail)
    if status == "wired":
        return Verdict("unverified", detail)
    return Verdict("not_ready", detail or "no execution-instruction route resolves for this venue")


# ---------------------------------------------------------------------------
# credentials -- W1's 7th readiness dimension (2026-08-19 addition).
#
# Derived from UAC's OWN declared auth model (SourceCapability.auth_scope /
# auth_environments / supports_testnet / supports_mainnet, plus the per-operation
# required_credential + signing_scheme in operation_details) -- not from a
# hand-written list of which venues "need keys".
#
# The honest split this leg draws:
#   ready       -- the venue declares it needs NO credential for this env
#                  ("none" auth_scope / required_credential). A real fact: there
#                  is nothing to be missing.
#   not_ready   -- the venue structurally does not support this mode's env at all
#                  (e.g. PAPER on a source declaring supports_testnet=False).
#                  Structurally cannot, which is hard evidence.
#   unverified  -- a credential IS declared as required. Whether the secret is
#                  actually present/valid is NOT checked here: that needs a live
#                  GSM read, which this read-only pass deliberately does not do.
#                  This is the BLOCKED-CREDENTIALS state made visible per venue
#                  rather than hidden behind a silent pass.
#
# BATCH deliberately resolves against mainnet: batch capture reads production
# history, and there is no separate "batch env" in the capability model.
# ---------------------------------------------------------------------------
def credentials(venue: str, mode: str, cap: dict[str, object] | None) -> Verdict:
    """``cap``: flattened UAC capability facts for this venue, or None if unresolvable."""
    if cap is None:
        return Verdict(
            "unverified",
            f"no UAC SourceCapability resolves for {venue} -- credential requirement undeclared, not confirmed absent",
        )

    env = "testnet" if mode == "PAPER" else "mainnet"
    supports = bool(cap.get("supports_testnet") if env == "testnet" else cap.get("supports_mainnet"))
    if not supports:
        return Verdict("not_ready", f"{venue} declares supports_{env}=False -- mode={mode} cannot run at all")

    auth_scope = [str(a).lower() for a in (cap.get("auth_scope") or [])]
    required = [str(r).lower() for r in (cap.get("required_credentials") or [])]
    needs = sorted({a for a in auth_scope if a != "none"} | {r for r in required if r != "none"})

    if not needs:
        declared = "auth_scope=['none']" if auth_scope else "no auth_scope declared and no operation requires one"
        return Verdict("ready", f"{venue} requires no credential for env={env} ({declared})")

    env_key = cap.get("auth_environments") or {}
    named = env_key.get("test") if env == "testnet" else env_key.get("prod")
    named_note = f"; auth_environments names {named!r}" if named else "; no auth_environments entry names the secret"
    return Verdict(
        "unverified",
        f"{venue} requires {needs} for env={env}{named_note} -- secret presence/validity is NOT read by this "
        "pass (a live GSM read); declared requirement only",
    )


LEG_ORDER: tuple[str, ...] = (
    "declared",
    "credentials",
    "instruments_service",
    "market_tick_data",
    "market_data_processing",
    "features",
    "strategy",
    "strategy_archetype_code",
    "execution_orders",
    "execution_fills",
    "execution_trades",
    "execution_account_balance",
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
