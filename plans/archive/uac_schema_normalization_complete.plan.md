---
doc_type: plan
title: UAC Schema Normalization Complete
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-05'
overview: 'Full resolution of unified-api-contracts schema normalization across every data provider with no exceptions. Combines SCHEMA_NORMALIZATION_AUDIT, SCHEMA_NORMALIZATION_AUDIT_FULL, and SCHEMA_NORMALIZATION_GAPS_AUDIT into a single executable plan. Target: 0 orphaned schemas, 70% test coverage for UAC, interfaces own integration tests (real auth). Future: config-driven subscription to interfaces.'
todos:
- {id: phase1-cefi-core, content: 'CeFi core: coinbase (order/fill), upbit (order), aster (trade/orderbook/order/ticker), hyperliquid (order/fill/ticker), nautilus (order/fill). Add normalizers per GAPS §2.1.', status: completed}
- {id: phase1-tradfi, content: 'TradFi: ibkr, fix, prime_broker, versifi + Databento (TradFi provider: CME, futures, options). TradFi parity with CeFi where possible. Per GAPS §2.2.', status: completed}
- {id: phase1-databento, content: 'Databento: complete OhlcvBar; add Mbo, Bbo1s, Bbo1m, Cmbp1, OptionQuote, CMEOptionQuote, Symbol, Definition→InstrumentRecord. Per GAPS §2.11.', status: completed}
- {id: phase2-fees, content: 'Fees: add CanonicalFee; normalize BinanceFeeRate, CcxtFee, BybitFeeRate, OKXFeeRate, deribit (fee in fills). Per GAPS §2.4.', status: completed}
- {id: phase2-reference, content: 'Reference data: add normalize_* for BinanceSymbol, BybitMarket, OKXMarket, CcxtMarket, DeribitInstrument, DatabentoSymbol, IBKRContractDetails → CanonicalMarketInfo/InstrumentRecord. Per GAPS §2.5.', status: completed}
- {id: phase2-liquidations, content: 'Liquidations: add normalize_* for market (public) + own (private) feeds — different endpoints per venue. All venues for our trades must provide own liquidations. Per GAPS §2.8.', status: completed}
- {id: phase2-derivative-ticker, content: 'Derivative ticker: add normalize_* for Tardis, Binance, Deribit, Bybit, OKX, Hyperliquid → CanonicalDerivativeTicker. Check Tardis.dev docs: ticker vs derivative ticker are distinct; spot may not have derivative ticker. Per GAPS §2.9.', status: completed}
- {id: phase2-options-chain, content: 'Options chain: add normalize_* for Tardis (TardisOptionsChain), Deribit (DeribitMarkPriceOption, DeribitOptionsGreeks), Databento, Yahoo, IBKR → CanonicalOptionsChainEntry. Find raw equivalents per provider (Deribit uses markprice.options channel). Per GAPS §2.10.', status: completed}
- {id: phase3-errors, content: 'Errors: add normalize/errors.py with full taxonomy (§2.17). normalize_<provider>_error for 50+ venues.', status: completed}
- {id: phase3-rate-limits, content: 'Rate limits: implement fully per [RATE_LIMIT_HANDLING_GAPS.md](../../../unified-api-contracts/docs/RATE_LIMIT_HANDLING_GAPS.md) §4 Remediation Order — all 6 steps: (1) header extraction, (2) CanonicalRateLimitError normalization, (3) Retry-After-aware backoff, (4) venue coverage (Kalshi, Polymarket, Pinnacle, Betfair, Odds API), (5) RATE_LIMIT_HIT event + metrics, (6) WebSocket rate limit mapping.', status: completed}
- {id: phase4-sports, content: 'Sports: less detail than CeFi on market/order feed, but map as much as we can. Add external schemas for 20+ bookmakers; normalize kalshi, polymarket, manifold, predictit, betdaq, smarkets, pinnacle. Per GAPS §2.3.', status: completed}
- {id: phase4-prediction, content: 'Prediction markets: kalshi, polymarket, manifold, predictit normalizers. Per GAPS §2.3.', status: completed}
- {id: phase5-bonds-fx, content: 'Bonds/CDS/FX: OFR, ECB, FRED, OpenBB, IBKR → CanonicalBondData, CanonicalYieldCurve. Per GAPS §2.12–2.13.', status: completed}
- {id: phase5-data-alt, content: 'Data/Alt: barchart, footystats, understat, fred, glassnode, coingecko, arkham, pyth, openbb, defillama, regulatory. Per GAPS §2.7.', status: completed}
- {id: phase6-connectivity, content: 'Connectivity: document ping/pong/disconnect/connect per endpoint; normalize to canonical WebSocket lifecycle. Per GAPS §2.16.', status: completed}
- {id: phase6-market-state, content: 'Market state: add MarketState normalization. Per GAPS §2.15.', status: completed}
- {id: live-batch-align, content: 'Live vs batch alignment: ensure identical canonical output regardless of source. Per GAPS §3.', status: completed}
- {id: uac-coverage-70, content: UAC test coverage ≥70%. Integration tests with real auth = interfaces responsibility., status: completed}
- {id: audit-docs-cohesion, content: 'Audit docs cohesion: reconcile AUDIT (outdated), AUDIT_FULL (incomplete), GAPS (SSOT).', status: completed}
- {id: schema-audit-matrix, content: 'Generate final schema audit matrix: Provider × Schema Type with ✓/~/— and canonical target. Run scripts/generate_schema_audit_matrix.py; regenerate when schemas change. Output: docs/SCHEMA_AUDIT_MATRIX.md', status: completed}
isProject: true
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# UAC Schema Normalization — Complete Action Plan

**SSOT:** unified-api-contracts/docs/SCHEMA_NORMALIZATION_GAPS_AUDIT.md **Feeds from:**
[schema_contracts_full_audit.md](schema_contracts_full_audit.md) (Plan #0c) — any missing normalizer gaps identified in
the 60-repo audit will be added to the todo list above.

---

## 1. Cohesion Analysis

| Doc                                | Issues                                                          |
| ---------------------------------- | --------------------------------------------------------------- |
| SCHEMA_NORMALIZATION_AUDIT.md      | Outdated: 3 providers (actually 9), ~57 orphaned (actually ~50) |
| SCHEMA_NORMALIZATION_AUDIT_FULL.md | Incomplete table; missing 30+ providers                         |
| SCHEMA_NORMALIZATION_GAPS_AUDIT.md | **SSOT** — most comprehensive                                   |

---

## 2. Success Criteria

- 0 orphaned schemas
- All normalizers per GAPS §2.1–§2.17
- Live vs batch aligned
- UAC coverage ≥70%
- Integration tests = interfaces
- Future: config-driven subscription
- **Final audited doc:** Provider × Schema Type matrix with ✓/~/— and canonical target, easy to read. Generated from
  code via `python scripts/generate_schema_audit_matrix.py` so it stays current when schemas change.

---

## 3. Execution Order

Phase 1: CeFi core, TradFi, Databento | Phase 2: Fees, reference, liquidations, derivative ticker, options | Phase 3:
Errors (50+ venues) + **Rate limits** (implement fully per RATE_LIMIT_HANDLING_GAPS.md §4 — all 6 steps) | Phase 4:
Sports, prediction | Phase 5: Bonds, data/alt | Phase 6: Connectivity, market state | Final: Live/batch, coverage, audit
cohesion

---

## 4. Out of Scope

- Integration tests with real auth → interfaces
- Config-driven subscription → future
- Interface adoption → future

---

## 5. Provider × Data-Type Matrix (Exhaustive)

### CeFi — Trading

| Provider    | Trade | OB  | Ticker | Order | Fill | Fee     | Liq | DerivTicker | Ref |
| ----------- | ----- | --- | ------ | ----- | ---- | ------- | --- | ----------- | --- |
| binance     | ✓     | ✓   | ✓      | ✓     | ✓    | P1      | P1  | P1          | P1  |
| bybit       | ✓     | ✓   | ✓      | ✓     | ✓    | P1      | P1  | P1          | P1  |
| okx         | ✓     | ✓   | ✓      | ✓     | —    | P1      | P1  | P1          | P1  |
| coinbase    | ✓     | ✓   | ✓      | P1    | P1   | —       | —   | —           | —   |
| ccxt        | ✓     | ✓   | ✓      | ✓     | ✓    | P1      | P1  | —           | P1  |
| deribit     | ✓     | ✓   | ✓      | ✓     | —    | partial | P1  | P1          | P1  |
| upbit       | ✓     | ✓   | ✓      | P1    | —    | —       | —   | —           | —   |
| databento   | ✓     | ✓   | —      | —     | —    | —       | —   | —           | P1  |
| tardis      | ✓     | ✓   | —      | —     | —    | —       | P1  | P1          | —   |
| aster       | P1    | P1  | P1     | P1    | —    | —       | P1  | —           | —   |
| hyperliquid | —     | —   | P1     | P1    | P1   | —       | P1  | P1          | —   |
| nautilus    | —     | —   | —      | P2    | P2   | —       | —   | —           | —   |

### TradFi

| Provider     | Ticker | Order | Fill | Bond | Options |
| ------------ | ------ | ----- | ---- | ---- | ------- |
| ibkr         | P1     | P1    | P1   | P1   | P1      |
| fix          | —      | P2    | P1   | —    | —       |
| prime_broker | —      | —     | P2   | —    | —       |
| versifi      | —      | P2    | P2   | —    | —       |

### Sports / Prediction

kalshi, polymarket, manifold, predictit (P1); betdaq, smarkets, pinnacle (P2); 20+ scrapers (add schemas)

### Data / Alt

barchart (P2), api_football (Adapters), fred/openbb/ofr/ecb (P1),
footystats/understat/glassnode/coingecko/arkham/pyth/defillama/regulatory (P2/P3)

---

## 6. Blockers

| Blocker                      | Type         | Resolution                                   |
| ---------------------------- | ------------ | -------------------------------------------- |
| VersiFi error schema unknown | `[EXTERNAL]` | Request from VersiFi or capture from sandbox |
| API keys Phase 4 venues      | `[EXTERNAL]` | api_keys_and_auth.md                         |
| IBKR TWS VCR strategy        | `[STUB]`     | api_keys_and_auth.md                         |

---

## 7. Reference

- unified-api-contracts/docs/SCHEMA_NORMALIZATION_GAPS_AUDIT.md §2.1–§2.18, §4
- unified-api-contracts/docs/SCHEMA_AUDIT_MATRIX.md — generated Provider × Schema Type matrix (run
  scripts/generate_schema_audit_matrix.py). VersiFi: partial VENUE_ERROR_MAP (500→RETRY, 401→FAIL); Context7
  reverse-engineer for docs without auth.
- [RATE_LIMIT_HANDLING_GAPS.md](../../../unified-api-contracts/docs/RATE_LIMIT_HANDLING_GAPS.md) — rate limit current
  state vs gaps; **implement fully per §4 Remediation Order (all 6 steps)**
- unified-api-contracts/unified_api_contracts/schemas/errors.py
- unified-api-contracts/unified_api_contracts/schemas/rate_limits.py
- CODEX: 02-data/contracts-scope-and-layout.md, 04-architecture/batch-live-symmetry.md
