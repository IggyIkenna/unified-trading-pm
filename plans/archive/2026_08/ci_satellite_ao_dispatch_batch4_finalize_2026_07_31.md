---
doc_type: plan
title: CI satellite AO batch 4 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch4_2026_07_31.md — machine-held via depends_on + gate_on_depends: true
  until all 9 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the Deferred items (D4-1 through D4-20) for whether their blocker has cleared, and archives batch 4 via the
  standard 6-step ritual.
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-4, satellite-docs, archival]
related:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-31"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ci_satellite_ao_dispatch_batch4_2026_07_31]
gate_on_depends: true
source: >-
  `/ag-closeout-audit ci` run 2026-07-31, per `plans/active/task_template.md` §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan, mirroring the batch1/batch2 precedent. Authored `status:
  active` (not `draft`) per the skill's 2026-07-30 finding: `gate_on_depends: true` already machine-holds every task
  here until the batch's own todos are `done` (via `_wire_gate_on_depends_prereqs`, which covers a still-draft batch too
  via a derived `gate-upstream-open:<stem>` condition read off the batch file's own checkboxes) — stacking `status:
  draft` on top is a redundant second gate that requires a separate manual flip nobody reliably remembers.
assigned_role: cicd
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/08-workflows/deployment-flow.md,
    /codex/04-architecture/ci-alerting.md,
    /plans/active/task_template.md,
  ]
---

# CI satellite AO batch 4 — finalize

> **🟢 ARCHIVED 2026-08-09 — COMPLETE.** All 4 todos shipped. Sibling
> `/plans/archive/2026_08/ci_satellite_ao_dispatch_batch4_2026_07_31.md` (the 9-item fourth ci-tranche AO-dispatch
> batch) completed and archived alongside in the same commit set. All 20 Deferred items (D4-1 through D4-20) were
> re-checked (todos 2-3): D4-2/D4-3/D4-4/D4-11/D4-15/D4-16/D4-19/D4-20 fully discharged or superseded-by-completion;
> D4-5/D4-6/D4-10 operator-ruled and reclassified to independently dispatchable todos in their own source docs; the
> remaining 9 (D4-1/D4-7/D4-8/D4-9/D4-12/D4-13/D4-14/D4-17/D4-18) remain genuinely open with a live tracked `- [ ]`
> checkbox in their own active source doc — none evaporates with this archival. Successor: none drafted here; D4-1 is
> ready for a future `ci_satellite_ao_dispatch_batchN` extraction.

> **🔒 GATED, not draft.** `depends_on: [ci_satellite_ao_dispatch_batch4_2026_07_31]` + `gate_on_depends: true` holds
> every todo below until all 9 of batch4's own todos are `done` — this applies whether batch4 is still `status: draft`
> (via the derived `gate-upstream-open:` condition) or has been flipped `active` by the operator (via
> `prereqs.completed_tasks`). No separate flip is needed for THIS doc; it is correctly `status: active` from authoring.
> `sequential: true` because todo 1 must land before todo 2's reconciliation cites it, todo 3 needs both, and todo 4
> (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-08-09 (slot 2, review→cicd craft).** Reconciled all 9 batch-4 todos' 8 distinct source
      docs (todo 1 cites two; todo 9's 4 items share one doc). All 9 commits verified live ancestors of
      `origin/live-defi-rollout` via `git merge-base --is-ancestor` before citing (`b02ba28c7`, `dc1dc7df`, `445f02081`,
      `eff7413da`, `917fc626a`, `f83716c0b`, `4bf65b67c`, `ccb1d7b10`, `b3abf1bd5`). Per-doc outcome:
  - `stale_staging_versions_manifest_2026_07_23.md` — already archived + `status: resolved`, zero-open, correctly cites
    `b3abf1bd5`. No edit needed.
  - `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md` — flipped its sole remaining `[ ]` (hook
    deletion) citing `b02ba28c7`; live-verified the hook file no longer exists and all 4 referrers are repointed;
    reached zero open work → flipped to `status: resolved`, archive banner added, `git mv`d to `plans/archive/issues/`,
    2 path-formatted corpus referrers repointed (`silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md`).
  - `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` (todo 2's true source — no explicit `Source:`
    line existed in the batch4 doc for todo 2; located via corpus grep on the alias-precedence fix) — already correctly
    reconciled (steps 2+4 done citing `dc1dc7df`/fleet grep, step 3/D4-1 genuinely still open). No edit needed.
  - `deployment_flow_doc_stale_pre_ldr_direct_mvp_2026_07_30.md`,
    `uv_bootstrap_fallback_test_structural_anchor_stale_2026_07_30.md` — both already archived + `status: resolved`,
    zero-open, correctly cite `445f02081`/`eff7413da`. No edit needed.
  - `fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md` — already fully reconciled by a sibling
    `ci_satellite_ao_dispatch_batch6_finalize` todo 1 worker same-day (checkbox flipped citing `917fc626a`; correctly
    stays `archive_exempt: true`, not `resolved` — genuine prose-form open work survives, the documented false-zero trap
    this todo itself warns about). No edit needed.
  - `pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28.md` — already fully reconciled (`f83716c0b`
    confirmed as the actual shipping commit for the Tier-B sign-off log); `status: superseded` (terminal, unrelated
    billing-premise reason) with 2 remaining checkboxes explicitly marked stale BLOCKED-SUPERSEDED pointers per the
    doc's own guidance. No edit needed.
  - `ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md` — already `status: resolved`/archived; added
    the closing citation its own 2026-07-31 na-eligibility-audit verdict asked for ("cite/close lines 128 and 132-144...
    once batch4 ships") — both migrated items shipped via batch1 (not batch4 itself), `ccb1d7b10` ([SCRIPT] P2
    monitor) + `4bf65b67c` ([CI] P1 auto-merge-arm fix), both verified ancestors; batch4 todos 7/8 correctly found these
    `DONE-ELSEWHERE` rather than re-shipping.
  - `github_actions_operator_gated_followups_2026_07_17.md` — todo 9's own worker already flipped all 4 checkboxes
    inline with a dated 2026-08-09 Progress Log entry (live billing/measurement data, no code commit — correct for a
    `[VERIFY]` todo). Doc has 5 unrelated open checkboxes, correctly stays `status: active`. No edit needed.
  - No FALSE-CHECKED-checkbox traps found among the 9 docs beyond the ones already correctly handled by prior
    reconciliation passes (fleet_wide_qg doc's `archive_exempt`, github_actions_operator_gated_followups' partial-open
    status).
- [x] ✅ [REVIEW] P1. **DONE 2026-08-09 (slot 33, review→cicd craft).** Re-checked all 4 conflict-gated Deferred items;
      no follow-up drafted here per scope.
  - **D4-1 (quickmerge.sh branch-check broadening, step 3 of
    `issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md`) — BOTH blockers cleared, ready for
    batch-5 extraction.** Batch-4 todo 1 (`quickmerge.sh` dormancy gate + hook deletion) landed
    `unified-trading-pm@b02ba28c7`, live-verified ancestor of `origin/live-defi-rollout` — `scripts/quickmerge.sh` is
    free again. Batch-4 todo 2 step 2 (the `UnifiedCloudServicesConfig` alias-precedence fix, the step-3 precondition)
    landed `unified-trading-library@dc1dc7df`, live-verified ancestor. Step 3 (broaden the branch check to recognise
    `live-defi-rollout`/`staging`) remains the sole open item in its source doc — genuinely a design/judgment call on
    the fleet-wide shipping gate, so still correctly `assigned_vm: NA` there; batch-5 (or later) should extract it as a
    bounded AO todo now that both preconditions are met. Not drafted here per this todo's own scope limit.
  - **D4-2 (test-impact design-scoping todo) and D4-3 (BigQuery `resource_samples` verification) — file freed AND both
    underlying items already fully DONE, no extraction needed at all.**
    `github_actions_operator_gated_followups_2026_07_17.md` was freed by batch-4 todo 9 landing (2026-08-09 billing
    sweep, confirmed in that doc's own Progress Log). But independently of batch-4, a sibling plan
    (`ci_satellite_ao_dispatch_batch5_2026_08_02.md` todo 2) already picked up and shipped both: BigQuery
    `resource_samples` utilization measured `avg_cpu_pct=50.6%` (within the 50-70% band, checkbox flipped ~line 685 of
    the source doc); the test-impact design-scoping item was found MOOT — already `[x]` (extracted 2026-08-03, shipped
    as `test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md`, no fresh design needed). Source doc's own
    2026-08-09 Progress Log entry ("`ci_satellite_ao_dispatch_batch5_2026_08_02.md` todo 2 ... both remaining items
    closed") confirms this. So D4-2/D4-3 are superseded-by-completion, not merely unblocked — batch 5 already did the
    work; nothing left to extract into a future batch.
  - **D4-4 (`sit_validated_tree_treadmill`'s stuck-gate monitor) — no longer open; already shipped.** Re-verification
    found batch1's own todo (`ci_satellite_ao_dispatch_batch1_2026_07_26.md`, the "SIT-BLOCKED for N consecutive
    promoter ticks" item) is now `[x]` ✅ done — `scripts/cicd/sit_gate_stuck_detector.py` +
    `.github/workflows/sit-gate-stuck-detector.yml` shipped `unified-trading-pm@409c35437`, live-verified ancestor of
    `origin/live-defi-rollout`. Source doc
    `plans/archive/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md` is `status: resolved`,
    archived, zero open checkboxes, `locked_by` empty. D4-4 is fully resolved — not "still open", not a fresh item to
    extract; batch4's original framing ("already claimed by batch1's still-open todo") is now stale since batch1's todo
    has since landed.
  - No new doc has claimed any of D4-1/D4-4's underlying work since batch4 was drafted; D4-2/D4-3 were claimed and
    completed by batch5, as detailed above.
- [x] ✅ [REVIEW] P2. **DONE 2026-08-09 (slot 7, review→cicd craft).** Re-verified all 16 items (D4-5 through D4-20)
      against live doc state. **7 of 16 have materially changed since batch4 was drafted (2026-07-31) — flagged only, no
      follow-up drafted, per this todo's own scope:**
  - **D4-5** (`orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`) — **operator RULED 2026-08-08** (option
    (b), a non-shared credential file per job). The head `[OPERATOR-DECISION]` gate is closed; 2 implementation todos
    are now open+unblocked directly in the source doc (still `assigned_vm: NA` there). Nothing to draft here — already
    tracked in the source doc's own todos.
  - **D4-6** (`aws_codebuild_terraform_import_pending_2026_07_22.md`) — **operator RULED all 4 rows (D1-D4) 2026-08-09**
    (D1 keep the IAM wildcard; D2 delete the 18 webhook TF resources; D3 adopt live config into TF; D4 fix both
    live-side drifts), reclassified `assigned_vm: NA → planning`. 2 dispatchable todos (`main.tf` reconciliation +
    guarded `terraform import`) now live directly in the doc. Nothing to draft here.
  - **D4-10** (`pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md`) — **operator answered the authority/scope
    question via the 2026-08-08 round7 corpus-wide precedent** ("plan-destination questions default to AO-dispatched"),
    reclassified `assigned_vm: NA → planning`; a paired finalize doc
    (`pm_bats_tests_never_invoked_by_quality_gates_2026_07_26_finalize_2026_08_08.md`) already exists. Both todos
    (warn-only BATS phase + re-harden) are dispatchable as-is. Nothing to draft here.
  - **D4-11** (`ldr_to_main_promote_churn_fix_verification_2026_07_27.md`) — **resolved 2026-08-05**: found the
    operator-gated blocker had already been satisfied a week earlier (quickmerge.sh's Option-B direct-PR-open step no
    longer fires in the normal path; live-measured 0/20 churning-shape PRs). `status: resolved`, archived, zero open.
  - **D4-15** (`provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md`) — already closed by THIS
    finalize plan's own todo 1 (2026-08-09): sole remaining checkbox flipped, doc reached zero-open, archived (see that
    entry below). D4-15's "spot-check or just close" judgment call resolved itself by reaching zero-open.
  - **D4-16** (`sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md`) — same doc as D4-4 (already
    confirmed resolved via this plan's todo 2): batch1's stuck-gate-monitor todo landed
    (`unified-trading-pm@409c35437`), doc `status: resolved`, archived, zero open. D4-16's direction-ruling question is
    moot — the doc closed without needing it.
  - **D4-19** (`github_actions_billing_wall_recurrence_2026_07_29.md`) — **RESOLVED 2026-07-31** (item 1: operator
    cleared the billing block, live-verified). Items 2-4 (the "3 remaining bounded items" batch4 flagged for future
    triage) were **already MIGRATED 2026-08-02** into `ci_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Migrated
    prevention todos from resolved incidents" section (operator ruling,
    `plan_reconcile_parked_operator_decisions_2026_08_02.md` §3) — already extracted elsewhere; nothing left to draft
    from this doc, per this todo's own instruction.
  - **D4-20** (`cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md`) — **re-scoped, dispatched,
    and fully shipped**: archived + resolved 2026-08-07, all todos closed, end-to-end proof via
    `ci_satellite_ao_dispatch_batch5_2026_08_02.md` todo 1. The re-scoping this item needed (name the actual mechanism,
    since the 2026-07-28 drift-checker now correctly refuses 15/19 consumers) happened and the work shipped.

  **9 of 16 re-confirmed unchanged** (still in their batch4-recorded state — no new ruling, no new claiming doc, no
  reclassification):
  - **D4-7** (`capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md`) — both residuals still correctly
    not-auto-queued; a reconciliation note flags Residual 1 as "worth a RECLASSIFY look" but explicitly declined to act
    this round (docs-only batch scope) — an open suggestion, not yet a state change.
  - **D4-8** (`build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`) — sole remaining item (#3) still
    under the explicit "Page-first, do NOT fix here" operator instruction; KEEP-NA re-confirmed round7 (2026-08-08).
  - **D4-9** (`breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`) — still parked as batch2's Deferred
    E8, still unruled.
  - **D4-12** (`mtds_deployment_env_race_survives_single_worker_2026_07_23.md`) — still a genuinely-unbounded
    investigation, KEEP-NA re-confirmed 2026-08-06.
  - **D4-13** (`uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`) — items [A]/[B] still require operator
    sign-off, unchanged; a _separate_ extracted design-call clause (not part of [A]/[B]) was ruled 2026-08-07 (yes) but
    still needs its own bounded-outcome scoping — noted, not a state change to D4-13's own item.
  - **D4-14** (`post_cutover_silent_assumption_sweep_2026_07_23.md`) — still 5 open items, all operator-/design-gated
    (kill-switch time-gate, tag-minting judgment call, F4 cron disposition, `digest-drift-sweep` non-convergence);
    KEEP-NA re-confirmed round7 (2026-08-08).
  - **D4-17** (`qg_sentinel_environment_blind_2026_07_23.md`) — still open, operator sequencing ruling + cross-doc MTDS
    blockers unchanged, re-confirmed 2026-08-06.
  - **D4-18** (`silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md`) — still open, operator-gated P0 (the
    crash-looped `|| true` fix needing a `--selfcheck` mode + staged roll), re-confirmed 2026-08-06.

  No follow-up drafted from this todo per its own scope. **Implication for todo 4 (archival)**: D4-11/D4-15/D4-16/D4-19/
  D4-20 are fully resolved/migrated-elsewhere — no migration needed. D4-5/D4-6/D4-10 are operator-ruled and now
  independently tracked as dispatchable todos in their own source docs — not batch4's concern to re-track. The remaining
  9 (D4-7/8/9/12/13/14/17/18) still need archival-time migration to a tracked follow-up per todo 4's own instruction,
  since they remain genuinely open and unclaimed by any active plan.

- [x] ✅ [DOC] P1. **DONE 2026-08-09 (slot 11, worker→cicd craft). Archived
      `ci_satellite_ao_dispatch_batch4_2026_07_31.md`** via the standard 6-step ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). (1) Migration check: verified all 9
      still-genuinely-open Deferred items (D4-1, D4-7, D4-8, D4-9, D4-12, D4-13, D4-14, D4-17, D4-18) already carry a
      live `- [ ]` checkbox in their own `plans/active/` source doc (grepped each —
      `capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md` (2 open),
      `build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md` (1),
      `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md` (1),
      `mtds_deployment_env_race_survives_single_worker_2026_07_23.md` (1),
      `uac_value_only_config_change_breaks_utl_untested_2026_07_20.md` (5),
      `post_cutover_silent_assumption_sweep_2026_07_23.md` (5), `qg_sentinel_environment_blind_2026_07_23.md` (1),
      `silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md` (3),
      `quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` (1, D4-1) — nothing evaporates; no new todo
      needed. (2) Archive banners added to both batch4.md and this doc. (3) Codex-alignment check: confirmed
      `/codex/08-workflows/deployment-flow.md` already reflects the LDR-direct/dormant-staging rewrite (todo 3), and
      `/codex/08-workflows/ci-cd-flow.md` + `/codex/05-infrastructure/per-tab-worktrees.md` carry no stale reference to
      the deleted `pre-push-strict-quickmerge.sh` hook (todo 1) — both already correctly repointed at
      `scripts/hooks/pre-push`, no NEW undocumented contract found. (4) No further CLAUDE.md/codex update needed —
      nothing new to establish. (5) Corpus-wide referrer sweep: repointed all 24 leading-slash path references across 18
      files (`ci_satellite_ao_dispatch_batch4_2026_07_31.md`'s original active path → `/plans/archive/2026_08/...`) plus
      4 references to this finalize doc's own path; bare prose mentions (no leading slash) left as historical citations
      per existing corpus convention. **Archive target is `plans/archive/2026_08/` (archival-date month), not
      `plans/archive/2026_07/`** as this todo's original text assumed — matches the precedent set by the sibling
      `ci_satellite_ao_dispatch_batch1_2026_07_26.md`/`_finalize` pair, archived the same day into `2026_08`. (6)
      `locked_by` confirmed empty on both docs; both `git mv`d to `plans/archive/2026_08/` in a follow-up commit after
      this checkbox-flip commit (per the archival-ritual's flip-then-move ordering rule). **Done when**: both docs live
      in `plans/archive/2026_08/`, every corpus referrer resolves, `check_reference_paths.py` has not regressed.

## Codex SSOTs

- `/codex/06-coding-standards/quality-gates.md` — how the gate composes; ratchet-baseline convention
- `/codex/08-workflows/ci-cd-flow.md` + `/codex/08-workflows/deployment-flow.md` — the pipeline contracts batch-4 todos
  1/3 touch
- `/codex/04-architecture/ci-alerting.md` — the `notify-slack.yml` carrier pattern batch-4 todo 8 uses
- `/codex/11-project-management/` — archival ritual, issue-doc lifecycle
- `plans/active/task_template.md` §4 — the finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-07-31** — Drafted alongside `ci_satellite_ao_dispatch_batch4_2026_07_31.md` by `/ag-closeout-audit ci`
  (autonomous mode, `ag_closeout_auditor` scheduled worker, slot 12). Authored `status: active` per the skill's
  2026-07-30 no-double-gate finding — `gate_on_depends: true` alone correctly holds every todo above until batch4's own
  todos are done; batch4 itself remains `status: draft` pending operator approval.
- **context-scout 2026-08-01**: populated/refreshed context_scope (6 entries).
- **context-scout 2026-08-03**: re-confirmed context_scope (6 entries) unchanged -- gated finalize doc, correctly
  code-free (dispatch/archival coordination only), all entries still resolve.
- **2026-08-09 (slot 2, review→cicd craft)** — Completed todo 1 (source-doc reconciliation, the last blocker before
  todos 2-4). Batch4's own 9 todos were all already `done` (confirmed via its Progress Log). Verified all 9 cited
  commits live-ancestor `origin/live-defi-rollout`; found 6 of 8 distinct source docs already fully reconciled by prior
  sessions (2 archived+resolved outright, 1 correctly reconciled with its genuine remaining item untouched, 1 already
  reconciled by a sibling `ci_satellite_ao_dispatch_batch6_finalize` worker same-day, 1 `status: superseded` terminal
  with stale-pointer checkboxes explicitly called out, 1 self-reconciled inline by its own todo-9 worker); made 2 real
  edits — flipped `provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md`'s sole remaining checkbox
  (hook deletion, live-verified) to reach zero-open → `status: resolved` → archived (banner + `git mv` to
  `plans/archive/issues/` + 2 corpus referrers repointed), and added the closing citation
  `ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md`'s own 2026-07-31 na-eligibility-audit note
  asked for. No FALSE-CHECKED-checkbox traps found beyond the ones already correctly flagged/handled elsewhere. Todos
  2-4 remain (D4-1..D4-20 re-checks + archival) — not in this todo's scope.
- **2026-08-09 (slot 33, review→cicd craft)** — Completed todo 2 (D4-1 through D4-4 re-check). D4-1: both blockers
  cleared (`unified-trading-pm@b02ba28c7`, `unified-trading-library@dc1dc7df`, both live-verified ancestors) — ready for
  batch-5 extraction, noted only, not drafted. D4-2/D4-3: file freed by batch-4 todo 9, but both underlying items were
  already independently shipped by sibling plan `ci_satellite_ao_dispatch_batch5_2026_08_02.md` todo 2 (2026-08-09) —
  superseded-by-completion, nothing to extract. D4-4: batch1's "still-open" todo has since landed
  (`unified-trading-pm@409c35437`, live-verified ancestor; source doc archived + `status: resolved`, zero open) — fully
  resolved, not open. Todos 3-4 (D4-5..D4-20 re-verify + archival) remain — not in this todo's scope.
- **2026-08-09 (slot 7, review→cicd craft)** — Completed todo 3 (D4-5 through D4-20 re-verify). Read all 16 source docs
  live: 7 have materially changed since batch4 was drafted — D4-5/D4-6/D4-10 operator-ruled and reclassified to
  `assigned_vm: planning` (dispatchable todos now live directly in each source doc, nothing to draft here); D4-11
  resolved 2026-08-05 (blocker turned out already satisfied); D4-15/D4-16 already closed by this finalize plan's own
  todos 1/2; D4-19 resolved 2026-07-31 with items 2-4 already migrated 2026-08-02 into batch1; D4-20 re-scoped,
  dispatched, and shipped via batch5, archived 2026-08-07. The other 9 (D4-7/8/9/12/13/14/17/18) re-confirmed unchanged
  — still in their batch4-recorded operator-/design-gated state, no new claiming doc or ruling. Full per-item detail in
  the todo 3 checkbox above. Flagged only, no follow-up drafted, per this todo's own scope. Todo 4 (archival) remains —
  not in this todo's scope.
- **2026-08-09 (slot 11, worker→cicd craft)** — Completed todo 4 (archival), the last remaining todo. Confirmed all 9
  still-genuinely-open Deferred items (D4-1/D4-7/D4-8/D4-9/D4-12/D4-13/D4-14/D4-17/D4-18) already carry a live `- [ ]`
  checkbox in their own active `plans/active/` source doc — nothing evaporates. Codex-alignment check:
  `deployment-flow.md` and `ci-cd-flow.md`/`per-tab-worktrees.md` already correctly reflect batch4's shipped contracts,
  no new undocumented contract found, no further codex update needed. Repointed 24 leading-slash corpus referrers (18
  files) from `ci_satellite_ao_dispatch_batch4_2026_07_31.md`'s original active path to `/plans/archive/2026_08/...`
  (archival-date month, matching the sibling batch1/batch1_finalize precedent archived the same day), plus 4 referrers
  to this finalize doc's own path. Both docs `git mv`d to `plans/archive/2026_08/` as a follow-up commit after this
  checkbox-flip commit (per the never-combine-flip-with-move rule). `locked_by` confirmed empty on both. Batch 4 and its
  finalize plan are now fully closed.
