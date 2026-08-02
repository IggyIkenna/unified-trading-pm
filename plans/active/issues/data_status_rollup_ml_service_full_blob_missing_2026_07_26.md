---
doc_type: issue
title: data-status rollup worker never writes ml-service's full.json.gz (coverage.json.gz succeeds)
summary: >-
  While diagnosing the uts-prod-data-status-rollup Cloud Run service (defi_satellite_ao_dispatch_batch1-032), found
  `gs://central-element-323112-data-status-rollups/ml-service/` carries only `coverage.json.gz` — `full.json.gz` is
  absent — while every other `_DEFAULT_SERVICES` entry except the known market-tick-data-service gap (tracked
  separately) got a fresh `full.json.gz` in the same cycle, including services processed AFTER ml-service in the
  worker's sequential list (strategy-service, execution-service). This means ml-service's full-rollup step specifically
  errors/is skipped, not a generic OOM-class or ordering artifact.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api]
scope: [engineer, admin]
tags: [data-status, rollup, cloud-run, ml-service, gcs, honest-absence]
related:
  [
    /plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md,
    /plans/archive/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: agent diagnosis of defi_satellite_ao_dispatch_batch1-032 (uts-prod-data-status-rollup health check), 2026-07-26
depends_on: []
context_scope:
  [
    /codex/02-data/honest-absence-downstream-handling.md,
    deployment-api/deployment_api/scripts/data_status_rollup_worker.py,
    deployment-api/deployment_api/services/data_status_service.py,
  ]
---

# data-status rollup: ml-service's `full.json.gz` never gets written (2026-07-26)

## What I found

Investigating `defi_satellite_ao_dispatch_batch1-032` ("diagnose the `uts-prod-data-status-rollup` job"), found the
scheduler (`uts-prod-data-status-rollup-cron`, `*/20 * * * *`) is firing reliably and the underlying Cloud Run service
(`uts-prod-data-status-rollup-svc`) IS actively producing fresh rollups for essentially every tracked service each cycle
— confirmed by reading `gs://central-element-323112-data-status-rollups/{service}/full.json.gz` creation timestamps
during one live cycle (2026-07-26 20:43–21:20 UTC):

| Service                           | `full.json.gz` created (UTC)                           |
| --------------------------------- | ------------------------------------------------------ |
| instruments-service               | 21:04:48                                               |
| market-data-processing-service    | 21:13:54                                               |
| features-delta-one-service        | 21:15:43                                               |
| features-volatility-service       | 21:16:09                                               |
| features-onchain-service          | 21:16:35                                               |
| features-calendar-service         | 21:17:37                                               |
| features-multi-timeframe-service  | 21:18:05                                               |
| features-cross-instrument-service | 21:18:30                                               |
| features-commodity-service        | 21:18:57                                               |
| **ml-service**                    | **absent — only `coverage.json.gz` (21:19:22) exists** |
| strategy-service                  | 21:19:47                                               |
| execution-service                 | 21:20:14                                               |
| market-tick-data-service          | absent — KNOWN gap, see below                          |

`market-tick-data-service`'s absence is the **already-documented, already-tracked** limitation from
`deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md` (archived) — MTDS's full 2018-today manifest build
exceeds any per-child memory ceiling ("no RAM tier through 64GB survives it"), and the real fix is scoped to
`/plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md`. **Not** what this issue is about.

`ml-service`'s absence is **different and not previously documented**: `_DEFAULT_SERVICES`
(`deployment_api/scripts/data_status_rollup_worker.py`) processes services sequentially, and ml-service sits SECOND TO
LAST (`..., ml-service, strategy-service, execution-service`) — both services processed AFTER it (strategy-service,
execution-service) got fresh `full.json.gz` in the same cycle, which rules out a generic "loop got cut off" or
container-timeout explanation (that would also block everything after ml-service, and it didn't). ml-service's own
`coverage.json.gz` succeeded in the same window (21:19:22) — only its `full.json.gz` step specifically fails or is
silently skipped. Cloud Logging for `uts-prod-data-status-rollup-svc` over the relevant window was too sparse (16
entries/2h, mostly Cloud Run revision-lifecycle noise) to see the actual per-service exception from this vantage point —
a deeper look needs either raising the service's log verbosity or reading `DataStatusService` /
`_build_one_service_rollup` for an ml-service-specific code path that could silently swallow an error only on the "full"
(not "coverage") branch.

**Caveat**: this is evidence from ONE cycle, not a confirmed-reproducible-across-cycles pattern — the next todo on this
issue should re-check across at least 2-3 cycles before concluding it's a hard, deterministic failure rather than a
transient one-off.

## Why it matters

The deployment-api `/api/data-status/manifest` endpoint serves ml-service's dashboard data-status tab from this rollup
blob (per the offline-rollup design doc, `data_status_offline_rollup_2026_05_06.md`) — if `full.json.gz` never lands,
that endpoint either 404s, falls back to the slow on-demand compute path (the exact latency problem the rollup exists to
avoid), or serves stale/no data for ml-service specifically. Silent per-service gaps in this rollup are the same class
of problem the 2026-07-13 OOM remediation fixed for MTDS/MDPS (an offender silently blocking downstream services) —
worth closing the same way (isolate + surface the real error) rather than leaving it silent.

## Recommended decision

1. Re-check across 2-3 more scheduler cycles (~20 min apart) to confirm ml-service's `full.json.gz` gap is consistent,
   not a one-off.
2. If consistent: read `DataStatusService._get_manifest_status_sync` for ml-service's specific code path (vs.
   `_get_coverage_summary_sync`, which succeeds) — likely candidates: a schema/shape assumption ml-service's manifest
   data violates that coverage's simpler summary doesn't hit, or an exception being caught too broadly and logged at a
   level Cloud Logging's current filter/verbosity drops.
3. Fix the root cause + add a regression test asserting ml-service's `full.json.gz` write is attempted and, on failure,
   that the failure is LOUD (a captured error, not a silent skip) per the honest-absence rule.

## Todos

- [x] [DIAG] P2. Re-check `gs://central-element-323112-data-status-rollups/ml-service/full.json.gz` existence/freshness
      across 2-3 more `uts-prod-data-status-rollup-cron` cycles (~20 min apart) to confirm the gap is reproducible, not
      transient. Repo: deployment-api. Done when: a Progress Log entry records either "confirmed reproducible across N
      cycles" or "resolved itself — false alarm" with timestamps.
- [ ] [CODE] P2. If confirmed reproducible: diagnose why `_build_one_service_rollup(dss, "ml-service", ...)` fails/is
      skipped while `_build_one_service_coverage` succeeds for the same service in the same run — read
      `DataStatusService`'s manifest-vs-coverage code paths for ml-service, find the divergence, and fix it (or, if
      ml-service's full-history manifest genuinely has the same "too large for any RAM tier" property as MTDS/MDPS,
      document that explicitly next to the MTDS/MDPS comment in `data_status_rollup_worker.py` rather than leaving it
      unexplained). Repo: deployment-api. Done when: `ml-service/full.json.gz` is confirmed refreshing on a live cycle,
      or the doc explicitly states why it structurally cannot (mirroring the MTDS/MDPS precedent) with a regression test
      guarding the honest-failure path either way. **UPDATED LEAD (2026-08-02)**: the "silent skip" framing is now the
      stronger hypothesis than "code-path-specific bug" — see Progress Log below. `run_rollup`'s per-service loop
      unconditionally `logger.error()`s every failure mode it can observe, including the "child exited without reporting
      (likely OOM/crashed)" fallback — yet zero Cloud Logging entries mention ml-service at all across ~24 cycles / 30h,
      unlike every OTHER currently-failing service in the list, which logs reliably every cycle. Worth checking FIRST:
      (1) does the deployed Cloud Run revision's image actually match current `_DEFAULT_SERVICES` (a stale/older
      deployed image predating the 2026-05-21 ml-training/ml-inference→ml-service consolidation comment would silently
      never attempt it), (2) does ml-service's specific compute shape trigger a native/C-level crash that takes down the
      PARENT gen1 process (not just the isolated child) — the `_rollup.py` docstring already documents this exact crash
      class for the gen2 Job; confirm it's truly gen1-safe for ml-service specifically, not just generically. A direct
      single-service test (`POST /api/data-status/rollup-run?services=ml-service`, authenticated) would settle (1) vs
      (2) vs a genuine fast-fail directly, faster than more passive cycle-watching.
- [ ] [CODE] P2. NEW regression found while diagnosing the above (not present in the 2026-07-26 baseline table, where
      instruments-service + market-data-processing-service both succeeded same-cycle): `instruments-service`'s manifest
      rollup step now fails every cycle with
      `Unable to allocate 2.55 GiB for an array with shape (29, ~11.8M) and data     type object` (its coverage step
      still succeeds — a genuine per-service partial failure, correctly isolated, not silent);
      `market-data-processing-service`'s manifest AND coverage BOTH now hit the 420s child-process timeout every cycle
      (previously only `market-tick-data-service` was the known/accepted MTDS gap — MDPS timing out is new). Both read
      as data-volume growth outpacing the `_CHILD_RLIMIT_AS_BYTES`/`_CHILD_JOIN_TIMEOUT_S` ceilings set in
      `data_status_rollup_worker.py` (same mechanism/precedent as the MTDS gap, just now also hitting MDPS + a NEW
      memory ceiling on instruments-service). Repo: deployment-api. Done when: either the per-service ceilings are
      raised/the compute is optimized to fit within them again, or (mirroring the MTDS precedent) the doc explicitly
      records these two as now-structural gaps next to the MTDS comment, with a regression test guarding the
      honest-failure (not silent-placeholder) path for both.
- [ ] [INFRA] P3. The `data-status-rollup-worker` `GcsEventSink` (the `log_event(SERVICE_PROCESSED/SERVICE_FAILED, ...)`
      calls in `run_rollup`) has not written a new dated prefix under
      `gs://central-element-323112-events/events/data-status-rollup-worker/` since `2026-06-17` — 6+ weeks stale — even
      though the worker is demonstrably still running every ~20 min today (confirmed via Cloud Logging). The per-service
      SUCCESS signal for this worker has therefore been invisible to anything reading the events bucket (not Cloud
      Logging) since 2026-06-17; only failures surface at all right now, via the separate `logger.error()` calls. Repo:
      deployment-api. Done when: either the event-sink write path is fixed and confirmed producing a fresh dated prefix
      on a live cycle, or (if intentionally retired in favor of Cloud Logging alone) that's documented explicitly rather
      than left silently dead.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **data_engineering (slot-15) 2026-08-02T19:22Z**: **CONFIRMED REPRODUCIBLE — not transient.**
  `gs://central-element-323112-data-status-rollups/ml-service/full.json.gz` is still fully absent (only
  `coverage.json.gz` exists, and it is now itself stale — `Update Time: 2026-08-01T18:13:16Z`, ~25h old at check time).
  Rather than passively watching 2-3 more live cycles, cross-checked Cloud Logging for
  `resource.labels.service_name="uts-prod-data-status-rollup-svc"` over the last 30h (`--freshness=30h`,
  ~2026-08-01T13:20Z → 2026-08-02T19:14Z) — a much stronger sample than the ask: the `*/20 * * * *` cron
  (`uts-prod-data-status-rollup-cron`, confirmed `state: ENABLED`, `lastAttemptTime: 2026-08-02T19:00:00Z`, no
  services-list override in its HTTP target — always dispatches the full `DEFAULT_SERVICES`) fired ~24 times in that
  window (`INFO "data-status rollup (LIVE): 14 service(s)"` every ~20 min, no drift/backlog). **Zero** log entries in
  that entire 30h window mention `ml-service` in any form — no
  `SERVICE_FAILED`/`manifest rollup failed`/`coverage rollup failed` line, nothing. By contrast every OTHER
  currently-struggling service in `_DEFAULT_SERVICES` logs reliably, every single cycle: `instruments-service`
  (`Unable to allocate 2.55 GiB for an array...` — NEW, see the fresh todo above), `market-tick-data-service` +
  `market-data-processing-service` (`timed out after 420s`, both — MDPS timing out is also NEW vs the 2026-07-26
  baseline), `features-delta-one-service` / `features-volatility-service`
  (`'<' not supported between instances of 'str' and 'NoneType'`). `run_rollup`'s per-service loop logs via
  `logger.error()` on every failure mode it can observe — including the "child exited without reporting a result (likely
  OOM-killed)" fallback for a crashed/timed-out isolated child — so this isn't merely "no error was caught", it's "the
  per-service loop appears to never even reach, or never returns any observable signal for, ml-service specifically."
  Also checked the `GcsEventSink` success-event channel as a second source (`log_event(SERVICE_PROCESSED, ...)` on
  success) — separately found DEAD since 2026-06-17 (its own new todo above), so it can't be used to positively confirm
  a silent ml-service success either; between the two channels there is no evidence anywhere of ml-service being
  processed at all, successfully or not. Verdict: **confirmed reproducible across ~24 cycles / 30h** (well past the
  requested 2-3), and the shape of the evidence (total silence, not a caught-and-logged error) shifts todo 2's most
  promising lead from "ml-service's compute has a code-path bug" toward "ml-service is either never reached in the
  per-cycle loop, or crashes in a way that takes the parent down before it can log" — both hypotheses, and the fastest
  way to distinguish them, are recorded in the updated todo 2 above.
