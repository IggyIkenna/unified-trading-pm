---
doc_type: plan
title: HedgeRatioSnapshot persistence — emit-to-data_type sub-plan
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, deployment-ui, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-13"
---

> **ARCHIVED 2026-05-19** — 100% complete (all items); preserved for archaeology.

---

title: HedgeRatioSnapshot persistence — emit-to-data_type for pnl-attribution consumption type: plan status: archived
created: 2026-05-13 deadline: 2026-05-21 horizon: ~2-3 day mini-plan locked_by: live-defi-rollout locked_since:
2026-05-13 priority: P1 parent_plan: defi_simulation_realism_2026_05_10.md spawned_from: |
defi_simulation_realism_2026_05_10.md Phase 6B-WIRE-IN DEFERRED: "P1 — emit HedgeRatioSnapshot rows to a dedicated
downstream data_type (today's attestations bundle is the audit trail; persistence via a new hedge_ratio_snapshots
writeback can land after Phase 6C identifies which downstream service consumes the audit log)." related_plans:

- defi_simulation_realism_2026_05_10.md (Phase 6 hedge-ratio)
- client_reporting_pnl_attribution_mvp_2026_05_10.md (consumer) estimate_class: design estimate_baseline_ai_days: 3
  estimate_calibrated_ai_days: 1.8 estimate_calibration_note: | Design class — UAC data_type registration + writer
  wire-in + consumer schema mapping

* parquet path SSOT + manifest entry. ~3 baseline × 0.6 multiplier = 1.8 cal-AI-days.

---

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each `- [ ]` item in body for the specific successor / blocker per-item. No single migration target
— this plan tracks multiple per-item dispositions.

# HedgeRatioSnapshot persistence — emit-to-data_type sub-plan

## Why this plan exists

Phase 6B-WIRE-IN of `defi_simulation_realism_2026_05_10.md` shipped `CarryStakedBasisEngine.on_tick` calling
`compute_dynamic_hedge_ratio` per tick (strategy-service@`6431955`). The decision's `HedgeRatioSnapshot` is currently
attached to `AtomicInstruction.attestations` as **audit metadata** — co-emitted with the trade instruction. But:

- **No standalone parquet emission**: there's no `hedge_ratio_snapshots` data_type, no manifest entry, no daily
  writeback. Phase 6C dynamic-vs-static backtest harness (strategy-service@`7eb3dab`) needs these rows as a primary data
  source for residual-variance analysis, not as an attestations side-channel.
- **pnl-attribution-service** is the canonical consumer per the `client_reporting_pnl_attribution_mvp_2026_05_10.md`
  plan. Its per-archetype attribution requires the hedge-ratio state at each rebalance point to decompose realised P&L
  into (a) carry yield, (b) hedge-residual P&L, (c) execution alpha.
- Without standalone persistence, the Phase 6C "dynamic vs static" comparison cannot be reconstructed from the audit
  trail alone — it'd need to join `AtomicInstruction` history × strategy decisions, which is fragile.

## Scope

### In scope

1. **UAC data_type registration** — add `HEDGE_RATIO_SNAPSHOT` to the canonical data_type enum (likely in
   `unified_api_contracts/canonical/crosscutting/data_types.py` or equivalent SSOT).
2. **UAC parquet schema** — define the on-disk column shape mirroring the Phase 1F `HedgeRatioSnapshot` Pydantic model
   (archetype, instrument_long, instrument_short, target_ratio, realized_ratio, peg_drift_bps, peg_drift_threshold_bps,
   last_adjustment_at, rebalance_triggered, captured_at) + standard `available_at` / `partition_dt` columns per
   `unified_api_contracts.availability_semantics`.
3. **Bucket + path SSOT** — register `hedge_ratio_snapshots` under `deployment-service/configs/cloud-providers.yaml`
   (likely under existing strategy-output bucket since this is strategy-emitted; verify with
   `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0f conventions). Path pattern:
   `gs://{pid}-strategy-output/hedge_ratio_snapshots/asset_group=defi/archetype={archetype}/dt={YYYY-MM-DD}/...parquet`.
4. **Producer wire-in** — at strategy-service `CarryStakedBasisEngine.on_tick`, when `decision.rebalance_triggered=True`
   emit the snapshot. Two design choices to decide before code:
   - **(A) Inline write** — strategy-service writes the parquet row in-thread alongside the trade instruction emit.
     Simple but adds I/O to the strategy hot path.
   - **(B) Append to an in-memory buffer + flush** — strategy-service appends to per-archetype-per-day buffer; a
     separate flush thread writes parquet rows at minute/hour cadence + on shutdown. Decouples hot path from I/O.
   - **Recommendation**: (B) for live trading (avoids strategy-loop latency); (A) is OK for batch backtest mode.
     `batch=live` SSOT means the same code path must work both ways → use a writer abstraction that auto-buffers in live
     and inline-writes in batch.
5. **Manifest entry** — register the data_type in `ManifestWriter` per CLAUDE.md "Availability manifest v5+";
   `record_captured` per-archetype-per-day with `available_at`.
6. **Consumer read** — `pnl-attribution-service` reads via the standard UAC reader interface; verify schema parity with
   the Pydantic model.
7. **Tests** — unit (writer schema correctness, manifest record_captured), integration (round-trip parquet via the mock
   cloud emulator).

### Out of scope

- Phase 6C dynamic-vs-static backtest harness — already shipped at strategy-service@`7eb3dab`; this sub-plan only adds
  the persistence layer it consumes.
- Streaming / real-time ingestion of hedge_ratio_snapshots to a Pub/Sub topic — defer to post-cutover when live-mode
  consumers need sub-minute freshness.
- UI rendering of hedge-ratio history — deployment-ui can add a panel later if operator wants.

## Phased execution DAG

### Phase 0 — Pre-audit + design call (~0.3 cal AI-days)

**Design decisions (slot-5 2026-05-17 ~21:30 UTC):**

- Fields sufficient: YES — `HedgeRatioSnapshot` has all required fields. Added `HedgeRatioSnapshotRecord` with
  `partition_dt`/`available_at`/`correlation_id` for parquet-specific shape.
- Bucket: `strategy-store` / `defi` asset_group (existing bucket; no new bucket — cardinality/retention identical).
- Writer pattern: **Pattern A (inline)** for both batch + live — rebalance events are infrequent (~25 bps threshold), so
  I/O latency is not a concern; inline is simpler + same code path per batch=live SSOT.

- [x] [SCRIPT] P0. Verify Phase 1F `HedgeRatioSnapshot` Pydantic model fields are sufficient for downstream consumer
      (pnl-attribution Phase 6C). ✅ All 10 fields present; `HedgeRatioSnapshotRecord` adds
      `partition_dt`/`available_at`/`correlation_id`. uac@`2fcb1bb`
- [x] [SCRIPT] P0. Decide on bucket choice — reuse `strategy-output` or create new `hedge-ratio-snapshots` bucket? ✅
      Reuse `strategy-store` / defi. uac@`2fcb1bb`
- [x] [SCRIPT] P0. Decide writer pattern (A inline vs B buffer). ✅ Pattern A inline for both modes. uac@`2fcb1bb`

### Phase 1 — UAC data_type + parquet schema (~0.5 cal AI-days)

- [x] [SCRIPT] P0. Add `DataType.HEDGE_RATIO_SNAPSHOT` to UAC enum (location per SSOT canonical/crosscutting). ✅ Added
      as `(defi, hedge_ratio_snapshot)` in `availability_semantics` + `source_priority` + `pipeline_mode`. uac@`2fcb1bb`
- [x] [SCRIPT] P0. Define `HedgeRatioSnapshotRecord` parquet schema in
      `unified_api_contracts/internal/domain/defi/sim_schemas.py`. ✅ Extends `HedgeRatioSnapshot` with `partition_dt` +
      `available_at` + `correlation_id`. uac@`2fcb1bb`
- [x] [SCRIPT] P0. Register data_type with `availability_semantics.AVAILABILITY_AT_SEMANTICS` (live-pipeline-arrival
      stamping per CLAUDE.md HARD RULE). ✅ `fetch_completed_at` semantic registered. uac@`2fcb1bb`
- [x] [SCRIPT] P0. Add bucket kind to `deployment-service/configs/cloud-providers.yaml` if new bucket; else map
      data_type to existing strategy-output bucket via `resolve_bucket_name(kind=..., asset_group="defi")`. ✅ No new
      bucket — reuses `strategy-store`. uac@`2fcb1bb`

### Phase 2 — Producer wire-in (~0.6 cal AI-days)

- [x] [AGENT] P0. Add `HedgeRatioSnapshotWriter` to `strategy_service/` (or use UTL `ManifestWriter` generic). Pattern
      decided in Phase 0. ✅ `hedge_ratio_writer.py` with `emit_hedge_ratio_snapshot` + `build_hedge_ratio_snapshot`.
      strategy-service@`21209bd`
- [x] [AGENT] P0. Wire `CarryStakedBasisEngine.on_tick` to emit on `decision.rebalance_triggered=True`. Include all
      Phase 1F fields + `partition_dt` from event timestamp + `correlation_id` from trade context. ✅ Wired inline after
      baseline update, using `instruction.instruction_id` as `correlation_id`. strategy-service@`21209bd`
- [x] [AGENT] P0. Manifest entry per CLAUDE.md "Availability manifest v5+" —
      `record_captured(asset_group="defi",     data_type=HEDGE_RATIO_SNAPSHOT, partition_dt=..., venue_name="strategy-internal")`.
      ✅ Best-effort
      `record_captured(category="defi", data_type="hedge_ratio_snapshot",     pipeline_mode=BATCH_STRATEGY_SERVICE)` in
      `_record_manifest()`. strategy-service@`21209bd`
- [x] [AGENT] P0. Unit test: synthetic decision → emit row → assert parquet schema matches contract. ✅ 6 tests in
      `test_hedge_ratio_writer.py` (schema round-trip, blob_path, row values, exception-swallow).
      strategy-service@`21209bd`

### Phase 3 — Consumer schema mapping (~0.4 cal AI-days)

- [x] [AGENT] P0. `pnl-attribution-service` reader: load `hedge_ratio_snapshots` parquets per archetype + date range.
      Confirm UAC reader interface (`unified_api_contracts.readers.<...>`). ✅
      `PnlDomainAdapter.read_hedge_ratio_snapshots()` added to `adapters/domain_adapter.py` using
      `resolve_bucket_name(strategy-store/defi)` + `get_storage_client()` direct download pattern (no PATH_REGISTRY —
      custom hive path). 5 unit tests in `test_hedge_ratio_snapshot_reader.py`. pnl-attribution-service@`ee96d3c`
- [x] [AGENT] P0. Update `client_reporting_pnl_attribution_mvp` plan Phase 2 with `hedge_ratio_snapshots` as upstream
      dependency; cross-reference this plan. ✅ Consumer plan (`client_reporting_pnl_attribution_mvp_2026_05_10.md`) is
      archived at 100% done (2026-05-16 sweep). Cross-reference captured in codex `amm-slippage-simulation.md` Phase 4
      update instead (consumer chain doc). pnl-attribution-service@`ee96d3c`

### Phase 4 — Codex SSOT + plan close (~0.2 cal AI-days)

- [x] ✅ [SCRIPT] P0. Update `/codex/04-architecture/amm-slippage-simulation.md` § "Hedge-ratio dynamic adjustment" with
      writeback pattern + consumer chain. ✅ Added FULLY SHIPPED banner with UAC@2fcb1bb + strategy-service@21209bd +
      pnl-attribution-service@ee96d3c commit refs.
- [x] ✅ [SCRIPT] P0. Flip parent plan `defi_simulation_realism_2026_05_10.md` Phase 6B-WIRE-IN DEFERRED entry with this
      sub-plan's commit reference. ✅ DEFERRED note updated to RESOLVED 2026-05-17 with all 3 commit refs.
- [x] ✅ [SCRIPT] P0. Archive this sub-plan. **[unlock-plan]** Phase 5 fully shipped; all items complete.
      unified-trading-pm@archive-2026-05-19.

### Phase 5 — Pre-decision INPUTS observability (scope addition 2026-05-18 by harsh-main)

**Why Phase 5 exists** (discovered on running B-015 paper VM `strategy-paper-carry-staked-basis-20260518-115404` at
2026-05-18 11:20 UTC):

The VM ran 5 consecutive ticks with `fills=0 | PnL=$0.00`. Phases 1-4 of this plan correctly persist the OUTPUT of
`compute_dynamic_hedge_ratio()` when `rebalance_triggered=True`, but the writer never fires when no rebalance happens —
so the engine's INPUTS (stake_apy observed, perp_funding observed, computed net_apr, peg-drift threshold value,
decision-not-to-rebalance reason) are not captured anywhere. Result: 5 hours of opaque ticks with no audit trail to
distinguish (a) carry not favorable, (b) threshold too aggressive, (c) feature stale, (d) config bug.

This is a Phase 6C / pvl-p18b consumer-side requirement that Phase 3 of this plan
(`PnlDomainAdapter.read_hedge_ratio_snapshots`) cannot satisfy — pnl-attribution + p18b matrix need to reason about
_why_ a rebalance didn't fire, not just _what happened_ when one did. Filing as scope extension to this same plan
(rather than spawning sibling) per operator direction 2026-05-18: persistence story should cover both output + input
sides coherently.

**Scope additions**:

- [x] ✅ [SCRIPT] P0. Add `DataType.STRATEGY_DECISION_CONTEXT` to UAC — design decision: separate data_type (not
      extending HedgeRatioSnapshotRecord) per plan's rationale (different cadence, different fields). — uac@b8bdedf
      (2026-05-18). `DecisionOutcome(StrEnum)` typed enum added (replaces untyped `str` field) uac@2494e0d (2026-05-18
      slot 3).
- [x] ✅ [SCRIPT] P0. Define `StrategyDecisionContextRecord` parquet schema covering: `stake_apy_bps`, `borrow_apy_bps`,
      `perp_funding_apy_bps`, `usdc_idle_apy_bps`, `computed_net_apr_bps`, `peg_drift_observed_bps`,
      `peg_drift_threshold_bps`, `decision_outcome: DecisionOutcome`, `decision_reason_detail`,
      `position_state_long_units`, `position_state_short_units`, standard
      `partition_dt`/`available_at`/`correlation_id`. Registered in availability_semantics + source_priority. —
      uac@b8bdedf (2026-05-18). Enum typed uac@2494e0d.
- [x] ✅ [AGENT] P0. Wire emitter into `CarryStakedBasisEngine.on_tick` **before** the `rebalance_triggered` gate —
      Pattern A inline, fires on EVERY tick. `decision_context_writer.py` + `build_decision_outcome()`.
      strategy-service@`3c332ac` (emitter wire-in) + strategy-service@`285f154` (11 unit tests) +
      strategy-service@`df2ff9f` (autouse perf guard, slot 3 2026-05-18).
- [x] ✅ [AGENT] P0. Extend `pnl-attribution-service` `PnlDomainAdapter` with `read_strategy_decision_context()` —
      mirrors `read_hedge_ratio_snapshots()` shape. pnl-attribution-service@`f8db566`.
- [x] ✅ [AGENT] P0. Manifest entry — `_record_manifest()` included in `emit_strategy_decision_context()`; calls
      `ManifestWriter.record_captured(data_type="strategy_decision_context", category="defi")`.
      strategy-service@`3c332ac`.
- [x] ✅ [AGENT] P0. Unit tests — 11 tests: `REBALANCED` round-trip, 5x `HOLD_WITHIN_DRIFT_BAND` variants,
      `HOLD_FEATURE_STALE`, exception swallow, schema match, row value verification. strategy-service@`285f154`. Autouse
      perf guard (720-tick batch overhead eliminated): strategy-service@`df2ff9f`.
- [x] ✅ [SCRIPT] P0. Updated `/codex/04-architecture/amm-slippage-simulation.md` § "Hedge-ratio dynamic adjustment" —
      added "Phase 5 pre-decision audit trail" subsection with full commit refs. unified-trading-pm@see-flip-commit.
- [x] ✅ [SCRIPT] P0. Cross-side notify filed (harsh-main → ikenna-main `_agent_pings.md` 2026-05-18 11:20 UTC) + acked
      (ikenna-main → harsh-main `_agent_pings.md`:3469 2026-05-18 11:23 UTC).

**Cost trade-off**: this is independent of the running B-015 paper VM. Harsh-main is keeping VM 115404 running
(preserves pvl-p18a 3-day clock; gate doesn't require this observability). Phase 5 lands as separate work, applies on
next natural VM relaunch (post-pvl-p18a or live-promote cycle). No clock loss.

**Owner** (per parent plan): assigned to whoever picks up the work — Ikenna's slot 5 / slot 7 (active strategy-service
work) is a natural fit, but harsh-main can also execute if Ikenna ack'd. Awaiting ikenna-main ack on the cross-side
ping.

**Estimate**: design class — UAC schema + writer + on_tick wire-in + consumer reader + tests. ~3 baseline × 0.6
multiplier = **1.8 cal-AI-days**.

## Full-execution criterion

- ✅ UAC data_type registered + parquet schema defined + bucket-name SSOT entry.
- ✅ `CarryStakedBasisEngine` emits a `hedge_ratio_snapshots` row on every rebalance trigger; verified via integration
  test that does a 10-tick synthetic run and reads back the parquet.
- ✅ `pnl-attribution-service` reads the parquet successfully + schema matches.
- ✅ ManifestWriter records the snapshot per-archetype-per-day.
- [x] ✅ **Phase 5**: `CarryStakedBasisEngine` emits a `strategy_decision_context` row on **every** tick (HOLD +
      rebalance); 11 unit tests cover REBALANCED + 5x HOLD variants + HOLD_FEATURE_STALE + exception swallow.
      strategy-service@`3c332ac` + strategy-service@`285f154` + strategy-service@`df2ff9f`.
- [x] ✅ **Phase 5**: `pnl-attribution-service` reads `strategy_decision_context` parquets + can answer "for tick at T,
      what rates did the engine see and why did it not rebalance". pnl-attribution-service@`f8db566`.

## Execution metadata (Runbook Execution-Owner SSOT)

```yaml
execution:
  owner: slot 6 follow-up (next cycle after Phase 3C closure)
  cadence: per-deploy (data_type + schema is one-shot once shipped; consumer reads on each pnl-attribution run)
  verifier: integration test round-trip + ManifestWriter assertion
  last_executed: NEVER
```

## Cross-plan dependencies

- **Phase 1F** (UAC `HedgeRatioSnapshot` BaseModel @`78371aa`) — DONE; this plan extends.
- **Phase 6B-WIRE-IN** (strategy-service @`6431955`) — DONE; this plan adds the data_type emission step.
- **Phase 6C** (strategy-service @`7eb3dab` synthetic dynamic-vs-static backtest) — DONE; consumer will use this plan's
  parquet output to validate against real-data 1-year replay (Phase 8A in defi_simulation_realism plan).
- **client_reporting_pnl_attribution_mvp_2026_05_10.md** — consumer plan; will cross-reference this sub-plan from its
  Phase 2 upstream-dependencies section after Phase 3 lands here.
