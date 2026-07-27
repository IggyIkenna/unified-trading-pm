---
doc_type: issue
title:
  The slot spawn_base_role self-heal only clears a stuck role when find_active_agent_for_session finds NO live AgentRow,
  so the adjacent case — a DIFFERENT-role agent booting live onto the same tmux session while spawn_base_role is still
  stuck at the prior one-off role (e.g. cicd) — correctly leaves the slot held working but leaves last_msg /
  dispatch_reason reading the STALE prior role, a cosmetic dashboard/operator-view mismatch
summary: >-
  On 2026-07-25 (~22:29Z) the review worker (agt-57e3f4) reported, as a live-observed FYI during its own boot, that the
  slot spawn_base_role self-heal (shipped as slot_stale_spawn_base_role_stuck_task_less-001, agent-orchestrator@1e74784)
  only clears a stuck spawn_base_role when find_active_agent_for_session finds NO live AgentRow for the session. The
  adjacent case it does not cover: slot 1's spawn_base_role was stuck at `cicd` (a prior one-off), and a review AgentRow
  (agt-57e3f4) then booted live on the SAME tmux session — so the self-heal correctly left the slot held `working` (a
  live agent owns it, do not reclaim), but last_msg / dispatch_reason still read the cicd one-off even though a
  different-role agent now owns the session. Purely cosmetic: the review agent followed its own role file and proceeded
  normally; nothing was mis-dispatched or blocked. Main (agt-52bb99) confirmed read-only that only main + review are
  currently registered AgentRows (/api/agents), consistent with the stuck-display being a stale field rather than a live
  ownership error. Worth closing only if/when it confuses the dashboard or operator view; filed now so the observation
  is not lost.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    spawn-base-role,
    self-heal,
    session-adoption,
    stale-display,
    dashboard,
    dispatch-reason,
    cosmetic,
    lifecycle,
  ]
related:
  [
    /plans/active/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
priority: P3
parent_epic: orchestrator_master
source:
  "review worker (agt-57e3f4) live-observed FYI in msg 2041; main (agt-52bb99) confirmed AgentRow registry read-only,
  2026-07-25 ~22:29Z"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# spawn_base_role stale-display when a different-role agent adopts a session already stuck at a prior one-off role

## Evidence (review live-observed FYI + main read-only confirmation, 2026-07-25)

- The self-heal shipped as `slot_stale_spawn_base_role_stuck_task_less-001` (agent-orchestrator@1e74784) clears a stuck
  `spawn_base_role` **only when `find_active_agent_for_session` finds NO live AgentRow** for the session.
- Adjacent case observed live by review (agt-57e3f4) on its own boot: slot 1's `spawn_base_role` was stuck at `cicd` (a
  prior one-off); a review AgentRow then booted live on the **same tmux session**. The fix correctly left the slot held
  `working` (a live agent owns it — do NOT reclaim), but `last_msg` / `dispatch_reason` still read the `cicd` one-off
  even though a different-role agent now owns the session.
- Main confirmed read-only via `/api/agents`: only `main` (agt-52bb99) + `review` (agt-57e3f4) are registered AgentRows
  — consistent with a stale display field rather than a live ownership error.

## Hypothesis (needs owner confirmation)

When a live agent adopts a session whose `spawn_base_role` is stuck at a prior one-off role, the self-heal's "no live
AgentRow → clear" guard does not fire (an AgentRow now exists), so the stale `spawn_base_role` / `dispatch_reason` /
`last_msg` are never refreshed to the adopting agent's actual role. The correct behaviour is likely: when a live agent
of a DIFFERENT role owns the session, refresh the display fields to the owning agent's role rather than leaving the
prior one-off role's strings in place.

## Todos

- [ ] [BACKEND] P3. When `find_active_agent_for_session` finds a live AgentRow whose role differs from the stuck
      `spawn_base_role`, refresh the slot's `spawn_base_role` / `dispatch_reason` / `last_msg` to the owning agent's
      actual role (instead of only clearing when NO live AgentRow exists). **Done when**: a slot whose session is
      adopted by a different-role live agent shows that agent's role in the dashboard/operator view, not the prior
      one-off role.

## Triage / charter note

Filed by main (agt-52bb99) per the discovery-capture rule from a peer-role (review) live FYI. Purely cosmetic (bounded
blast radius = a stale display string; nothing mis-dispatched, blocked, or reclaimed), hence **P3** (floor; genuinely
cosmetic). Main diagnosed only via a read-only `/api/agents` check and is charter-barred from editing AO runtime state,
so the fix is BACKEND-owned. Adjacent to the one-shot completion-exit-signal gap (both are one-off-worker lifecycle
display/exit gaps).
