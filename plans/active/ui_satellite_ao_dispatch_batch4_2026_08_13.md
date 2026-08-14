---
doc_type: plan
title: ui satellite AO dispatch batch 4 — 2026-08-13
summary: >-
  Extraction batch from the ui tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 11
  conflict-cleared, bounded/deterministic items pulled directly from 5 source docs (RECLASSIFY_SPLIT bounded items from
  the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each todo
  cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation back
  into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [ui]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ui, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md,
    /plans/active/issues/plan_reconciler_findings_2026_08_07.md,
    /plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md,
    /plans/active/issues/plan_reconciler_findings_ui_2026_08_11.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.6
estimate_calibrated_ai_days: 1.3
assigned_role: ui_developer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# ui satellite AO dispatch batch 4 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] ✅ [CODE] P2. Re-run pw:L2 full smoke suite and flip the 3 CODE-SHIPPED todos (venue-filter frontend, duplicate
      available/available-dates panel collapse, pagination visible-count selector) if it exits 0 — exit 0 confirmed
      (450/450), 3 items flipped in the source doc. A pre-existing unrelated blocker (stale hardcoded
      `capability_tab.spec.ts` manifest counts, missed by fix(capability) 6a323bf) was root-caused + fixed inline:
      deployment-ui@`d95f1934ef`. Source: `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`
- [x] ✅ [CODE] P2. Ship the small Rollup-difference-clarity UI tooltip/note (audit §F, by-design explainer) —
      CODE-SHIPPED deployment-ui@`8033b83651`. Extended the existing `InstrumentsServiceShardModal` note
      (`DataStatusDrilldown.tsx`) with a hover-tooltip explainer + inline text: IS's per-venue/day drilldown has no
      data_type axis by design (reference data), vs MTDS's 5-axis market-data shards — so the structural difference
      reads as intentional, not broken. **pw:L2 ✓** (full `tests/smoke/` re-run, 450/450 passed via 2-shard split) |
      regression: `tests/unit/components/DataStatusDrilldown.test.tsx` (new test: "explains the by-design structural
      difference vs MTDS's 5-axis shards for instruments-service"). Source:
      `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`
- [ ] [CODE] P2. Investigate + resolve the Yahoo/Kalshi market-tick-view out-of-scope registry check (add to
      EXPECTED_COVERAGE_BY_ASSET_GROUP if genuinely provided, else confirm correct-by-design) Source:
      `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`
- [ ] [CODE] P2. Root-fix the per-service coverage BucketNamingError for
      features-calendar/ml-service/features-cross-instrument Source:
      `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`
- [ ] [DOC] P3. Add a one-line cross-file conflict-check note to
      ui_satellite_ao_dispatch_batch3_finalize_2026_08_09.md's todo 1, naming
      ui_satellite_ao_dispatch_batch1_finalize_2026_08_06.md's still-open todo 4 as a same-file
      (artifact_pipeline_observability_2026_07_17.md) dispatch-collision risk. Source:
      `plans/active/issues/plan_reconciler_findings_ui_2026_08_10.md`
- [ ] [CODE] P2. Port the manual-trigger action into the new /ops/artifacts page; remove CloudBuildsTab from the
      per-service tab bar + DeployConsole; delete CloudBuildsTab.tsx (Phase 4) Source:
      `plans/active/artifact_pipeline_observability_2026_07_17.md`
- [ ] [CODE] P2. Retire the superseded narrow deployment-api build/artifact routes once the new artifact_pipeline
      service covers them; delete dead code (Phase 4) Source:
      `plans/active/artifact_pipeline_observability_2026_07_17.md`
- [ ] [CODE] P2. Build→deploy latency join: 'built but never deployed' + build-to-first-revision latency (Phase 6
      stretch) Source: `plans/active/artifact_pipeline_observability_2026_07_17.md`
- [ ] [CODE] P2. Add a deploy-churn/crash-loop health condition (e.g. a service redeployed ~14x in hours, ~40%
      config-only) (Phase 6 stretch) Source: `plans/active/artifact_pipeline_observability_2026_07_17.md`
- [ ] [CODE] P2. Resolve the ACTIVE_INDEX.md dangling normative-ref: edit cursor-configs/skills/plan-reconcile/SKILL.md
      (lines 5,59,425) + agents/plan_reconciler.md (line 114) to drop the stale name and cite only INDEX.md, or
      regenerate ACTIVE_INDEX.md if a distinct artifact was genuinely intended Source:
      `plans/active/issues/plan_reconciler_findings_2026_08_07.md`
- [ ] [CODE] P2. Expand the ui-tranche doc discovery/inventory logic (used by /plan-reconcile ui and /ag-closeout-audit
      ui) to include multiline-frontmatter `asset_group:` docs missed by same-line grep (named examples:
      data_status_tab_and_downloads_remediation_2026_06_16.md, deployment_registry_firestore_migration_2026_07_14.md).
      Source: `plans/active/issues/plan_reconciler_findings_ui_2026_08_11.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
