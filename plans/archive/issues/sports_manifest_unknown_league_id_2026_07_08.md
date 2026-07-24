---
doc_type: issue
title:
  Sports manifest has 2,373 real rows with league_id="UNKNOWN", spanning all 17 sports data_types, ongoing through today
  (2025-12-15 → 2026-07-08) — RESOLVED 2026-07-09, root cause pinned + fixed + backfilled
summary: |
  While investigating why the real sports reference catalog (prod/catalog.parquet) is bare (116 rows, all
  league-grain), found the catalog's single instrument_id="UNKNOWN" row is the DEDUPED tip of a much bigger bug:
  the real sports manifest (_index/availability_index.parquet, 4.94M rows) carries 2,373 rows with the literal
  league_id="UNKNOWN" across ALL 17 sports data_types (FIXTURES, TEAMS, STANDINGS, INJURIES, ODDS, XG, WEATHER,
  PLAYER_VALUES, etc.), dated 2025-12-15 through 2026-07-08 (today) — i.e. this is an ONGOING, currently-active
  write-path bug, not a historical artifact. Confirmed the per-fixture-entity write path
  (sports_reference_fixtures.py) explicitly guards against unmapped-league bare writes, so it is NOT the source.
  RESOLVED 2026-07-09: root cause pinned to a catalogue↔enumerator feedback loop
  (build_instrument_catalogue.build_sports_catalogue_from_manifest + enumerate_expected_universe._enumerate_v2_sports),
  fixed at both layers, and backfilled against real prod data (1 catalogue row + 2,373 manifest rows removed,
  0 remaining verified). See "Resolution (2026-07-09)" below for full evidence.
status: resolved
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, manifest, league-id, data-correctness, honest-coverage, write-path, resolved]
related:
  [
    plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    instruments-service/docs/SPORTS_INSTRUMENTS.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md,
  ]
created: 2026-07-08
last_updated: 2026-07-09
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
resolved_by: sub-agent dispatch (slot-3), 2026-07-09 — code fix + real prod backfill + verification
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

Per `/codex/02-data/availability-manifest-and-data-status.md`, the manifest is the SSOT for honest-coverage
calculations, and `league_id` is one of the manifest's primary partition keys. 2,373 rows silently bucketed under a
shared, non-canonical `"UNKNOWN"` pseudo-league:

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

## 2026-07-08 follow-up — re-verified with real data, re-characterizes severity, 2 more candidates ruled out

Re-pulled the real manifest (`_index/availability_index.parquet`, same 2,373 `league_id="UNKNOWN"` rows) and sampled
their `capture_status` / `venue` / `source` columns directly (not just counted them):

- **All 2,373 rows are `capture_status ∈ {expected_unattempted, empty_confirmed}` — ZERO are `captured`.** This changes
  the bug's characterization: these are honest-absence / gap-fill BOOKKEEPING rows (the "we expected data here but
  didn't get it" placeholder), not real fetched data silently mislabeled under the wrong league. The "Why it matters"
  section above ("means whatever real league(s) these rows actually belong to are under-counted... a data-completeness
  correctness bug") should be read as: a phantom "UNKNOWN" pseudo-league is polluting the DENOMINATOR/gap-tracking side
  of honest-coverage, not silently corrupting any real captured row's league attribution. Still a real, worth-fixing,
  currently-recurring bug — just a different (lower-severity) failure mode than "real data mislabeled."
- `source` is populated per data_type-family (`api_football` 983, `footystats` 278, `understat` 278, `transfermarkt`
  139, `soccer_football_info` 139, `open_meteo` 139, `mdps_odds_horizon_bucket` 139 — sums to 2,373), `venue` is blank
  on all 2,373. Every affected data_type count is exactly 139 (`FIXTURE_STATS`/`FIXTURE_EVENTS` at 144, matching the
  original finding). The fact that MULTIPLE independent source families (not just api_football) produce the identical
  "UNKNOWN" sentinel strongly suggests either (a) a shared helper all these per-source gap-fill loops call, or (b) each
  per-source enrichment orchestrator module (`footystats.py`, `understat.py`, `transfermarkt.py`, `sfi.py`,
  `weather`/`open_meteo`, `mdps` odds-horizon-bucket) has its OWN structurally-similar version of the
  `emit_empty_gaps_for_entity`-style loop found in `sports_reference_core.py` (`_AfManifestHooks`, around lines 95-133)
  and each independently hits the same edge case — this still needs a per-module trace to confirm which.
- **Ruled out (2 more candidates, checked this session):**
  1. `instruments_service/reference_data/adapters/sports/adapters/base.py:357` — this `return "UNKNOWN"` is the fallback
     branch of `_classify_error()`, an HTTP/network-error CLASSIFICATION string (alongside
     `INVALID_API_KEY`/`RATE_LIMIT_EXCEEDED`/etc.) — unrelated to `league_id` construction. Not the source.
  2. `unified_api_contracts.canonical.domain.sports.LEAGUE_REGISTRY` (via `league_classification_data_a.py` / `_b.py`)
     contains no literal `"UNKNOWN"` league_id entry (`grep -n "UNKNOWN"` on both files: zero hits) — the 94-league
     registry itself is clean; this isn't a bad static-data seed row propagating through
     `get_expected_leagues_for_source("api_football")`.
- Also checked for a generic `fillna("UNKNOWN")`-style manifest-consolidation substitution (would explain why it spans
  so many independent per-source paths uniformly) — no hit in `unified_trading_library` or `instruments-service`
  (grepped both for the literal pattern). Not ruled out entirely (a consolidator-side cause could still use a different
  literal/pattern), but the most common "blank → sentinel" idiom isn't present.
- **Did not attempt a data migration this pass**: with the exact write call site still unconfirmed, I don't know what
  the CORRECT `league_id` substitution should be for each of the 2,373 rows — rewriting them to a guessed value risks
  creating new, differently-wrong data. Recommend the dedicated trace above land FIRST, then a rewrite-in-place
  migration (operator's stated preferred mechanic) once the correct per-row league_id can be derived with confidence
  (e.g. from `fixture_id`/`date` cross-referenced against the real per-league fixtures parquet for that date, for the
  data_types that carry a `fixture_id`).

## Resolution (2026-07-09)

Root cause pinned same-day by a separate audit pass
(`plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md` item A1) and fixed + backfilled by this
dispatch. **Not a per-row-mislabel bug needing a rewrite migration** (the earlier "recommended next step" above) — these
were all bookkeeping rows (`expected_unattempted`/`empty_confirmed`/10 zero-count `captured`) minted by a feedback loop,
so the correct fix is DELETE, not rewrite-in-place.

**Root cause — catalogue↔enumerator feedback loop:**

- `instruments-service/scripts/build_instrument_catalogue.py`'s `build_sports_catalogue_from_manifest()` (~L1237,
  pre-fix) rolled the manifest into one catalogue row per distinct `league_id`, filtering only `league_id != ""` — it
  did NOT exclude the `"UNKNOWN"` sentinel, so it minted a real, persisted catalogue row
  `instrument_id="UNKNOWN"/league_id="UNKNOWN"` in `prod/catalog.parquet`.
- `instruments-service/scripts/enumerate_expected_universe.py`'s `_enumerate_v2_sports()` (~L1935, pre-fix) did
  `league_id = instr.league_id or instr.instrument_id` with no sentinel guard, read that phantom catalogue row back, and
  emitted one row per sports data_type × every alive day for it — the amplifier that grew the 2,373 manifest rows,
  recurring daily via the `enum-universe-sports-*` cron.
- The literal `"UNKNOWN"` seed traces to
  `instruments_service/reference_data/adapters/sports/adapters/api_football_reference.py:165` (fallback for a fixture
  with empty `league.name`) — frozen since the 2026-06-24 `_is_in_canonical_write_universe` write-universe gate; not
  touched by this fix.

**Code fix (both layers):**

1. `build_sports_catalogue_from_manifest()` now excludes `SPORTS_LEAGUE_ID_SENTINELS` (`{"UNKNOWN"}`, case-insensitive)
   before the roll-up. Deliberately a NARROW sentinel check, not a full `LEAGUE_REGISTRY` membership check — verified
   against the real prod catalogue that 22 real leagues (raw numeric long-tail ids, `LA_LIGA_2`, `RFPL`,
   `SCOTTISH_LEAGUE_CUP_185`) are not in `LEAGUE_REGISTRY`; a membership-based filter would have wrongly dropped all 22.
2. `_enumerate_v2_sports()` carries a matching defense-in-depth sentinel guard so it can never re-amplify a phantom
   league into expected/empty rows even if one somehow re-enters the catalogue.
3. Regression tests added:
   `tests/unit/scripts/test_build_instrument_catalogue.py::test_sports_catalogue_from_manifest_excludes_sentinel_league_ids`,
   `tests/unit/scripts/test_enumerate_expected_universe_v2.py::test_sports_v2_sentinel_league_id_never_emits_rows`.

**Backfill (real prod GCS, `instruments-store-sports-prd-central-element-323112`, 2026-07-09):**

- Verified before deleting: `prod/catalog.parquet` had exactly 1 `league_id="UNKNOWN"` row;
  `_index/availability_index.parquet` had exactly 2,373 (1,352 `expected_unattempted` + 1,011 `empty_confirmed` + 10
  `captured`, all 10 `instrument_count=0` with `error_reason="reconciled_from_existing_per_league_parquet"` written once
  2026-05-01 — the frozen bootstrap rows, no real captured data found under the sentinel beyond them, matching this
  doc's 2026-07-08 follow-up finding exactly). Two `_index/per_vm/*.parquet` shards checked: 0 `UNKNOWN` rows in either
  — no per-VM cleanup needed.
- Backed up both objects first (`prod/catalog.20260708-234112.unknown_league_backfill.bak.parquet`,
  `_index/availability_index.20260708-234112.unknown_league_backfill.bak.parquet`), then deleted: catalogue 116 → 115
  rows; manifest index 2,373 rows removed.
- Script: `instruments-service/scripts/backfill_remove_unknown_league_phantom_2026_07_09.py` (`--dry-run` / `--apply` /
  `--verify-only`; hard-aborts before writing if any `captured` row under the sentinel has non-zero `instrument_count`).

**Verification the loop is broken (not just patched at one layer):**

- Post-backfill `--verify-only`: 0 sentinel rows remaining across catalog, manifest index, and per-VM shards.
- Re-downloaded the LIVE post-backfill manifest and ran it through the PATCHED `build_sports_catalogue_from_manifest` —
  0 `"UNKNOWN"` rows minted (proves a real catalogue rebuild against current prod data cannot resurrect the phantom).
- Unit-level: constructed a synthetic `league_id="UNKNOWN"` catalog entry and ran it through the patched
  `_enumerate_v2_sports` — 0 rows emitted for it, while a sibling real-league entry in the same call emitted rows
  normally (control passed).

Ship: `instruments-service` (code fix + tests + backfill script), `docs/SPORTS_INSTRUMENTS.md` (updated in place), this
doc. Via quickmerge, quality-gates green.
