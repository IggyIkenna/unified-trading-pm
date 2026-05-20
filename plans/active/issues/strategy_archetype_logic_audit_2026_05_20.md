---
title: Strategy archetype logic audit — separate from data-sanity mega audit
created: 2026-05-20
author: ikenna-slot-1 main
locked_by: live-defi-rollout
locked_since: 2026-05-20
priority: P0
status:
  ACKED — operator authorised 2026-05-20 round 5 to run TONIGHT in parallel with strategy/ml consolidation tail (Phase
  11 cleanup, mostly done already). Requires **Opus 4.7 (1M context)** — cross-archetype + cross-codebase scope demands
  the full graph in one session per `codex/06-coding-standards/model-tier-selection.md` opus-required tier.
parent_epic: strategy_and_dart_master_2026_05_07.md
related_plans:
  - mega_audit_and_plan_beefup_progression_2026_05_20.md
  - trading_agent_service_architecture_unlock_2026_05_22.md
estimate_class: research
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 14.4
---

## Why this is a separate audit from the mega audit

The mega audit (`mega_audit_and_plan_beefup_progression_2026_05_20.md`) focuses on **data sanity** — contract pairs
between services, manifest correctness, expected_coverage, etc. It does NOT audit the strategy logic itself.

This issue captures the **strategy archetype logic audit** that must follow. The two are sequenced:

1. Mega audit (Phase A → B → C → D) lands first — gives clean data substrate
2. Strategy archetype audit runs against the now-clean substrate
3. Trading-agent-service architecture unlock (`trading_agent_service_architecture_unlock_2026_05_22.md`) gets the
   directive/PnL contracts wired
4. Strategy archetype audit findings flow into a Phase 2 (post-cutover) operational plan for the closed-loop allocator

## Audit dimensions — per archetype

For EVERY archetype in `codex/09-strategy/architecture-v2/archetypes/` (and any in
`strategy_service/strategy_service/engine/strategies/v2/`), produce a 4-dim audit row:

### 1. WHAT + WHERE

- Canonical archetype name + alpha hypothesis (one paragraph)
- File path (strategy-service implementation)
- Codex doc path (the archetype's design SSOT)
- Active / paper / shadow / scaffolded / archived status

### 2. DATA INPUTS

- Per-feature dependency (which features-service streams consumed)
- Per-MTDS data_type dependency (raw market data needs)
- Per-IS reference dependency (instrument metadata needs)
- Required vs optional inputs (graceful degradation behavior)
- `available_at` discipline (does it respect point-in-time? backtest-safe?)
- Per-input freshness threshold (when is data too stale to act on?)

### 3. PnL + BALANCES + ATTRIBUTION

- PnL calculation: realized + unrealized, per-leg + per-pair
- Balance tracking: how positions are reconciled with venue/wallet state
- Attribution rules: how PnL is split when multi-leg / multi-venue / multi-allocation
- Emission contract: does the archetype publish PnL on the new `strategy_pnl_stream` shape (per trading-agent unlock
  plan)?
- Drift detection: does internal balance state get reconciled against on-chain / venue state? Cadence?

### 4. CAPITAL HANDLING

- **Fund-style** (pooled capital across all clients):
  - How is gross exposure capped?
  - How are entry/exit timed to minimize market impact across pool?
  - How are realized PnL distributions allocated to client units?
- **SMA-style** (per-client segregated accounts):
  - How is per-client capital tracked?
  - How are orders split across accounts (proportional / threshold / sequential)?
  - How are fees + slippage attributed per-account?
- **Treasury flows**:
  - Deposit handling (how does new capital enter the strategy?)
  - Withdrawal handling (how is capital released back?)
  - Rebalance flows (how are inter-archetype allocations moved?)
  - Fee + funding flows (where does fee revenue / funding payment land?)

### 5. UNIVERSE ENUMERATION

- At decision time T, what's the set of viable instrument-tuples?
- Multi-venue example (funding rate arb): list of CEX venues × set of symbols = candidate pairs
- Multi-archetype universe: what's the cross-product across LST pools × CEX perp venues for staked basis?
- Filter rules: liquidity floor, freshness floor, event filter (depeg, funding cap, etc.)
- Is the universe enumeration WHERE? — in features-service (per the cross-asset decision) or in the strategy itself?

### 6. SIZING + RISK

- Sizing rule: Kelly / fixed-frac / risk-parity / volatility-targeted / equal-weight
- Per-leg size derivation (how is the leg ratio computed for multi-leg?)
- Max position size + max gross exposure
- Per-trade risk budget (% of capital at risk per trade)
- Stop-loss / take-profit logic if any
- Correlation aware? (do positions across archetypes adjust for cross-correlation?)

### 7. REBALANCING + LIFECYCLE

- Entry signal + entry cadence
- Hold period (continuous re-evaluation vs fixed-tenure)
- Rebalance triggers (drift % / time / regime change / volatility breach)
- Unwind triggers (PnL exit / stop / archetype turn-off via directive)
- Roll handling (for futures + perp expiries)

### 8. NEUTRALITY + DIRECTIONALITY

- Delta neutrality: how is it computed + maintained?
- Asset-class neutrality: is the archetype neutral across crypto / FX / commodity / equity?
- Direction: long-only / short-only / market-neutral / dynamic?
- Hedge leg specification: who chooses the hedge venue + hedge instrument?
- Beta-to-market / beta-to-asset-class: what's the residual?

### 9. VENUE RESTRICTIONS (operator focus 2026-05-20 round 6 — "the math is easy")

- Per-venue allow-list / deny-list per client_id (UK clients can't access Extended Starknet; Cayman clients can; etc.)
- Per-venue jurisdiction tags + auto-enforcement at order-construction time (UAC `client_funds_isolation` rule extends)
- Per-venue MAX position limit + MAX gross exposure
- Per-venue trading hours overlay (which archetypes can run during which venue's session?)
- Per-venue credential health gate (if API key revoked or rate-limited mid-day, what happens?)
- Per-(venue, instrument) blacklist (e.g. delisted, paused, low-liquidity)
- **Test**: what does the archetype do when 2/3 venues for a multi-venue arb are restricted for the active client?

### 10. COLLATERAL MANAGEMENT (operator focus)

- Per-venue collateral type registry (stablecoin / native / LST-as-collateral)
- Collateral haircut + LTV per venue (matches venue's actual risk params)
- Cross-margin vs isolated-margin choice per archetype × venue
- Collateral substitution (when can stETH replace ETH as collateral?)
- Collateral rebalancing triggers (LTV drift > X% → top up / reduce)
- DeFi-specific: liquidation health factor monitoring (Aave / Compound `getUserAccountData` reads)
- CeFi-specific: maintenance margin proximity alerts
- **Test**: at decision time, does the archetype know its current collateral position per venue + can it size correctly?

### 11. LIQUIDATION MANAGEMENT (operator focus)

- Per-archetype liquidation distance threshold (health factor ≤ X.X triggers action)
- Pre-liquidation action: deleverage / top-up collateral / unwind position
- Liquidation cascade detection: if one leg liquidates, what happens to the hedge leg?
- Mark-price vs index-price awareness (perp venues liquidate on mark; on-chain liquidates on oracle)
- Oracle freshness gate (Chainlink heartbeat < N min for the archetype's collateral assets)
- Per-venue liquidation fee + skip risk
- Recursive-loop archetypes: per-iteration liquidation health calc (e.g. Aave looping)
- **Test**: under flash-crash scenario, what's the archetype's pre-liquidation playbook + does the directive bus get the
  right signals fast enough?

### 12. CROSS-VENUE TRANSFERS (operator focus)

- Permitted transfer pairs per client (intra-client only per CLAUDE.md `Client funds isolation` HARD RULE)
- Transfer-window awareness (e.g. CEX withdrawal blackouts on Mondays UTC)
- Bridge-time tolerance per chain (Ethereum withdraw 7d challenge period, Arbitrum 7d, Optimism 7d, etc.)
- Stablecoin vs native asset transfer-cost calculus (USDC bridge vs ETH bridge)
- Failed-transfer reconciler (transfer initiated but didn't arrive within window → alert + manual ack)
- Sub-account move logic (CEFI internal: Binance spot → Binance futures sub-account)
- Per-leg dependency: if archetype needs cross-venue transfer to size correctly, what's the fallback if transfer fails?
- **Test**: a multi-venue staked-basis archetype needs to move stETH from Lido custody to a CEX as collateral — does the
  cross-venue transfer path exist + is it auditable?

### 13. ALLOCATION-BASED REBALANCING (operator focus — "most of the focus")

- Per-archetype target allocation % (of total client capital)
- Cross-archetype rebalance trigger: drift % / time / regime
- Allocation source-of-truth: `portfolio_allocator` (strategy-service)? `client_share_classes`? both?
- Per-(client, archetype) override (a client opts out of `recursive_lending` but in for `staked_basis`)
- Closed-loop feedback: realised PnL flows back to update allocations? Cadence?
- Cross-asset-group allocation (cefi 50% / defi 30% / sports 20% per client) — how surfaced in deployment?
- Forced-deallocation when an archetype is paused (capital returns to cash; what's the holding venue?)
- **Test**: when operator adds a new client mid-day with target allocation (40% cefi, 60% defi), does the allocator
  detect + rebalance without manual intervention?

### 14. DEPLOYMENT TOPOLOGY — DYNAMIC CONFIG + ACCOUNTS / CLIENTS (operator focus)

- Adding a new client mid-day: which configs hot-reload? Which require VM restart?
- Adding a new account (sub-account) to existing client: account discovery path + credential injection
- Removing a client: graceful unwind (don't strand positions); position liquidation pathway
- Removing an account: ditto
- Adding a new venue: config hot-reload OR VM redeploy?
- Per-archetype enable/disable from operator UI (directive bus): cadence to take effect
- Per-(archetype, asset_group) enable/disable (e.g. pause arb_price_dispersion on DeFi but keep CeFi running)
- Config drift detection: if `cloud-providers.yaml` or `client_share_classes.yaml` changes, do running VMs reload?
- Health-API endpoint per service reflects current client/account count + per-archetype state
- **Test**: with 3 archetypes running on 2 clients, operator adds a 3rd client + a new archetype simultaneously — does
  deployment topology absorb without restart?

## Audit deliverables (per archetype + per cross-cutting dimension)

1. **Design vs implementation gap table**: per dimension (1-14), what does the design SSOT say vs what does the code do?
   Surface every drift.
2. **Per-dimension risk register**: list every "missing handler" / "wrong default" / "silent fallback" the archetype has
   that would surface as a P0 in live trading.
3. **R-items for operator delegation**: each gap → a remediation item with target slot + estimated effort. Matches the
   mega-audit § 6 delegation SSOT format.
4. **Pre-live trading gate**: any gap in dimensions 9-14 (venue restrictions / collateral / liquidation / cross-venue
   transfer / allocation rebalancing / deployment topology) is **P0 cutover-blocking** for the affected archetype.

## Archetype inventory (to be confirmed during audit Phase 0)

Provisional list from codex + strategy-service:

| Archetype                                 | Asset group(s)          | Status      | Live mode by 2026-05-23? |
| ----------------------------------------- | ----------------------- | ----------- | ------------------------ |
| `carry_staked_basis`                      | DeFi + CeFi (hedge leg) | live target | YES                      |
| `arbitrage_price_dispersion`              | DeFi or CeFi or cross   | live target | YES                      |
| Multi-venue funding rate arb              | CeFi (cross-venue)      | scaffolded? | post-cutover             |
| Calendar / term basis                     | CeFi futures            | scaffolded? | post-cutover             |
| Stat arb / pairs (CeFi)                   | CeFi                    | scaffolded? | post-cutover             |
| Sports arb (e.g. inter-book arb)          | Sports                  | scaffolded? | post-cutover             |
| Sports value (model edge)                 | Sports                  | scaffolded? | post-cutover             |
| Polymarket / Kalshi arb                   | Prediction              | scaffolded? | post-cutover             |
| TradFi carry (e.g. VX term structure)     | TradFi                  | scaffolded? | post-cutover             |
| TradFi vol (e.g. variance / VIX)          | TradFi                  | scaffolded? | post-cutover             |
| TradFi momentum / trend                   | TradFi                  | scaffolded? | post-cutover             |
| LST yield arb (DeFi-internal)             | DeFi                    | scaffolded? | post-cutover             |
| Lending rate arb (Aave / Compound / etc.) | DeFi                    | scaffolded? | post-cutover             |

Phase 0 of this audit = enumerate the actual inventory + confirm status. Codex `architecture-v2/archetypes/` directory
is the SSOT.

## Cross-cutting questions

Beyond per-archetype audits, surface workspace-wide patterns:

- **Universe-enumeration consistency**: do all multi-venue archetypes get their universe from features-service (per the
  cross-asset decision)? Any outliers re-deriving from raw MTDS / IS?
- **PnL emission uniformity**: do all archetypes use the same emission shape, or do they roll their own?
- **Sizing rule diversity**: how many distinct sizing implementations exist? Any duplication? Any that should be
  promoted to a shared lib?
- **Attribution split logic**: is per-leg PnL attribution implemented uniformly, or are there inconsistencies?
- **Fund vs SMA handling**: is there a single shared client-split layer, or does each archetype implement its own?
- **Treasury flow contract**: is there a uniform "capital event" interface (deposit/withdraw/rebalance) consumed by
  every archetype?

## Audit deliverables

### Per-archetype audit doc (one per archetype, ~13 total)

- Location: `plans/audit/archetypes/<archetype_name>_2026_05_2X.md`
- Mirrors the mega-audit C-audit shape (4-dimensional matrix per archetype)
- ~1.5-2 calibrated AI-days each

### Cross-cutting findings audit doc (one)

- Location: `plans/audit/cross_cutting_strategy_logic_findings_2026_05_2X.md`
- Workspace-wide patterns + outlier flags + duplication candidates
- ~2 calibrated AI-days

### Beefed-up actionable plan (one)

- Location: `plans/active/strategy_archetype_consolidation_post_cutover_2026_05_2X.md`
- Absorbs per-archetype audit findings + cross-cutting recommendations
- Phase-D-equivalent for strategy logic (mirrors mega audit's Phase D plan beef-up shape)

## Sequencing — when this audit can run

**Blocked-on**:

1. **Mega audit Phase A (diagnostics)** lands first — gives clean data substrate. Strategy logic audit can't separate
   strategy bugs from data bugs without this.
2. **Mega audit Phase C6 (features→strategy contract audit)** lands — surfaces the per-pair viability + pricing
   ownership contract this audit consumes.
3. **Trading-agent unlock plan Phase 1 (May-23 architecture)** lands — the `strategy_pnl_stream` emission shape is the
   canonical PnL contract the strategy audit uses for dim-3.

**Unblocked-by** (once above land):

- Strategy audit can spawn 13 parallel agents (one per archetype), each filling its audit doc against the now-locked
  contracts.
- Cross-cutting findings agent runs after the 13 land, consolidating.
- Beefed-up plan written by ikenna (operator judgment on which consolidations are worth doing).

## Foundation-gate alignment

This audit is **layer 6** (strategy + execution) per
`codex/11-project-management/foundation-completion-gate-discipline.md`. Prereqs:

- Layer 1 GREEN (IS hardening — C0/C1/C2/C3 audits)
- Layer 5 GREEN (features → strategy contract — C6 audit)
- Layer 7 architecture unlocked (trading-agent unlock plan Phase 1)

When prereqs green, this audit can run safely. Until then, surfacing strategy bugs would conflate with upstream-data
bugs.

## Out of scope (explicit)

- Strategy DEPLOYMENT logic (already in strategy_and_dart_master epic)
- Allocator service implementation (covered by trading-agent unlock plan Phase 1 scaffold + Phase 2 operational)
- Backtest infrastructure (this audit USES backtest results but doesn't build them)
- New archetype design (this audits EXISTING archetypes; new alpha hypotheses are separate work)
- Execution-service logic (the strategy → execution boundary is covered by mega audit C7)
- Live trading risk limits (operator-set; not strategy-internal)

## Ack triggers (when this issue archives)

Per `codex/11-project-management/issue-doc-lifecycle.md`, this issue archives when:

1. Per-archetype audit docs (13) land in `plans/audit/archetypes/`
2. Cross-cutting findings doc lands
3. The beefed-up `strategy_archetype_consolidation_post_cutover` plan lands in `plans/active/`
4. Findings are absorbed into either Phase 2 trading-agent ops plan OR per-archetype plans
