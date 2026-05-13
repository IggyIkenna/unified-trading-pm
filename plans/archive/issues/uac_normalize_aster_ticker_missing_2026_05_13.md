---
title: "UAC normalize_aster_ticker missing from tickers.py — blocks all emission policy tests in features-service"
created: "2026-05-13"
author: "slot-7 sub-agent (Phase 6.5 sports wiring)"
source:
  - "features-service/.venv run of tests/sports/unit/test_emission_policy.py"
  - "unified-api-contracts/unified_api_contracts/normalize_utils/__init__.py:289-290"
severity: P1
suggested_owner: "UAC maintainer (Ikenna slot 1)"
status: RESOLVED
resolved_by: "slot-5 (UAC@f008af9 + regression-guard UAC@6110d05)"
resolved_at: "2026-05-13"
---

> **✅ RESOLVED 2026-05-13 by Ikenna slot 5**
>
> Root cause: `unified_api_contracts/normalize_utils/tickers.py` was a 10-line stub — ALL 15 venue ticker re-exports
> (not just `normalize_aster_ticker`) were missing. Every UAC consumer was failing on this same chain, masking the
> breadth of the outage.
>
> Fix: **UAC@f008af9** — restored 15 ticker re-exports in `tickers.py` (aster/binance/bitget/
> bybit/ccxt/coinbase/deribit/huobi/hyperliquid/ibkr/kalshi/kucoin/mexc/okx/upbit). Module now mirrors the re-export
> pattern from sibling `trades.py` / `sides.py`.
>
> Regression guard: **UAC@6110d05** — added `tests/test_normalize_utils_tickers_reexports.py` with 2 unit tests
> asserting all 15 expected re-exports + `__all__` completeness. Prevents future stub-regression at PR time.
>
> Downstream impact verified:
>
> - All 6 emission-policy test files in features-service (cross_instrument / delta_one / onchain / calendar / commodity
>   / sports) can now collect cleanly.
> - 12 pre-existing failures in QG `tests/unit/test_config.py` related to this root cause should resolve.
> - instruments-service `test_new_orchestrator.py::test_cli_main_imports_cleanly` no longer needs the workaround that
>   bypassed the import (Harsh's WIP — `git checkout --` restores original).
>
> Issue retained for archive; do NOT re-open unless `tickers.py` regresses again (regression-guard test will catch that
> at PR time).

## What I found

`unified_api_contracts/normalize_utils/__init__.py` line 290 imports `normalize_aster_ticker` from
`unified_api_contracts.normalize_utils.tickers`, but that symbol does NOT exist in `tickers.py`. This causes:

```
ImportError: cannot import name 'normalize_aster_ticker' from
  'unified_api_contracts.normalize_utils.tickers'
```

This error propagates through `unified_api_contracts/__init__.py` (line 708) which imports from `normalize_utils`. Any
test that does `from unified_api_contracts.canonical... import ...` (a deep-path import) triggers the root `__init__.py`
and fails with this error.

## Why it matters

All emission policy tests wired in Phase 6.3-6.5 import from UAC canonical directly:

- `tests/cross_instrument/unit/test_emission_policy.py`
- `tests/delta_one/unit/test_emission_policy.py`
- `tests/onchain/unit/test_emission_policy.py`
- `tests/calendar/unit/test_emission_policy.py`
- `tests/commodity/unit/test_emission_policy.py`
- `tests/sports/unit/test_emission_policy.py` (just wired, Phase 6.5)

None of these tests can execute in isolation (`pytest tests/*/unit/test_emission_policy.py`). They are structurally
correct but collection-fail with this ImportError.

The QG `tests/unit/` sweep also has 12 pre-existing failures traced to this same root cause (e.g.
`test_family_config_module_imports[sports]`, `test_family_config_module_imports[calendar]`, etc.)

## Recommended decision

1. Add `normalize_aster_ticker` to `unified_api_contracts/normalize_utils/tickers.py` (simplest fix), OR rename/remove
   the import from `normalize_utils/__init__.py` if Aster ticker support was intentionally removed.
2. Once fixed, all 6 emission policy test files (30+ tests) will execute cleanly.
3. The 12 QG failures in `tests/unit/test_config.py` will also resolve.

This is a UAC-only fix — no features-service changes needed.
