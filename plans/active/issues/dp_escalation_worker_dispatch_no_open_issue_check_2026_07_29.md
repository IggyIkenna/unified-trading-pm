---
doc_type: issue
title:
  Escalation dispatch spawns a fresh `data_pipeline_failure` worker per re-page even when an OPEN, already-diagnosed
  issue doc already covers the exact (asset_group, data_type, event) condition -- no dedup at the escalation-worker
  layer (distinct from the already-fixed Slack re-page cadence)
summary: >-
  Three `data_pipeline_failure` escalation workers (agt-7a4d1d, agt-27e235, agt-0df274) were dispatched across
  2026-07-28/29 for the SAME byte-identical `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009) condition -- asset_group=cefi,
  data_type=derivative_ticker, `attempted_failed` numerator frozen at 158,085 across all three readings (only
  `captured`/ratio moved as the backlog partially recovers). The first two sessions did all the real work (root-caused +
  fixed 3 distinct code bugs, `market-tick-data-service@6a067cf1`/`@6c6fab03`) and left 3 deliberately-deferred P3
  todos; the third session (this one) found nothing new to fix and spent a full escalation-worker session re-confirming
  that. `dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md` (archived, all 3 todos done) already fixed the adjacent
  problem -- Slack re-paging the SAME condition every detector tick -- via a cadence-aware cooldown map
  (`_RECURRING_ALERT_COOLDOWNS`, 1800s for `DP_RUN_MOSTLY_EMPTY`) and a persisted re-nag interval in
  `check_high_attempted_failed`. Neither fix touches the SEPARATE escalation fast path (`repository_dispatch
  escalate-to-orchestrator`, `wall_type=data_pipeline_failure`) that spawns a full `data_pipeline_failure`
  orchestrator-agent session on every CRITICAL page that reaches it -- that path has no check for "is there already an
  OPEN issue doc filed for this exact (asset_group, data_type, event) tuple, and if so, is a fresh worker actually
  needed vs. just appending to its Progress Log / verifying nothing regressed." This is real orchestrator-capacity waste
  (a full agent session per re-page of a KNOWN condition) and is NOT covered by the archived 2026-07-15 fix (that fix is
  about Slack noise, this is about escalation-worker dispatch).
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, deployment-service]
scope: [engineer, admin]
tags: [monitoring, alerting, data-pipeline, observability, escalation, dp-fetch-009, dedup, orchestrator-capacity]
related:
  [
    /plans/active/issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md,
    /plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-29
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  "data_pipeline_failure escalation worker (agt-0df274), found while working
  cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md's third re-fire"
last_updated: 2026-07-31
---

# Escalation-worker dispatch has no "already an open issue doc" dedup check

## What I found

The `DP_RUN_MOSTLY_EMPTY` (DP-FETCH-009, `check_high_attempted_failed`) alert fired three times in ~24h for the
identical `(asset_group=cefi, data_type=derivative_ticker)` cell, each time spawning a fresh `data_pipeline_failure`
orchestrator-agent session (`agt-7a4d1d` 2026-07-28, `agt-27e235` 2026-07-28, `agt-0df274` 2026-07-29). Evidence the
condition did NOT change between firings: the `attempted_failed` numerator was byte-identical (158,085) across all three
readings -- only the denominator (`captured`) grew, dropping the ratio 11.2%→10.9%, i.e. this is the SAME static backlog
the first session already split and mostly fixed, not a new failure batch.

This is a DIFFERENT layer from the already-fixed problem in `dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md`
(archived, all 3 todos `[x]`): that fix added a cadence-aware Slack cooldown (`_RECURRING_ALERT_COOLDOWNS`, 1800s) and a
persisted re-nag interval to the detector itself, so `#data-pipeline-alerts` isn't spammed every 15-min tick. But the
escalation fast path (`repository_dispatch escalate-to-orchestrator`, `wall_type=data_pipeline_failure`, per
`/codex/05-infrastructure/data-pipeline-alerts.md` § "self-heal actuator layer") apparently still fires a full
worker-spawn on each CRITICAL page that reaches PagerDuty/Telegram, with no check for "is there already an OPEN issue
doc filed for this exact tuple, and would a fresh full diagnosis actually find anything new."

**Not investigated in this session** (out of scope for a one-shot `data_pipeline_failure` escalation worker, and this
repo is `market-tick-data-service` — this issue's fix lives in `agent-orchestrator`/`deployment-service`):

- The exact call site in `agent-orchestrator` that receives the `repository_dispatch` and decides to spawn a
  `data_pipeline_failure` worker — whether it already has ANY notion of "this escalation_id maps to an existing issue
  doc" (the `source:` frontmatter field in the issue docs I read suggests escalation_id is recorded, but not clear
  whether it's used to SKIP a redundant spawn).
- Whether spawning a fresh worker every time is actually intentional design (e.g. "always re-verify the condition hasn't
  gotten WORSE, cheaply") vs. an oversight — this is a genuine design question, not a mechanical bug fix.

## Recommended decision

This needs an operator/design call on the right dedup semantics before implementation (marked `assigned_vm: NA` — not
AO-dispatch-eligible as a bare "fix it" todo per the workspace's dispatch-scope-eligibility rule). Options:

A: **Before spawning, check for an OPEN issue doc matching `(asset_group, data_type, event)` in its
`source:`/tags/title.** If found AND the alert's own numerator/ratio hasn't moved since that doc's `last_updated`, skip
the full worker spawn — instead append a one-line "re-fired, still static, no new action" note directly (a cheap
deterministic check, not a full diagnosis) and re-arm the Slack cooldown. [RECOMMENDED — closes the actual waste without
losing detection of genuine regressions, since a numerator MOVING still triggers a full worker] B: **Leave dispatch
as-is; only reduce PagerDuty/Telegram page frequency further** (extend the 1800s cooldown) so fewer re-pages reach the
escalation fast path at all — cheaper to implement but weakens "genuinely got worse" detection latency. C: **Do nothing
— the current 3-worker cost for this condition was small in absolute terms and the alternative (missing a real
regression) is worse.**

## Todos

- [ ] [DESIGN] P2. Operator/main-agent decision: pick option A/B/C above (or a variant), scoped precisely enough to
      dispatch as a bounded AO todo once decided.
- [ ] [CODE] P2. Once decided: implement the chosen dedup check in the escalation dispatch path
      (`agent-orchestrator`/`deployment-service`, exact call site TBD by whoever picks this up).

## Progress Log

- **na-eligibility-audit 2026-07-31** (tranche=cross-cutting, dispatch agt-845699): KEEP-NA, valid — both open todos
  gated on an operator/design decision on dedup semantics. Confirms the prior 2026-07-30 na-eligibility-audit KEEP-NA
  verdict on the same self-documented basis; 10+ subsequent Progress Log entries corroborate without resolving it.
- **2026-07-29 (data_pipeline_failure escalation worker, agt-0df274):** Filed this issue after finding a third
  escalation-worker spawn for the same static DP-FETCH-009 condition already fully diagnosed by two prior sessions. Did
  not implement a fix (design decision + wrong-repo for this one-shot's target repo). Cross-referenced from
  `cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md`'s Progress Log.
- **2026-07-29 (data_pipeline_failure escalation worker, agt-79063c) — stronger evidence for Option A.** A separate
  DP-FETCH-009 re-page for `(cefi, futures_chain)` dispatched a worker with no pre-linked issue doc, which (without
  checking `plans/active/issues/` first) re-derived a stale premise and shipped a code change + a prod manifest write
  that an existing, already-open issue doc (`deribit_options_chain_af_g4_blocker_2026_07_03.md`, 2026-07-18 correction
  banner) had explicitly ruled out. Caught and reverted in the same session (full account in that doc's 2026-07-29
  Progress Log entry) — no lasting damage, but this is a materially worse failure mode than redundant re-diagnosis: a
  missing dedup check let a worker actively UNDO a standing correction. Reinforces Option A (check for an OPEN issue doc
  on the exact tuple before spawning / before taking any write action) over B or C.
- **2026-07-30 (data_pipeline_failure escalation worker, agt-606bbf) — 4th dispatch for one condition in ~24h.**
  `cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md` has now had FOUR separate
  `data_pipeline_failure` worker dispatches for the identical `(asset_group=cefi, data_type=book_snapshot_5)` static
  backlog: 2 did the original diagnosis+fix (2026-07-28), 2 more (2026-07-30, escalation_ids `agt-ccb54c` twice then
  `agt-606bbf`) each spent a full session re-confirming the numerator is still frozen and the fix commits are still
  ancestors of `origin/live-defi-rollout` — genuinely cheap per-session (git ancestor check + a Progress Log append, no
  manifest read needed since the numbers were already labeled STATIC BACKLOG) but still a full worker-session dispatch
  each time. Further corroborates Option A over B/C — a numerator-unchanged condition with an OPEN issue doc already
  covering it should not need a fresh orchestrator-agent spawn at all, even a cheap one.
- **2026-07-30 (data_pipeline_failure escalation worker, agt-40f31f) — 5th+ dispatch, `(cefi, derivative_ticker)`.**
  `cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md` re-fired again (its 5th dispatch overall — 2
  diagnosis+fix sessions, 2 prior static-confirm sessions, now this one). This time the raw numerator had genuinely
  MOVED since the last reading (158,085 → 158,475, +390) rather than being byte-identical, so a full live bounded
  manifest read was actually warranted (not just a git-ancestor check) to rule out a real regression — it confirmed the
  delta was fully attributable to writes already made on 2026-07-29 (before/concurrent with the prior session's same-day
  reading), zero rows written in the last 24h, no new failure class. Still net-zero new work, but this instance shows a
  numerator-moved condition can still be a false alarm — Option A's "skip only if numerator/ratio unchanged since
  last_updated" criterion (as literally worded) would have WRONGLY forced a full re-diagnosis here, since the numerator
  DID move. Worth folding into whichever option gets picked: the correct skip condition is "no new `written_at` activity
  since the doc's last verified reading," not "numerator byte-identical" — the former is robust to reads landing on
  different sides of a write batch, the latter isn't.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the doc self-documents its own AO-ineligibility: 'This needs an
  operator/design call on the right dedup semantics before implementation (marked assigned_vm: NA — not
  AO-dispatch-eligible as a bare fix-it todo per the dispatch-scope-eligibility rule)'.
- **2026-07-30 (data_pipeline_failure escalation worker, agt-14f171) — 6th+ dispatch, `(cefi, derivative_ticker)`.**
  `cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md` re-fired yet again. This time the numerator
  (158,475) WAS byte-identical to the immediately-prior verified reading (agt-40f31f, same day), so — per that prior
  session's own "no new `written_at` activity" finding — skipped the live manifest read entirely and did only a
  git-ancestor check on the two shipped fix commits (both still ancestors of `live-defi-rollout`). Session cost: two
  file reads + one `git merge-base` check + a Progress Log append, no GCS read. Further corroborates Option A: this
  condition has now consumed 6 full orchestrator-agent dispatches for a backlog that has not moved in any
  root-cause-relevant way since 2026-07-28.
- **2026-07-30 (data_pipeline_failure escalation worker, agt-d36d2a, slot 2) — a second condition,
  `(cefi, liquidations)`, shows the identical pattern.**
  `cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md` (filed earlier the same day by `agt-029155`)
  re-fired with `attempted_failed` byte-identical (44,422) and `attempted` up only 2 (749,121→749,123) — the boot
  context's own `attempted_failed_staleness` annotation already labeled it "no new attempted_failed activity in 1d".
  Skipped the live manifest re-read and did only a git-ancestor check on the two referenced fixes
  (`market-tick-data-service@6a067cf1` + `tardis-concurrency-guard.sh`'s `TARDIS_MAX_CONCURRENT_VMS=1`), both still in
  place; appended a Progress Log entry to that doc instead of a fresh diagnosis. Confirms this is not isolated to one
  cell — at least two independent `(asset_group, data_type)` DP-FETCH-009 conditions are now each consuming repeat
  full-worker dispatches for backlogs that already have an OPEN issue doc and zero new root-cause-relevant activity,
  reinforcing that Option A's dedup check belongs at the dispatch layer (would save this exact session's spawn) rather
  than being re-derived per-condition by convention alone.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-794496, slot 5) — `(cefi, derivative_ticker)` now at its
  7th+ dispatch.** `cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md` re-fired yet again with a
  byte-identical `attempted_failed` numerator (158,475) to the immediately-prior verified reading; only the `attempted`
  denominator moved. Session cost: two file reads + one `git merge-base --is-ancestor` check (both fix commits still in
  place) + a Progress Log append, no GCS read, no code change. Further corroborates Option A — this single condition has
  now consumed 7+ full orchestrator-agent dispatches since 2026-07-28 for a backlog whose root-cause-relevant state has
  not changed since the second dispatch fixed it.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-bd4088, slot 2) — `(cefi, derivative_ticker)` now at its
  8th+ dispatch.** Same condition re-fired again with a byte-identical `attempted_failed` numerator (158,475) to
  agt-794496's immediately-prior verified reading; only `attempted` (denominator) moved. Session cost: two file reads +
  one `git merge-base --is-ancestor` check (both fix commits still in place) + two Progress Log appends, no GCS read, no
  code change. This single condition has now consumed 8+ full orchestrator-agent dispatches since 2026-07-28 for a
  backlog whose root-cause-relevant state has not changed since the second dispatch fixed it — the per-dispatch cost is
  small but the count keeps climbing with no sign of the underlying dedup gap closing; still awaiting the
  operator/design decision on Option A/B/C.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-79b187, slot 13) — `(cefi, book_snapshot_5)` at its 9th+
  dispatch; shipped a complementary, DIFFERENT-layer mitigation (not this doc's Option A/B/C, which stays open).**
  `cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md` re-fired again — its own root-cause fix
  (`unified-api-contracts@1c4d8864`, nullable-levels) confirmed still holding (a short post-fix tail was the same
  self-resolving in-flight-stale-code pattern already documented there 4 times, not a regression). Rather than adding a
  9th "nothing new, git-ancestor-check only" entry, traced WHY this specific condition keeps re-triggering a CRITICAL
  page + escalation-worker spawn despite being 97%+ resolved: the already-shipped STATIC BACKLOG severity-downgrade
  (`alerting-service@bb76cae`, `cefi_high_attempted_failed_batch_cluster_2026_07_23.md`) only fires when a cell's newest
  row is `>=1` day old — a cell with a small but NONZERO decaying trickle (this one: 91 rows/24h against a 300k-row
  total) never qualifies, so it reads "Fresh" and keeps CRITICAL-paging forever even after full root-cause resolution.
  Shipped `deployment-service@a564cca`: a cell's own last-24h volume must now cross `ATTEMPTED_FAILED_ABS_THRESHOLD`
  (the same bar the alert itself uses) to count as genuinely Fresh; below that it reads STATIC BACKLOG even at
  `stale_days == 0`. Since `router.py` applies the severity downgrade BEFORE the PagerDuty/Telegram paging-channel
  check, this should also stop the `wall_type=data_pipeline_failure` escalation fast path from re-firing for THIS
  specific decaying-trickle shape going forward (and for any other DP-FETCH-009 cell in the same shape, e.g.
  `cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md` if it has a similar tail). **This does NOT
  resolve this doc's own open Option A/B/C** (worker-spawn dedup at the orchestrator-dispatch layer for a condition
  whose numerator is merely unchanged rather than one whose recent volume has fallen below a materiality floor — e.g.
  `(cefi, derivative_ticker)`'s repeated dispatches above still need that separate, still-undecided fix). Full writeup
  in the book_snapshot_5 doc's own Progress Log.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-164899, slot 12) — `(cefi, book_snapshot_5)`'s 10th+
  dispatch, confirming the materiality fix (`deployment-service@a564cca`) is working but the escalation-worker spawn
  itself still fires anyway.** The dispatch context for this session already carried the STATIC BACKLOG materiality
  annotation (95 rows/24h, below the 500-row floor) — i.e. the alert severity/classification fix from the entry above IS
  correctly suppressing the false-Fresh label now. But a full `data_pipeline_failure` orchestrator-agent session still
  spawned anyway (this one) to handle it — the materiality fix downgrades CRITICAL to WARN routing/paging, it does not
  stop the `repository_dispatch escalate-to-orchestrator` fast path from firing, which is this doc's own still-open
  Option A/B/C. Session cost: two file reads + a git-ancestor check (4 commits) + one bounded column-projected manifest
  read + a Progress Log append, no code change. Further corroborates that Option A (dedup at the escalation-dispatch
  layer itself) is the fix that actually closes this doc's waste — the 9th dispatch's alerting-materiality fix is a
  genuinely useful, complementary layer (correct classification) but does not substitute for it.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-05ca7f, slot 11) — `(cefi, book_snapshot_5)`'s 11th+
  dispatch, same story again.** Dispatch context again carried the STATIC BACKLOG materiality annotation (110 rows/24h)
  and a full worker session still spawned to handle it. Session cost: two file reads + a git-ancestor check (5 commits)
  - one bounded column-projected manifest read + two Progress Log appends, no code change — this single condition has
    now consumed 11+ full orchestrator-agent dispatches since 2026-07-28, at least 5 of which (7th onward) found nothing
    to fix beyond re-confirming an already-materiality-suppressed decaying trickle. Full writeup in the book_snapshot_5
    doc's own Progress Log. Still awaiting the operator/design decision on Option A/B/C — this entry adds no new
    argument, just another data point on the climbing count.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-0bf4a3, slot 8) — `(cefi, book_snapshot_5)`'s 12th+
  dispatch, same story again.** Dispatch context again carried the STATIC BACKLOG materiality annotation (110 rows/24h)
  and a full worker session still spawned. Numerator (300,457) byte-identical to the last verified reading, so the live
  manifest re-read was skipped per established precedent; session cost was two file reads + a git-ancestor batch check
  (5 commits) + a Progress Log append, no GCS read, no code change. Adds no new argument — another data point on the
  climbing count, still awaiting the operator/design decision on Option A/B/C.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-0bf4a3, slot 4) — 13th+ dispatch, and this time the SAME
  escalation_id (`agt-0bf4a3`) as the entry directly above, not just the same condition.** This is a sharper data point
  than the prior 12: it is not merely the same static condition re-detected on a later sweep, it is the literal same
  escalation event dispatched to two different slots (slot 8, then slot 4) with byte-identical alert numbers
  (300,457/1,085,862). Only the second confirmed exact-duplicate-escalation_id case observed so far (the first was
  `agt-ccb54c` on 2026-07-30, also for this exact `(cefi, book_snapshot_5)` cell). This shape is NOT addressed by the
  materiality fix at all (that fix changes classification/paging severity for a condition, it cannot deduplicate two
  dispatches of the identical event) — it is squarely Option A/B/C's territory (dedup at the escalation-dispatch layer
  itself, e.g. by escalation_id or by "does an OPEN issue doc already exist for this alert signature"). Session cost:
  doc read + git-ancestor batch check (5 commits) + a Progress Log append in the book_snapshot_5 doc, no GCS read, no
  code change. Still awaiting the operator/design decision on Option A/B/C.
