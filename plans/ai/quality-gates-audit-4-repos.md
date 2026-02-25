# Quality Gates Audit: 4 Repos (Batch 1)

**Audit Date:** 2026-02-23  
**Baseline:** instruments-service (strict, codex-aligned)  
**Scope:** instruments-service, unified-cloud-services, market-tick-data-handler, market-data-processing-service

---

## Summary

| Repo | QG Pass | Coverage | ≥35% | Live Mode | Pyright | Warnings Fail | Tests >2min | Parallel | Deps |
|------|---------|----------|------|-----------|---------|----------------|------------|----------|------|
| **instruments-service** | ✅ | 59% | ✅ | ✅ | mypy (opt) | ✅ ruff | ~37s | ✅ -n auto | ✅ |
| **unified-cloud-services** | ✅ | 35.7% | ✅ | N/A (lib) | ✅ 0 warn | ✅ | ~26s | ✅ | ✅ no private |
| **market-tick-data-handler** | ✅ | **12%** | ❌ | ❌ | ✅ | ❌ | ~105s | ✅ | ✅ |
| **market-data-processing-service** | ✅ | 36% | ✅ | ✅ | ✅ | ❌ | ~29s | ✅ | ✅ |

---

## 1. instruments-service (BASELINE)

### Status: ✅ PASSING (reference)

- **Coverage:** 59% (≥35% ✅)
- **Test duration:** ~37s (quick mode)
- **Parallel:** `-n auto` (pytest-xdist)
- **Live mode:** ✅ `live_mode_handler.py`, `--mode live`
- **Dependencies:** UCS, UCI, UEI, UMI, UDS (per dependency matrix)
- **Codex compliance:** PASS (some WARN: Any type, GOOGLE_CLOUD_PROJECT - non-blocking)
- **Ruff:** E,F,W,I - warnings fail (ruff checks are errors)
- **Type check:** mypy (optional, non-blocking)
- **Local QG:** Skips integration/e2e/smoke (TODO); CI runs all
- **Fixtures:** conftest.py session fixtures, shared fixtures

### Gaps / Notes
- Codex WARNs (Any type, GOOGLE_CLOUD_PROJECT) do NOT fail - consider making strict
- Integration/e2e/smoke skipped locally

---

## 2. unified-cloud-services

### Status: ✅ PASSING

- **Coverage:** 35.7% (≥35% ✅)
- **Test duration:** ~26s (quick mode)
- **Parallel:** ✅ CPU cores
- **Live mode:** N/A (library)
- **Dependencies:** ✅ **No private repo deps** (PyPI only) - per dependency matrix
- **Pyright:** ✅ **0 errors, 0 warnings** - FAILS on any warning
- **Ruff:** E,F,I,W,UP - strict

### Gaps / Notes
- None identified for library scope

---

## 3. market-tick-data-handler

### Status: ⚠️ PASSING (with critical gaps)

- **Coverage:** **12%** ❌ (below 35%)
- **Test duration:** ~105s
- **Parallel:** ✅
- **Live mode:** ❌ "Streaming operations removed - not implementing live streaming yet"
- **Dependencies:** UCS, UCI, UEI, UMI (per matrix)
- **Pyright:** PASS

### Critical Gaps

1. **Coverage not enforced in quick mode**
   - `quality-gates.sh` line 351: `pytest tests/unit/ -v --tb=short -m "not slow"` — **no `--cov` or `--cov-fail-under=35`**
   - Full mode (line 374) also has no coverage in unit tests
   - Result: 12% coverage passes quality gates

2. **Live mode missing**
   - Parser: "Streaming operations removed - not implementing live streaming yet"
   - Config has `live_dataset`, `live_partition_type` but no live mode handler

3. **Needs more tests**
   - Coverage 12% → need ~+23% to reach 35%

### Needed

- Add `--cov=market_data_tick_handler --cov-fail-under=35` to quality-gates.sh
- Implement live mode (or document as out-of-scope)
- Add unit tests to reach 35% coverage

---

## 4. market-data-processing-service

### Status: ✅ PASSING

- **Coverage:** 36% (≥35% ✅)
- **Test duration:** ~29s
- **Parallel:** ✅
- **Live mode:** ✅ `live_mode_handler.py`
- **Dependencies:** UCS, UCI, UEI, UMI, UDS (per matrix)
- **Pyright:** PASS

### Gaps / Notes

- Codex compliance: some checks may be WARN not FAIL (verify)
- Consider aligning Pyright strictness with UCS (0 warnings)

---

## Cross-Cutting Findings

### 1. Linter strictness: warnings fail?

- **instruments-service:** ruff `select = ["E","F","W","I"]` — any violation fails
- **UCS:** Pyright `0 errors, 0 warnings` — FAIL on warnings
- **market-tick-data-handler:** ruff — no `--max-warnings 0` explicitly; ruff fails on any violation by default
- **market-data-processing-service:** similar

### 2. UI smoke tests

- None of these 4 repos are UI repos
- UI smoke tests: see `quality-gates-ui-typescript.md`; backtest-ui, onboarding-ui, etc. need `tsc --noEmit` + ESLint, not pytest

### 3. Test structure

- **instruments-service:** conftest.py session fixtures, pytest-xdist; tests >2min in full mode
- **market-tick-data-handler:** 105s; parallel OK
- **UCS:** 26s; parallel OK
- **market-data-processing-service:** 29s; parallel OK

### 4. Codex epics compliance

- Not fully audited per epic; recommend separate epic-completion audit

---

## Recommendations (Priority Order)

1. **market-tick-data-handler:** Add coverage enforcement to quality-gates.sh (quick + full modes)
2. **market-tick-data-handler:** Add unit tests to reach 35% coverage
3. **market-tick-data-handler:** Implement live mode or document as deferred
4. **instruments-service:** Consider making Codex WARNs (Any type, GOOGLE_CLOUD_PROJECT) blocking
5. **All repos:** Ensure UI repos use `--max-warnings 0` for ESLint if not already
