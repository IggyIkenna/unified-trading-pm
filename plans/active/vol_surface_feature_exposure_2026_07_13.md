---
doc_type: plan
title: Vol-Surface Feature Exposure — per-strike IV grid + multi-underlying vector
summary:
  Expose a per-strike IV-by-moneyness grid and a multi-underlying (index + component) vol-surface feature vector, both
  buildable off the already-live Deribit options feed — unlocks the denser VOL_* strip/structure engines and full-mode
  VOL_DISPERSION/VOL_CROSS_ASSET_SPREAD without waiting on Tardis backfill.
status: active
nature: process
asset_group: [cross-cutting]
stage: [features]
repos: [features-service, strategy-service]
scope: [engineer]
tags: [strategy, v2-engine, vol-trading, features, greeks]
related: [v2_engine_venue_buildout_2026_06_15.md]
created: 2026-07-13
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 4.0
assigned_role: backend-engineer
drift_direction: advance-code
last_updated: 2026-06-27
locked_by:
locked_since:
depends_on:
supersedes:
superseded_by:
source: [v2_engine_venue_buildout_2026_06_15.md follow-up 2026-07-13]
sequential: false
---

# Vol-Surface Feature Exposure

> **Split out 2026-07-13** from [`v2_engine_venue_buildout_2026_06_15.md`](v2_engine_venue_buildout_2026_06_15.md)
> Follow-ups section. Both feature gaps below are buildable NOW off the already-live Deribit options-chain adapter
> (confirmed live for BTC/ETH/SOL/BNB/XRP, 2026-06-15 connectivity proof) — Tardis/backfill is only needed later, to
> _backtest_ the engines that consume these features, not to build the feature-exposure code itself.

## Ground truth — canonical inputs, do not deviate

- Upstream canonical types (already shipped, unified-api-contracts): `CanonicalImpliedVolSurface` /
  `CanonicalIVSurfacePoint` (`unified_api_contracts/canonical/domain/derivatives/greeks.py`), `CanonicalGreeksSnapshot`
  — these are the ONLY inputs; do not invent a parallel schema.
- Existing flat-bucket feature keys (features-service `volatility/vol_surface_feature_extractor.py`,
  `extract_vol_greeks_feature_dict`): `iv_atm`, `iv_25d_call`, `iv_25d_put`, `iv_skew_25d`, `iv_term_1w/1m/3m/6m`,
  `iv_slope_1m_3m`, `delta`/`gamma`/`vega`/`theta`/`rho`. New feature keys added below must NOT collide with these names
  and must follow the same flat `dict[str,float]` on-tick shape (`GroupBRunner.on_tick` is feature-agnostic).
- **Honest absence is mandatory** (existing convention, do not weaken it): a bucket/leg/underlying with no usable data
  omits the key — never synthesise a value. Mirror the existing tests (`OTM-only→no iv_atm`, etc.).
- **`formula_version=1` on every NEW feature key** (no bump to existing keys — this is additive, not a math change), per
  `codex/02-data/feature-formula-versioning.md`.
- Consumers waiting on this (do not re-scope their engines here, just unblock the feature): `VOL_VARIANCE_SWAP`,
  `VOL_RATIO_SPREAD`, `VOL_SPREAD_STRUCTURES` (per-strike grid); `VOL_DISPERSION` full mode, `VOL_CROSS_ASSET_SPREAD`
  (multi-underlying vector) — all tracked in the parent plan, still `BACKTEST-PENDING` on Tardis regardless of this plan
  landing.

## Todos

- [ ] [SCRIPT] P2. Design the per-strike IV-by-moneyness grid feature shape — a denser strike ladder than the 3
      canonical buckets (`iv_atm`/`iv_25d_call`/`iv_25d_put`), keyed by strike/moneyness x expiry/tenor, sourced from
      `CanonicalImpliedVolSurface.points` (already carries per-point moneyness/tenor/implied_vol — this is exposing more
      of an already-fetched surface, not fetching new data). Repo: features-service.
- [ ] [SCRIPT] P2. Implement + unit-test the per-strike grid extractor (mirrors `extract_vol_greeks_feature_dict`'s
      honest-absence pattern — sparse surfaces omit missing strikes, never interpolate/synthesise). `formula_version=1`.
      Repo: features-service.
- [ ] [SCRIPT] P2. Wire VOL_VARIANCE_SWAP / VOL_RATIO_SPREAD / VOL_SPREAD_STRUCTURES
      (`strategy-service/.../vol_trading/`) to consume the denser grid where it's present, falling back to the existing
      3-bucket behavior when absent (do not regress the already-shipped honest-absence tests). Repo: strategy-service.
- [ ] [SCRIPT] P2. Design the multi-underlying vol-surface feature vector — index + per-component surfaces (for
      VOL_DISPERSION) and an explicit asset-pair shape (`iv_atm_asset_a`/`iv_atm_asset_b` etc., for
      VOL_CROSS_ASSET_SPREAD) built from multiple `CanonicalImpliedVolSurface` inputs (one per underlying — the Deribit
      adapter already enumerates BTC/ETH/SOL/BNB/XRP, so multi-asset fetch is not new work, only the feature-vector
      shape is). Repo: features-service.
- [ ] [SCRIPT] P2. Implement + unit-test the multi-underlying extractor, honest-absence on any missing underlying (no
      degraded single-surface synthesis beyond the existing `degraded_single_surface` attestation already in
      VOL_DISPERSION). `formula_version=1`. Repo: features-service.
- [ ] [SCRIPT] P2. Wire VOL_DISPERSION (full mode) + VOL_CROSS_ASSET_SPREAD to consume the multi-underlying vector,
      preserving the existing single-surface degraded fallback for VOL_DISPERSION and the both-surfaces-required honest
      no-trade for VOL_CROSS_ASSET_SPREAD. Repo: strategy-service.

## Progress Log

(loop handoff lands here)
