---
doc_type: plan
title: TradFi pyarrow per-symbol-writer fan-out remediation — worst-case confirm + low-risk write-path tuning
summary: >-
  Properly-scoped, phased successor to `issues/tradfi_backfill_oom_remediation_2026_06_24.md`'s open P3 todo ("fix the
  pyarrow per-symbol-writer fan-out identified by the 2026-07-27 memray repro"). That todo was dispatched as a single
  1h-class backlog task (`tradfi_backfill_oom_remediation-001`); a BLOCKED-question raised mid-dispatch was answered by
  main: do NOT attempt the full rewrite from one task — author a properly-scoped, phased plan with gated,
  independently-shippable todos instead, and leave the original backlog item alone pending this re-scope. This plan is
  that re-scope. It resolves the original todo's own ambiguous "either/or" framing (batch symbols onto a shared
  `pq.ParquetWriter`, OR cap concurrently-open writers) as an authoring-time design call rather than leaving it an
  open-ended judgment call for a dispatched worker: both structural options change the current one-file-per-symbol GCS
  output contract (BigQuery external tables + manifest shard atoms depend on it, and the docstring on
  `PartitionedTickWriter` explicitly records that a single-shared-file layout is the OLD design that CAUSED an earlier
  OOM — reverting toward it is not risk-free), so this plan scopes only the LOW-RISK, contract-preserving half (pyarrow
  write-path tuning) as dispatchable work, and defers the structural options to a future dedicated design pass if the
  low-risk half proves insufficient.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [tradfi, backfill, oom, pyarrow, memory, performance, vm-cost, streaming-writer]
related:
  [
    /plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_pyarrow_writer_fanout_remediation_2026_08_01_finalize.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Re-scope of `issues/tradfi_backfill_oom_remediation_2026_06_24.md`'s open `[TRADFI] P3` todo, per a main-agent
  BLOCKED-question ruling received on backlog task `tradfi_backfill_oom_remediation-001` (slot 11, 2026-08-01): "Do NOT
  attempt the full rewrite from this single dispatched task. Instead author/mirror a properly-scoped, phased plan (gated
  todos, each independently shippable) into the consolidated close-out plan per its own banner, and leave this backlog
  item alone pending that re-scope." Authored after reading `market_tick_data_service/engine/orchestrator/
  partitioned_writer.py` (`PartitionedTickWriter._get_writer`/`write_chunk`) and `unified_trading_library/io/
  streaming_writer.py` (`StreamingParquetWriter.write_chunk`) directly (2026-08-01, slot 11) to ground the split between
  "safe to dispatch now" and "needs its own design pass" in the actual code, not just the issue doc's prose.
context_scope:
  [
    /plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md,
    /plans/active/tradfi_backfill_throughput_followups_2026_07_24.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py,
    unified-trading-library/unified_trading_library/io/streaming_writer.py,
  ]
---

# TradFi pyarrow per-symbol-writer fan-out remediation

> **Why this plan exists, not a direct fix.** The source todo's own text offers two structural alternatives ("either
> batch multiple low-volume symbols onto a shared `pq.ParquetWriter` instance instead of one-per-symbol... or cap the
> number of concurrently-open per-symbol `StreamingParquetWriter`s and flush/close eagerly") without deciding between
> them — exactly the open-ended design-call shape `task_template.md` §4 bans from a single AO-dispatched todo. Both
> options change `PartitionedTickWriter`'s current **one-GCS-file-per-symbol** output contract, which downstream
> consumers (BigQuery external tables keyed on `{SYMBOL}.parquet`, the manifest's per-symbol shard atom) depend on — and
> the class docstring explicitly records that the CURRENT per-instrument split was adopted specifically to fix an
> **earlier** OOM caused by merging all instruments into one shared file, so "batch symbols onto a shared writer" is not
> a risk-free reversion. Resolving which structural direction (if any) is worth that risk needs its own design pass, not
> a 1h-class backlog task. This plan instead dispatches the bounded, contract-preserving half of the work now, and
> explicitly defers the structural half (see "Deferred" below) rather than guessing.

## Todos

- [ ] [DATA] P3. **Confirm which writer path the fleet's actual worst-case OOM shards route through, then get a real
      worst-case memory measurement.** The 2026-07-27 memray repro (`market-tick-data-service`,
      `memray run     --native`) measured the per-symbol SINGLES writer path (`PartitionedTickWriter._get_writer`'s
      non-chain branch) on an ordinary NYSE `ohlcv_1m` day — peak RSS 2.899 GB, top allocators
      `pyarrow/parquet/core.py:1180     write_table` + `pandas_compat.py:633 convert_column`. The fleet's documented
      worst case (`tradfi-bf-cme-ohlcv-1m-gc-2025-*`, 60 OOM-kills on e2-standard-4, ~15.3 GB peak) has never been
      memray'd, and it is NOT yet confirmed the same SINGLES writer path even applies to it — CME futures/options roots
      may route through `PartitionedTickWriter`'s OTHER branch (`options_chain`/`futures_chain`, grouped by underlying
      into ONE shared writer per underlying — a structurally different memory profile than "hundreds of small per-symbol
      writers"). First, determine which branch GC/ES/NQ `ohlcv_1m` rows actually carry by checking a sampled row's
      `instrument_type` against `_UNDERLYING_PARTITIONED_TYPES`
      (`market_tick_data_service/engine/orchestrator/symbol_rules.py`) — cite the actual value found, don't assume. If
      SINGLES-routed: pick the heaviest real single date for that root by reading the EXISTING
      `vm-logs/tradfi-bf-cme-ohlcv-1m-{gc,es,nq}-2025-*/run.log` per-date row counts already on GCS (no new VM launch —
      mirrors the read-only methodology `tradfi_backfill_throughput_followups_2026_07_24.md` already used for its own
      CME per-root-date re-measurement), then re-run the SAME memray methodology (real Databento creds via Secret
      Manager, `-test-` bucket, `IS_TEST_RUN=true`, no prod writes) against that date. **Bound the run** before
      executing it — a worst-case repro deliberately targets a ~15 GB peak, well past what should run unbounded on a
      shared host (`RULES.md` §1's memory-bounding HARD RULE, 3 confirmed same-shape incidents including one on
      2026-08-01 itself): use `bash scripts/dev/run-bounded-analysis.sh` with a cap sized above the expected peak (not
      the default), or run on a disposable VM if the expected peak is uncertain. Repo: market-tick-data-service. **Done
      when**: the writer-path classification is stated with evidence (code citation + the actual `instrument_type` value
      sampled), AND either (a) a fresh memray capture's peak-RSS + top-5-allocator table is recorded here (if
      SINGLES-routed — confirming or refuting the same mechanism dominates at ~15 GB scale), or (b) an explicit finding
      that the worst-case shards are CHAIN-routed is recorded with a follow-up todo filed in
      `issues/tradfi_backfill_oom_remediation_2026_06_24.md` for that separate mechanism (not guessed at or fixed here).
      Source: `issues/tradfi_backfill_oom_remediation_2026_06_24.md` (P3's own "Follow-up not done here" note).

- [ ] [BACKEND] P3. **Apply a low-risk pyarrow write-path memory optimization to `StreamingParquetWriter.write_chunk()`
      that reduces the fixed per-`write_table()`-call overhead WITHOUT changing the one-file-per-symbol GCS output
      contract.** In scope (evaluate, apply whichever measurably helps): constructing `pq.ParquetWriter` with
      `use_dictionary=False` or reduced per-column statistics for low-cardinality OHLCV columns (`venue`,
      `instrument_type`, `data_type` etc. — the "dictionary-encoding buffers, zstd compressor context, column statistics
      collectors" the source issue's own memray finding names as fixed per-call cost); reusing a shared `pa.Schema`
      across `write_chunk()` calls instead of re-deriving dictionary/type info from `pa.Table.from_pandas()` on every
      call; or another concrete, equally-scoped pyarrow-tuning knob found while implementing. **Out of scope for this
      todo** (see "Deferred" below): batching multiple symbols onto one shared writer, or capping+eagerly-closing
      concurrently-open writers — both change the per-symbol file-output contract and are explicitly NOT authorized
      here. Validate with a BEFORE/AFTER memray-measured peak-RSS comparison on the repro from todo 1 (or the original
      2026-07-27 NYSE repro if todo 1 found the worst-case shards are CHAIN-routed), plus regression tests proving the
      written parquet content (rows, columns, values, dtypes) is unchanged. If no safe tuning knob produces a meaningful
      peak-RSS reduction, record that negative finding explicitly rather than reaching for the out-of-scope structural
      options. Repos: unified-trading-library (`StreamingParquetWriter` itself), market-tick-data-service (only if
      `_get_writer`'s construction call needs a new kwarg threaded through). **Done when**: `quality-gates.sh` is green
      in both touched repos, a before/after memray comparison with concrete peak-RSS numbers is recorded, and either a
      shipped optimization or an explicit "no safe tuning knob helped enough" finding is recorded. Source:
      `issues/tradfi_backfill_oom_remediation_2026_06_24.md` (P3, the "un-released pyarrow frame" half of its own
      hypothesis).

Both todos are independent (different concern — investigation vs. code change) and touch disjoint files where they
overlap in repo (todo 1 makes no code edits); no `sequential`/`depends_on` gating needed — they may dispatch and run
concurrently.

## Deferred — needs its own dedicated design pass, not a todo here

**The structural options** (batch multiple low-volume symbols onto a shared `pq.ParquetWriter`, or cap concurrently-open
writers with eager flush/close) are NOT drafted as todos in this plan. Both would change `PartitionedTickWriter`'s
one-file-per-symbol GCS output contract that BigQuery external tables and the manifest's per-symbol shard atom currently
depend on, and the class's own docstring records that today's per-instrument split was adopted specifically to fix an
EARLIER OOM caused by the opposite (one shared file for everything) — so "batch onto a shared writer" is a reversion
with real prior-incident weight behind it, not a neutral tradeoff. If todo 2 finds the low-risk tuning insufficient
(worst-case peak RSS still threatens the current machine ceiling), that finding is the trigger for a fresh,
separately-authored design pass — weighing the downstream-consumer impact of a file-layout change against the VM-cost
savings of reverting to `e2-standard-4` — not something to guess at under this plan's existing todos. **Not required to
unblock regardless**: per the source issue's own text, the current `e2-highmem-4` (subsequently further bumped to
`e2-highmem-16` per `_tradfi-ohlcv-launcher-lib.sh`) machine bump already gives the fleet its practical OOM margin; this
whole plan is a VM-cost/engineering-debt optimization, not a correctness or stability blocker.

## Codex SSOTs

`/codex/02-data/tradfi-databento-sourcing-ssot.md` (todo 1's real Databento fetch),
`/codex/05-infrastructure/ vm-launcher-runbook.md` § heavy-compute-on-shared-host (todo 1's memory-bounding obligation).
No new durable contract is created by this plan — it is a bounded code-level optimization, not an architecture change.
