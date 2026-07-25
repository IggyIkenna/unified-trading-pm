---
doc_type: plan
title:
  Data completion to 100% — Sports live/forward data-availability matrix + source-latency validation (companion to the
  sports parity sibling)
summary: >-
  Sports-specific live/forward data-availability matrix (per data_type x source: availability phase, live
  timestamp/cadence, live feed status, gap + cheap-source recommendation) and the companion source-latency validation
  (empirical p95-lag investigation for the 5 assumed constants in unified-api-contracts' source_data_latency.py, the
  shipped observation-recorder instrumentation, and the re-pin migration plan), split out of
  data_completion_to_100_all_ag_2026_06_21.md (M-1) on 2026-07-24 per the plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md). This content is sports-specific (same class as the
  "Sports honest-coverage" section split into data_completion_sports_2026_07_24.md earlier the same day) but was kept as
  its own companion file rather than folded into that sibling to avoid pushing it over its own 1000-line cap. Two todos
  remain open here (Live-ODDS quota decision, source_data_latency.py re-pin); both are BLOCKED-OPERATOR-DECISION / gated
  on ~2-week accrual, not orphaned. Nothing was dropped or reworded in the move.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service, unified-api-contracts]
scope: [engineer, admin]
tags: [backfill, manifest, honest-coverage, data-completion, sports, live-trading, data-correctness]
related:
  [
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/data_completion_sports_2026_07_24.md,
    /plans/archive/2026_07/data_completion_sports_history_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  data_completion_to_100_all_ag_2026_06_21 (M-1) -- split 2026-07-24, plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md), operator-approved trim pattern (M-1 was ~1820 lines
  against the 1000-line cap; this sports-specific 249-line block was moved to its own active companion file rather than
  data_completion_sports_2026_07_24.md, which had no headroom left under its own cap).
drift_direction: advance-code
---

# Data completion to 100% — Sports live/forward availability + source-latency validation

> **Split from M-1 on 2026-07-24** (`data_completion_to_100_all_ag_2026_06_21.md`, plan line-cap remediation,
> `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`). This is a **verbatim** extraction of the "Live/forward
> sports data-availability matrix + continuation gaps" and "Source-latency validation" sections — no content was
> altered, only relocated. The 2 open todos below (Live-ODDS quota + the source_data_latency.py re-pin) remain tracked
> here, not archived. See `data_completion_to_100_all_ag_2026_06_21.md` for the cross-cutting coordinator hub and
> `data_completion_sports_2026_07_24.md` for the rest of the sports parity-sibling scope.

## Live/forward sports data-availability matrix + continuation gaps (2026-06-22)

> **Question (operator framing):** fixtures are determinable in advance then updated for cancelled/postponed; for the
> rest (weather, understat, footystats, odds, transfermarkt, player-stats …) figure out what we can get LIVE going
> FORWARD, the timestamps/latencies, and which sources we must scrape elsewhere or replace with a cheap API to keep
> FEATURES + ML flowing forward (not just historical backfill).

**Bottom line:** the sports pipeline already has a **live/forward driver** — the long-lived `sports-scheduler-*` VM
(`deployment-service/scripts/vm/launch-sports-scheduler-vm.sh`, daemon, `poll=300s`, singleton-locked) running
`deployment_service sports-trigger run --config configs/sports-trigger-tiers.yaml`. That tiers config IS the
forward-scheduling SSOT: it fires **the same batch CLIs** on fixture-proximate / rolling windows ("sports live = batch
with a fixture-proximate or rolling date window" — `sports-trigger-tiers.yaml` header). So the forward feed is **already
coded for nearly every data_type**; the real gaps are (a) two scrape-only sources with NO forward poll (Transfermarkt,
Understat-dedicated) and (b) the live ODDS WS being credit/quota-gated. "Live timestamp" below = when the data first
exists relative to kickoff (KO) / full-time (FT); the post-match lags are the empirically-calibrated p95 values in
`unified-api-contracts/.../registry/source_data_latency.py` (`report_time = match_end + lag`).

### Matrix — (data_type × source): availability phase · live timestamp/cadence · live feed status TODAY · gap + cheap-source recommendation

| data_type (source)                                               | Phase                           | Live timestamp / cadence                                                                                                                                                             | Live feed status TODAY                                                                                                                                                                                                               | Gap + recommendation                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ---------------------------------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **FIXTURES** (api_football)                                      | **FORWARD** / determinable      | Announced **KO−7d** (`_ANNOUNCED_AT_LEAD_DAYS=7`); re-polled every fire over `[today, today+8d]` → cancel/postpone propagates on `status_short` (PST→NS reverts, same `fixture_id`). | **LIVE — coded + scheduled.** `sports_fixtures_daily_repoll.py` (trigger `sports.fixtures.daily_repoll`) + Tier-1 `discovery` (6h, rolling `today−1..today+7`, `force_overwrite`). Manual: `launch-sfi-forward-poll.sh` is SFI-only. | **Covered, no gap.** Lifecycle = forward-determinable from the schedule + the daily re-poll captures cancel/postpone (`sports_fixtures_daily_repoll.py` docstring: "Today's fixtures get re-polled every fire so intra-day cancellation / postponement is captured").                                                                                                                                                                                                                 |
| **STANDINGS / LEAGUES / TEAMS** (api_football)                   | FORWARD / periodic              | STANDINGS weekly (Tier-1 6h refresh); LEAGUES/TEAMS season-boundary only (`window_condition: season_boundary`).                                                                      | **LIVE — coded + scheduled** (Tier-1 `discovery` + Tier-2 `reference`).                                                                                                                                                              | Covered, no gap.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **INJURIES** (api_football)                                      | FORWARD / daily                 | Daily refresh (Tier-2 `reference`, `run_always: true`, 24h).                                                                                                                         | **LIVE — coded + scheduled.**                                                                                                                                                                                                        | Covered, no gap.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **PRE_MATCH_ODDS snapshot** (footystats ODDS)                    | FORWARD / pre-match             | `data_available_at = KO−72h` (98% by T−24h, 100% by T−72h; 68 markets, opening odds).                                                                                                | **LIVE — coded.** `launch-footystats-forward-poll.sh` (rolling `today..today+14`, `--force-window`, `ENTITY=ODDS`); also Tier-3 `odds_t24h`→PREDICTIONS.                                                                             | Covered. FootyStats is a paid sub already in use; forward window is free of extra cost (same key).                                                                                                                                                                                                                                                                                                                                                                                    |
| **PREDICTIONS** (footystats model)                               | FORWARD / pre-match             | Pre-match model output; lands with the KO−72h..KO−24h snapshot window.                                                                                                               | **LIVE — coded** (Tier-3 `odds_t24h` + `launch-footystats-forward-poll.sh ENTITY=PREDICTIONS`).                                                                                                                                      | Covered, no gap (NB: never merge PREDICTIONS into ODDS — same-source label leakage, coverage-matrix §2.2).                                                                                                                                                                                                                                                                                                                                                                            |
| **LIVE_ODDS / odds_horizon_bucket** (odds_api)                   | FORWARD→intra-play / continuous | Moves continuously; bucketed 8 horizons T−24h/−12h/−6h/−4h/−2h/−1h/−10m/T−0; live poll **60s** interval.                                                                             | **LIVE — coded + RUNNING.** WS connector `odds_api_ws.py` (60s poll) + running VM `mtds-live-sports-odds-api-trades`. Tier-3 `odds_t24h/t6h/t1h` MTDS snapshots also fire.                                                           | **GAP (quota, not code):** The Odds API live polling at 60s × markets burns credits (~30 credits/call h2h+spreads+totals; ~43k/mo on Starter ~$10). Cheap alts for breadth/CLV: **api_football `/odds` (in-play), OddsAPI Starter tier already-sized, or scrape OddsPortal/Betfair Exchange public API**. Decision = which books + quota tier.                                                                                                                                        |
| **LINEUPS** (api_football)                                       | **FORWARD** / pre-match         | Confirmed lineups ~**KO−1h** (publication lag p95).                                                                                                                                  | **LIVE — coded + scheduled** (Tier-3 `odds_t1h` fires `--sports-entity LINEUPS`).                                                                                                                                                    | Covered, no gap.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **WEATHER forecast** (open_meteo)                                | **FORWARD** / pre-match         | Forecast point-in-time T−24h / T−12h / T−0 (per-fixture, venue coords). Match-day nowcast at KO−1h.                                                                                  | **LIVE — coded + scheduled.** `open_meteo.py` adapter uses the FREE `/v1/forecast` + Previous-Runs API for the T−24h/T−12h/T−0 horizons; Tier-3 `odds_t1h` fires `WEATHER` nowcast.                                                  | **Covered, no gap** — Open-Meteo **Forecast API is free, no key**, and is the canonical forward-weather source. (Historical reanalysis `WEATHER (actual)` lands T+24h via archive-api; that is the post-match leg, not the forward feed.)                                                                                                                                                                                                                                             |
| **SFI_PROGRESSIVE_STATS** (soccer_football_info)                 | LIVE→MATCH_END                  | Streams ~every 30s in-play; freeze-stamped at `match_end_time`; stabilises **FT+5min** (`SFI_DATA_LAG_P95_SECONDS=300`).                                                             | **LIVE — coded.** `launch-sfi-forward-poll.sh` (singleton, `VM_TASK=sports-forward-poll`); SFI_LEAGUES/STANDINGS weekly.                                                                                                             | Covered, no gap (low post-match lag — best fast post-match source).                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **FIXTURE_STATS / FIXTURE_EVENTS / PLAYER_STATS** (api_football) | **POST-match + lag**            | `report_time = FT + API_FOOTBALL_RESULT_LAG_P95 = FT+30min`. Tier-4 `stats_immediate` fires FT+30min.                                                                                | **LIVE — coded + scheduled** (Tier-4 `post_match.stats_immediate`).                                                                                                                                                                  | Covered, no gap. Inherently post-match (can't be forward); the lag is the floor.                                                                                                                                                                                                                                                                                                                                                                                                      |
| **XG** (understat)                                               | **POST-match + lag**            | Understat xG available **FT+2h** (`UNDERSTAT_DATA_LAG_P95_SECONDS=7200`); 5 leagues only (EPL/LaLiga/Bundesliga/SerieA/Ligue1). Tier-4 `stats_delayed` fires FT+24h.                 | **PARTIAL — scheduled via Tier-4 `stats_delayed` (XG), but NO dedicated understat forward/live launcher.** No `launch-understat-forward-poll.sh` exists (only backfill path).                                                        | **GAP (low):** Understat is scrape-only (no official API) + high latency (FT+2h) + 5 leagues. The Tier-4 `stats_delayed` XG trigger covers it on schedule, BUT for broader/faster forward xG use the **FootyStats pre-match xG (`xg_prematch_*`, already in PREDICTIONS) + api_football expected-goals fields**; understat stays the FT+2h enrichment. Add a `launch-understat-forward-poll.sh` for resilience.                                                                       |
| **PLAYER_VALUES / TRANSFERMARKT_LEAGUES** (transfermarkt)        | **PERIODIC** (transfer windows) | Changes ~weekly; only expected inside transfer windows (`is_transfer_window_open`); 55 leagues.                                                                                      | **GAP — NO forward poll.** Only `launch-transfermarkt-backfill-vm.sh` exists; Tier-2 `reference` fires `TRANSFERS` (api_football transfers) on `window_condition: transfer_window_open`, NOT transfermarkt PLAYER_VALUES.            | **GAP (medium):** Transfermarkt is **scrape-only** (no API; the 6.5h-hang incident 2026-06-22 was an unbounded HTTP scrape). Forward continuation options: (1) add a weekly **transfermarkt forward-poll launcher** gated on transfer-window (cheap — values move slowly); (2) cheap API alt = **api_football `/players` market-value-adjacent fields** or **FootyStats squad/value fields** for the features that need a fresh value; keep transfermarkt as the periodic enrichment. |
| **RESULTS / SETTLEMENT**                                         | POST-match + lag                | `FT + settlement_window`.                                                                                                                                                            | Derived from FIXTURES status + FIXTURE_STATS (Tier-4).                                                                                                                                                                               | Covered, no gap.                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

### Continuation gaps & recommended cheap sources (ranked)

1. **LIVE_ODDS quota (highest leverage for ML continuation)** — `odds_api_ws.py` is coded + the
   `mtds-live-sports-odds-api-trades` VM runs, but 60s polling burns The Odds API credits (~43k/mo on Starter).
   **Recommendation:** size the OddsAPI **Starter tier (~$10/mo, 50k credits)** for the live MVP league set; for
   breadth/CLV without extra spend add **api_football `/odds` (in-play, already-subscribed key)** as a second source.
   Repo: market-tick-data-service (connector tuning) + deployment-service (VM cadence). **BLOCKED-OPERATOR-DECISION**
   (which books + quota tier).
2. **Transfermarkt forward poll missing** — only a backfill launcher exists; scrape-only + slow-moving.
   **Recommendation:** add a weekly transfer-window-gated `launch-transfermarkt-forward-poll.sh` (cheap; values change
   ~weekly), AND wrap the scrape in `asyncio.wait_for` per-shard (the 6.5h-hang root cause). Cheap forward alt for the
   value feature: **api_football `/players` or FootyStats squad fields**. Repo: deployment-service +
   instruments-service.
3. **Understat dedicated forward poll missing** — Tier-4 `stats_delayed` covers XG on schedule (FT+24h), but no
   dedicated launcher + scrape-only + 5 leagues + FT+2h. **Recommendation:** for forward/fast xG use **FootyStats
   pre-match xG (`xg_prematch_*`) + api_football expected-goals** (both already live), keep understat as the FT+2h
   enrichment; add `launch-understat-forward-poll.sh` for resilience. Repo: deployment-service.
4. **WEATHER forward — already optimal, just confirm the free path stays primary** — Open-Meteo **Forecast API is free +
   keyless** (`/v1/forecast`); the adapter already uses it for T−24h/T−12h/T−0. No cheap-source swap needed;
   **covered**. (Action: ensure the live VM resolves the free forecast URL, not the `customer-api` paid host, when no
   key is set.)
5. **No structural gap on FIXTURES / LINEUPS / api_football post-match stats** — all forward-determinable or scheduled;
   lags are inherent floors, not feed gaps.

### Continuation-gap todos

- [x] ✅ [INFRA] P2. **Add `launch-transfermarkt-forward-poll.sh`** (deployment-service) — weekly, transfer-window-gated
      forward poll for PLAYER_VALUES / TRANSFERMARKT_LEAGUES (55 leagues) so values keep flowing forward (currently
      backfill-only). Wrap the scrape per-shard in `asyncio.wait_for(timeout=N)` to prevent the unbounded-HTTP hang
      (incident 2026-06-22). Repo: deployment-service (+ instruments-service if the trigger entity is missing).
      **NICE-TO-HAVE** — slow-moving data; api_football `/players` is the cheap forward fallback for the value feature
      meanwhile. — deployment-service@cc863de | QG green | launcher + vm_zombie_watchdog + launcher_registry all
      registered
- [x] ✅ [INFRA] P2. **Add `launch-understat-forward-poll.sh`** (deployment-service) — dedicated forward poll for
      understat XG (5 leagues) for resilience beyond the Tier-4 `stats_delayed` trigger; use FootyStats
      `xg_prematch_*` + api_football xG as the live/forward primary. Repo: deployment-service. —
      deployment-service@5758e97 | QG green | launcher + vm_zombie_watchdog + launcher_registry all registered
- [ ] [DATA] P2. **Live ODDS quota decision + cheap second source** (market-tick-data-service + deployment-service) —
      size The Odds API Starter (~$10/mo) for the live league set and/or wire **api_football `/odds` in-play** as a
      second forward odds source so LIVE_ODDS / odds_horizon_bucket keeps feeding CLV/steam features forward without
      exhausting credits. Repo: market-tick-data-service (connector) + deployment-service (VM cadence).
      **BLOCKED-OPERATOR-DECISION** (book set + quota tier).
- [x] ✅ [INFRA] P3. **Verify Open-Meteo forward weather uses the FREE forecast host on the live VM**
      (instruments-service) — confirm `open_meteo.py` resolves `https://api.open-meteo.com/v1/forecast` (keyless free)
      rather than the `customer-api.open-meteo.com` paid host when no key is configured, so forward weather stays
      zero-cost. Repo: instruments-service. **NICE-TO-HAVE**. **VERIFIED (2026-06-24):** Code trace confirms
      `OPEN_METEO` is explicitly exempt from API key requirements (`process_enrichment.py:58-60`);
      `_keys.get("open_meteo")` returns `None` (no SM secret exists for Open-Meteo — it's a free service);
      `OpenMeteoAdapter(api_key=None)` → host selection takes the `else` branch → `url = f"{_BASE_URL}/forecast"` =
      `https://api.open-meteo.com/v1/forecast` (FREE). ✅
- [x] ✅ [INFRA] P2. **Instrument the forward-poll/scheduler to capture per-fixture FIRST-PUBLISH lag → validate the
      `source_data_latency.py` p95 constants live** (instruments-service + deployment-service). The five constants (SFI
      300s · API-Football 1800s · FootyStats 3600s · Understat XG 7200s · Open-Meteo historical 3600s) are
      **UNVALIDATABLE FROM BACKFILL** — every captured `available_at` is either `match_end + constant` (circular) or the
      backfill wall-clock (days-to-weeks late). **SHIPPED (2026-06-22):** the `sports-scheduler` (the forward driver)
      now records `observed_publish_lag_s = first_fetch_utc − match_end` per (fixture, data_type, source) on each
      post-match trigger fire → `instruments-store-sports-prd/_index/latency_observations/day=<D>/<run>.parquet` (a
      DEDICATED file — **NEVER touches `available_at`**, leaving the circular arithmetic intact). Code:
      `deployment-service/deployment_service/sports_latency_observation.py` (`LatencyObservationRecorder` +
      `build_observations_for_fire` + `ENTITY_TO_OBSERVATION_TARGET` mapping post-match entities→source+assumed) wired
      into `sports_trigger_scheduler.py::fire_trigger`→`_record_latency_observations` (observes FIXTURE_STATS /
      FIXTURE_EVENTS / PLAYER_STATS → api_football, XG → understat, SFI_PROGRESSIVE_STATS → sfi). The aggregator
      `instruments-service/scripts/aggregate_source_latency_observations.py` reads the observation parquets → empirical
      p50/p95/max per source vs assumed (`--emit-constants` prints a ready-to-paste `source_data_latency.py` block,
      p95-ceil-to-minute, floored at assumed unless `--allow-lower`). — deployment-service@9a5387b (recorder + scheduler
      wire + 12 unit tests, QG-green --no-fix exit 0) + instruments-service@2fc4ac7 (aggregator). ±window base fetch
      launched + COMPLETED: `instr-backfill-sports-fixtures-20260622-135817` (FIXTURES 2026-06-15..2026-07-06, exit 0,
      33 new manifest entries). **Remaining = the ~2-week accrual + re-pin (split into the 3 todos below).** Provenance:
      Source-latency validation (2026-06-22) + Migration plan section below.

- [x] ✅ [DEPLOY] P2. **Wire the latency recorder onto the LIVE `sports-scheduler` VM + rebuild its tarball** — the
      recorder is `record_latency=True` by default in `SportsTriggerScheduler.__init__`, but the running
      `sports-scheduler-*` VM (`launch-sports-scheduler-vm.sh`) bakes deployment-service from a GCS tarball, so it keeps
      the pre-9a5387b code until a `create-code-tarballs.sh` rebuild from clean LDR + scheduler relaunch. Action:
      rebuild the deployment-service tarball, relaunch the long-lived sports-scheduler, T+10min-verify it fires
      post-match triggers AND writes ≥1 `_index/latency_observations/*.parquet` over the 36 in-season leagues. Repo:
      deployment-service. Provenance: Source-latency validation (2026-06-22). — deployment-service@01eaa94 (tarball
      confirmed contains 9a5387b latency recorder); `sports-scheduler-20260624-010804` (e2-small, asia-northeast1-c)
      launched 2026-06-24T01:08Z, RUNNING; `record_latency=True` is the default — latency parquet writes begin after
      first completed match trigger.
- [x] ✅ [INFRA] P3. **True first-SUCCESS (polling-retry) latency enhancement** — the shipped recorder stamps the
      first-ATTEMPT wall-clock (`fetched_rows=-1`, `first_success=False` sentinel — the scheduler dispatches async +
      does not see the fetch's row count), which the aggregator treats as a CEILING on the true publish lag. For a TIGHT
      first-success measurement, add a poll-until-non-empty path: from `match_end`, re-attempt each post-match
      (data_type, source) on a tightening cadence (e.g. 15-min for the first few hours, then hourly) until the source
      returns `rows>0`, and stamp the genuine first-success row (`first_success=True`, `fetched_rows=N`). The aggregator
      already filters via `--first-success-only`. Repo: deployment-service (scheduler) + instruments-service (the
      per-entity fetch must report its row count back to the scheduler, or the recorder reads the just-written manifest
      cell). **NICE-TO-HAVE** — the ceiling measurement is sufficient for a CONFIRM/TOO-LOW/TOO-HIGH verdict; this
      tightens it. Provenance: Source-latency validation (2026-06-22). — deployment-service@46ffbad (FirstSuccessPoller
      extracted to sports_latency_observation.py; scheduler ≤900 lines; QG green)
- [ ] [DATA] P2. **Re-pin `source_data_latency.py` from ≥2 weeks of empirical observations** (unified-api-contracts) —
      after the live scheduler has accrued ~2 weeks of `_index/latency_observations` over the open leagues, run
      `python3 instruments-service/scripts/aggregate_source_latency_observations.py --emit-constants` (add
      `--first-success-only` once the P3 enhancement lands), review the per-source p50/p95/max-vs-assumed verdict, and
      update the 5 constants in `unified-api-contracts/.../registry/source_data_latency.py` from REAL data (the
      constants feed `CanonicalFixture.report_time = match_end + lag`, a cross-repo contract → human-reviewed UAC edit,
      semver via the agent). NO historical-row migration needed: `available_at`/`report_time` on EXISTING captured rows
      are write-time stamps that don't retro-change; only NEW forward `report_time` derivation picks up the re-pinned
      constants (live=batch, one path). Then flip this + re-doc the Source-latency section as VALIDATED (not assumed).
      Repo: unified-api-contracts. Provenance: Migration plan section below.

## Source-latency validation (2026-06-22)

Empirical validation of the assumed-p95 lag constants in
`unified-api-contracts/unified_api_contracts/registry/source_data_latency.py` that feed
`CanonicalFixture.report_time = match_end + lag` (consumed at
`instruments-service/instruments_service/engine/orchestrator/sfi.py:354` → written into the per-row `available_at`).
Validated against the consolidated v9 `_index`
(`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 3.43M sports rows) +
per-entity post-match parquets under `sports_reference/by_date/`.

### Step 1 — leagues OPEN now (in-season on 2026-06-22)

Computed via `footystats_season_status_for_day()` over the 101-league `LEAGUE_REGISTRY` (returns `None` ⟺ in-season):
**36 of 101 leagues are in-season today.** The forward-validatable football set (where new completed matches land daily
right now): **MLS, USL_CHAMPIONSHIP, US_OPEN_CUP** (US); **BRASILEIRAO, BRASILEIRAO_SERIE_B, COPA_DO_BRASIL** (BR);
**ARGENTINA_PRIMERA, ARGENTINA_PRIMERA_NACIONAL, COPA_ARGENTINA, COPA_LIGA_PROFESIONAL** (AR); **CHILE_PRIMERA,
CHILE_PRIMERA_B, COPA_CHILE** (CL); **ALLSVENSKAN, SUPERETTAN** (SE); **ELITESERIEN, NORWAY_1_DIVISJON, NORWEGIAN_CUP**
(NO); **J1_LEAGUE, J2_LEAGUE, JLEAGUE_CUP, EMPEROR_CUP** (JP); **K_LEAGUE_1, K_LEAGUE_2, KOREAN_FA_CUP** (KR);
**AUSTRALIA_CUP** (AU); **COPA_LIBERTADORES, COPA_SUDAMERICANA** (continental). Non-football in-season: **MLB, NBA, NHL,
ATP, WTA**. (Caveat: **UCL/UEL/UECL** read "open" only because their `season_months=(9,6)` window includes June, but
they are in the post-final summer break — no fixtures. European top-tier domestic leagues (EPL/LaLiga/Serie
A/Bundesliga/Ligue 1) are all **off-season** today.)

### Step 2 — observed lag vs constant (per source)

**Critical caveat — what `available_at`/`written_at` actually measure here.** Both the manifest `written_at` and the
per-entity `available_at` reflect **OUR backfill write time, not the source's first-publish time** — proven two ways:

1. **Manifest `written_at` is backfill-batch-clustered, not per-fixture.** A single backfill run stamps thousands of
   rows with one identical timestamp regardless of when each match ended — e.g. **16,600** `api_football/FIXTURE_STATS`
   captured rows all share `written_at=2026-06-11 15:50:42Z`; 15,924 `FIXTURE_EVENTS` rows likewise. `fixture_id` is
   **null at index grain** (manifest rows are date×league, not per-match), so a per-fixture `written_at − match_end`
   join is impossible from the index.
2. **The per-entity `available_at` for the lag-derived sources is CIRCULAR.** SFI progressive-stats parquets
   (`pipeline_mode=batch_soccer_football_info/entity=progressive_stats/.../progressive_stats.parquet`, e.g.
   day=2026-04-20 EPL, 200 rows) carry `match_end_time=16:30:00Z`, `report_time=16:35:00Z`, `available_at=16:35:00Z` —
   i.e. `available_at = match_end + EXACTLY 300s = the constant itself`. Measuring `available_at − match_end` just
   recovers the assumed 300 and proves nothing. api_football `fixture_events` `available_at` is snapped to a round 5-min
   boundary on the match day (e.g. 2026-04-14 17:00:00Z, identical across rows). Open-Meteo weather `available_at` is
   the raw backfill wall-clock — e.g. a **2026-05-10** match's weather row has `available_at=2026-06-22 02:15:29Z` (a
   backfill **43 days later**, identical across all rows in the file).

| Source / data_type                  | Assumed-p95 constant | Observed from backfill `available_at`/`written_at`                                                           | Verdict                                                            | Sample (captured rows) |
| ----------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ | ---------------------- |
| `sfi` SFI_PROGRESSIVE_STATS         | 300 s (5 min)        | `available_at = match_end + 300s` (constant written in)                                                      | **UNVALIDATABLE-FROM-BACKFILL** (circular — recovers the constant) | 639                    |
| `api_football` FIXTURE_STATS/EVENTS | 1800 s (30 min)      | `available_at` snapped to match-day 5-min boundary; `written_at` = one backfill batch (16,600 rows @ one ts) | **UNVALIDATABLE-FROM-BACKFILL**                                    | 36,184 / 31,836        |
| `footystats` MATCHES                | 3600 s (1 h)         | `written_at` = backfill batch clusters (484 distinct minutes over 30k rows)                                  | **UNVALIDATABLE-FROM-BACKFILL**                                    | 30,128                 |
| `understat` XG                      | 7200 s (2 h)         | `written_at` = backfill batch clusters (top cluster 92 rows @ one ts)                                        | **UNVALIDATABLE-FROM-BACKFILL**                                    | 5,619                  |
| `open_meteo` WEATHER (historical)   | 3600 s (1 h)         | `available_at` = backfill wall-clock, up to 43 days post-match                                               | **UNVALIDATABLE-FROM-BACKFILL**                                    | 13,963                 |

**Verdict: all five constants are UNVALIDATABLE FROM BACKFILL DATA.** None can be confirmed or refuted from what GCS
holds today, because no captured sports cell carries a real source-first-publish timestamp — every `available_at` is
either the lag-constant arithmetic (`match_end + lag`, circular) or the backfill write wall-clock (days-to-weeks late).
The constants are NOT changed (no evidence justifies a change in either direction). They remain plausible as
order-of-magnitude assumptions (SFI is a live in-play feed → ~minutes is reasonable; understat xG genuinely posts ~hours
after FT; api-football/footystats post-match stats within ~tens-of-minutes-to-an-hour), but "assumed" must NOT be
re-labelled "validated" until a live-poll capture proves them.

### Step 3 — how to validate LIVE (the only path that proves source-publish lag)

The proof requires instrumenting the **forward/live path** to record, per fixture, the **wall-clock time of the FIRST
successful fetch** of each post-match data_type and differencing it against that fixture's real `match_end_time`. The 36
in-season leagues above (esp. MLS / Brasileirão / Argentina / J-League / K-League — matches land daily right now) are
where this is capturable immediately. Todo filed below.

### Step 4 — SHIPPED instrumentation (2026-06-22) — the empirical-latency mechanism

The forward-path instrumentation is now LIVE in code (deployment-service@9a5387b + instruments-service@2fc4ac7):

- **WHERE the lag is observed:** the long-lived `sports-scheduler` (`SportsTriggerScheduler`, the existing forward
  driver) fires post-match triggers at `match_end + offset` (`match_end = kickoff + 105 min` estimate,
  `MATCH_END_OFFSET_MIN`). On the FIRST fire of a `(trigger_name, fixture_id)` (`mark_fired` dedupes → first fire =
  first attempt), after a successful dispatch,
  `fire_trigger`→`_record_latency_observations`→`build_observations_for_fire` emits one observation per OBSERVABLE
  post-match entity (`ENTITY_TO_OBSERVATION_TARGET`: FIXTURE_STATS/FIXTURE_EVENTS/PLAYER_STATS→api_football,
  XG→understat, SFI_PROGRESSIVE_STATS→sfi).
- **WHAT lands (`observed_publish_lag_s`):** a per-(fixture, data_type, source) row with
  `observed_publish_lag_s = first_fetch_utc − match_end_utc`, `fetched_rows`, `first_success`, `trigger_name`, the
  `assumed_lag_constant_s` (yardstick), `recorded_at_utc`. **GCS location:**
  `gs://instruments-store-sports-prd-<pid>/_index/latency_observations/day=<YYYY-MM-DD>/<run_tag>.parquet` — a DEDICATED
  observation file (hive-partitioned by match-day, per-run shard via `run_tag` for multi-scheduler isolation). Written
  via UTL cloud-agnostic `get_storage_client().upload_bytes`; **NEVER overwrites `available_at`** (the circular
  `available_at = match_end + constant` arithmetic stays intact — the observation is a sibling truth source).
- **First-ATTEMPT vs first-SUCCESS:** the shipped recorder stamps the first-ATTEMPT wall-clock (sentinel
  `fetched_rows=-1`, `first_success=False`) because the scheduler dispatches asynchronously and doesn't see the fetch's
  row count. The aggregator treats this as a **CEILING** on the true publish lag (the source HAD published by
  `first_fetch_utc`) — sufficient for a CONFIRM/TOO-LOW/TOO-HIGH verdict. The P3 polling-retry todo tightens it to a
  genuine first-success (poll-until-`rows>0`, stamp `first_success=True`).

### Migration plan — re-pinning `source_data_latency.py` from real data (after ~2-week accrual)

1. **Accrue** (~1–2 weeks): the live `sports-scheduler` (after the P2 tarball-rebuild todo lands the recorder on the VM)
   writes `_index/latency_observations/day=*/*.parquet` daily as matches complete in the 36 open leagues. Progress
   metric = observation row count climbing per source (flat across days for a source = that source's post-match trigger
   isn't firing → diagnose, don't wait).
2. **Aggregate:**
   `python3 instruments-service/scripts/aggregate_source_latency_observations.py [--first-success-only] [--emit-constants]`
   → prints per-source `n / p50 / p95 / max / assumed / verdict` and (with `--emit-constants`) a ready-to-paste constant
   block (p95 ceil-to-minute, floored at the current assumed unless `--allow-lower` — fail-safe: an under-sampled window
   must never LOWER a lag floor and risk a too-early read). `--min-samples` (default 20) gates the recompute so a thin
   window reads UNDER-SAMPLED, not a spurious re-pin.
3. **Re-pin (human-reviewed UAC edit):** update the 5 `Final[int]` constants in
   `unified-api-contracts/unified_api_contracts/registry/source_data_latency.py` from the observed p95. These feed
   `CanonicalFixture.report_time = match_end + lag` (a cross-repo contract consumed at
   `instruments-service/.../engine/orchestrator/sfi.py`) → semver-agent handles the bump; ship via quickmerge.
4. **Historical rows — NO one-walk migration needed.** `available_at`/`report_time` on EXISTING captured parquets are
   write-time stamps that do not retro-change when the constant moves; only NEW forward `report_time` derivation picks
   up the re-pinned value (live=batch, one code path). (A future operator decision to recompute historical `report_time`
   for the affected sources would be its own bounded single-walk over the sports corpus — out of scope.)
5. **Re-doc:** flip the P2 re-pin todo + re-label this section's Step-2 verdict table from UNVALIDATABLE-FROM-BACKFILL
   to the empirical VALIDATED verdict, citing the observation sample size per source.
