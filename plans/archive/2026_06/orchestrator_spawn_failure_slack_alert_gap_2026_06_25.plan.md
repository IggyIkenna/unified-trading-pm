---
title:
  "Orchestrator hard spawn/escalation/autospawn FAILURE does not page Slack — worker can't spawn into slots 4/5/6,
  operator never alerted (2026-06-25)"
created: 2026-06-25
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

- Slots 4/5/6 (and slot 1) `autospawn_failed` / `escalation_dispatch_failed` with
  `tmux_spawn.spawn failed: session orch-slot-N not alive at paste time` — all spawning on account **`sub-a-ikenna`**
  (the only account with usage headroom; the others are over the 95% weekly ceiling — `sub-b` 99%, `sub-c`/`sub-d` 100%
  — or `auth_failed` for `harsh-primary`).

**The structural bug (the fix):** a startup-EXIT spawn failure ("not alive at paste time") is the SAME signal a poller
401 carries when the cause IS a dead token, but the spawn path NEVER fed it into account health. So a low-usage
dead-token account would stay `account_status='healthy'` ("healthy" is a USAGE verdict, not an auth verdict) and
`_pick_headroom_account` would RE-PICK it every tick, spawning doomed workers forever. The full auth-failed-cooldown
ROTATION mechanism already exists (`mark_account_auth_failed` → `account_in_auth_failed_cooldown` →
`account_is_usable=False` → `_pick_headroom_account` skips it → auto-re-probe after backoff) — it was simply never
triggered from the spawn path.

**Root-cause nuance corrected by live data (post-fix):** `sub-a-ikenna`'s token turned out to be ALIVE (it spawned slots
5/6 successfully + has 54 historical slot-4 successes), so the classifier correctly did NOT drop it. The persistent
slot-1/slot-4 failures are a **TRANSIENT spawn race** (bare "not alive at paste time", no pane-tail, intermittent), NOT
a dead token. Both gaps are still real + fixed: a genuinely dead account (auth-shaped pane-tail) is now dropped from
rotation; a transient/non-auth failure correctly keeps the healthy account AND now fires the deduped per-slot
`notify_spawn_failed` page so the operator SEES it (the headline gap). See the Progress Log + the P2 follow-up.

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

A worker that can't spawn = the orchestrator does no work on that slot, and the operator never saw it (no Slack page).
Two failure shapes were silent: a genuinely dead-token account would be re-picked every tick (no rotation drop), and a
persistent transient spawn race produced no page. The fix keeps velocity on the healthy pool (drop a dead account, keep
a transiently-flaky-but-healthy one) AND makes both visible (deduped pages), so the operator acts off the critical path
instead of the fleet starving silently.

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
- [x] [OPS] P0. Diagnosed + LIVE-VERIFIED slots 4/5/6 on the planning VM via SSM. The fix self-deployed (ao-self-pull
      `*/15` cron → HEAD=23e7006, service active). **Slots 5 & 6 RECOVERED** (both `working` with live tmux sessions);
      `sub-a-ikenna` spawned them successfully — **its token is ALIVE** (54 historical slot-4 successes + slots 5/6 just
      spawned on it), so the fix correctly did NOT drop it (`spawn_auth_fail_account_dropped`=0). The slot-1/slot-4
      failures are a **TRANSIENT spawn race** (bare "not alive at paste time", NO pane-tail → non-auth), NOT a dead
      token — and `notify_spawn_failed` now PAGES them (the `spawn_failed_alerted` sentinel carries slots 1+4; journal:
      "hard spawn-failure alert fired: slot 1"). **No operator re-auth needed for `sub-a-ikenna`** (alive); only
      `harsh-primary` is genuinely `auth_failed` (re-auth on your schedule if you want it back: `claude setup-token` →
      `~/.claude-accounts/harsh-primary.env` → `push_creds_to_gcs.sh`). — agent-orchestrator@23e7006
- [x] [DOCS] P1. `unified-trading-pm` — fix issue-doc frontmatter YAML (source entries had unquoted colons → invalid
      YAML → `check_frontmatter_schema` failed → would break PM CI). Quoted; all required fields valid. — PM@860896382
- [x] ✅ [CODE] P2. **NICE-TO-HAVE** `agent-orchestrator` — harden the TRANSIENT spawn race (a bare "not alive at paste
      time" with no pane-tail: claude's tmux session is fully destroyed between create + paste under load). Provenance:
      live slots 1/4 intermittently fail this way on a HEALTHY account (54 prior successes). The fix already PAGES it +
      keeps the account; robustness options: widen `ORCHESTRATOR_SPAWN_TIMEOUT_S`, or add a short backoff-retry of the
      whole `spawn()` (not just the paste) when the session dies with no auth evidence. Target: `server/tmux_spawn.py`
      `_start_session`/`spawn`. — agent-orchestrator@6e6638a: added `_SPAWN_TRANSIENT_MAX_RETRIES=2`,
      `_is_transient_spawn_failure()` helper (bare "not alive" + no pane-tail → True; pane-tail present → False to
      preserve auth-rotation path), and retry loop in `spawn()`+`spawn_named()` that kills orphan → sleeps 2s →
      re-calls `_start_session` → retries dismiss+paste. 5 new unit tests (QG green, 903 passed).

## Codex SSOT updates

- [x] `codex/04-architecture/agent-orchestrator-overview.md` § Auto-spawn — added "Spawn-time auth-fail →
      drop-from-rotation" + the alert reframe + the failure-modes table rows. — PM@f1126e71

## Progress Log

- 2026-06-25 (slot-3·laptop): diagnosed via SSM on the central VM. TWO real gaps surfaced + fixed: (1) **the rotation
  gap** — a startup-EXIT spawn failure was never fed into account health, so a genuinely dead/expired-token account (low
  usage, still `account_status='healthy'`) would be RE-PICKED by `_pick_headroom_account` every tick and spawn doomed
  workers forever instead of being dropped from rotation; (2) **the alerting gap** — a hard spawn failure on the
  escalation + autospawn paths fired NO Slack (the flap alert only trips on consecutive SUCCESSES). FIX
  (operator-reframed to ROTATION, not recovery): classify an AUTH-shaped spawn failure → `mark_account_auth_failed` (the
  existing rotation/cooldown machinery drops + auto-re-probes it) with a WARNING drop-from-rotation page; a NON-auth
  failure does NOT drop the account (caveat 2026-06-22) but DOES fire the deduped per-slot `notify_spawn_failed` page;
  CRITICAL rotation-exhausted page when no account has headroom; `remain-on-exit`
  - pane-tail capture for diagnosis. All unit-tested (QG green).
- 2026-06-25 LIVE VERIFICATION (post-deploy 23e7006, service active): **slots 5 & 6 RECOVERED** (`working`, live
  sessions). **Corrected root-cause nuance:** `sub-a-ikenna` is NOT actually dead — it spawned slots 5/6 successfully
  and has 54 historical slot-4 successes; `spawn_auth_fail_account_dropped`=0 (the classifier correctly did NOT drop a
  healthy account). The persistent slot-1/slot-4 failures are a **TRANSIENT spawn race**
  (`session not alive at paste time`, NO pane-tail, intermittent) — and the fix now PAGES them: the
  `spawn_failed_alerted` sentinel carries slots 1+4 and the journal shows `hard spawn-failure alert fired: slot 1`. So
  the headline gap (a hard spawn failure must page) is CLOSED on the live system, and the rotation logic is in place for
  a genuinely dead account. Follow-up P2 (transient-spawn-race robustness) filed above.
