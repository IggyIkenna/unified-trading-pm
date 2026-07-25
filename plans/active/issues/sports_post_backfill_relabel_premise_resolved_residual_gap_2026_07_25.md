---
doc_type: issue
title:
  "sports_satellite_ao_dispatch_batch2-014's 789-league/120-date entity-coverage relabel premise is STALE (already
  resolved by intervening canonicalization work) — a much smaller, differently-shaped 33,905-row residual remains,
  needing its own targeted diagnosis, not the described migration"
summary: >-
  The dispatched todo (source: data_completion_sports_2026_07_24.md, itself dated from a 2026-06-22 finding) says the
  sports manifest carries ~1,027,396 `expected_unattempted` rows across 120 dates (2026-02-20→06-19) x 789 league_ids
  from a WEATHER-driven over-enumeration bug, and prescribes a relabel (no-coverage pairs -> expected_empty, GCS-backed
  cells -> captured) once 6 named backfill VMs go terminal. Live measurement today (2026-07-25) shows that finding is
  now STALE: only 33,905 expected_unattempted rows remain in that exact window, across 96 league_ids (not 789) - ALL 96
  of which are IN the current 94/96-league api_football in-universe set (zero out-of-universe leagues left in the
  window). The 30x reduction is a side effect of the intervening canonical-universe write-gate + dereg + canonicalize
  program (instruments-service@0345ffc and follow-ons, 2026-06-24 through 2026-07-21) - not something this todo's script
  needs to redo. The residual is dominated by odds_horizon_bucket (11,146, MDPS-owned) and
  FIXTURES_OUTCOMES/FIXTURES_SCHEDULE (9,265 + 9,256 = 18,521, the 2026-07-14+ split entities) - a structurally
  DIFFERENT shape (in-universe leagues with plausible genuine gaps, not out-of-universe phantoms) that a blind
  no-coverage->expected_empty relabel could mislabel as false-empty (the exact corruption class
  close_stale_enrichment_expected_unattempted_cells_2026_07_19.py's docstring warns against). Filed instead of running
  the stale-premise migration against a currently-live manifest writer.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [sports, honest-coverage, manifest, data-correctness, stale-finding, entity-coverage]
related:
  [
    /plans/active/data_completion_sports_2026_07_24.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency_2026_07_19.md,
  ]
created: 2026-07-25
priority: P2
parent_epic: sports_master
source:
  "Slot 9, data_engineering, 2026-07-25 — measured live against prod manifest while executing
  sports_satellite_ao_dispatch_batch2-014."
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# sports post-backfill entity-coverage relabel: premise resolved, residual needs its own diagnosis

## What I found

Dispatched task `sports_satellite_ao_dispatch_batch2-014` asked me to run a manifest relabel over "120 recent dates
(2026-02-20->06-19) x 789 leagues" per a 2026-06-22 finding (`data_completion_sports_2026_07_24.md` line 722-737): a
WEATHER-honest-coverage investigation found the sports `_index/availability_index.parquet` carried 1,027,396
`expected_unattempted` rows in that exact window across 789 league_ids (the enumerator over-expanded to the full raw
league universe instead of the ~57-94 leagues actually captured).

Before running the prescribed script, I measured the CURRENT manifest state directly (single read of
`_index/availability_index.parquet`, no new whole-corpus GCS walk):

- Total `expected_unattempted` rows workspace-wide: 249,338 (was ~1.03M+ in the window alone a month ago).
- Rows in the SAME 120-date window today: **33,905** (a ~30x reduction from the diagnosed 1,027,396).
- Distinct `league_id`s in that window subset today: **96** (not 789).
- **All 96 are in the current `get_expected_leagues_for_source("api_football")` in-universe set** — zero out-of-universe
  leagues remain in the window (the 94-league count is now 96 after CHINA_SUPER_LEAGUE/ RUSSIA_PREMIER_LEAGUE were added
  2026-07-21).
- Breakdown by `data_type` (top contributors): `odds_horizon_bucket` 11,146 (MDPS-owned, not IS); `FIXTURES_OUTCOMES`
  9,265; `FIXTURES_SCHEDULE` 9,256; `TEAMS` 1,758; the rest (WEATHER/STANDINGS/FIXTURES/SFI_PROGRESSIVE_STATS/
  INJURIES/FIXTURE_LINEUPS) 240 each; MATCHES/PREDICTIONS/ODDS 212 each; FIXTURE_STATS/FIXTURE_EVENTS 82 each.

This is NOT the bug the source finding described. The old bug's signature was "789 raw league_ids, mostly
out-of-universe, WEATHER-driven, ~1M rows." Today's residual signature is "96 in-universe league_ids, dominated by
`FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE` (the 2026-07-14+ entity-split), 34k rows." The most plausible read: the
2026-07-14 FIXTURES-schema split introduced a NEW enumerator-vs-writer-timing mismatch for PRE-cutover historical dates
(the enumerator now expects `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE` for every in-window date, but the writer only
started producing those entities going forward from the cutover, per `gcs_paths.py`'s own "NO legacy dual-write" note) —
not independently confirmed, flagged as the leading hypothesis for whoever picks this up.

**Additionally**: while measuring, I found a currently-RUNNING sports backfill VM (`af-backfill-20260725-002739`,
INJURIES/API_FOOTBALL/SPORTS, `days=1800` from 2018-01-01, currently ~2020-04) writing DIRECTLY to
`_index/availability_index.parquet` (no per-VM shard — the last-modified timestamp on the index was ~15s behind the VM's
own log tail at check time). This is unrelated to the 6 named VMs from the original 2026-06-22 finding (those ARE
confirmed terminal — 0 sports-tagged instances, running or otherwise, exist in the project today) but it means the
manifest is NOT currently in a safe drained state for an unprotected read-modify-write regardless of the premise
question above.

## Why it matters

- The dispatched todo's "Done when" (relabel over 120x789, re-measure honest-cov, record the delta) cannot honestly be
  satisfied as written — there is no 789-league phantom set left to relabel. Running the prescribed script against
  today's manifest would either no-op on 693 leagues that no longer have any rows in-window, or — worse — if adapted to
  match today's 96-league residual without re-diagnosing it, risks mislabeling genuine post-cutover pending-fetch gaps
  as `expected_empty` (false-absence corruption), exactly the failure mode
  `close_stale_enrichment_expected_unattempted_cells_2026_07_19.py`'s docstring documents for a structurally similar
  case (a blind "no coverage" closer stamping `EXPECTED_NO_FIXTURE` over a real pending gap).
- Honest coverage is currently reading a manifest with a much healthier `expected_unattempted` count than the parent
  plan believes — the parent plan's "expect a large jump" framing for this todo is itself now stale and should be
  corrected so a future reader doesn't re-diagnose the same already-resolved bug.
- The residual 33,905-row gap (mostly `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE`) is real, current, and undiagnosed — it
  should not be silently dropped just because the original prescription no longer fits.

## Recommended decision

Not prescribing the fix (needs someone to confirm the FIXTURES-split-timing hypothesis against real data first). Shape
of the follow-up:

1. Confirm/refute whether `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE`'s 18,521 pre-cutover-window `expected_unattempted`
   rows are a genuine enumerator/writer timing mismatch (the split entities never had a writer to fill them before
   2026-07-14) vs. a real pending-fetch gap the writer should still be able to close on a targeted re-run.
2. If timing-mismatch: this is an honest-absence classification fix (the enumerator should not expect
   `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE` for dates before the entity existed, OR — if the FIXTURES legacy entity's own
   row already proves the fixture happened — a provable-closure script mirroring
   `close_stale_enrichment_expected_unattempted_cells_2026_07_19.py`'s safety pattern, not a blind relabel).
3. `odds_horizon_bucket` (11,146, MDPS-owned) and `TEAMS` (1,758) need their own separate check — different owning
   service/writer, not necessarily the same root cause.
4. Any future manifest read-modify-write against `_index/availability_index.parquet` MUST use CAS
   (`download_bytes_with_generation` + `conditional_upload_bytes(if_generation_match=...)`, mirroring
   `dereg_purge_24_leagues_2026_07_13.py`'s pattern) given a live sports backfill VM is confirmed actively writing this
   same file with no per-VM sharding.

## Todos

- [ ] [DATA] P2. Confirm or refute the FIXTURES-split-timing hypothesis for the 18,521
      `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE` `expected_unattempted` rows in the 2026-02-20->06-19 window (check whether
      the legacy `FIXTURES` entity's own row proves the fixture happened for a sample of these cells, and whether the
      writer has ever been asked to backfill the split entities for pre-cutover dates). (repo: instruments-service)
- [ ] [DATA] P2. Once diagnosed, close the provably-closeable subset via a safety-pattern script (never a blind
      no-coverage relabel) — mirror `close_stale_enrichment_expected_unattempted_cells_2026_07_19.py`'s provable-closure
      discipline. Re-measure honest-cov delta afterward. (repo: instruments-service)
- [ ] [DATA] P3. Separately check the `odds_horizon_bucket` (11,146 rows, MDPS-owned) and `TEAMS` (1,758 rows) residuals
      in the same window — different owning writer, likely a different root cause than the FIXTURES-split timing gap.
      (repo: market-tick-data-service for odds_horizon_bucket; instruments-service for TEAMS)

## Progress Log

- **2026-07-25 (slot 9, data_engineering)**: Filed while executing `sports_satellite_ao_dispatch_batch2-014`. Measured
  the current manifest directly (single read, no new corpus walk) before running the prescribed script; found the
  original 789-league/1M-row premise resolved (30x reduction, 0 out-of-universe leagues left in-window) and a much
  smaller, structurally different 33,905-row residual that needs its own diagnosis rather than the prescribed relabel.
  Also confirmed a live sports backfill VM (`af-backfill-20260725-002739`) is currently writing the same manifest file
  unprotected — any future write against it needs CAS. Not fixing the residual in this pass (would be unplanned scope on
  top of an already-resolved-premise task); filed as this new, correctly-scoped issue instead.
