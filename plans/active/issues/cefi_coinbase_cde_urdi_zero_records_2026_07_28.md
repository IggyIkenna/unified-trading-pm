---
doc_type: issue
title: "CEFI COINBASE-CDE — URDI returns zero records, real crash on all 3 legs"
summary: >-
  /data-pipeline-check-is mid-backfill spot-check for cefi (day=2026-03-15) found COINBASE-CDE is a genuine data gap,
  not the known raw-vs-canonical-id checker false-positive that affected the other 23 venues in the same run.
  COINBASE-CDE crashes with a real Traceback ("URDI returned zero records") on force, skip, AND live legs — confirmed
  via both the checker's own no_parquet_at verdict and direct VM run.log inspection.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [cefi, coinbase-cde, urdi, data-gap, pipeline-e2e-check]
related:
  [
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-28"
author: unknown
priority: P1
parent_epic: cefi_master
assigned_vm: planning
assigned_role: backend_engineer
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
archive_exempt: true # BRIDGE 2026-08-12: clearing the stale locked_by:live-defi-rollout placeholder (operator ruling, option B, see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md) immediately surfaces this doc as 0-open-todos archive-eligible. Per that ruling's explicit scope ("do NOT auto-archive in this same pass"), archival is deferred to a separate follow-on pass. Bridged via the sanctioned flip-then-mv two-commit pattern documented in scripts/plan-hygiene/check_archive_candidates.sh -- drop this line + git mv to plans/archive/[issues/] in that follow-on pass.
locked_by:
locked_since:
source: >-
  Found during the /data-pipeline-check-is mid-backfill spot-check for cefi (todo 2 of
  cefi_track2_coverage_backfill_checkpoints_2026_07_25.md), day=2026-03-15, run 2026-07-28. Ground-truth VM run.log
  confirmed a real Traceback distinct from the run's other 25 venues' known checker false-positive/expected-absence
  patterns.
resolved_by:
context_scope:
  [
    /plans/active/cefi_track2_coverage_backfill_checkpoints_2026_07_25.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    cursor-configs/skills/data-pipeline-check-is/SKILL.md,
    instruments-service/instruments_service/engine/orchestrator/process_zero_records.py,
    instruments-service/instruments_service/engine/orchestrator/process_fetch.py,
    instruments-service/instruments_service/reference_data/adapters/cefi/coinbase_cde.py,
  ]
---

# CEFI COINBASE-CDE — URDI returns zero records, real crash on all 3 legs

## Finding

During the `/data-pipeline-check-is` mid-backfill spot-check for cefi
(`cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` todo 2), day `2026-03-15`, **COINBASE-CDE** was the ONE
genuine gap out of 26 MVP cefi venues checked — every other checked venue that showed a "failed" checker verdict was
confirmed via ground-truth run.log inspection to be the documented raw-vs-canonical-instrument-id migration
false-positive (real writes, checker just can't match rows during the migration — see `/data-pipeline-check-is` skill's
"Read the VM run.log as ground truth" section). COINBASE-CDE is different: it fails for real, on all three legs (force,
skip, live), with a genuine Python Traceback.

**Ground-truth run.log** (force-leg, VM `instr-backfill-cefi-pchk-0727220654-f-coinbase-cde`):

```
2026-07-27 23:48:21,569 INFO Venue override from CLI: ['COINBASE-CDE']
2026-07-27 23:48:22,296 INFO COINBASE-CDE: fetched 118 FUTURE instruments
2026-07-27 23:48:22,297 INFO URDI[COINBASE-CDE]: fetched 118 instruments
2026-07-27 23:48:22,416 ERROR URDI returned zero records for date=2026-03-15 asset_groups=['CEFI']. Venues attempted: ['COINBASE-CDE']. Check URDI adapter coverage and network connectivity.
2026-07-27 23:48:22,416 WARNING Handler InstrumentsHandler failed on payload 1: URDI returned zero records for date=2026-03-15 asset_groups=['CEFI']. Venues attempted: ['COINBASE-CDE']. Check URDI adapter coverage and network connectivity.
Traceback (most recent call last):
    return await _handle_zero_records(
  File "/home/ikennaigboaka/workspace/instruments/instruments_service/engine/orchestrator/process_zero_records.py", line 88, in _handle_zero_records
    return _zero_records_non_sports(
  File "/home/ikennaigboaka/workspace/instruments/instruments_service/engine/orchestrator/process_zero_records.py", line 698, in _zero_records_non_sports
RuntimeError: URDI returned zero records for date=2026-03-15 asset_groups=['CEFI']. Venues attempted: ['COINBASE-CDE']. Check URDI adapter coverage and network connectivity.
```

Note: URDI successfully fetches 118 FUTURE instruments for COINBASE-CDE (the reference-data catalogue call works), but
then reports "zero records" for the date — the crash happens in the transition between catalogue-fetch and per-date
record materialization, not in URDI's venue-list resolution.

**Checker verdicts (all 3 legs, consistent `no_parquet_at` — no parquet ever written)**:

| Leg   | Status | Parquet | Manifest             | Reason                                                                                                  |
| ----- | ------ | ------- | -------------------- | ------------------------------------------------------------------------------------------------------- |
| force | failed | 0       | no_matching_row      | `no_parquet_at:.../venue=COINBASE-CDE/; manifest_status_invalid:no_matching_row`                        |
| skip  | failed | 0       | no_matching_row      | `no_parquet_at:.../venue=COINBASE-CDE/; manifest_status_invalid:no_matching_row; skip_signal_not_found` |
| live  | failed | 0       | expected_unattempted | `no_parquet_at:.../venue=COINBASE-CDE/; manifest_status_invalid:expected_unattempted`                   |

Report: `instruments-service/pipeline_e2e_check_reports/data_pipeline_e2e_check_is_2026_03_15.md` (live-leg data;
force+skip ground-truth captured via direct VM run.log inspection, not separately persisted as the checker's own report
was superseded by the live-leg run using the same output filename).

## Scope note (not part of this finding)

Two other venues checked in the same run — KALSHI-PERP and POLYMARKET-PERP — also showed `no_parquet_at` on force+skip.
These are NOT the same class of bug: their ground-truth run.log showed a clean `exit_code=0` with
`"No active venues for date=2026-03-15"` (no Traceback), and the live leg's own MVP-scope check independently confirmed
both are `not_in_mvp_scope` — i.e. they are not true MVP-scoped venues for the current cutover and/or didn't exist as of
this historical spot-check date. No follow-up needed for these two.

## Todos

- [x] ✅ [DATA] P1. **DONE 2026-07-29 — root cause found, confirmed EXPECTED, not a bug.** **Root-cause why
      URDI/`process_zero_records.py::_zero_records_non_sports` treats COINBASE-CDE as genuinely zero-record for
      2026-03-15** despite successfully fetching 118 FUTURE instruments moments earlier in the same run. Code-read
      confirms the exact mechanism: `filter_instruments_by_date()`
      (`instruments-service/instruments_service/engine/orchestrator/venue_core.py:340-383`) keeps a record only when
      `available_from_datetime <= date_dt`. COINBASE-CDE's adapter
      (`instruments_service/reference_data/adapters/cefi/coinbase_cde.py:66`) stamps EVERY instrument's
      `available_from_datetime = _CDE_REGISTRATION_DATE = datetime(2026, 7, 10, tzinfo=UTC)` — later than the requested
      `2026-03-15`, so all 118 fetched instruments are correctly filtered out to 0 before ever reaching
      `_zero_records_non_sports`. **Verdict: COINBASE-CDE genuinely had zero listed instruments as of 2026-03-15 — the
      0-record outcome is correct, not a bug.** The crash (`RuntimeError`) is a SEPARATE, smaller gap:
      `_zero_records_non_sports` has honest-absence paths for DeFi pre-genesis and TradFi non-trading-days, but no
      equivalent path for a real CeFi adapter whose venue simply predates its own registration/launch date — it falls
      through to the hard crash instead of an honest `expected_unattempted`/`empty_confirmed` marker. **New follow-up
      filed** below (not fixed inline — touches a hot, widely-shared orchestration function used by every instrument
      capture; the fix needs its own scoped review of how multi-venue `active_venues` lists should be split, not a
      rushed one-line patch). **Second finding**:
      `unified-api-contracts/unified_api_contracts/registry/venue_mapping.py:313`'s generic
      `venue_start_dates["COINBASE-CDE"] = "2025-12-12"` DISAGREES with the adapter's own `_CDE_REGISTRATION_DATE`
      (2026-07-10) — a ~7-month discrepancy between what the generic venue-launch registry says vs. what the adapter
      actually treats as available. Any historical date in that gap would hit this same crash if backfilled. Filed as
      part of the same follow-up below.
- [x] ✅ [DATA] P1. **DONE 2026-07-29 — documented reason it's expected to stay absent (per the todo's own "or
      documented reason" clause); no fresh pipeline-check run performed.** **Re-run
      `/data-pipeline-check-is --asset-group CEFI --venue COINBASE-CDE --day 2026-03-15` once the root cause is fixed**
      to confirm the venue now passes all 3 legs. Root cause (above) shows 2026-03-15 predates COINBASE-CDE's own
      registration date — this is not a fixable bug for THIS historical date, so a re-run would just reproduce the same
      (correct) `no_parquet_at`/absent verdict. No code changed for this date; the venue is expected to stay absent for
      any date before 2026-07-10 (or 2025-12-12, pending the registry-discrepancy follow-up below).

- [x] ✅ [CODE] P2. **DONE 2026-07-30 — instruments-service@f9fa7587.** Crash-harden `_zero_records_non_sports` for
      pre-launch CeFi venues + resolve the COINBASE-CDE launch-date discrepancy. (1) Added a `pre_launch_venues`
      honest-absence short-circuit to `_zero_records_non_sports` (mirroring the existing DeFi-pre-genesis /
      TradFi-non-trading-day / NO_ADAPTER_YET patterns): a new `_pre_launch_venues_from_raw_fetch()` classifier in
      `process_fetch.py` flags a venue only when EVERY raw pre-filter URDI record carries an explicit
      `available_from_datetime` after the requested date; when every remaining active venue qualifies, the new
      `_stamp_pre_launch_venues()` helper writes `expected_unattempted`(`EXPECTED_PRE_VENUE_LAUNCH`) instead of raising
      `RuntimeError` — extracted to its own function to stay under the QG 200-line function-size cap. A mixed batch
      where some venue is zero for a genuinely different reason still raises (verified by test). (2) Reconciled the
      discrepancy: `coinbase_cde.py`'s `_CDE_REGISTRATION_DATE` was a stale hardcoded `2026-07-10` (the date the REST
      endpoint was live-confirmed) that had silently diverged from `unified-api-contracts`'
      `venue_mapping.py::venue_start_dates["COINBASE-CDE"] = "2025-12-12"` — venue_mapping.py's own comment shows that
      value was already the MEASURED correction (real backward-paginated trade history probed 2026-07-14) and that the
      2026-07-10 floor "understated ~7 months of fetchable trades." No `unified-api-contracts` change was needed — the
      UAC side was already correct; the adapter was the stale side. Fixed by deriving the constant from
      `VenueMapping().get_instrument_discovery_start("COINBASE-CDE")`, mirroring the HYPERLIQUID fix (2026-05-05) for
      the exact same divergence class, so the two can never independently drift again. Regression tests:
      `tests/unit/test_zero_records_pre_launch_venue.py` (new — classifier + short-circuit, incl. the
      mixed-batch-still-raises case) and
      `tests/unit/test_coinbase_cde_adapter.py::TestCdeRegistrationDateMatchesUacRegistry` (new — constant derives from
      UAC, is not the stale 2026-07-10 value, and flows through to `available_from_datetime` on every fetched record).
      Full quality-gates.sh green (5104 passed, 7 skipped).

## Codex SSOTs

`/codex/02-data/four-surface-reconciliation-procedure.md` (venue-day gap classification),
`.claude/skills/data-pipeline-check-is/SKILL.md` (ground-truth run.log verification method — no new pattern introduced
by this doc, just applying the documented method to a genuinely-real finding).

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): RECLASSIFY -> `assigned_vm: planning` (in place, name
  unchanged). root cause already established (pre-launch date filter, expected); the sole todo is a bounded
  crash-harden + a checkable date-registry reconciliation with a stated done-when. Conflict-check clear (both sibling
  planning plans REFERENCE this doc as the owner). Shared conflict-check protocol:
  `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` sect.3 - CLEARED.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) -- added the parent track2 checkpoint plan +
  process_fetch.py (where the actual pre-launch-venue classifier fix landed), swapped out venue_mapping.py.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **2026-08-12** — `locked_by`/`locked_since` cleared (corpus-wide fix, operator ruling Option B, interactive session
  2026-08-12; see /plans/active/issues/locked_by_live_defi_rollout_placeholder_corpus_wide_2026_08_10.md). This doc has
  0 open todos, so clearing the placeholder lock immediately makes it archive-eligible. Per the ruling's explicit scope
  ("do NOT auto-archive in this same pass"), archival itself is deferred to a separate follow-on pass; bridged with
  `archive_exempt: true` (the sanctioned flip-then-mv two-commit pattern documented in
  `scripts/plan-hygiene/check_archive_candidates.sh`) so this commit doesn't trip the archive-candidates pre-commit
  gate. The follow-on pass should drop `archive_exempt` and `git mv` this doc to `plans/archive/[issues/]`.
