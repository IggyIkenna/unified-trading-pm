---
doc_type: issue
title:
  Track C footystats venue mislabel — completion-state CONTRADICTION between sessions (2026-07-27 claimed 0 stale rows,
  2026-08-14 live census finds 19,782 real shards through TODAY) + a previously-unexamined LADBROKES_UK/SPORT888 casing
  gap under the same footystats-derived odds_horizon_bucket shape
summary: >-
  Dispatched to execute sports_consolidated_closeout_2026_07_19.md's Track C "venue vocabulary cleanup" todo
  (casing/aliasing re-stamp + the footystats legacy-bundle mislabel, venue=ODDS_API->FOOTYSTATS, 42,476 rows). Live
  measurement (2026-08-14, this session) found the premise contradicted by the corpus's own history, plus one genuinely
  new, previously-untouched population. (1) `sports_consolidated_native_ao_extract_2026_07_25.md`'s 2026-07-27 Progress
  Log claims this exact population was migrated and verified clean: "removed 42,476 old-venue rows, added 42,476
  new-venue rows, VERIFY stale_remaining=0" and "FOOTYSTATS 42,476 rows -- all matching the raw-tick counts exactly."
  But a fresh live census against the SAME manifest index today finds `venue=ODDS_API`/`pipeline_mode=batch_footystats`
  still holding 19,782 shards (19,469 `captured`, real non-empty data, `source=footystats`), with dates running through
  2026-08-14 -- i.e. TODAY -- while `venue=FOOTYSTATS` itself shows 0 captured rows (independently corroborated by
  `sports_taxonomy_p2_migration_2026_08_08.md`'s own 2026-08-14 slot-26 closure note). The two states cannot both be
  true of a one-time historical batch job; the date range running through today points at an unfixed WRITER still
  emitting new objects under the wrong stamp daily, not stale residue. (2) A day BEFORE the 2026-07-27 rename executed,
  the archived `sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md` investigation (status: still `open`)
  had already measured that a straight rename-to-FOOTYSTATS is the WRONG fix for this exact population -- 56.40% of the
  footystats `(date, league)` cells already exist under `batch_odds_api`, so a 1:1 relabel creates DUPLICATE manifest
  rows; the operator-ruled correct fix is a de-cased PURGE, still open as that doc's own unchecked P0 todo. The
  2026-07-27 session that executed the rename does not appear to have read that finding. (3) New, previously-unexamined:
  `venue=LADBROKES_UK`/`SPORT888` ALSO appear under `pipeline_mode=batch_footystats` (`source=footystats`,
  `instrument_type=MATCH_ODDS`/`OVER_UNDER_*`, `data_type=odds_horizon_bucket`) -- a THIRD GCS/manifest shape distinct
  from both the raw-tick shape the 2026-07-27 restamp covered and the `processed_candles/` derived-candle shape
  `sports_venue_restamp_derived_candle_gap_2026_07_27.md` covered (resolved 2026-08-03). Measured: LADBROKES_UK 25,645
  shards / 2,454,668 rows / 570 days (2023-03-31..2026-04-14); SPORT888 96,239 shards / 9,857,007 rows / 1,350 days
  (2020-06-06..2026-04-14). No prior effort has touched this population.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags:
  [data-correctness, sports, venue-mapping, manifest, footystats, ssot-contradiction, writer-bug, casing, investigation]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/archive/2026_08/sports_venue_restamp_derived_candle_gap_2026_07_27.md,
    /plans/active/sports_satellite_ao_dispatch_batch13_2026_08_13.md,
  ]
created: 2026-08-14
last_updated: 2026-08-14
parent_epic: sports_master
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: unified-trading-pm (docs-only investigation, slot-27, 2026-08-14)
assigned_vm: planning
source:
  [
    "sports_satellite_ao_dispatch_batch13_2026_08_13.md todo 4 (Track C venue vocabulary cleanup), dispatched
    2026-08-14, slot-30",
    "Live read_availability_index census against gs://market-data-tick-sports-prd-central-element-323112, 2026-08-14",
  ]
context_scope:
  [
    market-tick-data-service/scripts/sports/restamp_sports_bookmaker_venue_2026_07_27.py,
    market-tick-data-service/scripts/sports/census_track_c_venue_restamp_targets_2026_07_27.py,
    market-tick-data-service/scripts/sports/manifest_swap_venue_restamp_2026_07_27.py,
    /plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md,
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
  ]
---

# Track C footystats mislabel: completion contradiction + a new bookmaker-casing gap

> **✅ ARCHIVED 2026-08-14 — all 5 todos done, no `locked_by`.** Moved from `plans/active/issues/` to
> `plans/archive/2026_08/issues/` per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`. Every
> question this doc opened is closed: the completion-state contradiction was reconciled (byproduct of the DIAG todo — a
> legacy-seed manifest layer, not a live writer or a re-measurement error), the legacy-seed residue purge was routed to
> `sports_taxonomy_p2_migration_2026_08_08.md`, and the LADBROKES_UK/SPORT888 live-content-verify confirmed a genuine
> content-distinct feed (not a casing/alias duplicate — mirrors the UNIBET precedent, no fold/restamp tool needed). One
> new finding surfaced during that last verification (the `batch_footystats`/`source=footystats`/ `odds_horizon_bucket`
> population's physical content reading `source=ODDS_API`, a manifest mislabel disjoint from this doc's own original
> scope) was routed forward as a new P1 todo in `sports_taxonomy_p2_migration_2026_08_08.md` rather than reopening this
> doc.

## What I found

**1. Completion-state contradiction (SSOT violation).**

| Source                                                             | Claim                                                                                                                                                               | Date       |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| `sports_consolidated_native_ao_extract_2026_07_25.md` Progress Log | `venue=ODDS_API`/`batch_footystats`: 0 stale rows remaining (42,476 removed, 42,476 `FOOTYSTATS` rows added, `VERIFY stale_remaining=0`)                            | 2026-07-27 |
| This session, live `read_availability_index` census                | `venue=ODDS_API`/`pipeline_mode=batch_footystats`: **19,782 shards, 19,469 `captured`** (real data, `source=footystats`), date range through **2026-08-14** (today) | 2026-08-14 |
| `sports_taxonomy_p2_migration_2026_08_08.md` slot-26 closure note  | `venue=FOOTYSTATS`: 0 captured rows of any data_type                                                                                                                | 2026-08-14 |

~~Both cannot be true of a one-time historical migration. The date range on the still-populated
`ODDS_API`/`batch_footystats` rows running through **today** is the strongest signal: this reads as an **unfixed
writer/backfill path still emitting new objects under the wrong stamp daily**, not leftover residue from before the
2026-07-27 rename. The 2026-07-27 session's own tooling only ever touched the historical objects present _at that time_
(16,970 objects) — nothing in this corpus shows a writer-side fix (e.g. to whatever job produces
`pipeline_mode=batch_footystats` + `venue=ODDS_API` shards) that would stop new mis-stamped objects from continuing to
land. This is a hypothesis, not yet confirmed — the writer/job itself has not been located in this session.~~

**CORRECTED 2026-08-14 (slot-30) — the "dates through today" claim was a measurement artifact; no writer exists.** This
session's census (`census_track_c_venue_restamp_targets_2026_07_27.py`, THIS session's own reported number above) was
read at the **venue level only**, and `venue=ODDS_API` carries rows under **4 distinct `pipeline_mode`s**:
`batch_footystats` (the mislabeled population this doc is about), `batch_mdps_odds_horizon_bucket`, `batch_odds_api`,
and — the actual source of the "through today" date — `live_odds_api` (1,694 rows, 2026-06-21..2026-08-14, the genuinely
live, correctly-attributed ODDS_API vendor capture). Re-scoped live to
`venue=ODDS_API AND pipeline_mode=batch_footystats` specifically: **19,782 rows, date range 2020-06-01..2026-04-14** —
frozen exactly at the 2026-05-05 migration's own boundary, **0 rows with any `attempted_at` in the last 14 days** (in
fact `attempted_at` is `NaT`/absent for the entire population, consistent with a legacy bulk-migrated set predating
`attempted_at` tracking). **There is no writer producing new mis-stamped objects.** Confirmed no-hit greps for both
`ODDS_API` and `batch_footystats` as literals in `market-tick-data-service`'s live source tree
(`market_tick_data_service/`, migration one-off scripts excluded); the one candidate live writer that DOES touch
FootyStats odds (`instruments-service/instruments_service/engine/orchestrator/footystats.py::_fetch_footystats_odds`,
active since the 2026-06-22 coherence-check fix) writes `venue="footystats"` (lowercase) to a completely different
path/bucket (`sports_reference/by_date/.../entity=footystats_odds/`, the IS reference-data surface) — it is not this
population's source.

**But the population's PERSISTENCE despite the 2026-07-27 "0 stale remaining" claim IS real, and now has a confirmed
root cause: a legacy per-VM seed shard the 2026-07-27 rename never touched.** Live-read
`_index/per_vm/_legacy_seed.parquet` (the bucket's own legacy-row carrier, always merged into the main index by
`manifest_consolidator.consolidate()` on every cycle per `unified-trading-library`'s own
`_seed_legacy_if_needed`/`legacy_seed_captured_outranks_resurrection_risk_2026_07_15` logic) directly: it still holds
**20,095** `venue=ODDS_API`/`pipeline_mode=batch_footystats` rows, never re-stamped.
`manifest_swap_venue_restamp_2026_07_27.py`'s CAS-swap operates ONLY on `_index/availability_index.parquet` (the merged
index) — it has no code path touching `_index/per_vm/*.parquet` shards at all. So the 2026-07-27 run's "VERIFY
stale_remaining=0" was true of the merged index in that moment, but the very next consolidation cycle re-merged the
un-renamed legacy-seed copy back in — the population never actually left, it was masked for one consolidation cycle.
**This is the real blocker for any future purge/rename of this population**, not a live writer: whatever operation lands
next (routed to `sports_taxonomy_p2_migration_2026_08_08.md` per this doc's own recommendation below) must also
re-stamp/purge the matching rows in `_index/per_vm/_legacy_seed.parquet` in the SAME change, or the consolidator will
resurrect them again on its next cycle exactly as it did this time. Tooling fix shipped this session:
`market-tick-data-service@<see /done evidence>` adds a per-`pipeline_mode` date-range breakdown to
`census_track_c_venue_restamp_targets_2026_07_27.py` whenever a venue spans more than one pipeline_mode, so this exact
aggregation-artifact false alarm can't recur silently for any future venue/mode combination.

**2. The rename-to-FOOTYSTATS approach was already determined to be the WRONG fix, one day before it was executed.**

`sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md` (archived, `status: open` — its correctness finding
was never closed even though the doc itself is filed under `archive/`) measured, on 2026-07-17: a straight
`venue=ODDS_API`→`FOOTYSTATS` rename/move is **not** a clean operation — 56.40% of the footystats `(date, league)` cells
already exist under `batch_odds_api` (the correct home, reached via a separate read-split-merge that doc DID execute and
verify). A 1:1 rename therefore creates **duplicate** manifest rows for content already correctly attributed elsewhere.
The operator-ruled correct fix for the remainder is a **de-cased PURGE** of the mis-stamped rows+objects, still that
doc's own open, unchecked P0 todo. The 2026-07-27 session that executed the FOOTYSTATS rename
(`sports_consolidated_native_ao_extract_2026_07_25.md`) does not cite or appear to have read this finding — it treated
the population as a simple casing/alias rename, the same class as `LADBROKES_UK`→`LADBROKES`, which it is not.

**3. New finding — a third, previously-untouched population with the same casing/alias defect.**

`venue=LADBROKES_UK` and `venue=SPORT888` also appear under `pipeline_mode=batch_footystats`, `source=footystats`,
`instrument_type=MATCH_ODDS`/`OVER_UNDER_1_5`/`OVER_UNDER_2_5`/`OVER_UNDER_3_5`/`OVER_UNDER_4_5`,
`data_type=odds_horizon_bucket` — a derived-odds shape, structurally distinct from both:

- the raw-tick shape (`instrument_type=ODDS`/`data_type=TRADES`, `pipeline_mode=batch_odds_api`) the 2026-07-27
  `restamp_sports_bookmaker_venue_2026_07_27.py` tool covers, and
- the `processed_candles/` derived-candle shape (`arbitrage_opportunity`/`odds_horizon_bucket`/`odds_movement`/
  `odds_snapshot` under MDPS's own root prefix) `sports_venue_restamp_derived_candle_gap_2026_07_27.md` covers (resolved
  2026-08-03, slot-13).

Measured (live census, this session):

| venue        | shards | row_count sum | date range                            |
| ------------ | ------ | ------------- | ------------------------------------- |
| LADBROKES_UK | 25,645 | 2,454,668     | 2023-03-31 .. 2026-04-14 (570 days)   |
| SPORT888     | 96,239 | 9,857,007     | 2020-06-06 .. 2026-04-14 (1,350 days) |

No prior investigation or tooling in this corpus has scoped, sized, or touched this population.

## Why it matters

This is real, live production sports odds data (>12.3M rows combined for the new LADBROKES_UK/SPORT888 finding alone)
still carrying the un-folded bookmaker-casing alias identified as a data-correctness defect back in the original Track C
finding. The ODDS_API/FOOTYSTATS population is a genuine SSOT contradiction between two "done" claims in the corpus's
own history, on ground a THIRD active plan (`sports_taxonomy_p2_migration_2026_08_08.md`) is concurrently working today
— dispatching yet another worker to re-run the existing FOOTYSTATS rename script would very likely repeat the
already-identified wrong fix (creating duplicate manifest rows) rather than resolve it.

## Recommended decision

1. **Do NOT re-run `restamp_sports_bookmaker_venue_2026_07_27.py --venue FOOTYSTATS`** — it was already determined
   (2026-07-17, one day before it was actually run) to be the wrong fix for this population.
2. Route ODDS_API/FOOTYSTATS resolution through the currently-active `sports_taxonomy_p2_migration_2026_08_08.md` plan
   (already working overlapping ground, closed an adjacent todo today) rather than a second independent effort — this
   doc is a pointer/handoff, not a competing claim on that ground.
3. For LADBROKES_UK/SPORT888 under `batch_footystats`/`odds_horizon_bucket`: before building a restamp tool, verify (per
   the original Track C todo's own UNIBET_UK/SMARKETS caution) that these are genuinely a casing/alias duplicate and not
   a content-distinct feed under this specific derived shape — a live content comparison, same method already used to
   disprove the UNIBET fold.

## Todos

- [x] ✅ [DIAG] P1. Identify the writer/backfill job that produces `pipeline_mode=batch_footystats` + `venue=ODDS_API`
      objects (dates through 2026-08-14) and determine whether it needs a writer-side fix to stop the ongoing mis-stamp,
      vs. this being a one-off re-population this session mis-measured. Cross-reference
      `/plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md`'s still-open PURGE todo
      before choosing rename vs. purge vs. writer-fix. (repo: market-data-processing-service or wherever the footystats
      capture job lives) — **DONE 2026-08-14 (slot-30), live-verified, no writer exists.** Neither hypothesis in the
      todo's own title is quite right: re-scoped to `venue=ODDS_API AND pipeline_mode=batch_footystats` specifically,
      the population is frozen at 2020-06-01..2026-04-14 (0 rows with recent `attempted_at`) — genuinely a one-off, not
      a re-population this session mis-measured (the "through today" figure was real, just wrongly attributed — it
      belongs to the co-resident `live_odds_api` pipeline_mode under the same venue, a separate, correctly-labeled,
      actively-live population). The real reason the population never reached zero after the 2026-07-27 rename is a
      THIRD explanation neither hypothesis names: `_index/per_vm/_legacy_seed.parquet` still carries 20,095 matching
      rows the rename script never touched, and the manifest consolidator re-merges them every cycle. See the corrected
      "What I found" §1 above for full evidence. No writer-side fix needed; a manifest-hygiene fix is needed instead
      (see new todo below). Tooling: `census_track_c_venue_restamp_targets_2026_07_27.py` fixed to break out
      per-`pipeline_mode` date ranges so this exact aggregation-artifact false alarm can't recur silently.
- [x] ✅ [REVIEW] P2. Reconcile the completion-state contradiction between
      `sports_consolidated_native_ao_extract_2026_07_25.md` (2026-07-27: claims 0 stale `ODDS_API`/`batch_footystats`
      rows) and this doc's 2026-08-14 measurement (19,782 real shards) — most likely writer-recurrence (see todo above),
      but state it explicitly once confirmed rather than leaving two "done" claims standing. — **DONE 2026-08-14
      (slot-30), resolved as a byproduct of the DIAG todo above (same investigation, not writer-recurrence).** Both
      claims were true of different manifest LAYERS at different times, not a genuine contradiction about the same
      state: the 2026-07-27 CAS-swap genuinely zeroed the MERGED index (`_index/availability_index.parquet`) at that
      moment — but never touched `_index/per_vm/_legacy_seed.parquet`, so the very next consolidation cycle re-merged
      the legacy seed's un-renamed 20,095 rows back in. "0 stale remaining" and "19,782 shards present today" are both
      accurate readings of their respective moments; the gap between them is the legacy-seed omission, not a
      re-measurement error or a live writer.
- [x] ✅ [DATA] P1. **Before any future purge/rename of the `ODDS_API`/`batch_footystats` population lands** (routed to
      `sports_taxonomy_p2_migration_2026_08_08.md` per the Recommended decision above): the fix MUST also re-stamp or
      purge the matching rows in `_index/per_vm/_legacy_seed.parquet` (20,095 rows, live-confirmed 2026-08-14, slot-30)
      in the SAME change as the merged-index operation — the manifest consolidator (`unified-trading-library`'s
      `manifest_consolidator.consolidate()`, `_seed_legacy_if_needed`) always re-merges this shard on every cycle, and
      this is confirmed to be exactly why the 2026-07-27 `manifest_swap_venue_restamp_2026_07_27.py` run's "VERIFY
      stale_remaining=0" did not stick — it only ever touched the merged index. Any operation that repeats that mistake
      will silently revert again. (repo: market-tick-data-service or wherever the next purge/rename tool is built) —
      **DONE 2026-08-14 (slot-30), routed as instructed**: `sports_taxonomy_p2_migration_2026_08_08.md` had already
      closed its own "Re-attribute the ODDS_API and FOOTYSTATS venue rows" todo (2026-08-14, slot-26) without
      discovering this legacy-seed residue — that closure verified `venue=FOOTYSTATS` reached 0 rows but never
      re-checked `venue=ODDS_API AND pipeline_mode=batch_footystats` itself. Added a new P1 todo directly beneath that
      closed one in that plan carrying this exact requirement (both-layers purge, do-not-rename-straight guidance,
      citation back to this doc) so the next worker to touch that population has it in-plan, not just in this issue doc.
      `unified-trading-pm@<see /done evidence>`.
- [x] ✅ [DATA] P2. Live-content-verify whether `LADBROKES_UK`/`SPORT888` under `batch_footystats`/`odds_horizon_bucket`
      are a genuine casing/alias duplicate (safe to fold, mirroring the existing `SPORTS_VENUE_FOLD` entries) or a
      content-distinct feed (like UNIBET_UK/UNIBET_EU turned out to be) before building any restamp tooling for this
      shape. (repo: market-tick-data-service) — **DONE 2026-08-14 (slot-27), live-verified: CONTENT-DISTINCT, NOT a
      casing/alias duplicate — mirrors the UNIBET precedent exactly, do not fold.** Method: downloaded the real
      `processed/by_date/day={D}/data_type=odds_horizon_bucket/league_id={L}/timeframe={T}/bucketed.parquet` shards two
      manifest rows for `venue=LADBROKES_UK`/`SPORT888` under this pipeline_mode/data_type resolve to
      (`day=2023-04-02`/`league_id=PRIMEIRA_LIGA` and `day=2020-06-06`/`league_id=BUNDESLIGA`, independent samples) and
      inspected the `bookmaker_key` column directly (the file's real per-bookmaker natural key — same one MDPS's own
      `migrate_odds_horizon_bucket_venue_to_bookmaker_2026_07_27.py` groups on). Findings: (1) `ladbrokes_uk` and
      `sport888` are first-class, native `bookmaker_key` values in the vendor's own fan-out (confirmed in both samples,
      alongside `unibet`/`unibet_uk` co-existing as separate keys in the identical file — the exact structural pattern
      already proven genuinely-distinct for UNIBET); (2) **no bare `ladbrokes` or `bet888sport` key exists anywhere in
      this shape at all** (0 manifest rows for either, confirmed via `read_availability_index` census scoped to
      `pipeline_mode=batch_footystats AND data_type=odds_horizon_bucket` — so there is no collision/duplicate-risk from
      leaving them unfolded, unlike the ODDS_API/FOOTYSTATS raw-tick population); (3) on a shared fixture
      (`7f7e2bbbdbaf5fca3c422adf3cb84225`, CS Maritimo vs Boavista Porto, 2023-04-02), `ladbrokes_uk` stamped its own
      independent `bm_time` (13:24:50Z) and odds (HOME 2.25/DRAW 3.10/AWAY 3.30) distinct in timing from every other
      bookmaker's own independently-timestamped row on the same fixture — an independent per-bookmaker observation, not
      a duplicated/copied row. **No restamp tooling should be built for this population** (todo below is resolved as
      N/A, not skipped). No code changes required; this todo's own done_definition (checkbox flip) is the full task.
- [x] ✅ [CODE] P3. If todo 4 confirms a genuine casing/alias duplicate: build a restamp tool mirroring
      `restamp_sports_bookmaker_venue_2026_07_27.py`'s proven pattern, scoped to
      `instrument_type=MATCH_ODDS|OVER_UNDER_*`/`data_type=odds_horizon_bucket`/`pipeline_mode=batch_footystats`, and
      execute + manifest-swap for the ~121,884 shards / ~12.3M rows measured above. (repo: market-tick-data-service) —
      **N/A 2026-08-14 (slot-27), premise disproven by todo 4** — LADBROKES_UK/SPORT888 are content-distinct, real
      per-bookmaker feeds, not a casing/alias duplicate; building this tool would silently conflate two distinct
      bookmakers' data under one venue key, exactly the mistake the UNIBET precedent already warned against. No tool
      built, none needed.

## New finding (2026-08-14, slot-27) — the `batch_footystats`/`odds_horizon_bucket` manifest population's own

`pipeline_mode`/`source` stamp does not match its physical content; likely a much larger mislabel than this doc's
original scope

While live-content-verifying todo 4 above, both sampled `bucketed.parquet` shards' **own `source`/`data_source` columns
read `ODDS_API` for 100% of rows** (86/86 and 23/23 respectively, across every `bookmaker_key` present, not just
`ladbrokes_uk`/`sport888`) — not `footystats`, despite the manifest rows pointing at these exact shards being stamped
`pipeline_mode=batch_footystats`/`source=footystats`. The physical shard path itself
(`processed/by_date/day={D}/data_type=odds_horizon_bucket/league_id={L}/timeframe={T}/bucketed.parquet`) carries no
`pipeline_mode=` segment at all, confirming it is genuinely ODDS_API-vendor derived data (same schema/shape as the
already-migrated `mdps_odds_horizon_bucket` population), just manifest-mislabeled as footystats. This population
measures **1,784,473 manifest rows** (`read_availability_index` census,
`pipeline_mode=batch_footystats AND data_type=odds_horizon_bucket`, this session) — entirely separate from, and not
counted by, `sports_taxonomy_p2_migration_2026_08_08.md`'s "Move `odds_horizon_bucket` onto the `odds` + `horizon`
model" P0 todo, whose 2026-08-14 (slot-26) closure scoped its 1,070,078-row total to `source=mdps_odds_horizon_bucket`
specifically and never examined this disjoint `source=footystats` population sitting under the identical `data_type`.
Routed as a new P1 todo in `sports_taxonomy_p2_migration_2026_08_08.md` (the actively-working plan on this exact ground)
rather than re-opening this doc's own closed scope — see that plan for the tracked follow-up.
