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
parent_epic: infrastructure_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-18
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
- [ ] [SCRIPT] P1. Design + ship GCS-persisted state for the `_RECURRING_ALERT_COOLDOWNS` subset
      of `AlertDeduplicator` (repo: alerting-service), scoped to avoid adding GCS I/O to the
      general 60s-default dedup path. Verify post-fix via a live-behavior re-sample that survives
      at least 2 observed redeploys within one 30-min cooldown window (a single quiet sample is not
      sufficient evidence per this doc's own "why this evaded prior investigations" section).
- [ ] [OPERATOR] P1. (carried over, unresolved) Investigate the 2 genuine live-capture stalls
      first flagged 2026-08-17 (BYBIT-FUTURES on `mtds-live-cefi-consolidated-20260817-025031`;
      CME trades on `mtds-live-tradfi-cme-trades-20260809-163443`) — both VMs running, both
      actively attempting, neither producing rows. Needs a look at the live capture
      process/adapter itself (auth, upstream API change, schema mismatch), not a VM relaunch.

## Progress Log

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
