---
doc_type: plan
title:
  UI satellite AO batch 4 — denominator-freshness trust annotation (na-eligibility-audit RECLASSIFY-per-todo-split of
  data_status_tab_and_downloads_remediation)
summary: >-
  Fourth AO-dispatch batch for the ui tranche, produced by the 2026-08-17 na-eligibility-audit RECLASSIFY-per-todo-split
  pass on `data_status_tab_and_downloads_remediation_2026_06_16.md`. Extracts the ONE bounded item out of that doc's 3
  remaining open todos (the other 2 stay NA — both explicitly self-gated on the same still-open, named 2026-08-07
  operator HOLD on defi/sports APPLY-GATE sign-off): add a denominator-freshness / coverage-% staleness trust
  annotation to the data-status tab, mirroring the pattern `consolidator_throughput_backlog_monitor_2026_07_09.md`
  already ships. The concept was concretely hand-off'd in that doc's own text (2026-07-10); no design/implementation
  exists yet.
status: active
nature: process
asset_group: [ui]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer]
tags: [ui, ao-dispatch, close-out, batch-4, satellite-docs, data-status, denominator-freshness]
related:
  [
    /plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
    /plans/active/ui_satellite_ao_dispatch_batch4_finalize_2026_08_17.md,
    /plans/active/ui_consolidated_closeout_2026_07_30.md,
  ]
created: "2026-08-17"
last_updated: "2026-08-17"
parent_epic: deployment_and_user_management_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md,
    /plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md,
  ]
source: >-
  na-eligibility-audit 2026-08-17 (ui tranche, dispatch agt-96972b) — RECLASSIFY-per-todo-split of
  `data_status_tab_and_downloads_remediation_2026_06_16.md`'s Phase B todo (added 2026-08-16 by plan_reconciler
  agt-8fc5a6 as a zero-checkbox-to-todo conversion of a 2026-07-10 prose hand-off).
assigned_role: ui_developer
effort: low
sequential: false
drift_direction: advance-code
---

# UI satellite AO batch 4 (deployment_and_user_management_master) — denominator-freshness trust annotation

> **Status: active.** 1 todo, conflict-checked clean against every active `assigned_vm: planning` doc under
> `parent_epic: deployment_and_user_management_master` (only `ui_satellite_ao_dispatch_batch1_2026_08_06.md` +
> its finalize twin — neither touches this) and a corpus-wide "denominator" grep (no other active plan claims this
> work), plus `ui_consolidated_closeout_2026_07_30.md`'s Track content (no overlap).

## Todos

- [x] ✅ [UI] P3. **Denominator-freshness / coverage-% staleness trust annotation.** Add a UI trust/staleness indicator
      to the data-status tab (deployment-ui) showing how fresh the denominator (coverage-%) computation is, mirroring
      the annotation pattern `consolidator_throughput_backlog_monitor_2026_07_09.md` already ships (a "denominator
      last computed Nh ago" stale-warning caveat on the coverage-% headline). Source:
      `data_status_tab_and_downloads_remediation_2026_06_16.md`'s Phase B todo (item extracted verbatim; that doc's
      own checkbox is flipped citing this doc). First confirm whether the backend (deployment-api) already exposes a
      "denominator last computed" timestamp for the data-status rollup; if not, add it as part of this same todo (a
      small, bounded backend addition — not a design question). Repo: deployment-api + deployment-ui. Done when: the
      coverage-% headline shows the staleness annotation live, `[UI]` + `pw:L2 ✓` + a regression spec covering it. Evidence: deployment-ui@153eae2cf1 + deployment-api@3180b1c22e + tests/smoke/data_status_denominator_freshness.spec.ts + tests/unit/test_data_status_denominator_freshness.py + pw:L2 ✓.

## Codex SSOTs

None new — this is a small UI/backend feature addition mirroring an existing pattern, no contract change.

## Progress Log

- **2026-08-17**: Batch authored via the 2026-08-17 na-eligibility-audit RECLASSIFY-per-todo-split pass (ui tranche,
  dispatch agt-96972b) on `data_status_tab_and_downloads_remediation_2026_06_16.md`. That doc's other 2 open todos
  (DeFi sub-bucket phantom-row audit; defi/sports APPLY-GATE sign-off) stay `assigned_vm: NA` — both are explicitly
  self-gated on a still-open, named 2026-08-07 operator HOLD, not bounded/AO-eligible. Conflict-checked clean: grepped
  `plans/active/` for "denominator" (no other active plan claims this work) and confirmed the only 2 active
  `assigned_vm: planning` docs under `parent_epic: deployment_and_user_management_master`
  (`ui_satellite_ao_dispatch_batch1_2026_08_06.md`/`_finalize`) don't touch it either.
- **context-scout 2026-08-20**: populated/refreshed context_scope (2 entries)
