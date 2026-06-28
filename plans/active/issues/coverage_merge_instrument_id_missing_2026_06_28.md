---
doc_type: plan
title: "measure_honest_coverage merge dedup missing instrument_id — shard-level accuracy broken"
created: 2026-06-28
parent_epic: instruments_master
assigned_vm: NA
source:
  - mvp_backfill_cefi_tick_v10_2026_06_27.md G4 verification
summary: "`scripts/measure_honest_coverage.py` (instruments-service) Bug 2 fix (bbff145) added a prd/non-prd merge that deduplicates on `_SHARD_KEY = [\"date\", \"venue\", \"data_type\"]`. However, the manifest sh..."
status: active
nature: process
asset_group: cross-asset
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

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

- [ ] [CODE] P1. Fix measure_honest_coverage merge to aggregate prd+non-prd counts without instrument-level dedup (avoids OOM) — `instruments-service`. Use prd aggregate (cap/af/ec) + non-prd eu count; remove row-level merge. Update `_count_statuses` / `_compute_coverage` / tests accordingly.
