---
title: "UTL `quality-gates.sh` has 6 pre-existing failure categories (post-117-sweep finding)"
created: 2026-05-14
author: slot-3-harsh
source:
  - unified-trading-library/scripts/quality-gates.sh
  - utl@26ded7d (post-117-test-fixture sweep)
severity: P1
status: filed (pre-existing; not blocking my sweep done-def)
locked_by: live-defi-rollout
locked_since: 2026-05-14
routing:
  primary_owner: operator triage (multi-area cleanup; not single-owner)
  composes_with: utl_117_test_fixture_pipeline_mode_sweep_closed_2026_05_14.md
---

## What I found

Per slot 3 Day-3 Wave 2 done-def ("117 UTL tests pass via `bash scripts/quality-gates.sh`;
pre-existing-foreign issues filed as issue docs with owner-tag"), the 117 test sweep
is shipped at utl@`26ded7d`. The **test step** of `quality-gates.sh` passes
(3482 tests pass, 5 skipped, 9 xfailed per separate freshness-monitor issue doc).

However, the **full QG run fails on 6 unrelated pre-existing categories** that
were already failing on `origin/live-defi-rollout` before my sweep:

### 1. STEP 5.5 — Direct cloud SDK imports

```text
./unified_trading_library/instrument_lifecycle_loader.py
```

`from google.cloud import storage` at module scope. Was present on
`origin/live-defi-rollout` parent commit (`55424a9`) before my sweep — not
introduced by me. Should be routed through `unified_cloud_interface`
`get_storage_client()`.

### 2. Backward-compat patterns

```text
unified_trading_library/kill_switch/bus.py:    audit-log-disabled (backward-compatible with pre-2026-05-11 callers).
unified_trading_library/kill_switch/bus.py:        # Bridge to legacy subscribers for backward compatibility.
unified_trading_library/treasury/approval_bus.py:        idempotency_key: Redundant alias for request_id (backward compat).
```

Violates `cursor-rules/core/no-backward-compat-shims.mdc`. All pre-existing.

### 3. Function/class/method size exceeded (22 violations)

```text
scenario/runner.py:110:ScenarioRunner.run(): 51L
treasury/approval_bus.py:120:ApprovalBus.collect_approvals(): 100L
treasury/withdrawal_audit_log.py:54:WithdrawalAuditLog.append(): 59L
treasury/withdrawal_reconciler.py:94:WithdrawalReconciler.reconcile(): 85L
treasury/withdrawal_executor.py:171:WithdrawalExecutor.withdraw(): 73L
kill_switch/bus.py:286:KillSwitchBus.arm(): 51L
kill_switch/bus.py:338:KillSwitchBus.disarm(): 60L
post_trade/statement_emitter.py:51:DailyStatementEmitter.emit_daily_statement(): 54L
post_trade/settler.py:179:SettlementHandler.settle_trade(): 89L
post_trade/settler.py:269:SettlementHandler.accrue_daily_fees(): 68L
post_trade/settler.py:338:SettlementHandler.update_hwm_ledger(): 81L
post_trade/hwm_crystallization.py:128:HWMCrystallizer.crystallize_at_period_boundary(): 112L
allocation/engine.py:111:AllocationEngine.allocate_per_client(): 115L
circuit_breaker/recovery.py:268:BreakerRecoveryEngine.evaluate(): 87L
streaming/live_aggregator.py:341:MDPSStreamingAggregator.run(): 53L
streaming/live_aggregator.py:411:MDPSStreamingAggregator.aggregate_window(): 82L
streaming/live_aggregator.py:556:MDPSStreamingAggregator.cascade_parent_candle(): 75L
synthetic/harness.py:287:BenchmarkHarness._run_stage(): 82L
synthetic/harness.py:372:BenchmarkHarness.run(): 112L
client_lifecycle/onboarding.py:254:ClientOnboardingStateMachine.advance(): 105L
feature_service_base/live_aggregator.py:459:CrossCuttingFeaturesRunner.run(): 102L
feature_service_base/live_aggregator.py:654:CrossCuttingFeaturesRunner.process_aligned_window(): 95L
feature_service_base/live_aggregator.py:750:CrossCuttingFeaturesRunner._emit_stale_data(): 51L
```

Per coding standards, method limit is 50L. 22 methods exceed; concentrated in
`treasury/`, `post_trade/`, `streaming/live_aggregator.py`, `feature_service_base/`,
`synthetic/harness.py`. Pre-existing.

### 4. pip-audit vulnerabilities

```text
urllib3 2.6.3 — CVE-2026-44431  fix=2.7.0
urllib3 2.6.3 — CVE-2026-44432  fix=2.7.0
```

Workspace-wide dep issue; fix is `uv pip install urllib3>=2.7.0` (probably
via `pyproject.toml` bump). Affects every Python repo, not UTL-specific.

### 5. STEP 5.23 — Deep UAC imports (10 callsites)

```text
unified_trading_library/manifest_writer.py
unified_trading_library/risk/family_aggregator.py
unified_trading_library/availability_stamping.py
unified_trading_library/reconcile/order_state.py
unified_trading_library/reconcile/pnl_clock_batch_live.py
unified_trading_library/reconcile/manifest.py
unified_trading_library/reconcile/onchain.py
unified_trading_library/reconcile/balance.py
unified_trading_library/streaming/live_aggregator.py
unified_trading_library/treasury/withdrawal_reconciler.py
unified_trading_library/feature_service_base/live_aggregator.py
```

Imports from `unified_api_contracts.canonical.crosscutting.*` (UAC-internal
path) instead of facade. 5 callsites have `# noqa: qg-deep-import` justification
("not yet on root facade; lift when UAC root facade re-exports"); 5 do not.
Composite scope: needs UAC facade re-exports (Ikenna territory) + per-callsite
migration.

### 6. Codex compliance: 14 violations

(Detail aggregated from STEP 5.21 / 5.22 / 5.23 output.)

## Why it matters

These do not block the 117-test-fixture sweep done-def (test step passes), but
they keep `unified-trading-library/scripts/quality-gates.sh` red on every push,
which masks new regressions and forces every UTL-touching agent to inspect
"is this failure pre-existing or mine?". Composite scope: not a 30-min fix.

## Recommended decision

Operator triage / break into themed sub-issues:

1. **Cloud SDK import** (`instrument_lifecycle_loader.py`): single-file fix; route
   through `unified_cloud_interface`. ~30-60 min — assign to next UTL slot.
2. **Backward-compat shims** (3 instances): targeted deletions; check callers
   first. ~1 hour.
3. **Function/method size** (22 violations): per-module refactors. ~1-2 AI-days
   total. Concentrated areas: `treasury/` (5), `post_trade/` (4),
   `streaming/live_aggregator.py` (3), `feature_service_base/live_aggregator.py`
   (3), `synthetic/harness.py` (2).
4. **urllib3 CVE bump**: workspace-wide dep bump to 2.7.0 — single PR across
   all repos via PM dep alignment scripts.
5. **Deep UAC imports** (10 callsites): pair with Ikenna for facade re-exports
   on `canonical.crosscutting.{service_emission_policy,honest_coverage,strategy_family,circuit_breaker,source_priority,kill_switch}`,
   then per-callsite migration.

This issue doc is the audit-trail record per slot-3-harsh done-def; it is **not**
a blocker for the 117-test-fixture sweep closure (utl@`26ded7d`).
