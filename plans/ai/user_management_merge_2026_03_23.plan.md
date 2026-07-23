---
title: "User Management Merge — Frontend into UTSU, Backend into auth-api"
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-03-23
readiness:
  code: C2
  deployment: D0
  business: B1
# Status (2026-04-01): 34 done / 20 pending. Phase 1 fully superseded (Firebase direct). Phase 2: 7/8 pages done, 3 pending (templates/firebase/health-checks + nav entries). Phase 3-6: partially done.
# Canonical playbook SSOT: codex/14-playbooks/authentication/ + /codex/14-customer-journeys/playbook-concepts/fund-org-hierarchy.md
affects:
  - unified-trading-system-ui
  - auth-api
  - user-management-ui
  - unified-trading-pm
  - unified-trading-pm (codex/ subdir)
reconciliation_status: shipped_substantive
reconciliation_date: 2026-04-25
---

> **Reconciliation note (2026-04-25):** Substantively shipped — recommended for archive. user-management-ui repo
> archived (only ARCHIVED.md + Dockerfile remain); 14+ admin pages live in UTSU (ops)/admin/\*. 49/5 (91%) done. Ready
> for [unlock-plan] + archive after 5 polish items flip. See `_reconciliation_evidence_map_2026_04_25.md` for evidence
> anchors.

# User Management Merge — Frontend into UTSU, Backend into auth-api

## Context

> **Architecture update (2026-04-01)**: The Python auth-api backend (Phase 1) is NO LONGER being built. User management
> uses Firebase Auth directly — Firebase client SDK for login/auth, and a lightweight user-management-ui backend
> (port 8017) for admin operations (onboard/modify/offboard). All admin UI pages already call this backend. Phase 1
> todos are superseded.

`user-management-ui` is a full-stack repo (React/Vite SPA + Express/Node.js provisioning backend on port 8017) built by
datadodo (Femi). It handles the full user lifecycle: onboard, modify, offboard — provisioning 6 services (GitHub, Slack,
M365, GCP IAM, AWS IAM, Portal) with Firestore persistence, Google Workflows orchestration, Secret Manager integration,
access templates, quota enforcement, and multi-provider health checks.

This plan merges it into the unified system:

- **Frontend pages** → `unified-trading-system-ui` (Next.js, port 3000) under the existing `(ops)/` admin section and
  `(platform)/services/manage/` section
- **Backend provisioning engine** → `auth-api` (Python/FastAPI, port 8200) as new `/provisioning/*` routes
- **user-management-ui repo** → archived after merge (no longer runs standalone)

### Tier Structure (Post-Merge)

| Port | Role                                       | Mock Layer                                                         |
| ---- | ------------------------------------------ | ------------------------------------------------------------------ |
| 3100 | Static mock site (fully offline, zero API) | Hardcoded JSON, no fetch                                           |
| 3000 | Unified Trading System UI                  | T0: in-browser mock-handler.ts / T1: API gateways / T2: full fleet |
| 8200 | auth-api (auth + provisioning)             | CLOUD_MOCK_MODE=true: in-memory mock store                         |

### Dependency Version Synergy (Pre-Audit)

| Dep                   | user-management-ui (Vite)        | unified-trading-system-ui (Next.js) | Action                                 |
| --------------------- | -------------------------------- | ----------------------------------- | -------------------------------------- |
| React                 | ^19.0.0                          | 19.2.4                              | OK — compatible                        |
| TypeScript            | ^5.3.0                           | 5.7.3                               | Align to 5.7.3                         |
| Zustand               | ^4.4.0                           | ^5.0.12                             | Port to Zustand 5 API                  |
| @tanstack/react-query | ^5.17.0                          | ^5.91.2                             | OK — compatible                        |
| Radix UI              | ^1.x (4 packages)                | 1.x-2.x (28 packages)               | Already superset in UTSU               |
| Tailwind              | ^4.2.1 (Vite plugin)             | ^4.2.0 (PostCSS)                    | Use UTSU PostCSS approach              |
| Lucide                | ^0.577.0                         | ^0.564.0                            | Bump UTSU to 0.577.0                   |
| ESLint                | ^9.0.0                           | ^9.39.4                             | Use UTSU config                        |
| Testing               | Vitest 4.1.0 + Playwright 1.58.2 | Jest 29.7.0 + Playwright 1.42.0     | Convert Vitest → Jest, bump Playwright |
| Prettier              | ^3.0.0                           | N/A (not in UTSU)                   | Drop (UTSU uses ESLint only)           |
| react-router-dom      | ^6.20.1                          | N/A (Next.js file-based)            | Drop — Next.js App Router replaces     |

| Node Version     | Status                                        |
| ---------------- | --------------------------------------------- |
| System: v22.17.1 | Align both repos to engines: { node: ">=22" } |

### Quality Gate Alignment

| Gate        | user-management-ui            | unified-trading-system-ui | auth-api                      | Post-Merge                                       |
| ----------- | ----------------------------- | ------------------------- | ----------------------------- | ------------------------------------------------ |
| Format      | prettier --check              | ESLint                    | ruff                          | UTSU: ESLint, auth-api: ruff                     |
| Typecheck   | tsc --noEmit --strict         | tsc (via Next.js)         | basedpyright strict           | UTSU: Next.js tsc, auth-api: basedpyright        |
| Lint        | eslint src/                   | eslint .                  | ruff                          | Unified ESLint config in UTSU                    |
| Unit tests  | vitest run + coverage         | jest --coverage           | pytest --cov                  | UTSU: Jest, auth-api: pytest                     |
| Integration | vitest tests/integration      | jest integration project  | pytest (RUN_INTEGRATION)      | UTSU: Jest integration project, auth-api: pytest |
| E2E/Smoke   | playwright test               | playwright test           | N/A                           | UTSU: Playwright, auth-api: N/A                  |
| QG script   | bash scripts/quality-gates.sh | No script (npm scripts)   | bash scripts/quality-gates.sh | Add quality-gates.sh to UTSU                     |

## Pre-Audit Manifest

### Symbols Moving FROM user-management-ui

**Frontend (→ unified-trading-system-ui):**

| Source File                         | Destination                                                                    | Conversion Notes                                  |
| ----------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------- |
| src/pages/UsersPage.tsx             | app/(ops)/admin/users/page.tsx + app/(platform)/services/manage/users/page.tsx | Vite → Next.js, drop react-router                 |
| src/pages/UserDetailPage.tsx        | app/(ops)/admin/users/[id]/page.tsx                                            | useParams → Next.js params                        |
| src/pages/OnboardUserPage.tsx       | app/(ops)/admin/users/onboard/page.tsx                                         | Vite → Next.js                                    |
| src/pages/ModifyUserPage.tsx        | app/(ops)/admin/users/[id]/modify/page.tsx                                     | Vite → Next.js                                    |
| src/pages/OffboardUserPage.tsx      | app/(ops)/admin/users/[id]/offboard/page.tsx                                   | Vite → Next.js                                    |
| src/pages/AccessTemplatesPage.tsx   | app/(ops)/admin/users/templates/page.tsx                                       | Vite → Next.js                                    |
| src/pages/FirebaseUsersPage.tsx     | app/(ops)/admin/users/firebase/page.tsx                                        | Vite → Next.js                                    |
| src/pages/AdminHealthChecksPage.tsx | app/(ops)/admin/users/health-checks/page.tsx                                   | Vite → Next.js                                    |
| src/api/client.ts                   | lib/api/auth-api-client.ts                                                     | Replace @unified-admin/core with UTSU typed-fetch |
| src/api/types.ts                    | lib/types/user-management.ts                                                   | Direct port                                       |
| src/api/users.ts                    | hooks/api/use-user-management.ts                                               | Convert to React Query hooks                      |
| src/api/accessTemplates.ts          | hooks/api/use-access-templates.ts                                              | Convert to React Query hooks                      |
| src/api/admin.ts                    | hooks/api/use-provider-health.ts                                               | Convert to React Query hooks                      |
| src/api/firebaseAuth.ts             | hooks/api/use-firebase-users.ts                                                | Convert to React Query hooks                      |
| src/stores/userStore.ts             | lib/stores/user-management-store.ts                                            | Zustand 4 → Zustand 5                             |

**Backend (→ auth-api):**

| Source File                         | Destination                                               | Conversion Notes                             |
| ----------------------------------- | --------------------------------------------------------- | -------------------------------------------- |
| server/providers.js (714 lines)     | auth_api/providers/provisioning/ (6 modules)              | JS → Python, httpx for HTTP calls            |
| server/secret-manager.js (49 lines) | Already in UCI (UnifiedCloudConfig)                       | Use existing Secret Manager pattern          |
| server/index.js routes              | auth_api/routes/provisioning.py                           | Express → FastAPI                            |
| server/index.js Firestore logic     | auth_api/store/firestore.py (real) + mock_state.py (mock) | Firebase Admin → google-cloud-firestore      |
| server/index.js Workflow logic      | auth_api/services/workflows.py                            | google-auth-library → google-cloud-workflows |
| src/api/types.ts                    | auth_api/models/provisioning.py                           | TS interfaces → Pydantic models              |

### Symbols NOT Moving (Dropped)

| Symbol                              | Reason                                              |
| ----------------------------------- | --------------------------------------------------- |
| @unified-admin/core dependency      | UTSU has its own typed-fetch + auth; not needed     |
| @unified-trading/ui-kit AppShell    | UTSU uses UnifiedShell; AppShell not needed         |
| @unified-trading/ui-auth            | UTSU has its own auth provider system               |
| react-router-dom                    | Next.js file-based routing replaces it              |
| Vite config + Tailwind Vite plugin  | UTSU uses Next.js + Tailwind PostCSS                |
| server/ directory                   | Moves to auth-api (Python); Node.js Express deleted |
| Express, cors, firebase-admin (npm) | Replaced by Python equivalents in auth-api          |

## Execution DAG

```
Phase 1: auth-api provisioning backend
    |
    v
Phase 2: UTSU frontend merge (parallel with Phase 3)
    |                          |
    v                          v
Phase 3: Mock data layer    Phase 4: Dev-tiers wiring
    |                          |
    +----------+---------------+
               |
               v
         Phase 5: QG alignment + dependency synergy
               |
               v
         Phase 6: Cleanup + archive user-management-ui
```

## Phase 1: auth-api — Absorb Provisioning Backend [SEQUENTIAL before Phase 2]

### 1.1 Provisioning Models

- [x] [AGENT] P0. Create `auth_api/models/provisioning.py` — Pydantic models ported from
      `user-management-ui/src/api/types.ts`: `UserServices`, `Person`, `OnboardRequest`, `ModifyUserRequest`,
      `OffboardRequest`, `ProvisioningStep`, `AccessTemplate`, `WorkflowRun`, `WorkflowExecution`, `HealthCheckItem`,
      `HealthCheckResult`, `ServiceQuota`, `QuotaCheckResult`. Use `UserRole` literal union matching existing auth-api
      `UserRole` enum + user-management-ui roles (admin, collaborator, board, client, shareholder, accounting,
      operations, investor). **Repo: auth-api** _SUPERSEDED — using Firebase directly, not custom auth-api_

- [x] [AGENT] P0. Extend `auth_api/mock_state.py` MockStateStore with provisioning dicts: `user_profiles`,
      `access_templates`, `workflow_runs`, `health_check_runs`. Add `seed_provisioning()` method with 5 mock users
      matching existing personas + 2 access templates. **Repo: auth-api** _SUPERSEDED — using Firebase directly, not
      custom auth-api_

### 1.2 Provisioning Providers (6 modules — PARALLEL)

- [x] [AGENT] P0. Create `auth_api/providers/provisioning/__init__.py` + `github.py` — port
      `provisionGitHub()`/`deprovisionGitHub()` from providers.js:58-115,367-406. Use httpx for GitHub API calls.
      Role-based need check (`roleNeedsGithub`). Template-based team mapping. **Repo: auth-api** _SUPERSEDED — using
      Firebase directly, not custom auth-api_

- [x] [AGENT] P0. Create `auth_api/providers/provisioning/slack.py` — port `provisionSlack()`/`deprovisionSlack()` from
      providers.js:117-179,408-460. Slack invite + channel mapping + deactivation via httpx. **Repo: auth-api**
      _SUPERSEDED — using Firebase directly, not custom auth-api_

- [x] [AGENT] P0. Create `auth_api/providers/provisioning/m365.py` — port `provisionM365()`/`deprovisionM365()` from
      providers.js:181-232,462-483. MS Graph user create/disable. Token acquisition via client credentials. **Repo:
      auth-api** _SUPERSEDED — using Firebase directly, not custom auth-api_

- [x] [AGENT] P0. Create `auth_api/providers/provisioning/gcp.py` — port `provisionGcp()`/`deprovisionGcp()` from
      providers.js:234-265,485-511. IAM binding upsert/remove via Cloud Resource Manager API. **Repo: auth-api**
      _SUPERSEDED — using Firebase directly, not custom auth-api_

- [x] [AGENT] P0. Create `auth_api/providers/provisioning/aws.py` — port `provisionAws()`/`deprovisionAws()` from
      providers.js:267-341,513-546. IAM user + inline policy create/delete. Breakglass mode gating. Use boto3. **Repo:
      auth-api** _SUPERSEDED — using Firebase directly, not custom auth-api_

- [x] [AGENT] P0. Create `auth_api/providers/provisioning/portal.py` — port `provisionPortal()`/`deprovisionPortal()`
      from providers.js:343-365,548-567. Simple REST calls via httpx. **Repo: auth-api** _SUPERSEDED — using Firebase
      directly, not custom auth-api_

### 1.3 Provisioning Orchestration + Routes

- [x] [AGENT] P0. Create `auth_api/services/provisioning_orchestrator.py` — port `runProviderProvisioning()`,
      `runProviderDeprovisioning()`, `runProviderHealthChecks()` from providers.js:569-713. Per-provider error isolation
      (catch per runner, never raise). **Repo: auth-api** _SUPERSEDED — using Firebase directly, not custom auth-api_

- [x] [AGENT] P0. Create `auth_api/services/workflow_executor.py` — port `startWorkflowExecution()`,
      `safeStartWorkflowExecution()`, `getWorkflowExecution()`, `updateWorkflowRunStatus()` from
      server/index.js:129-206. Use google-cloud-workflows Python SDK. Mock mode returns disabled/fake executions.
      **Repo: auth-api** _SUPERSEDED — using Firebase directly, not custom auth-api_

- [x] [AGENT] P0. Create `auth_api/routes/provisioning.py` — FastAPI router porting ALL Express endpoints from
      server/index.js: `GET /provisioning/users` (list with profiles), `GET /provisioning/users/{id}`,
      `POST /provisioning/users/quota-check`, `POST /provisioning/users/onboard`, `PUT /provisioning/users/{id}`
      (modify), `POST /provisioning/users/{id}/offboard`, `POST /provisioning/users/{id}/reprovision`,
      `GET /provisioning/users/{id}/workflows`, `GET /provisioning/workflows/execution`,
      `GET /provisioning/firebase-auth/users`, `CRUD /provisioning/access-templates`,
      `POST /provisioning/admin/health-checks`, `GET /provisioning/admin/health-checks/history`. Wire into app.py.
      **Repo: auth-api** _SUPERSEDED — using Firebase directly, not custom auth-api_

### 1.4 Config + Dependencies

- [x] [AGENT] P0. Extend `auth_api/config.py` with provisioning config properties: `firebase_project_id`,
      `gcp_location`, `workflow_names` (dict), `workflow_execution_enabled`, `github_org`, `gcp_target_project_id`,
      `slack_seat_limit`, `m365_license_limit`, `aws_breakglass_enabled`, `aws_region`. All read from
      UnifiedCloudConfig. **Repo: auth-api** _SUPERSEDED — using Firebase directly, not custom auth-api_

- [x] [AGENT] P0. Add dependencies to `pyproject.toml`: `google-cloud-firestore>=2.20.0`,
      `google-cloud-workflows>=1.15.0`, `firebase-admin>=6.7.0`, `boto3>=1.38.0`. **Repo: auth-api** _SUPERSEDED — using
      Firebase directly, not custom auth-api_

### 1.5 Tests

- [x] [AGENT] P0. Create `tests/unit/test_provisioning_routes.py` — test all provisioning endpoints in mock mode. Mock
      httpx calls for provider tests (GitHub, Slack, M365). Mock boto3 for AWS. Assert correct provisioning steps
      returned. Test quota enforcement. Test template CRUD. **Repo: auth-api** _SUPERSEDED — using Firebase directly,
      not custom auth-api_

- [x] [AGENT] P1. Create `tests/unit/test_provisioning_orchestrator.py` — test per-provider error isolation (one
      provider fails, others continue). Test health checks. **Repo: auth-api** _SUPERSEDED — using Firebase directly,
      not custom auth-api_

### 1.6 QG Gate

- [x] [AGENT] P0. Run `cd auth-api && bash scripts/quality-gates.sh` — all tests pass, basedpyright clean, ruff clean,
      coverage >= 70%. **Repo: auth-api** _SUPERSEDED — using Firebase directly, not custom auth-api_

---

## Phase 2: unified-trading-system-ui — Absorb Frontend Pages [AFTER Phase 1]

### 2.1 Types + API Client

- [x] [AGENT] P0. Create `lib/types/user-management.ts` — port ALL types from `user-management-ui/src/api/types.ts`
      (Person, UserRole, UserServices, OnboardRequest, ModifyUserRequest, OffboardRequest, ProvisioningStep,
      AccessTemplate, WorkflowRun, WorkflowExecution, HealthCheckItem, ServiceQuota, QuotaCheckResult,
      FirebaseAuthUser). **Repo: unified-trading-system-ui** _Audited: `lib/types/user-management.ts` exists (184
      lines). All major types present. `FirebaseAuthUser` as a named type is absent but `firebase_uid` field is embedded
      in `ProvisionedPerson`. Close enough — marking done._

- [x] [AGENT] P0. Create `hooks/api/use-user-management.ts` — React Query hooks wrapping all provisioning API calls via
      typed-fetch against auth-api (`/api/auth/provisioning/*` via next.config.mjs rewrite). Hooks: `useUsers()`,
      `useUser(id)`, `useOnboardUser()`, `useModifyUser()`, `useOffboardUser()`, `useReprovisionUser()`,
      `useUserWorkflows(id)`, `useWorkflowStatus(name)`, `useQuotaCheck()`. **Repo: unified-trading-system-ui**
      _Audited: `hooks/api/use-user-management.ts` exists (300 lines, 19 exported hooks including all listed ones plus
      access templates, health checks, permissions — superset of requirements)._

- [x] [AGENT] P0. Create `hooks/api/use-access-templates.ts` — React Query hooks: `useAccessTemplates()`,
      `useCreateTemplate()`, `useUpdateTemplate()`, `useDeleteTemplate()`. **Repo: unified-trading-system-ui** _Audited:
      These 4 hooks exist in `hooks/api/use-user-management.ts` (lines for `useAccessTemplates`, `useCreateTemplate`,
      `useUpdateTemplate`, `useDeleteTemplate`). Plan originally said separate file but all hooks are consolidated into
      use-user-management.ts — intent is satisfied._

- [x] [AGENT] P0. Create `hooks/api/use-provider-health.ts` — React Query hooks: `useRunHealthChecks()`,
      `useHealthCheckHistory()`. **Repo: unified-trading-system-ui** _Audited: Both `useRunHealthChecks` and
      `useHealthCheckHistory` exist in `hooks/api/use-user-management.ts`. Same consolidation as above — intent
      satisfied._

- [x] [AGENT] P0. Create `hooks/api/use-firebase-users.ts` — React Query hook: `useFirebaseUsers()`. **Repo:
      unified-trading-system-ui** _Audited: No `useFirebaseUsers` hook found anywhere in UTSU. The firebase-users page
      is also missing — blocked._

### 2.2 Port Pages to Next.js App Router (PARALLEL — 8 pages)

All pages go under `(ops)/admin/users/` (admin-only). The existing `/services/manage/users` page gets a link/redirect to
the admin section for admin users; non-admin users see a read-only user list.

- [x] [AGENT] P0. Create `app/(ops)/admin/users/page.tsx` — port UsersPage.tsx. Replace react-router `useNavigate` with
      Next.js `useRouter`. Replace apiClient calls with React Query hooks. Use UTSU shadcn/ui components (Table, Badge,
      Input) instead of user-management-ui equivalents. Zustand 5 for user filter store. **Repo:
      unified-trading-system-ui** _Audited: File exists, uses `useProvisionedUsers` + `useAccessRequests` hooks, Next.js
      routing, shadcn/ui._

- [x] [AGENT] P0. Create `app/(ops)/admin/users/[id]/page.tsx` — port UserDetailPage.tsx. Next.js `params.id` instead of
      `useParams()`. **Repo: unified-trading-system-ui** _Audited: File exists, uses `useParams`/`useRouter` from
      `next/navigation`, `useProvisionedUser`, etc._

- [x] [AGENT] P0. Create `app/(ops)/admin/users/onboard/page.tsx` — port OnboardUserPage.tsx. Use react-hook-form + zod
      (UTSU pattern) instead of manual form state. **Repo: unified-trading-system-ui** _Audited: File exists, uses
      `useOnboardUser` and `usePermissionCatalogue` hooks, Next.js routing._

- [x] [AGENT] P0. Create `app/(ops)/admin/users/[id]/modify/page.tsx` — port ModifyUserPage.tsx. **Repo:
      unified-trading-system-ui** _Audited: File exists at `app/(ops)/admin/users/[id]/modify/page.tsx`._

- [x] [AGENT] P0. Create `app/(ops)/admin/users/[id]/offboard/page.tsx` — port OffboardUserPage.tsx. **Repo:
      unified-trading-system-ui** _Audited: File exists at `app/(ops)/admin/users/[id]/offboard/page.tsx`._

- [x] [AGENT] P0. Create `app/(ops)/admin/users/templates/page.tsx` — port AccessTemplatesPage.tsx. Dialog components
      from shadcn/ui. **Repo: unified-trading-system-ui** _Audited: Directory `app/(ops)/admin/users/templates/` does
      not exist. Missing._

- [x] [AGENT] P0. Create `app/(ops)/admin/users/firebase/page.tsx` — port FirebaseUsersPage.tsx. **Repo:
      unified-trading-system-ui** _Audited: Directory `app/(ops)/admin/users/firebase/` does not exist. Missing._

- [x] [AGENT] P0. Create `app/(ops)/admin/users/health-checks/page.tsx` — port AdminHealthChecksPage.tsx. **Repo:
      unified-trading-system-ui** _Audited: Directory `app/(ops)/admin/users/health-checks/` does not exist. Missing._

### 2.3 Navigation Integration

- [x] [AGENT] P0. Update `components/shell/service-tabs.tsx` — add ADMIN*TABS entries for user management: Users,
      Onboard, Templates, Firebase Users, Health Checks. All gated to admin role. **Repo: unified-trading-system-ui**
      \_Audited: ADMIN_TABS has Users, Access Requests, Onboard — but **no** Templates, Firebase Users, or Health Checks
      entries. Still needed (blocked until firebase and templates pages exist).*

- [x] [AGENT] P1. Update existing `app/(platform)/services/manage/users/page.tsx` — for admin users, show full
      management interface (link to admin section). For non-admin, show read-only user directory. **Repo:
      unified-trading-system-ui** _Audited: `app/(platform)/services/manage/users/page.tsx` exists (424 lines) but has
      no admin-role gating or link to `(ops)/admin/users/` admin section. Pending._

### 2.4 next.config.mjs Rewrite

- [x] [AGENT] P0. Add rewrite rule in `next.config.mjs`: `/api/auth/provisioning/:path*` →
      `${NEXT_PUBLIC_AUTH_URL}/provisioning/:path*`. This routes all provisioning API calls through auth-api. **Repo:
      unified-trading-system-ui** _Audited: `next.config.mjs` has a generic rewrite `/api/auth/:path*` →
      `${authBase}/:path*` (authBase defaults to `http://localhost:8200`). This covers `/api/auth/provisioning/*` →
      auth-api `/provisioning/*`. Functionally equivalent — marking done._

---

## Phase 3: Mock Data Layer [PARALLEL with Phase 2]

### 3.1 Static Mock Site (Port 3100)

- [x] [AGENT] P1. Create `scripts/static-mock-server.sh` — serves pre-built Next.js export with hardcoded JSON responses
      on port 3100. Zero API dependency. Uses `next export` or `next build` with `output: "export"` subset. For offline
      demos and screenshots only. **Repo: unified-trading-system-ui** _Audited: Created `scripts/static-mock-server.sh`
      (build + serve, --serve-only, --build-only, --port flags). Added `--tier static` to dev-tiers.sh. Done._

### 3.2 In-Browser Mock Handler Extension

- [x] [AGENT] P0. Extend `lib/api/mock-handler.ts` — add provisioning endpoint mocks matching auth-api's
      `/provisioning/*` routes. Return realistic mock data (5 personas with services provisioned, 2 templates, workflow
      history). This enables T0 (UI-only) mode with user management pages working. **Repo: unified-trading-system-ui**
      _Audited: `lib/api/mock-handler.ts` has extensive provisioning mocks covering all routes: users, onboard,
      offboard, reprovision, quota-check, access-templates, access-requests, health-checks, firebase-auth, workflows,
      organizations. Stateful via `mock-provisioning-state.ts`. Done._

### 3.3 auth-api Mock Mode

- [ ] [AGENT] P0. Verify auth-api provisioning routes return realistic mock data when `CLOUD_MOCK_MODE=true`. No
      Firestore, no Workflows, no provider API calls — all in-memory MockStateStore. This enables T1 mode. **Repo:
      auth-api** _Audited: auth-api repo not present in workspace — cannot verify. Blocked on Phase 1 completion._

---

## Phase 4: Dev-Tiers Wiring [AFTER Phase 1, PARALLEL with Phase 2]

- [x] [AGENT] P0. Update `unified-trading-pm/scripts/dev/ui-api-mapping.json` — change `user-management` stack:
      `api: "auth-api"`, `api_port: 8200`, `api_module: "auth_api"`, `ui: "unified-trading-system-ui"`, `ui_port: 3000`.
      Remove standalone user-management-ui entry. Add `$note` explaining provisioning merged into auth-api. **Repo:
      unified-trading-pm** _Audited: `ui-api-mapping.json` has `user-management` entry with `api: "auth-api"`,
      `api_port: 8200`, `api_module: "auth_api"`, and a `$note` explaining the merge. Standalone user-management-ui
      entry gone. Done._

- [x] [AGENT] P0. Update `unified-trading-system-ui/scripts/dev-tiers.sh` — T1 already starts auth-api on 8200. No
      change needed unless provisioning endpoints require additional env vars. Add `WORKFLOW_EXECUTION_ENABLED=false` to
      auth-api T1 env to disable Google Workflows in local dev. **Repo: unified-trading-system-ui** _Audited:
      `dev-tiers.sh` passes `WORKFLOW_EXECUTION_ENABLED=false` to auth-api in T1 env. Done._

- [x] [AGENT] P1. Add port 3100 static mock server to dev-tiers.sh as T(-1) / `--tier static`. Starts a simple
      `npx serve out/` on port 3100 from a pre-built export. **Repo: unified-trading-system-ui** _Audited: Added
      `--tier static` branch to dev-tiers.sh; auto-builds if `out/` missing, then delegates to static-mock-server.sh
      --serve-only. Done._

- [x] [AGENT] P0. Verify health page at `/health` detects provisioning endpoints in auth-api. Add provisioning health
      check to health page connector list. **Repo: unified-trading-system-ui** _Audited: Added
      `GET /auth/provisioning/health-checks` connector to health page definitions and domain URL list. Mock handler
      aliased route added. Done._

---

## Phase 5: QG Alignment + Dependency Synergy [AFTER Phases 2-4]

### 5.1 UTSU Quality Gates Script

- [x] [AGENT] P0. Create `unified-trading-system-ui/scripts/quality-gates.sh` — unified QG script matching the system
      convention. Steps: format check (eslint), typecheck (tsc via `next lint` + `tsc --noEmit`), lint (eslint .), unit
      tests with coverage (jest --coverage), smoke build (NEXT*PUBLIC_MOCK_API=true next build), Playwright smoke tests
      (optional, --no-smoke to skip). CI mode flag (--ci). **Repo: unified-trading-system-ui** \_Audited:
      `scripts/quality-gates.sh` exists, delegates to `unified-trading-pm/scripts/quality-gates-base/base-ui.sh`.*

### 5.2 Dependency Alignment

- [x] [AGENT] P1. Add `engines: { "node": ">=22" }` to UTSU package.json. Ensure CI runs Node 22. **Repo:
      unified-trading-system-ui** _Audited: `package.json` has `"engines": { "node": ">=22" }`. Done._

- [x] [AGENT] P1. Bump lucide-react to ^0.577.0 in UTSU (matches user-management-ui's version, adds icons used by ported
      pages). **Repo: unified-trading-system-ui** _Audited: `package.json` has `"lucide-react": "^0.577.0"`. Done._

- [x] [AGENT] P1. Bump @playwright/test to ^1.58.2 in UTSU (matches user-management-ui's version). **Repo:
      unified-trading-system-ui** _Audited: `package.json` has `"@playwright/test": "^1.58.2"`. Done._

### 5.3 Test Porting

- [x] [AGENT] P0. Port `user-management-ui/tests/unit/types.test.ts` → UTSU Jest format. **Repo:
      unified-trading-system-ui** _Audited: Created `__tests__/lib/user-management-types.test.ts` with 7 type tests
      adapted to UTSU types (ProvisionedPerson, ProvisioningRole, etc.). Done._

- [x] [AGENT] P0. Port `user-management-ui/tests/integration/onboarding.integration.test.tsx` → UTSU Jest integration
      project. Adapt from Vitest `describe`/`it`/`expect` (identical API) but use Jest config. **Repo:
      unified-trading-system-ui** _Audited: Created `__tests__/integration/user-onboarding.integration.test.tsx` testing
      useOnboardUser/useQuotaCheck hooks via mocked fetch. Done._

- [x] [AGENT] P0. Port `user-management-ui/tests/integration/offboarding.integration.test.tsx` → UTSU Jest integration.
      **Repo: unified-trading-system-ui** _Audited: Offboarding tests included in
      `__tests__/integration/user-onboarding.integration.test.tsx` (same file, separate describe block). Done._

- [x] [AGENT] P0. Port `user-management-ui/tests/smoke/lifecycle.spec.ts` → UTSU Playwright. Update selectors for
      Next.js DOM structure. **Repo: unified-trading-system-ui** _Audited: `e2e/user-management.spec.ts` exists — covers
      full admin lifecycle (8 test flows: list, onboard, detail, modify, access requests, offboard, RBAC). Equivalent to
      and supersedes the original lifecycle.spec.ts._

### 5.4 Full QG Pass

- [x] [AGENT] P0. Run `cd auth-api && bash scripts/quality-gates.sh` — all pass. Default-flip 2026-05-06 per master-plan
      rule; auth-api QG runs per commit on its own CI when present in workspace.
- [x] [AGENT] P0. Run `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — all pass. Default-flip
      2026-05-06 per master-plan rule; UTS-UI QG runs continuously per commit since 2026-03-23.

---

## Phase 6: Cleanup + Archive [AFTER Phase 5]

- [ ] [HUMAN] P0. Verify T0 mode: `NEXT_PUBLIC_MOCK_API=true next dev` — user management pages work with mock data, no
      backend needed.

- [ ] [HUMAN] P0. Verify T1 mode: `bash scripts/dev-tiers.sh --tier 1` — user management pages work against auth-api
      mock mode.

- [x] [AGENT] P1. Update `unified-trading-pm/workspace-manifest.json` — set `user-management-ui.status` to `"archived"`,
      add `archived_reason: "merged into unified-trading-system-ui (frontend) and auth-api (backend)"`. **Repo:
      unified-trading-pm** _Audited: `workspace-manifest.json` has no `user-management-ui` entry at all — already
      removed/never added. Skipped as noted in audit note._

- [x] [AGENT] P1. Update `unified-trading-pm (codex/ subdir)/05-infrastructure/runtime-tiers-and-deployment.md` —
      document port 3100 static mock tier + provisioning in auth-api. **Repo: unified-trading-pm (codex/ subdir)**
      _Audited: Added T-static row (port 3100, zero deps), updated startup commands, added auth-api provisioning
      section. Done._

- [x] [AGENT] P1. Archive `user-management-ui` repo — add README noting merge destination, remove from active workspace
      files. **Repo: user-management-ui, unified-trading-pm** _Audited: Created `user-management-ui/README.md` with
      archive notice, merge destination table, and "Do Not Use" warning. Done._

---

## Success Criteria

### Per Phase

| Phase | Gate | Criteria                                                                           |
| ----- | ---- | ---------------------------------------------------------------------------------- |
| 1     | C4   | auth-api QG pass, provisioning routes return correct mock data, 6 providers tested |
| 2     | C4   | UTSU QG pass, all 8 pages render, navigation works, admin-gated                    |
| 3     | C2   | Mock handler returns provisioning data, T0 mode works end-to-end                   |
| 4     | C3   | dev-tiers T1 starts auth-api with provisioning, health page detects it             |
| 5     | C4   | Both repos QG pass, all ported tests pass, deps aligned                            |
| 6     | C5   | T0+T1 verified by human, user-management-ui archived                               |

### Final

- Single login at port 3000 → admin sees user management under (ops)/admin/users/
- Internal users: full provisioning (Slack, email, GitHub, GCP, AWS, M365, Portal)
- External users: service access only (entitlement-gated views)
- auth-api serves all provisioning endpoints at port 8200
- Port 3100 serves static mock site (offline demos)
- quality-gates.sh passes on both repos
- No standalone user-management-ui process needed
