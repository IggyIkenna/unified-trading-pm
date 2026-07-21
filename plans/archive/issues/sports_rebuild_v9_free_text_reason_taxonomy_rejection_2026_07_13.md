---
doc_type: issue
title:
  rebuild_sports_manifest_v9.py silently fails to re-write ~35K+ IS rows carrying legacy free-text EMPTY reason strings
summary: >
  Live during a real production --apply of rebuild_sports_manifest_v9.py --surface instruments (slot 3, this session),
  observed a large, sustained stream of "record_empty failed ... is not in the closed-set EMPTY_CONFIRMED_REASONS
  taxonomy" warnings. Root cause: several historical touches (2026-06-28, 2026-06-29, 2026-07-13) wrote free-text
  suffixed reason strings (e.g. EXPECTED_NO_FIXTURE__truthset_20260628_confirms_no_fixtures) directly into the manifest
  instead of the bare canonical EXPECTED_NO_FIXTURE. The rebuild script's classifier treats any
  already-EXPECTED_*-prefixed reason as "keep_typed" (safe, re-emit as-is) — but the writer's record_empty() validates
  against the CURRENT closed-set taxonomy and rejects these free-text variants, catching the exception and silently
  skipping the row (no crash, no written_empty increment). Net effect: this CF-8 available_at backfill pass will NOT
  actually update these rows — they keep their pre-rebuild (missing available_at) state — while the overall run still
  reports success.
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [sports, manifest, data-correctness, taxonomy, cf-8, big-finding]
related: [plans/active/sports_manifest_canonicalisation_2026_06_01.md]
created: 2026-07-13
parent_epic: sports_master
priority: P1
source:
  Observed live during slot 3's --surface instruments --force --no-dry-run apply (this session, 2026-07-13T21:15Z),
  cross-referenced against my own --surface instruments --dry-run run's histogram (data_engineering slot 6, task
  sports_manifest_canonicalisation-001)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-20
locked_by:
resolved_by: market-tick-data-service@52c695d5
---

# rebuild_sports_manifest_v9.py silently under-delivers on rows with legacy free-text EMPTY reasons

## What I found

While dispatched to `sports_manifest_canonicalisation-001` (E8 Verify / CF-8 backfill todo), found slot 3 already
mid-`--apply` on the IS surface (`--surface instruments --project-id central-element-323112 --force --no-dry-run`, PID
1995687, started ~21:08:18Z, both sports manifest-consolidator crons coordinated-paused at 21:06:18-19Z). Deferred my
own IS work to avoid duplication, ran my own `--dry-run` on IS (informational) and `--dry-run` on MDPS (the
non-overlapping surface) instead.

**My IS dry-run's reason-relabel histogram flagged 4 categories kept `(unchanged)` — meaning the classifier treats them
as already-safe-to-re-emit-as-is**:

```
EXPECTED_NO_FIXTURE__truthset_20260628_confirms_no_fixtures: 30183 (unchanged)
EXPECTED_NO_FIXTURE__truthset_20260713-142756: 53 (unchanged)
EXPECTED_NO_FIXTURE__truthset_20260713-142830: 4441 (unchanged)
EXPECTED_NO_FIXTURE__truthset_20260713-172514: 684 (unchanged)
```

**Total: 35,361 rows.**

**Live-observed in slot 3's actual `--apply` run** (tailed its stdout via `/proc/1995687/fd/1`): a sustained stream of
warnings exactly matching these 4 reason strings, e.g.:

```
WARNING record_empty failed for row_key={'date': '2025-07-27', 'venue': '', 'league_id': 'DANISH_CUP', 'data_type':
'FIXTURES', 'instrument_type': ''}: record_empty(reason='EXPECTED_NO_FIXTURE__truthset_20260628_confirms_no_fixtures')
is not in the closed-set EMPTY_CONFIRMED_REASONS taxonomy. Allowed: [...36 canonical reasons, none of which include
any __truthset_* suffix variant...]
```

Confirmed dozens of distinct `league_id` values across many different dates hitting this same rejection — consistent
with the full 35,361-row scope from my dry-run histogram, not an isolated glitch.

**Root cause** (read `market_tick_data_service/scripts/_rebuild_sports_write.py:220-242`): the classifier's `not force`
branch treats ANY reason starting with `EXPECTED_` (except `EXPECTED_DEPRECATED_DATA_TYPE`) as `skip`/`keep_typed` —
correct in spirit (don't clobber an already-typed row) — but the actual write attempt still calls
`writer.record_empty(reason=new_reason, ...)` with that SAME free-text string, and `record_empty()`'s taxonomy
validation (added independently, presumably after these free-text reasons were written by earlier one-off scripts on
2026-06-28/06-29/07-13) rejects it. The `except Exception` wrapper (line 241-242) catches this, logs a WARNING, and
moves on — `written_empty` is never incremented for these rows, so they are silently absent from the new per-VM shard.

## Why it matters

- **Not data loss**: since the rebuild writes a NEW per-VM shard (not the canonical index directly) and these 35,361
  rows simply never appear in it, the eventual consolidator merge falls back to whatever's already in the canonical
  index for those row_keys — i.e. their PRE-rebuild state persists unchanged. No row disappears or gets corrupted.
- **Real under-delivery**: this run's entire purpose is the CF-8 `available_at` backfill. These 35,361 IS rows will NOT
  receive that fix in this pass, despite the run completing without a crash and (presumably) reporting overall success —
  a classic "green but incomplete" outcome the kind CLAUDE.md's honest-absence discipline exists to prevent. Whoever
  reviews slot 3's completion and reassesses the CF-8 gate needs to know this ~35K-row residual exists, or the plan's E8
  verdict could be marked GREEN prematurely.
- **Scope is probably wider than the 4 known variants**: this issue doc's own quantification is limited to the exact
  suffix patterns visible in my dry-run's histogram at the time I ran it (2026-07-13T21:14Z). Any OTHER free-text reason
  variant written by a different one-off script (this plan's Progress Log documents at least 3-4 separate historical
  touches that wrote custom `flipped_*`/`__truthset_*` suffixed reasons) could hit the same rejection and isn't
  necessarily enumerated here — a full grep of the manifest's distinct `reason` values against the canonical
  `EMPTY_CONFIRMED_REASONS` set would give the true total.
- **MDPS surface unaffected by this specific finding**: my MDPS dry-run's histogram showed zero free-text/custom reason
  categories (only `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE`, `EXPECTED_PAUSED_LEAGUE`, `SOURCE_RETURNED_ZERO`, all
  canonical) — this class of problem appears IS-surface-specific, consistent with IS being the surface that received the
  multiple truthset-reconciliation one-off scripts referenced in the plan's Progress Log.

## Confirmed against the completed run's own summary

Slot 3's `--apply` completed at 2026-07-13T21:18:10Z (`elapsed_s: 620.3`):
`DONE: written_empty=3570213 written_attempted_failed(CF11)=18324 written_captured=1212196 reemit_attempted_failed(v9)=3281 skipped=0 passthrough_expected=0 (force=True projection=False)`.

Reconciling against my dry-run's pre-apply counts: `empty_confirmed=3,623,898` minus the `18,324` rows upgraded to
`attempted_failed` via CF-11 (written via `record_failed`, not `record_empty`) = `3,605,574` expected `record_empty`
writes. Actual `written_empty=3,570,213` — a gap of **exactly 35,361**, matching this doc's dry-run-derived total to the
row. The run's own `DONE` summary line does not surface this gap anywhere (no `skipped_taxonomy_rejected` counter
exists) — confirming this is a genuinely silent under-delivery, not something slot 3 (or anyone reviewing the `DONE`
line alone) would necessarily notice without reading the WARNING-level log stream in full.

## What I did NOT do

Did not attempt to kill or interrupt slot 3's in-flight `--apply` process — it is not silently corrupting data (bounded,
understood failure mode: skip + old-row-persists, not data loss), so there is no emergency justifying interrupting
another slot's live production write without clear authority. Did not attempt a live patch to
`_rebuild_sports_write.py`'s exception handling mid-run (would require restarting the apply anyway, and the current run
should be allowed to finish and reconcile what it CAN fix cleanly). Did not enumerate the full universe of free-text
reason variants beyond what my dry-run histogram already surfaced — that full audit is the recommended follow-up todo
below.

## Recommended decision

Two sequenced follow-ups, both concrete (not ambiguous operator calls):

1. Once slot 3's current IS `--apply` completes and the consolidator is force-merged + cron resumed, run a **full
   audit** of the IS surface's distinct `reason` values against the canonical `EMPTY_CONFIRMED_REASONS` set (single read
   of the consolidated index, group-by `reason`, diff against the closed-set list) to get the TRUE total affected-row
   count (this doc's 35,361 is a lower bound from one dry-run snapshot).
2. Build a narrowly-scoped companion script (same pattern as the 25th/26th touches' targeted fix scripts, NOT a second
   full-surface `rebuild_sports_manifest_v9.py --force` run) that re-emits ONLY the affected rows with the STRIPPED
   canonical reason (`EXPECTED_NO_FIXTURE__truthset_YYYYMMDD*` → `EXPECTED_NO_FIXTURE`, etc.) via the same
   `record_empty()` + `available_at` plumbing this session's rebuild already uses correctly for canonical reasons.

## Todos

- [x] ✅ [DATA] P1. After slot 3's current IS `--apply` + consolidator force-merge completes: run a full
      distinct-`reason` audit against `EMPTY_CONFIRMED_REASONS` on the IS surface to get the true affected-row count
      (this doc's 35,361 is a lower bound). (repo: market-tick-data-service) — `market-tick-data-service@52c695d5`
- [x] ✅ [DATA] P1. Build a narrowly-scoped companion script to re-emit the affected rows with the canonical reason
      (strip the free-text `__truthset_*`/`flipped_*` suffix) + `available_at`, closing the residual CF-8 gap this
      rebuild pass could not close for these rows. (repo: market-tick-data-service) —
      `market-tick-data-service@444c8dd8`
- [x] ✅ [DATA] P2. Consider whether `_rebuild_sports_write.py`'s `not force` skip-condition should also validate the
      existing reason is in the closed-set taxonomy (not just that it starts with `EXPECTED_`) — a reason failing that
      check should be treated as "needs relabel" (route through the oracle), not "keep_typed", closing this class of gap
      at the source for any future rebuild run. (repo: market-tick-data-service) — `market-tick-data-service@d936444d`.
      Found the actual gap lives in `rebuild_sports_manifest_v9.py::_classify_empty_row` STEP 3 (not
      `_rebuild_sports_write.py`, which only has a _secondary_ `not force` skip-check downstream of the classifier) —
      its blanket `existing_reason.startswith("EXPECTED_")` check preserved non-canonical suffixed variants (e.g.
      `EXPECTED_NO_FIXTURE__truthset_20260713-142830`) verbatim regardless of `--force`. Now gated on
      `_validate_reason()` (previously defined, never called) — a look-alike falls through to the oracle (steps 4-8)
      instead of `keep_typed`. Added 2 regression tests (canonical-preserved + noncanonical-routes-through-oracle), all
      40 tests in `test_rebuild_sports_manifest_v9.py` pass.

## Progress Log

**Full distinct-`reason` audit — 2026-07-13 (data_engineering slot 5, task
`sports_rebuild_v9_free_text_reason_taxonomy_rejection-001`)**: verified prereq first — confirmed slot 3's IS `--apply`
completed (21:18:10Z) AND the consolidator `--force` merge subsequently ran to completion (canonical
`_index/availability_index.parquet` `last_modified` advanced 21:06:41Z (stale, pre-apply) → 21:34:41Z (86MB → 101MB),
process exit confirmed dead) before running anything — did not audit against a stale pre-merge index.

Shipped `market-tick-data-service/scripts/audit_sports_is_empty_confirmed_reason_taxonomy_2026_07_13.py` (single read of
the consolidated index via `get_storage_client().download_bytes()` — no whole-corpus GCS walk, single-walk discipline;
groups `capture_status="empty_confirmed"` rows by `error_reason`, diffs against
`unified_api_contracts.EMPTY_CONFIRMED_REASONS`).

**Result: 43,032 rows carry a taxonomy-rejected `error_reason`** (this doc's 35,361 dry-run estimate was confirmed as a
genuine lower bound — the true total is higher). 5 distinct non-canonical reason values, not 4:

```
EXPECTED_NO_FIXTURE__truthset_20260628_confirms_no_fixtures                 30183 rows
flipped_via_recover_fixtures_from_truthset_20260628-230236__truth_says_empty 7671 rows  <- NEW, not in original estimate
EXPECTED_NO_FIXTURE__truthset_20260713-142830                                4441 rows
EXPECTED_NO_FIXTURE__truthset_20260713-172514                                 684 rows
EXPECTED_NO_FIXTURE__truthset_20260713-142756                                  53 rows
```

The 5th variant (`flipped_via_recover_fixtures_from_truthset_20260628-230236__truth_says_empty`) confirms this doc's own
"scope is probably wider than the 4 known variants" caveat — traced to a `2026-06-28` one-off fixture-recovery touch not
covered by the original dry-run histogram. Audit result parquet also written to
`gs://instruments-store-sports-prd-central-element-323112/_index/audit/sports_is_empty_confirmed_reason_taxonomy_2026_07_13.parquet`
for the next todo (the companion re-emit script) to consume directly rather than re-deriving. Evidence:
`market-tick-data-service@52c695d5`.

**Next todo (P1, unclaimed)** should target these 5 reason strings (read from the audit parquet above, not hardcoded) —
the companion re-emit script's row-count target is 43,032, not the original 35,361.

**Companion re-emit script — 2026-07-13 (data_engineering slot 6, task
`sports_rebuild_v9_free_text_reason_taxonomy_rejection-002`)**: shipped
`market-tick-data-service/scripts/fix_sports_free_text_empty_reasons_2026_07_13.py` — a narrow companion (not a second
full-surface `rebuild_sports_manifest_v9.py --force` run) that scans `empty_confirmed` rows for a non-closed-set
`error_reason`/`reason` and, when resolvable, re-emits via the same `record_empty()` + `available_at` plumbing the
rebuild uses for canonical reasons (row-key building, league_id canonicalisation, source→pipeline_mode resolution —
imported from `rebuild_sports_manifest_v9`/`_rebuild_sports_write`, never duplicated).

Read the prior Progress Log entry's audit result (43,032 rows, 5 distinct reason strings) BEFORE finalizing the
stripping logic — an initial `EXPECTED_*__<suffix>` → split-on-`__` implementation only covers 4 of the 5 variants
(35,361 rows); the 5th (`flipped_via_recover_fixtures_from_truthset*__truth_says_empty`, 7,671 rows) has a non-canonical
prefix that a bare split would leave unresolved. Added a second branch mirroring
`rebuild_sports_manifest_v9._classify_empty_row` step 2 (imports `_FREE_TEXT_TRUTHSET_PREFIX` rather than redefining
it): any reason with that prefix → `EXPECTED_NO_FIXTURE`, closing the full 43,032-row residual, not just the
`EXPECTED_*`-prefixed subset. 10 unit tests cover both families + the genuinely-unresolved case (reported, not guessed
at). `quality-gates.sh` full green (host QG concurrency governor — `IGNORE_TIMEOUT=true` used to bypass the wall-clock
gate inflated by the shared-host governor queue wait, not by actual test/lint time).

Did not execute `--no-dry-run` against production in this task — the script is VM-run, after-slot-3's-apply is already
satisfied, but the actual re-emit apply is left to whoever picks up verification (dry-run first, per the script's own
usage docs). Evidence: `market-tick-data-service@444c8dd8`.
