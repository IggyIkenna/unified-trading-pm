---
doc_type: codex-ssot
title: Sports Scheduling & Sharding
summary:
  Sports scheduling + sharding SSOT — shard atom (asset_group,source,data_type,league_id,day) with fixture_id row-level,
  per-provider fetch cadence + publish windows, historical-backfill lookahead-bias rules, and per-fixture
  denormalisation.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, execution-service, features-service, instruments-service]
scope: [engineer]
tags: [sports, manifest, backfill, data-correctness, mtds, orchestrator]
related:
  [
    /codex/02-data/sports-data-source-coverage-matrix.md,
    /codex/02-data/sports-adapter-dependency-order.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
  ]
created: 2026-04-21
authoritative_for:
  [sports fetch scheduling cadence and shard-atom contract, sports historical-backfill lookahead-bias rules]
referenced_by:
  [
    /codex/02-data/sports-adapter-dependency-order.md,
    /codex/02-data/sports-data-source-coverage-matrix.md,
    /codex/02-data/sports-data-types-catalog.md,
    /codex/02-data/sports-fixtures-lifecycle.md,
    /codex/02-data/sports-gcs-path-ssot.md,
  ]
owner:
last_reviewed: 2026-09-15
code_refs:
last_updated: 2026-04-21
---

# Sports Scheduling & Sharding

> **⚠️ CORRECTION (2026-07-19; §9 body fixed 2026-07-23).** §9's diagram + schema note now show the current split layout
> (`entity=fixtures_schedule`/`entity=fixtures_outcomes` under `pipeline_mode=batch_api_football/`, bare
> `entity=fixtures/fixtures.parquet` marked FROZEN/historical-only) — see §9, no further action needed there. §12's
> "Roadmap — open plans (as of 2026-04-21)" is still a stale historical snapshot (13 plans, all shipped/archived); live
> open sports work is tracked in `plans/active/sports_consolidated_closeout_2026_07_19.md`, not §12.

<!-- MULTI_AXIS_CORRECTION_2026_05_06 -->

> **Multi-axis correction (2026-05-06)** — shard atoms vs display axes (row-level columns) per asset_group are the SSOT
> in
> [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md#multi-axis-correction-banner-canonical).
> See that doc for the full per-asset-group shard-atom matrix (sports / prediction / cefi options-futures / DeFi chain /
> ML+strategy+execution job_id / TradFi EVENT_CONTRACT).

SSOT for **when** each sports data source is fetched, **how far ahead / behind**, **when the underlying data is actually
published** (lookahead-bias discipline for historical backfill — `available_at` per row stamped per UAC
`AVAILABILITY_AT_SEMANTICS`), and **how shards are keyed** in the availability manifest. Consolidates the trigger-tier
scheduler (`deployment-service/configs/sports-trigger-tiers.yaml`) with adapter implementation details and the
per-(league, day) sharding contract (with `fixture_id` as a row-level column).

**Related**: [availability-manifest-and-data-status.md](./availability-manifest-and-data-status.md),
[04-architecture/shard-level-failure-isolation.md](/codex/04-architecture/shard-level-failure-isolation.md),
[05-infrastructure/deployment-clusters-live-vs-batch.md](/codex/05-infrastructure/deployment-clusters-live-vs-batch.md),
[06-coding-standards/validation-and-errors.md](/codex/06-coding-standards/validation-and-errors.md).

## 1. Anchoring principle — fixture_id is the per-row anchor; (league_id, day) is the shard atom

Every piece of sports data — schedules, stats, odds, standings, weather, player values — maps back to a **fixture**.
`(league_id, kickoff_date)` is derivable from `fixture_id`, not the other way round.

**Shard atom** (banner-canonical per
[`availability-manifest-and-data-status.md § Multi-axis correction banner`](./availability-manifest-and-data-status.md#multi-axis-correction-banner-canonical)):
`(asset_group=sports, source, data_type, league_id, day)` for **all** sports data_types — fixture-native AND
day-aggregate. **`fixture_id` is a row-level column inside the parquet, NOT a hive-partition shard axis** —
`(league_id, day)` already bounds the per-day fixture set; per-fixture detail at drill-down comes from reading the
parquet, not from a separate manifest row. Avoids ~10× manifest inflation. Fixture-native data_types: `ODDS_SNAPSHOT`,
`ODDS_MOVEMENT`, `ARBITRAGE`, `FIXTURE_STATS`, `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`, `PLAYER_STATS`, `INJURIES` (when
fixture-scoped). Day-aggregate data_types: `STANDINGS`, `LEAGUES`, `TEAMS`, `REFEREES`, `COACHES`, `ROUNDS`.

**Cluster validation MANDATORY for fixture-native per-day bundles** (writegate Phase 1A + 2.B): per-fixture aggregate
clusters live INSIDE the per-(league, day) parquet — `cluster_extractor=lambda row: row["fixture_id"]` (or `bookmaker`
for ODDS\_\*) + `SPORTS_FIXTURE_CLUSTERS` per league-tier (UAC seeds tier-1 EU football, greenfield for the broader
matrix). UTL guard `MissingClusterValidationError` if absent; QG STEP 5.64 statically checks. See the
[cluster-validation rule](./availability-manifest-and-data-status.md#multi-axis-correction-banner-canonical).

**Consequence:** the availability manifest's primary per-shard key for sports is `(league_id, day)`. For venue-native or
player-native data (weather, Transfermarkt values, league standings), we still write shard-native rows in their own
storage layout, but **features-service (sports family) denormalises them onto each fixture** at feature-compute time so
every fixture has a complete as-of snapshot without lookahead leakage.

`(date, league_id)` is BOTH the **query-time index** + **backfill horizon** + **shard atom** — it's what the daily cron
iterates, what the UI data-status drilldown renders, and what the manifest indexes. Per-fixture detail surfaces by
reading the parquet rows.

## 2. Provider-by-provider scheduling matrix

For each provider, four dimensions:

- **Fetches**: canonical data_types produced.
- **Cadence**: when we fire in production.
- **Published**: when the upstream source actually has the data (lookahead discipline — never timestamp a backfill row
  at a moment the data didn't exist in the wild).
- **Shard key**: natural key for the rows; the denormalisation hop (if any) onto `fixture_id`.

### 2.1 API-Football (`api_football.py`, `api_football_reference.py`)

- **Fetches:** `FIXTURES` (schedule), `LEAGUES`, `TEAMS`, `STANDINGS`, `INJURIES`, `FIXTURE_EVENTS`, `FIXTURE_LINEUPS`,
  `FIXTURE_STATS`, `PLAYER_STATS`.
- **Cadence:**
  - `FIXTURES` — rolling forward-poll `[today, today+7]` every 6h, plus Tier-1 discovery refresh of full season calendar
    every 24h.
  - `STANDINGS`, `INJURIES`, `TEAMS`, `LEAGUES` — Tier-2 daily.
  - `FIXTURE_LINEUPS` — Tier-3 T-1h pre-kickoff (line-ups are typically confirmed 60-90m before kickoff).
  - `FIXTURE_STATS`, `FIXTURE_EVENTS`, `PLAYER_STATS` — Tier-4 T+30m post-final-whistle.
- **Published:**
  - Schedule: days to months ahead for league play, short notice (hours/days) for cup draws, playoffs, postponements.
  - Line-ups: ~60-90m before kickoff.
  - Stats: basic counts immediate at full time; advanced (expected goals from API-Football's model, detailed per-player
    metrics) within 30-60m.
- **Shard key:** `fixture_id` for fixture-scoped entities; `(date, league_id)` for `STANDINGS` / `INJURIES`; `league_id`
  for `LEAGUES`; `team_id` for `TEAMS`.

### 2.2 Transfermarkt (`transfermarkt.py`)

- **Fetches:** `PLAYER_VALUES`, `TRANSFERS`, `TEAM_SQUAD`, `PLAYER_HISTORY`, `TRANSFERMARKT_LEAGUES`.
- **Cadence:** Tier-2 daily, **window-aware**: `TRANSFERS` only fires when the transfer-window-open flag is true for the
  league's country. Outside windows, `TRANSFERS` fires **weekly** to catch late registrations and free-agent signings
  that can happen outside windows.
- **Published:** Player valuations are revised by Transfermarkt editors on roughly a weekly cadence during playing
  seasons and monthly in off-season. Transfers register when the deal is officially paperwork-complete — days after
  press announcement.
- **Shard key:** `(player_id, as_of_date)` for values; `(transfer_id)` for transfers; `(team_id, season)` for squads.
  Not fixture-native.
- **Denormalisation to fixture:** features-service (sports family) materialises
  `fixture_id → [{player_id, value_eur_as_of_kickoff}]` by joining `FIXTURE_LINEUPS` (who played) × `PLAYER_VALUES` (≤
  kickoff). The player value is the most-recent snapshot with `as_of_date <= kickoff_date`. **Duplicating the value onto
  every fixture is correct** — it preserves the as-of invariant and keeps the features table flat.
- **Team-mapping cache** (shipped 2026-04-22, `transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22`):
  per-season roster parquet at `sports_reference/mappings/transfermarkt_league_teams/season={YYYY}/teams.parquet`.
  Columns: `league_id, canonical_league, team_id, name, squad_size, player_count, last_fetched_at`. 7-day staleness
  window; on a cache-hit non-trigger date (`get_leagues_needing_refresh(date) == []`) the adapter short-circuits the
  per-league API loop, populates `_captured_league_counts` from the cache, and emits `UPSTREAM_FETCH_COMPLETED` with
  `details.cached=True`. The cache is rewritten on every live-fetch branch, keeping `last_fetched_at` fresh. Reader:
  [`features-service (sports family)/features_sports_service/data/gcs_reader.py::read_transfermarkt_team_mapping(season: int)`](../../../features-service
  (sports family)/features_sports_service/data/gcs_reader.py).

### 2.3 FootyStats (`footystats.py`)

- **Fetches:** `FIXTURES` (FootyStats-branded IDs), `MATCH_STATS`, `ODDS_SNAPSHOTS`, `PREDICTIONS`,
  `PLAYER_PERFORMANCE`.
- **Cadence:**
  - `PREDICTIONS` — Tier-3 T-24h (model output is static pre-match).
  - `ODDS_SNAPSHOTS` — Tier-3 T-24h, T-6h, T-1h (closing). **Pre-match only.** Live in-play odds are emitted separately
    via market-tick-data-service at the venue's live cadence (see §3).
  - `MATCH_STATS`, `PLAYER_PERFORMANCE` — Tier-4 T+24h (FootyStats finalises xG / advanced stats with a 6-24h delay).
- **Published:** Odds are snapshots of a real live market, so they're "published" continuously. Our snapshot captures
  the value at fetch time. Match stats finalise at T+6-24h (mostly same-day post-match).
- **Shard key:** `fixture_id` across all data types.

### 2.4 SoccerFootballInfo / SFI (`soccerfootball_info.py`)

- **Fetches:** `SFI_LEAGUES`, `SFI_PROGRESSIVE_STATS` (streaks, sequences). **Not `SFI_STANDINGS`** — SFI has no
  standings endpoint. This was confirmed against the archived service and is enforced by
  [`instruments-service/instruments_service/engine/orchestrator.py`](../../instruments-service/instruments_service/engine/orchestrator.py)
  L4365-4367 (`_want_sfi_standings = False`). Pre-match league position / points come from the API-Football `STANDINGS`
  endpoint (see §2.1); `features-service (sports family)` reads that pre-match partition via
  `data/gcs_reader.py::read_pre_match_standings` (`day=kickoff_date - 1` with 7-day fallback).
- **Cadence:** Tier-1 every 6h for `SFI_LEAGUES`; Tier-4 T+24h for `SFI_PROGRESSIVE_STATS` (needs completed-matchday
  state).
- **Published:** Progressive stats recomputed daily; league metadata refreshed on season boundaries.
- **Shard key:** `(league_id, season)` for both entities. Not fixture-native.
- **Backfill launchers:**
  - `deployment-service/scripts/vm/launch-sfi-forward-poll.sh` — T-1 forward-poll (default cadence).
  - `deployment-service/scripts/vm/launch-sfi-backfill-vm.sh` — multi-year historical range (2020-2026 etc.);
    singleton-locked against ALL `sfi-*` VMs (shared `soccer-football-info-api-key`; reference: 2026-04-19
    thundering-herd incident).
- **League-mapping cache** (shipped 2026-04-22, `transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22`):
  flat parquet at `sports_reference/mappings/sfi_league_mapping.parquet` (not season-scoped — SFI hex league IDs are
  long-lived). Columns: `canonical_league_id, sfi_league_hex, name, last_fetched_at`. 24h staleness window. Cache-hit on
  non-trigger dates skips the paid `get_leagues` call and feeds `sfi_league_ids` directly from the cache;
  progressive-stats per-match fetches still run because they're date-scoped. Reader:
  [`features-service (sports family)/features_sports_service/data/gcs_reader.py::read_sfi_league_mapping()`](../../../features-service
  (sports family)/features_sports_service/data/gcs_reader.py).

### 2.5 OpenMeteo / Weather (`open_meteo.py`)

- **Fetches:** `WEATHER` (temperature, precipitation, wind, humidity, cloud cover, weather_code) per (latitude,
  longitude, hour).
- **Cadence:**
  - **Forecast** (dates > today): Tier-1 discovery 6h + Tier-3 T-24h + T-1h (nowcast just before kickoff).
  - **Observed** (dates ≤ today): single fetch at T+1h post-kickoff from the ERA5 archive endpoint.
- **Published:** OpenMeteo refreshes forecast every hour; ERA5 archive finalised several days post-date.
- **Shard key:** `(venue_lat, venue_lon, date)` — one weather fetch per venue per day covers all fixtures at that venue.
- **Denormalisation to fixture:** features-service (sports family) joins `(venue_id → lat/lon)` ×
  `(lat/lon, date) → hourly weather` and picks the hourly bucket containing `kickoff_utc`. Duplicated onto every fixture
  at that venue on that day.

### 2.6 Understat (`understat.py`)

- **Fetches:** `XG` (expected goals per shot + per fixture aggregates), `SHOTS`, `ADVANCED_STATS`. Six leagues only
  (EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1, RFPL).
- **Cadence:** Tier-4 T+24h. Understat requires `(league, season)` as the fetch key, not date — we fetch the whole
  season and filter in-memory. Rolling-forward the season fetch once per day is cheap (single HTTP call per league per
  day).
- **Published:** xG computed 4-24h post-match; shot data ~6h post-match. Understat never retroactively revises past
  matches.
- **Shard key:** `fixture_id` once parsed; fetch granularity is `(league_id, season)` so the adapter reads the
  season-wide JSON and explodes into per-fixture rows.

### 2.7 Data-quality drift detection (shipped 2026-04-22)

Plan:
[`transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22`](../../plans/archive/transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22.plan.md).

Honest-coverage tells us _whether_ a shard wrote — it does not tell us whether the number of rows is sane. A successful
fetch that silently returns 17 teams for EPL (expected 20) lands in the manifest as `captured` and looks identical to a
legit 20-row fetch. The two gaps closed by this plan:

- **Per-league team-count** (Transfermarkt): UAC
  [`get_expected_team_count_for_league(league_id: str, season: int) -> int | None`](../../../unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py)
  is the canonical denominator. Values are seeded in `LEAGUE_EXPECTED_TEAM_COUNTS` (EPL=20, LaLiga=20, Bundesliga=18,
  MLS expansion tracked year-by-year, …). `None` means "no seed → silent skip, never emit". The TM adapter's per-league
  loop calls the shared helper `orchestrator._maybe_emit_drift_anomaly(...)` with a 10% warn / 25% HIGH threshold.
- **Expected-league denominator** (SFI): after `adapter.get_leagues()` the SFI fetch counts how many returned leagues
  map into `SOCCER_FOOTBALL_INFO_IDS` and compares the count against
  `get_expected_leagues_for_source("soccer_football_info", classifications=["Prediction"])`. Wider 15% warn / 30% HIGH
  threshold because SFI routinely drops and re-adds fringe leagues day-to-day.

Both paths call `log_event("ADAPTER_FETCH_ANOMALY", details={…})` — never raise. Details shape:
`{venue, endpoint, league_id, date, season?, expected_count, got_count, deviation_pct, severity}`. The manifest write
still proceeds so shard-level failure isolation is preserved.

Event registration:
[`unified-trading-library/unified_trading_library/events/event_types.py`](../../../unified-trading-library/unified_trading_library/events/event_types.py)
(`ADAPTER_FETCH_ANOMALY`, `ADAPTER_FETCH_FAILED`, `ADAPTER_FETCH_EVENT_TYPES`).

## 3. Match-state-driven odds polling

Odds polling cadence is not daily — it is **match-state-driven**:

| Match state              | Cadence                                        | Producer                                                                |
| ------------------------ | ---------------------------------------------- | ----------------------------------------------------------------------- |
| Pre-match (> T-24h)      | Daily refresh                                  | market-tick-data-service                                                |
| Pre-match (T-24h → T-1h) | Hourly + trigger snapshots T-24h / T-6h / T-1h | market-tick-data-service (Tier-3 triggers in sports-trigger-tiers.yaml) |
| Kickoff ±0h → full time  | 5-30s per venue (WS or REST poll)              | market-tick-data-service live loop                                      |
| T+0 → T+15m              | Final settlement capture                       | market-tick-data-service                                                |
| T+1h onwards             | No further polling                             | —                                                                       |

The producer (market-tick-data-service sports adapter) reads `kickoff_utc`

- `status` from the fixture manifest and routes polling by state. `status` transitions come from the fixtures endpoint
  itself (`NS` → `1H` → `HT` → `2H` → `ET` → `P` → `FT` → `AET` / `PEN`).

## 4. Rolling forward-poll semantics

The daily `FIXTURES` cron fires at 06:00 UTC for the window:

```
[today - 1 day, today + 7 days]
```

- **Lookback 1 day** absorbs late API-Football schedule corrections (common for lower-tier leagues).
- **Lookahead 7 days** captures new fixture announcements (cup draws, TV reschedules, postponement replays, playoff
  brackets). API-Football's confirmed window is reliably 7 days — beyond that, schedule shifts and TBD matches mean we'd
  freeze invalid data into the manifest.
- **Overwrite is mandatory**: the adapter MUST re-fetch + overwrite existing parquets in this window. Skip-if-exists is
  disabled for rolling-poll dates via `--force-window` (see §7).

For dates outside the rolling window, the orchestrator's existing freshness check applies (0h freshness for dates older
than 7 days → immutable; 24h freshness for dates within the last 7 days).

## 5. Lookahead-bias rules for historical backfill

When backfilling historical dates (e.g. 2018-01-01..2019-01-15), the adapter MUST timestamp each row **as-of the
historical date**, not the fetch date. Specifically:

- `as_of_date` column on denormalised rows (Transfermarkt values, SFI standings) = the historical fixture date being
  backfilled, NOT `datetime.now()`.
- Transfer values: use Transfermarkt's historical value endpoint where available; otherwise record
  `value_eur_as_of=None, provenance="no historical data"` — never backfill today's value onto a 2018 fixture.
- Weather: use the ERA5 archive endpoint for dates in the past, not the current forecast.
- Odds: historical odds snapshots come from cassette-replay of past runs, not re-fetch. Once a snapshot is missed, it's
  missed — writing today's odds onto a 2018 fixture is a data crime.
- Stats / xG: retroactive fetches are legit because stats don't change.

The shard row's `attempted_at` column captures when the adapter actually ran (metadata). The payload columns must
reflect the state as-of the fixture date.

### 5.1 Enforcement — Timestamp-Alignment-Gate

Every raw-data `sink.write(...)` in `instruments-service` with a `day={D}` partition runs through `InstrumentsWriteGate`
from `unified_trading_library.instruments_write_gate`. The gate scans the `DEFAULT_AS_OF_COLUMNS` families
(`as_of_date`, `valuation_date`, `available_at`, `kickoff_utc`, `event_time`, `computed_at`) and emits
`DATA_ALIGNMENT_VIOLATION` (warn mode) or raises `TimestampAlignmentError` (strict mode) if any non-null value satisfies
`value.date() > D`. See
[`06-coding-standards/validation-and-errors.md` §5 InstrumentsWriteGate](/codex/06-coding-standards/validation-and-errors.md#5-instrumentswritegate-raw-data-sink-writes)
for the full contract + usage.

Pre-2026-04-22 the raw-data layer relied on adapter discipline alone — the Transfermarkt VM data-crime incident (18h
writing wall-clock-2026 `valuation_date` onto `day=2023-03-16`) is the reason the gate now exists.

## 6. Manifest dumps: empty-confirmed for full-manifest coverage

Every (expected_date, expected_league) pair that the adapter attempted — whether the API returned rows or not — MUST
produce a manifest row:

| API outcome                        | `capture_status`   | `instrument_count` |
| ---------------------------------- | ------------------ | ------------------ |
| Rows returned                      | `captured`         | `n > 0`            |
| Empty response (legitimately zero) | `empty_confirmed`  | `0`                |
| HTTP error / timeout / rate-limit  | `attempted_failed` | `0`                |

**No row at all** means the adapter never attempted (e.g. date before the service was deployed). The UI renders these as
"unknown" distinct from "empty".

This is the contract already in manifest v5. The **rescan script** (`rescan_sports_fixtures_canonical.py`) closes the
gap retroactively by emitting `empty_confirmed` for every in-season league whose parquet exists but has zero rows.

## 7. Trigger-window invalidation (transfers, seasons)

Two classes of events invalidate slow-changing reference data beyond the default daily Tier-2 cadence:

### 7.1 Transfer windows

When a transfer window opens (summer / winter by country), the Tier-2 `TRANSFERS` trigger switches from weekly to daily.
Windows are declared in UAC `sports.transfer_windows[league_id]` as `(open_date, close_date)` per season. The scheduler
checks `is_transfer_window_open(league_id, today)` and flips the frequency.

Player rosters (TEAM_SQUAD) also invalidate on window close day — signings finalised in the last 24h should flush the
cache.

### 7.2 Season boundary

End-of-season fires a one-off refresh of `LEAGUES` + `TEAMS` + `STANDINGS` to pick up promotion/relegation + new team
registrations. Start-of-season fires a full schedule pre-fetch (Tier-1 extended window to 30 days since fixtures are
pre-announced by leagues months ahead of matchday).

Season boundaries per league live in UAC `sports.season_calendar[league_id] = [{start, end, season_year}, ...]`.

## 8. Cloud Run vs VM — deployment economics

Two deployment shapes for sports-reference jobs:

| Shape                                 | Cold start                                  | Cost floor                             | Right for                                                                                                                  |
| ------------------------------------- | ------------------------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| **Cloud Run** (request-triggered job) | ~1-3s warm / ~15-30s cold (full image pull) | $0 when idle, per-second while running | Tier-1 + Tier-2 + Tier-3 trigger jobs (short + intermittent, sub-minute runtime). Saves money vs a long-lived VM.          |
| **GCE VM** (tarball boot)             | 3-5 min (image + venv + tarballs)           | Runs for the full backfill window      | Historical backfills (hours of runtime), migrations, smoke tests. Tarball refresh faster than image rebuild for iteration. |

**Default for sports reference data:** Cloud Run job. Tier-1 through Tier-3 triggers average < 60s of work each — a warm
Cloud Run instance is 10-100× cheaper than keeping an `e2-small` VM alive for a 6h window.

**Exception:** the daily historical refresh (when re-fetching a multi-day window) and one-off backfills stay on VMs —
Cloud Run has a 60-minute max-per-request cap and VMs win on long-running batch.

**VMs running longer than ~60s** use the shared wrapper's heartbeat daemon, streaming GCS log, `/api/vm-deployments`
registry, and self-delete on completion — see
[`vm-tarball-deployment.md` § Observability & Lifecycle](/codex/05-infrastructure/vm-tarball-deployment.md#observability--lifecycle)
(provenance: `deployment-service` `cc07649`, `beaa2e5`).

See [`/codex/05-infrastructure/vm-tarball-deployment.md`](/codex/05-infrastructure/vm-tarball-deployment.md) for the VM
shape; see
[`/codex/05-infrastructure/runtime-tiers-and-deployment.md`](/codex/05-infrastructure/runtime-tiers-and-deployment.md)
for Cloud Run job wiring.

**VM-daemon pattern for live schedulers** — Long-lived scheduling processes (polling loops, cron-alternatives) can run
as GCE daemons via the `launch-*-vm.sh` + `setup-data-pipeline-vm.sh` + `VM_TASK=*-poll` pathway. Zero Cloud-Run-image
dependency — the VM boots off the existing tarball deployment infra (UAC / UTL / service tarballs on GCS) and the
launcher omits `VM_SHUTDOWN_ON_COMPLETION=true` so the VM stays up. Uses the shared singleton-lock pattern
(same-prefix-running refusal with `--force` bypass) to prevent double-dispatch. First adopted by sports-scheduler
2026-04-22 (`launch-sports-scheduler-vm.sh` + `SPORTS_SCHEDULER_poll` branch in `setup-data-pipeline-vm.sh`) as a
workaround for Plan 12 + Plan 13 Cloud Build blockers; pattern is reusable for any service whose shipped CLI already
contains an internal polling loop (e.g. features-sports live forward-poll, execution-service live signal broadcast
watchdog).

## 9. Per-fixture denormalisation pattern

Fixture-native providers (API-Football fixture-scope entities, FootyStats, Understat) write directly to per-fixture
parquets. Non-fixture providers (Transfermarkt, SFI standings, OpenMeteo weather) write to their natural shard and are
denormalised onto fixtures by features-service (sports family):

```
Raw shards                                       Denormalised per-fixture table
-----------                                      ------------------------------
sports_reference/by_date/day={D}/
  pipeline_mode=batch_api_football/
    entity=fixtures_schedule/      ─┐            af_fixture_id
       fixtures_schedule.parquet    │            ├─ timestamp, af_league_id, af_home_id/name, af_away_id/name
                                     │            ├─ round (from fixtures_schedule)
    entity=fixtures_outcomes/       │            ├─ score / status (from fixtures_outcomes)
       fixtures_outcomes.parquet   ─┤            ├─ home_standing_position_pre (from SFI)
                                     │            ├─ away_standing_position_pre (from SFI)
  by_date/day={D}/entity=           ├── join ───►├─ home_team_value_as_of (from Transfermarkt)
    standings/standings.parquet    ─┤            ├─ away_team_value_as_of (from Transfermarkt)
                                     │            ├─ kickoff_weather (from OpenMeteo)
  player_values/                    │            └─ ... (xG, odds snapshots, etc.)
    player={P}/values.parquet      ─┤
                                     │
  weather/                          │
    venue={V}/day={D}/              │
    weather.parquet                ─┘

FROZEN — historical-only, never write/read for current data:
  sports_reference/by_date/day={D}/entity=fixtures/fixtures.parquet
  (bare entity, no pipeline_mode= segment; last real write 2026-05-23)
```

> **Schema note (2026-07-23, supersedes the 2026-04-28 note it replaces)**: the live write targets are
> `pipeline_mode=batch_api_football/entity=fixtures_schedule/fixtures_schedule.parquet` (schedule fields —
> `af_fixture_id`, `af_league_id`, `af_home_id`, `af_home_name`, `af_away_id`, `af_away_name`, `timestamp`, `date`,
> `round`, …) and the sibling `entity=fixtures_outcomes/fixtures_outcomes.parquet` (score/status fields —
> `af_winner_id`, score breakdowns, fixture `status`, …). Match-stats (xG, possession, corners, …) still live in the
> separate `entity=fixture_stats/fixture_stats.parquet` partition. The manifest `data_type` for this entity must record
> `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES`, not a `FIXTURES` umbrella. **The bare `entity=fixtures/fixtures.parquet` path
> (no `pipeline_mode=` segment) is FROZEN as of 2026-05-23 (last real write) — it is historical-only.** Do not write to
> it, and do not read it as a live source; any reader/writer still touching it live is a bug against this contract, not
> a supported fallback (see
> [`plans/active/sports_consolidated_closeout_2026_07_19.md`](../../plans/active/sports_consolidated_closeout_2026_07_19.md),
> which as of 2026-07-23 found live artifacts still violating this freeze — that reconciliation, not this doc, is the
> place to track those). The earlier pre-2024 nested-struct schema (`league = {…}`, `home_team = {…}`, `kickoff_utc`,
> inline match-stats) was retired before the entity split, by the
> [sports_fixtures_legacy_schema_migration_2026_04_28](../../plans/ai/sports_fixtures_legacy_schema_migration_2026_04_28.plan.md)
> migration; those archived legacy parquets are at
> `gs://instruments-store-sports-prd-{pid}/sports_reference_v1_archive/`.

The denormalisation happens at feature-compute time (features-service (sports family)), not at ingestion. The raw shards
stay normalised (single source of truth per data class); the feature pipeline owns the join + as-of discipline.

### 9.1 Shipped implementation (2026-04-21)

As of 2026-04-21, this contract is implemented by
`features-service (sports family)/features_sports_service/pipeline/fixture_features.py`:

- **UAC schema:** `unified_api_contracts.internal.FixtureFeatures` (Pydantic, `frozen=True`, `extra="forbid"`) declares
  every column — 21 value-bearing fields plus provenance (`transfermarkt_values_partition_used`,
  `standings_partition_used`, `weather_source`) and metadata (`feature_computed_at`, `schema_version`, `feature_group`).
- **Feature group:** `fixture_features` — sibling to `derived_features` and `odds_features`. Written to
  `gs://features-sports-{project}/sports_features/by_date/day={D}/feature_group=fixture_features/features.parquet` (or
  per-league shards when `league_id` present). Manifest shards record `capture_status` via `ManifestWriter.record_empty`
  / `record_failed` / `add` like the existing groups.
- **Asof lookup helper:** `features_sports_service.pipeline.asof_lookup(df, key_cols, timestamp_col, as_of)` — strict
  `<=` semantics; future rows dropped per key. Unit-tested for lookahead regression-gate: when a source `PLAYER_VALUES`
  parquet contains rows dated after kickoff, the aggregate uses ONLY rows with `as_of_date <= kickoff_date`.
- **Join details:**
  - Transfermarkt — `FIXTURE_LINEUPS × PLAYER_VALUES` asof join. Aggregates per team: `sum(market_value_eur)` over
    lineup players with resolved values, plus `team_value_coverage_pct = resolved / lineup_size`. Missing players ->
    NULL (not 0).
  - Standings — reads `entity=standings` from `day=kickoff_date - 1` (pre-match); falls back up to 7 days earlier.
    Missing team (promoted/relegated mid-season) -> NULL for `home_standing_pre` / `away_standing_pre`.
  - Weather — joined on `venue_id`; hourly-kickoff bucket already pre-computed upstream by instruments-service.
    Preference order: `actual_ko_*` (ERA5 historical) > `forecast_t0_ko_*` (same-day nowcast) > `forecast_t24h_ko_*`
    (T-24h forecast). `weather_source` column records which family fed each row.
- **Failure isolation:** the per-fixture loop never raises. A fixture that hits an unexpected data shape emits a NULL
  row with all value columns set to `None` and `weather_source="none"` so the shard as a whole still captures.
- **Lookahead invariants enforced by unit tests:**
  1. Future `PLAYER_VALUES` rows never surface in `home_team_value_eur_as_of_kickoff` (even when dominant in the source
     DataFrame).
  2. Weather picks the kickoff-hour bucket containing `kickoff_utc`, never adjacent hours / daily averages.
  3. Missing raw inputs propagate NULL — never zeros, never "latest available", never a current-date fallback.
- **Out-of-scope / follow-ups:**
  - Transfermarkt `player_values` 2020-2026 backfill — prod has 2019-01 partitions only. Operator task; run
    `bash deployment-service/scripts/vm/launch-transfermarkt-backfill-vm.sh 2020-01-01 2026-04-21`.
  - SFI `SFI_LEAGUES + SFI_PROGRESSIVE_STATS` 2020-2026 backfill — prod has 2019-01 partitions only. Operator task; run
    `bash deployment-service/scripts/vm/launch-sfi-backfill-vm.sh 2020-01-01 2026-04-21`. Launcher shipped by plan
    `features_sports_upstream_coverage_gaps_2026_04_21`. Note: there is no `SFI_STANDINGS` endpoint (see §2.4).

### 9.2 Derived-features data-crime fixes (2026-04-21)

Paired follow-up plan `features_sports_derived_data_crime_fixes_2026_04_21` removed two pre-existing crimes from
`features-service (sports family)` on 2026-04-21 (FSS commit `576d210`):

- **`calculators/squad_value_calculator.py`** — every `0.0` default flipped to `np.nan`. Missing-team / missing-row /
  divide-by-zero-guard paths now propagate NaN so ML downstream can distinguish "Transfermarkt coverage unknown" from
  "team literally worth €0" (direct violation of §5 before the fix). 4 regression tests in
  `test_new_phase4_calculators.py` proving NaN propagation + populated-team backward compat.
- **`exporters/derived_features_exporter.py::_compute_league_batch`** — standings read hoisted to
  `data/gcs_reader.py::read_pre_match_standings(target_date)` which reads `day=kickoff_date - 1` with 7-day fallback.
  Previously read `day=kickoff_date` which could include post-match table refreshes from earlier-kickoff fixtures
  (same-day Tier-1 cron fires every 6h). 7 regression tests in `test_pre_match_standings.py` proving the same-day
  partition is NEVER read + fallback + empty-result discipline.
- **Aligned bug fix**: `pipeline/fixture_features.py::_lookup_standing` read the raw `rank` column, but
  `gcs_reader._normalize_standings` renames `rank → position` at read time. Fix reads `position` (canonical) with `rank`
  fallback for legacy test frames. Resolves the `home_standing_pre NULL while home_points_pre populates` finding from
  the parent plan's 2024-09-01 dry-run — post-fix all 3 EPL fixtures populate `home_standing_pre` from the
  `day=2024-08-31` pre-match partition.

### 9.3 Weather venue-id cross-ref — SCREAMING_SNAKE resolution (2026-04-21)

Follow-up plan `features_sports_upstream_coverage_gaps_2026_04_21` shipped the venue-id cross-ref fix for the weather
join. Root cause: OpenMeteo in `instruments-service.engine.orchestrator._fetch_weather_data` writes weather.parquet
keyed by SCREAMING_SNAKE(venue_name) (e.g. "De Leunen" → `'DE_LEUNEN'`) via an in-adapter `_to_snake(name)` helper,
while fixtures.parquet's `venue_id` is the raw numeric API-Football id (e.g. `'562'`). The two keys never matched, so
parent plan's dry-run saw `weather_source='none'` for 100% of fixtures despite populated weather data.

**Shipped fix** (FSS commit `???` from plan `features_sports_upstream_coverage_gaps_2026_04_21`):

- `features-service (sports family)/features_sports_service/pipeline/fixture_features.py::_lookup_weather` now accepts
  the fixture's `venue_name` alongside `venue_id` and tries two lookups in order: (1) raw `venue_id` (future-friendly if
  upstream ever migrates to numeric weather keys — Option A) then (2) SCREAMING_SNAKE(venue_name) via
  `_venue_name_to_canonical` which replicates the orchestrator's `_to_snake` transform exactly.
- 4 new unit tests in `tests/unit/test_fixture_features_pipeline.py` proving: SCREAMING_SNAKE fallback resolves ("De
  Leunen" → `DE_LEUNEN`), multi-word collapse ("Old Trafford" → `OLD_TRAFFORD`), unknown venue yields
  `weather_source='none'`, raw numeric match takes precedence when both keys are present.
- Dry-run on 2024-09-01 prod GCS: **115/170 fixtures now populate weather** (up from 0/170 before the fix). Remaining 55
  `weather_source='none'` are venues absent from the UAC `VENUE_COORDINATES` registry — legitimate upstream coverage
  gap, not a pipeline bug.

Future cleanup (Option A, tracked as a separate plan when needed): migrate OpenMeteo upstream to write weather keyed on
numeric `venue_id` matching fixtures + venues parquets. Rewrite existing textual-keyed weather parquets in a one-shot
migration. This removes the downstream resolution hop and aligns all three entities on one venue-id semantic.

## 10. Operational summary

| Layer             | Cadence                         | Output                                                             |
| ----------------- | ------------------------------- | ------------------------------------------------------------------ |
| Tier-1 discovery  | 6h                              | FIXTURES (rolling +7d), STANDINGS, LEAGUES, TEAMS                  |
| Tier-2 reference  | 24h                             | INJURIES, TRANSFERS (window-aware), TRANSFERMARKT_VALUES           |
| Tier-3 pre-match  | Per-fixture T-24h / T-6h / T-1h | ODDS snapshots, PREDICTIONS, LINEUPS, WEATHER                      |
| Tier-3 features   | Per-fixture T-1h                | features-service (sports family) denormalised join                 |
| Tier-3 inference  | Per-fixture T-1h                | ml-inference-service pre-match                                     |
| Live odds loop    | Per-venue continuous            | market-tick-data-service sports adapter                            |
| Tier-4 post-match | T+30m / T+24h                   | FIXTURE_STATS, FIXTURE_EVENTS, PLAYER_STATS, XG, PROGRESSIVE_STATS |
| Daily cron        | 06:00 UTC                       | Rolling window refresh + Tier-1/2 batch                            |

## 11. Cross-refs

- Trigger tier config:
  [`deployment-service/configs/sports-trigger-tiers.yaml`](../../deployment-service/configs/sports-trigger-tiers.yaml)
- Per-league coverage rules:
  [`/codex/02-data/sports-data-source-coverage-matrix.md`](sports-data-source-coverage-matrix.md)
- Adapter dependency order: [`/codex/02-data/sports-adapter-dependency-order.md`](sports-adapter-dependency-order.md)
- Manifest v5 contract:
  [`/codex/02-data/availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md)
- Chunk-safe multi-VM writes: [`/codex/02-data/chunk-safe-manifest-migrations.md`](chunk-safe-manifest-migrations.md)
- Live odds connectivity:
  [`/codex/04-architecture/sports-live-odds-connectivity.md`](/codex/04-architecture/sports-live-odds-connectivity.md)
- VM tarball deployment:
  [`/codex/05-infrastructure/vm-tarball-deployment.md`](/codex/05-infrastructure/vm-tarball-deployment.md)

## 12. Roadmap — open plans (entry point for agent hand-off)

This section is the canonical index of every open sports plan as of 2026-04-21. A fresh agent should read this section +
the referenced plan file; together they contain everything needed to pick up any individual plan and execute. No other
context required.

Legend: **C0-C5** = code readiness per `plans/PLAN_FORMAT.md` (C5 = merged). **P0/P1/P2** = priority. **Gated on**:
dependency plan that must reach C5 before this plan can fully execute.

### 12.0 Live progress register (re-audit when plan checkboxes change)

Last audit: 2026-04-22 late (Plan 1 DONE 17/0; Plan 11 near-C5 20/2; Plans 6 + 10 flipped; Plan 5 activated via
VM-daemon path). `[x] done` / `[ ] open` is the mechanical checkbox count in each plan file — not a judgement call.
`First open item` surfaces what the next agent should tackle.

| Plan                                                 | `[x]` / `[ ]` | Status                           | First open item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ---------------------------------------------------- | ------------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 utl_manifest_migration_primitives                  | 17 / 0        | **DONE** ✅ (promote to §12.1)   | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 2 apifootball_enrichment_historical_backfill         | 3 / 7         | **in-flight** — ops work         | VM monitoring through completion, rescan, audits, more VMs, data-status + spot-checks                                                                                                                                                                                                                                                                                                                                                                                                                      |
| 3 non_apifootball_provider_backfill_launchers        | 5 / 2         | **near-C5** — 4 launchers landed | Per-launcher VM smokes; one QG line still called out in plan                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| 4 instruments_service_orchestrator_reliability_fixes | 12 / 8        | **half-way** (Bug 4 shipped)     | Re-smoke WEATHER+XG (`8a91324`) + Bugs 7-8 AF enrichment + STANDINGS per-league + forward-poll VM                                                                                                                                                                                                                                                                                                                                                                                                          |
| 5 sports_scheduler_cron_activation                   | 7 / 4         | **live via VM-daemon** ✅        | Activated 2026-04-22 via `launch-sports-scheduler-vm.sh` on `sports-scheduler-20260422-111929` (Cloud Run path deferred on Plans 12 + 13). Remaining: 6h / 24h first-fire observation + Grafana alert wiring                                                                                                                                                                                                                                                                                               |
| 6 features_sports_pipeline_deployment                | 11 / 3        | **near-C5**                      | Historical backfill VM + coverage audit + UI FIXTURE_FEATURES polish (blocked on Plan 13 UTL base image)                                                                                                                                                                                                                                                                                                                                                                                                   |
| 7 upcoming_fixtures_ui_view                          | 12 / 1        | **near-C5**                      | Local dev smoke only                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 8 vm_observability_codex_update                      | 7 / 0         | **DONE** ✅                      | —                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 9 sports_manifest_shard_migration_cleanup            | 11 / 5        | **half-way** (3 newly flipped)   | Staging/prod purge apply + rescan VM launch + manifest API verify + UI spot-check (VM/operator)                                                                                                                                                                                                                                                                                                                                                                                                            |
| 10 sports_data_status_fixture_level_drilldown        | 15 / 1        | **near-C5**                      | Manual dev smoke only (SPORTS path through fixture list → CSV download)                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| 11 transfermarkt_sfi_team_mapping_cache_and_drift    | 20 / 2        | **near-C5** — nearly shipped     | Final QG + staging spot-check (2 polish items); 20 substantive todos flipped across 4 tracks / 4 repos (UAC `36bed50` + UTL `bf7ad8d1` + instruments-service `9bf23d8` + FSS `1bdf58d` on origin)                                                                                                                                                                                                                                                                                                          |
| 12 deployment_service_build_infrastructure_repair    | 0 / 9         | **authored** — ready-to-pick-up  | Phase 0 archaeology: confirm `ui/api/backends/deployment` never existed + live `deployment-dashboard` image age + gunicorn.conf.py location. Blocks Plan 5 Cloud-Run cron path (VM-daemon workaround already active).                                                                                                                                                                                                                                                                                      |
| 13 utl_base_image_rebuild_and_workflow_unblock       | 0 / 17        | **authored** — ready-to-pick-up  | Phase 0 archaeology confirmed: UTL `:latest` AR image frozen at 2026-04-15 (20+ UTL commits behind). Cloud Build trigger fires but every build since 2026-04-20 18:08 FAILS with `unified-api-contracts was not found in the package registry` inside Dockerfile `uv pip install -e .`. Fix = clone UAC source into Docker build context (Option A). Blocks Plan 6 Phase 3 (features-sports smoke), features-onchain daily workflow, Plan 3 sports-scheduler Cloud Run activation (also gated on Plan 12). |

**On-disk implementation evidence** (sanity-check: the code is actually there):

| Check                                                                                                                 | Result                                                         |
| --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `unified-trading-library/unified_trading_library/manifest_migrations/`                                                | Present (chunk_splitter.py, migrator.py, rescan.py, purger.py) |
| `deployment-service/scripts/vm/launch-{transfermarkt,footystats,openmeteo,understat}-backfill-vm.sh`                  | All 4 present                                                  |
| `deployment-api/deployment_api/services/data_status_drilldown.py::build_fixture_breakdown` / `build_fixture_download` | Present                                                        |
| `deployment-ui/src/api/client.ts::fetchFixtureBreakdown` + `FixtureBreakdown.test.tsx`                                | Present                                                        |
| `deployment-api/deployment_api/routes/fixtures.py`                                                                    | Present                                                        |
| `/codex/05-infrastructure/vm-tarball-deployment.md` Observability section                                             | Present (Plan 8's target)                                      |

**Heaviest remaining work:**

- **Plan 2** (AF enrichment backfill) — multi-day VM runs gated by API-Football rate limit.
- **Plan 4** (orchestrator reliability) — Bugs 7-8 (AF enrichment + STANDINGS per-league) + re-smoke still open. Bug 4
  (adapter output dict coercion) shipped 2026-04-22 `7f2cbf0`.
- **Plans 5 + 6** (deployment activation) — GCP auth + IAM + Cloud Scheduler creation; operator-sign-off territory.
- **Plan 9** (shard-migration cleanup) — depends on Plan 1 C5 + Plan 4 Bugs 7-8; then runs per-entity rescans + purge. 3
  todos flipped 2026-04-22 crediting `5f2cae3` (Phase 1-2) + `d194288` (Phase 2 XG test inversion).
- **Plan 11** (transfermarkt + SFI team-mapping cache + drift detection) — code shipped 2026-04-22 across 4 repos (UAC
  `36bed50` + UTL `bf7ad8d1` + instruments-service `9bf23d8` + FSS `1bdf58d`); 20/22 todos flipped. Only 2 polish items
  remain (tarball refresh `--asset-group SPORTS` + cache-speedup validation VM run + plan unlock).
- **Plans 12 + 13** (deployment-service Dockerfile repair + UTL base image rebuild) — authored 2026-04-22 after wave-2
  crisis recovery surfaced Cloud Build infra rot. Gate Plan 5 Cloud Run path + Plan 6 features-sports Cloud Build.

**Basically done (orchestrator-gate only):** Plans 1, 7, 8, 10, 11 (post-smoke + unlock), 3 (post per-launcher smoke).

### 12.1 Shipped (reference only — no more work)

| Plan                                                                                                                                  | Repos                                                    | Status                     |
| ------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | -------------------------- |
| [`sports_scheduler_periodic_tier_dispatch`](../../plans/archive/sports_scheduler_periodic_tier_dispatch_2026_04_21.plan.md)           | deployment-service                                       | C5 (`d9652cd`)             |
| [`instruments_service_rolling_window_cli_flags`](../../plans/archive/instruments_service_rolling_window_cli_flags_2026_04_21.plan.md) | instruments-service + deployment-service                 | C5 (`70517b2` + `b0eb874`) |
| [`features_sports_denormalisation_pipeline`](../../plans/archive/features_sports_denormalisation_pipeline_2026_04_21.plan.md)         | unified-api-contracts + features-service (sports family) | C5 (`ef1e89f` + `c7a363d`) |
| [`utl_manifest_migration_primitives`](../../plans/archive/utl_manifest_migration_primitives_2026_04_21.plan.md)                       | unified-trading-library + instruments-service            | C5 (`b2ad7d0c`, 17/0)      |
| [`vm_observability_codex_update`](../../plans/archive/vm_observability_codex_update_2026_04_21.plan.md)                               | unified-trading-pm                                       | C5 (7/0)                   |

### 12.2 Open — data coverage + adapter quality

| Priority | Plan | Repos | Gated on | Delivers | | -------- |
-------------------------------------------------------------------------------------------------------------------------------------------------------------

| --------------------------------------------------------------------------------------------------- |
----------------------------------------------------------------------------------------------------------------------------------------

|
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| -------------- |
-------------------------------------------------------------------------------------------------------------------- | |
**P0** |
[`apifootball_enrichment_historical_backfill`](../../plans/archive/apifootball_enrichment_historical_backfill_2026_04_21.plan.md)
| deployment-service | — | Biggest SPORTS coverage lift: FIXTURE_STATS / EVENTS / LINEUPS / PLAYER_STATS / INJURIES over
2019-01-16..2026-04-20. Takes attempted-coverage 17.8% → 50%+ | | **P1** |
[`non_apifootball_provider_backfill_launchers`](../../plans/archive/non_apifootball_provider_backfill_launchers_2026_04_21.plan.md)
| deployment-service | — | 4 new launchers for Transfermarkt / FootyStats / OpenMeteo / Understat mirroring the AF
launcher | | **P1** |
[`instruments_service_orchestrator_reliability_fixes`](../../plans/archive/instruments_service_orchestrator_reliability_fixes_2026_04_21.plan.md)
| instruments-service | — | 8 bugs: 3 reliability (Pydantic None-goals, UnboundLocalError, 404 on future dates) + 1
adapter-output dict coercion (**shipped `7f2cbf0`**) + 4 per-league shard uniformity (WEATHER + XG **shipped
`8a91324`**; AF enrichments + STANDINGS open — Bugs 7-8). **Currently C1** — Phases 1-3, 3b, 4 shipped; Phase 5 (Bugs
7-8) + Phases 6-7 open | | **P2** |
[`transfermarkt_sfi_team_mapping_cache_and_drift_detection`](../../plans/archive/transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22.plan.md)
| unified-api-contracts + instruments-service + features-service (sports family) + unified-trading-pm |
`features_sports_denormalisation_pipeline` ✅ C5 + `features_sports_derived_data_crime_fixes` +
`features_sports_upstream_coverage_gaps` | Cut redundant TM + SFI API calls via
`sports_reference/mappings/transfermarkt_league_teams/season={YYYY}/teams.parquet` + `sfi_league_mapping.parquet`. Adds
UAC `LeagueDefinition.expected_team_count_per_season` + `get_expected_team_count_for_league`; emits
`ADAPTER_FETCH_ANOMALY` when
` | got - expected | /expected > 10%`without blocking manifest writes.
22 todos / 4 tracks / 4 repos. **Authored 2026-04-22`e5d941e1`\*\* |

### 12.3 Open — manifest + UI hygiene (gated on 12.2)

**Dependency chain:** `utl_manifest_migration_primitives` ships the SSOT chunk-safe machinery in
`unified-trading-library.manifest_migrations` (see `chunk-safe-manifest-migrations.md`). It **must reach C5** before
`sports_manifest_shard_migration_cleanup` — the cleanup plan calls those primitives directly and must not re-introduce
forked coordinator/worker logic in `instruments-service`.

| Priority | Plan                                                                                                                              | Repos                                                      | Gated on                                                         | Delivers                                                                                                                                                                                                         |
| -------- | --------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0**   | [`sports_manifest_shard_migration_cleanup`](../../plans/ai/sports_manifest_shard_migration_cleanup_2026_04_21.plan.md)            | instruments-service + deployment-api                       | `utl_manifest_migration_primitives` ✅ C5 + reliability Bugs 7-8 | Uses UTL primitives to scan every entity's parquet + emit per-league rows. Drops backwards-compat unsharded emission. One-time legacy-row purge. Closes the three-state manifest orphan problem                  |
| **P1**   | [`sports_data_status_fixture_level_drilldown`](../../plans/archive/sports_data_status_fixture_level_drilldown_2026_04_21.plan.md) | deployment-api + deployment-ui                             | `sports_manifest_shard_migration_cleanup` + reliability Bugs 7-8 | Fixture-anchored UI navigation: Category → Data Type → League → Day → **Fixture** → Download CSV/JSON. Green-day expands fixture list with per-fixture coverage; red-day shows missing fixtures from AF schedule |
| **P2**   | [`upcoming_fixtures_ui_view`](../../plans/archive/upcoming_fixtures_ui_view_2026_04_21.plan.md)                                   | deployment-api + deployment-ui + unified-trading-system-ui | —                                                                | Per-league next-7-days forward-view cards (complementary to the backward drilldown above)                                                                                                                        |

### 12.4 Open — deployment activation (dependencies already at C5)

| Priority | Plan                                                                                                                                      | Repos                                                 | Gated on                                                                                                                                           | Delivers                                                                                                                                                                                                                                                                                                                                                                                                                  |
| -------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0**   | [`utl_base_image_rebuild_and_workflow_unblock`](../../plans/ai/utl_base_image_rebuild_and_workflow_unblock_2026_04_22.plan.md)            | unified-trading-library                               | —                                                                                                                                                  | Rebuild UTL base image in AR (frozen since 2026-04-15, 20+ commits behind). Fix `cloudbuild.yaml` Docker build step which fails because `uv pip install -e .` can't resolve UAC from AR. Option A: clone UAC into Docker build context via new cloudbuild step. **Blocks Plan 6 Phase 3 (features-sports smoke), features-onchain daily workflow, Plan 3 sports-scheduler Cloud Run activation (also gated on Plan 12).** |
| **P0**   | [`deployment_service_build_infrastructure_repair`](../../plans/archive/deployment_service_build_infrastructure_repair_2026_04_22.plan.md) | deployment-service                                    | —                                                                                                                                                  | Repair 6 bugs in Dockerfile + cloudbuild.yaml blocking all Cloud Builds since 2026-02-20. Lands first fresh `deployment-dashboard` + `sports-scheduler` AR image in 2+ months. **Blocks Plan 5** below.                                                                                                                                                                                                                   |
| **P0**   | [`sports_scheduler_cron_activation`](../../plans/ai/sports_scheduler_cron_activation_2026_04_21.plan.md)                                  | deployment-service                                    | `sports_scheduler_periodic_tier_dispatch` ✅ C5 + `deployment_service_build_infrastructure_repair` + `utl_base_image_rebuild_and_workflow_unblock` | Cloud Run + Cloud Scheduler cron so Tier-1/2 actually fire in prod                                                                                                                                                                                                                                                                                                                                                        |
| **P1**   | [`features_sports_pipeline_deployment`](../../plans/archive/features_sports_pipeline_deployment_2026_04_21.plan.md)                       | features-service (sports family) + deployment-service | `features_sports_denormalisation_pipeline` ✅ C5 + `utl_base_image_rebuild_and_workflow_unblock`                                                   | Cloud Run deployment + historical FixtureFeatures backfill 2018-2026                                                                                                                                                                                                                                                                                                                                                      |

### 12.5 Open — docs

All doc-only plans shipped. See §12.1 for `vm_observability_codex_update` (C5).

### 12.6 Execution DAG

```
Start-anywhere (independent):
  ├─ apifootball_enrichment_historical_backfill  (P0)
  ├─ non_apifootball_provider_backfill_launchers (P1)
  ├─ upcoming_fixtures_ui_view                   (P2)
  ├─ vm_observability_codex_update               (P2 docs)
  ├─ deployment_service_build_infrastructure_repair  (P0) ─┐
  │                                                         │
  │                                                         └─► sports_scheduler_cron_activation (P0, gated on build repair)
  ├─ features_sports_pipeline_deployment         (P1, unblocked — own Dockerfile clean; Phase 6 confirms)
  ├─ transfermarkt_sfi_team_mapping_cache_and_drift_detection  (P2, unblocked — 3 parent plans at C5)
  └─ instruments_service_orchestrator_reliability_fixes  (P1, C1 — Bugs 7-8 + re-smoke + E2E + QG remain)
           │
           └─ Bugs 7-8 ship ─► sports_manifest_shard_migration_cleanup (P0)
                                       │
                                       └─► sports_data_status_fixture_level_drilldown (P1)
```

### 12.7 Agent-handoff minimum

For each plan, the executing agent needs exactly:

1. `plans/PLAN_FORMAT.md`
2. `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
3. The plan file itself (self-contained — pre-audit manifest + phased DAG + success criteria)
4. This codex doc (§1-11 for architecture; §12 for cross-plan dep awareness)

**Preferred dispatch shape — master plan with orchestrator + parallel sub-agents:** Use
[`sports_roadmap_master_execution_2026_04_21.plan.md`](../../plans/ai/sports_roadmap_master_execution_2026_04_21.plan.md)
— one orchestrator agent dispatches 8 parallel sub-agents for independent plans, barriers on completion, runs
integration QG, pushes all repos serially (avoiding concurrent-push races), then dispatches the 2 chained plans.
Sub-agents commit locally but don't push; orchestrator owns origin.

**Solo dispatch** (if not using the master plan): "Execute `plans/active/<plan_name>.md`. Follow pre-audit manifest
strictly. Flip checkboxes as you go. Commit + quickmerge per repo in the phases."

Also update the shard-migration plan's gated-on to include the UTL primitives plan — once the UTL refactor ships, the
shard-migration plan's Phase 1 is "use the UTL primitives" not "extend the rescan script".

### 12.8 Universal VM pre-flight (applies to every plan that launches a VM)

Every plan that dispatches a GCE VM via `deployment-service/scripts/vm/launch-*.sh` MUST run these in order, BEFORE the
launcher:

1. **Pass 1 QG** on every repo the VM runs code from: `cd <repo> && bash scripts/quality-gates.sh`. Establishes that the
   local venv's deps resolve + tests pass.
2. **Tarball refresh** matching the repos above:
   `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group <CAT>` (or `--all` for multi-repo features,
   or `--include <repo>` for one-offs). Tarballs are built from the same venvs that just passed QG — so VM deps = local
   deps.
3. **Use a launcher, never raw gcloud**. Every `launch-*-vm.sh` script inherits observability from today's fixes
   (`cc07649` + `beaa2e5`):
   - Heartbeat daemon → Pub/Sub events + GCS log streaming every 30s + entry in `/api/vm-deployments`
   - Self-delete on rc=0 → VMs auto-clean, no manual `gcloud compute instances delete`
   - Singleton-lock semantics per rate-limited API key

   Raw `gcloud compute instances create` bypasses all three. Don't do it.

4. Launchers that route through `_launch_with_tee` (every existing one does) inherit the observability guarantees
   automatically — no per-launcher wiring needed.

Plans that violate the pre-flight (raw gcloud, skip tarball refresh, skip QG) should be flagged back to the operator
before execution.

**Observability endpoints (no SSH required):**

- `gcloud compute instances list --filter="labels.purpose=<tag>" --zones=asia-northeast1-c` — list live VMs
- `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/<vm-name>/run.log` — streaming log
- `curl -sS 'https://<deployment-api>/api/vm-deployments?status=running' | jq` — registry query
- Pub/Sub topic `deployment-lifecycle-events` — every DEPLOYMENT_STARTED / PROGRESS / COMPLETED / FAILED
