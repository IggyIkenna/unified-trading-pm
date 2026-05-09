---
title: "ARBITRAGE_PRICE_DISPERSION canonicalisation finalisation — strategy-service catalog + tracer + P&L attribution"
overview:
  "Close Stream B's 3 deferred sister todos: ship the funding-rate-dispersion config variant slot in
  strategy-service, the trace_arbitrage_price_dispersion.py tracer, and pnl-attribution-service archetype rows; resolve
  the lingering codex circular cross-ref."
type: plan
asset_group: defi
priority: P1
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
epic: live_defi_rollout
locked_by: live-defi-rollout
locked_since: 2026-05-09
date: 2026-05-09
status: active
migrated_from: defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md # Stream B sister todos
folds_in: []
related:
  - defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md
  - defi_master_2026_05_07.md
  - master_to_live_defi_2026_05_23.md
repos_touched:
  - strategy-service # Phase A (slot + factory) + Phase B (tracer)
  - pnl-attribution-service # Phase C (archetype-aware P&L bucket)
  - unified-trading-pm # Phase D (gate close + plan flips) + Phase E (codex)
depends_on:
  - defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07 # parent Stream B; we close 3 deferred sister todos
completion_gates:
  code: C5 # all 3 service repos green on QG + landed on live-defi-rollout
  deployment: none
  business: B4 # tracer batch run validates against expected funding-dispersion P&L envelope
todos: []
isProject: false
---

# ARBITRAGE_PRICE_DISPERSION canonicalisation finalisation

> **Why this plan exists.** Stream B of
> [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
> declared the canonicalisation gate: _"Codex doc/code/plans all use `ARBITRAGE_PRICE_DISPERSION` (with config variant)
> for funding-rate-dispersion. No remaining references to `leveraged_funding_arb` as a standalone archetype except
> in this plan + the issue file (as historical context)."_
>
> Audit verification 2026-05-09 (this plan's session):
>
> - ✅ UAC `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` exists at
>   `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py:68`; no `LEVERAGED_FUNDING_ARB` in
>   the enum.
> - ❌ strategy-service catalog has 6 `ARBITRAGE_PRICE_DISPERSION` slots in `archetype_slot_resolver.py`
>   (Aave/Aave-Compound/Aave-Compound-Ethereum/Aave-Morpho-Arbitrum/Polymarket-Binance/Unity-Betfair-Matchbook) but **no
>   `funding-rate-dispersion` config variant**.
> - ❌ No `trace_arbitrage_price_dispersion.py` tracer script in `strategy-service/scripts/` (only
>   `trace_carry_staked_basis.py` + `trace_all_carry_archetypes.py` exist).
> - ❌ Zero `ARBITRAGE_PRICE_DISPERSION` references in `pnl-attribution-service/pnl_attribution_service/` source — only
>   sports test fixtures use the lowercase string `"arbitrage"`.
>
> The 3 sister todos (strategy-service / tracer / P&L attribution) are genuine feature work. This plan owns each as an
> explicit phase with verification command per CLAUDE.md "Plans Run To Actual Completion" HARD RULE.

## Cross-plan banner

This plan is the **named successor** for Stream B's 3 deferred sister todos (strategy-service / tracer-scripts / P&L
attribution) marked `DEFERRED-TO-arbitrage_price_dispersion_finalisation_2026_05_09` at
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
lines 175–188. The UAC enum sister todo (line 170-174) is already shipped and verified. Phase E of this plan also
absorbs the lingering codex P0 todo at parent line 155-157 (resolve the `arbitrage-price-dispersion.md` ↔
`carry-basis-perp.md` circular cross-reference), since per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE codex
updates ship in the same logical unit as the contract change they reflect.

## Pre-audit blast-radius (per Citadel-Grade § 1)

Workspace grep performed 2026-05-09; manifest of files touched per phase:

| Repo                    | File                                                                                          | Phase | Action                                                                                                  |
| ----------------------- | --------------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------------------------------------------------- |
| strategy-service        | `strategy_service/engine/strategies/v2/archetype_slot_resolver.py` (after L811)               | A     | Add 1 new `Slot(...)` row for the `funding-rate-dispersion` variant                                |
| strategy-service        | `strategy_service/engine/strategies/v2/factory.py:66`                                         | A     | Verify `ARBITRAGE_PRICE_DISPERSION` factory entry handles new variant; subclass only if engine diverges |
| strategy-service        | `strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py`              | A     | Read-only audit; subclass `ArbitragePriceDispersionFundingLeveragedEngine` only if needed               |
| strategy-service        | `strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion_hierarchical.py` | A     | LEADER_HEDGE mode reference per parent plan codex update                                                |
| strategy-service        | `strategy_service/portfolio_allocator/archetypes.py:678,729`                                  | A     | `ArbitragePriceDispersionRankAllocator` — verify it ranks funding-dispersion variant alongside others   |
| strategy-service        | `tests/unit/test_archetype_slot_resolver.py`                                                  | A     | Add `test_arbitrage_price_dispersion_funding_leveraged_slot_exists`                                     |
| strategy-service        | `scripts/trace_arbitrage_price_dispersion.py` (NEW)                                           | B     | Modeled on `scripts/trace_carry_staked_basis.py` + `scripts/trace_all_carry_archetypes.py`              |
| strategy-service        | `scripts/trace_all_carry_archetypes.py`                                                       | B     | Optional cross-invoke for the funding-spread variant (don't fold the dispersion tracer in)              |
| pnl-attribution-service | `pnl_attribution_service/engine/` + `analytics/`                                              | C     | Add archetype bucket for ARBITRAGE_PRICE_DISPERSION + per-config-variant breakdown                      |
| pnl-attribution-service | `tests/unit/test_archetype_pnl.py`                                                            | C     | New test `test_arbitrage_price_dispersion_attribution`                                                  |
| pnl-attribution-service | output bucket `gs://${PID}-pnl-attribution/by_strategy/ARBITRAGE_PRICE_DISPERSION/...`        | C     | Verify rows produced for tracer's 1-week window                                                         |
| unified-trading-pm      | `codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md:171-179`          | E     | Remove line redirecting funding-rate perp arb → `CARRY_BASIS_PERP` (circular ref)                       |
| unified-trading-pm      | same file, "Example instances" section (after L159)                                           | E     | Add `funding-rate-dispersion` example slot label                                                   |
| unified-trading-pm      | `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` lines 155-157, 175-188      | D     | Flip 4 `[ ]` → `[x]` with this plan's commit shas                                                       |

**Read-only verifications already complete (do not re-do):** UAC enum entry exists at
`unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py:68`; no `LEVERAGED_FUNDING_ARB` symbol
anywhere in the workspace except parent plan + this plan + archived issue + codex historical annotations.

## Phase dependency DAG

```
        ┌───────────────────────────────────────────────────┐
        │ Phase A — strategy-service slot + factory wiring  │
        │ (independent; ships first; no upstream blockers)  │
        └────────────────────┬──────────────────────────────┘
                             │ Slot exists in resolver
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ Phase B — trace_arbitrage_price_dispersion.py     │
        │ (needs slot to resolve; runs through full         │
        │  unified pipeline per Batch=Live)                 │
        └────────────────────┬──────────────────────────────┘
                             │ Tracer emits real signals + simulated fills for 1-week window
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ Phase C — pnl-attribution-service archetype rows  │
        │ (consumes tracer output; verifies bucket          │
        │  attribution for ARBITRAGE_PRICE_DISPERSION)      │
        └────────────────────┬──────────────────────────────┘
                             │ A + B + C all green
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ Phase D — Stream B gate close + plan flips        │
        └────────────────────┬──────────────────────────────┘
                             │ parallelisable with C, must complete before D
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ Phase E — codex SSOT updates (circular ref +      │
        │ funding-rate-dispersion example)             │
        │ MAY run in parallel with B/C; MUST land by D      │
        └───────────────────────────────────────────────────┘
```

**Sequencing note:** A → B → C is strictly sequential (each consumes the prior phase's artefact). E (codex) is
independent of B+C and can run in parallel as soon as A's slot label is decided. D is the last gate.

## Open questions / operator decisions

### ✅ All 6 resolved 2026-05-09 (operator); plan ships Phase A with confirmed values, no placeholders

1. **Config-variant slug naming → `funding-rate-dispersion`.** Drops the `-leveraged` suffix; leverage is orthogonal
   (Stream D `target_leverage` config field, not part of the dispersion-type slug). All references in this plan + every
   downstream codex / strategy-service / pnl-attribution-service / tracer artefact use `funding-rate-dispersion`.
2. **Venue selection model → dynamic best-long + best-short across the full 6-venue universe** (Bybit, Deribit, Binance,
   OKX, Hyperliquid, Aster). NOT a fixed venue pair. The strategy's whole alpha is selecting per cycle which two
   venues offer the widest funding-rate spread; pre-locking a pair would defeat the strategy. **Implication for the
   slot:**
   - Slot label uses a multi-venue universe descriptor, not two specific venue names. Proposed shape:
     `ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-<asset>-<currency>-prod`
     (e.g. `ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-btc-usdt-prod` for the BTC/USDT instance).
   - Slot config includes `venue_universe: [bybit, deribit, binance, okx, hyperliquid, aster]` + a per-cycle
     selector (`best_long_venue` + `best_short_venue` resolved dynamically by the engine from features-perp-funding's
     latest funding-rate snapshot per venue).
   - `ArbitragePriceDispersionEngine` (or the hierarchical sibling) needs to support venue-universe + dynamic-pair
     selection if it doesn't already; if it doesn't, Phase A spawns a subclass
     `ArbitragePriceDispersionFundingRateEngine` that wraps the universe iteration + best-pair selection.

3. **Leverage cap → `target_leverage = 5.0`.** 5× max (operator override of the 3× conservative default). Slot config
   field `target_leverage: "5.0"`. Live-cutover risk discipline relies on the vol-cap clamp (Q4) + position-balance-
   monitor + kill-switch wiring rather than a low static cap.
4. **Volatility-cap clamp → short-term realised-vol features (NOT 60-day).** Use `features-volatility-service`'s
   short-window outputs: `realized_vol_5` / `realized_vol_10` / `realized_vol_20` (5/10/20 bar annualized close-to-
   close, computed at
   [`features_volatility_service/calculators/realized_vol_calculator.py`](../../../features-volatility-service/features_volatility_service/calculators/realized_vol_calculator.py)).
   Proposed shape: clamp `target_leverage → 1.0` when **`realized_vol_20` (1h candles, ≈ 20h trailing) exceeds 80%
   annualized OR `vol_regime_zscore_20` > 2.0** (the latter adapts to per-asset baseline rather than using a fixed
   threshold). The engine reads these from features-volatility's parquet output per the existing reader pattern. Slot
   config:
   ```python
   "vol_cap_clamp_feature": "realized_vol_20",
   "vol_cap_clamp_timeframe": "1h",
   "vol_cap_clamp_threshold_pct": "80.0",
   "vol_cap_clamp_zscore_feature": "vol_regime_zscore_20",
   "vol_cap_clamp_zscore_threshold": "2.0",
   "vol_cap_clamp_target_leverage": "1.0",
   "vol_cap_clamp_combine": "any",  # OR — clamp if EITHER threshold is breached
   ```
5. **`bidirectional_funding` → `true`.** Capture both signs of the funding-rate spread (operator confirmed: doesn't
   matter whether `funding(long_venue) − funding(short_venue)` is positive or negative).
6. **Sign-match entry filter (NEW — operator-added 2026-05-09).** Only enter when the **price-spread sign matches the
   funding-spread sign** between the two selected venues. Rationale: collecting funding while price spread mean-reverts
   in your favour stacks two edges; collecting funding while price spread widens against you eats P&L. Slot config:
   ```python
   "entry_filter_sign_match": "price_spread == funding_spread",  # only enter if signs match
   ```
   Engine logic (Phase A engine wiring): every funding cycle, after picking `best_long_venue` (argmax(funding_rate))
   and `best_short_venue` (argmin(funding_rate)), compute `price_spread = mid_price(long_venue) − mid_price(short_venue)`
   and `funding_spread = funding_rate(long_venue) − funding_rate(short_venue)`. Enter ONLY if
   `sign(price_spread) == sign(funding_spread)`; otherwise skip the cycle (no entry, no fees burned).

## Phase A — strategy-service catalog: add `funding-rate-dispersion` config variant

- [ ] [strategy-service] P1. Add slot entry (start with BTC/USDT, ETH/USDT in A.6) to
      `strategy-service/strategy_service/engine/strategies/v2/archetype_slot_resolver.py` per the existing pattern (e.g.
      after the current ARBITRAGE_PRICE_DISPERSION rows ~L225–L811). The slot wires the **6-venue universe** with
      dynamic best-long/best-short selection (NOT a fixed venue pair) + sign-match entry filter + short-term-vol
      clamp:

      ```python
      Slot(
          archetype=StrategyArchetype.ARBITRAGE_PRICE_DISPERSION,
          slot_label="ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-btc-usdt-prod",
          asset_group=MarketAssetGroup.CEFI,  # all 6 perp venues are CEFI
          config={
              # Q1 + Q2 — dispersion type + venue universe
              "dispersion_type": "funding-rate-dispersion",
              "asset": "BTC",
              "quote_currency": "USDT",
              "venue_universe": ["bybit", "deribit", "binance", "okx", "hyperliquid", "aster"],
              "venue_selection_mode": "dynamic-best-long-short",  # per funding cycle (~8h)
              # Q3 — leverage cap
              "target_leverage": "5.0",
              # Q4 — vol-cap clamp using short-term realised-vol features
              "vol_cap_clamp_feature": "realized_vol_20",            # 20-bar annualized close-to-close
              "vol_cap_clamp_timeframe": "1h",                       # 1h candles → ~20h trailing window
              "vol_cap_clamp_threshold_pct": "80.0",                 # raw rv threshold
              "vol_cap_clamp_zscore_feature": "vol_regime_zscore_20",
              "vol_cap_clamp_zscore_threshold": "2.0",               # 2σ above 60-bar mean
              "vol_cap_clamp_combine": "any",                        # OR — clamp if EITHER breached
              "vol_cap_clamp_target_leverage": "1.0",
              # Q5 — bidirectional funding capture
              "bidirectional_funding": "true",
              # Q6 — sign-match entry filter
              "entry_filter_sign_match": "price_spread == funding_spread",
          },
      ),
      ```

- [ ] [strategy-service] P1. Slot consumed by `ArbitragePriceDispersionEngine` factory entry at `factory.py:66`.
      Audit the existing engine + `ArbitragePriceDispersionHierarchicalEngine` for `venue_universe` + dynamic-pair
      selection support. Two outcomes possible:
      - **(a)** Existing engine already supports the `venue_universe` + dynamic-best-pair pattern (LEADER_HEDGE mode at
        `price_dispersion_hierarchical.py:105` is closest fit). Wire the new slot config through; no new subclass.
      - **(b)** Engine doesn't support dynamic pair selection from a >2-venue universe. Spawn
        `ArbitragePriceDispersionFundingRateEngine` subclass that, every funding cycle (~8h):
        1. Reads per-venue funding-rate snapshot from features-perp-funding (latest tick per venue in `venue_universe`).
        2. Selects `best_long_venue = argmax(funding_rate)`, `best_short_venue = argmin(funding_rate)`.
        3. Reads latest mid-prices for the pair from MTDS perp tick data.
        4. Computes `funding_spread = funding_rate(long_venue) − funding_rate(short_venue)` and `price_spread =
           mid_price(long_venue) − mid_price(short_venue)`.
        5. **Sign-match entry filter (Q6):** if `sign(price_spread) != sign(funding_spread)` → SKIP this cycle (no
           entry, no fees burned). Emit a trace event `SIGN_MISMATCH_SKIP` with both signs for observability.
        6. Reads `realized_vol_20` + `vol_regime_zscore_20` from features-volatility for the asset.
        7. **Vol-cap clamp (Q4):** if `realized_vol_20 > 80%` OR `vol_regime_zscore_20 > 2.0` → clamp
           `target_leverage` from configured 5.0 down to 1.0. Emit `VOL_CAP_CLAMPED` trace event.
        8. Emits the leg pair through `LegController.update` per the May-2026 leg-controller refactor with the
           clamp-adjusted leverage.

      Document the chosen branch (a vs b) inline in the commit message + the slot doc-string.

- [ ] [strategy-service] P1. Tests:
      `tests/unit/test_archetype_slot_resolver.py::test_arbitrage_price_dispersion_funding_leveraged_slot_exists`. QG
      green. Commit + push.

- [ ] [VERIFY] P0. From within strategy-service repo:
      `grep -n "funding-rate-dispersion" strategy_service/engine/strategies/v2/archetype_slot_resolver.py` returns
      ≥ 1 hit;
      `python -c "from strategy_service.engine.strategies.v2.factory import ARCHETYPE_TO_ENGINE; assert     StrategyArchetype.ARBITRAGE_PRICE_DISPERSION in ARCHETYPE_TO_ENGINE"`
      exits 0.

- [ ] [strategy-service] P1. **A.6 follow-up — extend to ETH/USDT slot.** Once BTC/USDT slot ships green, add
      `ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-eth-usdt-prod` (same shape, asset=`ETH`). Verify
      both slots resolve in `archetype_slot_resolver`; both consumed by the engine factory entry. Re-run QG. Commit +
      push as a separate `feat(strategies):` commit.

**Code gates**: C4 — `bash strategy-service/scripts/quality-gates.sh` Pass 1 green (basedpyright + ruff + tests). C5 —
landed on `live-defi-rollout` per workspace dirty-deps rule (`git push origin live-defi-rollout` directly).

**Full-execution criterion**: slot live on `live-defi-rollout`; consumed by an integration smoke that resolves
`("ARBITRAGE_PRICE_DISPERSION", "funding-rate-dispersion")` to a non-None Slot object. **What ran**: integration
smoke from strategy-service `tests/integration/` that calls the slot resolver + factory together. **Verification**: test
green;
`python -c "from strategy_service.engine.strategies.v2.archetype_slot_resolver import resolve_slot; print(resolve_slot('ARBITRAGE_PRICE_DISPERSION', 'funding-rate-dispersion'))"`
prints non-None Slot.

## Phase B — tracer script: `trace_arbitrage_price_dispersion.py`

- [ ] [strategy-service] P1. Create `strategy-service/scripts/trace_arbitrage_price_dispersion.py` modeled on
      `trace_carry_staked_basis.py`. Should accept: - `--mode batch|live` -
      `--start-date YYYY-MM-DD --end-date YYYY-MM-DD` -
      `--config-variant default|funding-rate-dispersion|cross-venue-spread` (default = `default`) -
      `--asset-group defi|cefi` (the archetype spans both per the slot taxonomy)

      The script runs the archetype's signal generation through the unified pipeline (per CLAUDE.md "Batch = Live")
      and emits per-fixture/per-day P&L + signal trace rows for operator inspection.

- [ ] [strategy-service] P1. Cross-reference: extend `trace_all_carry_archetypes.py` to optionally invoke
      `trace_arbitrage_price_dispersion.py` for the cross-venue funding-spread variant. Don't fold the dispersion tracer
      INTO the carry tracer — different families.

- [ ] [VERIFY] P0.
      `python strategy-service/scripts/trace_arbitrage_price_dispersion.py --mode batch     --start-date 2024-01-01 --end-date 2024-01-07 --config-variant funding-rate-dispersion --asset-group defi`
      runs to completion + emits non-empty CSV/parquet output.

- [ ] [strategy-service] P1. Tests: `tests/unit/test_trace_arbitrage_price_dispersion.py` — verify CLI flags accepted,
      dry-run path emits a header row, error path raises `SystemExit(2)` on missing required flag.

**Code gates**: C4 — strategy-service `quality-gates.sh` Pass 1 green including the new test file. C5 — landed on
`live-defi-rollout`.

**Full-execution criterion** (per CLAUDE.md "Plans Run To Actual Completion" HARD RULE): tracer script runs end-to-end
against real backfilled MTDS + features data for a 1-week window; produces a CSV with at least one signal-emit row.

- **What ran**:
  `python strategy-service/scripts/trace_arbitrage_price_dispersion.py --mode batch --start-date 2024-01-01 --end-date 2024-01-07 --config-variant funding-rate-dispersion --asset-group defi --output-dir /tmp/arb_trace_2024_w1/`
- **Verification**: `wc -l /tmp/arb_trace_2024_w1/*.csv` returns ≥ 2 (header + ≥1 row); `head -3` shows columns
  `timestamp,signal_type,leg1_venue,leg2_venue,funding_spread_bps,leverage,simulated_pnl_usd,...`; sample row inspection
  confirms non-zero `funding_spread_bps` for at least one timestamp.

## Phase C — pnl-attribution-service rows for ARBITRAGE_PRICE_DISPERSION

- [ ] [pnl-attribution-service] P1. Add `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` handling to the service's
      archetype-aware P&L aggregator. Today the service has zero `ARBITRAGE_PRICE_DISPERSION` references in
      `pnl_attribution_service/` source. Likely surfaces: - Per-archetype P&L bucket (alongside `CARRY_STAKED_BASIS`,
      etc.) - Per-config-variant breakdown (`funding-rate-dispersion` vs other variants) - Output path:
      `gs://pnl-attribution-{pid}/by_strategy/ARBITRAGE_PRICE_DISPERSION/...`

- [ ] [pnl-attribution-service] P1. Tests:
      `tests/unit/test_archetype_pnl.py::test_arbitrage_price_dispersion_attribution`. Verify P&L bucket exists +
      attributes correctly given mock fills.

- [ ] [VERIFY] P0. After tracer (Phase B) emits rows for the 1-week window:
      `gcloud storage ls gs://${PID}-pnl-attribution/by_strategy/ARBITRAGE_PRICE_DISPERSION/...` returns non-empty;
      sample probe of one row confirms `archetype="ARBITRAGE_PRICE_DISPERSION"` + `config_variant=...` columns
      populated.

**Code gates**: C4 — pnl-attribution-service `quality-gates.sh` Pass 1 green. C5 — landed on `live-defi-rollout`.
**Business gate**: B4 — batch tracer P&L envelope per `funding-rate-dispersion` slot matches the simulated-fills
P&L (face-value zero-execution-alpha mode, per CLAUDE.md "Batch = Live").

**Full-execution criterion** (per CLAUDE.md "Plans Run To Actual Completion" HARD RULE): pnl-attribution-service
produces non-empty rows under `ARBITRAGE_PRICE_DISPERSION` for the same 1-week window the tracer covered;
archetype-bucket check passes.

- **What ran**: pnl-attribution-service
  `python -m pnl_attribution_service --mode batch --archetype ARBITRAGE_PRICE_DISPERSION --start-date 2024-01-01 --end-date 2024-01-07`
  (or VM equivalent if a launcher exists).
- **Verification**:
  `gcloud storage cat gs://${PID}-pnl-attribution/by_strategy/ARBITRAGE_PRICE_DISPERSION/year=2024/ month=01/<sample-day>.parquet | head`
  returns rows with `archetype="ARBITRAGE_PRICE_DISPERSION"` + `config_variant="funding-rate-dispersion"` +
  populated `realised_pnl_usd` + `attributed_strategy_alpha_usd`.

## Phase D — Stream B gate close

- [ ] [PM-plan] P0. After Phases A+B+C+E all ship: re-check Stream B gate in
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
      § Gate (line 168-170). Workspace grep `rg 'leveraged_funding_arb' --type py --type md` returns only: - the source
      plan + this finalisation plan + the original issue doc (historical context) - codex doc historical references with
      explicit "renamed to ARBITRAGE_PRICE_DISPERSION" annotations - archive/\* commits (frozen historical state)

- [ ] [PM-plan] P0. Flip the 3 deferred Stream B sister todos (lines 175-188) + the codex circular-ref P0 (lines
      155-157) in defi_archetypes plan from `[ ]` to `[x]` with this plan's commit shas as evidence. Per CLAUDE.md
      "Commit + Push + Flip" HARD RULE Half 2, the flip ships in a `docs(plans):` PM commit referencing each phase's
      code commits. Archive defi_archetypes plan only if Streams A/C/D/E are also complete; otherwise leave active.

## Phase E — codex SSOT updates (per "Post-Plan-Phase Codex Audit" HARD RULE)

Phase E may run in parallel with Phases B/C (no upstream dependency on artefacts) but MUST land before Phase D.

- [ ] [codex] P0. Resolve circular cross-reference at
      [`codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md:171-179`](../../codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md):
      remove the line _"Funding-rate arbitrage between perp venues (bidirectional funding capture) — `CARRY_BASIS_PERP`
      (cross-venue mode)"_ from the "Not in this archetype" section. The 2026-05-07 operator decision sent
      funding-rate-spread-as-price-dispersion HERE (ARBITRAGE_PRICE_DISPERSION with `funding-rate-dispersion`
      config variant); the redirect to CARRY_BASIS_PERP is the legacy framing. Leave the paired authoritative claim in
      [`carry-basis-perp.md:138-139`](../../codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md) only. This
      closes the parent plan's pending P0 codex todo at line 155-157.

- [ ] [codex] P0. In the same `arbitrage-price-dispersion.md` "Example instances" section (after L159
      `ARBITRAGE_PRICE_DISPERSION@multi-cex-btc-funding-usdt-prod`), add a new sub-section showing the
      `funding-rate-dispersion` config variant slot-label shape that strategy-service uses. Per Q2 resolution
      2026-05-09 the slot is **multi-venue universe + dynamic-best-pair selection**, NOT a fixed venue pair:

      ```
      Funding-rate dispersion (multi-venue universe + dynamic best-long/best-short — Stream B 2026-05-07):
        ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-btc-usdt-prod
        ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-eth-usdt-prod
        # config (operator-confirmed 2026-05-09):
        #   venue_universe         = [bybit, deribit, binance, okx, hyperliquid, aster]
        #   venue_selection_mode   = dynamic-best-long-short        (per funding cycle, ~8h)
        #   target_leverage        = 5.0
        #   vol_cap_clamp_feature  = realized_vol_20 (1h candles)   (short-term, NOT 60-day)
        #   vol_cap_clamp_threshold_pct = 80.0  OR  vol_regime_zscore_20 > 2.0  (any breach → clamp)
        #   vol_cap_clamp_target_leverage = 1.0
        #   bidirectional_funding  = true                           (capture both spread signs)
        #   entry_filter_sign_match = price_spread == funding_spread (skip cycle if signs differ)
      ```

- [ ] [codex] P1. Touch-check
      [`codex/09-strategy/architecture-v2/category-instrument-coverage.md § 11`](../../codex/09-strategy/architecture-v2/category-instrument-coverage.md):
      ensure the funding-rate-dispersion variant is enumerated under ARBITRAGE_PRICE_DISPERSION's coverage matrix.

- [ ] [VERIFY] P0.
      `rg 'CARRY_BASIS_PERP.*funding|funding.*CARRY_BASIS_PERP'     codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`
      returns zero hits (the circular pointer is gone).
      `rg 'funding-rate-dispersion'     codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`
      returns ≥ 1 hit.

**Full-execution criterion**: codex docs reflect the new SSOT (single authoritative claim in `carry-basis-perp.md`;
canonical example in `arbitrage-price-dispersion.md`). **What ran**: surgical edits + workspace grep verification.
**Verification**: both grep commands above pass.

## Done definition

1. ✅ Phase A — strategy-service slot for `funding-rate-dispersion` shipped + factory wired + QG green (C4 → C5 on
   `live-defi-rollout`).
2. ✅ Phase B — `trace_arbitrage_price_dispersion.py` script ships + runs end-to-end on real backfill window (C4 → C5;
   Full-execution criterion met with the 2024-W1 batch run).
3. ✅ Phase C — pnl-attribution-service ARBITRAGE_PRICE_DISPERSION rows ship + 1-week sample probe non-empty (C4 → C5;
   B4 batch-vs-simulated-fills parity confirmed).
4. ✅ Phase D — Stream B gate closes; workspace grep for `leveraged_funding_arb` returns only historical refs; parent
   plan's 4 deferred sister todos flipped to `[x]` with this plan's commit shas as evidence.
5. ✅ Phase E — codex SSOT updates land; circular cross-ref resolved; `funding-rate-dispersion` example slot shape
   canonicalised in `arbitrage-price-dispersion.md`.

**Full-execution criterion** (per PLAN_FORMAT.md § 8 + "Plans Run To Actual Completion" HARD RULE):

- ✅ **Tracer ran-to-completion against real infra**.
  - **What ran**:
    `python strategy-service/scripts/trace_arbitrage_price_dispersion.py --mode batch --start-date 2024-01-01 --end-date 2024-01-07 --config-variant funding-rate-dispersion --asset-group defi`
  - **Verification**: tracer CSV non-empty; pnl-attribution rows populated for the same window; deployment-UI drilldown
    shows ARBITRAGE_PRICE_DISPERSION bucket under DeFi.
- ✅ **Workspace grep gate**.
  - **What ran**: `rg 'leveraged_funding_arb' --type py --type md`
  - **Verification**: only historical-context hits remain (source plan + this plan + archived issue + codex historical
    annotations); no standalone-archetype refs.
- ✅ **Codex circular-ref gate**.
  - **What ran**:
    `rg 'CARRY_BASIS_PERP.*funding|funding.*CARRY_BASIS_PERP' codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`
  - **Verification**: zero hits.

**Handoff exception(s)**: none. Every phase runs in this plan; no deferral to a downstream plan beyond the
operator-decision items in Open Questions (which are A.6 follow-ups, not handoffs).

## Repos touched + commit-evidence target

| Repo                    | Phase | Expected commit shape                                                                      | Code gate |
| ----------------------- | ----- | ------------------------------------------------------------------------------------------ | --------- |
| strategy-service        | A     | `feat(strategies): add ARBITRAGE_PRICE_DISPERSION funding-rate-dispersion slot`       | C5        |
| strategy-service        | A.6   | `feat(strategies): swap funding-rate-dispersion slot placeholders → confirmed`        | C5        |
| strategy-service        | B     | `feat(scripts): add trace_arbitrage_price_dispersion.py`                                   | C5        |
| pnl-attribution-service | C     | `feat(pnl-attribution): add ARBITRAGE_PRICE_DISPERSION archetype bucket`                   | C5        |
| unified-trading-pm      | E     | `docs(codex): resolve arbitrage-price-dispersion ↔ carry-basis-perp circular ref`         | n/a       |
| unified-trading-pm      | E     | `docs(codex): add funding-rate-dispersion example slot to ARBITRAGE_PRICE_DISPERSION` | n/a       |
| unified-trading-pm      | D     | `docs(plans): close Stream B gate in defi_archetypes_canonicalisation`                     | n/a       |

**Commit cadence note** (per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" HARD RULE Half 1): each row above is a
single shippable unit; commit + push per row, do not batch across rows. Plan-flip in this plan + parent plan ships in
the SAME logical unit as the code commit per Half 2.

## Deferred work after this plan ships (per CLAUDE.md "Plan Archival" HARD RULE)

All 6 open questions resolved 2026-05-09 → no operator-blocked deferrals. Carryover candidates:

| Phase / item                                   | Status                              | Successor / blocker                                                                                             |
| ---------------------------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Phase A.6 — ETH/USDT slot extension            | `todo` (unblocked; ships post-A)    | Same plan; small follow-up commit after BTC/USDT slot is green                                                  |
| Live cutover dry-run (paper-trade integration) | `deferred-after-2026-05-23-cutover` | `master_to_live_defi_2026_05_23.md` Group F item 17 (paper-trade smoke) consumes this archetype's tracer output |

If A.6 ships within this plan's lifetime, that row collapses to "no carryover" and this section is trimmed at archive
time per the "Plan Archival" HARD RULE migration discipline.

## Cross-references

- [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
  — Stream B parent (this plan is the named successor for the 3 deferred sister todos + the lingering codex P0)
- [`defi_master_2026_05_07.md`](defi_master_2026_05_07.md) — master archetype owner; L152-153 already uses
  `ARBITRAGE_PRICE_DISPERSION` per 2026-05-08 rename
- [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) — May-23 cutover master; this plan unblocks
  the `ARBITRAGE_PRICE_DISPERSION` half of the "2 DeFi archetypes live" deliverable
- UAC `unified_api_contracts/internal/architecture_v2/enums.py:68` — SSOT enum entry (already shipped 2026-05-07)
- [`codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`](../../codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md)
  — codex SSOT updated by Phase E
- [`codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md)
  — paired authoritative claim survives here after Phase E circular-ref fix
