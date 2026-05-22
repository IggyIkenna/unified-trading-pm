---
title: strategy-service QG regression — dydx removed from UAC venue_tokens breaks test_target_universe.py
created: 2026-05-20
source:
  - QG-CLUSTER-C Phase -1 sweep
  - UAC@df2c754 — "defunct UAC provider dirs Phase 3 cleanup - sharpapi + fear_greed + dydx"
  - strategy-service tests/unit/engine/strategies/v2/test_target_universe.py
locked_by: live-defi-rollout
priority: P2
status: RESOLVED 2026-05-22
resolved_via:
  Option A — dydx re-added to UAC venue_tokens.py (confirmed line 128). Strategy catalog entries retained. 5 test
  failures cleared.
---

## What I found

`UAC@df2c754` (2026-05-20 12:50 UTC) removed `dydx` from `_DEFI_PERP_TOKENS` in
`unified_api_contracts/internal/architecture_v2/venue_tokens.py` as part of "defunct UAC provider dirs Phase 3 cleanup".

After this commit, strategy-service QG fails with 5 test failures:

```
FAILED tests/unit/engine/strategies/v2/test_target_universe.py::TestSlotLabelIntegrity::test_every_slot_label_parses
FAILED tests/unit/engine/strategies/v2/test_target_universe.py::TestLoader::test_loader_registers_every_row
FAILED tests/unit/engine/strategies/v2/test_target_universe.py::TestLoader::test_definition_family_matches_archetype_mapping
FAILED tests/unit/engine/strategies/v2/test_target_universe.py::TestLoader::test_config_slots_content_hashed
FAILED tests/unit/engine/strategies/v2/test_target_universe.py::TestLoader::test_combined_loader_has_legacy_plus_target
```

Root cause:

```
ValueError: slot label 'ML_DIRECTIONAL_CONTINUOUS@dydx-btc-1h-usdc-v2-prod':
scope tokens ('dydx', 'btc') start with a non-venue token — grammar requires
at least one venue token first
```

The strategy catalog (`strategy_service/engine/strategies/v2/target_universe/catalog.py:127-128`) still has `dydx`
entries:

```python
("dydx", "btc"),
("dydx", "eth"),
```

The `parse_slot_label()` function in `slot_label.py` calls `split_scope_tokens()` from UAC
`architecture_v2/venue_tokens.py` which no longer recognizes `dydx`.

## Why it matters

- strategy-service QG is FAILING → Phase -1 (workspace-wide QG green) is NOT fully green
- Phase -1 must be GREEN before Phase 2 (code freeze) can begin
- The strategy_archetype_logic_audit (Opus-1M session tonight) must address this gap

## Scope

- strategy-service `engine/strategies/v2/` — covered by LOGIC freeze gate
- UAC `internal/architecture_v2/venue_tokens.py` — NOT under freeze gate

## Recommended resolution (operator to decide)

**Option A — Re-add `dydx` to UAC venue_tokens** (if dydx is still an active perp venue):

```python
# In unified_api_contracts/internal/architecture_v2/venue_tokens.py
_DEFI_PERP_TOKENS: frozenset[str] = frozenset({
    "gmx",
    "drift",
    "dydx",  # Restore — still referenced in strategy catalog
})
```

Fast fix, UAC change only (not under strategy-LOGIC freeze gate). Risk: may conflict with the "defunct provider cleanup"
intent of `df2c754`.

**Option B — Remove dydx from strategy catalog** (if dydx was intentionally retired):

```python
# In strategy_service/engine/strategies/v2/target_universe/catalog.py
# Remove:
#   ("dydx", "btc"),
#   ("dydx", "eth"),
```

Correct if dydx is no longer an active venue. UNDER freeze gate — needs strategy_archetype_logic_audit.

**Option C — Defer catalog cleanup, add xfail markers** (shortest path to QG green): Mark the 5 failing tests as
`@pytest.mark.xfail(reason="dydx removed from venue_tokens — catalog cleanup pending strategy_archetype_logic_audit")`
temporarily. Allows Phase -1 to land green while the catalog decision is pending. Add follow-up task to clean up once
the audit decides on dydx retention.

## Status

`BLOCKED-OPERATOR-DECISION` — operator must choose between Option A/B/C.

Escalation path: strategy_archetype_logic_audit_2026_05_20.md (Opus-1M session).

Referenced from: plans/active/work_split_2026_05_20_ikenna.md § Slot 11 row.

## Update 2026-05-20 — slot 4 boot investigation

**Separate issue resolved**: A second root cause was masking the 5 dydx test failures: `STRATEGY_PNL_STREAM` was not
re-exported from `unified_trading_library.__init__` (added to `events/event_types.py` in `de5ca0a0` but re-exports
missed from `events/__init__.py` and `__init__.py`). This caused an `ImportError` at collection time, preventing the 5
dydx failures from appearing individually.

Fixed in utl@672c0517 (`fix(exports): add STRATEGY_PNL_STREAM to UTL __init__ and events __init__ re-exports`). After
the fix, the 5 dydx failures now appear as individual `FAILED` lines rather than a single collection `ERROR`. The dydx
BLOCKED-OPERATOR-DECISION status is unchanged.
