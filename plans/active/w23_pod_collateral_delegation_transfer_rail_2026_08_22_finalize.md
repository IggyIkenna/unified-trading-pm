---
doc_type: plan
title: W23 POD collateral-delegation rail — finalize
summary: >-
  Gated finalize for w23_pod_collateral_delegation_transfer_rail_2026_08_22 — reconcile evidence back to the epic
  and T4 plan, re-verify the mock async state-machine actually exercises multi-poll timing (not first-poll-instant),
  archive once done.
status: active
nature: process
asset_group: [defi]
stage: [execution]
repos: [execution-service, unified-trading-pm]
scope: [engineer]
tags: [execution, transfer, pod, w23, finalize]
related:
  [
    /plans/active/w23_pod_collateral_delegation_transfer_rail_2026_08_22.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/code_readiness_t4_execution_settlement_2026_08_19.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: [w23_pod_collateral_delegation_transfer_rail_2026_08_22]
gate_on_depends: true
supersedes:
superseded_by:
locked_by:
locked_since:
sequential: true
context_scope:
  [
    /plans/active/w23_pod_collateral_delegation_transfer_rail_2026_08_22.md,
    /plans/epics/system_readiness_master.md,
  ]
source:
---

# W23 POD collateral-delegation rail — finalize

## Progress Log

- 2026-08-22 — Plan authored alongside the parent W23 plan, mirroring W14/W15/W22's finalize pattern.

---

- [ ] [AGENT] P0. **Re-verify the mock actually exercises multi-poll timing, not instant success** — don't trust
      the parent plan's own done-claim: independently drive `MockPodCollateralAdapter` through
      `TransferConfirmationPoller.wait_for_confirmation` and confirm the result is `PENDING` after poll 1 with
      default config (per the parent plan's Section B `MockPodCollateralAdapter` todo's stated done-condition) —
      if it resolves on poll 1, the operator's "fuller async simulator" ruling was not actually honored and this
      is a real, re-openable gap, not a nitpick.
- [ ] [AGENT] P0. **Reconcile every completed todo's evidence back to the epic's `## W23` section** in
      `/plans/epics/system_readiness_master.md` — commit SHAs, not just "done."
- [ ] [AGENT] P1. **Confirm the T4 plan's pointer todo (Section F of the parent plan) actually landed** and points
      at the right file.
- [ ] [AGENT] P1. **Run the standard 6-step archival ritual** on
      `/plans/active/w23_pod_collateral_delegation_transfer_rail_2026_08_22.md` once every parent-plan todo is
      genuinely `- [x]` and this finalize plan's own todos are done — per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.
