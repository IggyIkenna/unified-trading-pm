---
doc_type: plan
title: >-
  Strategy-service centralization fixes — DeFi position-risk reads, venue-literal audit, config-loader unification
summary: >-
  Executes the fix work three issue docs from a same-day audit found: DeFi-leverage archetypes' liquidation
  kill-gate reads an ad-hoc, never-populated generic feature key instead of the correct (but unwired) centralized
  module; venue eligibility is hardcoded per-literal outside one family; two GCS config-loader path conventions
  diverge for the same lookup. Genuine judgment calls stay [OPERATOR]-tagged and non-dispatchable; everything else
  is bounded, symbol-referenced AGENT work. `sequential: true` because several todos have a real chain (route the
  live feed, then switch the archetypes onto it, then extend the data model) — a deliberate choice given the
  correctness stakes (this is live liquidation-risk gating), not a reflexive default.
status: active
nature: process
asset_group: [defi]
stage: [execution]
repos: [strategy-service, execution-service, features-service, unified-api-contracts]
scope: [engineer]
tags: [defi, risk, centralization, health-factor, venue-eligibility, config-loader, architecture]
related:
  [
    /plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md,
    /plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md,
    /plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md,
    /codex/04-architecture/defi-position-risk-centralization.md,
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
  ]
created: 2026-08-16
last_updated: "2026-08-16"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: []
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-16. Operator direction: audit findings must resolve into tracked plan todos, not sit
  passive in issue docs — per this workspace's own findings-triage rule ("issue resolves to folded-in-plan/AO-scope/
  operator-gated, never passive"). Operator confirmed AO-dispatched, one wrapper plan.
context_scope:
  [
    /codex/04-architecture/defi-position-risk-centralization.md,
    /plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md,
    /plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md,
  ]
---

# Strategy-service centralization fixes

Full findings, root cause, and evidence for every todo below live in the three source issue docs (linked in
`related`) — this plan is the execution surface, not a duplicate of the analysis.

- [ ] [OPERATOR] P0. Decide the callable-path fix shape (in-process function vs. a shared helper both
      strategy-service and execution-service import, keyed by wallet/client) for reading DeFi position-risk data
      from `engine/strategies/v2/*`. Details:
      [defi_leverage_archetypes_health_factor_wrong_source_2026_08_16](/plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md).
- [ ] [BACKEND] P0. Route execution-service's `HealthFactorMonitor`'s live per-wallet Aave data into
      `DeFiHealthAggregator`'s state via `update_wallet_health_from_lending` — not a new poller, not the stub
      `AavePositionAdapter`. Done-when: the aggregator's state reflects real position data after a live/paper run,
      verified by reading it back.
- [ ] [BACKEND] P0. Switch `staked_basis.py`'s `_validate_lst_margin_slot` and `recursive_staked.py`'s entry gate
      plus `_check_family2_health_kill` off `features.get("health_factor")` onto the centralized source the prior
      todo wired. Done-when: neither file reads `features.get("health_factor")` anymore, both call the centralized
      source, and existing archetype tests stay green.
- [ ] [BACKEND] P1. Switch `arbitrage_structural/liquidation_capture.py`'s health-factor gate and
      `mev/liquidation_bundle.py`'s `liq_candidate_health_factor_*` gate to the same centralized source
      (candidate-wallet-parameterized, not client-scoped — a different call shape from the prior todo). Done-when:
      neither reads an ad-hoc `features.get` key for this purpose anymore.
- [ ] [OPERATOR] P1. Decide `liquidation_proximity_circuit.py`'s fate — wire it in as the shared gate the four
      archetypes above call, or retire it. It currently has zero callers anywhere.
- [ ] [BACKEND] P1. Extend `DeFiAggregatedHealth`/`ProtocolHealthBreakdown` with LTV, borrow-capacity, and
      liquidation-price fields (or unify with `PositionHealthSnapshot`'s fields); fix `positions_health.py`'s
      `MarginModel.AAVE_V3`-hardcoded liquidation-threshold lookup to resolve per-position protocol instead.
- [ ] [OPERATOR] P2. Decide `AavePositionAdapter` (`aave.py`)'s fate — delete it or finish it as a canonical feed —
      now that a working live-poller route exists via the earlier todos.
- [ ] [BACKEND] P2. Fix `_process_health_factor()`'s misleading docstring in
      `features-service/features_service/onchain/engine/orchestrator.py` to describe the generic protocol-level
      rate-index data it actually reads, not the per-wallet Aave polling it currently claims.
- [ ] [BACKEND] P2. Unify the two divergent GCS config-loader path conventions —
      `ConfigLoader.load_config`'s `configs/{strategy_id}.json` vs. `load_strategy_config_gcs`'s
      `configs/strategies/{strategy_id}.json` — behind one loader, building on `get_strategy_params()`'s existing
      resolution seam. Delete the dead local-YAML `config.py::load_strategy_config` path and its unused
      `load_config` alias. Details:
      [per_client_config_surface_keying_and_missing_axes_2026_08_12](/plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md).
- [ ] [BACKEND] P2. Audit every hardcoded venue literal in `catalog_trading.py`/`catalog_directional.py` against
      each named venue's actual current capabilities (does OKX/Bybit/Hyperliquid/CME/IBKR/etc. genuinely support
      what each row assumes, today) — record findings as a new dated section in
      [venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16](/plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md),
      correcting any drift found. Useful regardless of the next todo's outcome.
- [ ] [OPERATOR] P2. Decide the venue-eligibility generalization shape — extend `venue_capabilities.py` to every
      strategy family, or accept the hardcoded catalog literals (now verified accurate by the prior todo) as
      deliberate. If generalizing, add a regression check so a catalog row whose venue lacks the assumed capability
      fails loudly at build/test time rather than shipping a slot that can't actually trade.
- [ ] [OPERATOR] P2. Design the mode-aware dispatch (batch / live / paper-testnet / paper-live) for the
      centralized DeFi position-risk read, once the earlier routing/switch todos land.
- [ ] [BACKEND] P3. Update
      [defi-position-risk-centralization](/codex/04-architecture/defi-position-risk-centralization.md) from
      "not yet complete" to reflect the landed state, once the earlier BACKEND todos land.

## Progress Log

- **2026-08-16** — Authored from three same-day issue docs per operator direction (AO-dispatched, one wrapper
  plan). `sequential: true` set deliberately given the real chain among the first several todos — not a reflexive
  default. Companion finalize plan:
  [strategy_service_centralization_fixes_finalize_2026_08_16](/plans/active/strategy_service_centralization_fixes_finalize_2026_08_16.md).
