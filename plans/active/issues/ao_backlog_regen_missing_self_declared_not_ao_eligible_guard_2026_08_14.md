---
doc_type: issue
title: "regen_backlog_from_plan.py dispatches checkboxes that self-declare 'not AO-eligible' — 3rd confirmed recurrence"
summary: >-
  A todo in `strategy_archetype_latency_deployment_profile_execution_2026_08_10.md` self-labels "not AO-eligible" in its
  own text, but `regen_backlog_from_plan.py` still derives a dispatchable backlog task from it. Three independent slots
  (7, 21, 26) have now each burned a dispatch cycle reaching the same "no operator ruling yet" conclusion.
  `_is_non_dispatchable()`'s `_PERMANENT_NON_DISPATCHABLE_RE` already handles the analogous `DEFERRED-BY-DESIGN` case
  but has no pattern for self-declared judgment-call/operator-ruling phrasing — proposes extending it.
created: 2026-08-14
author: backend_engineer (slot 26)
source:
  [
    /plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
parent_epic: orchestrator_master
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md,
  ]
resolved_by:
locked_by:
priority: P2
tags: [dispatch-scope, backlog-regen, guard-gap, recurring]
---

# regen_backlog_from_plan.py dispatches checkboxes that self-declare "not AO-eligible"

## What I found

`plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md`'s todo carries this exact text:

```
- [ ] [DOC] P2. **Residual gaps (2)(3)(4) — still open, each a judgment call / operator ruling, not AO-eligible.** (2) ...
```

`regen_backlog_from_plan.py` derived a dispatchable backlog task from it anyway
(`strategy_archetype_latency_deployment_profile_execution-73c2e13d68fc`), and the dispatcher has now handed it to
**three independent slots**, each burning a full dispatch cycle re-verifying the same already-known "no operator ruling
has landed yet" conclusion:

- slot 7, 2026-08-12 — GATED, no code action, recommended a guard fix.
- slot 21, 2026-08-13 — re-dispatched the SAME checkbox, independently re-confirmed the same verdict, re-recommended the
  guard fix "get prioritized ahead of a third recurrence."
- slot 26, 2026-08-14 (this session) — the third recurrence slot 21 predicted. Re-verified live state again
  (`isolation_policies.strategy-service.default` still `shared`, `vol-market-making.md` still `min_sla_tier: premium` vs
  the `distributed` mapping, no commits to `RUNTIME_TOPOLOGY_DECISIONS.md`/`runtime-topology.yaml` since `ab157b54a1`) —
  same conclusion, same GATED skip.

Root cause: `_is_non_dispatchable()` in `agent-orchestrator/server/regen_backlog_from_plan.py` (around line 1397)
already has the exact mechanism for this — `_PERMANENT_NON_DISPATCHABLE_RE` currently matches the standing
`DEFERRED`-`BY`-`DESIGN` qualifier and the stretch/optional markers, but has no pattern for a todo whose own text
asserts it needs a **judgment call / operator ruling**, e.g. "not AO-eligible", "not-AO-eligible", "needs an operator
ruling", "requires operator judgment".

## Why it matters

Every recurrence dispatches a fresh worker session (real token/time cost) to reach a conclusion the plan's own Progress
Log already states twice. It also pollutes the plan's Progress Log with near-duplicate re-confirmation entries instead
of forward progress, and will keep firing on every future regen tick until either an operator ruling lands (resolving
the underlying (2)(3)(4) judgment calls — separate, real work, not this issue's scope) or the guard is fixed.

## Recommended decision

Extend `_PERMANENT_NON_DISPATCHABLE_RE` in `agent-orchestrator/server/regen_backlog_from_plan.py` to also match a todo
block that self-declares non-AO-eligibility — e.g. a case-insensitive pattern for `not[\s-]+AO[\s-]+eligible` /
`needs?\s+an?\s+operator\s+ruling` / `requires?\s+operator\s+judg?ment` — mirroring the existing standing
deferred-permanently-by-design marker's treatment (asserted as a CURRENT permanent-until-ruled state, no stale-mention
guard needed since a resolved judgment call would have its checkbox flipped `[x]`, not just its prose edited). Add a
unit test asserting this exact checkbox text (or a synthetic equivalent) is excluded from `_parse_open_todos`'s
dispatchable set.

## Todos

- [x] ✅ [SCRIPT] P2. In `agent-orchestrator/server/regen_backlog_from_plan.py`, extend `_PERMANENT_NON_DISPATCHABLE_RE`
      (~line 1389) with a pattern matching self-declared non-AO-eligibility phrasing ("not AO-eligible",
      "not-AO-eligible", "needs an operator ruling" — see the source todo in
      `/plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md`, "requires operator
      judgment") so `_is_non_dispatchable()` excludes these todos from the backlog the same way the existing
      permanent-marker case already is. Add a regression test in the corresponding test file covering this exact phrase.
      (repo: agent-orchestrator) — agent-orchestrator@5c3dfb58c8. Added
      `test_parse_skips_self_declared_not_ao_eligible_todos` covering all three phrasings; full QG green (3741 passed).
