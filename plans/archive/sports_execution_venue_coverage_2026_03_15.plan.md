---
doc_type: plan
title: sports-execution-venue-coverage
summary: 'Comprehensive sports execution coverage plan for all venues the Odds API covers. Adds venue

  execution profiles to UAC, browser automation infrastructure to USEI, and execution adapters

  for ~70 bookmakers. Designed for world-class sports arbitrage.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-15'
todos:
- {id: p0-venue-execution-schema, content: '[AGENT] P0. Create VenueExecutionProfile Pydantic model in UAC canonical/domain/sports/

    with all fields needed for any execution method. See section 2 for schema.

    ', status: pending}
- {id: p0-venue-profiles-api-tier, content: '[AGENT] P0. Populate VenueExecutionProfile data for all Tier 1 (API) venues.

    See section 4.1 for the 5 venues.

    ', status: pending}
- {id: p0-venue-profiles-browser-tier, content: '[AGENT] P1. Populate VenueExecutionProfile data for all Tier 2 (browser automation)

    venues. See section 4.2 for the full list (~65 venues).

    ', status: pending}
- {id: p1-browser-adapter-base, content: '[AGENT] P0. Create BrowserAutomationAdapter base class in USEI with Playwright

    integration, CAPTCHA handling hooks, session management, and anti-detection patterns.

    ', status: pending}
- {id: p1-usei-router-expansion, content: '[AGENT] P1. Expand SportsExecutionRouter to support browser-based venue routing

    alongside existing API routing. Add venue capability resolution.

    ', status: pending}
- {id: p2-exchange-adapter-hardening, content: '[AGENT] P0. Harden existing exchange adapters (Betfair, Smarkets, Matchbook, Betdaq)

    with full order lifecycle, position tracking, commission calc. Wire into router.

    ', status: pending}
- {id: p2-us-sportsbook-adapters, content: '[HUMAN+AGENT] P1. Build browser adapters for US sportsbooks: DraftKings, FanDuel,

    BetMGM, Caesars, BetRivers. Requires live account testing.

    ', status: pending}
- {id: p2-uk-bookmaker-adapters, content: '[HUMAN+AGENT] P1. Build browser adapters for UK bookmakers: Bet365, William Hill,

    Ladbrokes, Coral, Paddy Power, Sky Bet, Betway.

    ', status: pending}
- {id: p2-eu-bookmaker-adapters, content: '[HUMAN+AGENT] P1. Build browser adapters for EU bookmakers: 1xBet, Unibet, Betsson,

    Marathon Bet, Winamax, Betclic, Tipico.

    ', status: pending}
- {id: p2-au-bookmaker-adapters, content: '[HUMAN+AGENT] P1. Build browser adapters for AU bookmakers: Sportsbet, TAB, Neds,

    PointsBet AU, Ladbrokes AU.

    ', status: pending}
- {id: p2-offshore-adapters, content: '[HUMAN+AGENT] P2. Build browser adapters for offshore books: Bovada, BetOnline,

    MyBookie, BetUS.

    ', status: pending}
- {id: p3-arb-detection-integration, content: '[AGENT] P1. Wire venue execution profiles into arbitrage detection pipeline.

    Cross-reference Odds API bookmaker keys with execution profiles for instant

    can-we-execute-on-both-legs resolution.

    ', status: pending}
- {id: p3-config-credentials-schema, content: '[AGENT] P0. Add sports venue credential schemas to UCfgI. Supports API keys,

    OAuth tokens, and username/password (for browser venues). Secret Manager integration.

    ', status: pending}
- {id: p4-venue-health-monitoring, content: '[AGENT] P2. Build venue health monitoring: session validity, login state, CAPTCHA

    detection, rate limit tracking, withdrawal queue status.

    ', status: pending}
- {id: p4-concurrent-execution-engine, content: '[AGENT] P1. Build concurrent multi-venue execution engine for arbitrage. Must place

    orders on N venues within <2s window. Handles partial fills and rollback.

    ', status: pending}
- {id: p5-clv-tracking, content: '[AGENT] P0. Add CLV tracking fields to BetExecution in UAC (odds_at_placement, closing_odds,

    clv_edge_pct). Add CLVRecord schema for historical CLV analysis. Every bet records placement

    odds vs closing line — the fundamental metric for whether models work.

    ', status: pending}
- {id: p5-exchange-market-making, content: '[AGENT] P1. Create SportsMarketMakingStrategy in strategy-service. Wire matching-engine-library

    spread management concepts to Betfair Stream API via USEI. Post back+lay at spread, capture

    difference. Exchanges do not limit market makers — sustainable edge.

    ', status: pending}
- {id: p5-cross-asset-bridge, content: '[AGENT] P1. Create sports-financial feature bridge in features-cross-instrument-service.

    Connect features-sports-service outputs (odds, form, xG) to cross-instrument correlation

    pipeline. Enable sports-to-financial and financial-to-sports signal generation.

    ', status: pending}
- {id: p5-multi-account-management, content: '[AGENT] P0. Extend UCfgI SportsVenueCredentialConfig to support per-venue, per-account

    credential storage. Add account lifecycle tracking (warmup, active, restricted, recycled).

    Support 50-100+ accounts across books with independent identities.

    ', status: pending}
- {id: p5-enhanced-kelly-sizing, content: '[AGENT] P1. Enhance KellyCriterionStrategy with portfolio Kelly (correlated bets),

    simultaneous Kelly (bankroll sharing across open bets), and venue-specific max bet

    limits from VenueExecutionProfile. Add half-Kelly safety default.

    ', status: pending}
- {id: p6-steam-move-detection, content: '[AGENT] P1. Add steam move detection calculator to features-sports-service. Detect when

    sharp money moves a line at Pinnacle/exchanges and exploit lag at soft books. Wire into

    odds_calculator alongside existing gap_max_vs_pinnacle features.

    ', status: pending}
- {id: p6-middle-betting, content: '[AGENT] P2. Add middle betting strategy to strategy-service. Bet both sides at different

    lines to create a middle zone where both bets win. Calculate middle probability and EV.

    ', status: pending}
- {id: p6-in-play-trading, content: '[HUMAN+AGENT] P1. Build in-play trading infrastructure. Real-time feature calculation

    during matches, sub-second inference, Betfair Stream API execution. Highest alpha,

    highest difficulty. Requires proprietary live data feeds.

    ', status: pending}
isProject: false
---

# Sports Execution Venue Coverage -- World-Class Arbitrage Infrastructure

## Related Documents

- UAC Citadel Architecture: uac_citadel_architecture_0ccb5b9b.plan.md
- UAC Citadel Execution: uac_citadel_implementation_execution.plan.md
- UAC Citadel Remediation: uac_citadel_remediation.plan.md

---

## 1. Current State Assessment

### 1.1 What We Have (Execution-Ready)

| Venue      | Category       | Adapter               | In Router | Status                     |
| ---------- | -------------- | --------------------- | --------- | -------------------------- |
| Betfair    | Exchange       | BetfairAdapter        | Yes       | Full execution             |
| Pinnacle   | Bookmaker API  | PinnacleAdapter       | Yes       | Full execution             |
| Polymarket | Prediction Mkt | PolymarketCLOBAdapter | Yes       | Full execution             |
| Smarkets   | Exchange       | SmarketsAdapter       | No        | Adapter exists, not routed |
| Matchbook  | Exchange       | MatchbookAdapter      | No        | Adapter exists, not routed |
| Betdaq     | Exchange       | BetdaqAdapter         | No        | Adapter exists, not routed |
| Paper      | Simulated      | PaperBettingAdapter   | Yes       | Testing only               |

### 1.2 What We Have (Odds Only -- No Execution)

| Venue             | Adapter Type  | Notes                                                     |
| ----------------- | ------------- | --------------------------------------------------------- |
| Odds API          | Aggregator    | Covers 70+ bookmakers for odds data                       |
| API-Football      | Data API      | Fixtures, lineups, odds                                   |
| 1xBet             | Bookmaker API | Odds only in current adapter                              |
| 16 UK/EU scrapers | Scrapers      | bet365, coral, ladbrokes, skybet, etc. odds scraping only |

### 1.3 The Gap

67 venues in BOOKMAKER_REGISTRY are category SCRAPER with zero execution capability. The Odds API gives us live odds
from ~70 bookmakers. We can detect arbitrage opportunities across all of them. But we can only execute on 6 venues (3
exchanges + Pinnacle + Polymarket + 1xBet partially). For world-class arbitrage, we need execution coverage on every
venue where we can detect an edge.

### 1.4 Two Strategy Paths

| Strategy      | Data Source                                                     | Execution Venues                         | Latency Requirement          |
| ------------- | --------------------------------------------------------------- | ---------------------------------------- | ---------------------------- |
| ML Prediction | Odds API (aggregated features), FSS derived features, ML models | Exchanges (Betfair, Smarkets) + Pinnacle | Moderate (seconds)           |
| Arbitrage     | Odds API (real-time per-bookmaker), exchange APIs, scrapers     | ALL venues where legs are priced         | Critical (<2s for both legs) |

ML Prediction works today with current infrastructure. Arbitrage requires this plan.

---

## 2. VenueExecutionProfile Schema (UAC Addition)

This schema captures everything an AI agent or human operator needs to know about executing on any venue. Lives in
canonical/domain/sports/venue_execution.py.

Key enums: ExecutionMethod (rest_api, websocket_api, fix_protocol, browser_automation, hybrid), AntiDetectionLevel
(none, basic, moderate, aggressive, extreme), CredentialType (api_key, api_key_secret, oauth2, username_password,
username_password_2fa, certificate, wallet_private_key), AccountVerificationLevel (none, email, phone, kyc_basic,
kyc_enhanced, kyc_full).

VenueExecutionProfile fields (Pydantic model extending CanonicalBase):

- Identity: venue_key, odds_api_key, display_name, parent_company
- Execution method: primary_execution_method, fallback_execution_method
- API details: api_base_url, api_docs_url, api_version, has_rest_api, has_websocket_api, has_streaming_api,
  has_fix_protocol, api_rate_limit_requests_per_second, api_rate_limit_requests_per_minute, api_fee_monthly,
  api_fee_one_off, api_fee_currency
- Browser automation: login_url, bet_placement_url_pattern, account_url, withdrawal_url, deposit_url, mobile_site_url,
  uses_single_page_app, requires_javascript, anti_detection_level, known_waf, requires_captcha, captcha_type,
  requires_geolocation_check, geolocation_provider, session_timeout_minutes, max_concurrent_sessions
- Credentials: credential_type, requires_2fa, two_factor_method, account_verification_level
- Geographic: headquarters_country, license_jurisdictions, available_countries, blocked_countries, blocked_us_states,
  available_us_states, requires_residency, residency_countries, requires_local_payment_method, ip_geo_enforcement,
  vpn_detection
- Financial: supported_currencies, min_deposit, max_deposit, min_withdrawal,
  max_withdrawal_per_transaction/day/week/month, withdrawal_delay_hours_min/max, withdrawal_methods, deposit_methods,
  supports_crypto_deposit/withdrawal, crypto_currencies_accepted
- Bet limits: min_bet, min_bet_currency, max_bet_per_market, max_payout, max_payout_currency, limits_winning_accounts,
  account_limiting_severity
- Fees: commission_model, commission_rate, commission_notes, withdrawal_fee, withdrawal_fee_type
- Operational: notes, known_issues, last_verified_date

### 2.1 Separation of Concerns (UAC vs UIC vs USEI)

| Layer | What It Owns                                           | Sports Execution Additions                                                             |
| ----- | ------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| UAC   | External API schemas, venue contracts, canonical types | VenueExecutionProfile schema, per-venue profile data, VENUE_EXECUTION_REGISTRY         |
| UIC   | Internal service-to-service schemas                    | Sports execution events (order placed, filled, failed), health check schemas           |
| USEI  | Execution adapters, routing, order lifecycle           | BrowserAutomationAdapter base, per-venue browser adapters, concurrent execution engine |
| UCfgI | Config schemas, credentials                            | Sports venue credential config, Secret Manager field mappings                          |

UAC does NOT contain execution logic, adapter code, or browser automation. It contains the contract -- what a venue
looks like, what it requires, what its constraints are. USEI reads these contracts and implements the adapters.

---

## 3. Browser Automation Architecture (USEI Addition)

### 3.1 Adapter Hierarchy

BaseSportsAdapter (existing)

- OddsAdapter (existing -- odds only)
- BettingAdapter (existing -- API execution)
  - BetfairAdapter, PinnacleAdapter, SmarketsAdapter, MatchbookAdapter, BetdaqAdapter
- BrowserBettingAdapter (NEW -- browser execution)
  - BrowserAdapterUK: Bet365, WilliamHill, Ladbrokes, Coral, PaddyPower, SkyBet...
  - BrowserAdapterUS: DraftKings, FanDuel, BetMGM...
  - BrowserAdapterEU: OneXBet, Unibet...
  - BrowserAdapterAU: Sportsbet, TAB...
  - BrowserAdapterOffshore: Bovada, BetOnline...

### 3.2 BrowserBettingAdapter Base Class Responsibilities

- Playwright browser context management with anti-detection (stealth mode)
- Session lifecycle: login, maintain, refresh, detect expiry
- CAPTCHA handling hooks (2Captcha/Anti-Captcha/hCaptcha solver integration)
- GeoComply/XPoint geolocation compliance (where required)
- Bet slip interaction: navigate to market, enter stake, confirm, capture confirmation
- Withdrawal/deposit automation
- Screenshot capture for audit trail
- Health check: is session alive, is account funded, is venue accessible

### 3.3 Anti-Detection Strategy

| Protection            | Mitigation                                                     |
| --------------------- | -------------------------------------------------------------- |
| Cloudflare            | Stealth Playwright with playwright-extra + stealth plugin      |
| Device fingerprinting | Persistent browser profiles with consistent canvas/WebGL/fonts |
| Behavioral analysis   | Human-like mouse movements, random delays, scroll patterns     |
| IP reputation         | Residential proxy rotation (per-venue sticky sessions)         |
| CAPTCHA               | 2Captcha/Anti-Captcha API integration; human fallback queue    |
| GeoComply             | Requires real device in authorized jurisdiction                |
| Rate limiting         | Respect venue-specific session timeouts, space requests        |
| 2FA                   | TOTP token generation from stored secret; SMS via API          |

---

## 4. Venue Execution Profiles

### 4.1 Tier 1: API-Based Execution (5 venues -- already have adapters)

#### Betfair Exchange

- Odds API keys: betfair_ex_uk, betfair_ex_eu, betfair_ex_au
- Execution: REST API + Stream API
- API base: [https://api.betfair.com/exchange/betting/rest/v1.0/](https://api.betfair.com/exchange/betting/rest/v1.0/)
- Docs: [https://docs.developer.betfair.com/](https://docs.developer.betfair.com/)
- Stream: stream-api.betfair.com:443 (lowest latency)
- Fee: Live App Key GBP 299 one-off; Delayed key free
- Rate limits: 200 weighted data points/cycle; 20 req/s betting; Historical 100 req/10s
- Credentials: API key + session token (SSOID); certificate for non-interactive
- Commission: Up to 5% net profit per market (volume discounts down to 2%)
- Min bet: GBP 2.00
- KYC: Full (ID + address proof)
- Currencies: GBP, EUR, AUD, SEK, DKK, NOK, USD, CAD, HKD, SGD
- Available: UK, EU (most), AU, Asia (select); NOT US
- Withdrawal: Bank transfer, debit card, Skrill, Neteller, PayPal; 1-5 days bank, instant e-wallet
- Account limiting: None (exchange model)
- Notes: Most liquid exchange globally. Stream API essential for arb.

#### Pinnacle

- Odds API key: pinnacle (may have 30s delay on free Odds API tier)
- Execution: REST API (Betting API)
- API base: [https://api.pinnacle.com/](https://api.pinnacle.com/)
- Docs: [https://pinnacleapi.github.io/](https://pinnacleapi.github.io/)
- Rate limits: Lines API 6 req/min per sport
- Credentials: Username + password (HTTP Basic Auth)
- Commission: Built into odds (low vig ~2-3%)
- Min bet: ~USD 1 (varies by sport)
- Max bet: Up to USD 50,000+ on major markets; will NOT restrict winners
- KYC: Full
- Currencies: USD, EUR, GBP, CAD, AUD + 15 more
- Available: EU, Asia, LatAm; NOT US, NOT UK, NOT France, NOT AU
- Withdrawal: Bank, Skrill, Neteller, crypto (BTC, USDT); 1-3 days, crypto 24-48h
- Account limiting: NONE -- Pinnacle famously does not limit or ban winners
- Notes: Industry benchmark sharp lines. CLV reference. Best venue for professionals.

#### Smarkets Exchange

- Odds API key: smarkets
- Execution: REST API (Trading API)
- API base: [https://api.smarkets.com/v3/](https://api.smarkets.com/v3/)
- Docs: [https://docs.smarkets.com/](https://docs.smarkets.com/)
- Credentials: OAuth2 (API token)
- Commission: 2% flat; 0% on Premium (GBP 1500+/month)
- Min bet: GBP 1.00
- Available: UK, EU (select); NOT US
- Withdrawal: Bank, debit card; 1-3 days
- Account limiting: None (exchange model)
- Notes: Free API. Good tennis/politics liquidity.

#### Matchbook Exchange

- Odds API key: matchbook
- Execution: REST API
- API base: [https://api.matchbook.com/edge/rest/](https://api.matchbook.com/edge/rest/)
- Docs: [https://www.matchbook.com/edge/rest](https://www.matchbook.com/edge/rest)
- Rate limits: Free < 1M GET req/month
- Credentials: Username + password (session token)
- Commission: 2% net profit (often 1.5% promo)
- Min bet: GBP 0.10
- Available: UK, EU; NOT US
- Withdrawal: Bank, Skrill; 2-5 days
- Notes: Lower liquidity than Betfair/Smarkets.

#### Betdaq Exchange

- Odds API key: N/A (not in Odds API)
- Execution: REST API (contact for access)
- Credentials: Username + password
- Commission: 2% net profit
- Min bet: GBP 0.50
- Available: UK, Ireland; limited international
- Notes: Strong in horse racing. Fewer markets. Owned by Entain.

### 4.2 Tier 2: Browser Automation Required

#### 4.2.1 US Sportsbooks

All require: state licensing, GeoComply/XPoint geolocation (physical presence), SSN, no public API, Cloudflare +
behavioral anti-bot.

| Venue      | Odds API Key          | Login URL                                                                                        | Anti-Detection                                 | States | Min Bet | Withdrawal Delay | Limits Winners? | Parent         |
| ---------- | --------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------- | ------ | ------- | ---------------- | --------------- | -------------- |
| DraftKings | draftkings            | [https://sportsbook.draftkings.com/](https://sportsbook.draftkings.com/)                         | Aggressive (Cloudflare, device FP, GeoComply)  | ~25+   | $0.10   | 1-5 days         | Moderate        | DraftKings Inc |
| FanDuel    | fanduel               | [https://sportsbook.fanduel.com/](https://sportsbook.fanduel.com/)                               | Aggressive (Cloudflare, behavioral, GeoComply) | ~25+   | $1.00   | 1-5 days         | Moderate        | Flutter        |
| BetMGM     | betmgm                | [https://sports.betmgm.com/](https://sports.betmgm.com/)                                         | Aggressive (Cloudflare, GeoComply)             | ~20+   | $0.10   | 2-5 days         | Moderate        | Entain/MGM     |
| Caesars    | williamhill_us (paid) | [https://www.caesars.com/sportsbook-and-casino/](https://www.caesars.com/sportsbook-and-casino/) | Aggressive (GeoComply)                         | ~20+   | $0.50   | 2-5 days         | Moderate        | Caesars        |
| BetRivers  | betrivers             | [https://www.betrivers.com/](https://www.betrivers.com/)                                         | Moderate (GeoComply)                           | ~15    | $0.50   | 2-5 days         | Mild            | Rush Street    |
| ESPN Bet   | espnbet               | [https://www.espnbet.com/](https://www.espnbet.com/)                                             | Aggressive (GeoComply)                         | ~18    | $1.00   | 2-5 days         | Unknown         | Penn           |
| Hard Rock  | hardrockbet           | [https://www.hardrock.bet/](https://www.hardrock.bet/)                                           | Moderate (GeoComply)                           | ~10    | $1.00   | 2-5 days         | Unknown         | Seminole       |
| Fanatics   | fanatics (paid)       | [https://sportsbook.fanatics.com/](https://sportsbook.fanatics.com/)                             | Moderate (GeoComply)                           | ~20    | $0.50   | 2-5 days         | Unknown         | Fanatics       |

Deposit: Debit card, ACH, PayPal, Venmo, Play+, Apple Pay. No crypto. Limits $10-$25K/tx. Residency: Must be physically
in authorized state (GeoComply real-time). Cannot VPN.

#### 4.2.2 UK Bookmakers

All require: UK GC license, full KYC, no public API, Cloudflare standard.

| Venue         | Odds API Key        | Login URL                                                      | Anti-Detection                                                     | Min Bet  | Max Payout | Withdrawal Delay | Limits Winners? | Parent       |
| ------------- | ------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------ | -------- | ---------- | ---------------- | --------------- | ------------ |
| Bet365        | bet365_au (AU paid) | [https://www.bet365.com/](https://www.bet365.com/)             | EXTREME (Enterprise CF, CAPTCHA, device FP, IP rep, behavioral ML) | GBP 0.10 | GBP 2M     | 1-5 days         | Aggressive      | bet365 Group |
| William Hill  | williamhill         | [https://www.williamhill.com/](https://www.williamhill.com/)   | Moderate-Aggressive                                                | GBP 0.10 | GBP 2M     | 1-5 days         | Aggressive      | 888 Holdings |
| Ladbrokes     | ladbrokes_uk        | [https://sports.ladbrokes.com/](https://sports.ladbrokes.com/) | Moderate                                                           | GBP 0.10 | GBP 1M     | 1-3 days         | Moderate        | Entain       |
| Coral         | coral               | [https://sports.coral.co.uk/](https://sports.coral.co.uk/)     | Moderate                                                           | GBP 0.10 | GBP 1M     | 1-3 days         | Moderate        | Entain       |
| Paddy Power   | paddypower          | [https://www.paddypower.com/](https://www.paddypower.com/)     | Moderate                                                           | GBP 0.10 | EUR 500K   | 1-3 days         | Moderate        | Flutter      |
| Sky Bet       | skybet              | [https://www.skybet.com/](https://www.skybet.com/)             | Aggressive (device FP)                                             | GBP 0.10 | GBP 1M     | 1-3 days         | Moderate        | Flutter      |
| Betway        | betway              | [https://www.betway.com/](https://www.betway.com/)             | Moderate                                                           | GBP 0.10 | GBP 250K   | 1-3 days         | Moderate        | Super Group  |
| 888sport      | sport888            | [https://www.888sport.com/](https://www.888sport.com/)         | Moderate                                                           | GBP 0.10 | GBP 500K   | 1-5 days         | Moderate        | 888 Holdings |
| Bet Victor    | betvictor           | [https://www.betvictor.com/](https://www.betvictor.com/)       | Basic-Moderate                                                     | GBP 0.10 | GBP 500K   | 1-3 days         | Mild            | BV Gaming    |
| BoyleSports   | boylesports         | [https://www.boylesports.com/](https://www.boylesports.com/)   | Basic                                                              | GBP 0.10 | GBP 500K   | 1-3 days         | Mild            | BoyleSports  |
| Betfred       | N/A                 | [https://www.betfred.com/](https://www.betfred.com/)           | Basic-Moderate                                                     | GBP 0.10 | GBP 500K   | 1-3 days         | Mild            | Betfred      |
| Virgin Bet    | virginbet           | [https://www.virginbet.com/](https://www.virginbet.com/)       | Basic                                                              | GBP 0.10 | GBP 250K   | 1-3 days         | Unknown         | Gamesys      |
| LiveScore Bet | livescorebet        | [https://www.livescorebet.com/](https://www.livescorebet.com/) | Basic                                                              | GBP 0.10 | GBP 250K   | 1-3 days         | Unknown         | LiveScore    |

Deposit: Debit card, bank transfer, PayPal, Skrill, Neteller, Apple Pay, Paysafecard. No credit cards (UK regulation
since April 2020). No crypto generally. Account limiting reality: UK books actively monitor for arb. Bet365/William Hill
fastest to limit (1-2 winning sharp bets).

#### 4.2.3 EU Bookmakers

| Venue         | Odds API Key          | Login URL                                                                            | Anti-Detection | Jurisdictions                | Min Bet  | Withdrawal Delay           | Limits Winners? | Parent     |
| ------------- | --------------------- | ------------------------------------------------------------------------------------ | -------------- | ---------------------------- | -------- | -------------------------- | --------------- | ---------- |
| 1xBet         | onexbet               | [https://1xbet.com/](https://1xbet.com/)                                             | Moderate       | Curacao; blocked UK/US/FR/AU | EUR 0.20 | 1-5 days; crypto 15min-24h | Moderate        | 1X Corp    |
| Unibet        | unibet_uk/fr/it/nl/se | [https://www.unibet.com/](https://www.unibet.com/)                                   | Moderate (CF)  | UK GC, MGA, regional         | EUR 0.10 | 1-3 days                   | Moderate        | Kindred    |
| Betsson       | betsson               | [https://www.betsson.com/](https://www.betsson.com/)                                 | Basic-Moderate | MGA, Sweden                  | EUR 0.10 | 1-3 days                   | Mild            | Betsson AB |
| Marathon      | marathonbet           | [https://www.marathonbet.com/](https://www.marathonbet.com/)                         | Basic          | Curacao, UK GC               | EUR 0.10 | 1-3 days                   | Mild            | Marathon   |
| Winamax       | winamax_fr/de         | [https://www.winamax.fr/](https://www.winamax.fr/)                                   | Moderate       | ANJ (France)                 | EUR 0.10 | 1-3 days                   | Mild            | Winamax    |
| Betclic       | betclic_fr            | [https://www.betclic.fr/](https://www.betclic.fr/)                                   | Basic          | ANJ, Portugal                | EUR 0.10 | 1-3 days                   | Mild            | Betclic    |
| Tipico        | tipico_de             | [https://www.tipico.de/](https://www.tipico.de/)                                     | Moderate       | Germany (GGL)                | EUR 0.10 | 1-3 days                   | Mild            | Tipico     |
| Coolbet       | coolbet               | [https://www.coolbet.com/](https://www.coolbet.com/)                                 | Basic          | MGA, Estonia                 | EUR 0.10 | 1-3 days                   | Mild            | GAN        |
| NordicBet     | nordicbet             | [https://www.nordicbet.com/](https://www.nordicbet.com/)                             | Basic          | MGA, Denmark                 | EUR 0.10 | 1-3 days                   | Mild            | Betsson AB |
| Suprabets     | suprabets             | [https://www.suprabets.com/](https://www.suprabets.com/)                             | Basic          | Curacao                      | EUR 0.10 | 1-5 days                   | Unknown         | N/A        |
| Everygame     | everygame             | [https://www.everygame.eu/](https://www.everygame.eu/)                               | Basic          | Antigua                      | USD 1.00 | 2-7 days                   | Mild            | Everygame  |
| GTbets        | gtbets                | [https://www.gtbets.eu/](https://www.gtbets.eu/)                                     | Basic          | Curacao                      | USD 1.00 | 3-7 days                   | Unknown         | N/A        |
| Parions Sport | parionssport_fr       | [https://www.enligne.parionssport.fdj.fr/](https://www.enligne.parionssport.fdj.fr/) | Moderate       | ANJ (France only)            | EUR 1.00 | 1-3 days                   | Mild            | FDJ        |
| PMU           | pmu_fr                | [https://paris-sportifs.pmu.fr/](https://paris-sportifs.pmu.fr/)                     | Moderate       | ANJ (France only)            | EUR 1.00 | 1-3 days                   | Mild            | PMU        |
| LeoVegas      | leovegas/leovegas_se  | [https://www.leovegas.com/](https://www.leovegas.com/)                               | Basic          | MGA, UK GC, Sweden           | EUR 0.10 | 1-3 days                   | Mild            | MGM        |
| bwin          | N/A                   | [https://sports.bwin.com/](https://sports.bwin.com/)                                 | Moderate (CF)  | GRA, MGA                     | EUR 0.10 | 1-3 days                   | Moderate        | Entain     |

1xBet: Accepts 50+ cryptos. Fast crypto withdrawals. No residency. Good for arb (high limits, crypto speed). French ANJ:
Betclic, Parions Sport, PMU, Winamax, Unibet FR require French residency + bank. Swedish: LeoVegas SE, Betsson SE,
NordicBet SE require Swedish residency.

#### 4.2.4 AU Bookmakers

All require: AU residency, no in-play online betting (phone only), no credit cards, state-licensed.

| Venue        | Odds API Key     | Login URL                                                      | Min Bet | Withdrawal Delay | Limits Winners? | Parent         |
| ------------ | ---------------- | -------------------------------------------------------------- | ------- | ---------------- | --------------- | -------------- |
| Sportsbet    | sportsbet        | [https://www.sportsbet.com.au/](https://www.sportsbet.com.au/) | AUD 1   | 1-3 days         | Moderate        | Flutter        |
| TAB          | tab              | [https://www.tab.com.au/](https://www.tab.com.au/)             | AUD 1   | 1-3 days         | Mild            | Tabcorp/Entain |
| TABtouch     | tabtouch         | [https://www.tabtouch.com.au/](https://www.tabtouch.com.au/)   | AUD 1   | 1-3 days         | Mild            | RWWA           |
| Neds         | neds             | [https://www.neds.com.au/](https://www.neds.com.au/)           | AUD 1   | 1-3 days         | Moderate        | Entain         |
| PointsBet AU | pointsbetau      | [https://www.pointsbet.com.au/](https://www.pointsbet.com.au/) | AUD 1   | 1-3 days         | Moderate        | PointsBet      |
| Ladbrokes AU | ladbrokes_au     | [https://www.ladbrokes.com.au/](https://www.ladbrokes.com.au/) | AUD 1   | 1-3 days         | Moderate        | Entain         |
| Bet365 AU    | bet365_au (paid) | [https://www.bet365.com.au/](https://www.bet365.com.au/)       | AUD 1   | 1-3 days         | Aggressive      | bet365         |
| PlayUp       | playup           | [https://www.playup.com.au/](https://www.playup.com.au/)       | AUD 1   | 1-3 days         | Unknown         | PlayUp         |
| Betfair AU   | betfair_ex_au    | [https://www.betfair.com.au/](https://www.betfair.com.au/)     | AUD 5   | 1-3 days         | None            | Flutter        |
| Betr AU      | betr_au          | [https://www.betr.com.au/](https://www.betr.com.au/)           | AUD 1   | 1-3 days         | Unknown         | News Corp      |
| Bet Right    | betright         | [https://www.betright.com.au/](https://www.betright.com.au/)   | AUD 1   | 1-3 days         | Unknown         | BlueBet        |
| Dabble       | dabble_au (paid) | [https://www.dabble.com.au/](https://www.dabble.com.au/)       | AUD 1   | 1-3 days         | Unknown         | Dabble         |

AU arb constraint: In-play betting restricted to phone. Pre-match arb only.

#### 4.2.5 Offshore / Caribbean Books

| Venue        | Odds API Key | Login URL                                                    | Anti-Detection | Crypto                   | Withdrawal Delay           | Limits Winners?  |
| ------------ | ------------ | ------------------------------------------------------------ | -------------- | ------------------------ | -------------------------- | ---------------- |
| Bovada       | bovada       | [https://www.bovada.lv/](https://www.bovada.lv/)             | Moderate       | BTC, BCH, ETH, USDT, LTC | Crypto 24-48h; Wire 10-15d | Mild; max ~$100K |
| BetOnline    | betonlineag  | [https://www.betonline.ag/](https://www.betonline.ag/)       | Moderate       | BTC, ETH, LTC, USDT+     | Crypto 24-48h; Wire 5-10d  | Mild             |
| MyBookie     | mybookieag   | [https://www.mybookie.ag/](https://www.mybookie.ag/)         | Moderate       | BTC, ETH, LTC, USDT      | Crypto 48-72h; Wire 5-10d  | Moderate         |
| BetUS        | betus        | [https://www.betus.com.pa/](https://www.betus.com.pa/)       | Basic          | BTC, ETH, LTC            | Crypto 48-72h; Wire 7-14d  | Moderate         |
| LowVig       | lowvig       | [https://www.lowvig.ag/](https://www.lowvig.ag/)             | Basic          | BTC, ETH                 | Crypto 24-48h              | Unknown          |
| BetAnySports | betanysports | [https://www.betanysports.eu/](https://www.betanysports.eu/) | Basic          | BTC                      | Crypto 24-72h              | Mild             |

Offshore notes: No US state licensing (regulatory grey zone). Crypto best method. Bovada ~$3K/wk limit; BetOnline
$5-25K. Avoid bonuses for arb (rollover requirements).

---

## 5. Odds API to Execution Mapping

### 5.1 Priority Mapping

| Odds API Key        | Execution Method | Adapter Status      | Priority               |
| ------------------- | ---------------- | ------------------- | ---------------------- |
| betfair_ex_uk/eu/au | REST API         | EXISTS              | P0 done                |
| pinnacle            | REST API         | EXISTS              | P0 done                |
| smarkets            | REST API         | EXISTS (not routed) | P0 wire into router    |
| matchbook           | REST API         | EXISTS (not routed) | P0 wire into router    |
| polymarket          | REST API         | EXISTS              | P0 done                |
| draftkings          | Browser          | NOT BUILT           | P1 high liquidity US   |
| fanduel             | Browser          | NOT BUILT           | P1 high liquidity US   |
| betmgm              | Browser          | NOT BUILT           | P1 high liquidity US   |
| williamhill_us      | Browser          | NOT BUILT           | P1 US Caesars          |
| bet365_au           | Browser          | SCRAPER (odds only) | P1 hardest anti-bot    |
| bovada              | Browser          | NOT BUILT           | P1 top US offshore     |
| betonlineag         | Browser          | NOT BUILT           | P1 US offshore         |
| williamhill         | Browser          | SCRAPER (odds only) | P2 UK                  |
| ladbrokes_uk        | Browser          | SCRAPER (odds only) | P2 UK                  |
| coral               | Browser          | SCRAPER (odds only) | P2 UK                  |
| paddypower          | Browser          | SCRAPER (odds only) | P2 UK                  |
| skybet              | Browser          | SCRAPER (odds only) | P2 UK                  |
| sport888            | Browser          | SCRAPER (odds only) | P2 UK/EU               |
| betway              | Browser          | SCRAPER (odds only) | P2 UK                  |
| unibet              | Browser          | SCRAPER (odds only) | P2 multi-region        |
| onexbet             | Browser/API      | ADAPTER (odds only) | P2 has unofficial API  |
| betvictor           | Browser          | SCRAPER (odds only) | P3 UK                  |
| boylesports         | Browser          | SCRAPER (odds only) | P3 UK/IE               |
| betrivers           | Browser          | NOT BUILT           | P3 US secondary        |
| espnbet             | Browser          | NOT BUILT           | P3 US secondary        |
| mybookieag          | Browser          | NOT BUILT           | P3 offshore            |
| betus               | Browser          | NOT BUILT           | P3 offshore            |
| sportsbet           | Browser          | NOT BUILT           | P3 AU primary          |
| tab                 | Browser          | NOT BUILT           | P3 AU primary          |
| neds                | Browser          | NOT BUILT           | P3 AU                  |
| pointsbetau         | Browser          | NOT BUILT           | P3 AU                  |
| ladbrokes_au        | Browser          | NOT BUILT           | P3 AU                  |
| All remaining       | Browser          | NOT BUILT           | P4 coverage completion |

### 5.2 Execution Coverage Roadmap

| Phase   | Venues Added                                                   | Cumulative | Arb Potential             |
| ------- | -------------------------------------------------------------- | ---------- | ------------------------- |
| Current | 6 (Betfair, Pinnacle, Smarkets, Matchbook, Betdaq, Polymarket) | ~8%        | Exchange-to-exchange only |
| P0      | +0 (wire Smarkets/Matchbook/Betdaq into router)                | ~8%        | Same, properly routed     |
| P1      | +8 (DK, FD, BetMGM, Caesars, Bet365, Bovada, BetOnline, ESPN)  | ~20%       | Cross-venue arb unlocked  |
| P2      | +12 (UK + EU major books)                                      | ~45%       | Full UK/EU arb            |
| P3      | +10 (AU + US secondary + offshore)                             | ~60%       | Global arb                |
| P4      | +remaining                                                     | ~90%+      | Comprehensive             |

---

## 6. Financial and Operational Considerations

### 6.1 Capital Allocation by Venue Type

| Type                                     | Allocation | Rationale                                       |
| ---------------------------------------- | ---------- | ----------------------------------------------- |
| Exchanges (Betfair, Smarkets, Matchbook) | 40%        | Deepest liquidity, no limiting, commission-only |
| Sharp books (Pinnacle)                   | 20%        | No limits on winners, benchmark odds, API       |
| Soft books (US sportsbooks)              | 20%        | High limits but will restrict winners           |
| Offshore (Bovada, BetOnline)             | 10%        | Crypto settlement, moderate limits              |
| Regional (AU, EU secondary)              | 10%        | Coverage depth, niche markets                   |

### 6.2 Account Lifecycle (Soft Books)

1. New account: Full limits, normal patterns
2. Warming: Natural activity 2-4 weeks (recreational bets)
3. Exploitation: Selective arb, target 3-5% ROI/month
4. Restriction: Reduced max stakes detected
5. Recycling: New account or accept limits

Track per-account: max stake observed, restriction signals, lifetime PnL.

### 6.3 Settlement Speed Matrix

| Method                     | Speed       | Best For           |
| -------------------------- | ----------- | ------------------ |
| Crypto (BTC/ETH/USDT)      | 15min-24h   | Offshore, 1xBet    |
| E-wallet (Skrill/Neteller) | Instant-24h | UK/EU              |
| PayPal                     | Instant-24h | US where available |
| Debit card                 | 1-3 days    | UK                 |
| ACH                        | 2-5 days    | US                 |
| SEPA                       | 1-3 days    | EU                 |
| Wire                       | 5-15 days   | Offshore (avoid)   |

### 6.4 Key Risks

| Risk                         | Severity | Mitigation                                             |
| ---------------------------- | -------- | ------------------------------------------------------ |
| Account restriction/closure  | High     | Warming, pattern diversification, multi-account        |
| Geolocation enforcement (US) | High     | Physical presence required; cannot VPN                 |
| Anti-bot during execution    | High     | Stealth browser, human interaction, CAPTCHA solving    |
| Partial fill (one leg only)  | Critical | Concurrent engine <2s; hedging strategy                |
| Settlement delay mismatch    | Medium   | Crypto for offshore; e-wallet for UK/EU                |
| Regulatory change            | Medium   | Multi-jurisdiction diversification                     |
| Odds staleness (API 5-10min) | High     | Supplement with direct scraping for time-sensitive arb |

---

## 7. Integration Points

### 7.1 Data Flow

Odds API (aggregated) + Exchange APIs (live) -> features-sports-service -> Arb Detection Engine -> strategy-service (arb
signal) -> unified-sports-execution-interface -> API adapters (Betfair, Pinnacle) + Browser adapters (DraftKings,
Bet365) -> Venue A (back) + Venue B (lay/back)

### 7.2 What Goes Where

| Component                    | Repo                                                    | Content                 |
| ---------------------------- | ------------------------------------------------------- | ----------------------- |
| VenueExecutionProfile schema | UAC canonical/domain/sports/                            | Schema definition       |
| Per-venue profile data       | UAC canonical/domain/sports/venue_execution_registry.py | Static data             |
| Odds API key mapping         | UAC canonical/domain/sports/odds_api_mapping.py         | Mapping data            |
| Browser adapter base         | USEI adapters/browser/                                  | Execution logic         |
| Per-venue adapters           | USEI adapters/browser/{region}/                         | Per-venue logic         |
| Credential configs           | UCfgI                                                   | Secret Manager fields   |
| Execution events             | UIC                                                     | Internal event schemas  |
| Arb detection                | features-sports-service                                 | Feature calculation     |
| Arb strategy                 | strategy-service                                        | Strategy logic          |
| Order routing                | USEI routing.py                                         | Execution orchestration |

---

## 8. Odds API Full Reference

### 8.1 All Bookmaker Keys by Region

US: betonlineag, betmgm, betrivers, betus, bovada, williamhill_us (paid), draftkings, fanatics (paid), fanduel, lowvig,
mybookieag US2: ballybet, betanysports, betparx, espnbet, fliff, hardrockbet, rebet (paid) US Exchanges: betopenly,
kalshi, novig, polymarket, prophetx US DFS: betr_us_dfs, pick6, prizepicks, underdog UK: sport888, betfair_ex_uk,
betfair_sb_uk, betvictor, betway, boylesports, casumo, coral, grosvenor, ladbrokes_uk, leovegas, livescorebet,
matchbook, paddypower, skybet, smarkets, unibet_uk, virginbet, williamhill EU: onexbet, sport888, betclic_fr,
betanysports, betfair_ex_eu, betonlineag, betsson, codere_it, betvictor, coolbet, everygame, gtbets, leovegas_se,
marathonbet, matchbook, mybookieag, nordicbet, parionssport_fr, pinnacle, pmu_fr, suprabets, tipico_de,
unibet_fr/it/nl/se, williamhill, winamax_de/fr AU: betfair_ex_au, betr_au, betright, bet365_au (paid), dabble_au (paid),
ladbrokes_au, neds, playup, pointsbetau, sportsbet, tab, tabtouch, unibet FR: betclic_fr, netbet_fr, parionssport_fr,
pmu_fr, unibet_fr, winamax_fr SE: atg_se, betsson, leovegas_se, mrgreen_se, nordicbet, sport888_se, svenskaspel_se,
unibet_se

### 8.2 Rate Limits and Pricing

- 30 calls/second (HTTP 429 if exceeded)
- Credits: live odds 1/region/market; historical 10/region/market
- Free: 500 credits/month
- 20K: $30/mo; 100K: $59/mo; 5M: $119/mo; 15M: $249/mo

### 8.3 Sports Coverage

80+ sport keys: American Football (NFL, NCAAF, CFL, UFL), Aussie Rules (AFL), Baseball (MLB, NPB, KBO, NCAA), Basketball
(NBA, WNBA, NCAAB, EuroLeague, NBL), Boxing, Cricket (20+ formats), Golf (4 majors), Handball, Ice Hockey (NHL, AHL,
SHL, Liiga), Lacrosse, MMA, Politics, Rugby, Soccer (50+ leagues), Tennis (all ATP/WTA).

---

## 9. Phased Execution Summary

| Phase | Description                   | Todos | Effort | Blocker               |
| ----- | ----------------------------- | ----- | ------ | --------------------- |
| P0    | Schema + profiles             | 3     | M      | Citadel arch complete |
| P1    | Browser infra + router        | 2     | L      | P0                    |
| P2    | Venue adapters (5 batches)    | 5     | XL     | P1 + live accounts    |
| P3    | Arb integration + config      | 2     | M      | P0                    |
| P4    | Health + concurrent execution | 2     | L      | P2                    |

Human-required: account creation (KYC), physical US presence for GeoComply, funding, live site verification, withdrawal
testing, restriction monitoring.

AI-doable: schema creation, profile data, adapter scaffolds, anti-detection framework, integration wiring, mocked test
scaffolds.

---

## 10. Advanced Strategy Infrastructure

### 10.1 CLV Tracking (Closing Line Value)

CLV is the single most important metric for validating sports betting models. If your bets consistently beat the closing
line (the final odds before an event starts, typically at Pinnacle), you have a genuine edge regardless of short-term
variance.

**Schema additions to UAC `betting.py`:**

- `odds_at_placement`: Decimal — odds when bet was placed
- `closing_odds`: Decimal | None — Pinnacle closing line (populated post-event)
- `clv_edge_pct`: Decimal | None — (closing_implied_prob - placement_implied_prob) / closing_implied_prob
- `closing_line_source`: str | None — which book provided the closing line (default: "pinnacle")

**New schema: CLVRecord** — tracks historical CLV for model validation:

- Aggregates by model_version, sport, market_type, bookmaker, time_period
- Calculates: mean_clv, median_clv, hit_rate (% of bets that beat closing line)
- This is the primary performance attribution metric (more reliable than P&L over <1000 bets)

**Integration:**

- `features-sports-service` → captures closing odds at event start from Pinnacle API
- `pnl-attribution-service` → joins execution records with closing odds for CLV calculation
- Strategy dashboard → CLV trend is the health metric for the entire sports operation

### 10.2 Exchange Market Making

Market making on Betfair/Smarkets is structurally identical to market making in crypto/equity. Post back AND lay at a
spread. Capture the difference minus commission.

**Why it works for sports:**

- Exchanges never limit market makers (unlike bookmakers who limit winners)
- Commission is the only cost (Betfair: 2-5% of net winnings)
- Deep liquidity on major events (EPL, NFL, horse racing)
- Matching-engine-library already has L2 order book management

**Architecture:**

- `SportsMarketMakingStrategy` in strategy-service — spread calculation, inventory risk management
- MEL `L2Matcher` for order book state tracking
- USEI Betfair Stream API for real-time order book depth and execution
- Risk limits: max position per market, max inventory imbalance, kill switch on rapid movement

**Key parameters:**

- Spread width (ticks above/below mid)
- Position limits (max exposure per selection)
- Inventory skew (adjust quotes based on current position)
- Cancel-on-event triggers (pull all quotes at kickoff/result)

### 10.3 Cross-Asset Sports-Financial Feature Bridge

The unique advantage of the unified trading system: sports features feed into financial market strategies and vice
versa.

**Sports → Financial signals:**

- Team ownership stocks move on results (MANU, JUVE.MI, BVB.DE)
- Event economics: World Cup → hospitality, airlines, local FX
- Weather features → cricket/tennis AND commodity futures
- Player transfers → club stocks AND prediction markets
- Sponsorship performance → consumer brand sentiment

**Financial → Sports signals:**

- Sharp money in financial betting markets (Kalshi, Polymarket) → leading indicator for sports odds
- Insider trading patterns in team stocks before results
- Options flow on event-sensitive stocks

**Implementation:**

- `features-cross-instrument-service` gets a `sports_bridge` module
- Input: `features-sports-service` publishes derived features to PubSub
- `features-cross-instrument-service` subscribes and correlates with financial features
- Output: cross-asset signals published to strategy-service

### 10.4 Multi-Account Management

World-class arb requires 50-100+ accounts across books. Each with its own identity, payment method, and betting pattern.
Accounts have lifecycle stages.

**Account lifecycle states:**

- `warmup` — New account, recreational betting patterns, 2-4 weeks
- `active` — Selective arb/value betting, target 3-5% ROI/month
- `restricted` — Max stakes reduced by book, detected as sharp
- `suspended` — Account suspended or locked
- `recycled` — New account created, old account data preserved for analysis

**Schema: SportsVenueAccountConfig (extends SportsVenueCredentialConfig):**

- `account_id`: unique identifier for this specific account
- `account_alias`: human-readable name
- `lifecycle_state`: warmup | active | restricted | suspended | recycled
- `max_observed_stake`: Decimal — highest stake the book accepted
- `last_restriction_date`: date | None
- `lifetime_pnl`: Decimal
- `warmup_start_date`: date
- `warmup_complete_date`: date | None
- `payment_method`: str (crypto, e-wallet, card)
- `identity_profile`: str — which identity set this account uses

### 10.5 Enhanced Kelly Criterion

The existing KellyCriterionStrategy handles single-bet sizing. World-class operation needs:

**Portfolio Kelly (correlated bets):**

- When you have N simultaneous bets, some outcomes are correlated
- e.g., two arb legs are perfectly negatively correlated — both winning is impossible
- Portfolio Kelly optimizes the joint allocation, not each bet independently
- Requires covariance matrix of bet outcomes

**Simultaneous Kelly (bankroll sharing):**

- With 20 open bets, each using Kelly, total exposure can exceed 100%
- Simultaneous Kelly allocates from remaining bankroll after accounting for open positions
- Prevents over-leveraging from concurrent opportunities

**Venue-specific limits:**

- VenueExecutionProfile.max_bet_per_market caps the Kelly output per venue
- Account-level max_observed_stake further constrains
- Different Kelly fraction per venue (lower for books that limit, higher for exchanges)

### 10.6 Steam Move Detection

Sharp money moves lines. The fastest detection wins.

**Pattern:**

1. Pinnacle line moves >2% in <5 minutes (steam move detected)
2. Check all soft books for stale lines
3. If soft book still at old line → execute immediately
4. Window: seconds to minutes (depends on how fast the book adjusts)

**Implementation:**

- `features-sports-service` calculator: `steam_detector.py`
- Input: Pinnacle Stream API + Odds API snapshot
- Output: `SteamMoveSignal` with venue, direction, magnitude, staleness_seconds
- Strategy-service consumes signal and routes to USEI for execution on stale books

### 10.7 In-Play Trading

The highest-alpha strategy. Requires:

- Sub-second odds streaming (Betfair Stream API, direct scraping)
- Real-time feature calculation (xG, momentum, possession changes)
- Fast ML inference (pre-loaded model, batch predictions per state change)
- Exchange execution only (Betfair — no books accept in-play browser bets at speed)

This is a [HUMAN+AGENT] effort: data feed setup requires commercial agreements.

---

## 11. Strategy Priority Matrix (Updated)

| Priority | Strategy                    | Edge           | Sustainability          | System Readiness            |
| -------- | --------------------------- | -------------- | ----------------------- | --------------------------- |
| P0       | CLV Betting (ML prediction) | 3-8%           | High (model-dependent)  | ML pipeline exists          |
| P0       | Exchange Market Making      | 2-5% on volume | Very High (no limiting) | MEL + Betfair adapter exist |
| P1       | In-Play Trading             | 5-15%          | Very High               | Needs live data feeds       |
| P1       | Cross-Asset Correlation     | Variable       | Unique edge             | System uniquely positioned  |
| P2       | Steam Move Exploitation     | 2-5%           | Decaying                | Needs sub-minute detection  |
| P2       | Arbitrage                   | 1-3%           | Low (accounts limited)  | Just built infrastructure   |
| P3       | Middle Betting              | 0.5-2%         | Moderate                | Strategy extension          |
| P3       | Prop Market Inefficiency    | 2-5%           | High                    | ML pipeline + prop data     |

---

## 12. Phased Execution Summary (Updated)

| Phase | Description                          | Todos | Effort | Blocker               |
| ----- | ------------------------------------ | ----- | ------ | --------------------- |
| P0    | Schema + profiles                    | 3     | M      | Citadel arch complete |
| P1    | Browser infra + router               | 2     | L      | P0                    |
| P2    | Venue adapters (5 batches)           | 5     | XL     | P1 + live accounts    |
| P3    | Arb integration + config             | 2     | M      | P0                    |
| P4    | Health + concurrent execution        | 2     | L      | P2                    |
| P5    | CLV + Multi-account + Enhanced Kelly | 3     | M      | P0                    |
| P5    | Exchange MM + Cross-asset bridge     | 2     | L      | P2                    |
| P6    | Steam + Middles + In-play            | 3     | L-XL   | P5                    |
