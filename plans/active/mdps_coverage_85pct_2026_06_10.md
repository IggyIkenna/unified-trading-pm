---
title: MDPS quality-gates coverage → 85% (logic tests + branch coverage + entry-point omit)
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
priority: P1
status: active
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
created: 2026-06-10
related_plans:
  - plans/active/uac_coverage_90pct_2026_06_10.md
  - plans/active/quality_gates_speed_and_config_ssot_2026_06_09.md
  - plans/active/cicd_contract_hardening_2026_06_01.md
locked_by: live-defi-rollout
locked_since: 2026-06-10
---

# MDPS quality-gates coverage → 85%

## Context

`market-data-processing-service` (MDPS) is a **service** repo (codex service floor **70%**). It had self-elevated to
`fail_under = 77` with `branch = true` (combined statement+branch metric). A **stale** `coverage.xml` (2026-05-28) read
75.51%, but a fresh measurement (2026-06-10) was **74.79% combined** — i.e. the configured gate was **RED against its
own config**: the `77` floor had been set against an older statement-only number, and switching on `branch=true`
(combined metric, branch coverage is harder) dragged actual below it. Default quality gate failed at HEAD.

Operator directive (2026-06-10): raise MDPS to **85% combined** and lock the gate there — a new elevated target above
the 70% service floor, documented the same way as the UAC 90% precedent (codex entry + this plan).

Three levers (mirrors `uac_coverage_90pct_2026_06_10.md`):

- **Lever 1 — Entry-point omit:** only `__main__.py` (3-stmt `run_cli()` shim, no logic) is a legitimate omit. Unlike
  UAC, MDPS has almost no pure-stub surface — `engine/mock_data_provider.py` and `api/main.py` were measured at 0% but
  contain **real logic** (mock_data_provider is imported at runtime by `cli/handlers/process_handler.py`), so they were
  **tested, not omitted** (no `# pragma: no cover` inflation — codex-banned).
- **Lever 2 — Logic-module tests:** the two 0% logic modules (`mock_data_provider.py` 125 stmts, `api/main.py` 17 stmts)
  plus the largest partially-covered modules.
- **Lever 3 — Branch/edge-case tests:** error paths, shard-isolation no-raise loops, typed-error routing, CLI mode
  dispatch on the orchestration-core / CLI / writer modules.

Codex SSOT: `codex/06-coding-standards/quality-gates.md` § "Coverage by repo type".

## Result (2026-06-10)

Fresh combined coverage **74.79% → 86.71%** (statement 89.7% / branch 77.3%); covered lines 5,964 → 6,807; unit tests
1,354 → 1,861 (**+507 new tests**, 0 failures). `fail_under` raised **77 → 85** (≈1.7pt churn headroom above the round
target). Full `scripts/quality-gates.sh --no-fix` green.

## Audit — per-module coverage gains

| Module                                    | Stmts | Before | After | Lever |
| ----------------------------------------- | ----- | ------ | ----- | ----- |
| `app/core/live_workers.py`                | 522   | 58.9%  | ~87%  | 2/3   |
| `app/core/orchestration_service.py`       | 219   | 52.2%  | ~88%  | 2/3   |
| `app/core/orchestration_scanner.py`       | 195   | 62.7%  | ~85%  | 3     |
| `cli/handlers/process_handler.py`         | 296   | 59.2%  | ~92%  | 2/3   |
| `cli/main.py`                             | 131   | 33.7%  | ~97%  | 2/3   |
| `cli/handlers/live_mode_handler.py`       | 142   | 51.9%  | ~92%  | 3     |
| `cli/parser.py`                           | 79    | 67.1%  | 100%  | 3     |
| `cli/handlers/live_aggregator_handler.py` | 37    | 53.5%  | 100%  | 3     |
| `engine/mock_data_provider.py`            | 125   | 0%     | ~91%  | 2     |
| `api/main.py`                             | 17    | 0%     | 100%  | 2     |
| `app/core/canonical_writer.py`            | 594   | 81.2%  | ~89%  | 3     |
| `app/core/dependency_checker.py`          | 213   | 72.5%  | ~99%  | 3     |
| `app/utils/market_state_detector.py`      | 153   | 70.0%  | ~95%  | 3     |
| `__main__.py`                             | 3     | 0%     | omit  | 1     |

### Not pursued (backstop — already over target without them)

- `app/calculators/numba_kernels.py` (181 stmts, 11.9%) — numba-compiled kernels; coverage needs `NUMBA_DISABLE_JIT=1`
  instrumentation. Left for a follow-up if the gate ever needs more headroom; **85% cleared without it**.

## Phased execution

### Phase 1 — Measure + classify + entry-point omit (DONE 2026-06-10)

- [x] ✅ [SCRIPT] P1. Fresh combined-coverage measurement (74.79%) — confirmed gate was RED vs `fail_under=77` —
      `market-data-processing-service`
- [x] ✅ [SCRIPT] P1. Classify 0% modules STUB-vs-LOGIC: `__main__.py` STUB (omit); `mock_data_provider.py` +
      `api/main.py` LOGIC (test) — `market-data-processing-service`
- [x] ✅ [SCRIPT] P1. Add `__main__.py` to `[tool.coverage.run] omit` in `pyproject.toml` —
      `market-data-processing-service`

### Phase 2 — Logic + branch tests (DONE 2026-06-10)

- [x] ✅ [TEST] P1. Orchestration-core tests (`live_workers`, `orchestration_service`, `orchestration_scanner`) —
      `market-data-processing-service`
- [x] ✅ [TEST] P1. CLI tests (`process_handler`, `cli/main`, `live_mode_handler`, `parser`, `live_aggregator_handler`)
      — `market-data-processing-service`
- [x] ✅ [TEST] P1. Engine/writer/checker tests (`mock_data_provider`, `api/main`, `canonical_writer`,
      `dependency_checker`, `market_state_detector`) — `market-data-processing-service`

### Phase 3 — Threshold lock + gate green (DONE 2026-06-10)

- [x] ✅ [SCRIPT] P1. Raise `fail_under` 77→85 in `pyproject.toml` (actual 86.71%) — `market-data-processing-service`
- [x] ✅ [QG] P1. `bash scripts/quality-gates.sh --no-fix` green at 85% floor — `market-data-processing-service`
- [x] ✅ [DOCS] P2. Update `codex/06-coding-standards/quality-gates.md` § "Coverage by repo type" with MDPS 85% combined
      target + rationale — `unified-trading-pm`
- [ ] [QG] P2. Run PM `bash scripts/quality-gates.sh` to confirm plan + codex update pass — `unified-trading-pm`

## Temporary states + their canonical follow-up plans

| Temporary state             | Status                                                                                                |
| --------------------------- | ----------------------------------------------------------------------------------------------------- |
| `fail_under=85`             | Permanent — locked as MDPS elevated coverage gate                                                     |
| `numba_kernels.py` at 11.9% | Acceptable — 85% cleared without it; revisit (NUMBA_DISABLE_JIT) only if the gate needs more headroom |
| Branch coverage at 77.3%    | No separate branch gate; combined metric at ≥85% is sufficient                                        |
