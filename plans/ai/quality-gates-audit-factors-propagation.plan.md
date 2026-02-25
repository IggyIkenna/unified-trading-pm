---
name: Quality Gates Audit Factors Propagation
overview: Extend quality gates hardening with 11 audit factors across all Python repos. Update Cursor rules and Codex docs, template, instruments-service (reference), then propagate to 25 repos. Add pip-audit and security validators.
todos:
  - id: phase0-cursor-rules-codex
    content: "Phase 0: Create quality-gates-audit-factors.mdc, update .cursorrules, quality-gates.md, README.md, audit-remediation-guide.md"
    status: completed
  - id: phase1-template
    content: "Phase 1: Add rg checks (gitignore credentials, hardcoded project ID, broad except), large-file warning, pip-audit step, validators to quality-gates-template.sh"
    status: completed
  - id: phase2-gitignore
    content: "Phase 2.1: Remove !central-element-*.json from instruments-service .gitignore; ensure credential JSON never committed"
    status: completed
  - id: phase2-project-id
    content: "Phase 2.2: Replace central-element-323112 with test-project in instruments-service tests (test_performance, conftest, test_cloud_agnostic, test_cloud_agnostic_paths)"
    status: completed
  - id: phase2-except
    content: "Phase 2.3: Replace broad except Exception in instrument_processing_service, instruments_service, cloud_data_provider, corporate_actions/adapter"
    status: completed
  - id: phase2-any
    content: "Phase 2.4: Replace Any types with Protocol/TypedDict/TypeVar in instruments-service production code"
    status: pending
  - id: phase2-lazy-imports
    content: "Phase 2.5: Move lazy imports to top in dependency_checker.py; use TYPE_CHECKING if needed"
    status: pending
  - id: phase2-remaining
    content: "Phase 2.6-2.8: Test coverage to 50%, document os.getenv exceptions, plan instrument_processing_service split"
    status: pending
  - id: phase3-propagate
    content: "Phase 3: Propagate template + fixes to 25 Python repos (4 parallel agents); fix .gitignore and tests per repo"
    status: completed
  - id: phase4-pip-audit
    content: "Phase 4: Add pip-audit to quality-gates-template.sh, GitHub Actions, and all repo quality-gates.sh"
    status: completed
  - id: phase5-validators
    content: "Phase 5: Change validators from --category alignment to --category all (alignment + security + hardening)"
    status: completed
  - id: env-stop-tracking
    content: "ALL REPOS: Commit git rm --cached .env change (stop tracking .env; .env for local dev only; CI/Cloud Build use env injection)"
    status: pending
  - id: env-uv-lock-pip-audit
    content: "ALL REPOS: Add pip-audit to dev deps, run uv lock (with path deps available) so uv.lock includes pip-audit"
    status: pending
  - id: env-local-setup
    content: "ALL REPOS: Ensure .env.example exists; document: copy to .env and fill values; .env remains untracked"
    status: pending
  - id: env-quality-gates
    content: "ALL REPOS: pip-audit runs in quality gates once uv pip install -e \".[dev]\" installs it"
    status: pending
  - id: bypass-audit-instruments
    content: "Bypass hardening (instruments-service): Audit QUALITY_GATE_BYPASS_AUDIT.md; fix invalid exceptions (type: ignore, Ruff E722/E402, import whitelist, test skips); keep only logical exceptions per cursor rules"
    status: in_progress
  - id: bypass-audit-all-repos
    content: "Bypass hardening (ALL REPOS): Create QUALITY_GATE_BYPASS_AUDIT.md per repo; fix invalid bypasses; no shortcuts"
    status: pending
isProject: true
---

# Quality Gates Audit Factors Propagation Plan

**Scope:** Extend quality gates hardening with 11 audit factors across all Python repos.
**Reference:** Previous plan (phases 1–4 completed: template, instruments-service, 25 repos, UI verification).
**Source:** Audit findings from instruments-service and workspace-wide scan.

---

## Summary: 11 Audit Factors


| #   | Factor                               | Priority | Blocking? | Action                                                                   |
| --- | ------------------------------------ | -------- | --------- | ------------------------------------------------------------------------ |
| 2   | .gitignore allows credentials file   | P1       | Yes       | Remove `!central-element-*.json`; ensure credential JSON never committed |
| 3   | Hardcoded project ID fallbacks       | P1       | Yes       | Replace real IDs with `test-project` in tests; add rg check              |
| 4   | Broad except Exception usage         | P1       | Yes       | Add rg check; use decorators/specific exceptions                         |
| 5   | Any type usage                       | P1       | Yes       | Already in template (Check 8c); enforce across repos                     |
| 6   | Lazy imports in dependency_checker   | P2       | No        | Move to top; use TYPE_CHECKING; document whitelist                       |
| 7   | Test coverage below 50%              | P2       | No        | Raise MIN_COVERAGE to 50% for production readiness                       |
| 8   | No dependency vulnerability scanning | P2       | No        | Add pip-audit to quality gates                                           |
| 9   | Validators only alignment            | P2       | No        | Add `--category security` (and possibly hardening)                       |
| 10  | Large files near limit               | P2       | No        | Plan split; add warning at 1200 lines                                    |
| 11  | os.getenv in non-production code     | P2       | No        | Document exceptions; prefer config where feasible                        |


---

## Phase 0: Update Cursor Rules and Codex Docs (First)

**Purpose:** Document the 11 audit factors so Cursor and agents follow them. Codex maintenance: "When establishing new patterns, update codex. Then update workspace/per-repo rules."

### Cursor rules (`.cursor/rules/`)

- **New or update:** `quality-gates-audit-factors.mdc` — Document all 11 factors, blocking vs non-blocking, and enforcement (rg checks, pip-audit, validators).
- **Update:** `.cursorrules` — Add reference to the new rule in Anti-Patterns or relevant section.
- **Existing rules to cross-reference:** `strict-type-checking.mdc`, `no-empty-fallbacks.mdc`, `event-logging.mdc`.

### Codex docs (`unified-trading-codex/`)

- **Update:** `06-coding-standards/quality-gates.md` — Add section "Audit Factors (11)" with the table, priorities, and links to rules.
- **Update:** `06-coding-standards/README.md` — Add bullets for credentials in .gitignore, no hardcoded project IDs in tests, broad except Exception.
- **Update or create:** `06-coding-standards/audit-remediation-guide.md` — If it exists, add these factors; otherwise reference quality-gates.md.

---

## Phase 1: Update quality-gates-template.sh and quality-gates.md

**Files:**

- `unified-trading-codex/06-coding-standards/quality-gates-template.sh`
- `unified-trading-codex/06-coding-standards/quality-gates.md`

**Changes:**

1. **Check 2b: .gitignore credentials (P1)**
  - Add rg check: `rg "!central-element|!.*credentials.*\.json" .gitignore`
  - Fail if negation allows credential JSON files to be committed
2. **Check 3b: Hardcoded project ID in tests (P1)**
  - Add rg check: `rg "central-element-323112|get_config.*central-element" tests/`
  - Fail if real project ID found in tests
3. **Check 4b: Broad except Exception (P1)**
  - Add rg check: `rg "except Exception:" --type py --glob "!tests/**" $SOURCE_DIR/`
  - Fail if found (use decorators or specific exceptions)
4. **Check 8b: Large files warning (P2)**
  - Add warning (not fail) when file >1200 lines: "Plan split before 1500"
5. **Add pip-audit step (P2)**
  - After tests: `pip-audit` (or `uv pip install pip-audit && pip-audit`) — non-blocking if not installed
6. **Update validators step (P2)**
  - Change `--category alignment` to `--category alignment --category security` (or run both)
7. **Document MIN_COVERAGE**
  - Add: `RECOMMENDED_COVERAGE=50` (informational; MIN_COVERAGE stays 35 for blocking)

---

## Phase 2: Fix instruments-service (Reference Implementation)

**Repos:** `instruments-service` only (template for propagation)

### 2.1 .gitignore (P1)

**File:** `instruments-service/.gitignore`

- Remove: `!central-element-323112-e35fb0ddafe2.json`
- Ensure: `*.json` or `*credentials*.json` or `*central-element*.json` ignores credential files
- Add if missing: `*credentials*.json`, `*central-element*.json` (or ensure no negation)

### 2.2 Hardcoded project ID in tests (P1)

**Files:**

- `tests/integration/test_performance.py`: Replace `get_config("GCP_PROJECT_ID", "central-element-323112")` with `get_config("GCP_PROJECT_ID", "test-project")` (4 uses)
- `tests/conftest.py`: Replace bucket names `instruments-store-test-*-central-element-323112` with `instruments-store-test-*-test-project` (or use env var)
- `tests/unit/test_cloud_agnostic.py`: Replace `"central-element-323112"` with `"test-project"`
- `tests/unit/test_cloud_agnostic_paths.py`: Adjust assertions to use placeholder

### 2.3 Broad except Exception (P1)

**Files (high count):**

- `instrument_processing_service.py` (12)
- `instruments_service.py` (10)
- `cloud_data_provider.py` (5)
- `corporate_actions/adapter.py` (9)

**Action:** Replace with `@handle_api_errors` / `@handle_storage_errors` or specific exceptions; re-raise with context. Prioritize production code paths.

### 2.4 Any type usage (P1)

**Files:** `instrument_processing_service.py`, `instruments_service.py`, `adapter_loader.py`, `defi_processor.py`, `ccxt_service.py`, etc.

**Action:** Replace with Protocol, TypedDict, TypeVar, or concrete types per `.cursor/rules/strict-type-checking.mdc`. Exception: `dict[str, Any]` for non-finite nested dicts with `# type: ignore[reportAny]`.

### 2.5 Lazy imports in dependency_checker.py (P2)

**File:** `instruments_service/app/core/dependency_checker.py`

- Lines 124, 193, 256: Move imports to top
- Use `TYPE_CHECKING` for optional deps if needed
- Add to whitelist if circular import is unavoidable (document with comment)

### 2.6 Test coverage (P2)

- Add integration/e2e tests for core flows and error paths
- Target: 50% (recommended); 35% remains blocking minimum

### 2.7 os.getenv / get_config in non-production (P2)

**Files:** `pytest_load_env.py`, `conftest.py`, `run_quality_gates.py`, `find_subgraph_ids.py`

- Document exceptions in codex or .cursorrules
- Prefer config classes where feasible

### 2.8 Large file planning (P2)

**File:** `instrument_processing_service.py` (~1179 lines)

- Add to backlog: split by SRP per `file-splitting-guide.md` before adding more logic

---

## Phase 3: Propagate to All Python Repos

**Repos (25):** Libraries (7), services (14), utils (4).

**Strategy:** Parallel agents (max 4) — each repo is independent.

**Per-repo tasks:**

1. Copy new checks from template to `scripts/quality-gates.sh`
2. Fix .gitignore credentials negation (if present)
3. Fix hardcoded project ID in tests (if present)
4. Fix broad except Exception (prioritize P1 files)
5. Fix Any type usage (prioritize P1 files)
6. Run quality gates and verify

**Repos with `!central-element-*.json` in .gitignore (fix first):**

- instruments-service
- unified-trading-deployment-v3
- unified-trading-deployment-v3
- market-tick-data-handler
- market-data-processing-service
- features-onchain-service
- ml-inference-service
- features-volatility-service
- features-calendar-service

**Repos with `*credentials*.json` or `*central-element*.json` (correct pattern):**

- strategy-service, ml-training-service, features-delta-one-service, etc.

---

## Phase 4: Add pip-audit to CI

**Files:**

- `unified-trading-codex/06-coding-standards/quality-gates-template.sh`
- `unified-trading-deployment-v3/.github/workflows/quality-gates.yml` (template for services)
- Each repo's `quality-gates.sh`

**Steps:**

1. Add `pip-audit` to dev deps in pyproject.toml (or run via `uv pip install pip-audit`)
2. Add step: `pip-audit` (or `pip-audit --strict` for blocking)
3. Document: non-blocking initially; can make blocking after baseline clean

---

## Phase 5: Validators — Add Security Category

**File:** `instruments-service/scripts/quality-gates.sh` (and template)

**Current:**

```bash
"${REPO_ROOT}/unified-trading-codex/scripts/run-all-validators.sh" --category alignment --failed-only
```

**Change to:**

```bash
"${REPO_ROOT}/unified-trading-codex/scripts/run-all-validators.sh" --category alignment --failed-only
"${REPO_ROOT}/unified-trading-codex/scripts/run-all-validators.sh" --category security --failed-only
```

Use `--category all` to run alignment + hardening + security in one call. Validators are non-blocking (informational).

---

## Phase 6: .env + pip-audit (ALL REPOS)

**Context:** .env was only for local development. CI, Cloud Build, and UTD v3 use explicit env injection, substitution variables, and Secret Manager. Removing .env from git does not affect deployments.

### 6.1 Stop tracking .env (per repo where applicable)

- **Already done:** `git rm --cached .env` was run in repos that had .env tracked
- **Action:** Commit this change in each affected repo
- **Repos to check:** Any repo where .env was previously tracked (e.g. instruments-service)

### 6.2 Update lock file with pip-audit

- Add `pip-audit` to `[project.optional-dependencies]` dev in pyproject.toml
- Run `uv lock` from workspace root (with path deps available) so uv.lock includes pip-audit
- Commit uv.lock

### 6.3 Local .env setup

- Ensure `.env.example` exists in each repo
- Document: Copy `.env.example` to `.env` and fill in your values
- `.env` will remain untracked (in .gitignore)

### 6.4 Quality gates

- pip-audit will run once `uv pip install -e ".[dev]"` (or equivalent) installs it
- Add pip-audit step to quality-gates.sh (graceful skip if not installed)

### Repos (Python + UI with quality-gates.sh)

**Services (14):** instruments-service, market-tick-data-handler, market-data-processing-service, strategy-service, execution-services, ml-training-service, ml-inference-service, features-calendar-service, features-volatility-service, features-delta-one-service, features-onchain-service, position-balance-monitor-service, risk-and-exposure-service, pnl-attribution-service, alerting-system

**Libraries (7):** unified-cloud-services, unified-config-interface, unified-events-interface, unified-market-interface, unified-trade-execution-interface, unified-domain-services, execution-algo-library

**Utils (2):** unified-trading-deployment-v3, unified-trading-deployment-v3

**UIs (8):** batch-audit-ui, logs-dashboard-ui, ml-deployment-ui, trading-analytics-ui, client-reporting-ui, live-health-monitor-ui, onboarding-ui, backtest-ui

**Note:** Repos that intentionally track .env (e.g. market-data-processing-service with `!.env`) — evaluate per repo; standard is .env untracked for local dev.

---

## Phase 7: Quality Gate Bypass Hardening (No Shortcuts)

**CRITICAL — Only Audited Exceptions May Pass:** basedpyright must pass. Only bypasses explicitly documented in each repo's `QUALITY_GATE_BYPASS_AUDIT.md` (sections 2.1, 2.2, 2.3) are allowed. Fix all other type errors. Never relax rules, add baseline files, or downgrade reportAny/reportUnknown*.

**Source:** `instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md` — inventory of exceptions, exclusions, whitelists. Many are invalid; fix root causes per cursor rules. Propagate to all repos.

### 7.1 Valid exceptions (keep per cursor rules)


| Category             | Valid                                                                                                                                | Rationale               |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------- |
| **Import whitelist** | `adapter_loader.py` (lazy loading), `__init__.py` (lazy submodule), `symbol_parser.py`, `canonical_key_generator.py` (TYPE_CHECKING) | Design pattern          |
| **Import whitelist** | `cloud_instrument_storage.py`, `parser.py`, `ccxt_service.py` (optional deps)                                                        | Optional deps           |
| **type: ignore**     | Pydantic validators (`def validate_*(cls, v: object)`), CCXT untyped (`cast(dict[str, Any], ...)`), yfinance return types            | Third-party lacks stubs |
| **Path exclusions**  | `tests/`**, `scripts/`** for print, os.getenv, bare except                                                                           | Tests/scripts exempt    |
| **noqa F401**        | Side-effect import in `__init__.py`                                                                                                  | Intentional             |


### 7.2 Invalid exceptions (fix — no shortcuts)


| Category                          | Count                        | Action                                                                                                                                                                     |
| --------------------------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Import whitelist**              | 6+ files (circular import)   | Fix circular imports: `dependency_checker.py`, `instruments_service.py`, `live_mode_handler.py`, `corporate_actions_*.py` — use TYPE_CHECKING, move to top, or restructure |
| **type: ignore[reportAny]**       | 18                           | Replace with Protocol, TypedDict, TypeVar, or concrete types per strict-type-checking.mdc; keep only for third-party (yfinance, CCXT, Pydantic)                            |
| **Ruff E722** (bare except)       | Global + scripts             | Remove; use specific exceptions or `@handle_api_errors`                                                                                                                    |
| **Ruff E402** (import not at top) | `cli/main.py`, `conftest.py` | Move imports to top where possible; document if dotenv-before-import required                                                                                              |
| **pyright: ignore**               | 6                            | Fix underlying type issues; avoid suppressors                                                                                                                              |
| **Dict[str, Any] exclusion**      | Blanket                      | Tighten: require `# type: ignore[reportAny]` per use; document in code                                                                                                     |
| **Test skips**                    | ~24                          | Replace with fixtures, env setup, or mock where possible; reduce skipif for env                                                                                            |


### 7.3 Per-repo tasks

1. **instruments-service** — Use QUALITY_GATE_BYPASS_AUDIT.md; fix invalid exceptions; reduce whitelist
2. **All Python repos** — Create `docs/QUALITY_GATE_BYPASS_AUDIT.md` (or equivalent); audit; fix; no shortcuts

### 7.4 Decision checklist (from audit)

- **Import whitelist** — Reduce by fixing circular imports (TYPE_CHECKING, restructure)
- **type: ignore[reportAny]** — Replace with proper types; keep only third-party
- **dict[str, Any] exclusion** — Tighten; require explicit type: ignore per use
- **Ruff E722** — Disallow bare except in scripts
- **Ruff E402** — Move imports to top in main.py / conftest
- **pyright: ignore** — Fix underlying type issues
- **Test skips** — Replace with fixtures or env setup where possible

### Per-repo task matrix (all repos)

| Repo | .env commit | pip-audit + uv.lock | .env.example | quality-gates | credentials | project ID | bypass audit |
|------|-------------|---------------------|--------------|---------------|-------------|------------|
| instruments-service | ✓ | ✓ | ✓ | ✓ | Remove ! | test-project | Full audit (template) |
| market-tick-data-handler | eval | ✓ | ✓ | ✓ | Remove ! | - | ✓ |
| market-data-processing-service | skip (tracked) | ✓ | ✓ | ✓ | Remove ! | - | ✓ |
| strategy-service | eval | ✓ | ✓ | ✓ | ok | - | ✓ |
| execution-services | eval | ✓ | ✓ | ✓ | ok | - | ✓ |
| ml-training-service | eval | ✓ | ✓ | ✓ | ok | - | ✓ |
| ml-inference-service | eval | ✓ | ✓ | ✓ | Remove ! | - | ✓ |
| features-calendar-service | eval | ✓ | ✓ | ✓ | Remove ! | - | ✓ |
| features-volatility-service | eval | ✓ | ✓ | ✓ | Remove ! | - | ✓ |
| features-delta-one-service | eval | ✓ | ✓ | ✓ | ok | - | ✓ |
| features-onchain-service | eval | ✓ | ✓ | ✓ | Remove ! | - | ✓ |
| position-balance-monitor-service | ✓ | ✓ | ✓ | ✓ | ok | - | ✓ |
| risk-and-exposure-service | ✓ | ✓ | ✓ | ✓ | ok | - | ✓ |
| pnl-attribution-service | ✓ | ✓ | ✓ | ✓ | ok | - | ✓ |
| alerting-system | ✓ | ✓ | ✓ | ✓ | ok | - | ✓ |
| unified-cloud-services | ✓ | ✓ | ✓ | ✓ | ok | - | ✓ |
| unified-config-interface | ✓ | ✓ | ✓ | ✓ | ok | - | ✓ |
| unified-events-interface | ✓ | ✓ | ✓ | ✓ | ok | - | ✓ |
| unified-market-interface | ✓ | ✓ | ✓ | ✓ | ok | - | ✓ |
| unified-trade-execution-interface | ✓ | ✓ | ✓ | ✓ | ok | - | ✓ |
| unified-domain-services | ✓ | ✓ | ✓ | ✓ | ok | - | ✓ |
| execution-algo-library | ✓ | ✓ | ✓ | ✓ | ok | - | ✓ |
| unified-trading-deployment-v3 | eval | ✓ | ✓ | ✓ | Remove ! | - | ✓ |
| unified-trading-deployment-v3 | skip (tracked) | ✓ | ✓ | ✓ | Remove ! | - | ✓ |
| batch-audit-ui, logs-dashboard-ui, etc. | ✓ | N/A (Node) | ✓ | ✓ | ok | - | N/A |

---

## Execution Order

1. **Phase 0** — Update Cursor rules and Codex docs (document 11 factors first)
2. **Phase 1** — Update quality-gates-template.sh and quality-gates.md
3. **Phase 2** — Fix instruments-service (reference implementation)
4. **Phase 3** — Propagate in batches (4 parallel agents × 6–7 repos each)
5. **Phase 4** — Add pip-audit (template + propagate)
6. **Phase 5** — Add security validators (template + propagate)
7. **Phase 6** — .env + pip-audit for ALL repos: commit git rm .env, uv lock, .env.example, quality gates
8. **Phase 7** — Quality gate bypass hardening: audit exceptions, fix invalid (no shortcuts), propagate to all repos

---

## Verification Checklist

- Phase 0: Cursor rule `quality-gates-audit-factors.mdc` exists; Codex quality-gates.md and README updated
- Template has all new checks
- instruments-service passes all quality gates
- No `!central-element-*.json` in any .gitignore
- No `central-element-323112` in tests (use `test-project`)
- pip-audit runs (or gracefully skips if not installed)
- Security validators run in quality gates
- All repos: .env stop-tracking committed where applicable
- All repos: pip-audit in dev deps, uv.lock updated
- All repos: .env.example exists; .env untracked for local dev
- All 25+ Python repos updated and passing
- Phase 7: Bypass audit done per repo; invalid exceptions fixed; import whitelist reduced; Ruff E722/E402 addressed

---

## References

- `.cursor/rules/quality-gates-audit-factors.mdc` (to create in Phase 0)
- `.cursor/rules/strict-type-checking.mdc`
- `.cursor/rules/no-empty-fallbacks.mdc`
- `unified-trading-codex/06-coding-standards/quality-gates.md`
- `unified-trading-codex/06-coding-standards/file-splitting-guide.md`
- `unified-trading-codex/scripts/run-all-validators.sh`
- `instruments-service/docs/QUALITY_GATE_BYPASS_AUDIT.md` — template for bypass hardening
