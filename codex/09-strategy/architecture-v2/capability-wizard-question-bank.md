---
scope: [engineer, admin]
last_reviewed: 2026-06-11
---

# Capability Wizard — walkthrough question bank

Every wizard question is pinned to the code anchor that powers its answer set. **Rule: a question may only appear in the
wizard if its options are derivable from a registry/enum (status `registry`) or it is an explicitly tracked gap (`gap` →
[gap tracker](../../../plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md)).** A question with no anchor
and no gap entry is itself a finding.

Modes: **walkthrough** (chained, each stage filters the next), **isolation** (any single question, flat),
**screener/inverse** (start from holdings or target metrics → qualifying strategies), **portfolio** (combine multiple
configured strategies). Same manifest, four query styles.

## Stage A — Mandate & investor profile

| Question                                                                                                                | Answer source                                                                                   | Status                |
| ----------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | --------------------- |
| Who is configuring? (internal allocation / operator / client / agent)                                                   | wizard session metadata; persona resolution pattern from `lib/questionnaire/resolve-persona.ts` | registry              |
| Fund structure: pooled / SMA / prop? How many investors/pools now; planned migration (e.g. 2 pooled → 1 SMA next year)? | fund-administration subscription/redemption state machines; **offerable-structure manifest**    | gap (fund structures) |
| Share class / treasury denomination?                                                                                    | USDC/ETH/SOL/BTC per `codex/04-architecture/wallet-hierarchy-and-capital-flow.md`               | registry              |
| Base-currency neutrality: USD-only / BTC-neutral / ETH-neutral?                                                         | questionnaire enum + share-class-aware PnL views (global ledger)                                | registry              |
| Investor jurisdiction & entity type? (filters venues/instruments)                                                       | client_isolation_and_governance jurisdiction restrictions                                       | partial               |
| Reporting cadence + attribution granularity?                                                                            | client-reporting-api; global ledger PnL attribution views                                       | registry              |
| Subscription/redemption cadence needed (e.g. daily deposit/withdraw)?                                                   | fund-administration state machines; capital_router rebalance support                            | partial               |

## Stage B — Capital, custody & collateral

| Question                                                                                                    | Answer source                                                                | Status   |
| ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------- |
| Initial deposit asset(s) & schedule (multi-tranche: BTC today, USDT tomorrow)? Show conversion path preview | `capital_router.py` AllocationTargets + wallet hierarchy → fund-flow mermaid | registry |
| Custody: Copper (DeFi) / CEFFU (CeFi) / self-custody?                                                       | defi_master + cefi_master epic scopes; custody adapters in execution-service | partial  |
| Treasury vs trading-wallet split — accept default (DeFi 20/80, CeFi 0/100) or override?                     | wallet-hierarchy doc; deployment wallet config                               | registry |
| How much collateral stays on each exchange — explicit, or assumed from policy?                              | **collateral registry**                                                      | gap      |
| Which collateral does each venue accept, at what haircut?                                                   | **collateral registry**                                                      | gap      |
| Margin mode per venue: isolated / cross?                                                                    | `MarginMode` (architecture_v2 enums)                                         | registry |
| Leverage cap; target LTV vs max/liquidation LTV; maintenance vs liquidation margin per venue?               | **collateral registry**                                                      | gap      |
| Which brokers are usable (TradFi)?                                                                          | **collateral registry** (broker list)                                        | gap      |

## Stage C — Strategy selection

| Question                                                                                                                      | Answer source                                                                       | Status        |
| ----------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------- |
| Asset category(ies)?                                                                                                          | `VenueCategoryV2` (CEFI/DEFI/TRADFI/SPORTS/PREDICTION)                              | registry      |
| Strategy family → archetype? (options filtered by capability matrix)                                                          | `StrategyFamily` (9) → `StrategyArchetype` (53) via `ARCHETYPE_CAPABILITY_REGISTRY` | registry      |
| Edge method?                                                                                                                  | `EdgeMethod` enum                                                                   | registry      |
| Hold policy / urgency?                                                                                                        | `HoldPolicy`, `Urgency` enums                                                       | registry      |
| Staking method (for LST archetypes — e.g. stake → LST → post to CeFi → short perp)?                                           | `StakingMethod` enum + carry/staked-basis archetypes                                | registry      |
| Market exposure: neutral / directional? Target Sharpe / max DD / capacity? (becomes the plan-format B3 KPI declaration)       | questionnaire prefs + `performance_metrics.py` over backtests                       | registry      |
| Decision engine: ML (which models), rules, or trading-agent LLM over features (which models permitted, what parameter scope)? | ml-service model registry (walk-forward); **agent capability declarations**         | partial / gap |

## Stage D — Universe

| Question                                                                                           | Answer source                                                                    | Status        |
| -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------------- |
| Venues — all, or explicit? (auth-wired status shown per venue)                                     | instruments-service `InstrumentRecord` + `ENDPOINT_REGISTRY` (access_mode, auth) | registry      |
| Chains; multi-chain allowed? Bridge policy; MEV submission mode?                                   | chain registries + `MevSubmissionMode` enum                                      | registry      |
| Instrument types?                                                                                  | `ArchetypeInstrumentType` (SPOT/PERP/DATED_FUTURE/OPTION) × archetype matrix     | registry      |
| Sports: which leagues, fixture date ranges, settlement currency?                                   | instruments snapshot (league_id); sports_master (GBP settlement)                 | registry      |
| Prediction: which canonical question groups?                                                       | post-v9 canonical_question_group axis                                            | registry      |
| Options: expiries, strike ranges, greek limits? Is execution wired end-to-end on the chosen venue? | `CanonicalExpiryCalendar` + greeks-service; **execution wiring depth**           | partial / gap |

## Stage E — Data & batch-live symmetry

| Question                                                                                        | Answer source                                                                      | Status             |
| ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | ------------------ |
| Timeframes/granularities? Candle vs tick?                                                       | feature registry timeframes; MTDS/MDPS vs market-tick-data-service                 | registry           |
| Per source: WS vs REST? batch / live / replay supported?                                        | source-mode capability matrix (to be codified from the 2026-06-07 audit)           | gap (extraction)   |
| Minimum history to run (features lookback × ML training window) — and do we _actually have it_? | derived manifest edge + live check via deployment-api `/api/data-status/drilldown` | registry (derived) |
| Which feature groups/versions feed this archetype?                                              | features registry (~1,382 specs / 34 groups, versioned)                            | registry           |
| What simulation matching/fill assumptions will the backtest use here?                           | **simulation-assumptions registry**; PIT guard (`backtest_pit_guard.py`)           | gap                |
| Known batch-live asymmetries for this venue/instrument?                                         | batch_live_symmetry_master audits → registry                                       | gap                |

## Stage F — Execution

| Question                                                                                       | Answer source                                                                         | Status        |
| ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ------------- |
| Which instruction/account actions does this strategy emit?                                     | `InstructionActionV2` / `AccountActionV2`; `instruction_type.py`                      | registry      |
| Algo per instruction type?                                                                     | `algorithms/registry.py` (SOR, sor_twap, swap_twap, atomic_bundle_executor, selector) | registry      |
| Multi-leg (basis/spread/combo): atomic or legged? Who owns inter-leg delta risk while filling? | `AtomicExecutionMode`; **order-semantics declarations**                               | partial / gap |
| TIF: FOK / IOC / post-only? Make or take?                                                      | order_types enums; **per-venue honor matrix**                                         | partial / gap |
| Ref pricing: fixed entry, or delta-adjusted to underlying (premium-on-delta)?                  | **order-semantics declarations**                                                      | gap           |
| Partial-fill compensation policy?                                                              | `CompensationPolicy` enum                                                             | registry      |
| Full fee stack at my size (exchange/gas/broker/clearing, maker-taker tier)?                    | **fees registry** + execution cost prediction (strategy_master scope)                 | gap           |
| Transfer/rebalance cadence and routing (incl. daily withdraw/deposit)?                         | `capital_router.py`; transfer handlers in execution-service                           | registry      |

## Stage G — Risk & circuit breakers

| Question                                                              | Answer source                                                                                                                              | Status   |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| Which kill switches to arm, with what thresholds?                     | `KillSwitchReason` (DAILY_LOSS_BREACH, MAX_DRAWDOWN_BREACH, DATA_STALE, COINTEGRATION_BREAKDOWN, GREEK_LIMIT_BREACH, VENUE_UNAVAILABLE, …) | registry |
| At which gate layer does each check run?                              | `RiskGateLayer` (STRATEGY_SELF_CHECK → RISK_PREFLIGHT → EXECUTION_PRETRADE → VENUE_SIDE) + `RiskGateDecision`                              | registry |
| Where do I watch liquidation proximity, and at what alert thresholds? | strategy-service risk/ (liquidation proximity) + alerting-service channels                                                                 | partial  |
| What is the liquidation protocol on each selected venue?              | **collateral registry** (per-platform protocol)                                                                                            | gap      |
| Which named stress scenarios should the prospectus replay?            | stress library over backtest runner (proposed — see plan Wave 2)                                                                           | proposed |

## Stage H — Deployment & infra

| Question                                                                                   | Answer source                                                                        | Status   |
| ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------ | -------- |
| Cloud: AWS or GCP? Region?                                                                 | `UnifiedCloudConfig`; deployment-service backends (cloud_run / aws_batch); terraform | registry |
| Lifecycle: EPHEMERAL_BATCH / EPHEMERAL_EXPERIMENT / SCHEDULED_RECURRING / LONG_LIVED_LIVE? | deployments registry lifecycle_class                                                 | registry |
| Batch schedule? Live protocol affinity constraints (e.g. DeFi live = Solana + EVM)?        | deployment topology; colocation rules                                                | partial  |
| Client isolation level?                                                                    | per-client subprocess isolation (strategy-service); funds isolation rules            | registry |

## Stage I — Reporting & observability

| Question                                                               | Answer source                                                                                                                                 | Status   |
| ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| Where do I see balances / PnL / order fills, and what are the schemas? | `LedgerRow` + transaction taxonomy (`canonical/crosscutting/ledger.py`); per-shard schema via `/api/data-status/schema`; client-reporting-api | registry |
| Attribution granularity (per strategy / venue / leg / fee component)?  | global ledger PnL attribution views                                                                                                           | partial  |
| Alert channels and escalation paths?                                   | alerting-service config                                                                                                                       | registry |

## Stage J — Handover & verification

| Question                                                                                                        | Answer source                                                                                  | Status   |
| --------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | -------- |
| "Here is what I need from you to get started" — API keys, wallet signers, custody onboarding per selected venue | `ENDPOINT_REGISTRY` auth requirements + custody adapters                                       | registry |
| "Want a 5-year backtest of your configured preference?" (gated on data precheck)                                | `strategy_service/engine/backtest/runner.py` + `performance_metrics.py` + data-status precheck | registry |
| Artifacts handed over: strategy config, prospectus, session JSON, generated smoke test                          | prospectus generator + session artifact (plan Wave 2)                                          | proposed |

## Isolation-mode starter set

What strategies can I trade? · What venues/instruments per category? · Which execution algos exist and for which
instruction types? · What strategy instructions am I capable of? · Can I do multi-chain transactions? · What data do we
have at which granularities, batch vs live, WS vs REST? · What are the simulation assumptions for X? · What collateral
does venue V accept and at what haircut? · What is V's liquidation protocol / max LTV / maintenance margin? · Which
brokers can I use? · Where do I track liquidation proximity? · What feature groups exist; which models are available? ·
Can an agent generate instructions over features? · What's the minimum data to smoke-test archetype A on venue V? · What
fees would I pay at granularity G? · For a spread trade, which algo manages the delta between legs? · How do I do an
option combo, and is ref pricing delta-adjusted or fixed?

## See also

- Concept SSOT: [`capability-wizard.md`](capability-wizard.md)
- Plan:
  [`plans/active/capability_wizard_and_manifest_2026_06_11.md`](../../../plans/active/capability_wizard_and_manifest_2026_06_11.md)
- Gap tracker:
  [`plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md`](../../../plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md)
