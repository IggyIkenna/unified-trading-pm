---
doc_type: issue
title: Dispatcher does not exclude non-worker roles (review) from backlog task_id assignment on /heartbeat AND /boot
summary:
  "Review agent (role=review, slot 1) has received real worker backlog task_ids as new_task via plain POST
  /api/slots/1/heartbeat four times across two agent instances in one session, at an accelerating cadence:
  deployment_service_qg_red_file_size_and_broad_except-001 (~08:32, agt-3a2395),
  system_integration_tests_pip_audit_red-001 (~13:02, ~4.5h later), system_integration_tests_pip_audit_red-003 (~13:17,
  ~15min later), plus a burst of 6 misfires in one tick (~13:34, backlog_queued=64 and climbing). A NEW agent instance
  on the same slot (agt-f00d8b) then hit the SAME gap via POST /api/slots/1/boot (already_in_progress=true) at ~15:20,
  receiving execution_service_codex_compliance_red-003 as a CODE task — confirming the gap is not specific to
  /heartbeat, it affects at least two dispatch entry points. review.md explicitly documents review agents as does_not
  pull backlog tasks. Each occurrence self-mitigated via /api/slots/1/skip-current-task (and the review agent
  additionally switched its routine polling from /heartbeat to /api/agents/<id>/poll to reduce self-triggering), so no
  worker-role task was ever left undone or double-worked, but the dispatcher eligibility check appears to have no
  role-based filter across multiple endpoints, and the accelerating frequency suggests this will keep recurring and
  worsening as backlog volume grows."
status: resolved
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [dispatcher, role-eligibility, review-agent, orchestration-bug]
related: []
created: 2026-07-13
parent_epic: orchestrator_master
source: review-agent flags at 08:33, 13:03, 13:17 (main agent session 2026-07-13)
assigned_vm: NA
resolved_by:
  - "agent-orchestrator@962e676 — `review_slot` SLOT-scope filter in the shared `_FILTERS` table (dispatch.py:132
    `_blocks_review_slot`, registered :199, ctx populated :314). Keys off `config.review_slot_ids()` — deliberately NOT
    `SlotRow.slot_role`, which is a CRAFT tag that is None for most ordinary workers too and would have broken worker
    dispatch fleet-wide. Sound because `ensure_review_agents` (autospawn.py:143) is the ONLY path that boots a review
    agent and only onto slots in that same list, so the gate's slot-set is definitionally identical to the set that can
    ever run review. Covers all THREE pick_next_task call sites: /boot, /heartbeat and /done
    (slots_worker.py:204/408/991)"
  - "VERIFIED 2026-07-17 by independent skeptical audit: SHA reachable; tests/test_dispatch_review_slot_gate.py RUN LIVE
    at HEAD (5 passed), including the negative control proving a slot_role=None generic worker STILL gets dispatched —
    direct evidence the dangerous slot_role variant was not shipped"
locked_by:
execution_scope: local-only
assigned_role: backend_engineer
model_tier: sonnet-doable
thinking_tier: medium
drift_direction: advance-code
depends_on: []
priority: P2
---

## What happened

Slot 1 is running the `review` role. Four times in one session, a plain `POST /api/slots/1/heartbeat` call caused the
dispatcher to hand it a real worker backlog `task_id`:

1. `deployment_service_qg_red_file_size_and_broad_except-001` — ~08:32 (agt-3a2395)
2. `system_integration_tests_pip_audit_red-001` — ~13:02 (~4.5h later)
3. `system_integration_tests_pip_audit_red-003` — ~13:17 (~15min later)
4. A burst of 6 misfires in a single tick — ~13:34 (deployment_service_qg_red_file_size_and_broad_except-001,
   system_integration_tests_pip_audit_red-001/-003, slot11_silent_branch_reset_data_loss-003,
   execution_service_codex_compliance_red-005/-002); `backlog_queued` was observed at 64 and climbing at this point.

Then, on a NEW agent instance for the same slot (`agt-f00d8b`), the SAME gap fired via `POST /api/slots/1/boot`
(`already_in_progress=true`) at ~15:20, handing it `execution_service_codex_compliance_red-003` (a CODE task) —
confirming this is not `/heartbeat`-specific; at least two dispatch entry points (`/heartbeat` and `/boot`) share the
same missing role check.

Each time the review agent noticed (per `review.md`'s explicit `does_not: pull tasks from the backlog`), called
`POST /api/slots/1/skip-current-task`, and continued its review work — no data was lost and no worker task was silently
double-worked. The review agent also switched its own routine status pings from `/api/slots/1/heartbeat` to
`/api/agents/<id>/poll` to reduce self-triggering, but that is a workaround, not a fix, and does not cover `/boot`.

## Likely root cause (not yet confirmed by code read — flagging for whoever picks this up)

The dispatcher's slot-eligibility check for backlog task assignment does not appear to filter by the slot's attached
agent `role` (worker vs review vs main), and this gap exists in at least two places: the `/heartbeat` handler and the
`/boot` handler (both apparently share or duplicate the same eligibility logic, or each independently lacks a role
check). `review.md` encodes the "review agents don't pull backlog work" rule as agent-side behavior only; there is no
server-side enforcement preventing a review-role slot from being handed a `task_id` via either entry point.

## Recommended fix

Find wherever backlog `task_id` candidate selection happens (likely a single shared helper used by both `/heartbeat` and
`/boot` handlers in agent-orchestrator `server/`) and exclude any slot whose currently attached agent has
`role != "worker"` — the same place `parallel_safe`, `collision_group`, and `target_slot`/`affinity` are already
checked. If `/heartbeat` and `/boot` do NOT share the eligibility helper, both call sites need the fix.

## Todos

- [x] [BACKEND] P2. ✅ **DONE 2026-07-16 — `agent-orchestrator@962e676` (R6).** ⚠️ **NOT via this doc's own recommended
      fix.** It proposed a `slot_role`-based filter; two independent code-verification agents established that would be
      _actively dangerous_ — `slot_role` is a CRAFT tag, empty for review/main AND for **most ordinary generic
      workers**, so gating on its falsiness would refuse dispatch to the majority of the normal fleet. Implemented
      instead as a row in the shared `_FILTERS` table keyed on the explicit `review_slot_ids()` config list (scope
      `SLOT`, so the spawn budget honours it too). ~~Locate the dispatcher's slot-eligibility/candidate-selection logic
      for backlog task assignment~~ (agent-orchestrator `server/`, likely near the heartbeat handler or a
      `dispatch`/`assign` helper) and add a role-based filter so only `role == "worker"` slots are eligible for backlog
      `task_id` assignment.
- [x] [BACKEND] P3. ✅ **DONE 2026-07-16 — `agent-orchestrator@962e676`, `tests/test_dispatch_review_slot_gate.py` (5
      tests; removing the gate fails 3, the other 2 are negative controls).** Two corrections to this todo's premise:
      (1) it names **2** routes — there are **3**; `pick_next_task` is the single chokepoint for `/boot`
      (`slots_worker.py:204`), `/heartbeat` (`:408`) **and `/done`** (`:957`, where a worker takes its next task on
      completion). (2) there is **no "main-role slot"** to test — main runs as its own tmux session
      (`MAIN_SESSION_NAME`), not a numbered slot, so it never reaches a slot dispatch route. Also caught:
      `conftest.py`'s autouse `_default_review_slots_off` disables review slots suite-wide, so a test that does not set
      `ORCHESTRATOR_REVIEW_SLOTS` passes while testing NOTHING — all 5 set it explicitly. ~~Add a regression test
      dispatching a backlog task to a `review`-role (and `main`-role) slot via BOTH~~ `/heartbeat` and `/boot`,
      asserting no `task_id` is returned from either.

## Progress Log

- **2026-07-13 (main agent, sonnet/medium)** — Filed after the review agent flagged this occurring a 3rd time in one
  session with an accelerating cadence (previously acked the 1st and 2nd occurrences in operator chat without filing a
  durable artifact). Asked the operator earlier in chat whether this should be a dispatched agent-orchestrator plan or a
  human plan; no response yet, so filing as a `local-only` human-plan-style issue doc per findings-triage (default =
  human unless operator says otherwise) so it is not lost. Did not attempt a code fix myself — main agent does not ship
  code (worker.md's job); this is ready for a worker/operator to pick up.
- **2026-07-13 (main agent, sonnet/medium), update** — Severity spiked (6 misfires in one tick, `backlog_queued=64` and
  climbing) and then a NEW agent instance on the same slot hit the same gap via `/boot` (not `/heartbeat`), handing it a
  CODE task. Updated scope: this is not `/heartbeat`-specific. Released the stuck task via `skip-current-task` again;
  escalated the severity spike to the operator in chat.
