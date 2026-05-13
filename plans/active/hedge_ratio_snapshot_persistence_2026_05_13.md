---
title: HedgeRatioSnapshot persistence — emit-to-data_type for pnl-attribution consumption
type: plan
status: active
created: 2026-05-13
deadline: 2026-05-21
horizon: ~2-3 day mini-plan
locked_by: live-defi-rollout
locked_since: 2026-05-13
priority: P1
parent_plan: defi_simulation_realism_2026_05_10.md
spawned_from: |
  defi_simulation_realism_2026_05_10.md Phase 6B-WIRE-IN DEFERRED:
  "P1 — emit HedgeRatioSnapshot rows to a dedicated downstream data_type
   (today's attestations bundle is the audit trail; persistence via a new
   hedge_ratio_snapshots writeback can land after Phase 6C identifies which
   downstream service consumes the audit log)."
related_plans:
  - defi_simulation_realism_2026_05_10.md (Phase 6 hedge-ratio)
  - client_reporting_pnl_attribution_mvp_2026_05_10.md (consumer)
estimate_class: design
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.8
estimate_calibration_note: |
  Design class — UAC data_type registration + writer wire-in + consumer schema mapping
  + parquet path SSOT + manifest entry. ~3 baseline × 0.6 multiplier = 1.8 cal-AI-days.
---

# HedgeRatioSnapshot persistence — emit-to-data_type sub-plan

## Why this plan exists

Phase 6B-WIRE-IN of `defi_simulation_realism_2026_05_10.md` shipped `CarryStakedBasisEngine.on_tick` calling
`compute_dynamic_hedge_ratio` per tick (strategy-service@`6431955`). The decision's `HedgeRatioSnapshot` is currently
attached to `AtomicInstruction.attestations` as **audit metadata** — co-emitted with the trade instruction. But:

- **No standalone parquet emission**: there's no `hedge_ratio_snapshots` data_type, no manifest entry, no daily
  writeback. Phase 6C dynamic-vs-static backtest harness (strategy-service@`7eb3dab`) needs these rows as a primary data
  source for residual-variance analysis, not as an attestations side-channel.
- **pnl-attribution-service** is the canonical consumer per the
  `client_reporting_pnl_attribution_mvp_2026_05_10.md` plan. Its per-archetype attribution requires the hedge-ratio
  state at each rebalance point to decompose realised P&L into (a) carry yield, (b) hedge-residual P&L, (c) execution
  alpha.
- Without standalone persistence, the Phase 6C "dynamic vs static" comparison cannot be reconstructed from the audit
  trail alone — it'd need to join `AtomicInstruction` history × strategy decisions, which is fragile.

## Scope

### In scope

1. **UAC data_type registration** — add `HEDGE_RATIO_SNAPSHOT` to the canonical data_type enum (likely in
   `unified_api_contracts/canonical/crosscutting/data_types.py` or equivalent SSOT).
2. **UAC parquet schema** — define the on-disk column shape mirroring the Phase 1F `HedgeRatioSnapshot` Pydantic model
   (archetype, instrument_long, instrument_short, target_ratio, realized_ratio, peg_drift_bps,
   peg_drift_threshold_bps, last_adjustment_at, rebalance_triggered, captured_at) + standard `available_at` /
   `partition_dt` columns per `unified_api_contracts.availability_semantics`.
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
     `batch=live` SSOT means the same code path must work both ways → use a writer abstraction that auto-buffers in
     live and inline-writes in batch.
5. **Manifest entry** — register the data_type in `ManifestWriter` per CLAUDE.md "Availability manifest v5+";
   `record_captured` per-archetype-per-day with `available_at`.
6. **Consumer read** — `pnl-attribution-service` reads via the standard UAC reader interface; verify schema parity
   with the Pydantic model.
7. **Tests** — unit (writer schema correctness, manifest record_captured), integration (round-trip parquet via the
   mock cloud emulator).

### Out of scope

- Phase 6C dynamic-vs-static backtest harness — already shipped at strategy-service@`7eb3dab`; this sub-plan only adds
  the persistence layer it consumes.
- Streaming / real-time ingestion of hedge_ratio_snapshots to a Pub/Sub topic — defer to post-cutover when live-mode
  consumers need sub-minute freshness.
- UI rendering of hedge-ratio history — deployment-ui can add a panel later if operator wants.

## Phased execution DAG

### Phase 0 — Pre-audit + design call (~0.3 cal AI-days)

- [ ] [SCRIPT] P0. Verify Phase 1F `HedgeRatioSnapshot` Pydantic model fields are sufficient for downstream consumer
      (pnl-attribution Phase 6C). If gaps (e.g. need `tx_hash` for blockchain attribution), file UAC schema extension.
- [ ] [SCRIPT] P0. Decide on bucket choice — reuse `strategy-output` or create new `hedge-ratio-snapshots` bucket?
      Read `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0f conventions; default to existing bucket unless
      cardinality / retention diverges materially.
- [ ] [SCRIPT] P0. Decide writer pattern (A inline vs B buffer). Record decision in plan body.

### Phase 1 — UAC data_type + parquet schema (~0.5 cal AI-days)

- [ ] [SCRIPT] P0. Add `DataType.HEDGE_RATIO_SNAPSHOT` to UAC enum (location per SSOT canonical/crosscutting).
- [ ] [SCRIPT] P0. Define `HedgeRatioSnapshotRecord` parquet schema in
      `unified_api_contracts/internal/positions/` or `unified_api_contracts/internal/domain/defi/` — extends
      the Phase 1F Pydantic model with `available_at` + `partition_dt` + `correlation_id` columns.
- [ ] [SCRIPT] P0. Register data_type with `availability_semantics.AVAILABILITY_AT_SEMANTICS` (live-pipeline-arrival
      stamping per CLAUDE.md HARD RULE).
- [ ] [SCRIPT] P0. Add bucket kind to `deployment-service/configs/cloud-providers.yaml` if new bucket; else map data_type
      to existing strategy-output bucket via `resolve_bucket_name(kind=..., asset_group="defi")`.

### Phase 2 — Producer wire-in (~0.6 cal AI-days)

- [ ] [AGENT] P0. Add `HedgeRatioSnapshotWriter` to `strategy_service/` (or use UTL `ManifestWriter` generic). Pattern
      decided in Phase 0.
- [ ] [AGENT] P0. Wire `CarryStakedBasisEngine.on_tick` to emit on `decision.rebalance_triggered=True`. Include all
      Phase 1F fields + `partition_dt` from event timestamp + `correlation_id` from trade context.
- [ ] [AGENT] P0. Manifest entry per CLAUDE.md "Availability manifest v5+" — `record_captured(asset_group="defi",
      data_type=HEDGE_RATIO_SNAPSHOT, partition_dt=..., venue_name="strategy-internal")`.
- [ ] [AGENT] P0. Unit test: synthetic decision → emit row → assert parquet schema matches contract.

### Phase 3 — Consumer schema mapping (~0.4 cal AI-days)

- [ ] [AGENT] P0. `pnl-attribution-service` reader: load `hedge_ratio_snapshots` parquets per archetype + date range.
      Confirm UAC reader interface (`unified_api_contracts.readers.<...>`).
- [ ] [AGENT] P0. Update `client_reporting_pnl_attribution_mvp` plan Phase 2 with `hedge_ratio_snapshots` as upstream
      dependency; cross-reference this plan.

### Phase 4 — Codex SSOT + plan close (~0.2 cal AI-days)

- [ ] [SCRIPT] P0. Update `codex/04-architecture/amm-slippage-simulation.md` § "Hedge-ratio dynamic adjustment" with
      writeback pattern + consumer chain.
- [ ] [SCRIPT] P0. Flip parent plan `defi_simulation_realism_2026_05_10.md` Phase 6B-WIRE-IN DEFERRED entry → `[x]`
      with this sub-plan's commit reference.
- [ ] [SCRIPT] P0. Archive this sub-plan with `Plans Run To Actual Completion` checklist.

## Full-execution criterion

- ✅ UAC data_type registered + parquet schema defined + bucket-name SSOT entry.
- ✅ `CarryStakedBasisEngine` emits a `hedge_ratio_snapshots` row on every rebalance trigger; verified via integration
  test that does a 10-tick synthetic run and reads back the parquet.
- ✅ `pnl-attribution-service` reads the parquet successfully + schema matches.
- ✅ ManifestWriter records the snapshot per-archetype-per-day.

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
