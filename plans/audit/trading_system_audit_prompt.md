# Unified Trading System — Production Readiness Audit Prompt

**Purpose:** Canonical prompt for evaluating whether the unified trading system workspace is ready for production and
free of regressions against institutional-grade standards. Run this prompt against the workspace to determine overall
production readiness. Covers all layers: governance, code quality, security, architecture, schema governance,
observability, deployment, technical debt, cross-repo alignment, CI/CD, UI/npm governance, tooling SSOT quality,
integration test coverage, coverage regression prevention, cloud-agnostic compliance, semver, data freshness,
performance, autonomous agent infrastructure, API domain coverage, configuration architecture, infrastructure pattern
facilitation, and format string safety (Sections 1–32).

**Scope:** ~33 active repos (services, libraries, UIs, APIs, infrastructure). Usable by human auditors and AI agents.

**SSOT:** `unified-trading-pm/plans/audit/trading_system_audit_prompt.md` Registered in
`unified-trading-pm/codex/00-SSOT-INDEX.md` and `unified-trading-pm/00-SSOT-INDEX.md`.

**DO NOT ARCHIVE — used for continuous re-audits and production-readiness gates.**

---

## AGENT FAST-PATH — Run Scripts First (~80% of audit, no runaway processes)

Before doing any ad-hoc analysis, run the pre-built audit scripts. They use `rg`/`grep`/`find` exclusively (no Python
DOTALL regex — avoids catastrophic backtracking and runaway processes).

```bash
# Full scriptable audit (§1, §2, §3, §4/12, §6, §8, §9, §11, §13, §27):
bash unified-trading-pm/scripts/audit/run-audit-scriptable.sh

# Single section:
bash unified-trading-pm/scripts/audit/run-audit-scriptable.sh --sections 3

# Section scoped to one repo:
bash unified-trading-pm/scripts/audit/run-audit-scriptable.sh --sections 13 --repo execution-service

# Individual section scripts (all in unified-trading-pm/scripts/audit/):
bash unified-trading-pm/scripts/audit/s01-governance.sh
bash unified-trading-pm/scripts/audit/s02-code-quality.sh
bash unified-trading-pm/scripts/audit/s03-security.sh
bash unified-trading-pm/scripts/audit/s04-architecture.sh   # also covers §12
bash unified-trading-pm/scripts/audit/s06-observability.sh
bash unified-trading-pm/scripts/audit/s08-tech-debt.sh
bash unified-trading-pm/scripts/audit/s09-cross-repo.sh
bash unified-trading-pm/scripts/audit/s11-coverage.sh
bash unified-trading-pm/scripts/audit/s13-stubs.sh
bash unified-trading-pm/scripts/audit/s27-contracts.sh
```

**Sections requiring semantic review** (no script — read section and reason manually): §5 Schema Governance · §7
Deployment · §10 Integration Tests · §14 Orphaned Code · §15-16 CI/CD + UI · §17 Tooling SSOT · §18 Semver · §19
Readiness Gates · §20-26 Domain/Perf/E2E

**NEVER write `python3 << 'EOF'` heredocs for file searching** — use `rg` or the scripts above. Inline Python with
`re.DOTALL` + nested quantifiers causes catastrophic backtracking (12–22 hour runaway processes have occurred on this
machine from this exact pattern).

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
| Repos registered   | All known repos present; count matches expected (currently ~33)  |
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
failure logging and full auth event coverage. No `verify=False` in HTTP clients. No mock auth in production paths. No
broad `except Exception` in production code.

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

# Check full auth event set (beyond AUTH_FAILURE)
# execution-service auth.py must emit: AUTH_SUCCESS (first-per-session), AUTH_FAILURE, AUTH_DENIED
# execution-service auth_s2s.py must emit: S2S_AUTH_SUCCESS, S2S_AUTH_FAILURE
for event in AUTH_SUCCESS AUTH_FAILURE AUTH_DENIED S2S_AUTH_SUCCESS S2S_AUTH_FAILURE; do
  hits=$(rg "$event" execution-service/ --type py --glob '!**/tests/**' -l 2>/dev/null | wc -l)
  [ "$hits" -eq 0 ] && echo "MISSING auth event: $event in execution-service"
done

# Check AUTH_FAILURE event in ALL API services (not just execution-service)
           risk-and-exposure-service client-reporting-api trading-analytics-api \
           ml-inference-api ml-training-api deployment-api batch-audit-api; do
  hits=$(rg 'AUTH_FAILURE' "$svc/" --type py --glob '!**/tests/**' -l 2>/dev/null | wc -l)
  [ "$hits" -eq 0 ] && echo "MISSING AUTH_FAILURE event: $svc"
done

# Check all auth logging goes through UTL events_interface (no custom auth loggers)
rg 'logger\.(info|warning|error).*auth\|logging\..*auth' --type py \
  --glob '!.venv*' --glob '!**/tests/**' -i -n | \
  grep -v 'log_event\|unified_trading_library.events\|unified_trading_library.*events_interface' | head -20

# Check broad except Exception in production code
rg 'except Exception' --type py \
  --glob '!.venv*' --glob '!**/tests/**' --glob '!**/scripts/**' -n | \
  grep -v '# broad-except-ok' | head -20
# Each hit must be in QUALITY_GATE_BYPASS_AUDIT.md or narrowed to specific exceptions
```

**Required state:**

| Criterion                | Requirement                                                                                                                                   |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Hardcoded secrets        | Zero in production source (excluding test fixtures)                                                                                           |
| Secret access            | All secrets via `get_secret_client(project_id, secret_name)`; no `os.getenv` fallback                                                         |
| HTTP verify              | No `verify=False` outside test code                                                                                                           |
| API authentication       | All API services have auth middleware; 401 paths log `AUTH_FAILURE` event                                                                     |
| `SECRET_ACCESSED` event  | Logged on every secret retrieval                                                                                                              |
| `CONFIG_CHANGED` event   | Logged on every config mutation                                                                                                               |
| Full auth event set      | AUTH_SUCCESS (first-per-session), AUTH_FAILURE, AUTH_DENIED, S2S_AUTH_SUCCESS, S2S_AUTH_FAILURE all emitted                                   |
| Auth events all services | ALL API services with auth middleware emit AUTH_FAILURE at minimum — not just execution-service                                               |
| Auth via UEI only        | All auth-related logging (login, session, permission, role) flows through `unified-trading-library.events_interface` — no custom auth loggers |
| Mock auth                | `DISABLE_AUTH` env flag does NOT affect production deployments                                                                                |
| Broad `except Exception` | Zero in production source; each legitimate use in `QUALITY_GATE_BYPASS_AUDIT.md`                                                              |

**Scoring:** `PASS` — all criteria met. `WARN` — minor documentation gap; OR ≤3 broad `except Exception` all documented
in BYPASS_AUDIT.md. `FAIL` — any hardcoded secret; any 401 path missing `AUTH_FAILURE`; any `verify=False`; OR
`get_secret_client` bypassed with env var fallback; OR any auth event missing from execution-service auth paths; OR any
API service with auth middleware missing AUTH_FAILURE event; OR auth logging bypasses
`unified-trading-library.events_interface`; OR undocumented broad `except Exception` in production code.

---

## Section 4 — Architecture

**Goal:** Tier boundaries are respected. No cross-service Python imports. Cloud I/O is abstracted through UTL
cloud_interface (formerly UCI). All services use batch-live symmetry (same engine, mode-switched transport).

**Audit commands:**

```bash
# No cross-service Python imports (T4 service importing another T4 service directly)
rg 'from (execution_service|strategy_service|risk_and_exposure_service|alerting_service|pnl_attribution_service)' \
  --type py --glob '!.venv*' --glob '!**/tests/**' -n

# No direct cloud SDK imports outside UTL cloud_interface / deployment-service
rg 'from google\.cloud|import boto3|from boto3' \
  --type py --glob '!.venv*' \
  --glob '!unified-trading-library/unified_trading_library/cloud_interface/**' \
  --glob '!deployment-service/**' -n

# No GCS bucket name construction outside UTL cloud_interface
rg 'gcs_bucket|gs://' --type py --glob '!.venv*' \
  --glob '!unified-trading-library/unified_trading_library/cloud_interface/**' -n
```

**Required state:**

| Criterion                | Requirement                                                                                                                                |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Service→service imports  | Zero cross-service Python imports in T4 repos                                                                                              |
| Cloud SDK confinement    | `google.cloud.*` and `boto3` only in `unified-trading-library/unified_trading_library/cloud_interface/` and `deployment-service/backends/` |
| Cloud-agnostic I/O       | `get_storage_client()`, `get_secret_client()`, `CloudEventSink` used everywhere (from UTL cloud_interface)                                 |
| Batch-live symmetry      | Same processing engine for batch and live; transport layer switches on `--mode`                                                            |
| UCI PubSub               | Services use `get_pubsub_client()` from UTL cloud_interface, not `google-cloud-pubsub` directly                                            |
| Deployment API boundary  | No direct `deployment_service` Python imports from other services                                                                          |
| Separation of concerns   | Services contain only business logic (orchestration, decisions); all infrastructure delegated to libraries                                 |
| No library duplication   | No service reimplements functionality that already exists in a unified-\* library (check with cross-repo rg)                               |
| Import ↔ manifest match | Every `from unified_*` import in a service has a corresponding entry in workspace-manifest.json `dependencies[]`                           |

**Audit commands (separation of concerns):**

```bash
# Check services don't reimplement library functionality
# Look for custom cloud clients, event loggers, config readers in service source
for svc in execution-service strategy-service alerting-service risk-and-exposure-service \
           pnl-attribution-service position-balance-monitor-service market-tick-data-service \
           market-data-processing-service instruments-service; do
  # Custom cloud clients (should use UTL cloud_interface)
  rg 'class.*Client.*Storage|class.*Client.*PubSub|class.*Client.*BigQuery' \
    "$svc/" --type py --glob '!**/tests/**' -n 2>/dev/null
  # Custom event loggers (should use UTL events_interface)
  rg 'class.*EventLogger|class.*EventPublisher' \
    "$svc/" --type py --glob '!**/tests/**' -n 2>/dev/null
done

# Verify all unified-* imports have manifest dependency entries
python3 -c "
import json, pathlib, re
m = json.load(open('unified-trading-pm/workspace-manifest.json'))
dep_map = {r['name']: [d.get('name') if isinstance(d, dict) else d for d in r.get('dependencies', [])] for r in m['repos']}
for repo in m['repos']:
    src = pathlib.Path(repo['name'])
    if not src.exists(): continue
    declared = set(dep_map.get(repo['name'], []))
    for py in src.rglob('*.py'):
        if '.venv' in str(py) or 'tests' in str(py): continue
        try:
            for line in py.read_text().splitlines():
                match = re.match(r'from (unified[_\w]+)', line)
                if match:
                    pkg = match.group(1).replace('_', '-')
                    if pkg not in declared and pkg != repo['name'].replace('_', '-'):
                        print(f'UNDECLARED DEP: {repo[\"name\"]} imports {pkg} (not in manifest dependencies)')
                        break
        except: pass
"
```

### §4.X Interface Usage Compliance

- Services MUST use URDI for reference/instrument data, not UMI directly
- UMI is for market data (trades, orderbooks, tickers). URDI is for reference data (instrument definitions, options
  chains, expiry calendars)
- Check: `rg "from unified_market_interface import.*Adapter" --type py --glob '!tests/' $SOURCE_DIR/` — any adapter
  import in a service that fetches instrument definitions is a violation
- Services hand API keys to interfaces via config/Secret Manager; they don't manage credentials themselves

### §4.Y Shard-Level Failure Isolation

- A failed shard (venue × date) MUST NOT kill other shards in the same batch
- Check: `rg "raise RuntimeError" --type py --glob '!tests/' $SOURCE_DIR/` inside per-venue/per-shard processing loops
- Pattern: catch all exceptions per-shard, log VENUE_PROCESSING_FAILED event with details, return empty result
- SSOT: unified-trading-pm/codex/04-architecture/shard-level-failure-isolation.md

**Scoring:** `PASS` — zero violations. `FAIL` — any cross-service import; any direct cloud SDK outside UTL
cloud_interface/deployment; any service reimplements library functionality; any undeclared dependency import; any
service using UMI for reference data instead of URDI; any unguarded raise inside per-venue/per-shard processing loops.

---

## Section 5 — Schema Governance

**Goal:** Clean separation between `unified-api-contracts` (external venue schemas) and `unified-api-contracts.internal`
(internal schemas, formerly `unified-internal-contracts`). No float for price/monetary fields. No duplicated schemas
across AC and UIC.

**Audit commands:**

```bash
# Check for float price fields in UIC/UAC schemas
rg 'float' unified-api-contracts/unified_api_contracts/internal/ \
  unified-api-contracts/unified_api_contracts/ \
  --type py --glob '!.venv*' -n | \
  grep -v '# financial-ratio: float-ok\|# volatility-pct: float-ok\|# time-based: float-ok\|# pct: float-ok'

# Run Layer 0 contract alignment tests
cd unified-api-contracts && bash scripts/quality-gates.sh

# Check BestExecutionRecord has version trail fields (MiFID II / SEC Rule 17a-4)
rg 'execution_service_version|strategy_service_version' \
  unified-api-contracts/ --type py -n
# Expected: both fields present on BestExecutionRecord in regulatory/schemas.py

# Check EXECUTION_AUDIT schema is actually consumed (not just defined)
rg 'persist_audit_log' execution-service/ --type py --glob '!**/tests/**' -n
# Expected: calls for ORDER_CREATED, ORDER_FILLED, ORDER_REJECTED, ORDER_CANCELLED, ORDER_UPDATED

# Check STRATEGY_AUDIT is consumed
rg 'persist_audit_log\|STRATEGY_AUDIT' strategy-service/ --type py --glob '!**/tests/**' -n
# Expected: calls for STRATEGY_INSTRUCTION, SIGNAL_GENERATED

# Check audit payload validation exists
rg '_validate_audit_payload\|validate_audit' execution-service/ strategy-service/ \
  --type py --glob '!**/tests/**' -n
```

**Required state:**

| Criterion                 | Requirement                                                                                            |
| ------------------------- | ------------------------------------------------------------------------------------------------------ |
| AC scope                  | External venue schemas only (exchange responses, raw data formats)                                     |
| UIC scope                 | Internal domain schemas only (canonical processed forms)                                               |
| No float price fields     | All price/monetary fields use `Decimal`; ratio/pct/time fields annotated with `# float-ok` comment     |
| No AC/UIC duplication     | No schema class defined in both repos                                                                  |
| Layer 0 tests             | `test_contract_alignment.py` + `test_ac_uic_alignment.py` pass                                         |
| Schema robustness tests   | `test_schema_robustness.py` passes per-service                                                         |
| BestExecutionRecord trail | `execution_service_version` + `strategy_service_version` fields present on `BestExecutionRecord`       |
| EXECUTION_AUDIT consumed  | `persist_audit_log()` called for ORDER_CREATED/FILLED/REJECTED/CANCELLED/UPDATED in execution-service  |
| STRATEGY_AUDIT consumed   | `persist_audit_log()` called for STRATEGY_INSTRUCTION/SIGNAL_GENERATED in strategy-service             |
| Audit payload validation  | `_validate_audit_payload()` validates against `EXECUTION_AUDIT.required_fields`; raises on missing     |
| No rogue service schemas  | Services do NOT define Pydantic BaseModel/TypedDict for cross-service data — those belong in UIC/UAC   |
| Schema location rule      | Internal domain schemas → UIC; external vendor schemas → UAC; service-local models → internal-only use |

**Audit commands (schema location enforcement):**

```bash
# Find Pydantic BaseModel definitions in service source (not tests, not contracts repos)
for svc in execution-service strategy-service alerting-service risk-and-exposure-service \
           pnl-attribution-service position-balance-monitor-service market-tick-data-service \
           market-data-processing-service instruments-service; do
  hits=$(rg 'class \w+\(BaseModel\)|class \w+\(TypedDict\)' \
    "$svc/" --type py --glob '!**/tests/**' --glob '!.venv*' -n 2>/dev/null)
  if [ -n "$hits" ]; then
    echo "=== $svc: LOCAL SCHEMA DEFINITIONS ==="
    echo "$hits"
    echo "--- Verify each is internal-only (not imported by other repos) ---"
  fi
done

# Cross-check: are any service-defined models imported by OTHER repos?
for svc in execution-service strategy-service alerting-service risk-and-exposure-service; do
  pkg=$(echo "$svc" | tr '-' '_')
  rg "from ${pkg}\." --type py --glob '!.venv*' --glob "!${svc}/**" -l 2>/dev/null | head -5
done
# Any hit = schema should be moved to UIC/UAC
```

**Scoring:** `PASS` — all criteria met. `WARN` — 1–2 float fields with `# float-ok` comment; OR ≤3 service-local models
that are genuinely internal-only. `FAIL` — any price/monetary field using `float`; any AC/UIC duplication; Layer 0 tests
failing; OR `BestExecutionRecord` missing version fields; OR `persist_audit_log()` not called for all order lifecycle
events; OR audit payload validation absent; OR any service-defined schema imported by another repo (should be in
UIC/UAC).

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

# Check order-flow guard script exists and is wired
ls unified-trading-pm/scripts/deployment/check-order-flow.sh 2>/dev/null
grep -l 'check-order-flow' unified-trading-pm/.github/workflows/cloud-build-router.yml

# Check canary deployment script exists with traffic splitting
ls unified-trading-pm/scripts/deployment/canary-deploy.sh 2>/dev/null
grep -l 'canary' unified-trading-pm/.github/workflows/cloud-build-router.yml

# Check Cloud Build regional fallback (not hard-coded single region)
rg 'fallback\|FALLBACK_REGION\|us-central1' \
  unified-trading-pm/.github/workflows/cloud-build-router.yml -n

# Check partial staging promotion recovery (start_from_repo resume)
rg 'start_from_repo\|promoted.*failed\|resume' \
  unified-trading-pm/.github/workflows/staging-to-main.yml -n

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

| Criterion                  | Requirement                                                                                                                                |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Checklist phases 1–7       | Present in `deployment-service/configs/checklist.*.yaml` per service                                                                       |
| `runtime-topology.yaml`    | Has `version`, `deployment_profiles`, `clusters`, `service_flows` keys                                                                     |
| Layer 2 infra verify       | `/infra/health` passes post-deploy                                                                                                         |
| Layer 3a smoke             | Passes in <5 min                                                                                                                           |
| Layer 3b full E2E          | Passes in 15–30 min                                                                                                                        |
| Pytest markers registered  | `unit`, `integration`, `smoke`, `e2e` in all `pyproject.toml`                                                                              |
| Kill switch wiring         | `cloud-build-router.yml` calls `trading-kill-switch.sh halt` pre-deploy and `resume` post-deploy for execution/strategy services           |
| Position reconciliation    | `cloud-build-router.yml` runs `position-reconciliation-check.sh` snapshot pre-deploy and compare post-deploy for execution/risk services   |
| Tier-ordered deploy        | `cloud-build-router.yml` validates T0→T1→T2→service deployment ordering via manifest `topologicalOrder.levels`                             |
| Post-deploy health check   | `cloud-build-router.yml` runs `post-deploy-smoke.sh` polling `/health` + `/readiness` after Cloud Build success                            |
| Change freeze enforcement  | `cloud-build-router.yml` prod path calls `change-freeze-check.yml` as first job; blocked during macro/session windows                      |
| Disaster recovery targets  | `plans/ops/disaster-recovery-rto-rpo.md` exists with RTO/RPO per environment                                                               |
| Secret rotation plan       | `plans/ops/secret-rotation-plan.md` exists with rotation schedule for all secrets                                                          |
| Order-flow guard           | `cloud-build-router.yml` calls `check-order-flow.sh` as pre-deploy step for trading-critical services; bypassable via `force_deploy`       |
| Canary deployment          | `canary-deploy.sh` exists with Cloud Run traffic splitting (5%/95%), health monitor, auto-promote/rollback                                 |
| Regional fallback          | `cloud-build-router.yml` has fallback region alert on build failure (not hard-coded single region)                                         |
| Partial promotion recovery | `staging-to-main.yml` has `start_from_repo` resume param; tracks promoted/failed repos in manifest; Telegram escalation on partial failure |

**Scoring:** `PASS` — all services have deployment checklist; topology YAML valid; kill switch + position
reconciliation + health check + order-flow guard + canary deploy wired. `WARN` — 1–2 services pre-1.0.0 with documented
reasons; OR kill switch in soft-gate mode; OR canary deploy not yet wired for non-critical services. `FAIL` — any
service without a checklist; OR topology YAML missing required keys; OR no kill switch wiring for trading-critical
services; OR no order-flow guard for execution/risk/strategy services; OR staging-to-main has no partial failure
recovery.

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

# Find broad except Exception (see also §3)
rg 'except Exception' --type py \
  --glob '!.venv*' --glob '!**/tests/**' -n | \
  grep -v '# broad-except-ok'
# Each hit must be narrowed to specific exceptions OR in QUALITY_GATE_BYPASS_AUDIT.md
```

**Required state:**

| Criterion                          | Requirement                                                                                    |
| ---------------------------------- | ---------------------------------------------------------------------------------------------- |
| `# type: ignore` count             | <10 total; every occurrence in `QUALITY_GATE_BYPASS_AUDIT.md`                                  |
| `.basedpyright-baseline.json`      | Zero target; each present file requires BYPASS_AUDIT.md entry (WARN); undocumented = FAIL      |
| `try/except ImportError` fallbacks | Zero in production source (fail loud on missing imports)                                       |
| `QUALITY_GATE_BYPASS_AUDIT.md`     | Present in every repo that has any suppression                                                 |
| `# noqa` suppressions              | Zero in production source                                                                      |
| Broad `except Exception`           | Zero undocumented; each legitimate use annotated `# broad-except-ok` AND in BYPASS_AUDIT.md    |
| QG bypass reasons                  | Every bypass/skip in quality-gates.sh has a documented best-practice reason in BYPASS_AUDIT.md |
| `RUN_INTEGRATION` must be `true`   | All services must have `RUN_INTEGRATION=true` in quality-gates.sh; `false` is not allowed      |
| No bypass-to-pass pattern          | No evidence of suppressions added solely to make QG pass (review git blame for context)        |

**Audit commands (QG bypass audit):**

```bash
# Check RUN_INTEGRATION setting across all repos (MUST be true)
rg 'RUN_INTEGRATION=' */scripts/quality-gates.sh 2>/dev/null | \
  grep -v 'RUN_INTEGRATION=true' | \
  awk -F: '{print "VIOLATION: " $1 " has " $2}'

# Check for skip/bypass patterns in QG scripts without documented reasons
rg 'skip|SKIP|bypass|BYPASS|disable|DISABLE' */scripts/quality-gates.sh 2>/dev/null | \
  grep -v '#.*reason:\|#.*best-practice:' | head -20

# Verify QUALITY_GATE_BYPASS_AUDIT.md covers all suppressions
for repo in */; do
  has_suppress=$(rg '# type: ignore|# noqa|\.basedpyright-baseline|except ImportError|RUN_INTEGRATION=false' \
    "$repo" --type py --glob '!.venv*' -c 2>/dev/null | awk -F: '{s+=$2} END {print s+0}')
  if [ "$has_suppress" -gt 0 ] && [ ! -f "${repo}QUALITY_GATE_BYPASS_AUDIT.md" ]; then
    echo "MISSING BYPASS_AUDIT.md: $repo (has $has_suppress suppressions)"
  fi
done
```

**Scoring:** `PASS` — zero suppressions; all `RUN_INTEGRATION=true`. `WARN` — ≤10 `type: ignore` all documented;
baseline files documented; ≤5 broad `except Exception` all in BYPASS_AUDIT.md. `FAIL` — any undocumented suppression;
any `try/except ImportError`; any `# noqa` in production code; OR undocumented broad `except Exception`; OR any repo
with `RUN_INTEGRATION=false`; OR any QG bypass without documented best-practice reason.

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

# Check manifest version ↔ pyproject.toml version drift
python3 -c "
import json, pathlib
try:
    import tomllib
except ImportError:
    import tomli as tomllib
m = json.load(open('unified-trading-pm/workspace-manifest.json'))
for r in m['repos']:
    pp = pathlib.Path(r['name'] + '/pyproject.toml')
    if pp.exists():
        with open(pp, 'rb') as f:
            pv = tomllib.load(f).get('project', {}).get('version', '?')
        mv = r.get('version', '?')
        if pv != mv and mv != '?':
            print(f'DRIFT: {r[\"name\"]} manifest={mv} pyproject={pv}')
"
```

**Required state:**

| Criterion                   | Requirement                                                                             |
| --------------------------- | --------------------------------------------------------------------------------------- |
| All plans in SSOT-INDEX     | Every `.plan.md` in `plans/active/` registered in `00-SSOT-INDEX.md`                    |
| No phantom SSOT entries     | Every SSOT entry has a corresponding live file                                          |
| Manifest ↔ topology sync   | All repos in manifest present in `runtime-topology.yaml`                                |
| Cursor rules in sync        | `unified-trading-pm/cursor-rules/` and `.cursor/rules/` have equal rule counts          |
| No orphan repos             | Every repo with a `pyproject.toml` is in `workspace-manifest.json`                      |
| Manifest↔pyproject version | `workspace-manifest.json` version matches `pyproject.toml` version per repo; zero drift |

**Scoring:** `PASS` — all criteria met. `WARN` — 1–3 new plans not yet registered (grace period 24h). `FAIL` — any plan
unregistered for >24h; OR phantom SSOT entries; OR manifest/topology mismatch; OR manifest↔pyproject version drift on
any repo (causes incorrect cascade dispatch).

---

## Section 10 — Integration Test Coverage

**Goal:** Every repo with private deps (L2+) has `tests/integration/` with Layer 1.5 mock integration tests. All
interface repos have VCR cassettes validating external API schemas. Services/libraries have integration tests that
import and exercise each direct library dependency. All UIs with backing APIs have
`tests/integration/api.integration.test.ts`. No standalone coverage-boost files (`test_coverage_boost_*.py`,
`test_*_coverage.py`).

**SSOT:** `unified-trading-pm/docs/testing/testing-requirements.md`

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

# Check library-dep integration coverage (run per service)
# python3 unified-trading-pm/scripts/validation/check-integration-dep-coverage.py --repo <repo> --project-root .

# Check UI integration tests (all 12 UIs)
for ui in batch-audit-ui client-reporting-ui deployment-ui execution-analytics-ui live-health-monitor-ui logs-dashboard-ui ml-training-ui onboarding-ui settlement-ui strategy-ui trading-analytics-ui unified-admin-ui; do
  [ -f "$ui/tests/integration/api.integration.test.ts" ] || echo "MISSING UI integration: $ui"
done

# Check for coverage-boost files (should be merged per testing-requirements.md)
rg -l 'test_coverage_boost|test_.*_coverage\.py|test_boost_coverage' --glob '*.py' */tests/unit/ 2>/dev/null | head -20

# Check VCR cassettes in interface repos
for repo in unified-market-interface unified-trade-execution-interface \
            unified-reference-data-interface unified-position-interface \
            unified-sports-execution-interface unified-defi-execution-interface; do
  cassette_count=$(find $repo -name '*.yaml' -path '*/mocks/*' 2>/dev/null | wc -l)
  echo "$repo: $cassette_count cassettes"
done
# Note: unified-cloud-interface is now unified-trading-library/unified_trading_library/cloud_interface/
cassette_count=$(find unified-trading-library -name '*.yaml' -path '*/cloud_interface/*/mocks/*' 2>/dev/null | wc -l)
echo "unified-trading-library (cloud_interface): $cassette_count cassettes"
```

**Required state:**

| Criterion                             | Requirement                                                                                                        |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `tests/integration/` presence         | All T3+ repos (services, APIs) have at least 1 integration test                                                    |
| Library-dep integration coverage      | Each service/library has ≥1 integration test that imports each direct library dep                                  |
| UI integration tests                  | All 12 UI repos have `tests/integration/api.integration.test.ts` (real HTTP, skip when API unreachable)            |
| Coverage consolidation                | No standalone `test_coverage_boost_*.py`, `test_*_coverage.py`, `test_boost_*.py` — merged into primary test files |
| VCR cassettes in interface repos      | All 7 interface repos have cassettes in `unified_api_contracts_external/<venue>/mocks/`                            |
| Integration tests are credential-free | `CLOUD_MOCK_MODE=true`, no live API calls in quickmerge                                                            |
| Layer 1.5 per dep boundary            | At least 1 integration test per private dependency boundary                                                        |
| Functional depth (not import-only)    | Integration tests CALL functions/classes from each dependency — not just `import` the package                      |
| `RUN_INTEGRATION=true` enforced       | All repos with integration tests must have `RUN_INTEGRATION=true` in quality-gates.sh; `false` is FAIL             |
| Manifest `integration_deps` tracked   | workspace-manifest.json tracks all inter-repo import relationships in `integration_dependencies[]` field           |
| QG runs integration tests             | quality-gates.sh actually executes `pytest tests/integration/` when `RUN_INTEGRATION=true`                         |

**Audit commands (integration test depth):**

```bash
# Check that integration tests actually CALL functions (not just import)
# For each repo, verify integration test files contain function calls, not just imports
for repo in */; do
  int_dir="${repo}tests/integration/"
  [ -d "$int_dir" ] || continue
  for tf in "$int_dir"*.py; do
    [ -f "$tf" ] || continue
    # Count import lines vs actual function call/assertion lines
    imports=$(rg '^from |^import ' "$tf" 2>/dev/null | wc -l)
    calls=$(rg '\w+\(|assert ' "$tf" 2>/dev/null | wc -l)
    if [ "$calls" -le "$imports" ]; then
      echo "SHALLOW TEST (import-only): $tf (imports=$imports, calls=$calls)"
    fi
  done
done

# Verify RUN_INTEGRATION=true in all repos that have integration tests
for repo in */; do
  [ -d "${repo}tests/integration/" ] || continue
  qg="${repo}scripts/quality-gates.sh"
  [ -f "$qg" ] || continue
  setting=$(rg 'RUN_INTEGRATION=' "$qg" 2>/dev/null | head -1)
  echo "$repo: $setting"
  echo "$setting" | grep -q 'false' && echo "  FAIL: must be true"
done

# Check manifest has integration_dependencies field
python3 -c "
import json
m = json.load(open('unified-trading-pm/workspace-manifest.json'))
missing = [r['name'] for r in m['repos'] if 'integration_dependencies' not in r]
if missing:
    print(f'MISSING integration_dependencies field: {len(missing)} repos')
    for name in missing[:10]: print(f'  {name}')
else:
    print('PASS: all repos have integration_dependencies')
"
```

**Scoring:** `PASS` — all T3+ repos have integration tests; all interface repos have cassettes; library-dep coverage OK;
integration tests call actual functions (not import-only); `RUN_INTEGRATION=true` in all repos; manifest tracks
`integration_dependencies`; UI integration tests present; no coverage-boost files. `WARN` — 1–2 repos missing but
tracked in active plan. `FAIL` — any interface repo with zero cassettes; OR integration tests make live API calls; OR
services with library deps missing integration test imports; OR any repo with `RUN_INTEGRATION=false`; OR integration
tests are import-only (no actual function calls); OR `integration_dependencies` field absent from manifest.

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

**Goal:** No cloud-provider-specific code outside `unified-trading-library/unified_trading_library/cloud_interface/` and
`deployment-service/backends`. All repos use UTL cloud_interface abstractions for storage, secrets, PubSub, and config.

**Audit commands:**

```bash
# GCS bucket references outside UTL cloud_interface
rg 'gcs_bucket|upload_to_gcs|download_from_gcs' --type py \
  --glob '!unified-trading-library/unified_trading_library/cloud_interface/**' --glob '!.venv*' -n

# Google Cloud imports outside UTL cloud_interface
rg 'from google\.cloud|import google\.cloud' --type py \
  --glob '!unified-trading-library/unified_trading_library/cloud_interface/**' \
  --glob '!deployment-service/**' \
  --glob '!.venv*' -n

# boto3 imports outside deployment-service
rg 'import boto3|from boto3' --type py \
  --glob '!unified-trading-library/unified_trading_library/cloud_interface/**' \
  --glob '!deployment-service/**' \
  --glob '!.venv*' -n

# BigQuery references outside UTL cloud_interface
rg 'bigquery_dataset|BigQueryClient' --type py \
  --glob '!unified-trading-library/unified_trading_library/cloud_interface/**' --glob '!.venv*' -n
```

**Required state:**

| Criterion                       | Requirement                                                                                                   |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `google.cloud.*` imports        | Only in `unified-trading-library/unified_trading_library/cloud_interface/` and `deployment-service/backends/` |
| `boto3` imports                 | Only in `unified-trading-library/unified_trading_library/cloud_interface/` and `deployment-service/backends/` |
| `gcs_bucket`/`gs://` references | Only in `unified-trading-library/unified_trading_library/cloud_interface/`                                    |
| `os.getenv` in cloud config     | Zero (use `UnifiedCloudConfig`); bootstrap exception only                                                     |
| `get_pubsub_client()`           | All services use UTL cloud_interface PubSub abstraction                                                       |

### §12.X Credential Placeholder Detection

- .env files MUST NOT contain placeholder credential paths (e.g. `your-service-account-key.json`)
- Check: `rg "your-service-account" .env .env.example` — any match is a violation
- ADC (Application Default Credentials) is the default for local dev; no key file references

**Scoring:** `PASS` — zero violations. `FAIL` — any banned pattern found in non-UTL-cloud_interface/non-deployment
source; any .env file containing placeholder credential paths.

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

# Check Telegram if: guard antipattern (env.* unavailable in GHA if: expressions)
rg 'if:.*env\.(TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID)' \
  unified-trading-pm/.github/workflows/*.yml -n
# Expected: zero results — early-exit should be inside run: block instead

# Check secrets.TELEGRAM_CHAT_ID (should be vars.TELEGRAM_CHAT_ID)
rg 'secrets\.TELEGRAM_CHAT_ID' \
  unified-trading-pm/.github/workflows/*.yml -n
# Expected: zero results — CHAT_ID is a repository variable, not a secret

# Check overnight-orchestrator has its own concurrency guard
rg 'concurrency:' unified-trading-pm/.github/workflows/overnight-agent-orchestrator.yml -A2
# Expected: group: overnight-orchestrator, cancel-in-progress: true

# Check SHA pinning TOCTOU in staging-to-main.yml
rg 'rev-parse\|staging_commits\|sha.*mismatch\|skip ci' \
  unified-trading-pm/.github/workflows/staging-to-main.yml -n
# Expected: SHA verification before promoting each repo

# Check conflict-resolution-agent output validation
rg 'py_compile\|yaml\.safe_load\|<<<<<<<\|merge.*marker' \
  unified-trading-pm/.github/workflows/conflict-resolution-agent.yml -n
# Expected: validation checks for merge markers, py_compile, yaml.safe_load

# Check SIT debounce reads pending_repos from manifest
rg 'pending_repos\|sit_retry_count' \
  unified-trading-pm/.github/workflows/sit-debounce-trigger.yml -n
# Expected: reads staging_status.pending_repos, enforces max retries

# Check starvation detector workflow
ls unified-trading-pm/.github/workflows/sit-starvation-detector.yml 2>/dev/null
rg 'locked_alert_sent\|locked_at\|locked_since' \
  unified-trading-pm/.github/workflows/sit-starvation-detector.yml -n 2>/dev/null

# Check Telegram rate-limit guard exists
ls unified-trading-pm/scripts/telegram-rate-limit.sh 2>/dev/null
rg 'telegram_last_alert_ts' \
  unified-trading-pm/scripts/telegram-rate-limit.sh -n 2>/dev/null

# Check manifest writes use atomic tmp+rename pattern
rg '\.json\.tmp\|os\.replace\|mv.*workspace-manifest' \
  unified-trading-pm/.github/workflows/*.yml -n
# Expected: all manifest-mutating workflows write to tmp then rename
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

**CI/CD infrastructure hardening checks:**

| Criterion                     | Requirement                                                                                                          |
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Manifest concurrency          | All manifest-mutating workflows share `concurrency: { group: manifest-update, cancel-in-progress: false }`           |
| Dead man switch               | `overnight-dead-man-switch.yml` runs at 03:00 UTC, alerts if overnight orchestrator didn't complete                  |
| Version bump loop breaker     | `update-repo-version.yml` has `CASCADE_DEPTH` counter with `MAX_CASCADE_DEPTH=3`; halts + alerts on exceed           |
| GHA burst throttling          | `overnight-agent-orchestrator.yml` staggers dispatches with delay between repos per tier                             |
| Claude API health precheck    | All agent workflows (conflict-resolution, semver, overnight) source `claude-api-health-precheck.sh`                  |
| SIT runbook                   | `plans/ops/sit-runbook.md` documents force-unlock, failure modes, escalation path                                    |
| Manifest mutation audit trail | `log-manifest-mutation.sh` appends to `plans/audit/manifest-mutations.jsonl` on every manifest write                 |
| Change freeze calendar        | `plans/ops/change-freeze-calendar.csv` covers NFP/FOMC/ECB/BOE + session open/close windows                          |
| Telegram `if:` guard          | Zero `if: ... env.TELEGRAM_*` in GHA workflows; early-exit inside `run:` block instead                               |
| Telegram `vars` vs `secrets`  | `TELEGRAM_CHAT_ID` accessed via `vars.` (repository variable), never `secrets.`                                      |
| Orchestrator concurrency      | `overnight-agent-orchestrator.yml` has `concurrency: { group: overnight-orchestrator, cancel-in-progress: true }`    |
| SHA pinning in staging→main   | `staging-to-main.yml` verifies `git rev-parse HEAD` matches `staging_commits[repo]` before promoting                 |
| Conflict agent validation     | `conflict-resolution-agent.yml` validates output: no merge markers, all files present, `py_compile`/`yaml.safe_load` |
| SIT debounce wiring           | `sit-debounce-trigger.yml` reads `staging_status.pending_repos`; `sit_retry_count` max 3                             |
| Starvation detector           | Scheduled workflow alerts if `staging_status.locked` age >1hr; dedup via `locked_alert_sent`                         |
| Telegram rate limiting        | `scripts/telegram-rate-limit.sh` guards max 1 alert per workflow per 60s via `telegram_last_alert_ts`                |
| Manifest write atomicity      | All manifest-mutating workflows write to `.json.tmp` then rename; no direct writes to `workspace-manifest.json`      |

**Scoring:**

- `PASS` — all Python repos use `uv venv .venv` + `--python .venv/bin/python` + `PATH` export + `CLOUD_MOCK_MODE`; all
  infrastructure hardening checks pass
- `WARN` — any UI repo missing a CI quality gate step; OR any infrastructure check in soft-gate mode; OR starvation
  detector/rate-limiter present but not yet battle-tested
- `FAIL` — any Python repo uses `--system`, bare `pip install`, or missing `PATH` export; OR manifest concurrency groups
  missing; OR no dead-man switch; OR Telegram `if:` guard antipattern present; OR staging-to-main SHA verification
  absent; OR manifest writes not atomic (tmp+rename); OR `secrets.TELEGRAM_CHAT_ID` used instead of `vars.`

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
| `major-bump-issue-handler.yml`     | Present in all ~33 repos; validates approver write access              |
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
    rpath = pathlib.Path('unified-trading-pm/codex/10-audit/repos/' + r['name'] + '.yaml')
    if not rpath.exists():
        print('MISSING readiness file:', r['name'])
"

# Check canonical schema SSOT exists
ls unified-trading-pm/codex/10-audit/REPO_READINESS_CHECKLIST.yaml

# Run automated verifier
python3 unified-trading-pm/scripts/check-repo-readiness.py --all
```

**Required state:**

| Criterion                   | Requirement                                                                  |
| --------------------------- | ---------------------------------------------------------------------------- |
| Readiness schema SSOT       | `unified-trading-pm/codex/10-audit/REPO_READINESS_CHECKLIST.yaml` v3.0       |
| Per-repo readiness YAML     | `unified-trading-pm/codex/10-audit/repos/{repo-name}.yaml` for all ~33 repos |
| CR/DR/BR axes               | Each axis tracked independently; N/A items documented with reason            |
| v1.0.0 gateway gates        | CR5 + DR3 + DR4 + BR2 + BR3 + BR4 + BR8 all PASS before any 1.0.0 tag        |
| `deployment_modes` declared | `batch`, `live`, or `both` per repo in readiness YAML                        |
| `.readiness-ref`            | Symlink in each repo pointing to codex canonical location                    |

**Scoring:** `PASS` — all ~33 repos have YAML files; verifier exits 0. `WARN` — 1–5 repos missing YAML (tracked in
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

# Check inject-mandatory-rules.sh exists
ls unified-trading-pm/scripts/agents/inject-mandatory-rules.sh 2>/dev/null

# Verify all Claude-invoking agent workflows inject mandatory rules into prompts
# Each must use MANDATORY_RULES (GHA GITHUB_ENV heredoc) or inject-mandatory-rules.sh (local)
for wf in conflict-resolution-agent.yml plan-health-agent.yml \
          rules-alignment-agent.yml; do
  hits=$(rg 'MANDATORY_RULES\|inject-mandatory-rules' \
    "unified-trading-pm/.github/workflows/$wf" 2>/dev/null | wc -l)
  [ "$hits" -eq 0 ] && echo "MISSING rules injection: $wf"
done
# Also check codex-sync-agent in PM repo (codex is now a sub-directory of PM)
rg 'MANDATORY_RULES\|inject-mandatory-rules' \
  unified-trading-pm/.github/workflows/codex-sync-agent.yml 2>/dev/null | wc -l

# Check SUB_AGENT_MANDATORY_RULES.md has system-first architecture §0
rg 'System-First Architecture\|system-first' \
  unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md -n | head -5
```

**Required state:**

| Criterion                          | Requirement                                                                                                       |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `semver-agent.yml`                 | Present in PM; triggers on staging push                                                                           |
| `rules-alignment-agent.yml`        | Present in PM; verifies rules/AGENTS.md/CLAUDE.md consistency                                                     |
| `codex-sync-agent.yml`             | Present in PM (codex is now a sub-directory of PM); triggers on manifest-updated dispatch                         |
| `plan-alignment-agent.yml`         | Present in PM; validates INDEX.md ↔ active plans ↔ SSOT-INDEX alignment                                         |
| `overnight-agent-orchestrator.yml` | Present; cron 01:00 UTC; tier-ordered (T0→T4); 3x retry on failure                                                |
| `AGENTS.md` in all repos           | Workspace-generic, not PM-specific; includes full rules + mandatory cleanup                                       |
| `.claude/CLAUDE.md` in all repos   | Symlink to canonical `unified-trading-pm/cursor-configs/CLAUDE.md`                                                |
| `ANTHROPIC_API_KEY` secret         | Set on all repos for agent execution                                                                              |
| Telegram secrets                   | `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` on all repos                                                            |
| Rules injection in prompts         | All Claude-invoking workflows use `MANDATORY_RULES` env var or `inject-mandatory-rules.sh`; verified per-workflow |
| `inject-mandatory-rules.sh`        | Present in `scripts/agents/`; used by local scripts (run-parallel-agents.sh, llm-agent-wrapper.sh)                |
| System-first architecture §0       | `SUB_AGENT_MANDATORY_RULES.md` §0 contains decision tree (events→UEI, schemas→UIC/UAC, cloud→UCI, etc.)           |

**Scoring:** `PASS` — all 4 workflows present; overnight orchestrator wired; all repos have AGENTS.md + CLAUDE.md; all
Claude-invoking workflows inject mandatory rules. `WARN` — 1–5 repos missing AGENTS.md (rollout in progress). `FAIL` —
overnight orchestrator absent; OR semver-agent missing; OR `ANTHROPIC_API_KEY` not propagated; OR any Claude-invoking
workflow missing `MANDATORY_RULES`/`inject-mandatory-rules.sh` in prompt construction; OR `SUB_AGENT_MANDATORY_RULES.md`
missing system-first architecture §0.

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

| Criterion                          | Requirement                                                                                                           |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `DataFreshnessContract`            | Defined for all 30 data sources in `unified-api-contracts/unified_api_contracts/internal/reference/data_freshness.py` |
| `FreshnessMonitor`                 | Wired in all 9 data-producing services                                                                                |
| `DATA_STALE` event                 | Emitted when age > `warn_age_seconds`                                                                                 |
| `FEED_UNHEALTHY` event             | Emitted when age > `max_age_seconds`; triggers PagerDuty + Telegram                                                   |
| `DATA_AVAILABILITY_RESTORED` event | Emitted when feed recovers                                                                                            |
| Freshness gates in consumers       | `strategy-service` + `execution-service` raise `DataStalenessError`                                                   |
| Daily completeness check           | `check-data-completeness.sh` scheduled via Cloud Scheduler 08:00 UTC                                                  |
| SIT test                           | Injects artificial staleness; verifies `FEED_UNHEALTHY` emission                                                      |

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
ls unified-trading-pm/codex/06-coding-standards/performance-targets.md 2>/dev/null

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

**Goal:** All public symbols in `unified-api-contracts.internal` (UIC, formerly `unified-internal-contracts`) and
`unified-api-contracts` (UAC) `__all__` are consumed by at least one downstream service. All symbols defined in source
are in `__all__` or explicitly in `KNOWN_INTERNAL` allowlist.

**Audit commands:**

```bash
# Run UIC completeness check (UIC is now unified_api_contracts.internal)
python3 unified-api-contracts/scripts/check_uic_completeness.py
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

### §27.X UAC Error Classification Coverage

- Every URDI/UMI adapter that makes external API calls MUST classify errors through UAC
- Check: adapter files should import `classify_venue_error` from `unified_api_contracts`
- Check: adapter files should emit `log_event("ADAPTER_FETCH_FAILED", details={...})` with error_code, action,
  retry_safe
- Every venue in VenueMapping MUST have entries in UAC VENUE_ERROR_MAP
- The Graph returns HTTP 200 for errors — adapters MUST parse response body for `errors` key

**Scoring:** `PASS` — all checkers exit 0; SIT tests pass; all adapters classify errors through UAC. `WARN` — UAC
curation backlog exists but tracked in `contract_completeness_checker_2026_03_10.plan.md`. `FAIL` — UIC has missing
`__all__` entries; OR any `__all__` symbol has zero consumers; OR SIT completeness tests failing; OR any adapter makes
external API calls without UAC error classification.

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

## Section 29 — API Domain Data Coverage

**Goal:** The combination of all API repos collectively serves every domain data type in the system. No domain data is
"orphaned" — produced by libraries/services but inaccessible via any REST API. Since APIs serve UIs, all data must be
queryable.

**Audit commands:**

```bash
# Step 1 — Catalog all API repos and their route endpoints
           risk-and-exposure-service client-reporting-api trading-analytics-api \
           ml-inference-api ml-training-api deployment-api batch-audit-api \
           market-tick-data-service position-balance-monitor-service pnl-attribution-service; do
  echo "=== $api ==="
  rg '@(router|app)\.(get|post|put|delete|patch|websocket)\(' \
    "$api/" --type py --glob '!**/tests/**' -n 2>/dev/null | head -20
done

# Step 2 — Catalog all domain data types from contracts repos (UIC is now unified_api_contracts.internal)
rg 'class \w+\(BaseModel\)' \
  unified-api-contracts/unified_api_contracts/internal/ --type py -n 2>/dev/null | \
  awk -F: '{print $1 ": " $3}'

# Step 3 — Cross-reference: for each UIC domain schema, is it served by an API?
python3 -c "
import pathlib, re
uic_dir = pathlib.Path('unified-api-contracts/unified_api_contracts/internal')
domains = set()
for py in uic_dir.rglob('*.py'):
    if '__pycache__' in str(py): continue
    for line in py.read_text().splitlines():
        m = re.match(r'class (\w+)\(BaseModel\)', line)
        if m: domains.add(m.group(1))

# Check which schemas are referenced in API repos
            'risk-and-exposure-service', 'client-reporting-api', 'trading-analytics-api',
            'ml-inference-api', 'ml-training-api', 'deployment-api', 'batch-audit-api']
served = set()
for api in api_dirs:
    p = pathlib.Path(api)
    if not p.exists(): continue
    for py in p.rglob('*.py'):
        if '.venv' in str(py) or 'tests' in str(py): continue
        content = py.read_text()
        for d in domains:
            if d in content: served.add(d)

orphaned = domains - served
if orphaned:
    print(f'ORPHANED SCHEMAS ({len(orphaned)} not served by any API):')
    for s in sorted(orphaned): print(f'  {s}')
else:
    print('PASS: all UIC schemas served by at least one API')
" 2>/dev/null

# Step 4 — Check domain coverage checklist
# Each domain must have at least one API endpoint or documented N/A reason
python3 -c "
domains = {
    'instruments': [],  # GAP: no API for instrument metadata
    'execution': ['execution-results-api'],
    'strategy': [],  # GAP: no API for strategy management
    'risk': ['risk-and-exposure-service'],
    'features': [],  # GAP: 7 feature services have no API
    'alerts': ['alerting-service'],
    'config': ['config-api'],
    'reporting': ['client-reporting-api', 'trading-analytics-api'],
    'ml': ['ml-inference-api', 'ml-training-api'],
    'deployment': ['deployment-api'],
    'audit': ['batch-audit-api'],
    'positions': ['position-balance-monitor-service'],
    'pnl': ['pnl-attribution-service'],
    'sports': [],  # GAP: no dedicated sports data API
    'defi': [],  # GAP: no DeFi position/wallet data API
    'events': [],  # GAP: no event query API
}
for domain, apis in domains.items():
    if not apis:
        print(f'ORPHANED DOMAIN: {domain} — no API serves this data')
    else:
        print(f'COVERED: {domain} → {apis}')
"
```

**Required state:**

| Criterion                  | Requirement                                                                              |
| -------------------------- | ---------------------------------------------------------------------------------------- |
| All UIC schemas API-served | Every UIC BaseModel is referenced by at least one API repo; orphaned schemas documented  |
| Domain coverage checklist  | Every data domain has ≥1 API endpoint or a documented N/A reason in codex                |
| No orphaned domain data    | No domain data produced by services/libraries that is inaccessible via REST API          |
| Config data served         | `config-api` serves all config types (venue config, system config, feature flags)        |
| Events queryable           | Auth events, system events, audit events are queryable — not just PubSub fire-and-forget |
| Alerts API complete        | `alerting-service` serves all alert types (trade, risk, system, DeFi, data freshness)    |
| Instruments API exists     | Instrument metadata, properties, and definitions are queryable via REST                  |
| Feature data API exists    | Pre-computed feature vectors are queryable (at least latest values per instrument)       |

**Scoring:** `PASS` — all domains have API coverage; orphaned schema count is zero. `WARN` — 1–3 orphaned domains with
active plan to add API endpoints. `FAIL` — any domain with data in services/libraries but no API and no documented
reason; OR config/events/alerts data not fully queryable.

---

## Section 30 — Configuration Architecture & ConfigStore Compliance

**Goal:** All services follow the canonical configuration pattern. Service config extends `UnifiedCloudConfig`. Config
schemas are Pydantic models in `config.py`. Runtime-mutable config uses `ConfigStore` (UTL cloud_interface storage).
Bootstrap config uses `os.environ` only in declared exception files. No ad-hoc config patterns.

**Audit commands:**

```bash
# Step 1 — Check every service config.py extends UnifiedCloudConfig
for svc in execution-service strategy-service alerting-service risk-and-exposure-service \
           pnl-attribution-service position-balance-monitor-service market-tick-data-service \
           market-data-processing-service instruments-service deployment-service \
           features-calendar-service features-commodity-service features-cross-instrument-service \
           features-delta-one-service features-multi-timeframe-service features-onchain-service \
           features-sports-service features-volatility-service; do
  cfg=$(find "$svc/" -name 'config.py' -o -name 'service_config.py' 2>/dev/null | \
    grep -v '.venv\|tests\|__pycache__' | head -1)
  if [ -z "$cfg" ]; then
    echo "MISSING config.py: $svc"
  else
    extends=$(rg 'UnifiedCloudConfig|UnifiedCloudConfig\)' "$cfg" 2>/dev/null | wc -l)
    [ "$extends" -eq 0 ] && echo "NOT EXTENDING UnifiedCloudConfig: $cfg"
  fi
done

# Step 2 — Check ConfigStore usage for runtime-mutable config
rg 'ConfigStore|config_store|get_config_store' --type py \
  --glob '!.venv*' --glob '!**/tests/**' -l

# Step 3 — Check for ad-hoc config patterns (json.load of config files, yaml.safe_load of config)
rg 'json\.load.*config|yaml\.safe_load.*config' --type py \
  --glob '!.venv*' --glob '!**/tests/**' --glob '!**/scripts/**' -n | \
  grep -v 'unified-trading-library/.*config_interface\|deployment-service\|unified-trading-pm' | head -20

# Step 4 — Check config singleton patterns
rg '@lru_cache|_config\s*=\s*\w+Config\(\)' --type py \
  --glob '!.venv*' --glob '!**/tests/**' -n | head -20

# Step 5 — Verify no direct os.environ in service config files (except bootstrap exceptions)
for svc in */; do
  cfg=$(find "$svc" -name 'config.py' -o -name 'service_config.py' 2>/dev/null | \
    grep -v '.venv\|tests\|__pycache__' | head -1)
  [ -z "$cfg" ] && continue
  hits=$(rg 'os\.environ|os\.getenv' "$cfg" 2>/dev/null | wc -l)
  [ "$hits" -gt 0 ] && echo "DIRECT ENV ACCESS in config: $cfg"
done
```

**Required state:**

| Criterion                         | Requirement                                                                                       |
| --------------------------------- | ------------------------------------------------------------------------------------------------- |
| Config extends UnifiedCloudConfig | Every service's config.py/service_config.py inherits from `UnifiedCloudConfig`                    |
| Config schema is Pydantic         | All config classes are Pydantic `BaseSettings` or extend `UnifiedCloudConfig` (also BaseSettings) |
| No direct `os.environ` in config  | Only bootstrap exception files (factory.py, constants.py, config_loader.py) use `os.environ`      |
| ConfigStore for mutable config    | Runtime-changeable config (feature flags, thresholds) read via `ConfigStore`, not env vars        |
| No ad-hoc config loading          | No `json.load(open('config.json'))` or `yaml.safe_load(open('config.yaml'))` in service code      |
| Singleton pattern consistent      | Config instantiated once per process (`@lru_cache(maxsize=1)` or module-level)                    |
| Config documented in codex        | `unified-trading-pm/codex/06-coding-standards/configuration-management.md` covers all patterns    |

### §30.X ConfigStore Load Isolation

- ConfigStore.load_config() MUST use \_env_file=None to prevent .env pollution when loading from cloud storage
- Services loading domain config from cloud storage should not have local .env vars leak into the config model
- Check: UTL cloud_interface persistence.py uses `config_class(_env_file=None, **data)` not `model_validate(data)`

**Scoring:** `PASS` — all services extend UnifiedCloudConfig; zero ad-hoc config; ConfigStore used for mutable config;
ConfigStore load uses \_env_file=None isolation. `WARN` — 1–2 services missing ConfigStore for optional config. `FAIL` —
any service config not extending UnifiedCloudConfig; OR direct `os.environ` in non-bootstrap config; OR ad-hoc config
file loading in service source; OR ConfigStore.load_config() allows .env pollution.

---

## Section 31 — Runtime Topology ↔ Library Abstraction Parity

**Goal:** Every infrastructure component declared in the runtime topology has a corresponding abstraction in the library
layer (UTL cloud_interface). No service should need to access an infrastructure component for which no library
abstraction exists. If the topology says "Redis for caching," UTL cloud_interface must provide a Redis client
abstraction. If it says "PubSub for messaging," UTL cloud_interface must provide `get_pubsub_client()`.

**Audit commands:**

```bash
# Step 1 — Extract infrastructure components from runtime topology
python3 -c "
import yaml, json
try:
    t = yaml.safe_load(open('unified-trading-pm/configs/runtime-topology.yaml'))
    print('Topology version:', t.get('version', 'unknown'))
    # List all infrastructure components
    for profile_name, profile in t.get('deployment_profiles', {}).items():
        for comp in profile.get('infrastructure', []):
            print(f'  INFRA: {comp}')
except Exception as e:
    print(f'Cannot parse topology: {e}')
" 2>/dev/null

# Step 2 — Check UTL cloud_interface factory methods cover all infra components
rg 'def get_\w+_client|def get_\w+_sink|def get_\w+_bus' \
  unified-trading-library/unified_trading_library/cloud_interface/ --type py -n

# Step 3 — Check for direct infra SDK imports in services (should go through UTL cloud_interface)
# Redis
rg 'import redis|from redis' --type py --glob '!.venv*' \
  --glob '!unified-trading-library/unified_trading_library/cloud_interface/**' -n
# Firestore
rg 'from google.cloud import firestore|import firestore' --type py \
  --glob '!.venv*' --glob '!unified-trading-library/unified_trading_library/cloud_interface/**' -n
# Memcached
rg 'import memcache|import pymemcache' --type py --glob '!.venv*' \
  --glob '!unified-trading-library/unified_trading_library/cloud_interface/**' -n
# Kafka (if in topology)
rg 'import kafka|from kafka' --type py --glob '!.venv*' \
  --glob '!unified-trading-library/unified_trading_library/cloud_interface/**' -n
# Direct PubSub (should use get_pubsub_client)
rg 'from google.cloud import pubsub|google.cloud.pubsub' --type py \
  --glob '!.venv*' --glob '!unified-trading-library/unified_trading_library/cloud_interface/**' -n

# Step 4 — Cross-reference: infra declared in topology vs UTL cloud_interface abstractions available
python3 -c "
import pathlib, re
# Known UTL cloud_interface abstractions
uci_dir = pathlib.Path('unified-trading-library/unified_trading_library/cloud_interface')
abstractions = set()
for py in uci_dir.rglob('*.py'):
    for line in py.read_text().splitlines():
        m = re.match(r'def (get_\w+)', line)
        if m: abstractions.add(m.group(1))
print('UTL cloud_interface abstractions:', sorted(abstractions))

# Expected coverage map (update as topology evolves)
required = {
    'get_storage_client': 'GCS/S3 storage',
    'get_pubsub_client': 'PubSub/SNS messaging',
    'get_secret_client': 'Secret Manager',
    'get_query_client': 'BigQuery/Athena',
    'get_cloud_config': 'Cloud config',
}
for func, desc in required.items():
    status = 'PASS' if func in abstractions else 'MISSING'
    print(f'  {status}: {func} ({desc})')
"

# Step 5 — Check service_flows in topology match actual service entry points
python3 -c "
import yaml, pathlib
try:
    t = yaml.safe_load(open('unified-trading-pm/configs/runtime-topology.yaml'))
    for flow_name, flow in t.get('service_flows', {}).items():
        for svc in flow.get('services', []):
            svc_dir = pathlib.Path(svc.get('name', ''))
            if not svc_dir.exists():
                print(f'TOPOLOGY DRIFT: {svc[\"name\"]} in flow {flow_name} but repo not found')
except Exception as e:
    print(f'Cannot parse topology: {e}')
" 2>/dev/null
```

**Required state:**

| Criterion                                | Requirement                                                                                                 |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Infra ↔ UTL parity                      | Every infrastructure component in runtime-topology.yaml has a corresponding UTL cloud_interface abstraction |
| No direct infra SDK in services          | Services never import redis, kafka, firestore, etc. directly — only via UTL cloud_interface                 |
| Storage abstraction                      | `get_storage_client()` covers GCS + S3                                                                      |
| Messaging abstraction                    | `get_pubsub_client()` covers PubSub + SNS/SQS                                                               |
| Secrets abstraction                      | `get_secret_client()` covers GCP Secret Manager + AWS Secrets Manager                                       |
| Query abstraction                        | `get_query_client()` covers BigQuery + Athena (if in topology)                                              |
| Cache abstraction (if Redis in topology) | `get_cache_client()` or equivalent in UTL cloud_interface covers Redis/Memcached                            |
| Topology ↔ repo parity                  | All services in topology `service_flows` exist as repos in workspace                                        |
| No infrastructure orphans                | No infra component provisioned but never abstracted (dead infrastructure cost)                              |

**Scoring:** `PASS` — full parity; every topology component has UTL cloud_interface abstraction; zero direct infra SDK
imports. `WARN` — 1 infra component lacking UTL cloud_interface abstraction but tracked in plan. `FAIL` — any service
directly imports infra SDK that UTL cloud_interface should abstract; OR ≥2 topology components have no library
abstraction; OR topology references non-existent repos.

---

## Section 32 — Format String Safety & Logging Hygiene

**Goal:** No raw error messages used as format strings in logging calls. No malformed format specifiers in production
code. These are silent bugs that cause ValueError crashes at runtime when error messages contain `%` characters.

**Audit commands:**

```bash
# Check for raw error messages used as format strings
rg 'logger\.(warning|error|info)\(_err\.message' --type py --glob '!tests/' --glob '!.venv*' -n
# Fix: Use logger.warning("%s", _err.message, ...) instead

# Check for malformed format specifiers
rg '%\.\.1f' --type py --glob '!.venv*' -n
# Should be %.1f%%

rg '%,d' --type py --glob '!.venv*' -n
# Python doesn't support %,d for thousands separator — use f-strings or locale
```

**Required state:**

| Criterion                        | Requirement                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------- |
| No raw error format strings      | Zero `logger.warning(_err.message, ...)` — use `logger.warning("%s", _err.message)` instead |
| No malformed format specifiers   | Zero `%..1f` or `%,d` patterns in production source                                         |
| Format string safety in adapters | All adapter error logging uses `"%s"` placeholder, not raw message as format string         |

**Scoring:** `PASS` — zero violations. `WARN` — 1–2 occurrences in non-critical paths. `FAIL` — any raw error message
used as format string in production adapter/service code; OR malformed format specifiers in production source.

---

## Key SSOT References for Auditors

- **Repo registry & DAG:** `unified-trading-pm/workspace-manifest.json`
- **Deployment configs (canonical):** `deployment-service/configs/` — checklist._.yaml, venues.yaml,
  RUNTIME_TOPOLOGY_DECISIONS.md, data-catalogue._.yaml, per-service PROTOCOL\_\* env files
- **Runtime topology (canonical SSOT):** `unified-trading-pm/configs/runtime-topology.yaml`
- **Coverage targets:** `unified-trading-pm/cursor-rules/testing/test-coverage-targets.mdc`
- **Stub tracker:** `unified-trading-pm/plans/active/stub_completion_interfaces_and_infra.plan.md`
- **Performance targets:** `unified-trading-pm/codex/06-coding-standards/performance-targets.md`
- **Semver rules:** `unified-trading-pm/plans/active/major_version_bump_approval_gate_2026_03_11.plan.md`
- **Readiness checklist:** `unified-trading-pm/codex/10-audit/REPO_READINESS_CHECKLIST.yaml`
- **Data freshness contracts:** `unified-api-contracts/unified_api_contracts/internal/reference/data_freshness.py`
- **Batch-live symmetry:** `unified-trading-pm/codex/batch-live-symmetry.md`
- **API key phases:** `unified-trading-pm/plans/active/api_keys_and_auth.plan.md`
- **Previous audit reports:** `system-integration-tests/reports/audit_<date>.json`
- **Config architecture:** `unified-trading-pm/codex/06-coding-standards/configuration-management.md`
- **Runtime topology:** `unified-trading-pm/configs/runtime-topology.yaml`
- **UCI factory methods:** `unified-trading-library/unified_trading_library/cloud_interface/factory.py`
- **UIC domain schemas:** `unified-api-contracts/unified_api_contracts/internal/`
- **API domain coverage:** Verify against this audit §29 domain checklist
