---
doc_type: issue
title: >-
  instruments-service QG red — UAC commit 26092ac8 registered FOOTYSTATS/LADBROKES/BET888SPORT/SMARKETS into
  VENUES_BY_ASSET_GROUP["sports"], violating the IS/UAC sports two-registry disjoint invariant
summary: >-
  Discovered while shipping an unrelated instruments-service fix (cleanup() AttributeError suppress). Full
  quality-gates.sh run failed 2 pre-existing tests: test_expected_universe_golden.py's golden-drift check (sports:
  golden=27, actual=31, 4 extra) and test_orchestrator_helpers.py's test_sports_exempt_is_disjoint_from_uac_sports
  (overlap={'FOOTYSTATS'}). Root cause: unified-api-contracts@26092ac8 ("feat: register tradfi/sports distinct-values
  accepted-exceptions + venue registry additions", 2026-07-30 11:11:38Z) added FOOTYSTATS/LADBROKES/BET888SPORT/SMARKETS
  to market_data_categories.py's VENUES_BY_ASSET_GROUP["sports"] list — but instruments-service's own sports venue
  registry (get_venues_for_asset_groups(["SPORTS"])) already carries FOOTYSTATS as an IS-owned, UAC-EXEMPT reference-
  data provider (Decision C, operator 2026-06-29: two disjoint registries by design). The two registries are no longer
  disjoint, breaking the invariant test and the golden fixture. Verified pre-existing (byte-identical failure on the
  tree before my unrelated 1-file diff, confirmed via git checkout of the parent commit).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [instruments-service, unified-api-contracts]
scope: [engineer]
tags: [qg-red, sports, footystats, venue-registry, two-registry-model, repo-blocker]
related: []
created: 2026-07-30
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source: ["discovered while shipping instruments-service@2cec0ab2 (unrelated cleanup() fix), slot-11, 2026-07-30"]
resolved_by:
locked_by:
---

# instruments-service QG red — UAC sports venue registry overlap

## What I found

Running `bash scripts/quality-gates.sh` on a clean instruments-service tree (HEAD at the time, `2cec0ab2`, an unrelated
1-file `cleanup()` fix) failed with 2 pre-existing test failures, both in the sports venue-registry
two-registry-disjoint invariant:

- `tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[sports]` —
  golden=27, actual=31; 4 extra: `('BET888SPORT', 'odds', 'trades')`, `('FOOTYSTATS', 'odds', 'trades')`,
  `('LADBROKES', 'odds', 'trades')`, `('SMARKETS', 'odds', 'trades')`.
- `tests/unit/test_orchestrator_helpers.py::TestVenueProducerUACInvariant::test_sports_exempt_is_disjoint_from_uac_sports`
  — `overlap={'FOOTYSTATS'}`.

Confirmed pre-existing, not caused by my diff: `git stash` (no-op, nothing unstaged) +
`git checkout HEAD~1 -- instruments_service/cli/instruments_handler.py` (my one changed file) reproduces byte-identical
failures.

Root cause: `unified-api-contracts@26092ac8` ("feat: register tradfi/sports distinct-values accepted-exceptions + venue
registry additions", landed 2026-07-30 11:11:38Z — ~30 min before this QG run) added
`FOOTYSTATS`/`LADBROKES`/`BET888SPORT`/`SMARKETS` to `market_data_categories.py`'s `VENUES_BY_ASSET_GROUP["sports"]`
list (`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:465-476`). But
`instruments_service/engine/orchestrator/venue_core.py::get_venues_for_asset_groups`'s own docstring (lines 458-462)
states: "SPORTS: IS owns reference-data providers (API_FOOTBALL/FOOTYSTATS/UNDERSTAT/TRANSFERMARKT/
SOCCER_FOOTBALL_INFO/OPEN_METEO). These are DISJOINT from the UAC sports venues (ODDS_API/PINNACLE/BETFAIR*/
DRAFTKINGS/FANDUEL) ... Decision C (operator 2026-06-29): two separate registries." FOOTYSTATS is now registered in BOTH
— the newly-added UAC entries broke a design invariant that was true until this commit.

## Why it matters

- instruments-service's full `quality-gates.sh` is RED — per the green-tree HARD RULE, no unrelated instruments-service
  commit can ship (Pass-1 QG can't produce a passing sentinel) until this clears.
- This looks like active, in-flight sports venue-registry cleanup work (many recent commits reference
  `sports_distinct_values_registry_cleanup_2026_07_30.md` / `sports_consolidated_native_ao_extract_2026_07_25.md`) —
  likely a real venue reclassification in progress, not a simple typo. Whoever owns that work needs to either (a) remove
  FOOTYSTATS from UAC's sports list if it's staying IS-owned/exempt, or (b) remove FOOTYSTATS from IS's own exempt
  list + `_ADAPTERS`/golden fixture if it's being reclassified INTO UAC's sports (odds-provider) registry, and
  regenerate the golden fixture either way. LADBROKES/BET888SPORT/SMARKETS don't currently appear in IS's own list (only
  FOOTYSTATS overlaps) — those 3 are likely fine as pure UAC additions; only FOOTYSTATS needs the disjoint decision.

## Recommended decision

Whoever owns the FOOTYSTATS venue-registry migration (per the referenced
`sports_distinct_values_registry_cleanup_ 2026_07_30.md` plan) should explicitly decide: is FOOTYSTATS staying an
IS-owned exempt reference-data provider (in which case UAC's new addition is the bug — remove it there), or is it being
reclassified as a UAC sports odds-provider venue (in which case IS's own exempt-list/golden-fixture needs updating to
match, and the golden fixture regenerated per its own docstring recipe).

## Todos

- [ ] [DATA] P1. **Resolve the FOOTYSTATS two-registry disjoint-invariant break** — decide + implement per "Recommended
      decision" above, then regenerate `tests/unit/scripts/test_expected_universe_golden.py`'s sports golden fixture per
      its docstring recipe so `quality-gates.sh` goes green again. (repo: instruments-service, unified-api-contracts)

## Progress Log

- **slot-11 2026-07-30**: Filed while blocked shipping an unrelated instruments-service fix (`cleanup()` AttributeError
  suppress, `2cec0ab2`). Declared repo-blocker via `/api/repo-blockers` for `instruments-service` (kind=`qg_red`) so the
  backend's RepoHealthWatcher pages me when green.
