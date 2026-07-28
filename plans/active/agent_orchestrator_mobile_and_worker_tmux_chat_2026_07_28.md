---
doc_type: plan
title: Agent-orchestrator mobile parity + worker-tmux chat
summary:
  Operator (Ikenna) wants three things — (1) real two-way chat with a plan-dispatch slot worker's tmux session, since
  today only role-agents (main/review/plan_reconciler) have real bidirectional chat via RoleChat while slot workers only
  get a one-way async note; (2) the existing desktop backlog/done/queued stats (BacklogSummary/KpiRow/
  BacklogDetailModal) wired into the dashboard's existing MobileTriage mobile view, where they currently don't render at
  all; (3) the existing desktop role-chat (RoleChat/AgentsPanel) wired into MobileTriage too, whose "Agents" tab today
  only shows a read-only AgentTypesPanel roster. No new network/auth infra needed — a public HTTPS dashboard domain
  already exists and a phone can already log in with the same JWT flow as a laptop.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [orchestrator, dashboard, mobile, chat, tmux, ui]
related:
  [
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-07-28"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
last_updated: "2026-07-28"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  Operator request 2026-07-28 (Slack, 9:27am thread), scoped via AskUserQuestion in the same session — operator's own
  words were "on the pc i can already chat with aorchestrator. i also wanna be able to chat with workers tmux.
  furthermore when i open on mobile i wanna be able to use the same features i can on laptop thats it." Pre-task
  conflict-check run against plans/active + issues before authoring (per CLAUDE.md's new pre-task rule) — no existing
  plan covers this; only tangential hit was
  `plans/active/issues/deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07-21.md` (unrelated pre-existing
  deployment-ui mobile-NAV smoke failures, not this feature).
drift_direction: advance-code
---

# Agent-orchestrator mobile parity + worker-tmux chat

## Context (read this before touching code)

Research done 2026-07-28 (two parallel investigation agents) established the current state precisely:

- **Role-chat (main/review/plan_reconciler) already works, desktop only.** `RoleChat` in
  `agent-orchestrator/dashboard/src/layout.tsx` (`AgentsPanel`, `ROLES_ORDER`), wired via `onSendToRole` in
  `dashboard/src/App.tsx`, backed by `POST /api/agents/by-role/{role}/message` +
  `GET /api/agents/by-role/{role}/history` in `server/routes/agents.py`. This is the feature Ikenna means by "on the pc
  I can already chat with agent-orchestrator."
- **Worker-tmux chat does NOT really exist yet.** A plan-dispatch slot worker (`orch-slot-N`) only gets a one-way async
  note via `POST /api/slots/{slot_id}/message` → `enqueue_message` → the worker's own `/loop` drains it on its next poll
  (`take_pending_messages`). The existing `LogViewerModal` (`App.tsx`) is READ-ONLY (renders the worker's Claude JSONL
  transcript via `transcript_log.render_transcript`, with a tmux `capture-pane` fallback) — no compose box, no live
  two-way exchange.
- **The proven send primitive already exists and is safe to reuse.** `tmux_spawn.submit_to_pane(session, text)` does
  `tmux send-keys -l <text>` + `C-m` with a verify-loop confirming the input box cleared — currently only used for boot
  prompts and `nudge()`. This is the "one sanctioned pane-injection instrument" per the research; build on it, don't
  reinvent pane injection.
- **Raw `capture-pane` cannot be the read-back mechanism** — Claude Code runs on the tmux alternate screen, so
  `capture-pane` only ever returns the ~24 visible lines, no scrollback. The durable, complete content is the JSONL
  transcript file (`transcript_log.render_transcript`) — the same source `LogViewerModal` already reads. Worker-chat's
  "read the reply" side must poll/tail THAT, not raw `capture-pane`.
- **Mobile scaffolding already exists but two surfaces aren't wired into it.** The dashboard has a real `isMobile`
  breakpoint (`window.innerWidth < 760`, `App.tsx`) and a dedicated `MobileTriage` component (`mobile-tabs`:
  Triage/Fleet/Agents/Registry/Activity). `BacklogSummary`/`KpiRow`/`BacklogDetailModal` (fed by `GET /api/state`'s
  `backlog_summary`) are wired ONLY into `DesktopLayout` — none of `MobileTriage`'s tabs render them. `MobileTriage`'s
  "Agents" tab renders `AgentTypesPanel` (read-only roster), not `AgentsPanel`/`RoleChat` — so chat is unreachable on
  mobile today even though the JS/CSS mobile-mode scaffolding is real.
- **No new network/auth work needed.** A public HTTPS front door already exists —
  `https://agent-orchestrator.odum-research.com` (Firebase Hosting SPA) → `api.agent-orchestrator.odum-research.com`
  (nginx :443) → backend :8765 on the orchestrator EC2 box. A phone reaches this exactly like a laptop, same
  JWT/Argon2id login (`server/auth.py`). Raw `:8765` has no public inbound rule, but that's irrelevant to a browser
  client — it only ever talks to the public TLS domain.
- **Security-relevant fact from the research**: `submit_to_pane` is genuine arbitrary-keystroke injection into a live
  `claude --dangerously-skip-permissions` shell holding real repo/AWS/GCS credentials. `server/auth.py` currently lets
  localhost-direct/loopback callers bypass JWT via `ALLOW_ANONYMOUS=True`. The new worker-chat SEND route must not
  inherit that bypass just because it happens to be called from the same box the backend runs on.

## Track 1 — Worker-tmux chat (new capability; build once, both desktop and mobile consume it)

- [x] [BACKEND] P0. Add a send-to-pane chat endpoint for a specific slot (extend `POST /api/slots/{slot_id}/message` or
      add a sibling route in `server/routes/slots_ops.py`) that calls `tmux_spawn.submit_to_pane(session, text)`
      directly against that slot's live tmux session — NOT the existing `enqueue_message`/DB-queued path, which only
      surfaces on the worker's own next poll. Definition of done: sending a message via this endpoint causes the target
      slot's Claude session to visibly react (its next transcript entry reflects having received the text) within the
      same interactive turn, not after a poll-cycle delay. — agent-orchestrator@9e9b921 — shipped
      `POST /api/slots/{slot_id}/message-live` (sibling route in `server/routes/slots_ops.py`), calling
      `tmux_spawn.submit_to_pane` synchronously against the resolved live tmux session (stored `tmux_session` or the
      derived canonical `orch-slot-N` name, mirroring `/log`'s existing fallback). Proven by
      `tests/test_slot_message_live.py::test_message_live_calls_submit_to_pane_with_correct_session_and_text` (asserts
      `submit_to_pane` is called with the exact session name + text — no DB enqueue in the path) +
      `test_message_live_falls_back_to_derived_session_when_stored_missing` (fallback case) +
      `test_message_live_404_when_no_live_tmux_session` (no live session → 404, submit never called).
- [x] [BACKEND] P0. Add a "read the reply" endpoint/mechanism that tails `transcript_log.render_transcript` for the
      named slot's session, returning only entries newer than a client-supplied offset/cursor (do not re-read the whole
      transcript every poll). Definition of done: after a Track-1-send, polling this endpoint surfaces the worker's
      actual new output within one poll interval, sourced from the JSONL transcript (not `capture_pane`, which cannot
      see scrollback under the alt-screen). — agent-orchestrator@9e9b921 — shipped
      `GET /api/slots/{slot_id}/transcript-tail` (`server/routes/slots_ops.py`) backed by new
      `transcript_log.render_transcript_since(path, since_offset, max_lines) -> TranscriptTail` (byte-offset cursor;
      only complete lines advance the offset so a poll landing mid-write doesn't skip the in-flight line; an
      out-of-range offset resets to a fresh first-poll). Proven by
      `tests/test_transcript_log.py::test_render_since_returns_only_new_entries_after_offset` (poll → append → poll
      again with the returned offset → only the new entries come back, old ones absent) +
      `test_render_since_does_not_advance_past_incomplete_trailing_line` +
      `tests/test_slot_transcript_tail.py::test_transcript_tail_second_poll_with_returned_offset_sees_only_new_content`
      (same proof at the route level, against a real temp transcript file, not a mocked function).
- [x] [BACKEND] P0. Exclude the new send-to-pane route from `ALLOW_ANONYMOUS`/loopback-bypass in `server/auth.py` —
      require the same JWT bearer auth as the rest of the authenticated dashboard API regardless of caller origin.
      Definition of done: a request to the new endpoint without a valid JWT is rejected (401/403) even when called from
      localhost on the orchestrator box itself. — agent-orchestrator@9e9b921 — shipped `auth.require_authenticated_user`
      (rejects the anonymous-claims fallback unconditionally — no `ALLOW_ANONYMOUS`/trusted-loopback bypass, composes on
      top of `get_current_user`) wired as `STRICT_AUTHED_DEPS` (`server/routes/_deps.py`) on `/message-live` ONLY
      (`/transcript-tail` stays on ordinary `AUTHED_DEPS`, matching its read-only blast radius). Proven by
      `tests/test_require_authenticated_user.py::test_loopback_no_token_is_rejected_even_though_get_current_user_would_allow_it`
      (asserts the baseline: `get_current_user` DOES grant anonymous access to this exact request, then asserts
      `require_authenticated_user` rejects the identical request with 401) +
      `test_loopback_no_token_rejected_even_with_allow_anonymous_true` (fails closed even with the permissive flag
      explicitly True) + `tests/test_slot_message_live.py::test_message_live_route_is_wired_to_strict_auth_dependency`
      (introspects the actual FastAPI route object to confirm `/message-live` carries `auth.require_authenticated_user`
      — not just that the helper function works in isolation).
- [ ] [UI] P1. Add a compose box + live-updating transcript view for a single slot — either extend `LogViewerModal` or
      add a sibling component — wired to the two Track-1 endpoints above. Definition of done: opening a slot's detail
      view on desktop shows an input box; submitting text sends via the new send-to-pane route; the visible transcript
      updates with the worker's next output without a manual page refresh.
- [ ] [UI] P2. Playwright regression spec covering: open a slot's chat view, send a message, assert the transcript shows
      new content after the worker's next output. Cite the spec file in the done-claim per
      `/codex/06-coding-standards/ui-testing-layers.md`'s playwright gate.

## Track 2 — Mobile parity: backlog/done/queued stats

- [ ] [UI] P1. Wire `BacklogSummary` + `KpiRow` into `MobileTriage` (either a new tab or folded into the existing
      "Fleet" tab) sourced from the same `GET /api/state` `backlog_summary` desktop already uses — no new backend work.
      Definition of done: loading the dashboard at a <760px viewport shows the same queued/dispatched/done/cancelled
      counts a desktop user sees.
- [ ] [UI] P2. Wire `BacklogDetailModal` (the sortable/filterable full task table) into the mobile view, reachable from
      the new mobile backlog-stats surface. Definition of done: a mobile viewport can open the same detail table desktop
      users reach via the "Detail" button, with the same filter/sort behavior (list layout instead of a wide table is
      fine — content parity is the bar, not identical visual layout).

## Track 3 — Mobile parity: chat

- [ ] [UI] P1. Replace or extend `MobileTriage`'s "Agents" tab so it renders the real `AgentsPanel`/`RoleChat`
      (main/review/plan_reconciler) instead of the read-only `AgentTypesPanel`. Definition of done: sending a message to
      a role from a <760px viewport reaches `POST /api/agents/by-role/{role}/message` and the reply renders in the
      mobile chat UI, matching desktop behavior.
- [ ] [UI] P1. Surface Track 1's worker-tmux chat in the mobile view (a per-slot chat screen reachable from the mobile
      "Fleet"/"Triage" tab). Definition of done: from a phone, opening a slot shows the same compose-box +
      live-transcript UI Track 1 shipped for desktop.
- [ ] [UI] P2. Playwright mobile-viewport regression specs for both of the above (role-chat and worker-chat reachable
      and functional at the `isMobile` breakpoint). Cite per `/codex/06-coding-standards/ui-testing-layers.md`.

## Track 4 — Sanity check before declaring done

- [ ] [REVIEW] P1. From an actual mobile browser (or a devtools mobile-viewport emulation at minimum), load
      `https://agent-orchestrator.odum-research.com`, log in with the existing JWT flow, and walk all three new mobile
      surfaces (backlog stats, role chat, worker chat) end to end. Definition of done: all three work from the public
      domain exactly as they do on desktop — this is the actual acceptance bar the operator asked for ("the same
      features I can on laptop").

## Progress Log

- 2026-07-28 — Plan authored. Scoped via operator AskUserQuestion answers (human-driven plan, `assigned_vm: NA`) + two
  parallel research agents establishing exact current-state file/symbol references above. No implementation done yet.

- 2026-07-28 — **Track 1 backend (all three `[BACKEND] P0` todos) shipped: `agent-orchestrator@9e9b921`.** Dispatched
  autonomously (`/autonomous`) to implement + ship the send-to-pane endpoint, cursor-based transcript-tail read-back,
  and the strict-auth exclusion, with real passing tests proving each.

  **Decision under ambiguity #1 — inherited uncommitted WIP found at task start.** On starting this phase, the
  agent-orchestrator working tree already had _uncommitted, unstaged_ changes to exactly the four files this task needed
  to touch (`server/auth.py`, `server/routes/_deps.py`, `server/routes/slots_ops.py`, `server/transcript_log.py`), with
  docstrings explicitly citing this plan's slug and Track 1 by name — evidently a prior attempt at this same dispatch
  that never reached `quality-gates.sh`/quickmerge. No `.agent-claim` marker existed for it and file mtimes were ~55 min
  old (≫120s), so per the workspace's dirty-WIP liveness rule (dead claim → inherit + commit) this was treated as
  inheritable, not foreign-in-progress work to protect around. Read every diff in full, cross-checked each new
  function/route against the real call signatures it used (`tmux_spawn.submit_to_pane`/`has_session`/`session_name`,
  `state_store.get_slot`/`log_activity`, `transcript_log.resolve_transcript_path`) and against the established sibling
  route `slot_log` for pattern-fidelity, confirmed it was complete and correct, then finished the phase (venv sync,
  tests, gate, ship) on top of it rather than discarding it and re-implementing from scratch. Net new code beyond what
  was inherited: all 4 test files (30 tests) and the venv sync.

  **Decision under ambiguity #2 — pre-existing environment drift blocked even importing the code.** `.venv` had
  `fastapi==0.136.1` installed while the committed `uv.lock` pinned `0.140.7` (confirmed pre-existing and
  code-unrelated: reproduced identically with the inherited WIP stashed away against a clean HEAD). Ran
  `uv sync --frozen` (frozen so it could not touch `uv.lock` itself — no re-lock, per the workspace's
  no-internal-dep-relock rule) to bring the local dev `.venv` in line with the already-committed lockfile. This sandbox
  checkout is a separate machine from the live EC2 orchestrator process, so this had zero effect on the running service.

  **What shipped** (`agent-orchestrator@9e9b921`, `docs(plans):` flip is this same commit's PM-side companion):
  - `POST /api/slots/{slot_id}/message-live` — synchronous tmux-direct send, `STRICT_AUTHED_DEPS`
    (`auth.require_authenticated_user`). Request/response shape documented in full in the report back to the dispatching
    agent (also captured below for the Frontend phase).
  - `GET /api/slots/{slot_id}/transcript-tail?since_offset=N&max_lines=M` — cursor-based incremental transcript
    read-back, ordinary `AUTHED_DEPS` (read-only). Backed by new `transcript_log.render_transcript_since` /
    `TranscriptTail` dataclass.
  - `auth.require_authenticated_user` + `_deps.STRICT_AUTHED_DEPS` — the no-anonymous-bypass dependency, applied ONLY to
    `/message-live` (not `/transcript-tail`, which stays on the ordinary dependency — a read-only route has a smaller
    blast radius than one that injects keystrokes into a live credentialed shell).

  **Tests** (30 total, all passing; also verified failing-before/passing-after is not applicable since this is new code,
  so instead each test was verified to actually exercise the mechanism it claims — e.g. the auth test asserts the SAME
  request shape passes under `get_current_user` and fails under `require_authenticated_user`, so it cannot pass
  vacuously):
  - `tests/test_slot_message_live.py` (6 tests) — send-endpoint behavior + route-level strict-auth wiring assertion.
  - `tests/test_slot_transcript_tail.py` (6 tests) — read-back route end-to-end against a real temp transcript file +
    route-level ordinary-auth wiring assertion.
  - `tests/test_require_authenticated_user.py` (7 tests) — the auth dependency itself, including the
    fails-closed-even-under-ALLOW_ANONYMOUS=True case.
  - `tests/test_transcript_log.py` (+11 tests appended) — `render_transcript_since` cursor math (new-entries-only,
    incomplete-trailing-line handling, offset-past-EOF reset, truncation+flag).
  - Re-run with: `cd agent-orchestrator && bash scripts/quality-gates.sh` (full gate, green: ruff/format/frontmatter/
    basedpyright/1889 passed+1 skipped pytest/dashboard tsc+vitest — dashboard untouched this phase, confirmed no
    regression) or narrowly:
    `.venv/bin/python -m pytest tests/test_slot_message_live.py tests/test_slot_transcript_tail.py tests/test_require_authenticated_user.py tests/test_transcript_log.py -q`.

  **Not done this phase (by design, out of scope)**: the `[UI]`/`[REVIEW]` todos under Track 1 (compose box + Playwright
  spec) and all of Track 2/3/4 — this phase's dispatch was scoped explicitly to the three `[BACKEND]` todos. The live
  orchestrator process was NOT restarted (per explicit instruction for this phase); the shipped commit reaches it
  automatically via the existing `ao-self-pull.sh` cron (≤15 min, or instant for these `server/**.py` changes via the
  uvicorn `--reload` watch) with no action needed.
