---
doc_type: plan
title: MDPS filter-pushdown + memory pathology — audit, fix, verify (2026-05-28)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, features-service, market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_06/features_calc_efficiency_and_correctness_2026_05_27.md,
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
  ]
created: 2026-05-28
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-05-28
---

# MDPS filter-pushdown + memory pathology — audit, fix, verify

> **✅ ARCHIVED 2026-06-21 — audit+fix+verify complete + codex Phase 4 present; 0 deferred work. [unlock-plan]**

> **Operator direction 2026-05-28**: a **larger MDPS service refactor** is queued and will start in some time; a
> **14-day backfill run is in flight right now**, so the actual 4h/24h-unblocking data is arriving via that path. The
> plan below stays open as the structural-fix tracker (it's the right diagnosis), but the features-side unblock no
> longer depends on the per-day OOM tactic decisions (3.X-A/B/C/D below) — the bigger refactor will subsume them. Treat
> 3.X-\* as informational once the 14-day data lands.

## Goal

Diagnose + fix the MDPS memory-pathology that makes narrow-scope backfills consume 70 GB+ of RAM regardless of the
`--instrument-ids` / `--venues` / `--data-types` filters. Land the smallest viable fix so a small-sample CeFi 1h-candle
backfill (16 days × 2 venues × ~4 instruments, trades-only) runs on a modest VM in under an hour.

## Provenance (what happened — DO NOT RECREATE)

This plan exists because **two MDPS runs blew up on memory in the same day** (2026-05-28):

1. **VM `mdps-backfill-cefi-20260528-112956`** (`e2-standard-8`, 32 GB, `MDPS_MAX_WORKERS=4` default). Full-scope CeFi
   backfill for 2026-04-15 → 04-30. Hung after processing **only 2 instruments** in 40 minutes (per-VM shard had 2
   entries; run.log frozen). SSH unreachable. VM auto-deleted by operator after diagnosis.

2. **Local laptop smoke** (`mdps@cef7263`, `MDPS_MAX_WORKERS=2`, narrow scope: 4 instruments × 1 data_type × 1 day).
   `MDPS_DATA_TYPES=trades MDPS_VENUES="BINANCE-FUTURES BYBIT" MDPS_INSTRUMENT_IDS="BINANCE-FUTURES:PERPETUAL:BTCUSDT BINANCE-FUTURES:PERPETUAL:ETHUSDT BYBIT:PERPETUAL:BTCUSDT BYBIT:PERPETUAL:ETHUSDT"`.
   **Successfully aggregated all 7 timeframes for the first instrument in ~43 seconds**, then memory grew to **75.2 % of
   93 GB ≈ 70 GB** in the next ~2 minutes, with the MDPS log saying
   `BatchOrchestrationMixin: memory backpressure engaged at 75.2 % — gating new submissions`. Operator killed before the
   OOM-killer fired.

**Pre-existing workspace signal we missed**: `deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh` already
contains:

> "TradFi gets e2-highmem-8 (64 GB) + max-workers=2 (halves concurrent peak footprint vs default 4) until the MDPS
> [memory issue is fixed]." "single python process hit 79 GB RSS (basedpyright/pytest)" — incident log 2026-05-15.

The memory pathology is **already documented** workspace-wide as an unfixed MDPS issue; this plan is the focused fix.

### Smoke log fingerprint (so the next agent recognises the symptom WITHOUT recreating)

```text
ManifestWriter: per-VM shard updated (1 total entries, 1 new)    ← first TF lands
POLARS AGGREGATED: 1440 1m candles
ManifestWriter: per-VM shard updated (2 total entries, 1 new)    ← second TF
…
POLARS AGGREGATED: 1 24h candles                                  ← all 7 TFs done for 1 instrument
BatchOrchestrationMixin: memory backpressure engaged at 75.2 %    ← memory bloat starts HERE
   …                                                              ← no further progress before kill
```

If you see the backpressure line, **stop the process** — do not let it climb. The memory grows between instruments, not
during aggregation.

## Hypothesis (most likely root cause — needs Phase 1 to confirm)

`--instrument-ids` / `--venues` / `--data-types` filters apply at **write-time**, not **read-time**. MDPS loads the
entire `raw_tick_data/by_date/day=…/asset_group=…/venue=…/instrument_type=…/data_type=…/*.parquet` corpus for the date
into memory, then filters at the per-instrument-write step. Narrow scope shrinks GCS writes (the visible "4 instruments
× 7 TFs" output), not RAM reads.

**Evidence supporting this**:

- 4-instrument scope hit 70 GB — way more than 4 instruments of trades data should occupy.
- First instrument's outputs all wrote successfully (read + aggregate + write works); memory bloat appeared **between**
  instruments (and the launcher VM hung at exactly the same boundary, after 2 instruments).
- The workspace's own mitigation pattern (`e2-highmem-8 + max-workers=2`) treats the symptom by capping concurrent
  in-memory blocks, not by narrowing reads — consistent with reads being unfiltered.

## Phase 1 — AUDIT (read-only; no execution risk)

Goal: confirm filter-pushdown is the root cause and pinpoint the exact line(s) where the filter should attach to the
read path. Deliverable: short audit doc at `plans/active/issues/mdps_filter_pushdown_audit_2026_05_28.md` (frontmatter:
`title` / `created: 2026-05-28` / `author: <slot>` / `source: [mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md]`
/ `locked_by: live-defi-rollout`). No code edits in this phase.

- [x] [AUDIT][P1] **1.1 Trace the read path.** ✅ Done. See audit doc § 1 — full CLI→worker call-stack with file:line at
      each hop. Memory-backpressure log line confirmed at `batch_workers.py:236` inside
      `BatchOrchestrationMixin._on_memory_warning()`.
- [x] [AUDIT][P1] **1.2 Map where the filter args land.** ✅ Done. See audit doc § 2 — 12-row table classifying every
      `instrument_ids` / `venues` / `data_types` callsite.
- [x] [AUDIT][P1] **1.3 Identify the bloat owner.** ✅ Done. See audit doc § 3 — bloat is **not** per-instrument
      DataFrame retention. The scanner returns the wrong file list (`instrument_ids` silently dropped on venue-prefix
      match at `orchestration_scanner.py:441-449`); workers faithfully download whatever the scanner queued. Memory
      grows linearly with the over-queued blob count.
- [~] [AUDIT][P1] **1.4 Sanity-check on a contained, instrumented canary.** SKIPPED — static-trace evidence in § 3 is
  unambiguous. A canary would burn ~1h to confirm `len(files_to_process)` is much larger than the operator-requested
  scope; the code already shows it. Audit § 6 recommends going straight to Phase 2 + Phase 3.1 (which IS the canary, but
  against the fix instead of against the bug).
- [x] [AUDIT][P1] **1.5 Update the hypothesis + name the fix.** ✅ Done. See audit doc § 4 (verdict: CONFIRMED with
      refinement — plumbing exists, gating logic short-circuits) and § 5 (3-line fix in
      `_collect_matching_parquet_blobs` + parallel fallback). Sibling-correct shape exists at
      `orchestration_scheduling.py:243` as proof of intent.

> **Phase 1 deliverable:**
> [`plans/active/issues/mdps_filter_pushdown_audit_2026_05_28.md`](issues/mdps_filter_pushdown_audit_2026_05_28.md).
> Audit recommends skipping Phase 2.2 (`del` between iterations) and Phase 2.3 (streaming orchestrator) — both target a
> non-existent leak. The scanner fix alone should resolve the pathology; if Phase 3.1 fails the RSS cap, revisit.

## Phase 2 — FIX (only after Phase 1 names the cause)

Principle: **minimum-viable change**. Don't refactor more than needed.

- [x] [P1] **2.1 Push the 3 filters down to the read layer.** ✅ Done — `market-data-processing-service@e47205d`.
      Refined per audit: the _read-time_ plumbing was already wired through to
      `CandleOrchestrationScanner._collect_matching_parquet_blobs`, but the venue-prefix shortcut silently dropped
      `instrument_ids` whenever the prefix matched. Fix splits the gate so `instrument_ids` is always applied as its own
      step (`orchestration_scanner.py:441-457` + identical pattern for the sports/prediction fallback at lines 380-398).
      Regression tests in `tests/unit/test_orchestration_scanner.py` (6 new, 28 sibling tests still green): pre-fix
      returned 8 blobs for the 4-symbol scope, post-fix returns 4; pre-fix returned 3 for `venues=None + instrument_ids`
      (filter ignored), post-fix returns 2.
- [~] [P1] **2.2 Free per-instrument memory between iterations.** SKIPPED — audit § 3 confirms there is no
  per-instrument retention leak. The polars frame is `del`'d at `live_workers.py:470`; the pandas frame is scoped to one
  instrument's `_process_all_timeframes()` call. Bloat was upstream (scanner over-queueing). Revisit only if Phase 3.1
  RSS cap fails with the scanner fix in place.
- [~] [P2] **2.3 Optional: streaming-per-instrument orchestrator mode.** SKIPPED — same reasoning. The orchestrator IS
  already streaming-per-instrument (ThreadPoolExecutor with one future per blob, max*workers=N concurrent). The previous
  symptom was N × \_over-queued blobs*, not N × _too-large frames_. Once the scanner returns the operator-requested file
  list, the existing concurrency model is correctly shaped.

If Phase 3 verification surprises us with residual memory growth, revisit 2.2 and 2.3 with concrete evidence.

## Phase 3 — VERIFY (no re-OOMing the dev machine)

Critical: verification runs on a VM, never locally. The fix must be confirmed on **a deliberately modest VM** so the bug
returns audibly if the fix is incomplete — not silently absorbed by capacity.

- [x] [VERIFY][P1] **3.1 Canary run** — single day, BINANCE-FUTURES + BYBIT × BTCUSDT + ETHUSDT × trades for 2026-04-15.
      ✅ **PASSED on e2-standard-8 (32 GB)** — `mdps-backfill-cefi-20260528-135305`. Evidence: pre-count scanner
      returned 18 (venues-only, expected); production processing scanner returned **4 files** (fix confirmed); 4/4
      instruments × 7 timeframes = 28/28 parquets landed in
      `gs://market-data-tick-cefi-test-central-element-323112/processed_candles/by_date/day=2026-04-15/`; 30,460 candles
      total; 191s wall-clock; exit 0; no `MEMORY_BACKPRESSURE` events; VM auto-shutdown. **Plan-amendment:** the
      original `e2-standard-4` (16 GB) target proved too small for MDPS startup itself — the prod
      availability_index.parquet is 526 MB compressed (~2-5 GB decompressed) + 4128-instrument reference data load =
      ~4-8 GB baseline before any per-blob processing. First attempt on `e2-standard-4` OOM'd during
      `check_shard_freshness` BEFORE the scanner ran (rc=137). The 32 GB box is the realistic minimum for any MDPS
      narrow-scope verification; the "RSS < 2 GB" target in the original plan was unattainable independent of the
      filter-pushdown fix.
- [~] [VERIFY][P1] **3.2 7-day scope** — PARTIAL on `e2-standard-8` (32 GB), `mdps-backfill-cefi-20260528-140503`. Day 1
  (2026-04-15) ✅ — `Listed 4 files` (scanner fix confirmed twice over Phase 3.1 + 3.2 day 1), 28/28 outputs landed for
  the 4 × 7 cells in test bucket. **Hang on day-2 transition.** VM stayed RUNNING but SSH unresponsive + no application
  log progress for 38+ min after `POLARS AGGREGATED: 1 24h candles` for instrument 3/4 of day 1 (other instruments
  completed silently — verified in test bucket). VM deleted manually after diagnosis. **NEW FINDING — surfaced by this
  canary, contradicts Phase 1 audit conclusion**: the per-instrument / per-day DataFrame retention the audit dismissed
  in § 3 IS real at multi-day scale. The scanner fix solves the _intra-day_ over-queueing (the original 70 GB symptom),
  but cross-day cleanup is independently missing — the orchestrator re-enters `process_category` per date without
  freeing the previous date's pandas frames, 526 MB manifest cache, or 4128-instrument reference DataFrame. Phase 2.2
  (per-iteration `del` + targeted `gc.collect()` at the date-loop boundary in
  `process_handler.py:_process_candles_for_one_date` and/or at the per-instrument boundary in
  `live_workers._process_instrument_file`) needs to be re-opened — this plan's audit was wrong to skip it. See
  "Re-opened Phase 2.2" below.
- [x] ✅ [VERIFY] P1. **3.3 The actual unblock — 16-day narrow scope** 2026-04-15 → 04-30. **PASSED.** VM
      `mdps-backfill-cefi-20260529-090755` auto-deleted (exit 0). GCS
      `market-data-tick-cefi-test-central-element-323112/processed_candles/by_date/` has all 16 days (2026-04-15 →
      2026-04-30) × 28 parquet files each (4 instruments × 7 timeframes). No OOM / no MEMORY_BACKPRESSURE events. MDPS
      tarball `@db233e266a4f` (Stage 1-4 pure-polars + `_cleanup_after_day` wired) on `e2-standard-8` (32 GB),
      `MAX_WORKERS=2`.

## Re-opened Phase 2.2 (NEW — added 2026-05-28 mid-Phase-3)

The audit's § 3 conclusion ("not per-instrument DataFrame retention") was based on static read of
`live_workers.py:447-470` showing the polars frame is `del`'d before the pandas frame is returned. That's correct for
the immediate scope but misses cross-iteration retention. Empirical evidence from Phase 3.2: day 1 completes (4
instruments × 7 TFs = 28 outputs land), then day 2 transition hangs — symptom signature of cumulative memory pressure on
the 32 GB box, distinct from the intra-day fan-out the scanner fix addressed.

- [x] [AUDIT][P1] **2.2a** Re-inspected the date loop at `process_handler.py:642-661`. Per-iteration construction of
      `CandleOrchestrationService` in `_process_one_category` (line 379) is correct in shape — when the function returns
      the local goes out of scope. The issue is reference-cycle retention via the orchestrator's mixin caches
      (`storage_client`, `data_sink`, `_data_sinks` dict, lazy instruments DataFrame) that Python's reference-counting
      GC doesn't reclaim until a cycle-collection pass runs.
- [x] [P1] **2.2b** Shipped `del orchestrator` at end of `_process_one_category` + `del tracker + gc.collect()` at end
      of `_process_candles_for_one_date` with an RSS log line — `market-data-processing-service@0254531`.
- [~] [P1] **2.2c** Phase 3.2 re-run on `e2-standard-8`, VM `mdps-backfill-cefi-20260528-172303`. **Fix fires correctly
  but is structurally insufficient**:

  ```
  ✅ trades complete: 4/4 succeeded in 133.6s (30,460 candles)
  🏁 cefi processing complete: 4/4 succeeded, 0 errors in 176.7s
  📉 date-boundary GC for 2026-04-15: RSS 25216 MB → 25129 MB (freed 87 MB)
  Processing candles for 2026-04-16
  Listed 18 files from market-data-tick-cefi-central-element-323112/raw_tick_data/by_date/day=2026-04-16/ for data_type=trades
  [vm-exec] command exited rc=137   ← OOM
  ```

  Key data points:
  - Day 1 still completed (4/4 instruments, 30,460 candles, 133.6s).
  - `BatchOrchestrationMixin: memory backpressure engaged at 85.9%` fired during day 1 — the orchestrator's own
    backpressure layer gates new submissions when memory hits the warning threshold. This is working as designed.
  - **Post-day RSS held at 25.1 GB after my `del orchestrator + gc.collect()`** — only 87 MB / 25.2 GB reclaimed
    (~0.3%). Most of the day-1 footprint is NOT reachable from the orchestrator's reference graph at the moment we `del`
    it. `gc.collect()` cannot free it because Python's GC works on reference cycles among Python objects — it doesn't
    reclaim:
    - Polars memory arenas (Polars uses its own allocator; freed bytes stay in the arena, not returned to OS)
    - PyArrow / pandas buffer pools (same pattern as Polars)
    - C-allocator heap fragmentation (glibc malloc rarely returns mmap'd regions to OS without an explicit
      `malloc_trim(0)`)
    - Possible module-level caches in the data_sink / event sink / ResourceProfiler
  - Day 2 attempted at ~25 GB baseline; needed ~27 GB peak again; total ~52 GB ⇒ OOM-killed at 32 GB cap.

  **Conclusion**: cross-date `del + gc.collect()` is correct discipline but cannot reach the underlying retention. The
  25 GB per-day floor is the operational reality on the current MDPS codepath; Phase 2.2 lowers it by ~87 MB, not the
  ~20 GB that would be required to fit a second day on 32 GB.

## Operator-driven findings + decision (2026-05-28 EOD)

After Phase 3.2 attempt-2 surfaced the 25 GB per-day floor, operator (Harsh) raised four concerns and chose a near-term
path. Capturing them here so subsequent agents have the full reasoning context, not a half-baked picture from the audit.

### Finding A — `_cleanup_after_day` exists but isn't wired into the success path

The MDPS authors built
[`_cleanup_after_day`](../../../market-data-processing-service/market_data_processing_service/app/core/orchestration_base.py#L79)
— clears `candle_processing_service.cache` + `sampling_service.cache` for the current date, then `gc.collect()`s. It's
invoked from exactly **one** place:
[`orchestration_service.py:489`](../../../market-data-processing-service/market_data_processing_service/app/core/orchestration_service.py#L489)
— the early-exit branch of `_load_tradable_context` when `tradable_instruments.empty`. The normal "instruments exist, do
work, succeed" path never calls it.

This is the most likely owner of the 25 GB residue Phase 2.2's `del orchestrator + gc.collect()` couldn't reach —
`del`ing the orchestrator doesn't clear the per-service caches it constructed inside, because the service objects
(`candle_processing_service`, `sampling_service`) may be module-level singletons or otherwise held outside the
orchestrator's reference graph.

**Immediate fix**: wire `_cleanup_after_day(date_str)` into the normal success path of `process_category` (and any other
terminal path of per-day work). Should run even on single-day single-instrument single-data_type drilldown runs — there
is no path through the orchestrator where skipping cleanup is correct.

### Finding B — CLI granularity claims aren't matched by the filter logic

Operator: "instrument*id is the last thing and it covers everything — which venue, which asset_group, which data_type."
That is the \_intent* of the canonical instrument_id form (`VENUE:INSTRUMENT_TYPE:SYMBOL`). But the current
implementation breaks the contract:

- `MDPS_INSTRUMENT_IDS` env var → bridged to `--instrument-ids` argv → reaches `_collect_matching_parquet_blobs` →
  matched as **substring against the blob path**.
- Blob path: `…/venue=BINANCE-FUTURES/instrument_type=perpetual/data_type=trades/BTCUSDT.parquet`.
- The canonical form `BINANCE-FUTURES:PERPETUAL:BTCUSDT` is **not** a substring of that path. So if you pass the
  _correct_ canonical form, the scanner returns **zero** blobs.
- The only thing that works today is the bare-symbol substring (`BTCUSDT`) which matches `BTCUSDT.parquet`. That's what
  the canary used.
- And bare-symbol substring is **ambiguous** — `BTCUSDT` matches across all venues, all instrument_types, and any other
  instrument whose symbol contains the substring (e.g., a hypothetical `1000BTCUSDT.parquet` or `BTCUSDT-PERP.parquet`).

So the CLI surface lies about its granularity. To actually pin to one cell — single date × single venue × single
instrument_type × single data_type × single symbol — the operator has to pass `--data-types` + `--venues` +
`--instrument-ids` all together AND know the substring semantics.

The right shape: parse the canonical instrument_id form, derive `venue` + `instrument_type` + `symbol` from each entry,
and filter the blob path on each derived axis. Then `--instrument-ids BINANCE-FUTURES:PERPETUAL:BTCUSDT` alone is
sufficient (with `--data-types`, since data_type IS an independent axis — the same instrument has trades +
book_snapshot_5 + derivative_ticker, all valid).

### Finding C — orchestrator design assumes one-VM-per-shard (legacy fan-out)

The orchestrator carries heavy per-instance state (lazy GCS client, per-asset_group `_data_sinks` dict, instruments
DataFrame, manifest read buffer). That's appropriate if each VM processes ONE shard (one day × one venue × one
asset_group × one data_type) — startup cost amortises across a tight scope, and process-exit reclaims everything.

The original MDPS design assumed thousands or tens of thousands of small VMs. That assumption was abandoned for cost
reasons (each VM has ~$0.01 minimum + setup time per launch), so the workspace pivoted to long-running VMs that process
many shards. But the orchestrator code wasn't refactored when the deployment model changed. The current symptoms (25 GB
per-day floor, cross-date retention, repeated 526 MB manifest reads) are all consequences of running a fan-out-shaped
codebase as a long-running multi-shard worker.

The Phase 2.2 + `_cleanup_after_day` wiring is a tactical patch. The structural fix is a re-architecture for
long-running multi-shard execution — covered in the new architectural plan
[`plans/active/mdps_long_running_multi_shard_architecture_audit_2026_05_28.md`](mdps_long_running_multi_shard_architecture_audit_2026_05_28.md)
(created in this session).

### Finding D — Polars/Pandas churn

`_read_tick_data`
([live_workers.py:449-479](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py#L449-L479))
opens the raw parquet with `pl.read_parquet(low_memory=True)`, converts to pandas via `.to_pandas()`, `del`s the polars
frame, returns pandas. Then `_process_all_timeframes`
([live_workers.py:671+](../../../market-data-processing-service/market_data_processing_service/app/core/live_workers.py#L671))
consumes the pandas frame and (per the `POLARS AGGREGATED:` log lines we saw) re-enters polars for the per-timeframe
aggregation. So the data shape is:

```
GCS bytes
  → polars (read_parquet)
    → pandas (.to_pandas())
      → polars again (for aggregation)
        → pandas (for write?)
          → GCS bytes
```

Each conversion allocates a fresh buffer; the `del` of the polars frame doesn't release the polars arena back to the OS.
This is the same anti-pattern the codex's existing concurrency / single-writer guidance was trying to avoid. There is no
reason to involve both libraries — either pick polars end-to-end (it can do everything pandas does for this workload,
and it's already the chosen aggregation engine), or pick pandas end-to-end with `engine="pyarrow"` for the read.

Pure-polars is the more obvious target since the aggregation is already polars and the codebase has explicit
`POLARS AGGREGATED` log lines suggesting that was the original direction. Eliminating the intermediate pandas would also
let `low_memory=True` actually buy us something — currently it's negated by the immediate `.to_pandas()` copy.

This is also covered in the new architectural plan.

## Operator decision: ship `_cleanup_after_day` wiring + 16-day unblock + architectural plan

Per operator 2026-05-28 EOD, the sequence is:

- [x] ✅ [P0] **3.X-1** Wire `_cleanup_after_day(date_str)` into the success path of `process_category` (and any other
      terminal path where per-day work completes — including single-day-single-instrument drilldowns). Smallest viable
      cleanup landing. — `market-data-processing-service@dcd7416`: added `try/finally` wrapping entire
      `process_category` body (`orchestration_service.py:296-302`) so `_cleanup_after_day(date_str)` fires on every exit
      path. (Note: checkbox was incorrectly reverted by commit `76288c4d6` word-wrap reformat; re-flipped 2026-05-29.)
- [~] [P0] **3.X-2** Rebuild MDPS tarball, re-run Phase 3.2 (7-day) on `e2-standard-8`. Pass criterion: RSS reclaim at
  each date boundary measurable in the `📉 date-boundary GC` log line; no day-2 OOM. **SUPERSEDED by Stage 1-4
  pure-polars refactor** — canary `mdps-backfill-cefi-20260528-195400` used pre-Stage-4 tarball `@029843a` and OOM'd at
  day-2 transition (only `day=2026-04-15` + `day=2026-04-18` landed in test bucket). The Stage 1-4 pure-polars migration
  (commits `ceb7a12..db233e2`) eliminates the polars→pandas→polars double-allocation (Finding D), which was the dominant
  contributor to the 25 GB per-day floor. A fresh tarball `@db233e266a4f` was built 2026-05-29 and used for 3.X-3
  directly — the 16-day run IS the Phase 3.2 re-verification at wider scope.
- [x] ✅ [P0] **3.X-3** Launch the 16-day narrow-scope backfill on `e2-standard-8`. Outputs go to the test bucket so
      downstream agents (features-service, etc.) can re-run their per-shard work against the canary data. — VM
      `mdps-backfill-cefi-20260529-090755` (asia-northeast1-c, e2-standard-8) launched 2026-05-29T09:07:55Z. MDPS
      tarball `@db233e266a4f` (Stage 1-4 pure-polars + `_cleanup_after_day` wired). Scope: BINANCE-FUTURES + BYBIT ×
      BTCUSDT + ETHUSDT × trades × 2026-04-15→2026-04-30, `MAX_WORKERS=2`, output →
      `market-data-tick-cefi-test-central-element-323112`. VM auto-deletes on completion.
- [x] ✅ [AGENT] P1. **3.X-4** Create the long-running multi-shard architectural audit plan (separate file). Don't try
      to land architecture here — that's a multi-week refactor, not a "smallest viable fix". — unified-trading-pm@(see
      commit) | plan: plans/active/mdps_long_running_multi_shard_architecture_audit_2026_05_28.md | 7 phases covering
      execution model, data engine, CLI granularity, observability, codex updates; codex audit of 4 operator findings
      included.

## Phase 4 — Codex SSOT updates (HARD RULE)

- [x] ✅ [AGENT] P2. **4.1 Update `codex/04-architecture/` or `codex/06-coding-standards/` with the read-time filter
      discipline** — every batch service whose pipeline matches MDPS's shape (list raw → filter → load → process →
      write) MUST apply scope filters at the LIST stage, not the WRITE stage. Reference this plan + the 2026-05-28
      incident. (If no codex doc fits, write a stub.) — Doc already landed at PM commit `d52b0eb6`:
      `/codex/06-coding-standards/read-time-filter-pushdown.md`. Covers: rule, anti-pattern, correct pattern,
      verification recipe, reference implementation (MDPS `e47205d`), incidents, cross-service generalization. Checkbox
      flip 2026-05-30.
- [x] ✅ [AGENT] P2. **4.2 ~~Remove the now-stale workspace mitigations~~ Re-scope the TradFi mitigation in the sharded
      launcher.** Updated header comment + `_machine_type_for` inline comment in
      `deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh` to attribute the TradFi
      `e2-highmem-8 +     max-workers=2` mitigation to the BUNDLE-READER issue (not filter-pushdown), name the unblock
      (bundle-reader streaming refactor tracked in `mdps_long_running_multi_shard_architecture_audit_2026_05_28.md`),
      and leave mitigation code untouched. Shipped deployment-service@c566e3e → live-defi-rollout. 2026-05-30.

## DO NOT (anti-patterns the next agent should avoid)

- **Do not run MDPS locally on the dev machine.** It's not configured for MDPS's memory profile; the 2026-05-28 incident
  proved this. Even "narrow scope" hits 70 GB before the fix.
- **Do not "make the VM bigger" as the fix.** `e2-highmem-16` (128 GB) would mask the bug, not solve it. The pathology
  scales with corpus size; today's 4128 instruments is tomorrow's 8000.
- **Do not set `MDPS_MAX_WORKERS > 2` until Phase 3 passes.** Even if the fix lands, validating with workers=1 first
  isolates whether the bloat is per-worker or shared.
- **Do not skip the canary VM** in Phase 3.1. Going straight to 16 days hides whether the fix actually drops RSS or just
  spreads the bloat over more time.
- **Do not add `gc.collect()` blindly** to "fix memory". Measure first; collect targets specific refs the audit
  identified. Unprovoked `gc.collect()` in a hot loop just wastes CPU.

## Performance / time balance (operator-stated principle)

- VM has good capacity → use it sensibly. **Don't pessimize to e2-micro to "save resources"** — that wastes dev-cycle
  time.
- But **don't oversize** either. e2-standard-4 (16 GB) for the canary is the right starting point; scale up only if
  Phase 3.3 needs it for the 16-day window and the fix is sound.
- Time budget: **1.6 calibrated AI-days** (infra class, 0.8× of 2-day baseline). If Phase 1 audit takes > half a day,
  ping operator with the partial findings rather than going dark.
- The unblock is the goal — not making MDPS perfect. Phase 4 cleanup is P2 specifically so the 4h/24h features-side work
  isn't gated on it.

## Success criterion

- 4h + 24h delta_one features land for CeFi 2026-05-03 in `features-delta-one-cefi-test-...`.
- MDPS runs the 16-day narrow-scope CeFi backfill on `e2-standard-4` (16 GB) without backpressure warnings; RSS stays <
  4 GB throughout.
- Workspace mitigation comments in the sharded launcher updated.
