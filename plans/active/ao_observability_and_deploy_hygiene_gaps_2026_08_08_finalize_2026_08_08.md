---
doc_type: plan
title: AO observability + deploy-hygiene gaps — finalize
summary: >-
  Gated closeout for `ao_observability_and_deploy_hygiene_gaps_2026_08_08.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 3 of that doc's remaining todos (fleet-cap raise, slot-30 re-run, stash-content
  verifier) are done. Reconciles evidence for the two bounded items, confirms the operator-gated cap raise landed with
  a live RAM re-measurement, then archives.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, observability, close-out, archival, plan-hygiene]
related:
  [
    /plans/active/issues/ao_observability_and_deploy_hygiene_gaps_2026_08_08.md,
    /plans/epics/orchestrator_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/ao_observability_and_deploy_hygiene_gaps_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [ao_observability_and_deploy_hygiene_gaps_2026_08_08]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# AO observability + deploy-hygiene gaps — finalize

> **Machine-gated on `ao_observability_and_deploy_hygiene_gaps_2026_08_08.md`** (`depends_on` + `gate_on_depends:
> true`) — the dispatcher will not queue any todo below until the parent doc's 3 remaining todos are `done`.

## Todos

- [ ] [REVIEW] P2. **Verify the stash-content-verifier's own claim before trusting it.** Confirm it genuinely reuses
      `worktree_clean_check.verify_all_wip_preserve_refs`'s SUPERSEDED/GONE/STILL-ORPHANED vocabulary (not a
      parallel re-implementation), and that every stash across the fleet-wide sweep (hundreds, 20 slots per the
      parent doc's own measurement) ends with a recorded verdict — landed, preserved to a `wip-preserve/` ref, or
      explicitly written off. **Done when**: a live re-count of `stash_pile_stale` events shows the backlog
      genuinely cleared or explicitly triaged, not just that a verifier script exists. Repo: unified-trading-pm.
- [ ] [REVIEW] P2. **Confirm the fleet-cap raise, once the operator rules, actually landed live.** The parent doc's
      `[OPERATOR] P1` item needs a VM-side `.env.local` edit + orchestrator restart (config is a cached singleton,
      no hot-reload) — verify the new `ORCHESTRATOR_FLEET_WORKER_CAP` value is live (not just committed/decided) and
      re-measure RAM across one full tick cycle per the parent doc's own stated watch-condition. **Done when**: a
      live post-raise RAM figure is recorded here, sourced from a fresh SSM read.
- [ ] [DOCS] P2. **Archive the parent doc per the 6-step ritual, and only then.** Confirm zero open `- [ ]` todos
      remain; add the archival banner + set `status: complete`; grep the corpus for
      `ao_observability_and_deploy_hygiene_gaps_2026_08_08` and repoint every referrer; clear any lock if set
      (confirm rather than assume). Then physically move the parent doc under `plans/archive/2026_08/`. **Done
      when**: `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard, `check_reference_paths.py`
      shows no NEW dangling reference above its baseline, and `regenerate_active_plan_inventory.py` reports 0
      orphans for this doc. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/11-project-management/cross-reference-path-convention.md` · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually
  dispatching via `depends_on` + `gate_on_depends: true` until the parent doc's 3 remaining todos are done.
