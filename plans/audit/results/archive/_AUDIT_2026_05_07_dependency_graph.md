---
type: audit-report
audit_run: 2026-05-07
scope: all active plans + 37 running VMs
status: durable-reference
last_update: 2026-05-07T11:30Z
estimate_class: research
estimate_baseline_ai_days: TBD
estimate_calibrated_ai_days: TBD
estimate_calibration_note: |
  No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from filename (research, multiplier 1.2×).
  Owner agent: fill baseline + multiply × 1.2 per /codex/08-workflows/estimation-calibration.md. Refine class if dominant work-class differs.
---

# Active Plan Audit — 2026-05-07

## Session close-out 2026-05-07T12:30Z — durable handover

This is the close-out summary. The active PM plans now capture every piece of work going forward for the 2026-05-23
deadline. Anyone picking up after this session reads §"Where every piece of work lives" below to find the right plan,
then checks the per-plan `## Audit 2026-05-07` header for status.

### Decisions taken in-session (binding)

1. **Dual-cloud-active is the steady state.** Not a transitional cutover. Both GCP and AWS run in parallel. Backfills
   hit both. Live deployments chosen ad-hoc per archetype / use case based on cost / latency / credit trade-offs. GCP
   stays first-class; AWS is added alongside, not replacing. Captured in
   [`aws_migration_defi_first_2026_05_07.md`](aws_migration_defi_first_2026_05_07.md) §"Operator answers" (commit
   `893a9da4` + Phase 0 flips).

2. **AWS scope for May-23**: DeFi + CeFi-instruments. Everything else (sports / predictions / tradfi / cefi-historical)
   stays GCP-resident with opportunistic dual-write expansion post-May-23 as Phase 9.

3. **Credit budget**: ≥$40k over 11 months = ~$3,636/mo sustainable. Comfortably covers DeFi+CeFi-instruments AWS
   run-rate. No service / region / account locks expected (Phase 1 smoke test confirms).

4. **Custody**: Copper + CEFFU AWS-compatible — wallet hosts can run AWS-resident.

5. **UI/API co-locates with data** (data-locality principle). UI on AWS when serving AWS-resident DeFi data; UI on GCP
   when serving GCP-resident sports/predictions/tradfi. `CROSS_CLOUD_EGRESS_DETECTED` AlertCode added to alerting
   taxonomy as safety net.

6. **AWS Q3-defer recommendation** (in
   [`plans/archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md`](../archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md))
   is **superseded** by the dual-cloud plan above. The per-resource cost numbers were extracted to
   [`/codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md`](/codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md)
   for ongoing reference (numbers still valid); the recommendation paragraph is replaced.

### Where every piece of work lives (for May-23)

The 23 active plans (20 audited 2026-05-07 + 3 new keystones) cover everything.

| Concern                                                                                     | Plan                                                                                                                                          |
| ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Live-trading critical path / Group A-G readiness                                            | [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md)                                                                      |
| Manifest write-side honesty (record_empty / record_failed / record_expected_empty)          | [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md)                                        |
| Manifest legacy-row migration (write-side back-fill)                                        | [`manifest_migration_SUPERSEDED_2026_05_21.md`](/plans/epics/manifest_migration_SUPERSEDED_2026_05_21.md)                                     |
| Strategy engine v2 finalization (V1-RETIRE done, futures-roll + Unity UAT remain)           | [`strategy_architecture_v2_finalization_2026_04_19.plan.md`](../archive/strategy_architecture_v2_finalization_2026_04_19.plan.md)             |
| DART operator UX (substantively shipped, 7 polish items)                                    | [`dart_ux_cockpit_refactor_2026_04_29.plan.md`](../archive/dart_ux_cockpit_refactor_2026_04_29.plan.md)                                       |
| **CeFi backfills, venues, instruments, date ranges**                                        | [`cefi_master.md`](/plans/epics/cefi_master.md)                                                                                               |
| **DeFi backfills, protocols, chains, LST tokens, 6 perp-venue hedges**                      | [`/plans/epics/defi_master.md`](/plans/epics/defi_master.md)                                                                                  |
| **TradFi backfills, ES.OPT 11-cluster, Databento, MDPS**                                    | [`tradfi_master.md`](/plans/epics/tradfi_master.md)                                                                                           |
| **Sports backfills, 6 sources, leagues, fixture/odds/lineups/weather**                      | [`sports_master.md`](/plans/epics/sports_master.md)                                                                                           |
| **Predictions / Polymarket / Kalshi canonical-question-group**                              | [`predictions_master.md`](/plans/epics/predictions_master.md)                                                                                 |
| **Shard granularity SSOT, data-status drilldown, deployment-build infra**                   | [`infrastructure_master.md`](/plans/epics/infrastructure_master.md)                                                                           |
| Asset-group vocabulary (3 absorbed items remain)                                            | [`venue_axis_asset_group_vocabulary_2026_04_25.plan.md`](../archive/venue_axis_asset_group_vocabulary_2026_04_25.plan.md)                     |
| Instruments-service + MTDS completion                                                       | [`instruments_and_market_tick_data_completion_2026_05_01.plan.md`](../archive/instruments_and_market_tick_data_completion_2026_05_01.plan.md) |
| MTDS per-instrument download API                                                            | [`mtds_per_instrument_download_api_2026_04_24.md`](mtds_per_instrument_download_api_2026_04_24.md)                                            |
| Feature DAG UAC SSOT + LookaheadBiasError honesty                                           | [`feature_dag_uac_ssot_and_features_coverage_2026_05_06.plan.md`](../archive/feature_dag_uac_ssot_and_features_coverage_2026_05_06.plan.md)   |
| Features consolidation + drilldown (P2/P3)                                                  | [`features_consolidation_and_drilldown_2026_05_06.plan.md`](../archive/features_consolidation_and_drilldown_2026_05_06.plan.md)               |
| ML training feature-read perf (1-3 day pure-win)                                            | [`ml_training_feature_read_perf_2026_05_06.plan.md`](../archive/ml_training_feature_read_perf_2026_05_06.plan.md)                             |
| ML advanced pipeline (cross-asset-group ML scaffolding)                                     | [`consolidated_ml_advanced_pipeline_2026_04_15.plan.md`](../archive/consolidated_ml_advanced_pipeline_2026_04_15.plan.md)                     |
| Cluster e2e operational validation (cross-cutting)                                          | [`consolidated_operational_validation_2026_04_15.plan.md`](../archive/consolidated_operational_validation_2026_04_15.plan.md)                 |
| Strategy-and-UI consolidation (rescope candidate)                                           | [`consolidated_strategy_and_ui_2026_04_15.plan.md`](../archive/consolidated_strategy_and_ui_2026_04_15.plan.md)                               |
| **NEW: Alerting live rules SSOT + thresholds + paging + rehearsal**                         | [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md)                                                      |
| **NEW: deployment-api work-stream-A endpoints (`/api/backfill/launch` + `/api/vm/events`)** | [`deployment_api_work_stream_a_2026_05_07.plan.md`](../archive/deployment_api_work_stream_a_2026_05_07.plan.md)                               |
| **NEW: AWS dual-cloud buildout DeFi+CeFi-instruments first**                                | [`aws_migration_defi_first_2026_05_07.md`](aws_migration_defi_first_2026_05_07.md)                                                            |

### Anomalies from §6 still open (not yet captured in any plan)

These were surfaced in the original audit but have no dedicated home plan and are not yet folded into a parent.
**Authored** `audit_followups_2026_05_07.md` 2026-05-07 to track these. **All 6 closed 2026-05-08 by Tab 8.**

| #      | Anomaly                                                                                                                                                     | Suggested home                                          | Status                                                                                                                           |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| §6 #2  | master plan body references folded `defi_e2e_pipeline_2026_04_30` / `leveraged_leg_controller_2026_05_01` / `defi_pipeline_extension_2026_05_01`            | master plan body fix (housekeeping commit)              | ✅ DONE PM@`8286cf4` (2026-05-08, Tab 8) — 5 live-context refs replaced + 1 STALE-marked + historical "(folds in)" preserved     |
| §6 #3  | service-readiness matrix lists already-archived `manual_trade_booking_reconciliation_2026_03_22`                                                            | master plan body fix                                    | ✅ DONE PM@`8d33d97` (2026-05-08, Tab 8) — verified resolved by matrix evolution; all 12 primary refs in plans/active/           |
| §6 #4  | plan-hygiene work-stream-G item counts (140/142/31) obsolete after Stage 7 batch consolidation                                                              | master plan body re-derive against active/+ai/= ~25+111 | ✅ DONE PM@`8d33d97` (2026-05-08, Tab 8) — re-derived: 28 active / 66 ai / ~437 archive; structure preserved                     |
| §6 #5  | `manifest_migration_master` line 473 cites stale module path `unified_api_contracts.canonical.crosscutting.empty_confirmed_reasons.EMPTY_CONFIRMED_REASONS` | manifest_migration_master line edit                     | ✅ DONE PM@`8d33d97` (2026-05-08, Tab 8) — verified already resolved; canonical `honest_coverage` path documented at lines 96-99 |
| §6 #6  | MDPS-1440-NaN reproduction-test in infrastructure_master is STALE                                                                                           | infrastructure_master line edit                         | ✅ DONE PM@`b9593b2` (2026-05-08, Tab 8) — STALE marker already at line 130; reconciled audit-header count 4→2                   |
| §6 #7  | strategy v2 Phase 3 entirely STALE (V1-RETIRE bypassed shadow window)                                                                                       | strategy_architecture_v2 line edit                      | ✅ DONE PM@`b9593b2` (2026-05-08, Tab 8) — moot by archival: plan archived per PM@`b638c37` (consolidation-B umbrella fold)      |
| §6 #11 | `manifest_migration_master` is NOT superseded by writegate 3D.2 — both required (write-side vs read-side)                                                   | already captured in audit doc; no action                | ✅ noted (audit doc itself)                                                                                                      |
| §6 #12 | Lighter `block_height` on-chain replay infeasible (sequencer-internal)                                                                                      | defi_master Lighter section already STALE               | ✅ noted (defi_master STALE)                                                                                                     |

### Dual-cloud changes that should propagate INTO existing plans

The dual-cloud-active policy decision touches multiple plans. Recommend a follow-up housekeeping commit (or per-plan
edits as work progresses):

- `master_to_live_defi:work-stream-D` — replace "AWS↔GCP cloud parity Q3-deferred" with "dual-cloud-active per
  `aws_migration_defi_first` plan; DeFi production live on AWS by 2026-05-23, sports/predictions/tradfi GCP-resident
  with Phase 9 dual-write expansion."
- `defi_master:carry_staked_basis-live` — note live deploy is AWS-resident. Add Phase 0 link to AWS plan.
- `defi_master:leveraged_funding_arb-live` — same.
- `cefi_master` — add note that CeFi-instruments dual-writes to AWS; CeFi historical stays GCP-resident.
- `infrastructure_master` — flip "AWS infra deferred to Q3" to "AWS infra critical-path May-23 (DeFi+CeFi-instruments
  only)."
- `manifest_migration_master` — add Phase 1.5.A bucket-name parity reference; manifest reads must work on both backends.
- `alerting_service_live_rules` — add `CROSS_CLOUD_EGRESS_DETECTED` AlertCode + threshold to Phase 1 taxonomy (already
  noted in AWS plan §"Data locality principle").

### Workspace rules that should land (post-this-session)

These are cross-cutting policies surfaced in this session. Should become CLAUDE.md / codex SSOT entries:

1. **Cloud-agnostic policy**: every script touching cloud accepts `--cloud {gcp,aws}` flag with default from
   `CLOUD_PROVIDER` env. No `gcloud storage`/`gsutil`/`google.cloud.storage` without an AWS branch. Pattern doc:
   `unified-trading-pm/codex/05-infrastructure/cloud-agnostic-script-pattern.md` (Phase 1.5.D ships this).
2. **Data-locality principle**: UI/API co-locates with the data it reads. Cross-cloud egress on every dashboard request
   is a bug, alerted via `CROSS_CLOUD_EGRESS_DETECTED`. Add to CLAUDE.md alongside existing "Batch = Live" architecture
   rule.
3. **Bucket name SSOT discipline**: every parquet read/write computes bucket from `cloud-providers.yaml` via UCI
   factory, never inline string formatting. Already implicit but should be explicit rule.
4. **Plan-checkbox-flip cadence**: per existing CLAUDE.md `896c9bc5` hard rule. The 4 plans whose markers got reset in
   the audit (master/writegate/dart/strategy) demonstrate why immediate commit+push matters.

### Concrete next-session entry points (priority-ordered)

1. **Operator: confirm AWS Phase 1 smoke test green** —
   `cd instruments-service && CLOUD_PROVIDER=aws AWS_DEFAULT_REGION=ap-northeast-1 python -m instruments_service --health-check`.
   Single highest-leverage validation. ~1h.
2. **Operator: kick off Harsh Phase 1 review** of `alerting_service_live_rules` UAC `AlertCode` taxonomy. Async; sets up
   Phase 2-9 of alerting plan.
3. **Operator: run `bash deployment-service/scripts/aws/setup-defi-buckets.sh`** (Phase 2 of AWS plan, after script
   lands).
4. **Drain 24 cefi backfill VMs** (ETA 2026-05-08/09 per §4) before launching cross-asset manifest rescan or AWS
   data-migration via Storage Transfer Service.
5. **Open `audit_followups_2026_05_07.md`** for the 7 anomalies above. ~1h author.
6. **Land cloud-agnostic-script-pattern codex doc** (workspace rule #1 above). ~1h.
7. **Implement `deployment-api` work-stream-A endpoints** per
   [`deployment_api_work_stream_a_2026_05_07.plan.md`](../archive/deployment_api_work_stream_a_2026_05_07.plan.md)
   3-phase plan. 1-2 days.

### What this session shipped (close-out manifest)

| #   | Artefact                                                                                                                                                                                                                                                                | Path                                                                  | Commit        |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | ------------- |
| 1   | 16-plan audit pass (per-todo + per-plan headers)                                                                                                                                                                                                                        | `plans/active/*.plan.md` (16 plans)                                   | `dada46d1`    |
| 2   | Cross-plan dependency graph + critical path synthesis                                                                                                                                                                                                                   | `plans/active/_AUDIT_2026_05_07_dependency_graph.md`                  | `12ce828a`    |
| 3   | Alerting service live-rules plan (keystone #1)                                                                                                                                                                                                                          | `plans/active/alerting_service_live_rules_2026_05_07.md`              | `3712c640`    |
| 4   | Deployment-api work-stream-A sub-plan (keystone #2, parallel agent)                                                                                                                                                                                                     | `plans/active/deployment_api_work_stream_a_2026_05_07.plan.md`        | `c6fe668d`    |
| 5   | AWS migration cost analysis (extracted to `/codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md`; original archived to `plans/archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md` per codex_refactor F.4 — Q3-defer recommendation superseded) | `plans/archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md` | `4973dd71`    |
| 6   | Audit doc keystone-status update                                                                                                                                                                                                                                        | (this file)                                                           | `e7bbcc36`    |
| 7   | AWS dual-cloud DeFi-first plan (keystone #3, supersedes #5 recommendation)                                                                                                                                                                                              | `plans/active/aws_migration_defi_first_2026_05_07.md`                 | `893a9da4`    |
| 8   | Audit doc final close-out (this section)                                                                                                                                                                                                                                | (this file)                                                           | (next commit) |

---

## Update 2026-05-07T11:30Z — 3 keystone unblocks scoped/landed

The 3 operator action items flagged in §7 are now closed-or-scoped:

1. **Alerting plan**: shipped as
   [`alerting_service_live_rules_2026_05_07.md`](alerting_service_live_rules_2026_05_07.md) (commit `3712c640`). 9
   phases, 9-12 days (parallelisable to 7-8). Note: the alerting-**service** itself already exists with multi-channel
   routing + KillSwitchBus subscriber via `7b74ed8` + MarginEvent consumer via `f4c308f`
   - AWS-aware `buildspec.aws.yaml`. The plan covers the rules-SSOT + thresholds + paging targets + operator playbook +
     rehearsal that were actually missing. Anomaly #13 ("alerting plan does not exist") in §6 is now superseded — the
     SERVICE existed; the live-rules SSOT did not.

2. **Deployment-api work-stream-A**: sub-plan landed as
   [`deployment_api_work_stream_a_2026_05_07.plan.md`](../archive/deployment_api_work_stream_a_2026_05_07.plan.md)
   (commit `c6fe668d` by parallel agent). 3 phases — UAC types (`BackfillLaunchRequest`, `BackfillLaunchResult`,
   `VMLifecycleEvent`, `VMEventListResult`, `BackfillLaunchTaskKind` StrEnum), POST/GET endpoints, QG. Implementation
   can start immediately.

3. **AWS migration cost analysis**: shipped as
   [`plans/archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md`](../archive/audits/aws_migration_cost_analysis_2026_05_07.plan.md)
   (commit `4973dd71`; per-resource cost snapshot extracted by codex_refactor F.4 to
   [`/codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md`](/codex/05-infrastructure/aws-migration-cost-snapshot-2026-05-07.md)).
   Top-line: GCP ~$8.3-12.5k/mo, AWS list ~$8.8-13.3k/mo (+5-7%), 12-mo delta +$6-10k/yr — **decision is not
   cost-driven**. **Recommendation: option (a) — defer full AWS parity to Q3 2026.** Scoped subset (S3 + Secrets
   Manager + ECR) is shippable in 5-7 engineer-days but adds zero live-trading capability before May-23.

**Net effect on critical path** (§3): items 1-3 of "Week 1 keystone unblocks" are now scoped — the work itself is the
next ship. AWS work moves from "BLOCKED on cost analysis" to "DEFERRED to Q3 2026 per recommendation"; this removes ~10
BLOCKED items from infrastructure_master + master:work-stream-D that were waiting on the report. Live-trading May-23
path is now clear of upstream-doc gates — execution begins.

---

Cross-plan dependency graph + per-plan status snapshot. Companion to per-plan `## Audit 2026-05-07` headers +
`[AUDIT 2026-05-07: ...]` per-todo markers inserted in 16 of 20 active plans (commit `dada46d1`, 2026-05-07).

**Methodology**: 8 parallel sub-agents, one per plan-cluster. Each enumerated unchecked todos via `grep -n "- \[ \]"`,
verified implementation against shipped commits (UAC / UTL / MTDS / MDPS / instruments-service / execution-service /
strategy-service / deployment-api+ui / deployment-service / features-\* / ml-training / ml-inference repos), matched
against 37 currently-running VMs, and cross-referenced sibling plans for blocker chains.

**Deadline**: 2026-05-23 (live DeFi trading on real wallet ≥7 days). **Days remaining**: 16.

> ⚠️ Note: 4 large plans (master_to_live_defi, writegate, dart_ux_cockpit, strategy_architecture_v2) lost their per-todo
> markers mid-audit to concurrent agent `git reset` operations. Their findings are preserved in this doc rather than
> re-edited in the plan files (low-collision recovery). The other 16 plans have full per-todo markers in-place.

---

## 1. Per-plan status snapshot

| Plan                                                       | Total todos`<br>`unchecked | Mis-marked`<br>`→ flipped DONE | In-flight`<br>`(VMs running) | Blocked-by`<br>`(plans) | Stale | Recommendation                                                                                                                   |
| ---------------------------------------------------------- | -------------------------: | -----------------------------: | ---------------------------: | ----------------------: | ----: | -------------------------------------------------------------------------------------------------------------------------------- |
| **master_to_live_defi_2026_05_23**                         |                        110 |                              5 |                           ~6 |                     ~70 |   ~10 | needs-scoping; 3 keystone unblocks (work-stream A endpoints, alerting plan, AWS cost analysis) cascade through ~50 BLOCKED items |
| **writegate_honest_coverage_endtoend_2026_05_06**          |                         87 |                             15 |                            1 |                       1 |     1 | keep active; Phase 4.A typed-error rendering = highest leverage next                                                             |
| **dart_ux_cockpit_refactor_2026_04_29**                    |                          7 |                              0 |                            0 |                       0 |     0 | substantively shipped; 7 polish/SSOT items not live-blocking                                                                     |
| **strategy_architecture_v2_finalization_2026_04_19**       |                         67 |                              9 |                            0 |                       1 |     4 | rescope: split into 4 successor plans (post-V1-RETIRE cleanup, futures-roll, UI service-split fold-in, Unity UAT)                |
| **manifest_migration_SUPERSEDED_2026_05_21**               |                         18 |                              0 |                            0 |                       8 |     0 | keep active; convert to codex SSOT after Stage 4                                                                                 |
| **cefi_master**                                            |                         22 |                              4 |                  12 (24 VMs) |                       6 |     2 | keep active; VM-tied work draining 2026-05-08 to 2026-05-09                                                                      |
| **defi_master**                                            |                         32 |                              2 |                            0 |                       6 |     0 | **TOP-PRIORITY P0** (May-23 headline)                                                                                            |
| **tradfi_master**                                          |                         18 |                              1 |                   5+ (5 VMs) |                       2 |     2 | keep active; P1 batch-only this cycle                                                                                            |
| **sports_master**                                          |                         70 |                              0 |                    3 (4 VMs) |                      22 |     0 | keep active; heavy P0 surface, cross-plan coupling                                                                               |
| **predictions_master**                                     |                         35 |                              1 |                            0 |                      13 |     0 | keep active; P1, 14 P0 items in 16 days = tight                                                                                  |
| **infrastructure_master**                                  |                         30 |                              0 |              33 (live tests) |                      17 |     4 | keep active; 9 actionable + 17 blocked                                                                                           |
| **venue_axis_asset_group_vocabulary_2026_04_25**           |                          3 |                              0 |                            0 |                       1 |     0 | **archive-ready** after folding 3 absorbed items into umbrellas                                                                  |
| **instruments_and_market_tick_data_completion_2026_05_01** |                         22 |                              0 |           26 (sports + cefi) |                      13 |     2 | keep active; gates master operator-facing data-status                                                                            |
| **mtds_per_instrument_download_api_2026_04_24**            |                         11 |                              1 |                            0 |                       6 |     1 | keep active; Phase 1.5 critical-path for May-23 (DeFi multi-chain)                                                               |
| **feature_dag_uac_ssot_and_features_coverage_2026_05_06**  |                         11 |                              0 |                            0 |                       7 |     0 | keep active; Phase 1A is highest-leverage 1-day work                                                                             |
| **features_consolidation_and_drilldown_2026_05_06**        |                         14 |                              0 |                            0 |                       4 |     0 | keep active; P2/P3, post-May-23                                                                                                  |
| **ml_training_feature_read_perf_2026_05_06**               |                         11 |                              0 |                            0 |                       0 |     0 | keep active; 1-3 day pure-win, post-May-23                                                                                       |
| **consolidated_ml_advanced_pipeline_2026_04_15**           |                         17 |                              1 |                            0 |                       4 |     0 | rescope; ~70% partially done; cross-asset-group ML scaffolding (no umbrella covers)                                              |
| **consolidated_operational_validation_2026_04_15**         |                         11 |                              0 |                  33 (inputs) |                       9 |     0 | keep active; cross-cutting, fold into master Group F or successor post-May-23                                                    |
| **consolidated_strategy_and_ui_2026_04_15**                |                         32 |                              1 |                            0 |                       8 |     0 | rescope; supersession candidate flagged in plan body itself                                                                      |

**Totals**: ~628 unchecked todos audited / ~40 mis-marked → flipped DONE / ~38 in-flight VM-tied / ~150 cross-plan
blocked / ~26 stale.

---

## 2. Cross-plan dependency graph

```
                ┌──────────────────────────────────────────┐
                │ master_to_live_defi_2026_05_23 (umbrella)│
                │ Group A code-health · B data-correctness │
                │ C runtime-parity · D coverage · E ops    │
                │ F live-trading · G operator UX           │
                └──────────────────────────────────────────┘
                                    ▲
       ┌────────────────────────────┼────────────────────────────┐
       │                            │                            │
       │ feeds Group F live trading │                feeds Group G operator UX
       │                            │                            │
┌──────┴──────┐  ┌──────────────────┴────┐  ┌──────────────────┐ │
│defi_master  │  │cefi_master            │  │tradfi_master     │ │
│ (P0 hd)     │  │ (P0; 24 VMs draining) │  │ (P1 batch-only)  │ │
└─────┬───────┘  └──────────┬────────────┘  └────────┬─────────┘ │
      │                     │                        │           │
      │ blocked by          │ blocked by             │ blocked by│
      ▼                     ▼                        ▼           │
┌─────────────────────────────────────────────────────────────┐  │
│ writegate_honest_coverage_endtoend_2026_05_06               │  │
│   Phase 2.A: adapter migration                              │◀─┘
│   Phase 2.E: orchestrator pre-skip → reasons (PARTIAL)      │
│   Phase 3.D: legacy-row reconcilers (3D.1 + 3D.2 SHIPPED)   │
│   Phase 4.A: deployment-api typed-error rendering (KEY)     │
│   Phase 5: baseline + ratchet (gates May-23)                │
└─────┬───────────────────────────────────────────────────────┘
      │ blocked by
      ▼
┌─────────────────────────────────────┐
│ manifest_migration_SUPERSEDED_2026_05_21│
│ Stage 1: sports rename (operator)   │
│ Stage 4: cross-asset rescan         │
└─────┬───────────────────────────────┘
      │ blocked by
      ▼
┌──────────────────────────────────────┐
│ infrastructure_master     │◀─── 33 backfill VMs are
│ shard-axis SSOT · drilldown · build  │     LIVE TESTS of this
│ raw-tables-migration (cross-asset)   │     plan's shipped infra
└──────────────────────────────────────┘
      ▲
      │ vocabulary basis (Wave A/B/C/D/E shipped)
      │
┌─────┴───────────────────────────────────┐
│ venue_axis_asset_group_vocabulary_      │  ARCHIVE-READY pending
│ 2026_04_25 (3 absorbed items remain)    │  fold into umbrellas
└─────────────────────────────────────────┘

                ┌───────────────────────────────────────────┐
                │ Group G (operator UX) — feeds master      │
                ▼                                           ▼
┌──────────────────────────┐               ┌──────────────────────────────┐
│ dart_ux_cockpit_refactor │               │ strategy_architecture_v2_    │
│ 2026_04_29               │               │ finalization_2026_04_19      │
│ (substantively shipped)  │               │ (rescope: split into 4)      │
└──────────────────────────┘               └──────────┬───────────────────┘
                                                      │ blocks
                                                      ▼
                                         ┌──────────────────────────────┐
                                         │ Group F (live trading) gate  │
                                         └──────────────────────────────┘

      ┌─────────────────────────────────┐
      │ sports_master · predictions_    │
      │ master · features-* + ML        │
      ▼                                 ▼
┌───────────────────────────┐   ┌────────────────────────────────────┐
│ feature_dag_uac_ssot_and_ │──▶│ features_consolidation_and_        │
│ features_coverage         │   │ drilldown                          │
│ (Phase 1A = key 1-day)    │   │ (P2/P3 post-May-23)                │
└──────────┬────────────────┘   └────────────────────────────────────┘
           │ blocks
           ▼
┌─────────────────────────────────┐
│ ml_training_feature_read_perf   │  (self-contained; no upstream)
└──────────┬──────────────────────┘
           │ blocks Phase-1C
           ▼
┌──────────────────────────────────────────────┐
│ consolidated_ml_advanced_pipeline_2026_04_15 │  ~70% partially-shipped
│ consolidated_operational_validation_2026_04_15│  cross-cutting cluster e2e
│ consolidated_strategy_and_ui_2026_04_15       │  supersession candidate
└──────────────────────────────────────────────┘

instruments_and_market_tick_data_completion_2026_05_01:
  ├─ blocked by writegate Phase 2.A (MDPS parity)
  ├─ blocked by predictions_master Phase 1 (canonical_question_group SSOT)
  ├─ blocked by defi_master DeFi-protocol-backfill
  └─ gates master operator-facing data-status verification (≥99% captured)

mtds_per_instrument_download_api_2026_04_24:
  ├─ Phase 1 + Phase 4 done
  ├─ Phase 1.5 chain axis: largely unblocked (UAC CHAIN_RPC_TEMPLATES shipped)
  ├─ Phase 1.5 prediction axis: mostly unblocked (UAC predictions_master partial)
  └─ gates infrastructure_master Phase B.2/C.13 drilldown leaf access
```

---

## 3. Critical path to 2026-05-23

Three keystone unblocks cascade through ~50 BLOCKED items:

### Week 1 (2026-05-07 → 2026-05-13) — KEYSTONE UNBLOCKS

1. **Open `alerting-service-live-rules_2026_*.plan.md`** — does not exist anywhere (confirmed via
   `ls plans/active/ plans/ai/ plans/archive/`). Highest single-line risk to Week-2 alerting/kill-switch verification.
   `master_to_live_defi:work-stream-E` is the home; cascade gates Group F+G.
2. **Ship `master_to_live_defi:work-stream-A` deployment-api endpoints** (`/api/backfill/launch`, `/api/vm/events`).
   Without these the Week-2 Group F/G items cannot start.
3. **Author AWS migration cost-analysis report** — gates all D.1-D.5
   (`infrastructure_master:Phase 5+ deployment build`). Without it, AWS work is permanently gated.

### Week 1 (parallel)

4. **`writegate:Phase 4.A` deployment-api typed-error rendering** — unblocks operator visibility AND
   `infrastructure_master:data_status_multi_axis`. ~3 days; high-leverage.
5. **`feature_dag:Phase 1A`** = highest-leverage 1-day work for LookaheadBiasError honesty. Blocks
   features_consolidation Phase 1B + ML downstream.
6. **`writegate:Phase 2.A` residual** (batch_workers path B/C, `_write_manifest_records` delete, MDPS cluster wiring).
   ~3-4 days.
7. **VM drain awareness** — 24 cefi backfill VMs ETA 2026-05-08 to 09; do not start any cefi-master
   "MTDS-100%-verification" or cross-asset rescan work before VMs stop (manifest_migration_master:Stage 4 explicitly
   waits).

### Week 2 (2026-05-14 → 2026-05-20)

8. **`writegate:Phase 5` baseline + ratchet + workspace QG** — gates May-23 ratchet activation. ~2-3 days.
9. **`writegate:Phase 2.E.3` consumer-class audits** (execution / ml-training / ml-inference / 3× features-\* / strategy
   / reconciliation), 6 audits ~2 days each, parallelisable. GATES live-DeFi May-23 deadline.
10. **DART manual-trade gate (`dart_ux_cockpit:Group G`)** — substantively shipped per DART agent audit; 7 polish items
    not live-blocking. Verify Playwright matrix passes 6 personas × manual-trade flow.
11. **Strategy alpha measurement** — `strategy_architecture_v2:Phase 5 Unity UAT` blocked by external-commercial $550
    fee + Java Feed Connector binary (operator action).

### Week 3 (2026-05-21 → 2026-05-23)

12. **End-to-end live DeFi smoke** — carry_staked_basis lead + leveraged_funding_arb on real wallet, 6-perp-venue hedge
    legs (Bybit, Deribit, Binance, OKX, Hyperliquid, Aster).
13. **AWS↔GCP cloud parity validation** (deferrable post-May-23 per agent findings; hard floor is GCP-only).

### Defer post-May-23 (do NOT attempt before deadline)

- DART v2 archetype roadmap (HUMAN-P1, plan author already flagged "not blocking v1")
- Marketing copy reconciliation (§25.A.1-A.3 vs problem-led pivot)
- features_consolidation Phase 1 (consolidation 500 LOC)
- ml_training_feature_read_perf Phase 4
- All `consolidated_*_2026_04_15` rescoping
- `venue_axis_asset_group_vocabulary` 3 absorbed-item folds
- `mtds_per_instrument_download_api` Phase 2 + 3 P1-deferral

---

## 4. In-flight VM ETAs

37 VMs running as of 2026-05-07T03:30 UTC. Plans referencing these backfills are IN-FLIGHT, NOT BLOCKED — work is in
progress.

### CeFi historical (24 VMs) — ETA 2026-05-07 to 2026-05-09

Owner plan: **cefi_master**.

| Group                          | VMs                                                         | Created             | Elapsed | Heavy/light          | ETA              |
| ------------------------------ | ----------------------------------------------------------- | ------------------- | ------: | -------------------- | ---------------- |
| bitfinex spot 2020-2026 (6)    | `cefi-bitfinex-spot-{2020..2026}-heavy-...`                 | 2026-05-06T08:01-02 |     19h | heavy                | 2026-05-07 to 09 |
| bitfinex futures 2021-2025 (4) | `cefi-bitfinex-futures-{2021,22,23,25}-heavy-...`           | 2026-05-06T09:53-56 |     18h | heavy                | 2026-05-07 to 08 |
| bitget futures 2025-2026 (3)   | `cefi-bitget-futures-2025-h/2025-l/2026-h-...`              | 2026-05-06T10:03-04 |     17h | mixed                | 2026-05-07 to 08 |
| coinbase spot ada+avax (4)     | `cefi-coinbase-spot-2021/22/24-ada-usd + 2025-avax-usd-...` | 2026-05-06T13:28    |     14h | per-instrument light | 2026-05-08       |
| hyperliquid 2024-2025 (2)      | `cefi-hyperliquid-{2024,25}-light-...`                      | 2026-05-06T04:18    |  22-23h | light                | 2026-05-07       |
| kraken futures 2020 (1)        | `cefi-kraken-futures-2020-heavy-...`                        | 2026-05-06T09:57    |     17h | heavy                | 2026-05-07 to 08 |
| kraken spot 2020-2026 (7)      | `cefi-kraken-spot-{2020..2026}-heavy-...`                   | 2026-05-06T17:11-12 |  10-11h | heavy                | 2026-05-08 to 09 |

### TradFi MDPS (5 VMs) — ETA 2026-05-08

Owner plan: **tradfi_master**.

- `mdps-tradfi-{2021,22,23,24,25}-...` created 2026-05-06T05:00, T+22h, ETA 2026-05-08

### Sports recovery (4 VMs) — ETA 2026-05-07 to 2026-05-08

Owner plan: **sports_master**.

- `af-backfill-20260507-033214` (api_football, T+0h)
- `fs-backfill-20260507-010724` (footystats, T+5h)
- `sfi-backfill-20260507-010938` (soccer-football-info, T+5h)
- `us-backfill-20260507-010653` (understat, T+5h)
- ETA: 4-12h depending on date range, so 2026-05-07 to 2026-05-08

### Always-on (1 VM)

- `vm-zombie-watchdog-20260506-175221` — infra; never has an ETA

### NOT currently running (ETAs N/A)

- DeFi backfills: 0 running. **defi_master** has no in-flight VM cover; needs new launches for May-23 critical path.
- Predictions backfills: 0 running. **predictions_master** same.
- ml-training/inference VMs: 0 running.

---

## 5. Plans this audit recommends archiving

**None ready as of 2026-05-07.**

Closest candidates (not yet — listed for follow-up tracking):

- `venue_axis_asset_group_vocabulary_2026_04_25` — 5 main waves all shipped (Wave A/B/C/D/E per CLAUDE.md). 3 absorbed
  items remain (VenueMapping deletion, dashboard SSOT, poolGetSnapshots). Recommend folding those into asset_group
  umbrellas, then archive.
- `dart_ux_cockpit_refactor_2026_04_29` — 9-phase cockpit programme substantively shipped; 7 polish/SSOT items remain.
  Could archive after fold of 3 AGENT-P0 items into a `dart_polish_2026_*` follow-up.

---

## 6. Anomalies + workspace risks

1. **Concurrent `git reset` operations** wiped per-todo audit markers from 4 large plans mid-audit (master_to_live_defi,
   writegate, dart, strategy). Reflog shows 2 separate `reset: moving to HEAD` events. The 16 surviving plans were
   committed + pushed (commit `dada46d1`) immediately to lock them in. Workspace rule "plan-checkbox-flips MUST happen
   at ship time" (CLAUDE.md hard rule per `896c9bc5`) is exactly this lesson.
2. **Plan-body references to folded plans**: `master_to_live_defi` body references `defi_e2e_pipeline_2026_04_30`,
   `leveraged_leg_controller_ 2026_05_01`, `defi_pipeline_extension_2026_05_01` as live plans — all folded into
   `defi_master` per Stage 7 batch consolidation. Work-stream-E EXTEND items + critical-path Week-1 alerting line need
   updating to point at `defi_master:Fork 1`.
3. **Service readiness matrix in master plan** lists `manual_trade_booking_reconciliation_2026_03_22` as "to archive"
   but Stage 1 already archived it. Matrix row should now reference only
   `consolidated_operational_validation_2026_04_15`.
4. **Plan-hygiene work-stream G** assumes ~148 active plans with 140/142/31 affected — Stage 7 batch consolidation
   reduced active/ to ~25 plans, so item counts are obsolete; script scope must re-derive.
5. **Stale module-path reference in manifest_migration_master**: line 473 cites
   `unified_api_contracts.canonical.crosscutting.empty_confirmed_ reasons.EMPTY_CONFIRMED_REASONS` — actual canonical
   module is `honest_coverage.py`. Fix on next ship.
6. **MDPS-1440-NaN reproduction-test** in infrastructure_master is STALE (superseded by writegate Phase 2.A adapter
   migrations + reconciler `MDPS@d3be0ef`).
7. **Phase 3 of strategy_architecture_v2 is entirely STALE**: V1-RETIRE bypassed the 14-21d shadow window per operator
   directive. All 4 OPS items in Phase 3 should be dropped in next housekeeping.
8. **mlr-p3-shap-inference (consolidated_ml_advanced_pipeline)**: SHAP wiring shipped (UAC `InferenceRequest.explain` +
   `inference_shap.py` + orchestrator wiring). Plan body says "no schema field" but verified at
   `internal/domain/ml/schemas.py:605`. Flipped to DONE.
9. **cda-p2-microstructure (consolidated_strategy_and_ui)**:
   `features-service (delta-one family)/.../calculators/microstructure.py` + tests shipped. Flipped to DONE.
10. **features-cross-instrument paired-dispersion stack** (UAC@`0e7ba95` +
    features-cross-instrument@`d1da107`/`071604f`/etc.) belongs to **strategy v2 Phase 9**, NOT to feature_dag plan.
    Confusion risk: anyone reading "features-cross-instrument shipped" in commit logs may falsely flip feature_dag items
    as DONE.
11. **manifest_migration_master is NOT superseded by writegate Phase 3.D.2** reader-side fallback. Read-side fallback
    (UTL@`c5c2669e` + deployment-api@`176c599`) classifies legacy null-reason rows on read; manifest_migration_master
    scripts are the WRITE-side back-fill. Both required.
12. **Lighter `block_height` on-chain replay is INFEASIBLE** (sequencer- internal, NOT zkSync L1).
    `defi_master:dex_historical_replay_*` section needs marking STALE / BLOCKED-ON
    `dex_perp_onboarding_handover Item C`.
13. **`alerting-service-live-rules_2026_*.plan.md` does not exist anywhere** in active/ai/archive.
    master_to_live_defi:work-stream-E references it as the alerting plan — must be authored before any Week-2 Group F
    alerting verification.

---

## 7. Operator action items (in priority order)

1. **Open the alerting plan**. Single highest leverage. ~1 hour. Unblocks master:work-stream-E + Group F alerting
   verification.
2. **Ship `master_to_live_defi:work-stream-A` deployment-api endpoints** (`/api/backfill/launch`, `/api/vm/events`). 1-2
   days.
3. **Author AWS migration cost-analysis report**. Gates D.1-D.5 + cloud parity Group D.
4. **Drain 24 cefi VMs (ETA 2026-05-08/09) before launching cross-asset manifest rescan**. Schedule the rescan launch
   for 2026-05-09 09:00 UTC.
5. **Update `master_to_live_defi` plan body** to drop refs to folded defi-\* plans + obsolete plan-hygiene counts
   (anomalies #2, #4).
6. **Author `master_to_live_defi:Phase Audit-Followup`** that lists the 13 anomalies above so they don't fall off the
   radar.
7. **DART live-readiness check**: confirm 6-persona Playwright matrix passes manual-trade flow. Plan claims it does;
   verify by running.
8. **Strategy `Phase 5 Unity UAT`**: pay $550 fee + acquire Java Feed Connector binary. Operator-only.

---

## 8. Sub-agent IDs (for follow-up SendMessage if needed)

| Cluster                   | Agent ID            |
| ------------------------- | ------------------- |
| master_to_live_defi       | `a4e4b25035dc1d61e` |
| writegate_honest_coverage | `a3f456bbd88c77198` |
| dart_ux_cockpit_refactor  | `a6036d08c25dfc3a1` |
| strategy_architecture_v2  | `a219040e2d22d62db` |
| manifest_migration_master | `a03f5a3fb2c072fea` |
| 5 asset_group umbrellas   | `a775c69dc6e14e657` |
| infrastructure cluster    | `a95f323a70fcbaa02` |
| features + ML cluster     | `a262040dedc07c538` |

---

## 9. Re-running this audit

This audit is a snapshot. Recommended cadence: weekly, or after any major backfill completion. To re-run:

1. `git fetch origin live-defi-rollout && git pull` to sync plan state.
2. `gcloud compute instances list --filter="status:RUNNING"` for current VMs.
3. Per-cluster sub-agent prompts in this conversation provide the template.
4. Push commit immediately after agent edits to defeat concurrent resets.
