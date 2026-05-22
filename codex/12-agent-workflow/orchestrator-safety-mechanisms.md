---
scope: [engineer, admin]
last_reviewed: 2026-05-21
---

# Orchestrator Safety Mechanisms (SSOT)

> **Permanent SSOT** for the safety mechanisms the orchestrator runs on every VM: stuck-agent detection + auto-respawn,
> auth failover (non-blocking), Telegram alerts, git staleness ping, fresh-spawn dirty-commit (overrides CLAUDE.md
> foreign-files rule for that specific case).
>
> Codified 2026-05-21 from the `orchestrator_v07_multi_vm_topology` plan (promoted to
> [`../../plans/epics/orchestrator_master.md`](../../plans/epics/orchestrator_master.md)). Implementation phases live
> in active plans under `parent_epic: orchestrator_master`.
>
> Composes with: [`orchestrator-multi-vm-topology.md`](orchestrator-multi-vm-topology.md) (where these mechanisms run);
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

## B) Auth failover (non-blocking)

When the active credentials for a slot 401 OR Anthropic returns billing/rate-limit error:

1. Detect at spawn time (slot pane shows `401 Invalid authentication credentials`) OR mid-session (agent's tool call
   returns 401).
2. **Do NOT respawn the agent** — that loses context.
3. Switch the per-account env file via `source ~/.claude-accounts/<next-id>.env` to the next failover account
   (lowest-weekly-pct-first across the VM's 3 non-primary accounts). Per
   [`claude-cli-multi-account-headless-auth.md`](claude-cli-multi-account-headless-auth.md): env files set
   `CLAUDE_CODE_OAUTH_TOKEN` to a long-lived 1-year `sk-ant-oat01-...` token; no `.credentials.json` swap.
4. The in-memory claude session still has the dead token — kicker sends `/clear` or `/login` nudge so claude re-reads
   env from the shell on next invocation (Anthropic's CLI doesn't auto-detect env change but `/clear` forces fresh
   session init).
5. If `/clear` works (verified by next heartbeat succeeding) → done.
6. If `/clear` doesn't work (e.g. CLI doesn't re-read) → respawn the slot per § A.

### Failover selection algorithm (`server/account_failover.py`)

```python
def pick_failover_account(vm_id, current_account, exclude=None):
    candidates = registry[vm_id].failover_accounts
    candidates = [a for a in candidates if a != current_account and a not in (exclude or [])]
    # Filter out exhausted (weekly_pct >= 95, sonnet_pct >= 95, 5h_pct >= 95) + rate_limited_until > now
    healthy = [a for a in candidates if account_healthy(a)]
    if not healthy:
        return None  # Telegram alert: all-VM-accounts-exhausted
    # Sort by remaining headroom (lowest_weekly_pct first)
    return min(healthy, key=lambda a: account_state[a].weekly_pct)
```

## C) Telegram alerts (workspace-wide alert framework)

| Event                            | When                                                                  | Severity |
| -------------------------------- | --------------------------------------------------------------------- | -------- |
| `notify_agent_stuck_respawned`   | Auto-respawn fired per § A                                            | warn     |
| `notify_agent_stuck_escalation`  | Respawn failed; operator needs to intervene                           | crit     |
| `notify_account_failover`        | Active account swapped per § B                                        | info     |
| `notify_all_accounts_exhausted`  | Failover ran out of healthy accounts                                  | crit     |
| `notify_setup_token_required`    | 1-year long-lived token dead; operator must regenerate (replaces      | crit     |
|                                  | `notify_oauth_refresh_failed` under r3 auth — see auth SSOT)          |          |
| `notify_setup_token_expiring`    | Token within 30-day (warn) or 7-day (crit) window of expiry           | warn/crit |
| `notify_git_staleness_red`       | Slot git_status red >15 min AND no auto-pull within 5 min             | warn     |
| `notify_vm_unreachable`          | Dashboard's `/api/vm/summary` 5xx'd for >5 min                        | warn     |

All channels: same group chat (`-5288420200`) for now. Per-VM channels deferred.

**Deprecated under r3 auth** (see [`claude-cli-multi-account-headless-auth.md`](claude-cli-multi-account-headless-auth.md)):

- ❌ `notify_oauth_token_expiring` (was firing at 1h-out for 8h tokens — replaced by `notify_setup_token_expiring` at
  30-day-out)
- ❌ `notify_oauth_refresh_succeeded` (no refresh under r3; 1-year tokens don't rotate)
- ❌ `notify_oauth_refresh_failed` (replaced by `notify_setup_token_required`)

## D) Git staleness ping + alert

Auto-pull cron on each VM runs every 5 min: FF-pull from `origin/live-defi-rollout` per worktree, EXCEPT when locally
dirty (preserves WIP). Cron records last-run timestamp.

Dashboard's git status badge already shows red/yellow/green per slot. New: orchestrator polls the cron timestamp file
per slot every 60s. If `git_status` is RED AND last-pull was >15 min ago AND no manual fix has happened → fire
`notify_git_staleness_red` once per slot-30min.

## E) Fresh-spawn dirty-commit (overrides CLAUDE.md foreign-files rule for this case)

**Problem**: when a slot's worker dies mid-work and respawns, the worktree has uncommitted changes from the predecessor
agent. The new agent reads CLAUDE.md "Never touch files outside your clear context" and refuses to commit them. Result:
perpetually dirty worktrees that block further work + contain potentially valuable WIP.

**Fix**: at the START of every fresh spawn, the spawn endpoint:

1. Walks each repo worktree in `.tabs/<N>/<repo>/`
2. For any dirty repo:
   - Stages everything: `git add -A`
   - Commits with `chore(orphan-wip): inherited WIP from predecessor on slot <N> at <ts>` + the predecessor's last-known
     `agent_id` if available
   - Pushes to the slot's branch: `git push origin tab/<operator>/<N>`
3. Logs an activity event `slot_orphan_wip_committed` with the SHA + repo list
4. Tells the new claude session via boot prompt: "Predecessor WIP committed to your branch at SHA `<X>`. Review for
   relevance to your next task; if useful, reference; if not, ignore (it's preserved in git history)."

This makes the foreign-files rule consistent: it remains true for ACTIVE-WORK files in OTHER slots, but a respawned slot
owns its predecessor's WIP and ships it cleanly.

**Compose with**: existing `worktree_clean_check.py` pre-spawn gate. Today it REFUSES spawn on dirty state OR stashes
(with `dirty_state_resolution: stash`). New default mode: `commit_and_push` (the behavior above), with stash + refuse
remaining as overrides.

**Rationale**: the foreign-files HARD RULE in CLAUDE.md is about preventing one slot from accidentally clobbering
another slot's in-flight work. The respawn case is different: the predecessor agent IS gone (process-dead), nobody else
is editing those files, and the WIP belongs to that slot's branch by definition. Committing it cleanly preserves it +
unblocks the new agent on the same slot. The override is scoped to one spawn endpoint, not workspace-wide.

## Composes with

- [`orchestrator-multi-vm-topology.md`](orchestrator-multi-vm-topology.md) — the topology these mechanisms run on
- [`claude-cli-multi-account-headless-auth.md`](claude-cli-multi-account-headless-auth.md) — auth model the failover
  mechanism switches between (long-lived setup-token via `CLAUDE_CODE_OAUTH_TOKEN`)
- [`../../plans/epics/orchestrator_master.md`](../../plans/epics/orchestrator_master.md) — the L5 epic; this file is
  pointed at from the epic body
- CLAUDE.md "Two teammates × multiple parallel agents (CRITICAL)" — the foreign-files HARD RULE that § E scopes-override
