---
doc_type: issue
title:
  Sports canonical FIXTURE_EVENTS — 4,991 manifest rows claim capture_status=captured with ZERO backing GCS object
  (concentrated 2019-2020)
summary: >-
  Full census (43,233 canonical FIXTURE_EVENTS objects, sports_satellite_ao_dispatch_batch2-031's schema-heterogeneity
  re-fetch todo) found 4,991 (11.5%) manifest rows marked capture_status=captured for which NO object exists at any
  candidate path (incl. the legacy v1 archive) — confirmed via direct spot-checks, not a census-script bug. Concentrated
  in 2019-2020 (~58% of that 2-year window's manifest volume). This is a manifest-integrity defect distinct from the
  schema-heterogeneity defect the parent todo targets — a consumer trusting `capture_status=captured` for these rows
  reads a false-positive "data exists" for ~5k cells that are actually empty.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, data-correctness, fixture-events, manifest-integrity, phantom-rows, canonical]
related:
  [
    /plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
  ]
created: 2026-07-25
priority: P1
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: instruments-service@e0b48bc2 (2026-07-26, sports_satellite_ao_dispatch_batch5-011)
source: ["sports_satellite_ao_dispatch_batch2-031 full census, slot 2, 2026-07-25"]
---

# Sports canonical FIXTURE_EVENTS phantom manifest rows (2019-2020 concentrated)

## What was found

While censusing every canonical `entity=fixture_events` object's schema for the parent todo (schema-heterogeneity
re-fetch), the census read all 4 candidate paths (canonical + pipeline_mode-aware + legacy `sports_reference_v1_archive`
fallback) per manifest row and found **4,991 of 43,233 `capture_status=captured` rows (11.5%) have no backing object at
any candidate path**.

**Not a census-script artifact** — the first version of the census script conflated this with transient connection-pool
read errors; that bug was found and fixed (retry + per-thread client + a distinct `read_error` bucket) before the full
run. The 4,991 count is from the fixed script with `errors=0` reported. Spot-checked directly via `gcloud storage ls`
for multiple specific (day, league) pairs (e.g. `day=2019-01-07`, `PRIMEIRA_LIGA`/`FA_CUP`/`LA_LIGA`/others): the
`pipeline_mode=batch_api_football/` prefix for that day contains ONLY `entity=fixtures_outcomes/` and
`entity=fixtures_schedule/` — zero `entity=fixture_events/` folder at all, for any league, that day.

**Year concentration** (from the full manifest, not just the missing subset):

| year  | captured manifest rows | note                                                |
| ----- | ---------------------: | --------------------------------------------------- |
| 2018  |                      4 |                                                     |
| 2019  |                  3,872 | missing-count plateaued at 4,991 within this + 2020 |
| 2020  |                  4,760 |                                                     |
| 2021  |                  6,847 | canonical_13col starts dominating from here         |
| 2022+ |              ~6,300/yr | overwhelmingly canonical, low missing rate          |

The progress log of the census run shows `missing` climbing to exactly 4,991 by object #8,000 (≈ the combined 2019+2020
volume) and staying flat for the remaining ~35,000 objects — i.e. this defect is essentially confined to the 2019-2020
window, not spread evenly across the corpus.

## Why this matters

Any consumer trusting the manifest's `capture_status=captured` for these ~5k cells reads a false "data exists" —
identical failure shape to the already-documented `instrument_count` semantic drift (issue doc
`canonical_player_stats_fixture_events_quality_2026_07_16.md` defect 3) for the same 2019 era, suggesting a shared root
cause in that generation's writer/manifest-recording path, not an independent coincidence.

## What this is NOT

Not the schema-heterogeneity defect the parent todo (`sports_satellite_ao_dispatch_batch2-031`) targets — that todo's
12,603 genuinely-present non-canonical objects (5-col stub / 9-col named / 10-col af_-prefixed) are handled separately
via the real re-fetch campaign (see that plan's Progress Log for the recovery-ids parquet + launch). This doc is scoped
ONLY to the rows with literally zero backing object.

## Recommended remediation

1. Determine root cause: did the 2019-2020-era writer ever actually persist `entity=fixture_events` objects for these
   cells, or did it mark `capture_status=captured` without a corresponding write (a writer bug), or were the objects
   since deleted by an untracked cleanup? Check `written_at`/`enumerator_run_id` on a sample of the 4,991 rows against
   deploy history for that era.
2. Once root cause is known: either (a) genuinely re-fetch these ~5k cells from api-football (same mechanism as the
   schema-heterogeneity re-fetch, `--recovery-fixture-ids`) if the fixtures are recoverable, or (b) flip these rows'
   `capture_status` to `attempted_failed`/`expected_unattempted` (honest-absence) if genuinely unrecoverable — do NOT
   leave them silently mis-marked as `captured`.
3. Cross-reference against the already-known `instrument_count` semantic drift finding for the same era — one systemic
   2019-era writer-generation audit may explain both.

## Todos

- [x] [DATA] P1. Root-cause the 4,991 phantom `capture_status=captured` FIXTURE_EVENTS rows (2019-2020 concentrated) —
      determine whether the writer ever persisted these objects, then either re-fetch or honestly re-mark
      `capture_status`. (repo: instruments-service). **Done when**: root cause documented, and every one of the 4,991
      rows either has a real backing object or an honest non-`captured` status. ✅ 2026-07-26 —
      `instruments-service@e0b48bc2` (see RESOLVED section below).

## RESOLVED 2026-07-26

**Re-derived count**: an exhaustive re-census (3-retry existence check across all 3 candidate paths — canonical,
pipeline_mode-aware, legacy `sports_reference_v1_archive` — per row,
`scripts/census_fixture_events_phantom_missing_2026_07_26.py`) found **4,996** captured rows with no backing object (the
original 4,991 was a close undercount from the earlier pilot census; this run is exhaustive with 0 read errors). Year
concentration confirmed: 2018=4, 2019=3,865, 2020=1,127.

**Root cause — NOT the hypothesized 2019-era writer bug.** All 4,996 rows' `written_at` timestamps fall in a narrow
2026-07-15..2026-07-25 window, with **ZERO overlap** against the `written_at` values of the 38,264 genuinely-backed
FIXTURE_EVENTS captured rows for the same data_type. This proves the phantom rows were never touched by the original
per-fixture capture writer at all — they are a manifest-only artifact of a 2026-07 sports manifest
migration/reconciliation pass (candidate: the CF11 api_football reconcile, `instruments-service@87d1a353`, timestamped
2026-07-15 18:52 UTC — matches the lower bound of the phantom rows' written_at range) that recorded a plausible non-zero
`instrument_count` (e.g. 10, 12, 20) for these (date, league_id) cells without a paired successful GCS write. No
archived process log or source dataframe ties the recorded count back to a real object, and this task's own exhaustive
existence check independently reconfirms absence at every candidate path for all 4,996 rows — so recovery via direct
verification is not possible with what's on disk today.

**Resolution — honest-absence reflip (not a re-fetch in this task).** Per
`/codex/02-data/honest-absence-downstream-handling.md` and this doc's own remediation option (b), flipped all 4,996
rows' `capture_status` from `captured` → `attempted_failed` (error_reason
`fixture_events_phantom_manifest_reflip_2026_07_26`, `attempted_at` re-stamped to now), via
`scripts/reflip_fixture_events_phantom_rows_2026_07_26.py` — backup-then-write CAS-safe manifest mutation targeting the
exact (date, league_id) key set from the census (not a heuristic re-derivation), mirroring the sibling precedent
`flip_phantom_to_attempted_failed.py`. This re-opens all 4,996 cells to the standard api_football per-fixture
orchestrator's normal re-fetch path — no manual re-fetch campaign was run in this task (out of scope for a
single-session data-engineering todo: a live re-fetch campaign needs credentialed VM dispatch, not this doc's remit).

**Verification**: manifest backup retained at
`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.20260726-004618.bak.parquet`.
Post-apply state: 38,264 FIXTURE_EVENTS rows remain `capture_status=captured` (spot-checked 100/100 sampled rows
confirmed a real backing object — no full re-walk, per single-walk discipline) and exactly 4,996 rows now carry
`capture_status=attempted_failed` + the reflip error_reason (spot-checked 20/20 sampled rows confirmed still genuinely
absent, as expected). 0 rows remain silently mis-marked `captured` with no backing object.

**Cross-reference to `instrument_count` semantic drift**: this defect is NOT the same era/mechanism as the
`canonical_player_stats_fixture_events_quality_2026_07_16.md` defect-3 finding (that finding is about the ORIGINAL
2019-era writer generation; this one is a 2026-07 migration-era manifest artifact) — no shared root cause established;
noting this explicitly so a future reader doesn't conflate the two eras.

## Codex SSOTs

Executes the same manifest-integrity principle already codified in
`/codex/02-data/availability-manifest-and-data-status.md` (4-state `capture_status`, no silent placeholders) +
`/codex/02-data/honest-absence-downstream-handling.md`.
