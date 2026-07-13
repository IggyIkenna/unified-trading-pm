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

- [ ] [AGENT] P1. **Drop-in migrate** mt, volatility, onchain: delete local `BuilderEntry` + `resolve_build_order`
      (incl. `_build_dag`/`_kahn_bfs`) → `from unified_trading_library import BuilderEntry, resolve_build_order` (match
      the already-shipped calendar/delta_one pattern). Keep `_build_registry`/`get_builder`; volatility keeps its
      orthogonal `_CALCULATOR_CLASS_MAP`.
- [ ] [AGENT] P1. **sports — resolver-only migration now** (safe: `depends_on`-based, identical semantics):
      `resolve_build_order()` → `_utl_resolve_build_order(_get_registry())`. **Do NOT blind-swap the dataclass.**
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
- [ ] [VERIFY] P1. `resolve_build_order` golden output identical per family; `quality-gates.sh` green; quickmerge.

## Success criteria

mt/vol/onchain on UTL `BuilderEntry`; sports resolver on UTL; only `_boxcox_transform` swapped in base.py; volatility
bucket via resolver.

## Notes for the worker

- **MINOR-bump-first ordering** if the sports `FunctionBuilderEntry` design call lands on (a): ship the UTL bump, let
  the range-pin pull carry it, then migrate.
- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
