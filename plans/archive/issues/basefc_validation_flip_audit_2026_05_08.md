---
title:
  "BaseFeatureCalculator validation flip — audit reveals 75 calcs across paradigm-split, not 12; needs successor plan"
created: 2026-05-08
author: wave-8-basefc-validationflip-sub-agent
source:
  - plans/active/features_repo_consolidation_2026_05_08.md (Phase 6 mandatory-validation flip)
  - plans/active/work_split_2026_05_08_ikenna.md (Wave-8 BaseFC-ValidationFlip Tab)
  - unified-trading-library/unified_trading_library/feature_calculator/registry.py (UTL@9936e7b6 Generic[DataFrameT]
    base)
  - features-service/features_service/{cross_instrument,delta_one,multi_timeframe,calendar,onchain,volatility,sports,commodity}/
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# BaseFeatureCalculator validation flip — audit reveals 75 calcs across paradigm-split, not 12

> **Severity**: P1 (post-cutover) — type-safety hardening, not a correctness/data-bug. **Blast radius**:
> features-service (6 family sub-packages, 74 concrete calculator classes) + unified-trading-library
> (`feature_calculator/registry.py`) + per-family base classes. **Suggested owner**: spawn
> `plans/active/basefc_validation_flip_2026_05_XX.md` post-features-consolidation Phase 6 parity-green.

## What Wave-8 was asked to ship

Per work_split_2026_05_08_ikenna.md Wave-8 prompt:

1. Audit features-service calculators for `feature_group: ClassVar[str]` + `feature_family: ClassVar[FeatureFamily]`
   declarations.
2. Migrate ~12 calculators missing the declarations.
3. Flip UTL canonical `BaseFeatureCalculator.validate_class_attributes()` from opt-in (callable helper) to mandatory
   (`__init_subclass__` enforcement).
4. Per-family commits → UTL flip commit → PM plan-flip.

## What the audit actually found

### Calculator counts (workspace-grep verified 2026-05-08)

74 concrete calculator class definitions across 8 family sub-packages of `features-service/features_service/`:

| Family             | Legacy `(FeatureCalculator)` subclasses | `(BaseFeatureCalculator)` subclasses | Notes                                                                                                                                                                          |
| ------------------ | --------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `delta_one`        | 35                                      | 4                                    | 33 of 35 extend a **LOCAL pandas `FeatureCalculator`** at `features_service/delta_one/app/calculators/base.py:235`, NOT the canonical UTL class                                |
| `cross_instrument` | 0                                       | 21                                   | All inherit polars-based `BaseFeatureCalculator(_CanonicalBaseFeatureCalculator[pl.DataFrame])` from `features_service/cross_instrument/app/calculators/base_calculator.py:40` |
| `multi_timeframe`  | 0                                       | 9                                    | Polars-based local base; same shape as cross_instrument                                                                                                                        |
| `calendar`         | 4                                       | 0                                    | All extend pandas-based `FeatureCalculator` from `unified_trading_library` (which extends canonical `BaseFeatureCalculator`)                                                   |
| `onchain`          | 0                                       | 1                                    | `OnChainCalculator(BaseFeatureCalculator, ABC)` at `features_service/onchain/app/calculators/base.py:36`                                                                       |
| `volatility`       | 0                                       | 0                                    | Service uses dispatcher pattern; no `class X(FeatureCalculator)` definitions in this scan                                                                                      |
| `sports`           | 0                                       | 0                                    | Same — dispatcher/builder pattern, no concrete `Calculator` subclasses                                                                                                         |
| `commodity`        | 0                                       | 0                                    | Same                                                                                                                                                                           |
| **Total**          | **39**                                  | **35**                               | **74 classes**                                                                                                                                                                 |

`grep -rln "feature_group: ClassVar\b\|feature_family: ClassVar\b" features_service/ --include="*.py"` returns **0
hits** — zero concrete calculators currently use ClassVar declarations.

### How calculators currently declare `feature_group` (the existing override pattern)

Per-family base class declares `feature_group` as an `@property @abstractmethod` to satisfy the canonical UTL ABC's
`ClassVar[str] = ""` slot without ClassVar-vs-property collision:

```python
# features_service/cross_instrument/app/calculators/base_calculator.py:84-88
@property
@abstractmethod
def feature_group(self) -> str:  # pyright: ignore[reportIncompatibleVariableOverride]
    """Feature group name for GCS path (Phase 6 will migrate to ClassVar)."""
    pass
```

Concrete subclasses then override via `@property @override` returning a string literal:

```python
# features_service/multi_timeframe/calculators/tf_session_context.py:54-56
@property
def feature_group(self) -> str:
    return "tf_session_context"
```

The comment at base_calculator.py:73-83 + plan body line 1441 explicitly defer concrete-calc ClassVar migration to
"Phase 6 mandatory-validation flip".

### Why `feature_family` ClassVar declaration is at family-base level, not per-calculator

Every calculator in `features_service/cross_instrument/` has the same `feature_family = FeatureFamily.CROSS_INSTRUMENT`.
Same for delta_one / multi_timeframe / etc. The right place to declare `feature_family: ClassVar[FeatureFamily]` is the
per-family base class (5 declarations), not 74 per-calculator declarations. This deviates from the original Wave-8
prompt's "per-calculator declaration" recipe.

### Critical paradigm split that breaks the original plan

**33 of 35 delta_one calculators extend a LOCAL `FeatureCalculator` class at
`features_service/delta_one/app/calculators/base.py:235`** — that local class does NOT extend canonical UTL
`BaseFeatureCalculator` at all (it's a standalone ABC with `@abstractmethod calculate(...)`).

Flipping UTL canonical `validate_class_attributes()` to `__init_subclass__`-mandatory would **NOT fire** on these 33
delta_one calculators because they aren't canonical subclasses. The validation flip therefore needs a paradigm-bridge
step FIRST: extend the local pandas `FeatureCalculator` to inherit from canonical `BaseFeatureCalculator[pd.DataFrame]`.
That's a separate refactor (~33 calculator surface).

### Required migration sequence (3 steps, in order)

1. **Step A — paradigm bridge** (~33 delta_one pandas-legacy calculators). Extend
   `features_service/delta_one/app/calculators/base.py:235` `class FeatureCalculator(_FeatureCalculatorStatsMixin, ABC)`
   to `class FeatureCalculator(_FeatureCalculatorStatsMixin, _CanonicalBaseFeatureCalculator[pd.DataFrame])`. Verify
   smoke imports clean.
2. **Step B — per-family `feature_family: ClassVar[FeatureFamily]` declarations** (5 per-family base edits:
   cross_instrument / delta_one / multi_timeframe / calendar / onchain). One ClassVar declaration each; all subclasses
   inherit.
3. **Step C — concrete `feature_group: ClassVar[str]` migrations** (74 calculator edits). Each migrates
   `@property @override def feature_group` returning literal → `feature_group: ClassVar[str] = "<literal>"` declaration.
   Removes the per-family `@property @abstractmethod` slot + scoped `pyright: ignore`.
4. **Step D — UTL canonical validation flip**. `BaseFeatureCalculator.__init_subclass__` calls
   `validate_class_attributes()` automatically; deprecate the standalone helper. Tests cover the new mandatory failure
   mode + migration path.

## Why Wave-8 did NOT ship code

1. **75-edit refactor with paradigm bridge in-flight is multi-day, not single-Tab scope**. The original prompt's "~12
   calculators" assumed all candidates were canonical-subclassing. Reality is 6×.
2. **Foot-gun #2 risk on UTL `feature_calculator/registry.py`**. UTL working tree had the file unstaged-modified by a
   parallel agent (Tab B Wave 7 work, line-wrap formatter) at audit time — editing it during this window risks bundling
   foreign hunks per CLAUDE.md "mandatory pre-commit check" failure modes.
3. **Plan body line 1441 + 1444 explicitly defer concrete-calc ClassVar migration to Phase 6 of
   features_repo_consolidation_2026_05_08.md**, SEQUENTIAL after parity-green. Phase 6 is currently `[ ]`; Phase 5 just
   shipped the canonical Generic[DataFrameT] base (UTL@9936e7b6).
4. **Ordering hazard**. Original prompt instructed "flip UTL AFTER consumers migrate, else UTL change breaks consumers
   immediately" — correct. Shipping the UTL flip without first migrating 74 concrete subclasses is banned.
5. **"Plans Run To Actual Completion" HARD RULE**. A partial migration (e.g. flip UTL + migrate only canonical-extending
   35 calcs, leave 39 legacy unfixed) is the exact pattern banned by 2026-05-08 user direction "we tend to make scripts
   and stuff... not actually do full backfills or full runs."

## Why it matters

- **No data-correctness impact today.** Validation is currently opt-in via callable helper;
  `validate_class_attributes()` is invoked nowhere in production paths. Existing `@property @abstractmethod` runtime
  overrides correctly enforce the contract at instantiation time (concrete subclasses must override to be instantiable).
- **Type-safety hardening only.** The flip removes per-family `@property @abstractmethod` re-declaration boilerplate +
  scoped `pyright: ignore[reportIncompatibleVariableOverride]` annotations. Reduces drift surface.
- **Post-cutover scope.** Not blocking 2026-05-23 live-DeFi cutover because: (a) the runtime contract holds via property
  abstractness; (b) `feature_group` / `feature_family` are correctly populated wherever they're consumed today (manifest
  writes, GCS paths, registry routing).

## Recommended decision

**Spawn a successor plan** at `plans/active/basefc_validation_flip_2026_05_XX.md` (post-Phase-6 parity-green). 4 phases
as enumerated above (A. paradigm bridge → B. family-base ClassVar[FeatureFamily] → C. 74 concrete ClassVar[str]
migrations → D. UTL `__init_subclass__` mandatory flip + tests). Estimated 3-5 days. Full-execution criterion:
workspace-grep verifies zero `(BaseFeatureCalculator)` subclass without ClassVar declarations + `__init_subclass__`
validation fires on regression test.

**Do NOT** include scope in the current `features_repo_consolidation_2026_05_08.md` plan — that plan's Phase 6 is
parity-test, Phase 7 is repo archival; expanding it dilutes the 2026-05-08 closeout. Better to file as a separate clean
post-cutover refactor.

**Existing plan-body annotation at line 1444** of `features_repo_consolidation_2026_05_08.md` already captures this
audit (in unstaged form, foreign WIP — Wave-8 left untouched per CLAUDE.md "don't edit unfamiliar files"). When that
annotation lands via its author's commit, this issue doc can be cross-referenced and either folded back into the plan
body or kept as the durable record.

## Composes with

- `features_repo_consolidation_2026_05_08.md` Phase 6 parity-test gate (must land first).
- CLAUDE.md "Plans Run To Actual Completion" HARD RULE (banned partial migrations).
- CLAUDE.md "Two teammates × multiple parallel agents — don't edit unfamiliar files" (avoided UTL `registry.py`
  collision per Wave-8 audit window).
- Existing scoreboard row `BaseFeatureCalculator polars/pandas paradigm split` (line 1441) — the polars/pandas split
  shipped 2026-05-08 evening per UTL@9936e7b6; this validation flip is the next step in the same chain.
