---
scope: [engineer, admin]
doc_kind: gaps_register
status: active
ssot_for: prediction_market_codification_gaps
execution:
  owner: predictions-master owner (Ikenna; cross-ref `plans/active/predictions_master_2026_05_07.md`)
  cadence:
    per-PR — every PR touching prediction registries / handlers / UAC predictions surface MUST review this gaps
    register; weekly sweep during the May-23 cutover window to close gaps as they land
  verifier: |
    Each gap (G1..GN) is closed by (a) deleting from this register + (b) landing the corresponding UAC / UIC /
    features-cross-instrument change in the same logical unit (per CLAUDE.md "Commit + Push + Flip" rule).
    Reviewers reject PRs that land the change but don't delete the gap row, and vice versa.
  last_executed: 2026-05-07 (file creation); ongoing per-PR review until predictions_master cutover
---

# Prediction markets — codification gaps

> Scoped register of implementation gaps needed to bring prediction markets (Polymarket, Kalshi) to parity with CeFi,
> DeFi, and TradFi venues in the registries. Doctrine lives in
> [`prediction-markets.md`](../architecture-v2/cross-cutting/prediction-markets.md); this file lists what is missing
> from the code/config surface.
>
> **This is the gaps SSOT for prediction-market integration.** `prediction-markets.md` cites this file in place of
> inline TODO-CODIFY blocks. Close a gap by deleting it from this register and landing the corresponding UAC / UIC /
> features-cross-instrument change.

## G1 — Use-case classification

Three-tier classification (`FEATURE` / `TRADABLE` / `ARB_SURFACE`) has no machine-readable form.

Required:

- Add `PredictionMarketUseCase` enum to UIC: `FEATURE`, `TRADABLE`, `ARB_SURFACE`, `BOTH`.
- Add `equivalent_instrument_type` field to `CanonicalPredictionMarket`: maps to traditional instrument if arb is
  possible (e.g., `SPX_BINARY_CALL`, `FED_FUNDS_FUTURE`, `BETFAIR_BACK`).
- Add `domain_mapping` field linking to strategy domains.
- Cross-platform matching rules: normalise event descriptions to canonical form for matching.

Owner: UIC + features-cross-instrument. Consumed by: prediction-arb strategy + feature calculators.

## G2 — Instrument ID convention

Canonical `{VENUE}:{MARKET_TYPE}:{EVENT_SLUG}@{OUTCOME}` pattern (see
[`prediction-markets.md` §Instrument ID Convention](../architecture-v2/cross-cutting/prediction-markets.md#instrument-id-convention))
is not in UIC's instrument ID rules. `CanonicalPredictionMarket` in `prediction_mapping.py` generates deterministic IDs
that don't match the standard instrument-key format.

Required: add the pattern to `unified-config-interface` instrument-ID rules; back-fill existing prediction-market IDs.

## G3 — Semantic market matching

"Bitcoin above $95k on March 20" and "BTC price exceeds 95000 by end of March 20" are the same market. No grouping
exists.

Required:

- Rule-based normalisation: strip dates, amounts, standardise asset names.
- Group markets by `(asset, direction, threshold, expiry_bucket)`.
- Aggregate implied probabilities across grouped markets for stronger signal.
- Track historical accuracy per market group (calibration curve).

Owner: features-service (cross-instrument family).

## G4 — Automated market classifier

Required: `prediction_market_classifier.py` in features-service (cross-instrument family) that periodically pulls all
markets from Polymarket + Kalshi, classifies them against G1, identifies cross-platform matches per G3, and publishes a
classified market registry to GCS. That registry becomes the SSOT for which prediction markets are useful and how.

## G5 — Venue registry wiring

Polymarket and Kalshi live in `PLANNED_VENUES`. Until they move to `VENUE_REGISTRY` with capability declarations,
`get_adapter()` cannot instantiate.

Required: move both into `VENUE_REGISTRY`, land capability declarations, wire reference-data + execution adapters.

## G6 — Kalshi testnet

`demo-api.kalshi.com` exists and does not require real money.

Required: register as the testnet equivalent in the testnet registry alongside Polymarket's Amoy testnet.

## G7 — Historical data pipeline

Polymarket prices-history API has 12h+ granularity for resolved markets. Fine-grained history requires a WebSocket
recorder. Kalshi has 1-min candlestick history endpoints.

Required:

- Build a Polymarket WebSocket recorder that persists to MTDS for fine-grained history.
- Adopt Kalshi's 1-min candlestick endpoints for backfill and live ingestion.
- Align both into the standard MTDS market-tick schema.

Owner: MTDS + features-service (cross-instrument family).

## Closing gaps

When a gap ships, delete it from this file in the same PR that lands the implementation. Keep this register under 15
entries. Longer backlogs live in the plan directory, not here.
