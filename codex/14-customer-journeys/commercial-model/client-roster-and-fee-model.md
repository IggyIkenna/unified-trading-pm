---
doc_type: codex-ssot
title: Managed-Account Client Roster & Fee/HWM Invoicing Model
summary:
  Committed SSOT for the live managed-account book — organisation/client hierarchy, per-client Odum/trader/introducer
  fee %s, tranches + pooled-account splits, the four-tier HWM fee model, the three HWM methods (TWR / Notional / PnL
  Recovery), per-client HWM nuances (seeds, GP pnl_based special case, IK pool), and the invoice lifecycle + committed
  invoice/refund history. The human commercial SSOT the "grep codex before asking the operator for committed numbers"
  rule points at; the LIVE machine config is execution-service/configs/credentials-registry.yaml.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [client-reporting-api, execution-service]
scope: [sales, admin]
tags: [commercial-model, client-reporting, fees, hwm, invoicing, roster, twr, pooled-account, introducer]
related:
  [
    /codex/04-architecture/client-reporting-architecture.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    /codex/14-customer-journeys/commercial-model/README.md,
    /codex/04-architecture/client-funds-isolation.md,
  ]
created: 2026-07-29
authoritative_for:
  [
    managed-account client roster + org hierarchy,
    per-client Odum/trader/introducer fee percentages,
    four-tier HWM fee model + three HWM methods,
    committed invoice + refund history,
  ]
referenced_by: [/codex/04-architecture/client-reporting-architecture.md]
owner:
last_reviewed: 2026-07-29
code_refs: [execution-service/configs/credentials-registry.yaml, client-reporting-api/client_reporting_api]
---

# Managed-Account Client Roster & Fee/HWM Invoicing Model

> **Committed commercial SSOT.** This is the human-readable single source of truth for Odum's managed-account book: the
> client roster, the per-client fee arrangements, and the HWM/invoicing model. It exists so that committed commercial
> numbers are grep-able in codex (per CLAUDE.md "grep codex before asking the operator for committed numbers") instead
> of living only in a repo `docs/` folder.
>
> **Machine SSOT for LIVE config:** `execution-service/configs/credentials-registry.yaml` holds the runtime per-client
> fee %s, tranche, venue, currency, pooled weights, and Secret-Manager key names. When the two disagree on a LIVE config
> value, the registry yaml is authoritative for what the pipeline actually runs; this codex doc is authoritative for the
> **commercial model** and the **committed historical facts** (roster snapshot, invoice/refund history, HWM seeds).
> Numbers below are the operator-confirmed snapshot as of the `last_reviewed` date (roster + fee %s confirmed current by
> the operator 2026-07-28).
>
> **The reporting PIPELINE** (how NAV/PnL/attribution parquet is produced and served) is a separate concern — see
> [`/codex/04-architecture/client-reporting-architecture.md`](/codex/04-architecture/client-reporting-architecture.md).
> **Funds never move between clients** — every transfer is scoped to one `client_id`
> ([`/codex/04-architecture/client-funds-isolation.md`](/codex/04-architecture/client-funds-isolation.md)).

## 1. Organisation & client hierarchy

Every client belongs to an **organisation**. Organisations are either `internal` (Odum's own accounts) or `client`
(external managed accounts).

```
Organisation (org)
  └── Client (account)
        └── Strategy (what we trade on their behalf)
```

### Organisations

| Org ID       | Name          | Type     | Contact   |
| ------------ | ------------- | -------- | --------- |
| `odum`       | Odum Capital  | internal | —         |
| `prism`      | Prism Capital | client   | Max       |
| `namnar`     | Namnar        | client   | —         |
| `eqvilent`   | Eqvilent      | client   | Bluecoast |
| `steadyhash` | Steady Hash   | client   | —         |
| `gpd`        | GPD Capital   | client   | —         |
| `shaun_lim`  | Shaun Lim     | client   | —         |
| `anu`        | Anu           | client   | —         |
| `ik`         | IK Group      | client   | —         |
| `yoav`       | Yoav          | client   | —         |
| `guy_asraf`  | Guy Asraf     | client   | —         |

### Clients

`Fee (Odum)` is the **gross** Odum performance-fee share; where an introducer exists, the introducer fee is carved out
of Odum's share (§3), so Odum's **net** is lower. See §3 for the introducer splits.

| Client ID   | Organisation | Venue   | Currency | Strategy              | Tranche      | Fee (Odum, gross) | Fee (Trader) |
| ----------- | ------------ | ------- | -------- | --------------------- | ------------ | ----------------- | ------------ |
| `PR`        | Prism        | OKX     | USDT     | Mean Reversion Top 20 | managed      | 40%               | 10%          |
| `NN`        | Namnar       | OKX     | USDT     | Mean Reversion Top 20 | managed      | 30%               | 10%          |
| `ET`        | Eqvilent     | Binance | USDT     | Mean Reversion Top 20 | managed      | 30%               | 10%          |
| `STD`       | Steady Hash  | OKX     | USDT     | Mean Reversion Top 20 | managed      | 35%               | 10%          |
| `GP`        | GPD Capital  | OKX     | USDT     | Mean Reversion Top 20 | managed      | 30%               | 10%          |
| `SL`        | Shaun Lim    | OKX     | USDT     | Mean Reversion Top 20 | managed      | 30%               | 10%          |
| `SL2`       | Shaun Lim    | OKX     | BTC      | Mean Reversion Top 20 | managed      | 30%               | 10%          |
| `ANU`       | Anu          | OKX     | BTC      | Mean Reversion Top 20 | managed      | 30%               | 10%          |
| `IK`        | IK Group     | OKX     | USDT     | Mean Reversion Top 20 | managed      | 35%               | 10%          |
| `YOAV`      | Yoav         | —       | BTC      | DeFi BTC Yield        | fund_of_fund | 20%               | 0%           |
| `GUY_ASRAF` | Guy Asraf    | —       | BTC      | DeFi BTC Yield        | fund_of_fund | 20%               | 0%           |
| `ODUM_PROP` | Odum Capital | Binance | USDT     | Mean Reversion Top 20 | managed      | 0%                | 0%           |

10 managed clients run `mean_reversion_top20`; 2 fund-of-fund clients run `defi_btc_yield`. `ODUM_PROP` is the internal
reference/prop account (no fees).

### Tranches

| Tranche        | Data Source  | Description                                          |
| -------------- | ------------ | ---------------------------------------------------- |
| `managed`      | Exchange API | We hold the client's API keys, trade on their behalf |
| `fund_of_fund` | Manual entry | No exchange API — NAV entered manually per period    |

### Pooled accounts

Client `IK` is a **pooled account** — three investors share one OKX sub-account. Fees and P&L split pro-rata by weight:

| Investor | Weight  |
| -------- | ------- |
| Jihane   | 25.344% |
| Amaka    | 21.6%   |
| IK       | 53.056% |

```yaml
pool_investors:
  jihane: 0.25344
  amaka: 0.216
  ik: 0.53056
```

Pooled investor weights should be validated periodically (investors may add/withdraw capital, changing the split).

## 2. Strategies

| Strategy ID            | Name                  | Description                                                            |
| ---------------------- | --------------------- | ---------------------------------------------------------------------- |
| `mean_reversion_top20` | Mean Reversion Top 20 | Perpetual futures mean reversion on top 20 crypto assets by market cap |
| `defi_btc_yield`       | DeFi BTC Yield        | BTC-denominated yield via DeFi protocols and fund-of-fund allocation   |

## 3. Fee structure — four-tier HWM model

Each client has up to four fee components:

| Tier           | Beneficiary    | Typical %         | Calculated on                       |
| -------------- | -------------- | ----------------- | ----------------------------------- |
| Trader fee     | Desk trader    | 10%               | PnL above the trader HWM            |
| Odum fee       | Odum Capital   | 20–40%            | PnL above the Odum HWM              |
| Introducer fee | Introducer     | 5–15% of Odum fee | Only if an introducer is configured |
| Server cost    | Infrastructure | $50/month         | Only when the account is underwater |

### High-water mark (HWM)

Performance fees are charged only on **new profits above the previous high**. If the account loses money, no performance
fees are charged until it recovers past the previous peak.

- **Dual HWM:** each client tracks two independent HWMs — trader and Odum. They can differ because Odum may reset its
  HWM (e.g. after a refund) while the trader's stays, so the trader can earn fees even if Odum hasn't recouped yet, and
  vice-versa.
- **Crystallisation:** after an invoice is issued/paid, both HWMs are bumped to the closing AUM for that period.

### Underwater accounts

When `is_underwater: true` in the registry: no performance fees are charged; a $50/month server cost is charged instead,
tracked until equity exceeds the HWM again.

### Introducer fees

Some clients were referred. The introducer gets a percentage of **Odum's fee** (not of total P&L), carved from Odum's
gross share:

| Client | Introducer        | Introducer fee | Effective split                         |
| ------ | ----------------- | -------------- | --------------------------------------- |
| PR     | Max (Maxim Shilo) | 15% of Odum    | Odum 34%, Introducer 6%, Trader 10%     |
| ET     | Blue Coast        | 5% of Odum     | Odum 28.5%, Introducer 1.5%, Trader 10% |

### Per-client fee rates (net)

| Client    | Odum % (net) | Trader % | Introducer        | Introducer % |
| --------- | ------------ | -------- | ----------------- | ------------ |
| PR        | 34%          | 10%      | Max (Maxim Shilo) | 15% of Odum  |
| NN        | 30%          | 10%      | —                 | —            |
| ET        | 28.5%        | 10%      | Blue Coast        | 5% of Odum   |
| STD       | 35%          | 10%      | —                 | —            |
| GP        | 30%          | 10%      | —                 | —            |
| SL        | 30%          | 10%      | —                 | —            |
| SL2       | 30%          | 10%      | —                 | —            |
| ANU       | 30%          | 10%      | —                 | —            |
| IK        | 35%          | 10%      | —                 | —            |
| YOAV      | 20%          | 0%       | —                 | —            |
| GUY_ASRAF | 20%          | 0%       | —                 | —            |
| ODUM_PROP | 0%           | 0%       | —                 | —            |

## 4. The three HWM methods

We track three high-water marks simultaneously; each answers a different question. Per-client invoicing picks which one
matters for fees. (The general "HWM is never raw equity" invariant lives in
[`pnl-attribution.md`](/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md).)

### Method 1 — TWR HWM (performance %)

- **Answers:** "What % return does the trader need to make back?"
- Uses the Time-Weighted Return index (unitless, base = 1.0 at inception); deposits/withdrawals don't change the %
  recovery needed. Tracks pure trader performance, irrelevant of capital flows.
- **Fields:** `high_water_mark_twr`, `twr_recovery_pct`, `twr_recovery_amount`.

### Method 2 — Notional HWM (transfer-adjusted, native units)

- **Answers:** "How much actual money/BTC needs to be recovered?"
- Starts at the historical equity peak (or seed value); deposits raise the HWM, withdrawals lower it. Tracks capital
  recovery in native units (USD or BTC).
- **Fields:** `notional_hwm`, `notional_recovery`, `notional_recovery_pct`.

### Method 3 — PnL Recovery (USDT, for `pnl_based` accounts)

- **Answers:** "How much USDT trading P&L needs to be recovered?"
- For accounts where BTC balance changes are all transfers (no BTC trading); only USDT trading generates P&L.
  `recovery = seed_amount − USDT_balance_growth since tracking_start`. Stays in USDT regardless of account denomination
  — never convert to BTC.
- **Fields:** `pnl_recovery_usd`, `pnl_recovery_usd_pct`, `pnl_recovery_seed_usd`.

**Why all three?** For unseeded accounts with no transfers, Methods 1 and 2 agree (a good cross-check). For accounts
with large deposits/withdrawals they diverge and each perspective is valid. Method 3 exists specifically for GP's
invoicing model.

## 5. Per-client HWM nuances

### At HWM (no seed needed)

| Client        | Venue   | Currency | Notes                                                                             |
| ------------- | ------- | -------- | --------------------------------------------------------------------------------- |
| **PR**        | OKX     | USDT     | Best performer. HWM bumped to $335,070 on the Apr 9 invoice.                      |
| **NN**        | OKX     | USDT     | HWM bumped to $111,986 on the Apr 9 invoice.                                      |
| **ET**        | Binance | USDT     | HWM bumped to $537,939 on the Apr 9 invoice. Blue Coast introducer.               |
| **STD**       | OKX     | USDT     | HWM bumped to $1,012,861 on the Apr 9 invoice. Largest AUM.                       |
| **ODUM_PROP** | Binance | USDT     | Reference/prop account. No fees. ~49 days track record. TWR recovery 2.82% ($51). |

### Underwater — equity HWM seeds

These accounts had historical peaks before our equity-curve data starts. Seeds extracted from `invoice_state._HWM_SEED`
as of 2026-02-17/19.

| Client  | Venue | Currency | HWM Seed  | TWR Recovery | Notional Recovery  |
| ------- | ----- | -------- | --------- | ------------ | ------------------ |
| **SL**  | OKX   | USDT     | $650,000  | 318.55%      | $492,861 (216.8%)  |
| **SL2** | OKX   | BTC      | 3.216 BTC | 430.29%      | 2.578 BTC (125.5%) |
| **ANU** | OKX   | BTC      | 1.01 BTC  | 53.13%       | 0.350 BTC (53.1%)  |
| **IK**  | OKX   | USDT     | $89,000   | 73.86%       | $37,809 (73.9%)    |

- SL/SL2: same person (Shaun Lim), two accounts — USDT and BTC share classes. Methods diverge significantly (large
  historical transfers).
- ANU/IK: TWR and Notional agree closely (no large transfers distorting).
- All underwater accounts pay $50/month server cost instead of performance fees.

### GP — PnL-based recovery (special case)

| Field             | Value                                            |
| ----------------- | ------------------------------------------------ |
| Venue             | OKX                                              |
| Currency          | BTC account, but P&L tracked in USDT             |
| HWM model         | `pnl_based` (not equity-based)                   |
| PnL Recovery seed | $75,000 USDT (was $80K, $5K credited Mar 2026)   |
| Tracking start    | 2026-03-02 (after last USDT sweep of −$4,989.45) |
| Current recovery  | ~$70,464 (16.2% of equity)                       |

- BTC balance changes are ALL transfers (no BTC trading); only USDT trading generates P&L.
  `recovery = $75K − cumulative USDT P&L since tracking start`.
- At tracking start: USDT balance $258; current ~$4,794; P&L earned ~$4,536.
- Reports show: TWR = At HWM, Notional = At HWM (in BTC terms), PnL Recovery = $70,464 USD.
- Two voided invoices totalling $3,888 refunded; trader credits −$1,501.70.
- **Transfer resilience:** if GP withdraws USDT, the PnL recovery amount stays the same — the code detects USDT
  transfers (>$500 jumps on transfer-flagged days) and subtracts them from the balance change so only actual trading P&L
  counts. Edge case: many small transfers could slip through — worth spot-checking.

### IK — pooled account

IK is a single OKX sub-account shared by three investors (Jihane 25.344% / Amaka 21.6% / IK 53.056%, §1). P&L and fees
split proportionally by these weights.

### Fund-of-fund clients (manual entry)

| Client    | Currency | Odum Fee | Notes                            |
| --------- | -------- | -------- | -------------------------------- |
| YOAV      | BTC      | 20%      | NAV entered manually each period |
| GUY_ASRAF | BTC      | 20%      | NAV entered manually each period |

No exchange API, no trader fee (0%), DeFi BTC yield strategy.

## 6. Invoice lifecycle

### States

| Status | Meaning                        | Action          |
| ------ | ------------------------------ | --------------- |
| ISSUED | Invoice sent, awaiting payment | Client pays     |
| PAID   | Payment received and confirmed | HWM bumped      |
| VOIDED | Cancelled/refunded             | Credits created |

### Generation flow

1. Compute period P&L (`equity_end − equity_start`, transfer-adjusted).
2. Compare against the trader HWM and the Odum HWM.
3. If profit is above either HWM → calculate fees.
4. Generate invoice HTML with the full HWM math breakdown.
5. Issue the invoice (`status=ISSUED`).
6. On payment → mark PAID, bump both HWMs to closing AUM.
7. If a refund is needed → mark VOIDED, create trader credits.

### Committed invoice history — Apr 9, 2026 run

| Invoice          | Client          | Total     | PnL above HWM |
| ---------------- | --------------- | --------- | ------------- |
| INV-2026-PR-002  | PR              | $2,954.60 | $8,690        |
| INV-2026-NN-002  | NN              | $1,075.80 | $3,586        |
| INV-2026-ET-002  | ET              | $5,681.70 | $18,939       |
| INV-2026-STD-002 | STD             | $4,458.65 | $12,739       |
| INT-MAX-002      | PR (introducer) | $443.00   | 15% of Odum   |
| INT-BC-001       | ET (introducer) | $284.00   | 5% of Odum    |

### Committed refund history

| Client | Voided invoices            | Refunded total | Trader credits |
| ------ | -------------------------- | -------------- | -------------- |
| GP     | INV-2025-007, INV-2025-017 | $3,888         | −$1,501.70     |
| SL     | INV-2025-003, INV-2025-008 | $21,757        | −$3,949.93     |
| SL2    | INV-2025-004               | $8,308         | −$1,660.70     |
| ANU    | INV-2025-006, INV-2025-009 | $1,517         | −$309.90       |
| IK     | (none voided)              | $0             | −$1,241.18     |

## Cross-references

- Reporting pipeline (NAV/PnL/attribution parquet + API + UI):
  [`/codex/04-architecture/client-reporting-architecture.md`](/codex/04-architecture/client-reporting-architecture.md)
- HWM-is-never-raw-equity invariant + factor×layer model:
  [`/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`](/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md)
- Client funds isolation (funds never move between clients):
  [`/codex/04-architecture/client-funds-isolation.md`](/codex/04-architecture/client-funds-isolation.md)
- Live machine config (per-client fee %s, tranche, pooled weights, Secret-Manager keys):
  `execution-service/configs/credentials-registry.yaml`
- Operational runbook (onboarding / backfill / hourly update / Cloud Run / troubleshooting):
  `client-reporting-api/docs/CLIENT_OPERATIONS_GUIDE.md`
- Reporting-output + HWM-seed code details: `client-reporting-api/docs/PNL_AND_INVOICING_GUIDE.md`
