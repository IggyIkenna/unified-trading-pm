# Security Audit Report — Unified Trading System Repos

**Date:** 2026-02-25  
**Scope:** All Python files, config files (.env, .yaml, .json), .gitignore, Dockerfiles, cloudbuild.yaml across 30+ repos  
**Focus:** Hardcoded secrets, project IDs, insecure patterns, credential exposure, dependencies, .gitignore, env leaks, unsafe file ops

---

## Executive Summary

| Severity | Count | Status |
|----------|-------|--------|
| **Critical** | 3 | Immediate remediation |
| **High** | 5 | Address within 1 sprint |
| **Medium** | 8 | Security best practices |
| **Low** | 4 | Informational |

**Strengths:** Quality gates in instruments-service include security checks (credential negation, hardcoded project ID, private keys, Dockerfile secrets). Production code uses `get_secret_with_fallback` for API keys. No SQL injection, command injection, or unsafe deserialization found.

**Gaps:** Hardcoded project ID in scripts; pip-audit not yet in quality gates; some scripts still use `os.environ.get` for API keys.

---

## 1. Critical Security Violations

### C1. Hardcoded GCP Project ID in Executable Scripts

**Risk:** Project ID exposure; multi-tenant failure; targeted attacks if project is known.

| File | Line | Finding |
|------|------|---------|
| `unified-trading-pm/scripts/check-private-deps.sh` | 19 | `GCP_PROJECT="central-element-323112"` |
| `unified-trading-pm/scripts/pre-flight-audit-agent.sh` | 26 | `--project=central-element-323112` |
| `.cursor/scripts/pre-flight-audit-agent.sh` | 26 | Same |
| `unified-trading-pm/scripts/coding-standards-align-agent.sh` | 144 | `--project=central-element-323112` |
| `unified-trading-pm/plans/ai/tasks_claude_code/run-parallel-agents.sh` | 50 | `--project=central-element-323112` |
| `unified-trading-pm/plans/ai/tasks_claude_code/orchestrator-simple.sh` | 71 | Same |
| `unified-trading-pm/plans/ai/tasks_claude_code/orchestrator-test.sh` | 49 | Same |
| `.cursor/scripts/coding-standards-align-agent.sh` | 141 | Same |
| `.cursor/plans/tasks_claude_code/run-parallel-agents.sh` | 50 | Same |
| `.cursor/plans/tasks_claude_code/orchestrator-simple.sh` | 71 | Same |
| `.cursor/plans/tasks_claude_code/orchestrator-test.sh` | 49 | Same |

**Exploit scenario:** Attacker with repo access sees production project ID; can target GCP resources, enumerate buckets, or attempt IAM abuse.

**Remediation:**
```bash
# Replace with:
GCP_PROJECT="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
# Or require: GCP_PROJECT_ID env var, fail if unset
```

---

### C2. Cursor API Key Written to World-Readable Temp File

**Risk:** Key written to `/tmp/cursor_key.txt`; other users on shared machines may read it.

| File | Line | Finding |
|------|------|---------|
| `unified-trading-pm/scripts/pre-flight-audit-agent.sh` | 26, 29 | `gcloud secrets ... > /tmp/cursor_key.txt`; `CURSOR_API_KEY=$(cat /tmp/cursor_key.txt)` |
| `.cursor/scripts/pre-flight-audit-agent.sh` | Same | Same |
| `unified-trading-pm/plans/ai/tasks_claude_code/run-parallel-agents.sh` | 50 | Same pattern |
| `.cursor/plans/tasks_claude_code/run-parallel-agents.sh` | 50 | Same |

**Exploit scenario:** On multi-user or shared CI runners, another process or user reads `/tmp/cursor_key.txt` and exfiltrates the API key.

**Remediation:**
```bash
# Use process substitution or secure temp file:
CURSOR_API_KEY=$(gcloud secrets versions access latest --secret=cursor-api-key --project="$GCP_PROJECT_ID" 2>/dev/null)
# Or: TMPFILE=$(mktemp -u); gcloud ... > "$TMPFILE"; CURSOR_API_KEY=$(cat "$TMPFILE"); rm -f "$TMPFILE"
```

---

### C3. Hardcoded Artifact Registry URL with Project ID

**Risk:** Same as C1; also breaks in non-production environments.

| File | Line | Finding |
|------|------|---------|
| `.lobster/scripts/apply-fixes-single-repo.sh` | 86 | `extra-index-url = https://asia-northeast1-python.pkg.dev/central-element-323112/unified-libraries/simple/` |

**Remediation:** Use `$GCP_PROJECT_ID` or `$PROJECT_ID` from environment.

---

## 2. High-Risk Patterns

### H1. Scripts Using os.environ.get for API Keys (Documented Technical Debt)

**Risk:** API keys in environment can leak via process listing, core dumps, or error messages.

| File | Context | Finding |
|------|---------|---------|
| `scripts/test_batch_cost_comparison.py` | Per INSTRUMENT_AGGREGATION plan | `os.environ.get("DATABENTO_API_KEY")` |
| `scripts/find_subgraph_ids.py` | Same | `os.environ.get("THEGRAPH_API_KEY", "test-key")` — fallback "test-key" is weak |
| `dependency_checker.py` | Per plan | `os.environ.get(env_var)` as fallback |

**Standard:** Use `get_secret_with_fallback()` from unified-cloud-services. Primary = Secret Manager; env fallback only for local dev.

**Remediation:** Migrate to `get_secret_with_fallback(secret_name, project_id, fallback_env_var="DATABENTO_API_KEY")`.

---

### H2. Schema Validation Docs with Hardcoded Project ID

**Risk:** Documentation used as copy-paste source; propagates hardcoded IDs.

| File | Lines | Finding |
|------|-------|---------|
| `unified-trading-pm/plans/ai/code_optimizations_and_ci_cd_alignment/05-schema-validation.md` | 53, 56, 59–60, 96, 104, 335, 386, 402, 470, 477, 498, 502 | `gs://central-element-323112-unified-trading-data/`, `project_id="central-element-323112"` |

**Remediation:** Replace with `$GCP_PROJECT_ID` or `your-project-id` placeholders.

---

### H3. Quality Gates Set GOOGLE_CLOUD_PROJECT (Deprecated)

**Risk:** Inconsistent config; rules require `GCP_PROJECT_ID` only.

| File | Line | Finding |
|------|------|---------|
| `instruments-service/scripts/quality-gates.sh` | 131 | `export GOOGLE_CLOUD_PROJECT="test-project"` |

**Remediation:** Use `export GCP_PROJECT_ID="test-project"` (or `TEST_GCP_PROJECT_ID`). Remove `GOOGLE_CLOUD_PROJECT` per `.cursor/rules/single-project-id-env-var.mdc`.

---

### H4. .gitignore: instruments-service Excludes All *.json

**Risk:** Overly broad `*.json` can accidentally exclude config; `!package.json` etc. create negation complexity. Audit (Feb 2022) flagged `!central-element-323112-e35fb0ddafe2.json` — current instruments-service .gitignore does NOT have this; unified-cloud-services .gitignore also clean. **Verify no repo has credential negation.**

**Status:** instruments-service and unified-cloud-services .gitignore reviewed — no `!central-element` or `!*credentials*.json`. Quality gates check: `rg "!central-element|!.*credentials.*\.json" .gitignore`.

---

### H5. .env Files — Git Tracking

**Risk:** If `.env` is ever committed, secrets (API keys, project IDs) are exposed.

**Status:** `.env` is in .gitignore for instruments-service and unified-cloud-services. `.env_template` exists at workspace root (template only). **Recommendation:** Run `git ls-files | grep '\.env'` in each repo to confirm no .env is tracked.

---

## 3. Medium-Risk Issues (Security Best Practices)

### M1. No pip-audit in Quality Gates

**Risk:** Known CVEs in dependencies may go undetected.

**Status:** pip-audit is planned (Phase 4 of quality-gates-audit-factors-propagation) but not yet in template. instruments-service quality-gates.sh mentions "pip-audit, bandit" in header but no pip-audit step found in script.

**Remediation:** Add `pip-audit` (or `pip-audit --strict`) to quality-gates-template.sh and propagate to all repos.

---

### M2. Production Readiness Validators Non-Blocking

**Risk:** Security validators (SEC-03, etc.) run but do not block merge.

**Status:** Per `.cursor/rules/validator-integration.mdc`, validators are Step 5 in quality gates, non-blocking. Provides visibility without blocking workflow.

**Recommendation:** Consider making SEC-* validators blocking for production branches; keep non-blocking for feature branches.

---

### M3. Cloud Build GH_PAT in Secret Manager

**Status:** instruments-service cloudbuild.yaml correctly uses `secretEnv: ['GH_PAT']` and `availableSecrets.secretManager`. No hardcoded tokens. ✅

---

### M4. Dockerfiles — No Hardcoded Secrets

**Status:** Grep for `ENV.*KEY|ENV.*SECRET|ENV.*PASSWORD` in Dockerfiles found no matches. Quality gates check: `rg "^ENV\s+[A-Z_]*(KEY|SECRET|PASSWORD|TOKEN|CREDENTIAL)"`. ✅

---

### M5. No SQL Injection Vectors

**Status:** No SQL queries with string formatting found. No `execute(.*%)` or `f"...SELECT..."` patterns. ✅

---

### M6. No Command Injection (subprocess shell=True)

**Status:** No `subprocess.call/run/Popen(..., shell=True)` in Python files. ✅

---

### M7. No Unsafe Deserialization

**Status:** No `pickle.loads`, `yaml.load()` (unsafe), or `marshal.loads`. `yaml.safe_load` used in validate-alignment.py. ✅

---

### M8. Path Traversal

**Status:** `open(path + user_input)` or `Path(user_input)` patterns not found. Path manipulation in fix-workspace-alignment scripts is for internal structure, not user input. ✅

---

## 4. Low-Risk / Informational

### L1. Test Project ID Placeholder

**File:** `.lobster/scripts/improve-tests-single-repo.sh` line 51  
**Finding:** `TEST_PROJECT_ID = "test-project-12345"` — acceptable test placeholder.

---

### L2. MASTER CICD Plan Examples

**File:** `unified-trading-pm/plans/ai/code_optimizations_and_ci_cd_alignment/00-MASTER-CICD-PLAN.md`  
**Finding:** Example `GCP_PROJECT_ID=central-element-323112` — documentation only; use placeholder in public docs.

---

### L3. Logging of Config Values

**Status:** No `logger.info(config.secret)` or `print(api_key)` patterns found in production code. Scripts use `print` for status, not secrets.

---

### L4. API Keys in URLs

**Status:** No API keys in URL query params found. Cloud Build uses Secret Manager for GH_PAT. ✅

---

## 5. Remediation Priority Matrix

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| P0 | C1: Replace hardcoded project ID in scripts with env var | 2–4 hrs | High |
| P0 | C2: Avoid writing Cursor API key to /tmp | 1 hr | High |
| P0 | C3: Parameterize Artifact Registry URL in lobster script | 30 min | Medium |
| P1 | H1: Migrate scripts to get_secret_with_fallback | 4–8 hrs | High |
| P1 | H2: Replace hardcoded IDs in schema-validation docs | 1 hr | Medium |
| P1 | H3: Use GCP_PROJECT_ID in quality-gates test env | 15 min | Low |
| P2 | M1: Add pip-audit to quality gates | 2–4 hrs | Medium |
| P2 | Verify no .env committed: `git ls-files \| grep '\.env'` | 15 min | High if found |

---

## 6. Quality Gates Security Checks (Already Implemented)

instruments-service `scripts/quality-gates.sh` includes:

- `rg "!central-element|!.*credentials.*\.json" .gitignore` — blocks credential negation
- `rg "central-element-323112"` in tests and production — blocks hardcoded project ID
- Service account JSON detection (`"type": "service_account"`)
- Private key detection (`BEGIN RSA PRIVATE KEY`, etc.)
- Dockerfile ENV secrets (`ENV *KEY*=`, etc.)
- Hardcoded credential path (`central-element-323112-*.json`)
- `os.getenv` empty fallback detection

**Recommendation:** Ensure these checks are in quality-gates-template.sh and propagated to all Python repos.

---

## 7. References

- `.cursor/rules/quality-gates-audit-factors.mdc` — P1 blocking factors
- `.cursor/rules/no-hardcoded-project-ids.mdc` — Project ID standard
- `.cursor/rules/instruments-domain-and-api-keys.mdc` — API key via get_secret_with_fallback
- `unified-trading-pm/plans/ai/INSTRUMENT_AGGREGATION_AND_API_KEYS_PLAN.md` — Script migration list
- `unified-trading-codex/06-coding-standards/quality-gates.md` — Quality gates spec
