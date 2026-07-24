---
doc_type: issue
title:
  First live run of /vm-preemption-billing-waste-audit + design for a cross-run pre-flight gate on known-dead shards
summary: >-
  Two follow-ups from `/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md` (shipped 2026-07-24) that
  the codex doc itself explicitly defers: (1) the skill (`/vm-preemption-billing-waste-audit`) exists but has never been
  run for real against both clouds' live fleets — its findings are unknown until it's actually invoked; (2) the codex
  doc's own "What this contract deliberately does NOT do" section names a real gap — no automated pre-flight gate stops
  a future backfill wave from re-attempting a shard `classify_venue_error()` already FAIL-classified, or one that's
  failed identically across N consecutive waves. Both are tracked here per
  `data_pipeline_e2e_milestones_gate_2026_07_24.md` §4.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, market-tick-data-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [vm, spot, preemption, billing, attempted_failed, monitoring, cost, pre-flight-gate]
related:
  [
    /codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md,
    /codex/04-architecture/shard-level-failure-isolation.md,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md §4
depends_on: []
---

# First live run of the VM billing-waste audit + pre-flight gate design

## Todos

- [ ] [SCRIPT] P1. Run `/vm-preemption-billing-waste-audit` for the first time against both clouds' live fleets with a
      30-day lookback. Definition-of-done: for every launcher family, either a filed finding (preemption with no
      matching auto-recovery, or a confirmed billing-wasting `attempted_failed` cluster) or a stated "clean" — cite the
      run's own output, not a summary.
- [ ] [BACKEND] P2. Design + wire a cross-run pre-flight gate: when `classify_venue_error()` returns `action=FAIL` for a
      shard (or N consecutive waves hit the identical `error_reason` on the same shard), route it to a "known-dead, do
      not re-attempt" manifest-level marker instead of the current default (silent infinite retry via
      `record_failed()`). Definition-of-done: the marker mechanism is designed (schema field or side-table), at least
      one launcher family wired to check it before dispatching a shard, and a regression test proving a marked shard is
      skipped on the next wave.
