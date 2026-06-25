---
title:
  "Orchestrator hard spawn/escalation/autospawn FAILURE does not page Slack — worker can't spawn into slots 4/5/6,
  operator never alerted (2026-06-25)"
created: 2026-06-25
author: "ikennaigboaka [slot-3·laptop]"
parent_epic: orchestrator_master
assigned_vm: planning
status: active
priority: P0
locked_by: live-defi-rollout
source:
  - "2026-06-25 ~01:1x UTC operator report — orchestrator UI activity feed escalation_dispatch_initiated → escalation
    failed: tmux_spawn.spawn failed: session orch-slot-5 not alive at paste time (also slot-4) + autospawn failed; NOT
    seen in Slack"
  - "slot-3 source read — agent-orchestrator/server/{tmux_spawn,escalation,autospawn}.py + server/notifications/slack.py"
---

# Orchestrator hard spawn-failure does not page Slack (2026-06-25)

## What I found

The agent-orchestrator fails to spawn workers into slots 4/5/6 on the planning VM, and the operator does NOT see it in
Slack. The design intent is **ROTATION, not recovery**: a dead account/slot must drop OUT of rotation and the
orchestrator keep spawning on HEALTHY accounts — it must not block the queue retrying a dead slot.

### THE SOURCE BUG — a dead-token account is never dropped from rotation

Verified on the central VM (i-0c9b283b31d6b5ca7) via SSM:

- Slots 4/5/6 (and slot 1) `autospawn_failed` / `escalation_dispatch_failed` EVERY tick with
  `tmux_spawn.spawn failed: session orch-slot-N not alive at paste time` — and they all spawn on account
  **`sub-a-ikenna`**.
- `sub-a-ikenna` is the ONLY account with usage headroom (weekly 38% / 5h 10%); the others are over the 95% weekly
  ceiling (`sub-b` 99%, `sub-c`/`sub-d` 100%) or `auth_failed` (`harsh-primary`).
- `sub-a-ikenna`'s env file is dated **May 22** → its setup-token is **expired** (~34 days; tokens last ~30) → claude
  exits at startup ("Please run /login") → "session not alive at paste time".

The bug: a startup-EXIT spawn failure is the SAME signal a poller 401 carries, but the spawn path NEVER fed it into
account health. So `sub-a-ikenna` stayed `account_status='healthy'` (its USAGE is low — "healthy" is a usage verdict,
not an auth verdict), and `_pick_headroom_account` RE-PICKED it every tick, spawning a doomed worker into the slot
forever. The full auth-failed-cooldown ROTATION mechanism already exists (`mark_account_auth_failed` →
`account_in_auth_failed_cooldown` → `account_is_usable=False` → `_pick_headroom_account` skips it → auto-re-probe after
backoff) — it simply was never triggered from the spawn path.

### Gap B — opaque failure reason ("not alive at paste time")

When claude exits at startup the tmux session dies between `_start_session` and `_load_and_paste`, raising the opaque
`session not alive at paste time`. The dead pane (which holds the real cause — "Please run /login" / a rate-limit
banner) was never captured, so neither the rotation classifier nor any alert could see WHY.

### Alerting gap — no page on the RIGHT condition

A hard spawn failure produced UI events but **NO Slack page**:

- the escalation `do_spawn` failure path logged + quarantined, **no Slack**;
- the AutoSpawn-loop failure path logged + `_record_attempt(success=False)`, and the flap alert fires only on N
  consecutive SUCCESSES → a hard failure **never pages**.

The right conditions to page (operator reframe): (a) WARNING when an account drops OUT of rotation (re-auth on the
operator's schedule — the orchestrator does NOT wait); (b) CRITICAL when rotation is EXHAUSTED (no healthy account left
to rotate to) — NOT a per-slot page on every doomed retry of a dead slot.

## Why it matters

A worker that can't spawn = the orchestrator does no work on that slot. Because the dead account was re-picked every
tick, ALL spawns funnelled onto the one expired token and the fleet starved silently. The fix keeps velocity on the
healthy pool by dropping the dead account; the operator re-auths it later, off the critical path.

## What shipped (this issue)

- [x] [CODE] P0. `agent-orchestrator` — SOURCE FIX: classify an AUTH-shaped spawn failure (dead/expired token —
      pane-tail matches `/login`/`Invalid API key`/`setup-token`/`unauthorized`/…) in `_do_spawn` and
      `mark_account_auth_failed` the account so ROTATION drops it (next `_pick_headroom_account` lands on a HEALTHY
      account; auto-re-probe after backoff). A generic non-auth tmux throw does NOT drop the account (operator caveat
      2026-06-22). Unit-tested. — agent-orchestrator@23e7006
- [x] [CODE] P0. `agent-orchestrator` — Gap B: `remain-on-exit on` + pane-tail capture in `tmux_spawn` so a
      startup-exit's dead pane is preserved + read (the auth classifier + alert show WHY); orphan dead-pane session torn
      down on failure. — agent-orchestrator@23e7006
- [x] [CODE] P0. `agent-orchestrator` — ALERTING (reframed): WARNING drop-from-rotation page reuses the deduped
      `notify_account_auth_failed` (one page per account-drop episode, re-armed on recovery); CRITICAL
      rotation-exhausted page (no headroom account while a slot wants a spawn) routed through the shared
      `_maybe_alert_pool_exhaustion` dedup so autospawn + escalation page ONCE. The per-slot hard-spawn page
      (`notify_spawn_failed`, GCS-persisted, pane-tail) is reserved for a genuinely SLOT-specific NON-auth failure — NOT
      per doomed retry. Unit-tested. — agent-orchestrator@23e7006
- [x] [OPS] P0. Diagnosed slots 4/5/6 on the planning VM via SSM (above). Recovery IS the rotation: with this fix the
      orchestrator drops `sub-a-ikenna` (dead token) + the over-ceiling accounts and rotates to whatever has headroom;
      if ALL are exhausted it pages CRITICAL. **Operator action (off the critical path):** re-auth the dead accounts on
      your schedule — `sub-a-ikenna` (expired May-22 token), `harsh-primary` (auth_failed): `claude setup-token` →
      update `~/.claude-accounts/<id>.env` → `push_creds_to_gcs.sh`. The over-ceiling `sub-b/c/d` recover at their
      weekly window reset. — see Progress Log.

## Codex SSOT updates

- `codex/04-architecture/agent-orchestrator-overview.md` § Auto-spawn / Watchdog / Alerts — note the spawn-time
  auth-shaped → drop-from-rotation path + the rotation-exhausted page.

## Progress Log

- 2026-06-25 (slot-3·laptop): diagnosed via SSM on the central VM. ROOT CAUSE: a dead/expired setup-token account
  (`sub-a-ikenna`, May-22 token, low usage so still "healthy") was RE-PICKED by `_pick_headroom_account` every tick
  because a startup-exit spawn failure was never fed into account health — so every spawn (slots 1/4/5/6) funnelled onto
  the one expired token and died. FIX (operator-reframed to ROTATION, not recovery): classify the auth-shaped spawn
  failure → `mark_account_auth_failed` (the existing rotation/cooldown machinery then drops + auto-re-probes it);
  WARNING drop-from-rotation alert; CRITICAL rotation-exhausted alert; pane-tail capture for diagnosis. The orchestrator
  now keeps velocity on the healthy pool; the operator re-auths dead accounts off the critical path. All unit-tested.
