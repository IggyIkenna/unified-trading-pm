---
title: "execution-service: PoolStateResult ImportError in defi_execution/protocols/__init__.py"
created: 2026-05-13
author: slot-3-wave3
source:
  - execution-service/execution_service/defi_execution/protocols/__init__.py
severity: P1
status: RESOLVED
resolved_at: 2026-05-14
resolved_by: slot-2-wave2
resolution_commit: execution-service@09198760
suggested_owner: "operator triage"
---

## ✅ RESOLVED 2026-05-14 (slot-2-wave2)

Already fixed on LDR by execution-service@`09198760` (2026-05-13 19:27 IST) — root cause was ruff AUTO-FIX stripping `PoolStateResult`/`SwapQuoteResult`/`SwapResult` aliases from `protocols/base.py` because they appear unused within `base.py` itself (they exist only as re-exports for `protocols/__init__.py` and `uniswap.py` consumers). Fix: added `# noqa: F401` to each of the three aliased imports.

**Diagnose-first verification (2026-05-14 06:35 UTC, slot-2-wave2 resume)**:
- `python -c "from execution_service.defi_execution.protocols import PoolStateResult"` → ✅ succeeds, resolves to `unified_api_contracts.internal.domain.execution_service.results.DeFiPoolStateResult`.
- `pytest --collect-only tests/` → 7921 tests collected. 5 remaining collection errors are unrelated (`get_testnet_contract_registry` UTL top-level export gap + 4 sports_execution adapter modules) — separate issues, not PoolStateResult.

No further action on this issue.

## What I found

Running `bash scripts/quality-gates.sh` in execution-service fails with:

```
ImportError: cannot import name 'PoolStateResult' from 'execution_service.defi_execution.protocols.base'
```

at `execution_service/defi_execution/protocols/__init__.py:78`.

The `__init__.py` attempts to import `PoolStateResult` from `.base`, but that symbol is not
exported (or has been renamed/removed) in `execution_service/defi_execution/protocols/base.py`.

This is a pre-existing breakage — NOT introduced by Wave 3 C901 refactors (which only touched
`providers/rpc_fallback.py` and `api/manual_instruction_api.py`).

## Why it matters

- All tests under `tests/` that import from `execution_service.defi_execution.protocols` fail
  at collection time, blocking the test suite.
- QG STEP tests cannot run against defi_execution code, masking coverage gaps.
- May indicate a renamed symbol from a DeFi protocol refactor that wasn't propagated to `__init__.py`.

## Recommended decision

1. Check git log on `execution_service/defi_execution/protocols/base.py` — find when `PoolStateResult`
   was removed/renamed and what replaced it.
2. Update `__init__.py` line 78 to import the correct symbol (or remove if no longer needed).
3. Run full QG to confirm test suite passes.

Assign to whoever owns the `defi_execution` protocols module (likely the slot currently working
on DeFi connector refactors).
