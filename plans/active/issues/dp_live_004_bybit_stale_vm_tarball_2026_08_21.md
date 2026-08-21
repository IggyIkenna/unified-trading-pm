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
- [ ] [INFRA-or-BACKEND] P1. **DUPLICATE OF `/plans/archive/issues/dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md`
      todo 2** (the canonical, already-consolidated doc for this same VM/incident; verified status: open,
      not archived) — this todo's diagnostic progress feeds that doc's own "verify a real captured row / if
      unproductive, inspect subscribe acks" open todo directly; do not diagnose independently in both places.
      **NEW FINDING 2026-08-21 (slot-3, infra) — investigate
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

## Progress Log

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
