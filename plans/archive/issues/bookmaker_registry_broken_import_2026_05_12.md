---
title:
  "UAC canonical/domain/__init__.py:266 imports get_expected_bookmakers from wrong module — blocks all
  instruments-service tests"
created: 2026-05-12
resolved: 2026-05-12
author: ikenna
resolved_by: Harsh slot 2 (UAC@b73949d)
source:
  - slot 5 Phase 2.D work session 2026-05-12
  - instruments-service QG test collection failure
status: RESOLVED
severity: P0
---

## ✅ RESOLVED 2026-05-12

Fixed by Harsh slot 2 — `unified-api-contracts@b73949d` corrected the import path
(`from .sports.bookmaker_registry import get_expected_bookmakers` →
`from .sports.bookmaker_accessors import get_expected_bookmakers`).

Verified via Slot 2 DONE-ping in `harsh_orchestrator/pings/slot_2.md` + PM coordination
ledger `pm_coordination_ledger_2026_05_13.md` § "Active Issues" table.

Moved from `plans/active/issues/` → `plans/archive/issues/` on 2026-05-13.

---

## What I found

`unified_api_contracts/canonical/domain/__init__.py:266` imports `get_expected_bookmakers` from `bookmaker_registry`:

```python
from .sports.bookmaker_registry import (
    ...
    get_expected_bookmakers,
)
```

But `bookmaker_registry.py` has a comment at line 868:

```python
# get_expected_bookmakers lives in bookmaker_accessors.py
```

The function was moved to `bookmaker_accessors.py` by a foreign agent (the file is dirty / foreign-modified in the UAC
worktree), but `domain/__init__.py` was not updated.

### Failure mode

Every `import unified_api_contracts` import chain that touches `canonical.domain` fails with:

```
ImportError: cannot import name 'get_expected_bookmakers' from 'unified_api_contracts.canonical.domain.sports.bookmaker_registry'
```

This blocks ALL instruments-service unit tests at collection time — pytest fails before running a single test.

### Files involved

- `unified-api-contracts/unified_api_contracts/canonical/domain/__init__.py` line 266
- `unified-api-contracts/unified_api_contracts/canonical/domain/sports/bookmaker_accessors.py` (correct home)
- `unified-api-contracts/unified_api_contracts/canonical/domain/sports/bookmaker_registry.py` (foreign-modified; has the
  redirect comment)

## Why it matters

- All instruments-service unit tests are blocked — no test coverage for ANY instruments-service code until fixed.
- This includes the 5 new Phase 2.D timing tests (`test_phase2d_match_timing.py`) that were shipped in UAC@0a3d464
  - instruments-service@9bffca2 — they cannot be verified to pass.
- Any CI that runs instruments-service tests will hard-fail on import.
- This is a foreign file: `bookmaker_registry.py` shows as dirty in `git status` for the UAC worktree. The fix is a
  1-line change in `domain/__init__.py` (not the dirty file), so it CAN be applied without touching the foreign WIP.

## Recommended decision

**Fix**: In `unified_api_contracts/canonical/domain/__init__.py` line 266, change:

```python
from .sports.bookmaker_registry import (
    ...
    get_expected_bookmakers,
)
```

to:

```python
from .sports.bookmaker_accessors import get_expected_bookmakers
```

(or fold `get_expected_bookmakers` into the existing `bookmaker_accessors` import block if one exists).

The owning agent for the `bookmaker_registry.py` foreign-modified WIP should verify this doesn't conflict with their
in-flight changes before pushing. `domain/__init__.py` itself is NOT the dirty file — it's safe to edit.

**Priority**: P0 — blocks test execution workspace-wide for instruments-service consumers. Should be fixed before the
next test run or CI push to `live-defi-rollout`.
