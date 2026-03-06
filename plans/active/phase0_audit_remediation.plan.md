---
name: "Phase 0 — Audit Remediation"
overview: |
  Companion to phase0_standards_enforcement.plan.md. Runs IN PARALLEL with enforcement during Phase 0.
  Converts every FAIL/WARN audit finding into a concrete, ordered task with file-level evidence.
  DOES NOT replace enforcement — enforcement scans and verifies; this plan fixes what enforcement finds.

  Sequencing: enforcement runs first (or concurrently) to establish the FAIL/WARN list.
  Remediation fixes FAIL items in Stream order (Stream 1→2→3→4→5). enforcement's p0-gate-check
  verifies remediation is complete. Both must reach DONE before Phase 1 starts.

  BLOCKS: Phase 1 Stream A, B, C — same gate as enforcement.
todos:
  - id: stream1-secrets-uci-uci-config
    content: "Stream 1 (unblocks everything): trading-analytics-ui .env removal; UCI 30+ os.environ → UnifiedCloudConfig bootstrap pattern; unified-config-interface 1 os.environ in loaders.py."
    status: pending
  - id: stream2-utl-fds
    content: "Stream 2 (after Stream 1 merges): unified-trading-library 50+ os.environ + try/except ImportError in aws_clients.py; features-delta-one-service try/except ImportError in _openbb_types.py."
    status: done
  - id: stream3-instruments-strategy-mlt-deploy
    content: "Stream 3 (parallel after Stream 2): instruments-service PYTEST_CURRENT_TEST antipattern + 68 type:ignore; strategy-service 3x try/except ImportError + create_presentation.py 1187L split; ml-training-service Dockerfile pip→uv; deployment-service env_substitutor.py boundary + scripts; deployment-api time.sleep in async."
    status: pending
  - id: stream4-exec-mtds-sports
    content: "Stream 4 (parallel after Stream 1): execution-service hardcoded project IDs + 5 oversized files + 139 type:ignore; market-tick-data-service hardcoded ID + os.environ scripts; features-sports-service _registry_data_b.py 1570L split."
    status: pending
  - id: stream5-warn-cleanup
    content: "Stream 5 (parallel, WARN cleanup): unified-market-interface 3 files >900L; execution-results-api 13 type:ignore; market-data-processing-service Any type; strategy-ui + batch-audit-ui .env hygiene; 8 services datetime TZ verification."
    status: done
isProject: true
blockedBy:
  - plan: phase0_standards_enforcement.plan.md
    reason: "Enforcement scan identifies the FAIL/WARN items that this plan fixes. Stream 1 can begin as soon as the initial scan is complete — does not need full enforcement to be done."
---

# Phase 0 — Audit Remediation Plan

## Relationship to phase0_standards_enforcement.plan.md

These are **two parallel Phase 0 companions, not competing plans:**

|            | phase0_standards_enforcement                        | phase0_audit_remediation (this plan)               |
| ---------- | --------------------------------------------------- | -------------------------------------------------- |
| **Role**   | Runs QG scans, establishes baseline, verifies fixes | Fixes each FAIL/WARN item with file-level evidence |
| **Output** | Pass/fail per repo; QUALITY_GATE_BYPASS_AUDIT.md    | Fixed code committed in Stream order               |
| **Gate**   | p0-gate-check verifies all fixes are in             | N/A — enforcement gate is the final arbiter        |
| **Start**  | Day 0, parallel with remediation                    | Day 0, can begin after Stream 1 scan results       |

**There is no circularity.** Enforcement DISCOVERS violations → remediation FIXES them → enforcement's gate check VERIFIES they are fixed. Both complete before Phase 1 starts.

## Context

A full-system audit (2026-03-04) scored the workspace **Grade D** across 53 repos.
13 repos have FAIL status; 16 have WARN. Phase 1 cannot start until all FAIL items are
resolved and WARN items are either fixed or formally deferred.

**Automatic-FAIL triggers found:**

- Secrets committed to git (`trading-analytics-ui/.env`)
- `try/except ImportError` in production source (2 files)
- `os.environ` in core library source (unified-cloud-interface: 29+, unified-trading-library: 50+)
- `time.sleep()` inside `async def` (deployment-api)
- Hardcoded project ID in source (market-tick-data-service)
- `.env` file committed (trading-analytics-ui)

---

## Plan Metadata

| Field       | Value                                                                    |
| ----------- | ------------------------------------------------------------------------ |
| **Plan ID** | phase0_audit_remediation                                                 |
| **Day**     | 0 (runs in parallel with phase0_standards_enforcement)                   |
| **Blocks**  | Phase 1 stream A, B, C                                                   |
| **Scope**   | 13 FAIL repos + 16 WARN repos                                            |
| **Gate**    | All FAIL items resolved; all WARN items resolved or deferred with ticket |

---

## Execution Order

Fix in dependency order — core libraries first, then services that import them.

```
Stream 1 (immediate, unblocks everything):
  trading-analytics-ui        ← secrets leak, 0 deps
  unified-cloud-interface     ← root config provider; 29+ os.environ; services depend on it
  unified-config-interface    ← 1 os.environ; depended on by all services

Stream 2 (after Stream 1 merges):
  unified-trading-library     ← 50+ os.environ, try/except ImportError; T1 library
  features-delta-one-service  ← os.environ + try/except ImportError

Stream 3 (parallel after Stream 2):
  instruments-service         ← 68x type:ignore + os.environ in app code
  strategy-service            ← try/except ImportError × 3 + file size
  ml-training-service         ← Dockerfile pip install
  deployment-service          ← 12× os.environ in scripts
  deployment-api              ← time.sleep() in async def

Stream 4 (parallel, can start after Stream 1):
  execution-service           ← 139x type:ignore + hardcoded IDs + file sizes
  market-tick-data-service    ← hardcoded project ID + os.environ in scripts
  features-sports-service     ← 1570-line file

Stream 5 (WARN cleanup, parallel):
  unified-market-interface    ← 3 files >900 lines
  execution-results-api       ← 13x type:ignore
  market-data-processing-service ← Any type + os.environ detection
  batch-audit-ui              ← placeholder Okta defaults
  strategy-ui                 ← .env.development not in .gitignore
  8x datetime TZ services     ← verify datetime.now(UTC) compliance
```

---

## Stream 1 — Immediate / Secrets / Root Config

### TASK 1.1 — `trading-analytics-ui` — Remove committed `.env`

**Grade:** F | **Type:** Automatic FAIL (secrets in git)

**Files:**

- `trading-analytics-ui/.env` — REMOVE from git tracking

**Steps:**

1. `git rm --cached .env` in trading-analytics-ui repo
2. Rename to `.env.example` with placeholder comments only
3. Add `.env` and `.env.` (except `.env.example`) to `.gitignore`
4. Verify no real credentials exist in file (current values are placeholders — safe)
5. Commit: `"fix(security): remove .env from git tracking, add .env.example template"`

**Done:** `.env` absent from git history on next push; `.gitignore` blocks re-commit.

---

### TASK 1.2 — `unified-cloud-interface` — Replace `os.environ` with config class

**Grade:** F | **Type:** Automatic FAIL (30+ violations in root config provider)

**Files (violations):**

- `unified_cloud_interface/factory.py:52,53,57,58,84,93,94,98,99,125,128,129`
- `unified_cloud_interface/providers/local.py:198,205,208,213,217,221,222,227`
- `unified_cloud_interface/constants.py:18,54,87,89,94,155`
- `unified_cloud_interface/providers/gcp.py:35,300,303,416`

**Fix pattern:**

- `os.environ.get("GCP_PROJECT_ID")` → `UnifiedCloudConfig().gcp_project_id`
- `os.environ.get("GCP_REGION", "us-central1")` → `UnifiedCloudConfig().gcp_region`
- Provider-detection fallbacks in `factory.py` → read from `UnifiedCloudConfig().cloud_provider`
- `constants.py` env lookups → promote to `UnifiedCloudConfig` fields with proper validation

**Note:** `unified-cloud-interface` IS the cloud config provider — it bootstraps before
`UnifiedCloudConfig` is fully available. For the bootstrap path only (provider detection),
use `os.environ.get()` is acceptable IF wrapped in a single `_detect_provider()` function
and documented with `# config-bootstrap: pre-UnifiedCloudConfig`. All other accesses must
use the config class.

**Done:** `rg "os\.environ" unified_cloud_interface/ --type py` returns 0 results outside
the single `_detect_provider()` bootstrap function.

---

### TASK 1.3 — `unified-config-interface` — Fix `os.environ` in loaders

**Grade:** D | **1 violation**

**Files:**

- `unified_config_interface/loaders.py:158` — `os.environ.items()` iteration

**Fix:** Replace direct `os.environ.items()` with an injected environment mapping parameter
with a default of `dict(os.environ)` at call site (loader receives a snapshot, not live access).

**Done:** `rg "os\.environ" unified_config_interface/ --type py` returns 0 results.

---

## Stream 2 — Core Library Hardening

### TASK 2.1 — `unified-trading-library` — `os.environ` + `try/except ImportError`

**Grade:** F | **50+ violations**

**Files (os.environ):**

- `unified_trading_library/core/client_factory.py:82,90,91,134,158,166,167,223`
- `unified_trading_library/core/cloud_constants.py:39,70,106,110,111,112,121,187,331,338,341,351`
- `unified_trading_library/core/cloud_auth_factory.py:146,152`
- `unified_trading_library/core/market_category.py:79,80`
- `unified_trading_library/core/cloud_data_provider.py:97`
- `unified_trading_library/__init__.py:67`
- `unified_trading_library/cli.py:113`
- `unified_trading_library/core/gcsfuse_helper.py:88,276`
- `unified_trading_library/core/secret_manager.py:192,310,315`

**File (try/except ImportError — BANNED):**

- `unified_trading_library/core/aws_clients.py:23`

**Fix pattern:**

- All `os.environ.get("KEY")` → `UnifiedCloudConfig().field_name`
- Extend `UnifiedCloudConfig` with any missing fields needed
- `aws_clients.py:23` → remove `try/except ImportError`; if boto3 is optional, declare it
  as an optional extra in pyproject.toml and guard with `importlib.util.find_spec("boto3") is not None`
  at module level (no fallback mock — fail loud)
- `testing/test_config_helpers.py` os.environ usage is acceptable (test helper, not prod)

**Done:** `rg "os\.environ" unified_trading_library/ --type py --glob '!**/testing/**' --glob '!**/tests/**'` = 0.

---

### TASK 2.2 — `features-delta-one-service` — `os.environ` + `try/except ImportError`

**Grade:** D

**Files:**

- `features_delta_one_service/app/calculators/_openbb_types.py` — `try/except ImportError` **BANNED**
- `examples/test_batch_features_real_data.py:23,26,30` — `os.environ` (examples dir)

**Fix:**

- `_openbb_types.py`: Remove `try/except ImportError`. If openbb is optional, use
  `importlib.util.find_spec("openbb")` guard with a hard `raise ImportError(...)` message.
- `examples/` os.environ usage: acceptable in examples — add `# noqa: S105` or move to
  test fixtures, but do NOT suppress with `# type: ignore`.

**Done:** `rg "except ImportError" features_delta_one_service/ --type py` = 0.

---

## Stream 3 — Service Hardening (Parallel after Stream 2)

### TASK 3.1 — `instruments-service` — `os.environ` + `# type: ignore` (68×)

**Grade:** F

**Files (os.environ in app code):**

- `instruments_service/app/core/cloud_instrument_storage.py:73,254`
- `instruments_service/app/core/cloud_data_provider.py:141`

These use `os.environ.get("PYTEST_CURRENT_TEST")` for pytest-detection — an anti-pattern.

**Fix (os.environ):** Inject a `testing_mode: bool = False` parameter at construction time.
In tests, pass `testing_mode=True` explicitly. Remove all `PYTEST_CURRENT_TEST` checks.

**Fix (type:ignore 68×):** Audit all 68 instances. Categorize:

- Legitimate pandas/ccxt/tardis API gaps → create `py.typed` stubs or use `cast()`
- Architectural violations → fix root cause, never suppress
- Target: reduce to ≤5 documented instances, each with a `# type: ignore[specific-code]`
  comment referencing a GitHub issue

**Done:** `rg "os\.environ\|PYTEST_CURRENT_TEST" instruments_service/app/ --type py` = 0.
`rg "# type: ignore" instruments_service/ --type py | wc -l` ≤ 5.

---

### TASK 3.2 — `strategy-service` — `try/except ImportError` (3×) + file size

**Grade:** F

**Files (try/except ImportError — BANNED):**

- `scripts/export_strategy_csvs.py:16–30` — matplotlib fallback
- `scripts/run_backtest_api.py:19–28` — ArchiveBacktestAdapter fallback
- `scripts/run_backtest_api.py:194–204` — mock mode fallback

**Fix (ImportError):** Scripts are NOT exempt from this rule. Remove all fallbacks.
If matplotlib is optional, add it as `[project.optional-dependencies.viz]` and
document the install requirement in the script header docstring.

**File (1187 lines):**

- `presentation/create_presentation.py` — split into:
  - `presentation/slides/data_loader.py`
  - `presentation/slides/chart_builder.py`
  - `presentation/slides/layout.py`
  - `presentation/create_presentation.py` (orchestrator only, ≤150 lines)

**Done:** `rg "except ImportError" strategy_service/ scripts/ --type py` = 0.
`wc -l presentation/create_presentation.py` ≤ 150.

---

### TASK 3.3 — `ml-training-service` — Dockerfile `pip install`

**Grade:** D

**File:**

- `Dockerfile:33` — `RUN pip install --no-cache-dir -e ".[dev]"`

**Fix:** Replace with:

```dockerfile
RUN uv pip install --system --no-cache -e ".[dev]"
```

**Done:** `grep "pip install" ml-training-service/Dockerfile` returns 0 non-uv matches.

---

### TASK 3.4 — `deployment-service` — 12× `os.environ`

**Grade:** F

**Files:**

- `deployment_service/config/env_substitutor.py:42` — core service code
- 11 instances in `scripts/` — automation scripts

**Fix (env_substitutor.py:42):** `env_substitutor.py` substitutes env vars into config
templates — this is a legitimate use. Wrap in a single `_get_env_snapshot() -> dict[str, str]`
function that reads `os.environ` once and documents it as the config substitution boundary.
All other access must go through the snapshot.

**Fix (scripts):** Replace `os.environ["GCP_PROJECT_ID"]` with a shared `_get_project_id()`
helper in `scripts/_common.py` that reads from `GCP_PROJECT_ID` with a hard fail if absent.

**Done:** `rg "os\.environ" deployment_service/ --type py --glob '!**/scripts/**'` = 0 (except documented boundary).

---

### TASK 3.5 — `deployment-api` — `time.sleep()` in `async def`

**Grade:** D

**File:**

- `deployment_api/routes/cloud_builds.py:565` — `time.sleep(2)`
- `deployment_api/routes/cloud_builds.py:574` — `time.sleep(1)`

**Fix:** Replace both with `await asyncio.sleep(N)`. Add `import asyncio` if not present.

**Done:** `rg "time\.sleep" deployment_api/ --type py` = 0.

---

## Stream 4 — Parallel Remediation (can start after Stream 1)

### TASK 4.1 — `execution-service` — `# type: ignore` (139×) + hardcoded IDs + file sizes

**Grade:** F

**Hardcoded IDs (fix first — automatic FAIL):**

- `scripts/generate_mock_defi_data.py:24` — `PROJECT_ID = "central-element-323112"`
- `scripts/check_tradfi_data_2023_05_23.py:20,21,37` — bucket/project literals
- 16 other script instances

**Fix (hardcoded IDs):** Create `scripts/_env.py`:

```python
import os
def get_project_id() -> str:
    pid = os.environ.get("GCP_PROJECT_ID")
    if not pid:
        raise RuntimeError("GCP_PROJECT_ID env var required")
    return pid
```

Replace all literal `"central-element-323112"` with `get_project_id()`.

**File sizes (fix blocking):**

- `execution_service/benchmark/comparison.py` (1092L) → split metrics/reporting
- `execution_service/cli/multi_leg_config.py` (994L) → split config/validation
- `execution_service/backtest/actors/signal_driven_v3.py` (953L) → split state/execution
- `execution_service/engine/backtest/preflight.py` (967L) → split checks/setup
- `execution_service/algorithms/impl/hybrid_optimal.py` (905L) → split strategy/math

**type:ignore (139×):** Audit and reduce. Target ≤10 documented instances.
Priority: fix architectural violations first (imports, schema boundaries); use `cast()` for
legitimate pandas/numpy type gaps.

**Done:** `rg "central-element" execution_service/ --type py` = 0.
All 5 files ≤ 900 lines. `rg "# type: ignore" execution_service/ --type py | wc -l` ≤ 10.

---

### TASK 4.2 — `market-tick-data-service` — Hardcoded project ID + `os.environ`

**Grade:** D

**Hardcoded ID (Automatic FAIL):**

- `scripts/test_unified_cloud_integration.py:206` — `"central-element-323112"`

**Fix:** Replace with `os.environ.get("GCP_PROJECT_ID", "test-project")` inside test
scripts, or use `get_project_id()` helper from env.py pattern above.

**os.environ (20+ in scripts):** Apply same `_env.py` helper pattern.

**Done:** `rg "central-element" market-tick-data-service/ --type py` = 0.

---

### TASK 4.3 — `features-sports-service` — File size 1570 lines

**Grade:** D

**File:**

- `features_sports_service/tracking/_registry_data_b.py` (1570 lines)

**Fix:** Split into logical modules:

- `_registry_data_b_fixtures.py` — fixture/team data
- `_registry_data_b_schedule.py` — schedule data
- `_registry_data_b_odds.py` — odds/market data
- `_registry_data_b.py` — re-export shim ≤50 lines

**Done:** `wc -l features_sports_service/tracking/_registry_data_b.py` ≤ 50 (shim only).

---

## Stream 5 — WARN Cleanup (Parallel)

### TASK 5.1 — `unified-market-interface` — 3 files >900 lines

**Grade:** B → target A

- `tardis_base_client.py` (936L) — split into `tardis_base_client.py` + `tardis_stream_client.py`
- `deribit_execution.py` (1020L) — split order types into `deribit_order_types.py`
- `lst_adapters.py` (985L) — split LST provider adapters into per-protocol files

---

### TASK 5.2 — `execution-results-api` — 13× `# type: ignore`

**Grade:** B → target A

Audit all 13 in `services/analysis_service.py` and `services/backtest_retrieval.py`.
Replace with `cast()` where appropriate. Document any remaining with `[specific-code]`.

---

### TASK 5.3 — `market-data-processing-service` — `Any` type + `os.environ` check

**Grade:** B

- `base_adapter.py:342,582` — replace `config: Any | None = None` with a typed Protocol
  or `BaseAdapterConfig` TypedDict
- `config.py:477` — `os.environ.get("VM_INSTANCE_NAME")` for VM detection is acceptable
  at the config boundary only; annotate with `# config-bootstrap: VM detection`

---

### TASK 5.4 — `strategy-ui` + `batch-audit-ui` — `.env` hygiene

**Grade:** B

- `strategy-ui`: Add `.env.development` and `.env.` (except `.env.example`) to `.gitignore`
- `batch-audit-ui/src/App.tsx:8-9`: Add code comment explaining placeholder defaults are
  intentional for `VITE_SKIP_AUTH=true` dev mode

---

### TASK 5.5 — Datetime TZ Verification (8 services)

**Grade:** B — verify then close

Run for each service:

```bash
rg "datetime\.now\(\)" <service>/ --type py --glob '!**/tests/**'
```

Services: `risk-and-exposure-service`, `pnl-attribution-service`, `position-balance-monitor-service`,
`ml-inference-service`, `features-cross-instrument-service`, `features-multi-timeframe-service`,
`features-onchain-service`, `features-volatility-service`.

If `datetime.now()` found with no arg → replace with `datetime.now(UTC)`.
If all calls already use `datetime.now(UTC)` → mark PASS, no change needed.

---

## Gate Criteria (Phase 0 Audit Remediation DONE)

All of the following must be true before Phase 1 Stream A starts:

| Check                                    | Command                                                                                                                                                                     | Expected                                          |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| No os.environ in prod library source     | `rg "os\.environ" unified-cloud-interface/ unified-config-interface/ unified-trading-library/ --type py --glob '!**/tests/**' --glob '!**/testing/**'`                      | 0 results (except documented bootstrap functions) |
| No try/except ImportError in prod source | `rg "except ImportError" unified-trading-library/ features-delta-one-service/ strategy-service/ execution-service/ --type py --glob '!**/tests/**' --glob '!**/scripts/**'` | 0 results                                         |
| No hardcoded project IDs                 | `rg "central-element-323112" --type py`                                                                                                                                     | 0 results                                         |
| No secrets in git                        | `git -C trading-analytics-ui ls-files .env`                                                                                                                                 | empty                                             |
| No time.sleep in async                   | `rg "time\.sleep" deployment-api/ --type py`                                                                                                                                | 0 results                                         |
| No pip install in Dockerfiles            | `grep -r "pip install" /Dockerfile                                                                                                                                          | grep -v "pip install uv"`                         |
| File size check                          | `find . -name "_.py" -not -path "_/.venv"                                                                                                                                   | xargs wc -l                                       |
| type:ignore total                        | `rg "# type: ignore" --type py --glob '!**/tests/**' --glob '!/.venv/'                                                                                                      | wc -l`                                            |
| quality-gates.sh passes                  | Run per-repo quality-gates                                                                                                                                                  | All repos green                                   |

---

## Files to Create/Modify (Summary)

| Action | Path                                                                                     |
| ------ | ---------------------------------------------------------------------------------------- |
| MODIFY | `unified-cloud-interface/unified_cloud_interface/factory.py`                             |
| MODIFY | `unified-cloud-interface/unified_cloud_interface/constants.py`                           |
| MODIFY | `unified-cloud-interface/unified_cloud_interface/providers/local.py`                     |
| MODIFY | `unified-cloud-interface/unified_cloud_interface/providers/gcp.py`                       |
| MODIFY | `unified-config-interface/unified_config_interface/loaders.py`                           |
| MODIFY | `unified-trading-library/unified_trading_library/core/*.py` (10 files)                   |
| MODIFY | `unified-trading-library/unified_trading_library/core/aws_clients.py`                    |
| MODIFY | `features-delta-one-service/features_delta_one_service/app/calculators/_openbb_types.py` |
| MODIFY | `instruments-service/instruments_service/app/core/cloud_instrument_storage.py`           |
| MODIFY | `instruments-service/instruments_service/app/core/cloud_data_provider.py`                |
| MODIFY | `strategy-service/scripts/export_strategy_csvs.py`                                       |
| MODIFY | `strategy-service/scripts/run_backtest_api.py`                                           |
| SPLIT  | `strategy-service/presentation/create_presentation.py` → 4 files                         |
| MODIFY | `ml-training-service/Dockerfile`                                                         |
| MODIFY | `deployment-service/deployment_service/config/env_substitutor.py`                        |
| CREATE | `deployment-service/scripts/_common.py`                                                  |
| MODIFY | `deployment-api/deployment_api/routes/cloud_builds.py`                                   |
| MODIFY | `execution-service/scripts/generate_mock_defi_data.py`                                   |
| CREATE | `execution-service/scripts/_env.py`                                                      |
| SPLIT  | `execution-service/execution_service/benchmark/comparison.py` → 2 files                  |
| SPLIT  | `execution-service/execution_service/cli/multi_leg_config.py` → 2 files                  |
| SPLIT  | `execution-service/execution_service/backtest/actors/signal_driven_v3.py` → 2 files      |
| SPLIT  | `execution-service/execution_service/engine/backtest/preflight.py` → 2 files             |
| SPLIT  | `execution-service/execution_service/algorithms/impl/hybrid_optimal.py` → 2 files        |
| MODIFY | `market-tick-data-service/scripts/test_unified_cloud_integration.py`                     |
| SPLIT  | `features-sports-service/features_sports_service/tracking/_registry_data_b.py` → 4 files |
| DELETE | `trading-analytics-ui/.env` (git rm --cached)                                            |
| CREATE | `trading-analytics-ui/.env.example`                                                      |
| MODIFY | `trading-analytics-ui/.gitignore`                                                        |
| MODIFY | `strategy-ui/.gitignore`                                                                 |

---

## Plan File Location

Once approved, save as:
`unified-trading-pm/plans/active/phase0_audit_remediation.plan.md`

Add to INDEX.md as Day 0, blocking Phase 1 stream A.
