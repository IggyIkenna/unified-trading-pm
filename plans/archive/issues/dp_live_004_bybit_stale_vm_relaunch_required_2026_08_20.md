---
doc_type: issue
title: DP-LIVE-004 BYBIT-FUTURES remains on a pre-fix live VM
summary: The active consolidated CeFi VM still runs the pre-5f88715e4b MTDS image, so BYBIT-FUTURES book_snapshot_5 remains unproductive until a safe VM cycle.
status: superseded
superseded_by: [dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20]
nature: process
asset_group: [cefi]
stage: [meta]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [data-pipeline, DP-LIVE-004, bybit-futures, stale-vm, live-capture]
related:
  [
    /plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-08-20
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P1
source: [DP-LIVE-004, agt-0d8048]
locked_by:
resolved_by:
context_scope:
  [
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh,
  ]
---

> **SUPERSEDED 2026-08-21 (ag-closeout-audit cefi tranche, Phase 3 sweep)**: consolidated into
> `/plans/active/issues/dp_live_004_stale_mtds_vm_pre_fix_image_2026_08_20.md` — same VM
> (`mtds-live-cefi-consolidated-20260817-025031`), same root cause (`5f88715e4b`), same recommended action. This
> doc's own evidence/detail is kept for provenance; the tracked `- [ ]` todos live on the canonical doc now.

## What I found

The DP-LIVE-004 finding names `mtds-live-cefi-consolidated-20260817-025031`,
`BYBIT-FUTURES`, and `book_snapshot_5`. The VM is RUNNING in
`asia-northeast1-c`, with all four BYBIT stream processes alive. Its BYBIT log
file mtimes were current during inspection, so this is not a dead or stale VM.

The MTDS root-cause fix is already shipped as
`market-tick-data-service@5f88715e4b`: it filters the IS-resolved BYBIT
universe to `PERPETUAL`/`FUTURE` before subscription. The named VM was created
on 2026-08-16/17, while the current `mtds-code.tar.gz` was refreshed on
2026-08-20; the VM therefore cannot contain that later fix.

## Why it matters

Force-launching would create a duplicate consolidated CeFi VM while the
current one is actively writing the other CeFi streams. Deleting or stopping
the current VM without an operator decision would destroy live capture from
those productive shards. The stale-image fix requires a controlled cycle of
the singleton VM, followed by STARTED/progress and captured-row verification.

## Recommended decision

Cycle the singleton through
`deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh` only
after the operator confirms the maintenance action and the current VM's
productive-shard handoff. Do not use `--force` while the current VM is RUNNING.
After the new VM is STARTED, verify a real BYBIT-FUTURES `captured` row in its
per-VM manifest shard before closing the DP-LIVE-004 follow-up in
`/plans/active/cross_ag_live_capture_parity_2026_08_14.md`.

## Evidence

- Current VM: `mtds-live-cefi-consolidated-20260817-025031`, RUNNING,
  `asia-northeast1-c`, created 2026-08-16T19:50:40Z.
- Current VM BYBIT log mtimes: 2026-08-20T22:19Z during inspection.
- Fix commit: `market-tick-data-service@5f88715e4b`.
- Current tarball object: `mtds-code.tar.gz`, refreshed 2026-08-20T22:15Z.
