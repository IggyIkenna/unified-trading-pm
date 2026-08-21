---
doc_type: issue
title: Prediction smoke checker samples a KALSHI instrument for a POLYMARKET row
summary: >-
  The Prediction MTDS smoke driver selected a KALSHI raw parquet/instrument while executing the POLYMARKET trades
  row, then launched POLYMARKET force and skip VMs with that KALSHI identifier. The terminal VM wrote zero records,
  so the row is not a valid capture proof and the checker can mask a venue-routing defect as an ordinary absence.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [venue-readiness, smoke-test, prediction, pipeline-e2e-check, instrument-sampling, cross-venue]
related: [/plans/active/prediction_venue_smoke_batch1_2026_08_20.md]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
source: /plans/active/prediction_venue_smoke_batch1_2026_08_20.md
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
context_scope: [market-tick-data-service/scripts/pipeline_e2e_check.py, /codex/02-data/availability-manifest-and-data-status.md]
---

# Prediction smoke checker cross-venue sampling

## What I found

- The live driver `pipeline-e2e-check-mtds-20260821-012839-18224b` enumerated four current Prediction rows.
- For `PREDICTION:POLYMARKET:trades`, the driver logged a sampled ID of
  `KALSHI:PREDICTION_MARKET:FEDHIKE-26DEC31` from
  `raw_tick_data/.../venue=KALSHI/.../data_type=trades/...parquet`, then launched
  `mtds-backfill-prediction-pipelinecheck-20260821-013210-9ac067` with `--venues POLYMARKET` and that KALSHI ID.
- The force VM reached terminal `EXIT_STATUS=0` but processed `0 records`, emitted `SHARD_INCOMPLETE`, and wrote
  only partial manifest atoms. The subsequent skip VM repeated the same mismatched identifier and also produced no
  capture proof.

## Why it matters

The smoke contract requires a row-specific capture proof. A cross-venue sample makes the force/skip result invalid:
it can report a real venue as empty because the checker requested an identifier belonging to another venue. This also
violates the source-scoped `(venue, data_type)` shard atom and prevents the Prediction P0 gate from closing honestly.

## Recommended decision

- [ ] [BACKEND] P0. Make the MTDS smoke sampler enforce the requested `(asset_group, venue, data_type)` against the
  source parquet path and sampled instrument identity; reject or resample any candidate whose path venue differs from
  the requested venue, then add a regression test for the POLYMARKET/KALSHI collision (repo: market-tick-data-service).
- [ ] [BACKEND] P0. Rerun all four generator-scoped Prediction rows after the sampler fix, retaining per-row force/skip,
  canonical-path, manifest-atom, and genuine `capture_status` evidence (repo: market-tick-data-service).

## Progress Log

**2026-08-21 — slot 7.** Finding measured during the live staging run above; terminal VM logs and the aggregate report
are retained after terminal completion. The aggregate report finished at `2026-08-21T01:47:07Z` with 12 leg cells: 1 passed, 7 failed, and 4 explicitly skipped. The issue remains open until the sampler is fixed and the four-row
contract is rerun.

**2026-08-21 — terminal evidence.** The report recorded `POLYMARKET/book_snapshot_5` canonical as the sole pass (`checked=7 canonical=7 raw=0`); both trades rows failed force and skip capture checks with zero parquet, and both trades canonical checks had no matching rows. `KALSHI/book_snapshot_5` force/skip were correctly classified as live-only, while its canonical check had no matching rows. This is a RED execution result, not a valid green capture claim.
