---
doc_type: issue
title: "LIGHTER-ZKSYNC (and likely any Tardis venue) _route_lighter hangs indefinitely when called with writer=None"
summary:
  "While re-verifying the LIGHTER-ZKSYNC Tardis exchange-slug/market_id fix with a diagnostic script calling
  _route_lighter directly with writer=None, the call reliably hung indefinitely (no further log output, no exception, no
  completion) immediately after a successful Tardis download + one 'Event logging not initialized' warning from the
  in-flight registry. Reproduced 3/3 times across trades/book_snapshot_5/derivative_ticker. Not a defect in the
  Tardis-slug/market_id fix itself (real rows download correctly in every case) — this is a separate robustness gap in
  the post-download validation/in-flight-registry path when no real ChunkWriter or setup_events() call is present."
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [tardis, lighter-zksync, hang, event-logging, diagnostics]
related: [/plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md]
created: 2026-07-28
parent_epic: infrastructure_master
priority: P3
source:
  "Discovered while executing defi_satellite_ao_dispatch_batch1-045 (re-verify LIGHTER-ZKSYNC Tardis fix), slot-12,
  2026-07-28."
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
last_updated: 2026-07-28
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

## What I found

Re-verifying the LIGHTER-ZKSYNC Tardis exchange-slug + numeric market_id fix (`market-tick-data-service@0c4000a02`)
required calling `market_tick_data_service.adapters.umi_tick_provider._route_lighter` directly from a standalone
diagnostic script (no real `ChunkWriter`, `writer=None`, `setup_events()` never called — this is not a real service
entrypoint, just a probe). For each of the 3 data_types (`trades`, `book_snapshot_5`, `derivative_ticker`), the sequence
was identical:

1. `Tardis streaming request: exchange=lighter, symbol=<id>, data_type=<dt>, date=2026-07-01` — correct.
2. `Free data date detected, skipping auth` — correct (first-of-month free tier).
3. `Tardis streaming success: <N> rows, ...` — real data, confirms the fix works.
4. `DomainValidationService initialized` + a `Stage-0 OBSERVE: non-canonical instrument-id form` notice (expected — cefi
   single-instrument shard filenames are not full canonical instrument_ids, a separate known/tracked pre-existing gap,
   not this finding).
5. `WARNING in-flight key=<key> failed: Event logging not initialized. Call setup_events() first.`
6. **Then: nothing. No further log lines, no exception, no return from the awaited coroutine.** CPU/RSS on the process
   stayed elevated (in one 3-symbol/3-data_type combined run, RSS grew past 13GB before eventually being killed by an
   outer `timeout`) but no forward progress was observed. Each single-symbol, single-data_type repro also hung the same
   way after step 5, requiring the exact PID to be killed manually.

## Why it matters

- This is NOT the fix being re-verified — the Tardis slug (`lighter`, not `lighter-zksync`) and numeric market_id
  resolution both work correctly on current code; real rows returned every time (trades: 88,494/218,300/591,860 rows
  across market_ids 0/1/2; book_snapshot_5: 1,459,257 rows; derivative_ticker: 238,121 rows — all for BTC market_id=1 on
  2026-07-01).
- But it's a real robustness gap: any code path that reaches `_route_lighter` (or, likely, the shared
  `TardisAdapter.download_batch`/in-flight-registry plumbing more generally, not LIGHTER-specific) without a live
  event-logging system initialized appears to hang forever rather than failing fast or degrading gracefully. That's a
  foot-gun for future diagnostic tooling, one-off scripts, or tests that call these adapters directly (a genuine, if
  rare, production-adjacent risk — a mis-wired one-off backfill/diagnostic script could hang a process indefinitely
  instead of erroring).
- Root cause NOT yet isolated (not confirmed): the in-flight registry's failed-item path awaiting a flush/ack that
  nothing ever provides when there's no real writer consuming it; or a retry loop with no backoff cap tied to the "Event
  logging not initialized" condition.

## Recommended decision

Investigate whether `TardisAdapter.download_batch` / `_ChainAnnotatingWriter` / the in-flight-registry consumer path has
an unbounded await when `writer is None` and/or `setup_events()` was never called, and either (a) fail fast with a clear
error in that case, or (b) add a bounded timeout so a misconfigured caller degrades instead of hanging.

## Todos

- [ ] [DIAG] P3. Root-cause the indefinite hang in the Tardis download post-processing path (in-flight registry /
      `DomainValidationService` / event-logging consumer) when a caller invokes an adapter's `download_batch`/
      `_route_*` with `writer=None` and no prior `setup_events()` call. Reproduce via a minimal standalone script
      calling `_route_lighter(..., writer=None, ...)` for any Tardis-routed venue/data_type; use `asyncio.wait_for`
      wrapping or `py-spy dump`/`faulthandler` to capture the exact await point causing the hang. Repo:
      market-tick-data-service (adapter call site) / unified-trading-library (in-flight registry, event facade). **Done
      when**: the exact blocking await is identified and documented (or fixed, if the fix is a clear one-line-class
      bounded-timeout/fail-fast change — otherwise stop at the documented root cause for a human design decision on the
      right fix).
