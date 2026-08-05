---
doc_type: issue
title: 2 pre-existing QG test failures block MTDS quickmerge — lending CLI module + Polymarket per-data-type sentinel
summary: >-
  quality-gates.sh run at market-tick-data-service@18f635ea found 2 pre-existing test failures unrelated to the
  both-legs-varying dedup rule extension being shipped: test_protocol_class_ops_have_modules[lending] (CLI operation
  'collect-rewards' has no _CLI_OP_TO_MODULE entry) and test_tier3_prediction_polymarket_no_crash (PREDICTION Tier-3 row
  missing instrument_id). These block quickmerge for unrelated code changes.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [qg-red, pre-existing, mtds]
related: [/plans/active/issues/mdt_canonical_odds_poll_key_duplicate_rows_2026_07_25.md]
created: 2026-08-05
author: slot-2 (data_engineering)
priority: P2
parent_epic: infrastructure_master
source:
  "Discovered while shipping both-legs-varying dedup rule extension (mtd_canonical_odds_poll_key_duplicate_rows-001)"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# 2 pre-existing QG test failures block MTDS quickmerge

## What I found

Running `quality-gates.sh` at `market-tick-data-service@18f635ea` (LDR HEAD + both-legs-varying dedup rule extension)
produced 2 test failures that are pre-existing (reproduced byte-identical on a clean tree at LDR HEAD, confirmed
unrelated to the in-flight change):

1. `tests/unit/test_collect_handler_schema.py::TestCollectHandlerCoversProtocolClass::test_protocol_class_ops_have_modules[lending]`
   — `AssertionError: CLI operation 'collect-rewards' (ProtocolClass.LENDING) has no entry in _CLI_OP_TO_MODULE`
2. `tests/unit/test_orchestrator_per_data_type_sentinel.py::test_tier3_prediction_polymarket_no_crash` —
   `AssertionError: PREDICTION Tier-3 row must carry instrument_id`

Both are assertion failures (not flaky timeouts) — real defects in the lending handler schema registry and Polymarket
per-data-type sentinel respectively.

## Why it matters

Quickmerge's `--agent` sentinel check requires `quality-gates.sh` to pass on the exact HEAD SHA being shipped. These 2
pre-existing failures prevent ANY unrelated code change (including the both-legs-varying dedup rule extension at
`market-tick-data-service@18f635ea`) from shipping via quickmerge.

## Recommended fix

- [x] ✅ [BACKEND] P2. Add `collect-rewards` CLI operation to `_CLI_OP_TO_MODULE` for `ProtocolClass.LENDING` (repo:
      market-tick-data-service) — market-tick-data-service@51f778d4 (slot-16, 2026-08-05)
- [x] ✅ [BACKEND] P2. Fix Polymarket Tier-3 per-data-type sentinel to include `instrument_id` in rows (repo:
      market-tick-data-service) — market-tick-data-service@1bcee624 (slot-2, 2026-08-05; UAC oracle
      `is_per_instrument_shard_data_type` now scopes the assertion to per-instrument dts)

## Progress Log

**2026-08-05 (slot-2, data_engineering)** — discovered while trying to ship both-legs-varying dedup rule extension.
Confirmed pre-existing via isolated re-run of both failing tests. Filing this issue doc + declaring qg_red repo-blocker
so the backend owns the resolution signal.
