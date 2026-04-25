---
title: "E2E Test: batch-live-reconciliation-service"
service: batch-live-reconciliation-service
date: 2026-03-22
status: pending
---

# E2E Test: batch-live-reconciliation-service

Follows `procedure.md`. Pipeline position: L6 monitoring (nightly T+1 reconciliation job).

## Service Characteristics

**T+1 nightly job.** Replays the entire batch pipeline for a given date and compares live data vs batch data to detect
drift and discrepancies. Runs as a Cloud Run Job on a nightly schedule.

- **NOT ServiceCLI-based** -- simple argparse with `--date`, `--dry-run`, `--log-level`
- **No `--operation`** -- single operation (reconciliation)
- **No `--mode`** -- effectively batch-only (nightly run)
- **No `--asset-group`** -- reconciles ALL domains in one run
- **Mock mode:** `ReconConfig().is_mock_mode()` checked before argparse (early exit)
- **CLI:** `python -m batch_live_reconciliation_service --date 2026-03-21 --dry-run`

## Pipeline Stages (6-stage sequential pipeline)

| Stage | Name            | What it does                                                 |
| ----- | --------------- | ------------------------------------------------------------ |
| 0     | Config pull     | Validates config + checks data availability for date         |
| 1     | ML recon        | Compares batch vs live ML predictions (direction match rate) |
| 2     | Strategy recon  | Compares batch vs live strategy signals                      |
| 3     | Execution recon | Compares batch vs live fills (fill rate, slippage)           |
| 4     | Agent analysis  | LLM-powered analysis of stage 1-3 deviations                 |
| 5     | Results writer  | Writes consolidated report to GCS                            |

Stage 0 failure aborts the pipeline. Stages 1-3 run independently. Stage 4 consumes stages 1-3. Stage 5 writes the final
report.

## Upstream Dependencies

| Source service       | What is read                       |
| -------------------- | ---------------------------------- |
| execution-service    | Fill records (batch vs live)       |
| strategy-service     | Signal records (batch vs live)     |
| ml-inference-service | Prediction records (batch vs live) |

## Deviation Thresholds

Defined in `batch_live_reconciliation_service/models/deviation_thresholds.py`:

- **ML:** `signal_direction_match_rate_min` -- minimum batch-vs-live direction agreement
- **Execution:** `slippage_delta_bps_max` -- maximum average slippage divergence

## Frontend API Surface

| Endpoint / view                       | What it feeds                          |
| ------------------------------------- | -------------------------------------- |
| Reconciliation tab in Reports service | Full recon report with stage breakdown |
| Batch/live drift charts               | Time-series deviation metrics          |
| Discrepancy tables                    | Per-instrument deviation detail        |
| `summary_gcs_path`                    | Link to GCS consolidated report        |
| `agent_report_gcs_path`               | Link to GCS LLM analysis report        |

## Test Matrix

### Phase 1: Startup Validation

| #   | Env vars / flags                                            | Expected                          | Status |
| --- | ----------------------------------------------------------- | --------------------------------- | ------ |
| 1.1 | `CLOUD_PROVIDER=gcp ENVIRONMENT=dev CLOUD_MOCK_MODE=false`  | OK                                |        |
| 1.2 | `CLOUD_PROVIDER=local ENVIRONMENT=dev CLOUD_MOCK_MODE=true` | OK (mock pipeline runs)           |        |
| 1.3 | `LOG_LEVEL=INVALID`                                         | SystemExit with valid values list |        |
| 1.4 | `--date not-a-date`                                         | ValueError from strptime          |        |
| 1.5 | No `--date` flag                                            | Defaults to yesterday             |        |
| 1.6 | `CLOUD_PROVIDER=azure`                                      | STARTUP_VALIDATION_FAILED         |        |

Note: Service does NOT use ServiceRuntime. Startup validation is limited to `LOG_LEVEL` enum check, date format
validation, and `ReconConfig()` Pydantic validation.

### Phase 2: Dry-Run (read-only validation)

| #   | Date       | Flags       | Expected                                                  | Status |
| --- | ---------- | ----------- | --------------------------------------------------------- | ------ |
| 2.1 | 2026-03-21 | `--dry-run` | All 6 stages run, no GCS writes, report returned          |        |
| 2.2 | 2026-03-21 | `--dry-run` | Stage 0 checks data availability (may fail if no data)    |        |
| 2.3 | 2026-03-21 | `--dry-run` | UEI events emitted: STARTED, per-stage, STOPPED/FAILED    |        |
| 2.4 | 1999-01-01 | `--dry-run` | Stage 0 fails (no data for ancient date), pipeline aborts |        |

### Phase 3: Real Writes (dev environment)

| #   | Date       | Flags  | GCS check                                                         | Status |
| --- | ---------- | ------ | ----------------------------------------------------------------- | ------ |
| 3.1 | 2026-03-21 | (none) | Stage 5 writes consolidated report to `recon-{project_id}` bucket |        |
| 3.2 | 2026-03-21 | (none) | Agent analysis report written to `agent_report_gcs_path`          |        |
| 3.3 | 2026-03-21 | (none) | Summary written to `summary_gcs_path`                             |        |
| 3.4 | 2026-03-21 | (none) | Events written to `{project_id}-events` bucket                    |        |

After each run, **verify GCS blobs directly** -- do not trust log output alone:

```python
from google.cloud import storage
client = storage.Client(project='central-element-323112')
bucket = client.bucket('recon-central-element-323112')
blobs = list(bucket.list_blobs(prefix='2026-03-21/', max_results=20))
for b in blobs[:10]:
    print(f'  {b.name} ({b.size:,} bytes)')
```

### Phase 4: Category Sweep

**Not applicable.** Batch-live-reconciliation-service reconciles ALL domains in a single run. There is no
`--asset-group` flag. Each stage (ML, Strategy, Execution) covers all instruments regardless of category.

However, verify that the reconciliation report includes data from multiple categories:

| #   | Check                                     | Expected                                     | Status |
| --- | ----------------------------------------- | -------------------------------------------- | ------ |
| 4.1 | ML recon covers CEFI + TRADFI predictions | Deviations (if any) span multiple categories |        |
| 4.2 | Execution recon covers CEFI + DEFI fills  | Fill comparison includes multi-venue fills   |        |
| 4.3 | Strategy recon covers all signal sources  | Signal comparison is category-agnostic       |        |

### Phase 5: Live Mode

**Not applicable.** This service is batch-only (T+1 nightly job). There is no `--mode live` flag.

The service runs once, produces a report, and exits. It does not maintain a persistent connection or subscription.

#### Phase 5b: Mock/Real A/B

| #    | Configuration                             | Expected behavior                                                                                                              | Status |
| ---- | ----------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------ |
| 5b.1 | `CLOUD_MOCK_MODE=true`                    | Mock pipeline: loads seed from execution + ml-inference services, runs REAL deviation detection, writes to `.local-dev-cache/` |        |
| 5b.2 | `CLOUD_MOCK_MODE=false --date 2026-03-21` | Real pipeline: reads GCS data for date, runs all 6 stages                                                                      |        |
| 5b.3 | `CLOUD_MOCK_MODE=true` (seed exists)      | Idempotent: "Seed data already present", returns 0                                                                             |        |
| 5b.4 | `CLOUD_MOCK_MODE=false --dry-run`         | Real data read, no GCS writes, report returned                                                                                 |        |

### Phase 6: Mock Mode (scenario testing)

Mock mode loads upstream data from `execution-service` and `ml-inference-service` seed directories, runs REAL deviation
detection against configured thresholds (`ML_THRESHOLDS`, `EXECUTION_THRESHOLDS`), and writes a reconciliation report to
`.local-dev-cache/mock-seed/batch-live-reconciliation-service/reports/`.

| #   | Scenario                           | What it tests                 | Expected                                                  | Status |
| --- | ---------------------------------- | ----------------------------- | --------------------------------------------------------- | ------ |
| 6.1 | Both upstreams seeded              | Full mock reconciliation      | ML + execution recon run, report written                  |        |
| 6.2 | Only execution-service seeded      | Partial upstream availability | ML recon SKIPPED, execution recon runs                    |        |
| 6.3 | No upstream seeds                  | Missing upstream data         | Both stages SKIPPED, report status PASSED (no deviations) |        |
| 6.4 | Seed already exists                | Idempotent re-run             | "Seed data already present" log, returns 0                |        |
| 6.5 | High slippage in fills seed        | Execution threshold breach    | `avg_slippage_bps` deviation recorded, status FAILED      |        |
| 6.6 | Low confidence in predictions seed | ML threshold breach           | `signal_direction_match_rate` deviation, status FAILED    |        |
| 6.7 | Verify `.seed-complete` marker     | Pipeline completion marker    | JSON with layer=7, overall_status, deviation_count        |        |
| 6.8 | Verify `reports/recon_report.json` | Report structure              | date, run_id, status, stages[], deviations[]              |        |

### Phase 7: Observability

| #   | Check                | Expected                                                   | Status |
| --- | -------------------- | ---------------------------------------------------------- | ------ |
| 7.1 | UEI lifecycle events | STARTED with date + run_id + dry_run                       |        |
| 7.2 | UEI completion event | STOPPED (passed) or FAILED (with failed_stages)            |        |
| 7.3 | Per-stage logging    | Each stage logs status + deviation count                   |        |
| 7.4 | GCSEventSink setup   | `setup_events()` called with events bucket                 |        |
| 7.5 | Exit code            | 0 = PASSED, 1 = FAILED                                     |        |
| 7.6 | Log format           | `%(asctime)s %(levelname)s %(name)s` with configured level |        |
| 7.7 | Stage 0 abort        | Pipeline aborts on stage 0 failure, logs reason            |        |

## Known Issues Audit

Before running tests, check for these patterns known from prior services:

| Pattern                      | What to check                                                                                       | Applies?                 |
| ---------------------------- | --------------------------------------------------------------------------------------------------- | ------------------------ |
| `load_dotenv(override=True)` | `.env` overrides shell env vars silently                                                            | Check                    |
| No ServiceRuntime            | Service uses raw argparse, not ServiceCLI/ServiceRuntime                                            | Yes -- by design         |
| Mock mode early exit         | `ReconConfig().is_mock_mode()` checked before argparse -- `--date`/`--dry-run` never parsed in mock | Check if problematic     |
| Bucket resolution            | `recon_bucket`, `events_bucket`, `execution_store_bucket` derived from `gcp_project_id`             | Verify derivation works  |
| No `--mode` flag             | Service is batch-only, but has no explicit mode flag                                                | OK -- by design          |
| `strptime` validation        | `--date` validated via `datetime.strptime` but error message may be cryptic                         | Check UX                 |
| `run_reconciliation()` sync  | Entire pipeline is synchronous (no asyncio) -- simpler than alerting-service                        | OK                       |
| Stage timeout                | `stage_timeout_seconds=1800` configured but not enforced in code                                    | Check if stages can hang |

## AWS Testing

Batch-live-reconciliation-service uses GCS for reading upstream data and writing reports. AWS equivalent would require:

- S3 for all bucket operations
- Different bucket naming convention

| #   | Test                                       | Expected                            | Status |
| --- | ------------------------------------------ | ----------------------------------- | ------ |
| A.1 | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=true`  | Mock pipeline runs (no cloud calls) |        |
| A.2 | `CLOUD_PROVIDER=aws CLOUD_MOCK_MODE=false` | UCI routes to S3 if wired           |        |

## Issues Found

(logged in `plans/active/issues/service_control_surface_issues_2026_03_21.md`)

| Issue | Severity | Fixed? |
| ----- | -------- | ------ |

## Next Service

After batch-live-reconciliation-service passes all phases -> proceed to the next service in pipeline order.
