---
doc_type: issue
title:
  "Re-check the consolidated CeFi live-capture VM's ASTER data landing after the 13:30 UTC daily instrument-catalogue
  refresh (2026-07-30)"
summary: >-
  mtds-live-cefi-consolidated-20260730-010147 was launched 2026-07-30 01:01 UTC with ASTER's book_snapshot_5 +
  liquidations shards folded in per the operator's 2026-07-28 ruling (infra_capture_and_devops_leftovers_2026_07_06.md).
  VM booted cleanly and all 17 shards are running, but every shard (ASTER and all 15 pre-existing venues alike) is
  waiting on today's instrument-availability catalogue, which instruments-service's daily scheduler
  (google_cloud_scheduler_job.is_daily_enum, schedule "30 13 * * *") had not yet produced at launch time. This is
  expected 300s-retry behavior, not a bug — needs a follow-up check after 13:30 UTC to confirm real data actually lands
  once the catalogue refreshes.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, instruments-service]
scope: [engineer]
tags: [cefi, aster, live-capture, verification, follow-up]
related:
  [
    /plans/active/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/archive/issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md,
  ]
created: 2026-07-30
priority: P2
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: "autonomous session 2026-07-30, VM launch + monitoring for infra_capture_and_devops_leftovers_2026_07_06.md"
resolved_by:
drift_direction: advance-code
---

# CeFi consolidated VM — ASTER data-landing re-check after 13:30 UTC

## What happened

Launched `mtds-live-cefi-consolidated-20260730-010147` (`asia-northeast1-c`, `e2-highmem-16`, on-demand) at
2026-07-30T01:01:47Z, folding ASTER `book_snapshot_5` + `liquidations` into the MVP shard list per the operator's
2026-07-28 ruling. Confirmed healthy:

- Boot + full setup completed in ~140s (well under the STARTED<60s-class check — this counts the whole dependency
  install + shard launch, not just VM creation).
- All 17 shards (15 pre-existing venues + 2 new ASTER) confirmed running via direct SSH `ps aux` — steady CPU
  accumulation, not crash-looping.
- **Every shard, ASTER included, is correctly logging `IS universe empty ... retrying in 300s`** because today's
  (2026-07-30) `instruments.parquet` does not exist yet under
  `gs://instruments-store-cefi-prd-central-element-323112/instrument_availability/by_date/day=2026-07-30/...` for ANY
  venue — confirmed via direct GCS listing that yesterday's (2026-07-29) equivalent exists for every venue including
  ASTER. Root cause: `deployment-service/terraform/gcp/daily_is_enumeration_scheduler.tf`'s
  `google_cloud_scheduler_job.is_daily_enum` runs at `30 13 * * *` (13:30 UTC) — it simply had not fired yet at 01:16
  UTC launch/check time. This is designed retry behavior, not a defect.

## Todos

> **✅ OWNERSHIP RESOLVED 2026-07-31 (corpus-wide ownership-conflict sweep, operator ruling keep-one-cite-the-other).**
> The near-verbatim "verify `live_aster` rows land" claim appeared in both this doc and
> `/plans/active/infra_capture_and_devops_leftovers_2026_07_06.md`'s `[DATA] P1`. **Split by phase, not deleted from
> either**: the infra plan OWNS _register + launch_ the ASTER live connector (its actual scope, and it holds all the
> prereq history); **THIS doc OWNS the post-launch data-landing verification** — it is newer (2026-07-30 vs 2026-07-06),
> carries the concrete dated command, and already declares itself the thing that flips the infra plan's checkbox. The
> infra plan's todo now cites this doc for the verification half instead of restating it.
>
> **Not verified this session, and deliberately not claimed either way**: the 2026-07-30T13:30Z re-check could not be
> run — `gcloud storage ls` failed reauth in this non-interactive slot for all three credentialed identities
> (`unified-trading-sa` has no valid credentials here; the operator account needs an interactive `gcloud auth login`).
> The todo stays `- [ ]`. Whoever picks it up runs the command below first; a fabricated "rows landed" is worse than an
> unrun check.

- [ ] [DATA] P2. **After 2026-07-30T13:30Z UTC**, re-check whether real rows are landing:
      `gcloud storage ls "gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2026-07-30/pipeline_mode=live_aster/**"`.
      If populated: flip `infra_capture_and_devops_leftovers_2026_07_06.md`'s ASTER-connector todo's remaining checkbox
      with this evidence, and archive/retire `issues/cefi_live_ws_capture_dormant_since_2026_06_29_2026_07_14.md` as
      resolved (both per that plan's own completion mandate). If still empty well past 13:30 UTC, treat as a genuine new
      bug (this doc's finding only explains absence BEFORE the catalogue refresh) and investigate the live shard logs
      fresh (SSH, `sudo tail -f /home/ikennaigboaka/logs/live-aster-*.log`) rather than assuming the same root cause
      applies.
- [ ] [DATA] P3. Spot-check 2-3 of the 15 pre-existing venues (e.g. HYPERLIQUID, BINANCE-FUTURES) the same way — they
      hit the identical empty-universe wait, so their data-landing should resume at the same time; confirms the fix is
      fleet-wide, not ASTER-specific relief only.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY candidate PARKED on conflict-check:
  `infra_capture_and_devops_leftovers_2026_07_06.md` (active, assigned_vm:planning) already carries the near-verbatim
  "verify `live_aster` rows land" claim, and this doc's own todo says to flip THAT plan's checkbox. Duplicate dispatch
  risk. Filed as BLOCKED-OPERATOR-DECISION in this run's Deferred list; `assigned_vm` unchanged.

## Progress Log (na-eligibility-audit)

- **na-eligibility-audit 2026-08-01** (tranche=cefi, autonomous): KEEP-NA, pending. Both open todos (ASTER recheck +
  2-venue spot-check) clear the bounded-outcome bar on their own merits (one `gcloud storage ls` command per venue,
  fully-specified branches) and the 2026-07-30 park reason (conflict with
  `infra_capture_and_devops_leftovers_2026_07_06.md`) is independently confirmed RESOLVED (that doc's verification-half
  checkbox now explicitly re-homes to this doc, 2026-07-31 banner). NOT reclassified this run because
  `cefi_satellite_ao_dispatch_batch4_2026_07_31.md` todo 2 already drafted this exact scope verbatim (Source-cited) —
  batch4 is `status: draft`, not active. Reclassifying independently now risks the same `gcloud storage ls` check being
  dispatched twice via two mechanisms once batch4 activates. Recommend: prefer batch4's operator-review/activation path
  over an independent flip here.
