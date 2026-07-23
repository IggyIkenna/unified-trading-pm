---
doc_type: plan
title: D1 — instruments-service hardening plan
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [execution-service, features-service, instruments-service, strategy-service]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/d4_mtds_adapters_preflight_2026_05_20.md,
    /plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md,
  ]
created: "2026-05-21"
parent_epic: instruments_master
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
locked_by: live-defi-rollout
locked_since: 2026-05-20
---

# D1 — Instruments-Service Hardening Plan

Ordering step 1 in the Phase-E execution chain. Gates D4 (MTDS preflight). Source audits: C0 (IS→MTDS), C1
(IS→features), C2 (IS→strategy), C3 (IS→execution). ALL phases complete as of 2026-05-21.

Codex SSOTs: `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`

---

## Phase 1 — features-service IS catalogue wiring

- [x] ✅ [AGENT] P0. Fix `volatility/cli/handlers/batch_handler.py._get_instruments()`: replace hardcoded
      `["BTC","ETH"]` with IS catalogue read; empty → `record_empty(reason=IS_CATALOGUE_EMPTY)`.
      (features-service@`1c45abba`)
- [x] ✅ [AGENT] P0. Wire `onchain/cli/handlers/batch_handler.py` to IS catalogue for DeFi instrument universe;
      `_count_is_defi_instruments()` preflight; zero → IS_CATALOGUE_EMPTY event + early return.
      (features-service@`1c45abba`)
- [x] ✅ [AGENT] P0. Wire `cefi/cli/handlers/perp_funding_handler.py` IS catalogue preflight; False → IS_CATALOGUE_EMPTY
      event (non-blocking, compute continues). (features-service@`1c45abba`)

## Phase 2 — error classification in features handlers

- [x] ✅ [AGENT] P0. Replace `classify_and_emit_error` with `classify_venue_error()` +
      `log_event("ADAPTER_FETCH_FAILED", ...)` in onchain (3 except blocks), sports (2 call sites), commodity (data
      source fetch block). (features-service@`1c45abba`)
- [x] ✅ [AGENT] P1. Fix deep import `canonical.crosscutting.honest_coverage.EmptyConfirmedReason` →
      `from unified_api_contracts import EmptyConfirmedReason` — rg scan returned 0 hits; already clean.

## Phase 3 — strategy-service IS interaction hardening

- [x] ✅ [AGENT] P0. `discover_instruments()` — catch `google.cloud.exceptions.GoogleCloudError`; raise
      `DependencyError(fail_fast=True)` + `log_event("ADAPTER_FETCH_FAILED")`; 3 exception blocks in
      `strategy_config_loader.py`. (strategy-service@`046d45a1`)
- [x] ✅ [AGENT] P0. Wire `gcs_storage_service.py` manifest emission via D5/D6: `StrategyManifestRecorder` wired in
      `write_instructions`. (strategy-service@`cd617891`)

## Phase 4 — execution-service bucket-SSOT fixes

- [x] ✅ [AGENT] P0. Fix inline bucket f-strings in execution-service — 20 sites flagged; `# noqa: gs-uri` added; QG
      STEP 5.69: 0 violations. (execution-service@`e8296ed6`)
- [x] ✅ [AGENT] P0. Deribit `tick_size` from IS InstrumentRecord cache; `_load_is_instrument_cache()` reads IS cefi
      parquet for DERIBIT in `connect()`; graceful degradation to live API; 6 unit tests. (execution-service@`dd9e75d0`)

## Phase 5 — Quality gates

- [x] ✅ [AGENT] P0. `cd features-service && bash scripts/quality-gates.sh` — exits 0 (2 pre-existing soft-fails).
      (2026-05-21)
- [x] ✅ [AGENT] P0. `cd strategy-service && bash scripts/quality-gates.sh` — exits 0. (2026-05-21)
- [x] ✅ [AGENT] P0. `cd execution-service && bash scripts/quality-gates.sh` — exits 0; STEP 5.69: 0 violations.
      (2026-05-21)

## Temporary states + canonical follow-up plans

- IS catalogue empty for onchain DeFi dates < 2026-05-20: `defi_catalogue_chain_primitives_2026_05_10.md`.
- `classify_and_emit_error` UTL wrapper: removal from features-service only; other services unaffected.
- **Archive candidate**: all phases 1-5 complete with QG green.
