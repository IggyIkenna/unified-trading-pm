---
doc_type: plan
title: sports venue batch smoke tests — batch 1 — 2026-08-20
summary: Per-asset-group smoke-test batch for the 39 in-scope Sports (venue, data_type) rows from the canonical work list.
status: active
nature: process
asset_group: [sports]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, sports, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/sports_consolidated_closeout_2026_07_19.md]
created: "2026-08-20"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.8
estimate_calibrated_ai_days: 1.44
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
effort: high
context_scope: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /codex/02-data/availability-manifest-and-data-status.md, /codex/02-data/sports-2020-06-data-floor.md, unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py]
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
---

# Sports venue smoke-test batch 1

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Apply the Sports 2020-06 data floor; filter the generator output to `asset_group=sports` at execution time.

## Todos

- [ ] [BACKEND] P0. Execute the canonical batch smoke contract for every current Sports row above the 2020-06-06 data floor; Gate: rows, canonical paths, manifest atoms, and genuine capture statuses are measured per unit.
- [ ] [BACKEND] P1. Record one testnet verdict for every Sports venue, including matching-engine simulation where appropriate; Gate: every distinct venue has a written verdict.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage for provisionable credentials and record an honest unavailable result for accounts that cannot be provisioned; file an operator credential request when a credential gap is confirmed. Gate: no missing credential is treated as a wiring absence.
- [ ] [BACKEND] P1. Track every failed or absent Sports row with its source and data type; Gate: expected-unattempted is never presented as captured.
- [x] ✅ [BACKEND] P0. Verify the Sports data floor and source-scoped Databento/canonical checks with a negative control; Gate: pre-floor or no-data probes fail rather than pass. — `unified-api-contracts@25bcebdd` + runtime evidence below.

## Progress Log

**2026-08-20 — forked from W5.** Sports keeps the data-floor rule in its context scope and follows W4's five-todo
AG batch shape.

**2026-08-21 — slot-4 verification.** The managed UAC quality gate completed with `ALL QUALITY GATES PASSED`
(390s). The runtime generator measured 364 declared pairs, 8 exact Databento exemptions, 356 in-scope rows, and 39
Sports rows. Direct assertions confirmed every Sports row resolves to a non-Databento source; each distinct resolved
source/data-type pair rejects the pre-floor `2020-06-05` window with the documented empty/inverted-range signal; and
the canonical-path negative control is rejected by `canonical_path_violations(require_pipeline_mode=True)`. The
source-scoped negative control `CBOE/ohlcv_24h -> yahoo` remains in scope and outside the eight-cell exemption set.
This closes only the floor/source/oracle verification todo; row-level production capture, manifest atoms, and genuine
capture statuses remain open under the first todo.

**2026-08-21 — slot-5 execution attempt #1 (denominator mismatch, superseded by attempt #2 below).** Launched
`deployment-service/scripts/vm/launch-pipeline-e2e-check-driver-vm.sh --service mtds --day 2026-08-20 --asset-group
SPORTS --legs force,skip,canonical --mvp-only --require-captured --auto-day --wall-clock-timeout-sec 14400` (VM
`pipeline-e2e-check-mtds-20260821-131503-1ccdef`). Terminal `EXIT_STATUS=1` after ~2h25m. Report:
`gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_sports.md`
— `total=75 passed=0 failed=75 ambiguous=0 skipped=0` over 25 `(venue, odds)` shards × 3 legs, every row genuinely
`no_parquet_under:...`/`canonical_no_matching_objects_in_test_bucket` (fail-closed, not ambiguous). Root cause traced
into one child VM's own log: `No active venues for date=2026-07-26 asset_groups=['SPORTS']` — the `--auto-day`
sampler resolved a day with no scheduled fixture activity for the sampled venue, so the force leg legitimately wrote
zero rows and every downstream leg failed closed on the empty result.

**This run used the wrong CLI mode.** `--mvp-only` invokes the plain MVP shard enumeration, not the
`--generator-scoped-sports` mode `market-tick-data-service@aaa0c8b1b6` shipped specifically for Sports
(`/plans/active/issues/sports_venue_smoke_checker_scope_and_canonical_gap_2026_08_20.md`, which this plan's own
context_scope did not surface because it lives under the sibling `venue_smoke_test_bar` doc's issue tree, not this
plan's own). The result: 25 shards / 75 checks measured here does not match the 39-row canonical UAC work-list
denominator this todo's Gate requires ("every current Sports row"). The zero-capture/`No active venues` finding
itself is genuine evidence (and consistent with that issue doc's own prior finding of the identical failure mode on
`SPORTS:PINNACLE:odds`/2025-12-20), but the row coverage is not the canonical set. Re-launching with
`--generator-scoped-sports` (see next entry) rather than closing this todo on the wrong denominator.
