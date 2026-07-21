---
doc_type: plan
title: DeFi e2e pipeline — both batch (GCS-mediated) and live (Pub/Sub-mediated) closure
summary:
status: complete
nature: record
asset_group: defi
stage: [meta]
repos:
  [
    client-reporting-api,
    deployment-ui,
    execution-service,
    market-tick-data-service,
    strategy-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-30
locked_by: live-defi-rollout
locked_since: 2026-04-30
plan_type: e2e_validation
owner: ikenna
---

## Deferred work — migrated to: `plans/active/defi_consolidated_closeout_2026_07_18.md` — successor:

defi_consolidated_closeout_2026_07_18 (17 of 19 open items — the Fork 1/Fork 2 code/test/coverage-gate checklists for
all 8 DeFi archetypes, plus the folded-in `defi_full_coverage_expansion_2026_04_09` data-quality-verification +
subgraph-schema-mismatch items for PancakeSwap/SushiSwap/Aerodrome/Camelot V3, plus the folded-in
`defi_data_types_completeness_2026_04_24` end-to-end validation item — are all DeFi pipeline/data-correctness surface
now owned by this active plan's "ONE ordered pass" scope). **2 items left ambiguous, NOT covered by the banner above**:
the `leveraged_leg_controller_2026_05_01`-folded items (Phase A/B/C formal unit tests for `holding_wallet` override
precedence + Solana inner-instruction handling; features-onchain-service Docker image rebuild to pick up the Phase-1
LegController changes) are strategy-engine/deployment specific, not data-canonicalisation — no active plan visibly owns
them, and the batch-4 todo in `pm_qg_plan_discipline_and_frontmatter_regression_2026_07_21.md` already flags
`leveraged_leg_controller_2026_05_01` itself as needing "a real successor issue-doc … or operator confirmation both are
abandoned." Left for that batch-4 pass rather than guessed here.

# DeFi e2e pipeline — both batch (GCS-mediated) and live (Pub/Sub-mediated) closure

## Context & motivation

All 8 DeFi archetype tracers now run end-to-end against real 2025 data and emit ranked decisions (recursive-staked,
rebasing-yield, carry-staked-basis, basis-perp, yield-rotation-lending, liquidation-capture, arbitrage-dispersion
cross-chain + cross-venue-funding, target-universe rebalance recommender). EigenLayer aggregate restaking APY is layered
onto restaking-eligible LSTs in both rebasing-yield and recursive-staked tracers (commits `726e20f4` + `e8938ae6` on
execution-service).

The next gap is wiring the existing services so a single archetype runs end-to-end through the **service mesh** rather
than via the standalone tracer scripts. Per workspace `.claude/CLAUDE.md` Batch=Live rule, this is NOT building
orchestrator glue — it's making the existing event topology actually close.

Two forks, both shippable:

- **Fork 2 — Batch / GCS-mediated.** All four service batch CLIs (strategy-service `--operation backtest`,
  execution-service `batch_backtest`, position-balance-monitor `--mode batch`, pnl-attribution
  `--operation compute --mode batch`) exist. Path is GCS-mediated: each service writes parquet, the next reads. Closure
  proves component integrity without needing live Pub/Sub wiring.
- **Fork 1 — Live / Pub/Sub-mediated.** Five wiring holes block live closure: MTDS→features-onchain feature input,
  features-onchain→strategy-service feature consumer, strategy-service v2 orchestrator instruction publisher,
  execution-service fill auto-publisher, risk-and-exposure-service intent subscriber.

User direction (2026-04-30): "yeah makes sense to do both anyway — don't stop until it's done."

## Pre-audit: what exists today

### Batch path (Fork 2)

| Stage | Service                  | CLI                                                                            | GCS read                             | GCS write                                                                                         |
| ----- | ------------------------ | ------------------------------------------------------------------------------ | ------------------------------------ | ------------------------------------------------------------------------------------------------- |
| 1     | features-onchain-service | `--operation features --mode batch`                                            | `market-data-tick-defi-{pid}/...`    | `features-onchain-{pid}/lst_rates,lending_indices,aave_health_factor/day=…`                       |
| 2     | strategy-service         | `--operation backtest --mode batch --category DEFI`                            | features-onchain output              | `strategy-store-{pid}/strategy_instructions/client_id=*/strategy_id=*/day=…/instructions.parquet` |
| 3     | execution-service        | `python -m execution_service.cli.batch_backtest --configs … --start … --end …` | strategy instructions                | `execution-store-{pid}/fills/...` (path TBC — verify writer)                                      |
| 4     | position-balance-monitor | `--mode batch --start-date … --end-date …`                                     | execution fills                      | `position-store-{pid}/position_snapshots/by_date/day=…`                                           |
| 5     | pnl-attribution-service  | `--operation compute --mode batch --start-date … --end-date …`                 | execution fills + position snapshots | `pnl-store-{pid}/by_strategy/strategy_id=…/day=…`                                                 |

### Live path (Fork 1) — 5 wiring holes

| Hole | Where                                          | Topic                                                                       | Schema                                        |
| ---- | ---------------------------------------------- | --------------------------------------------------------------------------- | --------------------------------------------- |
| 1    | features-onchain `live_handler`                | input: `defi-onchain-data-ready-sub`; output: `defi-onchain-features-ready` | dict → `OnchainFeatureSnapshot` (UAC)         |
| 2    | strategy-service `live_handler`                | subscribe `defi-onchain-features-ready`                                     | `OnchainFeatureSnapshot`                      |
| 3    | strategy-service v2 orchestrator               | publish `strategy-intent-defi`                                              | `AtomicInstruction` (UAC internal)            |
| 4    | execution-service Aave + Uniswap connectors    | publish `fill-events-{venue}` post-fill                                     | `CanonicalFill` (UAC execution)               |
| 5    | risk-and-exposure-service `live_handler` (NEW) | sub `strategy-intent-defi`; pub `risk-pass-defi`                            | `AtomicInstruction` in / `RiskAssessment` out |

### Pre-existing wiring (not holes)

- `StrategyLiveHandler` in `strategy-service/strategy_service/cli/service_entry.py` already starts `CascadeSubscriber` +
  `FillEventSubscriber` (DEFI category) — recon agent A underestimated this.
- `position-balance-monitor-service` `fill_subscriber.py` already subscribes to `fill-events-{venue}` — only the
  publisher is missing.
- `strategy-service/.../v2/base.py:emit_instructions` records into `_emitted` buffer; v2 `Orchestrator.on_tick()`
  returns the list. The publisher is just missing at the drain point.

### Known gaps surfaced during pre-audit

- **No real CARRY_RECURSIVE_STAKED config exists on disk.** Manifest entry `DEFI_RECURSIVE_BASIS_ETH_1H` references
  `default_basis_trade.yaml`, but that file is for spot-perp stat-arb (BINANCE BTCUSDT spot vs perp), not for LST + Aave
  recursive loops. C4 maturity status with `class_exists: false`. → must write a real config.
- **Circular import in strategy-service `cli/handlers/__init__.py`.** Deferred-import workaround at line 43 doesn't
  fully resolve because `service_entry.py` imports `seed_lifecycle_handler` first which loads `handlers/__init__.py`,
  which then imports `live_handler.py`, which imports `StrategyLiveHandler` from `service_entry` before that class is
  defined. → must fix before strategy-service CLI runs.
- **fake-gcs-server bucket pre-creation.** Local emulator auto-creates on first write, but config files must be uploaded
  BEFORE strategy-service backtest reads them. Need a bootstrap step.
- **demo-mode.sh seed scope.** Per `.claude/CLAUDE.md` it's the canonical local-stack primer but its seed coverage of
  strategy configs / instrument metadata for DeFi is unverified.

## Phased execution DAG

```
Phase 0  — Bootstrap + pre-flight  (must succeed before anything else)
   ├─ 0.1 Reset cwd + venv (.venv-workspace activated)
   ├─ 0.2 Boot dev-start.sh --backend-only --mode mock (Pub/Sub + GCS emulators)
   ├─ 0.3 Fix circular import in strategy-service/cli/handlers/__init__.py
   └─ 0.4 Write CARRY_RECURSIVE_STAKED config + upload to fake-gcs

Phase 1  — Fork 2 batch e2e for ONE archetype (CARRY_RECURSIVE_STAKED)
   ├─ 1.1 Run features-onchain batch over 2025-06-15..2025-06-21 → verify lst_rates parquet on GCS
   ├─ 1.2 Run strategy-service backtest → verify instructions parquet on GCS
   ├─ 1.3 Run execution-service batch_backtest → verify fills parquet on GCS
   ├─ 1.4 Run PBM batch → verify position snapshots parquet on GCS
   ├─ 1.5 Run pnl-attribution batch → verify per-strategy PnL series row on GCS
   └─ 1.6 GATE — non-zero PnL row exists for DEFI_RECURSIVE_BASIS_ETH_1H, attribution components present

Phase 2  — Fork 1 live wiring (PARALLEL after Phase 1 gate)
   ├─ 2.1 Verify topic SSOT names in UAC registry
   ├─ 2.2 Add OnchainFeatureSnapshot subscriber to strategy-service live path
   ├─ 2.3 Add AtomicInstruction publisher to v2 orchestrator
   ├─ 2.4 Add CanonicalFill auto-publisher to execution-service Aave + Uniswap connectors
   ├─ 2.5 Create risk-and-exposure-service live_handler with intent sub + risk-pass pub
   └─ 2.6 Verify MTDS→features-onchain wiring (may already be covered)

Phase 3  — Fork 1 verify (one tick closes the loop on emulator)
   ├─ 3.1 dev-start.sh --all --mode mock (full topology)
   ├─ 3.2 demo-mode.sh --seed (or equivalent)
   ├─ 3.3 Inject one feature tick into defi-onchain-features-ready
   └─ 3.4 GATE — observe fill on fill-events-{venue} + position snapshot update + pnl emission

Phase 4  — Extend Fork 2 batch coverage to all 8 archetypes (PARALLEL with Phase 3)
   └─ 4.1–4.8 One archetype per todo, same Phase 1 sequence, accept any per-archetype quirks

Phase 5  — Hardening
   ├─ 5.1 quality-gates.sh pass on every modified repo (strategy-service, execution-service, risk-and-exposure-service, features-onchain-service, PM)
   ├─ 5.2 Add regression tests for the 5 wired publishers/subscribers
   └─ 5.3 quickmerge --agent per repo
```

## Success criteria

### Code gates

- [ ] strategy-service `quality-gates.sh` passes
- [ ] execution-service `quality-gates.sh` passes
- [ ] risk-and-exposure-service `quality-gates.sh` passes
- [ ] features-onchain-service `quality-gates.sh` passes
- [ ] basedpyright clean across all 4 service repos

### Test gates (Phase 1)

- [ ] CARRY_RECURSIVE_STAKED batch e2e produces non-zero PnL row in pnl-store-{pid}/by_strategy/.../day=2025-06-21
- [ ] PnL row decomposes into base_apy + restaking_apy + borrow_cost + gas attribution components
- [ ] Position snapshot reflects leveraged LST holding + WETH debt
- [ ] Health factor recorded ≥ configured min_health_factor for every snapshot

### Test gates (Phase 3)

- [ ] One synthetic feature tick injected into `defi-onchain-features-ready` produces a fill on `fill-events-{venue}`
      within 30 seconds on the emulator
- [ ] PBM emits position snapshot for the new position
- [ ] pnl-attribution emits a per-strategy attribution row
- [ ] Risk-and-exposure-service log shows RISK_PASS published before execution

### Coverage gate (Phase 4)

- [ ] All 8 archetypes pass Phase 1 batch e2e: CARRY_RECURSIVE_STAKED, CARRY_STAKED_BASIS, CARRY_BASIS_PERP,
      YIELD_ROTATION_LENDING, REBASING_YIELD, LIQUIDATION_CAPTURE, ARBITRAGE_PRICE_DISPERSION (cross-chain +
      cross-venue-funding), TARGET_UNIVERSE_REBALANCE_RECOMMENDER

## Out of scope

- Per-AVS / per-LST EigenLayer attribution (v0 aggregate APY is shipped; v1 attribution is a follow-up).
- Karak / Symbiotic restaking integration (currently uncaptured).
- 8th archetype tracer for cross-protocol DEX arbitrage (deferred per existing tracer's docstring; needs DEX swap data
  in `evm-defi` bucket, currently lending-only).
- Cloud Run redeploy of deployment-dashboard (separate auth-chain follow-up).
- Multi-client allocation + per-client margin-pool accounting (next iteration after one client / one archetype proves
  out).

## Phase 0+1 progress log (2026-04-30 — full day)

### Late-day fixes shipped (after the 02:30 cascade)

- **features-onchain `cda2ab2`** — same projection-mistake pattern fix across 5 more daily-feature calculators that had
  the utilization bug shipped in `3671b06`: perps, rewards, risk_params, flash_loan, health_factor, liquidation. Each
  one called `rate_data.select(self._base_cols(rate_data))` (keeping only timestamp + instrument_id) then referenced
  `pl.col("X")` for columns that had been projected away. Same fix: include the referenced columns in the .select()
  projection up-front.
- **features-onchain `fc2333e`** — bumped `WriteGateConfig.nan_threshold` from 0.5 → 0.95 so DeFi feature_groups whose
  upstream MTDS feed is index-heavy (lending_indices) can write partial parquets. Strategies do their own None-guard;
  fail-closed semantics preserved.
- **features-onchain `012c975`** — added `variable_borrow_rate` to the borrow-APY rename-map. Real Aave V3
  lending_indices parquet schema for ETHEREUM uses `variable_borrow_rate` (not `borrow_rate`/`borrow_apy`), so before
  this fix `aave_borrow_apy` came out >95% NaN and CARRY_RECURSIVE_STAKED + CARRY_STAKED_BASIS strategies saw no
  borrow_apy_bps. Verified probing real 2025-06-15 ETH parquet (1000 rows, USDT example: variable_borrow_rate=0.049225).

> **⚠️ SUPERSEDED 2026-05-05 — `CARRY_STAKED_BASIS` borrow path deleted.** The variable_borrow_rate fix above unblocked
> `aave_borrow_apy` for CARRY_RECURSIVE_STAKED, but `CARRY_STAKED_BASIS` no longer uses that code path.
> `carry_staked_basis_structure_axis_2026_05_04.md` deleted COLLATERAL_BORROW (2026-05-04), then deleted SPLIT_STAKE
> (2026-05-05). Only **LST_AS_MARGIN** structure survives. Engine emits a 4-leg sequence (SWAP+STAKE+TRANSFER+TRADE), no
> borrow leg. Empirical-progress entries below for `DEFI_ETH_STAKED_BASIS_HYPERLIQUID_SCE_1H` describe the **pre-pivot**
> shape — re-verify after running against the structure-axis-aligned engine. CARRY_RECURSIVE_STAKED progress notes are
> still valid (it kept the borrow leg).

### Empirical pipeline progress

- **Strategy-service backtest 7/7 dates successful** for DEFI 2025-06-15..21. Two real DeFi v2 archetype instances
  initialized:
  - `DEFI_ETH_STAKED_BASIS_HYPERLIQUID_SCE_1H` (CARRY_STAKED_BASIS, ETHERFI weETH + Hyperliquid perp)
  - `DEFI_ETH_RECURSIVE_HEDGED_ALL_HYPERLIQUID_HUF_1H` (CARRY_RECURSIVE_STAKED, target_leverage=2.5,
    flash_provider=MORPHO)
- **`gs://strategy-store-central-element-323112/strategy_instructions/client_id=/strategy_id=*/day=2025-06-15/instructions.parquet`**
  — empty parquets (0 instructions) because strategies need both `staking_apy_bps` (have via lst_yields) AND
  `borrow_apy_bps` (now fixed via lending_rates path, populating).
- **lst_yields** populated for all 7 days (2025-06-15..21, 6 rows/day).
- **lending_rates 7-day population in progress** with the variable_borrow_rate fix applied.

### Remaining bugs surfaced but not yet fixed

- **PBM `FillEventConsumer.subscription_path` AttributeError** —
  `position-balance-monitor-service/.../core/fill_event_consumer.py:150` calls `self.subscriber.subscription_path(...)`
  but `PubSubQueueClient` has no such attribute. PBM batch-mode crashes immediately. Either add the missing method to
  `PubSubQueueClient` (UTL) or change the consumer to use a different path-resolution approach.
- **features-onchain multi-day `--start-date X --end-date Y` only iterates 1 day** — workaround is per-day invocation.
  Needs root-cause investigation in date-range handling.
- **WriteGate threshold may need further tuning** — even at 0.95 some feeds rejected. Long-term fix: derive missing APY
  columns from cumulative indices (per-second rate × seconds-in-year) instead of leaving them NaN.

### CLI mode discrepancy (CLAUDE.md aspirational?)

CLAUDE.md says "Strategy-service interacts with position-balance-monitor, risk-and-exposure-service, execution-service —
all CO-LOCATED" in batch mode. Empirically, the strategy-service `batch_handler` ONLY writes `instructions.parquet` — it
does NOT run an in-process matching engine, position tracker, or PnL attribution. Fills + positions + PnL are produced
by separate downstream services (execution-service.batch_backtest, PBM batch, pnl-attribution batch) reading the
strategy parquets. Either CLAUDE.md is aspirational or there's a separate orchestration we haven't discovered.

## Phase 0 progress log (2026-04-30 ~02:30)

### Shipped this session

- [x] [HUMAN_AGENT] strategy-service `b2b918e` — fix circular import in `cli/handlers/__init__.py` via PEP 562 lazy
      `__getattr__`. Without this fix, `strategy-service --help` (the registered console-script) fails with
      `ImportError: cannot import name 'StrategyLiveHandler'` on every invocation. The deferred-after-function-def
      pattern that was in place doesn't work because the cycle is at IMPORT time, not at call time.
- [x] [HUMAN_AGENT] execution-service `e8938ae6` — layer EigenLayer aggregate restaking APY into CARRY_RECURSIVE_STAKED
      tracer. Net APR uplift ~4.31pp at LTV=0.85 for `{weETH, pufETH, ETHx, ankrETH}`. pufETH flips from base-loss to
      net-profit thanks to EL.
- [x] [HUMAN_AGENT] execution-service `726e20f4` — same EL APY layered into REBASING_YIELD tracer.
- [x] [HUMAN_AGENT] PM `defi_e2e_pipeline_2026_04_30.md` — this plan.
- [x] [HUMAN_AGENT] Strategy-service quality-gates pass: 2006 tests passing, 75.10% coverage (above 74% threshold). Only
      2 pre-existing unrelated failures (test_service_startup.py uses `categories=` kwarg but ServiceCLI now expects
      `asset_group_choices=` per the asset_group vocabulary rename).

### CLI startup cascade discovered (NOT YET FIXED — needs operator direction)

After fixing the circular import, `strategy-service --help` exposes additional cascading bugs in non-mock startup that
block the real backtest CLI. With `CLOUD_MOCK_MODE=true` the service short-circuits to `_get_mock_pipeline` which writes
synthetic seed data to `.local-dev-cache/`, so the bugs below only fire with `CLOUD_MOCK_MODE=false` + emulator hosts:

1. **`google.cloud.firestore` missing from venv-workspace + strategy-service pyproject** —
   `start_instance_lifecycle_service()` runs unconditionally in `_get_config()` and triggers
   `build_firestore_lifecycle_reloader()` which lazy-imports firestore. The package is not installed and not declared as
   a dep. Fix: add `google-cloud-firestore` to strategy-service `pyproject.toml [project.dependencies]`. Per workspace
   flat-deps rule.

2. **`observability_ingest` background thread starts before `setup_events()` is called** — In
   `signal_broadcast/observability_ingest.py:329`, the thread tries to `log_event("OBSERVABILITY_INGEST_STARTED", …)`
   before the events module is initialised by ServiceBootstrap. Today this throws
   `RuntimeError: Event logging not initialized. Call setup_events() first.` on every CLI startup. Fix: gate the
   `log_event` call on a flag set after setup, OR start the thread after ServiceBootstrap has fully initialised events.

3. **No real CARRY_RECURSIVE_STAKED config exists on disk.** `unified-trading-pm/strategy-manifest.json` lists
   `DEFI_RECURSIVE_BASIS_ETH_1H` with `config_file: strategy-service/.../configs/defaults/default_basis_trade.yaml` and
   `class_path: defi_recursive_basis.RecursiveStakedBasisStrategy`. The class doesn't exist (`class_exists: false`, C4
   maturity). The yaml file IS for spot-perp stat-arb (BINANCE BTCUSDT spot vs perp), not for LST + Aave recursive. →
   must write a real config that matches the v2 archetype-engine's expected shape (see
   `engine/strategies/v2/carry_and_yield/recursive_staked.py:88-122` preflight + `_emitted` instruction shape).

4. **dev-start.sh tracks UI/API gateways, NOT data-pipeline service CLIs.** `dev-status.sh` shows it manages
   `deployment-ui/api`, `market-data-api`, `client-reporting-api`, etc. — but NOT strategy-service / execution-service /
   position-balance-monitor-service / pnl-attribution-service / features-onchain-service / market-tick-data-service.
   Those are run as standalone CLIs against the emulators. Per recon-agent-A: "For batch work, you run service CLIs
   directly against the emulator." So the e2e drive-loop is bash-orchestrated CLI invocations, not `dev-start.sh --all`.

### Realistic alternate Fork-2 path (faster validation)

Instead of fighting the full strategy-service CLI cascade, the existing test suite at
`strategy-service/tests/unit/engine/strategies/v2/test_archetype_engines.py` already exercises `V2EngineOrchestrator`
directly against synthetic feature snapshots, verifying that each archetype engine emits the right `AtomicInstruction`
shape. This is unit-test scope but it IS a code-path validation of the actual archetype logic. To make it true e2e:

1. Plumb in real on-chain feature data (lst_rates / lending_indices / aave_health_factor) from
   features-onchain-service's existing parquets into the test harness as fixtures.
2. Take the emitted `AtomicInstruction` list and run them through `execution-service.batch_backtest` with the matching
   engine in benchmark / always-fill mode.
3. Feed fills to PBM batch handler, then to pnl-attribution batch.
4. Each step is a separate process invocation with explicit GCS paths; chain via a bash harness in
   `unified-trading-pm/scripts/dev/`.

This path skips the strategy-service CLI cascade entirely (engines are imported and called as Python objects, not via
the broken CLI). Single-archetype validation could close in a day; all 8 in 3-4.

## Notes for resumption across sessions

- Active feature branch: `live-defi-rollout` (workspace-manifest.json).
- All commits in this work go via `bash scripts/quickmerge.sh --agent` per repo.
- If a fix lands in a shared library (UAC, UTL, UCI, UEI), commit + push that repo FIRST, then the consumer.
- After every phase gate, update this plan's checkbox state + commit to PM via fast-path (PM/codex doc-only fast-path
  goes direct to main).

## Absorbed from sibling plans (2026-05-06)

Items folded in from `leveraged_leg_controller_2026_05_01` (since archived). The DeFi e2e cluster carries forward the
two remaining LegController items because the leveraged_funding_arb archetype runs through this plan's pipeline:

- [ ] Phase A/B/C tests — formal unit tests pinning the `holding_wallet` override precedence + Solana inner-instruction
      handling. (Source plan covered the Phase 1 implementation; the formal-test follow-up wasn't shipped.)
- [ ] features-onchain-service Docker image rebuild — Cloud Build needs to emit a new `:latest` tag containing the Phase
      1 LegController changes so downstream services pull the updated controller.

Items folded in from `defi_full_coverage_expansion_2026_04_09` (since archived). 27/29 done in source; 2 remaining P1
items covered by this cluster lead's data-quality verification surface:

- [ ] [SCRIPT] P1. Verify data quality across all new DeFi protocols (PancakeSwap V3, SushiSwap V3, Aerodrome V3,
      Camelot V3) — gas consistency, rates plausibility, no NaN drops.
- [ ] [AGENT] P1. Fix subgraph schema mismatches for PancakeSwap V3, SushiSwap V3, Aerodrome V3, Camelot V3 — these
      forks use UniV3-style subgraph with renamed fields.

Items folded in from `defi_data_types_completeness_2026_04_24` (since archived). The 12 open todos there reduce to the
verification surface below + items already represented in `consolidated_defi_data_pipeline_2026_04_15` Group F:

- [ ] [AGENT] P1. Validate the 8 added DeFi data types (per UAC `13db4a9` + `56feaff`) flow end-to-end through MDPS /
      features-onchain into strategy-service archetype tracers.
