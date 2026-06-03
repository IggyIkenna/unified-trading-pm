---
name: gcs_hive_partition_malformed_paths_remediation
title: "GCS hive-partition malformed paths — TradFi day- empties + CeFi root-level real data"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
created: 2026-06-01
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
status: active
locked_by: live-defi-rollout
source:
  - market-tick-data-service/docs/GCS_PATHS.md
  - market-tick-data-service/market_tick_data_service/scripts/_migrate_tradfi_hyphen_rewriter.py
  - market-tick-data-service/market_tick_data_service/engine/orchestrator.py
  - market-tick-data-service/market_tick_data_service/reader.py
priority: P2
---

# GCS hive-partition malformed paths — remediation

> **🟦 SUPERSEDED-BY (slot-3 2026-06-02, operator cross-check)** — both GCS **data** remediations are now executed by
> the per-AG v9 canonicalisation migration (NOT a separate run). **Verified current + correct on 2026-06-02** (not
> stale, not irrelevant): Pattern-1 tradfi hyphen files re-confirmed 0-row placeholders (AAPL/AUD/CME-option all 0
> rows); Pattern-2 cefi 9 root real-data files re-confirmed present in both prd + legacy; defi/prediction/sports
> re-confirmed clean.
>
> - **Pattern 2 (CeFi 9 root real-data files)** → **SUPERSEDED by `cefi_manifest_canonicalisation` E2** —
>   `migrate_cefi_flat_to_v9_canonical.py` L-flat branch reads each root `{SYMBOL}.parquet`, regroups by
>   (venue,itype,dtype,day), and fans out to canonical `day=/pipeline_mode=/asset_group=cefi/…` paths
>   (read+regroup+write, the 9 orphans). Resolves the Pattern-2 "CeFi Pattern-2 migration" todo by construction when
>   cefi migration runs.
> - **Pattern 1 (TradFi ~110k 0-row hyphen placeholders)** → **SUPERSEDED by `tradfi_manifest_canonicalisation` E2+E7**
>   — `migrate_tradfi_to_v9_canonical.py` has a 0-row footer guard that NEVER migrates them; the 12 `day-*` hyphen
>   prefixes are bulk-deleted at tradfi E7 (with the pre-delete 0-row re-assert guard). Plus a NEW coverage-gap todo:
>   equities/ETF were never genuinely ingested → backfill (tradfi plan P1).
> - **P2 recurrence guard** (QG/CI check that fails on any `raw_tick_data/by_date/` object not matching
>   `^…/day=\d{4}-\d{2}-\d{2}/`) stays here — generic, AG-independent; keep until landed, then this doc archives.
>
> **"Irrelevant vs old-information" (operator's question):** NEITHER. The doc was current + correct — it CAUGHT a real
> bug (the first tradfi migrator draft would have migrated the 0-row placeholders) which the row-count cross-check
> fixed.

> **Scope note (operator decision 2026-06-01)**: GCS data operations in this plan are **NOT executed yet** — operator
> chose "report a plan, execute nothing" for the data and "fix docs/code only" for the TradFi empties. The doc-drift fix
> (root cause) ships immediately; the two GCS data remediations below are documented executable-ready and await a
> go-ahead. No whole-corpus walk — both remediations are targeted prefix scans (NOT a single-walk-discipline breach).

> **🟦 OPERATOR DECISION LEDGER — 2026-06-01 (Ikenna, recorded slot-1).** Ownership split for **slot 7**: the doc-drift
> fix (`GCS_PATHS.md` hyphen → canonical `key=value`, secondary docs) is a **FIX-STALE literal edit owned by
> `codex_vs_repo_docs_ssot_audit`** — slot 7 records it as a todo there and does NOT edit the doc itself (avoids
> double-done with the codex-docs consolidation lane). The two GCS **data** remediations stay operator-deferred per the
> scope note above. Net: **slot 7 takes no action on this issue beyond routing the doc-fix todo.**

## What I found

A read-only audit of all five `market-data-tick-{asset_group}-central-element-323112` buckets surfaced **two distinct
path patterns that GCS/pyarrow/BigQuery hive-partition discovery cannot see** (`key=value` is required; these use
`key-value` or bare segments). `defi`, `prediction`, `sports` buckets are clean (`day=` only).

### Pattern 1 — TradFi: ~110k empty Massive dry-run placeholders

- **Path written**:
  `raw_tick_data/by_date/day-2026-01-03/data_type-ohlcv_1m/equities/NASDAQ/NASDAQ:EQUITY:AAPL-USD.parquet`
- **Three breakages vs canonical**:
  1. `day-2026-01-03` → must be `day=2026-01-03`
  2. `data_type-ohlcv_1m` → must be `data_type=ohlcv_1m`
  3. bare `equities/NASDAQ/` → must be `asset_group=tradfi/venue=NASDAQ/instrument_type=equities/` (hive keys absent,
     and segment order differs from canonical)
- **Scope**: ~11k files/day × ~10 days (`day-2025-11-02`, `day-2025-11-08`, `day-2026-01-01/03/04/10/11/17/24/25/31`,
  `day-2026-02-01`) ≈ **110,000 objects**. All written **2026-02-09**.
- **All 0 rows** — verified on a Saturday (`day-2026-01-17`) AND a Friday trading day (`day-2026-01-03`); uniform 3070 /
  4251-byte header-only files. Columns: `timestamp,symbol,open,high,low,close,volume,instrument_key,underlying`.
- **Not manifest-tracked**: `_index/availability_index.parquet` (579,372 rows) has **zero** `BATCH_MASSIVE`/`massive`
  rows. Only `batch_databento`, `batch_barchart`, `None`.
- **Origin**: pre-credential Massive dry run (the `MASSIVE_API_KEY` secret was not created until 2026-05-29 — 3.5 months
  after these were written). No production Massive ingest has ever run.

### Pattern 2 — CeFi: 9 orphaned **real-data** files at the partition root

- **Path**: `raw_tick_data/by_date/{SYMBOL}.parquet` — **no partition keys at all** (files sit directly at the
  `by_date/` root, which also corrupts partition discovery for the whole prefix).
- **9 files, REAL data**, 47 KB–13.5 MB, written **2026-05-04**: `AVAXUSDT`, `BTC-28MAR25`, `BTC-PERPETUAL`, `BTCUSDT`,
  `ETH-PERPETUAL`, `ETH-USD-250328`, `KRW-LINK`, `SOL-ETH`, `TRX-USDT`.
- Example: `BTC-PERPETUAL.parquet` = **191,945 rows**, `exchange=deribit`, `data_type=derivative_ticker`, covering a
  single day **2025-12-24** (ts 1766534400–1766620799). Schema is the real CeFi derivative_ticker schema
  (`funding_rate`, `open_interest`, `mark_price`, …).
- **Different root cause** from Pattern 1 — a 2026-05-04 backfill bug that wrote to the bucket root instead of the
  partitioned path. Canonical home for the example:
  `day=2025-12-24/asset_group=cefi/venue=DERIBIT/ instrument_type=perpetual/data_type=derivative_ticker/BTC-PERPETUAL.parquet`.

## Why it matters

Hive partition discovery (pyarrow `partitioning="hive"`, BigQuery external tables, Spark) keys on `key=value` path
segments. `key-value` and bare segments are **invisible** to these readers → Pattern-2 real data (191k+ rows × 9
instruments) is unreadable through the canonical reader, and Pattern-1 phantoms would be silently picked up as 0-row /
schema-drift rows by any recursive parquet scan that does NOT rely on partition keys.

## Root cause — doc drift (fixed in this plan)

`market-tick-data-service/docs/GCS_PATHS.md` is the apparent SSOT and documents the **legacy**
`day-{YYYY-MM-DD}/ data_type-{TYPE}/{asset_class}/` hyphen+bare convention throughout. The actual pipeline writer
(`engine/orchestrator.py` `PartitionedTickWriter` + `reader.py`) emits the **canonical**
`day=/asset_group=/venue=/ instrument_type=/data_type=` form (proven by 1,996 canonical `day=` tradfi partitions + 2,613
cefi). ~10 docs still describe the legacy form, which is what the Feb-9 dry run followed. **No live code emits the
malformed format.**

Canonical spec (SSOT = `reader.py:19` / `orchestrator.py:25`):

```
# per-instrument (non-derivative)
raw_tick_data/by_date/day={date}/asset_group={ag}/venue={venue}/instrument_type={itype}/data_type={dt}/{SYMBOL}.parquet
# derivative chains (options_chain / futures_chain)
raw_tick_data/by_date/day={date}/asset_group={ag}/venue={venue}/instrument_type={itype}/data_type={dt}/underlying={U}/ticks.parquet
# defi (chain= inserted after asset_group)
raw_tick_data/by_date/day={date}/asset_group=defi/chain={CHAIN}/venue={PROTOCOL}/instrument_type={itype}/data_type={dt}/...
```

`asset_group=` is canonical (`RAW_TICK_ASSET_GROUP_HIVE_KEY`); `category=` is legacy-tolerated on historical objects.

## Tooling gap

`market_tick_data_service/scripts/_migrate_tradfi_hyphen_rewriter.py` (`rewrite_hyphen_partitions` /
`rewrite_hyphen_blobs_for_day`) handles `key-value`→`key=value` **only**. It does NOT:

- repair **bare** segments (`equities`/`NASDAQ` → `instrument_type=`/`venue=`) — needed for Pattern 1, and
- handle root-level files with **no** partition segment at all — needed for Pattern 2.

So the existing rewriter is insufficient for both patterns as-is.

## Remediation (executable-ready — awaiting operator go-ahead)

- [x] ✅ [DOCS] P0. **Fix doc drift (root cause).** Rewrote `GCS_PATHS.md` to the canonical `key=value` form + added a
      "Deprecated legacy layout" note + `instrument_type=` table. Converted hyphen separators (`day-`/`data_type-`) to
      `=` across the 9 secondary docs (`ARCHITECTURE.md`, `DEPENDENCIES.md`, `DEPLOYMENT_GUIDE.md`,
      `DEPLOYMENT_GUIDE_FEMI.md`, `SHAHRIYAR_DEPLOYMENT_INFRA_SPEC.md`, `OPTIONS_CHAIN_DOWNLOAD_STRATEGY.md`,
      `DATABENTO_FUTURES_DOWNLOAD.md`, `DATABENTO_OPTIONS_DOWNLOAD.md`, `DEFI_DOWNLOAD_STRATEGY.md`) —
      market-tick-data-service@e906bb0. **Remaining P2**: full bare-segment restructuring (`equities/`→
      `instrument_type=equity/` etc.) of the 9 secondary docs; SSOT `GCS_PATHS.md` is already fully canonical.
- [x] ✅ [DOCS] P0. **Fix stale bucket naming (env-tier drift).** The docs hardcoded the legacy un-tiered
      `market-data-tick-{ag}-{project_id}` form; canonical (bucket_name_ssot Phase 0e) is env-tiered
      `market-data-tick-{ag}-{env}-{project_id}` (prod→`prd`; PREDICTION→`pred`), resolved via `resolve_bucket_name()`.
      Fixed the codex SSOT `codex/02-data/per-asset-group-bucket-layouts.md` (matrix + resolver-authority note),
      `GCS_PATHS.md` (env-tiered table + codex pointer), + env-tiered every bucket ref across 8 MTDS docs + 11 codex
      docs (`prediction-schema-paths`, `availability-manifest-and-data-status`, `chart-candle-delivery-flow`,
      `partitioning`, `subscription-model`, `expected-absence-backfill-runbook`, `quality-gates`, 3× sports docs,
      `live-pipeline-architecture`, `sports-integration-plan`, `04-architecture/README`) —
      market-tick-data-service@9acbee1 + this commit. Only intentional legacy-example lines (deprecation notes +
      phase-2-6 cutover-runbook "from" state) retain the no-env form.
- [ ] [SCRIPT] P1. **TradFi Pattern-1 cleanup** — **SUPERSEDED → `tradfi_manifest_canonicalisation_2026_06_01.md` E7**
      (0-row guard skips migration + E7 bulk-deletes the 12 hyphen prefixes). Original text retained for reference:
      operator chose "leave GCS, fix docs/code". When greenlit: bulk-delete the ~110k 0-row objects under the 12 `day-*`
      hyphen prefixes (they are not manifest-tracked; a real Massive backfill writes canonical paths). Pre-delete guard:
      assert each object is 0-row before deletion; abort the prefix if any non-empty object appears (would mean real
      data, not a phantom). Recommended: extend `_migrate_tradfi_hyphen_rewriter` with a `--delete-empty-only` mode
      using `gcs_delete_object` (UTL, workers=32) — NOT subprocess gsutil.
- [ ] [SCRIPT] P1. **CeFi Pattern-2 migration** — **SUPERSEDED → `cefi_manifest_canonicalisation_2026_06_01.md` E2**
      (`migrate_cefi_flat_to_v9_canonical.py` L-flat branch already does exactly this). Original text retained for
      reference: for each of the 9 root files: read footer → derive
      `day`/`asset_group=cefi`/`venue`/`instrument_type`/`data_type` from the row contents (`exchange`, `data_type`,
      `symbol`, ts→day) → copy to canonical path via `gcs_copy_object` → verify row-count parity → `gcs_delete_object`
      the root copy. Pre-check: if the canonical target already exists, compare row-parity before overwrite (rename to
      `_migrated_{ts}` on mismatch, per existing rewriter collision pattern). Multi-day files (if any span >1 day) must
      be split per `day=`.
- [ ] [SCRIPT] P2. **Guard against recurrence.** Add a QG/CI check (or a `data_catalog` lint) that fails if any object
      under `raw_tick_data/by_date/` does not match `^raw_tick_data/by_date/day=\d{4}-\d{2}-\d{2}/`. Catches both hyphen
      partitions and root-level files in future.

## Verification

- Doc fix: `rg 'day-\{|data_type-|/by_date/day-' market-tick-data-service/docs/` returns 0 path-spec hits.
- Pattern 1 (post-execution): `gcloud storage ls gs://market-data-tick-tradfi-*/raw_tick_data/by_date/ | grep -c 'day-'`
  → 0.
- Pattern 2 (post-execution): `gcloud storage ls gs://market-data-tick-cefi-*/raw_tick_data/by_date/*.parquet` → 0
  objects; the 9 instruments readable at their canonical `day=.../data_type=.../` paths with matching row counts.

## Evidence (audit session 2026-06-01)

- Manifest `pipeline_mode` value-counts: `batch_databento` 348,724 · `batch_barchart` 4,655 · `None` 225,993 ·
  MASSIVE 0.
- TradFi `day-` object counts per day: 3 / 3 / 11242 / 11333 / 11333 / 11173 / 11173 / 11336 / 11132 / 11132 / 10834
  / 4.
- CeFi root files: 9 × real data, 47 KB–13.5 MB, written 2026-05-04.
- `MASSIVE_API_KEY` secret createTime: 2026-05-29T08:47:29Z (post-dates all Pattern-1 writes by 3.5 months).
