---
title: "Predictions reader migration to canonical_question_group + per-market LookaheadBiasError feature enforcement"
parent_epic: predictions_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: brand-new
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/predictions_master.md
  - ./prediction_manifest_canonicalisation_2026_06_01.md
  - ../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md
---

> **Provenance**: extracted 2026-06-20 from the inline `predictions_master` epic body during the asset-group-umbrella
> restructure (L0 umbrellas had ~30+ stale May-07 inline todos that `regen_backlog_from_plan.py` never scanned). This
> plan is the **genuinely net-new, unowned** consumer-side prediction migration: the reader callsites, feature-compute,
> and strategy-config migration to the canonical `prediction_canonical_question_group` shape, plus the per-market
> `LookaheadBiasError` enforcement in feature compute.
>
> **Boundaries — do NOT duplicate**:
>
> - The manifest/parquet canonicalisation + writer-rebundling (the `category=prediction → asset_group=prediction`
>   migration, the `_index` v9 rebuild, the reflip/reconcilers) is owned by
>   [`prediction_manifest_canonicalisation_2026_06_01.md`](./prediction_manifest_canonicalisation_2026_06_01.md).
> - The **lifecycle-bounded `available_at` stamping** for Polymarket + Kalshi adapters
>   (`available_at = max(tick_ts, market_created_at)`, refuse rows past `market_settlement_time`) is owned by
>   [`available_at_lookahead_bias_completion_2026_05_08`](../archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md)
>   Phase 1 — point there, do NOT include it here. This plan's lookahead todo is the FEATURE-COMPUTE per-market gate,
>   which is distinct from the adapter-level `available_at` write-stamp.

## Context

The adapter-level migration shipped (per the epic body: `umi_tick_provider` rename mtds@3f631b9, Polymarket adapter
lifecycle gating mtds@7643a5c, Kalshi mtds@e8a6903, MARKET_LIFECYCLE-bounded clip mtds@006beab5, cluster validation
mtds@e777dc40). What remains is the CONSUMER side: every reader callsite, feature compute, and strategy archetype config
must reference `prediction_canonical_question_group` + filter on `canonical_question_group` (not the legacy
`<base_asset>` shape), and feature compute must enforce per-market lifecycle so a feature at time T sees only market_ids
where `market_created_at ≤ T`.

## P0 — reader + feature + strategy migration

- [ ] [SCRIPT] P0. **Reader migration**: every callsite with `data_type=BTC|ETH|...` →
      `data_type=prediction_canonical_question_group` + filter on `canonical_question_group`. (Gated on the Phase 1
      lifecycle + adapter migration, which has shipped per the epic body.)
- [ ] [SCRIPT] P0. **Per-market `LookaheadBiasError` enforcement in feature compute**: feature compute at time T can
      only consume ticks where `tick.timestamp ≤ T` AND `tick.market_id`'s `market_created_at ≤ T`. Today
      features-cross-instrument does NOT enforce this per-market; flip to strict-mode check. (This is the SINGLE
      feature-compute lookahead gate — the epic body stated it twice, at the "Reader / feature / strategy migration"
      tier and again at the "completeness hierarchy" tier; written here as ONE todo. Distinct from the adapter-level
      `available_at` write-stamp owned by the `available_at_lookahead_bias_completion` plan.)
- [ ] [SCRIPT] P0. **Strategy-service prediction archetypes**: archetype configs reference `canonical_question_group`
      directly (not `base_asset`).
- [ ] [TEST] P0. **End-to-end smoke**: 1 canonical_group (`BTC_UP_DOWN_HOURLY`) × 1 day; run feature compute + verify
      the migrated reader + per-market lookahead gate produce a correct feature matrix.

## P1 — feature registry

- [ ] [SCRIPT] P1. **Predictions feature_groups → UAC `FEATURE_REQUIRED_INPUTS`**. Per-canonical_question_group +
      per-binary-outcome features need registry entries. Source-of-truth: the features-\* services that consume
      prediction tick data. (Coordinator: `available_at_lookahead_bias_completion` Phase 4 — this is the
      predictions-feature-registry slice.)

## Success criteria

- Zero reader callsites reference the legacy `data_type=<base_asset>` prediction shape; all read
  `prediction_canonical_question_group` + filter on `canonical_question_group`.
- Feature compute raises `LookaheadBiasError` (strict mode) when asked to consume a market_id whose
  `market_created_at > T`.
- Strategy archetype configs reference `canonical_question_group`; the `BTC_UP_DOWN_HOURLY` × 1-day E2E smoke passes
  through feature compute clean.
- Predictions feature_groups registered in UAC `FEATURE_REQUIRED_INPUTS`.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the E2E smoke runs feature compute on a
real `BTC_UP_DOWN_HOURLY` day through the migrated reader path; the per-market lookahead gate is exercised with a market
whose `market_created_at` falls inside the window and confirmed to exclude its rows before that timestamp;
`bash scripts/quality-gates.sh` green on every touched repo before commit.
