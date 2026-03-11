---
name: cicd-versioning-cloud-build-2026-03-11
overview:
  Fix 6 CI/CD pipeline gaps + 3 new phases: per-repo ≥1.0.0 staging gate, SIT code/deployment test split, and
  deployment UI build selector. Staging lock lifecycle, dep reconciliation, multi-project GCP Cloud Build isolation,
  SIT SHA pinning, semver-at-staging, manifest schema extensions.
type: infra
epic: epic-infra
status: active

completion_gates:
  code: C5
  deployment: none
  business: none

repo_gates:
  - repo: unified-trading-pm
    code: C4
    deployment: none
    business: none
    readiness_note:
      "DR N/A: local developer tooling — no cloud deployment required. BR N/A: internal tooling, no commercial KPI."
  - repo: system-integration-tests
    code: C4
    deployment: none
    business: none
    readiness_note:
      "DR N/A: local developer tooling — no cloud deployment required. BR N/A: internal tooling, no commercial KPI."
  - repo: deployment-api
    code: C1
    deployment: none
    business: none
    readiness_note:
      "DR N/A: local developer tooling — no cloud deployment required. BR N/A: internal tooling, no commercial KPI."
  - repo: deployment-ui
    code: C1
    deployment: none
    business: none
    readiness_note:
      "DR N/A: local developer tooling — no cloud deployment required. BR N/A: internal tooling, no commercial KPI."

depends_on: []

todos:
  - id: phase-1-manifest-schema
    content:
      "Initialize staging_versions, staging_status, staging_commits, main_commits, deployed_versions fields in
      workspace-manifest.json."
    status: done
    note: "DONE — manifest schema extended."
  - id: phase-2-semver-at-staging
    content:
      "semver-agent.yml triggers on staging only (not main); update-repo-version.yml writes staging_commits[repo]=sha;
      staging-to-main.yml confirmed [skip ci]."
    status: done
    note: "DONE — semver-agent.yml and update-repo-version.yml updated."
  - id: phase-3-sit-lock
    content:
      "Create sit-gate.yml + sit-unlock.yml; add concurrency debounce + sit-lock dispatch to smoke-test-gate.yml;
      quickmerge.sh informs on locked staging."
    status: done
    note: "DONE — sit-gate.yml + sit-unlock.yml created."
  - id: phase-4-dep-reconciliation
    content:
      "Create check-dep-alignment.py; add pre-push hook; add to quickmerge Stage 0; integrate in workspace-bootstrap.sh."
    status: done
    note: "DONE — check-dep-alignment.py + pre-push hook + install-hooks.sh created."
  - id: phase-5-multi-project-cloud-build
    content:
      "Terraform for 3 GCP projects; qg-passed dispatch in quality-gates.yml template; cloud-build-router.yml;
      cloudbuild.yaml multi-project substitutions; uv sync --frozen in Dockerfiles; rollback endpoint in deployment-api."
    status: done
    note:
      "DONE — Terraform environments, cloud-build-router.yml, cloudbuild.yaml template, qg-passed dispatch all created."
  - id: phase-6-cicd-flow-doc
    content:
      "Update docs/repo-management/CI-CD-FLOW.md with staging lock lifecycle, SIT batching, dep ref rules, multi-project
      Cloud Build, semver lifecycle, rollback sections."
    status: done
    note: "DONE — CI-CD-FLOW.md updated."
  - id: phase-7-deployment-ui
    content:
      "Deployment UI build selector: BuildSelector.tsx dropdown + GET /builds/{service} AR tag listing endpoint +
      POST /deployments/{service}/deploy endpoint. Display format: '{version} @ {branch}'. Pre-1.0.0 builds allowed
      for manual deploys. Create deployment_ui_version_selector.plan.md."
    status: todo
    note: "In progress — see Phase 7 section below for full spec."
  - id: phase-8-staging-version-gate
    content:
      "Create staging-version-gate.yml template: blocks PRs to staging if repo version < 1.0.0. PM repo exempt.
      Propagate to all repos via propagate-canonical-versions.py. Register as required status check on staging
      branch protection in each repo."
    status: todo
    note: "Gap in existing plan — staging-gate check was described but no workflow file existed."
  - id: phase-9-sit-code-deployment-split
    content:
      "Split smoke-test-gate.yml into three jobs: setup (v1 repo filter + skip guard), code-tests (static,
      <10 min, pytest -m code_test), deployment-tests (docker-compose mock stack, pytest -m deployment_test).
      Add code_test/deployment_test markers to pyproject.toml and all 34 test files. Update
      docker-compose.mock.yml with v1 service profiles."
    status: todo
    note: "Preserves all existing tests — classification only, no test logic changes."
isProject: false
---

# Plan: CI/CD Versioning, Multi-Project Cloud Build & Staging Queue

**Status:** In Progress **Created:** 2026-03-11 **Supersedes:** `version_control_ci_cd_overhaul_2026_03_11.plan.md`
(absorbed + deleted), `semver_multi_project_env_2026_03_10.plan.md` (superseded) **Refs:**

- `docs/repo-management/CI-CD-FLOW.md`
- `scripts/quickmerge.sh`
- `.github/workflows/staging-to-main.yml`, `update-repo-version.yml`
- `system-integration-tests/.github/workflows/smoke-test-gate.yml`

---

## Context

Four interconnected gaps in the current pipeline:

| #   | Gap                                                                                           | Impact                                                                                              |
| --- | --------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| 1   | Staging lock fires only on major bump cascade, not when SIT starts                            | New repos can land on staging mid-SIT, invalidating the tested set                                  |
| 2   | Dep check compares to `origin/main`, which is behind staging during new releases              | Blocks valid staging work (chicken-and-egg)                                                         |
| 3   | Single GCP project for all builds; dev/staging/prod indistinguishable                         | Can't safely use feature branch images without risking prod AR pollution                            |
| 4   | No commit SHA record for a "tested staging set"                                               | SIT can't know it's testing the same set it was given; reruns are untargeted                        |
| 5   | `semver-agent.yml` triggers on `main` AND `staging`                                           | Version decided twice — at staging merge AND at main merge; should be decided once at staging merge |
| 6   | `staging_versions`, `staging_status`, `staging_commits`, `main_commits` missing from manifest | All referenced by workflows but not initialized                                                     |

**Intended outcome:** Repos queue on staging via GitHub PR auto-merge queue. SIT batches pushes (10-min quiet window via
GHA concurrency groups), owns the staging lock, validates the exact committed SHA set, then promotes to main. Version is
decided once at staging merge. Three isolated GCP projects produce immutable tagged artifacts. Deployment UI can select
branch/version/environment.

---

## Phase 1: Manifest Schema Extensions (prerequisite for everything) ✅ DONE

**Touches:** `unified-trading-pm/workspace-manifest.json`

Initialize all missing fields:

```json
"staging_versions": {},

"staging_status": {
  "locked": false,
  "locked_since": null,
  "locked_reason": null,
  "lock_version": null
},

"staging_commits": {
  "_note": "Exact commit SHAs under test in the current SIT run. Written by update-repo-version.yml when branch=staging. Locked by sit-gate.yml at SIT start. Cleared by staging-to-main.yml after promotion."
},

"main_commits": {
  "_note": "Rolling history of last 5 staging sets promoted to main. Used for rollback reference.",
  "history": []
},

"deployed_versions": {
  "_note": "Current deployed image tag per repo per environment. Updated by Cloud Build post-deploy.",
  "dev": {},
  "staging": {},
  "prod": {}
}
```

---

## Phase 2: Semver at Staging Merge ✅ DONE (semver-agent.yml already staging-only; update-repo-version.yml + staging-to-main.yml updated)

**Goal:** Version decided once when `feat/*` merges to staging. Main merge is silent (`[skip ci]`). No double-bump.

### Current state

- `semver-agent.yml` triggers on push to `main` OR `staging` in 12 service repos
- `version-bump.yml` (per-repo) is DISABLED (`if: false`)
- `update-repo-version.yml` writes `versions[repo]` (main) — no staging_versions write

### Target state

- `semver-agent.yml` triggers on push to `staging` ONLY (remove `main` from trigger)
- When staging-to-main merges via `staging-to-main.yml`, merge commit uses `[skip ci]` — semver-agent does NOT re-run
- Dispatch payload from semver-agent: `{ repo, version, branch: "staging", commit_sha: $GITHUB_SHA }`
- PM's `update-repo-version.yml` writes `staging_versions[repo] = version` AND `staging_commits[repo] = commit_sha` when
  branch=staging
- PM's `staging-to-main.yml` promotes `staging_versions → versions` on SIT pass (no new semver computation)

### Pre-1.0.0 rules unchanged

`feat!:` / removed export → MINOR bump; `feat:` / new export → MINOR; `fix:` → PATCH

### Files

- `unified-trading-pm/scripts/propagation/templates/semver-agent.yml` — change `on.push.branches` from `[main, staging]`
  to `[staging]`
- Propagate to 12 repos via `propagate-canonical-versions.py`: `features-calendar-service`,
  `features-volatility-service`, `features-onchain-service`, `features-sports-service`, `strategy-service`,
  `ml-inference-service`, `pnl-attribution-service`, `risk-and-exposure-service`, `position-balance-monitor-service`,
  `market-tick-data-service`, `features-delta-one-service`, `market-data-processing-service`
- `unified-trading-pm/.github/workflows/update-repo-version.yml` — when branch=staging: write both
  `staging_versions[repo]` and `staging_commits[repo]`; guard `staging_status` access with `.get()` (line ~102 is
  currently unsafe)
- `unified-trading-pm/.github/workflows/staging-to-main.yml` — confirm `[skip ci]` on all merge commits

---

## Phase 3: SIT Lock Lifecycle ✅ DONE (sit-gate.yml + sit-unlock.yml created; smoke-test-gate.yml + quickmerge.sh updated)

**Goal:** SIT owns the staging lock. Lock is set when SIT starts (not earlier). Unlock on failure so engineers can push
fixes.

### Lock flow

```
feat/* passes QG → quickmerge --to-staging → PR to staging (GitHub auto-merge queue)

GitHub auto-merge queue: staging-gate check
  PASS if staging_status.locked == false
  PENDING if staging_status.locked == true  ← PRs queue here during SIT

SIT debounce (GHA concurrency group, 10-min quiet):
  staging push → triggers smoke-test-gate.yml
  concurrency group cancels/replaces if new push arrives within 10 min
  after 10 min quiet → job proceeds

SIT START:
  → reads staging_commits from PM manifest (current SHA set)
  → dispatches sit-lock to PM
  → PM's sit-gate.yml: sets locked=true, locked_reason="SIT running", locked_since=utcnow()
  → SIT clones each repo at its staging_commits SHA for full isolation

SIT PASS:
  → dispatches staging-validated to PM (existing)
  → staging-to-main.yml: appends staging_commits to main_commits.history, promotes staging_versions → versions, clears lock, clears staging_commits

SIT FAIL:
  → dispatches sit-failed to PM
  → sit-unlock.yml: sets locked=false, reason="SIT failed — open for fixes"
  → Queued PRs to staging can now merge (gate passes again)
  → Engineers push fix to feat/* → quickmerge --to-staging → new SIT run
```

### New PM workflows

**`sit-gate.yml`** (new)

- Trigger: `repository_dispatch: sit-lock`
- Payload: `{ repos, commit_shas }` (passed by SIT)
- Actions: set `staging_status.locked=true`, write `staging_commits` from payload, commit `[skip ci]`

**`sit-unlock.yml`** (new)

- Trigger: `repository_dispatch: sit-failed`
- Actions: set `staging_status.locked=false`, clear `locked_since`/`locked_reason`, commit `[skip ci]`

### Updates to existing workflows

**`staging-to-main.yml`**

- Add step: append `staging_commits` to `main_commits.history` (keep last 5, pop oldest if >5)
- Add step: clear `staging_commits` to empty dict
- Add step: clear staging lock (currently done for major bumps in `update-repo-version.yml` — move responsibility here)

**`smoke-test-gate.yml` (system-integration-tests)**

- Add concurrency group for debounce:
  ```yaml
  concurrency:
    group: sit-staging
    cancel-in-progress: true
  ```
  Sleep at start of job for quiet-period enforcement (600s sleep, replaced on new push by cancel-in-progress)
- Add step at workflow start: dispatch `sit-lock` to PM with `{ repos: [...], commit_shas: {...} }` read from manifest
- SIT clones each repo at its `staging_commits[repo]` SHA (not latest) for isolation
- Add step at workflow failure: dispatch `sit-failed` to PM

### `quickmerge.sh` change (Stage 1.5)

When `--to-staging`: check `staging_status.locked` before creating PR. If locked, inform (do not abort):

```
Staging is locked: "SIT running" (since {locked_since}).
Your --to-staging PR will queue automatically via GitHub's staging-gate check.
PR creation will proceed — GitHub will hold it until SIT completes.
```

---

## Phase 4: Dependency Reconciliation Gate ✅ DONE (check-dep-alignment.py + pre-push hook + install-hooks.sh + workspace-bootstrap.sh integration)

**Goal:** Block pushes when a repo's direct deps are not aligned with the correct remote reference (staging or main
depending on context).

### Per-dep reference logic

```
for each direct dep:
    if dep is in manifest.staging_versions AND (push target is staging OR --to-staging):
        compare to origin/staging
    else:
        compare to origin/main
```

If dep NOT in `staging_versions`, fall back to `origin/main`. Handles partial staging sets correctly — avoids
chicken-and-egg when a dep is on staging but not yet promoted to main.

### 4a. Quickmerge Stage 0 enhancement

Add new **STAGE 0: Dep alignment check** before existing Stage 0 (cascade dep-branch):

```bash
# STAGE 0: Validate direct deps against staging or main reference
log_info "STAGE 0: Checking direct dependency alignment..."
python3 "$WORKSPACE_ROOT/scripts/repo-management/check-dep-alignment.py" \
  --repo "$(basename $PWD)" \
  --to-staging "$TO_STAGING" \
  --manifest "$MANIFEST_PATH" \
  || fail "Direct dep alignment failed. Run: bash run-version-alignment.sh --fix"
```

**New script:** `unified-trading-pm/scripts/repo-management/check-dep-alignment.py`

- Reads manifest, gets `dependencies[].name` for this repo
- Per dep: if `--to-staging` and dep is in `staging_versions` → fetch+compare `origin/staging`, else `origin/main`
- Uses `packaging.version.Version` for constraint evaluation
- Exits 0 = aligned, 1 = misaligned with per-dep error message + fix command

### 4b. Git pre-push hook (staging push only)

**File:** `unified-trading-pm/scripts/hooks/pre-push` (new, tracked) **Deployed via:** `workspace-bootstrap.sh` +
`install-hooks.sh`

```bash
#!/usr/bin/env bash
# Blocks git push to staging when direct deps are out of alignment.
# Delegates to check-dep-alignment.py (same logic as quickmerge Stage 0).
# Only fires when pushing to staging branch — no-op for feat/* pushes.

REMOTE="$1"
PUSHING_TO_STAGING=false

while read local_ref local_sha remote_ref remote_sha; do
  if echo "$remote_ref" | grep -q "refs/heads/staging"; then
    PUSHING_TO_STAGING=true
  fi
done

if [ "$PUSHING_TO_STAGING" = false ]; then exit 0; fi

WORKSPACE_ROOT="$(git rev-parse --show-toplevel)/../../"
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"
REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")

[ ! -f "$MANIFEST" ] && exit 0

python3 "$WORKSPACE_ROOT/unified-trading-pm/scripts/repo-management/check-dep-alignment.py" \
  --repo "$REPO_NAME" --to-staging true --manifest "$MANIFEST"
exit $?
```

**`install-hooks.sh`** (new) — for existing workspaces without re-running bootstrap:

```bash
#!/usr/bin/env bash
# Installs pre-push hook in all workspace repos
for repo_dir in $(jq -r '.repositories | keys[]' unified-trading-pm/workspace-manifest.json); do
  hook_target="$repo_dir/.git/hooks/pre-push"
  cp unified-trading-pm/scripts/hooks/pre-push "$hook_target"
  chmod +x "$hook_target"
done
```

**Bootstrap install** (add to `workspace-bootstrap.sh` Phase 4):

```bash
bash unified-trading-pm/scripts/workspace/install-hooks.sh
```

---

## Phase 5: Multi-Project GCP Cloud Build ✅ DONE (Terraform environments, cloud-build-router.yml, cloudbuild.yaml template, qg-passed dispatch in quality-gates.yml)

**Goal:** Three isolated GCP projects. Builds triggered by QG pass (not push). Images tagged with semver + environment
suffix. Libraries build Python wheels; services/APIs/UIs build Docker images.

### 5a. GCP Provisioning

**Terraform:** `unified-trading-pm/terraform/environments/{dev,staging,prod}/main.tf`

Resources per environment:

- `google_project` → `uts-dev-ikenna`, `uts-staging-ikenna`, `uts-prod-ikenna`
- `google_project_service`: `cloudbuild.googleapis.com`, `artifactregistry.googleapis.com`, `run.googleapis.com`
- `google_artifact_registry_repository` named `unified-trading` (Docker format)
- Cloud Build SA IAM: Artifact Registry Writer + Cloud Run Developer + Secret Manager Accessor
- GH secrets to create: `GCP_SA_KEY_DEV`, `GCP_SA_KEY_STAGING`, `GCP_SA_KEY_PROD`

### 5b. QG-triggered build dispatch

Each repo's `quality-gates.yml` (template) adds a final step on success:

```yaml
- name: Dispatch build to PM
  if: success()
  uses: peter-evans/repository-dispatch@v3
  with:
    token: ${{ secrets.GH_PAT }}
    repository: IggyIkenna/unified-trading-pm
    event-type: qg-passed
    client-payload: |
      {
        "repo": "${{ github.event.repository.name }}",
        "branch": "${{ github.ref_name }}",
        "commit_sha": "${{ github.sha }}",
        "version": "${{ steps.read-version.outputs.version }}",
        "repo_type": "${{ steps.read-type.outputs.type }}"
      }
```

### 5c. PM `cloud-build-router.yml` (new)

- Trigger: `repository_dispatch: qg-passed`
- Routes based on branch:
  - `feat/*` → trigger Cloud Build in `uts-dev-ikenna`
  - `staging` → trigger Cloud Build in `uts-staging-ikenna`
  - `main` → trigger Cloud Build in `uts-prod-ikenna`
- If `repo_type == "library"` → build Python wheel (not Docker); push to AR as `.whl`
- If `repo_type` is service/api/ui → build Docker image
- Uses `gcloud builds triggers run {repo}-{env}` with substitutions `_VERSION`, `_BRANCH`, `_SHA`

### 5d. cloudbuild.yaml template update

```yaml
substitutions:
  _VERSION: "0.0.0"
  _BRANCH: "main"
  _SHA: ""
  _PROJECT_ID: ""
  _AR_HOST: "asia-northeast1-docker.pkg.dev"
  _AR_REPO: "unified-trading"

steps:
  - name: "gcr.io/cloud-builders/docker"
    entrypoint: bash
    args:
      - -c
      - |
        BRANCH_SLUG=$(echo "${_BRANCH}" | sed 's|/|-|g' | tr '[:upper:]' '[:lower:]')
        if [ "${_BRANCH}" = "main" ]; then
          TAG="${_VERSION}"
        elif [ "${_BRANCH}" = "staging" ]; then
          TAG="${_VERSION}-staging"
        else
          TAG="${_VERSION}-${BRANCH_SLUG}"
        fi
        docker build -t ${_AR_HOST}/${_PROJECT_ID}/${_AR_REPO}/${_REPO_NAME}:${TAG} .
        docker push ${_AR_HOST}/${_PROJECT_ID}/${_AR_REPO}/${_REPO_NAME}:${TAG}

  # Post-build: update deployed_versions in PM manifest
  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk"
    entrypoint: bash
    args:
      - -c
      - |
        python3 scripts/update-deployed-version.py \
          --repo $_REPO_NAME --env $_ENV --tag $TAG
```

**Image tag formula:**

| Branch            | Tag                       |
| ----------------- | ------------------------- |
| `main`            | `0.3.168`                 |
| `staging`         | `0.3.168-staging`         |
| `feat/my-feature` | `0.3.168-feat-my-feature` |

**Tags are immutable.** Never overwrite. To fix a bad image at the same semver, bump version first.

### 5e. Dockerfile `uv sync --frozen`

All service Dockerfiles updated:

```dockerfile
RUN uv sync --frozen --no-dev
```

`uv.lock` = reproducibility SSOT. `pyproject.toml` ranges are API compatibility contracts. Never re-resolve in CI or
prod builds.

### 5f. Rollback

- Images kept indefinitely; 90-day lifecycle policy for dev project only
- `deployment-api`: new endpoint `POST /deployments/{service}/rollback` with body
  `{ "image_tag": "0.3.165", "environment": "prod" }`
- Triggers `gcloud run deploy --image {ar_host}/{project}/{repo}/{service}:{tag}`
- Updates `deployed_versions.{env}.{repo}` in PM manifest via GitHub API

---

## Phase 6: CI-CD-FLOW.md Update ✅ DONE (Staging Lock Lifecycle, SIT Batching, Dep Reference Rules, Multi-Project Cloud Build, Semver Lifecycle, Rollback sections added)

**File:** `unified-trading-pm/docs/repo-management/CI-CD-FLOW.md`

Add / update the following sections to reflect the new pipeline:

**Section: Staging Lock Lifecycle** (new)

- SIT-owned lock: set at SIT start via `sit-lock` dispatch, cleared on SIT pass OR fail
- Diagram: `feat/* → staging queue → SIT lock → (pass) main / (fail) unlock + fix`
- Document `sit-gate.yml` + `sit-unlock.yml`

**Section: SIT Batching** (new, under "Phase 3 — Sync to Main")

- 10-min quiet-period debounce via GHA concurrency groups (`cancel-in-progress: true`)
- Multiple staging pushes within 10 min → single SIT run covering the full batch

**Section: Dependency Reference Rules** (update existing)

- Replace "all deps vs `origin/main`" with per-dep logic:
  - Dep in `staging_versions` AND push target is staging → `origin/staging`
  - Otherwise → `origin/main`
- Note: avoids chicken-and-egg when dep is on staging but not yet on main

**Section: Multi-Project Cloud Build** (new)

- Routing table:
  ```
  Branch    GCP Project          Tag format
  feat/*    uts-dev-ikenna       {semver}-{branch-slug}
  staging   uts-staging-ikenna   {semver}-staging
  main      uts-prod-ikenna      {semver}
  ```
- Trigger: QG pass → `qg-passed` dispatch → PM `cloud-build-router.yml` → Cloud Build
- Libraries build Python wheels; services/APIs/UIs build Docker images
- All builds use `uv sync --frozen` (`uv.lock` = reproducibility SSOT)

**Section: Semver Lifecycle** (update)

- Version decided at staging merge (semver-agent on staging push)
- `staging_versions` = in-flight; `versions` = stable post-SIT
- Main merge is `[skip ci]` — no re-bump
- `main_commits.history` = rolling last 5 promoted staging sets

**Section: Rollback** (new)

- Tags are immutable in Artifact Registry
- Rollback = `POST /deployments/{service}/rollback {"image_tag": "...", "environment": "..."}`
- Deployment UI will show last 5 known-good tags from `main_commits.history`

---

## Phase 7: Deployment UI Build Selector (In Progress)

**Tracked in:** `deployment_ui_version_selector.plan.md` (to be created)

**Goal:** Dropdown in deployment-ui showing available builds as `{version} @ {branch}` parsed from AR tags. Select any
build to deploy to any environment. Pre-1.0.0 builds allowed (manual deploy, no version gate here).

### Tag → display name mapping

| AR Tag                    | Display                     |
| ------------------------- | --------------------------- |
| `0.3.168`                 | `0.3.168 @ main`            |
| `0.3.168-staging`         | `0.3.168 @ staging`         |
| `0.3.168-feat-my-feature` | `0.3.168 @ feat/my-feature` |

Parse: version = leading `M.N.P` digits; branch slug = suffix (reverse `-` to `/` for `feat-`, `fix-`, `chore-`).
Idempotent: same version + same branch always refers to the same artifact (enforced by immutable tags in Phase 5d).

### New API endpoints (`deployment-api/deployment_api/routes/builds.py`)

**`GET /builds/{service}?env=dev|staging|prod`**

- Lists AR tags for `{service}` in the GCP project for `env`
- Returns: `[{ "tag": str, "display": str, "version": str, "branch": str, "is_v1": bool }]` sorted version desc
- Falls back to `deployed_versions` from PM manifest if AR unreachable

**`POST /deployments/{service}/deploy`**

- Body: `{ "image_tag": str, "environment": "dev|staging|prod" }`
- Deploys any tag (including pre-1.0.0) to any environment — manual deploys have no version gate
- Same Cloud Run mechanics as existing rollback endpoint
- Register in `deployment_api/main.py`

### New UI component (`deployment-ui/src/components/BuildSelector.tsx`)

- Fetches from `GET /builds/{service}?env={selectedEnv}` on env/service change
- Dropdown: shows `{display}` label, sorted version desc
- Badge: `v1` (green) for `is_v1: true`; `pre-v1` (amber) for `is_v1: false`
- On select: pre-fills `image_tag` field in DeployForm (user can still type manually)

### Files

- `deployment-api/deployment_api/routes/builds.py` (NEW)
- `deployment-api/deployment_api/main.py` (register builds router)
- `deployment-ui/src/components/BuildSelector.tsx` (NEW)
- `deployment-ui/src/components/DeployForm.tsx` (extend: add BuildSelector above image_tag input)
- `deployment-ui/src/api/deploymentApi.ts` (add `fetchBuilds`, `deployBuild`)
- `unified-trading-pm/plans/active/deployment_ui_version_selector.plan.md` (CREATE)

---

## Phase 8: Per-Repo Staging Version Gate (NEW)

**Goal:** Block PRs from individual repos to staging when their version < 1.0.0. Per-repo gate — a repo at 1.0.0 merges
freely even if other repos are still on 0.x.x. PM repo (`unified-trading-pm`) is exempt (it manages the manifest, has no
semver).

### Gap addressed

The plan described a "staging-gate check" (GitHub branch protection required status check) but no workflow file
implemented it. Only `staging_status.locked` was enforced. This phase fills that gap.

### `staging-version-gate.yml` template

**File:** `unified-trading-pm/scripts/propagation/templates/staging-version-gate.yml`

```yaml
name: Staging Version Gate
on:
  pull_request:
    branches: [staging]

jobs:
  version-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check version >= 1.0.0
        run: |
          REPO="${{ github.event.repository.name }}"
          if [ "$REPO" = "unified-trading-pm" ]; then
            echo "PM repo exempt from version gate — pass."; exit 0
          fi
          if [ -f pyproject.toml ]; then
            VERSION=$(grep -m1 '^version\s*=' pyproject.toml | sed 's/.*= *"\([^"]*\)".*/\1/')
          elif [ -f package.json ]; then
            VERSION=$(node -p "require('./package.json').version")
          else
            echo "::error::No version file found (pyproject.toml or package.json)"; exit 1
          fi
          echo "Version: $VERSION"
          python3 -c "
          from packaging.version import Version
          v = Version('$VERSION')
          if v < Version('1.0.0'):
              raise SystemExit(
                  f'::error::Version {v} < 1.0.0 — blocked from staging. '
                  f'Reach 1.0.0 via production checklist before this PR can merge.'
              )
          print(f'Version {v} >= 1.0.0 — staging gate passed.')
          "
```

**Propagation:** `propagate-canonical-versions.py` — same mechanism as `semver-agent.yml` (Phase 2). Deploy to all repos
listed in `workspace-manifest.json`.

**GitHub branch protection:** Add `Staging Version Gate / version-gate` as required status check on the staging branch
protection rule of each repo (or `staging-version-gate` check name).

### Files

- `unified-trading-pm/scripts/propagation/templates/staging-version-gate.yml` (NEW)
- Each repo's `.github/workflows/staging-version-gate.yml` (propagated)
- `unified-trading-pm/docs/repo-management/CI-CD-FLOW.md` (add "Per-Repo Version Gate" section)

---

## Phase 9: SIT Code-Tests / Deployment-Tests Split (NEW)

**Goal:** Split monolithic `smoke-test-gate.yml` into fast code-tests (<10 min) and slower deployment-tests
(docker-compose mock stack). Both scoped to repos with `staging_versions[repo] >= 1.0.0`. All existing tests preserved —
classification only, no test logic changes.

### Skip guard

When `staging_versions` has no repos with version ≥1.0.0, SIT exits immediately (no lock dispatched):

```python
v1_repos = [r for r, v in staging_versions.items()
            if not r.startswith('_') and Version(v) >= Version('1.0.0')]
if not v1_repos:
    print("No repos >= 1.0.0 on staging. Skipping SIT.")
    sys.exit(0)
```

### Test classification

**`code_test` marker** (static, no live services, <10 min total):

| File                             | Directory    |
| -------------------------------- | ------------ |
| `test_layer0_contracts.py`       | smoke/       |
| `test_layer1_services.py`        | smoke/       |
| `test_portable_criteria.py`      | smoke/       |
| `test_cli_worker_smoke.py`       | smoke/       |
| `test_library_imports.py`        | integration/ |
| `test_contract_coverage.py`      | integration/ |
| `test_uac_completeness.py`       | integration/ |
| `test_uic_completeness.py`       | integration/ |
| `test_uac_contract_coverage.py`  | integration/ |
| `test_utl_contract_coverage.py`  | integration/ |
| `test_uac_uic_compat.py`         | integration/ |
| `test_uac_uic_schema_compat.py`  | integration/ |
| `test_uac_deep_import_health.py` | integration/ |
| `test_uei_event_dispatch.py`     | integration/ |
| `test_error_normalisation.py`    | integration/ |
| `test_config.py`                 | unit/        |
| `test_event_logging.py`          | unit/        |

**`deployment_test` marker** (needs docker-compose mock stack):

| File                               | Directory    |
| ---------------------------------- | ------------ |
| `test_api_smoke.py`                | smoke/       |
| `test_deployment_smoke.py`         | smoke/       |
| `test_internal_services_smoke.py`  | smoke/       |
| `test_pipeline_smoke.py`           | smoke/       |
| `test_cache_smoke.py`              | smoke/       |
| `test_database_smoke.py`           | smoke/       |
| `test_pubsub_smoke.py`             | smoke/       |
| `test_artifact_registry_smoke.py`  | smoke/       |
| `test_cloud_infra_smoke.py`        | smoke/       |
| `test_cross_service_chains.py`     | integration/ |
| `test_data_freshness.py`           | integration/ |
| `test_data_freshness_contracts.py` | integration/ |
| `test_recon_rebalancing.py`        | integration/ |
| `test_deployment_e2e.py`           | e2e/         |
| `test_auth_e2e.py`                 | e2e/         |
| `test_pipeline_e2e.py`             | e2e/         |
| `test_version_cascade_e2e.py`      | e2e/         |
| `test_aws_s3_smoke.py`             | e2e/         |
| `test_execution_latency.py`        | performance/ |

### Workflow restructure (`smoke-test-gate.yml`)

Three jobs (sequential via `needs:`):

```
setup
  → reads staging_versions, computes v1_repos
  → sets output has_v1_repos: true/false
  → if false: exits success (no lock dispatched)

code-tests (needs: setup, if: has_v1_repos)
  → timeout-minutes: 10
  → dispatches sit-lock to PM
  → pytest tests/ -m code_test
  → on failure: dispatches sit-failed

deployment-tests (needs: code-tests, if: has_v1_repos)
  → docker compose -f docker/docker-compose.mock.yml --profile v1 up -d
  → waits for health checks
  → pytest tests/ -m deployment_test
  → docker compose down
  → on success: dispatches staging-validated
  → on failure: dispatches sit-failed
```

The existing `contract-adoption-check` job is classified as `code_test` work and merged into the `code-tests` job (no
separate job needed — reduces GHA minutes).

### docker-compose.mock.yml `v1` profile

Services for repos with version ≥1.0.0 get `profiles: [v1]`. The `setup` job writes a `.env.v1` file (list of enabled
services) — compose reads it to decide which `v1` profile services to start. Avoids hardcoding the v1 set in the compose
file.

### Files

- `system-integration-tests/.github/workflows/smoke-test-gate.yml` (restructure)
- `system-integration-tests/pyproject.toml` (add `code_test` and `deployment_test` markers)
- `system-integration-tests/tests/smoke/test_layer0_contracts.py` + 16 other code_test files (add
  `@pytest.mark.code_test`)
- `system-integration-tests/tests/smoke/test_api_smoke.py` + 18 other deployment_test files (add
  `@pytest.mark.deployment_test`)
- `unified-trading-pm/docker/docker-compose.mock.yml` (add `profiles: [v1]` to each service)

---

## Implementation Order (updated)

```
Phase 1–6: DONE

Phase 8 (staging version gate)         ← independent, no deps
  → create template → test on 1 repo → propagate all

Phase 9 (SIT split)                    ← independent of Phase 8
  → add markers to pyproject.toml
  → add @pytest.mark decorators to 34 test files
  → restructure smoke-test-gate.yml
  → update docker-compose.mock.yml

Phase 7 (deployment UI build selector) ← independent
  → builds.py route (GET + POST)
  → register in main.py
  → BuildSelector.tsx
  → extend DeployForm.tsx
  → create deployment_ui_version_selector.plan.md
```

---

## Original Implementation Order (Phases 1–6, all DONE)

```
Phase 1 (manifest schema)
  → Phase 2 (semver-agent) + Phase 3 (SIT lock) — parallel, both need Phase 1
  → Phase 4 (dep check) — needs Phase 2 (staging_versions exists) + Phase 3 (lock check in quickmerge)
  → Phase 5 (Cloud Build) — needs Phase 1 (deployed_versions); Terraform can start in parallel
  → Phase 6 (CI-CD-FLOW.md) — update after Phase 1–5 committed so doc reflects real state
```

---

## Non-Goals

- Changing `>=X.Y.Z` ranges to `==X.Y.Z` in pyproject.toml — `uv.lock` + `--frozen` handles reproducibility
- Service mesh (existing architecture decision)
- Changing T0→T1→T2→T3 cascade order
- Building Docker images for library repos (wheels only)

---

## Potential Conflict to Watch

`full_autonomous_agent_ci.plan.md` also references `semver-agent.yml`. That plan is in planning stage only. No code
conflict expected, but Phase 2 of this plan (semver trigger change) must land before that plan implements any
semver-agent changes.

---

## Critical Files

| File                                                                 | Phase | Change                                                                                                                      |
| -------------------------------------------------------------------- | ----- | --------------------------------------------------------------------------------------------------------------------------- |
| `unified-trading-pm/workspace-manifest.json`                         | 1     | Add `staging_versions`, `staging_status`, `staging_commits`, `main_commits`, `deployed_versions`                            |
| `unified-trading-pm/scripts/propagation/templates/semver-agent.yml`  | 2     | Trigger `staging` only, not `main`; include `commit_sha` in dispatch payload                                                |
| `unified-trading-pm/.github/workflows/update-repo-version.yml`       | 2     | Write `staging_commits[repo]=sha` when branch=staging; guard `.get()` on `staging_status`                                   |
| `unified-trading-pm/.github/workflows/staging-to-main.yml`           | 2, 3  | Confirm `[skip ci]`; append to `main_commits.history`; clear `staging_commits`; clear lock                                  |
| `unified-trading-pm/.github/workflows/sit-gate.yml`                  | 3     | NEW — sets lock + writes staging_commits SHAs on sit-lock dispatch                                                          |
| `unified-trading-pm/.github/workflows/sit-unlock.yml`                | 3     | NEW — clears lock on sit-failed dispatch                                                                                    |
| `unified-trading-pm/scripts/quickmerge.sh`                           | 3, 4  | Inform (not block) on locked staging; add Stage 0 dep check                                                                 |
| `system-integration-tests/.github/workflows/smoke-test-gate.yml`     | 3     | Add concurrency group (debounce); dispatch sit-lock at start; clone at staging_commits SHAs; dispatch sit-failed on failure |
| `unified-trading-pm/scripts/repo-management/check-dep-alignment.py`  | 4     | NEW — dep constraint vs staging/main reference                                                                              |
| `unified-trading-pm/scripts/hooks/pre-push`                          | 4     | NEW — git pre-push hook (staging pushes only)                                                                               |
| `unified-trading-pm/scripts/workspace/install-hooks.sh`              | 4     | NEW — installs pre-push hook across all repos                                                                               |
| `unified-trading-pm/scripts/workspace/workspace-bootstrap.sh`        | 4     | Add hook install call in Phase 4                                                                                            |
| `unified-trading-pm/terraform/environments/`                         | 5a    | NEW — Terraform for 3 GCP projects                                                                                          |
| `unified-trading-pm/scripts/propagation/templates/quality-gates.yml` | 5b    | Add qg-passed dispatch step on success                                                                                      |
| `unified-trading-pm/.github/workflows/cloud-build-router.yml`        | 5c    | NEW — routes qg-passed to correct Cloud Build project                                                                       |
| `unified-trading-pm/scripts/propagation/templates/cloudbuild.yaml`   | 5d    | Multi-project substitutions + tag formula                                                                                   |
| All service Dockerfiles                                              | 5e    | `uv sync --frozen --no-dev`                                                                                                 |
| `deployment-api/`                                                    | 5f    | `POST /deployments/{service}/rollback` endpoint                                                                             |
| `docs/repo-management/CI-CD-FLOW.md`                                 | 6     | Add sections: staging lock lifecycle, SIT batching, dep ref rules, multi-project routing, semver lifecycle, rollback        |

---

## Reusable Utilities

- `packaging.version.Version` — constraint evaluation in `check-dep-alignment.py`
- `propagate-canonical-versions.py` — propagate semver-agent.yml + quality-gates.yml templates to all repos
- `update-repo-version.yml` — reuse for `staging_commits` write (add `commit_sha` input)
- `staging-to-main.yml` — reuse, extend with history management + lock clear
- `gh api` CLI — all GHA workflows already use it

---

## Verification

1. **Manifest schema** — `jq 'keys' workspace-manifest.json` includes all 5 new fields
2. **Semver at staging** — `feat!:` merge to staging → semver-agent fires → `staging_versions` updated; main merge → no
   semver re-run (`[skip ci]` confirmed)
3. **Lock lifecycle** — push two repos to staging within 5 min → single SIT run after 10-min quiet; SIT start →
   `locked=true`; SIT pass → `locked=false` + `main_commits.history` has entry
4. **SHA isolation** — SIT workflow logs show `git checkout {sha}` per repo (not latest HEAD)
5. **Lock on failure** — force SIT failure → `sit-unlock.yml` fires → `locked=false` → new PRs to staging merge
6. **Dep check (quickmerge)** — pin dep to version older than `staging_versions` → Stage 0 fails with dep name + fix
   command
7. **Pre-push hook (staging only)** — misaligned dep → `git push origin staging` blocked;
   `git push origin feat/my-feature` NOT blocked
8. **Cloud Build routing** — QG passes on `feat/*` → Cloud Build triggers in `uts-dev-ikenna`; image tagged
   `{semver}-feat-*`
9. **uv.lock frozen** — no `uv pip install` in Docker layer history; only `uv sync --frozen`
10. **Rollback** — `POST /deployments/market-tick-data-service/rollback {"image_tag":"0.3.165","environment":"prod"}` →
    Cloud Run revision updated; `deployed_versions.prod` updated in manifest
