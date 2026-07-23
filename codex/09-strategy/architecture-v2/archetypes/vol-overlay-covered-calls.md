---
doc_type: codex-ssot
title: "Archetype: `VOL_OVERLAY_COVERED_CALLS`"
summary:
  "Archetype spec for `VOL_OVERLAY_COVERED_CALLS` — writes 15-25 delta OTM calls against an existing delta-1 long to
  harvest premium and offset carry, rolling up on rally; covered-only, never naked; Deribit/OKX."
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, covered-calls, overlay, income]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-overlay-protective-put.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-straddle.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-continuous.md,
    ../families/vol-trading.md,
  ]
created: 2026-05-19
authoritative_for: ["VOL_OVERLAY_COVERED_CALLS archetype spec"]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-overlay-protective-put.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-synthetic-delta.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: VOL_OVERLAY_COVERED_CALLS
family: VOL_TRADING
venue_universe: [DERIBIT, OKX_OPTIONS]
topology_requirements:
  isolation: { execution-service: isolated }
  co_location: []
  latency_budget_ms: 300
  min_sla_tier: standard
---

# Archetype: `VOL_OVERLAY_COVERED_CALLS`

> **Family:** [Vol Trading](../families/vol-trading.md) **Settlement model:** Expiry-driven — calls written per expiry
> cycle; position rewritten at expiry or rolled up on rally. **Code module (target):**
> `strategy-service/engine/strategies/v2/vol_trading/vol_overlay_covered_calls_engine.py`

## What it does

Systematically writes OTM calls against existing delta-1 long positions (spot or perp) to generate premium income and
reduce effective carry costs. The overlay sells calls at 15-25 delta (roughly 1-2 standard deviations OTM) each expiry
cycle, collecting time decay as the primary P&L source. Premium income partially offsets funding costs on perp longs or
adds yield to spot holdings. The trade-off is capped upside: if the underlying rallies past the call strike, the overlay
triggers and limits gains at that level. On rally, the position is rolled up to a higher strike to maintain the long
exposure. This archetype operates as an overlay on an existing delta-1 book — it does not initiate the underlying
position itself.

## Token / position flow

```
1. UNDERLYING POSITION CHECK:
   - Read current delta-1 long (spot qty or perp notional) from position manager
   - Compute max_call_contracts = floor(underlying_qty / contract_multiplier)

2. CALL SELECTION:
   - Fetch options chain for target expiry (target_dte_entry DTE)
   - Find OTM call at target_call_delta (e.g. 0.20 = 20 delta)
   - Verify bid > min_premium_threshold (minimum premium to make writing economic)

3. POSITION SIZING:
   - Write call_coverage_ratio × max_call_contracts (e.g. 0.80 = write calls on 80% of position)
   - Size respects max_open_call_contracts cap

4. ENTRY: SELL call via TRADE instruction on options venue

5. HOLD:
   - Monitor underlying price vs call strike
   - If underlying > strike × roll_up_trigger_pct: ROLL UP (close current call, write new call
     at higher strike + same or next expiry) to maintain upside participation partially
   - Monitor IV change: if IV spikes post-entry, evaluate early buy-back

6. EXPIRY / REWRITE:
   - Call expires worthless: full premium retained → write new call at next cycle
   - Call in-the-money at expiry: underlying "called away" (or cash-settled); reopen underlying
     long if underlying_reopen_on_assignment = true
   - Early close: if mark < take_profit_pct × initial_premium, buy back and rewrite early

7. EXIT (overlay):
   - Operator signals underlying position closure → buy back calls before closing underlying
   - IV collapses → buy back cheap, wait for better premium environment to rewrite
```

## Entry conditions + signal

- Underlying delta-1 long position exists and size >= min_underlying_qty
- Target call premium (bid) >= min_premium_threshold in USD per contract
- ATM IV >= min_iv_to_write: only write when implied vol is sufficient for meaningful income
- DTE within [min_dte_entry, max_dte_entry] — prefer weekly or bi-weekly cycles
- No known binary event (upgrade, governance vote) within call tenor (suppress writing)

## Risk management

- Covered: max loss on the short call is absorbed by underlying appreciation (position is covered)
- Uncapped downside on underlying: this archetype does not hedge the long; pair with `VOL_OVERLAY_PROTECTIVE_PUT` for
  tail protection (collar structure)
- Roll-up discipline: never let the call expire deep ITM without rolling — exercise assignment disrupts underlying
  position size
- Max calls written = call_coverage_ratio × underlying_qty: never over-write (uncovered calls forbidden)
- IV spike guard: if ATM IV rises > iv_spike_buyback_threshold post-entry, buy back calls to avoid being short-gamma
  into a rally

## Config parameters

- `underlying`: BTC | ETH | SOL (etc.)
- `venue`: DERIBIT | OKX_OPTIONS
- `underlying_position_source`: spot | perp | both
- `target_call_delta`: delta of call to write (e.g. 0.20 = 20d)
- `target_dte_entry`: DTE at call writing (e.g. 7 or 14)
- `call_coverage_ratio`: fraction of underlying quantity to cover (e.g. 0.80)
- `min_premium_threshold_usd`: minimum call premium in USD per contract to write
- `min_iv_to_write`: minimum ATM IV required to write (e.g. 0.40 = 40%)
- `take_profit_pct`: buy back call when premium decays to this fraction of initial (e.g. 0.20)
- `roll_up_trigger_pct`: roll call up when underlying > strike × this (e.g. 1.02 = 2% ITM)
- `iv_spike_buyback_threshold`: buy back if ATM IV rises this much post-entry (e.g. 0.15 absolute)
- `underlying_reopen_on_assignment`: reopen delta-1 long if call assigned (true | false)

## When to use / market regime

- **Best regime**: sideways to mildly bullish market with elevated IV — maximises premium while limiting probability of
  call being exercised
- **Avoid**: strongly trending bull markets where the covered call caps significant gains; also avoid very low IV
  environments where premium barely covers execution costs
- **Asset fit**: BTC, ETH (liquid options chain on Deribit); any asset with a clean perp or spot long already running in
  the portfolio
- **Complements**: `VOL_OVERLAY_PROTECTIVE_PUT` (add puts to form a collar with defined risk on both sides)

## Example instances

```
VOL_OVERLAY_COVERED_CALLS@deribit-btc-call-7dte-usdt-prod
VOL_OVERLAY_COVERED_CALLS@deribit-eth-call-14dte-usdt-prod
VOL_OVERLAY_COVERED_CALLS@okx-options-btc-call-7dte-usdt-prod
```

## Not in this archetype

- Writing calls without an existing underlying long (naked call writing) — not supported; this archetype is covered-only
- Buying puts for tail protection on the same underlying long →
  [`VOL_OVERLAY_PROTECTIVE_PUT`](vol-overlay-protective-put.md)
- Structural short-vol carry without an existing delta-1 book (standalone theta harvesting) →
  [`VOL_CARRY`](vol-carry.md)
- ATM straddle expression (symmetric vol view, no underlying long required) → [`VOL_STRADDLE`](vol-straddle.md)
- Directional options expression where alpha is the underlying move, not premium income →
  [`ML_DIRECTIONAL_CONTINUOUS`](ml-directional-continuous.md)

## See also

- Protective put overlay: [vol-overlay-protective-put.md](vol-overlay-protective-put.md)
- Vol carry: [vol-carry.md](vol-carry.md)
- Family: [vol-trading.md](../families/vol-trading.md)
