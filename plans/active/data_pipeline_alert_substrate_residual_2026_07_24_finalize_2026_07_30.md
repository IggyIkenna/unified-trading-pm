---
doc_type: plan
title: Finalize — data-pipeline alert-substrate residual close-out
summary: >-
  Gated close-out twin for `data_pipeline_alert_substrate_residual_2026_07_24.md`, which was reclassified `assigned_vm:
  NA → planning` by the 2026-07-30 `/na-eligibility-audit cross-cutting` run. Holds the post-ship verification +
  archival ritual for that plan's 3 remaining todos (the per-source SOURCE_RATE_LIMITED / SOURCE_KEY_POOL_EXHAUSTED
  event, the deployment-ui streaming-events pane, and the UTL DP_DAILY_DIGEST / DP_HYGIENE_SUMMARY string constants).
  Flipped to `status: active` 2026-07-30 once the source plan's last todo (the market-tick-data-service
  SOURCE_RATE_LIMITED/SOURCE_KEY_POOL_EXHAUSTED item) landed — `market-tick-data-service@7f42c557`.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service, deployment-ui, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit, data-pipeline, alerting, observability]
related:
  [
    /plans/active/data_pipeline_alert_substrate_residual_2026_07_24.md,
    /plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: [data_pipeline_alert_substrate_residual_2026_07_24]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /na-eligibility-audit cross-cutting, 2026-07-30 — RECLASSIFY verdict on
  data_pipeline_alert_substrate_residual_2026_07_24.md. Phase-2 conflict-check CLEAR for the 3 OPEN todos:
  cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md's claims against this doc all land on items already `[x]`
  here (the Phase-4 writer invariants, the alerting reliability trio, and the dp-audit terraform apply).
---

# Finalize — data-pipeline alert-substrate residual close-out

> **Gated twin** (`gate_on_depends: true`). Do NOT start until every todo in
> [`/plans/active/data_pipeline_alert_substrate_residual_2026_07_24.md`](/plans/active/data_pipeline_alert_substrate_residual_2026_07_24.md)
> is `- [x]` with cited evidence. Authored by the 2026-07-30 `/na-eligibility-audit` reclassification pass per
> [`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
> § 1(b).

## Why this exists

The source plan is the residual tail of the shipped emit→route→escalate alert substrate. Its 3 remaining todos are
bounded code/UI work, which is why the NA audit reclassified it. Two of them, though, only become REAL once they are
observed end-to-end in prod — a registered event that never routes, or a UI pane that renders nothing, is exactly the
"shipped but not operationally shipped" failure this workspace's plans-run-to-actual-completion rule exists to catch.
This twin holds that verification plus the archival ritual.

## Todos

- [ ] [DATA] P1. **Verify the new rate-limit/health events actually ROUTE, not just emit.** Once
      `SOURCE_RATE_LIMITED{source, venue, http_429_count}` + `SOURCE_KEY_POOL_EXHAUSTED` are emitted by MTDS, confirm
      each has a matching rule in the UAC `DATA_PIPELINE_ALERT_RULES` registry and lands in `#data-pipeline-alerts` —
      not the generic INCIDENT catch-all. This is the exact defect class already recorded on this plan's sibling (the
      `DP_FLEET_MONITOR_RUN_*` events that fell through to the catch-all because they were never registered, fixed
      `unified-api-contracts@92e068ea`). **Done when**: a real or injected 429-storm produces a routed
      `#data-pipeline-alerts` post, with the rule ids cited. Repos: market-tick-data-service, unified-api-contracts.
- [ ] [UI] P2. **Confirm the streaming-events pane renders a real VM event stream.** The source plan's `[UI] P0` ships
      the pane; this verifies it against live data rather than mock — per-AG/per-VM tail, honest empty-state when a VM
      has emitted nothing (never a fabricated row). `[UI]` gate applies: needs `pw:L2 ✓` plus a cited regression spec
      per [`/codex/06-coding-standards/ui-testing-layers.md`](/codex/06-coding-standards/ui-testing-layers.md). **Done
      when**: the pane is verified against a live stream and the regression spec is cited. Repo: deployment-ui.
- [ ] [PLANNING] P3. **Archive the source plan per the 6-step ritual.** Once the two verifications above are done and
      the source plan has zero open todos and no `locked_by:`, run the standard archival ritual from
      [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)
      (dated archive folder, `status: complete`, every corpus referrer repointed — note the sibling forks
      `data_pipeline_self_healing_completion_residual_2026_07_24.md` and
      `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md` both cite it, as does the parent
      `data_pipeline_hardening_self_monitoring_2026_06_22.md`), then archive this finalize twin alongside it. **Done
      when**: both docs are under `plans/archive/2026_07/` and `regenerate_active_plan_inventory.py` reports 0 new
      orphans. Repo: unified-trading-pm.

## Codex SSOTs

- [`/codex/05-infrastructure/data-pipeline-alerts.md`](/codex/05-infrastructure/data-pipeline-alerts.md) — the
  failure-mode registry + emit→route→escalate model todo 1 verifies against.
- [`/codex/06-coding-standards/ui-testing-layers.md`](/codex/06-coding-standards/ui-testing-layers.md) — the `pw:L2`
  gate todo 2 must satisfy.
- [`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`](/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md)
  — the naming/pairing convention + the conflict-check that cleared the reclassification.
- [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md)
  — the 6-step archival ritual todo 3 runs.

## Progress Log

- **2026-07-30** — Authored by the `/na-eligibility-audit cross-cutting` tranche run as the paired finalize twin for the
  `NA → planning` reclassification of `data_pipeline_alert_substrate_residual_2026_07_24.md`. No work executed here;
  `status: draft` + `gate_on_depends: true` hold it until the source plan's todos land.
