---
title: features-service TODO/FIXME audit — 9 items, 0 stale, 0 quick-fixes
created: 2026-05-19
author: slot-4
source:
  - features-service rg scan (MECH5-TODO-FEATURES_SERVICE)
locked_by: ""
---

> **🟡 SUBSUMED BY MEGA AUDIT** — findings absorbed by **Phase C4 (MTDS → features audit) + Phase C6 (features →
> strategy audit)** per
> [mega_audit_and_plan_beefup_progression_2026_05_20.md](mega_audit_and_plan_beefup_progression_2026_05_20.md) (slot-1
> triage 2026-05-20). 9 TODOs split: Group 1 (futures roll) → C2+C4; Group 2 (aave on-chain) → C4; Group 3 (sports) → C6
> or D5. Do NOT work standalone.

## What I found

9 TODO comments in features-service production code (excluding tests/scripts). All are real, unresolved, non-trivial
items. None are stale. None can be fixed in <5 min.

### Group 1: futures roll adjuster — 4 GH-BACKLOG items

**File**: `features_service/delta_one/app/core/futures_roll_adjuster.py:550-555`

- Load single contract for symbol with no rolls
- Load front and back contracts around each roll date
- Build roll calendar with actual prices
- Stitch contracts together using Panama-method adjustment

These are placeholders for the full futures roll methodology. Currently the adjuster runs without them (likely using
approximations). Scope: instruments-service integration + roll calendar data.

### Group 2: aave on-chain enhancement TODOs

**Files**:

- `features_service/onchain/app/calculators/aave_utilization_calculator.py:44,128`
- `features_service/onchain/app/calculators/aave_rate_impact_calculator.py:69`

Enhancement note: actual on-chain liquidity index requires RPC calls, not just off-chain captures. Currently uses
approximation. Scope: adds RPC dependency, blocked on RPC credentials.

### Group 3: sports module migration TODOs

**Files**:

- `features_service/sports/tracking/__init__.py:3-8` — tracking/ (~1500L fixture registry) should move to
  `unified-internal-contracts/testing/scenarios/` or `unified-sports-reference-interface`
- `features_service/sports/arb/__init__.py:3-8` — `calculate_vig()` / `is_arbitrage()` math utilities should move to UTL
  `domain/sports/` sub-package

## Why it matters

Items 1-2 are functionality gaps (not correctness bugs) — futures roll is incomplete and aave rate math uses
approximations. Items 3 are architecture migration notes that will eventually require PR work across repos.

## Recommended decision

- **Group 1**: Assign to delta-one/tradfi epic when futures-roll feature is scoped.
- **Group 2**: Unblock with RPC credentials → mark BLOCKED-CREDENTIALS. File in aave_utilization epic.
- **Group 3**: Keep in features-service until UTL sports sub-package is created (post-cutover scope). No action before
  May-23.
