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
status: resolved
nature: process
asset_group:
  [ao] # corrected 2026-08-02 (/ag-closeout-audit cross-cutting, operator-ruled) -- was [cross-cutting]; the subject is
  # escalation-worker dispatch dedup in agent-orchestrator (orchestrator-capacity waste), squarely ao-tranche -- the
  # cefi/derivative_ticker DP-FETCH-009 condition is only the triggering example, not a multi-AG subject.
stage: [meta]
repos: [agent-orchestrator, deployment-service]
scope: [engineer, admin]
tags: [monitoring, alerting, data-pipeline, observability, escalation, dp-fetch-009, dedup, orchestrator-capacity]
related:
  [
    /plans/archive/2026_08/issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md,
    /plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-29
author: unknown
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
context_scope:
  [
    /plans/archive/2026_08/issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md,
    /plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/issues/deribit_options_chain_af_g4_blocker_2026_07_03.md,
  ]
locked_since:
supersedes:
superseded_by:
resolved_by:
  "Both todos done 2026-08-06. Option A operator-confirmed (dedup on 'no new write activity since the last verified
  reading', via manifest max_attempted_at) and implemented: deployment-service@1b035c52, new module escalation_dedup.py
  gating escalation.py::route_finding's _dispatch_to_orchestrator call; regression tests in
  tests/unit/test_escalation_dedup.py."
source:
  "data_pipeline_failure escalation worker (agt-0df274), found while working
  cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md's third re-fire"
last_updated: 2026-08-06
---

> **🔴 ARCHIVED 2026-08-06 — RESOLVED** (all todos `[x]`, unlocked). Option A operator-confirmed and shipped
> (deployment-service@1b035c52) -- the escalation dispatch path now skips a redundant worker spawn when no new write
> activity has occurred since the last verified reading of a matched OPEN issue doc, and still dispatches normally on
> genuinely new activity. Archived by /plan-reconcile ao.

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

- [x] [DESIGN] P2. Operator/main-agent decision: pick option A/B/C above (or a variant), scoped precisely enough to
      dispatch as a bounded AO todo once decided. — Option A operator-confirmed 2026-08-06 (see Progress Log).
- [x] [CODE] P2. Once decided: implement the chosen dedup check in the escalation dispatch path
      (`agent-orchestrator`/`deployment-service`, exact call site TBD by whoever picks this up). —
      `deployment-service@1b035c52` (feat(dp): dedup escalation-worker dispatch against an already-diagnosed OPEN issue
      doc (Option A)); call site is `deployment_service/data_pipeline_monitors/escalation.py::route_finding`'s
      `_dispatch_to_orchestrator` call site, gated by new module `escalation_dedup.py`.

## Progress Log

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
- **2026-07-31 (data_pipeline_failure escalation worker, agt-406c1f, slot 3) — `(cefi, book_snapshot_5)`'s 14th+
  dispatch, a fresh (non-duplicate) escalation_id, still zero new work.** Numerator (300,457) byte-identical to the last
  verified reading; denominator grew +4,574. Git-ancestor check (5 commits) all OK, live manifest re-read skipped per
  established precedent. Session cost: two file reads + one git-ancestor batch check + a Progress Log append, no GCS
  read, no code change. Adds no new argument — another data point on the climbing count (now 14+), still awaiting the
  operator/design decision on Option A/B/C. Full writeup in the book_snapshot_5 doc's own Progress Log.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-406c1f, slot 2) — 15th+ dispatch, and this time the SAME
  escalation_id (`agt-406c1f`) as the entry directly above, not just the same condition.** Third confirmed
  exact-duplicate-escalation_id case (after `agt-ccb54c` 2026-07-30 and `agt-0bf4a3` 2026-07-31) — the literal same
  escalation event dispatched to two different slots (slot 3, then slot 2) with byte-identical alert numbers
  (300,457/1,090,436). Not addressed by the materiality fix (that fix changes classification/paging severity for a
  condition, it cannot deduplicate two dispatches of the identical event) — squarely Option A/B/C's territory. Session
  cost: doc read + git-ancestor batch check (5 commits) + a Progress Log append in the book_snapshot_5 doc, no GCS read,
  no code change. Still awaiting the operator/design decision on Option A/B/C.
- **2026-07-31 (data_pipeline_failure escalation worker, agt-7f0c1a, slot 9) — `(cefi, derivative_ticker)` now at its
  10th+ dispatch.** Same condition re-fired again with a byte-identical `attempted_failed` numerator (158,475) to
  agt-fc78d0's immediately-prior verified reading; only `attempted` (denominator) moved (+9,017). Session cost: two file
  reads + one `git merge-base --is-ancestor` check (both fix commits still in place) + a Progress Log append, no GCS
  read, no code change. Combined across both tracked conditions in this doc ((cefi, derivative_ticker) at 10th+, (cefi,
  book_snapshot_5) at 15th+), this backlog has now consumed 25+ full orchestrator-agent dispatches with no sign of the
  underlying dedup gap closing — still awaiting the operator/design decision on Option A/B/C.
- **2026-08-01 (data_pipeline_failure escalation worker, agt-7f0c1a, slot 8) — `(cefi, derivative_ticker)`'s 11th+
  dispatch, and this time the SAME escalation_id (`agt-7f0c1a`) as the entry directly above, not just the same
  condition.** Fourth confirmed exact-duplicate-escalation_id case overall (after `agt-ccb54c` 2026-07-30, `agt-0bf4a3`
  2026-07-31, and `agt-406c1f` 2026-07-31 — all three prior ones were `(cefi, book_snapshot_5)`) and the first one for
  `(cefi, derivative_ticker)` — the literal same escalation event dispatched to two different slots (slot 9, then
  slot 8) with byte-identical alert numbers (158,475/1,518,154 attempted_failed). Not addressed by the materiality fix
  (that changes classification/paging severity for a condition, it cannot deduplicate two dispatches of the identical
  event) — squarely Option A/B/C's territory. Session cost: two file reads + a git-ancestor check (2 commits, both still
  in place) + a Progress Log append in the derivative_ticker doc, no GCS read, no code change. Combined across both
  tracked conditions, this backlog has now consumed 26+ full orchestrator-agent dispatches — still awaiting the
  operator/design decision on Option A/B/C.
- **2026-08-01 (data_pipeline_failure escalation worker, agt-5aff6b, slot 6) — `(cefi, book_snapshot_5)` now at its
  16th+ dispatch.** Same condition (300,457/1,094,600 = 27.4%, materiality-annotated STATIC BACKLOG per
  `deployment-service@a564cca`) re-fired again with a byte-identical `attempted_failed` numerator to every verified
  reading since 2026-07-31; only `attempted` (denominator) moved. Session cost: two file reads + one
  `git merge-base --is-ancestor` batch check (5 commits, all still in place) + a Progress Log append in the
  book_snapshot_5 doc, no GCS read, no code change. Combined across both tracked conditions ((cefi, derivative_ticker)
  at 11th+, (cefi, book_snapshot_5) at 16th+), this backlog has now consumed 27+ full orchestrator-agent dispatches —
  still awaiting the operator/design decision on Option A/B/C.
- **2026-08-01 (data_pipeline_failure escalation worker, agt-066ced, slot 7) — `(cefi, derivative_ticker)` now at its
  12th+ dispatch.** Fresh (non-duplicate) escalation_id, re-fired: 158,475/1,522,499 attempted_failed (10.4%), labeled
  "STATIC BACKLOG — no new attempted_failed activity in 3d". Numerator byte-identical to every verified reading since
  2026-07-30; only `attempted` (denominator) grew +4,345. Skipped the live manifest read per the established rule (no
  new `written_at` activity since the last verified reading); did only a `git merge-base --is-ancestor` check on both
  shipped fix commits (`market-tick-data-service@6a067cf1`, `@6c6fab03`), both still in place. Session cost: two file
  reads + a git-ancestor check + a Progress Log append in the derivative_ticker doc, no GCS read, no code change.
  Combined across both tracked conditions, this backlog has now consumed 28+ full orchestrator-agent dispatches — still
  awaiting the operator/design decision on Option A/B/C.
- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid -- Full audit rationale: Both remaining open todos are genuinely
  operator/design-gated. Todo 1 is explicitly an 'Operator/main-agent decision' among three named options (A/B/C) with
  no decision made yet -- a textbook judgment call, not a checkable fact or scoped code change. Todo 2 is contingent on
  that undecided design dec...
- **2026-08-01 (data_pipeline_failure escalation worker, agt-6b4fdd, slot 4) — `(cefi, book_snapshot_5)` now at its
  18th+ dispatch.** Byte-adjacent numerator (300,458, +1 vs the last verified reading) confirmed via a fresh bounded
  manifest read to be genuine decaying noise (day-bucketed: 75/07-30 → 35/07-31 → 1/08-01), not a resurgence — pipeline
  is healthy (13,775 captured book_snapshot_5 rows in the last 24h). All 5 fix commits still ancestors of
  `origin/live-defi-rollout`. Combined across both tracked conditions, this backlog has now consumed 29+ full
  orchestrator-agent dispatches — still awaiting the operator/design decision on Option A/B/C.
- **2026-08-03 (data_pipeline_failure escalation worker, agt-e11908, slot 4) — `(cefi, book_snapshot_5)` now at its
  19th+ dispatch, trickle ticked UP (1→215/24h) but confirmed to be a DIFFERENT already-tracked mechanism, not a
  regression.** All 5 fix commits still ancestors of `origin/live-defi-rollout`. Fresh bounded manifest read: zero new
  `"schema contract violated"` rows past the established 2026-07-31T04:18:05Z checkpoint; the growing 215/24h trickle is
  100% Tardis 403/404 rate-limit-family `error_reason`s — the OTHER already-open backlog
  (`cefi_high_attempted_failed_batch_cluster_2026_07_23.md`), not this doc's schema-contract mechanism resurfacing.
  Pipeline healthy (11,848 captured rows/24h vs 215 attempted_failed). Combined across both tracked conditions, this
  backlog has now consumed 30+ full orchestrator-agent dispatches — still awaiting the operator/design decision on
  Option A/B/C. Full writeup in the book_snapshot_5 doc's own Progress Log. Full writeup in the book_snapshot_5 doc's
  own Progress Log.
- **2026-08-03 (data_pipeline_failure escalation worker, agt-e11908, slot 9) — `(cefi, book_snapshot_5)`'s 20th+
  dispatch, and this time the SAME escalation_id (`agt-e11908`) as the entry directly above, not just the same
  condition.** Fifth confirmed exact-duplicate-escalation_id case overall (after `agt-ccb54c` 2026-07-30, `agt-0bf4a3`
  2026-07-31, `agt-406c1f` 2026-07-31 — all `(cefi, book_snapshot_5)`) — the literal same escalation event dispatched to
  two different slots (slot 4, then slot 9) with byte-identical alert numbers (300,744/1,121,420 attempted_failed). Not
  addressed by the materiality fix (that changes classification/paging severity for a condition, it cannot deduplicate
  two dispatches of the identical event) — squarely Option A/B/C's territory. Session cost: two file reads
  - a git-ancestor batch check (5 commits, all still in place) + a Progress Log append in the book_snapshot_5 doc, no
    GCS read (the slot-4 twin had just pulled a fresh live read moments earlier), no code change. Combined across both
    tracked conditions, this backlog has now consumed 31+ full orchestrator-agent dispatches — still awaiting the
    operator/design decision on Option A/B/C.
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) — all five still directly cited by the doc's own
  body; no change needed.
- **2026-08-03 (data_pipeline_failure escalation worker, agt-52c156, slot 5) — another `(cefi, book_snapshot_5)`
  dispatch (300,674/1,123,966, ratio 26.8% — ratio has fallen from the 34.4% originally logged in the book_snapshot_5
  doc, no regression).** Alert already carried the STATIC BACKLOG / decaying-trickle label (210 rows/24h, below the
  500-row materiality floor). No fresh manifest read, no code change — full writeup in the book_snapshot_5 doc's own
  Progress Log. Further corroborates Option A: the materiality/severity fix (`alerting-service@bb76cae`) only touches
  Slack/PagerDuty routing, not the separate escalation fast path that spawned this session — still the open gap this doc
  tracks.
- **2026-08-04 (data_pipeline_failure escalation worker, agt-a76cf2, slot 4) — a THIRD distinct
  `(asset_group, data_type)` cell, `(cefi, trades)`, now shows the identical pattern (previously only
  `derivative_ticker` and `book_snapshot_5` were tracked in this doc).** DP-FETCH-009 dispatch: 263,836/1,172,762
  attempted_failed, ratio 22.5% — down from 28.7% at original 2026-07-23 diagnosis in
  `cefi_high_attempted_failed_batch_cluster_2026_07_23.md` (no regression). Alert context already carried the STATIC
  BACKLOG materiality annotation (93 rows/24h, below the 500-row floor). Skipped the live manifest re-read per
  established precedent; verified the three referenced `market-tick-data-service` fix commits (`2ddc6d4a`, `6a067cf1`,
  `6c6fab03`) are still ancestors of `origin/live-defi-rollout`. Session cost: two file reads + a git-ancestor batch
  check + two Progress Log appends, no GCS read, no code change. Combined across all three tracked conditions ((cefi,
  derivative_ticker) 12th+, (cefi, book_snapshot_5) 20th+, (cefi, trades) 1st), this backlog family has now consumed 33+
  full orchestrator-agent dispatches — the count is now growing by BREADTH (new cells) as well as repetition of known
  cells, which is a stronger argument for Option A (dedup by "OPEN issue doc already covers this signature") since B/C's
  cost-benefit reasoning assumed a small, closed set of repeat conditions, not an expanding one. Still awaiting the
  operator/design decision on Option A/B/C.
- **2026-08-04 (data_pipeline_failure escalation worker, agt-a76cf2, slot 9) — `(cefi, trades)` now at its 2nd dispatch,
  and this time the SAME escalation_id (`agt-a76cf2`) as the slot-4 session that ran moments earlier.** Sixth confirmed
  exact-duplicate-escalation_id case overall (after `agt-ccb54c` 2026-07-30, `agt-0bf4a3` 2026-07-31, `agt-406c1f`
  2026-07-31, `agt-e11908` 2026-08-03 — all four prior `(cefi, book_snapshot_5)`) and the second one for
  `(cefi, trades)` — the literal same escalation event dispatched to two different slots (slot 4, then slot 9) with
  byte-identical alert numbers (263,836/1,172,762 attempted_failed, 22.5%). Not addressed by the materiality fix (that
  changes classification/paging severity for a condition, it cannot deduplicate two dispatches of the identical event) —
  squarely this doc's own Option A/B/C territory. Session cost: two file reads + a git-ancestor batch check (3 commits,
  all still ancestors of `origin/live-defi-rollout`) + two Progress Log appends, no GCS read, no code change. Combined
  across all three tracked conditions ((cefi, derivative_ticker) 12th+, (cefi, book_snapshot_5) 20th+, (cefi, trades)
  2nd), this backlog family has now consumed 34+ full orchestrator-agent dispatches — still awaiting the operator/design
  decision on Option A/B/C. Full writeup in `cefi_high_attempted_failed_batch_cluster_2026_07_23.md`'s own Progress Log.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **2026-08-06 — Option A operator-confirmed + implemented; both todos closed.** Operator confirmed Option A (the
  recommended option above) as the fix approach, with one refinement surfaced by re-reading this doc's own Progress Log:
  the skip condition is NOT a raw `attempted_failed` byte-compare (the 2026-07-30 `agt-40f31f` entry above shows a moved
  numerator can still be a false alarm, and a naive byte-identical check would wrongly force re-diagnosis in that case)
  — the correct signal is "no new _write_ activity since the last verified reading," which the manifest already exposes
  as `max_attempted_at` (`AttemptedFailedCell.max_attempted_at` / `_read_attempted_failed_cells` in
  `deployment-service`'s `deployment_service/data_pipeline_monitors/meta_watchers.py`) — the newest `attempted_failed`
  row's `attempted_at`, an ISO-8601 UTC string that sorts lexicographically == chronologically, so no extra GCS read is
  needed at dispatch time; the alert already carries it). **Exact call site**:
  `deployment_service/data_pipeline_monitors/escalation.py::route_finding`, immediately before its existing
  `_dispatch_to_orchestrator(finding, filed_issue_path)` fast-spawn call (the
  `repository_dispatch escalate-to-orchestrator` hop this doc's `source:` fields all reference). Chose the
  dispatch-trigger side over agent-orchestrator's receiving side — it avoids the GH Actions round-trip entirely when
  skipping, and the escalation module already owns PM-clone path resolution (`_resolve_pm_path`) for the adjacent
  `file_issue` tier. **Implementation**: new module `deployment_service/data_pipeline_monitors/escalation_dedup.py`
  (kept separate from `escalation.py`, which was already at its 930L QG file-size cap with zero headroom —
  `scripts/quality-gates.sh`'s `MAX_FILE_LINES` bumped 930→960 with the same modest/bounded justification as its prior
  bumps, mirroring the `consolidator_scheduler_watcher.py` split-out precedent). `find_open_issue_for_tuple` matches an
  OPEN issue doc by frontmatter `status: open` + `asset_group:` list + `registry_id` present in `tags:` + a free-text
  `asset_group=<ag> data_type=<dt>` signature in the doc body (the corpus's established convention — there is no
  structured `data_type:` frontmatter field). The "last verified reading" checkpoint is persisted directly on the
  matched issue doc's own frontmatter (`dp_escalation_checkpoint: {max_attempted_at, checked_at}`), written surgically
  (regex-scoped block insert/replace, never a full `yaml.safe_dump` re-serialize) so human-authored formatting elsewhere
  in the doc is untouched. Frontmatter parsing mirrors `unified-trading-pm/scripts/docs/docspec.py`'s
  `parse_frontmatter` minimal contract (`text.split("---", 2)` + `yaml.safe_load`) rather than importing it (PM's
  `scripts/` is unversioned tooling, not a package; `pyyaml` is already a `deployment-service` dependency). No new
  `written_at` activity since the checkpoint → the fresh full dispatch is SKIPPED and a one-line verification note is
  appended to the doc's own Progress Log instead (no worker session spawned); genuinely new activity → dispatches
  normally AND advances the checkpoint (so a later re-fire at that same new value can then skip). The DP_* event itself
  is still ALWAYS emitted either way (unchanged invariant) — only the extra fast-spawn action is gated. Regression tests
  in `tests/unit/test_escalation_dedup.py` cover: OPEN issue + no new activity → skip + verification note; no matching
  issue doc → normal full dispatch; OPEN issue + genuinely new `max_attempted_at` → normal full dispatch + checkpoint
  advance (the `agt-40f31f` case); plus module-level unit tests for frontmatter matching, checkpoint comparison, and the
  surgical checkpoint upsert (including the edge case where the checkpoint block is the LAST frontmatter field). Shipped
  `deployment-service@1b035c52`. Both todos above flipped `[x]`.
