---
doc_type: issue
title:
  defi_dex_pool_symbol_fix_backfill_purge_finalize-001 dispatched despite upstream plan's 5 todos all still open —
  gate_on_depends prereqs.completed_tasks empty in live backlog.yaml
summary: >-
  Slot 3 was dispatched `defi_dex_pool_symbol_fix_backfill_purge_finalize-001` (task from
  `plans/active/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md`, whose header states it is
  "Machine-gated on `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`" via `depends_on` + `gate_on_depends: true",
  and should not queue until all 5 tasks of that upstream plan are done). Verified against the upstream plan file
  directly: all 5 todos are still `- [ ]` (none checked, single-commit history, no Progress Log entries) — so the
  finalize task's own done_definition ("once the query-fix + live-test + backfill + purge todos are all `done`, flip
  this issue doc's `status: open` -> `status: resolved`...") cannot honestly be executed. Cross-checked the live
  `agent-orchestrator/data/config/backlog.yaml`: the upstream plan's 5 todos ARE ingested as real backlog tasks
  (`defi_dex_pool_symbol_fix_backfill_purge-001` .. `-005`, none `done`), so this is NOT the documented "upstream never
  ingested" edge case (`gate_on_depends_noop_on_local_only_upstream_2026_07_21.md`) that `_wire_gate_on_depends_prereqs`
  already has a named-prerequisite fallback for. Yet `defi_dex_pool_symbol_fix_backfill_purge_finalize-001`'s own entry
  shows `prereqs.completed_tasks: []` (only `-002`, the archive todo, carries a prereq — and that's the in-plan
  `sequential: true` chain to `-001`, not the cross-plan gate). A static read of `_wire_gate_on_depends_prereqs` /
  `_parse_frontmatter_depends_on` / `_parse_frontmatter_gate_on_depends` did not surface an obvious parsing bug
  (frontmatter looks well-formed: `depends_on: [defi_dex_pool_symbol_fix_backfill_purge_2026_07_25]` + `gate_on_depends:
  true`, matching the documented inline-list + stem-matching contract) — so root cause is UNCONFIRMED: either a real
  wiring defect on this specific shape, or a regen-tick timing/staleness gap between task creation and gate-wiring, or a
  live SQLite `state.db` vs on-disk `backlog.yaml` divergence I could not check from a worker slot. Filing as a defect
  rather than silently declining, per the "big finding -> notify operator + issue doc" triage rule — a `gate_on_depends`
  plan that doesn't actually gate is a repeat of the `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` bug class (a
  documented-but-not-actually-enforced gate), and every `<plan>_finalize_*.md` plan authored per the
  operator-ruling-2026-07-24 convention relies on this exact mechanism to avoid prematurely flipping status/evidence
  claims.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [backlog, regen, gate_on_depends, prereqs, dispatch-defect, orchestrator-bug, finalize-plan]
related:
  [
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md,
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /plans/archive/issues/backlog_regen_drops_handtuned_prereqs_2026_07_12.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: advance-code
source: slot-3-observed-2026-07-25
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# gate_on_depends premature dispatch — finalize plan task queued with empty completed_tasks

## Evidence

- `plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` (upstream): `git log` shows a single commit
  (`781b98eea`), all 5 todos still `- [ ]`, no Progress Log section. Frontmatter: `assigned_vm: planning`,
  `sequential: true`.
- `plans/active/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md` (downstream/gated) frontmatter:
  `depends_on: [defi_dex_pool_symbol_fix_backfill_purge_2026_07_25]`, `gate_on_depends: true`, `sequential: true`.
  Header prose explicitly states this should machine-hold both todos until the upstream's 5 tasks are done.
- Live `agent-orchestrator/data/config/backlog.yaml`:
  - Upstream tasks exist and are live: `defi_dex_pool_symbol_fix_backfill_purge-001` through `-005`, sequentially
    chained (`prereqs.completed_tasks` pointing to the prior task in the chain), none carrying a `done_sha`.
  - Downstream task `defi_dex_pool_symbol_fix_backfill_purge_finalize-001`:
    `prereqs: {completed_tasks: [], prerequisites: []}` — empty. Only
    `defi_dex_pool_symbol_fix_backfill_purge_finalize-002` (the archive todo) has a `completed_tasks` entry, and it's
    just `[defi_dex_pool_symbol_fix_backfill_purge_finalize-001]` — the in-plan `sequential: true` predecessor link, not
    the cross-plan gate.
  - This task was then dispatched to slot 3 via `/boot`
    (`dispatch_reason: "tier=1 priority=50 plan_order=0 — highest-rank queued task with prereqs met and no collision"`)
    — confirming the empty `prereqs.completed_tasks` is what let it through, since there is genuinely nothing to gate
    on.

## Code read (inconclusive on root cause)

Read `server/regen_backlog_from_plan.py`'s `_parse_frontmatter_depends_on`, `_parse_frontmatter_gate_on_depends`, and
`_wire_gate_on_depends_prereqs` end to end. The frontmatter shape here (`depends_on: [bare-stem]` inline list,
`gate_on_depends: true`) matches what the regexes/parsers expect, and `_wire_gate_on_depends_prereqs`'s logic (match
`_stem(t.plan_ref)` against `_stem(dep)` on both sides, extend `completed_tasks` with all upstream ids) reads correct
for this case — the upstream plan is NOT in the ambiguous "zero ingested tasks" bucket
(`gate_on_depends_noop_on_local_only_upstream_2026_07_21.md`'s fix), since all 5 upstream ids ARE present in
`backlog.tasks` at regen time. Could not confirm root cause without either (a) log access to a `regen()` tick's actual
behavior on this plan pair, or (b) SQLite `state.db` access to check whether the live dispatch source diverges from the
on-disk YAML I read. Leaving this open rather than guessing.

## Impact

- Any `<plan>_finalize_*.md` plan authored per the `task_template.md` operator-ruling-2026-07-24 convention (companion
  finalize plan, `depends_on` + `gate_on_depends: true`) may dispatch its reconciliation/archival todos BEFORE the
  upstream plan is actually done, producing false "resolved"/"shipped" claims in the referenced docs if a worker doesn't
  independently re-verify (as this one did) before acting.
- This specific instance: slot 3 declined to execute the reconciliation todo since its premise (upstream done) is false.
  No incorrect status flip happened. Filing this instead of silently re-queuing so the pattern gets investigated rather
  than rediscovered per-instance by future workers on this or other `_finalize_` plans.

## Todos

- [ ] [SCRIPT] P0. Reproduce directly against this exact plan pair (or a throwaway sandbox pair with the identical
      frontmatter shape): trigger `POST /api/backlog/regen`, then re-read `backlog.yaml` for
      `defi_dex_pool_symbol_fix_backfill_purge_finalize-001`'s `prereqs.completed_tasks` — confirm whether a regen tick
      actually wires it now (this issue doc's evidence may reflect a since-passed timing gap) or whether it's durably
      empty. (repo: agent-orchestrator)
- [ ] [SCRIPT] P1. If durably empty: isolate why `_wire_gate_on_depends_prereqs` doesn't fire for this shape — check
      whether `state.db` (live dispatch source) actually reflects `backlog.yaml`'s `prereqs.completed_tasks` or whether
      there's a sync gap between the two stores that only shows up post-dispatch. Fix the wiring defect or the sync gap,
      whichever is the actual root cause. (repo: agent-orchestrator)
- [ ] [SCRIPT] P2. Add a regression test mirroring `test_regen_priority_override_survives_regen_tick`'s pattern (from
      `backlog_regen_drops_handtuned_prereqs_2026_07_12.md`): author two throwaway plans with a real `depends_on` +
      `gate_on_depends: true` pair where the upstream has several genuinely-open, ingested todos, run `regen()`, and
      assert the downstream task's `prereqs.completed_tasks` actually contains every upstream id. This exact shape
      (non-empty, non-local-only upstream) does not appear to be covered by the existing
      `gate_on_depends_noop_on_local_only_upstream_2026_07_21.md`-driven test suite. (repo: agent-orchestrator)
- [ ] [DATA] P2. Once root-caused, re-verify `defi_dex_pool_symbol_fix_backfill_purge_finalize-001`/`-002` are correctly
      held (empty `prereqs.completed_tasks` was the direct cause of this premature dispatch) — either the code fix above
      self-heals it on the next regen tick, or apply the RULES.md §4 park-a-task recipe (`priority: 999` +
      `priority_override: true` + a false named prerequisite) as an interim mitigation if the fix lands later than the
      next dispatch cycle. (repo: agent-orchestrator)
