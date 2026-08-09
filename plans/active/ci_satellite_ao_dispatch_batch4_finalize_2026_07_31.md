---
doc_type: plan
title: CI satellite AO batch 4 — finalize (reconcile source docs, re-check deferrals, archive)
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch4_2026_07_31.md — machine-held via depends_on + gate_on_depends: true
  until all 9 of that plan's todos are done. Reconciles each distinct source doc's checkboxes/prose independently,
  re-checks the Deferred items (D4-1 through D4-20) for whether their blocker has cleared, and archives batch 4 via the
  standard 6-step ritual.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-4, satellite-docs, archival]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
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
    /plans/active/ci_satellite_ao_dispatch_batch4_2026_07_31.md,
    /codex/06-coding-standards/quality-gates.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/08-workflows/deployment-flow.md,
    /codex/04-architecture/ci-alerting.md,
    /plans/active/task_template.md,
  ]
---

# CI satellite AO batch 4 — finalize

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
- [ ] [REVIEW] P2. **Re-verify the operator-gated (D4-5 through D4-18), live-incident (D4-19), and needs-re-scoping
      (D4-20) Deferred items have not silently changed state.** In particular: has the operator ruled on D4-10 (the
      `pm_bats_tests` base-service.sh plan-destination question, escalated below)? Has
      `github_actions_billing_wall_recurrence_2026_07_29.md` (D4-19) self-resolved or been operator-closed since
      2026-07-31 — if so, note it is ready for a future batch's fresh triage of its 3 remaining bounded items (2-4), do
      NOT draft them here even if it has resolved. Has `aws_codebuild_terraform_import_pending_2026_07_22.md`'s D1-D4
      rulings table (D4-6) received an answer? For every other item (D4-5, D4-7 through D4-9, D4-11 through D4-18,
      D4-20): confirm no new doc has claimed them and no operator ruling has landed that would newly unblock them.
      **Done when**: each is re-confirmed still in its recorded state, or flagged if changed (flag only — do not
      draft/dispatch a follow-up from this reconciliation todo).
- [ ] [DOC] P1. **Archive `ci_satellite_ao_dispatch_batch4_2026_07_31.md`** via the standard 6-step ritual (CLAUDE.md §
      plan archival): migrate any still-unresolved Deferred item to a tracked follow-up (todos 2-3 above should have
      re-confirmed D4-1 through D4-20 — verify none silently vanishes) → add the archive banner → run the
      codex-alignment check (todo 3's `deployment-flow.md` rewrite and todo 1's `ci-cd-flow.md`/ `per-tab-worktrees.md`
      referrer repoints changed durable contracts — confirm those landings are reflected and no NEW undocumented
      contract exists, e.g. the STAGE 1.6 dormancy-aware dep-gate behavior, the `UnifiedCloudServicesConfig`
      alias-precedence fix, the MTDS auto-merge-arm fix) → update CLAUDE.md/codex if any batch-4 todo established a new
      contract → grep the corpus for every referrer of `ci_satellite_ao_dispatch_batch4_2026_07_31` and repoint each to
      the archived path → clear `locked_by` (already empty; confirm). **Done when**: the plan is in
      `plans/archive/2026_07/`, every corpus referrer resolves, `check_reference_paths.py` has not regressed, and this
      finalize doc is archived alongside it in the same commit.

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
