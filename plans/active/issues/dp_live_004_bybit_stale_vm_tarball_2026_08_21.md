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

- [ ] [OPERATOR] P1. Approve replacement of the confirmed stale
      `mtds-live-cefi-consolidated-20260817-025031` VM after the three-signal
      staleness check, or explicitly choose to leave it running.
- [ ] [INFRA] P1. If approved, stop/replace the VM using
      `launch-mtds-live-cefi-consolidated.sh`; verify the launcher freshness gate,
      startup, process health, and per-VM manifest progress.
- [ ] [DATA] P1. After replacement, verify captured rows for all four
      BYBIT-FUTURES data types and confirm DP-LIVE-004 clears.

## Progress Log

- **2026-08-21 (data-pipeline-failure escalation `agt-2bf629`)**: Read-only
  inspection of the live VM proved the running package predates
  `market-tick-data-service@5f88715e4b`; logs show `SPOT_PAIR` subscriptions.
  Current LDR already contains the complete filter fix. No source edit is needed;
  remediation is a replacement of the stale running VM and requires an operator
  decision because it changes live infrastructure state.
