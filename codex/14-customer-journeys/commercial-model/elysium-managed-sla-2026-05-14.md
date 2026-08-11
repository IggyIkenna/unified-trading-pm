---
doc_type: codex-ssot
title: Elysium / POD — Managed SLA commercial structure (post-Phase-2 acceptance)
summary:
  Elysium/POD managed-SLA commercial structure pre-signing — $3k/mo retainer cost-build, tranche-tiered 25%/10%
  performance share, self-run carve-out ($35k = $10k handover + $25k licence), locked Phase-2 scope (CARRY_STAKED_BASIS
  + CARRY_BASIS_PERP on OKX/Bybit/Binance), and the contract-vs-SLA audit.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    deployment-ui,
    instruments-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [admin, sales]
tags: [commercial-model, elysium, sla, defi, profit-share, custody, cost]
related:
  [
    /codex/14-customer-journeys/commercial-model/elysium-account-trajectory-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/managed-defi-sla-cost-build.md,
    /codex/14-customer-journeys/commercial-model/pricing-building-blocks.md,
    /codex/14-customer-journeys/commercial-model/im-profit-share-structures.md,
  ]
created: 2026-05-20
authoritative_for: [Elysium/POD managed-SLA commercial structure and contract-vs-SLA audit]
referenced_by:
  [
    /codex/14-customer-journeys/commercial-model/elysium-account-trajectory-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/managed-defi-sla-cost-build.md,
  ]
owner:
last_reviewed:
code_refs: [unified-api-contracts/unified_api_contracts/registry/venue_collateral.py]
---

# Elysium / POD — Managed SLA commercial structure (post-Phase-2 acceptance)

> **Created 2026-05-14** in response to operator request to fold the Elysium / POD managed-SLA commercial structure into
> codex before the SLA goes out for signing. Captures: cost-build for the $3k/mo retainer, profit-share structure,
> carve-out (self-run) option, and the contract-vs-proposal audit findings (deviations, extras, under-delivery risk).
>
> **Audience**: Ikenna + Saabii_Boi + counsel pre-sign-off. Codex-internal — internal cost numbers per
> [rule 08](../_ssot-rules/08-pricing-principles.md) never leak into the client-facing SLA.
>
> **Companion docs**: [`pod-elysium-client-onboarding.md`](../pod-elysium-client-onboarding.md) — entity stack + custody
> onboarding; [`managed-defi-sla-cost-build.md`](managed-defi-sla-cost-build.md) — reusable cost-build template;
> [`pricing-building-blocks.md`](pricing-building-blocks.md) — DART 13-block anchors (this SLA is a custom shape, not a
> direct block instance); [`im-profit-share-structures.md`](im-profit-share-structures.md) — performance-fee mechanics
> (Elysium's 25%-of-their-fees model is a derivative of these).

---

## §1 — Engagement state going into the SLA

| Item                                | Status                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Underlying contract                 | Consulting Agreement, **IkeNova Ltd ↔ Elysium AM Ltd** — verbatim text now in codex at [`contracts/elysium-consulting-agreement-2025-03.md`](contracts/elysium-consulting-agreement-2025-03.md). **⚠️ Two claims in this row were CORRECTED 2026-08-11 against the source documents.** (a) **Date is UNRESOLVED, not 1 March**: the e-signed PDF (`Doc ID 5f6491d2…`) says **3 March 2025** and the subcontracting instrument cites 3 March twice; only the `(w specifics)` DOCX and track-changes PDF say 1 March. Art. 4 and Art. 6 wording is identical across versions. Do not assert either date in a client-facing document until the executed copy is confirmed. (b) **IkeNova has NOT "migrated" to Odum Research**: the only instrument on file is an **unsigned subcontracting agreement** under which IkeNova stays the Elysium counterparty and "shall remain fully responsible for performance of all obligations" — see [`contracts/elysium-subcontracting-agreement-ikenova-odum.md`](contracts/elysium-subcontracting-agreement-ikenova-odum.md). §7's instruction to name IkeNova in the legal-parties section is the correct one                                                                                           |
| Total fee (revised)                 | **$135,000** total (upward variation from the original Annex A $90,000 — **⚠️ the variation document has NEVER been located** as of 2026-08-11: Annex A of the executed contract totals $90,000 ($45k Phase One + $45k Phase Two) and no addendum exists in codex or on the operator's machine, so the uplift is currently unevidenced — do not invoice the final tranche against it until found). **Variation rationale**: extra scope absorbed during Phases 1–2 beyond Annex A's baseline, specifically (a) DeFi backtesting infrastructure (on-chain feature pipelines, LST rate handlers, lst_rates / lending_rates batch traces, paired-spec resolvers — multi-week effort across MTDS + features-onchain + strategy-service); (b) DeFi live execution path (AtomicInstruction with LEADER_HEDGE mode, 4-leg LST_AS_MARGIN compensation policy, hedge-deadline + position-balance-monitor); (c) treasury-balance-based auto-rebalancing mechanisms (react_to_equity_change → SWAP USDC↔native + matching perp rescale; lease-controller cash-sweep deferral of STAKE/UNSTAKE micro-flows); (d) Copper.co MPC + CEFFU OES institutional custody integrations and cutover from pre-cutover Trust Wallet / Cloud KMS envelope encryption. |
| Payment status (as of 2026-05-14)   | **$90,000 paid to date**; **$45,000 remaining**, due on Phase 2 production acceptance (target 2026-06 post-Copper/CEFFU cutover). Exact tranche schedule (Phase 1 upfront / Phase 1 completion / Phase 2 tranche(s) under the variation) is recorded in the underlying variation document — verify against that before final-tranche invoicing.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Out-of-scope-even-under-variation   | **MEV protection** mechanisms (private mempools, bundle submission, flashbots-style protections, encrypted-mempool relays) and **HFT execution** infrastructure (co-location, kernel-bypass networking, FPGA-accelerated order paths, sub-millisecond market-making engines) remain expressly OUT of scope. Already implicit under Annex A "Ultra-low-latency execution" exclusion; SLA §9 makes both explicit.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| Phase 1 (Research & Design)         | Delivered                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| Phase 2 (Production Implementation) | Pending production acceptance — target **2026-06 (post-cutover + Copper/CEFFU integration)**; Client seed capital under Annex A § Phase 2 "pilot execution with 'seed' capital" arrives **30 June 2026** (Service Provider's own capital used for pre-cutover testing through May 2026)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| Original expected total duration    | 8 months from 2026-03-01 ⇒ expected ~2026-11. **Now ~6 months over.** Contract uses "expect" not "shall", so soft not hard breach.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Governing law                       | Ireland (Irish Arbitration Centre)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Non-compete on consultant           | **Art. 6.2 — 24 months following agreement** — covers tokenisation + systematic DeFi basis with staking/re-staking + systematic CeFi funding/staking yields. Sweeping.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| IP ownership                        | **Art. 4 — Work Product is exclusively Elysium's** (works-for-hire + irrevocable assignment). Art. 4.6 retained right is "generic programming methods + open-source components" only.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Future-engagement clause            | **Art. 2.3** — "best efforts over 30–90 days post-completion to establish further agreement with respect to Consultant satisfying the ongoing role." This SLA _is_ that further agreement.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |

---

## §2 — Contract-vs-SLA audit (deviations + extras + under-delivery risk)

### 2.1 ✅ Aligned (SLA terms that contract anchors)

| SLA term                                                | Contract anchor                                                                                         |
| ------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| 30-day complimentary post-delivery support              | Art. 2.3 explicitly anticipates 30–90 day post-completion window                                        |
| Paid ongoing managed service from day 31                | Annex A "Scope Exclusions" — _post-launch maintenance and upgrades (can be arranged separately)_        |
| Charging separately for new venues, share classes, etc. | Annex A excludes ultra-low-latency, tokenisation, prime broker mgmt, post-launch maintenance + upgrades |

### 2.2 🟢 Extras (over-delivery — looks commercial, low cost, anchors goodwill)

| Extra                                                                   | Why not material risk                                                                                                                                                                                                                                                                               |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Copper.co + CEFFU institutional integration (June 2026)                 | NOT named in original Phase 2 scope — original scope said "major trading venues (CeFi + DeFi)" with no specified custody-provider integration. **Bundle as "Optional Pre-Cutover Integration Services at no additional cost"** in SLA — sets expectation that further custody changes are billable. |
| Structured 30-day SLA framework (vs. contract's "best efforts" wording) | Pure goodwill. Easy to bound.                                                                                                                                                                                                                                                                       |
| 24/7 alert paging via Telegram + phone                                  | Distinct from contract Phase 2 deliverable "monitoring dashboard implementation". Frame as included only during 30-day complimentary period; paid SLA carries it forward.                                                                                                                           |
| AI anomaly-triage layer (Claude Code branded as "AI Anomaly Triage")    | Wasn't in scope. Brand-up generically; don't disclose underlying provider.                                                                                                                                                                                                                          |

### 2.3 🔴 Deviations that NEED handling before signing

#### Deviation A — Re-frame the "carve-out" (Art. 4 IP)

**Problem.** Under Art. 4.1–4.2 Elysium _already owns_ all Work Product (works-for-hire + irrevocable assignment). Art.
4.5 lets them demand "all Work Products" on request. They could legally request our entire delivered codebase regardless
of what we'd prefer to share.

**Resolution.** SLA Exhibit A (Work Product Manifest) enumerates _exactly_ which modules constitute Work Product under
the Consulting Agreement. Anything not on that list is _pre-existing Service Provider platform IP_ under Art. 4.6's
"generic programming methods" retention or pre-dates the engagement. The manifest:

**INCLUDED (Work Product — Elysium-owned):**

- `strategy_service/.../strategies/v2/carry_and_yield/staked_basis.py` (CARRY_STAKED_BASIS engine)
- `strategy_service/.../strategies/v2/carry_and_yield/basis_perp.py` (CARRY_BASIS_PERP engine)
- `strategy_service/.../strategies/v2/carry_and_yield/yaml configs` for the locked venue set (§3 below)
- `execution_service/.../adapters/cefi/{okx,bybit,binance}_perp_adapter.py` for the locked venue set
- `execution_service/.../adapters/defi/{copper_mpc,ceffu_oes}_adapter.py` (the two custody adapters delivered)
- `execution_service/.../adapters/defi/lido_staking_adapter.py` (Lido stake/wrap leg)
- Strategy-specific monitoring dashboards (the two strategy P&L panels delivered)
- Phase 1 design docs + Phase 2 operational runbooks specific to the delivered Strategy

**Execution boundary — connectivity vs execution intelligence (operator ruling 2026-08-11).** Exhibit A must split the
execution layer on this line rather than naming "execution-service" wholesale:

| Layer                                                                                                       | Covers                                                                                                                                                                              | Bucket                      |
| ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| **Connectivity** — the venue adapters                                                                       | endpoints/transport, auth + key handling, order/cancel semantics, symbol + instrument mapping, rate limits + backoff, error classification, venue quirks, Copper/CEFFU signing path | **INCLUDED** (Work Product) |
| **Choreography** — the multi-leg structure                                                                  | leg ordering for the 4-leg staked-basis trade, `LEADER_HEDGE` sequence, `hedge_deadline_ms`, compensation/unwind policy, delta-neutrality held through execution                    | **INCLUDED** (Work Product) |
| **Execution intelligence** — `execution_service/algo_library/` + `algorithms/` + `v2/execution_policies.py` | slicing + scheduling, pacing vs realised volume, passive/aggressive posture, SOR (DEX + cross-chain), batching, impact model, the policy registry that resolves an algo             | **EXCLUDED** (platform IP)  |

**Two independent grounds support the EXCLUDED row — cite both, they fail differently:**

1. **Out of engagement scope.** The library is a multi-asset-group platform component. Measured 2026-08-11 by symbol
   frequency across `execution_service/algo_library/` + `algorithms/`: tradfi 55 · equity 29 · defi 25 · sports 10 ·
   prediction 5 · cefi 5. The dominant consumers are asset classes this engagement does not touch at all, so it is not
   "developed for" a delta-neutral crypto basis engagement under Art. 4.1.
2. **Art. 4.6 retention.** TWAP, VWAP, participation-rate scheduling and Almgren–Chriss are published, industry-standard
   methods — squarely "generic programming methods and open-sourced components", which Art. 4.6 expressly retains.

**Also note there is no standalone delivery obligation for algorithms.** The only delivery/return clause is Art. 4.5,
and it attaches to **Work Product** — so if a component is not Work Product, no obligation to hand it over arises.

**Open tension to put in front of counsel (do NOT paper over):** Annex A Phase One expressly lists "Development of
back-testing framework" as a deliverable, while the EXCLUDED list below places historical batch-ingestion pipelines in
platform IP. Our position: what was commissioned is the strategy-level back-testing capability, not the multi-tenant
data estate under it. That is arguable, unlike the execution position above. Tracked on
[`elysium_sla_v4_support_period_and_stale_dates_2026_08_08`](/plans/active/issues/elysium_sla_v4_support_period_and_stale_dates_2026_08_08.md).

**EXCLUDED outright — never licensed under §A.3** (Service Provider / Odum Research platform IP):

- `unified-trading-system-ui/*`, `deployment-ui/*`, `user-management-ui/*` (multi-tenant client portal — not needed for
  headless live op)
- `deployment-service/*` (multi-tenant deploy/CI infra — Client procures their own)
- Strategy archetypes outside the locked Phase 2 scope (all non-In-Scope archetypes — they're not part of what was sold)
- Non-Carry-and-Yield calculators in `features-*-service` (delta-one, volatility, calendar, sports, prediction)
- Historical batch-ingestion pipelines in MTDS + instruments-service + features-\*-service (back-test infra)
- **Execution intelligence** — `algo_library/` + `algorithms/` + the `ExecutionPolicyRegistry` (per the table above);
  the venue adapters themselves are INCLUDED
- Audit / risk / observability / alerting / operational tooling surfaces (multi-tenant)
- ML pipeline + research stack
- Service Provider's data vendor licences (Tardis / Alchemy / The Graph) — Client procures their own for research

**LICENSED (NOT transferred) under §A.3 — perpetual non-exclusive non-transferable non-sublicensable royalty-free,
solely for operating the In-Scope Strategies**:

- `unified-api-contracts/*` runtime subset (types, schema registry, venue registry for In-Scope venues, capability
  decls, lifecycle events, `VENUE_COLLATERAL_MATRIX` for In-Scope LST/venue pairs)
- `unified-trading-library/*` runtime subset (manifest readers/writers for In-Scope data shapes, primitive type guards,
  parallel runners, audit middleware, on-chain LST-rate + venue funding-rate reader primitives)
- `unified-cloud-interface/*` runtime subset (cloud abstraction for execution adapters)
- `features-onchain/*` calculator subset (`staking_apy_total` aggregator + `funding_apy_bps` derivation specifically
  consumed by In-Scope archetypes)
- `instruments-service/*` minimal reference-data subset (venue identifier registry for In-Scope venues)

**Why license-not-transfer**:

- Maintains our right to continue developing + commercialising these components for our own platform + other engagements
- Frozen snapshot at hand-over date — future updates, fixes, security patches stay with us. Elysium re-engages at
  $300/hr if they want a refresh.
- Restrictions: no redistribution, no open-source, no competing-service use, must preserve our copyright notices,
  non-transferable on change of control without acquirer ack.

**Data dependency (CRITICAL — was originally a viability gap in v1 of this codex doc)**:

- Live operation reads directly from venue WebSocket/REST APIs + Ethereum mainnet RPC. NO Service Provider data
  middleware required at runtime.
- LST rate reads: direct on-chain calls (`getPooledEthByShares` for stETH, `stEthPerToken()` for wstETH) — these are
  public Ethereum RPC calls Elysium makes via their own RPC provider.
- Funding rate reads: direct from venue (OKX/Bybit/Binance) WebSocket — Elysium uses their own institutional API
  credentials.
- Historical data (only for backtest/research) is NOT in scope of Option B; Elysium re-engages us at $300/hr if they
  want historical research after carve-out.

If Elysium opts for the **self-run carve-out**, what they receive is the §A.1 Work Product (ownership) + §A.3 Licensed
Components (frozen-snapshot licence) + the operations runbook for standing up just-enough deployment infra (lightweight
CLI runner, no UI, no fancy dashboards). They handle their own CI/CD, secrets, monitoring, alerting, security, RPC,
venue credentials.

#### Deviation B — Non-compete carve-out (Art. 6.2)

**Problem.** Art. 6.2 prohibits IkeNova for 24 months following agreement from:

1. Tokenisation of investment funds
2. **Systematic DeFi basis trading and funding strategies premised on staking/re-staking**
3. **Systematic CeFi funding rate and staking yields strategies**

Items 2 + 3 cover our entire `Carry & Yield` archetype family. The 24-month clock starts after agreement ends; while the
agreement is ongoing it's not yet active, but it will become a hard block.

**Resolution (per operator 2026-05-14).** SLA Exhibit B (Strategy Family Scope + Non-Compete Clarification) clarifies:

- **In Scope for Elysium under the Consulting Agreement + SLA**:
  - `CARRY_STAKED_BASIS` (Phase 2 acceptance scope — see §3)
  - `CARRY_BASIS_PERP` (Phase 2 acceptance scope — see §3)
- **Within the Carry & Yield family but OUT of current engagement scope** (other Carry & Yield archetypes IkeNova has
  designed independently):
  - `CARRY_RECURSIVE_STAKED` (recursive-leverage variant)
  - `YIELD_STAKING_SIMPLE` (passive LST hold)
  - `YIELD_ROTATION_LENDING` (lending-only rotation)
  - `CARRY_BASIS_DATED` (dated-futures variant)
  - `CARRY_RECURSIVE_BORROW_LENDING_ONLY` / `..._PERP_HEDGED`
- **Strategy families NEVER in scope for Elysium** (e.g. ARBITRAGE*\*, MARKET_MAKING*\_, ML*DIRECTIONAL*\_,
  EVENT*DRIVEN, VOL_TRADING_OPTIONS, STAT_ARB*\_, RULES*DIRECTIONAL*\_, LIQUIDATION*CAPTURE, DEFI_LP*\*) — operating
  these is unaffected by Art. 6.2 because they fall outside the strategy types described.

**Right of first refusal mechanic.** For the _in-family-but-out-of-engagement_ Carry & Yield variants above, Elysium is
granted a right of first refusal — IkeNova will offer Elysium first opportunity to commission each as a new SOW. **If
Elysium declines or doesn't respond within 30 days of offer, IkeNova retains the right to deliver that variant to its
own book or to other clients without breach of Art. 6.2.** This protects our broader business without taking commercial
value away from Elysium.

**Action**: Exhibit B drafted alongside the SLA; both signed together.

#### Deviation C — Timeline reset

**Problem.** Contract expected 8 months (signed 2026-03-01, expected ~2026-11). We're now mid-2026-05, projecting Phase
2 acceptance in 2026-06. Soft language ("expect" in Art. 3.2) means not a hard breach, but written reset protects both
sides.

**Resolution.** SLA preamble includes: _"The parties confirm by mutual continued performance that the Phase 2
production-acceptance event occurring on or around [date] in 2026-06 satisfies the Consulting Agreement's Phase 2
acceptance criteria notwithstanding the indicative 8-month expected duration in Annex A § Term."_

### 2.4 🟡 Under-delivery risk — Phase 2 scope precision

**Problem.** Contract scope = "delta-neutral basis trading on BTC/ETH/SOL spot + perps across major venues" —
archetype-agnostic. If we ship only one archetype and Elysium signs SLA, they could later argue Phase 2 is incomplete.

**Resolution (per operator 2026-05-14).** Phase 2 acceptance scope is broader than just CARRY_STAKED_BASIS — see §3.

---

## §3 — Locked Phase 2 acceptance scope

### 3.1 In-scope strategies + venues

| Archetype            | Custody        | Spot/stake venue        | Perp venue                       | LST / collateral            | Status     |
| -------------------- | -------------- | ----------------------- | -------------------------------- | --------------------------- | ---------- |
| `CARRY_STAKED_BASIS` | Copper + CEFFU | Lido (Ethereum mainnet) | **OKX** (multi-currency margin)  | wstETH (wrapped Lido stETH) | In Phase 2 |
| `CARRY_STAKED_BASIS` | Copper + CEFFU | Lido (Ethereum mainnet) | **Bybit** (UTA cross-collateral) | stETH (Lido rebasing form)  | In Phase 2 |
| `CARRY_BASIS_PERP`   | Copper + CEFFU | spot venue per perp     | **OKX**                          | n/a (USDC margin)           | In Phase 2 |
| `CARRY_BASIS_PERP`   | Copper + CEFFU | spot venue per perp     | **Bybit**                        | n/a (USDC margin)           | In Phase 2 |
| `CARRY_BASIS_PERP`   | Copper + CEFFU | spot venue per perp     | **Binance** (Multi-Assets Mode)  | n/a (USDC/USDT margin)      | In Phase 2 |

**That's the full Phase 2 scope.** Anything else is out.

> **Scope rationale.** OKX and Bybit are the only contracted perp venues that accept Lido staked tokens (wstETH / stETH)
> as cross-margin, so they're the only venues where `CARRY_STAKED_BASIS` can run under the LST_AS_MARGIN structure — see
> [`../../09-strategy/architecture-v2/archetypes/carry-staked-basis.md`](../../09-strategy/architecture-v2/archetypes/carry-staked-basis.md)
> §"Token / position flow — LST_AS_MARGIN" and the venue-collateral matrix table. Binance and other CeFi perp venues
> don't accept LST cross-margin, so they're CARRY_BASIS_PERP-only.

### 3.2 Out-of-Phase-2 (priced separately)

Any additions to the in-scope list above are **one-time charges**:

- **New perp venue** (e.g. Deribit, Hyperliquid, Aster, Drift, Kraken, Bitfinex, Bitget): **$2,500 one-time** covering
  50–100 hours of research + backtesting + venue-collateral matrix update + adapter integration + data subscription
  evaluation + risk-engine calibration + operational go-live hours.
- **New LST / staking protocol** (e.g. Rocket Pool rETH, Coinbase cbETH, EtherFi eETH, Jito jitoSOL, Marinade mSOL,
  Binance bETH): **$2,500 one-time** covering same components — **but conditional on Client securing venue-side
  cross-margin acceptance first** (direct venue, Copper/CEFFU tri-party mirror, or prime broker line). That commercial
  work is _Client's scope, not ours_. SLA §4.3.1 spells out the boundary + trigger + hourly fallback if venue acceptance
  is withdrawn mid-integration. Why Lido is starting scope: only LST issuer with native cross-margin acceptance at the
  In-Scope venues (Bybit accepts stETH, OKX accepts wstETH).
- **Bundled new venue + new LST** (e.g. Drift + jitoSOL): **$3,500 one-time** when commissioned together.
- **New strategy archetype** (any non-CARRY_STAKED_BASIS, non-CARRY_BASIS_PERP): **separate SOW** with its own
  commercial — not within the SLA. Defaults to $15k–$45k depending on complexity.

---

## §4 — Cost build-up for the $3k/mo retainer

> **Codex-private** per rule 08. Never leaks into the client-facing SLA.

### 4.1 Components (USD/month, sole-client allocation at launch)

| Layer                | Component                                                                                   | Sole-client cost      | Steady-state (3+ clients) marginal cost |
| -------------------- | ------------------------------------------------------------------------------------------- | --------------------- | --------------------------------------- |
| Cloud infrastructure | Compute (Elysium-allocated GCP+AWS share)                                                   | $150                  | $120                                    |
| Cloud infrastructure | Storage (~150 GB hot + ~1 TB warm)                                                          | $30                   | $25                                     |
| Cloud infrastructure | Network egress, DNS, load balancing                                                         | $30                   | $25                                     |
| Cloud infrastructure | Cloud KMS, Secret Manager, IAM mgmt                                                         | $20                   | $15                                     |
| Cloud subtotal       |                                                                                             | **$230**              | **$185**                                |
| Network + Security   | Cloudflare Pro / WAF / DDoS (shared)                                                        | $20                   | $10                                     |
| Network + Security   | Pen-test + vuln-scan amortized ($5k/y)                                                      | $80                   | $30                                     |
| Network + Security   | Backup + DR archival                                                                        | $40                   | $25                                     |
| Net + Sec subtotal   |                                                                                             | **$140**              | **$65**                                 |
| AI ops layer         | "AI Anomaly Triage & Code-Repair" (Claude Code)                                             | $400                  | $100 (1/4 of $400 across 4 tenants)     |
| Human ops time       | L1 monitoring (US 24/7 operator, $1k/mo total)                                              | $500 (50% allocation) | $200 (1/5 across 5 tenants)             |
| Human ops time       | L2/L3 engineering oversight (10h/mo sole-client → 5h/mo steady-state @ $150/h fully-loaded) | $1,500                | $750                                    |
| Human ops time       | Monthly reporting & investor-facing admin                                                   | $300                  | $200                                    |
| Human ops subtotal   |                                                                                             | **$2,300**            | **$1,150**                              |
| Strategy maintenance | Strategy slot upkeep ($150/slot × 2 archetypes)                                             | $300                  | $250                                    |
| Execution layer      | Custody+perp-venue adapter monitoring                                                       | $200                  | $150                                    |
| **Raw monthly cost** |                                                                                             | **$3,570**            | **$1,800**                              |
| **+ 20% buffer**     |                                                                                             | **$4,284**            | **$2,160**                              |

### 4.2 Pricing landing — $3,000/mo flat

- **Sole-client launch period (June 2026 onwards)**: $3k under-prices true cost by ~$1,300/mo. We eat the difference as
  goodwill/learning-curve discount — documented internally, never disclosed.
- **Steady-state (3+ Carry & Yield managed-SLA clients on platform)**: $3k is ~40% gross margin over marginal cost.
  Healthy.
- **20% buffer applied to steady-state marginal cost ($1,800) lands at $2,160** → $3k carries an additional ~$840 margin
  baked in. This is the room to absorb cost-growth drivers (§4.3) without re-negotiating mid-term.

### 4.3 Projected cost-growth drivers (charged separately or via re-negotiation)

| Driver                                                            | Threshold               | Pricing                                                   |
| ----------------------------------------------------------------- | ----------------------- | --------------------------------------------------------- |
| New venue added to in-scope set                                   | Per venue               | $2,500 one-time + $0/mo (folded into $3k)                 |
| New LST / staking protocol                                        | Per protocol            | $2,500 one-time + $0/mo (folded into $3k)                 |
| New end-client share class onboarded                              | Within 10h/mo allowance | $0                                                        |
| New end-client share class onboarded                              | Beyond 10h/mo allowance | $200/hr at preferred rate                                 |
| Capital scaling — AUM > $50M                                      | Per tier                | Re-negotiated retainer tier (anticipate +25-50%)          |
| Capital scaling — AUM > $100M                                     | Per tier                | Dedicated infrastructure tier — re-negotiated             |
| Custody provider material change (e.g. Copper API v2, MPC re-key) | Per event               | Billed at $200/hr                                         |
| Venue API breaking change                                         | Per venue per event     | First 4 hr/quarter included; beyond billed at $200/hr     |
| New chain support (beyond Ethereum)                               | Per chain               | Treated as new venue: $2,500 one-time                     |
| Security incident requiring forensics                             | Per event               | $250/hr forensics + remediation                           |
| SLA tier upgrade (e.g. 24h response → 1h response)                | On request              | Re-negotiated retainer tier                               |
| **NOT a cost-growth driver**: new strategy archetype              | —                       | Always separate SOW, never re-negotiates the $3k retainer |

---

## §5 — Profit-share (tiered: 25% then 10% on AUM tranches above $100M)

Per operator direction 2026-05-14 (refined): variable compensation is a **tranche-tiered share** of the gross
performance fees POD/Elysium receives from end-clients allocated to the in-scope Strategies:

| Strategy-attributable AUM tranche | Performance share rate                            |
| --------------------------------- | ------------------------------------------------- |
| First $100M of AUM                | **25%** of perf fees attributable to that tranche |
| Above $100M of AUM                | **10%** of perf fees attributable to that tranche |

Waterfall application: at $150M AUM, the rate is 25% on the perf fees attributable to the first $100M + 10% on the
remaining $50M. Drop to 10% kicks in only above $100M; for the inaugural-period AUM (expected well below $100M) the
effective rate is 25%.

### 5.1 Reporting + payment mechanic

- POD/Elysium's **fund administrator** (registered, regulated fund admin) produces the monthly statement of (a)
  Strategy-attributable AUM at calendar-month-start and (b) gross performance fees received from end-clients allocated
  to `CARRY_STAKED_BASIS` and/or `CARRY_BASIS_PERP`, broken down by AUM tranche.
- Statement made available via fund-administrator portal (or email PDF/CSV if portal access isn't practical) within 10
  business days of month-end.
- **Service Provider cross-verifies** Reported Performance Fees against trade-level records held internally — including
  via venue API keys we hold for accounts trading the in-scope Strategies (read-only keys at minimum). This is the
  primary reconciliation channel; formal audit is fallback.
- Service Provider invoices applicable tranche-weighted share within 5 business days of statement receipt.
- Payment due within 20 calendar days of invoice.
- Retainer ($3k/mo flat) and performance share are independent.

### 5.2 Survival

- **Under Option A** (Managed Service): performance-share continues as long as the Service Provider continues to operate
  the Strategy under this SLA.
- **Under Option B** (Self-Run Carve-Out): performance-share survives for **24 calendar months from Option B election**
  — not indefinite. After 24 months, no further performance-share is due in respect of Option B operation. Rationale:
  capped survival protects core economics against Elysium terminating to capture 100% of upside, but doesn't trap them
  indefinitely after they've taken full operational responsibility.

### 5.3 Audit right (fallback to fund-admin portal reconciliation)

Service Provider has the right, on 10 business days' written notice, to commission a third-party auditor to verify the
Reported Performance Fees during any rolling 12-month period. Audit cost borne by Service Provider unless audit
finds >5% under-reporting, in which case Elysium bears audit cost + back-pays delta + 10% interest. **Where the
fund-administrator portal provides sufficient self-service reconciliation (expected default), no separate audit is
required** — we cross-verify via internal trade records + portal data.

### 5.4 Cap / floor

No cap, no floor, no high-water mark on the Service Provider side. Performance share is a flat tranche-weighted
percentage flow-through on whatever POD/Elysium _actually receives_. POD/Elysium's own structure with end-clients
(high-water marks, hurdle rates, fee-tier breakpoints) is their commercial concern.

---

## §6 — Carve-out option (client self-runs after Day 30)

After the 30-day complimentary post-delivery support period ends, Elysium has two options:

### Option A — Managed SLA (recommended for client, default)

- IkeNova continues to operate the Strategy 24/7 from IkeNova infrastructure.
- $3,000/mo retainer + 25% performance share (§5).
- Includes alert monitoring, incident response, deployment of bug-fixes, custody re-keys, venue API upgrades within
  scope.
- New strategies, new venues, new chains, new share classes (beyond 10h/mo) billed separately.

### Option B — Self-run carve-out

- Elysium receives the Work Product Manifest (§2.3 Deviation A — INCLUDED list).
- Elysium handles **all of**: deployment, CI/CD pipeline setup, secrets management, infrastructure provisioning (cloud
  accounts, VMs, networking, monitoring stack), security posture, alerting, on-call rotation, custody-provider
  operational relationships, venue operational relationships, regulatory reporting infrastructure, fund-administration
  interfaces, ongoing strategy parameter tuning.
- Service Provider provides a one-time written hand-over package: code repository access (Work Product per §A.1) +
  frozen snapshot of Licensed Components per §A.3 (UAC + UTL + UCI + features-onchain calc subset + instruments-service
  reference data) + lightweight CLI-runner deployment runbook + strategy-config templates + operational runbook + 4-hour
  Q&A walkthrough.
- **Carve-Out Fees**: **$10,000 hand-over and training fee** (covers prep + walkthrough) + **$25,000 Licensed Components
  one-time licence fee** (perpetual non-exclusive non-transferable paid-up licence under §A.3) = **$35,000 total**
  payable on election.
- Performance share (§5) applies for **24 months from Option B election** (not indefinite). After 24 months, no further
  performance-share is due in respect of Option B operation.
- Service Provider has no ongoing operational obligations under this option.
- Post hand-over, any further Service Provider involvement (consulting, debugging, upgrades, new venues) billed at
  $300/hr with a 4-hour minimum per request.

### Switching between options

- Default: Option A from Day 31 (managed SLA auto-applies absent written election).
- Elysium may elect Option B at any time on 30 days' written notice; the **Carve-Out Fees ($35k total = $10k hand-over +
  $25k licence)** become due on election.
- Switching from Option B back to Option A: $5k one-time re-onboarding fee + 30-day delay. **The $25k Licensed
  Components licence stays paid-up** — a future second Option B election would only re-trigger the $10k hand-over fee,
  not the licence fee.

---

## §7 — SLA structural notes

- **Legal entity match**: SLA names "IkeNova Ltd" exactly as contract signature page. "Odum Research" is a marketing
  trade name and shouldn't appear in the SLA's legal-parties section. (Existing draft says "Odom Research" — typo +
  entity-mismatch — fix.)
- **Contract date in SLA preamble**: must say 1 March 2025 (existing draft says 3 March — error).
- **Governing law**: Ireland (mirror contract Art. 7.2).
- **Dispute resolution**: Irish Arbitration Centre (mirror contract Art. 7.4).
- **24/7 commitment**: paid SLA carries a 24/7 alert-response commitment (mirror operator direction 2026-05-14 _"we
  probably need to guarantee 24/7 functionality"_) with response-target tiers tightened from the current draft
  (Critical: 1h not 24h; High: 4h not 48h; Medium: 1 business day; Low: 3 business days).
- **Exclusions section**: drop "no 24/7 operational guarantee" line from the existing draft — it contradicts the paid
  SLA promise.

---

## §8 — Cross-references

- **Contract text, in codex (verbatim):**
  [`contracts/elysium-consulting-agreement-2025-03.md`](contracts/elysium-consulting-agreement-2025-03.md) ·
  [`contracts/elysium-subcontracting-agreement-ikenova-odum.md`](contracts/elysium-subcontracting-agreement-ikenova-odum.md).
  **Read the consulting-agreement record before relying on any ownership statement in this doc.**
- Contract source (local originals):
  `/Users/ikennaigboaka/Downloads/20250301 _ Elysium x IkeNova _ Consulting Agreement _v2 (w specifics).docx` (also
  `/Users/ikennaigboaka/Downloads/Elysium_x_IkeNova_contract.pdf`).
- SLA output: `/Users/ikennaigboaka/Downloads/ODUM_SLA_v2_2026-05-14.docx` (revised; supersedes
  `ODUM SLA - DRAFT.docx`).
- Strategy spec:
  [`../../09-strategy/architecture-v2/archetypes/carry-staked-basis.md`](../../09-strategy/architecture-v2/archetypes/carry-staked-basis.md)
  — venue-collateral matrix + LST_AS_MARGIN structure.
- Venue/LST matrix SSOT: `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py`
  (`VENUE_COLLATERAL_MATRIX`).
- POD/Elysium onboarding: [`../pod-elysium-client-onboarding.md`](../pod-elysium-client-onboarding.md).
- DART pricing anchors (NOT directly applied here — Elysium is a custom shape):
  [`pricing-building-blocks.md`](pricing-building-blocks.md).
- Reusable managed-SLA cost-build template: [`managed-defi-sla-cost-build.md`](managed-defi-sla-cost-build.md).
- Pricing principles (rule 08, internal-cost-private):
  [`../_ssot-rules/08-pricing-principles.md`](../_ssot-rules/08-pricing-principles.md).
