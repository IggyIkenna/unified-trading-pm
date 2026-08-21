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
archive_exempt: true
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

- [x] [BACKEND] P0. Add a generator-scoped Sports execution mode to the MTDS pipeline checker that runs exactly the 39 rows emitted by the UAC work-list generator and reports observed out-of-registry cells separately (repo: market-tick-data-service; supporting contract: unified-api-contracts) — market-tick-data-service@aaa0c8b1b6; QG=11104 passed, 28 skipped, 1 xpassed, 19 warnings.
- [x] [BACKEND] P0. Implement and run a Sports canonical-path verification leg that checks the actual test-bucket
      object against the applicable UAC machine oracle or Sports writer template, and fails closed when no object/row is
      produced (repo: market-tick-data-service) — market-tick-data-service@01745226fa + QG=11102 passed, 28 skipped, 1 xpassed, 19 warnings; runtime report
      `data_pipeline_e2e_check_mtds_2025_12_20.md` (`canonical_no_matching_objects_in_test_bucket`, fail-closed).
- [x] [DATA] P1. Reconcile the 96 observed Sports `(venue, data_type)` cells absent from the UAC registry against the
      canonical venue/data-type declarations; classify derived/retired data types and accepted legacy/source-scoped
      observations without widening canonical bookmaker capabilities (repo: unified-api-contracts) — unified-api-contracts@a78f07dce0; QG=passed.
- [x] [BACKEND] P1. Preserve a per-unit result schema containing row count, canonical-path verdict, manifest shard-atom
      verdict, `capture_status`, source, and the exact no-active-venue/zero-row reason so an exit code of zero cannot be
      mistaken for a passing smoke test (repo: market-tick-data-service) — unified-trading-library@9325fe00d8 (adds
      `capture_status`/`source` to `ShardCheckResult`, round-tripped through JSON merge + rendered in the markdown
      table) + market-tick-data-service@f88dfdbd19 (always propagates capture_status/source from the manifest row,
      even on the failure path; surfaces the manifest's classified `error_reason` or, when no manifest row was ever
      written, greps the VM's `run.log` for the orchestrator's own exact "No active venues" line); full QG passed on
      both repos.

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
- **2026-08-20 — slot-7:** Shipped the generator-scoped Sports mode as `--generator-scoped-sports`; it loads exactly the 39 UAC work-list rows, preserves venue/data-type filters, and logs observed PROD cells outside the generator without widening the denominator. Quickmerge verified `market-tick-data-service@aaa0c8b1b6` on LDR; full QG passed with 11,104 tests passed, 28 skipped, 1 xpassed, and 19 warnings.

- **2026-08-21 — slot-10:** Reconciled the observed Sports registry gaps in `unified-api-contracts`: canonical bookmaker/data-type capabilities remain unchanged; derived/retired data types and accepted legacy, source-scoped, writer-residue, empty-residue, and cross-asset observations are classified explicitly. Full quality gates passed (tests, type check, Codex compliance); quickmerge landed the commit on LDR.

- **2026-08-21 — slot-7:** Closed the last open todo. Traced the finding to its root: `_verify_batch_shard`'s per-VM
  manifest read (`_read_per_vm_batch_row`) already resolved the unit's real `capture_status`/`error_reason` but
  discarded both on the failure path (only used inside the `write_verified` branch), and there was no path at all to
  surface the orchestrator's own diagnostic line for the genuine "no manifest row written" case (the exact
  `No active venues for date=... asset_groups=[...]` finding from 2026-08-20 above). Added `capture_status`/`source`
  as dedicated `ShardCheckResult` fields (`unified-trading-library@9325fe00d8`, additive/back-compat defaults, so
  every other `pipeline_e2e_check` caller — instruments-service, features-service, market-data-processing-service —
  is unaffected), then wired MTDS's batch verifier (`market-tick-data-service@f88dfdbd19`) to (1) always propagate
  capture_status/source from the per-VM manifest row regardless of write_verified, (2) append the manifest's own
  classified `error_reason` to `reason` when a row exists, and (3) grep the VM's `run.log` for the orchestrator's
  exact "No active venues" WARNING when no manifest row was ever written at all — closing the exact gap this issue's
  first finding identified (a zero-exit VM with `No active venues` in its log previously left no trace of that reason
  in the report). Full quality gates passed on both repos (UTL 129s, MTDS 43s via content-sentinel reuse of the
  genuine full run); both SHAs verified post-push ancestors of `origin/live-defi-rollout` via quickmerge's own
  ancestry check. Added/updated unit tests: UTL round-trips `capture_status`/`source` through the JSON merge path;
  MTDS covers the 3-tuple `_read_per_vm_batch_row` return shape, the new `_extract_no_active_venues_reason` grep
  helper, and `_verify_batch_shard`'s exact-reason surfacing on both the log-grep and manifest-error_reason paths.
  All four todos in this issue doc are now closed — archiving in a follow-up commit per the cross-repo
  flip-then-archive rule (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`); `archive_exempt:
  true` set on this flip-only commit as the sanctioned bridge, dropped in the immediately-following `git mv` commit.
