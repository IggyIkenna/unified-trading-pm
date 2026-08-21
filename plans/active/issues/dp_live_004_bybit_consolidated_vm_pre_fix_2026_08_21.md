---
doc_type: issue
title: "DP-LIVE-004: BYBIT-FUTURES book_snapshot_5 remains unproductive on pre-fix consolidated VM"
summary: >-
  The BYBIT-FUTURES book_snapshot_5 shard on mtds-live-cefi-consolidated-20260817-025031 remains unproductive.
  MTDS commit 5f88715e (2026-08-18) already filters the combined BYBIT catalog to LINEAR PERPETUAL/FUTURE ids;
  the VM predates that fix and must be relaunched from a current artifact.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-alerts, dp-live-004, bybit-futures, stale-live-vm]
related: []
created: 2026-08-21
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P1
source: [DP-LIVE-004]
locked_by: live-defi-rollout
---

# DP-LIVE-004: BYBIT-FUTURES book_snapshot_5 remains unproductive on pre-fix consolidated VM

## What I found

The affected VM is `mtds-live-cefi-consolidated-20260817-025031`. The MTDS checkout on
`live-defi-rollout` already contains commit `5f88715e` (2026-08-18), which filters the
BYBIT-FUTURES subscription universe to `PERPETUAL` and `FUTURE` instrument types before
building `orderbook.50.*` topics. The book connector reuses this filter. The VM name shows
it was created before that fix, so its running code can still subscribe the combined BYBIT
catalog, including unsupported `SPOT_PAIR` instruments.

## Why it matters

The old runtime can keep attempting the shard and emit `empty_confirmed` without producing
book snapshots. Leaving that VM running preserves the stale behavior even though the fix is
already on `origin/live-defi-rollout`.

## Recommended decision

Use the deployment-service live CeFi launcher/relaunch path to replace the pre-fix VM from
an artifact containing MTDS `5f88715e`, then verify target-scoped manifest productivity and
that the DP-LIVE-004 candidate clears. This escalation does not perform the live VM mutation.

## Todos

- [ ] [OPERATOR] P1. Relaunch `mtds-live-cefi-consolidated` from a current MTDS artifact and verify the BYBIT-FUTURES `book_snapshot_5` shard produces rows; retain the current VM only until replacement liveness and productivity are confirmed.
- [x] [DIAGNOSIS] P1. Confirm MTDS commit `5f88715e` is an ancestor of `origin/live-defi-rollout` and covers the shared Bybit book connector filter.

