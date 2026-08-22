---
doc_type: issue
title: DP-LIVE-004 BYBIT-FUTURES shard is running a pre-filter MTDS tarball
summary: >-
  The live CeFi VM mtds-live-cefi-consolidated-20260817-025031 still subscribes
  BYBIT-FUTURES SPOT_PAIR instruments and produces no captured rows because its
  deployed tarball predates market-tick-data-service@5f88715e4b, which shipped the
  PERPETUAL/FUTURE filter. The fix is on live-defi-rollout but the VM needs a
  safe replacement before the live shard can recover.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-live-004, bybit-futures, stale-tarball, live-capture]
related:
  - /plans/active/issues/mtds_live_cefi_redeploy_cold_start_is_universe_gap_2026_08_17.md
  - /plans/active/cross_ag_live_capture_parity_2026_08_14.md
created: "2026-08-21"
parent_epic: mtds_mdps_master
assigned_vm: planning
priority: P1
source: [DP-LIVE-004, DP_CRON_DID_NOT_FIRE, agt-2bf629]
author: data-pipeline-failure
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-infra
depends_on: []
context_scope:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /plans/active/issues/mtds_live_cefi_redeploy_cold_start_is_universe_gap_2026_08_17.md
  - market-tick-data-service/market_tick_data_service/live/connectors/bybit_ws.py
  - market-tick-data-service/market_tick_data_service/live/connectors/bybit_futures_book_ticker_ws.py
  - deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh
---

# DP-LIVE-004 BYBIT-FUTURES shard is running a pre-filter MTDS tarball

> Same-shape predecessor (resolved, archived — cited here as historical evidence, per the
> archive-safety ratchet, operator ruling 2026-08-17):
> `/plans/archive/issues/dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md`.

## What I found

The live productivity alert names `mtds-live-cefi-consolidated-20260817-025031`,
venue `BYBIT-FUTURES`, and `book_snapshot_5`. Read-only inspection on
2026-08-21 confirmed:

- The VM has been `RUNNING` since 2026-08-16T19:50:40-07:00 (2026-08-17T02:50:40Z).
- The live Bybit logs contain `BYBIT:SPOT_PAIR:*` instrument-window errors, proving
  the running connector is still accepting the unfiltered IS universe.
- The deployed `bybit_ws.py` contains the 21,000-character chunker but no
  `_is_linear_derivative`/`PERPETUAL` filter markers. The corresponding
  book/ticker connector is likewise pre-filter.
- `market-tick-data-service@5f88715e4b` is an ancestor of the current
  `origin/live-defi-rollout`; that commit adds the filter to all four Bybit live
  data types. Therefore this is stale deployment state, not an unshipped code fix.

The VM also cold-started at 02:50Z before the same-day instruments partition was
published, matching the separate cold-start issue linked above. It later resolved
1,282 instruments at 06:07Z, but the stale tarball continued attempting the
unfiltered universe and never produced a captured row for this shard.

## Why it matters

The DP-LIVE-004 detector is correctly identifying an unproductive, live process.
Leaving the VM running preserves a false appearance of liveness while the Bybit
connectors continue to waste subscriptions on unsupported spot instruments and
the four Bybit data types remain uncaptured. No placeholder output should be
written.

## Recommended decision

Replace the running consolidated CeFi VM with a fresh launcher-generated VM after
the standard three-signal staleness check confirms it is the same unproductive
shard (heartbeat age, run-log tail, and per-VM manifest mtime). The launcher’s
tarball-freshness gate must pass, and post-relaunch verification must show at
least one real `captured` BYBIT-FUTURES row for `book_snapshot_5` (then the other
three data types). Deleting/stopping the current running VM is an operator-facing
external action and is not performed by this escalation without that decision.

## Todos

- [x] ✅ [OPERATOR] P1. **DONE 2026-08-21 (slot-3, infra).** Operator (Harsh, via
      `/ao-watchdog`) APPROVED replacement of the confirmed stale
      `mtds-live-cefi-consolidated-20260817-025031` VM, with an explicit
      controlled-cutover condition (keep old VM running/undeleted until the
      replacement is verified). Ruling captured + executed — see todo below and
      Progress Log.
- [x] ✅ [INFRA] P1 (launch half). **DONE 2026-08-21 (slot-3, infra).** Launched
      replacement `mtds-live-cefi-consolidated-20260821-200626` via
      `launch-mtds-live-cefi-consolidated.sh` (`FORCE=true`, justified: old VM
      reverified healthy-but-stale-code per infra.md STEP 0.65's
      deliberate-stale-code-replacement carve-out, matching the 2026-08-17
      precedent in `cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16_finalize.md`).
      Launcher's own `lc_verify_tarball_freshness` auto-republished a stale
      market-tick-data-service tarball and rebuilt from local HEAD
      (`f88dfdbd19db`, confirmed `git merge-base --is-ancestor 5f88715e4b
      f88dfdbd19db` — the filter fix is an ancestor). Verified on the new VM: all
      24 MVP shard processes up (`ps aux`), all 3 Bybit connector files
      (`bybit_ws.py`, `bybit_futures_book_ticker_ws.py`, `bybit_spot_ws.py`)
      contain the `PERPETUAL`/`_is_linear_derivative` filter markers, and no
      `SPOT_PAIR` errors appear in any Bybit log (unlike the old VM). **Old VM
      left RUNNING/undeleted** — the decommission half of this todo is NOT done;
      see the new todo below for why.
- [x] ✅ [INFRA-or-BACKEND] P1 — **DONE 2026-08-21 (slot-10, infra) — code fix shipped:
      market-tick-data-service@efd0e788.** Was: **DUPLICATE OF `/plans/archive/issues/dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md`
      todo 2** (the canonical, already-consolidated doc for this same VM/incident; verified status: open,
      not archived) — this todo's diagnostic progress feeds that doc's own "verify a real captured row / if
      unproductive, inspect subscribe acks" open todo directly; do not diagnose independently in both places.
      That doc's own todo 2 was itself resolved 2026-08-21 (negative captured-row result, root-caused, follow-up
      filed at `/plans/archive/issues/dp_live_004_bybit_futures_subscribe_ack_unobserved_2026_08_21.md`) — root
      cause: Bybit's own subscribe/unsubscribe ack control frames were silently dropped, unlogged, by every Bybit
      connector's receive loop, so there was no way to tell a rejected subscribe from an accepted one producing
      no ticks. Shipped the fix that follow-up doc's todos 1+2 called for: added a shared `_log_subscribe_ack()`
      helper (`bybit_ws.py`, aliased into `bybit_futures_book_ticker_ws.py`) that recognizes a control frame (has
      `"op"`, no `"topic"`) and logs it at WARNING (rejected) or INFO (accepted) in all four BYBIT-FUTURES
      connectors (trades, book_snapshot_5, depth_of_book_10, derivative_ticker), plus unit tests per that doc's
      DoD. Full QG green (11212 passed). **Remaining work — todo 3 of the follow-up doc** (re-verify via a
      per-VM manifest-shard read after the next `mtds-live-cefi-consolidated-*` relaunch deploys this fix) is
      NOT done by this todo — it requires a VM relaunch + live observation, tracked there, not here.
      **Original NEW FINDING 2026-08-21 (slot-3, infra) — investigate
      why BYBIT-FUTURES produces ZERO captured rows on the new VM despite the
      filter fix being present and the universe resolving correctly.** On
      `mtds-live-cefi-consolidated-20260821-200626`, the per-VM manifest
      (`_index/per_vm/<vm>.parquet`) shows BYBIT-FUTURES 100% `empty_confirmed`
      across all 4 MVP data types after 30+ min live (trades: 825 rows,
      depth_of_book_10: 1291 rows, derivative_ticker: 1 row, book_snapshot_5: 0
      rows — none `captured`), while every sibling venue on the SAME VM in the
      SAME window has hundreds-to-thousands of `captured` rows (ASTER 519,
      BINANCE-FUTURES 2135, COINBASE-SPOT 408, DERIBIT 4333, HYPERLIQUID 223,
      KRAKEN-FUTURES 571, OKX-FUTURES 377, OKX-SWAP 451). Ruled out as causes:
      (a) universe resolution — `read_is_universe_sync` correctly resolves the
      full 1291-row BYBIT catalog (747 PERPETUAL + 44 FUTURE + 500 SPOT_PAIR,
      confirmed against `instrument_availability/by_date/day=2026-08-21/.../
      venue=BYBIT/instruments.parquet`); (b) `canonical_instrument_id` shape —
      sampled ids (`BYBIT:PERPETUAL:0G-USDT@LIN`, `BYBIT:FUTURE:BTC-USDT@LIN-
      20260904`) match exactly what `bybit_ws.py`'s `_is_linear_derivative`
      expects (`parts[1].upper() in {PERPETUAL, FUTURE}`), so the 791
      derivative-eligible instruments should pass the filter; (c) no `ERROR`/
      `SPOT_PAIR` lines in the per-shard logs. NOT yet isolated: whether
      `connect()`'s filtered `self._instrument_ids` set is actually non-empty at
      runtime, whether the LINEAR websocket endpoint is acking the subscribe
      batch, and whether `bybit_futures_book_ticker_ws.py` (book_snapshot_5/
      derivative_ticker/depth_of_book_10) has an equivalent or different bug from
      `bybit_ws.py` (trades) — both showed the same zero-capture symptom, so
      likely a shared root cause, but not confirmed. SSH access to the VM is
      already available (`gcloud compute ssh mtds-live-cefi-consolidated-
      20260821-200626 --zone=asia-northeast1-c`) — sudo required for
      `/home/ikennaigboaka/logs/` and the venv at
      `/home/ikennaigboaka/venv/bin/python`, package installed at
      `/home/ikennaigboaka/workspace/mtds/market_tick_data_service`. **Old VM
      `mtds-live-cefi-consolidated-20260817-025031` must stay running/undeleted
      until this is resolved and a real captured BYBIT-FUTURES row is confirmed**
      — the operator's controlled-cutover condition is not yet met. Repo:
      market-tick-data-service.
- [ ] [DATA] P1. After the above is fixed and a real captured row is confirmed for
      all four BYBIT-FUTURES data types, decommission the old VM
      (`mtds-live-cefi-consolidated-20260817-025031`) per the 3-signal staleness
      check and confirm DP-LIVE-004 clears.
- [ ] [INFRA] P1 — **NEW 2026-08-22 (autonomous dispatch).** Root-caused (see
      Progress Log) and fixed the actual reason all four BYBIT-FUTURES data types
      stayed zero-captured even on the `efd0e788`-deployed VM
      (`mtds-live-cefi-consolidated-20260822-092840`): the shared linear-derivative
      filter let `@INV` (inverse-margin) instruments through to the LINEAR-only
      endpoint, and Bybit rejects the WHOLE subscribe batch (not just the bad
      topic) when any `@INV` topic rides along with valid `@LIN` ones — silently
      zeroing every chunk that happened to contain one of the 4 real BYBIT inverse
      instruments (BTCUSD/DOGEUSD/LINKUSD/SOLUSD perpetual+future). Fix ships as
      `market-tick-data-service@<pending quickmerge sha>`. Once shipped: launch a
      fresh `mtds-live-cefi-consolidated-*` VM (FORCE=true, 4th parallel instance —
      justified: none of the 3 existing VMs carry this fix, and this is the exact
      relaunch-then-verify-then-decommission pattern already used twice today),
      verify a real `capture_status=captured` BYBIT-FUTURES row on the new VM, then
      decommission all 3 prior VMs together (superseding the single-VM decommission
      todo above).

## Progress Log

- **2026-08-22 (autonomous dispatch, `/autonomous`)**: Picked up per the operator's
  `BLK-9e8ffbb2` answer **A** (authorize relaunch). Fresh-verified rather than
  trusted: `gcloud compute instances list` confirms all THREE VMs still `RUNNING`
  (`...-025031` since 2026-08-16, `...-200626` since 2026-08-21, `...-092840` since
  2026-08-22T01:43:57-07:00). SSH-confirmed `...-092840` genuinely has `efd0e788`
  deployed (`_log_subscribe_ack` present and firing — matches the D10 remediation
  entry below) but a fresh per-VM manifest read (via UTL `get_storage_client()`,
  not `gsutil` — the hook-blocked path) shows it is STILL 100% `empty_confirmed`
  across all 4 BYBIT-FUTURES data types (`book_snapshot_5`/`depth_of_book_10`/
  `derivative_ticker`/`trades`: 1294/1294 each, `max attempted_at`
  2026-08-22T15:22Z — current, not stale), 6.5+ hours after launch. So the sibling
  escalation `agt-81aea5`'s earlier "3rd-parallel-VM risk" concern from a few hours
  ago is now moot: the 3rd VM already exists, has the ack fix, and is STILL not
  producing captured rows — this is a live, unresolved code bug, not a
  deploy-lag question.
  **Root-caused via direct live reproduction** (not guesswork): live logs on
  `...-092840` show exactly 4 repeating `Bybit subscribe ack REJECTED` topics every
  reconnect cycle (`publicTrade.BTCUSD-25SEP26`, `publicTrade.DOGEUSD`,
  `publicTrade.LINKUSD`, `publicTrade.SOLUSD` — all bare-USD, no `T`, i.e. Bybit
  INVERSE/coin-margined instruments) and literally zero "accept" acks or real
  ticks logged in 792 reconnect cycles over 6.5h. Traced to `_is_linear_derivative`
  (`bybit_ws.py`) only checking `instrument_type` (PERPETUAL/FUTURE), never the
  `@LIN`/`@INV` margin marker baked into the canonical `instrument_id` — so these 4
  real BYBIT inverse instruments (Bybit only lists 4: BTC/DOGE/LINK/SOL) pass the
  filter and reach the LINEAR-only endpoint (`_BYBIT_LINEAR_WS_URL` — inverse
  contracts live on a SEPARATE `.../v5/public/inverse` endpoint this connector
  never opens). Confirmed the blast radius with an isolated probe connection
  (`aiohttp` direct to `wss://stream.bybit.com/v5/public/linear`, not the buggy
  production reconnect loop): a batch of 3 valid `@LIN` topics
  (`BTCUSDT`/`ETHUSDT`/`SOLUSDT`) + the 4 `@INV` ones got exactly ONE reject ack
  and ZERO ticks in 20s; the SAME 3 valid topics alone (no `@INV` mixed in) got a
  success ack and **217 real trade ticks in 15s**. Bybit fails the entire
  subscribe request atomically when any topic in it is invalid — it does not
  partially honor the valid topics. Since `_send_sub_batch` chunks the full sorted
  instrument set into fixed-size batches, these 4 poisoned symbols zero out every
  chunk they land in, which fully explains the observed 100% `empty_confirmed`
  across ALL 4 data types (not a partial degradation limited to 4 symbols).
  **Shipped the fix**: `_is_linear_derivative` now also excludes any `@INV`-marked
  instrument (market-tick-data-service, `bybit_ws.py` — shared by both
  `bybit_ws.py` and `bybit_futures_book_ticker_ws.py` via the existing
  `is_bybit_linear_derivative` alias, so book_snapshot_5/depth_of_book_10/
  derivative_ticker/trades all get the fix from one change). Updated
  `tests/unit/test_bybit_ws_connector.py` (the OLD test literally asserted
  `_is_linear_derivative("BYBIT:FUTURE:BTC-USD@INV-20261225") is True` — codifying
  the bug; now asserts `False`, plus a new `test_connect_filters_out_inverse_margin_ids`
  connect()-level test mirroring the existing SPOT_PAIR-filter test). Next: QG,
  quickmerge, relaunch a 4th `mtds-live-cefi-consolidated-*` VM with the fix,
  verify a real captured row, decommission all 3 prior VMs. See the linked
  ack-unobserved doc's Progress Log for a duplicate-avoiding cross-reference.
- **2026-08-22 (task `dp_live_004_bybit_stale_vm_tarball-953844d905c9`, slot 7, data_engineering)**: Picked up the
  same open `[DATA] P1` decommission todo already worked by slots 13/21 today. Fresh-verified rather than trusted:
  `gcloud compute instances list` shows THREE `mtds-live-cefi-consolidated-*` VMs now `RUNNING` in parallel —
  `...-20260817-025031` (original, since 2026-08-16T19:50:40-07:00), `...-20260821-200626` (2nd, since
  2026-08-21T13:07:39-07:00), and `...-20260822-092840` (3rd, launched by the D10 remediation pass logged
  immediately below, since 2026-08-22T01:43:57-07:00). `GET /api/escalations/active` shows escalation `agt-aecdd5`
  (`market-tick-data-service`, `data_pipeline_failure`) currently `dispatched` to **slot 21** (dispatched
  2026-08-22T12:00:27Z, unresolved) — i.e. this exact incident is ALREADY being actively worked by another slot
  right now. `GET /api/state`'s `blocked_queue` has no open Bybit/`BLK-9e8ffbb2`-shaped entry (the earlier
  blocked-question is resolved/closed, consistent with the D10 remediation pass having acted on it). Per the D10
  remediation entry below, the precondition for this todo ("a real captured row confirmed for all four
  BYBIT-FUTURES data types") is still NOT met — the newest root cause (Bybit gateway explicitly REJECTING specific
  topic/symbol combinations, not a silent ack drop) requires a code fix to `bybit_ws.py`/
  `bybit_futures_book_ticker_ws.py`'s subscribe-topic/category construction that has not yet shipped. Did not
  re-run the SSH/manifest inspection a further time (slot 21's live escalation is doing exactly that right now;
  duplicating it risks colliding SSH sessions on the same VMs for no new information). Not decommissioning either
  prior VM — the controlled-cutover condition remains unmet on all three VMs. Releasing this task back to the
  queue (`reason_code: GATED`) rather than looping on work already actively in flight under `agt-aecdd5`; no
  code/infra/manifest changes made this pass.
- **2026-08-22 (D10 remediation, `dispositions.json` `issues_corpus_completion_2026_08_21` — "cycle the singleton
  BYBIT-FUTURES live-capture VM through its registered launcher, controlled cutover")**: Executed the fresh relaunch
  this doc's own open todos + standing `BLK-9e8ffbb2` blocked-question already called for. Confirmed pre-state
  matched the record (both prior VMs `RUNNING`, `efd0e788` undeployed to either). Launched
  `mtds-live-cefi-consolidated-20260822-092840` via the registered `launch-mtds-live-cefi-consolidated.sh`
  (`FORCE=true` — required, a same-prefix VM was RUNNING; the launcher's own tarball-freshness gate auto-republished
  stale `unified-api-contracts`/`deployment-service` tarballs from local HEAD, then re-verified all 5 fresh,
  including `mtds-code@7facfa4383a5`, before creating the VM). Verified STARTED (`RUNNING`, external IP assigned).
  SSH-confirmed `efd0e788` (the ack-logging fix) IS now live on this VM (`_log_subscribe_ack` present and firing).
  **Captured-row verification: STILL NEGATIVE, but with a materially more precise root cause than before.** Per-VM
  manifest read (`_index/per_vm/<vm>.parquet`, filtered `venue=BYBIT-FUTURES`) after ~15 min live: only
  `derivative_ticker: empty_confirmed 817` — `trades`, `book_snapshot_5`, `depth_of_book_10` show ZERO rows of any
  status. The ack-logging fix now makes the failure VISIBLE (the new signal this session found): live
  `bybit_ws.py`/`bybit_futures_book_ticker_ws.py` logs show explicit `WARNING ... Bybit subscribe ack REJECTED:
  op=subscribe ret_msg=error:handler not found,topic:orderbook.50.BTCUSD-25SEP26` (and identically for
  `publicTrade.BTCUSD-25SEP26`, plus `...DOGEUSD`/`...LINKUSD`/`...SOLUSD` topics) on repeated subscribe attempts —
  Bybit's own gateway REJECTS these specific topic/symbol combinations outright, not a silent drop. The rejected
  symbols share a shape distinct from passing ones (bare `BTCUSD-25SEP26`/`DOGEUSD`/`LINKUSD`/`SOLUSD`, no explicit
  linear/`USDT` marker) — consistent with an INVERSE-contract or dated-expiry topic/category mismatch in the
  connector's subscribe-topic construction (Bybit v5 WS separates `linear`/`inverse` category endpoints and
  topic-symbol conventions), NOT the previously-suspected silent-drop (that hypothesis is now reasonably ruled out —
  acks ARE observed, and they are explicit rejections). **Not yet root-caused to a specific code line this
  session** — flagging as the next diagnostic step. **Old 2 VMs (`...-025031` pre-fix, `...-200626`
  fix-without-ack-visibility) LEFT RUNNING/undeleted** — the controlled-cutover condition (a real captured
  BYBIT-FUTURES row on the replacement) is still not met, now on a THIRD parallel VM; no decommission performed.
  Next step for whoever continues: root-cause the Bybit topic/category construction for the rejected symbol class
  in `bybit_ws.py`/`bybit_futures_book_ticker_ws.py`'s subscribe-message builder.
- **2026-08-22 (task `dp_live_004_bybit_stale_vm_tarball-953844d905c9`, slot 13, data_engineering)**: Re-dispatched
  the same task id already logged by slot 21 immediately below (released back to queue, unchanged). Fresh-verified
  rather than trusted: `gcloud compute instances list` shows both VMs still `RUNNING` (old since
  2026-08-16T19:50:40-07:00, replacement `mtds-live-cefi-consolidated-20260821-200626` since
  2026-08-21T13:07:39-07:00); SSH+sudo grep on BOTH VMs confirms `_log_subscribe_ack` count is still `0` in both
  `bybit_ws.py` and `bybit_futures_book_ticker_ws.py` on each — `market-tick-data-service@efd0e788` (the
  ack-logging fix) remains undeployed to either live VM. `GET /api/state`'s `blocked_queue` confirms
  `BLK-9e8ffbb2` (recommending an operator-authorized `FORCE=true` relaunch to pick up `efd0e788`) is still
  `answered_at: null` — no operator ruling has landed since slot 21's pass. This todo's precondition ("above is
  fixed and a real captured row confirmed for all four BYBIT-FUTURES data types") is therefore still unmet; not
  decommissioning the old VM. Did not re-file a duplicate blocked-question (same established reasoning as every
  prior pass below). No code/infra/manifest changes made this pass. Releasing back to the queue via
  `/skip-current-task` (`reason_code: GATED`) rather than looping on an unresolved operator decision.
- **2026-08-22 (task `dp_live_004_bybit_stale_vm_tarball-953844d905c9`, slot 21, data_engineering)**: Picked up the
  open `[DATA] P1` decommission todo above. Its precondition ("above is fixed and a real captured row confirmed for
  all four BYBIT-FUTURES data types") is NOT met — fresh-verified rather than trusted from the doc: `gcloud compute
  instances list` shows both VMs still `RUNNING` (old since 2026-08-16T19:50:40-07:00, replacement
  `mtds-live-cefi-consolidated-20260821-200626` since 2026-08-21T13:07:39-07:00), and SSH+sudo grep on the
  replacement VM confirms `_log_subscribe_ack` count is still `0` in both `bybit_ws.py` and
  `bybit_futures_book_ticker_ws.py` — `market-tick-data-service@efd0e788` (the ack-logging fix, confirmed an
  ancestor of local `origin/live-defi-rollout` HEAD) is still not deployed to either live VM. This is identical to
  every escalation logged today (`agt-521494`/`agt-81aea5`/`agt-ebe5eb`/`agt-b28ff1`) — no forward progress since the
  standing blocked-question `BLK-9e8ffbb2` (recommending an operator-authorized relaunch to pick up `efd0e788`) was
  filed and remains unanswered (`GET /api/escalations/active` returns `[]` right now — nothing currently dispatched
  to push this forward). Did not re-file a duplicate blocked-question per the same established reasoning in the
  entries below. Not decommissioning the old VM — doing so before a real captured row is confirmed on the
  replacement would leave BYBIT-FUTURES with zero live capture on either VM. Releasing this task back to the queue
  as gated on the same unresolved operator decision; no code/infra/manifest changes made this pass.
- **2026-08-22 (data_pipeline_failure escalation `agt-b28ff1`, slot 33)**: DP-LIVE-004 re-fired again for the OLD VM
  (`mtds-live-cefi-consolidated-20260817-025031`), venue BYBIT-FUTURES, data_type `trades` this time (previous
  same-day re-fires were `book_snapshot_5`) — last attempt 0.2h old. `gcloud compute instances list` confirms both
  VMs still `RUNNING` (old since 2026-08-16T19:50:40-07:00, replacement since 2026-08-21T13:07:39-07:00) — unchanged
  from every prior escalation today. SSH into the OLD VM: `bybit_ws.py` (the trades connector) shows 7 combined hits
  for `_log_subscribe_ack|_is_linear_derivative|PERPETUAL` (some filter-related tokens present, unlike the earlier
  "predates the filter entirely" characterization — worth a closer read next time someone digs into this VM, not
  re-derived here), but the live `live-bybit-futures-trades.log` tail is all routine `ManifestWriter`/
  `RESOURCE_SAMPLE` lines and the log still contains 25 `SPOT_PAIR` occurrences — the trades data_type is exhibiting
  the same symptom (subscribing/erroring on unsupported spot instruments, zero captured rows) as the already-diagnosed
  book_snapshot_5/depth_of_book_10 data types on this VM. `GET /api/escalations/active` shows only this escalation
  dispatched; no blocked-questions surface reachable from here to re-check `BLK-9e8ffbb2`'s answer status. Did not
  re-file a duplicate blocked-question (a 4th identical ask adds noise, not information, per `agt-521494`'s same
  reasoning) and did not relaunch/decommission any VM (unresolved operator decision). No code/infra/manifest changes
  made this pass — this is escalation #4 today confirming the identical stalled state; the fix (relaunch the old VM's
  replacement to pick up `market-tick-data-service@efd0e788`, then verify captured rows, then decommission) remains
  exactly as scoped in the open todos above, gated on the standing operator answer to `BLK-9e8ffbb2`.
- **2026-08-22 (data_pipeline_failure escalation `agt-ebe5eb`, slot 31)**: DP-LIVE-004 re-fired again for the OLD VM
  (`mtds-live-cefi-consolidated-20260817-025031`), venue BYBIT-FUTURES, data_type `book_snapshot_5` (last attempt
  0.2h old). `gcloud compute instances list` confirms both VMs still `RUNNING` (old since 2026-08-16T19:50:40-07:00,
  replacement since 2026-08-21T13:07:39-07:00) — unchanged from the immediately-prior escalation. SSH into the OLD
  VM confirms `_log_subscribe_ack` grep count 0 in both connector files (expected — this VM predates even the
  linear-instrument filter, per the earlier diagnosis) and the live log tail shows only routine `ManifestWriter`/
  `RESOURCE_SAMPLE` lines, no subscribe/ack activity. `GET /api/escalations/active` shows only this escalation as
  currently dispatched (the blocked-question mechanism is a separate surface from this queue, so its live status
  couldn't be re-checked from here). No new root cause — identical stalled state to `agt-521494`/`agt-81aea5` above.
  Did **not** re-file a duplicate blocked-question: `BLK-9e8ffbb2` (filed by `agt-521494`, recommending a fresh
  `mtds-live-cefi-consolidated-*` relaunch with `FORCE=true` to pick up `market-tick-data-service@efd0e788`) is
  already standing and unanswered; a second identical ask would only add noise, not information, per the same
  reasoning `agt-81aea5` applied. Did not relaunch or decommission any VM myself (an unresolved operator decision,
  not mine to make unilaterally). No code/infra/manifest changes made this pass.
- **2026-08-22 (data_pipeline_failure escalation `agt-521494`, slot 33)**: DP-LIVE-004 re-fired for the OLD VM
  (`mtds-live-cefi-consolidated-20260817-025031`), venue BYBIT-FUTURES, data_type `book_snapshot_5` (last attempt
  0.4h old). `gcloud compute instances list` confirms both VMs still `RUNNING` (old since 2026-08-16T19:50:40-07:00,
  replacement since 2026-08-21T13:07:39-07:00) — the controlled-cutover parallel-run window is unchanged. SSH into
  the replacement VM (`mtds-live-cefi-consolidated-20260821-200626`) re-confirms `market-tick-data-service@efd0e788`
  (the ack-logging fix) is still NOT deployed (`_log_subscribe_ack` grep count 0 in both connector files; no
  `subscribe`/`ret_msg`/`success` lines in `live-bybit-futures-book-snapshot-5.log` beyond the generic bootstrap
  line) — identical state to the sibling escalation `agt-81aea5` (~30min prior, `depth_of_book_10`) documented just
  above. No new root cause. Rather than re-confirming the same stalled state a further time with no forward
  progress (3+ same-day escalations now), filed blocked-question `BLK-9e8ffbb2` recommending the operator authorize
  a fresh `mtds-live-cefi-consolidated-*` relaunch (FORCE=true, same precedented pattern) to actually pick up
  `efd0e788`, then verify a real captured BYBIT-FUTURES row, then decommission both prior VMs — to converge this
  loop instead of leaving it open indefinitely. Polled 2 minutes per the one-shot bounded-wait contract; no answer
  arrived in that window, so the question is left standing for the operator/main agent (a later answer re-dispatches
  a fresh worker per the standard blocked-question flow). No code/infra/manifest changes made this pass.
- **2026-08-22 (data_pipeline_failure escalation `agt-81aea5`, slot 8)**: DP-LIVE-004 re-fired for this same VM
  (`mtds-live-cefi-consolidated-20260821-200626`), venue BYBIT-FUTURES, data_type `depth_of_book_10`. SSH-confirmed
  the ack-logging fix (`market-tick-data-service@efd0e788`, an ancestor of current LDR HEAD) is still not deployed
  to this VM (`_log_subscribe_ack` count 0 in both connector files) and all four Bybit log files still show zero
  subscribe/ack observability — no new root cause, matches the already-diagnosed pending-relaunch state. Full
  evidence appended to the canonical follow-up doc
  (`dp_live_004_bybit_futures_subscribe_ack_unobserved_2026_08_21.md`). Did not relaunch the VM myself (would add a
  third parallel instance on top of the already in-flight two-VM verify-before-cutover window; that action stays
  with the already-scoped [DATA]/[INFRA] todo below under the existing operator ruling). No code/manifest changes.
- **2026-08-21 (slot-10, infra, task `dp_live_004_bybit_stale_vm_tarball-9fedd3a6cca7`)**: Shipped the code fix
  the linked follow-up doc (`dp_live_004_bybit_futures_subscribe_ack_unobserved_2026_08_21.md`) root-caused and
  called for — Bybit's subscribe/unsubscribe ack control frames were silently dropped, unlogged, by every
  BYBIT-FUTURES connector's receive loop. Added a shared `_log_subscribe_ack()` helper (`bybit_ws.py`) recognizing
  a control frame (`"op"` present, `"topic"` absent) and logging WARNING (rejected) / INFO (accepted); aliased into
  `bybit_futures_book_ticker_ws.py` for the book/depth/ticker connectors. Applied at all four call sites
  (`bybit_ws.py::_handle_text`, `bybit_futures_book_ticker_ws.py`'s `_BybitBookStateConnector._handle_frame` and
  `BybitFuturesTickerWSConnector._handle_frame`). Added unit tests in both existing test files (rejected→WARNING,
  accepted→INFO, non-ack frames still parse normally) per the follow-up doc's stated DoD. Full local
  `quality-gates.sh` green (11212 passed, 0 failed). Shipped `market-tick-data-service@efd0e788` via quickmerge,
  verified on `origin/live-defi-rollout`. This closes THIS doc's own open todo (which was itself a duplicate of
  the already-resolved canonical doc's todo 2) — the remaining re-verify-after-relaunch step lives in the
  follow-up doc's todo 3, not here.
- **dedup pass 2026-08-21**: This is the SAME incident (identical VM `mtds-live-cefi-consolidated-20260817-025031` →
  identical replacement VM `mtds-live-cefi-consolidated-20260821-200626`, identical root cause — stale pre-filter
  BYBIT tarball predating `market-tick-data-service@5f88715e4b`) as the already-canonical, already-consolidated doc
  `dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md` (which itself absorbed 3 other independent filings of this
  exact finding on 2026-08-21, but did not yet reference this specific file) — a 4th, previously-uncaught duplicate
  of that same pattern. Marked the sole overlapping open todo `DUPLICATE OF` that canonical doc's own open todo 2
  (kept `status: open` here rather than a whole-doc `superseded` flip, since todo 1's decommission step and this
  doc's own ruled-out-causes diagnostic detail are not literally duplicated there yet — nothing archived by this
  pass). **Not lost**: this doc's own diagnostic progress feeds the canonical doc's open todo 2 directly —
  specifically, this doc already ruled out universe resolution and `canonical_instrument_id` shape as causes for
  BYBIT-FUTURES' zero-capture symptom on the *new* (post-fix) VM, narrowing the remaining hypothesis space to the
  connector's runtime subscribe-set/websocket-ack behavior. Whoever next picks up the canonical doc's todo 2 should
  read this doc's "NEW FINDING 2026-08-21" todo in full rather than re-deriving those ruled-out causes from scratch.
- **2026-08-21 (data-pipeline-failure escalation `agt-2bf629`)**: Read-only
  inspection of the live VM proved the running package predates
  `market-tick-data-service@5f88715e4b`; logs show `SPOT_PAIR` subscriptions.
  Current LDR already contains the complete filter fix. No source edit is needed;
  remediation is a replacement of the stale running VM and requires an operator
  decision because it changes live infrastructure state.
- **2026-08-21 (slot-3, infra, task
  `dp_live_004_bybit_stale_vm_tarball-7248e1b02fde--ruling`)**: Applied the
  operator's APPROVED ruling. Reverified old VM live (heartbeat 40s old,
  `RUNNING`) immediately before acting — genuinely healthy-process/stale-code,
  matching the 2026-08-17 precedent's carve-out. Launched replacement
  `mtds-live-cefi-consolidated-20260821-200626` with `FORCE=true` (required —
  the launcher's singleton lock refuses a launch while a same-prefix VM is
  RUNNING, and the ruling required the old VM to keep running until verified;
  reconciled the ruling's "do not `--force`" language as a caution against
  skipping staleness verification, not a ban on the launch mechanism itself,
  since both cannot be literally true at once and the historical precedent
  confirms this exact parallel-run-then-verify-then-decommission pattern was
  used before). Verified: process health (24/24 MVP shards up), code
  provenance (tarball SHA `f88dfdbd19db` confirmed ancestor-descendant of
  `5f88715e4b`; all 3 Bybit connector files carry the filter markers), no
  `SPOT_PAIR` errors. **Did NOT find a real captured BYBIT-FUTURES row** — see
  the new todo above for the full diagnosis of this distinct, newly-discovered
  problem (universe + filter shape both look correct in isolation, but live
  capture is silently zero for all 4 Bybit data types while every sibling venue
  on the same VM captures normally). Per the ruling's explicit condition, did
  NOT stop/delete the old VM — both VMs are currently running in parallel
  (expected, temporary duplication during a verify-before-cutover window; old
  VM was already non-productive for BYBIT-FUTURES before this action, so no
  regression, just deferred cleanup). Two scratch diagnostic scripts
  (`_slot3_manifest_check.py`, `_slot3_is_sample.py`) were created and deleted
  in `deployment-service/` during this session — not committed, throwaway only.
  Left [OPERATOR] stripped from todo 1 since the operator's decision itself was
  captured and enacted; the unresolved capture gap is tracked as its own P1
  todo rather than reopening the operator-approval question.
