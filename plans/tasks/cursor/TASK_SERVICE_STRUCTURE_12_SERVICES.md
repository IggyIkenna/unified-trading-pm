# Task: Service Structure Standardization (12 Services)

**Source plan**: `.cursor/plans/service_structure_standardization_4a4b3ff3.md` **Scope**: All 14 Python services EXCEPT
instruments-service and market-tick-data-handler → **12 services**.

**Codex refs**:

- `unified-trading-/codex/06-coding-standards/cli-standards.md` — CLI pattern (--operation, --mode)
- `unified-trading-/codex/06-coding-standards/service-structure-standards.md` — engine/, adapters/, cli/
- `unified-trading-/codex/06-coding-standards/thin-adapters-pattern.md` — Adapters <100 lines, delegate to
  UTL/UMI/UCI/UEI

---

## Completed Items (Verify Only)

Do a quick sanity check; do not redo:

- **Phase 0.1**: unified-trading-library has `ErrorWarningCounter`, `get_dataframe_memory_usage`, `log_memory_metrics`
  in `observability/`.
- **Phase 0.2**: unified-config-interface has ConfigStore / TimeSeriesConfigStore (see `persistence.py`,
  `CONFIG_STORE.md`).
- **Phase 0.4**: Codex has `cli-standards.md` and `service-structure-standards.md`.

---

## Services and Operations (from codex)

| Service                          | Operations                                     | Mode                                |
| -------------------------------- | ---------------------------------------------- | ----------------------------------- |
| market-data-processing-service   | `process`                                      | batch, live                         |
| pnl-attribution-service          | `compute`                                      | batch, live                         |
| features-calendar-service        | `compute`                                      | batch, live                         |
| features-delta-one-service       | `compute`                                      | batch, live                         |
| features-volatility-service      | `compute`                                      | batch, live                         |
| features-onchain-service         | `compute`                                      | batch, live                         |
| ml-training-service              | `train_phase1`, `train_phase2`, `train_phase3` | batch, live                         |
| ml-inference-service             | `infer`                                        | batch, live                         |
| strategy-service                 | `backtest`, `live_trade`                       | batch (backtest), live (live_trade) |
| execution-service                | `execute`                                      | live only                           |
| risk-and-exposure-service        | `compute`                                      | batch, live                         |
| position-balance-monitor-service | `monitor`                                      | batch, live                         |

---

## Per-Service Execution

For each assigned service:

### 1. CLI (Phase 1)

- Add or normalize **--operation** (required, service-specific choices as above) and **--mode** (required, choices:
  `batch`, `live`; execution-service: `live` only).
- Batch: support `--start-date`, `--end-date` where applicable. Live: support `--interval` (e.g. minutes) where
  applicable.
- In `cli/main.py` (or equivalent): dispatch by `args.operation` to the right handler; then run handler with `args.mode`
  (batch vs live). No duplicate logic: one code path using `args.operation` and `args.mode`.
- If the service currently uses subparsers (e.g. `process`, `train`), refactor to flags: `--operation process` /
  `--operation train_phase1` etc., and `--mode batch` or `--mode live`.
- Optional backward compatibility: at parse time only, map deprecated `--mode X` (e.g. old operation names) to
  `--operation X` and `--mode batch` with a deprecation warning; then require both flags.

### 2. Structure (Phase 3)

- Create `{service_module}/engine/` and `{service_module}/adapters/` if missing.
- Move business logic from `app/core/` (or equivalent) into `engine/` (orchestrators, processors, validation). **No I/O
  in engine**: no GCS, no API calls, no storage.
- Extract I/O into **thin** adapters in `adapters/`: e.g. `data_source.py`, `data_sink.py` (or `storage_adapter.py`).
  Adapters must delegate to unified-trading-library (e.g. `get_storage_client`), unified-market-interface,
  unified-config-interface, unified-trading-library. Each adapter file <100 lines; no business logic.
- Ensure `engine/` has **zero** imports from `adapters/`. Dependencies point inward: adapters → engine.
- Keep or add `cli/handlers/` for operation-specific handlers; each handler orchestrates engine + adapters. If the
  service has only one entry (e.g. one batch handler), one handler under `cli/handlers/` is fine (e.g.
  `compute_handler.py`).
- features-calendar-service: plan says it has `cli/batch_handler.py` only — move to `cli/handlers/` (e.g.
  `batch_handler.py` or `compute_handler.py`) for consistency.
- Update all imports and tests so they reference new paths. No circular imports.

### 3. Quality Gates

- Run `bash scripts/quality-gates.sh` then `bash scripts/quality-gates.sh --no-fix` in the service repo.
- Fix all failures (lint, type, tests, file size, etc.). Do not skip or bypass.

### 4. Observability (if missing)

- Prefer `log_event` and lifecycle events from `unified_trading_library.events`.
- If the service has a local error/warning counter, replace with `ErrorWarningCounter` from
  `unified_trading_library.events`; use `get_dataframe_memory_usage` / `log_memory_metrics` from UEI for DataFrame
  memory.

---

## Agent Assignments (4 agents, 3 services each)

- **Agent 1**: market-data-processing-service, pnl-attribution-service, features-calendar-service
- **Agent 2**: features-delta-one-service, features-volatility-service, features-onchain-service
- **Agent 3**: ml-training-service, ml-inference-service, strategy-service
- **Agent 4**: execution-service, risk-and-exposure-service, position-balance-monitor-service

Each agent returns: for each service, (1) done / not done, (2) CLI and structure changes summary, (3) quality gates
pass/fail and any remaining issues.
