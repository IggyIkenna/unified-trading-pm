---
doc_type: plan
title: position-precision-pnl-hardening-2026-03-11
summary: Fix inverse perp is_inverse hardcode, add margin_type to instruments, and add fee/funding/yield reconciliation
  engines to eliminate unexplained P&L and achieve attribution correctness.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [batch-live-reconciliation-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-11'
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-internal-contracts, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-reference-data-interface, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: execution-service, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: position-balance-monitor-service, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: risk-and-exposure-service, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: strategy-service, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: trading-analytics-api, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: batch-live-reconciliation-service, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: onboarding-ui, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: settlement-ui, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
- {repo: unified-events-interface, code: C1, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
depends_on: [uei_pending_event_additions, recon_rebalancing_order_recovery_2026_03_10]
todos:
- {id: phase-a-uic-margin-type, content: 'UIC v0.1.82: Add MarginType enum, fee_schedule.py; export all new types', status: done, note: DONE 2026-03-11}
- {id: phase-a-urdi-adapters, content: 'URDI Bybit/OKX/Deribit adapters: populate margin_type', status: done, note: DONE 2026-03-11}
- {id: phase-a-exec-is-inverse, content: 'execution-service: Fix is_inverse=False hardcode at factory_cefi_defi.py:468; add notional_calculator.py', status: done, note: DONE 2026-03-11}
- {id: phase-b-fee-recon, content: 'URDI, trading-analytics-api, position-balance-monitor, execution-service: Add fee reconciliation infrastructure', status: done, note: DONE 2026-03-11}
- {id: phase-c-funding-recon, content: 'execution-service, strategy-service, batch-live-reconciliation-service: Add funding reconciliation', status: done, note: DONE 2026-03-11}
- {id: phase-d-yield-recon, content: 'execution-service, trading-analytics-api, settlement-ui: Add yield reconciliation and settlements backend', status: done, note: DONE 2026-03-11}
- {id: phase-e-pnl-loop-closure, content: 'strategy-service, risk-and-exposure-service: Close P&L attribution loop', status: done, note: DONE 2026-03-11 (except UEI UNEXPLAINED_PNL_RESIDUAL event)}
- {id: phase-e-uei-event, content: 'UEI: Emit UNEXPLAINED_PNL_RESIDUAL event hourly + AlertEvent when > 2% of total PnL', status: done, note: DONE 2026-03-11 — PnLResidualEmitter in strategy_service/engine/core/components/pnl_residual_emitter.py}
isProject: false
---

# Plan: Position Precision & P&L Attribution Hardening

**Created:** 2026-03-11 **Status:** DONE **Priority:** P0 — Correctness + Attribution Quality

---

## Context

Our internal view of positions diverges from the exchange across multiple dimensions — fees charged vs expected, funding
payments calculated vs actually credited, interest/yield accrued vs actually received. Each unexplained gap inflates
`PnLAttribution.unexplained_pnl` and makes P&L attribution unreliable.

There is also a correctness bug: `factory_cefi_defi.py:468` hardcodes `is_inverse=False` for all instruments, meaning
inverse (coin-margined) perps (e.g. Bybit BTCUSD) have wrong delta/notional everywhere downstream — risk, position
sizing, P&L.

The insight is additive: every dimension we reconcile correctly is one less source of phantom discrepancy. Eventually
`unexplained_pnl` only contains genuine unknowns.

---

## Streams & Priority

```
P1: Stream 1 — margin_type hardening         (correctness gate)
P2: Stream 2 — fee reconciliation + PB model (every fill; 50-200 bps cumulative impact)
P3: Stream 3 — funding reconciliation         (every 8h; 10-50 bps/day)
P4: Stream 4 — interest/staking/EigenLayer    (lower frequency, high per-event value)
P5: Stream 5 — settlement backend + UI        (closes the attribution loop visually)
```

---

## Progress Checklist

### Phase A — Foundation (Stream 1 + alert fix)

- [x] **UIC v0.1.82**: Add `MarginType` enum + `margin_type: MarginType | None` to `InstrumentRecord`
- [x] **UIC v0.1.82**: Add `fee_schedule.py` with `FeeType`, `FeeScheduleEntry`, `ClientFeeSchedule`,
      `PrimeBrokerEntity`, `ClientPrimeBrokerLink`
- [x] **UIC v0.1.82**: Export all new types from `reference/__init__.py` and top-level `__init__.py`
- [x] **URDI Bybit adapter**: Populate `margin_type` in `_parse_category_symbol()`; add `"inverse"` category to fetch
      loop
- [x] **URDI OKX adapter**: Map `ctType` to `MarginType`; use `settleCcy == baseCcy` as fallback
- [x] **URDI Deribit adapter**: Map `settlement_currency == baseCurrency` → `MarginType.INVERSE`
- [x] **execution-service**: Fix `is_inverse=False` hardcode at `factory_cefi_defi.py:468`
- [x] **execution-service**: Add `notional_calculator.py` with `calculate_notional_usd()`
- [x] **execution-service**: Add startup `log_event("missing_margin_type")` WARNING for unclassified perps
- [x] **position-balance-monitor**: Fix `ReconciliationEngine._send_alert()` to publish real `AlertEvent` via pubsub

### Phase B — Fee Reconciliation + Fee Schedule Infrastructure

- [x] **URDI**: Add `get_exchange_fee_schedule(venue, client_id)` to `BaseReferenceDataAdapter`; implement in Bybit and
      OKX
- [x] **trading-analytics-api**: Add `fee_schedule_store.py` (GCS-backed, PB entity + client link resolution)
- [x] **trading-analytics-api**: Add `routes/prime_brokers.py` (CRUD for `PrimeBrokerEntity`)
- [x] **trading-analytics-api**: Add `routes/client_fees.py` (`GET/PUT /clients/{id}/fee-schedule`, effective schedule
      merge)
- [x] **position-balance-monitor**: Add `FeeLayerSnapshot`, `FeeReconciliationSnapshot`, `CumulativeFeeDiscrepancy` to
      `models.py`
- [x] **position-balance-monitor**: Add `FeeReconciliationEngine` (`core/fee_reconciliation_engine.py`)
- [x] **execution-service**: Add `AccountHistoryClient` (`services/account_history_client.py`) with `get_fill_fees()` +
      `get_funding_payments()`
- [x] **onboarding-ui**: Add "Fee Structure" wizard step to `ClientOnboarding.tsx` (PB selection + per-layer overrides)
- [x] **onboarding-ui**: Add "Fee Schedule" tab to `ClientDetail.tsx` (view/edit post-onboarding)

### Phase C — Funding Reconciliation

- [x] **execution-service**: Add `FundingReconEngine` + `ExchangeFundingPayment` + `FundingReconciliationRecord`
      (`services/funding_recon_engine.py`)
- [x] **strategy-service**: Add `exchange_reported_amount`, `reconciliation_status`, `discrepancy_bps` to
      `SettlementDelta`
- [x] **batch-live-reconciliation-service**: Add `ReconStage.FEE_RECON` and `ReconStage.FUNDING_RECON` enum entries

### Phase D — Yield Reconciliation + Settlement Backend

- [x] **execution-service**: Add `YieldReconEngine` with `AaveIndexReconciliation`, `LSTYieldReconciliation`,
      `EigenLayerRewardReconciliation` (`services/yield_recon_engine.py`)
- [x] **trading-analytics-api**: Add `routes/settlements.py` (submit/confirm/pending/residuals endpoints)
- [x] **trading-analytics-api**: Add `settlements_store.py` (GCS-backed NDJSON)
- [x] **trading-analytics-api**: Wire existing empty stubs in `routes/recon.py` to GCS reads
- [x] **settlement-ui**: Add `Settlements.tsx` page (pending table + confirm form + residual donut)

### Phase E — P&L Attribution Loop Closure

> ⚠️ **H2 SEQUENCING NOTE (2026-03-11):** Phase E's `UNEXPLAINED_PNL_RESIDUAL` UEI event is tracked in
> `uei_pending_event_additions.md`. Coordinate with recon_rebalancing and data_availability UEI batches to avoid
> schemas.py conflicts. Also: `batch-live-reconciliation-service` changes in Phase C (`ReconStage` enum additions) must
> be committed before `recon_rebalancing_order_recovery_2026_03_10` begins its own `ReconStage` additions — check
> current enum state before Phase C additions to avoid duplication. Phase C items confirmed DONE 2026-03-11.

- [x] **strategy-service**: Add `fee_recon_confirmed`, `funding_recon_confirmed`, `staking_recon_confirmed`,
      `eigenlayer_recon_confirmed` to `PnLAttribution`
- [x] **strategy-service**: Add `unexplained_pnl_post_recon` property to `PnLAttribution`
- [x] **risk-and-exposure-service**: Use correct inverse notional in `pre_trade_check_engine.py`
- [ ] **UEI**: Emit `UNEXPLAINED_PNL_RESIDUAL` event hourly + `AlertEvent` when `> 2%` of total PnL

---

## Alert Threshold Reference

| Dimension                               | Warning   | Critical   | `rule_id`                           |
| --------------------------------------- | --------- | ---------- | ----------------------------------- |
| Position qty (existing — alerts broken) | 1% or $1k | 5% or $10k | `position_qty_discrepancy`          |
| Exchange fee discrepancy (per-fill)     | 5 bps     | 20 bps     | `exchange_fee_discrepancy_per_fill` |
| Prime broker fee discrepancy (per-fill) | 2 bps     | 10 bps     | `pb_fee_discrepancy_per_fill`       |
| Clearing fee discrepancy (per-fill)     | 1 bps     | 5 bps      | `clearing_fee_discrepancy_per_fill` |
| Cumulative fee total (24h, all layers)  | 50 bps    | 200 bps    | `fee_discrepancy_cumulative`        |
| Funding payment                         | 10 bps    | 50 bps     | `funding_discrepancy`               |
| Funding rate divergence                 | —         | 5 bps      | `funding_rate_divergence`           |
| AAVE index accrual                      | 0.1%      | 1.0%       | `aave_index_discrepancy`            |
| LST yield                               | 5%        | 20%        | `lst_yield_discrepancy`             |
| EigenLayer rewards                      | 5%        | 50%        | `eigenlayer_discrepancy`            |
| Unexplained P&L residual                | 2%        | 5%         | `unexplained_pnl_residual`          |
| Missing margin_type on perp at startup  | WARNING   | —          | `missing_margin_type`               |

---

## Repo Version Cascade Order

```
unified-internal-contracts v0.1.86
  → unified-reference-data-interface
  → execution-service
  → position-balance-monitor-service
  → risk-and-exposure-service
  → pnl-attribution-service
  → strategy-service
  → trading-analytics-api
  → batch-live-reconciliation-service
```

---

## Critical Files

| File                                                                     | Change                                                                                                      |
| ------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| `unified-internal-contracts/.../reference/instrument.py`                 | `MarginType` enum + `margin_type` field on `InstrumentRecord` ✅                                            |
| `unified-internal-contracts/.../reference/fee_schedule.py`               | **NEW** `FeeType`, `FeeScheduleEntry`, `ClientFeeSchedule`, `PrimeBrokerEntity`, `ClientPrimeBrokerLink` ✅ |
| `unified-reference-data-interface/.../adapters/bybit.py`                 | Populate `margin_type`; add `inverse` category fetch                                                        |
| `unified-reference-data-interface/.../adapters/okx.py`                   | Map `ctType` → `MarginType`                                                                                 |
| `unified-reference-data-interface/.../adapters/deribit.py`               | Map `settlement_currency` → `MarginType`                                                                    |
| `execution-service/.../instruments/factory_cefi_defi.py:468`             | Replace `is_inverse=False` hardcode                                                                         |
| `execution-service/.../instruments/notional_calculator.py`               | **NEW** linear vs inverse notional formula                                                                  |
| `execution-service/.../services/account_history_client.py`               | **NEW** exchange account history (fills, funding)                                                           |
| `execution-service/.../services/funding_recon_engine.py`                 | **NEW** funding recon records + engine                                                                      |
| `execution-service/.../services/yield_recon_engine.py`                   | **NEW** AAVE/LST/EigenLayer recon                                                                           |
| `position-balance-monitor-service/.../models.py`                         | Add `FeeLayerSnapshot`, `FeeReconciliationSnapshot`, `CumulativeFeeDiscrepancy`                             |
| `position-balance-monitor-service/.../core/fee_reconciliation_engine.py` | **NEW** fee recon engine                                                                                    |
| `position-balance-monitor-service/.../core/reconciliation_engine.py`     | Fix `_send_alert()` → real `AlertEvent`                                                                     |
| `strategy-service/.../models/pnl.py`                                     | `SettlementDelta` recon fields + `unexplained_pnl_post_recon`                                               |
| `trading-analytics-api/.../fee_schedule_store.py`                        | **NEW** GCS-backed fee schedule store with PB resolution                                                    |
| `trading-analytics-api/.../routes/prime_brokers.py`                      | **NEW** PB entity CRUD                                                                                      |
| `trading-analytics-api/.../routes/client_fees.py`                        | **NEW** effective client fee schedule                                                                       |
| `trading-analytics-api/.../routes/settlements.py`                        | **NEW** settlement submit/confirm/residuals                                                                 |
| `onboarding-ui/src/pages/ClientOnboarding.tsx`                           | Add "Fee Structure" wizard step                                                                             |
| `onboarding-ui/src/pages/ClientDetail.tsx`                               | Add "Fee Schedule" tab                                                                                      |
| `settlement-ui/src/pages/Settlements.tsx`                                | **NEW** settlement confirmation UI                                                                          |
| `risk-and-exposure-service/.../core/pre_trade_check_engine.py`           | Correct inverse notional                                                                                    |

---

## Verification

1. **Inverse notional**: Create Bybit BTCUSD inverse instrument; assert `is_inverse == True`; assert
   `calculate_notional_usd(qty=100, price=100000) == Decimal("100")` (not `10_000_000`)
2. **PB fee inheritance**: Create `PrimeBrokerEntity("hidden_road", pb_fee_bps=1.0)`; link client with no overrides →
   effective PB bps = 1.0; add override 0.8 → effective = 0.8;
   `total_taker_bps(exchange=4, PB=0.8, clearing=0.5) == Decimal("5.3")`
3. **Fee recon alert**: Fill with expected=6 bps, exchange actual=8 bps (25 bps discrepancy) → CRITICAL `AlertEvent`
   with `rule_id="exchange_fee_discrepancy_per_fill"`; PB layer status = MATCH
4. **Funding recon**: Internal payment=$50, exchange reported=$52 → `discrepancy_bps > 10` → WARNING AlertEvent
5. **Unexplained shrinks**: `unexplained_pnl=$100` on $1000 total; confirm $80 funding+fee →
   `unexplained_pnl_post_recon <= $20`, `is_reconciled == True`
6. **Settlement UI**: POST submit + confirm → `GET /settlements/residuals` shows reduced unexplained
