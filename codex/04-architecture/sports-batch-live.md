---
scope: [engineer, admin]
created: 2026-06-11
last_reviewed: 2026-06-11
plan:
  plans/active/sports_manifest_canonicalisation_2026_06_01.md +
  pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md (R6-codex seam doc)
---

# Sports Batch/Live Architecture

> Per-asset-group narrative for `asset_group=sports`. Cross-cutting batch=live invariant lives in
> [`batch-live-architecture.md`](batch-live-architecture.md) (whose §7 carries the SportsMatchingEngine bet-lifecycle
> notes); the source-aware `pipeline_mode` contract lives in
> [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md) § "Ratified TARGET design". This doc
> covers the sports-specific shape: source list, the fixture-pinned data model, batch-SSOT continuity, matcher pattern,
> shard atomicity + the fixture-dependent empty-reason taxonomy.

---

## §1 Sports sources in scope

Sports is fixture-centric, multi-source, and (today) has **no in-play live source** — every source is a batch/REST
archive or scheduled snapshot, and every source is **replay-capable** (historical endpoints + Secret-Manager keys
already held), per UAC `SOURCE_MODE_CAPABILITY`:

| Source                     | Role (data_types)                                                                                                                                        | `SOURCE_MODE_CAPABILITY` (UAC)           |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `api_football`             | Primary fixture lifecycle: FIXTURES, FIXTURE_LINEUPS/EVENTS/STATS/PLAYER_STATS, INJURIES, RESULTS, STANDINGS, + reference (TEAMS/PLAYERS/VENUES/LEAGUES) | `{BATCH, REPLAY}`                        |
| `footystats`               | MATCHES, ODDS, PREDICTIONS (+ deferred FIXTURES multi-source merge candidate)                                                                            | `{BATCH, REPLAY}`                        |
| `odds_api`                 | ODDS_SNAPSHOT, ODDS_MOVEMENT, ARBITRAGE (multi-bookmaker odds)                                                                                           | `{BATCH, REPLAY}`                        |
| `understat`                | UNDERSTAT_XG / XG / XG_SHOTS                                                                                                                             | `{BATCH, REPLAY}`                        |
| `soccer_football_info`     | SFI_PROGRESSIVE_STATS                                                                                                                                    | `{BATCH, REPLAY}`                        |
| `transfermarkt`            | TRANSFER_RECORDS, PLAYER_VALUES                                                                                                                          | `{BATCH, REPLAY}`                        |
| `open_meteo`               | WEATHER / WEATHER_FORECAST (fixture-pinned)                                                                                                              | `{BATCH, REPLAY}`                        |
| `mdps_odds_horizon_bucket` | Computed ODDS_HORIZON_BUCKET (internal service source)                                                                                                   | `{BATCH, LIVE, REPLAY}` (service source) |

A `live_<source>` capability lands only when a sports in-play live archetype exists — the capability matrix is the gate,
not an aspiration (closed-set rule: a `live_<source>`/`replay_<source>` PipelineMode member exists iff
`SOURCE_MODE_CAPABILITY` declares it).

**Source of truth**: UAC `SOURCE_PRIORITY[("sports", <data_type>)]` (per-data_type source order) +
`SOURCE_MODE_CAPABILITY` (mode capability) + `registry/capability_declarations/` (per-source operations). Collection
rides the instruments-service sports write-paths (fixtures/reference/weather/SFI/footystats — fixture data is
reference-shaped) + the MTDS odds connectors; the computed odds-horizon buckets are MDPS output.

---

## §2 Batch/live symmetry — sports-specific shape

The core invariant from [`batch-live-architecture.md §1`](batch-live-architecture.md) applies: ONE sports pipeline,
mode-conditional logic only at the 4 seams. Sports-specific shape:

- **Sports is the canonical "batch sole SSOT" asset group (M6 case 3).** With no live source, the `[batch-cutoff → now]`
  continuity tail resolves per shard to: autostart `replay_<source>` where the gap is re-fetchable (all sports sources
  are replay-capable), else wait-for-batch / a configured-OK-gap (per-shard DR config). Sports fixtures are the worked
  example of M6's "no replay AND no live" arm in the ratified contract — the startup gate never demands a live feed that
  cannot exist (`could_exist(shard, mode)` guardrail, M2×M3).
- **Forward-looking fixtures are a CADENCE property, not a new pipeline_mode (M8).** The api-football 7-days-ahead
  fixtures snapshot is `batch_api_football` + cadence `scheduled_recurring` — sparse/forward-looking data never gets its
  own mode (that would fragment the reader's union).
- **Seasonality replaces the trading calendar.** Where TradFi gates staleness on `is_non_trading_day`, sports gates
  expected-coverage on the fixture calendar: no fixture scheduled ⇒ absence is the EXPECTED state (see §4 reasons).

| Seam            | Batch                                        | Live (when an in-play archetype lands)         |
| --------------- | -------------------------------------------- | ---------------------------------------------- |
| Data source     | REST archive snapshots → Parquet on GCS      | In-play odds feed (capability-gated, none yet) |
| Feature compute | Load feature Parquet from GCS                | Embedded UTL `feature_calculator` in-process   |
| ML inference    | Load prediction Parquet from GCS             | Subscribe to prediction topic                  |
| Execution fills | `SportsMatchingEngine` (L0 top-of-book odds) | Real bookmaker bet placement                   |

---

## §3 Matching engine — L0Matcher + SportsMatchingEngine

Sports fills route through `execution-service/execution_service/matching_engine/sports_matching.py` — dispatch is on
`BatchExecutionMode`, never on asset_group:

- **`L0Matcher`** — top-of-book model over scraped bookmaker odds (`BENCHMARK` fills at exact odds; `SIMULATED` adds
  per-venue commission + a small odds spread for market impact).
- **`SportsMatchingEngine`** owns the full bet lifecycle: `place_bet(BetOrder)` → `CanonicalFill`
  (`instrument_id=fixture_id`, `price=odds`, `quantity=stake`), `settle`/`settle_fixture`/`settle_all`,
  `get_portfolio_summary()`. **Bets are positions** — open on placement, closed on settlement — so sports flows through
  the same position-tracking + PnL-attribution pipeline as every other asset group. Walk-forward capital carries over
  season→season through the engine's `PortfolioSummary`, never a side variable. Full lifecycle narrative:
  [`batch-live-architecture.md §7`](batch-live-architecture.md).

---

## §4 Shard atomicity — sports

Sports shard atom is **`(asset_group=sports, venue/source, data_type, league_id, day)`**. **`fixture_id` is a row-level
parquet column, NOT a shard axis** — `(league_id, day)` already bounds the per-day fixture set; promoting fixture_id
would 10× the manifest for zero failure-isolation gain (multi-axis correction, SSOT:
[`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md)).

**Path SSOT**: `unified_api_contracts.sports.candidate_parquet_paths()`
(`unified_api_contracts/canonical/domain/sports/gcs_paths.py`) — byte-exact batch=live, `pipeline_mode=`-aware at level
1 (`…/by_date/day={D}/pipeline_mode={mode}/…`) with legacy fallbacks. Never hand-build a sports path. Coverage clipping:
`clip_dates_to_source_coverage()` + `is_in_known_gap()` bound requests to each source's real archive window.

**Empty-record rules (closed set, UAC `EmptyConfirmedReason`)** — sports owns the fixture-dependent family:

- `EXPECTED_NO_FIXTURE` — no fixture scheduled for `(league_id, day)`; fixture-pinned sources (SFI, footystats
  MATCHES/ODDS/PREDICTIONS, open_meteo WEATHER) cannot emit without a fixture. The workhorse reason.
- `EXPECTED_PRE_SEASON` / `EXPECTED_POST_SEASON` — outside the league's season window.
- `EXPECTED_PAUSED_LEAGUE` — league suspended (winter break, force majeure).
- `EXPECTED_OUTSIDE_TRANSFER_WINDOW` — transfermarkt TRANSFER_RECORDS outside a transfer window.
- `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` — the source's league coverage excludes this league.
- `EXPECTED_NO_MAPPING` — canonical league/entity exists but the per-source provider mapping is absent (fetch not
  addressable; coverage-extendable, not permanently empty).
- `EXPECTED_PRE_SOURCE_COVERAGE_START` / `EXPECTED_PAST_SOURCE_COVERAGE_END` — per-source archive bounds.
- Any other absence MUST be `record_failed(error=classify_venue_error(...))` — a 401/quota failure is `attempted_failed`
  (retryable), never honest absence.

**Shard identity propagation**: writer atomicity → manifest row key → data-status → preflight gate → deployment-UI
drilldown carry the identical atom. SSOT:
[`../../plans/epics/infrastructure_master.md`](../../plans/epics/infrastructure_master.md).

---

## §5 Source provenance + `pipeline_mode` — sports

- `pipeline_mode` is source-aware: `batch_api_football` / `batch_footystats` / `batch_odds_api` / `batch_understat` /
  `batch_soccer_football_info` / `batch_transfermarkt` / `batch_open_meteo` (+ computed
  `batch_mdps_odds_horizon_bucket`); `replay_<source>` members exist for every sports source per the capability matrix.
  NEVER coarse `batch`, never an asset_group-glued value.
- `transport` is a COLUMN (`rest` for every sports source today), never glued into the source name (R4).
- Row-level `source` column + per-source manifest row are REQUIRED (`record_captured(source=...)`; `MissingSourceError`
  on blank). Sports is one of the crosscutting-provenance RED gaps — the historical `_index` source-stamp + the
  `pipeline_mode=` path partition ride the sports canonicalisation walk
  (`sports_manifest_canonicalisation_2026_06_01.md` single-walk rider), with the source lifted path→column.
- Multi-bookmaker odds: the bookmaker is data INSIDE the odds parquet, not a source — `odds_api` is the vendor.

---

## §6 Live pipeline timing — sports

There is no sports live stream today (capability matrix, §1). The timing rules that already apply:

- Scheduled snapshot cadences (fixtures 7-days-ahead, daily results/stats sweeps) are deployment topology — cadence
  column + deployment-registry `run_class`, per M8.
- The MDPS odds-horizon-bucket computation consumes batch odds snapshots and emits at its own cadence with write-time
  `available_at` (never derived at read time — `LookaheadBiasError` discipline applies to odds movement exactly as to
  ticks).
- When an in-play archetype lands, live odds ride the standard MTDS → Redis → MDPS cascade with UTC-aligned boundaries
  ([`batch-live-architecture.md §10`](batch-live-architecture.md)) and the source gains `Mode.LIVE` in the capability
  matrix FIRST (closed-set rule) — the M6 startup gate then resolves sports shards to case 1/2 automatically.

---

## §7 Anti-patterns

- Don't build a sports-only backtest engine — route through execution-service `SportsMatchingEngine`
  (`batch-live-architecture.md §8` anti-pattern 4: inline `returned = stake * odds` settlement is the canonical
  violation).
- Don't stamp coarse `pipeline_mode=batch` (or `sports_batch`) — sports is source-aware (`batch_api_football` / …);
  readers prefix-match `batch_*`/`live_*`/`replay_*`, never an exact coarse literal.
- Don't invent a `pipeline_mode` for forward-looking fixtures — sparse/scheduled/7-days-ahead is CADENCE
  (`scheduled_recurring`), a manifest column, never a mode or a path key (M8).
- Don't make `fixture_id` a shard axis — it is a row-level column; per-fixture drilldown reads the parquet.
- Don't hand-build sports GCS paths — `candidate_parquet_paths()` is the path SSOT (byte-exact batch=live).
- Don't record a no-fixture day as `attempted_failed` (it is `EXPECTED_NO_FIXTURE`) — and don't record a 401/quota error
  as `record_empty` (it is `attempted_failed`, retryable).
- Don't glue a transport into the source name (`odds_api_rest` etc.) — `transport` is a separate manifest COLUMN.

---

## §8 Cross-references

- **Batch/live invariant (global) + SportsMatchingEngine narrative**:
  [`batch-live-architecture.md`](batch-live-architecture.md) §1–§4, §7
- **Source-aware pipeline_mode + M1–M8 target**:
  [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md) § "Ratified TARGET design"
- **Reconciliation column + precedence**:
  [`../02-data/pipeline-mode-and-batch-live-reconciliation.md`](../02-data/pipeline-mode-and-batch-live-reconciliation.md)
- **Sibling per-AG docs**: [`cefi-batch-live.md`](cefi-batch-live.md) · [`tradfi-batch-live.md`](tradfi-batch-live.md) ·
  [`prediction-batch-live.md`](prediction-batch-live.md)
- **Shard-atom + empty-reason SSOT**:
  [`../02-data/availability-manifest-and-data-status.md`](../02-data/availability-manifest-and-data-status.md) +
  [`../02-data/honest-absence-downstream-handling.md`](../02-data/honest-absence-downstream-handling.md)
- **Mode-axis discipline**:
  [`../06-coding-standards/mode-axis-discipline.md`](../06-coding-standards/mode-axis-discipline.md)
- **Sports odds connectivity**: [`sports-live-odds-connectivity.md`](sports-live-odds-connectivity.md) +
  [`sports-integration-plan.md`](sports-integration-plan.md)
- **Sports canonicalisation walk**: `plans/active/sports_manifest_canonicalisation_2026_06_01.md`
- **Sports epic**: `plans/epics/sports_master.md`
