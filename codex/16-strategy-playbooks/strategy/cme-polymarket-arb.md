---
scope: [engineer]
---

# CME × Polymarket Cross-Venue Event-Contract Arb — Playbook

> **Status (2026-05-22)**: Phases 1–5 shipped. Engine live in strategy-service. All 9 roots wired in
> `cme_polymarket_link.py`. Instruments-service catalog backfill + MTDS CLOB tick history for 7 new groups pending (VM
> launch not yet dispatched). Full onboarding (paper-trade soak + DART gate) post-cutover.
>
> **Shipped**: Phase 1 UAC@b95d146 · Phase 2 UAC@77facd65+UAC@9c491bdd (FULL: all 9 roots) · Phase 3 MTDS@b59b63e ·
> Phase 4 instruments-service@7a3db05 · Phase 5 strategy-service@2c59f2ce.

**Plan SSOT**:
[`plans/active/cme_polymarket_arb_2026_05_08.md`](../../../plans/active/cme_polymarket_arb_2026_05_08.md).

**Source RFC**:
[`plans/archive/issues/cme_event_contracts_cross_venue_arb_shard_design_2026_05_08.md`](../../../plans/archive/issues/cme_event_contracts_cross_venue_arb_shard_design_2026_05_08.md)
(26KB — read for full design intent + per-phase blast-radius analysis).

**Composes with**:

- [`category-instrument-coverage.md`](../../09-strategy/architecture-v2/category-instrument-coverage.md) § "Family 4:
  Arbitrage / Structural" → archetype `ARBITRAGE_PRICE_DISPERSION` row "TradFi ↔ Prediction event_contract" +
  slot-label cluster `cme-polymarket-*-up-down-daily-*`.
- [`per-category-bucket-layouts.md`](../../02-data/per-category-bucket-layouts.md) § "Multi-axis correction" → "TradFi
  EVENT_CONTRACT" shard atom bullet.

## TL;DR — what the strategy does

Detect basis between CME event-contract implied probability and the equivalent Polymarket canonical-question-group
implied probability on the same underlying (BTC, SPX, etc.) for the same resolution date. When the gap exceeds the
`max_basis_threshold` (after fees + slippage assumption), enter paired positions: BUY the cheaper venue's YES + SELL (or
hedge equivalent) the expensive venue's YES. Both legs cleared / settled on the underlying close per exchange-published
spec — no oracle-dispute risk on the CME leg.

**Strategy archetype name**: `ARBITRAGE_CROSS_DOMAIN_EVENT` (UAC `StrategyArchetype` enum; engine class
`ArbitrageCrossDomainEventEngine` in `strategy_service/engine/strategies/v2/arbitrage_structural/cme_polymarket.py`).
Registered in `ARCHETYPE_ENGINE_REGISTRY` + `GREENFIELD_ARCHETYPES` + `KELLY_FRACTION_BY_ARCHETYPE` (half-Kelly,
`TIER_STABLE_STRUCTURAL`). 3 seed rows in `TARGET_UNIVERSE` catalog (2 ECES + 1 ECBTC).

**Underlyings (9 CME roots)** — covered by the
`unified_api_contracts.registry.tradfi_instrument_universe._CME_EVENT_CONTRACTS` SSOT:

| CME root | Underlying  | Polymarket canonical_question_group equivalent | Phase 1 link status                         |
| -------- | ----------- | ---------------------------------------------- | ------------------------------------------- |
| ECES     | E-mini SPX  | `SPX_UP_DOWN_DAILY`                            | already exists                              |
| ECNQ     | E-mini NDX  | `NDX_UP_DOWN_DAILY`                            | already exists                              |
| ECBTC    | Bitcoin     | `BTC_UP_DOWN_DAILY`                            | already exists                              |
| ECRTY    | E-mini RUT  | `RUT_UP_DOWN_DAILY` _(needs backfill)_         | predictions_master Phase 5 → blocks Phase 2 |
| ECYM     | E-mini Dow  | `DJIA_UP_DOWN_DAILY` _(needs backfill)_        | predictions_master Phase 5 → blocks Phase 2 |
| ECGC     | Gold        | `GOLD_UP_DOWN_DAILY` _(needs backfill)_        | predictions_master Phase 5 → blocks Phase 2 |
| ECCL     | Crude WTI   | `CRUDE_OIL_UP_DOWN_DAILY` _(needs backfill)_   | predictions_master Phase 5 → blocks Phase 2 |
| ECNG     | Natural gas | `NATGAS_UP_DOWN_DAILY` _(needs backfill)_      | predictions_master Phase 5 → blocks Phase 2 |
| EC6E     | Euro FX     | `EUR_UP_DOWN_DAILY` _(needs backfill)_         | predictions_master Phase 5 → blocks Phase 2 |

## Basis-calc reference

For a paired `(CME root, resolution_date, strike_threshold)` with YES/NO contracts on each side:

```text
cme_implied_p_yes      = cme_yes_mid / (cme_yes_mid + cme_no_mid)
poly_implied_p_yes     = poly_yes_mid_for_equivalent_threshold
basis_bps_annualised   = (cme_implied_p_yes - poly_implied_p_yes) * 10_000
                          * (365 / days_to_resolution)
```

**Threshold to fire**: `abs(basis_bps_annualised) >= max_basis_threshold` (plan-default ~50bps for liquid roots —
calibrate per archetype config). Below threshold the leg-pair is not entered (transaction-cost defeat).

## Leg-balancing assumptions

- **Notional matching**: CME contracts are integer count × $contract_size; Polymarket shares are fractional. Pair must
  match $ notional per leg ± rounding tolerance (default 1%). Use the smaller leg's $ size to constrain the larger.
- **Expiry alignment**: pair only fires when the CME `resolution_date` matches the Polymarket market's `resolution_time`
  to the same calendar UTC day. CME daily binaries resolve at exchange-published settlement window; Polymarket resolves
  on UMA oracle finalisation. Use `linked_canonical_question_group` (Phase 2) to look up the matching market_id.
- **Strike matching**: CME strikes are pre-set by the exchange; Polymarket strikes are market-defined. Default link is
  at canonical-group grain (`BTC_UP_DOWN_DAILY`); per-strike alignment is a strategy-side fair-value computation, not
  instrument-discovery (full content Phase 5).
- **Settlement-rule equivalence**: both venues settle on the underlying's close per a published spec. CME ClearPort is
  exchange-determined (no oracle dispute risk); Polymarket is UMA-bond-arbitrated. The strategy treats them as a paired
  hedge ONLY when settlement-rule equivalence is asserted in `linked_canonical_question_group` metadata.

## Kill-switch rules

- **Per-leg fill failure**: if the CME leg fills but the Polymarket leg does not within `max_pair_complete_seconds`
  (default 60s), unwind the CME leg at market and emit `PAIR_COMPLETION_FAILED`. Do NOT carry single-leg directional
  risk.
- **Mid-position resolution divergence**: if the underlying's settlement source disputes between CME ClearPort and
  Polymarket UMA (rare — settlement-rule equivalence ought to prevent it), kill-switch fires `RESOLUTION_DIVERGENCE` and
  the position is held flat until a manual operator decision.
- **Liquidity floor**: per-leg `min_liquidity_per_leg` check on top-of-book size; below the floor, the archetype skips
  the trade.
- **Per-trade clip**: `max_clip_usd` (small for thin liquidity — default $5K-$10K per archetype config). Total exposure
  cap across all in-flight pairs governed by risk-and-exposure-service standard limits.

## DART manual-trade gate (live-only)

`cme_polymarket_event_arb` is **not a fast-path archetype**. Standard onboarding checklist applies before live trading:
paper-trade in staging (min 100 simulated pairs, hit-rate ≥60%, P&L >0 net of fees), soak-test (7-day continuous batch
run on captured data with operator-grade batch-vs-live reconciliation), DART manual-trade gate per
`master_to_live_defi_2026_05_23` plan Group F + G live-only prerequisites, operator approval. Out of scope for the
May-23 cutover.

## Anti-patterns (do NOT do this)

- **Don't skip the canonical-question-group cross-link**: directly hand-mapping CME root → Polymarket market_id at
  strategy level bypasses the UAC SSOT. Use `linked_question_group(cme_root)` from
  `unified_api_contracts.canonical.crosscutting.cme_polymarket_link` (Phase 2 — UAC@77facd65+UAC@9c491bdd; all 9 roots
  wired as of 2026-05-22; IS catalog backfill + MTDS CLOB for 7 new groups pending VM dispatch).
- **Don't treat ECBTC.OPT as a vanilla option**: per Phase 1, the Databento classifier emits
  `InstrumentType.EVENT_CONTRACT` (not OPTION) for EC\* roots on `instrument_class=BAG` (current Databento encoding) or
  legacy `instrument_class=O`. Downstream features that filter by `instrument_type` MUST treat EVENT_CONTRACT distinctly
  — greeks don't apply the same way (binary payoff, not piecewise-linear).
- **Don't reuse the 11-cluster ES.OPT taxonomy for cluster validation**: event contracts cluster by
  `(root, resolution_date, strike_threshold)`, NOT the ES.OPT weekly/EOM scheme. Phase 1A of writegate cluster
  validation applies but with the EVENT_CONTRACT-specific kwargs:
  `expected_root_clusters[(root, resolution_date)] = {strike_threshold: 2}`,
  `cluster_extractor=lambda row: f"{row.strike_threshold}:{row.outcome}"`.
- **Don't try this without paper-trade soak**: thin liquidity (event contracts launched 2022-2023; Databento coverage
  2025-09-28 onward → ~7 months of history at plan time). Risk-managed sizing required; small clip per leg.
