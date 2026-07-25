---
doc_type: issue
title:
  record_expected_empty() never stamped source= — calendar-skip manifest rows invisible to source-filtered gate queries
  across weather/SFI/understat/footystats
summary:
  "ManifestWriter.record_expected_empty() (unified-trading-library) never accepted or forwarded a source kwarg to
  record_empty(), so every calendar-pre-skip / coverage-start-guard / season-window-guard write across 18 callsites in 6
  instruments-service orchestrator modules landed with a blank source. Confirmed via a live reproduction: the
  understat_eu_residual_closer_2026_07_08.py script wrote ~7,553 correctly-typed rows for the item #4 residual, but they
  landed with source='' instead of source='understat' — invisible to every source=='understat' filtered gate query used
  throughout sports_p2_history_reference_and_odds_2015_to_present, making 3 consecutive slot sessions' worth of
  diagnosis (2026-07-08) believe the fix wasn't working when it actually was."
status: open
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-library, instruments-service]
scope: [engineer, admin]
tags: [sports, manifest, data-correctness, honest-absence, source-provenance, expected-unattempted, instruments]
related:
  [
    plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md,
    plans/active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md,
  ]
created: 2026-07-08
parent_epic: sports_master
priority: P0
source: [plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-08
---

## What I found

Dispatched to close item #4 (understat XG/XG_SHOTS zero-missing gate) of
`sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md`. Found slot-3's
`understat_eu_residual_closer_2026_07_08.py` (PID 3704218) already running live — a script that force-refetches the
1,169 blank-`error_reason` `expected_unattempted` dates and, for genuine non-matchdays, calls
`ManifestWriter.record_expected_empty(reason=<typed status>)` to convert them to a correctly-typed terminal state.

The process completed cleanly (`processed=1169 raised=0`), but re-verifying via the SAME `source=='understat'` filtered
query every prior slot session in this plan used (`/tmp/verify_understat_gate.py`) showed **zero change** — XG
`expected_unattempted` still exactly 250, XG_SHOTS still exactly 5,843, byte-for-byte identical to before the run.

Traced it to the actual GCS content
(`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`), bypassing the source
filter:

- **7,553 new rows** landed with `attempted_at` in the closer's run window (21:38–22:02 UTC 2026-07-08) — the writes DID
  happen and DID reach the canonical index (confirmed the manifest consolidator itself is healthy: transfermarkt and
  api_football writes from other concurrent VMs merged correctly in the same window).
- Every one of those 7,553 rows carries `source=''` (blank) instead of `source='understat'` — invisible to any
  `source=='understat'` filtered read, including the exact tooling this plan's last 3 sessions used to conclude "no
  change."
- The 250 XG + 5,843 XG*SHOTS original blank-\_reason* rows (`source='understat'`, unresolved) are UNTOUCHED —
  confirming the new typed rows did not even dedup-collide with them (a second, currently-unconfirmed anomaly — see
  "Open question" below).

**Root cause, confirmed by reading the code**: `ManifestWriter.record_expected_empty()`
(`unified-trading-library/unified_trading_library/manifest_writer/_writer_record.py`) is a thin wrapper over
`record_empty()`. `record_empty()` has accepted an optional `source: str | None = None` kwarg since CF-4
(`mtds_honest_absence_swallow_remediation_2026_06_10` Phase 2), but `record_expected_empty()`'s own signature never
exposed `source` at all and never forwarded one to its `record_empty()` call — so **every** calendar-pre-skip write
through this method was permanently `source=""`, regardless of what the caller intended.

`grep -rn "record_expected_empty(" instruments_service/engine/orchestrator/*.py` finds **18 callsites across 6 files**,
none of which set `row_key["source"]` either (there'd be nowhere for it to go pre-fix anyway):

| File                      | Callsite lines     | Fixed this session? |
| ------------------------- | ------------------ | ------------------- |
| `understat.py`            | 104, 122, 413, 431 | ✅ yes              |
| `weather.py`              | 131, 149           | ❌ no               |
| `sfi.py`                  | 284, 291, 315      | ❌ no               |
| `footystats.py`           | 113, 131, 449, 467 | ❌ no               |
| `process_write.py`        | 441, 487, 786      | ❌ no               |
| `process_completeness.py` | 486                | ❌ no               |
| `process_zero_records.py` | 528                | ❌ no               |

## Why it matters

1. **Directly blocked item #4 for 3+ slot sessions.** Every "gate re-verified, still FAIL" note in the plan's Progress
   Log since 2026-07-08 20:10 UTC (slot-7, slot-5, slot-14, slot-2, slot-3) queried via `source=='understat'` and would
   have seen this exact blindness — none of them were wrong about the gate still failing (the OLD rows really are
   unresolved), but the diagnosis chain never had a way to see that force-refetch writes for typed non-matchdays WERE
   landing, just invisibly.
2. **Weather (item #1) and SFI (item #2) are ALREADY flipped ✅ in this same plan** based on gate verification passes
   that likely used the same `source==<X>` filtering convention. If any of THEIR calendar-pre-skip writes (the exact
   code path this bug lives in) also landed blank-sourced, their reported `pending_fetch=0` / captured counts could be
   undercounting real state. **This needs independent re-verification** — I did not have scope to check weather/SFI's
   historical gate-verification queries in this session.
3. **Cross-cutting**: `process_write.py` / `process_completeness.py` / `process_zero_records.py` are NOT sports-only
   modules — the same blank-source gap likely affects every other asset_group whose orchestrator calls
   `record_expected_empty()` on a calendar-pre-skip path, not just the 4 sports sources named above. Scope was not
   audited beyond `instruments-service` in this session.

## What I already fixed (this session)

- `unified-trading-library@192b2836` — added `source: str | None = None` (+`asset_group: str = ""`) passthrough to
  `record_expected_empty()`, mirroring `record_empty()`'s existing parameter. Backward compatible (both default to the
  pre-fix blank behaviour when omitted).
- `instruments-service@5fc535e` — updated all 4 `understat.py` callsites to pass
  `source=_sports_ref_source("understat_xg" | "understat_xg_shots")` (the same helper already used at the
  `record_captured` callsites in the same file, guaranteeing the value matches UAC `SOURCE_PRIORITY`).
- Re-ran the residual closer (`understat-eu-residual-closer-20260708-v2`) with the fix live to confirm resolution before
  flipping item #4's checkbox — see the plan's Progress Log for the outcome.

## Open question — dedup non-collision — RESOLVED 2026-07-08 (slot-13): confirmed (b), escalated

Root-caused. Confirmed via a direct read of the persisted canonical `_index/availability_index.parquet` (bypassing the
reader's self-shard overlay entirely — a plain `pandas.read_parquet` against the GCS blob, so this reflects exactly what
the DuckDB consolidator itself wrote) that the OLD blank-reason `source='understat'` rows and the NEW correctly-typed
rows written by today's `understat-eu-residual-closer-20260708-v2` run DO coexist for byte-identical dedup keys — **9/15
sampled (date, data_type, league_id) cells have both rows present**, the newer one ~10 days more recent by
`attempted_at`/`written_at`. This is scenario **(b)**: a real, independent bug in the manifest consolidator's CAS-retry
path (NOT the DuckDB anti-join SQL itself, which is logically correct on inspection) — see the escalated issue doc for
the full root cause (a lost-update race in `_write_consolidated()`'s `PreconditionFailed` retry loop, which re-uploads a
stale already-computed merge instead of recomputing against the fresh canonical).

**Filed**: `plans/active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md` (P0, repo
unified-trading-library) with 4 actionable todos (fix the race, correct the misleading module docstring, re-verify this
doc's understat cells post-fix, audit other high-concurrency buckets for the same symptom).

## Recommended decision

- [x] ✅ [DATA] P0. Add `source=` at the 2 `weather.py` `record_expected_empty()` callsites (repo: instruments-service)
      — use the same source-resolution helper the file's `record_captured`/`record_empty` callsites already use for
      weather; re-verify weather's item #1 gate afterward since it's already flipped ✅ on possibly-blind data. —
      instruments-service@c09980b. Note: row_key already embedded `"source": "open_meteo"` for both callsites (commit
      8ad3b57, 2026-06-27, predates this issue) and `ManifestWriter._record_status` resolves
      `row_key["source"] or kwarg` with row_key winning, so these 2 writes were NOT actually blank-sourced — this change
      is a convention-consistency fix (top-level `source=` kwarg, matching understat.py + this file's own
      record_captured/record_empty callsites), not a correctness fix for these 2 sites specifically. Re-verification of
      item #1's gate is therefore not expected to change its result, but still worth a confirmatory pass per the
      recommended decision.
- [x] ✅ [DATA] P0. Add `source=` at the 3 `sfi.py` `record_expected_empty()` callsites (repo: instruments-service) —
      same pattern; re-verify SFI's item #2 gate afterward (already flipped ✅). — instruments-service@d6fff68. Added
      `source=_orch._sports_ref_source("progressive_stats")` as a top-level kwarg to all 3 callsites (lines 284, 291,
      315 — the coverage-start/known-gap guard and the season-window guard), matching this file's own `record_captured`
      callsite (L456) and the already-fixed understat.py/weather.py/footystats.py pattern; these had NO source in
      `row_key` pre-fix — genuinely blank-sourced writes, same correctness-fix class as footystats.py. Gate
      re-verification: already covered by the P1 unfiltered-vs-filtered re-verify item below — it found SFI's 31
      blank-source rows (pre-this-fix) were all `capture_status='empty_confirmed'`, none `expected_unattempted`, so item
      #2's `pending_fetch==0`-at-flip-time claim was not corrupted by this bug even before this fix landed; this fix
      closes the ongoing blank-source production going forward.
- [x] ✅ [DATA] P0. Add `source=` at the 4 `footystats.py` `record_expected_empty()` callsites (repo:
      instruments-service) — this may also close some fraction of item #5's PREDICTIONS/MATCHES residual (the
      cup-fixture-calendar gap slot-7 diagnosed 2026-07-08 20:10 UTC as a separate CODE gap — re-verify AFTER this fix
      lands whether that gap is smaller than currently measured, since the measurement itself may be source-blind). —
      instruments-service@31dbcc6. Unlike weather.py, these 4 callsites (2 PREDICTIONS coverage-start/season-window
      guards, 2 MATCHES coverage-start/season- window guards) had NO source in `row_key` pre-fix — genuinely
      blank-sourced writes, confirmed correctness fix (not a convention-only change). Added
      `source=_orch._sports_ref_source("footystats_predictions"|"footystats_matches")` as a top-level kwarg, matching
      this file's own `record_captured`/`record_empty` callsites. Re-verification of item #5's PREDICTIONS/MATCHES
      residual still needed per the recommended decision — not done in this session.
- [x] ✅ [DATA] P1. Audit `process_write.py` (3 callsites) / `process_completeness.py` (1) / `process_zero_records.py`
      (1) for the correct `source=` value per callsite (these are cross-asset-group, not sports-specific — needs a wider
      audit than this doc's sports scope covers) (repo: instruments-service). — instruments-service@e493e6d. All 5
      callsites (`_write_tradfi_non_trading_day_entries` L441, `_pre_stamp_non_trading_tradfi` L487,
      `_seed_expected_unattempted_for_target_universe` pre-launch branch L786 in `process_write.py`;
      `_finalize_completeness` L486 in `process_completeness.py`; `_zero_records_non_sports` L528 in
      `process_zero_records.py`) uniformly pass `pipeline_mode=BATCH_INSTRUMENTS_SERVICE` with row_keys carrying no
      `source` — genuinely blank-sourced (same correctness-fix class as footystats.py, not weather.py's convention-only
      case). Added `source=source_string_for(PipelineMode.BATCH_INSTRUMENTS_SERVICE)` == `"instruments_service"` at
      each, matching the C-#6 pipeline_mode⇔source contract already enforced for `record_captured` in this same file
      (`writers.py` / `_write_prediction_venue`). Root-cause note: see the new P0 finding below — a systemic
      library-level gap, not a per-callsite pattern, so this audit's scope (the 5 named callsites) is now closed but the
      class of bug is NOT fully closed until that finding resolves.
- [x] ✅ [DATA] P0. **Root-cause found during the audit above**: `ManifestWriter._record_status()`
      (`unified_trading_library/manifest_writer/_writer_record.py`, backs `record_empty`/`record_expected_empty`/
      `record_failed`/`record_expected_unattempted`) never calls `_stamp_producer_source()` — the helper
      `record_captured()` DOES call (`_writer_captured.py:263`, `:643`) that stamps a blank-resolved source with
      `source_string_for(pipeline_mode)` for any BATCH producer row. Because `_record_status` is missing this call,
      EVERY current and future `record_empty`/`record_expected_empty`/`record_failed`/`record_expected_unattempted`
      callsite across the ENTIRE codebase (not just sports or instruments-service) that passes a BATCH `pipeline_mode`
      without an explicit `source=` kwarg silently lands blank-sourced — the identical bug class this whole issue doc is
      about, just at its root instead of at each callsite. Fixing callsites one at a time (as this doc has done for
      understat/weather/footystats/process_write/process_completeness/process_zero_records) will never fully close this
      class — any NEW callsite added anywhere in the codebase reintroduces it by default. Fix: add
      `resolved_source = self._stamp_producer_source(resolved_source, resolved_pipeline_mode)` in `_record_status`
      (mirroring `_writer_captured.py`'s pattern), placed after the existing `explicit_source`/`default_source`
      resolution block and before `_assert_source_matches_pipeline_mode` (so the C-#6 cross-check's `explicit_source`
      semantics — "only an EXPLICITLY-provided source is policed" — are preserved; the stamp only fires when
      `resolved_source` is still blank). Needs its own test-impact review: this changes runtime behaviour for every
      non-captured row currently landing blank-sourced under a BATCH pipeline_mode with no `asset_group` kwarg — a
      repo-wide grep for existing tests asserting blank `source` on an
      `empty_confirmed`/`attempted_failed`/`expected_unattempted` row is needed before landing (repo:
      unified-trading-library). — unified-trading-library@ca5f1dbd. Added the
      `_stamp_producer_source(resolved_source, resolved_pipeline_mode)` call at the exact placement specified above.
      Test-impact review: `grep -rn '\.source == ""' tests/` across UTL found exactly 3 tests whose blank-stays-blank
      assertion used a BATCH pipeline_mode (all in `test_manifest_writer_source_noncaptured.py` — none in
      `test_manifest_writer_source.py` / `test_manifest_writer_transport.py`, both `record_captured`-only and already
      stamped pre-fix); switched those 3 to a non-batch (`LIVE_DATABENTO`) pipeline_mode so they keep testing the
      OPTIONAL-source contract instead of asserting now-incorrect blank output, and added 4 new tests covering the
      auto-stamp directly (incl. the literal `record_expected_empty` repro scenario and an explicit-source-wins
      regression guard). Full `quality-gates.sh` green (6309+ tests passed) before shipping via quickmerge.
- [x] ✅ [DATA] P1. Re-verify item #1 (weather) and item #2 (SFI) gate state in
      `sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` using an UNFILTERED-by-source query (or
      post-fix filtered query) to confirm their ✅ flips still hold (repo: unified-trading-pm, plan file). — Read the
      consolidated sports `availability_index` once (`read_availability_index`, shard-merged, single-walk-safe) and
      compared UNFILTERED vs `source==<X>`-filtered `capture_status` counts for both `(data_type=WEATHER)` and
      `(data_type=SFI_PROGRESSIVE_STATS)` (filtered by `data_type` only, not `venue` — many calendar-pre-skip row_keys
      omit `venue` entirely, so a venue-filtered query would itself be blind). **Weather: 0 blank-source rows out of
      263,103** (100% carry `source='open_meteo'`) — confirms the code-level finding (row_key already embedded `source`
      pre-fix) holds at the data level too; `pending_fetch` (`expected_unattempted`) UNFILTERED=264 == filtered=264,
      identical. **SFI: 31 blank-source rows out of 227,722** (confirms sfi.py's still-unfixed calendar-pre-skip path IS
      actively producing blank-sourced writes, as expected — the sfi.py fix todo above remains unchecked) — but all 31
      are `capture_status='empty_confirmed'` (a single batch, `attempted_at` 2026-07-07T13:49:57Z), none
      `expected_unattempted`; `pending_fetch` UNFILTERED=264 == filtered (`source=='soccer_football_info'`)=264,
      identical. **Conclusion: both items' ✅ flips hold w.r.t. THIS bug** — the source-blindness bug has not (yet, for
      SFI) produced any blank-sourced `expected_unattempted` rows that a filtered query would miss, so neither item's
      `pending_fetch==0`-at-flip-time claim (2026-06-27) was corrupted by it. Note: the CURRENT (2026-07-08) unfiltered
      `pending_fetch=264` for BOTH weather and SFI is NOT a new finding — it's the same already-documented
      drift-since-flip in the sibling plan's VERIFY item (daily-pipeline-lag hypothesis, "unverified this session,"
      2026-07-08 slot-7/slot-5) and is out of scope for this todo to re-diagnose. Full counts + Progress Log entry added
      to `plans/active/sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md`.
- [x] ✅ [DATA] P1. Root-cause the dedup non-collision question above — if the v2 closer re-run (this session) shows the
      old blank-reason rows STILL coexisting alongside new correctly-sourced rows, escalate as its own P0 issue
      targeting `unified_trading_library/manifest_consolidator.py`'s DuckDB incremental anti-join (repo:
      unified-trading-library). — unified-trading-pm (this doc + new issue doc, no code SHA). Confirmed (b): 9/15
      sampled cells show the OLD blank row and a NEW (~10-days-newer) correctly-typed row coexisting for a
      byte-identical dedup key. Root cause is NOT the DuckDB anti-join SQL (inspected, logically correct) but a
      lost-update race in `_write_consolidated()`'s CAS-retry loop, which re-uploads a stale already-computed merge on
      `PreconditionFailed` instead of recomputing. Filed
      `plans/active/issues/manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md` (P0) with the fix + 3
      follow-up todos.
- [x] ✅ [DATA] P0. **Fourth blank-source callsite found this session (2026-07-08, slot-4)**: the understat.py table
      above marked ALL 4 `record_expected_empty()` callsites fixed (`instruments-service@5fc535e`), but that fix did NOT
      cover the file's separate per-league **honest-absence** `record_empty()` calls (3 in `_fetch_understat_xg`'s "no
      fixtures this date" fallback paths, 1 in `_run_understat_shots_date`) — these still landed `source=''`, confirmed
      live via the understat-eu-residual-closer-20260708-v2 re-run (see plan Progress Log, 22:5x UTC entry). Fixed:
      `instruments-service@ffe7555`, added `source=_orch._sports_ref_source("understat_xg"|"understat_xg_shots")` to
      all 4. Reinforces the still-open P0 root-cause todo below (`_record_status()` missing `_stamp_producer_source()`)
      — this file alone needed 2 separate rounds of per-callsite patching (`record_expected_empty()` then
      `record_empty()`), exactly the whack-a-mole pattern that root fix would end.
