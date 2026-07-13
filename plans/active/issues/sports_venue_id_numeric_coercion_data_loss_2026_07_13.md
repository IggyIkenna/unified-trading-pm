---
doc_type: issue
title:
  features-service sports venue_id normalization silently destroys the real (non-numeric) venue_id, breaking every venue
  join workspace-wide
summary: >
  While root-causing features_sports_unbounded_memory_early_history_dates_2026_07_13.md's OOM, found the real trigger:
  every venue join in features-service's sports pipeline collapses to a degenerate constant key because THREE separate
  normalization sites (gcs_normalizers.normalize_fixtures, gcs_mappings.read_venues, travel_calculator's inline venue
  prep) force venue_id through pd.to_numeric(errors="coerce") then str(int(v)). Real production venue_id values are
  non-numeric canonical codes (e.g. "OLD_TRAFFORD", "ANFIELD", "EMIRATES_STADIUM" — confirmed live against
  sports_reference/venues/venues.parquet, 591/591 rows). pd.to_numeric on a non-numeric string returns NaN, so EVERY
  row's venue_id becomes NaN -> "" on all three call sites. This isn't just the OOM's trigger (a degenerate/blank join
  key on both sides of a merge = a cartesian product) — it means venue_context features (home_win_pct,
  home_venue_clean_sheet_rate, travel_distance_km, away_cumulative_travel_km, stadium_capacity, surface_type, etc., ~19
  columns in VENUE_CONTEXT_COLUMNS) are silently NaN/wrong for every sports date the pipeline has ever computed, not
  just the two OOM-triggering dates. The OOM fix (features-service@efc0b57c) makes the merges cartesian-proof against a
  blank key regardless of this defect, so the crash is closed — but the underlying venue_id data-loss bug is untouched
  and is a genuine, silent, workspace-wide data-correctness defect.
status: open
nature: notes
asset_group: [sports]
stage: [features]
repos: [features-service]
scope: [engineer, admin]
tags: [sports, features, data-correctness, venue-id, silent-failure, normalization, honest-absence]
related:
  [
    plans/active/issues/features_sports_unbounded_memory_early_history_dates_2026_07_13.md,
    plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-13
parent_epic: sports_master
priority: P1
source:
  features_sports_unbounded_memory_early_history_dates-005 dispatch, slot 14, 2026-07-13 (real-data OOM root-cause
  investigation)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by:
---

# features-service sports venue_id normalization silently destroys the real venue_id

## What I found

Real-data profiling of `export_derived_features()` for 2018-06-17/06-18 (see the sibling issue doc) traced a
cartesian-product row explosion to `_compute_venue_features`'s merges on `venue_id`/`away_venue_id`. Live inspection of
both sides of those merges, at the exact point of use inside the real pipeline:

```
venues.shape=(591, 8)  venues['venue_id'].nunique()=1
target_fixtures['venue_id'].value_counts().head()={'': 24}
```

`venues['venue_id']` has exactly **1** unique value across 591 rows (all `""`), and `target_fixtures['venue_id']` is
`""` for every row. A direct raw-parquet read of
`gs://instruments-store-sports-prd-central-element-323112/sports_reference/venues/venues.parquet` (bypassing all
normalization) shows the REAL data is fine — 591/591 unique, real string codes:

```
OLD_TRAFFORD, ST_JAMES_PARK, VITALITY_STADIUM, CRAVEN_COTTAGE, MOLINEUX_STADIUM, ANFIELD, EMIRATES_STADIUM, ...
```

The corruption happens in normalization. THREE separate call sites all carry the identical pattern:

1. `features_service/sports/data/gcs_normalizers.py:188-190` (`normalize_fixtures`) — comment: "Normalize venue_id to
   clean int-string (173.0 → '173') for venue join".
2. `features_service/sports/data/gcs_mappings.py:158-160` (`read_venues`) — comment: "Normalize venue_id to clean
   int-string for consistent joins with fixtures".
3. `features_service/sports/calculators/travel_calculator.py:182-184` — same pattern inline, comment: "Normalize
   venue_id to str in venues DataFrame for consistent type comparison with fixtures".

All three do:

```python
df["venue_id"] = pd.to_numeric(df["venue_id"], errors="coerce")
df["venue_id"] = df["venue_id"].apply(lambda v: str(int(v)) if pd.notna(v) else "")
```

`pd.to_numeric("OLD_TRAFFORD", errors="coerce")` → `NaN` for every non-numeric value → every row becomes `""`. The
comments make clear this was written for an EARLIER data era where venue_id was a raw numeric ID from the source API
(e.g. `173.0 → "173"`). The current canonical `venues.parquet` — presumably instruments-service-owned — has since moved
to human-readable string codes. All three normalization sites were never updated to match, so they now destroy the value
on every call, for every date, workspace-wide (not just 2018).

## Why it matters

- **Venue-derived features have likely never been correct** in production: `home_advantage_pct`, `home_venue_win_rate`,
  `home_venue_goals_avg`, `home_venue_clean_sheet_rate`, `home_venue_matches_played`, `travel_distance_km`,
  `away_travel_distance_km`, `away_cumulative_travel_km`, `stadium_capacity`, `surface_type`, `venue_capacity`,
  `venue_is_artificial_turf` (the `VENUE_CONTEXT_COLUMNS` set, `venue_context.py:16-43`) are silently NaN/default for
  every fixture, every date, since whenever `venues.parquet` moved to string venue_id codes. If any ML model consumes
  these columns, it has been training/predicting on honest-absence-shaped NaN it never should have had to see — this is
  a correctness gap, not just a coverage gap.
- **The OOM in `features_sports_unbounded_memory_early_history_dates_2026_07_13.md` was a symptom, not the root cause.**
  The shipped fix (`features-service@efc0b57c`) makes every affected merge cartesian-proof against a blank/degenerate
  key regardless of upstream defects — this closes the crash risk permanently, independent of whether venue_id
  normalization is ever fixed. But it does NOT restore correct venue features; it just makes the incorrect state
  (NaN-filled, not exploding) safe.
- This is exactly the class of finding CLAUDE.md's data-pipeline-correctness HARD RULE calls a "big finding" — silent,
  cross-cutting, affects a whole feature family across the full historical corpus.

## What this is NOT

- NOT a re-open of the OOM — that crash is fixed and verified (both 2018-06-17 and 2018-06-18 now complete
  `export_derived_features()` fully at ~620MB peak RSS against real GCS data).
- NOT necessarily specific to 2018 — I have not audited whether venue_id was EVER numeric in the live corpus, or whether
  this has been broken since the venues table was first introduced. Scoping that is Todo 1 below.

## Recommended decision (data-engineering / architecture call — not mine to make unilaterally)

The real fix depends on which venue_id format is actually canonical today, which I did not have full context to
determine unilaterally:

- **Option A** — the string code (e.g. `"OLD_TRAFFORD"`) IS the current canonical `venue_id` everywhere
  (instruments-service writes it, and any consumer should treat it as an opaque string). Fix: delete the
  `pd.to_numeric`/`int()` round-trip at all three sites; keep venue_id as a plain string (strip/uppercase-normalize if
  needed for join hygiene, but do not parse it as a number).
- **Option B** — there are TWO id spaces in play (a legacy numeric API-Football venue id still present in raw fixture
  payloads, and a newer instruments-service-assigned canonical string code in `venues.parquet`), and joining fixtures ↔
  venues actually requires a separate id-mapping/crosswalk (not a direct value equality), which none of these three
  sites currently attempt. Fix is bigger: build/locate the crosswalk, thread it through all three sites.
- **Option C** — venue_id really is inconsistent across the corpus (some eras numeric, some string), and the fix needs
  to handle both without destroying either (e.g. try numeric first, fall back to the raw string instead of `""` on
  coercion failure).

## Todos

- [x] ✅ [VERIFY] P1. Audit `venues.parquet`'s venue_id history — is it consistently string-coded across the whole
      corpus, or did it change format at some point? Check the raw upstream write path in instruments-service (whoever
      writes `sports_reference/venues/venues.parquet`) to confirm the current canonical format and whether the
      three-call-site assumption was ever correct. (repos: features-service, instruments-service) — **DONE, slot 14,
      read-only investigation, no code change (this todo is a factual audit, not the operator decision itself). RESOLVES
      the ambiguity — Option B confirmed, with a bigger-than-expected wrinkle:**
  - **`venues.parquet` is 100% string-coded, consistently** — direct read of the live file confirms all 591 rows
    (`OLD_TRAFFORD`, `ST_JAMES_PARK`, ...), 0/591 numeric-looking. No format drift found in this table.
  - **Raw fixture payloads carry a GENUINELY NUMERIC venue_id** — sampled raw (pre-normalizer) `fixtures.parquet` across
    eras: 2021-05-01 (165 rows, `venue_id` dtype `float64`, values `1394.0`/`11913.0`/`1397.0`, 165/165 numeric-like)
    and 2024-01-15 (13 rows, same pattern, `19941.0`/`12684.0`/`20474.0`) both confirm a real numeric
    API-Football-native venue id — a DIFFERENT id-space from `venues.parquet`'s string codes, not a normalization
    artifact. (2018-06-17 and 2026-06-01 samples show `venue_id` present but fully NULL, not numeric — a separate,
    pre-existing sparse-coverage gap in those specific days' raw data, not investigated further here.)
  - **CONFIRMS Option B, not Option A**: this is genuinely two id-spaces (raw-fixture numeric API-Football id vs.
    `venues.parquet`'s canonical string code), not a single space with an accidental type-coercion bug. Simply deleting
    the `pd.to_numeric`/`int()` round-trip (Option A) would NOT fix the join — a numeric fixture `venue_id` still
    wouldn't equal a string `venues.parquet` `venue_id` even compared as raw strings (`"1394"` != `"OLD_TRAFFORD"`).
  - **New wrinkle Option B's original framing didn't anticipate**: `venues.parquet` has **no crosswalk/external-id
    column** (`venues.parquet` columns: `venue_id, name, city, country, capacity, surface, latitude, longitude` — no
    `api_football_venue_id` or equivalent). A numeric→string venue-id crosswalk may not exist ANYWHERE in the current
    corpus, not just be "missing from these 3 call sites" — this could be a genuinely bigger fix (build/backfill a
    crosswalk table, or match venues by `name`+`city` fuzzy-join as a fallback) than Option B's original text implied.
    Flagging this refined finding for the operator decision below.
- [ ] [DECISION] P1. Rule on Option A/B/C above with the operator/data-engineering owner, informed by the audit above —
      **note the audit found Option B confirmed but bigger than originally scoped: no crosswalk column exists in
      `venues.parquet` at all, so the fix may require building one (via `name`/`city` matching or a new upstream ingest
      of API-Football's venue-id mapping), not just wiring an existing crosswalk into the 3 call sites.**
- [ ] [CODE] P1. Apply the chosen fix at all three sites (`gcs_normalizers.py:188-190`, `gcs_mappings.py:158-160`,
      `travel_calculator.py:182-184`) — keep them consistent with each other (a fourth site could exist; grep
      `venue_id` + `to_numeric` fleet-wide before closing this out).
- [ ] [VERIFY] P2. Once fixed, re-run `export_derived_features` for a representative sample of dates (including
      2018-06-17/06-18) and confirm `VENUE_CONTEXT_COLUMNS` are populated with real (non-NaN-everywhere) values; compare
      against a hand-computed expectation for at least one venue.
- [ ] [VERIFY] P3. Check whether any downstream ML model/strategy already trained on the broken (all-NaN) venue-context
      columns — if so, flag for a retrain, this is out of scope for this issue to fix directly.

## Secondary finding (noise, not fixed here)

While re-verifying the fix on 2018-06-17, the `run_new_calculators` phase (per-fixture `elo`/`manager`/`travel` group)
printed a large volume of `Traceback (most recent call last):` output for
`Skipping fixture row N: Cannot compare tz-naive and tz-aware timestamps` — the exception is caught and the row is
skipped (not a crash), but something in that path is logging the full traceback on every occurrence instead of a
one-line warning, which is expensive/noisy at scale and masks real errors in the same log stream. Not investigated
further (out of scope for this issue) — flagging for whoever picks up the venue_id fix to glance at, since it's in the
same calculator neighborhood.
