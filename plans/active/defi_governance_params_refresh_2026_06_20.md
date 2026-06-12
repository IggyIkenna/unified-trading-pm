---
title: "DeFi protocol governance-parameters refresh — event listener → time-versioned parquet → asof-read migration"
parent_epic: defi_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: brand-new
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 9
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/defi_master.md
  - ./defi_onchain_derivable_values_and_date_drift_2026_06_20.md
---

> **Provenance**: extracted 2026-06-20 from the inline `defi_master` epic body (§ "Governance parameters refresh",
> migrated there from the archived `defi_protocol_governance_parameters_refresh_2026_05_08` issue) during the
> asset-group-umbrella restructure. The umbrellas were carrying ~75 stale May-07/08 inline todos that the backlog regen
> (`regen_backlog_from_plan.py`, which scans `plans/active/*.md` only — never `plans/epics/`) never dispatched. This is
> genuinely net-new, unowned work: Aave/Compound/Morpho governance parameters (LTV, liquidation threshold, rate-curve
> kinks, borrow caps) are frozen at discovery time today with no refresh path, so a governance change between discovery
> and execution silently mis-prices a live position. Manifest/coverage/`source` work for DeFi is owned separately by
> [`defi_manifest_canonicalisation_2026_06_01.md`](./defi_manifest_canonicalisation_2026_06_01.md) — do NOT duplicate it
> here.

## Context

Live trading risk: governance parameters are read once at discovery and never refreshed. A DAO LTV / liquidation-
threshold / IRM change between the historical compute timestamp and the live execution timestamp is invisible to the APR
calculator and the strategy sizer → positions are mis-priced with no lookahead protection.

This plan ships the refresh path end-to-end: a per-protocol event listener → a time-versioned `governance_params`
parquet → asof reads wired into the features-onchain APR calculator and strategy-service sizing, plus the new UAC
lifecycle event the listener emits. **This plan GATES** the Cat-B fallback removal in
[`defi_onchain_derivable_values_and_date_drift_2026_06_20.md`](./defi_onchain_derivable_values_and_date_drift_2026_06_20.md)
Phase 3 (that phase replaces the inline LTV/liquidation constants with reads from the Phase-2 parquet shipped here).

## P0 — governance-params refresh path

- [x] ✅ [SCRIPT] P0. **Phase 1 — Per-protocol event listener.** Aave V3: listen for `ReserveDataUpdated` +
      `BorrowCapChanged` + `SupplyCapChanged` events. Compound V3: listen for IRM-change events. Morpho: curator
      `MarketParamsUpdated` events. Per-event: write to the time-versioned parquet (Phase 2). Implementation: extend the
      MTDS DeFi adapters with an event-listener mode (separate from the current snapshot-poll mode).
      — market-tick-data-service@fc3df1c: `GovernanceParamsEventPoller` in
      `market_tick_data_service/market_interface/adapters/defi/live/governance_params_event_poller.py`.
      Covers Aave V3 Pool + PoolConfigurator (BorrowCapChanged, SupplyCapChanged, LtvChanged,
      LiquidationThresholdChanged, LiquidationBonusChanged; optional ReserveDataUpdated gated behind
      `include_rate_updates=True`), Compound V3 Configurator (SetConfiguration — full IRM kink/slope
      update detection; struct decode deferred to Phase 2 parquet writer), Morpho Blue
      (CreateMarket with initial market params; MetaMorpho curator MarketParamsUpdated topic TBD
      once per-vault contract addresses are confirmed). eth_getLogs polling at 12s / 1-block
      intervals; per-event ABI decoding yields `GovernanceParamChange` dataclass;
      caller emits GOVERNANCE_PARAMS_CHANGED + writes parquet (Phase 2). QG green on MTDS
      (basedpyright + ruff + tests, 23s).
- [ ] [SCRIPT] P0. **Phase 2 — Time-versioned `governance_params` parquet schema.** Path:
      `gs://market-data-tick-defi-{pid}/governance_params/by_protocol/protocol={p}/chain={c}/by_date/day={d}/...parquet`.
      Schema: `{protocol, chain, asset, param_name, param_value, asof_block, asof_timestamp, governance_tx_hash}`. Asof
      lookups via a `read_governance_params_asof(protocol, chain, asset, asof: datetime)` UTL helper —
      `asof <= timestamp` filter, latest row wins. NO future-dated rows ever returned (`LookaheadBiasError` if
      attempted).
- [ ] [SCRIPT] P0. **Phase 3 — features-onchain APR calculator migration.** Replace inline LTV / IR constants with asof
      reads from the `governance_params` parquet (Phase 2). `LookaheadBiasError` check at every read. **This is the
      dependency that gates Cat-B fallback removal** in `defi_onchain_derivable_values_and_date_drift_2026_06_20`
      Phase 3.
- [ ] [SCRIPT] P0. **Phase 4 — strategy-service sizing migration.** Historical-asof in batch (read params at the
      historical compute timestamp); current-asof in live (read latest available). Strategy onboarding checklist gains a
      "governance dependency declaration" requirement.
- [x] ✅ [SCRIPT] P0. **NEW UAC `LifecycleEventType` `GOVERNANCE_PARAMS_CHANGED`** emitted by the Phase 1 listener at every
      change. Payload: `{protocol, chain, asset, param_name, old_value, new_value, asof_block, governance_tx_hash}`.
      — unified-api-contracts@5a3961f: `LifecycleEventType.GOVERNANCE_PARAMS_CHANGED` added to enum;
      `GovernanceParamsChangedDetails(BaseModel)` (protocol/chain/asset/param_name/old_value/new_value/
      asof_block/governance_tx_hash) + `GovernanceParamsChangedEvent` typed wrapper added to
      `unified_api_contracts/internal/events.py`. QG green (263s, all gates pass).
- [ ] [SCRIPT] P1. **Phase 5 — Snapshot space monitoring (proactive).** Cloud Scheduler job polls Snapshot.org
      governance spaces (aavedao, comp-vote, morpho) every 6h; emits a `GOVERNANCE_PROPOSAL_LIVE` event when a
      parameter-change proposal opens; alert routes to operator-on-call.

## Success criteria

- A governance parameter change on Aave V3 / Compound V3 / Morpho produces a `GOVERNANCE_PARAMS_CHANGED` event and a new
  time-versioned `governance_params` row within one listener cycle.
- The features-onchain APR calculator and strategy-service sizer read params via the asof helper; a feature timestamp
  earlier than the params asof raises `LookaheadBiasError` (no silent stale value, no future-dated row returned).
- `bash scripts/quality-gates.sh` green on `market-tick-data-service`, `features-service`, `strategy-service`, and
  `unified-api-contracts` before each commit; basedpyright + ruff clean.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the listener runs on real infra and emits
at least one real or back-tested `GOVERNANCE_PARAMS_CHANGED` event; the `governance_params` parquet is written and
sample-inspected (non-NaN rows, monotonic asof ordering) on real GCS; the asof read is exercised end-to-end through the
APR calculator on a real historical window.
