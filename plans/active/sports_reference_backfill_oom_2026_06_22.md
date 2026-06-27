---
doc_type: plan
title: Sports reference backfill OOM (TM/SFI/FootyStats per-league skip-check)
summary:
status: active
assigned_vm: planning
nature: process
stage: [meta]
repos: [instruments-service, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-22
parent_epic: sports_master
assigned_role: data_engineering
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
last_updated: 2026-06-27
locked_by: live-defi-rollout
locked_since: 2026-05-21
supersedes:
superseded_by:
depends_on:
source:
asset_group: cross-asset
drift_direction: advance-code
---

# Sports reference backfill OOM — per-league skip-check re-read the 6.5 GB index

## What I found

The TRANSFERMARKT / SOCCER_FOOTBALL_INFO / FOOTYSTATS sports reference backfills OOM-crashed (exit_code=137) within ~2
dates even on e2-standard-8 (32 GB). The WEATHER (OPEN_METEO) backfill on the SAME orchestrator runs fine on 8 GB.

**Root cause (measured):** `instruments_service/engine/orchestrator/sports.py` `_should_skip_date_for_per_league` called
`manifest.lookup()` **once per expected league** (55–93 leagues) per date. Each `lookup()` calls
`read_availability_index(bucket)`. The sports consolidated availability index is **4,147,371 rows x 41 cols = ~6.5 GB in
pandas** (from an 80 MB parquet). The in-process `_INDEX_CACHE` has a **60 s TTL** that expires mid-date under the
throttled per-league fan-out, so the loop re-decompressed the 6.5 GB frame (plus `_merge_shard_frames` concat +
`_backfill` copies, multiple multi-GB frames live at once) up to 93x per date -> 32 GB OOM within ~2 dates.

WEATHER does not fan out per-league (calls the skip path ~0–1x/date) -> at most one 6.5 GB frame per 60 s TTL window ->
fits in 8 GB.

## The fix

`_should_skip_date_for_per_league` now reads the index **ONCE** and resolves all expected leagues in-memory (filter to
service + (date, data_type), build a per-league last-write-wins status map), preserving exact `lookup()` semantics. All
three providers route through this one function.

- [x] [SCRIPT] P1. Fix per-league skip-check to single index read — `instruments-service`
      `engine/orchestrator/sports.py` + regression test
      `tests/unit/test_orchestrator_gaps.py::TestShouldSkipDateForPerLeague::test_index_read_happens_once_not_per_league`.
      Relaunch TM/SFI/FootyStats on e2-standard-8 full range; verify chunk count climbs past the prior ~2-date death
      point with no exit 137.

## Why it matters

Data correctness for the SPORTS asset_group — these backfills cannot complete at all without this fix (0% coverage, 75k+
attempted_failed rows from prior runs).

## Follow-up (DEFERRED — not blocking the OOM fix)

- [x] [SCRIPT] P2. **DONE** Column-prune slim reads via `read_availability_index(columns=[...])` —
      `unified-trading-library@39eccc9c`. Adds `_INDEX_SLIM_CACHE`, `_backfill_slim`,
      `_read_availability_index_slim`, `_read_parquet_columns_safe` (ArrowInvalid fallback), and
      15-test regression suite. Peak decode memory reduced from ~6.5 GB to requested columns only.
      QG: 1 failed → 0 failed (6354 passed, 87.59% coverage). Evidence: `tests/unit/test_manifest_read_index_slim.py`.
