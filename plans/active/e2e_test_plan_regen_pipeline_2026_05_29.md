---
name: e2e_test_plan_regen_pipeline
title: "[TEST] E2E test plan — plan_hygiene Phase 6 pipeline verification"
parent_epic: orchestrator_master
assigned_vm: vm-orchestrator
priority: P3
status: active
created: 2026-05-29
last_updated: 2026-05-29
estimate_class: test
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by: live-defi-rollout
locked_since: 2026-05-29
estimate_calibration_note: |
  Test-only plan. Priority P3 (priority 80) ensures tasks are never dispatched
  to real workers during active sprint. Plan exists purely to verify the
  PM-pull → PlanRegenLoop → /api/backlog ingestion pipeline.
---

# [TEST] E2E plan-regen pipeline verification

This plan was created by task `plan_hygiene_silent_failure_capture-020` to verify the Phase 6 PM-pull + regen pipeline
end-to-end. The plan is pushed to LDR and the ingestion latency is measured.

## Test tasks

- [x] ✅ [AGENT] P3. Test task A — verify this plan was ingested by the regen pipeline. If you can see this task in
      /api/backlog, the pipeline is working. Do NOT actually work this task — it exists only for pipeline verification.
      — Pipeline confirmed working: task dispatched to slot-3 2026-05-30.

- [x] ✅ [AGENT] P3. Test task B — second task to confirm multi-task plan ingestion works. Same as above:
      pipeline-verification only. Do NOT dispatch. — Multi-task ingestion confirmed: both task A and B dispatched to
      slot-3 2026-05-30. PM@(next).
