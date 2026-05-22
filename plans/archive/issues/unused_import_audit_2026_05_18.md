---
title: "Workspace unused-import audit — 2026-05-18"
created: 2026-05-18
source:
  - work_split_2026_05_18_harsh.md § slot-4 item 15
locked_by: live-defi-rollout
priority: P2
status: active
---

> **[ACKED-INTO-PLAN]** Archived 2026-05-22. 11 F401 violations tracked as P3 todos in
> `plans/active/strategy_execution_contract_remediation_2026_05_20.md` (execution-service),
> `plans/active/instruments_backfill_phase3_2026_05_22.md` (instruments-service), and
> `plans/active/mtds_backfill_phase3_2026_05_22.md` (market-tick-data-service). Low-priority lint debt.
> deployment-service re-exports intentional — do not fix.

> **[ACKED-INTO-PLAN]** Archived 2026-05-22. 11 F401 violations tracked as P3 todos in `plans/active/strategy_execution_contract_remediation_2026_05_20.md` (execution-service), `plans/active/instruments_backfill_phase3_2026_05_22.md` (instruments-service), and `plans/active/mtds_backfill_phase3_2026_05_22.md` (market-tick-data-service). Low-priority lint debt. deployment-service re-exports intentional — do not fix.

## What I found

Ruff F401 scan across 12 active Python service repos (2026-05-18). All violations are `[*]` (auto-fixable by ruff).
Summary:

| Repo                     | Violations | Files                                                                                                                                                                            | Fixable now?                                                                        |
| ------------------------ | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| deployment-service       | 4          | `configs/generate_topology_svg.py:33`                                                                                                                                            | ❌ SKIP — explicit re-export comment; intentional                                   |
| execution-service        | 4          | `scripts/run_execution_alpha_measurement.py` (os, BenchmarkFillInput) · `scripts/run_execution_alpha_parallel.py` (json, tempfile)                                               | ❌ BLOCKED — slot 2 in-flight (11 foreign dirty files + pre-existing lint failures) |
| instruments-service      | 5          | `tests/scripts/test_canonicalize_defi_manifest_data_types_2026_05_16.py` (contextlib, os, tempfile, pytest) · `tests/scripts/test_reconcile_lending_indices_phantom.py` (pytest) | ❌ BLOCKED — foreign dirty files + pre-existing lint failures                       |
| market-tick-data-service | 2          | `tests/unit/test_drift_solana_ws_connector.py` (json) · `tests/unit/test_kraken_futures_ws_connector.py` (json)                                                                  | ❌ BLOCKED — slot 9 in-flight (14 foreign dirty files)                              |
| All others (8 repos)     | 0          | —                                                                                                                                                                                | ✅ clean                                                                            |

### Repos scanned (0 violations)

alerting-service, alerting-service, batch-live-reconciliation-service, ml-inference-service, pnl-attribution-service,
risk-and-exposure-service, strategy-service, system-integration-tests.

## Why it matters

Low-severity lint debt (no correctness risk). The 11 fixable violations in 3 repos are all trivially removed by
`ruff check --select F401 --fix <file>`. Verified locally — auto-fix applies cleanly with no downstream breakage.

## Recommended decision

Next slot that picks up one of these repos in a clean session can apply the 1-line ruff fix:

```bash
# For each repo, after verifying git status is clean:
ruff check --select F401 --fix <affected_files>
# Then run QG + commit
```

**Priority**: P3 (cosmetic lint — no correctness or coverage impact).

**Ownership routing**:

- execution-service `scripts/` → slot 2 (lint surface) or any slot with clean execution-service window
- instruments-service `tests/scripts/` → any instruments-service slot with clean window
- market-tick-data-service `tests/unit/` → slot 9 or any MTDS slot with clean window
- deployment-service re-exports → intentional, DO NOT fix
