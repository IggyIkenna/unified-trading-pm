# deployment-api + deployment-ui — Playwright MCP Audit Checklist

**Purpose.** Hand this to a fresh Playwright MCP agent to validate the deployment-api / deployment-ui observability
stack end-to-end. Every item is a PASS/FAIL assertion — the agent should click, read, capture screenshots, and record a
verdict per row.

**Date of this spec:** 2026-04-19 **Covers commits through:** deployment-api `959bdab` (DeFi legacy allowlist),
deployment-ui `ed2d198` (rate-metric row guard), deployment-api data-status drill-down endpoints (`/schema`,
`/instruments-for-shard`, `/bucket-counts`, `/download-csv`).

---

## 0. Preflight — start the stack

| #   | Action                                                                                   | Expected                                                                                                                               |
| --- | ---------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 0.1 | `cd deployment-api && uvicorn deployment_api.main:app --port 8004`                       | server binds to 8004, `GET /health` → 200                                                                                              |
| 0.2 | `cd deployment-ui && npm run dev`                                                        | vite serves on 5183 (port registry SSOT: `unified-trading-pm/scripts/dev/ui-api-mapping.json`; `vite.config.ts` is `strictPort: true`) |
| 0.3 | Browser → `http://localhost:5183`                                                        | UI loads. Tab list at top: **Overview** / **Epics**                                                                                    |
| 0.4 | Click any service in the left rail                                                       | Per-service tab strip appears: **Deploy / Status / History / Builds / Data Status / Readiness / Config**                               |
| 0.5 | `curl -s http://localhost:8004/api/data-status/turbo/stats \| jq '.turbo_cache.entries'` | integer ≥ 0                                                                                                                            |
| 0.6 | `curl -X POST http://localhost:8004/api/data-status/turbo/clear` → re-hit `stats`        | `turbo_cache.entries = 0` post-clear                                                                                                   |

If 0.1–0.4 fail, **halt the audit** — UI cannot render without backing API.

---

## 1. Top-level expectations (every service tab)

Before drilling into per-service specifics, verify the **common shell** is present on the Data Status tab for every
service listed in `TURBO_MODE_SERVICES` (`src/api/client.ts:1043`):

- instruments-service
- market-tick-data-handler _(tick ingester)_
- market-tick-data-service _(canonical tick storage)_
- market-data-processing-service _(MDPS — processed candles)_
- features-delta-one-service, features-onchain-service, features-volatility-service, features-calendar-service,
  features-sports-service, features-multi-timeframe-service, features-cross-instrument-service,
  features-commodity-service

### 1.1 Layout assertions (per service × `/data-status`)

| #    | Expected DOM element                                                    | How to verify                                                                                                                                              |
| ---- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1.1a | **Overall coverage %** card at top                                      | Single number, 0–100, never > 100. If rendered > 100 it is a regression (see §5 bug registry)                                                              |
| 1.1b | **Per-category breakdown** (CEFI / TRADFI / DEFI / SPORTS / PREDICTION) | Each shows `numerator/denominator shards` + percentage + progress bar                                                                                      |
| 1.1c | **Date range selector** (start / end, defaults sensible)                | Defaults to `today − 30d → today`. Operator must set an explicit earlier start to go back further (e.g. `2018-03-20` for full instruments-service history) |
| 1.1d | **Check Status** button with cache-bust                                 | Triggers `GET /api/data-status/turbo?service=<svc>&...&force=true`                                                                                         |
| 1.1e | **Clear cache** button (admin)                                          | Triggers `POST /api/data-status/turbo/clear`; toast confirms                                                                                               |
| 1.1f | **Sub-dimension accordion** under each category                         | Expands to show venue / instrument_type / data_type rows                                                                                                   |

### 1.2 Rate-metric row rendering guard (UI fix `ed2d198`)

For rows where `numerator > denominator × 1.1` (e.g. event/row counts — many rows per day), the UI MUST NOT show 100% or
a green bar. Instead:

| #    | Row                                        | Expected render                                                                               |
| ---- | ------------------------------------------ | --------------------------------------------------------------------------------------------- |
| 1.2a | Sports `FIXTURE_EVENTS 14098/1583`         | Label `14,098 rows / 1583 days`, right column `9/day`, **muted striped mini-bar** (not green) |
| 1.2b | Sports `SFI_PROGRESSIVE_STATS 2116865/335` | `6,319/day`                                                                                   |
| 1.2c | Sports `FIXTURES 1583/1583`                | Normal 100% green bar (coverage row, not rate row)                                            |
| 1.2d | Sports `SFI_STANDINGS 0/335`               | Normal 0% empty bar                                                                           |

Failure mode to watch for: any rate row showing `100%` is stale UI bundle — verify `formatRatePerDay` +
`isRateMetricRow` imported from `src/lib/utils.ts`.

### 1.3 Category-level completion sanity

Run
`curl -s "http://localhost:8004/api/data-status/turbo?service=instruments-service&start_date=2018-03-20&end_date=2026-04-18&force=true" | jq '.per_category[] | {category, completion_pct, shards}'`.

Record and compare against UI table:

| Category   | Expected (post-DeFi-alias-fix 2026-04-19)      | FAIL threshold  |
| ---------- | ---------------------------------------------- | --------------- |
| CEFI       | ~99.5%                                         | < 95% or > 100% |
| TRADFI     | ~99.7%                                         | < 95% or > 100% |
| DEFI       | ~97.2%                                         | < 90% or > 100% |
| SPORTS     | 100.0%                                         | < 98% or > 100% |
| PREDICTION | ~94% (rising as Polymarket re-shard completes) | < 80% or > 100% |

If DEFI renders ~40% the legacy-venue alias filter is not loaded — reload backend.

---

## 2. Tab-specific expectations

### 2.A — Instruments Service (`instruments-service`)

This is the **reference-data** service. It owns instrument definitions per day per venue across all 5 categories.

#### 2.A.1 Coverage structure

| #       | Expectation                                                                                                                                                                                                               |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.A.1a  | All 5 categories appear (no category missing)                                                                                                                                                                             |
| 2.A.1b  | DEFI sub-rows: canonical venues only — `UNISWAP_V2`, `UNISWAP_V3`, `UNISWAP_V4`, `CURVE`, `BALANCER`, `AAVE_V3`. **NO** legacy aliases like `AAVEV3-ETHEREUM`, `UNISWAPV3-BASE` (filter landed in `22f0024`/`959bdab`)    |
| 2.A.1b2 | **Venues summary widget (top-of-tab)** must ALSO not leak `AAVEV3-{chain}` aliases — check this separately from the per-shard rollup, as the two surfaces derive from different projections and can regress independently |
| 2.A.1c  | DEFI rows carry a `chain` dimension (ETHEREUM / ARBITRUM / OPTIMISM / POLYGON / BASE / AVALANCHE) visible in drill-down                                                                                                   |
| 2.A.1d  | PREDICTION sub-rows: `POLYMARKET` venue; drill-down shows 6-dim sharding `market_category × underlying × market_type × resolution_period`                                                                                 |
| 2.A.1e  | SPORTS sub-rows: sports*reference data types (`MATCHES`, `LEAGUES`, `FIXTURES`, `FIXTURE_EVENTS`, `SFI*\*`, `STANDINGS`, `ODDS`, `PREDICTIONS`, `PLAYER_STATS`, `PLAYER_VALUES`, `INJURIES`)                              |
| 2.A.1f  | CEFI / TRADFI rows carry `instrument_type` dimension (SPOT, PERPETUAL, FUTURE, OPTION, FUTURE_SPREAD, OPTION_COMBO, etc.)                                                                                                 |

#### 2.A.2 Drill-down (click a coverage row → day → instrument list)

| #      | Expectation                                                                                                                                                |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.A.2a | Clicking a **green (available) day pill** opens `InstrumentsModal`                                                                                         |
| 2.A.2b | Modal fetches `GET /api/data-status/instruments-for-shard?service=instruments-service&category=<>&venue=<>&day=YYYY-MM-DD&instrument_type=<>&data_type=<>` |
| 2.A.2c | Returns a list of `instrument_id` strings (raw, not hashed)                                                                                                |
| 2.A.2d | List is searchable + paginated (post UX-refinement `af63bfb`) — large venues like `BINANCE SPOT` return 10k+ rows without crashing the modal               |
| 2.A.2e | **Full-CSV button** (UX refinement) — `GET /api/data-status/download-csv?...` streams a CSV of all instruments for the day                                 |
| 2.A.2f | Empty-day click → modal shows "No instruments recorded for this shard" (no 500)                                                                            |

#### 2.A.3 Schema popup

| #      | Expectation                                                                                                            |
| ------ | ---------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| 2.A.3a | Each data-type row has a **Schema** icon button                                                                        |
| 2.A.3b | Click → `GET /api/data-status/schema?service=instruments-service&category=<>&instrument_type=<>&data_type=<>&venue=<>` |
| 2.A.3c | Response contains: `source` (e.g. `uac:CONTRACT_REGISTRY`), `registered: true                                          | false`, `columns: [{name, dtype, nullable, description}]`, optional `symbol_column` |
| 2.A.3d | For `UNISWAP_V4` pools the schema shows `pool_id` (not `pool_address`) as `symbol_column`                              |
| 2.A.3e | For `UNISWAP_V3` pools the schema shows `pool_address`                                                                 |
| 2.A.3f | Unregistered shard → modal shows yellow warning `"No contract registered — the UI will project raw parquet columns."`  |

#### 2.A.4 Bucket count badge

| #      | Expectation                                                                                              |
| ------ | -------------------------------------------------------------------------------------------------------- |
| 2.A.4a | Each venue row carries a small bucket-count badge                                                        |
| 2.A.4b | Badge sources from `GET /api/data-status/bucket-counts?service=instruments-service&category=<>&venue=<>` |
| 2.A.4c | Shows `<n> files / <m> MB` or similar; tooltip on hover explains it is the GCS object count              |

---

### 2.B — Tick Data (`market-tick-data-service` + `market-tick-data-handler`)

**market-tick-data-handler** is the live ingester (raw_tick_data). **market-tick-data-service** owns canonical tick
storage.

Validate BOTH appear in the service rail and BOTH have Data Status tabs.

#### 2.B.1 Coverage

| #      | Expectation                                                                                                                                              |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.B.1a | CEFI category dominant (Binance / OKX / Bybit / Hyperliquid / Deribit / Coinbase / CBOE pricing-only)                                                    |
| 2.B.1b | TRADFI category present (IBKR / CME / ICE via Databento)                                                                                                 |
| 2.B.1c | DEFI category has **chain** shard (not venue-only)                                                                                                       |
| 2.B.1d | SPORTS tick data (odds-api) has `ODDS_API` venue — **NOTE current gap**: last write 2026-04-14, 54-day hole Feb 22→Apr 13 visible as red band in heatmap |
| 2.B.1e | Data-type dimension visible: `trades`, `book_snapshot_5`, `book_ticker`, `quotes`, etc.                                                                  |
| 2.B.1f | `instrument_type` dimension visible under CEFI/TRADFI: SPOT / PERPETUAL / FUTURE / OPTION / COMBO                                                        |

#### 2.B.2 Drill-down — options & combos

| #      | Expectation                                                                                                             |
| ------ | ----------------------------------------------------------------------------------------------------------------------- |
| 2.B.2a | Clicking a day pill on **OPTION / OPTION_COMBO / FUTURE_SPREAD** venue rows opens `InstrumentsModal` in **bundle mode** |
| 2.B.2b | Bundle mode renders as a collapsed header per instrument: `instrument_id` + number of bundled components                |
| 2.B.2c | Expanding a combo shows leg table: `leg_instrument_id`, `leg_side`, `leg_ratio_qty`, `leg_strike`                       |
| 2.B.2d | `leg_ratio_qty` values make sense: butterfly 1/-2/1, calendar ±1, iron condor ±1/±1                                     |
| 2.B.2e | **Single-click bundle download** (UX refinement) — one button downloads all legs as a CSV                               |

#### 2.B.3 Heatmap calendar

| #      | Expectation                                                                                                                                                                                                                                                                                              |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2.B.3a | `HeatmapCalendar` renders one cell per day in range                                                                                                                                                                                                                                                      |
| 2.B.3b | Green = captured, grey hatch = empty_confirmed, red diagonal hash = attempted_failed, solid red = missing (not attempted), grey = pre-launch                                                                                                                                                             |
| 2.B.3c | Hovering a day shows tooltip `YYYY-MM-DD — <n>/<m> shards`                                                                                                                                                                                                                                               |
| 2.B.3d | Pre-launch days (before `expected_start_dates.yaml` category_start) render **grey** and are **not counted** in the denominator                                                                                                                                                                           |
| 2.B.3e | **Phase C — honest-coverage:** every cell renders exactly ONE of the 4 states: `captured` / `empty_confirmed` / `attempted_failed` / `missing` (plus the structural `future` / `no_expectation`). No "unknown" state is permitted. Cell's `data-status` attribute MUST be one of these values.           |
| 2.B.3f | **Phase C — legend 4-state:** legend renders all four honest-coverage chips with `data-legend-state` attributes (`captured`, `empty_confirmed`, `attempted_failed`, `missing`). `attempted_failed` uses a red diagonal hash so it is visually distinct from solid red `missing` even in monochrome mode. |
| 2.B.3g | **Phase C — failed aria-label:** clicking or keyboard-focusing an `attempted_failed` cell, the `aria-label` attribute MUST contain the classified error code from `error_reason` (e.g. `RATE_LIMIT_HIT`, `GRAPH_API_ERROR`).                                                                             |

---

### 2.C — Market Data Processing (`market-data-processing-service`)

MDPS consumes `market-tick-data-service` output and produces processed candles. It is an **upstream-dependent** service
(`UPSTREAM_CHECK_SERVICES` includes MDPS).

#### 2.C.1 Upstream-aware coverage

| #      | Expectation                                                                                                 |
| ------ | ----------------------------------------------------------------------------------------------------------- |
| 2.C.1a | The denominator for each MDPS shard is clamped to the set of days where tick data actually exists upstream  |
| 2.C.1b | UI shows an **info banner** / tooltip: `"Missing calculated against market-tick-data-service availability"` |
| 2.C.1c | Days with no upstream tick data render **grey** (pre-upstream) not red (missing)                            |
| 2.C.1d | Clicking a red day invites `Deploy` action and pre-fills the date in the Deploy tab                         |

#### 2.C.2 Coverage dimensions

| #      | Expectation                                                            |
| ------ | ---------------------------------------------------------------------- |
| 2.C.2a | `timeframe` dimension visible (1m, 5m, 15m, 1h, 4h, 1d)                |
| 2.C.2b | Per-venue × per-instrument_type × per-timeframe breakdown              |
| 2.C.2c | Same canonical venues as tick-data (no legacy aliases)                 |
| 2.C.2d | Category breakdown: CEFI / TRADFI / DEFI only (no SPORTS / PREDICTION) |

#### 2.C.3 Schema popup

| #      | Expectation                                                                                                                                                                                                                                |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2.C.3a | Processed-candle schema columns: `ts`, `instrument_id`, `open`, `high`, `low`, `close`, `volume`, `n_trades`, `vwap` (exact list comes from CONTRACT_REGISTRY — agent MUST capture and compare to `SchemaContract` for `PROCESSED_CANDLE`) |
| 2.C.3b | Optional columns for DEFI: `pool_address` or `pool_id`                                                                                                                                                                                     |

---

### 2.D — Market Data (collective / features) — remaining `TURBO_MODE_SERVICES`

**Agent must load each of these tabs and run the generic §1 checks:**

- features-delta-one-service _(upstream-dependent)_
- features-onchain-service
- features-volatility-service
- features-calendar-service
- features-sports-service
- features-multi-timeframe-service
- features-cross-instrument-service
- features-commodity-service

#### 2.D.1 Shard-dimension expectations by service

| Service                           | Primary shard dimensions (should be visible in drill-down) |
| --------------------------------- | ---------------------------------------------------------- |
| features-delta-one-service        | venue × instrument_type × timeframe × feature_group        |
| features-onchain-service          | chain × protocol × feature_group × timeframe               |
| features-volatility-service       | venue × instrument_type × timeframe × feature_group        |
| features-calendar-service         | category × feature_group (date-only)                       |
| features-sports-service           | league_id × feature_group                                  |
| features-multi-timeframe-service  | venue × instrument_type × timeframe-pair × feature_group   |
| features-cross-instrument-service | venue × instrument_pair × feature_group                    |
| features-commodity-service        | venue × instrument_type × feature_group                    |

#### 2.D.2 Schema contract coverage

For each features service, clicking the schema icon must:

| #      | Expectation                                                                         |
| ------ | ----------------------------------------------------------------------------------- |
| 2.D.2a | Return `registered: true` for the canonical feature_group                           |
| 2.D.2b | Columns include `ts`, `instrument_id` or `league_id`, plus feature-specific columns |
| 2.D.2c | `source` field references the schema SSOT (e.g. `uac:FEATURE_GROUPS`)               |

---

## 3. VM Deployments view (`/vm-deployments`)

The Pub/Sub event pipeline is the other half of observability. These rows are populated by the `deployment-events`
topic, written by VM-side `deployment_heartbeat.py`.

| #   | Expectation                                                                                                                                                                                                                                                                          |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 3.1 | Table lists active + recent VMs with columns: `deployment_id`, `vm_name`, `category`, `task`, `mode`, `status`, `rows_in`, `rows_out`, `rows_error`, `events_emitted`, `exit_code`, `started_at`, `last_heartbeat_at`, `log_uri`                                                     |
| 3.2 | **Status** column shows `running`, `completed`, or `failed` — never stuck on `pending`                                                                                                                                                                                               |
| 3.3 | Clicking a row opens `VmDeploymentDetails` with a live event stream                                                                                                                                                                                                                  |
| 3.4 | Detail page shows the lifecycle events in order: `DEPLOYMENT_STARTED` → N × `DEPLOYMENT_PROGRESS` → `DEPLOYMENT_COMPLETED` or `DEPLOYMENT_FAILED`                                                                                                                                    |
| 3.5 | `rows_in` / `rows_out` counters are non-decreasing across PROGRESS events                                                                                                                                                                                                            |
| 3.6 | `log_uri` is a clickable `gs://` link that opens the GCS console in a new tab                                                                                                                                                                                                        |
| 3.7 | If no active VMs, page renders "No active deployments" placeholder (not an error)                                                                                                                                                                                                    |
| 3.8 | Every active VM's `category` column must be a real category (`CEFI` / `TRADFI` / `DEFI` / `SPORTS` / `PREDICTION`), **never `UNKNOWN`**. An `UNKNOWN` value indicates the launcher dropped the `--category` arg or the deployment-events emitter stripped it — both are regressions. |

---

## 4. Deploy-trigger tab per service (smoke only)

Not the primary focus, but agent should confirm:

| #   | Expectation                                                                                                                                                                                |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 4.1 | `Deploy` tab shows a form with: service (pre-filled), operation, category multi-select, venue multi-select (filtered by category), start_date, end_date, mode (batch/live), dry_run toggle |
| 4.2 | Submitting with `dry_run=true` does NOT launch a VM — it returns the CLI preview modal                                                                                                     |
| 4.3 | CLI preview shows the exact `bash launch-*.sh` command that would run                                                                                                                      |
| 4.4 | Operating on a service that requires upstream data (MDPS, features-delta-one) warns if upstream coverage is incomplete for the requested range                                             |

---

## 5. Regression registry — known bugs agent MUST re-verify as fixed

Each row was a confirmed defect at some point in the last two weeks. Agent must actively try to reproduce and mark each
as ✅ fixed or ❌ regressed.

| #   | Bug                                                                                                        | Fix commit                           | How to re-test                                                                                                               |
| --- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| 5.1 | Data Status showed 100% for pre-launch DeFi dates (2018 counted)                                           | deployment-api `47df3f8`             | Instruments-service DEFI with start 2018-01-01 — should NOT be 100% artificially; should respect `expected_start_dates.yaml` |
| 5.2 | Completion % was date-based not shards-weighted → PREDICTION false 100%                                    | deployment-api `fc420cf`             | Prediction row should show real shards numerator/denominator, not 1.0                                                        |
| 5.3 | DEFI showed 40% because legacy-format venue aliases duplicated canonical rows                              | deployment-api `22f0024` + `959bdab` | DEFI on instruments-service should show ~97%, not 40%                                                                        |
| 5.4 | Rate-metric rows (events/day) rendered 100% green bar                                                      | deployment-ui `ed2d198`              | Sports `FIXTURE_EVENTS` row — see §1.2                                                                                       |
| 5.5 | Uniswap schema popup returned `symbol_column=symbol` for all Uniswap venues (override module not imported) | UAC `7a17536`                        | `UNISWAP_V3` schema should show `symbol_column=pool_address`, `UNISWAP_V4` should show `pool_id`                             |
| 5.6 | Polymarket shard denominator `2806/401` mixed shard numerator with date denominator                        | same as 5.2                          | Prediction Polymarket row should show `X shards / Y shards` consistent units                                                 |

---

## 5b. Phase C — honest-coverage assertions (4-state + filter + retry)

Every row is a new expectation introduced by the `honest_coverage_metrics_2026_04_19` plan (Phase C). Agent MUST assert
each item explicitly; missing or incorrect = ❌ regressed.

| #    | Expectation                                                                                                                                                                                                                                                                                                                                                                                                    |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 5b.1 | **Heatmap 4-state coverage:** every cell in any heatmap view renders exactly one of `{captured, empty_confirmed, attempted_failed, missing, future, no_expectation}`. No `unknown` state is permitted. Verified by reading `data-status` on each `[data-testid^="heatmap-day-"]`.                                                                                                                              |
| 5b.2 | **Event-driven rows (PREDICTION + SPORTS):** show `"X% attempted · Y% captured (Z% empty)"` via `formatEventDrivenCoverageLabel`, not a single percentage. Verified via `[data-testid="event-driven-label-PREDICTION"]` text content.                                                                                                                                                                          |
| 5b.3 | **Dense rows (CEFI / TRADFI / DEFI):** stay as a single percentage bar (no attempt/capture split). No regression of 2.B.3 layout.                                                                                                                                                                                                                                                                              |
| 5b.4 | **Show only failures toggle:** the `[data-testid="show-only-failures-toggle"]` checkbox above the Category Breakdown card narrows the visible categories to those with `failure_rate > 0` when checked ON, restores on OFF. Preference persists in `localStorage['deployment-ui/show-only-failures']` (value `"1"` when on, `"0"` when off).                                                                   |
| 5b.5 | **Drill-down shows capture_status badge:** clicking an `attempted_failed` day opens InstrumentsModal; each `[data-testid="shard-row-<id>"]` row carries a `[data-testid^="capture-status-badge-"]` badge whose `data-capture-status` matches the manifest row. The badge tooltip exposes `error_reason` text.                                                                                                  |
| 5b.6 | **Retry button on failed rows:** for every shard row with `data-capture-status="attempted_failed"` a `[data-testid^="retry-shard-button-"]` button is rendered. Clicking fires a confirm() dialog; on accept, a `POST /deployments/deploy-missing` call is made with `force=true` + `start_date == end_date == day` + the correct service/category/venue in the body. Verified via `browser_network_requests`. |
| 5b.7 | **Retry action fails loud:** if the POST returns non-2xx the button flips to `Retry failed` and `data-retry-status="err"`. If 2xx, flips to `Retried ✓` and `data-retry-status="ok"`.                                                                                                                                                                                                                          |
| 5b.8 | **API surfaces capture_status_counts:** `/data-status/manifest` (and `/turbo`) response carries `capture_status_counts: {captured, empty_confirmed, attempted_failed}` per category and per venue, and a top-level `failure_rate_by_dimension` map keyed by venue containing `{failure_rate, attempted_failed_count}`. Verified by capturing the network response.                                             |
| 5b.9 | **Drill-down endpoint surfaces capture metadata:** `/data-status/instruments-for-shard` response carries `capture_status`, `error_reason`, `attempted_at` on every item in `instruments[]`. Legacy manifest rows (no v5 column) coerce to `capture_status: "captured"` + empty `error_reason`/`attempted_at`. Verified by calling the endpoint for a known-post-Phase-B shard.                                 |

Each row above maps to concrete DOM selectors / network assertions so the Playwright agent does not have to guess.

---

## 6. Observability — Pub/Sub event stream (out-of-band sanity)

These are NOT UI assertions but the agent should run them as confidence checks for the VM tab:

```bash
gcloud pubsub subscriptions pull deployment-events-sub-live-debug-001204 \
  --project=central-element-323112 --limit=5 --auto-ack --format=json | jq '.[] | {event_name: .message.attributes.event_name, deployment_id: .message.attributes.deployment_id}'
```

Expected: recent `DEPLOYMENT_STARTED` / `DEPLOYMENT_PROGRESS` / `DEPLOYMENT_COMPLETED` events from active or
recently-finished VMs. If zero events in last 24h while VMs are active → observability broken (likely `PubSubEventSink`
construction regression in `deployment_heartbeat.py` or IAM `pubsub.publisher` on compute-default SA).

---

## 7. Error + empty states

Agent must trigger each of these and verify graceful handling:

| #   | Trigger                                                                          | Expected                                                                   |
| --- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| 7.1 | Date range with `start > end`                                                    | UI shows validation error, does NOT call API                               |
| 7.2 | Service not in any list (typo in URL)                                            | Page shows "Unknown service" placeholder                                   |
| 7.3 | API unreachable (stop uvicorn)                                                   | All data fetches show "failed to connect" toast, UI does NOT crash         |
| 7.4 | API returns 500 on `/turbo`                                                      | Data Status tab shows inline error with retry button                       |
| 7.5 | Category with zero expected shards (e.g. PREDICTION on market-tick-data-handler) | Category row is omitted or shows "N/A", NOT 0/0 = 100%                     |
| 7.6 | Click on pre-launch grey day                                                     | InstrumentsModal shows "Date is before category launch — no data expected" |

---

## 8. Delivery format for the Playwright agent

Return a single markdown report with:

1. **Executive summary table** — every `§N.X` row marked ✅ / ❌ / ⚠️ (partial) / ⏭ (skipped, with reason).
2. **Screenshots** (one per failing row, saved to `playwright-artifacts/`).
3. **Raw API responses** for any row where UI vs API disagreed — include the `curl` command, status code, and response
   body snippet.
4. **Regression alerts** — if ANY §5 bug reproduces, flag at top of report with red banner.
5. **Recommendations** — grouped by repo (`deployment-ui` / `deployment-api` / `unified-api-contracts` /
   `deployment-service`).

---

## Appendix A — Service × category matrix

| Service                           | CEFI | TRADFI | DEFI | SPORTS        | PREDICTION                     |
| --------------------------------- | ---- | ------ | ---- | ------------- | ------------------------------ |
| instruments-service               | ✅   | ✅     | ✅   | ✅            | ✅                             |
| market-tick-data-handler          | ✅   | ✅     | ✅   | ✅ (odds-api) | ⚠ (Polymarket when CLOB-live) |
| market-tick-data-service          | ✅   | ✅     | ✅   | ✅            | ✅                             |
| market-data-processing-service    | ✅   | ✅     | ✅   | —             | —                              |
| features-delta-one-service        | ✅   | ✅     | ✅   | —             | —                              |
| features-onchain-service          | —    | —      | ✅   | —             | —                              |
| features-sports-service           | —    | —      | —    | ✅            | —                              |
| features-volatility-service       | ✅   | ✅     | ✅   | —             | —                              |
| features-calendar-service         | ✅   | ✅     | ✅   | ✅            | ✅                             |
| features-multi-timeframe-service  | ✅   | ✅     | ✅   | —             | —                              |
| features-cross-instrument-service | ✅   | ✅     | ✅   | —             | —                              |
| features-commodity-service        | —    | ✅     | —    | —             | —                              |

A cell marked `—` should render either "no data expected" or be absent. A `✅` cell that shows 0/0 is a bug (empty
denominator = pre-launch handling failure).

## Appendix B — Useful endpoints cheat-sheet

```
GET  /api/data-status/turbo?service=<svc>&start_date=<d>&end_date=<d>&force=true
GET  /api/data-status/turbo/stats
POST /api/data-status/turbo/clear
GET  /api/data-status/coverage-summary?service=<svc>
GET  /api/data-status/schema?service=<svc>&category=<c>&instrument_type=<it>&data_type=<dt>[&venue=<v>]
GET  /api/data-status/instruments-for-shard?service=<svc>&category=<c>&venue=<v>&day=<d>&instrument_type=<it>&data_type=<dt>[&limit=<n>&offset=<n>&search=<q>]
GET  /api/data-status/bucket-counts?service=<svc>&category=<c>&venue=<v>
GET  /api/data-status/download-csv?service=<svc>&category=<c>&venue=<v>&day=<d>&instrument_type=<it>&data_type=<dt>
POST /api/data-status/drilldown/clear-cache
```

## Appendix C — Session state (as of 2026-04-19)

Baseline numbers the agent should see on a fresh cache, `start_date=2018-03-20`, `end_date=2026-04-18`:

- `instruments-service` overall ≈ 98%
- `market-tick-data-service` overall ≈ 50–70% (category-dependent — migration ongoing)
- `market-data-processing-service` overall ≈ 30–60% (upstream-clamped)
- `features-*` overall 0–40% (earlier in pipeline than tick/MDPS work)

If `instruments-service` overall renders < 80% the DeFi legacy filter has regressed. If `market-tick-data-handler`
DEFI > 100% the canonicalisation re-sharding has duplicated shards.
