---
doc_type: plan
title: AO consolidated close-out — finalize (na-eligibility-audit reclassification twin)
summary: >-
  Gated closeout for ao_consolidated_closeout_2026_07_25.md, reclassified `assigned_vm: NA -> planning` by the
  na-eligibility-audit infra-tranche run 2026-07-30 (retroactive-reclassification shape, codex
  ao-dispatch-batch-naming-and-conflict-check.md §1(b) — name unchanged, bolt-on finalize twin). Once the source doc's 2
  todos (liveness-kick host-load-awareness, soft-kick-to-hard-kill escalation) are done, verifies the fix against its
  own stated regression-test criteria and checks whether the source doc is now itself an archival candidate.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, reclassification, na-audit]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: infra
sequential: true
drift_direction: advance-code
depends_on: [ao_consolidated_closeout_2026_07_25]
gate_on_depends: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  /na-eligibility-audit infra tranche, dispatch agt-30721a, 2026-07-30 — retroactive reclassification of an
  already-owned assigned_vm:NA doc per the skill's Phase 2/3 (conflict-check cleared: the 2 todos were added 2026-07-29,
  after ao_satellite_ao_dispatch_batch1_2026_07_26.md was drafted, so no active planning doc claims this content).
---

# AO consolidated close-out — finalize

> **Machine-gated on `ao_consolidated_closeout_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue this plan's todo until the parent's 2 todos are done.

## Todos

- [ ] [DOC] P2. **Verify the parent's 2 todos against their own stated regression-test criteria, then check archival
      eligibility.** Once `ao_consolidated_closeout_2026_07_25.md`'s liveness-kick-host-load-aware and
      soft-kick-to-hard-kill-escalation todos are `[x]`: (1) re-verify each cited commit sha actually lands the
      regression test named in the todo's own "Done when" text — do not trust the parent doc's own copy of the evidence
      line. (2) Grep the parent doc's remaining `- [ ]` items; if zero remain, it is an archival candidate — run the
      standard 6-step archival ritual (codex `plan-completion-and-archival-discipline.md`), not just a checkbox flip —
      this doc is `ag_closeout_audit_rollout_2026_07_25.md`'s own tracked "Finish applying" item, so also update that
      tracker's reference once this closes. If the parent still carries genuine judgment-call items by then, leave it
      `status: active`. (3) Run the standard 6-step archival ritual on THIS finalize plan + its parent once both are
      done. **Done when**: both todos' commits are verified against their stated done-when, the parent's archival
      eligibility is explicitly checked (archived if zero open todos remain, left active with a stated reason
      otherwise), and this finalize plan + its parent are archived if applicable.
