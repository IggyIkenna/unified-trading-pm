---
title: "BaseFeatureCalculator validation flip — mandatory ClassVar enforcement across 75 calcs (paradigm-split rollout)"
status: active
created: 2026-05-10
deadline: 2026-05-23
prior_deadline: post-cutover (P1 — type-safety hardening, not correctness blocker)
deadline_change_reason: |
  Operator direction 2026-05-13: pulled forward into May-23 scope. "Validation is important and we have space" —
  workspace throughput at ~200 cal-AI-days/day vs ~310 cal-days May-23 remaining = ~5-6x margin.
  Type-safety hardening across 75 calculators improves cutover confidence on production strategies.
priority: P1
horizon: 1-2 week scope-bounded
spawned_from: plans/archive/issues/basefc_validation_flip_audit_2026_05_08.md (archived 2026-05-10)
locked_by: live-defi-rollout
locked_since: 2026-05-10
execution:
  owner: features-service maintainer + UTL maintainer (paired commits)
  cadence: one-shot, post-features-consolidation Phase 6 parity-green
  verifier: ruff + basedpyright clean across features-service after UTL flip; integration smoke green per family
  last_executed: NEVER
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3.0
estimate_calibration_note: |
  Backfilled 2026-05-13: 4 todos, 0 done; design call (paradigm-split strategy decision) drives a refactor across 35-74 calcs. Picked HIGHER (design) per CLAUDE.md "optimism is the failure mode this corrects". Baseline 5 (strategy decision + UTL flip + per-family migration + QG ratchet); × 0.6 = 3.0. post-cutover P1.
---

# BaseFeatureCalculator validation flip

> **Severity**: P1 (post-cutover) — type-safety hardening, not a correctness/data-bug. **Blast radius**:
> features-service (8 family sub-packages, 74 concrete calculator classes) + unified-trading-library
> (`feature_calculator/registry.py`) + per-family base classes. **Suggested owner**: features-service maintainer + UTL
> maintainer paired commits.

## Why this plan exists

Spawned 2026-05-10 from the archived issue
[`plans/archive/issues/basefc_validation_flip_audit_2026_05_08.md`](../archive/issues/basefc_validation_flip_audit_2026_05_08.md).

The Wave-8 BaseFC-ValidationFlip task was scoped against ~12 calculators with `feature_group: ClassVar[str]` +
`feature_family: ClassVar[FeatureFamily]` declarations to migrate. The audit found:

- 74 concrete calculator classes (not 12) across 8 family sub-packages
- ZERO use ClassVar declarations today; all use `@property @abstractmethod` override pattern
- The paradigm split (39 legacy `(FeatureCalculator)` pandas subclasses vs 35 new `(BaseFeatureCalculator)` polars
  subclasses) means the flip can't be a simple `__init_subclass__` enforcement — the 39 legacy subclasses extend a LOCAL
  pandas `FeatureCalculator` base that doesn't share the canonical UTL ABC

## Done definition

- [ ] **[AGENT] P1**. Decide flip strategy across the paradigm split. Options: (a) flip ONLY canonical UTL
      `BaseFeatureCalculator` subclasses (35 calcs); leave legacy pandas `FeatureCalculator` alone as deprecated; (b)
      extend the flip helper to support both inheritance trees; (c) migrate all 39 legacy pandas calcs to the canonical
      `BaseFeatureCalculator` first, then flip universally. Recommendation: (a) — narrow blast radius, isolates the
      change to the polars-canonical surface.
- [ ] **[AGENT] P1**. Migrate concrete calculators from `@property @abstractmethod`/`@property @override` pattern to
      `feature_group: ClassVar[str] = "..."` + `feature_family: ClassVar[FeatureFamily] = FeatureFamily.X`. Per-family
      commits.
- [ ] **[SCRIPT] P1**. Flip UTL canonical `BaseFeatureCalculator.validate_class_attributes()` from opt-in (callable
      helper) to mandatory (`__init_subclass__` enforcement). UTL commit.
- [ ] **[AGENT] P1**. Plan-flip cite: `unified-trading-pm` plan-flip commit pointing at the per-family + UTL commits.

## Full-execution criterion (per "Plans Run To Actual Completion" HARD RULE)

- ✅ All canonical-base calculators declare `feature_group` + `feature_family` as ClassVar.
  - **What ran**: per-family ruff + basedpyright + integration smoke.
  - **Verification**: `grep -rln "feature_group: ClassVar" features-service/` returns ≥35 hits; `__init_subclass__`
    enforcement raises in unit test for a deliberately-malformed subclass.

## Dependencies / sequencing

- **Pre-req**: `features_repo_consolidation_2026_05_08.md` Phase 6 parity-green (reduces flip-target risk by unifying
  the inheritance trees first).
- **Post-cutover**: this plan does NOT block May-23 cutover. Schedule post-cutover wave.

## References

- Archived issue:
  [`plans/archive/issues/basefc_validation_flip_audit_2026_05_08.md`](../archive/issues/basefc_validation_flip_audit_2026_05_08.md)
- Parent plan: [`plans/active/features_repo_consolidation_2026_05_08.md`](features_repo_consolidation_2026_05_08.md)
  (Phase 6 mandatory-validation flip)
- UTL: `unified-trading-library/unified_trading_library/feature_calculator/registry.py` (Generic[DataFrameT] base)
