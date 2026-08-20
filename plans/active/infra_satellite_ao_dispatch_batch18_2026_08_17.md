---
doc_type: plan
title: Infra satellite — na-eligibility-audit RECLASSIFY_SPLIT extraction batch (batch 18)
summary: >-
  Extraction batch from the infra tranche's 2026-08-17 `/na-eligibility-audit` run — 6 conflict-cleared,
  bounded/deterministic todos pulled from 6 source docs (RECLASSIFY_SPLIT bounded items; each source doc's remaining
  open items stay `assigned_vm: NA` and are unaffected). Each todo cites its exact source doc; this run flipped the
  extracted checkbox in each source doc at authoring time to cite this batch, matching the na-eligibility-audit
  skill's Phase 3 "per-todo split" extraction mechanics. Conflict-checked against every existing active batch/finalize
  plan for this tranche (incl. batch17), the infra consolidated-closeout doc, and every other active
  `assigned_vm:planning` doc via the shared four-surface protocol before drafting — no item here duplicates ground an
  existing dispatched todo already claims. Two items found during this same conflict-check turned out to be
  ALREADY covered by prior batches and are explicitly NOT included here (see "Deliberately excluded" below).
status: active
nature: process
asset_group: [infrastructure]
stage: [meta, data]
repos:
  [
    deployment-service,
    market-tick-data-service,
    client-reporting-api,
    features-service,
    instruments-service,
    e2e-testing,
  ]
scope: [engineer, admin]
tags: [infra, ao-dispatch, satellite, batch-18, na-eligibility-audit]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch17_2026_08_16.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md,
    /plans/active/issues/deployment_service_prod_terraform_drift_2026_08_07.md,
    /plans/active/issues/deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md,
    /plans/active/issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md,
    /plans/active/manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md,
    /plans/active/repo_scripts_governance_audit_2026_06_18.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/06-coding-standards/cli-convention.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/empty_confirmed_and_coverage_correctness_audit_2026_08_15.md,
    /plans/active/issues/deployment_service_prod_terraform_drift_2026_08_07.md,
    /plans/active/issues/deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md,
    /plans/active/issues/shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md,
    /plans/active/manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md,
    /plans/active/repo_scripts_governance_audit_2026_06_18.md,
    /plans/active/infra_satellite_ao_dispatch_batch17_2026_08_16.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `/na-eligibility-audit infra` (2026-08-17, dispatch agt-4d48a4) — Phase 1 per-todo RECLASSIFY_SPLIT classification
  across a 5-hunter Workflow fan-out (44 in-scope docs), Phase 2 conflict-check against the full active corpus before
  drafting.
---

# Infra satellite — na-eligibility-audit extraction, batch 18

## Rules this plan follows

Same discipline as `infra_satellite_ao_dispatch_batch17_2026_08_16.md`: same-priority todos touch disjoint file sets;
`sequential:` unset; genuinely operator-gated/judgment items from each source doc are left there, not extracted.
Todos 6 and 7 below both touch `deployment-service`'s watchdog-coverage registry, so they are merged into ONE todo
rather than split into two same-priority concurrent items on the same file.

## Deliberately excluded (found during this run's conflict-check, not acted on here)

- **`gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`'s two remaining open items**
  (enumerate live Cloud Run runtime SAs; document default-compute-SA blast radius) — a Phase-1 hunter flagged these as
  RECLASSIFY_SPLIT candidates, but conflict-check found `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md`
  already dispatched and SHIPPED both (`deployment-service@f5ad937bee`, `deployment-service@2062cb7ba1`) — the source
  doc's checkboxes were simply never flipped to cite that. Fixed as a KEEP-NA-STALE citation correction directly on
  the source doc instead of re-extracting; not duplicated here.
- **`defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md`'s relaunch item** (and the identical item in
  `defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md`'s todo 2) — already claimed by
  `defi_satellite_ao_dispatch_batch14_2026_08_16.md`'s todo ("Relaunch the legacy-fold VM with the fixed worker
  count..."), not yet executed there. Both source docs' checkboxes annotated with that citation instead of
  re-extracting a competing claim.

## Todos

- [x] ✅ [DATA] P1. **DeFi `empty_confirmed` breakdown + `EXPECTED_INSTRUMENT_NOT_LISTED` semantics — CLOSED
      STALE-DUPLICATE 2026-08-18 (slot-11, data_engineering), no new investigation needed.** This todo's premise ("mid-run
      at the 2026-08-15 session checkpoint, not yet reported") was extracted from a snapshot taken mid-checkpoint on
      2026-08-15 — but by the end of that SAME session (same day), the source doc's `/autonomous` execution pass
      finished the last of its 9 original audit todos, and the breakdown + semantics work landed as todos 4 and 5 in
      `empty_confirmed_and_coverage_correctness_audit_2026_08_15.md` (both `[x]` RESOLVED, full grain/chain/venue/date/
      error_reason breakdown for the 78.7M rows + the `EXPECTED_INSTRUMENT_NOT_LISTED` "both true" nuanced resolution
      with 2 confirmed real incidents) — literally the same scope as this todo's own title. The 2026-08-17
      na-eligibility-audit extraction that created this todo didn't account for that later same-day completion. Source
      doc's own stale placeholder (its item citing this extraction) corrected in the same edit to point back at todos
      4/5 instead. No manifest mutation, code change, or ship was needed or performed. Source:
      `empty_confirmed_and_coverage_correctness_audit_2026_08_15.md` todos 4 & 5.

- [x] ✅ [INFRA] P2. **Retry the 3 crash-loop alert-policy creates.** Retry the 3
      `google_monitoring_alert_policy.cloud_run_service_crash_loop` resource creates (3 named services) now that the
      `restart_count` metric should be queryable (was 404ing after 3 retries over ~30min as of 2026-08-16). **Done
      when**: `tofu plan` shows zero diff for all 3 alert-policy resources, or a fresh root-cause is filed if they
      still 404. Repo: deployment-service. Source: `deployment_service_prod_terraform_drift_2026_08_07.md`.
      **RESOLVED 2026-08-20 (slot-12, task infra_satellite_ao_dispatch_batch18-bdde083837b7)**: retried via
      `ENV=prod ./tofu.sh apply -target='google_monitoring_alert_policy.cloud_run_service_crash_loop'` — all 3 still
      404 (`Cannot find metric(s) that match type = "run.googleapis.com/container/restart_count"`). Fresh root cause
      filed: that metric type is not a real Cloud Run descriptor (verified via Monitoring REST API — 26
      `run.googleapis.com/container/*` descriptors, none named restart_count; 0 time series; the memory-HIGH and
      instance-zero policies for the same 3 services created fine). Issue:
      `/plans/active/issues/cloud_run_crash_loop_alert_policy_invalid_metric_2026_08_20.md`. No code change needed
      for this todo (config fix tracked in the issue doc).

- [x] ✅ [INFRA] P2. **Re-add `cost_snapshot_cron`'s X-API-Key header via Secret Manager.** — deployment-service@13ebe52635; Evidence: quality-gates.sh PASS (3650 passed, 5 skipped), tofu fmt -check PASS. `cost_snapshot_scheduler.tf`
      dropped the `X-API-Key` header when it migrated off a hardcoded literal; re-add it sourced from a proper Secret
      Manager reference (never a literal). This is now load-bearing since `DISABLE_AUTH=false` went live — the cron
      currently 401s silently every 12h without it. **Done when**: the cron's next scheduled fire succeeds
      (non-401), verified via Cloud Scheduler execution history or Cloud Run request logs. Repo: deployment-service.
      Source: `deployment_service_prod_terraform_drift_2026_08_07.md`.

- [x] ✅ [INFRA] P2. **Remove the dead `alerting_paging_cron` import block.** `_imports_reconcile.tf`'s import block
      for the Cloud Scheduler resource was confirmed live `NOT_FOUND` — matches this same file's own documented precedent for 2 prior
      identical dead-import removals. Currently hard-blocks any untargeted `ENV=dev tofu plan`. **Done when**: the
      import block is removed and a fresh untargeted `ENV=dev tofu plan` no longer errors on this resource. Evidence:
      `deployment-service@77d89c8887`; `ENV=dev ./tofu.sh plan -no-color` exit 0; quality-gates.sh PASS (3650 passed, 5 skipped).
      Note:
      this file is also touched by `deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md`'s
      remaining `[OPERATOR]`-gated items (module-duplication + prod-hardcoding decisions) — this todo only removes
      the one confirmed-dead import block, not the broader unresolved items. Repo: deployment-service. Source:
      `deployment_service_t1_recon_duplicate_module_definitions_2026_08_09.md` item 3.

- [x] ✅ [INFRA] P2. **Pin gcloud identity per-invocation in VM launcher scripts.** Audit `launcher_common.sh` and
      `launch-*.sh` for any bare `gcloud` call relying on the ambient/global active account instead of an explicit
      `--account=`/`CLOUDSDK_CORE_ACCOUNT`, and pin it explicitly — prevents a cross-slot active-account clobber on
      the shared host from silently redirecting a launcher's `gcloud` calls to the wrong identity. **Coordination
      note**: `infra_satellite_ao_dispatch_batch17_2026_08_16.md` also touches `launcher_common.sh` (SPOT-provisioning
      params, still `[OPERATOR]`-gated as of this batch's authoring) — different concern, no claim overlap, but pull
      latest before editing to avoid a stale-base diff. **Done when**: every bare ambient-account `gcloud` call in
      these files is pinned, verified via a targeted grep (`gcloud (?!.*--account)` or equivalent) showing zero
      remaining bare calls. Repo: deployment-service. Source:
      `shared_host_gcloud_active_account_cross_slot_clobber_2026_08_04.md` item 1. — deployment-service@062c79c3f9; Evidence: quality-gates.sh PASS (3652 passed, 5 skipped), bash -n PASS on all four modified launchers, and all launchers with host-side gcloud references inherit or declare CLOUDSDK_CORE_ACCOUNT.

- [ ] [INFRA] P2. **Author the Terraform diff for the 45 classified-STRIP-buckets lifecycle policy; re-run the
      cost-delta query once shipped.** The source doc's full 105-bucket STRIP/KEEP/UNCLEAR classification is done (5
      UNCLEAR buckets excluded pending an operator call, not in scope here); its blocking precondition
      (`deployment_service_prod_terraform_drift`) is now resolved. Author + ship the Terraform diff for the 45
      known-STRIP buckets' GCS lifecycle policy — **code + ship only; `tofu apply` itself stays operator-executed**,
      matching this doc's own established pattern for infra changes. Once shipped, re-run the `bq` before/after
      $/day query (same shape already used earlier in the source doc) to quantify the actual realized cost delta,
      and record it back in the source doc. **Done when**: the Terraform diff is committed + `tofu plan` shows the
      expected 45-bucket lifecycle-rule diff with zero unexpected changes, and the cost-delta table is recorded.
      Repo: deployment-service. Source: `manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md`
      (lines 109/135 — near-duplicate content in the source, treat as one task).

- [ ] [INFRA] P2. **Wire manifest-consolidator watchdog coverage for `ml_service` and the bespoke `*_daily_cron`
      launchers.** Two related gaps in the same watchdog-coverage registry, merged into one todo to avoid a
      same-file concurrent-edit risk: (1) determine whether `ml_service`'s GCS prefixes can be derived per-launcher
      and wire watchdog coverage the same way the other 5 families were wired this same day; (2) for the bespoke
      `*_daily_cron` launchers, confirm each one's actual write target before wiring — do not assume. **Done when**:
      both families appear in the watchdog's coverage report with a verified (not assumed) prefix mapping. Repo:
      deployment-service. Source: `manifest_consolidator_and_lifecycle_cost_optimization_2026_08_16.md` (lines
      210, 220).

- [ ] [SCRIPT] P2. **PROMOTE-TO-CLI — client-reporting-api.** File `daily_update.py` as a `client-reporting-api` CLI
      subcommand, per `/codex/06-coding-standards/cli-convention.md` (`--operation`/`--mode` convention). Delete the
      standalone script once the subcommand is verified equivalent. Repo: client-reporting-api. Source:
      `repo_scripts_governance_audit_2026_06_18.md` (PROMOTE-TO-CLI item).

- [ ] [SCRIPT] P2. **PROMOTE-TO-CLI — features-service.** File `collect_lst_seasonal_rewards_daily.py` and
      `check_pipeline_completeness.py` as `features-service` CLI subcommands. Delete the standalone scripts once
      verified equivalent. Repo: features-service. Source: `repo_scripts_governance_audit_2026_06_18.md`
      (PROMOTE-TO-CLI item).

- [ ] [SCRIPT] P2. **PROMOTE-TO-CLI — instruments-service.** File `measure_honest_coverage.py` and
      `verify_instrument_manifest_coverage.py` as `instruments-service` CLI subcommands. Delete the standalone
      scripts once verified equivalent. Repo: instruments-service. Source: `repo_scripts_governance_audit_2026_06_18.md`
      (PROMOTE-TO-CLI item).

- [ ] [SCRIPT] P2. **PROMOTE-TO-CLI — e2e/weekly-pipeline scripts.** File `run_weekly_pipeline.py` and
      `backfill_vix_yahoo.py` as CLI subcommands of their owning service (confirm the correct owning repo first — the
      source doc's own text is ambiguous between e2e-testing and a data-pipeline service; resolve before filing).
      Repo: e2e-testing (tentative, confirm at execution time). Source: `repo_scripts_governance_audit_2026_06_18.md`
      (PROMOTE-TO-CLI item).

## Progress Log

- **na-eligibility-audit 2026-08-17 (infra tranche, dispatch agt-4d48a4)**: drafted this batch from 6
  conflict-cleared RECLASSIFY_SPLIT candidates found during the 2026-08-17 infra-tranche Phase 1 classification pass
  (44 in-scope docs read end-to-end via a 5-agent fan-out). All 6 source docs' own checkboxes flipped to cite this
  batch at authoring time. Two additional RECLASSIFY_SPLIT candidates found during conflict-check were excluded as
  already-covered-elsewhere rather than re-extracted (see "Deliberately excluded" above).
- **2026-08-18 (slot-11, data_engineering, dispatched task infra_satellite_ao_dispatch_batch18-9efc4d0b3824)**: item 1
  (DeFi `empty_confirmed` breakdown + `EXPECTED_INSTRUMENT_NOT_LISTED` semantics) closed as a stale-duplicate on
  investigation — the source doc's todos 4 and 5 (both `[x]` RESOLVED, same-day 2026-08-15 completion after this
  batch's extraction snapshot was taken) already fully cover this exact scope. No new investigation, code, or manifest
  mutation was needed; only a citation correction on both docs. Read-only doc-only change, no code repo touched.
- **context-scout 2026-08-20**: populated/refreshed context_scope (7 entries)
- **2026-08-20 (slot-12, infra, task infra_satellite_ao_dispatch_batch18-bdde083837b7)**: item 2 (retry the 3
  crash-loop alert-policy creates) RESOLVED via root-cause filing — the targeted prod apply still 404s because
  `run.googleapis.com/container/restart_count` is not a real Cloud Run metric descriptor (26 container descriptors
  exist, none named restart_count; memory-HIGH + instance-zero policies for the same 3 services created fine). Fresh
  issue doc: `plans/active/issues/cloud_run_crash_loop_alert_policy_invalid_metric_2026_08_20.md` carries the fix
  todos (rework onto a logs-based metric, or remove). No deployment-service code change performed.
