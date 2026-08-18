---
doc_type: issue
title: Finalize — AO pre-spawn dirty-state gate fired against a live interactive session
summary: >-
  Gated finalize for the retroactive RECLASSIFY of
  `ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17.md` (assigned_vm flipped NA ->
  planning in place, name unchanged, per the na-eligibility-audit reclassification pairing convention).
  Verifies the 3 landed fixes actually close the near-miss (a live re-trigger test, not just a code read), then
  archives the source doc.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, close-out, finalize, na-eligibility-audit, agent-orchestrator]
related:
  [
    /plans/active/issues/ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
parent_epic: orchestrator_master
created: "2026-08-17"
last_updated: "2026-08-17"
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
assigned_role: review
drift_direction: advance-code
depends_on: [ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/active/issues/ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17.md,
  ]
source: >-
  Mandatory finalize companion for a na-eligibility-audit retroactive RECLASSIFY, per the naming/pairing
  convention in `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 1(b).
---

# Finalize — AO pre-spawn dirty-state gate fired against a live interactive session

- [ ] [REVIEW] P1. Verify the 3 fixes actually resolve the near-miss, not just that the code changed: (1) the
      liveness-check fix — confirm it against a real or faithfully-simulated live interactive session with no
      recent commit, not just a unit test of the check in isolation; (2) `DirtyStateResolution.COMMIT_AND_PUSH` —
      confirm a genuinely-dead predecessor's orphan-wip commit actually reaches `origin` now, live; (3) the
      reset-to-origin scoping decision — confirm whatever was decided (keep, remove, or condition it) behaves as
      intended. Done-when: each of the 3 has a live-verification citation, not a code-read-only claim.
- [ ] [DOC] P2. Once every todo in the source doc is `[x]` and unlocked, run the standard 6-step archival ritual
      on `ao_pre_spawn_dirty_state_gate_targets_live_interactive_session_2026_08_17.md`, then archive this
      finalize doc alongside it.

## Progress Log

- **2026-08-17 (na_eligibility_auditor, dispatch agt-7e78e2, slot 28)**: drafted alongside the source doc's
  RECLASSIFY (whole-doc) per the mandatory finalize-plan rule.
