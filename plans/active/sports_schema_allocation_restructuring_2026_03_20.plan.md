---
name: sports-schema-allocation-restructuring
overview: |
  Fix 7 misplaced sports schemas: SportsFeatureVector UAC→UIC, MTDS duplicate delete,
  api_football UMI→URDI, understat/footystats UMI→features-interface, round_names
  instruments→UAC. Plus GCS player mapping migration and PlayerAliasResolver.
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-internal-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-reference-data-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-features-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-market-interface
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: instruments-service
    code: C0
    deployment: none
    business: none
  - repo: features-sports-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on:
  - sports-canonical-mapping-and-gcs-migration

todos:
  # ========================================================================
  # PHASE 0 — Commit pending uncommitted changes
  # ========================================================================
  - id: p0a-commit-instruments
    content: |
      - [ ] [AGENT] P0. Commit instruments-service pending QG fixes.
        Files: instrument_validation.py, live_mode_handler.py, parser.py,
        cloud_data_provider.py, service_config.py, writer.py (CORRECT-LOCAL),
        quality-gates.sh (IMPORT_INSIDE/DEEP_IMPORT/GCP_PROJECT_ID exclude globs).
        Verify QG first: cd instruments-service && bash scripts/quality-gates.sh
    status: todo
  - id: p0b-commit-uac
    content: |
      - [ ] [AGENT] P0. Commit UAC pending sports data additions.
        Run git status, verify QG, commit all sports data.
    status: todo
  - id: p0c-commit-usri
    content: |
      - [ ] [AGENT] P0. Commit USRI __init__.py changes.
        Verify QG, commit.
    status: todo

  # ========================================================================
  # PHASE 1 — Add schemas to target repos [PARALLEL within phase]
  # ========================================================================
  - id: p1a-uic-sports-feature-vector
    content: |
      - [ ] [AGENT] P0. Add SportsFeatureVector + 5 mixin files to UIC.
        Copy from UAC canonical/domain/sports/ to UIC domain/features_sports/:
        features.py → feature_vector.py, _features_league_halftime_goals.py,
        _features_promoted_synthetic_schedule.py, _features_team_h2h.py,
        _features_venue_referee_player_odds.py, _features_xg_advanced_market.py.
        Update domain/features_sports/__init__.py + __init__.py exports.
        QG: cd unified-internal-contracts && bash scripts/quality-gates.sh
    status: todo
  - id: p1b-uac-round-names
    content: |
      - [ ] [AGENT] P0. Add round_names.py to UAC canonical/domain/sports/.
        Copy from instruments-service/instruments_service/sports/round_names.py.
        Export ROUND_NAMES, ROUND_PREFIXES, RoundMatch, resolve_round_name,
        is_known_round from sports/__init__.py and sports.py facade.
        QG: cd unified-api-contracts && bash scripts/quality-gates.sh
    status: todo

  # ========================================================================
  # PHASE 2 — Remove old copies [SEQUENTIAL after Phase 1 QG]
  # ========================================================================
  - id: p2a-uac-remove-feature-vector
    content: |
      - [ ] [AGENT] P0. Remove SportsFeatureVector from UAC.
        Delete 6 files from canonical/domain/sports/: features.py + 5 _features_*.py.
        Update canonical/domain/sports/__init__.py, canonical/domain/__init__.py,
        __init__.py, features.py facade — remove all feature re-exports.
        QG: cd unified-api-contracts && bash scripts/quality-gates.sh
    status: todo
    blocked_by: p1a-uic-sports-feature-vector
  - id: p2b-instruments-replace-round-names
    content: |
      - [ ] [AGENT] P0. Replace round_names in instruments-service with UAC import.
        Replace instruments_service/sports/round_names.py content with re-exports:
        from unified_api_contracts.sports import ROUND_NAMES, ROUND_PREFIXES,
        RoundMatch, resolve_round_name, is_known_round
        QG: cd instruments-service && bash scripts/quality-gates.sh
    status: todo
    blocked_by: p1b-uac-round-names

  # ========================================================================
  # PHASE 3 — Move adapters UMI → URDI / features-interface [after Phase 2]
  # ========================================================================
  - id: p3a-urdi-api-football
    content: |
      - [ ] [AGENT] P0. Create ApiFootballReferenceDataAdapter in URDI.
        Port from UMI adapters/alt_data/api_football_adapter.py.
        Adapt to BaseReferenceDataAdapter pattern. Register in router/factory.
        QG: cd unified-reference-data-interface && bash scripts/quality-gates.sh
    status: todo
    blocked_by: p2a-uac-remove-feature-vector
  - id: p3b-features-interface-understat-footystats
    content: |
      - [ ] [AGENT] P0. Create understat + footystats adapters in features-interface.
        Port from UMI adapters/alt_data/. Add BaseFeatureDataAdapter base class.
        Update __init__.py exports.
        QG: cd unified-features-interface && bash scripts/quality-gates.sh
    status: todo
    blocked_by: p2a-uac-remove-feature-vector
  - id: p3c-umi-remove-adapters
    content: |
      - [ ] [AGENT] P0. Remove api_football, understat, footystats from UMI.
        Delete 3 adapter files from adapters/alt_data/.
        Update __init__.py and adapters/alt_data/__init__.py re-exports.
        QG: cd unified-market-interface && bash scripts/quality-gates.sh
    status: todo
    blocked_by: p3a-urdi-api-football

  # ========================================================================
  # PHASE 4 — Update service consumers [after Phase 3]
  # ========================================================================
  - id: p4a-mtds-dedup
    content: |
      - [ ] [AGENT] P0. Delete MTDS duplicate sports schemas.
        Repoint adapters/sports/odds_tick_adapter.py:34 and
        tests/unit/test_sports_schemas.py:10 imports to UIC.
        Delete schemas/sports.py.
        QG: cd market-tick-data-service && bash scripts/quality-gates.sh
    status: todo
  - id: p4b-fss-imports
    content: |
      - [ ] [AGENT] P0. Update features-sports-service imports.
        cli/_providers.py: ApiFootballAdapter → URDI,
        UnderstatAdapter/FootystatsAdapter → features-interface.
        QG: cd features-sports-service && bash scripts/quality-gates.sh
    status: todo
    blocked_by: p3c-umi-remove-adapters

  # ========================================================================
  # PHASE 5 — Full QG sweep [after Phase 4]
  # ========================================================================
  - id: p5-validation-sweep
    content: |
      - [ ] [SCRIPT] P0. Full QG sweep across all 8 modified repos.
        Verify clean breaks: SportsFeatureVector from UIC works,
        from UAC raises ImportError. ApiFootballAdapter from URDI works,
        from UMI raises ImportError. Grep for stale imports.
    status: todo
    blocked_by: p4b-fss-imports

  # ========================================================================
  # PHASE 6 — GCS player mapping migration
  # ========================================================================
  - id: p6-gcs-player-migration
    content: |
      - [ ] [AGENT] P0. Create player mapping migration script.
        unified-trading-pm/scripts/sports/migrate_player_mappings_to_canonical.py
        Reads football-mapped-consolidated-{pid}/mapping/players.csv,
        deduplicates, constructs PlayerMapping, writes to
        sports-data-{pid}/sports/player_mappings.parquet.
    status: todo

  # ========================================================================
  # PHASE 7 — instruments-service PlayerAliasResolver
  # ========================================================================
  - id: p7a-player-alias-resolver
    content: |
      - [ ] [AGENT] P0. Create instruments_service/sports/player_aliases.py.
        PlayerAliasResolver class (mirrors team_aliases.py pattern).
        Indexes by canonical_player_id, api_football_player_id, understat_player_id.
        load_player_mappings_from_gcs() for GCS loading.
    status: todo
  - id: p7b-player-alias-tests
    content: |
      - [ ] [AGENT] P0. Create tests/unit/sports/test_player_aliases.py.
        5 test cases using load_player_mappings_from_dict fixtures.
        Add player_aliases.py to IMPORT_INSIDE_EXCLUDE_GLOBS.
        QG: cd instruments-service && bash scripts/quality-gates.sh
    status: todo
    blocked_by: p7a-player-alias-resolver
---

# Sports Schema Allocation Restructuring

## Problem

Sports domain audit identified 7 misplaced schemas violating the system's allocation principles:

1. **SportsFeatureVector** (derived ML feature, 16 mixins, 250+ fields) in UAC — should be UIC
2. **MTDS schemas/sports.py** — duplicate of UIC SSOT (file says "migration pending Phase 2")
3. **ApiFootballAdapter** in UMI — fetches reference data, belongs in URDI
4. **UnderstatAdapter** in UMI — fetches derived features (xG), belongs in features-interface
5. **FootystatsAdapter** in UMI — fetches derived features, belongs in features-interface
6. **round_names.py** in instruments-service — reference data registry, belongs in UAC
7. Plus: GCS player mapping migration + PlayerAliasResolver (new capabilities)

## Allocation Principles (User-Defined)

| Data type                               | Schema location                  | Connectivity       | Owner service            |
| --------------------------------------- | -------------------------------- | ------------------ | ------------------------ |
| Raw market data (odds)                  | UAC canonical + UIC tick schemas | UMI                | market-tick-data-service |
| Derived features (xG, predictors)       | UIC features_sports/             | features-interface | features-sports-service  |
| Static reference data (fixtures, teams) | UAC canonical + UIC storage      | URDI               | instruments-service      |
| External raw schemas                    | UAC external/{provider}/         | N/A                | N/A                      |
| Registry/config                         | UAC registry/                    | N/A                | N/A                      |

## Dependency DAG

```
Phase 0 (commit pending) ──────────────────────────────────────────────────
                                        │
Phase 1 ┌─ 1A: SportsFeatureVector → UIC ─┐
[PARALLEL] └─ 1B: round_names → UAC ────────┤
                                        │ QG gate
Phase 2 ┌─ 2A: Remove features from UAC ──┐
[SEQUENTIAL] └─ 2B: Replace round_names ──────┤
                                        │ QG gate
Phase 3 ┌─ 3A: api_football → URDI ──────┐
[PARALLEL] ├─ 3B: understat/footy → feat-intf ┤
           └─ 3C: Remove from UMI ───────────┤
                                        │ QG gate
Phase 4 ┌─ 4A: MTDS dedup ───────────────┐
[PARALLEL] └─ 4B: FSS import fix ────────────┤
                                        │ QG gate
Phase 5 ── Full QG sweep (8 repos) ────────────
                                        │
Phase 6 ── GCS player migration script ────────
                                        │
Phase 7 ── PlayerAliasResolver ────────────────
```

## Pre-Audit: Blast Radius

| Move                                 | Files affected                                                           | Runtime imports outside source |
| ------------------------------------ | ------------------------------------------------------------------------ | ------------------------------ |
| SportsFeatureVector (UAC→UIC)        | 57 files total — all UAC-internal or UI context copies                   | **Zero**                       |
| MTDS duplicate                       | 2 consumers: odds_tick_adapter.py:34, test_sports_schemas.py:10          | 2 files                        |
| ApiFootballAdapter (UMI→URDI)        | 2 consumers: features-sports-service cli/\_providers.py, UMI **init**.py | 2 files                        |
| Understat/FootyStats (UMI→feat-intf) | 2 consumers each: FSS cli/\_providers.py, UMI **init**.py                | 2 files each                   |
| round_names (instruments→UAC)        | Used only within instruments-service sports/ module                      | 0 external                     |

## NSBS GCS Migration Assessment

| Bucket                                   | Content                | Action                                     |
| ---------------------------------------- | ---------------------- | ------------------------------------------ |
| football-raw-data-all-sources-{pid}      | Raw reference parquets | FOLLOW-UP                                  |
| market-data-tick-sports-{pid}-v3         | Odds ticks 50GB+       | FOLLOW-UP                                  |
| football-mapped-consolidated-{pid}       | Canonical mappings     | Phase 6 (player), follow-up (team/fixture) |
| football-ml-features-{pid}               | Feature vectors        | NO — regenerate                            |
| football-ml-models-and-predictions-{pid} | CatBoost models        | NO — retrain                               |
| football-backtest-results-{pid}          | Backtest outputs       | NO — re-run                                |

## Success Criteria

- All 8 repo QGs green after Phase 5
- `from unified_internal_contracts.domain.features_sports import SportsFeatureVector` works
- `from unified_api_contracts import SportsFeatureVector` raises ImportError (clean break)
- `from unified_reference_data_interface.adapters.api_football import ApiFootballReferenceDataAdapter` works
- `from unified_features_interface import UnderstatAdapter` works
- Zero stale imports across workspace
- Player migration script runs in dry-run without errors
- PlayerAliasResolver tests pass
