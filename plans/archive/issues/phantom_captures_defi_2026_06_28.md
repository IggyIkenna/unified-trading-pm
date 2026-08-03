---
doc_type: issue
title: Phantom captures — defi manifest (2026-06-28)
summary:
  219,529 phantom captures (10.5% of captured scope) in defi MTDS manifest — swaps_ohlcv_* dominant across Uniswap
  V3/V4, Balancer, SushiSwap. Major data integrity finding.
status:
  resolved # all 3 todos genuinely done: todo 2 verified + flipped 2026-07-27; todo 1 genuinely completed 2026-07-28
  # (slot-15, root cause diagnosed via git/commit archaeology, same evidence as
  # defi_satellite_ao_dispatch_batch1_2026_07_25 todo 52); todo 3 done 2026-07-26. The earlier "todo 1's [x] was FALSE"
  # note described a transient 2026-07-27 state that the 2026-07-28 completion superseded -- it is no longer true.
  # Unlocked + archived 2026-07-31 under the operator's [unlock-plan] ruling.
nature: process
asset_group: [defi]
stage: [meta]
repos: [market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [phantom, defi, manifest-hygiene, data-quality]
related: [mvp_backfill_defi_onchain_v10_2026_06_27]
created: 2026-06-28
parent_epic: observability_master
priority: P1
source: [reconcile_phantom_manifest_rows_all.py, mvp_catalogue_finalization_v10_2026_06_27.md (G3 phantom audit task)]
assigned_vm: NA
resolved_by:
  "reconciliation applied 2026-06-28 (run bj755413o, exit_code=0, 219,632 phantom rows flipped to attempted_failed);
  root cause diagnosed 2026-07-28 (slot-15) with the same evidence as defi_satellite_ao_dispatch_batch1_2026_07_25 todo
  52; current-writer confirmation 2026-07-26"
locked_by:
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    instruments-service/scripts/reconcile_phantom_manifest_rows_all.py,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-31
locked_since:
---

# Phantom captures — defi manifest (2026-06-28)

> **🗄️ ARCHIVED 2026-07-31 (operator-ruled locked-plan unlock + archive sweep, 2026-07-30 Q&A session)** — all 3 todos
> verified `[x]` done today; the `locked_by: live-defi-rollout` lock (a branch name, never a person) is cleared under
> the operator's explicit `[unlock-plan]` ruling covering all 7 fully-done locked docs. The history below is retained
> verbatim as the record — note the "todo 1's `[x]` was FALSE" line describes a **transient 2026-07-27 state that the
> 2026-07-28 (slot-15) completion superseded**; it is not a live caveat. Per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

> **⚠️ Historical note (2026-07-27 /plan-vintage-audit correction; UPDATED 2026-07-30)** — a 2026-07-27 pass verified
> todo 2 ("apply reconciliation") is genuinely done (2026-06-28T21:35:53Z, `bj755413o`, exit_code=0, 219,632 phantoms
> flipped, verified against `plans/archive/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md:754-762` +
> `plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md`'s banner) and flipped it. Todo 1's `[x]` was then found
> FALSE on 2026-07-27 (its "already covered by `defi_satellite_ao_dispatch_batch1_2026_07_25.md`" citation didn't hold
> up at the time — that plan's own copy of the root-cause todo was still unchecked) and reverted to open. **2026-07-28
> (slot-15): todo 1 was genuinely completed for real** (root cause diagnosed via git/commit archaeology — see Progress
> Log "2026-07-28 (slot-15)" entry) as part of the SAME dispatch that closed
> `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s own root-cause-diagnosis todo (todo 52 there) — both carry
> identical evidence. **All 3 todos in this doc are now `[x]` done.** Confirmed 2026-07-30
> (defi_satellite_ao_dispatch_batch1 finalize reconciliation pass): re-verified batch1 todo 52 is checked done with this
> same evidence before touching this doc, per the finalize plan's explicit instruction not to flip anything here without
> that confirmation. **The `[unlock-plan]` ask this paragraph was waiting on was granted by the operator on 2026-07-30**
> — lock cleared, `status` flipped to `resolved`, archived 2026-07-31 (see the banner above).

> Auto-filed by the G3 phantom-manifest audit (`reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run`)
> run during Phase-0 catalogue finalization. Found 219,529 `capture_status=captured` rows in the MTDS defi manifest
> (`market-data-tick-defi-prd-central-element-323112/_index/`) with no backing GCS parquet. These are NOT
> catalogue-shape (they are DeFi market-data records — swaps OHLCV, DEX pool swaps, gas fees, etc.) → issue doc per plan
> triage rule.

## What I found

Manifest: `gcp://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`

- Manifest rows total: 8,040,229
- Captured rows in scope: 2,089,059
- Unique (date, venue[, chain], hive-vocab) prefixes: 1,793,190
- **Real captures (parquet exists):** 1,869,530
- **Phantom captures (captured → no parquet):** 219,529 ← will flip to `attempted_failed` on `--apply`

Triage JSONL: `gs://central-element-323112-phantom-triage/triage_defi_20260628_023523.jsonl` (219,529 records)

Phantom distribution by data_type (all 14 shown):

| data_type         | phantom count |
| ----------------- | ------------- |
| swaps_ohlcv_1d    | 25,437        |
| swaps_ohlcv_4h    | 25,432        |
| swaps_ohlcv_15m   | 25,424        |
| swaps_ohlcv_1h    | 25,424        |
| swaps_ohlcv_1m    | 25,418        |
| swaps_ohlcv_15s   | 25,399        |
| swaps_ohlcv_5m    | 25,397        |
| dex_pool_swaps    | 20,586        |
| gas_fees          | 12,249        |
| liquidations      | 8,509         |
| derivative_ticker | 103           |
| perp_funding      | 92            |
| vault_share_price | 30            |
| trades            | 29            |
| **TOTAL**         | **219,529**   |

Phantom distribution by venue (top 14 shown):

| venue          | phantom count |
| -------------- | ------------- |
| UNISWAP_V4     | 69,573        |
| UNISWAP_V3     | 42,807        |
| BALANCER       | 31,967        |
| SUSHISWAP_V3   | 15,579        |
| PANCAKESWAP_V3 | 13,283        |
| ALCHEMY        | 12,249        |
| CURVE          | 10,492        |
| AAVE_V3        | 7,611         |
| SUSHISWAP      | 6,233         |
| CAMELOT_V3     | 4,965         |
| AERODROME_V3   | 3,618         |
| COMPOUND_V3    | 898           |
| ASTER          | 224           |
| MORPHOVAULTS   | 30            |

## Pattern analysis

The 7 `swaps_ohlcv_*` variants each have ~25,400 phantoms — nearly identical counts. This strongly suggests a
**systematic writer failure** (not individual shard failures): the manifest recorded captures but the OHLCV aggregation
writers never wrote the parquets. The near-uniform counts across all 7 time granularities (1m/5m/15m/15s/1h/4h/1d)
suggest the same set of (date, venue, pool_address) cells were affected.

UNISWAP_V4 (69,573) is the single largest venue — it was added to the DeFi universe recently; its writer may have logged
`captured` before actually writing parquets.

ALCHEMY (12,249 gas_fees) suggests the gas-fee writer had a similar issue (likely the same batch window).

## Why it matters

219,529 phantom rows (10.5% of captured scope) is a major data-correctness issue:

- The defi backfill plan's G0 gap analysis will count these as "captured" (not gaps) and skip them
- Without reconciliation, the defi backfill will leave these ~220k cells unbackfilled
- The defi backfill plan's G3 final verification includes its own phantom check — this will catch it, but applying the
  fix first avoids false starts

## Recommended decision

1. **Apply phantom reconciliation BEFORE defi backfill G0 gap analysis**:
   `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi` (no `--dry-run`, with
   `MANIFEST_PER_VM_SHARDS=true VM_NAME=defi-reconcile` per consolidator-SSOT). Reference triage JSONL:
   `gs://central-element-323112-phantom-triage/triage_defi_20260628_023523.jsonl`.
2. **Diagnose root cause**: check DeFi writer logs for the UNISWAP_V4/swaps_ohlcv batch window when these captures were
   logged. The uniform 25,400 count across all 7 granularities is a smoking gun for a batch that recorded manifest
   entries but crashed before writing.
3. **After reconcile**: re-run `--dry-run` to confirm 0 phantoms, then proceed with defi backfill G0.

Cold-start context: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` +
`/codex/05-infrastructure/manifest-consolidator-ssot.md` + `/codex/02-data/availability-manifest-and-data-status.md` +
`/codex/02-data/defi-canonical-naming-ssot.md`.

## Todos

- [x] ✅ [SCRIPT] P1. Diagnose defi phantom root cause: uniform ~25,400 counts across 7 swaps_ohlcv_* granularities +
      UNISWAP_V4 dominance suggest a single batch writer failure. Check DeFi OHLCV writer logs for affected window.
      Repo: `market-tick-data-service`. **CORRECTED 2026-07-27**: reverted from a false `[x]` — the prior "already
      covered by `defi_satellite_ao_dispatch_batch1_2026_07_25.md` + this doc's own 2026-07-26 Progress Log entry" claim
      does not hold: the Progress Log entry below explicitly scopes itself to a DIFFERENT question (current-writer
      write-then-record safety, matching todo 3) and says "Todos 1+2 above... remain open"; `batch1`'s own copy of this
      exact todo (status: active) is still unchecked with no completion evidence. Genuinely open — tracked at
      `/plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md`. — **DONE 2026-07-28 (slot-15,
      data_engineering)**: root cause diagnosed via git/commit archaeology (no writer-fix required — see Progress Log
      "2026-07-28 (slot-15)" entry below for full evidence). Repo scope corrected: `swaps_ohlcv_*` (81% of the phantom
      set) is written by `market-data-processing-service` (MDPS), not MTDS — same repo-scoping error the 2026-07-26
      entry below already flagged for `dex_pool_swaps`/`gas_fees`.
- [x] ✅ [SCRIPT] P1. Apply defi phantom reconciliation (219,529 rows → `attempted_failed`) BEFORE defi backfill G0. Run
      `reconcile_phantom_manifest_rows_all.py --asset-group defi` (no dry-run) with `MANIFEST_PER_VM_SHARDS=true`.
      Verify with `--dry-run` post-apply confirms 0 phantoms. Repo: `instruments-service`. — **APPLY COMPLETE, verified
      2026-07-27**: `plans/archive/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md:754-762` records the
      2026-06-28T21:35:53Z apply run (`bj755413o`, exit_code=0, 219,632 phantoms flipped `captured→attempted_failed`, 0
      unphantomed — idempotent run confirmed), independently corroborated by
      `plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md:105-110`'s own banner (same timestamp/counts). Both
      citations re-read + confirmed real this session.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-26 (worker, slot 6).** Confirmed against the CURRENT writer code (the original
      batch OHLCV writer implicated in this finding was RETIRED 2026-07-18/19 for a per-instrument writer
      re-architecture, `market-tick-data-service@4ca2640d` — this re-checks the NEW path, not the retired one). Full
      writeup in Progress Log below. Verdict: SAFE across every active writer for `dex_pool_swaps`/`gas_fees` —
      `record_captured` fires only after a confirmed-successful parquet upload, in every handler checked. No new issue
      doc needed; nothing to fix. Repo: `market-tick-data-service`.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid - ARCHIVE-eligible by content (all 3 todos now done, incl. todo 1
  completed 2026-07-28) but locked_by: live-defi-rollout blocks archival — needs [unlock-plan], never autonomous

- **2026-07-28 (slot-15, `data_engineering`, root-cause diagnosis, todo 1):** Read-only git/commit archaeology across
  `market-tick-data-service`, `market-data-processing-service` (MDPS) and `unified-trading-library` (UTL). **Repo
  correction**: `swaps_ohlcv_*` (177,931 of 219,529 phantoms, 81%) is written by MDPS's candle writer, not MTDS —
  `grep -rl swaps_ohlcv --include=*.py` in MTDS returns zero production writer hits (only a rebuild-script helper and a
  test); MDPS's `market_data_processing_service/app/adapters/defi/swap_adapter.py` +
  `app/core/canonical_writer{,_streaming}.py` are the real implicated writers. This mirrors the exact repo-scoping error
  the 2026-07-26 entry below already flagged for `dex_pool_swaps`/`gas_fees`.
  - **Writer-ordering hypothesis RULED OUT for both MDPS write paths, at the exact commit that was HEAD on the incident
    date.** `git log -1 --before="2026-06-28T23:59:59"` on MDPS resolves to `afccc71f` (2026-06-28 22:02 UTC). At that
    commit: (1) the eager path `write_candle_parquet` (`canonical_writer.py:500,520`) calls
    `bytes_written = _upload_local_to_gcs(...)` BEFORE `manifest_writer.record_captured(...)` — upload-then-record,
    correct; (2) the streaming (chain-bundle) path `close_candle_streaming_writer`
    (`canonical_writer_streaming.py:465,477`, split out of `canonical_writer.py` 2026-06-11 "pure code motion, no
    behaviour change" per its own docstring — i.e. this ordering predates the split too) has the identical
    upload-then-record order, documented explicitly in its own docstring ("`_upload_local_to_gcs` → `record_captured`").
    No writer-side inversion bug exists in either path as of the incident date. (Adjacent but NOT the mechanism: MDPS
    `93a3680`, 2026-07-27, fixed the streaming path silently swallowing a manifest-write _failure_ — but that produces
    the OPPOSITE symptom, a captured shard with NO manifest row at all, not a phantom row with no parquet; ruled out.)
  - No evidence of a deleted/retired predecessor "batch OHLCV writer" module: `git log --diff-filter=D` for
    `*defi*ohlcv*`/`*batch*defi*`/`*swap*` patterns in MDPS returns zero hits: the writer family has evolved
    continuously since 2026-04-18 (`c1cb73c`), with the v4→v5 manifest-verb migration (`afdb754`, 2026-05-10) already
    establishing the current record-on-confirmed-write-success contract well before the incident.
  - **Strongest evidence-based hypothesis: the pre-fix UTL manifest-consolidator column-misalignment bug**, fixed by
    `unified-trading-library@6b0520a6` ("fix(manifest_consolidator): project shard columns in canonical order before
    UNION ALL", landed **2026-06-27 08:24 UTC — ~18h before** the phantom audit's triage file
    (`triage_defi_20260628_023523.jsonl`, 2026-06-28 02:35 UTC). Per the commit's own description: per-VM manifest
    shards had the same 40 column NAMES as canonical but in a DIFFERENT positional order; the pre-fix incremental merge
    built `shard_scan` with `SELECT *` (shard order) then did a plain positional `UNION ALL` against `canon.*`
    (canonical order) — so "each shard value landed in the WRONG canonical column slot (e.g., capture_status ended up in
    job_id, pipeline_mode in error_reason, etc.)". The commit's own "Manifested" note cites a confirmed instance on
    tradfi instruments-service VMs (~11,600 misaligned rows, repaired separately) — **the SAME shared
    `_duckdb_consolidate_and_write`/`shard_scan` code path is used generically for every per-AG bucket**, confirmed via
    `market-tick-data-service/market_tick_data_service/scripts/rebuild_defi_manifest.py:682` invoking
    `unified_trading_library.manifest_consolidator` for the defi bucket by the same `consolidate(bucket, ...)` entry
    point. A column-misalignment merge would (a) plausibly manufacture spurious `capture_status="captured"` values on
    cells whose real parquet was never written, and (b) do so in **shard-wide, systematically uniform batches** — which
    is exactly the "near-uniform ~25,400 phantom count across all 7 time granularities" pattern the original audit
    flagged as "a smoking gun for a batch that recorded manifest entries but crashed before writing" (the audit's own
    speculation was about a writer, but a column-misaligned merge batch produces the identical uniform-batch fingerprint
    without any writer bug). The fix landed ~18h before the audit, so it stops FUTURE misalignment but does not
    retroactively repair rows already merged wrong by an earlier (pre-fix) incremental consolidation pass — those would
    still read `captured` with no real backing parquet on the 2026-06-28 audit, consistent with what was found.
    (`dd17ce23`, the sibling fix landed 2026-06-27 09:46 UTC for stale blank-`capture_status` rows re-accreting, is a
    related but structurally different bug — blank-status carry-forward, not column misalignment producing false
    `captured` — considered and set aside as a weaker match.)
  - **Caveat / confidence**: this is the best-evidenced hypothesis from available git history, not a certainty proven
    against the actual incident-window run — no VM run logs for the specific 2026-06-28-detected consolidation pass(es)
    were locatable in this session (no GCS log-fetching was attempted; per this todo's own "Done when (b)" allowance,
    and given both writer paths are independently cleared, retroactive confirmation via logs is not pursued further
    here). If a future investigation has GCS log access to the pre-2026-06-27 consolidation runs for the defi bucket,
    confirming column-misaligned rows in that window would upgrade this from hypothesis to proof.
  - **No code fix required by this todo** — todo 2 (phantom reconciliation, already applied 2026-06-28) and the
    already-shipped consolidator fixes (`6b0520a6`/`dd17ce23`) together close the loop: the generating bug is fixed, and
    the corrupted rows it left behind are reconciled. Closing this todo as a documented root-cause diagnosis per the
    batch1 plan's own "Done when (a)" criterion.

- 2026-07-27 (`/plan-vintage-audit` June-2026 sweep, §2 execution): verified + flipped todo 2 (apply reconciliation) —
  genuinely complete, 2026-06-28T21:35:53Z (`bj755413o`, exit_code=0, 219,632 phantoms flipped), evidence re-read from
  `plans/archive/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md:754-762` +
  `plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md`'s banner. While reading the doc end-to-end (not just
  checkbox count), found todo 1's `[x]` was FALSE — its own Progress Log entry below (2026-07-26) explicitly disclaims
  covering it ("Todos 1+2 above... remain open"), and the plan it cited as coverage
  (`defi_satellite_ao_dispatch_batch1_2026_07_25.md`, status: active) still carries the identical root-cause-diagnosis
  todo unchecked with zero completion evidence. Reverted todo 1 to `[ ]`. **Did NOT archive this doc** — 1 genuine open
  item remains (already has a home: batch1's own todo). Flagged per CLAUDE.md's findings-triage HARD RULE.
- 2026-07-26 (worker, slot 6, `defi_satellite_ao_dispatch_batch2-021`): re-verified the write-then-record ordering (the
  exact bug class suspected here) across every active DeFi writer handling `dex_pool_swaps`/`gas_fees` in
  `market-tick-data-service` (repo scope per this doc + the batch2 todo). `swaps_ohlcv_*` is out of scope for this repo
  — it is written by market-data-processing-service (MDPS), not MTDS; not re-checked here.
  - `write_defi_rows` (`market_interface/adapters/defi/canonical_write.py:158-351`) — never touches GCS or calls
    `record_captured`; pure sharding helper. Not itself a risk point.
  - `evm_defi_collectors.py::_write_and_upload` (`cli/handlers/evm_defi_collectors.py:42-85`) — SAFE.
    `storage.upload_bytes` (line 81) runs per-shard before the counts are returned; `record_captured` (line 636) fires
    only from the `try` block whose exception path calls `record_failed` (line 597) instead.
  - `dex_swaps_handler.py` (`dex_pool_swaps`) — SAFE. `_write_swap_shard` (line 484-528) uploads every shard (line 525)
    before building the row-count map; `_collect_one_shard` (line 271-315) only reaches `record_captured`
    (`_dex_swaps_queries.py:154`) after that succeeds — an upload exception routes to `record_failed` (line 307)
    instead.
  - `gas_fee_handler.py` (`gas_fees`) — SAFE across all 4 write paths (EVM date-shard, Solana historical, Solana live,
    BTC); each uploads (e.g. line 770) inside the `try:` (line 330) that `record_captured` depends on (line 332); an
    exception routes to `record_failed` (line 303) instead.
  - Live WS streaming path (`live/websocket_runner.py` → `curve_defi_ws.py`/`dex_swap_uniswap_v3_ws.py`) — SAFE.
    `_persist_window_to_sink` (line 640-688) calls `record_captured` (line 676) only using the `blob_path` returned by a
    successful `flush` (line 651); `LiveWebsocketTickSink.flush` (line 164-190) has no swallowing try/except around
    `upload_bytes` (line 189), so a failure raises and `record_captured` is unreachable for that window.
  - Shared foundation: `GCPCloudProvider.upload_bytes` (unified-trading-library
    `cloud_interface/providers/gcp.py:230-246`) has no swallowing try/except — GCS SDK errors propagate as real
    exceptions, which every handler above relies on. `DefiManifestRecorder.record_captured`
    (`cli/handlers/_defi_manifest.py:153`) is a thin per-row `ManifestWriter` shim — no batch-level "mark all captured"
    shortcut exists that could decouple it from an individual write's success.
  - **Verdict: the 2026-06-28 phantom-capture ordering bug is CLOSED for the current writer generation** — every active
    `dex_pool_swaps`/`gas_fees` handler correctly gates `record_captured` on a confirmed prior write. No new issue doc
    filed (nothing found vulnerable). Todos 1+2 above (root-cause diagnosis of the ORIGINAL 2026-06-28 incident +
    applying the 219,529-row reconciliation) are unrelated to this check and remain open — out of this todo's scope
    (read-only code review, no live backfill/reconciliation run, per the batch2 plan's own todo text).
