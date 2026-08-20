---
doc_type: issue
title: Sports venue smoke checker expands the denominator and skips the canonical leg
summary: >-
  The canonical Sports smoke execution was scoped by the work-list to 39 rows, but the MTDS checker expanded it to
  252 shards by adding observed out-of-registry cells and league partitions. The same checker explicitly skips its
  canonical leg for Sports, so the run cannot satisfy the batch smoke contract's canonical-path gate.
assigned_vm: planning
created: "2026-08-20"
author: slot-7 (backend_engineer)
source:
  - /plans/active/sports_venue_smoke_batch1_2026_08_20.md
  - /plans/active/venue_smoke_test_bar_2026_08_16.md
  - unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py
status: open
nature: issue
parent_epic: security_and_cross_cutting_master
priority: P0
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [sports, venue-smoke, denominator, canonical-path, manifest, capture-status]
related:
  - /plans/active/sports_consolidated_closeout_2026_07_19.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - /codex/02-data/sports-2020-06-data-floor.md
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope:
  - /plans/active/sports_venue_smoke_batch1_2026_08_20.md
  - /plans/active/venue_smoke_test_bar_2026_08_16.md
  - /codex/02-data/availability-manifest-and-data-status.md
  - /codex/02-data/sports-2020-06-data-floor.md
  - unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py
---

# Sports venue smoke checker scope and canonical gap

## What I found

On 2026-08-20, the live UAC work-list generator reported the plan's expected Sports denominator of **39** in-scope
`(venue, data_type)` rows. I launched the dedicated test-bucket-only MTDS driver using the canonical busy-day fixture
date `2025-12-20` (the pinned `SPORTS_SMOKE_DATES["busy"]` date, above the 2020-06-06 floor), with
`--legs force,skip --require-captured --auto-day`.

The driver measured **252 shards**, not 39 rows. Its `_augment_with_observed_cells` step added **96
`(venue, data_type)` cells** observed in PROD but absent from the UAC enumeration; Sports also expands the work into
the manifest's real `league_id` shard axis. This is a different denominator from the plan's generator output and makes
the execution neither a 39-row smoke result nor a clean registry audit.

The first force child (`mtds-backfill-sports-pipelinecheck-20260820-200221-78892f`) terminated with
`EXIT_STATUS=0`, but its run log said `No active venues for date=2025-12-20 asset_groups=['SPORTS']`. The driver then
started the skip leg for the same cell. A zero exit code therefore does not establish a captured row, canonical object,
or genuine capture status for that unit.

The MTDS checker source and skill contract explicitly state that the `canonical` leg is **skipped for Sports**. Thus the
existing force/skip run cannot prove the required canonical-path leg, even when its manifest row is `captured`.

## Why it matters

The parent smoke contract requires, per named unit: real rows, a canonical path checked by the machine oracle or the
writer's canonical validator, a matching manifest shard atom, and a genuine `capture_status` rather than
`expected_unattempted`. The current checker can produce a zero-row successful child and silently widen the denominator,
while its canonical leg leaves Sports unverified. Flipping the P0 checkbox from this run would overclaim the contract.

The 96 observed cells also represent a registry/manifest vocabulary drift that should be resolved explicitly. They must
not be silently folded into the 39-row denominator, and they must not be ignored if they are meant to be current Sports
capabilities.

## Recommended decision

Cancel the over-broad 252-shard run after preserving its measured logs, then add a generator-scoped execution path that
accepts exactly the 39 current work-list rows (while reporting observed out-of-registry cells separately). Add a
Sports-specific canonical verifier using the UAC path oracle where its path shape is covered, or the Sports writer's
canonical template validator where the generic oracle is structurally inapplicable. Re-run the narrowed contract only
after those gates fail closed on the `No active venues`/zero-row case.

## Todos

- [ ] [BACKEND] P0. Add a generator-scoped Sports execution mode to the MTDS pipeline checker (or a dedicated batch
      runner) that runs exactly the 39 rows emitted by
      `unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py` and reports observed out-of-registry cells
      separately (repo: market-tick-data-service; supporting contract: unified-api-contracts).
- [x] [BACKEND] P0. Implement and run a Sports canonical-path verification leg that checks the actual test-bucket
      object against the applicable UAC machine oracle or Sports writer template, and fails closed when no object/row is
      produced (repo: market-tick-data-service) — market-tick-data-service@01745226fa + QG=11102 passed, 28 skipped, 1 xpassed, 19 warnings; runtime report
      `data_pipeline_e2e_check_mtds_2025_12_20.md` (`canonical_no_matching_objects_in_test_bucket`, fail-closed).
- [ ] [DATA] P1. Reconcile the 96 observed Sports `(venue, data_type)` cells absent from the UAC registry against the
      canonical venue/data-type declarations; either register them with source-scoped capabilities or classify them as
      legacy/non-canonical observations (repo: unified-api-contracts).
- [ ] [BACKEND] P1. Preserve a per-unit result schema containing row count, canonical-path verdict, manifest shard-atom
      verdict, `capture_status`, source, and the exact no-active-venue/zero-row reason so an exit code of zero cannot be
      mistaken for a passing smoke test (repo: market-tick-data-service).

## Progress Log

- **2026-08-20 — slot-7:** Read the Sports smoke plan, parent smoke contract, availability-manifest SSOT, Sports floor
  SSOT, and canonical work-list generator. Launched driver
  `pipeline-e2e-check-mtds-20260820-195837-4dd553` with test-bucket writes only. Measured 252 driver shards versus the
  39-row generator denominator; first child exited 0 while logging `No active venues`, and the MTDS canonical leg is
  explicitly skipped for Sports. Declared blocker `BLK-b463fb0b`; operator ruling requested before further launches.

- **2026-08-20 — slot-18:** Shipped `market-tick-data-service@70d0c7ed`, adding the Sports writer-template canonical
  verifier and regression tests. Ran the canonical-only verifier against the actual test bucket for
  `SPORTS:PINNACLE:odds` on `2025-12-20`; test-bucket consolidation succeeded (`shards=1 rows_in=1200 rows_out=1200`),
  but no matching `data_type=odds` object existed, so the report returned
  `canonical_no_matching_objects_in_test_bucket` with `status=failed`, proving the zero-object fail-closed gate.


- **2026-08-20 — slot-18:** Final scoped quickmerge landed on LDR as `market-tick-data-service@01745226fa`; full QG passed with 11,102 tests passed, 28 skipped, 1 xpassed, and 19 warnings.
