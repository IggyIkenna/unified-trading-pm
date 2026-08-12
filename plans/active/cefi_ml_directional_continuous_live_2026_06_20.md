---
doc_type: plan
title: CeFi ML_DIRECTIONAL_CONTINUOUS — live archetype end-to-end (OKX + Binance + Bybit)
summary:
  "Ship the live CeFi ML_DIRECTIONAL_CONTINUOUS archetype across OKX, Binance, and Bybit: live tick to live ML inference
  to live strategy to live execution."
status: active
nature: process
asset_group:
  [cefi] # corrected 2026-08-08 (ag-closeout-audit cefi, Phase 0.3 orthogonality check) -- was [cefi, defi], a mistag:
  # doc's own provenance note says "Distinct from the rules-based DeFi carry family" and scope is 100% CeFi
  # (OKX/Binance/Bybit live trading, parent_epic:cefi_master), zero DeFi content anywhere. The dual tag made this doc
  # invisible to both cefi's and defi's own tranche audits (each excludes docs carrying a peer-AG marker per
  # SKILL.md's Orthogonality HARD CHECK) -- the exact falls-through-both-audits failure class that check exists to
  # catch.
stage: [meta]
repos: [alerting-service, execution-service, features-service, ml-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [cefi, ml, directional, live-trading, okx, binance, bybit, execution]
related:
  [
    ../epics/cefi_master.md,
    ../archive/2026_07/master_to_live_defi_2026_05_23.md,
    ../archive/2026_05/trading_agent_service_architecture_unlock_2026_05_22.md,
  ]
created: "2026-06-12"
parent_epic: cefi_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 12
last_updated: 2026-06-27
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
drift_direction: advance-code
context_scope:
  [
    /plans/epics/cefi_master.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    strategy-service/scripts/run_2yr_config_grid_backtest.py,
    strategy-service/strategy_service/engine/strategies/v2/factory.py,
    /plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
  ]
---

> **Provenance**: extracted 2026-06-20 from the `cefi_master` epic body (formerly the folded
> `cefi_ml_may_23_2026.epic`). This is the second live CeFi archetype — a continuous ML directional prediction signal
> traded on real capital across OKX + Binance + Bybit. Distinct from the rules-based DeFi carry family. The design
> decisions below are LOCKED (resolved 2026-05-08, `operator_decisions_2026_05_08.plan.md`); the open work is shipping
> the live loop. Shares ML-lifecycle infrastructure with `sp_prediction` / `sports_ml` / `prediction_markets` — do not
> rebuild those primitives here.

## Locked design (resolved 2026-05-08 — do not re-litigate)

- **Archetype**: `ML_DIRECTIONAL_CONTINUOUS` — continuous directional prediction signal. Wires through
  `mlr-p4-strategy-calibrated-signals` + `mlr-p4-cost-aware-strategy` + live model registry.
- **Venues**: OKX + Binance + Bybit (deepest liquidity, lowest unit cost; Deribit deferred post-cutover).
- **Retraining**: daily overnight retrain via ml-training (UTC midnight + 30min tick-settlement buffer); ml-inference
  hot-reloads next day-open. Feature staleness budget 24h hard / 6h soft.
- **Capital**: $10k notional per venue ($30k total). `position_cap_usd = 10000`/venue; `kill_switch_drawdown_pct = 5`;
  `kill_switch_position_breach_pct = 20`; `kill_switch_scope = ARCHETYPE` (a CeFi-ML trip does NOT halt DeFi). Ramp
  2×/week absent trips, capped $250k by post-cutover review.

## P0 — live ML loop

- [x] ✅ [AGENT] P0. End-to-end ML pipeline live: live tick data → live features → live model inference → live strategy
      decision → live execution → live position + risk + P&L attribution, across OKX + Binance + Bybit. —
      strategy-service@5dd062bf | `_build_predictions_from_cascade()` bridges `CascadeSignalAggregator.get_latest()` →
      `list[MLPrediction]` with direction mapping (-1→2, 0→0, 1→1); `_generate_signals_from_candles_v2()` now passes
      cascade predictions to `V2BatchHarness.on_tick()` → `V2EngineOrchestrator` → `MLDirectionalContinuousEngine`
      (which consumes `predictions: list[MLPrediction]`, discards features entirely). 8 unit tests
      (`tests/unit/cli/handlers/test_batch_signals.py`). Batch=live code path complete; live execution gate (wallet keys
      for OKX/Binance/Bybit) is BLOCKED-OPERATOR and tracked in task -002.
- [x] ✅ [AGENT] P1. Infrastructure readiness: add `ML_DIRECTIONAL_CONTINUOUS` to `credentials_per_archetype.yaml` in
      UAC (currently absent — only DeFi archetypes declared); add `bybit_secret_name` field to
      `execution-service/service_config.py` (Deribit+Binance+Hyperliquid have named SM secret fields, Bybit does not);
      fix `live_execution_handler._create_orchestrator_for_venue()` to load OKX/Binance/Bybit credentials from Secret
      Manager before calling `get_order_adapter()` (currently called with `api_key=None` → raises ValueError in real
      mode). OKX is per-client (`exec-<client>-okx-*`); Bybit is single unscoped key
      (`bybit_api_key`/`bybit_api_secret`); Binance is `binance-trade-api-key`/`binance-trade-api-key-secret`. Blocked
      on operator provisioning SM secrets first (see CREDENTIAL APPROVAL REQUEST in slot_6.md, BLK-e64b661a). —
      unified-api-contracts@6d3d900c (credentials_per_archetype.yaml: ML_DIRECTIONAL_CONTINUOUS added with
      Bybit+Binance+OKX credential set) execution-service@b46f43e8 (bybit_secret_name + okx_secret_name fields added to
      service_config.py; \_create_orchestrator_for_venue() now loads api_key/api_secret from SM via
      load_credentials_from_secret_manager per venue map; no-credentials ValueError eliminated). QG green on both repos.
- [ ] [AGENT] P0. Continuous ML prediction signal live on real capital across OKX + Binance + Bybit for ≥7 continuous
      days (the cutover gate).
  > **GATED 2026-06-12 (slot-2, BLK-4badaa3c)**: Re-queued with explicit dependency on task -001 (end-to-end ML
  > pipeline) completing first. Hard-stops per plan (wallet keys for OKX/Binance/Bybit, live-trading kill-switch arming)
  > require operator action before this gate can be verified. Operator flagged: wallet keys needed. **GATED 2026-06-16
  > (slot-6, BLK-e64b661a)**: Infrastructure audit complete. Additional agent-doable gaps found (see P1 todo above).
  > Operator hard-stops confirmed: SM secrets not yet provisioned for OKX/Bybit; kill-switch arming pending. See
  > slot_6.md CREDENTIAL APPROVAL REQUEST for exact SM secret names needed.
- [x] ✅ [AGENT] P0. Live model lifecycle: hot-reload of model artefacts without service restart; per-trade
      `model_version` traceability; model-drift alerting. — Hot-reload: ModelPromotionSubscriber already wired
      (ml-service@live). Per-trade model*version: PredictionEventDict.swing*{high,low}\_model_version flows through
      InferenceRequest→PredictionEvent→publish. Model-drift alerting: PredictionOutcomeSubscriber wired (subscribes to
      ml_prediction_outcomes, feeds DriftMonitor.record_outcome + check_retune; models pre-registered from
      timeframe_specific_models on live start). InferenceConfig:
      drift_auto_retune_enabled/baseline_accuracy/drop_threshold/window_days. ml-service landed 2026-06-12.
- [x] ✅ [AGENT] P0. Live alerting active: signal-staleness (`ML_SIGNAL_STALENESS` warns 4h / critical 12h / kill-switch
      24h) + execution-quality + P&L deviation + position breaches. — alerting-service@090b622 |
      `cefi_ml_event_handler.py`: 3-tier ML_SIGNAL_STALENESS ladder
      (4h=WARN/12h=CRITICAL+PagerDuty+Telegram/24h=KILL_SWITCH_ML_MODEL_FAILURE) + PASSTHROUGH set covers
      ML_PNL_DEVIATION/ORDER_REJECTION_SPIKE/POSITION_CRITICAL_DISCREPANCY/POSITION_DRIFT_DETECTED; wired at
      `alert_subscriber.py:278`; 18 unit tests. Kill-switch at 24h via
      CircuitBreakerId.ML_SIGNAL_STALENESS_SECONDS=86400s (uac@547cba3). Fix: alerting-service@9de040b archetype-aware
      `_breaker_action_for` resolves DRAWDOWN_DAILY_BPS KILL_ALL/SCALE_DOWN cross-archetype conflict. QG green (284s).
      alerting-service landed 2026-06-12.
- [x] ✅ [AGENT] P0. Kill switches + circuit breakers wired per the locked params above (position-limit, P&L drawdown,
      signal-staleness, model-drift), `kill_switch_scope=ARCHETYPE`. — unified-api-contracts@547cba3 | 4 breakers
      (POSITION_LIMIT_EXCEEDED/DRAWDOWN_DAILY_BPS/ML_SIGNAL_STALENESS_SECONDS/ML_MODEL_DRIFT_ACCURACY_DROP) +
      KILL_PER_ARCHETYPE_ML_DIRECTIONAL_CONTINUOUS + 7 new taxonomy tests; QG green.
- [x] ✅ [AGENT] P0. DART manual override: operator can pause / override / replicate any ML-driven trade. —
      strategy-service@7995e4e4 | ArchetypeModeStore extracted to engine/strategies/v2/mode_store.py;
      V2EngineOrchestrator.\_tick_one_engine wired with per-archetype MANUAL mode gate (suppress automated instructions
      when operator explicitly sets mode=MANUAL via POST /api/archetypes/{id}/operational-mode); override+replicate via
      existing execution-service /manual/submit + DART UI ManualTradingPanel. 5 new tests (manual suppress, live/paper
      forward, cross-archetype isolation, unregistered pass-through). QG green.
- [ ] [VERIFY] P0. Backtest fidelity for the same signal proven via the 2-year batch backtest config grid (master plan
      Group F item 18) — batch = live, same code path, no standalone backtest engine. **CORRECTED 2026-07-14
      (doc-reconciliation verify-rerun-2, finding 36): flipped `[x]`→`[ ]` — the nested detail immediately below and the
      Success criteria section (further down this doc) both admit the 2-year config-grid run has NOT been executed; only
      the architecture-verification half of this gate is actually done.** (was: `- [x]`)

  > **Partial PASS — architecture verified; grid run pending operator scheduling (2026-06-12, slot-6)**:
  >
  > - ✅ **batch=live, same code path, no standalone engine**: `ML_DIRECTIONAL_CONTINUOUS` is wired in
  >   `strategy_service/engine/strategies/v2/factory.py` → `MLDirectionalContinuousEngine`; dispatches through
  >   `GroupBRunner` + `V2BatchHarness` → `V2EngineOrchestrator` (same orchestrator as live mode).
  >   `tests/unit/engine/backtest/test_runner.py::test_runner_produces_deterministic_pnl_for_ml_directional` PASSES (4/4
  >   tests, 6.7s): batch=live reproducibility invariant confirmed (same tick stream → identical fills).
  > - ⚠️ **2-year config-grid run partially complete — script extended, VM run still pending**: ✅ **(1) script
  >   extended** — `run_2yr_config_grid_backtest.py` now includes `ML_DIRECTIONAL_CONTINUOUS` in `SUPPORTED_ARCHETYPES`
  >   with dimension tables (position_size_pct / confidence_threshold / stop_loss_bps / take_profit_bps / model_family)
  >   and branch coverage at every per-archetype dispatch point; unit test proves the new archetype accepted
  >   (strategy-service @dff5b2c0, verified on origin/live-defi-rollout 2026-08-07,
  >   `cefi_satellite_ao_dispatch_batch6_2026_08_02_finalize.md` todo 1). Remaining: **(2) operator-scheduled VM run
  >   (~8-12h, same shape as DeFi grid runs)**; **(3) GCS parquet output inspection** — no GCS output at
  >   `strategy-store-*/backtest_results/strategy_id=ML_DIRECTIONAL_CONTINUOUS/` yet. This grid run is an operator-only
  >   scheduling action per the "Plans Run To Actual Completion" HARD RULE.

  > **RULED (operator, 2026-08-08)**: schedule the grid run, BUT gated on first verifying features/MTDS/MDPS data is
  > actually available for OKX+Binance+Bybit across the real 2-year window (`run_2yr_config_grid_backtest.py`'s own
  > example invocation uses `--start 2024-01-01 --end 2026-05-01`, i.e. the window is ~2024-01-01→present).
  > **Investigated 2026-08-08 (na-corpus-digest-closeout, grep-based against manifest/honest-coverage state — no new
  > full-corpus GCS walk run)**: coverage is **NOT CONFIRMED for this window** — do not schedule yet.
  >
  > - The only honest-coverage number on record is an **aggregate over the FULL registered CeFi history** (back to
  >   ~2019-2020), not scoped to 2024-2026: **44.96%** pre-backfill baseline (2026-07-27,
  >   `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md`), reopening the previously-archived **50.79%**
  >   "honest-done" verdict (`plans/archive/2026_07/cefi_completion_program_2026_07_15.md`) — both numbers span every
  >   MVP CeFi venue (OKX-SPOT/-SWAP/-FUTURES, BINANCE-SPOT/-FUTURES, BYBIT included) combined, not broken out per venue
  >   or per date-window.
  > - The mechanism that would produce a **fresh, confirmed** number — the POST-BACKFILL `/data-pipeline-check-mtds`
  >   gate in `cefi_track2_coverage_backfill_checkpoints_2026_07_25.md` (todos -004/-005) — is **still blocked** as of
  >   2026-08-08: the chronological historical backfill it's gated on has failed/preempted **7 times across 12 days**
  >   (2026-07-27→08-06) and is currently at only `last_completed_date=2019-10-21` of a `2019-01-01..2026-08-01` target
  >   span (~10.7% through), per that plan's own Progress Log. That backfill works chronologically from **2019 forward**
  >   — it has not yet reached anywhere near 2024, so its completion (or lack thereof) says nothing directly about
  >   whether 2024-2026 specifically is captured; it just means **no fresh aggregate re-measurement exists yet either
  >   way**.
  > - The one existing single-day snapshot inside the window (`data_pipeline_e2e_check_mtds_2026_03_15.md`, run
  >   2026-03-15) shows BINANCE-SPOT/BINANCE-FUTURES/BYBIT `trades`/`book_snapshot_5` all `failed` — but that failure is
  >   **root-caused to a launcher/guard bug**
  >   (`issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28.md`, "not a data-correctness
  >   regression"), so it is **not usable evidence** either way about the underlying capture state for that date.
  > - **Conclusion: coverage for the required 2024-01-01→present / OKX+Binance+Bybit window is neither confirmed present
  >   nor confirmed absent** — no window-scoped measurement exists. Per the operator's own gating condition ("only
  >   schedule once coverage is confirmed"), **the grid run stays NOT schedulable.** Filed the specific prerequisite as
  >   a new todo below (a narrow, window-scoped honest-coverage check — NOT contingent on the unrelated full 2019-2026
  >   chronological backfill finishing).

- [x] ✅ [DATA] P1. **DONE 2026-08-09, result NOT-COMPLETE** (dispatched via
      `cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 10, read-only measurement, no code shipped). Blocking
      prerequisite for the grid-run schedule todo above: window-scoped honest-coverage measurement for OKX/BINANCE/BYBIT
      over 2024-01-01→present. **Result: 48.90% overall reachable coverage — materially below complete.** Grid-run
      schedulability verdict: still NOT schedulable. Full breakdown + evidence: this doc's Progress Log, "window-scoped
      honest-coverage measurement RUN" entry below.

## Model-improvement backlog (deferred — not blocking the live loop)

- [ ] [RESEARCH] P2. **DEFERRED — Volume as a first-class feature for the cs/ext ML models** (operator 2026-06-24).
      **Current state (audited 2026-06-24):** the cs panel uses volume EXACTLY ONCE — `volz` =
      `log(v) − log(rolling-96 mean v)` (a single volume-momentum/surprise term); **ext uses NO volume at all.** Price
      and volume are badly under-paired despite 1m candles giving rich volume data, and volume↔price confluence is a
      classic edge. **Build + ablation-test over multiple horizons:** (1) **VWAP** from 1m (typical-price × volume,
      rolling) + price-vs-VWAP distance; (2) **multi-horizon volume momentum** (volume vs trailing average at several
      windows) + volume z-score/surprise; (3) **volume × price confluence** (volume confirming vs diverging a price move
      — a confluence filter); (4) **volume-based price-prediction** assumptions + price↔volume correlation features; (5)
      **volume PREDICTION as a feature** — we had an early volume-prediction strategy (predicted volume with some
      accuracy, per the strategy journal); feed predicted-volume (and predicted-VOLATILITY — we had that too) over
      timeframes as model inputs; (6) **audit features-service** `delta_one` registry for existing volume indicators
      (OBV / MFI / VWAP / vol-z) and wire useful ones into the cs/ext feature sets. Each addition must be a
      point-in-time feature-ablation (does it lift VALIDATION Sharpe, per the window-sweep selection discipline — never
      picked on the test years). Provenance: research session 2026-06-24 (cs/ext window + universe sweep). **DEFERRED**
      — model improvement for after the window/universe work lands.

## Cross-epic handshakes

- **Depends on**: strategy catalogue / strategy IDs / client wiring / infra baseline (was `cross_cutting_may_23`, now
  its live successors); `available_at` stamping for CeFi tick inputs (owned by
  `available_at_lookahead_bias_completion_2026_05_08`).
- **Shares with**: `live_defi_rollout` (Bybit/Binance/OKX execution-service adapters + alerting rules).
- **Provides to**: `sp_prediction` / `sports_ml` / `prediction_markets` (shared ML lifecycle: model registry, training
  pipeline, drift detection, batch backtest harness) — build the primitives once, here.

## Success criteria

- ≥7 continuous days live on real capital across the 3 venues with the full live loop, alerting, kill-switches, and DART
  override all exercised.
- Backtest fidelity proven (2-year config grid) with reproducibility from a single config + seed.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the ≥7-day live run executes on real
capital with live telemetry; the backtest grid runs to completion on real history. Hard-stops (operator-only): wallet
keys, live-trading kill-switch arming, capital ramp beyond the locked schedule.

**Reviewed 2026-07-28 (operator gate-cleanup pass) — confirmed remains a PERMANENT hard-stop**: live wallet/custody
approval (Copper/CEFFU) + kill-switch arming for real capital on OKX/Binance/Bybit are named in CLAUDE.md as a
permanent, human-only hard-stop alongside force-push-main and 1.0.0 graduation — never delegated to an agent no matter
how finished the surrounding code is (and the surrounding code IS finished here — P0 items above are shipped; only the
live-capital gate itself is withheld). Not retagged, not unlocked.

## Deferred work — migrated to:

**Not yet identified** — the "Volume as a first-class feature for the cs/ext ML models" `[RESEARCH] P2` item
(Model-improvement backlog, provenance: research session 2026-06-24) is `**DEFERRED**` — "model improvement for after
the window/universe work lands" — but no plan currently tracks that window/universe work as a distinct, named item;
grepped `plans/active/` and `plans/epics/` for "window/universe sweep"/"cs/ext window" with no hit outside this plan.
This plan's own "Model-improvement backlog" section remains the owner until a successor is authored.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - live wallet keys + kill-switch arming
  are a PERMANENT human-only hard-stop (re-confirmed 2026-07-28), and the 2-year config-grid run is operator-scheduled.
- **na-eligibility-audit 2026-07-30** (tranche=defi, autonomous): KEEP-NA, valid - live wallet keys + kill-switch arming
  are a PERMANENT human-only hard-stop, re-confirmed by the operator 2026-07-28; `locked_by` set. Reached independently
  of the cefi tranche above; both agree.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — dropped the generic autonomous-recovery-matrix.md
  and trading_agent_service_architecture_unlock.md codex/archive entries (least load-bearing for the two still-open P0
  todos) and added the two source-code paths those open todos actually target: `run_2yr_config_grid_backtest.py` (needs
  an `ML_DIRECTIONAL_CONTINUOUS` grid entry per the backtest-fidelity todo) and
  `strategy_service/engine/strategies/v2/factory.py` (where the engine is wired, named in the shipped-todo evidence).
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, valid — remaining items are a permanent
  human-only ≥7-day live-capital cutover hard-stop (2026-07-28 operator gate) plus judgment-gated follow-ons; consistent
  with 2 prior 2026-07-30 passes (cefi+defi tranches).
- **na-corpus-digest-closeout 2026-08-08 (item 26 — backtest-fidelity gate)**: operator ruled "schedule it, but gated on
  verifying data coverage first." Investigated: no window-scoped (2024-01-01→present, OKX+Binance+Bybit) honest-coverage
  measurement exists — only a full-history (~2019-2026) aggregate (44.96%/50.79%, both well below complete) whose
  refresh mechanism is itself blocked on an unrelated, chronologically-far-off (~2019-10, ~10.7% done) backfill; the one
  in-window snapshot check is contaminated by a known launcher bug, not usable as evidence. Coverage is therefore **not
  confirmed** — grid run stays NOT schedulable. Filed a new `[DATA] P1` todo for the narrow, window-scoped check that
  would actually answer this (deliberately decoupled from the stalled full-history backfill gate). No data-pipeline
  correctness violation created — this is a "cannot confirm yet" finding, not a fabricated pass.
- **na-corpus-digest-closeout 2026-08-08 (item 32 — wallet keys / kill-switch arming)**: operator answer: "Not yet —
  stays pending, permanent hard-stop until operator says otherwise." Doc status re-confirmed accurate as-is (the
  "Reviewed 2026-07-28" note above already states this is a PERMANENT hard-stop, not retagged/unlocked) — no change
  needed.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — doc carries
  `locked_by: live-defi-rollout` (conflict: not touched for a flip regardless of content). Both open todos were freshly
  re-investigated by TODAY's own na-corpus-digest-closeout entries above (items 26 and 32) and both remain genuinely
  gated: the backtest-fidelity grid run stays NOT schedulable (window-scoped coverage unconfirmed, a new bounded
  `[DATA] P1` prerequisite todo was filed for that check itself but the grid-run gate above it stays judgment-adjacent
  pending that check's result), and live-capital wallet keys/kill-switch arming is a reaffirmed PERMANENT human-only
  hard-stop. No cheat-sheet precedent from today applies (not a delete, not IAM, not a script-flag gap).

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — locked (live-defi-rollout); permanent
  human-only hard-stop (wallet/kill-switch for real capital, reaffirmed 2026-08-08) + operator-scheduled backtest grid +
  deferred research.
- **cefi_satellite_ao_dispatch_batch11 todo 10, 2026-08-09 — window-scoped honest-coverage measurement RUN, result
  NOT-COMPLETE**: read the cefi availability-index manifest once (bounded column-pruned reader reused from
  `instruments-service/scripts/measure_honest_coverage.py`'s `_read_manifest`/`_count_statuses` — no new whole-corpus
  GCS walk), filtered in-memory to venue in {OKX-SPOT, OKX-SWAP, OKX-FUTURES, BINANCE-SPOT, BINANCE-FUTURES, BYBIT} and
  date >= 2024-01-01 (2,980,916 scoped rows out of 10,537,552 total cefi manifest rows). **Overall window-scoped
  coverage = 48.90%** reachable (captured=1,295,524 / attempted_failed=94,706 / expected_unattempted=1,258,908 /
  empty_confirmed=331,778) — **materially below complete**, confirming the operator's 2026-08-08 "not confirmed" finding
  and quantifying it. Per-venue: OKX-FUTURES 80.51%, OKX-SWAP 64.18%, BINANCE-FUTURES 57.46%, BINANCE-SPOT 45.25%, BYBIT
  35.99%, **OKX-SPOT worst at 29.34%**. Per (venue, data_type): the gap concentrates almost entirely in `trades` and
  `book_snapshot_5` (10.6%-46.3% coverage across every venue) vs. `derivative_ticker`/`liquidations` (58%-97%) —
  `trades`/`book_snapshot_5` are exactly the two data_types the 2-year config-grid backtest needs for LOB/trade-level
  fidelity. **Recency check (last ~90d, >= 2026-05-11) is WORSE than the full-window average, not better: 24.70%
  overall** (OKX-SPOT 12.21%, BINANCE-SPOT 13.13%, BYBIT 18.66%) — backwards from what a live-capital gate needs (the
  most-recent data should be the best-covered, not the worst). Filed the specific gap as a blocking issue:
  `/plans/active/issues/cefi_window_scoped_coverage_gap_okx_binance_bybit_2024_2026_2026_08_09.md` (link fixed
  2026-08-09, batch11-finalize reconciliation — was missing a `_2026` segment, a broken reference to a real file).
  **Grid-run schedulability verdict unchanged: still NOT schedulable** — the operator's 2026-08-08 gating condition
  ("only schedule once coverage is confirmed") is now answered with a confirmed NO, not an unconfirmed unknown; the
  blocking issue's fix todos are the new path to schedulability. Full breakdown + evidence:
  `/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch11_2026_08_09.md` todo 10 Progress Log entry (same commit).
