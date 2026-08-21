---
doc_type: issue
title: Wire Pendle into execution-service's real dispatch (currently unreachable — no dedicated remediation doc, unlike karak/symbiotic)
summary: >-
  Pendle is a registered, real DeFi venue (UAC `venue_adapter_keys.py`, `capability_declarations/_defi.py`, YIELD
  protocol class) with a working simulation-only connector (`execution_service/defi_execution/protocols/pendle.py`,
  PT/YT yield-tokenization via an SY-wrap primitive flow) — but it is never instantiated in `DeFiAdapter` or any
  other dispatcher, and absent from the UAC SIT invariant's own `DEFI_VENUE_TO_CONNECTOR_CLASS`/
  `DEFI_VENUE_TO_GATE_MARKER` maps. It does not currently gate
  `test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions` because no strategy-service
  archetype declares Pendle in its `venue_universe` yet — but the moment one does, this becomes a live blocker
  exactly like karak/symbiotic were. Splitting this out so Pendle has the same dedicated-doc ownership karak and
  symbiotic already have, per `/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md` L361.
status: open
nature: issue
asset_group: [defi] # corrected 2026-08-19 (ag-closeout-audit cross-cutting, Phase 1 Workflow) -- was [cross-cutting, defi]; Pendle is a single DeFi venue execution-wiring gap, not multi-AG
stage: [strategy, execution]
repos: [execution-service, unified-api-contracts, strategy-service]
scope: [engineer]
assigned_vm: NA
execution_scope: local-only
tags: [defi, pendle, venue-onboarding, execution-wiring]
priority: P2
source: agent-discovered-2026-08-16
parent_epic: security_and_cross_cutting_master
related:
  [
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/active/issues/karak_decommission_2026_08_16.md,
    /plans/archive/issues/symbiotic_venue_onboarding_2026_08_16.md,
  ]
created: 2026-08-16
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    execution-service/execution_service/defi_execution/protocols/pendle.py,
    execution-service/execution_service/adapters/defi_adapter.py,
    unified-api-contracts/tests/test_execution_service_venue_coverage_cascade_invariant.py,
  ]
---

# Wire Pendle into execution-service's real dispatch

## Why (measured 2026-08-16)

- Pendle IS a real, registered venue — not a stub. `unified-api-contracts/registry/venue_adapter_keys.py` and
  `registry/capability_declarations/_defi.py` (`"pendle": _ProtocolCapability(venue_prefix="PENDLE",
  protocol_class=ProtocolClass.YIELD, ...)`) both declare it. `execution_service/defi_execution/protocols/pendle.py`
  has a real, documented PT/YT yield-tokenization write path (SY-wrap primitive flow, requires per-market
  `config["pendle_markets"][market_id]` addresses — deliberately does not hand-roll Pendle's zap/swap calldata blob).
- Per `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`'s reachability audit, Pendle is one of 20
  protocol connector classes never instantiated anywhere in execution-service outside its own module and tests —
  `DeFiAdapter`, `V2InstructionRouter`, and `RecursiveLoopOrchestrator` all skip it. Tier-2/simulation-only per that
  same doc's write-path audit — accepts `is_live` but never reads it.
- Zero references in `execution-service/execution_service/adapters/defi_adapter.py` (confirmed by direct grep,
  2026-08-16) — unlike Symbiotic, which was wired into that dispatcher's `_dispatch_defi_operation` this same day.
  Zero entry in the UAC SIT invariant test's own `DEFI_VENUE_TO_CONNECTOR_CLASS`/`DEFI_VENUE_TO_GATE_MARKER` maps
  (`unified-api-contracts/tests/test_execution_service_venue_coverage_cascade_invariant.py`) — confirmed by direct
  grep, same session.
- **Not currently gating the SIT invariant**: `grep -rl "pendle" strategy-service/strategy_service/engine/strategies/v2/`
  returns zero hits — no archetype's `venue_universe` names Pendle today, so
  `test_strategy_defi_venues_have_reachable_execution_adaptor_no_new_regressions` doesn't see it as a strategy-declared
  DeFi venue needing a reachable executor. This is why `archetype_feature_groups.py` (L228) shipped cleanly once
  Symbiotic was wired and Karak was scoped out of the cascade by its own decommission decision — Pendle was never in
  the failing set. **This is a latent gap, not an active blocker** — it becomes one the moment a strategy archetype
  adds Pendle to its `venue_universe`.
- Documented as a real venue in 3 codex docs (`instrument-pipeline-defi.md`, `defi-data-type-taxonomy.md`,
  `defi-venue-protocol-catalogue.md`) — not a speculative venue, just one whose execution wiring lagged its
  registry/data-pipeline presence, the same shape Symbiotic was in before its own onboarding doc closed the gap.

## What's needed

- [x] ✅ [AGENT] P2. **Wire `PendleConnector` into `DeFiAdapter`** — **execution-service@0c0b6a1a40**. Facade export,
      constructor param + `ensure_connected` entry, `_execute_pendle_lending` handler, route-table entry, and
      real construction in `live_execution_handler._build_defi_adapter`. **LEND only**: `withdraw()` is
      simulation-only by this connector's own docstring, so routing a live WITHDRAW there would fabricate a
      success; `PENDLE_OPERATIONS` is a strict subset of `LENDING_OPERATIONS` and the other three operations
      raise "Unsupported lending venue" until real `YT.redeemPY()` redemption is implemented.
- [ ] [AGENT] P2. **Implement Pendle PT redemption (`withdraw`) for real**, then widen `PENDLE_OPERATIONS` to
      include WITHDRAW in the SAME change. Needs the transfer-then-call pattern plus pre- vs post-maturity
      branching. Until then the operation is refused rather than simulated — do not widen the set first.
- [ ] [AGENT] P2. **Add `"pendle": "PendleConnector"` to `DEFI_VENUE_TO_CONNECTOR_CLASS`** and the matching
      gate-marker comment to `DEFI_VENUE_TO_GATE_MARKER` in
      `unified-api-contracts/tests/test_execution_service_venue_coverage_cascade_invariant.py` — the same two-map
      requirement that blocked Symbiotic's cascade invariant for most of 2026-08-16 (see the 16-confirmation flap log
      in `venue_readiness_and_registry_hardening_2026_08_16.md`'s Progress Log). Do this BEFORE any strategy
      archetype adds Pendle to its `venue_universe`, or the invariant fails immediately on that change.
- [ ] [AGENT] P3. **Resolve `config["pendle_markets"][market_id]` addresses** (SY/YT/PT/underlying-token contracts
      per market) before any live construction — the connector's own docstring already states unconfigured markets
      return an explicit error, so this is a config-population task, not a code-correctness one.
- [ ] [AGENT] P3. **Decide whether Pendle belongs in any strategy archetype's `venue_universe`** — it is currently
      absent from all of them; if no archetype needs it, the P2 items above are still worth doing (closes the
      SIT-invariant latent gap pre-emptively) but drop to P3.

## Progress Log

- **2026-08-16 (slot-29)**: issue authored per
  `/plans/active/venue_readiness_and_registry_hardening_2026_08_16.md` L361, splitting Pendle out from its 7
  incidental mentions (karak decommission doc, venue-coverage asymmetry doc, and 5 others) into its own dedicated
  doc, matching karak/symbiotic's pattern. No code changed this entry — scoping only.
- **na-eligibility-audit 2026-08-16** [body-hash:421769a9fe30ba85]: KEEP-NA, valid — Freshly authored issue doc (created TODAY, 2026-08-16, zero code changed yet -- doc's own Progress Log: 'issue authored...No code changed this entry -- scoping only'), explicitly split out of parent venue_readiness_and_registry_hardening_2026_08_16.md (also assigned_vm:NA) at that parent's own explicit direction (L361), matching the SAME doc-shape/pattern its two siblings use: karak_decommission_2026_08_16.md (status:open, assigned_vm:NA) and the now-ARCHIVED symbiotic_venue_onboarding_2026_08_16.md (assigned_vm:NA) -- both confirmed via direct grep this session.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
