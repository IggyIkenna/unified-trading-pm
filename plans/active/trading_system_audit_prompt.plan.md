---
name: trading-system-audit-prompt
overview:
  Canonical audit checklist for the unified trading system workspace against institutional-grade standards. Covers
  workspace governance, code quality, security, architecture, schema governance, observability, deployment, technical
  debt, and cross-repo alignment.
todos:
  - id: audit-workspace-governance
    content:
      "Audit Section 1 — Workspace Governance: workspace-manifest.json complete + DAG valid; all 57 repos registered;
      arch_tier correct; ci_status fields present. Score each criterion PASS/WARN/FAIL/N/A with file:line evidence."
    status: completed
  - id: audit-code-quality
    content:
      "Audit Section 2 — Code Quality: quality-gates.sh present + passing per repo; MIN_COVERAGE=70; file <900L,
      function <100L, method <50L, class <500L; ruff + basedpyright strict + reportAny:error; zero os.getenv in
      production source; zero Any in public API. Score each repo."
    status: pending
  - id: audit-security
    content:
      "Audit Section 3 — Security (items 10.1–10.19): no hardcoded API keys; all secrets via get_secret_client(); no
      verify=False in HTTP clients; all API services authenticated; no mock auth in prod; AUTH_FAILURE + SECRET_ACCESSED
      + CONFIG_CHANGED events logged."
    status: pending
  - id: audit-architecture
    content:
      "Audit Section 4 — Architecture: tier boundaries respected (no service→service Python imports); no UI embedded in
      service repo; batch-live symmetry (same engine for both modes); cloud-agnostic I/O (get_storage_client,
      get_secret_client, CloudEventSink); no GCS* protocol names; deployment-api HTTP boundary (no direct
      deployment_service imports)."
    status: pending
  - id: audit-schema-governance
    content:
      "Audit Section 5 — Schema Governance: AC contains external venue schemas only; UIC contains internal schemas; no
      AC/UIC duplication; Layer 0 contract alignment tests pass (test_contract_alignment.py, test_ac_uic_alignment.py);
      per-service test_schema_robustness.py passes."
    status: pending
  - id: audit-observability
    content:
      "Audit Section 6 — Observability: /health + /readiness endpoints on all API services; correlation_id propagated
      end-to-end; Prometheus metrics exported; Grafana dashboards present (trading-overview.json, system-health.json);
      pre-crash checkpoint at 85% memory; compliance reporting wired (MiFID/FCA); 12.16-12.20: timestamp validation,
      CloudEventSink naming, test_event_logging.py, memory watchdog, correlation_id propagation."
    status: pending
  - id: audit-deployment
    content:
      "Audit Section 7 — Deployment: deployment checklist phases 1–7 complete per service; runtime-topology.yaml
      accurate; Layer 2 infra verify passes (/infra/health); Layer 3a smoke (<5 min) passes; Layer 3b full E2E (15–30
      min) passes; v1.0.0 tagged on main."
    status: pending
  - id: audit-technical-debt
    content:
      "Audit Section 8 — Technical Debt: QUALITY_GATE_BYPASS_AUDIT.md present + up to date in all repos; zero
      undocumented suppressions; type: ignore count <10 total documented exceptions; no old import names as aliases; no
      try/except ImportError fallbacks."
    status: pending
  - id: audit-cross-repo-alignment
    content:
      "Audit Section 9 — Cross-Repo Alignment: all plans in INDEX.md have corresponding implementation; codex docs
      reflect current decisions; cursor rules consistent with codex; workspace-manifest.json matches
      runtime-topology.yaml; no orphan repos (4 API services previously missing from manifest — verify fixed)."
    status: pending
  - id: audit-output
    content:
      "Produce final audit output: per-criterion PASS/WARN/FAIL/N/A table; overall grade (PASS=0 FAILs, CONDITIONAL=≥1
      WARNs + 0 FAILs, FAIL=≥1 FAILs); top 10 blocking findings with file:line references; technical debt trajectory vs
      previous audit."
    status: pending
  - id: audit-config-injection
    content:
      "Audit Section on dynamic config injection compliance — GCP_PROJECT_ID banned, DomainConfigReloader used for
      domain entity hot-reload, get_config_store() factory only, no hardcoded subscription lists, CONFIG_CHANGED events
      logged."
    status: pending
isProject: false
---

# Unified Trading System — Canonical Audit Prompt

**Purpose:** Single source of truth audit checklist for evaluating the unified trading system workspace against
institutional-grade standards. Covers workspace governance, code quality, security, architecture, schema governance,
observability, deployment, technical debt, and cross-repo alignment.

**Scope:** 60+ repos (services, libraries, UIs, APIs, infrastructure). Usable by human auditors and AI agents.

**SSOT:** This file is the canonical audit prompt. Registered in `unified-trading-codex/00-SSOT-INDEX.md`.

**Format:** Score each criterion `PASS / WARN / FAIL / N/A`. Provide per-item evidence (file path + line). Output as
structured table + findings list.

---

## AUDITOR INSTRUCTIONS

You are auditing the unified trading system workspace. For each section below, evaluate every listed criterion. Return
results in this format:

```
CATEGORY | CRITERION | STATUS | EVIDENCE
```

Where STATUS = `PASS` | `WARN` | `FAIL` | `N/A`.

At the end, output:

- Overall grade: PASS (0 FAILs) / CONDITIONAL (≥1 WARNs, 0 FAILs) / FAIL (≥1 FAILs)
- Top 10 blocking findings with file:line references
- Technical debt trajectory vs previous audit (if available)

**Key SSOT references for auditors:**

- Repo registry & DAG: `unified-trading-pm/workspace-manifest.json`
- **Deployment configs (canonical):** `deployment-service/configs/` — checklist._.yaml, venues.yaml,
  RUNTIME_TOPOLOGY_DECISIONS.md, data-catalogue._.yaml, per-service PROTOCOL\_\* env files.
- **Runtime topology (canonical SSOT):** `unified-trading-pm/configs/runtime-topology.yaml` — owned by PM;
  `deployment-service/configs/runtime-topology.yaml` is a partial local view with `ssot_ref` pointing to PM.
- Tier architecture: `unified-trading-codex/04-architecture/TIER-ARCHITECTURE.md`
- SSOT master index: `unified-trading-codex/00-SSOT-INDEX.md`
- Cursor rules: `unified-trading-pm/cursor-rules/` (synced to `.cursor/rules/`)
- Quality gate templates: `unified-trading-codex/06-coding-standards/quality-gates-service-template.sh`
- TS quality gate rollout: `unified-trading-pm/scripts/propagation/rollout-quality-gates-typescript.py`
- Canonical dependency versions: `unified-trading-pm/workspace-constraints.toml`

**Analysis exclusions:** `.venv`_, `venv/`, `node_modules/`, `build/`, `dist/`, `_.egg-info/`, `archive/`

---

# PART A — WORKSPACE-LEVEL CHECKS

---

## SECTION 1 — WORKSPACE MANIFEST & REPO REGISTRY

Validates that `workspace-manifest.json` is complete, consistent, and authoritative as the code DAG SSOT.

| #    | Criterion                                                                                                                          | Blocking |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 1.1  | All repo directories under workspace root are registered in `workspace-manifest.json` `repositories`                               | YES      |
| 1.2  | No orphan directories (directories in workspace root not listed in manifest, excluding `.venv`, `.cursor`, `archive`)              | YES      |
| 1.3  | Every repo has `type` field set correctly (library / service / api-service / ui / infrastructure / documentation)                  | YES      |
| 1.4  | Every repo has `arch_tier` matching codex `TIER-ARCHITECTURE.md` (0/1/2/3/service/api/ui)                                          | YES      |
| 1.5  | Every repo has `doc_standard` matching its type (service-canonical / library-canonical / ui-canonical / infrastructure-canonical)  | WARN     |
| 1.6  | `topologicalOrder` covers all active repos and respects tier constraints (T0 at lower levels than T1, etc.)                        | YES      |
| 1.7  | No `>=1.0.0` versions in any `pyproject.toml` — versions_policy requires all pre-stable (`0.x.x`) until full CI pipeline validates | YES      |
| 1.8  | `pyproject.toml` versions match manifest `versions` section                                                                        | YES      |
| 1.9  | `dependencies` for each repo list only repos at lower or equal tier                                                                | YES      |
| 1.10 | `status` field present and accurate for all repos (active / scaffolded / planned / archived)                                       | WARN     |
| 1.11 | `ci_status` and `quality_gate_status` fields populated and reflect current state                                                   | WARN     |
| 1.12 | `coverage_pct` field populated for repos with tests (not all zeros)                                                                | WARN     |
| 1.13 | `completion_path` fields accurately tag CeFi / DeFi / Sports / TradFi scope                                                        | WARN     |
| 1.14 | Archived repos removed from `repositories` and noted in `notes` or `removedEntries`                                                | WARN     |
| 1.15 | Manifest `lastUpdated` within 7 days of audit date                                                                                 | WARN     |

---

## SECTION 2 — TIER ARCHITECTURE & DAG ENFORCEMENT

Validates the 5-tier dependency model from `TIER-ARCHITECTURE.md` and cursor rule `dag-enforcement.mdc` (priority 90).

| #    | Criterion                                                                                                                                                                                                                                               | Blocking |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 2.1  | T0 repos (unified-api-contracts, unified-internal-contracts, unified-config-interface, unified-events-interface, unified-cloud-interface, execution-algo-library, matching-engine-library) have zero internal workspace dependencies                    | YES      |
| 2.2  | T1 repos (unified-trading-services, unified-reference-data-interface) depend only on T0 repos                                                                                                                                                           | YES      |
| 2.3  | T2 repos (unified-market-interface, unified-trade-execution-interface, unified-ml-interface, unified-feature-calculator-library, unified-position-interface, unified-defi-execution-interface, unified-sports-execution-interface) depend only on T0+T1 | YES      |
| 2.4  | T3 (unified-domain-client) depends only on T0+T1 — never on T2 or service-tier packages                                                                                                                                                                 | YES      |
| 2.5  | Service repos NEVER import another service as a Python package dependency in `pyproject.toml`                                                                                                                                                           | YES      |
| 2.6  | No circular dependencies in the `pyproject.toml` DAG (graph is acyclic)                                                                                                                                                                                 | YES      |
| 2.7  | API repos (execution-results-api, market-data-api, client-reporting-api) import only T0+T1 — never T2/T3/service packages                                                                                                                               | YES      |
| 2.8  | UI repos are TypeScript-only — never declare Python package dependencies                                                                                                                                                                                | YES      |
| 2.9  | Service-to-service interaction is only via messaging / APIs / storage per `runtime-topology.yaml` — no direct Python imports                                                                                                                            | YES      |
| 2.10 | `pyproject.toml` path sources use `../repo-name` pattern (not `deps/` or absolute paths)                                                                                                                                                                | YES      |
| 2.11 | `WORKSPACE_MANIFEST_DAG.svg` is regenerated and matches current manifest content                                                                                                                                                                        | WARN     |
| 2.12 | No upward-tier violations (e.g., T2 importing T3, library importing service)                                                                                                                                                                            | YES      |
| 2.13 | `deployment-api` MUST NOT import `deployment_service` as a Python package — all interaction via HTTP REST API. Search: `rg 'from deployment_service\|import deployment_service' deployment-api/ --type py` = 0 hits.                                    | YES      |

---

## SECTION 3 — SSOT ENFORCEMENT & CENTRALIZATION

Checks that `00-SSOT-INDEX.md` is accurate, no duplicate implementations exist, and the SSOT placement principle is
respected.

| #    | Criterion                                                                                                                                                                                                                                 | Blocking |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 3.1  | Every entry in `00-SSOT-INDEX.md` points to a file that exists and contains current content                                                                                                                                               | YES      |
| 3.2  | No duplicate schema definitions across repos (e.g., `ModelVariantConfig` in only one location)                                                                                                                                            | YES      |
| 3.3  | No duplicate cloud service abstractions (single config class name: `UnifiedCloudConfig` from `unified-config-interface`)                                                                                                                  | YES      |
| 3.4  | Config class naming standardized — no `UnifiedCloudServicesConfig` from `unified_trading_services` in any repo                                                                                                                            | YES      |
| 3.5  | Cursor rules source of truth is `unified-trading-pm/cursor-rules/`, synced to `.cursor/rules/` via symlink (not copies)                                                                                                                   | YES      |
| 3.6  | Quality gate scripts (`scripts/quality-gates.sh`) across all repos aligned with canonical template from codex — no template drift                                                                                                         | YES      |
| 3.7  | Runtime topology SSOT: `runtime-topology.yaml` is sole authority for messaging/storage/API interaction policy — not duplicated in service configs                                                                                         | YES      |
| 3.8  | Venue catalog SSOT: `deployment-service/configs/venues.yaml` (or `unified-trading-deployment-v3/configs/venues.yaml`) — not duplicated in service-level venue lists                                                                       | YES      |
| 3.9  | No parallel code paths (old + new schema, old + new import) — `delete-deprecated.mdc` (priority 95) enforced                                                                                                                              | YES      |
| 3.10 | No `_old.py`, `_legacy.py`, `_deprecated.py` files in any active repo                                                                                                                                                                     | YES      |
| 3.11 | Event field definitions live in `unified-internal-contracts` only — not redefined in services                                                                                                                                             | YES      |
| 3.12 | No copy-paste test templates diverging across repos (e.g., `test_event_logging.py` variants)                                                                                                                                              | WARN     |
| 3.13 | Documentation references machine-readable SSOTs, never duplicates them (SSOT placement principle)                                                                                                                                         | WARN     |
| 3.14 | No deployment-engine / deployment-v3 / deployment-service code duplication — single canonical location for deployment logic (`deployment-service/configs/`)                                                                               | YES      |
| 3.15 | Tests for UIC internal schemas live only in `unified-internal-contracts/tests/` — not in `unified-api-contracts/tests/`. Search: `rg 'UIC\|unified_internal_contracts\|internal_schema' unified-api-contracts/tests/ --type py` = 0 hits. | YES      |
| 3.16 | No backward-compat shim aliases anywhere: `rg '# deprecated:\|# backward.compat\|# kept for backward\|# alias for' --type py --glob '!.venv*'` = 0 hits in production source.                                                             | YES      |

---

## SECTION 4 — EXTERNAL DEPENDENCY GOVERNANCE

Checks `canonical-dependency-manifest.json`, `workspace-constraints.toml`, and version consistency.

| #    | Criterion                                                                                                               | Blocking |
| ---- | ----------------------------------------------------------------------------------------------------------------------- | -------- |
| 4.1  | `canonical-dependency-manifest.json` lists all external PyPI packages used across workspace                             | YES      |
| 4.2  | `workspace-constraints.toml` defines single canonical range per external package                                        | YES      |
| 4.3  | No version conflicts: each external package has one version range across all repos                                      | YES      |
| 4.4  | All dependency versions bounded (no unbounded `>=X` without upper bound on critical deps) — pattern: `>=X.Y.Z,<X+1.0.0` | WARN     |
| 4.5  | `uv` used as package manager everywhere — no bare `pip install` in any script or Dockerfile                             | YES      |
| 4.6  | `uv.lock` committed and up to date in all Python repos                                                                  | YES      |
| 4.7  | `pyproject.toml` is canonical dependency source — no `requirements.txt` as parallel source                              | WARN     |
| 4.8  | Dev dependencies separated from production (`[project.optional-dependencies.dev]`)                                      | WARN     |
| 4.9  | Internal workspace dependencies use `>=0.x.0` editable path references                                                  | YES      |
| 4.10 | Build system standardized (consistent `requires-python` spec across repos)                                              | WARN     |
| 4.11 | `propagate-canonical-versions.py` has been run and all repos aligned with workspace constraints                         | WARN     |
| 4.12 | No completely unpinned dependencies (bare package names without any version spec)                                       | YES      |

---

## SECTION 5 — WORKSPACE DOCUMENTATION STANDARDS

Checks `doc_standards` from manifest, canonical docs compliance, and documentation quality.

| #    | Criterion                                                                                                                                                                                                                                                                                                                                                                             | Blocking |
| ---- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 5.1  | Every service repo has all `service-canonical` required docs: README.md, docs/ARCHITECTURE.md, docs/CONFIGURATION.md, docs/GCS_PATHS.md, docs/DEPLOYMENT_GUIDE.md, docs/TESTING.md, docs/SCHEMA_VALIDATION.md, QUALITY_GATE_BYPASS_AUDIT.md                                                                                                                                           | YES      |
| 5.2  | Every library repo has all `library-canonical` required docs: README.md, docs/ARCHITECTURE.md, docs/CONFIGURATION.md, docs/TESTING.md, QUALITY_GATE_BYPASS_AUDIT.md                                                                                                                                                                                                                   | YES      |
| 5.3  | Every UI repo has all `ui-canonical` required docs: README.md, docs/ARCHITECTURE.md, docs/DEPLOYMENT_GUIDE.md, docs/TESTING.md                                                                                                                                                                                                                                                        | WARN     |
| 5.4  | No stub documentation files (3 lines or fewer, just "TODO", or empty) in required doc locations                                                                                                                                                                                                                                                                                       | WARN     |
| 5.5  | No summary/overview docs that duplicate information already in SSOT (`no-summary-docs.mdc`, priority 100)                                                                                                                                                                                                                                                                             | WARN     |
| 5.6  | Docs use `{project_id}` placeholders — no hardcoded project IDs or bucket names                                                                                                                                                                                                                                                                                                       | YES      |
| 5.7  | `AGENTS.md` exists for repos with non-obvious setup quirks (recommended, not required)                                                                                                                                                                                                                                                                                                | WARN     |
| 5.8  | Codex section references in manifest `codex_sections` match actual codex directory structure                                                                                                                                                                                                                                                                                          | WARN     |
| 5.9  | No embedded UI artifacts in service repos — no `package.json`, `tsconfig.json`, `frontend/`, `dist/`, `visualizer-ui/`, `visualizer-api/`, `static/`, `templates/` dirs in Python service repos. Search: `find <repo> -maxdepth 3 \( -name "package.json" -o -name "tsconfig.json" -o -type d -name "visualizer-ui" -o -type d -name "visualizer-api" -o -type d -name "frontend" \)` | YES      |
| 5.10 | `specs/` directories, if present, do not have diverged copies of files also in `docs/`                                                                                                                                                                                                                                                                                                | WARN     |

---

## 5a. Cloud Isolation Audit (Hard Gates — must pass before Phase 2+)

STEP 5.10 — No direct cloud SDK imports outside UCI providers: PASS gate: rg 'from google.cloud|import boto3|import
botocore' --type py --glob '!.venv\*' --glob '!unified-cloud-interface/\*\*' = 0 matches

STEP 5.11 — No protocol-leaking symbols in service code: PASS gate: rg
'CloudTarget|StandardizedDomainCloudService|upload_to_gcs_batch|gcs_bucket=|bigquery_dataset=' --type py --glob
'!.venv\*' --glob '!tests/\*\*' = 0 matches in service repos Per-repo enforcement: `scripts/quality-gates.sh` must
include STEP 5.11 check as hard-fail (not warn). Verify with: grep -q "STEP 5.11\|CloudTarget\|upload_to_gcs_batch"
scripts/quality-gates.sh

STEP 5.12 — No hardcoded cloud protocol names in service source: PASS gate: rg
'gcs_bucket\s*=|bigquery_dataset\s*=|upload_to_gcs|CloudTarget\b' --type py --glob '!.venv\*' --glob '!tests/**' --glob
'!scripts/**' = 0 matches

STEP 5.13 — Services use ServiceMode + PROTOCOL*\* env vars for deployment injection: PASS gate: Services that have
live/batch modes use `SERVICE_MODE` env var (not hardcoded string); cloud routing via `PROTOCOL_DATA_SINK*\*` env vars
injected at deploy time, not in source. Verify: rg 'SERVICE_MODE|PROTOCOL_DATA_SINK' deployment-service/configs/ --
presence confirms injection pattern

UTL gate: [project.dependencies] in unified-trading-library/pyproject.toml has no google-cloud-\* or boto3 (only in
[project.optional-dependencies.gcp/aws])

All 5 checks must be PASS before any Phase 2+ work begins on a repo.

---

## SECTION 6 — CURSOR RULES & AGENT GOVERNANCE

Checks that cursor rules are complete, consistent, enforced, and synced.

### 6.1 Cursor Rule Category → Audit Criteria Mapping

- **architecture** — Tier enforcement (SECTION 2), batch-live symmetry (14.1), service structure (14.2), cloud-agnostic
  (14.3), adapters (14.2)
- **ci-cd** — Cloud Build test-in-image (22.1), quickmerge pipeline (22.5, SECTION 8.19), branch protection (22.4)
- **config** — UnifiedCloudConfig (7.7), GCP_PROJECT_ID (single-project-id), ConfigStore usage (SECTION 13)
- **core** — All blocking rules (6.2), basedpyright-safety (6.5, 8.20), runtime-verification (6.2), delete-deprecated,
  never-revert-local-changes
- **dependencies** — Breaking-change protocol, dependency alignment (SECTION 4), path-dependency-ci (22.10)
- **quality-gates** — Strict quality gates (8.x), safe-linting-execution (8.20), exclude-build-artifacts (8.20), E501
  (8.3)
- **testing** — GCP auth in tests (no skip for missing creds), test quality standards (SECTION 17)
- **ui** — UI-service separation (no Python in UI repos), TypeScript quality gates only (17.2)

### 6.2 BLOCKING Rules (Mandatory PASS)

The following rules are BLOCKING — any violation fails the audit:

- **strict-quality-gates** — E501 enforced, no E722 global ignore, no empty fallbacks, no hardcoded project IDs
- **no-type-any-use-specific** — `reportAny: "error"`, no `dict[str, Any]`, only audited bypasses in
  QUALITY_GATE_BYPASS_AUDIT.md
- **runtime-verification-required** — Never claim "done" without running code, waiting 8–10s, checking terminal output
- **basedpyright-safety** — Never `basedpyright .`; always `timeout 120 basedpyright <source_dir>/` or `run_timeout 120`
- **dag-enforcement** — No repo imports from higher or equal tier
- **delete-deprecated** — No parallel code paths; single source of truth
- **never-revert-local-changes** — No `git reset --hard` in scripts or agent prompts
- **agents-follow-cursor-rules** — Sub-agents receive blocking rules explicitly
- **no-summary-docs** — No `*_SUMMARY.md`, `*_STATUS.md`, or recap docs unless explicitly requested
- **always-use-quickmerge** — All pushes via `bash scripts/quickmerge.sh`; never standalone quality gates or bare
  `git push`

---

| #    | Criterion                                                                                                                                                                                                                                                                                                             | Blocking |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 6.1  | All blocking cursor rules (priority ≥ 90) are present and active: `basedpyright-safety` (100), `no-summary-docs` (100), `no-type-any-use-specific` (90), `dag-enforcement` (90), `runtime-verification-required` (95), `delete-deprecated` (95), `never-revert-local-changes` (95), `agents-follow-cursor-rules` (95) | YES      |
| 6.2  | `.cursor/rules/` is a symlink to `unified-trading-pm/cursor-rules/` — not a copy                                                                                                                                                                                                                                      | YES      |
| 6.3  | No cursor rules contradict codex standards (rules are enforcement reminders, codex is specification)                                                                                                                                                                                                                  | YES      |
| 6.4  | Each cursor rule has `CODEX:` reference linking to the codex document it derives from                                                                                                                                                                                                                                 | WARN     |
| 6.5  | `basedpyright` never run as bare `basedpyright .` — always with explicit source dir + `timeout 120`                                                                                                                                                                                                                   | YES      |
| 6.6  | `never-revert-local-changes.mdc` enforced: no `git reset --hard` in any script or agent prompt                                                                                                                                                                                                                        | YES      |
| 6.7  | `always-use-quickmerge.mdc` (priority 85) enforced: all pushes via `bash scripts/quickmerge.sh`, never standalone quality gates or bare `git push`                                                                                                                                                                    | YES      |
| 6.8  | Sub-agents receive blocking rules explicitly per `agents-follow-cursor-rules.mdc`                                                                                                                                                                                                                                     | YES      |
| 6.9  | Rule priority ordering is internally consistent (100 > 95 > 90 > 85 > ...)                                                                                                                                                                                                                                            | WARN     |
| 6.10 | No deprecated or conflicting rules remain in `.cursor/rules/`                                                                                                                                                                                                                                                         | WARN     |
| 6.11 | `.cursorrules` file at workspace root references cursor rules directory and codex correctly                                                                                                                                                                                                                           | WARN     |
| 6.12 | `alwaysApply: true` rules do not require glob patterns (they apply everywhere by definition)                                                                                                                                                                                                                          | WARN     |

---

## SECTION 7 — CODEX vs CODE ALIGNMENT

Checks for documentation drift between codex standards and actual implementations.

| #    | Criterion                                                                                                                          | Blocking |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 7.1  | All bucket names match parameterized pattern from codex — not hardcoded                                                            | YES      |
| 7.2  | Venue names use canonical form from `venues.yaml` (e.g., `BINANCE-SPOT` / `BINANCE-FUTURES`, not `BINANCE`)                        | WARN     |
| 7.3  | Lifecycle event names match canonical list in `03-observability/lifecycle-events.md` — no custom event names like `INGESTING_DATA` | YES      |
| 7.4  | Import routing matches `TIER-ARCHITECTURE.md` import routing map (symbols imported from correct source package)                    | YES      |
| 7.5  | Package names in code match current names (not old aliases: `unified-trading-services` not `unified-cloud-services`)               | WARN     |
| 7.6  | Dockerfile base images use `unified-trading-services:latest` — no `unified-cloud-services:latest` references                       | WARN     |
| 7.7  | Config classes extend `UnifiedCloudConfig` or `BaseServiceConfig` per codex — no `UnifiedCloudServicesConfig`                      | YES      |
| 7.8  | Service structure follows codex pattern: engine / adapters / CLI separation                                                        | WARN     |
| 7.9  | Codex references to repo names are current (no `unified-trading-deployment-v2`, `market-tick-data-handler`, `corporate-actions`)   | WARN     |
| 7.10 | Architectural changes accompanied by codex doc update in same PR                                                                   | WARN     |

## AC/UIC Combined Audit

### AC/UIC Refactor Layout Status

**Plans:** [archive README § ac_package_layout_refactor](../archive/README.md)

| Phase                                    | Status                                                                                                      |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Phase 0 (SSOT + cursor rules)            | Done                                                                                                        |
| Phases 1–8 (package layout)              | Done — venue_manifest, sports, fix, nautilus, regulatory, prime_broker under unified_api_contracts_external |
| Phase 9 (root, tests, QG, 2-min timeout) | **QG fails:** 63 lint errors (E501 line length, F401 unused imports)                                        |
| Phase 10 (workspace consumers)           | Blocked by Phase 9                                                                                          |

**QG lint blockers:** Run `ruff check --fix` and manually fix E501 (line length) in AC. Ensure
`pytest -m "not integration"` completes in <2 min. Workspace consumers: update imports after AC QG passes.

**Does not block first deployment:** AC/UIC refactor improves structure; existing imports work via top-level re-exports.

---

### Intended Split (AC vs UIC)

- **unified-api-contracts (AC):** Everything **external** to our private repos (needs API key / external connection) + a
  **normalised** layer (one-hop from raw external responses). No purely internal service-to-service contracts.
- **unified-internal-contracts (UIC):** Purely **internal** contracts between private components (no API key, not
  normalised-from-external, not "getting something external").
- **Dependency rule:** AC must **not** depend on UIC (AC is Tier 0). Canonical namings that AC needs for
  external/normalised (e.g. venue enums, error classification at API boundary) stay in AC.
- **VCR and live schema validation:** Done in the **interfaces** that depend on AC (interfaces hold API keys). AC holds
  only schemas and static examples. Interfaces that perform VCR and contract-vs-reality validation:
  **unified-trade-execution-interface**, **unified-sports-execution-interface**, **unified-reference-data-interface**,
  **unified-position-interface**, **unified-market-interface**, **unified-cloud-interface**.

---

### Part A: unified-api-contracts (AC) — existing audit

(See full plan in .cursor/plans/ for sections 1–8: layout, docs, .cursor/ boundary, deprecated files, file size, import
standards, other alignment, summary table and suggested order.)

---

### Part B: unified-internal-contracts (UIC) — audit

**Role:** SSOT for internal message schemas, topic names, and request/response/error contracts (no external APIs, no API
keys).

**Current content (correct for "internal only"):** events, market_data, positions, pubsub, risk, features, ml, schemas,
reference, messaging, defi, execution (ManualInstruction).

**Dependencies:** Only pydantic; no dependency on AC. Tier 0. OK.

**Alignment tests:** test_uic_ac_alignment.py imports from unified_api_contracts.internal.; obsolete once AC.internal is
removed.

**schema_registry.json:** Remove entries for unified_api_contracts.internal. when AC.internal is deleted.

**Verdict:** UIC is already internal-only and well-scoped.

**Before deleting AC internal/:** Verify every AC internal symbol (config, domain, execution, health, signals, sor) has
an equivalent in UIC; add any gaps to UIC first, then delete AC internal/.

---

### Part C: Combined split and remediation

**What belongs where:** External + FIX + nautilus + normalised + canonical namings → AC. Events, pubsub, risk, features,
ml, config, health, execution, signals, sor → UIC only (delete from AC). internal_execution_services, prime_broker,
regulatory, shared → classify (internal → UIC/delete; external → AC).

**Dependency:** AC must NOT depend on UIC. UIC may optionally depend on AC to re-export normalised types.

**Normalised in AC:** Make unified_normalised_contracts self-contained (Option A: own definitions in AC; Option B: UIC
depends on AC and re-exports).

**VCR / live capture:** Move collected_responses/ and generated_schemas/ responsibility to the six interfaces
(integration tests). Remove or relocate from AC: collect_responses.py, capture_api_responses.py, validate_schemas.py
(live/--generate-schemas), verify_contracts_vs_reality.py. AC keeps only schemas and static examples.

**Docs and SSOT updates:** (1) Codex 00-SSOT-INDEX.md — AC = contracts only; VCR/live validation in the six interfaces;
add internal contracts row. (2) Codex 05-infrastructure/contracts-integration.md — same. (3) Codex 02-data (VCR/schema
ownership) — interfaces record/validate; AC holds schemas and examples. (4) Cursor rules: vcr-ownership.mdc (interfaces
do VCR; list six), unified-api-contracts-usage.mdc (live verification in interfaces), contracts-integration.mdc (one
line on six interfaces). (5) AC README/docs — point live validation to interfaces.

**Orphaned-schemas audit (two types):** (1) **Not normalised** — external/venue schemas that have no corresponding
normalised form in AC. (2) **Not used by any interface** — schemas that none of the six interfaces import or use. Single
report, two sections; list by module and symbol; output in unified-trading-pm/docs/audit/ or AC docs.

**Combined remediation order:** (1) AC docs + script move + .bak + gitignore; (2) normalised self-contained in AC; (3)
verify UIC has all AC internal symbols, then remove internal (and classify other dirs) from AC, update AC tests; (4)
UIC: remove alignment tests and schema_registry AC.internal entries; (5) confirm no production imports of AC.internal;
(6) move VCR/live scripts to interfaces, remove collected_responses/generated_schemas from AC; (7) update docs and SSOT
as above; (8) **produce orphaned-schemas audit report** — Type 1: not normalised; Type 2: not used by any of the six
interfaces; (9) optional AC layout + remove sys.modules alias.

---

---

# PART B — PER-REPO CODE QUALITY CHECKS

---

## SECTION 8 — LINTING, FORMATTING & QUALITY GATES

| #    | Criterion                                                                                                                                                                                | Blocking |
| ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------------------- | --- |
| 8.1  | Ruff linter runs with zero errors (`ruff check --no-fix`)                                                                                                                                | YES      |
| 8.2  | Ruff formatter is applied (`ruff format --check`)                                                                                                                                        | YES      |
| 8.3  | Line length ≤ 100 chars enforced (E501 in ruff config, not globally ignored)                                                                                                             | YES      |
| 8.4  | No bare `except:` or `except Exception: pass` (E722 not in global ruff ignore)                                                                                                           | YES      |
| 8.5  | No `# noqa` or `# type: ignore` used to hide architectural violations — each must be documented in QUALITY_GATE_BYPASS_AUDIT.md                                                          | YES      |
| 8.6  | basedpyright passes with `typeCheckingMode: "strict"` and `reportAny: "error"` — run via `timeout 120 basedpyright <source_dir>/`                                                        | YES      |
| 8.7  | Import order correct — stdlib → third-party → local; no imports inside functions (except `TYPE_CHECKING` blocks)                                                                         | YES      |
| 8.8  | `scripts/quality-gates.sh` exists and matches canonical template from codex (`quality-gates-service-template.sh` or `quality-gates-library-template.sh`)                                 | YES      |
| 8.9  | No `                                                                                                                                                                                     |          | true` or similar bypasses in quality gate CI workflows (`quality-gates.yml`, `quality-gates-simple.yml`) | YES |
| 8.10 | McCabe complexity ≤ 10 enforced in ruff config                                                                                                                                           | WARN     |
| 8.11 | Ruff config uses standard rule selection (`["E", "F", "W", "I"]` minimum) — not `["I"]` only                                                                                             | YES      |
| 8.12 | `QUALITY_GATE_BYPASS_AUDIT.md` exists at repo root, is either empty (all gates pass) or contains only genuine unsolvable exceptions with justification — no stale or unjustified entries | YES      |
| 8.13 | No wildcard imports (`from X import` ) in production code                                                                                                                                | YES      |
| 8.14 | `.pre-commit-config.yaml` exists in repo root with ruff (`v0.15.0`), prettier (`3.6.2`), and pre-commit-hooks (`v6.0.0`) — matching canonical instruments-service template               | YES      |
| 8.15 | Pre-commit hooks installed via `prek install` — `.git/hooks/pre-commit` exists and delegates to pre-commit                                                                               | YES      |
| 8.16 | Prettier configured to format TypeScript/JSON/Markdown/YAML (`types_or: [ts, tsx, javascript, jsx, json, markdown, yaml]`)                                                               | WARN     |
| 8.17 | Library repos include `bump-library-version` pre-commit hook; non-library repos (services, UIs, PM) omit it                                                                              | YES      |
| 8.18 | `pre-commit run --all-files` exits 0 on clean repo (no trailing whitespace, no missing newlines, ruff clean)                                                                             | YES      |

### 8.19 Quickmerge Pipeline: Stages & Flags

**Stages (in order):**

1. **Dependency validation** — workspace-manifest.json SSOT; path deps checked vs origin/main
2. **Pre-flight audit** — path dependency uncommitted changes check; PM dependency alignment (PM repos only)
3. **Two-phase quality gates** — auto-fix phase, then verify phase (lint + type + codex + tests)
4. **Act simulation** — default on; skip with `--quick`
5. **PR creation** — create PR, enable auto-merge

**Flags:**

| Flag                | Effect                                                                  |
| ------------------- | ----------------------------------------------------------------------- |
| `--dep-branch NAME` | Branch isolation when dependencies differ from main; cascades into deps |
| `--unit-only`       | Fast feedback: lint + type + unit tests only; skip integration + act    |
| `--quick`           | Skip act simulation (Stage 4) only; all other checks run                |
| `--skip-tests`      | Pass to quality-gates.sh: lint + type + codex only                      |
| `--skip-typecheck`  | Pass to quality-gates.sh: skips basedpyright only                       |
| `--files "p1 p2"`   | Stage only these paths (multi-agent)                                    |

### 8.20 Type Checking & Linting Safety

| Criterion                   | Blocking                                                                                                                                                                                                                                   |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **basedpyright-safety**     | Never run `basedpyright .` or `basedpyright` without source dir. Always use `timeout 120 basedpyright <source_dir>/` or `run_timeout 120 basedpyright <source_dir>/`. For audits, run quality gates per repo, NOT standalone basedpyright. |
| **safe-linting-execution**  | Ruff/linters run with timeout and specific source dir. `timeout 30 ruff check <source_dir>/`; job-level timeout in CI. Never `ruff check .` or run linters without timeout.                                                                |
| **exclude-build-artifacts** | Never type-check `build/`, `dist/`, `__pycache__/`, `.venv/`, `node_modules`. Add to pyrightconfig.json exclude. Run basedpyright on source_dir only.                                                                                      |
| **UCS_DOMAIN_IMPORT**       | Services importing domain clients from UTS (e.g. `InstrumentsDomainClient`) FAIL — must import from `unified_domain_client`.                                                                                                               |
| **E501**                    | Line length ≤ 100 chars enforced in ruff config; E501 not in global ignore.                                                                                                                                                                |

---

## SECTION 9 — TYPE SAFETY

| #    | Criterion                                                                                                                         | Blocking |
| ---- | --------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 9.1  | No `Any` types except in documented bypass audit file                                                                             | YES      |
| 9.2  | All dict parameters typed as `dict[str, SpecificType]`, not `dict[str, Any]`                                                      | YES      |
| 9.3  | No `TypedDict` fields typed as `Any`                                                                                              | YES      |
| 9.4  | Protocol types used for duck typing instead of `Any`                                                                              | WARN     |
| 9.5  | TypeVar used for generic functions instead of `Any`                                                                               | WARN     |
| 9.6  | Built-in generics used: `list[X]`, `dict[K,V]`, `tuple[X,...]` — not `typing.List`, `typing.Dict`                                 | WARN     |
| 9.7  | `pyrightconfig.json` exists with `typeCheckingMode: "strict"` — not "basic" or "off"                                              | YES      |
| 9.8  | `pyrightconfig.json` `include` paths match actual source directories (not typos like `execution_services` vs `execution_service`) | YES      |
| 9.9  | No production files excluded from type checking in `pyrightconfig.json` exclude list                                              | YES      |
| 9.10 | `reportAny` set to `"error"` not `"warning"` in pyrightconfig                                                                     | YES      |
| 9.11 | No bare `dict` / `list` annotations without type parameters (use `dict[str, X]`, `list[X]`)                                       | WARN     |

---

## SECTION 10 — SECURITY & SECRETS

| #     | Criterion                                                                                                              | Blocking |
| ----- | ---------------------------------------------------------------------------------------------------------------------- | -------- |
| 10.1  | No API keys, passwords, or credentials hardcoded anywhere in source                                                    | YES      |
| 10.2  | All secrets retrieved via `get_secret_client()` from `unified-cloud-interface` — not `os.getenv()` with empty fallback | YES      |
| 10.3  | No credential JSON files in repository (`.gitignore` covers `*credentials*.json`)                                      | YES      |
| 10.4  | No hardcoded project IDs — parameterized via config class                                                              | YES      |
| 10.5  | `GCP_PROJECT_ID` not used as primary env var (use `GCP_PROJECT_ID`)                                                    | YES      |
| 10.6  | No `verify=False` in HTTP clients (no auth bypass flags in production code)                                            | YES      |
| 10.7  | No `.env` files tracked in git — only `.env.example` with placeholder values                                           | YES      |
| 10.8  | No `pickle.load`, `joblib.load`, `jsonpickle.decode` from untrusted sources — use safe serialization                   | YES      |
| 10.9  | No command injection: user inputs sanitized before `subprocess` / `gcloud` calls                                       | YES      |
| 10.10 | No SQL injection: no f-string interpolation in SQL queries                                                             | YES      |
| 10.11 | All API services authenticated — no unauthenticated POST/PUT/DELETE endpoints in production                            | YES      |
| 10.12 | No mock authentication in production code (e.g., `"client-{anything}-key"` accepted as valid)                          | YES      |
| 10.13 | FastAPI Swagger/OpenAPI docs disabled in production environments (only enabled in dev/staging)                         | WARN     |
| 10.14 | No verbose error tracebacks returned to HTTP clients in production — sanitized error responses only                    | WARN     |
| 10.15 | No hardcoded CORS origins — parameterized via config, not `allow_origins=["*"]` or hardcoded domains                   | WARN     |
| 10.16 | PII fields tagged in schema definitions (`pii: True` metadata or equivalent)                                           | WARN     |
| 10.17 | AUTH_FAILURE events logged with `auth_type`, `username`, `failure_reason` — no silent auth failure                     | YES      |
| 10.18 | SECRET_ACCESSED events logged with `secret_name`, `caller_identity`, `success`                                         | WARN     |
| 10.19 | CONFIG_CHANGED events logged with `config_file`, `changed_by`, `authorized`                                            | WARN     |

---

## SECTION 11 — ERROR HANDLING & RESILIENCE

| #     | Criterion                                                                                                 | Blocking |
| ----- | --------------------------------------------------------------------------------------------------------- | -------- |
| 11.1  | No empty `except Exception: pass` blocks in production code                                               | YES      |
| 11.2  | Every error type has an assigned strategy: retry / fail-fast / exit-job / exit-process / circuit-breaker  | YES      |
| 11.3  | Transient errors (rate limit, network blip) use bounded retry with exponential backoff                    | YES      |
| 11.4  | Fatal errors (config corrupt, unrecoverable) trigger clean shutdown with FAILED lifecycle event           | YES      |
| 11.5  | Circuit breakers used for upstream dependencies that fail repeatedly                                      | WARN     |
| 11.6  | All external API errors normalized to typed error schema — no raw exception propagation across boundaries | YES      |
| 11.7  | Validation failures at API boundaries route to dead-letter queue — never silently passed through          | YES      |
| 11.8  | `EnhancedError` (or equivalent typed error) used at all service boundaries — no bare `Exception`          | YES      |
| 11.9  | Dead-letter records include `correlation_id` and `trace_id` for cross-service incident reconstruction     | WARN     |
| 11.10 | No `try/except ImportError` fallback imports — fail loud on missing dependencies                          | YES      |
| 11.11 | Exception logging uses `logger.exception()` — not `logger.info(f"Error: {e}")` (preserves tracebacks)     | WARN     |
| 11.12 | No silent `return None` in except blocks without logging the error                                        | YES      |

---

## SECTION 12 — OBSERVABILITY & LOGGING

| #     | Criterion                                                                                                                                                                                                                                                                                                                                         | Blocking        |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- | --------------------------- | ---- |
| 12.1  | No `print()` statements in production code — all output through structured logger                                                                                                                                                                                                                                                                 | YES             |
| 12.2  | All 11 batch lifecycle events emitted in correct order: STARTED → VALIDATION_STARTED → VALIDATION_COMPLETED → DATA_INGESTION_STARTED → DATA_INGESTION_COMPLETED → PROCESSING_STARTED → PROCESSING_COMPLETED → PERSISTENCE_STARTED → PERSISTENCE_COMPLETED → STOPPED / FAILED                                                                      | YES             |
| 12.3  | All 12 live lifecycle events emitted (batch events plus DATA_BROADCAST)                                                                                                                                                                                                                                                                           | YES             |
| 12.4  | Service never exits without logging STOPPED or FAILED                                                                                                                                                                                                                                                                                             | YES             |
| 12.5  | No `setup_cloud_logging` — use structured event logging via `unified_events_interface`                                                                                                                                                                                                                                                            | YES             |
| 12.6  | `setup_events(service_name=...)` called in every service's CLI entrypoint                                                                                                                                                                                                                                                                         | YES             |
| 12.7  | `datetime.now(timezone.utc)` used — never `datetime.now()`, `datetime.utcnow()`, or `datetime.today()`                                                                                                                                                                                                                                            | YES             |
| 12.8  | All timestamps in stored schemas are timezone-aware UTC                                                                                                                                                                                                                                                                                           | YES             |
| 12.9  | No `logging.basicConfig()` in library code (clobbers root logger configuration)                                                                                                                                                                                                                                                                   | YES             |
| 12.10 | No f-string logging (`logger.info(f"...")`) — use lazy `%s` formatting or `extra={}` for structured data                                                                                                                                                                                                                                          | WARN            |
| 12.11 | Events logged with structured metadata (not free-form strings)                                                                                                                                                                                                                                                                                    | WARN            |
| 12.12 | Correlation IDs propagated through all events for trace reconstruction. End-to-end test (`test_correlation_id_e2e.py`) in `system-integration-tests/` or per-service `tests/integration/` verifying `correlation_id` flows from API ingress → service → PubSub → consumer                                                                         | WARN            |
| 12.13 | Health check endpoints standardized: consistent path (`/health`) and response shape (`{"status": "healthy"}`) across all services                                                                                                                                                                                                                 | WARN            |
| 12.14 | Prometheus metrics exported by all T4–T6 service repos — each exports minimum: `requests_total`, `processing_duration_seconds`, `errors_total`. Verify: `grep -r "prometheus_client" <service>/`                                                                                                                                                  | WARN            |
| 12.15 | AUTH_FAILURE, SECRET_ACCESSED, CONFIG_CHANGED compliance events logged in every service that handles auth or config changes (per lifecycle-events.md). Verify per service: `rg "AUTH_FAILURE                                                                                                                                                      | SECRET_ACCESSED | CONFIG_CHANGED" <service>/` | WARN |
| 12.16 | `validate_timestamp_utc()` (or `validate_timestamp_date_alignment()`) from `unified_trading_library` called on ALL inbound timestamps from external sources (market data, API, PubSub) before processing — no raw datetime ingestion without validation.                                                                                          | YES             |
| 12.17 | `CloudEventSink` (not `GCSEventSink`) used as canonical event sink class name everywhere — `rg 'GCSEventSink' --type py --glob '!.venv*'` = 0 hits.                                                                                                                                                                                               | YES             |
| 12.18 | `test_event_logging.py` MUST exist in `tests/unit/` for every Python service/API/library repo — tests SERVICE_STARTED, SERVICE_STOPPED, SERVICE_FAILED lifecycle events.                                                                                                                                                                          | YES             |
| 12.19 | Memory watchdog implemented in all long-running services (market-tick-data, features-\*, ml-training, ml-inference, execution, strategy, alerting, risk, position-monitor, pnl): psutil memory check ≥ every 60s; at >85% triggers `log_event('SERVICE_MEMORY_CRITICAL', ...)` + checkpoint write via `get_data_sink(routing_key='checkpoints')`. | YES             |
| 12.20 | `correlation_id` propagated through ALL `log_event` calls: extracted from inbound message or generated as `uuid4()` at ingress; present in STARTED/STOPPED/FAILED and all data processing events.                                                                                                                                                 | YES             |

---

## SECTION 13 — CONFIGURATION & ENVIRONMENT

| #     | Criterion                                                                                                                                                                                                                                     | Blocking |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 13.1  | No `os.getenv()` in service code — all config via typed config class (e.g., Pydantic BaseSettings)                                                                                                                                            | YES      |
| 13.2  | No `os.getenv('KEY', '')` empty fallbacks — required values must fail loudly if absent                                                                                                                                                        | YES      |
| 13.3  | No `os.environ["KEY"]` at module level / import time — deferred to config class initialization                                                                                                                                                | YES      |
| 13.4  | Config class validates all required fields at startup — not lazily on first use                                                                                                                                                               | YES      |
| 13.5  | No hardcoded environment-specific values (bucket names, topic names, project IDs)                                                                                                                                                             | YES      |
| 13.6  | Bucket / topic names parameterized by environment (e.g., `market-data-{category}-{project_id}`)                                                                                                                                               | YES      |
| 13.7  | Config extends `UnifiedCloudConfig` from `unified-config-interface` per codex                                                                                                                                                                 | YES      |
| 13.8  | `CLOUD_PROVIDER` env var respected for GCP/AWS switching (`cloud-agnostic.mdc`)                                                                                                                                                               | WARN     |
| 13.9  | `MAX_WORKERS` set based on workload type: I/O-bound=16, CPU-bound=1-3                                                                                                                                                                         | WARN     |
| 13.10 | `.env.example` exists documenting all required env vars with placeholder values                                                                                                                                                               | WARN     |
| 13.11 | `GCP_PROJECT_ID` env var banned — use `GCP_PROJECT_ID` via `UnifiedCloudConfig.gcp_project_id`. Search: `rg 'GCP_PROJECT_ID' --type py --glob '!.venv*'` = 0 hits.                                                                            | YES      |
| 13.12 | Services that manage domain entities (instruments, strategies, clients, venues) MUST declare a `config_store_bucket` field in their config class extending `UnifiedCloudConfig` — no hardcoded domain entity lists in source.                 | YES      |
| 13.13 | Direct `ConfigStore()` construction banned in services — MUST use `get_config_store(domain)` from `unified_config_interface`. Search: `rg 'ConfigStore(' --type py --glob '!.venv*' \| grep -v 'get_config_store\|test_\|conftest'` = 0 hits. | YES      |
| 13.14 | Domain entity subscription lists (instruments, strategies, clients, venues) come from `DomainConfigReloader` — never hardcoded as Python lists/dicts in production source.                                                                    | YES      |
| 13.15 | `CONFIG_CHANGED` event logged whenever any domain config is written (via `/api/config-store/{domain}` endpoint) — includes `domain`, `config_path`, `updated_by`, `schema_version` fields.                                                    | YES      |

---

## SECTION 14 — ARCHITECTURE & DESIGN PATTERNS

### 14.1 Batch-Live Symmetry

| #      | Criterion                                                                                                                                                                                                                             | Blocking                                              |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- | --- |
| 14.1.1 | Service supports `--mode batch                                                                                                                                                                                                        | live` with a single shared engine (≥90% shared logic) | YES |
| 14.1.2 | No `if mode == "batch": ... else: ...` inside engine business logic                                                                                                                                                                   | YES                                                   |
| 14.1.3 | Only 4 seams differ by mode: data source, data sink, persistence, trigger                                                                                                                                                             | YES                                                   |
| 14.1.4 | Business logic, validation, schema, event logging are mode-agnostic                                                                                                                                                                   | YES                                                   |
| 14.1.5 | Batch-live seam test exists (`tests/unit/test_batch_live_seams.py` or `test_service_modes.py`) — calls engine with mock `DataSink` in BATCH mode and mock PubSub source in LIVE mode; asserts identical output schema from both paths | YES                                                   |

### 14.2 Service Architecture

| #      | Criterion                                                                                         | Blocking |
| ------ | ------------------------------------------------------------------------------------------------- | -------- |
| 14.2.1 | Services are thin orchestrators — no business logic in CLI or main entry point                    | WARN     |
| 14.2.2 | Engine / adapters / CLI structure enforced                                                        | WARN     |
| 14.2.3 | Adapters are thin — delegate normalization to unified libraries, not reimplemented per-service    | YES      |
| 14.2.4 | No duplicate schema definitions that already exist in shared contracts library                    | YES      |
| 14.2.5 | No parallel code paths (old + new schema, old + new import) — single source of truth per function | YES      |
| 14.2.6 | Deprecated code deleted, not commented out or aliased                                             | YES      |

### 14.3 Cloud-Agnostic Abstractions

| #      | Criterion                                                                                                                                                                                                                                                                                                                                       | Blocking |
| ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 14.3.1 | Cloud I/O through `get_storage_client()`, `get_secret_client()` from `unified-cloud-interface` — no direct `from google.cloud import` in production code                                                                                                                                                                                        | YES      |
| 14.3.2 | No direct `from google.cloud import pubsub_v1` — use `unified-cloud-interface` PubSub abstraction                                                                                                                                                                                                                                               | YES      |
| 14.3.3 | No direct `import boto3` in production code (except within `unified-cloud-interface` implementations)                                                                                                                                                                                                                                           | YES      |
| 14.3.4 | GCS paths use `key=value` format (`day={date}`, `timeframe={tf}`) with day-first ordering                                                                                                                                                                                                                                                       | YES      |
| 14.3.5 | No protocol-leaking symbols in service source — banned: `CloudTarget`, `upload_to_gcs_batch`, `gcs_bucket=`, `bigquery_dataset=`, `StandardizedDomainCloudService`. Use `DataSink`/`EventBus` ABCs from `unified-cloud-interface`. Search: `rg 'CloudTarget\|upload_to_gcs_batch\|gcs_bucket=\|bigquery_dataset=' --type py --glob '!tests/**'` | YES      |
| 14.3.6 | Services declare runtime mode via `SERVICE_MODE` env var (`LIVE`/`BATCH`) — not hardcoded. Cloud routing injected via `PROTOCOL_DATA_SINK_*` env vars at deploy time, never in source.                                                                                                                                                          | YES      |
| 14.3.7 | Quality gate STEP 5.11 (protocol-leaking symbols check) is present as hard-fail in `scripts/quality-gates.sh` for all service repos                                                                                                                                                                                                             | YES      |
| 14.3.8 | Config event subscriptions go through `DomainConfigReloader` from `unified_trading_library` — services MUST NOT subscribe to `config-updates` or `config-domain-*` PubSub/SQS topics directly. Search: `rg 'config-updates\|config-domain-' --type py --glob '!.venv*' \| grep -v 'DomainConfigReloader\|test_'` = 0 hits.                      | YES      |

### 14.4 Async & Concurrency

| #      | Criterion                                                                          | Blocking |
| ------ | ---------------------------------------------------------------------------------- | -------- |
| 14.4.1 | `aiohttp` used for HTTP in async contexts — no `requests.get()` inside `async def` | YES      |
| 14.4.2 | `asyncio.sleep()` used — not `time.sleep()` in async functions                     | YES      |
| 14.4.3 | No `asyncio.run()` called inside a running event loop                              | YES      |
| 14.4.4 | `ClientSession` reused — not created per-request                                   | WARN     |
| 14.4.5 | `ThreadPoolExecutor` always given `max_workers` limit                              | YES      |

---

## SECTION 15 — FILE SIZE & COMPLEXITY

| #    | Criterion                                                                                                                                                                                                            | Blocking |
| ---- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 15.1 | No source file exceeds 900 lines (warn at 700)                                                                                                                                                                       | YES      |
| 15.2 | No function exceeds 100 lines                                                                                                                                                                                        | WARN     |
| 15.3 | No method (inside class) exceeds 50 lines                                                                                                                                                                            | WARN     |
| 15.4 | No class exceeds 500 lines                                                                                                                                                                                           | WARN     |
| 15.5 | Files split by Single Responsibility Principle (no god files mixing adapters + schemas + CLI)                                                                                                                        | WARN     |
| 15.6 | No functions over 200 lines in production code (extreme oversized — automatic FAIL)                                                                                                                                  | YES      |
| 15.7 | No near-duplicate files serving the same purpose in different locations                                                                                                                                              | WARN     |
| 15.8 | Static data extracted to YAML/JSON — not inline Python dicts >500 lines                                                                                                                                              | WARN     |
| 15.9 | All known files that legitimately exceed size limits (e.g., generated schema files: `aws_schemas.py` 1424L, `venue_manifest.py` 1058L) are documented in `QUALITY_GATE_BYPASS_AUDIT.md` — no undocumented exceptions | WARN     |

---

## SECTION 16 — SCHEMA GOVERNANCE & DATA CONTRACTS

### 16.1 Schema Ownership

| #      | Criterion                                                                                                                                                                                                                                                                                  | Blocking |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| 16.1.1 | Three-tier schema separation: external (api-contracts) → normalized (canonical) → internal (service)                                                                                                                                                                                       | YES      |
| 16.1.2 | Each service owns its output schema — not defined in shared library                                                                                                                                                                                                                        | YES      |
| 16.1.3 | `validate_timestamp_date_alignment()` called before every storage write                                                                                                                                                                                                                    | YES      |
| 16.1.4 | `schema_version` field present on all internal contract models                                                                                                                                                                                                                             | WARN     |
| 16.1.5 | `SchemaRegistry` documents compatibility matrix for all versioned schemas                                                                                                                                                                                                                  | WARN     |
| 16.1.6 | Breaking changes (field removal, type narrowing, Optional→required) require version bump                                                                                                                                                                                                   | YES      |
| 16.1.7 | Service output schemas consumed cross-service live in `unified-internal-contracts domain/<service>/` — not in the producing service's own `output_schemas.py`. Verify: `rg 'from <service_name>.*output_schemas' --type py --glob '!tests/**'` returns 0 matches across consuming services | YES      |
| 16.1.8 | Layer 0 contract-alignment tests (`test_contract_alignment.py`, `test_ac_uic_alignment.py`) are EXECUTED in the owning interface repos (unified-market-interface, unified-cloud-interface, unified-reference-data-interface) — not just defined in AC                                      | YES      |

### 16.2 External API Contracts

| #      | Criterion                                                                           | Blocking |
| ------ | ----------------------------------------------------------------------------------- | -------- |
| 16.2.1 | Every external API response parsed through a Pydantic model before any processing   | YES      |
| 16.2.2 | Per-venue schemas exist for all data types the system consumes                      | YES      |
| 16.2.3 | VCR cassettes exist for all external API interactions used in tests                 | WARN     |
| 16.2.4 | VCR cassette coverage ≥ 80% of external endpoints (not relying on live calls in CI) | WARN     |
| 16.2.5 | Consumer-driven contract tests: consuming services declare `consumed_schemas.py`    | WARN     |
| 16.2.6 | `unified-api-contracts` version alignment checked per consumer                      | WARN     |

### 16.3 Canonical Schema Completeness

Verify the following data type groups have canonical schemas with appropriate Optional fields:

| Data Type          | Required Fields                                                                      | Optional Pattern             |
| ------------------ | ------------------------------------------------------------------------------------ | ---------------------------- |
| Trade              | instrument_key, venue, timestamp, price, size, side, trade_id                        | is_liquidation               |
| OrderBook          | instrument_key, venue, timestamp, bids, asks, levels                                 | —                            |
| OHLCV              | instrument_key, venue, timestamp, interval, open/high/low/close, volume, source_enum | vwap, trade_count            |
| DerivativeTicker   | instrument_key, venue, timestamp, mark_price, index_price                            | funding_rate, open_interest  |
| Liquidation        | instrument_key, venue, timestamp, side, price, size                                  | order_id                     |
| OptionsChain       | underlying, expiry, strike, put_call, bid, ask                                       | iv, greeks, oi, volume       |
| LiquidityPool      | pool_address, protocol, chain, token0/1, fee_tier, reserves, tvl                     | apy, tick fields (V3)        |
| LendingRate        | protocol, chain, asset, supply_apy, borrow_apy_variable                              | borrow_apy_stable            |
| OraclePrice        | feed_id, protocol, asset, price, publish_time                                        | confidence                   |
| InstrumentRecord   | instrument_key, venue, asset_class, instrument_type, base, quote                     | expiry, strike, pool_address |
| Position (CeFi)    | instrument_key, venue, side, size, entry_price, mark_price, unrealized_pnl           | liquidation_price            |
| Position (DeFi LP) | pool_address, protocol, token amounts, liquidity, fee_income                         | in_range, tick bounds        |

| #      | Criterion                                                                      | Blocking             |
| ------ | ------------------------------------------------------------------------------ | -------------------- | ---- |
| 16.3.1 | All consumed data types have a canonical schema                                | YES                  |
| 16.3.2 | Absent fields (venue does not provide) are `Optional` — not absent from schema | YES                  |
| 16.3.3 | `source` enum on OHLCV: `NATIVE_CANDLE                                         | COMPUTED_FROM_TICKS` | WARN |
| 16.3.4 | No monolithic position schema mixing CeFi + DeFi                               | WARN                 |

### 16.4 Dead-Letter & DLQ

| #      | Criterion                                                                                         | Blocking |
| ------ | ------------------------------------------------------------------------------------------------- | -------- |
| 16.4.1 | Dead-letter queue exists for failed validation records                                            | YES      |
| 16.4.2 | `DeadLetterRecord` schema includes: original_payload, error_type, error_message, venue, timestamp | YES      |
| 16.4.3 | `correlation_id` and `trace_id` in `DeadLetterRecord` for tracing                                 | WARN     |
| 16.4.4 | DLQ depth monitored and alerted                                                                   | WARN     |

### 16.5 Connectivity & Lifecycle Schemas

| #      | Criterion                                                                                                    | Blocking |
| ------ | ------------------------------------------------------------------------------------------------------------ | -------- |
| 16.5.1 | WebSocket lifecycle schemas exist per venue: connect, disconnect, reconnect, error, ping/pong, subscribe ack | WARN     |
| 16.5.2 | REST connectivity error schemas exist: timeout, rate limit, maintenance mode, connection refused             | WARN     |
| 16.5.3 | `SCHEMA_VERSIONS.md` exists documenting which external SDK versions schemas were validated against           | WARN     |
| 16.5.4 | Endpoint-to-schema association matrix documented: every schema class tied to its source endpoint/channel     | WARN     |

---

## SECTION 17 — TESTING STANDARDS

### 17.1 Python Testing

| #       | Criterion                                                                                                                                                                                                                                       | Blocking |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 17.1.1  | Test coverage ≥ 70% (unit + integration) per codex canonical target                                                                                                                                                                             | YES      |
| 17.1.2  | `tests/unit/test_event_logging.py` exists and is not skipped                                                                                                                                                                                    | YES      |
| 17.1.3  | Unit tests never skip due to missing cloud credentials — mocks used instead                                                                                                                                                                     | YES      |
| 17.1.4  | GCP auth uses `google.auth.default()` pattern — not `pytest.skip` on missing credentials file                                                                                                                                                   | YES      |
| 17.1.5  | Integration tests marked `@pytest.mark.integration` and skipped gracefully without credentials                                                                                                                                                  | YES      |
| 17.1.6  | No `central-element-323112` or real project IDs in tests — use `test-project` placeholder                                                                                                                                                       | YES      |
| 17.1.7  | No tests with zero assertions (`assert True` placeholders or empty test functions)                                                                                                                                                              | YES      |
| 17.1.8  | No duplicate fixtures across test files — singleton fixtures in `conftest.py`                                                                                                                                                                   | WARN     |
| 17.1.9  | `conftest.py` exists with autouse `mock_secret_client` fixture                                                                                                                                                                                  | WARN     |
| 17.1.10 | VCR cassettes used for external API tests — no live calls in CI                                                                                                                                                                                 | WARN     |
| 17.1.11 | Python version alignment: workflows, Cloud Build, local quality gates, and `pyproject.toml` all specify same Python version (3.13)                                                                                                              | YES      |
| 17.1.12 | Layer 1.5 per-component integration tests exist in `tests/integration/` per service repo — at least one `test_<component>_integration.py` using mocked direct dependencies (`@pytest.mark.integration`). These tests BLOCK quickmerge (D3 gate) | YES      |
| 17.1.13 | Layer 1.5 tests are included in `scripts/quickmerge.sh` integration step — not skipped by default. Verify: `grep -q "integration\|Layer 1.5\|pytest.*integration" scripts/quickmerge.sh`                                                        | YES      |
| 17.1.14 | No `test_*_extended.py` files — all extended test cases merged into their base `test_*.py` file. Search: `rg 'test_.*_extended\.py' --type py` = 0 hits.                                                                                        | YES      |

### 17.2 TypeScript Testing & Quality Gates

| #      | Criterion                                                                                                        | Blocking |
| ------ | ---------------------------------------------------------------------------------------------------------------- | -------- |
| 17.2.1 | UI repos have `scripts/quality-gates.sh` using TypeScript checks (not Python ruff/basedpyright)                  | YES      |
| 17.2.2 | `tsconfig.json` has `strict: true`, `noImplicitAny: true`, `strictNullChecks: true`, `strictFunctionTypes: true` | YES      |
| 17.2.3 | `tsc --noEmit` passes with zero errors (TypeScript equivalent of basedpyright strict)                            | YES      |
| 17.2.4 | `package.json` has `"typecheck": "tsc --noEmit"` and `"lint": "eslint ."` scripts                                | YES      |
| 17.2.5 | ESLint configured and passing (`npm run lint`)                                                                   | YES      |
| 17.2.6 | UI repos have at least smoke tests (vitest or Playwright)                                                        | WARN     |
| 17.2.7 | No Python quality gate tools (ruff, basedpyright, pytest) in UI repo scripts                                     | YES      |
| 17.2.8 | `package.json` `name` field matches repo name (no stale names like `backtest-ui`)                                | WARN     |

---

# PART C — CROSS-REPO ALIGNMENT CHECKS

---

## SECTION 18 — RUNTIME TOPOLOGY ALIGNMENT

Validates `runtime-topology.yaml` against actual implementations.

| #     | Criterion                                                                                                      | Blocking |
| ----- | -------------------------------------------------------------------------------------------------------------- | -------- |
| 18.1  | `runtime-topology.yaml` version field current and matches deployed version                                     | YES      |
| 18.2  | All service clusters in topology match manifest service repos (no phantom services, no missing services)       | YES      |
| 18.3  | Transport modes per edge match actual implementations: batch=GCS, live=PubSub, co_located=in_memory            | YES      |
| 18.4  | Service-to-service flows listed in `service_flows` match actual data dependencies in code                      | YES      |
| 18.5  | PubSub topic naming follows templates defined in topology                                                      | WARN     |
| 18.6  | All services persist to GCS regardless of transport mode (dual write in live mode)                             | YES      |
| 18.7  | Redis used only by execution-service for hot transient state — not as transport or persistence                 | WARN     |
| 18.8  | `RUNTIME_DEPLOYMENT_TOPOLOGY_DAG.svg` regenerated and matches current topology                                 | WARN     |
| 18.9  | No service-to-service Python imports that should be runtime interactions per topology                          | YES      |
| 18.10 | Co-location rules match deployment config (only services in `co_located_vm` profile share in_memory transport) | WARN     |

---

## SECTION 19 — DATA FEED UNIVERSE COMPLETENESS

_Applicable to systems with multi-venue market data ingestion._

| #     | Criterion                                                                                                       | Blocking |
| ----- | --------------------------------------------------------------------------------------------------------------- | -------- |
| 19.1  | api-contracts schema exists for every data type per supported venue                                             | YES      |
| 19.2  | Normalizer function exists in adapter for each confirmed data type                                              | YES      |
| 19.3  | Confirmed data types have VCR cassette test (not live call)                                                     | WARN     |
| 19.4  | Absent data types documented in `VenueCapabilities` — not just missing                                          | YES      |
| 19.5  | Canonical output identical whether data sourced from aggregator (Tardis/CCXT) or direct exchange WS             | YES      |
| 19.6  | Source choice is a config concern, not hardcoded in engine                                                      | YES      |
| 19.7  | DeFi schemas support V2/V3/V4 liquidity pools (V3-specific fields Optional)                                     | WARN     |
| 19.8  | Lending schemas include: supply APY, borrow APY, utilization, health factor, LTV                                | WARN     |
| 19.9  | Oracle price schemas cover both Pyth and Chainlink formats                                                      | WARN     |
| 19.10 | Order lifecycle state machine: `PENDING_NEW → NEW → PARTIALLY_FILLED → FILLED / CANCELLED / REJECTED / EXPIRED` | WARN     |
| 19.11 | Sports data schemas: LiveOddsUpdate, LiveMatchState, bookmaker schemas (22 bookmakers in USEI)                  | WARN     |
| 19.12 | Per-venue order type support declared in `VenueCapabilities` schema                                             | WARN     |

---

## SECTION 20 — TECHNICAL DEBT TRACKING

| #     | Criterion                                                                                                                                           | Blocking |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 20.1  | `# type: ignore` suppression count tracked per repo and trending downward from previous audit                                                       | WARN     |
| 20.2  | `Any` type usage count tracked per repo and trending downward                                                                                       | YES      |
| 20.3  | Skipped test count tracked with justification for each skip                                                                                         | WARN     |
| 20.4  | `except ImportError` fallback count tracked (target: zero in production code)                                                                       | YES      |
| 20.5  | `except Exception: pass` count tracked (target: zero)                                                                                               | YES      |
| 20.6  | Files exceeding 900-line limit tracked with refactoring plan                                                                                        | WARN     |
| 20.7  | Functions exceeding 200-line limit tracked with split plan                                                                                          | WARN     |
| 20.8  | Missing return type annotations tracked (target: <20% missing)                                                                                      | WARN     |
| 20.9  | Dead code (unused functions, commented-out blocks) tracked and scheduled for removal                                                                | WARN     |
| 20.10 | `QUALITY_GATE_BYPASS_AUDIT.md` workspace aggregate at codex level (`10-audit/QUALITY_GATE_BYPASS_AUDIT.md`) updated quarterly                       | WARN     |
| 20.11 | Per-repo `QUALITY_GATE_BYPASS_AUDIT.md` entries are either empty or contain only genuine unsolvable exceptions — no stale entries, no lazy bypasses | YES      |
| 20.12 | Coverage thresholds below 70% tracked per repo with remediation timeline                                                                            | WARN     |

---

## SECTION 21 — SAFETY & RISK CONTROLS

| #     | Criterion                                                                                                                                                                                        | Blocking |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| 21.1  | Position limits enforced before order submission                                                                                                                                                 | YES      |
| 21.2  | Margin state checked before every leveraged trade                                                                                                                                                | YES      |
| 21.3  | `MarginState` fields all non-optional and required from every adapter                                                                                                                            | YES      |
| 21.4  | Gas cost estimated before every DeFi transaction — never unlimited gas                                                                                                                           | YES      |
| 21.5  | Slippage tolerance enforced on all DEX swaps                                                                                                                                                     | YES      |
| 21.6  | `health_factor` checked before additional borrowing (DeFi)                                                                                                                                       | YES      |
| 21.7  | Liquidation threshold monitored with alerts                                                                                                                                                      | WARN     |
| 21.8  | Circuit breaker exists for P&L drawdown limits                                                                                                                                                   | WARN     |
| 21.9  | All order amounts validated against tick size and lot size constraints                                                                                                                           | YES      |
| 21.10 | Kill switch topology matches `runtime-topology.yaml` `kill_switches` section                                                                                                                     | WARN     |
| 21.11 | Regulatory retention periods defined for trade records (min 7 years for most jurisdictions)                                                                                                      | WARN     |
| 21.12 | Sports execution path risk controls (circuit breaker, preflight checks, kill switch) are explicitly marked N/A until USEI v1 adapters (Betfair, Pinnacle) are implemented — not silently omitted | WARN     |

---

# PART D — DEPLOYMENT CHECKS

---

## SECTION 22 — CI/CD & QUICKMERGE PIPELINE

| #     | Criterion                                                                                                                                                                                                                                                                                                           | Blocking |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 22.1  | Quality gates run INSIDE the built Docker image — not by cloning source in CI                                                                                                                                                                                                                                       | YES      |
| 22.2  | Image pushed only after tests pass                                                                                                                                                                                                                                                                                  | YES      |
| 22.3  | Library version bumped only by GitHub Action (`version-bump.yml`) on merge — not manual                                                                                                                                                                                                                             | YES      |
| 22.4  | Branch protection blocks direct push to main                                                                                                                                                                                                                                                                        | YES      |
| 22.5  | Quickmerge used for all pushes — never standalone quality gates or bare `git push`                                                                                                                                                                                                                                  | YES      |
| 22.6  | `--dep-branch` used in quickmerge when dependencies differ from main                                                                                                                                                                                                                                                | YES      |
| 22.7  | Pre-flight audit runs before quality gates (path dependency uncommitted changes check)                                                                                                                                                                                                                              | WARN     |
| 22.8  | No git token or SA key embedded in Dockerfile or Cloud Build YAML                                                                                                                                                                                                                                                   | YES      |
| 22.9  | `uv.lock` committed alongside `pyproject.toml` changes                                                                                                                                                                                                                                                              | YES      |
| 22.10 | CI clones path deps to `../repo-name` with `${DEP_BRANCH:-main}` fallback per `path-dependency-ci.mdc`                                                                                                                                                                                                              | YES      |
| 22.11 | Conventional commit messages used (`feat:` / `fix:` / `chore:`)                                                                                                                                                                                                                                                     | WARN     |
| 22.12 | `quality-gates.yml` GitHub Actions workflow exists and runs on PRs — no repos with zero CI enforcement                                                                                                                                                                                                              | YES      |
| 22.13 | Pre-commit hooks fire automatically during quickmerge's `git commit` step (Stage 5) — ruff auto-fix, prettier, and file checks run before commit is created                                                                                                                                                         | YES      |
| 22.14 | Test-in-image pattern used for services with Docker-based deployment: tests run inside built Docker image (not as separate cloudbuild pip install step). Verify `cloudbuild.yaml` has `docker run --entrypoint pytest ...` step. Currently required for: `instruments-service`, `position-balance-monitor-service`. | YES      |

---

## SECTION 23 — DOCKER & DEPLOYMENT STANDARDS

| #     | Criterion                                                                                               | Blocking |
| ----- | ------------------------------------------------------------------------------------------------------- | -------- |
| 23.1  | Multi-stage Docker build pattern followed per codex `05-infrastructure/docker.md`                       | YES      |
| 23.2  | Python 3.13 base image used (matching `pyproject.toml` `requires-python`)                               | YES      |
| 23.3  | Non-root user (`appuser`) in all Dockerfiles — no running as root in production                         | YES      |
| 23.4  | `.dockerignore` exists in all repos with Dockerfiles                                                    | YES      |
| 23.5  | `HEALTHCHECK` directive in every service Dockerfile                                                     | WARN     |
| 23.6  | No `GH_PAT` or secrets persisted in final image layer (multi-stage build cleans build args)             | YES      |
| 23.7  | `uv pip install` used in Dockerfiles — no bare `pip install`                                            | YES      |
| 23.8  | Dev dependencies NOT included in production images                                                      | WARN     |
| 23.9  | Dockerfile exists for all deployable services and API services                                          | YES      |
| 23.10 | `tini` or equivalent init process used for proper signal handling                                       | WARN     |
| 23.11 | All service Dockerfiles use `unified-trading-services:latest` base image (not `unified-cloud-services`) | YES      |
| 23.12 | Terraform configs exist for all production services (or documented exception)                           | WARN     |

---

# PART E — ANTI-PATTERNS & SUMMARY

---

## SECTION 24 — ANTI-PATTERN SCAN

Run a targeted scan for the following patterns. Each `FOUND` in production code = automatic FAIL (unless noted WARN).

```
PATTERN                                | SEARCH                                                    | BLOCKING
os.getenv(                             | rg "os\.getenv" --type py (excl tests)                    | YES
os.environ["KEY"] at import time       | rg 'os\.environ\[' --type py (module level)               | YES
requests.get( / requests.post(         | rg "requests\.(get|post)" --type py (async contexts)      | YES
datetime.now() (no timezone)           | rg "datetime\.now\(\)" --type py                          | YES
datetime.utcnow()                      | rg "datetime\.utcnow" --type py                           | YES
except Exception: pass                 | rg "except Exception:\s*pass" --type py                   | YES
except: (bare)                         | rg "except:" --type py                                    | YES
from typing import List/Dict           | rg "from typing import.*(List|Dict)" --type py            | WARN
# type: ignore (each instance)         | rg "# type: ignore" --type py                             | WARN
Any (unaudited)                        | rg ": Any|-> Any" --type py                               | YES
pip install (in scripts/Dockerfiles)   | rg "pip install" scripts/ Dockerfile                      | YES
git push origin main                   | rg "git push origin main"                                 | YES
git reset --hard                       | rg "git reset --hard"                                     | YES
GCP_PROJECT_ID                   | rg "GCP_PROJECT_ID" --type py                       | YES
hardcoded project ID                   | rg "central-element|my-project-id" --type py              | YES
_old.py / _legacy.py files            | find . -name "*_old.py" -o -name "*_legacy.py"            | YES
try/except ImportError                 | rg "except ImportError" --type py                         | YES
print( in production                   | rg "^\s*print\(" --type py (excl tests, scripts)          | WARN
time.sleep( in async contexts          | rg "time\.sleep" --type py (in async functions)            | YES
from google.cloud import (production)  | rg "from google\.cloud import" --type py (excl tests, UCI)| YES
import boto3 (production)              | rg "import boto3" --type py (excl tests, UCI)             | YES
logging.basicConfig() in libraries     | rg "logging\.basicConfig" --type py (excl tests)          | YES
from X import * (wildcard)             | rg "from \w+ import \*" --type py (excl __init__)         | YES
logger.info(f" (f-string logging)     | rg 'logger\.\w+\(f"' --type py                            | WARN
.pre-commit-config.yaml missing        | ls .pre-commit-config.yaml (each repo root)               | YES
bump-library-version in non-library    | grep "bump-library-version" .pre-commit-config.yaml (svc) | WARN
prettier version mismatch             | grep "prettier@" .pre-commit-config.yaml (expect 3.6.2)   | WARN
ruff pre-commit rev mismatch          | grep "rev: v" .pre-commit-config.yaml (expect v0.15.0)    | YES
verify=False in HTTP clients          | rg "verify=False" --type py (excl tests)                  | YES
mock auth in production               | rg '"client-.*-key"\|mock.*auth\|fake.*token' --type py (excl tests) | YES
CloudTarget in service code           | rg "CloudTarget" --type py (excl tests, UCI, UTL)         | YES
upload_to_gcs_batch in service code   | rg "upload_to_gcs_batch" --type py (excl tests, UTL)      | YES
output_schemas.py cross-service import| rg "from \w+_service.*output_schemas" --type py           | YES
ConfigStore() without get_config_store | rg 'ConfigStore(' --type py | grep -v get_config_store  | FAIL
Hardcoded domain lists in source      | rg 'subscription_list\s*=\s*\[' --type py --glob '!test*' | WARN
```

---

## SECTION 25 — SCORING GUIDE & REPORT TEMPLATE

### Scoring Guide

| Grade                | Criteria                                |
| -------------------- | --------------------------------------- |
| **PASS**             | 0 FAIL items                            |
| **CONDITIONAL PASS** | 0 FAIL, ≤5 WARN (with remediation plan) |
| **FAIL**             | ≥1 FAIL item                            |

**Automatic FAIL triggers (any one is sufficient):**

- Hardcoded API key or credential in source
- `except Exception: pass` in production code
- Validation failure silently passed through (no dead-letter)
- `os.getenv()` with empty string fallback for required config
- No lifecycle STOPPED/FAILED event on service exit
- `basedpyright` `reportAny` errors present (or `typeCheckingMode` not "strict")
- `tsc --noEmit` errors present in TypeScript repos (or `strict: false` in tsconfig)
- `Any` type in schema models at API boundaries
- Tests skipped due to missing credentials (unit test scope)
- Direct `git push main` bypassing quality gates
- Service importing another service as Python package dependency
- `QUALITY_GATE_BYPASS_AUDIT.md` missing from repo
- `|| true` in CI quality gate workflow steps

### Output Template

```
## Unified Trading System — Audit Report
## Date: [YYYY-MM-DD] | Auditor: [name/agent]
## Scope: [workspace-wide / specific repo(s)]

### Summary
- Total criteria evaluated: N
- PASS: X | WARN: Y | FAIL: Z | N/A: W
- Overall grade: PASS / CONDITIONAL PASS / FAIL

### Part A: Workspace-Level (Sections 1-7)
CATEGORY | CRITERION | STATUS | EVIDENCE
S1 Manifest | 1.1 All repos registered | PASS | 60/60 repos found
...

### Part B: Per-Repo Code Quality (Sections 8-17)
CATEGORY | CRITERION | STATUS | EVIDENCE
S8 Linting | 8.1 Ruff zero errors | PASS | ruff check returned 0
...

### Part C: Cross-Repo Alignment (Sections 18-21)
...

### Part D: Deployment (Sections 22-23)
...

### Part E: Anti-Pattern Scan (Section 24)
PATTERN | SEARCH | FOUND | COUNT | FILES
os.getenv | rg "os\.getenv" | YES | 25 | [file list]
...

### Blocking Findings (FAIL) — Top 10
1. [SECTION] [ID] — [description] — [file:line]
...

### Warning Findings (WARN)
1. [SECTION] [ID] — [description] — [file:line]
...

### Technical Debt Trajectory
| Metric | Previous Audit | Current | Delta |
|--------|---------------|---------|-------|
| # type: ignore | — | 395 | — |
| Any usage | — | 1,626 | — |
| Skipped tests | — | 231 | — |
| Files >900 lines | — | 30+ | — |
| Functions >200 lines | — | 271 | — |
| Coverage avg % | — | 0 | — |

### Remediation Priority
P0 (Security): [items]
P1 (Architecture): [items]
P2 (Quality): [items]
P3 (Polish): [items]

### Per-Repo Scorecard
| Repo | S8 | S9 | S10 | S11 | ... | Grade |
|------|----|----|-----|-----|-----|-------|
| ... | P | W | P | F | ... | FAIL |
```
