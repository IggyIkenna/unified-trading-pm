---
name: API Keys and Auth Plan
overview:
  Consolidates API keys, auth rules, and VCR cassette recording. Single source for secrets management, audit alignment,
  and per-venue VCR status (Phases 1–5). Supersedes VCR_CREDENTIAL_RECORDING_PLAN.md.
todos:
  - id: remove-fallback-env-var
    content:
      "DONE 2026-03-06: Removed fallback_env_var param from get_secret_with_fallback() in UTL secret_manager.py and
      get_secret() in client_factory.py. Removed the env-var fallback test from test_uniform_config_access.py. Updated
      cloud_constants.py docstring. Commit: dd6367c in unified-trading-library."
    status: done
  - id: migrate-os-getenv-api-key
    content:
      "DONE 2026-03-06: Audited all os.getenv.*API_KEY matches. All matches are in tests/ or scripts/ (acceptable) or
      archive/. No production source files outside tests/scripts use os.getenv for API keys."
    status: done
  - id: per-venue-secret-sm
    content: Per-venue ensure secret in SM per VCR plan; use secret_name in config
    status: pending
  - id: phase-1-tardis
    content: Phase 1 — tardis cassette (key in SM, definition exists)
    status: pending
  - id: phase-2-http
    content: Phase 2 — databento, thegraph, alchemy, aavescan, envio, openbb-fmp, openbb-fred (add cassette, record)
    status: pending
  - id: phase-2-ws
    content: Phase 2 WS — binance, deribit, ibkr (cassette approach TBD)
    status: pending
  - id: phase-3-keys
    content:
      Phase 3 — pinnacle, odds_api, api_football, glassnode, arkham, soccer_football_info, footystats, coinglass (key in
      SM first; coinglass required by citadel_grade_feature_architecture liquidation-levels todo)
    status: pending
  - id: phase-3-coinglass
    content:
      "Coinglass heatmap API — key NOT in SM. Required by citadel_grade_feature_architecture.plan.md
      (liquidation_levels.py). Check Tardis coverage first; if not covered, obtain Coinglass API key via coinglass.com
      and add as coinglass-api-key in Secret Manager."
    status: pending
  - id: phase-4-blockers
    content: Phase 4 — betfair, kalshi, coinbase, bloxroute, smarkets, betdaq (key/cassette blockers)
    status: pending
  - id: phase-5-sports-betting
    content:
      "DONE 2026-03-06: sports-betting-services repo does not exist at workspace root. Target files
      (footballbets/clients/soccer_football.py, footystats.py, cli/odds_api_cli.py, cli/location.py) are absent — only
      archive/sports-betting-services-previous exists and lacks these files. Migration task is N/A for current workspace
      state."
    status: done
  - id: fix-api-football-key
    content:
      "DONE 2026-03-06: API_FOOTBALL_KEY rename target file (sports-betting-services/footballbets/core/config.py) does
      not exist at workspace root. vcr_endpoints.py already uses API_FOOTBALL_API_KEY correctly. No live code uses
      API_FOOTBALL_KEY (bare form) outside archive."
    status: done
  - id: sm-naming-violations
    content:
      "DONE 2026-03-06: Audited code for bybit_api_key/bybit_api_secret references — zero matches in Python source. SM
      secret names (bybit_api_key underscore) are an SM-level rename, no code change required. Rename should be done via
      SM console/Terraform when safe. graph-api-key deprecated — no code references found."
    status: done
isProject: false
---

# API Keys and Auth Plan

**Consolidates:** [trading_system_audit_prompt.plan.md](trading_system_audit_prompt.plan.md) Section 10. VCR content
inlined below (formerly VCR_CREDENTIAL_RECORDING_PLAN.md, now archived).

---

## Rules (per instruments-domain-and-api-keys.mdc)

| Rule                                                                 | Enforcement                                        |
| -------------------------------------------------------------------- | -------------------------------------------------- |
| All secrets via `get_secret_client(project_id=..., secret_name=...)` | BLOCKING                                           |
| No `get_secret_client(..., fallback_env_var=...)`                    | BLOCKING — silently swallows missing-secret errors |
| No `os.environ.get("TARDIS_API_KEY")` or similar                     | BLOCKING                                           |
| No hardcoded API keys                                                | BLOCKING (audit 10.1)                              |

---

## SSOT References

| Document                                                                       | Purpose                                     |
| ------------------------------------------------------------------------------ | ------------------------------------------- |
| unified-trading-codex/07-security/secrets-management.md                        | Secret Manager SSOT; per-venue secret names |
| unified-api-contracts vcr_endpoints.py                                         | Cassette definitions; key_env per venue     |
| [trading_system_audit_prompt.plan.md](trading_system_audit_prompt.plan.md) §10 | Security audit checklist (10.1–10.19)       |
| api-contracts/scripts/record_vcr_cassettes.py                                  | Record script                               |

> **Note:** api-contracts/build/ is a stale build artifact. Ignore build/lib/api_contracts/endpoint_registry.py — the
> live source is api_contracts/vcr_endpoints.py.

---

## How to Record VCR Cassettes

```bash
cd api-contracts
# Set the API key env var for the venue, then:
PINNACLE_API_KEY=<key> uv run python scripts/record_vcr_cassettes.py --venue pinnacle
# Commit the cassette yaml file to api_contracts/api_contracts_external/<venue>/mocks/
```

After recording: confirm cassette file exists and vcr_endpoints.py entry has a non-empty cassette name.

---

## Phase 1 — Key in SM + cassette definition exists

| Done | Venue  | key_env in vcr_endpoints.py | Secret Name in SM | Notes                                                                               |
| ---- | ------ | --------------------------- | ----------------- | ----------------------------------------------------------------------------------- |
| [ ]  | tardis | TARDIS_API_KEY              | tardis-api-key ✅ | Cassette definition at vcr_endpoints.py:tardis. VCR captures the auth HEAD request. |

---

## Phase 2 — Key in SM, but [] in vcr_endpoints.py

| Done | Venue         | Secret Name in SM                 | Env Var             | Action needed in vcr_endpoints.py                              |
| ---- | ------------- | --------------------------------- | ------------------- | -------------------------------------------------------------- |
| [ ]  | databento     | databento-api-key ✅ (pool of 22) | DATABENTO_API_KEY   | Add get(...) entry with hist.databento.com endpoint            |
| [ ]  | thegraph      | thegraph-api-key ✅ (pool of 9)   | THE_GRAPH_API_KEY   | Add post(...) GraphQL entry; key in URL path — must filter     |
| [ ]  | alchemy       | alchemy-api-key ✅                | ALCHEMY_API_KEY     | Add post(...) entry; key is in URL path — scrub in VCR filter  |
| [ ]  | aavescan      | aavescan-api-key ✅               | AAVESCAN_API_KEY    | Add get(...) entry; determine endpoint URL first               |
| [ ]  | envio         | envio-api-key ✅                  | ENVIO_API_KEY       | Add entry; Envio indexing API endpoint TBD                     |
| [ ]  | openbb (FMP)  | openbb-fmp-api-key ✅             | OPENBB_FMP_API_KEY  | Add entry; FMP endpoints via OpenBB wrapper                    |
| [ ]  | openbb (FRED) | openbb-fred-api-key ✅            | OPENBB_FRED_API_KEY | Add entry; FRED via OpenBB (separate from direct fred-api-key) |

---

## Phase 2 — WebSocket/binary (cassette approach TBD)

| Done | Venue   | Secret Name(s) in SM                               | Env Var              | Notes                                                                                                                                                                                           |
| ---- | ------- | -------------------------------------------------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [ ]  | binance | binance-read-api-key + binance-read-api-key-secret | BINANCE_READ_API_KEY | Private WS (listen key). Need REST call first to get listenKey, then WS.                                                                                                                        |
| [ ]  | deribit | deribit-read-api-key + deribit-read-api-key-secret | DERIBIT_READ_API_KEY | Private WS auth. Synthetic cassette approach TBD.                                                                                                                                               |
| [~]  | ibkr    | ❌ key not in SM yet                               | IBKR_TWS_KEY         | TWS socket protocol — VCR not applicable. RESOLVED: mock at ib_insync layer (MagicMock(spec=IB)); all 4 adapters implement inject-IB. Remaining: add ibkr-account-credentials to SM. [EXTERNAL] |

---

## Phase 3 — key NOT in SM → get key first

| Done | Venue                | key_env               | Target Secret Name    | How to Get Access                                                                                                                                         |
| ---- | -------------------- | --------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [ ]  | pinnacle             | PINNACLE_API_KEY      | pinnacle-api-key      | pinnacle.com/affiliates or partner agreement                                                                                                              |
| [ ]  | odds_api             | ODDS_API_KEY          | odds-api-key          | the-odds-api.com — sign up                                                                                                                                |
| [ ]  | api_football         | API_FOOTBALL_API_KEY  | api-football-api-key  | api-football.com — RapidAPI subscription                                                                                                                  |
| [ ]  | glassnode            | GLASSNODE_API_KEY     | glassnode-api-key     | glassnode.com — subscription                                                                                                                              |
| [ ]  | arkham               | ARKHAM_API_KEY        | arkham-api-key        | arkhamintelligence.com                                                                                                                                    |
| [ ]  | soccer_football_info | FOOTBALL_DATA_API_KEY | football-data-api-key | football-data.org — free tier available                                                                                                                   |
| [ ]  | footystats           | FOOTYSTATS_API_KEY    | footystats-api-key    | footystats.org — API subscription                                                                                                                         |
| [ ]  | coinglass            | COINGLASS_API_KEY     | coinglass-api-key     | coinglass.com — check Tardis coverage first; if not covered, obtain via coinglass.com. Required by citadel_grade_feature_architecture liquidation-levels. |

---

## Phase 4 — No cassette definition AND no key in SM / non-HTTP

| Done | Venue         | Target Secret Name                                         | Env Var               | Blocker                                                                       |
| ---- | ------------- | ---------------------------------------------------------- | --------------------- | ----------------------------------------------------------------------------- |
| [ ]  | betfair       | betfair-api-key                                            | BETFAIR_API_KEY       | Key not in SM; [] in vcr_endpoints.py                                         |
| [ ]  | kalshi (priv) | kalshi-api-key                                             | KALSHI_API_KEY        | Key not in SM (public Kalshi cassette already exists)                         |
| [ ]  | coinbase      | coinbase-api-key                                           | COINBASE_API_KEY      | Key not in SM                                                                 |
| N/A  | hyperliquid   | aws-hyperliquid-s3 (JSON: aws_access_key_id/secret/region) | n/a                   | Already live. S3 requester-pays path uses aws-hyperliquid-s3 (in SM, active). |
| [ ]  | bloxroute     | bloxroute-auth-header                                      | BLOXROUTE_AUTH_HEADER | Key not in SM; paid tier                                                      |
| [ ]  | smarkets      | smarkets-api-key                                           | SMARKETS_API_KEY      | Key not in SM                                                                 |
| [ ]  | betdaq        | betdaq-api-key                                             | BETDAQ_API_KEY        | Key not in SM                                                                 |
| [ ]  | binance (WS)  | binance-read-api-key                                       | BINANCE_READ_API_KEY  | Key in SM ✅; WS not HTTP — VCR approach TBD                                  |
| [ ]  | deribit (WS)  | deribit-read-api-key                                       | DERIBIT_READ_API_KEY  | Key in SM ✅; WS not HTTP — VCR approach TBD                                  |
| [ ]  | ibkr          | ibkr-tws-key                                               | IBKR_TWS_KEY          | Key not in SM; TWS protocol — VCR not applicable                              |

---

## Phase 5 — Sports Betting Services Repo Migration

| Done | Current Env Var              | Target Secret Name           | Notes                                              |
| ---- | ---------------------------- | ---------------------------- | -------------------------------------------------- |
| [ ]  | SOCCER_FOOTBALL_INFO_API_KEY | soccer-football-info-api-key | footballbets/clients/soccer_football.py            |
| [ ]  | FOOTYSTATS_API_KEY           | footystats-api-key           | footballbets/clients/footystats.py                 |
| [ ]  | ODDS_API_KEY                 | odds-api-key                 | footballbets/cli/odds_api_cli.py (shared with UMI) |
| [ ]  | GOOGLE_MAPS_API_KEY          | google-maps-api-key          | footballbets/cli/location.py                       |
| [ ]  | API_FOOTBALL_KEY             | api-football-api-key         | Env var must be renamed to API_FOOTBALL_API_KEY    |

---

## Env Var Inconsistencies — Already Fixed / TODO

| Fixed?   | Was (wrong)      | Now (correct)        | Location fixed                                      |
| -------- | ---------------- | -------------------- | --------------------------------------------------- |
| ✅ Done  | THEGRAPH_API_KEY | THE_GRAPH_API_KEY    | uniswapv2_adapter.py, uniswapv4_adapter.py          |
| [ ] TODO | API_FOOTBALL_KEY | API_FOOTBALL_API_KEY | sports-betting-services/footballbets/core/config.py |

---

## Naming Violations in SM — Fix When Safe

| Current SM Name  | Correct Canonical Name | When to Rename                                                           |
| ---------------- | ---------------------- | ------------------------------------------------------------------------ |
| bybit_api_key    | bybit-api-key          | After confirming no active consumers use underscore name                 |
| bybit_api_secret | bybit-api-secret       | Same as above                                                            |
| graph-api-key    | deprecated → delete    | After confirming no code references graph-api-key (use thegraph-api-key) |

---

## Audit Checklist Alignment

| Audit Item | Action                                                           |
| ---------- | ---------------------------------------------------------------- |
| 10.1       | No API keys hardcoded                                            |
| 10.2       | All secrets via get_secret_client(); no os.getenv empty fallback |
| 10.6       | No verify=False in HTTP clients                                  |
| 10.11      | All API services authenticated                                   |
| 10.12      | No mock auth in production                                       |
| 10.17      | AUTH_FAILURE events logged                                       |
| 10.18      | SECRET_ACCESSED events logged                                    |
| 10.19      | CONFIG_CHANGED events logged                                     |

---

## Deliverables

1. Grep workspace for fallback_env_var — remove all
2. Grep workspace for os.getenv.API_KEY — migrate to get_secret_client
3. Per-venue: ensure secret in SM per VCR plan; use secret_name in config

---

## Completion Criteria

- Phase 1 + Phase 2: cassettes recorded and committed to api_contracts/api_contracts_external//mocks/
- Phase 3: keys obtained + added to SM + cassettes recorded
- Phase 4 WS: architectural decision made on WS cassette tooling
- Phase 5: sports-betting-services migrated to get_secret_client

Codex SSOT: unified-trading-codex/07-security/secrets-management.md#data-vendor-api-keys
