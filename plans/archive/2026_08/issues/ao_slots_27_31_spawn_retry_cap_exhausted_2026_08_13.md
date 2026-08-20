---
doc_type: issue
title: AO slots 27 and 31 — spawn retry cap exhausted, ~44h silent, unrelated to the tmux-socket investigation
summary: >-
  Spotted in the activity feed while working an unrelated AO tmux-socket investigation
  (`ao_tmux_session_loss_mid_task_root_cause_2026_08_10`): slot #31 logged `spawn retry cap reached retry 2/2 ·
  pane=no_session · 159240s silent` and slot #27 logged the same pattern at `159890s silent`, both around 2026-08-13
  17:30 UTC. 159240-159890s is ~44.2-44.4 hours — predates that day's tmux incidents by roughly two days, so this is
  very likely a distinct, pre-existing problem, not the same root cause. Neither slot had a currently-registered agent
  record at the time (`GET /api/agents` returned no match for either), consistent with them sitting idle/unclaimed in
  the backlog with exhausted automatic retry, rather than being actively stuck-but-running. Not investigated further at
  the time — flagged and deferred rather than pulled into an unrelated investigation's scope.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, fleet-efficiency, spawn-retry, stuck-slot, dedup-state, account-rotation]
related:
  - /plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md
  - /plans/archive/2026_08/issues/ao_kick_escalation_rate_limit_blind_force_kill_2026_08_14.md
  - /codex/04-architecture/agent-orchestrator-scheduled-jobs.md
  - /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md
created: "2026-08-13"
author: main (Claude Code, interactive session)
parent_epic: orchestrator_master
resolved_by: agent-orchestrator@14deb17714
locked_by:
locked_since:
source: >-
  Operator pasted a live activity-feed dashboard dump mid-turn on 2026-08-13 (~17:30 UTC), asking for any issues in the
  last 17 minutes to be flagged. This finding was one of two flagged (the other, slot #18's dirty-worktree `/done`
  failure, was a transient in-progress condition and not tracked separately). Deferred rather than chased down given the
  primary investigation in progress at the time.
assigned_vm: NA
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
---

# AO slots 27 and 31 — spawn retry cap exhausted, silent ~44h

## What was observed

Activity feed entries, both around 2026-08-13 17:30:2x-3x UTC:

- `#31 spawn retry cap reached — retry 2/2 · pane=no_session · 159240s silent`
- `#27 spawn retry cap reached — retry 2/2 · pane=no_session · 159890s silent`

159240-159890 seconds is approximately 44.2-44.4 hours — placing the START of whatever silence this measures around
2026-08-11 ~21:00-22:00 UTC, roughly two days before that day's `ao_tmux_session_loss_mid_task_root_cause` incidents
began. This timing makes it very unlikely to share that investigation's root cause (the `tmpfs-disk-cleanup.sh` denylist
gap and the split-brain socket fallback were both first-observed 2026-08-13, and the earliest confirmed incident under
that investigation was 2026-08-12 21:47Z — this predates even that).

A quick check via `GET /api/agents` (AO's local API, queried through SSM per `/check-agent-orchestrator`'s pattern)
found **no currently-registered agent record** for either `orch-slot-27` or `orch-slot-31` at query time — consistent
with both slots sitting idle/unclaimed in the backlog with exhausted automatic retry, not with an
actively-running-but-stuck worker.

## What this is NOT

- Not the tmux-socket split-brain (timing predates it by ~2 days; that investigation's supervisor instrumentation was
  not yet armed at the time this silence would have started).
- Not confirmed to be the SAME underlying cause as each other — both slots showing the identical
  `retry 2/2 · pane=no_session` pattern at similar durations is suggestive but not proof of a shared mechanism.

## Root cause found (2026-08-14)

Surfaced while investigating the unrelated overnight kill-storm
(`ao_kick_escalation_rate_limit_blind_force_kill_2026_08_14`, archived) — operator asked "isn't that a done-for account,
why was it getting stuck" about `spawn_retry_cap_reached` noise for these same two slots.

**Both halves of the original todo list, answered together:**

1. **What slot 27/31 were last assigned / why the cap was reached**: `account_id: sub-g-alpavolt`. Live `account_usage`
   row: `weekly_pct: 99`, `account_status: "disabled"`, `overage_status: "rejected"`,
   `overage_disabled_reason: "org_level_disabled"` — the account genuinely exhausted its weekly quota around 2026-08-11
   21:00 UTC (matching both slots' `last_spawned_at`) with no overage path available. `retry_count` hit
   `_SPAWN_HEARTBEAT_MAX_RETRIES` (2) and the automatic retry-on-same-account path correctly gave up — an operator then
   manually paused both slots (`routes/slots_ops.py` `POST /pause` is the only setter of `status="paused"`) as a
   stopgap, since nothing in the code path reassigned them to a healthy account.

2. **Root cause of the 44h-then-58h-then-never-recovering silence**: TWO compounding bugs, both fixed.
   - `kicker._spawn_cap_alerted` (the "alert once per cap episode" dedup) was an **in-memory-only `set[int]`**, wiped on
     every orchestrator restart. `ao-self-pull.sh` restarts the process on close to every LDR HEAD move (checked every
     15 min; this fleet lands commits far more often than that), so the dedup never actually held — the SAME unchanged,
     already-known condition re-fired `spawn_retry_cap_reached` + a Slack page on nearly every restart. Measured: 221
     duplicate pages over 58h for a fact that hadn't changed since 2026-08-11.
   - `check_spawn_heartbeat_timeouts` had **no `status == "paused"` guard**, so an operator-parked slot (the correct,
     intentional stopgap) kept being re-diagnosed by this watchdog forever instead of being left alone like every other
     fleet-wide loop already treats "paused" (`rotate_all_slots_off_account`, `AutoSpawnLoop`).
   - Neither bug is what originally caused the 44h silence noted 2026-08-13 — that was the account exhaustion itself,
     working as designed (correctly stopped retrying a dead account). The bugs are why nothing ever _resolved_ it and
     why it kept noisily re-alerting instead of going quiet or self-healing.

## Fix shipped (agent-orchestrator@14deb17714)

- `server/dedup_state.py` — new `spawn_retry_cap_alerted_path()`, same persisted-set pattern as every other alert-dedup
  in this module.
- `server/worker_liveness/__init__.py` — `WorkerLivenessKicker.__init__` now seeds `_spawn_cap_alerted` from disk
  instead of starting empty.
- `server/worker_liveness/_auth_failover.py` — `check_spawn_heartbeat_timeouts` now (a) skips any `status == "paused"`
  slot entirely, and (b) persists `_spawn_cap_alerted` to disk once per tick.
- Tests: 2 new cases in `tests/test_spawn_heartbeat_liveness.py`, 1 in `tests/test_worker_liveness.py`.
- `quality-gates.sh` green: 3674 passed, 0 ruff/basedpyright issues.

**Live remediation** (operator-authorized, same session): resumed slots 27 and 31 via their own
`POST /api/slots/{id}/resume` (loopback-trusted, the same minimal mutation an operator would make from the dashboard)
rather than writing new spawn-triggering code for this one narrow case — `AutoSpawnLoop`'s existing
`select_account_for_spawn` already picks a fresh healthy account on every spawn regardless of a slot's last-used
`account_id`, so this alone gets them off `sub-g-alpavolt` the next time eligible backlog work reaches them. Verified
live (09:24 UTC): both slots confirmed `status: idle`, `slot_resumed` logged; they are not spawning yet only because
their eligible backlog tasks are currently gated (276 blocked tasks fleet-wide, unrelated to this account issue) —
`account_id` will read stale (`sub-g-alpavolt`) until their next real spawn event, cosmetic only. Healthy candidate
accounts confirmed available at the time: `sub-f-odum2default` (14%/1%), `sub-d-odum1default` (54%/10%), `sub-a-ikenna`
(68%/40%).

## Todo

1. ✅ [INFRA] P2. Determine what task/account slots 27 and 31 were last assigned and why the cap was reached —
   `sub-g-alpavolt`, weekly-quota-exhausted 2026-08-11, org-level overage disabled. See "Root cause found" above.
2. ✅ [INFRA] P2. Root-cause why the spawn retry cap was reached and never recovered — two durable-dedup /
   paused-slot-guard bugs, both fixed in agent-orchestrator@14deb17714. See above.
3. ✅ [INFRA] P3. Decide + execute the recovery — resumed both slots live; `AutoSpawnLoop`'s existing account selection
   handles "use a new account" without further code changes. See "Live remediation" above.

## Progress Log

- 2026-08-13: doc created from a chat-only finding surfaced while working an unrelated investigation — flagged, not
  chased, per the operator's own framing at the time ("I don't want to burn time chasing that down fully right now"). No
  further investigation performed yet.
- 2026-08-14: root-caused (account exhaustion + two durable-dedup/paused-slot bugs), fixed + shipped
  (agent-orchestrator@14deb17714, quality-gates.sh green), and live-remediated (slots 27/31 resumed). Issue resolved.
