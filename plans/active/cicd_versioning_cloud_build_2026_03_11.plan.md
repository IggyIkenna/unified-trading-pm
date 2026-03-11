# Plan: CI/CD Versioning, Multi-Project Cloud Build & Staging Queue

**Status:** Active **Created:** 2026-03-11 **Supersedes:** `version_control_ci_cd_overhaul_2026_03_11.plan.md`
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

## Phase 1: Manifest Schema Extensions (prerequisite for everything)

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

## Phase 2: Semver at Staging Merge

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

## Phase 3: SIT Lock Lifecycle

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

## Phase 4: Dependency Reconciliation Gate

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

## Phase 5: Multi-Project GCP Cloud Build

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

## Phase 6: CI-CD-FLOW.md Update

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

## Phase 7: Deployment UI Branch/Version Selection (P2 — future)

Track separately: `deployment_ui_version_selector.plan.md`

- Environment dropdown (Dev/Staging/Prod)
- Version list from `deployed_versions.{env}` + AR tag list
- "Last known good" from `main_commits.history[0]`
- Rollback button → `POST /deployments/{service}/rollback`

---

## Implementation Order

```
Phase 1 (manifest schema)
  → Phase 2 (semver-agent) + Phase 3 (SIT lock) — parallel, both need Phase 1
  → Phase 4 (dep check) — needs Phase 2 (staging_versions exists) + Phase 3 (lock check in quickmerge)
  → Phase 5 (Cloud Build) — needs Phase 1 (deployed_versions); Terraform can start in parallel
  → Phase 6 (CI-CD-FLOW.md) — update after Phase 1–5 committed so doc reflects real state
  → Phase 7 (deployment UI) — needs Phase 5
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
