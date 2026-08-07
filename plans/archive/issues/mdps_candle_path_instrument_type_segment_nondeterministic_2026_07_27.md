---
doc_type: issue
title: MDPS candle object path's instrument_type segment presence varies run-to-run for the same shard
summary: >-
  Two consecutive --force candle writes for the identical (CEFI, BINANCE-FUTURES, trades, 2026-07-05, 1m, BTC-USDT@LIN)
  shard landed at two different object paths in the -test- bucket — one with an instrument_type= path segment, one
  without — despite byte-identical content (same md5Hash, same size). Not root-caused; tracked as a P3 follow-up
  alongside the existing candle canonical-path migration epic.
status: false-positive
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer, admin]
created: 2026-07-27
author: unknown
assigned_vm: planning
assigned_role: data_engineering
parent_epic: infrastructure_master
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md,
    market-data-processing-service/market_data_processing_service/app/core/output_path_helpers.py,
  ]
source: [data_pipeline_check_mdps_features_2026_07_20.md todo 8]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
tags: [data, mdps, canonical-path, minor]
priority: P3
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

> **🟢 ARCHIVED 2026-08-06** — `status: false-positive` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Root-cause proved no non-determinism — 'The current code CANNOT produce the segment-less
> path'; it is version skew (pre-bcc4d64 legacy object) and migrate_candle_canonical_2026_07.py converges the duplicate;
> no code fix needed for MDPS. Moved by the 2026-08-06 AO issue-doc archive sweep.

# MDPS candle object path's instrument_type segment presence varies run-to-run for the same shard

## What I found

While re-running `/data-pipeline-check-mdps` force-leg checks against the SAME shard (CEFI:BINANCE-FUTURES:trades,
day=2026-07-05, instrument BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN) across several independent `--force` VM runs today,
two OBJECTS exist side by side in the `-test-` bucket for the identical timeframe=1m candle, byte-identical content
(same `md5Hash=aS3EOfBORmGK24TlkgEpOA==`, same `size=246354`), but at two different paths — one WITH an
`instrument_type=PERPETUAL` path segment, one WITHOUT it:

```
processed_candles/by_date/day=2026-07-05/pipeline_mode=batch_tardis/timeframe=1m/data_type=trades/instrument_type=PERPETUAL/venue=BINANCE-FUTURES/BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN.parquet
processed_candles/by_date/day=2026-07-05/pipeline_mode=batch_tardis/timeframe=1m/data_type=trades/venue=BINANCE-FUTURES/BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN.parquet
```

Per `/data-pipeline-check-mdps`'s own skill doc: "`instrument_type=` is **required** on this declared/canonical template
but only **tolerated** (not required) by the force/skip legs' measured template — a not-yet-migrated legacy object still
on disk during the P7 migration window lacks it." That describes a KNOWN legacy-vs-canonical split, but does not explain
why a **fresh `--force` re-run today** would write to the segment-less path at all, given every attempt used the
identical CLI invocation shape.

## Why it matters

If the instrument_type segment's presence in the write path is non-deterministic for the identical input (same
venue/instrument/day/timeframe/pipeline_mode), that is either (a) a race/ordering dependency in how the writer resolves
`instrument_type` for this instrument (e.g., depends on which entry of the 424,624-key wire-map hash iteration order
lands first), or (b) two different code paths (e.g., the `pipeline_e2e_check.py` skill's own launcher invocation vs. a
plain direct `python -m market_data_processing_service --operation process` CLI invocation) resolve `instrument_type`
differently for the same shard. This was NOT root-caused this session (out of scope for todo 8's force/skip proof) but
is exactly the kind of "canonical shape gap" the check skill's own `content_check=non_canonical` worklist is meant to
catch — it should have caught this if the canonical leg had run against both write attempts.

## Recommended decision

File as tracked follow-up rather than block on it — todo 8's force/skip proof does not depend on which of the two paths
is "the" canonical one; both carry the same 7,615-candle-equivalent content. Root-cause during the canonical A/B/C
migration work already tracked (`candle_canonical_path_migration_execution_2026_07_24.md`) rather than as new scope
here.

## Todos

- [x] ✅ [DATA] P3. Root-cause: version skew, not non-determinism — the segment-less path was written by pre-`bcc4d64`
      code (~2026-07-21), the canonical path by current code. Neither invocation-path (same
      `_write_candles`→`write_candle_parquet` chain) nor race (`_infer_instrument_type` is CPU-local, no shared state).
      Current code is deterministic; the duplicate exists because old object at legacy path evaded the new code's
      canonical-path skip-if-exists check. Migration script `migrate_candle_canonical_2026_07.py` will converge. (repo:
      market-data-processing-service).

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY -> `assigned_vm: planning` (in place, name
  unchanged). sole todo is a bounded root-cause with two named candidate mechanisms (invocation-path vs resolution
  race), determinable by code read; conflict-check clear (`data_pipeline_check_mdps_features` only REFERENCES this doc
  as owner). Shared conflict-check protocol:
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` sect.3 - CLEARED.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries) — reviewed against current doc content, list still
  accurate (unchanged).
- **Root cause analysis 2026-08-05** (slot 5, task mdps_candle_path_instrument_type_segment_nondeterministic-001):
  **Neither candidate mechanism is the cause.** The two paths are from DIFFERENT CODE VERSIONS, not a non-determinism in
  the current code.

  _Evidence chain_:
  1. `git log` confirms the canonical shape (`instrument_type=` segment) landed in `bcc4d64`
     (`feat(candles): canonical single-derivation writer — instrument_type+SOURCE data_type+pipeline_mode`,
     ~2026-07-21/22). Writes predating this commit produce the segment-less path.
  2. The CURRENT write path is deterministic — both `_build_candle_output_path` (skip-if-exists via
     `derive_candle_object_path` in `canonical_writer_shaping.py:967`) and `write_candle_parquet` (actual upload via
     `build_canonical_candle_object_path` in `canonical_writer.py:331`) funnel through the SAME canonical builder.
  3. `_infer_instrument_type("BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN")` always returns `"PERPETUAL"` — the 3-segment
     id's position-1 token is authoritative (step 1 of the 6-step resolution in `canonical_writer_shaping.py:344-404`).
     The function is purely CPU-local, no shared state, no I/O — no race surface exists.
  4. NOT invocation-path-dependent: the skill driver (`/data-pipeline-check-mdps`) and direct CLI both funnel through
     `_write_candles` → `_upload_candles_to_gcs` → `write_candle_parquet`. No alternate write seam exists.
  5. The duplicate was created because: old code wrote to the legacy (segment-less) path → new `--force` code checked
     for existence at the CANONICAL path → didn't find it → wrote a second byte-identical copy at the canonical path.
     This is exactly the gap `migrate_candle_canonical_2026_07.py` exists to close.

  _Conclusion_: The current code CANNOT produce the segment-less path. `build_canonical_candle_object_path` in
  `output_path_helpers.py:74-110` always passes `instrument_type` (a required `str`) to `build_canonical_candle_path`,
  which always includes the `instrument_type=` segment (UTL `registry.py:324-362` → `_candle_prefix` appends it when
  `instrument_type is not None`, i.e. always for the public API). The migration script will converge the two objects
  onto the canonical path. No code fix needed for MDPS — the write path is already correct and deterministic.

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.
