# Semver Version Tagging + Multi-Project per Environment

**Status:** Superseded — see `cicd_versioning_cloud_build_2026_03_11.md` (extends + replaces all items here)
**Created:** 2026-03-10 **Refs:** `docs/dev-environment-vars.md`,
`plans/archive/uci_cloud_abstraction_complete.md`, `plans/archive/roadmap-batch-85pct-2026-02-11.md`

---

## Goal

Differentiate feature/dev vs staging vs prod deployments via:

1. **Semver version tags** with optional branch suffix (or nothing on main)
2. **Different GCP project IDs** per environment (dev / staging / prod)
3. **Cloud Build triggers** scoped by branch and project

---

## Current State

- **Version bump:** `version-bump.yml` runs on main merge; reads conventional commit prefix → semver bump
- **Cloud Build:** Uses `$PROJECT_ID` (Cloud Build substitution) and `$SHORT_SHA` + `latest` tags
- **Images:** Pushed to `{ar_host}/$PROJECT_ID/{ar_repo}/{repo_name}:$SHORT_SHA` and `:latest`
- **No branch suffix:** All builds share same tag pattern regardless of branch
- **Single project:** One GCP project for all builds

---

## Target State

### 1. Semver Version Tags with Branch Suffix

| Branch    | Tag pattern               | Example                |
| --------- | ------------------------- | ---------------------- |
| `main`    | `{version}`               | `0.12.3`               |
| `staging` | `{version}-staging`       | `0.12.3-staging`       |
| `feat/*`  | `{version}-{branch-slug}` | `0.12.3-feat-rollback` |
| `dev`     | `{version}-dev`           | `0.12.3-dev`           |

- **Version source:** `version-bump.yml` writes to `pyproject.toml` / `package.json` on main
- **Branch slug:** Derived from `$BRANCH_NAME` (sanitized: replace `/` with `-`, lowercase)
- **Nothing on main:** Main gets clean semver only (no suffix)

### 2. Project ID per Environment

| Environment | Project ID          | Branch          | Purpose              |
| ----------- | ------------------- | --------------- | -------------------- |
| **dev**     | `uts-dev-{org}`     | `feat/*`, `dev` | Feature/dev rollouts |
| **staging** | `uts-staging-{org}` | `staging`       | Pre-prod validation  |
| **prod**    | `uts-prod-{org}`    | `main`          | Production           |

- **Cloud Build:** Each trigger uses `_PROJECT_ID` substitution or `projectId` in the trigger config
- **Artifact Registry:** Images pushed to `{ar_host}/{project_id}/{ar_repo}/{repo_name}:{tag}`
- **Secrets:** `TELEGRAM_BOT_TOKEN`, etc. propagated per project via `propagate-github-secrets.sh --repo X`

### 3. Trigger Separation (Already in Place)

| Repo type                                 | Builds               | Triggers                               |
| ----------------------------------------- | -------------------- | -------------------------------------- |
| **Deployable** (service, api-service, ui) | Docker images        | Cloud Build on push/merge              |
| **Libraries**                             | Artifact wheels only | Cloud Build → `unified-libraries` repo |
| **PM, codex**                             | Docs only; no builds | Cloned as siblings for GHA             |

---

## Implementation Phases

### Phase 1: Project IDs per Environment

1. Create GCP projects: `uts-dev-*`, `uts-staging-*`, `uts-prod-*` (or use existing)
2. Enable Artifact Registry, Cloud Build, Secret Manager in each
3. Create Cloud Build triggers per project, scoped by branch:
   - `main` → `uts-prod-*`
   - `staging` → `uts-staging-*`
   - `feat/*`, `dev` → `uts-dev-*`
4. Propagate secrets to all projects via `propagate-github-secrets.sh`

### Phase 2: Semver Tag with Branch Suffix

1. Update `version-bump.yml` to output `VERSION_SUFFIX` env var:
   - Main: `""`
   - Staging: `-staging`
   - Other: `-{branch-slug}`
2. Update `cloudbuild.yaml` templates to tag images with:
   - `{version}` or `{version}{suffix}` (from `version-bump.yml` or `$BRANCH_NAME`)
3. Ensure `version-bump.yml` runs on main only; staging/feat builds use `$SHORT_SHA` + suffix if no version file

### Phase 3: Rollout

1. Update `rollout-ui-build-infra.py` cloudbuild template with new tag logic
2. Add service/API cloudbuild template if not present (or document manual propagation)
3. Run `run-all-setup.sh --rollout-first` to propagate
4. Update `CI-CD-FLOW.md` with trigger separation and multi-project docs

---

## Dependencies

- `docs/dev-environment-vars.md`: `GCP_PROJECT_ID`, `ENVIRONMENT` (development/staging/production)
- `plans/archive/uci_cloud_abstraction_complete.md`: Terraform `project_id`, `environment`
- `unified-trading-pm/scripts/workspace/propagate-github-secrets.sh`: Per-repo secrets; extend for multi-project

---

## Acceptance Criteria

- [ ] Main builds push to prod project with clean semver tag (`0.12.3`)
- [ ] Staging builds push to staging project with `-staging` suffix
- [ ] Feature branch builds push to dev project with `-{branch-slug}` suffix
- [ ] No cross-project image pollution (dev images never in prod artifact registry)
- [ ] CI-CD-FLOW documents trigger separation and multi-project flow
