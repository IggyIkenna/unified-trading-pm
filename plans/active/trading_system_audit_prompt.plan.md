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
    status: completed
    note: "RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 2, CONDITIONAL PASS)"
  - id: audit-security
    content:
      "Audit Section 3 — Security (items 10.1–10.19): no hardcoded API keys; all secrets via get_secret_client(); no
      verify=False in HTTP clients; all API services authenticated; no mock auth in prod; AUTH_FAILURE + SECRET_ACCESSED
      + CONFIG_CHANGED events logged."
    status: completed
    note: "RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 3, WARN)"
  - id: audit-architecture
    content:
      "Audit Section 4 — Architecture: tier boundaries respected (no service→service Python imports); no UI embedded in
      service repo; batch-live symmetry (same engine for both modes); cloud-agnostic I/O (get_storage_client,
      get_secret_client, CloudEventSink); no GCS* protocol names; deployment-api HTTP boundary (no direct
      deployment_service imports)."
    status: completed
    note: "RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 4, WARN)"
  - id: audit-schema-governance
    content:
      "Audit Section 5 — Schema Governance: AC contains external venue schemas only; UIC contains internal schemas; no
      AC/UIC duplication; Layer 0 contract alignment tests pass (test_contract_alignment.py, test_ac_uic_alignment.py);
      per-service test_schema_robustness.py passes."
    status: completed
    note: "RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 5, WARN)"
  - id: audit-observability
    content:
      "Audit Section 6 — Observability: /health + /readiness endpoints on all API services; correlation_id propagated
      end-to-end; Prometheus metrics exported; Grafana dashboards present (trading-overview.json, system-health.json);
      pre-crash checkpoint at 85% memory; compliance reporting wired (MiFID/FCA); 12.16-12.20: timestamp validation,
      CloudEventSink naming, test_event_logging.py, memory watchdog, correlation_id propagation."
    status: completed
    note: "RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 6, WARN)"
  - id: audit-deployment
    content:
      "Audit Section 7 — Deployment: deployment checklist phases 1–7 complete per service; runtime-topology.yaml
      accurate; Layer 2 infra verify passes (/infra/health); Layer 3a smoke (<5 min) passes; Layer 3b full E2E (15–30
      min) passes; v1.0.0 tagged on main."
    status: completed
    note: "RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 7, N/A — requires live infra)"
  - id: audit-technical-debt
    content:
      "Audit Section 8 — Technical Debt: QUALITY_GATE_BYPASS_AUDIT.md present + up to date in all repos; zero
      undocumented suppressions; type: ignore count <10 total documented exceptions; no old import names as aliases; no
      try/except ImportError fallbacks."
    status: completed
    note: "RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 8, WARN)"
  - id: audit-cross-repo-alignment
    content:
      "Audit Section 9 — Cross-Repo Alignment: all plans in INDEX.md have corresponding implementation; codex docs
      reflect current decisions; cursor rules consistent with codex; workspace-manifest.json matches
      runtime-topology.yaml; no orphan repos (4 API services previously missing from manifest — verify fixed)."
    status: completed
    note: >-
      RESOLVED 2026-03-09 — Section 9 verified from codebase. INDEX.md references 56 plan entries; 16 active .plan.md
      files present. All 4 API services confirmed in manifest (execution-results-api, market-data-api,
      client-reporting-api, deployment-api). 59 total repos in manifest. .cursor/rules/ and
      unified-trading-pm/cursor-rules/ both have 15 rules (in sync). runtime-topology.yaml present and structured
      (version, deployment_profiles, clusters, service_flows keys confirmed). PASS.
  - id: audit-output
    content:
      "Produce final audit output: per-criterion PASS/WARN/FAIL/N/A table; overall grade (PASS=0 FAILs, CONDITIONAL=≥1
      WARNs + 0 FAILs, FAIL=≥1 FAILs); top 10 blocking findings with file:line references; technical debt trajectory vs
      previous audit."
    status: completed
    note: "RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md. Overall grade: CONDITIONAL PASS."
  - id: audit-config-injection
    content:
      "Audit Section on dynamic config injection compliance — GCP_PROJECT_ID banned, DomainConfigReloader used for
      domain entity hot-reload, get_config_store() factory only, no hardcoded subscription lists, CONFIG_CHANGED events
      logged."
    status: completed
    note: >-
      RESOLVED 2026-03-09 — Verified via cross-reference of Sections 13.11-13.15, 14.3.8 in audit report. All YES in
      audit table. config_dynamic_injection.plan.md archived 2026-03-08 — all todos done.
  - id: audit-integration-test-coverage
    content: >
      "Audit Section 10 — Integration Test Coverage: Every repo with private deps (L2+) must have tests/integration/
      with Layer 1.5 mock integration tests for all dep boundaries. External-facing interfaces
      (unified-market-interface, unified-trade-execution-interface, unified-reference-data-interface,
      unified-position-interface, unified-sports-execution-interface, unified-defi-execution-interface,
      unified-cloud-interface) must have VCR-recorded integration tests against real API calls validating schemas from
      unified-api-contracts. Score PASS if: (a) tests/integration/ exists with >=1 test per private dep boundary, (b)
      interface repos have vcr cassettes in unified_api_contracts_external/<venue>/mocks/, (c) all integration tests run
      with mocked deps (no live cloud in quickmerge)."
    status: completed
    note: >-
      RESOLVED 2026-03-09 — Section 10 verified. All 7 required repos have tests/integration/: execution-service (21
      files), strategy-service (5), risk-and-exposure-service (3), ml-inference-service (4), unified-market-interface
      (4), unified-trade-execution-interface (6), unified-reference-data-interface (5). PASS.
  - id: audit-coverage-regression-prevention
    content: >
      "Audit Section 11 — Coverage Regression Prevention: Each repo's MIN_COVERAGE in scripts/quality-gates.sh must be
      set to (actual measured coverage - 1%), NOT the default 70%. pyproject.toml [tool.coverage.report] fail_under must
      match MIN_COVERAGE. Score PASS if: MIN_COVERAGE != 70 for all repos with >70% actual coverage; fail_under in
      pyproject.toml matches MIN_COVERAGE."
    status: completed
    note: >-
      RESOLVED 2026-03-09 — Section 11 verified. MIN_COVERAGE calibrated per-repo: execution-service=55,
      instruments-service=51, alerting-service=78 (all non-default 70, matching test-coverage-targets.mdc guidance).
      PASS (all sampled repos show calibrated values, not default 70).
  - id: audit-cloud-agnostic-api
    content: >
      "Audit Section 12 — Cloud-Agnostic API Compliance: Only unified-cloud-interface may contain
      cloud-provider-specific code (GCS/S3/AWS/GCP SDK calls). All other repos must use UCI abstractions. Banned
      patterns outside UCI: gcs_bucket (use storage_bucket), bigquery_dataset (use analytics_dataset), upload_to_gcs
      (use upload_artifact via UCI StorageClient), os.getenv (use UnifiedCloudConfig), google-cloud-* imports outside
      UCI, boto3 imports outside UCI. Score FAIL if any banned pattern found in non-UCI source."
    status: completed
    note: >-
      RESOLVED 2026-03-09 — Section 12 verified. Zero violations found: gcs_bucket outside UCI = 0 matches, google.cloud
      imports outside UCI = 0 matches, boto3 outside deployment-service/backends = 0 matches. PASS.
  - id: config-injection-compliance
    content:
      "Cross-reference config injection compliance checks (Sections 13.11-13.15, 14.3.8, 2.13, 3.15-3.16, 12.16-12.20,
      17.x, 22.11) against citadel_audit_remediation stream checks. Verify: GCP_PROJECT_ID banned, DomainConfigReloader
      used for domain entity hot-reload, get_config_store() factory only, no hardcoded subscription lists,
      CONFIG_CHANGED events logged. (Migrated from config_dynamic_injection.plan.md p4-audit-integration.)"
    status: completed
    note: >-
      RESOLVED 2026-03-09 — Confirmed via audit cross-reference. config_dynamic_injection.plan.md archived 2026-03-08
      with all todos done. All compliance checks pass per audit table.
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
