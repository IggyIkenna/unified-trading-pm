---
title: Batch-Live Reconciliation Service (BLRS) — Repo Audit, Codex↔Code Drift, Cross-Repo Responsibility Map
created: 2026-05-27
source:
  - batch-live-reconciliation-service/
  - unified-trading-pm/codex/04-architecture/reconciliation-resolution.md
  - unified-trading-pm/codex/04-architecture/reconciliation-age-tracking.md
  - unified-trading-pm/codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md
  - unified-trading-pm/codex/15-runbooks/position-reconciliation-deploy-gate.md
  - unified-trading-pm/codex/04-architecture/paper-vs-live-execution-seam.md
  - unified-trading-pm/codex/04-architecture/separation-of-concerns.md
  - unified-trading-pm/codex/04-architecture/data-flow-map.md
locked_by: live-defi-rollout
status:
  AUDIT COMPLETE (pass 2) — D1 ✅ DECIDED=A (codex corrected); D2/D3/D4/G12 → routed to ikenna-main 2026-05-27; G2/G4/G5
  self-completing
priority: P2
---

# Batch-Live Reconciliation Service (BLRS) — Audit

> **🟦 OPERATOR DECISION LEDGER — 2026-06-01 (Ikenna, recorded slot-1).** D1 already DECIDED=A. The three routed items
> are now ruled (FINAL). Execution: **slot 7** records each into `batch_live_symmetry_master` (SSOT) and ships the quick
> one.
>
> - **D2** — BLRS calls strategy-service/position **query API** for the canonical position baseline (not event-archive
>   reads). Stronger correctness; endpoints exist.
> - **D3** — **build all three** recon green gates now (drawdown + fill-rate + bps). Only-bps = false-pass recon
>   (data-correctness HARD RULE). [record D2/D3 as todos in `batch_live_symmetry_master`]
> - **D4** — BLRS resolution route moves to **`/t1-recon/...`**; live recon stays on strategy-service/position. [slot 7
>   > ships the rename if cleanly QG-green]
> - **G12** — see `recon_freeze_armed_never_published_2026_05_27.md` (in-scope, per-incident-type — ruled there).

> **Purpose**: Full audit of `batch-live-reconciliation-service`: what it does, how data flows, codex↔code drift, and
> which responsibilities are misplaced (here vs other repos).
>
> **Decision legend**: `✅ DECIDED (auto)` = trivial, decided by auditor + rationale. `❓ NEEDS-OPERATOR` = material
> design call awaiting Harsh/Ikenna. All tracked in § 7.

---

## 0. Executive summary

BLRS is a **T+1 nightly batch-vs-live reconciliation orchestrator**. It runs a sequential multi-stage DAG that, for the
prior trading day, compares the _batch replay_ of the pipeline against what actually happened _live_ (and _paper_),
decomposing any P&L gap into **data-pipeline noise → ML noise → strategy alpha → execution alpha**. It writes
JSON/markdown recon reports to a `recon-{project}` bucket and emits drift events that `alerting-service` consumes. It
also exposes a FastAPI **resolution surface** for operators to accept/reject/investigate breaks from the UI.

It is **its own standalone repo** (~3,600 LoC), NOT merged into strategy-service or any other service. It is registered
in `workspace-manifest.json` at `0.1.0`, has its own Dockerfile + cloudbuild + AWS buildspec, and is triggered by a
Cloud Scheduler cron at **06:00 UTC** (final stage of the T+1 pipeline DAG). Per codex it has **never run in prod** —
prod activation is gated behind master-plan item F-21.

**Headline findings:**

1. **Code is AHEAD of codex on the 3-way recon.** Codex (`paper-vs-live-execution-seam.md`,
   `reconciliation-resolution.md`) says BLRS ships "5 logical stages, no `paper_live_recon` / `batch_paper_recon` stage"
   and marks 3-way recon (batch↔paper↔live) as **DEFERRED**. The code **already has** `stage3b_paper_live_recon.py` +
   `stage3c_batch_paper_recon.py` with per-pair thresholds and failure-routing (`AUTO_DEMOTE_TO_PAPER`). → codex must be
   un-deferred. (§ 4 #1)

2. **Codex misattributes live recon to BLRS — but it IS built, elsewhere (pass-2 finding, see § 9).** Codex
   (`reconciliation-age-tracking.md`) attributes to BLRS a 12-dimension continuous reconciliation, an Incident-Gateway
   `recovery_verifier.py` callback, and a daily `check_oldest_age.py`. **None of those are in BLRS.** But live
   continuous reconciliation is NOT absent from the workspace — it is **distributed across three other repos**:
   strategy-service's `position/` module (the absorbed PBMS — `reconciliation_engine.py`, `position_drift_monitor.py`,
   deviation lifecycle, age fields), execution-service (`yield_recon_engine`, `funding_recon_engine`, `recon_freeze`
   preflight), and alerting-service (age-band rules, `recovery_verifier.py`, recon-drift handler). BLRS is purely the
   **T+1 batch auditor**. So the codex doc is _misattributed_, not describing vapor. This strongly favours D1-(A). (§ 4
   #2, § 9.1, § 7.2 D1)

3. **PBMS no longer exists as a repo — merged into strategy-service on 2026-05-20 (pass-2 finding).**
   `separation-of-concerns.md` (reviewed 2026-05-17, three days earlier) still names a standalone `PBMS query API` as
   BLRS's canonical baseline. Per `workspace-manifest.json:231` PBMS was merged into
   `strategy-service/strategy_service/position/`. BLRS reads **GCS event archives** and makes **no position-query call
   at all**. The codex matrix is stale, and the "PBMS query API" it means is now strategy-service/position's
   `/reconciliation/snapshots/history` + `/pnl-series` routes. (§ 4 #3, § 9.2, § 7.2 D2)

4. **Resolution API is mock-backed.** `GET /reconciliation/breaks` returns 3 hardcoded breaks; the resolution store is
   an in-memory dict. It is not wired to the Stage-5 GCS summaries it is supposed to surface. Acceptable pre-activation,
   but a tracked gap. (§ 4 #5)

5. **Several codex-spec'd artifacts are unbuilt**: `SOAK_MODE`/`BLR_SOAK_MODE` (orchestrator),
   `batch_live_recon.analysis.threshold_distribution` module, `stage4_risk_recon.py` (drawdown gate). Two stage1 metrics
   are stubbed (`latency_delta_ms` hardcoded `0.0`). Stage-4 agent dispatch to `trading-agent-service` writes markdown
   only (Phase-6 stub). (§ 4 #6–#9)

6. **Cross-repo separation is mostly clean.** execution-service (`yield_recon_engine`, `funding_recon_engine`,
   `recon_freeze`), ml-service (`drift_monitor`), and alerting-service (`recon_drift_event_handler`) are **legitimately
   distinct or downstream consumers**, not duplication. The one genuine boundary question is which repo owns _live
   continuous position reconciliation_ (§ 7.2 D1).

---

## 1. What the service is & does (code-truth)

### 1.1 Package layout

```
batch_live_reconciliation_service/
  __main__.py / cli/main.py              CLI entrypoint (ServiceCLI + ServiceBootstrap)
  cli/handlers/reconcile_handler.py      --operation reconcile handler
  engine/orchestrator.py                 9-stage sequential DAG runner
  engine/mock_data_provider.py           CLOUD_MOCK_MODE seed + real deviation detection
  stages/stage0_config_pull.py           upstream availability gate
  stages/stage0_manifest_reason_check.py batch/live manifest capture_status agreement
  stages/stage0_data_pipeline_recon.py   instruments/MTDS/MDPS file+row+schema parity (538 LoC)
  stages/stage1_ml_recon.py              ML signal direction/magnitude/coverage
  stages/stage2_strategy_recon.py        instruction alignment / pnl / position / VaR
  stages/stage3_execution_recon.py       alpha-pnl / fill-rate / slippage(bps) / algo / latency
  stages/stage3b_paper_live_recon.py     paper↔live (2× tighter, AUTO_DEMOTE routing)
  stages/stage3c_batch_paper_recon.py    batch↔paper (wider, ALERT routing)
  stages/stage4_agent_analysis.py        builds markdown analysis prompt → GCS (no dispatch yet)
  stages/stage5_results_writer.py        summary_{date}.json + index.json
  api/main.py                            health router (data_freshness callback)
  api/resolution_api.py                  GET /breaks, POST /resolve, POST /book-correction
  models/recon_report.py                 ReconStage, ReconStatus, DeviationRecord, StageReport, ReconReport
  models/deviation_thresholds.py         6 frozen-dataclass threshold sets
  config.py                              ReconConfig(UnifiedCloudConfig)
  config_reloaders.py                    instruments + venues DomainConfigReloader
```

### 1.2 The reconciliation stages (stage0 → stage5)

| Stage                   | Compares                                               | Key metrics                                                                          | Failure routing                                                                 |
| ----------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------- |
| 0 config_pull           | upstream snapshot availability                         | blob-exists: config snapshot, ML `_SUCCESS`, strategy `_SUCCESS`                     | **aborts pipeline** if missing                                                  |
| 0 manifest_reason_check | batch vs live manifest `capture_status`/`error_reason` | agreement rules; flags asymmetric failures                                           | deviation only (fail-open)                                                      |
| 0.5 data_pipeline_recon | instruments / MTDS / MDPS, all 5 asset-groups          | file-count match %, row-count match %, schema+value mismatch (`reconcile_shard`)     | deviation if <95% match; shard-isolated                                         |
| 1 ml_recon              | batch vs live ML inference events                      | signal-direction match, magnitude MAE, coverage %, latency Δ (**0.0 stub**)          | deviation                                                                       |
| 2 strategy_recon        | batch vs live strategy events                          | instruction alignment %, P&L Δ, position Δ, VaR Δ                                    | deviation                                                                       |
| 3 execution_recon       | batch vs live execution events                         | alpha-P&L gap, fill-rate Δ, slippage bps (per-archetype), algo accuracy, latency P99 | emits `BATCH_VS_LIVE_RECON_DRIFTED` on UAC `RECON_GREEN_THRESHOLDS` breach      |
| 3b paper_live_recon     | paper vs live execution                                | same as 3, **2× tighter**                                                            | emits `BATCH_LIVE_RECON_DRIFT` + `PAPER_LIVE_DEVIATION`; `AUTO_DEMOTE_TO_PAPER` |
| 3c batch_paper_recon    | batch vs paper execution                               | pnl Δ%, position Δ, fill-count Δ%, latency-model Δ                                   | `BATCH_PAPER_DEVIATION`; `ALERT` only                                           |
| 4 agent_analysis        | (analysis, not comparison)                             | builds markdown prompt from all deviations                                           | writes `agent_report_{date}.md`; **no dispatch**                                |
| 5 results_writer        | (persist)                                              | consolidated report                                                                  | `summary_{date}.json` + appends `index.json`                                    |

### 1.3 Orchestrator & engine

`engine/orchestrator.py` runs the stages **sequentially**. Stage 0 failure aborts; all other stages use **shard-level
failure isolation** (per-service/per-category try/except, never raises to caller — compliant with the workspace
shard-isolation rule). Emits lifecycle `STARTED`/`STOPPED`/`FAILED` plus the drift events above. Respects `--dry-run`
(skips all GCS I/O, returns synthetic PASSED). `mock_data_provider.run_mock_pipeline()` is wired for
`CLOUD_MOCK_MODE=true` and runs **real** deviation detection against seeded upstream data (idempotent via
`.seed-complete` marker).

### 1.4 CLI surface

`python -m batch_live_reconciliation_service --operation reconcile --mode batch [--start-date YYYY-MM-DD] [--dry-run]`.
Only operation = `reconcile`, only mode = `batch`, **no `--asset-group`** (it sweeps all groups internally). Defaults
`start-date` to yesterday (UTC). Returns `{"status":"ok"}` on PASSED, else
`{"status":"error","message":"reconciliation_failed"}`.

### 1.5 Resolution API (FastAPI)

- `GET /reconciliation/breaks` — filters venue/break_type/status. **Returns 3 hardcoded mock breaks.**
- `POST /reconciliation/resolve` — `ReconciliationResolution` (UAC internal); stores in **in-memory dict**; emits
  `RECONCILIATION_BREAK_RESOLVED`.
- `POST /reconciliation/book-correction` — pre-fills a manual correction (side from delta sign).
- `api/main.py` health router with `data_freshness` callback over `_last_processed_date`.

### 1.6 Models & schemas

All recon models are **correctly service-local** (recon report internal). `DeviationRecord` inherits
`ReconciliationAgeFields` from **UAC**, carries a `ReconciliationDimension` (UAC, 12-member enum), and has the
`DeviationRecord.new()` factory that auto-populates age fields at write-time (P0.4). `ReconciliationResolution` /
`ReconciliationAction` come from `unified_api_contracts.internal`.

### 1.7 Config & reloaders

`ReconConfig(UnifiedCloudConfig)` — no `os.getenv()`. Derives `recon_bucket`, `events_bucket`, `execution_store_bucket`,
and per-asset-group instruments/tick buckets via `resolve_bucket_name()` (bucket-name SSOT). `config_reloaders.py` runs
`DomainConfigReloader` for instruments + venues domains with atomic swap + `CONFIG_CHANGED` events. (One
`os.environ.get("WORKSPACE_ROOT")` in `mock_data_provider.py:45` is `# noqa: qg-os-env` — local-dev seed only,
acceptable.)

---

## 2. Data flow (end-to-end)

### 2.1 Inputs (read-only)

| Producer repo                  | Artifact                          | GCS path                                                                | Consumed by                             |
| ------------------------------ | --------------------------------- | ----------------------------------------------------------------------- | --------------------------------------- |
| execution-service              | EOD config snapshot               | `execution-store-*/configs/snapshots/{date}/config.json`                | stage0                                  |
| ml-service (ml-inference)      | batch + live inference events     | `{t1-recon,live}/events/{date}/ml-inference-service/`                   | stage1                                  |
| strategy-service               | batch + live strategy events      | `{t1-recon,live}/events/{date}/strategy-service/`                       | stage2                                  |
| execution-service              | batch+paper+live execution events | `{t1-recon,paper,live}/events/{date}/execution-service/`                | stage3/3b/3c                            |
| instruments-service            | batch+live reference data         | `instruments-*-{pid}/{date}/` + `live/{date}/`                          | stage0.5                                |
| market-tick-data-service       | batch+live ticks                  | `market-data-tick-*-{pid}/{date}/` + `live/{date}/`                     | stage0.5                                |
| market-data-processing-service | processed candles                 | `market-data-tick-*-{pid}/processed/{date}/` + `processed/live/{date}/` | stage0.5                                |
| (manifest)                     | availability index                | via `read_availability_index()`                                         | stage0 manifest_reason_check + stage0.5 |

### 2.2 Per-stage transforms — see § 1.2.

### 2.3 Outputs (written by BLRS)

```
gs://recon-{project}/t1-recon/recon/
  summary_{date}.json     full ReconReport JSON
  agent_report_{date}.md  markdown analysis prompt
  index.json              cumulative {date,status,total_deviations,path,completed_at}, desc
```

Plus events: `BATCH_VS_LIVE_RECON_DRIFTED`, `BATCH_LIVE_RECON_DRIFT`, `PAPER_LIVE_DEVIATION`, `BATCH_PAPER_DEVIATION`,
`RECONCILIATION_BREAK_RESOLVED`. **BLRS never writes to `batch/` or `live/` prefixes** — outputs to `t1-recon/recon/`
only.

### 2.4 Batch vs live symmetry

Consistent with the workspace "live = batch" rule: BLRS does not run the pipeline; it _reads the event archives both
modes already produced_ and diffs them. The only thing that differs between the two sides by design is the **fill
source** (matching-engine simulated vs real venue), which is exactly what stage3 isolates as "execution alpha."

### 2.5 Trigger mechanism

- **Cron (primary):** `deployment-service/terraform/gcp/t1_batch_scheduler.tf` Cloud Scheduler `0 6 * * *` (06:00 UTC) →
  `deployment-service/terraform/gcp/audit03_cron_provisioning.tf` `batch_live_recon_job` Cloud Run Job (cpu 2 / mem 4Gi
  / timeout 7200s) with `args=["--operation","reconcile","--mode","batch"]`. Final stage of the T+1 DAG (after
  instruments 00:00 → MTDS 00:30 → MDPS 01:30 → ml 03:00 → strategy 04:00).
- **CLI (manual):** as § 1.4.
- **API:** resolution endpoints are operator-driven, not a recon trigger.

---

## 3. Codex SSOT — what the docs specify

| Codex doc                                                                    | Last reviewed | Scope                                                                                                                                                                                      |
| ---------------------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `04-architecture/reconciliation-resolution.md`                               | 2026-05-17    | PRIMARY. 6-stage DAG, alpha decomposition, inputs (incl. **PBMS baseline**), comparison keys, failure-routing, resolution schema + API. Says "5 stages today, 3-way DEFERRED".             |
| `04-architecture/reconciliation-age-tracking.md`                             | 2026-05-23    | **12 reconciliation dimensions**, age fields, 3-band escalation ladder (5/15/30 min), 7 immediate-SEV0 overrides, recon-freeze, **BLRS recovery_verifier callback + check_oldest_age.py**. |
| `09-strategy/operational/batch-live-reconciliation-threshold-calibration.md` | (none)        | UAC `RECON_GREEN_THRESHOLDS` SSOT, 3 gates (bps/drawdown/fill), pre-soak smoke criteria, 7-day soak procedure, **`SOAK_MODE` env**, `threshold_distribution` analysis cmd.                 |
| `15-runbooks/position-reconciliation-deploy-gate.md`                         | 2026-05-12    | Pre/post-deploy `/positions` snapshot gate (owned by deployment-service + execution-service; resolves _via_ BLRS resolution API).                                                          |
| `04-architecture/paper-vs-live-execution-seam.md`                            | 2026-05-10    | 3-way recon (batch↔paper↔live) marked **DEFERRED design-only (pvl-p21a)**; per-pair thresholds + alert/auto-pause/auto-demote routing future.                                            |
| `04-architecture/separation-of-concerns.md`                                  | 2026-05-17    | PBMS consumer matrix: **BLRS reads PBMS query API, writes nothing**.                                                                                                                       |
| `04-architecture/data-flow-map.md`                                           | 2026-05-20    | Recon writer→`recon-{P}/`→reader `trading-analytics-api`→`trading-analytics-ui`.                                                                                                           |
| `04-architecture/scenario-outcome-assertions.md`                             | 2026-05-18    | `RECONCILIATION_FLAGGED` outcome category.                                                                                                                                                 |

Threshold-resolution model in codex is **two layers**: per-stage tolerances in `models/deviation_thresholds.py`
(ML/Strategy/Execution/DataPipeline/PaperLive/BatchPaper) **and** per-archetype green gates in UAC
`RECON_GREEN_THRESHOLDS` (bps_delta/drawdown/fill_rate). The orchestrator's drift event uses the UAC per-archetype gate;
the stages use per-stage tolerances.

---

## 4. Codex ↔ Code drift

| #   | Topic                                                                        | Codex says                                                                                                                                           | Code does                                                                                                                                                                                                                                                                                                                                                                       | Verdict                                                         | Action                                                                                           |
| --- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| 1   | **3-way recon stages**                                                       | "5 stages; **no** `paper_live_recon`/`batch_paper_recon`; 3-way DEFERRED (pvl-p21a)"                                                                 | `stage3b_paper_live_recon.py` + `stage3c_batch_paper_recon.py` **exist & run**, with per-pair thresholds + `AUTO_DEMOTE_TO_PAPER` routing                                                                                                                                                                                                                                       | **CODE is right** — 3-way is shipped                            | ✅ auto: un-defer in `paper-vs-live-execution-seam.md` + `reconciliation-resolution.md` (§7.1-1) |
| 2   | **Continuous 12-dim age tracking + recovery_verifier + check_oldest_age.py** | BLRS owns live continuous reconciliation across 12 dims, registers Incident-Gateway `recovery_verifier.py`, runs daily `scripts/check_oldest_age.py` | **None in BLRS.** BLRS is T+1 batch only. Live recon IS built — in strategy-service/`position/` (`reconciliation_engine.py`, `position_drift_monitor.py`, deviation lifecycle, age fields), execution-service (`recon_freeze`, yield/funding recon), alerting-service (`recovery_verifier.py`, age-band rules). Only 2 of 12 dims (POSITIONS, FEES) actually populated anywhere | **MISATTRIBUTED** — codex assigns to BLRS what 3 other repos do | ❓ operator: D1 — formally reassign in codex (recommend A) — see § 9.1                           |
| 3   | **PBMS canonical baseline**                                                  | BLRS reads positions via standalone **PBMS query API** as canonical batch↔live baseline                                                             | No position-query call at all; reads GCS event archives. **PBMS repo no longer exists — merged into strategy-service/position 2026-05-20** (`workspace-manifest.json:231`); query API is now position/`api/routes/{pnl_series,positions_health}` + `/reconciliation/snapshots/history`                                                                                          | **DRIFT + stale repo** — codex (2026-05-17) predates the merge  | ❓ operator: D2 — call strategy-service/position API, or ratify event reads — see § 9.2          |
| 4   | **Resolution API backing**                                                   | `GET /breaks` lists real breaks; resolutions persisted (GCS)                                                                                         | 3 hardcoded mock breaks; in-memory resolution dict                                                                                                                                                                                                                                                                                                                              | **CODE incomplete** (acceptable pre-activation)                 | ✅ auto: track as P1 gap; wire to Stage-5 summaries before prod activation (§7.1-4)              |
| 5   | **SOAK_MODE**                                                                | orchestrator `SOAK_MODE=os.getenv("BLR_SOAK_MODE",...)` suppresses CRITICAL during 7-day soak                                                        | not implemented (and `os.getenv` would violate rules)                                                                                                                                                                                                                                                                                                                           | **CODEX spec unbuilt**                                          | ✅ auto: implement via `ReconConfig` flag (not env); track P2 (§7.1-2)                           |
| 6   | **threshold_distribution analysis**                                          | `python3 -m batch_live_recon.analysis.threshold_distribution ...`                                                                                    | module absent; package is `batch_live_reconciliation_service` not `batch_live_recon`                                                                                                                                                                                                                                                                                            | **CODEX wrong name + unbuilt**                                  | ✅ auto: fix doc module path; track build as P2 (§7.1-3)                                         |
| 7   | **Drawdown + fill-rate gates**                                               | `RECON_GREEN_THRESHOLDS` has bps_delta **+ drawdown_pct + fill_rate_min**; drawdown "measured by `stage4_risk_recon.py`"                             | only slippage/bps read by orchestrator; **no `stage4_risk_recon.py`**; drawdown gate unimplemented                                                                                                                                                                                                                                                                              | **CODE partial**                                                | ❓ operator-lite: D3 — are drawdown/fill gates in May-23 scope?                                  |
| 8   | **stage1 latency delta**                                                     | latency Δ is a real ML recon metric                                                                                                                  | hardcoded `0.0` (TODO: timestamp compare)                                                                                                                                                                                                                                                                                                                                       | **CODE stub**                                                   | ✅ auto: track P2 implement-or-remove (§7.1-5)                                                   |
| 9   | **stage4 agent dispatch**                                                    | agent analysis dispatched to `trading-agent-service`                                                                                                 | writes markdown only ("Phase 6")                                                                                                                                                                                                                                                                                                                                                | **CODE stub** (matches codex "future")                          | ✅ auto: track P2 (§7.1-6)                                                                       |
| 10  | **data-flow-map reader/UI names**                                            | reader=`trading-analytics-api`, UI=`trading-analytics-ui`                                                                                            | those repos don't exist in workspace; recon UI hooks are in `unified-trading-system-ui`, API surface in `unified-trading-api`                                                                                                                                                                                                                                                   | **CODEX stale repo names**                                      | ✅ auto: fix `data-flow-map.md` (not BLRS-owned; low-pri) (§7.1-7)                               |
| 11  | **prod status**                                                              | "NEVER executed in prod; pending F-21"                                                                                                               | consistent — cron exists but staging only                                                                                                                                                                                                                                                                                                                                       | aligned                                                         | none                                                                                             |

---

## 5. Cross-repo responsibility map

### 5.1 What BLRS legitimately owns

- T+1 batch-vs-live(-vs-paper) **audit** of the full pipeline (data → ML → strategy → execution).
- Alpha decomposition (data-pipeline noise / ML noise / strategy alpha / execution alpha).
- Recon report persistence (`recon-{P}/t1-recon/recon/`) + cumulative index.
- Drift event emission (consumed downstream by alerting-service).
- Operator **resolution surface** (breaks list / resolve / book-correction).

### 5.2 BLRS responsibilities the codex assigns to it but that are executed elsewhere

Codex `reconciliation-age-tracking.md` assigns live continuous reconciliation (`recovery_verifier.py`,
`check_oldest_age.py`, 12 dims) to BLRS. **Reality: it's already built and distributed across three repos** (full map in
§ 9.1). BLRS contributes nothing live today. The honest fix is to **disown it in the codex** (reassign), not to move
code into BLRS — unless the operator wants centralisation (D1-(B)). The live machinery:

- **strategy-service/`position/`** (absorbed PBMS): `core/reconciliation_engine.py` (venue↔internal position recon
  loop), `core/position_drift_monitor.py` (continuous drift → `POSITION_DRIFT_DETECTED` / `KILL_SWITCH_ACTIVATED`),
  deviation lifecycle (`deviation_tracker.py`: TRANSIENT→CONFIRMED→AUTO_RECONCILED|ESCALATED→RESOLVED), age fields on
  `ReconciliationSnapshot`, `v2/recon_freshness.py` (freshness feed to risk-service), and a full reconciliation API
  (`api/reconciliation_routes.py`).
- **execution-service**: `preflight/recon_freeze.py` (order-block on freeze), `services/{yield,funding}_recon_engine.py`
  (live venue accrual/funding recon), `services/account_history_client.py`.
- **alerting-service**: `gateway/recovery_verifier.py` (the recovery callback codex attributes to BLRS — actually a
  generic 5-boolean DR aggregator here), `rules/reconciliation_rules.py` (age-band 5/15/30 + 7 immediate-SEV0
  overrides), `recon_drift_event_handler.py` (consumes BLRS drift events).

### 5.3 Non-BLRS responsibilities currently in BLRS (candidates to move OUT) — none found

No misplaced logic detected inside BLRS. Its data-pipeline parity (stage0.5) reads producer buckets but does not
duplicate producer logic; comparison-only is correct for a recon service.

### 5.4 Integration touchpoints (correct as-is)

- **alerting-service** — pure consumer of BLRS drift events (`recon_drift_event_handler.py`,
  `subscribers/batch_event_reader.py`). No duplication.
- **execution-service yield/funding recon** — _live-cycle_ venue reconciliation; orthogonal to BLRS's T+1
  strategy/execution-alpha audit. Legitimately separate.
- **ml-service `drift_monitor`** — model-accuracy drift; different layer. Legitimately separate.
- **deployment-service** — owns the cron trigger + the pre/post-deploy `/positions` gate; the gate _resolves through_
  BLRS's resolution API. Correct.
- **deployment-api `strategy_runs.py`** — naming-convention comment only; no logic coupling.
- **strategy-service `seed_mock_data.py`** — test fixtures only.

### 5.5 ⚠️ Overlap risk — two `/reconciliation/resolve` APIs (pass-2 finding)

BLRS and strategy-service/`position/` **both expose `POST /reconciliation/resolve`** taking a UAC `ReconciliationAction`
(ACCEPT/REJECT/INVESTIGATE) and both emit `RECONCILIATION_BREAK_RESOLVED`:

|              | BLRS `api/resolution_api.py`                   | strategy-service `position/api/reconciliation_routes.py`                                    |
| ------------ | ---------------------------------------------- | ------------------------------------------------------------------------------------------- |
| Backing      | **mock** (3 hardcoded breaks, in-memory store) | **real** (DB-backed deviation lifecycle + `/snapshots/history`)                             |
| Key          | `break_id`                                     | `deviation_id`                                                                              |
| Scope        | T+1 batch breaks                               | live position/balance deviations                                                            |
| Extra routes | `/breaks`, `/book-correction`                  | `/deviations`, `/balances`, `/pnl`, `/summary`, `/auto-recon/history`, `/snapshots/history` |

These are **different concerns** (T+1 batch break vs live deviation) but a UI consumer hitting `/reconciliation/resolve`
must know which service it's talking to, and the path collision is a real footgun. → **D4** (consolidate vs namespace vs
leave). The strategy-service surface is the more complete one and is real today; BLRS's is mock.

---

## 6. Gaps / undecided / incomplete (tracked)

- G1 (P1) Resolution API mock-backed; not reading Stage-5 summaries; in-memory resolution store. [→§7.1-4]
- G2 ✅ DONE (BLRS@07222f6) `stage1` `latency_delta_ms` now a real median |batch−live| `metadata.inference_duration_ms`
  over matched keys + `latency_samples` gate (no-data ≠ pass); 2 unit tests; QG green. [→§7.1-5]
- G3 (P2) stage4 agent dispatch to trading-agent-service is markdown-only. [→§7.1-6]
- G4 (P2) `soak_mode` unbuilt. **Re-triage 2026-05-27: cross-repo.** The BLRS config flag alone is inert — the actual
  CRITICAL→PagerDuty suppression lives in alerting-service's `recon_drift_event_handler`. BLRS is staging-only (F-21
  gated) so this is low-urgency. Producer-side flag + alerting-side suppression should land together → grouped with the
  alerting-service recon work (G12-adjacent). [→§7.1-2]
- G5 (P2) `threshold_distribution` calibration analyzer unbuilt. **Re-triage 2026-05-27:** the **bps** distribution is
  self-doable now (the bps gate is live; stage3 emits `alpha_pnl_gap_bps_{archetype}`). The **drawdown_pct + fill_rate**
  distributions depend on D3 (those gates aren't built → routed to Ikenna). Plan: build the bps analyzer now, extend for
  drawdown/fill once D3 lands. [→§7.1-3, §7.2 D3]
- G6 (P1/❓) drawdown_pct + fill_rate_min green gates unimplemented (no `stage4_risk_recon`). [→§7.2 D3]
- G7 (❓) Live recon machinery codex assigns to BLRS lives in 3 other repos; BLRS is T+1-only. [→§7.2 D1, §9.1]
- G8 (❓) PBMS merged into strategy-service/position 2026-05-20; BLRS makes no position-query call. [→§7.2 D2, §9.2]
- G9 ✅ RESOLVED (no-op) `AUTO_PAUSE_LIVE` is a **documented routing action** in the codex failure-routing closed set
  (`reconciliation-resolution.md`: alert / auto-pause-live / auto-demote-to-paper) — intentionally defined ahead of
  wiring, not dead code. Keep as-is. (Enum members don't trip unused-symbol lints.)
- G10 (P3) UI→resolution-API wiring (`unified-trading-system-ui` use-reports.ts hooks) unverified.
- G11 (P2/❓) Two `/reconciliation/resolve` APIs (BLRS mock + strategy-service real) — path collision. [→§7.2 D4, §5.5]
- G12 (**P0/cross-repo — bigger than BLRS**) **`RECON_FREEZE_ARMED` is never published by any service.** Both
  execution-service `recon_freeze.py` and codex reference it, but no code arms the freeze → the
  reconciliation→order-block safety chain is **dormant**. Only `position_drift_monitor` independently fires
  `KILL_SWITCH_ACTIVATED` on critical drift. This is a live-trading safety gap, not BLRS-owned; needs its own issue +
  operator visibility. [→§9.3]

---

## 7. Decisions ledger

### 7.1 ✅ Auto-decided (trivial — actioned/queued by auditor)

1. **Un-defer 3-way recon in codex.** `paper-vs-live-execution-seam.md` (Reconciliation §) and
   `reconciliation-resolution.md` (Stage DAG §) must stop calling `stage3b`/`stage3c` "DEFERRED" — they ship today.
   Rationale: code is the truth; both files predate the implementation. _Action: codex edit (separate commit)._
2. **SOAK_MODE via config not env.** When built, soak suppression must be a `ReconConfig` field (e.g.
   `soak_mode: bool`), never `os.getenv` — the codex calibration snippet shows an `os.getenv` that would violate the
   workspace ban. _Action: correct codex snippet; track build as P2._
3. **Fix calibration doc module path.** `batch_live_recon.analysis.threshold_distribution` →
   `batch_live_reconciliation_service.analysis.threshold_distribution` (module to be built).
4. **Resolution API → Stage-5 wiring is a required pre-activation gap (P1), not a redesign.** The mock backing is
   acceptable while BLRS is staging-only, but must read `index.json`/`summary_*.json` before F-21 prod activation.
   _Action: tracked G1._
5. **stage1 latency Δ:** implement timestamp-based delta or remove the metric — don't ship a hardcoded `0.0` into prod.
   _Action: tracked G2 (P2)._
6. **stage4 dispatch** remains a Phase-6 stub — consistent with codex "future". Keep markdown, track dispatch as P2.
   _Action: tracked G3._
7. **data-flow-map repo names** `trading-analytics-api`/`trading-analytics-ui` are stale → should be
   `unified-trading-api` + `unified-trading-system-ui`. Low-pri, not BLRS-owned. _Action: note for data-flow-map owner._

### 7.2 ❓ Needs operator input (material — see § "Decisions for you" in chat)

- **D1 — Ownership of live continuous reconciliation — ✅ DECIDED 2026-05-27 = (A).** Operator chose (A): BLRS stays
  **T+1-batch-only**; the codex is corrected to attribute live recon to the three repos that actually implement it. Zero
  code. **Done:**
  - `reconciliation-age-tracking.md` — ownership-correction banner + new "Component ownership" table; recovery-callback
    - continuous-verification sections rewritten (recovery_verifier is alerting-service's generic 5-bool aggregator, no
      recon-age gate / no BLRS registration; age fields produced by strategy-service/position; `check_oldest_age.py`
      never existed); `last_reviewed`→2026-05-27.
  - `incident-gateway-state-machine.md` — removed the BLRS recovery-callback row + correction note.
  - (rejected (B): centralising live recon into BLRS — large refactor against the 2026-05-20 PBMS→strategy-service
    merge, not worth it pre-May-23.)
    > **ROUTING 2026-05-27**: per operator, the heavy cross-cutting decisions below (D2, D3, D4) + the G12 safety gap
    > are **routed to ikenna-main** (`plans/active/_agent_pings.md` 2026-05-27 entry). G12 has its own issue doc
    > (`recon_freeze_armed_never_published_2026_05_27.md`). The bounded BLRS code gaps (G2/G4/G5) are being
    > self-completed.

- **D2 — Canonical position baseline: query strategy-service/position vs ratify event archives. → ROUTED TO IKENNA.**
  PBMS is no longer a repo (merged into strategy-service/position 2026-05-20), so codex's "PBMS query API" now means
  `position/api/routes/{pnl_series,positions_health}` + `/reconciliation/snapshots/history`. Either:
  - **(A)** BLRS calls the strategy-service/position query API for the canonical position baseline (codex-intent, real
    endpoints exist today, stronger correctness — a T+1 audit grounded on the canonical ledger).
  - **(B)** Ratify GCS event-archive reads as sufficient for a T+1 audit and amend the codex consumer matrix + the stale
    standalone-PBMS reference. _Lower effort; weaker canonical guarantee._
- **D4 — (new) Two `/reconciliation/resolve` APIs. → ROUTED TO IKENNA.** BLRS (mock) and strategy-service/position
  (real) both serve `POST /reconciliation/resolve` (§ 5.5). Options: (A) BLRS drops its resolution API and the UI uses
  strategy-service/position for live + a distinct BLRS path (e.g. `/t1-recon/breaks`) for batch; (B) namespace BLRS's
  routes under a `/t1/` prefix; (C) leave both (accept the collision, document which UI hook calls which). Recommend (A)
  or (B) before any UI wiring lands.
- **D3 — Are the drawdown_pct + fill_rate_min green gates in May-23 scope? → ROUTED TO IKENNA.** UAC
  `RECON_GREEN_THRESHOLDS` defines all three gates; only bps/slippage is wired. Build the drawdown + fill-rate gates now
  (needs a risk-recon step), or formally defer to post-cutover with a named successor.

---

## 8. Appendix — evidence index

- Stages 3b/3c exist: `batch_live_reconciliation_service/stages/stage3b_paper_live_recon.py`,
  `stage3c_batch_paper_recon.py` (vs codex "DEFERRED").
- No PBMS / recovery_verifier / check_oldest_age / SOAK_MODE / threshold_distribution: verified via `rg` across
  `batch_live_reconciliation_service/` + `scripts/` (2026-05-27) — zero hits.
- Cron: `deployment-service/terraform/gcp/t1_batch_scheduler.tf` (`0 6 * * *`), `audit03_cron_provisioning.tf`
  (`batch_live_recon_job`, args `--operation reconcile --mode batch`).
- Live recon elsewhere: `execution-service/execution_service/services/{yield,funding}_recon_engine.py`,
  `execution-service/.../preflight/recon_freeze.py`,
  `alerting-service/alerting_service/{recon_drift_event_handler.py,rules/reconciliation_rules.py}`.
- Codex sources: see frontmatter `source:`.

---

## 9. Deeper-dig findings (2026-05-27, pass 2)

Second pass after operator asked to dig deeper before deciding. These **supersede** the pass-1 framing of finding #2, #3
in § 0 and rows 2–3 in § 4 (already updated above).

### 9.1 The live reconciliation landscape — where it actually lives

Codex `reconciliation-age-tracking.md` reads as if BLRS is the home of live, continuous, 12-dimension reconciliation
with recon-freeze and a recovery verifier. **It is not — but the capability exists, distributed across three repos.**
End-to-end live chain:

```
DETECT          execution-service: funding_recon_engine.reconcile() (>10bps WARN / >50bps CRIT)
                                   yield_recon_engine.reconcile_{aave,lst,eigenlayer}() → RISK_ALERTS
                strategy-service/position: reconciliation_engine.reconcile_all_positions() (venue↔internal)
                                           position_drift_monitor (equity/delta drift; WARN 2% / CRIT 5%)
AGE-TRACK       strategy-service/position: ReconciliationSnapshot.{first_seen_at,unreconciled_age_seconds,dimension}
                                           deviation_tracker: TRANSIENT→CONFIRMED→AUTO_RECONCILED|ESCALATED→RESOLVED
ESCALATE        alerting-service: rules/reconciliation_rules.py
                  evaluate_recon_age()  → bands 0–5min none / 5–15 WARN / 15–30 INVESTIGATE / >30 CRITICAL
                  evaluate_immediate_sev0() → 7 overrides (UNKNOWN_NET_EXPOSURE, OPEN_ORDERS_UNCONFIRMABLE, …)
ARM FREEZE      ⚠️ GAP — execution-service recon_freeze.py has arm()/assert_not_frozen()/lift(), but
                NO service publishes RECON_FREEZE_ARMED. The freeze set is never populated. (§ 9.3, G12)
BLOCK ORDERS    execution-service: preflight/recon_freeze.ReconFreezeChecker.assert_not_frozen() (would block if armed)
RECOVER         alerting-service: gateway/recovery_verifier.py — generic 5-boolean DR aggregator (health/positions/
                orders/market-data/strategy-state). NOT reconciliation-age-specific; does NOT reference BLRS.
UNFREEZE        execution-service recon_freeze.lift() — HUMAN-ONLY (no auto-unfreeze)
```

Independent of the (dormant) freeze chain, `position_drift_monitor` **does** fire `KILL_SWITCH_ACTIVATED`
(STOP_NEW_ONLY) on CRITICAL drift today — so there is a live safety reflex, just not the codex-described recon-freeze
one.

**12 dimensions reality:** the full `ReconciliationDimension` enum (12 members) exists in
`unified_api_contracts/internal/reconciliation.py`, but only **2** are populated by any code: `POSITIONS` and `FEES`
(strategy-service/position). The other 10 (ORDERS, FILLS, BALANCES, FUNDING_PAYMENTS, TRANSFERS, BORROW_LENDING,
COLLATERAL, MARGIN_MODE, STRATEGY_ALLOCATION, ACCOUNT_AGGREGATE) are spec-only. → codex 12-dim claim is aspirational
workspace-wide, not just in BLRS.

### 9.2 PBMS is gone as a repo

`workspace-manifest.json:231`: _"position-balance-monitor-service dep removed 2026-05-20 (merged into
strategy-service/strategy_service/position/)."_ There is still a stale manifest stanza at line 1120 + a stale
`github_url` at 1159, and `unified-trading-api/services/pbm_performance.py` still HTTP-calls a
`position-balance-monitor-service` `/api/v1/accounts/{id}/pnl-series` endpoint (with a synth fallback). The real
endpoint is now served by strategy-service/position `api/routes/pnl_series.py`. **Codex `separation-of-concerns.md`
(reviewed 2026-05-17) predates the merge and still treats PBMS as a standalone repo** — its consumer matrix needs a
refresh (auto-decidable doc fix; queued as § 7.1-8 below).

### 9.3 ⚠️ Cross-repo safety gap — recon-freeze chain is dormant (G12, bigger than BLRS)

`execution-service/preflight/recon_freeze.py` is fully built (arm / assert_not_frozen / lift, thread-safe, human-only
lift) and its docstring says alerting-service publishes `RECON_FREEZE_ARMED` on critical recon age / immediate-SEV0.
**No code in alerting-service (or anywhere) publishes that event.** So the age-band CRITICAL and the 7 immediate-SEV0
overrides currently route to PagerDuty/Telegram **alerts only** — they never arm the freeze, so orders are never blocked
by reconciliation state. This is a live-trading safety gap on the May-23 critical path and is **not BLRS's to own**.
Recommend a dedicated issue doc + operator visibility; noting here because it surfaced during the recon audit.

### 9.4 BLRS→alerting coupling is T+1 batch replay (not live)

`alerting-service/subscribers/batch_event_reader.py` reads BLRS events from GCS JSONL
(`events/{service}/{date}/ events.jsonl`), not a live PubSub topic. Consistent with BLRS being a T+1 batch job; not a
defect, just confirming the coupling is daily, not real-time.

### 9.5 Net effect on the decisions

- **D1** → strongly favours (A): live recon is already built elsewhere; only the codex doc is wrong. (Updated § 7.2.)
- **D2** → the "PBMS API" is now strategy-service/position; (A) is feasible against real endpoints. (Updated § 7.2.)
- **D4 (new)** → resolution-API path collision needs resolving before UI wiring. (§ 5.5, § 7.2.)
- **G12 (new)** → recon-freeze dormancy is a separate, higher-severity cross-repo safety issue to escalate.

### 9.6 Pass-2 auto-decided additions

8. **Refresh `separation-of-concerns.md` PBMS rows.** Replace standalone-PBMS references with strategy-service/position;
   mark the merge (2026-05-20). Also flag the stale `workspace-manifest.json` PBMS stanza (lines 1120/1159) +
   `unified-trading-api/pbm_performance.py` endpoint base for the respective owners. _Doc fix._
