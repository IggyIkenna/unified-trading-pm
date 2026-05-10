---
name: wallet-treasury-client-flow-post-trade-readiness
overview: End-to-end client lifecycle — onboarding (deposit + KYC + API keys + risk preferences + share-class subscription) → treasury / wallet / custody (Copper + CEFFU + DeFi wallet PK + exchange sub-accounts + on-chain wallets) → working-capital movement → strategy allocation across 50+ archetypes × share-class derivatives → post-trade settlement + reconciliation + fee accrual + performance-fee crystallization + statements + reporting. Across DeFi + CeFi + TradFi + sports + prediction. Is the full flow mapped + are per-archetype × per-share-class permutations covered?
type: question
status: drafting
created: 2026-05-08
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-08
spawned_plan: null
related_codex:
  - codex/04-architecture/interface-credential-convention.md
  - codex/04-architecture/flash-loan-receiver.md
  - codex/02-data/availability-manifest-and-data-status.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/defi_master_2026_05_07.md
  - plans/epics/cefi_master_2026_05_07.md
  - plans/epics/tradfi_master_2026_05_07.md
  - plans/epics/sports_master_2026_05_07.md
  - plans/epics/predictions_master_2026_05_07.md
  - plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md
  - plans/questions/defi_readiness_catalogue_2026_05_08.md
  - plans/questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md
---

# Wallet / treasury / client-account flow + post-trade readiness — across all asset groups + all 50+ archetypes × share-class derivatives

## Intent

The May-23 cutover brings two DeFi archetypes live on a real wallet for ≥7 continuous days. That's a single archetype
pair on a single client / single share-class / single wallet. **The full system is supposed to be a multi-client,
multi-archetype, multi-share-class, multi-asset-group asset manager** — 50+ strategy archetypes spanning DeFi + CeFi +
TradFi + sports + prediction, each with a fan-out of share-class derivatives (different base currency, different
fee class, different leverage cap, different hedging mode, different jurisdiction, different liquidity profile,
retail-vs-accredited, etc.). Every client onboarded brings their own deposit currency, custody preference, risk
preferences, jurisdictional constraints, share-class subscription, and (for external-strategy clients) their own venue
API keys + strategy declarations.

The operator's worry: **the full client lifecycle — from "client deposits assets + signs an IMA" through "client
withdraws + receives final statement" — is probably NOT end-to-end mapped today**, even though chunks of it exist
(DeFi wallet PK custody, CeFi exchange API key handling, position-balance-monitor, execution-service, the upcoming
client-reporting + invoicing surface). The pieces exist as standalone modules; what's missing is the
**client-account-as-a-first-class-citizen flow** that walks every asset / venue / chain / strategy / share-class
through deposit → custody → allocation → trading → settlement → reporting → withdrawal as one composable pipeline.

This question doc is the cross-cutting framing that demands an audit of the **end-to-end flow**, not a
per-component readiness check. Component-level readiness checks live in sibling question docs:

- **Credentials + wallets + accounts inventory** —
  [`api_keys_wallets_accounts_readiness_2026_05_08.md`](api_keys_wallets_accounts_readiness_2026_05_08.md). That doc
  owns the **inventory side** (every API key, wallet, IAM role, custody endpoint); this doc owns the
  **client-account-attached lifecycle** that consumes those credentials per (client, share-class, archetype).
- **DeFi venue + protocol + chain readiness** —
  [`defi_readiness_catalogue_2026_05_08.md`](defi_readiness_catalogue_2026_05_08.md). That doc owns **what we trade**;
  this doc owns **whose money moves through what we trade**.
- **Codex vs Citadel infrastructure audit** —
  [`codex_vs_citadel_infrastructure_specs_2026_05_08.md`](codex_vs_citadel_infrastructure_specs_2026_05_08.md). That
  doc owns the **target-state architecture**; this doc surfaces the client-lifecycle gaps that must be in any
  target-state.

The 4 question docs together form a coherent operating-model audit. This one is the connective tissue: who can deposit
what, into what custody, allocated by what rule to which archetype × share-class, executed where, settled how, reported
how, withdrawn how — **for every (asset_group, venue, archetype, share-class) tuple the system claims to support**.

## Question

### Block A — Client onboarding (deposit + KYC + API keys + risk preferences + share-class subscription)

A1. **Is there a canonical "client" entity in the system today?** What repo + table / collection / Firestore document
defines a `Client` (or `Account` / `Investor` / `Subscriber` / whatever the SSOT term is)? Is it modeled in UAC under
`unified_api_contracts.canonical.crosscutting.client` (or equivalent), or is it ad-hoc per-service? If the latter, how
many parallel definitions exist (one in deployment-api, one in execution-service, one in the UI Firebase auth claims,
etc.)?

A2. **Onboarding intake surface** — for a NEW client, what's the path from "person wants to invest" to "client is
trading"?
  - Is there a self-serve onboarding UI in `unified-trading-system-ui` (or a separate admin UI), or is it
    operator-driven (Ikenna manually creates the client record + provisions accounts)?
  - What KYC / AML checks are wired (third-party provider integration, document upload + review, sanctions screening),
    or is KYC explicitly out of scope for the current client model (institutional-only / accredited-only / Ikenna's own
    capital + named friends-and-family)?
  - What jurisdictional gating logic exists (per-country availability of certain archetypes / share-classes / venues
    based on regulatory regime)? E.g. US clients can't trade Polymarket; EU clients can't access certain DeFi
    protocols post-MiCA; KYC tier determines which share-classes are available.
  - What investor-suitability / risk-questionnaire intake captures the client's risk preferences (max drawdown
    tolerance, leverage cap, asset-group exclusions like "no DeFi" or "no sports", liquidity preferences, holding-period
    expectations)? Where does this live as data, and which downstream component reads it?
  - How does the client signal **which share-class they're subscribing to** (form selection, IMA terms, default per
    risk-tier)? How does the system bind the client → share-class relationship as data?

A3. **Deposit intake per asset_group + currency**:
  - **Fiat** (USD / EUR / GBP / JPY) — wire instructions per banking rail (Wise / SVB-successor / a prime broker's
    cash management / a stablecoin on-ramp like Circle's CCTP). Per-jurisdiction banking partners. Reconciliation: when
    a wire arrives at the bank, how does the client's account balance get credited (manual operator entry, bank API
    pull, ledger-service reconciliation job)? What's the SLA from wire-arrival to credited?
  - **Stablecoins** (USDC / USDT / DAI / PYUSD on Ethereum + Arbitrum + Base + Polygon + Solana + Tron + Avalanche +
    others) — per-chain per-asset deposit address, per-client unique address (vault per client) vs shared address with
    memo / tag, deposit confirmation thresholds, reconciliation between on-chain receipt and client-account credit.
  - **Crypto natives** (BTC / ETH / SOL / etc.) — same as stablecoins, plus cross-chain wrapping decisions
    (does USDC-on-Solana auto-route to USDC-on-Ethereum if the client's allocated archetype runs on Ethereum, or does
    the client choose deposit chain == working chain?). Bridging cost + slippage + bridge-risk preference.
  - **LSTs / LRTs as deposit** — does the system accept stETH / rETH / jitoSOL / weETH / ezETH as deposits, or does it
    require unwinding to ETH/SOL first? If it accepts, how are they valued at deposit (fair-value oracle vs face-value
    vs day-1 mark)?
  - **In-kind transfers from prior managers** (TradFi-style) — securities / futures positions transferred via prime
    broker. Out of scope, or supported?

A4. **Client-supplied venue API keys** (the "external strategy" / signal-leasing surface) — for clients running their
own strategies but wanting our infrastructure for execution / risk / reporting:
  - How does the client securely deliver venue API keys to the system (UI form with E2E encryption, hardware-token
    enrollment, dedicated client portal, operator-side intake via secure channel)?
  - Where do the keys land (Secret Manager per client_id, custody provider's vault, HashiCorp Vault, encrypted
    Firestore field)? Per the workspace `ApiKeyReloader` pattern from CLAUDE.md, there's a hot-reload path for
    workspace-owned keys — does it generalise to per-client keys, or is per-client a separate path?
  - What's the per-client-API-key permission scope contract? (Read-only for reporting / position pull. Trade-enabled for
    signal-leasing strategy. No-withdrawal for safety.) Is the system enforcing this at intake (rejecting keys with
    withdrawal scope as a tripwire), or trusting the client?
  - Per-venue: which venues' API key intake is wired today (Bybit + Binance + OKX + Deribit + Hyperliquid + Aster +
    Polymarket + Kalshi + bookmakers via odds_api?), and which are stub / not-yet-wired?
  - Signal-leasing flow per CLAUDE.md "Signal Leasing / strategy-service signal broadcast" — external counterparty
    signal emission uses HMAC signing + ApiKeyReloader. Is this wired client-by-client, or is the client-account model
    distinct from the signal-leasing counterparty model? (I.e. is "client subscribed to share-class X" the same record
    as "external counterparty receiving signals via HMAC"?)

A5. **Risk preferences as data** — the risk questionnaire output (or operator-set per-client overrides) needs to be
data the strategy + risk + execution stack reads at decision time:
  - Per-client risk envelope: max gross exposure, max net exposure, max leverage, per-asset-group caps (no more than X%
    in DeFi, no more than Y% in any single venue, no concentration above Z% in any single instrument), VaR cap,
    drawdown trigger (auto-deleverage if peak-to-trough > P%), hedging mandate (must always be net delta-zero / always
    have a fixed hedge ratio / freeform).
  - Where does this envelope live (UAC `ClientRiskProfile` type? Firestore client document? Risk-and-exposure-service
    config?). How does the strategy / risk / execution stack consume it (per-tick read vs cached + reload-on-update)?
  - Is there a versioned audit trail when the operator or client changes the envelope (so we can replay "what was the
    leverage cap on date X")?
  - Does the per-client risk envelope feed into pre-flight risk checks at execution-service, or is risk a post-trade
    monitor only today?

A6. **Share-class subscription as data** — every client is subscribed to one or more share-classes (e.g. "Class A
USD-denominated, 2/20 fee, monthly liquidity, max-drawdown 15%" vs "Class F SOL-denominated, 0/30 fee, quarterly
liquidity, no-drawdown-cap, accredited-only"):
  - Where is the share-class catalogue defined as data? UAC `ShareClass` registry? PM doc? Operator-side spreadsheet
    that doesn't exist as code yet?
  - What attributes define a share-class? (Base currency, hedging mode, fee structure (mgmt + perf + crystallization
    period + high-water-mark), liquidity terms (subscription cadence, redemption cadence, gate / lock-up), eligibility
    (accredited / institutional / retail / per-jurisdiction), strategy-allocation overrides (which subset of the 50+
    archetypes is in scope for this class).)
  - When a client subscribes, what data record links Client × ShareClass × subscription_amount × subscription_date ×
    high-water-mark-anchor? Is it a `Subscription` table / collection? Is it queryable for "show me all subscriptions
    to Class B as of date X"?
  - Multi-share-class clients — can one client hold positions in multiple share-classes simultaneously (each with its
    own NAV slice)? How does the allocation engine partition the client's deposited capital across their share-class
    subscriptions?

A7. **End-to-end onboarding state today** — for the May-23 cutover, what's the actual operating model? Single client
(Ikenna's own capital), single share-class (whatever the carry-archetype defaults to), no KYC, no IMA, no
client-supplied API keys? Or are there other clients already onboarded whose state lives somewhere I (the asking
operator) should be auditing? **Has any non-Ikenna client ever been onboarded through any flow, or is the entire client
model aspirational today?**

### Block B — Treasury / wallet / custody architecture

B1. **Custody topology per asset_group**:
  - **DeFi wallets** — per CLAUDE.md DeFi Execution Architecture, execution-service injects `wallet_private_key` at
    runtime via `connector.connect(config={"wallet_private_key": pk, "rpc_url": url})`. Per-chain-per-strategy-
    per-client wallet model? Per-client multi-chain wallet (one address per chain per client)? Pooled wallets where
    multiple clients share an address with internal-ledger accounting? What's the SSOT decision and why?
  - **Wallet PK custody at rest** — where do PKs live (Secret Manager per chain per wallet, Copper / Fireblocks-style
    MPC custody, Safe multi-sig with operator + co-signer, hardware HSM)? At runtime, how are they fetched (per-tx
    sign request to MPC service, full PK loaded into memory at execution-service startup, JIT fetch per signing)? What
    rotation / revocation / lost-key recovery procedure exists?
  - **CeFi exchange sub-account model** — for each CeFi venue (Bybit / Binance / OKX / Deribit / Hyperliquid (DEX-CEX
    hybrid) / Aster), how is per-client capital segregated? Per-client master + sub-account model (each client has a
    dedicated sub-account on each venue with their own API key + funded balance)? Pooled-account-with-internal-ledger
    (one operator-owned account per venue, internal ledger attributes positions to clients)? Different per venue based
    on what the venue supports?
  - **CEFFU / Copper for CeFi off-exchange settlement** — per master plan Group F item 19, "Copper + CEFFU treasury"
    is in scope. CEFFU's MirrorX (Binance-integrated tri-party custody) and Copper's ClearLoop (multi-venue tri-party)
    let us hold capital in custody but trade with venue-margin attribution without moving the capital onto the venue.
    Are the integrations actually wired in execution-service / position-balance-monitor today, or only architecturally
    planned? Per-client allocation across the tri-party slot — is that modeled?
  - **TradFi prime broker / custody** — for Databento-sourced TradFi (CME futures / ES.OPT options / equity ETFs), is
    there a real broker account today (Interactive Brokers / a prime broker like StoneX / Marex / etc.) or is TradFi
    backtest-only with no live trading wired? If live exists, per-client sub-account model? Cash management? Span
    margin computation?
  - **Sports betting accounts** — per-bookmaker accounts (Bet365 / Pinnacle / Bookmaker XYZ via odds_api). Per-client
    account-on-bookmaker (clients each have their own bookmaker account we API-into) vs operator-pooled bookmaker
    accounts with internal ledger? KYC handled by bookmaker (so client must onboard with bookmaker individually)?
    Currency management (most sports books are GBP / EUR / USD denominated; per-client base currency conversion)?
  - **Prediction-market accounts** — Polymarket (USDC.e on Polygon → Polymarket smart contract) + Kalshi (USD via ACH
    + KYC at Kalshi). Same pooled vs per-client question. Polymarket is a smart-contract venue so it's effectively a
    DeFi flow with prediction-specific instrument shape; Kalshi is a CeFi-style account with full KYC. Are both wired?

B2. **Working-capital movement** — once a client deposits, how does capital flow to where the trading happens?
  - **Deposit → operating treasury** — initial credit lands in (a) Copper / CEFFU custody, (b) on-chain wallet, (c)
    bank account, (d) a stablecoin holding on a chain. Reconciliation lag.
  - **Operating treasury → strategy-allocated capital** — the allocation engine (does this exist?) decides "of client
    C's $X subscribed to share-class Y, allocate $A to archetype carry_staked_basis on Solana, $B to leveraged_funding_
    arb on Ethereum, $C to a CeFi spot-perp basis archetype on Bybit, leave $D as treasury cash buffer." Where does
    this allocation logic live (strategy-service? a separate allocation-service? operator manual decision in a
    spreadsheet)?
  - **Strategy-allocated capital → venue margin** — for CeFi-perp strategies, capital flows from custody → exchange
    sub-account margin. For DeFi strategies, capital flows from custody → working wallet → on-chain protocol (Aave
    supply / DEX swap / LST mint). For sports betting, capital flows from custody → bookmaker account. Each of these
    movements is a real on-chain or off-chain transfer with cost (gas / wire fees / bridge fees / withdrawal fees) +
    settlement time + risk window. Is the cost + settlement-time budget modeled in the allocation decision?
  - **Reverse path on rebalance / withdrawal** — when the strategy reduces position, when the client requests
    redemption, when the share-class hits a liquidity window: capital flows back through the same rails in reverse,
    with their own costs + risks. Is the reverse path symmetric (every forward movement has a tested reverse path) or
    asymmetric (we can deposit easily but can't withdraw at scale)?

B3. **Multi-currency + multi-collateral accounting**:
  - The client subscribed in USD; their deposits arrived in USDC; their share-class is SOL-denominated; their
    archetype runs in jitoSOL on Solana with a USDC-margin perp hedge on Hyperliquid. **At every point in the flow,
    what's the canonical asset + valuation + reporting currency, and how do conversions between them get accounted
    for?**
  - FX-equivalent for crypto: USDC ↔ ETH ↔ stETH ↔ jitoSOL ↔ SOL conversions with both an "exchange rate at the time"
    component and a "drift / yield accrual" component. Does the ledger preserve the historical rate at every
    conversion, or does it always re-mark to current?
  - Per-share-class hedging mode: a USD-denominated share-class trading SOL strategies must hedge SOL → USD price
    risk; a SOL-denominated share-class doesn't. How is the hedging mandate plumbed into the execution path?

B4. **Multi-sig + operational signing controls**:
  - For DeFi wallet movements above some $ threshold, is there a multi-sig requirement (Safe / Squads on Solana)?
    Per-chain.
  - For CeFi withdrawals (moving capital out of an exchange to custody), is there an operator-approval gate, or is the
    automated path trusted to handle every withdrawal regardless of size?
  - Withdrawal whitelisting per venue (capital can only leave a venue to a known custody address) — wired across all
    venues, or only some?
  - Audit trail for every signing event (who triggered, what was signed, what was the on-chain or off-chain effect).
    Centralised or per-venue?

B5. **Treasury liquidity buffers + counterparty risk**:
  - Does the system maintain a target cash / stablecoin buffer per share-class (so daily redemptions can be honored
    without forcing strategy unwinds at adverse prices)? Where is the buffer policy declared?
  - Per-counterparty exposure tracking — total client capital exposed to (Bybit / Aave-on-Ethereum / Polymarket
    contract / Bet365-the-bookmaker / Copper-the-custodian) at any moment. Per-counterparty risk caps?
  - Counterparty insurance / risk-mitigation surface (BitGo Trust, Lloyd's-of-London-style crypto insurance, on-chain
    cover via Nexus Mutual / Sherlock for DeFi protocols) — wired or out of scope?

### Block C — 50+ strategy archetypes × share-class derivative matrix

C1. **Is there a canonical SSOT listing of the 50+ archetypes?** Where (UAC `ArchetypeRegistry`? a codex doc? PM
master plan? operator's notebook)? Per archetype, what's captured (ID / name / asset_group / venues / instruments /
data dependencies / strategy-service handler / execution-service requirements / risk envelope template)?

C2. **Per-archetype × per-share-class allowability matrix** — not every archetype is appropriate for every share-class
(retail share-class probably can't access flash-loan-heavy DeFi archetypes; conservative-tier share-class can't access
high-leverage funding-arb). Is there a declared "share-class X allows archetypes {A, B, C}" mapping as data, or is the
implicit-knowledge "we know retail can't do X" un-codified?

C3. **Allocation engine** — given client C subscribed to share-class S with subscribed amount $X, with risk envelope
R, the allocation engine decides per-archetype dollar allocation. Concretely:
  - Does an allocation engine exist as code today, or is allocation operator-set per-client?
  - Inputs: share-class strategy whitelist, risk envelope, current positions, target weights per archetype, available
    venue capacity, cost / slippage estimate per allocation move.
  - Outputs: per-(client, share-class, archetype, venue) target capital allocation, with per-rebalance cadence (daily
    / weekly / on-trigger).
  - Constraint solver shape (min-cost rebalance subject to risk envelope + target weights + transaction-cost budget)?
    Or simple proportional allocation?

C4. **Per-archetype data dependency declaration** — for each archetype, what data feeds does it depend on (which
features, which markets, which venues, which instruments)? Per CLAUDE.md "doc → plan → code" + the
`feature_group → required_inputs` DAG SSOT in UAC, is this declared as data so the system can validate "client
subscribed to share-class with archetype X, but the data feeds X needs are not currently green for the venue Y this
client allocates to"?

C5. **Per-archetype × per-share-class fee + perf-fee accounting** — performance fees crystallize per share-class +
high-water-mark + crystallization-period. For an archetype that runs across multiple share-classes, the fee accounting
is per-share-class, not per-archetype. Does the system attribute realized PnL to (client, share-class, archetype)
correctly so per-share-class fee accrual is right?

C6. **Capacity per archetype** — every strategy has finite capacity (a basis-arb on Bybit-BTC has a limit before it
moves the funding rate; a sports market-make on a single bookmaker has a stake-cap before liquidity dries up). When
new client subscriptions arrive, who decides "this archetype is at capacity, the new subscription can't allocate to
it"? Is capacity tracked per-archetype × per-venue × per-time-window?

C7. **Live archetype set today vs aspirational 50+** — of the claimed 50+ archetypes, how many are actually
production-ready (have shipped strategy-service handler + execution-service connector + features wired + tested
end-to-end backtest + tested live or at least testnet)? What's the per-archetype readiness matrix (per master plan
Group A-G coverage)? Is there a single source for "archetype X is at readiness level Y" or is it per-archetype-plan
scattered?

### Block D — Post-trade flow (settlement + reconciliation + reporting + fees + statements)

D1. **Per-trade settlement flow per asset_group**:
  - **CeFi spot / perp** — fill from venue → position-balance-monitor updates position → ledger entry (per (client,
    archetype, venue, instrument)) → fee + funding accrual updated → mark-to-market on next tick.
  - **DeFi swap / lending / LST mint** — on-chain tx submitted → confirmation watcher waits N blocks →
    position-balance-monitor reads on-chain state (Aave reserves, LP shares, LST balance) + reconciles against
    submitted tx → ledger entry per (client, archetype, chain, contract, asset) → gas + fee + slippage attributed.
  - **TradFi futures** — fill from broker → position-balance-monitor → SPAN margin recomputed → variation margin
    nightly settlement.
  - **Sports bets** — bet placed at bookmaker → odds + stake recorded in position-balance-monitor → resolve at fixture
    end → win/loss settled → bookmaker balance updated → reconcile against bookmaker API.
  - **Prediction markets** — Polymarket: smart-contract trade settled on-chain → reconcile USDC balance + market-token
    balance per market_id. Kalshi: trade fill via Kalshi API → reconcile USD balance + position.
  Is each of these flows actually wired end-to-end (fill → ledger → reconcile → mark) for all archetypes that touch
  that asset_group?

D2. **Reconciliation cadence + drift handling** — for each venue / chain / bookmaker / custody, there's a reconcile
job that pulls ground-truth positions + balances and compares against the internal ledger. Cadence (per tick / per
minute / per hour / EOD)? Drift threshold (alert if delta > X bps)? Drift-resolution procedure (manual operator
investigation / auto-correct internal ledger to match venue / halt strategy)? Per asset_group + per venue.

D3. **Fee accrual + crystallization**:
  - Management fee — typically X% per annum, accrued continuously (per-day or per-tick) and crystallized monthly /
    quarterly. Is this wired to the per-share-class NAV computation correctly (so reported NAV = pre-fee NAV - accrued
    fee)?
  - Performance fee — typically Y% over high-water-mark, crystallized at period-end. Is HWM tracked per (client,
    share-class, period)? When a client subscribes mid-period, does their HWM anchor at subscription NAV (correct) or
    at period-start NAV (incorrect for them)?
  - Per-archetype P&L attribution feeds the per-share-class fee accrual via the C5 → D3 chain. Is the data plumbing
    actually present, or are fees computed by an operator-side spreadsheet at month-end?

D4. **Statement generation + delivery**:
  - Per-client periodic statement (daily / monthly / quarterly per share-class terms) — what's in it (NAV / PnL / fee
    accrual / per-archetype attribution / per-venue exposure / risk metrics / fee invoice if crystallization period)?
  - Generation surface — automated (cron + PDF render + S3 / GCS storage + email delivery), or operator-manual?
  - Self-serve UI — does the client log into `unified-trading-system-ui` and see their statements + download PDFs?
  - Audit trail — are historical statements immutable + retrievable for regulatory / dispute purposes?
  - Has any real client account ever had their NAV + PnL + metrics + invoice rendered through the full live pipeline
    against real venues — or is statement generation entirely code-shipped-but-never-run?

D5. **Withdrawal flow** — client requests redemption → per share-class liquidity terms → strategy unwind kickoff →
capital movement back through reverse rails (B2) → final NAV + final fee crystallization → wire / on-chain transfer to
client's bank / wallet → final statement. Is this end-to-end wired, or has no client ever withdrawn (because no
non-Ikenna client has ever onboarded per A7)?

D6. **Tax + regulatory reporting**:
  - Per-client tax lot tracking (FIFO / LIFO / specific-lot per jurisdiction) — wired or out of scope?
  - Per-jurisdiction reporting forms (US 1099 / W-8 / FATCA / CRS / EU DAC8 for crypto / UK self-assessment helper
    pack) — wired or out of scope?
  - Counterparty / venue regulatory reporting (SEF / EMIR / Dodd-Frank for derivatives, MiFID II for EU venues) —
    wired or operator-manual / not-applicable?

### Block E — Cross-asset-group interaction matrix (50+ archetypes × asset_group × share-class × venue × chain)

E1. **For each of the 50+ archetypes, what's the (asset_group, venue / chain set, share-class compatibility, capacity,
data dependencies, custody requirements) tuple?** This is the master matrix. Is it codified anywhere (UAC registry?
codex doc? master plan section?), or scattered across per-archetype docs + implicit operator knowledge?

E2. **Cross-asset-group archetypes** — some archetypes span asset_groups (e.g. crypto-vs-equity statistical arb;
sports-vs-prediction cross-venue arb on the same event; CeFi-spot-vs-DeFi-AMM arb on the same asset). For these:
  - How is the cross-asset-group data dependency declared (single archetype consumes feeds from 2+ asset_groups +
    needs simultaneous trading paths into 2+ asset_groups)?
  - How is the cross-asset-group execution timing handled (latency mismatch between CeFi venue ms-latency vs DeFi
    chain block-time s-to-min latency)?
  - How is cross-asset-group risk attribution done (a stat-arb has shared risk that doesn't decompose cleanly into
    per-asset-group)?

E3. **Per-share-class jurisdictional venue exclusion** — already touched in A2. Concretely: a "EU retail" share-class
might exclude Polymarket (US prediction-markets venue not regulated in EU), all sports-bookmakers (gambling regulation
varies wildly per EU country), and certain DeFi protocols (post-MiCA). A "US accredited" share-class might exclude
Hyperliquid + Aster (US-restricted DEX perps in some readings). Is the per-share-class venue allowlist / blocklist as
data?

E4. **Venue-onboarding status per asset_group** — the master plan lists 6 perp venues for live; the cefi_master /
defi_master / sports_master / predictions_master / tradfi_master each enumerate venues. For client-account flow
specifically: per (asset_group, venue), is the per-client-sub-account-or-per-pooled-account decision made + the API-
intake + custody-rails wired + the reconciliation job running + the fee-tracking integrated? Per-venue readiness
checkbox.

E5. **End-to-end cross-asset-group lifecycle test** — has any test (e2e-testing/) ever run a full simulated lifecycle
for a synthetic client (deposit → multi-archetype allocation → multi-venue trading → reconcile → fee accrual →
statement → withdrawal) across multiple asset_groups? If yes, where is it + what does it cover. If no, that's the
single biggest gap to flag.

### Block F — Operational + operator-experience layer

F1. **Operator views for client lifecycle management** — in `unified-trading-system-ui` (or a separate ops UI), does
the operator have:
  - Per-client view (subscriptions / positions / NAV / risk / pending operations)?
  - Per-share-class view (capacity / utilisation / NAV / per-archetype allocation / pending subscriptions /
    redemptions)?
  - Treasury overview (per-venue + per-chain + per-custody balance, target buffer vs actual, low-balance alerts)?
  - Pending-operations queue (deposits awaiting confirmation, redemptions awaiting strategy unwind, rebalances
    pending)?
  - Audit log per client + per share-class (every change, who made it, when, what was the prior state)?

F2. **Failure modes + recovery procedures**:
  - Client's deposit arrives but is 2x the expected amount / wrong currency / wrong chain — operator workflow?
  - Bridge fails mid-deposit (USDC bridged from Ethereum to Solana stuck in the bridge for hours) — handling?
  - Venue suspends withdrawals (FTX-style scenario) — per-client position freeze + client communication procedure?
  - DeFi protocol exploit (Aave drained, an LST de-pegs catastrophically) — per-client exposure read-out + emergency
    unwind path?
  - Custody provider (Copper / CEFFU) operational issue — fallback path to direct-on-venue-margin?
  - Bookmaker voids a settled bet retroactively — reconcile correction + client-side accounting?
  - Each of these failure modes should have a documented runbook per CLAUDE.md "Runbook Execution-Owner SSOT" — exist
    today or to-be-written?

F3. **Compliance + audit trail end-to-end** — for regulatory inspection / SOC 2 / ISO 27001 / industry-equivalent
audit, can we produce a per-client end-to-end audit trail (every onboarding decision, every deposit, every allocation,
every trade, every reconciliation, every fee accrual, every statement, every withdrawal) with timestamps + actor +
prior-state + post-state? Where does this live (event-stream archive / immutable ledger / queryable audit DB)?

F4. **Multi-tenancy data isolation** — within the system, is client C's data isolated from client D's data at the
storage layer (separate Firestore subcollections per client_id, separate S3 / GCS prefixes per client, row-level
security in any SQL stores)? Or is isolation only at the application layer (application code filters by client_id but
all clients live in the same DB rows)?

F5. **Operator-vs-client permission model** — Firebase custom claims for client_id + role (`client` /
`operator` / `compliance` / `auditor`). Wired today across all the UIs? Per-API-endpoint authz checks the claim before
returning data?

## What "answered" looks like

- One or more canonical plans exist in `plans/active/` (or fold into `master_to_live_defi_2026_05_23.md` Group F + G
  + the per-asset_group epic plans) covering each of:
  - **Client lifecycle data model + onboarding flow** — UAC `Client` + `ShareClass` + `Subscription` + `RiskProfile`
    SSOT; onboarding intake UI / API; KYC integration (or explicit deferral); jurisdictional gating engine; risk-
    questionnaire intake; share-class subscription as data.
  - **Treasury + custody architecture** — per-asset_group custody topology (pooled vs per-client per venue), Copper +
    CEFFU integration in execution-service + position-balance-monitor, DeFi wallet PK custody at-rest + at-runtime,
    multi-sig + signing controls + withdrawal whitelisting, treasury liquidity buffer policy, per-counterparty
    exposure tracking + caps.
  - **Allocation engine** — share-class strategy whitelist + risk envelope + target weights → per-(client, share-
    class, archetype, venue) capital allocation; rebalance cadence + cost-aware rebalance solver; capacity-aware
    allocation (refuse to allocate to over-capacity archetype).
  - **Strategy archetype + share-class registry** — UAC `ArchetypeRegistry` (50+ archetypes with full metadata) +
    `ShareClassRegistry` + per-share-class × per-archetype allowability matrix as data.
  - **Post-trade flow per asset_group** — per-asset_group settlement → ledger → reconcile flow wired end-to-end
    including DeFi (on-chain confirmation watch + state read), CeFi (sub-account reconcile), TradFi (broker reconcile
    + SPAN margin), sports (bookmaker fixture-resolve reconcile), prediction (smart-contract / API reconcile).
  - **Fee accrual + crystallization + statement generation + withdrawal flow** — wired per share-class with HWM +
    period-tracking + automated statement render + delivery + immutable archive.
  - **Operator + client UI surfaces** — per-client view, per-share-class view, treasury overview, pending-ops queue,
    audit log; client self-serve statement + invoice download.
  - **Cross-asset-group lifecycle e2e test** — at least one synthetic-client end-to-end test in `e2e-testing/`
    covering deposit → allocation → trade → reconcile → statement → withdrawal across ≥2 asset_groups.
  - **Failure-mode runbooks** — per F2, per CLAUDE.md "Runbook Execution-Owner SSOT" with executable owner + cadence +
    verification.

- Codex SSOT(s) describe:
  - **Client lifecycle architecture** (single doc per `codex/04-architecture/client-lifecycle-onboarding-to-
    withdrawal.md` or similar) — all the Block A-D flow.
  - **Treasury + custody topology** (`codex/05-infrastructure/treasury-custody-topology.md`) — per-asset_group custody
    SSOT + the Copper / CEFFU / DeFi wallet model + signing + reconciliation cadence.
  - **Share-class + archetype registry** (`codex/04-architecture/archetype-share-class-registry.md`) — the registry
    SSOT + the per-share-class × per-archetype matrix + allocation-engine contract.
  - **Post-trade flow per asset_group** (`codex/04-architecture/post-trade-settlement-reconcile-flow.md`) — the
    asset-group-by-asset-group flow including the asymmetric reverse-path on withdrawal.
  - **Tax + regulatory reporting** (`codex/14-playbooks/compliance/regulatory-reporting.md`) — per-jurisdiction
    coverage + per-venue regulatory obligations + tax-lot tracking SSOT.
  - **Per-asset-group epic / master updates** — each of `defi_master_2026_05_07.md` /
    `cefi_master_2026_05_07.md` / `tradfi_master_2026_05_07.md` / `sports_master_2026_05_07.md` /
    `predictions_master_2026_05_07.md` body updated with per-venue client-account-flow readiness checklist.
  - **Master plan Group F + G** (`master_to_live_defi_2026_05_23.md`) extended with per-archetype × per-share-class
    readiness rows where the lifecycle gates are explicit.

- Real-data evidence per axis:
  - At least one non-Ikenna client onboarded end-to-end (or explicit decision recorded that May-23 cutover is
    Ikenna-capital-only and multi-client lifecycle is post-cutover).
  - Per asset_group, at least one client-attributed real fill flowing through the full settle → reconcile → ledger →
    fee-accrual chain, with a generated statement that the operator (or test client) can download.
  - At least one synthetic-client end-to-end lifecycle test passing in CI, covering a representative subset of
    archetypes × share-classes × asset_groups.

- Service-readiness checklist: per master plan Group F items 19 (Copper + CEFFU treasury) + 20 (live observability) +
  Group G item 23 (operator UX), all gates green for the live-DeFi cutover scope; for the post-cutover multi-client
  surface, an explicit deferred-work plan exists per the Plan Archival HARD RULE.

## Audit findings (to be filled by audit pass)

For each sub-question in Blocks A-F, fill:

- **Code state**: file:line citations across UAC (Client / ShareClass / Subscription / RiskProfile / ArchetypeRegistry
  types), instruments-service (per-archetype data dependency declarations), execution-service (custody integrations +
  signing path), position-balance-monitor (per-client ledger shape), strategy-service (allocation engine if exists),
  risk-and-exposure-service (per-client risk envelope reads), deployment-api + deployment-ui + unified-trading-system-
  ui (per-client + operator surfaces), unified-config-interface (per-client config storage), e2e-testing (lifecycle
  tests).
- **Data state**: how many client records exist in production storage (Firestore / DB), how many share-classes
  defined, how many subscriptions active, how many archetypes have a registry entry, how many per-client positions in
  position-balance-monitor today, audit log volume / coverage.
- **Run state**: has any non-Ikenna client onboarded end-to-end; has any real deposit reconciled to a per-client
  ledger entry; has any real client-attributed trade settled per asset_group; has any real fee accrual crystallized;
  has any statement been generated + delivered; has any client withdrawal completed.
- **Codex state**: do any of the listed codex SSOTs exist in current form, or are they all greenfield? Drift between
  whatever client-lifecycle code exists vs what the docs describe.
- **Gap analysis**: per the master matrix (50+ archetypes × N share-classes × M asset_groups × K venues × J chains),
  where are the systemic gaps; what's blocking May-23 cutover (likely "Ikenna-only operational mode"); what's
  deferred-post-cutover with named successor plan; what failure-mode runbooks are missing.

## Operator notes / answers

(Empty — to be filled during iteration.)

## Iteration log

| Date | Author | Change |
| ---- | ------ | ------ |
| 2026-05-08 | ikenna + main agent | Initial draft created |
| 2026-05-09 | main agent | Re-created after parallel-agent cleanup wiped uncommitted draft + sibling docs (client_reporting + risk_simulations) + README.md from `plans/questions/`; bundled commit + push this time per foot-gun #4 mitigation |

## Plan-shape decisions (filled before plan extraction)

- **Plan name + path**: TBD — likely splits into 4-5 plans:
  - `plans/active/client_lifecycle_data_model_<date>.md` (UAC types + onboarding flow + share-class + subscription
    SSOT — folds into a new client-lifecycle epic or extends `master_to_live_defi_2026_05_23.md` Group F/G)
  - `plans/active/treasury_custody_topology_<date>.md` (per-asset_group custody + Copper/CEFFU + DeFi wallet PK +
    signing + reconcile cadence — Group F item 19 expansion)
  - `plans/active/allocation_engine_archetype_share_class_registry_<date>.md` (50+ archetype registry + share-class ×
    archetype matrix + allocation engine — composes with strategy-service + risk-and-exposure-service)
  - `plans/active/post_trade_settlement_reconcile_per_asset_group_<date>.md` (settle → ledger → reconcile flow per
    asset_group + fee accrual + statement gen + withdrawal — composes with reporting work)
  - `plans/active/client_lifecycle_e2e_test_failure_mode_runbooks_<date>.md` (e2e synthetic-client test +
    failure-mode runbooks per F2 — composes with e2e-testing scope)
- **Plan type**: mixed (code + infra + business + operational + compliance)
- **Owner side**: TBD — likely ikenna for cross-cutting design (data model + lifecycle architecture + share-class
  registry + custody topology decisions + jurisdictional gating policy) + harsh for per-asset_group flow
  implementation + per-venue connector + per-archetype registry entry population + e2e test harness construction
- **Codex SSOTs touched**: per "What answered looks like" — 5 NEW + 5 UPDATE listed above
- **Cross-plan dependencies**:
  - Composes with [`api_keys_wallets_accounts_readiness_2026_05_08.md`](api_keys_wallets_accounts_readiness_2026_05_08.md)
    — credentials inventory side; this doc adds the client-account-attached lifecycle on top.
  - Composes with [`defi_readiness_catalogue_2026_05_08.md`](defi_readiness_catalogue_2026_05_08.md) — DeFi venue +
    chain catalogue is the substrate; this doc adds the client-account + custody overlay on top.
  - Composes with [`codex_vs_citadel_infrastructure_specs_2026_05_08.md`](codex_vs_citadel_infrastructure_specs_2026_05_08.md)
    — fresh-eyes target-state must include client-lifecycle gaps surfaced here.
  - Composes with `master_to_live_defi_2026_05_23.md` Group F items 19 + 20 + Group G item 23 — extends them with
    per-archetype × per-share-class readiness rows.
  - Composes with each per-asset_group epic (`defi_master` / `cefi_master` / `tradfi_master` / `sports_master` /
    `predictions_master`) — each gets per-venue client-account-flow readiness checklist additions.
- **Estimated scope**: TBD — audit pass first; expect ≥ 4 plans × 5-10 AI-day each + a beefier coordination master if
  multi-client lifecycle is targeted pre-May-23 vs deferred post-cutover.

## Plan extraction record

(Empty — fills when the plan ships.)
