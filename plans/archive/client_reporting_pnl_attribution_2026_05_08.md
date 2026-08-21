---
doc_type: plan
title: client-reporting-pnl-attribution
summary: Client reporting API + unified-trading-system UI surface — NAV / PnL / metrics per client, invoicing, PnL attribution.
  Internal-strategy vs external-strategy (via client-supplied API keys). Is it solved end-to-end and could PnL attribution
  be offered as a standalone service?
status: plan-spawned
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, execution-service, market-tick-data-service, strategy-service, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/questions/wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md,
    plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md,
    plans/active/issues/missing_question_docs_orphan_references_2026_05_10.md,
  ]
created: 2026-05-08
type: question
plan_spawned: 2026-05-10
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-08
spawned_plan: plans/active/client_reporting_pnl_attribution_mvp_2026_05_10.md
related_codex: [/codex/04-architecture/separation-of-concerns.md]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Client reporting + PnL attribution — end-to-end question

> **Reconstruction note (2026-05-10).** The original draft of this doc (created 2026-05-08) was lost — never committed
>
> - erased from disk during parallel-agent activity. Re-spawned per
>   [`missing_question_docs_orphan_references_2026_05_10.md`](../active/issues/missing_question_docs_orphan_references_2026_05_10.md)
>   disposition (a). Block A + B content reconstructed from conversation context (Read tool output preserved the
>   original Blocks A1-A7 + B1-B5). Block C synthesized from the original framing line. Operator should review the
>   iteration log + the body for any framing drift vs original intent.

## Intent

Two separable surfaces are in scope here, and the question is whether either is actually production-ready today:

1. **Client reporting** — for each client account we manage, the operator + the client need a self-serve view of NAV,
   PnL (gross / net / by period), per-client metrics (Sharpe, drawdown, hit rate, fee accruals, capital efficiency,
   exposure breakdowns by venue / instrument-type / strategy / asset_group), and **invoicing** (period-end management
   fee + performance fee derived from the same NAV+PnL feed, not a parallel bookkeeping path). The UI is
   `unified-trading-system-ui` — the question is whether the API + UI surface actually exists, what data feeds it, and
   whether the numbers reconcile against position-balance-monitor + execution-service ground truth.

2. **PnL attribution** — decomposing PnL into the components that produced it (strategy alpha vs execution alpha vs
   financing/funding vs venue rebates vs slippage vs fees vs FX vs basis-roll vs whatever else applies per archetype).
   This needs more than top-line PnL — it needs the full ladder of intermediate signals + fills + venue-side cost data.

The _separable_ part of question 2: PnL attribution as currently designed assumes our internal pipeline emitted the
strategy instructions + we own the execution path. **But in theory** — if a third party gives us their account's API
keys + tells us what strategies they're running (or even just gives us position + instruction history), could we run the
attribution layer over their data and offer it as a service? What in the current codebase intrinsically depends on
internal data structures vs what is generic-enough to ingest external strategy-instruction + position streams? This
matters because it informs whether the attribution module belongs as a tightly-coupled internal component or as a
cleaner-bounded service with a public API contract.

## Question

### Block A — Client reporting API + UI surface

A1. Does a client-reporting API service exist today? If yes — what's the repo, what endpoints, what auth model
(per-client OAuth / API key / Firebase claim), what data sources feed it (position-balance-monitor? execution-service? a
separate ledger service?). If no — where would it land in the 67-repo system and what's the closest existing surface
(deployment-api? a UI-specific BFF?).

A2. NAV calculation — what's the canonical NAV-per-client computation today? Live mark-to-market across venues +
accounts + chains + instruments, or end-of-day snapshot? Does it handle multi-currency / multi-collateral correctly
(USDC + ETH + stETH + perp-margin all denominated to USD)? Does it handle DeFi positions (LST yield accrual, AMM LP,
lending, vaults) the same way as CeFi positions, or is there divergence? Where's the SSOT for "NAV at time T for client
C"?

A3. PnL computation — gross vs net (post-fee, post-financing), realized vs unrealized, period boundaries (does it
support arbitrary date ranges, monthly/weekly/daily snapshots, since-inception)? Are PnL numbers reconciled against
ground-truth fills + carry / funding / staking yield events, or is there divergence between "what the strategy thinks
happened" vs "what actually settled at the venue"?

A4. Per-client metrics — what's the agreed metric set? Sharpe / sortino / max drawdown / hit rate / capital efficiency /
VaR / per-asset-group exposure / per-venue exposure / fee load / financing load. Where do they get computed (live in the
API, batch job, materialized view)? Are they consistent with what risk-and-exposure-service computes for internal
monitoring, or are there two parallel definitions?

A5. Invoicing — does an invoicing pipeline exist today? Inputs (period NAV start + NAV end + high-water mark +
management-fee rate + performance-fee rate + crystallization period), outputs (invoice PDF / line-item ledger / wire
instructions). Reconciliation (does the invoiced fee reduce reported NAV in the next period correctly)? Is there a
self-serve client-facing invoice surface in the UI, or is this operator-side only?

A6. UI surface in `unified-trading-system-ui` — which pages today render client-scoped NAV / PnL / metrics? Are they
client-self-serve (client logs in, sees their own account only) or operator-only (Ikenna sees all clients)? What's the
auth/authz model (Firebase custom claims for client_id?)? Are mock-mode fixtures populated for client-reporting widgets,
or do those widgets show "Failed to load" today?

A7. End-to-end real-data state — has any real client account ever had their NAV + PnL + metrics + invoice rendered
through the full live pipeline against real venues? Or is this code-shipped-but-never-run? What's the operational gap
between current state and "Ikenna can show a real client a real account view today"?

### Block B — PnL attribution

B1. What's the canonical PnL-attribution decomposition we want per archetype? Concretely: for `carry_staked_basis` (LST
stake + perp short hedge), the natural decomposition is (staking yield accrual) + (perp funding accrued) + (basis carry
/ roll) + (execution slippage at entry/exit) + (fee load) + (venue financing) + (FX if any) + (residual / unexplained).
For `leveraged_funding_arb` (perp funding farming with leverage), what's the equivalent? What about CeFi arbitrage /
market-making / sports betting / prediction-markets? Is there a per-archetype attribution schema declared anywhere
(UAC?), or is it implicit-knowledge-only?

B2. Internal-strategy attribution — for our own strategies running through strategy-service → execution-service, where
does the attribution computation live today? Does it consume strategy-service emitted signals + execution-service
fills + position-balance-monitor positions + market-tick-data-service venue costs, or is there a dedicated attribution
service? Is the data lineage clean enough to attribute correctly (strategy instruction X at time T produced fill Y at
time T+latency for instrument Z resulting in position delta D + fee F + slippage S vs reference price R)?

B3. Backtest vs live attribution parity — per workspace SSOT _"Live = batch — same data, same fields, same timing
semantics"_, the attribution decomposition should be identical for backtest vs live runs (different fill sources, same
attribution math). Is this actually true today, or does backtest attribution use simplified fee/slippage assumptions
that drift from live attribution?

B4. External-strategy attribution (the "as a service" question) — if a client gives us:

- their venue API keys (read-only enough to pull positions + fills)
- their strategy-instruction history (or even just a labelled ledger of "intended position at time T")
- their archetype declaration (so we know which decomposition schema to apply)

  ...could we run the attribution layer over their data? What in the current attribution code intrinsically depends on:

- internal UAC types / internal event streams that external clients can't reasonably produce?
- knowing the strategy-service signal lineage (vs just the fills + positions)?
- having execution-service's matching engine for backtest comparison?
- position-balance-monitor's specific shape for position state?

  Is the attribution module already factored cleanly enough that the "external strategy via API keys" path is mostly an
  adapter problem, or is it tangled with internal-only assumptions?

B5. Productisation surface — if (B4) is feasible, what would the public API contract look like? Inputs (venue keys /
position ledger / instruction ledger / archetype declaration) → outputs (per-period attribution decomposition +
visualization). Auth, billing, multi-tenant data isolation, SLA. Is there appetite + market for this, or is it premature
to discuss?

### Block C — Cross-cutting integration

C1. How does client reporting interact with the **risk** stack
([`risk_simulations_limits_alerting_2026_05_08.md`](risk_simulations_limits_alerting_2026_05_08.md))? Per-client risk
limits should feed per-client reporting (utilization vs limit, breach history). Per-client PnL should feed risk
simulations (capital-at-risk for stress scenarios). Is there a shared per-client data model, or are reporting + risk
computing per-client metrics independently?

C2. How does it interact with **alerting**? Client-facing alerts (NAV drawdown breach, daily PnL threshold) vs
operator-facing alerts (reconciliation drift between reported NAV vs ground-truth NAV). The current `AlertChannel` enum
(UAC@d00326d) has 5 channels — `PAGERDUTY` / `TELEGRAM` / `SLACK` / `EMAIL` / `LOG_ONLY` — **none client-facing**. For
per-client alerts, do we extend `AlertChannel` with `FIREBASE_CLIENT` / `EMAIL_CLIENT` / `IN_APP_CLIENT` (one canonical
enum), or route per-client alerts via a separate service that consumes the same `AlertCode` taxonomy (two parallel
surfaces)? Per-client subscription preferences (which alert types the client wants) — wired or out of scope? See sibling
[`risk_simulations_limits_alerting_2026_05_08.md`](risk_simulations_limits_alerting_2026_05_08.md) Block C5 for the
parallel framing of this question.

C3. How does it interact with **custody / treasury** (Copper + CEFFU per master plan Group F item 19)? NAV must include
custody-held assets + venue-margin assets + on-chain wallet assets. Is there a unified treasury view, or is custody NAV
bolted on later? See sibling
[`wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md`](wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md)
Block B for the treasury-side framing of the same surface.

C4. How does it interact with **client onboarding + share-class subscription** (sibling wallet_treasury Block A + C)?
Client-reporting outputs (NAV / PnL / fee-accrual) require the share-class registry + client-share-class subscription
links + per-archetype attribution schema as data. The reporting surface CONSUMES these from the wallet_treasury
lifecycle SSOTs.

## What "answered" looks like

- A canonical plan exists in `plans/active/client_reporting_pnl_attribution_<date>.md` (or folds into the existing
  live-DeFi epic if scoped narrowly enough).
- Codex SSOT(s) describe: client-reporting service architecture; NAV / PnL / metrics computation contracts;
  per-archetype PnL-attribution decomposition schema; external-strategy attribution as a service (boundary + API
  contract) — even if the productisation is deferred, the architecture is described so the boundary is clean.
- A real-data run has shipped: at least ONE real client account has their NAV + PnL + metrics + invoice rendered
  end-to-end through the live pipeline, against real venues, with reconciliation against ground-truth fills + carry
  events.
- The PnL-attribution decomposition is declared per-archetype as data (UAC `AttributionSchema` registry or equivalent)
  - tested for backtest-vs-live parity per the workspace "Live = batch" SSOT.
- The external-strategy attribution boundary is declared (productisable or not), with the architecture shape recorded in
  codex even if no external customer is onboarded by May-23.
- Service-readiness checklist: per master plan Group F items 19 + 20 + Group G item 23, all gates green for live-DeFi
  cutover scope; per-client surfaces deferred-post-cutover with named successor plan per Plan Archival HARD RULE.

## Audit findings (to be filled by audit pass)

For each sub-question in Blocks A-C, fill:

- **Code state**: file:line citations across deployment-api / unified-trading-system-ui / position-balance-monitor /
  execution-service / risk-and-exposure-service / strategy-service for NAV / PnL / metrics / attribution / invoicing
  surfaces.
- **Data state**: how many client records in production storage; per-client NAV history depth; per-client PnL history
  depth; attribution-schema entries per archetype; reconciliation drift metrics if logged.
- **Run state**: has any real client account ever rendered end-to-end through the live pipeline; has any invoice ever
  generated; has any external-strategy attribution test ever run.
- **Codex state**: do client-reporting + PnL-attribution codex docs exist; drift vs current code; gaps.
- **Gap analysis**: per the Block A1-C4 questions, which surfaces are code-shipped-but-never-run vs genuinely-wired vs
  greenfield; what's blocking May-23 cutover; what's deferred-post-cutover.

## Operator notes / answers

(Empty — to be filled during iteration.)

## Iteration log

| Date       | Author              | Change                                                                                                                                                        |
| ---------- | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-08 | ikenna + main agent | Initial draft created (lost — never committed; see iteration entry below)                                                                                     |
| 2026-05-10 | main agent          | Re-spawned after the original 2026-05-08 draft was confirmed lost. Reconstruction from conversation context (Block A1-B5 high fidelity, Block C synthesized). |

## Plan-shape decisions (filled before plan extraction)

- **Plan name + path**: TBD — likely splits into 2 plans:
  - `plans/active/client_reporting_internal_<date>.md` (NAV + PnL + metrics + invoicing per internal client; the
    must-have for May-23 multi-client mode IF non-Ikenna clients onboard)
  - `plans/active/pnl_attribution_decomposition_and_external_offering_<date>.md` (attribution schema per archetype +
    productisation boundary for external-strategy attribution)
- **Plan type**: mixed (code + business + product)
- **Owner side**: TBD — likely ikenna for product/business decisions (productisation scope, fee model, attribution
  schema) + harsh for implementation (UI surface, API endpoints, attribution data plumbing)
- **Codex SSOTs touched**: TBD — likely:
  - NEW: `/codex/04-architecture/client-reporting-service-architecture.md`
  - NEW: `/codex/04-architecture/pnl-attribution-decomposition-per-archetype.md`
  - NEW: `/codex/14-customer-journeys/external-strategy-attribution-as-a-service.md` (if productisation in scope)
  - UPDATE: master plan Group F + G
- **Cross-plan dependencies**:
  - Composes with
    [`wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md`](wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md)
    Block D (post-trade settlement → ledger → reconcile is upstream of NAV / PnL feeds here).
  - Composes with [`risk_simulations_limits_alerting_2026_05_08.md`](risk_simulations_limits_alerting_2026_05_08.md) —
    per-client risk envelope + breach-history feeds reporting; reporting PnL feeds risk-simulation capital-at-risk.
  - Composes with
    [`api_keys_wallets_accounts_readiness_2026_05_08.md`](api_keys_wallets_accounts_readiness_2026_05_08.md) —
    per-client API-key intake (B4 external-strategy path) consumes credential discipline declared there.
- **Estimated scope**: TBD — audit pass first.

## Plan extraction record

(Empty — fills when the plan ships.)
