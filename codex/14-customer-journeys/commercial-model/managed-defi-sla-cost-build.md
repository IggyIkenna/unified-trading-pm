---
doc_type: codex-ssot
title: Managed DeFi-allocator SLA — reusable cost-build template
summary:
  Reusable codex-private cost-build template for any DeFi-allocator managed-SLA — the per-tenant cost atoms, the
  retainer landing formula (max of 0.85× sole-client cost and 1.2×1.4× steady-state marginal), IP-power
  performance-share tiering (A 10% → C 25%/10% tranche), and one-time expansion charges.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [admin, sales]
tags: [commercial-model, sla, defi, cost, pricing, profit-share]
related:
  [
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/elysium-account-trajectory-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
  ]
created: 2026-05-20
authoritative_for: [managed DeFi-allocator SLA reusable cost-build template]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/elysium-account-trajectory-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Managed DeFi-allocator SLA — reusable cost-build template

> **Created 2026-05-14** alongside [`elysium-managed-sla-2026-05-14.md`](elysium-managed-sla-2026-05-14.md). Captures
> the _generalisable_ cost-build pattern for any future DeFi-allocator managed-SLA engagement so we don't re-derive the
> numbers next time. Elysium is the inaugural worked example; future allocators (next-tier DeFi funds, family offices,
> single-strategy mandates) plug into this template.
>
> **Audience**: admin + sales pre-quote. Codex-private per [rule 08](../_ssot-rules/08-pricing-principles.md) §Internal
> cost column. Numbers here never appear in client-facing quotes.
>
> **Companion**: [`pricing-building-blocks.md`](pricing-building-blocks.md) DART 13-block anchors (which this template
> echoes — managed-SLA is a _commercial shape_ not a _DART block_, but the underlying cost atoms are the same).

---

## §1 — Pattern shape

A managed-SLA engagement bundles four atoms:

1. **Fixed monthly retainer** — covers steady-state cost-to-serve + small operational margin.
2. **Variable performance share** — 15–25% of client's gross performance fees from end-clients, depending on IP-power
   tier.
3. **Per-event one-time charges** — for capability expansions (new venue, new LST, new chain) costed at ~$2.5k each.
4. **Optional self-run carve-out** — one-time hand-over fee + reduced retainer or no retainer thereafter; performance
   share survives.

The retainer + performance share are **independent flows** (performance share doesn't offset retainer). Rationale:
retainer pays for _capability to operate_; performance share pays for _strategy IP value delivered downstream_.

---

## §2 — Cost atoms (monthly, per tenant, USD)

> Numbers below are the **sole-client allocation** floor + the **steady-state (3+ tenants)** marginal cost. Real cost
> for a given engagement sits between these two as the tenant count ramps. **Apply 20% buffer to the steady-state
> marginal number, then add a small over-pricing margin to land the public retainer figure** (see §4).

| Atom                                                                     | Sole-client | Steady-state marginal | Driver                                                     |
| ------------------------------------------------------------------------ | ----------- | --------------------- | ---------------------------------------------------------- |
| Cloud compute (Elysium-equivalent tenant)                                | $150        | $120                  | Mix of always-on services + intermittent backfill VMs      |
| Cloud storage (~150 GB hot + 1 TB warm)                                  | $30         | $25                   | Tick + features + execution-store partition for the tenant |
| Cloud network (egress, DNS, LB)                                          | $30         | $25                   | Per-tenant API + dashboard egress                          |
| Cloud KMS / Secret Manager / IAM                                         | $20         | $15                   | Per-tenant CMK + secret rotations                          |
| Cloudflare / WAF / DDoS (shared)                                         | $20         | $10                   | Per-tenant slice of shared edge                            |
| Pen-test + vuln-scan amortized                                           | $80         | $30                   | $5k/y annual scan ÷ tenants ÷ 12                           |
| Backup + DR archival                                                     | $40         | $25                   | Per-tenant per-day archival cost                           |
| AI Anomaly Triage layer (Claude Code)                                    | $400        | $100                  | $400/mo Claude Code cap; 1/4 allocation at 4 tenants       |
| L1 monitoring operator (US 24/7, $1k/mo total)                           | $500        | $200                  | $1k/mo absolute cost; allocation drops as clients grow     |
| L2/L3 engineering oversight (10h sole-client → 5h steady-state @ $150/h) | $1,500      | $750                  | Alert-driven; matures down                                 |
| Monthly reporting + admin (4–6h)                                         | $300        | $200                  | Investor-facing report prep                                |
| Strategy slot maintenance ($150 × N archetypes)                          | $150 × N    | $125 × N              | Per archetype in scope                                     |
| Execution layer monitoring (custody + venue adapters)                    | $200        | $150                  | Per tenant                                                 |
| **Sub-total (Elysium-equivalent: 2 archetypes)**                         | **$3,570**  | **$1,800**            |                                                            |

**Important branding rule**: when these atoms appear in client-facing pricing decomposition (rare — usually only on
request), they're named **operationally**, never by underlying provider. Use these labels:

| Internal name             | Client-facing label                   |
| ------------------------- | ------------------------------------- |
| Claude Code               | AI Anomaly Triage & Code-Repair Layer |
| GCP/AWS compute + storage | Managed Cloud Infrastructure          |
| Pen-test contractor       | Security Assurance Layer              |
| Engineering oversight     | Senior Engineering Standby            |
| L1 operator               | 24/7 Monitoring Operator              |

---

## §3 — Retainer landing formula

```
retainer = max(
    sole_client_real_cost × 0.85,       # absorb up to 15% inaugural-client subsidy
    steady_state_marginal × 1.20 × 1.4  # 20% buffer + 40% gross margin
)
```

For Elysium (2 archetypes, 5 venue-LST slots): `max($3,570 × 0.85, $1,800 × 1.2 × 1.4) = max($3,035, $3,024) ≈ $3,000`.
Lands cleanly at $3k.

For a hypothetical 1-archetype tenant (single CARRY_STAKED_BASIS slot on Drift+JitoSOL only):

- Sole-client real cost: $3,420 (subtract one $150 archetype slot)
- Steady-state marginal: $1,675
- Retainer: `max($2,907, $2,814) ≈ $2,900` — round to $2,500/mo with a slightly higher performance share to compensate.

For a hypothetical 4-archetype tenant (full Carry & Yield family):

- Sole-client real cost: $3,870
- Steady-state marginal: $2,050
- Retainer: `max($3,290, $3,444) ≈ $3,400` — round to $3,500/mo.

---

## §4 — Performance share — IP-power tiering

| Tier  | IP-power                                                                                                                                     | Performance share                                                                               | Rationale                                                                                                                                                                                                                  |
| ----- | -------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A     | Generic capacity-rental (any well-known basis trade run on commodity infra)                                                                  | 10% flat                                                                                        | Low IP differentiation; retainer carries the value                                                                                                                                                                         |
| B     | Differentiated implementation (e.g. specific venue+LST combination, custom risk overlay)                                                     | 15% flat                                                                                        | Some IP value beyond commodity capacity                                                                                                                                                                                    |
| **C** | **Single-source strategy delivered to client (no alternative provider exists; client took non-compete on the in-scope deliverable to lock)** | **Tranche-tiered: 25% on the first $100M of Strategy-attributable AUM; 10% on AUM above $100M** | **Maximum IP-power — Elysium tier.** Tiering reflects that at large AUM, the value-add of operating the Strategy becomes proportionally smaller (infra scales sublinearly), so flat 25% becomes commercially indefensible. |
| D     | Strategy + capital deployment (we manage capital too, not just infra)                                                                        | 20% performance fee on client AUM                                                               | This is IM-style — different commercial shape — see [`im-profit-share-structures.md`](im-profit-share-structures.md)                                                                                                       |

Elysium sits in **Tier C** because (a) the strategy is the specific delivered Work Product, (b) Art. 6.2 non-compete
locks us out of competing on the _exact In-Scope Strategy/venue/LST combinations_ (and only those — see SLA Exhibit B),
and (c) no alternative provider has the same implementation. The 25%-then-10% tranche-tier captures the IP value at
modest AUM while keeping the deal defensible if Elysium grows materially.

---

## §5 — One-time charges (capability expansion)

| Expansion type                                                   | Hours    | Charge                      |
| ---------------------------------------------------------------- | -------- | --------------------------- |
| New perp venue (existing chain, existing LST)                    | 50–100   | $2,500                      |
| New LST / staking protocol (existing chain, existing perp venue) | 50–100   | $2,500                      |
| Bundled new venue + new LST (when commissioned together)         | 75–150   | $3,500                      |
| New chain (e.g. Solana to a previously ETH-only tenant)          | 100–200  | $5,000                      |
| New strategy archetype (within Carry & Yield family)             | 200–400  | $15,000                     |
| New strategy family entirely (e.g. Arbitrage, Market-Making)     | varies   | Separate SOW; floor $25,000 |
| Custom risk overlay / kill-switch tuning                         | 20–60    | $1,500                      |
| End-client share class onboarding (within 10h/mo allowance)      | 0–10     | $0                          |
| End-client share class onboarding (beyond 10h/mo)                | per hour | $200/hr preferred rate      |

**Why $2,500 for a new venue?** Build-up:

- Venue-collateral matrix research + live-API verification: 8h
- Backtesting against historical funding + price data: 12h
- Adapter integration (CeFi or DeFi side): 20–30h
- Data subscription / API auth setup: 4h
- Risk-engine calibration (haircut, kill-switch thresholds): 8h
- Operational runbook update: 4h
- Live cutover + smoke + 1 week elevated monitoring: 10h
- Total: 66–76 hours × $150/hr = $9,900–$11,400 internal cost. **Charge $2,500.** We absorb the difference as platform
  investment (the new venue helps all tenants, not just the requesting one).

For _strategy-family scale_ (Arbitrage / MM / ML / Vol etc.), there's no "discount" — these are full-fat SOWs because
they require entirely new infrastructure paths.

---

## §6 — Cost-growth drivers that justify retainer re-negotiation

| Driver                                                                 | Re-negotiation threshold                                 |
| ---------------------------------------------------------------------- | -------------------------------------------------------- |
| Capital scaling — AUM > $50M for managed Strategy                      | Tier up retainer by 25–50%                               |
| Capital scaling — AUM > $100M                                          | Dedicated infrastructure tier; bespoke pricing           |
| End-client count > 10 active share classes                             | Tier up retainer by 25%                                  |
| Response-target tier upgrade (e.g. 1h → 15-min Critical)               | Tier up retainer by 50–100%                              |
| Geographic expansion (new fund domicile / new regulatory jurisdiction) | New SOW + retainer adjustment                            |
| Custody provider material change (e.g. Copper migrates to v2 MPC)      | Billed at $200/hr for re-integration; retainer unchanged |
| Venue API breaking change                                              | First 4 hr/quarter included; beyond billed at $200/hr    |

**NOT a re-negotiation trigger**: new strategies, new venues, new LSTs, new chains, new end-client share classes within
10h/mo allowance. These all map to one-time charges (§5) and don't perturb the retainer.

---

## §7 — Open commercial questions (for future template iterations)

- **Inflation indexation** — should retainers carry an annual indexation clause (e.g. UK CPI + 1%)? Not in Elysium SLA
  yet. Decide before next managed-SLA quote.
- **Term length** — Elysium SLA defaults to month-to-month after the 30-day complimentary period. DART Tier-B carries
  12-month minimums per rule 08. Should managed-SLA carry a 6-month or 12-month minimum to amortize onboarding
  investment? Likely yes; revisit.
- **Capacity caps** — at what total tenant count does the L1 operator + AI triage capacity saturate? Currently sized for
  ~5 tenants. Beyond that need a second operator or new tier. Plan a capacity-review cadence.
- **Refund / pro-ration on early termination** — Elysium SLA doesn't carry refund mechanics. Acceptable for inaugural;
  standardise before scaling.

---

## §8 — Cross-references

- Worked example: [`elysium-managed-sla-2026-05-14.md`](elysium-managed-sla-2026-05-14.md).
- DART 13-block anchors: [`pricing-building-blocks.md`](pricing-building-blocks.md).
- IM performance-fee mechanics (different shape; not managed-SLA):
  [`im-profit-share-structures.md`](im-profit-share-structures.md).
- Pricing rule SSOT: [`../_ssot-rules/08-pricing-principles.md`](../_ssot-rules/08-pricing-principles.md).
- Strategy archetype catalogue (which strategies fit which SLA tier):
  [`../../09-strategy/architecture-v2/archetypes/`](../../09-strategy/architecture-v2/archetypes/).
