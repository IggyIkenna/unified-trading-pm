---
doc_type: issue
title: Delete confirmed-dead venue_mapping.DataTypeConfig + its one unit test
summary: >-
  `unified_api_contracts.registry.venue_mapping.DataTypeConfig` has ZERO production call sites (confirmed by the
  2026-08-08 SSOT ruling in `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`: every other repo hit is a
  passthrough re-export, never actually accessing `.instrument_data_types`; the only real read anywhere in the workspace
  is its own unit test). Deferred out of that doc's `[SCRIPT]` todo by the todo's own scoping ("Follow-up — do not do in
  this todo") and filed here as its own bounded, deterministic cleanup so the source doc's todos stay closed and its
  gated finalize plan can complete.
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, unified-trading-library, market-tick-data-service]
scope: [engineer]
tags: [defi, dead-code, cleanup, venue_mapping, follow-up]
related:
  [
    /plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
    /plans/active/defi_expected_unattempted_backlog_1m_2026_07_03_finalize_2026_08_08.md,
  ]
created: "2026-08-08"
author: unknown
source: [defi_expected_unattempted_backlog_1m_2026_07_03_finalize-001 (slot 30)]
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.06
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/venue_mapping.py,
    unified-trading-library/tests/config_interface/unit/test_venue_config.py,
    market-tick-data-service/market_tick_data_service/market_interface/models/venue_config.py,
    /plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
  ]
---

# Delete confirmed-dead venue_mapping.DataTypeConfig + its one unit test

## What I found

`unified_api_contracts.registry.venue_mapping.DataTypeConfig.instrument_data_types` has zero production call sites, per
the 2026-08-08 SSOT ruling (`issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`, na-corpus-digest-closeout
entry): the real production caller for A_TOKEN/DEBT_TOKEN valid-data_types resolution is
`market_data_categories._INSTRUMENT_TYPE_ALIASES` / `valid_data_types_for_instrument_type` (consumed by
`instruments-service/scripts/enumerate_expected_universe.py:708` and
`unified-api-contracts/unified_api_contracts/registry/possible_manifest.py::is_valid_shard_key`). Every other repo's hit
on `DataTypeConfig` (`market-tick-data-service/.../models/venue_config.py`,
`unified-trading-library/.../config_interface/venue_config.py`) is a passthrough re-export
(`from unified_api_contracts.registry import DataTypeConfig` + `__all__`) that never actually accesses
`.instrument_data_types`. The only real read anywhere in the workspace is
`unified-trading-library/tests/config_interface/unit/test_venue_config.py::TestDataTypeConfig` — a unit test of the dead
table itself.

## Why it matters

Dead code with a disagreeing (stale) data contract is a latent trap: `DataTypeConfig.instrument_data_types` declares
`oracle_prices` valid for `A_TOKEN`/`DEBT_TOKEN` in a way that already disagreed with the (until 2026-08-08) narrower
`PROTOCOL_CAPABILITIES`-derived set for VENUS/SOLEND — exactly the kind of two-registries-disagree drift that produced
this whole issue chain. Removing the dead table removes the disagreement permanently instead of leaving a second, unread
SSOT-shaped table around to confuse the next reader.

## Recommended decision

Delete the class + its re-exports + its one unit test. Bounded, deterministic, fully scoped — re-grep both repos for
call sites immediately before deleting (registry drift is possible between the ruling and execution) to confirm the
zero-call-site premise still holds.

## Todos

- [x] ✅ [SCRIPT] P3. Re-grep `unified-api-contracts`, `unified-trading-library`, and `market-tick-data-service` for any
      read of `DataTypeConfig` / `.instrument_data_types` beyond the passthrough re-exports and the one unit test named
      above (confirm the zero-call-site premise still holds at execution time). Repo: all three. — re-grepped
      2026-08-16: every hit was the class definition, its passthrough re-exports/`__all__` entries, the one unit test,
      or two historical comments in `unified-api-contracts/.../capability_declarations/_defi.py` (no real reads) —
      zero-call-site premise confirmed still holds.
- [x] ✅ [SCRIPT] P3. Delete `DataTypeConfig` from `unified-api-contracts/unified_api_contracts/registry/venue_mapping.py`
      and its passthrough re-exports in `market-tick-data-service/.../models/venue_config.py` and
      `unified-trading-library/.../config_interface/venue_config.py` (incl. `__all__` entries). Repo:
      unified-api-contracts, market-tick-data-service, unified-trading-library. — unified-api-contracts@7aa3143e06,
      market-tick-data-service@08aae3da84 (also removed the two `_defi.py` comments' literal `DataTypeConfig` mentions
      to satisfy the zero-remaining-references done-condition).
- [x] ✅ [SCRIPT] P3. Delete `TestDataTypeConfig` from
      `unified-trading-library/tests/config_interface/unit/test_venue_config.py`. Repo: unified-trading-library. Done
      when: `quality-gates.sh` is green in every touched repo, with zero remaining references to
      `DataTypeConfig`/`instrument_data_types` in any of the three repos. — unified-trading-library@0e4ae686eb;
      `quality-gates.sh` green in all three repos; post-edit repo-wide grep for `DataTypeConfig`/`instrument_data_types`
      across all three repos returns zero hits.

## Progress Log

- **2026-08-08 (finalize-plan REVIEW re-verification, slot 30)**: filed as the tracked follow-up to
  `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`'s `[SCRIPT]` todo, per that todo's own "do not do in this
  todo" deferral and the workspace HARD RULE that every follow-up is a tracked `- [ ]` todo, never prose.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **2026-08-16 (slot 33, AO data_engineering worker)**: executed all 3 todos. Re-grep confirmed the zero-call-site
  premise still held; deleted the `DataTypeConfig` dataclass + every passthrough re-export/`__all__` entry across the
  three repos, plus reworded two historical comments in `unified-api-contracts/.../capability_declarations/_defi.py`
  that named the class literally (the done-condition is zero remaining *references*, not just zero *imports*).
  `quality-gates.sh` green in all three repos (unified-api-contracts, unified-trading-library,
  market-tick-data-service). Shipped: unified-api-contracts@7aa3143e06, unified-trading-library@0e4ae686eb,
  market-tick-data-service@08aae3da84 — all verified ancestors of `origin/live-defi-rollout`. All 3 todos done; every
  todo is unlocked (`locked_by:` empty) — archiving this issue doc in the same commit.
