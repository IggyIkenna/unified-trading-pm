---
doc_type: codex-ssot
title: Elysium / POD — Account trajectory + upsell roadmap
summary:
  Internal 24-month Elysium/POD ARR trajectory and upsell roadmap — phased retainer ($3k→$9k+/mo), Carry & Yield
  archetype subscription waterfall, venue-expansion menu ($2.5k/venue, CME $15-25k), cross-sell of non-C&Y families, AUM
  capital-scaling tiers, and the sales-conversation calendar.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-api-contracts]
scope: [admin, sales]
tags: [commercial-model, elysium, defi, upsell, exclusivity, revenue, sla]
related:
  [
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/managed-defi-sla-cost-build.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
    /codex/14-customer-journeys/commercial-model/signal-leasing.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
  ]
created: 2026-05-20
authoritative_for: [Elysium/POD account trajectory and upsell roadmap]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/managed-defi-sla-cost-build.md,
  ]
owner:
last_reviewed:
code_refs: [unified-api-contracts/unified_api_contracts/registry/venue_collateral.py]
---

# Elysium / POD — Account trajectory + upsell roadmap

> **Created 2026-05-14** alongside [`elysium-managed-sla-2026-05-14.md`](elysium-managed-sla-2026-05-14.md). Captures
> the _commercial trajectory_ we see with Elysium / POD over the 24 months following Phase 2 acceptance: the locked
> managed SLA, the additional Carry & Yield archetypes we expect them to subscribe to, the venue-expansion upsell
> schedule, and the cross-sell of other strategy families. Used internally to set ARR targets and to sequence sales
> conversations.
>
> **Audience**: admin + sales internal planning. Codex-private per [rule 08](../_ssot-rules/08-pricing-principles.md) —
> numbers below never appear in client-facing quotes verbatim, though the _menu of options_ (venue upgrades, archetype
> add-ons) can be shared with Elysium at the right cadence.
>
> **Companion docs**: [`elysium-managed-sla-2026-05-14.md`](elysium-managed-sla-2026-05-14.md) — SLA structure + cost
> model; [`managed-defi-sla-cost-build.md`](managed-defi-sla-cost-build.md) — reusable cost-build template;
> [`exclusivity-and-noncompete.md`](exclusivity-and-noncompete.md) — exclusivity pricing framework;
> [`signal-leasing.md`](signal-leasing.md) — strategy IP licensing primitives.

---

## §1 — Headline ARR trajectory

| Period                                                                    | Fixed retainer (USD/mo) | Performance share                                                                                     | Annualised fixed | Notes                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------------------- | ----------------------- | ----------------------------------------------------------------------------------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Phase 0** (now → 2026-06 Phase 2 acceptance)                            | $0                      | $0                                                                                                    | $0               | **Consulting fee revised $90k → $135k** under variation (DeFi backtesting + live execution + treasury auto-rebalancing + Copper/CEFFU integration). **$90k paid; $45k remaining** on Phase 2 production acceptance. Not retainer; one-off consulting fee under the original contract + variation. |
| **Phase 1** (2026-07 → 2026-09, 3 months managed-SLA shakedown)           | $3,000                  | tiered (25% first $100M AUM, 10% above) of POD perf fees on `CARRY_STAKED_BASIS` + `CARRY_BASIS_PERP` | $36k             | Inaugural sole-client; subsidising real cost ~$1.3k/mo                                                                                                                                                                                                                                            |
| **Phase 2** (2026-10 → 2027-03, 6 months venue + LST expansion)           | $4,500                  | 25% on same archetypes, expanded venue surface                                                        | $54k             | +1 archetype OR +3 venues land                                                                                                                                                                                                                                                                    |
| **Phase 3** (2027-04 → 2027-09, 6 months Carry & Yield family completion) | $6,500                  | 25% on all subscribed C&Y archetypes                                                                  | $78k             | 3-4 Carry & Yield archetypes live                                                                                                                                                                                                                                                                 |
| **Phase 4** (2027-10 → 2028+, cross-sell other families)                  | $9,000+                 | 25%/10% tier on C&Y; per-family rate on non-C&Y (10-25%)                                              | $108k+           | First non-Carry-and-Yield archetype lands                                                                                                                                                                                                                                                         |

**One-time fees layered over the above** (Phase 2 / 3 / 4 expansions): see §3, §4, §5.

**ARR projection**:

- Year 1 (2026-07 → 2027-06): **~$45k fixed** + perf share (depends on POD's downstream fees) + ~$15-25k one-time
  expansion fees ≈ **$60-90k revenue from Elysium alone**.
- Year 2 (2027-07 → 2028-06): **~$80k fixed** + perf share + ~$30-50k one-time ≈ **$130-180k**.
- Year 3+: depends on cross-sell + AUM growth.

These are **target trajectories, not commitments** — Elysium can decline any expansion. The sales conversation calendar
drives this (§6).

---

## §2 — Strategy archetype subscription waterfall (Carry & Yield family)

**Important framing per SLA Exhibit B**: Art. 6.2 non-compete applies _only_ to the Strategy / venue / LST combinations
actually delivered under the Consulting Agreement — i.e. `CARRY_STAKED_BASIS` on OKX/Bybit/Lido and `CARRY_BASIS_PERP`
on OKX/Bybit/Binance. Other Carry & Yield archetypes we've independently designed, and the same In-Scope archetypes on
_different_ venues/chains/LSTs, are **outside the non-compete**.

We still offer them to Elysium first as a commercial courtesy (right of first refusal, 30-day window), but if they
decline we are free to operate them on our own book or for other clients without breach. This is a softer commercial
lock than a contractual one — we control timing and economics rather than being held to a 24-month wait.

### 2.1 In Phase 2 acceptance scope (locked, included in original $90k consulting fee)

| Archetype            | In scope on (venue, LST)              | Status  |
| -------------------- | ------------------------------------- | ------- |
| `CARRY_STAKED_BASIS` | OKX/wstETH (Lido), Bybit/stETH (Lido) | Phase 2 |
| `CARRY_BASIS_PERP`   | OKX, Bybit, Binance                   | Phase 2 |

### 2.2 Additional Carry & Yield archetypes we expect Elysium to subscribe to (sequenced upsell)

> Each is offered to Elysium first under Art. 6.2 right-of-first-refusal. If declined within 30 days, IkeNova retains
> the right to operate that archetype on its own book or for other clients (per Exhibit B of the SLA).

| #   | Archetype                                                                                   | One-time integration | Δ monthly retainer | Exclusivity premium (Tier B)                        | When to pitch                                                                                                     |
| --- | ------------------------------------------------------------------------------------------- | -------------------- | ------------------ | --------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 1   | `YIELD_STAKING_SIMPLE` (passive LST hold, no perp)                                          | $7,500               | +$500/mo           | +$500/mo if exclusive within DeFi-allocator segment | Month 3 post-acceptance — simplest add-on, baseline yield enhancement on idle USDC sleeves                        |
| 2   | `CARRY_RECURSIVE_STAKED` (leveraged staked basis with flash-loan recursion)                 | $15,000              | +$1,000/mo         | +$1,000/mo if exclusive                             | Month 4-6 — once CARRY_STAKED_BASIS has 3+ months of clean P&L, leverage variant is the natural next conversation |
| 3   | `YIELD_ROTATION_LENDING` (cross-protocol lending-rate rotation: Aave/Compound/Morpho/Spark) | $12,000              | +$750/mo           | +$750/mo if exclusive                               | Month 4-6 — independent capital allocation track; can run alongside                                               |
| 4   | `CARRY_BASIS_DATED` (dated futures variant, term-structure basis capture)                   | $18,000              | +$1,000/mo         | +$1,500/mo if exclusive                             | Month 6-9 — requires dated-perp venue (Deribit + CME); more complex commercially                                  |
| 5   | `CARRY_RECURSIVE_BORROW_LENDING_ONLY`                                                       | $12,000              | +$750/mo           | +$750/mo if exclusive                               | Month 9-12 — only if Elysium hasn't taken `YIELD_ROTATION_LENDING` — adjacent variant                             |
| 6   | `CARRY_RECURSIVE_BORROW_PERP_HEDGED`                                                        | $18,000              | +$1,250/mo         | +$1,250/mo if exclusive                             | Month 9-12 — only if `CARRY_RECURSIVE_STAKED` has been adopted                                                    |

**Total upsell potential within Carry & Yield family**: ~$83k one-time + ~$5.25k/mo additional retainer
($63k/y) +
~$5.5k/mo exclusivity premia ($66k/y) = **~$83k upfront + ~$129k/y ongoing**, on top of the base $36k/y
retainer.

### 2.3 Exclusivity pricing rationale

Per [`pricing-building-blocks.md`](pricing-building-blocks.md) Block 12 (Exclusivity / non-compete premium): 20–200%
uplift on Tier B monthly, by IP-power tier. For Carry & Yield context with Elysium:

- **Implicit exclusivity exists ONLY on the In-Scope Strategy/venue combinations actually delivered** (Art. 6.2
  non-compete + SLA Exhibit B). Elysium has paid for it via the $90k consulting fee. We shouldn't double-charge on
  those.
- **Explicit exclusivity premium applies to _new_ archetypes** we ship after Phase 2 acceptance — the §2.2 list. These
  are _outside_ Art. 6.2 (per Exhibit B), so no implicit lock exists; if Elysium wants exclusivity within the
  DeFi-allocator segment, they pay the premium.
- **Tier C IP-power applies** (per [`managed-defi-sla-cost-build.md`](managed-defi-sla-cost-build.md) §4) — these are
  single-source strategies; no alternative provider. Exclusivity premium = ~100% uplift on the +Δ retainer, i.e. roughly
  doubles the monthly add for each archetype.

If Elysium declines exclusivity but still subscribes to the archetype: half premium applies (we can sell to others, but
they have priority on incident response + new venue prioritisation).

---

## §3 — Venue expansion roadmap (for in-scope archetypes)

For `CARRY_STAKED_BASIS` + `CARRY_BASIS_PERP` (and later archetypes), each additional venue adds a slot to the
strategy's tradeable universe and triggers a one-time fee. Per
[`elysium-managed-sla-2026-05-14.md`](elysium-managed-sla-2026-05-14.md) §3.2 the default is $2,500 one-time per venue.

### 3.0 LST scope boundary — Client must secure venue-side acceptance first

`CARRY_STAKED_BASIS` requires the LST to be accepted as **cross-margin** at the perp venue (LST_AS_MARGIN structure).
This is why the In-Scope list starts with **Lido on OKX (wstETH) + Lido on Bybit (stETH)** only — those are the only
LST/venue pairs with native cross-margin acceptance today.

To add Rocket Pool rETH, Coinbase cbETH, EtherFi eETH, Mantle mETH, Frax sfrxETH, Jito jitoSOL, Marinade mSOL, Binance
bETH, or any other LST, the **Client must first secure venue-side cross-margin acceptance** via one of:

- Direct venue acceptance (Bybit/OKX/etc. add the LST to their cross-collateral list — Client/POD negotiates with
  venue's institutional team)
- Tri-party mirrored collateral via Copper.co or CEFFU (LST held at custodian, custodian posts equivalent USDC/USDT
  margin at the venue under OES/mirror arrangement — Client arranges tri-party agreement)
- Prime broker line of credit (PB accepts LST against Client's account, extends credit line at venue — Client arranges
  PB relationship)

**This is Client-side commercial relationship work, NOT in our scope.** Our $2.5k fee only covers the engineering
integration once venue-side acceptance is in place: matrix row + wrap-step discriminator + on-chain rate reader +
rebasing reconciliation + haircut/kill-switch calibration + runbook + cutover. SLA §4.3.1 spells out the boundary,
trigger ("Client provides written confirmation of venue-side acceptance"), and the hourly fallback if venue-side
acceptance is withdrawn mid-integration.

**Sales conversation framing**: when pitching new LST adoption, the pitch is two-step:

1. "Here's the LST + venue combination — go work with your venue / Copper / prime broker to get it accepted as
   cross-margin"
2. "Once you have written acceptance, we plug it in for $2.5k in 50-100 hours"

If the Client struggles to secure venue acceptance, that's a deal that doesn't progress. Don't waste engineering time on
speculative LST integration.

### 3.1 Venue upgrade menu (DeFi-allocator-relevant)

| Venue                               | Strategy applicability                                                                                            | One-time fee        | Δ retainer                                               | Notes                                                                                                                                                    |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Deribit**                         | CARRY_STAKED_BASIS (stETH at 7.5% haircut, cross-collateral with ETH-perp); CARRY_BASIS_PERP (BTC-PERP, ETH-PERP) | $2,500              | +$0 (folded into $3k retainer if within 12 venues total) | Already on roadmap; high priority — natively supports stETH offset of ETH-perp                                                                           |
| **Hyperliquid**                     | CARRY_BASIS_PERP only (USDC-only margin; doesn't accept LSTs)                                                     | $2,500              | +$0                                                      | High-volume L1 perp DEX; popular with allocators                                                                                                         |
| **Aster**                           | CARRY_BASIS_PERP only (USDT/USDF/asBNB only)                                                                      | $2,500              | +$0                                                      | Newer perp DEX; emerging volume                                                                                                                          |
| **Drift**                           | CARRY_STAKED_BASIS (JitoSOL/mSOL margin); CARRY_BASIS_PERP (SOL-PERP)                                             | $2,500              | +$0                                                      | Already partially scoped via existing platform; Solana side                                                                                              |
| **Kraken Futures**                  | CARRY_BASIS_PERP only                                                                                             | $2,500              | +$0                                                      | TradFi-adjacent CeFi venue                                                                                                                               |
| **Bitfinex**                        | CARRY_BASIS_PERP only                                                                                             | $2,500              | +$0                                                      | Lower priority; thin volume on relevant pairs                                                                                                            |
| **Bitget**                          | CARRY_BASIS_PERP only                                                                                             | $2,500              | +$0                                                      | Lower priority                                                                                                                                           |
| **GMX**                             | CARRY_BASIS_PERP only (no LST collateral)                                                                         | $3,000              | +$0                                                      | DEX perp; needs different adapter pattern (GMX removed 2026-07-25 — see `plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; no longer offered) |
| **CME** (BTC/ETH futures + options) | TradFi adapter — CARRY_BASIS_DATED is the natural fit; CARRY_BASIS_PERP also possible                             | **$15,000–$25,000** | **+$1,500/mo**                                           | TradFi regulated venue; requires reg-reporting layer; AML/KYC infra; clearing-broker integration                                                         |

### 3.2 Venue bundles (discounted)

To incentivise broader venue coverage rather than one-at-a-time:

- **"DeFi-allocator basis bundle"** — Deribit + Hyperliquid + Aster + Drift commissioned together: **$8,000** (vs $10k
  individually) — saves $2k.
- **"Full CeFi perp coverage"** — adds Kraken Futures + Bitfinex + Bitget on top: **+$5,000** (vs $7.5k individually) —
  saves $2.5k.
- **"CME TradFi onramp"** — CME alone with reg-reporting layer: **$20,000** + +$1,500/mo retainer increase for ongoing
  TradFi reg-reporting + clearing-broker oversight.

### 3.3 Why CME is priced an order of magnitude higher

CME isn't a "new venue" in the DeFi sense — it's a new **regulatory environment**:

- New TradFi adapter family (FIX protocol, not REST/WebSocket)
- Clearing-broker relationship (we need a clearing FCM)
- Reg-reporting infrastructure (CFTC large-trader reports, position-limit monitoring)
- Settlement workflow (T+1 cash margin, not crypto wallet)
- Margin calculations (SPAN, not haircut-based)
- 50-100 hours of _engineering_ isn't enough; closer to **200-400 hours** + ongoing reg-reporting overhead

Charge for CME signals "this is materially more than a venue add" and primes Elysium to either fund it properly or
defer.

---

## §4 — Cross-sell of non-Carry-and-Yield strategy families

After 12+ months on Carry & Yield, if Elysium has appetite for further allocations, the other strategy families come
into play. These were **never in scope of the original Consulting Agreement** (per Annex A — basis trading only), so
Art. 6.2 non-compete does NOT apply to them. We can sell them to Elysium or anyone else.

### 4.1 Strategy family upsell menu

| Family                      | Archetypes available today                                        | SOW floor               | Δ monthly retainer | Performance share (Tier B/C)           | Pitch month                                                                                 |
| --------------------------- | ----------------------------------------------------------------- | ----------------------- | ------------------ | -------------------------------------- | ------------------------------------------------------------------------------------------- |
| **Arbitrage**               | `ARBITRAGE_PRICE_DISPERSION` (active), `ARBITRAGE_MEV_*` (paper)  | $25,000                 | +$1,500/mo         | 15% (Tier B)                           | Month 12-15 — natural complement to basis (different risk factor)                           |
| **Stat-Arb**                | `STAT_ARB_PAIRS_FIXED`, `STAT_ARB_CROSS_SECTIONAL`                | $30,000                 | +$1,500/mo         | 15% (Tier B)                           | Month 15-18 — once basis P&L narrative is established, statistical alpha becomes credible   |
| **DeFi LP**                 | `DEFI_LP_POOL`, `DEFI_LP_CONCENTRATED`, `DEFI_LP_VAULT`           | $25,000 (per archetype) | +$1,000/mo each    | 20% (Tier B+)                          | Month 12-15 — LP fees are DeFi-native; pairs naturally with Carry & Yield narrative         |
| **Yield Rotation expanded** | already covered in C&Y §2.2 but ML-overlay variant available      | $20,000 ML overlay      | +$1,500/mo         | 20% (overlay tier)                     | Month 18+ — once basic rotation has track record                                            |
| **Vol Trading**             | `VOL_TRADING_OPTIONS` (Deribit + CME options)                     | $40,000                 | +$2,500/mo         | 20% (Tier B+)                          | Month 18-24 — requires Deribit options venue scope; serious capital threshold               |
| **Market Making**           | `MARKET_MAKING_CONTINUOUS`, `MARKET_MAKING_EVENT_SETTLED`         | $50,000                 | +$3,000/mo         | 15% (Tier B; high-capacity infra cost) | Month 24+ — only if Elysium specifically wants MM exposure (different fund mandate usually) |
| **ML-Directional**          | `ML_DIRECTIONAL_CONTINUOUS`, `ML_DIRECTIONAL_EVENT_SETTLED`       | $45,000                 | +$2,500/mo         | 25% (Tier C — proprietary models)      | Month 18+ — directional risk, different fund mandate                                        |
| **Rules-Directional**       | `RULES_DIRECTIONAL_CONTINUOUS`, `RULES_DIRECTIONAL_EVENT_SETTLED` | $25,000                 | +$1,500/mo         | 15% (Tier B)                           | Month 15+ — simpler than ML; faster path                                                    |
| **Event-Driven**            | `EVENT_DRIVEN`                                                    | $30,000                 | +$1,500/mo         | 20% (Tier B+)                          | Month 18+ — depends on Elysium's appetite for event risk                                    |
| **Liquidation Capture**     | `LIQUIDATION_CAPTURE`                                             | $25,000                 | +$1,500/mo         | 20% (Tier B+)                          | Month 15+ — DeFi-native; pairs naturally                                                    |

**Discipline**: don't pitch more than one new family per quarter. Sequencing matters; over-pitching dilutes the
narrative and risks Elysium pushing back on the base retainer.

### 4.2 Exclusivity for cross-sold non-C&Y strategies

Unlike Carry & Yield (where Art. 6.2 already gives implicit 24-month exclusivity), non-C&Y strategies have **no
contractual exclusivity baseline**. If Elysium wants exclusivity on a non-C&Y strategy within the DeFi-allocator
segment, the Block 12 premium applies as an additive line:

- **Within DeFi-allocator segment exclusivity** (we won't sell same archetype to another DeFi-allocator): +50% on Tier B
  retainer for that archetype.
- **Within institutional segment exclusivity** (we won't sell to any institutional allocator — fund admins, family
  offices, prime brokers): +100% on Tier B retainer.
- **Full single-source exclusivity** (we won't sell to anyone, including our own book): +200% on Tier B retainer.

Most DeFi-allocator buyers take the within-segment tier (+50%). Full exclusivity is rarely worth it commercially.

---

## §5 — Capital scaling tiers

The base $3k/mo retainer assumes Elysium AUM-allocated to the in-scope Strategies stays below $50M. Beyond that,
infrastructure cost-to-serve grows non-linearly (rate-limit quota purchases, dedicated VMs, separate cluster tier).
Anticipated tiers:

| AUM tier (USD) | Retainer multiplier | Notes                                                                                                     |
| -------------- | ------------------- | --------------------------------------------------------------------------------------------------------- |
| < $50M         | 1.0×                | Base tier                                                                                                 |
| $50M – $100M   | 1.25×               | Dedicated VM allocation; increased rate-limit quotas                                                      |
| $100M – $250M  | 1.5×                | Separate execution cluster; dedicated L1 operator share                                                   |
| $250M – $500M  | 2.0×                | Dedicated infrastructure tier; dedicated engineering allocation                                           |
| > $500M        | Bespoke negotiation | New SOW; likely IM-style structure (see [`im-profit-share-structures.md`](im-profit-share-structures.md)) |

These multipliers apply to the **base retainer** including all subscribed archetype add-ons + exclusivity premia.

---

## §6 — Sales conversation calendar

Working back from the trajectory:

| Cadence       | Touchpoint                                                   | Owner                  | Topic                                                          | Sales asset                           |
| ------------- | ------------------------------------------------------------ | ---------------------- | -------------------------------------------------------------- | ------------------------------------- |
| Monthly       | Investor-style strategy report (P&L, attribution, narrative) | IkeNova ops            | Performance — sets the narrative for "this works, more please" | Standard monthly report               |
| Quarterly     | Strategy review + roadmap pitch                              | Ikenna or Saabii_Boi   | New venue + new archetype proposals                            | One-page menu (subset of §2.2 / §3.1) |
| Semi-annually | Commercial review                                            | Ikenna                 | Retainer tier re-assessment + AUM-tier check                   | Renewal memo                          |
| Annually      | Strategic review                                             | Ikenna + Patrick Lynch | Cross-family conversation (§4) + multi-year roadmap            | Multi-year proposal                   |
| Ad-hoc        | New venue announcement (e.g. new perp DEX launches)          | Saabii_Boi             | Tactical venue upgrade pitch                                   | Single-venue brief                    |
| Ad-hoc        | New end-client share class onboarding                        | Saabii_Boi             | Reminder on 10h/mo allowance + overage rate                    | Onboarding-fee schedule               |

**Discipline**: don't pitch a roadmap expansion until current month's P&L narrative is clean. Failed-month pitches don't
land.

---

## §7 — Risks to trajectory

| Risk                                                                                                       | Mitigation                                                                                                                                                                                                                                                       |
| ---------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Elysium goes self-run (carve-out Option B) at Day 30 — retainer evaporates                                 | Performance share survives the carve-out (per SLA §6) — protects core economics. Self-run hand-over fee ($15k) captures some of the lost retainer up front.                                                                                                      |
| Strategy underperforms in first 3 months — Elysium loses confidence                                        | Retainer fixed regardless; performance share absorbs the disappointment. Use first 3 months for venue + LST expansion to broaden the carry surface and recover narrative.                                                                                        |
| POD's end-client fee structure is opaque or sub-economic (e.g. they only charge 0.5% mgmt and no perf fee) | Audit right (SLA §5.2). If they truly don't charge perf fees, performance share is moot — re-negotiate to higher fixed retainer ($5k/mo) at the 6-month review.                                                                                                  |
| Elysium acquires us / changes corporate structure                                                          | Contract Art. 7.7 (Successors and Assigns) — agreement survives. Negotiate carefully on any change-of-control.                                                                                                                                                   |
| Another DeFi-allocator wants Carry & Yield strategy from us                                                | Art. 6.2 blocks us for 24 months without Elysium written waiver. Either (a) wait out 24 months, (b) request waiver from Elysium (likely declined unless we offer a finder's fee), (c) deliver a clearly differentiated variant outside Art. 6.2's literal scope. |
| Elysium / POD churns to a different provider                                                               | Performance share survives ("for as long as Strategy runs"); negotiate enforcement carefully. Self-run hand-over fee anchors a partial offboarding.                                                                                                              |
| Regulatory / fund-structure change at Elysium causes scope contraction                                     | Quarterly review identifies this early; downgrade tier gracefully.                                                                                                                                                                                               |

---

## §8 — Cross-references

- SLA structure + cost model: [`elysium-managed-sla-2026-05-14.md`](elysium-managed-sla-2026-05-14.md)
- Reusable cost-build template: [`managed-defi-sla-cost-build.md`](managed-defi-sla-cost-build.md)
- POD/Elysium entity stack + custody onboarding:
  [`../pod-elysium-client-onboarding.md`](../pod-elysium-client-onboarding.md)
- Strategy archetype catalogue:
  [`../../09-strategy/architecture-v2/archetypes/`](../../09-strategy/architecture-v2/archetypes/)
- Carry & Yield family overview:
  [`../../09-strategy/architecture-v2/families/carry-and-yield.md`](../../09-strategy/architecture-v2/families/carry-and-yield.md)
  (if present)
- Venue collateral SSOT: `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py`
- DART pricing anchors: [`pricing-building-blocks.md`](pricing-building-blocks.md)
- Exclusivity pricing framework: [`exclusivity-and-noncompete.md`](exclusivity-and-noncompete.md)
- Signal-leasing (alternative IP-licensing shape): [`signal-leasing.md`](signal-leasing.md)
- IM performance-fee mechanics: [`im-profit-share-structures.md`](im-profit-share-structures.md)
