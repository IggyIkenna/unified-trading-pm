---
doc_type: plan
title: Fix broken main/review agent_id-injection surgery in spawn paths + add regression tests
summary:
  The 2026-07-10 boot-stub refactor (prompts.py) silently broke the agent_id-injection string surgery in both POST
  /api/agents/spawn and main_agent_keeper._spawn() for slot-less roles (main/review/monitor) — this is why main went
  dark and the keeper never revived it. Fix the surgery + add the missing end-to-end regression coverage.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [orchestrator, spawn, regression, main-agent, boot-stub]
related: [orchestrator_master.md]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: backend-engineer
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source: review agent (slot 1), incident found 2026-07-13 while diagnosing why main agent was not running
---

# Fix broken main/review agent_id-injection surgery in spawn paths

## What I found (review agent, 2026-07-13)

Operator reported the main agent was not running. Investigation (no tmux session named for main, no `role=main` row in
`/api/agents`, `main_agent_keeper` background daemon supposedly "ALWAYS on") traced to a real regression:

- `server/prompts.py` was refactored 2026-07-10 (see its module docstring: "boot-STUB composer... the server now sends a
  SMALL dynamic stub... nothing can truncate"). For slot-less roles (`main`, `review`, `monitor`) the composed stub
  (`_compose()`) no longer embeds a register-curl payload at all — it only tells the agent to "follow the
  boot/registration procedure documented in your role file" (the actual `curl -d '{"role": "main", ...}'` lives ONLY
  inside `agents/main.md` / `agents/review.md`, read by the freshly-spawned agent post-boot, never pasted into the
  stub).
- Both `POST /api/agents/spawn` (`server/routes/agents.py:404-411`) and `main_agent_keeper.AgentKeeper._spawn()`
  (`server/main_agent_keeper.py:714-717`) do an agent_id-injection surgery that `str.replace()`s the literal substring
  `'"role": "main"'` inside the **boot_prompt/rendered stub** — a substring that, since the cutover, no longer exists in
  that stub for slot-less roles. The manual endpoint 400s (`could not find '"role": "main"' in boot prompt`); the
  keeper's `_spawn()` returns `False` silently (`logger.error(...)` then early-return) every tick, so main was NEVER
  actually respawned by the "always-on" keeper despite `_enabled()` being pinned `True`.
- **Coverage gap that let this ship unnoticed**: `tests/test_main_agent_keeper.py::test_spawns_when_session_absent`
  patches `keeper._spawn` directly (`patch.object(keeper, "_spawn", return_value=True)`) — it never exercises the real
  `_spawn()` body against the real `prompts.render("main", ...)` output, so the broken surgery was never actually run in
  CI. There is **no test file at all** for `POST /api/agents/spawn` (`grep` for `spawn_agent_endpoint` /
  `/api/agents/spawn` in `tests/` returns nothing) — the manual endpoint's agent_id-injection logic has zero coverage.
- Confirmed by direct reproduction: manually building the exact stub `prompts.render()` produces for `role="main"` and
  calling `POST /api/agents/spawn` with it 400s exactly as predicted (worked around live by hand-injecting a literal
  `{"role": "main"}` fragment into the boot_prompt text so the surgery had something to match — that hack is NOT a fix,
  it's a one-off unblock; this plan is the real fix).

## Why it matters

Every automated respawn of main or review (crash, usage-cap kill, `dead-tmux-session`) has been silently broken since
2026-07-10 — the "mandatory steady-state, ALWAYS on" main agent guarantee (operator 2026-06-23,
`main_agent_keeper.py:_enabled()`) has not actually held since the cutover. Any operator-triggered manual respawn via
the dashboard's spawn modal for `main`/`review` also 400s today unless the operator crafts a workaround boot_prompt by
hand (not a reasonable expectation).

## Recommended fix

Either of these closes the gap (pick whichever keeps `prompts.py`'s "no truncation risk" invariant from its 2026-07-10
docstring intact — do not re-introduce a giant pasted template):

1. **(preferred) Decouple agent_id linkage from string-matching the stub.** Instead of grep-and-replace against
   free-form prose, have `_compose()` for slot-less roles emit one literal, greppable line (e.g.
   `AGENT_ID_HINT: <PLACEHOLDER>`), and have `agents/main.md` / `agents/review.md`'s STEP 1 register-curl instructions
   read: "if a session variable `AGENT_ID_HINT` is present and non-placeholder, include it as `"agent_id": "<value>"` in
   your register curl body." Update `spawn_agent_endpoint` and `AgentKeeper._spawn()` to replace that one dedicated
   placeholder token instead of grepping for `'"role": "<role>"'`.
2. **(alternative, smaller diff)** Keep the current grep-and-replace design but make `_compose()` embed a literal
   register-payload hint line containing `'"role": "<role>"'` (mirroring what I hand-crafted as the live workaround) for
   the `else` (slot-less) branch of `_compose()`, and update `main.md`/`review.md` to instruct copying that fragment
   into their own register curl body verbatim.

Whichever is chosen, also **audit `monitor` role** (also slot-less per `prompts.py`) for the same break.

## Todos

- [x] ✅ [BACKEND] P0. Reproduce the bug as a failing test FIRST: in `tests/test_prompts.py` or a new
      `tests/test_agent_spawn_endpoint.py`, add a test that calls
      `prompts.render("main", server_url=..., machine=...,     rc_url=..., model=..., effort=..., thinking="")`
      (matching `main_agent_keeper._spawn()`'s real call) and asserts the composed stub contains the literal substring
      `'"role": "main"'` — confirm this test FAILS on current `main` (repo: agent-orchestrator). —
      agent-orchestrator@43dc13d. Chose fix option 1 (preferred, decoupled token), so the added
      `test_slotless_stub_carries_agent_id_hint_placeholder` asserts the new `AGENT_ID_HINT: <PENDING>` token instead of
      the old `'"role": "main"'` substring — confirmed failing
      (`AttributeError: no attribute     'AGENT_ID_HINT_PLACEHOLDER'`) before the fix landed.
- [x] ✅ [BACKEND] P0. Implement the chosen fix (see "Recommended fix" above) in `server/prompts.py` `_compose()` for
      the slot-less branch, so the failing test from the prior todo goes green (repo: agent-orchestrator). —
      agent-orchestrator@43dc13d. Implemented option 1: `_compose()` now emits a dedicated `AGENT_ID_HINT: <PENDING>`
      literal line for slot-less roles (new `prompts.AGENT_ID_HINT_PLACEHOLDER` constant); repro test goes green.
- [x] ✅ [BACKEND] P0. Update `server/routes/agents.py::spawn_agent_endpoint` and
      `server/main_agent_keeper.py::AgentKeeper._spawn()` if the chosen fix changes what substring/token they inject
      against (both currently hardcode `f'"role": "{role}"'` — keep them in sync with whatever `_compose()` now emits)
      (repo: agent-orchestrator). — agent-orchestrator@43dc13d. Both spawn paths now replace
      `f"AGENT_ID_HINT: {prompts.AGENT_ID_HINT_PLACEHOLDER}"` instead of grepping `'"role": "<role>"'`; updated the one
      existing test that mocked the old fixture shape
      (`test_main_agent_keeper.py::test_spawn_generates_and_persists_session_id`) to the new token so it keeps
      exercising the real `_spawn()` body. Full `quality-gates.sh` green (1205 passed, 1 skipped) + shipped via Pass-1
      QG → Pass-2 `quickmerge --agent`. Also updated `agents/main.md` + `agents/review.md`'s STEP 1 register-curl prose
      (and `agents/monitor.md`'s, for consistency — same slot-less spawn path) to read `AGENT_ID_HINT` from the boot
      text and include it as `"agent_id"` when non-placeholder — without this doc-side change the server-side fix alone
      would still reproduce the split-identity artifact from todo 7 (freshly-spawned agent registers under a NEW id
      instead of upserting the pre-created row). The `monitor` role's own P1 test-coverage audit (below) is still open —
      this only fixed its doc prose for consistency.
- [ ] [BACKEND] P0. Add an end-to-end regression test for `POST /api/agents/spawn` with `role="main"` and
      `role="review"` that exercises the REAL `spawn_agent_endpoint` body (not a mock of the whole function) through the
      agent_id-injection step, asserting it does NOT 400 and that the injected `agent_id` actually lands in the
      resulting boot_with_id string — mock only the tmux-spawning side effects (`tmux_spawn.spawn_named` /
      `_dismiss_bypass_warning` / pane-scrolling), not the string-surgery itself (repo: agent-orchestrator).
- [ ] [BACKEND] P1. Replace `test_main_agent_keeper.py::test_spawns_when_session_absent`'s
      `patch.object(keeper, "_spawn", return_value=True)` with a variant that also runs the REAL `_spawn()` body at
      least once (mocking only `tmux_spawn.spawn_named` + the DB session, not `_spawn` itself) so a future refactor of
      `prompts.render()` output can't silently break this path again without a test noticing (repo: agent-orchestrator).
- [ ] [BACKEND] P1. Audit the `monitor` role (also slot-less per `prompts.py`'s `_WORKER_BASE_ROLE` != monitor) for the
      same agent_id-injection break — add the same test coverage if a `monitor` spawn path exists and is affected (repo:
      agent-orchestrator).
- [x] ✅ [BACKEND] P2. Clean up the orphaned pre-created agent row from my live workaround spawn (`agt-d0c383`, tmux
      session `orch-agent-main-d0c383` — the real live main agent self-registered as a different id, `agt-770694`,
      because it composed its own register curl from `main.md` without picking up my ad-hoc hint) — either delete the
      orphan row via the dashboard/DB or, if the chosen fix in this plan makes the linkage work correctly, verify a
      fresh test-spawn no longer produces this split-identity artifact (repo: agent-orchestrator). — agent-orchestrator
      (no code change; the earlier P0/P1 surgery-fix todos above are still open, so option 2 isn't provable yet).
      Verified via the live API: `agt-d0c383` was already auto-archived (`exit_reason: dead-main-session`,
      `finished_at: 2026-07-13T05:39:41Z`, same instant as the real `agt-770694`), confirming it never appears in the
      live roster (`GET /api/agents` default view). Ran the dashboard-sanctioned cleanup path,
      `DELETE /api/agents/agt-d0c383` →
      `{"ok": true, "agent_id": "agt-d0c383", "killed_tmux":     "orch-agent-main-d0c383", "retained": true}`; row now
      `status: finished`, `exit_reason: operator-deleted` (the code's Plan-B retention design intentionally soft-deletes
      rather than hard-deleting agent rows, so this is the correct/only sanctioned "delete" — a raw DB hard-delete would
      fight that documented design).
- [ ] [BACKEND] P2. Run `bash scripts/quality-gates.sh` full and ship via the standard Pass-1 QG → Pass-2 quickmerge
      --agent flow; flip this plan's checkboxes with `<repo>@<sha>` evidence per commit (repo: agent-orchestrator).

## Codex SSOTs

- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (main-agent-keeper always-on contract)
