---
name: d4-mtds-adapters-preflight-2026-05-20
title: D4 — MTDS adapters preflight + batch-live parity
created: 2026-05-20
author: ikenna (slot-8)
status: active
priority: P0
deadline: 2026-05-23
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
parent_plan: master_to_live_defi_2026_05_23.md
source_audits:
  - plans/audit/is_mtds_contract_audit_2026_05_20.md # C0
  - plans/audit/mtds_features_contract_audit_2026_05_20.md # C4
  - plans/audit/mtds_strategy_contract_audit_2026_05_20.md # C5
  - plans/audit/results/batch_live_adapter_parity_2026_05_20_summary.md # A6
related_plans:
  - live_pipeline_mtds_mdps_features_2026_05_08.md
  - d3_manifest_v8_finish_2026_05_20.md
  - defi_catalogue_chain_primitives_2026_05_10.md
prerequisite_plans:
  - d3_manifest_v8_finish_2026_05_20.md # manifest v8 must be green before preflight reads it
---

# D4 — MTDS adapters preflight + batch-live parity

> **Ordering step 4** in the Phase-E execution chain. Requires D3 (manifest v8) green first.
>
> **REVIEW-BLOCKING status**: C4 audit found ZERO MTDS manifest preflight in ALL 9 features-service families.
> features-service reads MTDS GCS parquets directly without checking MTDS manifest `capture_status`. This means 236k
> `MISSING_EXPECTED` MTDS cells (A3) silently flow into feature computation as empty inputs — no alert, no
> DependencyError.

## What this covers

1. **MTDS manifest preflight in features-service**: every handler reads MTDS availability_index before compute
2. **MTDS manifest emission gaps**: MTDS has zero manifest emission on batch+live write paths (C5)
3. **perp_funding schema drift**: Int64 epoch-nanos vs Datetime in MTDS output — fix at root (C4)
4. **Batch-live parity gaps**: 13 BATCH_ONLY cells in MTDS need live equivalents (A6)

## P0 findings from audits

### From C4 (MTDS → features)

| Finding                                                                              | Severity | File                                                                                                                                     |
| ------------------------------------------------------------------------------------ | -------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Zero MTDS manifest preflight in ALL 9 features-service handler families              | P0-C4-1  | `onchain/`, `cefi/`, `commodity/`, `sports/`, `calendar/`, `delta_one/`, `volatility/`, `multi_timeframe/`, `cross_instrument/` handlers |
| Zero `DependencyError` raises — features proceeds silently when MTDS data missing    | P0-C4-2  | All families                                                                                                                             |
| `DependencyChecker` checks GCS prefix existence only, not MTDS `capture_status`      | P0-C4-3  | `onchain/app/core/dependency_checker.py`                                                                                                 |
| perp_funding MTDS output: timestamp stored as Int64 epoch-nanos (should be Datetime) | P0-C4-4  | MTDS perp_funding handler                                                                                                                |
| MTDS batch path: no `record_captured` / `record_empty` / `record_failed` calls       | P0-C5-1  | MTDS batch handlers (C5 finding)                                                                                                         |
| MTDS live path: no `record_captured` calls                                           | P0-C5-2  | MTDS live handlers (C5 finding)                                                                                                          |

### From A6 (batch-live parity)

| Cell (venue, data_type)         | Status     | Gap                    |
| ------------------------------- | ---------- | ---------------------- |
| aster (liquidations)            | BATCH_ONLY | Live equivalent needed |
| aster (trades)                  | BATCH_ONLY | Live equivalent needed |
| deribit (trades)                | BATCH_ONLY | Live equivalent needed |
| hyperliquid (book_snapshot_5)   | BATCH_ONLY | Live equivalent needed |
| hyperliquid (derivative_ticker) | BATCH_ONLY | Live equivalent needed |
| hyperliquid (liquidations)      | BATCH_ONLY | Live equivalent needed |
| hyperliquid (trades)            | BATCH_ONLY | Live equivalent needed |
| curve (dex_pools)               | BATCH_ONLY | Live equivalent needed |
| curve (dex_swaps)               | BATCH_ONLY | Live equivalent needed |
| jito (lst_rates)                | BATCH_ONLY | Live equivalent needed |
| morpho (lending_indices)        | BATCH_ONLY | Live equivalent needed |
| kalshi (trades)                 | BATCH_ONLY | Live equivalent needed |
| polymarket (trades)             | BATCH_ONLY | Live equivalent needed |

## Remediation backlog (ordered)

### Phase 1 — MTDS manifest emission (upstream prerequisite)

- [ ] [AGENT] P0. Add `record_captured` / `record_empty(reason=...)` / `record_failed` to MTDS batch handlers:
  - Every handler that writes a parquet to GCS MUST call `record_captured(...)` with cluster validation
  - Empty data from upstream API → `record_empty(reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)`
  - Exception during fetch → `record_failed(error_reason=...)`
  - Scan: `rg 'record_captured|record_empty|record_failed' market-tick-data-service/ --type py` to find current gaps
- [ ] [AGENT] P0. Add `record_captured` to MTDS live write paths — same contract; live mode rows must be
      manifest-visible
- [ ] [AGENT] P0. Fix perp_funding schema drift: MTDS perp_funding handler should write timestamp column as `Datetime`
      (not Int64 epoch-nanos); remove the runtime cast workaround in features-service once MTDS is fixed

### Phase 2 — features-service manifest preflight

- [ ] [AGENT] P0. Upgrade `DependencyChecker` (`onchain/app/core/dependency_checker.py`):
  - Change from GCS prefix existence check (`list_blobs`) to MTDS manifest `capture_status` read
  - Load MTDS `_index/availability_index.parquet` for the required (venue, data_type, date) shard
  - If `capture_status == "attempted_failed"` → raise `DependencyError(fail_fast=True)`
  - If `capture_status == "expected_unattempted"` → `record_empty(reason=EmptyConfirmedReason.EXPECTED_UPSTREAM_EMPTY)`
  - If `capture_status == "empty_confirmed"` → `record_empty(reason=EmptyConfirmedReason.EXPECTED_UPSTREAM_EMPTY)`
  - If manifest row missing entirely → raise `DependencyError(fail_fast=True)` (not silent skip)
  - Change all DEFI dependency declarations from `"required": False` to `"required": True`
- [ ] [AGENT] P0. Wire MTDS preflight into remaining 8 handler families that don't use DependencyChecker:
  - `commodity/cli/handlers/batch_handler.py` — EIA/FRED upstream (preflight their manifest if applicable)
  - `sports/cli/handlers/batch_handler.py` — MTDS not primary; verify IS dependency preflight
  - `calendar/cli/handlers/batch_handler.py` — verify external dependency check
  - `cefi/cli/handlers/perp_funding_handler.py` — reads MTDS perp-funding bucket directly; add manifest check
- [ ] [AGENT] P0. Fix EIA adapters warn-but-proceed (A5 finding):
  - `features_service/commodity/adapters/eia_ng.py:70` → replace `logger.warning("no data rows"); return {}` with
    `record_empty(reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO); raise DependencyError`
  - `features_service/commodity/adapters/eia_crude.py:61` → same fix

### Phase 3 — Batch-live parity (A6: 13 BATCH_ONLY cells)

- [ ] [AGENT] P0. For each BATCH_ONLY cell, implement live adapter OR document why live equivalent is blocked:
  - For cells with WebSocket upstream (aster, deribit, hyperliquid): implement live WebSocket handler using existing
    MTDS WebSocket infra pattern
  - For cells with polling-only upstream (curve dex_pools/dex_swaps, jito, morpho): implement polling live handler (same
    as batch but triggered by candle boundary crossing)
  - For prediction (kalshi, polymarket trades): implement live WebSocket handler or file `BLOCKED-CREDENTIALS` request
  - For each implemented live handler: match batch schema exactly (same columns, same data types, same manifest emission
    contract)
- [ ] [AGENT] P1. File `BLOCKED-CREDENTIALS` pings for any batch-live gap where live adapter needs credentials not yet
      provisioned

### Phase 4 — Quality gates + verification

- [ ] [AGENT] P1. Add `no_silent_absence_handlers.sh` QG step to features-service QG (STEP 5.70 equivalent): checks
      every handler for `record_captured` or `record_empty` calls
- [ ] [OPERATOR] P0. Run full features-service QG post-Phase-2: `cd features-service && bash scripts/quality-gates.sh`
- [ ] [OPERATOR] P0. Smoke test: run features-service onchain handler for one DeFi shard with MTDS mock returning
      `attempted_failed` → verify `DependencyError` is raised, not silent skip

## Success criteria

- [ ] Phase 1: MTDS QG green; every MTDS batch+live handler has `record_captured` / `record_empty` / `record_failed`
- [ ] Phase 2: `rg 'DependencyError' features-service/ --type py` returns hits in ALL 9 handler families
- [ ] Phase 3: A6 BATCH_ONLY cells: 0 unaddressed cells (either live handler shipped or BLOCKED-CREDENTIALS filed)
- [ ] Phase 4: features-service QG green; smoke test passes

## Full-execution criterion

> features-service onchain batch handler tested against a real MTDS manifest that has `attempted_failed` cells for one
> DeFi shard → DependencyError raised (not silent empty). MTDS batch handler verified to write `record_captured` rows to
> manifest (confirm via pyarrow read of `_index/availability_index.parquet` post-write). Batch-live parity: every
> BATCH_ONLY cell has either a live adapter committed or a BLOCKED-CREDENTIALS ping with operator ack.

## Temporary states + their canonical follow-up plans

- BATCH_ONLY cells pending live adapter implementation: status `BLOCKED-CREDENTIALS` for credential-gated venues; open
  todos in Phase 3 for others. Follow-up: each live adapter ships as its own PR.
- DependencyChecker upgrade may temporarily surface DependencyError noise for historically-empty shards: acceptable;
  resolve by classifying those as `EXPECTED_UPSTREAM_EMPTY` once expected_coverage() integration is wired (D2 plan
  successor).
