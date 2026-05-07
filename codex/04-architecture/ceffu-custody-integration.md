---
scope: [engineer, admin]
status: stub
created: 2026-05-07
created_by: Agent-5 deep-audit follow-up to Group F item 19
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

> **STUB — content owners pending.** Created 2026-05-07 as a deep-audit follow-up to
> [`../../plans/active/master_to_live_defi_2026_05_23.plan.md`](../../plans/active/master_to_live_defi_2026_05_23.plan.md)
> Group F item 19 (Treasury / custody integration). The Copper-side companion at
> [`copper-custody-integration.md`](copper-custody-integration.md) is the reference shape; CEFFU coverage parallels it
> for Binance institutional flow. Content authors: whoever owns Binance institutional wiring (defi_master Fork 1
> hedging-leg + Group F item 19). Sub-headings below mirror the Copper page so the two can be read side-by-side.

# CEFFU Custody Integration

## Overview

CEFFU (formerly Binance Custody) is the **institutional custody provider for Binance perp / spot exposure** in the
6-venue perp universe (Bybit / Deribit / Binance / OKX / Hyperliquid / Aster). The same pluggable `CustodyProvider`
interface used for Copper applies here — switching providers is a config change, not a code change.

**Why CEFFU:**

- AWS-compatible — wallet hosts can run AWS-resident (per master plan §"Decisions taken in-session" point 4 — custody
  provider AWS-compat is a precondition for the dual-cloud-active steady state).
- Native integration with Binance institutional flow (deposit/withdrawal via Binance APIs without bridging from a
  separate MPC provider).
- Sub-account model maps cleanly to per-strategy wallet hierarchy (see
  [`wallet-hierarchy-and-capital-flow.md`](wallet-hierarchy-and-capital-flow.md)).

**Scope of this integration:**

- Binance perp (carry_staked_basis hedge leg + leveraged_funding_arb cross-venue funding spread).
- Binance spot (collateral movement between perp and spot accounts).
- (Out of scope) Bybit, Deribit, OKX use their own institutional custody — Hyperliquid + Aster are on-chain-direct (no
  CEFFU equivalent, wallets sit at the smart-contract level).

## API Architecture

> **PENDING.** CEFFU API auth shape, request signing, endpoint catalogue. Mirror the Copper page sections
> (Authentication, Core Endpoints, Wallet Types, Transaction Signing Flow, Supported Chains, Transfer Policies) when
> content authors populate. Reference: <https://www.ceffu.com/docs> (validate against current CEFFU institutional-API
> documentation).

## Integration in execution-service

> **PENDING.** `CEFFUCustodyProvider` class in `execution-service/execution_service/custody/`. Mirror the Copper page
> sections (Constructor / Methods / Factory). The pluggable `CustodyProvider` interface in
> `unified-config-interface/testnet_contracts.py` drives the factory pattern.

## Testing

> **PENDING.** Mock mode + integration tests + VCR cassettes — mirror Copper's
> `tests/integration/test_copper_custody_provider.py` shape under `tests/integration/test_ceffu_custody_provider.py`.
> Per CLAUDE.md "Testing Infrastructure" rule: credential-free local tests via
> `CLOUD_PROVIDER=local CLOUD_MOCK_MODE=true`; cassette parity test in
> `unified-api-contracts/tests/test_cassette_schema_parity.py`.

## Configuration

> **PENDING.** Environment variables, Secret Manager keys, per-strategy wallet mapping. Mirror Copper page sections.
> CEFFU credentials should follow the workspace HMAC-SHA256 pattern + `ApiKeyReloader` from UTL (per CLAUDE.md "Service
> Infrastructure Requirements" rule).

## Cross-Strategy Wallet Concerns

> **PENDING.** Sub-account allocation per strategy archetype, transfer policies, audit log retention. Mirror Copper page
> § "Cross-Strategy Wallet Concerns".

## Open questions (for content authors)

- [ ] Does CEFFU expose a sub-account-per-strategy model out-of-the-box, or do we manage strategy-attribution ourselves
      at the application layer (PBMS) on top of a single CEFFU account?
- [ ] Is there a CEFFU-side equivalent to Copper's MPC + transfer-policy "circuit breaker" or do we rely on Binance
      account-level withdrawal limits + alerting-service kill switches?
- [ ] AWS-region pinning: is CEFFU's API endpoint region-specific (must we deploy to a particular AWS region for low
      latency) or is it global edge-cached?
- [ ] What's the cost / fee model? (Copper charges by AUM band; CEFFU's institutional pricing is bespoke per client.)
- [ ] Withdrawal whitelist management — is it API-driven or operator-driven via the CEFFU dashboard?

## References

- [`copper-custody-integration.md`](copper-custody-integration.md) — peer integration; structural template for this page
  once populated.
- [`custody-providers.md`](custody-providers.md) — catalogue of supported / candidate custody providers.
- [`wallet-hierarchy-and-capital-flow.md`](wallet-hierarchy-and-capital-flow.md) — strategy-instance / venue-account
  capital-flow contract.
- [`../../plans/active/master_to_live_defi_2026_05_23.plan.md`](../../plans/active/master_to_live_defi_2026_05_23.plan.md)
  § Group F item 19 — live-trading prereq tracking.
- [`../../plans/active/defi_master_2026_05_07.plan.md`](../../plans/active/defi_master_2026_05_07.plan.md) Fork 1 —
  Binance perp hedging-leg ownership.
