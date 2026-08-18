---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 17 — 2026-08-18
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-18 /na-eligibility-audit sweep (slot 19,
  na_eligibility_auditor, dispatch agt-4d9716) — 3 conflict-cleared, bounded/deterministic items pulled from 1
  source doc (RECLASSIFY per-todo split). Each todo cites its exact source doc; the source doc's own extracted
  checkboxes are flipped with a citation in the same audit pass, not deferred to this batch's finalize. Conflict-
  checked against every active-plan hit for "main-backmerge-to-ldr"/"branch-health.yml" (7 docs: ao_satellite_batch3,
  ci_pipeline_speed_and_cost_redesign, ci_satellite_batch13, cross_cutting_satellite_batch13,
  fleet_workflow_template_dedup_to_unified_trading_ci, github_actions_operator_gated_followups,
  june_2026_vintage_audit_findings), the cross-cutting consolidated closeout, and existing satellite batches
  (13-16) before drafting — no item here duplicates ground an existing dispatched todo already claims.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, unified-trading-ci, trading-agent-service]
scope: [engineer, admin]
tags: [cross-cutting, ao-dispatch, satellite-batch, na-eligibility-audit, ci-cd, backmerge]
related:
  [
    /plans/active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md,
  ]
created: "2026-08-18"
last_updated: "2026-08-18"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: cicd
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
source: >-
  /na-eligibility-audit cross-cutting tranche, dispatch agt-4d9716, slot 19, 2026-08-18. Each item's own Source:
  line below names the exact source doc + todo it was extracted from.
---

# cross-cutting satellite AO dispatch batch 17

## From `main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md`

- [ ] [CI] P1. **Make the `branch-health.yml` drift-tick safety-net FLEET-WIDE instead of `github.repository`-scoped.**
      Dispatch `main-backmerge-to-ldr.yml` for every `promotion_model: ldr_main` repo in `workspace-manifest.json`
      (the same repo-list read the AR-lag job in that file already does), not just `unified-trading-pm`. Without
      this, a single transient GHA failure (e.g. a `429` downloading `actions/create-github-app-token`) strands
      any fleet repo's LDR until a human or a `conflict_resolver` notices — measured live: 11h13m drift on
      trading-agent-service, 2026-08-17/18. Done-when: `branch-health.yml`'s drift-tick job loops every `ldr_main`
      repo (not just PM) and a live dispatch test confirms a non-PM repo receives the trigger. Source:
      `/plans/active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md` todo 1.
      Repo: unified-trading-pm.
- [ ] [CI] P2. **Fix the misleading safety-net comment in the `main-backmerge-to-ldr.yml` caller stub, once P1
      lands.** It currently states the drift-tick is "now handled by PM's branch-health.yml (every 30 min) which
      dispatches this workflow" and that "for non-PM repos the push trigger covers the common case" — both
      mislead: the cadence is hourly, not 30 min, and (pre-P1) the dispatch never reached non-PM repos at all.
      **Correction to the source doc's own fix-location text (found during this extraction's conflict-check)**:
      edit the reusable workflow hosted in `unified-trading-ci` — NOT `unified-trading-pm/scripts/workflow-templates/`,
      which no longer hosts `main-backmerge-to-ldr.yml` at all (deleted during the 2026-08-07/08 template-hosting
      migration, `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` todos 4/7 — every fleet
      repo's own copy, including PM's, is now a thin `uses:` stub pointing at the `unified-trading-ci`-hosted
      file). Depends on the P1 todo above landing first — the corrected wording depends on what the net actually
      becomes. Done-when: the comment accurately describes the post-P1 fleet-wide, hourly safety-net. Source:
      `/plans/active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md` todo 2.
      Repo: unified-trading-ci.
- [ ] [CI] P2. **Add a detection surface for a FAILED backmerge run**, distinct from the already-shipped
      `backmerge_sync_failure` escalation wall_type (which polls for RESOLUTION of an already-open escalation on
      `DECISION=error` — a different mechanism, not proactive detection; see
      `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md`'s Progress Log). `branch-health.yml`'s
      lag-monitor already computes LDR↔main lag per repo — assert additionally that the most recent
      `main-backmerge-to-ldr` run per repo did not end `failure`, and route it through the existing
      `notify-slack.yml` carrier with a state-transition `dedup_key` (same pattern every other standing CI alert
      in that carrier uses). Done-when: a deliberately-failed test run produces exactly one dedup'd Slack alert,
      and a subsequent healthy run produces a recovery/all-clear per the carrier's existing convention. Source:
      `/plans/active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md` todo 3.
      Repo: unified-trading-pm.

## Progress Log

- **2026-08-18 (na_eligibility_auditor, dispatch agt-4d9716, slot 19)**: drafted from the cross-cutting tranche's
  2026-08-18 audit — 3 of the source doc's 4 open todos are bounded/deterministic with cited existing patterns
  (repo-list read, notify-slack carrier, dedup_key convention); todo 4 (evaluate a warm local action-cache) stays
  in the source doc, explicitly framed there as an open investigation with an uncertain answer ("the answer may
  be 'accept the transient'"). Conflict-check swept every active-plan hit for "main-backmerge-to-ldr"/
  "branch-health" (7 docs) — all cover a different axis (git-ref hygiene, CI cost/billing, stuck-queued-run
  cleanup, template hosting location, self-hosted-runner migration cost, an already-shipped escalation-resolution
  poll for a different `DECISION=error` case) — none claims the fleet-wide dispatch-scope fix, the comment
  correction, or the failure-detection surface. Found and corrected one staleness while checking: todo 2's
  original text pointed at `unified-trading-pm/scripts/workflow-templates/` as the edit location, which no longer
  hosts `main-backmerge-to-ldr.yml` (migrated to `unified-trading-ci` per the 2026-08-06 dedup plan) — corrected
  above rather than propagating the stale pointer forward.
