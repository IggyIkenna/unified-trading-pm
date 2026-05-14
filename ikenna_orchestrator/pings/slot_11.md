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

---

## [slot 1 main → slot 11] 2026-05-14 — RETRACTING cbETH + Kraken credential asks

Per operator review 2026-05-14 + actual code path inspection:

**cbETH credential — RETRACT.** The primary data path for cbETH is **on-chain RPC `exchangeRate()` call**,
NOT the Coinbase Institutional API:

- `market-tick-data-service/.../cli/handlers/lst_rates_handler.py:100` has cbETH wired with contract
  address `0xBe9895146f7AF43049ca1c1AE358B0541Ea49704`, selector `0x3ba0b9a9` (keccak256
  of `exchangeRate()`).
- This is the SAME pattern as stETH / rETH / sUSDe / sDAI / mETH / swETH — direct RPC, $0 cost.
- Per PM@3a7a4914 ("canonicalize LST APR sourcing — on-chain exchangeRate() is SSOT, DefiLlama is non-goal")
  and PM@0e9fe345 ("cbETH smoke shipped MTDS@f0b1f7f9"), the canonical source is on-chain + cbETH smoke is
  already shipped.
- cbETH/ETH rate drift over time = staking yield, which is what `carry_staked_basis` consumes — that data
  is collected via the existing on-chain handler. No Coinbase API required.

**Slot 11 action**: re-mark the cbETH adapter scaffold as `**DEFERRED-POST-CUTOVER**` (Coinbase
Institutional REST is a richer-data nice-to-have, not a May-23 blocker). Update master plan deferred-items
row from `BLOCKED-CREDENTIALS` → `DEFERRED` with named successor (post-cutover Coinbase Institutional
integration). Adapter scaffold + unit tests stay shipped; integration tests remain
`@pytest.mark.requires_credentials`.

**Kraken credential — RETRACT for HISTORIC.** Historic Kraken CeFi ticks + funding rates are covered by
**Tardis** (`market-tick-data-service/.../adapters/cefi/tardis_shared.py` exists; Tardis paid commercial
subscription is already operator-acked as `BLOCKED-CREDENTIALS` in master plan).

Live Kraken API would only be needed if Kraken is required as a **primary live hedge venue** for
May-23 — it's the 7th of 7+ CeFi venues (Binance/Bybit/OKX/Deribit/Hyperliquid/Aster already covered).
Per archetype matrix, Kraken is **optional** for both `carry_staked_basis` (Bybit UTA / Deribit / OKX
already cover stETH/wstETH margin) and `arbitrage_price_dispersion` (6 venues already cover the spread).

**Slot 11 action**: same as cbETH — re-mark Kraken adapter as `**DEFERRED-POST-CUTOVER**` (live Kraken
streaming is post-cutover scope, historic via Tardis is the May-23 path). Adapter scaffold stays;
master plan row updates from `BLOCKED-CREDENTIALS` → `DEFERRED` with successor plan filename.

**Operator: NO action needed.** Both items resolve to deferral, not credential approval. Slot 11 takes
the master plan row updates as item #8 (mechanical).
