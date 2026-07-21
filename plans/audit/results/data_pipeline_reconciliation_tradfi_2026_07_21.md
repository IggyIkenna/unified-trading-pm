---
doc_type: audit-result
title: "Data-pipeline reconciliation — tradfi (2026-07-21)"
summary: >-
  Four-surface canonicalisation reconciliation of asset_group=tradfi over PROD buckets only (read-only), run while a
  live MVP backfill was writing. KEY CORRECTION of a same-session operator-facing claim: catalogue/paths/filenames/
  forward-writes ARE canonical, but historical manifest + parquet-content instrument_id form is only 30.8% canonical
  among captured single-instrument rows (0% pre-2023) — NOT the ~99.65% claimed. batch_massive CONFIRMED fully purged (0
  objects/rows across GCP tick+IS+AWS+manifest) — 4 codex docs still calling it pending are stale. Consolidated index
  was LOCKED mid-consolidation (58 outstanding per-VM shards) — all S3 counts are lower bounds. Purge plan identified
  ~47GB reclaimable (migration_backup/quarantine/needs_attribution, since deleted) + one only-copy hazard (107 CME MBO
  monoliths, 2.53GB, migrate-first).
status: partial
nature: record
asset_group: [tradfi]
stage: [data]
repos:
  [unified-trading-pm, unified-api-contracts, unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    canonicalisation,
    four-surface,
    tradfi,
    delete-safety,
    non-canonical-paths,
    manifest,
    databento,
    massive-purge,
  ]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    orphan-object-detection,
    tradfi-databento-sourcing-ssot,
    tradfi_consolidated_closeout_2026_07_18,
    tradfi_docs_reconciliation_findings_2026_07_21,
  ]
created: 2026-07-21
auditor: /data-pipeline-reconciliation (tradfi, run during a live MVP backfill — second execution)
parent_epic: infrastructure_master
severity: P1
audited_scope:
  "asset_group=tradfi, PROD (-prd-) buckets only, read-only, Tier-1 in-session; sample = full manifest census (lower
  bound, index locked) + full catalogue census + sampled id/schema (<=500 objects) + non-canonical-path register sweep"
date: 2026-07-21
resulting_plan:
lib_version:
doc_versions_checked:
---

# Data-pipeline reconciliation — `asset_group=tradfi` (PROD, read-only)

- **Run:** `/data-pipeline-reconciliation --asset-group tradfi`, Phases 0→2, Tier-1 (in-session) only.
- **Date:** 2026-07-21 (UTC). **Clouds:** GCP `central-element-323112` + AWS `427895769566`.
- **Mode:** strictly READ-ONLY. No GCS write, no manifest write, no delete, no backfill, no Tier-2 VM.
- **Venv:** `market-tick-data-service/.venv` (imports both UTL 1.6.0 and UAC). `GCP_PROJECT_ID` set; buckets via
  `resolve_bucket_name(...)`.
- **Reality caveat:** the tradfi backfill is **RUNNING NOW** — 58 outstanding per-VM shards (CME/NYSE `ohlcv_1m`)
  written seconds before this read; the consolidated `_index` is **LOCKED / mid-consolidation**. Every S3 count below is
  a **lower bound on a moving target**. This run tests canonicality + four-surface consistency, NOT completeness.

---

## ⭐ VERDICT (lead)

**The resting tradfi estate is NOT uniformly canonical or four-surface-consistent — it is BIFURCATED.** Forward/live
writes and the reference catalogue are canonical; the historical resting estate is largely NOT (numeric/bare
instrument-ids pending the operator-gated physical migration).

- **Canonical & clean:** the S4 catalogue (`prod/catalog.parquet`, 836,961 rows, full canonical ids, UPPERCASE type
  enum, fresh today); the IS reference manifest; and the **live-day GCS paths** (lowercase in-vocab `instrument_type`,
  canonical venues/data_types, `batch_databento`/`batch_yahoo`/`live_databento`).
- **NOT canonical (migration state):** the **manifest instrument-id form** — among **captured single shards only 30.8 %
  carry a canonical `instrument_id`; 68.7 % are bare-symbol or raw numeric** (`SRE`, `uint32 56340`). 0 % in 2020-2022,
  ~28-34 % in 2023-2026. This is on structurally-canonical paths — it is an **id-FORM** defect, not a path-structure
  defect, and the codex already declares tradfi's manifest expected-non-canonical wholesale (migration `--apply`
  operator-gated).

### 🔴 BIG FINDINGS (data-correctness / SSOT contradiction — operator attention)

1. **SSOT-vs-reality contradiction — MASSIVE IS ALREADY PURGED, but the codex says it is pending.**
   `pipeline_mode=batch_massive` = **0 objects across all 2,039 GCS `day=` prefixes**, **0 rows in the tick manifest**,
   **0 in the IS manifest**, and **AWS is empty (0 objects)**. Yet `reconciliation-finding-taxonomy.md` AE-4,
   `non-canonical-path-inventory.md` row 10 ("1,696,166 objects — HUMAN-ONLY HARD STOP"),
   `gcs-and-manifest-delete-safety-protocol.md` §3.3, and `tradfi-databento-sourcing-ssot.md` all still describe the
   ~1.47-1.7 M Massive purge as a **pending human-only hard stop with read-recognition deliberately kept**. **The purge
   has executed; those four codex docs are STALE.** Register-patch stanza below (§ Register patch).

2. **A session claim of "migration complete (~99.65-99.84 % canonical derivatives)" is OVERSTATED for the resting
   estate.** On the manifest/id surface the captured-single canonical-id fraction is **30.8 % (lower bound)**, not
   ~99.65 %. The claim may hold for a narrower slice (forward-only writes, or path-STRUCTURE-only, where live paths are
   canonical), but it is **not true of the resting id-form estate**. The physical content-migration (copy→verify→delete
   to canonical ids) is operator-gated and **has not run** on the bulk of history.

3. **Consolidated `_index` is LOCKED / mid-consolidation** (consolidator instance `1-9bd305ec`, lock held 08:45:51Z;
   last run a no-op with `error_reason:"locked"`; 58 outstanding per-VM shards). Every S3 count is a lower bound; no
   S3-derived delete may rise above `unknown` on locked shards.

---

## Phase 0 — Bucket-paths table + resolution/reachability gate

| Surface / kind                              | Cloud | Resolved bucket                                       | Reachable                           | Notes                   |
| ------------------------------------------- | ----- | ----------------------------------------------------- | ----------------------------------- | ----------------------- |
| raw-tick (`market-data`, S1/S2/S3)          | GCP   | `market-data-tick-tradfi-prd-central-element-323112`  | ✅ YES                              | primary target          |
| instruments-store (`instruments-store`, S4) | GCP   | `instruments-store-tradfi-prd-central-element-323112` | ✅ YES                              | catalogue + IS manifest |
| raw-tick (`market-data`)                    | AWS   | `market-data-tick-tradfi-prd-427895769566`            | ✅ reachable, **EMPTY (0 objects)** | no tradfi data on AWS   |
| instruments-store                           | AWS   | `instruments-store-tradfi-prd-427895769566`           | ✅ reachable, **EMPTY (0 objects)** | no tradfi data on AWS   |

- No resolved name carries `-test-` (refusal condition not triggered). Buckets resolved from `cloud-providers.yaml` via
  `resolve_bucket_name(cloud, kind, asset_group="tradfi", deployment_env="prod")` — never inline `gs://`, never
  `PATH_REGISTRY`.
- **Raw-tick top-level children:** `_index/`, `_migration_backup/`, `_migration_backup_2026_07_09/`,
  `_needs_attribution/`, `_quarantine/`, `_vm_staging/`, `backfill-logs/`, `configs/`, `databento-batch-registry/`,
  `processed_candles/`, `raw_tick_data/`. No top-level `day=`/`pipeline_mode=`/`batch_massive`.
- **IS top-level children:** `_catalogue/`, `_index/`, `_vm_staging/`, `instrument_availability/`, `prod/`. **No stale
  `prd/catalog.parquet`** (register row 2 affects defi+pred only — tradfi confirmed clean).

### Index freshness / lock state (§ 2d — decisive)

| File (raw-tick `_index/`)              | Value                                                                                            | Meaning                                                 |
| -------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------- |
| `availability_index.parquet`           | 103.3 MB, 5,846,844 rows, updated **08:45:03Z today**                                            | consolidated manifest read for this run                 |
| `consolidator.lock`                    | present, `instance 1-9bd305ec`, started **08:45:51Z**                                            | **LOCKED — consolidation in progress**                  |
| `latest.json`                          | `no_op:true, error_reason:"locked", shards_scanned:0` @08:46:41Z                                 | last run did nothing (lock contention)                  |
| `consolidator_stall_state.json`        | `streak:0, baseline_shards:59`                                                                   | not stalled                                             |
| `_index/per_vm/`                       | **58 shard objects**, newest 08:47:20Z (`tradfi-bf-cme-ohlcv-1m-*`, `tradfi-bf-nyse-ohlcv-1m-*`) | **outstanding, NOT yet consolidated** — active backfill |
| `phantom_audit_latest.json`            | `phantom_count:1635` @**2026-07-14**                                                             | published phantom count, a week STALE                   |
| `reprobe_audit_latest.json`            | all zeros @2026-07-14                                                                            | stale                                                   |
| IS `_index/availability_index.parquet` | 889 KB, 27,200 rows, @09:02Z, **no lock**                                                        | IS manifest fresh, unlocked                             |
| IS `prod/catalog.parquet`              | 12.4 MB, 836,961 rows, @today                                                                    | S4 catalogue fresh                                      |

**Consequence:** the consolidated index read (08:45:03Z) predates 58 outstanding shards → **all tick-manifest (S3)
counts are lower bounds and a moving target.** Read with pyarrow column-projection over the consolidated index
(single-walk-exempt); no corpus walk opened.

### Suppression inputs loaded (accepted-exception list applied BEFORE emitting)

| AE                            | What                                              | Applied                                                                    |
| ----------------------------- | ------------------------------------------------- | -------------------------------------------------------------------------- |
| AE-2                          | tradfi `combo` bare-`underlying=` carve-out       | combo bundles NOT flagged as `non_canonical_path`                          |
| AE-4                          | `batch_massive` read-recognition kept until purge | **N/A this run — measured 0 batch_massive everywhere (see BIG FINDING 1)** |
| C2a (§5.1, migration_pending) | manifest `instrument_type` COLUMN case            | compared **case-insensitively**; **no casing finding emitted**             |

---

## Phase 1 — Four-surface verdict per shard-class (four bits, never collapsed)

`require_pipeline_mode=True` (per cutover register §2, effective 2026-05-19). Oracle = UAC `canonical_path_violations()`
(structure only). Id-FORM checked **separately** on a sample (§ S2). "Which of the two questions was machine-checked" is
stated per row.

| Shard class                                                                                                     | S1 path (structure / id-form)                                                                     | S2 content (schema / id-form)                                                                           | S3 manifest (atom / id-form)                                                          | S4 catalogue                       |
| --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ---------------------------------- |
| **Singles — FORWARD (2026, live writers)** e.g. `venue=KRX/instrument_type=equity`, `FX/spot_pair`, `ICE/index` | ✅ structure canonical · ✅ stem = full canonical id (`KRX:EQUITY:000660-USD.parquet`)            | ✅ schema PASS (contract exists) · ✅ content `instrument_id` canonical, == stem                        | ⚠️ atom OK · id-form MIXED (see split below)                                          | ✅ canonical                       |
| **Singles — LEGACY (2020-2022, pre-migration)** e.g. `CME/instrument_type=future`                               | ❌ stem non-canonical (`ticks.parquet`, `E1AF0_C3225`, `42854.parquet`) · structure canonical     | ✅ schema PASS (`ts_event` tz-aware UTC) · ❌ content `instrument_id` = **raw uint32** (`56340`)        | ⚠️ atom OK · ❌ id-form bare/numeric                                                  | ✅ (catalogue holds canonical ids) |
| **Chains (`futures_chain`/`options_chain`) — FORWARD**                                                          | ✅ structure canonical (`underlying=/quote=/margin=/ticks.parquet`) · stem `ticks` legit (bundle) | ✅ schema PASS (validate_dataframe) · ✅ content id canonical (`CME:FUTURE:PALLADIUM-USD@LIN-20260918`) | ✅ atom carries quote/margin · id null-by-design (pattern #2)                         | ✅ canonical                       |
| **Chains — per-contract legacy** (`data_type=options_chain`, 112,839 rows, CME, captured, 2023-2026)            | ❌ non-canonical (per-contract shape, `data_type=options_chain` is not a data_type)               | content-needed (pending rebundle REDUCE)                                                                | ❌ `data_type=options_chain` non-canonical axis value; `underlying=ESM1`-per-contract | n/a                                |
| **`combo`**                                                                                                     | AE-2: bare `underlying=/ticks.parquet` — **suppressed** (not flagged)                             | id-form unsettled (AE-2) — combo leg-id grammar deliberately open                                       | ⚠️ 1.33 M rows, ~49 % null id (by design)                                             | catalogue COMBO 59,103 canonical   |
| **Legacy off-path pockets** (`day=/venue=CME/ticks.parquet`; `day=/data_type=/...`; `day-2026-01-01/`)          | ❌ `non_canonical_path` (missing `pipeline_mode`/`asset_group`/etc.)                              | mixed (monoliths = numeric MBO ids; data_type-pockets = canonical filenames)                            | mostly no atom (off-canonical-path)                                                   | n/a                                |

**Machine-checked, stated explicitly:** the path-STRUCTURE question was machine-checked by the oracle (live-day descent
= clean canonical). The **id-FORM** question was checked **separately** — on the manifest (S3, whole-index) and on a
**SAMPLE of ≤500 objects** (S1/S2, Tier-1). Neither the id-form nor the schema was validated at 100% — that requires the
Tier-2 walk (not run).

### S3 distinct-value census (manifest, 5,846,844 rows — lower bound, index locked)

| Axis                                            | Distinct values (count)                                                                                                                                            | Verdict                                                                                                                                                   |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `asset_group`                                   | `tradfi` (5,846,844)                                                                                                                                               | ✅ sanity                                                                                                                                                 |
| `pipeline_mode`                                 | `batch_databento` 5,799,782 · `batch_yahoo` 42,383 · `batch_barchart` 4,655 · `live_databento` 24                                                                  | `batch_barchart` = **`non_canonical_axis_value` (S3)** — legacy, all rows `empty_confirmed`                                                               |
| `venue`                                         | CME, NYSE, NASDAQ, ICE, KRX, CBOE, FX (all canonical) · **BARCHART 9,119**                                                                                         | `BARCHART` = **`non_canonical_axis_value` (S3)** — retired venue, all 9,119 rows `empty_confirmed`                                                        |
| `instrument_type` (case-folded, C2a suppressed) | equity, etf, future, combo, index, spot_pair, options_chain, futures_chain (all canonical) · **`futures` 16 · `spot` 2** · blank/null 413,740                      | `futures`/`spot` = **`non_canonical_axis_value` (S3)**, 18 rows (content-repair). Blank on 306,559 `attempted_failed` (benign) + 2,229 `captured` (minor) |
| `data_type`                                     | ohlcv_1s/1m/24h/15m, mbp_10, trades, tbbo, corporate_action_confirmed, earnings_result, macro_result (canonical) · **`options_chain` 112,839 · `futures_chain` 8** | `options_chain` = **`non_canonical_axis_value` (S3/data_type)** — the known per-contract-chain-pending-rebundle                                           |
| `source`                                        | databento 5,799,806 · yahoo 42,383 · **barchart 4,655**                                                                                                            | `barchart` = legacy `non_canonical_axis_value`, all empty                                                                                                 |
| `chain`                                         | null / blank only                                                                                                                                                  | ✅ n/a for tradfi (blank sentinel)                                                                                                                        |
| `capture_status`                                | empty_confirmed 3,500,799 · captured 1,653,247 · expected_unattempted 385,985 · attempted_failed 306,813                                                           | 4-state honest                                                                                                                                            |

**M vs G (census comparison c, `shard_atom_vocab_desync`):** case-folded, the S1 (live-day GCS descent) and S3
instrument_type/venue/data_type vocabularies **AGREE** on the canonical set. Manifest UPPERCASE variants = C2a
migration_pending fold (suppressed). No true vocabulary desync detected on sampled days.
`batch_barchart`/`BARCHART`/`barchart` exist only in S3 (all `empty_confirmed`, no GCS objects) — not a desync, legacy
empty rows.

### S2 content — id-form + schema (SAMPLE ≤500, Tier-1 — NOT the full corpus)

- **id-canonical (G2):** three cohorts observed — legacy 2020 (`ts_event` tz-aware UTC + **raw uint32 `instrument_id`**
  → `non_canonical_id`); forward chain 2026 (`timestamp` int64-nanos + canonical string id); forward single 2026
  (`timestamp` string + canonical string id). Forward objects PASS stem==id byte-equality; legacy fail (numeric ids).
- **schema (G3):** ran the authoritative UAC `validate_dataframe(df, lookup_contract(...))`. Sampled objects **PASS**
  where a contract exists (`future/ohlcv_1m`, `futures_chain/ohlcv_1m`). **No contract registered** for
  `spot_pair/ohlcv_24h` or `equity/ohlcv_24h` → G3 **not-assessable** for daily equity/FX singles (contract-coverage
  gap, not a data defect). My initial tz heuristic falsely flagged int64/string timestamps — **retracted**; the real
  validator accepts them.
- **Label:** id/schema **validated on a SAMPLE of ≤500, NOT the full corpus.** 100% requires a Tier-2 per-datapoint VM
  (not dispatched this run).

### Manifest-wide id-form split (S3, the "99.65% canonical" test)

| Cohort                                      | canonical id | non-canonical id                                                   | % canonical                 |
| ------------------------------------------- | ------------ | ------------------------------------------------------------------ | --------------------------- |
| All rows                                    | 2,410,420    | 1,742,340 (+ 970,925 null [chain/combo by design] + 723,159 blank) | —                           |
| **Captured SINGLE rows** (fair denominator) | 347,811      | **775,732**                                                        | **30.8 %**                  |
| — 2020/2021/2022                            | 0            | all                                                                | **0.0 %**                   |
| — 2023 / 2024 / 2025 / 2026                 | —            | —                                                                  | 27.3 / 31.8 / 34.3 / 28.7 % |

**`reachable_coverage`** (formula = `captured / (captured + attempted_failed + expected_unattempted)`, `empty_confirmed`
EXCLUDED, per `honest-coverage-model.md`) = 1,653,247 / 2,346,045 = **70.5 % — LOWER BOUND** (index locked, 58 shards
outstanding, all AGs gate Layer-2 `instrument_gates_download=true`). Coverage is not this run's question; stated with
formula per contract.

### S4 catalogue — CLEAN

`prod/catalog.parquet`: 836,961 rows; id col canonical (`CBOE:FUTURE:VIX-USD@LIN-20200617`); `instrument_type` UPPERCASE
(OPTION 767,244 · COMBO 59,103 · FUTURE 4,717 · SPOT_PAIR 4,545 · EQUITY 1,219 · ETF 115 · INDEX 18); venues all
canonical; `mvp` False 766,031 / True 70,930 (narrow tradfi MVP by design). IS manifest: 27,200 rows,
`pipeline_mode=batch_instruments_service`, `source=instruments_service`, UPPERCASE type, **0 massive**.
`data-catalogue.*.yaml` staleness = standing known condition (reported once, per §3c).

### Typed findings (taxonomy names; suppressed exceptions counted separately)

| #   | type                                                    | severity     | surfaces | shard_atom / scope                                                               | detail                                                                                                                                                       | delete_eligible             | suppressed_by |
| --- | ------------------------------------------------------- | ------------ | -------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------- | ------------- |
| F1  | `non_canonical_id`                                      | MEDIUM       | S2,S3    | captured singles, all venues                                                     | **775,732 of 1,129,056 (68.7%)** captured-single manifest ids bare/numeric; 0% pre-2023. Migration state (operator-gated), not a fresh writer regression     | NO                          | —             |
| F2  | `non_canonical_axis_value` (data_type)                  | MEDIUM       | S1,S3    | CME `data_type=options_chain`                                                    | 112,839 captured rows in per-contract shape, pending the operator-gated `--rebundle` REDUCE (migration design doc)                                           | NO                          | —             |
| F3  | `non_canonical_path`                                    | MEDIUM       | S1       | 107 `day=/venue=CME/ticks.parquet` monoliths (2.53 GB)                           | legacy MBO/depth fan-in (604 numeric ids each), missing pipeline_mode/asset_group/type/data_type; **only-copy** (not duplicated by same-day canonical ohlcv) | NO (migrate-first)          | —             |
| F4  | `non_canonical_path`                                    | LOW          | S1       | 900 `day=/data_type=/…/{id}.parquet` pockets (12 MB) + `day-2026-01-01/` (2 obj) | non-hive pockets; **canonical filenames**; twins CONFIRMED present (see purge plan)                                                                          | via `legacy_duplicate` only | —             |
| F5  | `non_canonical_axis_value` (venue/pipeline_mode/source) | LOW          | S3       | BARCHART / batch_barchart / barchart                                             | 9,119 / 4,655 / 4,655 rows, **all `empty_confirmed`** (no data, no objects); retired Barchart                                                                | NO                          | —             |
| F6  | `non_canonical_axis_value` (instrument_type)            | LOW          | S3       | `futures`(16), `spot`(2)                                                         | 18 rows, content-repair targets                                                                                                                              | NO                          | —             |
| F7  | `catalogue_gap`-adjacent (contract-coverage)            | INFO         | S2       | `spot_pair/ohlcv_24h`, `equity/ohlcv_24h`                                        | no UAC `SchemaContract` registered → G3 not-assessable for daily equity/FX singles                                                                           | NO                          | —             |
| —   | phantom (published)                                     | HIGH-context | S3↔S1    | tradfi                                                                           | `phantom_count=1635` @2026-07-14 (STALE, read not re-run) — a lower bound, pre-dates current wave                                                            | NO                          | —             |

**Suppressed accepted-exception counts (proving suppression happened):** C2a instrument_type casing — **~2.87 M
`equity`/`EQUITY` + 0.33 M `etf`/`ETF` + 0.40 M `future`/`FUTURE` + 1.33 M `combo`/`COMBO` + … rows compared
case-insensitively, 0 casing findings emitted** (pointer: `reconciliation-finding-taxonomy.md` §5.1). AE-2 combo
bare-underlying — **~1.33 M rows suppressed** (pointer: taxonomy §4 AE-2). AE-4 batch_massive — **0 rows to suppress
(already purged)**.

---

## Phase 2 — Non-canonical sweep + register reconciliation

Register→reality re-verification of `non-canonical-path-inventory.md` rows scoped to tradfi (I did **not** edit the
shared register — concurrency; patch stanza below):

| Register row | Claim                                                                                      | Reality (measured 2026-07-21)                                                                                                                                                    | Disposition change                                             |
| ------------ | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **10**       | `batch_massive` 1,696,166 objects, HUMAN-ONLY HARD STOP, read-recognition kept             | **0 objects (all 2,039 days) + 0 manifest rows + 0 AWS**                                                                                                                         | **RETIRE — purge EXECUTED** (see BIG FINDING 1)                |
| **11**       | tradfi legacy: hyphen 100,698 · non-hive 920 · chain-addqm 528,961 · single-rename 389,703 | hyphen → **2 objects** remain (99.998% migrated); off-path pockets → 1,007 objects / 2.55 GB; chain/single legacy id-form persists on-canonical-path (68.7% of captured singles) | UPDATE counts — bulk migrated; id-form migration still pending |
| **19**       | `databento-batch-registry/{sha}.json` sanctioned operational                               | present, 7,146 objects / 0.01 GB                                                                                                                                                 | unchanged (accepted)                                           |
| **22**       | tradfi QUARANTINE garbage-underlying 14,633 + corrupt 1,180                                | `_quarantine/` = **146,288 objects / 7.18 GB** (garbage combos `underlying=12/13/23` confirmed)                                                                                  | UPDATE count                                                   |
| **24**       | `_needs_attribution/` two nesting conventions                                              | present: **71,830 objects / 4.01 GB** (`category=tradfi` + `pipeline_mode=` shapes, `ticks_migrated_*`)                                                                          | UPDATE count                                                   |

Reality→register (NEW locations found, not in register): `_migration_backup_2026_07_09/raw_tick_data/` (**158,808
objects / 35.91 GB**, pre-migration backup) and `_migration_backup/manifest_dedup_2026_07_10/` (1 obj / 0.12 GB).
Orphans: **NOT ASSESSED** (no whole-corpus walk in this run — per `orphan-object-detection.md` §3, a manifest-driven
pass may not claim "0 orphans").

### Register patch (apply serially — do NOT hand-edit inline during concurrent AG runs)

```
# non-canonical-path-inventory.md
- Row 10 (batch_massive): MOVE to "Entry retired 2026-07-20/21 (audit trail)".
  Disproof: measured 2026-07-21 — 0 objects across all 2039 GCS day= prefixes,
  0 tick-manifest rows, 0 IS-manifest rows, AWS both buckets empty. Purge EXECUTED.
  ⇒ ALSO update: reconciliation-finding-taxonomy.md AE-4, gcs-and-manifest-delete-safety-protocol.md §3.3,
     tradfi-databento-sourcing-ssot.md — all four still describe the purge as PENDING; they are STALE.
- Row 11: update measured counts — hyphen 2 (was 100,698); off-path pockets 1,007 obj / 2.55 GB.
- Row 22: _quarantine/ measured 146,288 obj / 7.18 GB (was ~15,813).
- Row 24: _needs_attribution/ measured 71,830 obj / 4.01 GB.
- NEW rows: _migration_backup_2026_07_09/ (158,808 obj / 35.91 GB, pre-migration backup, disposition yes-after-verify);
           _migration_backup/manifest_dedup_2026_07_10/ (1 obj / 0.12 GB, manifest snapshot).
```

---

## 🧹 PURGE PLAN (executable by the main agent — I did NOT delete anything)

> Operator authorization (relayed) lifts the human-only hard stops for THIS run's execution. All prod-bucket deletes
> remain the **main agent's** action, gated on the proofs below. This section is a plan; my run stayed read-only.

### 1. MASSIVE — footprint to purge

| Location                                                    | Cloud | batch_massive objects                      | batch_massive manifest rows | Action                                 |
| ----------------------------------------------------------- | ----- | ------------------------------------------ | --------------------------- | -------------------------------------- |
| `market-data-tick-tradfi-prd-central-element-323112` (tick) | GCP   | **0** (verified all 2,039 `day=` prefixes) | **0** (5.85 M-row index)    | **NOTHING TO DELETE — already purged** |
| `instruments-store-tradfi-prd-central-element-323112` (IS)  | GCP   | **0**                                      | **0** (27,200-row index)    | nothing                                |
| `market-data-tick-tradfi-prd-427895769566`                  | AWS   | **0 (bucket empty)**                       | n/a                         | nothing                                |
| `instruments-store-tradfi-prd-427895769566`                 | AWS   | **0 (bucket empty)**                       | n/a                         | nothing                                |

**Massive footprint = 0 objects, 0 bytes, 0 manifest rows.** The purge already executed. **No delete action required.**
(Verification method: per-day delimiter descent for a `pipeline_mode=batch_massive/` child across all 2,039 days + full
manifest census + AWS paginated listing. Not observed anywhere, including inside
`_migration_backup*`/`_quarantine`/`_needs_attribution` samples.) The only residual work is the **codex stale-doc
correction** (register patch above).

### 2. LEGACY NON-CANONICAL — 5-part-proof dispositions

| Target                                                                                                   | Objects / bytes                               | Twin (Part 1 `gcs_describe_object`)                                                                                                                          | Content (Part 2)                                               | Writes (Part 3)                                                      | Reads (Part 4)                             | Copied-not-moved (Part 5) | **Disposition**                                                                                                                                                                                                 |
| -------------------------------------------------------------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------ | ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A. `day=/data_type=ohlcv_1m/{etf,equity}/…/{canonical-id}.parquet` pockets**                           | 900 obj / ~12 MB                              | ✅ canonical `batch_databento` twin **RESOLVES** (verified `ARKB`,`IBIT`: twin present, **larger/fresher** than legacy)                                      | ⚠️ sizes differ (twin larger) — spot-verify rows before delete | live single writer emits canonical path (not this pocket)            | not read (canonical path is the live read) | twin is separate object   | **`yes-after-verify`** — delete AFTER a row-level content spot-check confirms twin ⊇ legacy (the running backfill already re-captured these)                                                                    |
| **B. `day-2026-01-01/data_type-{tbbo,trades}/`**                                                         | 2 obj / 4.6 KB                                | not probed (fully non-hive)                                                                                                                                  | fan-in of unknown content                                      | superseded writer (raises on this shape)                             | none found                                 | —                         | **`unknown` → migrate-first** (tiny; content-read to attribute, or accept loss with operator OK)                                                                                                                |
| **C. `day=/venue=CME/ticks.parquet` monoliths**                                                          | 107 obj / **2.53 GB**                         | ❌ **NO single twin** — content is MBO/depth (604 numeric ids/file), NOT duplicated by same-day canonical ohlcv; on `day=2026-02-22` it is the ONLY CME data | fan-in, numeric ids                                            | superseded (writer now RAISES on symbol-less tradfi `ticks.parquet`) | unknown (mbp_10 readers?)                  | —                         | 🔴 **`no-migrate-first` — ONLY-COPY.** Do NOT blind-delete. Content-read → derive canonical `mbp_10` ids → write canonical → then delete. If databento-sourced, the running backfill can re-capture then delete |
| **D. On-canonical-path legacy id-form** (2020-2022 numeric-id singles/chains; 68.7% of captured singles) | not enumerable in-session (needs Tier-2 walk) | these ARE at canonical-STRUCTURE paths; only the filename/id is legacy                                                                                       | numeric/bare ids                                               | superseded writers                                                   | live readers resolve by manifest           | —                         | 🔴 **`no-migrate-first`** — the operator-gated content-migration executor's job (`migrate_tradfi_canonical_2026_07.py`), NOT a delete                                                                           |
| **E. per-contract `data_type=options_chain`**                                                            | 112,839 rows (~148 K obj per migration doc)   | canonical bundle twin does NOT yet exist (rebundle pending)                                                                                                  | content-needed (only copy of that options data)                | —                                                                    | —                                          | —                         | 🔴 **`no-migrate-first`** — run `rebundle_tradfi_chains_2026_07.py --apply` FIRST                                                                                                                               |

### 3. STORAGE ESTIMATE (reclaimable)

| Bucket                              | (a) Massive purge | (b) Twin-confirmed legacy delete                      | (c) Held for migrate-first (only-copy)                                                                             | Operator-decision cleanup                                                                                                                                                                                                                                                                                                         |
| ----------------------------------- | ----------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `market-data-tick-tradfi-prd` (GCP) | **0 GB** (done)   | ~**12 MB** (pocket group A, after content spot-check) | **2.53 GB** monoliths (C) + on-path legacy id-form (D, not sized — needs Tier-2 walk) + options_chain rebundle (E) | see below                                                                                                                                                                                                                                                                                                                         |
|                                     |                   |                                                       |                                                                                                                    | `_migration_backup_2026_07_09/` **35.91 GB** (158,808 obj, pre-migration backup — reclaimable once migration verified good) · `_quarantine/` **7.18 GB** (146,288 garbage/corrupt) · `_needs_attribution/` **4.01 GB** (71,830 unattributable) · `_migration_backup/` 0.12 GB · `_vm_staging/` 0.04 GB · `backfill-logs/` 0.06 GB |
| AWS (both)                          | 0 (empty)         | 0                                                     | 0                                                                                                                  | 0                                                                                                                                                                                                                                                                                                                                 |

- **Immediately reclaimable, low-risk:** `_migration_backup_2026_07_09/` (**35.91 GB**) — a pre-migration snapshot of
  `raw_tick_data`; delete once the migration is confirmed good (verify a sample of its objects have live canonical twins
  first). This is the single largest safe win.
- **Reclaimable, operator-decision:** `_quarantine/` (7.18 GB garbage-underlying/corrupt, no twin by definition —
  deleting = accepting loss of un-canonicalizable data) + `_needs_attribution/` (4.01 GB). Register row 22 flags
  "retain-or-purge" as an open question — the operator's storage-saving mandate answers it toward purge, but these are a
  judgment call, not a mechanical delete.
- **Held for migrate-first (do NOT delete yet):** monoliths 2.53 GB (C) + the on-canonical-path legacy id-form bulk (D,
  unsized) + per-contract options_chain (E). These are only-copies or content-needed.
- **Total measured cleanup opportunity (excl. the unsized on-path id-form bulk):** ~**49.7 GB** — of which ~**47.9 GB is
  safe-after-verify** (35.91 backup + 7.18 quarantine + 4.01 needs_attribution + small + 0.012 twin-confirmed) and
  ~**2.5 GB is migrate-first only-copy** (monoliths). `processed_candles/` was NOT sized (out of raw-tick scope).

---

## Coverage gaps (what this run did NOT assess)

1. **Orphans: NOT ASSESSED** — no whole-corpus walk (per single-walk discipline). A manifest-driven pass cannot
   enumerate orphans; not claiming "0".
2. **id-form / schema at 100%: NOT ASSESSED** — Tier-1 SAMPLE ≤500 only. The on-canonical-path legacy id-form bulk
   (finding D) is un-enumerated; a Tier-2 read-only per-datapoint VM is required to size it and to certify S2 at 100%.
3. **S3 counts are LOWER BOUNDS** — consolidated index LOCKED + 58 outstanding per-VM shards; live backfill running.
4. **`processed_candles/`** not sized (out of raw-tick scope). **AWS** reachable but empty — nothing measured beyond
   emptiness.
5. **G3 schema** not-assessable for `spot_pair/ohlcv_24h` + `equity/ohlcv_24h` (no UAC contract registered).
6. Register rows re-verified for tradfi only; other-AG rows untouched.

---

## Todos / issue-doc candidates (do not fix inline)

- [ ] **P0 [DOCS]** Retire `non-canonical-path-inventory.md` row 10 + correct AE-4 / delete-safety §3.3 /
      tradfi-databento-sourcing-ssot to reflect Massive purge EXECUTED (SSOT-vs-reality contradiction). → register patch
      above.
- [ ] **P1 [DATA]** Operator-gated content-migration of the on-canonical-path legacy id-form bulk (68.7% of captured
      singles carry numeric/bare ids) — `migrate_tradfi_canonical_2026_07.py --apply` + manifest rebuild; this is what
      makes the "~99.65% canonical" claim true.
- [ ] **P1 [DATA]** Run `rebundle_tradfi_chains_2026_07.py --apply` for the 112,839 per-contract
      `data_type=options_chain` rows.
- [ ] **P2 [DATA]** Content-migrate the 107 `day=/venue=CME/ticks.parquet` MBO monoliths (only-copy) to canonical
      `mbp_10`; then the 900 twin-confirmed pockets are safe to delete.
- [ ] **P2 [UAC]** Register UAC `SchemaContract` for `(tradfi, spot_pair, ohlcv_24h)` and `(tradfi, equity, ohlcv_24h)`
      (G3 coverage gap).
- [ ] **P3 [DATA]** Re-run the phantom auditor (published count 1635 is a week stale, pre-dates the current wave).

```

```
