---
doc_type:
title: measure_honest_coverage merge dedup missing instrument_id — shard-level accuracy broken
summary: '`scripts/measure_honest_coverage.py` (instruments-service) Bug 2 fix (bbff145) added a prd/non-prd merge that deduplicates on `_SHARD_KEY = ["date", "venue", "data_type"]`. However, the manifest sh...'
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-28
parent_epic: instruments_master
priority: P2
source: [mvp_backfill_cefi_tick_v10_2026_06_27.md G4 verification]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
locked_since: 2026-05-21
---

> **✅ RESOLVED → archived 2026-06-30.** Fix `instruments-service@f81e339` (`_SHARD_KEY_WITH_IID` + eu-only secondary
> read) is live + regression-tested. Content-verified (§6 A4.1 of `plan_issue_epic_consolidation_2026_06_30`).

## What I found

`scripts/measure_honest_coverage.py` (instruments-service) Bug 2 fix (bbff145) added a prd/non-prd merge that
deduplicates on `_SHARD_KEY = ["date", "venue", "data_type"]`. However, the manifest shard atom is
`(date, venue, instrument_id, data_type)` — the `instrument_id` dimension is absent from the dedup key.

The column-prune (72bd260) reads only `["capture_status", "venue", "data_type", "date"]` to avoid OOM on the
35.8M-row cefi manifest. Without `instrument_id`, the dedup collapses ALL instruments of a venue/data_type on a
day into one row. The result after merge is only ~164K rows (distinct date/venue/data_type tuples) instead of the
expected ~5-40M shard-level rows, producing a false coverage of 74.03%.

Confirmed: prd manifest has `instrument_id` column. Running `--no-merge` gives accurate prd-only metrics (5.4M
rows, 82.75% of processed shards captured). The non-prd oracle (35.8M rows, June 27) holds the eu universe.

## Why it matters

Coverage is the primary gate metric for G4 of `mvp_backfill_cefi_tick_v10_2026_06_27.md`. A wrong merge produces
a falsely high coverage number (74% vs real ~38%). The correct G4 gate metric requires accurate af and eu counts.
Using `--no-merge` is a valid workaround: prd af=610,207 (true backfill failures), non-prd eu=4,122,727 (unprocessed
oracle rows).

## Recommended decision

Fix `_merge_manifests` to aggregate counts from each manifest separately rather than doing a row-level merge:
- captured + af + ec: from prd aggregate
- eu: from non-prd aggregate
- No row-level dedup needed → avoids instrument_id OOM issue

Implementation: change `_read_manifest` to return pre-aggregated counts (dict) instead of a raw DataFrame when
merge=True. Keep the DataFrame path for `--no-merge`. Update `_compute_coverage` to accept both shapes.

Alternatively: read `instrument_id` but only for small asset groups where memory allows; skip merge for large
cefi/defi manifests.

## Todos

- [x] [CODE] P1. Fix measure_honest_coverage merge to aggregate prd+non-prd counts without instrument-level dedup (avoids OOM) — `instruments-service`. Use prd aggregate (cap/af/ec) + non-prd eu count; remove row-level merge. Update `_count_statuses` / `_compute_coverage` / tests accordingly.
  — instruments-service@f81e3395a · QG green ✅ · Implemented as: add `instrument_id` to `_READ_COLUMNS` + `_SHARD_KEY_WITH_IID`; `_merge_manifests` uses full shard key when instrument_id present (fallback to 3-col with warning); new `_read_parquet_eu_only` uses pyarrow push-down filter to read only eu rows (~4.1M vs 35.8M) from oracle for memory-bounded merge. New test `test_merge_instrument_id_prevents_cross_instrument_collapse` verifies per-instrument dedup.
