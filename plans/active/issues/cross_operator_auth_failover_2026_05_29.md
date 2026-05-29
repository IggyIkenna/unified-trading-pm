---
title: "Cross-operator account rotation + auth-fail trigger + Slack alert on rotation (operator-corrected 2026-05-29)"
created: 2026-05-29
author: slot-1 (ikenna)
source:
  - agent-orchestrator/server/server.py `_pick_next_account` (line 334)
  - agent-orchestrator/data/config/accounts.json (4 accounts: 3 ikenna + 1 harsh, intended shared pool)
  - Slack `agent-orchestrator-alerts` 2026-05-29T09:40Z — "Slot 6 STALE — last heartbeat 09:15Z, stale 25min"
  - 2026-05-29 dispatch session: slot 6 spawned with `account_id: harsh-primary`, server returned `ok` but no /heartbeat
  - operator clarification 2026-05-29 (ikenna): "harsh shoudl be able to fail ove rteh ieknna auth those 4 keys are there for a reason for both to be able to round robin betwene each. Setup-token stale / OAuth auth-fail at startup shoudl allo round robin and send a slack alert ... doesnt need 2 more harsh accounts just neeeds use of ikenna accounts"
locked_by: cross_operator_auth_failover_2026_05_29
supersedes:
  - issues/harsh_account_pool_expansion_2026_05_29.md  # original misframing — operator corrected
---

## What I found

The orchestrator account pool in `agent-orchestrator/data/config/accounts.json` has 4 accounts (3 ikenna-tagged + 1
harsh-tagged). Design intent (operator-stated 2026-05-29): the pool is **shared across operators** — Harsh's worker
should rotate to an Ikenna account if `harsh-primary` is unusable, and vice versa. The 4 entries exist precisely so
either operator can round-robin through all of them.

But two gaps prevent that today:

### Gap 1 — rotation only triggers on rate-limit, not on stale-token / auth-fail at startup

`_pick_next_account` (server.py:334) is called when:

- Rate-limit detected on `/boot` (line 587).
- Periodic re-dispatch fires for accounts marked rate-limited in the DB (line 404).
- Operator-driven via `/api/blocked/<id>/answer` (line 728).

It is **NOT** called when a worker boots and the OAuth setup-token is stale / expired / corrupted. In that case the
worker never reaches any orchestrator endpoint — claude exits at startup or hangs at the auth prompt — and the server
sees no signal. Slot stays in pre-/boot limbo indefinitely.

### Gap 2 — Slack does not announce rotation events (or which trigger caused them)

The Slack `agent-orchestrator-alerts` channel fires on `Slot N STALE` (heartbeat-based) but **not** on rotation events
themselves. When a rotation happens, the operator has no visibility into:

- **Which account** got swapped out.
- **Which account** got swapped in.
- **Why** — rate-limit (429) vs. stale-token vs. operator-directed.

This matters operationally: a rotation caused by a stale setup-token signals "this account needs Phase-5 re-auth before
its 365-day TTL"; a rotation caused by rate-limit signals "this account hit its weekly quota" — wildly different fix
paths, indistinguishable from current dashboards.

## Reproduction

2026-05-29 dispatch session: slot 6 spawned via `POST /api/slots/6/spawn` with `account_id: harsh-primary`. Server
returned `{ok: true, tmux_session: orch-slot-6}`. After 25+ min: no /heartbeat. Slack auto-alert at 09:40Z confirmed
"Slot 6 STALE". Server never rotated to `sub-a-ikenna` (or any other account in the pool) because no auth-fail signal
reached it. Slots 4 / 5 / 9 / 10 (sub-a-ikenna / sub-b-iggy2london / sub-c-ikenna-odum) worked fine, confirming the
non-harsh accounts are healthy and would have been viable failover targets.

## Why it matters

- Any operator-tagged slot can stall on a single bad account, despite a healthy 3-account fallback pool sitting unused.
- Stale-token failure is silent — operator only learns from a `Slot N STALE` alert 25 min later, with no breadcrumb
  pointing at "the account, not the worker".
- Rotation events that already happen (via 429) are also silent — operator can't audit which accounts are healthy / hot
  / cold from the Slack feed alone.

## Recommended decision

Three fixes in one plan:

1. **Confirm cross-operator rotation works.** Test by simulating `harsh-primary` rate-limited and verifying
   `_pick_next_account` picks an `ikenna`-tagged account. If `_pick_next_account` filters by operator, remove that
   filter so rotation is fully shared.
2. **Add auth-fail rotation trigger.** New server signal: if a slot's worker doesn't /heartbeat within N seconds after
   `/spawn`, mark the current account `auth_failed` in the DB and call `_pick_next_account`; re-spawn the slot's tmux
   with the next account.
3. **Slack alert on every rotation event** with the rotation reason: `rate_limit` (429), `auth_failed` (stale-token
   inferred from no-heartbeat-after-spawn), or `operator_directed`.

Operator stated explicitly 2026-05-29: "doesnt need 2 more harsh accounts just neeeds use of ikenna accounts" —
confirming the shared-pool design intent; the fix is rotation logic + alerting, not account-pool expansion.

## Scope

See [`plans/active/cross_operator_auth_failover_2026_05_29.md`](../cross_operator_auth_failover_2026_05_29.md).

## Unblocks

- Slot 6 (and any harsh-tagged slot) survives `harsh-primary` issues by rotating into the ikenna pool.
- Operator gets timely Slack notification when an account needs Phase-5 re-auth (`auth_failed` rotation) vs. quota
  top-up (`rate_limit` rotation).
- The 4 existing tokens are used to their full capacity, no operator-asymmetric fragility.

## Supersedes

`issues/harsh_account_pool_expansion_2026_05_29.md` (original misframing — proposed Harsh add 2 accounts; operator
corrected: shared pool is the design, the gap is rotation + alerting, not account count).
