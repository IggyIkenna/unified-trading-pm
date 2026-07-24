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
status: superseded
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

> 🔴 **SUPERSEDED (2026-07-16, operator ruling, verbatim):** "kill drift entirely from our whole system it's pointless —
> Jupiter is the main one let's just use that. kill all other solana perp dex's. uac, code, adaptors, manifest, gcs,
> everything. no instruments no mvp nothing." The DRIFT venue this doc's finding concerns has been **removed entirely**
> (Drift was hacked ~$280M on 2026-04-01, rebranded to Velocity DEX 2026-07-01, now a ~2-week-old private beta with ~$0
> listed TVL) — all Solana perp DEXes are dropped except Jupiter (not integrated). This doc's finding/fix is now moot;
> kept for historical record only. SSOT for the removal: `/codex/04-architecture/solana-defi-coverage.md` (tombstone
> banner).

# Drift V2 Helius day-backfill OOM on a program-wide sig-index day (2026-07-15)

> **🔴 2026-07-15 (data_engineering slot-10): the P2 investigation below found something bigger than the todo asked.**
> The whole Helius sig-index/day-backfill path this doc is about (`mtds-solana-drift-backfill` +
> `mtds-drift-sig-walker-*` fleet) was declared **OBSOLETE** and **NOT on any critical path** by
> `/codex/04-architecture/drift-v2-data-sources.md` on **2026-06-01** — a full month before the
> `mvp_backfill_defi_onchain_v10` DRIFT-perp-funding saga (2026-06-29 → present) even started. A fully-built, tested,
> per-market replacement (`DriftV2HistoricalIngester` / `backfill_drift_v2_historical.py`, shipped
> `market-tick-data-service@0f70f376` 2026-06-01) already exists in the repo but was **never wired into any VM
> launcher** — the launcher actually in use (`launch-mtds-solana-drift-backfill-vm.sh`) still routes through the legacy
> `solana_defi_handler.py` Helius path. See "Investigation: should the sig index be per-market?" below. **NOTIFIED main
> via `POST /api/agents/by-role/main/message` this session** — this is a data-correctness/cost/SSOT-contradiction
> finding per CLAUDE.md governance rules, not something a single P2 investigation task should resolve unilaterally (it
> implies killing/not-relaunching a multi-VM SPOT fleet that's been running for ~a month of sessions).
>
> **🟢 RETIRED 2026-07-16 (data_engineering slot-15): migration to Velocity complete — the Helius sig-walker path this
> whole doc is about is now formally retired, not just under investigation.** All of main's sequencing
> (`issues/drift_helius_path_obsolete_2026_07_15.md`) has landed: the `mtds-drift-sig-walker-*` fleet is stopped and
> blocked from auto-relaunch (`deployment-service@46d6492`); `mtds-solana-drift-backfill` is re-routed to
> `backfill_drift_v2_historical.py` (Velocity Data API, e2-highmem-8, `deployment-service@ee859e4`) and launched at
> scale over the `2025-01-15`–`2025-12-23` gap; the DRIFT manifest registry gap for `perp_trades` is code-fixed
> (`unified-api-contracts@5fd781c7`). The streaming-fix (P1), per-market investigation (P2), zombie-VM CLI monitor (P2),
> and relaunch (P3) todos below remain accurate as the historical incident record — the zombie-VM monitor is a
> permanent, protocol-agnostic tool (not superseded by the Velocity migration), and the relaunch todo is already closed
> as superseded (slot-13). No further Helius-path work is expected on DRIFT; new gaps route through Velocity. Full
> migration record: `issues/drift_helius_path_obsolete_2026_07_15.md` (that doc is the migration SSOT — this doc stays
> the incident post-mortem, not duplicated further here).

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
- [x] ✅ [DATA] P2. Investigate whether the DRIFT V2 sig index should be built/queryable per-market (or
      per-instruction-type) instead of program-wide, so a single-market backfill run doesn't resolve + mislabel the
      whole program's daily activity. Confirm with whoever owns the `data_quality="helius_v2_signatures_only"` decision
      whether cross-market mislabeling is an already-accepted limitation or a fresh defect worth flagging separately.
      (repo: market-tick-data-service) — **INVESTIGATED 2026-07-15 (data_engineering slot-10). Answer: no, it should not
      be rebuilt per-market — the whole sig-index/Helius approach should very likely be RETIRED, not repaired.**
      Findings: 1. **The Drift V2 program has no per-market signature-scoping mechanism to build the index against in
      the first place.** `getSignaturesForAddress` (used by `build_drift_v2_sig_index.py`) only accepts ONE address —
      the program's — and Drift V2 markets are distinguished by instruction-level account args, not separate program
      addresses/PDAs walkable the same way. A genuinely per-market Helius-RPC-walked index isn't a small tweak; it would
      need full instruction decoding (a Drift V2 IDL decoder, which `_parse_helius_batch`'s own
      `data_quality="helius_v2_signatures_only"` flag already documents as NOT being available on this path). 2. **That
      decoder/per-market gap is moot — a per-market replacement already exists and is already shipped.**
      `/codex/04-architecture/drift-v2-data-sources.md` (`status: current`, created 2026-06-01) is the codex SSOT for
      Drift V2 ingestion and states plainly: the Helius sig-walking path is **"OBSOLETE for Drift V2 historical needs"**
      and **"REMAINS in the MTDS repo as cold infrastructure ... but is NOT on any critical path"**. The replacement —
      Drift's own Velocity Data API (`data.api.drift.trade`) — exposes genuinely **per-market** endpoints
      (`/market/{symbol}/fundingRates/{Y}/{M}/{D}`, `/market/{symbol}/trades/{Y}/{M}/{D}`) with **full historical
      coverage confirmed back to 2024-06-01, "zero gap"** at the free tier — including the exact crashed date,
      2025-01-09 (doc's own coverage table: "2025-01-08 → ~2026-04-01: Velocity API per-day endpoints (free tier covers
      this fully)"). This is inherently per-market by construction — no program-wide resolution, no mislabeling, no OOM
      risk, no Helius spend at all. 3. **The replacement is fully implemented, tested, and already in the repo — just
      never wired into the actual backfill VM.** `market_tick_data_service/cli/handlers/drift_v2_historical_handler.py`
      (`DriftV2HistoricalIngester`) + `market_tick_data_service/scripts/backfill_drift_v2_historical.py` (CLI, supports
      `--markets`/`--start`/`--end`/`--data-types funding,trades` + `--live --continuous` for the live=batch hard rule)
      shipped `market-tick-data-service@0f70f376` (2026-06-01,
      `feat(mtds): DriftV2HistoricalIngester via        data.api.drift.trade Velocity Data API — replaces Helius sig-index path for funding + trades`),
      with 12 unit tests (`tests/unit/test_drift_v2_historical_handler.py`). Its own docstring documents the intended
      VM-routing mechanism: generic `VM_TASK=mdps-backfill` + `VM_BACKFILL_CMD` metadata (already a real, working route
      in `deployment-service/scripts/vm/setup-data-pipeline-vm.sh` line ~1243, used by other backfills). **But no
      `launch-*.sh` script actually invokes it for Drift.** The VM that's been crashing (`mtds-solana-drift-backfill`,
      launched by `launch-mtds-solana-drift-backfill-vm.sh`) sets `VM_TASK=solana-drift-backfill`, which
      `setup-data-pipeline-vm.sh` line ~1410 explicitly routes to `solana_defi_handler.py`'s legacy
      `_backfill_drift_s3_date`/`_backfill_drift_helius_date` — the same OBSOLETE path the codex doc names — via a
      comment citing a DIFFERENT, older ruling ("Bug-D-prime fix 2026-05-31 … PerpFundingHandler has no \_collect_drift
      dispatch") that predates and is superseded by the 2026-06-01 Velocity API doc, but was never updated to reflect
      it. 4. **Cross-market mislabeling verdict**: not really an "accepted limitation" in the sense of a deliberate
      data-quality tradeoff someone signed off on — `data_quality="helius_v2_signatures_only"` is a self-documenting
      degraded-mode flag on what the codex doc already calls cold/non-critical-path infrastructure. The real defect
      isn't the mislabeling itself; it's that production has been running (and OOM-crashing on) deprecated
      infrastructure for six weeks while a correct, already-shipped, per-market replacement sat unused. 5. **Scale of
      the current-path cost**: per the v10 plan's 2026-07-14 G1.5 entry, closing the sig-index's ~11-month unindexed gap
      (2025-01-15 → 2025-12-23) via 2 parallel Helius sig-walker SPOT VMs is estimated at **1.7-9 days** of wall-clock
      on a Helius API key **already observed hard-throttling** (persistent 429s on manual single-RPC probes) — before
      the actual per-day Helius batch-resolve backfill (this doc's OOM incident) even runs. All of that cost may be
      unnecessary if DRIFT perp_funding is instead backfilled via the Velocity API path, which needs no sig index, no
      Helius key, and no per-day resolution step at all. **This is filed as a finding, not fixed here** — my assigned
      task was investigation-only (P2, 1h estimate); the actual fix (stop/don't-relaunch the Helius sig-walker fleet,
      point `mtds-solana-drift-backfill` — or a new launcher — at `backfill_drift_v2_historical.py` instead, verify
      Velocity API coverage/rate limits at production scale, and reconcile the manifest's
      `attempted_failed`/`expected_unattempted` DRIFT perp_funding cells against whichever path is authoritative) is
      real, multi-repo (`market-tick-data-service` + `deployment-service` + manifest state) work that touches a live
      multi-VM SPOT fleet an operator already made a throughput-economics call about on 2026-07-14 — it needs an
      explicit operator/main ruling, not a unilateral P2-task fix. See the new P0 todo below + the banner at the top of
      this doc. NOTIFIED main via `POST /api/agents/by-role/main/message` this session.

- [x] ✅ [DATA] P0. **RULED 2026-07-15 (data_engineering slot-2): option A confirmed by main (`/blocked` `BLK-ba6c367c`,
      consistent with `BLK-5d122841`/`BLK-6067d459`) — migrate to Velocity API.** Verify-first step done: ran the real
      ingester against production, found + fixed a real `pipeline_mode` shard-atom-identity bug
      (`market-tick-data-service@1bd507b4`), confirmed correct rows land at the correct path post-fix. Remaining
      sequencing (stop the Helius fleet, wire the launcher, reconcile the manifest) is tracked in the new consolidated
      doc per main's instruction: `issues/drift_helius_path_obsolete_2026_07_15.md` — see it for full detail, not
      duplicated here. **NEW 2026-07-15 (data_engineering slot-10), operator/main ruling needed**: decide whether to (a)
      abandon the Helius sig-index/day-backfill path for DRIFT `perp_funding` entirely and switch to
      `backfill_drift_v2_historical.py` (Velocity Data API, per-market, already shipped `mtds@0f70f376`, zero Helius
      spend, documented "zero gap" coverage back to 2024-06-01 per `/codex/04-architecture/drift-v2-data-sources.md`),
      stopping/not-relaunching the `mtds-drift-sig-walker-*` fleet and re-routing `mtds-solana-drift-backfill` (or a new
      launcher) to the Velocity path; or (b) there's a reason (rate limits, data-shape mismatch, a gap the codex doc
      doesn't know about) the team already implicitly rejected the Velocity path for this specific backfill and kept
      building the Helius sig-walker fleet instead, in which case that reason should be written down (codex doc updated
      / this doc closed as "already considered and rejected, here's why") so the next 15 sessions don't re-discover the
      same question. Before ruling, verify Velocity API coverage holds at the actual backfill's date range/volume
      (spot-check a few historically-busy days, confirm rate limits, confirm the `perp_trades` CSV format parses cleanly
      at the observed volume) — the codex doc's "zero gap" claim is from 2026-06-01 and hasn't been re-validated against
      this specific incident's dates. If (a): reconcile the DRIFT `perp_funding` manifest cells currently
      `attempted_failed`/`expected_unattempted` under the old path once the new path starts capturing them. (repos:
      market-tick-data-service, deployment-service, instruments-service for manifest reconciliation) — **PRE-RULING
      VERIFICATION DONE 2026-07-15 (data_engineering slot-2), decision still pending operator/main.** Live-probed
      `https://data.api.drift.trade` (no code changes, read-only curl + pandas parse, no ruling executed) against the
      actual backfill's real date range, not just the doc's original 2026-06-01 probe dates: 1. **Funding
      (`/market/SOL-PERP/fundingRates/{Y}/{M}/{D}`)** — exactly 24 rows/day, `meta.totalPages=1`, across 6 spot-checked
      dates spanning the whole incident: 2025-01-09 (the OOM-crash date), 2025-01-15 (gap lower bound per this plan's
      G1.5), 2025-12-23 (gap upper bound / the walker's single busiest day, see #2), 2024-08-05, 2025-02-03, 2025-11-21.
      All 200s, all 24 records. Matches the codex doc + handler docstring exactly. 2. **Trades volume is the strongest
      evidence for (a).** `plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md` line 1085 logs the Helius
      sig-walker's **actual observed cost** for 2025-12-23: **1,720,013 program-wide sigs, 17,207 batches, 200 minutes
      of wall-clock** on that one day alone. Paginating the SAME date's Velocity API trades endpoint
      (`/market/SOL-PERP/trades/2025/12/23?format=csv`, 5 pages) returns **20,290 actual SOL-PERP trades — an ~85x
      reduction**, confirming the vast majority of the program-wide sig volume the walker choked on is genuinely
      unrelated-market/instruction-type noise, not SOL-PERP activity the Velocity path would miss. 2025-01-09 (the crash
      date) similarly resolved to 17,219 trades (4 pages) via Velocity vs. the 1,209,478 program-wide sigs that
      OOM-killed the VM. Both day volumes are trivially in-memory-tractable (no chunking needed at this scale, unlike
      the Helius path's chunked-resolution fix). 3. **CSV parses cleanly at observed volume**: `pandas.read_csv` on a
      5,000-row page — 34 columns, 0 nulls in `ts`, all 34 CSV columns present that day are covered 1:1 by
      `DriftV2HistoricalIngester._TRADES_RAW_TO_CANONICAL` (no silent column drops at this row count/shape). 4. **No
      rate-limiting observed**: 10 concurrent funding-endpoint requests all returned `200` (no `429`s) — the codex doc's
      "rate limit: unknown/unprobed" note can be updated to "not observed under light burst load; production backfill
      should still add 429 backoff defensively since sustained high-QPS wasn't tested." 5. **Coverage boundary
      re-confirmed, with a caveat**: 2026-03-25 still returns 24 funding rows; 2026-06-01 returns `totalRecords=0`.
      Consistent with the doc's "~2026-04-01 → present: lags ~2 months" — but today is 2026-07-15, so the live lag
      window is now wider than it was at the doc's 2026-06-01 writing; the live-mode endpoints
      (`/market/{symbol}/fundingRates` / `/trades` with no date suffix) would need to cover whatever the current gap is,
      not just the historical window — worth confirming at execution time, not re-verified further here (out of this
      todo's "historical day volume" scope). **Net**: verification did not surface any reason to prefer (b) — Velocity
      API coverage, format, and rate-limit behavior all hold at the actual incident's dates/volumes, and the trade-count
      comparison on the walker's own logged busiest day is a strong quantitative case for (a). The actual (a)/(b) call —
      which means stopping/not-relaunching a live multi-VM SPOT fleet — is unchanged as an explicit operator/main
      decision, not executed by this verification pass. Posted `/blocked` from slot-2 with this evidence + a
      recommendation for (a).
- [x] ✅ [INFRA] P2. The zombie-VM blind spot (RUNNING instance, dead worker process, ~4h44m undetected) suggests the VM
      roster + run.log-tail monitoring convention used across this plan's many "-003" check-ins should add a
      log-staleness check (e.g. flag a VM whose `run.log` hasn't advanced in >30 min while still `RUNNING`) rather than
      relying on an agent noticing a `TERMINATED` status change on the next dispatch. (repo: deployment-service or
      wherever the VM-launcher/observability runbook lives — /codex/05-infrastructure/deployment-observability.md) —
      deployment-service@c56463b. Added
      `python -m deployment_service.data_pipeline_monitors.check_vm_cli --vm-name     <VM>` (DP-VM-006): an ad-hoc,
      self-contained, on-demand CLI that reuses the SAME tested `heartbeat_stall_watcher.classify_vm_liveness` the
      periodic Cloud Run fleet sweep uses (via `check_vm.py`), so a manual check-in gets a measured ALIVE/STALL verdict
      (sidecar-heartbeat + run.log-frozen signals, exit code 1 on STALL/EVENT_LOOP_STARVED) instead of an agent
      eyeballing raw timestamps. Never alerts or auto-kills (dry_run always True). Unit tests: `test_check_vm.py` (pure
      verdict logic incl. the OOM-zombie shape — frozen run.log, no sidecar/shard-mtime) + `test_check_vm_cli.py` (CLI
      wiring). Full `quality-gates.sh` green (2684 passed).
- [x] ✅ [DATA] P3. Once the streaming fix lands, relaunch `mtds-solana-drift-backfill` (same launcher args, `--resume`
      semantics) to continue past 2025-01-09 — do NOT relaunch with today's unfixed code, since the identical crash will
      very likely recur on the same day. (repo: deployment-service launcher + market-tick-data-service) — **⚠️
      2026-07-15 (data_engineering slot-10): this todo is now GATED by the new P0 todo above.** The
      streaming/chunked-resolution fix already landed (see `solana_defi_drift_helius.py` module docstring
      "Chunked-resolution OOM fix"), so the OOM itself is mitigated — but relaunching this VM at all means continuing to
      invest in the path the new P0 finding says may be obsolete. Do not relaunch until the P0 ruling lands. — **CLOSED
      AS SUPERSEDED 2026-07-15T23:09-23:33Z (data_engineering slot-13).** Dispatched to this exact todo and fresh-pulled
      `unified-trading-pm` at ~23:08Z — **before** slot-10's 23:12:03Z commit landed the P0-gate note above, so my
      pulled copy of this doc still showed the plain unchecked P3 todo with no gate. Executed it literally: rebuilt the
      4 core tarballs (`create-code-tarballs.sh`, no `--asset-group`) after confirming the deployed `mtds-code.tar.gz`
      was pinned to `545ce50b` — an ancestor of, and ~4 minutes older than, the streaming fix
      `market-tick-data-service@1df45ce3` (the exact silent-stale-tarball trap `lc_verify_tarball_freshness` exists to
      catch); new tarball pinned `mtds-code@1df45ce3b6ab`. Deleted the stale `TERMINATED` VM and relaunched
      `mtds-solana-drift-backfill --start 2025-01-09 --end 2026-07-14` (same window as the original 2026-07-14 12:37Z
      launch per the v10 plan's G1.5 entry — no explicit `--resume` flag exists on this launcher; "resume" here is the
      shard-level manifest re-entry the per-day backfill already gets for free). Confirmed via fresh `run.log` (new
      deployment ID, `RESOURCE_SAMPLE` RSS flat at 552-557MiB through the sig-index parts-cache scan phase, vs. 14.1GB
      pre-fix) that the VM booted clean on the fixed code — did **not** get far enough to observe the fix actually
      resolving a busy day (still mid-scan) before the next event below. **Received a steering message from main
      mid-session** relaying the P0 ruling this todo's gate was waiting on: the Helius sig-index/day-backfill path is
      OBSOLETE (`/codex/04-architecture/drift-v2-data-sources.md`, current since 2026-06-01) — ruling is (a), switch to
      the Velocity Data API path; "if your sub-task depends on the sig-index/sig-walker, STOP investing further ...
      verify the Velocity path on a sample market-day first, then decommission." This task depends on it entirely.
      Independently re-verified before acting: `curl https://data.api.drift.trade/market/SOL-PERP/fundingRates/2025/1/9`
      → `200`, clean per-market SOL-PERP funding rows (not program-wide) for the exact crash date — matches slot-2's
      pre-ruling verification above. **Decommissioned**: deleted the just-relaunched `mtds-solana-drift-backfill` VM
      (`gcloud compute instances delete`, confirmed) rather than let it keep burning SPOT VM-hours resolving a path the
      ruling retires. **Net effect**: the todo's literal instruction (streaming-fix relaunch) was executed and verified
      OOM-free, but the underlying goal (draining DRIFT `perp_funding` via this VM) is now moot — future DRIFT
      `perp_funding` backfill routes through `backfill_drift_v2_historical.py` (Velocity path) instead, which is
      `mvp_backfill_defi_onchain_v10-005`'s scope (slot-2, already pivoting per main's message), not re-actioned here.
      Checkbox flipped to reflect the todo is CLOSED, not because the Helius path succeeded, but because it's now
      superseded and no further Helius-path relaunch should happen. No code changes this session beyond the tarball
      rebuild (no source diff — tarball packaging only); repos touched: `deployment-service` (tarball rebuild + VM
      launch/delete, no committed code change), `market-tick-data-service` (tarball packaging of the already-shipped
      `@1df45ce3`, no new commit).

## Progress Log

### 2026-07-15 — data_engineering slot-10: P2 investigation surfaces a bigger SSOT contradiction

Picked up the assigned P2 todo ("should the sig index be per-market?"). Read `build_drift_v2_sig_index.py` (confirmed:
walks `getSignaturesForAddress` on the Drift V2 PROGRAM address only, no per-market scoping mechanism available at the
RPC level) and `solana_defi_drift_helius.py`/`solana_defi_drift.py` (confirmed: `_parse_helius_batch` unconditionally
labels every resolved row with the CLI-supplied `market`, and the OOM streaming fix from todo P1 above has already
landed independently of this task). While tracing "whoever owns the `data_quality=helius_v2_signatures_only` decision"
per the todo's second half, found `/codex/04-architecture/drift-v2-data-sources.md` — a `status: current` codex SSOT
dated 2026-06-01 declaring the entire Helius sig-index path OBSOLETE and NOT on any critical path, superseded by Drift's
Velocity Data API (per-market, free, "zero gap" back to 2024-06-01). Confirmed the replacement
(`DriftV2HistoricalIngester`/`backfill_drift_v2_historical.py`) is fully implemented + tested
(`market-tick-data-service@0f70f376`, 12 unit tests) but never wired into any VM launcher —
`launch-mtds-solana-drift-backfill-vm.sh` still routes through the legacy Helius path via a stale 2026-05-31 comment
that predates and doesn't reference the 2026-06-01 replacement. Cross-checked against
`defi_perp_funding_mvp_scope_contradiction_2026_06_29.md` (the MVP-scope ruling history for this exact backfill) and the
v10 plan's 2026-07-14 G1.5 entries (the 2-VM parallel sig-walker fleet launch, 1.7-9 day drain estimate on an
already-throttled Helius key) — neither mentions the Velocity API alternative at all. Flipped the assigned P2 todo with
full findings, added a new `[DATA] P0` todo asking for an explicit operator/main ruling on whether to abandon the Helius
sig-walker fleet in favor of the Velocity path, gated the existing P3 relaunch todo on that ruling, and notified main
via `POST /api/agents/by-role/main/message` (data-correctness + cross-repo + SSOT-contradiction = a "big finding" per
CLAUDE.md governance rules, not something a single P2 task should resolve unilaterally given it implies
stopping/redirecting a live multi-VM SPOT fleet). No code changes this session — investigation + issue-doc closure only,
per the task's own scope (P2, 1h estimate, "Investigate whether...").

### 2026-07-15T23:09-23:33Z — data_engineering slot-13: executed the pre-gate P3 relaunch, then stopped + decommissioned on main's mid-session ruling

Dispatched straight to the P3 relaunch todo. Fresh-pulled `unified-trading-pm` at ~23:08Z, before slot-10's 23:12:03Z
commit landed the P0-gate note on this todo — so proceeded on a copy of this doc that still read as a plain actionable
P3 item. Rebuilt the 4 core VM tarballs (confirmed the deployed `mtds-code.tar.gz` was pinned `545ce50b`, an ancestor of
and ~4 minutes older than the streaming fix `market-tick-data-service@1df45ce3` — would have silently shipped the
pre-fix OOM code, the exact class of bug `lc_verify_tarball_freshness` exists to catch), deleted the stale `TERMINATED`
VM, and relaunched `mtds-solana-drift-backfill --start 2025-01-09 --end 2026-07-14` (same window as the original
launch). Watched the fresh `run.log`: new deployment ID, RSS flat 552-557MiB through the sig-index parts-cache scan (vs
14.1GB pre-fix) — confirmed the fixed code boots clean, but the VM hadn't yet reached actual day-resolution when a
steering message from main arrived mid-session relaying the P0 ruling: option (a), Helius path OBSOLETE, switch to
Velocity. Independently re-verified before acting further (`curl` to `/market/SOL-PERP/fundingRates/2025/1/9` → 200,
clean per-market rows for the exact crash date), then killed the background watcher and deleted the just-relaunched VM
rather than let it keep resolving a retired path. Folded the outcome into the P3 todo above (flipped,
closed-as-superseded, not claimed as a clean win). Did not pick up the Velocity-path re-implementation itself (`-005`,
already slot-2's scope per main's message). Repos touched: `deployment-service` (tarball rebuild + VM launch/delete
only, no source diff), `market-tick-data-service` (tarball packaging of the pre-existing `@1df45ce3`, no new commit this
session).
