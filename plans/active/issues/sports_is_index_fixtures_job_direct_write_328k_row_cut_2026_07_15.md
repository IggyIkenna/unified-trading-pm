---
doc_type: issue
title:
  IS sports canonical `_index` lost 328,292 rows at 2026-07-15T00:49:43Z to a direct ManifestWriter index write by
  `uts-prod-instruments-service-sports-fixtures` — L6-legacy-only regressed 28 → 3,316 cells, reopening the E8 data-loss
  gate the 2026-07-13 targeted migration had closed
summary: |
  The operator-initiated L6 re-migration touch (2026-07-15) regenerated the legacy-only cell lists for both sports
  surfaces and found the IS surface REGRESSED: `cf_manifest_audit_2026_06_01.py` now reports 3,316 legacy-only cells
  (was 28 across four independent audits on 2026-07-14). Root cause of the regression, attributed from Cloud Run logs:
  the consolidator wrote a 5,758,047-row canonical at 00:44:28Z; at 00:49:43Z the Cloud Run job
  `uts-prod-instruments-service-sports-fixtures` logged `ManifestWriter: updated availability index (5,430,037 total
  entries, 282 new)` — a DIRECT read-modify-write of `_index/availability_index.parquet` whose base was 328,292 rows
  SMALLER than the consolidator's 5-minutes-earlier state; the next consolidator cycle read canon_rows=5,430,037 and
  the rows never came back (source shards long pruned). The vanished cohort is precisely the 2026-07-13 L6 targeted
  migration's re-emitted captured rows PLUS their per-league placeholder cohorts: 3,288 (date,venue,data_type) cells
  (2018=1,467 / 2019=1,402 / 2020=419 / 2024=12 / 2025=16; FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/PLAYER_STATS/
  MATCHES/PLAYER_VALUES/PREDICTIONS/ODDS + 28 known INJURIES + 2 WEATHER phantoms) now have ZERO rows of ANY status in
  the canonical index at (date, data_type) grain — full absence, which dedup alone cannot produce. 2,848 of the 3,316
  carry legacy `instrument_count>0` (real data per the legacy manifest; backing objects were verified already-copied
  to canonical on 2026-07-13 — the OBJECT layer is intact, only the manifest-row layer regressed). The fixtures job
  direct-writes the index every ~1 minute (log history), permanently racing the per-minute consolidator cron — so any
  manifest re-emission fix is liable to be reverted again until this double-writer race is fixed. MDPS is unaffected
  (140 legacy-only cells, byte-identical to the operator-ACCEPTED phantom class; index row count 1,958,499 unchanged).
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, instruments-service, market-tick-data-service]
scope: [engineer]
tags: [manifest, consolidator, manifest-writer, lost-update, data-correctness, sports, l6-legacy-only, e8-gate]
related:
  [
    plans/active/sports_manifest_canonicalisation_2026_06_01.md,
    plans/active/issues/legacy_seed_captured_outranks_resurrection_risk_2026_07_15.md,
    plans/active/issues/sports_index_recency_masked_captured_atoms_2026_07_13.md,
    plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
    codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-15
last_updated: 2026-07-15
parent_epic: mtds_mdps_master
priority: P0
source: |
  Discovered by the operator-initiated L6 re-migration dispatch (2026-07-15) while regenerating the current
  legacy-only cell lists (step 1 of that task) — the pre-action baseline itself exposed the regression. Attribution
  from `gcloud logging read` on the consolidator + fixtures Cloud Run jobs; cell characterisation from the audit
  tool's own downloaded `_index` parquets (no new whole-corpus GCS walk).
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# IS sports canonical index: fixtures-job direct write erased 328k rows — L6 gate regressed 28 → 3,316

## Timeline (all 2026-07-15 UTC, from Cloud Run logs — evidence commands at the bottom)

1. Through 00:44:28Z the `uts-prod-manifest-consolidator-instruments-sports` cycles repeatedly wrote the canonical at
   **5,758,047 rows** (`wrote consolidated index (5758047 rows, …)` at 00:36:39, 00:41:29, 00:42:00, 00:44:28).
2. **00:49:43Z — `uts-prod-instruments-service-sports-fixtures`**:
   `ManifestWriter: updated availability index (5430037 total entries, 282 new) in instruments-store-sports-prd-central-element-323112`
   — a DIRECT canonical write (not a per-VM shard). Base = 5,430,037 − 282 = **5,429,755 rows: 328,292 rows smaller**
   than the consolidator's state written 5 minutes earlier.
3. 00:50:46Z — the next consolidator cycle's `phase=canonical_downloaded` read **canon_rows=5,430,037**; every cycle
   since re-merges only the live per-VM shards (the 2026-07-13 migration shards were absorbed + pruned long ago), so the
   canonical has hovered at ~5,430,039-5,433,118 ever since. The lost rows have no surviving shard source.
4. The fixtures job's log history shows it direct-writes the index every ~1 minute while running (e.g. 18 writes
   06:31-06:54Z) — a standing lost-update race against the per-minute consolidator cron, not a one-off.

## Effect on the L6/E8 data-loss gate (measured this touch, full enumeration — not sampled)

- `cf_manifest_audit_2026_06_01.py instruments-store-sports-prd-… --legacy instruments-store-sports-…`: **legacy-only =
  3,316** (legacy captured cells 41,939 / canonical 78,242 / overlap 38,623). On 2026-07-14 four independent audits read
  **28** (all INJURIES, accepted-phantom class). Legacy side is unchanged (41,939 both days) — the canonical side lost
  previously-overlapping captured cells.
- Breakdown of the 3,316 (per-cell groupby-MAX legacy `instrument_count`, per the 25th touch's Gotcha-#2 lesson):
  FIXTURE_STATS 1,184 (1,025 real) / FIXTURE_EVENTS 467 (437) / FIXTURE_LINEUPS 464 (433) / PLAYER_STATS 434 (219) /
  MATCHES 325 (322) / PLAYER_VALUES 166 (166) / PREDICTIONS 123 (123) / ODDS 123 (123) / INJURIES 28 (0) / WEATHER 2
  (0). Years: 2018=1,467, 2019=1,402, 2020=419, 2024=12, 2025=16. **Real (ic>0) total: 2,848.**
- **3,288 of the 3,316 have ZERO canonical rows of ANY capture_status at (date, data_type) grain** (the remaining 28 =
  the known accepted-phantom INJURIES class, still present as `empty_confirmed`). Full absence of entire per-league
  populations (~95 rows/cell ≈ the 328k total) is a row-DELETION signature — dedup/collapse keeps a winner per key and
  cannot produce it. Not venue-rekeying either (checked: no captured row under ANY venue for those date+data_type).
- **The object layer is intact**: the 2026-07-13 migration verified all 14,111 backing objects present in canonical (0
  copied / 14,111 skipped_existing) and nothing has deleted objects. Only the manifest-row layer regressed.

## Root-cause status

Attribution is confirmed (the fixtures job's 00:49:43Z direct write). The MECHANISM by which its in-memory base came to
be 328,292 rows smaller is NOT root-caused this touch. Candidates for the P0 below, in likelihood order:

1. The ManifestWriter direct-update path's read-before-write (e.g. `merge_canonical_with_outstanding_shards` /
   `_merge_shard_frames`) deduping at a COARSER key than the consolidator's, collapsing per-league populations — note
   the reader-side merge gained the captured-outranks tie-break `unified-trading-library@17ee38de` (2026-07-14) and the
   consolidator gained Option-B cross-service_name collapse `@9bc06261`; the deployed instruments-service image was
   digest-bumped 2026-07-14 (`instruments-service@ca3902bb`), so the fixtures job is running recent UTL.
2. A stale/partial canonical download inside the fixtures job (lost-update with an old base).
3. A filter/exception path silently dropping rows on the write-back (would be the `never silent placeholders` class).

## What this touch did NOT do (and why)

- **No re-migration write was attempted.** Three reasons, each individually sufficient: (a) 3 `af-backfill-20260714-*`
  VMs (API_FOOTBALL FIXTURE_EVENTS/FIXTURE_LINEUPS/FIXTURE_STATS, 2020-06-06..2026-07-13) are actively writing per-VM
  shards to this exact surface with the consolidator merging every ~7 min — the pause-cron/force-consolidate recipe the
  documented targeted-migration mechanism requires would collide with the in-flight fleet (the Finding-1 class, 3×
  recurred); (b) the fixtures job's unfixed direct-write race means a re-emission is liable to be silently reverted
  again (the cefi resurrection lesson: do not burn another cycle before the root cause lands); (c) per-cell verification
  to a stable 0 is impossible against a mid-rewrite index.
- **Zero deletions performed anywhere; legacy buckets touched by READS only** (operator constraint honoured).

## Recommended next steps

- [ ] [CODE] P0. Root-cause + fix the fixtures-job direct-write row loss (repo: unified-trading-library +
      instruments-service): reproduce the ManifestWriter direct-update read path against a copy of the current
      canonical + live shards and find where 328k rows drop (dedup-key mismatch vs stale base vs silent filter). The
      structural fix should ALSO stop the standing race: either move the fixtures job to per-VM-shard mode
      (`MANIFEST_PER_VM_SHARDS=true`, consolidator-mediated like every other writer) or give the direct path a
      generation-CAS + row-count/column-fill regression guard (the `MANIFEST_ROW_COUNT_REGRESSION` / `@2e132bb2`
      pattern). A 5.6% silent index shrink must page, not pass.
- [ ] [DATA] P0. Re-run the targeted L6 manifest re-emission for the regressed cells (repo: market-tick-data-service;
      scripts `migrate_sports_instruments_legacy_gap_2026_07_13.py` +
      `write_sports_instruments_legacy_gap_manifest_2026_07_13.py`, both accept `--cells-csv`) — **ONLY AFTER** (a) the
      P0 above lands (else it reverts again) AND (b) the `af-backfill-20260714-*` fleet completes (avoid the pause-cron
      collision). Regenerate the cell list fresh at run time (the af fleet is re-capturing some 2020+ cells; 2018/2019
      footystats-era cells it cannot re-capture). Then re-run `cf_manifest_audit_2026_06_01.py … --legacy …` per-cell to
      a stable count.
- [ ] [DATA] P2. Determine whether any OTHER canonical index has the same fixtures-job-style direct-writer racing its
      consolidator (grep services for non-per-VM `ManifestWriter` usage against consolidator-managed buckets); the
      lost-update pattern is generic.

## Evidence

- `gcloud logging read 'resource.type="cloud_run_job" resource.labels.job_name="uts-prod-manifest-consolidator-instruments-sports" textPayload:"rows_out"' --freshness=40h`
  — rows_out 5,758,047 through 00:44:28Z; 5,430,039 at 00:58:39Z; `canonical_downloaded canon_rows=5430037` at
  00:50:46Z.
- `gcloud logging read '("5430037" OR "5430039") timestamp>="2026-07-15T00:40:00Z" …'` — the fixtures job's
  `updated availability index (5430037 total entries, 282 new)` line at 00:49:43.515Z (the only non-consolidator hit).
- Audit runs + full cell enumerations: operator-initiated L6 re-migration touch 2026-07-15 (this session), from the
  audit tool's own downloaded `canon_index.parquet`/`legacy_index.parquet` (fresh `_index` pulls, both surfaces).
- MDPS control: `market-data-tick-sports-prd` index rows 1,958,499 (unchanged since 2026-07-14); legacy-only 140,
  byte-identical to the ACCEPTED phantom class (all `instrument_count=0`, canonical `empty_confirmed` for all 140).
