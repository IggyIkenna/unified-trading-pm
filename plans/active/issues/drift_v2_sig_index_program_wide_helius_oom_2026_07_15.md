---
doc_type: issue
title:
  Drift V2 Helius day-backfill OOM-killed on a program-wide sig-index day (1.2M sigs vs ~700 assumed); VM sat
  RUNNING-but-dead undetected for ~4h44m
summary: >
  `mtds-solana-drift-backfill` (market=SOL-PERP) crashed silently (OOM, no exit log line) at ~2026-07-15T17:10-17:11Z
  while resolving date 2025-01-09. `_load_drift_v2_sig_index` returned 1,209,478 signatures for that single day — the
  persisted sig index is built at the DRIFT V2 PROGRAM level (every instruction touching the program address across
  every market), not scoped to one market, and there is no per-signature market filter anywhere in
  `_backfill_drift_helius_date`/`_resolve_helius_rows`. That handler's own docstring assumes ~167-700 sigs/day —
  observed volume was >1700x that. `_resolve_helius_rows` pre-materialises every 100-sig batch as a coroutine and only
  extends/returns `rows` after the WHOLE `asyncio.gather` completes, so peak memory scales with the day's total sig
  count regardless of the bounded concurrency semaphore. RSS climbed linearly from ~864MiB to ~14.1GB over 18 minutes on
  an e2-standard-4 (16GB) VM before the process died with no graceful shutdown line in `run.log`. The VM itself then
  stayed `RUNNING` (zombie — process dead, instance up) for ~4h44m, undetected by any of the ~15+ prior data_engineering
  sessions monitoring this exact task, until an unrelated automated reaper issued `compute.instances.stop` at
  21:54-21:55Z. Applied a safety-ceiling mitigation (`market-tick-data-service`, this session):
  `_backfill_drift_helius_date` now `record_failed`s any day whose sig-index window exceeds 50,000 sigs instead of
  attempting in-memory resolution, converting a silent OOM crash into a diagnosable `attempted_failed` shard. The deeper
  questions below (why is the index program-wide, is market-mislabeling already an accepted
  `data_quality="helius_v2_signatures_only"` limitation, and how to actually resolve high-volume days) are NOT resolved
  by the mitigation and need follow-up.
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [correctness, efficiency, oom, drift, sig-index, helius, gap-monitoring]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    issues/drift_v2_sig_index_parts_cache_full_download_2026_07_15.md,
  ]
created: 2026-07-15
parent_epic: defi_master
priority: P1
source: [mvp_backfill_defi_onchain_v10-003 verify-todo, data_engineering slot-10]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
locked_since:
---

# Drift V2 Helius day-backfill OOM on a program-wide sig-index day (2026-07-15)

## What I found

Dispatched to `mvp_backfill_defi_onchain_v10-003` ("Verify the DRIFT fleet drains") at 2026-07-15T22:26Z, ~5.5h after
the last check (slot-2, 17:00-17:25Z). VM roster (`gcloud compute instances list`, project `central-element-323112`):
`mtds-solana-drift-backfill` is **TERMINATED** (was RUNNING at every prior check). GCE audit log
(`gcloud logging read ... protoPayload.resourceName:"mtds-solana-drift-backfill"`) shows two `v1.compute.instances.stop`
calls at 21:54:30Z / 21:55:26Z by `unified-trading-sa@...` — a service-account-initiated stop, NOT a `preempted` system
event (ruled out SPOT preemption).

`run.log` (`gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-drift-backfill/run.log`, 198 lines total)
stops abruptly at **17:10:27Z** with no exit/shutdown line. The tail shows:

```
16:53:23,222 INFO Drift V2 sig index parts: metadata cache built (17082 parts across 3 prefixes)
16:53:23,686 INFO Loaded Drift V2 sig index (parts, filtered, 17082 parts...): 1209478 rows after dedup (1209478 before), window [1736380800, 1736467199]
16:53:23,784 INFO Drift Helius backfill: 1209478 sigs in window [2025-01-09, 2025-01-09] for SOL-PERP
```

followed by `RESOURCE_SAMPLE` lines showing `rss` climbing linearly and near-continuously: 864MiB (16:52:11) → 1130 →
1505 → 1888 → 2284 → 3048 → 3839 → 4617 → 5420 → 6238 → 7036 → 7816 → 8608 → 9379 → 10223 → 11061 → 11816 → 12647 →
13448 → **14127MiB (17:10:23)** — `mem%` reaching 94.7% on an `e2-standard-4` (16,384 MB, confirmed via
`gcloud compute machine-types describe`) — then silence. No `EXIT_STATUS` blob exists at the VM's log path (present for
genuinely-clean completions per prior sessions' convention). This is consistent with a Linux OOM-kill: no graceful
shutdown code path runs on OOM, so `VM_SHUTDOWN_ON_COMPLETION`'s self-delete/self-stop never fired — the instance sat
`RUNNING` with a dead worker process for ~4h44m until something else (a reaper, not identified further here) issued the
stop.

**Root cause of the OOM**: `_backfill_drift_helius_date`'s own docstring states "Per-day cost: 1 cache hit + N/100 batch
calls (N ~ 167-700 sigs/day -> 2-7 batch calls)". The observed 1,209,478 sigs for ONE day is >1700x that assumption.
Tracing why: the persisted sig index (`build_drift_v2_sig_index.py`) is built by walking `getSignaturesForAddress` on
the **DRIFT V2 PROGRAM address** — every instruction touching the program (trades, funding settlements, liquidations,
oracle cranks, across ALL markets) — not scoped to one market. Nowhere in `_backfill_drift_helius_date` /
`_resolve_helius_rows` / `_parse_helius_batch` is there a per-signature market filter; `_parse_helius_batch`
unconditionally sets `"symbol": market` on every parsed row using the CLI-provided market string, regardless of what the
underlying transaction actually concerns. So a single-market backfill run (`solana_defi_handler.process()` resolves
`market = getattr(args, "solana_drift_market", "SOL-PERP")` — one market, no market loop for this VM's invocation) still
resolves and labels the **entire program's** daily signature volume.

Independent of _why_ the count is 1.2M (data-index scope question below), the memory-bound mechanism is a real,
separately-fixable defect: `_resolve_helius_rows` (`solana_defi_drift_helius.py`) does
`batches = [target_sigs[i:i+100] for ...]` (pre-materialises ALL ~12,094 batch slices up front) then
`results = await asyncio.gather(*(_run_one(i, batch) for i, batch in enumerate(batches)))` — the `asyncio.Semaphore`
bounds how many batches are **in-flight over the network** concurrently, but `results`/`rows` are only extended/returned
after the **entire** `gather` resolves, so peak memory scales with the day's total sig count, not with the concurrency
bound. Verified the basic pyarrow `filters=` predicate-pushdown mechanism itself works correctly in isolation (a
synthetic 1000-row/1-window probe filtered to exactly 2 rows, pyarrow 23.0.1) — so this is NOT a broken parquet filter;
the day-window filter genuinely returns 1.2M signatures because the underlying index has that many DRIFT-V2-program-wide
entries for the day.

## Why it matters

1. **Reliability**: any day this busy (very plausible for 2025 — Drift is a heavily-used perp DEX, its program address
   gets touched by every trade/funding/liquidation/oracle-crank instruction across all markets) will OOM-crash the
   walker again, wasting VM-hours and delaying the whole DRIFT MVP backfill (currently the dominant blocker on the
   plan's `-003` gate: `perp_funding` `attempted_failed=321`, `expected_unattempted=81,724` as of the last `-002` gate
   run).
2. **Silent-crash blind spot**: this crash produced NO alert and NO log signal distinguishable from healthy activity
   until a human/agent happened to notice the VM had gone from RUNNING to TERMINATED — ~15+ prior sessions across many
   slots monitored this exact task over multiple days without catching it, because the standard "VM roster + run.log
   tail" check only samples point-in-time state. The zombie window (dead process, RUNNING instance) lasted ~4h44m.
3. **Possible data-quality question (not confirmed a NEW bug — may be an already-accepted limitation)**: because
   `_parse_helius_batch` labels every resolved signature with the CLI-supplied `market` regardless of the tx's actual
   content, and the sig index is program-wide, captured `perp_funding` rows for one market may include unrelated program
   activity. These rows already carry `data_quality="helius_v2_signatures_only"` specifically because the team knows
   this path can't fully decode market-specific content (no Drift V2 IDL decoder yet) — so this may be a long-accepted,
   flagged limitation rather than a fresh defect. Not re-litigated here; flagged for whoever picks up the todos below to
   confirm.

## Mitigation applied this session (market-tick-data-service)

Added `_MAX_HELIUS_DAY_SIGS = 50_000` ceiling in `solana_defi_drift.py`: `_backfill_drift_helius_date` now checks
`len(target_sigs)` immediately after loading the day-window-filtered index and, if it exceeds the ceiling, calls
`recorder.record_failed(...)` with a clear diagnostic reason and returns **before** touching the Helius API or
`_resolve_helius_rows` at all — no network calls, no per-batch memory growth. This converts a silent multi-GB OOM crash
into an honest, immediately-visible `attempted_failed` shard (never a silent zero — consistent with the honest-absence
discipline). Added a regression test
(`tests/unit/test_solana_defi_handler.py::TestBackfillDriftHelius::test_helius_day_sig_count_over_ceiling_records_failed_without_resolving`)
asserting `record_failed` fires, `record_captured`/`record_zero_rows` do NOT fire, and `session.post` is never called
(the safety valve trips before any Helius call). 50,000 was chosen as a conservative ceiling ~70x the documented
167-700/day expectation — generous headroom for a genuinely busy day without risking OOM at the observed growth rate.
This is a **stopgap**, not a fix for the underlying scale/scoping problem — days that legitimately exceed 50K
program-wide sigs will now fail cleanly instead of crashing, but still won't get their data captured until the proper
fix below lands.

## Recommended follow-up (NOT actioned here — needs its own scoped implementation pass)

- [x] ✅ [DATA] P1. Refactor `_resolve_helius_rows` to stream/chunk: process the day's `target_sigs` in bounded
      sub-chunks (e.g. 5,000-10,000 sigs), writing/flushing each chunk's resolved rows before starting the next, instead
      of materialising the whole day in one `asyncio.gather` + one final write. This is the real fix that lets
      high-volume days actually get captured (not just fail cleanly). (repo: market-tick-data-service) — **DONE
      `market-tick-data-service@1df45ce3`** (data_engineering slot-7, 2026-07-15T23:00-23:10Z): `_resolve_helius_rows`
      now processes batches in sequential chunks of `_HELIUS_RESOLVE_CHUNK_BATCHES=50` (5,000 sigs/chunk), parsing +
      discarding each chunk's raw Helius JSON before starting the next (peak memory holds one chunk's raw responses, not
      the whole day's), and short-circuits between chunks on first batch failure. **Scope note (partial vs. the todo's
      "writing/flushing" wording)**: this fixes the resolution-side OOM mechanism (the
      `asyncio.gather`-over-the-whole-day memory blowup) WITHOUT changing the write side — `_write_drift_helius_shard`
      still writes ONE parquet shard per (market, day) at the end, deliberately preserving the existing
      shard-atom-identity contract rather than risking a multi-file-per-day write (the workspace's
      manifest/shard-atom-identity rule flags that as needing its own careful review, not a drive-by change).
      `_MAX_HELIUS_DAY_SIGS=50_000` is UNCHANGED — this fix bounds peak memory within any day the ceiling already allows
      through (chunking + estimated per-row size puts even a full 50K-sig day at ~500MB-1GB peak, well under 16GB); it
      does NOT by itself unblock days that exceed the ceiling — that would need the write-side chunking too, left as a
      future follow-up if a day is ever observed hitting the ceiling with legitimate volume. 2 new regression tests
      (`test_helius_multi_chunk_resolves_across_chunks_and_concatenates_rows`,
      `test_helius_chunk_failure_aborts_before_next_chunk_starts`), full `quality-gates.sh` green (sentinel `229af3a2`),
      `--files`-scoped quickmerge.
- [ ] [DATA] P2. Investigate whether the DRIFT V2 sig index should be built/queryable per-market (or
      per-instruction-type) instead of program-wide, so a single-market backfill run doesn't resolve + mislabel the
      whole program's daily activity. Confirm with whoever owns the `data_quality="helius_v2_signatures_only"` decision
      whether cross-market mislabeling is an already-accepted limitation or a fresh defect worth flagging separately.
      (repo: market-tick-data-service)
- [ ] [INFRA] P2. The zombie-VM blind spot (RUNNING instance, dead worker process, ~4h44m undetected) suggests the VM
      roster + run.log-tail monitoring convention used across this plan's many "-003" check-ins should add a
      log-staleness check (e.g. flag a VM whose `run.log` hasn't advanced in >30 min while still `RUNNING`) rather than
      relying on an agent noticing a `TERMINATED` status change on the next dispatch. (repo: deployment-service or
      wherever the VM-launcher/observability runbook lives — codex/05-infrastructure/deployment-observability.md)
- [ ] [DATA] P3. Once the streaming fix lands, relaunch `mtds-solana-drift-backfill` (same launcher args, `--resume`
      semantics) to continue past 2025-01-09 — do NOT relaunch with today's unfixed code, since the identical crash will
      very likely recur on the same day. (repo: deployment-service launcher + market-tick-data-service)
