---
doc_type: plan
title: Data Pipeline Completion — Instruments → MTDS → MDPS → Features (schema, manifest, backfill, retire, schedule)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-api-contracts,
    unified-trading-library,
    unified-cloud-interface,
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-delta-one-service,
    features-volatility-service,
    features-onchain-service,
    features-sports-service,
    features-calendar-service,
    features-multi-timeframe-service,
    features-cross-instrument-service,
    features-commodity-service,
    ml-training-service,
    ml-inference-service,
    deployment-service,
    deployment-api,
    deployment-ui,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-18
locked_by: live-defi-rollout
locked_since: 2026-04-18
priority: P0
code_readiness: C1
deployment_readiness: D0
business_readiness: B0
completion_gates: { code: C5, deployment: D3, business: B3 }
---

## Deferred work — migrated to: `plans/active/data_completion_to_100_all_ag_2026_06_21.md` — successor:

data_completion_to_100_all_ag_2026_06_21 (verified 2026-07-21, batch-5 archived-plan discipline triage). This plan's
literal implementation is architecturally obsolete (targets manifest schema v4, now at v9; 8 separate
`features-*-service` repos + split ml-training/ml-inference services, now consolidated into single
`features-service`/`ml-service` repos; its bucket-retirement target no longer exists). But its actual GOAL — driving
every asset group's manifest to honest 100% coverage across batch+live — is the direct ancestor of a documented
succession chain: this plan → `path_to_100pct_backfill_mtds_is_2026_06_17` → `data_completion_to_100_all_ag_2026_06_21`
(frontmatter `supersedes:` confirms) → folded 2026-07-13 into per-asset-group children
(`data_completion_cefi/defi/tradfi/prediction_2026_07_15.md`), with observability/cost/event-integrity concerns carried
by `data_pipeline_hardening_self_monitoring_2026_06_22.md` / `data_pipeline_e2e_check_2026_07_10.md` /
`data_pipeline_alerts_batch_remediation_2026_07_15.md`.

# Data Pipeline Completion — Instruments → MTDS → MDPS → Features

## Context

This plan consolidates today's full 3×4 audit (services × categories) and lays out the minimal-delta path to finish the
data pipeline from **instruments-service** through **MTDS**, **MDPS**, **features-\***, and **ml-\*** with:

1. **Correct manifests** (v4 shard dimensions, zero empty-string leaks, zero `"None"` literals, zero orphan rows)
2. **Uniform GCS schemas** per SchemaContract — same bytes on disk as running the current writer with `--force` on the
   same source
3. **Backfill completion** per category × bucket (ODDS_API 54-day hole, CeFi enrichment pass, DeFi full-history, TradFi
   full-history, Polymarket migration)
4. **Cost-of-service** visibility — GCS lifecycle tiers applied, Cloud Run Job / Scheduler cost accounted
5. **UI data status page** green for all 5 categories (CeFi, DeFi, TradFi, Sports, Prediction) across 3 services
   (instruments, MTDS, MDPS) + features + ml
6. **Full SchemaContract validation** at write time — `StreamingParquetWriter` strict=True mandatory
7. **Source-replay symmetry** — re-running a day with `--force` produces bit-identical output (modulo timestamps); no
   data path is a write-only function of hidden state
8. **Full use of production services** — every VM / Cloud Run Job emits `DEPLOYMENT_STARTED/PROGRESS/COMPLETED/FAILED`
   via Pub/Sub with canonical error codes; nothing orphaned in the deployments registry; GCS log-tee wrapper for all
   batch runs
9. **Old buckets retired / destroyed** — clear separation between services in terms of read/write
10. **GCS Hive partitioning** leveraged for fast downstream reads — BigQuery external tables optional; partition naming
    strictly `key=value` (no `key-value` hyphen drift)

This is **not a reinvention** — 95% of the infrastructure exists. Minimal deltas only: finishing migrations, fixing
writer drift, rebuilding manifests, retiring empty buckets, applying unapplied terraform. The data-status page is the
ultimate test: once static for a period, we are done.

## Canonical reference documents

- Audit matrix: this plan's Phase 0 (captured 2026-04-18)
- Canonicalisation plan: `unified-trading-pm/plans/active/data_canonicalisation_mvp_2026_04_17.plan.md` (67 todos,
  phases 0-2 + partial 3 done as of 2026-04-18)
- Availability manifest v4 spec: `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md`
- T+1 scheduler terraform: `deployment-service/terraform/gcp/t1_batch_scheduler.tf` (commit `56492ad`, not applied for
  data-layer services)

## Dependency DAG

```
Phase 0 — Baseline capture (2026-04-18 audit, commits, VMs)
   │
   ▼
Phase 1 — UAC contracts complete (Prediction + Sports; helper derivation)        [PARALLEL]
Phase 2 — Writer fixes (Polymarket, Sports odds, case, None literals, hyphen)    [SEQ after 1]
Phase 3 — Migration scripts                                                      [PARALLEL under 2]
Phase 4 — Manifest reconciliation (rebuild, populate v4 shard dims)              [SEQ after 3]
   │
   ▼
Phase 5  — Bucket retirement (market-data-candles-* empty shells)                [PARALLEL with 6]
Phase 5b — MDPS schemas + strict writer + full-history backfill                  [SEQ after 4]
Phase 5c — Features backfill per category (8 feature services)                   [SEQ after 5b]
Phase 5d — ML training experiments per (model_type x category) minimum           [SEQ after 5c]
Phase 6  — T+1 scheduler terraform apply (data layer)                            [PARALLEL with 5]
Phase 7  — Backfill completion (ODDS_API hole + gaps)                            [SEQ after 6]
   │
   ▼
Phase 8 — Event-log / deployment-registry integrity + Pub/Sub streaming          [SEQ after 7]
Phase 9 — GCS Hive + partition audit                                             [SEQ after 4]
Phase 10 — Features & ML pipeline symmetry (read paths)                          [SEQ after 4 + 9]
Phase 11 — Cost-of-service monitoring                                            [SEQ after 5]
   │
   ▼
Phase 12 — [HUMAN] Data Status checkpoint (per service per category)             [BLOCKING GATE per phase]
   │
   ▼
Phase 13 — Regression prevention (CI smoke + --force symmetry test)              [POST-LAUNCH]
```

**Checkpoint discipline**: Every phase that writes data (3, 4, 5b, 5c, 5d, 7) is gated by **Phase 12 Data Status
visibility**. Completion is not "VM exited rc=0" — it is "deployment-ui data-status page for that (service, category)
shows the delta reflected AND the deployment-ui /deployments page shows the run's full lifecycle
(STARTED/PROGRESS/COMPLETED) with canonical error codes on any partial failure". Nothing advances to the next phase
without this visibility confirmed.

**Idempotency requirement**: No phase may re-fetch data from a paid upstream (Databento, Tardis, ODDS_API, Polymarket,
FootyStats, The Graph) that has already been written to GCS. All migrations work on existing bucket contents; backfills
only pull what's genuinely missing per the availability filter. `--force` rewrites from already-landed source data,
never from upstream.

## Principles

1. **Every write goes through** `StreamingParquetWriter` (strict=True) **+** `ManifestWriter.write_with_zero_fill`. No
   ad-hoc `parquet.write_table` / `df.to_parquet` bypasses.
2. **SchemaContract validation** is the single gate. Pre-write hook rejects missing columns, wrong dtypes, null-rate
   violations.
3. **Manifest v4 shard dimensions** (per CLAUDE.md):
   `venue, chain, data_type, instrument_type, league_id, timeframe, feature_group, model_family, training_period, strategy_id, client_id, instruction_type`.
   **Never overload `venue`.**
4. **Sports venue = bookmaker** (BET365, PINNACLE, BETFAIR, MATCHBOOK, UNITY_BETFAIR). **Sports data_source = provider**
   (ODDS_API, SFI, FOOTYSTATS). These are orthogonal. Brokers (Unity, direct) and clients (allocation wrappers) are
   row-level execution columns, NOT partition dimensions.
5. **Instrument_id derivation, not column materialization.** Read-side helper
   `derive_instrument_id(path_context, row) -> str` — no per-row instrument_id column on disk (revises canonicalisation
   plan Principle 1).
6. **Lowercase all data_type / instrument_type tokens** (`odds` not `ODDS`).
7. **Pandas NA, not `str(None)`**, for optional fields. Nullable schema everywhere.
8. **Event-driven observability mandatory** for every VM / Cloud Run Job. Use `deployment_heartbeat.py` +
   `vm-exec-with-gcs-tee.sh` + `ServiceBootstrap` for service lifecycle events.
9. **Clear bucket ownership**:
   - `instruments-store-{category}-*` → instruments-service (read+write)
   - `market-data-tick-{category}-*` → MTDS (write), MDPS/features/ml (read) — MDPS also writes to `processed_candles/`
     subfolder here (co-located, not separate buckets)
   - `features-{group}-{category}-*` → features service (write), ml (read), strategy (read)
   - `market-data-candles-{category}-*` → **RETIRED** (empty; co-location wins)
10. **Pre-audit before every multi-repo change**. Embed manifest in plan.

---

## Phase 0 — Baseline capture (2026-04-18 audit)

### 3×4 state matrix (as of session end 2026-04-18)

| Service \ Category      | CeFi                                                                                                                                 | DeFi                                                                                                                                                                               | TradFi                                                                                                                                                           | Sports + Prediction                                                                                                                                          |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **instruments-service** | ALIGNED / N/A / CLEAN / 2019-03→2026-04, 21.9K rows                                                                                  | ALIGNED / N/A / STALE (2080 `data_type="None"`, 5838 `chain=""`) / 2020-01→2026-04, 69.7K rows                                                                                     | ALIGNED / N/A / CLEAN / 2020-01→2026-04, 11.3K rows                                                                                                              | DRIFT all 112K `venue=""` + `instrument_type=""` / REBUILD NEEDED / league-keyed not venue-keyed / 2019→present (Polymarket 2025-03→2029-01 future expiries) |
| **MTDS**                | DRIFT (Tardis-native cols, **no `instrument_id`** — derive-on-read sufficient) / enrichment needed / 40 `venue=""` / 2019-03→2026-04 | PARTIAL (29 cols vs contract 5; no `ts_event`) / **IN PROGRESS** full-history 2020→2026 (at 2024-12-17 ~85%) / SEVERELY STALE (94 rows covering 2wks vs 2yr GCS) / 2024-05→2026-04 | DRIFT (raw Databento cols) / **IN PROGRESS** with 5-pattern classifier (ICE/CME/CBOE/6L) / 35 `venue=""` + `day-2025-11-02/` hyphen partitions / 2020-01→2026-04 | DRIFT `instrument_type=""` in 2024 / PARTITION REWRITE NEEDED / case mismatch `ODDS`/`odds` / 2020-06→2026-04 + **54-day hole Feb 22→Apr 13 2026**           |
| **MDPS**                | BUCKETS EMPTY — MDPS writes under MTDS `processed_candles/` co-located                                                               | same                                                                                                                                                                               | same                                                                                                                                                             | same (sports uses `processed/` subprefix)                                                                                                                    |

### Today's commits on `live-defi-rollout`

**UAC** (unified-api-contracts):

- `b681762` UNISWAP V3/V4 + Curve + Balancer `pool_address` overrides
- `43efa05` 8 new DeFi reserve/LST data_type contracts (Aave V3 reserve + Morpho + LST)
- `3f10fc4` symbol_column alignment (AAVE_V3=`token`, MORPHO=`instrument_key`, UNISWAP_V2=`pair_address`, ETHENA
  override)
- `be4cbb4` `(tradfi, combo, trades)` SchemaContract

**MTDS** (market-tick-data-service):

- `095df12` BRK.B full-symbol-first; DeFi data_type alias (liquidity→dex_pool_state, swaps→dex_pool_swaps)
- `0157f11` legacy `data_type=options_chain/futures_chain` normalised to `trades`
- `6f43624` `resolve_equity_venue` uses UAC G5 `resolve_exchange`
- `7adc2fa` `InstrumentType.COMBO → "combo"` partition token
- `8511759` `6L` FX + ICE BRN/G/CC + CL:C1 continuous + CBOE UD:1V: (spaced + compact)
- `0599ba8` + `c4dc28b` CBOE UD:1V: accepts compact + numeric Globex codes

**PM** (unified-trading-pm):

- `03a37b6a` `data_canonicalisation_mvp_2026_04_17.plan.md` updated with session progress + Phase 3.5 audit items

### Running VMs (as of end of session 2026-04-18)

- `canonical-migration-defi-20260418-140539` — at 2024-12-17 (~85% through full 2020-01-01→2026-04-18)
- `canonical-migration-tradfi-20260418-164915` — full-history with 5-pattern classifier; 329K previous drops expected to
  fall to <1%

### Phase 0 todos

- [x] [AGENT] P0. 3×4 matrix captured (this plan's Context).
- [x] [AGENT] P0. Session commits documented (this plan's "Today's commits").
- [x] [AGENT] P0. Running VMs documented.
- [ ] [SCRIPT] P0. Run final capture of VM logs + manifest states at session end — archive to
      `gs://deployment-scripts-central-element-323112/audits/2026-04-18/` for reproducibility.

---

## Phase 1 — UAC contracts complete [PARALLEL]

### 1.1 Prediction SchemaContract

- [ ] [AGENT] P0. Add `PREDICTION_PREDICTION_MARKET_TRADES` SchemaContract in
      `unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py`:
      `     category="prediction", instrument_type="prediction_market", data_type="trades"     columns = [_INSTRUMENT_ID, _VENUE, _CHAIN, _TS_EVENT, _PRICE,                ColumnSpec("size", float64),                ColumnSpec("side", string),              # BUY/SELL                ColumnSpec("outcome", string),            # Yes/No/Up/Down                ColumnSpec("outcome_index", int64),                ColumnSpec("condition_id", string),                ColumnSpec("asset_id", string),                ColumnSpec("underlying", string)]         # BNB, ETH, ...     symbol_column="condition_id"     `
- [ ] [AGENT] P0. Register `("prediction", "prediction_market", "trades")` in `CONTRACT_REGISTRY`.
- [ ] [AGENT] P0. Extend `build_instrument_id` for `PREDICTION_MARKET`: canonical form
      `POLYMARKET:PREDICTION_MARKET:{condition_id}:{outcome_index}`.
- [ ] [AGENT] P0. Unit tests: contract validation + ID builder.

### 1.2 Sports SchemaContract (re-do with proper venue/data_source split)

- [ ] [AGENT] P0. Add `SPORTS_ODDS_TRADES` SchemaContract:
      `     category="sports", instrument_type="odds", data_type="trades"     columns = [_INSTRUMENT_ID, _VENUE, _TS_EVENT,                ColumnSpec("data_source", string),        # ODDS_API, SFI, FOOTYSTATS                ColumnSpec("league_id", string),          # EPL, LALIGA — v4 shard                ColumnSpec("fixture_id", string),                ColumnSpec("market_type", string),        # H2H, OU, BTTS                ColumnSpec("outcome", string),                ColumnSpec("odds_decimal", float64),                ColumnSpec("broker", string, nullable=True),   # execution-side                ColumnSpec("client", string, nullable=True)]   # allocation-side     symbol_column="fixture_id"     `
- [ ] [AGENT] P0. Register `("sports", "odds", "trades")` in `CONTRACT_REGISTRY`.
- [ ] [AGENT] P0. Extend `build_instrument_id` for sports: canonical form
      `{VENUE}:ODDS:{fixture_id}:{market_type}:{outcome}`.
- [ ] [AGENT] P0. Unit tests.

### 1.3 Instrument_id derivation helper (replaces plan Principle 1)

- [ ] [AGENT] P0. Add `unified_trading_library.canonical.derive_instrument_id(path_context: dict, row: Mapping) -> str`
      — takes partition context (`venue`, `chain`, `instrument_type`, `data_type`, `underlying`) + row fields (e.g.
      Databento `symbol`, strike, expiry), calls `build_instrument_id`, returns canonical ID.
- [ ] [AGENT] P0. Unit tests covering: CeFi perpetuals, CeFi options bundled, TradFi futures bundled, TradFi options
      bundled, TradFi combo, DeFi pool, DeFi a_token, sports odds, Polymarket.
- [ ] [AGENT] P1. Document in UTL `docs/canonical-identifiers.md` with table of (category, instrument_type, data_type) →
      derivation inputs.
- [ ] [AGENT] P1. Update `data_canonicalisation_mvp_2026_04_17.plan.md` Principle 1 to reflect derivation-over-
      materialisation policy; reference this plan.

---

## Phase 2 — Writer fixes [SEQ after 1]

### 2.1 Polymarket adapter

- [ ] [AGENT] P0.
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py`: -
      Emit path with `instrument_type=prediction_market` (not `BNB`) - Move raw `BNB` from partition into `underlying`
      column - Convert `timestamp` int → `ts_event` datetime64[ns, UTC] - Drop user-metadata columns (`pseudonym`,
      `bio`, `profileImage`, `profileImageOptimized`, `name`, `proxyWallet`, `icon`, `title`, `slug`, `eventSlug`) - Add
      `chain=POLYGON` column - Route writes through `StreamingParquetWriter` + `ManifestWriter.write_with_zero_fill`

### 2.2 Sports odds writer

- [ ] [AGENT] P0.
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py`: - Emit
      path
      `category=sports/data_source=ODDS_API/venue={BOOKMAKER}/league_id={LEAGUE}/instrument_type=odds/data_type=trades/ticks.parquet` -
      `venue` = bookmaker (iterate ODDS_API's `bookmakers[]` array per match); one file per bookmaker per league per
      day - `league_id` = proper shard column - Fall through to SchemaContract validation

### 2.3 Case + None + hyphen fixes

- [ ] [AGENT] P0. Enforce lowercase `data_type=odds` via SchemaContract `data_type` lowercase validator.
- [ ] [AGENT] P0. `instruments-service/instruments_service/engine/orchestrator.py`: replace `str(None)` coercion on
      optional `data_type`/`chain` columns with `pd.NA` + nullable string dtype.
- [ ] [AGENT] P0. `market-tick-data-service/market_tick_data_service/scripts/migrate_tradfi_canonical.py`: detect legacy
      `day-YYYY-MM-DD/` + `data_type-X/` hyphen partitions and rewrite to `day=YYYY-MM-DD/` / `data_type=X/` layout.

### 2.4 CeFi — NO instrument_id materialization (per user decision 2026-04-18)

- [x] [AGENT] P0. Decision: Tardis-native column shape is CANONICAL. `instrument_id` derived via UTL helper on read. No
      migration required.
- [ ] [AGENT] P1. Ensure CeFi Tardis writer preserves `exchange`, `symbol`, `data_type`, `instrument_type`, `underlying`
      columns — enough inputs for helper.

---

## Phase 3 — Migration scripts [PARALLEL]

### 3.1 Polymarket migration (new)

- [ ] [AGENT] P0. New script
      `market-tick-data-service/market_tick_data_service/scripts/migrate_prediction_canonical.py`: scan 2025-03 →
      2026-04 Polymarket files under `venue=POLYMARKET/instrument_type={BNB,ETH,...}/`, rewrite to
      `instrument_type=prediction_market/` + column normalisation (as 2.1), emit `MigrationManifestUpdate`.
- [ ] [SCRIPT] P0. Launch migration VM using `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` pattern,
      in-region, 32 workers, fail-loud.

### 3.2 Sports odds migration

- [ ] [AGENT] P0. New script `migrate_sports_canonical.py`: scan legacy
      `venue=ODDS_API/instrument_type=/data_type=odds/league={L}/ticks.parquet`, repartition rows per their `bookmaker`
      column into
      `data_source=ODDS_API/venue={BOOKMAKER}/league_id={L}/instrument_type=odds/data_type=trades/ticks.parquet`.
- [ ] [SCRIPT] P0. Migration VM per pattern.

### 3.3 TradFi — finish in-progress full-history

- [ ] [SCRIPT] P0. Wait for `canonical-migration-tradfi-20260418-164915` to finish (ETA ~8hr from 16:49 UTC).
- [ ] [AGENT] P0. Extend `migrate_tradfi_canonical.py` with hyphen-partition detector (Phase 2.3) if any remain; rerun.
- [ ] [AGENT] P1. Sample 10 unparseable symbols from final log; decide if extend classifier or document as structured
      `UNPARSEABLE_DATABENTO_SYMBOL` events.

### 3.4 DeFi — finish in-progress full-history

- [ ] [SCRIPT] P0. Wait for `canonical-migration-defi-20260418-140539` to finish (at 2024-12-17, ETA ~2hr).
- [ ] [SCRIPT] P0. Verify final counters: files_migrated ≈ files_scanned, row_errors = 0, rc=0.

### 3.5 CeFi — no migration (derive-on-read policy)

- [x] [AGENT] P0. Derive-on-read decision obviates CeFi instrument_id migration (confirmed with user 2026-04-18).

---

## Phase 4 — Manifest reconciliation [SEQ after 3]

- [ ] [AGENT] P0. Root-cause why MTDS DeFi manifest emission stopped after 2024-05-15 (94 rows covering 2wks vs 2yr
      GCS). Fix whatever disabled the `ManifestWriter.write_with_zero_fill` call path.
- [ ] [SCRIPT] P0. Rebuild DeFi manifest via
      `unified_trading_library.rebuild_manifest_from_canonical_paths('gs://market-data-tick-defi-*')` after Phase 3.4
      completes. Emit drift report.
- [ ] [AGENT] P0. Sports instruments manifest: populate `venue` column from per-row `bookmaker`; emit `data_source`
      column; drop `venue=""` rows; drop literal `day="all"` sentinels; lower-case `data_type`.
- [ ] [SCRIPT] P0. Prediction manifest: rebuild after Phase 3.1 migration lands.
- [ ] [AGENT] P0. All-category pass: for each of
      `market-data-tick-{cefi,defi,tradfi,sports,prediction}-central-element-323112` run: - Delete rows with `venue=""`
      / `chain=""` / `data_type=""` / `instrument_type=""` - Convert `"None"` string literals → `pd.NA` via one-shot
      rewrite - Validate every row against `CONTRACT_REGISTRY` lookup; emit `MANIFEST_ROW_VIOLATION` on mismatch
- [ ] [SCRIPT] P0. Write `_index/availability_index_rebuild_2026_04_18.parquet` backup per bucket before mutation.

---

## Phase 5 — Bucket retirement [PARALLEL with 6]

> **Scope clarification 2026-04-18**: Phase 5 only retires the **empty separate** `market-data-candles-*` buckets. The
> **actual MDPS writer + backfill + schemas** live in **Phase 5b** (see below) — MDPS itself is NOT retired; the candles
> it produces are co-located inside the MTDS tick buckets under `processed_candles/` (or `processed/` for sports). Do
> Phase 5 + 5b in parallel; 5a can run without waiting on 5b.

### 5.1 market-data-candles-\* retirement (5 prod + 5 test, all empty)

- [x] [AGENT] P0. Verified: 10/10 candles buckets = 0 objects / 0 bytes (2026-04-18).
- [x] [AGENT] P0. No Python code actively targets these buckets — MDPS writes to `processed_candles/` under MTDS.
- [ ] [AGENT] P0. `unified-trading-library/unified_trading_library/core/cloud_constants.py`: remove
      `market_data_candles` key from `gcp` + `aws` dicts (lines 143, 161).
- [ ] [AGENT] P0. `deployment-service/configs/bucket_config.yaml`: remove line 329 (`market-data-candles` AWS template).
- [ ] [AGENT] P0. `deployment-service/scripts/setup-gcs-lifecycle-policies.sh`: remove lines 85-87 (3 candles buckets in
      apply array).
- [ ] [AGENT] P0. `unified-trading-pm/configs/dependencies.yaml`: remove `candles` data-source block (lines 135-138).
- [ ] [AGENT] P0. `deployment-service/terraform/gcp/main.tf`: remove 3
      `google_storage_bucket.candles_{cefi,tradfi,defi}` resources + any `google_storage_bucket_iam_*` referencing them
      (lines 489-541+).
- [ ] [AGENT] P1. Trace origin of sports + prediction candles buckets + all 5 `-test-` variants (not in main.tf). Likely
      separate terraform or manual `gsutil mb` — find + remove.
- [ ] [AGENT] P1. Docs update: `bucket-permissions-per-service.md` (×2 repos), `COST.md`,
      `GCS_LIFECYCLE_COST_OPTIMIZATION.md` — add note "candles co-located under MTDS; separate buckets retired
      2026-04-18".
- [ ] [SCRIPT] P0.
      `cd deployment-service/terraform/gcp && terraform plan -target=google_storage_bucket.candles_cefi     -target=google_storage_bucket.candles_tradfi -target=google_storage_bucket.candles_defi`.
      Review destroy list (3 empty buckets). Apply.
- [ ] [SCRIPT] P0. For non-terraform orphans:
      `for b in sports prediction cefi-test tradfi-test defi-test sports-test     prediction-test; do gsutil rb gs://market-data-candles-$b-central-element-323112/; done`.
- [ ] [AGENT] P1. Update `data_canonicalisation_mvp_2026_04_17.plan.md` Phase 3.5 — mark MDPS retirement DONE.

### 5.2 Other legacy path cleanup

- [ ] [AGENT] P1. Identify legacy DeFi `venue=AAVE_V3-ETHEREUM` style paths in GCS post-migration; confirm all rewritten
      to `venue=AAVE_V3/chain=ETHEREUM` canonical form; delete `_migrated_{ts}` backups after 7 days.
- [ ] [AGENT] P1. Identify any TradFi `instrument_type=future/data_type=options_chain/` legacy mislabelled paths from
      the Phase-3.2 TradFi migration; confirm cleaned.

---

## Phase 5b — MDPS schemas + symmetric sharding + backfill [NEW 2026-04-18, SEQ after 4]

### Context (2026-04-18 audit)

MDPS writes to `processed_candles/` **co-located inside MTDS tick buckets** (confirmed for cefi/defi/tradfi/prediction;
sports uses `processed/`). Current state is bad:

- **UAC has only 2 candle contracts**: `tradfi/future/ohlcv_1m` + `tradfi/equity/ohlcv_1m` (pass-through from
  Databento's native 1m bars — not computed). **Zero contracts** for CeFi/DeFi/Sports/Prediction candles or for non-1m
  TradFi timeframes.
- **Writer validation absent**: MDPS does not go through `StreamingParquetWriter(strict=True)`.
- **Coverage gap**: CeFi = 1 day, DeFi = 2 days, TradFi = 2 days, Prediction = 361 days, Sports = 1835 days. CeFi/DeFi/
  TradFi are essentially empty.
- **Manifest coverage broken**: the `timeframe` shard column exists in the v4 manifest (alongside
  venue/chain/data_type/instrument_type) but 99.94% of MTDS-bucket manifest rows have `timeframe=""`. Only 16 rows have
  `timeframe` populated (4 timeframes × 4 shards for 1 day).

### Principles (MDPS symmetry with MTDS)

1. **Same shard dimensions** as MTDS: `(category, venue, chain, instrument_type, data_type, timeframe)` + `league_id`
   for sports. MDPS output = MTDS shape + `timeframe` dimension.
2. **SchemaContract keyed by** `(category, instrument_type, source_data_type, timeframe)` — different source
   `data_type`s produce different candle shapes:
   - `trades` → OHLCV + trade_count + volume_base/quote + vwap
   - `book_snapshot_5` → OHLCV of mid + spread/depth/imbalance means (microstructure)
   - `derivative_ticker` → OHLCV + funding_rate/mark_price/index_price means
   - `liquidations` → count + notional aggregates (not pure OHLCV)
   - `dex_pool_swaps` → OHLCV of price + swap_count + volume (DeFi-specific)
   - `odds` → OHLCV of decimal odds + quote_count (sports-specific)
3. **Pass-through for TradFi**: Databento delivers 1m OHLCV natively. MDPS writes it through as `tradfi/*/ohlcv_1m`.
   Higher timeframes (5m/15m/1h/4h/1d) are re-aggregated from the 1m bars.
4. **Timeframes**: 15s, 1m, 5m, 15m, 1h, 4h, 1d. Per-category timeframe subset decided by strategy need (CeFi ticks →
   all; TradFi → 1m+ only since that's native granularity; DeFi → 15s+; sports → 1m+; prediction → 1m+).
5. **Strict writer gate**: `StreamingParquetWriter(strict=True)` on every MDPS write. No ad-hoc `to_parquet`.
6. **Manifest emission**: every MDPS write also emits `MigrationManifestUpdate` / `ManifestWriter.write_with_zero_fill`
   with the full shard tuple including `timeframe`.

### 5b.1 UAC MDPS SchemaContracts [PARALLEL with Phase 1]

- [ ] [AGENT] P0. Add base column-spec builders for candles in
      `unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py`:
      `     _CANDLE_OHLCV_BASE = [_INSTRUMENT_ID, _VENUE, _CHAIN, _TS_EVENT,                           ColumnSpec("open", float64), ColumnSpec("high", float64),                           ColumnSpec("low", float64), ColumnSpec("close", float64),                           ColumnSpec("volume", float64, nullable=True),                           ColumnSpec("trade_count", int64, nullable=True),                           ColumnSpec("timeframe", string)]     _CANDLE_BOOK_5_EXT = [... + spread_bps_mean, depth_bid_mean, depth_ask_mean,                           imbalance_ratio_mean, bid_vol_0_mean, ask_vol_0_mean,                           tob_depth_ratio_mean, mid_price_mean]     _CANDLE_DERIV_EXT   = [... + funding_rate_mean, mark_price_mean, index_price_mean]     _CANDLE_LIQ_EXT     = [ColumnSpec("liquidation_count", int64), ColumnSpec("liquidation_notional_usd", float64)]     _CANDLE_DEX_EXT     = [... + swap_count, volume_quote_usd]     _CANDLE_ODDS_EXT    = [... + quote_count, source_count]     `
- [ ] [AGENT] P0. Register MDPS contracts for every (category × instrument*type × source_data_type × timeframe): -
      **CeFi**: -
      `cefi/perpetual/{trades,book_snapshot_5,derivative_ticker,liquidations}/ohlcv*{15s,1m,5m,15m,1h,4h,1d}` -`cefi/spot*pair/{trades,book_snapshot_5}/ohlcv*{15s,1m,5m,15m,1h,4h,1d}` -`cefi/options*chain/{trades}/ohlcv*{1m,15m,1h,1d}`(book
      not typically aggregated for options) -`cefi/futures*chain/{trades}/ohlcv*{1m,15m,1h,1d}` - **TradFi**
      (pass-through 1m + re-aggregated higher): -`tradfi/future/{trades,ohlcv*1m}/ohlcv*{1m,5m,15m,1h,4h,1d}`(1m is
      pass-through from source
      ohlcv_1m) -`tradfi/equity/{trades,ohlcv*1m}/ohlcv*{1m,5m,15m,1h,4h,1d}` -`tradfi/options*chain/{trades}/ohlcv*{1m,15m,1h,1d}` -`tradfi/index/{trades}/ohlcv*{1m,5m,15m,1h,1d}` -
      **DeFi**: -`defi/pool/{dex_pool_swaps,dex_pool_state}/ohlcv*{15s,1m,5m,15m,1h,1d}`(pool price/liquidity
      candles) -`defi/a*token/{lending_indices,rate_indices,oracle_prices}/ohlcv*{1m,15m,1h,1d}` -`defi/lst/{lst*rates,oracle_prices}/ohlcv*{1m,15m,1h,1d}` -
      **Sports**: -`sports/odds/{trades}/ohlcv*{1m,15m,1h}`(bookmaker odds time series per fixture) -
      **Prediction**: -`prediction/prediction_market/{trades}/ohlcv*{1m,15m,1h}`
- [ ] [AGENT] P0. Venue overrides where MDPS aggregates differ per venue (mirror Phase 3.3 DeFi pattern:
      `VENUE_CONTRACT_OVERRIDES[("cefi","BINANCE-FUTURES","perpetual","book_snapshot_5")]` etc only when columns truly
      diverge).
- [ ] [AGENT] P0. Unit tests per contract shape.

### 5b.2 MDPS writer — strict validation + ManifestWriter

- [ ] [AGENT] P0. `market-data-processing-service/market_data_processing_service/` sinks wired through
      `StreamingParquetWriter(strict=True)` with SchemaContract pre-write validation.
- [ ] [AGENT] P0. Every write emits `MigrationManifestUpdate` / `ManifestWriter.write_with_zero_fill` with full
      `(category, venue, chain, instrument_type, data_type, timeframe, league_id)` shard tuple.
- [ ] [AGENT] P0. Fail-loud on missing `instrument_id` / wrong dtype / empty venue per pre-write hook.
- [ ] [AGENT] P1. `--force` behaviour: re-compute + overwrite day partition atomically; same input ticks → same output
      candles (verified by Phase 13 symmetry test).
- [ ] [AGENT] P1. Skip behaviour: if target parquet exists AND row count > 0 AND schema_version matches, skip. Otherwise
      re-run (don't trust partial writes).

### 5b.3 MDPS backfill — per category × venue × timeframe

- [ ] [SCRIPT] P0. Launch MDPS backfill VMs per category (e2-standard-8, asia-northeast1-c, 32 workers). Reads from
      `market-data-tick-{category}-*/raw_tick_data/by_date/` (canonical after Phase 3 migrations), writes to
      `market-data-tick-{category}-*/processed_candles/by_date/day=/timeframe=/data_type=/venue=/.parquet`.
- [ ] [SCRIPT] P0. Full-history scope per category: - CeFi: 2020-01-01 → 2026-04-18 (~2300 days × N venues × N
      instruments × 7 timeframes) - TradFi: 2020-01-01 → 2026-04-18 (Databento ohlcv_1m is pass-through; re-aggregate
      higher timeframes) - DeFi: 2020-01-01 → 2026-04-18 (DEX pool price candles; ~2300 days × N chains × N pools) -
      Sports: 2019-01-01 → 2026-04-18 (bookmaker odds candles per fixture) - Prediction: 2025-03-14 → 2026-04-18
      (Polymarket only)
- [ ] [SCRIPT] P0. Parallel launch (5 VMs, one per category). Each emits lifecycle events
      (`DEPLOYMENT_STARTED/PROGRESS/COMPLETED/FAILED`) via deployment_heartbeat.py.
- [ ] [SCRIPT] P0. Monitor via deployment-ui /deployments/active; gate on rc=0 + row_errors=0.

### 5b.4 MDPS manifest reconciliation

- [ ] [SCRIPT] P0. After 5b.3 completes per category, rebuild manifest via `rebuild_manifest_from_canonical_paths` on
      each MTDS bucket including `processed_candles/` subtree.
- [ ] [AGENT] P0. Verify manifest shows `timeframe`-populated rows for every expected (day, venue, instrument_type,
      data_type, timeframe) combo. Zero-fill for expected-empty days (e.g. weekends for TradFi).
- [ ] [AGENT] P1. Per-timeframe instrument count matches tick manifest for same day (sanity).

### 5b.5 Integration

- [ ] [AGENT] P1. features-\* services' MDPS consumers verify they read canonical `timeframe=` partition (not legacy
      flat `processed_candles/` heuristics). Update path template if needed.
- [ ] [AGENT] P1. ml-training / ml-inference MDPS consumers same audit.
- [ ] [HUMAN] P1. Data Status page shows per-timeframe coverage per category (sub-tab under each service).

---

## Phase 5c — Features backfill per category [SEQ after 5b]

### Context

8 feature services (delta-one, volatility, onchain, sports, calendar, multi-timeframe, cross-instrument, commodity).
Each produces per-feature-group parquet files. They must be backfilled against canonical MTDS + MDPS output so
downstream ML has a clean dataset.

### Principles

1. **feature_group** is the primary manifest shard column per CLAUDE.md v4. Each service registers its groups.
2. Writers go through `StreamingParquetWriter(strict=True)` + `ManifestWriter.write_with_zero_fill`.
3. Idempotent — re-running the backfill with `--force` overwrites; without, it skips existing days.

### 5c.1 Per-service UAC SchemaContracts

- [ ] [AGENT] P0. For each of the 8 feature services, enumerate the feature groups emitted. Register each
      `(category, instrument_type, feature_group)` SchemaContract in UAC.
- [ ] [AGENT] P0. Per-group contract declares required columns, dtypes, and the `symbol_column` used for joining back to
      instrument_id.
- [ ] [AGENT] P0. Unit tests per group.

### 5c.2 Features writer strict mode

- [ ] [AGENT] P0. Per feature service, confirm writer uses `StreamingParquetWriter(strict=True)` +
      `ManifestWriter.write_with_zero_fill`. Fix the ones that don't.
- [ ] [AGENT] P0. Every write emits manifest row with
      `(category, venue, chain, instrument_type, feature_group, timeframe)` shard tuple.

### 5c.3 Full-history features backfill per category

- [ ] [SCRIPT] P0. Launch backfill VMs per (feature_service × category) that has upstream MTDS+MDPS data. Grid (worst
      case 8 × 5 = 40 runs; many will be no-op if category doesn't apply to the feature group, e.g. features-onchain
      only runs against DeFi).
- [ ] [SCRIPT] P0. Target date ranges: same as source categories (CeFi/DeFi/TradFi 2020-01→2026-04, Sports
      2019-01→2026-04, Prediction 2025-03→2026-04).
- [ ] [SCRIPT] P0. Each VM emits lifecycle events via `deployment_heartbeat.py` + `vm-exec-with-gcs-tee.sh`; no orphans
      per Phase 8.
- [ ] [AGENT] P0. Batch into 4 parallel waves max per deployment-service concurrency budget.

### 5c.4 Manifest reconciliation for features

- [ ] [SCRIPT] P0. Rebuild feature manifests post-backfill via
      `rebuild_manifest_from_canonical_paths('gs://features-{group}-{category}-*')`.
- [ ] [AGENT] P0. Verify feature_group column populated per row + zero empty venue.

### 5c.5 Data Status checkpoint

- [ ] [HUMAN] P0. Data Status page `/data-status/features-{group}` shows coverage per (day, category, timeframe,
      instrument_type) matching expected denominators. No false-missing.

---

## Phase 5d — ML training experiments per (model_type x category) [SEQ after 5c]

### Context

Before calling the data pipeline "done", we must prove it is fit for downstream ML. The test is: for every viable
(model_type × category) combination, ml-training-service runs a minimal training experiment end-to-end using real
features from Phase 5c, emitting a model artifact and manifest row. We don't chase accuracy here — we prove the pipe
works.

### 5d.1 Catalogue viable (model_type × category) combinations

- [ ] [AGENT] P0. Enumerate the model_type registry in ml-training-service. Document which model_types are viable per
      category. Expected matrix: | model_type | CeFi | DeFi | TradFi | Sports | Prediction | | --- | --- | --- | --- |
      --- | --- | | classification | ✓ | ✓ | ✓ | ✓ | ✓ | | regression | ✓ | ✓ | ✓ | ✓ | ✓ | | timeseries_forecasting | ✓
      | ✓ | ✓ | ✓ | ✓ | | ranking | - | - | - | ✓ | ✓ | | anomaly_detection | ✓ | ✓ | - | - | - | | reinforcement | ✓ |
      ✓ | - | - | - |
- [ ] [AGENT] P0. Produce a concrete run-list: per-cell, pick 1 instrument subset + 1 timeframe + 1 training window.
      E.g. `cefi/classification/BTC-PERP-binance-futures/1h/2023-01..2024-12 → 2025 test`.

### 5d.2 Training experiments execution

- [ ] [SCRIPT] P0. For each run-list entry, launch `ml-training-service` CLI with real features from Phase 5c.
- [ ] [AGENT] P0. Each run writes: - Model artifact to
      `gs://ml-models-{category}-*/models/{model_family}/{experiment_id}/` - Training manifest row with
      `(category, model_family, training_period, strategy_id)` shard tuple - Training metrics (loss curve, val accuracy,
      AUC) via UAC `ML_TRAINING_METRICS` events - Lifecycle events (DEPLOYMENT_STARTED/PROGRESS/COMPLETED/FAILED)
- [ ] [AGENT] P0. Register `(category, model_family, training_period, experiment_id)` SchemaContract in UAC for training
      manifest rows.

### 5d.3 Inference smoke per experiment

- [ ] [SCRIPT] P0. For each trained model, run 1-day inference on 2026-04-14 data via ml-inference-service. Assert
      output parquet lands + manifest row emitted.
- [ ] [AGENT] P1. Model family-level symmetry test: rerun training with `--force` same config → bit-identical model
      artifact (seed-pinned).

### 5d.4 Data Status checkpoint

- [ ] [HUMAN] P0. Data Status page `/data-status/ml-training` shows per-(category, model_family) experiment count +
      last-run-timestamp + last rc. Data Status `/data-status/ml-inference` same.

---

## Phase 6 — T+1 scheduler terraform apply [PARALLEL with 5]

### 6.1 Apply data-layer schedulers

- [ ] [SCRIPT] P0. `cd deployment-service/terraform/gcp && terraform plan` — capture full plan diff.
- [ ] [SCRIPT] P0. Dev environment first: `terraform workspace select dev && terraform apply` — confirm 7 new Cloud
      Scheduler jobs + 7 new Cloud Run Jobs.
- [ ] [SCRIPT] P0. Verify dev nightly run emits `DEPLOYMENT_STARTED/COMPLETED` events via Pub/Sub → deployments registry
      → deployment-ui.
- [ ] [SCRIPT] P0. Staging + prod rollout after dev 3-day burn-in.

### 6.2 Verify T+1 schedule correctness

- [ ] [AGENT] P0. Verify 2-phase split still correct: FAST 00:00-03:00 UTC (Sports/DeFi/Prediction/TradFi) + SLOW
      06:00-08:00 UTC (CeFi/Tardis).
- [ ] [AGENT] P1. Add `uts-{env}-market-tick-data-service-sports-fixtures-hourly-schedule` for odds hourly refresh if
      sports strategies need finer granularity.

---

## Phase 7 — Backfill completion [SEQ after 6]

### 7.1 ODDS_API 54-day hole

- [ ] [SCRIPT] P0. Manual invoke `market-tick-data-service-fast-t1-recon` Cloud Run Job for each day 2026-02-22 →
      2026-04-13 (54 days). Use `gcloud run jobs execute ... --update-env-vars TARGET_DATE=YYYY-MM-DD`.
- [ ] [SCRIPT] P0. Verify per-day landed in `gs://market-data-tick-sports-central-element-323112/raw_tick_data/by_date/`
      with proper 2.1 partition shape.

### 7.2 Per-category gap audit

- [ ] [AGENT] P0. For each category, run `get_instruments_available_on(day, ...)` × each expected day; diff against
      manifest `row_count > 0`; emit gap report to GCS.
- [ ] [SCRIPT] P0. Launch targeted backfill VMs for any identified gaps (non-overlapping with 3.x migrations).
- [ ] [AGENT] P1. Rate-limit + cost guardrails: each backfill VM emits cost estimate before start; human approves runs
      expected to exceed $50.

---

## Phase 8 — Event-log / deployment-registry integrity audit [SEQ after 7]

- [ ] [AGENT] P0. Every VM / Cloud Run Job / migration script MUST emit: 1. `DEPLOYMENT_STARTED` at start 2.
      `DEPLOYMENT_PROGRESS` every 60s (via heartbeat loop) 3. `DEPLOYMENT_COMPLETED` or `DEPLOYMENT_FAILED` at end 4.
      Canonical error codes via `classify_venue_error()` on all failures
- [ ] [AGENT] P0. Audit `deployment-service/deployment_service/deployments_registry.py` for zombie entries (started but
      never completed); prune.
- [ ] [AGENT] P0. Verify `deployment-ui` pages: - `/deployments/active` shows currently-running VMs + jobs -
      `/deployments/archive` shows past 30 days with per-run drill-down - `/events` shows last N events with filter by
      event_type, service, severity
- [ ] [AGENT] P1. Nightly orphan-event detector: for any `DEPLOYMENT_STARTED` > 24h without `COMPLETED`/`FAILED`, emit
      `DEPLOYMENT_ORPHANED` alert.
- [ ] [AGENT] P1. `ServiceBootstrap` required on all services (CLAUDE.md SERVICE_INFRASTRUCTURE QG rule).

### 8.2 Pub/Sub error streaming + debug mode

- [ ] [AGENT] P0. Every VM / Cloud Run Job must `setup_events(service_name=..., mode="batch")` at start, then every
      error path calls `log_event` with canonical error code from `unified_api_contracts.classify_venue_error()`. Errors
      land in Pub/Sub topic `events-{env}` via `unified_trading_library.events` sink.
- [ ] [AGENT] P0. Debug mode: `--debug` CLI flag + `DEBUG_EVENTS=1` env var emit verbose `DEBUG_SHARD_SCANNED` /
      `DEBUG_ROW_CLASSIFIED` / `DEBUG_MANIFEST_ROW` at INFO severity every N rows. Default off (prod) so Pub/Sub doesn't
      flood.
- [ ] [AGENT] P0. deployment-ui `/events` page subscribes via SSE to `events-{env}` topic; displays last N events with
      filter by event_type, service, severity, deployment_id. Live stream (not polled).
- [ ] [AGENT] P0. VMs stream stdout/stderr to GCS via `vm-exec-with-gcs-tee.sh` AND emit key INFO events to Pub/Sub. No
      "debug via SSH into VM" required.
- [ ] [AGENT] P0. UTL `events/` + UAC `classify_venue_error` + deployment-service registry + deployment-ui integration
      MUST be wired end-to-end for every batch VM launched. Gate: a test run of each migration script produces (a) GCS
      log tee, (b) `DEPLOYMENT_STARTED/PROGRESS/COMPLETED` events visible in /deployments UI, (c) any errors in /events
      UI with clickable drill-down to the offending shard, (d) deployments registry entry pruned on exit.

### 8.3 Production-event integrity (no double-fetch)

- [ ] [AGENT] P0. Every upstream data adapter (Tardis, Databento, ODDS_API, Polymarket CLOB, FootyStats, The Graph)
      emits `UPSTREAM_FETCH_STARTED` + `UPSTREAM_FETCH_COMPLETED` events with the date range + row count. Migrations +
      backfills read these events via deployment-api to confirm a day is already landed before launching a new upstream
      call.
- [ ] [AGENT] P0. Idempotency guard in every migration/backfill script: check GCS day partition exists + passes
      SchemaContract + manifest row emitted → skip. Only re-fetch on `--force` explicit flag.
- [ ] [AGENT] P1. Cost alert: if an `UPSTREAM_FETCH_STARTED` is emitted for a date range already covered by a prior
      `UPSTREAM_FETCH_COMPLETED`, emit `UPSTREAM_DOUBLE_FETCH` warning.

---

## Phase 9 — GCS Hive + partition audit [SEQ after 4]

- [ ] [AGENT] P0. Scan all canonical buckets for `day-YYYY-MM-DD/` (dash) partitions. Rewrite to `day=YYYY-MM-DD/`
      (equals). Detect via `gsutil ls | grep -E "day-[0-9]"`.
- [ ] [AGENT] P0. Scan for any non-Hive subdir names (e.g. `venue_BINANCE/` no `=`). Rewrite.
- [ ] [AGENT] P1. BigQuery external table definitions per category:
      `CREATE EXTERNAL TABLE uts_{env}_{category}_ticks OPTIONS(format='PARQUET',     hive_partition_uri_prefix='gs://market-data-tick-{category}-*/raw_tick_data/by_date/')`.
      Enables fast ad-hoc SQL without loading. Document in codex/02-data/.
- [ ] [AGENT] P1. Verify partition cardinality per shard dim stays bounded (per CLAUDE.md
      availability-manifest-and-data-status.md). No runaway partitions.

---

## Phase 10 — Features & ML pipeline symmetry [SEQ after 4, 9]

- [ ] [AGENT] P0. Per features service (features-delta-one, features-onchain, features-sports, features-volatility,
      features-calendar, features-multi-timeframe, features-cross-instrument, features-commodity): 1. Confirm reads from
      correct canonical MTDS path (not legacy) 2. Writer goes through `StreamingParquetWriter` + `ManifestWriter` 3.
      Per-feature-group SchemaContract registered in UAC 4. `feature_group` manifest shard column populated
- [ ] [AGENT] P0. ml-training-service + ml-inference-service: same audit. Reads features-\* from canonical paths.
- [ ] [AGENT] P1. Cross-service data lineage doc: `codex/02-data/data-lineage-MTDS-features-ml.md` — one table per
      feature group showing (upstream_bucket, upstream_path, feature_calculator, output_bucket, output_path,
      manifest_shard_dims).

---

## Phase 11 — Cost-of-service monitoring [SEQ after 5]

- [ ] [AGENT] P0. Weekly cost report per bucket: `gsutil du -s gs://*-central-element-323112/` → BigQuery →
      deployment-ui cost page.
- [ ] [AGENT] P0. GCS lifecycle policies applied to all active buckets per
      `deployment-service/scripts/setup-gcs-lifecycle-policies.sh` — verify post-retirement list is accurate.
- [ ] [AGENT] P0. Cloud Run Job + Cloud Scheduler cost per service per env (dev/staging/prod).
- [ ] [AGENT] P1. Cost alerts: email on monthly total > threshold.

---

## Phase 12 — [HUMAN] Data Status checkpoints [BLOCKING per phase + FINAL]

Phase 12 is not a single end-gate — it is a **per-phase visibility checkpoint**. Every data-writing phase (3, 4, 5b, 5c,
5d, 7) is only "done" when the corresponding deployment-ui view shows the expected delta. The human confirms each
checkpoint; no VM-rc=0 auto-advances.

### 12.1 Phase 3 checkpoint — migrations

- [ ] [HUMAN] P0. After MTDS DeFi migration: `/data-status/market-tick-data-service?category=DEFI` shows 2020-01→2026-04
      green. Confirmed today.
- [ ] [HUMAN] P0. After MTDS TradFi migration: same page filter `category=TRADFI`. Confirm green.
- [ ] [HUMAN] P0. After MTDS Sports + Prediction migrations: same for each category.

### 12.2 Phase 4 checkpoint — manifest reconciliation

- [ ] [HUMAN] P0. For each category × service pair, confirm manifest shard dimensions populate non-empty in
      deployment-ui data-status. No `venue=""`, no `"None"` literals, no `data_type=ODDS`-upper.

### 12.3 Phase 5b checkpoint — MDPS candles

- [ ] [HUMAN] P0. `/data-status/market-data-processing-service` shows per-timeframe coverage per category (CeFi, DeFi,
      TradFi, Sports, Prediction). Green for full history date range.

### 12.4 Phase 5c checkpoint — features

- [ ] [HUMAN] P0. `/data-status/features-{group}` green per feature group × applicable category. 8 pages total (one per
      feature service).

### 12.5 Phase 5d checkpoint — ML training experiments

- [ ] [HUMAN] P0. `/data-status/ml-training` shows per-(category, model_family) experiment count, last-run timestamp,
      last rc. Grid from Phase 5d.1 matrix is fully exercised.
- [ ] [HUMAN] P0. `/data-status/ml-inference` shows smoke-run output per experiment.

### 12.6 Phase 7 checkpoint — ODDS_API backfill

- [ ] [HUMAN] P0. `/data-status/market-tick-data-service?category=SPORTS` shows Feb 22→Apr 13 2026 hole closed.

### 12.7 Event integrity checkpoint — /deployments + /events

- [ ] [HUMAN] P0. `/deployments/active` empty (no runs outstanding past their ETA).
- [ ] [HUMAN] P0. `/deployments/archive` last 7 days — every run has `STARTED` and `COMPLETED`/`FAILED` bookends. No
      orphans.
- [ ] [HUMAN] P0. `/events` shows Pub/Sub stream live; errors drill down to canonical error codes + deployment_id.

### 12.8 Final gate — 7-day green window

- [ ] [HUMAN] P0. Every category green on every service page for a **7-day rolling window**. Zero false-missing flags
      (every flag corresponds to a real gap, not a manifest drift).
- [ ] [AGENT] P1. On any discrepancy at any checkpoint above: file bug against the specific phase + iterate before
      advancing.

---

## Phase 13 — Regression prevention [POST-LAUNCH]

- [ ] [AGENT] P0. CI smoke test per adapter: write 10 rows to sandbox bucket → assert SchemaContract valid → assert
      manifest row emitted with all shard dims → assert `StreamingParquetWriter(strict=True)` passed.
- [ ] [AGENT] P0. **Source-replay symmetry test**: for each adapter, ingest day D with `--force`; ingest again with
      `--force`; assert output parquet bit-identical (modulo lifecycle timestamps). Failure = writer has hidden state.
- [ ] [AGENT] P0. `StreamingParquetWriter(strict=True)` MANDATORY — code path lints error on `strict=False` except
      explicit legacy-adapter list.
- [ ] [AGENT] P1. Nightly data-status audit job: compare GCS truth to manifest; alert on drift.
- [ ] [AGENT] P1. PR code-review checklist: any adapter/writer change confirms canonical partitioning + manifest
      emission + SchemaContract registered.

---

## Success criteria

- **Code readiness C5**: QG green on all 19 repos after Phase 13 CI tests land.
- **Deployment readiness D3**: T+1 scheduler applied in prod (Phase 6). Migrations complete (Phase 3). Manifests rebuilt
  (Phase 4). Buckets retired (Phase 5). Backfills caught up (Phase 7).
- **Business readiness B3**: Data Status page (deployment-ui) shows correct counts per (day, venue, instrument_type,
  data_type, chain, league_id) across all 5 categories × 3 services + features + ml, with correct denominators from
  per-day availability filter. Zero false-missing flags, zero zombie VMs, zero orphan events. `--force` symmetry test
  passes for every adapter.

---

## Out of scope (explicit)

- Reinventing write paths — every fix is a minimal delta on existing `StreamingParquetWriter` / `ManifestWriter` /
  `SchemaContract` infrastructure. No new framework.
- Non-canonical per-file schema exceptions — every (category, instrument_type, data_type) has ONE contract. Venue
  overrides via `VENUE_CONTRACT_OVERRIDES` only where row-shape genuinely differs (legacy writers).
- Materialising `instrument_id` as a disk column (revised from canonicalisation plan Principle 1; use derive-helper).
- Rebuilding the UIs — existing deployment-ui pages are the truth. Minor wiring only if gaps surface.
- MDPS separate candles buckets — co-located under MTDS wins (user decision 2026-04-18).

---

## Follow-up references

- Canonicalisation plan (67 todos, phases 0-2 + 3 partial): `data_canonicalisation_mvp_2026_04_17.plan.md`
- Availability manifest v4 plan (96 todos): `availability_manifest_v4_and_data_status_2026_04_13.plan.md`
- Pipeline scheduling plan: `unified_pipeline_scheduling_and_triggers_2026_04_15.plan.md`
- Sports pipeline comprehensive: `sports_data_pipeline_comprehensive_2026_04_16.plan.md`

This plan is the **consolidation layer** above those four — it identifies the specific gaps each one leaves open and
sequences them to the single binding gate (Phase 12 Data Status page validation).
