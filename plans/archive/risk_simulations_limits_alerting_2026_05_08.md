---
doc_type: plan
title: risk-simulations-limits-alerting
summary: Risk monitor vs risk simulations vs risk alerts vs pre-flight risk checks — wire-up across the system, dimensions
  (venue / account / strategy / client), per instrument-type + strategy-family / archetype, consequences of failure (block
  vs monitor vs test). Owner of the canonical circuit-breaker rule taxonomy + the mock-data-as-stress-test surface that
  downstream plans consume.
status: plan-spawned
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, execution-service, strategy-service, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/alerting_service_live_rules_2026_05_07.md,
    plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md,
    plans/questions/wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md,
    plans/questions/client_reporting_pnl_attribution_2026_05_08.md,
    plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md,
    plans/questions/defi_readiness_catalogue_2026_05_08.md,
    plans/active/issues/missing_question_docs_orphan_references_2026_05_10.md,
  ]
created: 2026-05-08
type: question
plan_spawned: 2026-05-10
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-08
spawned_plan: plans/active/risk_simulations_limits_alerting_2026_05_10.md
related_codex: [/codex/04-architecture/kill-switch-circuit-breaker.md, /codex/04-architecture/separation-of-concerns.md]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Risk monitor + risk simulations + risk alerts + pre-flight risk checks — end-to-end wire-up question

> **🟢 SSOT-RECONCILIATION CLOSED — Framing 1 picked by operator 2026-05-10.** Spawned plan
> [`plans/active/risk_simulations_limits_alerting_2026_05_10.md`](../active/risk_simulations_limits_alerting_2026_05_10.md)
> § "§ 7 SSOT reconciliation seam (Framing 1)" canonicalises `RiskRuleConsequence` (BLOCK / SCALE_DOWN / MONITOR /
> TEST_ONLY) as a NEW abstraction at Layer 2 of the existing 4-layer risk-gates model — composing with all 5 canonical
> workspace SSOTs (4-layer risk-gates / 3 circuit-breaker actions / 5 kill-switch trigger types / ErrorAction /
> AlertCode 39→43 closed set). Block D body of THIS question doc has DRAFT-INFERENCE framing superseded by the spawned
> plan's seam diagram — read the spawned plan section as canonical, not Block D here. Issue
> [`risk_rule_taxonomy_ssot_reconciliation_2026_05_10.md`](../active/issues/risk_rule_taxonomy_ssot_reconciliation_2026_05_10.md)
> closed.

> **Reconstruction note (2026-05-10).** The original draft of this doc (created 2026-05-08) was lost — never committed
>
> - erased from disk during parallel-agent activity. Re-spawned per
>   [`missing_question_docs_orphan_references_2026_05_10.md`](../active/issues/missing_question_docs_orphan_references_2026_05_10.md)
>   disposition (a). **Lower-fidelity reconstruction than the sibling re-spawn**: original block-by-block content was
>   not preserved in conversation context. Body synthesized from (a) the original 2026-05-08 README backlog one-liner;
>   (b) orphan-reference citations from 8 sibling docs (which name this doc as owner of the circuit-breaker rule
>   taxonomy + the mock-data-as-stress-test surface); (c) workspace SSOTs in
>   `/codex/04-architecture/kill-switch-circuit-breaker.md`
> - master plan Group F items 17-22. **Operator should review for framing drift vs original intent before audit pass
>   consumes this as canonical.**

## Intent

The system has at least 4 distinct risk-flavored surfaces today, and they're often conflated even though each has a
different audience, cadence, blast-radius-on-failure, and home in the architecture:

1. **Risk monitor** — continuous, post-trade observation of position + exposure + capital + leverage + concentration per
   (venue / account / strategy / client / archetype). Read-only; doesn't intervene. Lives in risk-and-exposure-service.
   Output: real-time dashboards + persisted exposure history for reporting and reconciliation. Failure mode: silent gap
   in observation surface (blind spot).
2. **Risk simulations** — forward-looking stress + scenario evaluation. Two flavors:
   - **Mock-data-as-stress-test** — synthetic price shocks / vol spikes / correlation breakdowns / venue outages applied
     to current positions, run on demand or on a cron, output is "if scenario X happened now, our P&L would be Y, our
     liquidation cascade would unwind in Z venues." See sibling
     [`paper_vs_live_workflow_maturity_2026_05_08.md`](paper_vs_live_workflow_maturity_2026_05_08.md) for the mock-data
     carve-out.
   - **Real-state-bundle-simulation** — pre-flight Tenderly bundle simulation for DeFi (and equivalent for CeFi /
     prediction): given the EXACT pending instruction + current chain/venue state, simulate the full bundle and check
     reverts / slippage / margin impact. See sibling
     [`defi_readiness_catalogue_2026_05_08.md`](defi_readiness_catalogue_2026_05_08.md) Block C5 for Tenderly hookups.
3. **Risk alerts** — notifications when monitored quantities cross thresholds (operator-facing, sometimes
   client-facing). Routing through `alerting_service_live_rules_2026_05_07.md`. Failure mode: alert flood (cry wolf) or
   alert silence (missed breach).
4. **Pre-flight risk checks** — at the execution-service boundary, before sending an instruction to a venue / chain /
   bookmaker, evaluate: does this instruction violate a hard limit (per-archetype capital cap, per-venue concentration
   cap, per-client risk envelope, kill-switch state)? If yes → BLOCK. If borderline → MONITOR (allow + flag). If unknown
   surface → TEST (route to paper / matching engine instead). Failure mode: bypass (instruction reaches venue despite a
   violation), or false-positive (legitimate instruction blocked).

The operator's question collapses to: **for each of the 4 surfaces, is it actually wired today across every dimension
the system supports — or are there silent blind spots?** The dimensions:

- **(venue / account / strategy / client)** — exposure and limits at every aggregation level.
- **(instrument-type)** — perp vs spot vs option vs future vs LST vs LP-share vs prediction-market-share vs sports-bet
  have different risk shapes.
- **(strategy-family / archetype)** — the 50+ archetypes have different risk envelopes by design (a high-leverage
  funding-arb vs a delta-neutral basis carry vs a sports market-make all need different limits).
- **(failure consequence)** — for each rule that fires, the action is one of {block / monitor / test}. The taxonomy must
  be explicit per-rule, not implicit.

This doc is the canonical SSOT for the circuit-breaker rule taxonomy. Downstream plans consume it as upstream owner.

## Question

### Block A — Risk monitor (post-trade observation)

A1. **What's the canonical risk-monitor service today?** Is risk-and-exposure-service the SSOT, or are
position-balance-monitor + risk-and-exposure-service overlapping? What's the data flow (venue fill events → position
update → exposure recompute → monitor dashboard write)?

A2. **Per-dimension exposure tracking** — for each of {venue, account, strategy, client, archetype, asset_group, chain,
instrument_type, instrument}, is real-time aggregated exposure tracked? At what cadence (per-tick / per-minute /
per-hour)? Where is it stored (in-memory only / Firestore / a time-series DB)? Is historical exposure replayable for
audit + reconciliation?

A3. **Per-client risk envelope read-side** — sibling
[`wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md`](wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md)
Block A5 owns the per-client risk envelope as data. The risk monitor must consume it: for each (client, share-class)
tuple, what's the live utilisation vs limit, breach history, time-to-breach trajectory? Is this surface wired today?

A4. **Cross-venue + cross-chain exposure aggregation** — for an archetype that spans 2+ venues (basis carry on Bybit
spot + Hyperliquid perp; arb across Polymarket + Kalshi), exposure must be aggregated across the boundary, not siloed
per-venue. Wired?

A5. **Reconciliation drift as a risk signal** — when the internal ledger diverges from venue ground-truth by ≥ X bps,
that itself is a risk monitor input (the system's view of position is wrong). Per asset_group + per venue, is this drift
surfaced as a risk metric or only as an alerting trigger?

### Block B — Risk simulations

B1. **Mock-data-as-stress-test surface** — does a stress-test scenario library exist as code (UAC `StressScenario`
registry?) or only as ad-hoc operator-run scripts? What scenarios are catalogued (BTC -20% / ETH -30% / DeFi protocol
exploit / venue suspension / stablecoin de-peg / LST de-peg / funding rate spike / vol spike / correlation breakdown /
combined cascade)? Per-archetype tail-risk decomposition (slashing for staking archetypes, protocol exploit for DeFi-LP
archetypes, FTX-style venue suspension for CeFi archetypes)?

B2. **Stress-test runner** — is there a service or job that, given (current positions, scenario), produces (PnL impact,
liquidation cascade, margin call requirement, time-to-recover)? Cadence (ad-hoc / nightly cron / on-trigger when
volatility regime changes)? Output (queryable history vs ephemeral)?

B3. **Tenderly bundle pre-flight simulation** — see sibling
[`defi_readiness_catalogue_2026_05_08.md`](defi_readiness_catalogue_2026_05_08.md) Block C5 for the chain-side
mechanics. From the risk-simulation side: is Tenderly bundle pre-flight gating live order placement (BLOCK if simulated
bundle reverts) or advisory-only? Per-archetype simulation budget per day given Tenderly rate limits? Equivalent
surfaces for CeFi (paper-fill via matching engine?) / sports (??) / prediction (??).

B4. **Scenario simulation cadence + integration** — for "what if" exploration during operator decision-making (e.g. "if
I increase carry_staked_basis allocation by 2x, what's the marginal liquidation-cascade risk?"), is there an
operator-facing simulation tool or is this implicit-knowledge-only? Live in unified-trading-system-ui or separate?

B5. **Mock-data carve-out vs real-state simulation** — per the paper-vs-live-workflow_maturity sibling, mock-data
risk-sim is explicitly OUT of paper scope. Real-state simulation (Tenderly + matching engine) IS in paper scope. Is this
separation enforced as code (different code paths, no shared state, no risk of mock-data leaking into live decisions),
or is it convention-only?

### Block C — Risk alerts

C1. **Alert taxonomy** — what's the canonical AlertCode SSOT? Per
[`alerting_service_live_rules_2026_05_07.md`](../active/alerting_service_live_rules_2026_05_07.md) — does the risk-alert
subset live as code in UAC (`AlertCode` enum or equivalent), or scattered per-rule? Per-rule severity (INFO / WARN /
CRITICAL) + routing (Telegram operator / Firebase client / both / silent)?

C2. **Per-dimension alert rules** — alerts by (venue / account / strategy / client / archetype) — the rules engine must
support compound predicates ("breach if client_C and archetype_X exceeds Y% of envelope") + threshold types (absolute /
relative / time-window / rate-of-change). Wired today, or simple per-metric thresholds only?

C3. **Alert dedup + escalation** — preventing alert flood when a single underlying event triggers 50 cascading rules.
Time-windowed dedup, priority-based suppression, escalation if not acknowledged within X minutes. Wired or implicit?

C4. **Client-facing alert routing** — distinct channel for client-facing alerts (NAV drawdown breach, daily PnL
threshold, share-class redemption gate triggered) vs operator-facing alerts (reconciliation drift, venue API outage,
kill-switch armed). Per-client subscription preferences (which alert types the client wants).

C5. **Alert history + audit** — is every alert event persisted (timestamp, rule, actor-receiving, ack timestamp)? For
regulatory + post-incident audit per the wallet_treasury Block F3 compliance surface.

### Block D — Pre-flight risk checks (execution-boundary)

D1. **Where in execution-service is the pre-flight check?** Per CLAUDE.md DeFi Execution Architecture, every adapter
runs `connect()` + venue-error classification. Is there a pre-flight risk gate BETWEEN strategy-service emission and
execution-service venue submission, or is the gate inside execution-service per-adapter? Single SSOT for the pre-flight
rule set, or per-asset_group / per-adapter divergence?

D2. **Per-rule action taxonomy {BLOCK / MONITOR / TEST}** — the canonical taxonomy this doc owns. For each circuit-
breaker rule, the action MUST be explicit per-rule:

- **BLOCK** — instruction never reaches venue; alert raised; rule violation logged; client-attributable order is
  refunded.
- **MONITOR** — instruction proceeds; flag persisted with the order metadata; post-trade reporting attributes the flag.
- **TEST** — instruction routed to paper / matching engine instead of live venue; output captured for analysis;
  client-attributable economics are simulated, not real.

  Is this taxonomy declared as data (UAC `CircuitBreakerAction` enum)? Per-rule action declared per-rule? Default action
  for unspecified rules (default-BLOCK is fail-loud per workspace rule)?

D3. **Per-archetype × per-rule activation** — not every rule applies to every archetype (a sports-betting archetype
doesn't need a "perp funding rate spike" rule; a DeFi-LP archetype doesn't need a "venue maintenance margin tier" rule).
Is the per-archetype × per-rule activation matrix declared as data, or implicit-knowledge?

D4. **Per-client × per-share-class × per-rule activation** — different share-classes have different risk envelopes
(retail blocks high-leverage rules at lower threshold; institutional permits broader). Is this driven by the
share-class-allowability matrix from sibling
[`wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md`](wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md)
Block C2, or is there a parallel per-share-class rule registry?

D5. **Kill-switch integration** — `/codex/04-architecture/kill-switch-circuit-breaker.md` is the workspace SSOT. When
the kill-switch is armed (manual operator trigger, automated trigger from breach cascade, dead-man's-switch from
heartbeat loss), pre-flight goes default-BLOCK across all rules. Is the kill-switch read-state available at
execution-service pre-flight time, with sub-second freshness?

D6. **Pre-flight failure mode handling** — when the pre-flight rule engine itself errors (rule registry unreachable,
risk-and-exposure-service down, share-class data stale), what's the default? Fail-open (allow instructions through —
risk of unconstrained execution) or fail-closed (BLOCK all instructions — risk of paralysis during transient
infrastructure outages)? Per-archetype configurable, or system-wide?

### Block E — Cross-cutting integration

E1. **Risk-stack feeds into reporting** — per sibling
[`client_reporting_pnl_attribution_2026_05_08.md`](client_reporting_pnl_attribution_2026_05_08.md) Block C1 + here:
per-client risk utilisation + breach history feeds per-client reporting. Shared per-client data model?

E2. **DART manual-trade gate** — DART (master plan Group G item 23) is the operator manual-trade surface. Manual trades
MUST flow through the same pre-flight risk checks as automated trades, otherwise the operator can bypass risk
discipline. Wired?

E3. **Backtest-vs-live risk parity** — per the workspace "Live = batch" SSOT, risk rules + circuit-breaker actions
should evaluate identically against backtest fills + live fills (different fill source, same rule engine + same action).
Is this enforced or are there backtest-mode bypasses for some rules?

E4. **External-strategy risk integration** — per the wallet_treasury sibling Block A4 (external clients providing their
own venue API keys + strategy declarations), do external-strategy fills flow through OUR pre-flight risk gate, or are
they trusted to have their own? If trusted: how do we attribute risk-induced losses cleanly between
"client-strategy-decision risk" vs "infrastructure-induced risk"?

E5. **Counterparty risk surface** — sibling wallet_treasury Block B5 owns per-counterparty exposure tracking + caps.
Risk monitor (Block A here) consumes it; pre-flight (Block D here) enforces it. Wired across the seam?

## What "answered" looks like

- A canonical plan exists in `plans/active/risk_simulations_limits_alerting_<date>.md` (or splits into 2-4 sub-plans per
  the 4 surfaces) covering each of:
  - **Risk monitor** — per-dimension exposure tracking + per-client envelope read-side + reconciliation-drift signal.
  - **Risk simulations** — `StressScenario` registry + stress-test runner + Tenderly bundle pre-flight wiring +
    real-state-vs-mock-data carve-out enforcement.
  - **Risk alerts** — `AlertCode` SSOT + compound rule predicates + dedup/escalation + client-vs-operator routing +
    audit history.
  - **Pre-flight risk checks** — `CircuitBreakerAction` enum + per-archetype × per-rule activation matrix + per-client ×
    per-share-class envelope binding + kill-switch read-state + fail-mode default.
  - **Cross-cutting** — risk-feeds-reporting + DART pre-flight + backtest-live parity + external-strategy-risk-seam +
    counterparty exposure enforcement.

- Codex SSOT(s) describe:
  - **Risk-stack architecture** (`/codex/04-architecture/risk-stack-monitor-simulation-alert-preflight.md`) — the 4
    surfaces + their interactions + the canonical action taxonomy.
  - **Circuit-breaker rule taxonomy** (extends `/codex/04-architecture/kill-switch-circuit-breaker.md`) — per-rule
    {BLOCK / MONITOR / TEST} declared as data + per-archetype × per-share-class activation matrix.
  - **Stress scenario library** (`/codex/04-architecture/stress-scenario-library.md`) — every catalogued scenario +
    per-archetype tail-risk decomposition + cadence + output schema.
  - **UPDATE master plan Group F** items 17-22 — risk-stack readiness rows per archetype.

- Real-data evidence:
  - At least one circuit-breaker rule has fired in production (or testnet) and BLOCKED a real instruction with full
    audit trail.
  - At least one stress-test run has produced output that the operator acted on (rebalance / hedge / capacity cut).
  - At least one Tenderly bundle pre-flight has rejected a deliberately-broken bundle (synthetic test).
  - At least one alert dedup window has prevented a flood from a real triggering event.

- Service-readiness checklist: per master plan Group F items 17 + 21 + 22 (paper-trade smoke, kill-switch + alerting,
  auto-recovery), all gates green for live-DeFi cutover. Per-share-class × per-archetype risk envelope
  deferred-post-cutover with named successor plan per Plan Archival HARD RULE.

## Audit findings (to be filled by audit pass)

For each sub-question in Blocks A-E, fill:

- **Code state**: file:line citations across risk-and-exposure-service + position-balance-monitor + alerting-service +
  execution-service + UAC (AlertCode / CircuitBreakerAction / StressScenario / RiskRule registries)
  - DART surface + kill-switch wiring.
- **Data state**: how many rules registered per surface; per-archetype × per-rule matrix coverage; alert volume + dedup
  ratio over last 30 days; stress-scenario library size + last-run timestamps; Tenderly simulation budget + burn-rate.
- **Run state**: any rule fired in production; any stress-test run consumed by operator decision; any Tenderly
  pre-flight rejection; any kill-switch armed event.
- **Codex state**: do the listed codex SSOTs exist; drift vs current code; gaps.
- **Gap analysis**: per the master matrix (4 surfaces × N rules × M archetypes × K share-classes × J venues), where are
  the systemic gaps; what's blocking May-23; deferred-post-cutover with named successor plan.

## Operator notes / answers

(Empty — to be filled during iteration. **Note for operator: the pre-reconstruction original may have had specific
risk-limit numbers, scenario library entries, or rule taxonomies that this reconstruction lacks. If you have any notes,
please add them here so the audit pass starts from your latest thinking, not just the structural framing.**)

## Iteration log

| Date       | Author              | Change                                                                                                                                                                                                                                                                                                                 |
| ---------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-08 | ikenna + main agent | Initial draft created (lost — never committed; see iteration entry below)                                                                                                                                                                                                                                              |
| 2026-05-10 | main agent          | Re-spawned after the original 2026-05-08 draft was confirmed lost. **Lower-fidelity reconstruction**: original block-by-block content was not preserved in conversation context. Body synthesized from README backlog one-liner + 8 orphan-citing files + workspace SSOTs. Operator review for framing drift required. |

## Plan-shape decisions (filled before plan extraction)

- **Plan name + path**: TBD — likely splits into 4 plans (one per surface):
  - `plans/active/risk_monitor_per_dimension_exposure_<date>.md`
  - `plans/active/risk_simulations_stress_scenarios_tenderly_<date>.md`
  - `plans/active/risk_alerts_taxonomy_dedup_routing_<date>.md`
  - `plans/active/preflight_risk_checks_circuit_breaker_taxonomy_<date>.md`
- **Plan type**: mixed (code + infra + business + operational)
- **Owner side**: TBD — likely ikenna for design (action taxonomy + per-archetype × per-share-class activation + fail
  mode policy + kill-switch integration design) + harsh for implementation (per-rule wiring + dashboard surface + alert
  routing + Tenderly pre-flight glue)
- **Codex SSOTs touched**: per "What answered looks like" — 3 NEW + 1 UPDATE
- **Cross-plan dependencies**:
  - Composes with [`alerting_service_live_rules_2026_05_07.md`](../active/alerting_service_live_rules_2026_05_07.md) —
    alert routing layer this question doc consumes.
  - Composes with
    [`simulation_scenarios_topology_price_shocks_2026_05_09.md`](../active/simulation_scenarios_topology_price_shocks_2026_05_09.md)
    — that plan CONSUMES the circuit-breaker rule taxonomy this doc owns.
  - Composes with
    [`wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md`](wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md)
    Block A5 + C2 — per-client risk envelope + per-share-class × per-archetype matrix is shared data.
  - Composes with [`client_reporting_pnl_attribution_2026_05_08.md`](client_reporting_pnl_attribution_2026_05_08.md) —
    per-client risk utilisation + breach history feeds reporting.
  - Composes with [`paper_vs_live_workflow_maturity_2026_05_08.md`](paper_vs_live_workflow_maturity_2026_05_08.md) —
    mock-data stress-test carve-out vs real-state simulation separation.
  - Composes with [`defi_readiness_catalogue_2026_05_08.md`](defi_readiness_catalogue_2026_05_08.md) Block C5 — Tenderly
    bundle pre-flight wiring.
- **Estimated scope**: TBD — audit pass first; expect ≥ 4 plans × 5-10 AI-day each.

## Plan extraction record

(Empty — fills when the plan ships.)
