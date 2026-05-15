---
title: "Workspace-wide deprecated-pattern sweep — type:ignore / noqa / os.getenv / ImportError fallbacks"
created: 2026-05-15
author: slot-8
source:
  - rg scans across all service/library repos (excluding .venv* / build / tests / scripts)
locked_by: live-defi-rollout
---

## What I found

Comprehensive scan across all workspace repos for four violation categories.

### 1. `# type: ignore` violations — 466 occurrences across 31 files

Top offenders (source files only, excluding tests/scripts):

| Repo                     | Count |
| ------------------------ | ----- |
| unified-trading-library  | 126   |
| features-service         | 107   |
| execution-service        | 66    |
| market-tick-data-service | 54    |
| deployment-api           | 16    |
| unified-api-contracts    | 15    |
| deployment-service       | 11    |
| instruments-service      | 10    |
| strategy-service         | 7     |

Most common suppression codes:

- `# type: ignore[arg-type]` — function argument type mismatch (likely fixed by proper typing)
- `# type: ignore[union-attr]` — union type not narrowed before attribute access
- `# type: ignore[attr-defined]` — accessing private/dynamic attributes (prometheus registry, native GCS client)
- `# type: ignore[import-untyped]` — third-party untyped libraries (`google.cloud.storage`, `pyarrow.parquet`, `pandas`)

Notable patterns:

- `# type: ignore[import-untyped]` for `google.cloud.storage` in UTL — these are in `client_lifecycle/onboarding.py` (a
  non-critical path) but violate the "use UCI, not direct cloud SDK" rule simultaneously
- `pd.Series` / `pd.DataFrame` without type args — use `pd.Series[Any]` or type-stub approach

### 2. `# noqa` suppressions — 1,376 occurrences (bare `# noqa` without code = most egregious)

Top offenders:

| Repo                     | Count |
| ------------------------ | ----- |
| market-tick-data-service | 297   |
| unified-trading-api      | 206   |
| execution-service        | 188   |
| unified-trading-library  | 163   |
| strategy-service         | 154   |

**Bare `# noqa` without error code** count: `rg "# noqa$" --type py` — these suppress ALL ruff warnings on a line,
masking future violations silently.

Most common suppressed codes (where specified):

- `PLC0415` (43) — import outside top level
- `C901` (22) — function too complex
- `B008` (18) — function calls in default args
- `BLE001` (14) — bare `except Exception` catch
- `E402` (13) — module-level import not at top

The `PLC0415` (43 occurrences) are the most concerning: these are `# noqa: PLC0415` on local imports, which is a pattern
the `no-empty-fallbacks.mdc` rule forbids (lazy imports that hide dependency issues).

### 3. `os.getenv()` violations — 4 source files (CLAUDE.md rules: use UnifiedCloudConfig)

| File                                                                               | Context                                                            |
| ---------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| `batch-live-reconciliation-service/batch_live_reconciliation_service/config.py`    | Config module — MUST use UnifiedCloudConfig                        |
| `new-sports-batting-services/footballbets/features/data_loader.py`                 | Data loader — MUST use UnifiedCloudConfig                          |
| `system-integration-tests/system_integration_tests/audit/checks/check_security.py` | Security audit — likely intentional (checking for os.getenv usage) |
| `unified-trading-library/unified_trading_library/startup_validation.py`            | Startup — needs review                                             |

### 4. `except ImportError` fallbacks — 56 occurrences across service source files

Worst offenders (source code, not scripts):

- `execution-service/execution_service/defi_execution/protocols/drift.py`
- `execution-service/execution_service/defi_execution/protocols/__init__.py`
- `market-tick-data-service/market_tick_data_service/adapters/hyperliquid_s3.py`
- `unified-trading-library/unified_trading_library/manifest_writer.py`
- `instruments-service/instruments_service/reference_data/adapters/tradfi/ibkr.py`

Most are optional dependency guards (`try: import drift_protocol; except ImportError: drift_protocol = None`). These are
banned by CLAUDE.md `no-empty-fallbacks.mdc` rule.

### 5. `sys.exit(1)` bare exits (exit-code audit) — 127 occurrences

Should be preceded by `log_event(..., "FAILED")` per CLAUDE.md lifecycle event requirements. Top offenders:

- `deployment-service` (20)
- `new-sports-batting-services` (17)
- `unified-trading-library` (7)
- `execution-service` (7)

## Why it matters

- `# type: ignore` violations mask type errors and accumulate over time — basedpyright strict mode should catch these
  once the underlying types are fixed. Current count (466) indicates systematic type system shortcuts.
- `noqa` suppressions hide ruff violations — 1,376 suppressions means the lint bar is effectively lowered for all these
  lines. The `PLC0415` suppressions are directly contradicting the `no-lazy-imports` rule.
- `os.getenv()` in config modules is a hard violation of the UnifiedCloudConfig requirement (QG STEP 5.x enforces this
  at build time but some repos may not have this STEP yet).
- `except ImportError` fallbacks create silent dependency failures and hide missing packages until runtime.
- Bare `sys.exit(1)` without `log_event FAILED` means these services exit without emitting the required lifecycle event,
  breaking the STARTED/STOPPED/FAILED monitoring contract.

## type:ignore slice — slot-2 progress (2026-05-15)

32 lazy `# type: ignore` suppressions removed, 5 repos with QG green:

| Repo                      | Count | SHA      | Notes                                                |
| ------------------------- | ----- | -------- | ---------------------------------------------------- |
| alerting-service          | 1     | 0718226  | defi_feature_event_handler + governance_forum_watcher |
| deployment-service        | 11    | 51be710  | ruff post-120 + type:ignore sweep                   |
| risk-and-exposure-service | 10    | 6d6abd2  | mock_data_provider + backtest_depeg_ladder           |
| strategy-service          | 7     | 7456dcb  | staked_basis identity, _safe_log_event, batch_utils  |
| execution-service         | 3     | cde5142f | sports fill_reports — negative→positive check pattern|

3+ repos threshold: ✅ (5 repos)  
50+ threshold: ❌ partial (32/50+) — 3 repos blocked by pre-existing QG failures:

- pnl-attribution-service: pip-audit CVEs (cryptography 46.0.5, urllib3 2.6.3, python-dotenv 1.2.1, pip 26.0.1) — 1 mock_data_provider no-any-return fix uncommitted
- position-balance-monitor-service: Pydantic/TypedDict schema placement + 10 codex violations — 1 fix uncommitted
- trading-agent-service: empty-string fallback + local BaseModel + pip-audit — 1 fix uncommitted

Deferred: 50+ threshold requires either pip-audit CVE upgrades workspace-wide OR adding more repos (UTL 126, features-service 107, MTDS 54, deployment-api 16 have remaining opportunities).

## Recommended decision

**Priority 1 (immediate, P1)**: Fix `os.getenv()` in `batch-live-reconciliation-service/config.py` — this is a core
config module. Use `UnifiedCloudConfig` instead.

**Priority 2 (P2, pre-cutover)**: Fix `except ImportError` in execution-service DeFi protocol modules (`drift.py`,
`__init__.py`) — these are in the May-23 critical path.

**Priority 3 (P3, sprint-aligned)**: Tackle `# type: ignore` in UTL (126 occurrences) — most are `union-attr` on cloud
client (can be fixed with proper narrowing) or `import-untyped` for pandas/pyarrow (add type stubs or use
`TYPE_CHECKING` guard).

**Priority 4 (P3)**: Audit all bare `# noqa` without error code; replace with explicit code or remove.

**Not recommended**: Mass-sweep of all 466 type:ignore at once — high risk of cascading type changes across repos. Fix
per-module with QG green gate after each repo.

**Owner**: Per-repo teams; batch-live-reconciliation-service P1 can be done in <30 min.
