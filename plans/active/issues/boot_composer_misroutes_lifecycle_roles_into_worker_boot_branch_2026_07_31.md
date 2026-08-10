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
asset_group:
  [ao] # corrected 2026-08-04 (ag-closeout-audit ao tranche run) -- was [meta]. Genuinely AO server code
  # (server/prompts.py::_compose() boot-prompt routing bug), not a generic process doc.
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
author: unknown
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [review-role-finding-agt-0e7906, main-orchestrator-triage]
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/prompts.py,
    agent-orchestrator/server/autospawn.py,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/state_store/tasks.py,
    /agents/ag_closeout_auditor.md,
    /plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md,
  ]
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

- [x] ✅ [SCRIPT] P2. Make `server/prompts.py::_compose()` route lifecycle roles (`review`/`main`/`monitor`) to the
      slot-less register/poll STEP block even when a `slot_id` is present — add a `_REGISTER_POLL_ROLES` guard before
      the `elif slot_id is not None:` branch (prompts.py:184); keep the escalation-role branch (line 166) unchanged. Add
      a `_compose()` unit test asserting review/main/monitor render the register/poll block with `slot_id` set. Verify
      no downstream consumer in `ensure_review_agents` depends on the boot-prompt slot_id. Cite
      `plans/active/issues/boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md` in the commit.
      — **SHIPPED `agent-orchestrator@6166269`** ("composer-guard fix routing review/main/monitor to register/poll
      shape", landed 2026-08-08T19:35:33Z). Review-verified holding: a fresh slot-1 review boot at ~22:53Z
      (`agt-e817dd`) went through `POST /api/agents/register` cleanly on the first attempt, no `/api/slots/1/boot` call
      at all; `/api/activity` shows zero `boot_read_unconfirmed` events for slot 1 since 18:07:28Z (1.5h before the fix
      landed) through ~22:58Z (~3.3h clean vs. the prior ~6-of-14 boot cycles hitting it same-day pre-fix).

# 2026-07-31 (main-orchestrator) — SEVERITY ESCALATION: auditor variant causes SILENT DATA LOSS, and the fix set is incomplete

The same `_compose()` misroute hit a **second, more damaging** lifecycle role, and the current fix scope does not cover
it. Reported by review, verified + corrected by main.

- **New affected role: `ag_closeout_auditor`** (slot 4, scheduled one-shot `/ag-closeout-audit`, tranche=cefi). It is
  spawned WITH a `slot_id` and is NOT in `_ONE_SHOT_ESCALATION_ROLES`, so it falls into the same
  `elif slot_id is not None:` worker-boot branch — `/boot` independently handed it a generic backlog task
  (`unified_trading_sa_live_iam_drift_vs_terraform-003`, a `[TERRAFORM]` P2 to revoke/import 2 self-escalation-capable
  IAM roles) on top of its mandated audit. The current suggested fix's `_REGISTER_POLL_ROLES = {review, main, monitor}`
  **omits `ag_closeout_auditor`** (and any other one-shot lifecycle/audit role that carries a `slot_id`). Whatever guard
  lands must be driven by a role classification that includes the auditor lifecycle roles, not a hard-coded trio.
- **The data-loss chain (this is the escalation).** Slot 4 correctly did NOT work the mismatched task (it did its real
  cefi audit — 2 commits `cf5658f3a`/`2d5fb4b59` on origin), then called `/done` on the mismatched task with an **empty
  `sha`**, intending to release it untouched. But `/done` marked it `status=done` (`done_sha=""`) — a genuine, undone,
  security-relevant backlog item silently dropped from the queue. The plan SSOT was fine (checkbox
  `issues/unified_trading_sa_live_iam_drift_vs_terraform_2026_07_31.md` P2 still `- [ ]`), but the derived backlog row
  falsely read done, so no worker would ever pick it up. For a self-discovering review agent the misroute is merely
  wasted tokens (existing P2 framing); for a one-shot auditor it is **silent data loss** — hence P1.
- **Repeating pattern, not a one-off:** 2 more `ag_closeout_auditor` runs are registered (`agt-89a9c6`, `agt-c2a8bd`);
  each scheduled run can false-done whatever task `/boot` mis-hands it until both defects below are fixed.
- **Immediate damage corrected (main, 2026-07-31):** reopened `unified_trading_sa_live_iam_drift_vs_terraform-003` via
  `POST /api/backlog/{id}/reopen` (`prior_status=done`, `prior_done_sha=""` → `queued`; verified it survives a regen,
  the still-unchecked checkbox keeps it not-done). The task is back in the queue as `ready (no blockers)`.

## Added follow-up todos

- [ ] [SCRIPT] P1. Fix `/done` so an **empty `sha`** does NOT mark a task `status=done` — a release-not-complete signal
      must return the task to `queued` (or be rejected), never record a terminal `done` with `done_sha=""`. This is the
      distinct data-integrity defect that turned a benign boot-misroute into silent data loss; independent of the
      composer fix. Pair with the existing `/api/backlog/{id}/reopen` correction path and the `no_plan_flip` hardening
      referenced in its docstring. Add a regression test: `/done` with empty sha on a task whose plan checkbox is
      unchecked must leave it `queued`.
- [x] ✅ [SCRIPT] P1. Extend the composer-guard fix (todo above) so its role classification covers **one-shot
      lifecycle/audit roles** (`ag_closeout_auditor` and siblings), not just `{review, main, monitor}` — otherwise the
      auditor data-loss variant persists after the review/main/monitor guard lands. — **SHIPPED
      `agent-orchestrator@0a8ed16`** ("fix(prompts): plan_health-family one-shot dispatches skip generic /boot",
      2026-08-02, ancestor-verified on `origin/live-defi-rollout`): `server/prompts.py:70-84`
      `_ONE_SHOT_ESCALATION_ROLES` now contains `ag_closeout_auditor`, `na_eligibility_auditor`,
      `context_scout_auditor`, `plan_reconciler`, `docs_reconciler`, `plan_health`, and `_compose()`'s one-shot branch
      (`:194`) precedes the worker-`/boot` `elif` (`:214`). Landed via the sibling doc
      `/plans/archive/issues/persistent_slot_tmux_session_hijacked_by_transient_plan_health_dispatch_2026_08_01.md`'s
      todo 5, which is why this doc's own checkbox was never flipped — found by `/plan-reconcile ao` 2026-08-06. The
      other two todos in this doc are confirmed genuinely still open (no `_REGISTER_POLL_ROLES` symbol exists;
      `mark_done()` still has no empty-`sha` guard).

# 2026-08-01 (ag_closeout_auditor, slot 12, dispatch agt-dd7b76, tranche=defi) — third occurrence, still unfixed, data-loss avoided this time

Confirms the composer misroute is **still live** as of 2026-08-01T11:35Z (one day after this doc was filed) and **not
cefi-specific** — same defect now reproduced on a second tranche.

- Slot 12's generic `AGENT BOOT` boot-stub text (STEP 2: `POST /api/slots/12/boot` … "the response carries your task")
  gave no hint to declare `slot_role`. A `/boot` call without it landed in the `elif slot_id is not None:` worker branch
  and bound an unrelated stray task (`sports_fast_t1_recon_oom_live_capture_outage-002`, `[DATA] P0`,
  `assigned_role: data_engineering` — a different stray task than the cefi run's IAM P2, underscoring this is "whatever
  `pick_next_task` finds," not a specific-task bug).
- **Data loss avoided**: caught the mismatch via code-read (`server/prompts.py` + `server/routes/slots_worker.py`)
  before calling `/done`, so the empty-sha trap (this doc's first P1 todo) never triggered. Re-`/boot`ed with
  `"slot_role": "ag_closeout_auditor"` explicitly set; the existing server-side self-heal
  (`ag_closeout_auditor_one_shot_complete_no_agentrow_recurrence_2026_07_29`) fired as designed —
  `plan_health_stray_task_binding_released` (confirmed via `GET /api/activity`) cleanly released the stray task back to
  the general queue (`target_slot=None`, so any data_engineering worker can still pick it up) instead of leaving it
  silently bound-but-unworked. No backlog corruption this run.
- **New wrinkle for the eventual fix/workaround to account for**: declaring `slot_role` on the first `/boot` call is
  necessary but not sufficient — the read-confirmation gate (`slots_worker.py::boot_slot`) computes its expected file
  set from the slot's _persisted_ `spawn_base_role`, which is still unset on that first call, so it falls back to
  `expected_read_files("worker", req.slot_role)` and 428s demanding `worker.md` too, even though
  `ag_closeout_auditor.md` never tells the agent to read it. Recovery needs BOTH: `slot_role` set on every `/boot` call,
  AND `worker.md` included in `read_files` alongside RULES.md + the role file — undocumented anywhere today, only
  discoverable by reading server source.
- Given this is the third confirmed occurrence and the real fix (follow-up todos above) is still open, worth considering
  a cheap interim mitigation alongside it: have `_compose()` (or each `PLAN_HEALTH_FAMILY_ROLES` role doc) emit the
  `slot_role` field explicitly in the STEP 2 curl example, so a scheduled one-shot agent doesn't have to rediscover this
  by code-reading every time. Not filing as a separate todo — folds naturally into the composer-guard fix already
  tracked above.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — added `/agents/ag_closeout_auditor.md` (the second
  affected lifecycle role documented in the 2026-07-31 severity-escalation section, whose data-loss variant the fix must
  also cover); kept the other 4 entries, verified all resolve.
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid.** First verdict for this doc
  (no prior marker). Read end-to-end; `grep -cE '^- \[ \]'` = **3**, matching this verdict's item count. All 3 are
  `[SCRIPT]` fixes inside `agent-orchestrator`'s own boot-composer, `/done` completion gate and backlog task-binding
  path. **KEEP-NA on a standing corpus ruling, not a fresh judgment**: the origin plan
  `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md`'s Phase-2 entry establishes that AO/orchestrator
  dispatch-and-state machinery stays human-reviewed even when a fix "looks mechanical", because a wrong fix corrupts the
  very backlog this audit depends on. This doc is the strongest instance of that class — its own escalation section
  documents the `/done` empty-`sha` variant causing **silent data loss** (a real, security-relevant backlog item
  recorded done with `done_sha=""`), reproduced across three occurrences (cefi 07-31, defi 08-01). Its "AO-scope,
  small + clear, worker-dispatchable" self-framing is exactly what this skill's calibration note says to stay skeptical
  of when the target is live-dispatch-critical-path machinery. **Also flagged**: `asset_group: [meta]` with
  `parent_epic: agent_operating_framework_master` — a third instance of the `ao`-mistag deadlock measured this run; see
  the tranche-level BLOCKED-OPERATOR-DECISION in `infra_consolidated_closeout_2026_07_25.md`'s 2026-08-02 marker.
- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, valid — re-affirmed on the standing corpus
  ruling above (not re-litigated). All 3 open todos are now already extracted into
  `/plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md` todos 6-7 (composer-guard fix + one-shot-role extension
  as todo 6; the `/done` empty-sha data-integrity fix as todo 7) — same tranche-standing-NA convention as
  `fleet_git_health_ip_185...`'s marker today. `asset_group` now correctly `[ao]` (retagged 2026-08-04, no longer the
  flagged mistag).
- **context-scout 2026-08-05**: re-scouted; swapped `/agents/review.md` for
  `/plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md` (now the doc actually tracking the remaining 2 open
  todos per the 2026-08-04 na-eligibility-audit marker above), 5 entries.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — added
  `agent-orchestrator/server/state_store/tasks.py`, the file `mark_done()` actually lives in (the still-open P1 `/done`
  empty-`sha` fix's real target, confirmed by grep — not previously cited despite the doc's own Progress Log naming
  `mark_done()` directly).
- **na-eligibility-audit 2026-08-07** (ao tranche, batch3of3): KEEP-NA, valid — code-verified both open items are
  genuinely still unfixed: `grep -rn "_REGISTER_POLL_ROLES" agent-orchestrator/server/prompts.py` returns zero hits (the
  `[SCRIPT] P2` register/poll-routing guard was never shipped), and `agent-orchestrator/server/state_store/tasks.py`'s
  `mark_done()` (lines 55-71) still unconditionally sets `status="done"`/`done_sha=sha` with no empty-`sha` guard (the
  `[SCRIPT] P1` data-integrity fix). Standing corpus ruling (AO dispatch/state machinery stays human-reviewed) still
  applies.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of the sole open
  item (`/done` empty-`sha` data-integrity fix in `state_store/tasks.py::mark_done()`). This doc cites a standing corpus
  ruling explicitly: AO dispatch/state machinery stays human-reviewed even when a fix 'looks mechanical,' because a
  wrong fix corrupts the very backlog this audit depends on — this doc's own history (3 confirmed silent-data-loss
  incidents) is the proof case for that ruling. High-stakes; agrees fully, not re-litigated.
