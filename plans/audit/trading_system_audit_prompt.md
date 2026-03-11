# Unified Trading System — Production Readiness Audit Prompt

**Purpose:** Canonical prompt for evaluating whether the unified trading system workspace is ready for production and
free of regressions against institutional-grade standards. Run this prompt against the workspace to determine overall
production readiness. Covers all layers: governance, code quality, security, architecture, schema governance,
observability, deployment, technical debt, cross-repo alignment, CI/CD, UI/npm governance, tooling SSOT quality,
integration test coverage, coverage regression prevention, cloud-agnostic compliance, semver, data freshness,
performance, and autonomous agent infrastructure (Sections 1–28).

**Scope:** 65+ repos (services, libraries, UIs, APIs, infrastructure). Usable by human auditors and AI agents.

**SSOT:** `unified-trading-pm/plans/audit/trading_system_audit_prompt.md` Registered in
`unified-trading-codex/00-SSOT-INDEX.md` and `unified-trading-pm/00-SSOT-INDEX.md`.

**DO NOT ARCHIVE — used for continuous re-audits and production-readiness gates.**

---

## AUDITOR INSTRUCTIONS

You are auditing the unified trading system workspace for production readiness and regression detection. For each
section below, evaluate every listed criterion against the current state of the codebase. Return results in this format:

```
CATEGORY | CRITERION | STATUS | EVIDENCE
```

Where STATUS = `PASS` | `WARN` | `FAIL` | `N/A`.

At the end, output:

- **Overall grade:** `PASS` (0 FAILs) / `CONDITIONAL` (≥1 WARNs, 0 FAILs) / `FAIL` (≥1 FAILs)
- **Top 10 blocking findings** with file:line references
- **Technical debt trajectory** vs previous audit (if reports/audit\_<prev_date>.json exists)
- **Regression summary:** any section that regressed from PASS→WARN or PASS/WARN→FAIL since last run

**Analysis scope exclusions (apply to all sections):**

```bash
--glob '!.venv*' --glob '!**/.venv*/**' --glob '!node_modules/**'
--glob '!build/**' --glob '!dist/**' --glob '!*.egg-info/**'
```

---

## Section 1 — Workspace Governance

**Goal:** `workspace-manifest.json` is the authoritative source of truth for all registered repos, their tiers, CI
status, and dependency DAG. Every repo in the system is registered; the DAG is acyclic; all required fields are present.

**Audit commands:**

```bash
# Count registered repos
python3 -c "import json; m=json.load(open('unified-trading-pm/workspace-manifest.json')); print(len(m['repos']),'repos')"

# Validate DAG (acyclic)
python3 unified-trading-pm/scripts/validate-dag.py

# Check required fields
python3 -c "
import json
m = json.load(open('unified-trading-pm/workspace-manifest.json'))
required = ['name','arch_tier','ci_status','git_url','dependencies']
for r in m['repos']:
    missing = [f for f in required if f not in r]
    if missing: print('MISSING', r['name'], missing)
"

# Count cursor rules
ls unified-trading-pm/cursor-rules/**/*.mdc 2>/dev/null | wc -l
```

**Required state:**

| Criterion          | Requirement                                                      |
| ------------------ | ---------------------------------------------------------------- |
| Repos registered   | All known repos present; count matches expected (currently 65+)  |
| DAG validity       | No cycles; `validate-dag.py` exits 0                             |
| `arch_tier`        | T0–T5 present on every repo entry                                |
| `ci_status`        | Field present; value not blank                                   |
| `semver_rules_ref` | Present for all repos (added 2026-03-11 for semver audit trail)  |
| Cursor rules       | At least 100 rules present in `unified-trading-pm/cursor-rules/` |

**Scoring:** `PASS` — all criteria met. `WARN` — 1–3 repos missing optional fields. `FAIL` — any repo missing
`name`/`arch_tier`/`ci_status`/`dependencies`; OR DAG has cycles.

---

## Section 2 — Code Quality

**Goal:** All repos pass quality gates with calibrated thresholds. No file/function/class size violations. ruff and
basedpyright strict in all Python repos. Zero production-code uses of `os.getenv`.

**Audit commands:**

```bash
# Check quality-gates.sh stub size (>50 lines = violation)
wc -l */scripts/quality-gates.sh 2>/dev/null | sort -rn | awk '$1 > 50 {print "STUB VIOLATION:", $0}'

# Find function length violations (>200L)
rg '^\s+def ' --type py --glob '!.venv*' -n | \
  python3 unified-trading-pm/scripts/check-function-lengths.py --max 200

# Find os.getenv in non-bootstrap source
rg 'os\.getenv' --type py \
  --glob '!.venv*' --glob '!**/tests/**' \
  --glob '!**/factory.py' --glob '!**/bootstrap_config.py' \
  --glob '!**/constants.py'

# Check pyrightconfig.json excludes tests/ in all Python repos
for repo in */; do
  cfg="$repo/pyrightconfig.json"
  [ -f "$cfg" ] && python3 -c "
import json
c = json.load(open('$cfg'))
ex = c.get('exclude', [])
if 'tests' not in ex and 'tests/' not in ex:
    print('MISSING tests exclusion:', '$cfg')
" 2>/dev/null
done

# Check base-service.sh codex checks exclude tests/
grep -c '"!tests/\*\*"' unified-trading-pm/scripts/quality-gates-base/base-service.sh
# Must be ≥ 6
```

**Required state:**

| Criterion                    | Requirement                                                                     |
| ---------------------------- | ------------------------------------------------------------------------------- |
| `quality-gates.sh` stub size | ≤50 lines per repo (stub only, delegates to base-service/library/ui.sh)         |
| File length                  | <900 lines per source file                                                      |
| Function length              | <200 lines per function                                                         |
| Method length                | <50 lines per method                                                            |
| Class length                 | <900 lines per class                                                            |
| `os.getenv` in production    | Zero (only allowed in bootstrap: factory.py, bootstrap_config.py, constants.py) |
| `pyrightconfig.json`         | All Python repos have `"exclude": ["tests"]`                                    |
| Linter glob scope            | base-service.sh codex rg checks all use `--glob '!tests/**'`                    |
| `basedpyright` mode          | `strict` + `reportAny: error` in all `pyproject.toml`                           |

**Scoring:** `PASS` — zero violations. `WARN` — ≤5 violations with each tracked in an active plan. `FAIL` — any
full-body QG script (>50L); any `os.getenv` in non-bootstrap prod source; any repo using `pyright` instead of
`basedpyright`; OR `tests/` is typechecked or linted.

---

## Section 3 — Security

**Goal:** Zero hardcoded secrets. All secrets via `get_secret_client()`. All API services authenticated with proper
failure logging. No `verify=False` in HTTP clients. No mock auth in production paths.

**Audit commands:**

```bash
# Scan for hardcoded keys (exclude tests and example files)
rg '(api_key|secret_key|password|token)\s*=\s*["\'][a-zA-Z0-9+/]{20,}' \
  --type py --glob '!.venv*' --glob '!**/tests/**' -n

# Check AUTH_FAILURE event logging
rg 'AUTH_FAILURE' --type py --glob '!.venv*' --glob '!**/tests/**' -l

# Check verify=False in requests
rg 'verify\s*=\s*False' --type py --glob '!.venv*' --glob '!**/tests/**' -n

# Check SECRET_ACCESSED and CONFIG_CHANGED events
rg 'SECRET_ACCESSED|CONFIG_CHANGED' --type py --glob '!.venv*' -l
```

**Required state:**

| Criterion               | Requirement                                                                           |
| ----------------------- | ------------------------------------------------------------------------------------- |
| Hardcoded secrets       | Zero in production source (excluding test fixtures)                                   |
| Secret access           | All secrets via `get_secret_client(project_id, secret_name)`; no `os.getenv` fallback |
| HTTP verify             | No `verify=False` outside test code                                                   |
| API authentication      | All API services have auth middleware; 401 paths log `AUTH_FAILURE` event             |
| `SECRET_ACCESSED` event | Logged on every secret retrieval                                                      |
| `CONFIG_CHANGED` event  | Logged on every config mutation                                                       |
| Mock auth               | `DISABLE_AUTH` env flag does NOT affect production deployments                        |

**Scoring:** `PASS` — all criteria met. `WARN` — minor documentation gap. `FAIL` — any hardcoded secret; any 401 path
missing `AUTH_FAILURE`; any `verify=False`; OR `get_secret_client` bypassed with env var fallback.

---

## Section 4 — Architecture

**Goal:** Tier boundaries are respected. No cross-service Python imports. Cloud I/O is abstracted through UCI. All
services use batch-live symmetry (same engine, mode-switched transport).

**Audit commands:**

```bash
# No cross-service Python imports (T4 service importing another T4 service directly)
rg 'from (execution_service|strategy_service|risk_and_exposure_service|alerting_service|pnl_attribution_service)' \
  --type py --glob '!.venv*' --glob '!**/tests/**' -n

# No direct cloud SDK imports outside UCI / deployment-service
rg 'from google\.cloud|import boto3|from boto3' \
  --type py --glob '!.venv*' \
  --glob '!unified-cloud-interface/**' \
  --glob '!deployment-service/**' -n

# No GCS bucket name construction outside UCI
rg 'gcs_bucket|gs://' --type py --glob '!.venv*' \
  --glob '!unified-cloud-interface/**' -n
```

**Required state:**

| Criterion               | Requirement                                                                                        |
| ----------------------- | -------------------------------------------------------------------------------------------------- |
| Service→service imports | Zero cross-service Python imports in T4 repos                                                      |
| Cloud SDK confinement   | `google.cloud.*` and `boto3` only in `unified-cloud-interface/` and `deployment-service/backends/` |
| Cloud-agnostic I/O      | `get_storage_client()`, `get_secret_client()`, `CloudEventSink` used everywhere                    |
| Batch-live symmetry     | Same processing engine for batch and live; transport layer switches on `--mode`                    |
| UCI PubSub              | Services use `get_pubsub_client()` from UCI, not `google-cloud-pubsub` directly                    |
| Deployment API boundary | No direct `deployment_service` Python imports from other services                                  |

**Scoring:** `PASS` — zero violations. `FAIL` — any cross-service import; any direct cloud SDK outside UCI/deployment.

---

## Section 5 — Schema Governance

**Goal:** Clean separation between `unified-api-contracts` (external venue schemas) and `unified-internal-contracts`
(internal schemas). No float for price/monetary fields. No duplicated schemas across AC and UIC.

**Audit commands:**

```bash
# Check for float price fields in UIC/UAC schemas
rg 'float' unified-internal-contracts/unified_internal_contracts/ \
  unified-api-contracts/unified_api_contracts/ \
  --type py --glob '!.venv*' -n | \
  grep -v '# financial-ratio: float-ok\|# volatility-pct: float-ok\|# time-based: float-ok\|# pct: float-ok'

# Run Layer 0 contract alignment tests
cd unified-api-contracts && bash scripts/quality-gates.sh
```

**Required state:**

| Criterion               | Requirement                                                                                        |
| ----------------------- | -------------------------------------------------------------------------------------------------- |
| AC scope                | External venue schemas only (exchange responses, raw data formats)                                 |
| UIC scope               | Internal domain schemas only (canonical processed forms)                                           |
| No float price fields   | All price/monetary fields use `Decimal`; ratio/pct/time fields annotated with `# float-ok` comment |
| No AC/UIC duplication   | No schema class defined in both repos                                                              |
| Layer 0 tests           | `test_contract_alignment.py` + `test_ac_uic_alignment.py` pass                                     |
| Schema robustness tests | `test_schema_robustness.py` passes per-service                                                     |

**Scoring:** `PASS` — all criteria met. `WARN` — 1–2 float fields with `# float-ok` comment. `FAIL` — any price/monetary
field using `float`; any AC/UIC duplication; Layer 0 tests failing.

---

## Section 6 — Observability

**Goal:** All API services and long-running services expose health + readiness endpoints. Correlation IDs propagate
end-to-end. Prometheus metrics exported. Compliance events wired.

**Audit commands:**

```bash
# Check health + readiness endpoints
rg 'make_health_router\|/health\|/readiness' --type py \
  --glob '!.venv*' --glob '!**/tests/**' -l

# Check correlation_id propagation
rg 'correlation_id' --type py --glob '!.venv*' --glob '!**/tests/**' -l

# Check Prometheus metrics
rg 'prometheus_client\|Histogram\|Counter\|Gauge' --type py \
  --glob '!.venv*' --glob '!**/tests/**' -l

# Check MiFID/FCA compliance events
rg 'TRADE_EXECUTED\|ORDER_SUBMITTED\|COMPLIANCE' --type py \
  --glob '!.venv*' -l
```

**Required state:**

| Criterion               | Requirement                                                              |
| ----------------------- | ------------------------------------------------------------------------ |
| `/health` endpoint      | Present in all API services + long-running services                      |
| `/readiness` endpoint   | Present in all API services                                              |
| `correlation_id`        | Propagated end-to-end; logged on every request/event                     |
| Prometheus metrics      | Exported by all services; includes request latency histograms            |
| Grafana dashboards      | `trading-overview.json` + `system-health.json` present                   |
| Memory watchdog         | Pre-crash checkpoint at 85% memory in all long-running services          |
| MiFID/FCA compliance    | `TRADE_EXECUTED`, `ORDER_SUBMITTED` events logged with regulatory fields |
| `test_event_logging.py` | Present in 40+ repos                                                     |

**Scoring:** `PASS` — all criteria met. `WARN` — 1–2 services missing `/readiness`. `FAIL` — any service missing
`/health`; OR `correlation_id` not propagated; OR MiFID events absent.

---

## Section 7 — Deployment

**Goal:** Deployment checklist phases 1–7 complete per service. Runtime topology YAML accurate. Deployment pipeline gate
progression (infra → smoke → SIT → load → production) enforced.

**Audit commands:**

```bash
# Check deployment checklist presence per service
ls deployment-service/configs/checklist.*.yaml

# Check runtime-topology.yaml structure
python3 -c "
import yaml
t = yaml.safe_load(open('unified-trading-pm/configs/runtime-topology.yaml'))
required = ['version','deployment_profiles','clusters','service_flows']
missing = [k for k in required if k not in t]
print('MISSING:', missing) if missing else print('PASS: all keys present')
"

# Verify v1.0.0 tag readiness per repo (check pyproject.toml version field)
python3 -c "
import toml, pathlib
for p in pathlib.Path('.').glob('*/pyproject.toml'):
    try:
        v = toml.load(p)['project']['version']
        if not v.startswith('1.'):
            print('PRE-1.0.0:', p.parent.name, v)
    except: pass
"
```

**Required state:**

| Criterion                 | Requirement                                                            |
| ------------------------- | ---------------------------------------------------------------------- |
| Checklist phases 1–7      | Present in `deployment-service/configs/checklist.*.yaml` per service   |
| `runtime-topology.yaml`   | Has `version`, `deployment_profiles`, `clusters`, `service_flows` keys |
| Layer 2 infra verify      | `/infra/health` passes post-deploy                                     |
| Layer 3a smoke            | Passes in <5 min                                                       |
| Layer 3b full E2E         | Passes in 15–30 min                                                    |
| Pytest markers registered | `unit`, `integration`, `smoke`, `e2e` in all `pyproject.toml`          |

**Scoring:** `PASS` — all services have deployment checklist; topology YAML valid. `WARN` — 1–2 services pre-1.0.0 with
documented reasons. `FAIL` — any service without a checklist; OR topology YAML missing required keys.

---

## Section 8 — Technical Debt

**Goal:** All suppressions documented. Zero undocumented `type: ignore`. No `try/except ImportError` fallbacks. No
`.basedpyright-baseline.json` files without `QUALITY_GATE_BYPASS_AUDIT.md` entries.

**Audit commands:**

```bash
# Count type: ignore occurrences
rg '# type: ignore' --type py --glob '!.venv*' -n | wc -l
# Target: <10 total; each must be in QUALITY_GATE_BYPASS_AUDIT.md

# Find undocumented basedpyright baselines
find . -maxdepth 2 -name '.basedpyright-baseline.json' \
  ! -path './.venv*' ! -path './.venv-workspace*'
# Any hit is WARN minimum; check QUALITY_GATE_BYPASS_AUDIT.md for documentation

# Find try/except ImportError fallbacks
rg 'except ImportError' --type py --glob '!.venv*' --glob '!**/tests/**' -n

# Find noqa suppressions
rg '# noqa' --type py --glob '!.venv*' -n | wc -l
# Target: 0 in production source (use ruff config instead)
```

**Required state:**

| Criterion                          | Requirement                                                                               |
| ---------------------------------- | ----------------------------------------------------------------------------------------- |
| `# type: ignore` count             | <10 total; every occurrence in `QUALITY_GATE_BYPASS_AUDIT.md`                             |
| `.basedpyright-baseline.json`      | Zero target; each present file requires BYPASS_AUDIT.md entry (WARN); undocumented = FAIL |
| `try/except ImportError` fallbacks | Zero in production source (fail loud on missing imports)                                  |
| `QUALITY_GATE_BYPASS_AUDIT.md`     | Present in every repo that has any suppression                                            |
| `# noqa` suppressions              | Zero in production source                                                                 |

**Scoring:** `PASS` — zero suppressions. `WARN` — ≤10 `type: ignore` all documented; baseline files documented. `FAIL` —
any undocumented suppression; any `try/except ImportError`; any `# noqa` in production code.

---

## Section 9 — Cross-Repo Alignment

**Goal:** All active plans registered in `SSOT-INDEX.md`. `workspace-manifest.json` matches `runtime-topology.yaml`. No
orphan repos. Cursor rules consistent with codex.

**Audit commands:**

```bash
# Count active .plan.md files
ls unified-trading-pm/plans/active/*.plan.md | wc -l

# Check all are registered in codex SSOT-INDEX
python3 unified-trading-pm/scripts/validate-ssot-index.py

# Check manifest repos match topology
python3 unified-trading-pm/scripts/validate-alignment.py

# Count .mdc cursor rules
ls unified-trading-pm/cursor-rules/**/*.mdc 2>/dev/null | wc -l
ls .cursor/rules/*.mdc 2>/dev/null | wc -l
# Both counts should match (symlinks)
```

**Required state:**

| Criterion                 | Requirement                                                                    |
| ------------------------- | ------------------------------------------------------------------------------ |
| All plans in SSOT-INDEX   | Every `.plan.md` in `plans/active/` registered in `00-SSOT-INDEX.md`           |
| No phantom SSOT entries   | Every SSOT entry has a corresponding live file                                 |
| Manifest ↔ topology sync | All repos in manifest present in `runtime-topology.yaml`                       |
| Cursor rules in sync      | `unified-trading-pm/cursor-rules/` and `.cursor/rules/` have equal rule counts |
| No orphan repos           | Every repo with a `pyproject.toml` is in `workspace-manifest.json`             |

**Scoring:** `PASS` — all criteria met. `WARN` — 1–3 new plans not yet registered (grace period 24h). `FAIL` — any plan
unregistered for >24h; OR phantom SSOT entries; OR manifest/topology mismatch.

---

## Section 10 — Integration Test Coverage

**Goal:** Every repo with private deps (L2+) has `tests/integration/` with Layer 1.5 mock integration tests. All
interface repos have VCR cassettes validating external API schemas.

**Audit commands:**

```bash
# Check tests/integration/ presence in T3+ repos
python3 -c "
import json, pathlib
m = json.load(open('unified-trading-pm/workspace-manifest.json'))
for r in m['repos']:
    if int(str(r.get('arch_tier','0')).replace('T','')) >= 3:
        if not pathlib.Path(r['name'] + '/tests/integration').exists():
            print('MISSING integration:', r['name'])
"

# Check VCR cassettes in interface repos
for repo in unified-market-interface unified-trade-execution-interface \
            unified-reference-data-interface unified-position-interface \
            unified-sports-execution-interface unified-defi-execution-interface \
            unified-cloud-interface; do
  cassette_count=$(find $repo -name '*.yaml' -path '*/mocks/*' 2>/dev/null | wc -l)
  echo "$repo: $cassette_count cassettes"
done
```

**Required state:**

| Criterion                             | Requirement                                                                             |
| ------------------------------------- | --------------------------------------------------------------------------------------- |
| `tests/integration/` presence         | All T3+ repos (services, APIs) have at least 1 integration test                         |
| VCR cassettes in interface repos      | All 7 interface repos have cassettes in `unified_api_contracts_external/<venue>/mocks/` |
| Integration tests are credential-free | `CLOUD_MOCK_MODE=true`, no live API calls in quickmerge                                 |
| Layer 1.5 per dep boundary            | At least 1 integration test per private dependency boundary                             |

**Scoring:** `PASS` — all T3+ repos have integration tests; all interface repos have cassettes. `WARN` — 1–2 repos
missing but tracked in active plan. `FAIL` — any interface repo with zero cassettes; OR integration tests make live API
calls.

---

## Section 11 — Coverage Regression Prevention

**Goal:** Every repo's `MIN_COVERAGE` is calibrated to actual-1% (not default 70%). `pyproject.toml` `fail_under`
matches `MIN_COVERAGE`. `--cov-fail-under` is wired into the pytest invocation.

**Audit commands:**

```bash
# Check MIN_COVERAGE is calibrated (not default 70) for high-coverage repos
rg 'MIN_COVERAGE=' */scripts/quality-gates.sh | \
  awk -F= '{if ($2==70) print "DEFAULT (uncalibrated):", $0}'

# Verify fail_under matches MIN_COVERAGE per repo
python3 unified-trading-pm/scripts/check-coverage-alignment.py

# Verify --cov-fail-under is wired in base-service.sh
grep 'cov-fail-under' unified-trading-pm/scripts/quality-gates-base/base-service.sh
```

**Required state:**

| Criterion                     | Requirement                                                    |
| ----------------------------- | -------------------------------------------------------------- |
| `MIN_COVERAGE` calibrated     | Each repo with >70% actual coverage uses `actual_coverage - 1` |
| `pyproject.toml` `fail_under` | Matches `MIN_COVERAGE` exactly                                 |
| `--cov-fail-under` wired      | Passed to pytest in `base-service.sh`; not just declared       |
| Below-floor repos have plans  | Any repo with <70% coverage has a remediation plan active      |

**Scoring:** `PASS` — all calibrated; fail_under aligned; cov-fail-under wired. `WARN` — 1–3 repos still at default 70
but tracked for calibration. `FAIL` — `MIN_COVERAGE` declared but not passed to pytest; OR any repo above 70% actual
using default 70 threshold.

---

## Section 12 — Cloud-Agnostic API Compliance

**Goal:** No cloud-provider-specific code outside `unified-cloud-interface` and `deployment-service/backends`. All repos
use UCI abstractions for storage, secrets, PubSub, and config.

**Audit commands:**

```bash
# GCS bucket references outside UCI
rg 'gcs_bucket|upload_to_gcs|download_from_gcs' --type py \
  --glob '!unified-cloud-interface/**' --glob '!.venv*' -n

# Google Cloud imports outside UCI
rg 'from google\.cloud|import google\.cloud' --type py \
  --glob '!unified-cloud-interface/**' \
  --glob '!deployment-service/**' \
  --glob '!.venv*' -n

# boto3 imports outside deployment-service
rg 'import boto3|from boto3' --type py \
  --glob '!unified-cloud-interface/**' \
  --glob '!deployment-service/**' \
  --glob '!.venv*' -n

# BigQuery references outside UCI
rg 'bigquery_dataset|BigQueryClient' --type py \
  --glob '!unified-cloud-interface/**' --glob '!.venv*' -n
```

**Required state:**

| Criterion                       | Requirement                                                           |
| ------------------------------- | --------------------------------------------------------------------- |
| `google.cloud.*` imports        | Only in `unified-cloud-interface/` and `deployment-service/backends/` |
| `boto3` imports                 | Only in `unified-cloud-interface/` and `deployment-service/backends/` |
| `gcs_bucket`/`gs://` references | Only in `unified-cloud-interface/`                                    |
| `os.getenv` in cloud config     | Zero (use `UnifiedCloudConfig`); bootstrap exception only             |
| `get_pubsub_client()`           | All services use UCI PubSub abstraction                               |

**Scoring:** `PASS` — zero violations. `FAIL` — any banned pattern found in non-UCI/non-deployment source.

---

## Section 13 — No Unimplemented Stubs

**Goal:** Zero stub code in production source. A stub is any of:

| Pattern                         | Search                           | Allowed exception                                                                   |
| ------------------------------- | -------------------------------- | ----------------------------------------------------------------------------------- |
| `raise NotImplementedError`     | `rg 'raise NotImplementedError'` | Abstract base/Protocol methods where ALL concrete subclasses override               |
| `# TODO` / `# FIXME` / `# HACK` | `rg '# TODO\|# FIXME\|# HACK'`   | None — every TODO must be a plan todo or deleted                                    |
| `# STUB` / `# placeholder`      | `rg '# STUB\|# placeholder'`     | None                                                                                |
| `pass` as sole function body    | AST / manual                     | `__init__`, Protocol stubs, `except` handlers that intentionally swallow (must log) |
| `...` as function body          | `rg '^\s+\.\.\.$'`               | Protocol/ABC stubs only                                                             |

**Audit command (run per repo, from repo root):**

```bash
rg 'raise NotImplementedError|# TODO|# FIXME|# HACK|# STUB|# placeholder' \
  --type py \
  --glob '!.venv*' --glob '!**/.venv*/**' \
  --glob '!**/tests/**' --glob '!**/test_*' \
  --glob '!**/archive/**' --glob '!**/*.egg-info/**' \
  -n
```

**Scoring:**

- `PASS` — zero results
- `WARN` — ≤10 results total; each item has an open todo in an active plan (cite plan + todo ID)
- `FAIL` — any result with no owning active plan todo, OR total count > 10

**Reference plan:** `stub_completion_interfaces_and_infra.plan.md` — covers all known interface and infrastructure
stubs. Any new stub must be added to that plan or a relevant existing plan before the audit can score WARN.

---

## Section 14 — No Orphaned Code

**Goal:** Every public class, function, and schema is either used within the same repo or imported by a downstream repo
that declares this one as a dependency in `workspace-manifest.json`.

**Orphan categories:**

| Category                                            | Tool                                                                   |
| --------------------------------------------------- | ---------------------------------------------------------------------- |
| Unused Pydantic models / TypedDicts                 | `vulture <src_dir> --min-confidence 80`                                |
| Unused public functions (`def foo`, not `def _foo`) | `vulture` + cross-repo `rg`                                            |
| Unused Protocol implementations                     | class `C(Protocol)` with no consumer accepting `C` as a parameter type |
| Unused UAC/UIC schemas                              | schema class never imported by downstream service or interface repo    |
| Unused constants / module-level variables           | `vulture` + cross-repo `rg`                                            |

**Procedure:**

```bash
# Step 1 — run vulture per repo (workspace venv has vulture installed)
vulture <src_dir> --min-confidence 80

# Step 2 — for each finding, cross-check all downstream repos
rg '<SymbolName>' <downstream-repo-dirs> --type py -l

# If zero matches in step 2 → confirmed orphan
```

Downstream repos are determined by the `dependencies` field in `workspace-manifest.json` for the repo under audit.

**Exclusions (do not flag):**

- Symbols in `__all__` (public re-export surface)
- Protocol/ABC abstract method bodies
- Test fixtures and `conftest.py` helpers
- Symbols prefixed `_` (private by convention)
- Entry-point symbols registered via decorators (`@app.route`, `@router.get`, `@subscriber`, `@celery.task`,
  `@click.command`, etc.)
- `__init__`, `__repr__`, `__str__`, `__eq__` dunder methods

**Scoring:**

- `PASS` — zero confirmed orphans
- `WARN` — ≤5 confirmed orphans; each has a `# orphan: <reason>` comment OR an open plan todo
- `FAIL` — any confirmed orphan with no comment and no plan todo, OR total > 5

**Remediation:** Delete confirmed orphans immediately. If uncertain (consumer may be unregistered), add
`# orphan: kept because <reason>` comment and open a plan todo to track removal.

---

## Section 15 — CI/CD Pipeline Quality

**Goal:** Every repo's CI workflow runs QG in the same environment as local execution. Env mismatch is a silent failure
mode — tests pass locally but CI runs in a different Python/venv context and produces different results.

**Audit commands:**

```bash
# Check for --system installs (forbidden)
grep -r "uv pip install --system\|pip install --system\|pip install -r" \
  */.github/workflows/ --include="*.yml" -l

# Check for PATH export before QG call
grep -B2 "quality-gates.sh" */.github/workflows/quality-gates.yml | grep -L "PATH="

# Check CLOUD_MOCK_MODE is set
grep -L "CLOUD_MOCK_MODE" */.github/workflows/quality-gates.yml
```

**Required pattern (Python repos):**

```yaml
- name: Install dependencies
  run: |
    uv venv .venv
    uv pip install --python .venv/bin/python -e ".[dev]"
    uv pip install --python .venv/bin/python ruff basedpyright pytest pytest-cov

- name: Run quality gates
  env:
    CLOUD_MOCK_MODE: "true"
    GCP_PROJECT_ID: "test-project"
  run: |
    export PATH="$(pwd)/.venv/bin:$PATH"
    bash scripts/quality-gates.sh --no-fix
```

**Scoring:**

- `PASS` — all Python repos use `uv venv .venv` + `--python .venv/bin/python` + `PATH` export + `CLOUD_MOCK_MODE`
- `WARN` — any UI repo missing a CI quality gate step
- `FAIL` — any Python repo uses `--system`, bare `pip install`, or missing `PATH` export

---

## Section 16 — UI/npm Governance

**Goal:** All UI repos are governed by workspace-level version constraints and test standards. Previously there was no
audit coverage for UI repos beyond manifest registration.

**Audit commands:**

```bash
# Step 1 — check for stale package-lock (run from workspace root)
bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --ui-only --strict

# Step 2 — check canonical npm version alignment
python3 unified-trading-pm/scripts/propagation/rollout-npm-versions.py

# Step 3 — check test presence
for repo in */; do
  [ -f "$repo/package.json" ] && [ ! -f "$repo/pyproject.toml" ] && \
    grep -q '"test"' "$repo/package.json" || echo "NO TESTS: $repo"
done

# Step 4 — check workspace-manifest testing_level
python3 -c "
import json; m = json.load(open('unified-trading-pm/workspace-manifest.json'))
for r in m['repos']:
    if r.get('stack') == 'typescript' and r.get('testing_level') == 'none':
        print('FAIL:', r['name'])
"
```

**Required state per UI repo:**

| Criterion                  | Requirement                                                                                                            |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `package-lock.json`        | Present and not older than `package.json`                                                                              |
| `devDependencies`          | Match `workspace-npm-constraints.json` (typescript, vite, vitest, @vitest/coverage-v8, @testing-library/react, eslint) |
| Tests                      | At least 1 test file; `testing_level` ≠ `none` in manifest                                                             |
| `scripts/quality-gates.sh` | Thin stub (<50 lines) calling `base-ui.sh`                                                                             |
| CI workflow                | Calls `quality-gates.sh` or equivalent                                                                                 |

**Scoring:**

- `PASS` — all criteria met for all UI repos
- `WARN` — 1–2 repos missing test files; all others compliant
- `FAIL` — any UI repo has `testing_level: none`; OR stale `package-lock.json`; OR unconstrained devDependency versions

---

## Section 17 — Tooling SSOT & DRY Quality

**Goal:** Workspace tooling scripts (QG, version-alignment, quickmerge) are DRY, SSOT-governed, and maintainable.
Application-code quality standards (no duplication, single responsibility) apply equally to infrastructure scripts.

**Audit commands:**

```bash
# Find full-body QG scripts (violation: >50 lines = not a stub)
wc -l */scripts/quality-gates.sh 2>/dev/null | sort -rn | awk '$1 > 50 {print "VIOLATION:", $0}'

# Verify base scripts exist
ls unified-trading-pm/scripts/quality-gates-base/base-service.sh \
   unified-trading-pm/scripts/quality-gates-base/base-library.sh \
   unified-trading-pm/scripts/quality-gates-base/base-ui.sh

# Verify version-alignment steps present
grep -c "^\# 0\.[567]\|^\# [1-4]\." unified-trading-pm/scripts/repo-management/run-version-alignment.sh

# Verify npm constraints file exists
ls unified-trading-pm/workspace-npm-constraints.json
ls unified-trading-pm/scripts/propagation/rollout-npm-versions.py
```

**Required state:**

| Criterion                        | Requirement                                                                               |
| -------------------------------- | ----------------------------------------------------------------------------------------- |
| Per-repo `quality-gates.sh`      | Stub only: `source .../base-{service,library,ui}.sh` + required vars; <50 lines total     |
| `base-service.sh`                | Exists in `unified-trading-pm/scripts/quality-gates-base/`; SSOT for all service QG logic |
| `base-library.sh`                | Same; SSOT for library QG logic                                                           |
| `base-ui.sh`                     | Same; SSOT for UI QG logic                                                                |
| `run-version-alignment.sh`       | Contains steps 0.5 (symlinks), 0.6 (UI npm drift), 0.7 (npm versions), 1–4 (Python)       |
| `workspace-npm-constraints.json` | Exists; enforced by `rollout-npm-versions.py` in step 0.7                                 |
| Orphaned scripts                 | Zero scripts in `unified-trading-pm/scripts/` that are never called                       |

**Scoring:**

- `PASS` — all Python repos have `"exclude": ["tests"]` in pyrightconfig; base-service.sh has `!tests/**` on all codex
  checks; all QG scripts are stubs; all base scripts present; npm constraints enforced; no orphaned scripts
- `WARN` — 1–3 repos missing `pyrightconfig.json` test exclusion; or 1 orphaned script with explanation
- `FAIL` — any full-body QG script (>50 lines) in any repo; OR base scripts missing from PM; OR any codex check linting
  `tests/`; OR npm constraints file absent

---

## Section 18 — Semver Hardening & Major Version Bump Approval Gate

**Goal:** No agent may autonomously bump a MAJOR version. All MAJOR bumps (including `0.x.x → 1.0.0`) require human
approval via a GitHub Issue + Telegram alert → `/approve` comment → GHA workflow dispatch.

**Audit commands:**

```bash
# Verify cursor rule exists (priority 99)
ls unified-trading-pm/cursor-rules/workflow/major-bump-approval-required.mdc

# Check major-bump-issue-handler.yml present in all repos
python3 -c "
import json, pathlib
m = json.load(open('unified-trading-pm/workspace-manifest.json'))
for r in m['repos']:
    wf = pathlib.Path(r['name'] + '/.github/workflows/major-bump-issue-handler.yml')
    if not wf.exists():
        print('MISSING major-bump handler:', r['name'])
"

# Check semver_rules_ref field in manifest
python3 -c "
import json
m = json.load(open('unified-trading-pm/workspace-manifest.json'))
for r in m['repos']:
    if 'semver_rules_ref' not in r:
        print('MISSING semver_rules_ref:', r['name'])
"

# Check pre-1.0.0 override is enforced (feat!: on 0.x.x → MINOR, never MAJOR)
grep -l 'pre_1_0_0_override\|pre-1.0.0' \
  unified-trading-pm/.github/workflows/*.yml \
  */github/workflows/semver-agent.yml 2>/dev/null
```

**Required state:**

| Criterion                          | Requirement                                                            |
| ---------------------------------- | ---------------------------------------------------------------------- |
| `major-bump-approval-required.mdc` | Present with `alwaysApply: true`, `priority: 99`                       |
| `major-bump-issue-handler.yml`     | Present in all 65 repos; validates approver write access               |
| `semver_rules_ref` field           | In manifest for all repos; points to `docs/per-repo-semver-rules.yaml` |
| Pre-1.0.0 override                 | `feat!:` on 0.x.x bumps MINOR; never crosses to 1.0.0 automatically    |
| Semver-agent triggers              | Only on `staging` branch; never on `main` directly                     |
| Approval gate flow                 | GitHub Issue → Telegram alert → `/approve` → GHA bump                  |

**Scoring:** `PASS` — all criteria met. `WARN` — 1–5 repos missing `major-bump-issue-handler.yml` (tracked in
`major_version_bump_approval_gate_2026_03_11.plan.md`). `FAIL` — any agent that autonomously bumped a MAJOR version; OR
`semver-agent.yml` triggers on `main`; OR pre-1.0.0 override absent.

---

## Section 19 — Repository Readiness (CR/DR/BR Gates)

**Goal:** Every repo has a machine-readable readiness declaration across three axes: Code Readiness (CR), Deployment
Readiness (DR), Business Readiness (BR). The v1.0.0 gateway requires CR5 + DR3 + DR4 + BR2 + BR3 + BR4 + BR8.

**Audit commands:**

```bash
# Check per-repo readiness YAML files exist
python3 -c "
import json, pathlib
m = json.load(open('unified-trading-pm/workspace-manifest.json'))
for r in m['repos']:
    rpath = pathlib.Path('unified-trading-codex/10-audit/repos/' + r['name'] + '.yaml')
    if not rpath.exists():
        print('MISSING readiness file:', r['name'])
"

# Check canonical schema SSOT exists
ls unified-trading-codex/10-audit/REPO_READINESS_CHECKLIST.yaml

# Run automated verifier
python3 unified-trading-pm/scripts/check-repo-readiness.py --all
```

**Required state:**

| Criterion                   | Requirement                                                           |
| --------------------------- | --------------------------------------------------------------------- |
| Readiness schema SSOT       | `unified-trading-codex/10-audit/REPO_READINESS_CHECKLIST.yaml` v3.0   |
| Per-repo readiness YAML     | `codex/10-audit/repos/{repo-name}.yaml` for all 65 repos              |
| CR/DR/BR axes               | Each axis tracked independently; N/A items documented with reason     |
| v1.0.0 gateway gates        | CR5 + DR3 + DR4 + BR2 + BR3 + BR4 + BR8 all PASS before any 1.0.0 tag |
| `deployment_modes` declared | `batch`, `live`, or `both` per repo in readiness YAML                 |
| `.readiness-ref`            | Symlink in each repo pointing to codex canonical location             |

**Scoring:** `PASS` — all 65 repos have YAML files; verifier exits 0. `WARN` — 1–5 repos missing YAML (tracked in
`repo_readiness_semver_hardening_2026_03_11.plan.md`). `FAIL` — any repo reaches 1.0.0 without passing v1.0.0 gateway
gates; OR readiness schema SSOT absent.

---

## Section 20 — Live vs Batch Mode Protocol Completeness

**Goal:** All T4 services support both live and batch execution modes with symmetric outputs. No service is
single-mode-only without a documented exception.

**Audit commands:**

```bash
# Check live/batch handler presence per T4 service
python3 -c "
import json, pathlib
m = json.load(open('unified-trading-pm/workspace-manifest.json'))
for r in m['repos']:
    if r.get('arch_tier') == 'T4':
        has_live = bool(list(pathlib.Path(r['name']).glob('**/live*handler*.py')))
        has_batch = bool(list(pathlib.Path(r['name']).glob('**/batch*handler*.py')))
        if not (has_live and has_batch):
            print('MISSING handler:', r['name'], 'live=', has_live, 'batch=', has_batch)
" 2>/dev/null

# Check --mode CLI flag
rg '\-\-mode\s*(batch|live)' --type py \
  --glob '!.venv*' --glob '!**/tests/**' -l

# Check FreshnessMonitor wired in live handlers
rg 'FreshnessMonitor' --type py --glob '!.venv*' -l
```

**Required state:**

| Criterion                     | Requirement                                                        |
| ----------------------------- | ------------------------------------------------------------------ |
| Live mode handler             | `live_mode_handler.py` (or equivalent) per T4 service              |
| Batch mode handler            | `batch_handler.py` (or equivalent) per T4 service                  |
| `--mode` CLI flag             | Accepted by all T4 service entry points                            |
| Transport switching           | Live → PubSub; Batch → GCS (verified via `test_mode_switching.py`) |
| `FreshnessMonitor`            | Wired in all live handlers                                         |
| `test_batch_live_symmetry.py` | Present in SIT; verifies identical output schema for same input    |
| Codex documentation           | `batch-live-symmetry.md` in codex with reference implementations   |

**Scoring:** `PASS` — all T4 services have both handlers; mode switching tested. `WARN` — 1–2 services missing handler
with explicit single-mode exception documented. `FAIL` — any T4 service has only one transport handler without
documentation; OR `test_batch_live_symmetry.py` absent from SIT.

---

## Section 21 — Position Reconciliation & Order Recovery

**Goal:** The system can self-heal position discrepancies and orphaned orders without manual intervention.
Reconciliation, order recovery, and portfolio rebalancing are all automated with proper event emission.

**Audit commands:**

```bash
# Check reconciliation and recovery event emission
rg 'POSITION_CORRECTION_DISPATCHED|POSITION_CORRECTION_FAILED|ORDER_ORPHANED|ORDER_RECOVERY_COMPLETED|ORDER_RECOVERY_FAILED' \
  --type py --glob '!.venv*' -l

# Check OrderRecoveryEngine in execution-service
rg 'OrderRecoveryEngine|order_recovery' \
  execution-service/ --type py -n

# Check PortfolioRebalancer in strategy-service
rg 'PortfolioRebalancer|portfolio_rebalancer' \
  strategy-service/ --type py -n

# Check auto_correct threshold config
rg 'auto_correct_threshold_pct|auto_correct_enabled' --type py --glob '!.venv*' -n
```

**Required state:**

| Criterion                        | Requirement                                                           |
| -------------------------------- | --------------------------------------------------------------------- |
| `POSITION_CORRECTION_DISPATCHED` | Emitted on CRITICAL discrepancy (>auto_correct_threshold_pct)         |
| `ORDER_ORPHANED` event           | Emitted when orphaned order detected on startup                       |
| `ORDER_RECOVERY_COMPLETED` event | Emitted after successful orphan cancellation                          |
| `OrderRecoveryEngine`            | Present in execution-service; runs on startup                         |
| `PortfolioRebalancer`            | Present in strategy-service; triggered daily + on CRITICAL event      |
| `auto_correct_threshold_pct`     | Configurable via `ConfigStore`; default 1.0%; false by default in dev |
| Gas cost guard (DeFi)            | `DeFiVaultRebalancer` prevents rebalance if gas > yield improvement   |
| SIT chain test                   | Integration test verifying correction → recovery → rebalance chain    |

**Scoring:** `PASS` — all components present; events emitted correctly; SIT chain test passes. `WARN` — gas cost guard
missing but tracked in `recon_rebalancing_order_recovery_2026_03_10.plan.md`. `FAIL` — `OrderRecoveryEngine` absent; OR
position corrections not automated; OR UEI events not emitted.

---

## Section 22 — CI/CD Versioning & Multi-Project Cloud Build

**Goal:** Staging lock prevents concurrent version bumps during SIT. Semver happens exclusively at staging merge.
Multi-project Cloud Build routes images to correct environment. Immutable image tags.

**Audit commands:**

```bash
# Check manifest has staging_* fields
python3 -c "
import json
m = json.load(open('unified-trading-pm/workspace-manifest.json'))
required_fields = ['staging_versions', 'staging_status', 'staging_commits', 'main_commits', 'deployed_versions']
for f in required_fields:
    if f not in m:
        print('MISSING manifest field:', f)
"

# Check SIT-owned lock workflow
ls unified-trading-pm/.github/workflows/sit-gate.yml \
   unified-trading-pm/.github/workflows/sit-unlock.yml 2>/dev/null

# Verify Dockerfile uses uv sync --frozen
grep 'uv sync --frozen\|uv pip install' */Dockerfile 2>/dev/null | \
  grep 'uv pip install' | grep -v '#' | head -10
# Expected: zero results (all Dockerfiles should use uv sync --frozen)

# Check semver-agent only triggers on staging
grep -A3 'on:' */github/workflows/semver-agent.yml 2>/dev/null | \
  grep -v 'staging\|#'
# Should only see staging branch triggers
```

**Required state:**

| Criterion                          | Requirement                                                         |
| ---------------------------------- | ------------------------------------------------------------------- |
| `staging_versions` field           | Present in workspace-manifest.json; tracks per-repo staging version |
| `staging_status.locked`            | Set by SIT at start; cleared on pass/fail                           |
| Multi-project GCP Cloud Build      | `uts-dev`, `uts-staging`, `uts-prod` projects; immutable image tags |
| Image tag formula                  | main=`0.3.x`, staging=`0.3.x-staging`, feat=`0.3.x-feat-<slug>`     |
| Dockerfile uses `uv sync --frozen` | Never `uv pip install` in Dockerfile (ensures lockfile fidelity)    |
| Semver-agent scope                 | Triggers only on `staging` branch push; never `main`                |
| Staging→main merge                 | Uses `[skip ci]` to prevent re-running semver on main               |

**Scoring:** `PASS` — all criteria met; lock lifecycle works. `WARN` — 1–2 Dockerfiles still use `uv pip install`
(tracked in `cicd_versioning_cloud_build_2026_03_11.plan.md`). `FAIL` — staging lock absent; OR semver runs on main; OR
Dockerfile installs from URL (not lockfile).

---

## Section 23 — Autonomous Agent CI Infrastructure

**Goal:** Four specialized GHA workflows are wired and functional. Overnight orchestrator runs tier-ordered (T0→T4)
quality passes. All repos have ANTHROPIC_API_KEY and Telegram secrets. AGENTS.md and CLAUDE.md symlinks committed.

**Audit commands:**

```bash
# Check 4 core agent workflows exist in PM
ls unified-trading-pm/.github/workflows/semver-agent.yml \
   unified-trading-pm/.github/workflows/rules-alignment-agent.yml \
   unified-trading-pm/.github/workflows/codex-sync-agent.yml \
   unified-trading-pm/.github/workflows/plan-alignment-agent.yml 2>/dev/null

# Check overnight orchestrator
ls unified-trading-pm/.github/workflows/overnight-agent-orchestrator.yml 2>/dev/null

# Check AGENTS.md symlinks in all repos
python3 -c "
import pathlib
missing = [str(p.parent) for p in pathlib.Path('.').glob('*/.github')
           if not (p.parent / 'AGENTS.md').exists() and
              (p.parent / 'pyproject.toml').exists()]
print('MISSING AGENTS.md:', missing[:10]) if missing else print('PASS')
"

# Check CLAUDE.md symlinks
python3 -c "
import pathlib
missing = [str(p.parent) for p in pathlib.Path('.').glob('*/.github')
           if not (p.parent / '.claude/CLAUDE.md').exists()]
print('MISSING CLAUDE.md:', missing[:10]) if missing else print('PASS')
"
```

**Required state:**

| Criterion                          | Requirement                                                                 |
| ---------------------------------- | --------------------------------------------------------------------------- |
| `semver-agent.yml`                 | Present in PM; triggers on staging push                                     |
| `rules-alignment-agent.yml`        | Present in PM; verifies rules/AGENTS.md/CLAUDE.md consistency               |
| `codex-sync-agent.yml`             | Present in codex; triggers on manifest-updated dispatch                     |
| `plan-alignment-agent.yml`         | Present in PM; validates INDEX.md ↔ active plans ↔ SSOT-INDEX alignment   |
| `overnight-agent-orchestrator.yml` | Present; cron 01:00 UTC; tier-ordered (T0→T4); 3x retry on failure          |
| `AGENTS.md` in all repos           | Workspace-generic, not PM-specific; includes full rules + mandatory cleanup |
| `.claude/CLAUDE.md` in all repos   | Symlink to canonical `unified-trading-pm/cursor-configs/CLAUDE.md`          |
| `ANTHROPIC_API_KEY` secret         | Set on all repos for agent execution                                        |
| Telegram secrets                   | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` on all repos                      |

**Scoring:** `PASS` — all 4 workflows present; overnight orchestrator wired; all repos have AGENTS.md + CLAUDE.md.
`WARN` — 1–5 repos missing AGENTS.md (rollout in progress). `FAIL` — overnight orchestrator absent; OR semver-agent
missing; OR `ANTHROPIC_API_KEY` not propagated.

---

## Section 24 — API Key & VCR Cassette Coverage

**Goal:** All 30 external data sources have API keys in Secret Manager and VCR cassettes (or documented equivalents). No
live API calls in tests. `ENDPOINT_REGISTRY` in `unified-api-contracts` tracks cassette status per venue.

**Audit commands:**

```bash
# Count ENDPOINT_REGISTRY entries
python3 -c "
from unified_api_contracts.endpoint_registry import ENDPOINT_REGISTRY
print(len(ENDPOINT_REGISTRY), 'endpoints registered')
" 2>/dev/null || echo "Check ENDPOINT_REGISTRY in unified-api-contracts/"

# Count cassettes per interface repo
for repo in unified-market-interface unified-trade-execution-interface \
            unified-reference-data-interface unified-position-interface; do
  count=$(find $repo -name '*.yaml' -path '*/mocks/*' 2>/dev/null | wc -l)
  echo "$repo: $count cassettes"
done

# Check for hardcoded API keys
rg 'api_key\s*=\s*["\'][a-zA-Z0-9_-]{20,}' --type py \
  --glob '!.venv*' --glob '!**/tests/**' -n

# Verify all secret access via get_secret_client (no os.getenv fallback)
rg 'os\.getenv.*[Kk]ey\|os\.getenv.*[Ss]ecret\|os\.getenv.*[Tt]oken' \
  --type py --glob '!.venv*' --glob '!**/tests/**' -n
```

**Required state:**

| Criterion                      | Requirement                                                                   |
| ------------------------------ | ----------------------------------------------------------------------------- |
| Hardcoded API keys             | Zero in production source                                                     |
| Secret access pattern          | All via `get_secret_client(project_id, secret_name)`; no `os.getenv` fallback |
| `ENDPOINT_REGISTRY`            | ≥55 venues; each has `CassetteStatus` enum value                              |
| Phase 1–3 sources              | All have SM entries + cassette definitions committed                          |
| Free sources                   | All have cassettes; zero live calls in tests                                  |
| `@responses.activate` for REST | Used in all DeFi/HTTP tests; `passthrough=False`                              |
| WS tests                       | Use `MockWebSocketFeed`; no live WS connections in tests                      |

**Scoring:** `PASS` — all phases 1–3 complete; ENDPOINT_REGISTRY ≥55; zero hardcoded keys. `WARN` — phases 4–5
incomplete but tracked in `api_keys_and_auth.plan.md`. `FAIL` — any hardcoded key; OR live API calls in tests; OR
`os.getenv` fallback for secret access.

---

## Section 25 — Data Freshness Monitoring & Availability Expectations

**Goal:** Every data source has a declared freshness contract. All data-producing services emit staleness events.
Consuming services gate on data freshness before processing.

**Audit commands:**

```bash
# Check DataFreshnessContract definitions
rg 'DataFreshnessContract' --type py --glob '!.venv*' -l

# Check FreshnessMonitor in data-producing services
for svc in market-tick-data-service market-data-processing-service \
           features-delta-one-service features-calendar-service \
           features-volatility-service features-onchain-service \
           features-commodity-service features-cross-instrument-service \
           features-sports-service; do
  count=$(rg 'FreshnessMonitor' $svc/ --type py 2>/dev/null | wc -l)
  echo "$svc: FreshnessMonitor=$count"
done

# Check DATA_STALE and FEED_UNHEALTHY events
rg 'DATA_STALE|FEED_UNHEALTHY|DATA_AVAILABILITY_RESTORED|DATA_GAP_DETECTED|DATA_COMPLETENESS_CHECK' \
  --type py --glob '!.venv*' -l

# Check freshness gate in consuming services
rg 'assert_feature_fresh\|assert_market_data_fresh\|DataStalenessError' \
  strategy-service/ execution-service/ --type py -n
```

**Required state:**

| Criterion                          | Requirement                                                                                 |
| ---------------------------------- | ------------------------------------------------------------------------------------------- |
| `DataFreshnessContract`            | Defined for all 30 data sources in `unified-internal-contracts/reference/data_freshness.py` |
| `FreshnessMonitor`                 | Wired in all 9 data-producing services                                                      |
| `DATA_STALE` event                 | Emitted when age > `warn_age_seconds`                                                       |
| `FEED_UNHEALTHY` event             | Emitted when age > `max_age_seconds`; triggers PagerDuty + Telegram                         |
| `DATA_AVAILABILITY_RESTORED` event | Emitted when feed recovers                                                                  |
| Freshness gates in consumers       | `strategy-service` + `execution-service` raise `DataStalenessError`                         |
| Daily completeness check           | `check-data-completeness.sh` scheduled via Cloud Scheduler 08:00 UTC                        |
| SIT test                           | Injects artificial staleness; verifies `FEED_UNHEALTHY` emission                            |

**Scoring:** `PASS` — all criteria met. `WARN` — 1–2 data sources missing `DataFreshnessContract` (tracked in
`data_availability_live_expectations_2026_03_10.plan.md`). `FAIL` — freshness gates absent from consuming services; OR
`FEED_UNHEALTHY` not wired to alerts.

---

## Section 26 — Performance Testing & Load Benchmarks

**Goal:** All critical execution paths have documented p50/p95/p99/max latency targets. Load test scenarios (normal,
peak, sustained) are defined and automated. Regressions vs baseline trigger Telegram alerts.

**Audit commands:**

```bash
# Check performance targets document
ls unified-trading-codex/06-coding-standards/performance-targets.md 2>/dev/null

# Check SIT performance tests
ls system-integration-tests/tests/performance/ 2>/dev/null | wc -l
# Expected: ≥8 test files

# Check baseline file exists
ls system-integration-tests/baselines/baseline.json 2>/dev/null

# Check nightly performance workflow
ls unified-trading-pm/.github/workflows/performance-test.yml 2>/dev/null ||
ls system-integration-tests/.github/workflows/performance-test.yml 2>/dev/null

# Check execution-service has p99 assertions
rg 'p99\|assert.*latency\|assert.*percentile' \
  execution-service/tests/ --type py -n | head -20
```

**Required state:**

| Criterion                  | Requirement                                                           |
| -------------------------- | --------------------------------------------------------------------- |
| `performance-targets.md`   | Documents p50/p95/p99/max for all critical paths                      |
| Order submission p99       | ≤500ms (production readiness gate)                                    |
| Signal generation p99      | ≤1000ms                                                               |
| ML inference p99           | ≤250ms                                                                |
| Tick ingestion throughput  | ≥1000 ticks/s                                                         |
| SIT performance test suite | ≥8 test files covering all critical paths                             |
| `baseline.json`            | Present; nightly workflow detects >20% regression                     |
| Load scenarios             | `NORMAL_LOAD`, `PEAK_LOAD` (5×), `SUSTAINED_PEAK` (5× for 1h) defined |
| Nightly performance CI     | `performance-test.yml` with Telegram regression alert                 |

**Scoring:** `PASS` — all criteria met; no baseline regressions. `WARN` — SIT performance suite exists but <8 tests; or
baseline >20% regression detected but tracked. `FAIL` — no `performance-targets.md`; OR p99 order submission

> 500ms; OR no performance tests at all.

---

## Section 27 — Contract Completeness & Adoption Verification

**Goal:** All public symbols in `unified-internal-contracts` (UIC) and `unified-api-contracts` (UAC) `__all__` are
consumed by at least one downstream service. All symbols defined in source are in `__all__` or explicitly in
`KNOWN_INTERNAL` allowlist.

**Audit commands:**

```bash
# Run UIC completeness check
python3 unified-internal-contracts/scripts/check_uic_completeness.py
# Expected: 0 missing from __all__

# Run UAC completeness check
python3 unified-api-contracts/scripts/check_uac_completeness.py
# Expected: 0 unclassified symbols

# Run adoption checkers (inverse direction)
python3 unified-trading-pm/scripts/check_uic_adoption.py
python3 unified-trading-pm/scripts/check_uac_adoption.py
python3 unified-trading-pm/scripts/check_utl_adoption.py

# Run SIT completeness tests
cd system-integration-tests && python3 -m pytest tests/contracts/ -v --tb=short
```

**Required state:**

| Criterion                  | Requirement                                                              |
| -------------------------- | ------------------------------------------------------------------------ |
| UIC `__all__` completeness | All public UIC classes in `__all__`; 0 missing (target: 195+ entries)    |
| UAC `__all__` completeness | All public UAC classes either in `__all__` or `KNOWN_INTERNAL` allowlist |
| UIC adoption               | Every `__all__` entry has ≥1 terminal consumer                           |
| UAC adoption               | Every `__all__` entry has ≥1 terminal consumer                           |
| UTL adoption               | Every exported UTL function has ≥1 caller                                |
| SIT completeness tests     | `test_uic_completeness.py` + `test_uac_completeness.py` pass             |
| GHA smoke-test-gate.yml    | Completeness check steps present (warn-mode, non-blocking)               |

**Scoring:** `PASS` — all checkers exit 0; SIT tests pass. `WARN` — UAC curation backlog exists but tracked in
`contract_completeness_checker_2026_03_10.plan.md`. `FAIL` — UIC has missing `__all__` entries; OR any `__all__` symbol
has zero consumers; OR SIT completeness tests failing.

---

## Section 28 — E2E Smoke, Portable Backtests & Integration Layer Completeness

**Goal:** The 5-layer integration test hierarchy is intact. All 4 asset-class portable backtests pass with deterministic
outputs. No external API calls in SIT. Portable backtests verify batch-live symmetry.

**Audit commands:**

```bash
# Check Layer 0 contract alignment tests
cd unified-api-contracts && python3 -m pytest tests/test_cassette_schema_parity.py -v

# Check Layer 3a smoke tests
ls system-integration-tests/tests/smoke/ | wc -l

# Check Layer 3b e2e tests
ls system-integration-tests/tests/e2e/ | wc -l

# Check portable backtests
ls system-integration-tests/tests/backtests/ 2>/dev/null
# Expected: cefi_backtest.py, tradfi_backtest.py, defi_backtest.py, sports_arb_backtest.py

# Verify deterministic backtest outputs
cd system-integration-tests && python3 -m pytest tests/backtests/ -v --tb=short
```

**Required state:**

| Criterion                     | Requirement                                                          |
| ----------------------------- | -------------------------------------------------------------------- |
| Layer 0 contract alignment    | `test_cassette_schema_parity.py` passes; runs on every commit        |
| Layer 1.5 per dep boundary    | ≥1 integration test per private dependency boundary in all T3+ repos |
| Layer 3a smoke tests          | ≥10 smoke tests in SIT; run in <5 min                                |
| Layer 3b e2e tests            | ≥5 e2e tests in SIT                                                  |
| CeFi portable backtest        | 11 trades; deterministic pnl; <2s runtime; no live API               |
| TradFi portable backtest      | 2 trades; deterministic pnl; <2s runtime                             |
| DeFi portable backtest        | 20 trades; deterministic pnl; <2s runtime; VCR cassettes             |
| Sports arb portable backtest  | 2 trades; deterministic pnl; <2s runtime                             |
| No external API calls in SIT  | `pytest --block-network` passes for all SIT tests                    |
| Batch-live symmetry assertion | Each backtest verifies identical output between batch and live modes |

**Scoring:** `PASS` — all 4 backtests pass; Layer 3a smoke passes in <5 min; no live API calls. `WARN` — 1–2 backtests
not yet implemented (tracked in `e2e_smoke_and_portable_backtests.plan.md`). `FAIL` — any backtest makes live API calls;
OR batch/live outputs differ; OR Layer 0 contract tests failing.

---

## Key SSOT References for Auditors

- **Repo registry & DAG:** `unified-trading-pm/workspace-manifest.json`
- **Deployment configs (canonical):** `deployment-service/configs/` — checklist._.yaml, venues.yaml,
  RUNTIME_TOPOLOGY_DECISIONS.md, data-catalogue._.yaml, per-service PROTOCOL\_\* env files
- **Runtime topology (canonical SSOT):** `unified-trading-pm/configs/runtime-topology.yaml`
- **Coverage targets:** `unified-trading-pm/cursor-rules/testing/test-coverage-targets.mdc`
- **Stub tracker:** `unified-trading-pm/plans/active/stub_completion_interfaces_and_infra.plan.md`
- **Performance targets:** `unified-trading-codex/06-coding-standards/performance-targets.md`
- **Semver rules:** `unified-trading-pm/plans/active/major_version_bump_approval_gate_2026_03_11.plan.md`
- **Readiness checklist:** `unified-trading-codex/10-audit/REPO_READINESS_CHECKLIST.yaml`
- **Data freshness contracts:** `unified-internal-contracts/reference/data_freshness.py`
- **Batch-live symmetry:** `unified-trading-codex/batch-live-symmetry.md`
- **API key phases:** `unified-trading-pm/plans/active/api_keys_and_auth.plan.md`
- **Previous audit reports:** `system-integration-tests/reports/audit_<date>.json`
