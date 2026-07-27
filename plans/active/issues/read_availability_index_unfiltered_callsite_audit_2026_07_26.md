---
doc_type: issue
title:
  Audit remaining unfiltered `read_availability_index(bucket)` call sites for the same repeated-full-manifest-read OOM
  class that has now hit three times (MTDS rc137, sports 2026-06-22, sports FIXTURES 2026-07-26)
summary: >-
  Fixing an `exit_code=137` OOM in the FIXTURES per-league backfill VM (2026-07-26,
  `sports_freshness_preflight_stale_scope_escape_burns_shared_quota_2026_07_25.md`, now archived) found the SAME root
  cause pattern as two prior, independently-fixed incidents: a function that calls the FULL, unfiltered
  `read_availability_index(bucket)` once per date inside a long per-date loop, decoding the entire manifest (up to ~6.5
  GB for the sports bucket) every time the in-process cache misses. Prior fixes:
  `mtds_backfill_vm_startup_oom_rc137_2026_07_14` (DeFi, `check_shard_freshness`) and the 2026-06-22 sports incident
  (`_should_skip_date_for_per_league`, per its own docstring). This session's fix (`unified-trading-library@666c73d8`,
  `instruments-service@e74e1a00`) converted BOTH of those exact functions to the slim + date-filtered
  `read_availability_index(bucket, columns=[...], filters=[("date","==",date)])` pattern. A quick grep after the fact
  found several MORE unaudited call sites of the bare `read_availability_index(bucket)` form across instruments-service
  and market-tick-data-service — not all of these are necessarily in a per-date hot loop (some may be legitimately
  one-shot, e.g. CLI entrypoints), so this is a triage-then-fix audit, not a blind find-replace.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [oom, manifest, read-availability-index, performance, backfill, recurring-bug-class]
related:
  [
    /plans/active/issues/sports_freshness_preflight_stale_scope_escape_burns_shared_quota_2026_07_25.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
priority: P3
parent_epic: infrastructure_master
source: >-
  Found via `grep -rln 'read_availability_index(bucket)'` immediately after shipping the third independent fix for this
  exact OOM pattern in one calendar month; filed proactively to prevent a fourth recurrence rather than waiting for the
  next backfill VM to crash.
assigned_vm: NA
execution_scope: local-only
estimate_class: research
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# Unfiltered `read_availability_index(bucket)` call sites — third-strike audit

## Unaudited call sites found (2026-07-26, `grep -rln` for the bare no-`columns`/no-`filters` form)

- `instruments-service/instruments_service/cli/main.py`
- `instruments-service/instruments_service/engine/orchestrator/process_preflight.py` (other call sites beyond the two
  already fixed this session — confirm none remain in a per-date loop)
- `instruments-service/instruments_service/engine/orchestrator/venue_core.py`
- `instruments-service/instruments_service/engine/orchestrator/process_completeness.py`
- `instruments-service/instruments_service/engine/orchestrator/catalogue.py`
- `market-tick-data-service/market_tick_data_service/reader.py`
- `market-tick-data-service/market_tick_data_service/scripts/_rebuild_sports_projection.py`
- `market-tick-data-service/market_tick_data_service/scripts/delete_defi_zero_row_placeholders.py`
- `market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py`
- `market-tick-data-service/market_tick_data_service/engine/orchestrator/__init__.py`

Not all of these are wrong — a one-shot CLI entrypoint or a script that runs once per invocation (not per date in a
loop) has no OOM risk from a single full read. The risk is specifically: **called once per date/shard inside a loop that
iterates over a large range**, where the in-process cache (60-120s TTL) misses on every real manifest write and triggers
a fresh full decode each time.

## Todos

- [x] [DATA] P3. **Triage each call site above**: for each, determine (a) is it inside a per-date/per-shard loop over a
      potentially-large range, or a one-shot call; (b) if the former, convert to the slim + date-filtered pattern
      (`columns=[...]`, `filters=[("date", "==", date)]` or a range filter) matching the two call sites already fixed in
      `_queries.py::check_shard_freshness` and `sports.py::_should_skip_date_for_per_league`. **Done when**: every
      per-date-loop call site is converted (with the same column-list-matches-actual-usage discipline the two fixed
      sites used) or explicitly documented as safe (one-shot, small range, or already TTL-cache-warm by construction) —
      no site left unaudited. — already covered by plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md
      (see that doc for execution).
