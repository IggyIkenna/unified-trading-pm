---
name: sports-integration-04-feature-calculators-full
locked_by: live-defi-rollout
locked_since: 2026-03-25
overview: |
  Port remaining feature calculators from archived new-sports-batting-services to reach
  1000+ feature target. Audit each of 17 archived calculators vs 21 FSS calculators,
  port missing features, vectorize .iterrows() usage, complete halftime + odds multi-horizon.
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
      - [ ] [AGENT] P0. Compare archived vs FSS calculators. For each of 17 archived:
        Count features produced by archived version.
        Count features produced by FSS version.
        Identify missing features per calculator.
        Document in comparison table.
        Archived source: archive/new-sports-batting-services/footballbets/features/calculators/
        FSS source: features-sports-service/features_sports_service/calculators/
        Key comparisons:
          archived team.py (1813L, 262 features) vs FSS team_form+goals+xg+derived
          archived halftime.py (1200L, 70 features) vs FSS halftime_calculator+ht_features
          archived odds.py (373L, 53 features) vs FSS odds_calculator
          archived weather.py (277L, 10 features) vs FSS weather_calculator
    status: pending

  # ============================================================================
  # PHASE 2 — Port missing features  [PARALLEL per calculator]
  # ============================================================================
  - id: p2a-team-features
    content: |
      - [ ] [AGENT] P1. Port missing team features from archived team.py (1813L).
        Compare: pressing intensity, transition metrics, recovery patterns.
        Target: 262 features (matching archived count).
    status: pending
    blocked_by: p1-calculator-audit
  - id: p2b-halftime-features
    content: |
      - [ ] [AGENT] P1. Port missing halftime features from archived halftime.py (1200L).
        Focus: 2nd half predictions (Poisson model for remaining play).
        Target: 70 features.
    status: pending
    blocked_by: p1-calculator-audit
  - id: p2c-odds-features
    content: |
      - [ ] [AGENT] P1. Port odds multi-horizon features from archived odds.py (373L).
        Verify FSS odds_calculator produces T-24h, T-6h, T-1h, T-0 features.
        Port: bookmaker probability calibration, line movement deltas.
        Target: 53 features across all horizons.
    status: pending
    blocked_by: p1-calculator-audit
  - id: p2d-weather-features
    content: |
      - [ ] [AGENT] P1. Port weather features from archived weather.py (277L).
        Verify FSS weather_calculator receives stadium lat/lon from Open-Meteo.
        Port: weather impact coefficients.
        Target: 10 features.
    status: pending
    blocked_by: p1-calculator-audit

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

# Sports Integration Plan 4: Feature Calculators Full 1000+

Part of the 6-plan sports integration series. Depends on Plan 3 (enrichment data flowing from all providers).

## Success Criteria

- Feature count >= 1000 (vs archived 857)
- All 17+ calculators producing non-zero features
- No .iterrows() in production paths
- Halftime (70+), odds multi-horizon (53+), weather (10+) complete
