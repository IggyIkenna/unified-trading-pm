---
doc_type: plan
title: CME x Polymarket cross-venue event-arb
summary:
status: complete
nature: record
asset_group: [tradfi]
stage: [meta]
repos: [instruments-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/trading_agent_service_architecture_unlock_2026_05_22.md,
    /plans/archive/2026_05/tradfi_ohlcv_only_mvp_backfill_2026_05_15.md,
    /plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
  ]
created: "2026-05-08"
parent_epic: tradfi_master
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 15.0
estimate_calibrated_ai_days: 15.0
---

# CME x Polymarket Cross-Venue Event-Arb Plan

> **Cross-link 2026-05-20**: Emits StrategyPnlStreamEvent per UAC contract (see
> trading_agent_service_architecture_unlock plan Phase 1+2). Status: TODO post-cutover unless explicitly listed in this
> plan's May-23 scope.

Cross-venue arbitrage between CME event-contracts (9 roots: ECES/ECBTC/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECNQ) and
Polymarket binary outcomes. Both resolve YES/NO at a strike threshold — same economics, different venues, different
schemas. Source RFC archived at `plans/archive/issues/cme_event_contracts_cross_venue_arb_shard_design_2026_05_08.md`.
Post-May-23 critical path; not a deadline blocker. Operator note 2026-05-15: OHLCV-1m sufficient for arb backtest (no
tick-data dependency).

Codex SSOTs: `/codex/02-data/per-asset-group-bucket-layouts.md` ·
`/codex/09-strategy/architecture-v2/category-instrument-coverage.md` ·
`/codex/16-strategy-playbooks/strategy/cme-polymarket-arb.md`

---

## Phase 1 — `InstrumentType.EVENT_CONTRACT` enum

- [x] [SCRIPT] P1. UAC `InstrumentType.EVENT_CONTRACT` + Databento BAG classifier; `INSTRUMENT_TYPES_BY_VENUE[CME]`
      gains EVENT_CONTRACT; `INSTRUMENT_TYPE_FOLDER_MAP` seeded with `event_contracts`; 4 integration tests.
      (unified-api-contracts@`b95d146`)

## Phase 2 — `linked_canonical_question_group` cross-link

- [x] ✅ [SCRIPT] P1. NEW UAC SSOT `unified_api_contracts/canonical/crosscutting/cme_polymarket_link.py` — per-CME-root
      canonical_question_group map. **FULL** — all 9 CME roots wired. UAC@77facd65 (ECES+ECBTC) + UAC@9c491bdd
      (2026-05-22): +7 groups (NDX/RUT/DJIA/GOLD/CRUDE_OIL/NATGAS/EUR_UP_DOWN_DAILY) added to CanonicalQuestionGroup +
      PREDICTION_GROUPS + cme_polymarket_link.py; 5 new unit tests 27/27 pass. QG exit 0.

## Phase 3 — MTDS binary-outcome shard atom

- [x] ✅ [SCRIPT] P1. MTDS `PartitionedTickWriter` event_contract_bundle_counts; orchestrator finalize loop with
      `record_captured_from_counts` per (root, resolution_month) bundle; UAC `EVENT_CONTRACT` in `BUNDLED_DATA_TYPES`;
      `extract_event_contract_shard_key`; `EVENT_CONTRACT_ROOT_CLUSTERS` (9 roots) + `DATA_TYPE_TO_CLUSTER_REGISTRY`
      wired. TEMPORARY: expected == observed until Phase 4 IS catalog. (mtds@`b59b63e`, uac@`f70b975`, uac@`2751910`)

## Phase 4 — instruments-service per-cluster expiry

- [x] ✅ [SCRIPT] P1. Databento adapter: BAG + EC\* prefix -> EVENT_CONTRACT; `_estimate_available_since` EVENT_CONTRACT
      branch; UTL `event_contracts.py` with `expiry_for_cluster(root, resolution_date, strike_threshold)` at CME 21:00
      UTC settlement; 18 new unit tests. (instruments-service@`7a3db05`, UTL@`3c004c1`)

## Phase 5 — strategy-service cross-venue arb archetype

- [x] ✅ [SCRIPT] P1. New archetype `ARBITRAGE_CROSS_DOMAIN_EVENT` in strategy-service — strategy-service@2c59f2ce
      (2026-05-22): `cme_polymarket.py` engine + factory.py registration + TIER*STABLE_STRUCTURAL Kelly +
      GREENFIELD_ARCHETYPES + 3 target_universe seed rows (ECES×2 + ECBTC×1). Reads
      `cme_event_bid*{root}`/`cme*event_ask*{root}`+`polymarket*yes_bid*{group}`/ `polymarket*yes_ask*{group}` features;
      emits LEADER_HEDGE AtomicInstruction when net basis > threshold. CME leg venue="CME"; Polymarket leg
      venue="POLYMARKET". QG all gates green.

## Codex updates

- [x] ✅ [AGENT] P1. `per-asset-group-bucket-layouts.md` EVENT_CONTRACT shard atom bullet;
      `category-instrument-coverage.md` Family 4 ARBITRAGE_PRICE_DISPERSION cross-venue row; NEW
      `/codex/16-strategy-playbooks/strategy/cme-polymarket-arb.md` stub. (PM@2026-05-08)

## Temporary states + canonical follow-up plans

- Phase 2 CLEARED: all 9 roots wired — UAC@9c491bdd (2026-05-22). `predictions_master` Phase 5 UAC portion done.
- Phase 5 post-cutover: full `cme_polymarket_event_arb` archetype via standard paper-trade onboarding checklist.
- Manifest re-classification of existing `instrument_type=OPTION` rows for 9 EC\* roots: deferred until Phase 3 ships.

## Deferred work — migrated to:

**MIGRATED FROM:** this plan → `plans/epics/tradfi_master.md` P2:

- **Phase 5 full archetype onboarding**: `cme_polymarket_event_arb` archetype paper-trade → live via standard promote
  checklist (post-cutover, no date set)
- **OPTION row re-classification**: manifest re-classification of existing `instrument_type=OPTION` rows for 9 EC\*
  roots (ECES/ECBTC/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECNQ) — deferred until IS Phase 3 ships
