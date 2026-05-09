---
title: "ARBITRAGE_PRICE_DISPERSION canonicalisation finalisation — strategy-service catalog + tracer + P&L attribution"
type: plan
asset_group: defi
priority: P1
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-09
date: 2026-05-09
status: active
migrated_from: defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md  # Stream B sister todos
folds_in: []
related:
  - defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md
  - defi_master_2026_05_07.md
todos: []
isProject: false
---

# ARBITRAGE_PRICE_DISPERSION canonicalisation finalisation

> **Why this plan exists.** Stream B of [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
> declared the canonicalisation gate: _"Codex doc/code/plans all use `ARBITRAGE_PRICE_DISPERSION` (with config variant)
> for funding-dispersion-leveraged. No remaining references to `leveraged_funding_arb` as a standalone archetype except
> in this plan + the issue file (as historical context)."_
>
> Audit verification 2026-05-09 (this plan's session):
>
> - ✅ UAC `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` exists at `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py:68`; no `LEVERAGED_FUNDING_ARB` in the enum.
> - ❌ strategy-service catalog has 6 `ARBITRAGE_PRICE_DISPERSION` slots in `archetype_slot_resolver.py` (Aave/Aave-Compound/Aave-Compound-Ethereum/Aave-Morpho-Arbitrum/Polymarket-Binance/Unity-Betfair-Matchbook) but **no `funding-dispersion-leveraged` config variant**.
> - ❌ No `trace_arbitrage_price_dispersion.py` tracer script in `strategy-service/scripts/` (only `trace_carry_staked_basis.py` + `trace_all_carry_archetypes.py` exist).
> - ❌ Zero `ARBITRAGE_PRICE_DISPERSION` references in `pnl-attribution-service/pnl_attribution_service/` source — only sports test fixtures use the lowercase string `"arbitrage"`.
>
> The 3 sister todos (strategy-service / tracer / P&L attribution) are genuine feature work. This plan owns each as
> an explicit phase with verification command per CLAUDE.md "Plans Run To Actual Completion" HARD RULE.

## Cross-plan banner

This plan is the **named successor** for Stream B's 3 sister todos in
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
lines 158-166 (UAC + strategy-service + tracer-scripts + P&L attribution).

## Phase A — strategy-service catalog: add `funding-dispersion-leveraged` config variant

- [ ] [strategy-service] P1. Add slot entry to
      `strategy-service/strategy_service/engine/strategies/v2/archetype_slot_resolver.py` per the existing pattern
      (e.g. after the current ARBITRAGE_PRICE_DISPERSION rows ~L225–L811):

      ```python
      Slot(
          archetype=StrategyArchetype.ARBITRAGE_PRICE_DISPERSION,
          slot_label="ARBITRAGE_PRICE_DISPERSION@funding-dispersion-leveraged",
          asset_group=MarketAssetGroup.DEFI,  # or CEFI depending on funding-leg venues
          # ... per-slot config: leverage, perp-pair venues, hedge-leg ratios, etc.
      ),
      ```

- [ ] [strategy-service] P1. Slot consumed by `ArbitragePriceDispersionEngine` factory entry at `factory.py:66`. Confirm
      the engine handles the funding-dispersion-leveraged config (cross-venue funding-rate spread between two perp
      venues). If a new engine subclass is needed, add `ArbitragePriceDispersionFundingLeveragedEngine`.

- [ ] [strategy-service] P1. Tests:
      `tests/unit/test_archetype_slot_resolver.py::test_arbitrage_price_dispersion_funding_leveraged_slot_exists`.
      QG green. Commit + push.

- [ ] [VERIFY] P0. From within strategy-service repo:
      `grep -n "funding-dispersion-leveraged" strategy_service/engine/strategies/v2/archetype_slot_resolver.py` returns
      ≥ 1 hit; `python -c "from strategy_service.engine.strategies.v2.factory import ARCHETYPE_TO_ENGINE; assert
      StrategyArchetype.ARBITRAGE_PRICE_DISPERSION in ARCHETYPE_TO_ENGINE"` exits 0.

**Full-execution criterion**: slot live on `live-defi-rollout`; consumed by an integration smoke that resolves
`("ARBITRAGE_PRICE_DISPERSION", "funding-dispersion-leveraged")` to a non-None Slot object.

## Phase B — tracer script: `trace_arbitrage_price_dispersion.py`

- [ ] [strategy-service] P1. Create `strategy-service/scripts/trace_arbitrage_price_dispersion.py` modeled on
      `trace_carry_staked_basis.py`. Should accept:
      - `--mode batch|live`
      - `--start-date YYYY-MM-DD --end-date YYYY-MM-DD`
      - `--config-variant default|funding-dispersion-leveraged|cross-venue-spread` (default = `default`)
      - `--asset-group defi|cefi` (the archetype spans both per the slot taxonomy)

      The script runs the archetype's signal generation through the unified pipeline (per CLAUDE.md "Batch = Live")
      and emits per-fixture/per-day P&L + signal trace rows for operator inspection.

- [ ] [strategy-service] P1. Cross-reference: extend `trace_all_carry_archetypes.py` to optionally invoke
      `trace_arbitrage_price_dispersion.py` for the cross-venue funding-spread variant. Don't fold the dispersion
      tracer INTO the carry tracer — different families.

- [ ] [VERIFY] P0. `python strategy-service/scripts/trace_arbitrage_price_dispersion.py --mode batch
      --start-date 2024-01-01 --end-date 2024-01-07 --config-variant funding-dispersion-leveraged --asset-group defi`
      runs to completion + emits non-empty CSV/parquet output.

**Full-execution criterion**: tracer script runs end-to-end against real backfilled MTDS + features data for a
1-week window; produces a CSV with at least one signal-emit row.

## Phase C — pnl-attribution-service rows for ARBITRAGE_PRICE_DISPERSION

- [ ] [pnl-attribution-service] P1. Add `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` handling to the
      service's archetype-aware P&L aggregator. Today the service has zero `ARBITRAGE_PRICE_DISPERSION` references in
      `pnl_attribution_service/` source. Likely surfaces:
      - Per-archetype P&L bucket (alongside `CARRY_STAKED_BASIS`, etc.)
      - Per-config-variant breakdown (`funding-dispersion-leveraged` vs other variants)
      - Output path: `gs://pnl-attribution-{pid}/by_strategy/ARBITRAGE_PRICE_DISPERSION/...`

- [ ] [pnl-attribution-service] P1. Tests:
      `tests/unit/test_archetype_pnl.py::test_arbitrage_price_dispersion_attribution`. Verify P&L bucket exists +
      attributes correctly given mock fills.

- [ ] [VERIFY] P0. After tracer (Phase B) emits rows for the 1-week window:
      `gcloud storage ls gs://${PID}-pnl-attribution/by_strategy/ARBITRAGE_PRICE_DISPERSION/...` returns non-empty;
      sample probe of one row confirms `archetype="ARBITRAGE_PRICE_DISPERSION"` + `config_variant=...` columns
      populated.

**Full-execution criterion**: pnl-attribution-service produces non-empty rows under `ARBITRAGE_PRICE_DISPERSION` for
the same 1-week window the tracer covered; archetype-bucket check passes.

## Phase D — Stream B gate close

- [ ] [PM-plan] P0. After Phases A+B+C all ship: re-check Stream B gate in
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
      § Gate (line 168-170). Workspace grep `grep -rn "leveraged_funding_arb" --include='*.py' --include='*.md'`
      returns only:
      - the source plan + this finalisation plan + the original issue doc (historical context)
      - codex doc historical references with explicit "renamed to ARBITRAGE_PRICE_DISPERSION" annotations
      - archive/* commits (frozen historical state)

- [ ] [PM-plan] P0. Flip 4 Stream B sister todos in defi_archetypes plan from `[ ]` to `[x]` with finalisation
      commit shas. Archive defi_archetypes plan if Streams A/C/D/E are also complete; otherwise leave active.

## Done definition

1. ✅ Phase A — strategy-service slot for `funding-dispersion-leveraged` shipped + factory wired + QG green.
2. ✅ Phase B — `trace_arbitrage_price_dispersion.py` script ships + runs end-to-end on real backfill window.
3. ✅ Phase C — pnl-attribution-service ARBITRAGE_PRICE_DISPERSION rows ship + 1-week sample probe non-empty.
4. ✅ Phase D — Stream B gate closes; workspace grep for `leveraged_funding_arb` returns only historical refs.

**Full-execution criterion** (per PLAN_FORMAT.md § 8 + "Plans Run To Actual Completion" HARD RULE):

- ✅ **Tracer ran-to-completion against real infra**.
  - **What ran**: `python strategy-service/scripts/trace_arbitrage_price_dispersion.py --mode batch
    --start-date 2024-01-01 --end-date 2024-01-07 --config-variant funding-dispersion-leveraged --asset-group defi`
  - **Verification**: tracer CSV non-empty; pnl-attribution rows populated for the same window; deployment-UI
    drilldown shows ARBITRAGE_PRICE_DISPERSION bucket under DeFi.
- ✅ **Workspace grep gate**.
  - **What ran**: `rg 'leveraged_funding_arb' --type py --type md`
  - **Verification**: only historical-context hits remain (source plan + this plan + archived issue + codex
    historical annotations); no standalone-archetype refs.

## Cross-references

- [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
  — Stream B parent (this plan is the named successor)
- [`defi_master_2026_05_07.md`](defi_master_2026_05_07.md) — master archetype owner; L152-153 already uses
  `ARBITRAGE_PRICE_DISPERSION` per 2026-05-08 rename
- [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) — May-23 cutover master
- UAC `unified_api_contracts/internal/architecture_v2/enums.py:68` — SSOT enum entry
