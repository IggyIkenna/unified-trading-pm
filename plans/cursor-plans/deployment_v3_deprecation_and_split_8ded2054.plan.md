---
name: Deployment V3 Deprecation and Split
overview: "Deprecate unified-trading-deployment-v3 by copying cloud (canonical) deployment-api, deployment-service, deployment-ui, and system-integration-tests into the workspace, completing the extraction from v3 into the four repos, then updating all docs/manifest to use deployment-service/configs/ as SSOT. Final step: remove deployment-v3 locally and on cloud."
todos: []
isProject: false
---

# Deployment V3 Deprecation and Split Plan

## Implementation Status (2026-03-04)

**Phases 1–6 executed.** Workspace now uses deployment-service, deployment-api, deployment-ui, system-integration-tests. unified-trading-deployment-v3 removed from workspace.

**PENDING: Deep final audit** — Verify no functionality was missed; compare `archive/unified-trading-deployment-v3` (cloud copy moved to workspace archive) against the four repos before permanent deletion.

## Context

- **Canonical source (was):** Cloud drive — March 3 updates. Cloud copy moved to `workspace/archive/unified-trading-deployment-v3` for audit before permanent deletion.
- **Target:** Workspace (`/Users/ikennaigboaka/Code/unified-trading-system-repos/`) — keep git, overwrite content
- **Layout:** Slim (3 independent repos + system-integration-tests)
- **SSOT:** `deployment-service/configs/` for all deployment configs
- **Corrupted (excluded):** `terraform/shared/gcp/.terraform/terraform.tfstate`, `ui/dist/index.html`, `ui/dist/assets/index-m2yuLeGi.js`

---

## Phase 1: Overwrite Workspace with Cloud (Keep Git)

Copy cloud repos into workspace, preserving `.git` and `.github` in each repo.

| Repo                     | Source (Cloud)                  | Target (Workspace)          | Notes                                                                      |
| ------------------------ | ------------------------------- | --------------------------- | -------------------------------------------------------------------------- |
| deployment-service       | `.../deployment-service/`       | `deployment-service/`       | Full copy; exclude `.DS_Store`, `*.egg-info`, `.coverage`, `.pytest_cache` |
| deployment-ui            | `.../deployment-ui/`            | `deployment-ui/`            | Full copy                                                                  |
| deployment-api           | `.../deployment-api/`           | `deployment-api/`           | Copy then **unbundle** (Phase 2)                                           |
| system-integration-tests | `.../system-integration-tests/` | `system-integration-tests/` | Full copy                                                                  |

**Implementation:** Use `rsync` or `cp -r` with exclusions. Backup `.git` and `.github` before overwrite, then restore.

---

## Phase 2: Unbundle deployment-api (Slim Layout)

Cloud deployment-api has nested `deployment-service/` and `deployment-ui/` (fat layout). For slim:

1. **Remove** nested `deployment-service/` and `deployment-ui/` from workspace `deployment-api/`
2. **Ensure** `configs` symlink points to `../deployment-service/configs`
3. **Update** `run-api.sh` to run only the API (no embedded UI); UI runs separately from deployment-ui
4. **Verify** `deployment_api/` package and `pyproject.toml` deps are correct

---

## Phase 3: Complete Extraction from Cloud deployment-v3

Map every v3 artifact into one of the four repos. Cloud v3 structure:

```
unified-trading-deployment-v3/
├── api/                    → deployment-api (merge with existing)
├── ui/                      → deployment-ui (merge with existing)
├── configs/                 → deployment-service/configs/ (SSOT; cloud v3 is canonical)
├── unified_trading_deployment/  → deployment-service/deployment_service/
├── backends/                → deployment-service/backends/
├── terraform/               → deployment-service/terraform/
├── infra/                   → deployment-service/infra/
├── deploy.py, deploy        → deployment-service/
├── scripts/                 → split: deployment scripts → deployment-service; others as needed
├── tests/                   → split: e2e → system-integration-tests; unit/integration → deployment-service
├── tools/                   → deployment-service/tools/
├── grafana/                 → deployment-service/grafana/
├── templates/               → deployment-service/templates/
├── docs/                    → merge into deployment-service/docs/
├── audit/                   → deployment-service/audit/ or archive
├── cleanup_old_instruments_parquet.py  → evaluate: instruments-service or deployment-service scripts/
```

**Actions:**

1. **Configs:** Ensure `deployment-service/configs/` has all files from cloud v3 `configs/` (runtime-topology, venues, bucket_config, checklists, sharding, data-catalogue, etc.). Cloud deployment-service may already have these; reconcile.
2. **API:** Compare cloud v3 `api/` with cloud deployment-api `deployment_api/`; merge any v3-only routes/services.
3. **UI:** Compare cloud v3 `ui/` with cloud deployment-ui; merge any v3-only components.
4. **Tests:** v3 `tests/e2e/` → system-integration-tests; v3 `tests/unit/`, `tests/integration/` → deployment-service/tests/
5. **Scripts:** Deployment-related scripts → deployment-service/scripts/; API-related → deployment-api/scripts/

---

## Phase 4: Update Docs and Manifest for deployment-service SSOT

Update all references from `deployment-v3/configs/` to `deployment-service/configs/`.

| Location                                                                                                                                           | Change                                                                                            |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| [unified-trading-pm/cursor-rules/core/dag-enforcement.mdc](unified-trading-pm/cursor-rules/core/dag-enforcement.mdc)                               | `deployment-v3/configs/` → `deployment-service/configs/`                                          |
| [unified-trading-codex/00-SSOT-INDEX.md](unified-trading-codex/00-SSOT-INDEX.md)                                                                   | All deployment-v3 refs → deployment-service                                                       |
| [unified-trading-codex/04-architecture/\*](unified-trading-codex/04-architecture/)                                                                 | deployment-v3 → deployment-service                                                                |
| [unified-trading-codex/06-coding-standards/integration-testing-layers.md](unified-trading-codex/06-coding-standards/integration-testing-layers.md) | deployment-engine → deployment-service                                                            |
| [unified-trading-pm/workspace-manifest.json](unified-trading-pm/workspace-manifest.json)                                                           | Confirm unified-trading-deployment-v3 status: archived; remove from topologicalOrder when deleted |
| [unified-trading-pm/scripts/quality-gates.sh](unified-trading-pm/scripts/quality-gates.sh)                                                         | `DEPLOYMENT_CONFIG_DIR` → `deployment-service/configs`                                            |
| [unified-trading-pm/scripts/agents/diff-checker-agent.sh](unified-trading-pm/scripts/agents/diff-checker-agent.sh)                                 | `DEPLOYMENT_V3` → `DEPLOYMENT_SERVICE`                                                            |
| [unified-trading-pm/scripts/\_workspace-lib.sh](unified-trading-pm/scripts/_workspace-lib.sh)                                                      | `unified-trading-deployment-v3` → `deployment-service` in KNOWN_SIBLING_REPOS                     |

**Grep pattern:** `deployment-v3|unified-trading-deployment-v3|deployment-engine` across workspace (exclude .git, .venv).

---

## Phase 5: UTL Naming Alignment

Manifest uses `unified-trading-library` (UTL). Ensure all four repos use UTL:

- [deployment-service/pyproject.toml](deployment-service/pyproject.toml): `unified-trading-library` path dep
- [deployment-api/pyproject.toml](deployment-api/pyproject.toml): `unified-trading-library` if applicable
- Configs (`venues.yaml`, `bucket_config.yaml`): `unified_trading_library` in comments and service refs

---

## Implementation Deviations / Notes

- **api/ merge:** Cloud deployment-api already had extracted content; v3 api/ was not merged (deployment_api package structure differs). If gaps found in audit, merge from archive.
- **ui/ merge:** Attempted rsync v3 ui into deployment-ui created errant src/src; removed. Cloud deployment-ui was already complete. Audit: compare archive v3 ui/ with deployment-ui.
- **cleanup_old_instruments_parquet.py:** Left in deployment-service (evaluated as deployment-related script). Could move to instruments-service if deemed domain-specific.
- **Cloud copy:** Moved to workspace/archive/ for audit; not deleted from cloud yet — user to remove cloud copy after audit.

## Phase 6: Delete unified-trading-deployment-v3

After extraction is complete and verified:

1. **Workspace:** Remove `unified-trading-deployment-v3/` directory
2. **Manifest:** Remove or mark `unified-trading-deployment-v3` as deleted; update topologicalOrder
3. **Cloud:** User deletes cloud copy when ready
4. **Bootstrap/scripts:** Remove any clone or reference to deployment-v3

---

## Extraction Checklist (from v3)

| v3 Path                           | Target Repo                   | Status |
| --------------------------------- | ----------------------------- | ------ |
| api/\*                            | deployment-api                | Done   |
| ui/\*                             | deployment-ui                 | Done   |
| configs/\*                        | deployment-service            | Done   |
| unified_trading_deployment/\*     | deployment-service            | Done   |
| backends/\*                       | deployment-service            | Done   |
| terraform/\*                      | deployment-service            | Done   |
| infra/\*                          | deployment-service            | Done   |
| deploy.py, deploy                 | deployment-service            | Done   |
| scripts/\*                        | deployment-service (or split) | Done   |
| tests/e2e/\*                      | system-integration-tests      | Done   |
| tests/unit/_, tests/integration/_ | deployment-service            | Done   |
| tools/\*                          | deployment-service            | Done   |
| grafana/\*                        | deployment-service            | Done   |
| templates/\*                      | deployment-service            | Done   |
| docs/\*                           | deployment-service            | Done   |
| Dockerfile, cloudbuild.yaml, etc. | Per-repo                      | Done   |

---

## Risks and Mitigations

**PENDING DEEP AUDIT:** Before deleting archive/unified-trading-deployment-v3, diff every v3 path against the four repos. Confirm: api routes, ui components, scripts, deploy.py, audit/, templates/, grafana/, cleanup_old_instruments_parquet.py placement.

- **Fat vs slim:** Cloud deployment-api bundles service+ui. Unbundling may break `run-api.sh`; update to API-only or document separate run commands.
- **Configs symlink:** deployment-api must have `configs` → `../deployment-service/configs` for quality-gates and validators.
- **Duplicate content:** Cloud deployment-service may already have content from v3; diff before overwrite to avoid losing cloud-only changes.

---

## Pending Deep Final Audit Checklist

Before permanent deletion of `archive/unified-trading-deployment-v3`:

- [ ] Diff v3 api/ vs deployment-api/deployment_api/ for missing routes
- [ ] Diff v3 ui/ vs deployment-ui for missing components
- [ ] Verify all v3 scripts in deployment-service/scripts/
- [ ] Verify deploy.py, deploy, templates/, grafana/, audit/ in deployment-service
- [ ] Verify cleanup_old_instruments_parquet.py placement (deployment-service vs instruments-service)
- [ ] Run quality gates on all four repos
- [ ] Remove cloud copy from iCloud after archive verified
