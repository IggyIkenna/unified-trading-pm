---
doc_type: plan
title: contract-completeness-checker-2026-03-10
summary: Add AST-based completeness checkers for UIC and UAC that detect public classes defined in source but absent from
  __all__, with SIT tests and GHA wiring.
status: completed
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [system-integration-tests, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-internal-contracts, code: C5, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-api-contracts, code: C5, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: system-integration-tests, code: C5, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
depends_on: []
todos:
- {
    id: write-check-uic-completeness,
    content: 'Write unified-internal-contracts/scripts/check_uic_completeness.py — AST-scan UIC source, diff against __all__, exit 1 if gaps.',
    status: done,
    note: DONE (94411e6) — 0 missing.,
    verified:
      '2026-08-15 VERIFIED (review, slot 7, per measurement-claims-discipline — confirmed via gh api commit lookup
      against the still-extant-on-GitHub IggyIkenna/unified-internal-contracts repo, not a local-workspace-absence
      assumption): the DONE (94411e6) claim is ACCURATE. Commit 94411e6c71b833e7db059d12d4347a40630a9cd0
      (2026-03-10T13:35:53Z, Rollout Agent) genuinely added scripts/check_uic_completeness.py (178 lines, file
      status "added") to unified-internal-contracts. The repo/dir absence from the current local workspace is
      CONFIRMED-BUILT-THEN-RETIRED, not fabrication — unified-internal-contracts was later formally eliminated
      and merged into unified-api-contracts as the unified_api_contracts.internal subpackage (2026-03-26, per
      codex/10-audit/_archive/unified-internal-contracts.yaml), which is why it and check_uic_completeness.py are
      absent from this workspace today. No correction to the done-claim itself is needed.',
  }
- {id: add-10-missing-uic-classes, content: Add 10 missing UIC domain classes (features_liquidity + features_sports domains) to unified_internal_contracts/__init__.py __all__., status: done, note: DONE — 0 missing after fix.}
- {id: write-check-uac-completeness, content: 'Write unified-api-contracts/scripts/check_uac_completeness.py — AST-scan UAC source, diff against __all__, exit 1 if gaps.', status: done, note: DONE (3761420) — 163 missing (curation backlog).}
- {id: write-sit-uic-completeness, content: Write system-integration-tests/tests/integration/test_uic_completeness.py — parametrized SIT test mirroring the script., status: done, note: DONE.}
- {id: write-sit-uac-completeness, content: Write system-integration-tests/tests/integration/test_uac_completeness.py — parametrized SIT test mirroring the script., status: done, note: DONE.}
- {id: wire-gha, content: Add UIC + UAC completeness check steps (warn-mode) to system-integration-tests/.github/workflows/smoke-test-gate.yml contract-adoption-check job., status: done, note: DONE.}
- {id: uac-curator-review, content: Curator review of 163 UAC missing classes — decide PROMOTE (add to __all__) or EXEMPT (add to checker EXEMPT_MISSING) for each., status: done, note: 'DONE 2026-03-11 — check_uac_completeness.py reports 0 missing (330 exported, 225 defined in source). Curation complete.'}
isProject: false
---

# Plan: Contract Completeness Checkers (UIC + UAC)

## Status: DONE (2026-03-10) — scripts + SIT tests + GHA wiring all complete; UIC 0 missing, UAC 0 missing

## Created: 2026-03-10

## Context

The adoption checkers (`check_uic_adoption.py`, `check_uac_adoption.py`) verify the **forward direction**: classes in
`__all__` must have at least one terminal consumer importer. There is no check for the **reverse direction**: a public
class defined in UIC/UAC source files that was never added to `__all__`.

This gap was confirmed on 2026-03-10 via manual grep: **10 UIC domain classes** exist in source but are absent from
`__all__`:

- `BookDepthFeature1m`, `CompositeSRFeature1m`, `FlowInteractionFeature1m`, `LiquidationClusterFeature1m`,
  `LiquidityWallEvent` — features_liquidity domain
- `HalfTimeFeatureRecord`, `RefereeFeatureRecord`, `SeasonContextFeatureRecord`, `VenueContextFeatureRecord`,
  `SportsMLPredictionRecord` — features_sports domain

Without a completeness check, new schemas added to source silently never become importable by services.

---

## Scope

Two new scripts + two new GHA steps + two new SIT tests:

| Artifact                                     | Repo                       | Purpose                                                       |
| -------------------------------------------- | -------------------------- | ------------------------------------------------------------- |
| `scripts/check_uic_completeness.py`          | unified-internal-contracts | AST-scan UIC source → diff against `__all__`                  |
| `scripts/check_uac_completeness.py`          | unified-api-contracts      | AST-scan UAC source → diff against `__all__`                  |
| `tests/integration/test_uic_completeness.py` | system-integration-tests   | SIT parametrized test mirroring the script                    |
| `tests/integration/test_uac_completeness.py` | system-integration-tests   | SIT parametrized test mirroring the script                    |
| `.github/workflows/smoke-test-gate.yml`      | system-integration-tests   | Add both completeness checks to `contract-adoption-check` job |

---

## Part 1: `check_uic_completeness.py`

**File:** `unified-internal-contracts/scripts/check_uic_completeness.py`

### Algorithm

```
1. Glob all *.py files under unified_internal_contracts/ (excluding __init__.py, tests/, __pycache__)
2. For each file: ast.parse → walk → collect ast.ClassDef nodes with public names (no leading _)
3. Also collect: functional TypedDict (X = TypedDict("X", ...)), StrEnum/IntEnum subclasses,
   NewType aliases (X = NewType(...))  → these are less common in UIC but UAC uses them
4. Build set: ALL_DEFINED_PUBLIC
5. Load __all__ from __init__.py (same regex as check_uic_adoption.py)
6. missing_from_all = ALL_DEFINED_PUBLIC - set(__all__) - KNOWN_INTERNAL
7. Exit 1 if any missing; print each missing name
```

### `KNOWN_INTERNAL` exclusion list (UIC)

Base/mixin classes that are implementation details, not contracts:

```python
KNOWN_INTERNAL = frozenset([
    # Pydantic/TypedDict infrastructure — not contracts themselves
    "BaseModel",       # re-exported from pydantic; never defined in UIC source
    # Abstract base classes used only within UIC
    "_BaseSchema",     # if any private base class slips through with non-_ convention
])
```

> The list starts small. The script should print the `KNOWN_INTERNAL` additions needed if the gap count is unreasonably
> high.

### Output

```
Loading UIC source files...
Found 247 public class definitions across 34 source files.
Found 195 entries in __all__.
MISSING from __all__ (10):
  BookDepthFeature1m        (unified_internal_contracts/domain/features_liquidity/__init__.py)
  CompositeSRFeature1m      (unified_internal_contracts/domain/features_liquidity/__init__.py)
  ...
Exit code 1 — add missing classes to __all__ or KNOWN_INTERNAL.
```

### Fix for 10 known gaps

After the script exists, a companion task adds the 10 missing domain classes to `unified_internal_contracts/__init__.py`
`__all__`. These are real contracts that services should be able to import. Then run adoption checker to get to 0
orphans for them too.

---

## Part 2: `check_uac_completeness.py`

**File:** `unified-api-contracts/scripts/check_uac_completeness.py`

Same algorithm as UIC but with a larger `KNOWN_INTERNAL` list because UAC has more internal-only types:

```python
KNOWN_INTERNAL = frozenset([
    # UAC internal base classes
    "_CanonicalBase",
    "_ExternalBase",
    # Pydantic config / validator inner classes
    "Config",        # inner class in Pydantic v1 models
    "model_config",  # Pydantic v2 ConfigDict is not a class def
    # Protocol adapter base classes (venue-specific, not cross-service contracts)
    "BaseVenueAdapter",
    "BaseNormalizer",
])
```

> Tune after first run. Expected gap is larger than UIC's 10. Any genuine contract missing from `__all__` gets added;
> pure implementation types get added to `KNOWN_INTERNAL`.

---

## Part 3: SIT Tests

### `test_uic_completeness.py`

```python
# system-integration-tests/tests/integration/test_uic_completeness.py
import ast, importlib, pkgutil
import pytest
import unified_internal_contracts as uic

def get_defined_classes(pkg_path):
    """Return set of public class names defined in source (not imported)."""
    defined = set()
    for finder, name, ispkg in pkgutil.walk_packages(pkg_path):
        # ... AST walk ...
    return defined

def test_uic_no_public_class_missing_from_all():
    """Every public class defined in UIC source must be in __all__."""
    defined = get_defined_classes(uic.__path__)
    in_all = set(uic.__all__)
    missing = defined - in_all - KNOWN_INTERNAL
    assert not missing, f"{len(missing)} UIC classes missing from __all__: {sorted(missing)}"
```

### `test_uac_completeness.py`

Mirror of the above for UAC.

---

## Part 4: GHA Wiring

**File:** `system-integration-tests/.github/workflows/smoke-test-gate.yml`

In the `contract-adoption-check` job, add two new steps after the existing UIC/UAC/UTL adoption checks:

```yaml
- name: Run UIC completeness check
  run: |
    python3 workspace/unified-internal-contracts/scripts/check_uic_completeness.py \
      --workspace workspace >> uic_completeness_gaps.txt 2>&1 || true
    if [ -s uic_completeness_gaps.txt ]; then
      echo "::warning::UIC completeness gaps found (classes in source but not in __all__)"
      cat uic_completeness_gaps.txt
    fi

- name: Run UAC completeness check
  run: |
    python3 workspace/unified-api-contracts/scripts/check_uac_completeness.py \
      --workspace workspace >> uac_completeness_gaps.txt 2>&1 || true
    ...
```

> Note: Start as **warning** (non-blocking) since there are existing gaps. Upgrade to blocking after all gaps are
> resolved.

---

## Implementation Order

1. **Write `check_uic_completeness.py`** — run locally, confirm it finds the 10 known gaps
2. **Add 10 missing UIC domain classes to `__all__`** — then run adoption checker for them (expect new orphans → follow
   `orphan-contracts-utilization.md` pattern to wire each into a service)
3. **Write `check_uac_completeness.py`** — run locally, baseline the gap count
4. **Add UAC missing classes to `__all__`** — follow orphan-uac-utilization pattern
5. **Write SIT tests** — parametrized, mirror adoption coverage tests pattern
6. **Wire into GHA** — as warnings first, promote to blocking once gaps hit 0

---

## Key Files

| File                                                                  | Action                                     | Status                                             |
| --------------------------------------------------------------------- | ------------------------------------------ | -------------------------------------------------- |
| `unified-internal-contracts/scripts/check_uic_completeness.py`        | CREATE                                     | ✅ Done (94411e6) — 0 missing                      |
| `unified-api-contracts/scripts/check_uac_completeness.py`             | CREATE                                     | ✅ Done (3761420) — 163 missing (curation backlog) |
| `unified-internal-contracts/unified_internal_contracts/__init__.py`   | ADD 10 missing domain classes to `__all__` | Done                                               |
| `system-integration-tests/tests/integration/test_uic_completeness.py` | CREATE                                     | Done                                               |
| `system-integration-tests/tests/integration/test_uac_completeness.py` | CREATE                                     | Done                                               |
| `system-integration-tests/.github/workflows/smoke-test-gate.yml`      | ADD 2 new steps (warn-mode)                | Done                                               |

## Baseline Results (2026-03-10)

### UIC (check_uic_completeness.py)

- 195 exported in `__all__`, 186 defined in source
- **0 missing** — UIC is fully covered ✅
- Note: `__all__` has 9 more entries than source classes because it includes non-class constants
  (`VM_INFRASTRUCTURE_EVENTS`, `EXECUTION_AUDIT`, `STRATEGY_AUDIT`) and some re-exported enums

### UAC (check_uac_completeness.py)

- 166 exported in `__all__`, 224 defined in scoped source
- **163 missing** — curation backlog
- Source breakdown:
  - `unified_normalised_contracts/domain.py`: 40 classes (CanonicalTicker, CanonicalTrade, CanonicalOrderBook, etc.)
  - `unified_normalised_contracts/errors.py`: 23 classes (CanonicalError, CanonicalRateLimitError, etc.)
  - `unified_normalised_contracts/execution.py`: 15 classes (OrderSide, OrderType, TimeInForce, etc.)
  - `schemas/derivatives.py`: 20 classes (VolSurface, PositionRisk, etc.)
  - `schemas/risk.py`: 10 classes (VaR, stress tests)
  - `schemas/protocol_sdks.py`: 35 classes (DeFi protocol action params)
  - Other schemas/\*: remaining 41 classes
- Many in `unified_normalised_contracts/` are core canonical schemas that SHOULD be in `__all__`
- UAC `__init__.py` does selective promotion (no `from .schemas import *`) — gaps are intentional narrowing vs true gaps
- Next step: curator review — for each of the 163, decide PROMOTE (add to `__all__`) or EXEMPT (add to checker's
  `EXEMPT_MISSING`)

---

## Verification

```bash
# After writing scripts:
source .venv-workspace/bin/activate

python3 unified-internal-contracts/scripts/check_uic_completeness.py --workspace .
# Expect: 10 missing classes listed, exit 1

python3 unified-api-contracts/scripts/check_uac_completeness.py --workspace .
# Expect: some missing classes listed, exit 1

# After adding missing classes to __all__ and wiring orphans:
python3 unified-internal-contracts/scripts/check_uic_completeness.py --workspace .
# Expect: exit 0

python3 unified-api-contracts/scripts/check_uac_completeness.py --workspace .
# Expect: exit 0
```

---

## Notes

- Both raw and normalised UAC schemas belong in `__all__`: raw schemas are consumed by instrument-service adapters;
  normalised canonical schemas are consumed by downstream services. Both sides of the normalisation boundary are public
  contracts.
- UIC is a pure internal contract library — every public class defined there is by definition a cross-service contract
  and should be in `__all__`.
- `KNOWN_INTERNAL` is the escape hatch for genuine implementation-only types (base classes, validators, mixins). Keep it
  small and documented.
