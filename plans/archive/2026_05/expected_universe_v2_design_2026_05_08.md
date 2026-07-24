---
doc_type: plan
title: Expected-universe v2 design — per-asset-group dynamic denominators
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-api, deployment-service, instruments-service]
scope: [engineer, admin]
tags: []
related:
  [/plans/archive/2026_07/master_to_live_defi_2026_05_23.md, /plans/archive/2026_05/d1_is_hardening_2026_05_20.md]
created: "2026-05-21"
parent_epic: instruments_master
priority: P1
estimate_class: design
estimate_baseline_ai_days: 5.0
estimate_calibrated_ai_days: 3.0
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Expected-Universe v2 Design

Per-asset-group dynamic denominators for data-status: instruments-service catalogue drives the expected-universe count
(not hardcoded constants). Phases 1-3 (code) complete; Phase 4 (Polymarket calendar integration) deferred; Phase 5
(codex) complete.

Codex SSOTs: `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md` ·
`/codex/02-data/availability-manifest-and-data-status.md`

---

## Phase 1 — UAC `ExpectedUniverseSpec` schema

- [x] ✅ [SCRIPT] P0. UAC `ExpectedUniverseSpec` + `get_expected_universe(asset_group, data_type, date)` — reads IS
      catalogue parquet; falls back to UAC static constants if IS unavailable. (instruments-service@`5c5b1f8`)

## Phase 2 — deployment-api data-status wiring

- [x] ✅ [SCRIPT] P0. `deployment-api/data_status_service.py` denominators switched from hardcoded constants to
      `get_expected_universe()` calls; per-asset-group dynamic counts. (deployment-service@`7313a39`)

## Phase 3 — IS catalogue export

- [x] ✅ [SCRIPT] P0. instruments-service exports per-asset-group instrument count to GCS
      `_index/expected_universe_<ag>_<date>.parquet`; daily refresh schedule. (instruments-service@`c670a72`,
      deployment-service@`31fe24f`)

## Phase 4 — Polymarket calendar integration (deferred)

- [x] ✅ [TRACKED] P1. Polymarket expected-universe calendar integration — DEFERRED to `predictions_master` Phase 3
      (calendar-aware denominators for prediction markets). **BLOCKED-ON G4**: predictions_master Phase 3.

## Phase 5 — Codex SSOT

- [x] ✅ [AGENT] P1. `/codex/02-data/availability-manifest-and-data-status.md` § "Expected universe" updated; IS
      catalogue path documented.

## Temporary states + canonical follow-up plans

- Phase 4 Polymarket calendar: `predictions_master` Phase 3.
- IS catalogue empty for onchain DeFi dates < 2026-05-20: `defi_catalogue_chain_primitives_2026_05_10.md`.
