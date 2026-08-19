---
doc_type: issue
title: >-
  DP_CRON_DID_NOT_FIRE (and every other _RECURRING_ALERT_COOLDOWNS event) still
  violates its 1800s cooldown live — NEW root cause: in-memory AlertDeduplicator
  state is wiped on every dp-alerting-subscriber redeploy, which lands far more
  often than the cooldown window
summary: >-
  6-hourly `/data-pipeline-alerts-reconcile` sweep (2026-08-18) found `#data-pipeline-alerts`
  NOT quiet: `slack-read-channel.py data-pipeline-alerts 24` returned 150 messages/24h
  (66 `DP_CRON_DID_NOT_FIRE`, 62 `DP_RUN_MOSTLY_EMPTY`, 19 `DP_VM_EXIT_NONZERO`, 3 `DP_VM_STALL`).
  Both `DP_CRON_DID_NOT_FIRE` and `DP_RUN_MOSTLY_EMPTY` have PRIOR, confirmed-shipped fixes
  for exactly this symptom class (`dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md`,
  archived `dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md`, archived
  `dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md`) — the most recent of which was
  CONFIRMED 1800s-compliant live as of 2026-08-17 09:36Z. This sweep re-sampled the exact
  same previously-fixed identity (`mtds-live-cefi-consolidated-20260817-025031`/BYBIT-FUTURES/
  `book_snapshot_5`+`derivative_ticker`+`depth_of_book_10`+`trades`) and found it STILL firing
  every 15-17 minutes as of 2026-08-18 02:06Z, ~16.5h after the last confirmed-good sample —
  a live regression of an event that was proven working, not a residual pre-existing gap.

  Root cause (NEW, not previously identified): `alerting_service.core.dedup.AlertDeduplicator`
  stores its `_seen` dedup-key dict as a plain in-process Python dict, keyed by
  `time.monotonic()` timestamps, on a module-level singleton
  (`alerting_service/notifiers/router.py:68`). `dp-alerting-subscriber` runs `minScale=1,
  maxScale=1` (confirmed by two prior sweeps, ruling out horizontal fragmentation) — but a
  NEW Cloud Run REVISION is a fresh container/process regardless of scale settings, and this
  service redeploys far more often than any `_RECURRING_ALERT_COOLDOWNS` window (1800s/30min):
  `gcloud run revisions list --service=dp-alerting-subscriber` shows 5 revisions landing in the
  ~3.25h window 2026-08-17T22:46Z-2026-08-18T02:08Z, including a 17-minute gap between
  `-00112-z5m` (00:38Z) and `-00113-2vg` (00:55Z) — SHORTER than the 30-min cooldown itself.
  Every redeploy silently resets `_seen` to empty, so the very next fire for ANY identity
  (not just the one this sweep sampled) is treated as first-occurrence and delivered instead
  of deduped — structurally defeating every entry in `_RECURRING_ALERT_COOLDOWNS`
  fleet-wide, independent of which detector or event name is involved. This is NOT the
  volatile-detail-key bug (already fixed) and NOT the RESOLVED-bookend severity-override bug
  (already fixed) — those explain SPECIFIC identity-hash/severity-classification defeats;
  this explains why the cooldown breaks even for an identity with a fully stable hash and
  correct severity, on a service with a normal/expected deploy cadence for an actively-worked
  repo.
status: open
nature: issue
asset_group: [cefi, tradfi, cross-cutting]
stage: [live, meta]
repos: [alerting-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    data-pipeline-alerts,
    dp-cron-did-not-fire,
    dp-run-mostly-empty,
    alert-dedup,
    alerting-service,
    cloud-run-redeploy,
    in-memory-state-loss,
    live-capture-stall,
  ]
related:
  [
    /plans/archive/issues/dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md,
    /plans/active/issues/dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md,
    /plans/archive/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-08-18
author: data_pipeline_alerts_reconciler (slot 23, one-shot dispatch agt-d52c5d)
parent_epic: security_and_cross_cutting_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-19
locked_since:
context_scope:
  [
    alerting-service/alerting_service/notifiers/router.py,
    alerting-service/alerting_service/core/dedup.py,
    deployment-service/deployment_service/data_pipeline_monitors/renag_tracker.py,
    /plans/archive/issues/dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md,
  ]
source: >-
  6-hourly data_pipeline_alerts_reconciler dispatch (agt-d52c5d, 2026-08-18), running the
  /data-pipeline-alerts-reconcile skill's mandatory ground-truth Slack read + registry
  cross-check + § 1.5(ii) actuator/dedup-state-persistence check.
---

# DP_CRON_DID_NOT_FIRE cooldown still violated — root cause is redeploy-wiped in-memory dedup state

## What was found

Fresh `slack-read-channel.py data-pipeline-alerts 24` (150 msgs/24h) + a targeted 2h re-pull
confirmed the SAME identity that a prior sweep (2026-08-17, slot 10) proved 1800s-compliant at
`09:06Z/09:36Z` is firing every 15-17 min again as of `2026-08-18 01:21Z/01:36Z/01:52Z/02:06Z`
— a regression, not a stale finding. Also observed the SAME every-~15min pattern on `DP-LIVE-003`
(`missing_live_producer_watcher`, "LONG_LIVED_LIVE producer prefix ... ZERO running instances")
and `DP-WATCHER-002` (`cron_alive_probe`, "cron '...' did not fire on schedule") — three
DIFFERENT detectors, all sharing the `DP_CRON_DID_NOT_FIRE` event name and the same downstream
1800s cooldown, all violating it simultaneously. That breadth (not confined to one detector's
own `details` shape) is what pointed away from a per-detector volatile-field bug and toward the
shared `AlertDeduplicator` layer itself.

## Root cause

`alerting_service/core/dedup.py::AlertDeduplicator` — `_seen: dict[str, tuple[float, float]]`
is a plain in-process dict; `is_duplicate()` timestamps entries with `time.monotonic()`. The
router module (`alerting_service/notifiers/router.py:68`) instantiates ONE singleton
(`_deduplicator = AlertDeduplicator(ttl_seconds=60.0)`) at import time. `dp-alerting-subscriber`
is confirmed `minScale=1, maxScale=1` (ruling out cross-instance fragmentation, per the prior
sweep's own check) — but that setting only bounds CONCURRENT instances of a given REVISION; it
says nothing about revision churn. `gcloud run revisions list --service=dp-alerting-subscriber
--region=asia-northeast1` (checked 2026-08-18 ~02:10Z):

```
dp-alerting-subscriber-00114-pp2  2026-08-18T02:08:33Z
dp-alerting-subscriber-00113-2vg  2026-08-18T00:55:55Z
dp-alerting-subscriber-00112-z5m  2026-08-18T00:38:26Z
dp-alerting-subscriber-00111-9gf  2026-08-17T23:44:26Z
dp-alerting-subscriber-00110-bhs  2026-08-17T22:46:07Z
dp-alerting-subscriber-00109-zlx  2026-08-17T13:54:22Z
...
```

5 revisions in ~3.25h; the `00112`→`00113` gap is 17 minutes — shorter than the 1800s cooldown
itself. Each new revision is a fresh container/process: `_deduplicator._seen` starts empty every
time. A redeploy landing inside a still-open 30-min cooldown window silently resets it, so the
NEXT fire for every currently-cooling-down identity (not just the one sampled) is treated as a
first occurrence and delivered — this is orthogonal to, and not fixed by, either of the two
previously-shipped fixes (the volatile-`attempted_age_hours`-key fix and the RESOLVED-bookend
severity-override fix), both of which addressed identity-hash/classification correctness, not
state durability across redeploys.

## Why this evaded the two prior investigations

Both prior sessions explicitly checked for "instance recycling" and ruled it out — but their
checks (Cloud Logging `"AlertSubscriber initialized"` count staying at 2 through a ~7h window;
a live-behavior sample confirming 1800s-compliance at `09:06Z→09:36Z`) happened to land inside
windows WITHOUT an intervening redeploy. This repo's actual redeploy cadence (5 revisions/3.25h
observed here) is fast enough that a 30-min-window sample can easily land clean by chance while
the underlying fragility remains. The mechanism is real and reproducible in principle (any redeploy
during an open cooldown window resets it) even though it isn't deterministic per-sample.

## Recommended fix (scoped, not yet implemented — flagged for next dispatch)

Persist `AlertDeduplicator`'s `_seen` state (or at minimum the subset keyed to
`_RECURRING_ALERT_COOLDOWNS`-eligible events) to GCS, mirroring the EXACT pattern already proven
in this codebase for the sibling redeploy-survives-restart problem —
`deployment_service/data_pipeline_monitors/renag_tracker.py::RenagTracker` (load-at-start,
persist-after-record, JSON blob in `vm-census/`, fail-open on read/parse error). Candidate design:
add an optional GCS-backed store to `AlertDeduplicator` (or a parallel persisted layer specifically
for the recurring-cooldown subset, keeping the general 60s-default path in-memory-only to avoid
adding GCS I/O to every alert route call) — load once per container start, write-through on each
new key recorded. Scope carefully: `route_event`/`route_event_with_explicit_channels` are hot
paths for EVERY alert in the system (not just DP-*), so a blanket persistence change has real
blast radius; the narrower, lower-risk cut is to persist ONLY entries whose `ttl_override` came
from `_RECURRING_ALERT_COOLDOWNS` (i.e., the ones that need to survive minutes-scale gaps in the
first place — the 60s-default path is already shorter than any plausible redeploy gap and doesn't
need this).

This is a genuinely new, cross-cutting finding (affects every event in `_RECURRING_ALERT_COOLDOWNS`,
not just `DP_CRON_DID_NOT_FIRE`) — flagged per findings-triage HARD RULE rather than attempted in
this one-shot medium-effort sweep, which instead shipped a smaller, safe, immediately-actionable
defense-in-depth fix at the SOURCE for one of the three affected detectors (see Progress Log).

## Also shipped this sweep (source-side defense-in-depth, independent of the above)

`deployment-service@9abb2d20e4`: `missing_live_producer_watcher.check_missing_live_producers`
(DP-LIVE-003) had NO ongoing re-fire suppression at all (only `MissTracker`'s onset gate) — wired
the existing `RenagTracker`/`apply_cooldown` pattern into it (mirrors the 2026-07-15
`DP_RUN_MOSTLY_EMPTY` fix #2), so this ONE detector now re-nags source-side on a 1800s cooldown
regardless of whether the downstream alerting-service dedup is working. Does not fix the other two
affected detectors (`DP-LIVE-004`/`live_stream_watcher`, `DP-WATCHER-002`/`cron_alive_probe`) —
both already have source-side renag_tracker wiring per the codebase's existing pattern, so their
repeat-firing is downstream-only and depends entirely on this doc's root cause getting fixed.

## Todos

- [x] ✅ [SCRIPT] P1. Wire `RenagTracker`/`apply_cooldown` into `missing_live_producer_watcher`
      (DP-LIVE-003) as source-side defense-in-depth, independent of the alerting-service dedup bug.
      Evidence: `deployment-service@9abb2d20e4`, `quality-gates.sh --no-fix` ALL PASSED (252s).
- [x] ✅ [SCRIPT] P1. **RESOLVED 2026-08-19 (data_pipeline_failure escalation worker, agt-b66b27)**
      — Design + ship GCS-persisted state for the `_RECURRING_ALERT_COOLDOWNS` subset of
      `AlertDeduplicator` (repo: alerting-service), scoped to avoid adding GCS I/O to the general
      60s-default dedup path. Shipped a new `RecurringCooldownState` layer
      (`alerting_service/core/recurring_dedup_persistence.py`) consulted in `router._is_duplicate_alert`
      (both `route_event`/`route_event_with_explicit_channels` call sites) ONLY for events carrying a
      `_RECURRING_ALERT_COOLDOWNS` `ttl_override` — reuses the ALREADY-BUILT-BUT-NEVER-CALLED
      `AlertStorageStore.read_cooldown_state()`/`write_cooldown_state()` (`alerting/state/cooldowns.json`)
      rather than inventing a new GCS blob/bucket (that persistence layer shipped with zero production
      caller until this fix — the same "built but not called" anti-pattern already documented for the
      revocation actuator in `/codex/05-infrastructure/data-pipeline-alerts.md`). State loads once per
      process/container lifetime (cached) and writes through only on an actual new delivery
      (cooldown-gated, so writes stay infrequent); fails OPEN (never suppress, never raise) on any GCS
      read/write error, mirroring `RenagTracker`'s documented fail-open direction. Evidence:
      `alerting-service@f48a61193f`, `quality-gates.sh --no-fix` ALL QUALITY GATES PASSED (52s, full
      1070-test suite green incl. 2 new test files + isolation fixtures added to `tests/conftest.py`
      to prevent the persisted layer from leaking state across unrelated tests). **Live-behavior
      re-sample deferred, not yet done this session** — the doc's own verify bar (≥2 observed redeploys
      within one 30-min cooldown window post-fix) needs a follow-up dispatch once `dp-alerting-subscriber`
      picks up this deploy; tracked as the new todo below rather than closed on unit-test evidence alone.
- [ ] [SCRIPT] P2. **ADDED 2026-08-19** — live-verify the `RecurringCooldownState` fix
      (`alerting-service@f48a61193f`) actually holds a `DP_CRON_DID_NOT_FIRE`/`DP_RUN_MOSTLY_EMPTY`/
      `CONSOLIDATOR_DOWN` cooldown across a real `dp-alerting-subscriber` redeploy: confirm the deploy
      reached `dp-alerting-subscriber` (`gcloud run revisions list`, digest/content-check per this doc's
      own established discipline — not SHA-ancestor alone, Option-B direct-promote rewrites commits),
      then sample the SAME previously-repeat-firing identity (BYBIT-FUTURES on
      `mtds-live-cefi-consolidated-*`, or whatever is currently firing) across ≥2 observed redeploys
      within one 30-min window and confirm it stays suppressed for the full cooldown instead of
      re-firing on every redeploy. Also spot-check `alerting/state/cooldowns.json` in the
      `alerting-service-<project>` bucket actually gets written (confirms the wiring reaches real GCS,
      not just the unit-test-mocked path). Repo: alerting-service.
- [x] ✅ [OPERATOR] P1. (carried over) Investigate the 2 genuine live-capture stalls first
      flagged 2026-08-17 (BYBIT-FUTURES on `mtds-live-cefi-consolidated-20260817-025031`; CME
      trades on `mtds-live-tradfi-cme-trades-20260809-163443`) — both VMs running, both
      actively attempting, neither producing rows. **RESOLVED 2026-08-18 — two DIFFERENT root
      causes, each with a fresh live-VM evidence check (not a re-citation of old findings):**
      - **CME trades**: NOT a new bug — a live-side recurrence of the already-tracked
        `/plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`
        (Databento account billing suspended, `api_key_deactivated`/`unpaid invoice` CRAM auth
        failure). Fresh manifest read confirms the exact same boundary: `captured` cleanly
        2026-08-09..08-11, then 100% `empty_confirmed`/`SOURCE_RETURNED_ZERO` every single date
        2026-08-12 through TODAY (rows written as recently as `2026-08-18T10:26:01Z`). This is
        `BLOCKED-OPERATOR-DECISION` (pay the invoice) — that doc's existing `[OPERATOR]` P0 todo
        already covers it; added a fresh Progress Log reconfirmation there rather than
        duplicating. No code fix possible — the feed is dead on the vendor side.
      - **BYBIT-FUTURES**: a genuine, distinct CODE bug — root-caused and FIXED this session.
        The `BYBIT-FUTURES→BYBIT` Tardis-alias venue resolution
        (`_resolve_is_lookup_venue`, `market_tick_data_service/live/_is_universe.py`) correctly
        returns instruments-service's combined `venue=BYBIT` catalog, but that catalog mixes
        737 PERPETUAL + 44 FUTURE + 501 SPOT_PAIR instruments under one venue token (IS only
        writes ONE blob per Tardis exchange). Bybit's public LINEAR WS endpoint cannot serve
        SPOT_PAIR symbols. A 2026-08-15 diagnosis
        (`/plans/active/cross_ag_live_capture_parity_2026_08_14.md` Finding C) had already
        identified BOTH required fixes — (1) filter to PERPETUAL/FUTURE only, (2) chunk the
        subscribe request under Bybit's 21,000-char cap — but only fix (2) ever shipped
        (`market-tick-data-service@a89bd433`); fix (1) was designed and stashed
        (`orchestrator-slot-4-bybit_futures_dp_live_004_subscribe_fix-001`) but never committed
        (host RAM contention blocked `quality-gates.sh` at the time) and the stash was never
        recovered. Live-reconfirmed on the CURRENT VM (launched 2026-08-17, well after the
        chunking fix landed): its manifest shard shows ALL 10,258 BYBIT-FUTURES rows
        `empty_confirmed`/`SOURCE_RETURNED_ZERO`, with the connector still attempting the FULL
        unfiltered 1,282-instrument universe (737+44+501, matching the source catalog exactly)
        — confirming the filter genuinely never shipped and chunking alone was not sufficient.
        Shipped the missing filter this session: `_is_linear_derivative()` added to
        `market-tick-data-service/market_tick_data_service/live/connectors/bybit_ws.py`,
        applied in `BybitFuturesWSFeedConnector.connect()`/`.subscribe()` and (via the new
        `is_bybit_linear_derivative` export) in `bybit_futures_book_ticker_ws.py`'s
        `_BybitBookStateConnector` + `BybitFuturesTickerWSConnector` — all 4 BYBIT-FUTURES
        data_types now filter SPOT_PAIR ids before ever building a subscribe topic. See
        `cross_ag_live_capture_parity_2026_08_14.md` Finding C for full evidence + the new
        follow-up todo (verify a real `captured` row post-relaunch, since this VM needs a
        fresh cycle to pick up the new code — not blocking this todo's resolution, the code
        fix itself is what this todo asked for).

## Progress Log

- **2026-08-19 (data_pipeline_failure escalation worker, slot 16, agt-b66b27)**: dispatched off a
  CRITICAL `DP_CRON_DID_NOT_FIRE` (DP-WATCHER-002) escalation naming cron `dp-exit-code-monitor`
  (no issue slug — alert-carries-the-details path). Live-verified `dp-exit-code-monitor` itself is
  healthy (`gcloud scheduler jobs describe`: `ENABLED`, `0 * * * *`; last 8 `gcloud run jobs
  executions list` rows all "Execution completed successfully" in 55s-2m26s) — the cron is NOT
  failing to fire. Cross-checked `dp-alerting-subscriber` revision churn
  (`gcloud run revisions list`): 2 revisions 95s apart same day (`-00127-z47` 01:38:16Z →
  `-00128-7nj` 01:39:51Z), confirming this doc's root cause is still live as of today. Fresh
  `slack-read-channel.py data-pipeline-alerts 3` showed the SAME DP_CRON_DID_NOT_FIRE spam pattern
  this doc already diagnosed (DP-LIVE-004 findings mislabeled under the shared event name, dozens of
  sports-odds venues re-firing at 05:06Z). Concluded this escalation is a duplicate/spam symptom of
  THIS doc's already-open root cause, not a new failure mode — did not file a separate issue doc.
  Shipped the doc's own recommended fix (the one remaining open P1 todo) rather than just
  re-diagnosing: see the flipped todo above for the full design + evidence. Pinged the authoring
  slot with the outcome.
- 2026-08-18: `data_pipeline_alerts_reconciler` (slot 23, dispatch agt-d52c5d) ran the 6-hourly
  `/data-pipeline-alerts-reconcile` sweep. Ground-truth Slack read (150 msgs/24h) found the
  channel not quiet; cross-checked against the two prior confirmed-fixed issue docs for this
  exact symptom, re-sampled the previously-fixed identity live, and found it firing every 15-17
  min again. Root-caused to Cloud Run revision churn wiping `AlertDeduplicator`'s in-memory
  `_seen` state faster than the 1800s cooldown window — a new, cross-cutting finding distinct from
  the two already-shipped fixes. Shipped a bounded, low-risk source-side defense-in-depth fix for
  one of the three affected detectors (DP-LIVE-003); filed this doc for the deeper
  alerting-service persistence fix, which needs careful scoping given `AlertDeduplicator`'s hot-path
  usage across every alert in the system, not just DP-*.
- **data_pipeline_alerts_reconciler 2026-08-18 (slot 1, dispatch agt-a01f7a), re-confirm sweep**: fresh
  `slack-read-channel.py data-pipeline-alerts 24` (1698-line dump) + `gcloud run revisions list
  --service=dp-alerting-subscriber` re-confirm the SAME symptom, unchanged, no new mechanism: `DP-LIVE-004`
  (BYBIT-FUTURES all 5 data_types + CME trades) still firing `DP_CRON_DID_NOT_FIRE` every ~14-15min at
  `06:22Z/06:36Z/06:37Z` today, well under the 1800s cooldown; a new revision `-00116-vx8` deployed
  `06:15:16Z`, 6-7min before the 06:22Z fire, consistent with (not new evidence beyond) this doc's own
  redeploy-wipes-`_seen` root cause. `DP_RUN_MOSTLY_EMPTY` event counts (600/24h) are ~98% `STATIC
  BACKLOG — no new attempted_failed activity` (already-tracked pre-existing backlogs, not fresh
  regressions) with a handful of `Fresh` cells matching known-open items (`defi/dex_pool_swaps`,
  `tradfi/ohlcv_*`, `sports/odds_horizon_bucket`) already covered by their own asset-group issue docs —
  no new class found. One `DP_VM_STALL` (`canonical-migration-cefi-itype-casing-apply-20260818-012605`)
  self-resolved by `03:41Z`, no action needed. Did not re-attempt the P1 GCS-persistence design (still
  correctly scoped as its own dispatch, not a low-effort reconciliation-sweep change to a hot alert path)
  or re-run the P1 Cloud-Logging root-cause trace (no new evidence to add beyond what's above). No
  behavioral change shipped this pass — channel confirmed NOT quiet, all 3 open todos above remain the
  correct next actions, no new registry entry needed (no new failure class).
- **2026-08-18 (interactive session, dispatched specifically to answer the [OPERATOR] investigate-the-2-stalls
  todo)**: root-caused BOTH live-capture stalls with fresh live evidence (VM SSH, direct manifest reads via UTL
  `download_bytes`, source-catalog cross-checks — never gcloud/gsutil subprocess). CME trades: NOT a code bug, a
  live-side recurrence of the already-open `tradfi_databento_account_billing_suspended_2026_08_09.md` (Databento
  billing block) — reconfirmed via a fresh manifest read (still zero as of `10:26:01Z` today), added a Progress Log
  entry there, no code fix possible. BYBIT-FUTURES: a genuine code bug — the BYBIT-FUTURES→BYBIT Tardis-alias
  universe resolution returns an UNFILTERED catalog (737 PERPETUAL + 44 FUTURE + 501 SPOT_PAIR), and Bybit's LINEAR
  WS endpoint can't serve the SPOT_PAIR symbols; a 2026-08-15 diagnosis already named this exact fix but only half of
  it (message chunking) ever shipped, the other half (instrument-type filtering) was stashed and lost. Shipped the
  missing filter (`_is_linear_derivative()` in `bybit_ws.py`, applied across all 4 BYBIT-FUTURES connectors) —
  evidence + full diagnosis in `cross_ag_live_capture_parity_2026_08_14.md` Finding C and this doc's flipped todo
  above. Flipped the carried-over [OPERATOR] todo to done. All todos in this doc are now resolved except the P1 GCS-
  persistence design (still correctly its own dispatch, not attempted this session — out of this session's assigned
  scope, which was specifically the live-capture-stall investigation).
