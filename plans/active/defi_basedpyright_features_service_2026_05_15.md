---
title: "basedpyright reportAny cleanup — features-service"
created: 2026-05-15
author: ikenna
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
locked_by: live-defi-rollout
locked_since: 2026-05-15
---

**MIGRATED FROM:** `defi_master_2026_05_07.md` line 292 deferral **Status:** DEFERRED — 825 reportAny errors remain in
features-service

## Context

features-service has 825 `reportAny` errors blocking basedpyright clean. The other 3 DeFi service repos
(strategy-service, risk-and-exposure-service, execution-service) are at 0 errors.

This plan tracks the remaining work to bring features-service to 0 reportAny errors.

## Error profile (2026-05-15 snapshot)

825 errors, primarily in:

- `features_service/calculators/` — numpy array operations + pandas row access
- `features_service/adapters/` — external API resp.json() calls
- `features_service/onchain/` — driftpy / web3 untyped attributes

## Approach

Same patterns as execution-service fix:

- `cast(dict[str, object], resp.json())` for HTTP response bodies
- `cast(list[float], arr.tolist())` for numpy arrays
- `cast(object, getattr(obj, "attr", default))` for untyped library objects
- `cast(int, df["col"].iloc[0])` for pandas scalar extraction

## Tasks

- [ ] [AGENT] P0. Run basedpyright on features-service and triage top 10 error locations.
- [ ] [AGENT] P0. Fix cast() wrappers in features_service/calculators/ (expected ~300 errors).
  - [x] ✅ transfer_window_calculator.py 32→0 errors — features-service@9183f81f (slot-8 2026-05-17)
  - [x] ✅ season_context.py 28→0 errors — features-service@5199db4d (slot-8 2026-05-17)
  - [x] ✅ team_form.py 28→0 errors — features-service@62e460cf (slot-8 2026-05-17)
  - [x] ✅ sports_validity_engine.py 26→0 errors (engine/ surface) — features-service@d2013034 (slot-8 2026-05-17)
  - [x] ✅ poisson_xg_calculator.py 17→0 errors — features-service@5aa6079f (slot-8 2026-05-17)
  - [x] ✅ elo_calculator.py 17→0 errors — features-service@5aa6079f (slot-8 2026-05-17)
  - [x] ✅ delta_one/app/calculators/returns.py 23→0 errors — features-service@e14fdae8 (slot-8 wave 2 2026-05-17)
  - [x] ✅ delta_one/app/calculators/trendline.py 19→0 errors — features-service@e14fdae8 (slot-8 wave 2 2026-05-17)
  - [x] ✅ delta_one/app/utils/numba_kernels.py 37→0 errors — features-service@be6f01a5 (slot-8 wave 2 2026-05-17)
  - [x] ✅ delta_one/app/calculators/streaks.py 18→0 errors — features-service@8828900b (slot-8 wave 2 2026-05-17)
  - [x] ✅ delta_one/app/calculators/market_structure_sequence.py 14→0 errors — features-service@8828900b (slot-8 wave 2 2026-05-17)
  - [x] ✅ sports/calculators/travel_calculator.py 14→0 errors — features-service@360a804d (slot-8 wave 2 2026-05-17)
  - [x] ✅ sports/calculators/referee_features.py 14→0 errors — features-service@360a804d (slot-8 wave 2 2026-05-17)
  - [x] ✅ sports/calculators/halftime_calculator.py 14→0 errors — features-service@360a804d (slot-8 wave 2 2026-05-17)
  - [x] ✅ sports/calculators/advanced_stats_calculator.py 14→0 errors — features-service@360a804d (slot-8 wave 2 2026-05-17)
- [ ] [AGENT] P0. Fix cast() wrappers in features_service/adapters/ (expected ~200 errors).
- [ ] [AGENT] P0. Fix cast() wrappers in features_service/onchain/ (expected ~200 errors).
- [ ] [AGENT] P0. Fix remaining errors in other modules.
- [ ] [AGENT] P0. Verify basedpyright 0 errors, run quality-gates.sh, commit+push.
- [ ] [AGENT] P0. Flip checkbox in defi_master_2026_05_07.md.

## Temporary states + their canonical follow-up plans

None.
