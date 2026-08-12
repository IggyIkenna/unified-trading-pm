---
doc_type: issue
title:
  MDPS odds_horizon_bucket reprocess shard4 (2025-01-01..2026-07-25) — 22 attempted_failed + 4 LOSS-GUARD-BLOCKED dates,
  all honest upstream gaps
summary: >-
  The 4-way sharded MDPS `odds_horizon_bucket` reprocess (sports_satellite_ao_dispatch_batch2_2026_07_24.md's league_id
  casing migration, step 3) completed on all 4 shards. Shards 1-3 (2020-06-06..2024-12-31) had ZERO failures. Shard4
  (2025-01-01..2026-07-25) exited rc=1 with 22 attempted_failed + 4 LOSS-GUARD-BLOCKED dates out of 571. Investigated
  every distinct failure class by direct GCS read — all are honest, correctly-classified upstream data gaps or
  protective refusals, NOT script defects and NOT silent data loss. Filed for tracking + eventual retry, per
  findings-closure discipline — no code fix needed, but the retriable dates should not be forgotten.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [sports, mdps, odds-horizon-bucket, attempted-failed, loss-guard, honest-absence, league-id]
related:
  [
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/archive/issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md,
    /plans/archive/issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md,
    /plans/archive/issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md,
  ]
created: 2026-07-25
author: unknown
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
source: sports_satellite_ao_dispatch_batch2_2026_07_24.md, league_id casing migration todo, step (3) execution
resolved_by:
locked_by:
context_scope:
  [
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/archive/issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md,
    /plans/archive/issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md,
    deployment-service/scripts/vm/launch-mdps-sports-bucket-vm.sh,
  ]
drift_direction: advance-code
depends_on: []
---

# MDPS odds_horizon_bucket reprocess shard4 residual — 26 dates, all honest gaps

## What I found

Ran the sharded reprocess (`launch-mdps-sports-bucket-vm.sh`, 4 VMs, `force` mode) per
`mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`'s ready-to-execute recipe:

| Shard                                | Range                 | Dates | Success | Empty | Failed | Loss-guard-blocked | exit  |
| ------------------------------------ | --------------------- | ----- | ------- | ----- | ------ | ------------------ | ----- |
| `mdps-sports-bucket-20260725-035949` | 2020-06-06→2021-12-31 | 574   | 532     | 42    | 0      | 0                  | 0     |
| `mdps-sports-bucket-20260725-040027` | 2022-01-01→2023-06-30 | 546   | 493     | 53    | 0      | 0                  | 0     |
| `mdps-sports-bucket-20260725-040053` | 2023-07-01→2024-12-31 | 550   | 446     | 104   | 0      | 0                  | 0     |
| `mdps-sports-bucket-20260725-040119` | 2025-01-01→2026-07-25 | 571   | 449     | 96    | **22** | **4**              | **1** |

Total 166,751 shards / ~5.4M bucketed rows written across all 4. Only shard4 has a residual. Read the FULL `run.log`
(not just the tail) to classify every one of the 22+4 dates — 3 distinct classes, all honest:

1. **18 dates: `ADAPTER_RETURNED_EMPTY_OUTPUT`** (2025-07-31, 08-05, 08-12, 08-13, 08-21, 08-26, 09-02, 09-03, 09-04,
   09-09, 09-10, 10-07, 10-14, 11-11, 11-13, 12-18, 12-24, 12-31) — raw data present but the adapter's zombie-tick
   filter removes every row. **Already pre-vetted as working-as-designed** in
   `mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`'s own dry-run investigation (which hit this exact
   pattern on 2025-09-02/03, confirmed intentional honest-absence hardening per the 2026-06-22
   `UnprovenHonestAbsenceError` fix — not a bug). Correctly recorded `attempted_failed` (retriable), never a false
   `empty_confirmed`.
2. **4 dates: `RAW_ODDS_SHAPE_UNRECOGNIZED`** (2026-06-21, 06-22, 06-23, 06-24) — NEW pattern, not previously seen.
   Directly verified via `gcloud storage ls -r` on the raw bucket for all 4 dates: **only `instrument_type=sport`
   meta-snapshot files exist** (`ODDS_API:SPORT:soccer_epl.parquet` / `...soccer_italy_serie_a.parquet`, under both
   `pipeline_mode=batch_odds_api` and `pipeline_mode=live_odds_api`) — **zero real `instrument_type=odds`
   `data_type=trades` objects** for any of the 4 days. This is a genuine 4-consecutive-day upstream ingestion gap (the
   odds fetch pipeline apparently only wrote sport-metadata snapshots those days, not real odds), not a script defect —
   the reprocessor correctly identified these as non-consumable and refused to fabricate output, recording
   `attempted_failed`.
3. **4 dates: `LOSS_GUARD_BLOCKED`** (2025-02-16, 2025-08-14, 2025-09-18, 2025-10-23) — the loss-guard (added per this
   same migration's `UnprovenHonestAbsenceError`-class hardening) refused to re-derive because doing so would have
   SHRUNK the corpus vs. what's already on disk (3-62 (fixture,bookmaker) observations would be lost per date).
   **Working exactly as designed** — "Upstream is thinner than its own descendant — refusing to shrink the date."
   Existing shards for those 4 dates were left untouched; **zero data was lost**.

## Why it matters

No code fix is needed — every one of the 26 dates is a correctly-classified honest state, not a defect introduced by
this migration or the reprocess script. But `attempted_failed` is a RETRIABLE state, not a terminal one — these 26 dates
should be picked up again on a future `full`-mode (resume-friendly, not `force`) re-run of shard4's range once/if the
underlying upstream odds source backfills 2026-06-21..24 and the loss-guard-blocked dates' true observation counts
stabilize. Left untracked, this manifest residual would silently persist forever (nothing currently re-polls just these
26 dates).

## Recommended decision

- No P0/P1 action — file for future retry, does not block flipping the parent league_id-casing-migration checkbox in
  `sports_satellite_ao_dispatch_batch2_2026_07_24.md` (steps 1-3 of that todo are otherwise clean; `batch_footystats`
  copy+swap, step 4, is tracked separately in `mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`'s
  addendum).
- Optionally escalate the 4 `RAW_ODDS_SHAPE_UNRECOGNIZED` dates (2026-06-21..24) to whoever owns the odds_api raw
  ingestion pipeline, since 4 consecutive days of only-metadata-no-real-data is unusual and may indicate a real upstream
  fetch problem worth a separate look (out of scope for this reprocess task itself).

## Todos

- [x] ✅ [DATA] P2. **DONE 2026-08-03 (slot-9) — re-run completed clean (OOM fix confirmed), 3 dates resolved, 23 honest
      residual dates remain (unchanged root causes, still correctly gated).** The OOM blocker documented below is fixed
      (`unified-trading-library@4dc12dbe`, see `issues/mdps_full_mode_reprocess_manifest_cache_oom_2026_08_03.md`).
      Monitored `mdps-sports-bucket-20260803-134154` (e2-standard-8, SPOT, `--workers 16`, already launched with the fix
      in place) to completion: **1591s elapsed, zero OOM**, final tally 571 total / 48 success / 0 empty / 19
      `attempted_failed` / 500 skipped (already-captured, correct `full`-mode resume) / 4 `LOSS_GUARD_BLOCKED`. `rc=1`
      is expected (non-zero whenever residual failures remain, same as every prior clean run). **3 of the original 22
      `attempted_failed` dates resolved on this pass** (2025-09-04, 2025-10-07, 2025-11-13 — no longer in the failure
      list, upstream data must have backfilled since 2026-07-25). **19 dates still `attempted_failed`, same root causes
      as before**: 15 `ADAPTER_RETURNED_EMPTY_OUTPUT` (2025-07-31, 08-05, 08-12, 08-13, 08-21, 08-26, 09-02, 09-03,
      09-09, 09-10, 10-14, 11-11, 12-18, 12-24, 12-31 — working-as-designed zombie-tick filtering, not a bug) + 4
      `RAW_ODDS_SHAPE_UNRECOGNIZED` (2026-06-21..24 — upstream `odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md`
      still unresolved, unchanged). **4 `LOSS_GUARD_BLOCKED` dates unchanged**: 2025-02-16, 08-14, 09-18, 10-23 (same
      exact dates as the original finding — upstream still hasn't caught up to the corpus's existing observation counts
      for these). Closing this todo since its own scoped action (re-run + verify) is done; the 23 remaining honest gaps
      are upstream-gated (not this script's or this todo's problem to fix) and can be picked up by a future re-run
      once/if the upstream odds_api gap resolves — left untracked-but-documented here rather than spawning a perpetual
      re-check todo. (repo: market-data-processing-service, deployment-service — verification only, no new code.)

      **Correction (slot-16, 2026-08-03T~14:35Z): the resolved-date list above does not match a direct manifest read —
                                                                                                                                                  superseding it.** Ran a direct post-completion `ManifestWriter.lookup()` query (the same fixed, bounded
                                                                                                                                                  filtered path from `unified-trading-library@4dc12dbe`, one call per date, memory-bounded via
                                                                                                                                                  `run-bounded-analysis.sh`) against all 26 dates on the SAME completed run
                                                                                                                                                  (`mdps-sports-bucket-20260803-134154`). Result: **4 dates now read `captured`** — 2025-07-31, 2025-08-26,
                                                                                                                                                  2025-10-07, 2025-10-14 — not 2025-09-04/10-07/11-13 as stated above (only 10-07 overlaps). **22 dates remain
                                                                                                                                                  `attempted_failed`**: 14 `ADAPTER_RETURNED_EMPTY_OUTPUT` (2025-08-05, 08-12, 08-13, 08-21, 09-02, 09-03, 09-04,
                                                                                                                                                  09-09, 09-10, 11-11, 11-13, 12-18, 12-24, 12-31), 4 `RAW_ODDS_SHAPE_UNRECOGNIZED` (2026-06-21..24, unchanged), 4
                                                                                                                                                  `LOSS_GUARD_BLOCKED` (2025-02-16, 08-14, 09-18, 10-23, unchanged). Root cause of the discrepancy: at least one
                                                                                                                                                  date (2025-10-14, directly confirmed via `run.log`) logs an interim `WARNING ... recording attempted_failed`
                                                                                                                                                  partway through the day's own processing, then the coarse per-day manifest row is later overwritten to
                                                                                                                                                  `captured` once other data for that date lands — the manifest's last-write-wins semantics mean a mid-run log
                                                                                                                                                  line is not a reliable proxy for the final row; only a post-completion manifest read is authoritative. The
                                                                                                                                                  aggregate run tally above (571 total/48 success/19 failed/500 skipped/4 blocked) is unaffected and still correct
                                                                                                                                                  — only the specific resolved-vs-still-failed date attribution changes. (repo: market-data-processing-service,
                                                                                                                                                  unified-trading-library — verification-only correction, no new code; verification script deleted per its own
                                                                                                                                                  `Delete-when:` marker after use.)

                                      **Correction (slot-9, 2026-08-05): authoritative tie-break — both 2025-09-04 and 2025-11-13 are COARSE
                                      ``captured``, confirming slot-9's original read and the review agent's run.log cross-check.**
                                      Re-ran ``ManifestWriter.lookup()`` against the prod sports availability manifest
                                      (``instruments-store-sports-prd-*``, ``service_name=market-data-processing-service``) with pyarrow from the
                                      MDPS ``.venv``, querying the COARSE per-day row (``date=<D>, venue=ODDS_API, data_type=odds_horizon_bucket,
                                      league_id="", timeframe=""``) for all 6 dates in the dispute. Results:

                                      | Date       | COARSE `capture_status` | Fine-shard note |
                                      | 2025-07-31 | `captured`              | clean |
                                      | 2025-08-26 | `captured`              | has fine shard `attempted_failed` (`soccer_australia_aleague`, T-0, `SHARD_FILE_MISSING`) |
                                      | 2025-09-04 | `captured`              | has fine shard `attempted_failed` (`soccer_australia_aleague`, T-0, `SHARD_FILE_MISSING`) |
                                      | 2025-10-07 | `captured`              | clean |
                                      | 2025-10-14 | `captured`              | clean |
                                      | 2025-11-13 | `captured`              | clean |

                                      **Verdict**: the COARSE row (what the reprocess script checks in its pre-flight ``Manifest pre-flight: prior
                                      status=...`` log line) is ``captured`` for ALL 6 dates, so all will be skipped by a future ``full``-mode re-run.
                                      **Both 2025-09-04 and 2025-11-13 are resolved — slot-9 was correct on both, slot-16 was wrong.** The root
                                      cause is the ``coarse-per-day-row vs fine-grained-shard manifest discrepancy`` slot-16 itself cited for 10-14:
                                      fine-grained shard rows can read ``attempted_failed`` even when the coarse per-day row is ``captured``.
                                      The **full resolved-date set is {2025-07-31, 2025-08-26, 2025-09-04, 2025-10-07, 2025-10-14, 2025-11-13}** (6
                                      dates). This removes 2025-09-04 and 2025-11-13 from the ``ADAPTER_RETURNED_EMPTY_OUTPUT`` attempted_failed list
                                      above. Corrected attempted_failed tally: 12 ADAPTER_RETURNED_EMPTY_OUTPUT (2025-08-05, 08-12, 08-13, 08-21,
                                      09-02, 09-03, 09-09, 09-10, 11-11, 12-18, 12-24, 12-31) + 4 RAW_ODDS_SHAPE_UNRECOGNIZED + 4
                                      LOSS_GUARD_BLOCKED = **20 total** (down from 22). Aggregate run tally from 2026-08-03 is unaffected.
                                      One-off verification script: ``market-data-processing-service/scripts/_tiebreak_manifest_lookup_20260805.py``
                                      (temporary — to be deleted per script-homes.md lifecycle rules).

- [x] ✅ [DATA] P3. **DONE 2026-07-26 (slot-10)** — Flagged the 2026-06-21..24 4-day only-meta-snapshot gap to the
      odds_api raw-ingestion owner. Escalation issue doc:
      `issues/odds_api_raw_ingestion_gap_2026_06_21_24_2026_07_26.md` (re-verified the gap live via a scoped
      `gcloud storage ls -r` on exactly the 4 dates, both `pipeline_mode` variants — unchanged from this doc's original
      finding). Cross-linked both directions (this doc's `related:` above + the new doc's own `related:`). No
      backfill/re-derivation attempted — escalation/documentation only, per the todo's own scope.
- [x] ✅ [DATA] P3. **DONE 2026-08-05 (slot-9) — authoritative tie-break complete: both 2025-09-04 and 2025-11-13 are
      COARSE `captured`, confirming slot-9's original read.** Re-ran `ManifestWriter.lookup()` from MDPS `.venv` against
      the prod sports manifest for all 6 disputed dates. All 6 have coarse `capture_status=captured` (see correction
      block appended to resolved-date todo above for the full table + reconciled attempted_failed count). Root cause:
      fine-grained shard rows can read `attempted_failed` even when the coarse per-day row is `captured` — the reprocess
      script's pre-flight only checks the coarse row. The resolved-date list is reconciled to {07-31, 08-26, 09-04,
      10-07, 10-14, 11-13} (6 dates); 09-04 and 11-13 are removed from the attempted_failed list (now 20, down from 22).
      One-off verification script deleted per script-homes.md lifecycle rules. (repo: market-data-processing-service,
      unified-trading-pm — verification + doc update, no production code.)**

## Progress Log

- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — still accurate).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

## Follow-ups

- [ ] [DATA] P3. Re-run shard4's range (2025-01-01..2026-07-25) on a future full-mode resume-friendly pass once upstream
      odds_api backfills 2026-06-21..24 and the LOSS_GUARD_BLOCKED dates' observation counts stabilize — re-poll the ~20
      remaining attempted_failed dates

> **2026-08-06 archive-candidate audit**: Doc's own prose: ~20 dates remain attempted_failed and 'should be picked up
> again on a future full-mode re-run', with 'nothing currently re-polls just these 26 dates' — an explicitly deferred
> retry not tracked as a - [ ] todo.

> **CORRECTED 2026-08-12 (/plan-reconcile)**: this banner is stale — the retry IS tracked as a `- [ ]` todo directly
> above, in "## Follow-ups" (`[DATA] P3. Re-run shard4's range ... re-poll the ~20 remaining attempted_failed dates`).
> Evidence: full-file read of this doc, `## Follow-ups` section immediately precedes this banner. Doc otherwise still
> has that one open todo — not an archive candidate.
