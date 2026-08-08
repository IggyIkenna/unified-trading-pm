---
doc_type: plan
title: Multi-agent slot collision + safe-doc-push hardening — finalize
summary: >-
  Gated closeout for `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md` — machine-held via
  `depends_on` + `gate_on_depends: true` until all 4 of that doc's remaining todos (rename-corruption fix, the
  now-unblocked `.agent-claim` heartbeat + session-start collision warning, and the codex/CLAUDE.md fold-in) are done.
  Verifies the live heartbeat + warning mechanism actually reduces collision frequency before archiving.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao, multi-agent-safety, git, close-out, archival, plan-hygiene]
related:
  [
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
    /plans/epics/agent_operating_framework_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# Multi-agent slot collision + safe-doc-push hardening — finalize

> **Machine-gated on `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md`** (`depends_on`
>
> - `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 4 of the parent doc's remaining
>   todos are `done`.

## Todos

- [ ] [REVIEW] P2. **Verify the rename-corruption fix against a real archival + forced-retry simulation.** Confirm the
      parent doc's own done-when: an archival `git mv` + a forced retry (simulate a concurrent push between commit and
      push) yields a commit whose `git ls-tree -r HEAD` shows the doc at exactly ONE path, not both. **Done when**:
      independently re-run, not just the shipping worker's own claim trusted. Repo: unified-trading-pm.
- [ ] [REVIEW] P2. **Confirm the live `.agent-claim` heartbeat + session-start collision warning actually reduce
      collision frequency, not just that the code shipped.** Watch for at least one real multi-session collision after
      deploy and confirm the warning fired (WARN, not refuse, per the operator's 2026-08-08 ruling). **Done when**: a
      live-observed warning event is cited, or a stated reason none has occurred yet (low collision rate since deploy is
      itself informative, not a gap).
- [ ] [DOCS] P2. **Archive the parent doc per the 6-step ritual, and only then.** Confirm zero open `- [ ]` todos
      remain; add the archival banner + set `status: complete`; grep the corpus for
      `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01` and repoint every referrer (including
      `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`, which explicitly defers its own mechanism
      build to this doc); clear any lock if set. Then physically move the parent doc under `plans/archive/2026_08/`.
      **Done when**: `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard,
      `check_reference_paths.py` shows no NEW dangling reference above its baseline, and
      `regenerate_active_plan_inventory.py` reports 0 orphans for this doc. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/05-infrastructure/per-tab-worktrees.md` · `plans/PLAN_FORMAT.md` · `plans/active/task_template.md` §4
(finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually dispatching
  via `depends_on` + `gate_on_depends: true` until the parent doc's 4 remaining todos are done.
