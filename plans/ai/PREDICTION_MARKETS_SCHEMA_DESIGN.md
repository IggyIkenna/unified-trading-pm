# Prediction Markets Schema Design Requirements
## Kalshi + Polymarket — Full API Research (Feb 2026)

---

## 1. KALSHI — Full Schema Requirements

### 1.1 API Basics

**Base URL (v2):** `https://api.elections.kalshi.com/trade-api/v2`
**Demo URL:** `https://demo-api.kalshi.co/trade-api/v2`
**OpenAPI version:** 3.8.0
**WebSocket:** `wss://api.elections.kalshi.com/trade-api/ws/v2`

**API Versioning History:**
- **v1** (deprecated): integer cents pricing (e.g., `yes_bid: 45` = $0.45), no FP fields, no historical partition
- **v2** (current): FixedPointDollars strings (`"0.4500"`), FP count fields, historical data partition, subaccounts, multivariate events
- **v2 → v2 internal breaking changes (March 5 2026):** all integer cent fields (`yes_bid`, `no_bid`, `yes_ask`, `no_ask`, `tick_size`, `volume`, `open_interest` as integers) are **deprecated** — use `*_dollars` and `*_fp` variants exclusively from this date forward

---

### 1.2 Authentication

**REST:** RSA key pair. Headers on each request:
```
KALSHI-ACCESS-KEY: <api_key_id>
KALSHI-ACCESS-SIGNATURE: <rsa_pss_sha256_signature>
KALSHI-ACCESS-TIMESTAMP: <unix_ms>
```
Signature payload: `{timestamp}GET/trade-api/v2` (or relevant method+path)

**WebSocket:** Same 3 headers as HTTP connection upgrade headers.

**API Key management:** `GET/DELETE /api_keys/{api_key_id}`, `GET /api_keys`

---

### 1.3 Rate Limits

| Tier | Read | Write | Qualification |
|------|------|-------|---------------|
| Basic | 20/s | 10/s | Complete signup |
| Advanced | 30/s | 30/s | Complete typeform |
| Premier | 100/s | 100/s | 3.75% monthly exchange volume |
| Prime | 400/s | 400/s | 7.5% monthly exchange volume |

Write-limited endpoints: `CreateOrder`, `CancelOrder`, `AmendOrder`, `DecreaseOrder`, `BatchCancelOrders` (each cancel = 0.2 txns), `BatchCreateOrders`

---

### 1.4 Taxonomy: Series → Event → Market

```
Series (recurring template)
  └── Event (specific instance, e.g. "December 2024 CPI")
        └── Market (binary outcome, e.g. "CPI > 3.0%?")
```

**Series fields:**
```
ticker: str                     # e.g. "KXCPI", "INXD"
frequency: str                  # "weekly", "daily", "monthly", "one-off"
title: str
category: str                   # "Economics", "Geopolitics", "Sports", etc.
tags: list[str]                 # cross-category subject tags
settlement_sources: list[{name, url}]
contract_url: str
contract_terms_url: str
fee_type: "quadratic" | "quadratic_with_maker_fees" | "flat"
fee_multiplier: float
volume: int                     # total contracts across all events
volume_fp: str                  # "1234.00"
last_updated_ts: datetime
```

**Known categories (non-exhaustive):**
- Economics: CPI, FOMC rate, jobs report, PCE, PPI, GDP
- Geopolitics: conflicts, elections, policy
- Finance: S&P 500 level, gold price, BTC price
- Sports: NFL, NBA, soccer, tennis
- Politics: US elections, approval ratings
- Weather, Science, Tech

**Event fields (`GET /events/{event_ticker}`):**
```
event_ticker: str               # e.g. "KXCPI-24DEC"
series_ticker: str
title: str
sub_title: str
category: str
status: "open" | "closed" | "settled"
markets_url: str
markets: list[Market]           # when with_nested_markets=true
mutually_exclusive: bool        # if yes, exactly one market settles YES
```

---

### 1.5 Market Schema (Full)

`GET /markets/{ticker}` — fully documented fields:

```python
class KalshiMarket:
    # Identity
    ticker: str                         # e.g. "KXCPI-24DEC-T3.2"
    event_ticker: str                   # parent event
    market_type: Literal["binary", "scalar"]

    # Titles (use yes_sub_title / no_sub_title — title/subtitle deprecated)
    yes_sub_title: str                  # "Above 3.2%"
    no_sub_title: str                   # "At or below 3.2%"
    rules_primary: str                  # plain-language settlement rule
    rules_secondary: str

    # Timing
    created_time: datetime
    updated_time: datetime
    open_time: datetime
    close_time: datetime
    expected_expiration_time: datetime | None
    latest_expiration_time: datetime
    settlement_timer_seconds: int       # delay between determination and settlement

    # Status lifecycle
    status: Literal[
        "initialized", "inactive", "active", "closed",
        "determined", "disputed", "amended", "finalized"
    ]

    # Pricing (CURRENT — use *_dollars fields, integer fields deprecated Mar 2026)
    yes_bid_dollars: str                # "0.4500" — best YES buy
    yes_ask_dollars: str                # "0.4700" — best YES sell
    no_bid_dollars: str                 # "0.5300" — best NO buy
    no_ask_dollars: str                 # "0.5500" — best NO sell
    last_price_dollars: str             # last traded YES price
    previous_yes_bid_dollars: str       # 24h ago bid
    previous_yes_ask_dollars: str       # 24h ago ask
    previous_price_dollars: str         # 24h ago last price

    # Order sizes at best quotes
    yes_bid_size_fp: str                # contracts at best bid
    yes_ask_size_fp: str                # contracts at best ask

    # Volume / OI
    volume_fp: str                      # total volume in contracts
    volume_24h_fp: str                  # 24h volume
    open_interest_fp: str               # contracts outstanding (no netting)

    # Settlement
    result: Literal["yes", "no", "scalar", ""]
    settlement_value_dollars: str | None    # only after determination
    settlement_ts: datetime | None
    expiration_value: str               # actual observed value at settlement
    notional_value_dollars: str         # "$1.0000" per contract

    # Strike (for range/scalar markets)
    strike_type: Literal["greater", "greater_or_equal", "less", "less_or_equal",
                         "between", "functional", "custom", "structured"] | None
    floor_strike: float | None         # min value for YES settlement
    cap_strike: float | None           # max value for YES settlement
    functional_strike: str | None
    custom_strike: dict | None

    # Market mechanics
    can_close_early: bool
    fractional_trading_enabled: bool
    fee_waiver_expiration_time: datetime | None
    early_close_condition: str | None

    # Price structure (replaces deprecated tick_size integer)
    price_level_structure: str
    price_ranges: list[PriceRange]     # [{start, end, step}] in dollars

    # Multivariate
    mve_collection_ticker: str | None
    mve_selected_legs: list[MveLeg] | None
```

**Implied NO price rule:** `no_bid = 1 - yes_ask`, `no_ask = 1 - yes_bid` (Kalshi provides explicit NO quotes unlike Polymarket)

---

### 1.6 Order Book Schema

`GET /markets/{ticker}/orderbook`

```python
class KalshiOrderBook:
    ticker: str
    yes: list[tuple[int, int]]   # [[price_cents, size], ...] sorted best-first — DEPRECATED
    no:  list[tuple[int, int]]   # same for NO side — DEPRECATED
    # v2 new format uses dollars with fp counts
    yes_dollars: list[tuple[str, str]]   # [["0.45", "100.00"], ...]
    no_dollars: list[tuple[str, str]]
```

---

### 1.7 Trades / Fills

`GET /markets/trades` — public trade history
```python
class KalshiTrade:
    trade_id: str
    ticker: str
    created_time: datetime
    yes_price_dollars: str      # execution price for YES side
    no_price_dollars: str
    count_fp: str               # number of contracts
    taker_side: Literal["yes", "no"]
```

`GET /portfolio/fills` — personal fills
```python
class KalshiFill:
    trade_id: str
    ticker: str
    created_time: datetime
    side: Literal["yes", "no"]
    action: Literal["buy", "sell"]
    count_fp: str
    yes_price_dollars: str
    is_taker: bool
    fees_dollars: str
```

**Historical data:** `GET /historical/fills` (same schema, older than ~3-month cutoff)

---

### 1.8 Portfolio / Positions

`GET /portfolio/balance`
```python
class KalshiBalance:
    balance_dollars: str        # available cash
    payout_dollars: str         # pending settlement payouts
    subaccount: str | None
```

`GET /portfolio/positions`
```python
class KalshiPosition:
    ticker: str
    market_title: str
    position: int               # net YES contracts (negative = net NO)
    position_fp: str
    market_exposure_dollars: str  # max loss
    resting_orders_count: int
    realized_pnl_dollars: str
    unrealized_pnl_dollars: str
    total_traded_dollars: str
    fees_paid_dollars: str
    event_ticker: str
    series_ticker: str
    last_price_dollars: str
    yes_bid_dollars: str
    yes_ask_dollars: str
    status: str
    settlement_value_dollars: str | None
```

---

### 1.9 Order Management

`POST /portfolio/orders`
```python
class KalshiOrderRequest:
    ticker: str
    action: Literal["buy", "sell"]
    side: Literal["yes", "no"]
    type: Literal["limit"]      # market type removed
    count_fp: str               # number of contracts
    yes_price_dollars: str      # limit price in dollars
    client_order_id: str | None  # idempotency key
    time_in_force: Literal["gtc", "fok", "ioc"] | None
    expiration_ts: datetime | None
```

`GET /portfolio/orders/{order_id}` — query order
`DELETE /portfolio/orders/{order_id}` — cancel order
`PUT /portfolio/orders/{order_id}` — amend order
`POST /portfolio/batch_orders` — batch create
`DELETE /portfolio/orders` (batch cancel)

---

### 1.10 WebSocket Channels

**Endpoint:** `wss://api.elections.kalshi.com/trade-api/ws/v2`

**Public channels (no auth):**

| Channel | Purpose | Key fields |
|---------|---------|------------|
| `ticker` | Real-time price updates | ticker, yes_bid, yes_ask, last_price, volume, open_interest |
| `trade` | Trade executions | trade_id, ticker, yes_price, count, taker_side, created_time |
| `market_lifecycle_v2` | Market status changes | status transitions, settlement_value (new in 2026) |
| `multivariate` | Multi-leg event updates | collection_ticker, legs, combined payoff |
| `orderbook_delta` | L2 book updates (PUBLIC) | ticker, side, price, delta |

**Private channels (auth required):**

| Channel | Purpose |
|---------|---------|
| `fill` | Personal fill notifications |
| `market_positions` | Position changes |
| `order_group_updates` | Batch order status |
| `communications` | RFQ responses |

**Subscription format:**
```json
{
  "id": 1,
  "cmd": "subscribe",
  "params": {
    "channels": ["ticker"],
    "market_tickers": ["KXCPI-24DEC-T3.2"]
  }
}
```

---

### 1.11 Historical Data Architecture

**Cutoff endpoint:** `GET /historical/cutoff`
```python
class KalshiHistoricalCutoff:
    market_settled_ts: datetime   # markets settled before this → /historical/markets
    trades_created_ts: datetime   # fills before this → /historical/fills
    orders_updated_ts: datetime   # orders before this → /historical/orders
```

**Current live window:** ~1 year (reducing to ~3 months post March 2026)
**Historical endpoints mirror live endpoints** with same cursor pagination:
- `GET /historical/markets`
- `GET /historical/markets/{ticker}`
- `GET /historical/markets/{ticker}/candlesticks`
- `GET /historical/fills`
- `GET /historical/orders`

**Candlestick schema:** `GET /markets/{ticker}/candlesticks`
```python
class KalshiCandlestick:
    end_period_ts: datetime
    ticker: str
    yes_bid_dollars: str
    yes_ask_dollars: str
    yes_close_dollars: str
    yes_open_dollars: str
    yes_high_dollars: str
    yes_low_dollars: str
    volume_fp: str
    open_interest_fp: str
```

---

### 1.12 Market Categories and Ticker Patterns

**Ticker anatomy:** `{SERIES}-{EVENT_DATE_CODE}-{STRIKE}`

Examples:
- `KXCPI-24DEC-T3.2` — CPI series, December 2024, threshold 3.2%
- `KXFED-25JAN-B550` — Fed series, January 2025, between 550-575bps range
- `INXD-25-T5000` — S&P 500, 2025, threshold 5000
- `KXBTCD-25FEB28-T85000` — Bitcoin daily, Feb 28 2025, threshold $85k

**Key series by category:**
```
Economics:
  KXCPI     — CPI YoY (monthly)
  KXPCE     — PCE inflation (monthly)
  KXFED     — FOMC rate decision (8 meetings/year)
  KXJOBS    — Non-farm payrolls (monthly)
  KXUNEMP   — Unemployment rate (monthly)
  KXGDP     — GDP growth (quarterly)

Finance:
  INXD      — S&P 500 level (daily/weekly)
  KXBTCD    — Bitcoin price (daily)
  KXETHU    — ETH price
  KXGOLDD   — Gold price (daily)

Sports:
  NFL series — team win totals, game spreads
  NBA series — game outcomes, championship
```

---

### 1.13 Settlement and Resolution

**Settlement flow:**
1. Market closes (`status: closed`)
2. Kalshi determines outcome using settlement source (`status: determined`)
3. `expiration_value` is set (e.g. "3.4" for CPI)
4. After `settlement_timer_seconds`, payout executes (`status: finalized`)
5. YES holders receive `$1.00` per contract if result = "yes", else $0
6. NO holders receive `$1.00 - settlement_value_dollars` for scalar markets

**Disputed markets:** `status: disputed` — outcome challenged, may be amended

---

## 2. POLYMARKET — Additional Schema Requirements

*(Context from freelancer engagement: 215K markets, 240M trades, Nov 2022–present CLOB data, pre-2022 AMM trades only)*

### 2.1 Three-Layer Architecture

```
Gamma API (metadata)       https://gamma-api.polymarket.com
  Events → Markets (discovery, categories, tags, resolution)

CLOB API (trading)          https://clob.polymarket.com
  Order books, prices, order management, fills

Subgraph (on-chain)         Goldsky-hosted GraphQL
  Positions, historical trades, splits/merges, OI, PNL
```

---

### 2.2 Identifiers (Critical for Joining)

```python
class PolymarketIdentifiers:
    # Gamma identifiers
    condition_id: str     # "0x" + 64 hex — CTF condition, links to subgraph
    question_id: str      # hash of market question — used in CTF resolution
    market_id: str        # Gamma integer ID (for API joins)
    slug: str             # URL slug, e.g. "fed-decision-in-october"

    # CLOB identifiers
    clob_token_ids: list[str]   # [yes_token_id, no_token_id] — ERC1155 on Polygon
    # token_id is the primary CLOB key; maps to asset_id in WS messages

    # On-chain
    market_maker_address: str   # FPMM address (AMM era) or CTF exchange address
```

**Join pattern:**
```
Gamma market.condition_id == Subgraph condition.id
Gamma market.clob_token_ids[0] == CLOB token_id (YES)
Gamma market.clob_token_ids[1] == CLOB token_id (NO)
Trades CSV market_id == Gamma market.id
```

---

### 2.3 Gamma API — Full Endpoint List

**Base:** `https://gamma-api.polymarket.com`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/events` | None | List events, paginated |
| GET | `/events/{id}` | None | Single event by ID |
| GET | `/events/slug/{slug}` | None | Single event by slug |
| GET | `/markets` | None | List markets, paginated |
| GET | `/markets/{id}` | None | Single market by ID |
| GET | `/markets/slug/{slug}` | None | Single market by slug |
| GET | `/tags` | None | All ranked tags |
| GET | `/sports` | None | Sports metadata with tag IDs |
| GET | `/public-search` | None | Cross-search events/markets/profiles |

**Key query params for `/events` and `/markets`:**
```
active=true|false               # live tradable
closed=true|false               # resolved
limit=100 (max)
offset=N                        # pagination
order=volume_24hr|volume|liquidity|start_date|end_date|competitive
ascending=true|false
tag_id=N                        # filter by category tag
exclude_tag_id=N
related_tags=true
slug=<slug>
clob_token_ids=<id>
condition_ids=<id>
liquidity_num_min/max=N
volume_num_min/max=N
start_date_min/max=ISO8601
end_date_min/max=ISO8601
sports_market_types=<type>
game_id=<id>
closed=false
cyom=true                       # create-your-own-market
uma_resolution_status=<status>
include_tag=true                # include full tag objects in response
```

**Event schema:**
```python
class PolymarketEvent:
    id: str
    ticker: str                     # e.g. "nvda-above-in-january-2026"
    slug: str
    title: str
    description: str
    category: str | None            # often blank — use tags instead
    tags: list[PolymarketTag]
    markets: list[PolymarketMarket] # nested markets in same event
    active: bool
    closed: bool
    archived: bool
    restricted: bool
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime
    volume: float
    volume_24hr: float
    liquidity: float
    competitive: float              # metric for market quality
    neg_risk: bool                  # multi-outcome neg-risk event
    neg_risk_market_id: str | None
```

**Market schema:**
```python
class PolymarketMarket:
    id: str
    condition_id: str               # "0x..." — PRIMARY join key to subgraph
    question_id: str
    question: str                   # full question text
    slug: str
    outcomes: list[str]             # ["Yes", "No"] or multiple for neg-risk
    outcome_prices: list[str]       # ["0.73", "0.27"] — implied probabilities
    clob_token_ids: list[str]       # [yes_token_id, no_token_id]
    market_maker_address: str       # on-chain address

    # Status
    active: bool
    closed: bool
    archived: bool
    restricted: bool
    accepting_orders: bool
    accepting_order_timestamp: datetime | None
    cyom: bool                      # user-created market

    # Pricing
    best_bid: str                   # best YES bid
    best_ask: str                   # best YES ask
    last_trade_price: str
    spread: str

    # Volume / Liquidity
    volume: float
    volume_24hr: float
    liquidity: float
    competitive: float

    # Timing
    start_date: datetime
    end_date: datetime
    created_at: datetime
    updated_at: datetime

    # Resolution
    resolution_source: str | None
    resolution_rules: str
    uma_resolution_status: str | None   # "proposed" | "disputed" | "settled"
    winner: str | None              # winning outcome after resolution

    # Tags
    tags: list[PolymarketTag]
    group_item_threshold: float | None
    group_item_title: str | None    # for multi-outcome bucketed events

    # Neg-risk (multi-outcome mutual exclusion)
    neg_risk: bool
    neg_risk_market_id: str | None
    neg_risk_request_id: str | None

    # Sports-specific
    game_start_time: datetime | None
    seconds_delay: int | None
```

---

### 2.4 Gamma API — Tagging Taxonomy (Why It's Messy)

**Problem:** Polymarket has no rigid category taxonomy. Tags are text labels, inconsistently applied.

**Tag structure:**
```python
class PolymarketTag:
    id: int
    label: str          # e.g. "NBA", "Fed Rate", "Crypto", "Politics"
    slug: str
    forceShow: bool
    publishedAt: datetime
    rank: int           # tag priority for display
    icon: str | None
```

**What's available:**
- `GET /tags` returns all tags ranked by prominence
- `GET /sports` returns sports-specific tags with additional metadata (resolution sources, series info, league images)
- Markets can have **multiple tags** (a BTC market might have both "Crypto" and "Finance")
- Events often have no `category` field set — rely on tags

**Known gap:** Markets can be created without any tags (CYOM markets). Many historical markets (2020-2022) have sparse tagging. Pattern matching on `question` field is required as fallback.

**Recommended approach:**
1. Use tag_id for bulk category filtering
2. Supplement with question/slug text matching for uncategorized markets
3. Build a local normalized taxonomy mapping tag_ids → canonical category enum

---

### 2.5 CLOB API — Full Endpoint List

**Base:** `https://clob.polymarket.com`

**Public (no auth):**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API status |
| GET | `/book?token_id=X` | Full L2 order book for one token |
| POST | `/books` | Order books for multiple tokens |
| GET | `/price?token_id=X&side=BUY\|SELL` | Best available price |
| GET | `/midpoint?token_id=X` | (bid + ask) / 2 |
| POST | `/spreads` | Bid-ask spread for multiple tokens |
| GET | `/prices-history?token_id=X&interval=X` | Sampled price history (~10min intervals, ~4K points) |
| GET | `/trades?token_id=X` | Historical trade fills |
| GET | `/last-trade-price?token_id=X` | Most recent execution |
| GET | `/markets` | All CLOB markets (limited fields) |
| GET | `/markets/{condition_id}` | Single CLOB market |
| GET | `/simplified-markets` | Lightweight market list for discovery |
| GET | `/sampling-markets` | Market subset for sampling |
| GET | `/sampling-simplified-markets` | Lightweight sampling |
| GET | `/tick-size?token_id=X` | Current tick size |
| GET | `/neg-risk` | Neg-risk market information |
| GET | `/orders/{order_id}` | Single order (public if unauth'd returns limited info) |

**L2 authenticated (HMAC `POLY_*` headers):**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/api-key` | Derive API credentials |
| GET | `/auth/derive-api-key` | Re-derive existing credentials |
| POST | `/auth/create-api-key` | Create new credentials |
| DELETE | `/auth/delete-api-key` | Revoke credentials |
| POST | `/order` | Create limit order |
| DELETE | `/order` | Cancel order by ID |
| POST | `/orders` | Create multiple orders |
| DELETE | `/orders` | Cancel multiple orders |
| DELETE | `/orders?market=X` | Cancel all orders in market |
| GET | `/orders` | List active orders |
| GET | `/orders/{order_id}` | Single order with full auth detail |
| GET | `/trades?maker_address=X` | Personal trade history |
| GET | `/data/positions?user=X` | User USDC positions per market |
| GET | `/data/pnl?user=X` | Position P&L data |
| GET | `/data/trade-history?user=X` | Full trade history |
| GET | `/notifications` | User notifications |
| POST | `/notifications/mark-as-read` | Mark notifications read |

**CLOB Order schema:**
```python
class PolymarketOrder:
    order_id: str
    asset_id: str               # token_id (YES or NO token)
    side: Literal["BUY", "SELL"]
    price: str                  # "0.73" — probability/price (0 to 1)
    size_matched: str           # USDC matched
    size_remaining: str         # USDC remaining
    status: Literal["LIVE", "MATCHED", "CANCELED", "DELAYED"]
    type: Literal["GTC", "FOK", "GTD"]
    expiration: int | None      # Unix timestamp if GTD
    maker_address: str
    owner: str
    created_at: datetime
    associate_trades: list[str] # linked trade IDs
    outcome: Literal["Yes", "No"]
    outcome_index: int
    market: str                 # condition_id / market address
```

**CLOB Book schema:**
```python
class PolymarketOrderBook:
    market: str                 # condition_id / market address
    asset_id: str               # token_id
    bids: list[dict]            # [{"price": "0.48", "size": "30"}, ...]
    asks: list[dict]            # [{"price": "0.52", "size": "25"}, ...]
    hash: str                   # state hash for change detection
    timestamp: str
```

---

### 2.6 WebSocket Channels (CLOB)

**Endpoint:** `wss://ws-subscriptions-clob.polymarket.com/ws/market`

**Market channel (public):**
```json
{ "assets_ids": ["<token_id>"], "type": "market", "custom_feature_enabled": true }
```

Message types:
- `book` — Full L2 snapshot (bids/asks/hash)
- `price_change` — Order placed or cancelled; `size: "0"` = level removed
- `tick_size_change` — When price > 0.96 or < 0.04 tick changes (0.01 → 0.001)
- `last_trade_price` — Trade execution (price, size, side, fee_rate_bps)
- `best_bid_ask` — BBA summary with spread (requires `custom_feature_enabled`)
- `new_market` — New market created (requires `custom_feature_enabled`)
- `market_resolved` — Market resolved with winning_outcome (requires `custom_feature_enabled`)

**User channel (authenticated):**
```json
{ "type": "user", "auth": { "apiKey": "...", "secret": "...", "passphrase": "..." } }
```
Message types: `trade`, `order`

**Sports channel (separate):**
```
wss://sports-api.polymarket.com/ws   (no auth)
```
Heartbeat: server sends `ping`, must respond `pong` within 10s.

**RTDS channel (live data):**
```
wss://ws-live-data.polymarket.com
```

---

### 2.7 Subgraph (The Graph / Goldsky)

**All hosted at Goldsky. POST with `{"query": "..."}` to GraphQL endpoints.**

| Subgraph | Endpoint (Goldsky) |
|----------|--------------------|
| Positions | `.../subgraphs/positions-subgraph/0.0.7/gn` |
| Orders | `.../subgraphs/orderbook-subgraph/0.0.1/gn` |
| Activity | `.../subgraphs/activity-subgraph/0.0.4/gn` |
| Open Interest | `.../subgraphs/oi-subgraph/0.0.6/gn` |
| PNL | `.../subgraphs/pnl-subgraph/0.0.14/gn` |

**Goldsky project:** `cl6mb8i9h0003e201j6li0diw`

**Activity subgraph key queries (pre-CLOB AMM era data):**
```graphql
query splits($condition: String!) {
  splits(where: { condition: $condition }) {
    id
    timestamp         # Unix seconds
    stakeholder       # wallet address
    collateralAmount  # USDC in (split = buy)
    collection { id } # CTF collection
    condition { id }  # condition_id
    partition         # outcome set
    amount            # tokens received
  }
}

query merges($condition: String!) {
  merges(where: { condition: $condition }) {
    id
    timestamp
    stakeholder
    collateralAmount  # USDC out (merge = sell/close)
    condition { id }
    amount            # tokens burned
  }
}

# Maps token_id → condition_id
query tokenCondition($tokenId: String!) {
  tokenIdCondition(id: $tokenId) {
    id
    conditionId
  }
}
```

**Orders subgraph (CLOB era fills):**
```graphql
query fills($market: String!) {
  orderFilledEvents(where: { market: $market }, orderBy: timestamp, orderDirection: desc) {
    id
    timestamp
    maker
    taker
    makerAssetId   # token_id
    takerAssetId
    makerAmountFilled
    takerAmountFilled
    market
    fee
  }
}
```

**Open Interest subgraph:**
```graphql
query marketOI($conditionId: String!) {
  marketOpenInterest(id: $conditionId) {
    id
    openInterest   # total OI in USDC
    condition { id, outcomeSlotCount }
  }
}
```

---

### 2.8 AMM Era vs CLOB Era

| Period | Mechanism | Price Data | Available Via |
|--------|-----------|-----------|---------------|
| Before Nov 21 2022 | AMM (Automated Market Maker) | No order book snapshots; price = f(reserves) | Activity subgraph: splits/merges as proxy trades |
| Nov 21 2022 → present | CLOB (Central Limit Order Book) | Full L2 order book, every fill | CLOB API trades endpoint + Orders subgraph |

**AMM trade interpretation:**
- `split` = user deposited USDC and received YES + NO tokens (equivalent to opening a position)
- `merge` = user returned YES + NO tokens for USDC (equivalent to closing at fair value)
- `redemption` = claimed winning payout after resolution
- Price at time of split ≈ FPMM price (from fixedProductMarketMaker reserves), NOT stored in event

**Historical price reconstruction for AMM era:** Use the freelancer's trades.csv which maps split/merge transaction amounts as proxy for implied price. **Not tick-by-tick price series** — represents capital flows, not quotes.

---

### 2.9 Multi-Outcome "Neg-Risk" Markets

Polymarket's **neg-risk** mechanism supports mutually-exclusive multi-outcome markets (analogous to Kalshi's `mutually_exclusive` events):

```
Event: "Gold price on Dec 31"
  Market A: Gold above $3000?       YES/NO
  Market B: Gold $2500-3000?        YES/NO
  Market C: Gold below $2500?       YES/NO
```

All three are linked via `neg_risk_market_id`. The probabilities **must sum to 1.0** (one and only one resolves YES).

```python
class PolymarketNegRiskEvent:
    neg_risk_market_id: str         # shared neg-risk ID
    markets: list[PolymarketMarket] # all linked binary markets
    # Sum constraint: sum(market.best_bid for market in markets) ≈ 1.0
```

**Subgraph neg-risk queries:**
```graphql
query negRiskEvent($id: String!) {
  negRiskEvent(id: $id) {
    id
    markets { id condition { id } }
    questionCount
  }
}
```

---

### 2.10 Resolution Sources

Polymarket uses UMA (Universal Market Access) oracle for most resolutions:

```python
class PolymarketResolution:
    resolution_source: str | None   # URL or description
    uma_resolution_status: str | None  # "proposed" | "disputed" | "settled" | None
    question_id: str                 # UMA question hash
    winner: str | None               # outcome string after resolution
    # On-chain: redemption events in Activity subgraph
```

UMA resolution flow:
1. Market closes
2. Proposer submits outcome to UMA optimistic oracle
3. 2-hour dispute window
4. If undisputed: auto-settles
5. If disputed: UMA DVM (Decentralized Verification Mechanism) votes

**Resolution risk:** UMA disputes can delay resolution by 48-72 hours. Some markets have been incorrectly resolved and later corrected via `disputed` status. Schema must store `uma_resolution_status` separately from `closed`/`resolved` booleans.

---

## 3. Cross-Venue Arbitrage Patterns

### 3.1 Direct Same-Market Arb (Kalshi vs Polymarket)

Both venues may list markets on identical events (Fed rate, CPI, BTC price). Price discrepancy = arb.

**Example:**
```
Kalshi:     "FOMC rate above 5.25% after Jan meeting?"  YES bid 0.48 / ask 0.52
Polymarket: "Fed raises rates in January?"              YES bid 0.43 / ask 0.47
```

If semantically equivalent: buy Polymarket YES at 0.47, sell Kalshi YES at 0.48 → 1¢ profit per $1 notional.

**Schema requirement:**
```python
class CrossVenueLink:
    venue_a: Literal["kalshi", "polymarket", "manifold", "metaculus"]
    market_id_a: str
    venue_b: str
    market_id_b: str
    link_type: Literal["identical", "equivalent", "related", "correlated"]
    basis_bps: float        # current price difference in basis points
    verified_by: str        # "manual" | "nlp_similarity" | "structured_match"
    created_at: datetime
```

**Challenges:**
- Kalshi uses binary YES/NO on exact thresholds; Polymarket uses open-ended questions
- Different expiry timestamps (Kalshi settles at specific data release time; Polymarket often settles on "latest reported" date)
- Different resolution sources (Kalshi: BLS; Polymarket: UMA which cites BLS)
- Currency: Kalshi = USD (regulated); Polymarket = USDC (crypto)

---

### 3.2 Probability-Bucket Arb (The Gold Pattern)

User observation: "gold June contracts... combined prob of 94... pick up 6"

**Pattern:** Multiple binary markets on the same underlying cover non-overlapping, exhaustive ranges. Their probabilities must sum to 1.0. If sum < 1.0, there is arbitrage.

```
Gold June 30 price prediction markets:
  "Gold above $3200?"      p = 0.31
  "Gold $3000-$3200?"      p = 0.29
  "Gold $2800-$3000?"      p = 0.22
  "Gold $2600-$2800?"      p = 0.08
  "Gold below $2600?"      p = 0.04
  ─────────────────────────────────
  Sum                        = 0.94  ← 6% arb opportunity

Arb: Buy YES on ALL five markets at current ask prices.
If sum(asks) < 1.0, guaranteed profit regardless of outcome.
```

**Schema representation:**
```python
class ProbabilityBucket:
    group_id: str               # shared identifier for all buckets in set
    underlying: str             # "GOLD_JUNE_2025"
    expiry: datetime
    venue: str

    buckets: list[BucketMarket]

class BucketMarket:
    market_id: str
    lower_bound: float | None   # None = negative infinity
    upper_bound: float | None   # None = positive infinity
    include_lower: bool
    include_upper: bool
    yes_bid: float
    yes_ask: float
    no_bid: float
    no_ask: float

# Arb signal:
# sum(bucket.yes_ask for bucket in buckets) < 1.0 → buy all YES
# sum(bucket.yes_bid for bucket in buckets) > 1.0 → sell all YES (or buy all NO)
```

**How to detect bucket groups automatically:**
1. Find markets on same underlying with same expiry (string similarity on title/slug)
2. Check if lower bound of market[i+1] ≈ upper bound of market[i]
3. Confirm first bucket extends to -∞ and last to +∞
4. Flag groups where sum(ask) < 0.99 or sum(bid) > 1.01

---

### 3.3 Sports Book Cross-Venue Arb

Polymarket vs traditional sports books (DraftKings, Pinnacle, Betfair):

```
Polymarket:  "Chiefs win Super Bowl?"  YES = 0.38
Pinnacle:    Chiefs ML odds           = -163 → implied p = 0.62 (chalk)
```

**Why Polymarket is often mispriced vs books:**
- Polymarket uses UMA resolution (24h+ delay) — liquidity providers discount for resolution risk
- Polymarket has no "vig" (theoretical hold) on individual markets — mispricing more persistent
- Kalshi is regulated and tighter to efficient market; Polymarket more exploitable for sports

**Schema:**
```python
class SportsbookLink:
    polymarket_market_id: str
    sportsbook: str             # "pinnacle", "draftkings", "betfair"
    sportsbook_event_id: str
    sportsbook_market_type: str # "moneyline", "spread", "total"
    sportsbook_implied_prob: float
    polymarket_yes_mid: float
    discrepancy_bps: float
    captured_at: datetime
```

---

### 3.4 Polymarket neg-risk Internal Arb

When neg-risk buckets show sum < 1.0 within Polymarket itself:

```python
class NegRiskArbSignal:
    neg_risk_event_id: str
    bucket_markets: list[str]   # condition_ids
    yes_ask_sum: float          # should be ~1.0 at fair value
    no_bid_sum: float           # = 1 - yes_ask_sum
    arb_bps: float              # (1.0 - yes_ask_sum) * 10000
    capital_required_usdc: float
    expected_profit_usdc: float
    captured_at: datetime
```

**Execution complexity:**
- Each market is a separate EIP-712 signed order
- Gas-free via Polymarket's gasless transaction mechanism
- Must execute all legs atomically (or risk partial fill and exposure)

---

## 4. Data Pipeline Requirements

### 4.1 What We Have (From Freelancer)

```
markets.csv           215,429 markets, all Polymarket history (Gamma API)
trades.csv            240M trades, Nov 22 2022 – Dec 2025 (CLOB fills)
2022_markets.parquet  264 filtered AMM-era markets
2022_trades.parquet   42K AMM-era splits/merges (on-chain activity)
```

**Schema of trades.csv (main price data):**
```
timestamp       datetime (seconds resolution — same-second trades may be milliseconds apart)
market_id       → joins to markets.csv id
price           float (0-1) — execution price for token side
nonusdc_side    "token1" (YES) | "token2" (NO)
maker_direction "BUY" | "SELL"
taker_direction "BUY" | "SELL"
usd_amount      float — USDC value of trade
token_amount    float — outcome tokens exchanged
```

**Known data quality notes:**
- 68.7% of same-timestamp YES/NO pairs sum to exactly 1.0 (efficient)
- 30% sum to 0.95-1.05 (within normal spread)
- 0.2% sum < 0.95 (stale quotes or illiquid — filter for backtesting)
- This is **trade data** (executed fills), NOT order book snapshots
- `/prices-history` endpoint provides sampled history at ~10-min intervals (~4K points per market) — too coarse for arb backtesting
- Historical L2 order book snapshots **do not exist** in any Polymarket API

### 4.2 What Is Missing (Gaps for Kalshi + Enhanced Polymarket)

**Kalshi missing data:**
- [ ] Full market history (fetch via `/historical/markets` before March 2026 cutoff removal)
- [ ] Historical fills (`/historical/fills`)
- [ ] Candlestick data per market (`/historical/markets/{ticker}/candlesticks`)
- [ ] Series metadata (category taxonomy mapping)

**Polymarket gaps:**
- [ ] Real-time L2 order book snapshots (must be recorded live — no historical API)
- [ ] Neg-risk market group identification (requires Gamma API query + bucketing logic)
- [ ] UMA resolution status for each market (track disputes)
- [ ] Pre-CLOB price series (AMM era — reconstruction requires FPMM reserve tracking)
- [ ] NBA and NFL sports markets (original dataset filtered to soccer only)
- [ ] Full subgraph OI data per market (available but not yet pulled)

**Cross-venue missing:**
- [ ] Systematic market-matching between Kalshi and Polymarket
- [ ] Sports book integration (Pinnacle API, Betfair API)
- [ ] Probability bucket auto-detection algorithm

---

## 5. Recommended Normalized Schema (Storage Layer)

### Core tables for GCS parquet (partitioned by `utc_date`):

```python
# Table: prediction_markets
market_id: str           # venue-prefixed: "kalshi:KXCPI-24DEC-T3.2"
venue: str               # "kalshi" | "polymarket"
venue_native_id: str     # original ID
event_id: str            # parent event
series_id: str | None    # recurring series (Kalshi) or neg_risk_event (Poly)
question: str
category: str            # normalized: "economics" | "finance" | "sports" | ...
subcategory: str         # "cpi" | "fed_rate" | "nfl" | "gold" | etc.
underlying: str | None   # "GOLD", "BTC", "SPX" for financial markets
expiry: datetime
resolution_source: str
status: str              # normalized lifecycle
result: str | None       # "yes" | "no" | "n/a"
created_at: datetime
utc_date: date           # partition key

# Table: market_prices (tick data / sampled)
market_id: str
venue: str
token_side: str          # "yes" | "no"
timestamp: datetime
yes_bid: float
yes_ask: float
no_bid: float
no_ask: float
mid: float               # (bid + ask) / 2
spread: float            # ask - bid
volume_usdc: float
open_interest_usdc: float
source: str              # "tick" | "sampled_10min" | "candlestick_1h"
utc_date: date

# Table: market_trades
trade_id: str
market_id: str
venue: str
timestamp: datetime
side: str                # "yes" | "no"
action: str              # "buy" | "sell" (taker perspective)
price: float
size_usdc: float
size_contracts: float
is_taker: bool
utc_date: date

# Table: arb_signals
signal_id: str
signal_type: str         # "cross_venue" | "bucket_sum" | "neg_risk_internal"
markets: list[str]       # market_ids involved
detected_at: datetime
yes_ask_sum: float | None
discrepancy_bps: float
capital_required_usdc: float
expected_profit_usdc: float
expired_at: datetime | None
executed: bool
utc_date: date
```

---

## 6. Key Implementation Notes

1. **Kalshi price migration (urgent):** Integer cent fields deprecated March 5 2026. All code must use `*_dollars` (string fixed-point) fields now.

2. **Polymarket trade data is NOT order book data.** It shows where trades executed, not where orders were sitting. For arb backtesting on Polymarket, build a real-time L2 recorder going forward.

3. **neg-risk markets are the primary bucket arb opportunity on Polymarket.** They are structurally guaranteed to sum to 1.0 if efficient; deviations are exploitable. Use `neg_risk_market_id` to group them.

4. **Kalshi settlement timer matters for arb.** After determination, there is a `settlement_timer_seconds` delay before payout. Capital is locked during this window — factor into P&L calculations.

5. **Cross-venue arb execution risk:** Kalshi = regulated, USD-settled (T+1). Polymarket = USDC on Polygon (near-instant). Must maintain balances on both venues and hedge FX risk (USDC is not perfectly $1.00 always).

6. **Kalshi historical data window is shrinking.** Target: 3 months. Initial: 1 year. Bulk-download all historical markets/fills before March 6 2026.

7. **Polymarket `/prices-history`** returns ~4K data points per market at minimum 10-minute intervals — sufficient for daily strategy signals, insufficient for intraday arb.
