---
doc_type: plan
title: deployment-ui-version-selector
summary: Build selector dropdown in deployment-ui — shows available builds as "{version} @ {branch}" parsed from Artifact
  Registry tags. Manual deploy of any build to any environment. New API endpoints in deployment-api for AR tag listing and
  forward deploys.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui, market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-11'
type: feature
epic: epic-infra
completion_gates: {code: C3, deployment: none, business: none}
repo_gates:
- {repo: deployment-api, code: C3, deployment: none, business: none, readiness_note: 'DR N/A: internal tooling. BR N/A: internal tooling.'}
- {repo: deployment-ui, code: C3, deployment: none, business: none, readiness_note: 'DR N/A: internal tooling. BR N/A: internal tooling.'}
depends_on: [cicd-versioning-cloud-build-2026-03-11]
todos:
- {id: builds-api-endpoint, content: 'Add GET /api/builds/{service}?env=dev|staging|prod to deployment-api/deployment_api/routes/builds.py. Lists AR tags, parses to display name ''{version} @ {branch}'', returns is_v1 flag.', status: done, note: 'New route file: deployment-api/deployment_api/routes/builds.py'}
- {id: deploy-api-endpoint, content: 'Add POST /api/deployments/{service}/deploy to deployment-api/deployment_api/routes/builds.py. Body: {image_tag, environment}. Deploys any tag (including pre-1.0.0) to any environment. No version gate on manual deploys — that''s the whole point.', status: done, note: Same route file as builds API.}
- {id: register-builds-router, content: Register builds router in deployment-api/deployment_api/main.py., status: done, note: Add import + include_router call.}
- {id: build-selector-ui, content: 'Create deployment-ui/src/components/BuildSelector.tsx — dropdown fetching from GET /api/builds/{service}?env={env}. Shows ''{version} @ {branch}'' labels, v1/pre-v1 badges.', status: done, note: New component.}
- {id: deploy-form-extend, content: Extend deployment-ui/src/components/DeployForm.tsx — add BuildSelector above the image_tag input field. Selecting a build pre-fills image_tag., status: done, note: User can still type a tag manually.}
- {id: deploy-api-client, content: Add fetchBuilds() and deployBuild() to deployment-ui/src/api/deploymentApi.ts., status: done, note: Type-safe API client functions.}
isProject: false
---

# Plan: Deployment UI Build Selector

**Status:** Active **Created:** 2026-03-11 **Parent plan:** `cicd_versioning_cloud_build_2026_03_11.md` (Phase 7)

---

## Context

The CI/CD pipeline (Phase 5) builds Docker images tagged as `{version}-{branch-slug}` and pushes them to Artifact
Registry. Examples: `0.3.168`, `0.3.168-staging`, `0.3.168-feat-my-feature`.

Currently, the deployment-ui has no way to see what builds are available in AR. Engineers must look up image tags
manually. The rollback endpoint exists but only handles rollback semantics.

**Goal:** Add a `BuildSelector` dropdown to the deployment form that shows all available builds in a human-readable
format (`{version} @ {branch}`), allows selecting any build for any environment, and submits a deploy request. Pre-1.0.0
builds are allowed (deployment is always a manual decision).

---

## Tag → Display Name Mapping

Artifact Registry tags follow the formula from `cloud-build-router.yml` (Phase 5d):

| AR Tag                    | Parsed display              | Notes                     |
| ------------------------- | --------------------------- | ------------------------- |
| `0.3.168`                 | `0.3.168 @ main`            | Main build — clean semver |
| `0.3.168-staging`         | `0.3.168 @ staging`         | Staging build             |
| `0.3.168-feat-my-feature` | `0.3.168 @ feat/my-feature` | Feature build             |
| `0.3.168-fix-auth-bug`    | `0.3.168 @ fix/auth-bug`    | Fix build                 |

**Parsing rules:**

1. Extract leading `M.N.P` as `version`
2. Remainder (after first `-` following semver digits) is the `branch_slug`
3. Reverse slug to branch name: `feat-`, `fix-`, `chore-`, `refactor-` → replace first `-` with `/`
4. Special cases: `staging` → `staging`; empty remainder → `main`

**Idempotent:** Same version + same branch = same artifact. Immutable tags (Phase 5d) enforce this.

---

## API Changes (`deployment-api`)

### `deployment-api/deployment_api/routes/builds.py` (NEW)

#### `GET /api/builds/{service}?env=dev|staging|prod`

Lists available builds for a service from Artifact Registry.

**Response:**

```json
[
  {
    "tag": "0.3.168-feat-my-feature",
    "display": "0.3.168 @ feat/my-feature",
    "version": "0.3.168",
    "branch": "feat/my-feature",
    "is_v1": false
  },
  {
    "tag": "1.0.0",
    "display": "1.0.0 @ main",
    "version": "1.0.0",
    "branch": "main",
    "is_v1": true
  }
]
```

Sorted by version descending (newest first). Falls back to `deployed_versions` from PM manifest if AR is unreachable
(mock mode / no GCP credentials).

#### `POST /api/deployments/{service}/deploy`

Deploys any build tag to any environment. No version gate — deployment is always manual.

**Request body:**

```json
{
  "image_tag": "0.3.168-feat-my-feature",
  "environment": "dev"
}
```

**Response:** `{ "status": "deploying", "service": "...", "image_tag": "...", "environment": "..." }`

Internally calls Cloud Run deploy via the `UnifiedCloudConfig`-backed client (same mechanism as the existing rollback
endpoint in `deployments.py`). Returns 202 if accepted.

---

## UI Changes (`deployment-ui`)

### `deployment-ui/src/components/BuildSelector.tsx` (NEW)

```tsx
interface BuildEntry {
  tag: string;
  display: string;
  version: string;
  branch: string;
  is_v1: boolean;
}

interface BuildSelectorProps {
  service: string;
  env: string;
  onSelect: (tag: string) => void;
}
```

- Fetches from `GET /api/builds/{service}?env={env}` when `service` or `env` changes
- Shows loading state while fetching; empty state if no builds found
- Dropdown label: `{display}` (e.g. `0.3.168 @ feat/my-feature`)
- Badge next to label: green `v1` chip for `is_v1: true`; amber `pre-v1` for false
- On selection: calls `onSelect(tag)` to pre-fill the image tag field in parent

### `deployment-ui/src/components/DeployForm.tsx` (EXTEND)

Add `BuildSelector` above the existing image tag input. When a build is selected:

- Pre-fills the `image_tag` field
- Clears any manual override the user had typed

User can still type an image tag manually (useful for tags not yet showing in AR).

### `deployment-ui/src/api/deploymentApi.ts` (EXTEND)

```typescript
// Add these two functions:
export async function fetchBuilds(service: string, env: string): Promise<BuildEntry[]>;
export async function deployBuild(service: string, imageTag: string, environment: string): Promise<void>;
```

---

## Files Changed

| File                                             | Change                                                                   |
| ------------------------------------------------ | ------------------------------------------------------------------------ |
| `deployment-api/deployment_api/routes/builds.py` | NEW — GET /api/builds/{service} + POST /api/deployments/{service}/deploy |
| `deployment-api/deployment_api/main.py`          | Import + register builds router                                          |
| `deployment-ui/src/components/BuildSelector.tsx` | NEW                                                                      |
| `deployment-ui/src/components/DeployForm.tsx`    | Add BuildSelector above image_tag input                                  |
| `deployment-ui/src/api/deploymentApi.ts`         | Add fetchBuilds + deployBuild                                            |

---

## Verification

1. `GET /api/builds/market-tick-data-service?env=dev` → returns list with display names
2. `GET /api/builds/market-tick-data-service?env=dev` in mock mode → falls back to deployed_versions
3. `POST /api/deployments/market-tick-data-service/deploy` with pre-1.0.0 tag → succeeds (no version gate)
4. Open DeployForm in UI → BuildSelector dropdown appears, fetches builds on load
5. Select `0.3.168 @ feat/my-feature` → image_tag field pre-fills with `0.3.168-feat-my-feature`
6. `is_v1: true` build → green `v1` badge; `is_v1: false` → amber `pre-v1` badge
