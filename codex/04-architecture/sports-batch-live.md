---
doc_type: codex-ssot
title: Sports Batch/Live Architecture
summary:
  Per-asset-group batch/live architecture for asset_group=sports — odds_api is a live source today (REST-poll → GCS +
  Pub/Sub; see sports-live-odds-connectivity.md), every other sports source stays replay-capable batch-only, the
  (source,data_type,league_id,day) shard atom with fixture_id as a row column, L0Matcher/SportsMatchingEngine fills, and
  the fixture-dependent empty-reason taxonomy.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, instruments-service]
scope: [engineer, admin]
tags: [sports, batch-live, manifest, pipeline-mode, odds]
related:
  [
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/sports-integration-plan.md,
    /codex/04-architecture/sports-live-odds-connectivity.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: 2026-06-11
authoritative_for: [sports asset-group batch/live architecture, sports fixture-dependent empty-reason taxonomy]
referenced_by:
  [
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/prediction-batch-live.md,
    /codex/04-architecture/sports-integration-plan.md,
    /codex/04-architecture/sports-live-odds-connectivity.md,
    /codex/04-architecture/tradfi-batch-live.md,
  ]
owner:
last_reviewed: 2026-07-24
code_refs:
plan:
  plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md +
  pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md (R6-codex seam doc) +
  sports_consolidated_closeout_2026_07_19.md
---

# Sports Batch/Live Architecture

> Per-asset-group narrative for `asset_group=sports`. Cross-cutting batch=live invariant lives in
> [`batch-live-architecture.md`](batch-live-architecture.md) (whose §7 carries the SportsMatchingEngine bet-lifecycle
> notes); the source-aware `pipeline_mode` contract lives in
> [`/codex/02-data/pipeline-mode-partition.md`](/codex/02-data/pipeline-mode-partition.md) § "Ratified TARGET design".
> This doc covers the sports-specific shape: source list, the fixture-pinned data model, batch-SSOT continuity, matcher
> pattern, shard atomicity + the fixture-dependent empty-reason taxonomy.

> **⚠️ CORRECTION (2026-07-23) — §1 source table was stale, no banner previously existed.** Two facts below were drifted
> and are now fixed in place in §1: (1) **Fixtures entity is SPLIT** — `entity=fixtures_schedule` (schedule fields incl.
> `round`) + `entity=fixtures_outcomes` (scores/status), both under `pipeline_mode=batch_api_football/` (split
> 2026-05-23). Legacy bare `entity=fixtures/` is **FROZEN** (no real write since 2026-05-23) — never describe it as an
> active write target. (2) **Sports `data_type` is being reconciled to LOWER-case for ALL types** (operator decision
> 2026-07-23, reverting the 2026-07-18 UPPER K0-DECISION(b) and its since-shipped K1/K2 uppercase migration). The §1
> table is corrected to the lower-case target forms; the actual data/code revert has **not** executed yet — this is a
> documented decision only, not yet the on-disk/in-code reality. Most-current casing state:
> [`/codex/02-data/sports-data-types-catalog.md`](/codex/02-data/sports-data-types-catalog.md). SSOT for both:
> `plans/active/sports_consolidated_closeout_2026_07_19.md` (ENTITY-SPLIT / K-DECISIONS).

> **⚠️ CORRECTION (2026-07-24) — §1/§2/§6 wrongly claimed sports has no live source; `odds_api` IS live.** UAC
> `SOURCE_MODE_CAPABILITY["odds_api"]` flipped to `{BATCH, LIVE, REPLAY}` in `unified-api-contracts@249ca53f2`
> (2026-06-21) — the code comment there calls it "the FIRST live sports source" — but this doc's prior
> `last_reviewed: 2026-07-23` pass never touched the §1 capability row or the "no in-play live source" framing repeated
> in §1/§2/§6. Fixed in place below, scoped to `odds_api` only — every OTHER sports source (fixtures, reference,
> weather, xG, transfers, SFI) remains batch/replay-only with no live archetype. Live-path mechanics (poll cadence,
> Pub/Sub topic, MDPS producer) are the SSOT of [`sports-live-odds-connectivity.md`](sports-live-odds-connectivity.md),
> not duplicated here. Provenance: `plans/active/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md`.

---

## §1 Sports sources in scope

Sports is fixture-centric and multi-source. **`odds_api` is a live source today** — UAC `SOURCE_MODE_CAPABILITY`
declares `odds_api = {BATCH, LIVE, REPLAY}` (`_source_priority_data.py`, commit `249ca53f2`, 2026-06-21 — "the FIRST
live sports source"); live-path mechanics (REST-poll cadence, Pub/Sub topic, MDPS producer) are the SSOT of
[`sports-live-odds-connectivity.md`](sports-live-odds-connectivity.md), not duplicated here. Every OTHER sports source
is still a batch/REST archive or scheduled snapshot with no live archetype — but every source, `odds_api` included, is
**replay-capable** (historical endpoints + Secret-Manager keys already held), per UAC `SOURCE_MODE_CAPABILITY`:

| Source                     | Role (data_types)                                                                                                                                                                                                                                                                        | `SOURCE_MODE_CAPABILITY` (UAC)           |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `api_football`             | Primary fixture lifecycle: `fixtures_schedule`/`fixtures_outcomes` (split entity, 2026-05-23 — legacy bare `entity=fixtures/` FROZEN, never an active write target), fixture_lineups/events/stats/player_stats, injuries, results, standings, + reference (teams/players/venues/leagues) | `{BATCH, REPLAY}`                        |
| `footystats`               | matches, odds, predictions (+ deferred `fixtures_schedule`/`fixtures_outcomes` multi-source merge candidate)                                                                                                                                                                             | `{BATCH, REPLAY}`                        |
| `odds_api`                 | odds_snapshot, odds_movement, arbitrage (multi-bookmaker odds)                                                                                                                                                                                                                           | `{BATCH, LIVE, REPLAY}`                  |
| `understat`                | understat_xg / xg / xg_shots                                                                                                                                                                                                                                                             | `{BATCH, REPLAY}`                        |
| `soccer_football_info`     | sfi_progressive_stats                                                                                                                                                                                                                                                                    | `{BATCH, REPLAY}`                        |
| `transfermarkt`            | transfer_records, player_values                                                                                                                                                                                                                                                          | `{BATCH, REPLAY}`                        |
| `open_meteo`               | weather / weather_forecast (fixture-pinned)                                                                                                                                                                                                                                              | `{BATCH, REPLAY}`                        |
| `mdps_odds_horizon_bucket` | Computed odds_horizon_bucket (internal service source)                                                                                                                                                                                                                                   | `{BATCH, LIVE, REPLAY}` (service source) |

A `live_<source>` capability lands only when a sports in-play live archetype exists for THAT source — the capability
matrix is the gate, not an aspiration (closed-set rule: a `live_<source>`/`replay_<source>` PipelineMode member exists
iff `SOURCE_MODE_CAPABILITY` declares it). `odds_api` has already cleared this gate (`LIVE_ODDS_API` PipelineMode member
exists, `pipeline_mode.py`); the other 6 sports sources have not.

**Source of truth**: UAC `SOURCE_PRIORITY[("sports", <data_type>)]` (per-data_type source order) +
`SOURCE_MODE_CAPABILITY` (mode capability) + `registry/capability_declarations/` (per-source operations). Collection
rides the instruments-service sports write-paths (fixtures/reference/weather/SFI/footystats — fixture data is
reference-shaped) + the MTDS odds connectors; the computed odds-horizon buckets are MDPS output.

---

## §2 Batch/live symmetry — sports-specific shape

The core invariant from [`batch-live-architecture.md §1`](batch-live-architecture.md) applies: ONE sports pipeline,
mode-conditional logic only at the 4 seams. Sports-specific shape:

- **Fixtures/reference sources stay the "batch sole SSOT" shape (no live source); `odds_api`-sourced data does not.**
  Fixtures (api_football) and every other non-odds sports source have no live archetype — the `[batch-cutoff → now]`
  continuity tail resolves per shard to: autostart `replay_<source>` where the gap is re-fetchable (all sports sources
  are replay-capable), else wait-for-batch / a configured-OK-gap (per-shard DR config); the startup gate never demands a
  live feed that cannot exist (`could_exist(shard, mode)` guardrail, M2×M3). **`odds_api`-sourced data_types
  (`odds_snapshot`/`odds_movement`/`arbitrage`/`trades`) are the exception: `odds_api` is `{BATCH, LIVE, REPLAY}` today
  (§1)** — live-path mechanics are the SSOT of [`sports-live-odds-connectivity.md`](sports-live-odds-connectivity.md),
  not duplicated here. _(Flagged, not resolved by this pass:
  [`pipeline-mode-partition.md` § M6](/codex/02-data/pipeline-mode-partition.md) names "sports fixtures" as the M6
  case-3 "no replay AND no live" worked example, but this doc's own §1 table shows api_football as REPLAY-capable — a
  pre-existing case-1-vs-case-3 labeling question, orthogonal to this pass's `odds_api` fix, that needs its own review
  by whoever owns M6 case semantics — not resolved here.)_
- **Forward-looking fixtures are a CADENCE property, not a new pipeline_mode (M8).** The api-football 7-days-ahead
  fixtures snapshot is `batch_api_football` + cadence `scheduled_recurring` — sparse/forward-looking data never gets its
  own mode (that would fragment the reader's union).
- **Seasonality replaces the trading calendar.** Where TradFi gates staleness on `is_non_trading_day`, sports gates
  expected-coverage on the fixture calendar: no fixture scheduled ⇒ absence is the EXPECTED state (see §4 reasons).

| Seam            | Batch                                        | Live (`odds_api`-sourced data_types only — §1)                                    |
| --------------- | -------------------------------------------- | --------------------------------------------------------------------------------- |
| Data source     | REST archive snapshots → Parquet on GCS      | Odds API REST-poll + exchange poll → Pub/Sub (`sports-live-odds-connectivity.md`) |
| Feature compute | Load feature Parquet from GCS                | Embedded UTL `feature_calculator` in-process                                      |
| ML inference    | Load prediction Parquet from GCS             | Subscribe to prediction topic                                                     |
| Execution fills | `SportsMatchingEngine` (L0 top-of-book odds) | Real bookmaker bet placement                                                      |

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
[`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md)).

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
- **Gap, not yet closed-set (flagged 2026-07-24)**: no `EmptyConfirmedReason` member exists today for
  "`odds_horizon_bucket` window missed because the fixture kicked off early" —
  [`sports-data-types-catalog.md`](/codex/02-data/sports-data-types-catalog.md) previously cited a non-existent
  `EXPECTED_FIXTURE_STARTED_EARLY`; corrected there to flag the gap explicitly rather than claim the member exists.
  Needs an actual UAC enum addition (mint a new member, name TBD) before this case can honestly be `empty_confirmed` —
  open follow-up, not a shippable reason yet.
- Any other absence MUST be `record_failed(error=classify_venue_error(...))` — a 401/quota failure is `attempted_failed`
  (retryable), never honest absence.

**Shard identity propagation**: writer atomicity → manifest row key → data-status → preflight gate → deployment-UI
drilldown carry the identical atom. SSOT:
[`../../plans/epics/infrastructure_master.md`](../../plans/epics/infrastructure_master.md).

---

## §5 Source provenance + `pipeline_mode` — sports

- `pipeline_mode` is source-aware: `batch_api_football` / `batch_footystats` / `batch_odds_api` / `batch_understat` /
  `batch_soccer_football_info` / `batch_transfermarkt` / `batch_open_meteo` (+ computed
  `batch_mdps_odds_horizon_bucket`); `replay_<source>` members exist for every sports source per the capability matrix,
  and `live_odds_api` additionally exists for `odds_api` (§1 — the one sports source with a live archetype today). NEVER
  coarse `batch`, never an asset_group-glued value.
- `transport` is a COLUMN (`rest` for every sports source today), never glued into the source name (R4).
- Row-level `source` column + per-source manifest row are REQUIRED (`record_captured(source=...)`; `MissingSourceError`
  on blank). Sports is one of the crosscutting-provenance RED gaps — the historical `_index` source-stamp + the
  `pipeline_mode=` path partition ride the sports canonicalisation walk
  (`sports_manifest_canonicalisation_2026_06_01.md` single-walk rider), with the source lifted path→column.
- Multi-bookmaker odds: **CORRECTED 2026-08-15 — this line previously said "the bookmaker is data INSIDE the odds
  parquet, not a source"; that was stale/wrong.** Per `/codex/02-data/sports-data-types-catalog.md` (the more current,
  actively-maintained SSOT for this axis): the bookmaker IS the `venue` — `odds_api` is the `source` (vendor/ aggregator
  column), never a venue itself. `venue`=bookmaker (e.g. `WILLIAMHILL`, `FANDUEL`, `PINNACLE`) is real, live production
  shape (4.1M+ rows across 33 bookmaker venues, `source=odds_api`), not a data-layer implementation detail.

---

## §6 Live pipeline timing — sports

**`odds_api` live odds streaming is operating today** (§1) — REST-poll → GCS + Pub/Sub; SSOT for the live-path mechanics
(poll cadence, adapters, MDPS producer, Pub/Sub topic) is
[`sports-live-odds-connectivity.md`](sports-live-odds-connectivity.md), not duplicated here. Every OTHER sports source
still has no live stream. Timing rules that apply:

- Scheduled snapshot cadences (fixtures 7-days-ahead, daily results/stats sweeps) are deployment topology — cadence
  column + deployment-registry `run_class`, per M8.
- The MDPS odds-horizon-bucket computation consumes batch odds snapshots and emits at its own cadence with write-time
  `available_at` (never derived at read time — `LookaheadBiasError` discipline applies to odds movement exactly as to
  ticks).
- Live odds ride the standard MTDS → Redis → MDPS cascade with UTC-aligned boundaries
  ([`batch-live-architecture.md §10`](batch-live-architecture.md)); `odds_api` already carries `Mode.LIVE` in the
  capability matrix (closed-set rule cleared) — the M6 startup gate resolves `odds_api`-sourced shards to case 1/2
  automatically. A future non-odds sports source landing a live archetype would need to clear the same `Mode.LIVE` gate
  before this applies to it.

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
  [`/codex/02-data/pipeline-mode-partition.md`](/codex/02-data/pipeline-mode-partition.md) § "Ratified TARGET design"
- **Reconciliation column + precedence**:
  [`/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`](/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md)
- **Sibling per-AG docs**: [`cefi-batch-live.md`](cefi-batch-live.md) · [`tradfi-batch-live.md`](tradfi-batch-live.md) ·
  [`prediction-batch-live.md`](prediction-batch-live.md)
- **Shard-atom + empty-reason SSOT**:
  [`/codex/02-data/availability-manifest-and-data-status.md`](/codex/02-data/availability-manifest-and-data-status.md) +
  [`/codex/02-data/honest-absence-downstream-handling.md`](/codex/02-data/honest-absence-downstream-handling.md)
- **Mode-axis discipline**:
  [`/codex/06-coding-standards/mode-axis-discipline.md`](/codex/06-coding-standards/mode-axis-discipline.md)
- **Sports odds connectivity**: [`sports-live-odds-connectivity.md`](sports-live-odds-connectivity.md) +
  [`sports-integration-plan.md`](sports-integration-plan.md)
- **Sports canonicalisation walk**: `plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md`
- **Sports epic**: `plans/epics/sports_master.md`
