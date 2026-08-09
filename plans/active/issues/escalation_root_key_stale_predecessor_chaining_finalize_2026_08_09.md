---
doc_type: issue
title: Escalation root_key stale-predecessor chaining — finalize (reconcile + archive)
summary: >-
  Gated closeout for `escalation_root_key_stale_predecessor_chaining_2026_08_09.md` (`assigned_vm: planning` since the
  round9 cross-cutting sweep RECLASSIFY, 2026-08-09) — machine-held via `depends_on` + `gate_on_depends: true` until
  both of that doc's optional maintenance todos are done. Reconciles/archives the source doc once both todos land (or
  are explicitly declined as genuinely not worth doing, since both are marked "Optional").
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, satellite-docs, archival, escalation]
related:
  [
    /plans/active/issues/escalation_root_key_stale_predecessor_chaining_2026_08_09.md,
    /plans/active/issues/escalation_queue_reconciler_false_resolution_via_unrelated_qg_green_2026_08_09.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
depends_on: [escalation_root_key_stale_predecessor_chaining_2026_08_09]
gate_on_depends: true
source: >-
  round9 cross-cutting RECLASSIFY + satellite-extraction sweep, 2026-08-09 — per `task_template.md`'s
  finalize-plan-coverage rule (the source doc carries 2 open todos, past the single-todo carve-out that would otherwise
  exempt it).
assigned_role: backend_engineer
effort: low
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/escalation_root_key_stale_predecessor_chaining_2026_08_09.md,
    agent-orchestrator/server/escalation.py,
  ]
---

# Escalation root_key stale-predecessor chaining — finalize

> **Machine-gated on `escalation_root_key_stale_predecessor_chaining_2026_08_09.md`** (`depends_on` +
> `gate_on_depends: true`). `sequential: true` because archival (todo 2) must run after reconciliation (todo 1).

## Todos

- [ ] [REVIEW] P3. Reconcile the source doc's 2 optional todos: run the one-off
      `reconcile_stale_unresolved_escalations(window_hours=<large>, limit=<large>)` sweep to correct `agt-3dc7e9` and
      any other similarly-stale `unresolved` rows in the historical record (cosmetic — no future chaining risk
      post-fix), and expose `reescalations` on `GET /api/escalations/active` alongside `attempts`. Both are explicitly
      "Optional" in the source doc — if either is judged genuinely not worth doing (e.g. the historical-record cleanup
      has zero remaining stale rows once checked), record that determination with evidence rather than silently
      skipping. Flip each checkbox in the source doc citing the shipped commit(s)/evidence, or the explicit
      not-worth-doing determination. Done when: both todos in the source doc are `[x]` (either shipped or explicitly
      declined with evidence) and the doc reads 0 open todos.
- [ ] [DOC] P3. Archive `escalation_root_key_stale_predecessor_chaining_2026_08_09.md` via the standard 6-step ritual
      once todo 1 is done: archive banner → codex-alignment check → fix every corpus referrer → clear `locked_by`
      (confirm already empty). Done when: the doc is moved to `plans/archive/2026_08/`, every referrer resolves to the
      new path, and this finalize doc archives alongside it in the same commit.

## Progress Log

- **2026-08-09**: Finalize twin authored alongside the source doc's RECLASSIFY flip (round9 cross-cutting sweep) — the
  source doc carries 2 open todos, past `check_finalize_plan_coverage.py`'s single-open-todo carve-out, so a gated
  finalize plan is required per `task_template.md`.
