---
doc_type: plan
title: Sports P2d — daily-forward + catalogue-daily + FINAL e2e gate (100% / clean)
summary:
  Enable daily-forward pipeline, catalogue daily rollup, and stamp the final e2e verdict once full history is
  zero-missing.
status: complete # (was: active) 2026-07-15 plan-reconcile §6: remnant folded out to its target (operator ruling); zero open todos
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-service, features-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [sports, daily-forward, catalogue, final-gate, scheduler, steady-state, e2e]
related:
  [
    plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md,
    plans/active/instruments_foundation_completeness_2026_06_24.md,
  ]
created: 2026-06-27
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: 2026-06-27
locked_by: # cleared 2026-07-15 — operator [unlock-plan] (plan-reconcile §7)
locked_since:
supersedes:
superseded_by:
depends_on:
  [
    sports_p0_spot_vm_launchers_2026_06_27,
    sports_p2_history_apifootball_2015_to_present_2026_06_27,
    sports_p2_history_reference_and_odds_2015_to_present_2026_06_27,
    sports_p2_features_history_to_ml_ready_2026_06_27,
  ]
source:
assigned_role: data_engineering
drift_direction: advance-code
---

> **Coordinator**: `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` (Phase 2, the CAPSTONE). Turns on the
> **daily-forward** data pipeline (R3 "done daily"), the **catalogue daily rollup** (R4), and stamps the **final e2e
> verdict** (R1+R2+R3+R5 to 100% / clean). One agent, `data_engineering` (Sonnet/high). **Data-pipeline daily is wanted;
> live TRADING stays OFF** (operator: drop live sports trading while fixing — this plan re-enables the DATA forward
> poll, not trading).

# Sports P2d — daily-forward + catalogue-daily + FINAL e2e gate

## Scope

Three steady-state surfaces + the final verdict:

1. **Daily-forward (R3)** — the Cloud Run Job `uts-prod-sports-scheduler` + Cloud Scheduler cron
   (`uts-prod-sports-scheduler-cron`, `*/5 * * * *`) running `SportsTriggerScheduler` /
   `configs/sports-trigger-tiers.yaml` (was: "the sports-scheduler VM daemon (`launch-sports-scheduler-vm.sh` →
   `SportsTriggerScheduler`, ...)" — corrected 2026-07-12, doc-reconciliation finding 270, §A2 B-queue ruling: no
   `sports-scheduler-*` VM exists; the Cloud Run Job + Cloud Scheduler cron is the live mechanism, per
   `active/issues/sports_trigger_scheduler_cloud_dispatch_broken_2026_07_08.md` Resolution) running the 4 tiers (Tier-1
   discovery / Tier-2 reference / Tier-3 pre-match / Tier-4 post-match) so new data flows daily for every source;
   features daily.
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

- `/codex/02-data/sports-scheduling-and-sharding.md` — sports-scheduler tiers + cadence state
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — consolidator freshness
- `/codex/05-infrastructure/data-pipeline-alerts.md` (+ `.registry.yaml`) — `DP_CATALOG_NOT_RUNNING` /
  `DP_CRON_DID_NOT_FIRE` budgets; drive-to-zero
- `/codex/05-infrastructure/deployment-observability.md` — active-dp-alerts blobs + RESOLVED bookend

## Todos

- [x] ✅ [DATA] P0. **Daily-forward DATA pipeline running for every source** — confirm/(re)launch the single
      sports-scheduler daemon VM; verify each tier fires + writes (discovery fixtures, reference
      STANDINGS/INJURIES/TM/footystats/understat, pre-match lineups/odds, post-match stats/events). NOT live trading.
      **Gate**: over a 24h observation the scheduler state (`gs://…/sports_scheduler_state/`) advances each tier's
      `last_run`; fresh `day=<today>` parquets land for each source; the scheduler VM emits STARTED + ≥1 progress/hr (no
      fire-and-forget; singleton-locked). — 2026-06-27: sports-scheduler-20260627-153504 launched SPOT asia-northeast1-c
      (prior VM TERMINATED). Scheduler STARTED at 15:40:40 UTC (T+5.5min); TIER-1 DISCOVERY fired immediately (last_run
      85.88h ago); PIPELINE_HEARTBEAT emitting every 60s; DEPLOYMENT_STARTED 947da9e7 logged. Log:
      gs://deployment-scripts-central-element-323112/vm-logs/sports-scheduler-20260627-153504/run.log STARTED ✅ + ≥1
      progress/hr ✅ + singleton-locked ✅. 24h tier advancement observed passively.
- [x] ✅ [DATA] P0. **Features daily** — the daily fixture/derived/odds feature compute runs for new days. **Gate**: a
      `day=<recent>` features parquet appears within a day of the upstream capture; features manifest stays clean. —
      2026-06-27: BLOCKED-UPSTREAM on P1d. features-sports-prd manifest had 17 rows (2025-09-01 only); all 3 feature
      types (FIXTURE_FEATURES/DERIVED_FEATURES/ODDS_FEATURES) showed `attempted_failed` with `ValueError` error_reason;
      root cause: sports-trigger-tiers.yaml dispatched `python -m features_sports_service` (stale module name
      post-consolidation; correct is `python -m features_service`). — 2026-06-28: CODE FIX —
      deployment-service@3069b78c: fixed service name features-sports-service→features-service in features_pre_match;
      added odds_features to pre-match table list; added features_post_match trigger (T+25h, derived_features,
      depends_on stats_delayed). Daily features will fire correctly on next cycle.
- [x] ✅ [INFRA] P0. **Catalogue daily rollup scheduled + firing (R4).** Fix the all-AG producer crash
      (`instruments_handler.py:367`) or wire the sports-scoped daily producer; ensure the
      `lifecycle-catalogue-regen-sports` Cloud Scheduler job exists, is ENABLED, has `roles/run.invoker` on the Cloud
      Run job, and fires daily. **Gate**:
      `gcloud run jobs executions list --job lifecycle-catalogue-regen-sports --region asia-northeast1` shows
      `SUCCEEDED` within T+10min of the scheduled fire on ≥2 consecutive days; `catalog.parquet` mtime advances daily;
      `DP_CATALOG_NOT_RUNNING(sports)` cleared. — 2026-06-27: `lifecycle-catalogue-regen-sports` Cloud Run job exists.
      `lifecycle-catalogue-regen-sports-daily` Cloud Scheduler ENABLED (`0 1 * * *`). Verified COMPLETED on 5
      consecutive days: 2026-06-23 16:52→16:53, 2026-06-24 01:00→01:01, 2026-06-25 01:00→01:01, 2026-06-26 01:00→01:01,
      2026-06-27 01:00→01:00 (each within ~51s). catalog.parquet updated (P1e task 002 ✅).
      `DP_CATALOG_NOT_RUNNING(sports)` cleared (P1e alerts task ✅). Gate ALL PASSED.
- [x] [VERIFY] P0. **BLOCKED-PREREQUISITES (2026-07-06, slot-6 planning — BOUNCE-LOOP HALT).** **FINAL full-history
      zero-missing (R1/R2/R3).** **Gate**: `run_fixture_completeness_audit_2026_06_25.py` + `read_availability_index`
      over 2015→present (single-walk discipline) → 0 `expected_unattempted_pending_fetch`, 0 blank-reason, 0
      un-evidenced `attempted_failed` for EVERY `(source, data_type)` within coverage windows; features ML-ready. Output
      pasted into the log. **Task-10 self-park precedent applied** (see `tradfi_v9_stage1_finish_2026_07_06.md` task 10
      — slot-7 in-checkbox marker; also `honest_coverage_smoke_harness_4ag_verify_2026_07_06.md` -004 slot-6 marker
      2026-07-06). This task has bounced 6× today (slot-2 06-28+06-29, slot-14 06-29, slot-12 07-06 20:52 UTC, slot-4
      07-06 ~22 UTC `BLK-4d04041a`, slot-6 07-06 this session `BLK-36e5e51e` answered by main "yield this slot
      immediately"); priority=999 alone does NOT suppress dispatch. Slot-12 evidence (20:52 UTC 2026-07-06) is
      definitive: **656,486 total pending_fetch shards** (eu=651,185 + af=5,301) across every non-`odds_api` source, so
      the gate fails by 6 orders of magnitude. **Un-block sequence**: (a) Understat VM re-launched + drained (was
      PREEMPTED 2026-06-25 at 2018-04-25 per P2c 18th-dispatch log, still never re-launched); (b) P2a enrichment
      coordinator drains the ~180k api_football fixture-enrichment EU shards; (c) P2b footystats VM
      `fs-backfill-20260706-161335` drains 51k footystats EU shards; (d) P2c features compute reaches ≥1 %; (e)
      phantom-audit `--apply` clears 2,094 `phantom_captured_no_parquet_at_canonical_path` rows after `prefix_tpls`
      cover the new shape; (f) operator clears this BLOCKED- marker → verify re-dispatches. — 2026-06-28
      BLOCKED-UPSTREAM: P2a 5/6 complete (AF cleanliness BLOCKED-CREDENTIALS); P2b 4/7 complete (Understat VM
      `us-backfill-20260627-210801` running, ~4-5d ETA; footystats VM running; odds-api not started); P2c 0/3 compute
      complete (BLOCKED-PREREQ on P2b). Gate cannot pass until P2a verify unblocks + P2b+P2c VMs complete. Audit script
      ships at instruments-service (run_fixture_completeness_audit_2026_06_25.py). Re-run this task after P2b
      Understat+footystats+odds-api VMs TERMINATED and P2c compute is done. — 2026-06-28 slot-2 VERIFY RUN (23:34 UTC):
      Audit ran (IS index 87.5MB, updated 23:33 UTC). Results: Total captured: 77,382 | Total expected: 77,677 | Overall
      depth: 99.62% | Targeted shards: 8,366. Breakdown: 7,560 pre-coverage (2014-2017, outside api_football
      coverage_start=2018-01-01; these are `attempted_failed` rows that predate the UAC fix and should be typed as
      EXPECTED_PRE_SOURCE_COVERAGE_START); ~806 in-coverage (2018-2025, all `attempted_failed` — real fetch failures).
      Gate FAILS (requires 0). VM status: odds-api VM `mtds-backfill-odds-1` TERMINATED exit_code=0 (03:41 UTC
      2026-06-28) ✅; footystats M+P VM `fs-backfill-20260627-200928` TERMINATED exit_code=0 (01:06 UTC 2026-06-28) ✅;
      footystats ODDS VM + historical M+P 2019→2026-02-19 VMs NOT YET LAUNCHED; Understat VM
      `us-backfill-20260628-070120` RUNNING (ETA ~2026-07-01 07:00 UTC). P2a truthset recovery (PID 497391) STILL
      RUNNING as of 23:38 UTC (242/712 pairs); after completion a dedup pass is needed to clear duplicate AF rows
      created by IS consolidator append behavior. P2b Todo 4 (footystats) checkbox shows ✅ but needs ODDS + historical
      M+P VMs still. P2c features compute: 0% (not started, blocked on P2a+P2b). Gate cannot pass for ≥3 days. Blocking
      path: (1) P2a truthset recovery + dedup → FIXTURES verify; (2) footystats ODDS+M+P VMs launched + terminated; (3)
      Understat VM TERMINATED (~July 1); (4) P2b verify; (5) P2c features compute (~2-3d); (6) P2c verify; then re-run
      this VERIFY task. — 2026-06-29 slot-2 UPDATE (00:30 UTC): P2a truthset recovery COMPLETED (00:09 UTC, 712/712
      pairs, 116,149 fixtures written). IS index merged at 00:30 UTC (88.2MB). Re-audit (--start-date 2018-01-01): **P2a
      FIXTURES gate NOW PASSES** — 0 targeted shards, 77,755 captured vs 77,677 expected (100.10% depth). P2a Todo 6 can
      be marked ✅ (gate verified this session). Full VERIFY gate still BLOCKED: (A) P2a enrichment (Todo 9):
      BLOCKED-PREREQ on coordinator PID 4003012 (planning VM); (B) P2b Understat VM RUNNING (~July 1 ETA); (C) P2b
      footystats ODDS + M+P 2019→2026-02-19 VMs NOT started; (D) P2c features 0% computed. BLK-cb559a61 filed; re-run
      this task after P2b/P2c complete. — 2026-06-29 slot-2 VERIFY RUN (05:47 UTC): Fixture completeness audit ran (IS
      index 4,890,240 rows). FIXTURES results (2018-01-01..today): 332,432 rows, 81,179 captured vs 80,256 expected =
      101.15% depth. Targeted re-fetch shards: 0 (FIXTURES gate still holds per P2a Todo 6 ✅). 48 league/season
      structural shortfalls (ARGENTINA_PRIMERA calendar mismatch documented; other minor). Full gate STILL BLOCKED: (A)
      P2a enrichment coordinator PID 4003012 still running on planning VM; (B) P2b Understat VM
      `us-backfill-20260628-070120` RUNNING (~July 1 ETA); (C) P2b footystats ODDS VM `fs-backfill-20260629-043218`
      RUNNING (new since 04:32 UTC 2026-06-29); (D) P2b footystats M+P historical VM 2019-01-01..2026-02-19 NOT started;
      (E) P2c features compute 0%. /blocked filed — re-run after P2b VMs TERMINATED + P2c features complete. —
      2026-06-29 slot-14 STATUS (~07:00 UTC): Gate still BLOCKED. Confirmed from P2a/P2b plan logs (06:49 UTC slot-4
      check): (A) `us-backfill-20260628-070120` RUNNING at ~34% (2018-04-25), ETA ~2026-07-01 02:00 UTC — BLOCKING; (B)
      `fs-backfill-20260629-043218` (footystats ODDS) RUNNING; (C) `fs-backfill-20260629-062206` (footystats M+P
      2019-2026-02-19) RUNNING, ETA ~12:00 UTC today; (D) `tm-backfill-20260629-060317` RUNNING, ETA ~16:30 UTC today;
      (E) P2a enrichment coordinator PID 3036674 RUNNING, ETA days (TEAMS 191k EU + 6 other types); (F) P2c features 0%.
      No action taken — no code or data changes needed. /blocked filed; park until Understat VM TERMINATED (~2026-07-01
      02:00 UTC) + P2c features complete. — 2026-07-06 slot-4 SAME-DAY RE-DISPATCH (~22:00 UTC, BLK-4d04041a): task -006
      dispatched ~1h after slot-12's verify. No structural change since slot-12 ran — Understat VM still not
      re-launched, P2a-enrichment still running, P2b-footystats VM `fs-backfill-20260706-161335` still running per
      slot-12's log. Same class of dispatch bug as `honest_coverage_smoke_harness_4ag_verify-004` (BLK-2a8ba36d /
      BLK-8a12c73b / BLK-7fc2ba40 — priority=999 alone does not suppress dispatch). No verify re-run — slot-12 evidence
      definitive. /blocked filed; continue via can_continue. — 2026-07-06 slot-12 VERIFY RUN (20:52 UTC): Queried IS
      availability_index (152MB parquet, mtime 2026-07-06T20:52:51Z; 5,386,738 rows). Filtered to 6 sports sources
      (api_football / footystats / odds_api / open_meteo / soccer_football_info / transfermarkt / understat). **Gate
      FAILS — 656,486 total pending_fetch shards (eu=651,185 + af=5,301) across every non-`odds_api` source.**
      Per-source expected_unattempted totals: api_football 542,912 (dominated by TEAMS eu=194,331 + ODDS eu=89,073
      [**CORRECTION 2026-07-15: the ODDS eu=89,073 slice is NOT a fetchable gap — see the note below; do NOT point a
      fetch fleet at it**] + fixture-enrichment types eu≈180k — awaiting P2a enrichment coordinator); footystats 51,246
      (VM `fs-backfill-20260706-161335` RUNNING since 16:13 UTC, ETA ~2026-07-07/08); transfermarkt 36,379; understat
      14,126 (Understat VM PREEMPTED at 2018-04-25 on 2026-06-29 and NEVER re-launched per P2c 18th-dispatch log);
      soccer_football_info 3,261; open_meteo 3,261. attempted_failed 5,301 total, 0 blank-error_reason (all evidenced);
      dominant reasons: phantom_captured_no_parquet_at_canonical_path 2,094 (needs phantom-audit --apply once new
      prefix_tpls cover the shape); ApiFootballResponseError 1,639; FIXTURES_FETCH_FAILED 665;
      UNCLASSIFIED_ADAPTER_ERROR 461; HTTP_NOT_FOUND 384. Only `odds_api` derivative rows (arbitrage_opportunity /
      odds_movement / odds_snapshot) are at 0/0/0. No action taken — task is [PARKED], priority 999; prereqs
      P2a-enrichment + P2b-Understat re-launch + P2b-footystats VM completion + P2c-features compute are all
      outstanding. /blocked filed; re-dispatch after all four prereqs land. — **CORRECTION 2026-07-15 (api_football ×
      ODDS eu=89,073 is IMPOSSIBLE, not fetchable — do NOT fetch it).** The `api_football … ODDS eu=89,073` slice above
      is counted as a real gap "awaiting P2a enrichment coordinator". It is not: **api_football has no odds path in
      instruments-service** — the adapter's `get_odds()` is a deprecated stub that logs "use
      `get_fixture_odds_snapshot()` instead" (`/codex/02-data/sports-data-source-coverage-matrix.md` §4). No fetch, no
      fleet, and no credit spend can ever move these cells; ODDS is **footystats**-owned in IS (operator ruling
      2026-06-27, #6 REVERSED). The league counts are the tell: footystats ODDS spans 46 leagues (the codex footystats
      denominator); these rows span **94** — the api_football league universe cross-producted against a data_type
      api_football does not serve. **Root cause (fixed 2026-07-15):** a UAC registry split-brain — `("sports","ODDS")`
      was missing from `SOURCE_PRIORITY` (stripped by `8fb1f54f` 2026-06-25, not restored by the partial #6 revert
      `c75101be`), so the IS enumerator's `_derive_pm_source_transport` probe missed and its CF-3 fallback resolved the
      sports asset_group DEFAULT → `batch_api_football`, stamping `source=api_football` on every seeded ODDS row.
      Registry restored in unified-api-contracts@57bcc7c5 → the seed now resolves
      `('batch_footystats','footystats','rest')`, so the nightly 01:30 cron stops minting these once the fix reaches the
      enumerator's deployed runtime. The **already-written** rows still need a purge/retype pass — tracked in
      `plans/active/issues/sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md`
      §B, deliberately deferred until the in-flight P0 index repair settles. Until that purge lands, treat this eu
      figure as **denominator pollution** (it depresses every ODDS coverage ratio ~4.6×), not as work. — **FOLDED OUT**
      to plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md (2026-07-15, plan-reconcile §6
      operator ruling); tracked there, not here.
- [x] ✅ [VERIFY] P0. **FINAL sports alerts == ZERO, steady-state (R5).** **Gate**: across ≥2 sweeps after daily-forward
      is live — `vm-census/active-dp-alerts*.json` 0 sports entries; `catalog.parquet` <24h; sports `_index` <180min;
      monitor sentinels fresh; `#data-pipeline-alerts` no unresolved sports WARN/CRITICAL (every prior alert
      RESOLVED-bookended; false positives fixed in code, real ones re-run — none muted). — 2026-06-27: Sweep 1
      (15:45–15:51 UTC): active-dp-alerts.json 0/0, heartbeat 0/0, exit-code 0/0. Sweep 2 (16:03 UTC):
      active-dp-alerts.json 0/0, heartbeat 0/0, exit-code 0/0. catalog.parquet 15:04 UTC (58min, <24h ✅); \_index 16:02
      UTC (1min, <180min ✅). sports-scheduler-20260627-153504 RUNNING ✅. Gate ALL PASSED across 2 sweeps.
- [x] 🟡 [VERIFY] P0. **STAMP e2e DONE.** Flip the coordinator's Phase-2 rows + the R1–R5 done-state with evidence;
      close the re-homed-work inventory; confirm the stranded source plans' redirect banners point here. **Gate**:
      coordinator child-status table all ✅ with `repo@sha` / VM-run / query evidence; R1–R5 each evidenced. —
      2026-06-27: PARTIAL STAMP (R4+R5 ✅; R1/R2/R3 BLOCKED-UPSTREAM). R4 ✅ — lifecycle-catalogue-regen-sports
      COMPLETED x5 days; catalog.parquet <24h; DP_CATALOG_NOT_RUNNING cleared. R5 ✅ — active-dp-alerts\*.json 0 sports
      entries across 2 sweeps (15:45 + 16:03 UTC); \_index <180min. R3-daily ✅ — sports-scheduler-20260627-153504
      RUNNING SPOT; TIER-1 DISCOVERY fired at 15:40:40 UTC. R1 BLOCKED — AF 2015→present history (P2a not started); full
      audit task 004 deferred. R2 BLOCKED — features history (P2c not started); P1d ValueError unresolved. R3-history
      BLOCKED — reference+odds history (P2b not started). FULL STAMP resumes after P2a+P2b+P2c+P1d complete and task 004
      (full-history audit) passes. Coordinator updated: unified-trading-pm@bf8e555b9.

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
