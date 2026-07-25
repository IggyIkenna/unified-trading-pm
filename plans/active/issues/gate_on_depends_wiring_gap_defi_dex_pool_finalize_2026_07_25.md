---
doc_type: issue
title:
  "gate_on_depends dispatched defi_dex_pool_symbol_fix_backfill_purge_finalize-001 despite its upstream plan having 0/5
  todos done — /api/backlog/<id>/blockers reports 'ready (no blockers)'"
summary: >-
  defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md declares `depends_on:
  [defi_dex_pool_symbol_fix_backfill_purge_2026_07_25]` + `gate_on_depends: true`, with the doc's own prose stating this
  should never dispatch until all 5 of the upstream plan's todos are done. Slot 5 was dispatched its first todo
  (`defi_dex_pool_symbol_fix_backfill_purge_finalize-001`, a reconciliation todo whose done_definition assumes the
  upstream fix/backfill/purge already shipped) while the upstream plan's todos are ALL still `- [ ]` (0/5 done; 2 are
  `[OPERATOR]` human-gated prod-bucket deletes that cannot complete without a human). Confirmed via `GET
  /api/backlog/defi_dex_pool_symbol_fix_backfill_purge_finalize-001/blockers` → `"ready (no blockers)"`, and via `GET
  /api/backlog` showing the 5 upstream task ids (`defi_dex_pool_symbol_fix_backfill_purge-001..005`) present with status
  `queued`/`blocked` (never `done`), so `_completed_task_satisfied` should read them as unsatisfied if wired. This is
  the SAME failure class as the two archived `gate_on_depends_noop_on_*_2026_07_21.md` issues, but neither of those root
  causes appears to apply here at face value (the upstream plan is `assigned_vm: planning`, not local-only/NA, and its 5
  tasks DO exist in the backlog — not pruned/empty) — so either a third distinct wiring gap exists, or the
  `_wire_gate_on_depends_prereqs` regen pass simply has not run since this finalize plan's tasks were ingested (e.g.
  `gated_plans` dict was built before the finalize plan existed, and reload/regen since then has been add-only and never
  re-wired it). Filed rather than fixed live — dispatch-logic changes have fleet-wide blast radius and the task at hand
  (todo 1 of the finalize plan itself) is genuinely not doable yet: doing it now would falsely claim resolved/shipped
  status on work that has not shipped. I filed a `/blocked` (BLK-0d30dec1) recommending we do NOT do the reconciliation
  work now, and am moving to other work rather than holding the slot.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch-logic, gate_on_depends, plan-discipline, recurring-bug, finalize-plan]
related:
  [
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md,
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /plans/archive/issues/gate_on_depends_noop_on_local_only_upstream_2026_07_21.md,
    /plans/archive/issues/gate_on_depends_noop_on_assigned_vm_na_upstream_2026_07_21.md,
  ]
created: "2026-07-25"
author: slot-5-worker
source: [defi_dex_pool_symbol_fix_backfill_purge_finalize-001]
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# What I found

Dispatched task `defi_dex_pool_symbol_fix_backfill_purge_finalize-001` (plan_ref
`plans/active/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md`) asks to reconcile 3 docs on the premise
that the parent plan's fix/backfill/purge work has landed. The parent plan
(`plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`) is `sequential: true` with 5 todos, ALL still
`- [ ]`:

```
- [ ] [OPERATOR] P2. Purge orphaned lst_rates _migrated_* markers ...
- [ ] [BACKEND]  P1. Fix the messari_basic subgraph query ...
- [ ] [DATA]     P1. Live-test whether 2022-era pool metadata is still indexed ...
- [ ] [BACKEND]  P1. Re-backfill dex_pool_state for curve/sushiswap/velodrome_v2/trader_joe_v2 ...
- [ ] [OPERATOR] P1. Purge the now-superseded old data ...
```

`git log` in `market-tick-data-service` shows no commit touching `dex_pools_handler.py`'s `messari_basic`/`_CURVE_QUERY`
adding `inputTokens` — the very first (BACKEND) todo hasn't shipped, let alone the sequential chain after it.

The finalize plan's own frontmatter/prose is explicit that it is gated:

```
depends_on: [defi_dex_pool_symbol_fix_backfill_purge_2026_07_25]
gate_on_depends: true
> Machine-gated ... the dispatcher will not queue either todo below until all 5 of that plan's tasks are done
```

Yet it dispatched. Live verification:

```
GET /api/backlog/defi_dex_pool_symbol_fix_backfill_purge_finalize-001/blockers
→ {"task_id":"...-001","explanation":"ready (no blockers)"}
```

`GET /api/backlog` shows the 5 upstream ids exist as real backlog rows (not pruned/absent):

```
defi_dex_pool_symbol_fix_backfill_purge-001  status=blocked   (OPERATOR purge)
defi_dex_pool_symbol_fix_backfill_purge-002  status=queued    (BACKEND query fix)
defi_dex_pool_symbol_fix_backfill_purge-003  status=queued    (DATA live-test)
defi_dex_pool_symbol_fix_backfill_purge-004  status=queued    (BACKEND backfill)
defi_dex_pool_symbol_fix_backfill_purge-005  status=blocked   (OPERATOR purge)
```

Per `dispatch.py::_completed_task_satisfied`, a `completed_tasks` prereq id with an existing non-`done` `TaskRow`
correctly reads as unsatisfied — so if these 5 ids had actually been wired into
`defi_dex_pool_symbol_fix_backfill_purge_finalize-001`'s `prereqs.completed_tasks`, the blockers endpoint would show a
`prereq task ... not done` reason, not `"ready (no blockers)"`. This means the wiring itself did not happen for this
plan pair — NOT that the wiring logic is unsound once applied.

# Why it matters

A gated finalize-plan todo dispatching before its gate holds risks a worker fabricating a "shipped"/"resolved" status on
docs that reference real production data-integrity work (subgraph query bug, backfill, prod-bucket purges) that
genuinely has not happened yet — a false-completion claim on exactly the kind of doc (`issues/...resolved`,
`defi_consolidated_closeout_2026_07_18.md` progress log) other agents and the operator trust as ground truth. This is
the third occurrence of `gate_on_depends` failing to hold (after the two archived 2026-07-21 incidents), each with a
seemingly different proximate cause — suggests the wiring pass may have a broader reliability gap (e.g. wiring happening
only once at plan-ingestion time and not re-applied on every regen tick once both plans coexist) rather than three
unrelated one-off bugs.

# Recommended decision

1. `backend_engineer`/`agent-orchestrator`: instrument or trace why `_wire_gate_on_depends_prereqs` did not attach
   `defi_dex_pool_symbol_fix_backfill_purge-00{1..5}` to `defi_dex_pool_symbol_fix_backfill_purge_finalize-001`'s
   `prereqs.completed_tasks` — check whether `gated_plans` (built from `_parse_frontmatter_gate_on_depends` scanning
   `plans/active/*.md`) actually included the finalize plan's filename on the regen tick(s) since it was authored, and
   whether the wiring pass re-runs on every regen or only once at first-ingestion (if the latter, a plan
   authored+ingested in the same/adjacent tick as its own gate declaration could race past the wiring pass before its
   upstream ids exist in `file_to_ids`).
2. Once root-caused, add a regression test asserting a `gate_on_depends: true` plan's tasks carry the upstream's task
   ids in `prereqs.completed_tasks` immediately after a regen tick that ingests both plans together (this exact
   same-tick-ingestion shape, not just the already-covered empty-upstream cases).
3. Until fixed: `defi_dex_pool_symbol_fix_backfill_purge_finalize-001` should NOT be worked (filed `/blocked`
   BLK-0d30dec1, recommendation A: skip and let it re-dispatch once the parent plan is genuinely done). Todo 2 (`-002`,
   the archival todo) is separately unsafe to run early since archival explicitly requires todo 1 to be correct first
   (`sequential: true`).
