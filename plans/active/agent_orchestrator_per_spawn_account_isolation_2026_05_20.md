---
title: agent-orchestrator — per-spawn account isolation (HOME-shim) for parallel multi-account throughput
type: implementation-plan
status: active
created: 2026-05-20
deadline: 2026-06-10
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: brand-new
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.0
companion_to:
  - codex/04-architecture/agent-orchestrator-overview.md
  - plans/active/agent_reliability_mitigations_2026_05_20.md
---

# Per-spawn account isolation (HOME-shim) — parallel multi-account throughput

> **Provenance**: surfaced 2026-05-20 mid-failover-implementation discussion. The current swap_claude_account.sh
> design works (file-copy + worker bounce) but constrains the fleet to ONE active Claude Max account at a time. With
> 2+ Max accounts on the VM (harsh-primary + ikenna-backup as of 2026-05-20), we have ~2× message capacity that's
> idle today. This plan unlocks parallel use of both.

## Current state (post-2026-05-20)

| Artifact | What it does | Limitation it imposes |
| --- | --- | --- |
| `~/.claude/.credentials.json` (active) | Source-of-truth file claude reads on startup | All running workers share whichever account this points at |
| `~/.claude/.credentials.harsh-primary.json` | Backup snapshot, ikenna@odum-research.com Max | Inert unless `swap_claude_account.sh` copies it over `.credentials.json` |
| `~/.claude/.credentials.ikenna-backup.json` | Backup snapshot, ikennaigboaka@gmail.com Max | Same as above |
| `swap_claude_account.sh` (Harsh's, on VM `/home/ubuntu/`) | File-copy switchover + audit-log to `/tmp/account_swaps.log` | Requires ALL workers to bounce on swap (claude reads creds at startup, holds OAuth tokens in memory) |
| `accounts.json` (`data/config/`) | Static metadata: account_id, label, tier, weekly_msg_limit | Doesn't yet point at per-account credentials_path |
| `AccountUsageRow` | Live usage + `rate_limited_until` per account | Used for display only today; not consulted by spawn endpoint |

**Net**: failover works, but it's SERIAL — fleet on harsh-primary OR ikenna-backup, never both. Both Max accounts have
their own weekly + 5h windows; running them in parallel doubles aggregate throughput on the same VM.

## Future state — parallel multi-account

Goal: at any moment, slot N can be running under account A while slot M runs under account B, without either claude
process being aware of the other's creds. Failover becomes a local-only event (kill + respawn ONLY the exhausted-
account workers), not a fleet-wide bounce.

### Design

1. **Per-slot HOME dir under `${WORKSPACE_ROOT}/.tabs/<N>/.claude-home/`** (gitignored). Each slot's claude session
   sees its own `~/.claude/` namespace via `HOME=.../.tabs/<N>/.claude-home/`. Inside lives a symlink:
   `.tabs/<N>/.claude-home/.claude/.credentials.json` → `~/.claude/.credentials.<account_id>.json`.

2. **`accounts.json` extended**:
   ```jsonc
   {
     "accounts": [
       {
         "id": "harsh-primary",
         "label": "Harsh (ikenna@odum-research.com Max)",
         "tier": "max",
         "weekly_msg_limit": 240,
         "primary_email": "ikenna@odum-research.com",
         "credentials_path": "/home/ubuntu/.claude/.credentials.harsh-primary.json"
       },
       {
         "id": "ikenna-backup",
         "label": "Ikenna (ikennaigboaka@gmail.com Max)",
         "tier": "max",
         "weekly_msg_limit": 240,
         "primary_email": "ikennaigboaka@gmail.com",
         "credentials_path": "/home/ubuntu/.claude/.credentials.ikenna-backup.json"
       }
     ]
   }
   ```

3. **Spawn endpoint plumbs the symlink**:
   - `SpawnRequest.account_id` already exists (default `harsh-primary`)
   - Before `tmux new-session`, `worktree_claim` (or new helper) materialises `.tabs/<N>/.claude-home/.claude/`
     and symlinks `.credentials.json` → the account's `credentials_path`
   - `tmux_spawn.spawn()` passes `env={"HOME": str(slot_home)}` to the subprocess

4. **Failover becomes per-slot**:
   - Worker on slot N hits rate-limit → reports via `/heartbeat` (or `/progress`)
   - Orchestrator looks up which account that slot was on; consults `accounts.json` for an alternative with
     `rate_limited_until < now`
   - Re-points the symlink + sends `kill_worker=true` reassign for THAT slot
   - Other slots (potentially still on the exhausted account but with fresh context) keep running until they too hit
     the limit, at which point they individually rotate

5. **Backwards-compat path**:
   - If `accounts.json` has no `credentials_path` set, fall back to current global `~/.claude/.credentials.json`
   - If `HOME` shim is disabled via `ORCHESTRATOR_DISABLE_HOME_SHIM=1` env var, behave exactly like today
   - This lets the orchestrator ship the new code without forcing every slot's worker to migrate simultaneously

## Phased execution

### Phase 1 — Data model + `accounts.json` schema bump (~0.3 cal)
- Extend `AccountsFile` pydantic model with `credentials_path: str | None`
- Update `accounts.json` to include `credentials_path` for both accounts on the VM
- `sync_accounts_to_db()` validates the path exists + is mode 0600 at boot time (logs a warning if not, doesn't fail)

### Phase 2 — Per-slot HOME shim materialisation (~0.5 cal)
- New helper `agent-orchestrator/server/account_home.py::ensure_slot_home(slot_id, account_id) -> Path`
  - Creates `.tabs/<N>/.claude-home/.claude/` if absent
  - Symlinks `.credentials.json` → `credentials_path` (atomic rename via tempfile + `os.replace`)
  - Returns the HOME path
- `spawn_slot()` calls `ensure_slot_home(slot_id, req.account_id or "harsh-primary")` BEFORE tmux launch
- `tmux_spawn.spawn()` accepts new kwarg `env: dict[str, str] | None = None` and merges into subprocess env
- `.tabs/<N>/.claude-home/` added to per-slot `.gitignore` (via PM SSOT)

### Phase 3 — Failover detection + per-slot rotate (~0.6 cal)
- New endpoint `POST /api/slots/<N>/rotate-account {to_account_id: str}` — re-symlinks + reassigns (kill_worker=true)
- `/heartbeat` + `/progress` accept new `rate_limit_signal: bool` field — when true, orchestrator triggers rotate
  if a non-exhausted account exists; otherwise fires the both-accounts-exhausted Telegram alert (from
  agent-orchestrator slack-notifications scaffold but via the Telegram helper)
- Periodic `/usage` poller (existing `usage_tracker.py`) checks all accounts every 5 min and updates
  `AccountUsageRow.rate_limited_until` — orchestrator can pre-empt failover before a worker hits the wall
- Audit trail: extend `account_swaps.log` to per-slot granularity, write to SQLite `account_rotation_events` table

### Phase 4 — Parallel hot start + per-spawn account routing (~0.6 cal)
- Spawn dispatcher chooses account per spawn based on AccountUsageRow free-window (e.g., round-robin within the
  non-rate-limited pool)
- Dashboard adds account badge per slot (already shows account_id; just light it up red on rate-limit)
- Removes `swap_claude_account.sh` once Phase 4 ships; legacy script kept for 30 days as fallback

## Acceptance criteria

- Two slots running simultaneously on different accounts; `~/.claude/.credentials.json` (global) is no longer
  read by any worker
- When account A hits rate-limit, ONLY slots bound to A get bounced. Slots on B keep running
- When BOTH accounts hit rate-limit, no rotation happens; Telegram alert fires; orchestrator continues serving
  read endpoints
- Existing `swap_claude_account.sh` continues to work for ~30 days as a fallback (don't remove until Phase 4 lands)
- `ORCHESTRATOR_DISABLE_HOME_SHIM=1` flips to legacy behaviour cleanly

## Composes with

- `plans/active/agent_reliability_mitigations_2026_05_20.md` Phase 3 `.agent-claim` — the claim file already carries
  `account_id`, so the rotate endpoint can update it without breaking the predecessor-recognition contract
- Telegram alert helper (`server/notifications/telegram.py`) shipped 2026-05-20 alongside this plan
- Slack notifications (existing `server/notifications/slack.py`) — same alert payload can fork-and-fan-out

## Out of scope

- More than 2 accounts in active rotation (Phase 4 supports it but UX hasn't been thought through for 3+)
- Cross-VM account sharing (each VM has its own `.credentials.*.json` set)
- Anthropic Console (API-billing) accounts in the failover pool — different auth model entirely
