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
asset_group:
  [infrastructure] # corrected 2026-07-29 (ag-closeout-audit cross-cutting-tranche run) -- was [cross-cutting]. This is
  # the `infra` tranche's OWN top-level consolidated-closeout/coordinator doc; the 2026-07-27 asset_group_ao_ci_infra_
  # schema_expansion retag (unified-trading-pm@a97bc7bed) re-derived membership for docs CITED in each tranche's
  # Sources list but missed each tranche's own master doc, which still carried its pre-2026-07-27 [cross-cutting] tag.
stage: [meta]
repos: [unified-trading-pm, deployment-ui, execution-service]
scope: [engineer, admin]
tags: [infra, close-out, consolidation, repo-hygiene, cve, terraform, plan-hygiene]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
    /plans/active/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-07-25
last_updated: "2026-08-04"
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
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/11-project-management/,
    /plans/archive/2026_08/issues/ag_closeout_audit_infra_parked_2026_08_07.md,
  ]
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
[issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md](/plans/archive/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md)
(ARCHIVED 2026-07-27, RESOLVED — CVE vs vcrpy dependency conflict + pyproject duplicate-key) ·
[issues/cve_affected_pinned_deps_remediation_2026_06_18.md](/plans/active/issues/cve_affected_pinned_deps_remediation_2026_06_18.md)
(lift CVE-driven dependency caps once blockers clear) ·
[issues/setuptools_fleet_pysec_2026_3447_bump_2026_07_14.md](/plans/archive/issues/setuptools_fleet_pysec_2026_3447_bump_2026_07_14.md)
(ARCHIVED 2026-07-30, RESOLVED — fleet-wide setuptools CVE, PYSEC-2026-3447, bumped 82.0.1→83.0.0, ignore removed) ·
[/plans/archive/issues/uv_pin_fleet_drift_2026_06_22.md](/plans/archive/issues/uv_pin_fleet_drift_2026_06_22.md) (uv
binary drifted off its pinned version on the VM fleet) ·
[issues/pm_scripts_typecheck_debt_2026_06_11.md](/plans/active/issues/pm_scripts_typecheck_debt_2026_06_11.md) (PM
`scripts/` basedpyright typecheck-debt ratchet regression) ·
[utl_uac_reuse_consolidation_remediation_2026_06_10.md](/plans/archive/2026_07/utl_uac_reuse_consolidation_remediation_2026_06_10.md)
(ARCHIVED 2026-07-27; UTL/UAC dedup/reimplementation consolidation refactor) ·
[stash_pile_workspace_cleanup_2026_06_03.md](/plans/active/stash_pile_workspace_cleanup_2026_06_03.md) (cross-host git
stash-pile audit/cleanup runbook) ·
[issues/service_dockerfile_pattern_normalization_2026_06_17.md](/plans/archive/issues/service_dockerfile_pattern_normalization_2026_06_17.md)
(9 services' Dockerfiles inconsistent vs the clean base-image pattern) ·
[issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md](/plans/archive/issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md)
(ARCHIVED 2026-07-27, RESOLVED — execution-service@e00152b6, aiohttp-3.14 CVE bump unblocked) ·
[issues/qg_checkers_missing_claude_worktree_exclusion_2026_08_06.md](/plans/active/issues/qg_checkers_missing_claude_worktree_exclusion_2026_08_06.md)
(28 shared QG checker scripts lack a `.claude` worktree-exclusion pattern, retagged in from `cross-cutting` 2026-08-07).

**Close-out criterion**: all CVE remediations land (aiohttp/vcrpy, setuptools PYSEC-2026-3447, execution-service
aioresponses migration); the codex-violation ratchet stays green; scripts/ governance sweep complete; uv pin re-synced
fleet-wide; PM typecheck debt cleared; UTL/UAC dedup shipped; Dockerfile pattern normalized.

## Track 2 — Org/account admin + terraform drift · P1

**Sources**:
[org_migration_to_odumresearch_2026_06_07.md](/plans/archive/2026_07/org_migration_to_odumresearch_2026_06_07.md)
(ARCHIVED; GitHub org migration, IggyIkenna→OdumResearch, fleet-wide — **CANCELLED 2026-07-27**, operator declined,
staying on `IggyIkenna` Pro; `june_2026_vintage_audit_findings_2026_07_27.md` §5#39) ·
[issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md](/plans/active/issues/prod_terraform_drift_backlog_reconcile_2026_07_24.md)
(prod terraform drift backlog — 21 add / 18 change — reconcile-apply) ·
[issues/vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md](/plans/archive/issues/vm_startup_scripts_no_auto_rollout_to_gcs_2026_07_19.md)
(VM startup/helper scripts have no auto-rollout to GCS) ·
[issues/managed_by_label_launcher_standardization_2026_07_13.md](/plans/archive/issues/managed_by_label_launcher_standardization_2026_07_13.md)
(ARCHIVED 2026-08-03, RESOLVED — deployment-service@db67173 + deployment-api@95a7a19; generic VM/Cloud-Run launcher
"managed-by" label convention adopted, deployment-api echoes it as `managed_by`) ·
[issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md](/plans/archive/issues/vm_billing_waste_first_audit_and_preflight_gate_design_2026_07_24.md)
(fleet-wide VM-launcher billing-waste audit + pre-flight gate design) ·
[issues/cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md](/plans/active/issues/cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md)
(3rd occurrence of green-CI-stale-traffic; drift check + canary-deploy alert shipped, Slack routing open — added
2026-08-06 closeout-linkage fix).

**Close-out criterion**: ~~org migration fully verified fleet-wide (no stale `IggyIkenna` refs)~~ — **DROPPED
2026-07-27**, org migration cancelled by operator ruling, `IggyIkenna` refs are now the permanent correct state, not
drift; terraform drift reconciled + applied; VM startup scripts auto-roll to GCS; `managed-by` label convention adopted;
the billing-waste pre-flight gate designed + shipped.

## Track 3 — PM plan-format / plan-hygiene tooling · P2

**Sources**:
[/plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md](/plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md)
(workspace-wide plan-checkbox/AI-days inventory dashboard) ·
[ag_closeout_audit_rollout_2026_07_25.md](/plans/active/ag_closeout_audit_rollout_2026_07_25.md) (the meta-plan driving
this whole `/ag-closeout-audit` rollout — self-referential, included for completeness) ·
[issues/autonomous_session_operator_decisions_2026_07_25.md](/plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md)
(operator-decisions log companion to the rollout plan) ·
[issues/issue_docs_zero_checkbox_sweep_2026_07_24.md](/plans/archive/issues/issue_docs_zero_checkbox_sweep_2026_07_24.md)
(corpus-wide sweep for prose-only, zero-checkbox issue docs) ·
[issues/plan_quality_four_line_defense_architecture_2026_07_23.md](/plans/active/issues/plan_quality_four_line_defense_architecture_2026_07_23.md)
(plan-quality four-line-of-defense architecture: task_template/QG hygiene/reconcile skills) ·
[issues/reference_path_convention_2026_07_23.md](/plans/active/issues/reference_path_convention_2026_07_23.md)
(cross-reference leading-slash path convention rollout) ·
[l0_doc_index_generator_2026_06_24.md](/plans/archive/2026_07/l0_doc_index_generator_2026_06_24.md) (ARCHIVED 2026-07-27
— re-verified 2026-07-28 directly against the filesystem after a false "not yet archived" correction landed here
transiently: `plans/active/l0_doc_index_generator_2026_06_24.md` does not exist,
`plans/archive/2026_07/l0_doc_index_generator_2026_06_24.md` does; its 2 remaining items migrated to
`infra_satellite_ao_dispatch_batch1_2026_07_26.md` and are tracked there; L0 doc-index generator + FF-cron auto-regen) ·
`task_template.md` (the plan-authoring template/rules doc itself) ·
[codex_vs_repo_docs_ssot_audit_2026_06_01.md](/plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md) (generic "audit
all active repo docs vs codex SSOT" hygiene) ·
[issues/human_led_audit_pool_2026_05_21.md](/plans/archive/issues/human_led_audit_pool_2026_05_21.md) (archived
2026-07-27, superseded by `plans/audit/README.md`'s audit-instructions/results lifecycle + `/ag-closeout-audit` —
operator's original catalogue/process doc for background-agent-driven issue remediation at scale) ·
[issues/issue_docs_remediation_sweep_2026_06_02.md](/plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md)
(code-fixable-items sweep across the issue-doc backlog) ·
[/plans/archive/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md](/plans/archive/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md)
(plan-hygiene tooling migration: prek + fold-to-QG + agentic contradiction resolution) ·
[issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md](/plans/archive/issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md)
(**ARCHIVED 2026-07-27/28** — the "NOT archived" note above was accurate when written but is now stale: the operator
resolved the P3 decision the same session, `june_2026_vintage_audit_findings_2026_07_27.md` §5#26, KEEP+auto-generate
INDEX.md; `scripts/plans/regenerate_active_plan_index.py` built + wired into `run_hygiene_sweep.sh` + regenerated live
263 plans/10 domains; both findings resolved, doc archived) ·
[issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md](/plans/active/issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md)
(generic UI e2e test-helper `?persona=` bug, unrelated to any AG/AO/CI concern) ·
[issues/smoke_matrix_stale_ssot_citations_remaining_7_domains_2026_08_04.md](/plans/archive/issues/smoke_matrix_stale_ssot_citations_remaining_7_domains_2026_08_04.md)
(stale SSOT citations in 7 domain smoke_matrix.py files — doc-hygiene; added 2026-08-06 closeout-linkage fix) ·
[issues/infra_satellite_batch10_fabricated_commit_sha_evidence_2026_08_09.md](/plans/archive/2026_08/issues/infra_satellite_batch10_fabricated_commit_sha_evidence_2026_08_09.md)
(a `- [x]` citing a commit SHA that resolves nowhere — local, fetch, or GitHub API; evidence-integrity, so it belongs
with the plan-hygiene tooling that is supposed to catch it. Added 2026-08-12 closeout-linkage fix: the doc had sat
UNTRACKED for 3 days because this mention did not exist).

**Close-out criterion**: each tooling doc's own open todos closed; the zero-checkbox sweep's findings triaged; the
reference-path convention rollout complete corpus-wide.

## Track 4 — Generic product/UI bugs (no data-pipeline or single-AG content) · P2

> **✅ SUPERSEDED 2026-07-30 — moved to the new `ui` tranche.** Both this Track's sources were retagged
> `asset_group: [ui]` (was `[infrastructure]`) when the UI tranche launched — deployment-ui/deployment-api now has its
> own dedicated tranche instead of falling into this infra catch-all. See
> [ui_consolidated_closeout_2026_07_30.md](/plans/active/ui_consolidated_closeout_2026_07_30.md) Track 4 (nav/smoke/
> mock-parity hygiene) and Track 3 (observability surfaces), which now own this content. Left cited below for history;
> this Track's close-out criterion no longer belongs to the infra tranche's own completeness measurement.

**Source** (historical — now `ui`-tranche primary):
[issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md](/plans/archive/2026_08/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md)
(8 pre-existing deployment-ui smoke/playwright failures — Daily Costs page, mobile nav; generic product/UI bugs, not
data-pipeline or CI mechanics; RESOLVED + ARCHIVED 2026-08-10) ·
[artifact_pipeline_observability_2026_07_17.md](/plans/active/artifact_pipeline_observability_2026_07_17.md)
(build→artifact→deploy lineage UI — Cloud Build images, VM tarballs, drift-vs-running; deployment-observability domain,
not data-pipeline).

**Close-out criterion**: **N/A here — see `ui_consolidated_closeout_2026_07_30.md` Tracks 3/4 instead.**

## Codex SSOTs (read before touching a track)

`/codex/06-coding-standards/` (README + quality-gates.md), `/codex/11-project-management/`.

## Todos

> **Dispatch-vs-digest model: A (real todos on the hub itself), not B (a separate `..._aggregated_sources_*` sibling).**
> Verification-only — measures whether the tranche is actually done, not new work to dispatch (`assigned_vm: NA`, not
> itself AO-eligible). Added per `issues/autonomous_session_operator_decisions_2026_07_25.md` entry #38, so the next
> infra audit measures a real covering set instead of re-deriving the same orphan verdict from a zero-todo hub. Model A
> was chosen over Model B (the `<ag>_consolidated_closeout_aggregated_sources_*` sibling the 5 AGs use) because this
> tranche's own Track close-out criteria (below) ARE genuinely hub-owned work (cross-Track verification, not a single
> source doc's job) — a separate aggregated-sources sibling would just duplicate the Track membership already listed
> above without adding a distinct role, whereas the 5 AGs' sibling docs exist because their hubs needed a place to list
> sources SEPARATELY from dispatchable hub-owned work. Re-confirmed still the right model as of 2026-08-09
> (`infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` todo 3): re-measured, this hub's 3 open Track todos are
> what keeps `/ag-closeout-audit infra`'s covering-set discovery non-empty; converting to Model B would remove the only
> hub-owned dispatchable work without adding new coverage.

- [ ] [REVIEW] P2. Track 1 close-out: all CVE remediations landed (aiohttp/vcrpy, setuptools PYSEC-2026-3447,
      execution-service aioresponses migration); codex-violation ratchet green; `scripts/` governance sweep complete; uv
      pin re-synced fleet-wide; PM typecheck debt cleared; UTL/UAC dedup shipped; Dockerfile pattern normalized.
- [ ] [REVIEW] P2. Track 2 close-out: terraform drift reconciled + applied; VM startup scripts auto-roll to GCS;
      `managed-by` label convention adopted; billing-waste pre-flight gate designed + shipped. (The "org migration
      verified fleet-wide / no stale `IggyIkenna` refs" clause was **DROPPED 2026-07-28** — operator ruled **STAY on
      `IggyIkenna` Pro**, so those refs are the permanent correct state, not drift;
      `june_2026_vintage_audit_findings_2026_07_27.md` §5-RESOLVED #36, applied in `unified-trading-pm@cd5c0bde1`. That
      commit dropped the clause from this Track's body criterion above but missed this todo's restatement of it — fixed
      here by the 2026-07-30 na-eligibility-audit.)
- [ ] [REVIEW] P2. Track 3 close-out: each tooling doc's own open todos closed; the zero-checkbox sweep's findings
      triaged; the reference-path convention rollout complete corpus-wide.
- [x] ➡️ [REVIEW] P2. **SUPERSEDED 2026-07-30** (was: "Track 4 close-out: the 8 deployment-ui smoke failures fixed +
      pw:L2 regression specs added; the artifact-lineage UI's remaining phases ship.") — both Track 4 sources retagged
      `asset_group: [ui]`, moved to `ui_consolidated_closeout_2026_07_30.md` Tracks 3/4. Not this tranche's completeness
      measurement anymore; not double-counted as done here.

## Progress Log

- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — unchanged since the 2026-08-06 verdict. The 3
  remaining `[REVIEW]` Track close-out todos are unchanged all-of-N gates created by an explicit resolved operator
  decision (`issues/autonomous_session_operator_decisions_2026_07_25.md` entry #38); read end-to-end,
  `grep -cE '^- \[ \]'` = 3, matching. Only ag-closeout-audit linkage-discoverability entries and a context-scout
  refresh touched the doc since the last marker — no change to the 3 gates' own content or bounded-outcome status.
- **ag-closeout-audit 2026-08-06 (infra tranche)**: linkage fix — added
  `cloud_run_traffic_pin_silent_freeze_alert_wiring_2026_08_05.md` (Track 2) +
  `smoke_matrix_stale_ssot_citations_remaining_7_domains_2026_08_04.md` (Track 3) to Sources;
  `check_ag_closeout_linkage.py` infra orphans 2→0 (the corpus-wide 87-vs-69 regression is tracked in
  `issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md`, per-tranche triage). Parked findings for this
  run: `issues/ag_closeout_audit_infra_parked_2026_08_06.md`.

- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — unchanged; 3 [REVIEW] roll-up todos exist by
  resolved operator decision #38 (issues/autonomous_session_operator_decisions_2026_07_25.md,
  unified-trading-pm@2c61a8dc4); confirmed on citation, not re-derived.

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
  `/plans/archive/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md`. Exit gate re-run after rebasing onto
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
  [issues/infra_plan_reconcile_parked_decisions_2026_07_26.md](/plans/archive/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md)):
  **29 orphaned** (28 `orphaned_never_touched` + 1 `orphaned_partial_coverage`), 5 not orphaned (the generated inventory
  dashboard, `task_template.md`, the self-referential rollout meta-plan, and the two operator-decision registers). Phase
  3 drafted
  [infra_satellite_ao_dispatch_batch1_2026_07_26.md](/plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md) +
  [infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md](/plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md)
  — **25 todos from 17 source docs, both `status: draft` (NOT ingested; the flip to `active` is the operator's call)**.
  The HARD conflict check ran against all 93 existing batch/finalize/closeout plans plus pairwise across the 25 drafted
  todos: 10 further AO-eligible items were deferred conflict-gated (notably `PYTEST_UNIT_DIR`, where a cefi doc
  prescribes a different approach gated behind 22 test fixes; `DataStatusTab.tsx`, claimed by a cross-cutting batch; and
  `base-service.sh`/`base-library.sh`, a multi-tranche hotspot with no ownership rule), and **3 were resolved by logic
  rather than re-drafted** — the CME BTC/ETH OPT-atom question is answered by an explicit operator ruling recorded in
  `tradfi_consolidated_closeout_2026_07_18.md:196-197`, the `vm_log_archival_scheduler.tf` apply already landed
  (`deployment-service@3cd0b1d`, verified 2026-07-07), and 4 DeFi items are already claimed by defi batches 1/3/4. Also
  measured and reported (not fixed here — reconcile's territory):
  [utl_uac_reuse_consolidation_remediation_2026_06_10.md](/plans/archive/2026_07/utl_uac_reuse_consolidation_remediation_2026_06_10.md)'s
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
  `docker_artifact_registry_cleanup_policy_2026_07_24.md`,
  `/plans/archive/issues/stranded_prek_stash_patch_2026_07_23.md` (archived 2026-07-30),
  `issues/deployment_service_ungated_revision_delete_no_rollback_target_2026_07_26.md` (archived — resolved,
  deployment-service@5690ad3, now at
  `/plans/archive/issues/deployment_service_ungated_revision_delete_no_rollback_target_2026_07_26.md`),
  `issues/unified_trading_system_ui_codex_violations_far_exceed_estimate_2026_07_21.md` (archived — resolved,
  unified-trading-system-ui@030d2575, now at
  `/plans/archive/issues/unified_trading_system_ui_codex_violations_far_exceed_estimate_2026_07_21.md`),
  `archive/issues/quickmerge_agent_files_pure_deletion_gap_2026_07_26.md`,
  `issues/ui_hardcoded_colour_and_localhost_debt_2026_07_21.md` (archived — resolved,
  unified-trading-system-ui@145bf5dd, now at
  `/plans/archive/issues/ui_hardcoded_colour_and_localhost_debt_2026_07_21.md`),
  `issues/instruments_service_run_tag_flag_not_applied_2026_07_08.md` (archived — resolved,
  instruments-service@f7e64c54, now at
  `/plans/archive/issues/instruments_service_run_tag_flag_not_applied_2026_07_08.md`),
  `issues/qg_workspace_root_template_drift_12_repos_2026_07_24.md`,
  `issues/ui_repos_eslint_base_config_never_wired_no_explicit_any_unenforced_2026_07_21.md` (archived — resolved,
  unified-trading-system-ui@ff811a8c, now at
  `/plans/archive/issues/ui_repos_eslint_base_config_never_wired_no_explicit_any_unenforced_2026_07_21.md`),
  `/plans/archive/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md`,
  `issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md` (archived — resolved 2026-07-31, root cause was
  playwright.config.ts host-contention false positives, now at
  `/plans/archive/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md`). None were tracked in any Track above; all are
  now `assigned_vm: planning` and live in the AO backlog.
- **na-eligibility-audit 2026-07-30** (infra tranche, incremental run): **KEEP-NA, valid — stale-item clause fixed on
  todo 2.** This hub was the one infra-tranche doc carrying no verdict marker from the earlier same-day pass
  (`unified-trading-pm@4c6587543`/`ddf6a8adf`/`f3b018596`), so it was in scope here. All 4 open `[REVIEW]` todos read
  end-to-end (`grep -cE '^- \[ \]'` = 4, matches this verdict's item count). **KEEP-NA is confirmed on citation, not
  re-derived**: the todos exist by an explicit resolved operator decision —
  `issues/autonomous_session_operator_decisions_2026_07_25.md` entry #38, option A, `unified-trading-pm@2c61a8dc4` —
  which added them as _verification_ roll-ups so a future tranche audit measures a real covering set instead of a
  zero-todo digest. Independently re-checked against the bounded-outcome bar rather than accepting the doc's own "not
  AO-eligible" gloss: each todo is an all-of-N close-out gate whose underlying work lives in its source docs (many
  already `assigned_vm: planning`, plus `infra_satellite_ao_dispatch_batch1_2026_07_26.md`), so it can only flip once
  those finish. Dispatching it eagerly would burn a worker re-deriving "not yet"; that gating shape belongs in a
  `depends_on` + `gate_on_depends: true` companion, not an `NA → planning` flip. **Fix applied**: todo 2 still demanded
  "org migration verified fleet-wide (no stale `IggyIkenna` refs)" — a criterion the operator CANCELLED on 2026-07-28
  (§5-RESOLVED #36; `IggyIkenna` refs are now correct-by-ruling, not drift). `unified-trading-pm@cd5c0bde1` dropped that
  clause from the Track 2 body criterion but missed the todo restating it, so the todo would have sent a reviewer
  hunting for "stale" refs that are the intended permanent state. Clause removed with the ruling cited inline. No
  conflict-check needed (no RECLASSIFY).
- **2026-07-31** — `/ag-closeout-audit infra` re-run (autonomous mode, scheduled daily run, slot 13). Covering set is
  now 9 docs (batch1/finalize + batch2/finalize + batch3(draft)/finalize(draft) + this hub +
  `infra_capture_and_devops_ leftovers`/finalize — batch2 and batch3 existed since 2026-07-27/30 but were never
  previously logged in this hub's own Progress Log, a discoverability gap worth noting for the next reader).
  `generate_ag_closeout_audit_candidates.py --tranche infra` now reports 32 members (corpus has grown/shrunk since
  2026-07-26's 34). Phase 1 ran a 10-agent Workflow over the 9 currently-never-cited docs plus a targeted re-check of
  `codex_violations_ratchet_to_five_2026_06_ 10.md` (whose citation in batch1 turned out to only partially cover its
  remaining work on full re-read): 8 of the 9 never-cited docs are legitimately self-dispatched
  (`assigned_vm: planning`, not orphans by the skill's own tooling definition), 1
  (`stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md`) is a genuine orphan but
  guardrail-blocked operator-only work (non-batchable), and `codex_violations_ratchet_to_five` has 5 of 7 open items
  genuinely uncovered — 3 remain correctly gated by batch1's own pre-existing Deferred classification (unchanged), 1
  (`delta_proxy_repricer.py`) turned out to be ALREADY SHIPPED (`execution-service@980a6ad0`) with a stale checkbox, and
  1 (`_solana_utils.py` line-cap split) was genuinely new, conflict-clear, and bounded. Phase 3 drafted a single-todo
  `infra_satellite_ao_dispatch_batch4_2026_07_31.md` (`status: draft`, no finalize twin per the single-todo carve-out)
  for that one item. The stale-checkbox finding plus a filesystem-vs-doc discrepancy on the stash-clone deletion (target
  directory already absent from disk in this session's environment, but the doc's todo still shows it open) are parked
  in `issues/ag_closeout_audit_infra_parked_2026_07_31.md` per the "parked findings always get a durable issue doc" hard
  rule — both are `/plan-reconcile`'s job to reconcile, not this skill's (false-unchecked-flip is out of scope here). G1
  (`base-service.sh`/`base-library.sh` serialization) shows partial progress
  (`ci_satellite_ao_dispatch_batch2_2026_ 07_29.md`'s both claims now `[x]`) but remains gated —
  `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s own claim on the same file is still open. G3
  (`DataStatusTab.tsx`) unchanged. No new `[REVIEW]` Track criteria needed above — the 3 existing ones still accurately
  measure this tranche's completeness.
- **2026-07-31 ~21:26 UTC** — `/ag-closeout-audit infra` re-dispatched same-day (autonomous mode, scheduled, slot 13,
  ~7h after the run above). Re-verification, not a from-scratch re-audit: candidate set re-derived twice
  (`generate_ag_closeout_audit_candidates.py --tranche infra`, 32→36→37 members across a mid-run `git pull --ff-only`);
  every net-new-since-14:06 doc (3) and the one persistently-never-cited candidate direct-read rather than re-running
  the full Phase 1 Workflow (justified in the parked-findings doc's own Progress Log — mirrors the sibling `prediction`
  tranche's same-day precedent, `unified-trading-pm@e89cdd5eb`). Result: **0 new genuine infra orphans, no batch5
  drafted.** The 3 new docs are all already self-dispatched (`assigned_vm: planning`) and well-fitted to their Tracks.
  The one never-cited candidate (`ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`) is a likely
  `asset_group` mistag — real owning tranche is `ao` (its content is agent-orchestrator dispatch/worker- lifecycle,
  `parent_epic: orchestrator_master`), not `infra` — reported as finding 3 in the parked-findings doc rather than
  retagged directly (owning-tranche-writes-only rule, concurrent sharded workers). Findings 1-2 from the 14:06 run
  re-checked live: both still open/unreconciled, no drift. Batch4 re-checked: still `status: draft`, untouched. Deferred
  gates G1/G3 re-checked against live checkbox state: both unchanged, nothing newly cleared.
- **2026-08-01** — `/ag-closeout-audit infra` re-run (autonomous mode, scheduled daily run, slot 5). Re-derived the
  candidate set (`generate_ag_closeout_audit_candidates.py --tranche infra`: 39 members, 10 covering docs, 1 never-cited
  — `issues/deployment_scripts_bucket_soft_delete_retention_drift_2026_07_31.md`, a genuine but operator-gated
  terraform-drift judgment call, correctly non-batchable). Per the iterative-drain methodology, re-checked
  batch1/batch3's tracked Deferred gates (G1-G6) live before any fresh Phase-1 triage. **G3 cleared**: the
  `DataStatusTab.tsx` `DATA_PIPELINE_SERVICES` sequencing gate (held since 2026-07-26, entry #35) was waiting on
  `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` item (B) — confirmed shipped today
  (`deployment-ui@727298b`, 2026-08-01 01:42 UTC) and the file confirmed genuinely quiet corpus-wide (no other active
  plan holds an unshipped claim on it). Drafted
  [infra_satellite_ao_dispatch_batch5_2026_08_01.md](/plans/archive/2026_08/infra_satellite_ao_dispatch_batch5_2026_08_01.md)
  (single todo, no finalize twin per the single-todo carve-out, `status: draft` — operator flip required). G1/G2
  (`base-service.sh`/`base-library.sh` serialization) remain gated, unchanged. G4 (`PYTEST_UNIT_DIR`) reconfirmed
  already resolved elsewhere (shipped 2026-07-31). G5's MTDS >900-line-tail sub-item reconfirmed already resolved
  elsewhere too (verified 2026-07-27, stale tracking note only, not new material). G6 stays owned by tradfi, unchanged.
  The 3 carried-forward findings from the 2026-07-31 parked-findings doc were re-verified live: all still open, no
  drift. 3 NEW findings surfaced this run (a stale `draft` banner in batch3's body text contradicting its own
  already-`active` frontmatter; a self-referential citation blind spot in `generate_ag_closeout_audit_candidates.py`'s
  never-cited pre-filter, discovered because it silently dropped the still-live
  `ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md` mistag from this run's never-cited list purely
  because a prior Progress Log entry named the file in prose; and a second likely `asset_group: [meta]` mistag whose
  real owner is probably `ao`, not `infra`) — all recorded in
  [issues/ag_closeout_audit_infra_parked_2026_08_01.md](/plans/archive/2026_08/issues/ag_closeout_audit_infra_parked_2026_08_01.md)
  per the parked-findings hard rule. **Linkage discoverability fix**: `check_ag_closeout_linkage.py` showed the
  shrinking-ratchet count risen to 78 (baseline 69) — corpus-wide, mostly other tranches' concurrent activity (not this
  run's doing; this run's own 2 new docs are both correctly linked, verified). Of the 78, exactly 7 carry
  `asset_group: [infrastructure]` and are this tranche's own responsibility to link. Adding them here per the
  established discoverability-mention remedy (SKILL.md's own prescribed fix: name the doc in the hub so the graph/
  mention check finds it) — none of these were tracked in any Track above:
  `basedpyright_extrapaths_pyproject_migration_findings_2026_08_01.md` (self-dispatched),
  `ci_registry_drift_uac_utl_stale_tag_version_conflict_2026_07_26.md` (self-dispatched),
  `deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md` (self-dispatched),
  `quickmerge_stage5_push_loses_fast_forward_race_under_high_churn_2026_07_27.md` (self-dispatched),
  `issues/legacy_bucket_template_literals_2026_07_16.md` (`assigned_vm: NA` — this is G5 item 5 from batch1's own
  Deferred tracking, event-timing-gated, non-batchable, unchanged),
  `issues/shared_host_home_filesystem_full_2026_07_26.md` (`assigned_vm: NA` — not previously read by this skill;
  flagging for a future Phase-1 pass to classify, not classified this run), and
  `issues/vm_launcher_class_b_no_stall_kill_gap_2026_07_27.md` (`assigned_vm: NA` — this is G5 item from batch3's own
  non-batchable table, blast-radius-judgment-gated, unchanged). Re-ran the linkage check after adding these mentions:
  71/78 (7 infra orphans resolved; the residual 71 are other tranches', outside this run's remit — flagged in this run's
  `evidence` for visibility, not fixed here).
- **context-scout 2026-08-03**: refreshed context_scope (7 -> 5 entries) — dropped the two specific
  `infra_satellite_ao_dispatch_batchN` pointers (batch1/batch5) since satellite batches rotate frequently (batch6/
  batch7-declined already superseded them by this date) and `README.md` (redundant with `quality-gates.md` for Track 1's
  coding-standards content); added the current `ag_closeout_audit_infra_parked_2026_08_03.md` parked-findings doc, which
  reflects this tranche's live unresolved state (the `asset_group` mistag deadlock) better than a stale batch number
  would.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid — unchanged from the 2026-07-30
  verdict.** In scope this run because the doc was edited since that marker (2026-08-01 `/ag-closeout-audit`
  Progress-Log appends, the Track-4 supersession, and a context-scout backfill). Read end-to-end; `grep -cE '^- \[ \]'`
  = **3** (was 4 at the last marker; Track 4's todo has since been correctly closed as SUPERSEDED into the `ui`
  tranche), matching this verdict's item count. The 3 remaining `[REVIEW]` todos are unchanged all-of-N Track close-out
  gates created by an explicit resolved operator decision (`issues/autonomous_session_operator_decisions_2026_07_25.md`
  entry #38, `unified-trading-pm@2c61a8dc4`); the reasoning recorded on 2026-07-30 (a gating shape belongs in a
  `depends_on` + `gate_on_depends` companion, not an `NA → planning` flip) still holds and is not re-derived here.

  **BLOCKED-OPERATOR-DECISION (tranche-level, new this run) — the `asset_group` mistag retag is structurally deadlocked,
  and the deadlock is now measured, not suspected.** Three infra-tranche docs whose real owner is `ao` by `parent_epic`
  have had a retag recommended-but-never-applied across multiple consecutive audits, each run correctly declining under
  `/ag-closeout-audit`'s owning-tranche-writes-only rule:

  | doc                                                                                    | `asset_group`      | `parent_epic`                      | retag first recommended |
  | -------------------------------------------------------------------------------------- | ------------------ | ---------------------------------- | ----------------------- |
  | `issues/ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`                | `[infrastructure]` | `orchestrator_master`              | 2026-07-31 (finding 3)  |
  | `issues/qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge_2026_07_31.md`        | `[meta]`           | `agent_operating_framework_master` | 2026-08-01 (finding 6)  |
  | `issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md` | `[meta]`           | `agent_operating_framework_master` | not previously flagged  |

  **Root cause, verified by direct code read of `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` this run,
  not inferred**: tranche membership is derived from `asset_group`, never `parent_epic` — `ao` membership requires a
  literal `asset_group: ao` (line ~201), a bare `[meta]` doc **default-folds into `infra`** (line ~202), and
  `owning_tranche()` deliberately refuses to assign ownership to a tranche the doc is not a member of, falling back to
  `tranches[0]`. So the corrective retag is reserved for a tranche that provably cannot see the docs needing it.
  **Measured**: `generate_na_doc_tranche_inventory.py --tranche ao --json` returns 61 docs and **none of the three
  above** — the same result `/ag-closeout-audit ao`'s own `asset_group`-driven pre-filter will produce. Every future
  `ao` run will keep not-seeing them and every future `infra` run will keep declining to write; the recommendation
  cannot converge on its own.

  - **A [WORKER REC]: authorise the tranche that CAN see a mistagged doc to apply the `asset_group` retag**, when the
    correct owner is evidenced by `parent_epic` + content and two independent audits already agree — i.e. treat a
    provably-unreachable owner as an exception to owning-tranche-writes-only. Cheapest fix, unblocks all three today,
    and the write is one frontmatter line with no dispatch effect.
  - **B: run the retags from a corpus-wide (non-sharded) pass** — a `meta`/mistag fold-in sweep like the 2026-07-31 one
    (`unified-trading-pm@0409fa053` region) that already retagged four docs into `infra`. Preserves the sharding rule
    intact; costs a separate scheduled pass, and these three were missed by exactly that sweep once already.
  - **C: make `owning_tranche()` (and `/ag-closeout-audit`'s pre-filter) fall back to the `parent_epic`-mapped tranche
    even when the doc is not an `asset_group` member of it**, so the real owner sees the doc and can retag it. Fixes the
    class rather than the three instances; changes shared corpus tooling used by all 9 tranches, so it needs its own
    conflict-check and is not a same-run action.
  - Other: operator free-text.

  Not actioned this run either way — the retag is an `asset_group` write, outside this skill's own Phase-3 apply set
  (which covers `assigned_vm`, checkbox citations, archival and verdict markers), and picking between A/B/C is a process
  ruling. Recorded here rather than in a new parked doc so it does not add to the very NA corpus this skill's ratchet is
  meant to shrink.

- **2026-08-03** — `/ag-closeout-audit infra` run (autonomous mode, scheduled daily run, slot 12). Re-derived the
  candidate set (13 covering docs, 45 members — up from 43 on 2026-08-02, 2 never-cited). Re-checked all 9
  carried-forward 2026-07-31/08-01/08-02 findings live before fresh triage: 5 resolved since yesterday
  (`delta_proxy_repricer.py` checkbox shipped; `docs_reconcile_autonomous_sweep_2026_07_30.md`'s P0-A 2026-08-15 cliff
  operator-ruled; `qg_owner_gate_full_workspace_rglob_walk_hangs_quickmerge_2026_07_31.md` retagged `[ao]`;
  `git_health_not_clean_since_pinned_constant_2026_07_27.md` retagged `[ao, meta]` by the cross-cutting tranche's own
  run, resolving both its dual-tag AND its underlying mistag in one move;
  `infra_satellite_ao_dispatch_batch6_2026_08_02.md`'s todo 1 found already-resolved-elsewhere and fixed in-line this
  run since the batch is still `status: draft`), 1 still open unchanged
  (`ao_self_pull_wedged_by_main_inbox_untracked_file_2026_07_30.md`'s mistag, still parked as
  `BLOCKED-OPERATOR-DECISION` above). Ran a fresh 45-agent Phase 1 Workflow over the full candidate set (0 errors).
  **Found a serious regression on finding 7's own fix**: `infra_satellite_ao_dispatch_batch3_2026_07_30.md`'s 2026-08-02
  operator-approved `assigned_vm: NA` → `planning` flip landed BLANK instead of `planning` (verified via direct raw-file
  read + `git log -p`, not the doc's own banner text, which falsely claims the flip succeeded and fooled today's own
  Phase-1 audit agent into reporting it as done) — the `[BACKEND] P3` todo is still not AO-dispatchable, one day after
  the "fix." Also found (real-host `find` sweep, confirming this is the genuine long-running shared host, not a
  sandbox): `issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md`'s previously-verified
  stash-backup bundle is now genuinely absent anywhere under `/home/ubuntu`, alongside the scratch directory itself —
  contradicts that todo's own done-when (the bundle was meant to survive as the sole remaining trace) and needs operator
  investigation (relocated durably vs. an unrecovered loss). Both, plus a methodology caveat (15 of today's 42
  orphaned-verdict docs are already self-dispatched and do not need batch7 treatment — corroborated unprompted by 7 of
  the 45 Phase-1 agents) and 2 unscoped batch7 candidates, are recorded in full in
  [issues/ag_closeout_audit_infra_parked_2026_08_03.md](/plans/archive/2026_08/issues/ag_closeout_audit_infra_parked_2026_08_03.md).
  Did not draft `infra_satellite_ao_dispatch_batch7` — of 42 orphaned docs, 15 are self-dispatched and the remaining 27
  are each operator/time/design/conflict-gated or this skill's own prior-run parked-findings docs; the 2 "maybe"
  candidates need dedicated scoping first, per the skill's own "report the residual, don't force a batch" allowance.
  **Linkage discoverability fix**: `check_ag_closeout_linkage.py` shows 64 orphans corpus-wide (baseline 69, still
  improving) — exactly 1 carried `asset_group: [infrastructure]` at the time of the first check:
  `issues/prod_vm_launch_missing_service_account_user_grant_2026_08_02.md` (conflict-gated against the active
  `bucket_iam_p2_tier_sa_scope_gap_and_default_compute_sa_overprivilege_2026_07_30.md` P0 plan per its own 2026-08-02
  na-eligibility-audit entry — not batchable this round, named here per the established discoverability remedy). Re-ran
  the linkage check after adding this mention: that one resolved (63/69), but
  `issues/honest_coverage_cron_run_job_sa_missing_actas_uts_prd_sa_2026_08_03.md` (also `asset_group: [infrastructure]`,
  this run's OTHER never-cited candidate) newly appeared as an orphan on the re-check — most likely a concurrent edit
  elsewhere in this actively multi-agent-edited corpus changed its indirect path between the two checks, not this run's
  own doing. Naming it here too (same conflict-gated status as its sibling — see this run's parked-findings doc finding
  context): it is a real, live data-pipeline-correctness gap (the honest-coverage data-status panel has been silently
  stale since ~2026-08-01) but conflict-gated against the same active P0 plan, not batchable this round either.
- **2026-08-04** — `/ag-closeout-audit infra` run (autonomous mode, scheduled daily run, slot 10). Re-derived the
  candidate set (13 covering docs, unchanged; 50 members, up from 45 on 2026-08-03; 3 never-cited, all created
  2026-08-03). Re-checked all 3 carried-forward findings from `ag_closeout_audit_infra_parked_2026_08_03.md` live: all 3
  (the `ao_self_pull` mistag, batch3's blank `assigned_vm`, the missing stash-backup bundle) remain open, unchanged.
  Classified the 3 net-new never-cited docs: `ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md` is genuinely
  non-batchable (large, actively-executing human VM-migration plan);
  `na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md`'s 2 todos and
  `deployment_service_live_event_log_disconnected_tofu_root_2026_08_03.md`'s investigation-only half (its structural
  decision half stays operator-gated) were conflict-clear and bounded. Drafted
  [infra_satellite_ao_dispatch_batch7_2026_08_04.md](/plans/archive/2026_08/infra_satellite_ao_dispatch_batch7_2026_08_04.md) +
  its finalize twin (3 todos, both `status: draft`). **New finding**: 4 drafted batches (4/5/6/7) now sit unreviewed,
  oldest 4 days — see
  [issues/ag_closeout_audit_infra_parked_2026_08_04.md](/plans/archive/2026_08/issues/ag_closeout_audit_infra_parked_2026_08_04.md)
  finding 14. **Linkage discoverability fix**: `check_ag_closeout_linkage.py` showed 66 orphans corpus-wide (baseline
  69, still improving) — exactly 1 carried `asset_group: [infrastructure]`:
  `issues/fix_frontmatter_strips_required_author_field_from_issue_docs_2026_08_04.md` (already `status: resolved`,
  shipped `unified-trading-pm@ebc2075b9` same day — correctly excluded from this run's Phase-1 candidate set by the
  generator's own `EXCLUDED_STATUS` filter, but still linkage-unlinked). Named here per the established discoverability
  remedy.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — swapped the parked-findings pointer from
  `ag_closeout_audit_infra_parked_2026_08_04.md` to the current `ag_closeout_audit_infra_parked_2026_08_07.md` (the
  08-04 doc's findings are now resolved/superseded by later runs; 08-07 reflects this tranche's live unresolved state).
- **2026-08-09 (review-craft-per-task, `infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` todo 3)** — Made the
  dispatch-vs-digest model explicit above (was implicit in the operator-decision citation only): **Model A, re-confirmed
  correct**. No structural change needed — this hub has carried real Track close-out todos since 2026-07-26 (same day
  batch1 was drafted), so batch1-finalize's own todo 3(b) premise ("carries ZERO todos, orphaned by construction") was
  already stale by the time it was read, having been drafted from the same-day pre-fix state. Full re-measurement
  written up in the finalize plan itself (not duplicated here): orphan count dropped from the 2026-07-26 baseline
  (29/34) to 0 genuinely-untriaged (11 never-cited-by-covering-doc candidates remain, but 7 are cross-tranche
  ci/defi-owned mistags and 4 are already-carried, reason-stated parked findings, per today's own
  `ag_closeout_audit_infra_parked_2026_08_09.md`). `check_ag_closeout_linkage.py` re-run fresh: 0 orphans carry
  `asset_group=[infrastructure]` (28 orphans corpus-wide, all other tranches); both
  `session_bound_vm_monitoring_ reliability_gap_2026_07_26.md` and `infra_plan_reconcile_parked_decisions_2026_07_26.md`
  confirmed already registered above (2026-07-27 entry) with proper `[text](path)` links, not bare filenames — no edit
  needed there.
