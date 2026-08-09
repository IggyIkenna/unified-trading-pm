---
doc_type: issue
title:
  "Boot-stub session-vars block shows names that don't match BootRequest's real JSON fields — 3rd live recurrence of the
  ag_closeout_auditor stray-Class-A-task-bind failure mode (2026-07-26, 2026-07-29, now 2026-08-02)"
summary: >-
  `agent-orchestrator/server/prompts.py`'s `_compose()` (the function that builds the `=== AGENT BOOT ===` stub every
  slot-worker session sees as its very first message) shows a "Session variables" block whose KEY NAMES do not match the
  real `BootRequest` Pydantic model's field names, and never surfaces the `slot_role` field name at all for a typed
  one-shot/scheduled role. Concretely: this run's boot message listed `WORKTREE_PATH=...` (no `WORKTREE=`) and no
  `ROLE=`/`SLOT_ROLE=` line anywhere — only the header marker `=== AGENT BOOT (role: ag_closeout_auditor, slot 12) ===`
  names the role, outside the vars block entirely. STEP 2's own text just says "POST .../boot with your session vars"
  with no example JSON body for a slot worker (unlike `worker.md`'s and `na_eligibility_auditor.md`'s own STEP 2
  sections, which both show a literal curl body). A fresh agent has no choice but to guess the JSON field names from the
  shown var names — this session guessed `"worktree_path"` (got a 422 `Field required: worktree`, self-corrected) and
  `"role"` (got a SILENT 200 — Pydantic drops unknown fields by default, so `req.slot_role` stayed `None`/empty with no
  error at all). That silent failure is the dangerous one: it let `/boot` fall through to the untyped-worker path,
  `pick_next_task()` bound an unrelated Class-A backlog task (`infra_capture_and_devops_leftovers_finalize-001`) to the
  slot, and no `lifecycle="one_shot"` `AgentRow` was ever registered — so `POST /done {"one_shot_complete": true}` 400'd
  with "no active agent owns its session ... a Class-A worker must /done with a task_id" after the full
  `/ag-closeout-audit cross-cutting` run was already complete and shipped. This EXACT symptom (stray Class-A bind +
  missing AgentRow blocking `one_shot_complete`) was already root-caused and "fixed" TWICE before —
  `ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_26.md` and `..._recurrence_2026_07_29.md` (both archived as
  resolved) — but both fixes were server-side RECOVERY guards (the stray-task-release-on-typed-reboot logic + the lazy
  `AgentRow` registration, both confirmed present and confirmed WORKING live this session — see Recovery below), not a
  fix to the actual GENERATIVE root cause: the boot stub text a fresh agent reads never tells it the correct field names
  to send. Every future one-shot/scheduled role spawn (not just `ag_closeout_auditor` — `na_eligibility_auditor`,
  `context_scout_auditor`, `docs_reconciler`, `plan_reconciler`, `plan_health` all share this same `_compose()` path) is
  one guessed field name away from reproducing this a 4th time.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [agent-orchestrator, boot-contract, session-vars, field-name-mismatch, one-shot-agentrow, docs-drift, recurring-bug]
related:
  [
    /plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_26.md,
    /plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_recurrence_2026_07_29.md,
    /plans/active/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-02"
author: unknown
last_updated: "2026-08-02"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: infra
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  Discovered live during the `/ag-closeout-audit cross-cutting` run 2026-08-02 (ag_closeout_auditor scheduled worker,
  dispatch agt-f23055, slot 12) — hit the `one_shot_complete` 400 after completing and shipping the actual audit work,
  root-caused via `server/routes/slots_worker.py` + `server/prompts.py` + `server/plan_health.py` reads, then
  self-recovered via a corrected re-`/boot` call (confirming the existing server-side guard/recovery logic works
  correctly — this doc is about the STUB TEXT that caused the wrong call in the first place, not the recovery path).
context_scope:
  [
    agent-orchestrator/server/prompts.py,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/models/worker_api.py,
    agent-orchestrator/server/plan_health.py,
    unified-trading-pm/agents/worker.md,
    /plans/active/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md,
  ]
---

# Boot-stub session-vars field-name mismatch — 3rd recurrence of the stray-Class-A-bind failure mode

## What's confirmed (live, this session)

- `server/prompts.py::_compose()` builds the `Session variables` block via `_session_vars_block()`, which just
  uppercases whatever `**vars` dict keys the caller passed (`f"- {key.upper()}={val}"`). For this dispatch, that dict
  contained a key `worktree_path` (rendered `WORKTREE_PATH=...`) and no `role`/`slot_role` key at all — `role` is passed
  as `render()`'s separate positional arg and appears ONLY in the header marker text
  (`=== AGENT BOOT (role: ag_closeout_auditor, slot 12) ===`), never in the vars block a worker is told to build its
  `/boot` JSON body FROM.
- The real `BootRequest` model (`server/models/worker_api.py:35`) fields are `worktree` (not `worktree_path`) and
  `slot_role` (not `role`, not shown anywhere in the stub for this role).
- `POST /boot` with `"worktree_path"` instead of `"worktree"` correctly 422'd (`Field required: worktree`) — a loud,
  self-correcting failure.
- `POST /boot` with `"role": "ag_closeout_auditor"` instead of `"slot_role"` returned **200 OK**, silently dropping the
  unrecognized field (default Pydantic behavior, no `extra="forbid"` on `BootRequest`) — `req.slot_role` stayed `None`.
  This is the dangerous failure: no error, no hint anything was wrong.
- Consequence, exactly matching the documented incident class in `server/routes/slots_worker.py`'s own comments
  (`ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_29` / `..._2026_07_26`): with `slot_role` empty,
  `req.slot_role in PLAN_HEALTH_FAMILY_ROLES` was `False`, so `pick_next_task()` ran normally and bound an unrelated
  Class-A backlog task (`infra_capture_and_devops_leftovers_finalize-001`) to the slot, and the
  `elif occupant == "not_typed" and req.slot_role in PLAN_HEALTH_FAMILY_ROLES:` lazy-`AgentRow`-registration branch
  never fired either. `POST /done {"one_shot_complete": true}` then 400'd:
  `"no active agent owns its session ... a Class-A worker must /done with a task_id"` — even though the actual
  `/ag-closeout-audit cross-cutting` work was already 100% complete and shipped (`unified-trading-pm@d91f44af5`).
- **Recovery confirmed working**: re-`POST /boot` with the CORRECT `"slot_role": "ag_closeout_auditor"` (plus the
  correct `"worktree"` field) triggered the existing guard at `slots_worker.py:282-312` (released the stray Class-A task
  back to the queue) and the lazy-`AgentRow` branch at `slots_worker.py:450-486`
  (`dispatch_reason: "one-off ag_closeout_auditor booted directly ... AgentRow lazily created"`). The subsequent
  `/done {"one_shot_complete": true}` call then succeeded cleanly. **So the server-side recovery mechanism from the two
  prior fixes is genuinely solid** — this doc is not asking for that logic to be touched. The gap is purely upstream:
  the boot STUB TEXT itself never told this session the right field names to use on the FIRST call.

## Why this is a 3rd recurrence, not a new bug class

Both prior incidents (`_2026_07_26`, `_recurrence_2026_07_29`, both archived resolved) diagnosed and fixed the SYMPTOM
(missing `AgentRow`, stray task binding) with server-side recovery guards. Neither touched
`_compose()`/`_session_vars_block()` — the actual text a cold agent reads to construct its first `/boot` call. Every
plan_health-family role (`ag_closeout_auditor`, `na_eligibility_auditor`, `context_scout_auditor`, `docs_reconciler`,
`plan_reconciler`, `plan_health` itself) spawns through this same `_compose()` path and is equally exposed. The guards
make each individual recurrence self-recoverable (as this session just proved), but they don't stop it from costing a
wasted 400 + investigation + re-boot cycle every time a fresh agent guesses the field names differently than the last
one did.

## Recommended fix

Two independent, complementary fixes — either alone helps, both together closes it:

1. **Show a literal example `/boot` curl body in the STEP 2 text**, the same way `worker.md`'s and
   `na_eligibility_auditor.md`'s own STEP 2 sections already do (see `worker.md` lines 97-112) — with the CORRECT field
   names (`worktree`, `slot_role`, etc.) pre-filled from the actual `vars` dict passed to `render()`, not left for the
   agent to reconstruct from the human-readable uppercase block. This is the most direct fix: nothing to guess if the
   exact curl command is already right there.
2. **Make `_session_vars_block()`'s displayed keys match the real API field names** (rename the `worktree_path` var key
   to `worktree` at the call site, and add the role under a `slot_role` key so it appears in the vars block, not only in
   the header marker) — even without fix 1, an agent copying "session var name → JSON field name" verbatim would then
   get it right.
3. **Belt-and-suspenders**: consider `model_config = ConfigDict(extra="forbid")` on `BootRequest` (and sibling
   worker-API request models) so a field-name typo 422s loudly instead of silently dropping — this would have turned
   THIS session's `"role"` mistake into the same loud, immediately-self-correcting 422 the `"worktree_path"` mistake
   already got, instead of a silent 200 that only surfaced as a failure minutes later at `/done`. Lower priority than
   1/2 since it's a defense-in-depth measure, not the direct fix, and touches a shared model other endpoints may rely on
   tolerating extra fields for — verify no caller depends on that tolerance first.

## Todos

- [ ] [BACKEND] P1. Fix `agent-orchestrator/server/prompts.py::_compose()` per recommendation 1 above: for the
      `slot_id is not None` (non-escalation) branch, replace the generic "POST .../boot with your session vars" STEP 2
      text with a literal curl example populated from the real `vars` dict (worktree/branch/operator/model/
      effort/thinking/context_used_pct/account_id/slot_role/read_files), mirroring `worker.md` lines 97-112's example.
      Done when: a fresh dispatch's boot stub shows the exact field names `BootRequest` expects, with no guessing
      required. (repo: agent-orchestrator)
- [ ] [BACKEND] P2. Fix recommendation 2: ensure the `vars` dict passed into `render()` for slot-worker roles (wherever
      that call site lives — `server/plan_health.py`'s `mode=ag_closeout` dispatch path and any generic slot-boot spawn
      path) uses `worktree` (not `worktree_path`) as the key, and includes the role under a `slot_role` key so
      `_session_vars_block()` surfaces it. Done when: the rendered stub's vars block key names are a 1:1 match with
      `BootRequest`'s field names for every field a slot worker needs to supply. (repo: agent-orchestrator)
- [ ] [BACKEND] P3. Evaluate recommendation 3 (`extra="forbid"` on `BootRequest` and sibling worker-API request models)
      — confirm no existing caller relies on extra-field tolerance before adding it; if clear, add it so a future
      field-name typo 422s immediately instead of silently no-oping. (repo: agent-orchestrator)

## Progress Log

- **2026-08-02** — Filed by `ag_closeout_auditor` (dispatch `agt-f23055`, slot 12) after hitting, diagnosing, and
  self-recovering from this exact failure mode mid-session. Root-caused via direct reads of
  `server/prompts.py`/`server/routes/slots_worker.py`/`server/models/worker_api.py`/`server/plan_health.py`; recovery
  path independently verified live (re-boot with corrected `slot_role` released the stray task, lazily created the
  `AgentRow`, and the subsequent `/done one_shot_complete` call then succeeded).
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — first pass on this doc (filed earlier
  the same day, no prior marker). All 3 todos modify `server/prompts.py::_compose()` / `_session_vars_block()` /
  `BootRequest` — the fleet-wide worker-boot path EVERY slot spawn reads as its first message, i.e. the same
  live-dispatch-critical-path class the 2026-07-31 operator directive (`unified-trading-pm@14478ca26`) deliberately
  routed to `execution_scope: local-only`. Todo 3 is explicitly a judgment call ("verify no caller depends on that
  tolerance first" before adding `extra="forbid"` to a shared request model). Bounded-per-todo is not the same test as
  safe-to-dispatch here.
- **context-scout 2026-08-03**: re-scouted; fixed a real bug in the existing context_scope — 3 of 4 entries were
  session-specific absolute paths (`/home/ubuntu/.../.tabs/12/agent-orchestrator/...`) that don't resolve for any other
  worker/host. Replaced with repo-relative paths, added `server/plan_health.py` (todo 2's other named call site) and
  `agents/worker.md` (the STEP 2 example todo 1 says to mirror) — now 6 entries.
- **context-scout 2026-08-03 (re-pass)**: re-verified under the updated methodology, unchanged (6 entries) — all still
  resolve and remain the right minimal set for the 3 open todos.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **context-scout 2026-08-07 (verification pass, correction)**: prior passes' "unchanged, still accurate" claim
  (2026-08-03 re-pass through the entry directly above) was never actually disk-verified — `agents/worker.md` has been a
  non-resolving bare path since the 2026-08-03 pass introduced it (every repo-relative entry elsewhere in this corpus
  carries a `<repo-name>/` prefix, e.g. `agent-orchestrator/server/...`; a bare `agents/worker.md` doesn't resolve from
  the workspace root, only from inside the PM repo itself). Fixed to `unified-trading-pm/agents/worker.md`, which
  resolves. Still 6 entries, no other changes.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — Prior verdict re-verified — content unchanged since the
  2026-08-06 marker. All 3 open todos remain in the fleet-wide worker-boot critical path the 2026-07-31 operator
  directive (`unified-trading-pm@14478ca26`) routed to `execution_scope: local-only`.
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — checked against the round7-10 precedent set (including
  plan-destination-defaults-AO-dispatched); it does not override the standing, dated, case-specific 2026-07-31 operator
  directive routing live-dispatch-critical-path work (this doc's exact class) to local-only — a general forward-looking
  default does not re-litigate an existing specific ruling, per this skill's own never-re-litigate convention. All 3
  todos still touch `_compose()`/`_session_vars_block()`/`BootRequest`, the fleet-wide worker-boot path every slot spawn
  reads first. Corroborated same-day: `/ag-closeout-audit ao` batch12 independently lists this doc under operator-gated
  (22).
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — re-affirmed on citation alone.
  The 2026-07-31 operator directive routing this exact live-dispatch-boot-critical-path class to local-only still
  stands, content unchanged since round11. All 3 todos remain unactioned and still touch the same
  fleet-wide worker-boot files.
