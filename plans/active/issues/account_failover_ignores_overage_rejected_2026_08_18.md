---
doc_type: issue
title: >-
  Account-failover monitor never checks overage_status — overage-rejected accounts keep killing
  sessions fleet-wide (15+ kills/18h on slot 2, 4 accounts) instead of triggering rotation
summary: >-
  **UPDATED 2026-08-18 ~20:21Z — scope expanded fleet-wide.** Originally filed against
  `sub-b-iggy2london` (Ikenna sub-B, `weekly_pct=90`, `overage_status=rejected`,
  `overage_disabled_reason=out_of_credits`), which killed slot-2 three times on 2026-08-18
  (14:55Z / 15:31Z / 16:46Z) on a ~35min cadence — confirmed directly from the `tmux_session_lost`
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

  **Fleet-wide confirmation (review agent agt-8de6ec, 2026-08-18 ~20:21Z)**: slot 2 alone has hit
  `tmux_session_lost` 15+ times over ~18h (2026-08-18T01:39Z through 19:46Z, roughly every
  1-1.5h), `death_class: unexplained` every time, across **4 rotating accounts**:
  `sub-b-iggy2london` (out_of_credits, most recent), `sub-h-igboestates` (org_level_disabled,
  19:46Z death), `sub-f-odum2default` (org_level_disabled, 2026-08-14/15), `sub-a-ikenna`
  (out_of_credits, 2026-08-14). This predates the current session lineage — pattern goes back to
  at least 2026-08-14. This confirms `overage_status` has (at least) two distinct rejection
  reasons the failover table misses — `out_of_credits` AND `org_level_disabled` — and that the
  gap is systemic across the account pool, not one account's fluke. Two open hypotheses (neither
  confirmed): (1) account rotation is repeatedly landing slot 2 on accounts already at their
  overage ceiling instead of excluding `org_level_disabled`/`out_of_credits` accounts from the
  rotation pool, or (2) the review role's long persistent loop burns through its assigned
  account's overage budget faster than rotation replenishes it.

  Found by review agent (agt-15d551), independently confirmed by main (agt-a03340) 2026-08-18
  ~17:05Z by pulling the three `tmux_session_lost` events directly via `/api/activity` and cross-
  checking `/api/accounts` for the account's live `overage_status`/`overage_disabled_reason`
  fields. Scope expanded by review agent agt-8de6ec 2026-08-18 ~20:21Z (see above). Notable:
  main's OWN session (`agt-a03340`) also runs on `sub-b-iggy2london` (`account_id` returned at
  `/api/agents/register` time) — main has not yet been killed by this mechanism as of filing, but
  is exposed to the same risk.
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
context_scope:
  [
    /codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md,
    agents/main.md,
    agent-orchestrator/server/server.py,
    /plans/active/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md,
    /plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md,
  ]
---

# Account-failover monitor ignores `overage_status` — recurring slot-2 kills fleet-wide

## Evidence

**Fleet-wide (agt-8de6ec, ~20:21Z)**: slot 2 hit `tmux_session_lost` 15+ times over
2026-08-18T01:39Z–19:46Z (~18h, roughly every 1-1.5h), `death_class=unexplained` every time, no
OOM/rate-limit-in-tail/core-dump. Near-universal correlation: at death time the active account's
`account_snapshot` already showed `overage_status=rejected`, across 4 rotating accounts:

| account            | overage_disabled_reason | last/example death |
| ------------------ | ------------------------ | ------------------- |
| `sub-b-iggy2london` | out_of_credits           | most recent (see table below) |
| `sub-h-igboestates` | org_level_disabled        | 2026-08-18 19:46Z    |
| `sub-f-odum2default` | org_level_disabled       | 2026-08-14/15        |
| `sub-a-ikenna`      | out_of_credits           | 2026-08-14           |

Pattern predates the current session lineage — traces back to at least 2026-08-14.

**Original 3-kill detail (main, ~17:05Z)**: three `tmux_session_lost` events, `agent-orchestrator`
`/api/activity`, all `slot_id=2`, `tmux_session=orch-slot-2`, `new_status=killed`,
`death_class=unexplained`:

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
- [x] N. ✅ [BACKEND] P2. **Add `overage_status == "rejected"` as an explicit 5th failover-trigger
      condition** alongside the existing four pct/rate-limit checks in the account-monitoring code
      path that feeds `rotate_all_slots_off_account` (see `main.md` § "Account-failover triggers"
      for the current four-condition table; the actual check lives in `server.py` per that section's
      own pointer). Should fire regardless of `weekly_pct`/`five_hour_pct` values, since overage
      rejection is a harder failure than either percentage threshold. Must cover BOTH observed
      `overage_disabled_reason` values (`out_of_credits` and `org_level_disabled`), not just one. Extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 7 (na-eligibility-audit 2026-08-19, ao tranche, RECLASSIFY per-todo split).
- [x] N. ✅ [BACKEND] P2. **Investigate whether account rotation excludes overage-rejected accounts from
      its selection pool.** Fleet-wide evidence (4 accounts, 15+ kills/18h on slot 2 alone) suggests
      rotation may be repeatedly re-landing on accounts already at their overage ceiling rather than
      skipping them — check the rotation-pool selection logic for an `overage_status` filter (or
      lack thereof), separate from the failover-trigger fix above (a trigger fix stops sessions
      dying on an already-bad account; a pool-exclusion fix stops rotation assigning a bad account
      in the first place). Extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 8 (na-eligibility-audit 2026-08-19, ao tranche, RECLASSIFY per-todo split).
- [ ] [BACKEND] P3. **Check whether the review role's persistent loop burns through its assigned
      account's overage budget faster than rotation replenishes it** — alternate/complementary
      hypothesis to the pool-exclusion one above; review agent agt-8de6ec flagged this as
      unconfirmed. If review's long-running loop pattern is a meaningfully higher burn rate than
      other roles, it may need its own rotation cadence rather than sharing the general pool logic.
- [x] N. ✅ [BACKEND] P3. **Classify this failure shape instead of leaving it `death_class: unexplained`**
      — when a killed slot's `account_snapshot.overage_status == "rejected"` at kill time, the
      death classifier should label it something diagnosable (e.g. `account_overage_exhausted`)
      rather than `unexplained`, so this doesn't read as a mystery crash on the next occurrence
      (on this or any other account). Extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` item 9 (na-eligibility-audit 2026-08-19, ao tranche, RECLASSIFY per-todo split).

## Interaction analysis vs. the CI-escalation-reserve pool (2026-08-18, later same day)

**Question**: would adding `overage_status=="rejected"` as a 5th failover trigger (feeding
`rotate_all_slots_off_account`) collide with the CI-escalation/scheduled-task reserve pool (slots
29-33), which a sibling investigation
(`/plans/active/issues/ao_finished_oneshot_sessions_not_reaped_blocks_escalation_dispatch_2026_08_18.md`)
was independently live-debugging the same day? Read `rotate_all_slots_off_account`
(`server/server.py:1014`) directly to ground this rather than reason from the docstring alone.

**Conclusion: no destructive collision on the currently-observed symptom; net positive for one
population, with one narrow unconfirmed race worth flagging.**

- `rotate_all_slots_off_account` explicitly SKIPS any slot that is `paused`/`killed` or has no live
  `tmux_session` (`if slot.account_id != account_id or slot.status in ("paused", "killed") or not
  slot.tmux_session: continue`). The sibling reserve-pool incident this same day
  (`ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`) found all 3 reserve slots `status=paused`,
  `worker_alive=false` — that exact population is **outside the proposed trigger's reach entirely**.
  Adding the trigger would not rescue an already-paused reserve slot; that still needs the manual
  `POST /api/slots/{id}/resume` path the operator used. So there is no regression risk to today's
  paused-slot remediation.
- For a reserve slot that is LIVE (has a tmux session) and bound to an overage-rejected account —
  confirmed live this same session: slot 33 currently reads `status=idle`,
  `account_id=sub-b-iggy2london`, `overage_status=rejected`/`overage_disabled_reason=out_of_credits`
  — the proposed trigger WOULD be eligible to fire and would proactively kill+respawn that slot onto
  a healthy account via `spawn_with_account_bg`. This is a net improvement over today: it evicts a
  doomed reserve slot BEFORE it dies mid-escalation-dispatch (today's failure mode), rather than
  leaving it to die silently and read as `death_class: unexplained`.
- **Genuine but unconfirmed race worth flagging**: `spawn_with_account_bg` kills the OLD session
  first, then spawns a new one on a background thread — not atomic. `_pick_free_slot`'s freedom check
  (`not tmux_spawn.has_session(...)`) reads the live tmux state directly, so in the brief window
  between the old session's kill and the new one's spawn, a reserve slot mid-rotation would read as
  "free" to a concurrently-dispatching escalation. Whether the escalation dispatcher and the
  rotation's own background spawn can then race to claim the SAME slot (and what happens if they
  do) was NOT verified in this session — a genuine code question for whoever implements the trigger,
  not something to guess at.
- **Resource-contention consideration, not a collision**: if implemented, a mass rotation firing on
  an account with many bound slots at once (main's own session + reserve + workers, per this doc's
  fleet-wide evidence) would compete for the same scarce headroom-account pool the reserve pool also
  needs. `rotate_all_slots_off_account` already degrades gracefully here — `select_account_for_spawn`
  returning `None` logs `account_rotation_no_fallback` and skips (leaves the slot on the bad account,
  i.e. no worse than today), it does not corrupt state or crash. So the worst case under pool
  scarcity is "no-op", not a new failure mode — but it does mean the trigger's actual effectiveness
  for the reserve pool specifically is bounded by how much headroom the account pool has at the
  moment it fires, which ties directly into this doc's own P2 todo ("spread 31/32/33 across more
  than one account instead of triple-booking sub-b").

**Verdict**: implement-safe with respect to the reserve pool as currently understood; the one open
item (mid-rotation free-slot race) should be checked by whoever writes the trigger, not assumed
either way.

## Codex SSOTs

- `/codex/12-agent-workflow/claude-cli-multi-account-headless-auth.md` — the multi-account auth
  architecture this bug lives in.
- `unified-trading-pm/agents/main.md` § "Account-failover triggers" — the trigger table this issue
  proposes extending.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:cf5ec6b8ba855a80]: RECLASSIFY (per-todo split) — 3 of 4 remaining todos (add the 5th failover trigger, investigate rotation-pool exclusion, classify the failure shape) extracted to `plans/active/ao_satellite_ao_dispatch_batch25_2026_08_19.md` items 7-9. Doc stays NA for the sole remaining item ([OPERATOR] immediate remediation decision: top up vs. accept unusable until weekly reset 2026-08-23).
- **context-scout 2026-08-19**: populated context_scope (5 entries).
