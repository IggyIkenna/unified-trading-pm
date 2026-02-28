# Configuration and Compliance Audit — 2026-02-25

**Scope:** unified-trading-system-repos workspace (40 repos, ~30 Python services + UIs)

---

## 1. Configuration Anti-Patterns

### 1.1 os.getenv / os.environ Usage

| Count | Type | Location |
|-------|------|----------|
| **~25** | Production code | `unified-trading-services/` (config.py, client_factory.py, market_category.py, gcp_clients.py, secret_manager.py, dependency_checker.py, gcsfuse_helper.py, cloud_data_provider.py) |
| **~15** | Production code | `market-tick-data-handler/` (config_utils.py, config_base.py) |
| **~25** | Test/conftest | `instruments-service/` (conftest.py, test_cloud_agnostic_paths.py, test_bucket_config.py) |
| **~5** | Test/conftest | `market-tick-data-handler/` (conftest.py) |

**Codex compliance:** `os.getenv`/`os.environ` forbidden in production; config via `UnifiedCloudConfig` / `load_config()`.

**Exceptions (acceptable):**
- `tests/conftest.py` — test setup
- `CLOUD_MOCK_MODE`, `PYTEST_CURRENT_TEST`, `GITHUB_ACTIONS` for CI/test detection
- `GOOGLE_APPLICATION_CREDENTIALS` in SDK bootstrap paths

### 1.2 Empty String Fallbacks

| Count | Pattern | Status |
|-------|---------|--------|
| **0** | `os.getenv("KEY", "")` in production | ✅ None found |
| **0** | `get_config("KEY", "")` in production | ✅ None found |

### 1.3 Hardcoded Configuration Values

| Location | Count | Notes |
|----------|-------|------|
| `.env_template` (workspace root) | 2 | `central-element-323112`, `central-element-323112-e35fb0ddafe2.json` — **P0 violation** |
| `.cursor/`, `unified-trading-pm/` scripts | ~15 | gcloud `--project=central-element-323112` — orchestration scripts |
| `.lobster/scripts/apply-fixes-single-repo.sh` | 1 | Artifact Registry URL `central-element-323112` |
| `unified-trading-pm/scripts/check-private-deps.sh` | 1 | `GCP_PROJECT="central-element-323112"` |

**Per-repo `.env.example`:** Uses `your-gcp-project-id` or similar — ✅ compliant.

### 1.4 Missing .env.example

| Repo | Status |
|------|--------|
| api-contracts | ❌ Missing |
| settlement-ui | ❌ Missing |
| unified-feature-calculator-library | ❌ Missing |
| unified-trading-codex | ❌ Missing |
| unified-trading-pm | ❌ Missing |
| **All others (35)** | ✅ Has |

### 1.5 Configuration Validation

| Pattern | Status |
|---------|--------|
| `unified-config-interface` BaseConfig/UnifiedCloudConfig | ✅ Pydantic validation, `validate_assignment=True` |
| `validate_config_for_startup()` | ✅ Available in UCI |
| `tests/unit/test_config_interface.py` | ⚠️ 3 services missing: instruments-service, strategy-service, ml-training-service (have test_config.py / test_config_extended.py instead) |

---

## 2. Compliance Violations

### 2.1 Missing LICENSE

| Repo | Status |
|------|--------|
| alerting-system | ❌ Missing |
| api-contracts | ❌ Missing |
| execution-service | ❌ Missing |
| unified-trading-services | ❌ Missing |
| unified-domain-client | ❌ Missing |
| unified-feature-calculator-library | ❌ Missing |
| unified-trading-codex | ❌ Missing |
| unified-trading-pm | ❌ Missing |
| **31 others** | ✅ Has |

### 2.2 README

| Status | Count |
|--------|-------|
| ✅ Has README.md | 40 |

### 2.3 Missing CONTRIBUTING.md

| Status | Count |
|--------|-------|
| ✅ Has | 14 |
| ❌ Missing | 26 |

**Repos with CONTRIBUTING:** api-contracts, execution-service, features-calendar-service, features-delta-one-service, features-onchain-service, features-volatility-service, instruments-service, market-data-processing-service, market-tick-data-handler, ml-inference-service, ml-training-service, strategy-service, unified-trading-services, unified-trading-deployment-v3, unified-trading-pm (partial).

### 2.4 CODE_OF_CONDUCT

| Status | Count |
|--------|-------|
| ❌ Missing | 40 |

---

## 3. CI/CD Health

### 3.1 GitHub Actions Workflows

| Status | Count | Repos |
|--------|-------|-------|
| ✅ Has `.github/workflows` | 38 | Most services, UIs, libraries |
| ❌ Missing | 2 | settlement-ui, unified-feature-calculator-library |

### 3.2 Quality Gates

| Status | Count | Repos |
|--------|-------|-------|
| ✅ Has `scripts/quality-gates.sh` | 38 | Most repos |
| ❌ Missing | 2 | settlement-ui, unified-trading-codex |

### 3.3 Quickmerge

| Status | Count | Repos |
|--------|-------|-------|
| ✅ Has `scripts/quickmerge.sh` | 37 | Most repos |
| ❌ Missing | 3 | settlement-ui, unified-feature-calculator-library, unified-ml-interface |

### 3.4 Docker

| Status | Count | Repos |
|--------|-------|-------|
| ✅ Has Dockerfile | 23 | Python services, shared libs |
| ❌ Missing (expected) | 17 | UIs (React/Vue), api-contracts, matching-engine-library, unified-defi-execution-interface, unified-domain-client, unified-feature-calculator-library, unified-trading-codex, unified-trading-pm |

### 3.5 quality-gates.yml

All repos with `.github/workflows` include `quality-gates.yml` or equivalent.

---

## 4. Documentation Coverage

### 4.1 Docstring Coverage (Sample)

| Repo | Documented | Total | % |
|------|------------|-------|---|
| instruments-service | 529 | 612 | 86.4% |
| unified-trading-services | 632 | 739 | 85.5% |
| market-tick-data-handler | 685 | 759 | 90.3% |

### 4.2 Required Test Files

| File | Status |
|------|--------|
| `tests/unit/test_event_logging.py` | ✅ 14/14 services have |
| `tests/unit/test_config_interface.py` | ⚠️ 3 services use test_config.py / test_config_extended.py instead |

---

## 5. Code Style Violations

### 5.1 E501 (Line Length > 120)

| Repo | Violations |
|------|------------|
| instruments-service | 2 |
| unified-trading-services | 1 |
| market-tick-data-handler | 117 |
| strategy-service | 139 |
| execution-service | 205 |
| **Total (5 repos)** | **464** |

### 5.2 __init__.py

| Status | Notes |
|--------|-------|
| ✅ | All Python packages have `__init__.py` |

---

## 6. Compliance Checklist

| Category | Pass | Fail | Notes |
|----------|------|------|-------|
| Config: no os.getenv in production | 0 | 2 | unified-trading-services, market-tick-data-handler |
| Config: no hardcoded project IDs | 0 | 1 | .env_template |
| Config: .env.example present | 35 | 5 | api-contracts, settlement-ui, unified-feature-calculator-library, unified-trading-codex, unified-trading-pm |
| Config: validation | ✅ | — | UCI BaseConfig/UnifiedCloudConfig |
| LICENSE | 31 | 9 | — |
| README | 40 | 0 | — |
| CONTRIBUTING | 14 | 26 | — |
| CODE_OF_CONDUCT | 0 | 40 | — |
| GitHub Actions | 38 | 2 | settlement-ui, unified-feature-calculator-library |
| Quality gates | 38 | 2 | settlement-ui, unified-trading-codex |
| Quickmerge | 37 | 3 | settlement-ui, unified-feature-calculator-library, unified-ml-interface |
| Docker (where expected) | 23 | 0 | UIs excluded |
| E501 line length | — | 464 | 5 repos sampled |

---

## 7. Remediation Priorities

### P0 (Blocking)

1. **Remove hardcoded project ID from `.env_template`**
   - Replace `central-element-323112` with `your-gcp-project-id`
   - Replace `central-element-323112-e35fb0ddafe2.json` with `path/to/your-service-account.json`

2. **Replace os.getenv in production code**
   - `unified-trading-services`: config.py, client_factory.py, market_category.py, gcp_clients.py, secret_manager.py, dependency_checker.py, gcsfuse_helper.py, cloud_data_provider.py
   - `market-tick-data-handler`: config_utils.py, config_base.py
   - Use `UnifiedCloudConfig` / `load_config()` and Pydantic `validation_alias`

### P1 (High)

3. **Add LICENSE to 9 repos**
   - alerting-system, api-contracts, execution-service, unified-trading-services, unified-domain-client, unified-feature-calculator-library, unified-trading-codex, unified-trading-pm

4. **Add .env.example to 5 repos**
   - api-contracts, settlement-ui, unified-feature-calculator-library, unified-trading-codex, unified-trading-pm

5. **Fix settlement-ui and unified-feature-calculator-library**
   - Add `.github/workflows`, `scripts/quality-gates.sh`, `scripts/quickmerge.sh`
   - Add `scripts/quickmerge.sh` to unified-ml-interface

6. **Fix E501 violations**

   - market-tick-data-handler: 117
   - strategy-service: 139
   - execution-service: 205

### P2 (Medium)

7. **Add CONTRIBUTING.md to 26 repos**

8. **Add CODE_OF_CONDUCT** (optional; consider workspace-level or single repo)

9. **Align test_config naming**
   - instruments-service, strategy-service, ml-training-service: add `test_config_interface.py` or rename to match UCI policy

### P3 (Low)

10. **Orchestration scripts**
    - `.cursor/`, `unified-trading-pm/` scripts using `central-element-323112` — use env var or config
    - `.lobster/scripts/apply-fixes-single-repo.sh` — Artifact Registry URL from env

---

## 8. Summary Metrics

| Metric | Value |
|--------|-------|
| Configuration anti-patterns (os.getenv, prod) | ~40 |
| Hardcoded project IDs | ~20 (mostly scripts) |
| Missing .env.example | 5 |
| Missing LICENSE | 9 |
| Missing CONTRIBUTING | 26 |
| Missing CODE_OF_CONDUCT | 40 |
| Repos missing CI/CD | 2–3 |
| E501 violations (5 repos) | 464 |
| Docstring coverage (avg) | ~87% |

---

*Audit conducted 2026-02-25. Per plan placement rules, this doc lives in `unified-trading-pm/plans/ai/`.*
