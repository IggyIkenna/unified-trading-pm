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
related:
  [
    /plans/archive/2026_06/alert_quality_overhaul_2026_06_18.md,
    /plans/audit/results/alert_quality_audit_2026_06_18.md,
    /plans/epics/orchestrator_master.md,
  ]
created: "2026-07-13"
last_updated: 2026-07-14
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: backend_engineer
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
  (`/codex/04-architecture/agent-orchestrator-alerting.md`) capturing the actionable-only channel contract + digest
  model, so this becomes the durable SSOT.
- Related: `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
  `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` (poll/heartbeat discipline for the new loop).

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

- **D1 — Spawn-FAILED (#5, 93) → RESOLVED: KEEP** (was: KEEP/no-suppression as recorded here; **superseded same-day by
  todo 13** — a later 2026-07-13 operator decision reversed this to summary-only/no-direct-page, downgrading
  `notify_spawn_failed` to `logger.info`; this Decisions entry was never updated to match at the time — corrected
  2026-07-14, finding 185). Operator (2026-07-13): "if it fails then only alert us." It is the failure signal, already
  state-deduped + re-armed on clean spawn. Its total also appears in the digest. See todo 13 for current behavior (no
  direct page; rolls into the daily digest instead).
- **D2 — git-health re-remind interval → RESOLVED: 1 h.** Operator (2026-07-13): a genuine issue should be fixable
  within the hour; if still unresolved, re-remind hourly. Drops the guard from every-15-min (96/day) to ≤24/day while
  unresolved (1 on break + 1 on fix + hourly nudge).
- **D3 — Digest scope → RESOLVED.** Operator: include plan-health + escalation dispatch totals "and any other info". So
  the digest carries all lifecycle counts (dispatches, respawns, recoveries, blocks) + any failures in the window + a
  short "actionable this period: N" line.

## Todos

- [x] 1. ✅ [BACKEND] P1. WS-A: dropped the `_post(...)` Slack call in the six churn notifiers in
      `server/notifications/slack.py` (`notify_plan_health_dispatched`, `notify_escalation_dispatched`,
      `notify_agent_stuck_respawned`, `notify_spawn_recovered`, `notify_slot_recovered`,
      `notify_git_staleness_resolved`) — now `logger.info` (AO logs) instead. `test_alert_quality_overhaul.py` asserts
      each logs + does NOT page. — agent-orchestrator@038beeb; full `quality-gates.sh` green (1212 pytest).
- [x] 2. ✅ [BACKEND] P1. WS-A: added `notify_plan_health_dispatch_failed` (GCS-persisted + deduped 1h via
      `dedup_state.plan_health_dispatch_failed_path`), fired from the `plan_health.py` do_spawn failure branch (was
      Slack-silent); test asserts dispatch SUCCESS is silent but FAILURE pages. Escalation failure already pages via
      `alert_spawn_failed`. — agent-orchestrator@038beeb.
- [x] 3. ✅ [BACKEND] P1. WS-B: added `DailySummaryLoop` (`server/daily_summary.py`) — reads the DB activity log since a
      persisted cursor via `activity_rollup`, posts one `notify_daily_summary` digest (counts by type + failures +
      total), advances the cursor; wired `.start()/.stop()` + supervision in `server.py`; `test_daily_summary.py` covers
      aggregation + cursor advance. — agent-orchestrator@038beeb.
- [x] 4. ✅ [BACKEND] P1. WS-B: added `daily_summary_cursor_path()` to `server/dedup_state.py` + `notify_daily_summary`
      and `notify_daily_summary_failed` in `slack.py`; `_tick_and_report` wraps the tick so any exception fires the
      failure page (tested). Config: `daily_summary_enabled`/`daily_summary_interval_seconds`. —
      agent-orchestrator@038beeb.
- [x] 5. ✅ [INFRA] P1. WS-C: added state-file dedup to `scripts/fleet-git-health-guard.sh` — posts only on
      signature-change / RESOLVED / 1h re-remind (D2); `--self-test` proves the state machine (new→skip→remind→new→
      resolved→none, PASS). Guard KEPT, just deduped. — agent-orchestrator@038beeb.
- [x] 6. ✅ [BACKEND] P2. WS-D: threaded `req.options` + `req.recommendation` from `routes/slots_worker.py` into
      `notify_slot_blocked`; options now render as a bulleted full-width section + a `*Recommendation:*` section (was
      crammed onto one line via the 2-column `fields` layout); `test_slack_notifications.py` asserts the multi-line
      render. — agent-orchestrator@038beeb.
- [x] [OPERATOR] P1. ✅ D1/D2/D3 all resolved by operator (2026-07-13) — see Decisions. Plan unblocked for
      implementation.
- [ ] [BACKEND] P0. WS-E: **auto-deploys — verification pending only.** Code is landed on LDR (WS-A/B/C/D). The prod
      backend runs uvicorn `--reload` **[CORRECTED 2026-07-13, verify-rerun finding 213: VM-verified (twice,
      2026-07-12/13) the installed orchestrator.service ExecStart runs uvicorn WITHOUT `--reload`; deploy-currency =
      scripts/ao-self-pull.sh 15-min root cron (FF-pull + systemctl restart on HEAD change) per
      epics/orchestrator_master.md §ao-self-pull (SSOT) — verify WS-E by confirming a real cron-triggered restart
      (journalctl/ExecMainStartTimestamp), NOT by assuming auto-reload.]** (operator 2026-07-13), so it restarts on the
      new code automatically once it reaches the VM — **no manual restart needed**. The git-health guard cron (WS-C)
      picks up its script change on its next tick. The ONLY remaining step is the **24–48 h verification observation
      window**: re-pull with `alerts_audit/fetch_alerts.py` after the code has been live ~24–48 h, confirm lifecycle
      churn is gone / volume at the actionable-only target, and drop the post-deploy jsonl in `alerts_audit/`.
- [x] 8. ✅ [REVIEW] P2. WS-E: stubbed `/codex/04-architecture/agent-orchestrator-alerting.md` (actionable-only
      contract + digest model + guard-dedup) as the durable SSOT; added the one-liner to CLAUDE.md's conditional index
      (size-cap QG green, 29,668 B / 40,960). — unified-trading-pm (this commit).
- [x] 9. ✅ [BACKEND] P2. WS-B follow-up (first live digest, 2026-07-13 16:15 UTC, 1706 events / 5 failures): the digest
      announced "5 failure event(s) — see the counts below" but showed only the top-25 types by frequency, and the
      failure rows (`worker_kick_failed` etc.) ranked below #25 were truncated out of view. Fixed `notify_daily_summary`
      to append any below-#25 failure row (🔴-marked) rather than drop it; `test_daily_summary.py` locks it
      (`test_digest_never_truncates_a_failure_out_of_view`); full `quality-gates.sh` green (1216 pytest). —
      agent-orchestrator@f79f028.
- [x] 10. ✅ [REVIEW] P2. Documented **every digest field + every `event_type`** in the codex SSOT
      `/codex/04-architecture/agent-orchestrator-alerting.md` (operator ask, 2026-07-13): a "Digest anatomy" field table
      (Since / Total events / N failure event(s) / Activity / Footer) + a "Digest event glossary" grouping all ~25 event
      types by lifecycle stage (boot·spawn / task / git-health / liveness·self-healing / plan-health·escalation) with
      their `log_activity` code refs. Frontmatter-schema + prettier green. — unified-trading-pm (this commit).
- [x] 11. ✅ [BACKEND] P1. WS-B bug (operator: "4 different summary alerts already"): the digest fired **once per server
      restart**, not once per interval. `DailySummaryLoop._loop` called `_tick_and_report()` immediately (30 s) on every
      start; prod runs uvicorn `--reload`, so each code change reaching the VM restarted the server → a boot digest. The
      channel showed 5 digests on 2026-07-13 (07:15 scheduled, then 10:45/11:27/11:31/11:46 as AO code landed) — windows
      non-overlapping (cursor kept the data honest), so noise not double-counting. Fixed: anchored the wait to the
      persisted cursor via `_seconds_until_due()` (0 when overdue/never-summarised → fire; >0 → a restart waits out the
      remainder). First-boot + genuinely-overdue still post. Tests: recent-cursor defer, absent/stale due; full
      `quality-gates.sh` green (1219 pytest). — agent-orchestrator@d5c5cae.
- [x] 12. ✅ [BACKEND] P2. WS-A gap (operator: "escalation RESOLVED alerts still coming"): the escalation-RESOLVED
      all-clear (`:ballot_box_with_check: escalation RESOLVED — <repo>`, verdict `qg_v2_green`) still paged after WS-A —
      it's an automatic recovery/closure bookend (a dispatched CI/CD wall confirmed clear), not operator-actionable. The
      original audit had parked it in the low-volume tail as KEEP, but it belongs with the other RECOVERED/RESOLVED
      bookends. Downgraded `notify_escalation_resolved` from `_post` → `logger.info` (WS-A/D11 pattern); the caller
      already logs `escalation_resolved` to the activity log, so it stays in the digest. UNRESOLVED / re-escalation-cap
      still pages CRITICAL (verified `_mark_unresolved_and_maybe_reescalate`). Added to the recovery-bookends
      logged-not-paged test; codex "does NOT page" list updated. Full `quality-gates.sh` green (1219 pytest). —
      agent-orchestrator@8843519.
- [x] 13. ✅ [BACKEND] P1. Operator decision (2026-07-13, reverses the audit's shape-#5 KEEP): **spawn failures →
      summary only, no direct page.** Downgraded `notify_spawn_failed` from `_post` → `logger.info` (kept its GCS-ledger
      persist so `GET /api/alerts` still records it). The callers already write `autospawn_failed` (AutoSpawn path) /
      `escalation_dispatch_failed` (escalation path) to the activity log, so spawn failures still roll into the daily
      digest — a persistent inability to spawn shows as a rising count. AutoSpawn retries + watchdog self-heal, so a
      transient failure isn't per-event actionable; auth-shaped failures still page via the account drop-from-rotation
      alert, and unresolved/re-escalation escalations still page CRITICAL. The `alert_spawn_failed` skip/dedup tests are
      unaffected (they mock the notifier); rewrote `test_notify_spawn_failed_*` → logged-not-paged. codex "does NOT
      page" / "DOES page" updated. Full `quality-gates.sh` green (1221 pytest). — agent-orchestrator@770f12f.
- [x] 14. ✅ [BACKEND] P1. Operator ("the api codes are already known, why are we guessing?"): a spawn failure was
      classified by GUESSING from the pane-tail (`_spawn_failure_is_auth_shaped`: `/login`, `invalid api key`) — which
      mislabelled a busy-but-alive worker (slot 8: pane showed live tasks + "wait for it") as "likely a dead/expired
      setup-token." Replaced the guess at `do_spawn`'s failure branch with a **definitive token probe**
      (`_classify_spawn_failure_via_token_probe`, the same 1-token call the poller uses): `401/403` → dead token →
      drop - CRITICAL `notify_account_auth_failed` re-mint page (the alert the operator cares about); `429` → mark
      `rate_limited` (transient, NO page); `200` → token healthy → NOT auth → summary-only spawn record (a working
      account is never dropped on a misleading pane); `5xx`/network → transient, no mark. Verified all 4 live tokens
      probe 200 (no dead token now; that's why no auth alert fired). Tests: dead-token drops, healthy-token-with-auth
      -pane does NOT drop, 429 marks rate_limited, 403 drops, network no-op. codex "code-based classification" section
      added. Full `quality-gates.sh` green (1225 pytest). — agent-orchestrator@67de599.
- [x] 15. ✅ [BACKEND] P1. Operator ("check EVERY alert, do the audit properly") — **complete pager audit** instead of
      one-at-a-time. Enumerated all 40 `slack._post` notifiers + grouped the live 7-day channel by shape; found 3
      automatic self-healing/lifecycle events still paging. Downgraded to `logger.info` (ledger persist kept; callers
      already log the digest events): `notify_agent_stuck_escalation` ("Auto-respawn FAILED" — the trigger),
      `notify_stash_on_done` (32/wk), `notify_autospawn_flap`. KEPT the actionable set (BLOCKED, auth-failed/recovered,
      digest(\_failed), plan-health-failed, escalation-unresolved/abandoned, setup-token-expiring,
      all-accounts-unusable, `notify_slot_quarantined` = dispatch STARVATION not a routine skip, `notify_watchdog_kill`
      = already gated to cap-hit). codex gains the **Complete pager audit table** as the durable SSOT; regression test
      `test_self_healing_lifecycle_alerts_are_summary_only`. Full `quality-gates.sh` green. —
      agent-orchestrator@bb87f59.
- [ ] [INFRA] P0. Separate fix (surfaced by the audit): the daily `:broom: Plan-hygiene sweep FAILED` is a PM **Cloud
      Run cron** (`uts-prod-plan-hygiene-sweep`, 05:00) that re-posts the SAME unchanged failure
      (`hard failures: 1, soft     warnings: 1`) every day with no dedup (7/wk). Fix the underlying hygiene failure OR
      add read-back dedup to that job — it does NOT flow through `slack._post`, so it's out of the AO-notifier scope.
      Owner: PM/infra.
- [x] 16. ✅ [BACKEND] P1. Operator (2026-07-14): "the agent working on it haven't done the job properly... check the
      channel for the past 24 hours." Pulled a fresh 24h window via `SLACK_ALERTS_READER_BOT_TOKEN` (134 msgs) and found
      the SAME-DAY git-staleness restore (commit `1be792c`, todo above the fold — a separate operator-directed fix that
      landed same-day, outside this plan's own todos) was flapping badly: 21x `git RED >30min` + 19x `git RECOVERED`,
      several "recovered after 0m" repeating every few minutes for hours. Root cause: `slot-git-status-report.sh`
      rebuilds each slot's whole repo snapshot via a bash walk that can transiently drop one repo for a single ~5-min
      cycle (a `pushd`/`git status` hiccup); that lone blip read as "recovered," which cleared the 4h re-alert throttle,
      so the next real-red tick re-alerted immediately. Fixed: a clean reading must sustain past a new
      `GIT_CLEAN_CONFIRM_S` (15 min) before it fires the RESOLVED bookend or clears the throttle — a single blip now
      leaves the episode fully armed. — agent-orchestrator@50557aa; full `quality-gates.sh` green (1255 pytest).
- [x] 17. ✅ [BACKEND] P1. Same sweep, two more repeat-page sources fixed in the same commit: (1)
      `notify_plan_health_dispatch_failed`'s 1h cooldown had a read-check-write race (no lock) — two near-concurrent
      dispatch failures could both read a stale cooldown, observed live as the same slot paging twice 6 minutes apart;
      fixed with an in-process `threading.Lock` (single-process `uvicorn`, no cross-process lock needed). (2)
      `notify_escalation_unresolved` repeated 7x for one repo in <3h — not a missing dedup but escalation OVER-CREATION:
      `_find_open_escalation` only collapses duplicates while non-terminal, so a wall still red after a prior escalation
      hit the re-escalation cap spawns a brand-new escalation that repeats its own full re-escalate/cap-hit page pair.
      Left self-healing (fresh-worker retry) untouched — cooldown-deduped the PAGE only, per
      `{repo}:{wall_type}:{reescalating|cap_hit}` (3h), cleared on resolution so a genuinely new break still pages
      immediately. — agent-orchestrator@50557aa (same commit as todo 16).
- [x] 18. ✅ [REVIEW] P2. Codex SSOT `/codex/04-architecture/agent-orchestrator-alerting.md` updated with the flap
      root-cause + the two repeat-page-hardening fixes (new "Git-staleness paging" bullet + a "Repeat-page hardening"
      section); `last_reviewed` bumped to 2026-07-14. — unified-trading-pm (this commit).

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
- **2026-07-13 (implemented)** — WS-A/B/C/D shipped in one commit **agent-orchestrator@038beeb**; full
  `quality-gates.sh` green (ruff + basedpyright + **1212 pytest** + dashboard tsc/vitest). WS-A: 6 churn notifiers →
  INFO logs + `notify_plan_health_dispatch_failed` (deduped 1h). WS-B: `DailySummaryLoop` (activity-log rollup, cursor,
  self-failure page), enabled by default, supervised. WS-C: `fleet-git-health-guard.sh` state-transition dedup +
  `--self-test` (PASS). WS-D: `notify_slot_blocked` multi-line options/recommendation. Codex SSOT
  `/codex/04-architecture/agent-orchestrator-alerting.md` + CLAUDE.md one-liner added. **Remaining:** WS-E deploy — a
  auto-deploy via uvicorn `--reload` (no manual restart) + a 24–48 h re-pull verification (the only remaining step).
- **2026-07-13 (complete pager audit)** — Operator (frustrated with one-at-a-time): "check EVERY alert, do the audit
  properly." Enumerated all 40 `slack._post` notifiers + grouped the live 7-day channel (2065 msgs) by shape. Most of
  the volume was already fixed today (dispatched/recovered/spawn-failed/escalation-resolved now logged). Found 3
  self-healing events still paging → downgraded (`notify_agent_stuck_escalation` "Auto-respawn FAILED",
  `notify_stash_on_done`, `notify_autospawn_flap`). **agent-orchestrator@bb87f59** (QG green). Added the **Complete
  pager audit table** to the codex SSOT so this stops being whack-a-mole. Surfaced a separate PM-cron issue
  (Plan-hygiene sweep FAILED, daily, no dedup) as a deferred todo.
- **2026-07-13 (stop guessing — classify by API code)** — Operator flagged a "Spawn FAILED — likely a dead/expired
  setup-token, a rate-limit, or an auth modal" alert whose pane showed a LIVE working agent, and asked why we guess when
  the API codes are known. Probed all 4 accounts live: **4/4 tokens WORKING** (200; 5h 5-31%, 7d 12-64%; none
  rate-limited) — no dead token, which is why no auth alert had fired. Replaced the spawn-time pane-guess with a
  **definitive token probe** (401/403→dead-token page, 429→silent rate_limited, 200→summary-only).
  **agent-orchestrator@67de599** (QG green, 1225 pytest). The authoritative dead-token page is
  `notify_account_auth_failed` (poller 401/403 + spawn probe); rate-limit stays silent.
- **2026-07-13 (spawn failures → summary-only)** — Operator: "spawn failures should not send direct alert, it should
  only go into summary one." This reverses the audit's shape-#5 KEEP. Downgraded `notify_spawn_failed` → `logger.info`
  (activity log already carries `autospawn_failed` / `escalation_dispatch_failed` → digest; GCS ledger kept).
  **agent-orchestrator@770f12f** (QG green, 1221 pytest). Auth-shaped + unresolved-escalation pages preserved.
- **2026-07-13 (escalation-RESOLVED still paging)** — Operator flagged two `escalation RESOLVED` alerts
  (execution-service, system-integration-tests) still hitting the channel. It's an all-clear bookend WS-A had left
  paging (parked as KEEP in the low-volume tail). Downgraded `notify_escalation_resolved` → `logger.info` (activity log
  still feeds the digest); UNRESOLVED/re-escalation still pages CRITICAL. **agent-orchestrator@8843519** (QG green). The
  sibling `account auth RECOVERED` bookend stays a page **by design** — it has an explicit
  `test_account_auth_recovered_still_pages` lock (an account returning to rotation is operationally significant, not
  churn), so it was left untouched.
- **2026-07-13 (digest-per-restart bug)** — Operator: "4 different summary alerts already". Pulled the channel — **5**
  digests in one morning (07:15, 10:45, 11:27, 11:31, 11:46), windows non-overlapping so the cursor was fine; the loop
  was firing on **every server restart** (uvicorn `--reload` restarts per code change reaching the VM; AO code landed
  repeatedly today). Fixed `DailySummaryLoop` to anchor the wait to the persisted cursor (`_seconds_until_due`), so a
  mid-interval restart resumes the countdown instead of posting — **agent-orchestrator@d5c5cae** (QG green, 1219
  pytest). First-boot + server-down-past-interval still post.
- **2026-07-13 (first live digest + follow-up)** — WS-B went live: the first `AO daily activity digest` posted (1706
  events / 5 failures since 07:15 UTC), confirming `DailySummaryLoop` runs in prod. Operator flagged a readability gap —
  the "5 failure event(s)" line pointed "see the counts below" but the failures ranked below the shown top-25 and were
  truncated. Fixed `notify_daily_summary` to always keep failure rows visible (🔴-marked) —
  **agent-orchestrator@f79f028** (QG green, 1216 pytest). Also documented every digest field + `event_type` in the codex
  SSOT per operator ask (todo 10). The stray `fleet-git-health-guard.sh` prune-hazard fix in the tree was a concurrent
  agent's WIP (shipped independently as `agent-orchestrator@a96c07c`) — left untouched.
- **2026-07-14 (post-cleanup flap + repeat-page sweep)** — Operator reported the channel was STILL noisy with new (not
  the old) noise, pasted a live `git RED` / `git RECOVERED` pair, and asked for a proper fix rather than more
  whack-a-mole. Pulled a fresh 24h window (134 msgs, `SLACK_ALERTS_READER_BOT_TOKEN`) and found: (1) the same-day
  git-staleness restore (`1be792c`, an operator-directed fix outside this plan's own todos, landed in response to a
  2-day-unpaged root-PM dirty-repo incident) was flapping — 21x RED + 19x RECOVERED in 24h, several "recovered after 0m"
  repeating for hours, root-caused to a single-tick reporter blip (`slot-git-status-report.sh` transiently dropping a
  repo from one snapshot) clearing the 4h throttle; (2) `notify_plan_health_dispatch_failed`'s cooldown had a
  read-check-write race (paged twice 6 and 21 minutes apart on two occasions); (3) `notify_escalation_unresolved`
  repeated 7x for one repo in <3h because `_find_open_escalation` only dedupes non-terminal escalations, so a
  persistently-red wall spawns a fresh escalation (and a fresh page pair) every cycle. All three fixed in one commit — a
  debounced clean-confirm for the git flap, an in-process lock for the dispatch-failed race, and a per-stage cooldown
  for the escalation repeat (self-healing retry behavior left untouched, only the operator page deduped). Verified via
  `verify_dispatched_escalations`/`_git_alerts` regression tests reproducing each exact observed pattern before fixing.
  **agent-orchestrator@50557aa**, full `quality-gates.sh` green (1255 pytest, ruff/basedpyright/dashboard tsc+vitest
  clean), pushed to `live-defi-rollout` and confirmed on `origin`. Codex SSOT updated (todo 18). **Remaining:** the same
  24–48h post-deploy re-pull (WS-E, still open) should now also confirm this second round of fixes actually drops the
  volume — fold into that same verification pass rather than opening a new one.

## Deferred work after 2026-07-13

| Item                                           | Why deferred                                                                                                                                                                                                                                                                                                                   | Next action                                                                                                                                                                             |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| WS-E verify (deploy is automatic)              | Prod backend auto-deploys via the ao-self-pull 15-min root cron (FF-pull + systemctl restart on HEAD change, corrected 2026-07-13 — see the WS-E todo above; NOT uvicorn `--reload`), so it picks up the new code with NO manual restart once the cron reaches the VM; verification is inherently a 24–48 h observation window | After the code has been live ~24–48 h, re-pull with `alerts_audit/fetch_alerts.py` and drop the jsonl in `alerts_audit/` to confirm the volume drop (can be re-run any time on request) |
| Underlying git corruption on `ip-172-31-5-118` | Out of scope for this alerting plan (operator decision); a separate agent already added commit-graph self-heal (`agent-orchestrator@297b867`)                                                                                                                                                                                  | Confirm the fsck failure clears after that fix propagates; if not, a targeted `instruments-service` .git repair                                                                         |
