---
doc_type: issue
title: The epsilon=0 paper-equals-batch proof is correct code that has never run — scheduler paused and structurally a no-op
summary: >-
  `batch-live-reconciliation-service/engine/trade_recon.py` implements a genuine trade-for-trade epsilon=0 proof
  (trade_key matching; is_deterministic requires zero unmatched plus qty_delta, fill_price_delta_bps and fees_delta all
  zero on every matched trade). It has never produced a verdict. The Cloud Scheduler is `paused = true`, and its own
  Terraform comments state that even unpaused the ledger roots are never populated and nothing triggers the batch-rerun
  CLI, so it "runs as a permanent (correct, honest) no-op". The platform invariant that paper(W) == batch-rerun(W) is
  therefore assumed, never verified.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [strategy]
repos: [batch-live-reconciliation-service, strategy-service, deployment-service]
scope: [engineer, admin]
tags: [determinism, epsilon-zero, paper, batch, reconciliation, dormant-infrastructure, verification]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
    /codex/04-architecture/cross-domain-state-fabric.md,
    /plans/epics/system_readiness_master.md,
  ]
context_scope:
  [
    batch-live-reconciliation-service/batch_live_reconciliation_service/engine/trade_recon.py,
    deployment-service/terraform/gcp/paper_week_determinism_scheduler.tf,
    batch-live-reconciliation-service/batch_live_reconciliation_service/cli/handlers/daily_determinism_handler.py,
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
  ]
created: 2026-08-20
last_updated: "2026-08-20"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P1
severity: P1
source: >-
  Sonnet-5 sub-agent measurement audit 2026-08-20 against an external batch/paper/live recovery-plane proposal.
drift_direction: advance-code
depends_on: []
---

# A correct proof that has never been run

## The code is good. That is what makes this worth filing.

`engine/trade_recon.py::reconcile_day` matches `TradeFillRecord`s by `trade_key` and sets `is_deterministic=True`
**only** if there are zero unmatched records on both sides AND every matched trade has `side_match`, `qty_delta == 0`,
`fill_price_delta_bps == 0` and `fees_delta == 0` (`trade_recon.py:96-112`). On mismatch it bug-classifies into
`NON_DETERMINISM | INPUT_CAPTURE_GAP | FILL_MODEL_DRIFT` (`trade_recon.py:114-122`). That is a real trade-for-trade
proof, not aggregate PnL agreement. It is unit-tested.

## Measured 2026-08-20 — it has never produced a verdict

- `deployment-service/terraform/gcp/paper_week_determinism_scheduler.tf:267` — *"The scheduler is PAUSED
  (paused = true) until all three CLI entrypoints are implemented."*
- The same file at `:136-152` documents that even unpaused it could not work: `paper_ledger_root` /
  `batch_ledger_root` "are still never populated by this scheduler, and no stage here triggers strategy-service's
  `batch-rerun` CLI op... Until both are wired, daily-determinism runs as a permanent (correct, honest) no-op — it
  never actually reconciles."
- `strategy_service/cli/handlers/daily_determinism_handler.py:59-68` defends correctly: empty roots return
  `{"status": "ok", "skipped": "no_run_configured"}`. **It has never fabricated a verdict** — it has simply never
  produced one.

## Why this matters more than its priority suggests

Every architectural ruling made on 2026-08-20 — the factor-state model, per-region replay, the fast/slow split —
assumes `paper(W) == batch-rerun(W)`. That invariant is currently **assumed, not verified**. This reconciliation is
also the check that would independently catch fill-model drift and input-capture gaps, including several defects filed
the same day from separate audits.

**Operator ruling 2026-08-20: wire it AFTER the state-fabric build**, accepting unproven determinism in the interim as
a documented known gap. Recorded here so the gap is explicit and dated rather than assumed closed. Priority is P1 by
that ruling, not P0 — the sequencing is deliberate, not an oversight.

## Two codex claims this contradicts

1. `paper-batch-live-reconciliation.md` §7 marks "trade-by-trade keyed diff + daily T+1 recon" and "daily T+1 recon
   verdict -> AlertEvent" as **EXISTS**, and the doc header states a cadence of "per-paper-run (daily ledger) + T+1
   (daily recon)". The code exists and is correct; the **cadence** claim does not hold — the cron is paused and, as
   configured, structurally cannot fire correctly.
2. `paper-batch-live-reconciliation.md` §2's entry-point table states the paper/live path is
   `colocated_engine.py StrategySupervisor -> ClientWorker` calling `V2EngineOrchestrator.on_tick()`. `client_worker.py`
   has **zero** references to `V2EngineOrchestrator` or `on_tick`. The closest real bridge found was
   `engine/core/engine/v2_shadow_runner.py`, a process-wide singleton fed from the legacy `BaseStrategy` manager, which
   the table does not mention. Flagged as a discrepancy, not a confirmed doc error — the auditor could not locate the
   documented wiring within budget.

Separately: `live-data-persistence-and-event-log.md` frames `EventTransport` / `InMemoryTransport` / `SINK_MATRIX` as
*the* paper-equals-batch determinism mechanism at the tick layer. In the audited repos `event_facade` is used **only**
for publishing `LEADER_HEDGE` multi-leg instructions; the determinism proof that actually exists is a separate
GCS-JSONL mechanism that never imports it.

## Todos

- [ ] [BACKEND] P1. **Populate `paper_ledger_root` / `batch_ledger_root` and trigger the batch-rerun CLI**, then
      unpause the scheduler. Sequenced after the state-fabric build per the 2026-08-20 ruling.
- [ ] [DOC] P1. **Correct `paper-batch-live-reconciliation.md` §7's cadence claim** — the mechanism EXISTS but does not
      RUN, and the table currently reads as though it does. A reader checking whether determinism is verified would
      conclude yes.
- [ ] [REVIEW] P1. **Resolve the §2 entry-point discrepancy** — either the doc names wiring that does not exist, or the
      wiring exists somewhere the auditor did not reach. Both are worth knowing; only one requires a code change.
- [ ] [DOC] P2. **Reconcile the two determinism narratives.** Two codex docs describe different mechanisms as the
      determinism spine. Establish which is authoritative and mark the other as describing a planned or adjacent
      mechanism.
- [ ] [REVIEW] P2. **Add fidelity labelling to `RunManifest`.** It carries `code_shas`, `feature_group_versions`,
      `fill_model` and `market_data_days` but no feed-fidelity or matcher-version field, so a "paper beat backtest"
      result cannot be distinguished from a model change. `fill_model: BENCHMARK|LIVE_VENUE` is the nearest proxy and
      is far coarser than the fidelity tier the codex doc itself describes.

## What was measured as sound, so nobody re-audits it

- **Multi-day state carries correctly.** One `GroupBRunner`, one engine instance, one flat tick list across the whole
  window (`paper_run_handler.py:1087-1138, 2181, 2404`; `runner.py:283-287`). Positions, `_position_state` and
  `BenchmarkFillEngine.fills` persist unbroken across UTC midnight because it is the same object being iterated. The
  nightly cron reprocesses a fresh trailing 7-day window, so state does not persist across invocations — only within
  one call's window.
- **Testnet is structurally a PAPER sub-mode.** `position/position_interface/base.py:56-82` raises on
  `mode==LIVE and testnet` and on `mode==BATCH and testnet`. Matches the codex ruling; no contradiction found.
- **`GroupCRunner` does not exist** (`rg "class GroupCRunner"` -> 0 hits), confirming the G1 gap "batch must run the
  same smart matching as paper" is still fully open — consistent with the documented design, not a new defect.

## Progress Log

**2026-08-20 — filed.** No code touched. Operator ruled the sequencing (after the state-fabric build) at filing time,
so this is a dated, accepted gap rather than an open question.

- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries); corrected 2 stale paths —
  `trade_recon.py` was missing its `batch_live_reconciliation_service/` package-dir prefix, and
  `daily_determinism_handler.py` was attributed to `strategy-service` (per the doc's own body-text citation at
  line 67) but actually lives in `batch-live-reconciliation-service` — both now verified on disk.
