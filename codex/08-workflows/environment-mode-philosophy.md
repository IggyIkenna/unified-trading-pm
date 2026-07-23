---
doc_type: codex-ssot
title: Environment × Auth × Data Mode Philosophy
summary: >-
  SSOT for UI environment decisions: the three independent axes — deployment env (hostname-derived), Firebase auth DB
  (UAT shares the prod project), and data mode (mock vs real) — plus which runtime badges/banners show on which surface.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-api, unified-trading-system-ui]
scope: [engineer]
tags: [ui, mvp, validation, verification]
related: [./local-dev.md, ./signup-signin-workflow.md]
created: 2026-04-23
authoritative_for:
  [UI environment × auth × data-mode three-axis model (deployment-env / Firebase-auth-db / mock-vs-real)]
referenced_by:
  [/codex/05-infrastructure/firebase-split-topology.md, /codex/14-customer-journeys/demo-ops/staging-demo-setup.md]
owner:
last_reviewed:
code_refs:
---

# Environment × Auth × Data Mode Philosophy

**SSOT for all environment/mock/auth decisions in `unified-trading-system-ui`.**

---

## The Three Axes

Every page in the Unified Trading System UI sits at the intersection of three independent axes. Never conflate them.

### Axis 1 — Deployment Environment

_Where is the app rendering?_

| Environment | Hostname pattern                    | Signals shown                                 |
| ----------- | ----------------------------------- | --------------------------------------------- |
| **dev**     | `localhost`, `127.0.0.1`, `*.local` | `DEV` pill (violet) in platform nav           |
| **staging** | `uat.odum-research.com`             | `STAGING` pill (amber) + SandboxBanner at top |
| **prod**    | `www.odum-research.com`             | `PROD` pill (muted green) — minimal           |

**Derived at runtime from `window.location.hostname`** via `lib/runtime/environment.ts → getDeploymentEnv()`. Never use
a build-time env var for this — it cannot be trusted to match where the app is actually running.

### Axis 2 — Firebase Auth Database

_Which user database is auth backed by?_

| Auth mode | When                                                 | Firebase / GCP project                                                         |
| --------- | ---------------------------------------------------- | ------------------------------------------------------------------------------ |
| **local** | `NEXT_PUBLIC_AUTH_PROVIDER=demo`, localhost only     | None — localStorage personas                                                   |
| **uat**   | UAT build — served at `uat.odum-research.com`        | Same as prod (`central-element-323112`), accessed via the `uat` hosting target |
| **prod**  | Production build — served at `www.odum-research.com` | `central-element-323112`, accessed via the `prod` hosting target               |

**Current state (2026-04-25, corrected):** UAT and prod **share the same Firebase project** (`central-element-323112`)
and therefore the same auth user pool, Firestore, and storage. They are separated only by:

- Hostname: `uat.odum-research.com` vs `www.odum-research.com`
- Cloud Run service: `odum-portal-staging` vs `odum-portal`
- Firebase hosting target: `uat` vs `prod` — both under `targets.central-element-323112.hosting` in `firebase.json`
- Build-time env file: `docker-build.env.uat` vs `docker-build.env.production`

The `.firebaserc` alias `staging: odum-staging` is **leftover misdirection** from an earlier design that anticipated a
separate staging Firebase project. That project was never created and is not needed — UAT IS staging, just on the same
Firebase project. Plan G2.6, originally scoped to provision a separate `odum-staging`, was retargeted 2026-04-25 to "UAT
auth wiring on the shared project".

**The `DemoPlanToggle` blocker is fixed** as of 2026-04-25 by the tier-override refactor in `lib/auth/tier-override.ts`.
The toggle writes a localStorage flag that overlays entitlements on top of the raw authenticated user —
provider-agnostic. Identity (email, uid, org) stays stable; only entitlements flip. Verified across 6 personas
(Desmond + Patrick toggles, Investor, Admin, demo-signals-client, demo-im-reports-only) via end-to-end smoke test on
UAT.

**Migration path to flip UAT to real Firebase** (operator-gated):

1. Operator: confirm `uat.odum-research.com` is in **Authorized domains** in Firebase console → Authentication →
   Settings (project `central-element-323112`). Add it if not.
2. **Operator: provision real Firebase users for every demo email** (`desmondhw@gmail.com`, `patrick@bankelysium.com`,
   `advisor@odum-research.co.uk`, `investor@odum-research.co.uk`, `demo-signals@odum-research.co.uk`,
   `demo-im@odum-research.co.uk`, `admin@odum-research.co.uk`, etc.). The demo personas in `lib/auth/personas.ts` only
   authenticate against the demo provider's local table — `FirebaseAuthProvider.login()` calls
   `signInWithEmailAndPassword` against the real user pool, so every demo email needs a corresponding Firebase user with
   the right password. Use Firebase console → Authentication → Add user, or scripted via `firebase-admin createUser()`.
3. Operator: confirm user-management-api `/authorize` returns the right role + entitlements + org for each demo email
   (it already keys off email; just needs the demo emails seeded into whatever backend store it reads).
4. Agent: copy the 6 `NEXT_PUBLIC_FIREBASE_*` values from `docker-build.env.production` to `docker-build.env.uat`.
5. Agent: change `NEXT_PUBLIC_AUTH_PROVIDER=demo` → `firebase` in `docker-build.env.uat`.
6. Agent: redeploy UAT. Smoke-test sign-in with one of the demo emails. The DemoPlanToggle keeps working unchanged
   because tier-override is localStorage-driven and provider-agnostic.

Until step 2 is done, flipping the env var would break UAT login for every demo persona — they'd hit
`auth/user-not-found` from Firebase. Don't flip prematurely.

For **local dev**: devs never need Firebase credentials. The `demo` auth provider uses personas from
`lib/auth/personas.ts` stored in localStorage. An `admin` persona is pre-seeded in `.env.local` via
`NEXT_PUBLIC_DEV_DEFAULT_PERSONA=admin` so any developer can log in with full access and create sub-users for testing
without touching staging or prod Firebase.

### Axis 3 — Data Source (Backend Connection)

_Is the platform connected to a live backend API?_

| Data mode | `NEXT_PUBLIC_MOCK_API` | What happens                                                                     |
| --------- | ---------------------- | -------------------------------------------------------------------------------- |
| **mock**  | `true`                 | Fetch intercepted client-side; all API calls return fixtures. No backend needed. |
| **real**  | `false`                | Fetch goes to real backend APIs; health is polled every 15s.                     |

**Current state (2026-04-23):** Both prod and UAT have `NEXT_PUBLIC_MOCK_API=true` because the backend
(`unified-trading-api`) is not yet deployed to Cloud Run. This will flip to `false` per-service as backends are
deployed.

---

## Surface Rules — What Shows Where

### Public pages (no backend, always "real")

Routes under `app/(public)/`: homepage, briefings, strategies, regulatory, contact, docs, questionnaire, who-we-are,
our-story, story.

- **Mock Data badge**: NEVER — these pages have no backend; the concept doesn't apply.
- **SandboxBanner**: shows on UAT domain (whole-site, not page-specific).
- **"Preparing demo" / loading text**: NEVER — blank screen during mock handler install.
- **ApiStatusIndicator**: not present (platform nav only).
- **Backend unreachable banner**: not present.

### Platform pages (post-login)

Routes under `app/(platform)/` and `app/(ops)/`.

| Component                             | When shown                                  | Location                  |
| ------------------------------------- | ------------------------------------------- | ------------------------- |
| **RuntimeModeBadge**                  | `MOCK_API=true` OR `AUTH_PROVIDER≠firebase` | Fixed bottom-left         |
| **ApiStatusIndicator**                | Always                                      | Top-right of platform nav |
| **RuntimeModeStrip (backend banner)** | `MOCK_API=false` AND API unreachable        | Sticky below nav          |
| **DebugFooter**                       | `MOCK_API=true`                             | Bottom of screen          |

**If mock mode**: `ApiStatusIndicator` shows `Mock` dot — never `Offline`. No backend is expected; an "offline" status
would be wrong. `RuntimeModeStrip` skips the poll entirely.

**If real mode + backend unreachable**: `RuntimeModeStrip` shows a red sticky banner.

- On dev: "Start it with `bash ...dev-start.sh --all --mode mock`"
- On staging/prod: "Backend API unreachable — live data unavailable. Contact support."

### Admin panel (`(ops)/admin/**`)

Same as platform. No separate mock data layer — auth is Firebase + User Management API which are always real. Only the
general axes apply (env pill, no badge in prod-real).

---

## The SandboxBanner

`components/sandbox-banner.tsx` mounts when `NEXT_PUBLIC_ENVIRONMENT_LABEL=sandbox` (set in
`config/docker-build.env.uat`). It:

- Sticks to the top of every page (public and platform).
- Shows "Demo environment — data is simulated".
- Links to `www.odum-research.com` ("← Live site") for accidental demo-site visitors.
- Is dismissible per session (sessionStorage, not localStorage — re-shows in new tabs).

**Do not add a separate "staging" indicator** — the SandboxBanner already covers UAT. Do not show the SandboxBanner on
prod (env label must be unset in prod build).

---

## Loading State Rule

When `NEXT_PUBLIC_MOCK_API=true`, `lib/providers.tsx` waits for the mock handler to install before rendering children
(to prevent real fetch calls before interception is ready). During this window:

- Show: a blank background div (`aria-busy="true"`).
- Never show: "Preparing demo", "Loading…", or any branded text.

The delay is sub-200ms and invisible to users in practice. Any visible text would be jarring on page load.

---

## Playwright Audit (Quality Gate)

`tests/e2e/environment-mode-audit.spec.ts` enforces all of the above. It runs in CI as part of
`scripts/quality-gates.sh` via:

```bash
npx playwright test tests/e2e/environment-mode-audit.spec.ts --project=chromium
```

Key test groups:

1. Public routes × {no mock badge, no "Mock Data" text, no "Preparing demo", renders < 3s}
2. "Preparing demo" absent site-wide at any load state
3. `ApiStatusIndicator` shows `DEV` on localhost (hostname-derived)
4. `ApiStatusIndicator` shows `Mock` not `Offline` when `MOCK_API=true`
5. `backend-unreachable-banner` absent in mock mode
6. `SandboxBanner` absent when `ENVIRONMENT_LABEL` unset; present + linked when `=sandbox`

---

## File Map

| File                                        | Role                                                      |
| ------------------------------------------- | --------------------------------------------------------- |
| `lib/runtime/environment.ts`                | `getDeploymentEnv()`, `getEnvLabel()`, `isPublicRoute()`  |
| `lib/runtime/data-mode.ts`                  | `isMockDataMode()` — single source for mock flag          |
| `components/runtime-mode-badge.tsx`         | Platform-only mock indicator (bottom-left fixed)          |
| `components/shell/api-status-indicator.tsx` | Env pill + API dot in platform nav top-right              |
| `components/shell/runtime-mode-strip.tsx`   | Backend-unreachable banner below nav                      |
| `components/shell/debug-footer.tsx`         | Persona switcher + Reset Demo (mock mode only)            |
| `components/sandbox-banner.tsx`             | UAT/sandbox top banner with prod link                     |
| `app/layout.tsx`                            | Root — SandboxBanner, StagingGate, ProtocolIndicator only |
| `app/(platform)/layout.tsx`                 | Platform — RequireAuth, UnifiedShell, RuntimeModeBadge    |
| `config/docker-build.env.production`        | Prod build vars (`MOCK_API=true` until backend deployed)  |
| `config/docker-build.env.uat`               | UAT build vars (`ENVIRONMENT_LABEL=sandbox`)              |
| `tests/e2e/environment-mode-audit.spec.ts`  | Playwright QG audit                                       |
