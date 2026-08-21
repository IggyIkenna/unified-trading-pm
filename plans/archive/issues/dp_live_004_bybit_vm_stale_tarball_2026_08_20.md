---
doc_type: issue
title: >-
  DP-LIVE-004 BYBIT-FUTURES book_snapshot_5 shard runs on a VM launched before the subscribe-universe fix
summary: >-
  The BYBIT-FUTURES book_snapshot_5 shard on mtds-live-cefi-consolidated-20260817-025031 remains unproductive
  because that VM booted before the shipped SPOT_PAIR subscription filter; current source already contains the fix.
status: superseded
superseded_by: [dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20]
nature: process
asset_group: [cefi]
stage: [live, meta]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-live-004, bybit, stale-runtime, live-capture]
related:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /plans/active/issues/dp_cron_did_not_fire_still_storming_after_gcs_persistence_fix_2026_08_20.md
  - /plans/active/cefi_consolidated_closeout_2026_07_18.md
created: 2026-08-20
parent_epic: observability_master
priority: P1
assigned_vm: vm-cross-cutting
execution_scope: local-only
source: [DP-LIVE-004, agt-0d8048]
resolved_by:
locked_by:
context_scope:
  - /codex/05-infrastructure/data-pipeline-alerts.md
  - /codex/05-infrastructure/vm-launcher-runbook.md
---

# DP-LIVE-004 BYBIT-FUTURES book_snapshot_5 stale-runtime capture gap

> **SUPERSEDED 2026-08-21 (ag-closeout-audit cefi tranche, Phase 3 sweep)**: consolidated into
> `/plans/active/issues/dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md` — same VM
> (`mtds-live-cefi-consolidated-20260817-025031`), same root cause (`5f88715e4b`), same recommended action. This
> doc's own evidence/detail is kept for provenance; the tracked `- [ ]` todos live on the canonical doc now.

## What I found

The alert identifies `mtds-live-cefi-consolidated-20260817-025031`, venue `BYBIT-FUTURES`, and
`book_snapshot_5` as still attempting without a capture. Read-only GCE metadata confirms that VM was created at
`2026-08-17T02:50:40Z` and is still `RUNNING`.

The current `market-tick-data-service` integration branch contains `5f88715e4bdf7fc0c17711d2647e22f8a4d4ba57`
(`fix(bybit-live): filter BYBIT-FUTURES subscribe universe to PERPETUAL/FUTURE, excluding SPOT_PAIR`, committed
2026-08-18T10:49:19Z). The shared BYBIT book/ticker connector filters instrument IDs before constructing
`orderbook.50` topics, so `SPOT_PAIR` IDs cannot be sent to the derivatives-only endpoint.

The VM predates that fix. The consolidated live launcher installs the MTDS code from GCS tarballs during startup;
there is no live-code hot reload. Therefore the current alert is consistent with an old runtime continuing to
subscribe the unfiltered combined BYBIT catalogue, not with a missing source-code fix on the integration branch.

## Why it matters

The alert is a genuine productivity gap: the stale runtime can repeatedly attempt unsupported spot instruments and
produce no `book_snapshot_5` captures for the affected shard. Deduplication changes would only reduce alert volume;
they would not restore data capture.

## Recommended decision

Relaunch the consolidated CeFi live VM through the registered launcher after confirming the current MTDS tarball
contains `5f88715e` (or a descendant), then verify the replacement VM reaches `RUNNING`, records a current code
provenance marker, and produces captured BYBIT-FUTURES `book_snapshot_5` rows. Do not delete the existing VM until
the required liveness and manifest checks establish that replacement is safe; the launcher’s singleton guard and
the VM runbook govern the cutover.

## Evidence

- `git merge-base --is-ancestor 5f88715e4bdf7fc0c17711d2647e22f8a4d4ba57 origin/live-defi-rollout` succeeds.
- GCE `instances describe` reports creation `2026-08-16T19:50:40.547-07:00`, status `RUNNING`, and run tag
  `20260817-025031`.
- `launch-mtds-live-cefi-consolidated.sh` invokes tarball freshness verification before launch; the startup path
  installs tarballs once from GCS.
