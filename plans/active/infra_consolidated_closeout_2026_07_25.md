---
doc_type: plan
title:
  Infra consolidated close-out — repo/script governance, dependency/CVE management, org admin, PM plan-hygiene tooling
summary: >-
  New "topic tranche" umbrella (sibling to the 5 asset groups + cross-cutting + ao + ci) for generic
  infrastructure/hygiene work that isn't agent-orchestrator-internal or CI/CD-pipeline-specific: repo/script governance,
  dependency/CVE remediation, terraform drift, org/account admin, uv/pip tooling, PM plan-format/hygiene tooling, and
  generic product/UI bugs with no data-pipeline or single-AG content. Authored 2026-07-25 from a corpus-wide
  classification pass (~32 docs) — the last of the 3 new topic tranches (ao/ci/infra) making the AG↔topic partition (5
  AGs + cross-cutting + ao + ci + infra) total across the whole plans/issues corpus, per operator request.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-ui, execution-service]
scope: [engineer, admin]
tags: [infra, close-out, consolidation, repo-hygiene, cve, terraform, plan-hygiene]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/ao_consolidated_closeout_2026_07_25.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-07-25
last_updated: "2026-07-25"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: infra
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Corpus-wide classification pass (unified-trading-pm, 2026-07-25) splitting generic-infra-flavored docs (previously all
  `asset_group: cross-cutting`, spread across `infrastructure_master`/`plan_hygiene_master`/
  `agent_operating_framework_master`/`deployment_and_user_management_master`/`strategy_master`) into this infra tranche,
  per operator request to make the 5-AG + cross-cutting + ao + ci + infra topic partition total (zero orphans) for
  sharded `/plan-reconcile` and `/ag-closeout-audit` runs.
---

# Infra consolidated close-out

> **Purpose.** One place to see all generic infra/hygiene work that isn't AO-internal or CI/CD-pipeline-specific. This
> plan **references** the source docs; it does not duplicate their content. The catch-all of the 3 new tranches — if a
> doc doesn't fit `ao_consolidated_closeout` or `ci_consolidated_closeout`, it lands here.

## Reachability map

1. **Repo/script governance + dependency/CVE management** → Track 1
2. **Org/account admin + terraform drift** → Track 2
3. **PM plan-format / plan-hygiene tooling** → Track 3
4. **Generic product/UI bugs (no data-pipeline or single-AG content)** → Track 4

## Track 1 — Repo/script governance + dependency/CVE management · P1/P2

**Sources**:
[codex_violations_ratchet_to_five_2026_06_10.md](/plans/active/codex_violations_ratchet_to_five_2026_06_10.md)
(codex-violation/file-size ratchet + splitting oversized source files) ·
[repo_scripts_governance_audit_2026_06_18.md](/plans/active/repo_scripts_governance_audit_2026_06_18.md) (`scripts/` dir
governance — ruff-lint, deprecate/delete audit) ·
[issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md](/plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md)
(CVE vs vcrpy dependency conflict + pyproject duplicate-key) ·
[issues/cve_affected_pinned_deps_remediation_2026_06_18.md](/plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md)
(lift CVE-driven dependency caps once blockers clear) ·
[issues/setuptools_fleet_pysec_2026_3447_bump_2026_07_14.md](/plans/active/issues/setuptools_fleet_pysec_2026_3447_bump_2026_07_14.md)
(fleet-wide setuptools CVE, PYSEC-2026-3447, blocking the zero-tolerance codex gate) ·
[issues/uv_pin_fleet_drift_2026_06_22.md](/plans/active/issues/uv_pin_fleet_drift_2026_06_22.md) (uv binary drifted off
its pinned version on the VM fleet) ·
[issues/pm_scripts_typecheck_debt_2026_06_11.md](/plans/active/issues/pm_scripts_typecheck_debt_2026_06_11.md) (PM
`scripts/` basedpyright typecheck-debt ratchet regression) ·
[utl_uac_reuse_consolidation_remediation_2026_06_10.md](/plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md)
(UTL/UAC dedup/reimplementation consolidation refactor) ·
[stash_pile_workspace_cleanup_2026_06_03.md](/plans/active/stash_pile_workspace_cleanup_2026_06_03.md) (cross-host git
stash-pile audit/cleanup runbook) ·
[issues/service_dockerfile_pattern_normalization_2026_06_17.md](/plans/active/issues/service_dockerfile_pattern_normalization_2026_06_17.md)
(9 services' Dockerfiles inconsistent vs the clean base-image pattern) ·
[issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md](/plans/active/issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md)
(aiohttp-3.14 CVE bump blocked by an aioresponses test-mock incompatibility in execution-service).

**Close-out criterion**: all CVE remediations land (aiohttp/vcrpy, setuptools PYSEC-2026-3447, execution-service
aioresponses migration); the codex-violation ratchet stays green; scripts/ governance sweep complete; uv pin re-synced
fleet-wide; PM typecheck debt cleared; UTL/UAC dedup shipped; Dockerfile pattern normalized.

## Track 2 — Org/account admin + terraform drift · P1

**Sources**: [org_migration_to_odumresearch_2026_06_07.md](/plans/active/org_migration_to_odumresearch_2026_06_07.md)
(GitHub org migration, IggyIkenna→OdumResearch, fleet-wide) ·
[issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md](/plans/active/issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md)
(prod terraform drift backlog — 21 add / 18 change — reconcile-apply) ·
[issues/vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md](/plans/active/issues/vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md)
(VM startup/helper scripts have no auto-rollout to GCS) ·
[issues/managed_by_label_launcher_standardization_2026_07_13.md](/plans/active/issues/managed_by_label_launcher_standardization_2026_07_13.md)
(generic VM/Cloud-Run launcher "managed-by" label convention for deployment-api provenance) ·
[issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md](/plans/active/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md)
(fleet-wide VM-launcher billing-waste audit + pre-flight gate design).

**Close-out criterion**: org migration fully verified fleet-wide (no stale `IggyIkenna` refs); terraform drift
reconciled + applied; VM startup scripts auto-roll to GCS; `managed-by` label convention adopted; the billing-waste
pre-flight gate designed + shipped.

## Track 3 — PM plan-format / plan-hygiene tooling · P2

**Sources**:
[active_plan_inventory_dashboard_2026_07_24.md](/plans/active/active_plan_inventory_dashboard_2026_07_24.md)
(workspace-wide plan-checkbox/AI-days inventory dashboard) ·
[ag_closeout_audit_rollout_2026_07_25.md](/plans/active/ag_closeout_audit_rollout_2026_07_25.md) (the meta-plan driving
this whole `/ag-closeout-audit` rollout — self-referential, included for completeness) ·
[issues/autonomous_session_operator_decisions_2026_07_25.md](/plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md)
(operator-decisions log companion to the rollout plan) ·
[issues/issue_docs_zero_checkbox_sweep_2026_07_24.md](/plans/active/issues/issue_docs_zero_checkbox_sweep_2026_07_24.md)
(corpus-wide sweep for prose-only, zero-checkbox issue docs) ·
[issues/plan_quality_four_line_defense_architecture_2026_07_23.md](/plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md)
(plan-quality four-line-of-defense architecture: task_template/QG hygiene/reconcile skills) ·
[issues/reference_path_convention_2026_07_23.md](/plans/active/issues/reference_path_convention_2026_07_23.md)
(cross-reference leading-slash path convention rollout) ·
[l0_doc_index_generator_2026_06_24.md](/plans/active/l0_doc_index_generator_2026_06_24.md) (L0 doc-index generator +
FF-cron auto-regen) · `task_template.md` (the plan-authoring template/rules doc itself) ·
[codex_vs_repo_docs_ssot_audit_2026_06_01.md](/plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md) (generic "audit
all active repo docs vs codex SSOT" hygiene) ·
[issues/human_led_audit_pool_2026_05_21.md](/plans/active/issues/human_led_audit_pool_2026_05_21.md) (operator's
catalogue/process doc for background-agent-driven issue remediation at scale) ·
[issues/issue_docs_remediation_sweep_2026_06_02.md](/plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md)
(code-fixable-items sweep across the issue-doc backlog) ·
[issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md](/plans/active/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md)
(plan-hygiene tooling migration: prek + fold-to-QG + agentic contradiction resolution) ·
[issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md](/plans/active/issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md)
(stale codex pointer + abandoned INDEX.md drift findings from the daily plan-reconciler) ·
[issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md](/plans/active/issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md)
(generic UI e2e test-helper `?persona=` bug, unrelated to any AG/AO/CI concern).

**Close-out criterion**: each tooling doc's own open todos closed; the zero-checkbox sweep's findings triaged; the
reference-path convention rollout complete corpus-wide.

## Track 4 — Generic product/UI bugs (no data-pipeline or single-AG content) · P2

**Source**:
[issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md](/plans/active/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md)
(8 pre-existing deployment-ui smoke/playwright failures — Daily Costs page, mobile nav; generic product/UI bugs, not
data-pipeline or CI mechanics) ·
[artifact_pipeline_observability_2026_07_17.md](/plans/active/artifact_pipeline_observability_2026_07_17.md)
(build→artifact→deploy lineage UI — Cloud Build images, VM tarballs, drift-vs-running; deployment-observability domain,
not data-pipeline).

**Close-out criterion**: the 8 smoke failures fixed + pw:L2 regression specs added; the artifact-lineage UI's remaining
phases ship.

## Codex SSOTs (read before touching a track)

`/codex/06-coding-standards/` (README + quality-gates.md), `/codex/11-project-management/`.

## Todos

> Verification-only — measures whether the tranche is actually done, not new work to dispatch (`assigned_vm: NA`, not
> itself AO-eligible). Added per `issues/autonomous_session_operator_decisions_2026_07_25.md` entry #38, so the next
> infra audit measures a real covering set instead of re-deriving the same orphan verdict from a zero-todo hub.

- [ ] [REVIEW] P2. Track 1 close-out: all CVE remediations landed (aiohttp/vcrpy, setuptools PYSEC-2026-3447,
      execution-service aioresponses migration); codex-violation ratchet green; `scripts/` governance sweep complete; uv
      pin re-synced fleet-wide; PM typecheck debt cleared; UTL/UAC dedup shipped; Dockerfile pattern normalized.
- [ ] [REVIEW] P2. Track 2 close-out: org migration verified fleet-wide (no stale `IggyIkenna` refs); terraform drift
      reconciled + applied; VM startup scripts auto-roll to GCS; `managed-by` label convention adopted; billing-waste
      pre-flight gate designed + shipped.
- [ ] [REVIEW] P2. Track 3 close-out: each tooling doc's own open todos closed; the zero-checkbox sweep's findings
      triaged; the reference-path convention rollout complete corpus-wide.
- [ ] [REVIEW] P2. Track 4 close-out: the 8 deployment-ui smoke failures fixed + pw:L2 regression specs added; the
      artifact-lineage UI's remaining phases ship.

## Progress Log

- **2026-07-25** — Doc authored from the same corpus-wide classification pass as
  `ao_consolidated_closeout_2026_07_25.md` and `ci_consolidated_closeout_2026_07_25.md` — the third and last of the 3
  new topic tranches. ~32 docs classified into this infra tranche across `infrastructure_master`, `plan_hygiene_master`,
  `agent_operating_framework_master`, `deployment_and_user_management_master`, and `strategy_master`. No fixes applied
  in this pass — pure consolidation for `/ag-closeout-audit`/`/plan-reconcile` sharding.
- **2026-07-26** — First `/plan-reconcile` run **topic-scoped to this tranche** (autonomous mode, operator away). All 32
  Source docs + this hub read; corpus-wide normative refs (`PLAN_FORMAT.md`, `task_template.md`, `INDEX.md`,
  `ACTIVE_INDEX.md`) and codex stayed in scope per the skill's sharding rule. Entry sweep
  `run_hygiene_sweep.sh --ci --no-regen` = **0 hard / 1 soft**; `check_delete_vm_launch_gating.sh` flagged **0**
  candidates inside this tranche (all its hits are cefi/defi/tradfi/sports batch docs); `check_archive_candidates.sh`'s
  4 candidates are all **outside** this tranche, so no archival was performed here. **9 auto-fixes applied across 9
  docs** (dangling archived-plan ref · stale `Delete-when` restatement vs the codex SSOT · 2 starlette todos voided by
  their own doc's later supersession + a measured pin check · a "line 2 is live" claim contradicted by a re-run grep · 2
  residual "confirmed double-fetch" references the same doc already retracted · 3 stale INDEX.md facts incl. a moved
  AUTO-INVENTORY host · a retired `>200k ctx` opus trigger · and 2 separate zero-checkbox issue docs each given real
  todos). **6 items parked** as `BLOCKED-OPERATOR-DECISION` — see
  `/plans/active/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md`. Exit gate re-run after rebasing onto
  current origin: `run_hygiene_sweep.sh --ci` = **0 hard / 1 soft** (the soft warning is the same pre-existing
  delete/VM-launch candidate signal, all of it outside this tranche). Shipped `unified-trading-pm@79f892f40`.
- **2026-07-26** — First `/ag-closeout-audit` run **scoped to this tranche** (autonomous mode, operator away), directly
  after the `/plan-reconcile` pass above. **Headline structural finding: this tranche's covering set is a ZERO-TODO
  digest.** This hub carries no `- [ ]` of its own (`grep -cE '^\s*-\s*\[[ xX]\]'` → `0`), its `depends_on:` is `[]` and
  its `related:` names only the 3 sibling tranche closeouts + the audit SKILL (so the dependency-graph discovery path
  finds no forked children either), and **no `infra_*_satellite_ao_dispatch_batch*` plan has ever existed** in
  `plans/active/` or `plans/archive/` — against 41 such plans across the 5 AGs. So the audit's projection question
  resolves to "everything is orphaned", because nothing in the covering set dispatches anything. All 34 tranche-primary
  docs were read end-to-end (32 Sources + 2 members not yet listed here:
  [issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md](/plans/active/issues/session_bound_vm_monitoring_reliability_gap_2026_07_26.md),
  found unclaimed by ANY of the 4 non-AG tranche closeouts, and
  [issues/infra_plan_reconcile_parked_decisions_2026_07_26.md](/plans/active/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md)):
  **29 orphaned** (28 `orphaned_never_touched` + 1 `orphaned_partial_coverage`), 5 not orphaned (the generated inventory
  dashboard, `task_template.md`, the self-referential rollout meta-plan, and the two operator-decision registers). Phase
  3 drafted
  [infra_satellite_ao_dispatch_batch1_2026_07_26.md](/plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md) +
  [infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md](/plans/active/infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md)
  — **25 todos from 17 source docs, both `status: draft` (NOT ingested; the flip to `active` is the operator's call)**.
  The HARD conflict check ran against all 93 existing batch/finalize/closeout plans plus pairwise across the 25 drafted
  todos: 10 further AO-eligible items were deferred conflict-gated (notably `PYTEST_UNIT_DIR`, where a cefi doc
  prescribes a different approach gated behind 22 test fixes; `DataStatusTab.tsx`, claimed by a cross-cutting batch; and
  `base-service.sh`/`base-library.sh`, a multi-tranche hotspot with no ownership rule), and **3 were resolved by logic
  rather than re-drafted** — the CME BTC/ETH OPT-atom question is answered by an explicit operator ruling recorded in
  `tradfi_consolidated_closeout_2026_07_18.md:196-197`, the `vm_log_archival_scheduler.tf` apply already landed
  (`deployment-service@3cd0b1d`, verified 2026-07-07), and 4 DeFi items are already claimed by defi batches 1/3/4. Also
  measured and reported (not fixed here — reconcile's territory):
  [utl_uac_reuse_consolidation_remediation_2026_06_10.md](/plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md)'s
  25 open boxes are almost certainly false-unchecked residue of its 2026-07-13 AO split — all 10 split children are now
  archived with 0 open todos, and its still-open Phase-9 registry-extract box is contradicted by
  `unified_trading_library/deployment_registry.py` existing and being exported at `__init__.py:695`. Exit gate
  `run_hygiene_sweep.sh --ci --no-regen` = **0 hard / 1 soft**, and the drafts themselves are clean of the
  delete/VM-launch signal.
- **2026-07-26** — Resolved `issues/autonomous_session_operator_decisions_2026_07_25.md` entry #38: flipped
  `infra_satellite_ao_dispatch_batch1_2026_07_26.md` to `active` (finalize stays `draft`, gated by
  `gate_on_depends: true`), and added the 4 Track close-out criteria above as verification todos so a future audit has a
  real covering set to measure against instead of a zero-todo hub.

- **2026-07-27** — Discoverability fix (`na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` Phase 4): 11
  `meta`/`infrastructure`-tagged docs reclassified `assigned_vm: NA → planning` this session were not mentioned anywhere
  in this hub — the exact gap `ag_closeout_audit_scope_widening_triage_2026_07_26.md` already tracks (this tranche's own
  asset_group coverage widened 2026-07-26 to include `meta`/`infrastructure`, but the discoverability index here was
  never backfilled for it). Added here for future tranche-sweep discoverability:
  `docker_artifact_registry_cleanup_policy_2026_07_24.md`, `issues/stranded_prek_stash_patch_2026_07_23.md`,
  `issues/deployment_service_ungated_revision_delete_no_rollback_target_2026_07_26.md`,
  `issues/unified_trading_system_ui_codex_violations_far_exceed_estimate_2026_07_21.md`,
  `issues/quickmerge_agent_files_pure_deletion_gap_2026_07_26.md`,
  `issues/ui_hardcoded_colour_and_localhost_debt_2026_07_21.md`,
  `issues/instruments_service_run_tag_flag_not_applied_2026_07_08.md`,
  `issues/qg_workspace_root_template_drift_12_repos_2026_07_24.md`,
  `issues/ui_repos_eslint_base_config_never_wired_no_explicit_any_unenforced_2026_07_21.md`,
  `issues/claude_code_settings_symlink_chain_broken_2026_07_23.md`,
  `issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md`. None were tracked in any Track above; all are now
  `assigned_vm: planning` and live in the AO backlog.
