---
doc_type: plan
title: VCR Cassette Recording Plan — External API Credentials
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: "2026-02-28"
---

# VCR Cassette Recording Plan — External API Credentials

**SSOT for secret names/env vars:** `unified-trading-/codex/07-security/secrets-management.md` **SSOT for VCR cassette
definitions:** `api-contracts/api_contracts/vcr_endpoints.py` — each venue entry has `key_env` (env var name) and
`cassette_name`. Empty `[]` = no cassette defined yet. **Record script:**
`api-contracts/scripts/record_vcr_cassettes.py`

> **Note:** `api-contracts/build/` is a stale build artifact. Ignore `build/lib/api_contracts/endpoint_registry.py` — it
> contains an `EndpointStatus` enum with `PENDING_CASSETTE_AWAITING_AUTH` notes that are no longer accurate. The live
> source is `api_contracts/vcr_endpoints.py`.

---

## How to Record

```bash
cd api-contracts
# Set the API key env var for the venue, then:
PINNACLE_API_KEY=<key> uv run python scripts/record_vcr_cassettes.py --venue pinnacle
# Commit the cassette yaml file to api_contracts/api_contracts_external/<venue>/mocks/
```

After recording: confirm cassette file exists and `vcr_endpoints.py` entry has a non-empty cassette name.

---

## Phase 1 — Key in SM + cassette definition exists → just need to run the recorder

`vcr_endpoints.py` has an entry. Key is confirmed in SM. Run the record script and commit.

| Done | Venue    | key_env in vcr_endpoints.py | Secret Name in SM   | Notes                                                                                 |
| ---- | -------- | --------------------------- | ------------------- | ------------------------------------------------------------------------------------- |
| [ ]  | `tardis` | `TARDIS_API_KEY`            | `tardis-api-key` ✅ | Cassette definition at `vcr_endpoints.py:tardis`. VCR captures the auth HEAD request. |

---

## Phase 2 — Key in SM, but `[]` in vcr_endpoints.py → add cassette definition, then record

These have keys in Secret Manager. Need to add an entry to `vcr_endpoints.py` before recording.

| Done | Venue           | Secret Name in SM                   | Env Var               | Action needed in vcr_endpoints.py                                |
| ---- | --------------- | ----------------------------------- | --------------------- | ---------------------------------------------------------------- |
| [ ]  | `databento`     | `databento-api-key` ✅ (pool of 22) | `DATABENTO_API_KEY`   | Add `_get(...)` entry with `hist.databento.com` endpoint         |
| [ ]  | `thegraph`      | `thegraph-api-key` ✅ (pool of 9)   | `THE_GRAPH_API_KEY`   | Add `_post(...)` GraphQL entry; key in URL path — must filter    |
| [ ]  | `alchemy`       | `alchemy-api-key` ✅                | `ALCHEMY_API_KEY`     | Add `_post(...)` entry; key is in URL path — scrub in VCR filter |
| [ ]  | `aavescan`      | `aavescan-api-key` ✅               | `AAVESCAN_API_KEY`    | Add `_get(...)` entry; determine endpoint URL first              |
| [ ]  | `envio`         | `envio-api-key` ✅                  | `ENVIO_API_KEY`       | Add entry; Envio indexing API endpoint TBD                       |
| [ ]  | `openbb` (FMP)  | `openbb-fmp-api-key` ✅             | `OPENBB_FMP_API_KEY`  | Add entry; FMP endpoints via OpenBB wrapper                      |
| [ ]  | `openbb` (FRED) | `openbb-fred-api-key` ✅            | `OPENBB_FRED_API_KEY` | Add entry; FRED via OpenBB (separate from direct `fred-api-key`) |

---

## Phase 2 — Key confirmed in SM, WebSocket/binary — cassette approach TBD

VCR captures HTTP only. These require a WS capture approach, mock gateway, or synthetic fixture.

| Done | Venue     | Secret Name(s) in SM                                   | Env Var                | Notes                                                                    |
| ---- | --------- | ------------------------------------------------------ | ---------------------- | ------------------------------------------------------------------------ |
| [ ]  | `binance` | `binance-read-api-key` + `binance-read-api-key-secret` | `BINANCE_READ_API_KEY` | Private WS (listen key). Need REST call first to get listenKey, then WS. |
| [ ]  | `deribit` | `deribit-read-api-key` + `deribit-read-api-key-secret` | `DERIBIT_READ_API_KEY` | Private WS auth. Synthetic cassette approach TBD.                        |
| [ ]  | `ibkr`    | ❌ key not in SM yet                                   | `IBKR_TWS_KEY`         | TWS socket protocol — VCR not applicable. Need mock TWS gateway.         |

---

## Phase 3 — Cassette definition exists in vcr_endpoints.py, key NOT in SM → get key first

`vcr_endpoints.py` has a fully configured entry. Just need the API key in SM. Steps: (1) obtain key → (2)
`echo -n "<key>" | gcloud secrets create <name> --data-file=- --project=central-element-323112` → (3) run recorder.

| Done | Venue                  | key_env                 | Target Secret Name      | How to Get Access                            |
| ---- | ---------------------- | ----------------------- | ----------------------- | -------------------------------------------- |
| [ ]  | `pinnacle`             | `PINNACLE_API_KEY`      | `pinnacle-api-key`      | pinnacle.com/affiliates or partner agreement |
| [ ]  | `odds_api`             | `ODDS_API_KEY`          | `odds-api-key`          | the-odds-api.com — sign up                   |
| [ ]  | `api_football`         | `API_FOOTBALL_API_KEY`  | `api-football-api-key`  | api-football.com — RapidAPI subscription     |
| [ ]  | `glassnode`            | `GLASSNODE_API_KEY`     | `glassnode-api-key`     | glassnode.com — subscription                 |
| [ ]  | `arkham`               | `ARKHAM_API_KEY`        | `arkham-api-key`        | arkhamintelligence.com                       |
| [ ]  | `soccer_football_info` | `FOOTBALL_DATA_API_KEY` | `football-data-api-key` | football-data.org — free tier available      |
| [ ]  | `footystats`           | `FOOTYSTATS_API_KEY`    | `footystats-api-key`    | footystats.org — API subscription            |

---

## Phase 4 — No cassette definition AND no key in SM / non-HTTP

| Done | Venue           | Target Secret Name                                           | Env Var                 | Blocker                                                                                                                                           |
| ---- | --------------- | ------------------------------------------------------------ | ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| [ ]  | `betfair`       | `betfair-api-key`                                            | `BETFAIR_API_KEY`       | Key not in SM; `[]` in vcr_endpoints.py                                                                                                           |
| [ ]  | `kalshi` (priv) | `kalshi-api-key`                                             | `KALSHI_API_KEY`        | Key not in SM (public Kalshi cassette already exists)                                                                                             |
| [ ]  | `coinbase`      | `coinbase-api-key`                                           | `COINBASE_API_KEY`      | Key not in SM                                                                                                                                     |
| N/A  | `hyperliquid`   | `aws-hyperliquid-s3` (JSON: aws_access_key_id/secret/region) | n/a                     | **Already live.** S3 requester-pays path uses `aws-hyperliquid-s3` (in SM, active). Public API needs no auth. No `hyperliquid-api-key` is needed. |
| [ ]  | `bloxroute`     | `bloxroute-auth-header`                                      | `BLOXROUTE_AUTH_HEADER` | Key not in SM; paid tier                                                                                                                          |
| [ ]  | `smarkets`      | `smarkets-api-key`                                           | `SMARKETS_API_KEY`      | Key not in SM                                                                                                                                     |
| [ ]  | `betdaq`        | `betdaq-api-key`                                             | `BETDAQ_API_KEY`        | Key not in SM                                                                                                                                     |
| [ ]  | `binance` (WS)  | `binance-read-api-key`                                       | `BINANCE_READ_API_KEY`  | Key in SM ✅; WS not HTTP — VCR approach TBD                                                                                                      |
| [ ]  | `deribit` (WS)  | `deribit-read-api-key`                                       | `DERIBIT_READ_API_KEY`  | Key in SM ✅; WS not HTTP — VCR approach TBD                                                                                                      |
| [ ]  | `ibkr`          | `ibkr-tws-key`                                               | `IBKR_TWS_KEY`          | Key not in SM; TWS protocol — VCR not applicable                                                                                                  |

---

## Phase 5 — Sports Betting Services Repo Migration

The `sports-betting-services/` repo uses raw `os.getenv()` — must migrate to `get_secret_client`.

| Done | Current Env Var                | Target Secret Name             | Notes                                                |
| ---- | ------------------------------ | ------------------------------ | ---------------------------------------------------- |
| [ ]  | `SOCCER_FOOTBALL_INFO_API_KEY` | `soccer-football-info-api-key` | `footballbets/clients/soccer_football.py`            |
| [ ]  | `FOOTYSTATS_API_KEY`           | `footystats-api-key`           | `footballbets/clients/footystats.py`                 |
| [ ]  | `ODDS_API_KEY`                 | `odds-api-key`                 | `footballbets/cli/odds_api_cli.py` (shared with UMI) |
| [ ]  | `GOOGLE_MAPS_API_KEY`          | `google-maps-api-key`          | `footballbets/cli/location.py`                       |
| [ ]  | `API_FOOTBALL_KEY`             | `api-football-api-key`         | Env var must be renamed to `API_FOOTBALL_API_KEY`    |

---

## Env Var Inconsistencies — Already Fixed

| Fixed?   | Was (wrong)        | Now (correct)          | Location fixed                                        |
| -------- | ------------------ | ---------------------- | ----------------------------------------------------- |
| ✅ Done  | `THEGRAPH_API_KEY` | `THE_GRAPH_API_KEY`    | `uniswapv2_adapter.py`, `uniswapv4_adapter.py`        |
| [ ] TODO | `API_FOOTBALL_KEY` | `API_FOOTBALL_API_KEY` | `sports-betting-services/footballbets/core/config.py` |

---

## Naming Violations in SM — Fix When Safe

| Current SM Name    | Correct Canonical Name | When to Rename                                                               |
| ------------------ | ---------------------- | ---------------------------------------------------------------------------- |
| `bybit_api_key`    | `bybit-api-key`        | After confirming no active consumers use underscore name                     |
| `bybit_api_secret` | `bybit-api-secret`     | Same as above                                                                |
| `graph-api-key`    | deprecated → delete    | After confirming no code references `graph-api-key` (use `thegraph-api-key`) |

---

## Completion Criteria

- Phase 1 + Phase 2: cassettes recorded and committed to `api_contracts/api_contracts_external/<venue>/mocks/`
- Phase 3: keys obtained + added to SM + cassettes recorded
- Phase 4 WS: architectural decision made on WS cassette tooling
- Phase 5: sports-betting-services migrated to `get_secret_client`

Codex SSOT: `unified-trading-/codex/07-security/secrets-management.md#data-vendor-api-keys`
