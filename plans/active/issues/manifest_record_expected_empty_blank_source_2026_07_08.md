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
assigned_vm: planning
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
- The 250 XG + 5,843 XG_SHOTS original blank-_reason_ rows (`source='understat'`, unresolved) are UNTOUCHED — confirming
  the new typed rows did not even dedup-collide with them (a second, currently-unconfirmed anomaly — see "Open question"
  below).

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

## Open question — dedup non-collision (unconfirmed, needs its own investigation)

The 7,553 blank-source rows and the 250+5,843 `source='understat'` blank-reason rows share the SAME
`(date, venue, data_type, service_name, league_id)` — the full dedup key per both
`unified_trading_library/manifest_consolidator.py::_resolve_dedup_cols` and the reader's `_merge_shard_frames` (`source`
is NOT part of either's dedup key). They should have collapsed to one row (newest `attempted_at` wins) — instead both
coexist in the canonical parquet. This is either (a) resolved by the source fix alone once the writer stops producing a
NEW distinct-looking row, or (b) a second, independent dedup bug in the DuckDB incremental anti-join merge. The re-run
in this session's Progress Log entry should disambiguate — if the v2 closer's rows correctly supersede the old
blank-reason rows, (a); if both still coexist, file (b) as its own P0 issue with the DuckDB merge SQL as the
investigation target.

## Recommended decision

- [ ] [DATA] P0. Add `source=` at the 2 `weather.py` `record_expected_empty()` callsites (repo: instruments-service) —
      use the same source-resolution helper the file's `record_captured`/`record_empty` callsites already use for
      weather; re-verify weather's item #1 gate afterward since it's already flipped ✅ on possibly-blind data.
- [ ] [DATA] P0. Add `source=` at the 3 `sfi.py` `record_expected_empty()` callsites (repo: instruments-service) — same
      pattern; re-verify SFI's item #2 gate afterward (already flipped ✅).
- [ ] [DATA] P0. Add `source=` at the 4 `footystats.py` `record_expected_empty()` callsites (repo: instruments-service)
      — this may also close some fraction of item #5's PREDICTIONS/MATCHES residual (the cup-fixture-calendar gap slot-7
      diagnosed 2026-07-08 20:10 UTC as a separate CODE gap — re-verify AFTER this fix lands whether that gap is smaller
      than currently measured, since the measurement itself may be source-blind).
- [ ] [DATA] P1. Audit `process_write.py` (3 callsites) / `process_completeness.py` (1) / `process_zero_records.py` (1)
      for the correct `source=` value per callsite (these are cross-asset-group, not sports-specific — needs a wider
      audit than this doc's sports scope covers) (repo: instruments-service).
- [ ] [DATA] P1. Re-verify item #1 (weather) and item #2 (SFI) gate state in
      `sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` using an UNFILTERED-by-source query (or
      post-fix filtered query) to confirm their ✅ flips still hold (repo: unified-trading-pm, plan file).
- [ ] [DATA] P1. Root-cause the dedup non-collision question above — if the v2 closer re-run (this session) shows the
      old blank-reason rows STILL coexisting alongside new correctly-sourced rows, escalate as its own P0 issue
      targeting `unified_trading_library/manifest_consolidator.py`'s DuckDB incremental anti-join (repo:
      unified-trading-library).
