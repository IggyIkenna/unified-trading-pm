---
scope: [engineer, admin]
---

# Availability Manifest & Data Status — SSOT

<!-- MULTI_AXIS_CORRECTION_2026_05_06 -->

## Multi-axis correction banner (canonical)

> **Multi-axis correction (2026-05-06)** — per
> [`data_status_multi_axis_shard_propagation_2026_05_06.plan.md`](../../plans/archive/data_status_multi_axis_shard_propagation_2026_05_06.plan.md):
> a column belongs in the **shard atom** ONLY IF it earns it via failure isolation OR memory ceiling OR concurrency
> orthogonality. Otherwise it's a **display axis** (row-level column for filter/group, NOT a manifest row per value).
> This refines the per-asset-group shard atoms below:
>
> - **Sports**: shard atom = `(asset_group=sports, venue/source, data_type, league_id, day)`. **`fixture_id` is a
>   row-level column in the parquet, NOT a shard axis** — `(league_id, day)` already bounds the per-day fixture set;
>   per-fixture detail at drill-down comes from reading the parquet, not from a separate manifest row. Avoids 10×
>   manifest inflation.
> - **Prediction**: shard atom =
>   `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)`.
>   **`market_id` is a row-level column in the parquet, NOT a shard axis** — same rationale. HOURLY (24/day) + DAILY +
>   ELECTION groups all roll up to one manifest row per `(canonical_question_group, day)`; per-market detail at
>   drill-down from parquet.
> - **CeFi options/futures bundles**: bundle root IS a shard axis (memory + concurrency); per-symbol within bundle is
>   parquet row (cluster validation enforces all expected per-bundle clusters covered).
> - **DeFi `chain`** IS a shard axis (independent RPC/subgraph endpoints + failure isolation).
> - **ML / strategy / execution**: new `job_id` v7 manifest column for experiment-keyed services. Same
>   `(model_family, training_period, job_id)` shard atom for ML training; `(strategy_id, job_id)` for strategy;
>   `(strategy_id, instruction_type, job_id)` for execution. Re-running same configs = new `job_id` (audit trail of
>   every experiment version).
> - **instrument_type for instruments-service**: NOT a shard axis (Databento + TARDIS bulk-fetch all instrument_types
>   per venue in one call). Display axis only — row column for filter/group.

> **This document is the single source of truth** for: what the availability manifest is, its schema, shard dimensions
> per service, how the data status page works, how availability % is calculated, and the integrity principles that make
> it trustworthy. All other docs, CLAUDE.md, cursor rules, and memory files cross-reference this document.

> **Reading this for chart debugging?** See also `chart-candle-delivery-flow.md` for the end-to-end flow from the
> price-chart widget through the manifest to the GCS parquets.

## What Is the Availability Manifest?

Every GCS data bucket has an `_index/availability_index.parquet` file. This parquet file is the **index of what data
exists** in that bucket. Each row represents one shard — a unit of data written atomically.

Services write to the manifest via `ManifestWriter` (UTL). The deployment-api reads it via `read_availability_index()`.
The deployment-ui renders it as the data status page.

### ⚠️ DeFi has 10+ separate manifest buckets — checking only one gives the wrong picture

A common misread (incident 2026-05-07 — sub-agent + main-agent both miscounted): MTDS DeFi data is **split across
multiple GCS buckets by `(asset_group=defi, data_type)`**. Reading only the "canonical" `market-data-tick-defi-{pid}`
bucket and concluding "Arb/Base/Polygon are at 0%" is **wrong** — those chains have data in the per-data_type buckets.

**Bucket layout** (verified 2026-05-07 by listing every DeFi-named bucket in `gs://central-element-323112` + reading
each `_index/availability_index.parquet`):

| Bucket pattern                              | Carries data_types                                                                                                                                                                                                                                                                                                                                        | Phase | Chains observed                                                                                            |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------- |
| `market-data-tick-defi-{pid}` (asset-group) | `dex_pool_state`, `dex_pool_swaps`, `dex_pools`, `oracle_prices`, `rate_indices`, `utilization`, `risk_params`, `vault_share_price`, `rewards`, `eigenlayer_rewards` + Phase-2 event-typed handlers (`liquidation_events`, `flash_loan_events`, `staking_yields`, `position_data`, `token_transfers`, `bridge_events`, `governance_events`, `mev_events`) | 1+2   | ETHEREUM + SOLANA                                                                                          |
| `lending-indices-{pid}`                     | `lending_indices`                                                                                                                                                                                                                                                                                                                                         | 1     | ETHEREUM + 9 EVM chains (Optimism / Base / Arbitrum / Scroll / Avalanche / Linea / BSC / Polygon / zkSync) |
| `dex-swaps-{pid}`                           | `dex_swaps`                                                                                                                                                                                                                                                                                                                                               | 1     | ETHEREUM + 7 EVM chains                                                                                    |
| `dex-pools-{pid}` (override-targeted)       | `dex_pools`                                                                                                                                                                                                                                                                                                                                               | 1     | (per-pool granularity)                                                                                     |
| `oracle-prices-{pid}`                       | `oracle_prices`                                                                                                                                                                                                                                                                                                                                           | 1     | ETHEREUM + Arbitrum / Base / Optimism / Polygon                                                            |
| `gas-fees-{pid}`                            | `gas_fees`                                                                                                                                                                                                                                                                                                                                                | 1     | ETHEREUM + 9 EVM chains                                                                                    |
| `lst-rates-{pid}`                           | `lst_rates`                                                                                                                                                                                                                                                                                                                                               | 1     | ETHEREUM + SOLANA                                                                                          |
| `perp-funding-{pid}`                        | `perp_funding`                                                                                                                                                                                                                                                                                                                                            | 1     | HYPERLIQUID, ASTER (DEX perps)                                                                             |
| `liquidations-{pid}` (override-targeted)    | `liquidations`                                                                                                                                                                                                                                                                                                                                            | 1     | EVM                                                                                                        |
| `evm-defi-{pid}`                            | `evm_defi`, `lending_indices`                                                                                                                                                                                                                                                                                                                             | mixed | ETHEREUM + 4 EVM chains                                                                                    |
| `solana-defi-{pid}`                         | `solana_defi`                                                                                                                                                                                                                                                                                                                                             | mixed | SOLANA                                                                                                     |
| `instruments-store-defi-{pid}`              | (instruments metadata, multi-chain)                                                                                                                                                                                                                                                                                                                       | n/a   | 7+ chains                                                                                                  |

**deployment-api routes correctly** — see `data_status_service.py`
[`_BUCKET_CATEGORY_OVERRIDES`](../../deployment-api/deployment_api/services/data_status_service.py) (line 2802) which
explicitly maps
`(market-tick-data-service, gas-fees|evm-defi|solana-defi|dex-pools|dex-swaps|lending-indices|liquidations|lst-rates|oracle-prices|perp-funding) → {data_type}-{pid}`.
The [`_MTDS_DEFI_SUB_DIMENSIONS`](../../deployment-api/deployment_api/services/data_status_service.py) list (line 2818)
enumerates the Phase-1 sub-buckets so the data-status panel queries each one. **If you're computing DeFi coverage, read
every bucket — not just the canonical asset-group one.**

#### Why two manifest layouts coexist

1. **Phase-1 per-data_type buckets** (`gas-fees`, `lending-indices`, etc.) — older sub-bucket pattern; per-data_type
   manifest is independent of the asset-group rollup. New DeFi data_types ship to dedicated buckets so the The Graph /
   Subgraph / chain-specific RPC adapters can rate-limit independently and operators can drill in via per-bucket
   coverage panels.
2. **Phase-2 event-typed handlers + eigenlayer_rewards** (`liquidation_events`, `flash_loan_events`, etc.) — newer
   pattern; lands in the canonical `market-data-tick-defi-{pid}` bucket (no override needed; default `_BUCKET_TEMPLATES`
   entry picks them up).

#### Vocabulary inconsistency to know about (kebab-case vs snake_case)

Many DeFi buckets contain BOTH `data_type=lending-indices` (kebab-case, older write path) AND
`data_type=lending_indices` (snake_case, newer + UAC-canonical) for the SAME data. Concrete numbers (verified
2026-05-07):

- `lending-indices-{pid}`: 24,976 kebab-case + 12,024 snake_case rows
- `dex-swaps-{pid}`: 28,171 kebab + 18,320 snake
- `lst-rates-{pid}`: 1,560 kebab + 2,796 snake
- `oracle-prices-{pid}`: 1,926 kebab + 5,106 snake
- `perp-funding-{pid}`: 3,298 kebab + 2,277 snake

The deployment-api handles this via
[`_canonicalise_defi_data_types()`](../../deployment-api/deployment_api/services/data_status_service.py) (line 991)
which read-time normalises kebab → snake. Per the function's docstring, "safe to remove once the corresponding one-shot
manifest migration runs (Plan B follow-up — currently no successor plan)" — so this is a real follow-up: write a
migration script that rewrites kebab `data_type` values in place across the 5 affected buckets, then delete the
canonicaliser. Aligns with the workspace "Manifest migration, NOT fallback" rule.

#### Operator verification recipe — exhaustive bucket walk

When in doubt about DeFi coverage, walk every manifest:

```bash
PID=central-element-323112
for B in dex-swaps evm-defi gas-fees lending-indices lst-rates market-data-tick-defi oracle-prices perp-funding solana-defi instruments-store-defi; do
  gcloud storage cp gs://${B}-${PID}/_index/availability_index.parquet /tmp/${B}.parquet 2>&1 | grep -i error
done
python3 -c "
import pandas as pd
from pathlib import Path
for p in sorted(Path('/tmp').glob('*-central-element-*.parquet')):
    pass  # iterate equivalent
for B in ['dex-swaps','evm-defi','gas-fees','lending-indices','lst-rates','market-data-tick-defi','oracle-prices','perp-funding','solana-defi','instruments-store-defi']:
    df = pd.read_parquet(f'/tmp/{B}.parquet')
    print(f'{B}: {len(df):,} rows · chains={sorted(df[\"chain\"].dropna().unique())}'  if 'chain' in df.columns else f'{B}: {len(df):,} rows')
"
```

Reference incident: **2026-05-07** — a per-chain coverage diagnosis sub-agent read only `market-data-tick-defi`,
concluded Arb/Base/Polygon were at 0%, surfaced as "PLANNING-CRITICAL CORRECTION" to the operator. Wrong call — those
chains have ~1k-5k rows each in the per-data_type buckets. The codex section above is the durable answer so future
agents don't repeat this misread.

### SSOT Locations

| Component                                            | Location                                                                                                                                                                                            |
| ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Schema definition                                    | `unified-trading-library/unified_trading_library/manifest_writer.py` — `AvailabilityRecord` dataclass                                                                                               |
| Writer                                               | `unified-trading-library/unified_trading_library/manifest_writer.py` — `ManifestWriter` class                                                                                                       |
| Reader                                               | `unified-trading-library/unified_trading_library/manifest_writer.py` — `read_availability_index()`                                                                                                  |
| Registry (start dates, expected venues, etc.)        | `unified-api-contracts/unified_api_contracts/registry/`                                                                                                                                             |
| **BUNDLED_DATA_TYPES + cluster registries**          | `unified-api-contracts/.../canonical/crosscutting/honest_coverage.py` (Phase 1B writegate plan)                                                                                                     |
| **SOURCE_PRIORITY (multi-source ranking)**           | `unified-api-contracts/.../canonical/crosscutting/source_priority.py` (Phase 1B writegate plan)                                                                                                     |
| **AVAILABILITY_AT_SEMANTICS (per-row stamp)**        | `unified-api-contracts/.../canonical/crosscutting/availability_semantics.py` (Phase 1B writegate plan)                                                                                              |
| **Per-source `available_at` stamping helpers**       | `unified-trading-library/unified_trading_library/availability_stamping.py` (LIFT-3 + writegate Phase 1A)                                                                                            |
| **Typed write-failure errors**                       | `unified-trading-library/unified_trading_library/errors.py` — `MissingClusterValidationError`, `UpstreamTimestampBiasError`, `MalformedTickFieldError`, `ClusterCoverageError` (writegate Phase 1A) |
| **CanonicalQuestionGroup + lifecycle (predictions)** | `unified-api-contracts/.../canonical/domain/predictions/` — `CanonicalQuestionGroup` enum, `classify_market_to_canonical_group`, `MarketLifecycle` (predictions Plan A Phase 1A)                    |
| API that serves data status                          | `deployment-api/deployment_api/services/data_status_service.py`                                                                                                                                     |
| UI that renders data status                          | `deployment-ui/src/components/DataStatusTab.tsx`                                                                                                                                                    |

### Active write-side contract changes (writegate plan + predictions plan)

The `ManifestWriter.record_captured` contract is being extended (writegate plan Phase 1A) — read this BEFORE adding new
caller code or assuming the legacy contract:

- `record_captured` will accept (and **require** for `data_type ∈ BUNDLED_DATA_TYPES`) two new kwargs:
  `expected_root_clusters: Mapping[str, int]` and `cluster_extractor: Callable[[str], str]`. Internal helper
  `_check_cluster_coverage` runs at write time; on under-coverage `record_failed(ClusterCoverageError(...))` fires
  INSTEAD of writing the parquet. UTL guard raises `MissingClusterValidationError` if `data_type` is bundled and the
  kwargs are absent. QG STEP 5.64 statically walks every `record_captured(` callsite + asserts the kwargs are passed
  when the literal data_type is bundled — fails CI if missing.
- `record_captured` will call `assert_available_at_present(df)` internally — every shard's parquet MUST have an
  `available_at` column populated per row, stamped at write time per `UAC.AVAILABILITY_AT_SEMANTICS`. Missing or null →
  `LookaheadBiasError`.
- Three new typed error variants for `record_failed`:
  `UpstreamTimestampBiasError(observed_dates, expected_day, n_ticks)` (path B in the empty-output decision tree below),
  `MalformedTickFieldError(field, n_dropped, sample_values)` (path C),
  `MissingClusterValidationError(data_type, expected_registry_key)` (cluster guard).
- A 4th typed error for the future NaN-ratio gate: `NanRatioExceededError(column, observed_ratio, threshold)` — landing
  in Plan B (UTL/UAC lift triple) which lifts `instruments-service _validate_predictions_null_rates` to a UTL helper.

**Streaming-writer companion — `record_captured_from_counts` (shipped UTL@`ef47c81b` per
[`wave2_polymarket_record_captured_from_counts_2026_05_09.md`](../../plans/active/wave2_polymarket_record_captured_from_counts_2026_05_09.md):49-60).**
`ManifestWriter.record_captured_from_counts(row_key, total_rows, expected_root_clusters, cluster_extractor, observed_clusters, available_at_envelope)`
is the streaming-writer-friendly variant of `record_captured`. Accepts `total_rows` (int) + `cluster_counts`
(`observed_clusters` mapping) + `available_at_envelope` (UTC timestamp) instead of a pandas DataFrame — used by
streaming writers (PartitionedTickWriter et al) that need to satisfy the BUNDLED_DATA_TYPES cluster validation gate
without reconstructing per-row DataFrames at finalize time. Internally calls the same `_check_cluster_coverage` private
gate + `assert_available_at_present` on the envelope timestamp + writes the manifest row. Failure modes mirror
`record_captured`: under-coverage → `record_failed(ClusterCoverageError)`, missing/null envelope → `LookaheadBiasError`,
empty observed → `record_empty(SOURCE_RETURNED_ZERO)`. 11 unit tests at
`tests/unit/test_manifest_writer_record_captured_from_counts.py` cover full-coverage success, under-coverage routing,
None/NaT/naive envelope, total_rows=0, unknown row_key column, multiple-call idempotency, non-UTC tz acceptance,
feature_group sibling-presence guard, attempted_at honored. Long-term plan deletes the legacy `add()` path entirely once
every bundled-shard callsite migrates (Wave-2 Phases 3-4); reviewers reject any new `add()` callsite for bundled
data_types post-migration.

**Bundled data_types (cluster validation mandatory):**

- `options_chain` — registry: `OPTIONS_CLUSTERS` (ES.OPT 11-cluster taxonomy seed; lifted from instruments-service to
  UAC).
- `futures_chain` — registry: `FUTURES_CLUSTERS` (ES + MES seeds; per-root spreads/butterflies; greenfield).
- `prediction_canonical_question_group` — registry: `PREDICTION_GROUPS` (per-canonical-group expected market_ids per day
  by cadence; populated by predictions Plan A Phase 1A; empty placeholder until then; cluster guard fires loud if used
  before populated).
- `ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ARBITRAGE` (sports per-fixture-bundle data_types) — registry:
  `SPORTS_FIXTURE_CLUSTERS` (per-league-tier expected bookmaker sets; tier-1 EU football seed; expand per follow-up).

**Multi-source merge** (Plan D, deferred): Phase 1B writegate seeds `SOURCE_PRIORITY` top-entry-only per
`(asset_group, data_type)`. Plan D extends to multi-source merge with per-field provenance tracking
(timestamp-availability > coverage > info-richness > merge-different-fields tie-breakers per user direction 2026-05-06).
Until Plan D lands, ranking is single-source per pair.

**Predictions migration** (Plan A): Polymarket adapter migrating from `data_type=<base_asset>`
(BTC/ETH/SPX/FOOTBALL/OTHER) → `data_type=prediction_canonical_question_group` with shard atom
`(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)`.
**`market_id` is a row-level column inside the parquet, NOT a hive-partition shard axis** (per the
[canonical banner above](#multi-axis-correction-banner-canonical)) — HOURLY (24/day), DAILY, ELECTION groups all roll up
to one manifest row per `(canonical_question_group, day)`; per-market detail at drill-down from parquet. Per-market
lifecycle (`market_created_at` / `resolution_time` / `settlement_time`) captured in instruments-service. MTDS respects
lifecycle bounds. LookaheadBiasError per-market-aware. Per-market_id cluster validation lives INSIDE the per-(cqg, day)
parquet via UAC `PREDICTION_GROUPS` + UTL `MissingClusterValidationError`. Until Plan A lands, Polymarket continues to
write per-base_asset shards; the data_type slot in BUNDLED_DATA_TYPES is reserved.

**Sports per-(league, day) sharding** (writegate plan Phase 2.B + multi-axis correction banner above): all sports
data_types — fixture-native (`ODDS_SNAPSHOT`, `ODDS_MOVEMENT`, `ARBITRAGE`, `FIXTURE_STATS`, `FIXTURE_EVENTS`,
`FIXTURE_LINEUPS`, `FIXTURE_PLAYER_STATS`, `INJURIES` when fixture-scoped) AND day-aggregate (`STANDINGS`, `LEAGUES`,
`TEAMS`, etc.) — shard at `(asset_group=sports, source, data_type, league_id, day)`. **`fixture_id` is a row-level
column inside the parquet, NOT a hive-partition shard axis** (per the
[canonical banner above](#multi-axis-correction-banner-canonical)) — per-fixture detail at drill-down comes from reading
the parquet rows, not from a separate manifest row. Avoids ~10× manifest inflation. Per-fixture cluster validation
enforced via UAC `SPORTS_FIXTURE_CLUSTERS` + UTL `MissingClusterValidationError` (see banner) — clusters are checked
INSIDE the per-(league, day) parquet at write time. ML predictions remain fixture-level because features-sports-service
reads the parquet rows.

**`available_at` stamping per source** (writegate plan Phase 1B `AVAILABILITY_AT_SEMANTICS` registry):

| `(asset_group, data_type)`                                                                         | Semantic                                          | Notes                                                                                                                                                                          |
| -------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `(sports, FIXTURES)`                                                                               | `announced_at`                                    | Currently low-confidence `kickoff_utc − 7d` fallback; named successor `sports_forward_poll_timestamps_2026_<TBD>.plan.md`                                                      |
| `(sports, FIXTURE_LINEUPS)`                                                                        | `kickoff_utc − 60min`                             | Conservative — actual is at LEAST 60min before, often 1-2h                                                                                                                     |
| `(sports, FIXTURE_EVENTS)`                                                                         | per-row `event_time`                              | Derived from `kickoff_utc + elapsed_min × 60s`                                                                                                                                 |
| `(sports, INJURIES)`                                                                               | per-row `report_time` / `occurrence_time`         | Currently low-confidence `kickoff_utc − injury_lead_time_estimate` fallback; named successor as above                                                                          |
| `(sports, FIXTURE_STATS)` / `(sports, FIXTURE_PLAYER_STATS)`                                       | `match_end_time`                                  | Detected via cascade: api_football native → SFI progressive-stats freeze (re-uses halftime detector) → footystats / understat → low-confidence `kickoff_utc + 120min` fallback |
| Sports reference (8 tables: players, venues, leagues, teams, referees, coaches, standings, rounds) | `fetch_completed_at`                              | From `_FETCH_COMPLETED_AT` cache in `_fetch_runner.py` (writegate Phase 2.C)                                                                                                   |
| `(prediction, prediction_canonical_question_group)`                                                | per-row `tick.timestamp + scrape_latency`         | Live = batch — same as live pipeline arrival                                                                                                                                   |
| `(prediction, MARKET_LIFECYCLE)`                                                                   | `market_created_at`                               | We couldn't have known about the market before it was listed                                                                                                                   |
| CeFi / DeFi / TradFi tick-level data                                                               | `tick.timestamp + source_priority_scrape_latency` | Live = batch                                                                                                                                                                   |
| Weather forecasts                                                                                  | forecast-issue-time                               | Distinct from forecast-target time                                                                                                                                             |

## Schema v8 (current; ratified 2026-05-09)

The schema has evolved through six published revisions: v4 → v5 (honest-coverage Phase A, 2026-04-19) → v6
(quote_margin_combo plan, 2026-04-23) → v7 (sports `fixture_id` + ML/strategy/execution `job_id`, UTL@`ed658e9b`) → v8
(maximalist final gate per
[`manifest_schema_final_gate_2026_05_09.md`](../../plans/active/manifest_schema_final_gate_2026_05_09.md):8-15) which
adds 3 emission-tracking columns: **`service_emission_state`** (closed-set `ServiceEmissionStateEnum`:
`PUBLISHED_OK` / `PUBLISHED_DEGRADED` / `STALE_DATA_HEARTBEAT_ONLY` / `BLOCKED`), **`last_emission_decision_at`**
(ISO-8601 UTC timestamp of the most recent `publish_with_policy()` decision for this row), and
**`expected_window_completeness_fraction`** (0.0-1.0 fraction of the expected per-row window that was actually
populated; denominator-aware coverage metric; renamed from `_pct` to `_fraction` at UAC@`76f950a` 2026-05-11 per
[`plans/active/issues/expected_window_completeness_pct_range_drift_2026_05_11.md`](../../plans/active/issues/expected_window_completeness_pct_range_drift_2026_05_11.md)
option (a) — value range is 0-1 fraction, not 0-100 percentage; aligns with UTL `completeness_fraction` arg
convention). The `pipeline_mode` column shipped earlier as part of the
`gcs_migration_bundle_pipeline_mode_2026_05_08` work and is preserved in v8. v7 is **legacy (in-flight migration; 30-day
grace window per the final-gate plan)** — `read_availability_index()` backfills missing v8 columns to defaults until the
~2026-06-15 reader-fallback deletion cutoff. The current runtime SSOT lives in
`unified-trading-library/unified_trading_library/manifest_writer.py` — `MANIFEST_SCHEMA_VERSION = 8` and the
`AvailabilityRecord` dataclass.

```python
MANIFEST_SCHEMA_VERSION = 7

@dataclass
class AvailabilityRecord:
    # ─────────────────────────────────────────────────────────────────────
    # Universal (always populated)
    # ─────────────────────────────────────────────────────────────────────
    date: str                       # YYYY-MM-DD — the date this shard covers
    venue: str                      # tradeable venue/protocol: BINANCE-SPOT, AAVE_V3, PINNACLE
    instrument_count: int           # number of rows/instruments in the shard
    service_name: str               # "instruments-service", "market-tick-data-service", etc.
    written_at: str                 # ISO timestamp — when this manifest entry was written
    schema_version: int = MANIFEST_SCHEMA_VERSION

    # ─────────────────────────────────────────────────────────────────────
    # Market data dimensions (populated by instruments-service, MTDS, MDPS)
    # ─────────────────────────────────────────────────────────────────────
    data_type: str = ""             # trades, book_snapshot_5, odds, swaps, liquidity, etc.
    timeframe: str = ""             # MDPS: 15s, 1m, 5m, 15m, 1h, 4h, 24h, T-24h..T-0
                                    # Features: 1m, 5m, 1h, T-24h..HT (sports horizons)
    league_id: str = ""             # SPORTS only: EPL, BUNDESLIGA, LA_LIGA, etc.
    chain: str = ""                 # DeFi only: ETHEREUM, ARBITRUM, BASE, SOLANA, etc.
    instrument_type: str = ""       # spot, perpetuals, equity, pool, lending, prediction_market
    underlying: str = ""            # Options/futures: BTC, ETH, ES, NQ — base for per-underlying shards

    # ─────────────────────────────────────────────────────────────────────
    # Feature/ML dimensions
    # ─────────────────────────────────────────────────────────────────────
    feature_group: str = ""         # Feature services: momentum, fixture_stats, macro_sentiment, etc.
    model_family: str = ""          # ML: pregame_xg, CEFI_BTC_swing-high_LIGHTGBM_1h_V1, etc.
    training_period: str = ""       # ML walk-forward: "2024-01" (month) or "2024" (season)

    # ─────────────────────────────────────────────────────────────────────
    # Downstream dimensions
    # ─────────────────────────────────────────────────────────────────────
    strategy_id: str = ""           # strategy, execution, PnL services
    client_id: str = ""             # risk-and-exposure service
    instruction_type: str = ""      # execution: TRADE, SWAP, LEND, BORROW, STAKE

    # ─────────────────────────────────────────────────────────────────────
    # Per-instrument identification (Phase 1.9 — zero-fill + canonical IDs)
    # ─────────────────────────────────────────────────────────────────────
    instrument_id: str = ""         # canonical instrument id (matches InstrumentRecord.instrument_key)
    expected: bool = True           # True = shard was expected on this date
    available: bool = True          # False only for zero-fill rows that have no data

    # ─────────────────────────────────────────────────────────────────────
    # v5 — honest-coverage Phase A (2026-04-19)
    # Distinguishes "tried + got nothing" from "tried + failed" from "didn't try".
    # ─────────────────────────────────────────────────────────────────────
    capture_status: str = "captured"    # one of: captured / empty_confirmed / attempted_failed / expected_unattempted
    error_reason: str = ""              # classified failure code for attempted_failed rows
    attempted_at: str = ""              # ISO-8601 UTC start-of-attempt; "" = legacy unknown

    # ─────────────────────────────────────────────────────────────────────
    # v6 — quote_margin_combo plan (2026-04-23)
    # Disambiguates DERIBIT inverse vs linear (BTC-PERPETUAL vs BTC_USDC-PERPETUAL)
    # on the same underlying, and carries multi-leg synthetic instrument metadata.
    # ─────────────────────────────────────────────────────────────────────
    quote_asset: str = ""           # "USD", "USDT", "USDC", "BTC", "ETH", "KRW"
    margin_type: str = ""           # "inverse" (coin-margined) | "linear" (stable-margined) | ""
    combo_type: str = ""            # "call_spread", "iron_condor", "butterfly", "" = non-combo
    leg_weights: str = ""           # JSON: [{"instrument_id": "...", "qty": 1|-1|...}]; "" = non-combo

    # ─────────────────────────────────────────────────────────────────────
    # v8 — pipeline_mode partition (gcs_migration_bundle_pipeline_mode_2026_05_08)
    # Source-and-mode tag per row — every parquet on disk + every manifest
    # row knows whether it was produced by batch (one entry per SOURCE_PRIORITY
    # source) or by live websocket. Closed-set per UAC `PipelineMode` StrEnum;
    # round-trip with `SOURCE_PRIORITY` enforced via test_pipeline_mode.py.
    # See codex/02-data/pipeline-mode-partition.md for the full SSOT.
    # ─────────────────────────────────────────────────────────────────────
    pipeline_mode: str | None = None  # "batch_databento" | "batch_tardis" | … | "live_websocket" | None (pre-migration)

    # ─────────────────────────────────────────────────────────────────────
    # v8 — emission tracking (manifest_schema_final_gate_2026_05_09)
    # Records what the publish-boundary helper decided for this row at the
    # most recent `publish_with_policy()` call. Closed-set 4-value enum per
    # UAC `ServiceEmissionStateEnum`; ratified 2026-05-09; frozen until cutover.
    # ─────────────────────────────────────────────────────────────────────
    service_emission_state: str | None = None  # "PUBLISHED_OK" | "PUBLISHED_DEGRADED" | "STALE_DATA_HEARTBEAT_ONLY" | "BLOCKED" | None (pre-migration)
    last_emission_decision_at: str | None = None  # ISO-8601 UTC timestamp of last publish_with_policy decision
    expected_window_completeness_fraction: float | None = None  # 0.0-1.0 fraction of expected per-row window populated (renamed from _pct at UAC@76f950a 2026-05-11)
```

### Column Rules

- Services write ONLY the columns relevant to their shard dimensions. All others default to `""`.
- **Never overload `venue`** with non-venue data. Use the proper column.
- **`venue` for DeFi** = protocol name only in canonical no-underscore form (AAVEV3, not AAVE_V3 nor AAVEV3-ETHEREUM).
  Chain goes in `chain` column. Legacy underscore forms (AAVE_V3, UNISWAP_V3, …) are canonicalised at write time in UTL
  `manifest_writer._coerce_row_key` + `.add()` via UAC `LEGACY_DEFI_VENUE_ALIASES`; the 2026-05-07 manifest migration
  rewrote 411,620 historical rows in place
  (`market_tick_data_service/scripts/migrate_mtds_defi_legacy_venue_underscore.py`). Read-time fallback removed in
  deployment-api 2026-05-07 (commit 64d2be9). Intentional canonical underscores like `TRADER_JOEV2` survive per UAC
  `ALL_DEFI_VENUES`.
- **`venue` for SPORTS (MTDS)** = individual bookmaker (PINNACLE, BETFAIR_EX, DRAFTKINGS), not "ODDS_API".
- **No `data_source` column.** Track what the data IS (transfers, injuries, odds), not where it came from
  (Transfermarkt, API Football, Tardis). If you swap providers, the manifest stays the same.
- **`capture_status` is canonical** for shard state — `captured` (real data on disk), `empty_confirmed` (source returned
  200 + zero rows; counts in denominator only), `attempted_failed` (exception during fetch; classified via
  `error_reason`).
- **`underlying` vs `instrument_id`** for derivatives: bundled chain shards (options_chain / futures_chain) populate
  `underlying` with the base asset (BTC, ETH) and leave `instrument_id` empty. Per-symbol shards populate
  `instrument_id` and leave `underlying` empty.
- **`quote_asset` + `margin_type`** are required for DERIBIT v6 chain shards (and any future inverse/linear-split venue)
  so the (date, venue, instrument_type, data_type, underlying) primary key extends to (..., quote_asset, margin_type)
  without colliding inverse/linear bundles. Leave both empty for non-derivative or single-margin venues.

### Backward Compatibility

`read_availability_index()` handles older index versions transparently — missing v5/v6/v7/v8 columns are backfilled with
their defaults (`captured` for capture*status, `""` for legacy string columns, `None` for v8 emission columns). No
migration needed for reads. Writes produce v8 entries that coexist with older entries until re-scanned by a `rebuild*\*\_manifest.py` pass. The v7 → v8 reader-fallback chain is bounded — deletion target ~2026-06-15 (30-day grace
window) per the final-gate plan's "no double SSOT" closure rule.

## Per-Service Shard Dimension Matrix

Each service writes a specific subset of columns. "—" means the column is always `""` for that service.

### Layer 1: instruments-service (reference data)

| Category   | venue                                                                                                          | chain                                                                                          | data_type | instrument_type                                               | league_id                         |
| ---------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------- | --------------------------------- |
| CEFI       | BINANCE-SPOT, BINANCE-FUTURES, BYBIT, OKX, DERIBIT, COINBASE, ASTER, HYPERLIQUID, UPBIT                        | —                                                                                              | —         | SPOT_PAIR, PERPETUAL, FUTURE, OPTION                          | —                                 |
| TRADFI     | CME, NASDAQ, NYSE, ICE, CBOE, FX                                                                               | —                                                                                              | —         | EQUITY, FUTURE, OPTION, INDEX, COMMODITY, CURRENCY, BOND, ETF | —                                 |
| DEFI       | AAVE_V3, UNISWAP_V3, UNISWAP_V4, CURVE, BALANCER, COMPOUND_V3, MORPHO, LIDO, DRIFT, KAMINO, ... (30 protocols) | ETHEREUM, ARBITRUM, BASE, OPTIMISM, POLYGON, BSC, AVALANCHE, LINEA, SOLANA, HYPERLIQUID, ASTER | —         | POOL, LENDING, LST, YIELD_BEARING, STAKING                    | —                                 |
| SPORTS     | —                                                                                                              | —                                                                                              | —         | EXCHANGE_ODDS, FIXED_ODDS                                     | league_id (EPL, BUNDESLIGA, etc.) |
| PREDICTION | POLYMARKET, KALSHI                                                                                             | —                                                                                              | —         | PREDICTION_MARKET                                             | —                                 |

> **Removed venues:** OddsJam, PredictIt, Betdaq, and Smarkets have been deleted from all repos (UAC, MTDS,
> execution-service, instruments-service, consumer repos, and UI repos). No manifest rows exist or should be expected
> for these venues. Do not add expected-shard entries for them in UAC registry functions.

> **Hyperliquid and Aster instrument-type guard:** Both venues support perpetuals only. Any attempt to fetch
> `instrument_type=OPTION` or `instrument_type=FUTURE` from these venues raises
> `UnsupportedCapabilityError(venue=..., capability="options")` in the MTDS `BaseOnchainPerpAdapter`.
> instruments-service must apply the same guard at reference-data fetch time. Consequently, **no OPTION or FUTURE
> manifest rows should ever exist for HYPERLIQUID or ASTER** — the data status page treats any such row as a pipeline
> misconfiguration.

### Layer 2: market-tick-data-service (raw market data)

| Category   | venue                                                                                           | chain                                 | data_type                                                                                                                                                                                                          | instrument_type                                | league_id                                                                              |
| ---------- | ----------------------------------------------------------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------- | -------------------------------------------------------------------------------------- |
| CEFI       | BINANCE-SPOT, BYBIT, DERIBIT, OKX, COINBASE, ...                                                | —                                     | trades, book_snapshot_5, derivative_ticker, liquidations, options_chain, futures_chain                                                                                                                             | spot, perpetuals, futures_chain, options_chain | —                                                                                      |
| CEFI \*    | HYPERLIQUID, ASTER                                                                              | —                                     | trades, book_snapshot_5, derivative_ticker, liquidations, perp_funding                                                                                                                                             | **perpetuals only** — see guard note below     | —                                                                                      |
| TRADFI     | CME, NASDAQ, NYSE, ICE, CBOE                                                                    | —                                     | trades, ohlcv_1m, ohlcv_15m, ohlcv_24h, tbbo                                                                                                                                                                       | equity, futures_chain, options_chain, index    | —                                                                                      |
| DEFI       | AAVE_V3, UNISWAP_V3, CURVE, DRIFT, ...                                                          | ETHEREUM, ARBITRUM, BASE, SOLANA, ... | swaps, liquidity, rate_indices, oracle_prices, utilization, rewards, risk_params, gas_fees, lst_rates, perp_funding, tvl                                                                                           | pool, lending, lst                             | —                                                                                      |
| SPORTS     | PINNACLE, BETFAIR_EX, DRAFTKINGS, FANDUEL, CORAL, PADDYPOWER, WILLIAMHILL, ... (~21 bookmakers) | —                                     | ODDS_SNAPSHOT, ODDS_MOVEMENT, ARBITRAGE, FIXTURE_STATS, FIXTURE_EVENTS, FIXTURE_LINEUPS, FIXTURE_PLAYER_STATS, INJURIES (per-fixture); STANDINGS, LEAGUES, TEAMS, REFEREES, COACHES, ROUNDS (day-aggregate)        | —                                              | league_id (rollup); **fixture_id** is the per-fixture shard axis (writegate Phase 2.B) |
| PREDICTION | POLYMARKET, KALSHI                                                                              | —                                     | **`prediction_canonical_question_group`** (post-Plan A) — bundled by canonical_question_group with per-market_id rows. Pre-Plan A: legacy `data_type=<base_asset>` per-market shards (BTC/ETH/SPX/FOOTBALL/OTHER). | prediction_market                              | —                                                                                      |

> **\* Hyperliquid / Aster perpetuals-only guard:** `BaseOnchainPerpAdapter` raises
> `UnsupportedCapabilityError(venue=..., capability="options")` when `instrument_type` is OPTION or FUTURE. The
> instruments-service reference-data adapter applies the same guard. The UAC registry functions
> `get_expected_instrument_types_for_venue()` and `get_expected_data_types_for_venue()` return only
> perpetuals-compatible types for these venues — so the expected-shard denominator is never inflated with option/futures
> rows.

### Layer 2.5: market-data-processing-service (bucketed data)

| Category | venue        | chain  | data_type                                                  | instrument_type                                | timeframe                                        | league_id |
| -------- | ------------ | ------ | ---------------------------------------------------------- | ---------------------------------------------- | ------------------------------------------------ | --------- |
| CEFI     | same as MTDS | —      | trades, ohlcv, book_snapshot_5                             | spot, perpetuals, futures_chain, options_chain | 15s, 1m, 5m, 15m, 1h, 4h, 24h                    | —         |
| TRADFI   | same as MTDS | —      | trades, option_chain, futures_chain, rate_indices          | equity, futures_chain, options_chain           | 15s, 1m, 5m, 15m, 1h, 4h, 24h                    | —         |
| DEFI     | protocols    | chains | swaps, liquidity, rate_indices, oracle_prices, utilization | pool, lending, lst                             | 15s, 1m, 5m, 15m, 1h, 4h, 24h                    | —         |
| SPORTS   | bookmakers   | —      | odds_horizon_bucket                                        | —                                              | T-24h, T-12h, T-6h, T-4h, T-2h, T-1h, T-10m, T-0 | league_id |

#### Combo Shard Key (Phase 4 forward-reference)

Bundle-level combo chains will be tracked at a dedicated shard key. The manifest row for a combo chain shard uses:

| Column            | Value                            |
| ----------------- | -------------------------------- |
| `venue`           | underlying venue (e.g. DERIBIT)  |
| `data_type`       | `COMBO_CHAIN`                    |
| `instrument_type` | `COMBO`                          |
| `chain`           | `""` (CeFi) or chain name (DeFi) |
| `league_id`       | `""` (not applicable)            |

The shard granularity is `venue × underlying × date × data_type=COMBO_CHAIN`, analogous to how `options_chain` shards
are keyed at `venue × underlying × date × data_type=options_chain`. Expected-shard denominator for combo chains comes
from UAC `get_expected_data_types_for_venue(venue)` — the registry must include `COMBO_CHAIN` for venues that support
combo instruments. This section is a forward-reference; implementation is tracked in Phase 4 of the relevant plan.

### Layer 3: Feature Services

| Service                   | feature_group                                                                        | timeframe                           | chain                   | league_id |
| ------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------- | ----------------------- | --------- |
| features-delta-one        | technical_indicators, momentum, volatility_realized, microstructure, moving_averages | 1m, 5m, 1h                          | —                       | —         |
| features-volatility       | options_iv, options_term_structure, futures_basis, futures_term_structure            | 1m                                  | —                       | —         |
| features-onchain          | macro_sentiment, lending_rates, lst_yields, onchain_perps                            | timeframe                           | ETHEREUM, ARBITRUM, ... | —         |
| features-sports           | fixture_stats, injuries, lineups, player_stats, standings, ... (14 groups)           | T-24h, T-12h, T-6h, T-1h, T-10m, HT | —                       | league_id |
| features-calendar         | time_features, economic_events                                                       | —                                   | —                       | —         |
| features-multi-timeframe  | per enabled group                                                                    | 1m, 5m, 1h, 4h, 1d                  | —                       | —         |
| features-cross-instrument | regime_detection, cross_venue_spreads, realized_implied_vol, cross_asset_correlation | 1h                                  | —                       | —         |
| features-commodity        | commodity names (WTI_CRUDE_OIL, etc.)                                                | —                                   | —                       | —         |

**Sports feature horizons note:** Not all features are available at all horizons:

- T-24h: historical stats, early odds, predictive lineup (based on prior fixtures + known injuries)
- T-6h: odds velocity between T-24h and T-6h now known
- T-1h: actual lineup confirmed (UEFA/FA announce 60-75 min before kickoff)
- T-10m: sharp money peaks, final odds movement, late CLV
- HT: first-half live stats, in-play odds, current score

### Layer 4: ML Services

| Service                        | model_family                                                    | training_period                                                              |
| ------------------------------ | --------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| ml-training (CEFI/TRADFI/DEFI) | {CATEGORY}\_{SYMBOL}\_{target}\_{algo}\_{timeframe}\_V{version} | Walk-forward month: "2024-01", "2024-02", ...                                |
| ml-training (SPORTS)           | pregame_xg, pregame_clv, ht_xg, ht_clv, meta (5 families)       | Walk-forward season: "2019", "2020", ..., "2024" (expanding window, 5 folds) |
| ml-inference                   | Same model_family references                                    | — (daily predictions)                                                        |

**Sports ML:** ONE global model per family (league is a categorical feature, NOT separate models per league). 7
horizon-specific models across 5 families. Seasonal expanding window walk-forward. Quarterly retrain.

### Layer 5-8: Downstream Services

| Layer | Service                   | strategy_id | venue                                      | client_id | instruction_type                 |
| ----- | ------------------------- | ----------- | ------------------------------------------ | --------- | -------------------------------- |
| L5    | strategy-service          | strategy_id | —                                          | —         | —                                |
| L6    | execution-service         | strategy_id | execution venue (BINANCE-FUTURES, BETFAIR) | —         | TRADE, SWAP, LEND, BORROW, STAKE |
| L7    | risk-and-exposure-service | —           | —                                          | client_id | —                                |
| L8    | pnl-attribution-service   | strategy_id | —                                          | —         | —                                |

Position-balance-monitor is DB-backed (PostgreSQL), not GCS. It does not write to the manifest — it is monitored via
health checks, not data status.

## Data Status Page Tree Hierarchy

The deployment-ui renders a hierarchical tree per service × category. The tree structure is determined by which manifest
columns are populated.

| Service + Category      | Tree                                                     |
| ----------------------- | -------------------------------------------------------- |
| instruments CEFI/TRADFI | venue → dates                                            |
| instruments DEFI        | chain → protocol(venue) → dates                          |
| instruments SPORTS      | league → dates (fixture count)                           |
| instruments PREDICTION  | venue → dates                                            |
| MTDS CEFI/TRADFI        | venue → instrument_type → data_type → dates              |
| MTDS DEFI               | chain → protocol(venue) → data_type → dates              |
| MTDS SPORTS             | league → bookmaker(venue) → dates                        |
| MTDS PREDICTION         | venue → data_type → dates                                |
| MDPS CEFI/TRADFI        | venue → instrument_type → data_type → timeframe → dates  |
| MDPS DEFI               | chain → protocol(venue) → data_type → timeframe → dates  |
| MDPS SPORTS             | league → timeframe(horizon) → dates                      |
| Features (all)          | feature_group → [timeframe →] [chain →] [league →] dates |
| ML training             | model_family → training_period → dates                   |
| ML inference            | model_family → dates                                     |
| Strategy                | strategy → dates                                         |
| Execution               | strategy → venue → instruction_type → dates              |
| Risk                    | client → dates                                           |
| PnL                     | strategy → dates                                         |

**DeFi grouping toggle:** The UI provides a dropdown to switch between chain→protocol and protocol→chain grouping.

## Availability % Calculation

```
availability_pct = found_shards / expected_shards × 100
```

### Expected Shards (Denominator)

The denominator comes from **UAC only**. Never hardcoded in services.

| Dimension                 | UAC function                                                 | What it returns                                  |
| ------------------------- | ------------------------------------------------------------ | ------------------------------------------------ |
| Venue start date          | `VenueMapping.get_venue_start_date(venue)`                   | When a venue's data begins                       |
| Chain start date (DeFi)   | `get_venue_chain_start_date(venue, chain)`                   | When a protocol deployed on a chain              |
| Data type start date      | `get_venue_data_type_start_date(venue, data_type)`           | When a specific data type became available       |
| Expected trading dates    | `VenueMapping.get_expected_trading_dates(venue, start, end)` | Trading days only (excludes weekends for TradFi) |
| Fixture calendar (SPORTS) | `get_league_fixture_calendar(league_id, start, end)`         | Dates with actual fixtures                       |
| Expected data types       | `get_expected_data_types_for_venue(venue)`                   | Which data types a venue should produce          |
| Expected instrument types | `get_expected_instrument_types_for_venue(venue)`             | Which instrument types a venue should produce    |
| Expected bookmakers       | `get_expected_bookmakers()`                                  | Audited bookmakers with start dates              |
| Expected feature groups   | `get_expected_feature_groups_for_service(service)`           | Feature groups per service                       |
| Expected timeframes       | `get_expected_timeframes_for_service(service, category)`     | Timeframes per service+category                  |

### Sparseness

Not all shards are expected every day:

- **Sports fixtures:** A day with no fixtures in a league is NOT a missing shard. Denominator = fixture calendar.
- **TradFi weekends:** Saturday/Sunday are not trading days. Denominator = trading calendar.
- **Transfer windows:** Transfer data arrives on seasonal cadence, not daily.
- **Chain start dates:** AAVEV3 on LINEA started much later than on ETHEREUM. Per-chain start dates.
- **New venues/bookmakers:** A bookmaker added in 2025-06 has no expected data before that date.

### Source coverage start dates (canonical) — `SOURCE_COVERAGE_START` SSOT

> **Runtime SSOT**: `unified_api_contracts.sports.SOURCE_COVERAGE_START` (+ per-`(source, data_type)` overrides in
> `DATA_TYPE_COVERAGE_START`). This codex table is the **canonical literal-values mirror** — every other codex doc
> references this section, never redeclares the dates. If UAC moves, update this table in lockstep; downstream docs
> auto-stay-correct because they cross-link.

Sources have launch dates. Data-status must clip pre-launch dates from expected denominators or those days falsely
render as `missing`. Adapters use `clip_dates_to_source_coverage(source, start, end, data_type=...)` and pass
`source_key=` through helpers like `_sports_expected_dates_for_league`.

| Source                            | `data_types` covered                                         | `coverage_start` |
| --------------------------------- | ------------------------------------------------------------ | ---------------: |
| `api_football`                    | LEAGUES, TEAMS, VENUES, FIXTURES, INJURIES, STANDINGS        |       2018-01-01 |
| `api_football` (override)         | FIXTURE_EVENTS, FIXTURE_LINEUPS, FIXTURE_STATS, PLAYER_STATS |       2020-06-06 |
| `footystats`                      | MATCHES, footystats_odds, footystats_predictions             |       2019-01-01 |
| `understat`                       | XG                                                           |       2015-01-16 |
| `transfermarkt`                   | PLAYER_VALUES                                                |       2019-01-01 |
| `soccer_football_info` (override) | SFI_PROGRESSIVE_STATS                                        |       2020-01-01 |
| `open_meteo`                      | WEATHER                                                      |       2019-03-02 |
| `odds_api`                        | odds (MTDS `odds_horizon_bucket`)                            |       2020-06-06 |
| `mdps_odds_horizon_bucket`        | bucketed odds movement                                       |       2020-06-06 |

**Per-`(source, data_type)` overrides** live in `DATA_TYPE_COVERAGE_START`. Currently:

- `("soccer_football_info", "SFI_PROGRESSIVE_STATS") = 2020-01-01` — SFI's progressive endpoint returns empty for every
  match before this date (probed 2026-04-30).
- `("api_football", {FIXTURE_EVENTS, FIXTURE_LINEUPS, FIXTURE_STATS, PLAYER_STATS}) = 2020-06-06` — endpoints have data
  back to 2017-10 per live probes 2026-05-01 but our backfill never captured 2018–2020 due to pre-flight skips, and
  downstream `odds_api` also starts 2020-06-06 so pre-cutoff per-fixture data has no trading value.

**Documented date-range gaps** (provider outages, paused leagues) go in `KNOWN_COVERAGE_GAPS` (currently empty) and are
filtered by `is_in_known_gap(source, data_type, iso_date)` — data-status drops them from the denominator and the
orchestrator pre-skips them so VMs don't waste rate-limit quota grinding through known-empty range.

### Data Freshness

The `written_at` column records when each manifest entry was written. This enables:

- **Point-in-time queries:** "What data existed as of 2026-04-10 08:00 UTC?" — filter by `written_at <= timestamp`.
  Critical for reproducible backtests.
- **Staleness detection:** Shard exists but `written_at` is old — may indicate stale data.
- **Monitoring:** "What was written in the last 24h?" — freshness dashboard.

The data status page supports an `as_of_timestamp` parameter for point-in-time views.

### Expected-Empty vs Missing Shards (Phase 1.9)

The v6 schema carries enough columns to encode the four distinct states a shard can be in on a given day. The
`capture_status` column (added in v5, honest-coverage Phase A) is the canonical source — `expected` / `available` /
`instrument_count` are kept for backward compat but `capture_status` is what the data-status UI + phantom audit read
first.

| State                | Manifest row? | `capture_status`   | `instrument_count` | Meaning                                                                                                                                                                                               |
| -------------------- | ------------- | ------------------ | ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Ingested**         | yes           | `captured`         | `> 0`              | Real parquet on disk at the canonical path. Counts toward numerator.                                                                                                                                  |
| **Expected-empty**   | yes           | `empty_confirmed`  | `= 0`              | Source returned 200 + zero rows on this date (paused league, dated future not yet trading, lending market with no activity). Counts in denominator only.                                              |
| **Attempted-failed** | yes           | `attempted_failed` | `0`                | Adapter raised an exception classified via `error_reason`. Counts in denominator + triggers alerts. The orchestrator's `_should_skip_shard` does NOT skip these — they auto-retry on the next VM run. |
| **Missing**          | no row        | —                  | —                  | Never attempted — pipeline gap. Counts in denominator; triggers alerts. The phantom audit flips manifest rows whose `captured` claim has no matching parquet on disk to `attempted_failed`.           |

Before Phase 1.9 + Phase A we could not distinguish empty-vs-failed-vs-missing — any day without a manifest entry looked
identical whether the source was silent or the pipeline had never run. `write_with_zero_fill`

- `capture_status` together close that gap. The phantom audit
  (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` — multi-asset-group; the older
  `reconcile_phantom_manifest_rows.py` is sports-only) is the inverse process: scans canonical GCS paths, compares vs
  `captured` rows, flips drift to `attempted_failed`.

### Phantom audit — re-runnable recipe

**Script SSOT:** `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` (multi-asset-group; the older
`reconcile_phantom_manifest_rows.py` is sports-only and being phased out).

**Seven drift axes the audit handles** (each one historically caused a wave of false-positive phantoms):

1. **Hive-vocab drift** — `category=` (legacy) vs `asset_group=` (post-2026-04 rename) coexist on disk; both probed.
2. **`instrument_type` casing** — manifest holds `PERPETUAL` / `perpetual` interchangeably; disk only has lowercase.
   Membership check is case-insensitive.
3. **Empty `instrument_type`** — schema-4 manifest rows omit the segment; audit accepts any disk `instrument_type`.
4. **Path-prefix drift** — Tardis/DeFi adapter writes via `build_*_partition_path` historically lived at top-level
   `day=*/...` while orchestrator-direct writes used `raw_tick_data/by_date/day=*/...`. UAC `77abd56` + MTDS `2a479ef`
   unified writes to the canonical prefix going forward; the rekeyer
   `instruments-service/scripts/migrate_rogue_root_to_raw_tick_data.py` relocates pre-existing rogue data. Audit probes
   both shapes as a safety net.
5. **Chain-bundle equivalence** — manifest `instrument_type=option` / `future` (row-level) vs disk `options_chain` /
   `futures_chain` (writer bundles them per `tardis_shared.finalise_rows_and_path`); audit accepts either form.
6. **DeFi protocol-name underscore drift** (added 2026-05-07 — C.9 audit) — manifest spells protocols as `AAVEV3` /
   `UNISWAPV3` / `COMPOUNDV3` (post-canonicalisation, no underscore between protocol and version). Pre-2026-04 writers
   used the underscored form `AAVE_V3` / `UNISWAP_V3` / `COMPOUND_V3`. Both spellings coexist on disk under different
   `venue=` segments. The audit probes both via `_defi_protocol_variants` (a regex transform inserting/removing the
   underscore between the alphabetic prefix and the `V<digits>` version suffix). **Reference incident**: 2026-05-07
   AAVEV3 dry-run reported 29,782 phantoms (the entire AAVEV3 dataset) BEFORE this axis was added. After: 0 phantoms.
7. **DeFi migrated-bundle wildcard** (added 2026-05-07 — C.9 audit) — `migrate_mtds_defi_legacy_venue_underscore.py`
   produced `ticks_migrated_*.parquet` bundle files at the combined-venue prefix
   (`raw_tick_data/by_date/day=*/asset_group=defi/venue=PROTOCOL-CHAIN/`) WITHOUT the trailing
   `instrument_type=*/data_type=*/` segments. The bundle holds ALL data*types for that (date, protocol, chain) tuple in
   one parquet. The audit's standard `data_type={dt}/` substring check fails because the bundle path has no such
   substring; the wildcard accepts any `ticks_migrated*\*.parquet` file under a matching combined-venue prefix as
   evidence of capture for any (data_type, instrument_type). DeFi-only — the migration bundle pattern is not used by
   other asset_groups.

**Plus**: schema-v4 vestigial empty-data_type rows are filtered out of audit scope (informational pre-v5 markers, not
real shards).

**How to re-run** (must run on a same-region GCE VM — cross-region listing is 18× slower):

```bash
# 1. Spin up an e2-standard-4 VM in asia-northeast1-c (same region as the bucket)
gcloud compute instances create cefi-phantom-audit-$(date +%Y%m%d-%H%M) \
    --project=central-element-323112 --zone=asia-northeast1-c \
    --machine-type=e2-standard-4 \
    --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud \
    --boot-disk-size=50GB --scopes=cloud-platform

# 2. SSH in and bootstrap (project requires Python 3.13 — Ubuntu 24.04 ships 3.12)
gcloud compute ssh cefi-phantom-audit-$(date +%Y%m%d-%H%M) --zone=asia-northeast1-c --tunnel-through-iap --command='
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt-get update -qq && sudo apt-get install -qqy python3.13 python3.13-venv python3.13-dev
mkdir -p /tmp/repos && cd /tmp/repos
gsutil -q cp gs://deployment-scripts-central-element-323112/code/instruments-service-code.tar.gz .
tar xzf instruments-service-code.tar.gz -C instruments-service
cd instruments-service
python3.13 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet pandas pyarrow google-cloud-storage requests   # minimal deps; no UAC needed
.venv/bin/python scripts/reconcile_phantom_manifest_rows_all.py --asset-group cefi --dry-run --workers 64
'

# 3. After verifying the phantom count is reasonable, drop --dry-run to actually flip
#    rows to attempted_failed.  The script is idempotent — re-running on a clean
#    manifest is a no-op.
```

**Always **start with `--dry-run`. Compare phantom count vs prior run; investigate distribution by venue/data_type
before flipping.

**Connection-pool warning**: the script bumps the GCS HTTP pool to `2 × workers` (default 10 silently truncates
`list_blobs()` results under high concurrency — this caused 9,757 false-positive phantoms in the 2026-05-04 audit before
the fix landed).

**Asset-group cross-cuts**: the script supports `cefi`, `defi`, `tradfi`, `prediction`, `sports` via `--asset-group`.
DeFi has additional drift axes (legacy `venue=PROTOCOL-CHAIN/` overload, no-asset-group hive segment); prediction has
the 9-segment Polymarket layout. Both are encoded in `ASSET_GROUP_CONFIG.prefix_tpls`.

**History benchmark**: 2026-05-04 cefi audit reduced phantom count from 130,897 (false-positive baseline pre-fixes) →
354 real (99.7% reduction). Real phantoms were flipped to `attempted_failed` so backfill VMs auto-retry. **2026-05-07
defi audit (C.9)** reduced AAVEV3 false-positives from 29,782 (entire dataset, would have destroyed all manifest state
if `--apply` had run) → 0 after axes 6 + 7 landed.

### Audit-script gotchas — adapter-specific path duality

Per-adapter quirks future audits MUST handle to avoid false-positive flips destroying real data:

- **Polymarket dual-schema** —
  `instruments-service/instruments_service/reference_data/adapters/prediction/polymarket.py` writes parquets at TWO path
  shapes depending on the adapter code path:
  1. **Question-format** (legacy): the file_stem is the human-readable question text
     (`will-bitcoin-cross-100k-by-end-of-2024.parquet`).
  2. **Canonical-ID format** (current): the file_stem is the Polymarket condition_id hex. Both are valid; the audit
     script must probe BOTH layouts before flagging a manifest row as phantom. Reference incident (plan
     `instruments_to_100pct_eod_2026_05_04.plan.md` lines 2540, 2659, 2692): a Phase-1 audit pass that only knew about
     the question-format would have destroyed 401 legitimate canonical-ID rows. Word-boundary keyword matchers in audit
     scripts must also handle this — `arch*` was over-aggressive across the question-format text and flagged 388
     legitimate market records before being narrowed (commit `b336834` word-boundary fix + `d7bd17f` hybrid
     long-form/short-ticker matcher). Always probe + assert on a sample BEFORE running `--apply`.
- **Sports per-league subpartition fallback** — `entity={F}/league={L}/{F}.parquet` first, bare `entity={F}/{F}.parquet`
  fallback (per `unified_api_contracts.sports.candidate_parquet_paths`). Same SSOT, two on-disk shapes; the canonical
  helper returns the ordered probe list.
- **PLAYER_VALUES per-day-per-season layout** — Transfermarkt team values land in ONE bulk parquet per (date, season) at
  `entity=player_values/season={S}/player_values.parquet`, NOT at the per-league-subpartition path. The `season` segment
  is a real partition dimension because near transfer windows old + new season values legitimately co-exist for the same
  day. Layout token: `SportsPathLayout.PER_DAY_PER_SEASON`. League filtering happens INTRA-FILE on the
  `canonical_league` column. **Reference incident 2026-05-05**: pre-fix UAC had
  `SPORTS_DATA_TYPE_TO_FOLDER["PLAYER_VALUES"] = "transfermarkt_teams"` with `PER_DAY_PER_LEAGUE` — never matched the
  writer; audit false-flagged every captured row as phantom; a band-aid script (`write_player_values_placeholders.py`,
  deleted 2026-05-05) wrote 906 zero-row placeholders to mask the drift. Aligned via UAC `gcs_paths.py` change +
  manifest rebuild (8,937 legacy denorm rows → 15,002 honest captured rows derived from disk truth at
  `entity=player_values/season=*/`). Lock test:
  `unified-api-contracts/tests/unit/sports/test_gcs_paths_player_values.py`. The `candidate_parquet_paths` helper probes
  a 3-year season window when no explicit `season` is passed (covers transfer-window overlap).
- **DeFi venue-overload + chain-bundle + protocol-name underscore + migrated-bundle wildcard** — encoded in
  `reconcile_phantom_manifest_rows_all.py` 7-axis drift handling. Axes 6 (`_defi_protocol_variants` for
  `AAVEV3`↔`AAVE_V3` etc.) and 7 (migrated `ticks_migrated_*.parquet` bundles at the combined-venue prefix accepted as
  capture-evidence for any data_type) added 2026-05-07 — see § "Phantom audit — re-runnable recipe" axes 6 + 7 above.

### Rollup-side metric inconsistency (deployment-api `_data_status_rollup_worker`) — open finding 2026-05-07

**Symptom (per the C.9 wrapper-tracker investigation 2026-05-07)**: the deployment-api offline rollup at
`gs://central-element-323112-data-status-rollups/market-tick-data-service/full.json.gz` emits per-(combined-venue) DEFI
entries where `dates_found` is non-zero for venues that have ZERO rows in the canonical manifest. Example:

```
AAVEV3-ARBITRUM dates 31/6072 (0.51%) capture_status_counts={captured: 0, empty_confirmed: 0, attempted_failed: 0}
```

`dates_found = 31` but `capture_status_counts` is all-zero — a contradiction. The canonical manifest has zero
`(venue=AAVEV3, chain=ARBITRUM)` rows; all 29,782 AAVEV3 rows are on chain `ETHEREUM`. The "31" is a stale or
miscomputed value coming from a different source than `capture_status_counts`.

**Likely cause**: the rollup worker's per-(combined-venue) computation conflates the EXPECTED denominator window
(clipped to chain genesis per `_mtds_expected_dates_cached`) with the FOUND-on-disk count, OR a stale per-VM shard
reference, OR a default initialisation that was never overwritten when the manifest had zero rows for that combo.

**Impact**: deployment-ui shows misleading per-(venue, chain) progress bars (e.g. AAVEV3-ARBITRUM "0.51% complete"
implies SOME data exists; reality is none). Operators waste time investigating phantom progress that has no on-disk
evidence and no manifest evidence.

**Action**: file under `infrastructure_master_2026_05_07.md` § Data-status multi-axis follow-up — the rollup worker must
derive `dates_found` from the same source as `capture_status_counts` (the manifest), not from the expected denominator.
Without this, every per-(combined-venue) figure for a chain that has no manifest rows is misleading. Owner: data-status
multi-axis stream.

When adding a new adapter, document any path duality here BEFORE merging the writer — silent dual-schemas are the
canonical phantom-audit blast radius.

### Rollup-vs-drilldown denominator divergence (codified 2026-05-07)

**Two code paths, two denominators.** The data-status panel surfaces TWO percentages that operators can see diverge, and
the divergence is by-design (not a bug) — but the workspace is closing it via writegate Phase 2.E.2.

| Layer                    | Code path                                                                                                   | Source                                                                                                        | Denominator                                                                                                                                                                                      |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Top-level (panel header) | [`_slice_rollup_to_window`](../../../deployment-api/deployment_api/services/data_status_service.py)         | Offline rollup blob (`gs://central-element-323112-data-status-rollups/{service}/full.json.gz`); sub-2s slicer | **Pre-computed expected universe** (calendar-clipped per `venue_trading_calendar`, source-coverage-clipped per UAC `SOURCE_COVERAGE_START` / `DATA_TYPE_COVERAGE_START` / `CHAIN_GENESIS_DATES`) |
| Drill-down breakdown     | [`get_hierarchical_drilldown`](../../../deployment-api/deployment_api/services/data_status_hierarchical.py) | Live `read_availability_index(bucket)` — manifest parquet; ~30MB read                                         | **Manifest row count** (only what the writer physically recorded)                                                                                                                                |

**Where they diverge.** Any expected `(shard_key, day)` tuple that has **no manifest row at all** (not `captured`, not
`empty_confirmed`, not `attempted_failed` — just absent) gets counted in the rollup denominator but missed by the
drill-down. Today this happens for:

- **DeFi pre-genesis chain dates** — ARBITRUM pre-2021-08-31, BASE pre-2023-07-13, LINEA pre-2023-07-11, etc. The
  orchestrator pre-skips with no row written.
- **Sports pre-`SOURCE_COVERAGE_START` dates** per-source (api_football pre-2018-01-01, footystats pre-2019-01-01,
  understat pre-2015-01-16, …).
- **Paused-league windows in `KNOWN_COVERAGE_GAPS`** (currently empty registry; will populate over time).
- **TradFi non-trading days** (calendar pre-skip — was emitting no row pre-Phase 2.E.2; partly shipped 2026-05-07).
- **CeFi instruments not yet listed / already delisted** on a given day.

### Why two paths exist (cannot collapse to one)

Operators sometimes ask: "why don't we just use drilldown for both?" The answer is performance + cost asymmetry:

- Rollup: 30MB pre-computed JSON.gz, slicer fast-path, sub-2-second response for full Jan 2018 → today window. Used by
  the panel header that's loaded on every dashboard view.
- Drilldown: live manifest parquet read (~30MB per asset_group), more compute on each request, paginated children. Used
  when an operator clicks into a venue.

Collapsing the panel header onto the drilldown's live-manifest read would 6x the every-page load time. **The canonical
fix is not to merge the paths; the canonical fix is to make their denominators agree** by ensuring the manifest carries
a row for every expected `(shard_key, day)`.

### The fix — writegate Phase 2.E.2 + expected-universe enumeration v2

The closure has two halves, both required:

**Half 1 — Forward-write `record_expected_empty(reason=EXPECTED_*)`** (writegate Phase 2.E.2 — partly shipped
2026-05-07). Every NEW empty case at adapter / orchestrator level emits a manifest row with structured reason instead of
skipping write. Adapter migrations done for sports + cefi + defi + tradfi this session
([`writegate_honest_coverage_endtoend_2026_05_06.md`](../../plans/active/writegate_honest_coverage_endtoend_2026_05_06.md)
Tier 2A/2B/2C/2D/2E + UTL contract Tier 1).

**Half 2 — Backward-fill the expected universe** (SHIPPED 2026-05-07 — PM@79e47874 + PM@341bb285).
`instruments-service/scripts/enumerate_expected_universe.py` (Phase 3.D.4 — instruments-service@8e404c8 / @d1c9928 /
@a936a28) walks the per-asset-group cross-product over UAC SSOTs + service catalogs and writes
`record_expected_empty(reason=EXPECTED_<X>)` rows for every tuple that has no manifest row. **1,455,901 rows written +
merged into canonical** across all 5 asset_groups (TradFi 35,033 + Sports 13,176 + CeFi 119,152 + Prediction 2,280 +
DeFi 1,286,260). The reconciler at `instruments-service/scripts/reconcile_expected_absence_reasons.py` (shipped
2026-05-07 late3) is the complementary pass that stamps reasons on **legacy null-reason rows that already have a
manifest entry**; the enumerator covers the **rows that have no manifest entry at all**. Per-asset-group cross-product:

| Asset group | Expected-universe inputs (UAC + service catalogs)                                                                                                                              |
| ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| DeFi        | `CHAIN_GENESIS_DATES` × instruments-service protocol catalog × `DATA_TYPES_BY_ASSET_GROUP['defi']` × dates                                                                     |
| Sports      | `SOURCE_COVERAGE_START` (+ `DATA_TYPE_COVERAGE_START` overrides) × leagues catalog (with paused-league filtering via `is_in_known_gap`) × `SPORTS_DATA_TYPE_TO_FOLDER` × dates |
| TradFi      | `venue_trading_calendar` × instruments-service catalog × `DATA_TYPES_BY_ASSET_GROUP['tradfi']` × dates                                                                         |
| CeFi        | Instrument lifecycle (`available_from`, `available_to`, `expiry`) × venue × `DATA_TYPES_BY_ASSET_GROUP['cefi']` × dates                                                        |
| Prediction  | Market lifecycle (`market_created_at`, `settlement_time`) × canonical_question_group registry × `DATA_TYPES_BY_ASSET_GROUP['prediction']` × dates                              |

#### Expected-universe enumerator: v1 (shipped) vs v2 (in-flight design)

The enumerator has two grain levels — v1 captures venue-grain coverage; v2 cross-joins the instruments-service catalog
to capture per-instrument lifecycle bounds. Both share the same SSOT inputs (UAC `*_LAUNCH_DATES` /
`*_GENESIS_DATES` / `SOURCE_COVERAGE_START` / `venue_trading_calendar` / `KNOWN_COVERAGE_GAPS`); v2 adds the second SSOT
half (per CLAUDE.md "Two SSOTs for the manifest's expected universe": instruments-service catalog × dates × data_types
cross-product applied at expected-row generation, not just at write-side).

- **v1 (shipped 2026-05-07)** — venue-grain expected universe; ~1.4M rows merged into canonical across all 5
  asset_groups (numbers above). Walks UAC SSOTs to enumerate every `(asset_group, venue, data_type, day)` row that
  SHOULD exist; pre-skips per-source / per-chain / per-calendar windows; emits `record_expected_empty(reason=EXPECTED_*)`
  for everything in the gap. Implementation:
  `instruments-service/scripts/enumerate_expected_universe.py` + per-VM launcher.
- **v2 (in-flight design)** — instrument-grain expected universe; ~190M row estimate. Designed in
  [`expected_universe_v2_design_2026_05_08.md`](../../plans/active/expected_universe_v2_design_2026_05_08.md):39-73
  (folded into `manifest_evolution_master_2026_05_08` umbrella; sequenced AFTER v8 schema in gate G3). v2 cross-joins
  v1's `(asset_group, venue, data_type, day)` axis with the instruments-service catalog's per-instrument lifecycle
  (cefi `available_from` / `available_to`, prediction `market_created_at` / `settlement_time`, defi
  `protocol_launch_date`, sports per-fixture). v2 plan body owns the canonical per-asset-group grain matrix (cefi
  spot/perp per-instrument; cefi options/futures per-root; tradfi futures/options per-root; tradfi ETFs per-instrument;
  defi per-protocol-or-instrument; sports per-fixture for fixture-native data_types; prediction per-canonical_question_group)
  — point at the plan as SSOT for the v2 grain matrix until v2 lands.

### Architectural framing — why `empty_confirmed + EXPECTED_*` is identical to "not_attempted" placeholder

Operators sometimes propose a separate `not_attempted` capture*status to mark expected-but-untouched tuples. The
workspace chose `empty_confirmed + error_reason=EXPECTED*\*` instead. Both are functionally identical — the
denominator-divergence closure depends on the row EXISTING, not on the specific status value:

- **Workspace approach (shipped)**: `capture_status=empty_confirmed`,
  `error_reason=EXPECTED_PRE_GENESIS_CHAIN | EXPECTED_HOLIDAY | EXPECTED_PRE_SOURCE_COVERAGE_START | EXPECTED_PRE_VENUE_LAUNCH | EXPECTED_INSTRUMENT_NOT_LISTED | EXPECTED_WEEKEND | …`.
  Reuses the existing `empty_confirmed` plumbing (downstream services already branch on it for NaN-fills, denominator
  counting). Closed-set reason taxonomy in UAC `EMPTY_CONFIRMED_REASONS` (per CLAUDE.md "Reason taxonomy codified
  2026-05-07"); `EXPECTED_PRE_VENUE_LAUNCH` added 2026-05-07 at UAC@ac218dc with the new
  `unified_api_contracts.registry.venue_launch_dates` SSOT (20 CeFi venues + 2 Prediction venues). Consumer-class
  behaviour documented in [`honest-absence-downstream-handling.md`](honest-absence-downstream-handling.md).

- **Hypothetical "not_attempted" approach**: separate status enum value. Identical effect (manifest carries the row,
  drilldown counts it, rollup denominator matches). Would have required updating every downstream consumer to branch on
  the new status. Net: more code change, same outcome.

The **absence-of-row semantic** ("not in expected universe") is preserved either way. With Half 2 shipped (2026-05-07),
manifest absence now definitively means "outside expected universe" — e.g. a pre-2021-08-31 row for an Arbitrum tuple is
present in canonical with `capture_status=empty_confirmed AND error_reason=EXPECTED_PRE_GENESIS_CHAIN`, so the rollup's
expected denominator counts it as known-empty rather than missing. Spot-check verification 2026-05-07:
`gs://market-data-tick-defi-{pid}/_index/availability_index.parquet` has 688,220 `EXPECTED_PRE_GENESIS_CHAIN` rows
(sample: `chain=ARBITRUM venue=AAVEV3-ARBITRUM day=2018-01-01`). TradFi has 35,050 `EXPECTED_WEEKEND` + 2,427
`EXPECTED_HOLIDAY` rows (sample: `venue=BARCHART day=2018-01-06` — Saturday).

### Mechanism: `ManifestWriter.write_with_zero_fill`

Location: `unified-trading-library/unified_trading_library/manifest_writer.py:329`.

```python
zero_filled = writer.write_with_zero_fill(
    actual_records,                # list[AvailabilityRecord] — rows produced this run
    expected_catalogue=catalogue,  # Iterable[InstrumentRecord] — from instruments-service
    ref_date=date(2026, 4, 17),
    category="cefi",
    venue="BINANCE_FUTURES",
    instrument_type="perpetual",
    chain=None,
    data_type="trades",
)
```

Flow:

1. Delegates to UAC `get_instruments_available_on(ref_date, catalogue, ...)` to compute which catalogue members were
   in-window on `ref_date` under the given scope filters.
2. Any expected instrument (matched by `InstrumentRecord.instrument_key` ↔ `AvailabilityRecord.instrument_id`) that is
   NOT in `actual_records` gets a zero-fill row appended with `instrument_count=0`, `expected=True`, `available=False`.
3. Actual records override — a real ingestion with `instrument_count==0` stays as the caller wrote it; no zero-fill is
   appended for that id.

The `instruments-service` catalogue (see `instruments-service/docs/instrument-catalogue.md`) is the canonical source for
`expected_catalogue`. MTDS, features-\*, and ML services load it via UTL and feed it into their per-shard
`write_with_zero_fill` call.

## Integrity Principles

### 1. Atomic Shard Failure

If ANY item in a shard fails, the ENTIRE shard must fail. `ManifestWriter.add()` is only called after the complete shard
write succeeds. No partial writes, ever.

**Why:** A human looking at the data status page must trust that "shard present = shard complete". Partially written
shards create false confidence.

**Enforcement:** Services validate all items in a shard before writing any. If 1 of 100 instruments in a venue×date
shard fails, write 0 and mark the shard as failed.

### 2. Schema Validation Before Write

`ParquetSchemaEnforcer` runs before every GCS write. Checks: no NaN values, correct column types, required columns
present. Schema failure = shard failure = no write = shows as missing on data status page.

**Why:** Millions of parquet files. No human can inspect them all. Schema validation + atomic shards = confidence
without manual inspection.

### 3. Single SSOT for Registry — UAC Only

What venues exist, what chains exist, what data types exist, what feature groups exist, when each became available — ALL
of this comes from UAC. No service has hardcoded lists. No service tries to get data before a venue's start date.

**Why:** If 5 services have 5 different ideas of when AAVE_V3 on BASE became available, some will try to fetch data that
doesn't exist, and the data status page will show false negatives.

### 4. Write-gate quartet at `record_captured` (post-2026-05-06)

Every `record_captured` call is gated by 4 pillars. Failure of any pillar → `record_failed(<typed_reason>)` instead of
writing the parquet. NO partial passes.

| Pillar                                         | Gate                                                                                                                                                                                                                                                             | Failure mode                                                         |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Row count > 0**                              | Mandatory unless source response was legitimately empty (then `record_empty`, not `record_captured`).                                                                                                                                                            | `record_failed(EmptyAfterFilterError)` for non-honest empties.       |
| **NaN ratio per column < threshold**           | Per-feature-group thresholds in UAC `nan_thresholds.NAN_RATIO_THRESHOLDS`. Currently inlined per-service (instruments-service `_validate_predictions_null_rates` is FootyStats-only); Plan B lifts to UTL `write_gate_helpers.check_nan_ratio` with single SSOT. | `record_failed(NanRatioExceededError(column, observed, threshold))`. |
| **Schema matches contract**                    | Required columns + types match UAC schema declaration. Existing `ParquetSchemaEnforcer`. Includes `available_at` column (per pillar 5 below).                                                                                                                    | `record_failed(SchemaMismatchError(column, expected, observed))`.    |
| **Cluster coverage ≥ expected** (BUNDLED only) | For `data_type ∈ BUNDLED_DATA_TYPES`, `expected_root_clusters` + `cluster_extractor` kwargs are MANDATORY (UTL guard raises `MissingClusterValidationError` if absent; QG STEP 5.64 statically checks). Internal `_check_cluster_coverage` runs at write time.   | `record_failed(ClusterCoverageError(missing, observed))`.            |

This 4-pillar model is the canonical write-gate going forward. Adapters that are post-migration MUST pass each pillar;
pre-migration adapters get phased through Phase 2 of the writegate plan.

### 5. `available_at` per row, write-time, equal to live-pipeline-arrival (post-2026-05-06)

Every shard's parquet contains an `available_at` column. Each row's value = when the live pipeline would have actually
had that row's information per `UAC.AVAILABILITY_AT_SEMANTICS`. NEVER derived at read-time.

`record_captured` calls `assert_available_at_present(df)` internally — missing or null `available_at` →
`LookaheadBiasError`. UTL stamping helpers in `unified_trading_library.availability_stamping`:

- `stamp_available_at_kickoff_offset(df, kickoff_col, minutes=60)` — sports lineups
- `stamp_available_at_post_match(df, kickoff_col, duration_min, scrape_latency_min)` — sports fixture_stats /
  fixture_player_stats
- `stamp_available_at_event_time(df, event_time_col)` — per-row event_time pass-through (fixture_events, injuries when
  in-fixture)
- `stamp_available_at_announcement(df, announced_col)` — fixtures (low-confidence default until forward-poll source
  lands)
- `stamp_available_at_explicit(df, fetch_completed_at)` — sports reference tables, prediction market lifecycle metadata
- `stamp_available_at_tick_plus_latency(df, ts_col, source_key)` — CeFi / DeFi / TradFi / prediction tick-level data;
  latency from `UAC.SOURCE_PRIORITY[(asset_group, data_type)]` top entry

**Live = batch principle**: live and batch produce identical schemas, identical fields, identical timing semantics. Only
the SOURCE differs (some live sources are faster than canonical historical archives). Historical writes stamp
`available_at` with the live-pipeline-equivalent arrival time, NOT the historical archive's slower archive time. Banned:
separate live-only data_types like `LINEUPS_PRE_MATCH` vs `LINEUPS_POST_MATCH`; field sets that diverge between live +
batch parquets.

### 6. Three-category empty-output decision tree (post-2026-05-06)

Every condition that could produce an empty result resolves to ONE of:

| Path                                | Condition                                                                              | Manifest verb                                                                      | Notes                                                                                                                                                                                                                                                           |
| ----------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A. Honest absence**               | Source returned 0 ticks for the requested window.                                      | `record_empty(row_key, attempted_at)`                                              | Counts in denominator only.                                                                                                                                                                                                                                     |
| **B. Upstream timestamp bias**      | Source returned ticks; ALL fall outside the requested day after `interval_idx` filter. | `record_failed(UpstreamTimestampBiasError(observed_dates, expected_day, n_ticks))` | UPSTREAM bug — partition mislabeled at MTDS write-time, OR source replay covered wrong window, OR clock-skew. Paired upstream MTDS partitioner-validation fix (writegate Phase 2.B) at `raw_tick_hive.py`: `assert tick.timestamp.date() == day_partition_key`. |
| **C. Mid-process malformed fields** | Rows in window but downstream calc dropped due to NaN/malformed source fields.         | `record_failed(MalformedTickFieldError(field, n_dropped, sample_values))`          | Data-quality bug worth diagnosing — adapter author surfaces sample values for triage.                                                                                                                                                                           |

**NO fourth category. NO silent NaN placeholder rows.** The `_create_empty_output()` method is BANNED from
`base_adapter` and equivalents (writegate Phase 2.A deletes it across MDPS' 37 callsites). Reference incident
**2026-05-05**: MDPS produced 1440-row NaN OHLC parquets per (venue, data_type, day) for years; manifest said
`captured`; downstream features computed garbage on garbage. The post-plan contract makes this bug class structurally
impossible.

**Downstream-consumption SSOT** (what feature calcs / ML / strategy do when they READ an `empty_confirmed` row):
[`honest-absence-downstream-handling.md`](honest-absence-downstream-handling.md). Short version: NaN-handle per the
consumer's modeling tolerance (tree-based ML, rank allocators, bounded forward-fill, drop-with-min-rows). Never
fabricate placeholder rows, never `fillna(0)` at calc boundaries, never use sentinels. Pre-flight gates are per-service.

**NEW BUG SURFACED (Phase 0 audit 2026-05-06)**: orchestrator prediction empty path at `live_workers.py:268-271` returns
`success=True, candles_generated=0` with NO manifest record (no `record_empty`, no `record_captured`, no
`record_failed`). Distinct from 1440-NaN class but equally opaque. Fix in writegate Phase 2.A scope expansion — adds
`record_empty(row_key)` so prediction empties surface as honest absence.

### 7. Per-VM shard isolation for concurrent backfills (workspace rule, codified 2026-05-06)

Every multi-worker backfill (multiple chunk processes locally OR multiple GCE VMs writing to the same manifest) MUST set
`VM_NAME=<unique>` + `MANIFEST_PER_VM_SHARDS=true` per worker. Manifest consolidator merges per-VM shards under
`_index/per_vm/{vm_name}.parquet` into the canonical `_index/availability_index.parquet` with last-writer-wins on
identical row_key.

UTL runtime guard: `ManifestWriter.__init__` raises `MultiWorkerWithoutShardIsolationError` when multi-process detection
fires AND per-VM shard isolation isn't set. New base-service.sh QG STEP 5.66 AST-walks launcher scripts that fork
multi-process; asserts envvar setting.

Reference incident **2026-05-04**: instruments-service chunk workers without isolation clobbered each other's manifest
entries (commits `00f6352` + `619a32e` were the per-script fixes; Plan C codifies the workspace rule).

### 8. Temporary state must have named successor plan (workspace rule, codified 2026-05-06)

When a plan ships a partial implementation that is not the final shape, the partial state MUST be documented in a
`## Temporary states + their canonical follow-up plans` section of that plan, with the named successor plan filename
listed. NO temporary state is silently accepted as final. NO "we'll fix it later" without a named doc. Reviewers reject
any partial implementation lacking a successor reference.

Currently-tracked temporary states relevant to the manifest:

- `BUNDLED_DATA_TYPES` slot for `prediction_canonical_question_group` reserved with empty `PREDICTION_GROUPS = {}`
  registry → successor: predictions Plan A.
- `SOURCE_PRIORITY` top-entry-only seed → successor: Plan D multi-source merge.
- `announced_at` / `report_time` / `match_end_time` low-confidence fallback values → successor:
  `sports_forward_poll_timestamps_2026_<TBD>.plan.md`.
- Prediction empty path patched with current Polymarket per-base_asset row_key → successor: predictions Plan A migrates
  to canonical_question_group shape.

## DeFi Protocol × Chain Coverage

30 protocols × 11 chains = 57 venue combos. Key coverage:

| Chain       | Protocol Count | Examples                                                                                 |
| ----------- | -------------- | ---------------------------------------------------------------------------------------- |
| ETHEREUM    | 16             | AAVEV3, UNISWAPV3, UNISWAPV4, CURVE, BALANCER, COMPOUNDV3, MORPHO, LIDO, ETHERFI, ...    |
| BASE        | 8              | AAVEV3, UNISWAPV3, BALANCER, AERODROMEV3, COMPOUNDV3, MORPHO, PANCAKESWAPV3, SUSHISWAPV3 |
| ARBITRUM    | 7              | AAVEV3, UNISWAPV3, BALANCER, COMPOUNDV3, CAMELOTV3, SUSHISWAP, GMX                       |
| AVALANCHE   | 6              | AAVEV3, BALANCER, CURVE, SUSHISWAPV3, TRADER_JOEV2, GMX                                  |
| OPTIMISM    | 6              | AAVEV3, UNISWAPV3, BALANCER, COMPOUNDV3, CURVE, VELODROMEV2                              |
| SOLANA      | 6              | DRIFT, KAMINO, RAYDIUM, ORCA, MARINADE, JITO                                             |
| POLYGON     | 3              | AAVEV3, UNISWAPV3, BALANCER                                                              |
| BSC         | 2              | AAVEV3, PANCAKESWAPV3                                                                    |
| LINEA       | 1              | AAVEV3                                                                                   |
| HYPERLIQUID | 1              | HYPERLIQUID                                                                              |
| ASTER       | 1              | ASTER                                                                                    |

Top multi-chain protocols: AAVEV3 (8 chains), BALANCER (6), UNISWAPV3 (5).

## Sports Bookmaker Venues (~21 Audited)

These are the actual pricing venues for sports odds. "ODDS_API" is the data aggregator, NOT a venue.

**Removed bookmakers:** Smarkets, Betdaq, and OddsJam have been removed from all repos. No manifest rows exist for these
venues and they must not appear in UAC registry functions or expected-shard calculations.

| Bookmaker    | Accuracy            | Execution?                        |
| ------------ | ------------------- | --------------------------------- |
| PINNACLE     | 99% exact           | No (API restricted)               |
| BETFAIR_EX   | Exchange            | **Yes** (current execution venue) |
| FANDUEL      | 100% exact          | No                                |
| CORAL        | 100% exact          | No                                |
| PADDYPOWER   | 100% exact          | No                                |
| WILLIAMHILL  | Audited             | No                                |
| LADBROKES    | Audited             | No                                |
| DRAFTKINGS   | 86% exact           | No                                |
| BETRIVERS    | 92% exact           | No                                |
| BETONLINEAG  | Audited clean       | No                                |
| CASUMO       | 96% exact           | No                                |
| VIRGINBET    | 97% exact           | No                                |
| BETVICTOR    | Audited             | No                                |
| UNIBET       | 66% exact           | No                                |
| SKYBET       | Audited             | No                                |
| BET888SPORT  | Audited             | No                                |
| LIVESCOREBET | Audited             | No                                |
| MATCHBOOK    | Exchange, consensus | Yes (adapter exists)              |
| BETFAIR_SB   | Sportsbook variant  | No                                |
| UNIBET_UK    | Audited             | No                                |

## Migration history

### v3 → v4 (Phase 1 — venue/chain/instrument_type/league_id columns)

- **No data re-downloads.** All data already exists in GCS. The manifest is just an index.
- **GCS paths do NOT need to change.** The manifest is an abstraction layer over GCS paths. Old data stays at old paths
  (e.g., `venue=ODDS_API/league=EPL/`). New manifest entries normalize to v4 columns (venue=PINNACLE, league_id=EPL).
  The deployment-api reads the manifest, not GCS paths. GCS path changes are optional future optimization, not a
  migration requirement.
- **Backward compat in reader:** `read_availability_index()` backfills missing v4 columns with `""`.
- **v4 writes coexist with v3 entries** until re-scanned.
- **Re-scan existing data:** Run `rebuild_*_manifest.py` scripts per service. Scans existing GCS paths, extracts new
  columns from path structure (instrument_type from hive path, chain from folder names), writes v4 index.
- **Dedup on write:** v4 entries supersede v3 entries for the same shard.

### v4 → v5 (honest-coverage Phase A, 2026-04-19)

- Adds `capture_status` (`captured` / `empty_confirmed` / `attempted_failed`), `error_reason`, `attempted_at`.
- Adapters MUST distinguish empty-vs-failed: `record_empty(row_key=...)` for legitimately-zero-rows,
  `record_failed(row_key=..., error=classify_venue_error(exc))` for exceptions.
- Reader backfills missing columns: `capture_status="captured"` (preserves old semantics where presence of a row implied
  success), `error_reason=""`, `attempted_at=""`.

### v5 → v6 (quote_margin_combo plan, 2026-04-23)

- Adds `quote_asset`, `margin_type`, `combo_type`, `leg_weights`.
- The v5 primary key `(date, venue, instrument_type, data_type, underlying)` collided DERIBIT inverse and linear bundles
  into the same parquet (BTC-PERPETUAL vs BTC_USDC-PERPETUAL on the same underlying = BTC). v6 extends the key to
  `(..., quote_asset, margin_type)` so the bundles stay separate.
- Reader backfills `quote_asset=""`, `margin_type=""`, `combo_type=""`, `leg_weights=""` for v4/v5 rows.

## Per-VM shard layout (Phase 1, manifest_429_per_vm_sharding plan)

When `UnifiedCloudConfig.manifest_per_vm_shards` is True (env var `MANIFEST_PER_VM_SHARDS=true`), or when a writer is
constructed with `ManifestWriter(per_vm_shards=True, ...)` — the explicit kwarg added 2026-05-03 — `ManifestWriter`
writes to `_index/per_vm/{instance}.parquet` instead of CAS-writing the canonical `_index/availability_index.parquet`.
The `manifest_consolidator` daemon (Cloud Scheduler `*/1 * * * *`) merges per-VM shards into the canonical view; readers
fall back to a live shard-merge when the canonical blob is older than `MANIFEST_CONSOLIDATED_STALENESS_SEC` (default
120s).

**When to use:**

- Backfill VM fleets with 10+ writers per bucket (eliminates 429 thundering-herd on the canonical CAS path).
- One-off `rebuild_*_manifest.py` scripts: pass `per_vm_shards=True` to skip CAS contention with concurrent rebuilds /
  the consolidator daemon. Without this, OCC `generation_match` retries can re-merge stale views and drop most of the
  rebuild's output (observed 2026-05-02 on DeFi: 80k mid-run rows compacted to 12k canonical).
- Local multi-process rebuilds where every process inherits the same `HOSTNAME` — set a unique `VM_NAME` per chunk
  worker so they each get their own per-VM shard (not a shared one).

**Force-merge after a rebuild:**

```bash
python -m unified_trading_library.manifest_consolidator --bucket market-data-tick-{ag}-{pid}
```

Idempotent + safe to run concurrently with the scheduled cycle.
