---
doc_type: audit-result
title: "Data-pipeline reconciliation — tradfi raw-tick (2026-07-24)"
summary: >-
  Four-surface canonicalisation reconciliation of asset_group=tradfi, layer=raw-tick, over PROD GCS only (read-only).
  Third run in the tradfi campaign (after 2026-07-20, 2026-07-21). Path-STRUCTURE and manifest-instrument-id-FORM
  canonicality have improved dramatically since 2026-07-21 (id-form for captured singles now ~99.3% by an id-shape check
  vs the 30.8% previously measured), consistent with the operator-gated content-migration having executed in the
  interim. TWO NEW live findings not previously reported: (1) Yahoo-exclusive venues ICE/KRX (and a longer-running FX
  companion pattern) are being captured under pipeline_mode=batch_databento/source=databento since ~2026-07-18,
  contradicting the sourcing SSOT and UAC's own routing code — a live, ongoing SSOT-vs-code contradiction; (2) the
  tradfi FX SPOT_PAIR manifest instrument_id is 0% canonically-formed across its entire 2020-2026 captured history
  (2,943 blank + rest bare/legacy), even though the real GCS object + its content ARE correctly formed — a pure S3
  (manifest) defect invisible to path-structure checks. `_quarantine/` has grown from a 07-21-measured 146,288 objects
  to >=400,000 objects in ~3-4 days (capped enumeration; true count higher) — the register is badly stale and the growth
  itself needs investigating. batch_massive purge (0 objects) and the AE-2 combo writer/reader path disagreement both
  re-confirmed unchanged from the prior run.
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
    yahoo,
    source-provenance,
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
    data_pipeline_reconciliation_tradfi_2026_07_20,
    data_pipeline_reconciliation_tradfi_2026_07_21,
  ]
created: 2026-07-24
auditor: /data-pipeline-reconciliation (tradfi, raw-tick layer, third execution)
parent_epic: infrastructure_master
severity: P1
audited_scope:
  "asset_group=tradfi, layer=raw-tick, PROD (-prd-) buckets only, read-only, Tier-1 in-session (full manifest census +
  bounded GCS spot-checks + non-canonical-path register sweep); instruments-store (S4) bucket NOT read this run
  (declared coverage gap, see below); AWS NOT checked this run (declared coverage gap)"
date: 2026-07-24
resulting_plan:
lib_version:
doc_versions_checked:
---

# Data-pipeline reconciliation — `asset_group=tradfi`, layer=raw-tick (PROD, read-only)

- **Run:** `/data-pipeline-reconciliation --asset-group tradfi` (raw-tick layer, default — candles explicitly
  out-of-scope for this dispatch). Phases 0→2, Tier-1 (in-session) only.
- **Date:** 2026-07-24/25 (UTC, run spanned the day boundary). **Cloud:** GCP `central-element-323112` only (AWS not
  probed this run — declared coverage gap, §6).
- **Mode:** strictly READ-ONLY. No GCS write, no manifest write, no delete, no backfill, no Tier-2 VM.
- **Venv:** `market-tick-data-service/.venv` (imports both UTL and UAC in one interpreter — verified). `GCP_PROJECT_ID`
  exported before every `resolve_bucket_name` call.
- **Third run in this campaign** — prior runs: `data_pipeline_reconciliation_tradfi_2026_07_20.md`, `…_2026_07_21.md`.
  This run cross-checks their findings for drift rather than re-deriving everything from scratch.

---

## ⭐ VERDICT (lead)

**`asset_group=tradfi` is NOT 100% canonical.** Path STRUCTURE (S1) and filename-stem/content agreement (S1↔S2) are now
very close to clean on sampled evidence (see §3). The estate is however carrying at least two live, currently-active
content/provenance defects that no path-structure check can see, plus the same handful of small vocabulary/legacy
findings the two prior runs already flagged (still present, unchanged in count):

1. 🔴 **NEW — Yahoo-exclusive venues captured under the wrong provenance stamp, live, ongoing since ~2026-07-18.** ICE
   (`DXY` index) and KRX (single-stock equities) — both explicitly Yahoo-only per `tradfi-databento-sourcing-ssot.md`
   and UAC's own `get_dxy_daily_source()` (hardcoded to always return `YAHOO_FINANCE`) — have REAL captured rows stamped
   `pipeline_mode=batch_databento` / `source=databento` for 2026-07-20 through 2026-07-23 (the last 4 fully-elapsed days
   at run time). Content-verified: the actual parquet holds plausible DXY/equity values, correctly typed and named, just
   mislabeled provenance. A structurally-identical, much longer-running (2020→2026) companion pattern exists for FX
   `ohlcv_24h` (802 of ~3,991 captured rows databento-stamped vs the correct yahoo-stamped majority). **Filed as an
   issue doc — see §7.**
2. 🔴 **NEW — tradfi FX `SPOT_PAIR` manifest `instrument_id` is 0% canonically-formed across its ENTIRE history.** 0 of
   4,310 captured FX rows (2020-01-02 → 2026-07-23) carry a well-formed id in the **manifest** column — mostly blank
   (2,812), literal `"ticks"` (983, a bundle-filename leaking into the id field), or a bare pair like `EUR-USD` (501,
   missing the `FX:SPOT_PAIR:` prefix) — even on the LATEST sampled day. The real GCS object is fine: verified directly,
   `FX:SPOT_PAIR:AUD-USD.parquet` exists with matching, correctly-formed content `instrument_id`. This is a pure **S3
   (manifest)** defect, invisible to any path-structure or filename-stem check, and it uniquely singles out FX —
   NASDAQ/NYSE/CME/CBOE/ICE/KRX manifest ids are >99% well-formed by the same check. **Filed as an issue doc — see §7.**
3. 🟡 **Still true, unchanged from 2026-07-21** — `venue=BARCHART` (9,119 rows, all `empty_confirmed`) despite removal
   from `VENUES_BY_ASSET_GROUP["tradfi"]` on 2026-06-24; `instrument_type` typos `FUTURES`(16)/`spot`(2); the AE-2
   adjacent combo writer/reader path disagreement (`symbol_rules.py:259` includes `combo`, `reader.py:62` does not —
   re-verified live in code this run).
4. 🟡 **`_quarantine/` register entry is badly stale and the population is GROWING, not shrinking.** Register row 22
   said "DELETED 2026-07-21" (against a 15,813-object baseline); the SAME-DAY 07-21 reconciliation re-measured it at
   146,288 objects/7.18GB (post-delete); this run measures **≥400,000 objects / ≥8.71GB** (enumeration capped at 400,000
   for time — true count is higher). The quarantine content spot-checked genuinely IS quarantine-worthy
   (oracle-confirmed bad `underlying=` values from an in-flight chain-tail migration), so this looks like healthy
   detection machinery working — but the volume more than doubled in ~3-4 days and nobody is watching it.
5. ✅ **Positive finding — the operator-gated content-migration appears to have executed.** Captured-single-row
   manifest-id canonicality (an id-shape check, not byte-exact) now measures **~99.3%** corpus-wide (99.4-99.6% for
   2023-2026, which dominate row count), a dramatic change from the 07-21 report's measured 30.8%. A
   builder+oracle-based reconstructed-path check (3,000 rows sampled across ALL years 2018-2026) independently confirms
   **99.95% clean** (1,972/1,973 measurable). See §3 for methodology caveats — the two reports' checks are not
   byte-identical, so this is reported as strong directional evidence, not a certified before/after delta.
6. ✅ **`batch_massive` purge holding** — 0 objects, 0 manifest rows, third consecutive run confirming this (07-20 →
   07-21 → this run).

---

## Phase 0 — Bucket-paths table + resolution/reachability gate

| Surface / kind                              | Cloud | Resolved bucket                                                                      | Reachable                                          | Notes                                                                                                                           |
| ------------------------------------------- | ----- | ------------------------------------------------------------------------------------ | -------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| raw-tick (`market-data`, S1/S2/S3)          | GCP   | `market-data-tick-tradfi-prd-central-element-323112`                                 | ✅ YES — non-recursive top-level listing succeeded | primary target, resolved via `resolve_bucket_name(cloud='gcp', kind='market-data', asset_group='tradfi', deployment_env='prd')` |
| instruments-store (`instruments-store`, S4) | GCP   | `instruments-store-tradfi-prd-central-element-323112` (not resolved/probed this run) | ⚠️ **NOT ASSESSED — declared coverage gap**        | this dispatch's scope named only the market-data bucket; S4 catalogue surface is UNAVAILABLE for the whole run, not per-shard   |
| raw-tick / instruments-store                | AWS   | not resolved this run                                                                | ⚠️ **NOT ASSESSED — declared coverage gap**        | prior run (07-21) found both AWS buckets reachable + empty for tradfi; not re-verified this run                                 |

No resolved name carried `-test-` (refusal condition not triggered). `GCP_PROJECT_ID=central-element-323112` exported
before every call; `deployment_env='prd'` passed explicitly (never a tier env-var mutation).

**Raw-tick top-level children** (non-recursive `delimiter='/'` listing via the native `bucket.list_blobs` handle, since
the UTL storage-facade drops `.prefixes`):

```
_index/  _migration_backup/  _quarantine/  _vm_staging/  backfill-logs/  configs/  databento-batch-registry/  processed_candles/  raw_tick_data/
```

Compare to the 07-21 report's list
(`_index/, _migration_backup/, _migration_backup_2026_07_09/, _needs_attribution/, _quarantine/, _vm_staging/, backfill-logs/, configs/, databento-batch-registry/, processed_candles/, raw_tick_data/`):
**`_migration_backup_2026_07_09/` and `_needs_attribution/` are GONE** — consistent with
`non-canonical-path-inventory.md`'s "Entry retired 2026-07-20/21" audit-trail rows recording an operator delete of those
exact locations (158,808 obj/35.91GB and 71,830 obj/4.01GB respectively) shortly after the 07-21 report's purge plan.
**No `batch_massive` top-level presence** (consistent with the purge).

### Index freshness / lock state (§ 2d — decisive)

| File (raw-tick `_index/`)       | Value                                                                                                             | Meaning                                                                                                              |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `availability_index.parquet`    | 96.0 MB, **5,902,157 rows**, tradfi-only (bucket-scoped index)                                                    | consolidated manifest read for this run (downloaded once to `$HOME`, column-projected reads thereafter)              |
| `consolidator.lock`             | **absent** (not listed under `_index/`)                                                                           | **NOT locked** — unlike the 07-21 run, which caught an active lock mid-consolidation                                 |
| `latest.json`                   | `last_run_at=2026-07-24T23:52:47Z, success=true, verdict="empty", shards_scanned=1, incremental=true, no_op=true` | healthy, low-volume incremental — no stall                                                                           |
| `consolidator_stall_state.json` | `streak:0, baseline_shards:2`                                                                                     | not stalled                                                                                                          |
| `_index/per_vm/`                | present (not enumerated — not needed; no lock contention this run)                                                | —                                                                                                                    |
| `phantom_audit_latest.json`     | `phantom_count:1635` @**2026-07-14**                                                                              | published count, now **~10-11 days stale**, unchanged from the value both prior runs cited — read here, never re-run |
| `reprobe_audit_latest.json`     | `new_empties:0, disagreements:0, ambiguous:0, proven:0` @2026-07-14                                               | stale, same date as the phantom audit                                                                                |

**Consequence:** unlike 07-21 (locked index, 58 outstanding shards, all S3 counts explicitly a lower bound), this run's
index read is a **stable, unlocked, fully-consolidated snapshot** — S3 counts below are a faithful point-in-time read,
not a lower bound from a moving target. The phantom/reprobe audits remain ~10 days stale regardless.

### Suppression inputs loaded (accepted-exception list applied BEFORE emitting)

| Input                                      | What                                                                                                                 | Applied                                                                                                        |
| ------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `canonical-cutover-register.md` §2         | `require_pipeline_mode` effective-from **2026-05-19** for tradfi                                                     | oracle called with `require_pipeline_mode=True` throughout                                                     |
| `canonical-cutover-register.md` §4         | tradfi chain-tail (`underlying=/quote=/margin=`) effective-from **2026-07-19**                                       | spot-checked recent chain writes against this shape (§3)                                                       |
| taxonomy §5.1 / cutover-register §3c (C2a) | manifest `instrument_type` COLUMN case — RULED UPPERCASE target, `migration_pending`                                 | compared case-insensitively; **45,426 lowercase rows suppressed, 0 casing findings emitted** (breakdown in §3) |
| taxonomy AE-2                              | tradfi `combo` bare-`underlying=` carve-out                                                                          | combo bundles NOT flagged as `non_canonical_path`                                                              |
| taxonomy AE-4 (CLOSED)                     | `batch_massive` — purge executed, no longer an accepted-exception, a surviving object would now be a genuine finding | N/A — measured 0 everywhere (§3)                                                                               |
| `non-canonical-path-inventory.md`          | living register, tradfi-scoped rows (10, 11, 19, 22)                                                                 | re-verified against reality (§4)                                                                               |

**Refusal condition not triggered** — no resolved bucket name carried `-test-`.

---

## Phase 1 — Four-surface comparison

Oracle = UAC `canonical_path_violations()`, called with `require_pipeline_mode=True` throughout (per the cutover
register, all tradfi data is post-2026-05-19-cutover-eligible for this axis). **Structure and id-FORM are two different
questions** — stated separately per shard class, never collapsed.

### 3a. S1 structural canonicality — sampled, not the full corpus

| Method                                                                                                                                                                                                                                 | Sample                                                                                                                                                                                                                                     | Result                                                                                                                                                                                                         |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Prefix-scoped listing of ONE full day (`day=2026-07-20`, no-walk route #1), random sample                                                                                                                                              | 80 of 307 objects that day                                                                                                                                                                                                                 | **0/80 oracle violations** (`require_pipeline_mode=True`); 62/62 filename-stem == content `instrument_id` (flat-per-contract subset)                                                                           |
| Reconstructed-path check: build the canonical path from each manifest row's OWN axes via `build_tradfi_partition_path`, run the oracle on the constructed path (index-only, no GCS I/O — same method `manifest_hygiene_daily.py` uses) | 3,000 random **captured** rows across full 2018-2026 history; 1,973 had a usable id/chain-axis set to reconstruct from (1,027 skipped — mostly bundle rows with by-design-null manifest id, or the FX defect below making the id unusable) | **1,972/1,973 = 99.95%** clean. The ONE failure is `FX/spot_pair/ohlcv_24h` reconstructing to a literal `ticks.parquet` filename — the SAME FX manifest-id defect as finding #2, not a new/independent defect. |
| Direct GCS content fetch (ICE, KRX, FX, NASDAQ, NYSE samples on 2026-07-20/23)                                                                                                                                                         | 8 objects                                                                                                                                                                                                                                  | All well-formed on disk: filename == content `instrument_id`, correct `VENUE:TYPE:SYMBOL-USD` shape                                                                                                            |

**Verdict:** S1 structure and S1↔S2 (filename-vs-content) agreement are **clean on every sample taken this run**. This
is consistent with (not proof of) the 07-21 report's F3/F4 finding that most legacy off-hive pockets have already been
migrated or are down to small, known, only-copy residuals (monoliths, quarantine — not re-measured at full scale this
run; see §4).

### 3b. S3 manifest-id-form — dramatic apparent improvement since 07-21 (methodology caveat below)

| Cohort (captured, single-instrument shard types: equity/etf/index/future/option/spot_pair/currency/bond/cds/commodity) | n       | canonical-shaped id (regex: `VENUE(-CHAIN)?:TYPE:body`) | %          |
| ---------------------------------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------- | ---------- |
| All years                                                                                                              | 912,486 | 905,796                                                 | **99.27%** |
| 2019                                                                                                                   | 585     | 585                                                     | 100.0%     |
| 2020                                                                                                                   | 1,283   | 576                                                     | 44.9%      |
| 2021                                                                                                                   | 873     | 249                                                     | 28.5%      |
| 2022                                                                                                                   | 1,258   | 576                                                     | 45.8%      |
| 2023                                                                                                                   | 197,075 | 196,010                                                 | 99.5%      |
| 2024                                                                                                                   | 299,755 | 298,469                                                 | 99.6%      |
| 2025                                                                                                                   | 256,375 | 254,958                                                 | 99.4%      |
| 2026                                                                                                                   | 155,282 | 154,373                                                 | 99.4%      |

**Compare to the 2026-07-21 report's F1** ("30.8% canonical among captured single rows; 0% in 2020-2022; 27.3-34.3% in
2023-2026"). This run's numbers are dramatically higher for every year, especially 2023-2026 (~28-34% → ~99.4-99.6%).
**Caveat, stated plainly**: the two checks are NOT byte-identical methodology — this run's is a permissive shape regex
(`^[A-Z0-9\-]+:[A-Z_]+:\S+$`), not a byte-exact rebuild via `build_canonical_instrument_id`. However, this is
corroborated by two independent, stricter methods on the same run: the reconstructed-path oracle check (§3a, 99.95%
clean, uses the shipped write-time filename guard, not a regex) and direct content fetches. **Read together, this is
strong evidence that the operator-gated content-migration `migrate_tradfi_canonical_2026_07.py --apply` (flagged as a P1
todo in the 07-21 report) has executed in the intervening ~3 days** — not certified with a byte-exact re-run of the
exact 07-21 methodology. Recommend the tradfi consolidated closeout plan confirm/flip this todo rather than treating it
as still-open. 2020-2022 remain a real residual (28-46%, not the "0%" the 07-21 report measured — same
methodology-difference caveat applies there too).

### 3c. Distinct-value census (S3, 5,902,157 rows, unlocked/consolidated read)

| Axis              | Distinct values                                                                                                                                                                                                                                                                   | Verdict                                                                                                                                                                                                                                                                                                                                    |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `asset_group`     | `tradfi` (5,902,157)                                                                                                                                                                                                                                                              | ✅ sanity                                                                                                                                                                                                                                                                                                                                  |
| `pipeline_mode`   | `batch_databento` (majority) · `batch_yahoo` · `batch_barchart` (4,655) · `live_databento`                                                                                                                                                                                        | ✅ 0 blank/null anywhere in the index (5.9M/5.9M rows carry a non-empty value) — `batch_barchart` is legacy, all rows `empty_confirmed` (see BARCHART row below)                                                                                                                                                                           |
| `source`          | `databento`, `yahoo`, `barchart`                                                                                                                                                                                                                                                  | ✅ 0 blank/null. `batch_massive`/`source=massive`: **0 rows anywhere in the index** — purge holding                                                                                                                                                                                                                                        |
| `venue`           | CME 2,024,673 · NYSE 1,852,408 · NASDAQ 1,524,088 · ICE 407,482 · KRX 38,912 · CBOE 29,765 · FX 15,710 · **BARCHART 9,119**                                                                                                                                                       | `BARCHART` = **`non_canonical_axis_value` (S3)** — removed from `VENUES_BY_ASSET_GROUP["tradfi"]` 2026-06-24 (`market_data_categories.py:1777`); all 9,119 rows `empty_confirmed`; `attempted_at` as late as **2026-07-07** (13 days post-removal) — still being re-touched. Matches the 07-21 report's F5 EXACTLY (same count, unchanged) |
| `instrument_type` | `EQUITY`/`equity`, `COMBO`/`combo`, `FUTURE`/`future`, `ETF`/`etf`, `INDEX`/`index`, `SPOT_PAIR`/`spot_pair` (C2a casing pairs, suppressed) · `options_chain` (261,666) / `futures_chain` (236,657) — **carve-out, see below** · blank (85,096) · **`FUTURES` (16) · `spot` (2)** | 45,426 lowercase rows suppressed as `migration_pending` C2a casing (§ suppression table above); `FUTURES`/`spot` = genuine `non_canonical_axis_value`, 18 rows total, matches 07-21's F6 EXACTLY (unchanged)                                                                                                                               |
| `data_type`       | `ohlcv_1s/1m/15m/24h`, `mbp_10`, `trades`, `tbbo`, `corporate_action_confirmed`, `earnings_result`, `macro_result`, `options_chain`, `futures_chain`                                                                                                                              | all in the UAC `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` vocabulary                                                                                                                                                                                                                                                                            |
| `chain`           | blank/null only                                                                                                                                                                                                                                                                   | ✅ correct — defi-only axis                                                                                                                                                                                                                                                                                                                |
| `capture_status`  | `empty_confirmed` 3,772,418 · `captured` 1,421,963 · `expected_unattempted` 401,027 · `attempted_failed` 306,749                                                                                                                                                                  | 4-state honest, no fifth value                                                                                                                                                                                                                                                                                                             |

**`options_chain`/`futures_chain` as `instrument_type` — verified NOT a finding, a census-methodology carve-out.** UAC
`TRADFI_CHAIN_INSTRUMENT_TYPES = frozenset({"options_chain", "futures_chain"})` (`partition_paths.py:279`) is the
**PATH-segment** value the machine builder itself emits for bundle-per-underlying shards, and oracle clause 8 explicitly
validates this shape. The manifest column mirrors the same shard-atom value by design (pattern #2, §1 of
`cross-asset-canonical-target-ssot.md`). A naive `InstrumentType`-enum-only census check would false-flag ~498,323 rows
here; this run applied the carve-out and emits no finding. **The census SSOT table (§1.3 of
`reconciliation-census-and-compute-tiers.md`) should gain this carve-out explicitly** — it currently only names the bare
`InstrumentType` enum as canonical vocabulary for the `instrument_type` axis, with no bundle-grain exception stated.

**Captured-row-only blank `instrument_type`:** 1,910 rows (FX/ohlcv_24h 832, NASDAQ/ohlcv_1m 600 + tbbo 22, CME 310,
NYSE 168) — a minor completeness gap, distinct from the much larger FX-specific defect below.

### 3d. 🔴 NEW — S3-only defect: FX `SPOT_PAIR` manifest `instrument_id` never well-formed

| Metric                                                                        | Value                                                                  |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| Captured FX rows total                                                        | 4,310                                                                  |
| Well-formed `FX:SPOT_PAIR:XXX-USD` (or `FX:CURRENCY:...`) in the **manifest** | **0 (0.00%)**                                                          |
| Blank                                                                         | 2,812                                                                  |
| Literal `"ticks"` (bundle filename leaking into the id field)                 | 983                                                                    |
| Bare pair, no venue/type prefix (`EUR-USD`, `AUD-USD`, …)                     | 501 (all 2026)                                                         |
| `FX:SPOT_PAIR:...` / `YAHOO_FINANCE:SPOT_PAIR:...` (right-shaped but rare)    | 13 (2025 only)                                                         |
| Date range affected                                                           | 2020-01-02 → 2026-07-23 (every year, including the latest sampled day) |

**Content-verified the real object is fine.**
`raw_tick_data/by_date/day=2026-07-23/pipeline_mode=batch_databento/ asset_group=tradfi/venue=FX/instrument_type=spot_pair/data_type=ohlcv_24h/FX:SPOT_PAIR:AUD-USD.parquet`
exists, 0.69735/0.69735/0.696864/0.697156 (plausible AUD-USD OHLC), `instrument_id` column = `FX:SPOT_PAIR:AUD-USD` —
matches the filename exactly. The corresponding **manifest row for the same shard atom** (venue=FX, date=2026-07-23,
pipeline_mode=batch_databento, instrument_type=spot_pair, data_type=ohlcv_24h) carries `instrument_id="AUD-USD"` —
missing the `FX:SPOT_PAIR:` prefix, one of the 501 "bare pair" rows above.

**Compare to non-FX single-instrument venues on the same check**: NASDAQ EQUITY 0.81% blank, NYSE EQUITY 0.11% blank,
NASDAQ/NYSE ETF 0.0% blank. FX is a categorical outlier, not a tail of the same distribution.

**This is a taxonomy-gap finding** — none of the 20 named types cleanly cover "the S1/S2 pair (path+content) is correct,
but the S3 manifest's copy of the atom key is wrong or blank," for a **flat-per-contract** pattern where the manifest
key is supposed to be non-null by design (unlike pattern #2 bundles, where a null manifest id is expected). Closest
existing types (`non_canonical_id` — about the PARQUET row's own id, which here is fine; `shard_pillar_fail` — about
content/schema, not the manifest copy) do not fit. Reported under the taxonomy's own "a disagreement that fits no type
is itself a finding" rule (§2, `reconciliation-finding-taxonomy.md`).

**Operational impact**: any downstream consumer that resolves an individual FX pair via the manifest's `instrument_id`
column (a per-instrument data-status drilldown, a phantom-reconciler stem-vs-column check, an id-keyed join) sees
garbage or nothing for FX, for the entire 6-year history, right up to the most recent capture. The real market data is
not lost — it is correctly on disk — but it is not discoverable through this key.

### 3e. 🔴 NEW — live provenance-mislabeling on Yahoo-exclusive venues

| Venue                                  | Correct source per SSOT                                                                                                                                                                                                                                                                                  | Captured rows w/ `source=databento` (this run)                                                      | Date range                                     | First appearance                                                                                              |
| -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| ICE (`ICE:INDEX:DXY-USD`, ohlcv_24h)   | `yahoo` (Yahoo `DX-Y.NYB`) — `tradfi-databento-sourcing-ssot.md`: "ICE was REMOVED from `venue_to_databento`… querying raises `DatabentoDatasetNotAllowedError`"; UAC `get_dxy_daily_source()` (`data_source_continuity.py:218-225`) unconditionally returns `"YAHOO_FINANCE"` for any date ≥ 2019-01-02 | 4 (2026-07-20, 21, 22, 23 — 1/day)                                                                  | 2026-07-20 → 2026-07-23                        | first `batch_databento` attempt (empty) 2026-07-18; first REAL capture 2026-07-20                             |
| KRX (single-stock equities, ohlcv_24h) | `yahoo` (Yahoo `.KS` tickers) — `tradfi-databento-sourcing-ssot.md` + `venue_mapping.py:237` `"KRX": "yahoo_finance"`                                                                                                                                                                                    | 12 (2026-07-20…23 — 3/day: `000660`, `005380`, `005930`)                                            | 2026-07-20 → 2026-07-23                        | same pattern, same 4 days                                                                                     |
| FX (currency pairs, ohlcv_24h)         | `yahoo` — `ohlcv_24h`/`ohlcv_15m` are documented as **NOT Databento schemas at all** ("Databento doesn't even serve a 15m schema"; daily bars for FX are the Yahoo-only route)                                                                                                                           | **802** (752 `SPOT_PAIR` + 28 blank-type + 22 `spot_pair`) out of ~3,991 captured FX ohlcv_24h rows | 2020-01-02 → 2026-07-23 (11/day most-recently) | present since 2020, NOT a new pattern for FX specifically — a long-running companion of the same defect class |

**Confirmed by direct content fetch** (not just the manifest): the 2026-07-20 `ICE:INDEX:DXY-USD.parquet` object itself
carries `source`-adjacent fields consistent with the manifest row (real plausible DXY value, `~100.98`), and the
corresponding manifest row is `pipeline_mode=batch_databento, source=databento, capture_status=captured`. Same for KRX
`000660`/`005380`/`005930` on 2026-07-21/22/23 (real plausible KRW-scale close/volume values).

**Grep-then-READ against the SSOT + shipped code**, not inference:

- `tradfi-databento-sourcing-ssot.md` §"KRX + ICE are YAHOO FINANCE, not Databento" (2026-06-27 operator correction):
  _"neither KRX nor ICE is operator-blocked, Databento-sourced, needs an adapter, or off-allowlist… the data is freely
  available via Yahoo and the adapters exist."_
- `unified-api-contracts/unified_api_contracts/registry/data_source_continuity.py:218-225` — `get_dxy_daily_source()`
  has no branch that returns anything but `"YAHOO_FINANCE"` (or `"GAP_NO_SOURCE"` pre-2019).
- `unified-api-contracts/unified_api_contracts/registry/venue_mapping.py:237` — `"ICE": "yahoo_finance"` (the ONLY entry
  for ICE in `venue_to_data_provider`).
- `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:1774-1777` — BARCHART's capability
  block was removed 2026-07-15 explicitly BECAUSE "BARCHART was removed from `VENUES_BY_ASSET_GROUP["tradfi"]`
  2026-06-24 (VIX 15m now aggregates from VX futures via Databento XCBF.PITCH)" — the doc trail is explicit that
  Databento does NOT serve these venues' data by design.

**Not root-caused this run** (out of scope for a read-only reconciliation — belongs to MTDS's own plan/investigation,
per the "findings triage" rule: don't fix inline, don't collide). The pattern (correct VALUE, wrong PROVENANCE STAMP,
starting abruptly on a specific date, across MULTIPLE venues at once) closely resembles the ALREADY-FIXED 2026-06-19
CBOE bug described in `tradfi-databento-sourcing-ssot.md` ("the OHLCV write path used to stamp source from
`SOURCE_PRIORITY[0]`… every 1m row stamped `batch_massive`… including CBOE VX futures, which only Databento carries") —
i.e. this looks like a provenance-stamping regression, most likely reintroduced by the 2026-06-24 "TradFi
SOURCE_PRIORITY is DATABENTO-FIRST" change finding a code path that doesn't yet carry the per-venue
`_VENUE_SOURCE_EXCLUSIONS` guard for ICE/KRX/FX-daily the way it already does for `("CBOE","ohlcv_1m"): {massive}`. This
is a hypothesis stated for the investigating team, not a verified root cause.

**Classified**: `non_canonical_axis_value` (S3, `source`/`pipeline_mode` axes) at minimum; qualitatively this is a live,
cross-repo SSOT-vs-shipped-code contradiction and is escalated as a big finding (§7), not just a typed line item.

### 3f. Chain-tail cutover (2026-07-19) — spot-checked, not re-measured at scale

`raw_tick_data/by_date/day=2026-07-20/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/` shows
`instrument_type={combo,futures_chain,options_chain}/` children only (no bare `underlying=` shapes at the
`instrument_type=` level) — consistent with the v6 `underlying=/quote=/margin=/ticks.parquet` tail being the live shape
post-cutover. Not re-measured at full-corpus scale this run (07-21's F1/F2 already covers legacy chain debt in detail;
not re-derived to respect single-walk discipline).

### 3g. AE-2 adjacent defect — re-verified live in code this run

`market_tick_data_service/engine/orchestrator/symbol_rules.py:259`:
`_UNDERLYING_PARTITIONED_TYPES = frozenset({"options_chain", "futures_chain", "combo"})` (writer treats `combo` as
underlying-partitioned) vs `market_tick_data_service/reader.py:62`:
`_UNDERLYING_PARTITIONED_TYPES: frozenset[str] = frozenset({"options_chain", "futures_chain"})` (reader does NOT include
`combo`). **Still present, unresolved, confirmed via direct grep+read this run** (not just cited from the codex). Per
taxonomy AE-2's own text this is explicitly NOT suppressed — "a live cross-repo finding … reported at severity HIGH, not
absorbed into AE-2."

### Coverage formula (Step 8 — name it, mark it a lower bound)

`reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`, `empty_confirmed` EXCLUDED
(`honest-coverage-model.md`, CK3-certified):

```
1,421,963 / (1,421,963 + 306,749 + 401,027) = 1,421,963 / 2,129,739 = 66.77%  — LOWER BOUND
```

(`instrument_gates_download=true` for tradfi, so this is a lower bound per the standing rule; `all_shards` including
`empty_confirmed` = 5,902,157.) The 07-21 report measured 70.5% off a locked/lower-bound index; this run's index was
unlocked/consolidated, so the two numbers are not a clean apples-to-apples trend without checking whether
`expected_unattempted`/`attempted_failed` denominators shifted for other reasons — reported with formula, not asserted
as a regression.

---

## Phase 2 — Non-canonical sweep + register reconciliation

Register→reality re-verification of `non-canonical-path-inventory.md` rows scoped to tradfi. **Did not edit the shared
register inline** (concurrency — other sessions hold live WIP in this same checkout this run, confirmed via mtime before
touching anything); register-patch stanza below for the maintainer to apply serially.

| Register row | Claim (as currently written)                                                                     | Reality (measured this run, 2026-07-24/25)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | Disposition change                                                                                            |
| ------------ | ------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| 10           | Retired 2026-07-21, purge executed                                                               | **CONFIRMED HOLDING** — 0 `batch_massive` objects/rows this run too (3rd consecutive confirmation)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | none — still retired                                                                                          |
| 11           | Retired 2026-07-21, migration executed 848,886 objects, 99.65% post-migration                    | Consistent with this run's S1 structural samples (0 violations) and the dramatic S3 id-form improvement (§3b) — **not independently re-measured at full scale**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | none — plausibly still holding, worth a fresh full measurement given §3b's finding                            |
| 19           | `databento-batch-registry/{sha}.json`, sanctioned operational, 7,146 objects (07-21 measurement) | **7,146 objects, unchanged** — exact match                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | none                                                                                                          |
| 22           | "RETIRED — DELETED 2026-07-21" (against a 15,813-object baseline)                                | **STALE.** `_quarantine/` = **≥400,000 objects / ≥8.71GB** (enumeration capped at 400,000 for time; true count is higher). The SAME-DAY 07-21 report already measured 146,288/7.18GB — i.e. the "DELETED" disposition was already out of date the day it was written, and the population has since nearly TRIPLED again. Spot-checked one object (`_quarantine/raw_tick_data/day=2026-01-01/…/underlying=CME:OPTION:EW1-USD-260102-100-CALL@LIN/…`, `time_created=2026-07-22`): the oracle independently confirms this underlying genuinely IS quarantine-worthy ("not a real product root… quarantine, never fake-canonicalize") when tested outside the `_quarantine/` wrapper — the detection machinery looks correct; the volume and growth rate are the open question. | **RE-OPEN — update disposition, do not describe as deleted/resolved; flag the growth rate for investigation** |

**Reality → register (locations found this run, not previously registered for tradfi specifically):**

| Location                                                             | Size                                    | Notes                                                                                                                                                                                                                                                                         |
| -------------------------------------------------------------------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `_migration_backup/manifest_dedup_2026_07_10/`                       | 1 object / 118.0 MB                     | The 07-21 report already proposed this exact register-patch line ("1 obj / 0.12 GB") — **the patch was never applied to the shared register**. Re-flagging.                                                                                                                   |
| `_vm_staging/migrate_tradfi_to_hive.py` + `logs/` + `mtds_backfill/` | 13 objects / 38.0 MB total              | Executable Python + operational staging content at the top level of a PROD DATA bucket — same class of issue as the sports `scripts/` register row (row 4). Not previously broken out as its own tradfi register row (only listed as an unexplored top-level child in 07-21). |
| `configs/patches/`                                                   | (rolled into `configs/` total, 0.19 MB) | Resolves register row 28's "patches/ child not probed" for tradfi — **confirmed present**. Disposition question (config-in-data-bucket) remains open per the row.                                                                                                             |

Orphans: **NOT ASSESSED** (no whole-corpus walk this run — per `orphan-object-detection.md` §3, a manifest-driven pass
must not claim "0 orphans").

### Register-patch stanza (apply serially — do NOT hand-edit inline during concurrent AG runs)

```
# non-canonical-path-inventory.md
- Row 22 (_quarantine/): The "RETIRED — DELETED 2026-07-21" disposition is STALE as of 2026-07-24/25.
  Re-measured: >=400,000 objects / >=8.71 GB (capped enumeration; true count higher — repeat with an
  uncapped, time-boxed listing). Population has grown from a 07-21-measured 146,288 obj/7.18GB to this in
  ~3-4 days. Spot-checked content is genuinely quarantine-worthy (oracle-confirmed bad `underlying=`
  values from the in-flight chain-tail migration) — looks like healthy detection, not corruption, but the
  growth rate is unexplained and unmonitored. Recommend: (a) re-measure with an uncapped walk, (b) find
  what process is feeding it and whether it should be draining faster than it fills, (c) keep disposition
  `no-still-authoritative` (it's live detection output) rather than any delete disposition until (b) is
  answered.
- NEW row: `_migration_backup/manifest_dedup_2026_07_10/` (tradfi bucket) — 1 obj / 118.0 MB, manifest
  dedup snapshot. Disposition `unknown` (five-part proof not run). NOTE: this exact line was already
  proposed in the 2026-07-21 report's register-patch stanza and was never applied — this is a re-flag,
  not a new discovery.
- NEW row: `_vm_staging/` (tradfi bucket) — 13 obj / 38.0 MB, includes `migrate_tradfi_to_hive.py` (executable
  script at the top level of a prod DATA bucket) + `logs/` + `mtds_backfill/`. Disposition `unknown` (five-part
  proof not run). Mirrors the already-registered sports `scripts/` pattern (row 4) — consider consolidating under
  one general "executable scripts in prod data buckets" finding class.
- Row 28 (configs/patches/): tradfi's `patches/` child CONFIRMED PRESENT (was "not probed"). Disposition question
  (config-in-data-bucket vs config-store) still open — no change to disposition, just resolves the open probe.
```

**No delete suggestions rise above `unknown` this run.** Nothing here completed the five-part proof
(`gcs-and-manifest-delete-safety-protocol.md`); every newly-observed or re-flagged location above is `unknown`, per the
doc's own default.

---

## Typed findings summary (taxonomy names; suppressed exceptions counted separately)

| #        | Type                                              | Severity                      | Surfaces                              | Scope                                                | Detail                                                                                              | Delete-eligible      | New / re-confirmed                        |
| -------- | ------------------------------------------------- | ----------------------------- | ------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------- | -------------------- | ----------------------------------------- |
| G1       | **taxonomy-gap** (S3-only manifest-id defect)     | **HIGH** (proposed)           | S3                                    | FX SPOT_PAIR, all captured rows                      | 0/4,310 well-formed manifest `instrument_id`, 2020-2026, ongoing; real GCS object is fine (§3d)     | NO                   | **NEW**                                   |
| G2       | `non_canonical_axis_value` (source/pipeline_mode) | **HIGH** (escalated — see §7) | S3 (+ plausible S1/S2 upstream cause) | ICE/KRX (live, 4 days) + FX (longstanding, 802 rows) | Yahoo-exclusive venues captured under `source=databento`; contradicts SSOT + UAC routing code (§3e) | NO                   | **NEW**                                   |
| F5       | `non_canonical_axis_value` (venue)                | LOW                           | S3                                    | `venue=BARCHART`, 9,119 rows, all `empty_confirmed`  | removed from vocabulary 2026-06-24, still re-touched as late as 2026-07-07                          | NO                   | re-confirmed, unchanged                   |
| F6       | `non_canonical_axis_value` (instrument_type)      | LOW                           | S3                                    | `FUTURES`(16) / `spot`(2)                            | content-repair targets                                                                              | NO                   | re-confirmed, unchanged                   |
| AE-2-adj | writer/reader path shape disagreement             | HIGH                          | code                                  | `combo` shard read path                              | `symbol_rules.py:259` vs `reader.py:62` — MTDS writes a shape the reader never probes               | n/a (code, not data) | re-confirmed live via grep+read           |
| —        | register staleness (`_quarantine/`)               | MEDIUM                        | register                              | row 22                                               | "DELETED" claim stale; population ≥400K and growing                                                 | n/a                  | **NEW** (growth), re-opens a "closed" row |
| —        | phantom (published, not re-run)                   | context-only                  | S3↔S1                                 | tradfi                                               | `phantom_count=1635` @2026-07-14, 10-11 days stale                                                  | NO                   | unchanged from both prior runs            |
| —        | id-form improvement (positive)                    | INFO                          | S3                                    | captured singles, corpus-wide                        | ~99.3% id-shape-canonical vs 07-21's 30.8% — see §3b caveats                                        | n/a                  | **NEW observation**                       |

**Suppressed accepted-exception counts (proving suppression happened, not re-listing them):**

- C2a instrument_type casing (`reconciliation-finding-taxonomy.md` §5.1) — **45,426 lowercase rows** compared
  case-insensitively, **0 casing findings emitted**.
- AE-2 combo bare-underlying (taxonomy §4) — 1,307,758 `COMBO`/`combo` rows NOT flagged as `non_canonical_path` for
  their bare `underlying=/ticks.parquet` tail.
- AE-4 `batch_massive` (CLOSED) — 0 rows to suppress; purge holding, confirmed a third time.
- Bundle-grain `instrument_type={options_chain,futures_chain}` carve-out (§3c, this run's own methodology note, not yet
  a named codex AE) — 498,323 rows NOT flagged as `non_canonical_axis_value`.

---

## §6 — Coverage gaps (what this run did NOT assess)

1. **Orphans: NOT ASSESSED** — no whole-corpus walk (single-walk discipline). Not claiming "0".
2. **S4 catalogue (instruments-store bucket): NOT ASSESSED this run** — the dispatch scope named only the `market-data`
   bucket for tradfi. Unlike the 07-21 report (which checked `instruments-store-tradfi-prd` and found it clean), this
   run has **no S4 read at all** — a full coverage gap for the catalogue surface, not a per-shard verdict. A prior run's
   clean S4 read should NOT be assumed still true without re-checking.
3. **AWS: NOT ASSESSED this run** — the 07-21 report found both AWS tradfi buckets reachable and empty; not re-verified
   here.
4. **id-form / schema at 100%: NOT ASSESSED** — every id-form number in §3 is a sample (largest: 3,000 rows out of
   1,421,963 captured rows, i.e. ~0.2%), not a full-corpus certification. A Tier-2 read-only per-datapoint VM would be
   required for a 100% claim; not dispatched this run.
5. **`_quarantine/` true size: NOT FULLY ENUMERATED** — capped at 400,000 objects for time; the true count is higher.
6. **`processed_candles/`** — explicitly out of scope for this dispatch (raw-tick layer only, per instruction).
7. **Register rows re-verified for tradfi only** — other-AG rows in `non-canonical-path-inventory.md` untouched.
8. **2020-2022 id-form residual not root-caused** — still 28-46% canonical by this run's shape check (§3b); not
   determined whether this is a genuine, permanently-orphaned historical gap or a slower-moving edge of the same
   migration that fixed 2023+.

---

## §7 — Big findings escalated to the operator (issue doc filed)

Per the workspace's findings-triage rule (data-correctness / cross-repo / SSOT contradiction → notify + issue doc), two
findings from this run are escalated:

1. **Yahoo-exclusive tradfi venues (ICE, KRX; longstanding FX companion) captured under `source=databento` /
   `pipeline_mode=batch_databento`, live and ongoing since ~2026-07-18** (§3e). Contradicts
   `tradfi-databento-sourcing-ssot.md` and UAC's own `get_dxy_daily_source()`/`venue_mapping.py` routing code.
2. **tradfi FX `SPOT_PAIR` manifest `instrument_id` is 0% canonically-formed across its entire 2020-2026 captured
   history** (§3d) — a taxonomy-gap-class S3-only defect, real data is fine on disk, the manifest's own copy of the key
   is not.

Filed: `plans/active/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`.

---

## Todos / issue-doc candidates (not fixed inline — belongs to the relevant service plan)

- [ ] **P0 [DATA]** Root-cause + fix the ICE/KRX/FX `source=databento` mis-stamping (§3e, §7). Likely candidate: the
      2026-06-24 "TradFi SOURCE_PRIORITY is DATABENTO-FIRST" change reaching a code path that lacks the per-venue
      `_VENUE_SOURCE_EXCLUSIONS` guard the way `("CBOE","ohlcv_1m"): {massive}` already has it. Re-stamp the affected
      historical rows once fixed (do not silently leave mislabeled provenance in place).
- [ ] **P0 [DATA]** Root-cause the FX manifest `instrument_id` defect (§3d) — likely the FX write path never passes a
      populated id through to the manifest-writer call, unlike every other single-instrument tradfi venue. Backfill the
      manifest `instrument_id` column for the 4,310 affected rows once fixed (the GCS content does not need to change).
- [ ] **P1 [DATA]** Confirm whether `migrate_tradfi_canonical_2026_07.py --apply` (the 07-21 report's P1 todo) has in
      fact run; if so, flip that todo and re-baseline the tradfi consolidated closeout's "~99.65%" claim against real
      current numbers instead of re-deriving it informally the way this run and the 07-21 run each did independently.
- [ ] **P1 [DATA]** Re-measure `_quarantine/` with an uncapped, time-boxed walk and identify what is feeding its rapid
      growth (146,288 → ≥400,000 in ~3-4 days) — either drain it faster or confirm the growth is a bounded, expected
      side-effect of the in-flight migration and will stop.
- [ ] **P2 [DOCS]** Apply the register-patch stanza above to `non-canonical-path-inventory.md` (including the
      `_migration_backup/manifest_dedup_2026_07_10/` line the 07-21 report already proposed and that was never applied).
- [ ] **P2 [DOCS]** Add the `TRADFI_CHAIN_INSTRUMENT_TYPES` bundle-grain carve-out (§3c) to
      `reconciliation-census-and-compute-tiers.md` §1.3's canonical-vocabulary table for `instrument_type`, so a future
      run doesn't have to re-derive it from source.
- [ ] **P3 [DATA]** Re-run the phantom auditor (published count 1,635 is now ~11 days stale).
- [ ] **P3 [CODE]** Fix the AE-2-adjacent `combo` writer/reader path-shape disagreement (`symbol_rules.py:259` vs
      `reader.py:62`) — still live, unresolved since first flagged.
