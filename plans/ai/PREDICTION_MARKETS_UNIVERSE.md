# Prediction Markets Universe — Kalshi, Polymarket, Cross-Venue Arb

## Overview

Our prediction market universe covers two regulated/crypto-native platforms and several
traditional sports books. The primary alpha thesis is:

1. **Neg-risk bucket arbitrage** (Polymarket-specific): Multi-outcome mutually-exclusive
   markets where `sum(YES ask prices) < 1.0` = guaranteed profit at resolution
2. **Cross-venue same-event arb**: Same event trading at different implied probabilities
   on Kalshi vs Polymarket vs Pinnacle/Betfair
3. **Market intelligence / sentiment features**: Prediction market probabilities as
   leading indicators for macro/crypto/sports models

---

## Kalshi

### API Basics

- **Base URL**: `https://trading-api.kalshi.com/trade-api/v2`
- **Auth**: Bearer JWT or API key header
- **Rate limits**: Basic 20/10 req/s (read/write). Prime 400/400 req/s (requires 7.5% of exchange monthly volume)
- **Hierarchy**: Series → Event → Market (3 levels, not 2)

### CRITICAL: March 5–6, 2026 Breaking Changes

Two breaking changes happening simultaneously:

1. **Integer cent fields deprecated March 5, 2026**. All code must use string fixed-point:
   - `yes_bid: 45` (int) → `yes_bid_dollars: "0.4500"` (string)
   - `volume: 1234` (int) → `volume_fp: "1234.00"` (string)
   - After this date, integer fields return `0`

2. **Historical data window shrinks to ~3 months** around March 6, 2026. Currently
   shows ~1 year of data. **Bulk-download before the cutoff**:
   - `GET /trade-api/v2/markets` (all historical markets)
   - `GET /trade-api/v2/portfolio/fills` (all historical fills)
   - `GET /trade-api/v2/markets/{ticker}/candlesticks` (price history)

### Market Lifecycle

```
initialized → inactive → active → closed → determined → disputed → amended → finalized
```

### Market Categories of Interest

| Category | Series Examples | Notes |
|----------|----------------|-------|
| **Economics** | KXCPI, KXFED, KXJOBS, KXGDP | Most liquid; Fed rate markets are daily |
| **Finance** | KXBTC, KXETH, INXD (S&P500), KXGOLD | Crypto + equity index prediction |
| **Sports** | NFL, NBA, Soccer (KXNFL, KXNBA) | Weekly/event-based |
| **Politics** | Elections (KXPOTUS, KXSENATE, KXHOUSE) | Very high volume around events |
| **Geopolitics** | Conflict outcomes, treaties | Lower liquidity |

### Key Arb Opportunities vs Polymarket

Both Kalshi and Polymarket list Fed rate decisions, CPI outcomes, Bitcoin price targets.
Cross-venue arb pattern:
```
Kalshi   YES ask for "Fed raises 25bps Nov" = 0.62
Polymarket NO ask for same event           = 0.34
Total cost                                  = 0.96
Guaranteed payout                          = $1.00
Profit                                      = 4% before fees
```

Detection: match markets by `series_ticker` keyword against Polymarket `question` text
(e.g. "KXCPI-24DEC" → Polymarket markets mentioning "CPI December 2024").

---

## Polymarket

### Three-API Architecture

Polymarket data comes from **three separate systems**. All three must be combined for
complete coverage:

| System | Base URL | What it Has | Auth |
|--------|----------|-------------|------|
| **Gamma API** | `gamma-api.polymarket.com` | Market metadata, tags, events, resolution rules, neg_risk grouping | None |
| **CLOB API** | `clob.polymarket.com` | Live order book, trades, order management, price history | L2 HMAC (trading only) |
| **Subgraph** | Goldsky GraphQL | On-chain history: splits/merges, OI, PNL, neg-risk on-chain | None |

### Authentication

- **L1 auth** (one-time): Sign EIP-712 message with wallet private key → derive CLOB credentials
- **L2 auth** (per-request): HMAC-SHA256 headers (`POLY_ADDRESS`, `POLY_SIGNATURE`, `POLY_TIMESTAMP`, `POLY_NONCE`) on all trading endpoints
- **Public endpoints** (no auth): price history, order books, market metadata

### Tagging — Known Messiness

Polymarket's tagging is intentionally/accidentally inconsistent:
- No rigid category field — rely on `tags[]` array from Gamma API
- Many CYOM (create-your-own-market) markets have zero tags
- Same event type (e.g. "BTC above X") may appear with tags `["crypto"]`, `["bitcoin"]`,
  no tags, or with completely different slugs
- **Fallback strategy**: regex match on `question` text for known keywords
  (BTC, ETH, CPI, Fed, NBA, soccer/football, election, etc.)
- For our dataset (215K markets, 240M trades): filtering by question text works better
  than tags

### Data Eras and Availability

| Era | Dates | Data Type | Notes |
|-----|-------|-----------|-------|
| **Pre-AMM** | Jun 2021 | Minimal metadata only | Very sparse |
| **AMM era** | Jun 2021 – Nov 21, 2022 | Splits/Merges (on-chain activity) | No price time-series; capital flow proxies only |
| **CLOB era** | Nov 21, 2022 – present | Full order book, fills, price history | 240M trade records; parquet dataset available |

### Neg-Risk Markets (Bucket Arb)

**Neg-risk** = multi-outcome markets where exactly one bucket resolves YES.
All markets in the group share `neg_risk_market_id`.

**The gold futures arb pattern you identified:**
```
"Gold above $3200 on June 30?"          ask = 0.31
"Gold $3000–$3200 on June 30?"          ask = 0.29
"Gold $2800–$3000 on June 30?"          ask = 0.22
"Gold $2600–$2800 on June 30?"          ask = 0.08
"Gold below $2600 on June 30?"          ask = 0.04
────────────────────────────────────────────────────
Sum of asks                             = 0.94
Guaranteed payout per $0.94 spent       = $1.00
Risk-free profit                        = ~6.4%
Lock-up period                          = until June 30 resolution
```

**Detection algorithm:**
1. Query Gamma API: `GET /markets?neg_risk=true` (or filter by `neg_risk_market_id`)
2. Group markets by `neg_risk_market_id`
3. For each group, verify ranges are exhaustive (cover full distribution)
4. Fetch current CLOB ask prices for each YES token
5. If `sum(asks) < 1.0` → signal (see `NegRiskArbSignal` schema)

**Note on tagging messiness for neg-risk detection**: Polymarket intentionally doesn't
make it easy to find these. Buckets for the same underlying often have different tags.
Most reliable approach: group by `neg_risk_market_id` from Gamma API.

---

## Cross-Venue Arb Schema

See `api_contracts/schemas/prediction_market_arb.py` for:
- `NegRiskArbSignal` — bucket arb within Polymarket
- `CrossVenueArbSignal` — Kalshi vs Polymarket vs sports books
- `PredictionMarketUniverse` — event grouping across venues

### Cross-Venue Matching by Category

| Event Type | Kalshi | Polymarket | Sports Books |
|------------|--------|------------|--------------|
| Fed rate decision | KXFED-* | "Will Fed raise rates..." | N/A |
| CPI release | KXCPI-* | "CPI above X% ..." | N/A |
| BTC price | KXBTC-* | "BTC above $X on..." | N/A |
| NBA Finals | KXNBA-* | "Who wins NBA Finals?" | Pinnacle, Betfair |
| NFL Super Bowl | KXNFL-* | "Who wins Super Bowl?" | Pinnacle, Betfair |
| Soccer leagues | KXSOCCER-* | "Will [Team] win..." | Pinnacle, Betfair |
| US Elections | KXPOTUS-* | "Who wins [race]?" | Betfair (large markets) |

---

## Market Categories of Strategic Interest

### Crypto Finance
- BTC above/below price targets (daily, weekly, monthly)
- ETH, SOL, BNB same pattern
- Crypto dominance metrics
- Exchange collapse/hack events (low prob, high payout when correlated)

### Macro Finance
- Fed funds rate: 25bps / 50bps / hold decisions (most liquid Kalshi series)
- CPI: above/below threshold (monthly)
- S&P 500 index: above/below targets (weekly/monthly)
- Gold, Oil price targets
- VIX above 30, above 40 (useful for volatility regime signals)

### Sports
- NBA: Finals winner, conference winners, regular season win totals
- NFL: Super Bowl winner, division winners, player awards
- Soccer: Premier League, Champions League, World Cup (Kalshi + Betfair overlap)

### Politics
- US elections (very high volume, significant arb vs Betfair historically)
- Congressional control (Senate/House)
- International elections (France, UK, Germany)

---

## Implementation Notes

### Probability Sum Sanity Check
When validating price data, per market YES + NO should sum to ≈ 1.0:
- Exact 1.0: 68.7% of timestamp pairs in historical data
- 0.95–1.05: 99.8% (normal spread/fee-adjusted range)
- < 0.95: 0.2% (low-liquidity early markets; not tradeable arb)

### Lock-Up Risk
Neg-risk bucket arbs require holding until market resolution. Capital is tied up for
the duration. Quantify as `requires_lock_up_days` in `NegRiskArbSignal`.

For the gold June futures arb example: ~60 day lock-up for 6% return = ~36% annualized
(before fees and assuming no slippage filling all buckets simultaneously).

### Fees
- Kalshi: ~2% fee on winnings (maker/taker model, varies by rate tier)
- Polymarket: ~1% fee on market-maker rebates
- Betfair: 5% commission on net winnings (market-dependent, can be reduced)
- Pinnacle: embedded in the juice/vig (~2-3% for major markets)

Always net fees before declaring arb viable.
