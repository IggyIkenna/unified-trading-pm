---
doc_type: issue
title:
  "Sports orchestration does per-date/per-league live GCS probes instead of manifest reads across 5 files, 17 call sites
  — measured backfill cost is tens of minutes to ~1-2 hours, not a single 60-130x-fixable function"
summary: >-
  check_api_football_dependency() checks raw hardcoded GCS paths (list_blobs + .exists()) per date instead of consulting
  the sports availability manifest, which already carries every column needed to answer the same question — measured
  ~11-25 min of pure network latency per 1-year backfill for that one function alone, vs. under 11s for a manifest-slice
  approach. A follow-up sweep found the SAME class of direct GCS probe in 4 more sports orchestrator files (weather.py,
  sports_fixtures.py, footystats.py, sports_reference_fixtures.py — 16 more call sites), adding roughly another 30-90
  minutes across a full-year backfill on top of the original finding — most are the same once-per-date shape and are
  manifest-replaceable, but one (sports_fixtures.py's per-league fixture-ID set-membership check) needs fixture-id
  granularity the manifest schema doesn't carry and requires a different fix (a cached per-date parquet read, not a
  manifest lookup). 2 of the 16 sites turned out to be dead code (zero callers). Separately, the hardcoded path
  templates have zero shared source with whatever the writer actually uses, so a future path migration could silently
  desync the checker from reality.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [performance, manifest, sports, backfill, gcs, p2]
related:
  [
    ../instruments_service_docs_consolidation_2026_07_08.md,
    ../../codex/02-data/availability-manifest-and-data-status.md,
    ../../codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-08
parent_epic: instruments_master
priority: P2
source:
  'Operator, reviewing instruments-service/docs/ADAPTER_ARCHITECTURE.md''s sports fixture-dependency description
  (check_api_football_dependency): ''shouldn''t it just check the manifest? Isn''t that quicker?... The manifest is
  supposed to be canonical availability... The file paths could migrate. If the code doesn''t [migrate too], but the
  manifest is consistent, then we''re not looking at the manifest.'' Then asked for real numbers on whether a
  manifest-slice approach would meaningfully speed up a year-long backfill ("which can waste half an hour") — confirmed
  with real measurements below.'
assigned_vm: NA
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
last_updated: 2026-07-08
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
resolved_by:
---

## The finding

`instruments-service/instruments_service/reference_data/sports_dependency.py::check_api_football_dependency()` never
touches the sports manifest (`_index/availability_index.parquet`) — it does live GCS calls
(`_prefix_has_object`/`_blob_exists`) against hardcoded path templates
(`_CANONICAL_FIXTURES_PREFIX_TEMPLATE`/`_LEGACY_FIXTURES_PREFIX_TEMPLATE`/etc.), once per date, every time a
fixture-dependent adapter (footystats/understat/transfermarkt/soccer_football_info/open_meteo/betfair) is created. This
is called from `sports/factory.py:89-90` at adapter-creation time.

**The manifest already has everything needed to answer the same question** — confirmed by reading it directly
(`instruments-store-sports-prd`, real `_index/availability_index.parquet`): columns include `venue`, `data_type`,
`league_id`, `date`, `capture_status`. A `venue == "API_FOOTBALL"` + date + non-empty `capture_status` filter answers
the identical dependency question the current path-probe answers.

## Real measured numbers (2026-07-08)

- **Per-call GCS latency**: a `list_blobs` prefix probe (the first thing the current check tries) = **~1.8s**. A direct
  `.exists()` blob probe = **~0.26s**.
- **1-year backfill cost at current per-date-probe rate**: 365 dates × ~1.8s (best case, canonical prefix hits every
  time) ≈ **11 minutes** of pure network round-trip latency, before any real work happens. Historical dates that fall
  through to the legacy-path fallback (up to 4 sequential calls) push this toward **20-25 minutes**.
- **Manifest file**: `_index/availability_index.parquet`, 72.6 MB compressed, 4,918,507 rows, 2014→2026. One-time full
  download+parse-to-bytes: ~10s (7s download + 3s parse). **Row groups are NOT date-clustered** (every row group spans
  the full 12-year range — write-order-appended, not date-sorted) — so row-group-level predicate pushdown gives zero
  download savings; you must download the full compressed file regardless of how narrow the date window is.
- **But post-download filtering is cheap**: naively loading the WHOLE file into a pandas DataFrame costs **8.77 GB** in
  memory — a real problem for a memory-constrained VM. But filtering via
  `pyarrow.parquet.read_table(..., filters=[...])` on the already-downloaded bytes, BEFORE pandas materialization,
  pulled one full year (596,641 rows) in **0.66s using only 233 MB**.
- **Net for a 1-year backfill**: current approach ≈ 11-25 minutes. Manifest-slice approach ≈ ~10s one-time download
  - ~0.7s filter ≈ **under 11 seconds total** — roughly **60-130x faster**, with bounded, small memory use as long as
    the slice (not the full corpus) is what gets materialized into pandas.

## Expanded scope (2026-07-08 follow-up sweep) — 4 more files, 16 more call sites

A follow-up check of every other sports orchestration file found the same class of direct GCS `.exists()`/
`list_blobs()` call in 16 more places. Full characterization (real call-frequency trace, not guessed):

| File:lines                             | What it checks                                                              | Real frequency                                                                                                                                                   | Manifest-replaceable?                                                                             |
| -------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `weather.py:46`                        | Global venue-coordinates parquet                                            | **Dead code** — zero callers (real code path uses UAC `VENUE_COORDINATES`)                                                                                       | N/A                                                                                               |
| `weather.py:87`                        | Fixtures parquet for a date                                                 | **Dead code** — zero callers                                                                                                                                     | N/A                                                                                               |
| `weather.py:248,350,352,504`           | List fixtures / probe already-fetched weather output / re-list during merge | Once per date (same driver as the original finding)                                                                                                              | No — needs venue_id-level state, manifest is league-level                                         |
| `sports_fixtures.py:141`               | Canonical-path-first probe (shared helper)                                  | Amplifier on the 5 call sites below, not independent                                                                                                             | Varies by caller                                                                                  |
| `sports_fixtures.py:160`               | Completed fixture IDs for a date                                            | Once per date                                                                                                                                                    | Partially — existence yes, FT/AET/PEN status filter no                                            |
| `sports_fixtures.py:356`               | Already-captured `af_fixture_id` set per (entity, league)                   | **Real multiplier**: once per distinct (entity × league) pair with fixtures that date — up to 4 entities × ~33 leagues, capped by league count not fixture count | **No** — needs fixture_id-level set membership; manifest only tracks (date, data_type, league_id) |
| `sports_fixtures.py:406`               | Skip-if-unchanged re-write guard                                            | Only the daily-repoll cron (9-day lookahead) — not a backfill cost                                                                                               | No (data-diff check)                                                                              |
| `sports_fixtures.py:474`               | Recovery-mode read-merge-write                                              | Only `--recovery-fixture-ids` operator path — rare, one-off                                                                                                      | No                                                                                                |
| `sports_fixtures.py:537`               | fixture_id→league map for a date                                            | Once per date                                                                                                                                                    | No — needs the mapping itself                                                                     |
| `footystats.py:652,654`                | fixture_id→kickoff map for NaN-fill                                         | Once per date                                                                                                                                                    | No — needs per-fixture kickoff timestamp                                                          |
| `sports_reference_fixtures.py:110,121` | Canonical-format check; legacy-path existence                               | Once per date, `fixture_ids_override` branch only                                                                                                                | No — schema/format check, not existence                                                           |

**Real combined cost**: ~10 of these are the same once-per-date shape as the original finding — stacking real per-call
latency (spot-checked in the ~0.25-1.5s range, consistent with the original ~1.8s/~0.26s baseline) adds roughly
**another 5-15s per date, ≈ 30-90 more minutes over a 365-day backfill**, on top of the ~11-25 min already measured for
`check_api_football_dependency()` alone. `sports_fixtures.py:356` is a genuine per-(entity×league) multiplier worth its
own fix, but capped by league count (not fixture count) and explicitly **not** a drop-in manifest swap — it needs
fixture_id-level data the manifest schema doesn't carry, so the fix shape there is a cached/batched per-date parquet
read, not "point it at the manifest." Two sites are dead code (bonus find, zero callers). Two more (406, 474) aren't
backfill costs at all — different execution contexts (live cron, rare recovery mode).

**Corrected net picture**: the original finding's 60-130x number is real for the ONE function it measured, but
understates total sports-backfill overhead by roughly 2-4x once all 5 files are counted — real total is closer to tens
of minutes to ~1-2 hours across a full-year backfill, not a single fixable hot path. A blanket "swap for manifest" does
not apply uniformly; each site needs its own fix shape per the table above.

## The separate path-drift risk

Independent of the performance question: `sports_dependency.py`'s path templates have no shared source-of-truth with
whatever the real writer uses to construct fixture output paths. If the write path ever migrates (this workspace has
done exactly this kind of migration more than once), the writer + manifest could stay perfectly consistent while this
checker's independently-hardcoded templates silently go stale, producing false "fixtures missing" errors on a pipeline
that's actually working correctly. A manifest-based check would be structurally immune to this — the manifest is
supposed to be the canonical, path-agnostic answer to "did this availability event happen."

## Todos

- [ ] [DATA] P2. **Design a manifest-slice-based replacement for `check_api_football_dependency()`** — load+filter once
      per backfill run (or per reasonable chunk, e.g. per year) rather than per-date network calls; keep the current
      direct-GCS path as a fallback ONLY if a genuine same-run consolidation-lag risk is confirmed real (the manifest
      consolidator cron runs every 1 minute — `codex/05-infrastructure/manifest-consolidator-ssot.md` — so there's a
      real but small lag window worth explicitly deciding how to handle, not silently ignoring).
- [ ] [DATA] P2. **Apply the same manifest-slice replacement to the ~9 once-per-date sites in the expanded-scope table**
      (`weather.py:248,350,352,504`; `sports_fixtures.py:160,537`; `footystats.py:652,654`;
      `sports_reference_fixtures.py:110,121`) — same fix shape as the primary function above, same manifest slice can
      likely be shared/reused across all of them in one load per backfill run rather than one load per site.
- [ ] [DATA] P2. **Design a separate, cached/batched fix for `sports_fixtures.py:356`** — this one needs
      fixture_id-level set membership the manifest doesn't carry; likely a single per-date (or per-backfill-window)
      parquet read of the real fixture-capture file, cached across the (entity × league) loop instead of one GCS call
      per pair.
- [ ] [SCRIPT] P3. **Remove the 2 confirmed-dead-code sites** (`weather.py:46` `_load_venue_coordinates`,
      `weather.py:87` `_extract_fixture_venue_ids`) — zero real callers, verified.
- [ ] [DATA] P2. **Share path-template constants between the real fixtures writer and this checker** (or derive the
      checker's expectations FROM the manifest instead of independent path literals) so a future path migration can't
      silently desync them — this fixes the path-drift risk regardless of the manifest-vs-GCS decision above.
- [ ] [VERIFY] P2. **Confirm real backfill speedup** against a real multi-month or full-year backfill run, before vs.
      after, not just the isolated per-call measurements above.
- [ ] [SCRIPT] P2. **Ship via quickmerge**, quality-gates green.

## Progress Log

- **2026-07-08** — Filed after the operator questioned why the sports fixture-dependency check uses direct GCS path
  probes instead of the manifest, then asked for real numbers to confirm whether a manifest-based approach would
  meaningfully help. Measured directly against real production data (see numbers above) — confirmed a real, substantial
  (60-130x) speedup opportunity for backfills, plus an independent path-drift robustness concern. No fix applied yet —
  this issue holds the scope.
- **2026-07-08 (later)** — Operator asked whether the same anti-pattern needed auditing across other asset groups.
  Checked CeFi/DeFi/TradFi/Prediction — clean (their shared freshness-preflight gate is already manifest-based; 2
  initially-flagged DeFi hits turned out to be local-filesystem dev-cache fallbacks, not GCS probes). But the same grep
  surfaced 16 more real GCS-probe call sites across 4 more sports files — dispatched a dedicated follow-up to
  characterize real call frequency and manifest-replaceability per site (not just assume they all match the original
  finding's shape). Findings folded into "Expanded scope" above — corrects the total backfill-cost picture from a single
  60-130x-fixable function to a real 2-4x understatement across all 5 sports files (tens of minutes to ~1-2 hours
  total), with 2 confirmed dead-code sites and one site needing a genuinely different fix shape (not a manifest swap).
  Todos updated accordingly. No fix applied yet.
