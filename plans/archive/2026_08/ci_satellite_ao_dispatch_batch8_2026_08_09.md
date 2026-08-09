---
doc_type: plan
title:
  CI satellite AO batch 8 — eighth AO-dispatch extraction for the ci tranche (agent_operating_framework_master group)
summary: >-
  Sibling of `ci_satellite_ao_dispatch_batch7_2026_08_09.md` — same manual satellite-batch-extraction pass over the 15
  `ci`-tranche candidate docs from today's `/ag-closeout-audit ci` run
  (`issues/ag_closeout_audit_ci_parked_2026_08_08.md`), split into a separate batch doc because its one extracted item's
  source carries `parent_epic: agent_operating_framework_master` rather than `infrastructure_master` — a corpus-wide
  frontmatter-hygiene fix (invalid `assigned_role: devops` value) that happens to have been surfaced by a
  `ci`-tranche-adjacent audit pass. See batch 7's own Progress Log for the full 15-doc disposition ledger; not
  duplicated here.
status: complete
nature: process
asset_group:
  [ci] # corrected 2026-08-09 (/ag-closeout-audit ci) -- was [ci, cross-cutting]; batch-extraction docs are single-
  # tranche by construction (per SKILL.md's own authoring discipline), content is a ci-tranche satellite batch, no
  # cross-AG scope
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, ao-dispatch, close-out, batch-8, satellite-docs, plan-hygiene, frontmatter, assigned-role]
related:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch7_2026_08_09.md,
    /plans/active/ci_satellite_ao_dispatch_batch8_finalize_2026_08_09.md,
    /plans/archive/2026_08/issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
effort: medium
sequential: false
drift_direction: none
context_scope:
  [
    /plans/archive/2026_08/issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md,
    agents/infra.md,
    agents/cicd.md,
    scripts/docs/docspec.py,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Manual satellite-batch-extraction pass, run 2026-08-09, against the `ci`-tranche candidate list from today's
  `/ag-closeout-audit ci` run. This item's source doc
  (`issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md`) carries `parent_epic:
  agent_operating_framework_master`, distinct from the `infrastructure_master` group extracted into sibling batch 7 —
  split per the parent_epic-grouping rule.
---

# CI satellite AO batch 8 (agent_operating_framework_master group)

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** The single todo (corpus-wide `assigned_role: devops` retag, 15 docs) shipped
> (`unified-trading-pm@987cb5734`), `grep -l '^assigned_role: devops$' plans/active/*.md plans/active/issues/*.md`
> confirmed zero results. Archived in the same session per the archival HARD RULE
> (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). Finalize plan
> `ci_satellite_ao_dispatch_batch8_finalize_2026_08_09.md` (source-doc reconciliation + this archival) completed and
> archived alongside. Successor: none.

> **Why this is a separate doc from batch 7.** Both batches came out of the same 2026-08-09 pass over the same 15
> `ci`-tranche candidate docs. This item's own source doc frontmatter names a different `parent_epic`
> (`agent_operating_framework_master`, not `infrastructure_master`) — grouping extractable items by `parent_epic` means
> a separate batch+finalize pair per group, even when the total item count is small.

## Todos

- [x] 1. ✅ [DOC] P3. **Retag every doc still carrying the invalid `assigned_role: devops` frontmatter value** to the
      correct real role from the live `agents/*.md` registry (`backend_engineer`, `cefi_mtds_smoke_tester`,
      `cefi_reconciliation_auditor`, `cicd`, `data_engineering`, `docs_reconciler`, `infra`, `main`, `monitor`,
      `plan_health`, `quant_dev`, `review`, `ui_developer`, `worker`, plus the audit-role names — re-derive the live
      list from `agents/*.md` at execution time, do not trust this list blind). Read each doc's actual subject matter
      and pick the best fit (mirror the judgment already used on the 2 docs fixed before the source issue was even
      filed: `infra` for host/VM-adjacent content, `cicd` for CI/CD-pipeline content) — never default every match to the
      same value. **Re-derive the live population fresh**
      (`grep -l '^assigned_role: devops$' plans/active/*.md plans/active/issues/*.md`) rather than trusting a static
      count — the corpus changes daily and already grew from 10 named docs at the source issue's filing time
      (2026-08-08) to 12 confirmed live as of this batch's own authoring (2026-08-09):
      `agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md`,
      `build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`,
      `digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`,
      `fleet_host_inventory_dead_host_and_pre_rewrite_drift_2026_08_08.md`,
      `glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md`,
      `image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md`,
      `ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md`,
      `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`,
      `semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md`,
      `sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md`,
      `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`,
      `unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md` (all under `plans/active/issues/`). Validate the
      new value against the live registry, never hand-type a near-miss. **Done when**:
      `grep -l '^assigned_role: devops$' plans/active/*.md plans/active/issues/*.md` returns zero results. Source:
      `issues/assigned_role_devops_invalid_value_corpus_wide_2026_08_08.md` (its own `[DOC] P3` todo, 10 docs named at
      authoring time) — never cited by any covering doc.

## Codex SSOTs

- `/codex/11-project-management/doc-frontmatter-schema.md` — `assigned_role` field definition + registry validation
- `plans/active/task_template.md` §4 — finalize-plan-coverage rule

## Progress Log

- **2026-08-09** — Drafted alongside sibling batch 7, splitting this one `agent_operating_framework_master`-epic item
  out per the parent_epic-grouping rule. Full 15-doc disposition ledger (which docs contributed zero and why) is
  recorded once, in batch 7's own Progress Log — not duplicated here.
- **2026-08-09** — Todo 1 done (slot 13). Re-derived the live population fresh
  (`grep -l '^assigned_role: devops$' plans/active/*.md plans/active/issues/*.md`) — 15 docs live at execution time (2
  from the plan's own 12-doc list already resolved by other work:
  `fleet_host_inventory_dead_host_and_pre_rewrite_drift_ 2026_08_08.md`,
  `unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md`; 5 new:
  `safe_doc_push_prek_patch_ not_restored_on_retry_success_2026_08_09.md`,
  `tier_a_ci_status_gate_unrecoverable_deadlock_2026_08_09.md`,
  `quickmerge_setup_bootstrap_loop_blocks_commit_2026_08_09.md`,
  `todo_cancelled_disposition_format_breaks_todo_ regression_check_2026_08_09.md`,
  `unified_trading_ci_lint_red_shellcheck_findings_2026_08_09.md`). Read each doc's subject matter and retagged: `infra`
  (host/VM-adjacent) for `build_deploy_pipeline_provenance_and_aws_deferred_gaps_ 2026_07_21.md` (AWS tarball
  launcher/bucket) and `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md` (shared orchestrator-VM gcloud
  credential poisoning); `cicd` (CI/CD-pipeline content) for the remaining 13 (GH Actions workflows,
  promote/SIT/quickmerge/ci_status pipeline mechanics — `todo_cancelled_disposition_format_...md` matches cicd.md's own
  `plan_health` wall-type todo-regression handling).
  `grep -l '^assigned_role: devops$' plans/active/*.md plans/active/issues/*.md` now returns zero results — done-when
  met. Evidence: `unified-trading-pm@987cb5734`.
