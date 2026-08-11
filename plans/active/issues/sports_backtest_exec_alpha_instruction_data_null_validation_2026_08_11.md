---
doc_type: issue
title: >-
  execution-service QG RED — test_sports_backtest_exec_alpha.py fails with Nautilus msgspec ValidationError
  (take_profit_price null) after the _InstructionRecord TypedDict narrowing
status: open
assigned_vm: planning
created: "2026-08-11"
author: slot-14 (backend_engineer)
source:
  [
    execution-service@fd11d44e,
    /plans/active/sports_group_c_execution_backtest_harness_2026_07_21_finalize_2026_08_08.md,
  ]
related:
  [
    /plans/active/sports_group_c_execution_backtest_harness_2026_07_21_finalize_2026_08_08.md,
    /plans/active/bybit_usdc_deposit_automation_plan_2026_08_11.md,
  ]
---

# execution-service QG RED — sports backtest exec-alpha hermetic test fails on `take_profit_price` null validation

## What I found

While shipping an unrelated Bybit deposit-automation todo (`bybit_usdc_deposit_automation_plan_2026_08_11.md` todo 2),
`bash scripts/quality-gates.sh` on `execution-service` at `origin/live-defi-rollout` HEAD (`fd11d44e`) fails with:

```
FAILED tests/unit/cli/test_sports_backtest_exec_alpha.py::test_run_sports_backtest_produces_nontrivial_execution_alpha
FAILED tests/unit/cli/test_sports_backtest_exec_alpha.py::test_run_sports_backtest_alpha_reflects_l0_spread
2 failed, 7983 passed, 21 skipped, 1 xpassed, 71 warnings
```

**Verified pre-existing, not caused by my diff**: `git stash push --include-untracked` (removing my two-file Bybit diff
entirely), then `.venv/bin/python -m pytest tests/unit/cli/test_sports_backtest_exec_alpha.py -q` on the clean tree —
byte-identical failure (same 2 test names, same exception). Restored my stash afterward.

**Root cause** (from the isolated run's traceback): a Nautilus `ValidationError` raised while building the strategy
config:

```
ValidationError(Expected `float`, got `null` - at `$.instruction_data[...].take_profit_price`)
  nautilus_trader/backtest/engine.pyx:241 in BacktestEngine.__init__
  .../trading/config.py:130 in StrategyFactory.create
  .../common/config.py:250 in parse
```

This traces to `execution-service@fd11d44e` ("fix(execution): replace Any with `_InstructionRecord` TypedDict, narrow
`type: ignore`s") — the commit that closed todo 4 of
`/plans/active/sports_group_c_execution_backtest_harness_2026_07_21_finalize_2026_08_08.md`. That commit narrowed
`signal_driven_v3_base.py`'s `instruction_data` from `dict[str, dict[str, Any]]` to `dict[str, _InstructionRecord]` with
`_InstructionRecord(TypedDict, total=False)` declaring `take_profit_price: float` (a concrete, non-optional primitive).
The finalize plan's design note for the original harness explicitly says TP/SL absence is represented as a **NaN
placeholder**, not `None` — but somewhere in the instruction-building path a `None` is still reaching this field, and
Nautilus' msgspec `dec_hook` now rejects it at strategy-config decode time (msgspec `float` fields do not accept `null`
unless declared `Optional`/given a default). The finalize plan's todo 4 evidence entry (2026-08-11, slot 24) states "the
hermetic test... is unchanged and still asserts non-trivial `total_execution_alpha_bps != 0.0`" — that verification
claim does not hold in practice; the test now fails before reaching the assertion, at config-parse time, not at the
assertion.

## Why it matters

- `execution-service`'s `quality-gates.sh` is RED at `origin/live-defi-rollout` HEAD for every worker in this repo,
  independent of what they're shipping — a repo-wide qg_red blocker (declared via `POST /api/repo-blockers`,
  `kind: qg_red`, from this session).
- Per CLAUDE.md "Data pipeline correctness is the heartbeat" / QG-as-merge-prerequisite: no worker can commit a
  green-tree change to `execution-service` until this is fixed (or the two tests are quarantined with a tracked
  follow-up, if a fix isn't immediate).
- The finalize plan's remaining todo (archival ritual) should NOT proceed while claiming todo 4's hermetic-test evidence
  is good — that evidence is stale/incorrect and should be revisited before archival.

## Recommended decision

Either:

(a) Fix the root cause: find where `instruction_data`'s `take_profit_price`/`stop_loss_price` values are populated for
the sports/predictions instruction stream and ensure the NaN-placeholder convention the harness design intended is
actually applied (e.g. `float("nan")` instead of `None`) before it reaches `_InstructionRecord`/msgspec encoding; or

(b) If NaN itself doesn't round-trip cleanly through msgspec either (worth checking — NaN is technically a valid `float`
but some strict JSON-mode encoders reject it), widen `_InstructionRecord`'s `take_profit_price`/ `stop_loss_price`
fields to `float | None` with an explicit `None`-handling path in the strategy's TP/SL logic, and re-verify the STEP
5.24 blanket-`type: ignore` ban isn't reintroduced by the widening.

Either fix must re-run `tests/unit/cli/test_sports_backtest_exec_alpha.py` (both tests) and the full `quality-gates.sh`
before claiming green, given the prior "done" claim here was not actually re-verified end-to-end.

## Todos

- [ ] [BACKEND] P1. Fix `execution-service`'s `test_sports_backtest_exec_alpha.py` failures — root-cause the `null`
      reaching `_InstructionRecord.take_profit_price` (see "Root cause" above), apply the NaN-placeholder or
      `float | None` fix, and get `quality-gates.sh` green on `execution-service` again. Repo: execution-service.
      Done-when: both `test_run_sports_backtest_produces_nontrivial_execution_alpha` and
      `test_run_sports_backtest_alpha_reflects_l0_spread` pass; `quality-gates.sh` green.
- [ ] [DOCS] P2. Correct `sports_group_c_execution_backtest_harness_2026_07_21_finalize_2026_08_08.md` todo 4's evidence
      entry (append a correction, do not overwrite the existing entry) once the fix above lands — the "hermetic test...
      still asserts non-trivial alpha" claim was not actually re-run and was wrong; re-verify before that plan's
      remaining archival todo proceeds. Repo: unified-trading-pm.

## Progress Log

- **2026-08-11 (slot 14, backend_engineer)**: Filed. Discovered while shipping
  `bybit_usdc_deposit_automation_plan_2026_08_11.md` todo 2 — `execution-service` QG red, confirmed pre-existing via
  stash/clean-tree diff isolation. Declared `qg_red` repo-blocker for `execution-service` in the same session.
