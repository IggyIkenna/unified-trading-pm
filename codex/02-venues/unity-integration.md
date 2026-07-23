---
doc_type: codex-ssot
title: Unity Integration
summary:
  "Unity sports-betting prime broker: META_BROKER, single USD wallet, single TCP connection + Java Feed Connector
  sidecar, 10 child books (8 confirmed + 2 TBD; 0.2%–3.0% commission-on-win), all 3 sports; commercial terms — $10.8k
  deposit refundable at $5.3M lifetime turnover, $2.6k/mo subscription waived at $260k/mo effective turnover, 1x
  rollover."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags: [unity, sports, odds, execution, meta-broker, cost]
related:
  [
    /codex/02-venues/prime-brokers.md,
    /codex/02-venues/venue-registry-reference.md,
    /codex/03-services/venue-capability-registry.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
  ]
created: 2026-04-17
authoritative_for: [Unity prime-broker integration, Unity child-book registry + commercial terms]
referenced_by:
  [
    /codex/02-venues/prime-brokers.md,
    /codex/02-venues/venue-registry-reference.md,
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/04-architecture/capital-structure-and-regulatory.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Unity Integration

> **What it is:** Unity is our primary sports-betting prime broker. Meta-broker venue, single wallet, 10 child books,
> single TCP connection (per Unity protocol), Java Feed Connector as sidecar. All 3 sports enabled. USD share class.
> Commercial terms tracked for subscription/deposit optimization.

## Why Unity

Unity gives us:

- **One integration, 10 books** (vs integrating 10 bookmakers individually)
- **Single wallet** backing all child-book bets (capital-efficient)
- **Unity's internal SOR** picks best child book per bet (saves reconnaissance cost)
- **Single reg relationship** (simpler compliance than per-book)

Trade-off:

- Commission markup on Unity's side (varies per child book)
- TCP-protocol-specific integration burden
- Subscription + deposit commercial terms to manage

## Technical setup

### Single TCP connection constraint

Unity protocol requires a **single persistent TCP connection** per client account. Not per strategy, not per book — one.
This forces:

- Centralized Unity adapter (not N parallel adapters)
- Multiplexing all strategies over one connection
- Careful disconnection + reconnection handling

### Java Feed Connector sidecar

Unity supplies a Java Feed Connector (binary) for protocol translation. Our architecture:

```
┌──────────────────┐         ┌─────────────────────────┐        ┌─────────┐
│ execution-service│◄───HTTP─┤ Unity Python bridge     │◄──TCP──┤ Unity   │
│ (Python)         │         │ (manages Java connector)│        │ servers │
└──────────────────┘         └─────────────────────────┘        └─────────┘
                                       ▲
                                       │ JVM sidecar
                             ┌─────────────────────────┐
                             │ Unity Java Feed Connector│
                             └─────────────────────────┘
```

- Java connector runs as sidecar process (via subprocess or Docker sidecar)
- Python bridge manages lifecycle (start, health check, restart)
- execution-service talks to Python bridge via HTTP/localhost
- Bridge multiplexes all strategies' bets over the single Unity TCP

### Lifecycle management

- On startup: start Java sidecar; establish Unity TCP; authenticate; subscribe to all eligible markets
- On disconnect: reconnect with exponential backoff; preserve subscription state
- On shutdown: graceful disconnect; flush pending bets; stop sidecar
- Health: sidecar pings bridge every N seconds; disconnect > 30s triggers kill-switch escalation

## Child books (10)

Canonical registry: `unified_api_contracts.internal.UNITY_CHILD_BOOKS` (pulled from
quant-portal.olesportsresearch.com/unity 2026-04-17). All books commissioned as **COMMISSION_ON_WIN** (charged on
winning-bet payouts only). CROWN and SBO are commission-free per Unity pricing.

| #   | Child book | Commission | Commission type   | Sports      | Notes                              |
| --- | ---------- | ---------- | ----------------- | ----------- | ---------------------------------- |
| 1   | VX         | 0.2%       | COMMISSION_ON_WIN | SOC/TEN/BKT | Cheapest; preferred first          |
| 2   | SHARPBET   | 0.2%       | COMMISSION_ON_WIN | SOC/TEN/BKT | Cheapest; preferred first          |
| 3   | 3ET        | 0.5%       | COMMISSION_ON_WIN | SOC/TEN/BKT |                                    |
| 4   | BETDEX     | 1.6%       | COMMISSION_ON_WIN | SOC/TEN/BKT | Decentralized betting exchange     |
| 5   | MATCHBOOK  | 2.2%       | COMMISSION_ON_WIN | SOC/TEN/BKT | Exchange (via Unity)               |
| 6   | IBC        | 2.5%       | COMMISSION_ON_WIN | SOC/BKT     | Asian — IBCBet handicap specialist |
| 7   | BETFAIR    | 2.8%       | COMMISSION_ON_WIN | SOC/TEN/BKT | Exchange (via Unity)               |
| 8   | BROKER5    | 3.0%       | COMMISSION_ON_WIN | SOC/TEN/BKT | Avoid unless spread justifies      |
| 9   | CROWN      | —          | Commission-free   | SOC/BKT     | Asian handicap specialist          |
| 10  | SBO        | —          | Commission-free   | SOC/BKT     | Asian — SBOBet handicap specialist |

Sport legend: SOC = Soccer, TEN = Tennis, BKT = Basketball.

Asian books (CROWN, SBO, IBC — marked `*` on the portal) are soccer/basketball only; they do not support tennis.
Exchanges (BETDEX, MATCHBOOK, BETFAIR) charge commission on winning-bet payouts, consistent with exchange convention.

## Sports enabled (all 3)

- **Soccer** — primary (EPL, LaLiga, Serie A, Bundesliga, Ligue 1, UCL, international)
- **Tennis** — ATP, WTA, Grand Slams
- **Basketball** — NBA, NCAA, EuroLeague

Each sport has its own market types (pre-game, in-play, HT, over/unders, outrights, etc.).

## Share class

**USD.** Unity wallet is denominated in USD conceptually; per-child-book settlements happen in USD against Unity's
internal accounts. Strategies routing via Unity default to `share_class: USD`.

## Commercial terms

Canonical registry: `unified_api_contracts.internal.UNITY_COMMERCIAL_TERMS`.

### Connection fee + free integration

- One-off **connection fee** (non-refundable) buys demo account credentials + support + free 2-month integration period:
  - USD 550 · EUR 500 · GBP 450 · CNY 4,000
- **2 months** of free API access from demo account creation, then monthly subscription kicks in (unless turnover waiver
  is met).
- If production cutover happens on or before the 15th of a month, 50% of the month's subscription is charged AND the
  turnover waiver requirement is halved for that month (prorated billing rule).

### Deposit (production account)

- **USD 10,800 bond** at production onboarding
- **Refundable at USD 5,300,000 lifetime effective turnover**
- **1× rollover** on deposits (must bet through the deposit once before withdrawal)

### Monthly subscription + turnover waiver

Billing currency is per-client; Unity supports four:

| Currency | Subscription / mo | Turnover waiver / mo (effective) |
| -------- | ----------------- | -------------------------------- |
| USD      | 2,600             | 260,000                          |
| EUR      | 2,500             | 250,000                          |
| GBP      | 2,200             | 220,000                          |
| CNY      | 20,000            | 2,000,000                        |

**Effective turnover** = absolute win + absolute loss (not gross volume). Subscription state is reviewed around the 2nd
of each calendar month — prior month's fee is refunded if waiver was met, retained toward the new month otherwise. If
balance is insufficient to cover the fee, Unity notifies before debiting.

### Monitoring

execution-service tracks:

- Cumulative turnover (lifetime → refund trigger; monthly → subscription waiver)
- Rollover remaining (% of deposit-turnover requirement not yet met)
- Subscription due date
- Deposit balance (post-bets, pre-settlements)

Emits events:

- `UNITY_REFUND_THRESHOLD_APPROACHING` (at $4.5M)
- `UNITY_SUBSCRIPTION_WAIVER_ACHIEVED` (at monthly $260k)
- `UNITY_DEPOSIT_LOW` (below $X threshold)

## Placement flow

```
1. Strategy emits BET_BACK / BET_LAY StrategyInstruction
   - eligible child books in config
   - preference hints
2. execution-service passes to Unity bridge
3. Unity Python bridge forwards to Java sidecar
4. Java sidecar sends over TCP to Unity
5. Unity's internal SOR picks child book
6. Unity executes, returns fill with child_venue tag
7. Bridge parses, returns to execution-service
8. execution-service → PBMS with child_venue attribution
```

## Fill attribution

Every Unity fill carries:

```yaml
fill:
  venue: UNITY # parent
  child_venue: VX # Unity's pick
  instrument: "EPL:MATCH_123:HOME"
  odds: 2.10
  stake: 500.00 # USD
  commission: 1.00 # 0.2% of stake
  timestamp_utc: "2026-04-17T18:30:00Z"
  unity_bet_id: "unity_abc123"
  strategy_instance_id: "..." # tagged
```

PBMS attributes:

- Capital to UNITY (parent venue)
- Child-venue tag for analysis + commission aggregation
- Strategy P&L per strategy_instance_id

## Market subscription

- We subscribe to Unity's market feed for eligible leagues
- Feed updates include:
  - New fixtures
  - Odds updates per book per market
  - Market close/suspend events
  - In-play pauses/resumes
- Local cache of last-known odds per (child_book, market, outcome)

## Scope of markets

- Pre-game: 1X2, Asian Handicap, Over/Unders, BTTS, Corners, Cards, DNB, DC
- In-play: same markets with faster refresh
- HT: half-time-specific markets
- Outrights: tournament winners, season-long

Per sport:

- Soccer: full market menu
- Tennis: match winner, set winner, game handicap, totals
- Basketball: moneyline, spread, totals, quarter-specific

## Limits and restrictions

- **Max bet size per book** — per commercial agreement; BROKER5 may have high limits vs PINNACLE_VIA_UNITY restrictions
- **Max concurrent bets** — connection throughput limit
- **Book availability** — certain markets not available on certain books (e.g., BETFAIR exchange has back+lay; others
  back-only)

execution-service pre-flight filters eligible child books per market availability.

## Recon with PBMS

- PBMS reads Unity wallet state periodically (balance, open bets, settled P&L)
- Drift between expected + actual: emit `UNITY_BALANCE_DRIFT_ALERT`
- Daily reconciliation with Unity settlement reports (CSV download via Unity portal)

## Failure modes

| Failure                                  | Mitigation                                              |
| ---------------------------------------- | ------------------------------------------------------- |
| Java sidecar crash                       | Python bridge restart with backoff                      |
| TCP disconnect                           | Reconnect; re-subscribe; alert if > 30s                 |
| Unity auth failure                       | Kill switch all Unity strategies; operator intervention |
| Commission mismatch (expected vs actual) | Log + alert; may indicate book-specific rule change     |
| Child book rejection (odds changed)      | StrategyInstruction retry policy per config             |
| Deposit below threshold                  | Alert ops to top up                                     |
| Subscription month-end without waiver    | Budget ops charge                                       |

## Deployment model

- Unity adapter + Java sidecar deployed alongside execution-service (same pod/VM for latency)
- Dedicated resource allocation (sidecar can be memory-heavy)
- Separate deployment life-cycle from rest of execution-service

## Configuration

Unity-specific config in UCI:

```yaml
unity:
  tcp_host: "unity.example.com"
  tcp_port: 9443
  client_id: "our_client_id"
  credentials_secret_path: "trading/{client_id}/UNITY/tcp_certificate"
  java_sidecar_path: "/opt/unity/feed-connector-v2.jar"
  sports_enabled: [SOCCER, TENNIS, BASKETBALL]
  subscription_threshold_usd_per_month: 260_000
  refund_threshold_usd_lifetime: 5_300_000
```

## Finalizing books 9 and 10

Books 9 and 10 are carried as `TBD_BOOK_9` / `TBD_BOOK_10` stubs in
`unified_api_contracts/internal/unity_child_books.py` until the user pulls the final identity + commission terms from
the user-authenticated quant-portal.

**Workflow:**

1. Log in to https://quant-portal.olesportsresearch.com/unity (requires user authentication — no service credentials).
2. Export the two remaining books' `child_venue_id`, `display_name`, `commission_bps`, `commission_type`, and
   `supported_sports`.
3. Drop them into `unified-api-contracts/data/unity_child_books_update.yaml`:

   ```yaml
   books:
     - child_venue_id: REAL_BOOK_9_ID
       display_name: Real Book 9 Name
       commission_bps: 45 # bps, not percent
       commission_type: FLAT # FLAT / TIERED / PERCENT / COMMISSION_ON_WIN / MAKER_TAKER
       supported_sports: [SOCCER, TENNIS]
       notes: Commission verified from quant-portal on YYYY-MM-DD
       confirmed: true
     - child_venue_id: REAL_BOOK_10_ID
       display_name: Real Book 10 Name
       commission_bps: 60
       commission_type: FLAT
       supported_sports: [SOCCER, TENNIS, BASKETBALL]
       notes: Commission verified from quant-portal on YYYY-MM-DD
       confirmed: true
   ```

4. Preview the change (no write):

   ```bash
   cd unified-api-contracts
   python scripts/update_unity_child_books.py \
       --input data/unity_child_books_update.yaml --dry-run
   ```

5. Apply (writes `unity_child_books.py` and runs `ruff format`):

   ```bash
   python scripts/update_unity_child_books.py \
       --input data/unity_child_books_update.yaml
   ```

6. Validate and commit:

   ```bash
   bash scripts/quality-gates.sh
   git add unified_api_contracts/internal/unity_child_books.py
   git commit -m "feat(unity): finalize books 9 and 10 from quant-portal"
   ```

**Invariants the script enforces** (via `unified_api_contracts.internal.validate_unity_child_book`):

- `supported_sports` must be a subset of `{SOCCER, TENNIS, BASKETBALL}`
- Confirmed books with `commission_bps > 0` must sit in `[20, 300]` bps (0.2% – 3.0%). Outside = almost certainly a unit
  error.
- Total count stays at 10 after merge.
- Unconfirmed stubs must retain the `TBD_BOOK_` prefix and empty `supported_sports` so they never leak into
  `unity_child_books_confirmed()`.

**Tests that will automatically cover the update:**

- `tests/unit/test_unity_child_books.py` runs against the live `UNITY_CHILD_BOOKS` list, so once books 9 and 10 are
  confirmed the count (`exactly_eight_confirmed`) and partition tests need updating. The script intentionally does NOT
  touch the tests — that reminder is left to the human so the acceptance-test change happens in the same commit as the
  data-landing commit.

## Cross-references

- Prime brokers pattern: [prime-brokers.md](prime-brokers.md)
- Venue registry: [venue-registry-reference.md](venue-registry-reference.md)
- Sports archetypes using Unity:
  [/codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md](/codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md),
  [ml-directional-event-settled](/codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md),
  [arbitrage-price-dispersion](/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md)
- Venue-account coordination (Unity shared wallet):
  [/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md)
- Capital structure + regulatory (Unity pool):
  [/codex/04-architecture/capital-structure-and-regulatory.md](/codex/04-architecture/capital-structure-and-regulatory.md)

## Not in this doc

- **Unity API details at protocol level** — Unity documentation + Java Feed Connector docs
- **Per-child-book commercial terms** — commercial agreements (TBDs pending from quant-portal)
- **Sports fixture reference data** — instruments-service (sports sub-package)
- **Bookmaker mapping** — sports reference data
- **Unity portal admin workflow** — ops
