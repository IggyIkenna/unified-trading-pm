---
doc_type: codex-ssot
title: Orchestrator Safety Mechanisms (SSOT)
summary:
  SSOT for the orchestrator's per-slot safety mechanisms — stuck-agent detection (3 signals) plus auto-respawn with
  exemptions, per-spawn account auth-failover (_pick_next_account, no mid-session token swap), the Telegram/Slack alert
  inventory, git-staleness ping, and liveness-gated fresh-spawn dirty-state resolution (inherit dead-predecessor WIP /
  protect live peer / quarantine wiped index).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [orchestrator, self-healing, slack, monitoring, escalation]
related:
  [
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    /codex/05-infrastructure/agent-orchestrator-slack-notifications.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-05-21
authoritative_for:
  [
    orchestrator stuck-agent detection and respawn,
    orchestrator per-spawn account auth-failover,
    fresh-spawn dirty-state resolution,
  ]
referenced_by:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/05-infrastructure/agent-orchestrator-slack-notifications.md,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    plans/audit/instructions/orchestrator_master_audit_instructions.md,
    plans/epics/orchestrator_master.md,
  ]
owner:
last_reviewed: 2026-05-28
code_refs:
---

# Orchestrator Safety Mechanisms (SSOT)

> **Permanent SSOT** for the safety mechanisms the orchestrator runs on every VM: stuck-agent detection + auto-respawn,
> auth failover (non-blocking), Telegram alerts, git staleness ping, fresh-spawn dirty-commit (overrides CLAUDE.md
> foreign-files rule for that specific case).
>
> Codified 2026-05-21 from the `orchestrator_v07_multi_vm_topology` plan (promoted to
> [`../../plans/epics/orchestrator_master.md`](../../plans/epics/orchestrator_master.md)). Implementation phases live in
> active plans under `parent_epic: orchestrator_master`.
>
> Composes with: [`agent-orchestrator-single-vm-architecture.md`](agent-orchestrator-single-vm-architecture.md) (the
> topology these mechanisms run on);
> [`claude-cli-multi-account-headless-auth.md`](claude-cli-multi-account-headless-auth.md) (auth model the failover
> mechanism switches between).

## A) Stuck-agent detection + auto-respawn

Three signals classify a slot as STUCK (action: respawn after Telegram alert):

1. **No compaction within 15 min** AND `context_used_pct > 70%`. Workers compact every ~5-10 min at that load; 15 min
   silence with high context = wedged.
2. **No pings/heartbeats within 15 min** AND no current_task that's properly `/blocked`. Workers self-direct via
   `/heartbeat` every 60s; 15 min silence = process gone.
3. **No git_status updates within 15 min** AND last status was red. Indicates auto-pull cron stopped firing OR worker
   can't reach orchestrator.

### Exemptions (do NOT respawn even if signals trigger)

- Slot is `paused` (operator-intentional).
- Slot is `blocked` and the `/blocked` event has `awaiting_response_from: orchestrator` set.
- Review agent slot when no commits to review for the configured idle window (e.g. >2h).
- Slot has an in-flight long tool call (>15 min OK if last activity log shows tool execution).

### Respawn recipe (in this order; abort if any step fails)

1. Telegram alert: `🔄 Auto-respawn slot <N> — stuck for <signal>`
2. Try to commit + push any dirty WIP in the slot's worktree (see § E "Fresh-spawn dirty-commit" below)
3. `tmux kill-session -t orch-slot-<N>`
4. `POST /api/slots/<N>/spawn` with the slot's current account (or failover if expired)
5. Verify new tmux session within 30s; if not, escalate to operator (Telegram + dashboard banner)

## B) Auth failover (per-spawn, not mid-session)

When the active account for a slot hits the rate-limit window OR is otherwise marked unhealthy:

1. Detect via `usage_poller` ticks (5h / weekly / weekly-Sonnet ≥ 95%) or at `/done` time when
   `account_is_rate_limited()` is true.
2. **Mid-session token swap is not supported.** claude CLI doesn't re-read env mid-process, and there is no
   `.credentials.json` to swap (that path was removed in Phase 4b-cleanup 2026-05-28).
3. `rotate_all_slots_off_account(account_id, trigger=...)` walks every slot currently on the exhausted account, picks a
   healthy sibling (`_pick_next_account`: lowest-weekly-pct first across accounts.json), and **respawns** each slot on
   the new account: kill tmux session → re-spawn with `env_file=~/.claude-accounts/<next-id>.env` sourced fresh (per
   [`claude-cli-multi-account-headless-auth.md`](claude-cli-multi-account-headless-auth.md)).
4. Workers receive `dispatch_reason: "account-rotated:<new-id> — exiting, new session spawning"` on their next `/done`
   response and exit cleanly; the orchestrator backend spawns the replacement with the new env file.
5. If no sibling account is healthy →
   `dispatch_reason: "Account <X> is rate-limited — no fallback accounts available. Slot held idle until window resets."` +
   Telegram `notify_all_accounts_exhausted`. No further action until quota resets or operator intervenes.

**Why not mid-session swap?** Setup-tokens are sourced once at `bash -c 'source <env_file>; exec claude'` time; the
authenticated session caches the token in-process. There is no `/clear`-then-reauth path that re-reads env on a live
session — the spawn must be replaced. This is intentional: a clean respawn preserves no half-state, and the new worker
reads the freshest `accounts.json` + creds-bucket state.

### Failover selection algorithm

Implementation in `server/server.py::_pick_next_account` (called from `rotate_all_slots_off_account`):

```python
def _pick_next_account(current_account_id, session):
    # Iterate accounts.json in declared order; skip current + skip exhausted
    # (weekly_pct >= 95 OR weekly_sonnet_pct >= 95 OR five_hour_pct >= 95 OR
    #  rate_limited_until > now). Return first healthy match.
    # If no healthy match: return None → Telegram notify_all_accounts_exhausted.
```

Lowest-pct-first selection is a future refinement; today the algorithm is "first healthy in declared order" which is
deterministic and simple. Refining to `min(healthy, key=lambda a: a.weekly_pct)` is a single-line change in
`_pick_next_account` when the operator decides headroom-aware routing is worth the added complexity.

## C) Telegram / Slack alerts (workspace-wide alert framework)

Current inventory (verified 2026-06-01; both `server/notifications/slack.py` and `server/notifications/telegram.py`
expose this set). **Authoritative SSOT**: `/codex/05-infrastructure/agent-orchestrator-slack-notifications.md` (event
table, payload shape, retry logic, secret inventory) — cross-link here to prevent the two from drifting.

| Event                              | When                                                                      | Severity  |
| ---------------------------------- | ------------------------------------------------------------------------- | --------- |
| `notify_slot_blocked`              | Slot calls `/blocked` (operator answer needed)                            | warn      |
| `notify_slot_stale`                | HealthMonitor sees working slot silent >25 min                            | warn      |
| `notify_slot_failed`               | HealthMonitor sees idle slot dead                                         | crit      |
| `notify_spawn_failure`             | `tmux_spawn.spawn` raised inside the spawn endpoint                       | crit      |
| `notify_agent_stuck_respawned`     | Auto-respawn fired per § A                                                | warn      |
| `notify_agent_stuck_escalation`    | Respawn failed; operator needs to intervene                               | crit      |
| `notify_account_rotated`           | Active account swapped per § B (slot respawned with new env file)         | info      |
| `notify_all_accounts_exhausted`    | Failover ran out of healthy accounts                                      | crit      |
| `notify_setup_token_expiring`      | Token within 30-day (warn) or 7-day (crit) window of expiry               | warn/crit |
| `notify_git_staleness_red`         | Slot git_status red >15 min AND no auto-pull within 5 min                 | warn      |
| `notify_orchestrator_restart_loop` | systemd OnFailure fires >N restarts in window (Telegram only)             | crit      |
| `notify_unpushed_plans`            | Plan-hygiene cron detects unpushed plan-flip commits on a slot's worktree | warn      |
| `notify_autospawn_flap`            | AutoSpawnLoop detects ≥3 consecutive spawns on same slot within 10 min    | warn      |
| `notify_watchdog_kill`             | WorkerLivenessWatchdog kills a slot (context-full or daily-cap hit)       | P0        |
| `notify_sync`                      | State/snapshot sync event (GCS or S3 upload outcome)                      | info      |

All channels: same group chat (`-5288420200`) for now. Per-VM channels deferred.

**Removed 2026-05-28 (Phase 4b-cleanup)** — the short-lived OAuth refresh path no longer exists, so neither do its
notifications. If you see code referencing any of these, treat it as stale documentation:

- ❌ `notify_oauth_token_expiring` — was firing at 1h-out for 8h tokens; replaced by `notify_setup_token_expiring` at
  30-day-out
- ❌ `notify_oauth_refresh_succeeded` — no refresh under r3; 1-year tokens don't rotate
- ❌ `notify_oauth_refresh_failed` — no programmatic refresh attempts to fail

**Not yet implemented** (referenced in earlier drafts of this doc):

- `notify_setup_token_required` — when a 1-year token dies pre-expiry (e.g. operator revokes). Currently treated as the
  same path as `notify_slot_failed` + manual investigation
- `notify_vm_unreachable` — central API surfaces 5xx for >5 min. Currently surfaces via Fleet tab card state, not alert

## D) Git staleness ping + alert

Auto-pull cron on each VM runs every 5 min: FF-pull from `origin/live-defi-rollout` per worktree, EXCEPT when locally
dirty (preserves WIP). Cron records last-run timestamp.

Dashboard's git status badge already shows red/yellow/green per slot. New: orchestrator polls the cron timestamp file
per slot every 60s. If `git_status` is RED AND last-pull was >15 min ago AND no manual fix has happened → fire
`notify_git_staleness_red` once per slot-30min.

## E) Fresh-spawn dirty-state resolution (liveness-gated, shipped `orchestrator_autonomy_audit_remediation` Phase 4)

**Problem**: when a slot's worker dies mid-work and respawns, the worktree may have uncommitted changes from the
predecessor agent.

**Shipped model**: at the START of every fresh spawn, all three spawn paths (manual `/api/slots/<N>/spawn`, autospawn,
failover) call the liveness-gated `resolve_dirty_state` coordinator + `check_slot_branch_state` (9-FM coverage). The
coordinator determines predecessor liveness **before** touching any files. Three outcomes:

| Predecessor state                        | Resolution                                                                                                                                                                                                    |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Dead predecessor**                     | **Inherit**: stage + commit with `chore(orphan-wip): inherited WIP from predecessor on slot <N> at <ts>`, push to slot branch, log `slot_orphan_wip_committed` event. New worker's boot prompt notes the SHA. |
| **Live peer (active slot)**              | **Protect**: do NOT touch the dirty files; spawn blocked (HTTP 409) until the active peer completes or is killed. Preserves foreign-WIP HARD RULE.                                                            |
| **Wiped index (no predecessor context)** | **Quarantine**: move dirty files to `_wip_quarantine/<ts>/` on the worktree, log `slot_wip_quarantined` event, unblock spawn. Operator recovers from quarantine dir.                                          |

The old unconditional `git add -A` path is removed — it was unsafe for the live-peer case.

**Compose with**: `worktree_clean_check.py` pre-spawn gate (produces the liveness signal that drives the three-way
branch above); `/codex/05-infrastructure/per-tab-worktrees.md` § "Fresh-spawn dirty-state" (canonical detail on the
coordinator contract).

**Rationale**: the foreign-files HARD RULE in CLAUDE.md governs ACTIVE-WORK files in OTHER slots. The dead-predecessor
case is different: the predecessor is gone, WIP belongs to that slot's branch by definition. The live-peer gate
preserves the invariant for concurrent active slots.

## Composes with

- [`agent-orchestrator-single-vm-architecture.md`](agent-orchestrator-single-vm-architecture.md) — the topology these
  mechanisms run on
- [`claude-cli-multi-account-headless-auth.md`](claude-cli-multi-account-headless-auth.md) — auth model the failover
  mechanism switches between (long-lived setup-token via `CLAUDE_CODE_OAUTH_TOKEN`)
- [`../../plans/epics/orchestrator_master.md`](../../plans/epics/orchestrator_master.md) — the L5 epic; this file is
  pointed at from the epic body
- CLAUDE.md "Two teammates × multiple parallel agents (CRITICAL)" — the foreign-files HARD RULE that § E scopes-override
