---
doc_type: issue
title:
  AO dispatch keeps redispatching an [INFRA] todo whose own same-doc [OPERATOR] predecessor todo is still unchecked,
  producing repeated identical blocked-questions across 4 distinct slots
summary: >-
  `plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md` has an [OPERATOR] P1 todo
  ("decide a/b/c") immediately followed by an [INFRA] todo ("once (a)/(b)/(c) is decided, implement it"). The [OPERATOR]
  todo is correctly tracked as a genuinely operator-gated blocked item
  (`BLK-op-plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock-182a19732410`, "no worker will be spawned for it").
  But the [INFRA] todo (a SEPARATE backlog task id, `-0d5981dddb99`) is NOT gated on that — it kept getting dispatched
  to fresh workers (4 distinct slots: originally, then slots 13, 10, 24, 2026-08-08 21:24Z-21:53Z), each of which
  independently discovered the predecessor was undecided and filed a near-identical `main_agent`-authority blocked-nudge
  (BLK-55dcc825, BLK-5740a7d3, BLK-b1cd5599) asking main to pick a/b/c — a design decision main correctly declined each
  time, since it belongs to the doc's own [OPERATOR] item. Net effect: 4 wasted dispatch cycles with zero possible
  forward progress, each burning a slot-boot + a blocked-queue round-trip before self-discovering the same block.
  Mitigated for now via `POST /api/backlog/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock-0d5981dddb99/park` —
  the underlying [OPERATOR] decision item remains correctly tracked separately and is unaffected by the park.
status: open
nature: issue
asset_group:
  [ao] # corrected 2026-08-10 (/ag-closeout-audit cross-cutting) -- was [cross-cutting]. Content is 100%
  # agent-orchestrator dispatch/backlog-mechanism internals (same-doc predecessor-todo gating), not a
  # cross-AG data-pipeline concern -- repos:[agent-orchestrator] only.
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, todo-ordering, task-affinity, live-incident, park]
related:
  - /plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md
  - /plans/active/issues/ao_park_disposition_blocked_answer_no_follow_through_2026_07_31.md
  - /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md
created: 2026-08-08
author: agt-22de53 (main)
parent_epic: infrastructure_master
priority: P2
source: >-
  Main-agent routine blocked-queue sweep, 2026-08-08 21:24Z-21:53Z window — noticed the exact same design-decision
  question re-filed 3x under different BLK ids across 3 distinct slots before recognizing the pattern and parking the
  underlying task.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-08
locked_since:
context_scope: [agent-orchestrator/server/routes/backlog.py, agent-orchestrator/server/dispatch.py]
---

# AO dispatch ignores a same-doc [OPERATOR]-predecessor todo when dispatching a dependent [INFRA] todo

## What was found

Live, directly-observed during routine blocked-queue sweeps:

- The issue doc's [OPERATOR] P1 todo IS correctly recognized as operator-gated — it shows up in the blocked queue as
  `BLK-op-...` with "This todo is operator-gated (no worker will be spawned for it)."
- The doc's [INFRA] todo directly below it (worded "once (a)/(b)/(c) is decided, implement it") has NO such gating — it
  is a normal dispatchable task, and got picked up 4 times by autospawn across the session, each time producing a
  near-identical `main_agent`-authority blocked-nudge that main correctly declined (the decision belongs to the
  [OPERATOR] item, not main).
- There is no `depends_on`/prerequisite link between the two todo's backlog task ids (`-182a19732410` for the [OPERATOR]
  item, `-0d5981dddb99` for the [INFRA] item) — they are simply two todos in the same source doc with no
  machine-readable ordering relationship, even though the [INFRA] todo's own text says it depends on the [OPERATOR] one.

## Why it matters

- Real, measurable waste: 4 slot-boot cycles + 4 blocked-queue round-trips with zero possible forward progress, purely
  because the dispatcher has no way to know the [INFRA] todo is logically gated on the [OPERATOR] todo above it.
- This is a distinct root cause from `ao_park_disposition_blocked_answer_no_follow_through_2026_07_31.md` (that doc is
  about a park RECOMMENDATION from main having no automatic follow-through) — this finding is about dispatch not
  respecting an IMPLICIT same-doc ordering between an operator-gated todo and its dependent, before any blocked-answer
  is even involved.
- Mitigated here via `park`, but the general pattern (any "once X is decided, do Y" [INFRA]/[BACKEND] todo following an
  [OPERATOR] todo in the same doc) will recur for any future doc authored the same way.

## Todos

- [ ] [BACKEND] P2. Consider whether `plans/active/task_template.md`'s authoring convention should be updated to require
      an explicit `depends_on` (or a same-doc todo-ordering convention already recognized by dispatch) when an
      [INFRA]/[BACKEND] todo textually depends on an earlier [OPERATOR] todo in the SAME doc, so the dispatcher can skip
      it automatically rather than relying on a worker to self-discover the block. Repo: agent-orchestrator (dispatch
      logic) + unified-trading-pm (template convention).
- [x] ✅ [DOC] P1. **RULED 2026-08-09** — option (a) decided + implemented in
      `plans/active/issues/plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md` (see that doc's
      Progress Log for the full ruling + `unified-trading-pm@d765b4cfb1` implementation evidence; not duplicated here).
      Retagged from `[OPERATOR]` in the same edit. **Standing follow-up, not done here**: the parked backlog task
      `plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock-0d5981dddb99` still needs a live
      `POST /api/backlog/.../unpark` call against the running AO server — this doc-editing session has no dashboard
      JWT/API access to actually issue that call. Whoever next has AO API access should unpark it now that the decision
      has landed — its remaining work (the sibling doc's now-unblocked "complete the deferred archival" `[INFRA]` todo)
      is ready to dispatch/execute.
- [ ] [REVIEW] P3. Once the decision lands and the task is unparked, verify it dispatches and completes cleanly without
      re-triggering a blocked-nudge. Repo: unified-trading-pm (verification + checkbox flip only).

## Progress log

- 2026-08-08 ~21:53Z (main agt-22de53): Filed after recognizing the 3rd near-identical blocked-nudge (BLK-b1cd5599,
  following BLK-55dcc825 and BLK-5740a7d3, all for the same underlying [INFRA] task) as a pattern rather than
  independent occurrences. Parked `plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock-0d5981dddb99` via
  `POST /api/backlog/.../park` — condition
  `auto_unpark__plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock-0d5981dddb99` confirmed set. Verified the
  separate `BLK-op-...-182a19732410` [OPERATOR] item remains correctly tracked and unaffected — the park only stops the
  wasteful [INFRA]-todo redispatch, not the actual decision-tracking.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (2 entries), still accurate.
- **2026-08-09 (operator ruling batch, this session)**: The underlying decision landed — see
  `plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md`'s Progress Log for the full ruling +
  `unified-trading-pm@d765b4cfb1`. Flipped this doc's `[OPERATOR]` todo accordingly. The live `unpark` API call itself
  is left as a standing follow-up (no AO dashboard/API access from this session) — noted inline on the todo.
