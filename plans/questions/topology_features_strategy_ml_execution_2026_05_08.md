---
title: Topology Q-group — features / strategy ensemble / ML / execution × batch / live / paper
type: question-doc
status: active-closing
created: 2026-05-08
status_changed: 2026-05-09
deadline: 2026-05-23
author: ikenna
related:
  - plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md
  - plans/active/features_repo_consolidation_2026_05_08.md
  - plans/epics/strategy_and_dart_master_2026_05_07.md
  - plans/epics/ml_and_features_master_2026_05_07.md
  - plans/epics/infrastructure_master_2026_05_07.md
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/defi_master_2026_05_07.md
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Topology Q-group — features / strategy ensemble / ML / execution × batch / live / paper

> **Purpose.** Pin the runtime topology of the four downstream-of-MTDS layers (features / strategy ensemble / ML /
> execution) across the three operational modes (batch / live / paper) for the **2026-05-23 live-DeFi cutover**. Per
> CLAUDE.md "Plans Run To Actual Completion, Not Smoke-Test Green" HARD RULE (codified 2026-05-08), **no question on this
> doc may defer post-cutover** — every Q either has a code-evidenced answer today or a P0 todo in an active plan that
> closes by 2026-05-23.
>
> **Annotation legend per Q:**
>
> - ✅ **ANSWERED** — code evidence cited (`file:line`); no further work needed pre-cutover.
> - 🟢 **IN-FLIGHT** — covered by a P0 todo in an active/epic plan with May-23 done-definition; cite plan + phase.
> - 🔴 **GAP** — no plan owns this; new P0 todo required by May-23. Closure destination + draft todo text in § 6.
>
> **What's already decided** (per
> [`live_pipeline_mtds_mdps_features_2026_05_08.md`](../active/live_pipeline_mtds_mdps_features_2026_05_08.md) +
> [`features_repo_consolidation_2026_05_08.md`](../active/features_repo_consolidation_2026_05_08.md)): MTDS standalone
> cluster · MDPS+features-asset-scoped colocated per asset_group · features-cross-cutting separate flavor · pipeline_mode
> hive partition · UAC SOURCE_PRIORITY fan-in · UTC-midnight alignment · same parquet schema across modes ·
> `CANDLE_BOUNDARY_CROSSED` + `CANDLE_COMPUTED` Redis Stream cascade · 4-category gap tree applied to live with
> stale-not-missing rule.

---

## Section 1 — Features layer

### 1.1 Static topology

- [ ] Q1.1.a — Is `features-asset-scoped` colocated with MDPS at the **process** level (same VM, separate processes
      IPC'd via Redis Stream) or the **container** level (one container, two threads/asyncio)?
  - 🟢 **IN-FLIGHT** — `live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 5.2: colocated per asset_group on same
    VM as **separate processes** communicating via Redis Stream `CANDLE_COMPUTED`. In-process MDPS→features handoff
    explicitly OPTIONAL post-May-23 optimization. **Today's reality** (post-investigation): NOT colocated yet —
    features and MDPS run as separate VM flavors per `deployment-service/deployment_service/catalog.py:48-51`.
    Co-location ships in Phase 5.2 by 2026-05-15 per plan.
- [ ] Q1.1.b — Does `features-cross-cutting` (cross-instrument / cross-venue / cross-asset_group calculators) run as a
      separate VM flavor or share infra with one of the asset-scoped clusters?
  - ✅ **ANSWERED** — `live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 5.2 + Phase 6: cross-cutting runs
    **separate flavor**, fans in via dedicated subscribers to multiple `CANDLE_COMPUTED` streams.
- [ ] Q1.1.c — Where does the `feature_family` UAC column get stamped — at calculator emit-time, or at a
      features-service-side router?
  - ✅ **ANSWERED** — `unified-api-contracts/canonical/domain/features/registry.py:13-50` defines `FeatureFamily` enum
    + `_SERVICE_TO_FAMILY` dict (line ~60). Stamped at **router layer** at calculator constructor time via
    `_build_feature_group_to_family()`. (Note: not yet a manifest v5 row key — additive only.)
- [ ] Q1.1.d — Post-features-repo consolidation, is the runtime still N processes (one per feature family) or one
      process with sub-package routing?
  - 🟢 **IN-FLIGHT** — `features_repo_consolidation_2026_05_08.md` Phase 7 (P0, May-13 deadline): ONE Docker image
    parameterized by `--feature-family` CLI flag; one `pyproject.toml`; per-family deployment flavors. So: ONE image,
    N processes (one per family) at deploy-time.

### 1.2 Mode behavior

- [ ] Q1.2.a — In **batch**, do features run as a daily DAG triggered post-MDPS, or as a streaming consumer of
      `CANDLE_COMPUTED` events replayed from history?
  - ✅ **ANSWERED** — Today: daily DAG via service CLI (`features_*_service/cli/main.py` `--operation compute`).
    Reads MDPS parquet directly via `gcs_feature_reader.py`. No Redis stream consumption in batch.
- [ ] Q1.2.b — In **live**, does each features process subscribe to `CANDLE_COMPUTED` directly, or is there a
      features-orchestrator in between?
  - 🟢 **IN-FLIGHT** — `live_pipeline_mtds_mdps_features_2026_05_08.md` Phase 5.2 + Phase 6: each features process
    subscribes **directly** to `CANDLE_COMPUTED` via consumer-group; no orchestrator middle-tier. **Today's reality
    is a SOFT BLOCKER**: live consumption is BLOCKED-ON writegate Phase 2.D adapter-side `available_at` stamping
    landing first. Phase 2.D is in-flight; live-stream wiring activates downstream once it lands. Cite gap in § 6.
- [ ] Q1.2.c — In **paper**, are features identical to live (same processes, same events), or do they replay from the
      same batch DAG as backtest?
  - ✅ **ANSWERED** — Per CLAUDE.md "Batch = Live: Unified Pipeline Architecture": **identical to live** — same
    process, same subscribers, same events. Paper differs only at the execution layer (matching engine vs live
    venue), not at the features layer.
- [ ] Q1.2.d — How is `available_at` stamped differently across the three modes? (Batch: write-time per source rules.
      Live: arrival-time. Paper: ?)
  - ✅ **ANSWERED** — Per CLAUDE.md "available_at is per-row, write-time, equal to live-pipeline-arrival": **same
    stamping rule across all 3 modes** = the live-pipeline arrival timestamp. Batch reconstructs it from source rules
    (kickoff − 60min, match_end_time, etc.); live = arrival time; paper = identical to live.

---

## Section 2 — Strategy ensemble (strategy + position-balance + risk-and-exposure + execution)

> The "strategy ensemble" = strategy-service + position-balance-monitor-service + risk-and-exposure-service +
> execution-service running in the **same logical unit** so strategy can call position/risk/execution synchronously
> without crossing a network. This is the colocated mesh the master plan refers to as "all normal component
> interactions."

### 2.1 Static topology

- [ ] Q2.1.a — Is the strategy ensemble **one VM per archetype** (carry_staked_basis VM separate from
      leveraged_funding_arb VM), **one VM per asset_group** (DeFi VM hosts both DeFi archetypes), or **one VM total**?
  - 🔴 **GAP** — no active plan owns this decision. Closes via § 6 GAP-1 (P0 todo into `strategy_and_dart_master`).
- [ ] Q2.1.b — Within a single VM, are the four services separate processes (HTTP/IPC) or one process (in-proc
      imports)? Per the "Batch = Live" CLAUDE.md rule the answer should be the same shape for both modes — what is it?
  - 🔴 **GAP** — `strategy_and_dart_master:Phase 1.9` covers handler/policy/orchestrator wiring but does not pin the
    process-vs-in-proc shape. Closes via § 6 GAP-2.
- [ ] Q2.1.c — How does strategy-service discover its colocated position-balance / risk / execution peers — env vars,
      config registry, service-mesh DNS, in-proc instantiation?
  - 🔴 **GAP** — closes via § 6 GAP-3 (linked to GAP-2; same plan todo can answer both).
- [ ] Q2.1.d — Does each archetype run its own dedicated ensemble, or is the ensemble multi-tenant across archetypes
      that share a wallet / venue?
  - 🔴 **GAP** — closes via § 6 GAP-4 (linked to GAP-1).

### 2.2 Mode behavior

- [ ] Q2.2.a — In **batch (strategy alpha)**, execution-service is in "always fill" mode (zero execution alpha, fills
      at requested price) — what flag/config flips it? Where does the flag live (UAC enum, env var, request payload)?
  - 🟢 **IN-FLIGHT** — `master_to_live_defi_2026_05_23.md` Group F item 17 (P0, May-23): `OperationalMode` enum
    (BATCH / PAPER / LIVE) + `ExecutionTarget` + `ExecutionTrigger` closed-set enums + `decompose(mode)` helper, all
    in UAC `internal/modes.py`. Always-fill = `BATCH` mode + `BenchmarkFillMode` per action type per
    `strategy_and_dart_master:Phase 1.9`.
- [ ] Q2.2.b — In **batch (execution alpha)**, the matching engine produces simulated fills — is that a separate VM
      run, or the same VM with a different mode flag, or a side-by-side process consuming the same strategy outputs?
  - ✅ **ANSWERED** — Same process, mode-flag dispatch. `execution_service/v2/matching_engine/` ships 5 matcher
    classes (L0 Sports, L1 TradFi, L2 CeFi, AMM, ALPHA_ZERO benchmark) per `strategy_and_dart_master:Phase 1.9`. Mode
    flag selects matcher vs live-venue connector.
- [ ] Q2.2.c — In **live**, how does strategy distinguish a live fill from a paper fill if both modes produce the same
      event shape? (Per "live = batch, only fill source differs" — what's the discriminator?)
  - 🟢 **IN-FLIGHT** — `master_to_live_defi_2026_05_23.md` Group F item 17d (P0, May-23): lift `mode: OperationalMode`
    field into UAC `StrategyInstructionEnvelope` + every fill event. Discriminator = the `mode` field on the
    envelope, propagated end-to-end.
- [ ] Q2.2.d — In **paper**, does execution-service still hit testnet/mainnet for read-side queries (gas estimates,
      pool state, orderbook depth) but never broadcast a tx, OR is it 100% offline simulation?
  - 🟢 **IN-FLIGHT** — `master_to_live_defi_2026_05_23.md` Group F item 20 (P0, May-23): per-venue testnet
    integration (Deribit EVM testnet, Tenderly fork EVM, Solana devnet). Decision per Settled #3:
    **simulate-first floor** = matching engine is universal paper-mode simulator; testnet hit only when testnet
    parity is being validated. Read-side queries hit live infra; writes go to matching engine.
- [ ] Q2.2.e — How is **paper mode P&L attribution** distinguished from live P&L in the position-balance-monitor
      ledger? Same db, separate `mode` column? Separate db?
  - 🟢 **IN-FLIGHT** — `master_to_live_defi_2026_05_23.md` Group F item 21 (P0, May-23): three-way reconciliation
    (batch ↔ paper ↔ live) requires `mode` column on every position/trade/PnL row. Same db, separate column.
    Schema migration covered in item 21a.

### 2.3 Cross-cutting

- [ ] Q2.3.a — Does risk-and-exposure-service have a **kill-switch authority** in live/paper that it does NOT have in
      batch (where strategy alpha is a measurement run, not a control loop)?
  - 🟢 **IN-FLIGHT** — `master_to_live_defi_2026_05_23.md` Group F item 22 (P0, May-23): R&E kill-switch rules
    engine + circuit-breaker integration. `kill_switch_scope=ARCHETYPE`, `kill_switch_drawdown_pct=5`,
    `position_breach_pct=20`. Authority = LIVE + PAPER only (not BATCH measurement runs).
- [ ] Q2.3.b — Does position-balance-monitor maintain **separate ledgers per mode** (batch_strategy_alpha,
      batch_execution_alpha, paper, live) or is mode just a tag on every entry?
  - 🟢 **IN-FLIGHT** — Same as Q2.2.e: single ledger + `mode` column per `master_to_live_defi_2026_05_23.md` Group F
    item 21a.
- [ ] Q2.3.c — When strategy emits a signal that the colocated execution-service can't fill (insufficient liquidity,
      rate-limit, kill-switch armed), what's the rejection event shape and who consumes it for retry / alert?
  - 🔴 **GAP** — closes via § 6 GAP-5 (P0 todo into `strategy_and_dart_master` for `ExecutionRejection` event +
    consumer wiring).

---

## Section 3 — ML layer (training + inference)

### 3.1 Static topology

- [ ] Q3.1.a — Is **ML training** colocated with features (consumes `CANDLE_COMPUTED` + features parquet directly) or
      a separate cluster pulling from GCS post-batch?
  - ✅ **ANSWERED** — Today: separate cluster. `ml-training-service` is a standalone repo + service. Reads features
    parquet from GCS via `ml-training-service/app/core/gcs_feature_reader.py`. NOT a streaming consumer.
- [ ] Q3.1.b — Is **ML inference** colocated with strategy-service (in-proc model.predict()), a separate service
      strategy calls over HTTP, or a streaming consumer that emits prediction events strategy subscribes to?
  - 🔴 **GAP** — Today: HTTP RPC from strategy-service to `ml-inference-service` (per architecture intent in
    `ml_and_features_master`). But: actual call-site wiring is **not yet audited or tested**. No integration test
    covers the strategy → ml-inference call path. `ml_and_features_master:Phase 4D` (P0, May-23 hard floor) ships
    "calibrated-signal consumption + cost-aware filtering" but **the acceptance pytest test does not exist** per
    code investigation. Closes via § 6 GAP-6.
- [ ] Q3.1.c — Where do ML model artifacts live (UAC config, MLflow registry, GCS bucket) and how does inference pick
      the right artifact for a given (archetype, asset_group, venue) tuple?
  - 🔴 **GAP** — Today: GCS buckets (likely `gs://{pid}-models/...`). No MLflow. No central registry SSOT in UAC.
    Selection logic ad-hoc. Closes via § 6 GAP-7 (lift model-registry SSOT into UAC).
- [ ] Q3.1.d — Does the ML cluster run per asset_group (mirroring features-asset-scoped) or is it monolithic?
  - 🟢 **IN-FLIGHT (decision deferred)** — Today: monolithic. `ml_and_features_master` notes per-asset-group
    sharding is **post-May-23 polish**, not a cutover blocker. Codify "monolithic ships May-23" as the explicit
    decision via § 6 GAP-8 (codex SSOT update only — no code change).

### 3.2 Mode behavior

- [ ] Q3.2.a — In **batch**, does ML inference run as a vectorized daily pass (predict-all-rows-at-once) or as a
      per-bar replay matching live exactly?
  - 🔴 **GAP** — `ml_and_features_master:Phase 1A` ships "batch feature read perf" but doesn't pin batch inference
    cadence. Closes via § 6 GAP-9 (per-bar replay required to honor "Batch = Live, only fill source differs").
- [ ] Q3.2.b — In **live**, what's the ML inference latency budget per signal, and is the model loaded in-proc
      (zero-RTT) or via RPC (non-zero)?
  - 🔴 **GAP** — No SLA documented. RPC adds ~5-50ms per signal; for sub-second carry/funding strategies this is
    fine, for high-freq it's not. Closes via § 6 GAP-10 (define + enforce SLA in `ml_and_features_master:Phase 4D`).
- [ ] Q3.2.c — In **paper**, is the same model artifact used as live, or a snapshot frozen at paper-run-start?
  - 🟢 **IN-FLIGHT** — `master_to_live_defi_2026_05_23.md` Group F item 20 (P0, May-23): "paper-mode evidence run
    ≥3 days" implies snapshot-at-run-start (otherwise mid-run model-update would invalidate the evidence). Codify
    via codex doc update folded into § 6 GAP-7.
- [ ] Q3.2.d — How does the LookaheadBiasError contract apply differently in batch (must respect `available_at`) vs
      live (arrival-time IS available_at by definition)?
  - ✅ **ANSWERED** (in spec) — `available_at` rule is identical across modes per CLAUDE.md "available_at is
    per-row, write-time, equal to live-pipeline-arrival." LookaheadBiasError raises loud on every features compute.
    **CRITICAL CODE GAP**: `features-onchain-service/features_onchain_service/app/core/feature_writer.py:125-131`
    wraps `PointInTimeEnforcer(strict=True)` in `contextlib.suppress(LookaheadBiasError)` — **suppresses the
    error**, violating CLAUDE.md rule. Filed as separate issue doc per § 6 ISSUE-1 (must fix before May-23).
- [ ] Q3.2.e — Is there an ML retraining cadence in live (online / weekly / monthly) and what's the topology for
      promoting a freshly-trained model into the running inference layer?
  - 🟢 **IN-FLIGHT** — `ml_and_features_master:Phase 4D` ships "live hot-reload + per-trade tagging." Cadence
    decision (online vs weekly vs monthly) folded into Phase 4D done-definition; codify via § 6 GAP-7.

---

## Section 4 — Execution layer

### 4.1 Static topology

- [ ] Q4.1.a — Is execution-service single-instance (one process serves all archetypes / asset_groups / venues) or
      fanned out (one instance per asset_group, or per venue)?
  - 🟢 **IN-FLIGHT** — Linked to Q2.1.a (single ensemble shape decision). `strategy_and_dart_master:Phase 1.9`
    covers venue-selection SOR + ATOMIC handler sub-modes. Closes alongside § 6 GAP-1.
- [ ] Q4.1.b — How does the **matching engine** for batch backtest sit relative to the live execution path — same
      process with a mode flag, separate process, or a library import inside execution-service?
  - ✅ **ANSWERED** — Same process, mode-flag dispatch. `execution_service/v2/matching_engine/` 5 matcher classes
    (L0 Sports, L1 TradFi, L2 CeFi, AMM, ALPHA_ZERO) per `strategy_and_dart_master:Phase 1.9`.
- [ ] Q4.1.c — DeFi vs CeFi vs sports vs prediction — does each have its own execution-service flavor / sub-package,
      or one service with adapter routing?
  - 🟢 **IN-FLIGHT** — `defi_master_2026_05_07.md` Fork 1 + `cefi_master_2026_05_07.md`: one execution-service +
    adapter routing per asset_group. Connectors validated on testnet per cefi audit.
- [ ] Q4.1.d — Where does the **wallet private key** live in the live DeFi path — Secret Manager + injected at
      request time, or held in execution-service memory for the VM's lifetime?
  - 🔴 **GAP** — Per CLAUDE.md "DeFi Execution Architecture" interface convention: `connector.connect(config={"wallet_private_key": pk, ...})` — keys flow from config dict. But: where the dict is constructed (per-request from
    Secret Manager vs VM-startup hold) is undocumented. Security-critical decision. Closes via § 6 GAP-11
    (P0 todo into `defi_master`).

### 4.2 Mode behavior

- [ ] Q4.2.a — Per "Batch = Live, only fill source differs" — what's the **clean seam** between strategy-side code
      and execution-side code such that flipping the seam is the only diff between batch and live?
  - 🟢 **IN-FLIGHT** — `master_to_live_defi_2026_05_23.md` Group F item 17 (P0, May-23): `ExecutionTarget` /
    `ExecutionTrigger` enums + `decompose()` helper define the seam. Strategy emits target+trigger; execution-service
    routes to matching engine OR live connector based on `mode` field.
- [ ] Q4.2.b — In **batch always-fill mode**, does the matching engine even run, or is it bypassed entirely with a
      "fill at requested price" stub?
  - 🟢 **IN-FLIGHT** — `strategy_and_dart_master:Phase 1.9`: `BenchmarkFillMode` per action type
    (arrival_mid, twap_window, pool_mid_at_block, ...). When BATCH + always-fill, matcher returns instant fill at
    benchmark price. Configured per archetype.
- [ ] Q4.2.c — In **batch matching-engine mode**, what assumptions does the engine use (slippage model, commission
      schedule, latency model, venue liquidity proxy) and where are those configured?
  - 🔴 **GAP** — `strategy_and_dart_master:Phase 1.9` ships matchers but doesn't enumerate the assumption surface
    (slippage, commission, latency, liquidity). Critical for backtest fidelity per master plan Group F item 18
    ("real gas / matching engine / cost+yield precision"). Closes via § 6 GAP-12.
- [ ] Q4.2.d — In **paper**, are tx broadcasts hard-blocked at the connector layer (e.g. `UniswapConnector` no-op's
      the broadcast), or at a higher policy layer that intercepts before reaching the connector?
  - 🟢 **IN-FLIGHT** — `master_to_live_defi_2026_05_23.md` Group F item 20 (P0): paper-mode dispatcher routes to
    matching engine, never reaches connector. Connector layer remains live-only; policy layer above intercepts.
- [ ] Q4.2.e — In **live**, is there a circuit-breaker that flips execution back to paper-mode mid-run if a
      kill-switch trips, and where does that gate live?
  - 🟢 **IN-FLIGHT** — `master_to_live_defi_2026_05_23.md` Group F item 22 (P0): kill-switch wiring + auto-recovery.
    R&E owns the circuit; execution-service consumes a kill-switch event and flips dispatcher to no-op (NOT to
    paper — kill means STOP, not switch-to-simulation). Codify "STOP not SWITCH" via codex doc update in § 6.

---

## Section 5 — Cross-mode invariants

- [ ] Q5.a — What is the **single canonical mode flag** (UAC enum? env var? request payload field?) and where does
      it propagate from (orchestrator → strategy → execution)?
  - 🟢 **IN-FLIGHT** — `master_to_live_defi_2026_05_23.md` Group F item 17 (P0, May-23): UAC `OperationalMode` enum
    (BATCH / PAPER / LIVE) in `unified_api_contracts/canonical/internal/modes.py`. Propagates via
    `StrategyInstructionEnvelope.mode` field.
- [ ] Q5.b — Does every event type carry the `mode` field, or is it inferred from the consumer's bootstrap config?
  - 🟢 **IN-FLIGHT** — `master_to_live_defi_2026_05_23.md` Group F item 17d + 22a (P0, May-23): `mode` field lifted
    into instruction envelope + alerting rules + every fill/position/PnL event. NO inference from bootstrap config.
- [ ] Q5.c — How is **batch-vs-live reconciliation** (master plan Group F item) implemented — same VM running both
      modes side-by-side and diffing, or two separate runs with a post-hoc reconciler reading both ledgers?
  - 🟢 **IN-FLIGHT** — UTL@908b1647 shipped `batch_live_reconciler` helper. `master_to_live_defi_2026_05_23.md`
    Group F item 21 (P0, May-23): two separate runs (live continuous + nightly batch replay) → post-hoc reconciler
    reads both ledgers via `mode` column, diffs per shard. 7-day live-vs-batch run gates cutover.
- [ ] Q5.d — Are there any **mode-asymmetric data types** (data the live pipeline produces that batch doesn't, or
      vice versa)? Per "Live = batch, same data, same fields, same timing semantics" — there should be ZERO. Verify.
  - ✅ **ANSWERED** — `live_pipeline_mtds_mdps_features_2026_05_08.md` + `features_repo_consolidation_2026_05_08.md`:
    same parquet schema across modes; only `pipeline_mode` hive partition differs; same `available_at` semantics. No
    mode-asymmetric data types.
- [ ] Q5.e — When a paper-trade run and a live run are happening simultaneously on the same wallet (e.g. live
      carry_staked_basis + paper leveraged_funding_arb), how are their position/risk views isolated?
  - 🔴 **GAP** — Three-way reconciliation (Group F item 21) covers per-mode P&L attribution but does NOT cover
    on-wallet position isolation when both modes hit the same address simultaneously. Critical for the May-23
    operating model (carry live + funding-arb paper ramp). Closes via § 6 GAP-13.

---

## Section 6 — May-23 closure plan (replaces old "cutover impact" framing)

> Per CLAUDE.md "Plans Run To Actual Completion, Not Smoke-Test Green" HARD RULE — **no Q on this doc may defer
> post-cutover**. The 13 GAPs identified in Sections 2-5 each map to either a P0 todo in an existing active/epic plan
> OR a new sub-plan, with done-definition closing by 2026-05-23. Plus 1 critical code-finding ISSUE filed separately.

### GAP closure matrix

| GAP    | Q-id           | Destination plan                     | Draft P0 todo text                                                                                                                                                                                                                                                                          |
| ------ | -------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GAP-1  | Q2.1.a, Q4.1.a | `strategy_and_dart_master_2026_05_07.md` Phase 1.9 | `[AGENT] P0. Pin strategy-ensemble VM topology for May-23: ONE VM per asset_group (DeFi VM hosts both DeFi archetypes; CeFi VM hosts hedge legs). Decision recorded in codex/04-architecture/strategy-ensemble-topology.md. Done = codex doc landed + launcher-script registry in deployment-service/scripts/vm/ updated.` |
| GAP-2  | Q2.1.b         | `strategy_and_dart_master_2026_05_07.md` Phase 1.9 | `[AGENT] P0. Pin process-vs-in-proc shape for strategy-ensemble: 4 services as SEPARATE processes on same VM, IPC via local Redis Stream + UCI HTTP within-VM. Same shape for batch + live (Batch = Live invariant). Codex doc + execution-service entrypoint config land together.` |
| GAP-3  | Q2.1.c         | (folds into GAP-2)                   | (covered by GAP-2 codex doc — service-discovery section: env vars `POSITION_BALANCE_URL` / `RISK_EXPOSURE_URL` / `EXECUTION_URL`, default to `http://localhost:{port}` when colocated)                                                                                                       |
| GAP-4  | Q2.1.d         | (folds into GAP-1)                   | (covered by GAP-1 codex doc — multi-tenancy section: dedicated ensemble per archetype within a VM, sharing position-balance + risk via VM-local IPC; no cross-archetype mixing of strategy state)                                                                                            |
| GAP-5  | Q2.3.c         | `strategy_and_dart_master_2026_05_07.md` Phase 1.9 | `[AGENT] P0. Define ExecutionRejection UAC event (rejection_code closed-set: INSUFFICIENT_LIQUIDITY / RATE_LIMITED / KILL_SWITCH_ARMED / VENUE_DOWN / SLIPPAGE_EXCEEDED) + wire strategy-service consumer for retry-or-alert routing. Done = UAC enum + UTL helper + strategy + alerting consumer.` |
| GAP-6  | Q3.1.b         | `ml_and_features_master_2026_05_07.md` Phase 4D | `[AGENT] P0. Ship strategy-service pytest integration test asserting ml-inference RPC call returns calibrated signal, cost-aware filter drops signals where expected_alpha < execution_cost_bps, AND end-to-end latency < SLA. Test required by Phase 4D acceptance criterion (currently missing).` |
| GAP-7  | Q3.1.c, Q3.2.c, Q3.2.e | `ml_and_features_master_2026_05_07.md` Phase 4D | `[AGENT] P0. Lift model-registry SSOT into UAC: ModelArtifactRegistry (model_id, model_family, asset_group, version, gcs_uri, trained_at). Codify selection logic + paper-snapshot semantics + live hot-reload cadence in codex/04-architecture/ml-lifecycle.md. Done = UAC + codex + ml-inference reads from registry.` |
| GAP-8  | Q3.1.d         | `ml_and_features_master_2026_05_07.md` Phase 4D | `[AGENT] P0. Codify "monolithic ML cluster ships May-23, per-asset-group sharding deferred post-cutover" as explicit decision in codex/04-architecture/ml-lifecycle.md. Done = codex doc landed.` |
| GAP-9  | Q3.2.a         | `ml_and_features_master_2026_05_07.md` Phase 1A | `[AGENT] P0. Pin batch ML inference cadence: per-bar replay (NOT vectorized daily pass) to honor "Batch = Live, only fill source differs" invariant. Acceptance: replay-mode pytest covering 24h of bars, asserting per-bar predict() called once per bar at the bar's available_at.` |
| GAP-10 | Q3.2.b         | `ml_and_features_master_2026_05_07.md` Phase 4D | `[AGENT] P0. Define live ml-inference latency SLA: p99 ≤ 200ms per signal for carry + funding-arb archetypes (sub-second strategies). Enforce via pytest + Grafana alert. Done = SLA documented + alert wired + 7-day live-soak passes.` |
| GAP-11 | Q4.1.d         | `defi_master_2026_05_07.md` Phase ? | `[AGENT] P0. Pin wallet private key custody for live DeFi VM: keys fetched per-request from Secret Manager via ApiKeyReloader pattern, NEVER held in process memory beyond single-request scope. Codify in codex/04-architecture/interface-credential-convention.md (extension). Done = codex + execution-service connector audit + integration test asserts no in-memory persistence.` |
| GAP-12 | Q4.2.c         | `strategy_and_dart_master_2026_05_07.md` Phase 1.9 | `[AGENT] P0. Enumerate matching-engine assumption surface in codex/04-architecture/matching-engine-assumptions.md: per-matcher slippage model + commission schedule + latency model + venue-liquidity proxy. Configurable via UAC MatchingEngineConfig. Required for backtest fidelity per master plan Group F item 18.` |
| GAP-13 | Q5.e           | `master_to_live_defi_2026_05_23.md` Group F | `[AGENT] P0. Define multi-mode wallet isolation: when paper + live run simultaneously on same wallet, position-balance-monitor MUST split exposure tracking by mode. Either (a) separate sub-accounts per mode, OR (b) virtual ledger overlay where paper positions are tracked off-chain. Decision + codex + integration test gate the May-23 carry-live + funding-arb-paper ramp.` |

### Code-finding ISSUE (not a topology Q, but May-23-blocking)

| ISSUE   | Source Q | Issue doc destination                                                                           | Summary                                                                                                                                                                                                                                                                              |
| ------- | -------- | ----------------------------------------------------------------------------------------------- | -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| ISSUE-1 | Q3.2.d   | `plans/active/issues/features_onchain_lookahead_bias_suppression_2026_05_09.md` (to be filed)   | `features-onchain-service/features_onchain_service/app/core/feature_writer.py:125-131` wraps `PointInTimeEnforcer(strict=True)` in `contextlib.suppress(LookaheadBiasError)`. Violates CLAUDE.md "LookaheadBiasError raised loud at every features-* compute." Must fix before May-23 — DeFi archetype features for carry_staked_basis depend on this calculator. |

### Implicit answers folded in

- **Q6.a** (which Qs block May-23) — Invalidated by HARD RULE; **all 30 Qs close by May-23**, no deferrals.
- **Q6.b** (carry vs funding-arb topology split) — ✅ Same execution-service + same matching engine + same ensemble
  shape; differ only in strategy config + feature inputs (per `defi_master`). One DeFi VM hosts both archetypes
  (per GAP-1).
- **Q6.c** (DART placement) — 🟢 IN-FLIGHT. `master_to_live_defi_2026_05_23.md` Group G items 23a-23b (P0, May-23):
  DART = UI-side intercept with manual-confirm dialog pre-execution; backed by `GET /strategy/{id}/runs?mode=` data
  API. NOT alongside strategy/execution.

---

## Disposition

This doc is **active-closing** with hard deadline **2026-05-23**. Resolution path per Q:

- **✅ ANSWERED** Qs require codex SSOT updates only (no code change). Folded into
  [`codex/04-architecture/`](../../codex/04-architecture/) +
  [`codex/05-infrastructure/live-pipeline-architecture.md`](../../codex/05-infrastructure/live-pipeline-architecture.md)
  per the "Post-Plan-Phase Codex Audit" HARD RULE as the relevant phases land.
- **🟢 IN-FLIGHT** Qs close as their cited plan phase ships. No new work needed; verification only.
- **🔴 GAP** Qs (13 total) close via § 6 GAP closure matrix — each has a draft P0 todo + destination plan. Apply
  the draft todos to their destination plans as part of closing this doc.
- **ISSUE-1** (features-onchain LookaheadBiasError suppression) gets a separate issue doc + code fix; not a
  topology Q but May-23-blocking.

This doc archives once: (a) every 🔴 GAP has a corresponding `- [ ]` todo in its destination plan; (b) every
🟢 IN-FLIGHT Q's plan phase has shipped; (c) every ✅ ANSWERED Q has a codex doc reflecting the answer; (d) ISSUE-1
is fixed in code. Until then, status: `active-closing`.
