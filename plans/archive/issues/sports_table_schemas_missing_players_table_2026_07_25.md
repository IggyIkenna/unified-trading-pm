---
doc_type: issue
title: features-service sports integration test expects a "players" table in UAC's TABLE_SCHEMAS that does not exist
summary: >-
  Found (pre-existing, unrelated to the ODDS_COLUMNS naming migration in progress) while running features-service's full
  sports test suite: `tests/sports/integration/test_unified_deps_functional.py::
  TestUnifiedApiContractsFunctional::test_table_schemas_dict_has_all_sport_tables` fails with `AssertionError: Missing
  table: players` -- confirmed byte-identical on a clean tree (stashed my unrelated diff, re-ran, same failure), so this
  is not a regression from any in-flight change.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [features-service, unified-api-contracts]
scope: [engineer]
tags: [sports, test-failure, table-schemas, pre-existing]
related: [/plans/active/sports_consolidated_closeout_2026_07_19.md]
created: 2026-07-25
priority: P2
parent_epic: sports_master
source: "[DATA] slot-4, discovered running full tests/sports/ during sports_satellite_ao_dispatch_batch2-013"
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# features-service sports integration test expects a UAC "players" table that doesn't exist

## What I found

`test_table_schemas_dict_has_all_sport_tables` iterates an expected sport-table list and asserts every entry exists as a
key in UAC's `TABLE_SCHEMAS` dict. `players` is in the expected list but not in `TABLE_SCHEMAS` (which does have
`fixture_lineups` and `fixture_events`, both of which carry `player_id`/`player_name` columns — so player data may
already be represented via those tables rather than a dedicated `players` table, or `TABLE_SCHEMAS` may simply be
missing an entry that used to exist).

Verified pre-existing (not caused by any in-flight change): stashed all working-tree changes, re-ran the single test on
a clean checkout at the same commit, same `AssertionError: Missing table: players` failure.

## Why it matters

A real, currently-red integration test in `features-service`'s own suite — not blocking any specific in-flight task
(discovered incidentally), but a red test sitting in the suite risks masking a FUTURE real regression in this area if
left as ambient noise.

## Recommended decision

Whoever picks this up should first determine: (a) does UAC's `TABLE_SCHEMAS` need a new `players` entry, or (b) is the
test's expected-table list stale and should be updated to reflect that player data now lives under
`fixture_lineups`/`fixture_events` instead of a dedicated table. Read both sides before picking — don't guess.

## Todos

- [x] ✅ [DATA] P2. **Diagnose + fix `test_table_schemas_dict_has_all_sport_tables` — DONE, stale test, not a missing
      schema.** — features-service@30d419f6. Correction to this doc's framing: `TABLE_SCHEMAS` is defined LOCALLY in
      `features_service/sports/schemas/output_schemas.py`, not UAC. Root cause found via `git log`: `d564bf6f`
      (2026-07-18, "delete players/coaches/referees/rounds dimension tables") deliberately shrank `TABLE_SCHEMAS` from
      14 to 10 entries — all 4 removed tables ALWAYS wrote empty parquets (100% empty_confirmed); real data lives in
      `fixture_lineups.coach_id/name` (coach), `fixtures.referee_id` (referee), `fixture_lineups`/`player_stats`
      (player), `fixtures.round` (round). That commit updated 3 other test files pinning the old 14-table contract but
      missed this integration test. Removed `players`, `referees`, `coaches`, `rounds` from `expected_tables` (not just
      `players` — the test fails fast on the first missing entry in list order, so the doc's title undercounted; the
      other 3 were equally stale). Test passes; full 23-test file green; `quality-gates.sh` green.

## Codex SSOTs

None identified as directly relevant; UAC's `TABLE_SCHEMAS` is presumably documented near its definition module — grep
before assuming no SSOT exists.
