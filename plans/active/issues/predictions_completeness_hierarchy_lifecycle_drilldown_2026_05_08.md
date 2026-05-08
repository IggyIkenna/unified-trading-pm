---
title:
  "Prediction markets — full-coverage parity with sports pattern: 3-level hierarchy (asset → canonical_question_group →
  timeframe), MTDS lifecycle-bounded CLOB capture, MDPS sparse-but-honest 4-category, full-column instrument metadata
  (description/clob_token_ids/oracle/settlement-basket), deployment-ui drilldown + parquet download"
created: 2026-05-08
author: ikenna
source:
  - unified-api-contracts/unified_api_contracts/canonical/domain/predictions/canonical_groups.py (CanonicalQuestionGroup
    enum + CANONICAL_GROUP_METADATA — Phase 1A SHIPPED)
  - unified-api-contracts/unified_api_contracts/canonical/domain/predictions/lifecycle.py (MarketLifecycle gold standard
    — Phase 1A SHIPPED)
  - unified-api-contracts/unified_api_contracts/canonical/domain/predictions/classifiers.py
    (classify_polymarket_to_canonical_group + classify_kalshi_to_canonical_group — SHIPPED)
  - instruments-service/instruments_service/reference_data/adapters/prediction/polymarket.py:321 (get_market_metadata_df
    — captures description/tags/event_slug post-fetch but NOT persisted as canonical shard schema)
  - market-tick-data-service/.../umi_tick_provider.py:225 (legacy category="prediction_market"; canonical_question_group
    routing pending Phase 2A)
  - market-data-processing-service/.../trades_adapter.py:25 (PredictionTradesAdapter — basic OHLCV present; 4-category
    empty decision NOT fully wired)
  - plans/active/predictions_master_2026_05_07.plan.md:69-215 (master plan, ~38% complete per 2026-05-07 audit; Phase
    2-5 deferred items)
  - operator screenshot 2026-05-08 — deployment-ui shows PREDICTION at 87.2% with FLAT MARKETS list
    (BNB/BTC/CRUDE_OIL/DJIA/DOGE/ETH/FOOTBALL/GOLD/HYPE/NDX/OTHER/SILVER/SOL/SPX/XRP); no per-canonical-question-group
    hierarchy, no per-shard parquet download
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Prediction markets — full coverage parity with sports pattern

> **Severity**: P1 — prediction asset_group is the most fleshed-out lifecycle pattern in the workspace (MarketLifecycle
> is gold-standard per issue 8 Q3) but its consumer-side parity (MTDS lifecycle-bounded capture, MDPS sparse-but-honest,
> deployment-ui drilldown) lags. Doesn't strictly block May 23 cutover (DeFi archetypes don't trade prediction markets
> in v1) but blocks any prediction-strategy graduation + degrades operator visibility today. **Blast radius**: UAC
> `predictions/` (PREDICTION_GROUPS registry stub backfill + clob_token_ids + settlement metadata) + instruments-service
> Polymarket / Kalshi adapters (full-column capture + MARKET_LIFECYCLE writer) + MTDS prediction CLOB adapters
> (lifecycle-bounded + cluster validation) + MDPS PredictionTradesAdapter (4-category empty decision + lookahead clip) +
> deployment-ui (3-level hierarchy + parquet download) + features-\* (LookaheadBiasError respecting per-market
> lifecycle). **Suggested owner**: `predictions_master_2026_05_07.plan.md` Phase 2 + 5 — this issue is the consumer-side
> completion list, not a competing plan.

## What I found

Predictions Phase 1A (UAC SSOT for canonical_question_group + lifecycle + classifier) shipped 2026-05-06 → 2026-05-07
and is the gold-standard lifecycle pattern in the workspace. But the consumer-side wiring across the 5 layers is
incomplete; the deployment-ui screenshot is the most visible symptom (flat MARKETS list, no hierarchy, no parquet
download).

### Q1 — UAC `canonical_question_group` taxonomy: ✅ SHIPPED

[canonical_groups.py](../../../unified-api-contracts/unified_api_contracts/canonical/domain/predictions/canonical_groups.py)
defines `CanonicalQuestionGroup` enum with 9 groups: `BTC_UP_DOWN_HOURLY` / `BTC_UP_DOWN_DAILY` / `ETH_UP_DOWN_HOURLY` /
`ETH_UP_DOWN_DAILY` / `SPX_UP_DOWN_DAILY` / `FED_RATE_DECISION_PER_FOMC` / `CPI_PRINT_PER_MONTH` /
`ELECTION_PRESIDENT_2028` / `OSCARS_BEST_PICTURE` / `OTHER`. `CANONICAL_GROUP_METADATA` carries cadence (hourly=24/day,
daily=1/day, irregular), resolution_basis, settlement_lag.
[lifecycle.py](../../../unified-api-contracts/unified_api_contracts/canonical/domain/predictions/lifecycle.py)
`MarketLifecycle` is hard-required `(market_created_at, resolution_time, settlement_time)`.

**Residual gap**: `PREDICTION_GROUPS` registry stub at UAC@bb24aba is `{}` (TEMPORARY STATE per writegate plan's
`Temporary states` section) — backfill needed for canonical groups beyond the initial 9. Per the screenshot, today's
flat MARKETS includes CRUDE*OIL / GOLD / SILVER / DJIA / NDX (commodities + indices) and DOGE / SOL / XRP / BNB / HYPE
(alt-coins) which need their own `\*\_UP_DOWN*\*` canonical_question_groups. Likely 30+ groups to flesh out.

### Q2 — instruments-service prediction adapter: PARTIAL — schema-narrow despite source-rich

[polymarket.py:321](../../../instruments-service/instruments_service/reference_data/adapters/prediction/polymarket.py#L321)
`get_market_metadata_df()` captures
`(market_id, canonical_question_group, question, description, outcomes, market_slug, tags, end_date_iso, active, closed, volume, liquidity, event_title, event_slug, series_slug)`
post-fetch. But:

- **Lifecycle timestamps stamped on `InstrumentRecord.available_from_datetime / available_to_datetime` but NOT persisted
  as separate `MARKET_LIFECYCLE` parquet** (deferred to Phase 2 per master plan line 125-126). Means downstream
  consumers can't read lifecycle as a first-class entity.
- **`clob_token_ids` NOT captured** — Polymarket Gamma API exposes them; needed for on-chain CLOB capture at MTDS.
- **`description` captured but NOT in canonical shard schema** — this is the long-form market resolution criteria (the
  user's "settlement basket / assumptions"). Critical for any feature that needs to reason about settlement rules.
- **`marketMakerAddress`, `umaBond`, `umaReward` NOT captured** — needed for risk-and-exposure-service to model UMA
  optimistic-oracle disputes.
- **Schema enforcement**: per issue 8 Q3 verdict, `MarketLifecycle`'s 3 timestamps ARE required at the dataclass level —
  but the instruments-service write path doesn't validate they're present per-row at `record_captured` time (no
  `record_failed(SCHEMA_VALIDATION_FAILED)` if a market is missing them). Same per-row-vs-venue-shard-fail-all pattern
  as issue 9.

### Q3 — Hierarchy: ✅ for classifier, ❌ for deployment-ui

[classifiers.py:107](../../../unified-api-contracts/unified_api_contracts/canonical/domain/predictions/classifiers.py#L107)
`classify_polymarket_to_canonical_group` parses `(category, underlying, market_type, resolution_period)` from slug +
description, maps via `_CATEGORY_UNDERLYING_PERIOD_TO_GROUP`. Override-first dict (POLYMARKET_CONDITION_ID_TO_GROUP)
catches edge cases. CLASSIFIER_STABILITY_HASH (UAC@5f76bd4) gates re-classification.

**3-level hierarchy IS declared** in metadata (asset → canonical_question_group → cadence) but **deployment-ui still
renders flat**. Today's screenshot:

```
PREDICTION (87.2%)
└── POLYMARKET (out of scope - 100%)
    ├── BNB (59%)        ← asset-level grouping (legacy / pre-canonical)
    ├── BTC (95%)
    ├── CRUDE_OIL (81%)
    └── ... 12 more
```

User's target hierarchy:

```
PREDICTION (87.2%)
└── POLYMARKET
    └── BTC (asset)
        ├── BTC_UP_DOWN_HOURLY (canonical_question_group, cadence=24/day)
        │   └── per-(market_id × day) shard with lifecycle bounds
        ├── BTC_UP_DOWN_DAILY (canonical_question_group, cadence=1/day)
        ├── BTC_UP_DOWN_WEEKLY
        └── BTC_PRICE_TARGET (canonical_question_group, cadence=irregular)
            ├── ABOVE_100K_BY_2026_12_31
            └── ABOVE_120K_BY_2026_12_31
```

### Q4 — MTDS lifecycle-bounded CLOB capture: ❌ NOT WIRED

[umi_tick_provider.py:225](../../../market-tick-data-service/market_tick_data_service/adapters/umi_tick_provider.py#L225)
still references legacy `category="prediction_market"`. Per CLAUDE.md "Prediction market lifecycle timing" rule:

> NO ticks before `market_created_at`, NO new ticks after `settlement_time`. Cluster validation per
> `(canonical_question_group, day)` checks that all expected market_ids with active windows in that day are represented
> (HOURLY → 24 clusters expected, DAILY → 1, etc.).

**Current state**:

- ❌ No upper-bound clip at `settlement_time` — adapter could keep fetching post-settlement (returns empty so harmless
  waste, but pollutes manifest with `record_empty(SOURCE_RETURNED_ZERO)` instead of
  `record_expected_empty(EXPECTED_POST_SETTLEMENT)`).
- ❌ No lower-bound clip at `market_created_at` — same issue at the pre-creation side.
- ❌ Cluster validation per `(canonical_question_group, day)` NOT wired. HOURLY group should expect 24 market_ids/day;
  if only 22 appear in the bundle, no `ClusterCoverageError` fires — silent partial-bundle.
- ❌ Available_at stamping for prediction trades uses tick-timestamp; correct in principle but no validation that
  `tick.timestamp ∈ [market_created_at, settlement_time]`.

### Q5 — MDPS PredictionTradesAdapter: PARTIAL — basic candle present, 4-category not fully wired

[trades_adapter.py:25](../../../market-data-processing-service/market_data_processing_service/adapters/trades_adapter.py#L25)
`PredictionTradesAdapter` extends `CefiTradesAdapter` for OHLCV aggregation. Same code path → same column schema. ✅

**Gaps**:

- ❌ **4-category empty-output decision (A/B/C/D per CLAUDE.md)** not explicitly tested in MDPS for prediction.
  Categories:
  - A (source returned 0 for active market) → `record_empty(SOURCE_RETURNED_ZERO)`
  - B (timestamp bias / partition mislabeled) → `record_failed(UpstreamTimestampBiasError)`
  - C (malformed source field) → `record_failed(MalformedTickFieldError)`
  - D (tradeable-but-illiquid: alive market, market window open, zero trades) → write zero-volume bar with prior market
    mid carry-forward + `record_captured`
- ❌ **Lifecycle clipping at MDPS / features-\***: feature compute does NOT clip at `min(target_ts, settlement_time)`.
  LookaheadBiasError check absent for prediction (sports has it via `available_at`, prediction lifecycle is more
  granular).
- ❌ **Per-market liquidity baseline** (composes with issue 5 `mdps_liquidity_baseline_and_live_tick_staleness`) —
  prediction markets have wildly different baselines (BTC_UP_DOWN_HOURLY active hours = high tick rate;
  OSCARS_BEST_PICTURE 11 months pre-resolution = near-zero). One global baseline doesn't apply.

### Q6 — deployment-ui drilldown + parquet download: ❌ GAP

Per screenshot:

- Flat MARKETS list, no canonical_question_group sub-hierarchy.
- No per-shard parquet download (sports has the pattern via the recent leaf-stats endpoint).
- No "available dates" expanded per market_id (the "▶ 420 available dates" at the bottom is global, not per-shard).

Sports drilldown pattern shipped 2026-05-07 evening per memory entry:

> deployment-api@3b0477a + LeafSchemaModal (15 tests) + LeafParquetStats Pydantic models + per-shard schema + NaN
> ratios + available_at envelope.

Same pattern needs to extend to prediction. Per `predictions_master_2026_05_07.plan.md:199`, this is BLOCKED-ON Phase
1 + manifest reflip — both already shipped per the Q1-Q3 verdicts above, so the UI work is now unblocked.

### Q7 — Plan coverage: PARTIAL — Phase 2-5 deferrals are the gap surface

`predictions_master_2026_05_07.plan.md` (38% complete per 2026-05-07 audit, line 85):

- ✅ Phase 1A (Q1 + Q3 classifier) shipped.
- ⚠️ Phase 2A (MTDS adapter migrations + MARKET_LIFECYCLE writer + MDPS empty-output validation) — pending. **All 4 of
  Q4 + parts of Q2 + Q5 belong here**.
- ⚠️ Phase 3 (manifest rewrite + reflip) — pending; required before deployment-ui hierarchy can render correctly.
- ⚠️ Phase 4 (reader / feature / strategy migration; LookaheadBiasError respecting per-market lifecycle) — pending.
- ❌ Phase 5 (deployment-ui drilldown + parquet download + canonical_groups backfill beyond initial 9) — pending.

**This issue is the consumer-side parity completion list — not a competing plan.** The work belongs IN
predictions_master Phase 2 + 5; this issue specifies the EXACT gap surfaces + acceptance criteria so the plan owner has
concrete todos.

## Why it matters

- **Operator visibility today**: 87.2% prediction coverage shown in deployment-ui is computed against today's flat-asset
  denominator. Once the 3-level hierarchy lands, the denominator changes (per-canonical-group cluster expectations) and
  the headline % is more honest (probably lower for sparse groups like OSCARS_BEST_PICTURE which sits near-zero for 11
  months).
- **Lifecycle-bounded MTDS unblocks honest sparse-but-correct semantics**: today's flat-shard manifest can't distinguish
  "BTC_UP_DOWN_HOURLY 2026-08-12 21:00 had no trades because market was already settled" from "we missed the trades
  during the active hour." Issue surface is the same as fixtures (sparse trades vs missing data) — needs the same
  lifecycle-anchored expected-universe.
- **Settlement-basket metadata blocks any settlement-aware feature**: features that reason about UMA dispute risk,
  oracle deviation, or basket recomputation can't be built without `description + umaBond + oracle_address` capture.
- **`Live = batch` violation**: live mode would naturally see lifecycle bounds (market closes for trading at
  `settlement_time`); batch's lifecycle-blind adapter records ticks past settlement as if they were normal — diverges.
- **Compounds with other 2026-05-08 issues**: composes with issue 5 (liquidity baseline per canonical_question_group),
  issue 8 (lifecycle hard-required — predictions is the gold standard already; this issue extends it to clob_token_ids +
  description + oracle), issue 9 (per-row schema validation), issue 12 (manifest cleanup when canonical_question_group
  taxonomy expands), issue 13 (oracle / mm addresses are on-chain-derivable Cat A immutable values).

## Recommended decision

Five workstreams, sequenced. **All belong in `predictions_master_2026_05_07.plan.md` Phase 2-5; this issue is the
consumer-side todo set.**

### Phase 2A — instruments-service full-column capture + MARKET_LIFECYCLE writer

Extend Polymarket + Kalshi adapters:

- Capture `clob_token_ids[]` (Polymarket on-chain CLOB token IDs).
- Capture `description` (long-form resolution criteria) as canonical column.
- Capture `marketMakerAddress`, `umaBond`, `umaReward`, `oracle_address`, `resolution_source`, `resolution_url`.
- Settlement-rule metadata: parse `description` for known patterns (`closing price >= X on date Y per source Z`) into
  structured `settlement_rule: SettlementRule` enum + `settlement_basket: dict[str, Any]` (the ticker / index basket +
  weights).

Ship `MARKET_LIFECYCLE` parquet at
`gs://{pid}-instruments/prediction/market_lifecycle/by_canonical_group/canonical_question_group={X}/asof={YYYY-MM-DD}/lifecycles.parquet`
per market_id. Schema-required:
`(market_id, canonical_question_group, market_created_at, resolution_time, settlement_time, oracle_address, settlement_rule, settlement_basket)`.

Per-row schema validation gate at `record_captured` (issue 9 pattern): missing required fields →
`record_failed(SCHEMA_VALIDATION_FAILED)` not silent venue-wide drop.

### Phase 2B — MTDS lifecycle-bounded CLOB capture

Polymarket + Kalshi MTDS adapters:

- Pre-fetch lifecycle lookup: query MARKET_LIFECYCLE for `(market_id)` → `(market_created_at, settlement_time)`. Skip
  fetch if `target_day` outside this range; emit `record_expected_empty(reason=EXPECTED_PRE_MARKET_CREATION)` or
  `record_expected_empty(reason=EXPECTED_POST_SETTLEMENT)`.
- During-window fetch with cluster validation: bundle by `(canonical_question_group, day)`; `record_captured` with
  `expected_root_clusters = expected_market_ids_for_canonical_group(group, day, lifecycles)` +
  `cluster_extractor = lambda r: r.market_id`. Under-coverage triggers `ClusterCoverageError`.
- Add 2 new typed reasons to `EMPTY_CONFIRMED_REASONS`: `EXPECTED_PRE_MARKET_CREATION`, `EXPECTED_POST_SETTLEMENT`.

### Phase 2C — MDPS 4-category empty-output decision for prediction

`PredictionTradesAdapter` extends inheritance to handle prediction-specific categories:

- A (source 0 trades during active window) → already `record_empty(SOURCE_RETURNED_ZERO)`.
- B (partition mislabeled) → `record_failed(UpstreamTimestampBiasError)`.
- C (malformed) → `record_failed(MalformedTickFieldError)`.
- D (tradeable-but-illiquid: market alive, lifecycle window open, zero trades during MDPS sample period) → write
  zero-volume bar with `prior_market_mid` carry-forward + `record_captured`. Compose with issue 5 liquidity-baseline 3rd
  state (suspected-data-bug if baseline says active hours of HOURLY market should have ≥N trades and we got 0).

### Phase 4 (renumbered) — Features + strategy migration

- features-\* read MARKET_LIFECYCLE parquet; clip feature compute at `min(target_ts, settlement_time)`.
- LookaheadBiasError in strict mode for prediction features: `feature.timestamp <= min(target_ts, settlement_time)` AND
  `tick.market_id`'s `market_created_at <= feature.timestamp`.

### Phase 5 — deployment-ui 3-level drilldown + parquet download

- Restructure prediction asset_group rendering:
  `POLYMARKET → asset (BTC) → canonical_question_group (BTC_UP_DOWN_HOURLY) → per-(market_id × day) shard`. Each level
  drilldown-clickable.
- Per-shard parquet download (extend the sports leaf-stats / LeafSchemaModal pattern shipped 2026-05-07). Same
  schema-view + NaN-ratios + available_at envelope.
- Show lifecycle bounds + cluster expectations per drilldown level:
  `BTC_UP_DOWN_HOURLY 2026-08-12: 22 of 24 expected market_ids captured (cluster coverage 91.7%)`.
- "Available dates" expanded per canonical_question_group instead of global asset_group level.

### Phase 5 (companion) — Backfill canonical_question_groups beyond initial 9

PREDICTION_GROUPS registry stub at UAC@bb24aba is `{}`. Add canonical groups for:

- Commodities: GOLD_UP_DOWN_DAILY / WEEKLY, SILVER_UP_DOWN_DAILY / WEEKLY, CRUDE_OIL_UP_DOWN_DAILY / WEEKLY.
- Indices: DJIA_UP_DOWN_DAILY / WEEKLY, NDX_UP_DOWN_DAILY / WEEKLY.
- Alt-coins: DOGE / SOL / XRP / BNB / HYPE × HOURLY / DAILY / WEEKLY (15 groups).
- Football: per-fixture or per-major-tournament canonical groups.
- Per-event recurring (CPI, FOMC, NFP, etc.) — extend FED_RATE_DECISION_PER_FOMC pattern.

Estimate ~30+ new canonical groups to seed. Each requires CANONICAL_GROUP_METADATA entry (cadence, resolution_basis,
settlement_lag).

## Acceptance criteria

- [ ] Phase 2A: Polymarket + Kalshi adapters capture full-column metadata (clob_token_ids, description, oracle_address,
      settlement_rule, settlement_basket).
- [ ] Phase 2A: MARKET_LIFECYCLE parquet written per (canonical_question_group, asof) with per-row schema validation.
- [ ] Phase 2B: MTDS lifecycle-bounded capture; `EXPECTED_PRE_MARKET_CREATION` + `EXPECTED_POST_SETTLEMENT` reasons
      added.
- [ ] Phase 2B: cluster validation per (canonical_question_group, day); under-coverage triggers `ClusterCoverageError`.
- [ ] Phase 2C: MDPS 4-category empty-output decision wired for prediction; smoke test for each category.
- [ ] Phase 4: features-\* clip at `min(target_ts, settlement_time)`; LookaheadBiasError enforces per-market_id
      `market_created_at` lower bound.
- [ ] Phase 5: deployment-ui shows 3-level hierarchy with cluster-coverage % per canonical_question_group + per-shard
      parquet download.
- [ ] Phase 5 companion: PREDICTION_GROUPS registry backfilled with ~30+ canonical groups covering all current top-level
      assets in screenshot.
- [ ] Manifest cleanup (issue 12 mandate): re-enumerate expected universe after canonical_groups expansion; purge legacy
      per-base_asset shard rows.
- [ ] Smoke test: drill into POLYMARKET → BTC → BTC_UP_DOWN_HOURLY → 2026-05-08; verify 24 expected market_ids with
      cluster coverage %, lifecycle bounds, parquet download for each.

## Open questions

- Polymarket's `clobTokenIds` are per-outcome (YES + NO), so a binary market has 2 token IDs. For multi-outcome markets,
  N token IDs. Does the schema capture per-outcome at row-grain or as `clob_token_ids: list[str]`? Default: list, per
  market.
- For settlement-rule parsing: how aggressive should the parser be? Default: capture `description` verbatim + a
  structured `settlement_rule` enum for common patterns; non-matching falls to `OTHER` with the verbatim description
  preserved. Avoid over-fitting heuristics.
- Kalshi vs Polymarket schema differences: `oracle_address` is Polymarket-specific (UMA); Kalshi uses CFTC-regulated
  settlement. Schema should accommodate both — recommend
  `resolution_mechanism: enum {UMA_OPTIMISTIC_ORACLE, CFTC_REGULATED, INTERNAL_OPERATOR}` + per-mechanism details.
- For per-market liquidity baseline (issue 5 composition): baseline calculation needs to bucket by
  canonical_question_group AND time-of-day (HOURLY markets have intra-hour activity skews). Is a single 30-day rolling
  sufficient, or per-group-per-hour-of-day required?
- For deployment-ui hierarchy: per-canonical_question_group cluster coverage is computed how when the group is irregular
  (FED_RATE_DECISION_PER_FOMC fires ~8x/year on irregular dates)? Default: cluster-coverage at "expected market_ids per
  FOMC date" grain, summed over historical FOMC dates within the date range.
- Coordination with issue 13 (on-chain-derivable Cat A): Polymarket `oracle_address` + `marketMakerAddress` are
  on-chain-derivable immutable values. Should they go through the `derive_*_addresses.py` SSOT script pattern, or
  capture-at-discovery suffices since they're 1:1 per market_id?
- The `OTHER` group at 100% (421/421) in the screenshot is suspicious — likely a catch-all bucket for un-classified
  markets. After canonical_groups backfill, this number should drop to near-zero (everything classified).
