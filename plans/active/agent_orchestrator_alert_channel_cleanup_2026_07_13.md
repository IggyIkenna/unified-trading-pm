---
doc_type: plan
title:
  Agent-Orchestrator Alert Channel Cleanup — remove lifecycle churn, daily digest, dedup git-health, richer BLOCKED
  schema
summary:
  The agent-orchestrator-alerts Slack channel is unusable — 1,598 messages in 7 days (~228/day) collapse to only 40
  distinct shapes, and the top 4 are 74% of volume. Root causes — one stuck condition re-firing every 15 min with zero
  suppression (git-health guard, 23%), routine backend lifecycle events treated as pages (dispatched/respawn/recovered,
  ~49%), and flapping with no rate-limit. This plan removes lifecycle churn from Slack (kept in AO logs + GCS ledger),
  adds a backend-scheduled daily-summary job (one digest message + a failure alert if the job dies), state-transition
  dedups the git-health guard, and fixes the worker-BLOCKED Slack schema so options render readably. Target — an
  actionable-only channel (~30–40 human-relevant events/week).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [alerts, slack, agent-orchestrator, dedup, observability, notifications]
related: [alert_quality_overhaul_2026_06_18.md, alert_quality_audit_2026_06_18.md, orchestrator_master.md]
created: "2026-07-13"
last_updated: 2026-07-13
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: backend-engineer
drift_direction: advance-code
---

# Agent-Orchestrator Alert Channel Cleanup

> **Human / LOCAL plan** (`assigned_vm: NA`) — operator-driven, not auto-dispatched. Deliverable was requested as "write
> a plan first"; code changes happen only after this plan is reviewed.

## Context — the 7-day audit (evidence)

Pulled every message from `#agent-orchestrator-alerts` (channel `C0B4N40BY9K`) for 2026-07-06 → 2026-07-13 via the
`SLACK_ALERTS_READER_BOT_TOKEN` reader bot. Raw + analysis saved locally to the workspace `alerts_audit/` dir:

- `alerts_audit/agent-orchestrator-alerts_7d_2026-07-13.jsonl` — 1,598 raw messages (one per line)
- `alerts_audit/analysis_7d_2026-07-13.md` — ranked report, all 40 shapes + examples
- `alerts_audit/grouped_7d_2026-07-13.json` — dedup groups (count + first/last-seen)

**Headline:** 1,598 messages → **40 distinct shapes**. Top 4 = **74%** of volume. True actionable "a human should look"
events ≈ 30–40 in the whole week.

|  Rank | Count |   % | Shape                                          | Disposition (this plan)                           |
| ----: | ----: | --: | ---------------------------------------------- | ------------------------------------------------- |
|     1 |   369 | 23% | ⚠️ VM git-health guard — `is: git fsck FAILED` | **WS-C** dedup (same issue, every 15 min, 4 days) |
|     2 |   337 | 21% | 📋 Plan-health dispatched to slot N            | **WS-A** remove from Slack → digest               |
|     3 |   271 | 17% | 🚒 Escalation dispatched to slot N             | **WS-A** remove from Slack → digest               |
|     4 |   203 | 13% | 🛑 Slot N BLOCKED                              | **WS-D** KEEP, fix schema                         |
|     5 |    93 |  6% | 🚨 Spawn FAILED — no worker                    | **KEEP** — failure signal, already state-deduped  |
|   6–9 |   214 | 13% | ✅ RECOVERED / Spawn RECOVERED / git RECOVERED | **WS-A** remove from Slack → digest               |
| 10–40 |  ~110 |  7% | escalation NOT/RESOLVED, hygiene, stash, drift | KEEP (genuine signal / low volume)                |

## Root causes

1. **One stuck condition, zero suppression.** `agent-orchestrator/scripts/fleet-git-health-guard.sh` POSTs the raw
   webhook every 15 min, bypassing all server-side dedup. Confirmed a **single identical body** —
   `instruments-service: git fsck FAILED` on VM `ip-172-31-5-118`, unresolved since 07-09 → 369 identical pages. This is
   a **genuine actionable alert that went unactioned precisely because it was buried** in 369 duplicates — catching real
   signals like this fast is the whole point of the cleanup. Dedup makes it visible; it does not downgrade it. (The
   underlying git corruption is a **separate** fix, out of scope here per operator — this plan only silences the
   repeat.)
2. **Backend lifecycle events posted as pages (~49%).** `dispatched` / `auto-respawn` / `recovered` are done
   automatically by the backend and need no human — they belong in AO logs + the GCS ledger, not Slack.
3. **Flapping without rate-limit.** Spawn-FAILED (93) and BLOCKED (203) fire per-event with no "only if unrecovered"
   gate.

Note: a prior **`alert_quality_overhaul_2026_06_18.md`** (complete, archived) improved alert _wording_ and built the
`dedup_state.py` state-transition infra — but did not stop lifecycle events from paging or add a digest. This plan is
the follow-on that finishes the job.

## Codex SSOTs

- No dedicated alerting codex doc exists yet — **WS-E** stubs one
  (`codex/04-architecture/agent-orchestrator-alerting.md`) capturing the actionable-only channel contract + digest
  model, so this becomes the durable SSOT.
- Related: `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
  `codex/12-agent-workflow/async-wait-and-poll-discipline.md` (poll/heartbeat discipline for the new loop).

## Design

**WS-A — Stop posting lifecycle churn to Slack (keep logs + GCS).** Each churn notifier keeps its `_persist_to_gcs(...)`
call (so `GET /api/alerts` + dashboard + the `unified-trading-cicd-events` ledger are unchanged) and drops **only** its
`_post(...)` Slack call. Notifiers + their callers:

| Notifier (`server/notifications/slack.py`) | Called from                          | Shape removed  |
| ------------------------------------------ | ------------------------------------ | -------------- |
| `notify_plan_health_dispatched` (:517)     | `plan_health.py:78`                  | #2 (337)       |
| `notify_escalation_dispatched` (:533)      | `escalation.py:203`                  | #3 (271)       |
| `notify_agent_stuck_respawned` (:469)      | `worker_liveness/_respawn.py:457`    | (auto-respawn) |
| `notify_spawn_recovered` (:449)            | `autospawn.py:858`                   | #8 (52)        |
| `notify_slot_recovered` (:278)             | `health.py:167`                      | #6 (90)        |
| `notify_git_staleness_resolved` (:312)     | `worker_liveness/_git_alerts.py:379` | #9 (16)        |

**Contract: success is silent, FAILURE still pages.** Removing a dispatch's success ping must not blind us to that job
_failing_. Two asymmetric cases:

- **Escalation dispatch failure — already covered.** `escalation.py:394` pages via `autospawn.alert_spawn_failed(...)`
  (the `orchestrator_spawn_failure_slack_alert_gap_2026_06_25` fix), deduped + re-armed on a clean spawn. That page is
  exactly shape #5 (Spawn FAILED — no worker) — hence #5 is **KEEP**, not noise. Removing `notify_escalation_dispatched`
  is safe; failures still alert. WS-A only adds a regression test asserting this.
- **Plan-health dispatch failure — a GAP.** `plan_health.py:171` only writes the DB activity log
  (`plan_health_dispatch_failed`) — it never pages Slack. So removing the success ping would make plan-health fully
  silent. WS-A must **add** a `notify_plan_health_dispatch_failed` page (mirror `alert_spawn_failed`: deduped,
  best-effort) at that failure branch.

**WS-B — Daily-summary job (new backend-scheduled loop).** New `DailySummaryLoop` in `agent-orchestrator/server/`,
modelled on `UsagePoller` / `AutoSpawnLoop` (`.start()`/`.stop()` wired in `server.py` ~L213). Every 24 h it reads the
**DB activity log** (`log_activity` events) since a persisted cursor (new `dedup_state.daily_summary_cursor_path()`) —
that is the authoritative stream that already records `plan_health_dispatched` / `escalation_dispatched` /
`*_dispatch_failed` / `spawn_recovered` / `slot_recovered` / `slot_blocked` (the dispatch **success** pings never hit
the GCS ledger, so the activity log — not the ledger — is the correct source; the GCS ledger is folded in for CI/watcher
alerts). It aggregates counts by event type and posts **one** Slack digest — total plan-health dispatches, escalation
dispatches, respawns, recoveries, blocks, plus any failures in the window and a short "actionable this period: N" line.
If the job body throws, it posts a `notify_daily_summary_failed` page (so a dead digest job is itself alerted). Interval

- enable flag live in typed config (no `os.getenv`).

**WS-C — Dedup the git-health guard.** `fleet-git-health-guard.sh` runs as a per-VM root cron (not through the server),
so dedup lives in the script: a local state file (e.g. `~/.cache/git-health-guard/last_alerted.json`) keyed by the
sorted problem signature. POST only when the signature **changes**, on **RESOLVED** (problems clear), or on a re-remind
interval (**D2 = 1 h**). Result: 1 page on break + 1 on fix + an hourly nudge while unresolved (≤24/day), instead of the
current 96/day.

**WS-D — Richer BLOCKED schema (keep all).** `BlockedRequest` (`routes/slots_worker.py:1032`) **already carries**
`options: list[str]` + `recommendation` — but `notify_slot_blocked` (slack.py:172) is called with only `req.question`
(slots_worker.py:1052), so the worker crams everything onto one line. Fix: pass `req.options` + `req.recommendation`
through and render them multi-line, mirroring `notify_operator_gated_blocked` (`"\n".join(f"• {o}" …)` + a
`*Recommendation:*` section). Small, data-already-present, low-risk.

**WS-E — Verify + document.** Re-pull a 24–48 h window post-deploy to confirm volume drop; stub the codex SSOT.

## Decisions

- **D1 — Spawn-FAILED (#5, 93) → RESOLVED: KEEP.** Operator (2026-07-13): "if it fails then only alert us." It is the
  failure signal, already state-deduped + re-armed on clean spawn. Its total also appears in the digest. No suppression.
- **D2 — git-health re-remind interval → RESOLVED: 1 h.** Operator (2026-07-13): a genuine issue should be fixable
  within the hour; if still unresolved, re-remind hourly. Drops the guard from every-15-min (96/day) to ≤24/day while
  unresolved (1 on break + 1 on fix + hourly nudge).
- **D3 — Digest scope → RESOLVED.** Operator: include plan-health + escalation dispatch totals "and any other info". So
  the digest carries all lifecycle counts (dispatches, respawns, recoveries, blocks) + any failures in the window + a
  short "actionable this period: N" line.

## Todos

- [ ] [BACKEND] P1. WS-A: drop the `_post(...)` Slack call (keep `_persist_to_gcs` where present) in the six churn
      notifiers in `server/notifications/slack.py` (`notify_plan_health_dispatched`, `notify_escalation_dispatched`,
      `notify_agent_stuck_respawned`, `notify_spawn_recovered`, `notify_slot_recovered`,
      `notify_git_staleness_resolved`); extend `tests/test_alert_quality_overhaul.py` to assert those post NO Slack
      payload.
- [ ] [BACKEND] P1. WS-A: ADD a `notify_plan_health_dispatch_failed` page at `plan_health.py:171` (the failure branch is
      currently Slack-silent); add a regression test asserting escalation dispatch failure STILL pages via
      `alert_spawn_failed` (`escalation.py:394`) after the success ping is removed. (Success silent, failure pages.)
- [ ] [BACKEND] P1. WS-B: add `DailySummaryLoop` (24 h, typed-config interval + enable) that reads the **DB activity
      log** since a persisted cursor, aggregates by event type (dispatches / respawns / recoveries / blocks / failures),
      and posts one `notify_daily_summary` digest with totals + an "actionable this period: N" line; wire
      `.start()/.stop()` in `server.py`; unit-test the aggregation + cursor advance.
- [ ] [BACKEND] P1. WS-B: add `daily_summary_cursor_path()` to `server/dedup_state.py` + `notify_daily_summary` and
      `notify_daily_summary_failed` in `slack.py`; job body wrapped so any exception fires the failure page.
- [ ] [INFRA] P1. WS-C: add state-file dedup to `scripts/fleet-git-health-guard.sh` — POST only on signature-change /
      RESOLVED / re-remind (D2 = 1 h); add a `--dry-run` self-test proving no repeat POST for an unchanged signature.
      (Guard is a KEEP — dedup so genuine issues surface fast, do NOT remove.)
- [ ] [BACKEND] P2. WS-D: thread `req.options` + `req.recommendation` from `routes/slots_worker.py:1052` into
      `notify_slot_blocked`; render options as a bulleted multi-line section + a `*Recommendation:*` section; test the
      rendered blocks.
- [x] [OPERATOR] P1. ✅ D1/D2/D3 all resolved by operator (2026-07-13) — see Decisions. Plan unblocked for
      implementation.
- [ ] [BACKEND] P2. WS-E: deploy agent-orchestrator to the central VM; re-pull a 24–48 h alert window and confirm
      lifecycle churn is gone from Slack + volume dropped to the actionable-only target. Evidence: post-deploy jsonl in
      `alerts_audit/`.
- [ ] [REVIEW] P2. WS-E: stub `codex/04-architecture/agent-orchestrator-alerting.md` (actionable-only contract + digest
      model + guard-dedup) as the durable SSOT; add a one-liner to CLAUDE.md's conditional index.

## Progress Log

- **2026-07-13** — Audit complete. 1,598 alerts / 7 days → 40 shapes, top-4 = 74%. Root causes + code touch-points
  identified (see Design). Artifacts in `alerts_audit/`. Plan authored (human/LOCAL).
- **2026-07-13 (rev)** — Operator clarifications folded in: (1) plan-health-dispatched + escalation-dispatched success
  pings removed from Slack, but FAILURES must page — found plan-health failure is currently Slack-silent (gap → WS-A
  adds a page) while escalation failure already pages (`alert_spawn_failed`); (2) both dispatch types feed the daily
  digest via the DB activity log (their success pings never hit the GCS ledger, so digest source switched to the
  activity log); (3) Spawn-FAILED #5 reclassified KEEP (it's the failure signal); (4) git-health guard reaffirmed a
  genuine KEEP — dedup only. D1 + D3 resolved; only D2 (re-remind interval) open. Awaiting D2 + review before code.
- **2026-07-13 (D2)** — D2 resolved: git-health re-remind interval = **1 h** (operator: fixable within the hour, else
  hourly nudge). All decisions closed; plan unblocked for implementation, pending operator go-ahead + commit.
