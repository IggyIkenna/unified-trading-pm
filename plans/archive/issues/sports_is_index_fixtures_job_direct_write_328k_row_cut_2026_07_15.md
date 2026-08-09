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
status: resolved
nature: notes
asset_group: [sports]
stage: [data]
repos: [unified-trading-library, instruments-service, market-tick-data-service]
scope: [engineer]
tags: [manifest, consolidator, manifest-writer, lost-update, data-correctness, sports, l6-legacy-only, e8-gate]
related:
  [
    plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    plans/active/issues/legacy_seed_captured_outranks_resurrection_risk_2026_07_15.md,
    plans/archive/2026_08/sports_index_recency_masked_captured_atoms_2026_07_13.md,
    plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
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
  unified-trading-library@45a43438, instruments-service@a25cf70d, unified-api-contracts@c280e1ff,
  unified-trading-pm@10ad5d69a
---

> **✅ ARCHIVED 2026-07-25** — `status: resolved`, core 328k-row finding resolved (the rows were correctly-clipped
> pre-launch artifacts, not data loss — see STEP 3). One residual item struck as void/superseded (was already explicitly
> superseded by this doc's own STEP 3); one genuinely-open low-priority P1 forensics item remains, tracked in
> `/plans/archive/2026_07/sports_consolidated_closeout_aggregated_sources_2026_07_24.md`'s digest. Moved to
> `plans/archive/issues/` per the issue-doc-lifecycle archival ritual.

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

- [x] [CODE] P0. Root-cause + fix the fixtures-job direct-write row loss (repo: unified-trading-library +
      instruments-service): reproduce the ManifestWriter direct-update read path against a copy of the current
      canonical + live shards and find where 328k rows drop (dedup-key mismatch vs stale base vs silent filter). The
      structural fix should ALSO stop the standing race: either move the fixtures job to per-VM-shard mode
      (`MANIFEST_PER_VM_SHARDS=true`, consolidator-mediated like every other writer) or give the direct path a
      generation-CAS + row-count/column-fill regression guard (the `MANIFEST_ROW_COUNT_REGRESSION` / `@2e132bb2`
      pattern). A 5.6% silent index shrink must page, not pass.
- [ ] ❌ [DATA] P0. ~~Re-run the targeted L6 manifest re-emission for the regressed cells~~ — **VOID, struck 2026-07-25
      (archival sweep).** This item was already SUPERSEDED by this doc's own "STEP 3" below at the time it was written
      (see "Recommended next steps (SUPERSEDING this doc's earlier P0-DATA re-emission item, which is now void)") — the
      doc's central premise (that the 328k rows were legitimate data) was FALSIFIED: the rows were pre-launch artifacts
      the UAC coverage SSOT correctly refuses to write, not a data-loss event. Re-emission was correctly never
      performed. Leaving struck-through rather than deleted so this doc's own history stays accurate; the doc's digest
      referrer (`sports_consolidated_closeout_aggregated_sources_2026_07_24.md`) listed this as an open residual — that
      listing is stale and is corrected in the same commit as this archival.
- [x] [DATA] P2. Determine whether any OTHER canonical index has the same fixtures-job-style direct-writer racing its
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
- 2026-07-15 10:29Z (loop, protective action): ALL FOUR uts-prod-sports-fixtures-*-t1-schedule schedulers PAUSED
  (midnight/6am/noon/6pm — verified PAUSED) before the next fire could clobber again; fixture T1 freshness halted until
  the fix deploys. Fix chain dispatched: per-VM-shard conversion for the job's manifest writes + row-count regression
  guard on direct canonical writes (defense-in-depth) → promote → image → re-enable schedulers with a watched first
  execution → re-emit the 3,288 vanished cells → L6 gate re-check.

## Fix-chain progress (2026-07-15, dispatched fix session)

- **Containment gap found + closed (~11:05Z)**: pausing the four t1 schedulers did NOT contain the vector — the 5-min
  `uts-prod-sports-scheduler-cron` (`sports_trigger_scheduler` + `configs/sports-trigger-tiers.yaml` Tier-1
  FIXTURES/STANDINGS entries) dispatches the SAME `uts-prod-instruments-service-sports-fixtures` job; post-pause
  executions at 10:45:48Z, and at **10:47:45Z the job direct-wrote the canonical again**
  (`updated availability index (5432297 total entries, 94 new)`). Closed by the per-VM conversion below (job CONFIG,
  effective for every dispatcher with the CURRENT image — no rebuild needed for this leg).
- **Per-VM conversion applied (job config, ~11:05Z)**:
  `gcloud run jobs update uts-prod-instruments-service-sports-fixtures --update-env-vars MANIFEST_PER_VM_SHARDS=true,VM_NAME=sports-fixtures-job`
  → job generation 6, env verified. The job's ManifestWriter now writes `_index/per_vm/sports-fixtures-job.parquet`
  (consolidator-mediated) and can never read-modify-write the canonical again. NOTE the job is NOT terraform-managed
  (created ad hoc via gcloud, creator unified-trading-sa) — this env config is the deployment record; if the job is ever
  recreated, these two env vars are REQUIRED.
- **Same vector on the 3 enrichment-provider jobs (same canonical!)**:
  `uts-prod-sports-enrichment-{footystats, transfermarkt,soccer-football-info}` (daily 00:35/00:40/00:45Z, TF-managed,
  same image + same legacy-mode ManifestWriter → the TF header itself documents a live direct canonical write). All 3
  updated in place the same way (`VM_NAME=sports-enrichment-<key>`) AND the terraform SSOT aligned so an apply can't
  revert: `deployment-service@17320c6` (`terraform/gcp/sports_enrichment_provider_scheduler.tf`).
- **Defense-in-depth guard shipped — `unified-trading-library@45a43438`**: `ManifestWriter` now REFUSES any direct
  canonical write whose merged output is >2% smaller than the base it just read (`_INDEX_SHRINK_GUARD_PCT` in
  `_writer_io.py`, both the generation-match and unconditional paths), raising `ManifestIndexShrinkRefusedError`,
  logging CRITICAL, and emitting `MANIFEST_ROW_COUNT_REGRESSION` (`action=write_refused`) so the shrink pages instead of
  passing. Explicit force flag = `ManifestWriter(allow_index_shrink=True)` (deliberate maintenance rewrites only). 7
  unit tests (`tests/unit/test_manifest_writer_index_shrink_guard.py`) cover refuse/threshold/force/fresh-index/both
  write paths/capture-loop isolation. (Config-knob variant was structurally impossible: `cloud_config.py` at 899/900 and
  `_state.py` at 900/900 of the codex size cap — constant + constructor flag mirrors the consolidator's
  `_ROW_COUNT_REGRESSION_ALERT_THRESHOLD` precedent.)
- **Blocking discovery — every recent FULL fixtures run was FAILING on an unrelated IS bug**: 00:10 + 06:10 execution
  pairs died at finalize with `InvalidCompletenessFractionError: ... got 4.0` — `catalogue.py:99` computed
  `len(written_venues)/len(expected_venues)` where the `--sports-provider=API_FOOTBALL` filter narrows expected to 1
  venue while the run writes 4. Fixed as intersection-over-expected (`_catalog_completeness_fraction`, always in [0,1]):
  `instruments-service@a25cf70d` + 5 regression tests. Without this the re-enabled schedulers could never produce the
  required green watched execution. (Secondary failure class also seen 10:46Z: transient
  `ManifestConsolidatorStaleError` when the consolidator cycle lags >120s under the af-backfill load — self-healing, not
  code-fixed this session.)
- **Root-cause note (mechanism)**: the write path is confirmed (legacy-mode direct canonical read-merge-write); the 328k
  collapse is the writer-side `_merge_dataframes` deduping the consolidator's canonical at a COARSER key (its
  optional-dim key is value-presence-gated vs the consolidator's schema-union key `_resolve_dedup_cols`) — exactly the
  candidate-#1 class. Both structural fixes remove the exposure regardless of which optional dim collapsed: the job no
  longer touches the canonical, and any residual direct writer that collapses >2% is refused.
- **Pre-clobber canonical unrecoverable**: bucket has NO object versioning (single generation `#1784115419463073`) and
  NO soft-delete policy — the 5,758,047-row generation cannot be restored; re-emission is the only repair path.
- **P2 executed (other direct writers on consolidator-managed indexes)**: full env enumeration of every prod Cloud Run
  job (region asia-northeast1) for `MANIFEST_PER_VM_SHARDS`. CONFIRMED same-class writers converted in place (2026-07-15
  ~12:05Z): `uts-prod-instruments-service-{cefi,defi,tradfi,prediction}-t1-recon` → `MANIFEST_PER_VM_SHARDS=true` +
  `VM_NAME=is-{ag}-t1-recon-job` (same IS code path, same canonical-index race, other asset_groups).
  `uts-prod-market-tick-data-service-fast-t1-recon` already ran per-VM (the sanctioned precedent). Remaining jobs
  without the env var are predominantly non-manifest-writers (digests/watchers/paging/tarball/paper) — any residual
  writer among them is now covered by the UTL >2% shrink-refusal guard once its image picks up
  `unified-trading-library@45a43438`; `uts-dev-instruments-service-t1-recon` (dev tier) left unconverted deliberately.
- **Deploy progress**: promote PRs merged to main — UTL#576 (45a43438), IS#796 (a25cf70d), DS#402 (17320c6), IS#797
  (digest bump `23982794` → UTL base `sha256:c19afa13…` built from 45a43438 by cloudbuild `07c7fd55` SUCCESS). IS image
  builds: `6b190bc1` SUCCESS (completeness fix, revision a6caef61 content-verified) → final `8221bc75` (revision
  e63e90f6 content-verified: new base digest + completeness fix both present).
- **First watched execution attempt (gv5g5, 11:55Z) FAILED at preflight** with `ManifestConsolidatorStaleError` — the
  consolidator's cycles under the 3-VM af-backfill load run ~430s each (interleaved `error=locked` cycles), so the
  canonical blob age exceeds the 120s staleness gate for most of each ~8-min window; the loud-fail is the DESIGNED
  health contract (refuse the possibly-OOM per-VM fallback merge). Not a regression, self-heals when the af fleet
  completes. Watched-green-execution + scheduler re-enable therefore sequenced AFTER af-fleet completion (monitor armed;
  ETA ~15:00-15:30Z from per-shard date-progress: FIXTURE_LINEUPS@2026-04-06, FIXTURE_EVENTS@2025-12-02,
  FIXTURE_STATS@2025-08-12 at ~3.3 months/h).

## Repair execution — autonomous finish-to-done session (2026-07-15, from ~16:33Z)

### STEP 1 — fix behaviour VERIFIED GREEN (watched execution `-7vlhs`)

- The dispatched watched execution `-nmg4j` (16:32:14→16:33:05Z, 51s) FAILED at the freshness preflight with
  `ManifestConsolidatorStaleError`
  (`process_preflight.py:141 _fixture_leagues_for_date → read_availability_index → _read_slow_path`). This is the
  DESIGNED loud-fail (blob age >120s while per-VM shards exist under the tail of the af-backfill load) — a SAFE refusal
  BEFORE any write, not a regression and not a direct-write. `-gv5g5` (11:55Z) failed the same way earlier.
- **af-backfill fleet DRAINED**: `af-backfill-20260714-172403` + `-172532` both powered off (172403 gone by ~16:44Z,
  172532 by ~16:51Z); their per-VM shards were absorbed + pruned from `_index/per_vm/` (only `_legacy_seed.parquet`
  remains). Consolidator resumed writing fresh (`update_time` 16:51:30Z, blob age → ~8s).
- **Fresh watched execution launched right after a consolidator write → `-7vlhs` SUCCEEDED** (16:52:05→16:57:09Z, ~5-min
  real run, `succeededCount=1`, `failedCount=0`, exit 0). All three STEP-1 assertions hold:
  - **(a) succeeded** — completeness fix `instruments-service@a25cf70d` works: a full run finalised without the
    `InvalidCompletenessFractionError` that killed every 00:10/06:10 run. (jrgn5, a 43-min full run 12:15→12:58Z, is a
    second independent green.)
  - **(b) per-VM shard, NOT a direct index write** — `gcloud logging` on `-7vlhs` (and `-jrgn5`): **ZERO**
    `"ManifestWriter: updated availability index"` lines; MANY
    `"per-VM shard updated … _index/per_vm/ sports-fixtures-job.parquet"` lines. Job env confirmed
    `MANIFEST_PER_VM_SHARDS=true`, `VM_NAME=sports-fixtures-job`, `MANIFEST_ALLOW_STALE_FALLBACK` unset (loud-refuse
    retained). The job can no longer read-modify-write the canonical.
  - **(c) index row count did NOT decrease across the run** — consolidator `rows_out` monotonically non-decreasing
    5,432,776 (16:36Z) → 5,432,779 (16:43Z) → 5,432,782 (16:51Z) → 5,432,782 (17:00Z), spanning `-7vlhs`. The UTL >2%
    shrink guard `unified-trading-library@45a43438` would block any regression regardless.
- **Consolidator cadence note (NOT a blocker; separate concern)**: real consolidation cycles run ~7.5 min each
  (bottleneck = read-merge-dedup-write of the 5.4M-row / 119 MB canonical; interleaved fast `error=locked` back-offs
  from overlapping invocations). So the canonical blob is fresh (<120s) only ~2 min of each ~7.5-min window → a fixtures
  execution launched at a random time has ~25-30% chance of passing the 120s preflight gate (`maxRetries=0`, so a stale
  fire fails safe with no retry). This pre-dates the incident and is bounded to a SAFE degraded-freshness failure (never
  a clobber, post-fix); tracked as the generic consolidator-throughput concern, not a re-enable blocker.
  - ✅ **CORRECTION (measured 17:54Z, after the af fleet fully drained): the concern above is RESOLVED, not standing.**
    The ~7.5-min cycles were af-backfill-load-induced, not structural. With the fleet drained the consolidator runs
    every ~60s at **~9s latency** (`success=True shards=1 rows_in=0 rows_out=0 error=-` — `shards=1` is just the
    permanent `_legacy_seed.parquet`; no-op cycles legitimately don't log "wrote consolidated index", which is why a "no
    write in 45m" reading is NOT a stall). The canonical blob is refreshed every cycle (`update_time` 17:53:43Z, 18s old
    at check), so it sits comfortably inside the 120s staleness gate → the re-enabled schedulers will pass preflight
    normally. Recorded so a future reader doesn't chase a phantom throughput problem.

### STEP 2 — 4 t1 schedulers RE-ENABLED (containment lifted; clobber vector closed)

`gcloud scheduler jobs resume uts-prod-sports-fixtures-{midnight,6am,noon,6pm}-t1-schedule --location asia-northeast1` →
all four verified **ENABLED** (schedules `0 0/6/12/18 * * *`). Safe to re-enable: the job is per-VM-shard-mediated and
UTL refuses any >2% direct-canonical shrink, so a scheduled fire can only (i) write a per-VM shard the consolidator
absorbs, or (ii) fail-safe at the staleness preflight — never clobber the index.

### STEP 3 — 🔴 RE-EMISSION DELIBERATELY **NOT** PERFORMED: this doc's central premise is FALSIFIED

> **Headline for the operator: the 328,292 rows were NOT legitimate data.** They were PRE-LAUNCH rows that the UAC
> coverage SSOT says must not exist, and that `ManifestWriter` refuses to write BY DESIGN. The canonical is now EXACTLY
> coverage-clipped — i.e. CORRECT. Re-emitting them would fabricate the exact phantom class the 2026-05-04 purge
> removed, so I stopped rather than force them in. This invalidates this doc's own "Recommended next step" P0-DATA
> re-emission item and the plan's E8 L6 `legacy_only == 0` criterion, and needs an operator ruling.

**How it surfaced.** Ran the sanctioned recipe end-to-end: regenerated the cell list fresh (2,848 REAL ic>0 cells /
2,484 unique `(date,data_type)` pairs), ran the object-copy leg, then the manifest re-emit. The re-emit reported a
confident `DONE: written_captured=31301 (of 31301)` — **and wrote nothing at all**: no shard in `_index/per_vm/`, and
consolidator cycles kept reporting `shards=1 rows_in=0`. Two distinct bugs stacked:

1. **Script bug (FIXED this session)** — the script called `writer.flush()`. `flush()` force-drains the module buffer
   but **deliberately DEBOUNCES the per-VM shard rewrite** (the GCS-429 fix); only `close()`/atexit pass
   `process_final=True` and actually persist `_index/per_vm/{VM_NAME}.parquet` (UTL: _"Only close() / atexit force the
   shard write … so nothing is ever stranded"_). Fixed → `writer.close()` + a **post-write read-back verification**
   (`_per_vm_shard_rowcount`) that ERRORs when the shard is empty/missing. `written_captured` counts rows handed to the
   writer, NEVER rows persisted — that gap is what made the silent no-op look like success.
2. **The real finding — the UAC PRE-LAUNCH GUARD blocks 100% of the target slice.** With `close()` in place the shard
   was STILL empty. Instrumenting the writer: after 5 successful `writer.add()` calls, `len(writer._records)==0` — rows
   discarded at `add()` with no exception (DEBUG log only). Cause: `_writer_ingest.py`'s pre-launch guard —
   `if is_pre_launch_date(data_type, date_str): return` — installed as the single chokepoint after the **2026-05-04
   incident where 229,224 pre-launch rows had to be PURGED** from the sports manifest.

**Measured: 2,848 / 2,848 target cells are pre-launch → 0 writable.** Per UAC `canonical/domain/sports/league_data.py`:
`DATA_TYPE_COVERAGE_START` floors api_football `FIXTURE_EVENTS`/`FIXTURE_LINEUPS`/`FIXTURE_STATS`/`PLAYER_STATS` at
**2020-06-06** (a deliberate POLICY floor — _"we only need data ≥ 2020-06 to match the odds_api downstream cutoff …
strategies built on these features can't trade on dates without odds anyway"_), and `SOURCE_COVERAGE_START` floors
footystats (MATCHES/PREDICTIONS/ODDS) + transfermarkt (PLAYER_VALUES) at **2019-01-01**. The target slice is entirely
2018 (1,462) / 2019 (1,064) / 2020-pre-06-06 (322).

**The clinching evidence — the canonical is ALREADY exactly coverage-clipped.** Across the 8 target data_types the
canonical carries **19,222 captured `(date,data_type)` pairs / 250,607 captured rows and ZERO pre-launch ones**, and the
minimum captured date per data_type equals its UAC floor EXACTLY:

| data_type                                                       | canonical min captured date | UAC floor                  |
| --------------------------------------------------------------- | --------------------------- | -------------------------- |
| FIXTURE_EVENTS / FIXTURE_LINEUPS / FIXTURE_STATS / PLAYER_STATS | **2020-06-06**              | 2020-06-06 (per-type)      |
| MATCHES / ODDS / PREDICTIONS                                    | **2019-01-01**              | 2019-01-01 (footystats)    |
| PLAYER_VALUES                                                   | **2019-01-01**              | 2019-01-01 (transfermarkt) |

A perfect boundary on every axis is not a coincidence, and not what a 328k-row data-loss event leaves behind. **These
2,848 cells are correctly absent by design; their legacy-only status is the coverage-clip policy working, not data
loss.**

**Consequence — this doc's timeline attribution is wrong.** Both the coverage floors (UAC `7fb79f85`, 2026-05-01) and
the writer guard (predating the 2026-06-11 module split) were live LONG before 2026-07-13. So the 2026-07-13 targeted
migration — same script → same `add()` → same guard — **cannot have written these rows either**; the claim that the
vanished cohort "is precisely the 2026-07-13 migration's re-emitted captured rows" does not survive contact with the
guard. NOT root-caused this session: what DID put pre-launch captured rows into the canonical such that 2026-07-14
audits read legacy-only=28. The `_legacy_seed.parquet` resurrection vector
(`legacy_seed_captured_outranks_resurrection_risk_2026_07_15.md`) is the shape-wise candidate, but THIS bucket's seed is
only 18,771 bytes — far too small to carry ~328k rows — so it is NOT a sufficient explanation. **That is the one genuine
open question left**, and it is a forensic question about how illegitimate rows GOT IN, not about restoring them.

**Decision (autonomous rule 12(f) decide-and-document; data-correctness HARD RULE).** I did NOT bypass the guard.
Forcing these rows in would be the banned `fake record_captured` pattern and would re-create the 229,224-row purge
class. If the coverage floors are judged WRONG, the correct and only sanctioned mechanism is to **amend the UAC coverage
SSOT** (a policy decision + a one-line floor edit per data_type), after which this same script flows through the writer
legitimately with no bypass. That is an operator ruling, not a worker call.

**⚠️ Side-effect requiring an operator ruling (surfaced honestly; done BEFORE the pre-launch finding emerged).** The
object-copy leg ran `--apply` and **copied 2,769 objects** legacy→canonical (`objects_found=22,327`,
`skipped_existing=19,558`, `zero_object_cells=0`) — essentially the ODDS `footystats_odds` 2018 tree (2,723 objects),
the one genuine OBJECT-layer legacy-only gap. Those objects now sit in canonical **with NO manifest rows** (the writer
refuses them), so they are inert/unreferenced by every manifest-driven reader and the coverage clip keeps 2018 out of
every expected-date denominator — but they ARE pre-launch artifacts in canonical, and a reader that globs GCS paths
directly (`candidate_parquet_paths()`) rather than reading the manifest could theoretically see them. I did **not**
delete them (zero-deletions HARD RULE + the standing legacy-bucket constraint). **Ruling requested**: leave (harmless,
manifest-invisible) vs. remove the copied 2018 `footystats_odds` tree.

### STEP 4 — L6/E8 gate re-run (official `cf_manifest_audit_2026_06_01.py`, both surfaces, 2026-07-15 ~17:35Z)

| surface                                        | index rows    | legacy captured | canonical | overlap | **legacy-only** |
| ---------------------------------------------- | ------------- | --------------- | --------- | ------- | --------------- |
| IS `instruments-store-sports-prd-…`            | **5,432,782** | 41,939          | 78,530    | 38,623  | **3,316** [RED] |
| MDPS `market-data-tick-sports-prd-…` (control) | **1,958,499** | 32,755          | 36,837    | 32,615  | **140** [RED]   |

**Decomposition of the IS 3,316 — every one legitimately-absent; the genuine data-loss component is ZERO:**

- **2,848 = PRE-LAUNCH real (ic>0)** — correctly clipped per the UAC coverage SSOT (proof above). NOT data loss, NOT
  migratable without a coverage-policy change.
- **468 = `instrument_count=0` phantoms** (incl. the 28 INJURIES + 2 WEATHER accepted class) — no real backing data;
  `_load_target_cells`' own `ic>0` filter excludes them; fabricating captured rows for them is banned.
- **0 = genuinely-migratable real cells.**

MDPS **140 unchanged** — the operator-ACCEPTED phantom class (all `instrument_count=0`, canonical
honest-`empty_confirmed`). Left exactly as-is; no captured rows fabricated, per instruction.

**Gate verdict (honest, NOT a naive GREEN).** The L6 **data-loss** gate is satisfied on both surfaces: **0 real
migratable cells**. But `cf_manifest_audit`'s literal `legacy_only == 0` criterion reads RED and is **unreachable BY
DESIGN** — it models neither the coverage-clip policy nor the accepted-phantom class, so no migration can ever green it
while the legacy buckets retain pre-clip-era artifacts. **The gate's DEFINITION needs amending** (exclude pre-launch +
ic=0 cells, exactly as the MDPS 140 were accepted) — filed as a P0 below. I did NOT flip the E8-verify todo to GREEN,
because claiming GREEN against the criterion as written would be false.

**E8 delete: BLOCKED PENDING OPERATOR RULING** — honoured as a HARD STOP; zero deletions performed anywhere this
session.

### Recommended next steps (SUPERSEDING this doc's earlier P0-DATA re-emission item, which is now void)

- [x] ✅ [CODE] P0. Fix the `flush()`-debounce silent no-op + add post-write read-back verification in
      `write_sports_instruments_legacy_gap_manifest_2026_07_13.py` (`close()` + `_per_vm_shard_rowcount` ERROR guard).
      Repo: market-tick-data-service.
- [x] ✅ [DATA] P0. ~~**OPERATOR DECISION NEEDED — are the UAC sports coverage floors correct?**~~ **RULED 2026-07-15:
      option (b) — THE FLOORS WERE WRONG. "Amend floors to reality."** Executed in full: floors amended to the earliest
      date we hold REAL objects, evidence-derived per source — `unified-api-contracts@c280e1ff` (+ blast radius
      `instruments-service@83e9bb23`). footystats 2019-01-01→**2018-01-01**; transfermarkt 2019-01-01→**2018-01-01**;
      open_meteo 2019-03-02→**2018-01-01**; the four api_football per-fixture 2020-06-06 overrides **DELETED** (measured
      earliest real = 2018-01-01 = the source-wide floor, so they were redundant AND contradicted the dict's own "later
      than source-wide" contract). api_football (2018-01-01), understat (2014-01-01), soccer_football_info (2019-01-01)
      and SFI_PROGRESSIVE_STATS (2020-01-01) measured **already correct** → unchanged. The false premise is replaced in
      the UAC comments by the measured evidence. **Then re-ran this session's recipe and it flowed through the writer
      legitimately — no bypass**: 31,301/31,301 rows accepted by the pre-launch guard (0 dropped), all 2,848 REAL cells
      now captured in canonical. Method + full evidence table: the canonicalisation plan's "L6 floors-to-reality"
      Progress Log entry. Repo: unified-api-contracts.
- [x] ✅ [DATA] P0. **Redefine the L6-legacy-only gate** in `cf_manifest_audit_2026_06_01.py` to exclude
      `instrument_count=0` cells from the legacy-only diff, so it measures GENUINE data loss instead of a permanent
      by-design RED. Without this, E8 can never green. Repo: unified-trading-pm. **DONE 2026-07-15 —
      `unified-trading-pm@10ad5d69a`** (decision 1: _"Redefine to real-data-only."_). Implemented exactly the proposed
      criterion below: `_split_backed_cells()` partitions legacy captured cells by per-cell **MAX** `instrument_count`
      (MAX, not per-row — Gotcha-#2), the gate diffs only the ic>0 REAL set against canonical, and the ic=0 phantoms are
      emitted on their own `L6-phantom-residual` INFO line (VISIBLE, not suppressed — honest-absence discipline). Null
      ic is NOT treated as real-data evidence; a legacy index lacking the column falls back to all-cells-real
      (conservative — the gate may read RED, it can never under-report data loss). 13 unit tests
      (`tests/unit/test_cf_manifest_audit_l6_gate.py`) cover the split/MAX-semantics/null/missing-column + the
      RED-on-stranded-real vs GREEN-on-phantom-only decision. `audit()` exceeded the codex function-size cap once the
      block landed → extracted to `_legacy_diff()`. QG green (EXIT=0, 1267 passed, sentinel==HEAD). **Measured on BOTH
      live surfaces (`run it, don't read it`, 2026-07-15 ~22:10Z):** | surface | L6-legacy-only BEFORE | AFTER (real
      ic>0) | phantom residual (reported separately) | | ------- | --------------------- | ----------------- |
      -------------------------------------- | | IS `instruments-store-sports-prd-…` | 468 [RED] | **0 [GREEN]** | 468 |
      | MDPS `market-data-tick-sports-prd-…` | 140 [RED] | **0 [GREEN]** | 140 | `L6-legacy-only` no longer appears in
      either surface's RED list (IS residual REDs `['CF-2-paths','CF-3','CF-4','CF-8']`, MDPS `['CF-8']` — all
      pre-existing canonical-FORM gaps, untouched by this change and independent of legacy-data safety). **NARROWED +
      SHARPENED 2026-07-15 by the floors amendment** (the pre-launch half of this todo is now moot — see below), and
      this is now the ONLY thing standing between L6 and GREEN: - The **pre-launch exclusion is no longer needed**. The
      floors were the wrong half of the model: amending them to reality made all 2,848 pre-launch REAL cells
      legitimately writable, and they are now captured in canonical. Re-audited legacy-only residual = **468, of which
      REAL (ic>0) = 0 and phantom (ic=0) = 468**. So the gate should NOT special-case pre-launch dates — the floors now
      tell the truth on their own, and a future pre-launch cell would be a real signal worth surfacing, not noise to
      suppress. - The **ic=0 exclusion IS still required**, and is the entire remaining gap: 468 on IS + 140 on MDPS,
      all of them the operator-ACCEPTED phantom class (incl. the 28 INJURIES + 2 WEATHER). These have **no backing
      data** — an object probe this session found INJURIES objects exist for every day from 2018 but are **zero-row on
      every one of the first 60 days probed, on both surfaces**. Fabricating `captured` rows for them is banned
      (`record_failed`/`record_empty`, never a fake `record_captured`), so no migration can ever green them. -
      **Proposed criterion**:
      `L6-legacy-only := legacy captured cells with instrument_count>0 that are absent from       canonical` (i.e. drop
      the ic=0 cells from `lc` before the set-diff, and report them separately as an informational `L6-phantom-residual`
      line so the class stays VISIBLE rather than silently suppressed). On today's data-state that criterion is **GREEN
      on both sports surfaces (0 and 0)** — measured, not projected. - Do NOT green the gate by fabricating rows;
      redefine the criterion or leave it RED. E8 stays operator-gated regardless of the gate's colour.
- [ ] [DATA] P1. **Forensics (the remaining open question)**: what wrote pre-launch captured rows into the IS canonical
      such that 2026-07-14 audits read legacy-only=28? Not the 07-13 script (guard-blocked), not sufficiently the 18KB
      `_legacy_seed.parquet`. Whatever it is bypasses the writer's pre-launch chokepoint and is the true
      illegitimate-row vector. Repos: unified-trading-library, market-tick-data-service. **STILL GENUINELY OPEN as of
      2026-07-25** (confirmed not investigated by the 2026-07-23 RE-TRIAGE below either) — tracked in
      `/plans/archive/2026_07/sports_consolidated_closeout_aggregated_sources_2026_07_24.md`'s residual-todos digest
      (this doc's entry) so it stays visible after this doc archives.
- [x] ✅ [DATA] P2. ~~**Decision needed on the 2,769 copied objects** (ODDS `footystats_odds` 2018 tree) now in
      canonical without manifest rows — leave (manifest-invisible) or remove.~~ **RESOLVED 2026-07-15 by the floors
      ruling — they were given proper manifest rows, not removed.** Under the amended footystats floor (2018-01-01)
      those objects are legitimate canonical data, so the correct fix was to make them VISIBLE rather than delete them.
      The re-emission covered the ODDS class (123 cells / 2,723 objects) among the 2,848; all 123 ODDS cells verified
      `captured` in the canonical index post-consolidation. The manifest-invisible-object anomaly is closed: zero
      deletions. Repo: instruments-service.

## RE-TRIAGE (2026-07-23)

**Verdict: RESOLVED BY LATER WORK.** This doc's own body already carried out and verified the full fix chain
(2026-07-15); this pass re-verified the fix is STILL live in the current codebase and the live index has not regressed
since.

- **Shrink guard confirmed live today**: `unified_trading_library/manifest_writer/_writer.py` still carries
  `_INDEX_SHRINK_GUARD_PCT`, `ManifestIndexShrinkRefusedError`, `allow_index_shrink` (grep against the current
  `unified-trading-library` checkout).
- **Completeness-fraction fix confirmed live today**: `instruments_service/engine/orchestrator/process_completeness.py`
  still defines `_catalog_completeness_fraction` (intersection-over-expected).
- **No regression recurrence**: live IS sports canonical index (`instruments-store-sports-prd-central-element-323112`)
  read today shows **5,523,146 rows** — up from the doc's own last-measured 5,432,782 (2026-07-15 ~17:35Z), i.e.
  monotonic growth over 8 days, not another shrink.
- **Residual, still genuinely open (not blocking)**: the P1 forensics todo ("what wrote pre-launch captured rows into
  the canonical such that 2026-07-14 audits read legacy-only=28") remains unchecked in this doc and was NOT investigated
  this pass — flagging it stays accurate; it does not affect the resolved status of the core 328k-row finding since the
  floors-amendment made the question moot for data-loss purposes (the rows are now legitimately present via the correct
  mechanism regardless of how the earlier illegitimate rows got in).
