---
doc_type: issue
title:
  rescan_sports_fixtures_canonical.py's FIXTURES handler still finds zero real blobs — missing the canonical
  pipeline_mode= prefix segment
summary: >-
  Even after fixing the per-league suffix-match defect (archived;
  /plans/archive/2026_08/issues/rescan_sports_fixtures_canonical_per_league_suffix_match_broken_2026_08_14.md) and a
  stale hardcoded bucket name (both instruments-service@622b641628), live-bucket verification found
  `_list_entity_blob_paths()`'s FIXTURES prefix still finds zero real objects for current dates: canonical
  fixtures_schedule writes live under an intervening `pipeline_mode=batch_api_football/` path segment
  (`day={D}/pipeline_mode=batch_api_football/entity=fixtures_schedule/league={L}/fixtures_schedule.parquet`, confirmed
  95 real blobs for 2026-08-01) that the handler's `prefix_suffix` (`entity=fixtures_schedule/`, no pipeline_mode
  segment) never matches. `_load_venue_to_leagues()` in the SAME file already handles this exact canonical-vs-legacy
  split (tries the `pipeline_mode=` prefix first, falls back to the bare legacy prefix) — `_list_entity_blob_paths()`
  needs the same treatment, but doing it correctly for a multi-day range scan (where `date_str is None` and the range
  can span the 2026-07-14 cutover, mixing canonical- and legacy-shaped dates in one scan) needs its own design pass, not
  a bolt-on.
created: "2026-08-14"
last_updated: "2026-08-14"
author: slot-18
assigned_vm: planning
execution_scope: orchestrator-agent
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, manifest, rescan, fixtures-schedule, pipeline-mode, follow-up]
related:
  [
    /plans/archive/2026_08/issues/rescan_sports_fixtures_canonical_per_league_suffix_match_broken_2026_08_14.md,
    /plans/active/sports_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
parent_epic: sports_master
priority: P2
locked_by:
resolved_by: instruments-service@6e81874504
source: [instruments-service/scripts/rescan_sports_fixtures_canonical.py]
status: open
drift_direction: advance-code
depends_on: []
archive_exempt: true
---

# rescan_sports_fixtures_canonical.py FIXTURES handler missing the canonical pipeline_mode= prefix segment

## What I found

While live-verifying the per-league suffix-match fix (archived;
`/plans/archive/2026_08/issues/rescan_sports_fixtures_canonical_per_league_suffix_match_broken_2026_08_14.md`,
instruments-service@622b641628) against the real bucket
(`resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")` ==
`instruments-store-sports-prd-central-element-323112` — also fixed a separate stale-hardcoded-bucket-name bug in the
same commit, the script's `BUCKET_NAME` constant previously pointed at a nonexistent bucket lacking the `-prd-`
segment), `_list_entity_blob_paths(storage, bucket, _FIXTURES_HANDLER, "2026-08-01")` still returned **zero** matches,
even with both prior fixes live.

Direct bucket probe confirms why:

```
sports_reference/by_date/day=2026-08-01/pipeline_mode=batch_api_football/entity=fixtures_schedule/  -> 95 blobs
sports_reference/by_date/day=2026-08-01/entity=fixtures_schedule/                                     -> 0 blobs
```

`_FIXTURES_HANDLER.prefix_suffix = "entity=fixtures_schedule/"` is appended directly after `day={D}/` with no
`pipeline_mode=` segment, so `_list_entity_blob_paths`'s GCS-prefix listing (`day={D}/entity=fixtures_schedule/`) never
reaches the real, canonically-written blobs at all — a prefix mismatch, upstream of the per-league suffix issue the
sibling doc fixed.

This is NOT a new pattern in this file: `_load_venue_to_leagues()` (used by the WEATHER scanner to join venue→league)
already handles the identical canonical-vs-legacy split correctly, per its own docstring: "fixtures_schedule is written
per-league only... since the 2026-07-14 FIXTURES entity-split cutover... canonical pipeline_mode= prefix first, legacy
prefix for pre-migration dates" — it tries `day={D}/pipeline_mode=batch_api_football/entity=fixtures_schedule/` first
and falls back to the bare `day={D}/entity=fixtures_schedule/` only if that's empty
(`sports_reference/by_date/day={D}/entity=fixtures_schedule/` is presumably still real for dates before the cutover).

WEATHER (`entity=weather/`) and XG (`entity=understat_xg/`) were spot-checked at the same date (2026-08-01) under BOTH
the canonical and legacy prefix shapes — both zero either way, consistent with the sibling doc's claim that they are
genuinely bare per-day files unaffected by this split (inconclusive for THIS specific date since neither prefix had any
data that day, but no evidence either handler needs the `pipeline_mode=` treatment).

## Why it matters

Same as the sibling per-league-suffix doc: `rescan_sports_fixtures_canonical.py --entity-type FIXTURES` silently finds
"0 files" for CURRENT/canonical dates and does nothing, with no error — the per-league suffix fix was necessary but is
not yet sufficient on its own; this prefix gap is upstream of it (a wrong prefix means the per-league suffix logic never
even sees a real blob to test its match against).

## Recommended decision

Apply the SAME canonical-prefix-first / legacy-prefix-fallback pattern `_load_venue_to_leagues()` already uses, but
`_list_entity_blob_paths()` has two call shapes `_load_venue_to_leagues()` doesn't: (1) a single-date lookup (`date_str`
given) — straightforward, mirror the existing try-canonical-then-legacy-if-empty logic; (2) a **range scan**
(`date_str is None`, `date_start`/`date_end` used to filter afterward) that lists the WHOLE `FIXTURES_PREFIX` in one
call and can span dates on BOTH sides of the 2026-07-14 cutover — a single "try canonical, fall back to legacy if empty"
won't work here since a wide date range can genuinely need BOTH prefixes' blobs simultaneously, not an either/or. This
needs its own design: likely UNION matches from both a canonical-prefixed listing AND a legacy-prefixed listing when
doing a range scan (with per-league suffix-tolerant matching from the sibling fix applied to both), while keeping the
simpler try-then-fallback shape for the single-date case. Verify against the real bucket (prefixes above) before/after,
for at least one date pre- and one date post- the 2026-07-14 cutover.

## Todos

- [x] ✅ [CODE] P2. Add canonical-prefix-first / legacy-prefix-fallback support to `_list_entity_blob_paths()` in
      `instruments-service/scripts/rescan_sports_fixtures_canonical.py`'s FIXTURES path (mirror
      `_load_venue_to_leagues()`'s existing pattern for the single-date case; design + implement the range-scan case to
      UNION canonical + legacy matches rather than either/or, since a wide date range can span the 2026-07-14 cutover).
      Keep WEATHER/XG on their existing single-prefix behavior (no evidence they need this). Add a regression test
      covering both the single-date and range-scan shapes. Verify against the real bucket
      (`instruments-store-sports-prd-central-element-323112`) for a pre-cutover and a post-cutover date before/after.
      Repo: instruments-service. — instruments-service@6e81874504

## Progress Log

- 2026-08-14 (slot-31): Added `_EntityHandler.pipeline_mode_segment` (FIXTURES only); single-date lookup now tries the
  canonical `day={D}/pipeline_mode=batch_api_football/entity=fixtures_schedule/` prefix first, falling back to the bare
  legacy prefix only if canonical is empty. Investigated the range-scan case (`date_str is None`): it already lists the
  whole `FIXTURES_PREFIX` with no per-day prefix narrowing, so it inherently reaches blobs shaped either way via the
  existing per-blob suffix/substring match — no separate union logic was needed there (documented in code). Added 3
  regression tests (canonical-first, legacy-fallback, range-scan-unions-both) — 11/11 unit tests pass. Verified live
  against `instruments-store-sports-prd-central-element-323112`: 2026-08-01 now resolves 90 real blobs via the canonical
  prefix (was 0 before this fix); 2020-06-10/2022-01-15/2023-06-01/2024-09-15 also resolve via the canonical prefix
  (legacy_raw=0 at every date probed — the live bucket currently has no genuinely legacy-shaped FIXTURES blobs, the
  fallback branch is a safe no-op there but still covered by the synthetic unit test).
