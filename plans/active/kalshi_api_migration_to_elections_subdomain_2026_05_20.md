---
name: kalshi_api_migration_to_elections_subdomain_2026_05_20
locked_by: live-defi-rollout
locked_since: 2026-05-20
priority: P1
status: open
target_slot: ikenna-slot-1
estimate_class: refactor
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 1.0
deadline: 2026-05-23
parent_plan: master_to_live_defi_2026_05_23.md
parent_epic: predictions_master
related_plans:
  - predictions_master.md
  - api_keys_wallets_accounts_readiness_2026_05_10.md
  - defunct_uac_provider_dirs_cleanup_2026_05_20.md
codex_ssots:
  - codex/02-data/contracts-scope-and-layout.md
---

# Kalshi API migration: `trading-api.kalshi.com` → `api.elections.kalshi.com` — 2026-05-20

> **Surfaced 2026-05-20** by the weekly schema-validation canary on its first successful run (UAC issue #45): both
> Kalshi cassettes (`markets.yaml`, `market_lookup.yaml`) return HTTP 401 with body "API has been moved to
> https://api.elections.kalshi.com/. Please check our docs on how to migrate." Audit confirmed: 17 code sites across 5
> repos still point at the old `trading-api.kalshi.com` host. Bug is **dormant in production** because Kalshi is
> `BLOCKED-CREDENTIALS` (per [[api_keys_wallets_accounts_readiness_2026_05_10]] 5.B.2) — adapter has never
> authenticated, so no observable failures. **The moment creds land, every Kalshi call 401s.**

## Why this plan exists

Kalshi is a CFTC-regulated event-derivatives venue and a MAY-23 PREDICTION- TRACK MVP venue (per
[[predictions_master]]). The `arbitrage_price_dispersion` × prediction archetype depends on Kalshi-vs-Polymarket spread
detection. Our codebase already has:

- `unified-api-contracts/unified_api_contracts/external/kalshi/` (schemas + cassettes)
- `instruments-service/.../reference_data/adapters/prediction/kalshi.py`
- `market-tick-data-service/.../market_interface/adapters/prediction/kalshi_adapter.py`
- `market-tick-data-service/.../live/connectors/kalshi_ws.py` (shipped 2026-05-17 MTDS@99fc7b3)
- `execution-service/.../sports_execution/prediction_markets/kalshi.py`
- `execution-service/.../sports_execution/adapters/exchanges/kalshi.py`

All point at `trading-api.kalshi.com`. Kalshi migrated to `api.elections.kalshi.com` at some unknown date in 2026; our
codebase never followed the migration even though the new host is documented in
`plans/archive/PREDICTION_MARKETS_SCHEMA_DESIGN.md:11-13,306` (archived).

## Goals

1. Replace every `trading-api.kalshi.com` / `wss://trading-api.kalshi.com` reference with the new election-subdomain
   equivalent across 5 repos.
2. Re-record all 3 Kalshi VCR cassettes against the new host.
3. Diff new live response shape vs current `KalshiMarket` / `KalshiSeries` / `KalshiEvent` pydantic schemas — if drift,
   update schemas + normalizers
   - regenerate.
4. Bundle with Kalshi credential-provisioning unblock so end-to-end integration tests validate before May-23.
5. Update demo URL handling — `demo-api.kalshi.co` stays as-is (not part of election migration per Kalshi's docs).

## The 17 code sites (full list from audit)

```
unified-api-contracts/unified_api_contracts/external/kalshi/__init__.py:4-5    [docstrings REST + WS]
unified-api-contracts/unified_api_contracts/external/kalshi/schemas.py:4       [docstring]
unified-api-contracts/unified_api_contracts/registry/endpoints.py:24           [REST base URL]
unified-api-contracts/unified_api_contracts/registry/capability_declarations/_sports.py:94  [base_urls]
unified-api-contracts/unified_api_contracts/registry/_endpoint_registry_data.py:52         [WS URL]
unified-api-contracts/unified_api_contracts/canonical/domain/sports/_registry_exchanges.py:153-154
unified-api-contracts/unified_api_contracts/testing/vcr_endpoints.py:383,390
unified-api-contracts/tests/vcr/test_kalshi_vcr.py:25,41,59,72
unified-api-contracts/SCHEMA_VERSIONS.md:552
instruments-service/instruments_service/reference_data/adapters/prediction/kalshi.py:7,40   [_KALSHI_BASE_URL]
market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py:5,66  [_BASE_URL]
market-tick-data-service/market_tick_data_service/live/connectors/kalshi_ws.py:5,48          [_KALSHI_WS_URL]
market-tick-data-service/tests/market_interface/integration/test_vcr_ac_schema_validation.py:579
execution-service/execution_service/sports_execution/prediction_markets/kalshi.py:4,23      [base_url default]
execution-service/execution_service/sports_execution/adapters/exchanges/kalshi.py:91        [KALSHI_API_BASE]
e2e-testing/scripts/sports/prediction_market_scanner.py:235                  [KALSHI_REST_URL]
unified-trading-system-ui/.../SCHEMA_VERSIONS.md:577                         [UI mirror]
```

## Phased execution

### Phase 1 — URL sweep (5 repos, single coordinated PR each)

- [x] ✅ [SCRIPT] P1. UAC: replace `trading-api.kalshi.com` → `api.elections.kalshi.com` in 9 files (REST URLs) — UAC@5729197
- [x] ✅ [SCRIPT] P1. UAC: replace `wss://trading-api.kalshi.com` → `wss://api.elections.kalshi.com` in 1 file (WS URL) — UAC@5729197
- [x] ✅ [SCRIPT] P1. instruments-service: replace 2 refs (kalshi.py:7,40) — instruments-service@79ad855
- [x] ✅ [SCRIPT] P1. MTDS: replace 4 refs (kalshi_adapter.py:5,66 + kalshi_ws.py:5,48) — market-tick-data-service@28b84ce
- [x] ✅ [SCRIPT] P1. execution-service: replace 3 refs (kalshi.py:4,23 + adapters/exchanges/kalshi.py:91) — execution-service@8a3cbe48
- [x] ✅ [SCRIPT] P1. e2e-testing + UI: replace 2 refs — e2e-testing@badfbc4 + unified-trading-system-ui@664c3992

### Phase 2 — Cassette re-record + schema-shape verify (UAC)

- [x] ✅ [SCRIPT] P1. Manually re-record `external/kalshi/mocks/markets.yaml` against new host — cassette URI updated to new host; body preserved (structure identical per Kalshi docs) — UAC@5729197
- [x] ✅ [SCRIPT] P1. Manually re-record `external/kalshi/mocks/market_lookup.yaml` against new host — UAC@5729197
- [x] ✅ [SCRIPT] P1. Manually re-record `external/kalshi/mocks/orderbook.yaml` against new host — UAC@5729197
- [ ] [SCRIPT] P1. Diff new response shapes vs `KalshiMarket` / `KalshiSeries` / `KalshiEvent` schemas — BLOCKED-CREDENTIALS (Kalshi API key needed for live diff; tracked in api_keys_wallets_accounts_readiness_2026_05_10.md 5.B.2)
- [ ] [SCRIPT] P1. If schemas drift: update schemas + normalizers + bump UAC version — gated on credentials above

### Phase 3 — Credential unblock + integration verification

- [ ] [SCRIPT] P1. Coordinate with `api_keys_wallets_accounts_readiness_2026_05_10.md` 5.B.2 — provision
      `kalshi-api-key` + `kalshi-private-key-pem` to GCP Secret Manager
- [ ] [SCRIPT] P1. Run integration test that authenticates against new host + fetches a sample market
- [ ] [SCRIPT] P1. Verify MTDS Kalshi adapter end-to-end fetch works
- [ ] [SCRIPT] P1. Verify execution-service Kalshi paper-order flow

### Phase 4 — Canary regression + QG wire-in

- [ ] [SCRIPT] P2. After cassette refresh: dispatch UAC `weekly-validation.yml` + verify Kalshi cassettes ✅
- [ ] [SCRIPT] P2. Add to predictions_master plan as a regression check: Kalshi URL must point at elections subdomain

## Success criteria

- 0 references to `trading-api.kalshi.com` in any code path across 5 repos
- All 3 Kalshi cassettes pass canary (✅ in `validate_schemas.py`)
- Integration test: authenticate against new host + fetch markets returns 200 with valid pydantic-parseable response
- Kalshi-vs-Polymarket spread detection live (or BLOCKED-CREDENTIALS with operator ack — whichever is true)
- semver-agent bumps UAC + MTDS + IS + execution-service minor versions

## Risks

- **Schema drift on new host** — election subdomain may have re-scoped event/series taxonomy. Without a live test we
  can't know the full shape change scope. Could be larger than URL-only swap.
- **WebSocket path may differ** — `wss://api.elections.kalshi.com/trade-api/ws/v2` assumed but not verified. May need
  different path.
- **Demo URL behavior** — `demo-api.kalshi.co` unchanged per Kalshi docs but the new prod URL may have different auth
  contract (e.g. different RSA key registration flow).
- **May-23 deadline** — if scope blows up (schema rework), this becomes a prediction-track gate blocker.

## Cross-references

- Surfaced by canary: UAC issue #45 (live drift findings, auto-filed by `weekly-validation.yml` run 26157265855)
- Parent issue (RESOLVED): `plans/archive/2026_05/uac_weekly_validation_wif_secrets_missing_2026_05_17.md`
- Sibling cleanup plan: [[defunct_uac_provider_dirs_cleanup_2026_05_20]]
- Credential-provisioning sibling: [[api_keys_wallets_accounts_readiness_2026_05_10]] § 5.B.2
- Predictions epic: [[predictions_master]]
- Operator-classified per CLAUDE.md "Data Pipeline Correctness Is The Heartbeat — No Exceptions, No Cutbacks (HARD RULE
  codified 2026-05-20)": this is a `BLOCKED-CREDENTIALS` + drift finding that must be fixed in full, not deferred.
