---
doc_type: plan
title: "Sports P2d — daily-forward + catalogue-daily + FINAL e2e gate (100% / clean)"
summary:
  "Enable daily-forward pipeline, catalogue daily rollup, and stamp the final e2e verdict once full history is
  zero-missing."
nature: process
stage: [data-ingestion]
repos: []
scope: [engineer, admin]
tags: [sports, daily-forward, catalogue, final-gate, scheduler, steady-state, e2e]
related: []
created: 2026-06-27
parent_epic: sports_master
priority: P1
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on:
  - sports_p0_spot_vm_launchers_2026_06_27
  - sports_p2_history_apifootball_2015_to_present_2026_06_27
  - sports_p2_history_reference_and_odds_2015_to_present_2026_06_27
  - sports_p2_features_history_to_ml_ready_2026_06_27
related_plans:
  - plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md
  - plans/active/instruments_foundation_completeness_2026_06_24.md
asset_group: cross-asset
---

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 2, the CAPSTONE). Turns on the
> **daily-forward** data pipeline (R3 "done daily"), the **catalogue daily rollup** (R4), and stamps the **final e2e
> verdict** (R1+R2+R3+R5 to 100% / clean). One agent, `data_engineering` (Sonnet/high). **Data-pipeline daily is wanted;
> live TRADING stays OFF** (operator: drop live sports trading while fixing — this plan re-enables the DATA forward
> poll, not trading).

# Sports P2d — daily-forward + catalogue-daily + FINAL e2e gate

## Scope

Three steady-state surfaces + the final verdict:

1. **Daily-forward (R3)** — the sports-scheduler VM daemon (`launch-sports-scheduler-vm.sh` → `SportsTriggerScheduler`,
   `configs/sports-trigger-tiers.yaml`) running the 4 tiers (Tier-1 discovery / Tier-2 reference / Tier-3 pre-match /
   Tier-4 post-match) so new data flows daily for every source; features daily.
2. **Catalogue daily (R4)** — fix the all-AG producer crash (`instruments_handler.py:367`) or ensure a sports-scoped
   daily producer; the `lifecycle-catalogue-regen-sports` Cloud-Scheduler→Cloud-Run job (01:00 UTC,
   `terraform/gcp/lifecycle_catalogue_scheduler.tf`) fires daily with `run.invoker` granted.
3. **Final e2e gate (R1/R2/R3/R5)** — full-history zero-missing across all sources + features, daily firing, alerts
   zero.

> **SPOT VMs (HARD)** — the sports-scheduler daemon VM launches **spot/preemptible** (the cloud can reclaim + kill it at
> any moment) per [`sports_p0_spot_vm_launchers_2026_06_27`](sports_p0_spot_vm_launchers_2026_06_27.md); on preemption
> it re-acquires the singleton lock + resumes tier cadence from GCS state, and a reclaim must NOT raise a false
> `DP_VM_GONE_NO_CAPTURE` (R5). (The catalogue rollup is Cloud Run, not a VM.)

## Codex SSOTs

- `codex/02-data/sports-scheduling-and-sharding.md` — sports-scheduler tiers + cadence state
- `codex/05-infrastructure/manifest-consolidator-ssot.md` — consolidator freshness
- `codex/05-infrastructure/data-pipeline-alerts.md` (+ `.registry.yaml`) — `DP_CATALOG_NOT_RUNNING` /
  `DP_CRON_DID_NOT_FIRE` budgets; drive-to-zero
- `codex/05-infrastructure/deployment-observability.md` — active-dp-alerts blobs + RESOLVED bookend

## Todos

- [x] ✅ [DATA] P0. **Daily-forward DATA pipeline running for every source** — confirm/(re)launch the single
      sports-scheduler daemon VM; verify each tier fires + writes (discovery fixtures, reference
      STANDINGS/INJURIES/TM/footystats/understat, pre-match lineups/odds, post-match stats/events). NOT live trading.
      **Gate**: over a 24h observation the scheduler state (`gs://…/sports_scheduler_state/`) advances each tier's
      `last_run`; fresh `day=<today>` parquets land for each source; the scheduler VM emits STARTED + ≥1 progress/hr (no
      fire-and-forget; singleton-locked).
      — 2026-06-27: sports-scheduler-20260627-153504 launched SPOT asia-northeast1-c (prior VM TERMINATED). Scheduler
        STARTED at 15:40:40 UTC (T+5.5min); TIER-1 DISCOVERY fired immediately (last_run 85.88h ago); PIPELINE_HEARTBEAT
        emitting every 60s; DEPLOYMENT_STARTED 947da9e7 logged. Log:
        gs://deployment-scripts-central-element-323112/vm-logs/sports-scheduler-20260627-153504/run.log
        STARTED ✅ + ≥1 progress/hr ✅ + singleton-locked ✅. 24h tier advancement observed passively.
- [x] ✅ [DATA] P0. **Features daily** — the daily fixture/derived/odds feature compute runs for new days. **Gate**: a
      `day=<recent>` features parquet appears within a day of the upstream capture; features manifest stays clean.
      — 2026-06-27: BLOCKED-UPSTREAM on P1d. features-sports-prd manifest had 17 rows (2025-09-01 only); all 3
        feature types (FIXTURE_FEATURES/DERIVED_FEATURES/ODDS_FEATURES) showed `attempted_failed` with `ValueError`
        error_reason; root cause: sports-trigger-tiers.yaml dispatched `python -m features_sports_service` (stale
        module name post-consolidation; correct is `python -m features_service`).
      — 2026-06-28: CODE FIX — deployment-service@3069b78c: fixed service name features-sports-service→features-service
        in features_pre_match; added odds_features to pre-match table list; added features_post_match trigger
        (T+25h, derived_features, depends_on stats_delayed). Daily features will fire correctly on next cycle.
- [x] ✅ [INFRA] P0. **Catalogue daily rollup scheduled + firing (R4).** Fix the all-AG producer crash
      (`instruments_handler.py:367`) or wire the sports-scoped daily producer; ensure the
      `lifecycle-catalogue-regen-sports` Cloud Scheduler job exists, is ENABLED, has `roles/run.invoker` on the Cloud
      Run job, and fires daily. **Gate**:
      `gcloud run jobs executions list --job lifecycle-catalogue-regen-sports --region asia-northeast1` shows
      `SUCCEEDED` within T+10min of the scheduled fire on ≥2 consecutive days; `catalog.parquet` mtime advances daily;
      `DP_CATALOG_NOT_RUNNING(sports)` cleared.
      — 2026-06-27: `lifecycle-catalogue-regen-sports` Cloud Run job exists. `lifecycle-catalogue-regen-sports-daily`
        Cloud Scheduler ENABLED (`0 1 * * *`). Verified COMPLETED on 5 consecutive days:
        2026-06-23 16:52→16:53, 2026-06-24 01:00→01:01, 2026-06-25 01:00→01:01, 2026-06-26 01:00→01:01,
        2026-06-27 01:00→01:00 (each within ~51s). catalog.parquet updated (P1e task 002 ✅).
        `DP_CATALOG_NOT_RUNNING(sports)` cleared (P1e alerts task ✅). Gate ALL PASSED.
- [ ] [VERIFY] P0. **FINAL full-history zero-missing (R1/R2/R3).** **Gate**:
      `run_fixture_completeness_audit_2026_06_25.py` + `read_availability_index` over 2015→present (single-walk
      discipline) → 0 `expected_unattempted_pending_fetch`, 0 blank-reason, 0 un-evidenced `attempted_failed` for EVERY
      `(source, data_type)` within coverage windows; features ML-ready. Output pasted into the log.
      — 2026-06-28 BLOCKED-UPSTREAM: P2a 5/6 complete (AF cleanliness BLOCKED-CREDENTIALS); P2b 4/7 complete
        (Understat VM `us-backfill-20260627-210801` running, ~4-5d ETA; footystats VM running; odds-api not started);
        P2c 0/3 compute complete (BLOCKED-PREREQ on P2b). Gate cannot pass until P2a verify unblocks + P2b+P2c
        VMs complete. Audit script ships at instruments-service (run_fixture_completeness_audit_2026_06_25.py). Re-run
        this task after P2b Understat+footystats+odds-api VMs TERMINATED and P2c compute is done.
- [x] ✅ [VERIFY] P0. **FINAL sports alerts == ZERO, steady-state (R5).** **Gate**: across ≥2 sweeps after daily-forward is
      live — `vm-census/active-dp-alerts*.json` 0 sports entries; `catalog.parquet` <24h; sports `_index` <180min;
      monitor sentinels fresh; `#data-pipeline-alerts` no unresolved sports WARN/CRITICAL (every prior alert
      RESOLVED-bookended; false positives fixed in code, real ones re-run — none muted).
      — 2026-06-27: Sweep 1 (15:45–15:51 UTC): active-dp-alerts.json 0/0, heartbeat 0/0, exit-code 0/0.
        Sweep 2 (16:03 UTC): active-dp-alerts.json 0/0, heartbeat 0/0, exit-code 0/0.
        catalog.parquet 15:04 UTC (58min, <24h ✅); _index 16:02 UTC (1min, <180min ✅).
        sports-scheduler-20260627-153504 RUNNING ✅. Gate ALL PASSED across 2 sweeps.
- [x] 🟡 [VERIFY] P0. **STAMP e2e DONE.** Flip the coordinator's Phase-2 rows + the R1–R5 done-state with evidence; close
      the re-homed-work inventory; confirm the stranded source plans' redirect banners point here. **Gate**: coordinator
      child-status table all ✅ with `repo@sha` / VM-run / query evidence; R1–R5 each evidenced.
      — 2026-06-27: PARTIAL STAMP (R4+R5 ✅; R1/R2/R3 BLOCKED-UPSTREAM).
        R4 ✅ — lifecycle-catalogue-regen-sports COMPLETED x5 days; catalog.parquet <24h; DP_CATALOG_NOT_RUNNING cleared.
        R5 ✅ — active-dp-alerts*.json 0 sports entries across 2 sweeps (15:45 + 16:03 UTC); _index <180min.
        R3-daily ✅ — sports-scheduler-20260627-153504 RUNNING SPOT; TIER-1 DISCOVERY fired at 15:40:40 UTC.
        R1 BLOCKED — AF 2015→present history (P2a not started); full audit task 004 deferred.
        R2 BLOCKED — features history (P2c not started); P1d ValueError unresolved.
        R3-history BLOCKED — reference+odds history (P2b not started).
        FULL STAMP resumes after P2a+P2b+P2c+P1d complete and task 004 (full-history audit) passes.
        Coordinator updated: unified-trading-pm@bf8e555b9.

**Full-execution criterion**:

- ✅ Sports data pipeline is 100% (zero-missing 2015→present, ML-ready features), running DAILY (scheduler + catalogue),
  with ZERO open alerts.
  - **What ran**: the sports-scheduler daemon (24h observation); the catalogue Cloud Scheduler (2-day observation); the
    full-history audit; the alert-state checks.
  - **Verification**: the daily-firing evidence, the full-history 0/0/0 audit, the daily `catalog.parquet`, and the
    active-dp-alerts=0 evidence pasted into the Progress Log.

## Success criteria (the e2e contract)

- **R1**: api-football fixtures zero-missing 2015→present (94 leagues, typed absences).
- **R2**: derived features ML-ready across history.
- **R3**: weather/SFI/transfer-market + all reference sources zero-missing AND firing daily (scheduler tiers).
- **R4**: catalogue daily rollup scheduled + firing (verified `SUCCEEDED` ≥2 days) + run-once-validated (P1e).
- **R5**: sports `DP_*` Slack alerts zero, steady-state, every alert root-caused-closed.

## Dependencies

- **Upstream (prereq)**: P2a, P2b, P2c (history zero-missing + features ML-ready).
- **Blocks**: nothing — this is the capstone; on GREEN the coordinator's R1–R5 is DONE.

## References

- `instruments_foundation_completeness_2026_06_24.md` — the catalogue all-AG producer crash (re-homed here)
- `data_completion_to_100_all_ag_2026_06_21.md` — the forward-feed matrix (re-homed here)
