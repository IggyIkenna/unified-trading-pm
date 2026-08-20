---
doc_type: issue
title: >-
  DP_CRON_DID_NOT_FIRE false-fires hourly for dp-exit-code-monitor — MONITOR_CRON_CADENCE_MIN["exit-code"]
  never updated when the live cron cadence was reconciled from */5 to hourly
summary: >-
  A CRITICAL DP_CRON_DID_NOT_FIRE (DP-WATCHER-002) escalation (agt-582c52) named cron 'dp-exit-code-monitor',
  "last output 34m ago". Live-verified the cron is genuinely healthy: `uts-prod-dp-exit-code-monitor-cron`
  is ENABLED, hourly (`0 * * * *`), and its last 8 `gcloud run jobs executions list` rows all completed
  successfully in 48s-2m26s. This is NOT the already-tracked alerting-service redeploy-wipes-dedup bug
  (`dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md`) — that fix (alerting-service@f48a61193f)
  is confirmed live in the currently-serving revision (content-verified: commit 08c5f39, image digest
  sha256:7c52789c..., built 2026-08-19T06:14:26Z, deployed as dp-alerting-subscriber-00130-cwn at
  06:16:07Z) and this alert's own cadence (once per hour, at :35-36Z, "34-36m ago" every single time —
  a `slack-read-channel.py data-pipeline-alerts 6` sweep found it fired at 02:35, 03:36, 04:35, 05:36,
  06:35, 07:36Z, i.e. every cycle) is consistent with a genuinely-true underlying condition gated by the
  renag cooldown, not a dedup-defeat re-fire storm.

  Root cause (NEW, distinct): `meta_watchers.MONITOR_CRON_CADENCE_MIN["exit-code"]` is hardcoded `5.0`
  (documented as `*/5`), giving the DP-WATCHER-002 freshness budget `max_age_min = 2 * 5 = 10.0` minutes
  for both (a) the sentinel-staleness check AND (b) the KEY #4 execution-history cross-check
  (`check_cron_fired` line ~859: `last_success_age <= target.max_age_min`) that is supposed to suppress
  a stale-sentinel false positive when the Cloud Run Job's real execution history shows a recent SUCCEEDED
  run. But the LIVE cron cadence has been hourly since the 2026-08-14 sweep-overlap-storm reconciliation
  (`/plans/archive/2026_08/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`'s "Reconcile the schedule discrepancy" todo,
  closed 2026-08-14 — that todo corrected the PLAN's stale `*/5` claim but never touched this code
  constant). At hourly cadence, the job's last-success age at meta-sweep check time (meta itself runs
  `*/15`) is routinely 15-59 minutes — always exceeding the stale 10-minute budget — so the KEY #4
  cross-check can NEVER suppress, and the alert fires as a genuine "miss" on every sweep past the
  `min_consecutive=2` onset gate, re-paging on the renag cooldown (~hourly cadence match is consistent
  with a ~30min cooldown gating a condition that's true every ~15min sweep).

  A THIRD, separate but related drift was found and deliberately NOT fixed here: terraform
  (`terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`, `dp_exit_code_monitor_cron` resource) still
  DECLARES `schedule = "*/5 * * * *"`, undeployed against the live hourly schedule. Applying that
  terraform would revert the live cron back to */5 and reopen the entire multi-week sweep-overlap/OOM
  storm this doc's sibling issues fought through (`/plans/archive/2026_08/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`,
  `dp_exit_code_monitor_oom_signal9_2026_08_09.md`) — flagged for a human/operator IaC-reconciliation
  pass, not touched by this fix.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [alerting, data-pipeline-monitors, dp-watcher-002, cron-freshness, false-positive, terraform-drift]
related:
  [
    /plans/active/issues/dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md,
    /plans/archive/2026_08/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md,
    /plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-08-19
author: data_pipeline_failure (slot 33, escalation agt-582c52)
parent_epic: observability_master
priority: P1
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-19
locked_since:
archive_exempt:
context_scope:
  [
    deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py,
    /plans/active/issues/dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md,
    deployment-service/terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf,
    deployment-service/cloud-build/deployment-service-jobs-image.cloudbuild.yaml,
  ]
source: >-
  data_pipeline_failure escalation agt-582c52 — CRITICAL DP_CRON_DID_NOT_FIRE (DP-WATCHER-002) naming
  cron 'dp-exit-code-monitor' (no issue slug at dispatch — alert-carries-the-details path).
---

# DP_CRON_DID_NOT_FIRE false-fires hourly for dp-exit-code-monitor — stale cadence constant

## What was found

Live-verified (2026-08-19, ~08:00-08:20Z):

- `gcloud scheduler jobs describe uts-prod-dp-exit-code-monitor-cron`: `ENABLED`, `schedule=0 * * * *`
  (hourly).
- `gcloud run jobs executions list --job=uts-prod-dp-exit-code-monitor` (last 8 rows, 02:00Z-08:00Z):
  every execution `Execution completed successfully` in 48.7s-2m26.4s. The cron is genuinely healthy.
- `slack-read-channel.py data-pipeline-alerts 6` (6h window): `[DP_CRON_DID_NOT_FIRE] cron
  'dp-exit-code-monitor' did not fire on schedule (last output 34-36m ago)` fired at 02:35Z, 03:36Z,
  04:35Z, 05:36Z, 06:35Z, 07:36Z — every ~60min, "last output" value barely varying (34-36m) — the
  signature of a condition that is TRUE every check, gated to roughly-hourly delivery by the renag
  cooldown, not an intermittent real staleness event.
- `dp-alerting-subscriber` currently serves revision `-00130-cwn` (deployed 06:16:07Z, image digest
  `sha256:7c52789c...`, commit `08c5f39` — content-verified to contain the `RecurringCooldownState`
  dedup-persistence fix from `dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md`, 3
  references to `RecurringCooldownState` in `router.py` at this commit). That fix is live; this alert's
  root cause is upstream of it, in the detector's own freshness budget.

## Root cause

`deployment_service/data_pipeline_monitors/meta_watchers.py::MONITOR_CRON_CADENCE_MIN["exit-code"]` was
hardcoded `5.0` (`*/5`). `monitor_cron_targets()` derives `max_age_min = 2.0 * cadence_min = 10.0` for the
`dp-exit-code-monitor` `FreshnessTarget`, and `check_cron_fired`'s KEY #4 execution-history cross-check
(the mechanism specifically built 2026-06-23 to suppress exactly this "sentinel stale but the job IS
firing" false-positive class) compares the job's real last-success age against that SAME budget
(`last_success_age <= target.max_age_min`). Since the live cron has run hourly since 2026-08-14 (per the
sibling sweep-overlap doc's "Reconcile the schedule discrepancy" todo — that todo corrected only the
PLAN's stale claim, never this code constant), the job's last-success age at any 15-minute-cadence
meta-sweep check is routinely >10min, so KEY #4 can never suppress and the alert fires as a genuine
"miss" every cycle past onset.

## Fix

`deployment-service@<pending>`: `MONITOR_CRON_CADENCE_MIN["exit-code"]` changed `5.0 -> 60.0` (budget
`10.0 -> 120.0` min), matching the live hourly cadence with the same 2x-cadence margin every other entry
uses. Updated the one existing test asserting the stale value
(`tests/unit/test_data_pipeline_deadman.py::test_monitor_cron_targets_one_per_mode`,
`max_age_min == 10.0  # 2 * 5` -> `== 120.0  # 2 * 60`). Scoped to `exit-code` only — `heartbeat`
(confirmed live `*/5 * * * *`) and `meta` (confirmed live `*/15 * * * *`) cadences are still correct,
verified via `gcloud scheduler jobs list` this session, not touched.

## Deliberately NOT fixed — terraform drift (flagged, not applied)

`terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf`'s `dp_exit_code_monitor_cron` resource still
declares `schedule = "*/5 * * * *"`, which does not match the live `0 * * * *` schedule. This is
almost certainly the SAME live-vs-IaC drift the 2026-08-14 sweep-overlap-storm fix chain left behind
(the schedule was changed live during that firefight and the terraform file was never backported —
mirrors the identical pattern already documented for the job's resource sizing in
`dp_exit_code_monitor_oom_signal9_2026_08_09.md`'s todo 2). Applying this terraform file as-is would
revert the live cron back to `*/5`, which would very likely reopen the multi-session sweep-overlap/OOM
storm both sibling issue docs fought through — NOT attempted here; needs a deliberate operator-aware
IaC-reconciliation pass (backport `0 * * * *` into the terraform file, matching the sizing-drift
backport precedent already used for this same job), not a same-session escalation-worker fix.

## Todos

- [x] [SCRIPT] P1. ✅ Fix `MONITOR_CRON_CADENCE_MIN["exit-code"]` (5.0 -> 60.0) + update the two
      dependent test fixtures (the third existing test only asserted `max_age_min == 10.0`, also
      updated to `120.0`). Evidence: `deployment-service@dc6ac3d7eb`, `quality-gates.sh --no-fix`
      ALL PASSED (238s, 3647 passed), landed on `live-defi-rollout`, post-push ancestry verified.
      Repo: deployment-service.
- [ ] [INFRA] P2. Backport the live `0 * * * *` schedule for `dp_exit_code_monitor_cron` into
      `terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf` (currently declares stale `*/5 * * * *`)
      — mirrors the sizing-drift backport already done for this same job in
      `dp_exit_code_monitor_oom_signal9_2026_08_09.md`. Do NOT `terraform apply` the file as-is; the
      backport must land the LIVE value into the file, never the reverse. Repo: deployment-service.
- [x] [SCRIPT] P2. ✅ **RESULT: the fix had NEVER actually deployed — a distinct root cause, now
      fixed.** A follow-on escalation (agt-63b255, slot 16, dispatched off the SAME alert firing again
      at 13:xxZ) found `dc6ac3d7eb` was on `live-defi-rollout` but the Cloud Run Jobs that actually run
      the meta/exit-code/heartbeat sweeps (`uts-prod-dp-exit-code-monitor`, `uts-prod-dp-heartbeat-watcher`,
      `uts-prod-dp-meta-watchers`) run off `deployment-service:latest`, built ONLY by
      `cloud-build/deployment-service-jobs-image.cloudbuild.yaml` — a config with NO Cloud Build trigger
      wired to it (confirmed: `gcloud builds triggers list` has no match), so a fix landing on
      `live-defi-rollout`/`main` never reaches these jobs unless someone manually runs
      `gcloud builds submit --config=...`. Content-verified the live job image
      (`deployment-service@sha256:d487e016e43d...`, pulled + grepped) still had `"exit-code": 5.0` — the
      SOURCE fix was real but never deployed. Fixed by manually triggering the build
      (`gcloud builds submit --config=cloud-build/deployment-service-jobs-image.cloudbuild.yaml
      --region=asia-northeast1 --substitutions=_GIT_SHA=3fedc96`), build `67e76f2d-3930-4f71-b391-a43402e06f03`
      SUCCESS (asia-northeast1, ~13:49-13:55Z) — Evidence: cloudbuild=67e76f2d-3930-4f71-b391-a43402e06f03.
      Its `redeploy-jobs` step re-resolved all 8 dependent Cloud Run Jobs (incl. the 3 named above) to
      the freshly-pushed `:latest`, no `WARN:` lines in the build log. Content-verified post-deploy: a
      fresh pull of `deployment-service:latest` (digest `sha256:1b7f25a3a1a3...`) now has
      `"exit-code": 60.0`. The "34-36m ago, every ~60min" signature should now genuinely stop (not just
      slow down) on the job's next `*/15` meta sweep. Repo: deployment-service (no source change — a
      deploy-only fix; the source fix was already correct).
- [ ] [INFRA] P2. **ADDED 2026-08-19 (agt-63b255, slot 16)** — the systemic gap behind the above: NOTHING
      auto-deploys `cloud-build/deployment-service-jobs-image.cloudbuild.yaml` on a `deployment_service/`
      change landing on `main`/`live-defi-rollout` — it is manual-only (`gcloud builds submit`), unlike
      most other services' Cloud Build configs which fire off a push trigger. This is exactly the failure
      shape this doc's own fix just fell into: a correct source fix that silently never reached the
      Cloud Run Jobs consuming it, discovered only because the SAME alert re-fired and a second escalation
      happened to content-verify the live job image instead of trusting the git landing. Wire a Cloud
      Build trigger (push to `main`, path-filtered to `deployment_service/**` + the cloudbuild file itself,
      mirroring whatever trigger pattern `deployment-api`'s own auto-deploy uses) so this class of gap
      cannot recur silently. Repo: deployment-service.

## Progress Log

- 2026-08-19 (data_pipeline_failure escalation worker, slot 33, agt-582c52): dispatched off a CRITICAL
  `DP_CRON_DID_NOT_FIRE` naming cron `dp-exit-code-monitor` (no issue slug). Checked the already-open
  `dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md` first (a near-identical prior
  escalation, agt-b66b27, answered the exact same symptom earlier today by shipping the
  `RecurringCooldownState` dedup-persistence fix) — confirmed that fix IS live (content-verified in the
  current serving revision) and confirmed the cron itself is genuinely healthy (scheduler ENABLED
  hourly, last 8 executions all successful). The repeat-every-hour, near-constant-"34-36m ago" pattern
  did not fit that doc's redeploy-wipes-dedup mechanism (which produces 15-17min irregular re-fires
  tied to redeploy timing, not a metronomic ~60min cadence), so traced the detector's own freshness
  logic instead: found `MONITOR_CRON_CADENCE_MIN["exit-code"]` still hardcoded to the pre-2026-08-14
  `*/5` cadence, feeding both the sentinel-staleness check AND the KEY #4 execution-history suppression
  cross-check with a 10-minute budget the hourly job can never satisfy. Fixed the constant (60.0),
  updated the one dependent test, filed this doc (a genuinely distinct root cause from the dedup-defeat
  bug, findings-triage: file a fresh issue rather than folding an unrelated mechanism into an
  already-scoped doc). Flagged but did NOT touch the terraform schedule drift (`*/5` declared vs `0
  * * * *` live) — applying it would revert the live cron and risk reopening the sweep-overlap storm.

- 2026-08-19 (data_pipeline_failure escalation worker, slot 16, agt-63b255): dispatched off the SAME
  `DP_CRON_DID_NOT_FIRE`/`dp-exit-code-monitor` alert firing again ("last output 34m ago"), context
  carried no issue slug. Grepped `plans/active/issues/` per the pre-task conflict-check rule and found
  this doc already open with an unchecked "live-verify the fix deployed" todo — read it first rather
  than re-diagnosing from scratch. Confirmed `dc6ac3d7eb` genuinely landed on `live-defi-rollout` (git
  log), then checked whether it reached the RUNTIME: `uts-shared-deployment-api` (Cloud Run Service) DOES
  have the fix live, but that is the WRONG resource — the actual meta/exit-code/heartbeat sweeps run as
  separate Cloud Run JOBS (`uts-prod-dp-meta-watchers` etc.) off a DIFFERENT image, `deployment-service:latest`,
  built only by `cloud-build/deployment-service-jobs-image.cloudbuild.yaml`. Content-verified (docker pull +
  grep inside the container, not a SHA-ancestor check — this doc's own established discipline) that image
  still shipped `"exit-code": 5.0` — the fix had never been rebuilt/redeployed to it, because that
  cloudbuild config has no CI trigger (`gcloud builds triggers list` confirmed no match) and nothing else
  runs it automatically. Manually ran `gcloud builds submit --config=cloud-build/deployment-service-jobs-image.cloudbuild.yaml
  --region=asia-northeast1 --substitutions=_GIT_SHA=3fedc96`; build `67e76f2d-3930-4f71-b391-a43402e06f03`
  reached `SUCCESS` (~6 min), its `redeploy-jobs` step re-resolved all 8 dependent Cloud Run Jobs to the
  fresh `:latest` with zero WARN lines. Re-pulled `deployment-service:latest` post-build (digest
  `sha256:1b7f25a3a1a3...`) and confirmed `"exit-code": 60.0` now live. Checked off todo 3 with this
  evidence and added a new P2 todo for the systemic gap (no CI trigger on this cloudbuild config) so the
  same "source fix silently never reaches the runtime" failure mode does not recur on the next fix to
  this file. Did not touch the terraform-drift todo (unrelated, still open, unchanged scope). No code
  changed this session — deploy-only fix, since the source fix from the prior session was already correct.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
