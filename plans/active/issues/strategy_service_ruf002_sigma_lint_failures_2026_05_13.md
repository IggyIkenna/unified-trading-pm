---
title: "strategy-service: pre-existing RUF002 lint failures (ambiguous σ) in dynamic_hedge_ratio.py"
created: 2026-05-13
author: slot-4-harsh
source:
  - arbitrage_price_dispersion_finalisation_2026_05_09
severity: P2
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

## What I found

Running `bash scripts/quality-gates.sh` in strategy-service (on `live-defi-rollout`, 2026-05-13) produces:

```
❌ Lint FAILED
strategy_service/engine/strategies/v2/carry_and_yield/dynamic_hedge_ratio.py:21:57: RUF002 Docstring contains ambiguous `σ` (GREEK SMALL LETTER SIGMA). Did you mean `o` (LATIN SMALL LETTER O)?
strategy_service/engine/strategies/v2/carry_and_yield/dynamic_hedge_ratio.py:21:59: RUF002 Docstring contains ambiguous `σ` (GREEK SMALL LETTER SIGMA). Did you mean `o` (LATIN SMALL LETTER O)?
tests/unit/engine/strategies/v2/test_dynamic_hedge_ratio.py:88:36: RUF002 Docstring contains ambiguous `σ` (GREEK SMALL LETTER SIGMA). Did you mean `o` (LATIN SMALL LETTER O)?
```

3 violations across 2 files. **These failures are pre-existing** — confirmed via `git stash` + re-run before
any edits; identical output with the clean tree. They block QG Pass 1 for any strategy-service work.

## Why it matters

- Any agent touching strategy-service hits a red QG Pass 1 immediately, even with zero related changes.
- Ruff `RUF002` is not a style preference — it prevents ambiguous Unicode characters in docstrings that could
  cause confusion. The σ appears in mathematical notation for standard deviation in carry_and_yield hedging.
- Blocks the two-pass model (Pass 1 full QG must be green before Pass 2 quickmerge).

## Files affected

- `strategy_service/engine/strategies/v2/carry_and_yield/dynamic_hedge_ratio.py:21` — docstring uses `σ`
  for standard deviation notation.
- `tests/unit/engine/strategies/v2/test_dynamic_hedge_ratio.py:88` — test docstring same.

## Recommended decision

**P2** — fix before next strategy-service quality-gate run.

Replace `σ` with plain ASCII `sigma` or `std_dev` in the affected docstrings. These are in mathematical
descriptions of the dynamic hedge ratio calculation.

**Owner**: carry_and_yield workstream owner (Ikenna per workstream tie-breaker — cross-repo design scope).

**RESOLVED 2026-05-13 (slot-4-harsh)**: operator directed fix. Replaced σ → `sigma` in:
- `strategy_service/engine/core/gcs_feature_provider.py` — C901 complexity also fixed by extracting
  `_load_date_frames()` helper (complexity 8→6); shipped at strategy-service@88f77c0
- `strategy_service/engine/strategies/v2/carry_and_yield/dynamic_hedge_ratio.py:21` — sigma fix
- `tests/unit/engine/strategies/v2/test_dynamic_hedge_ratio.py:88` — sigma fix
- Both sigma fixes at strategy-service@fe1e81d

QG lint now ✅ clean (0 RUF002 errors). 17 pre-existing test failures remain (orphan factory entries,
slot-label parser, coverage module) — outside slot-4 scope, filed separately.
