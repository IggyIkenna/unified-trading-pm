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

- [ ] [BACKEND] P0. Add a send-to-pane chat endpoint for a specific slot (extend `POST /api/slots/{slot_id}/message` or
      add a sibling route in `server/routes/slots_ops.py`) that calls `tmux_spawn.submit_to_pane(session, text)`
      directly against that slot's live tmux session — NOT the existing `enqueue_message`/DB-queued path, which only
      surfaces on the worker's own next poll. Definition of done: sending a message via this endpoint causes the target
      slot's Claude session to visibly react (its next transcript entry reflects having received the text) within the
      same interactive turn, not after a poll-cycle delay.
- [ ] [BACKEND] P0. Add a "read the reply" endpoint/mechanism that tails `transcript_log.render_transcript` for the
      named slot's session, returning only entries newer than a client-supplied offset/cursor (do not re-read the whole
      transcript every poll). Definition of done: after a Track-1-send, polling this endpoint surfaces the worker's
      actual new output within one poll interval, sourced from the JSONL transcript (not `capture_pane`, which cannot
      see scrollback under the alt-screen).
- [ ] [BACKEND] P0. Exclude the new send-to-pane route from `ALLOW_ANONYMOUS`/loopback-bypass in `server/auth.py` —
      require the same JWT bearer auth as the rest of the authenticated dashboard API regardless of caller origin.
      Definition of done: a request to the new endpoint without a valid JWT is rejected (401/403) even when called from
      localhost on the orchestrator box itself.
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
