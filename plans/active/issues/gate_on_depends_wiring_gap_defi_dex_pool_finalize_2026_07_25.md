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
source:
  [
    defi_dex_pool_symbol_fix_backfill_purge_finalize-001,
    prediction_satellite_ao_dispatch_batch3_2026_07_26_finalize-001,
  ]
parent_epic: agent_operating_framework_master
priority: P0
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

## 2026-07-25 recurrence note

Bounced from slot 5 to slot 4 within ~2 heartbeat ticks — `/skip-current-task` does NOT prevent immediate re-dispatch to
another idle slot (only removes the offending slot from consideration for that one task instance). Parent plan
`defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` was still 0/5 todos done at re-dispatch time (verified again: no
landing commit for the `messari_basic` query fix in `market-tick-data-service`). Skipped again with the same reasoning;
main (`agt-52bb99`) confirmed the ruling live and directed this note rather than a re-investigation. Root cause (item 1
above) is still unfixed as of this note.

## 2026-07-25 recurrence note (slot 6, third bounce)

Bounced again — slot 6 was dispatched `defi_dex_pool_symbol_fix_backfill_purge_finalize-001` fresh (no prior task
history in this session). Independently re-verified before finding this doc: read the parent plan
(`defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`), confirmed all 5 todos still `- [ ]`; read
`market-tick-data-service/market_tick_data_service/cli/handlers/dex_pools_handler.py` directly and confirmed
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

## Todos

- [ ] [BACKEND] P0. **Trace + fix `_wire_gate_on_depends_prereqs`**
      (`agent-orchestrator/server/regen_backlog_from_plan.py`) so a `gate_on_depends: true` finalize plan's tasks
      reliably get the upstream plan's real task ids wired into `prereqs.completed_tasks` on every regen tick, not just
      (maybe) at first-ingestion. Confirmed 9 times across ≥6 distinct plan pairs (defi_dex_pool,
      prediction_satellite_batch3, mdps_features 11c per-todo shape, cross_cutting_satellite_batch1 dual-gate,
      cefi_track7_candle_namespace_residual, cefi_track2_coverage_backfill — the last one bounced across at least 3
      separate slot dispatches) that `GET /api/backlog/<finalize-task>/blockers` reports `"ready (no blockers)"` while
      the real upstream tasks are still non-`done` in the live backlog. Repo: agent-orchestrator. **Done when**: root
      cause identified (e.g. wiring only running once at ingestion vs. every regen tick, or a
      `gated_plans`/`file_to_ids` ordering race), fixed, and a regression test proves a `gate_on_depends:     true`
      plan's tasks carry the upstream ids in `prereqs.completed_tasks` immediately after a regen tick that ingests both
      plans together (the same-tick-ingestion shape, not just the already-covered empty-upstream cases).
- [ ] [BACKEND] P2. **Add a standing dispatch-time re-check** as a second line of defense: even without the root-cause
      fix, `pick_next_task()` (or the `/blockers` endpoint) should independently verify a `gate_on_depends: true` task's
      cited upstream plan file's own on-disk `- [ ]`/`- [x]` checkbox count before dispatching it, refusing dispatch
      (not just relying on `prereqs.completed_tasks`) if the upstream isn't fully checked off. Repo: agent-orchestrator.
      **Done when**: a synthetic test plan pair with an intentionally-unwired gate is confirmed to NOT dispatch its
      finalize task, proving the check catches what `_wire_gate_on_depends_prereqs` currently misses.

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
