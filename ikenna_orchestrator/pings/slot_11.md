# Slot 11 — Intra-side ping ledger (EMERGENCY spawn 2026-05-14)

## Boot ack

[2026-05-14 slot-11 UTC] Slot 11 EMERGENCY spawn. Items:

1. alerting_service codex violations D5/D7 (sub-agent)
2. features_service size violations (sub-agent)
3. Tardis docstring + codex ✅ (PM@468c7e8d)
4. Sports scrapers cross-links ✅ (PM@3e349c65)
5. Phase 1 freeze-gate audit ✅ (6/6 green, PM@e67f5ce3 checkbox flips)
6. Coinbase cbETH adapter scaffold (sub-agent)
7. Kraken CeFi adapter scaffold (sub-agent)

## CREDENTIAL APPROVAL REQUEST — Coinbase cbETH Institutional API

[2026-05-14 slot-11 UTC]
Vendor: Coinbase Institutional API (read-only) — free tier for market data
What I need: API key + API secret for Coinbase Advanced Trade API (read-only tier)
Purpose: cbETH APR + supply/redemption rates for carry_staked_basis × DeFi cell
Cost: $0 (free tier for read-only market data endpoints)
Account needed: Coinbase Institutional account with API key scope: read market data
What it unblocks: carry_staked_basis × cbETH leg eligibility for May-23 cutover
Adapter: market_tick_data_service/market_interface/adapters/defi/lst_coinbase_adapter.py (scaffold shipped)
Secrets to provision in GCP Secret Manager:
  - coinbase-api-key   (CB-ACCESS-KEY header)
  - coinbase-api-secret  (HMAC-SHA256 signing secret)
Without it: integration tests skip (`@pytest.mark.requires_credentials`); unit tests + scaffold ship; adapter is dormant on AAVE Oracle fallback
Status: BLOCKED-CREDENTIALS until operator [ack]
