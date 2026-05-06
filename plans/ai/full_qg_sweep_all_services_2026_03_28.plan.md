---
title: "Full QG Sweep — All Services + Coverage Restoration"
status: active
priority: P0
created: 2026-03-28
locked_by: live-defi-rollout
locked_since: 2026-03-28
owner: human
---

# Full QG Sweep — All Services + Coverage Restoration

## Context

Post-consolidation contract alignment (2026-03-28) got 7 bottom-tier repos passing: PM ✅ | UAC ✅ | UTL ✅ | IS ✅ |
UMI ✅ | MTDS ✅ | MDPS ✅

But 22 service repos are ALL FAILING quality gates. Additionally, several repos had coverage thresholds dropped below
70% during the consolidation session.

**Goal: All 29 Python repos pass QG with MIN_COVERAGE ≥ 70%. No exceptions.**

## Archived Test Files Available for Migration

323 test files from archived repos that were merged during consolidation. These tests already cover the merged code —
just need import path updates.

| Merge Target                         | Archived Source                       | Test Files | Current Coverage |
| ------------------------------------ | ------------------------------------- | ---------- | ---------------- |
| **UTL** (65%)                        | unified-trading-library               | 12         |                  |
|                                      | unified-cloud-interface               | 27         |                  |
|                                      | unified-config-interface              | 26         |                  |
|                                      | unified-features-interface            | 6          |                  |
|                                      | unified-feature-calculator-library    | 11         |                  |
|                                      | unified-feature-orchestration-library | 3          |                  |
|                                      | unified-ml-interface                  | 24         |                  |
|                                      | unified-domain-client                 | 18         |                  |
|                                      | **Subtotal: 127 test files**          |            | Target: 70%      |
| **IS** (25%)                         | unified-reference-data-interface      | 25         | Target: 70%      |
| **execution-service**                | unified-trade-execution-interface     | 51         |                  |
|                                      | unified-defi-execution-interface      | 22         |                  |
|                                      | unified-sports-execution-interface    | 42         |                  |
|                                      | **Subtotal: 115 test files**          |            | Target: 70%      |
| **position-balance-monitor-service** | unified-position-interface            | 10         | Target: 70%      |
| **UAC** (84%)                        | unified-internal-contracts            | 46         | Already ≥70%     |

Archive location: `/Users/ikennaigboaka/Code/unified-trading-system-repos/archive/`

**Migration strategy:** Copy test folders → update imports (`unified_trading_library.events` →
`unified_trading_library.events_interface`, etc.) → run tests → fix failures → measure coverage.

## Coverage Debt (ALL repos must reach 70%)

| Repo                     | Current | Target | Strategy                                      |
| ------------------------ | ------- | ------ | --------------------------------------------- |
| unified-trading-pm       | 48%     | 70%    | Write tests for PM validation/checker scripts |
| unified-trading-library  | 65%     | 70%    | Migrate 127 archived test files               |
| unified-market-interface | 68%     | 70%    | Write tests for new adapters                  |
| instruments-service      | 25%     | 70%    | Migrate 25 archived URDI test files           |
| market-tick-data-service | 28%     | 70%    | Write tests for handlers + adapters           |

## Service QG Failures (22 repos)

### Category A: Lint only (11 repos — auto-fixable)

| Repo                              | Errors                    |
| --------------------------------- | ------------------------- |
| execution-service                 | 5 ruff errors             |
| position-balance-monitor-service  | 16 ruff errors            |
| pnl-attribution-service           | 4 ruff errors             |
| alerting-service                  | 3 ruff errors             |
| batch-live-reconciliation-service | 1 ruff error              |
| features-volatility-service       | 1 ruff error              |
| features-calendar-service         | 4 ruff errors             |
| features-multi-timeframe-service  | Import pattern violations |
| ml-inference-service              | 1 ruff error              |
| ml-training-service               | 2 ruff errors             |
| deployment-api                    | 3 ruff errors             |

### Category B: Test failures (7 repos — need investigation)

| Repo                              | Failures            | Root Cause                      |
| --------------------------------- | ------------------- | ------------------------------- |
| trading-agent-service             | 12 failed, 6 errors | L1 data refresh loops           |
| features-delta-one-service        | 5 failed            | Output schema null validation   |
| features-cross-instrument-service | 17 failed           | CLI + event logging             |
| features-onchain-service          | 1 failed            | Live handler publish            |
| features-sports-service           | 18 failed, 4 errors | Mode switching, PIT enforcement |
| deployment-service                | 3 failed, 3 errors  | Shard calc, CLI utils           |
| unified-trading-api               | 1 failed            | UnifiedCloudConfig usage        |

### Category C: Codex compliance only (4 repos)

| Repo                       | Violations                           |
| -------------------------- | ------------------------------------ |
| strategy-service           | 12 violations                        |
| risk-and-exposure-service  | 2 violations                         |
| features-commodity-service | 3 violations                         |
| client-reporting-api       | 5 violations (incl. brittle getattr) |

## Execution Phases

```
Phase 1 (PARALLEL)       Phase 2 (PARALLEL)       Phase 3 (PARALLEL)       Phase 4
├─ Cat A: 11 lint ──►    ├─ Cat B: 7 test ──►     ├─ Coverage: migrate ─►  ├─ Full sweep
│  ruff --fix             │  fix failures           │  archived tests        │  all 29 repos
├─ Cat C: 4 codex ──►    │                         │  for 6 repos           │  ≥70% coverage
│  excludes+source        │                         │  (PM,UTL,UMI,IS,      │
│                         │                         │   MTDS,exec-svc)       │
```

### Phase 1: Lint + Codex fixes (PARALLEL — 15 repos)

- [ ] [AGENT] P0. **Batch lint fix: execution-service** — `ruff check --fix` + remaining manual fixes
- [ ] [AGENT] P0. **Batch lint fix: position-balance-monitor-service** — 16 ruff errors
- [ ] [AGENT] P0. **Batch lint fix: pnl-attribution-service** — 4 ruff errors
- [ ] [AGENT] P0. **Batch lint fix: alerting-service** — 3 ruff errors
- [ ] [AGENT] P0. **Batch lint fix: batch-live-reconciliation-service** — 1 ruff error
- [ ] [AGENT] P0. **Batch lint fix: features-volatility-service** — 1 ruff error
- [ ] [AGENT] P0. **Batch lint fix: features-calendar-service** — 4 ruff errors
- [ ] [AGENT] P0. **Batch lint fix: features-multi-timeframe-service** — import patterns
- [ ] [AGENT] P0. **Batch lint fix: ml-inference-service** — 1 ruff error
- [ ] [AGENT] P0. **Batch lint fix: ml-training-service** — 2 ruff errors
- [ ] [AGENT] P0. **Batch lint fix: deployment-api** — 3 ruff errors
- [ ] [AGENT] P0. **Codex fix: strategy-service** — 12 violations
- [ ] [AGENT] P0. **Codex fix: risk-and-exposure-service** — 2 violations
- [ ] [AGENT] P0. **Codex fix: features-commodity-service** — 3 violations
- [ ] [AGENT] P0. **Codex fix: client-reporting-api** — 5 violations

### Phase 2: Test failures (PARALLEL — 7 repos)

- [ ] [AGENT] P0. **Fix: trading-agent-service** — 12 failed + 6 errors
- [ ] [AGENT] P0. **Fix: features-delta-one-service** — 5 failed
- [ ] [AGENT] P0. **Fix: features-cross-instrument-service** — 17 failed
- [ ] [AGENT] P0. **Fix: features-onchain-service** — 1 failed
- [ ] [AGENT] P0. **Fix: features-sports-service** — 18 failed + 4 errors
- [ ] [AGENT] P0. **Fix: deployment-service** — 3 failed + 3 errors
- [ ] [AGENT] P0. **Fix: unified-trading-api** — 1 failed

### Phase 3: Coverage restoration to ≥70% (PARALLEL per repo)

Migrate archived tests first (update imports), then write new tests for gaps.

- [ ] [AGENT] P1. **PM 48% → 70%** — write tests for validation scripts (check-import-patterns, check_schema_provenance,
      check_manifest_import_alignment, check-repo-readiness), checker scripts (triad_assertion_checker,
      fixture_drift_checker, flow_coverage_scorecard), and manifest utilities
- [ ] [AGENT] P1. **UTL 65% → 70%** — migrate 127 test files from archive (unified-trading-library → events_interface/,
      unified-cloud-interface → cloud_interface/, unified-config-interface → config_interface/,
      unified-features-interface → features_interface/, unified-feature-calculator-library → feature_calculator/,
      unified-ml-interface → ml/, unified-domain-client → domain_client/). Update imports:
      `from unified_trading_library.events import X` → `from unified_trading_library.events_interface import X`, etc.
- [ ] [AGENT] P1. **UMI 68% → 70%** — write tests for recently added adapters (DeFi LST, sports, prediction, gas price)
- [ ] [AGENT] P1. **IS 25% → 70%** — migrate 25 test files from archive/unified-reference-data-interface/tests/. Update
      imports: `from unified_reference_data_interface import X` → `from instruments_service.reference_data import X`
- [ ] [AGENT] P1. **MTDS 28% → 70%** — write tests for handlers (gas_fee_handler, solana_defi_handler,
      evm_defi_handler), adapters (hyperliquid_s3, umi_tick_provider), and orchestrator
- [ ] [AGENT] P1. **execution-service → 70%** — migrate 115 test files from archive (unified-trade-execution-interface →
      trade_execution/, unified-defi-execution-interface → defi_execution/, unified-sports-execution-interface →
      sports_execution/). Update imports accordingly.

### Phase 4: Full QG validation

- [ ] [AGENT] P0. **Run QG on all 29 Python repos** — every repo must show LOCAL_PASS with MIN_COVERAGE ≥ 70%
- [ ] [AGENT] P0. **Verify no repo has MIN_COVERAGE < 70%** in quality-gates.sh (except SIT at 2%)

## Success Criteria

- **All 29 repos**: `bash scripts/quality-gates.sh` → LOCAL_PASS
- **Coverage**: MIN_COVERAGE ≥ 70% for ALL repos (only exception: system-integration-tests)
- **Zero suppressions of real failures**
- **No backward-compat debt**
