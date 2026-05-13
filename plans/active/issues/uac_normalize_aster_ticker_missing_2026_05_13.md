---
title: "UAC normalize_aster_ticker missing from tickers.py — blocks all emission policy tests in features-service"
created: "2026-05-13"
author: "slot-7 sub-agent (Phase 6.5 sports wiring)"
source:
  - "features-service/.venv run of tests/sports/unit/test_emission_policy.py"
  - "unified-api-contracts/unified_api_contracts/normalize_utils/__init__.py:289-290"
severity: P1
suggested_owner: "UAC maintainer (Ikenna slot 1)"
---

## What I found

`unified_api_contracts/normalize_utils/__init__.py` line 290 imports `normalize_aster_ticker`
from `unified_api_contracts.normalize_utils.tickers`, but that symbol does NOT exist in
`tickers.py`. This causes:

```
ImportError: cannot import name 'normalize_aster_ticker' from
  'unified_api_contracts.normalize_utils.tickers'
```

This error propagates through `unified_api_contracts/__init__.py` (line 708) which imports
from `normalize_utils`. Any test that does `from unified_api_contracts.canonical... import ...`
(a deep-path import) triggers the root `__init__.py` and fails with this error.

## Why it matters

All emission policy tests wired in Phase 6.3-6.5 import from UAC canonical directly:
- `tests/cross_instrument/unit/test_emission_policy.py`
- `tests/delta_one/unit/test_emission_policy.py`
- `tests/onchain/unit/test_emission_policy.py`
- `tests/calendar/unit/test_emission_policy.py`
- `tests/commodity/unit/test_emission_policy.py`
- `tests/sports/unit/test_emission_policy.py` (just wired, Phase 6.5)

None of these tests can execute in isolation (`pytest tests/*/unit/test_emission_policy.py`).
They are structurally correct but collection-fail with this ImportError.

The QG `tests/unit/` sweep also has 12 pre-existing failures traced to this same root cause
(e.g. `test_family_config_module_imports[sports]`, `test_family_config_module_imports[calendar]`, etc.)

## Recommended decision

1. Add `normalize_aster_ticker` to `unified_api_contracts/normalize_utils/tickers.py` (simplest fix),
   OR rename/remove the import from `normalize_utils/__init__.py` if Aster ticker support was
   intentionally removed.
2. Once fixed, all 6 emission policy test files (30+ tests) will execute cleanly.
3. The 12 QG failures in `tests/unit/test_config.py` will also resolve.

This is a UAC-only fix — no features-service changes needed.
