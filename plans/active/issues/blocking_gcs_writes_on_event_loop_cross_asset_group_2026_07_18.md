---
doc_type: issue
title: >-
  Blocking GCS writes on the asyncio event loop — cross-asset-group audit (3 fixed, DeFi concurrency still open)
summary: >-
  After the Tardis batch finalizer was found to freeze the event loop (~97% of wall time), three parallel read-only
  audits swept the OTHER live and batch writers for the same class. Three real instances were found and fixed the same
  day — the live websocket_runner hot path, the shared venue_fetch writer.close, and sports per-shard writes. The
  largest remaining item is not a blocking-IO bug at all: the DeFi CLI handler family has ZERO concurrency at any level
  (dates serial, protocol x chain serial), which is a throughput ceiling rather than a wedge. Fixing that concurrency
  first REQUIRES fixing the latent blocking writes underneath it, or it converts them into live event-loop bugs.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service, unified-trading-library]
scope: [engineer]
tags: [asyncio, event-loop, gcs, throughput, defi, sports, live]
related:
  [
    /plans/archive/issues/backfill_vm_disk_starvation_misdiagnosed_as_tardis_quota_2026_07_18.md,
    /plans/archive/issues/launcher_gcloud_continuation_broken_by_disk_sweep_2026_07_18.md,
  ]
created: 2026-07-18
author: unknown
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend
drift_direction: advance-code
depends_on: []
source: ["three parallel read-only writer audits run after the 2026-07-18 CeFi disk/throughput investigation"]
resolved_by:
locked_by:
context_scope: [market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py, market-tick-data-service/market_tick_data_service/live/websocket_runner.py, unified-trading-library/unified_trading_library/streaming/live_aggregator.py, /plans/active/defi_satellite_ao_dispatch_batch2_2026_07_26.md, /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md, market-tick-data-service/market_tick_data_service/cli/handlers/solana_defi_handler.py]
---

# Blocking GCS writes on the event loop — cross-asset-group audit

## Why this audit ran

The 2026-07-18 CeFi throughput investigation found that a synchronous GCS upload called inline in an async coroutine
froze the single event loop for ~1.6s per shard, serialising every concurrent fetch — about 97% of that run's wall
clock. The operator asked whether the same class exists in the other live and batch writers. Three read-only audits ran
in parallel over (a) MTDS/MDPS live, (b) TradFi/Databento, (c) DeFi + sports/prediction.

## Fixed the same day

| Path                | Site                                                                      | Why it mattered                                                                                                                                                                                                                                                                         |
| ------------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Live (MTDS)         | `live/websocket_runner.py` `_persist_window_to_sink`, `_emit_empty_shard` | `record_captured` / `record_zero_rows` cascade into a full GCS download + parquet merge + upload of the per-VM shard, on the loop, every window. Worsens through the day as the shard grows; the 5s flush debounce never helps because the live `base_timeframe` is 60s.                |
| Shared venue writer | `engine/orchestrator/venue_fetch.py` `_process_venue` (3 sites)           | `writer.close()` walks every partition doing a blocking `upload_file()` (5 retries / 60s backoff). Up to 6 venues run concurrently under `asyncio.gather` on multi-venue cron/poll VMs, so one venue's upload tail stalled all the others. Used by TradFi, CeFi, sports AND prediction. |
| Sports              | `venue_fetch.py` `_process_sports_venue_with_leagues` (2 sites)           | One `shard_writer.close()` per (bookmaker, league, fixture) shard — dozens to hundreds per venue per day, each a round trip AND a loop freeze. Direct sibling of the row above, 60 lines below it, missed when that fix was written.                                                    |

Ordering is preserved at every site: the call is still awaited before the coroutine continues, so rows and manifest
entries are written in the same sequence. Only the loop is released during the GCS I/O.

## Open — in priority order

### 1. DeFi handlers have no concurrency at any level (the real throughput item)

`unified_trading_library/service_framework/_adapter.py` processes BatchPayloads (dates) one at a time via
`async for ... await self._handler.process(payload)`, never gathered. Inside a date, `dex_pools_handler`,
`dex_swaps_handler`, `evm_defi_collectors` and siblings (gas_fees, lst_rates, solana_defi, liquidations,
vault_share_price, eigenlayer_rewards) run nested `for protocol: for chain: await ...` with no semaphore or gather. A
default launch (e.g. `launch-mtds-dex-swaps-backfill-vm.sh`, START_DATE 2023-01-01) is ~1300 days x 20-35 protocol/chain
combos of strictly sequential round trips on ONE VM.

The fetches themselves are already correctly server-side batched (The Graph `first:100-1000`, <=500-pool batches), so
the win is purely adding `asyncio.gather` + a `Semaphore` across the (protocol, chain) loop — the pattern Polymarket and
Kalshi already use correctly (`polymarket_adapter.py`, `kalshi_adapter.py`, `_solana_defi_fetch.py`).

**Do the blocking-write fix (item 2) FIRST or in the same change.** Parallelising the loop while the writes are still
inline converts every latent blocking write below into a live event-loop bug.

### 2. Latent blocking writes in DeFi handlers — needs per-site verification, NOT a mass edit

The audit reported ~12 handlers calling `storage.upload_bytes` synchronously from async handlers. **Spot-checking showed
the reported line numbers had drifted and the characterisation was too broad**: of three sampled sites, only one
(`dex_swaps_handler.py` `_collect_protocol_chain` -> `_write_swap_shard`) actually has an async caller invoking a
blocking writer. The other two (`gas_fee_handler._collect_solana_historical`, `lst_rates_handler._finalize_lst_rows`)
sit in SYNC functions, so they are not event-loop bugs as written, and one cited line was not an upload call at all.

So the fix is per-site: find where async code invokes each sync writer helper and wrap **that call**, rather than
editing the helpers. Verify each site's enclosing function is genuinely `async def` before touching it.

Note `dex_swaps_handler.py` is already at exactly its 900-line cap, and `_collect_protocol_chain` is at its function
size cap — a one-line fix does not fit. That file needs the concurrency refactor (item 1) anyway, so do both together.

### 3. Live sibling sites in SYNC functions

`live/websocket_runner.py::_record_empty_window` and
`unified_trading_library/streaming/live_aggregator.py::_handle_zero_tick_window` perform the same blocking manifest
write but from sync functions, so fixing them needs signature changes up the call chain. Lower value than items 1-2
(they are the zero-row paths).

### 4. Default-executor DNS contention — watch, do not fix yet

Every live WS connector and several DeFi adapters build `aiohttp.TCPConnector(resolver=ThreadedResolver())`, and
`ThreadedResolver` runs `getaddrinfo` on the DEFAULT thread pool, which `asyncio.to_thread` also uses. This is the
mechanism that once wedged the Tardis path at cpu=0% with 203 ConnectionTimeouts. It does NOT bite today because live
runs ~1 blocking call at a time (one OS process per shard) and DeFi's `Semaphore(10)` x <=3 venues stays under the
default pool's ~32 slots. It becomes real if item 1 raises DeFi concurrency, or if live ever fans out per-instrument
flushes. If either happens, give those paths a dedicated executor first.

## Verification standard for this issue

Every fix above must be verified the way the shipped ones were: confirm the enclosing function is `async def`, confirm
the call is still awaited (ordering preserved), and check the file's line/function caps before adding comments — the
900-line cap is enforced and a rationale comment is enough to break it.

## Todos

- [x] [INFRA] P2. **SHIPPED — market-tick-data-service@eeade63b0c, landed on live-defi-rollout, 2026-08-15. 3 of 8
      residual handlers converted; the other 5 do NOT match the assumed `for protocol: for chain: await ...` shape,
      corrected diagnosis below.** (2026-08-15, slot-15·infra). Re-verified each of the 8 named handlers' actual
      structure (not inferred from the title alone, per this todo's own "per-site verification, NOT a mass edit"
      instruction): - ✅ **Converted to `ParallelPerSymbolRunner` fan-out** (bounded by `defi_max_inflight_tasks`,
      manifest-write ordering preserved — `evm_defi_collectors.py`'s split build-tasks/apply-results phase mirrors
      `mtds@ff1b5d51`; `liquidations_handler.py` and `liquidation_events_handler.py` fan out their existing per-shard
      closures directly since those already do their own manifest-write + never raise): `evm_defi_collectors.py`,
      `liquidations_handler.py`, `liquidation_events_handler.py`. - 🔴 **`dex_swaps_handler.py`** — DOES have the
      matching nested-loop shape (`_collect_all_protocols`), but the file sits at 886/900 lines — converting in place
      doesn't fit. Needs the SAME stage-module extraction `dex_pools_handler.py` used (`_dex_pools_subgraph.py`) before
      the fan-out can land; not attempted here (a distinct, larger refactor, not a mechanical port). New todo below. -
      🔴 **`gas_fee_handler.py`** — `_collect_evm_chains`/`_collect_one_evm_chain_with_freshness` are plain `def` (SYNC,
      called without `await` from `process()`), not an async loop. There is no coroutine set to `gather` — applying "the
      established pattern" here requires first async-ifying the chain-collection path, which is a separate design call,
      not this todo's scope. New todo below. - 🔴 **`vault_share_price_handler.py`** — same shape as gas_fee:
      `_collect_vault_rows`/`_collect_chain_vault_rows` are plain `def` (SYNC, called without `await`), driven by
      synchronous Alchemy/web3 RPC calls. No async loop to convert. New todo below. - 🔴 **`lst_rates_handler.py`** —
      has NO `for protocol: for chain:` loop at all; EVM LST rates are fetched via a single multicall-style
      `_collect_evm_lst_rows(web3, evm_lst_addresses, ...)` call per date, not a per-shard loop. The todo's premise
      doesn't apply to this handler's actual structure. New todo below (re-verify whether any different fan-out axis —
      e.g. per-address — is worth adding, or close as not-applicable). - 🔴 **`eigenlayer_rewards_handler.py`** — single
      (EIGENLAYER, ETHEREUM) shard per day (confirmed via its own preflight, which records exactly one shard on
      catalog-stale). There is nothing to parallelize — closing this one as **not-applicable** rather than carrying it
      forward as an open item (see new todo below, which just records the verdict). - **Verification standard met for
      the 3 done handlers**: async caller confirmed (`process()`/module-level `_process_protocols` are already
      `async def`), ordering preserved (manifest writes still apply per-shard, in original shard order where the
      split-phase pattern was used), file/function line caps re-checked post-edit (`evm_defi_collectors.py` 705L,
      `liquidations_handler.py` 818L, `liquidation_events_handler.py` 502L — all under the 900L cap).
      `bash scripts/quality-gates.sh --no-fix` returned `ALL QUALITY GATES PASSED` on this exact diff pre-rebase
      (2026-08-15); 20+ consecutive attempts (background + `setsid`+`nohup`+`disown`-detached) to mint a POST-rebase
      HEAD-matching sentinel were killed by the shared host before finishing — see the issue doc filed for that
      (`mtds_qg_background_task_near_instant_kill_2026_08_15.md`). A later `run_in_background` attempt (task
      `bgre3k8hi`) ran cleanly end-to-end and shipped `market-tick-data-service@eeade63b0c` to `live-defi-rollout`
      (ancestry-verified, `ahead=0`).
- [ ] [INFRA] P3. Extract `dex_swaps_handler.py`'s protocol×chain collection loop (`_collect_all_protocols`) into a
      dedicated stage module (mirroring `dex_pools_handler.py` → `_dex_pools_subgraph.py`) to free line-cap headroom,
      then convert it to the `ParallelPerSymbolRunner` fan-out pattern `mtds@ff1b5d51`/this doc's 2026-08-15 fix
      established. Repo: market-tick-data-service. Source: this doc's 2026-08-15 per-handler diagnosis above.
- [ ] [INFRA] P3. Async-ify `gas_fee_handler.py`'s EVM chain-collection path (`_collect_evm_chains` →
      `_collect_one_evm_chain_with_freshness`, currently plain `def` called without `await`) OR carry an explicit
      in-code note saying why it must stay sync/serial, before any concurrency fan-out can apply. Repo:
      market-tick-data-service. Source: this doc's 2026-08-15 per-handler diagnosis above.
- [ ] [INFRA] P3. Async-ify `vault_share_price_handler.py`'s vault-collection path (`_collect_vault_rows` →
      `_collect_chain_vault_rows`, currently plain `def` called without `await`, driven by sync Alchemy/web3 RPC calls)
      OR carry an explicit in-code note saying why it must stay sync/serial, before any concurrency fan-out can apply.
      Repo: market-tick-data-service. Source: this doc's 2026-08-15 per-handler diagnosis above.
- [ ] [INFRA] P3. Re-assess `lst_rates_handler.py`: confirm whether ANY per-shard fan-out axis exists (e.g. per LST
      address within the single multicall-style EVM fetch, or across the EVM/Solana split) worth parallelizing, or close
      this handler out of "the 8 residual DeFi handlers" scope as not-applicable — it has no `for protocol: for chain:`
      loop to convert. Repo: market-tick-data-service. Source: this doc's 2026-08-15 per-handler diagnosis above.
- [ ] [INFRA] P3. **Fix the 2 blocking-write sites in SYNC functions** — per "Open — in priority order" item 3:
      `live/websocket_runner.py::_record_empty_window` and
      `unified_trading_library/streaming/live_aggregator.py::_handle_zero_tick_window` perform the same blocking
      manifest write as items 1-2 but from sync functions, so the fix needs signature changes up the call chain (make
      the enclosing path async, or dispatch the write via a dedicated executor the way `mtds@ff1b5d51` did for item 2).
      Lower value than items 1-2 (zero-row paths only) — added 2026-08-06, previously untracked prose. **Done when**:
      both sites no longer call the blocking manifest-write helper directly from a sync function, verified the same way
      item 2's shipped fix was (confirm the call is still awaited, ordering preserved).

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY candidate PARKED (conflict) — stays KEEP-NA —
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` explicitly records 'GENUINE overlap found' against this
  doc. Not flipped.
- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid -- Full audit rationale: The single remaining open todo (adding
  asyncio.gather+Semaphore concurrency, via the established ParallelPerSymbolRunner pattern, to 8 remaining DeFi CLI
  handlers: dex_swaps_handler.py, evm_defi_collectors.py, gas_fee_handler.py, lst_rates_handler.py,
  liquidations_handler.py, liquidation_events_hand...
- **context-scout 2026-08-01**: populated context_scope (4 entries).

- **context-scout 2026-08-03**: refreshed context_scope (6 entries, unchanged) — verified all still accurate and
  resolve; the remaining open todo (extend concurrency to the 8 residual DeFi handlers) is already directly represented
  by the `dex_swaps_handler.py` + `solana_defi_handler.py` entries.
- **na-eligibility-audit 2026-08-03 (cross-cutting tranche)**: KEEP-NA, valid — reaffirmed, unchanged. Today's edit that
  put this doc back in incremental scope was a cosmetic `context_scope` backfill commit, not a content change; the
  2026-08-01 rationale (a concurrency-critical shared-writer change needing per-handler verification, not a mass edit)
  still holds.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — reaffirms the 2026-07-30 park (GENUINE overlap w/
  cross_cutting_satellite_ao_dispatch_batch1) and the 2026-08-03 reaffirmation: sole open todo needs per-handler
  concurrency-safety judgment, not a mechanical edit. NEW this pass: found problem #3 ("Live sibling sites in SYNC
  functions" — websocket_runner.py::_record_empty_window + live_aggregator.py::_handle_zero_tick_window) listed in the
  doc's own "Open" section but with zero checkbox tracking it anywhere in the corpus — added a tracked todo below per
  the workspace's "every follow-up is a checkbox, never prose" rule.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — swapped out `_adapter.py` (now described in-doc as
  already-shipped/tuning-question, not missing code) and the archived disk-starvation background doc (context already
  summarized in this doc's own "Why" section) for `live/websocket_runner.py` and `streaming/live_aggregator.py`, the two
  sync-function sites the new P3 todo (added 2026-08-06) names directly.
- **na-eligibility-audit 2026-08-07 (cross-cutting tranche)**: KEEP-NA, valid — reaffirmed, unchanged. Both open todos
  (item-1 concurrency fan-out for 8 residual DeFi handlers, item-3 the 2 sync-function blocking-write sites) still need
  per-site correctness judgment (verify async caller, ordering, line-cap), not a mechanical mass edit.
- **cross_cutting_satellite_ao_dispatch_batch13 2026-08-15 (slot-15·infra)**: item-1 code done, NOT yet shipped.
  Converted `evm_defi_collectors.py`, `liquidations_handler.py`, `liquidation_events_handler.py` to the
  `ParallelPerSymbolRunner` fan-out pattern (matches this doc's "Verification standard for this issue" section: async
  caller confirmed, ordering preserved, line caps re-checked). The other 5 named handlers do NOT match the assumed
  nested-loop shape — 4 new P3 todos filed above with the corrected per-handler diagnosis (2 are sync-not-async, 1 has
  no protocol×chain loop at all, 1 is single-shard with nothing to parallelize, 1 needs a stage-module extraction
  first). Committed locally `market-tick-data-service@eeade63b` (pre-rebase diff got a full `ALL QUALITY GATES PASSED`,
  2042s) but NOT pushed — 20+ consecutive `quality-gates.sh` re-runs against the rebased/ruff-formatted HEAD (needed to
  mint a matching `--agent` sentinel) were killed by the shared host over ~4h, including fully-`setsid`+`nohup`+
  `disown`-detached attempts per an operator-directed diagnostic (ruled out `resource-watchdog.sh`'s RAM/CPU/swap checks
  specifically — they exempt anything <30s old, and several kills were both near-instant AND happened at healthy
  measured host RAM/load). Filed `plans/active/issues/mtds_qg_background_task_near_instant_kill_2026_08_15.md` with the
  full evidence trail — this item stays open, blocked on that infra issue, not on remaining code work. **Next session**:
  check that issue doc's own resolution first; if QG can complete, `cd market-tick-data-service && git log --oneline -1`
  should show `9a21fe0c` already checked out — just re-run `quality-gates.sh --no-fix`, then
  `quickmerge --agent --files market_tick_data_service/cli/handlers/evm_defi_collectors.py market_tick_data_service/cli/handlers/liquidations_handler.py market_tick_data_service/cli/handlers/liquidation_events_handler.py`,
  then flip this todo to `[x]` + the `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` todo with the shipped
  SHA.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:8db5b002b714e273]: KEEP-NA, valid -- Grep-verified 5 open checkboxes (lines 153,157,161,165,169), matching inventory_open_todos=5. A real AO dispatch (batch13, 2026-08-15) actually attempted this exact class of work and found the original '8 residual handlers, same nested-loop shape' premise was wrong for 5 of them -- the current 5 open todos are the CORRECTED, freshly-diagnosed shape, and for 3 of them the doc's own text explicitly states the fix 'requires... a separate design call, not this todo's scope' (gas_fee/vault_share_price async-ification) or 'a distinct, larger refactor, not a mechanical port' (dex_swaps extraction). The remaining 2 (lst_rates re-assessment, the 2 sync-function sites) need per-site concurrency-safety judgment per this doc's own 'Verification standard' section (confirm async caller, ordering preservation, line caps) -- exactly the live-dispatch-critical-path caveat the bounded-outcome bar warns about. Doc also carries a standing 2026-07-30 PARK ruling (rule d-adjacent) reaffirmed 4 more times (08-01,08-03,08-06,08-07) before the 08-15 re-diagnosis.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirmed unchanged since 2026-08-17. 5 open todos
  (lines 153,157,161,165,169), each needing per-handler correctness judgment (async-ification design calls, a
  stage-module extraction refactor, a re-assessment of whether any fan-out axis exists, or a signature-chain
  change up the call stack) — not mechanical mass edits. Cross-cutting tranche, batch 2 of 3.
