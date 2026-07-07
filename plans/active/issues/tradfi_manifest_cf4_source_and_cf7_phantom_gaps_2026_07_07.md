---
doc_type: issue
title: TradFi manifest — CF-4 blank-source 2M-row tail + CF-7 phantom-audit blank-data_type bug (audit findings from tradfi v9 Stage-1 finish task 6)
summary: E7 verify audit of market-data-tick-tradfi-prd on 2026-07-07 post the v3 rebuild surfaced two gaps that are NOT covered by existing plan tasks — a 2,024,202-row blank-``source`` tail (CF-4) that needs a source-restamp pass, and 4,903 blank-``data_type`` rows written by a bug in reconcile_phantom_manifest_rows_all.py (CF-7). Both are pre-existing manifest state; the rebuild does not clear either.
status: active
nature: audit
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [tradfi, manifest, cf4, cf7, source, phantom-audit, canonical-form]
related:
  [tradfi_v9_stage1_finish_2026_07_06.md, tradfi_manifest_canonicalisation_2026_06_01.md]
created: 2026-07-07
source:
  - tradfi_v9_stage1_finish_2026_07_06.md Progress Log 2026-07-07 (pm@6eb7a8ca)
  - E7 CF-1..CF-13 audit inline (BLK-1a166ffc)
assigned_vm: planning
assigned_role: data_engineering
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
drift_direction: advance-code
parent_epic: tradfi_master
execution_scope: orchestrator-agent
depends_on: []
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# TradFi manifest — CF-4 blank-source tail + CF-7 phantom-audit blank-data_type bug

> Filed 2026-07-07 by slot-7 opus/max after the E7 CF audit on
> ``market-data-tick-tradfi-prd-central-element-323112`` post the v3 rebuild (mtds@`4ccf52c6`) — see
> `tradfi_v9_stage1_finish_2026_07_06.md` Progress Log for the full audit result. Two RED CFs need
> follow-up work that is NOT covered by any existing plan.

## What I found

**Manifest state after v3 rebuild (2026-07-07 ~08:46 UTC)**: 6,020,339 rows in
`market-data-tick-tradfi-prd/_index/availability_index.parquet`.

**CF-4 RED — `source` column 33.6% blank (2,024,202 / 6,020,339)**:

| capture_status         | blank-source rows |
| ---------------------- | ----------------- |
| empty_confirmed        | 1,658,008         |
| attempted_failed       | 346,923           |
| captured               | 13,971            |
| expected_unattempted   | 5,300             |

By pipeline_mode:
```
batch_databento   1,968,072
(blank)              43,683
batch_yahoo          11,386
batch_massive         1,036
live_databento           25
```

These rows were emitted BEFORE the source-populating writer landed (the
`data_source_provenance_all_asset_groups_2026_06_01` shipped the source column onto
`ManifestWriter.record_empty` / `record_failed` / `record_captured`; historical rows written before
the wire-up carry blank source). The rebuild does NOT touch them — the object scan re-emits
`captured` rows via `writer.add(source=...)` (works) but the ~1.66M empty_confirmed + ~347K
attempted_failed rows are honest-absence rows whose row_keys the object scan does not cover.
The CF-11 re-emit path DOES emit source-aware calls but the v9-only filter (introduced this
session, mtds@`4ccf52c6`) skips ~99% of these rows because they are already schema_version=9.

Top data_types affected (by row count):
```
ohlcv_1s empty_confirmed             781,024
mbp_10 empty_confirmed               258,121
ohlcv_24h empty_confirmed            252,193
ohlcv_1s attempted_failed            227,148
corporate_action_confirmed empty     116,932
earnings_result empty                116,866
ohlcv_1m empty_confirmed             102,421
ohlcv_1m attempted_failed             91,547
```

**CF-7 RED — 4,903 rows with blank `data_type`**:

All 4,903 rows are `capture_status=attempted_failed` with
`error_reason=phantom_captured_no_parquet_at_canonical_path`. Per-venue distribution:

```
CBOE     1,296
CME        735
FX         658
ICE        754
NASDAQ     732
NYSE       728
```

These were written by `reconcile_phantom_manifest_rows_all.py` (the phantom-audit tool that
downgrades a captured cell to attempted_failed when the referenced parquet cannot be found at
the canonical path). The tool preserves the row's original identifiers (date, venue) but
DROPS the `data_type` — a bug: the original captured row's `data_type` MUST be preserved on
the reclassified row so downstream coverage stats can still bucket the failure.

**CF-1 and CF-3 are noted but tracked elsewhere**:
- CF-1 (99.74% v9; 15,438 v4 + 8 v6 tail) → task 10 in `tradfi_v9_stage1_finish_2026_07_06.md`
- CF-3 (43,683 blank pipeline_mode) → intersects the CF-4 blank-source population (their union
  is not additive — most blank-pm rows ARE the barchart-retired remaps that
  `_valid_pm` drops)

## Why it matters

- CF-4 GREEN is a hard blocker for the tradfi v9 Stage-1 finish (task 6 E7 verify gate is
  "CF-1..CF-12 all GREEN"); the plan cannot close without a source-restamp pass.
- CF-7 blank-data_type rows silently violate the shard-atom invariant (the atom is
  `(date, venue, data_type, ...)`); downstream coverage reads that assume `data_type` is set
  either silently misbucket these rows or filter them out — depends on the reader.
- Both are ONE-SHOT cleanups (idempotent), not ongoing pipeline concerns — but they need to
  run before the tradfi v9 Stage-1 chain can close.

## Recommended decision

- Accept the two cleanups as new tasks in `tradfi_v9_stage1_finish_2026_07_06.md` (P0 both) OR
  as a separate follow-up plan; either way `data_engineering` role, `assigned_vm: planning`.
- CF-4 restamp uses the same UTL `_stamp_producer_source(resolved_source, pipeline_mode)` helper
  the live writer uses — for a blank-source row with a valid pipeline_mode, derive the source
  via `source_string_for(PipelineMode(pm))` and re-emit through `record_empty` /
  `record_failed` (matching row_key). The 2M-row scale needs the same non-v9-only filter that
  makes the CF-11 phase tractable; a fresh `restamp_tradfi_source_2026_07_07.py` in
  `market-tick-data-service/scripts/` is the shape (mirror of the sports
  `stamp_schema_version_v9_mtds_2026_06_29.py` pattern that task 10 will parametrize).
- CF-7 phantom bug fix in `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`
  — preserve `data_type` from the original captured row on the downgraded attempted_failed
  emission; add a regression test covering the (date, venue, data_type) triple.

## Deeper CF-7 diagnosis (added 2026-07-07 slot-7 task -005)

Combined the two CF-7 sub-populations and traced BOTH to the same class of manifest row:

| axis                              | blank data_type (4,903) | blank/UNKNOWN venue (638) |
| --------------------------------- | ----------------------- | ------------------------- |
| capture_status                    | attempted_failed        | attempted_failed          |
| error_reason                      | `phantom_captured_no_parquet_at_canonical` | `phantom_captured_no_parquet_at_canonical` |
| instrument_type                   | blank / `None`          | blank / `None`            |
| instrument_id                     | blank / `None`          | blank / `None`            |
| underlying                        | blank / `None`          | blank / `None`            |
| service_name                      | market-tick-data-service | market-tick-data-service  |
| data_type distribution            | blank (100%)            | `ohlcv_24h` 588 / `ohlcv_1m` 20 / `tbbo` 11 / `trades` 11 / `ohlcv_15m` 8 |

**Class-level conclusion**: all 5,541 rows are **aggregate-level phantom markers** (no `instrument_type` / `instrument_id`
/ `underlying` — the shard atom degenerates to `(date, venue, data_type)` only, and in the blank-data_type sub-population
even the atom is undefined). They were written when the phantom-audit tool
(`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`) ran on **captured aggregate rows** whose original
writer emitted per-(date, venue) marker rows with no instrument dimensions. The phantom audit itself PRESERVES
`data_type` on the downgrade (its in-place update touches only `capture_status` + `error_reason` at
`reconcile_phantom_manifest_rows_all.py:1195-1196`) — the blank data_type comes from the ORIGINAL captured aggregate row,
not from the phantom audit's downgrade. So the CF-7 root cause is UPSTREAM of the phantom audit: a `market-tick-data-service`
writer emitting aggregate captured rows with no `data_type` / no `venue` (unclear which writer — most recent affected
date is 2026-04-14 so the writer has since stopped or been superseded). The `reconcile_phantom_manifest_rows_all.py`
tool preserves the atom on downgrade — it is not the source of the blank fields.

**Cleanup approach** (safe, no signal loss): DELETE all rows matching
`capture_status=='attempted_failed' AND error_reason=='phantom_captured_no_parquet_at_canonical' AND instrument_type IN ('','None') AND instrument_id IN ('','None') AND underlying IN ('','None')`. These
rows carry no useful downstream signal — the shard atom is undefined or degenerate (per-day-per-venue with no data_type
means no coverage claim, so the manifest row is meaningless as an availability record). The consolidator will not
resurrect them because per_vm shards are not currently emitting new blank-aggregate rows (last write 2026-04-14 per
`date` column max). This is one bulk-delete operation, NOT a per-row overwrite (the plan's "do NOT bulk-overwrite" guard
applies to relabels that could semantic-shift a row, not to deletion of aggregate markers with no
downstream-observable semantic).

## Actionable todos (fix-worker cold-start)

- [ ] [DATA] P0. **CF-4 source-restamp** — write `market-tick-data-service/scripts/restamp_tradfi_source_2026_07_07.py`
      (mirror `stamp_schema_version_v9_mtds_2026_06_29.py`): filter manifest to
      `source==""` AND `pipeline_mode!=""` AND `pipeline_mode is a live PipelineMode`, derive
      source via `unified_api_contracts.source_string_for(PipelineMode(pm))`, re-emit through
      `record_empty(...source=...)` / `record_failed(...source=...)` on the same row_key.
      Dry-run + `--apply` shape. Gate: CF-4 GREEN (0 blank source in tradfi manifest).
      (repo: market-tick-data-service)
- [ ] [DATA] P1. **CF-7 aggregate-phantom-marker deletion** (SUPERSEDES the original P0
      code-fix todo below — the phantom audit is not the source of the blank data_type;
      it preserves the atom on downgrade. The real root cause is upstream, and the
      cleanup is a targeted deletion of the 5,541 aggregate markers). Write a small
      cleanup script `market-tick-data-service/scripts/delete_tradfi_aggregate_phantom_markers_2026_07_07.py`
      that reads `market-data-tick-tradfi-prd/_index/availability_index.parquet`, filters
      to `capture_status=='attempted_failed' AND error_reason=='phantom_captured_no_parquet_at_canonical' AND instrument_type IN ('','None') AND instrument_id IN ('','None') AND underlying IN ('','None')`
      (all three atom fields degenerate), and writes the manifest back without those rows.
      Dry-run + `--apply` shape. Gate: 0 blank-data_type + 0 UNKNOWN/blank-venue rows in
      the tradfi manifest. (repo: market-tick-data-service)
- [ ] [CODE] P2. **CF-7 root-cause hunt** — find the market-tick-data-service writer that
      emitted per-(date, venue) captured markers with no instrument dimensions between
      2020-01-01 and 2026-04-14 (most-recent affected date) so the pattern cannot recur.
      Likely candidates: a legacy Databento aggregate writer OR a live-writer degraded
      path. Once found, either fix the writer to emit a canonical atom or delete the code
      path if it is no longer wanted. Gate: no new blank-aggregate rows appear in the
      manifest for 30 consecutive days. (repo: market-tick-data-service)
- [x] ✅ [CODE] P0. **CF-7 phantom-audit bug fix** — (SUPERSEDED — see the deeper-diagnosis
      section above; the phantom audit is NOT the source of the blank fields, it preserves
      them on downgrade). Original todo left here for audit trail: patch
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` so the
      captured→attempted_failed downgrade PRESERVES the original row's `data_type`. Add a
      regression test asserting `data_type` is non-blank on all downgrade emissions. Gate:
      `_index` has 0 attempted_failed rows with blank data_type + error_reason ends in
      `_no_parquet_at_canonical_path`. (repo: instruments-service)
      — SUPERSEDED (no code change): reconcile_phantom_manifest_rows_all.py:1195-1196 confirmed only sets capture_status + error_reason, preserves all other cols incl. data_type; blank data_type originates from upstream aggregate writers, not phantom audit
- [ ] [DATA] P1. **CF-7 relabel of the existing 4,903 blank-data_type tail** — after the bug
      fix ships, do a one-shot re-emit (per-venue, per-day) to re-derive `data_type` from the
      original captured row (join on `date`, `venue`, `instrument_type` / `instrument_id`) and
      re-emit the attempted_failed row with the correct atom. Documented tradfi CF-7 cell
      count target: 0. (repo: market-tick-data-service)
