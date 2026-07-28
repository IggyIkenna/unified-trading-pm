---
title: Open-issues triage against mega audit — 2026-05-20
created: 2026-05-20
author: background agent (delegated by slot-1 main)
source:
  - operator directive 2026-05-20 "no clean issues outside this known audit we don't have a clean base"
  - parent tracker: mega_audit_and_plan_beefup_progression_2026_05_20.md
locked_by: live-defi-rollout
---

## Purpose

Classify the 28 unresolved issue docs under `plans/active/issues/` against the mega-audit framework in
`mega_audit_and_plan_beefup_progression_2026_05_20.md` so the operator can batch-apply banners/archival in a single
sweep. After this sweep no issue is "in limbo" — every one is subsumed, plan-covered, fixed, or genuinely standalone
with a named next step.

## Triage table

| Issue | Bucket | Pointer | Recommended action | Confidence | |
-------------------------------------------------------------------------- | ------------------------------------- |
------------------------------------------------------------------------------------------------------------------ |
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| ---------- |
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
| ---- | | `archive_deferred_migration_2026_05_19.md` | STANDALONE-OPEN | — | Mechanical sweep: 24 archived plans need
`MIGRATED FROM` annotations or successor pointers. Schedule as a 1.0 cal-day janitorial sweep — own one slot-day. Not
subsumed by mega-audit (no contract/schema content). | HIGH | | `bucket_name_ssot_residual_drift_2026_05_18.md` |
EXISTING-PLAN | `bucket_name_ssot_canonicalisation_2026_05_10.md` | Banner: covered by parent plan's Done-def #6
(zero-drift verification). Mega-audit A1 inventory will independently catch via "no hardcoded `gs://`" compliance row,
but this issue's findings already live in the parent plan body. | HIGH | | `changelog_update_2026_05_19.md` |
OPEN-QUESTION | — | Operator decision Option A (do nothing pre-1.0.0) vs Option B (add CHANGELOG.md + cron). Recommended
in issue body = Option A. Trivially closeable once operator picks. | HIGH | |
`concurrent_backfill_during_phase_2_6_migration_2026_05_15.md` | ALREADY-FIXED | — | Status: LESSONS-LEARNED.
Empirically safe (0 attempted_failed in 214k rows). Verification:
`grep -r "Phase 2.0 drain" plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` should confirm
gate-rationale documentation update happened. If not, 0.1 cal-day to add the "WHY safe" annotation to the gate. | HIGH |
| `cross_asset_instruments_service_scope_2026_05_14.md` | OPEN-QUESTION | — | Pure design call (3 options spelled out —
extend IS, new service, or features-owns). Needs ikenna or operator pick. Not on May-23 path. | HIGH | |
`defi_upstream_46day_full_backfill_2026_05_16.md` | OPEN-QUESTION | — | Operator approval request for 46-day MDPS DeFi +
IS DeFi backfill. Cross-references master plan; awaits explicit operator ack to launch backfill VMs. Phase A3 manifest
divergence report will quantify the gap but the _fix_ (backfill) is an operator-launched op. | HIGH | |
`deployment_api_shard_detail_gcs_locked_2026_05_17.md` | STANDALONE-OPEN | — | Post-cutover hygiene (P2). Not subsumed
by mega-audit (no schema/contract drift — just cloud-agnostic refactor). Recommend including in a post-cutover refactor
sprint plan (new sub-plan) — estimate 2.5 cal-days. Defer until post-June-1. | MEDIUM | |
`execution_service_method_size_violations_workspace_outlier_2026_05_17.md` | MEGA-AUDIT:D:D6 | Phase D6 strategy +
execution beef-up | Banner: D6 strategy+execution plan should absorb this as a "code-hygiene phase" of the
execution-service section. Method-size sweep folds naturally into the audit-driven backlog because C7/C8 audits will
read execution-service code anyway. | MEDIUM | | `execution_service_test_harness_missing_methods_2026_05_18.md` |
MEGA-AUDIT:C:C7 | C7 strategy → execution audit | Banner: C7 audit hits execution-service test surface; missing harness
methods (`_read_book_metrics`, `_parse_candle_horizon_secs`) will surface in audit's "tests pass" check. Trivial fix
lands in D6 backlog. | MEDIUM | | `expected_unattempted_validation_pending_phase3_2026_05_19.md` | MEGA-AUDIT:A:A3 | A3
manifest divergence report | Banner: A3 will produce the exact validation data this issue is waiting on
(`expected_unattempted` row counts per asset_group post-MTDS-Phase-3 run). The validation is auto-satisfied by A3
producing the manifest_divergence parquet. | HIGH | | `features_service_todo_audit_2026_05_19.md` | MEGA-AUDIT:C:C4 | C4
MTDS → features audit + C6 features → strategy audit | Banner: 9 TODOs split — Group 1 (futures roll) lands in C2
IS→strategy + C4 MTDS→features; Group 2 (aave on-chain) lands in C4; Group 3 (sports migration) lands in C6 or D5.
Audit-driven coverage. | MEDIUM | | `kalshi_polymarket_classify_venue_error_missing_2026_05_18.md` | ALREADY-FIXED | — |
Resolution block already present in file ("RESOLVED 2026-05-18 — execution-service@a2b5eef46"). Verification:
`cd .tabs/1/execution-service && git log --oneline a2b5eef46 -- execution_service/sports_execution/adapters/exchanges/`.
Operator should add top-level `resolved:` frontmatter + archive. | HIGH | |
`marinade_solana_subgraph_registration_2026_05_17.md` | OPEN-QUESTION | — | Operator decision Path A (Marinade subgraph
signup) vs Path B (Helius archive tier) vs Path C (defer with static APR). External-data rule applies: must pick a
credentialled path — not silent deferral. P2 (mSOL is Tier 2). | HIGH | | `ml_repo_consolidation_preaudit_2026_05_19.md`
| EXISTING-PLAN | `ml_repo_consolidation_2026_05_19.md` | Banner: this IS the Phase 0 pre-audit artifact for the named
consolidation plan. Stays in issues/ as the parent plan's diagnostic input until the consolidation finishes, then
archives with the parent. | HIGH | | `paper_defi_pre_run_data_readiness_2026_05_19.md` | EXISTING-PLAN |
`phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` + `promote_workflow_may23_cli_path_2026_05_10.md` |
Banner: data-readiness gate naturally belongs in the paper-trade runbook plan; the recommended
`PaperRunDataReadinessCheck` is a feature of `e2e-testing/scripts/defi/run-paper.sh`, owned by the May-23 CLI promote
plan. Should also leverage mega-audit A2 `expected_coverage()` once it lands. | MEDIUM | |
`prediction_polymarket_phantom_manifest_14403_2026_05_19.md` | EXISTING-PLAN |
`gcs_migration_bundle_pipeline_mode_2026_05_08.md` + `gate_3_phantom_audit_runbook_2026_05_13.md` | Banner: P0 migration
regression — owned by Phase 3.6 of the migration plan + the phantom-audit runbook. Phase 6 --apply is BLOCKED until
root-cause confirmed. Mega-audit A3 divergence report will ALSO surface this class but the immediate response is in the
migration plan. | HIGH | | `qg_basedpyright_or_true_bug_2026_05_18.md` | MEGA-AUDIT:D:cross-cutting-QG-ratchet |
Cross-cutting QG ratchet plan | Banner: the
`                                                                                                                                                                                                                                                                                                                                                        |            | true`
bug + the "16 silent errors in batch-live-reconciliation" finding is precisely a QG-ratchet item. Mega-audit's
QG-ratchet phase (under D) should absorb the fix AND a regression test that asserts non-zero exit on basedpyright error.
| HIGH | | `qg_snapshot_cron_stale_2026_05_18.md` | OPEN-QUESTION | — | Operator action required — slot 7 (harsh) lacks
`cloudscheduler.jobs.create/update`. Cannot triage without ikenna re-enabling the scheduler job or confirming the cron
is intentionally disabled. P1 freshness gap. | HIGH | | `smoke_b_perp_funding_type_schema_drift_2026_05_17.md` |
MEGA-AUDIT:C:C4 | C4 MTDS → features audit (perp_funding schema row) | Banner: Bug 1 (Int64→Datetime drift on
perp_funding) is exactly the kind of contract-pair schema-version row C4 audits. Bug 2 (utilization subprocess stall) +
Bug 3 (Callable NameError) are pre-fixed at features-service@818d8ecc / @64682456 — verify via `git log` then mark
partial-fixed. | MEDIUM | | `stale_manifest_entries_disk_absent_2026_05_18.md` | STANDALONE-OPEN | — | Trivial: 10
absent repos in `workspace-manifest.json`. Recommend a 0.2 cal-day fix to either remove or annotate
`"status": "archived"`. Add disk-presence check to `check-dependency-alignment.py`. Mega-audit doesn't touch manifest
tooling. Pure janitorial. | HIGH | | `strategy_repo_consolidation_preaudit_2026_05_19.md` | EXISTING-PLAN |
`strategy_repo_consolidation_2026_05_19.md` | Banner: Phase 0 pre-audit artifact for the named consolidation plan. Same
shape as ml_repo_consolidation_preaudit — stays in issues/ until parent plan closes. **Important**: this issue corrects
an earlier "ZERO cross-repo imports" fact-report — that correction needs to land in the parent plan body before Phase 4
import-rewrite. | HIGH | | `tardis_smarkets_test_regression_2026_05_17.md` | MEGA-AUDIT:C:C0 | C0 IS → MTDS audit (and
C9 UAC) | Banner: Group A (Tardis network-block isolation) + Group B + Group C (smarkets UAC venue registry gap) all
fall under the IS↔MTDS contract pair OR the UAC consumer audit (C9). 5 test failures get sourced into D4 MTDS preflight
beef-up. | MEDIUM | | `tradfi_forward_poll_cron_missing_2026_05_17.md` | STANDALONE-OPEN | — | P1
continuous-verification gap; requires Cloud Scheduler `tradfi-fwd-` job + `trigger-tradfi-job` Cloud Run service. Not
subsumed by mega-audit (this is a cron/infra deployment, not a contract audit). Recommend a 1.0 cal-day deployment task
— own one operator-permissioned slot. Composes with `qg_snapshot_cron_stale` (same operator-permission constraint). |
HIGH | | `trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md` | STANDALONE-OPEN | — | P2 single-repo GHA
failure (clone step). Not subsumed by mega-audit. Recommend 0.5 cal-day debug session — diagnostic path enumerated in
issue body (reproduce locally, inspect clone_repo invocation context). Could ride along with the workflow-templates
rollout. | MEDIUM | | `uac_coverage_excludes_blank_8b_8c_ratchet_2026_05_17.md` | MEGA-AUDIT:D:cross-cutting-QG-ratchet
| Cross-cutting QG ratchet plan + D3 manifest v8 plan | Banner: UAC's `[tool.coverage.run].omit` is exactly a QG-ratchet
item (the 7 patterns from B1 template, "validation_logic" + "error_classification" surfaces). Mega-audit QG-ratchet plan
should remove the omit lines + drive UAC test coverage to 100%/95%. | HIGH | |
`uac_weekly_validation_wif_secrets_missing_2026_05_17.md` | OPEN-QUESTION | — | Operator action: provision
`WIF_PROVIDER`/`WIF_SERVICE_ACCOUNT` GitHub secrets OR disable workflow. BLOCKED-OPERATOR-DECISION per issue. P3 (per-PR
Schema Health workflow IS gating; weekly is informational). | HIGH | | `unified_api_contracts_todo_audit_2026_05_19.md`
| MEGA-AUDIT:A:A2 + C:C9 | A2 expected_coverage + C9 UAC consumer audit | Banner: Issue 1 (VX front-month CBOE) lands in
C9 + the TradFi OHLCV plan. Issue 2 (5 `# TODO verify` coverage*starts) is \_literally* what A2 `expected_coverage()`
consumes — verification of those dates becomes part of the A2 deliverable. | HIGH | |
`unused_import_audit_2026_05_18.md` | STANDALONE-OPEN | — | P3 cosmetic. 11 trivial ruff F401 fixes across 3 repos.
Recommend: any slot picking up one of those repos in a clean window applies the 1-line fix. Estimate 0.1 cal-day total.
Composes with workspace cleanup sprints; no new plan needed. | HIGH |

## Bucket counts

- **MEGA-AUDIT subsumed**: 9
  - `execution_service_method_size_violations_workspace_outlier_2026_05_17.md` (D:D6)
  - `execution_service_test_harness_missing_methods_2026_05_18.md` (C:C7)
  - `expected_unattempted_validation_pending_phase3_2026_05_19.md` (A:A3)
  - `features_service_todo_audit_2026_05_19.md` (C:C4+C6)
  - `qg_basedpyright_or_true_bug_2026_05_18.md` (D:cross-cutting-QG-ratchet)
  - `smoke_b_perp_funding_type_schema_drift_2026_05_17.md` (C:C4)
  - `tardis_smarkets_test_regression_2026_05_17.md` (C:C0+C9)
  - `uac_coverage_excludes_blank_8b_8c_ratchet_2026_05_17.md` (D:cross-cutting-QG-ratchet)
  - `unified_api_contracts_todo_audit_2026_05_19.md` (A:A2 + C:C9)
- **EXISTING-PLAN covered**: 5
  - `bucket_name_ssot_residual_drift_2026_05_18.md`
  - `ml_repo_consolidation_preaudit_2026_05_19.md`
  - `paper_defi_pre_run_data_readiness_2026_05_19.md`
  - `prediction_polymarket_phantom_manifest_14403_2026_05_19.md`
  - `strategy_repo_consolidation_preaudit_2026_05_19.md`
- **ALREADY-FIXED**: 2
  - `concurrent_backfill_during_phase_2_6_migration_2026_05_15.md`
  - `kalshi_polymarket_classify_venue_error_missing_2026_05_18.md`
- **STANDALONE-OPEN**: 6
  - `archive_deferred_migration_2026_05_19.md`
  - `deployment_api_shard_detail_gcs_locked_2026_05_17.md`
  - `stale_manifest_entries_disk_absent_2026_05_18.md`
  - `tradfi_forward_poll_cron_missing_2026_05_17.md`
  - `trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md`
  - `unused_import_audit_2026_05_18.md`
- **OPEN-QUESTION**: 6
  - `changelog_update_2026_05_19.md`
  - `cross_asset_instruments_service_scope_2026_05_14.md`
  - `defi_upstream_46day_full_backfill_2026_05_16.md`
  - `marinade_solana_subgraph_registration_2026_05_17.md`
  - `qg_snapshot_cron_stale_2026_05_18.md`
  - `uac_weekly_validation_wif_secrets_missing_2026_05_17.md`

Total: 9 + 5 + 2 + 6 + 6 = **28** ✅

## STANDALONE-OPEN — proposed actions

### 1. `archive_deferred_migration_2026_05_19.md` — 1.0 cal-day janitorial sweep

Walk the 24 archived plans listed. For each open DEFERRED item: identify successor in `plans/active/`, add
`**MIGRATED FROM:** <archived_plan>` banner to the successor, add `## Deferred work — migrated to: <successor_plan>`
banner to the archived plan. If no successor exists → create a stub line item in the relevant active plan or in a new
janitorial sub-plan. Suggest: one slot-day, slot 1 main or any slot 4/8.

### 2. `deployment_api_shard_detail_gcs_locked_2026_05_17.md` — 2.5 cal-days post-cutover

New sub-plan: `deployment_api_cloud_agnostic_refactor_2026_06_xx.md` (post-June-1). Migrates `shard_detail.py` +
`cloud_storage_client.py` off GCS-locked `build_bucket()` to `resolve_bucket_uri()`. Defer until after June-1
paper-trade gate; this is post-cutover hygiene (P2). Compose with the AWS migration plan.

### 3. `stale_manifest_entries_disk_absent_2026_05_18.md` — 0.2 cal-day

Two trivial commits to `unified-trading-pm`: (a) annotate the 10 absent repos with `"status": "archived"` in
`workspace-manifest.json` (or move to `removedEntries`); (b) add a disk-presence assertion to
`check-dependency-alignment.py`. One slot-30-minute fix.

### 4. `tradfi_forward_poll_cron_missing_2026_05_17.md` — 1.0 cal-day deployment + operator perms

Provision Cloud Scheduler `tradfi-fwd-daily` + Cloud Run `trigger-tradfi-job` mirroring the cefi pattern.
Operator-permissioned (cloudscheduler.jobs.create). Compose with `qg_snapshot_cron_stale` since both block on same
permission; do them in the same slot-1 ikenna operator session.

### 5. `trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md` — 0.5 cal-day GHA debug

Reproduce locally, inspect clone_repo invocation context, fix or work around. Could ride along with the next
workflow-templates rollout (`rollout-workflow-templates.sh`). Any slot with trading-agent-service in clean state.

### 6. `unused_import_audit_2026_05_18.md` — 0.1 cal-day total

Distribute the 11 F401 fixes across the 3 repos as ride-along commits whenever a slot picks up that repo in a clean
session. No new plan needed.

**Total STANDALONE-OPEN load**: ~5.3 cal-days, of which 2.5 cal-days is post-cutover deferrable. Pre-cutover load: ~2.8
cal-days.

## OPEN-QUESTION — questions for ikenna

### 1. `changelog_update_2026_05_19.md`

**Q**: Adopt CHANGELOG.md for `unified-trading-pm` now (Option B, ~15min/week ongoing toil) or defer to 1.0.0
release-notes runbook (Option A, recommended)? Slot 2's prior recommendation = Option A. Confirm so the 3 deferred
sub-items can either close or fire.

### 2. `cross_asset_instruments_service_scope_2026_05_14.md`

**Q**: For `cross_asset` instrument definitions, pick one: (a) extend instruments-service with `CROSS_ASSET` shard
dimension, (b) spin up a new `cross-instruments-service`, or (c) let features-service own cross-asset instrument
derivation? P2 design call. Affects whether the deployment-UI CROSS_ASSET filter button shows up for
instruments-service.

### 3. `defi_upstream_46day_full_backfill_2026_05_16.md`

**Q**: Approve the 46-day DeFi upstream backfill (instruments-service DeFi + MTDS DeFi raw_tick_data,
2026-04-01..2026-05-16)? Required for full live-DeFi data correctness. Not on 5-day paper-trade critical path. Approval
format documented in issue body.

### 4. `marinade_solana_subgraph_registration_2026_05_17.md`

**Q**: For mSOL historical APR coverage, pick one: (a) Marinade subgraph via The Graph (free tier signup needed), (b)
Helius RPC archive tier (paid tier upgrade), or (c) keep static ~6.5% APR (Tier 2 acceptable for paper, NOT for live).
External-data rule says (c) requires a named successor — what's the path?

### 5. `qg_snapshot_cron_stale_2026_05_18.md`

**Q**: P1 — QG snapshot cron VM hasn't fired since 2026-05-14 (4-day staleness, growing). Slot 7 lacks
`cloudscheduler.jobs.create/update`. Ikenna please verify scheduler job status + re-enable, OR confirm cron is
intentionally paused. Composes with `tradfi_forward_poll_cron_missing` — same permission session.

### 6. `uac_weekly_validation_wif_secrets_missing_2026_05_17.md`

**Q**: UAC weekly schema-validation cron has been failing every Monday since 2026-04-13. Either provision
`WIF_PROVIDER` + `WIF_SERVICE_ACCOUNT` GH secrets on `unified-api-contracts`, or disable the workflow until cassette
parity covers the use case. P3 (not blocking; per-PR Schema Health is the gating workflow).

## ALREADY-FIXED — verification one-liners

### 1. `concurrent_backfill_during_phase_2_6_migration_2026_05_15.md`

This is a LESSONS-LEARNED doc, not a code fix. Verification = confirm Phase 2.0 gate documents WHY it's safe (the
8-day-prior-migration argument):

```bash
grep -n "vacuously satisfied\|migration landed.*days before\|drain gate" /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/unified-trading-pm/plans/archive/2026_05/code_freeze_migrate_backfill_sequencing_2026_05_10.md
```

If no hits, add a one-paragraph annotation to the Phase 2.0 gate description capturing the 2026-05-15 safety rationale.
Then add `resolved: 2026-05-15` to this issue's frontmatter and archive.

### 2. `kalshi_polymarket_classify_venue_error_missing_2026_05_18.md`

Resolution block already in file. Verify the commits landed:

```bash
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/execution-service && \
  git log --oneline a2b5eef46 -1 -- execution_service/sports_execution/adapters/exchanges/kalshi.py execution_service/sports_execution/adapters/exchanges/polymarket_clob.py && \
  git grep -n "classify_venue_error\|ADAPTER_FETCH_FAILED" execution_service/sports_execution/adapters/exchanges/kalshi.py execution_service/sports_execution/adapters/exchanges/polymarket_clob.py | head -20
```

Expected: commit present + ≥5 classify_venue_error sites per file. Then add top-level `resolved: 2026-05-18` to
frontmatter and archive.

## Confidence notes

**HIGH confidence (20 issues)**: Issues with clear pointers (existing-plan name explicitly cited in issue body, or
mega-audit phase obvious from issue subject like "expected_unattempted validation" → A3 manifest divergence). Most
ALREADY-FIXED and OPEN-QUESTION issues are HIGH because their own resolution block / open-question is explicit.

**MEDIUM confidence (8 issues)**: Mostly mega-audit subsumed issues where the audit _will_ surface the finding but I
haven't read the C-audit template to verify the row format. These are: `execution_service_method_size`,
`execution_service_test_harness`, `features_service_todo_audit`, `smoke_b_perp_funding`,
`tardis_smarkets_test_regression`, `paper_defi_pre_run_data_readiness`, `trading_agent_service_workspace_qg`,
`deployment_api_shard_detail_gcs_locked`. Worst-case downside: if the C-audit row format doesn't cover that exact
finding, the issue gets re-promoted to STANDALONE-OPEN at audit-spawn time — non-fatal.

**Patterns I noticed**:

1. **6 OPEN-QUESTIONs map to 2 ikenna operator sessions**: 4 of 6 questions are credential/permission gates (cron, WIF
   secrets, marinade subgraph signup, defi backfill approval) — all closeable in two focused ikenna sessions. Heavy
   concentration.
2. **2 ALREADY-FIXED issues just need archival metadata**: `resolved:` frontmatter + move to archive — 10 minutes of
   operator-batch work.
3. **MEGA-AUDIT subsumed cluster is dense around C4 (MTDS→features) and the cross-cutting QG ratchet**: 4 issues feed
   into those two audit slots. Indicates those audits will be heavyweight.
4. **STANDALONE-OPEN cluster is mostly janitorial (~2.8 pre-cutover cal-days)**: Not strategic loose ends — mostly
   cron/permission/cleanup. The mega-audit really does absorb the substantive contract-drift work.
5. **Two pre-audit manifest issues** (`ml_repo_consolidation_preaudit`, `strategy_repo_consolidation_preaudit`) are
   technically issue-docs only because the consolidation plans needed Phase 0 diagnostic artifacts somewhere — they're
   not real issues, just diagnostic outputs. Recommend a doc/plan-format clarification later: phase-0 artifacts should
   land in `plans/audit/` (mirroring the mega-audit's location for C-audit outputs).

**Classification I'm least sure about**: `paper_defi_pre_run_data_readiness_2026_05_19.md` — I placed it as
EXISTING-PLAN under the May-23 CLI promote plan but it might be cleaner as a STANDALONE-OPEN sub-plan (the
`PaperRunDataReadinessCheck` is a real code-write deliverable, not a "absorb into existing"). If operator disagrees,
flip to STANDALONE-OPEN with a ~1.5 cal-day estimate.
