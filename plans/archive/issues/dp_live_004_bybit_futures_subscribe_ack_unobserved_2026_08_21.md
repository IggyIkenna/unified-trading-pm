---
doc_type: issue
title: BYBIT-FUTURES still 100% empty_confirmed post-fix — subscribe ack/reject frames are silently dropped, unlogged
summary: >-
  DP-LIVE-004's fresh mtds-live-cefi-consolidated relaunch (2026-08-21) confirmed the
  PERPETUAL/FUTURE instrument filter is deployed and active, but all 4 BYBIT-FUTURES
  data_types remain 100% empty_confirmed. Root cause: the book/ticker AND trades
  connectors send `{"op":"subscribe",...}` but never log the send, and their receive
  loops silently drop every frame that isn't a recognized tick payload — including
  Bybit's own subscribe/unsubscribe ack ({"success":..., "ret_msg":..., "op":"subscribe"})
  control frames. There is currently no way to tell from the logs whether Bybit is
  rejecting the subscribe or accepting it and sending nothing.
status: resolved
nature: process
asset_group: [cefi]
stage: [live]
repos: [market-tick-data-service]
scope: [engineer]
tags: [data-pipeline-alerts, dp-live-004, bybit-futures, live-capture, observability]
related:
  [
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
  ]
created: 2026-08-21
author: data_engineering (slot 19)
parent_epic: security_and_cross_cutting_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: all 3 todos done 2026-08-22 (autonomous dispatch) — ack observability shipped + used exactly as
  designed; it revealed a Bybit REJECT (not a silent drop), which is root-caused + fixed in the parent doc
  (dp_live_004_bybit_stale_vm_tarball_2026_08_21) as a new, narrower @INV-margin-instrument bug
last_updated: 2026-08-22
locked_since:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/connectors/bybit_ws.py,
    market-tick-data-service/market_tick_data_service/live/connectors/bybit_futures_book_ticker_ws.py,
  ]
source: dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md todo 2 (post-relaunch captured-row verification)
---

# BYBIT-FUTURES post-relaunch verification: still zero captured rows, root-caused to missing subscribe-ack observability

> **RESOLVED 2026-08-22 (autonomous dispatch)**: all 3 todos done. The ack-observability gap this doc tracks is
> closed (`market-tick-data-service@efd0e788`) and used exactly as designed — the ack log revealed an explicit
> Bybit REJECT, not a silent drop. That REJECT is root-caused + fixed as a new, narrower bug (BYBIT-FUTURES's
> LINEAR-only endpoint was subscribing `@INV`-margin instruments too; Bybit fails the whole subscribe batch
> atomically on any invalid topic) in `/plans/active/issues/dp_live_004_bybit_stale_vm_tarball_2026_08_21.md`'s
> Progress Log, per `/codex/11-project-management/issue-doc-lifecycle.md`'s terminal-status convention — same
> pattern as this doc's own predecessor `/plans/archive/issues/dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md`.
> DP-LIVE-004 itself stays open/unmuted in the parent doc until a captured row is confirmed post-fix.

## What I found

Verified the 2026-08-21 fresh `mtds-live-cefi-consolidated-20260821-200626` relaunch (the fix-deployed VM from
`dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md`'s todo 1) via a direct, repeated read of its own per-VM
manifest shard (`_index/per_vm/mtds-live-cefi-consolidated-20260821-200626.parquet`, 5 stable reads ~10s apart, no
fluctuation this time — unlike the earlier flush-window instability that doc's Progress Log noted):

- **BYBIT-FUTURES, all 4 data_types, 100% `empty_confirmed`**: `book_snapshot_5` 1291/1291, `depth_of_book_10`
  1291/1291, `derivative_ticker` 799/799, `trades` 1291/1291. `attempted_at` spans 2026-08-21T20:56–22:02 UTC —
  current, not stale carryover.
- **Cross-check on the SAME shard**: `ASTER`/`book_snapshot_5` shows 524 genuinely `captured` rows (6
  `empty_confirmed`) — the pipeline mechanism (manifest write path, per-VM shard, IS universe resolve) is proven
  healthy on this VM; the failure is BYBIT-FUTURES-specific.
- Confirmed via SSH (`/home/ikennaigboaka/logs/live-bybit-futures-*.log`) that `read_is_universe_sync` resolves
  1291 instruments (unfiltered — expected, the filter applies downstream in `connect()`/`subscribe()`, not at
  universe-resolve time) and the deployed source's `_is_linear_derivative` filter IS present and wired
  (`bybit_ws.py` / `bybit_futures_book_ticker_ws.py`, both imported from `is_bybit_linear_derivative`) — this part
  of `market-tick-data-service@5f88715e4b` genuinely shipped and is active.

**Root cause**: across the full ~2-hour log history of `live-bybit-futures-book-snapshot-5.log` (boot 20:09:34 UTC
through now), there is **zero** occurrence of `subscribe`, `success`, or `ret_msg` — the connector never logs a
subscribe SEND, and its receive loop never logs a subscribe ACK/REJECT. Traced in code
(`bybit_futures_book_ticker_ws.py`):

- `_open_and_subscribe()` / `subscribe()` call `self._ws.send_str(json.dumps({"op": "subscribe", "args": batch}))`
  with no logging of the send (lines ~193-209).
- `stream()`'s receive loop (`async for msg in ws: ... self._handle_frame(...)`) dispatches every TEXT frame to
  `_handle_orderbook_frame`, which returns `[]` for anything whose `topic` doesn't start with `"orderbook."` —
  silently discarding Bybit's own subscribe/unsubscribe ack control frame
  (`{"success": bool, "ret_msg": str, "op": "subscribe", ...}`) with **no logging, no error, no metric**.
- `bybit_ws.py` (the trades connector) has the identical gap — same `send_str` with no log, same silent-drop
  receive loop (confirmed via the same grep).

This is the **third** distinct BYBIT-FUTURES bug in this chain (Tardis-alias resolution → fixed; unchunked
21,000-char subscribe frame → fixed; PERPETUAL/FUTURE filter → fixed 2026-08-18), and it explains why the prior two
fixes could not be independently verified sooner: the connector has genuinely never had subscribe-ack
observability. The 2026-08-15 diagnosis session (`cross_ag_live_capture_parity_2026_08_14.md`'s Finding C Progress
Log) DID design and locally stash this exact fix (item 3 of that session's 3-part fix:
"log subscribe/unsubscribe ack frames (success/ret_msg) instead of silently discarding them") — but the 2026-08-18
follow-up session that shipped `market-tick-data-service@5f88715e4b` only recovered/re-implemented the PERPETUAL/
FUTURE filter (item 1) from that lost stash, not the ack-logging (item 3); its own Progress Log entry says so
("fix (1) was designed + stashed ... but never committed ... the stash was never recovered"). The ack-logging
piece was never re-implemented.

## Why it matters

Without this, DP-LIVE-004 (and any future BYBIT-FUTURES live-capture regression) cannot be root-caused from logs
alone — every future investigator has to re-derive "is Bybit rejecting the subscribe, or accepting it and sending
nothing" from scratch, the same blind spot that made this exact bug take 2+ sessions to diagnose in 2026-08-15.
Whether the CURRENT zero-captured-rows state is a Bybit-side rejection (e.g. a per-connection topic-count limit
distinct from the already-fixed 21,000-char cap; the linear endpoint may cap active subscriptions per connection,
not just frame size) or something else cannot be determined until this observability gap is closed.

## Recommended decision

Add subscribe/unsubscribe ack-frame handling to both `bybit_ws.py` and `bybit_futures_book_ticker_ws.py`: in the
receive loop, recognize a control frame (`"op"` present, `"topic"` absent) and log it at INFO
(`success`/`ret_msg`/`op` fields) instead of silently dropping it as a non-orderbook frame. Once shipped and
redeployed, re-run this same per-VM-shard verification; if Bybit is genuinely rejecting the subscribe, the ack log
will show it and this becomes a new, independently diagnosable finding. Do NOT mute/relabel DP-LIVE-004 as
correctly-empty until a captured row is confirmed post-fix.

## Todos

- [x] ✅ [CODE] P2. **DONE 2026-08-21 (slot-10, infra) — market-tick-data-service@efd0e788.** Added a shared
      `_log_subscribe_ack()` helper in `bybit_ws.py` (a control frame has `"op"` present, `"topic"` absent) that
      logs WARNING on `success: false` / INFO otherwise, and wired it into both `_BybitBookStateConnector._handle_frame`
      and `BybitFuturesTickerWSConnector._handle_frame` in `bybit_futures_book_ticker_ws.py` (covers book_snapshot_5,
      depth_of_book_10, derivative_ticker). Unit tests added to `tests/unit/test_bybit_futures_book_ticker_ws_coverage.py`
      asserting the exact DoD shape (`{"success": false, "ret_msg": ..., "op": "subscribe"}` → WARNING,
      `{"success": true, ...}` → INFO) for both connector classes. Full QG green.
- [x] ✅ [CODE] P2. **DONE 2026-08-21 (slot-10, infra) — market-tick-data-service@efd0e788.** Same
      `_log_subscribe_ack()` helper wired into `bybit_ws.py`'s `BybitFuturesWSFeedConnector._handle_text` (trades
      connector). Unit tests added to `tests/unit/test_bybit_ws_connector.py` (rejected→WARNING, accepted→INFO) plus
      a dedicated `TestLogSubscribeAck` class covering the helper directly (ack-with-topic / no-op-key → False).
- [x] ✅ [DATA] P2. **DONE 2026-08-22 (autonomous dispatch).** Re-verified BYBIT-FUTURES via a direct per-VM
      manifest-shard read on `mtds-live-cefi-consolidated-20260822-092840` (the `efd0e788`-deployed VM): the ack
      log DOES now show a Bybit REJECT (`ret_msg=error:handler not found`) for 4 specific topics — exactly the
      "if the ack log now shows a Bybit REJECT, file that as its own follow-up" branch this todo called for.
      Filed + fixed as a new root cause in the parent doc
      (`dp_live_004_bybit_stale_vm_tarball_2026_08_21.md`'s Progress Log — `@INV`-margin instruments reaching the
      LINEAR-only endpoint, confirmed via an isolated live-probe reproduction). This doc does NOT close yet — that
      happens once the fix is shipped, relaunched, and a real captured row is confirmed, tracked as the parent
      doc's own new `[INFRA] P1` todo (not duplicated here, per this corpus's dedup convention).

## Progress Log

- **2026-08-22 (autonomous dispatch, `/autonomous`)**: Todo 3 ("re-verify after relaunch") executed for real:
  `efd0e788` (this doc's own fix) IS deployed and firing on `mtds-live-cefi-consolidated-20260822-092840` (launched
  2026-08-22, SSH-confirmed). The ack log did its job — it revealed exactly what todo 3 anticipated: **explicit Bybit
  REJECTs**, not silent drops (`ret_msg=error:handler not found` for 4 specific bare-USD topics:
  `BTCUSD-25SEP26`/`DOGEUSD`/`LINKUSD`/`SOLUSD`). Per this doc's own recommended decision ("if it shows a Bybit
  REJECT, file that as its own follow-up"), root-caused and fixed as a NEW, narrower bug in the parent doc
  (`dp_live_004_bybit_stale_vm_tarball_2026_08_21.md`'s Progress Log has the full evidence, incl. an isolated
  live-probe reproduction proving Bybit fails the WHOLE subscribe batch atomically when any `@INV`-margin topic
  rides with valid `@LIN` ones — explaining the still-100%-`empty_confirmed` result despite the ack fix being live).
  This doc's own todo 3 is DONE (ack observability worked exactly as designed); the captured-row confirmation itself
  is tracked in the parent doc's new `[INFRA] P1` todo, not duplicated here.
- **2026-08-21 (slot-10, infra, task `dp_live_004_bybit_stale_vm_tarball-9fedd3a6cca7`)**: Shipped todos 1+2
  (ack-frame recognition + logging in all four BYBIT-FUTURES connectors — trades, book_snapshot_5,
  depth_of_book_10, derivative_ticker) via `market-tick-data-service@efd0e788`, verified on
  `origin/live-defi-rollout`. Full local `quality-gates.sh` green (11212 passed, 0 failed). Todo 3 (re-verify via
  a per-VM manifest-shard read after the next `mtds-live-cefi-consolidated-*` relaunch) is NOT done — it requires
  a live VM relaunch to pick up this code, out of scope for this code-only task.
- **2026-08-21 (data_engineering, slot 19)**: filed from
  `dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md` todo 2 (post-relaunch captured-row verification). Full
  evidence above — stable 5x-repeated per-VM shard read (no fluctuation), cross-checked against a known-healthy
  venue on the same shard, SSH log inspection confirming zero subscribe-ack observability across the connector's
  full run, and a direct code read confirming the receive loop silently drops Bybit's own ack control frames in
  both `bybit_ws.py` and `bybit_futures_book_ticker_ws.py`.
- **2026-08-22 (data_pipeline_failure escalation `agt-81aea5`, slot 8)**: DP-LIVE-004 re-fired for the SAME VM
  (`mtds-live-cefi-consolidated-20260821-200626`), venue BYBIT-FUTURES, data_type `depth_of_book_10` (last attempt
  0.3h old, still unproductive). SSH-confirmed this is still the pre-fix runtime, not a new bug: `sudo grep -c
  '_log_subscribe_ack'` on the live VM returns `0` for both `bybit_futures_book_ticker_ws.py` and `bybit_ws.py` —
  `market-tick-data-service@efd0e788` (the ack-logging fix; confirmed an ancestor of current
  `origin/live-defi-rollout` HEAD `a9b1d055c9`) has not been deployed to this VM. Grepped all four live BYBIT-FUTURES
  log files (`book-snapshot-5`, `depth-of-book-10`, `derivative-ticker`, `trades`) for `subscribe`/`ret_msg`/ack
  patterns — zero matches beyond the generic kill-switch bootstrap line, confirming zero subscribe-ack observability
  is still live on this VM as of 2026-08-22T00:0xZ. No new root cause found; this is todo 3 exactly as already
  scoped — the VM needs another relaunch to pick up `efd0e788` before ack evidence can be observed. Did not perform
  the relaunch myself (a live-infra VM cutover already governed by the operator's 2026-08-21 controlled-cutover
  ruling and actively tracked in `dp_live_004_bybit_stale_vm_tarball_2026_08_21.md`'s open todo; adding a third
  parallel VM instance without a fresh sign-off risked compounding the in-flight two-VM verify-before-cutover
  window). No code or manifest changes made. Escalation closed as diagnosis-confirmed / no new action needed at this
  time.
