---
name: Sports Migration — Combined (Gap Fix + Phase 2 Full)
overview: |
  Consolidates sports_migration_gap_fix and sports_migration_phase2_full (merged 2026-03-09).
  Remaining work: live-mode scraper adapters + deployment config (gap fix B1/B5-B6 in_progress),
  feature calculators (pure code), USEI Betfair/Pinnacle adapters (blocked by API keys phase-4),
  and strategy/execution wiring (blocked by USEI adapters).
status: active
created: 2026-03-02
updated: 2026-03-09
isProject: false
todos:
  # ── From sports_migration_gap_fix (Part B) ──────────────────────────────
  - id: b1-scraper-adapters
    content:
      "B1 — Scraper adapters in USEI; validate CSS selectors; website version fingerprinting; Playwright in base image.
      In progress — core adapter scaffolding exists, selectors need validation + fingerprinting logic."
    status: in_progress

  - id: b5-b6-deployment
    content:
      "B5–B6 — Odds API validation; sports sharding; Playwright in base image; instruments sports namespace. In progress
      — base image Dockerfile change pending."
    status: in_progress

  # ── From sports_migration_phase2_full ───────────────────────────────────
  - id: feature-calculators
    content:
      "FSS feature calculators — season_context, goal_timing, venue_context, referee; team features (split team_form,
      team_goals, team_xg, team_derived; each ≤900L). Pure Python, no external deps. Also: arb vig + is_arbitrage in
      features_sports_service/arb/ (currently only __init__.py)."
    status: done

  - id: usei-adapters
    content:
      "USEI — Betfair and Pinnacle adapters (unit tests with VCR mocks). BLOCKED: Betfair key not in SM; Pinnacle key
      not obtained. See api_keys_and_auth.plan.md § phase-3-keys + phase-4-blockers."
    status: pending

  - id: strategy-execution
    content:
      "Strategy/execution — ArbitrageStrategy (reads vig + is_arbitrage from FSS, emits TradeSignal); MLSportsStrategy
      (consumes FSS features + PredictionEvent via UMI); execution_service places/cancels via USEI Betfair/Pinnacle
      mocks. Acceptance: quality-gates.sh passes; zero os.getenv; zero Any. BLOCKED: depends on usei-adapters."
    status: pending
---

# Sports Migration — Combined Plan

**Merged 2026-03-09** from:

- `sports_migration_gap_fix.plan.md` (Part A complete; Part B in progress)
- `sports_migration_phase2_full.plan.md`

## Completed Work (before merge)

### Gap Fix — Part A (DONE)

- Batch pipeline fully migrated from sports-betting-services-previous
- API contracts (CanonicalOdds, OddsType, progressive stats schemas)
- Live feature subset, feature cache, strategy-service sports arb
- Execution-service USEI routing
- PaperBettingAdapter + operation mode routing

### Phase 2 — Completed

- FSS config (UnifiedCloudConfig) + output schemas
- FSS engine (batch/live seam)
- Remaining features: h2h, league, odds, halftime, player_lineup, poisson_xg, multisource_xg, advanced_stats
- Data loader (in-memory DataFrames)

## Remaining Work

### Actionable Now (no external blockers)

1. **b1-scraper-adapters** — validate CSS selectors, add fingerprinting, finish Playwright adapter
2. **b5-b6-deployment** — update base image Dockerfile, instruments sports namespace
3. **feature-calculators** — season_context, goal_timing, venue_context, referee + arb/vig in FSS

### Blocked by API Keys (phase-4-blockers + phase-3-keys)

4. **usei-adapters** — Betfair + Pinnacle (need keys in SM to record VCR cassettes)
5. **strategy-execution** — depends on usei-adapters

## Blockers

| Blocker                | Type          | Specific Dependency                          | Resolution                           |
| ---------------------- | ------------- | -------------------------------------------- | ------------------------------------ |
| Betfair key not in SM  | `[EXTERNAL]`  | api_keys_and_auth.plan.md § phase-4-blockers | Obtain via betfair developer program |
| Pinnacle key not in SM | `[EXTERNAL]`  | api_keys_and_auth.plan.md § phase-3-keys     | Obtain via pinnacle.com/affiliates   |
| USEI v1 not ready      | `[PLAN_TODO]` | usei-adapters (this plan)                    | Unblocked once API keys in SM        |

## Standards

- `UnifiedCloudConfig` extension; no `os.getenv()`; secrets via `get_secret_client()`
- No `Any` in public API; `TypedDict`/`Protocol`/`dict[str, X]`
- Files ≤900L; functions ≤100L; methods ≤50L; classes ≤500L
- ruff (line-length 120) + basedpyright strict; MIN_COVERAGE=70
