---
doc_type: issue
title: "DP-FETCH-009 CeFi liquidations: feature contract overwrites raw liquidation contract"
summary: >-
  A fresh CeFi liquidations batch is failing schema validation because UAC registers the raw
  (cefi, perpetual, liquidations) tick contract and then overwrites that same registry key with
  the feature-group contract of the same name. The runtime therefore validates Tardis raw rows
  against feature columns instead of instrument_id/symbol/ts_event/price/size/side.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [data-pipeline, dp-fetch-009, dp-run-mostly-empty, schema-contract, registry-collision, cefi]
related: [/plans/active/cefi_consolidated_closeout_2026_07_18.md, /codex/02-data/availability-manifest-and-data-status.md, /codex/05-infrastructure/data-pipeline-alerts.md, /plans/active/issues/dp_fetch_009_cefi_liquidations_batch_aster_2026_08_20.md]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: observability_master
assigned_vm: vm-cross-cutting
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: data_pipeline_failure
drift_direction: regress
depends_on: []
resolved_by:
locked_by: live-defi-rollout
locked_since: 2026-08-20
supersedes:
superseded_by:
source: "Escalation agt-9d9a98; DP_RUN_MOSTLY_EMPTY / DP-FETCH-009"
context_scope: [unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py, unified-api-contracts/unified_api_contracts/internal/schemas/_feature_contracts.py, market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py, /codex/02-data/availability-manifest-and-data-status.md]
---

## Finding

The alert reported `asset_group=cefi`, `data_type=liquidations`, with 160,105
`attempted_failed` cells out of 1,852,684 attempted (8.6%). A bounded row-group
read of the live CeFi availability index measured 2,442 failures in the last day
as of 2026-08-20: 1,632 schema-contract violations and 810 Tardis HTTP 403
`code=274 concurrent-IP-lock` failures. The schema failures were on
BINANCE-FUTURES (720), BYBIT (509), BITGET-FUTURES (395), and BITFINEX-FUTURES
(8), all in `batch_tardis` mode.

The installed UAC runtime resolves
`lookup_contract("cefi", "perpetual", "liquidations", venue="BINANCE-FUTURES")`
to feature columns `instrument_id, venue, ts_event, ts_event_out, feature_group,
timeframe`. UAC's raw contract declaration correctly expects
`instrument_id, symbol, ts_event, price, size, side`, but `_feature_contracts.py`
uses the same three-tuple registry key for its feature group named `liquidations`
and overwrites the raw entry during import.

The Tardis adapter correctly treats validation failures as `record_failed`; no
placeholder or empty capture was written. The independent code-274 population is
an existing concurrency-lock condition and is not conflated with this registry
collision.

## Required resolution

- [x] [UAC] P1. ✅ Prevented feature-group registration from overwriting a raw tick
  contract when both use the same `(asset_group, instrument_type, data_type)` tuple; preserved the existing raw contract and added a CeFi liquidations regression test. Evidence: `unified-api-contracts@cff7a237` pushed to `origin/live-defi-rollout`; focused regression `1 passed`.
- [ ] [MTDS] P1. Re-run the Tardis CeFi liquidations path against the corrected
  UAC contract, verify fresh failures stop decreasing capture availability, and
  record the post-fix manifest evidence.
- [ ] [DATA] P1. Separately continue the existing Tardis code-274 lockout
  remediation; do not mark those failures as resolved by the registry fix.

## Evidence

- `unified-api-contracts/unified_api_contracts/internal/schemas/contracts.py:302-309`
  declares the raw CeFi liquidation contract.
- `unified-api-contracts/unified_api_contracts/internal/schemas/_feature_contracts.py:158-174`
  registers feature groups into the same key space; `liquidations` is in the
  delta-one feature-group list.
- `market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py:863-880`
  calls `lookup_contract` and records the schema violation as a failed capture.



## Post-fix audit

A bounded read-only availability-index audit on 2026-08-20 after the UAC commit still measured 4,535 fresh `cefi/liquidations` `attempted_failed` rows, latest `attempted_at` 07:36:57 UTC: 1,998 schema-contract violations and 2,537 Tardis code-274 concurrent-IP-lock failures. The UAC fix is therefore shipped but not yet reflected in the production MTDS writer; keep the MTDS replay/deploy todo open.

## Progress Log

- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries).
