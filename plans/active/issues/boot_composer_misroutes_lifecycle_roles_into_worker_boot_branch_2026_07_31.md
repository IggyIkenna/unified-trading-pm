---
doc_type: issue
title:
  boot-composer _compose() routes slot-bearing lifecycle roles (review, and any main/monitor spawned with a slot_id)
  into the worker /boot handshake branch instead of the slot-less register/poll branch their role file documents
summary: >-
  On 2026-07-31 the review-role agent (agt-0e7906, slot 1) reported that its AGENT BOOT header carried worker-shaped
  instructions (STEP 0 heartbeat -> STEP 2 POST /api/slots/{id}/boot -> STEP 3 /done) instead of the register/poll flow
  (POST /api/agents/register -> loop /api/agents/{id}/poll + /reply) that unified-trading-pm/agents/review.md itself
  documents. Root cause (confirmed by code-read, agent-orchestrator repo): server/prompts.py::_compose() branches on
  slot_id and role. Its own docstring declares "slot-less agents (main/review/monitor) follow the boot/registration
  procedure written in their role file", but review is spawned WITH a slot_id (into config.review_slot_ids(), default
  slot from server/config.py:266-269) by server/autospawn.py::ensure_review_agents (render_vars include slot_id,
  ~autospawn.py:291 prompt_template=_REVIEW_PROMPT_TEMPLATE). Because slot_id is not None AND review is NOT in
  _ONE_SHOT_ESCALATION_ROLES (prompts.py:56 = {cicd, conflict_resolver, data_pipeline_failure}), _compose() falls into
  the `elif slot_id is not None:` worker-boot branch (prompts.py:184) rather than the slot-less register/poll `else`
  branch (prompts.py:203) that review.md assumes. Net: every fresh review-agent respawn gets the wrong boot prompt and
  must self-discover the register flow. Plausibly implicated in the tmux_session_lost churn on slot 1 just before the
  reporter's boot (3 agent_ids agt-65ba48/agt-42e455/agt-2a8120 tied to tmux_session orch-slot-1 within ~25 min).
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags:
  [
    agent-orchestrator,
    boot-prompt,
    prompt-composer,
    lifecycle-roles,
    review-role,
    register-vs-boot,
    respawn-churn,
    autospawn,
  ]
related: [plans/active/issues/agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md]
created: "2026-07-31"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [review-role-finding-agt-0e7906, main-orchestrator-triage]
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# What was reported

The review-role agent (`agt-0e7906`, slot 1) reported via `POST /api/agents/by-role/main/message` (2026-07-31 19:08Z)
that on spawn its `AGENT BOOT` header gave **worker-shaped** instructions:

- STEP 0 — heartbeat `POST /api/slots/1/heartbeat`
- STEP 2 — boot handshake `POST /api/slots/1/boot`
- STEP 3 — `/done` completion signal

…instead of the **register/poll** flow that `unified-trading-pm/agents/review.md` itself documents
(`POST /api/agents/register` → loop `/api/agents/{id}/poll` + `/reply`). The agent had to self-discover the register
flow (via a sub-agent code investigation; it confirmed `rc_url` is optional/nullable on `AgentRegisterRequest`, so
registration is easy once you know to call it). It is registered and polling normally now — **not blocking** — but the
mismatch will keep confusing every future review-agent respawn until fixed. Review never commits, so it asked main to
capture this as a tracked issue.

# Root cause (verified by code-read)

`server/prompts.py::_compose()` picks the boot shape from `slot_id` and `role`:

- Its docstring states the intended contract: _"Two shapes: slot workers get the STEP 0 liveness ping + STEP 2 /boot
  handshake; slot-less agents (main/review/monitor) follow the boot/registration procedure written in their role file
  instead."_
- The escalation-role set is
  `_ONE_SHOT_ESCALATION_ROLES = frozenset({"cicd", "conflict_resolver", "data_pipeline_failure"})` (prompts.py:56) —
  **`review` is not in it** (nor `main`/`monitor`).
- Branch order (prompts.py):
  - `if slot_id is not None and role in _ONE_SHOT_ESCALATION_ROLES:` (line 166) — one-shot escalation, task
    pre-specified.
  - `elif slot_id is not None:` (line 184) — **worker /boot handshake** (STEP 2 `/boot`, STEP 3 `/done`).
  - `else:` (line 203) — **slot-less register/poll** branch (`AGENT_ID_HINT` + "follow the boot/registration procedure
    documented in your role file").

The docstring calls review "slot-less", but the **spawn wiring gives it a slot_id**:
`server/autospawn.py::ensure_review_agents` (def line 144) spawns review into `config.review_slot_ids()`
(`server/config.py:266-269`) via `_do_spawn(..., prompt_template=_REVIEW_PROMPT_TEMPLATE)` (~autospawn.py:291), and the
render_vars unconditionally include `slot_id`. So for review: `slot_id is not None` is TRUE and
`role in _ONE_SHOT_ESCALATION_ROLES` is FALSE ⇒ it lands in the **worker-boot `elif`** (line 184), contradicting the
docstring's stated intent. `main`/`monitor` hit the same trap **if** they are ever spawned with a slot_id in
render_vars.

# Impact

- Every fresh **review**-agent respawn boots with worker instructions it cannot follow (there is no queue task to drain
  via `/boot`; review runs a register/poll/reply loop). Best case it self-discovers the register flow (wasted tokens +
  time); worse case it cycles.
- Plausibly implicated in the **tmux_session_lost churn** the reporter observed on slot 1 immediately before its own
  boot: 3 distinct agent_ids (`agt-65ba48`, `agt-42e455`, `agt-2a8120`) all tied to `tmux_session orch-slot-1` within
  the prior ~25 min — each possibly a review incarnation confused by the mismatched boot prompt and cycling. (Plausible,
  not proven.)

# Suggested fix direction (from the reporter, endorsed by triage)

Either of:

1. **Make the branch role-aware, not just slot-aware.** In `_compose()`, force the slot-less register/poll branch for
   lifecycle roles regardless of `slot_id` — e.g. a `_REGISTER_POLL_ROLES = frozenset({"review", "main", "monitor"})`
   guard checked before the `elif slot_id is not None:` (or fold it into the first condition). Keep the `slot_tag` in
   the header if the slot number is still informational, but drive the STEP block off the role.
2. **Omit `slot_id` from render_vars for review/main/monitor lifecycle spawns** in `ensure_review_agents` / `_do_spawn`,
   so `_compose()`'s existing `else` (slot-less) branch is reached. Cleaner if review truly needs no slot identity in
   its boot vars; verify nothing downstream (heartbeat refresh, hung-session kill in `ensure_review_agents`) depends on
   the boot-prompt's slot_id.

Approach (1) is the more robust of the two (it fixes the composer regardless of what render_vars pass), and its guard
also protects `main`/`monitor` if they are ever slot-seeded. Add a `_compose()` unit test asserting review/main/monitor
render the register/poll STEP block even when `slot_id` is provided.

# Triage / disposition

- **AO-scope**, small + clear, non-blocking (`P2`). This is a code fix inside agent-orchestrator (`server/prompts.py`,
  possibly `server/autospawn.py`) + one composer unit test — a worker-dispatchable todo, tracked below. Not
  operator-gated (no spend/credentials/destructive-mutation/scope change).
- Related prior boot/comms defect: `agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22`
  (also a lifecycle-role messaging blind spot in the same server).

# Follow-up todos

- [ ] [SCRIPT] P2. Make `server/prompts.py::_compose()` route lifecycle roles (`review`/`main`/`monitor`) to the
      slot-less register/poll STEP block even when a `slot_id` is present — add a `_REGISTER_POLL_ROLES` guard before
      the `elif slot_id is not None:` branch (prompts.py:184); keep the escalation-role branch (line 166) unchanged. Add
      a `_compose()` unit test asserting review/main/monitor render the register/poll block with `slot_id` set. Verify
      no downstream consumer in `ensure_review_agents` depends on the boot-prompt slot_id. Cite
      `plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md` in the commit.
