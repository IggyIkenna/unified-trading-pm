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

- [ ] [DIAG] P2. Re-check `gs://central-element-323112-data-status-rollups/ml-service/full.json.gz` existence/freshness
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
      guarding the honest-failure path either way.
