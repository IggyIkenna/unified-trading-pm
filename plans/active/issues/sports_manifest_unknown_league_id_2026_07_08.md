---
doc_type: issue
title:
  Sports manifest has 2,373 real rows with league_id="UNKNOWN", spanning all 17 sports data_types, ongoing through today
  (2025-12-15 → 2026-07-08) — root cause not yet pinned to a write call site
summary: |
  While investigating why the real sports reference catalog (prod/catalog.parquet) is bare (116 rows, all
  league-grain), found the catalog's single instrument_id="UNKNOWN" row is the DEDUPED tip of a much bigger bug:
  the real sports manifest (_index/availability_index.parquet, 4.94M rows) carries 2,373 rows with the literal
  league_id="UNKNOWN" across ALL 17 sports data_types (FIXTURES, TEAMS, STANDINGS, INJURIES, ODDS, XG, WEATHER,
  PLAYER_VALUES, etc.), dated 2025-12-15 through 2026-07-08 (today) — i.e. this is an ONGOING, currently-active
  write-path bug, not a historical artifact. Confirmed the per-fixture-entity write path
  (sports_reference_fixtures.py) explicitly guards against unmapped-league bare writes, so it is NOT the source.
  Root cause not yet traced to a specific write call site — needs a dedicated investigation, not folded into the
  broader catalog-grain-scoping plan.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, manifest, league-id, data-correctness, honest-coverage, write-path, ongoing-bug]
related:
  [
    plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    instruments-service/docs/SPORTS_INSTRUMENTS.md,
    codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: sports_master
priority: P1
source:
  SUB_AGENT_MANDATORY_RULES dispatch (slot-3 this session) — discovered while investigating the "reference catalog is
  bare" finding in instruments-service/docs/SPORTS_INSTRUMENTS.md
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
audited_scope: data-correctness
---

# Sports manifest has 2,373 rows with league_id="UNKNOWN", ongoing through today

## How I found this

Investigating `instruments-service/docs/SPORTS_INSTRUMENTS.md`'s documented finding that the real sports reference
catalog (`prod/catalog.parquet`) has "one row's key is the literal sentinel string `UNKNOWN`", I downloaded and read the
real catalog (`gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet`, 116 rows) and confirmed
it: one row has `instrument_id="UNKNOWN"`, `league_id="UNKNOWN"`, `available_from="2025-12-15"`, `available_to=None`
(still active).

The catalog's league-grain builder (`build_sports_catalogue_from_manifest()` in `scripts/build_instrument_catalogue.py`)
derives one row per DISTINCT `league_id` seen in the manifest, so a single catalog row hides how many underlying
manifest rows share that `league_id`. I downloaded and read the real manifest directly
(`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 4,935,482 total rows) and
filtered on `league_id == "UNKNOWN"`:

- **2,373 rows** — NOT one.
- Spans **all 17 sports data_types** tracked (`FIXTURES`, `TEAMS`, `STANDINGS`, `INJURIES`, `ODDS`,
  `ODDS_HORIZON_BUCKET`, `XG`, `XG_SHOTS`, `WEATHER`, `PLAYER_VALUES`, `PLAYER_STATS`, `PREDICTIONS`, `MATCHES`,
  `SFI_PROGRESSIVE_STATS`, `FIXTURE_STATS`, `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`) at roughly ~139 rows each
  (`FIXTURE_STATS`/`FIXTURE_EVENTS` slightly higher at 144).
- Date range: **2025-12-15 to 2026-07-08** — the max date is TODAY. This is an ongoing, currently-active write-path
  issue, not a one-off historical artifact that stopped recurring.

## What I ruled out

The per-fixture-entity write path (`instruments_service/engine/orchestrator/sports_reference_fixtures.py`,
`_write_per_fixture_entities` around line 500-627) explicitly guards against exactly this: it separates fixtures with a
resolved league (`_with_league`) from unresolved ones (`_without_league`), and for the unresolved set it **logs a
warning and skips the write** ("Drop unmapped rows — single-SSOT means bare writes are forbidden for league-axis data
types... Skipping bare write to keep manifest honest"). So this specific code path is NOT the source of the 2,373
`"UNKNOWN"` rows.

The `_canonical_league_id()` helper itself (`instruments_service/engine/orchestrator/sports.py:57`) also cannot
introduce the literal `"UNKNOWN"` — it either resolves a numeric id via `get_league_by_api_football_id`, strips a
provider-id suffix via UAC's `canonicalize_league_id`, or passes an unresolved input through UNCHANGED. It has no
`"UNKNOWN"` fallback branch. So whatever raw `league_id`/`league_name` value is being passed INTO this helper for these
2,373 rows must already literally be the string `"UNKNOWN"` before canonicalization — this points upstream, to one of
the LEAGUE-LEVEL fetchers (understat.py, footystats.py, weather.py, sfi.py, transfermarkt.py, or the reference-fixtures
cups/continental discovery path in `sports_reference_fixtures.py`), one of which is constructing a raw `"UNKNOWN"`
league identifier somewhere upstream of the manifest write — not yet pinned to a specific line.

One candidate pattern (NOT confirmed as this bug's source, flagged only because it's the one place in the codebase using
this exact literal as a league-identifier fallback):
`instruments_service/reference_data/adapters/sports/ adapters/api_football_reference.py:165` —
`canonical_league = build_league_id(league_country, league_name) if league_name else "UNKNOWN"` — fires when a fixture's
league name is falsy. Whether this function's output actually feeds the manifest write path for the 17 affected
data_types needs a call-graph trace; I could not confirm it in the time available.

## Why it matters

Per `codex/02-data/availability-manifest-and-data-status.md`, the manifest is the SSOT for honest-coverage calculations,
and `league_id` is one of the manifest's primary partition keys. 2,373 rows silently bucketed under a shared,
non-canonical `"UNKNOWN"` pseudo-league:

- Pollutes the league-grain catalog with a phantom "league" that isn't real (the catalog row this produces has no
  meaningful `available_to`, so it will stay "active" forever until someone notices).
- Means whatever real league(s) these 2,373 rows actually belong to are UNDER-counted in their real league's
  honest-coverage denominator (their captures are attributed to `"UNKNOWN"` instead of the real league_id) — this is a
  data-completeness correctness bug, not just a cosmetic one.
- Is CURRENTLY RECURRING (max date = today), so every day this goes unfixed adds more misattributed rows.

## Recommended next step

This needs a dedicated root-cause trace (not scoped/timeboxed in this session): query the real manifest for a sample of
the 2,373 `(date, data_type)` UNKNOWN rows, identify which specific league/fixture/team lookup is failing to resolve for
each data_type family, and follow that fetcher's code path to the exact line writing the raw `"UNKNOWN"` value. Given
the scale (17 data_types affected) it may be a SHARED upstream helper rather than 17 independently broken fetchers —
check for a common dependency (e.g. a league-name-to-id lookup table missing an entry for one specific real league)
before assuming per-fetcher fixes are needed.
