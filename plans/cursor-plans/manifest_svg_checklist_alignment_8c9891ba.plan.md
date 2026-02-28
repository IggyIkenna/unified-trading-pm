---
name: Manifest SVG Checklist Alignment
overview: Fix manifest topological levels, align all SVGs, create checklist templates for all component types, check ML inference BigQuery gap, check Cloud Run scale-to-zero, update SSOT index, cursor rules, codex docs, and consolidated plan.
todos:
  - id: fix-manifest-levels
    content: "Fix topologicalOrder levels in workspace-manifest.json: UDC to L3, deployment-engine/api to L5"
    status: completed
  - id: fix-manifest-svg
    content: Rebuild WORKSPACE_MANIFEST_DAG.svg to match corrected manifest levels
    status: completed
  - id: create-checklist-templates
    content: "Create checklist templates for all component types: service, api-service, ui, library"
    status: completed
  - id: check-ml-bigquery-gap
    content: Verify ML inference BigQuery gap is in plan, add Cloud Run scale-to-zero deployment_mode to runtime-topology.yaml
    status: completed
  - id: update-ssot-docs-plan
    content: Update SSOT index, cursor rules, codex docs, and consolidated_remaining_work.plan.md with all changes
    status: completed
isProject: false
---

# Manifest, SVG, Checklist, and Plan Alignment

## Fixes Required

### 1. Manifest Topological Level Corrections

Fix [workspace-manifest.json](unified-trading-pm/workspace-manifest.json) `topologicalOrder`:

- Move `unified-domain-client` from Level 2 to Level 3 (matches arch_tier=3)
- Move `deployment-engine` from Level 6 to Level 5 (matches arch_tier=5)
- Move `deployment-api` from Level 7 to Level 5 (matches arch_tier=5)
- Remove ml-training-service from ml-inference-service dependencies in pyproject.toml (DAG violation V4 -- they share unified-ml-interface)

### 2. WORKSPACE_MANIFEST_DAG.svg Alignment

Fix [WORKSPACE_MANIFEST_DAG.svg](unified-trading-codex/04-architecture/WORKSPACE_MANIFEST_DAG.svg):

- Move UDC box from Level 2 row to Level 3 row
- Move deployment-engine and deployment-api from Levels 6/7 to Level 5
- Verify all repos shown match manifest exactly

### 3. Checklist Templates for All Component Types

Create or update checklist templates in [unified-trading-deployment-v3/configs/](unified-trading-deployment-v3/configs/):

- `checklist.template.service.yaml` -- for services (17 repos) -- based on existing 57-item template
- `checklist.template.api-service.yaml` -- for API services (4 repos) -- health probes, SSE/REST endpoints, auth
- `checklist.template.ui.yaml` -- for UIs (11 repos) -- build, env config, API wiring, auth gating
- `checklist.template.library.yaml` -- for libraries (17 repos) -- exports, type safety, tier compliance, tests

### 4. ML Inference BigQuery Gap

Research confirmed: ml-inference-service reads features from BigQuery (polling), not PubSub. Per architectural decisions, live features should come via PubSub. This is a known gap (documented in RUNTIME_TOPOLOGY_DECISIONS.md section 5). Ensure the plan has a todo for this.

### 5. Cloud Run Scale-to-Zero

Check if `runtime-topology.yaml` supports scale-to-zero for infrequent services. Add a `deployment_mode` field:

- `always_on`: services that must be running continuously (MTDH, MDPS, execution, strategy, PBM)
- `scale_to_zero`: services that can cold-start on demand (manual orders, reporting, batch jobs)
- Cold start ~1-2s is acceptable for manual/infrequent operations

### 6. SSOT Index Update

Update [00-SSOT-INDEX.md](unified-trading-codex/00-SSOT-INDEX.md) with:

- Checklist templates per component type
- Cloud Run deployment modes
- Component type naming convention

### 7. Consolidated Plan Update

Update [consolidated_remaining_work.plan.md](unified-trading-pm/plans/cursor-plans/consolidated_remaining_work.plan.md) with all new todos in logical dependency order.
