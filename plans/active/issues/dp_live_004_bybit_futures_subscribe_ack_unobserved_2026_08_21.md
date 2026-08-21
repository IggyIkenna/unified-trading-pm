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
status: open
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
resolved_by:
last_updated: 2026-08-21
locked_since:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/connectors/bybit_ws.py,
    market-tick-data-service/market_tick_data_service/live/connectors/bybit_futures_book_ticker_ws.py,
  ]
source: dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md todo 2 (post-relaunch captured-row verification)
---

# BYBIT-FUTURES post-relaunch verification: still zero captured rows, root-caused to missing subscribe-ack observability

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

- [ ] [CODE] P2. Add subscribe/unsubscribe ack-frame recognition + INFO-level logging to the receive loop in
      `market-tick-data-service/market_tick_data_service/live/connectors/bybit_futures_book_ticker_ws.py`
      (`stream()`/`_handle_frame`/`_handle_orderbook_frame`, ~lines 264-330) — a frame with `"op"` present and no
      `"topic"` is a subscribe/unsubscribe ack, not silently-dropped noise. DoD: a unit test asserts a
      `{"success": false, "ret_msg": "...", "op": "subscribe"}` frame produces a logged WARNING (or equivalent),
      and a `{"success": true, ...}` frame produces a logged INFO. (repo: market-tick-data-service)
- [ ] [CODE] P2. Same fix, `bybit_ws.py`'s trades connector (`_open_and_subscribe`/`_handle_text`/the receive
      loop around lines 292-386) — identical silent-drop gap confirmed by direct grep. Pair with the todo above;
      do both together (same root cause, same shape). (repo: market-tick-data-service)
- [ ] [DATA] P2. After both land + the next `mtds-live-cefi-consolidated-*` relaunch, re-verify BYBIT-FUTURES via
      a direct per-VM manifest-shard read (same method as this doc's evidence). If the ack log now shows a Bybit
      REJECT, file that as its own follow-up (a genuine, now-diagnosable Bybit-side limit); if it shows ACCEPT
      with zero subsequent ticks, that is a new, narrower mystery worth its own investigation. If a captured row
      finally appears, close this doc and update
      `/plans/active/cross_ag_live_capture_parity_2026_08_14.md`'s Finding C captured-row-verification todo with
      the confirming evidence.

## Progress Log

- **2026-08-21 (data_engineering, slot 19)**: filed from
  `dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md` todo 2 (post-relaunch captured-row verification). Full
  evidence above — stable 5x-repeated per-VM shard read (no fluctuation), cross-checked against a known-healthy
  venue on the same shard, SSH log inspection confirming zero subscribe-ack observability across the connector's
  full run, and a direct code read confirming the receive loop silently drops Bybit's own ack control frames in
  both `bybit_ws.py` and `bybit_futures_book_ticker_ws.py`.
