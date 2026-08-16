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

> **✅ PHASE 1 SHIPPED 2026-08-16** — mtds@bd07cfc3 (F1-F7 + the SPORTS `written_venues` fix) · utl@9fcf12af (F8).
> Both repos `quality-gates.sh --no-fix` GREEN before either shipped. Every fix is a no-op at the default
> `--batch-date-concurrency 1`, so nothing changes for the currently-running serial fleet.

- [x] ✅ [BACKEND] P0. **F1 — `KnownDeadShardGate` lost-update race.** — mtds@bd07cfc3. Gate is now a PROCESS-shared
      singleton (`load_shared_known_dead_shard_gate` / `persist_shared_known_dead_shard_gate`) behind one reentrant
      lock that also guards every `record_attempt`/`is_known_dead`/`dead_keys`/`persist`; interval-persisted
      (`SHARED_GATE_PERSIST_INTERVAL_SECONDS=300`) plus an `atexit` final flush. Call sites moved into the new
      `_process_scope.run_date_prologue`. Evidence (`tests/unit/engine/test_date_concurrency_correctness.py`):
      `test_per_date_gate_instances_lose_the_other_date_s_verdicts` reproduces the OLD lost update (date A's key
      ABSENT from the persisted blob), `test_concurrent_dates_share_one_gate_and_persist_the_union` asserts BOTH
      dates' keys survive, + load-once / interval-throttle / force-persist tests.
- [x] ✅ [BACKEND] P0. **F2 — get blocking calls off the event loop, stop re-reading the whole index per date.** —
      mtds@bd07cfc3. Date predicate pushed down (`filters=[("date","==",normalized_date)]`, mirroring
      `_tier3_prior_capture_guard`); availability check, preflight guards and `check_shard_freshness` all wrapped in
      `asyncio.to_thread`. Guards memoized per (bucket, asset_group) on a **TTL, not a permanent latch** — corrected
      during implementation: `assert_consolidator_healthy` reads a LIVE signal, so a permanent memo would stop
      detecting a consolidator that dies mid-backfill. Evidence:
      `test_preflight_availability_read_pushes_the_date_predicate_down`,
      `test_preflight_guards_run_once_per_bucket_for_the_whole_process`,
      `test_preflight_guards_re_run_once_the_recheck_ttl_has_elapsed`, plus two "a raising guard is never memoized"
      tests.
- [x] ✅ [BACKEND] P0. **F3 — catalog re-registration race.** — mtds@bd07cfc3. Took the LOCK route, not the hoist:
      `register_all_catalog_readers_once` runs registration on a worker thread under a per-loop `asyncio.Lock` with
      double-checked locking. **Finding — the `asyncio.to_thread` move is what MAKES the lock load-bearing**: while
      the call was inline and fully synchronous, asyncio could not actually interleave the read-then-write (no await
      point inside it), so the documented "race" was really a whole-loop stall for the entire ~1.6M-row download.
      Both halves are now fixed. Evidence: `test_concurrent_dates_trigger_exactly_one_catalogue_download` (6
      concurrent callers → 1 download), `test_registration_does_not_block_the_event_loop`.
- [x] ✅ [BACKEND] P0. **F7 — fail-closed guard for manifest write mode.** — mtds@bd07cfc3.
      `TickDataHandler._assert_date_concurrency_preconditions` raises when concurrency > 1 and
      `manifest_per_vm_shards` is off (citing `_writer_io.py::_write_to_gcs`'s own "melts under fleet load"), AND
      when concurrency > 1 without `--start-date` (Phase 2's watermark has no anchor without it, so the run would
      silently fall back to the racy max-seen frontier). Evidence:
      `tests/unit/cli/test_tick_data_handler_date_concurrency.py` — 9 tests incl. both raise paths, the
      serial-is-unaffected case, and the no-args/Cloud-Run-daily-batch case.
- [x] ✅ [BACKEND] P1. **F4 — process-level Graph semaphore.** — mtds@bd07cfc3. Now
      `_process_scope.get_graph_semaphore()`, lazily built once per event loop (rebuilt on loop change so the test
      suite's many `asyncio.run` loops don't share a bound semaphore). Evidence:
      `test_graph_semaphore_budget_is_process_wide_not_per_date`.
- [x] ✅ [BACKEND] P1. **F5 — bound the in-flight task multiplier.** — mtds@bd07cfc3.
      `validate_date_concurrency_inflight_budget` in `config/service_config.py` (config-time only, no runtime
      change) rejects `date_concurrency × tardis_max_inflight_tasks > 4 × tardis_max_concurrent_downloads` and names
      the exact `TARDIS_MAX_INFLIGHT_TASKS` value to set. **⚠️ Phase 3 MUST read this**: at defaults, concurrency 3
      REQUIRES `TARDIS_MAX_INFLIGHT_TASKS=42` (3×42=126 ≤ 128) — the launcher must set it or the canary fails closed
      at preflight before fetching anything. Correction to this todo's original text: there was NO pre-existing
      validation block in `service_config.py`; one was added. UTL semaphore instance-scoping is still open — see
      Deferred work below.
- [x] ✅ [BACKEND] P2. **F6 — CeFi resolver-miss attribution.** — mtds@bd07cfc3. Took the process-exit route, NOT
      date-keying: the accumulators are reached from a pure leaf (`resolve_cefi_instrument_id`) via paths that carry
      no date and partly run on `run_in_executor` worker threads, so any date-keying scheme (including a contextvar)
      would mis-attribute across the executor boundary — an unreliable attribution is worse than an honest
      process-global one. `log_and_reset_cefi_resolver_misses` → `note_cefi_resolver_miss_day`: cumulative for the
      run, names every date covered, interval-throttled (the first date still logs immediately, preserving the live
      signal on a long backfill) with an `atexit` final emission.
- [x] ✅ [BACKEND] P2. **F8 — UTL `pre_process_skip` try-placement parity.** — utl@9fcf12af. Moved inside the try in
      `_drive_concurrent`. Evidence: `TestPreProcessSkipRaiseIsolation` — a handler raising on ONE date now yields
      `processed=4, failed=1` under BOTH drivers, and serial/concurrent result dicts are asserted equal.
- [x] ✅ [REVIEW] P2. **CONFIRMED REAL and fixed** — mtds@bd07cfc3. `written_venues` was assigned only inside the
      non-SPORTS branch of `_write_date_manifest` but read unconditionally by the summary `logger.info`, so every
      SPORTS date raised `UnboundLocalError` AFTER `writer_pool.flush_all()` had already succeeded. **Blast radius
      was wider than the "non-blocking warning" the design assumed**: it also suppressed that date's summary line,
      its cefi-resolver-miss report, and (once Phase 2 landed) its completion-checkpoint signal. Fixed by hoisting
      the assignment above the branch — the value is branch-independent, so behaviour is unchanged for every other
      asset_group. Evidence: `test_sports_manifest_finalize_completes_without_unbound_local` + a non-sports
      counterpart.

### Phase 2 — checkpoint watermark (fixes a bug already live on TradFi, independent of CeFi)

- [x] ✅ [BACKEND] P0. **Contiguous-completion watermark SHIPPED** — utl@9fcf12af (`_vm_progress.py`) +
      mtds@bd07cfc3 (the `process_ticks` completion signal + `TickDataHandler.preflight` arming). Design as
      specified: `arm_contiguous_completion_watermark(range_start)` arms the mode once at run start,
      `record_date_completed(date)` is the explicit signal, and `last_completed_date` is the highest D whose WHOLE
      prefix back to the range start is signalled. `monotonic` is DERIVED (latches false if the prefix ever
      shrinks), never hardcoded. Emitted line format is byte-identical — a test asserts every marker matches
      `vm-exec-with-gcs-tee.sh`'s literal grep regex, so neither it nor `relaunch_backfill_vm.py` changes.
      **Two design decisions worth knowing**: (1) arming FAILS CLOSED on a non-`YYYY-MM-DD` range start, because
      several one-off migration scripts call `record_vm_progress` with a zero-padded object INDEX
      (`f"{done:010d}"`) — they keep the legacy max-seen frontier byte-for-byte; (2) once armed, the legacy
      `record_vm_progress` hook STOPS emitting, since two emitters would race to overwrite PROGRESS.json and the
      max-seen one is precisely the frontier that runs ahead. The completion signal sits inside
      `process_ticks`' manifest-write `try` AFTER the write returns, so a date whose write raised never advances the
      watermark; the "no active venues" early-return also signals (its full expected-empty set IS the completion
      evidence — otherwise a run opening on below-floor dates would pin the watermark at ∅ forever). Evidence
      (`tests/unit/test_vm_progress.py`, 12 tests):
      `test_out_of_order_completion_never_jumps_over_an_unfinished_date` asserts the exact `∅→D1→D3→D3` progression
      with `monotonic=true` throughout and no jump to D5;
      `test_a_date_whose_manifest_write_raised_never_advances_the_watermark`;
      `test_arming_stops_the_legacy_max_seen_emitter`;
      `test_a_non_date_range_start_does_not_arm_and_keeps_legacy_mode`;
      `test_every_watermark_marker_matches_the_tee_wrapper_regex`.
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

> **🟢 UNBLOCKED 2026-08-16** — Phase 1 + Phase 2 shipped (mtds@bd07cfc3, utl@9fcf12af), both repos QG-green.
> **Two hard preconditions the launcher MUST satisfy, or the canary fails closed at preflight before it fetches
> anything** (this is deliberate, F5/F7): (1) `MANIFEST_PER_VM_SHARDS=true` — production backfill VMs already set it
> via `setup-data-pipeline-vm.sh`, so verify rather than assume; (2) `TARDIS_MAX_INFLIGHT_TASKS` scaled down by the
> date-concurrency factor — **for the planned `--batch-date-concurrency 3` canary that means
> `TARDIS_MAX_INFLIGHT_TASKS=42`**. An explicit `--start-date` is also now REQUIRED under concurrency > 1 (the
> resume checkpoint anchors on it); the CeFi launcher already passes `START_DATE`, so verify it reaches the CLI.

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

## Deferred work after 2026-08-16

| Item                                                                                                                                                                                                                                                                                             | Priority | Owner / next step                                                                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 0 duty-cycle measurement was never run (the plan gates the rest of the work on it). Phases 1+2 shipped anyway because they are correctness fixes that stand on their own — but the Phase-0 "if duty cycle > 85%, re-scope to F2 only" decision point is still unanswered before the canary. | P1       | Run it against the live `cefi-binance-futures-2026-heavy-*` run.log before/alongside the Phase 3 baseline run.                                                              |
| Phase 3 (launcher flag, VM stop, baseline/canary runs) — deliberately NOT touched this session per operator scope.                                                                                                                                                                              | P0       | Handled separately; read the 🟢 banner above Phase 3 first for the two fail-closed preconditions.                                                                           |

- [ ] [BACKEND] P2. **UTL follow-up — instance-scope `ParallelPerSymbolRunner`'s in-flight semaphore.**
      `run()` mints a fresh `asyncio.Semaphore(self._max_concurrent)` on every call
      (`unified-trading-library/unified_trading_library/streaming/parallel_per_symbol_runner.py`), so the "max
      in-flight tasks" knob is per-CALL, not per-process — which is why F5 had to be a config-time guard rather than
      a real bound. Hoisting it to a per-instance (or per-process) semaphore would let date concurrency and
      `TARDIS_MAX_INFLIGHT_TASKS` be tuned independently instead of having to divide one by the other. Flagged in
      the original design as the bigger, separate UTL change; not required for Phase 3.

## Progress Log

- 2026-08-16 — Filed from a dedicated opus-tier design investigation (full text preserved in the linked issue doc and
  this session's own record). Operator ruled: human plan, execute today, canary on the live VM.
- 2026-08-16 — **Phase 1 (F1-F8) + Phase 2 implemented, tested, QG-green and SHIPPED** — mtds@bd07cfc3,
  utl@9fcf12af. Both repos ran `quality-gates.sh --no-fix` to full green BEFORE either shipped (MTDS: ALL QUALITY
  GATES PASSED, 11017 tests, cov 81.9%; UTL: ALL QUALITY GATES PASSED). ~35 new regression tests across 4 files.
  Notes for whoever picks up Phase 3:
  - **Three design decisions differ from the plan text** (all argued in the todo entries above): F3 took the lock
    route and found the "race" was really a whole-event-loop stall (asyncio could not interleave a fully
    synchronous read-then-write); F2's guard memo is a TTL rather than a permanent latch (a permanent one would
    stop detecting a consolidator that dies mid-backfill); F6 took process-exit emission rather than date-keying
    (the accumulators are reached across an executor boundary where no date context propagates reliably).
  - **The suspected SPORTS `written_venues` bug was REAL** and had a wider blast radius than the design assumed —
    it suppressed the summary line, the resolver-miss report and the completion checkpoint, not just a warning.
  - **A cross-test leak the fixes introduced was caught by the suite, not by review**: the process-level preflight
    -guard memo made an existing stale-consolidator test pass its gate silently. Fixed properly with an autouse
    reset fixture in `tests/conftest.py` (same pattern already used for the catalog-registration guard) plus the
    TTL change — worth knowing because any FUTURE process-level state added here needs the same treatment.
  - **Both repos had to ship via the sanctioned `Quickmerge: direct-carveout-dirty-deps` path** — quickmerge's
    dependency pre-flight was blocked throughout the session by foreign uncommitted WIP in `unified-api-contracts`
    (a concurrent agent's untracked `flatten.py` / `canonical/crosscutting/flatten_readiness.py` /
    `tests/internal/unit/test_flatten_readiness.py`). Never my own dirty state; MTDS was additionally rebased onto
    4 peer commits and RE-GATED green before the push.
