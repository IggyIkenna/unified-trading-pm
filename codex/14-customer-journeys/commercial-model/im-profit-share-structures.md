---
doc_type: codex-ssot
title: IM Profit-Share Structures
summary:
  All Investment-Management commercial mechanics — no management fee, 30-35% performance-share band with platform-fee
  client-choice (Option A +5% perf / Option B $500/mo), CME asymmetric 70/10 co-invest with $50k skin, India Options
  $100k onboarding, mean-rev migration path, and the BTC FoF external wrapper.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [admin, sales]
tags: [commercial-model, im, profit-share, pricing, cme, india-options]
related:
  [
    /codex/14-customer-journeys/commercial-model/im-vs-reg-reporting-logic.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/signal-leasing.md,
    /codex/14-customer-journeys/commercial-model/cash-deployment-plan.md,
  ]
created: 2026-04-20
authoritative_for:
  [IM profit-share commercial structures (perf-share / platform-fee-choice / CME co-invest / India Options)]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/cash-deployment-plan.md,
    /codex/14-customer-journeys/commercial-model/dart-entry-points.md,
    /codex/14-customer-journeys/commercial-model/elysium-account-trajectory-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/exclusivity-and-noncompete.md,
    /codex/14-customer-journeys/commercial-model/im-vs-reg-reporting-logic.md,
    /codex/14-customer-journeys/commercial-model/managed-defi-sla-cost-build.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
  ]
owner:
last_reviewed:
code_refs:
---

# IM Profit-Share Structures

> All Investment Management commercial mechanics: standard performance-share, platform-fee client-choice, CME asymmetric
> co-invest, India Options high-share-no-management, existing mean-rev migration path, BTC FoF external wrapper.

**Rule sources:** [rule 04](../_ssot-rules/04-dart-commercial-axes.md) — `(Odum, *)` cells resolve here;
[rule 08](../_ssot-rules/08-pricing-principles.md) — no management fee on Odum IM; Tier-B-only modifiers.

## Design principles

1. **No management fee.** Odum IM does not take a management fee on allocated capital. Performance-share only. This
   preserves alignment and avoids the "zero performance, still get paid" flaw of traditional 2-and-20.
2. **Client-choice platform fee.** Each IM mandate chooses at signing between a higher performance-share percentage OR a
   small fixed monthly fee. Preserves alignment optionality.
3. **Asymmetric structures allowed on co-invest mandates.** Where Odum co-invests capital alongside the client and
   brings the strategy IP, loss share can be asymmetric to profit share (e.g. 70% of profits, 10% of losses).
4. **External wrappers are distinct.** Mandates where Odum allocates to an external fund (no Odum-system compute) are
   wrappers, not catalogued strategies. Different revenue mechanic.

## Standard IM mandate — performance share

### The 30-35% band

Base performance share is **30-35%** of client net profits. Within the band:

- **30%**: liquid, commoditised strategies (BTC ML directional on perps). Tight margin because many competitors could
  offer similar.
- **35%**: specialised / harder-to-replicate strategies (sports ML where capacity is bound, India Options delta trading
  where venue access is hard).

Rationale for higher than a standard fund-of-funds perf fee (~20%): Odum brings strategy IP + operates the venue
integration + absorbs the operational overhead. The client only contributes capital.

### Platform-fee client choice at mandate signing

At mandate signing, client picks one:

- **Option A**: +5% performance fee uplift (base 30% → 35%, or base 35% → 40%). Zero fixed monthly. Pure alignment.
  Attractive for clients who want skin-aligned pricing.
- **Option B**: Base performance fee + **$500 monthly flat platform access**. Attractive for clients who prefer a small
  fixed floor over higher variable share.

Either option gives Odum a partial revenue floor: Option A = more upside when the strategy performs; Option B = a small
guarantee that runs regardless of strategy year. The choice is the client's preference.

### Worked example — BTC ML directional, 10 clients × $500k

Base 30% performance share. Assume client 1-5 pick Option A (35% perf, no flat), clients 6-10 pick Option B (30% perf +
$500/mo).

At 12% annualised net return on $500k per client:

|                     | Option A clients (5)     | Option B clients (5)    | Total                               |
| ------------------- | ------------------------ | ----------------------- | ----------------------------------- |
| Gross client profit | $60k × 5 = $300k/yr      | $60k × 5 = $300k/yr     | $600k/yr                            |
| Odum perf share     | 35% × $300k = $105k/yr   | 30% × $300k = $90k/yr   | $195k/yr                            |
| Platform-fee floor  | 0                        | $500 × 12 × 5 = $30k/yr | $30k/yr                             |
| **Total Odum**      | **$105k/yr = $8.75k/mo** | **$120k/yr = $10k/mo**  | **$225k/yr = $18.75k/mo ≈ £15k/mo** |

Good year (20%): ~£25k/mo. Flat year (5%): ~£4k/mo + £2k/mo Option B floor = £6k/mo minimum.

## CME co-investment structure (asymmetric)

**Unique mechanic**: Odum co-invests $50k skin-in-the-game alongside the client's $500k allocation. Working pool =
$550k
(ramping to $5.05M over year-1). Odum brings the S&P ML signal + CME trade execution.

### Profit / loss split

- **Profits**: Odum takes **70%**, client takes 30%.
- **Losses**: Odum bears **10%**, client bears 90%.

### Rationale for asymmetry

Odum's $50k skin signals commitment but is small relative to the $500k-$5M pool. The 70/10 asymmetry reflects that Odum
brings the strategy IP (the material alpha) while the client brings most of the capital. Client's risk-adjusted return
is effectively a leveraged version of the strategy; Odum's is a very high-torque position on its own capital.

### Scaling the skin-in-the-game

**TBD — to be confirmed with client at contracting:**

- **Option S1 (flat)**: Odum skin stays at $50k regardless of client allocation ramp. At $5M full allocation, Odum's
  skin is 1% of the pool. Minimal capital commitment.
- **Option S2 (pro-rata 10%)**: Odum scales skin to 10% of client allocation. At $5M client, Odum puts in $500k.
  Significant balance-sheet ask.
- **Option S3 (reduced ratio)**: Odum scales skin to a lower ratio (e.g. 2%). At $5M client, Odum puts in $100k. Middle
  ground.

**Recommendation**: Option S1 (flat $50k) as initial contracting stance, with an optional uplift to S3 at year-2 renewal
if the engagement performs and client wants deeper alignment. Pure S2 is excessive balance-sheet risk for the strategy
size.

### Year-1 expected economics

Averaging $500k → $5M over 12 months gives average working capital ~$2.8M. At 20% expected annualised return:

| Scenario  | Gross pool profit | Odum 70% profit share | Odum loss exposure (if opposite)                                                        |
| --------- | ----------------- | --------------------- | --------------------------------------------------------------------------------------- |
| +20% year | $560k             | **$392k ≈ £310k**     | —                                                                                       |
| +10% year | $280k             | **$196k ≈ £155k**     | —                                                                                       |
| Flat (0%) | $0                | 0                     | 0                                                                                       |
| -10% year | -$280k            | —                     | 10% × $280k = $28k Odum loss                                                            |
| -20% year | -$560k            | —                     | $56k (> skin; Odum loss capped by skin commitment but contractually still 10% of total) |

**Year-1 monthly average** at 20% return: £310k ÷ 12 = **~£26k/mo**. **Year-2 steady-state** at $5.05M × 20% × 70%:
**~£47k/mo**.

### If the client rejects the 70/10 asymmetric in negotiation

Fallback structure: **10% of both sides** (flat pari-passu). Client bears 90% of both; Odum bears 10% of both. Odum
share drops from 70% → 10%. Much less attractive; document in contracting notes as a last-resort posture.

## India Options (new-venue IM engagement)

**Structure**: `(Odum, full-pipeline)` per rule 04 — Odum trades the strategy (delta trading for convex payouts on NSE
options).

- **Upfront**: **$100k** onboarding fee. Covers new-venue integration (NSE options adapter + clearing + margin) +
  options-specific infrastructure. Paid over 3 months at contracting.
- **Ongoing**: Standard 30-35% performance-share + platform-fee client choice. Same framework as BTC ML.
- **Allocation**: $5-10M expected year-1 (they reckon $5-10M after the S&P ML signal proves out).
- **Gating**: S&P ML signal must ship first (demonstrates Odum can predict Indian futures / NSE options movements).
  Without S&P signal, India Options engagement doesn't unlock.

### Why $100k upfront plus standard perf-share (not higher)

The $100k already covers the new-venue cost premium (NSE options integration effort, clearing + margin mechanics, delta
trading infrastructure). Once live, the ongoing economics look like any other IM engagement — 30-35% of profits. India
doesn't warrant a higher perf-share band because the strategy is still delta trading (known mathematical structure), not
a novel alpha.

### Worked example — $7.5M mid-case allocation at 20% return

- Gross client profit: $1.5M/yr
- 30-35% perf-share: $450-525k/yr = £28-32k/mo + $500/mo platform-fee floor if client picks Option B
- **Year-1 annualised run-rate**: ~£32-35k/mo recurring post-onboarding, plus amortised upfront

## Existing mean-reversion IM strategy — migration path

**Current state** (2-year running):

- Clients allocate via external-to-system structure (not via our full IM stack)
- $5k/month gross revenue to Odum
- Costs baked in to advisor + introducer payouts

**Migration path to BTC ML + in-system IM**:

1. Existing mean-rev clients retain their existing mandate structure (grandfathered).
2. New mandate (BTC ML directional) signed separately under the new perf-share + platform-fee-choice model.
3. Same client runs both mandates in parallel — mean-rev continues, BTC ML is additive capital.
4. No migration discount. The two mandates are separate commercial engagements.
5. If a client wants to wind down mean-rev in favour of BTC ML, standard mandate termination applies.

**Commercial upside**: existing mean-rev clients are pre-qualified — they've run for 2 years, trust Odum's ops, are
unlikely to balk at adding a second mandate. **Expected**: 3-5 of the existing mean-rev clients will add BTC ML
directional in H2 2026.

## BTC Fund of Funds wrapper (external, non-catalogued)

**Structure**: Client allocates to Odum; Odum wraps by allocating to an external BTC fund-of-funds vehicle that Odum
does not operate. Odum keeps 20% of the client's profits.

- **Client capital**: 50 BTC (~$3.5M at $70k BTC)
- **FoF annualised**: ~5% net
- **Odum share**: 20% × 5% × 50 BTC = 0.5 BTC/yr (~$35k/yr = £2.3k/mo)

**Distinguishing features**:

- NOT an Odum-system strategy. Client's capital goes to an external fund.
- Appears ONLY in client-reporting for the specific mandate. Not in the strategy catalogue.
- No system compute cost. Near-pure-margin revenue.
- Rule 07 data-licensing not applicable (no Odum strategy IP involved).

**Commercial continuity**: existing; no changes planned. Treated as a legacy mandate that continues until client
terminates.

## Signal leasing (related but separate)

Signal leasing to institutional counterparties is a separate commercial mechanic. See
[`signal-leasing.md`](signal-leasing.md) for that structure. Distinguishing line: signal leasing sells Odum's strategy
_output_ (signals) to another manager who executes themselves; IM sells Odum's _execution_ + _strategy operating_ bundle
to a capital allocator.

## Commercial quote template — IM engagement

Every IM quote includes:

1. **Strategy scope**: named archetype × instrument × venue(s) cells, maturity ≥ BACKTESTED required (for novel
   strategies, wait until LIVE_TINY before signing).
2. **Allocation floor + ramp cadence**: initial allocation + review cadence (quarterly typical).
3. **Performance-fee band**: 30-35% range, specific percentage.
4. **Platform-fee choice**: Option A (+5% perf) or Option B ($500/mo) — client picks.
5. **Co-investment terms** (if applicable): asymmetric profit/loss split, skin-in-the-game amount + scaling rule.
6. **Onboarding fee** (if applicable): new-venue or bespoke-feature premium.
7. **Reporting cadence**: monthly + quarterly allocator pack.
8. **Termination terms**: twelve-month minimum per rule 08, notice period, perf-fee crystallisation on termination.
9. **Regulatory structure**: SMA (separate managed account) or Pooled fund slot — per
   [`../shared-core/org-fund-client-entity-model.md`](../shared-core/org-fund-client-entity-model.md).

## Cross-references

- [rule 04 — DART commercial axes](../_ssot-rules/04-dart-commercial-axes.md) — `(Odum, *)` cells map to IM
- [rule 08 — pricing principles](../_ssot-rules/08-pricing-principles.md) — tier framework
- [pricing-building-blocks.md](pricing-building-blocks.md) — 13-row structure with IM-specific notes
- [im-vs-reg-reporting-logic.md](im-vs-reg-reporting-logic.md) — IM vs Reg Umbrella commercial framings
- [signal-leasing.md](signal-leasing.md) — sibling mechanic
- [../shared-core/strategy-origin-vs-stack-depth.md](../shared-core/strategy-origin-vs-stack-depth.md) — worked examples
  for each IM engagement shape
- [../shared-core/strategy-allocation-lock-matrix.md](../shared-core/strategy-allocation-lock-matrix.md) — which cells
  are IM_RESERVED
- [../experience/im-decision-journey.md](../experience/im-decision-journey.md) — pb2a narrative
- [../experience/investment-management-demo.md](../experience/investment-management-demo.md) — pb3b demo
