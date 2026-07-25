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
status: open
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
resolved_by:
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

- [ ] [DATA] P1. Root-cause the 4,991 phantom `capture_status=captured` FIXTURE_EVENTS rows (2019-2020 concentrated) —
      determine whether the writer ever persisted these objects, then either re-fetch or honestly re-mark
      `capture_status`. (repo: instruments-service). **Done when**: root cause documented, and every one of the 4,991
      rows either has a real backing object or an honest non-`captured` status.

## Codex SSOTs

No new durable contract. Executes the same manifest-integrity principle already codified in
`/codex/02-data/availability-manifest-and-data-status.md` (4-state `capture_status`, no silent placeholders).
