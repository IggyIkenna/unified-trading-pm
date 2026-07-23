---
title: "Environment × Auth × Data Mode Philosophy — Audit & Enforcement"
id: environment_mode_philosophy_audit_2026_04_23
status: active
priority: P0
created: 2026-04-23
feature_branch: live-defi-rollout
locked_by: live-defi-rollout
locked_since: 2026-04-23
---

# Environment × Auth × Data Mode Philosophy — Audit & Enforcement

## Problem

The Unified Trading System UI conflates three independent axes under a single `NEXT_PUBLIC_MOCK_API` flag. This causes:

1. "Mock Data" badge and "Preparing demo…" text appearing on public marketing pages (`www.odum-research.com`) where
   there is no backend — these pages are always real, the badge is misleading.
2. No formal separation between Dev / Staging / Prod environment signals and data-layer mock state.
3. No Playwright audit enforcing these invariants in quality gates.

## Three Independent Axes (Canonical Philosophy)

```
Axis 1 — ENVIRONMENT (where is the app rendering?)
  dev      → localhost, local Firebase cache, full mock data
  staging  → uat.odum-research.com, Firebase staging project, Sandbox banner
  prod     → www.odum-research.com, Firebase prod project, real data where available

Axis 2 — FIREBASE AUTH (which auth database?)
  local    → demo-auth personas stored in localStorage (dev only)
  staging  → Firebase project: central-element-staging-*
  prod     → Firebase project: central-element-323112

Axis 3 — DATA (is the platform connected to a backend?)
  mock     → NEXT_PUBLIC_MOCK_API=true, fetch intercepted, no backend calls
  real     → NEXT_PUBLIC_MOCK_API=false, backend API must be reachable
```

### What belongs where

| Surface                                            | Environment signal                 | Mock badge          | "Backend unreachable" banner       |
| -------------------------------------------------- | ---------------------------------- | ------------------- | ---------------------------------- |
| Public marketing (homepage, briefings, strategies) | none                               | NEVER               | n/a                                |
| UAT public pages                                   | SandboxBanner (top, links to prod) | NEVER               | n/a                                |
| Platform (post-login, any env)                     | Env pill top-right nav             | bottom-left if mock | red banner top if real+unreachable |
| Admin panel                                        | same as platform                   | same                | same                               |

### Loading state rule

When `NEXT_PUBLIC_MOCK_API=true`, the mock handler installs client-side before any fetch call. The loading gate must
show a BLANK screen — no text, no branding. "Preparing demo…" was confusing on public pages; replaced with empty div.

---

## Implementation Plan

### Phase 1 — Immediate fixes (DONE 2026-04-23)

- [x] [AGENT] P0. `lib/providers.tsx`: Replace "Preparing demo…" text with blank loading div.
- [x] [AGENT] P0. `app/layout.tsx`: Remove `RuntimeModeBadge` — public pages must never show it.
- [x] [AGENT] P0. `app/(platform)/layout.tsx`: Add `RuntimeModeBadge` — platform only.

### Phase 2 — Codex documentation

- [ ] [AGENT] P1. Write `unified-trading-pm/codex/08-workflows/environment-mode-philosophy.md` capturing the three-axis
      model, which surface shows what, and the local-dev Firebase cache pattern.

### Phase 3 — `lib/runtime/` environment helpers

- [ ] [AGENT] P1. Create `lib/runtime/environment.ts` exporting:
  - `getDeploymentEnv(): "dev" | "staging" | "prod"` — detects via hostname (`localhost` → dev, `uat.` → staging, else →
    prod)
  - `getAuthMode(): "local" | "staging" | "prod"` — derives from `NEXT_PUBLIC_AUTH_PROVIDER` + hostname
  - `isPublicPage(pathname: string): boolean` — returns true for all routes under `(public)` layout
- [ ] [AGENT] P1. Update `RuntimeModeBadge` to import `getDeploymentEnv()` as a defensive guard — even if the badge
      accidentally lands in root layout again, it renders null on non-platform paths.
- [ ] [AGENT] P1. Update `lib/runtime/data-mode.ts` with a new export: `isPublicOnlyPage()` using the same routing
      logic.

### Phase 4 — Env pill in platform top-right nav

- [ ] [AGENT] P1. Add `EnvPill` component: amber "DEV" / orange "STAGING" / hidden on PROD.
- [ ] [AGENT] P1. Wire into `UnifiedShell` header row (top-right, alongside existing DEV|API pill).
- [ ] [AGENT] P1. Ensure pill reads `getDeploymentEnv()` — hostname-derived, not env-var-derived, so it always reflects
      where the user IS, not what the build was told.

### Phase 5 — Backend unreachable banner (platform only)

- [ ] [AGENT] P2. When `NEXT_PUBLIC_MOCK_API=false` and `/api/health` is unreachable: show sticky red banner at top of
      platform ("Backend API unreachable — data may be stale").
- [ ] [AGENT] P2. Banner must NOT appear when `NEXT_PUBLIC_MOCK_API=true` (mock mode = intentional, no backend
      expected).
- [ ] [AGENT] P2. Wire into `UnifiedShell` or a new `BackendHealthBanner` component rendered in platform layout.

### Phase 6 — Local dev Firebase auth (no-credential dev)

- [ ] [AGENT] P2. When `NEXT_PUBLIC_AUTH_PROVIDER=demo`, skip Firebase SDK entirely — use localStorage personas.
- [ ] [AGENT] P2. Pre-seed `admin` persona as the default local-dev user (stored in `.env.local` as
      `NEXT_PUBLIC_DEV_DEFAULT_PERSONA=admin`).
- [ ] [AGENT] P2. Document in `/codex/08-workflows/local-dev.md`: devs can login as any persona → create sub-users →
      test admin workflow without affecting prod/staging Firebase.

### Phase 7 — Playwright audit tests (quality gate enforced)

- [ ] [AGENT] P0. Create `tests/e2e/environment-mode-audit.spec.ts` with the following assertions:

  ```
  Public pages (/ /investment-management /platform /regulatory /contact /briefings/*)
  ├── no element matches [data-testid="runtime-mode-badge"]
  ├── no element contains text "Mock Data" or "Preparing demo"
  └── page renders without blank-screen timeout (< 3s)

  UAT environment (when ENVIRONMENT_LABEL=sandbox)
  ├── SandboxBanner visible
  ├── SandboxBanner contains link to www.odum-research.com
  └── no "Mock Data" badge on public pages

  Platform pages (post-login via demo auth)
  ├── when MOCK_API=true: RuntimeModeBadge visible with text "Mock Data"
  ├── when MOCK_API=true: DebugFooter visible
  └── when MOCK_API=false + backend down: BackendHealthBanner visible (Phase 5)
  ```

- [ ] [AGENT] P0. Add `playwright-environment-audit` step to `scripts/quality-gates.sh` running
      `npx playwright test tests/e2e/environment-mode-audit.spec.ts --project=chromium`.
- [ ] [AGENT] P0. Ensure tests run with `NEXT_PUBLIC_MOCK_API=true` for the mock assertions and a separate config with
      `NEXT_PUBLIC_MOCK_API=false` for the real-mode assertions.

### Phase 8 — Admin panel audit

- [ ] [AGENT] P2. Verify admin panel (`(ops)/admin/**`) uses only Firebase + User Management API — no mock data layer.
- [ ] [AGENT] P2. Add Playwright test: admin pages load without "Mock Data" badge (admin has its own auth, no
      `NEXT_PUBLIC_MOCK_API` dependency).

---

## Success Criteria

- [x] C1. `www.odum-research.com` homepage: no "Mock Data" badge, no "Preparing demo" text at any viewport width.
- [ ] C2. `uat.odum-research.com`: SandboxBanner visible on all pages with link to prod.
- [ ] C3. Platform dashboard: "Mock Data" badge visible (bottom-left) when `MOCK_API=true`.
- [ ] C4. Playwright audit passes in quality gates with zero violations on all 7 public path categories.
- [ ] C5. Codex doc merged and referenced in `CLAUDE.md` environment section.
- [ ] C6. Local dev: `NEXT_PUBLIC_AUTH_PROVIDER=demo` bypasses Firebase, admin persona pre-seeded.

---

## Pre-Audit Manifest (blast radius)

| File                                       | Change                        | Phase |
| ------------------------------------------ | ----------------------------- | ----- |
| `lib/providers.tsx`                        | "Preparing demo…" → blank div | 1 ✓   |
| `app/layout.tsx`                           | Remove RuntimeModeBadge       | 1 ✓   |
| `app/(platform)/layout.tsx`                | Add RuntimeModeBadge          | 1 ✓   |
| `lib/runtime/environment.ts`               | New file                      | 3     |
| `components/runtime-mode-badge.tsx`        | Defensive path guard          | 3     |
| `components/shell/unified-shell.tsx`       | Add EnvPill to header         | 4     |
| `components/env-pill.tsx`                  | New component                 | 4     |
| `components/backend-health-banner.tsx`     | New component                 | 5     |
| `app/(platform)/layout.tsx`                | Wire BackendHealthBanner      | 5     |
| `hooks/use-auth.tsx`                       | Skip Firebase when demo       | 6     |
| `tests/e2e/environment-mode-audit.spec.ts` | New test file                 | 7     |
| `scripts/quality-gates.sh`                 | Add playwright step           | 7     |
