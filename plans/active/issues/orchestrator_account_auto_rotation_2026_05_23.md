---
title: "Orchestrator: workers halt on rate-limit instead of rotating to next account"
created: 2026-05-23
author: slot-1-ikenna
source:
  - plans/active/workspace_qg_sweep_2026_05_23.md
  - agent-orchestrator/agents/worker.md
  - agent-orchestrator/server/server.py
---

## What I found

`worker.md` line 304-305 states:

> If /boot returns `dispatch_reason` mentioning "rate-limited", your account is depleted — STOP. Tell the operator. Do
> not pick up another task.

The server's `/api/slots/{id}/heartbeat` also holds slots idle when their account is rate-limited
(`dispatch_reason: "Account {account_id} is rate-limited. Slot held idle until window resets."`). There is no automatic
switch to a fallback account.

The orchestrator does have multi-account support (accounts.json with multiple `AccountDef` entries, per-account env
files in `~/.claude-accounts/`). The dispatch logic in `dispatch.py` already skips rate-limited accounts via
`ss.account_is_rate_limited(session, req.account_id)`.

**Gap**: when a worker's account is rate-limited, the worker stops permanently rather than re-booting with the next
non-rate-limited account from the same VM's accounts.json.

## Why it matters

- QG sweep runs all 20 repos. Each repo can take 5-30min for basedpyright. If an account hits its 5-hour session limit
  mid-sweep, that slot goes permanently idle.
- Fleet view shows accounts at 19-25% weekly — not at limit now — but will matter at high slot throughput.
- The orchestrator already tracks `rate_limited_until` per account. The dispatch layer already skips rate-limited
  accounts when picking tasks. The missing piece is the worker re-booting itself against a non-rate-limited account.

## Recommended decision

**Option A (preferred)**: Worker re-boot loop. On rate-limited `/boot` response, worker calls `/api/accounts` to find
the next non-rate-limited account on this VM, then calls `/api/slots/{id}/boot` with `account_id=<next>`. Adds ~10 lines
to worker.md boot logic.

**Option B**: Orchestrator auto-reassigns the slot to a different account on the next heartbeat. No worker change
needed, but requires server-side account-switching on heartbeat timeout.

**Operator decision required**: which option, and which accounts are available on which VMs (accounts.json on each VM
defines this — operator manages).

## Current state — RESOLVED 2026-05-23

**Shipped**: Option B (server-side auto-rotation). `agent-orchestrator@a03f874` on live-defi-rollout.

Changes:

- `server/config.py`: added `server_url()` for rendering replacement worker boot prompt
- `server/server.py`: `_pick_next_account()` + `_spawn_with_account_bg()` helpers; rate-limit branches in `boot_slot()`,
  `heartbeat_slot()`, `done_slot()` all call rotation instead of halting
- `agents/worker.md`: worker exits cleanly on `dispatch_reason` starting with `account-rotated:`; halts only when "no
  fallback accounts available"

**Pending**: test via `POST /api/accounts/{account_id}/rate-limited` to simulate, verify activity log shows
`account_rotation_triggered` + `account_rotation_complete` events.
