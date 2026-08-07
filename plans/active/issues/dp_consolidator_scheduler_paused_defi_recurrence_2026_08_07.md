---
doc_type: issue
title:
  DP_CONSOLIDATOR_SCHEDULER_PAUSED recurred for the defi cron — retroactive maintenance-window registered (2026-08-07)
summary: >-
  Escalation triage (escalation agt-ca5798, wall_type=data_pipeline_failure) for a CRITICAL
  DP_CONSOLIDATOR_SCHEDULER_PAUSED (DP-WATCHER-004) page on `uts-prod-manifest-consolidator-market-data-defi-cron`. Same
  false-positive-by-current-design class as the resolved
  `dp_consolidator_scheduler_paused_{tradfi,prediction}_recurrence_2026_07_31.md` siblings: the cron was paused
  (`unified-trading-sa`, `2026-08-06T20:16:52Z`, raw `gcloud`, no maintenance window registered) while
  `canonical-migration-defi-rebuild-20260806-223130` (SPOT VM, `rebuild_defi_manifest --chunk-days 90` over
  2020-01-01..2026-12-31, launched per the R3 relaunch chain in
  `/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`) was/is genuinely LIVE and actively writing
  per-VM shards to the defi manifest. Registered a retroactive maintenance window via the sanctioned
  `scheduler_maintenance` CLI (no code change, no `git push`; a live GCS CAS write) so the page stops recurring for the
  remainder of the VM's run, mirroring the tradfi/prediction fix exactly and explicitly NOT resuming the cron (the
  tradfi doc's own self-correction lesson: resuming mid-rebuild would race a live canonical-writing VM).
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer]
tags: [data_pipeline_failure, dp-alerts, consolidator, maintenance-window, scheduler, false-positive-by-design]
related:
  [
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/archive/issues/dp_consolidator_scheduler_paused_tradfi_recurrence_2026_07_31.md,
    /plans/archive/issues/dp_consolidator_scheduler_paused_prediction_recurrence_2026_07_31.md,
    /plans/archive/issues/dp_watcher_003_consolidator_scheduler_paused_maintenance_window_gap_2026_07_29.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-08-07
parent_epic: manifest_master
assigned_vm: planning
locked_by:
priority: P2
source: >-
  data_pipeline_failure escalation agt-ca5798 (dp-fleet-monitor → slot-5), CONTEXT: "CRITICAL
  DP_CONSOLIDATOR_SCHEDULER_PAUSED (DP-WATCHER-004) — manifest-consolidator scheduler
  'uts-prod-manifest-consolidator-market-data-defi-cron' is PAUSED (not -legacy-)."
resolved_by: slot-5 (dp_consolidator_scheduler_paused_defi_recurrence-001, 2026-08-07)
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-07
---

# DP_CONSOLIDATOR_SCHEDULER_PAUSED recurrence — defi cron (2026-08-07)

## What I found

1. **Live GCP state**: `uts-prod-manifest-consolidator-market-data-defi-cron` (`asia-northeast1`) = `PAUSED`,
   `userUpdateTime: 2026-08-06T20:16:52Z`. `market-data-tick-defi-prd-central-element-323112`'s maintenance-window CLI
   (`scheduler_maintenance status`) read "no live window — safe to pause/resume freely" at escalation time.
2. **Cloud Audit Logs** (Admin Activity, `protoPayload.resourceName:"...market-data-defi-cron"`, 7d window) show a busy
   pause/resume history 2026-08-04..08-06 from three principals — `ikenna@odum-research.com` (operator manual dry-runs),
   `1060025368044-compute@developer.gserviceaccount.com` (a VM's own service account), and `unified-trading-sa` (the
   ambient identity most worker sessions and launched VMs run as). The relevant tail:
   - `2026-08-05T19:21:54Z` PauseJob (`unified-trading-sa`) — this is the already-resolved `mtds_available_at_backfill`
     defi apply's OWN pause (matches the archived plan's Progress Log: window registered same window, resume script
     `mtds_available_at_backfill_resume_defi_2026_08_05.py`).
   - `2026-08-05T23:34:24Z` ResumeJob (`unified-trading-sa`) — that resume script firing after
     `rebuild_defi_available_at` run-3 completed cleanly (matches the archived plan's "Run-3 progress... ETA
     ~22:10-22:15 UTC" entry). This resume released the earlier window, explaining why `status` now reads "no live
     window."
   - `2026-08-06T14:54:39Z` / `15:52:50Z` — an unrelated short pause/resume cycle by the compute-SA VM identity (not
     followed up further; job was left `ENABLED` afterward, consistent with the canonical index's
     `consolidator_content_write_at` climbing normally through `2026-08-06T20:03:48Z`).
   - **`2026-08-06T20:16:52Z` PauseJob (`unified-trading-sa`) — the CURRENT, still-active pause. No matching ResumeJob
     since.**
3. **Correlated the current pause to genuinely live, plan-tracked work, not an accidental leftover.**
   `/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s R3 relaunch chain (same day, 2026-08-06) ran
   two `canonical-migration-defi-per-instrument-*` VMs that both OOM'd on the per-year discovery listing (`-165240` at
   17:30Z, `-175529` at 18:30Z — DP-VM-003, a separate `data_pipeline_failure` escalation agt-ef3dd8), then per the
   runbook's "re-fails the same way twice → stop relaunching, fix root cause" clause, launched
   `canonical-migration-defi-rebuild-20260806-223130` (SPOT, e2-standard-8) running `rebuild_defi_manifest` ALONE
   (`--chunk-days 90`, full 2020-01-01..2026-12-31 range, own PROGRESS-checkpointed resume) — the remaining Track-8
   collector-resume gate piece. **Confirmed still RUNNING** (`gcloud compute instances list`) and **actively writing**:
   its `run.log`
   (`gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-rebuild-20260806-223130/run.log`)
   shows steady `ManifestWriter: per-VM shard updated (...)` lines against
   `market-data-tick-defi-prd-central-element-323112/_index/per_vm/canonical-migration-defi-rebuild-20260806-223130.parquet`
   through at least `2026-08-07T00:18:36Z`, still scanning forward from `date=2021-08-30` (early in the 7-year range —
   this run has a long remaining runway).
4. **Did not resume.** Per the tradfi sibling's own self-correction lesson (resuming a paused consolidator cron without
   first confirming no live protected operation depends on the pause), and given a currently-RUNNING canonical-rewrite
   VM is directly correlated to the pause timestamp, resuming here would risk racing
   `canonical-migration-defi-rebuild`'s in-flight write — the correct remedy is registering the window, not restoring
   the cron.

## Why it matters

Fourth occurrence of the same false-positive-by-current-design DP-WATCHER-004 shape (tradfi + prediction 2026-07-29,
prediction + tradfi recurrences 2026-07-31, now defi 2026-08-07) — the watcher correctly cannot distinguish a
plan-tracked, protocol-following pause from a genuinely accidental one when the pause is issued via raw `gcloud` instead
of the sanctioned `scheduler_maintenance` CLI. The registry_id collision this class of incident originally also surfaced
(DP-WATCHER-003 vs `DP_FLEET_MONITOR_RUN_FAILED`) is **already fixed** — this escalation's own CONTEXT correctly cites
`DP-WATCHER-004`, confirming the 2026-07-31 fix (`unified-api-contracts@02071c9f`, `deployment-service@bd9e962`) is
holding. No new registry gap found this pass. The recurring theme across all four incidents remains the SAME: ad-hoc
infra VM launches / dry-run sessions pause this cron via raw `gcloud` instead of `pause_for_maintenance()`, so each one
needs a reactive retroactive registration. The 2026-07-31 tradfi doc already filed a P3 follow-up to retrofit the
`mtds_available_at_cross_asset_backfill` plan's own pause actions; this occurrence's pauser is a DIFFERENT script (the
`defi_track01_per_instrument_and_canon_id` VM-launch chain, not the `mtds_available_at_backfill` scripts), so that
existing P3 follow-up does not cover it — a fully general fix would need every VM-launch script across the workspace
that pauses a consolidator cron to route through the CLI, which is out of scope for a one-shot escalation.

## What I did

Registered a maintenance window covering the still-paused job (pure GCS CAS write via the already-shipped
`deployment_service.data_pipeline_monitors.scheduler_maintenance` CLI — no code change, no new commit to a service
repo):

```
$ GCP_PROJECT_ID=central-element-323112 .venv/bin/python -m deployment_service.data_pipeline_monitors.scheduler_maintenance \
    --bucket market-data-tick-defi-prd-central-element-323112 \
    pause --surface market-data-defi \
    --job uts-prod-manifest-consolidator-market-data-defi-cron \
    --reason "defi_track01_per_instrument_and_canon_id_2026_07_24 canonical-migration-defi-rebuild-20260806-223130
              (rebuild_defi_manifest --chunk-days 90, 2020-01-01..2026-12-31) is LIVE and actively writing per-VM
              shards to the defi manifest as of 2026-08-07T00:18Z -- registering retroactive maintenance window
              (escalation agt-ca5798, DP-WATCHER-004) rather than resuming, mirroring the tradfi/prediction
              self-correction precedent: resuming mid-rebuild would race a live canonical-writing VM. Job paused
              since 2026-08-06T20:16:52Z by unified-trading-sa, never registered." \
    --locked-by defi_track01_per_instrument_and_canon_id_2026_07_24 \
    --ttl-minutes 4320
[maintenance-window] acquired + paused ['uts-prod-manifest-consolidator-market-data-defi-cron'] until 2026-08-10T00:20:24Z
```

Verified post-write: `scheduler_maintenance ... status` reads back
`HELD by 'defi_track01_per_instrument_and_canon_id_2026_07_24'` covering exactly this job;
`gcloud scheduler jobs describe` confirms the job itself is unchanged (`state: PAUSED`, `userUpdateTime` still
`2026-08-06T20:16:52Z` — the CLI's own re-issued pause call was a no-op on an already-paused job, matching the
tradfi/prediction precedent exactly). Did NOT resume the cron, did NOT touch the running VM, did NOT ship any code.

`--locked-by` deliberately names the owning plan (`defi_track01_per_instrument_and_canon_id_2026_07_24`) rather than a
specific resume script (unlike the `mtds_available_at_backfill` lanes, this VM-launch chain has no dedicated
`resume_defi_*.py` script to match against) — whoever next verifies `canonical-migration-defi-rebuild-20260806-223130`
completed should resume the cron manually
(`scheduler_maintenance ... resume --job uts-prod-manifest-consolidator-market-data-defi-cron --locked-by defi_track01_per_instrument_and_canon_id_2026_07_24`)
and force-consolidate to absorb the accumulated per-VM shards, rather than waiting for the window to merely expire.

TTL chosen as 3 days (4320 min), matching the tradfi/prediction precedent's reasoning: the rebuild VM had only reached
2021-08-30 of a 2020-2026 range after ~1h47m of runtime at escalation time, so its total runway is uncertain and
plausibly multi-day; long enough to plausibly cover it without permanently blinding the watcher, and an expiry before
the VM finishes will correctly re-page rather than silently suppress forever.

## Recommended decision

No further paging-remediation action needed — resolved for the remainder of the rebuild VM's realistic runway. One
follow-up worth tracking (not fixed here, per one-shot escalation scope): a general fix routing every VM-launch script
across the workspace that pauses a manifest-consolidator cron through `pause_for_maintenance()` at pause time (not just
resume time) would close this recurring gap at the source instead of needing a reactive retroactive registration each
time a different launch chain hits it. Left as a P3 idea, not filed as a todo — the "every VM launcher" scope is too
broad to bound without an owning audit pass.

## Todos

- [x] ✅ [OPS] P1. **Registered a retroactive maintenance window for the defi cron — DONE live 2026-08-07T00:20:24Z.**
      No code shipped; pure infra action (sanctioned `scheduler_maintenance` CLI CAS write). Verified:
      `scheduler_maintenance ... status` reads `HELD by 'defi_track01_per_instrument_and_canon_id_2026_07_24'` until
      `2026-08-10T00:20:24Z`; `gcloud scheduler jobs describe` still reads `PAUSED`, `userUpdateTime` unchanged
      (2026-08-06T20:16:52Z — confirms the pause itself was untouched, only the window was registered). Correlated the
      pause to a confirmed-live `canonical-migration-defi-rebuild-20260806-223130` VM actively writing per-VM shards to
      the defi manifest at escalation time. (repo: NA)
