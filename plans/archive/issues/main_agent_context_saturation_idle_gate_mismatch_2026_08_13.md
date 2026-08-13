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
status: resolved
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
resolved_by: agent-orchestrator@acc41b1a00
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

> **🟢 ARCHIVED 2026-08-14** — status=resolved. P1 fix shipped (`agent-orchestrator@acc41b1a00`); all 3 follow-up
> investigation todos closed with real evidence (transcript-measured token-growth rate, 08-11 spike investigated and
> disconfirmed, tmux_session_lost recurrence checked) rather than left open. See Progress Log for the full trail.

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

- ~~Whether the ~23-31-minute time-to-saturation is itself abnormal~~ — **measured, see todo below**: main's raw
  tokens/min growth rate is NOT abnormally fast — if anything slightly slower than a worker's. The real driver is
  duration, not rate: main runs continuously for hours with no natural task-boundary reset, unlike a worker whose
  session is inherently bounded by task completion.
- ~~Whether the 2026-08-11 68-spawns/day spike has its own distinct trigger~~ — **investigated, see todo below**: NOT
  the idle-gate mismatch (didn't exist yet that day) and NOT the whole-fleet kill-server bug (0 matching events); driven
  by 2,607 individual `tmux_session_lost` events that day, cause unconfirmed, not currently reproducing.
- ~~Whether the 16:22:49 `tmux_session_lost` false-positive-looking event recurs~~ — **checked, see todo below**: 3 more
  `orch-agent-main` `tmux_session_lost` events occurred in the following 5 hours, but each landed within 1-6 minutes of
  a `main_agent_autospawned` — a signature the ORIGINAL false positive did not have (no subsequent autospawn, same tmux
  pane persisted). Reads as genuine respawns, not the same artifact recurring — not independently pane-verified
  per-instance, so held as a read, not a proof.

## Todos

- [x] ✅ [BACKEND] P1. **DONE 2026-08-13 — `agent-orchestrator@acc41b1a00`.** Gave the idle-streak compact gate a
      role-aware policy: new `context_force_idle_observations_main` tunable (default 1), applied only to `role=main` in
      `_maybe_force_compact`; `role=review` keeps the original 3-tick requirement unchanged (no evidence review has the
      same problem). The two non-streak safety checks (`pane_input_pending`, `_pane_has_child_processes`) still run
      unconditionally after the threshold is met, so this only removes the debounce-against-a-flicker margin, not the
      don't-stomp-active-work guard. `quality-gates.sh` green: 3604 pytest (2 new/updated), 323 vitest. Original text
      preserved below for provenance — a short, bounded reply (an `agent_replied` ack under some token/duration
      threshold) should not fully reset main's idle streak the way a real multi-turn task would for a worker — main's
      whole role is to be interrupted briefly and return to idle, not to work continuously. Candidate: count "idle since
      last real work" rather than "idle since last activity of any kind", or lower the consecutive-tick requirement
      specifically for `role=main`. Done when: a traced main instance that is repeatedly ack-interrupted still reaches a
      forced compact within a bounded time of first hitting the guidance threshold (e.g. <10 min, not 14-40 min).
- [x] ✅ [INVESTIGATE] P2. **DONE 2026-08-13/14 — measured directly from session transcripts, hypothesis DISCONFIRMED.**
      Parsed real `message.usage` records from two completed episodes: main's session
      `d90087a1-b098-4f4a-8261-f2fe80225596` (19:29:09-21:27:38, 605 usage-bearing turns, excluding the known "synthetic
      zero" tail-record measurement trap already documented in
      `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`) and a comparable
      worker episode (slot 3, `81f1c644-7baf-4bb0-a615-045cd553013a`, 2026-08-11, 99 turns). **Main: ~2,070
      tokens/min**, smooth/steady growth (long gaps between turns — waiting on the next real message). **Worker: ~3,281
      tokens/min**, bursty (one 6-second gap alone added ~40K tokens during active tool-call chaining). Main's raw burn
      rate is NOT abnormally fast — it is, if anything, slightly slower than a worker's mid-task rate. Also notable: a
      fresh main spawn starts at ~54,666 tokens already loaded (its own bootstrap: role files,
      `SUB_AGENT_MANDATORY_RULES.md`, the checkpoint doc), not near-zero. **Conclusion: main's saturation problem is
      DURATION, not rate** — it runs continuously for hours with no natural task-boundary reset the way a worker's
      task-scoped session gets, so a steady, unremarkable per-minute rate still accumulates to saturation over a long
      enough unbroken stretch. This means a context-REDUCTION fix (trimming main's own system/role prompt) would not
      meaningfully help; the already-shipped idle-gate fix (todo 1 above, letting main actually compact promptly instead
      of stalling at 99%) is the right lever, not a burn-rate optimization.
- [x] ✅ [INVESTIGATE] P2. **DONE 2026-08-13/14 — measured, hypothesis DISCONFIRMED, real cause still open.** Pulled
      08-11's event counts directly: `context_force_idle_gate_blocked` = **0** that day — the idle-gate mechanism this
      doc's own fix targets didn't exist yet (added ~08-09/08-10), so it structurally cannot explain the spike. Also NOT
      the whole-fleet kill-server bug from `/plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md`
      — 0 of that day's events carry the `tmux_server_alive=false` whole-server-death signature. The real mechanical
      driver: **2,607** individual `tmux_session_lost` events fleet-wide that single day (61 scoped directly to
      `orch-agent-main`), a rate wildly above every other sampled window this session (single-to-low-double-digits per
      30min). Not chased further — current live rates (checked 2026-08-13 ~16:00-20:00Z) are back to normal, suggesting
      whatever drove this either self-resolved or was fixed by unrelated work already, but which fix (if any) is NOT
      confirmed. Leaving as a closed investigation with an honest "cause unknown, no longer reproducing" verdict rather
      than forcing it to fit this doc's own idle-gate hypothesis.
- [x] ✅ [INVESTIGATE] P3. **DONE 2026-08-13/14 — checked, does NOT look like the same recurring artifact.** 3 more
      `orch-agent-main` `tmux_session_lost` events since 16:22:49 (17:08:27, 19:28:09, 21:30:01), each within 1-6
      minutes of a `main_agent_autospawned` (17:14:35, 19:29:09, 21:30:24 respectively) — unlike the original 16:22:49
      instance, which had NO subsequent autospawn and the same tmux pane (creation timestamp unchanged) persisted right
      through it. The tight autospawn correlation on all 3 later instances reads as genuine respawns/recycles being
      logged as `tmux_session_lost` (the event type doubles as a generic "this main instance is gone" marker, not
      exclusively a death signal), not a repeat of the specific liveness-check false-positive caught live on 08-13. Not
      independently pane-verified per-instance (would need a live capture at the moment of each event, not available
      after the fact) — held as a read of the correlation pattern, not a proof.

## Progress Log

- 2026-08-13: filed per direct operator ask, live SSM evidence gathered and cited above (240-respawn historical count,
  7-day daily breakdown, one instance traced end-to-end through the idle-streak gate to its eventual forced compact). No
  fix attempted yet — this is the diagnosis, not the resolution.
- 2026-08-13 (same session, follow-up per operator "fix everything"): shipped the P1 role-aware fix
  (`agent-orchestrator@acc41b1a00`) within the hour of filing — see todo 1 above for the full change description.
  Remaining 3 todos (token-growth-rate measurement, the 2026-08-11 spike explanation, and the transient
  `tmux_session_lost` false-positive) are still open investigation, not fixes — no live-traced evidence yet on any of
  them.
