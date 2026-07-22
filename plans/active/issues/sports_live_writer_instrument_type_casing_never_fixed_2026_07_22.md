---
doc_type: issue
title: >-
  Sports live odds writer still emits non-canonical lowercase instrument_type=odds/data_type=trades — the league_id
  relocation fixed history but not the source, so new daily captures keep landing non-canonical
summary: >-
  While preparing the gated delete of the old non-canonical sports odds objects (post league_id-relocation
  manifest-swap, 2026-07-22), found that the LIVE daily odds-api capture writer
  (`market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py::_build_sports_shard_path`,
  lines 887 + 896) still hardcodes lowercase `instrument_type=odds/data_type=trades` in both the GCS path AND the
  matching `shard_counts` manifest-key tuple (line 795-796) — this was NEVER touched by the relocation work (which was a
  one-time historical COPY only). `league_id` casing WAS already fixed at the write source two days earlier
  (`mtds@ad4f1872`, 2026-07-20, `_canonical_league_id()` in `odds_api_adapter.py`), so this is the one remaining
  non-canonical axis, and it is NOT historical debt — it is an ACTIVE, ONGOING leak: every single day's new odds capture
  writes fresh objects + manifest rows at the non-canonical `instrument_type=odds/data_type=trades` path/value.
  Consequence: any future "final" delete of the old non-canonical objects is a leaky bucket — tomorrow's capture just
  recreates the same non-canonical shape at new dates — unless this write-source bug is fixed FIRST.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags:
  [sports, canonical, casing, instrument_type, data_type, live-writer, league-id, relocation, manifest, ongoing-leak]
related:
  [
    sports_league_id_namespace_migration_2026_07_20.md,
    ../sports_master_closeout_2026_07_21.md,
    ../../codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-07-22
last_updated: 2026-07-22
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  discovered 2026-07-22 while preparing the 5-part-proof delete evidence for the league_id relocation's old
  non-canonical objects (sports_master_closeout_2026_07_21.md P0 chain), via a dedicated Explore-agent investigation
  into whether the live capture pipeline was also fixed or only the historical corpus.
depends_on: []
---

# Sports live odds writer never fixed for instrument_type/data_type casing (2026-07-22)

## What was found

`_build_sports_shard_path()` in `market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py`
(lines 869-899) builds the GCS path for every new sports odds shard. Both branches (with and without `fixture_id`) end
with a **hardcoded literal**:

```python
f"instrument_type=odds/data_type=trades/"
```

not derived from any canonicalization function or UAC enum. The matching **manifest** row-key tuple, built a few lines
earlier in the same function's caller (`venue_fetch.py:795-796`):

```python
shard_counts[(bm_str, "trades", league_str, "odds", fixture_str)] = (
    shard_counts.get((bm_str, "trades", league_str, "odds", fixture_str), 0) + rows
)
```

uses the same lowercase literals, consumed downstream in `manifest_finalize.py:347`
(`if itype_key == "odds" and data_type_key == "trades":`) which gates the sports-specific `source`/`pipeline_mode`
resolution AND the `available_at` timestamp stamping for the manifest INDEX row (the
`sports_mtds_available_at_manifest_gap` fix, comment at `manifest_finalize.py:353-358`).

**This is the reverse of `league_id`.** `league_id` casing WAS fixed at the write source on 2026-07-20 (`mtds@ad4f1872`,
"canonicalise league_id at the write path via numeric api-football id") — TWO DAYS BEFORE this session's league_id
relocation migration ran. `_canonical_league_id()` in `market_interface/adapters/sports/odds_api_adapter.py:69-93`
resolves the numeric `api_football_id` to the canonical `LEAGUE_REGISTRY` slug via
`unified_api_contracts.sports.get_league_by_api_football_id`, falling back to the raw display name only if unmapped —
confirmed live (traced through `_fetch_all_leagues` → `download_batch` → `_route_sports` in
`adapters/umi_tick_provider.py:178-189`, the actual call path). So `league_id` is a closed, already-fixed axis.
`instrument_type`/`data_type` casing is NOT — it was simply never touched, git-blame confirms the two `venue_fetch.py`
lines are unchanged since 2026-06-11, predating both the league_id fix and this session's relocation entirely.

UAC already documents the CORRECT target: `unified_api_contracts/market_data_categories.py:1647-1651` states "ODDS_API
emits 'ODDS' (uppercase)" (dated 2026-05-20) — the live writer directly contradicts UAC's own documented expectation.

## Why this matters (the leaky-bucket problem)

The 2026-07-22 league_id relocation (`sports_master_closeout_2026_07_21.md`) COPIED ~275K historical objects from
non-canonical to canonical paths/casing and manifest-swapped the bookkeeping rows. The plan's next step is a **separate,
later, gated delete** of the old non-canonical objects (human-only per
`codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3 hard stop #1 — any prod-bucket delete). But:

- The relocation executor is a **pure GCS-object copy** (confirmed via grep: zero `ManifestWriter`/`record_captured`
  calls in it) — it never touched the live writer.
- The live writer keeps producing **brand-new** non-canonical `instrument_type=odds/data_type=trades` objects every
  single day, for every new date, indefinitely.
- So a delete of "the old non-canonical objects" today only clears the HISTORICAL backlog. Tomorrow's capture run
  recreates the exact same non-canonical shape at the new date. Without this fix, the "gated delete" is not a one-time
  cleanup — it is a recurring chore that must be re-run forever, and the honest-coverage / `is_bookmaker_league_covered`
  / manifest-swap machinery this session built and shipped will need to be re-run against a permanently-growing
  non-canonical tail.

## What a fix needs (so a future session doesn't re-derive this)

Three call sites must change **together, atomically** (verified via grep — do not assume this list is exhaustive,
re-grep before starting):

1. `venue_fetch.py:887` and `:896` — the two `f"instrument_type=odds/data_type=trades/"` path literals →
   `f"instrument_type=ODDS/data_type=TRADES/"`.
2. `venue_fetch.py:795-796` — the `shard_counts[(bm_str, "trades", league_str, "odds", fixture_str)]` key literal (2
   occurrences, get+set) → `(bm_str, "TRADES", league_str, "ODDS", fixture_str)`.
3. `manifest_finalize.py:347` — `if itype_key == "odds" and data_type_key == "trades":` →
   `if itype_key == "ODDS" and data_type_key == "TRADES":`. **Missing this one is the dangerous case**: the shard would
   still get its GCS path canonicalized, but the manifest branch would silently fall through to the generic ELSE branch
   (line 359-373), losing sports-specific `source`/`pipeline_mode` resolution AND the `available_at` stamping — a
   regression of the `sports_mtds_available_at_manifest_gap` fix, worse than the current bug.

**`sentinels.py` has 9+ additional lowercase `"odds"`/`"trades"` literal usages** (grep confirmed: lines 126-127, 228,
308-310, 350-352, 391, 420-422 — the sentinel/expectation-seeding subsystem that materializes `expected_unattempted`
rows and drives `EXPECTED_NO_FIXTURE`/coverage-gate logic). **Not fully audited in this session** — a correct fix must
grep-then-READ every one of these before touching `sentinels.py`, since this subsystem already has known fragility
(`sports_shard_enumeration_cartesian_blowup_2026_07_20.md`) and a careless casing flip risks silently breaking
expectation-seeding or the coverage gate rather than just relocating a path segment. This is exactly why the fix was
**not attempted inline** during the 2026-07-22 P0 chain session — the blast radius grew from "2 string literals" to "3
confirmed call sites + 9 unaudited ones in a fragile subsystem" mid-investigation, and rushing it risked breaking the
LIVE daily sports capture pipeline in the same session as a large prod manifest write.

## Todos

- [ ] 1. [SCRIPT] P1. Grep-then-READ every `"odds"`/`"trades"` lowercase literal in `sentinels.py` (9+ candidates listed
      above) and classify each: does it compare against a `shard_counts`-derived key (needs the same uppercase flip) or
      against something else (UAC data_type/instrument_type enums, other asset_groups' literals that coincidentally
      share the string) that must NOT change?
- [ ] 2. [SCRIPT] P1. Make the 3 confirmed call-site changes (venue_fetch.py x2 spots, manifest_finalize.py x1) +
      whatever `sentinels.py` spots todo 1 confirms need it, ALL in one commit (a partial fix is worse than no fix — see
      the "dangerous case" above). Add/update unit tests asserting the manifest row's `instrument_type`/`data_type` land
      as `ODDS`/`TRADES` for a synthetic sports shard, and that `available_at` still stamps (regression guard for the
      gap this touches).
- [ ] 3. [REVIEW] P2. Once shipped + deployed, re-verify empirically: capture a live day post-fix, confirm the new GCS
      objects AND manifest rows are `ODDS`/`TRADES` (not just code-reviewed).
- [ ] 4. [DATA] P2. Only after todos 1-3 land AND are verified live: re-scope the "gated delete of old non-canonical
      objects" in `sports_master_closeout_2026_07_21.md` to a genuinely one-time historical cleanup (today, the delete
      candidate set grows by 1 day's worth of new non-canonical objects every day this fix is not live).
