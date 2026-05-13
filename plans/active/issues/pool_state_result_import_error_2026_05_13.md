---
title: "execution-service: PoolStateResult ImportError in defi_execution/protocols/__init__.py"
created: 2026-05-13
author: slot-3-wave3
source:
  - execution-service/execution_service/defi_execution/protocols/__init__.py
severity: P1
suggested_owner: "operator triage"
---

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
