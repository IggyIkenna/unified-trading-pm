---
title: features-service QG test path mismatch — 350 per-family unit tests invisible to quality gates
created: 2026-05-15
author: slot-4 (harsh)
source:
  - bash scripts/quality-gates.sh → coverage 3.16% (floor 70%)
  - tests/unit/ (5 files, 46 tests) vs tests/<family>/unit/ (350 files)
locked_by: live-defi-rollout
---

## What I found

`bash scripts/quality-gates.sh` in features-service always fails with **3.16% coverage** (floor 70%) because the base QG
template runs:

```bash
pytest tests/unit/
```

But features-service uses a **per-family layout**:

```
tests/
  unit/                        ← 5 files, 46 tests (run by QG)
  delta_one/unit/              ← ~60+ test files
  cross_instrument/unit/       ← ~60+ test files
  onchain/unit/                ← ~30+ test files
  sports/unit/
  commodity/unit/
  volatility/unit/
  multi_timeframe/unit/
  calendar/unit/
  api/unit/
  ...
```

`find tests -name "*.py" -path "*/unit/*"` → **356 unit test files total** across all directories. Of these, **350**
live in per-family subdirectories and are **never run by QG**.

The tests added in this cycle (TestUACPolicyParity in `tests/delta_one/unit/`, `tests/cross_instrument/unit/`,
`tests/onchain/unit/` — 26 tests) are also invisible to QG, even though they pass locally.

## Why it matters

1. **Coverage gate is toothless** — 3.16% is bogus. The actual unit test coverage is far higher when per-family tests
   are included. But the QG reports failure every time regardless of real coverage state.
2. **QG blocks commits** — the two-pass commit model (Pass 1 = full QG) is effectively broken for features-service since
   QG always fails at the coverage step. Agents working in this repo cannot validate their work via the standard gate.
3. **350 test files unvalidated by CI** — any breakage in per-family tests is invisible until someone runs them
   manually.
4. **New Phase 6 parity tests** (TestUACPolicyParity, 26 tests) are never caught by QG — future key drift in UAC would
   go undetected by automated gates.

## Recommended decision

**Fix the QG test path in `features-service/scripts/quality-gates.sh`** to use `tests/` (all unit tests) instead of the
base-service default `tests/unit/`.

Two options:

**Option A (preferred):** Override `PYTEST_UNIT_DIR` in features-service QG config if base-service supports it, or pass
a custom pytest path argument.

**Option B:** Add a `PYTEST_EXTRA_PATHS` variable to `base-service.sh` that features-service can set to `"tests/"`
(running all subdirectory unit tests).

Either way, the coverage measurement should reflect the actual test suite. The 70% floor may need re-calibration once
the real coverage is measured — likely it is already above 70%.

**Action required:** This is a QG infrastructure fix that requires modifying `base-service.sh` (Ikenna side, since it
touches the PM SSOT template) or adding a per-repo override in `features-service/scripts/quality-gates.sh`. Slot-4
cannot self-fix without touching the PM SSOT template.
