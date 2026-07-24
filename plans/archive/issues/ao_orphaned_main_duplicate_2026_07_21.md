---
doc_type: issue
title: Orphaned old-main process survives a restart → two mains on the dashboard + a second account burning
summary:
  On a 12:45 UTC orchestrator restart the old main's claude process survived (KillMode=process, deliberate). Its tmux
  server had meanwhile lost the default socket, so the keeper's has_session(orch-agent-main) read False, reaped the
  record, and spawned a REPLACEMENT main beside the still-running orphan. The orphan kept /poll-ing and
  update_agent_ping's restore-on-ping flipped its archived row back to active every tick → the dashboard showed TWO
  mains for ~2 days and a second account (sub-c-ikenna-odum) burned. kill_session could never reach it (it only talks to
  the current socket; the orphan was stranded on a prior, socketless server generation). Manually killed; root-cause fix
  shipped (agent-orchestrator@4f34391).
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [orchestrator, main-agent, singleton, orphan-process, tmux, restore-on-ping, self-healing, account-burn]
related:
  [
    plans/active/issues/orphaned_workers_on_tmux_loss_stale_dispatch_2026_07_17.md,
    plans/active/ao_worker_lifecycle_dispatch_context_2026_07_21.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
created: 2026-07-21
parent_epic: infrastructure_master
priority: P1
source: [agent-orchestrator main_agent_keeper / orphan_reap / update_agent_ping / tmux_spawn socket lifecycle]
assigned_vm: NA
resolved_by: agent-orchestrator@4f34391
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-21
---

## What the operator saw

> "why do i see two different orchestrator agents in the ui" … "why the fuck there are two ones in the first place?"

Two `role: main` / `agent_kind: orchestrator` rows, both `status: active, online: true`, with **identical** `last_msg`
and `context_used_pct` — differing only by `account_id` (`sub-c-ikenna-odum` vs `sub-d-odum1default`).

## Root cause (evidence-backed)

One live main, but a leaked old-main process kept its ghost row alive:

| UI row     | account            | session (claude) | process                                 | reality                   |
| ---------- | ------------------ | ---------------- | --------------------------------------- | ------------------------- |
| agt-d226b8 | sub-d-odum1default | 4cd9fd04         | pid 3850500 (in live `orch-agent-main`) | the real, current main    |
| agt-b8247c | sub-c-ikenna-odum  | d84b017d         | pid 1851465 (orphan, off-socket)        | ghost — still `/poll`-ing |

Chain of causation:

1. **`KillMode=process`** (orchestrator.service, deliberate — root-caused 2026-05-20 so workers survive a backend
   redeploy) means a `systemctl restart` kills only uvicorn. The old main's claude process keeps running.
2. On the **12:45 restart** the old main's tmux server had lost the default socket (three server generations were found
   alive, each on a different socket inode — `16016` Jul 14, `185095586` Jul 17, `381846408` Jul 21; only the newest
   held `/tmp/tmux-1000/default`; the old two were socketless and invisible to `tmux ls`). So the keeper's
   `has_session("orch-agent-main")` read **False** → journal
   `12:45:19 AgentKeeper reaped … ('agt-b8247c', 'dead-main-session')` → `12:46:53 spawned main agent agt-d226b8`.
3. The old main **process** was never killed. `kill_session` only talks to the current socket, so it cannot reach a main
   stranded on a prior server generation. The orphan kept running its `/loop` and `/poll`-ing as agt-b8247c.
4. **`update_agent_ping` restore-on-ping** (`state_store/agents.py`) flips any pinging archived row back to `active`.
   The code comment even asserted _"a superseded main can't resurrect itself — its session was already replaced, so it
   isn't pinging"_ — **false here**: the orphan process was still pinging. So the reaper archived b8247c each tick and
   the orphan's next ping resurrected it → permanent flapping duplicate + a second account burning.

**A4 was NOT the trigger** (zero A4 "stale socket / unlinking" warnings in the retained journal at 12:46) — see residual
todo below; A4 is a distinct latent bug that _can_ orphan a live server but did not fire this time.

## Remediation

- **Immediate (manual, done):** SIGTERM'd the orphan mains (1851465 = b8247c ghost; 2165096 = a week-old stray from
  Jul 14) + their now-empty socketless tmux servers. Dashboard collapsed to one main; verified 1 opus main process.
- **Root-cause fix (shipped + deployed — agent-orchestrator@4f34391):**
  - `orphan_reap.reap_orphan_agent_session(main)` — process-level reap of a **singleton agent-session orphan**, matched
    by the `CLAUDE_CONFIG_DIR` we set (never a name grep), excluding the live-pane occupant
    (`pid_belongs_to_live_session`), anchored on a live session (a transient tmux hiccup cannot misfire), honouring
    `boot_grace_seconds`. Wired into `AgentKeeper.tick_once` (always-live — a singleton has exactly one legit occupant).
  - `update_agent_ping` — never restore-on-ping a `main` that has a **newer-registered sibling** (definitionally
    superseded). Non-main restore-on-ping is unchanged.
  - Tests: `test_orphan_process_reap.py` (kill orphan / no-op without live anchor / spare within boot-grace),
    `test_reap_orphan_agents.py` (superseded main not resurrected; newest main + non-main still restore). QG green;
    deployed via clean restart; verified DB-locks=0, one main row, one main process.

## Residual open work

- [ ] [BACKEND] P2. **A4 stale-socket recovery unlinks without killing the server** — `tmux_spawn.py` A4 recovery
      (`os.unlink(_TMUX_DEFAULT_SOCKET)` + retry on "address already in use"/"error connecting") removes only the socket
      _filename_; a live-but-wedged server still holding the socket inode is **orphaned** (its main lingers), not
      killed. The `"error connecting"` substring match is also broad enough to false-positive on a healthy server. Fix:
      before unlinking, `tmux -S <socket> kill-server` (best-effort) so any live server on that socket is torn down, not
      orphaned. Latent (did not fire in this incident) but is a second, independent path to the same leak.
- [ ] [BACKEND] P2. **Wire `reap_orphan_agent_session` for the REVIEW singleton too** — the helper is generic (any
      singleton `orch-agent-<role>` session) but only the `main` is wired into the keeper. A leaked review process would
      still linger. Add the review session to the keeper's per-tick reap.
- [ ] [BACKEND] P3. **Investigate WHY the default socket is lost on restart** — the deeper trigger. `has_session` read
      False at 12:45 while the old server + main were alive; understand what strands the socket across a restart (tmux
      server dying and leaving a stale socket that the next `new-session` replaces, vs a wedge). If the socket can be
      kept stable across restarts, no orphan is created in the first place. Owner: backend.

## Provenance

Diagnosed live from the planning VM: `/proc` scan (three tmux server generations + socket inodes), process cmdlines
(`--session-id` ↔ `claude_session_id` ↔ agent row), journal reconstruction of the 12:45 restart, and the
orchestrator.service unit (`KillMode=process`). Fix committed agent-orchestrator@4f34391, deployed 2026-07-21 ~15:17
UTC.
