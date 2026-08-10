---
doc_type: codex-ssot
title: Sports odds-feature naming scheme (UAC `OddsFeaturesMixin`/`SportsFeatureVector` as SSOT)
summary: >-
  The canonical field-naming scheme for sports odds features, decided 2026-07-23 (operator ruling BLK-a1ce4719) and
  landed across UAC/features-service/ml-service/strategy-service by
  `sports_odds_feature_naming_canonicalization_2026_07_21.md`. UAC's `OddsFeaturesMixin` (part of `SportsFeatureVector`)
  is the SSOT; features-service's exporter/calculator, ml-service's loader, and strategy-service's archetype engines +
  legacy subscriber all migrated to match. Prevents a 5th orphaned naming dialect from being reintroduced by future
  archetype/consumer work.
status: current
nature: ssot
asset_group: [sports]
stage: [data]
repos: [unified-api-contracts, features-service, ml-service, strategy-service]
scope: [engineer, admin]
tags: [sports, odds-features, schema-parity, naming-convention, uac-ssot]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/market-making-prediction.md,
    /plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md,
    /plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md,
  ]
created: "2026-08-10"
authoritative_for: [sports odds-feature field naming scheme]
referenced_by: []
owner: sports_master
last_reviewed: "2026-08-10"
code_refs:
  [
    unified-api-contracts/unified_api_contracts/internal/domain/features_sports/_features_venue_referee_player_odds.py,
    features-service/features_service/sports/calculators/odds_columns.py,
    features-service/features_service/sports/exporters/odds_features_exporter.py,
    ml-service/ml_service/training/app/core/sports_feature_loader.py,
    strategy-service/strategy_service/adapters/sports_feature_subscriber.py,
  ]
---

# Sports odds-feature naming scheme

UAC's `OddsFeaturesMixin` (part of `SportsFeatureVector`) is the SSOT for sports odds-feature field names. Every real
consumer — features-service's exporter/calculator (producer), ml-service's `SportsFeatureLoaderMixin` (loader, with loud
schema validation at the read boundary — a naming mismatch raises, it never silently returns `None`/`KeyError`), and
strategy-service's v2 archetype engines (`SportsValueBettingEngine`/`SportsArbDutchingEngine`) plus the legacy
`sports_feature_subscriber.py` — has been migrated to match. Do not reintroduce a divergent naming convention in any new
sports odds-feature consumer or producer; extend the scheme below instead.

## Scheme

`<category>_<metric>[_<outcome>][_<venue>]`, `outcome` ∈ `{home, draw, away}` lowercase (matches the per-outcome
dict-key shape every consumer expects), `venue` only present for per-venue fields (the UAC-canonical venue token, e.g.
`pinnacle`).

| Category prefix                                                 | Meaning                                                                                            | Example                                                                                                                                             |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `prob_implied_`                                                 | raw implied probability from vig-laden odds                                                        | `prob_implied_home`                                                                                                                                 |
| `prob_fair_`                                                    | vig-removed fair probability                                                                       | `prob_fair_home`                                                                                                                                    |
| `prob_sharp_` / `prob_soft_`                                    | tier-consensus probability                                                                         | `prob_sharp_mean_home`, `prob_soft_consensus_home`                                                                                                  |
| `odds_market_`                                                  | market-structure scalars (not outcome-indexed)                                                     | `odds_market_vig`, `odds_market_overround`, `odds_market_vig_pct`, `odds_market_efficiency`, `odds_market_complexity`, `odds_market_spread_current` |
| `odds_decimal_`                                                 | consensus/best decimal odds per outcome (`SportsValueBettingEngine`'s `decimal_odds_<outcome_id>`) | `odds_decimal_home`                                                                                                                                 |
| `odds_decimal_<outcome>_<venue>`                                | per-bookmaker raw decimal odds (`SportsArbDutchingEngine`'s `<outcome_id>_<venue>` need)           | `odds_decimal_home_pinnacle`                                                                                                                        |
| `odds_disagreement_` / `odds_variance_` / `odds_fragmentation_` | cross-bookmaker dispersion                                                                         | `odds_disagreement_home`, `odds_fragmentation_home`, `prob_disagreement_std_home`                                                                   |
| `odds_movement_`                                                | closing-minus-opening / directional                                                                | `odds_movement_home`, `odds_movement_pinnacle_diff_home`                                                                                            |
| `odds_velocity_` / `odds_acceleration_`                         | rate / rate-of-rate of change                                                                      | `odds_velocity_home_24h_to_6h`, `odds_acceleration_home`, `prob_velocity_home`                                                                      |
| `odds_clv_`                                                     | closing-line-value family                                                                          | `odds_clv_home`, `odds_clv_sharp_home`, `odds_clv_direction_home`                                                                                   |
| `odds_steam_`                                                   | steam-move detection                                                                               | `odds_steam_detected_home`, `odds_steam_magnitude_home`                                                                                             |
| `odds_book_count_`                                              | bookmaker-tier population counts                                                                   | `odds_book_count_sharp`                                                                                                                             |
| `odds_<market>_`                                                | alternate-market blocks keep their existing market prefix under the `odds_` namespace              | `odds_asian_handicap_line`, `odds_btts_yes`                                                                                                         |

`ht_` (half-time) as a name-baked prefix is retired — half-time context is a `period` dimension on the row, not a naming
prefix (folds `ht_odds_home_implied`-style legacy names into the same `prob_implied_home` scheme).

This is a **generative rule** — apply it to any new odds-feature field rather than treating the table as exhaustive.
`outcome`/`venue` tokens are always lower-case, matching the workspace's sports data_type casing convention.

## Provenance

Decided 2026-07-23 (operator ruling BLK-a1ce4719 on
`/plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`), migrated across all 4 repos by
`sports_odds_feature_naming_canonicalization_2026_07_21.md` (archived — see that plan's Progress Log for the full
per-commit migration trail: `unified-api-contracts@689efa54`, `features-service@0ded2449`+`@e240eca2`,
`ml-service@91f031a`+`@07976ae`+`@10e219f`, `strategy-service@4c55438c`).
