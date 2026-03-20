---
title: Backend-Frontend Alignment & Enhancements
status: active
priority: P1
created: 2026-03-20
locked_by: null
---

# Backend-Frontend Alignment & Enhancements

Running plan for items discovered during UI development that require backend changes, data generation, or cross-system
alignment. Updated as new items are found.

---

## 1. Global Instrument Registry Generation

**Status:** - [ ] [BACKEND] P0. Generate static instrument registry from GCS

**Context:** The UI needs a comprehensive instrument registry showing every instrument available across all venues, with
metadata (asset class, venue, instrument type, data types available, date range, cloud location). Currently the UI uses
`lib/registry/ui-reference-data.json` which has venue→category mappings but NOT individual instruments.

**What's needed:**

- Script to scan `instruments-service` GCS storage (dev environment)
- List all instruments per venue with: symbol, instrument type, available data types, earliest date, latest date, cloud
  (GCP/AWS/both)
- Output: `instrument-registry.json` — static file for the UI (mock for now)
- Eventually: live API endpoint from instruments-service

**Where it lives:**

- Script: `instruments-service/scripts/` or `unified-trading-pm/scripts/`
- Output: `unified-trading-system-ui/lib/registry/instrument-registry.json`
- Access: use `unified-cloud-interface` `get_storage_client()` for GCS access

**Dependencies:** GCS credentials (dev environment), instruments-service repo

---

## 2. Data Granularity Labelling

**Status:** - [ ] [BACKEND+FRONTEND] P1. Clarify data granularity per asset class

**Context:** The UI shows "ohlcv" and "trades" as data types, but the actual granularity varies significantly by asset
class:

| Asset Class | Data Type   | Actual Granularity                          | Label in UI        |
| ----------- | ----------- | ------------------------------------------- | ------------------ |
| CeFi        | ohlcv       | Time-sampled (15s, 1m, 5m, 15m, 1h, 4h, 1d) | OHLCV (timeframe)  |
| CeFi        | trades      | Tick-level (every trade)                    | Tick trades        |
| TradFi      | ohlcv       | Time-sampled (same timeframes)              | OHLCV (timeframe)  |
| TradFi      | trades      | Tick-level                                  | Tick trades        |
| DeFi        | pool_state  | Per-block (Ethereum ~12s, L2s faster)       | Block-level state  |
| DeFi        | swaps       | Per-block (every swap event)                | Block-level events |
| Sports      | odds_tick   | Sampled every 5-10 minutes                  | Odds snapshots     |
| Sports      | odds_change | Event-driven (on odds movement)             | Odds changes       |
| Prediction  | odds_tick   | Sampled periodically                        | Market snapshots   |

**What's needed:**

- Backend: add `granularity` field to instrument/data type metadata (e.g., "tick", "block", "sampled_5m",
  "timeframe_configurable")
- Frontend: display granularity alongside data type in catalogue
- market-tick-data-service: confirm naming — is it "market_tick_data" for everything or "odds_tick_data" for sports?

**Open questions:**

- Should sports data service be called "odds-tick-data-service" or keep "market-tick-data-service" with a sports
  adapter?
- DeFi block-level: do we label it "block" or show the actual block time?

---

## 3. Cloud Location Per Instrument

**Status:** - [ ] [BACKEND] P1. Expose cloud location in instrument metadata

**Context:** The UI needs to show whether an instrument's data lives on GCP, AWS, or both. This affects pricing
(in-system query vs egress) and availability. Currently the mock data hardcodes cloud per shard, but in reality it's
per-instrument per-venue.

**What's needed:**

- instruments-service: add `cloud_locations: ["gcp", "aws"]` to instrument metadata
- deployment-service: expose data-status endpoint with cloud breakdown
- UI: show GCP/AWS badges per instrument in the catalogue

---

## 4. Data History Start Dates

**Status:** - [ ] [BACKEND] P2. Expose per-venue data start dates

**Context:** The deployment-service already has `expected-start-dates` per service. The UI needs this to show "Data
available since Sep 2019" per venue in the catalogue.

**What's needed:**

- Expose via API: `GET /api/config/expected-start-dates/{service_name}`
- UI: display in shard-catalogue venue rows (already has a `dataHistory` field)
- Currently hardcoded in `VENUE_DISPLAY` mock data — should come from backend

---

## 5. Subscription Model Backend

**Status:** - [ ] [BACKEND] P2. Subscription/entitlement management API

**Context:** The UI has a full subscription model (tiers, entitlements, locked/available service states) but it's all
mock. The backend needs:

- Org → subscription tier mapping
- Per-org entitlement list
- Subscription upgrade/downgrade API
- Usage tracking (API calls, data queries, compute hours)

**What's needed:**

- Database: org_subscriptions table (org_id, tier, entitlements[], start_date, renewal_date)
- API: CRUD for subscriptions, usage query
- Auth: entitlements included in JWT token

---

## 6. Activity Feed Events

**Status:** - [ ] [BACKEND] P3. Cross-service activity event stream

**Context:** The UI service hub has an activity feed showing lifecycle events (strategy deployed, backtest completed,
settlement confirmed, etc.). Currently mock.

**What's needed:**

- PubSub topic for platform-wide events
- Event schema: { type, entity, actor, timestamp, details, lifecycle_stage }
- API: `GET /api/events?org_id=X&limit=20`
- Sources: strategy-service, execution-service, ml-training-service, pnl-attribution-service

---

## Log

| Date       | Item      | Action                              |
| ---------- | --------- | ----------------------------------- |
| 2026-03-20 | Items 1-6 | Created from UI development session |
