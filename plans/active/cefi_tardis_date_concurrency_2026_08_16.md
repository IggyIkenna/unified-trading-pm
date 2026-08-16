---
doc_type: plan
title: Enable bounded date-concurrency for the CeFi Tardis backfill (fix the correctness gaps first)
summary: >-
  The CeFi Tardis backfill runs date-serial (~4 MB/s live-measured, vs a documented 17.56 MB/s resolved ceiling from
  the archived 350x-collapse investigation). The fix mechanism already exists — unified-trading-library's
  `--batch-date-concurrency` driver, already live on TradFi/Deribit — but CeFi's launcher never enables it, and 6 real
  correctness bugs (one already live on the TradFi fleet today) must be fixed first. This plan executes the full
  design: measure, fix correctness, harden the checkpoint watermark, enable for CeFi behind an opt-in flag, canary on
  the live VM.
status: active
nature: design
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, deployment-service]
scope: [engineer]
tags: [cefi, tardis, throughput, concurrency, checkpoint, big-finding]
related:
  [
    /plans/active/issues/cefi_tardis_date_serial_barrier_still_open_2026_08_16.md,
    /plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    /plans/active/issues/vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/cefi_tardis_date_serial_barrier_still_open_2026_08_16.md,
    /plans/archive/issues/cefi_tardis_throughput_collapse_350x_2026_07_17.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/__init__.py,
    unified-trading-library/unified_trading_library/service_framework/_adapter.py,
    unified-trading-library/unified_trading_library/manifest_writer/_vm_progress.py,
    deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh,
  ]
supersedes:
superseded_by:
depends_on: []
source: "Design produced by a dedicated opus-tier investigation, 2026-08-16 interactive session — full design text
  archived in this plan's Progress Log first entry"
assigned_role: backend_engineer
effort: high
drift_direction: advance-code
---

# Enable bounded date-concurrency for the CeFi Tardis backfill

> **Read `/plans/active/issues/cefi_tardis_date_serial_barrier_still_open_2026_08_16.md` first** — it has the live
> measurement (4 MB/s vs 17.56 MB/s resolved) and the corrected throughput expectation (low single-digit-x, NOT the
> archived doc's stale ~14x). This plan is the execution of that issue's linked design.

## Why — the corrected picture

`market_tick_data_service/engine/orchestrator/__init__.py::process_ticks` processes one calendar date across all
active venues via `asyncio.gather()`, writes that date's manifest, THEN the caller starts the next date. This is the
archived `cefi_tardis_throughput_collapse_350x_2026_07_17.md`'s own final, never-shipped todo. A design investigation
this session found:

1. The fix mechanism **already exists**: `unified-trading-library`'s `--batch-date-concurrency` driver
   (`service_framework/_adapter.py::_drive_concurrent`), already wired end-to-end for CeFi's exact launch path
   (`deployment-service/scripts/setup-data-pipeline-vm.sh:2057,2080-2081`) and **already live in production on
   TradFi** (`_tradfi-ohlcv-launcher-lib.sh`, default concurrency 20) and Deribit DVOL (concurrency 3). CeFi's
   launcher (`launch-cefi-sharded-backfill.sh`) simply never sets the env var.
2. The Tardis fetch concurrency cap (`TARDIS_MAX_CONCURRENT_DOWNLOADS`, 32) is a **process-global singleton
   semaphore** — N concurrent dates share ONE 32-slot budget, they do NOT get N×32. This is what makes enabling date
   concurrency safe from a Tardis-per-IP-lock perspective.
3. Manifest writes are already safe under concurrent dates (disjoint row keys, a process-level lock on the shared
   per-VM shard write). **6 real bugs are NOT safe** and must be fixed first (Phase 1 below) — one of them
   (checkpoint watermark going non-monotonic) is confirmed already live on the TradFi fleet today, independent of
   this plan.
4. Recommended shape: **Option A** (harden + enable the existing bounded-lookahead driver), NOT a full work-queue
   flatten — both hit the identical 32-slot ceiling, but a flatten requires rebuilding per-date error attribution,
   manifest-completion tracking, and the checkpoint contract by hand, for zero extra throughput.

## Phases (execute in order — each phase gates the next)

### Phase 0 — measure first (no code, blocks everything else)

- [ ] [DATA] P0. Measure the CeFi VM's real duty cycle: on the live `cefi-binance-futures-2026-heavy-*` VM (or its
      run.log), compute the fraction of wall-clock time with ≥1 Tardis fetch in flight, and the per-date wall-time
      split into prologue (venue-set build through preflight) / fan-out (`asyncio.gather`) / epilogue (manifest write
      + sentinel + known-dead-gate persist). **If duty cycle already exceeds 85%, STOP — re-scope this plan down to
      just Phase 1's F2 (preflight pushdown) and file the rest as a low-priority follow-up**, since Option A's ceiling
      would then be under 1.2x.
- [ ] [DATA] P0. Read a live TradFi VM's `PROGRESS.json` (via `unified_trading_library`'s storage client — never a
      `gcloud storage`/`gsutil` subprocess) and record whether `monotonic` is `false`. This confirms or refutes the
      §Phase 2 checkpoint-regression claim before any code changes.

### Phase 1 — correctness fixes (must ship + be QG-green before any concurrency flag is touched)

- [ ] [BACKEND] P0. **F1 — `KnownDeadShardGate` lost-update race.** Make the gate a process-level singleton (load
      once behind a lock, shared across in-flight dates, persist once at process exit + on an interval under the same
      lock) — `market_tick_data_service/engine/orchestrator/known_dead_shard_gate.py` +
      `engine/orchestrator/__init__.py`'s load/persist call sites. Regression test: two concurrent dates each
      recording distinct dead shards, assert the persisted blob contains BOTH sets.
- [ ] [BACKEND] P0. **F2 — get blocking calls off the event loop, stop re-reading the whole index per date.** Add
      `filters=[("date","==",...)]` pushdown to the preflight availability-index read
      (`market_tick_data_service/engine/orchestrator/preflight.py`, mirror the pattern already used in
      `_tier3_prior_capture_guard.py`); wrap the preflight availability check, preflight guards, and
      `check_shard_freshness` (`cli/handlers/tick_data_handler.py`) calls in `asyncio.to_thread`; memoize the
      bucket-scoped preflight guards per-process instead of per-date. Ship this independently first — it's a real win
      even at concurrency=1.
- [ ] [BACKEND] P0. **F3 — catalog re-registration race.** Guard `_registered_catalog_asset_groups` (
      `engine/orchestrator/catalog_registration.py`) with an `asyncio.Lock`, or hoist registration into
      `TickDataHandler.preflight()` (runs exactly once) instead of inside `process_ticks`. Prevents two concurrent
      dates both re-downloading the ~1.6M-row catalogue (the documented rc=137 OOM class).
- [ ] [BACKEND] P0. **F7 — fail-closed guard for manifest write mode.** At `TickDataHandler.preflight()`: if
      `--batch-date-concurrency > 1` and `manifest_per_vm_shards` is not enabled, raise loudly rather than silently
      using the single-writer-per-process CAS path under concurrent writers. Regression test included.
- [ ] [BACKEND] P1. **F4 — process-level Graph semaphore.** `_graph_semaphore` (`engine/orchestrator/__init__.py`) is
      built fresh per date (`Semaphore(3)`) — N dates means 3N concurrent Graph-based venues. Make it module-level /
      process-scoped.
- [ ] [BACKEND] P1. **F5 — bound the in-flight task multiplier.** `ParallelPerSymbolRunner` mints a per-call
      semaphore (`unified-trading-library/unified_trading_library/streaming/parallel_per_symbol_runner.py`), so N
      concurrent dates give N×128 in-flight task slots. Cheapest fix: scale `TARDIS_MAX_INFLIGHT_TASKS` down by the
      date-concurrency factor in the CeFi launcher so `N × inflight ≈ 128`, and assert
      `N × tardis_max_inflight_tasks ≥ 4 × tardis_max_concurrent_downloads` in
      `market_tick_data_service/config/service_config.py`'s existing validation block. File instance-scoping the
      semaphore as a P2 UTL follow-up, not required for this ship.
- [ ] [BACKEND] P2. **F6 — CeFi resolver-miss attribution.** `log_and_reset_cefi_resolver_misses` (
      `market_interface/adapters/cefi/catalog_id_resolver.py`) clears process-global counters per date-finalize, so
      concurrent dates cross-attribute misses in the log. Key the accumulators by date, or emit once at process exit.
      Observability-only, not a correctness blocker — can ship after Phase 3 if time-constrained.
- [ ] [BACKEND] P2. **F8 — UTL `pre_process_skip` try-placement parity.** `_drive_concurrent`
      (`unified-trading-library/unified_trading_library/service_framework/_adapter.py`) calls
      `handler.pre_process_skip` outside the try (unlike `_drive_serial`) — a raise there aborts the whole date range
      under concurrency instead of isolating to one date. Move inside the try for parity. Currently inert for MTDS
      (default no-op override) but a real hardening fix.
- [ ] [REVIEW] P2. Confirm/fix the suspected SPORTS-path bug found during the design read: `written_venues` in
      `market_tick_data_service/engine/orchestrator/manifest_finalize.py` is assigned only inside one branch but read
      unconditionally afterward — likely an `UnboundLocalError` on the SPORTS branch specifically, currently masked as
      a non-blocking warning. Confirm with a targeted test before touching; unrelated to this plan's concurrency work
      but found along the way — fix in this batch if trivial, otherwise split to its own issue doc.

### Phase 2 — checkpoint watermark (fixes a bug already live on TradFi, independent of CeFi)

- [ ] [BACKEND] P0. Convert `unified_trading_library/manifest_writer/_vm_progress.py` from a max-seen watermark to a
      **contiguous-completion watermark**: track dates that have FULLY completed (an explicit completion signal at
      the end of `process_ticks`, gated on that date recording ≥1 captured shard or a full expected-empty set — never
      on a date whose manifest write raised), and emit `last_completed_date` as the highest date D such that every
      date from the range start through D is complete. Keep the emitted line format
      (`last_completed_date=... monotonic=...`) byte-identical so
      `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh` and
      `deployment-service/scripts/recovery/relaunch_backfill_vm.py`'s parsing need no change. Regression tests:
      out-of-order completion signals (`D3,D1,D2,D5` from a `D1` start) produce watermark progression
      `∅→D1→D3→D3`, never `D5`, `monotonic=true` throughout; no completion signal emitted for a date whose manifest
      write raised.
- [x] ✅ [DATA] P1. **CHECKED 2026-08-16 — claim NOT confirmed by sample, correcting the design's framing.** Read
      `PROGRESS.json` for 5 recent `tradfi-bf-nyse-ohlcv-1m-2025-d05-*` VMs — all show `monotonic: true`. That
      launcher's own `LAUNCH_PARAMS.json` carries no `BATCH_DATE_CONCURRENCY` key at all (it's
      `launch-tradfi-bf-nyse-ohlcv-1m.sh`, not necessarily the same launcher the design cited,
      `_tradfi-ohlcv-launcher-lib.sh`). The underlying code-level race in `_vm_progress.py` (max-seen watermark, not
      contiguous-completion) is still real and confirmed by direct code read — Phase 2's fix is still worth doing —
      but "already actively breaking on the live TradFi fleet today" is NOT confirmed by this sample and should not
      be asserted as fact. Did not chase further given this session's scope; whoever picks up Phase 2 should find an
      actual `_tradfi-ohlcv-launcher-lib.sh`-launched VM (if one exists) before re-asserting the live-regression
      framing.

### Phase 3 — enable for CeFi + canary (only after Phase 1 + Phase 2 are QG-green and shipped)

- [ ] [INFRA] P0. Add `BATCH_DATE_CONCURRENCY` env passthrough to
      `deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh`, stamping `VM_BATCH_DATE_CONCURRENCY` metadata
      (the `cefi-coverage-backfill` branch of `setup-data-pipeline-vm.sh` already consumes it — confirm no further
      wiring needed there). **Default OFF** (unset = concurrency 1, current behavior) — the canary run sets it
      explicitly, never a blanket default flip.
- [ ] [OPERATOR] P0. **Stop the live `cefi-binance-futures-2026-heavy-*` VM cleanly at its current chunk boundary**
      before the canary run (Tardis's hard N=1-concurrent-VM cap means there is no true A/B — canary must be
      sequential on the same VM shape, never a second concurrent VM). Confirm the stop, note the exact checkpoint
      reached, before Phase 3's remaining todos proceed.
- [ ] [DATA] P0. **Baseline run**: relaunch the same VM shape, `--batch-date-concurrency` unset, bare
      `TARDIS_MAX_CONCURRENT_DOWNLOADS` default, a FIXED 14-day window already fully captured in PROD (idempotent,
      re-runnable) with `--force`, BINANCE-FUTURES heavy tier. Record MB/s, shards/hr, 403 count, ConnectionTimeout
      count, peak RSS, duty cycle.
- [ ] [DATA] P0. **Canary run**: same VM shape/window/`--force`, `--batch-date-concurrency 3` (start small — Tardis
      has a per-IP lock TradFi's Databento path doesn't). Compare against baseline. **Hard abort on: any HTTP 403
      `code=274`, RSS above baseline peak +25%, or any manifest row divergence from the baseline for that window.**
      Diff manifest rows (row key, `capture_status`, `row_count`, `source`, `pipeline_mode`) between the two runs for
      byte-identity.
- [ ] [DATA] P1. **Preemption drill**: with concurrency=3 live, terminate the VM mid-window; confirm
      `relaunch_backfill_vm.py` resumes from the new watermark with no date in the window ending up missing from the
      manifest.
- [ ] [DATA] P1. If steps above are clean: step to concurrency 6, re-measure; stop at the first step that doesn't
      improve throughput or trips an abort criterion. Do NOT jump straight to TradFi's 20 — that was tuned against a
      different vendor's per-IP budget (~80 vs Tardis's 32).
- [ ] [DATA] P1. Once a stable concurrency level is confirmed clean, relaunch the real BINANCE-FUTURES resume
      (`ONLY=BINANCE-FUTURES:2026:heavy START_DATE=<checkpoint+1>`) at that concurrency, resuming the actual backfill
      this plan was motivated by.

### Phase 4 — optional, only if Phase 0 shows the tail dominates

- [ ] [BACKEND] P3. If the per-date long-tail fetch latency (not the prologue/epilogue) is the dominant residual
      cost, widen the concurrency window further rather than attempting a full queue-flatten — re-open this plan's
      analysis, do not default to Option B (rejected in the design for good reason: identical throughput ceiling, far
      higher implementation/correctness risk).

## Explicitly out of scope

Raising `TARDIS_MAX_CONCURRENT_DOWNLOADS` above 32 — that number is a measured, documented value
(`market_tick_data_service/config/service_config.py`); date concurrency is the lever this plan pulls, not the fetch
cap.

## Progress Log

- 2026-08-16 — Filed from a dedicated opus-tier design investigation (full text preserved in the linked issue doc and
  this session's own record). Operator ruled: human plan, execute today, canary on the live VM.
