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

- [x] ✅ [SCRIPT] P2. Design the per-strike IV-by-moneyness grid feature shape — a denser strike ladder than the 3
      canonical buckets (`iv_atm`/`iv_25d_call`/`iv_25d_put`), keyed by strike/moneyness x expiry/tenor, sourced from
      `CanonicalImpliedVolSurface.points` (already carries per-point moneyness/tenor/implied_vol — this is exposing more
      of an already-fetched surface, not fetching new data). Repo: features-service. — DESIGNED (2026-07-13, slot-6), no
      code shipped (design-only; item 2 implements it). Read `CanonicalIVSurfacePoint`/`CanonicalImpliedVolSurface` and
      the full existing `vol_surface_feature_extractor.py` + its tests first — the decision below extends that file's
      existing conventions (moneyness-band delta-proxy, half-open day-range tenor buckets, dict-key-omission honest
      absence), it does not invent new ones. **Decision: extend today's 3-pillar/1-tenor ladder to a 4-wing-pillar ×
      4-tenor grid (16 new keys).** Pillars: keep the existing 25d bands unchanged (call `(1.02, 1.15]`, put
      `[0.85, 0.98)`) and add a 10-delta wing immediately outside them — 10d call `(1.15, 1.40]`, 10d put `[0.60, 0.85)`
      (first-cut heuristic like the existing 25d bands, not real option deltas — MUST be validated/tuned against real
      Deribit strike spacing in item 2). Tenors: reuse the 4 existing `_TENOR_BUCKETS` exactly (`1w`/`1m`/`3m`/`6m`) —
      the ask is a denser STRIKE axis, not a denser tenor axis. ATM row is NOT duplicated (`iv_term_{tenor}` already
      covers ATM-across-tenor), so the grid only adds the 4 non-ATM wing pillars
      (`10d_put`/`25d_put`/`25d_call`/`10d_call`) × 4 tenors. New key names (16 total, zero collisions with
      `iv_atm`/`iv_25d_call`/`iv_25d_put`/`iv_term_*`/`iv_skew_25d`/`iv_slope_1m_3m`): `iv_10d_put_{tenor}`,
      `iv_25d_put_{tenor}`, `iv_25d_call_{tenor}`, `iv_10d_call_{tenor}` for `tenor` in `{1w, 1m, 3m, 6m}` — mirrors
      this SAME module's own `iv_25d_call`/`iv_term_1w` prefix-then-suffix style, deliberately NOT the sibling
      `volatility/calculators/vol_surface_term_structure.py` calculator's `{side}_{pillar}d_iv_{tenor}d` day-count
      convention, since this grid extends `vol_surface_feature_extractor.py` directly and must stay internally
      consistent with its own existing keys, not a different pipeline's convention. Noted for awareness (not this task's
      scope): `vol_surface_term_structure.py` already computes a similar but asymmetric grid (ATM × 5 tenors, wings only
      × 30d) for a DIFFERENT consumer path — it's a batch `resolve_build_order` calculator, not the on-tick
      `extract_vol_greeks_feature_dict` path the listed strategy-service consumers actually read via
      `GroupBRunner.on_tick` — two parallel vol-grid implementations now exist by design, a future dedup opportunity but
      out of scope here. Selection + honest absence: identical rule to today — within a (tenor-bucket ∩ pillar-band)
      intersection, pick the point closest to the band's canonical anchor (mirrors `_pick_otm_iv`'s nearest-within-band
      tie-break); no matching point → omit the key entirely (never `None`/`NaN`/interpolated), exactly the existing
      `assert "<key>" not in result` test style. Derived composites for item 2 to add (mirrors
      `iv_skew_25d`/`iv_slope_1m_3m`, only when both inputs present):
      `iv_skew_25d_{tenor} = iv_25d_put_{tenor} - iv_25d_call_{tenor}`,
      `iv_skew_10d_{tenor} = iv_10d_put_{tenor} - iv_10d_call_{tenor}` (8 more derived keys). `formula_version`: mirror
      this module's own simple `FORMULA_VERSION: int = 1` constant, NOT the `delta_one` `FeatureSpec`
      registry/GCS-partition mechanism in `codex/02-data/feature-formula-versioning.md` — confirmed that mechanism isn't
      used anywhere in the volatility family; matching the direct sibling code being extended is the
      internally-consistent choice (a known pre-existing two-convention split in the repo, not something to reconcile
      here).
- [x] ✅ [SCRIPT] P2. Implement + unit-test the per-strike grid extractor (mirrors `extract_vol_greeks_feature_dict`'s
      honest-absence pattern — sparse surfaces omit missing strikes, never interpolate/synthesise). `formula_version=1`.
      Repo: features-service. — SHIPPED `features-service@6cfe2abf`. Implemented exactly per item 1's design: added
      `_TENOR_SUFFIXES`/`_WING_BANDS` dicts + a tenor-aware `_pick_otm_iv_in_tenor` helper (sibling of the existing
      shortest-tenor-only `_pick_otm_iv`), wired into `extract_vol_surface_features` as a new loop emitting the 16
      `iv_{pillar}_{tenor}` keys plus 8 derived `iv_skew_25d_{tenor}`/`iv_skew_10d_{tenor}` keys — 24 new keys total,
      zero collisions with existing ones, `FORMULA_VERSION` constant unchanged at 1 (matches the sibling-module
      convention decided in item 1). 12 new tests added to `tests/volatility/unit/test_vol_greeks_features.py` covering:
      band+tenor-scoped presence/absence for each of the 4 wing pillars, cross-tenor isolation (a point in the wrong
      tenor bucket doesn't leak into an adjacent one), the ATM-not-duplicated invariant, both skew composites
      (present/absent), float-type assertion, and a full 4-tenor sweep. 42/42 tests pass (30 pre-existing + 12 new, zero
      regressions), `ruff`/`basedpyright` clean, `check-import-patterns.py` 0 violations, full `quality-gates.sh` green
      (265s, sentinel-verified).
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
