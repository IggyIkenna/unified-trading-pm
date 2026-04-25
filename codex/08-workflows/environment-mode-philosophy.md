---
scope: [engineer]
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

| Auth mode   | When                                                                                                    | Firebase / GCP project                           |
| ----------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| **local**   | `NEXT_PUBLIC_AUTH_PROVIDER=demo`, localhost only                                                        | None — localStorage personas                     |
| **staging** | _Provisioned but not wired_ — `odum-staging` Firebase project exists (alias `staging` in `.firebaserc`) | `odum-staging`                                   |
| **uat**     | UAT build (current) — `NEXT_PUBLIC_AUTH_PROVIDER=demo` in `docker-build.env.uat`                        | None — localStorage personas (same as local-dev) |
| **prod**    | Production build                                                                                        | Firebase prod project (`central-element-323112`) |

**Current state (2026-04-25):** UAT runs the **demo provider** (not the staging Firebase project), even though
`odum-staging` is provisioned. The trade-off:

- **Why demo on UAT:** the `DemoPlanToggle` (Desmond DART Full ⇄ Signals-In, Elysium DeFi ⇄ DeFi Full) calls
  `loginByEmail(pairedPersonaId, "")` — an empty-password persona swap that only works against the demo provider's local
  `PERSONAS` table. Real Firebase auth rejects empty passwords. The toggle is the FOMO/upgrade-preview narrative for
  prospect demos and is core to the staging walkthrough today.
- **What the UAT bundle does host:** advisor accounts on `@odum-research.co.uk` are baked into `PERSONAS` and
  authenticate client-side. The prod login form bounces them to UAT via the per-prospect redirect (see
  `lib/auth/personas.ts::DEMO_PERSONA_EMAILS`).
- **What we'd need to flip UAT to real Firebase:** (a) refactor `DemoPlanToggle` to a **tier-override** pattern in
  localStorage that overlays entitlements on top of a real Firebase user (instead of swapping personas), or (b)
  provision two real Firebase users per prospect (`desmond+full@gmail.com` / `desmond+signals@gmail.com`) and have the
  toggle do `signOut` + `signIn`. Both are non-trivial; deferred until prospect-demo volume justifies the cost.

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
