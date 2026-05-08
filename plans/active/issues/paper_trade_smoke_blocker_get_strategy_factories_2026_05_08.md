---
title: "🚨 P0 BLOCKER — paper-trade smoke harness stale import (get_strategy_factories) blocks ALL DeFi paper smokes"
created: 2026-05-08
author: ikenna-tab1-main
source:
  - e2e-testing/scripts/defi/run-paper.sh (existing canonical paper-trade harness)
  - e2e-testing/scripts/defi/colocated_engine.py:306 (broken import)
  - strategy-service/strategy_service/cli/handlers/batch_utils.py (refactored 2026-05-01, V1-RETIRE Phase 2)
  - plans/active/issues/paper_trade_smoke_carry_staked_basis_runbook_2026_05_08.md (Tab 1 runbook)
  - plans/active/defi_master_2026_05_07.md
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# 🚨 P0 BLOCKER — paper-trade smoke harness stale import

> **Severity**: P0 — May-23 lead-archetype gating step is BROKEN. **Blast radius**: ALL DeFi paper-trade smokes (every
> strategy_id in `STRATEGY_CATEGORIES["DEFI"]` — AAVE_LENDING, BASIS_TRADE, STAKED_BASIS, SOL_STAKED_BASIS, etc.).
> **Suggested owner**: defi_master Fork 1 + operator triage (urgent).

## What I found

Tab 1 main agent attempted to execute the paper-trade smoke runbook (PM@b1bd92e6) per operator direction "do everything"
on 2026-05-08. The canonical harness `e2e-testing/scripts/defi/run-paper.sh --strategy SOL_STAKED_BASIS` invokes
`colocated_engine.py` which crashes at startup with:

```
File "/Users/ikennaigboaka/Code/.../e2e-testing/scripts/defi/colocated_engine.py", line 306, in _create_strategy
    from strategy_service.cli.handlers.batch_utils import get_strategy_factories
ImportError: cannot import name 'get_strategy_factories' from 'strategy_service.cli.handlers.batch_utils'
```

Root cause: strategy-service refactored `batch_utils.py` per V1-RETIRE Phase 2 (2026-05-01). The legacy factory
dispatcher at line 128 is marked `RETIRED in V1-RETIRE Phase 2 (2026-05-01)`. New shape is
`StrategyDispatch.from_strategy_type` (registry-keyed classmethod, line 233). `colocated_engine.py` was not migrated.

**Result: zero DeFi paper-trade smokes have run since 2026-05-01** — a week of silent rot before being caught when an
operator (or this Tab 1 agent) actually attempted to execute the runbook.

## Why it matters

1. **May-23 lead-archetype gating**: paper-trade smoke is the success criterion for `master_to_live_defi_2026_05_23.md`
   Group F item 17 + Group G item 23 (DART manual-trade gate). Without it, May-23 LIVE-on-real-wallet milestone has
   no end-to-end proof that strategy → execution → PBM → risk wiring works.
2. **Cross-cutting failure**: blocks every DeFi strategy — not just `carry_staked_basis`. Affects Fork 1 + Fork 2 +
   any DeFi archetype operator wants to paper-test.
3. **Silent rot signal**: 7 days of un-detected breakage matches the gap pattern user flagged
   ("runbooks shipped + nobody runs them + harness rots"). Need an operator-runnable smoke executed periodically (cron
   or daily Tab assignment) to catch this class of regression.

## Recommended fix

`colocated_engine.py:306` migration to V1-RETIRE Phase 2 dispatch shape. Per
`strategy_service/cli/handlers/batch_utils.py:233`:

```python
# OLD (broken):
from strategy_service.cli.handlers.batch_utils import get_strategy_factories

# NEW (V1-RETIRE Phase 2):
from strategy_service.cli.handlers.batch_utils import StrategyDispatch
# At call site:
dispatch = StrategyDispatch.from_strategy_type(strategy_id)
```

**Owner**: strategy-service maintainer who owns the V1-RETIRE Phase 2 refactor. The migration touches
`colocated_engine.py` extensively (the file was probably designed pre-refactor to expect the legacy factory). May
require multiple call-site updates beyond line 306.

**Tab 1 main agent will NOT ship this fix** per workspace "Two teammates × multiple parallel agents" rule (the
e2e-testing/scripts/defi/colocated_engine.py file is outside Tab 1's clear context).

## Recommended decision

1. **Operator immediate**: assign a Tab to migrate `colocated_engine.py` to the new dispatch shape. ~1-2 AI-days.
2. **Add periodic execution**: cron-wakeup or daily Tab assignment to actually run the paper-trade smoke. Catches
   silent rot like this.
3. **Catalog reference**: paper-trade smoke listed as Group F item 17 success criterion → must be actually green
   before May-23.

Cross-references:

- Tab 1 paper-trade runbook: `plans/active/issues/paper_trade_smoke_carry_staked_basis_runbook_2026_05_08.md`
- Tab 1 work-split: `plans/active/work_split_2026_05_08_ikenna.md` § "TAB 1 Item 1"
- Strategy-service V1-RETIRE: search commit history `git log --all --oneline -- strategy-service/strategy_service/cli/handlers/batch_utils.py`
