---
orphan_candidate: true
orphan_reason:
  "Pure agent dispatch prompt for ml_pipeline_ui_integration plan. Not a tracked work plan; companion runbook only."
reconciliation_date: 2026-04-25
---

> **ORPHAN CANDIDATE 2026-04-25.** Scope appears unconnected to the live system. Reason: Pure agent dispatch prompt for
> ml_pipeline_ui_integration plan. Not a tracked work plan; companion runbook only. See
> `_reconciliation_evidence_map_2026_04_25.md` for the integration check.

# Agent Prompt: ML Pipeline UI E2E Browser Validation

Copy this prompt to a Claude Code session with MCP browser access.

---

## Task

Validate that all ML UI pages render correctly with the API running in Tier 1 (mock mode). This is the Phase 7 E2E
validation for the ML Pipeline → UI Integration plan.

## Prerequisites

Before starting, run these commands in the workspace root (`/Users/ikennaigboaka/Code/unified-trading-system-repos`):

```bash
# Start the API + UI in Tier 1 mode
cd unified-trading-system-ui
bash scripts/dev-tiers.sh --stop    # clean slate
bash scripts/dev-tiers.sh --tier 1  # UI + 3 API gateways (mock mode)
```

Wait ~15 seconds for everything to start, then verify:

```bash
bash scripts/dev-tiers.sh --status
```

All 4 processes should be running:

- `ui` on port 3000 (Next.js dev)
- `unified-trading-api` on port 8030
- `client-reporting-api` on port 8014
- `auth-api` on port 8018/8019

## Pages to Validate

Navigate to each page and verify it renders without errors. Check the browser console for any API 404s or failures.

### 1. ML Overview Page

**URL:** `http://localhost:3000/services/research/ml` **Expected:** Dashboard with pipeline KPIs (models in production,
training stats, feature freshness) and active alerts. **Hooks used:** `useMLPipelineStatus`, `useMLAlerts` **API
endpoints:** `GET /api/ml/pipeline/status`, `GET /api/ml/alerts`

### 2. Training Runs Page

**URL:** `http://localhost:3000/services/research/ml/training` **Expected:** Table/list of training runs with status,
category, instrument, metrics. A "Create Training Run" button. **Hooks used:** `useUnifiedTrainingRuns`,
`useCreateUnifiedTrainingRun` **API endpoints:** `GET /api/ml/training-runs`, `POST /api/ml/training-jobs`

### 3. Training Run Detail (click any run)

**Expected:** Detailed view with accuracy, precision, recall, F1, SHAP feature importance, hyperparameters, walk-forward
fold results. **Hooks used:** `useUnifiedTrainingRunDetail`, `useRunAnalysisBundle` **API endpoints:**
`GET /api/ml/training-runs/{id}`, `GET /api/ml/analysis/runs/{id}`

### 4. Model Registry

**URL:** `http://localhost:3000/services/research/ml/registry` **Expected:** Table of registered models with family,
version, category, status (staging/production), metrics. Promote button. **Hooks used:** `useRegistryModels`,
`useModelVersions`, `usePromoteModel` **API endpoints:** `GET /api/ml/registry/models`, `GET /api/ml/versions`,
`POST /api/ml/models/{id}/promote`

### 5. Grid Config Editor

**Expected:** CRUD interface for ML training grid configurations. Feature group selector per category. **Hooks used:**
`useMLGridConfigs`, `useFeatureGroups`, `useCreateMLGridConfig` **API endpoints:** `GET /api/ml/grid-configs`,
`GET /api/ml/feature-groups?category=CEFI`

### 6. ML Monitoring

**Expected:** Model drift scores, prediction distribution, accuracy over time. **Hooks used:** `useMLMonitoring` **API
endpoint:** `GET /api/ml/monitoring`

### 7. ML Governance

**Expected:** Approval status, audit trail for model deployments. **Hooks used:** `useMLGovernance` **API endpoint:**
`GET /api/ml/governance`

### 8. ML Config

**Expected:** Current ML pipeline configuration (feature sets, training schedule, drift thresholds). **Hooks used:**
`useMLConfig` **API endpoint:** `GET /api/ml/config`

### 9. Validation Results

**URL:** `http://localhost:3000/services/research/signals` **Expected:** Walk-forward validation results, model
comparison. **Hooks used:** `useValidationResults` **API endpoint:** `GET /api/ml/validation-results`

## Validation Checklist

For each page:

- [ ] Page loads without blank screen
- [ ] Data renders (not just "Loading..." spinner forever)
- [ ] No 404 errors in browser console for `/api/ml/*` endpoints
- [ ] No JavaScript errors in console
- [ ] Mock data shows realistic values (not empty objects)

## After Validation

1. Take a screenshot of each page that renders correctly
2. Note any pages that fail to render or show errors
3. Stop the dev server: `cd unified-trading-system-ui && bash scripts/dev-tiers.sh --stop`

## What to Report

Report back with:

- Which pages rendered successfully
- Which pages had errors (and what the error was)
- Any missing API endpoints (404s in browser console)
- Screenshots if possible

## Tier Mode Context

In Tier 1 mode:

- `CLOUD_MOCK_MODE=true` → API uses MockStateStore + hardcoded fallbacks
- `DISABLE_AUTH=true` → No auth required
- `NEXT_PUBLIC_MOCK_API=true` → UI uses in-browser mock data for non-ML pages
- ML endpoints return mock data from the API's static fallback responses
