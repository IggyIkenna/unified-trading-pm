---
doc_type: plan
title: >-
  Execution-service policy evaluator, fill-model fidelity, and matching-engine gaps
summary: >-
  13 open execution-service todos extracted verbatim from `service_config_ownership_and_instruction_contract_2026_08_12.md`
  (parent_epic: strategy_master) per the execution_master-scope audit
  (`/plans/archive/2026_08/issues/execution_master_scope_scattered_across_strategy_and_cross_cutting_2026_08_19.md`). All 13 are
  literal execution-service production-code changes (algo-selection wiring, benchmark/fill-model matching-engine
  internals, candle-fill fidelity tiers) — not strategy-config or research work — so they belong under
  `parent_epic: execution_master` for correct AO dispatch/reporting. The source doc's already-DONE todos, audit tables,
  and Progress Log stay in place untouched (this is a checkbox-only extraction, not a doc merge) — see that doc for the
  full architecture context (§A audit summary explains why the target property is "already the documented AND
  implemented architecture" for the benchmark-fill/backtest-boundary design these todos complete).
status: active
nature: process
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-api-contracts]
scope: [engineer]
tags: [execution, algo-selection, execution-policy, fill-model, matching-engine, benchmark-fills, candle-fidelity]
related:
  [
    /plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md,
    /plans/archive/2026_08/issues/execution_master_scope_scattered_across_strategy_and_cross_cutting_2026_08_19.md,
    /codex/04-architecture/execution-policy.md,
    /codex/04-architecture/execution-algorithm-selection.md,
    /codex/04-architecture/backtest-groups.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-20"
parent_epic: execution_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Extracted 2026-08-19 (execution_master-scope audit, `/autonomous`) from
  `service_config_ownership_and_instruction_contract_2026_08_12.md` §§ B/G/I/K — every checkbox below is copied
  VERBATIM from that doc (todo text, priority, tag unchanged); nothing summarized or reworded. That doc's own §A audit
  + already-DONE todos (algo-selection wiring for the two real call sites, latency-timestamp threading, participation-
  cap primitive) are the prerequisite context for several items here (e.g. todo 5's "wire the evaluator" builds on the
  already-shipped resolver; todo 11's cap-definition fix builds on the already-shipped cap wiring) — read that doc's
  §A/§B/§G/§K prose for the full picture, not just these checkboxes in isolation.
context_scope:
  [
    execution-service/execution_service/v2/execution_policies.py,
    execution-service/execution_service/algorithms/selector.py,
    execution-service/execution_service/engine/instruction_convert.py,
    execution-service/execution_service/matching_engine/candle_book_cols.py,
    execution-service/execution_service/utils/fidelity_selector.py,
    /codex/04-architecture/execution-policy.md,
  ]
---

# Execution-service policy evaluator, fill-model fidelity, and matching-engine gaps

> **Moved from `/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` 2026-08-19**
> (execution_master-scope audit). That doc's §§ B/G/I/K each had this exact checkbox as an open todo; it is removed
> there and replaced with a pointer to this doc — see that doc for the surrounding architecture prose, the
> already-DONE sibling todos in the same sections, and the full Progress Log evidence trail. This doc exists only to
> give these 13 execution-service-owned items the correct `parent_epic` for AO dispatch; it does not duplicate the
> source doc's audit content.

## § B — Execution-policy registry (origin: source doc § B)

- [ ] [AGENT] P1. **Reject an unknown `execution_policy_ref` loudly.** Default-deny is already the rule-evaluation
      semantic; make an unresolvable REF equally loud rather than silently falling back to a default algo, which would
      hide a misconfigured client.

## § G — Execution-service change surface (origin: source doc § G)

- [ ] [AGENT] P0. **G3 — collapse the benchmark's TWO independent implementations into one sent value.** There is
      **one** benchmark-fills contract bridging the backtest groups
      ([backtest-groups](/codex/04-architecture/backtest-groups.md): Group B uses benchmark fills, Group C measures
      execution alpha "against the same benchmark"), and the standalone-backtest property is already built:
      `strategy_service/engine/backtest/benchmark_fills.py` is a pure, bit-identical, 653-line Group-B implementation
      whose own docstring states it lives in strategy-service "because Group B replaces execution entirely". The real
      risk is drift between two implementations of one definition — 653 lines here, `BenchmarkMatcher` there.
      `BenchmarkMatcher` is ONE of five matchers (`L0`/`L1`/`L2`/`AMM`/`Benchmark`), scoped to **ALPHA_ZERO protocol
      ops — LEND/STAKE/BORROW**, and its benchmark-price mode is already "instant fill at a **strategy-supplied**
      benchmark price, `price_impact_bps = 0`" — i.e. on the trade path it already consumes rather than re-derives.
      So sending the reference formalises the legacy mode's existing assumption; it does not displace a rival
      calculation, and there is no independent trade-side benchmark engine to delete. **Recommendation:
      strategy-sent is authoritative and the trade path becomes an explicit pass-through.**
- [ ] [AGENT] P0. **G3a — do NOT no-op the lending path.** The same matcher's Phase-3B lending mode routes through
      `LendingRateImpactCalculator` (`matching_engine/lending/rate_impact.py`) so backtest yield uses the
      **POST-trade** rate: `fill_price` becomes post-trade APY and `price_impact_bps` the signed rate delta (negative
      for SUPPLY/REPAY as utilisation drops, positive for BORROW/WITHDRAW). strategy-service cannot compute this — it
      is a function of pool state and your own size — and using the pre-trade rate would silently **overstate lending
      and borrow yields** on every recursive-carry and yield archetype. This matcher is not simulating a venue; it is
      modelling own-size market impact on a real pool. Add a test asserting the lending path stays live if the trade
      path is collapsed, so a future "make the benchmark matcher a pass-through" change cannot take the rate impact
      with it.
- [ ] [AGENT] P1. **Unify the algo vocabulary — there are two.** `engine/instruction_convert.py` does
      `algorithm = (algo or "MARKET").upper()`, and **`"MARKET"` does not exist in UAC `EXECUTION_ALGOS`** at all; it
      also re-implements TWAP slicing params inline. That is a second naming system on the manual-instruction path,
      invisible to the selector's validation. Either register the manual path's names in UAC or route it through the
      selector.
- [ ] [AGENT] P1. **Wire the execution-policy evaluator** (see § B above) — `ExecutionPolicyArtifact` / `PolicyRule`
      appear only in `v2/__init__.py` re-export plumbing, so the rule evaluator that already implements
      first-match-wins / default-deny is never called.
- [ ] [AGENT] P2. **Confirm the benchmark module's own consumers.** `metrics.py` is imported only by its siblings
      (`enhanced_comparison.py`, `ranking.py`) — verify the chain reaches a live/reporting caller rather than
      terminating in the benchmark package, so the alpha metrics are actually surfaced somewhere.

## § I — Candle-based fills / fidelity tiers (origin: source doc § I)

- [ ] [AGENT] P0. **DECIDED 2026-08-12 — build the sub-candle rung as a graded fallback, not a binary.** The ladder
      becomes **book-columns → sub-candle VWAP → OHLC bar**, each rung used only when the one above has no data.
      `CandleBookColsMatcher` needs `BOOK_SUMMARY_COLUMNS` precomputed on the candle, and cells that never had tick
      data can never have them — today those drop straight to the naive tier, which is the gap. Nothing sub-candle
      exists anywhere in `matching_engine/`. **The insertion is architecturally clean**:
      `execution_fidelity(asset_group, venue, instrument_type, mode)` resolves the data-supported tier declaratively
      from the cell's MVP data_types in `MVP_SCOPE` — not by probing storage — so "has 1m candles, lacks book
      columns" is expressible as a decision-table rule. `clamp_tier()` already only ever clamps DOWN, so a new rung
      cannot silently upgrade anything. **Two cautions for the implementer.** (1) `_TIER_RANK` is integer-ranked
      `OHLC_BAR: 1 / CANDLE_BOOK_COLS: 2 / L2_TICK: 3`; inserting between 1 and 2 means renumbering, which touches
      every clamp comparison and any persisted tier value — prefer widening the scale over shifting existing numbers.
      (2) Preserve the existing fail-loud guard: a cell not in `MVP_SCOPE` raises rather than degrading, because
      "execution must never silently fall back to OHLC for a venue/instrument_type that is not even in the capture
      universe" — the new rung must not become a soft landing for cells that should still raise.
- [ ] [AGENT] P1. **Measure the population the new rung serves** — cells with finer candles but no book-summary
      columns — so the build is sized against real coverage rather than assumed need. This informs, but no longer
      gates, the work above.
- [ ] [AGENT] P1. **If it is built, carry PB.8's correction — a share of candle VOLUME over-counts fillable volume.**
      `e2e-testing/scripts/paper_trading/_aggtrades_fidelity.py` (PB.8) already measured this against real Binance
      aggTrades: a resting maker only fills against trades that hit its level **on the filling side** (for a resting
      BUY at L: aggressive SELLS at price ≤ L, `isBuyerMaker=True`), while total candle volume includes the other
      side and trades away from L. So a flat "25% of the candle" participation cap is optimistic by a measurable
      ratio. **Both `_aggtrades_fidelity.py` (PB.8) and `_fill_backtest.py` (PB.7) are `Lifecycle: campaign` scripts
      whose delete-when condition is "the fill-model decision is made and the winner shipped"** — so this decision is
      what's actually blocking their retirement.
- [ ] [AGENT] P1. **Update `/codex/04-architecture/execution-policy.md`** to state the `(client_id, slot_label)`
      keying and the loader/reload story once § B lands — and to say plainly that the registry was
      declared-but-unwired until then, so the doc stops implying a live mechanism.

## § K — e2e fill models → execution-service reproducibility (origin: source doc § K)

- [ ] [AGENT] P0. **Carry PB.8's correction into the cap's definition.** The cap must apply to volume that crosses
      the limit **on the filling side** (for a resting BUY at L: aggressive SELLS at price ≤ L,
      `isBuyerMaker=True`), not to total candle volume — `_ledgers.py` already resolves the maker fill "against the
      REAL aggTrades flow that crossed our limit (true volume-at-price)", so the corrected model is already written
      down, not merely measured. Applies to the already-shipped `TradeMatcher.capped_passive_fill_quantity` /
      `L1Matcher._match_passive()` wiring (`execution-service@f3402a7c11`).
- [ ] [AGENT] P1. **Route the per-strategy fill assumptions through the execution-policy `then_params`** rather than
      a new config surface — this is precisely what that artifact is for, and it ties § K to § B/§ G1: the policy
      registry being unwired is _why_ per-strategy fill parameterisation has nowhere to live today.
- [ ] [AGENT] P2. **Then retire the campaign scripts.** `_fill_backtest.py` and `_aggtrades_fidelity.py` both carry
      `Lifecycle: campaign` with delete-when "the fill-model decision is made + the winner is shipped". They are the
      decision record; once the cap and its side-filter ship, they go.

## Progress Log

- **2026-08-19, claude (`/autonomous`)**: doc created as a checkbox-only extraction from
  `service_config_ownership_and_instruction_contract_2026_08_12.md` §§ B/G/I/K, per the execution_master-scope audit.
  All 13 todos copied verbatim (text, priority, tag unchanged) — no rewording, no re-scoping. The source doc's
  already-shipped ✅ todos in the same sections, its § A/C/D/H (strategy-owned: reference-price contract,
  `ClientDomainConfig` subscription, transfer-emit netting), § J's dual-path-documentation todo, and its full
  Progress Log all stay in the source doc untouched — this extraction moves only currently-open,
  execution-service-production-code todos, not the doc's audit narrative or evidence trail.
- **context-scout 2026-08-20**: refreshed context_scope (6 entries)
