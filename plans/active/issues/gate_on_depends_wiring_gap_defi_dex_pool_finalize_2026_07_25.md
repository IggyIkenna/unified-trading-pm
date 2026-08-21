---
doc_type: issue
title:
  "gate_on_depends dispatched defi_dex_pool_symbol_fix_backfill_purge_finalize-001 despite its upstream plan having 0/5
  todos done — /api/backlog/<id>/blockers reports 'ready (no blockers)'"
summary: >-
  /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md declares `depends_on:
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
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch-logic, gate_on_depends, plan-discipline, recurring-bug, finalize-plan]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-07-25"
author: unknown
source:
  [
    defi_dex_pool_symbol_fix_backfill_purge_finalize-001,
    prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize-001,
  ]
parent_epic: agent_operating_framework_master
priority: P0
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md,
    /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /plans/archive/issues/gate_on_depends_noop_on_local_only_upstream_2026_07_21.md,
    /plans/archive/issues/gate_on_depends_noop_on_assigned_vm_na_upstream_2026_07_21.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
  ]
depends_on: []
---

# What I found

Dispatched task `defi_dex_pool_symbol_fix_backfill_purge_finalize-001` (plan_ref
`/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md`) asks to reconcile 3 docs on the
premise that the parent plan's fix/backfill/purge work has landed. The parent plan
(`/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`) is `sequential: true` with 5 todos, ALL
still `- [ ]`:

```
- [ ] [OPERATOR] P2. Purge orphaned lst_rates _migrated_* markers ...
- [ ] [BACKEND] P1. Fix the messari_basic subgraph query ...
- [ ] [DATA] P1. Live-test whether 2022-era pool metadata is still indexed ...
- [ ] [BACKEND] P1. Re-backfill dex_pool_state for curve/sushiswap/velodrome_v2/trader_joe_v2 ...
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

## 2026-07-25 recurrence note

Bounced from slot 5 to slot 4 within ~2 heartbeat ticks — `/skip-current-task` does NOT prevent immediate re-dispatch to
another idle slot (only removes the offending slot from consideration for that one task instance). Parent plan
`/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` was still 0/5 todos done at re-dispatch
time (verified again: no landing commit for the `messari_basic` query fix in `market-tick-data-service`). Skipped again
with the same reasoning; main (`agt-52bb99`) confirmed the ruling live and directed this note rather than a
re-investigation. Root cause (item 1 above) is still unfixed as of this note.

## 2026-07-25 recurrence note (slot 6, third bounce)

Bounced again — slot 6 was dispatched `defi_dex_pool_symbol_fix_backfill_purge_finalize-001` fresh (no prior task
history in this session). Independently re-verified before finding this doc: read the parent plan
(`/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`), confirmed all 5 todos still `- [ ]`;
read `market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py` directly and confirmed
`_CURVE_QUERY`/`_CURVE_QUERY_FILTERED` (the query used by `curve`/`sushiswap`/`velodrome_v2`/`trader_joe_v2` via the
`messari_basic` protocol-table entry) still have no `inputTokens` field, and the protocol table still maps all four to
`_parse_curve`, not `_parse_messari_dex` — the BACKEND query-fix todo has not shipped, confirming the checkbox state is
accurate, not stale. Declining to flip any of the 3 referencing docs per this issue's existing recommendation A.
Skipping this task rather than re-filing a duplicate `/blocked` (BLK-0d30dec1 already covers the question and already
has main's answer). Root cause (item 1 above) is still unfixed as of this note.

## 2026-07-25 recurrence note (slot 3, sixth bounce)

Bounced again — slot 3 was dispatched `defi_dex_pool_symbol_fix_backfill_purge_finalize-001` fresh. Independently
re-verified before finding this doc (filed then deleted a duplicate issue doc with the same evidence + a static code
read of `_wire_gate_on_depends_prereqs`/`_parse_frontmatter_depends_on`/`_parse_frontmatter_gate_on_depends` — found no
obvious parsing bug on this frontmatter shape, consistent with this doc's "wiring simply didn't happen" conclusion
rather than a parser defect). Confirmed via live `agent-orchestrator/data/config/backlog.yaml`: upstream tasks
`defi_dex_pool_symbol_fix_backfill_purge-001..005` still exist, none carry a `done_sha`;
`defi_dex_pool_symbol_fix_backfill_purge_finalize-001`'s `prereqs.completed_tasks` is still `[]`. Main (`agt-52bb99`)
confirmed the standing ruling live (BLK-0d30dec1, Option A) before I acted, directing this note instead of a fresh
`/blocked`. Declining to author any reconciliation content; skipping this task. Root cause (item 1 above) is still
unfixed as of this note.

## 2026-07-25 park recipe re-applied (slot 8)

Per main (`agt-52bb99`)'s live directive after this bounce, re-applied the RULES.md §4 park recipe by hand on the live
`agent-orchestrator/data/config/backlog.yaml` `defi_dex_pool_symbol_fix_backfill_purge_finalize-001` entry (the prior
park had been silently wiped by an intervening `POST /api/backlog/regen` tick, per main: "the park override got wiped by
a backlog re-derivation tick (done 106->83)"). Set `priority: 999` + `priority_override: true` (was `50` / `false`), and
populated `prereqs.completed_tasks` with the 5 real upstream task ids
(`defi_dex_pool_symbol_fix_backfill_purge-00{1..5}`) instead of a synthetic named condition — `completed_tasks` is the
exact mechanism `dispatch.py::_completed_task_satisfied` already implements correctly (per this doc's own earlier
analysis), so this is effectively hand-applying the wiring `_wire_gate_on_depends_prereqs` should have done
automatically, not a workaround. Verified via `GET /api/backlog/.../blockers`: now correctly reports "prereq task ...
not done" for all 5 ids (was "ready (no blockers)"). Re-verified the gate SURVIVES both `POST /api/backlog/reload` and a
forced `POST /api/backlog/regen` (598 plans rescanned, 0 new tasks/prereqs) — the hand-set `completed_tasks` +
`priority_override` were NOT reverted. Root cause (why `_wire_gate_on_depends_prereqs` didn't wire this automatically at
ingestion) is still open — item 1's investigation remains the durable fix; this hand-park is a stopgap that stops the
8-slot bounce cycle until that lands and the parent plan's todos genuinely complete (at which point this hand-set
`completed_tasks` list becomes redundant with, not a blocker to, the real gate).

## 2026-07-25 recurrence note (slot 8, seventh bounce)

Bounced again — slot 8 was dispatched `defi_dex_pool_symbol_fix_backfill_purge_finalize-001` fresh (booted with
`slot_role: review`). Independently re-verified from scratch, at the code level rather than relying on the parent plan's
checkbox state alone: read `market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py`
directly and confirmed `_CURVE_QUERY`/`_CURVE_QUERY_FILTERED` (lines 357-390) still have no `inputTokens` field, while
`_MESSARI_DEX_QUERY`/`_MESSARI_DEX_QUERY_FILTERED` (lines 393-434+) do carry `inputTokens { symbol }` + `fees {...}` --
but that pair was already wired pre-existing to `aerodrome_v3`/`camelot_v3`/`pancakeswap_v3`/`sushiswap_v3`, not to the
4 venues this todo targets. Read `_dex_pools_subgraph.py`'s protocol table (lines 238-284): the `messari_basic` entry
that `curve`/`sushiswap`/`velodrome_v2`/`trader_joe_v2` all route through (line 276-283) still resolves to
`_h._CURVE_QUERY(_FILTERED)` + `self._parse_curve` (lines 238-241), NOT `_MESSARI_DEX_QUERY` + `_parse_messari_dex` --
confirming the query-fix todo (parent plan todo 2, `[BACKEND] P1`) genuinely has not shipped; `git log` on the handler
file shows only unrelated commits (GMX removal, catalogue-gate classification, freshness-cache scoping, uniswap_v2/v4
wiring) since this plan was authored. Verified live via `agent-orchestrator/data/config/backlog.yaml`-equivalent
(`GET /api/backlog`): `defi_dex_pool_symbol_fix_backfill_purge-001..005` are still `queued`/`blocked`, none `done`.
Declining to author any reconciliation content on the false premise that the fix/backfill/purge landed. Per the standing
ruling (BLK-0d30dec1, Option A), skipping this task rather than re-filing a duplicate `/blocked`. Root cause (item 1
above) is still unfixed as of this note -- this is now the SEVENTH slot to bounce off this same wiring gap (5, 4, 6, 3,
and now 8, per the notes above), which itself is evidence the root-cause fix (item 1's regen-tick / re-wiring
investigation) should be prioritized over further individual bounces re-verifying the same fact.

## 2026-07-26 recurrence — SECOND distinct plan pair confirms this is a general wiring gap, not a defi_dex_pool one-off

Slot 4 was freshly dispatched `prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize-001` (plan_ref
`plans/active/prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize.md`) — an ENTIRELY DIFFERENT plan pair from
the defi_dex_pool one this doc was originally filed against. That finalize plan declares
`depends_on: [prediction_satellite_ao_dispatch_batch3_2026_07_26]` + `gate_on_depends: true`, with prose stating the
dispatcher "will not queue any todo below until both tasks in that plan are `done`." Verified live:

```
GET /api/backlog/prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize-001/blockers
→ {"task_id":"...-001","explanation":"ready (no blockers)"}

GET /api/backlog (filtered):
prediction_satellite_ao_dispatch_batch3-001            dispatched   (not done)
prediction_satellite_ao_dispatch_batch3-002            blocked      (OPERATOR-gated, not done)
prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize-001   dispatched
```

Read the parent plan (`prediction_satellite_ao_dispatch_batch3_2026_07_26.md`) directly: both its todos are still
`- [ ]` (unchecked) in the doc source, consistent with the API's non-`done` statuses. The finalize todo's own
done_definition ("flip the corresponding checkbox... citing the batch-3 commit(s) that shipped it") presupposes the
parent's Kalshi-drift-triage + prediction-manifest-residual work has already shipped — it has not. Doing the
reconciliation now would be a false-completion claim on data-integrity/closeout docs, the exact failure mode this issue
predicts.

This is now confirmed to be a GENERAL `gate_on_depends` wiring gap affecting at least two unrelated plan-pairs
(defi_dex_pool_symbol_fix_backfill_purge + prediction_satellite_ao_dispatch_batch3), not something specific to the
defi_dex_pool plan's shape — strengthens the case for prioritizing root-cause item 1 (trace
`_wire_gate_on_depends_prereqs` across regen ticks) over continuing to patch/park each affected plan pair individually.
Applying the same disposition as every defi_dex_pool bounce above: declining to author any reconciliation content,
skipping this task rather than `/blocked`-ing on an already-answered question. Recommend the same hand-park stopgap
(populate `prereqs.completed_tasks` with `prediction_satellite_ao_dispatch_batch3-00{1,2}` + `priority_override: true`)
be applied to this task pair too if it starts bouncing across multiple slots the way the defi_dex_pool pair did.

## 2026-07-30 recurrence note (slot 12, second bounce on cross_cutting_satellite_ao_dispatch_batch1)

Freshly dispatched `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize-001` on slot 12
(`dispatch_reason: "resume"`, `already_in_progress: true`) — same task_id, same plan pair covered by the "SIXTH distinct
plan pair" note below (slot 7). Independently re-verified via a fresh grep of both gating docs before declining:
`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` still exactly 9/19 done (10 `- [ ]`), `...batch1b...` still
exactly 6/18 done (12 `- [ ]`) — byte-identical counts to slot 7's note, confirming no drift and no stale evidence.
Declining to author any reconciliation content on the false premise that all 31 todos shipped; skipping via
`POST /skip-current-task` (reason: GATED — upstream gate genuinely unmet) rather than filing a duplicate `/blocked`.

## 2026-07-30 recurrence — SIXTH distinct plan pair (cross_cutting_satellite_ao_dispatch_batch1, dual-gate, worst gap yet)

Slot 7 was dispatched `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize-001`
(`depends_on: [cross_cutting_satellite_ao_dispatch_batch1_2026_07_26, cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26]`,
`gate_on_depends: true`, requires all 31 todos across BOTH gating plans done) while the two parents are nowhere close:
`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` is 9/19 done (10 open), `...batch1b...` is 6/18 done (12
open) — 15/31 total, not 31/31. This is the widest gap observed across all six recurrences (previous worst was 3/5).
Declining, same disposition; skipping rather than re-blocking. Sixth distinct plan pair, and the first to exercise the
multi-doc `depends_on: [a, b]` gate shape (prior recurrences were all single-doc `depends_on`) — worth noting in the
eventual root-cause fix that the gap is not scoped to the single-dependency case either.

## 2026-07-30 recurrence — FIFTH distinct plan pair (cefi_track7_candle_namespace_residual)

Slot 7 was dispatched `cefi_track7_candle_namespace_residual_finalize-001` (plan_ref
`cefi_track7_candle_namespace_residual_finalize_2026_07_25.md`,
`depends_on: [cefi_track7_candle_namespace_residual_2026_07_25]`, `gate_on_depends: true`) while the gating parent
plan's single todo — an `[OPERATOR]`-tagged delete of 149 stale legacy candle objects — is still `- [ ]` unchecked.
Worse than the prior recurrences: this delete is human-execution-only under delete-safety-protocol hard-stop #2 (no §3a
carve-out per the parent doc's own 2026-07-28 "Hard-stop review" banner), AND its own upstream gate (candidate-7 of
`cefi_consolidated_native_ao_extract_2026_07_25.md`, the verify+`--force`-backfill prerequisite) is ALSO still `- [ ]`
unchecked — a two-level unmet gate, not one. Reconciling the finalize plan's checkboxes now would fabricate evidence for
a delete that has not been verified, backfilled, or executed. Declining, same disposition as every prior bounce;
skipping rather than re-blocking on an already-answered question. Fifth distinct plan pair confirms this is a durable,
general dispatcher gap, not an isolated one-off — root-cause item 1 remains the correct fix.

## 2026-07-30 recurrence — SEVENTH distinct plan pair (prediction_satellite_ao_dispatch_batch6)

Slot 7 was dispatched `prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize-001` (`already_in_progress: true`,
`depends_on: [prediction_satellite_ao_dispatch_batch6_2026_07_29]`, `gate_on_depends: true`, requiring all 14 of
batch6's todos done) while batch6 is only 3/14 done (001 CQG fix, 002 EventTransport bridge, 004 VM launch-only; 003,
005-014 still `queued`). Confirmed via
`GET /api/backlog/prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize-001/blockers` → `"ready (no blockers)"` —
same standard-wiring-path failure (all 14 upstream task ids are real, non-pruned backlog rows; the gate simply never
attached them). Cross-checked the finalize plan's OWN `sequential: true` chaining is working correctly
(`GET .../finalize-002/blockers` → `"prereq task ...finalize-001 not done"`), isolating the failure to the
`gate_on_depends` wiring specifically, not `sequential`. Read the current `regen_backlog_from_plan.py`/`dispatch.py`
(local HEAD `30568ec2`) end-to-end — depends_on parsing, `_stem()` matching, the non-empty-upstream_ids path in
`_wire_gate_on_depends_prereqs`, and `_wire_sequential_prereqs`'s same-plan-id scoping all look correct on static
reading, consistent with this doc's standing conclusion ("wiring simply didn't happen" / re-wiring across regen ticks is
the gap, not a parsing defect). Noted one additional data point for the root-cause investigation: the live
orchestrator's `GET /api/state` reports `server_started: 2026-07-30T16:44:20Z`, and my worker checkout's HEAD (pulled
fresh this session) has commits landing up to `~17:14:43Z` — i.e. it's possible the running server process predates some
regen-path commits from its own uptime window; `version` in `/api/state` reads literally `"unknown"`, so this couldn't
be confirmed either way. Worth checking whether the P0 fix in flight (below) has actually been deployed+restarted into
the live process once it lands, not just merged. Declining to author any reconciliation content on the false premise
that batch6 shipped; not flipping the finalize plan's todo 1 checkbox; skipped via `POST /skip-current-task` rather than
filing a duplicate issue doc (my first attempt did exactly that — reverted, see this doc's own dedup precedent from slot
14 on the batch1/1b pair the same day). 11th+ documented bounce off this general wiring gap.

## 2026-07-30 recurrence — EIGHTH distinct plan pair (cross_cutting_satellite_ao_dispatch_batch2, mid-sequence this time)

Same session, slot 7's very next dispatch after the recurrence above:
`cross_cutting_satellite_ao_dispatch_batch2_2026_07_26_finalize-002`
(`depends_on: [cross_cutting_satellite_ao_dispatch_batch2_2026_07_26]`, `gate_on_depends: true`, `sequential: true`,
requiring all 14/15 of batch2's todos done before ANY finalize todo dispatches). Todo 1 of the finalize plan was
genuinely done (verified — 13/14 source-doc reconciliations correct, one real discrepancy found and fixed), so
`sequential` chaining correctly let todo 2 through — but batch2's OWN plan file shows only 10/15 todos checked (5 still
`- [ ]`: features-service catalogue inventory, the dp-audit OOM fix, two bounded alert bug fixes, a retagged `[DATA]` P2
item, the unfiltered-callsite audit).
`GET /api/backlog/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26_finalize-002/blockers` → `"ready (no blockers)"`
— same failure. Notable new data point: this is the first recurrence where the finalize plan's TODO 1 (not just the
whole finalize plan) had already correctly dispatched-and-completed while the gate on the REMAINING todos still failed
to hold — confirms the wiring gap isn't a one-time "first dispatch after ingestion" race (todo 2 is a later dispatch,
well after the plan pair's initial regen tick), consistent with this doc's standing "re-wiring across regen ticks"
hypothesis over a first-tick-only race. Declined to author the Deferred-items re-check on the false premise the full
batch landed; not flipping todo 2's checkbox; skipped via `POST /skip-current-task`. 12th+ documented bounce, 8th
distinct plan pair.

## Todos

- [x] [BACKEND] P0. **Trace + fix `_wire_gate_on_depends_prereqs`** — ✅ agent-orchestrator@13a5dd8 +
      agent-orchestrator@bd522d0 (13a5dd8 alone was NOT sufficient — see "2026-07-30 correction" note below for the
      actual primary root cause) (`agent-orchestrator/server/regen_backlog_from_plan.py`) so a `gate_on_depends: true`
      finalize plan's tasks reliably get the upstream plan's real task ids wired into `prereqs.completed_tasks` on every
      regen tick, not just (maybe) at first-ingestion. Confirmed 9 times across ≥6 distinct plan pairs (defi_dex_pool,
      prediction_satellite_batch3, mdps_features 11c per-todo shape, cross_cutting_satellite_batch1 dual-gate,
      cefi_track7_candle_namespace_residual, cefi_track2_coverage_backfill — the last one bounced across at least 3
      separate slot dispatches) that `GET /api/backlog/<finalize-task>/blockers` reports `"ready (no blockers)"` while
      the real upstream tasks are still non-`done` in the live backlog. Repo: agent-orchestrator. **Done when**: root
      cause identified (e.g. wiring only running once at ingestion vs. every regen tick, or a
      `gated_plans`/`file_to_ids` ordering race), fixed, and a regression test proves a `gate_on_depends: true` plan's
      tasks carry the upstream ids in `prereqs.completed_tasks` immediately after a regen tick that ingests both plans
      together (the same-tick-ingestion shape, not just the already-covered empty-upstream cases).
- [x] [BACKEND] P2. **Add a standing dispatch-time re-check** as a second line of defense: even without the root-cause
      fix, `pick_next_task()` (or the `/blockers` endpoint) should independently verify a `gate_on_depends: true` task's
      cited upstream plan file's own on-disk `- [ ]`/`- [x]` checkbox count before dispatching it, refusing dispatch
      (not just relying on `prereqs.completed_tasks`) if the upstream isn't fully checked off. Repo: agent-orchestrator.
      **Done when**: a synthetic test plan pair with an intentionally-unwired gate is confirmed to NOT dispatch its
      finalize task, proving the check catches what `_wire_gate_on_depends_prereqs` currently misses. — ✅
      agent-orchestrator@c34b560
- [ ] [BACKEND] P1. **Root-cause the "zero-derived-parent-row" third mechanism** — distinct from both shipped fixes
      (`13a5dd8` in-process-cache staleness, `bd522d0` prose-masquerading-as-frontmatter). Confirmed via live
      `/api/backlog` query on TWO independent plan pairs, both AFTER a post-fix server restart: the PARENT plan's own
      task rows are entirely ABSENT from the backlog (not merely unwired) —
      `cefi_satellite_ao_dispatch_batch1_2026_07_25` (10th bounce, 2026-07-30) and
      `defi_satellite_ao_dispatch_batch8_2026_08_02` (11th+ bounce, 2026-08-02) both show zero backlog rows for the
      parent plan_ref while the finalize plan's own tasks exist normally — so `_wire_gate_on_depends_prereqs` has
      nothing to attach as an unmet prerequisite and the gate reads satisfied by omission. Both repro cases share a
      candidate trigger already flagged in the Progress Log: the parent's one remaining open todo has a `**bold**`
      phrase immediately after the `P<n>.` tag (`- [ ] [DATA] P3. **Prove force + skip...**`) — worth checking whether
      `regen_backlog_from_plan.py`'s todo-derivation regex mishandles a bold span directly after the priority tag,
      causing that specific todo to never derive into a backlog row at all. Repo: agent-orchestrator. **Done when**:
      root cause identified and fixed, and a regression test reproduces one of the two recorded repro shapes (a parent
      plan whose sole remaining open todo has `**bold**` immediately after its `P<n>.` tag) and confirms the todo now
      derives a backlog row + the downstream `gate_on_depends` finalize task correctly reports the unmet prerequisite
      instead of `"ready (no blockers)"`.

## 2026-07-30 todo 2 shipped (slot 9) — on-disk defense-in-depth check

Added `gate_on_depends_unmet_upstreams_on_disk`/`gate_on_depends_holds_on_disk`
(`agent-orchestrator/server/regen_backlog_from_plan.py`), which independently re-derive a `gate_on_depends: true` task's
gating straight from the plan FILES on every dispatch attempt — reading the task's own plan frontmatter
(`_parse_frontmatter_gate_on_depends`/`_parse_frontmatter_depends_on`, the SAME parsers `_wire_gate_on_depends_prereqs`
uses) and each `depends_on` upstream's open todos (`_parse_open_todos`, matching that function's own
never-ingested-upstream disambiguation branch), WITHOUT ever consulting `prereqs.completed_tasks` — so a still-unknown
THIRD wiring bug can no longer let a gated finalize task dispatch. Wired into `dispatch.py`'s `_FILTERS` SSOT as a new
`gate_on_depends_on_disk` row (FLEET scope, same as `prereqs` — an unmet on-disk gate blocks every slot identically) and
into `explain_blocked` so `/blockers` cites the specific unmet upstream stem instead of `"ready (no blockers)"`.

Deliberately reads the PM working tree directly (`_pm_repo_path()`), NOT `_resolve_plans_dir`'s LDR-snapshot indirection
(`git fetch` + `git archive` + `tar` per call) — that snapshot is right for `regen()`'s once-per-~30-min corpus scan but
far too costly on the dispatch hot path (`pick_next_task` runs on every boot/heartbeat/done fleet-wide); mirrors
`get_full_todo_text_with_status`'s existing working-tree-direct pattern. An unreadable/missing plan fails OPEN (not
blocked), consistent with `task_still_dispatchable`/`_completed_task_satisfied`'s existing conservative defaults.

New regression test `tests/test_dispatch_gate_on_depends_disk_check.py` proves the exact acceptance shape: a synthetic
downstream task with `prereqs.completed_tasks` left EMPTY (the exact unwired shape this issue doc's bounces produced)
whose own plan file cites `depends_on: [upstream]` + `gate_on_depends: true`, with the upstream plan file still carrying
an open `- [ ]` todo on disk — `pick_next_task` correctly returns `None`, and once the upstream is fully checked off,
dispatches normally. Also pinned `gate_on_depends_on_disk`'s FLEET scope in `tests/test_dispatch_filter_table.py`'s
existing classification-contract test.

Full `quality-gates.sh` green (2137 passed, ruff/basedpyright clean) before shipping via `quickmerge --agent`. Todo 1
(the root-cause fix) remains the primary defense; this todo is the backstop, not a replacement.

## 2026-07-30 recurrence — cefi_track2_coverage_backfill_checkpoints, second bounce (slot 4)

Freshly `/boot`ed with `cefi_track2_coverage_backfill_checkpoints_finalize-001` already `already_in_progress: true` on
slot 4 (`dispatch_reason: "resume"`) — same task, same plan pair already covered by the "FOURTH distinct plan pair"
recurrence note below (slot 7). Independently re-verified before declining:
`GET /api/backlog/cefi_track2_coverage_backfill_checkpoints_finalize-001/blockers` → `"ready (no blockers)"`;
`GET /api/backlog` shows `cefi_track2_coverage_backfill_checkpoints-004`/`-005` both still `queued` (not `done`) — the
gate is still genuinely 3/5, not 5/5. Live-checked the relaunched VM
(`cefi-queue-heavy-binancefutu-x17-20260730-161443`, per
`issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`'s todo-1 relaunch):
`gcloud compute instances describe` → `RUNNING` (still alive, not re-preempted), but nowhere near completing the
`2020-02-01..2026-07-29` span — consistent with slot-7's `date=2020-01-09` observation, no material progress that would
flip the gate. Nothing has changed that would let the finalize plan's todo 1/2 close honestly. This is now the **9th**
documented bounce off this general wiring gap (across ≥6 distinct plan pairs) with the root-cause fix still
unimplemented — added the two `- [ ]` todos above (this doc previously only carried prose recommendations, never a
trackable checkbox, despite 8 prior recurrences all pointing at the same fix) so the fix itself is dispatchable rather
than perpetually re-discovered. Declining to author any reconciliation content in the finalize plan or
`cefi_consolidated_closeout_2026_07_18.md`; skipping this task (`reason_code: GATED`) rather than re-filing a duplicate
`/blocked`.

## 2026-07-30 recurrence — FOURTH distinct plan pair (cefi_track2_coverage_backfill_checkpoints)

Slot 7 was dispatched `cefi_track2_coverage_backfill_checkpoints_finalize-001` (plan_ref
`cefi_track2_coverage_backfill_checkpoints_finalize_2026_07_25.md`,
`depends_on: [cefi_track2_coverage_backfill_checkpoints_2026_07_25]`, `gate_on_depends: true`) while the gating parent
plan is 3/5 done, not 5/5 — same symptom, a 4th unrelated plan pair. Full detail + independent re-verification in
`issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30.md`'s 2026-07-30 (slot-7) recurrence note. Declined the
same way; skipped rather than re-blocked. Strengthens the case that root-cause item 1 (trace
`_wire_gate_on_depends_prereqs` across regen ticks) is a genuine, still-unfixed general gap, not a one-off.

## 2026-07-26 recurrence note (slot 8, second bounce on the prediction pair)

Slot 8 was freshly dispatched `prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize-001` immediately after
completing an unrelated tradfi task — no prior history on this plan pair this session. Independently re-verified from
the doc source before finding this issue: `prediction_satellite_ao_dispatch_batch3_2026_07_26.md` still has BOTH its
todos `- [ ]` unchecked — todo 1 (`[DATA] P1`, Kalshi schema-drift) is annotated "PARTIAL... schema-drift half DONE,
paper-order-flow half BLOCKED-OPERATOR (BLK-c2d1fff9)" (a genuinely still-open human-gated half); todo 2
(`[OPERATOR] P1`, prediction-manifest residual purge) is entirely untouched. Confirms the same wiring gap two dispatches
in a row for this plan pair (was: slot 4 on the first dispatch, now slot 8). No local file-level access to the live
`agent-orchestrator/data/config/backlog.yaml` from this slot's worktree to apply the hand-park stopgap myself (that file
is server-side state, not present in the dev clone — only `backlog.test.yaml` is checked in) — flagging so main/operator
can apply the hand-park (or fix root cause item 1) before a third bounce. Declining to author any reconciliation content
on the false premise that batch3's work has shipped; skipping this task rather than re-filing/re-blocking on an
already-answered question.

## 2026-07-30 recurrence note (slot 9, second bounce on cefi_track7_candle_namespace_residual)

Freshly dispatched `cefi_track7_candle_namespace_residual_finalize-001` on slot 9 (`dispatch_reason: "resume"`,
`already_in_progress: true`) — same task_id, same plan pair already covered by the "FIFTH distinct plan pair" note above
(slot 7). Independently re-verified before declining: `cefi_track7_candle_namespace_residual_2026_07_25.md`'s single
`[OPERATOR]` delete todo is still `- [ ]` (its own 2026-07-30 Progress Log entry re-confirms both gates unchanged), and
its own upstream gate — candidate-7 of `cefi_consolidated_native_ao_extract_2026_07_25.md`, line 157 — is also still
`- [ ]`. Live-checked `GET /api/backlog` confirmed a real backlog task exists for the upstream todo
(`cefi_track7_candle_namespace_residual-001`, `status: blocked`), so this is the standard-wiring-path failure (task IDs
exist, just never got attached to the finalize task's `prereqs.completed_tasks`), not the ambiguous-empty-upstream case.
Nothing has changed that would let the finalize plan's todo close honestly. Declined to author any reconciliation
content; skipped via `POST /skip-current-task` (`reason_code: GATED`) rather than filing a duplicate `/blocked`. 10th
documented bounce off this general wiring gap.

## 2026-07-27 recurrence note (slot 8, THIRD distinct plan pair)

A third, again genuinely different plan pair: dispatched `data_pipeline_check_mdps_features-036` (todo 11c, "MIGRATE
existing candle/feature data to zero orphans", `plans/active/data_pipeline_check_mdps_features_2026_07_20.md:235`). Todo
11c's own prose declares `depends_on: 11b` ("Once 11b lands..."), but this is a **per-todo** `depends_on` inside a
single plan file (not the finalize-plan-vs-parent-plan shape the two entries above cover) — confirms the gap isn't
scoped to the two-plan `gate_on_depends: true` frontmatter case; a bare in-body `depends_on: 11b` reference on one todo
within one plan is equally unenforced, consistent with CLAUDE.md's "no per-todo prereq syntax exists" statement (prereqs
only come from plan-level `sequential`/`gate_on_depends`, so an in-body per-todo reference was never going to be wired
mechanically — this is closer to a documentation/authoring-convention gap than a `_wire_gate_on_depends_prereqs` parsing
bug, though the externally-observable symptom (premature dispatch of a todo whose real prerequisite is unmet) is
identical). Verified before filing: 11b (`:232`) is a non-checkbox pointer to 4 sub-todos in
`plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md`, all 4 still `- [ ]` — no
orphan-detection tooling exists yet for MDPS/features/ml/strategy, so there is nothing for 11c to migrate against. Filed
`/blocked` (BLK-d42a3dbf) rather than hand-parking (no `backlog.yaml` access from this worker slot, same limitation
noted in the prior recurrence note). Main confirmed live and applied the park recipe directly
(`mdps-features-11b-orphan-report-complete=false` prerequisite + `priority: 999` + `priority_override: true` on
`data_pipeline_check_mdps_features-036`), also noting sub-todo 1 of the 11b issue doc (the MDPS candle sweep) was
already independently dispatched elsewhere — so at least the routing/dispatch side is otherwise functioning correctly;
only the specific in-body per-todo `depends_on` reference wasn't mechanically gate-able. Declining to attempt 11c;
resuming the queue-drain loop per main's directive.

## 2026-07-30 priority bump (review agent, todo 1 P1→P0)

Per main (`agt-fd75de`)'s directive (chat message 2026-07-30T16:52:10Z): bumped todo 1 (`_wire_gate_on_depends_prereqs`
root-cause fix) from `P1` to `P0`, and the doc's frontmatter `priority` from `P1` to `P0` to match, given the blast
radius confirmed in this doc (≥6 distinct plan pairs, 9+ bounces, plus a separate `[OPERATOR]`-tagged prod-delete
near-miss on slot 7 that main flagged in the same message) — the fix should dispatch ahead of the finalize-bounce churn
it keeps generating, per CLAUDE.md's `docs(plans):`-flip mechanism (P0/P1-tagged todos derive top backlog priority ~20
vs P2/P3's 50/80, per main's corroboration in an earlier message this session re: a different P0 todo). Per
`/api/state`, slot 3 already shows `last_msg: "booted — resuming gate_on_depends_wiring_gap_defi_dex_pool_finalize-00…"`
— the root-cause fix appears to already be in flight, so this bump is a durable-record correction (keeps the doc
accurate for any future re-queue) rather than a live re-prioritization of already-dispatched work. Todo 2 (the P2
dispatch-time defense-in-depth check) is intentionally left unchanged — main's ask was scoped to item 1 only.

## 2026-07-30 root cause found + fixed (slot 3, todo 1 — agent-orchestrator@13a5dd8)

Root cause is NOT in `_wire_gate_on_depends_prereqs` itself, and not a parsing/matching defect — confirms the standing
hypothesis this doc converged on across the 8th-distinct-pair note above ("the wiring gap isn't a one-time 'first
dispatch after ingestion' race... consistent with this doc's standing 're-wiring across regen ticks' hypothesis").
`_wire_gate_on_depends_prereqs` DOES re-run on every `regen()` tick, correctly re-derives `gated_plans`/`file_to_ids`
from the full current backlog every time, and DOES correctly wire `prereqs.completed_tasks` — this is provably true both
by static reading and by the pre-existing passing test `test_regen_gate_on_depends_wires_completed_task_prereqs`
(same-tick dual-plan ingestion, exactly this doc's originally-filed shape). `regen()` also correctly calls
`save_backlog()` whenever `_wire_gate_on_depends_prereqs` reports a change, so `backlog.yaml` ON DISK genuinely does get
the correct wiring.

The actual bug is one layer up, in `server/server.py`'s `_on_plan_regen` — the callback `PlanRegenLoop` (the UNATTENDED,
automatic 30-min tick — the only mechanism supposed to self-heal this without any operator/agent action) invokes after
every `regen()` call to sync the freshly-written YAML into the live server's in-process `_state["backlog"]` + SQLite
(which `GET /api/backlog/<id>/blockers` and the dispatcher actually read — NOT `backlog.yaml` directly). That callback's
guard was:

```python
if summary.new_tasks == 0 and summary.pruned_yaml == 0:
    return
```

— added 2026-06-12 to fix an earlier prune-only-tick staleness bug, but STILL incomplete: it never checked `reconciled`,
`gate_conditions_synced`, or `ruling_tasks_added` (all pre-existing `RegenSummary` fields), and THREE more counters —
`gated_changed` (the exact one this doc's bug needs), `scrubbed`, `sequential_changed` — were never even carried on
`RegenSummary` at all, despite being computed every tick and driving `regen()`'s own `save_backlog()` decision
internally. So a tick whose ONLY reportable effect was gate-wiring correctly persisted to disk but this callback had no
way to know a refresh was needed, and the live server kept serving a stale pre-wiring in-process snapshot indefinitely —
exactly the symptom recorded across all 8 distinct plan pairs / 12+ bounces above, and exactly why a manual
`POST /api/backlog/regen`/`reload` (which both refresh `_state["backlog"]` unconditionally, no guard at all) always
showed the gate correctly wired whenever anyone checked by hand, while the automatic loop never did.

Fix (agent-orchestrator@13a5dd8): added `gated_changed`/`scrubbed`/`sequential_changed` to `RegenSummary`, threaded them
through `regen()`'s return, and added a `RegenSummary.has_changes` property that ORs every counter together — a single
source of truth so a future new counter can't repeat this exact omission again. `_on_plan_regen` now reads
`if not summary.has_changes: return`. Regression coverage: `test_regen_summary_has_changes_covers_every_counter`
(parametrized over all 9 counters, proving each independently trips `has_changes`) +
`test_regen_gate_on_depends_wires_completed_task_prereqs` extended to assert `summary.gated_changed >= 1` and
`summary.has_changes is True` on the exact same-tick dual-plan-ingestion shape this doc was originally filed against +
`test_on_regen_guard_covers_prune_only_ticks` (pre-existing, updated) pins the callback's delegation to `has_changes`
since the closure itself is lifespan-local and not directly unit-testable. Full quality-gates.sh green (2109 passed)
before shipping.

Caveat (raised by slot 7's 7th-plan-pair note above, answering it here): this fix landing on `live-defi-rollout` is the
CODE fix; the live orchestrator server process (the "planning" VM) still needs to pick it up via its normal
redeploy/restart path before the automatic self-heal is live in production — not verified/executed as part of this todo
(out of scope for a backend_engineer-craft code fix; a restart of the central orchestrator affects every in-flight
worker fleet-wide, so left for the operator/main's normal deploy cadence rather than executed unilaterally here). Until
that redeploy happens, existing hand-parked gates (e.g. the defi_dex_pool_symbol_fix_backfill_purge one from earlier in
this doc) remain correctly held by their hand-set `prereqs.completed_tasks`, and any NEW gate_on_depends-only wiring
tick still won't reach the live process until the redeploy lands.

Todo 2 (the P2 dispatch-time defense-in-depth re-check) is intentionally left undone — untouched per this doc's own
scoping note above; a separate backlog task.

## 2026-07-30 correction — 13a5dd8 was necessary but NOT sufficient; actual primary root cause found + fixed (slot 2, todo 1 — agent-orchestrator@bd522d0)

Independently re-verified live AFTER 13a5dd8 was already merged to `live-defi-rollout` AND the orchestrator server had
already restarted (observed `systemctl restart orchestrator` running + confirmed via `/api/state` fleet status showing
"SERVER RESTARTED... (maintenance)"), specifically to confirm slot 3's fix actually closed the gap end-to-end before
trusting the checkbox:

```
GET /api/backlog/defi_dex_pool_symbol_fix_backfill_purge_finalize-001/blockers
→ {"explanation":"ready (no blockers)"}          # STILL wrong — same symptom as before 13a5dd8

GET /api/backlog/cefi_track2_coverage_backfill_checkpoints_finalize-001/blockers
→ {"explanation":"ready (no blockers)"}          # a second, independent plan pair, also still wrong
```

This proves 13a5dd8's in-process-cache-staleness fix, while a genuine and correctly-diagnosed bug in its own right, was
**not** the primary cause of the symptom this doc tracks — the gate was still unheld post-fix, post-restart, live.
Traced further: `_wire_gate_on_depends_prereqs` itself is sound (confirmed by slot 3's own reading and by direct
unit-level reproduction here), but it never receives a `gated_plans` entry for these plans at all, because
`_parse_frontmatter_gate_on_depends(plan_path)` — the single-field frontmatter parser that decides whether a plan is
even a `gate_on_depends` candidate — returns `False` for
`/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25.md` despite its real
`gate_on_depends: true` frontmatter field.

Root cause: every single-field frontmatter parser in `regen_backlog_from_plan.py` (13 of them —
`_parse_frontmatter_gate_on_depends`, `_parse_frontmatter_depends_on`, `_parse_frontmatter_sequential`,
`_parse_frontmatter_status`, `_parse_frontmatter_execution_scope`, `_parse_frontmatter_model_tier`,
`_parse_frontmatter_provider`, `_parse_frontmatter_thinking_tier`, `_parse_frontmatter_effort`,
`_parse_frontmatter_assigned_role`, `_parse_frontmatter_assigned_vm`, `parse_frontmatter_parent_epic`,
`_frontmatter_has_value`) regex-matches every line between the `---` delimiters unconditionally, after only
`.strip()`-ping it — with no awareness that an indented line inside a folded block scalar (`summary: >-`) is prose, not
a new top-level key. This plan's own `summary:` field narrates its gating in prose, by the SAME convention used across
essentially every gated finalize plan in the corpus:

```yaml
summary: >-
  Gated closeout for /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md — machine-held via
  depends_on + gate_on_depends: true until all 5 of that plan's todos are done, so this never dispatches early.
  Reconciles the ...
depends_on: [defi_dex_pool_symbol_fix_backfill_purge_2026_07_25]
gate_on_depends: true
```

The indented prose line (`  gate_on_depends: true until all 5 of that plan's todos are done, so this never...`), once
`.strip()`-ped, matches `^gate_on_depends\s*:\s*(.+)$` — and since it appears BEFORE the real field a few lines down,
the scanner matched it FIRST, extracted
`"true until all 5 of that plan's todos are done, so this never dispatches early. Reconciles the"` as the value,
correctly found it wasn't the literal string `"true"`, and returned `False` without ever reaching the real field. A
corpus-wide sweep of every `plans/active/*.md` confirmed this is not plan-specific: **69 plans** declare
`gate_on_depends: true` for real, and before this fix essentially none of them were being correctly detected (every one
narrates its own gate in prose by the exact same authoring convention this doc's "Recommended decision" section itself
uses). This — not the in-process cache staleness 13a5dd8 fixed — is why the symptom reproduced identically across every
one of the 10+ bounces / 6+ distinct plan pairs recorded above: it was never "seemingly different proximate causes," it
was one bug hitting every plan that documents its own machine-gating in human-readable prose (which is most of them,
since that's the established, encouraged authoring style).

A second, adjacent defect surfaced by the same corpus sweep:
`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26_finalize.md` (the dual-upstream `depends_on: [a, b]` shape
flagged in the "SIXTH distinct plan pair" note above) writes its `depends_on:` key bare, with the bracket list on the
NEXT indented line:

```yaml
depends_on:
  [cross_cutting_satellite_ao_dispatch_batch1_2026_07_26, cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26]
```

`_parse_frontmatter_depends_on`'s block-continuation handling only recognized `- item` bullet lines, not an inline
bracket list on the continuation line, so this returned `deps=[]` — meaning even with `gate_on_depends` now parsing
correctly, this specific plan's gate still wouldn't wire (no upstream ids to attach). Fixed alongside.

Fix (agent-orchestrator@bd522d0): added `_is_frontmatter_key_line(raw)` — a column-0 check (this repo's frontmatter
convention always writes top-level keys unindented; verified corpus-wide, zero legitimate indented top-level keys found)
— and gated every single-field regex match across all 13 parser functions on it, so an indented prose/continuation line
can never again be mistaken for a real key. Also extended `_parse_frontmatter_depends_on`'s block-continuation handling
to recognize an inline bracket list on the line after a bare `depends_on:` key. Regression coverage:
`test_is_frontmatter_key_line_rejects_indented_lines`, `test_parse_gate_on_depends_survives_prose_mention_in_summary`,
`test_regen_gate_on_depends_wires_despite_prose_mention_in_summary` (end-to-end, same-tick dual-plan ingestion, exact
done-when this todo specifies), `test_parse_depends_on_bracket_list_on_continuation_line`. Verified against the live PM
corpus (not just synthetic fixtures): all 69 real `gate_on_depends: true` plans now resolve non-empty `depends_on`
(previously effectively none did). Full `quality-gates.sh` green (2113 passed) before shipping.

Same caveat as 13a5dd8: this is the CODE fix on `live-defi-rollout`; the live orchestrator server process still needs to
pick it up via the normal redeploy/restart path before existing hand-parked/bounced finalize tasks self-heal in
production. Todo 2 (the P2 dispatch-time defense-in-depth re-check) remains intentionally undone, unchanged from the
scoping above.

## 2026-07-30 recurrence — NINTH distinct plan pair (cefi_satellite_ao_dispatch_batch1), mid-sequence variant

Slot 5 was dispatched `cefi_satellite_ao_dispatch_batch1_finalize-004` (plan_ref
`cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md`,
`depends_on: [cefi_satellite_ao_dispatch_batch1_2026_07_25]`, `gate_on_depends: true`, `sequential: true`, requiring all
33 of the parent plan's todos done before ANY finalize todo dispatches). This is the mid-sequence shape (like the
EIGHTH/cross_cutting_batch2 recurrence, not the first-dispatch shape): the finalize plan's own todos 1-3 were genuinely
already done by other slots (verified by reading the plan — each carries a real DONE-with-evidence citation and a
Progress Log entry), so `sequential` chaining correctly let todo 4 (archival) through — but the underlying gate on the
PARENT plan never held. Verified live: `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` is 32/33 done — exactly ONE
todo still `- [ ]` (line 355, "Extend BYBIT futures_chain shape-2 duplicate verification to the full audited scope,"
source `issues/bybit_futures_chain_write_shape_2026_07_13.md`, a distinct read-only audit task unrelated to that doc's
already-completed backfill migration). Notably, the finalize plan's OWN todo-1 Progress Log (2026-07-30, slot-9,
`review`) already flagged this exact gap in advance ("Discrepancy 1 — the dispatcher queued this finalize todo anyway
... the batch1 plan cannot be archived (todo 4 below) while this todo remains open") — so this is a case where the
in-plan record correctly predicted the bounce before it happened, but the gate still didn't hold. Declining to author
the archival (would falsely represent the parent plan as fully complete); not flipping todo 4's checkbox; skipping via
`POST /skip-current-task` (`reason_code: GATED`) rather than filing a duplicate `/blocked` or issue doc, per this doc's
established disposition. Cross-referencing against the root-cause note directly above (slot 3,
`agent-orchestrator@13a5dd8`, committed the same day): this worker's checkout has that exact fix commit in local
history, yet the live dispatch still exhibited the bug — live confirmation of that note's own caveat that the code fix
landing on `live-defi-rollout` is not the same as the live orchestrator server process having redeployed/restarted to
pick it up. 9th distinct plan pair, ≥13 documented bounces total.

## 2026-07-30 recurrence note (slot 12, 10th bounce, SAME task_id `cefi_satellite_ao_dispatch_batch1_finalize-004` — first bounce AFTER a confirmed post-fix server restart)

Freshly dispatched the exact same task (`cefi_satellite_ao_dispatch_batch1_finalize-004`) the "NINTH distinct plan pair"
note above already covers. Independently re-verified before declining:

- Doc ground truth unchanged: `plans/archive/2026_07/cefi_satellite_ao_dispatch_batch1_2026_07_25.md:355` is still
  `- [ ]` unchecked (the BYBIT futures_chain shape-2 duplicate-verification audit, source
  `issues/bybit_futures_chain_write_shape_2026_07_13.md`) — 32/33, not 33/33.
- `GET /api/state` → `server_started: "2026-07-30T17:49:40.316854Z"`, i.e. the live server process restarted AFTER both
  root-cause fixes (`agent-orchestrator@13a5dd8`, `@bd522d0`) landed on `live-defi-rollout` earlier the same day
  (confirmed both commits present in this worker's freshly-pulled checkout). Despite that,
  `GET /api/backlog/cefi_satellite_ao_dispatch_batch1_finalize-004/blockers` → still `"ready (no blockers)"` — the gate
  did not self-heal even post-restart.
- **New data point not previously checked**: queried the live `/api/backlog` (1028 total tasks) for every id/plan_ref
  containing `cefi_satellite_ao_dispatch_batch1_2026_07_25` (the PARENT plan, not the finalize plan) — **zero rows
  exist**, not even one for the still-open BYBIT todo. Only the finalize plan's own 4 tasks are present. This suggests a
  plausible third contributing factor distinct from both the 13a5dd8 (stale in-process cache) and bd522d0 (prose
  masquerading as frontmatter) fixes: if `_wire_gate_on_depends_prereqs` populates `prereqs.completed_tasks` from
  currently-existing backlog rows for the upstream plan_ref rather than re-deriving/re-parsing the upstream doc's own
  checkbox list fresh, and the upstream's one remaining open item was never (re-)derived into a backlog row at all
  (possibly pruned alongside its 32 done siblings, or never derived in the first place), the wiring pass would have
  nothing to attach as an unmet prerequisite and the gate would read satisfied by omission — worth the
  `backend_engineer` investigating whether `regen_backlog_from_plan.py`'s derivation step is itself skipping this
  specific todo (e.g. a markdown-bold-text edge case in "**Extend BYBIT futures_chain...**") rather than assuming the
  wiring layer alone is at fault.
- Declining to author the archival (would falsely represent the parent plan as fully complete); not flipping todo 4's
  checkbox. Skipping via `POST /api/slots/12/skip-current-task` (`reason_code: GATED`) per this doc's established
  disposition rather than filing a duplicate `/blocked` or issue doc. 10th documented bounce, same task_id as the 9th.

## Progress Log

- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — NOT archivable despite both
  `## Todos` items being `- [x]` (root cause `agent-orchestrator@13a5dd8` + `@bd522d0`; defense-in-depth `@c34b560`).
  The 10th-bounce note (slot 12) records a still-unexplained residual measured AFTER a confirmed post-fix server
  restart: `.../cefi_satellite_ao_dispatch_batch1_finalize-004/blockers` still read `"ready (no blockers)"`, and a live
  `/api/backlog` query found **zero** rows for the parent plan_ref at all — a plausible third contributing factor (the
  wiring pass having nothing to attach, so the gate reads satisfied by omission) that neither shipped fix addresses.
  Also covered by the 2026-07-31 operator directive (`unified-trading-pm@14478ca26`) routing AO-machinery docs to
  `execution_scope: local-only`.
- **Counting note (2026-08-02)**: this doc's REAL open-todo count is **0**, not the 5 the NA inventory reports. All 5
  `- [ ]` lines it matches are the upstream plan's todos quoted inside a fenced code block in the "What I found"
  section. Tracked as a tooling defect in
  `/plans/active/issues/na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md`.
- **2026-08-02 recurrence — 11th+ distinct plan pair (defi_satellite_ao_dispatch_batch8), zero-derived-parent-row case
  reproduced again** (slot 15, `cicd`-role worker adopting `data_engineering` craft for the dispatched task). Dispatched
  `defi_satellite_ao_dispatch_batch8_2026_08_02_finalize-001` (`already_in_progress: true`, `dispatch_reason: "resume"`)
  — a fresh plan pair, both docs authored the same day (2026-08-02, single commit `f63b8eb1`). The finalize plan's todo
  1 literally opens "Once `defi_satellite_ao_dispatch_batch8_2026_08_02.md`'s todo is `[x]`..." and the frontmatter
  carries `depends_on: [defi_satellite_ao_dispatch_batch8_2026_08_02]` + `gate_on_depends: true`. Verified independently
  after a fresh-pull to current `live-defi-rollout` HEAD:
  - `plans/active/defi_satellite_ao_dispatch_batch8_2026_08_02.md`'s single `[DATA] P3` todo (the LST-rate force/skip
    VM-launch proof) is still `- [ ]` on disk — not done.
  - `GET /api/backlog/defi_satellite_ao_dispatch_batch8_2026_08_02_finalize-001/blockers` →
    `{"explanation":"ready (no blockers)"}` (should have reported the unmet upstream).
  - `GET /api/backlog` (1347 total tasks) has **zero rows** for the parent plan_ref
    (`plans/active/defi_satellite_ao_dispatch_batch8_2026_08_02.md`) at all — only the finalize plan's own 3 tasks
    exist. Not a timing/race artifact: `/api/state` shows `server_started: 2026-08-02T15:30:48Z` and
    `last_updated: 2026-08-02T16:33:50Z`, i.e. ~1h after the plan pair's single commit (14:54:59 UTC) with the ~30-min
    `PlanRegenLoop` cadence having had multiple ticks to derive it. This reproduces the exact "zero-derived-parent-row"
    pattern the 10th-bounce note (above) first flagged as a plausible third contributing factor distinct from both
    shipped fixes (`13a5dd8` in-process-cache staleness, `bd522d0` prose-masquerading-as- frontmatter) — that hypothesis
    is still unconfirmed/unfixed. One additional data point for whoever investigates it: the parent's sole todo text is
    `- [ ] [DATA] P3. **Prove force + skip for the LST-rate surfaces against the `-test-` bucket** — extracted verbatim from...`
    — a `**bold**` phrase immediately after the `P<n>.` tag, the same shape flagged as a suspect in the
    BYBIT/cefi_satellite_ao_dispatch_batch1 10th-bounce note ("a markdown-bold-text edge case"). Two data points now
    share that exact shape; worth the `backend_engineer` checking whether `regen_backlog_from_plan.py`'s todo-derivation
    regex mishandles a bold span directly after the priority tag specifically (as opposed to the wiring layer, which
    both shipped fixes already addressed). Declining to author the Phase-3 annotation/Deferred-item re-check on the
    false premise that batch8 shipped; not touching `lst_rate_honest_coverage_2026_07_21.md`'s Phase-3 checkbox.
    Skipping via `POST /api/slots/15/skip-current-task` (`reason_code: GATED`) per this doc's established disposition
    rather than filing a duplicate `/blocked` or issue doc.

- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — re-affirmed. The doc's `## Todos` section is fully
  `[x]` done; the 5 grep-matched `- [ ]` lines are a confirmed false positive (verbatim quotation of a now-archived
  upstream plan's todos inside a fenced code block, already self-flagged by this doc's own Counting note — real open
  count is 0). The doc stays NA on its most-recent Progress Log entries: a still-unresolved "zero-derived-parent-row"
  third root-cause mechanism, reproduced again the same day on an unrelated plan pair, plus the 2026-07-31 operator
  directive routing AO-machinery/dispatch-logic docs to `execution_scope: local-only`. Only change since the last marker
  is a mechanical `context_scope` path fix reflecting the quoted plan's archival — no substantive content changed.
- **context-scout 2026-08-03**: refreshed context_scope (5 entries, unchanged — verified all still resolve).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **2026-08-06 (AO issue-doc sweep, re-verification pass)**: this doc had been carried across multiple
  na-eligibility-audit passes as "`## Todos` fully `[x]`, real open count 0" (per the 2026-08-02 Counting note) — but
  that note only concerned the grep-false-positive fenced-code-block lines, not the genuine, still-unresolved
  "zero-derived-parent-row" mechanism the Progress Log itself has documented twice (10th bounce 2026-07-30, 11th+ bounce
  2026-08-02) as a confirmed live gap neither shipped fix addresses. That finding had never been captured as a real
  `- [ ]` todo — a violation of the workspace's own "every follow-up is a todo, never prose" rule. Added the todo above
  so it's dispatchable rather than perpetually re-discovered in prose across future bounces. Doc stays open, NOT
  archived.
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:c6cb81431286c616]: KEEP-NA, valid — 5 of 6 grep-matched checkbox lines are fenced-code-block quotes of an archived upstream plan (tracked tooling false-positive), not real open items; the one genuine item (root-cause the zero-derived-parent-row dispatch-gate mechanism) is live-dispatch-critical-path agent-orchestrator machinery under active investigation, per a 2026-07-31 operator directive routing AO-machinery docs to local-only.

## 2026-08-08 recurrence — another distinct plan pair (defi_expected_unattempted_backlog_1m_2026_07_03), zero-derived-parent-row again, new sub-bullet shape

Slot 7 was dispatched `defi_expected_unattempted_backlog_1m_2026_07_03_finalize-001` (plan_ref
`plans/archive/2026_08/defi_expected_unattempted_backlog_1m_2026_07_03_finalize_2026_08_08.md`,
`depends_on: [defi_expected_unattempted_backlog_1m_2026_07_03]`, `gate_on_depends: true`) while the upstream issue doc's
sole remaining `[SCRIPT] P2` todo was still `- [ ]` open. Verified live:

```
GET /api/backlog/defi_expected_unattempted_backlog_1m_2026_07_03_finalize-001/blockers
→ {"explanation":"ready (no blockers)"}

GET /api/backlog (filtered for defi_expected_unattempted_backlog_1m_2026_07_03):
defi_expected_unattempted_backlog_1m_2026_07_03_finalize-001   dispatched
defi_expected_unattempted_backlog_1m_2026_07_03_finalize-002   queued
```

Zero backlog rows exist for the upstream `[SCRIPT]` todo itself — only the finalize plan's own 2 tasks are present. Same
"zero-derived-parent-row" pattern as the 10th/11th+ bounces above. **New data point for the still-open root-cause item 3
(the suspected markdown-bold-after-`P<n>.`-tag derivation edge case)**: the undispatched todo here is BOTH (a) an
indented `  * [ ]` sub-bullet nested under a parent `- [x]` checkbox (not a top-level `- [ ]` line — a shape not
previously recorded in this doc's repro list) AND (b) carries `**bold**` immediately after its `P2.` tag
(`* [ ] [SCRIPT] P2. **Add \`a_token\`/\`debt_token\`
aliases...**`) — both suspected trigger shapes present at once. Worth the `backend_engineer`checking whether`regen_backlog_from_plan.py`'s todo-derivation regex requires a top-level (unindented) `-
[ ]`/`- [x]`prefix and silently skips indented` * [ ]` sub-bullets entirely, independent of the bold-span hypothesis.

Independently re-verified the underlying code state before declining (did not just skip blind): the source doc's
`[SCRIPT]` todo turned out to be significantly over-scoped relative to actual current code — most of its claimed effect
(alias resolution, the `perp_trades` over-fan non-reproduction) already holds true via an unrelated pre-existing fix;
only a small VENUS/SOLEND `oracle_prices` widening + one regression test remain. Narrowed the source todo in place to
reflect this (see `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`'s 2026-08-08 Progress Log entry for full
evidence) — a genuine content correction, not a false-completion claim. Declining to flip the finalize plan's `[REVIEW]`
checkbox (the gate is still genuinely unmet even after narrowing); not touching the `[DOC]` archival todo. Skipping this
task rather than forcing it through, per this doc's established disposition.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.

## 2026-08-09 recurrence — cleanest repro yet: `status: draft` upstream, not a markdown-formatting edge case (ao_satellite_ao_dispatch_batch11)

Slot 5 (data_engineering craft adopting review for this task) was dispatched
`ao_satellite_ao_dispatch_batch11_finalize-dd3fa33044f1` (plan_ref
`plans/archive/2026_08/ao_satellite_ao_dispatch_batch11_finalize_2026_08_09.md`,
`depends_on: [ao_satellite_ao_dispatch_batch11_2026_08_09]`, `gate_on_depends: true`). Verified live:

```
GET /api/backlog/ao_satellite_ao_dispatch_batch11_finalize-dd3fa33044f1/blockers
→ {"explanation":"ready (no blockers)"}

GET /api/backlog (filtered for ao_satellite_ao_dispatch_batch11_2026_08_09, non-finalize):
→ 0 rows
```

Same "zero-derived-parent-row" symptom as every prior entry below, but this repro is cleaner than the two standing
hypotheses (markdown-bold-after-`P<n>.`, indented sub-bullet): `ao_satellite_ao_dispatch_batch11_2026_08_09.md` is
`status: draft` — per `PLAN_FORMAT.md`, a draft plan is explicitly **NOT ingested** into the backlog at all (by design,
pending operator approval to flip to `active`). Its sole todo is a plain top-level `- [ ]` line with no bold span and no
nesting — neither of the two previously-suspected derivation-regex edge cases applies here. Zero backlog rows for a
`status: draft` upstream is _correct_ behavior for the upstream itself (drafts shouldn't dispatch); the bug is that
`gate_on_depends`'s wiring — and the on-disk defense-in-depth check (`gate_on_depends_holds_on_disk`,
`agent-orchestrator@c34b560`, which reads the upstream plan FILE directly via `_parse_open_todos`, not backlog rows) —
evidently doesn't independently re-derive "draft upstream with an unshipped todo" as an unmet gate either. Worth the
`backend_engineer` checking whether `_parse_open_todos`/`gate_on_depends_holds_on_disk` skips or mis-parses a
`status: draft` upstream specifically (e.g. treating "not ingested" as "nothing to be unmet about" rather than "not
done"), independent of the bold/sub-bullet hypotheses already on file.

Declined to author the reconciliation on the false premise batch11 shipped (no commit exists); recorded the discrepancy
inline in the finalize plan's own todo 1 + added a new tracked todo there per its done-when clause, rather than
duplicating a new issue doc. Skipping via `reason_code: GATED` per this doc's established disposition.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **6**, matching. This doc's own Progress Log already cites the 2026-07-31 operator directive
  (`unified-trading-pm@14478ca26`) routing AO-machinery/dispatch-logic docs to `execution_scope: local-only` — an
  explicit dated operator ruling, not re-litigated. The sole remaining real todo (root-cause the "zero-derived-parent-
  row" third mechanism) is live-dispatch-critical-path git/backlog machinery with 2 competing unconfirmed hypotheses
  (status:draft-upstream non-derivation, markdown-bold/indented-sub-bullet derivation-regex edge cases) still under
  active investigation via ongoing recurrence notes (most recently 2026-08-09) — genuinely not yet bounded to a single
  fix, consistent with every prior pass on this doc.
- **context-scout 2026-08-17**: re-verified context_scope (5 entries), unchanged.
- **na-eligibility-audit 2026-08-17 (ao tranche, re-verified)** [body-hash:daaa1b128dcd0006]: KEEP-NA, valid —
  re-affirms the earlier same-day marker above (content edited after it was written, substance unchanged). 5 of 6
  grep-matched checkbox lines remain fenced-code-block quotes of an archived upstream plan (tracked tooling
  false-positive), not real open items; the 1 genuine item (root-cause the "zero-derived-parent-row" dispatch-gate
  mechanism) is live-dispatch-critical-path agent-orchestrator machinery under active investigation, per the standing
  2026-07-31 operator directive routing AO-machinery docs to local-only.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:1e6c12c7e9789219]: KEEP-NA, valid — grep_open_todo_count mismatch (6 vs 1) explained: 5 of 6 hits are a quoted upstream doc's checkboxes inside a fenced code block (self-documented known tooling artifact, na_inventory_counts_fenced_code_block_checkboxes_as_open_todos_2026_08_02.md), not this doc's own todos. Doc cites the 2026-07-31 operator directive routing AO-machinery/dispatch-logic docs to execution_scope:local-only (4+ citations, most recently 2026-08-17); sole open todo is deep unresolved dispatcher-internals investigation, consistent with 6+ prior audit passes.
- **context-scout 2026-08-20**: re-verified context_scope (5 entries), unchanged.
