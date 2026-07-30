---
doc_type: plan
title: Deployment registry Firestore migration overview — finalize (na-eligibility-audit reclassification twin)
summary: >-
  Gated closeout for deployment_registry_firestore_migration_2026_07_14.md, reclassified `assigned_vm: NA -> planning`
  by the na-eligibility-audit infra-tranche run 2026-07-30 (retroactive-reclassification shape, codex
  ao-dispatch-batch-naming-and-conflict-check.md §1(b)). Once the source doc's single self-service unblock todo (deploy
  with the dual-write flag on, verify the 4 published GO/NO-GO criteria) is done, confirms the dual-write soak
  precondition that `deployment_registry_firestore_p3_cutover_2026_07_14.md` is blocked on is genuinely cleared before
  that sibling phase-plan is touched.
status: complete
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-api, unified-trading-library, deployment-ui, deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/deployment_registry_firestore_migration_2026_07_14.md,
    /plans/active/deployment_registry_firestore_p3_cutover_2026_07_14.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
sequential: true
drift_direction: advance-code
depends_on: [deployment_registry_firestore_migration_2026_07_14]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /na-eligibility-audit infra tranche, dispatch agt-30721a, 2026-07-30 — retroactive reclassification of an
  already-owned assigned_vm:NA doc. Conflict-check note: `deployment_registry_firestore_p3_cutover_2026_07_14.md` (the
  next phase in this same chain) independently verdicted KEEP-NA valid in the same audit run — it carries its own
  explicit 2026-07-14 operator HALT gated on this exact todo's dual-write-soak precondition, which is not yet met. Do
  NOT also reclassify P3 off the back of this flip; P3's own GO/NO-GO checklist must clear first.
---

# Deployment registry Firestore migration overview — finalize

> **🟢 ARCHIVED 2026-07-30** — status=complete, its one todo done (evidence below), no lock. The **parent overview doc
> (`/plans/active/deployment_registry_firestore_migration_2026_07_14.md`) stays `active` — intentionally NOT archived
> alongside this finalize plan.** `deployment_registry_firestore_p5_verify_2026_07_14.md` (todo 5 + its 2026-07-14
> Progress Log) explicitly reserves "mark the master complete + run the archival ritual on the whole phase-chain" as its
> OWN gated action, blocked on Phase 3 finishing — which this todo's own re-verification confirms is still genuinely
> blocked. A future dispatch (P5's final todo, once P3 unblocks) is the correct place that archival happens.

> **Machine-gated on `deployment_registry_firestore_migration_2026_07_14.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue this plan's todo until the parent's 1 todo is done.

## Todos

- [x] ✅ [DOC] P2. **DONE 2026-07-30 (slot 7).** (1) **Independently re-verified GO/NO-GO criterion 1 with fresh live
      data** (did not trust the parent doc's snapshot): Firestore REST API, full pagination, prod `deployments`
      collection = 193 docs (190 `status=failed`, 3 `status=completed`, **0 `status=running`**); cross-referenced every
      doc's `vm_name` against 50 currently-`RUNNING` GCE instances
      (`gcloud compute instances list     --filter=status=RUNNING`, project `central-element-323112`) — **zero
      overlap**. Criterion 1 genuinely fails (same root cause as
      `/plans/active/issues/deployment_registry_dualwrite_flag_not_propagated_to_vm_launchers_2026_07_30.md`: the Cloud
      Run dual-write flag only governs deployment-api's own process, not the VM-side heartbeat writer); criteria 2+4
      stay untestable as a direct consequence; criterion 3's read-path plumbing was already verified passing by slot-12
      (not re-verified — a code-path check, not a live-fleet-state check). (2) Added a Progress Log entry to
      `deployment_registry_firestore_p3_cutover_2026_07_14.md` explicitly re-confirming the HALT precondition is NOT met
      — the GCS-write-drop / snapshot-then-delete todos stay correctly BLOCKED; did not touch its `assigned_vm`. (3)
      **Grepped the parent's remaining `- [ ]` items: zero** — but did NOT run the archival ritual on the parent,
      because a literal zero-checkbox count is not the same as "the parent is done": reading
      `deployment_registry_firestore_p5_verify_2026_07_14.md` (its own todo 5 + 2026-07-14 Progress Log) shows P5
      explicitly RESERVES "mark the master `deployment_registry_firestore_migration_2026_07_14.md` complete — run the
      archival ritual on the whole phase-chain" as its OWN gated action, blocked on P3 finishing ("P5 stays
      `status: draft` until P3 unblocks"). P3 is still genuinely blocked (this todo's own re-verification above), so
      archiving the parent now would preempt and contradict P5's own documented intent — leaving it `active` is correct,
      not a shortfall. This finalize plan's own todo is done regardless of the parent's archival timing (same pattern as
      the archived `deployment_registry_firestore_p0_unblock_2026_07_14_finalize_2026_07_27.md` precedent); leaving this
      finalize plan itself in `active/` rather than archiving it standalone, since the observed corpus pattern
      (`git log` on that precedent) is finalize-plans archiving ALONGSIDE their parent, not independently ahead of it —
      a future dispatch (P5's own final todo, or a hygiene sweep) sweeps both together once the phase-chain genuinely
      completes.
