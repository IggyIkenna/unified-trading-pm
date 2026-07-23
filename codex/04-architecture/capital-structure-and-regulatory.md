---
doc_type: codex-ssot
title: Capital Structure, Custody, and Regulatory Context
summary:
  Custody + regulatory context per venue category — DeFi (Copper/Fireblocks client wallet), Sports (firm Unity pool),
  CeFi (client SMA, no-withdrawal API keys), TradFi (IBKR sub-account tunnel); we always face ONE client (fund mechanics
  abstracted); per-mode credential, onboarding, and P&L-attribution.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service]
scope: [engineer, admin]
tags: [capital, execution, cefi, defi, sports, tradfi]
related:
  [
    /codex/04-architecture/capital-flow-model.md,
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/02-venues/venue-registry-reference.md,
  ]
created: 2026-04-17
authoritative_for: [per-category custody, regulatory posture, and onboarding structure]
referenced_by:
  [
    /codex/02-venues/unity-integration.md,
    /codex/03-services/portfolio-allocator.md,
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/04-architecture/capital-flow-model.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/axes/share-class.md,
    /codex/09-strategy/architecture-v2/axes/venue-eligibility.md,
    /codex/09-strategy/architecture-v2/cross-cutting/capital-client-isolation.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Capital Structure, Custody, and Regulatory Context

> **Scope:** How capital is custodied per venue category, what the regulatory structure is for each mode, and what
> onboarding flow each requires. This is complementary to [capital-flow-model.md](capital-flow-model.md) — that doc
> covers the mechanical transfer/rebalance protocol; this doc covers the ownership and regulatory context.
>
> **Audience:** Implementers, ops, compliance, client-facing teams, and anyone building onboarding/reporting flows.
>
> **Context:** Augments the Capital Flow Lifecycle section in
> [/codex/09-strategy/architecture-v2/README.md](/codex/09-strategy/architecture-v2/README.md) — does not replace it.

## Important framing: we face ONE client, which may itself be a fund

Before the per-category detail, a critical framing that simplifies the whole architecture:

**We interact with a single counterparty per engagement — the "client" — regardless of whether that counterparty is an
individual, family office, prop firm, corporate treasury, or a fund.**

From our perspective:

- The client deposits capital (or grants access to a wallet / account that holds capital)
- We trade on their behalf under the agreed custody model
- We track positions, fills, P&L, and report back
- Our code path is identical whether the client is one person or one fund

**The "treasury wallet" concept applies when the client is a fund** (or any pooled structure aggregating multiple
end-investors). In that case:

- The treasury wallet is the _fund's_ aggregated capital — it's _their_ operational pool
- We still just face the fund as our single client
- The fund (or its administrator) handles subscriptions, redemptions, investor-level P&L, share class accounting, tax
  reporting
- That logic lives at the fund administrator / fund operator layer — NOT in our trading infrastructure

**If the client is not a fund:**

- They deposit assets directly to the account we trade (CEX SMA, IBKR tunnel, Copper wallet, etc.)
- No treasury abstraction is needed — the deposit _is_ the trading capital
- Subscriptions/redemptions reduce to simple deposit/withdrawal events on that account

**Our architecture is the same either way.** The treasury wallet, when present, is just a parent node in the
Transfer/Rebalance graph. What changes between fund-client and non-fund-client is:

- **Non-fund client**: one deposit event → goes into trading venue → strategies run
- **Fund client**: subscription event on administrator side → administrator wires capital to treasury wallet → we move
  from treasury to trading venues → strategies run. Redemptions reverse this. **Investor-level accounting is the fund's
  responsibility, not ours.**

What we still own in both cases:

- Per-client (per-fund) equity tracking
- Per-strategy allocation within that client
- Full P&L + fills + positions with the standard 9-field event tag

What the fund (if any) owns:

- Investor subscription / redemption ledger
- Investor share class accounting
- Fund-level NAV calculation (they pull our P&L reports and combine with other assets)
- Investor tax forms
- Fund-level regulatory reporting

This keeps our infrastructure strictly within the "trading for a single counterparty" model. Fund mechanics are
abstracted behind the client interface.

## Summary Table

| Venue category                           | Custody                                                             | Regulatory mode                                                                             | Our scope                                         | Onboarding artefact                                                               | Withdrawal path                                         |
| ---------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------- |
| **DeFi**                                 | Client wallet (Copper/Fireblocks default) or firm on-chain treasury | Not regulated (client's own wallet; we sign via custodian API with client permission)       | Trading permission on client wallet via custodian | Copper or Fireblocks workspace with signing policy                                | Client-initiated via custodian                          |
| **Sports (Unity)**                       | Firm-managed pooled wallet                                          | Not regulated trading activity under our permissions; firm owns wallet; client funds pooled | Full custody + trading                            | Fund-style contribution to Unity pool                                             | Firm-initiated on client request; rollover rule applies |
| **CeFi (SMA, default)**                  | Client CEX account                                                  | SMA — client retains custody at exchange; we hold trading API keys only                     | Trading via API; no custody                       | Client opens CEX account, deposits, shares API keys (trading only, no withdrawal) | Client withdraws directly from CEX                      |
| **CeFi (fund mode, future)**             | Firm treasury + firm CEX accounts                                   | Regulated fund (third-party administrator); investor holds fund shares                      | Full custody + trading                            | Fund subscription via administrator                                               | Redemption via administrator                            |
| **TradFi (IBKR SMA, default)**           | Client IBKR tunnel                                                  | SMA — IBKR-regulated custody; FIX API trading permission                                    | Trading via FIX API; no custody                   | IBKR tunnel onboarding via introducing broker relationship                        | Client withdraws directly from IBKR                     |
| **TradFi (counterparty direct, future)** | Counterparty custody                                                | Counterparty-arranged                                                                       | Trading signals / allocation only                 | Counterparty agreement                                                            | Counterparty-managed                                    |

## Section 1: DeFi Capital Structure

### Default: Client wallet + custodian (Copper / Fireblocks)

```
Client
  ├─ Own on-chain wallet(s)
  │   ├─ Ethereum wallet
  │   ├─ Arbitrum wallet
  │   ├─ Optimism wallet
  │   ├─ Polygon wallet, Base, Avalanche, Solana, etc.
  │
  ├─ Custodian workspace (Copper or Fireblocks)
  │   ├─ Policy: "Odum Research can sign: swap, lend, stake, transfer on these wallets"
  │   ├─ Limits: per-tx, daily, per-protocol
  │   └─ Approval thresholds: MPC signatures required
  │
  └─ Custodian API credentials shared with Odum Research
```

**Why custodian-routed:**

- Client retains on-chain wallet custody (no firm key holding)
- MPC multi-sig prevents any single-party rug risk
- Audit trail per transaction with policy enforcement
- Industry-standard for institutional DeFi participation

**Our scope via Copper/Fireblocks:**

- We initiate transactions via custodian API
- Custodian signs if within client-approved policy
- On-chain tx submitted; client and we both see fills
- We never hold private keys

**Onboarding flow:**

1. Client onboards to Copper or Fireblocks (their choice)
2. Client sets up signing policy authorizing our operations (swap, lend, stake, transfer) with limits
3. Client provides custodian API credentials to us
4. We register client wallet addresses in UAC registry + execution-service Copper/Fireblocks adapter
5. First test transaction (small swap, small deposit) validates end-to-end
6. Full strategy enablement

**Withdrawal:** Client-initiated via custodian UI. Our signing permission doesn't include transfers to third parties
(only internal rebalancing), so client retains full withdrawal control.

**Toggle for direct-wallet mode (no custodian):** For clients who want direct wallet connection (no Copper/Fireblocks),
we support a toggle:

- Client generates wallet (or uses existing)
- Client sets trading permission directly (e.g., via approve() on relevant protocols)
- We sign via our infrastructure with client-delegated keys
- **Higher trust model — we recommend custodian for all institutional clients**
- **Lower institutional credibility and less audit trail**

### Firm-owned treasury wallet (for firm DeFi capital)

For our own firm capital deployed in DeFi:

- Firm Treasury wallet holds idle capital
- Routed through Fireblocks for firm compliance
- Transfer/Rebalance service can move between Treasury and firm trading wallets
- Never mingled with client wallets

### Inter-chain capital movement (DeFi)

Our supported bridges:

| Bridge       | Route                        | Typical latency                | Typical fee | Use case                      |
| ------------ | ---------------------------- | ------------------------------ | ----------- | ----------------------------- |
| Circle CCTP  | USDC EVM ↔ EVM               | 15-20 min (attestation + mint) | ~$0         | Default for USDC cross-chain  |
| LayerZero    | Any token EVM ↔ EVM + Solana | 5-15 min                       | 0.05-0.2%   | Default for ETH, other tokens |
| Stargate     | Stable token EVM ↔ EVM       | 2-10 min                       | 0.05%       | Fast, liquid route            |
| Hop Protocol | USDC, USDT, ETH              | 5-10 min                       | Variable    | Alternative for EVM           |
| Wormhole     | Cross-chain including Solana | 15-30 min                      | Variable    | Solana bridge                 |

UAC's venue capability registry encodes per-bridge latency and fee. Transfer/Rebalance service picks bridge based on
route + speed requirement + cost.

## Section 2: Sports Capital Structure (Unity prime broker)

### Default: Firm-managed pooled wallet

```
Firm Unity account (single)
  ├─ USD balance (primary share class)
  ├─ Optional: EUR, GBP, CNY balances
  │
  ├─ Unity internal ledger allocates to 10 child bookmakers
  │   ├─ 2 commission-free books
  │   ├─ VX (0.2% commission on wins)
  │   ├─ Sharpbet (0.2%)
  │   ├─ 3ET (0.5%)
  │   ├─ Betdex-via-Unity (1.6%)
  │   ├─ Matchbook-via-Unity (2.2%)
  │   ├─ IBCbet (2.5%)
  │   ├─ Betfair-via-Unity (2.8%)
  │   └─ Broker5 (3.0%)
  │
  └─ Bets execute on chosen child book, debit Unity balance, settle to Unity balance
```

**Why firm-pooled:**

- Sports betting isn't regulated as a securities activity in most jurisdictions we operate in
- Firm can pool client capital in one Unity account
- Far simpler operational and tax structure than per-client Unity accounts
- Unity account-level rate limits, subscription fees, and turnover thresholds apply to pool as whole

**Commercial structure:**

- Deposit: USD 10,800 refundable at $5.3M cumulative 12-month volume
- Subscription: USD 2,600/month waived at ~$260k/month effective turnover (absolute wins + absolute losses)
- Commission per child book (see table above)
- Rollover: deposits must be wagered 1x before withdrawal

**Onboarding flow:**

1. Client contributes to Unity pool (treated as fund-like contribution)
2. Client's share is tracked in our internal ledger (not Unity's — Unity sees only pool total)
3. Strategies place bets on Unity; fills tagged with strategy + correlation_id
4. PBMS attributes each fill back to originating strategy
5. Portfolio Allocator distributes P&L to clients proportionally based on their share

**Withdrawal:** Firm-initiated on client request. Must respect:

- Unity rollover rule (deposits wagered 1x minimum)
- Firm notice period (typically 7 days for large withdrawals)
- Per-client share of pool (cannot exceed)

### Direct Betfair + other direct books (alternative to Unity)

For clients who want direct-book exposure without Unity pooling:

- Client opens direct Betfair account
- We get trading API access
- Runs as CEFI-style SMA — client retains custody at Betfair, we just trade
- Higher latency + commission (5% Betfair standard vs 2.8% via Unity) — typically only justified if Unity books don't
  cover required markets
- Useful for Smarkets, Matchbook, Betdaq (not in Unity)

## Section 3: CeFi Capital Structure

### Default: SMA (Separately Managed Account)

```
Client
  ├─ Binance account (or OKX, Bybit, Hyperliquid, Deribit)
  │   ├─ Funding wallet (deposited capital)
  │   ├─ Spot wallet
  │   ├─ USD-M Futures wallet
  │   ├─ COIN-M Futures wallet
  │   ├─ Cross-margin wallet (if enabled)
  │   └─ Options wallet (Deribit)
  │
  ├─ Client deposits directly to CEX
  ├─ Client generates API keys with:
  │   ✓ Spot trading permission
  │   ✓ Futures trading permission
  │   ✗ Withdrawal permission (NEVER granted to us)
  │
  └─ Shares API keys with Odum Research
```

**Why SMA:**

- Client retains full custody at exchange
- Exchange-regulated custody (KYC, AML, SOC compliance by exchange)
- Our scope is trading only — simpler compliance posture
- No firm fiduciary responsibility for client assets

**Our scope on an SMA CEX account:**

- Execute trades via API keys (spot, perp, options — whatever's enabled on the API key)
- Move funds between wallets within the same CEX (e.g., Funding → Futures) via API
- Monitor positions and margin health
- NEVER withdraw funds (API keys don't have permission; we enforce this at credential registration)

**Onboarding flow:**

1. Client opens account at CEX
2. Client completes KYC with CEX
3. Client deposits funds directly to CEX
4. Client generates API keys with trading permission only (no withdrawal)
5. Client provides API keys via secure channel (typically our onboarding UI + Secret Manager)
6. We register API keys in Secret Manager + execution-service adapter
7. Test trade (small spot order) validates connection
8. Strategy instances for this client activated on this venue

**Withdrawal:** Client withdraws directly from CEX. We don't touch fiat / crypto withdrawal flows.

**Internal venue transfers:** For strategies that need to move capital between wallets on the same CEX (e.g., Binance
funding → futures), we emit `TRANSFER` instructions. Execution-service's CEX adapter calls the exchange's SAPI to
execute the internal transfer. This is allowed under trading API permission.

Example: `CARRY_BASIS_PERP@binance-btc-usdt-prod` needs BTC in the futures wallet. Client deposited to spot. Strategy
emits:

```
TRANSFER(
  venue=BINANCE,
  from_wallet=SPOT,
  to_wallet=USDT_FUTURES,
  asset=USDT,
  target_balance=100_000,
)
```

Execution-service's Binance adapter handles via Binance SAPI endpoint.

### Future: CeFi fund mode (via third-party administrator)

```
Investor → subscribes via administrator → fund shares
Administrator → holds capital in firm treasury accounts
Firm Treasury → deploys to firm-owned CEX accounts
CEX accounts → trade across venues per allocation policy
```

**Why fund mode (future consideration):**

- Efficient aggregation of many small investors into one pool
- Single CEX onboarding per venue (not per client) — lower ops overhead
- Professional fund structure (audited financials, regulated administrator)
- Investor experience is similar to any managed fund

**What changes vs SMA:**

- Firm owns all CEX accounts (not clients)
- Transfer/Rebalance service can move between CEXes (allowed on firm-owned)
- Performance fees / management fees applicable
- Requires fund administrator, legal structure, offering memorandum
- Regulatory review depends on jurisdiction (GP/LP, AIF, offshore structures, etc.)

**Migration path from SMA to fund:**

- SMA clients can choose to transition their capital to the fund (if fund opens)
- SMA remains available for clients who prefer custody at exchange
- Both modes coexist technically — architecture already supports either (SMA is a per-client credential set; fund is a
  firm-owned credential set)

## Section 4: TradFi Capital Structure

### Default: IBKR SMA via tunnel

```
Firm IBKR account (own money portfolio)
  ├─ Sub-account A (firm own-money)
  ├─ Sub-account B (SMA client 1 tunnel)
  ├─ Sub-account C (SMA client 2 tunnel)
  └─ ...
```

**Why IBKR tunnel:**

- IBKR supports "sub-account" structures where each SMA client has their own IBKR account under a parent relationship
- Client deposits into their sub-account; IBKR holds their assets (regulated US broker-dealer custody)
- We have FIX API access to trade each sub-account separately
- Cleanest SMA structure in TradFi

**Onboarding flow:**

1. Client opens IBKR sub-account under introducing broker arrangement with us
2. Client completes KYC with IBKR (US SEC/FINRA-regulated)
3. Client deposits funds to their sub-account
4. Client grants us FIX API trading permission for their sub-account
5. We add client's sub-account to our IBKR FIX gateway configuration
6. Test trade validates
7. Strategy instances activated

**Our scope:**

- Equities routing (NYSE, NASDAQ, AMEX, LSE, etc. — IBKR routes internally)
- Futures routing (CME, CBOT, NYMEX, COMEX, ICE — IBKR routes)
- Options (US equity options, futures options — IBKR routes)
- FX spot, forwards (IBKR FX)
- Per-sub-account position + P&L tracking
- No withdrawal permission

### Future: counterparty direct execution

As the platform scales, we expect to move larger counterparties (prime brokers, family offices) to direct connections:

- Counterparty has their own execution infrastructure (OMS, FIX gateways, prime broker)
- They connect directly to exchanges via their infra
- We provide alpha signals / allocation directives
- They execute; we track via reconciliation reports from their side

**What changes:**

- Capital doesn't flow through us
- We only emit logical instructions (target position, rebalance directive)
- Counterparty's execution layer handles routing, algo selection, etc.
- We track fills via their reporting feeds

**When:** Post-scale-out. Not v1.

## Section 5: Wallet Movement Patterns Reference

Detailed flows for each category, in one place:

### DeFi multi-chain flow

```
Client wallet on Ethereum (USDC)
      │
      ├── TRANSFER to Aave V3 Ethereum (LEND)     ← supply rotation
      │
      ├── BRIDGE via Circle CCTP to Arbitrum
      │       │
      │       └── TRANSFER to Aave V3 Arbitrum (LEND)
      │
      ├── BRIDGE via Circle CCTP to Optimism
      │       │
      │       └── TRANSFER to Aave V3 Optimism (LEND)
      │
      ├── SWAP USDC → ETH on Uniswap V3 Ethereum
      │       │
      │       └── STAKE ETH on Lido → stETH
      │               │
      │               └── BORROW against stETH on Aave (for recursive leverage)
      │
      └── TRANSFER stETH to Aave Ethereum (pledge as collateral)
```

Key instructions used: `TRANSFER`, `BRIDGE`, `SWAP`, `LEND`, `BORROW`, `STAKE`, `ATOMIC` (for multicall).

### Sports Unity single-pool flow

```
Firm Unity pool (USD)
      │
      ├── TRADE bet #1 on Unity → routed to Smarkets (via Unity API)
      ├── TRADE bet #2 on Unity → routed to VX
      ├── TRADE bet #3 on Unity → routed to Betfair-via-Unity
      │
      │    [all bets debit/credit same Unity balance]
      │
      └── Settlement flows back to Unity pool
```

Key instruction used: `TRADE` (Unity routes internally to child book per specified preference).

### CeFi SMA internal transfer flow

```
Client Binance account (SMA)
      │
      ├── Spot wallet → TRANSFER (Binance SAPI internal)
      │                                    │
      │                                    ▼
      │                             USDT Futures wallet
      │                                    │
      │                                    ├── TRADE spot BTC on spot market
      │                                    └── TRADE perp BTC on futures market
      │                                        (cross-margin netted on same account)
      │
      └── Cross-margin wallet (if enabled) — spans spot + futures
```

Key instructions: `TRADE`, `TRANSFER` (internal venue only).

### TradFi IBKR SMA flow

```
Client IBKR sub-account
      │
      ├── Cash → allocated to:
      │        ├── Equity positions (SPY, QQQ) via NYSE/NASDAQ routing
      │        ├── Futures positions (ES, CL, GC) via CME
      │        ├── Options positions via CBOE
      │        └── FX positions via IBKR FX
      │
      └── IBKR handles all routing internally
```

Key instruction: `TRADE`. No explicit `TRANSFER` because IBKR is meta-gateway.

## Section 6: Credential Management

Credentials are central to custody model. Each mode has different credential lifecycles:

| Category                              | Credential type                          | Storage              | Rotation cadence                       | Scope                                             |
| ------------------------------------- | ---------------------------------------- | -------------------- | -------------------------------------- | ------------------------------------------------- |
| DeFi (Copper)                         | Custodian API key + signing policy       | Secret Manager       | Annual or on staff change              | Per-client; signed operations only                |
| DeFi (Fireblocks)                     | API key + MPC signing quorum             | Secret Manager + MPC | Annual                                 | Per-client                                        |
| DeFi (direct wallet — rare)           | Wallet private key (encrypted)           | Secret Manager       | Per-incident                           | Per-client — discouraged                          |
| Sports (Unity)                        | Unity API key                            | Secret Manager       | Annual or per-Unity-rotation           | Firm-level (one key for pool)                     |
| Sports (direct Betfair/Smarkets/etc.) | Betfair API session + application key    | Secret Manager       | Per session + annual app-key rotation  | Per-client or firm depending on account ownership |
| CeFi SMA                              | CEX API keys (trade-only, no withdrawal) | Secret Manager       | Per-client request or 6-month schedule | Per-client                                        |
| TradFi IBKR SMA                       | FIX gateway credentials                  | Secret Manager       | Annual                                 | Per-client sub-account                            |
| TradFi counterparty direct            | None (counterparty has their own)        | N/A                  | N/A                                    | Signal delivery only                              |

**Rules (codified in codex/06-coding-standards/):**

- No withdrawal permission ever requested on SMA API keys
- All credentials via Secret Manager, never in env files or code
- Credential rotation triggers re-test of end-to-end strategy lifecycle
- Per-client credential isolation at Secret Manager key path level

## Section 7: Transfer / Rebalance Operations Per Category

| Operation                    | DeFi                                         | Sports (Unity)             | CeFi SMA                | CeFi fund               | TradFi IBKR                 | TradFi counterparty    |
| ---------------------------- | -------------------------------------------- | -------------------------- | ----------------------- | ----------------------- | --------------------------- | ---------------------- |
| Top up account from Treasury | ✓ (firm capital only)                        | ✓ (Unity pool)             | ✗ (client deposits)     | ✓                       | ✓ (firm capital) or ✗ (SMA) | N/A                    |
| Cross-venue rebalance        | ✓ (firm capital only)                        | ✗ (single Unity account)   | ✗ (per-client SMA)      | ✓                       | ✗                           | N/A                    |
| Internal venue wallet move   | ✓ (swap protocol → protocol)                 | Unity internal (automatic) | ✓ (Binance SAPI, etc.)  | ✓                       | ✗ (IBKR automatic)          | N/A                    |
| Bridge cross-chain           | ✓                                            | ✗                          | ✗                       | ✗                       | ✗                           | N/A                    |
| Client withdrawal            | Client-initiated                             | Firm-initiated             | Client-initiated        | Administrator-initiated | Client-initiated            | Counterparty-initiated |
| Margin health top-up         | ✓ (firm only) or strategy-reduction (client) | ✓ (Unity pool)             | Strategy-reduction only | ✓                       | ✓ (firm) or ✗ (SMA)         | N/A                    |

## Section 8: Onboarding Summary (what each client needs to provide / do)

| Category                         | What client provides                                                 | What we configure                                                                                                                                       | Expected timeline |
| -------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------- |
| DeFi via Copper                  | Copper workspace + signing policy approved by them + API credentials | Add client wallet addresses to execution adapter; register credentials in Secret Manager; configure Transfer/Rebalance service with client wallet graph | 1-3 days          |
| DeFi via Fireblocks              | Fireblocks workspace + MPC quorum + API credentials                  | Similar to Copper                                                                                                                                       | 1-3 days          |
| Sports Unity (pool contribution) | USD deposit to Unity pool (tracked in firm ledger as client share)   | Register client share in internal ledger; Portfolio Allocator includes client in sports strategies                                                      | Same day          |
| CeFi SMA                         | CEX account + deposit + API keys (trade-only)                        | Register API keys in Secret Manager; activate venue adapter for client; run test trade                                                                  | 1-2 days          |
| CeFi fund (future)               | Fund subscription via administrator                                  | Standard fund subscription workflow                                                                                                                     | 1-2 weeks         |
| TradFi IBKR SMA                  | IBKR sub-account + deposit + FIX API permission                      | Register sub-account in FIX gateway config; run test trade                                                                                              | 3-5 days          |
| TradFi counterparty direct       | Counterparty connection details + signal delivery spec               | Configure signal export format; establish reconciliation feed                                                                                           | 1-2 weeks         |

## Section 9: P&L Attribution by Custody Mode

P&L attribution works the same at the event level regardless of custody — every fill is tagged with (strategy_instance,
client_id, etc.). But how P&L is realized and reported differs:

| Mode                       | P&L realized as                                    | Reported to client as                               | Tax considerations                                                       |
| -------------------------- | -------------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------ |
| DeFi client wallet         | On-chain balance change on client wallet           | Per-transaction + rolled-up daily/monthly           | Client's responsibility; we provide audit trail                          |
| Sports Unity pool          | Proportional share of Unity pool P&L (firm ledger) | Share-based allocation with 1099/T5 equivalent      | Firm tracks client shares; reports fund-level P&L                        |
| CeFi SMA                   | CEX account balance change                         | Per-venue balance statement + our aggregated report | Client's responsibility via CEX statements; we provide trade-level audit |
| CeFi fund                  | Fund NAV change                                    | Fund share statement via administrator              | Administered by fund structure                                           |
| TradFi IBKR SMA            | IBKR account balance change                        | IBKR 1099 + our trade-level report                  | Client's responsibility; IBKR handles tax forms                          |
| TradFi counterparty direct | Counterparty-reported P&L                          | Per-counterparty report                             | Counterparty-managed                                                     |

## Section 10: Regulatory Posture

**Not legal advice — this is operational context only. Consult compliance for every jurisdiction.**

| Activity                       | Typical regulatory status                                                        | Our posture                                                              |
| ------------------------------ | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------ |
| DeFi trading on client wallet  | Varies; generally not regulated when client retains custody                      | Act as agent under client delegation; audit trail per tx                 |
| Sports pool management (Unity) | Varies by jurisdiction; often not classified as securities activity              | Operate under firm's permission set; pool structure approved             |
| CeFi SMA trading               | Typically regulated as investment advisory; may require registration             | Register as required per jurisdiction; operate under SMA agreement       |
| CeFi fund operations           | Regulated as a fund; requires offering memo, administrator, audits               | Engage third-party administrator; comply with fund regulations           |
| TradFi IBKR SMA                | Regulated as investment advisory (US: Form ADV); introducing broker relationship | Register as investment advisor per US SEC / equivalent                   |
| TradFi counterparty direct     | Various (not typically our regulatory scope)                                     | Provide signals only; counterparty responsible for regulatory compliance |

## Section 11: What Goes Where in Code and Infra

| Concern                                     | Service / doc                                                           | Scope                                   |
| ------------------------------------------- | ----------------------------------------------------------------------- | --------------------------------------- |
| Credential storage                          | Secret Manager (GCP default)                                            | All categories                          |
| Credential rotation policy                  | `/codex/07-security/secret-rotation.md`                                 | Cross-category                          |
| Custodian API adapters (Copper, Fireblocks) | `execution-service/adapters/copper.py`, `fireblocks.py`                 | DeFi                                    |
| Unity execution adapter                     | `execution-service/adapters/unity.py` (with Java sidecar for feed)      | Sports                                  |
| CEX adapters (per-CEX)                      | `execution-service/adapters/{binance,okx,bybit,deribit,hyperliquid}.py` | CeFi                                    |
| IBKR FIX gateway                            | `execution-service/adapters/ibkr.py`                                    | TradFi                                  |
| Transfer/Rebalance service                  | `transfer-rebalance-service/` (new service)                             | Cross-category                          |
| Treasury wallet state                       | PBMS tracks as a "venue" with type=TREASURY                             | DeFi firm + Unity + fund mode           |
| Per-client SMA isolation                    | Secret Manager path structure + PBMS dimension                          | CeFi SMA + TradFi IBKR SMA              |
| Fund subscription tracking                  | `portfolio-allocator-service` (client share state)                      | Unity pool + future CeFi fund           |
| On-chain bridging logic                     | `execution-service/bridge_handlers/*.py` + UAC bridge registry          | DeFi                                    |
| Internal venue transfers                    | Per-venue adapter's `transfer()` method                                 | CeFi                                    |
| Cross-venue transfers (firm money)          | Transfer/Rebalance service                                              | DeFi firm, CeFi fund, TradFi firm-money |

## Section 12: Validation Checklist

For each new client onboarding:

- [ ] Venue category determined
- [ ] Custody model matches (SMA / pool / fund / firm)
- [ ] Custodian registered (if DeFi)
- [ ] Credentials stored in Secret Manager
- [ ] Credentials scope verified (no withdrawal)
- [ ] Test transfer / trade executed
- [ ] PBMS reconciles expected balance
- [ ] Portfolio Allocator registered client with share_class
- [ ] Risk limits configured per client + strategy
- [ ] Onboarding confirmation + audit trail generated

For each strategy going live:

- [ ] Archetype identified
- [ ] Config hash registered in UAC
- [ ] Eligible venues match client's onboarded custody mode
- [ ] Share class matches client's funding currency
- [ ] Backtest run on same config via Group B
- [ ] Shadow deploy (paper) for N days before real money
- [ ] R&E limits registered
- [ ] Kill switch configuration validated
- [ ] Cutover audit sign-off

## See Also

- [capital-flow-model.md](capital-flow-model.md) — mechanical protocol for capital flow (TRANSFER / BRIDGE /
  AllocationDirective)
- [strategy-execution-protocol.md](strategy-execution-protocol.md) — instruction catalog
- [/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md](/codex/09-strategy/architecture-v2/cross-cutting/transfer-rebalance.md)
  — service spec
- [/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md](/codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md)
  — allocator spec
- [/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md](/codex/09-strategy/architecture-v2/cross-cutting/venue-account-coordination.md)
  — shared-account primitives
- [/codex/02-venues/venue-registry-reference.md](/codex/02-venues/venue-registry-reference.md) — venue list with custody
  mode per venue
- [/codex/02-venues/unity-integration.md](/codex/02-venues/unity-integration.md) — Unity specifics
