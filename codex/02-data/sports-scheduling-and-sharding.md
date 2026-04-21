---
title: Sports Scheduling & Sharding
status: canonical
last_updated: 2026-04-21
---

# Sports Scheduling & Sharding

SSOT for **when** each sports data source is fetched, **how far ahead / behind**, **when the underlying data is actually
published** (lookahead-bias discipline for historical backfill), and **how shards are keyed** in the availability
manifest. Consolidates the trigger-tier scheduler (`deployment-service/configs/sports-trigger-tiers.yaml`) with adapter
implementation details and a per-fixture sharding contract.

## 1. Anchoring principle — fixture_id is the canonical shard key

Every piece of sports data — schedules, stats, odds, standings, weather, player values — maps back to a **fixture**.
`(league_id, kickoff_date)` is derivable from `fixture_id`, not the other way round.

**Consequence:** the availability manifest's primary per-shard key for fixture-native data types is `fixture_id`. For
venue-native or player-native data (weather, Transfermarkt values, league standings), we still write shard-native rows
in their own storage layout, but **features-sports-service denormalises them onto each fixture** at feature-compute time
so every fixture has a complete as-of snapshot without lookahead leakage.

`(date, league_id)` remains the **query-time index** and **backfill horizon** — it's what the daily cron iterates and
what the UI data-status drilldown renders. But it's not what the data is.

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
- **Denormalisation to fixture:** features-sports-service materialises
  `fixture_id → [{player_id, value_eur_as_of_kickoff}]` by joining `FIXTURE_LINEUPS` (who played) × `PLAYER_VALUES` (≤
  kickoff). The player value is the most-recent snapshot with `as_of_date <= kickoff_date`. **Duplicating the value onto
  every fixture is correct** — it preserves the as-of invariant and keeps the features table flat.

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

- **Fetches:** `SFI_STANDINGS` (league tables with live updates), `SFI_LEAGUES`, `PROGRESSIVE_STATS` (streaks,
  sequences).
- **Cadence:** Tier-1 every 6h for `SFI_STANDINGS` + `SFI_LEAGUES`; Tier-4 T+24h for `PROGRESSIVE_STATS` (needs
  completed-matchday state).
- **Published:** Standings update after every matchday's last whistle. Progressive stats recomputed daily.
- **Shard key:** `(date, league_id)` for standings; `(league_id, season)` for progressive stats. Not fixture-native.
- **Denormalisation to fixture:** for each fixture, features-sports-service takes the standings row with
  `as_of_date == kickoff_date - 1` for each of home/away teams (opponent's pre-match table position is a feature).

### 2.5 OpenMeteo / Weather (`open_meteo.py`)

- **Fetches:** `WEATHER` (temperature, precipitation, wind, humidity, cloud cover, weather_code) per (latitude,
  longitude, hour).
- **Cadence:**
  - **Forecast** (dates > today): Tier-1 discovery 6h + Tier-3 T-24h + T-1h (nowcast just before kickoff).
  - **Observed** (dates ≤ today): single fetch at T+1h post-kickoff from the ERA5 archive endpoint.
- **Published:** OpenMeteo refreshes forecast every hour; ERA5 archive finalised several days post-date.
- **Shard key:** `(venue_lat, venue_lon, date)` — one weather fetch per venue per day covers all fixtures at that venue.
- **Denormalisation to fixture:** features-sports-service joins `(venue_id → lat/lon)` ×
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
[`vm-tarball-deployment.md` § Observability & Lifecycle](../05-infrastructure/vm-tarball-deployment.md#observability--lifecycle)
(provenance: `deployment-service` `cc07649`, `beaa2e5`).

See [`codex/05-infrastructure/vm-tarball-deployment.md`](../05-infrastructure/vm-tarball-deployment.md) for the VM
shape; see
[`codex/05-infrastructure/runtime-tiers-and-deployment.md`](../05-infrastructure/runtime-tiers-and-deployment.md) for
Cloud Run job wiring.

## 9. Per-fixture denormalisation pattern

Fixture-native providers (API-Football fixture-scope entities, FootyStats, Understat) write directly to per-fixture
parquets. Non-fixture providers (Transfermarkt, SFI standings, OpenMeteo weather) write to their natural shard and are
denormalised onto fixtures by features-sports-service:

```
Raw shards                                   Denormalised per-fixture table
-----------                                  ------------------------------
sports_reference/
  by_date/day={D}/entity=fixtures/           fixture_id
     fixtures.parquet           ─┐           ├─ kickoff_utc, league_id, home, away
                                 │           ├─ home_standing_position_pre (from SFI)
  by_date/day={D}/entity=         │           ├─ away_standing_position_pre (from SFI)
    standings/standings.parquet ─┤           ├─ home_team_value_as_of (from Transfermarkt)
                                 ├── join ──►├─ away_team_value_as_of (from Transfermarkt)
  player_values/                 │           ├─ kickoff_weather (from OpenMeteo)
    player={P}/values.parquet   ─┤           └─ ... (xG, odds snapshots, etc.)
                                 │
  weather/                       │
    venue={V}/day={D}/           │
    weather.parquet             ─┘
```

The denormalisation happens at feature-compute time (features-sports-service), not at ingestion. The raw shards stay
normalised (single source of truth per data class); the feature pipeline owns the join + as-of discipline.

### 9.1 Shipped implementation (2026-04-21)

As of 2026-04-21, this contract is implemented by
`features-sports-service/features_sports_service/pipeline/fixture_features.py`:

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
  - `calculators/squad_value_calculator.py` (old path) still defaults missing data to 0.0 — a data crime per §5. Replace
    with the new `fixture_features` output once downstream consumers migrate.
  - Transfermarkt `player_values` partitions exist only for `day=2019-01-01 / 2019-01-02` in prod as of 2026-04-21; the
    2020-2026 backfill VM run is a prerequisite for non-NULL team-value coverage.
  - `entity=sfi_standings/` is absent; the SFI-native join defined in §2.4 uses API-Football `entity=standings` as the
    proxy until the SFI backfill lands.

## 10. Operational summary

| Layer             | Cadence                         | Output                                                             |
| ----------------- | ------------------------------- | ------------------------------------------------------------------ |
| Tier-1 discovery  | 6h                              | FIXTURES (rolling +7d), STANDINGS, LEAGUES, TEAMS                  |
| Tier-2 reference  | 24h                             | INJURIES, TRANSFERS (window-aware), TRANSFERMARKT_VALUES           |
| Tier-3 pre-match  | Per-fixture T-24h / T-6h / T-1h | ODDS snapshots, PREDICTIONS, LINEUPS, WEATHER                      |
| Tier-3 features   | Per-fixture T-1h                | features-sports-service denormalised join                          |
| Tier-3 inference  | Per-fixture T-1h                | ml-inference-service pre-match                                     |
| Live odds loop    | Per-venue continuous            | market-tick-data-service sports adapter                            |
| Tier-4 post-match | T+30m / T+24h                   | FIXTURE_STATS, FIXTURE_EVENTS, PLAYER_STATS, XG, PROGRESSIVE_STATS |
| Daily cron        | 06:00 UTC                       | Rolling window refresh + Tier-1/2 batch                            |

## 11. Cross-refs

- Trigger tier config:
  [`deployment-service/configs/sports-trigger-tiers.yaml`](../../deployment-service/configs/sports-trigger-tiers.yaml)
- Per-league coverage rules:
  [`codex/02-data/sports-data-source-coverage-matrix.md`](sports-data-source-coverage-matrix.md)
- Adapter dependency order: [`codex/02-data/sports-adapter-dependency-order.md`](sports-adapter-dependency-order.md)
- Manifest v5 contract:
  [`codex/02-data/availability-manifest-and-data-status.md`](availability-manifest-and-data-status.md)
- Chunk-safe multi-VM writes: [`codex/02-data/chunk-safe-manifest-migrations.md`](chunk-safe-manifest-migrations.md)
- Live odds connectivity:
  [`codex/04-architecture/sports-live-odds-connectivity.md`](../04-architecture/sports-live-odds-connectivity.md)
- VM tarball deployment:
  [`codex/05-infrastructure/vm-tarball-deployment.md`](../05-infrastructure/vm-tarball-deployment.md)

## 12. Roadmap — open plans (entry point for agent hand-off)

This section is the canonical index of every open sports plan as of 2026-04-21. A fresh agent should read this section +
the referenced plan file; together they contain everything needed to pick up any individual plan and execute. No other
context required.

Legend: **C0-C5** = code readiness per `plans/PLAN_FORMAT.md` (C5 = merged). **P0/P1/P2** = priority. **Gated on**:
dependency plan that must reach C5 before this plan can fully execute.

### 12.1 Shipped 2026-04-21 (reference only — no more work)

| Plan                                                                                                                                 | Repos                                           | Status                     |
| ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------- | -------------------------- |
| [`sports_scheduler_periodic_tier_dispatch`](../../plans/active/sports_scheduler_periodic_tier_dispatch_2026_04_21.plan.md)           | deployment-service                              | C5 (`d9652cd`)             |
| [`instruments_service_rolling_window_cli_flags`](../../plans/active/instruments_service_rolling_window_cli_flags_2026_04_21.plan.md) | instruments-service + deployment-service        | C5 (`70517b2` + `b0eb874`) |
| [`features_sports_denormalisation_pipeline`](../../plans/active/features_sports_denormalisation_pipeline_2026_04_21.plan.md)         | unified-api-contracts + features-sports-service | C5 (`ef1e89f` + `c7a363d`) |

### 12.2 Open — data coverage + adapter quality

| Priority | Plan                                                                                                                                             | Repos               | Gated on | Delivers                                                                                                                                                                                                                                                        |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0**   | [`apifootball_enrichment_historical_backfill`](../../plans/active/apifootball_enrichment_historical_backfill_2026_04_21.plan.md)                 | deployment-service  | —        | Biggest SPORTS coverage lift: FIXTURE_STATS / EVENTS / LINEUPS / PLAYER_STATS / INJURIES over 2019-01-16..2026-04-20. Takes attempted-coverage 17.8% → 50%+                                                                                                     |
| **P1**   | [`non_apifootball_provider_backfill_launchers`](../../plans/active/non_apifootball_provider_backfill_launchers_2026_04_21.plan.md)               | deployment-service  | —        | 4 new launchers for Transfermarkt / FootyStats / OpenMeteo / Understat mirroring the AF launcher                                                                                                                                                                |
| **P1**   | [`instruments_service_orchestrator_reliability_fixes`](../../plans/active/instruments_service_orchestrator_reliability_fixes_2026_04_21.plan.md) | instruments-service | —        | 7 bugs: 3 reliability (Pydantic None-goals, UnboundLocalError, 404 on future dates) + 4 per-league shard uniformity (WEATHER + XG **shipped `8a91324`**; AF enrichments + STANDINGS open). **Currently C1** — Phase 4 WEATHER/XG shipped, Phases 1-3 + 5-7 open |

### 12.3 Open — manifest + UI hygiene (gated on 12.2)

| Priority | Plan                                                                                                                             | Repos                                                      | Gated on                                                         | Delivers                                                                                                                                                                                                         |
| -------- | -------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0**   | [`utl_manifest_migration_primitives`](../../plans/active/utl_manifest_migration_primitives_2026_04_21.plan.md)                   | unified-trading-library + instruments-service              | —                                                                | Factors chunk-safe writer / rescan scanner / legacy-row purger into UTL as reusable primitives. Auto-emits MANIFEST*MIGRATION*\* events. Refactors `rescan_sports_fixtures_canonical.py` to thin wrapper         |
| **P0**   | [`sports_manifest_shard_migration_cleanup`](../../plans/active/sports_manifest_shard_migration_cleanup_2026_04_21.plan.md)       | instruments-service + deployment-api                       | `utl_manifest_migration_primitives` + reliability Bugs 6-7       | Uses UTL primitives to scan every entity's parquet + emit per-league rows. Drops backwards-compat unsharded emission. One-time legacy-row purge. Closes the three-state manifest orphan problem                  |
| **P1**   | [`sports_data_status_fixture_level_drilldown`](../../plans/active/sports_data_status_fixture_level_drilldown_2026_04_21.plan.md) | deployment-api + deployment-ui                             | `sports_manifest_shard_migration_cleanup` + reliability Bugs 6-7 | Fixture-anchored UI navigation: Category → Data Type → League → Day → **Fixture** → Download CSV/JSON. Green-day expands fixture list with per-fixture coverage; red-day shows missing fixtures from AF schedule |
| **P2**   | [`upcoming_fixtures_ui_view`](../../plans/active/upcoming_fixtures_ui_view_2026_04_21.plan.md)                                   | deployment-api + deployment-ui + unified-trading-system-ui | —                                                                | Per-league next-7-days forward-view cards (complementary to the backward drilldown above)                                                                                                                        |

### 12.4 Open — deployment activation (dependencies already at C5)

| Priority | Plan                                                                                                               | Repos                                        | Gated on                                         | Delivers                                                             |
| -------- | ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------------------- |
| **P0**   | [`sports_scheduler_cron_activation`](../../plans/active/sports_scheduler_cron_activation_2026_04_21.plan.md)       | deployment-service                           | `sports_scheduler_periodic_tier_dispatch` ✅ C5  | Cloud Run + Cloud Scheduler cron so Tier-1/2 actually fire in prod   |
| **P1**   | [`features_sports_pipeline_deployment`](../../plans/active/features_sports_pipeline_deployment_2026_04_21.plan.md) | features-sports-service + deployment-service | `features_sports_denormalisation_pipeline` ✅ C5 | Cloud Run deployment + historical FixtureFeatures backfill 2018-2026 |

### 12.5 Open — docs

| Priority | Plan                                                                                                   | Repos              | Gated on | Delivers                                                                                                                                                      |
| -------- | ------------------------------------------------------------------------------------------------------ | ------------------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P2**   | [`vm_observability_codex_update`](../../plans/active/vm_observability_codex_update_2026_04_21.plan.md) | unified-trading-pm | —        | Doc-only. Extends `codex/05-infrastructure/vm-tarball-deployment.md` with Observability + Lifecycle section documenting today's fixes (`cc07649` + `beaa2e5`) |

### 12.6 Execution DAG

```
Start-anywhere (independent):
  ├─ apifootball_enrichment_historical_backfill  (P0)
  ├─ non_apifootball_provider_backfill_launchers (P1)
  ├─ upcoming_fixtures_ui_view                   (P2)
  ├─ vm_observability_codex_update               (P2 docs)
  ├─ sports_scheduler_cron_activation            (P0, unblocked)
  ├─ features_sports_pipeline_deployment         (P1, unblocked)
  └─ instruments_service_orchestrator_reliability_fixes  (P1, C1 — 4 of 7 phases remaining)
           │
           └─ Bugs 6-7 ship ─► sports_manifest_shard_migration_cleanup (P0)
                                       │
                                       └─► sports_data_status_fixture_level_drilldown (P1)
```

### 12.7 Agent-handoff minimum

For each plan, the executing agent needs exactly:

1. `plans/PLAN_FORMAT.md`
2. `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
3. The plan file itself (self-contained — pre-audit manifest + phased DAG + success criteria)
4. This codex doc (§1-11 for architecture; §12 for cross-plan dep awareness)

One-sentence dispatch: "Execute `plans/active/<plan_name>.plan.md`. Follow pre-audit manifest strictly. Flip checkboxes
as you go. Commit + quickmerge per repo in the phases."

Also update the shard-migration plan's gated-on to include the UTL primitives plan — once the UTL refactor ships, the
shard-migration plan's Phase 1 is "use the UTL primitives" not "extend the rescan script".

### 12.8 Universal VM pre-flight (applies to every plan that launches a VM)

Every plan that dispatches a GCE VM via `deployment-service/scripts/vm/launch-*.sh` MUST run these in order, BEFORE the
launcher:

1. **Pass 1 QG** on every repo the VM runs code from: `cd <repo> && bash scripts/quality-gates.sh`. Establishes that the
   local venv's deps resolve + tests pass.
2. **Tarball refresh** matching the repos above:
   `bash deployment-service/scripts/vm/create-code-tarballs.sh --category <CAT>` (or `--all` for multi-repo features, or
   `--include <repo>` for one-offs). Tarballs are built from the same venvs that just passed QG — so VM deps = local
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
