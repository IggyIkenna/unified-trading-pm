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

## Actionable todos (fix-worker cold-start)

- [ ] [DATA] P0. **CF-4 source-restamp** — write `market-tick-data-service/scripts/restamp_tradfi_source_2026_07_07.py`
      (mirror `stamp_schema_version_v9_mtds_2026_06_29.py`): filter manifest to
      `source==""` AND `pipeline_mode!=""` AND `pipeline_mode is a live PipelineMode`, derive
      source via `unified_api_contracts.source_string_for(PipelineMode(pm))`, re-emit through
      `record_empty(...source=...)` / `record_failed(...source=...)` on the same row_key.
      Dry-run + `--apply` shape. Gate: CF-4 GREEN (0 blank source in tradfi manifest).
      (repo: market-tick-data-service)
- [ ] [CODE] P0. **CF-7 phantom-audit bug fix** — patch
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` so the
      captured→attempted_failed downgrade PRESERVES the original row's `data_type`. Add a
      regression test asserting `data_type` is non-blank on all downgrade emissions. Gate:
      `_index` has 0 attempted_failed rows with blank data_type + error_reason ends in
      `_no_parquet_at_canonical_path`. (repo: instruments-service)
- [ ] [DATA] P1. **CF-7 relabel of the existing 4,903 blank-data_type tail** — after the bug
      fix ships, do a one-shot re-emit (per-venue, per-day) to re-derive `data_type` from the
      original captured row (join on `date`, `venue`, `instrument_type` / `instrument_id`) and
      re-emit the attempted_failed row with the correct atom. Documented tradfi CF-7 cell
      count target: 0. (repo: market-tick-data-service)
