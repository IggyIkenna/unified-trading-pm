---
doc_type: issue
title: >-
  cefi/sports/prediction first-ever distinct-value census (2026-07-30) — small residual venue/instrument_type/data_type
  drift not covered by any existing tracked finding
summary: >-
  Phase G of data_pipeline_reconciliation_skill_2026_07_20.md ran the /data-pipeline-reconciliation distinct-value
  census (G1) for cefi/tradfi/sports/prediction for the first time ever (only defi had been measured, H6 in
  reference-defi.md). tradfi's findings and sports' instrument_type findings turned out byte-identical to two
  already-open 2026-07-28 issue docs (tradfi_distinct_values_net_new_clusters,
  sports_instrument_type_market_token_ssot_gap) — good independent confirmation, no new action there. This doc captures
  the genuinely NEW small-scale residuals across the other 3 AGs that no existing doc covers: cefi venue
  underscore/hyphen dupes + a lowercase `spot` instrument_type + 3 wrong-axis values leaked into the chain column; 6
  sports bookmaker venues not yet in the accepted-alias list; and prediction instrument_type/data_type case drift. Every
  item is small-scale (≤4,933 rows out of each AG's multi-million row corpus) — none is data-correctness-critical, all
  are canonicalisation hygiene.
status: open
nature: issue
asset_group: [cefi, sports, prediction]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [canonicalisation, census, distinct-values, venue, instrument_type, data_type, cefi, sports, prediction]
related:
  [
    data_pipeline_reconciliation_skill_2026_07_20,
    sports_instrument_type_market_token_ssot_gap_2026_07_28,
    tradfi_distinct_values_net_new_clusters_2026_07_28,
    cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "operator request 2026-07-30 — audit /data-pipeline-reconciliation's coverage against its own stated criteria across
  all 5 AGs"
resolved_by:
---

# cefi/sports/prediction first census — small residual drift

> **Priority rationale** (per `/codex/11-project-management/plan-priority-tier-and-dispatch-ordering.md`): not a
> CI/audit escalation; within the asset-group tier ordering cefi ranks second only to cross-cutting, but every item
> below is small-scale canonicalisation hygiene, not data-completion/backfill-critical — matches the **P2** precedent
> set by the two sibling 2026-07-28 census-finding docs this one is modeled on.

## cefi (9,492,020 rows measured)

1. **Venue underscore/hyphen dupes** — `POLYMARKET_PERP` (4 rows) / `KALSHI_PERP` (4 rows) are the same venues as the
   registered `POLYMARKET-PERP` (1,020 rows) / `KALSHI-PERP` (1,666 rows), wrong separator. `OKX-OPTIONS` (2 rows) is
   not in `VENUES_BY_ASSET_GROUP['cefi']` at all.
2. **`instrument_type=spot` (4,923 rows, lowercase)** — canonical is `SPOT_PAIR`/`SPOT_ASSET`, not `SPOT`; genuinely
   different token, not a case-only variant.
3. **3 wrong-axis values in the `chain` content column** — `FUTURES` (8 rows), `POLYMARKET_PERP` (3 rows), `KALSHI_PERP`
   (3 rows). Refines `reference-cefi.md` H7 ("chain content is display residue, not a defect") — these 3 specific values
   are NOT residue, they look like instrument_type/venue strings landing in the wrong column entirely.
4. **5 stray candle-timeframe-shaped `data_type` values** (2 rows each) — `ohlcv_5m`/`ohlcv_1h`/`ohlcv_1d`/`ohlcv_15s`/
   `ohlcv_15m` on the raw-tick bucket, vs the legitimate `ohlcv_1m` (4,604 rows). Likely a pre-MDPS-candle-layer
   historical/test artifact.

## sports (628,349 rows measured)

5. **6 non-canonical bookmaker venues not yet in `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS`** — `FOOTYSTATS`
   (22,962 rows), `SPORT888` (20,066), `BET888SPORT` (18,903), `LADBROKES_UK` (13,560), `LADBROKES` (12,210 — likely the
   same bookmaker as `LADBROKES_UK` under two spellings, needs a human call on which is canonical), `SMARKETS` (8,518).
   (The 7th non-canonical venue, `KALSHI` at 20,785 rows, is the ALREADY-TRACKED cross-AG bleed — archived
   `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` todo 15, `row_count=0` throughout, no
   new action here.)

## prediction (1,661,267 rows measured)

6. **`instrument_type` case drift** — `prediction_market` lowercase (9,720 rows) vs canonical `PREDICTION_MARKET`
   (781,626 rows); `prediction` (76 rows, truncated/wrong token).
7. **`data_type=prediction_trades`** (2,477 rows) — not in `DATA_TYPES_BY_ASSET_GROUP['prediction']`; looks like a
   redundant/legacy-prefixed variant of the canonical `trades` (753,064 rows).

## Todos

- [ ] [DATA] P2. **Resolve cefi items 1-4** — decide per item whether to (a) register a venue alias
      (`CEFI_VENUE_ACCEPTED_NONCANONICAL_ALIASES`) for the underscore/hyphen dupes, (b) fix the writer emitting
      `instrument_type=spot`, (c) root-cause the 14 wrong-axis `chain` values (repo: unified-api-contracts /
      market-tick-data-service). Gate: each of the 4 items has a stated disposition (fix / register-exception /
      quarantine), not left open-ended.
- [ ] [DATA] P2. **Resolve sports item 5** — for each of the 6 bookmaker venues, either register it in
      `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS` (if it's a real, distinct bookmaker) or fix the writer (if
      `LADBROKES`/`LADBROKES_UK` should collapse to one spelling) (repo: unified-api-contracts). Gate: distinct-value
      census re-run shows 0 non-canonical venues for sports outside the KALSHI cross-AG-bleed exception.
- [ ] [DATA] P2. **Resolve prediction items 6-7** — fix the writer path(s) emitting lowercase
      `prediction_market`/truncated `prediction`/`prediction_trades` (repo: market-tick-data-service). Gate: distinct-
      value census re-run shows 0 non-canonical instrument_type/data_type values for prediction.
