---
doc_type: issue
title: >-
  DP-LIVE-004 — sports live odds shard (venue=MATCHBOOK, data_type=odds) never
  captures: shared odds-api-key quota exhausted (15M/15M, 401s since 2026-08-18
  07:07) + live VM on pre-fix code misrecords 401s as SOURCE_RETURNED_ZERO
summary: >-
  `dp-fleet-monitor` DP-LIVE-004 (2026-08-20) flagged live shard
  vm=mtds-live-sports-odds-api-odds-20260816-145019 venue=MATCHBOOK data_type=odds
  as still-attempting (last attempt 0.0h ago) but never captured (staleness budget 3d).
  Root cause is a recurrence of the shared-key quota-exhaustion class (archived
  odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02): the single
  odds-api-key (15M requests = 5M recurring + 10M top-up) is fully drained
  (x-requests-used=15000000, x-requests-remaining=0) — live polling AND the standing
  batch backfill mtds-backfill-odds-20260817-062648 draw on the SAME key. Every fetch
  returns HTTP 401 → 0 odds rows → 0 captures since 08-18 07:07. Compounding: the VM
  runs boot-time (08-16) code WITHOUT the already-shipped upstream_failure_reason fix
  (market-tick-data-service@40b9b624, on origin/live-defi-rollout), so all 39,515
  per-VM shard rows are FALSE empty_confirmed[SOURCE_RETURNED_ZERO] — a §401-rule /
  honest-absence violation (a dead credential masked as honest absence). Additionally
  the batch backfill does not stop on an exhausted quota (historical-endpoint 401 body
  is 'Unauthorized', not OUT_OF_USAGE_CREDITS, and x-requests-remaining is absent → the
  credits_exhausted trip never fires) — it re-drains any topped-up key within hours.
status: open
nature: issue
asset_group: [sports]
stage: [live, data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    data-pipeline,
    dp-live-004,
    live-capture,
    odds-api,
    quota-exhaustion,
    shared-key,
    sports,
    honest-absence,
    misclassification,
  ]
related:
  [
    /plans/archive/issues/odds_api_key_quota_exhausted_4_days_after_provisioning_2026_08_02.md,
    /plans/archive/issues/sports_odds_vm_consolidator_stale_stall_2026_08_18.md,
    /plans/active/sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/live_sports_odds_upstream_failure_masked_as_honest_absence_2026_08_20.md,
  ]
created: 2026-08-20
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /codex/02-data/honest-absence-downstream-handling.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    market-tick-data-service/market_tick_data_service/live/connectors/odds_api_ws.py,
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py,
  ]
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P1
milestone: M3
source: [DP-LIVE-004]
resolved_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

# DP-LIVE-004 — sports live odds shard never captures

## What I found

Escalation `agt-f712d7` (data_pipeline_failure, DP-LIVE-004): live shard
`vm=mtds-live-sports-odds-api-odds-20260816-145019` `venue=MATCHBOOK` `data_type=odds`
is still attempting (last attempt 0.0h ago) but unproductive — **never captured**
(staleness budget 3d). No issue doc was pre-filed (alert carried the bare payload).

Live-state investigation (SSH on the running VM + Secret Manager + the-odds-api.com):

1. **VM still running, producer still attempting.** The VM runs
   `market_tick_data_service --operation websocket-streaming --mode live --asset-group
   SPORTS --shard-spec sports:ODDS_API:odds --instrument-ids ODDS_API:SPORT:soccer_*`
   (30 soccer leagues, `odds-api-key` from Secret Manager). The run.log (uploaded to
   `gs://deployment-scripts-…/vm-logs/mtds-live-sports-odds-api-odds-20260816-145019/run.log`)
   shows continuous `OddsApi: HTTP 401 for sport <league>` for ALL leagues — **81,713
   lines** since 2026-08-18 07:07:18 UTC, ~1 poll cycle of all 30 leagues every ~60s.

2. **The 401 is the shared key's quota, fully drained.** Immediately before the first
   401: `OddsApi live poll: shared odds-api-key credits critically low (8 remaining) --
   this key is also drawn on by batch backfills; live cannot self-throttle (must keep
   running), so operator action (top-up or pause backfills) is needed.` A live probe of
   the current secret value shows **`x-requests-used: 15000000`, `x-requests-remaining:
   0`** — every request shape (single-region minimal included) returns HTTP 401
   `Unauthorized`. The 15M budget (5M recurring + 10M top-up, per the 08-02 incident)
   is exhausted. (My first two minimal probes returned 200 — they consumed the final 2
   credits of the 14,999,998/15M the 08-20 fix commit already recorded; the key is now
   fully at 15M/15M.)

3. **Every per-VM shard row is a FALSE `empty_confirmed[SOURCE_RETURNED_ZERO]`.** The
   shard `_index/per_vm/mtds-live-sports-odds-api-odds-20260816-145019.parquet` in
   `market-data-tick-sports-prd-central-element-323112` holds 39,515 rows — **100%
   `capture_status=empty_confirmed`, 100% `error_reason=SOURCE_RETURNED_ZERO`**, zero
   captured, zero attempted_failed (MATCHBOOK group: 660 rows, all the same). A 401
   (credential/quota) is being stamped as proven honest absence — the exact
   `DP-FETCH-001`/`§401-rule` violation: "HTTP 401 MUST NOT be recorded as
   empty_confirmed … record as attempted_failed[CLASSIFIED_VENUE_ERROR]."

4. **The VM runs pre-fix code.** The misclassification fix — `odds_api_ws.py`
   `upstream_failure_reason()` (`market-tick-data-service@40b9b624`, plus credit-budget
   visibility `@3adab2d4`) — is committed on `origin/live-defi-rollout` and the runner
   (`websocket_runner.py:_record_empty_window` line 766) already routes a non-None
   failure reason to `record_failed`. The VM was launched 08-16 14:50Z and has not been
   restarted, so it runs the old code that lacks the hook → still fabricating
   SOURCE_RETURNED_ZERO.

5. **A batch backfill shares + drains the same key and does not stop on exhaustion.**
   `mtds-backfill-odds-20260817-062648` (historical odds backfill, RUNNING) makes
   `v4/historical/.../odds` calls with the same `odds-api-key` (URL carries the same
   key prefix) and is still looping `401 Unauthorized` across dates (e.g. 2022-10-02/03,
   `venues=0 shards=0 total_records=0 complete=False`) as of 2026-08-20 13:41Z. Its
   `credits_exhausted` trip requires `OUT_OF_USAGE_CREDITS` in the body or a present
   `x-requests-remaining` header — the historical 401 carries neither
   (`remaining=?`), so the loop never stops and would immediately re-drain any
   topped-up key.

6. **Boot-time flush 404 (historical, resolved).** The first ~15 min of the VM's life
   (08-16 14:55–15:10Z) logged `instrument-window flush failed … 404 Resource not
   found (resource=persist-sports-odds)` — 3,268 lines — because the
   `persist-sports-odds` Pub/Sub topic was created AFTER the VM booted (writer-flip
   landed ahead of topic provisioning). The topic now exists (`gcloud pubsub topics
   describe persist-sports-odds`), so this leg is resolved, but it was a second,
   independent "never captured even while the API worked" cause during that window.

## Why it matters

- **Live sports odds capture is the heartbeat for the arb/strategy stack.** This shard
  is the live odds source of record for 30 soccer leagues across all bookmakers. It has
  produced **zero** captured rows in 4 days — downstream strategy/arb has no live odds
  data.
- **The manifest is lying about coverage.** 39,515 `empty_confirmed[SOURCE_RETURNED_ZERO]`
  rows make a credential/quota outage look like "the source had no data." Downstream
  honest-coverage metrics and consumers treat a dead key as honest absence. This is a
  data-correctness violation, not just a productivity gap.
- **Third recurrence of the same class** (archived 08-02 incident was topped up with
  10M credits). Without fixing the drain (batch backfill not stopping on exhaustion) it
  will recur a fourth time.

## Fix status

- **Shipped (no new code needed for the live misclassification):**
  `market-tick-data-service@40b9b624` (upstream_failure_reason → record_failed, not fake
  SOURCE_RETURNED_ZERO) + `@3adab2d4` (credit-budget visibility). Both verified on
  `origin/live-defi-rollout` (slot-5 merge-base check) and consumed by the runner.
- **Blocked on an operator decision (BLOCKED-OPERATOR-DECISION / credentials):** the
  shared `odds-api-key` quota (15M/15M) must be topped up OR the batch backfill
  `mtds-backfill-odds-20260817-062648` paused; and the live VM
  `mtds-live-sports-odds-api-odds-20260816-145019` must be relaunched (or the deployed
  code refreshed + process restarted) to pick up the shipped fix. Relaunching now
  without quota restores honest `attempted_failed` but not captures.
- **Open gap (follow-up todo):** batch historical adapter does not stop on an exhausted
  quota.

## Recommended decision

Ask the operator for the credential decision (see the /blocked ask on this escalation):

- **A (recommended):** top up the the-odds-api `odds-api-key` quota (or rotate to a
  fresh paid key) AND pause `mtds-backfill-odds-20260817-062648` (or otherwise bound the
  batch path) so live is not re-starved; then relaunch the live odds VM on current LDR to
  pick up `40b9b624`.
- **B:** pause the batch backfill now (stops the pointless 401 loop) and keep live
  `attempted_failed`-honest after a VM relaunch, accepting no odds capture until a key
  decision is made.
- **C:** leave as-is (visibility only) — live keeps 401-looping and the manifest keeps
  fabricating SOURCE_RETURNED_ZERO until the pre-fix VM is replaced.

## Follow-up todos

- [ ] [CODE] P1 — `market-tick-data-service`: make the batch historical odds path stop on
  an exhausted quota (treat HTTP 401 on the historical endpoint as terminal: the key is
  dead or the shared quota is gone; record the current date attempted_failed then break)
  so a topped-up key is not re-drained and the pointless 401 loop ends. Provenance:
  this issue doc, `odds_api_adapter.py::_run_league_fetch_loop` (lines 855-862 — trip
  only fires on OUT_OF_USAGE_CREDITS / present x-requests-remaining, which the historical
  endpoint's 401 does not provide). **➡️ EXTRACTED → `plans/active/sports_satellite_ao_dispatch_batch17_2026_08_21.md`
  todo 1** (ag-closeout-audit sports Phase 3, 2026-08-21) — bounded, conflict-clear, no operator gate. Checkbox here
  flips once that batch's own todo lands.
- [ ] [SCRIPT] P1 — provision-check the live sink topic (`persist-{ag}-{dt}`) BEFORE a
  live producer launches (the 08-16 boot-time 404 window: writer-flip landed ahead of
  topic provisioning). Provenance: this issue doc §What I found item 6. **Re-verified 2026-08-21**: the SPECIFIC
  gap this todo names (the `persist-sports-odds` topic missing at this VM's 08-16 boot) is already closed — the
  topic + warm-sink subscription + BQ external table were provisioned by
  `/plans/active/sports_odds_writer_flip_and_trades_path_retirement_2026_08_15.md`'s Phase-0 work
  (`deployment-service@cc9974d07e` + `terraform apply`, landed 2026-08-16), per that plan's own Progress Log ("the
  event-log spine's `persist-sports-odds` Pub/Sub topic + warm-sink GCS subscription + BQ external table never
  existed... found and fixed"). What is NOT yet built is the general STANDING pre-launch provision-check this todo
  actually asks for (a reusable guard any future live-producer launch runs before booting) — left open as that
  narrower, still-real ask, not extracted this pass (no concretely scoped implementation target named yet, unlike
  todo 1 above).
- [ ] [INFRA] P0 — Relaunch `mtds-live-sports-odds-api-odds-20260816-145019` on current LDR once the
  `odds-api-key` quota is topped up/rotated, and bound the batch backfill consumer (see the `[CODE] P1` todo above)
  so it cannot re-starve live. Per D7 ruling (2026-08-22): OPERATOR-RULED 2026-08-21 — APPROVED: operator tops
  up/rotates the the-odds-api key; agent bounds the batch backfill consumer so it cannot starve live, then relaunches
  the live odds VM on current LDR once the key works. Provenance: the /blocked ask for escalation `agt-f712d7`.

## Progress Log

- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
- **ag-closeout-audit 2026-08-21 (sports tranche, Phase 2/3 sweep)**: found this doc and
  `live_sports_odds_upstream_failure_masked_as_honest_absence_2026_08_20.md` describe the identical incident (same
  VM `mtds-live-sports-odds-api-odds-20260816-145019`, same root cause) filed hours apart with no cross-reference
  either direction — added the sibling doc to `related:` above (bidirectional fix, see that doc's own Progress Log).
  Re-verified the two open non-OPERATOR todos: the CODE todo is still open, bounded, and conflict-clear — extracted
  into `sports_satellite_ao_dispatch_batch17_2026_08_21.md`. The SCRIPT todo's cited incident-specific gap is already
  closed by later work (annotated above); the narrower standing-guard ask stays open, not extracted (no scoped
  implementation target yet).
- **2026-08-22 — ruling D7 (the-odds-api key exhaustion)**: OPERATOR-RULED 2026-08-21 — APPROVED: operator tops
  up/rotates the the-odds-api key; agent bounds the batch backfill consumer so it cannot starve live, then relaunches
  the live odds VM on current LDR once the key works. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md
  ledger.
