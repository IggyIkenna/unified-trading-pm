---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 4 features-service builder_registry + calc base
summary:
  Drop-in migrate mt/volatility/onchain BuilderEntry to UTL, resolver-only migrate sports, swap the one clean boxcox
  helper in delta_one base.py, fix a mis-marked bucket-name inline.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service]
scope: [engineer, admin]
tags: [utl, uac, consolidation, refactor, features, builder-registry, split]
related:
  [
    plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md,
    plans/active/utl_reuse_phase0_guardrails_2026_07_13.md,
  ]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 1.0
locked_by: live-defi-rollout
locked_since: "2026-07-13"
supersedes:
superseded_by:
depends_on: [utl_reuse_phase0_guardrails_2026_07_13]
gate_on_depends: true
source: [split from utl_uac_reuse_consolidation_remediation_2026_06_10 tracker, operator-approved 2026-07-13]
assigned_role: backend-engineer
drift_direction: advance-code
---

# UTL/UAC reuse consolidation — Phase 4 features-service builder_registry + calc base

> **Split provenance (2026-07-13):** Phase 4 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md)
> (finding #5) — **fully unstarted**. **Machine-held** until
> [`utl_reuse_phase0_guardrails_2026_07_13.md`](utl_reuse_phase0_guardrails_2026_07_13.md) lands its golden
> `resolve_build_order` fixture (`depends_on` + `gate_on_depends: true`).

> **Verified reality:** mt/volatility/onchain `BuilderEntry` field sets are identical (onchain just omits
> `lookback_candles`, UTL default `0` reproduces it) and all four `resolve_build_order` bodies are semantically
> identical to UTL's. **sports is genuinely divergent** (function-based builders, `columns`/`required_inputs`/
> `default_kwargs`, no `calculator_name`/`sources`). In `delta_one/app/calculators/base.py` **only `_boxcox_transform`
> is a clean 1:1 swap**; `calculate_zscore` (rolling) and element-wise `calculate_time_since` have **no UTL
> equivalent**.

## Todos

- [x] ✅ [AGENT] P1. **Drop-in migrate** mt, volatility, onchain: delete local `BuilderEntry` + `resolve_build_order`
      (incl. `_build_dag`/`_kahn_bfs`) → `from unified_trading_library import BuilderEntry, resolve_build_order` (match
      the already-shipped calendar/delta_one pattern). Keep `_build_registry`/`get_builder`; volatility keeps its
      orthogonal `_CALCULATOR_CLASS_MAP`. — SHIPPED `features-service@4d9a1656`. All three families now import
      `BuilderEntry`/`resolve_build_order` (aliased `_utl_resolve_build_order`) from `unified_trading_library`; local
      `resolve_build_order()` wrappers reduced to `return _utl_resolve_build_order(_get_registry())`.
      `_build_registry`/`_get_registry`/`get_builder`/`get_all_builders` kept local unchanged; volatility's
      `_CALCULATOR_CLASS_MAP`/`get_calculator_class_name` untouched. onchain never sets `lookback_candles` — UTL's
      default `0` reproduces prior behaviour. Verified via
      `tests/common/test_golden_fixture_phase0_resolve_build_order.py` (all 4 families byte-identical build order),
      `tests/onchain/unit/test_calculators.py::test_resolve_build_order_raises_on_cycle` (UTL's "Dependency cycle in
      builder DAG" message still matches the "Dependency cycle" substring), and the full
      `tests/{multi_timeframe,volatility,onchain}/unit/test_feature_touchup.py` suites (128 passed). Full
      `quality-gates.sh` green, sentinel verified against `4d9a1656`.
- [x] ✅ [AGENT] P1. **sports — resolver-only migration now** (safe: `depends_on`-based, identical semantics):
      `resolve_build_order()` → `_utl_resolve_build_order(_get_registry())`. **Do NOT blind-swap the dataclass.** —
      SHIPPED `features-service@48895959`. Replaced the local hand-rolled Kahn's-algorithm `resolve_build_order()` body
      with a delegation to `unified_trading_library.resolve_build_order`, bridged via
      `cast(dict[str, _UTLBuilderEntry], _get_registry())` since sports keeps its own function-based `BuilderEntry`
      (`function`/`columns`/`required_inputs`/`default_kwargs` — no `calculator_name`/`sources`) and UTL's resolver only
      ever reads `entry.depends_on: list[str]`, a field both shapes carry identically — dataclass NOT swapped, per
      instruction. Verified behaviour-preserving via the Phase 0 golden fixture
      (`test_golden_resolve_build_order_sports`, identical output) plus the existing sports builder-registry suite
      (`test_no_dependency_cycles`, `test_all_groups_present`, `test_phase_0_has_no_deps`,
      `test_meta_features_in_last_phase`, `test_get_builder_returns_entry`/`_unknown_raises` — all green).
      `basedpyright` clean on the cast. `quality-gates.sh` exit 0, sentinel verified.
- [ ] [DESIGN] P2. **sports dataclass — operator/design call**: either (a) add a UTL `FunctionBuilderEntry` sibling
      (callable + `columns` + `required_inputs` + `default_kwargs`), or (b) keep sports' local function-based dataclass.
      Default to (b) unless a 2nd function-based consumer appears (YAGNI).
- [ ] [AGENT] P2. **delta_one base.py — surgical, not wholesale**: migrate `_boxcox_transform` → UTL
      `transformations.boxcox_transform` (adapt the `1e-8` vs `+1` edge-shift) and DELETE local. Leave
      `calculate_time_since` (element-wise log/lookback), `calculate_time_to_next`, rolling `calculate_zscore`,
      `normalize_bounded_metric`/`_logit_transform`, `safe_rolling_metric` (richer than UTL `calculate_rolling_stats`),
      and `normalize_distribution` (boxcox-inclusive, tuple-vs-series mismatch) **local** — UTL has no 1:1. The
      `FeatureCalculator(ABC)` validate/enrich pipeline stays local.
- [ ] [AGENT] P3. **Fix the mis-marked bucket inline** found in passing: `volatility/io/writer.py:35`
      `bucket = f"features-volatility-{ag}-{pid}"` is marked `# CORRECT-LOCAL` but is a genuine miss → use
      `resolve_bucket_name(kind="features-volatility", asset_group=...)` (its own sibling configs already do).
- [x] ✅ [VERIFY] P1. `resolve_build_order` golden output identical per family; `quality-gates.sh` green; quickmerge. —
      VERIFIED (2026-07-13, slot-6) for the migration completed so far: re-ran
      `test_golden_fixture_phase0_resolve_build_order.py` fresh against `features-service@d784c79f` — all 4 families
      (`multi_timeframe`, `volatility`, `onchain`, `sports`) reproduce their pinned golden build order identically. Full
      `quality-gates.sh` green, sentinel verified. **Scope note**: this confirms no regression from the sports
      resolver-only migration (item 2, done) — it does NOT mean mt/volatility/onchain are on UTL yet; item 1 (drop-in
      migrate mt/volatility/onchain) is still open, and their golden values are pinned against their still-local
      implementations, unchanged from before this plan started. No code changes needed here (pure verification) — no
      quickmerge required.

## Success criteria

mt/vol/onchain on UTL `BuilderEntry`; sports resolver on UTL; only `_boxcox_transform` swapped in base.py; volatility
bucket via resolver.

## Notes for the worker

- **MINOR-bump-first ordering** if the sports `FunctionBuilderEntry` design call lands on (a): ship the UTL bump, let
  the range-pin pull carry it, then migrate.
- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
