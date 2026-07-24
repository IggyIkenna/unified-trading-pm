---
doc_type: issue
title:
  "Dispatch: _claim_plan_for_slot pinned EVERY plan's tasks to one slot, defeating intra-plan concurrency — fixed to
  gate on sequential (agent-orchestrator@867b1731e); codex-alignment + live-deploy verification remain"
summary:
  A plan's tasks were all pinned to the single slot that claimed the first task (the small-plan one-plan-one-agent
  model), so a non-sequential plan meant to fan out (e.g. ao_remediation_a's 8 independent todos) ran serially on one
  slot instead of spreading to N agents. Root cause — _claim_plan_for_slot in state_store/slots.py pinned
  unconditionally, contradicting task_template.md's stated model that intra-plan concurrency is the default. Fixed
  2026-07-24 (operator ruling) to pin ONLY when the plan is sequential — a plumbed sequential flag from plan frontmatter
  through regen to the TaskRow, read by the dispatch guard. Shipped and QG-green on LDR; two follow-ups remain — update
  the two codex docs that still describe the old always-pin behavior, and verify the fix plus its DB migration landed on
  the live orchestrator VM after the pipeline promotes it.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, dispatch, intra-plan-concurrency, sequential, doc-code-drift]
related:
  [
    /plans/active/ao_remediation_a_independent_fixes_2026_07_23.md,
    /plans/active/ao_remediation_b_code_chain_2026_07_23.md,
    /plans/active/task_template.md,
  ]
created: 2026-07-24
last_updated: 2026-07-24
priority: P1
parent_epic: orchestrator_master
source:
  "operator-observed 2026-07-24 (ao_remediation_a's 8 'parallel' tasks all dispatched to slot 2); root-caused + fixed
  same session"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

## What happened

The operator dispatched `ao_remediation_a_independent_fixes` (8 independent todos, each on a distinct file, no
`sequential:` flag — meant to fan out). All 8 tasks were assigned `target_slot=2, affinity=medium` — pinned to one slot,
draining serially, instead of spreading across free agents. Confirmed live via `GET /api/backlog` on the orchestrator
VM.

## Root cause (code + data agreed)

`server/state_store/slots.py::_claim_plan_for_slot` — called from `assign_task_to_slot` on every dispatch — pinned the
REST of a plan's queued siblings to the claiming slot **unconditionally** (`target_slot=slot_id, affinity="medium"`).
Its docstring described the "small-plan model: one plan → one agent; cross-agent parallelism comes from separate plans."
That **contradicted** `task_template.md` §4, which states intra-plan concurrency is the default and a plan's
same-priority independent todos run concurrently across free workers.

Operator ruling 2026-07-24: the template is correct; the code was wrong. The pin must be an opt-in for `sequential`
plans only (a real ordering dependency where the same agent should drain the chain), not the default.

## The fix — shipped `agent-orchestrator@867b1731e` (on LDR, QG-green)

A `sequential` flag is now plumbed from plan frontmatter to the dispatch path:

- `server/backlog.py` — `BacklogTask.sequential: bool = False`.
- `server/regen_backlog_from_plan.py` — `_stamp_sequential_flag()` sets each task's flag from the existing
  `sequential_plan_refs` list, every regen tick (both directions, so flipping `sequential:` takes effect).
- `server/orm.py` — `TaskRow.sequential` column (Integer 0/1, default 0), mirroring `failover_allowed`.
- `server/bootstrap.py` — `_migrate_tasks_sequential_column()` (idempotent `ALTER TABLE`, backfills 0 = non-sequential);
  `sync_backlog_to_db` copies the flag on insert and refreshes it on existing rows.
- `server/state_store/slots.py` — `_claim_plan_for_slot` now returns early unless `task.sequential`. So
  `sequential: true` → pin to one agent; `sequential: false` (default) → no pin → N tasks fan out to N free slots.
- `tests/test_plan_claiming.py` — added `test_non_sequential_plan_is_not_pinned_fans_out` (the regression guard) plus
  `sequential=True` on the existing pin tests.

Ordering for a sequential plan is still enforced independently by prereqs (`_wire_sequential_prereqs`) — the pin is
purely the same-agent half. Full `agent-orchestrator` quality gate PASSED; migration self-tested (add + idempotent +
backfill).

## Open TODOs

- [ ] [DOCS] P1. **Update the two codex docs that still describe the OLD always-pin model** (now stale after
      `agent-orchestrator@867b1731e`). `/codex/12-agent-workflow/work-philosophy.md` says "tasks pin to the first slot
      that claims one — slots.py:\_claim_plan_for_slot; cross-agent speed comes from more plans"; and
      `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md` describes `_claim_plan_for_slot` pinning a
      plan's siblings. Both must be corrected to: pinning is now GATED on `sequential: true`; non-sequential plans fan
      out to N slots (intra-plan concurrency is the default, matching `task_template.md` §4). **Operator sign-off
      required before editing a codex SSOT** (workspace HARD RULE — codex edits are never autonomous). **Gate**: neither
      doc describes unconditional pinning; both cite the sequential gate + the shipping sha.
- [ ] [BACKEND] P1. **Verify the fix + migration landed on the live orchestrator VM** after the pipeline promotes it
      (LDR→staging via the Tier-C drain ~15min, then `ao-self-pull` FF-pull + restart picks up `server/**.py`). Confirm
      three things on `i-0c9b283b31d6b5ca7` (EIP 13.113.200.22, the planning VM): (a) the deployed HEAD contains
      `867b1731e` (`git merge-base --is-ancestor`); (b) the `sequential` column exists on the live `tasks` table (the
      migration ran at `create_all_tables()` on restart); (c) a non-sequential plan's tasks actually dispatch to
      different slots. **Gate**: all three confirmed, evidenced. **Cannot be done until the pipeline promotes the commit
      and the VM restarts** — not actionable immediately.

## Lessons (2026-07-24)

- **The pin is context-locality, NOT collision-safety.** File collisions are prevented by TIME separation (sequential
  prereqs gate task N on N-1, so two tasks on one file never run concurrently), not by same-slot pinning. That's why
  gating the pin off for non-sequential plans is safe: a sequential plan un-pinned still serializes via prereqs.
- **`/api/backlog` returns a JSON LIST, not a dict** — parse `d if isinstance(d, list) else d.get("tasks", [])`.
- **The `check-agent-orchestrator` skill's curl timeout is too short for a large backlog** — it timed out on
  `/api/backlog` while `/health` returned 200 in 1ms; a direct `curl -m 90` succeeded. The server was healthy, not hung.
  (Candidate follow-up if it recurs: raise the script's curl `--max-time`.)
- **The planning VM IS `i-0c9b283b31d6b5ca7`** (EIP 13.113.200.22, private 172.31.5.118) — the same box the raw-DB SSM
  reads hit. The operator's "why query the DB" was a method note (ask the running API, not the raw SQLite), not a
  wrong-host correction. Confirmed via `aws ec2 describe-addresses --public-ips 13.113.200.22`.
- **Deploy of the server Python is NOT instant and NOT `--reload`.** The deployed `orchestrator.service` runs without
  `--reload`; `ao-self-pull.sh` (cron FF-pull + `systemctl restart` on HEAD change) is deploy-currency, and the DB
  migration auto-applies on that restart via `create_all_tables()`.
- **The fix is forward-acting.** It does not un-pin the `ao_remediation_a` tasks already sitting at `target_slot=2` from
  the old behavior (the medium-affinity 600s spill releases those); the clean fan-out shows on the NEXT non-sequential
  plan dispatched after deploy.
