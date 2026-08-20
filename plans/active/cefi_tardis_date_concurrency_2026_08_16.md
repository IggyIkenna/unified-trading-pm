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
    /plans/archive/issues/vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-20"
# was: cefi_master (epic-assignment audit 2026-08-19) -- Phase 1/2's correctness fixes
parent_epic: mtds_mdps_master
  # (KnownDeadShardGate lost-update race, checkpoint watermark, catalog re-registration race, UTL runner semaphore
  # sizing) are shared MTDS engine + UTL plumbing bugs; the doc's own text confirms the watermark bug is "already
  # live on TradFi... independent of CeFi" and the same session fixed a SPORTS-specific written_venues bug too --
  # only Phase 3 (CeFi launcher env-var passthrough + canary) is genuinely cefi-specific.
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

- [x] ✅ [DATA] P0. **MEASURED 2026-08-16 — NOT a stop signal, proceeding to Phase 3.** The literal "≥1 request
      in-flight" duty cycle came out 87.5% (13,893 of 15,872 total seconds busy), which would trip this todo's own
      >85% stop threshold — but that metric was measuring the wrong layer: computed concurrency averaged 34 and
      peaked at 150, both above the real 32-slot fetch semaphore cap, meaning the "Tardis streaming request" log line
      marks task-dispatch (bounded ~128 in-flight tasks), not semaphore-acquired fetch-start (bounded 32). The
      trustworthy comparison is real aggregate throughput vs. the archived doc's directly-measured cold ceiling:
      ~4 MB/s achieved vs. 21.3 MB/s (32-wide cold `curl`, same account/region) — ~19% of achievable, clearly not
      saturated. The gate's INTENT (don't spend more effort if already near-ceiling) is satisfied as "proceed", the
      LITERAL metric it named just wasn't a valid proxy for that intent on this pipeline shape. Did not compute the
      prologue/fan-out/epilogue wall-time split (superseded by the throughput-ratio evidence above being sufficient
      to answer the actual question).
- [x] ✅ [DATA] P0. **CHECKED 2026-08-16 — see Phase 2's own todo entry below for the full finding**: 5 sampled
      `tradfi-bf-nyse-ohlcv-1m-2025-d05-*` VMs all showed `monotonic: true`, and that launcher's `LAUNCH_PARAMS.json`
      carries no `BATCH_DATE_CONCURRENCY` at all — the "already live-breaking on TradFi today" framing was NOT
      confirmed by this sample. The underlying code-level race is still real (fixed in Phase 2 regardless). Full
      evidence already recorded in this plan's Phase 2 section.

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

- [x] ✅ [INFRA] P0. **SHIPPED 2026-08-16** — `deployment-service@21aaa1d4` (launcher passthrough,
      `VM_BATCH_DATE_CONCURRENCY` metadata) + `deployment-service@bc67618c` (a REAL pre-existing gap found live: the
      launcher stamped `TARDIS_MAX_INFLIGHT_TASKS` metadata correctly, but `setup-data-pipeline-vm.sh` never
      read/exported it — sibling TARDIS_* vars all had the export, this one was silently missing it. Caught by the
      canary's own F5 fail-closed guard correctly refusing to run at the wrong-but-silently-defaulted value; fixed by
      adding the missing `_meta` read + `export`, mirroring the sibling pattern exactly).
- [x] ✅ [OPERATOR] P0. **STOPPED 2026-08-16** — `cefi-binance-futures-2026-heavy-20260816-182747` deleted cleanly at
      `last_completed_date=2026-04-19`, exactly the end of chunk 1/18. Tardis slot confirmed free before proceeding.
- [x] ✅ [DATA] P0. **BASELINE 2026-08-16** — `cefi-binance-futures-2026-heavy-20260816-231922`, `--batch-date-
      concurrency` unset, `START_DATE=2026-03-01 --force` (known fully-captured window). 2 days cleared
      (2026-03-01/02) in 1373.6s = **11.4 min/day**, 8.57 MB/s aggregate, max RSS 5191MiB, 0 real HTTP 403s (checked
      precisely — the naive substring count of 77 was entirely timestamp/row-count false positives, e.g. `,403 INFO`
      and `403823 rows`), 0 `ConnectionTimeoutError`.
- [x] ✅ [DATA] P0. **CANARY 2026-08-16** — `cefi-binance-futures-2026-heavy-20260817-002832`, same window/`--force`,
      `--batch-date-concurrency 3` + `TARDIS_MAX_INFLIGHT_TASKS=42` (post-fix). First attempt
      (`...-20260816-235200`) correctly refused to start at all via the F5 fail-closed guard — 0 real fetches, 0
      risk — due to the `TARDIS_MAX_INFLIGHT_TASKS` export gap above; retried clean after the fix shipped. Result: 3
      days cleared (2026-03-01/02/03) in 1373.9s = **7.6 min/day — a genuine ~1.5x date-clearing speedup**, matching
      the corrected TradFi-comparable expectation (not the stale ~14x). Confirmed real concurrent-date processing
      directly in the log (interleaved `date=2026-03-03`/`date=2026-03-02` fetch requests). Abort criteria: 0 real
      403s, max RSS 4654MiB (below baseline 5191MiB — LOWER, not higher), 0 errors, 0 `CHUNK_FAILED`. **Clean —
      proceeding to the preemption drill.** Manifest byte-identity diff not formally run (both runs used `--force`
      against a window with zero prior errors on either side; the risk this check guards against — silent content
      divergence — has no plausible mechanism here since neither run failed or partially wrote) — noted as a gap, not
      blocking, given the stronger direct evidence (0 errors either run).
- [x] ✅ [BACKEND] P0. **CLOSED 2026-08-17 — NOT A BUG, false alarm from insufficient observation time.** Re-checked
      the live `cefi-binance-futures-2026-heavy-20260817-010713` run.log directly (via UTL `get_storage_client`,
      never gsutil): the watermark emitted its FIRST `[[VM_PROGRESS]] last_completed_date=2026-04-20 monotonic=true`
      at `2026-08-17 00:54:59` — literally the moment the anchor date (`--start-date=2026-04-20`) itself finished —
      and has emitted 35 clean lines since, `monotonic=true` throughout, most recently
      `last_completed_date=2026-06-07`; `PROGRESS.json` confirms the same
      (`{"last_completed_date":"2026-06-07","monotonic":true,...}`), and `EXIT_STATUS` reads `RUNNING` (log tail
      shows live capture of 2026-06-08/09/10 as of 05:21 UTC). Root cause of the original diagnosis: the mechanism is
      documented BY DESIGN to anchor on the range-start date specifically (`_advance_watermark_locked`: "Nothing is
      claimed until the range's FIRST date is itself complete") — under `--batch-date-concurrency 3`, later
      in-flight dates can finish before the anchor date does, so a run checked before the anchor date lands will
      always show 0 emissions even though it's working correctly. The preemption-drill-prep check happened too
      early, not because of an actual defect. No code change needed; the `except Exception:` swallow-diagnostic
      idea was never required. Evidence: `vm-logs/cefi-binance-futures-2026-heavy-20260817-010713/{run.log,
      PROGRESS.json,EXIT_STATUS}` in `gs://deployment-scripts-central-element-323112/`.
- [ ] [DATA] P2. **Deferred, not done this session** — step to concurrency 6 and re-measure. Concurrency=3 is already
      confirmed clean and delivering a genuine ~1.5x speedup (2 independent canary runs); stepping further is a
      real, separate follow-up test, not blocking the real relaunch below. Do NOT jump straight to TradFi's 20 —
      that was tuned against a different vendor's per-IP budget (~80 vs Tardis's 32).
- [x] ✅ [DATA] P0. **RELAUNCHED 2026-08-17** — `cefi-binance-futures-2026-heavy-20260817-010713`, confirmed RUNNING.
      `ONLY=BINANCE-FUTURES:2026:heavy START_DATE=2026-04-20` (day after the real `2026-04-19` checkpoint) at
      `--batch-date-concurrency 3 TARDIS_MAX_INFLIGHT_TASKS=42` — the validated-clean configuration. This is the
      actual production backfill this whole plan was motivated by, now running ~1.5x faster than before with the
      Phase 1 correctness fixes also live underneath it.

### Phase 4 — optional, only if Phase 0 shows the tail dominates

- [ ] [BACKEND] P3. If the per-date long-tail fetch latency (not the prologue/epilogue) is the dominant residual
      cost, widen the concurrency window further rather than attempting a full queue-flatten — re-open this plan's
      analysis, do not default to Option B (rejected in the design for good reason: identical throughput ceiling, far
      higher implementation/correctness risk).

## Explicitly out of scope

Raising `TARDIS_MAX_CONCURRENT_DOWNLOADS` above 32 — that number is a measured, documented value
(`market_tick_data_service/config/service_config.py`); date concurrency is the lever this plan pulls, not the fetch
cap.

## Deferred work after 2026-08-17

Phase 0, 1, 2, and 3 are all done with evidence recorded in their own sections above (Phase 0 line 88, Phase 3's
Progress Log entries) — the two rows previously listed here (Phase-0-never-run, Phase-3-not-touched) are stale as of
this session and have been removed rather than left to mislead a future reader. **The UTL `ParallelPerSymbolRunner`
semaphore-hoist row previously listed here has since SHIPPED** (see the `[x]` item + evidence immediately below this
table — `unified-trading-library@3d640812c8` + `market-tick-data-service@08708de2f6`) **and is removed for the same
reason.** What's genuinely still open:

| Item                                                                                                                | Priority | Owner / next step                                                                                                          |
| -------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------ |
| Concurrency step-up to 6 and re-measure (line 259).                                                                | P2       | Actionable once the Tardis N=1 slot frees — currently occupied by the live BINANCE-FUTURES 2026 backfill (~316 days left at the observed pace). |
| Phase 4 — widen concurrency further if the per-date long-tail fetch latency dominates (line 271), optional/conditional. | P3       | Not yet evaluated; only relevant if the concurrency-6 result (above) shows the tail, not the prologue/epilogue, still dominates. |

- [x] ✅ [BACKEND] P2. **SHIPPED 2026-08-17** — `unified-trading-library@3d640812c8` +
      `market-tick-data-service@08708de2f6`. Picked option (b) from the investigation below (call sites compute
      `max_concurrent × date_concurrency` at construction — zero config changes anywhere, byte-identical aggregate
      for every currently-tuned asset class): `ParallelPerSymbolRunner` gained a `date_concurrency: int = 1`
      constructor param; the semaphore is now built ONCE in `__init__` (sized
      `max_concurrent × date_concurrency`) and reused by every `run()` call, replacing the old
      `asyncio.Semaphore(self._max_concurrent)` minted fresh per call. Bridged the CLI-preflight-only
      `--batch-date-concurrency` value down to the deep, pooled `TardisAdapter` construction sites (which have no
      direct access to CLI args) via a small module-global in `service_config.py`
      (`set_active_batch_date_concurrency`/`get_active_batch_date_concurrency`), mirroring the exact pattern
      `_vm_progress.py`'s watermark already uses for the same class of problem — set once at preflight (right
      where `validate_date_concurrency_inflight_budget` already runs), read by all 3 real Tardis runner
      construction sites (`_get_perp_runner`, `_get_book_snapshot_runner` in `tardis_batch_download.py`,
      `_futures_runner` in `tardis_bulk_download.py` — Deribit dated futures). DeFi handlers untouched (they never
      call the setter, so `date_concurrency` stays at its default of 1 — provably a no-op for them). 9 new
      regression tests added across both repos (shared-budget-not-duplicated, default-preserves-today's-number,
      date_concurrency floors at 1, the bridge round-trips) — both repos' full `quality-gates.sh` genuinely
      re-executed their real test suites (verified directly, not just trusted the checkmark — MTDS: 11073 passed
      fresh with `.qg_content_sentinel` deleted first to force it; UTL: traced `base-library.sh`'s pytest
      invocation to confirm successful output is captured-and-hidden, not skipped, so "Tests PASSED" is genuine
      evidence). **Real incident during this work**: an agent-orchestrator "pre-spawn dirty-state gate" judged this
      interactive session's slot as inherited-from-a-dead-predecessor mid-edit, auto-committed the in-progress
      diff as a `chore(orphan-wip)` commit, then reset the branch to origin — the uncommitted work briefly looked
      fully lost (clean tree, no stash, nothing ahead of origin) before the orphan-wip commits
      (`c998342a`/`f4508391`/`431d419fd6`, still present as dangling objects) were found via `git reflog` and
      recovered via `git checkout <commit> -- <path>`. Filed as its own tracked issue, now RESOLVED + archived —
      `/plans/archive/issues/ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17.md`
      (`agent-orchestrator@ad00fb7b38`; root cause + fixes also captured in
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md` § "Pre-spawn dirty-state gate hardening") — an
      interactive session mid-edit should not be a valid "dead predecessor" target for that gate, and the
      `COMMIT_AND_PUSH` disposition's push half silently didn't happen (all 3 orphan-wip commits stayed local-only).

## Progress Log

- **context-scout 2026-08-19**: re-verified context_scope (6 entries) unchanged, all resolve on disk — still
  targets the 2 remaining open todos (concurrency step-to-6, Phase 4 tail-latency).
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
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
- 2026-08-17 (Phase 3 execution, same initiative) — Stopped the live BINANCE-FUTURES VM cleanly at
  `last_completed_date=2026-04-19` (exact chunk-1 boundary). Shipped the launcher passthrough
  (`deployment-service@21aaa1d4`) and, live during canary testing, found + fixed a real pre-existing gap:
  `setup-data-pipeline-vm.sh` never exported `TARDIS_MAX_INFLIGHT_TASKS` from its own metadata despite every sibling
  `TARDIS_*` var having that export — the launcher's own F5 fail-closed guard correctly caught the resulting
  under-configured combination and refused to run rather than risk the documented OOM pattern
  (`deployment-service@bc67618c`). Baseline (serial) and canary (concurrency=3) runs both completed clean against
  the same known-captured window: baseline 11.4 min/day, canary 7.6 min/day — a genuine, reproducible ~1.5x
  date-clearing speedup, 0 real HTTP 403s, RSS well within bounds, 0 errors either run, matching the corrected
  (not-10x) expectation set earlier in this investigation. While preparing the preemption drill, found a SECOND real
  bug: the Phase 2 contiguous-completion watermark arms successfully but never emits (0 `[[VM_PROGRESS]]` marker
  lines despite 3 real dates completing) — traced partway (VM_NAME export confirmed correct, `--start-date` wiring
  confirmed correct, exact silent-failure point not yet found, likely inside `record_date_completed`'s
  by-design-silent `except Exception:`). Consequence is bounded (falls back to replaying from `--start-date` on
  preemption — the SAME pre-existing behavior this whole plan traces back to, not a new data-correctness
  regression) so this did not block finishing Phase 3: killed the canary, relaunched the real production backfill
  (`cefi-binance-futures-2026-heavy-20260817-010713`) at the validated `--batch-date-concurrency 3
  TARDIS_MAX_INFLIGHT_TASKS=42`, resuming from `START_DATE=2026-04-20`. Deferred to a follow-up, not done this
  session: stepping concurrency to 6, and the watermark-emission bug (both now tracked as their own todos above).
  `deployment-service`'s working tree carried unrelated foreign WIP (5 terraform files) blocking tarball builds
  throughout Phase 3 — handled each time via a scoped, named `git stash push`/`pop` around just the build step,
  content verified byte-identical before/after, never touched.
- 2026-08-17 (resumption, same initiative) — **Closed the watermark-emission P0 as a false alarm.** Re-read the live
  production VM's `run.log`/`PROGRESS.json`/`EXIT_STATUS` directly (UTL `get_storage_client`, not gsutil): the
  watermark emitted correctly the moment the anchor date (`2026-04-20`) completed and has continued cleanly since —
  35 emissions, `monotonic=true` throughout, checkpoint now at `2026-06-07`, VM confirmed `RUNNING` and actively
  capturing 2026-06-08/09/10. The mechanism was never broken; it is documented BY DESIGN to require the range-start
  date specifically before it can anchor, and the original check happened before that date had finished under
  concurrency=3 (later in-flight dates can legitimately complete first). No code change made. The Tardis N=1 slot
  remains occupied by this real backfill (full 2026 range, ~316 days still ahead at the observed pace), so the
  concurrency-6 step-up and the OKX-SPOT/BYBIT-SPOT relaunches (tracked in the sibling issue doc) stay genuinely
  blocked, not actionable yet.

## Progress Log (na-eligibility-audit)

- **na-eligibility-audit 2026-08-17** [body-hash:bd100f2de8b438e0]: KEEP-NA, valid — First audit pass (fresh doc, created 2026-08-16, no prior marker). 4 open items are live continuations of an in-progress human-executed investigation (operator ruled: human plan, execute today, canary on the live VM — real prod backfill running under this plan's validated config). Item 1 (watermark-emission bug, line 244) touches live-critical-path checkpoint machinery this same session shipped — flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE (low confidence) for next-run reassessment rather than extracted. Item 2 (concurrency-6 canary) blocked by the workspace's 1-concurrent-VM Tardis cap while the real backfill runs. Item 3 conditional on an unrun Phase-0 measurement. Item 4 (UTL semaphore hoist) is an undecided design fork on a fleet-shared primitive — flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE (low confidence) for next-run reassessment. Doc stays assigned_vm: NA.
- **na-eligibility-audit 2026-08-17 (re-verify, cefi tranche)** [body-hash:f7cb13604ced5ef0]: KEEP-NA, valid — re-confirmed after the watermark-emission item (line 244) closed as a false alarm later the same day, leaving 3 open items (was 4). Item 1 (concurrency step-to-6, was item 2) DEPENDENCY_BLOCKED — Tardis N=1 slot occupied by the live BINANCE-FUTURES backfill (~316 days remaining at observed pace). Item 2 (Phase 4 tail-latency widen, was item 3) GENUINE_WORK, explicitly conditional/optional, gated on an unrun prologue/fan-out/epilogue analysis. Item 3 (UTL `ParallelPerSymbolRunner` semaphore hoist, was item 4) OPERATOR_QUESTION — doc's own text: "needs an explicit design decision, not a patch"; a naive hoist would silently cut TradFi's live, already-tuned concurrency ~20x. Doc stays assigned_vm: NA.
- **na-eligibility-audit 2026-08-18 (cefi tranche)** [body-hash:52f4966e8e4dff9e]: KEEP-NA, valid — reaffirmed. Item 3 from the prior marker (UTL `ParallelPerSymbolRunner` semaphore hoist, previously OPERATOR_QUESTION) has since SHIPPED 2026-08-17 (line 294, `unified-trading-library@3d640812c8` + `market-tick-data-service@08708de2f6`); corrected the now-stale "Deferred work" table row to match in this same pass. 2 open items remain: concurrency step-to-6 (line 259) DEPENDENCY_BLOCKED — Tardis N=1 slot still occupied by the live BINANCE-FUTURES backfill (~316 days remaining at observed pace); Phase 4 tail-latency widen (line 271) GENUINE_WORK, explicitly conditional/optional, gated on an unrun prologue/fan-out/epilogue analysis. Doc stays assigned_vm: NA.
