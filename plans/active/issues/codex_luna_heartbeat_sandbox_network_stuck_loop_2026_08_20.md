---
doc_type: issue
title: >-
  Codex/Luna sessions can get stuck in a ~70-minute failed-heartbeat retry loop after their real work
  is done, burning ~1.85M tokens with zero progress — root cause traced live on slot 31
summary: >-
  Investigating an operator report that slot 31 (codex-luna) sat "idle, not doing much" for 20+
  minutes, the real transcript shows something worse than idle: the worker finished and verified its
  actual task (a CI/SIT execution-service fix) by 05:25 UTC, then got stuck retrying its own
  worker-liveness heartbeat (`POST /api/slots/31/heartbeat` against localhost:8765) roughly every 1-3
  minutes from ~05:27 through at least 06:39 — about 70 minutes, well past what the operator noticed —
  with only 6 of ~34 attempts succeeding. Each failed attempt still burns a full turn (6K-78K input
  tokens observed), for a measured total of ~1.85M input tokens on pure retry churn, matching the
  ~1.48M-token jump AO's own state recorded between two checks 40 minutes apart. Failure reasons
  varied turn to turn — missing `AO_HUMAN_TOKEN`/bearer token, a sandbox network permission error
  (`RTM_NEWADDR: Operation not permitted`), and a tool-approval gate asking for explicit operator
  confirmation that never comes in an unattended dispatch — strongly pointing at the Codex CLI
  sandbox's own outbound-network policy being applied inconsistently to this local heartbeat call,
  not a genuinely absent credential (the SAME session successfully delivered the same heartbeat 6
  times). The session was eventually reaped (tmux server gone entirely) sometime after 06:39; AO then
  correctly reports slot 31 as idle with 422 backlog tasks blocked on unrelated gates — that idle
  message describes NOW, not what caused the prior session to loop.
status: open
resolved_by:
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [agent-orchestrator, codex, luna, heartbeat, sandbox, worker-liveness, token-waste, stuck-loop]
related:
  [
    /plans/active/multi_provider_context_billing_reconciliation_2026_08_16.md,
    /plans/active/codex_mcp_tool_use_bridge_2026_08_18.md,
    /plans/active/codex_luna_flex_bridge_2026_08_14.md,
    /plans/active/issues/nvidia_codex_exhaustion_observability_gap_2026_08_19.md,
    /plans/active/issues/idle_lingering_session_reclaim_not_firing_2026_08_19.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
  ]
created: "2026-08-20"
last_updated: "2026-08-20"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/codex_bridge_server.py,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/tmux_pruner.py,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator, interactive session, 2026-08-20: "check on slot 31... now its idle, it wasnt doing much
  and waiting for like 20+ minutes... download its jsonl file... find out if it was wasting the
  tokens or genuinely waiting for some background work to finish." Investigated live via SSM against
  the real orchestrator VM (i-0c9b283b31d6b5ca7) — the slot's real, current transcript
  (2c66e832-5d2e-4934-b27b-cf8d67edf202.jsonl), not a synthetic reproduction.
assigned_role: infra
drift_direction: none
---

# Codex/Luna heartbeat sandbox-network stuck loop — real 70-minute token-burning incident

## The finding

**Verdict: wasting tokens, not genuinely waiting.** The real work was done. Everything after it was a
broken liveness check retrying itself into the ground.

Timeline reconstructed from `orch-slot-31`'s live transcript (352 records) and AO's own `/api/state`:

1. **03:34:40** — slot 31 boots, role `cicd`, account `codex-luna`, task: a failed full-workspace SIT
   run (`reserved_for: ci_escalation`).
2. **03:34–05:07** — real investigation. One `Request timed out`, one operator-answered BLOCKED
   question, then a genuine root-cause turn at **05:07:33**: `execution-service` was missing DeFi
   route/connector wiring; commit `0fae599c` fixed it; failed SIT `32331089802` (9 unreachable venues)
   → green SIT `32332147684` (all 21 repos passed). **This part is real, valuable, verified work.**
3. **05:08–05:25** — proper `/pre-compact` → auto-compact (`preTokens=279064`, matches the
   `auto_boundary_tokens` this session left in the learned-window registry — see the related
   context-window plan), two more manual compactions, two heartbeats that **succeeded** (05:14:30,
   05:24:19), each recapping the same completed fix.
4. **05:27:59 onward — the loop starts.** Every subsequent turn (1-3 minutes apart) is the agent
   trying to send the SAME heartbeat (`POST /api/slots/31/heartbeat`, message "alive; preserving
   completed SIT-fix scope") and reporting a DIFFERENT failure reason nearly every time:
   - `no AO_HUMAN_TOKEN nor the configured token file` / `no bearer token is available`
   - `the sandbox blocked local orchestrator access (RTM_NEWADDR: Operation not permitted)` — a Linux
     netlink permission error, the shape you get from a process denied a low-level network operation
     inside a restrictive sandbox/namespace
   - `the security approval gate rejected the authenticated POST because it would transmit slot/task
     metadata to the external AO service` — i.e. Codex's own tool-permission layer wants an
     interactive human approval that cannot arrive in an unattended background dispatch
   - `the local orchestrator on localhost:8765 is unavailable`
   - Between 05:33:43 and 06:12:50 it intermittently **succeeded** 4 more times (6 total across the
     whole session) — proving this is NOT a permanently-missing credential; it is flaky, consistent
     with an inconsistently-applied sandbox network policy rather than a hard configuration gap.
5. **05:33–05:38** — three of the successful heartbeats report "the orchestrator offered a new/
   unrelated task", which the agent correctly declined per its role scope ("no unrelated task was
   accepted") — reasonable behavior, but combined with (4) it means the session could neither pick up
   new work nor cleanly signal completion and get released.
6. **06:39:08** (last record observed) — still looping, same pattern. By the time this was checked
   (~06:45 UTC), the tmux session was gone entirely (`tmux_alive: false`, "no server running") and AO
   reports slot 31 `idle`. The session was reaped, not gracefully released.

**Measured cost**: summing `usage.input_tokens` across every heartbeat-loop turn from 05:27:59 to
06:39:08 gives ~1.85M input tokens across ~34 turns for a mechanism that exists purely to say "I'm
still here" — no code changed, no task progressed, in this window. This closely matches the
~1.48M-token jump AO's own `session_input_tokens` counter showed between two `/api/state` snapshots
~40 minutes apart during this session (1,060,419 → 2,536,471).

## Why this matters beyond slot 31

`codex-luna` was only recently operator-enabled for live dispatch (per
`codex_mcp_tool_use_bridge_2026_08_18.md`'s Progress Log). If the underlying cause is the Codex CLI
sandbox's default network policy being applied inconsistently to a same-host `localhost:8765` call,
this is not a slot-31-specific fluke — it can recur on ANY Codex/Luna dispatch, silently burning
real token budget while LOOKING busy (a live tmux session, real turns, real usage) rather than
genuinely idle, which is a worse failure mode than idle: nothing pages on it, nothing distinguishes
it from real work in the dashboard's `context_used_pct`/`tasks_completed` view, and it can run for
an unbounded time until whatever eventually reaps the tmux session catches up.

## Non-goals

- Not reproducing the exact sandbox network policy misconfiguration here — that needs someone with
  the real `openai-codex` SDK/sandbox docs and a live Codex account to test directly (see todo below).
- Not assuming this is unique to the heartbeat call specifically — the SAME sandbox network
  restriction could plausibly affect any other tool call this session's role instructions have it
  make against `localhost:8765` (e.g. a `/done` or `/blocked` submission), just not observed live
  here because the session never reached one.

## Todos

- [ ] [INFRA] P1. Root-cause WHY the Codex/Luna sandbox's network policy toward `localhost:8765`
      is inconsistent turn-to-turn within the SAME session (6 successes, ~28 failures, no pattern
      tied to elapsed time or turn count) — read the `openai-codex` SDK's sandbox/approval
      configuration (`codex_bridge_server.py`'s `_drive_codex_turn`/`Sandbox` usage) for whether
      network access is meant to be a per-call approval prompt, a session-wide grant, or something
      that should be pre-approved at spawn time for AO's own internal endpoints. Done when: the
      actual mechanism producing `RTM_NEWADDR: Operation not permitted` vs a clean success is
      understood and cited, not inferred from transcript text alone.
- [ ] [INFRA] P1. Once root-caused, fix it so the worker-liveness heartbeat is either (a) exempted
      from the sandbox's network-approval gate for the fleet's own internal `localhost:8765` origin,
      or (b) delivered through a path that doesn't need it (e.g. the same pattern
      `codex_bridge_server.py` itself uses to reach AO, if that path is more reliable than what the
      spawned session's own tool-call sandbox permits). Done when: a real Codex/Luna dispatch runs
      for 30+ minutes past its last real work with heartbeats succeeding on every attempt, not ~18%
      of them.
- [ ] [INFRA] P2. Add a STUCK-LOOP detector distinct from idle detection: N consecutive turns whose
      only content is a failed heartbeat/liveness attempt (no tool_use, no code change, no new
      finding) should page the same way a genuine stall does — today this session ran ~34 such turns
      with nothing watching for the pattern specifically (worker-liveness watchdog tracks aliveness,
      not turn-content). Done when: a real reproduction (or this session's own transcript, replayed)
      trips the detector before 70 minutes elapse, not after.
- [ ] [REVIEW] P2. Cross-check whether the 3 declined "unrelated task offered" heartbeat responses
      (05:33-05:38) were correctly declined per the `cicd` role's actual scope rules, or whether a
      genuinely idle-with-nothing-else-to-do session should have accepted one instead of looping —
      this issue does not have enough context on the `cicd` role's real instructions to judge that
      call. Done when: the role instructions are read and the decline is either confirmed correct or
      flagged as a second, separate gap.

## Progress Log

- **2026-08-20 (investigation only, no code changed)**: full finding above, reconstructed from the
  live transcript via SSM (`i-0c9b283b31d6b5ca7`), not guessed. Filed as a new issue — no existing
  plan/issue doc in this corpus covers heartbeat delivery reliability or Codex sandbox networking
  specifically (checked via grep before filing, per this workspace's pre-task conflict-check rule).
