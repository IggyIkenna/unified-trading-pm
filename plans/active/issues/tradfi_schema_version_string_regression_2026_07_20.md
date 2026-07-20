---
doc_type: issue
title: tradfi manifest schema_version stamped as STRING "9" — un-forced T+1 collection crash-loops nightly
summary: >-
  All ~5.2M rows of the tradfi availability index (_index/availability_index.parquet) carried schema_version as the
  STRING "9" (arrow type `string`, pandas dtype object) instead of int64. UTL check_shard_freshness
  (manifest_writer/_queries.py:130 `date_df["schema_version"] >= MANIFEST_SCHEMA_VERSION` and :165 `row.get(...) <
  MANIFEST_SCHEMA_VERSION`) then does `"9" < 9` / `Series[str] >= 9` → TypeError, killing every UN-FORCED tradfi T+1
  collection run (a `--force` run bypasses the freshness skip and never exercises the crash). ROOT WRITER:
  scripts/restamp_tradfi_schema_v9_tail_2026_07_16.py:427 `shard_df["schema_version"] = "9"` (Python str). AMPLIFIER:
  the manifest consolidator's DuckDB `read_parquet(..., union_by_name=true)` merge — unioning an int64 canonical column
  with a VARCHAR shard column promotes the WHOLE merged column to VARCHAR, so every row's 9 becomes "9". Same bug CLASS
  as tradfi_manifest_consolidator_row_count_varchar_crash_2026_07_12 (row_count VARCHAR broke the same merge).
status: resolved
resolved_by:
  "slot-1·laptop (2026-07-20) — (1) DATA REPAIR: CAS re-stamp of the live tradfi _index to int64 (5,209,585 rows, gen
  1784572840535586 -> 1784572895173237; pre-snapshot
  _index/snapshots/pre_schema_version_int64_restamp_20260720T184042Z.parquet), confirmed HELD across consolidator cycles
  (post-merge gen 1784574598529744 still arrow int64, all rows int 9). (2) WRITER FIX: market-tick-data-service@ac051bfe
  — restamp:427 now stamps int MANIFEST_SCHEMA_VERSION via new testable helper `stamp_v9_shard`, + regression test
  tests/unit/scripts/test_restamp_tradfi_schema_v9_tail.py (asserts int dtype + non-string arrow roundtrip). (3)
  VERIFIED: check_shard_freshness runs without TypeError on the int64 index; the UN-FORCED
  TickDataHandler._apply_freshness_skip nightly path completes with real verdicts (PARTIAL date=2026-07-19: 6/7 venues
  need processing) instead of crashing."
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [manifest, consolidator, data-correctness, regression, production-outage, big-finding, schema_version]
related:
  [
    tradfi_manifest_consolidator_row_count_varchar_crash_2026_07_12.md,
    tradfi_manifest_row_loss_regression_2026_07_12.md,
    tradfi_consolidated_closeout_2026_07_18.md,
  ]
parent_epic: tradfi_master
locked_by:
created: 2026-07-20
source:
  - tradfi_consolidated_closeout_2026_07_18.md (P0 dispatch — nightly T+1 collection down)
assigned_vm: NA
assigned_role: data_engineering
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **🟢 RESOLVED 2026-07-20 — nightly tradfi T+1 collection restored.** Live `_index` re-stamped to int64 (holds across
> consolidator cycles); root writer fixed + regression-tested (`market-tick-data-service@ac051bfe`).

# schema_version string regression — root cause, fix, repair, verification

## Symptom

Un-forced nightly tradfi T+1 collection dies with `TypeError` inside `check_shard_freshness`. A `--force` run "works"
(it skips the freshness check), which masked the failing path. The break started mid-day 2026-07-20 (a T+1 run succeeded
~12:44 UTC, crashed ~14:49 UTC).

## Root cause (proven, file:line)

- **Writer:** `market-tick-data-service/scripts/restamp_tradfi_schema_v9_tail_2026_07_16.py:427` —
  `shard_df["schema_version"] = "9"` assigns a Python **str**, so the per-VM shard's `schema_version` column is
  object/VARCHAR on disk. (This is the only writer in MTDS/UTL/IS that stamps a string `schema_version`; every other
  path writes the int `MANIFEST_SCHEMA_VERSION`.)
- **Amplifier (shared path):** `unified_trading_library/manifest_consolidator.py` merges the canonical index + per-VM
  shards with `read_parquet(..., union_by_name=true)` + `SELECT *` CTEs. DuckDB promotes a column that is BIGINT in one
  input and VARCHAR in another to VARCHAR, converting **every** `9` → `"9"` for the whole corpus. This is the identical
  mechanism as `tradfi_manifest_consolidator_row_count_varchar_crash_2026_07_12` (that one was `row_count` VARCHAR;
  fixed with a `TRY_CAST` in the merge).
- **Consumer that crashes:** `unified_trading_library/manifest_writer/_queries.py:130` (`>= MANIFEST_SCHEMA_VERSION`)
  and `:165` (`< MANIFEST_SCHEMA_VERSION`) — `"9" < 9` raises `TypeError: '<' not supported between 'str' and 'int'`.

**Proof (not timing):** the pre-restamp snapshot taken by an _earlier same-day_ restamp run on 2026-07-16
(`_index/snapshots/pre_tradfi_schema_v9_tail_restamp_20260716T070255Z.parquet`) ALREADY shows `schema_version` as arrow
`string`, dtype object, `{'9': 5539227, '4': 13971}` — a direct causal artifact of the string-stamping writer, not an
inference from run timing. Both 2026-07-18 migrate backups (`_index/backups/availability_index.pre_usd_lin_*`) are also
string. The current string content was (re)materialised by the consolidator (custom metadata
`consolidator_content_write_at=2026-07-20T15:09:39`); a live re-stamp to int64 held across the next merge, confirming no
string-schema_version shard remains to re-flip it (`_index/per_vm/` holds only the int64 `_legacy_seed.parquet`).

Candidates ruled OUT as the string source: `migrate_tradfi_manifest_usd_lin_2026_07_18.py` (never touches
`schema_version` — copies the frame and rewrites, preserving dtype); the `tradfi-catalogue-canon` VM (runs
instruments-service code against the instruments-store bucket, never the tick `_index`); `_rebuild_tradfi_cf11.py`
(writes via `record_empty`/`record_failed`, which stamp int).

## Fix

- **Writer root fix** — `market-tick-data-service@ac051bfe`: extracted `stamp_v9_shard(...)` which writes
  `schema_version = MANIFEST_SCHEMA_VERSION` (int64). Regression test
  `tests/unit/scripts/test_restamp_tradfi_schema_v9_tail.py` asserts (a) integer pandas dtype, (b) the exact
  `schema_version < MANIFEST_SCHEMA_VERSION` comparison does not `TypeError`, (c) the on-disk parquet arrow type is
  integer (the precise anti-regression that starves the `union_by_name` VARCHAR coercion).
- **NOT** changed: UTL's `_queries.py` comparison was intentionally left strict (int-only) — making it type-tolerant
  would paper over a data-correctness regression.

## Data repair (route taken)

Targeted **in-place CAS re-stamp** of the live `_index` (NOT waiting for the peer's force-rebuild, which was blocked
behind the Massive-purge execution-path repair). Read `download_bytes_with_generation` → `pd.to_numeric(schema_version)`
→ `.astype("int64")` → `conditional_upload_bytes(if_generation_match=gen)` (raced the consolidator once, won on retry
2). Pre-state: 5,209,585 rows, arrow `string`, all `"9"`. Post-state: arrow `int64`, all `9`; **held** across the next
consolidator merge. Announced to the rebuild peer: the `_index` is the shared object both target — the re-stamp is a
dtype-only change (no rows added/dropped), so a subsequent object-scan force-rebuild (which writes int `schema_version`
via the manifest writer) is compatible and idempotent.

## Verification (un-forced)

- `check_shard_freshness(bucket, date, service_name, ...)` returns clean tuples on the int64 index — both the venue
  branch (`(False, ['CME'], [])`) and the no-venue `schema_version >= 9 .all()` branch (`(True, [], [])`).
- The exact nightly caller `TickDataHandler._apply_freshness_skip(date, ["tradfi"], None)` with `_force=False` completes
  with real verdicts
  (`PARTIAL date=2026-07-19: 6/7 venues need processing (stale=0 missing=6): [CBOE, NASDAQ, NYSE, ICE, FX, KRX]`) —
  previously a `TypeError` at line 407.

## Follow-up recommendation (P2, defense-in-depth — NOT required for the P0 hold)

Harden the shared consolidator path so a future string-stamping shard can never corrupt the whole corpus again (the
`row_count` VARCHAR crash 2026-07-12 already proved this class recurs). Recommended: coerce `schema_version` (and any
other int-typed manifest column) to BIGINT at the `read_parquet` boundary via a `TRY_CAST(schema_version AS BIGINT)` in
`manifest_consolidator._duckdb_merge_payload`'s `shard_proj`/`canon_proj` column projections — mirroring the existing
`TRY_CAST(row_count AS BIGINT)` guard. This also auto-repairs a poisoned column on the next cycle. Deferred from this P0
because the merge SQL is incident-scarred and high-risk to edit under time pressure; the writer fix + live re-stamp
already restore and hold nightly collection.

## Todos

- [x] [DATA] P0. Re-stamp live tradfi `_index` schema_version → int64 (CAS) — held across consolidator cycles.
- [x] [SCRIPT] P0. Fix root writer restamp:427 → int + regression test — `market-tick-data-service@ac051bfe`.
- [x] [VERIFY] P0. check_shard_freshness + un-forced `_apply_freshness_skip` complete without TypeError.
- [ ] [SCRIPT] P2. Consolidator `TRY_CAST(schema_version AS BIGINT)` hardening (defense-in-depth; see recommendation).
