---
doc_type: plan
title: trading-system-audit-prompt
summary: DO NOT ARCHIVE — used for continuous audit checks. Canonical audit checklist for the unified trading system workspace
  against institutional-grade standards. Covers workspace governance, code quality, security, architecture, schema governance,
  observability, deployment, technical debt, cross-repo alignment, CI/CD pipeline quality, UI/npm governance, and tooling
  SSOT quality (Sections 1–17).
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-02-28'
type: infra
epic: none
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: system-integration-tests, code: C1, deployment: none, business: none, readiness_note: 'DR N/A: local developer tooling — no cloud deployment required. BR N/A: internal tooling, no commercial KPI.'}
- {repo: unified-trading-pm, code: C1, deployment: none, business: none, readiness_note: 'DR N/A: local developer tooling — no cloud deployment required. BR N/A: internal tooling, no commercial KPI.'}
depends_on: []
todos:
- {id: audit-workspace-governance, content: 'Audit Section 1 — Workspace Governance: workspace-manifest.json complete + DAG valid; all 57 repos registered; arch_tier correct; ci_status fields present. Score each criterion PASS/WARN/FAIL/N/A with file:line evidence.', status: completed, note: 'RE-AUDITED 2026-03-10T02:31:37Z — PASS. 59 repos registered (was 57 at last baseline), DAG acyclic, 132 cursor rules confirmed.'}
- {id: audit-code-quality, content: 'Audit Section 2 — Code Quality: quality-gates.sh present + passing per repo; MIN_COVERAGE=70 floor; file <900L, function <200L, method <50L, class <900L; ruff + basedpyright strict + reportAny:error; zero os.getenv in production source; zero Any in public API. ALSO CHECK: (a) pyrightconfig.json has "exclude": ["tests"] so basedpyright scope matches .cursorignore — FAIL if tests/ is typechecked; (b) all codex rg checks in quality-gates.sh/base-service.sh use --glob "!tests/**" so linter only scans source — FAIL if tests/ is linted for os.getenv/print/bare-except etc; (c) quality-gates.sh is a thin stub delegating to base-service.sh / base-library.sh / base-ui.sh — FAIL if a repo has a full-body QG script (>50 lines) instead of the stub pattern. Score each repo.', status: completed, note: 'RE-AUDITED 2026-03-09 — FAIL. 356 function violations (>100L), 78 class violations (>500L), 3 bare excepts (strategy-service/signal_publisher.py:96,151; execution-service/dependency_checker.py:222).
    See SYSTEM_AUDIT_REPORT_2026_03_09.md Section 2. RE-AUDITED 2026-03-10T02:31:37Z — FAIL. quality-gates.sh missing from 5 key repos (market-data-processing-service, execution-service, strategy-service, ml-inference-service, unified-market-interface); OrchestrationWorkersMixin 728L; write_candles() 204L. pyrightconfig exclude+linter scope criteria added 2026-03-10 — not yet re-audited against new criteria. RE-AUDITED 2026-03-11 — WARN. quality-gates.sh now present in all repos (all stubs ≤26 lines, zero violations). OrchestrationWorkersMixin reduced to 17L (was 728L). write_candles() reduced to 167L (was 204L — still above 200L limit in output_writer_service.py:263). 12 repos missing pyrightconfig.json "exclude": ["tests"] (unified-defi-execution-interface, unified-sports-execution-interface, unified-ml-interface, system-integration-tests, features-volatility-service, unified-feature-calculator-library, execution-algo-library, risk-and-exposure-service, unified-position-interface, ml-training-service,
    ml-inference-service, alerting-service). Zero os.getenv violations in non-bootstrap source.'}
- {id: audit-security, content: 'Audit Section 3 — Security (items 10.1–10.19): no hardcoded API keys; all secrets via get_secret_client(); no verify=False in HTTP clients; all API services authenticated; no mock auth in prod; AUTH_FAILURE + SECRET_ACCESSED + CONFIG_CHANGED events logged.', status: completed, note: 'RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 3, WARN). RE-AUDITED 2026-03-10T02:31:37Z — WARN. execution-service/auth.py:83 + alerting-service/auth.py:37,40 missing AUTH_FAILURE on 401 (market-data-api/execution-results-api previously fixed). RE-AUDITED 2026-03-11 — PASS. AUTH_FAILURE now present at execution-service/auth.py:47,57,86 and alerting-service/auth.py:40,52. All 401 paths logged.'}
- {id: audit-architecture, content: 'Audit Section 4 — Architecture: tier boundaries respected (no service→service Python imports); no UI embedded in service repo; batch-live symmetry (same engine for both modes); cloud-agnostic I/O (get_storage_client, get_secret_client, CloudEventSink); no GCS* protocol names; deployment-api HTTP boundary (no direct deployment_service imports).', status: completed, note: 'RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 4, WARN). RE-AUDITED 2026-03-10T02:31:37Z — PASS. Bare excepts justified (log+reraise); all tier/cloud boundaries respected.'}
- {id: audit-schema-governance, content: 'Audit Section 5 — Schema Governance: AC contains external venue schemas only; UIC contains internal schemas; no AC/UIC duplication; Layer 0 contract alignment tests pass (test_contract_alignment.py, test_ac_uic_alignment.py); per-service test_schema_robustness.py passes.', status: completed, note: 'RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 5, WARN). RE-AUDITED 2026-03-10T02:31:37Z — FAIL. 13+ float price fields in unified-internal-contracts/features.py:122,238-240,267 and domain/features_liquidity/__init__.py:77,100-103,212,218. RE-AUDITED 2026-03-11 — PASS. All price/monetary fields in features.py now use Decimal (bid_ask_spread, open_interest, spot_price, front_month_price, price_ratio, price_ratio_ma_20, price_ratio_std_20). Remaining float fields annotated with # financial-ratio: float-ok or # volatility-pct: float-ok or # time-based: float-ok — all appropriate use of float.'}
- {id: audit-observability, content: 'Audit Section 6 — Observability: /health + /readiness endpoints on all API services; correlation_id propagated end-to-end; Prometheus metrics exported; Grafana dashboards present (trading-overview.json, system-health.json); pre-crash checkpoint at 85% memory; compliance reporting wired (MiFID/FCA); 12.16-12.20: timestamp validation, CloudEventSink naming, test_event_logging.py, memory watchdog, correlation_id propagation.', status: completed, note: 'RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 6, WARN). RE-AUDITED 2026-03-10T02:31:37Z — PASS. All 9 criteria met; 46 repos have test_event_logging.py; MiFID/FCA compliance events wired.'}
- {id: audit-deployment, content: 'Audit Section 7 — Deployment: deployment checklist phases 1–7 complete per service; runtime-topology.yaml accurate; Layer 2 infra verify passes (/infra/health); Layer 3a smoke (<5 min) passes; Layer 3b full E2E (15–30 min) passes; v1.0.0 tagged on main.', status: completed, note: 'RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 7, N/A — requires live infra). RE-AUDITED 2026-03-10T02:31:37Z — PASS. Unit markers now registered in strategy-service + ml-inference-service pyproject.toml.'}
- {id: audit-technical-debt, content: 'Audit Section 8 — Technical Debt: QUALITY_GATE_BYPASS_AUDIT.md present + up to date in all repos; zero undocumented suppressions; type: ignore count <10 total documented exceptions; no old import names as aliases; no try/except ImportError fallbacks. .basedpyright-baseline.json policy: FAIL if present without QUALITY_GATE_BYPASS_AUDIT.md entry; WARN (counts as violation) even if documented — target state is zero baseline files in all repos. Run: find . -maxdepth 2 -name .basedpyright-baseline.json to enumerate; any hit is a WARN minimum regardless of documentation status.', status: in_progress, note: 'RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md (Section 8, WARN). RE-AUDITED 2026-03-10T02:31:37Z — PASS for importError/suppressions. RE-OPENED 2026-03-09: 3 repos have undocumented .basedpyright-baseline.json files (market-data-processing-service 8722L, ml-training-service 4090L, features-sports-service 1580L) — these are undocumented suppressions;
    QG base scripts now enforce FAIL if undocumented, WARN if documented.'}
- {id: audit-cross-repo-alignment, content: 'Audit Section 9 — Cross-Repo Alignment: all plans in INDEX.md have corresponding implementation; codex docs reflect current decisions; cursor rules consistent with codex; workspace-manifest.json matches runtime-topology.yaml; no orphan repos (4 API services previously missing from manifest — verify fixed).', status: completed, note: 'RESOLVED 2026-03-09 — Section 9 verified from codebase. INDEX.md references 56 plan entries; 16 active .md files present. All 4 API services confirmed in manifest (execution-results-api, market-data-api, client-reporting-api, deployment-api). 59 total repos in manifest. .cursor/rules/ and unified-trading-pm/cursor-rules/ both have 15 rules (in sync). runtime-topology.yaml present and structured (version, deployment_profiles, clusters, service_flows keys confirmed). PASS. RE-AUDITED 2026-03-10T02:31:37Z — FAIL (now fixed). quality_gates_dry_refactor + ui_auth_oauth_pkce plans were missing from SSOT-INDEX; 2 phantom
    entries (foundational_repos_remediation, schema_governance_full_audit) removed. SSOT-INDEX now current. PASS after fix. RE-AUDITED 2026-03-11 — WARN. 65 repos in manifest. 35 active .md files; 3 unregistered in SSOT-INDEX: audit_remediation_2026_03_11.md, position_precision_pnl_hardening_2026_03_11.md, uei_pending_event_additions.md. These are new plans from 2026-03-11 session; must be registered.'}
- {id: audit-output, content: 'Produce final audit output: per-criterion PASS/WARN/FAIL/N/A table; overall grade (PASS=0 FAILs, CONDITIONAL=≥1 WARNs + 0 FAILs, FAIL=≥1 FAILs); top 10 blocking findings with file:line references; technical debt trajectory vs previous audit.', status: completed, note: 'RESOLVED 2026-03-08 — see SYSTEM_AUDIT_REPORT_2026_03_08.md. Overall grade: CONDITIONAL PASS. RE-AUDITED 2026-03-10T02:31:37Z — see SYSTEM_AUDIT_REPORT_2026_03_09.md. Overall grade: FAIL (4 FAILs, 5 WARNs). RE-AUDITED 2026-03-11 — Overall grade: CONDITIONAL PASS (0 FAILs, 3 WARNs). Resolved: §2 QG presence/size, §3 AUTH_FAILURE, §5 float→Decimal schema, §11 coverage recalibration (65 repos, 0 errors). Remaining WARNs: §2 write_candles 167L (target <200L — borderline), §2 pyrightconfig missing tests exclusion in 12 repos, §9 3 new plans unregistered in SSOT-INDEX. Coverage floors met: all 14 key repos PASS against calibrated MIN_COVERAGE (execution-service=70%, features-multi-timeframe=97%, instruments=74%,
    trading-agent=95%, pnl-attribution=90%, unified-market-interface=85%, ml-training=87%, features-onchain=71%, market-data-processing=78%, market-tick-data=73%, features-commodity=99%, execution-results-api=80%, unified-trading-library=81%, features-cross-instrument=91%). Logic bugs fixed: LONG/SHORT aliases in instruction_validator.py, int64 threshold 1e6→1e10 in trade_converter.py. Low-coverage outliers with no plan: batch-live-reconciliation-service=13%, ibkr-gateway-infra=52%, elysium-defi-system=45% (ibkr tracked by ibkr_gateway_rollout.md; others need coverage plans).'}
- {id: audit-config-injection, content: 'Audit Section on dynamic config injection compliance — GCP_PROJECT_ID banned, DomainConfigReloader used for domain entity hot-reload, get_config_store() factory only, no hardcoded subscription lists, CONFIG_CHANGED events logged.', status: completed, note: 'RESOLVED 2026-03-09 — Verified via cross-reference of Sections 13.11-13.15, 14.3.8 in audit report. All YES in audit table. config_dynamic_injection.md archived 2026-03-08 — all todos done.'}
- {id: audit-integration-test-coverage, content: '"Audit Section 10 — Integration Test Coverage: Every repo with private deps (L2+) must have tests/integration/ with Layer 1.5 mock integration tests for all dep boundaries. External-facing interfaces (unified-market-interface, unified-trade-execution-interface, unified-reference-data-interface, unified-position-interface, unified-sports-execution-interface, unified-defi-execution-interface, unified-cloud-interface) must have VCR-recorded integration tests against real API calls validating schemas from unified-api-contracts. Score PASS if: (a) tests/integration/ exists with >=1 test per private dep boundary, (b) interface repos have vcr cassettes in unified_api_contracts_external/<venue>/mocks/, (c) all integration tests run with mocked deps (no live cloud in quickmerge)."

    ', status: completed, note: 'RESOLVED 2026-03-09 — Section 10 verified. All 7 required repos have tests/integration/: execution-service (21 files), strategy-service (5), risk-and-exposure-service (3), ml-inference-service (4), unified-market-interface (4), unified-trade-execution-interface (6), unified-reference-data-interface (5). PASS. RE-AUDITED 2026-03-10T02:31:37Z — PASS. execution-service grew to 38 integration test files; 46 VCR cassette dirs confirmed.'}
- {id: audit-coverage-regression-prevention, content: '"Audit Section 11 — Coverage Regression Prevention: Each repo''s MIN_COVERAGE in scripts/quality-gates.sh must be set to (actual measured coverage - 1%), NOT the default 70%. pyproject.toml [tool.coverage.report] fail_under must match MIN_COVERAGE. ALSO CHECK: --cov-fail-under=$MIN_COVERAGE is actually passed to the pytest invocation inside quality-gates.sh / base-service.sh — FAIL if MIN_COVERAGE is set but not wired into pytest (value declared but never enforced). Score PASS if: MIN_COVERAGE != 70 for all repos with >70% actual coverage; fail_under in pyproject.toml matches MIN_COVERAGE; --cov-fail-under wired in QG execution."

    ', status: completed, note: 'RESOLVED 2026-03-09 — Section 11 verified. MIN_COVERAGE calibrated per-repo: execution-service=55, instruments-service=51, alerting-service=78 (all non-default 70, matching test-coverage-targets.mdc guidance). PASS (all sampled repos show calibrated values, not default 70). RE-AUDITED 2026-03-10T02:31:37Z — PASS. 8/8 key repos MIN_COVERAGE ↔ fail_under aligned.'}
- {id: coverage-recalibrate-post-remediation, content: '"Run `python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py --recalibrate` once ALL repos in the coverage audit exit 0 (no FAILs). Blocked by: (1) execution-service broken imports (dump_to_csv, get_unified_monitor, nautilus_trader) cap coverage at 32%; (2) out-of-scope repos needing separate remediation campaigns (strategy-service, UDC, ml-training-api, trading-analytics-api, UIs). Do NOT run --recalibrate with stale coverage.xml — it will corrupt thresholds. Re-run each repo''s tests first: cd <repo> && .venv/bin/pytest tests/ --cov=<package> --cov-report=xml before recalibrating."

    ', status: completed, note: 'Added 2026-03-10. Follow-on from coverage_remediation_2026_03_10 plan (archived). 14 of 14 Section A repos above floor. COMPLETED 2026-03-11: 65 repos processed, 0 errors. MIN_COVERAGE updated per repo to actual-1%. Below-floor repos (batch-live-reconciliation=13%, ibkr-gateway=52%, elysium-defi-system=45%) retained floor=70 pending campaigns.'}
- {id: audit-cloud-agnostic-api, content: '"Audit Section 12 — Cloud-Agnostic API Compliance: Only unified-cloud-interface may contain cloud-provider-specific code (GCS/S3/AWS/GCP SDK calls). All other repos must use UCI abstractions. Banned patterns outside UCI: gcs_bucket (use storage_bucket), bigquery_dataset (use analytics_dataset), upload_to_gcs (use upload_artifact via UCI StorageClient), os.getenv (use UnifiedCloudConfig), google-cloud-* imports outside UCI, boto3 imports outside UCI. Score FAIL if any banned pattern found in non-UCI source."

    ', status: completed, note: 'RESOLVED 2026-03-09 — Section 12 verified. Zero violations found: gcs_bucket outside UCI = 0 matches, google.cloud imports outside UCI = 0 matches, boto3 outside deployment-service/backends = 0 matches. PASS. RE-AUDITED 2026-03-10T02:31:37Z — PASS. Zero violations maintained.'}
- {id: config-injection-compliance, content: 'Cross-reference config injection compliance checks (Sections 13.11-13.15, 14.3.8, 2.13, 3.15-3.16, 12.16-12.20, 17.x, 22.11) against citadel_audit_remediation stream checks. Verify: GCP_PROJECT_ID banned, DomainConfigReloader used for domain entity hot-reload, get_config_store() factory only, no hardcoded subscription lists, CONFIG_CHANGED events logged. (Migrated from config_dynamic_injection.md p4-audit-integration.)', status: completed, note: 'RE-AUDITED 2026-03-09 — WARN. GCP_PROJECT_ID re-exported as module-level constant in deployment-api/settings.py:21 (value from UnifiedCloudConfig, technically compliant but grep-visible). Bootstrap phase labels inconsistent in UCI factory.py. All other CI criteria PASS. See SYSTEM_AUDIT_REPORT_2026_03_09.md Config Injection section.'}
- {id: audit-no-stubs, content: '"Audit Section 13 — No Unimplemented Stubs: scan all production Python source (exclude tests/, archive/, .venv*, node_modules/, *.egg-info/) for: (a) `raise NotImplementedError` in non-abstract concrete classes; (b) `# TODO` / `# FIXME` / `# HACK` / `# STUB` / `# placeholder` comments; (c) `pass` as sole body of a non-Protocol class or function; (d) `...` (Ellipsis) as function body outside Protocol/ABC definitions. Score PASS if count is zero. Score WARN if count ≤ 10 with each item tracked in stub_completion_interfaces_and_infra.md or another active plan. Score FAIL if any stub exists with no owning plan todo. Use: rg ''raise NotImplementedError|# TODO|# FIXME|# HACK|# STUB|# placeholder'' --type py --glob ''!.venv*'' --glob ''!**/tests/**'' --glob ''!**/archive/**'' per repo."

    ', status: completed, note: 'RESOLVED 2026-03-09 — WARN. 187 raise NotImplementedError (99% tracked by stub_completion_interfaces_and_infra + phase3 + phase2 + ibkr_gateway plans). 59 TODO/FIXME with ~16 untracked non-blocking items. All pass/... bodies are legitimate Protocol/ABC patterns. See SYSTEM_AUDIT_REPORT_2026_03_09.md Section 13. RE-AUDITED 2026-03-10T02:31:37Z — WARN. 14 untracked items (11 TODOs + 3 UMI DeFi stubs); all in stub_completion plan.'}
- {id: audit-orphaned-code, content: '"Audit Section 14 — No Orphaned Code: detect classes, functions, and schemas defined in a repo but never imported or called by (a) the same repo''s production code, or (b) any downstream repo that declares it as a dependency in workspace-manifest.json. Orphan types: unused Pydantic models / TypedDicts (defined but never instantiated or imported), unused public functions (def-level, not prefixed _), unused Protocol implementations (class C(Protocol) where no function accepts C as a parameter type). Tools: `vulture <src_dir> --min-confidence 80` per repo (installed in workspace venv). Cross-repo: grep for the class/function name across all dependent repos before flagging. Score PASS if zero confirmed orphans. Score WARN if ≤ 5 with each item explained in a code comment or plan. Score FAIL if any confirmed orphan has no explanation. Exclude: __all__ re-exports, Protocol stub bodies, abstract base methods, test fixtures."

    ', status: completed, note: 'RESOLVED 2026-03-09 — FAIL. 12 confirmed orphans in unified-api-contracts: domain_config.py (4 Protocol classes: DomainConfigProtocol, DataTypeConfigProtocol, ExchangeInstrumentConfigProtocol, MLConfigProtocol), canonical_mappings.py (3 functions: get_venues_for_data_source, get_canonical_venue_for_dataset, get_defi_venue — superseded by UTL equivalents), endpoint_registry.py (4 classes: AccessMode, DataAvailability, ResponseFormat, EndpointSpec), vcr_endpoints.py (VCREndpoint TypedDict). None have # orphan: comments or plan todos. FAIL per scoring (>5 untracked). See SYSTEM_AUDIT_REPORT_2026_03_09.md Section 14. RE-AUDITED 2026-03-10T02:31:37Z — PASS. All 12 prior orphans remediated.'}
- {id: implement-audit-agent-core, content: 'Implement AuditResolutionAgent in system-integration-tests repo at system_integration_tests/audit/agent.py. The agent is a Python class that: (a) reads unified-trading-pm/workspace-manifest.json to discover all registered repos + their arch_tier and dependencies; (b) for each repo, runs each audit section from the canonical audit prompt (this file) as a programmatic check — not a subprocess call to a human-readable script, but typed Python functions that return AuditResult(section, repo, status, evidence); (c) aggregates results into a structured AuditReport with per-section PASS/WARN/FAIL/N/A scores and file:line evidence; (d) writes the report to system-integration-tests/reports/audit_<date>.json and a human-readable .md summary. No os.getenv — config via UnifiedCloudConfig. No Any types. No try/except ImportError. Full basedpyright strict.', status: pending}
- {id: implement-repo-discovery-and-cloning, content: 'Add repo discovery + shallow clone logic to system_integration_tests/audit/repo_manager.py. In CI (Cloud Build / CodeBuild), system-integration-tests is expected to clone all sibling repos during audit runs. Implementation: (a) read workspace-manifest.json repos[] array; (b) for each repo, check if a sibling directory exists at ../repo-name relative to the SIT workspace root — if yes, use it directly; if no (CI cold run), shallow-clone from the repo''s git_url with depth=1 into a temp directory; (c) return a RepoContext(name, local_path, arch_tier, deps) TypedDict for each repo. This enables the agent to run audit checks against actual source files without requiring a pre-configured monorepo checkout. Add cloudbuild.yaml step to pre-clone all repos before invoking the audit agent.', status: pending}
- {id: implement-audit-section-checks, content: 'Implement one Python function per audit section in system_integration_tests/audit/checks/. Each check module corresponds to a section in this audit prompt: check_workspace_governance.py (Section 1), check_code_quality.py (Section 2 — file/function/class size limits, ruff config present, basedpyright config present, pyrightconfig excludes tests/, linter globs exclude tests/, QG script is stub not full-body, zero os.getenv in prod source), check_security.py (Section 3 — no hardcoded keys, get_secret_client usage, AUTH_FAILURE events), check_architecture.py (Section 4 — tier boundary validation via import graph), check_schema_governance.py (Section 5 — AC vs UIC separation), check_observability.py (Section 6 — /health + /readiness endpoints, Prometheus metrics), check_technical_debt.py (Section 8 — QUALITY_GATE_BYPASS_AUDIT.md present, zero undocumented type:ignore), check_coverage_enforcement.py (Section 11 — MIN_COVERAGE calibrated AND --cov-fail-under
    wired in QG), check_stubs.py (Section 13 — rg NotImplementedError/TODO/FIXME), check_orphaned_code.py (Section 14 — vulture + cross-repo grep), check_ci_pipeline_quality.py (Section 15 — uv venv not --system, PATH export, CLOUD_MOCK_MODE), check_ui_npm_governance.py (Section 16 — package-lock freshness, canonical versions, test presence), check_tooling_ssot.py (Section 17 — QG stubs, base scripts, npm constraints, no orphaned scripts). Each function signature: def check_<section>(repo: RepoContext) -> list[AuditResult]. All checks are static analysis only — no network calls, no live infra required.', status: pending}
- {id: implement-regression-smoke-trigger, content: 'Wire the audit agent to trigger smoke + e2e tests when a regression is detected. A "regression" is defined as: any section that previously scored PASS or WARN now scores FAIL, OR any section that previously scored PASS now scores WARN. Implementation: (a) the agent loads the previous audit report from reports/audit_<prev_date>.json for comparison; (b) if regressions detected, it writes a regression_report.json with affected repos + sections; (c) a pytest fixture in tests/audit/conftest.py reads regression_report.json and marks the smoke + e2e test suites as required (not skipped); (d) CI (cloudbuild.yaml / buildspec.aws.yaml) runs audit agent first, then conditionally invokes `pytest tests/smoke/ tests/e2e/` only when regression_report.json is non-empty. No false negatives: if reports/audit_<prev_date>.json does not exist (first run), treat all non-PASS results as regressions.', status: pending}
- {id: implement-audit-pytest-entry-point, content: 'Add tests/audit/test_audit_agent.py as the pytest entry point for the audit agent. This file is what system-integration-tests CI calls. It: (a) instantiates AuditResolutionAgent with the workspace root path from a conftest fixture; (b) calls agent.run_full_audit() which returns AuditReport; (c) asserts report.overall_grade != "FAIL" — the test fails if any section regresses to FAIL; (d) writes the report to reports/ for the regression comparison in the next run; (e) prints the PASS/WARN/FAIL/N/A table to stdout (visible in CI logs). Add a pytest marker "audit" so the test can be run in isolation: `pytest tests/audit/ -m audit`. Register the marker in pyproject.toml [tool.pytest.ini_options] markers.', status: pending}
- {id: wire-audit-into-ci, content: 'Update system-integration-tests/cloudbuild.yaml and system-integration-tests/buildspec.aws.yaml to run the audit agent as a pre-step before Layer 3a smoke and Layer 3b e2e. CI sequence: (1) Shallow-clone all sibling repos (repo_manager.py); (2) Run audit agent (pytest tests/audit/ -m audit --tb=short); (3) If audit passes — run Layer 3a smoke (pytest tests/smoke/ --timeout=300); (4) If smoke passes AND e2e is enabled — run Layer 3b e2e (pytest tests/e2e/ --timeout=1800); (5) Upload reports/audit_<date>.json to artifact store (via UCI StorageClient, not direct GCS). The audit step is non-blocking for WARN results — only FAIL results block the pipeline. Document this in system-integration-tests/README.md.', status: pending}
- {id: audit-ci-pipeline-quality, content: 'Audit Section 15 — CI/CD Pipeline Quality: for each Python repo, inspect .github/workflows/quality-gates.yml (or equivalent). Check: (a) install step uses "uv venv .venv && uv pip install --python .venv/bin/python" — FAIL if "uv pip install --system" or bare "pip install" used (env mismatch with local QG); (b) run step exports "PATH=$(pwd)/.venv/bin:$PATH" before calling bash scripts/quality-gates.sh — FAIL if PATH not set and script relies on activated venv; (c) CLOUD_MOCK_MODE=true and GCP_PROJECT_ID set in env — FAIL if absent (live cloud calls in CI); (d) quality-gates.sh called with --no-fix — FAIL if called without it (auto-fix in CI hides violations). For UI repos, check: (e) npm ci used instead of npm install — WARN if npm install used; (f) quality-gates.sh or equivalent called in CI. Score FAIL if any Python repo has --system install or missing PATH export. Score WARN if any UI repo has no CI quality gate step.', status: pending, note: Added
    2026-03-10 — not yet audited. Blind spot that allowed --system CI venv bug to pass undetected.}
- {id: audit-ui-npm-governance, content: 'Audit Section 16 — UI/npm Governance: for each pure UI repo (package.json present, no pyproject.toml). Check: (a) package-lock.json present and newer than or same age as package.json — FAIL if package.json newer (stale install, detected by run-version-alignment.sh step 0.6); (b) devDependencies match workspace-npm-constraints.json canonical versions for: typescript, vite/@vitejs/plugin-react, vitest, @vitest/coverage-v8, @testing-library/react, eslint — FAIL if any version diverges without a documented exception; (c) at least 1 test file exists in src/ or tests/ — FAIL if testing_level=none in workspace-manifest.json (all UI repos must have tests); (d) quality-gates.sh is a thin stub calling base-ui.sh — FAIL if full-body or absent; (e) CI workflow runs quality-gates.sh. Audit command: bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --ui-only --strict; python3 unified-trading-pm/scripts/propagation/rollout-npm-versions.py.
    Score FAIL if any UI repo has stale package-lock or testing_level=none.', status: pending, note: 'Added 2026-03-10. M6 UPDATE (2026-03-11): ui_design_system_upgrade_2026_03_10 (DONE) added vitest

    to all 11 UI repos. Re-run Section 16 audit against current state — expected result: all 11 UI repos

    now pass testing_level check (vitest present). 3 UI repos (trading-analytics-ui,

    execution-analytics-ui, batch-audit-ui) were flagged as FAIL §16 in the 2026-03-11 full audit;

    verify these are resolved post ui_design_system_upgrade.

    '}
- {id: audit-tooling-ssot-quality, content: 'Audit Section 17 — Tooling SSOT & DRY Quality: audit the quality of workspace tooling scripts themselves (not application code). Check: (a) every Python repo''s scripts/quality-gates.sh is a stub (<50 lines) delegating to unified-trading-pm/scripts/quality-gates-base/base-service.sh or base-library.sh — FAIL if any repo has a full-body QG script (duplication); (b) base-service.sh, base-library.sh, base-ui.sh exist in unified-trading-pm/scripts/quality-gates-base/ and are the single SSOT for all QG logic — FAIL if QG logic is duplicated elsewhere; (c) run-version-alignment.sh contains steps 0.5 (symlinks), 0.6 (UI npm drift), 0.7 (npm version constraints), 1-4 (Python alignment) — FAIL if any step missing; (d) workspace-npm-constraints.json exists and is enforced by rollout-npm-versions.py — FAIL if npm versions ungoverned; (e) no orphaned scripts in unified-trading-pm/scripts/ (scripts that are never called by QG, quickmerge, version-alignment,
    or CI) — WARN per orphaned script. Audit command: wc -l */scripts/quality-gates.sh | sort -rn | head -20 (any >50 lines is a violation). Score FAIL if any full-body QG script found.', status: pending, note: Added 2026-03-10 — not yet audited. Blind spot that allowed 25-30K lines of duplicated QG logic to persist.}
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
- `WARN` — ≤ 10 results total; each item has an open todo in an active plan (cite plan + todo ID)
- `FAIL` — any result with no owning active plan todo, OR total count > 10

**Reference plan:** `stub_completion_interfaces_and_infra.md` (Plan #32) — covers all currently-known interface and
infrastructure stubs. Any new stub found must be added to that plan or a relevant existing plan before the audit can
score WARN.

---

## Section 14 — No Orphaned Code

**Goal:** Every public class, function, and schema is either used within the same repo or imported by a downstream repo
that declares this one as a dependency in `workspace-manifest.json`.

**Orphan categories:**

| Category                                            | Tool                                                                |
| --------------------------------------------------- | ------------------------------------------------------------------- |
| Unused Pydantic models / TypedDicts                 | `vulture <src_dir> --min-confidence 80`                             |
| Unused public functions (`def foo`, not `def _foo`) | `vulture` + cross-repo `rg`                                         |
| Unused Protocol implementations                     | class `C(Protocol)` with no consumer accepting `C` as type          |
| Unused UAC/UIC schemas                              | schema class never imported by downstream service or interface repo |
| Unused constants / module-level variables           | `vulture` + cross-repo `rg`                                         |

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
- `WARN` — ≤ 5 confirmed orphans; each has a `# orphan: <reason>` comment OR an open plan todo
- `FAIL` — any confirmed orphan with no comment and no plan todo, OR total > 5

**Remediation:** Delete confirmed orphans immediately. If uncertain (consumer may be unregistered), add
`# orphan: kept because <reason>` comment and open a plan todo to track removal. Never silence with `# type: ignore`.

---

---

## Section 15 — CI/CD Pipeline Quality

**Goal:** Every repo's CI workflow must run QG in the same environment as local execution. Env mismatch is a silent
failure mode — tests pass locally but CI runs in a different Python/venv context and produces different results.

**Audit commands:**

```bash
# Check for --system installs (forbidden)
grep -r "uv pip install --system\|pip install --system\|pip install -r" \
  */. github/workflows/ --include="*.yml" -l

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

**Goal:** All 11+ UI repos are governed by the same version constraints and test standards as Python repos. Previously
there was no audit coverage for UI repos beyond manifest registration.

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

# Find orphaned scripts (not referenced by QG, quickmerge, version-alignment, or CI)
# Manual: list scripts/ and cross-check against callers
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

**Extension to Section 2 — pyrightconfig scope and linter glob:**

These checks were added to Section 2 criteria but are listed here for clarity:

```bash
# Check pyrightconfig.json excludes tests/ in all Python repos
for repo in */; do
  cfg="$repo/pyrightconfig.json"
  [ -f "$cfg" ] && python3 -c "
import json, sys
c = json.load(open('$cfg'))
ex = c.get('exclude', [])
if 'tests' not in ex and 'tests/' not in ex:
    print('MISSING exclude tests:', '$cfg')
" 2>/dev/null
done

# Check base-service.sh linter checks use --glob '!tests/**'
grep -c '"!tests/\*\*"' unified-trading-pm/scripts/quality-gates-base/base-service.sh
# Must be ≥ 6 (one per codex rg check: print, os.getenv, datetime, except, requests, asyncio.run)
```

**Scoring:**

- `PASS` — all Python repos have `"exclude": ["tests"]` in pyrightconfig; base-service.sh has `!tests/**` on all codex
  checks; all QG scripts are stubs; all base scripts present; npm constraints enforced; no orphaned scripts
- `WARN` — 1–3 repos missing `pyrightconfig.json` test exclusion; or 1 orphaned script with explanation
- `FAIL` — any full-body QG script (>50 lines) in any repo; OR base scripts missing from PM; OR any codex check linting
  tests/; OR npm constraints file absent

---

**Key SSOT references for auditors:**

- Repo registry & DAG: `unified-trading-pm/workspace-manifest.json`
- **Deployment configs (canonical):** `deployment-service/configs/` — checklist._.yaml, venues.yaml,
  RUNTIME_TOPOLOGY_DECISIONS.md, data-catalogue._.yaml, per-service PROTOCOL\_\* env files.
- **Runtime topology (canonical SSOT):** `unified-trading-pm/configs/runtime-topology.yaml` — owned by PM;
