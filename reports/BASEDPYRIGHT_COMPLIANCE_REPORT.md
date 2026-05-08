# Basedpyright Compliance Report

**Plan:** strict_basedpyright_compliance.md **Generated:** 2026-03-04 **SSOT:**
`.cursor/plans/strict_basedpyright_compliance.md`

---

## Requirements

- `typeCheckingMode: "strict"` in pyrightconfig.json
- `reportAny: "error"`
- Run `timeout 120 basedpyright <source_dir>/` (never `basedpyright .`)
- T0–T3: zero `# type: ignore` in production source
- T0–T3: zero `Any` in public API

---

## Summary

| Tier | Repos Passed | Repos Failed | Notes                                                                      |
| ---- | ------------ | ------------ | -------------------------------------------------------------------------- |
| T0   | 5            | 1            | unified-cloud-interface has errors; unified-reference-data-interface FIXED |
| T1   | 1            | 1            | unified-trading-library has 398 errors, 793 warnings                       |
| T2   | 1            | 1            | unified-market-interface has 2707 errors (reportAny)                       |
| T3   | 1            | —            | unified-domain-client passes                                               |

---

## Per-Repo Results

| Repo                             | Tier | pyrightconfig           | basedpyright             | type:ignore | Any in public API                     |
| -------------------------------- | ---- | ----------------------- | ------------------------ | ----------- | ------------------------------------- |
| unified-api-contracts            | T0   | strict, reportAny error | 0 errors                 | 0           | PASS                                  |
| unified-config-interface         | T0   | strict, reportAny error | 0 errors                 | 0           | PASS                                  |
| unified-trading-library          | T0   | strict, reportAny error | 0 errors                 | 0           | PASS                                  |
| unified-internal-contracts       | T0   | strict, reportAny error | 0 errors                 | 0           | PASS                                  |
| unified-cloud-interface          | T0   | strict, reportAny error | 50 errors, 295 warnings  | —           | FAIL (reportUnknown\*)                |
| unified-reference-data-interface | T0   | strict, reportAny error | 0 errors                 | 0           | PASS                                  |
| unified-trading-library          | T1   | strict, reportAny error | 398 errors, 793 warnings | —           | FAIL (excludes many modules)          |
| unified-domain-client            | T3   | —                       | 0 errors                 | —           | PASS                                  |
| unified-market-interface         | T2   | —                       | 2707 errors              | —           | FAIL (reportAny in websocket/manager) |

---

## Recommended Fixes

1. **Phase 0 baseline** (phase0_standards_enforcement.md): Run basedpyright on all repos, document all bypasses.
2. **unified-cloud-interface**: Fix reportUnknown\* by adding explicit types.
3. **unified-reference-data-interface**: Fix TypedDict access in bybit.py (use .get() or make keys required).
4. **unified-trading-library**: Reduce exclude list; fix types in included modules.
5. **unified-market-interface**: Fix reportAny in websocket/manager.py — add TypedDict/Protocol for message types.

---

## Execution Order

T0 first → T1 → T2 → T3 → services.
