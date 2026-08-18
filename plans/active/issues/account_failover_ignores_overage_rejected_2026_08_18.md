---
doc_type: issue
title: >-
  Account-failover monitor never checks overage_status — an out-of-credits account keeps killing
  sessions on a ~35min cadence instead of triggering rotation
summary: >-
  `sub-b-iggy2london` (Ikenna sub-B, `weekly_pct=90`, `overage_status=rejected`,
  `overage_disabled_reason=out_of_credits`) has killed slot-2 three times today on a ~35min
  cadence (2026-08-18 14:55Z / 15:31Z / 16:46Z) — confirmed directly from the `tmux_session_lost`
  activity events, not inferred. Every kill's `account_snapshot` self-reports
  `account_status: "healthy"` and `death_class: "unexplained"`, despite `overage_status: rejected`
  already being true at kill time. Root cause: the account-failover trigger table (
  `unified-trading-pm/agents/main.md` § "Account-failover triggers") only watches
  `five_hour_pct >= 95`, `weekly_pct >= 95`, `weekly_sonnet_pct >= 95`, and
  `rate_limited_until is not null AND > now()` — none of those flag `overage_status == "rejected"`,
  so a functionally-dead-on-overage account (requests fail because the paid-overage budget is
  exhausted, independent of the raw usage percentage) never trips rotation even though it keeps
  killing every session assigned to it. `weekly_pct=90` sits below the 95% threshold, so the
  existing pct-based check would not have caught this even once it reaches the exact kill moment
  — the overage rejection is the actual proximate cause, not the usage percentage.

  Found by review agent (agt-15d551), independently confirmed by main (agt-a03340) 2026-08-18
  ~17:05Z by pulling the three `tmux_session_lost` events directly via `/api/activity` and cross-
  checking `/api/accounts` for the account's live `overage_status`/`overage_disabled_reason`
  fields. Notable: main's OWN session (`agt-a03340`) also runs on `sub-b-iggy2london`
  (`account_id` returned at `/api/agents/register` time) — main has not yet been killed by this
  mechanism as of filing, but is exposed to the same risk.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, account-failover, overage, tmux-session-lost, multi-account-auth]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: "2026-08-18"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
assigned_role: infra
drift_direction: none
source: >-
  Review agent (agt-15d551) flagged the recurring slot-2 kill pattern in chat with main
  (2026-08-18 ~17:03Z), citing a prior review session's (agt-14c73f, 15:31Z) last_msg as already
  noting the capacity angle. Main independently pulled and confirmed the underlying mechanism via
  `/api/activity` + `/api/accounts` (~17:05Z) and escalated to the operator in chat (same tick) —
  filed here per the "every follow-up is a tracked todo" rule rather than leaving it as chat-only.
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# Account-failover monitor ignores `overage_status` — recurring slot-2 kills on `sub-b-iggy2london`

## Evidence

Three `tmux_session_lost` events, `agent-orchestrator` `/api/activity`, all `slot_id=2`,
`tmux_session=orch-slot-2`, `new_status=killed`, `death_class=unexplained`:

| ts (UTC)  | account_status (self-reported) | overage_status | overage_disabled_reason |
| --------- | ------------------------------- | --------------- | ------------------------ |
| 14:55:07Z | healthy                         | rejected         | out_of_credits            |
| 15:31:04Z | healthy                         | rejected         | out_of_credits            |
| 16:46:11Z | healthy                         | rejected         | out_of_credits            |

Live `/api/accounts` snapshot (2026-08-18 ~17:05Z) for `sub-b-iggy2london`:

```json
{
  "account_id": "sub-b-iggy2london",
  "tier": "max20",
  "status": "high_usage",
  "weekly_pct": 90,
  "five_hour_pct": 0,
  "overage_status": "rejected",
  "overage_disabled_reason": "out_of_credits",
  "weekly_resets_at": "2026-08-23T19:00:00Z"
}
```

`five_hour_pct=0` — this is not an active 5-hour throttle. `weekly_pct=90` is below every
pct-based failover threshold in `main.md`'s trigger table (`>= 95`). The account is nonetheless
functionally unusable right now (`overage_status=rejected`), and nothing in the failover watch
list detects that state.

## Why this matters beyond one slot

- The failover rotation logic (`rotate_all_slots_off_account` per `main.md`) is never invoked for
  this account, because none of its four monitored conditions are true. Every session that gets
  scheduled onto `sub-b-iggy2london` will keep dying the same way until the weekly reset
  (`2026-08-23T19:00:00Z`) or until the operator manually intervenes (top-up / disable the
  account).
- `death_class: "unexplained"` on every occurrence means this failure mode is invisible to
  whatever alerting keys off `death_class` — it looks like a mystery crash, not a known,
  diagnosable capacity condition.
- Main's own session shares this account (`account_id` at `/api/agents/register` time), so main is
  exposed to the identical kill mechanism, not just worker/review slots.

## Todos

- [ ] [OPERATOR] P2. **Decide the immediate remediation**: top up / raise the overage limit on
      `sub-b-iggy2london` now, or accept the account is unusable until the weekly reset
      (`2026-08-23T19:00:00Z`) and let affected slots idle/fail over manually in the meantime.
- [ ] [BACKEND] P2. **Add `overage_status == "rejected"` as an explicit 5th failover-trigger
      condition** alongside the existing four pct/rate-limit checks in the account-monitoring code
      path that feeds `rotate_all_slots_off_account` (see `main.md` § "Account-failover triggers"
      for the current four-condition table; the actual check lives in `server.py` per that section's
      own pointer). Should fire regardless of `weekly_pct`/`five_hour_pct` values, since overage
      rejection is a harder failure than either percentage threshold.
- [ ] [BACKEND] P3. **Classify this failure shape instead of leaving it `death_class: unexplained`**
      — when a killed slot's `account_snapshot.overage_status == "rejected"` at kill time, the
      death classifier should label it something diagnosable (e.g. `account_overage_exhausted`)
      rather than `unexplained`, so this doesn't read as a mystery crash on the next occurrence
      (on this or any other account).

## Codex SSOTs

- `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` — the multi-account auth
  architecture this bug lives in.
- `unified-trading-pm/agents/main.md` § "Account-failover triggers" — the trigger table this issue
  proposes extending.
