---
doc_type: issue
title:
  e2e-testing test_collateral_validation.py imports a module deleted 2.5 months ago — 9 scenarios silently dead, zero CI
  protection
summary:
  A test aimed squarely at "does the strategy layer block posting the wrong collateral at the wrong venue" fails at
  import time and has for ~2.5 months; the property it checks does still hold in production, but through a different,
  newer mechanism that nothing in e2e-testing regression-protects.
status: open
nature: issue
asset_group: defi
stage: strategy
repos: [e2e-testing, strategy-service]
scope: engineer
tags: [testing-gap, defi, staked-basis, collateral, dead-code, ci-gap]
related: [pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21]
created: 2026-07-23
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: agent-discovered (e2e-testing vs prod DeFi corner-case audit, 2026-07-23)
depends_on: []
---

# e2e-testing collateral-validation test — dead import since 2026-05-01, 9 scenarios never run

## Finding

`e2e-testing/scripts/defi/test_collateral_validation.py` imports:

```python
from strategy_service.engine.strategies.defi_enhancements import (
    CollateralValidationMixin,
    max_leverage_for_token,
)
```

This module (`strategy_service/engine/strategies/_archived_pre_v2/defi_enhancements.py`, 755 lines + its own 686-line
unit test) was **permanently deleted 2026-05-01** in `strategy-service@a7f6f795` ("feat!: V1-RETIRE Phase 2 -- delete v1
strategy source"). Grepped `CollateralValidationMixin` / `max_leverage_for_token` across the **entire workspace** (every
repo) — the only remaining reference anywhere is this one e2e-testing import.

Because it's a module-level import, **all 9 scenarios in the file fail at import time**, not just the 3 (scenarios 7-9)
that actually reference the deleted symbols. Scenarios 1-6 use only still-live `unified-api-contracts` registry
functions (`venue_accepts_collateral`, `get_collateral_haircut`, `needs_wrapping`) and would otherwise pass, but the
file can't reach them.

**Silently broken for ~2.5 months** across at least 6 subsequent commits to the file (2026-05-12, 05-15, 05-23, 06-17,
06-23, 07-16 — lint/style/lifecycle-marker touches, never a real run). Root cause it was never caught:
`strategy-service/scripts/quality-gates.sh` (lines ~137-148) runs `basedpyright` + `ruff check` over
`e2e-testing/scripts/defi/`, but both are wired through `log_warn` (non-blocking) for that path — no gate actually
**executes** the script, so neither a basedpyright unresolved-import error nor the runtime `ModuleNotFoundError` can
ever fail a build.

## Is the actual safety property still enforced in production? Yes — by a different, newer mechanism

Traced and confirmed live (2026-07-23, same audit pass):

- `strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_staked_basis.py`
  `_resolve_start_token()` → UAC `accepted_perp_collateral()` — catalog-level filter, only emits slots for (LST,
  perp_venue) combos the venue actually accepts as margin.
- `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py` `_BANNED_LST_PERP_COMBOS`
  (lines ~130-142, ~444-457) — engine-level defense-in-depth ban for combos the raw collateral matrix technically marks
  `accepted=True` but that are unsafe in practice (e.g. `(wstETH,BYBIT)` — Bybit's margin engine calibrates on rebasing
  stETH, not wstETH price); raises `ValueError` in `_build_legs()`.

Both are v2, both are live, both were read in full this session. **The underlying property holds in production today** —
this is a test-integrity gap, not a live collateral-safety bug.

## Why this matters anyway

Nothing in `e2e-testing` currently regression-protects the mechanism that actually does the work
(`_resolve_start_token`/`accepted_perp_collateral` + `_BANNED_LST_PERP_COMBOS`). If either regresses, no CI signal would
catch it — the one test aimed at this exact property is dead code that nobody would notice failing, because it's already
failing and nobody notices.

## Recommendation (not yet actioned — needs an operator call on approach)

- **A — Rewrite `test_collateral_validation.py` against the current v2 mechanism** (drive `catalog_staked_basis.py`'s
  `build_carry_staked_basis()` + `staked_basis.py`'s `_BANNED_LST_PERP_COMBOS` directly, the way
  `test_csb_paper_e2e_smoke.py` and `test_failure_modes_e2e_smoke.py` already correctly do for other CSB properties).
  **[RECOMMENDED]** — restores real coverage of the property the file was clearly meant to protect.
- **B — Delete the file.** Minimal, but leaves this property's regression coverage solely to the two catalog/engine unit
  tests (if those exist and are adequate — not verified in this pass).
- **C — Leave as-is, but make the QG gate over `e2e-testing/scripts/defi/` blocking (not `log_warn`) so a future dead
  import at least fails loudly**, even without fixing this specific file today.

## Related follow-up (broader, not this doc's scope)

The same audit pass (2026-07-23) found `e2e-testing/scripts/defi/funding_ensemble_engine.py` hardcodes
`LST_VENUES = {"ETH": ("stETH","Bybit")}` with **zero** imports of `strategy_service`/`unified_api_contracts` — it
happens to match current prod state today but will silently drift if `VENUE_COLLATERAL_MATRIX` ever changes. Lower
severity (exploratory script, not a gated test) — noted here for visibility, not filed separately.

## Evidence / files read (2026-07-23 audit)

- `e2e-testing/scripts/defi/test_collateral_validation.py` (542 lines, all 9 scenarios)
- `strategy-service` git history: `a7f6f795` ("feat!: V1-RETIRE Phase 2 -- delete v1 strategy source", 2026-05-01)
- `strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog_staked_basis.py`
- `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py`
- `strategy-service/scripts/quality-gates.sh` (the `log_warn`-wired e2e-testing lint block)
