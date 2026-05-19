---
title: "features-tick-observation-audit: per-tick feature snapshot + MTDS provenance chain"
created: 2026-05-18
author: harsh-slot-6
source:
  - plans/active/_agent_pings.md (ikenna-main → harsh-main 2026-05-18 11:38 + 11:43 + 12:17 UTC)
  - plans/active/hedge_ratio_snapshot_persistence_2026_05_13.md (pattern source)
  - unified-api-contracts/unified_api_contracts/internal/domain/defi/sim_schemas.py
related_archetypes:
  - CARRY_STAKED_BASIS
estimate_class: brand-new
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.0
estimate_calibration_note: |
  brand-new 1.0×. New data_type + UAC schema + inline writer + manifest wiring + consumer
  reader. Mirrors hedge_ratio_snapshot_persistence Pattern A — but involves features-onchain
  engine wiring which adds surface area. Baseline 2 AI-days.
locked_by: live-defi-rollout
locked_since: 2026-05-18
---

# features-tick-observation-audit: per-tick feature snapshot + MTDS provenance

## Why this plan exists

**Audit gap surfaced 2026-05-18** (harsh-main ping at 11:38 UTC): the features-onchain-service
has no per-tick snapshot of what values it consumed from MTDS and what transformations it applied
before emitting the feature the strategy engine reads.

The full audit chain we want:
```
correlation_id → StrategyDecisionContextRecord (strategy-service, Phase 5 ✅ ikenna)
              → FeatureObservationRecord (features-onchain-service, THIS PLAN)
              → MTDS source rows (GCS parquet path + row ID)
```

Without `FeatureObservationRecord`, the join between strategy decision and raw market data
requires guessing on timestamp windows — brittle for pvl-p18b live-cutover-readiness audit.

**Routing decision** (ikenna-main 11:43 UTC): new sibling sub-plan under Harsh ownership.
features-onchain is Harsh territory (slot-6 live_pipeline). Ikenna owns strategy-side Phase 5
consumer. The `correlation_id` is the join key — already on LDR as `StrategyDecisionContextRecord.correlation_id: str | None` (ikenna Phase 5 ✅ 12:35 UTC).

## Pattern

Mirrors `hedge_ratio_snapshot_persistence_2026_05_13.md` (Pattern A inline parquet writer):
- UAC: `FeatureObservation` + `FeatureObservationRecord` Pydantic in `sim_schemas.py`
- features-onchain: `FeatureObservationWriter` (inline Pattern A) in engine
- manifest: `record_captured` per (date, archetype, chain)
- Every tick, no gate — we need the data even on non-rebalance ticks

---

## Phase 1 — UAC schema + registry entries

**Gate**: `FeatureObservation` + `FeatureObservationRecord` in UAC with correct exports;
availability_semantics + source_priority registered; UAC `quality-gates.sh` passes.

- [x] ✅ [UAC] P0. `FeatureObservation` + `FeatureObservationRecord` Pydantic added to
      `unified_api_contracts/internal/domain/defi/sim_schemas.py` Phase 6 section.
      Fields: archetype, chain, asset, tick_ts; stake_apy_bps, borrow_apy_bps,
      perp_funding_apy_bps, net_apr_computed_bps; mtds_parquet_path, mtds_row_id,
      staleness_seconds, fallback_fired, fallback_reason. Record adds partition_dt,
      available_at, `correlation_id: str | None = None`. — UAC@(slot-6 Phase 1 scaffold)
- [x] ✅ [UAC] P0. `("defi", "feature_observation_snapshot"): "fetch_completed_at"` registered
      in `availability_semantics.py`. — UAC@(slot-6 Phase 1 scaffold)
- [x] ✅ [UAC] P0. `("defi", "feature_observation_snapshot"): ["features_onchain_service"]`
      registered in `source_priority.py`. — UAC@(slot-6 Phase 1 scaffold)
- [x] ✅ [UAC] P0. `FeatureObservation` + `FeatureObservationRecord` exported from
      `internal/domain/defi/__init__.py` + `internal/__init__.py`. — UAC@(slot-6 Phase 1 scaffold)
- [ ] [UAC] P0. Unit test: `test_feature_observation_record_roundtrip` in
      `tests/internal/unit/test_domain_schemas.py` — instantiate `FeatureObservationRecord`
      with all fields + assert model_dump roundtrip. Run `quality-gates.sh`.
- [ ] [UAC] P0. QG: `bash scripts/quality-gates.sh` passes (basedpyright + ruff + cassette parity).

---

## Phase 2 — features-onchain writer scaffold

**Gate**: `FeatureObservationWriter` in features-service engine; dry_run=True path tested.

- [x] ✅ [features-service] P0. `features_service/onchain/engine/feature_observation_writer.py`
      created with `emit_feature_observation(observation, correlation_id, *, project_id, dry_run)`.
      Pattern A: build FeatureObservationRecord → write local parquet → upload to GCS →
      delete temp file. Errors swallowed + logged. dry_run suppresses GCS I/O. — features-service@(slot-6 Phase 2 scaffold)
- [ ] [features-service] P1. Wire `emit_feature_observation` into
      `features_service/onchain/engine/orchestrator.py` (or the tick-dispatch path).
      Call on every tick, passing `correlation_id=None` for now. Target: every on_tick
      call emits one snapshot row.
- [ ] [features-service] P1. Unit tests in
      `tests/onchain/unit/test_feature_observation_writer.py`:
      (1) dry_run=True → no GCS call; (2) emit produces correct partition_dt;
      (3) correlation_id=None round-trips as None; (4) Decimal fields converted for pyarrow.
      Run `quality-gates.sh`.
- [ ] [features-service] P2. Manifest wiring: after each tick's batch of observations,
      call `manifest_writer.record_captured(data_type="feature_observation_snapshot",
      asset_group="defi", dt=partition_dt, archetype=archetype, chain=chain)`.
      Shard atom: (date, archetype, chain) — matches the GCS hive path.

---

## Phase 3 — correlation_id wiring

**Dependency**: Ikenna Phase 5 (`StrategyDecisionContextRecord.correlation_id`) is already on
LDR (ikenna-main 12:35 UTC ✅). This phase wires the key end-to-end.

- [ ] [features-service] P1. Propagate `correlation_id` into `emit_feature_observation`:
      the strategy engine passes its `correlation_id` (from `AtomicInstruction.instruction_id`)
      to features-service on_tick calls. Update function signature + engine wiring.
      `correlation_id: str | None = None` field already in `FeatureObservationRecord`.
- [ ] [features-service] P1. Integration test (mocked GCS): emit a record with
      `correlation_id="test-123"`, read back the parquet, assert `correlation_id == "test-123"`.
- [ ] [PM/codex] P2. Add `correlation_id` to the audit chain doc at
      `codex/04-architecture/amm-slippage-simulation.md` § "Audit chain" (alongside
      StrategyDecisionContext Phase 5 section).

---

## Phase 4 — pnl-attribution reader

**Owner**: Ikenna (strategy-side Phase 5 consumer). Tracked here for cross-side visibility.

- [ ] [pnl-attribution-service] P2. `PnlDomainAdapter.read_feature_observation_snapshot()`
      method. Path: `feature_observation_snapshot/asset_group=defi/archetype={a}/
      chain={c}/dt={d}/*.parquet`. **DEFERRED to ikenna-side work** per routing decision.
      Named successor: ikenna strategy/pnl-attribution workstream.

---

## Success criteria

- [ ] UAC QG passes with `FeatureObservation` + `FeatureObservationRecord`
- [ ] features-service QG passes with `FeatureObservationWriter` + unit tests
- [ ] `emit_feature_observation` called on every features-onchain tick
- [ ] `correlation_id` flows end-to-end: engine tick → features writer → GCS parquet
- [ ] Audit query: given `correlation_id`, SQL join returns strategy decision + feature observation

## Temporary states + their canonical follow-up plans

- **correlation_id = None scaffold** (Phase 1/2): wired as `str | None = None` pending Phase 3
  propagation. Successor: Phase 3 of this plan.
- **pnl-attribution reader** (Phase 4): deferred to ikenna strategy workstream. Successor:
  ikenna-side pnl-attribution plan (to be opened when Phase 4 is scheduled).
- **cefi/tradfi parallel** (not in scope): DeFi first per ikenna-main routing. Successor:
  opened when cefi/tradfi carry archetypes need the same audit chain.
