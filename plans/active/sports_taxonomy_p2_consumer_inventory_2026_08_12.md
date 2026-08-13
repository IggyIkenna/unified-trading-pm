---
doc_type: plan
title: Sports taxonomy P2 — consumer inventory for the renamed/retired/collapsed tokens
summary: >-
  Required output of P2's "Consumer enumeration" gating todo, per the codex entity-rename-and-split-consumer-migration
  rule. Enumerates every consumer (writer, reader, path-prefix matcher, filename matcher, registry-membership binder,
  config-dict-key binder, and literal column/variable) of each token P2 renames/retires/collapses, across 7 repos:
  market-tick-data-service, market-data-processing-service, instruments-service, unified-api-contracts,
  features-service, ml-service, deployment-api. Produced via 7 parallel per-repo enumeration passes, 2026-08-12. The P2
  re-stamp/purge todos cite this doc as their consumer checklist.
status: active
nature: record
asset_group: [sports]
stage: [data]
repos:
  [
    market-tick-data-service,
    market-data-processing-service,
    instruments-service,
    unified-api-contracts,
    features-service,
    ml-service,
    deployment-api,
  ]
scope: [engineer]
tags: [sports, migration, canonicalisation, consumer-inventory, rename-rule]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md,
    /codex/02-data/entity-rename-and-split-consumer-migration-rule.md,
  ]
created: 2026-08-12
last_updated: 2026-08-12
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
supersedes:
superseded_by:
resolved_by:
depends_on:
source: ["P2's Consumer-enumeration gating todo, dispatched to slot 32, 2026-08-12"]
locked_by:
locked_since:
drift_direction: advance-code
---

# Sports taxonomy P2 — consumer inventory

> Per `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md`: **a grep of the renamed token is not a
> sufficient enumeration.** Consumers bind five ways: (1) GCS path prefix, (2) filename, (3) registry/constant
> membership, (4) config/frontmatter dict key, (5) the literal data_type/instrument_type/venue column or variable. Every
> finding below is tagged with its binding type. Zero-consumer findings are stated explicitly, never omitted.

## How this was produced

7 parallel Explore-agent passes, one per repo, each instructed to check all 5 binding types (not just grep) for every
token P2 touches. Findings below are organized by rename target; each cites `file:line` + binding type. This is a
synthesis of those 7 passes — the full per-repo transcripts are not preserved here, only the actionable findings.

**Repos NOT covered by this enumeration** (state explicitly, per the codex rule's honesty requirement):
`strategy-service` — P3's plan names `strategy_service/adapters/sports/arbitrage_detector.py` as a live consumer of
sports odds/arb data; it was not in this task's required minimum-surfaces list and was not searched. `execution-service`
and `system-integration-tests` were not searched either. If a re-stamp todo owner finds a consumer in one of these
repos, add it here rather than assuming this list is exhaustive there.

---

## 1. `trades` → `odds` (375,257 shards, 2020-06-06 → present)

| Consumer                                                                                                                                                                          | Binding     | Repo                                                                                                  |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------- |
| `_build_sports_shard_path()` — hardcodes `data_type=trades/ticks.parquet` (batch writer)                                                                                          | path-prefix | MTDS `engine/orchestrator/venue_fetch.py:852-881`                                                     |
| `sports_live_tick_blob_path()` — identical leaf, live writer, docstring says "mirrors batch EXACTLY"                                                                              | path-prefix | MTDS `live/_sports_tick_path.py:25-56`                                                                |
| `betfair_adapter.py::_trades_row_dict()` stamps `"data_type": "trades"` (scaffolded, not yet wired into the capture loop)                                                         | literal     | MTDS `market_interface/adapters/sports/betfair_adapter.py:423-489`                                    |
| `sports_catalog_reader.py:133` — literal `data_type="trades"` in reader query builder                                                                                             | literal     | MTDS                                                                                                  |
| `rebuild_sports_manifest_v9.py::_source_from_row()` — `dt_str.lower()=="trades" → "odds_api"`                                                                                     | literal     | MTDS `scripts/rebuild_sports_manifest_v9.py:218`                                                      |
| `_PER_FIXTURE_DERIVED_DATA_TYPES`/`_FIXTURE_GUARANTEED_DATA_TYPES` frozensets, `.upper() in set` membership test                                                                  | registry    | MTDS `scripts/rebuild_sports_manifest_v9.py:114-166`                                                  |
| `sentinels.py::_resolve_pipeline_mode_for_sentinel(venue,"trades",default=BATCH_ODDS_API)`                                                                                        | literal     | MTDS `engine/orchestrator/sentinels.py:230`                                                           |
| Many `scripts/sports/*` one-off migration tools hardcode `instrument_type=odds/data_type=trades/` path regexes (lifecycle-marked, would break if re-run post-rename)              | path-prefix | MTDS `scripts/sports/{league_id_relocation,exchange_fixed_odds_fork,k1k2_casing_revert_2026_07_27}/*` |
| `related_data_types=["odds","trades","ODDS","TRADES"]` — MDPS horizon-bucket adapter dual-accepts `trades`                                                                        | literal     | MDPS `app/adapters/sports/bucket_assignment_adapter.py:705`                                           |
| `_MDPS_SOURCE_DATA_TYPE_TO_PRIORITY_KEY[("sports","trades")]` bridge to UAC `SOURCE_PRIORITY`                                                                                     | config-key  | MDPS `app/core/canonical_writer_stamping.py:82,101`                                                   |
| **CAUTION**: `trades_adapter.py` literal key `"trades"` also exists for `cefi`/`tradfi`/`prediction` — **out of sports scope, do NOT touch** (same literal token shared cross-AG) | literal     | MDPS `app/adapters/{cefi,tradfi,prediction}/trades_adapter.py`                                        |
| `_raw_sports_data_types = frozenset({"trades","odds"})` gates the sports staleness check                                                                                          | registry    | MDPS `app/core/dependency_checker.py:910`                                                             |
| `_DATA_TYPE_TO_MDPS_PREFIX["trades"]="ohlcv"` used by `mdps_data_type_key()`                                                                                                      | config-key  | MDPS `app/core/canonical_writer_shaping.py:214,248,787`                                               |
| `reprocess_sports_odds.py` — `_LEGACY_PATH_TEMPLATE` embeds `data_type=trades/ticks.parquet`                                                                                      | path-prefix | MDPS `scripts/reprocess_sports_odds.py:99,111,168`                                                    |
| `_source_priority`, `_ENTITY_TO_DATA_TYPE`/`candidate_parquet_paths` etc. — no direct `trades` binding found in UAC beyond `DATA_TYPES_BY_ASSET_GROUP["sports"]` membership       | registry    | UAC `market_data_categories.py:317-356`                                                               |
| `_sports_target_generator.py` — zero hits for bare `trades`                                                                                                                       | —           | ml-service: **zero consumers**                                                                        |
| `_SPORTS_ODDS_SOURCE_KEY="odds_api"`, `_SPORTS_ODDS_DATA_TYPE="trades"` module constants, used at `missing_data_types=[...]`/`source_key=...`                                     | literal     | deployment-api `services/data_status/mtds.py:258-259,312,347`                                         |
| `_schema.py::_SPORTS_DATA_TYPE_TO_INSTRUMENT_TYPE` dict: `"trades": "odds"` — resolves UI-supplied instrument_type for UAC contract-key lookups                                   | config-key  | deployment-api `services/data_status_drilldown/_schema.py:108`                                        |

**No consumer found** (checked, confirmed absent): features-service (only the `data_type=odds` raw path exists there,
see §5).

---

## 2. `trades_inplay` → retired, folds into `odds` + `in_play=true` column

**Zero consumers found in MTDS, MDPS, features-service, ml-service, or deployment-api** — checked via literal grep +
`inplay`/`in_play` case-insensitive grep + filename-match search (`_is_consumable_trades_blob`/`inplay_ticks.parquet`
specifically, per the plan's own named target). Only comment-level mentions found (2, in dated MTDS migration scripts,
both explicitly noting the token was "left untouched").

**One real hit**: `filename-match binding` — UAC `market_data_categories.py:352-354` documents `trades_inplay` rows are
distinguished from `trades` PURELY by filename (`inplay_ticks.parquet` vs `ticks.parquet`), enforced by
`market-tick-data-service/.../reprocess_sports_odds.py::_is_consumable_trades_blob` (cross-referenced from UAC but the
actual matcher lives in MTDS — **search this again**: the MTDS agent's pass did not find this specific function by that
name; re-verify `_is_consumable_trades_blob`'s current location/name before the re-stamp todo runs — possible drift
between the UAC comment and current MTDS code, or the function was renamed/moved since the comment was written).

**Action for the re-stamp todo**: since the filename-match function's exact current location is unconfirmed, the todo
must grep `reprocess_sports_odds.py` fresh at run time for `inplay` before assuming it doesn't exist — the UAC citation
is second-hand evidence, not a direct read.

---

## 3. 19-token instruments-service uppercase vocabulary (lowercasing)

**Vocabulary is DEFINED in UAC**, not instruments-service: `unified_api_contracts.sports.SPORTS_DATA_TYPE_TO_SOURCE`
dict keys + individual constants (`FIXTURES_SCHEDULE`, `FIXTURES_OUTCOMES`, etc). instruments-service is the heaviest
**consumer/producer**, not the owner.

### 3a. instruments-service (heaviest consumer — 8 distinct registry-membership sites)

- `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` dict — 16 of 19 tokens as keys. **Missing `XG_SHOTS` and `ODDS_HORIZON_BUCKET`**
  — verify their pipeline_mode resolution separately. `engine/orchestrator/__init__.py:170-206`.
- `_SPORTS_CORE_ENTITIES` (`TEAMS`,`STANDINGS`,`INJURIES`), `_SPORTS_PER_FIXTURE_ENTITY_NAMES` (`FIXTURE_STATS`,
  `FIXTURE_EVENTS`,`FIXTURE_LINEUPS`,`PLAYER_STATS`), `_ENRICHMENT_ENTITY_VENUES` (`MATCHES`,`PREDICTIONS`,`ODDS`,`XG`,
  `PLAYER_VALUES`,`SFI_PROGRESSIVE_STATS`,`WEATHER`), `_SPORTS_PER_LEAGUE_ENTITIES` (13 tokens + literal
  `ODDS_HORIZON_BUCKET` — direct hit, easy to miss since not UAC-imported here) — all
  `engine/orchestrator/process_preflight.py:53-189`.
- **`_FIXTURES_ENTITY_ALIASES = frozenset({"FIXTURES", FIXTURES_SCHEDULE})`** (`process_preflight.py:202`) — dual-key
  bridge from a PRIOR partial rename (`FIXTURES`→`FIXTURES_SCHEDULE`). **Must update both sides** or
  `--sports-entity FIXTURES` CLI path silently breaks.
- `_API_FOOTBALL_FIXTURES_DATA_TYPES = frozenset({"FIXTURES","FIXTURES_SCHEDULE"})` — manifest membership test gating
  the cross-adapter dependency check. `reference_data/sports_dependency.py:97`.
- `_ENTITY_DT_BY_SHORT` config dict (`"fixture_stats":"FIXTURE_STATS"` etc.) —
  `engine/orchestrator/sports_reference_fixtures_write.py:44-47`.
- `writers.py`/`catalogue.py::_sports_prefixes = ("API_FOOTBALL","TRANSFERMARKT","FOOTYSTATS","SFI","UNDERSTAT","WEATHER")`
  — derives `manifest_data_type` by **string-slicing** the venue path segment (`venue_str[len(pfx)+1:]`), e.g.
  `"API_FOOTBALL_INJURIES"` → `"INJURIES"`. **Invisible to literal-token grep** — if the uppercase suffix is lowercased,
  this slicing produces a mismatched token unless updated in lockstep. `engine/orchestrator/writers.py:236,250-260`,
  `engine/orchestrator/catalogue.py:135-145`.
- `PredictionFixtureResolver` (Kalshi/Polymarket soccer crosswalk) calls
  `candidate_parquet_paths("FIXTURES", day, league, pipeline_mode=BATCH_API_FOOTBALL)` — a genuine cross-asset-group
  consumer living inside instruments-service. `reference_data/adapters/prediction/fixture_match.py:377-390`.

### 3b. ⚠️ CRITICAL PRECEDENT — `enumerate_expected_universe.py`'s override-dict pattern

`scripts/enumerate_expected_universe.py` (4742 lines) computes the sports expected-universe denominator. It **already
carries direct, in-repo proof of a prior partial-lowercase incident**:

- `_sports_data_types()` (line 268-281) iterates `sorted(SPORTS_DATA_TYPE_TO_SOURCE.keys())` — the full uppercase axis.
- `_SPORTS_MANIFEST_DATA_TYPE_OVERRIDE` (305-317) + `_SPORTS_MANIFEST_VENUE_OVERRIDE` (363-382) translate the
  UAC-uppercase axis key to the REAL on-disk manifest string at row-emission time. It already contains
  `"ODDS_HORIZON_BUCKET": "odds_horizon_bucket"` — **documenting a previously-shipped partial lowercase of exactly this
  token**, written by MDPS's `reprocess_sports_odds.py`, that caused a confirmed **0-overlap mismatch between 209,526
  uppercase-seeded `expected_unattempted` rows and 123,642 real lowercase-cased captured rows** (root-caused 2026-07-13,
  `sports_data_sources_canonical_completion_2026_07_13.md` §1). It also holds `"FIXTURES": "FIXTURES_SCHEDULE"`
  documenting a second historical mismatch.
- `_enumerate_v2_sports` (2442-2760) calls `_sports_manifest_data_type(dt)`/`_sports_manifest_venue(dt)` at every
  row-emission point to translate casing before stamping/matching.
- `_RETIRED_SPORTS_DATA_TYPES` (164-172) — defensive frozenset of already-retired legacy tokens.

**VERDICT (binding on the re-stamp todos): the override-dict pattern is the proven, correct mechanism to route this
migration through.** Extend `_SPORTS_MANIFEST_DATA_TYPE_OVERRIDE`/`_SPORTS_MANIFEST_VENUE_OVERRIDE` with every one of
the 19 tokens' new lowercase mapping (or flip the dict's default to identity-lowercase) — do NOT invent a new
translation layer, and do NOT skip this file. Skipping it repeats the identical incident at 19x scope instead of 1x.

### 3c. features-service, ml-service, deployment-api — dict-key consumers

- features-service: `gcs_reader.py::_ENTITY_TO_DATA_TYPE` (17 of 19 tokens, feeds `candidate_parquet_paths()`) +
  `compute/coverage_gate.py::DATA_TYPE_TO_REF_KEY` (13 tokens). **Self-documented gap**: `coverage_gate.py`'s own header
  comment (58-66) states `STANDINGS`, `VENUES`, `WEATHER`, `ODDS`, `ODDS_HORIZON_BUCKET` are NOT gated — they read via
  dedicated helpers instead, bypassing this coverage check entirely. A rename of `ODDS`/`ODDS_HORIZON_BUCKET` would
  silently miss this gate.
- ml-service: **zero direct consumers** of the 19-token vocabulary — it is two layers downstream, consuming
  features-service's derived `feature_group` names and MDPS's `odds_horizon_bucket` path segment instead (see §5, §7).
- deployment-api: `sports_helpers.py::SPORTS_DATA_TYPE_META` — 15 of 19 tokens as dict keys, drives data-status coverage
  math. A renamed token leaves a dead key here, silently dropping that data_type from coverage.
  `services/data_status/sports_helpers.py:75-231`. `data_status_drilldown/_fixtures_pools.py::_FIXTURE_ENTITIES` —
  8-tuple of `(label, "entity=<x>", "<x>.parquet")` (exactly the path-suffix + filename binding the codex rule warns
  about): `FIXTURES`/`FIXTURE_STATS`/`FIXTURE_LINEUPS`/`FIXTURE_EVENTS`/`PLAYER_STATS`/`INJURIES`/`XG`/`WEATHER`. Both
  label AND path-suffix/filename must move together or downloads 404 silently. `_fixtures_pools.py:29-39,271-295`.
  `breakdowns_domain.py:117,626,692` — direct `data_type=="FIXTURES"` column-literal comparisons, ground-truth
  denominator for every other sports entity's expected-date count.

### 3d. Non-canonical UAC producers of uppercase `ODDS` (two SEPARATE populations, both real)

- FOOTYSTATS `ODDS` (uppercase): 6,306 CAPTURED shards — a comment near
  `SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE` was self-corrected 2026-08-08 (already fixed in-source, no further
  edit needed): the original "4 stale rows" claim was wrong for this population; 4-stale-rows is accurate ONLY for
  `ODDS_MOVEMENT`+`ODDS_SNAPSHOT` (2+2).
- A SEPARATE, still-registered uppercase-`ODDS` capability declaration: `data_type_capability.py:1091-1093`,
  `DataTypeCapability(asset_group=SPORTS, data_type="ODDS", venue="ODDS_API", ...)` (~17K rows). **Both populations must
  be accounted for** in any `ODDS`→`odds` migration — they are not the same rows.

---

## 4. Fold footystats `ODDS` (6,306) + `odds` (16,207) into one `odds`

Covered by §3d above (the UAC accepted-exception registry + capability declaration). No additional consumer found beyond
the two UAC sites and the general `trades`/`odds` binding sites in §1.

---

## 5. `odds_horizon_bucket` → collapsed onto `odds` + `horizon` axis (135,980 shards: MDPS 121,762 / MTDS 14,656 / IS 1,106)

This is the **largest, most heavily-consumed** token in the migration. Consumer sites:

| Consumer                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Binding                                                           | Repo                                                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bucket_assignment_adapter.py` — `@CandleAdapterRegistry.register(SPORTS,"odds_horizon_bucket")`, `data_type="odds_horizon_bucket"`                                                                                                                                                                                                                                                                                                                                                                                             | registry+literal                                                  | MDPS `app/adapters/sports/bucket_assignment_adapter.py:687,696`                                                                                                                                                                             |
| `canonical_writer_stamping.py::_MDPS_SOURCE_DATA_TYPE_TO_PRIORITY_KEY[("sports","odds_horizon_bucket")]="ODDS_HORIZON_BUCKET"`                                                                                                                                                                                                                                                                                                                                                                                                  | config-key                                                        | MDPS `app/core/canonical_writer_stamping.py:120`                                                                                                                                                                                            |
| `_sports_derived = frozenset({"odds_snapshot","odds_movement","odds_horizon_bucket"})` gates staleness guard                                                                                                                                                                                                                                                                                                                                                                                                                    | registry                                                          | MDPS `cli/handlers/process_handler.py:376-399`                                                                                                                                                                                              |
| `canonical_writer_shaping.py` — deliberately NOT in `_DATA_TYPE_TO_MDPS_PREFIX`, falls through to `f"{dt}_{tf}"` (i.e. `odds_horizon_bucket_{tf}`) — **re-verify this fallback still resolves post-rename**                                                                                                                                                                                                                                                                                                                     | fallback/implicit                                                 | MDPS `app/core/canonical_writer_shaping.py:207,268`                                                                                                                                                                                         |
| 5 migration/backfill scripts hardcode `pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/data_type=odds_horizon_bucket` path segment                                                                                                                                                                                                                                                                                                                                                                              | path-prefix                                                       | MDPS `scripts/{migrate_odds_horizon_bucket_venue_to_bookmaker,reclassify_odds_horizon_bucket_unresolvable_rows,reprocess_sports_odds,close_odds_horizon_bucket_expected_unattempted_cells,backfill_odds_horizon_bucket_missing_shards}*.py` |
| `_MANIFEST_DATA_TYPE="odds_horizon_bucket"`, `_MANIFEST_SOURCE="mdps_odds_horizon_bucket"` — used throughout for manifest writes                                                                                                                                                                                                                                                                                                                                                                                                | literal                                                           | MDPS `scripts/reprocess_sports_odds.py:265,278,979,1001,1177,1203,1212`                                                                                                                                                                     |
| Timeout registry `_FAMILY_TIMEOUT_OVERRIDES[("SPORTS","odds_horizon_bucket")]=3600`                                                                                                                                                                                                                                                                                                                                                                                                                                             | registry                                                          | MDPS `scripts/pipeline_e2e_check.py:299`                                                                                                                                                                                                    |
| **`_SOURCE_SCOPED_PREFLIGHT_VENUES`/`_SOURCE_SCOPED_FRESHNESS_VENUES = frozenset({"ODDS_API"})`** — enrolled specifically because an MDPS `odds_horizon_bucket` rollup row (venue=`ODDS_API`) falsely pinned freshness dates forever (fixed a "572 permanently-skipped odds days" bug)                                                                                                                                                                                                                                          | registry, **coupled to §6's venue rename**                        | MTDS `engine/orchestrator/preflight.py:65-82`, `cli/handlers/tick_data_handler.py:56-80`                                                                                                                                                    |
| `rebuild_sports_manifest_v9.py` — `ODDS_HORIZON_BUCKET` in both `_PER_FIXTURE_DERIVED_DATA_TYPES` and excluded from `_FIXTURE_GUARANTEED_DATA_TYPES`                                                                                                                                                                                                                                                                                                                                                                            | registry                                                          | MTDS `scripts/rebuild_sports_manifest_v9.py:125,148`                                                                                                                                                                                        |
| `migrate_sports_canonical_v9.py` — casing-normalization dict `ODDS_HORIZON_BUCKET`→lower                                                                                                                                                                                                                                                                                                                                                                                                                                        | config-key                                                        | MTDS `scripts/migrate_sports_canonical_v9.py:123-129`                                                                                                                                                                                       |
| `_ODDS_HORIZON_BUCKET_MANIFEST_VENUE_AGGREGATE="ODDS_API"`, `_ODDS_HORIZON_BUCKET_MANIFEST_DATA_TYPE="odds_horizon_bucket"` — manifest `row_key` value                                                                                                                                                                                                                                                                                                                                                                          | registry-value                                                    | features-service `sports/data/gcs_reader.py:571-573`                                                                                                                                                                                        |
| **`_BUCKETED_ODDS_CANONICAL_PREFIX`/`_BUCKETED_ODDS_LEGACY_PREFIX`** — `processed/by_date/day={date}/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/data_type=odds_horizon_bucket/` — consumed via `list_blobs(prefix=...)`, a pure prefix match, NOT a column read. Fan-out callers: `sports_feature_loader.py` (ml-service, own independent copy — see below), `odds_features_exporter.py:329`, `odds_targets_exporter.py:54`, `sports/arb/runner.py` (all via `read_bucketed_odds()`, one central function) | **path-prefix, the canonical example the codex rule warns about** | features-service `sports/data/gcs_reader.py:562-675`                                                                                                                                                                                        |
| **`ml_service/training/app/core/sports_feature_loader.py:35-38`** — `_ODDS_BUCKETED_PREFIXES` = the SAME two prefix strings, an INDEPENDENT copy explicitly modeled on features-service's (per its own comment) — does NOT delegate, must be updated separately                                                                                                                                                                                                                                                                 | path-prefix (independent copy)                                    | ml-service                                                                                                                                                                                                                                  |
| P3's own already-open todo ("Move the sports feature loader off its PATH-PREFIX read of bucketed odds") names this exact ml-service consumer and has been **prematurely dispatched 4x** because this P2 re-stamp hasn't landed yet; it is now durably parked pending `POST /api/prerequisites/auto_unpark__sports_taxonomy_p3_consumers-13983a72aba5 {"value":true}` — **whoever lands this P2 re-stamp MUST clear that condition afterward**, or P3's loader-migration todo sits invisibly parked forever                      | —                                                                 | cross-plan                                                                                                                                                                                                                                  |
| `process_preflight.py:187` `_SPORTS_PER_LEAGUE_ENTITIES` includes literal `ODDS_HORIZON_BUCKET` (not UAC-imported here)                                                                                                                                                                                                                                                                                                                                                                                                         | literal                                                           | instruments-service                                                                                                                                                                                                                         |
| `enumerate_expected_universe.py`'s override dict (§3b) — the ALREADY-LANDED partial fix for this exact token                                                                                                                                                                                                                                                                                                                                                                                                                    | config-key                                                        | instruments-service                                                                                                                                                                                                                         |

**Coupling warning**: MTDS's `preflight.py`/`tick_data_handler.py` freshness fix is keyed on the CO-OCCURRENCE of
`odds_horizon_bucket` + venue=`ODDS_API`. If this re-stamp AND §6's `ODDS_API` re-attribution land in the same migration
(per the plan), **both frozensets must be re-verified together** — a rename of one without the other could silently
reintroduce the "572 permanently-skipped days" bug.

---

## 6. Re-attribute `ODDS_API` and `FOOTYSTATS` venue rows

- MTDS: `umi_tick_provider.py::_SPORTS_VENUES=frozenset({"ODDS_API","BETFAIR"})`; `venue_fetch.py:85,100`
  `{"ODDS_API":"odds_api"}` source map + `_LEAGUE_PARTITIONED_VENUES=frozenset({"ODDS_API"})`;
  `_is_meta_snapshot_blob()` filename-matches `"ODDS_API:SPORT:"` prefix (a **filename binding**, MTDS
  `scripts/reprocess_sports_odds.py:178-180`
  - `scripts/sample_bm_minutes_distribution.py:83-85`); `_MANIFEST_VENUE_AGGREGATE="ODDS_API"` fallback sentinel in 3
    scripts; `reader.py:189-198` comments confirm ODDS_API/FOOTYSTATS were **already removed from the VENUE axis** for
    ~146K CEFI-bucket rows in a prior migration, but manifest rows still carry `venue=ODDS_API`/`FOOTYSTATS` "until the
    P2 migration" — **this rename is continuing a known-incomplete prior migration, not fresh ground**.
    `scripts/sports/restamp_sports_bookmaker_venue_2026_07_27.py::REWRITE_SPECS` already re-attributes some
    `ODDS_API`-mislabeled rows to `FOOTYSTATS` — read this script's `REWRITE_SPECS` dict as the starting template for
    the full re-attribution; it explicitly excludes UNIBET_UK/EU and SMARKETS folds as "genuinely distinct."
    `market_interface/adapters/sports/odds_api_adapter.py::REQUESTED_ODDS_API_BOOKMAKERS` (23 real per-bookmaker keys)
    is the likely correct target list.
- MDPS: `FOOTYSTATS` has **no executable path/filename/registry binding** — only comments noting
  `pipeline_mode=batch_footystats` is deliberately excluded per a 2026-06-27 ruling (footystats odds excluded from
  arbitrage). `ODDS_API` bindings are covered in §5's table.
- UAC: `ODDS_API` removed from `VENUES_BY_ASSET_GROUP["sports"]` 2026-08-08 (it's a SOURCE, not a venue) but remains
  live in 6 other registries: `venue_constants.py:183` (definition), `venue_mapping.py:45`, `session_times.py:120`,
  `data_availability.py:102-108`, `capability_declarations/_sports.py:167-175`, `data_type_capability.py:1093`. All 6
  need updating if `ODDS_API` is retired as a token entirely (vs. just re-attributed row-by-row). `FOOTYSTATS` has a
  **deliberately disjoint dual role** (§9's sibling note): the sports odds-bookmaker exception
  (`SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS`) vs. a separate canonical instruments-service reference-data venue
  (`registry/__init__.py:819`, `venue_adapter_keys.py:238`, `canonical_mappings.py:149`) — **do not merge these two
  FOOTYSTATS identities**, they are intentionally different things.
- features-service: **THREE independent copies** of the raw `venue=ODDS_API/data_type=odds/ticks.parquet` path logic —
  `gcs_reader.py::read_odds_data` (own reader), `gcs_reader.py`'s manifest-key literal, and
  `cross_instrument/app/calculators/prediction_cross_venue_betfair.py::_SPORTS_ODDS_PATH_SUFFIX`/`_SPORTS_ODDS_PATH_SEGMENTS`
  (a fully separate implementation, does NOT delegate to `gcs_reader.py`). **All three must be migrated together** — a
  rename that only touches `gcs_reader.py` misses `prediction_cross_venue_betfair.py` entirely.
- ml-service: venue-classification via substring membership on the instrument_id venue prefix —
  `feature_query_support.py::_get_asset_group` set = `{"ODDS_API","BETFAIR","API_FOOTBALL","ODDSPAPI","FOOTYSTATS"}`;
  **`cross_asset_training_pipeline.py::_infer_domain`'s copy is `("ODDS_API","BETFAIR","API_FOOTBALL")` — MISSING
  `FOOTYSTATS`**. This is a **pre-existing bug** (a FOOTYSTATS-derived instrument_id misclassifies as CEFI via this
  second path) — flag as a fix-in-passing item for whoever lands this re-attribution, since both copies need touching
  anyway. `_ODDS_API_TEAM_MAPPING_BLOB="sports_reference/mappings/odds_api_team_mapping.parquet"` — a filename binding
  on the crosswalk blob itself (`sports_feature_loader.py:41-43,258,296`).
- deployment-api: `_distinct_values.py` reads `ODDS_API` via `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS`;
  `sports.py::_SPORTS_REFERENCE_PREFIXES` contains `"FOOTYSTATS_"` (prefix-match binding); `data_status_mock.py`
  hardcodes `FOOTYSTATS` in the mock-venue list; `backfill_launch.py::FOOTYSTATS_BACKFILL` enum member (unrelated
  subsystem, same venue token — the backfill-VM launcher, not data-status).

---

## 7. Move `odds_snapshot` (16,521) + `odds_movement` (16,470) onto `data_type=odds` + `timeframe`

- MDPS: `odds_snapshot_adapter.py`/`odds_movement_adapter.py` registry keys; `canonical_writer_stamping.py` config-key
  bridge (`"ODDS_SNAPSHOT"`/`"ODDS_MOVEMENT"`); `_sports_derived` frozenset (§5); **deliberate exclusion** from
  `_DATA_TYPE_TO_MDPS_PREFIX` documented at `canonical_writer_shaping.py:200-212` with an explicit comment warning this
  is a collision risk with `odds_ohlcv_{tf}` if "fixed" by adding them later — **re-read this comment before touching
  the table**; `restamp_sports_candle_venue_2026_08_03.py::DATA_TYPES` tuple includes both.
- UAC: removed from `DATA_TYPES_BY_ASSET_GROUP["sports"]` already (2026-08-08, per `market_data_categories.py:319-322`
  comment) but still present in
  `_SPORTS_ODDS_DERIVED_CANDLE_PREFIXES=("odds_movement_","odds_snapshot_", "odds_horizon_bucket_","arbitrage_opportunity_")`
  — a **prefix-matching consumer** in `contracts.py:1201-1246`, invisible to an exact-string grep: any data_type
  STARTING WITH one of these falls back to the `("sports","odds",...)` contract regardless of suffix. Also present (as a
  2-row-only accepted exception) in `SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE`.
- ml-service, deployment-api: no direct consumer of these two tokens as literal data_type values — only as feature
  COLUMN name prefixes (`odds_movement_pinnacle_diff_home` etc, ml-service `mock_data_provider.py:388`), unrelated to
  the taxonomy axis.

---

## 8. Purge `exchange_odds` / `fixed_odds` instrument_type (60,095 shards: 35,622 + 24,473)

- MTDS: only in one-off remediation scripts
  (`scripts/sports/exchange_fixed_odds_fork/{move_odds_unambiguous_venues, manifest_reconcile,move_odds_ambiguous_venues}_2026_07_27.py`)
  — dict `{"ODDS_API":"fixed_odds",...}` + path template `instrument_type={exchange_odds,fixed_odds}/data_type=trades/`.
  Lifecycle-marked "delete when 0 shards remain" — not live pipeline code, but confirms real manifest rows still carry
  both values, split WITHIN venues (per the plan's own note: BETFAIR_EX_UK has both).
- MDPS: only ONE consumer — `mock_data_provider.py:116` (`FIXED_ODDS`→empty string, mock/synthetic-data generation,
  dev-only). `exchange_odds` has **zero MDPS consumers**. No per-venue instrument_type mapping references
  `BETFAIR_EX_UK` in this repo.
- instruments-service: **two real producer adapters** — `betfair.py:110-113,383` (`InstrumentType.EXCHANGE_ODDS` +
  literal `"EXCHANGE_ODDS"` string filter), `api_football_reference.py:79-82,189` (`InstrumentType.FIXED_ODDS` + literal
  filter). These must both be migrated if the purge lands.
- UAC: venue-resolver `registry/_sports_venue_constants.py:84-119` (derive-at-read-time function mapping VENUE→
  `exchange_odds`/`fixed_odds`); `venue_constants.py:579-580` config map;
  `CONTRACT_REGISTRY[("sports","exchange_odds", "trades")]`/`[("sports","fixed_odds","trades")]` in
  `_sports_prediction_contracts.py:641-642`; **path-prefix consumer** at `contracts.py:1208-1220` — comment documents
  "GCS objects move venue-by-venue into `exchange_odds/` or `fixed_odds/` partitions" — a LIVE, in-progress path
  migration, plus dual-read fallback `_SPORTS_ODDS_FORK_INSTRUMENT_TYPES=("exchange_odds","fixed_odds")` at line 1220.
- features-service, ml-service, deployment-api: **zero consumers found** for either token, all binding types checked.

---

## 9. Delete 20,785 KALSHI `empty_confirmed` rows (source `polymarket_clob`) — cross-AG bleed into sports

- MTDS: no current manifest-writing code targets sports with a KALSHI/`polymarket_clob` source, but **confirmed,
  already-remediated-but-RECURRING** contamination: `scripts/sports/remediate_cross_ag_prediction_bleed_2026_07_23.py`
  - a "round 3" follow-up (`..._round3_2026_07_24.py`, because "the 2026-07-20 remediation didn't hold"). This has
    recurred at least 3 times — flag to the delete todo as a regression-risk pattern if venue/source axes are touched
    again in this same migration.
- instruments-service: `process_write.py:415-450` stamps prediction rows with `asset_group="prediction"` explicitly —
  not sports. The likely bleed mechanism is `PredictionFixtureResolver` (`kalshi.py:260-269,1286-1362`) which READS the
  sports `FIXTURES` parquet to compute `sports_canonical_instrument_id` for Kalshi soccer markets, joining
  Kalshi/prediction rows to sports fixture/team IDs — a genuine consumer of the `FIXTURES` token (already listed §3a)
  that touches this bleed indirectly.
- UAC: `KALSHI` is a real, correct `VENUES_BY_ASSET_GROUP["prediction"]` member (`market_data_categories.py:619`,
  `session_times.py:121`) PLUS the sports cross-AG-bleed accepted exception
  (`SPORTS_VENUE_ACCEPTED_CROSS_AG_BLEED=frozenset({"KALSHI"})`, `market_data_categories.py:933-937`, header comment
  already states it retires once the 20,785 rows are purged). **A rename/delete here must not touch the real
  prediction-venue KALSHI registration** — only the sports-axis phantom rows.
- deployment-api: `mtds_expected.py:53` / `prediction_catalogue.py:220` reference `KALSHI` — both confirmed **PREDICTION
  asset_group, not SPORTS** (different `venue_accessor`; sports uses the `"bookmaker"` sentinel). Flag for the
  delete-todo author to confirm this repo needs no change (KALSHI here is out of scope for a sports-only delete).

---

## 10. Delete 2,490 blank-venue rows (once P1's writer fix has stopped the source)

**Writer identified**: instruments-service `scripts/backfill_orphan_class_e_sports.py::record_cells()` (line 247) +
`resolve_source_and_mode()` (106-138). Confirmed via `scripts/restamp_sports_orphan_source_provenance_2026_08_03.py`
(one-off remediation script, lines 7-48): this script wrote `trades`=1,273 / `odds_horizon_bucket`=1,106 /
`trades_inplay`=111 rows with WRONG provenance due to a case-sensitivity gap in `resolve_source_and_mode()` (probed UAC
`SOURCE_PRIORITY` with the lowercase GCS path-segment value as-is, missed since UAC keys are uppercase-only, fell back
to `.upper()` retry — **fixed at `instruments-service@d9994199`**). Verify this fix is genuinely the root-cause fix P1
refers to before running the delete (the plan's own todo says "verify the writer is genuinely fixed before cleanup").

---

## 11. Delete `SPORT` instrument_type residue (8 rows on ODDS_API's `trades`)

**No producer found in ANY of the 7 repos searched.** Explicit `\bSPORT\b` token search (not `SPORTS`/`SPORT_*`) in
instruments-service found only prose/docstring hits (`betfair.py:141` — "eventTypeId (sport)" comment; a docstring in
`scripts/build_instrument_catalogue.py:743` describing the sports instrument-id SHAPE
`SPORT:BOOKMAKER:MARKET:LEAGUE:SEASON:HOME-AWAY::SELECTION` — i.e. `"SPORT"` as an id-NAMESPACE prefix segment, never an
`instrument_type` field value). UAC's only hit is inside `SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES`
(an accepted-exception set, `market_data_categories.py:1058`), not a live producer. **Most likely origin: a manual/
legacy backfill, or the MTDS ODDS_API `trades` writer under a code path not covered by this search** — the delete todo
can proceed (manifest-only, per the plan) but should re-grep MTDS's live `trades` writer for this exact string
immediately before deleting, since no repo here proves where it came from.

---

## 12. Sweep `league=` vs `league_id=` path duplication

**⚠️ CONTRADICTS THE PLAN'S OWN ASSUMPTION.** The P2 plan text says "Determine which is canonical (`league_id=` per the
path SSOT)" — but UAC's actual path-builder code says the opposite:

- UAC `canonical/domain/sports/gcs_paths.py` — path template docstring is
  `sports_reference/by_date/day={D}/entity={folder}/league={L}/{folder}.parquet` (line 14). The builder function's
  PARAMETER is named `league_id: str=""` (line 233), but every emitted path segment is literally
  `f"...league={league_id}/..."` (lines 351-352, 360, 365, 377, 380) — **the parameter named `league_id` writes into the
  path under the KEY `league`, never `league_id`.** `partition_paths.py:523,538-539` (the cross-repo entry point) also
  names its kwarg `league_id` but forwards unchanged into the same `league=` builder.
- MDPS: all production writer path-building (`canonical_writer.py:534,591,661`,
  `canonical_writer_streaming.py: 461-606`, `canonical_writer_stamping.py:508`) uses `league_id=` exclusively —
  `league=` appears only in legacy-path-recognition/compat code (`path_parsing.py:41`, `orchestration_scanner.py:533`,
  `scripts/pipeline_e2e_check.py:83`, `scripts/reprocess_sports_odds.py:110,138` — explicit comment "`league=` not
  `league_id=`"), never as a live write target. **No FOOTYSTATS-specific duplication logic found in MDPS** — MDPS only
  reads/parses, per the plan's own framing the duplicate write lives elsewhere (MTDS/instruments-service).
- MTDS: `scripts/migrate_sports_league_partition.py:59` (`if "league=" in name` — legacy-path detection, filename
  binding); `scripts/sports/league_id_relocation/migrate_instruments_store_sports_league_vocabulary_2026_08_04.py:282`
  (error message referencing unresolved `league=` values).

**Action for the sweep todo**: re-read `gcs_paths.py`'s actual emitted path string (not the parameter name) before
declaring either segment canonical — the plan's stated assumption (`league_id=` is canonical) is contradicted by the one
place that actually builds the path. Resolve this contradiction explicitly as the todo's first step, and correct the
plan text once resolved (this is exactly the "doc/pointer that misled you" HARD RULE — fix it in the same turn once
confirmed, per CLAUDE.md).

---

## Cross-cutting findings for every re-stamp/purge todo to carry forward

1. **The override-dict pattern in `enumerate_expected_universe.py` (§3b) is the load-bearing prior-incident lesson of
   this whole migration** — read it before touching any of the 19 tokens or `odds_horizon_bucket`.
2. **`odds_horizon_bucket` and `ODDS_API` are coupled in MTDS's freshness-preflight logic** (§5) — re-verify both
   frozensets together if both rename in the same pass.
3. **`league=` is the actual UAC-canonical path segment, not `league_id=`** (§12) — the plan's own text is wrong here;
   correct it once this is re-confirmed at run time.
4. **features-service has 3 independent copies and ml-service has 1 more independent copy** of the raw
   `venue=ODDS_API/data_type=odds` / `odds_horizon_bucket` path logic (§5, §6) — a migration that patches only the
   "obvious" `gcs_reader.py` misses `prediction_cross_venue_betfair.py` and `sports_feature_loader.py` entirely.
5. **A pre-existing bug**: ml-service's `cross_asset_training_pipeline.py::_infer_domain` venue set is missing
   `FOOTYSTATS` (§6) — fix in passing since that file needs touching for the venue re-attribution anyway.
6. **P3's ML loader-migration todo is durably parked** waiting on this P2 re-stamp — whoever lands the
   `odds_horizon_bucket` re-stamp must clear `auto_unpark__sports_taxonomy_p3_consumers-13983a72aba5` afterward (§5).
7. `strategy-service` was not searched (see "Repos NOT covered" above) — P3's plan names a live consumer there
   (`arbitrage_detector.py`). Low risk (it consumes via UAC's `arb_config.py`, not raw sports data_type tokens directly)
   but unverified by this pass.

## Codex SSOTs

- `/codex/02-data/entity-rename-and-split-consumer-migration-rule.md` — the rule this doc satisfies.
- `/codex/02-data/four-surface-reconciliation-procedure.md` — the post-migration verification this inventory feeds.
- `/codex/02-data/availability-manifest-and-data-status.md` — shard atom identity across writer/manifest/status/gate/UI.

## Progress Log

- **2026-08-12** — Produced via 7 parallel Explore-agent passes (MTDS, MDPS, instruments-service, UAC, features-service,
  ml-service, deployment-api), each checking all 5 binding types named by the codex rule. Surfaces the
  `enumerate_expected_universe.py` override-dict precedent as the load-bearing lesson, the `league=`/`league_id=`
  plan-text contradiction, and 4 independent copies of the same path-prefix logic across features-service/ml-service.
  `strategy-service` explicitly not covered — flagged as a stated blind spot, not silently omitted.
