---
name: sports-integration-04-feature-calculators-full
remaining_todos_consolidated_into: consolidated_sports_prediction_pipeline_2026_04_15
superseded_by: [consolidated_sports_prediction_pipeline_2026_04_15.plan.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
locked_by: live-defi-rollout
locked_since: 2026-03-25
overview: |
  Port remaining feature calculators from archived new-sports-batting-services to reach
  1000+ feature target. Audit each of 17 archived calculators vs 21 FSS calculators,
  port missing features, vectorize .iterrows() usage, complete halftime + odds multi-horizon.
  NOTE: Archived calculators exist in archive/sports_audit_data/. Some team and odds
  features already ported. Calculator count audit vs 1000+ target still needed.
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C4
  deployment: none
  business: B3

repo_gates:
  - repo: features-sports-service
    code: C0
    notes: "Port missing features, vectorize calculators"
  - repo: unified-api-contracts
    code: C0
    notes: "Schema additions for new feature fields if needed"

depends_on:
  - sports-integration-03-features-provider-integration

isProject: false
todos:
  # ============================================================================
  # PHASE 1 — Audit each calculator  [PARALLEL]
  # ============================================================================
  - id: p1-calculator-audit
    content: |
      - [x] [AGENT] P0. Compare archived vs FSS calculators.
        DONE (2026-04-03): Full audit complete.
        | Calculator | Archived | FSS  | Gap   | Status     |
        | Team       | 171      | 118  | -53   | GAPS       |
        | Halftime   | 69       | 39   | -30   | GAPS       |
        | Odds       | 53       | 137  | +84   | ENHANCED   |
        | Weather    | 9        | 5    | -4    | MINOR GAPS |
        Team missing: rolling windows (last1/3/5/season for shots, possession, xG conceded),
        velocity features (goals_trend_last10, xg_trend_last10), consistency (std dev),
        advanced stats (save%, pass accuracy, blocks).
        Halftime missing: goal timing (early/late flags), substitution patterns, comeback
        vulnerability, 2nd-half Poisson predictions, red card flags.
        Weather missing: binary flags (is_hot/cold/windy/adverse_weather).
        Total current: ~299 features. Target: 1000+. Gap: ~701 features to port.
    status: done

  # ============================================================================
  # PHASE 2 — Port missing features  [PARALLEL per calculator]
  # ============================================================================
  - id: p2a-team-features
    content: |
      - [x] [AGENT] P1. Port missing team features from archived team.py (1813L).
        DONE (2026-04-03): 54 new features ported across 4 files:
        team_form.py +32 (PPG rolling, streaks, cards, corners, rest/congestion),
        team_goals.py +6 (failed_to_score_rate, shots_per_goal, conversion_rate),
        team_derived.py +10 (velocity/trend features, consistency std dev),
        advanced_stats_calculator.py +6 (saves_per_game, save_pct, offsides).
        Total team features: ~223 (was 118). Exceeds archived 171.
    status: done
    blocked_by: p1-calculator-audit
  - id: p2b-halftime-features
    content: |
      - [x] [AGENT] P1. Port missing halftime features from archived halftime.py (1200L).
        DONE (2026-04-03): 67 new features ported:
        HALFTIME_COLUMNS: 79 (was 39). HT_FEATURE_COLUMNS: 45 (was 18).
        Score state flags (3), card features (5), goal timing per-team (5),
        per-team HT subs (4), historical HT patterns (16), 2nd-half Poisson
        predictions (7). Poisson PMF uses math.exp/factorial (no scipy dep).
        Comeback probability via CDF complement. All vectorized.
    status: done
    blocked_by: p1-calculator-audit
  - id: p2c-odds-features
    content: |
      - [x] [AGENT] P1. Port odds multi-horizon features from archived odds.py (373L).
        DONE (2026-03-28 + 2026-04-03): FSS odds_calculator produces 137 features
        (was 53 archived). Includes: T-24h/T-6h/T-1h/T-0 features, bookmaker tier
        consensus (16 cols), opening odds (6 cols), CLV features (9 cols),
        velocity/acceleration, steam detection.
    status: done
    blocked_by: p1-calculator-audit
  - id: p2d-weather-features
    content: |
      - [x] [AGENT] P1. Port weather features from archived weather.py (277L).
        DONE (2026-04-03): 4 binary flags added: is_hot_weather (>30°C),
        is_cold_weather (<5°C), is_windy (>40km/h), is_adverse_weather (any extreme).
        WEATHER_COLUMNS: 9 (was 5). Matches archived count exactly.
    status: done
    blocked_by: p1-calculator-audit

  # ============================================================================
  # PHASE 2e — BookmakerTier tagging in FSS odds calculator  [DONE]
  # ============================================================================
  - id: p2e-bookmaker-tier-tagging
    content: |
      - [x] [AGENT] P0. Wire BookmakerTier classification into FSS odds calculator.
        DONE (2026-04-03): compute_tier_features() added to odds_calculator.py.
        Imports classify_bookmaker() from UAC. Groups by fixture, classifies each
        bookmaker as SHARP/EXCHANGE/SOFT, computes: sharp_consensus_*, soft_consensus_*,
        exchange_price_*, sharp_soft_delta_*, sharp_disagreement_*, soft_disagreement_*,
        bookmaker_count_sharp/exchange/soft/total. 16 new columns.
        File: features_sports_service/calculators/odds_calculator.py
    status: done
  - id: p2f-ht-xg-from-shots
    content: |
      - [x] [AGENT] P1. Derive halftime xG from Understat per-shot data.
        DONE (2026-04-03): compute_ht_xg_from_shots() in ht_features.py.
        Filters shots where minute < 45, sums xG per team. Returns ht_xg_home,
        ht_xg_away, ht_shot_count_home, ht_shot_count_away.
        File: features_sports_service/calculators/ht_features.py
    status: done

  # ============================================================================
  # PHASE 3 — Vectorize  [SEQUENTIAL]
  # ============================================================================
  - id: p3-vectorize
    content: |
      - [ ] [AGENT] P2. Audit FSS calculators for .iterrows() usage.
        Replace with vectorized pandas operations.
        Archived note: 3/5 calculators used .iterrows().
    status: pending
    blocked_by: p2a-team-features

  # ============================================================================
  # PHASE 4 — Validation  [SEQUENTIAL]
  # ============================================================================
  - id: p4-validation
    content: |
      - [ ] [AGENT] P0. Run feature count audit.
        Total features across all calculators >= 1000.
        Each category meets or exceeds archived counts.
        QG: cd features-sports-service && bash scripts/quality-gates.sh
    status: pending
    blocked_by: p3-vectorize
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_sports_prediction_pipeline_2026_04_15.plan.md](./consolidated_sports_prediction_pipeline_2026_04_15.plan.md).**
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
