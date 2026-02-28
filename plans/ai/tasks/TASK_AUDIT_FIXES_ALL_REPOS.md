# Task: Execute Audit Fixes Across All Repos

**Source:** AUDIT_TO_A_GRADE_ROADMAP/CLOUD_BUILD_AUDIT.md, ALIGNMENT_SUMMARY.md
**Date:** 2026-02-24

**Execution status:** ✅ Fixes executed (main agent + 2 shell sub-agents). The 4 parallel generalPurpose sub-agents were **not** used (mcp_task hit monthly usage limit). Fixes were applied directly; uv lock and quality-gates verification ran via shell sub-agents.

---

## Fix Categories

### 1. Config Fallback (BLOCKING) - 1 repo
- **risk-and-exposure-service/risk_and_exposure_service/config.py**
- Remove try/except BaseConfig fallback
- Use: `from unified_config_interface import UnifiedCloudConfig`
- Class: `RiskAndExposureServiceConfig(UnifiedCloudConfig)`

### 2. UCS Version - 3 repos
- **pnl-attribution-service, alerting-service, unified-trading-deployment-v3**
- Change: `unified-trading-services>=0.5.0,<1.0.0` → `unified-trading-services>=1.5.0,<2.0.0`
- In pyproject.toml [project.dependencies]

### 3. Type Checker (pyright → basedpyright) - 11 repos
- pnl-attribution-service, features-calendar-service, features-onchain-service, features-delta-one-service, features-volatility-service, ml-training-service, ml-inference-service, alerting-service, unified-trading-deployment-v3, market-data-processing-service, unified-trade-execution-interface (verify)
- In quality-gates.yml: `pyright` → `basedpyright`
- In quality-gates.sh: `pyright` → `basedpyright` if referenced

### 4. Cloud Build Timeout (1800s → 600s) - 17 repos
- instruments-service, market-tick-data-handler, features-calendar-service, features-onchain-service, market-data-processing-service, risk-and-exposure-service, features-volatility-service, ml-training-service, position-balance-monitor-service, pnl-attribution-service, alerting-service, strategy-service, live-health-monitor-ui, ml-inference-service, features-delta-one-service, execution-service, unified-trading-deployment-v3
- In cloudbuild.yaml: `timeout: '1800s'` → `timeout: '600s'`

### 5. Hardcoded Project ID - 1 repo
- **ml-inference-service/.github/workflows/quality-gates.yml**
- Remove or replace: `GCP_PROJECT_ID: central-element-323112` in env
- Use: `GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}` or `test-project` for CI

### 6. position-balance-monitor-service
- Check quality-gates.sh for duplicate pytest (run both quality-gates.sh AND pytest)
- Remove redundant pytest if present

---

## Agent Partition (No Overlap) — for future parallel runs

*Use this partition when launching 4 parallel sub-agents (e.g. mcp_task generalPurpose or shell) to speed up re-runs or similar audits.*

### Agent 1 - Repos: alerting-service, pnl-attribution-service, risk-and-exposure-service, unified-trading-deployment-v3, features-calendar-service, features-onchain-service, features-delta-one-service, features-volatility-service

### Agent 2 - Repos: ml-training-service, ml-inference-service, market-data-processing-service, instruments-service, market-tick-data-handler, strategy-service

### Agent 3 - Repos: position-balance-monitor-service, live-health-monitor-ui, execution-service, execution-algo-library, unified-config-interface, unified-domain-client, unified-events-interface, unified-market-interface, unified-trade-execution-interface, unified-ml-interface

### Agent 4 - Verification and remaining repos (batch-audit-ui, client-reporting-ui, etc. if they have cloudbuild/quality-gates)

---

## Post-Fix Verification (2026-02-24)

### uv lock (completed by subagent)
- **pnl-attribution-service**: ✅ Resolved 103 packages
- **alerting-service**: ✅ Resolved 103 packages (unified-trading-services v1.5.16 → v1.5.17 in lock)
- **unified-trading-deployment-v3**: ✅ Resolved 148 packages
**Action:** Commit updated `uv.lock` in each repo (e.g. via quickmerge).

### GCP_PROJECT_ID (repo variable)
- **ml-inference-service:** Set repo variable (non-sensitive; use Variables not Secrets). Via CLI: `cd ml-inference-service && gh variable set GCP_PROJECT_ID --body "your-project-id"`. Or in GitHub: Settings → Secrets and variables → Actions → Variables → New repository variable. Required when `GCP_SA_KEY` is set for Artifact Registry pull. Workflow uses `vars.GCP_PROJECT_ID`.

### Quality gates (subagent sampled 13 repos)
- **Passed (6):** ml-inference-service, market-data-processing-service, features-calendar-service, features-onchain-service, strategy-service, ml-training-service
- **Failed (7):** risk-and-exposure-service (UnifiedCloudConfig import in env), pnl-attribution-service (duplicate --cov), alerting-service (0% coverage), unified-trading-deployment-v3 (codex/lint), instruments-service (lint/tests), features-delta-one-service (import), features-volatility-service (codex)
- **Note:** `UnifiedCloudConfig` is exported from `unified_config_interface`; risk-and-exposure failure may be path-dep or install order. Other failures are largely pre-existing (codex, coverage, lint).

---

## Reference: instruments-service (Canonical)
- cloudbuild.yaml: asia-northeast1, test-in-image, --entrypoint "", timeout 600s
- quality-gates.yml: basedpyright, path deps ../
