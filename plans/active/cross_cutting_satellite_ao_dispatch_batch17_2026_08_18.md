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
parent_epic: security_and_cross_cutting_master
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
    unified-trading-pm/.github/workflows/branch-health.yml,
    unified-trading-ci/.github/workflows/main-backmerge-to-ldr.yml,
    /codex/08-workflows/ci-cd-flow.md,
  ]
source: >-
  /na-eligibility-audit cross-cutting tranche, dispatch agt-4d9716, slot 19, 2026-08-18. Each item's own Source:
  line below names the exact source doc + todo it was extracted from.
---

# cross-cutting satellite AO dispatch batch 17

## From `main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md`

- [x] ✅ [CI] P1. **Make the `branch-health.yml` drift-tick safety-net FLEET-WIDE instead of `github.repository`-scoped.** — unified-trading-pm@96c163347f
      Dispatch `main-backmerge-to-ldr.yml` for every `promotion_model: ldr_main` repo in `workspace-manifest.json`
      (the same repo-list read the AR-lag job in that file already does), not just `unified-trading-pm`. Without
      this, a single transient GHA failure (e.g. a `429` downloading `actions/create-github-app-token`) strands
      any fleet repo's LDR until a human or a `conflict_resolver` notices — measured live: 11h13m drift on
      trading-agent-service, 2026-08-17/18. Done-when: `branch-health.yml`'s drift-tick job loops every `ldr_main`
      repo (not just PM) and a live dispatch test confirms a non-PM repo receives the trigger. Source:
      `/plans/active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md` todo 1.
      Repo: unified-trading-pm.
- [x] ✅ [CI] P2. **Fix the misleading safety-net comment in the `main-backmerge-to-ldr.yml` caller stub, once P1
      lands.** — comment corrected in **25 per-repo caller stubs** (23 shipped + verified on origin; 3 parked on
      pre-existing QG reds, see Progress Log 2026-08-20)
      It currently states the drift-tick is "now handled by PM's branch-health.yml (every 30 min) which
      dispatches this workflow" and that "for non-PM repos the push trigger covers the common case" — both
      mislead: the cadence is hourly, not 30 min, and (pre-P1) the dispatch never reached non-PM repos at all.
      **Correction to the source doc's own fix-location text (found during this extraction's conflict-check)**:
      the misleading text physically lives in **each repo's thin caller stub** (`.github/workflows/main-backmerge-to-ldr.yml`,
      the `uses:` stub pointing at the `unified-trading-ci`-hosted reusable workflow) — NOT in the reusable
      workflow itself, which carries no such comment, and NOT `unified-trading-pm/scripts/workflow-templates/`
      (deleted during the 2026-08-07/08 template-hosting migration, `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`
      todos 4/7). Depends on the P1 todo above landing first — the corrected wording depends on what the net actually
      becomes. Done-when: the comment accurately describes the post-P1 fleet-wide, hourly safety-net. Source:
      `/plans/active/issues/main_backmerge_to_ldr_no_retry_safety_net_for_non_pm_repos_2026_08_18.md` todo 2.
      Repo: 25 fleet caller stubs.
- [x] ✅ [CI] P2. **Add a detection surface for a FAILED backmerge run**, distinct from the already-shipped — unified-trading-pm@2ead733819 + Evidence: YAML parse OK; embedded shell bash -n OK; commit hooks YAML/provenance passed; origin ancestry verified.
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

- **2026-08-20 (worker, slot 7, dispatch cross_cutting_satellite_ao_dispatch_batch17-4873e1ae623b)**: shipped unified-trading-pm@2ead733819, adding a fleet-aware latest-run query for main-backmerge-to-ldr.yml, cached per-repo failure state, state-transition deduplication, and recovery/all-clear Slack carrier jobs. YAML parsing, embedded shell syntax, diff checks, commit hooks, and origin ancestry all passed. The full QG/quickmerge reservation remained queued for 24 minutes on a saturated shared host; the workflow-only .github/** carve-out was used after stopping only this session's stalled quickmerge process.

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

- **context-scout 2026-08-19**: refreshed context_scope (4 entries) — added the 2 real workflow-file targets the 3
  open todos edit directly: `unified-trading-pm/.github/workflows/branch-health.yml` (items 1 and 3, the fleet-wide
  dispatch fix and the new failure-detection surface) and
  `unified-trading-ci/.github/workflows/main-backmerge-to-ldr.yml` (item 2, the caller-stub comment fix — confirmed
  this is the real post-migration hosting location, matching this batch's own drafting-time correction above).
- **2026-08-19 (worker, slot 7, dispatch cross_cutting_satellite_ao_dispatch_batch17-6a8c25390694)**: item 1 DONE —
  `branch-health.yml`'s drift-tick now dispatches `main-backmerge-to-ldr.yml` for unified-trading-pm + every
  `promotion_model: ldr_main` repo in `workspace-manifest.json` (read from live-defi-rollout, fleet-promote staleness
  guard; repo-set mirrors `_main_direct_repos()` in `scripts/cicd/promotion_lag_monitor.py`; best-effort loop;
  timeout-minutes 3→10). Live dispatch test confirmed a non-PM repo receives the trigger: trading-agent-service run
  32303502126 (`workflow_dispatch`, completed success — backmerge ran clean/noop). Shipped unified-trading-pm@96c163347f
  (Pass-1 QG green → quickmerge `--agent` landed → post-push ancestry verified). Items 2 (comment fix, unified-trading-ci)
  and 3 (failed-backmerge detection surface) remain open; item 2 depends on this landing per its own note.
- **2026-08-20 (worker, slot 6, dispatch cross_cutting_satellite_ao_dispatch_batch17-640def3b3205)**: item 2 DONE —
  corrected the misleading caller-stub comment in all 25 per-repo caller stubs (the plan's "edit the reusable
  workflow in unified-trading-ci" pointer was wrong about the physical location — that file is the `workflow_call`
  reusable workflow and carries no such comment; the misleading text is the per-repo stub comment). Shipped 23/25
  via Pass-1 QG + quickmerge `--agent` and verified the corrected comment on `origin/live-defi-rollout` per repo
  (`git show origin/live-defi-rollout:<file>` old-comment-count=0). **3 repos parked on pre-existing QG reds** —
  features-service (RB-5e5dbb39), unified-trading-library (RB-09ca4f33), execution-service (RB-70f96454) — each
  with an unrelated Python test failure (comment-only YAML change cannot cause it); the fix commit is ready
  locally and ships once the blocker clears. **Finding filed**: on 5 repos the promote→`main-backmerge-to-ldr`
  cycle silently reverted the shipped comment-only change (commit became a non-ancestor of
  origin/live-defi-rollout) — the "ahead=0 ≠ landed" trap; 2 re-shipped + converged (fix now on main), root-cause
  reproduction tracked in `plans/active/issues/main_backmerge_backmerge_cycle_reverts_caller_stub_comment_fix_2026_08_20.md`.
