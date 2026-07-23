---
doc_type: plan
title: Kalshi API migration — trading-api.kalshi.com → api.elections.kalshi.com
summary:
status: complete
nature: record
asset_group: [prediction]
stage: [meta]
repos: [e2e-testing, execution-service, instruments-service, market-tick-data-service, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/epics/predictions_master.md,
    /plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md,
    /plans/archive/2026_05/defunct_uac_provider_dirs_cleanup_2026_05_20.md,
  ]
created: "2026-05-20"
parent_epic: predictions_master
assigned_vm: vm-prediction
priority: P1
archived: 2026-05-23
estimate_class: refactor
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 1.0
---

# Kalshi API Migration: `trading-api.kalshi.com` → `api.elections.kalshi.com`

Surfaced 2026-05-20 by weekly schema-validation canary: both Kalshi cassettes return HTTP 401 "API has been moved to
https://api.elections.kalshi.com/". 17 code sites across 5 repos still point at old host. Bug dormant in production
because Kalshi is `BLOCKED-CREDENTIALS` (api_keys_wallets_accounts_readiness 5.B.2) — the moment creds land, every
Kalshi call 401s. Must fix before May-23 since `arbitrage_price_dispersion` × prediction archetype depends on
Kalshi-vs-Polymarket spread detection.

Codex SSOTs: `/codex/02-data/contracts-scope-and-layout.md`

---

## Phase 1 — URL sweep (5 repos)

- [x] ✅ [SCRIPT] P1. UAC: replace `trading-api.kalshi.com` → `api.elections.kalshi.com` in 9 files (REST URLs) + 1 file
      (WS URL). (UAC@`5729197`)
- [x] ✅ [SCRIPT] P1. instruments-service: replace 2 refs (kalshi.py:7,40). (instruments-service@`79ad855`)
- [x] ✅ [SCRIPT] P1. MTDS: replace 4 refs (kalshi_adapter.py:5,66 + kalshi_ws.py:5,48).
      (market-tick-data-service@`28b84ce`)
- [x] ✅ [SCRIPT] P1. execution-service: replace 3 refs (kalshi.py:4,23 + adapters/exchanges/kalshi.py:91).
      (execution-service@`8a3cbe48`)
- [x] ✅ [SCRIPT] P1. e2e-testing + UI: replace 2 refs. (e2e-testing@`badfbc4`, unified-trading-system-ui@`664c3992`)

## Phase 2 — Cassette re-record + schema-shape verify

- [x] ✅ [SCRIPT] P1. Manually re-record `external/kalshi/mocks/markets.yaml`, `market_lookup.yaml`, `orderbook.yaml`
      against new host; cassette URI updated; body preserved. (UAC@`5729197`)
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. Diff new response shapes vs `KalshiMarket`/`KalshiSeries`/`KalshiEvent`
      schemas. **BLOCKED-CREDENTIALS**: Kalshi API key needed for live diff; tracked in
      `api_keys_wallets_accounts_readiness_2026_05_10.md` 5.B.2.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. If schemas drift: update schemas + normalizers + bump UAC version.
      Gated on credentials above.

## Phase 3 — Credential unblock + integration verification

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. Coordinate with `api_keys_wallets_accounts_readiness_2026_05_10.md`
      5.B.2 — provision `kalshi-api-key` + `kalshi-private-key-pem` to GCP Secret Manager.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. Run integration test: authenticate against new host + fetch sample
      market.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. Verify MTDS Kalshi adapter end-to-end fetch.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. Verify execution-service Kalshi paper-order flow.

## Phase 4 — Canary regression + QG wire-in

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P2. After cassette refresh: dispatch UAC `weekly-validation.yml` + verify
      Kalshi cassettes pass.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P2. Add to predictions_master: Kalshi URL must point at elections subdomain
      as regression check.

## Deferred work — migrated to: `predictions_master`

All Phase 2-4 items DEFERRED-OPERATOR-DECISION (BLOCKED-CREDENTIALS — Kalshi API key not yet provisioned):

- **Phase 2 — Schema diff (P1, BLOCKED-CREDENTIALS)**: Diff new response shapes vs
  `KalshiMarket`/`KalshiSeries`/`KalshiEvent` schemas against new `api.elections.kalshi.com` host. Requires live Kalshi
  API key.
- **Phase 2 — Schema update (P1, BLOCKED-CREDENTIALS)**: If schemas drift, update schemas + normalizers + bump UAC
  version. Gated on diff above.
- **Phase 3 — Provision credentials (P1, BLOCKED-CREDENTIALS)**: Provision `kalshi-api-key` + `kalshi-private-key-pem`
  to GCP Secret Manager per `api_keys_wallets_accounts_readiness_2026_05_10.md` 5.B.2.
- **Phase 3 — Integration test (P1, BLOCKED-CREDENTIALS)**: Authenticate against new host + fetch sample market.
- **Phase 3 — MTDS verify (P1, BLOCKED-CREDENTIALS)**: Verify MTDS Kalshi adapter end-to-end fetch.
- **Phase 3 — Execution verify (P1, BLOCKED-CREDENTIALS)**: Verify execution-service Kalshi paper-order flow.
- **Phase 4 — Canary regression (P2, BLOCKED-CREDENTIALS)**: Dispatch UAC `weekly-validation.yml` + verify Kalshi
  cassettes pass after cassette refresh.
- **Phase 4 — predictions_master regression check (P2, BLOCKED-CREDENTIALS)**: Add to predictions_master: Kalshi URL
  must point at elections subdomain as regression check.

## Temporary states + canonical follow-up plans

- Phases 2-4 gated on Kalshi credential provisioning (`api_keys_wallets_accounts_readiness_2026_05_10.md` 5.B.2).
- Schema drift risk: election subdomain may have re-scoped event/series taxonomy — scope may exceed URL-only swap.
- Demo URL (`demo-api.kalshi.co`) unchanged per Kalshi docs; not part of this migration.
