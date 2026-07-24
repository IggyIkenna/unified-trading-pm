---
doc_type: issue
title: Writegate slice (c) Phase 6.3-6.8 — BUILD emission infrastructure (not migrate) for 9 downstream services
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, features-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-13
author: ikenna-main-slot1
source:
  [
    plans/active/writegate_honest_coverage_endtoend_2026_05_06.md slice (c) Phase 6.3-6.8,
    features-volatility-service / features-cross-instrument-service / ml-training-service / ml-inference-service /
    strategy-service / execution-service / position-balance-monitor-service / risk-and-exposure-service /
    instruments-service,
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-13
---

# Writegate slice (c) Phase 6.3-6.8 — BUILD not migrate

> **Severity**: P0 — cutover-readiness blocker for Group D #12 (deployment-UI rollup matches on-disk truth-set) +
> downstream monitoring + batch-vs-live recon. **Suggested owner**: fan-out across slots 4 / 5 / 6 / 7 / 8 (1-2 services
> each). **Slot 3 ✅ acked** by surfacing the build-vs-migrate question (PM@`f0208d34`).

## What slot 3 found

Writegate slice (c) Phase 6.3-6.8 plan body was framed as "migration" of `record_*` callsites. Reality: these 9 services
have **ZERO `record_captured` / `record_empty` / `record_failed` callsites today** — they're
emission-infrastructure-greenfield.

The 8 services (corrected 2026-05-13 — `features-service` is ONE consolidated repo per
`features_repo_consolidation_2026_05_08.md` Phase 7 landed 2026-05-08; 8 family modules inside it):

1. **`features-service`** (consolidated; 8 family modules:
   `calendar / commodity / cross_instrument / delta_one / multi_timeframe / onchain / sports / volatility`) — each
   family has its own output `data_type` but shares the emission integration surface in `features_service/common/`.
2. `ml-training-service`
3. `ml-inference-service`
4. `strategy-service`
5. `execution-service`
6. `position-balance-monitor-service`
7. `risk-and-exposure-service`
8. `instruments-service` (catalog-refresh emission, separate from data adapters)

## Operator decision 2026-05-13: option (α) — BUILD emission infrastructure

**Operator clarification**: _"its expected there is no backfill yet those services are too downstream to have run
properly. whats manifest emission though i mean they need to be ready for production manifest wise"_

→ These services need production-ready manifest emission infrastructure even though they don't have historical backfill
yet. When they run in production starting 2026-05-23, every emission must be honest per the manifest 4-state taxonomy
(`captured` / `empty_confirmed` / `attempted_failed` / `expected_unattempted`).

## Per-service emission shape (output-type, not raw market data)

| Service                         | Output `data_type`                          | Shard key                                                  | Typical emission state                                                                                                                                                                                   |
| ------------------------------- | ------------------------------------------- | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **features-volatility**         | `volatility_features`                       | `(asset_group, instrument, day, timeframe)`                | `captured` per-bar feature batch; `empty_confirmed(reason=UPSTREAM_PRICE_BARS_MISSING)` when upstream gap; `attempted_failed` on schema-drift; `expected_unattempted` for pre-listing days.              |
| **features-cross-instrument**   | `cross_instrument_features`                 | `(asset_group, instrument-pair, day, timeframe)`           | Same 4-state. Cross-pair-specific empty reasons.                                                                                                                                                         |
| **ml-training**                 | `model_artefact`                            | `(family, variant, training_period_yyyymm, job_id)`        | `captured` on successful training; `attempted_failed(error=INSUFFICIENT_TRAINING_DATA / FEATURE_GAPS / TRAINING_NUMERICAL_FAILURE)`; `expected_unattempted(reason=EXPECTED_FAMILY_NOT_LIVE_FOR_PERIOD)`. |
| **ml-inference**                | `prediction`                                | `(model_id, instrument, timestamp_window, asset_group)`    | `captured` per prediction emit; `empty_confirmed(reason=NO_FEATURES_AT_TIMESTAMP / MODEL_NOT_LOADED)`; `attempted_failed` on inference exception.                                                        |
| **strategy**                    | `strategy_signal`                           | `(strategy_id, instrument, timestamp_window, asset_group)` | `captured` per signal emit; `empty_confirmed(reason=NO_EDGE_THIS_BAR / RISK_GATE_BLOCKED)`; `attempted_failed` on signal-generation exception.                                                           |
| **execution**                   | `execution_fill` + `order_state_transition` | `(venue, instrument, timestamp, order_id)`                 | `captured` per fill/state-transition; `attempted_failed(error=VENUE_REJECTED / TIMEOUT / INSUFFICIENT_BALANCE)`; `empty_confirmed` not typical (no orders → no rows).                                    |
| **position-balance**            | `position_snapshot`                         | `(account, instrument, timestamp, asset_group)`            | `captured` per snapshot cadence; `empty_confirmed(reason=ACCOUNT_INACTIVE)`.                                                                                                                             |
| **risk**                        | `risk_eval`                                 | `(strategy, axis, timestamp_window, asset_group)`          | `captured` per eval; `empty_confirmed(reason=NO_POSITIONS_TO_EVALUATE)`; `attempted_failed` on eval exception.                                                                                           |
| **instruments-service catalog** | `catalog_refresh`                           | `(source, asset_group, day)`                               | `captured` on successful refresh; `empty_confirmed(reason=EXPECTED_HOLIDAY / EXPECTED_WEEKEND)`; `attempted_failed(error=SOURCE_API_DOWN)`.                                                              |

## Implementation pattern (per service)

For each of the 9 services, ship:

1. **UAC `SERVICE_OUTPUT_POLICIES` entry** — register the service's output `data_type`s + emission policy per
   `unified_api_contracts/canonical/crosscutting/service_emission_policy.py`. Each policy declares the canonical shard
   key + expected emission cadence + when each state applies.

2. **`record_*` callsites** — at every output-write boundary. Pattern matches writegate slice (b) MDPS POC at
   MDPS@`d0df50c` + `311614a`:
   - On successful output:
     `manifest_writer.record_captured(data_type=..., row_key={...}, schema=..., pipeline_mode=..., service_emission_state=..., available_at=...)`
   - On honest absence: `record_empty(reason=<from EMPTY_CONFIRMED_REASONS closed-set>)`
   - On upstream-pipeline gap: `record_failed(error=DependencyError(fail_fast=True))`
   - On expected-unattempted (pre-launch / pre-coverage): `record_expected_unattempted(reason=...)`

3. **`publish_with_manifest_lookup()` integration** — through `emission_publisher.publish_with_policy` per writegate
   Phase 2.B (UTL `0adea1c6`). Service emits to event stream + manifest in one logical unit.

4. **Per-output-type schema declaration** — UAC schema for each `data_type` (strategy_signal / prediction /
   position_snapshot / risk_eval / etc). Existing schemas may exist in `unified_api_contracts.internal.domain.*`;
   verify + extend.

5. **Unit + integration tests** — minimum: each `record_*` call-path tested + emission state transitions tested.

6. **Plan-flip** — flip the relevant Phase 6.X sub-checkbox in `writegate_honest_coverage_endtoend_2026_05_06.md` + add
   evidence commit SHA.

## Routing — 8 services × slot mapping (corrected for consolidated features-service)

| Slot           | Service(s)                                                                                                                                                                     | Rationale                                                                                                                                                                                                   |
| -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **3** (Ikenna) | `instruments-service` catalog-refresh emission                                                                                                                                 | Already deep in instruments-service post-PipelineMode sweep                                                                                                                                                 |
| **4** (Ikenna) | `execution-service` + `position-balance-monitor-service`                                                                                                                       | Wallet/custody-adjacent; pairs with slot 4 api_keys_wallets context                                                                                                                                         |
| **5** (Ikenna) | `strategy-service`                                                                                                                                                             | Carry engine emits signals via this service; slot 5 CarryFamilyEngine context                                                                                                                               |
| **6** (Ikenna) | **`features-service` (ONE consolidated repo, ALL 8 family modules)** — `calendar / commodity / cross_instrument / delta_one / multi_timeframe / onchain / sports / volatility` | ONE repo integration; per-family `data_type` declarations; storage layer split by family × asset_group × env per bucket-name SSOT (b+) — e.g. `features-volatility-defi-${env}-${pid}`                      |
| **7** (Ikenna) | `risk-and-exposure-service` + `ml-inference-service`                                                                                                                           | Risk + DR scenarios alignment; ml-inference is downstream of features/strategy                                                                                                                              |
| **8** (Ikenna) | `ml-training-service`                                                                                                                                                          | Slot 8 owns cross_asset_audit + manifest Phase 3 consumer sweep; ml-training is the heaviest single-service emission scope (model artefact lifecycle + training_period rollover + per-family training runs) |

**features-service emission shape (slot 6 single-repo scope)**:

- ONE integration in `features_service/common/` (shared emission helper across families).
- 8 family modules each declare per-`data_type` (volatility_features / cross_instrument_features / delta_one_features /
  onchain_features / sports_features / multi_timeframe_features / commodity_features / calendar_features).
- Storage layer respects **family × asset_group × env split** per bucket-name SSOT (b+):
  - `resolve_bucket_name(cloud=, kind=features-{family}, asset_group=, env=)` → e.g.
    `features-volatility-defi-${env}-${pid}`, `features-cross-instrument-cefi-${env}-${pid}` etc.
- ONE `SERVICE_OUTPUT_POLICIES` entry per (family, asset_group) combo OR one entry per family with asset_group as policy
  axis.
- Per-family integration tests + shared smoke for the common emission path.

Each slot: 1-2 services (slot 6 = 1 repo / 8 families) × ~3-6 hours each = ~6-12 hours = ~1.5-3 calendar days at
single-AI pace = **~30-90 min at 5× pace with sub-agent fan-out** (slot 6 fans out 8 sub-agents per family; slot 4/7
fans out 2 sub-agents per service).

## Critical-path coverage for 2026-05-23 cutover

**MUST-SHIP this cycle** (2026-05-15 freeze gate) — full 9-service emission infra:

- Without manifest emission from strategy / execution / risk / position-balance, the live cutover monitoring is blind.
- Group D #12 (deployment-UI rollup matches on-disk truth-set) requires producer-side emission for the rollup to mean
  anything.
- Group F #21 (Reconciliation suite: batch-vs-live + P&L attribution + execution-alpha measurement) needs both batch and
  live emission paths.

**No deferrals**. Fans into existing slot scopes (each slot picks up 1-2 services as listed above).

## Composes with

- `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` slice (c) Phase 6.3-6.8 — primary plan body; flip
  checkboxes per service as shipped
- `plans/active/manifest_schema_final_gate_2026_05_09.md` Phase 3 — consumer sweep covers reader-side; this issue doc
  covers producer-side
- `plans/active/issues/strategy_archetype_taxonomy_refinement_2026_05_12.md` — strategy-service emission overlaps with
  carry-engine refactor (slot 5)
- `/codex/02-data/service-output-emission-semantics.md` — canonical pattern doc (writegate slice (b) MDPS POC reference)
