---
doc_type: issue
title: Dashboard shows "rate-limited" on accounts with plenty of capacity — clear was never wired
summary: >-
  Operator screenshot: sub-D (odum1default) at 10% 5-hour usage and sub-F (odum2default) at 1% 5-hour usage both showed
  a red "rate-limited until <time>" chip. Root cause: `update_account_usage`'s generic "None = unchanged" contract meant
  `rate_limited_until=None` could never express "please clear this" — indistinguishable from "didn't pass it". Two
  `usage_poller.py` call sites (`_tick_once`'s main successful-probe path and `_reprobe_unhealthy_once`'s fast recovery
  path) already passed exactly that on every successful probe, with comments explicitly claiming it cleared the mark —
  it silently never did. `routes/accounts.py`'s manual "Refresh from /usage" route never even attempted to clear it at
  all. The dashboard's manual "Clear" button was the ONLY path that ever worked, which is why it exists right next to
  "Refresh" on every affected account card.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, accounts, rate-limit, usage-poller, dashboard, stale-state]
related:
  - /plans/archive/2026_08/issues/ao_kick_escalation_rate_limit_blind_force_kill_2026_08_14.md
  - /plans/archive/2026_08/issues/ao_slots_27_31_spawn_retry_cap_exhausted_2026_08_13.md
  - /codex/04-architecture/agent-orchestrator-worker-liveness.md
created: "2026-08-14"
author: main (Claude Code, interactive session)
parent_epic: orchestrator_master
resolved_by: agent-orchestrator@b0e6c02542
locked_by:
locked_since:
source: >-
  Operator pasted a dashboard screenshot 2026-08-14, asking "why do these say rate limited when they have capacity" — a
  same-session follow-up to the sub-g-alpavolt spawn-retry-cap investigation.
assigned_vm: NA
execution_scope: local-only
priority: P2
drift_direction: advance-code
depends_on: []
---

# Dashboard shows "rate-limited" on accounts with plenty of capacity

## What was measured

Live account_usage row for `sub-f-odum2default` (the "3h 2m" account in the screenshot):

- `07:54:54 UTC` — marked rate-limited from a pane-detected "hit your limit" banner (`rate_limited_until: 12:54:54`,
  `note: "auto-detected from tmux pane (mid-session limit message)"`). Genuine, correct mark at the time.
- `09:51:52 UTC` — a fresh, authoritative `/usage` probe (`source: "usage_command_pty"`) read back
  `session_pct: 1%, weekly_pct: 14%` — genuinely healthy. `update_account_usage` wrote those numbers and stopped there;
  the still-standing `rate_limited_until: 12:54:54` was never revisited.
- At screenshot time, still showing the stale 12:54:54 block despite ~2 hours of proven headroom.

## Root cause

`server/state_store/account_usage.py::update_account_usage` treats every parameter as "None = leave unchanged" —
including `rate_limited_until`, a field whose CLEARED value (None) is textually identical to its UNCHANGED sentinel
(also None). This is the exact same tri-state problem the function's own docstring already documents for
`balance_is_available` ("a real tri-state... otherwise a genuine `is_available=False` reading could never be
distinguished from 'not passed this call'") — just never applied to this field.

Two call sites in `usage_poller.py` (`_tick_once`'s main path, `_reprobe_unhealthy_once`'s fast-recovery path) already
passed `rate_limited_until=None` on every successful probe, with comments explicitly claiming this cleared the mark
("Probe authenticated → recovered. Clear auth_failed + rate-limit (`update_account_usage` sets
`rate_limited_until=None`)") — the intent was correct, the mechanism was silently broken. `routes/accounts.py`'s manual
`/usage` refresh route (the dashboard's "Refresh from /usage" button) never even attempted the clear.

## Fix shipped (agent-orchestrator@b0e6c02542)

- `server/state_store/account_usage.py` — new `clear_rate_limited: bool = False` flag on `update_account_usage`,
  mirroring the existing `balance_is_available` pattern. Explicit-clear wins over a simultaneous `rate_limited_until`
  (documented caller-error precedence).
- `server/usage_poller.py` — both successful-probe call sites now pass `clear_rate_limited=True` instead of the
  silently-inert `rate_limited_until=None`.
- `server/routes/accounts.py` — the manual refresh route now clears too, gated on the SAME condition (mirroring the
  exact if/elif branches, incl. `and *_resets_at` guards) used to decide whether to mark — a fresh read at cap marks
  instead of clearing; anything else clears.
- Tests: 4 direct unit cases (`tests/test_account_usage_rate_limit_clear.py`), 2 poller-integration cases
  (`tests/test_usage_poller_auth_failover.py`), 2 route-level cases
  (`tests/test_refresh_account_usage_route_rate_limit_clear.py`).
- `quality-gates.sh` green.

**Live effect**: takes hold once the orchestrator's own next `ao-self-pull.sh` restart picks up this commit (same as any
AO code change) — no separate manual remediation needed for sub-D/sub-F specifically, since both already have a
rate-limited `account_status`, so `_reprobe_unhealthy_once`'s fast re-probe cadence (independent of the 30-min main
poll) will clear them automatically on its next successful probe after the restart.

## Todo

1. ✅ [SCRIPT] P2. Add the `clear_rate_limited` flag to `update_account_usage`.
2. ✅ [SCRIPT] P2. Wire both `usage_poller.py` successful-probe paths to it.
3. ✅ [SCRIPT] P2. Wire `routes/accounts.py`'s manual refresh route to it, symmetric with its mark condition.
4. ✅ [SCRIPT] P2. Add regression tests across all three layers; `quality-gates.sh` green; shipped.

## Progress Log

- 2026-08-14: root-caused from an operator dashboard screenshot, fixed + shipped (agent-orchestrator@b0e6c02542,
  quality-gates.sh green). Issue resolved.
