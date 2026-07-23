---
doc_type: codex-ssot
title: Cash Deployment Plan — April 2026 Starting £240k
summary:
  Codex-private cash-deployment plan from April 2026's ~£240k ($305k) opening cash — ~£34k/mo burn, committed
  deployments (backtest £25-50k, CME $50k skin Sept, ~10%-of-revenue eng profit-share), a ~£150k minimum reserve floor,
  and upside/downside deployment triggers.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [admin]
tags: [commercial-model, cash-flow, finance, cost, reserve-policy, cme]
related:
  [
    /codex/14-customer-journeys/commercial-model/revenue-projection-2026-monthly.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
  ]
created: 2026-04-20
authoritative_for: [2026 cash-deployment and reserve-buffer plan]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/commercial-model/revenue-projection-2026-monthly.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Cash Deployment Plan — April 2026 Starting £240k

> **CODEX-PRIVATE / INTERNAL** per rule 08. Finance-sensitive. Do NOT surface on client-facing docs, demos, or website.

**Cross-refs:** [revenue-projection-2026-monthly.md](revenue-projection-2026-monthly.md) for the revenue side;
[pricing-building-blocks.md](pricing-building-blocks.md) for unit pricing;
[im-profit-share-structures.md](im-profit-share-structures.md) for CME co-invest structure.

## Starting position

- **Cash in bank April 2026**: $305k = **~£240k** at 0.79 GBP/USD.
- **Monthly burn**: ~£34k steady-state.
- **Runway at current burn (no new revenue)**: £240k / £34k = **~7 months**.

This is a comfortably funded position. Framing is **cash deployment** (how we use the buffer to fund growth), not **cash
runway** (survival).

## Committed deployments 2026

### Backtest + paper-testing startup costs (Apr-May)

- **£25-50k one-time** for the full combinatoric backtest sweep + 1-2 week paper testing across all strategy archetypes
  × categories × instrument types. Required to unblock "ready to ship" status for 2026 strategy launches.
- Spread Apr-May at approximately £15k/mo each.
- Funded from opening cash; absorbed without stress.

### CME skin-in-the-game (Sept)

- **$50k = ~£40k** deposited into the co-investment vehicle at CME go-live.
- Per the CME deal structure: Odum puts $50k alongside client's $500k allocation; profits 70/30 Odum-favour; losses
  10/90 Odum-favour. See [im-profit-share-structures.md](im-profit-share-structures.md).
- **Funding source**: operating cash (~£249k expected at end-Aug after ramp). Absorbs easily.
- Skin-in-the-game scaling decision (S1 flat / S2 pro-rata / S3 reduced ratio) pending client close. Default posture:
  **S1 flat at $50k**.

### Engineering team profit share (ongoing, revenue-based)

- Modelled at **~10% of revenue** on top of base salary.
- 2026 total estimate: £66k across the year (0.10 × £636k, post Signal-leasing revision 2026-04-20).
- Mechanically variable — low months cost ~£1k, high revenue months cost ~£14k. Aligns team compensation with firm
  performance.
- Mechanism to confirm with team: ordinary income (taxable in-year) vs equity-like (delayed vesting).

## Reserve policy — H2 2026 minimum cash buffer

Maintain a **minimum cash buffer of ~£150k at all times** through 2026. Rationale:

- Covers ~4.5 months of burn in a total-revenue-loss scenario (highly unlikely but operational prudence).
- Covers the CME skin-in-the-game + 2-3 months of downside burn if Desmond and India Options both slip.
- Covers 2027 first-quarter ramp costs if strategies need to shift in Q1 2027.

Against the monthly cashflow model, the projected minimum is **£198k in April** — above the £150k floor with margin.

## Deployment priorities if upside exceeds base case

If year-end cash exceeds £500k (upside scenario):

1. **Advance engineering headcount to 4.5 FTE earlier** (originally planned Q1 2027 at 3.5). Could ship strategy
   launches faster and handle operational load of more clients.
2. **Pre-fund 2027 startup costs** for the next wave of strategy archetypes (market-making, advanced options,
   cross-chain arbitrage). Pulls forward ~£50-80k of backtest-ready infrastructure work.
3. **Seed second co-invest mandate** similar to CME structure but different venue / instrument family. Requires
   ~£50-100k capital commitment to sign a similar client.
4. **Signal leasing integration platform** — build out the productised signal-delivery infrastructure for scaling to 5+
   counterparties (needs ~£30-50k of engineering time wrapped in current team capacity, but accelerates with an extra
   seat).

## Deployment triggers if downside materialises

If year-end cash falls below £300k (downside scenario):

1. **Cut discretionary burn by £5-8k/mo**: defer TradFi data subscription if India Options slipping, scale AI model
   costs to cheaper tiers, audit SaaS licences.
2. **Delay 2027 headcount advance** (stay at 2.5 FTE through Q1 2027).
3. **Pull forward 2027 revenue opportunities** — close Desmond fully-paid before Dec if possible; push India Options to
   extract some 2027 allocation fees in Dec 2026.
4. **Consider short working-capital facility** (~£50-100k) as insurance against CME skin + 2027 ramp cost coincidence.
   Only if projected minimum cash drops below £100k.

## Cash flow through 2026 (per revenue-projection-2026-monthly.md)

| Month             | Net change £k | Cumulative cash £k |
| ----------------- | ------------- | ------------------ |
| Apr (opens £240k) | -42           | 198                |
| May               | +9            | 207                |
| Jun               | +22           | 229                |
| Jul               | +17           | 246                |
| Aug               | +2            | 248                |
| Sep               | -7            | 241                |
| Oct               | +92           | 333                |
| Nov               | +46           | 379                |
| Dec               | +34           | **413**            |

**Minimum £198k (April), maximum £413k (December). Above £150k reserve floor throughout.** (Revised 2026-04-20 to
reflect Signal-leasing anchor of ~$5k/mo combined from Sept 2026 — see `revenue-projection-2026-monthly.md` §Revision
note.)

## 2027 entry position

Year-end 2026 cash £413k entering 2027. At 2027 burn ~£45k/mo (3.5 FTE), that's ~9 months of runway on cash alone before
considering 2027 revenue. Combined with projected 2027 revenue £2M+ per the deck trajectory, the business is
self-funding indefinitely without external capital.

## What this does NOT cover

- **Regulatory capital adequacy**: FCA permissions may require a specific minimum capital floor. If so, that amount is
  separately ring-fenced and NOT part of operating-cash deployment. Finance/compliance to confirm the floor and adjust
  reserve policy if it exceeds £150k.
- **Co-investment balance sheet**: the CME $50k skin is the single current co-investment commitment. Any future
  co-invest mandate (proposal for 2027+) adds balance-sheet capital. Not modelled here.
- **Fundraise planning**: this plan assumes no external fundraise in 2026. If a raise is considered (for accelerated
  growth or a larger co-invest vehicle), it's a separate workstream outside this doc.

## Follow-ups

- Finance: confirm monthly profit-share mechanism (10% of revenue vs of net profit).
- Compliance: confirm FCA minimum capital floor.
- Commercial: confirm CME skin scaling (Option S1 flat vs S3 reduced ratio).
- Operations: track actual burn vs this model monthly; flag any line > 10% variance.

## Cross-references

- [revenue-projection-2026-monthly.md](revenue-projection-2026-monthly.md) — revenue side
- [im-profit-share-structures.md](im-profit-share-structures.md) — CME co-invest + skin mechanics
- [pricing-building-blocks.md](pricing-building-blocks.md) — unit pricing inputs
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — internal-cost-private discipline
