---
doc_type: issue
title: DP-LIVE-004 BYBIT-FUTURES book capture runs a pre-fix MTDS image
summary: >-
  The flagged BYBIT-FUTURES book_snapshot_5 shard runs on a VM created 2026-08-17,
  before market-tick-data-service@5f88715e4b landed on 2026-08-18. Read-only SSH
  inspection confirms the deployed connector still subscribes the unfiltered IS
  universe, so a fresh relaunch is required before judging the shipped fix.
status: open
nature: process
asset_group: [cefi]
stage: [live]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [data-pipeline-alerts, dp-live-004, bybit-futures, stale-vm-image, live-capture]
related:
  [
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/dp_live_004_bybit_futures_book_snapshot_unproductive_2026_08_21.md,
    /plans/archive/issues/dp_live_004_bybit_stale_vm_relaunch_required_2026_08_20.md,
    /plans/archive/issues/dp_live_004_bybit_vm_stale_tarball_2026_08_20.md,
  ]
created: 2026-08-20
author: data_pipeline_failure (slot 32, escalation agt-0d8048)
parent_epic: security_and_cross_cutting_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-20
locked_since:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/connectors/bybit_ws.py,
    market-tick-data-service/market_tick_data_service/live/connectors/bybit_futures_book_ticker_ws.py,
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
source: DP-LIVE-004 / DP_CRON_DID_NOT_FIRE (mtds-live-cefi-consolidated-20260817-025031, BYBIT-FUTURES, book_snapshot_5)
---

# DP-LIVE-004 BYBIT-FUTURES book shard is running a pre-fix image

> **CONSOLIDATED 2026-08-21 (ag-closeout-audit cefi tranche, Phase 3)**: this is the same incident as 3 sibling
> docs, filed independently by 4 different escalation dispatches, none cross-referencing each other, all naming the
> identical VM (`mtds-live-cefi-consolidated-20260817-025031`), the identical root cause (stale runtime predates
> `market-tick-data-service@5f88715e4b`), and the identical recommended action (cycle the VM through the registered
> launcher, then verify a real captured row). This doc is now the CANONICAL one (it already carried the correct
> `assigned_vm: planning` / `execution_scope: orchestrator-agent` dispatch frontmatter; the other 3 were either
> `execution_scope: local-only` or a stale `assigned_vm: vm-cross-cutting` legacy value that the single-VM AO
> ingestion path does not match, so none of them were actually reachable by AO dispatch). The other 3 are marked
> `status: superseded` and redirected here — their own evidence/detail is kept, not deleted:
> `/plans/active/issues/dp_live_004_bybit_futures_book_snapshot_unproductive_2026_08_21.md`,
> `/plans/archive/issues/dp_live_004_bybit_stale_vm_relaunch_required_2026_08_20.md`,
> `/plans/archive/issues/dp_live_004_bybit_vm_stale_tarball_2026_08_20.md`. A single consolidated Todos section
> (below) replaces the 4 separate un-dispatched recommendations.

## What was found

The flagged VM `mtds-live-cefi-consolidated-20260817-025031` is `RUNNING` in
`asia-northeast1-c`, created at `2026-08-17T02:50:40Z`. Its root-owned book process
started at `2026-08-17 02:52:18 UTC`. The MTDS fix
`5f88715e4bdf7fc0c17711d2647e22f8a4d4ba57` landed at `2026-08-18 10:49:19 UTC`.

Read-only SSH inspection of the deployed source at
`/home/ikennaigboaka/workspace/mtds` found:

- `bybit_ws.py` has no `_is_linear_derivative` helper.
- `bybit_futures_book_ticker_ws.py` still assigns
  `self._instrument_ids = set(instrument_ids)` in the book connector.
- The slot's `live-defi-rollout` origin contains the fix, which filters the
  IS-resolved BYBIT catalog to `PERPETUAL`/`FUTURE` before constructing topics.

Therefore this alert is explained by stale deployment state: the process has
never loaded the shipped fix. The source fix is present and does not need a
second code change.

## Why it matters

The VM continues producing `attempted` activity and manifest updates, so it is
not a dead process, but its pre-fix connector can continue subscribing the
unfiltered BYBIT catalog and yield zero captured rows. The existing plan's
fresh-relaunch verification must run before this DP-LIVE-004 condition can be
closed.

## Recommended decision

Use the registered CEFI live forward-poll relaunch path to replace the stale
VM with a current MTDS tarball. Do not terminate this healthy live VM from the
alert-triage worker. After the fresh VM starts, verify the deployed source (or
revision) contains the filter and verify at least one real
`captured` BYBIT-FUTURES row for `book_snapshot_5`; then close the related
follow-up in `/plans/active/cross_ag_live_capture_parity_2026_08_14.md`.

## Todos

- [ ] [OPERATOR] P1. Cycle the singleton `mtds-live-cefi-consolidated-*` VM through the registered launcher
      (`deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh`) onto the current MTDS tarball (contains
      `market-tick-data-service@5f88715e4b`, the BYBIT-FUTURES subscribe-universe filter that excludes `SPOT_PAIR`).
      Controlled cutover only — do **not** `--force` while the current VM is RUNNING and do **not** stop/delete it
      until the replacement is verified (the launcher's singleton guard + the other CeFi streams it is actively
      writing depend on this). Done when: the replacement VM reaches `RUNNING` with a current code-provenance
      marker (tarball refreshed after 2026-08-20T22:15Z / contains `5f88715e4b` or a descendant).
- [ ] [DATA] P1. After the cycle, verify at least one real `captured` `BYBIT-FUTURES`/`book_snapshot_5` row in the
      new per-VM manifest shard (direct GCS/manifest read, never a fabricated/placeholder row). Never reclassify the
      existing all-`empty_confirmed`/`SOURCE_RETURNED_ZERO` rows without this proof. If the fresh runtime is still
      unproductive, inspect Bybit subscribe acknowledgements/rejections and file a follow-up code issue rather than
      muting DP-LIVE-004. Once verified, close the related follow-up in
      `/plans/active/cross_ag_live_capture_parity_2026_08_14.md`.

## Progress Log

- **ag-closeout-audit 2026-08-21 (cefi tranche, Phase 3 sweep)**: consolidated this doc's 3 sibling near-duplicates
  (identical VM + root cause + recommended action, filed by 4 independent escalation dispatches with zero
  cross-referencing) into this canonical doc — added `related:` links, a consolidation banner, and the 2 tracked
  `- [ ]` todos above (previously all 4 docs carried only unactionable prose "Recommended decision" text, and this
  doc specifically had zero `- [ ]` todos despite `assigned_vm: planning`, so nothing was actually dispatchable).
  Marked the 3 siblings `status: superseded` + `superseded_by:` pointing here, with their own evidence kept intact.
- 2026-08-20 (slot 32, escalation `agt-0d8048`): confirmed the MTDS worktree is
  clean and current on `live-defi-rollout`; inspected commit
  `5f88715e4b` and its book-connector tests; inspected the live VM and found the
  process and deployed source predate the fix. No code change was made because
  the root-cause fix is already shipped. The VM remains running; relaunch and
  post-relaunch captured-row verification are operator/infra follow-up work.
