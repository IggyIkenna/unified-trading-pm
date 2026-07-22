---
doc_type: issue
title:
  Sports B_legacy_duplicate triage (34,385 reference-bucket objects) — ZERO pass the 5-part delete-safety proof; every
  sub-population fails for a different, evidenced reason (stale-already-deleted / pre-floor fabrication / live reader /
  content-incomplete twin)
summary:
  'Read-only 5-part-proof triage of the 34,385 `B_legacy_duplicate` rows flagged by `migration_orphan_sweep_sports.py
  --bucket reference` (estate_orphan_assessment_2026_07-21 todo 2), against
  `codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. The population splits into two path shapes —
  `sports_reference/fixtures/day={D}/[league={L}/]fixtures.parquet` (flat, non-`by_date`, 32,835 rows) and
  `sports_reference_v2/by_date/...` (the 2026-04-28 v1→v2 migration staging tree, 1,550 rows) — and each splits again on
  the ratified 2020-06-06 sports data floor (day &lt; 2020-06-06 = "every sports source" per operator ruling
  2026-07-21). **Result: 0 of 34,385 rows achieve `yes-twin-confirmed` or `yes-after-verify`.** (1) 4,735 flat pre-floor
  rows are STALE AUDIT ENTRIES — 0/15 sampled still exist on GCS; they were already deleted by the independent,
  already-executed 2026-07-21 pre-floor wipe (`deployment-service@78a0aa4`, which logged deleting exactly
  `sports_reference/fixtures 4,735` objects — an exact count match). (2) 1,492 v2 pre-floor rows DO still exist (15/15
  sampled) with ZERO canonical twin at any path variant — these are pre-floor "fabrication-by-construction" per the
  standing floor ruling and belong in the SAME already-ruled wipe scope, not this duplicate-preservation framework — the
  wipe evidently never reached `sports_reference_v2/`. (3) 28,100 flat post-floor rows: Part 1 (twin exists) passes for
  98.3% at SOME `by_date/entity=fixtures/` object, but Part 4 (no live reader) FAILS categorically — TWO confirmed live
  readers of this exact legacy path shape: `instruments-service/instruments_service/engine/orchestrator/
  sports_reference_fixtures.py:139` (`_ensure_canonical_fixtures_for_override`, an active cost-saving fallback) and
  `deployment-service/deployment_service/cli/utils/data_status_sports.py:42,74` (`_load_fixture_counts_for_date`''s
  last-resort fixture-calendar fallback, reachable specifically when the 3 newer path shapes have zero objects — true
  for at least 478 of these 28,100 rows, which have NO canonical twin at all and are therefore this reader''s ONLY data
  source for that date). (4) 58 v2 post-floor rows: Part 1 fails for 40/58 (no canonical object under `by_date/` at
  all); for the other 18, an exhaustive per-league row-count sum shows the "canonical" side holds a tiny FRACTION of the
  v2 object''s row count in every case (e.g. day=2026-04-02: legacy=397 rows vs twin=8 rows across 4 objects) — Part 2
  (content verify) fails 58/58. **Also found: ACROSS ALL 3,396 distinct (day, entity) pairs checked, ZERO (0.0%) have a
  `pipeline_mode=`-tagged canonical object** — the v9 pipeline_mode-migration never reached FIXTURES/FIXTURE_STATS for
  this population at all. Human-only delete disposition is NOT executed here; the recommendation is migrate-forward /
  extend-the-existing-wipe / repoint-readers first, never delete-as-is.'
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, deployment-service, unified-trading-library, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    sports,
    orphan,
    legacy-duplicate,
    delete-safety,
    five-part-proof,
    pre-launch-floor,
    data-floor,
    migration,
    canonicalisation,
    read-only,
  ]
related:
  [
    estate_orphan_assessment_2026_07_21.md,
    sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md,
    ../../codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    ../../codex/02-data/sports-2020-06-data-floor.md,
    ../../codex/02-data/sports-gcs-path-ssot.md,
    ../sports_master_closeout_2026_07_21.md,
    ../migration_verification_orphan_safety_2026_06_10.md,
  ]
created: 2026-07-22
last_updated: 2026-07-22
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: estate_orphan_assessment_2026_07_21.md todo 2 ("Triage the 34,385 sports LEGACY_DUPLICATE")
depends_on: []
---

# Sports B_legacy_duplicate triage — 2026-07-22

> **Read-only investigation. No GCS object, manifest row, or code was deleted, moved, or modified in producing this
> report.** Two small audit-trail parquets were written under `_index/audit/` (the same durable-report convention the
> sweep itself uses) — see § Artifacts. Any delete disposition below is a SUGGESTION per
> `codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — **prod-bucket deletes are a human-only hard stop** and
> none are executed here.

## 0. Headline

**0 of the 34,385 `B_legacy_duplicate` rows pass all five parts of the delete-safety proof.** Every sub-population fails
for a _different_, independently-evidenced reason — this is not a blanket "be conservative" default, it is four
distinct, measured failure modes:

| Sub-population                      |       Rows | Fails on                                                       | Why                                                              |
| ----------------------------------- | ---------: | -------------------------------------------------------------- | ---------------------------------------------------------------- |
| flat, pre-floor (day < 2020-06-06)  |      4,735 | N/A — **objects no longer exist**                              | Already deleted by the independent 2026-07-21 pre-floor wipe     |
| v2 staging, pre-floor               |      1,492 | Part 1 (no twin) + **out of scope** (floor policy applies)     | Fabrication-by-construction per the standing floor ruling        |
| flat, post-floor (day ≥ 2020-06-06) |     28,100 | **Part 4 (live reader)** — categorical, regardless of Part 1/2 | 2 confirmed live readers of this exact path shape                |
| v2 staging, post-floor              |         58 | Part 1 (40/58) + **Part 2 content** (18/18 of the rest)        | Twin, where found, holds ~2-10% of the legacy object's row count |
| **Total**                           | **34,385** |                                                                |                                                                  |

## 1. What the sweep already checked (and did NOT check)

`instruments-service/scripts/migration_orphan_sweep_sports.py` (`classify_reference_object`,
`_classify_definitions_object`, `is_covered_sports`) classifies an object `B_legacy_duplicate` when its path is a
**legacy shape** (either `sports_reference/{entity}/day={D}/[league={L}/]{entity}.parquet` — the flat, non-`by_date`
tree, or anything under `sports_reference_v2/`) **AND** `is_covered_sports(day, data_type, league)` returns `True`.

`is_covered_sports` only asks: _does the consolidated MANIFEST (`_index/availability_index.parquet`) have a `captured`
row for this `(date, data_type)` cell, with a `(venue, league, timeframe)` pattern that matches (blank-is-wildcard on
either side)?_ **It never touches GCS.** A `True` here proves "the manifest believes this cell was captured somewhere" —
it does **not** prove a canonical-shaped object physically exists, nor that its content matches the flagged legacy
object. This is precisely the "legacy-COPIED-not-MOVED" trap the delete-safety protocol's Part 5 exists to catch
(`codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §1 Part 5): _"the manifest `_index` is CELL-KEYED and
path-agnostic — it does not by itself tell you whether a cell's data sits at a canonical path."_ This triage exists to
close that exact gap for sports.

Distinct-cell counts (`instruments-service/scripts/read_audit.py`-style groupby on the durable audit parquet, no
re-walk):

```
obj_class counts (whole audit parquet, 286,299 rows):
  E_orphan_real           186,971
  C3_pre_launch_window     64,943
  B_legacy_duplicate       34,385   <- this triage

B_legacy_duplicate shape × entity × data_type:
  sports_reference/fixtures/day=...  (flat, non-by_date)  entity=fixtures        FIXTURES        32,835
  sports_reference_v2/...            (v2 staging tree)    entity=fixtures        FIXTURES           796
  sports_reference_v2/...            (v2 staging tree)    entity=fixture_stats   FIXTURE_STATS      754
```

Day range: flat 2019-01-16 → 2026-05-31 (2,621 distinct days, 83 leagues); v2 2018-01-02 → 2026-04-20 (398 distinct days
— exactly the day-count the 2026-04-28 cutover script reports as 100% succeeded, see §3).

## 2. The pre-floor cross-reference (the finding that reframes this whole triage)

The sweep's classifier checks `is_covered_sports` **before** `_is_pre_launch(dt, day)` — so a pre-floor day whose
manifest cell is (stale-but-not-yet-pruned) `captured` gets `B_legacy_duplicate`, never `C3_pre_launch_window`, even
though per the operator's 2020-06-06 floor ruling **("clamped for every sports source", 2026-07-21, restated verbatim in
the sibling doc `sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md`)** that data is
fabrication-by-construction regardless of manifest state. This is the same registry-gap failure class as the sibling
doc's `E_orphan_real` misclassification, manifesting on the `B` class instead of `E`.

Splitting the 34,385 rows on the floor (`day < "2020-06-06"`):

```
shape  pre_floor   rows
flat   True         4,735   (days 2019-01-16 .. 2020-06-05, 472 distinct days)
flat   False       28,100   (days 2020-06-06 .. 2026-05-31, 2,149 distinct days)
v2     True         1,492   (days 2018-01-02 .. 2020-05-25, 382 distinct days)
v2     False           58   (days 2024-12-24 .. 2026-04-20, 16 distinct days)
```

**The flat pre-floor count, 4,735, is an EXACT match** to the `sports_reference/fixtures 4,735` figure the 2026-07-21
pre-floor GCS wipe logged as deleted (`deployment-service@78a0aa4`, `plans/active/sports_master_closeout_2026_07_21.md`
§"PENDING EXECUTION" + Progress Log: _"instruments-store-sports-prd = 437,124 (`sports_reference/by_date` 398,240 ·
`sports_reference/fixtures` 4,735 · `instrument_availability/by_date` 34,149)"_). A live spot-check
(`gcs_describe_object` on 15 random flat pre-floor URIs from the audit parquet) confirms: **0/15 still exist.** These
4,735 rows in the durable `orphan_sweep_sports.parquet` audit are **stale entries for objects that no longer exist** —
the sweep ran (or its snapshot predates) the same-day wipe. No disposition applies; there is nothing to delete, migrate,
or preserve. Recommend a rescan to retire these from the audit report (§7 todo 4).

The v2 pre-floor 1,492 rows are a DIFFERENT outcome: the same live spot-check found **15/15 still exist** — the
2026-07-21 wipe's scope (`sports_reference/by_date` + `sports_reference/fixtures`) never touched `sports_reference_v2/`.
These are real, present objects holding pre-floor data. Per the standing floor ruling they are not a "legacy duplicate
awaiting twin-verified delete" question at all — **they are the same fabrication-by-construction category already being
wiped elsewhere**, just under a prefix the existing wipe missed. Recommendation: fold these 1,492 into the existing
pre-floor-wipe operator-gated process (§7 todo 2), not this delete-safety framework.

## 3. Five-part proof — flat, post-floor (28,100 rows, the bulk of the live population)

**Part 1 (twin resolves via `gcs_describe_object` / true prefix listing, not path construction).** An exhaustive
prefix-listing check (`sports_reference/by_date/day={D}/entity=fixtures/`, one `list_blobs` per distinct day — 2,149
days, not per-row) found **≥1 object present for 27,622/28,100 rows (98.3%)**; genuinely zero for **478/28,100 (1.7%)**.
Of everything found, **0% carry a `pipeline_mode=` segment** — see §5.

**Part 2 (content verify).** A 40-row stratified sample (`verify_twins.py`, pipeline_mode-aware candidate probe) found a
twin for 31/40 (77.5%), and **31/31 of those had `twin_rows ≥ legacy_rows`** (often far more — e.g.
day=2024-08-31/ARGENTINA_PRIMERA_NACIONAL: legacy=2 rows, twin=310 rows), consistent with the legacy per-league file
being an early/partial snapshot the canonical write later superseded with a fuller capture. **Content, where checked, is
not divergent** — this population would clear Part 2 on its own.

**Part 3 (grep-then-READ: no live writer).** No production code constructs `sports_reference/{entity}/day=` (flat,
non-`by_date`) as a write target — grep across `instruments-service/instruments_service`,
`market-tick-data-service/market_tick_data_service`, `unified-trading-library`, `features-service`, `deployment-service`
finds zero write call sites; the only writers of this shape were the retired `migrate_sports_per_league.py`-era scripts.
**Part 3 PASSES.**

**Part 4 (grep-then-READ: no live reader) — FAILS. This is the categorical blocker.** Two independent, currently
reachable readers of this exact path shape:

1. `instruments-service/instruments_service/engine/orchestrator/sports_reference_fixtures.py:139` —
   `_ensure_canonical_fixtures_for_override`:
   ```python
   _old_path = f"sports_reference/fixtures/day={date}/fixtures.parquet"
   _old_blob = _storage.bucket(bucket).blob(_old_path)
   if _old_blob.exists() and not redo_all:
       ...  # read + copy forward into entity=fixtures/ (a cost-saving old-path branch, zero API calls)
   ```
   Called from `_resolve_fixture_ids` (line 83), the live fixture-ID-resolution entry point. Read here IS conditional
   (only when canonical per-league data is not yet found AND `redo_all=False`), but it is a genuine, reachable,
   non-hypothetical production code path — not a docstring or a dead branch.
2. `deployment-service/deployment_service/cli/utils/data_status_sports.py:32-42,72-75` —
   `_load_fixture_counts_for_date`'s **4-level fallback chain** (pipeline_mode canonical → bare `entity=fixtures` →
   `entity=fixtures_schedule` split → **`_FIXTURES_LEGACY_PREFIX = "sports_reference/fixtures/day={date}/"`**, scanned
   via `_scan_fixture_prefix` for every `league=` child, i.e. the exact per-league flat shape). Reached "if still
   nothing found" after the first three levels — which is exactly the condition **478 of these 28,100 rows already
   satisfy** (zero `by_date/` objects of any kind exist for those dates), making this reader their **sole surviving data
   source**, not a redundant fallback over a richer canonical copy.

Per the protocol: _"A location with no writer may still have live readers, and deleting under a live reader is a
production incident, not a cleanup"_ and _"Part 4 fails 'loudly-broken' readers too"_ — a reader that is conditionally
reached is still a reader. **Disposition: `no-migrate-first` for all 28,100 rows**, regardless of the favorable Part 1/2
results above. Repoint or retire both fallback branches (or instrument them to prove they're never actually hit for
canonicalised dates) before any delete reconsideration.

## 4. Five-part proof — v2 staging tree, post-floor (58 rows)

Exhaustive (not sampled — small enough) check via `v2_postfloor_exhaustive.py`: per distinct (day, entity), list
**every** object under `sports_reference/by_date/day={D}/entity={entity}/` and sum footer row counts across all of them
(the correct comparison against a per-league-split canonical, vs. the v2 object's single bare/day-level row count).

- **Part 1**: 0 canonical objects at all for 40/58 (69%). For the other 18/58, 1-8 canonical per-league objects exist.
- **Part 2**: **0/58 pass.** Where a twin exists, its summed row count is a small fraction of the legacy object's:

  | day        | entity   | legacy_rows | canonical objects found                | twin_total_rows |
  | ---------- | -------- | ----------: | -------------------------------------- | --------------: |
  | 2026-03-18 | fixtures |         348 | 4 (of ~30+ leagues that play that day) |               9 |
  | 2026-04-02 | fixtures |         397 | 4                                      |               8 |
  | 2026-04-07 | fixtures |         189 | 7                                      |              11 |
  | 2026-04-20 | fixtures |         119 | 8                                      |               8 |

  `entity=fixture_stats` has **zero** canonical objects in every single one of the 58 rows checked.

- **Part 3/4**: no live writer or reader anywhere in production code for `sports_reference_v2/` — grep across every
  service package (`instruments-service`, `market-tick-data-service`, `deployment-service`, `features-service`,
  `unified-trading-library`) turns up references ONLY in one-off migration/verification scripts:
  `instruments-service/scripts/{cutover_sports_fixtures_v2_to_canonical,migration_orphan_sweep_sports, validate_sports_fixtures_v2_parity}.py`
  and
  `market-tick-data-service/market_tick_data_service/scripts/ {migrate_sports_canonical_v9,_migrate_sports_reconcile,verify_v1_archive_row_coverage_2026_06_27}.py`.
  **Parts 3+4 PASS** — this is the one sub-population with no live-code blocker.

**Disposition: `no-migrate-first` for all 58** — not because of a live reader, but because Part 1/2 fail: the v2 object
is frequently the ONLY (or far more complete) copy of that day's fixtures data. The 2026-04-28 cutover
(`cutover_sports_fixtures_v2_to_canonical.py`) reports 398/398 days succeeded, but its own logic only copies the
**bare** `fixtures.parquet`/`fixture_stats.parquet` files (no per-league fan-out) — it never touches the modern
per-league write shape these 16 recent v2 days are actually compared against, so "cutover succeeded" and "canonical
per-league coverage is complete" are two different claims. **Recommended action is migrate-forward (copy v2 rows into
canonical, filling the per-league gap), not delete** — this is a small, tractable population (16 days) for a targeted
follow-up.

## 5. Cross-cutting finding: 0% pipeline_mode= coverage across the whole checked population

`codex/02-data/sports-gcs-path-ssot.md` states live sports_reference paths carry a `pipeline_mode=` segment
post-migration (`…/entity={E}/…` under a `pipeline_mode={mode}` hive level), and
`delete_legacy_sports_objects_ 2026_06_24.py`'s docstring describes `migrate_sports_canonical_v9.py --apply` as having
"inserted `pipeline_mode=` into every object path." An exhaustive check across **all 3,396 distinct (day, entity)
pairs** backing this triage's 34,385 rows found **zero (0.0%)** with a `pipeline_mode=`-tagged object present. Whatever
the v9 migration covered, it evidently never reached FIXTURES/FIXTURE_STATS for this day range — worth a targeted check
by whoever owns that migration's completion tracking, separate from this triage's delete question.

## 6. Disposition summary (per the protocol's required checklist, §6)

```
Sub-population: flat legacy, pre-floor (4,735 rows)
Part 1 twin probe:   N/A — legacy objects themselves 0/15 sampled still exist (already deleted 2026-07-21)
Part 2 content:      N/A
Part 3 writers:      N/A
Part 4 readers:      N/A
Part 5 twin coverage: N/A
Disposition:         N/A — stale audit entries, not live delete candidates. Rescan to retire (§7 todo 4).
Hard stop:           none applicable (nothing to delete)

Sub-population: v2 staging, pre-floor (1,492 rows)
Part 1 twin probe:   gcs_describe_object across all path variants -> None, 1492/1492 (0% twin)
Part 2 content:      not evaluated (Part 1 already fails)
Part 3 writers:      grep -> 0 production hits; READ -> no live writer (PASS)
Part 4 readers:      grep -> 0 production hits; READ -> no live reader (PASS)
Part 5 twin coverage: 0% for this sub-population
Disposition:         no-migrate-first (Part 1 fails) — but SUBSTANTIVELY out-of-scope: pre-floor
                      fabrication-by-construction per operator ruling 2026-07-21, belongs in the
                      existing pre-floor-wipe process (§2), not a duplicate-preservation question.
Hard stop:           none of the 5 enumerated hard stops directly names this case; flagging per
                      "big finding" triage rule (cross-reference to an existing operator ruling).

Sub-population: flat legacy, post-floor (28,100 rows)
Part 1 twin probe:   exhaustive prefix listing, 2,149 days -> >=1 object for 27,622/28,100 (98.3%)
Part 2 content:      40-row sample -> 31/40 twin found, 31/31 twin_rows >= legacy_rows (PASS where checked)
Part 3 writers:      grep -> 0 production hits; READ -> no live writer (PASS)
Part 4 readers:      grep "sports_reference/fixtures" -> 2 production hits; READ ->
                      instruments-service/.../sports_reference_fixtures.py:139 (live, conditional read) +
                      deployment-service/.../data_status_sports.py:42,74 (live, last-resort fallback,
                      sole source for >=478 of these rows) -> READS=yes (FAIL)
Part 5 twin coverage: 98.3% (but coverage % is moot once Part 4 fails)
Disposition:         no-migrate-first (Part 4 FAILS categorically, overrides favorable Part 1/2)
Hard stop:           none of the 5 enumerated; a live-reader Part-4 fail per protocol §1 Part 4

Sub-population: v2 staging, post-floor (58 rows)
Part 1 twin probe:   exhaustive per-day prefix listing, 16 days -> >=1 object for 18/58 rows (31%)
Part 2 content:      exhaustive footer-sum -> 0/58 pass (twin_total_rows << legacy_rows in every case found)
Part 3 writers:      grep -> 0 production hits; READ -> no live writer (PASS)
Part 4 readers:      grep -> 0 production hits; READ -> no live reader (PASS)
Part 5 twin coverage: 31% object-presence, ~2-10% row-content coverage where present
Disposition:         no-migrate-first (Part 1/2 fail; small population, migrate-forward recommended)
Hard stop:           none

TOTAL: 0/34,385 rows at yes-twin-confirmed or yes-after-verify.
```

## 7. Recommendation (no delete executed — human-only per the hard-stop rule)

**No action in this doc deletes, moves, or modifies anything.** Every disposition above is `no-migrate-first` or N/A.
Recommended next steps, in priority order:

- [ ] 1. [OPERATOR] P1. **Rule on the 1,492 v2 pre-floor rows**: fold into the existing pre-floor-wipe scope (extend
      `deployment-service`'s `wipe_pre_floor_sports_2026_07_21.py`-style tool to also cover `sports_reference_v2/`), or
      confirm they're already covered by a follow-up pass. This is a policy-consistency question, not a fresh delete
      decision — the operator already ruled the underlying data category.
- [ ] 2. [DATA] P2. **Migrate-forward the 58 v2 post-floor rows** (16 days) into canonical per-league `entity=fixtures`
      / `entity=fixture_stats` — a small, tractable per-league fan-out (reuse `migrate_sports_per_league.py`'s
      per-fixture-league-join logic), not a delete. Re-run the sweep after to confirm these flip to `A_canonical`.
- [ ] 3. [CODE] P2. **Repoint or retire the two flat-legacy readers** before the 28,100 post-floor flat rows can be
      reconsidered for delete: (a) `sports_reference_fixtures.py:139`'s old-path branch — verify it is never actually
      reached for canonicalised dates (add a counter/log), or remove it now that canonical coverage is ~98%; (b)
      `data_status_sports.py`'s level-4 fallback — same treatment. Re-run Part 4 grep+READ after either change lands.
- [ ] 4. [REVIEW] P3. **Rescan `migration_orphan_sweep_sports.py --bucket reference`** to retire the 4,735 stale
      (already-deleted) flat pre-floor rows from the durable audit parquet, and to fix the classifier's
      `is_covered_sports`-before-`_is_pre_launch` ordering so pre-floor cells with a stale-captured manifest row
      classify `C3_pre_launch_window` instead of `B_legacy_duplicate` (mirrors the fix already shipped for the `E` class
      in `sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md`, `unified-api-contracts@46d865df` — this is
      the same bug on a different branch of the same function, not yet fixed there).
- [ ] 5. [REVIEW] P3. Cross-file `sports_master_closeout_2026_07_21.md`'s pending "MANIFEST prune" deferred task — the
      944,776 phantom pre-floor manifest rows it already tracks are the root cause of §2's misclassification here too;
      pruning them removes the `is_covered_sports` false-positive at the source.

## Artifacts (durable, read-only, mirror the sweep's own audit-parquet convention)

- `gs://instruments-store-sports-prd-central-element-323112/_index/audit/legacy_dup_triage_sports_2026_07_21.parquet` —
  per-row triage (34,385 rows: reason, twin_uri, twin_exists, content_match, disposition, note) from the first-pass
  triage script (pre-pipeline_mode-aware; superseded in nuance by §2-§4 above but retained as the per-row detail table).
  First-pass disposition counts: `no-migrate-first`=19,467, `no-still-authoritative`=14,918 (0
  `yes-twin-confirmed`/`yes-after-verify` — directionally consistent with the refined analysis above).
- Scratchpad working files (not durable, session-local): `b_legacy_duplicate.parquet`, `verify_results.json`,
  `prefix_check_results.json`, `v2_postfloor_detail.csv`, `b_final_merged.parquet` — available for re-derivation but not
  required reading; every number in this doc is reproducible from the durable GCS artifacts + the grep+READ citations
  above.

## Lesson (do not re-learn)

A sweep's "manifest says covered" check is necessary but not sufficient evidence for "safe to delete this legacy-shaped
object" — it proves the CELL was captured somewhere, never that a canonical-shaped OBJECT exists there today, nor that
its content is a subset of what's flagged as legacy. This is the second time in two days
(`sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md` being the first, on the `E` class) that the sports
sweep's classifier has needed a floor-aware or twin-existence-aware correction layered on top of its manifest-only
`is_covered_sports` check — the underlying pattern (manifest-coverage ≠ GCS-canonical-existence) is exactly what
`gcs-and-manifest-delete-safety-protocol.md` Part 5 names as the "legacy-COPIED-not-MOVED" trap, and it recurs anytime a
classifier or reconciler treats a manifest `captured` row as proof of anything beyond "captured somewhere, at some
point, per this data_type/day/league key."
