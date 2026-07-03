---
doc_type: plan
title: sports-integration-04-feature-calculators-full
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-25'
remaining_todos_consolidated_into: consolidated_sports_prediction_pipeline_2026_04_15
superseded_by: [consolidated_sports_prediction_pipeline_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview: 'Port remaining feature calculators from archived new-sports-batting-services to reach

  1000+ feature target. Audit each of 17 archived calculators vs 21 FSS calculators,

  port missing features, vectorize .iterrows() usage, complete halftime + odds multi-horizon.

  NOTE: Archived calculators exist in archive/sports_audit_data/. Some team and odds

  features already ported. Calculator count audit vs 1000+ target still needed.

  '
type: code
epic: epic-code-completion
completion_gates: {code: C4, deployment: none, business: B3}
repo_gates:
- {repo: features-sports-service, code: C0, notes: 'Port missing features, vectorize calculators'}
- {repo: unified-api-contracts, code: C0, notes: Schema additions for new feature fields if needed}
depends_on: [sports-integration-03-features-provider-integration]
isProject: false
todos:
- {id: p1-calculator-audit, content: "- [x] [AGENT] P0. Compare archived vs FSS calculators.\n  DONE (2026-04-03): Full audit complete.\n  | Calculator | Archived | FSS  | Gap   | Status     |\n  | Team       | 171      | 118  | -53   | GAPS       |\n  | Halftime   | 69       | 39   | -30   | GAPS       |\n  | Odds       | 53       | 137  | +84   | ENHANCED   |\n  | Weather    | 9        | 5    | -4    | MINOR GAPS |\n  Team missing: rolling windows (last1/3/5/season for shots, possession, xG conceded),\n  velocity features (goals_trend_last10, xg_trend_last10), consistency (std dev),\n  advanced stats (save%, pass accuracy, blocks).\n  Halftime missing: goal timing (early/late flags), substitution patterns, comeback\n  vulnerability, 2nd-half Poisson predictions, red card flags.\n  Weather missing: binary flags (is_hot/cold/windy/adverse_weather).\n  Total current: ~299 features. Target: 1000+. Gap: ~701 features to port.\n", status: done}
- {id: p2a-team-features, content: "- [x] [AGENT] P1. Port missing team features from archived team.py (1813L).\n  DONE (2026-04-03): 54 new features ported across 4 files:\n  team_form.py +32 (PPG rolling, streaks, cards, corners, rest/congestion),\n  team_goals.py +6 (failed_to_score_rate, shots_per_goal, conversion_rate),\n  team_derived.py +10 (velocity/trend features, consistency std dev),\n  advanced_stats_calculator.py +6 (saves_per_game, save_pct, offsides).\n  Total team features: ~223 (was 118). Exceeds archived 171.\n", status: done, blocked_by: p1-calculator-audit}
- {id: p2b-halftime-features, content: "- [x] [AGENT] P1. Port missing halftime features from archived halftime.py (1200L).\n  DONE (2026-04-03): 67 new features ported:\n  HALFTIME_COLUMNS: 79 (was 39). HT_FEATURE_COLUMNS: 45 (was 18).\n  Score state flags (3), card features (5), goal timing per-team (5),\n  per-team HT subs (4), historical HT patterns (16), 2nd-half Poisson\n  predictions (7). Poisson PMF uses math.exp/factorial (no scipy dep).\n  Comeback probability via CDF complement. All vectorized.\n", status: done, blocked_by: p1-calculator-audit}
- {id: p2c-odds-features, content: "- [x] [AGENT] P1. Port odds multi-horizon features from archived odds.py (373L).\n  DONE (2026-03-28 + 2026-04-03): FSS odds_calculator produces 137 features\n  (was 53 archived). Includes: T-24h/T-6h/T-1h/T-0 features, bookmaker tier\n  consensus (16 cols), opening odds (6 cols), CLV features (9 cols),\n  velocity/acceleration, steam detection.\n", status: done, blocked_by: p1-calculator-audit}
- {id: p2d-weather-features, content: "- [x] [AGENT] P1. Port weather features from archived weather.py (277L).\n  DONE (2026-04-03): 4 binary flags added: is_hot_weather (>30°C),\n  is_cold_weather (<5°C), is_windy (>40km/h), is_adverse_weather (any extreme).\n  WEATHER_COLUMNS: 9 (was 5). Matches archived count exactly.\n", status: done, blocked_by: p1-calculator-audit}
- {id: p2e-bookmaker-tier-tagging, content: "- [x] [AGENT] P0. Wire BookmakerTier classification into FSS odds calculator.\n  DONE (2026-04-03): compute_tier_features() added to odds_calculator.py.\n  Imports classify_bookmaker() from UAC. Groups by fixture, classifies each\n  bookmaker as SHARP/EXCHANGE/SOFT, computes: sharp_consensus_*, soft_consensus_*,\n  exchange_price_*, sharp_soft_delta_*, sharp_disagreement_*, soft_disagreement_*,\n  bookmaker_count_sharp/exchange/soft/total. 16 new columns.\n  File: features_sports_service/calculators/odds_calculator.py\n", status: done}
- {id: p2f-ht-xg-from-shots, content: "- [x] [AGENT] P1. Derive halftime xG from Understat per-shot data.\n  DONE (2026-04-03): compute_ht_xg_from_shots() in ht_features.py.\n  Filters shots where minute < 45, sums xG per team. Returns ht_xg_home,\n  ht_xg_away, ht_shot_count_home, ht_shot_count_away.\n  File: features_sports_service/calculators/ht_features.py\n", status: done}
- {id: p3-vectorize, content: "- [ ] [AGENT] P2. Audit FSS calculators for .iterrows() usage.\n  Replace with vectorized pandas operations.\n  Archived note: 3/5 calculators used .iterrows().\n", status: pending, blocked_by: p2a-team-features}
- {id: p4-validation, content: "- [ ] [AGENT] P0. Run feature count audit.\n  Total features across all calculators >= 1000.\n  Each category meets or exceeds archived counts.\n  QG: cd features-sports-service && bash scripts/quality-gates.sh\n", status: pending, blocked_by: p3-vectorize}
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_sports_prediction_pipeline_2026_04_15.md](./consolidated_sports_prediction_pipeline_2026_04_15.md).**
> Original scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

# Sports Integration Plan 4: Feature Calculators Full 1000+

Part of the 6-plan sports integration series. Depends on Plan 3 (enrichment data flowing from all providers).

## Success Criteria

- Feature count >= 1000 (vs archived 857)
- All 17+ calculators producing non-zero features
- No .iterrows() in production paths
- Halftime (70+), odds multi-horizon (53+), weather (10+) complete
