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
related: []
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

- [ ] [DATA] P2. Diagnose + fix `test_table_schemas_dict_has_all_sport_tables` (repo: features-service,
      unified-api-contracts) — either add the missing `players` table schema to UAC's `TABLE_SCHEMAS`, or update the
      test's expected-table list if `players` was intentionally folded into `fixture_lineups`/`fixture_events`. **Done
      when**:
      `tests/sports/integration/test_unified_deps_functional.py::     TestUnifiedApiContractsFunctional::test_table_schemas_dict_has_all_sport_tables`
      passes, with the fix matching whichever side turns out to be correct (not a blind add-the-missing-key patch).

## Codex SSOTs

None identified as directly relevant; UAC's `TABLE_SCHEMAS` is presumably documented near its definition module — grep
before assuming no SSOT exists.
