---
title: "Data Pipeline Completion — Instruments → MTDS → MDPS → Features (schema, manifest, backfill, retire, schedule)"
created: 2026-04-18
status: active
locked_by: live-defi-rollout
locked_since: 2026-04-18
priority: P0
repos:
  - unified-api-contracts
  - unified-trading-library
  - unified-cloud-interface
  - instruments-service
  - market-tick-data-service
  - market-data-processing-service
  - features-delta-one-service
  - features-volatility-service
  - features-onchain-service
  - features-sports-service
  - features-calendar-service
  - features-multi-timeframe-service
  - features-cross-instrument-service
  - features-commodity-service
  - ml-training-service
  - ml-inference-service
  - deployment-service
  - deployment-api
  - deployment-ui
  - unified-trading-pm
code_readiness: C1
deployment_readiness: D0
business_readiness: B0
completion_gates:
  code: C5
  deployment: D3
  business: B3
---

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
Phase 5 — Bucket retirement (market-data-candles-*)                              [PARALLEL with 6]
Phase 6 — T+1 scheduler terraform apply (data layer)                             [PARALLEL with 5]
Phase 7 — Backfill completion (ODDS_API hole + gaps)                             [SEQ after 6]
   │
   ▼
Phase 8 — Event-log / deployment-registry integrity audit                        [SEQ after 7]
Phase 9 — GCS Hive + partition audit                                             [SEQ after 4]
Phase 10 — Features & ML pipeline symmetry (read paths)                          [SEQ after 4 + 9]
Phase 11 — Cost-of-service monitoring                                            [SEQ after 5]
   │
   ▼
Phase 12 — [HUMAN] Data Status page validation per service per category          [BLOCKING FINAL]
   │
   ▼
Phase 13 — Regression prevention (CI smoke + --force symmetry test)              [POST-LAUNCH]
```

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

- [ ] [AGENT] P1. Identify legacy DeFi `venue=AAVEV3-ETHEREUM` style paths in GCS post-migration; confirm all rewritten
      to `venue=AAVE_V3/chain=ETHEREUM` canonical form; delete `_migrated_{ts}` backups after 7 days.
- [ ] [AGENT] P1. Identify any TradFi `instrument_type=future/data_type=options_chain/` legacy mislabelled paths from
      the Phase-3.2 TradFi migration; confirm cleaned.

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

## Phase 12 — [HUMAN] Data Status page validation [BLOCKING FINAL]

- [ ] [HUMAN] P0. Open `deployment-ui/data-status/instruments-service` — per-category counts match manifest truth for
      CeFi, DeFi, TradFi, Sports, Prediction.
- [ ] [HUMAN] P0. Open `deployment-ui/data-status/market-tick-data-service` — same check.
- [ ] [HUMAN] P0. Open `deployment-ui/data-status/market-data-processing-service` — verify candles visible under MTDS
      co-located path; no "empty bucket" warnings.
- [ ] [HUMAN] P0. Open `deployment-ui/data-status/features-{group}` — per-feature-group per-category counts.
- [ ] [HUMAN] P0. Open `deployment-ui/data-status/ml-{training,inference}` — per-model per-category counts.
- [ ] [HUMAN] P0. Zero false-missing flags (every flag corresponds to a real gap, not a manifest drift).
- [ ] [HUMAN] P0. Every category green for a 7-day rolling window.
- [ ] [AGENT] P1. On any discrepancy: file bug against the specific phase + iterate.

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
