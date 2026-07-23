---
doc_type: codex-ssot
title: Revenue Projection 2026 — Monthly Build
summary:
  Codex-private month-by-month 2026 revenue build (~£636k total) across baseline, Elysium, BTC ML, sports ML, CME, India
  Options, Desmond, and signal leasing — with the ~£34k/mo cost decomposition, full P&L (+£92k net), and cumulative cash
  from £240k opening to £413k year-end above the £150k floor.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [admin]
tags: [commercial-model, revenue, cash-flow, finance, cost, forecast]
related:
  [
    /codex/14-customer-journeys/commercial-model/cash-deployment-plan.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
    /codex/14-customer-journeys/commercial-model/signal-leasing.md,
  ]
created: 2026-04-20
authoritative_for: [2026 monthly revenue projection and cashflow model]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/cash-deployment-plan.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/signal-leasing.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Revenue Projection 2026 — Monthly Build

> **CODEX-PRIVATE / INTERNAL** per rule 08. Contains pricing sensitivity and finance detail. Do NOT surface on
> client-facing docs, demo environments, or website copy.

**Rule sources:** [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) §internal cost codex-private;
[rule 09 — internal commercial one-liners](../_ssot-rules/09-internal-commercial-oneliners.md) §internal framing

**Cross-refs:** [pricing-building-blocks.md](pricing-building-blocks.md),
[im-profit-share-structures.md](im-profit-share-structures.md), [cash-deployment-plan.md](cash-deployment-plan.md),
[signal-leasing.md](signal-leasing.md).

## Starting position (April 2026)

- **Cash in bank**: $305k (~£240k at 0.79 GBP/USD).
- **Recurring revenue baseline**: £8k/month from existing engagements (Seed Reg Umbrella $2k/mo, mean-rev IM $5k/mo, BTC
  FoF wrapper £2.3k/mo).
- **Deals in pipeline**: Elysium (remaining $35k + $75-100k upsell through Dec), Desmond (£25-50k upfront + £22k/mo from
  May), CME (Sept go-live), India Options
  ($100k onboarding Oct), signal leasing (2 counterparties Q3-Q4), BTC ML (10 ×
  $500k from June), sports ML (2 clients
  June).

## Monthly revenue stream decomposition

### Recurring baseline (£8k/mo, live throughout 2026)

| Stream                                                                 | $/mo      | £/mo |
| ---------------------------------------------------------------------- | --------- | ---- |
| Seed Reg Umbrella                                                      | $2k       | 1.6  |
| Mean-rev IM (external-to-system, costs to advisor/introducer baked in) | $5k gross | 4.0  |
| BTC FoF wrapper (0.5 BTC/yr ≈ £28k at $70k BTC)                        | $2.9k     | 2.3  |

### Elysium (Phase A + upsells)

**Phase A — staked-basis strategy, $500k own allocation, 10% annualised, 30% Odum share:**

- From June onwards: $500k × 10% × 30% / 12 = $1.25k/mo = **£1k/mo**

**Phase B — their client allocates $5-10M, Elysium charges ~20% fees, Odum share 30% of those fees:**

- Timing: Phase B realistically late-Q3 / Q4 after Phase A proves out.
- Economics: $7.5M × 20% returns × 20% Elysium fee × 30% Odum = $90k/yr = **£6k/mo**.
- Modelled landing October.

**Upfront tranches** ($125k conservative + upsell path to $200-230k total, delivered as):

- $35k remaining go-live payment — **June** (completes $125k conservative)
- $25k MEV upsell — **July**
- $25k Solana chain + setup upsell — **September**
- $25k recursive-staking variant upsell — **November**
- $10-20k dynamic-weighting upsell — **December**

Total 2026 Elysium upfront: ~£108k (varies with upsell realization).

### BTC ML directional (IM — 10 × $500k ramp)

- Client ramp: 2 clients June, +2 July, +2 Aug, +2 Sept, +2 Oct = 10 by October.
- Per-client economics at 12% net annualised: $500k × 12% × 30% / 12 = $1.5k/mo = £1.2k/mo per client.
- Platform-fee choice split: half take Option B ($500/mo flat); Option A clients at 35% perf give slight uplift.

Monthly BTC ML revenue through 2026:

| Jun | Jul | Aug | Sep  | Oct | Nov | Dec |
| --- | --- | --- | ---- | --- | --- | --- |
| 2.8 | 5.6 | 8.4 | 11.2 | 14  | 14  | 14  |

### Sports ML directional (IM — 2 clients, capacity-bound)

- Clients live June onwards, 2 × $75k avg AUM.
- Economics: $150k × 12% × 30% / 12 = $450/mo = ~£360/mo. Rounded to £0.4k/mo throughout.

### CME S&P (co-invest, asymmetric 70%/10%)

- Sept go-live. $500k client + $50k Odum skin-in-the-game = $550k working capital, ramping to $5.05M.
- 70% profit share on pool returns at ~1%/mo (12% annualised).
- Monthly ramp:

| Sep | Oct | Nov | Dec |
| --- | --- | --- | --- |
| 3   | 5.8 | 8.3 | 11  |

### India Options ($100k onboarding + 2027 allocation)

- Onboarding payment: $100k lump October (when S&P ML signal proven + contract signs).
- Allocation: $5-10M Q1 2027 onwards. 2026 revenue = **£79k one-time October** only.

### Desmond (Reg Umbrella + DART signals-only)

- Start: **May** (earliest per user).
- Upfront: £35k (mid of £25-50k range).
- Monthly: £22k/mo (Reg Umbrella £12k + DART signals-only £10k).

| May                          | Jun-Dec each |
| ---------------------------- | ------------ |
| 35 upfront + 22 monthly = 57 | 22           |

### Signal leasing (2 counterparties, narrow prove-out scope — revised 2026-04-20)

**Revised anchor**: 2 counterparties combined targeting **~$5k/mo (≈£4k/mo) from September 2026**. Both live
simultaneously; narrow initial scope per counterparty. Expansion-driven growth modelled in 2027.

Backend enablement dependency: external-broadcast refactor per
[`../../../plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md`](../../../plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md).

| Sep | Oct | Nov | Dec |
| --- | --- | --- | --- |
| 4   | 4   | 4   | 4   |

## Full monthly revenue table

Sums (£k):

| Month          | Baseline | Elysium upfront | Elysium ongoing | BTC ML | Sports | CME    | India  | Desmond | Signal lease | **Total**  |
| -------------- | -------- | --------------- | --------------- | ------ | ------ | ------ | ------ | ------- | ------------ | ---------- |
| Jan            | 8        | 0               | 0               | 0      | 0      | 0      | 0      | 0       | 0            | **8**      |
| Feb            | 8        | 0               | 0               | 0      | 0      | 0      | 0      | 0       | 0            | **8**      |
| Mar            | 8        | 0               | 0               | 0      | 0      | 0      | 0      | 0       | 0            | **8**      |
| Apr            | 8        | 0               | 0               | 0      | 0      | 0      | 0      | 0       | 0            | **8**      |
| May            | 8        | 0               | 0               | 0      | 0      | 0      | 0      | 57      | 0            | **65**     |
| Jun            | 8        | 28              | 1               | 2.8    | 0.4    | 0      | 0      | 22      | 0            | **62**     |
| Jul            | 8        | 20              | 1               | 5.6    | 0.4    | 0      | 0      | 22      | 0            | **57**     |
| Aug            | 8        | 0               | 1               | 8.4    | 0.4    | 0      | 0      | 22      | 0            | **40**     |
| Sep            | 8        | 25              | 1               | 11.2   | 0.4    | 3      | 0      | 22      | 4            | **75**     |
| Oct            | 8        | 0               | 7               | 14     | 0.4    | 5.8    | 79     | 22      | 4            | **140**    |
| Nov            | 8        | 25              | 7               | 14     | 0.4    | 8.3    | 0      | 22      | 4            | **89**     |
| Dec            | 8        | 10              | 7               | 14     | 0.4    | 11     | 0      | 22      | 4            | **76**     |
| **2026 total** | **96**   | **108**         | **25**          | **84** | **3**  | **28** | **79** | **233** | **16**       | **~£636k** |

**Revision note (2026-04-20)**: Signal leasing revised from £12-24k/mo ramp (previous modelling) to £4k/mo flat Sept-Dec
(~$5k combined from 2 narrow-scope counterparties live simultaneously Sept 2026 per
`../../../plans/archive/signal_leasing_broadcast_architecture_2026_04_20.plan.md`). Annual revenue impact: **-£56k**
(from £692k to ~£636k). Net-of-cost impact with cascaded 10%-of-revenue profit-share: year-end cash moves from ~£464k to
**~£413k** — still well above £150k reserve floor; no funding implication. P&L + cumulative-cash tables below are
post-revision.

## Monthly cost decomposition (£k/month)

| Line                                          | Jan-Dec steady-state | Notes                            |
| --------------------------------------------- | -------------------- | -------------------------------- |
| Tardis (academic licence, £8k/yr)             | 0.67                 | Annual-to-monthly                |
| DeFi data (Graph + Alchemy)                   | 1.0                  |                                  |
| Sports data (API-Football + weather)          | 1.0                  |                                  |
| TradFi data                                   | 2.0                  |                                  |
| GCP cloud compute + storage                   | 5.0                  | Midpoint; scales sub-linearly    |
| Engineering team ($20k USD → £16k, 2.5 FTE)   | 16.0                 | Base salary, no profit share yet |
| AI agentic costs (Claude, Cursor, validators) | 2.0                  |                                  |
| FCA fees (£10k/yr)                            | 0.83                 |                                  |
| Audit fees (£20k/yr)                          | 1.67                 |                                  |
| Westbay registrar (£4k/yr)                    | 0.33                 |                                  |
| Banking (£600/yr)                             | 0.05                 |                                  |
| AML monitoring (no broader legal team)        | 1.0                  |                                  |
| SaaS (email/Slack/Docusign/Notion/etc)        | 2.0                  |                                  |
| **Base burn**                                 | **~£34k/month**      |                                  |

**Extras:**

- Apr: +£15k (startup proof-readiness backtest compute)
- May: +£15k (paper-testing compute)
- Sep: +£40k one-time (CME skin-in-the-game)
- Profit-share on engineering (revenue-based, ~10% of revenue): variable

## Full monthly P&L

| Month    | Revenue    | Base burn | Extras | Profit-share (10% of rev) | Total cost | **Net**       |
| -------- | ---------- | --------- | ------ | ------------------------- | ---------- | ------------- |
| Jan      | 8          | 34        | 0      | 1                         | 35         | **-27**       |
| Feb      | 8          | 34        | 0      | 1                         | 35         | **-27**       |
| Mar      | 8          | 34        | 0      | 1                         | 35         | **-27**       |
| Apr      | 8          | 34        | 15     | 1                         | 50         | **-42**       |
| May      | 65         | 34        | 15     | 7                         | 56         | **+9**        |
| Jun      | 62         | 34        | 0      | 6                         | 40         | **+22**       |
| Jul      | 57         | 34        | 0      | 6                         | 40         | **+17**       |
| Aug      | 40         | 34        | 0      | 4                         | 38         | **+2**        |
| Sep      | 75         | 34        | 40     | 8                         | 82         | **-7**        |
| Oct      | 140        | 34        | 0      | 14                        | 48         | **+92**       |
| Nov      | 89         | 34        | 0      | 9                         | 43         | **+46**       |
| Dec      | 76         | 34        | 0      | 8                         | 42         | **+34**       |
| **2026** | **~£636k** | £408k     | £70k   | ~£66k                     | £544k      | **+£92k net** |

## Cumulative cash — starting April at £240k

| Month             | Net | Cumulative cash |
| ----------------- | --- | --------------- |
| Apr (opens £240k) | -42 | **£198k**       |
| May               | +9  | £207k           |
| Jun               | +22 | £229k           |
| Jul               | +17 | £246k           |
| Aug               | +2  | £248k           |
| Sep               | -7  | £241k           |
| Oct               | +92 | £333k           |
| Nov               | +46 | £379k           |
| Dec               | +34 | **£413k**       |

**Cash never goes negative. Peak minimum £198k (April).** Year-end £413k (~$523k). Above £150k reserve floor throughout.

## Sensitivity scenarios

### Base case (modelled above)

- BTC ML @ 12% annualised
- Elysium Phase B lands October with $7.5M allocation
- Desmond contracts May
- India Options lands October
- Signal leasing 2 counterparties live Sept 2026 at ~$5k/mo combined (£4k/mo)
- Year-end cash: **£413k**

### Upside case

- BTC ML @ 20% annualised → +£15-20k/mo H2 uplift
- Elysium Phase B $10M and lands August → +£6-12k
- Elysium total upsell reaches $200k+ → +£15k
- Signal leasing 3rd counterparty by end-year → +£4-8k
- Year-end cash: **£520-570k**

### Downside case

- BTC ML @ 6% annualised → -£15k/mo H2
- Elysium Phase B slips to 2027 → -£18k (Oct-Dec loss)
- Desmond slips to July → -£44k (May-Jun)
- India Options slips to Nov → still lands but 1-mo delay, -£10-15k
- Signal leasing lands 1 counterparty only → -£20k
- Year-end cash: **£320-370k** (still positive, still healthy)

### Stress case (multiple slips)

- BTC ML @ 5% + Elysium Phase B 2027 + India Options Dec + Signal leasing 1 counterparty + Desmond July
- Year-end cash: **~£260-300k** — nearly flat vs opening. Absorbs the year but no growth funding for 2027.

## Strategic implications

1. **Self-funding through 2026** — even in downside scenarios, cash stays positive and ends year ≥ opening. No bridge
   capital required.
2. **India Options is the biggest single-month cash event** (October £92k net). Preserve by protecting S&P ML signal
   delivery.
3. **Elysium upsells materially shape Q3-Q4 revenue** — pulling MEV / Solana / recursive-staking upsells earlier
   improves mid-year cashflow.
4. **Engineering headcount scaling to 3.5 in 2027** adds ~£7k/mo burn; easily absorbed given 2027 revenue growth.
5. **Most vulnerable point: May through August** — revenue ramping but BTC ML perf not yet realising. Engineering
   - CME skin concentrated here. Keep discretionary cost under control.

## Follow-ups (finance-owned)

- ✅ `pricing-building-blocks.md` internal-cost column populated 2026-04-20 from the line-item data above, per-block.
  Re-trigger on ±15% base-burn moves.
- Finance to confirm profit-share mechanism for engineering (10% of revenue? Or of net profit?) — currently modelled as
  10% of revenue which may be aggressive.
- Commercial to confirm CME $50k skin-in-the-game funding source + scaling option (S1 flat vs S3 reduced).
- Commercial to confirm signal-leasing pricing model (Options 1/2/3/4 from signal-leasing.md).
