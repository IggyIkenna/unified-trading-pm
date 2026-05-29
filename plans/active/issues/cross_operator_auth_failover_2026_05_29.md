---
title: "Harsh has only 1 Anthropic account in accounts.json — no rotation pool, spawn-stall on stale auth (2026-05-29)"
created: 2026-05-29
author: slot-1 (ikenna)
source:
  - agent-orchestrator/data/config/accounts.json (Phase 5 note: "harsh.kantariya00787@gmail.com and harshkantariyawork@gmail.com are the same person — one token total")
  - agent-orchestrator/server/server.py `_pick_next_account` (line 334) — round-robin, skips rate-limited
  - Slack `agent-orchestrator-alerts` 2026-05-29T09:40Z — "Slot 6 STALE — last heartbeat 09:15Z, stale 25min"
  - 2026-05-29 dispatch session: slot 6 spawned with account_id `harsh-primary`, server returned `ok` but worker never /heartbeat-ed
locked_by: harsh_account_pool_expansion_2026_05_29
---

## What I found

Ikenna has **3 Anthropic accounts** wired into `agent-orchestrator/data/config/accounts.json`, each with its own
`oauth_token_env_file` (Phase 5 setup-tokens, expires 2027-05-21):

- `sub-a-ikenna` — ikennaigboaka@gmail.com (primary)
- `sub-b-iggy2london` — iggy2london@gmail.com
- `sub-c-ikenna-odum` — ikenna@odum-research.com

Harsh has **only 1**:

- `harsh-primary` — harsh.kantariya00787@gmail.com / harshkantariyawork@gmail.com (Phase 5 note: same person)

## Why it matters

The orchestrator's account-rotation logic (`server.py:334 _pick_next_account`) round-robins to the next
**non-rate-limited** account in `accounts.json`. Rotation triggers when:

1. The current account hits the rate limit (Anthropic 429), OR
2. Operator-driven (`/api/blocked/{id}/answer` → account-rotated dispatch_reason), OR
3. Periodic re-dispatch fires when a slot's account is flagged rate-limited.

**Rotation does NOT trigger on auth failure.** If `harsh-primary`'s setup-token is stale/expired, the worker fails at
boot with no /heartbeat ever fired — the orchestrator can't detect the failure mode and never rotates.

Empirical reproduction (2026-05-29): slot 6 spawned via `POST /api/slots/6/spawn` with `account_id: harsh-primary` —
server returned `{ok: true, tmux_session: orch-slot-6}` — but `/api/state` shows no /heartbeat for 25+ min. Slack
auto-alert at 09:40Z confirmed Slot 6 STALE. Meanwhile slots 4 / 5 / 9 / 10 (Ikenna's 3-account pool) all working.

Net consequence: **any harsh-tagged slot is a single point of failure**. If his one token expires (annually), or hits
rate-limit, or the env file gets corrupted, his entire worker fleet (3-4 slots typically) goes down with no rotation
fallback. Ikenna's fleet survives one account failing because rotation flips to the other two.

## Recommended decision

Harsh provisions **2 additional Anthropic accounts** (mirroring Ikenna's pool size). Same Phase 5 setup-token flow that
landed Ikenna's 3 accounts 2026-05-21 — each new account gets its own `oauth_token_env_file` in
`~/.claude-accounts/<id>.env` on every backend VM, pushed to the creds buckets
(`gs://central-element-323112-orchestrator-creds/accounts/` + `s3://uts-orchestrator-creds-427895769566/accounts/`), and
listed in `accounts.json`.

## Scope

See [`plans/active/harsh_account_pool_expansion_2026_05_29.md`](../harsh_account_pool_expansion_2026_05_29.md) for the
phased execution.

## Unblocks

- Slot 6 + any future harsh-tagged slot to rotate cleanly on auth/rate-limit failure.
- Harsh-side fleet survives a single-account expiry without a multi-hour stall.
- Mirrors Ikenna's resilience pattern → no operator-asymmetric fragility.
