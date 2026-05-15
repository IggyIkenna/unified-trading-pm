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
- [ ] [AGENT] P0. Fix cast() wrappers in features_service/adapters/ (expected ~200 errors).
- [ ] [AGENT] P0. Fix cast() wrappers in features_service/onchain/ (expected ~200 errors).
- [ ] [AGENT] P0. Fix remaining errors in other modules.
- [ ] [AGENT] P0. Verify basedpyright 0 errors, run quality-gates.sh, commit+push.
- [ ] [AGENT] P0. Flip checkbox in defi_master_2026_05_07.md.

## Temporary states + their canonical follow-up plans

None.
