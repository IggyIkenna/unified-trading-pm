---
doc_type: issue
title:
  Main-role agent saturates context roughly every 30-50 minutes and can sit pinned at ~99% for 20-30+ minutes before a
  forced compact fires — the idle-streak gate that protects a compact from interrupting mid-turn work structurally
  disadvantages "main" specifically, since it is the fleet's always-interrupted coordinator and rarely accumulates the
  required consecutive idle ticks
summary: >-
  Operator asked directly ("I don't see any progress on the main context bloating. Had this issue for ages... I don't
  know what the real issues are, what docs and plans are on this") after observing the main orchestrator agent
  (agt-bb4a8e) sitting at 99% context, "recycling", for an extended window with no clean respawn. Searched plans/active
  + issues + codex for existing coverage: found extensive, real, actively-tracked engineering on WORKER slot context
  wedging (`/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md` — learned
  per-model context windows, queued-message force-latch bugs, kick/kill/respawn escalation ordering) and the general
  watchdog architecture (`/codex/04-architecture/agent-orchestrator-worker-liveness.md`) — but nothing scoped to the
  MAIN role specifically, and nothing addressing WHY context grows this fast in the first place (all existing work is
  reactive recovery, not root-cause prevention). This doc is that missing piece, filed with live evidence, not a
  re-statement of the existing worker-wedge doc.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, main-role, context-lifecycle, compact, idle-gate, throughput]
related:
  - /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md
  - /codex/04-architecture/agent-orchestrator-worker-liveness.md
  - /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md
created: "2026-08-13"
author: main (Claude Code, interactive session)
parent_epic: orchestrator_master
resolved_by:
locked_by:
source: >-
  Operator chat instruction, 2026-08-13: "make to-dos so I can keep track of what you've been trying to achieve,
  because, for example, I don't see any progress on the main context bloating. Had this issue for ages. I don't
  understand. I don't know what the real issues are, what docs and plans are on this, but we should fix it."
assigned_vm: NA
execution_scope: local-only
priority: P1
drift_direction: advance-code
depends_on: []
---

# Main-role agent context saturation — the idle-streak compact gate structurally disadvantages the one role that never stays idle

## What was measured (live, read-only, via SSM against `state.db` on the orchestrator VM, 2026-08-13 ~16:00-16:30Z)

**Historical respawn rate — `main_agent_autospawned` count, all-time**: 240 total since first record 2026-06-27, last
2026-08-13 15:14:15. By day, last 7 days:

| Day        | Count            |
| ---------- | ---------------- |
| 2026-08-07 | 3                |
| 2026-08-08 | 1                |
| 2026-08-09 | 2                |
| 2026-08-10 | 10               |
| 2026-08-11 | 68               |
| 2026-08-12 | 21               |
| 2026-08-13 | 28 (partial day) |

The rate is not flat — it accelerated sharply starting 2026-08-10 and has stayed an order of magnitude above the
2026-08-07/08/09 baseline since. Today's (2026-08-13) 8 most recent spawns before the traced instance were as close as
**7 minutes apart** (12:32:16 → 12:39:41), with gaps ranging 7-53 minutes.

**One instance traced end-to-end** (agt-bb4a8e, spawned 15:14:15Z):

- Fresh spawn 15:14:15 → first self-reported "context at 60%" by 15:37:02 (**~23 minutes** to 60%).
- Hit high context and self-initiated a "RECYCLE" (wrote `main-agent-checkpoint.md`, declared itself ready to be
  replaced) by 15:45:28 (**~31 minutes** from fresh spawn to requesting recycle).
- Then sat in "holding recycle state — keeper respawn pending", continuing to ACK real incoming messages (a fleet
  git-health finding, a slot-14 retire-audit verdict, review routing) for the next **37 minutes**, still at ~99% context
  the whole time, until:
  - 16:22:23 `context_force_idle_gate_blocked` — pct=99, `idle_streak_insufficient` (had 1 of the required 3 consecutive
    idle observations).
  - 16:22:49 `tmux_session_lost` fired for the session — but the underlying tmux pane (`orch-agent-main`) never actually
    changed creation timestamp (still 15:14:15 as of 16:27:55 direct check) and kept emitting normal main-role events
    immediately after, so this reads as a transient liveness-check false-positive, not a real death — flagged here for
    completeness, not asserted as causal.
  - 16:23:26 `proactive_compact_guidance` — nudged again, still 99%.
  - 16:25:29, 16:26:29 `context_force_idle_gate_blocked` — idle_streak climbing 1 → 2 (of 3 required), each check ~60s
    apart.
  - 16:27:35 `forced_compact` **finally fires**, `submitted: true`, `idle_observations: 3`. Notably
    `precompact_forced_at: 2026-08-13T16:13:08` — the precompact was originally scheduled/requested at 16:13:08 but did
    not actually execute until 16:27:35, a **14+ minute delay** gated entirely by needing 3 consecutive confirmed idle
    checks.

## The mechanism (read from the live event sequence, not inferred)

`context_force_idle_gate_blocked` requires **3 consecutive** idle observations (spaced ~60s apart, per the observed
gate-check cadence) before a force-compact is allowed to fire — a deliberate, reasonable safety behavior: do not yank a
compact out from under an agent mid-turn. This is the correct design **for a worker**, which is idle between dispatched
tasks by construction.

**Main is not that kind of role.** It is the fleet's always-on coordinator — it receives review requests, retire-audit
verdicts, BLOCKED-question routing, and git-health alerts continuously, each of which is real incoming work that
plausibly resets or interrupts the idle streak before it reaches 3. The result: main can reach ~99% context in roughly
half an hour from a fresh spawn, and then sit pinned there for another 20-40+ minutes — still acking real messages,
still counted as "working" — before the idle-streak gate finally allows a compact. This is not a broken respawn keeper
(as it first appeared from the dashboard alone); it is the SAME context-lifecycle machinery documented in
`/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md` for workers, but
applied to a role whose whole job structurally defeats the "3 consecutive idle ticks" precondition.

## What is NOT yet established

- Whether the ~23-31-minute time-to-saturation is itself abnormal (i.e., is main's context genuinely growing faster per
  unit of real work than a comparable worker session would, or is this simply what a continuously-interrupted
  coordinator role costs under the existing per-model learned-window arithmetic from the worker-wedge doc). Not measured
  here — would need a token-growth-per-message-handled rate, not just wall-clock time to saturation.
- Whether the 2026-08-11 68-spawns/day spike has its own distinct trigger (a burst of real fleet activity that day
  driving more main interruptions) or is a symptom of this same idle-gate mismatch compounding under load. Not
  investigated.
- Whether the 16:22:49 `tmux_session_lost` false-positive-looking event recurs and is itself worth a targeted fix, or is
  one-off noise.

## Todos

- [ ] [BACKEND] P1. **Give the idle-streak compact gate a role-aware policy.** A short, bounded reply (an
      `agent_replied` ack under some token/duration threshold) should not fully reset main's idle streak the way a real
      multi-turn task would for a worker — main's whole role is to be interrupted briefly and return to idle, not to
      work continuously. Candidate: count "idle since last real work" rather than "idle since last activity of any
      kind", or lower the consecutive-tick requirement specifically for `role=main`. Done when: a traced main instance
      that is repeatedly ack-interrupted still reaches a forced compact within a bounded time of first hitting the
      guidance threshold (e.g. <10 min, not 14-40 min).
- [ ] [INVESTIGATE] P2. Measure main's actual token-growth-per-handled-message rate against a worker's
      token-growth-per-tool-call rate, to establish whether main's ~23-31-minute time-to-saturation is a genuinely
      faster burn rate or an artifact of the role's message volume. Needed before proposing any context-reduction fix
      (e.g. trimming what main's own system/role prompt carries) — don't optimize a rate that hasn't been measured
      against a baseline.
- [ ] [INVESTIGATE] P2. Explain the 2026-08-11 68-spawns/day spike specifically (10x the 08-07/08/09 baseline) — pull
      that day's `agent_message_sent`/`agent_replied` volume for role=main and check whether it correlates with the
      respawn count, which would support (not yet prove) the idle-gate-mismatch hypothesis directly.
- [ ] [INVESTIGATE] P3. Confirm whether the 16:22:49 `tmux_session_lost` on `orch-agent-main` (tmux pane creation
      timestamp unchanged before/after) is a recurring liveness-check false-positive worth its own fix, or one-off.

## Progress Log

- 2026-08-13: filed per direct operator ask, live SSM evidence gathered and cited above (240-respawn historical count,
  7-day daily breakdown, one instance traced end-to-end through the idle-streak gate to its eventual forced compact). No
  fix attempted yet — this is the diagnosis, not the resolution.
