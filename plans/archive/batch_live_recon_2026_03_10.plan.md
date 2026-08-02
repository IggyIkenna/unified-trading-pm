---
doc_type: plan
title: Batch-Live Reconciliation + Batch Audit System
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    deployment-api,
    deployment-service,
    execution-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-10"
overview:
  "Three interconnected deliverables:\n(1) batch-live-reconciliation-service — nightly T+1 orchestrator that replays the
  full pipeline\n    (features → ML → strategy → execution → position/risk/exposure) using T+1 GCS
  namespace,\n    compares batch events vs live events stage by stage, and attributes deviations to the responsible
  service.\n(2) batch-audit-api — new API service for batch-audit-ui covering recon results, full audit
  trail,\n    orphan/error/TTS compliance, and data completeness checks across the entire system.\n(3) GCS T+1 namespace
  + T+1 Cloud Scheduler for ALL batch services — every batch service gets a\n    daily T+1 Cloud Run Job + writes to
  t1-recon/ GCS prefix (not overwriting thermal backtest or\n    batch/ data). Applied uniformly across all
  repos.\nSurfaces everything in batch-audit-ui (expanded beyond current skeleton).\n"
todos:
  - { id: new-repo-blrs, content: Create batch-live-reconciliation-service repo, status: done }
  - { id: new-repo-batch-audit-api, content: Create batch-audit-api repo (pairs with batch-audit-ui), status: done }
  - { id: gcs-t1-namespace, content: "Add t1-recon/ GCS namespace to ALL batch services (ml-inference, strategy,
        execution, features-*); update every service's docs/GCS_PATHS.md; add --output-prefix / --run-tag to CLIs

        ", status: done }
  - { id: t1-cloud-scheduler, content: "Add T+1 Cloud Scheduler triggers for every batch service in deployment-service;
        each service runs independently on its own schedule so recon data is ready when the orchestrator runs

        ", status: done }
  - { id: codex-t1-dag-doc, content: "Write unified-trading-/codex/08-workflows/t1-batch-dag.md — canonical T+1
        pipeline DAG doc; register in SSOT-INDEX.md; no conflicts with existing docs

        ", status: done }
  - { id: extend-trading-analytics-ui, content: "Add Reconciliation tab to trading-analytics-ui: ReconRunsPage,
        ReconDetailPage, DeviationDrillPage (separate tab, trading vs expectation)

        ", status: done }
  - { id: extend-batch-audit-ui, content: "Expand batch-audit-ui with Audit Trail pages: AuditTrailPage,
        DataCompletenessPage, CompliancePage (orphans, errors, TTS)

        ", status: done }
  - {
      id: trading-agent-integration,
      content: Add reconciliation analysis task type to trading-agent-service,
      status: done,
    }
  - { id: register-manifest, content: "Register batch-live-reconciliation-service + batch-audit-api in
        workspace-manifest.json and unified-trading-codex/00-SSOT-INDEX.md

        ", status: done }
isProject: true
---

# Batch-Live Reconciliation + Batch Audit System

## Context

No existing prod-vs-backtest reconciliation exists. The existing `e2e_smoke_and_portable_backtests.md` covers only
fixture-based CI backtests (static VCR, no live comparison) — not relevant here. Items C.3 (Backtesting API) and C.4
(Reconciliation) in `master_pre_deployment_plan_chain.md` are stub post-sprint items. This plan formalises all three.

**The problem this solves:**

- When live trading deviates from backtest expectations, we currently cannot isolate which service caused the deviation
  (ML signals? Strategy instructions? Execution algo? Position/risk snapshot?)
- We have no audit trail for data completeness, orphan events, TTS compliance, or data retention health
- Every batch service runs ad-hoc; no uniform T+1 scheduled replay exists

**Intended outcome:**

- Nightly automated comparison: batch replay → live → deviation report pinned to service
- Reconciliation views in trading-analytics-ui (new tab — "trading vs expectation")
- Full system audit trail in batch-audit-ui (data completeness, orphans, TTS compliance)
- Uniform T+1 scheduling + GCS namespace isolation across all batch services

---

## What Already Exists (Reuse)

| Component                | Location                                                              | Reuse                                                |
| ------------------------ | --------------------------------------------------------------------- | ---------------------------------------------------- |
| ML batch inference CLI   | `ml-inference-service/ml_inference_service/cli/`                      | `--mode batch --date`                                |
| Strategy batch CLI       | `strategy-service/strategy_service/`                                  | `strategy-service batch --asset-group --date`        |
| Execution batch backtest | `execution-service/execution_service/cli/batch_backtest.py`           | NautilusTrader replay                                |
| GCS config loader        | `execution-service/execution_service/cli/config_loader.py`            | `get_gcs_config_path()`                              |
| Domain config reloader   | `execution-service/execution_service/`                                | `DomainConfigReloader`                               |
| PnL breakdown            | `pnl-attribution-service/pnl_attribution_service/engine/breakdown.py` | `compute_pnl_breakdown()`                            |
| Batch job UI shell       | `batch-audit-ui/src/App.tsx`                                          | `BatchJobsPage`, `JobDetailPage`, SidebarNav pattern |
| Autonomous agent         | `trading-agent-service/`                                              | Add recon analysis task type                         |
| Alerting                 | `alerting-service/`                                                   | PubSub → Slack/PagerDuty                             |
| API pattern              | `trading-analytics-api/`, `ml-inference-api/`                         | FastAPI structure, route layout                      |

---

## Architecture Overview

### Three New Deliverables

```
┌──────────────────────────────────────────────────────────────┐
│  batch-live-reconciliation-service                            │
│  (Cloud Run Job, T+1 nightly orchestrator)                   │
│   Stage 0: Config snapshot pull from GCS                     │
│   Stage 1: ML recon  → t1-recon/ml/{date}/                   │
│   Stage 2: Strategy recon → t1-recon/strategy/{date}/        │
│   Stage 3: Execution recon → t1-recon/execution/{date}/      │
│   Stage 4: Agent analysis (trading-agent-service dispatch)    │
│   Stage 5: Write consolidated summary → GCS + PubSub alert   │
└──────────────────────────────────────────────────────────────┘
         │ reads                    │ writes
         ▼                          ▼
┌───────────────────┐    ┌──────────────────────────┐
│  GCS: t1-recon/   │    │  GCS: recon-reports/     │
│  (per-service     │    │  recon_summary_{date}.json│
│   batch outputs)  │    │  agent_report_{date}.md  │
└───────────────────┘    └──────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  trading-analytics-api (existing — add /recon/* routes)      │
│  /recon/runs          → list recon runs by date              │
│  /recon/runs/{date}   → run detail + stage results           │
│  /recon/deviations    → filterable deviation list            │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  trading-analytics-ui (new "Reconciliation" tab added)        │
│  /trades        → (existing tabs unchanged)                  │
│  /recon         → ReconRunsPage (new — prod vs backtest)     │
│  /recon/:date   → ReconDetailPage                            │
│  /recon/:date/deviations → DeviationDrillPage                │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  batch-audit-api (new repo — audit trail only)               │
│  /audit/trail         → system-wide event audit trail        │
│  /audit/data-health   → data completeness + retention checks  │
│  /audit/compliance    → orphan events, errors, TTS           │
│  /batch/jobs          → batch job monitoring                  │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│  batch-audit-ui (expanded — audit trail focus)               │
│  /jobs          → BatchJobsPage (existing)                   │
│  /audit/trail   → AuditTrailPage (new)                       │
│  /audit/health  → DataCompletenessPage (new)                 │
│  /audit/compliance → CompliancePage (new — orphans/TTS/errors)│
└──────────────────────────────────────────────────────────────┘
```

---

## GCS Namespace Design (Applied to ALL Repos)

**Current namespaces:** `batch/`, `live/` **New namespace for T+1 recon:** `t1-recon/`

```
gs://<service-bucket>/
  batch/                    ← thermal backtests (UNCHANGED — do not touch)
  live/                     ← live trading data (UNCHANGED)
  t1-recon/                 ← NEW: T+1 reconciliation runs only
    ml/{date}/              ← ML batch inference outputs for T+1 recon
    strategy/{date}/        ← Strategy batch outputs for T+1 recon
    execution/{date}/       ← Execution batch backtest outputs for T+1 recon
    features/{date}/        ← Feature snapshots used in T+1 recon
    events/{date}/          ← Batch-emitted events for event comparison
```

**Key rule:** `t1-recon/` NEVER overwrites `batch/` or `live/`. Each service's CLI gets a `--run-tag t1-recon` (or
`--output-prefix t1-recon`) parameter. Without this tag, data goes to `batch/` as before.

**Applied to repos:**

- `ml-inference-service/` — add `--run-tag` to CLI + `docs/GCS_PATHS.md`
- `ml-training-service/` — add `--run-tag` to CLI + `docs/GCS_PATHS.md`
- `strategy-service/` — add `--run-tag` to CLI + `docs/GCS_PATHS.md`
- `execution-service/` — add `--run-tag` to CLI + `docs/GCS_PATHS.md`
- `features-delta-one-service/`, `features-volatility-service/`, `features-calendar-service/`,
  `features-onchain-service/`, `features-sports-service/`, `features-cross-instrument-service/`,
  `features-multi-timeframe-service/`, `features-commodity-service/` — same pattern

---

## Event Comparison (Batch Events vs Live Events)

In **live mode**, services publish events to PubSub (ephemeral). Live events are archived to GCS:
`live/events/{date}/{service}/` by the event archiver.

In **T+1 recon batch mode**, services write events to GCS directly: `t1-recon/events/{date}/{service}/` (not published
to PubSub).

The reconciliation service compares:

- `live/events/{date}/{service}/` ← what was published live
- `t1-recon/events/{date}/{service}/` ← what the batch replay would have published

**Comparison dimensions:**

- Event count match (same number of events per instrument)
- Event timing: live timestamp vs batch timestamp (structural alignment)
- Event content: field-by-field diff on signal direction, instruction side, fill price, position delta

Services do NOT need to "replay" PubSub — they just write events to GCS in batch mode. The recon orchestrator then reads
both GCS paths and diffs them. This is simpler and avoids PubSub event sourcing complexity.

---

## Stage DAG (Reconciliation Orchestrator)

```
[Cloud Scheduler: 06:00 UTC daily (after all T+1 batch jobs complete)]
        │
        ▼
Stage 0 — Config + Data Availability Check
  - Pull GCS: execution algo config snapshot as-of EOD yesterday
    (execution-service writes configs/snapshots/{date}/ nightly — see prerequisite below)
  - Pull GCS: model registry snapshot (model version used live)
  - Pull GCS: instrument universe snapshot
  - Verify: all T+1 recon batch jobs completed (poll GCS for presence of output files)
  - OUTPUT: config_context_{date}.json
        │
        ▼
Stage 1 — ML Reconciliation
  - BATCH:  Invoke ml-inference-service batch CLI with --run-tag t1-recon --date {date}
            (reads features from t1-recon/features/{date}/, writes to t1-recon/ml/{date}/)
  - LIVE:   Read live/events/{date}/ml-inference-service/ (archived PubSub events)
  - COMPARE:
      • Signal direction match rate (expected ≥ 95%)
      • Signal magnitude MAE
      • t+1 instrument coverage %
      • Event timing alignment (batch emit vs live emit — latency delta)
  - OUTPUT: t1-recon/recon/ml_recon_report_{date}.json
        │
        ▼
Stage 2 — Strategy Reconciliation
  - BATCH:  Invoke strategy-service batch CLI with --run-tag t1-recon --date {date}
            (reads t1-recon/ml/{date}/ signals, writes to t1-recon/strategy/{date}/)
  - LIVE:   Read live/events/{date}/strategy-service/ (archived instructions)
  - COMPARE:
      • Instruction alignment % (same side + instrument in batch vs live)
      • Benchmark P&L: batch strategy P&L vs live strategy P&L (marked to benchmark, not alpha)
      • Position deviation: position-balance-monitor-service EOD snapshot vs batch replay EOD
      • Exposure deviation: risk-and-exposure-service EOD VaR vs batch replay VaR
      • Event timing alignment
  - OUTPUT: t1-recon/recon/strategy_recon_report_{date}.json
        │
        ▼
Stage 3 — Execution Reconciliation
  - BATCH:  Invoke execution-service batch_backtest with --run-tag t1-recon --date {date}
            --config-snapshot configs/snapshots/{date}/ (GCS config as-of live)
  - LIVE:   Read live/events/{date}/execution-service/ (fills, orders, algo selection)
  - COMPARE:
      • Alpha P&L gap: live fills P&L minus batch fills P&L
      • Fill rate: live vs batch expected
      • Slippage: live vs batch-predicted
      • Algo selection accuracy (was TWAP/VWAP/POV correct per config?)
      • Order latency: live 500ms gate vs batch simulated
      • Event timing alignment
  - OUTPUT: t1-recon/recon/execution_recon_report_{date}.json
        │
        ▼
Stage 4 — Agent Analysis (trading-agent-service)
  - INPUT:  all three recon reports + config_context
  - TASK:   Identify largest deviations by service, hypothesize root cause, suggest improvements
  - OUTPUT: t1-recon/recon/agent_report_{date}.md
            PubSub event → alerting-service → Slack #trading-recon
        │
        ▼
Stage 5 — Consolidated Result
  - Write: t1-recon/recon/summary_{date}.json (all stage summaries + agent report GCS URL)
  - Update: recon index at t1-recon/recon/index.json (append date entry, for API listing)
  - Emit: PubSub success event → alerting-service
```

---

## T+1 Cloud Scheduler for All Batch Services

**Prerequisite for the recon orchestrator:** each batch service runs independently on its own T+1 schedule so data is
ready when the recon orchestrator starts at 06:00 UTC.

Cloud Run Jobs to add in `deployment-service/`:

| Service                             | Schedule (UTC) | Output GCS prefix                   |
| ----------------------------------- | -------------- | ----------------------------------- |
| features-delta-one-service          | 02:00          | t1-recon/features/delta-one/        |
| features-volatility-service         | 02:00          | t1-recon/features/volatility/       |
| features-calendar-service           | 01:30          | t1-recon/features/calendar/         |
| features-onchain-service            | 02:30          | t1-recon/features/onchain/          |
| features-sports-service             | 02:30          | t1-recon/features/sports/           |
| features-cross-instrument-service   | 02:30          | t1-recon/features/cross-instrument/ |
| features-multi-timeframe-service    | 02:30          | t1-recon/features/multi-timeframe/  |
| ml-inference-service                | 03:00          | t1-recon/ml/                        |
| strategy-service                    | 04:00          | t1-recon/strategy/                  |
| execution-service (config snapshot) | 00:30          | configs/snapshots/                  |
| batch-live-reconciliation-service   | 06:00          | t1-recon/recon/                     |

**Implementation:** Cloud Scheduler → Cloud Run Job per service in `deployment-service/terraform/gcp/`. The recon
orchestrator does NOT trigger these; it polls for data availability in Stage 0.

---

## API + UI Split

### trading-analytics-api: Add /recon/\* Routes (existing repo)

Extend `trading-analytics-api/` with a new route group. Pattern follows existing routes in that repo.

```
trading_analytics_api/api/routes/
  recon.py     # GET /recon/runs, /recon/runs/{date}, /recon/deviations, /recon/runs/{date}/stages/{stage}
```

**Data sources:**

- `/recon/*` → reads `t1-recon/recon/` GCS bucket (index.json + per-date summaries + stage reports)

### trading-analytics-ui: New Reconciliation Tab (existing repo)

Add to existing nav (new tab alongside current analytics tabs):

```
/recon         ReconRunsPage — table of nightly runs (date, status, deviation count by stage)
/recon/:date   ReconDetailPage — stage cards: ML / Strategy / Execution / Agent report
/recon/:date/deviations  DeviationDrillPage — per-deviation: batch vs live diff + agent commentary
```

All pages call `trading-analytics-api`. Mock mode supported.

---

### batch-audit-api: Route Design (new repo — audit trail only)

New repo pairs with `batch-audit-ui`. Pattern follows `trading-analytics-api/` and `ml-inference-api/`.

```
batch-audit-api/
  batch_audit_api/
    api/routes/
      audit_trail.py   # GET /audit/trail — system-wide event log (service, date, event type, error)
      data_health.py   # GET /audit/data-health — GCS path completeness + retention checks
      compliance.py    # GET /audit/compliance — orphan events, errors, TTS-tagged records
      batch_jobs.py    # GET /batch/jobs — batch job run history
    main.py
    config.py
```

**Data sources:**

- `/audit/trail` → UEI event archive GCS paths + deployment-api service status
- `/audit/data-health` → scans all expected GCS paths across services, checks missing/stale/deleted data
- `/audit/compliance` → orphan events log, error event archive, TTS-tagged records
- `/batch/jobs` → batch job run history from deployment-service/deployment-api

### batch-audit-ui: Expanded Page Map (existing repo)

Extend `batch-audit-ui/src/App.tsx` NAV_ITEMS (audit trail focus, no recon here):

```
/jobs              BatchJobsPage (existing)
/audit/trail       AuditTrailPage — filterable event log (service, date, event type, error flag)
/audit/health      DataCompletenessPage — per-service data presence grid, retention checks
/audit/compliance  CompliancePage — orphan events, TTS records, error counts by service
```

All pages call `batch-audit-api`. Mock mode (`MOCK_MODE`) supported (matching existing pattern).

---

## Files to Create / Modify

### New: `batch-live-reconciliation-service/`

```
batch_live_reconciliation_service/
  config.py             # UnifiedCloudConfig (no os.getenv())
  orchestrator.py       # Sequential stage runner
  stages/
    stage0_config_pull.py
    stage1_ml_recon.py
    stage2_strategy_recon.py
    stage3_execution_recon.py
    stage4_agent_analysis.py
    stage5_results_writer.py
  models/
    recon_report.py     # ReconReport, StageReport, DeviationRecord (Pydantic, no Any)
    deviation_thresholds.py
  cli/main.py           # python -m batch_live_reconciliation_service --date YYYY-MM-DD [--dry-run]
cloudbuild.yaml / buildspec.aws.yaml / Dockerfile / pyproject.toml
scripts/quality-gates.sh
```

### New: `batch-audit-api/`

FastAPI service. Structure follows `trading-analytics-api/` pattern.

```
batch_audit_api/
  api/routes/
    recon.py / audit_trail.py / data_health.py / compliance.py / batch_jobs.py
  main.py / config.py
cloudbuild.yaml / buildspec.aws.yaml / Dockerfile / pyproject.toml
scripts/quality-gates.sh
```

### Modified: `trading-analytics-ui/src/`

- `App.tsx` — add "Reconciliation" tab to nav + routes
- `pages/ReconRunsPage.tsx` (new)
- `pages/ReconDetailPage.tsx` (new)
- `pages/DeviationDrillPage.tsx` (new)

### Modified: `batch-audit-ui/src/`

- `App.tsx` — expand NAV_ITEMS with audit trail sections
- `pages/AuditTrailPage.tsx` (new)
- `pages/DataCompletenessPage.tsx` (new)
- `pages/CompliancePage.tsx` (new)

### Modified: Per-Service CLIs (ALL batch services)

Each gets `--run-tag` or `--output-prefix` parameter:

- `ml-inference-service/ml_inference_service/cli/` — add `--run-tag`
- `strategy-service/strategy_service/cli/` — add `--run-tag`
- `execution-service/execution_service/cli/batch_backtest.py` — add `--run-tag`, `--config-snapshot`
- All 8 feature services — add `--run-tag` to batch CLIs

Each service's `docs/GCS_PATHS.md` updated with `t1-recon/` namespace.

### Modified: `execution-service/` (prerequisite)

Add EOD config snapshot writer: `scripts/write_config_snapshot.py` — writes current live config to
`configs/snapshots/{date}/` at end of trading day. Called by its own Cloud Run Job (00:30 UTC).

### Modified: `trading-agent-service/`

Add reconciliation analysis task type (read existing task dispatch pattern first before modifying).

### Modified: `deployment-service/terraform/gcp/`

Add Cloud Run Job + Cloud Scheduler resources for each T+1 batch service (see schedule table above).

### Modified: `unified-trading-pm/`

- `workspace-manifest.json` — add 2 new repos
- `plans/active/` — move this plan here as `batch_live_recon_2026_03_10.md`

### New: `unified-trading-/codex/08-workflows/t1-batch-dag.md`

Canonical T+1 pipeline DAG doc. Sections:

- Pipeline overview (7-stage DAG with schedules)
- GCS namespace conventions (batch/ vs live/ vs t1-recon/)
- Event comparison pattern (batch→GCS vs live→PubSub→GCS archive)
- Deviation thresholds (per stage)
- Adding a new service to the T+1 pipeline (checklist)

### Modified: `unified-trading-codex/00-SSOT-INDEX.md`

Add entry pointing to `05-operations/t1-batch-dag.md`.

---

## Prerequisite: Execution-Service Config Snapshot

The execution-service `DomainConfigReloader` does hot-reload from GCS but does NOT snapshot config at EOD. We need a
nightly snapshot so Stage 3 can replay with the exact config that was live.

**Add to execution-service:** `execution_service/scripts/write_config_snapshot.py`

- Reads current config from GCS config store
- Writes a frozen copy to `configs/snapshots/{date}/config.json`
- Called by Cloud Run Job at 00:30 UTC (before T+1 recon runs)

---

## Implementation Phases

| Phase | Work                                                             | Repos                                     | Parallel?           |
| ----- | ---------------------------------------------------------------- | ----------------------------------------- | ------------------- |
| P1    | Codex T+1 DAG doc + SSOT-INDEX update                            | unified-trading-codex, unified-trading-pm | No (foundation)     |
| P2    | Add `--run-tag` to all batch service CLIs + GCS_PATHS.md updates | all 10 batch services                     | Yes (per-service)   |
| P3    | Execution-service config snapshot writer                         | execution-service                         | No (P2 dep)         |
| P4    | batch-live-reconciliation-service: shell + models + Stage 0      | new repo                                  | After P3            |
| P5    | Stages 1–3 (ML, Strategy, Execution recon)                       | new repo                                  | After P4            |
| P6    | Stage 4 (agent dispatch) + Stage 5 (results writer)              | new repo + trading-agent-service          | After P5            |
| P7a   | trading-analytics-api: add /recon/\* routes                      | trading-analytics-api                     | Parallel with P5-P6 |
| P7b   | batch-audit-api: new repo + audit trail routes only              | new repo                                  | Parallel with P5-P6 |
| P8a   | trading-analytics-ui: Reconciliation tab + 3 pages               | trading-analytics-ui                      | Parallel with P7a   |
| P8b   | batch-audit-ui: AuditTrail + DataHealth + Compliance pages       | batch-audit-ui                            | Parallel with P7b   |
| P9    | Cloud Run Jobs + Cloud Scheduler in deployment-service/terraform | deployment-service                        | After P4            |
| P10   | Register manifest + SSOT-INDEX                                   | unified-trading-pm                        | Last                |

---

## Verification

```bash
# 1. Dry-run recon for a specific date (reads GCS, no writes)
cd batch-live-reconciliation-service
python -m batch_live_reconciliation_service --date 2026-03-09 --dry-run

# 2. Verify t1-recon GCS namespace isolation (should NOT touch batch/ or live/)
gsutil ls gs://<service-bucket>/t1-recon/2026-03-09/
gsutil ls gs://<service-bucket>/batch/  # unchanged

# 3. Verify recon summary written
gsutil cat gs://<recon-bucket>/t1-recon/recon/summary_2026-03-09.json | python -m json.tool

# 4. Verify batch-audit-api serves recon results
curl http://localhost:8010/recon/runs | python -m json.tool
curl http://localhost:8010/recon/runs/2026-03-09 | python -m json.tool
curl http://localhost:8010/audit/data-health | python -m json.tool

# 5. Verify batch-audit-ui loads recon pages
# Navigate: /recon → /recon/2026-03-09 → /recon/2026-03-09/deviations
# Navigate: /audit/trail → /audit/health → /audit/compliance

# 6. Unit tests (each new/modified repo)
cd batch-live-reconciliation-service && pytest tests/unit/ -v --cov=batch_live_reconciliation_service
cd batch-audit-api && pytest tests/ -v --cov=batch_audit_api
cd batch-audit-ui && npx vitest run

# 7. Quality gates (each repo)
cd batch-live-reconciliation-service && bash scripts/quality-gates.sh
cd batch-audit-api && bash scripts/quality-gates.sh
```

---

## References

- `execution-service/execution_service/cli/batch_backtest.py` — batch backtest entry
- `execution-service/execution_service/cli/config_loader.py` — GCS config loading
- `pnl-attribution-service/pnl_attribution_service/engine/breakdown.py` — `compute_pnl_breakdown()`
- `batch-audit-ui/src/App.tsx` — existing shell (BatchJobsPage, JobDetailPage patterns)
- `trading-analytics-api/` — FastAPI API pattern to follow for batch-audit-api
- `trading-agent-service/` — autonomous agent task dispatch
- `alerting-service/` — PubSub → Slack
- `deployment-service/terraform/gcp/` — Cloud Run Job + Cloud Scheduler terraform
- `unified-trading-pm/plans/active/master_pre_deployment_plan_chain.md` — C.3 + C.4 this closes
- `unified-trading-pm/plans/active/e2e_smoke_and_portable_backtests.md` — different concern (CI fixtures)
