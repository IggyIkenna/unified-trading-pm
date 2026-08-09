---
doc_type: issue
title: >-
  10 active docs carry `assigned_role: devops` — not a valid role in the live `agents/*.md` registry
summary: >-
  Two independent agents in today's na-eligibility-audit RECLASSIFY conflict-check+flip pass (2026-08-08) each hit the
  same corpus hygiene gap on a different doc: `assigned_role: devops` is not a real role — the live registry
  (`agents/*.md`) has no `devops.md`, only `infra`, `cicd`, `backend_engineer`, `data_engineering`, and others. Both
  agents corrected their own doc in-place (one to `infra`, one to `cicd`, picked per that doc's actual subject matter)
  and flagged that the same invalid value likely exists elsewhere, without doing a corpus-wide sweep (out of scope for
  their dispatch). A precise grep (`grep -l '^assigned_role: devops$'`) confirms 10 more docs still carry it.
status: resolved
nature: issue
asset_group: [ci, cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, frontmatter, assigned-role, na-eligibility-audit, doc-maintenance]
related:
  [
    /plans/active/issues/deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md,
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
    /plans/active/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: 2026-08-08
author: claude-agent
parent_epic: agent_operating_framework_master
priority: P3
source:
  na-eligibility-audit RECLASSIFY conflict-check+flip pass 2026-08-08 — 2 sub-agents each independently found +
  corrected this on their own target doc, flagged the pattern as corpus-wide, neither dispatched to fix the rest.
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: none
depends_on: []
locked_by:
resolved_by: backend_engineer/review (slot 11, unified-trading-pm@987cb57342, 2026-08-09)
context_scope: [agents/infra.md, agents/cicd.md, scripts/docs/docspec.py]
---

# `assigned_role: devops` is not a valid role — 10 docs still carry it

> **🟢 ARCHIVED (2026-08-09).** Sole todo done + verified: `unified-trading-pm@987cb57342` retagged all 15 (grown from
> 10 at filing) live docs off the invalid `devops` value;
> `grep -l '^assigned_role: devops$' plans/active/*.md plans/active/issues/*.md` returns zero results, confirmed.
> Extracted-batch source doc — see `/plans/active/ci_satellite_ao_dispatch_batch8_2026_08_09.md` todo 1 for the shipping
> work itself (not yet archived as of this doc's own archival — a separate, gated finalize-plan todo).

## What was found

`agents/*.md` (the live role registry `docspec.py` validates `assigned_role` against) has no `devops` role. The valid
roles as of 2026-08-08: `backend_engineer`, `cefi_mtds_smoke_tester`, `cefi_reconciliation_auditor`, `cicd`,
`data_engineering`, `docs_reconciler`, `infra`, `main`, `monitor`, `plan_health`, `quant_dev`, `review`, `ui_developer`,
`worker` (plus the audit-role names: `ag_closeout_auditor`, `context_scout_auditor`, `na_eligibility_auditor`,
`plan_reconciler`, `escalation_queue_reconciler`, `conflict_resolver`, `data_pipeline_failure`).

Two docs already got fixed in-place today (as a side effect of unrelated dispatches, not a corpus sweep):
`deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md` (→ `infra`),
`provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md` and
`workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md` (→ `cicd`).

**10 more still carry the invalid value**
(`grep -l '^assigned_role: devops$' plans/active/*.md plans/active/issues/*.md`, re-verify at execution time since this
corpus changes daily):

- `plans/active/issues/agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md`
- `plans/active/issues/build_deploy_pipeline_provenance_and_aws_deferred_gaps_2026_07_21.md`
- `plans/active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md`
- `plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md`
- `plans/active/issues/glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md`
- `plans/active/issues/ldr_to_main_promote_fleet_queued_run_cancelled_livelock_2026_08_07.md`
- `plans/active/issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`
- `plans/active/issues/semver_agent_squash_promote_blind_to_patch_fixes_2026_08_07.md`
- `plans/active/issues/unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md`
- `plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md`

## Why it matters

Not currently gate-blocking (these docs are `assigned_vm: NA`, so `assigned_role` isn't consumed by dispatch yet) — but
every one of them is CI/CD-topic content, so if/when any gets reclassified to `assigned_vm: planning` (several are
plausible RECLASSIFY candidates on their own merits), an invalid role would either hard-fail `docspec.py`'s registry
check at that point or silently misroute the dispatch. Cheaper to fix now, in one pass, than to rediscover it 10
separate times during future reclassification passes.

## Todos

- [x] ✅ **[DOC] P3. DONE 2026-08-09 — see `ci_satellite_ao_dispatch_batch8_2026_08_09.md` todo 1.** Shipped:
      `unified-trading-pm@987cb57342` (ancestry-verified `origin/live-defi-rollout`) —
      `grep -l     '^assigned_role: devops$' plans/active/*.md plans/active/issues/*.md` returns zero results. ~~Retag
      all 10 docs' `assigned_role: devops` to the correct real role~~ — read each doc's actual subject matter and pick
      the best fit (likely `cicd` for most, `infra` for host/VM-adjacent ones — mirror the judgment the 2 already-fixed
      docs used, don't default all 10 to the same value without reading each). Validate against the live `agents/*.md`
      registry, never hand-type a near-miss. **Done when**:
      `grep -l '^assigned_role: devops$' plans/active/*.md plans/active/issues/*.md` returns zero results. Repo:
      unified-trading-pm.

## Codex SSOTs

- `/codex/11-project-management/doc-frontmatter-schema.md` — `assigned_role` field definition + registry validation.

## Progress Log

- **2026-08-09 (review craft, slot 11, ci_satellite_ao_dispatch_batch8_finalize todo 1)**: Batch-8 todo 1 (the extracted
  retag work) shipped at `unified-trading-pm@987cb57342` — ancestry-verified an ancestor of `origin/live-defi-rollout`
  before citing it. Re-ran the done-when grep myself:
  `grep -l '^assigned_role: devops$' plans/active/*.md plans/active/issues/*.md` returns zero results, confirmed. This
  was this doc's ONLY todo — flipped it `[x]` with the verified commit citation and set `status: resolved` (zero open
  work). Archival is the finalize plan's next (sequential) todo.
- **2026-08-09 (satellite-batch extraction)**: This doc's sole todo extracted verbatim into
  `ci_satellite_ao_dispatch_batch8_2026_08_09.md` todo 1 (checkbox above replaced with a citation pointer, per the
  `ci`-tranche satellite-batch-extraction pattern — this item's own `parent_epic` differs from the sibling
  `infrastructure_master`-group items pulled into batch 7, so it got its own batch per the parent_epic-grouping rule).
- 2026-08-08: Filed following the pre-compact ritual's Step 1 audit (chat-only finding from 2 sub-agent reports,
  converted to a tracked todo per the workspace's HARD RULE that every deferral must be a `- [ ]`, not prose).
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (3 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:3a10c7ffb2d96eae]:
  KEEP-NA, valid — 0 open `- [ ]` todos (sole item already extracted + cited to
  `ci_satellite_ao_dispatch_batch8_2026_08_09.md` todo 1, per today's `ag_closeout_audit_ci_parked_2026_08_09.md` Phase
  0-1 delta: "archivable_after_planned_work"). Not archive-eligible yet — batch8 todo 1 hasn't executed. Nothing further
  for this run to fix.
