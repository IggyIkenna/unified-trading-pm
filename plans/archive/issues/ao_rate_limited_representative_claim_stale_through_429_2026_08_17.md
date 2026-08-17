---
doc_type: issue
title: >-
  An account's binding-window/percentage display froze at its pre-rejection values once it hit a real 429 —
  dashboard showed binding=five_hour and a healthy 0% five-hour bar on an account whose real block matched the
  WEEKLY reset almost to the second — fixed
summary: >-
  Live investigation of the 2026-08-17 AO fleet outage (all 7 Claude accounts exhausted, main + review both dead)
  surfaced a second, independent display bug while explaining the account pool's dashboard readout to the operator.
  Several accounts showed `binding: five_hour` alongside `weekly_pct: 100` / `five_hour_pct: 0` — an apparent
  contradiction the operator directly challenged ("but look at the weekly and 5 hour... the actual numbers"). Traced
  to `server/usage_poller.py`: on a genuine HTTP 429, `_mark_rate_limited_db` (lines 366-380 at investigation time)
  only ever set `rate_limited_until` from Anthropic's real `Retry-After` header — it never touched
  `representative_claim`, `unified_status`, `weekly_pct`, or `five_hour_pct`, all of which are only written on a
  SUCCESSFUL (200) probe. So once an account tipped into a real rejection, its displayed "why" (the `binding:` label
  and percentage bars) froze at whatever the last successful probe reported BEFORE the rejection — stale, not live.
  Confirmed the mismatch was real: `rate_limited_until` (`2026-08-19T14:00:00.032086Z`) matched `weekly_resets_at`
  (`2026-08-19T14:00:00Z`) almost to the millisecond for the affected accounts, proving the WEEKLY window was the
  actual current constraint, while the stale `representative_claim: five_hour` label said otherwise. Distinct from
  the operator's first guess (a regression of `ao_rate_limited_stale_display_2026_08_14`) — that prior fix addressed
  the opposite transition (a stale BLOCKED mark outliving real recovery); this bug is the going-blocked side (stale
  HEALTHY-looking display fields outliving a real block) and was untouched by it.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, accounts, rate-limiting, dashboard, usage-poller]
related:
  [
    /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md,
    /plans/active/issues/ao_review_slot_hard_rule_and_diagnostics_2026_08_17.md,
  ]
created: "2026-08-17"
resolved: "2026-08-17"
author: main (Claude Code, interactive session, operator-reported)
parent_epic: orchestrator_master
resolved_by: agent-orchestrator@4dbac5d5c7
locked_by:
source: >-
  Operator, live during the 2026-08-17 all-accounts-exhausted incident: "but what about this its red but 5h and
  weekly are celarly free whats being logged?" then "but look at the weekly and 5 hour" then "the actual numbers" —
  pushed past my first (wrong) explanation that the numbers were self-consistent, to the real, code-confirmed bug.
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
context_scope:
  [
    agent-orchestrator/server/usage_poller.py,
    agent-orchestrator/server/state_store/account_usage.py,
    agent-orchestrator/server/routes/accounts.py,
    agent-orchestrator/tests/test_account_usage_rate_limit_clear.py,
  ]
---

# Stale `representative_claim`/`unified_status` survives a 429 — fixed

## Root cause (file:line at fix time)

- `server/usage_poller.py:366-380` — the 429-exception branch calls `_mark_rate_limited_db`, which sets
  `rate_limited_until` from Anthropic's real `Retry-After` header. `fetch_usage_via_api` (`usage_tracker.py`) raises
  before returning a parsed body on a 429, so this branch genuinely has no fresh `representative_claim`/
  `unified_status`/percentages to offer.
- Those four fields are only ever written on the SUCCESS path (`usage_poller.py:415-447`, a 200 response). So once an
  account transitions from healthy → rejected, its displayed "why" freezes at the pre-rejection snapshot with no
  signal to the operator that it's now stale.
- `server/state_store/account_usage.py`'s `mark_account_rate_limited` (the shared setter, called from 6 sites across
  `tmux_pruner.py`, `worker_liveness/__init__.py`, `autospawn.py` ×2, `usage_poller.py`, and `routes/accounts.py` ×3)
  had no mechanism to clear these fields at mark time — it only ever set `rate_limited_until`/`last_used_at`.

## Fix (shipped `agent-orchestrator@4dbac5d5c7`)

Added a `stale_claim: bool = True` parameter to `mark_account_rate_limited`. When true (the default), it now also
clears `representative_claim`/`unified_status` to `None` — the dashboard's existing `AccountRateLimitDetail`
component (`dashboard/src/layout.tsx:4378-4392`) already correctly hides the `binding: ...` line when
`representative_claim` is falsy, so no frontend change was needed; clearing the field server-side makes the stale
label disappear through existing render logic.

The default (`True`) is safe for 5 of the 6 existing call sites (`_mark_rate_limited_db`'s 429 branch,
`tmux_pruner.py`, `worker_liveness/__init__.py`, `autospawn.py` ×2) — none of them have a fresh claim in hand at mark
time (a real 429 with no body, or a pane-text regex guess). The 3 call sites in `routes/accounts.py`'s manual-refresh
route are the one case that DOES have fresh data — that route calls `update_account_usage` with a live
`representative_claim`/`unified_status` from the SAME parsed read immediately before calling
`mark_account_rate_limited`, so those 3 sites now explicitly pass `stale_claim=False` to avoid destroying a value
that is still genuinely live.

3 new regression tests in `tests/test_account_usage_rate_limit_clear.py` (`TestMarkRateLimitedStaleClaim`): default
clears a stale claim, `stale_claim=False` preserves a fresh one, default is a no-op when nothing was ever set. Full
quality gate green (4024 passed) before shipping.

## Progress Log

- 2026-08-17: Found while explaining the 2026-08-17 all-accounts-exhausted incident's account-pool dashboard to the
  operator — they directly challenged an apparent weekly/5-hour contradiction I'd initially (wrongly) explained away
  as self-consistent. Traced to code, confirmed via live `git blame` that the similarly-named
  `ao_rate_limited_stale_display_2026_08_14` fix (3 days prior) covered the opposite transition and did not touch
  this path. Fixed same session, shipped `agent-orchestrator@4dbac5d5c7`, tree verified clean, `ahead=0`.
