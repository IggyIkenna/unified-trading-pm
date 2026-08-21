---
doc_type: plan
title: mft-prod-safety-hardening
summary: Fix 13 production safety gaps identified in the 2026-03-11 full parallel audit (9 agents, 17 sections). Covers
  execution engine hardening, float→Decimal precision, network isolation, auth standardisation, and pytest-socket rollout
  across 45 repos.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-11'
type: code
epic: none
completion_gates: {code: C4, deployment: none, business: none}
repo_gates:
- {repo: execution-service, code: C4, deployment: none, business: none}
- {repo: unified-internal-contracts, code: C4, deployment: none, business: none}
- {repo: unified-trading-pm, code: C4, deployment: none, business: none}
- {repo: alerting-service, code: C4, deployment: none, business: none}
- {repo: market-data-api, code: C4, deployment: none, business: none}
- {repo: client-reporting-api, code: C4, deployment: none, business: none}
- {repo: ml-inference-api, code: C4, deployment: none, business: none}
- {repo: deployment-api, code: C4, deployment: none, business: none}
- {repo: risk-and-exposure-service, code: C4, deployment: none, business: none}
- {repo: ml-inference-service, code: C4, deployment: none, business: none}
depends_on: []
todos:
- {id: persist-blocked-spreads, content: Persist _BLOCKED_SPREADS set to GCS on every add via _persist_blocked_spreads() + load_blocked_spreads_from_storage() on startup. Prevents naked positions after pod restart. (execution-service/engine/concurrent.py), status: completed, note: Committed. Uses get_execution_bucket() from UTL + get_storage_client() from UCI. JSON blob at blocked_spreads/concurrent_blocked.json}
- {id: order-idempotency-cache, content: Add client_order_id dedup cache (300s TTL) in order adapter to prevent double-fills on network retry. (execution-service/adapters/order_adapter.py), status: completed, note: Committed. _ORDER_CACHE dict with _prune_order_cache(). Emits ORDER_IDEMPOTENCY_CACHE_HIT + ORDER_DUPLICATE_SUPPRESSED events.}
- {id: decimal-alpha-computation, content: 'Replace float arithmetic with Decimal in alpha_bps calculation in instruction_alpha_calculator.py:323. Silent 5-50 bps P&L divergence from float precision loss.', status: completed, note: Committed. alpha_bps now Decimal throughout. No float() wrapping in hot path.}
- {id: max-open-orders-cap, content: Add max_open_orders config key to PreTradeRiskEngine.check_order() to prevent runaway order spam from misconfigured TWAP/VWAP algorithms. Added OMS.count_open_orders() counting PENDING/VALIDATED/SUBMITTED/PARTIAL_FILLED., status: completed, note: Committed. _MAX_OPEN_ORDERS_EXCEEDED event logged. OMS.count_open_orders() added.}
- {id: price-sanity-checks, content: 'Add _validate_prices() to instruction_alpha_calculator.py: bid>ask check, spread >50% rejection, outlier bounds (0.1x–10x benchmark). Prevents corrupted feed data silently entering execution.', status: completed, note: Committed. Returns price_sanity_failed dict on violation. Logs PRICE_SANITY_CHECK_FAILED.}
- {id: sigterm-drain-ready-endpoint, content: Add SIGTERM handler with 30s drain timeout and /ready endpoint gated on ORDER_RECOVERY_COMPLETED to execution-service api/app.py. Prevents in-flight order loss on pod eviction., status: completed, note: Committed. asyncio.Event drained on SIGTERM. mark_recovery_complete() called from order recovery.}
- {id: block-network-base-scripts, content: Add --block-network to pytest invocations in base-service.sh and base-library.sh. Add check_emulator_reachability() warning function. Prevents live API calls in tests., status: completed, note: Committed to unified-trading-pm. base-service.sh and base-library.sh updated. Warning-only (never exits non-zero).}
- {id: float-to-decimal-schemas, content: 'Convert float fields to Decimal/int in PnLData (94 fields), OrderData, RiskMetrics, AlertMessage in unified-internal-contracts. Eliminates precision loss in P&L pipeline.', status: completed, note: 'Committed. 718 tests pass. pnl_bps → int, all equity/ratio/drawdown fields → Decimal.'}
- {id: risk-ml-integration-tests, content: 'Add integration tests for risk-and-exposure-service (28 tests: PreTradeRiskEngine, ExposureAggregator) and ml-inference-service (15 tests: prediction pipeline, boundary inputs, schema validation).', status: completed, note: Committed to both repos. All 43 tests pass.}
- {id: disable-auth-hard-fail, content: Standardise DISABLE_AUTH=true production guard to raise RuntimeError (hard-fail) across all 5 remaining API services. execution-results-api already had correct pattern., status: completed, note: 'Committed to alerting-service, market-data-api, client-reporting-api, ml-inference-api, deployment-api.'}
- {id: config-changed-logging, content: Add CONFIG_CHANGED event logging to alerting-service and market-data-api config mutation paths., status: completed, note: Committed to both repos.}
- {id: staleness-threshold-reduction, content: Reduce max_stale_position_seconds default from 5s to 0.5s. Add per-symbol override via max_stale_position_seconds_by_symbol config dict. 5s was too wide for MFT., status: completed, note: Committed to execution-service/engine/live/risk.py. Per-symbol dict lookup added.}
- {id: pytest-socket-rollout, content: 'Add pytest-socket>=0.7.0,<1.0.0 to dev dependencies in all Python repos that were missing it so --block-network flag added to base-service.sh actually works.', status: completed, note: Committed to 45 repos in one pass via Python script.}
isProject: false
---

# MFT Production Safety Hardening — 2026-03-11

**Context**: Full parallel audit (9 agents, 17 sections) identified 13 production safety gaps — items that pass all
quality gates but would cause incidents in live trading.

**Completed**: All 13 items committed across 10+ repos. Quality gates pass on all modified repos. Execution-service:
9487 tests, basedpyright 0 errors, 70% coverage.

**Archived**: 2026-03-11
