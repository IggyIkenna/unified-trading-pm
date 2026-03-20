# AI-GENERATED — awaiting user review and promotion

---

type: code
epic: epic-code-completion
status: in_progress
created: 2026-03-20
repo: unified-trading-system-ui
completion_gates:
  code: C4
  deployment: D1
  business: B1
repo_gates:
  - repo: unified-trading-system-ui
    code: C0
    deployment: D0
    business: B0

---

# Fix Auth Sign-In/Logout Flow in unified-trading-system-ui

## Problem Statement

The current auth implementation has several bugs that break the sign-in and logout user experience:

1. **SiteHeader always shows "Sign In" link** — The public header (`components/shell/site-header.tsx`) renders a static
   "Sign In" link with no auth awareness. When a logged-in user navigates to the home page (`/`), they see the "Sign In"
   button even though they are already authenticated. The header should show "Dashboard" or user info instead.

2. **Login page uses `router.push()` instead of full navigation** — The login page (`app/(public)/login/page.tsx`) uses
   Next.js `router.push()` after login. Because `useAuth` initializes state via `useEffect`, the auth state is not
   propagated to already-mounted components. The user lands on the target page but components that check `useAuth()` may
   still see `user = null` until a full page reload occurs.

3. **GlobalNavBar logout is non-functional** — The legacy nav (`components/trading/global-nav-bar.tsx`) has a "Log out"
   dropdown menu item with no `onClick` handler. It does not call `useAuth().logout()` or redirect to `/login`.

4. **No JWT-ready token layer** — Auth is localStorage-only with persona objects. Future JWT integration (FastAPI backend)
   requires a token abstraction layer that the current implementation lacks.

5. **RequireAuth inline login does `window.location.reload()`** — The RequireAuth component reloads the entire page after
   inline login. This works but is a poor UX (full-page flash). The state should propagate without a reload.

## Root Cause Analysis

- `useAuth()` hook uses local `useState` + `useEffect` hydration. Each component that calls `useAuth()` gets its own
  independent copy of auth state. There is no shared context or global subscription — login in one component does not
  notify others.
- `SiteHeader` is a pure presentational component with zero auth awareness.
- `GlobalNavBar` was built before the auth system existed and never wired up.
- The Zustand `auth-store` exists but is unused by the main auth flow (only used by `resetDemo`).

## Solution

### Phase 1: Shared auth state via React Context (this plan)

1. **Create `AuthProvider` context** that wraps the app at the root layout level. All auth state lives in this single
   provider. `useAuth()` becomes a context consumer instead of independent useState.

2. **Make SiteHeader auth-aware** — When logged in, show "Dashboard" link and user avatar instead of "Sign In".

3. **Wire GlobalNavBar logout** — Add `onClick` handler that calls `logout()` from context and redirects to `/login`.

4. **Remove `window.location.reload()` from RequireAuth** — Context propagation makes reload unnecessary.

5. **Login page uses `router.push()` correctly** — Because context updates propagate, `router.push()` works without
   reload.

6. **Add token abstraction** — The auth context stores an optional `token` field. For mock mode, it's a demo token.
   For future JWT mode, it will be the real JWT. API hooks can read the token from context.

### Phase 2: JWT integration (future — not this plan)

- Replace mock login with `POST /api/auth/login` to FastAPI backend
- Store JWT in httpOnly cookie (not localStorage) for security
- Add token refresh logic
- Add `middleware.ts` for server-side auth validation

## Todos

- [x] Create `AuthProvider` React context wrapping root layout
- [x] Refactor `useAuth` hook to be a context consumer
- [x] Make `SiteHeader` auth-aware (show Dashboard/user when logged in)
- [x] Wire `GlobalNavBar` logout to auth context
- [x] Remove `window.location.reload()` from `RequireAuth` inline login
- [x] Fix login page to work with context (no reload needed)
- [x] Add `token` field to auth state for future JWT readiness
- [x] Sync Zustand `auth-store` with context (for `resetDemo` compatibility)
- [ ] Runtime verify: login → navigate → see user state persisted
- [ ] Runtime verify: logout → redirected to /login → sign in button visible
- [ ] Runtime verify: home page shows Dashboard link when logged in

## Files Changed

- `hooks/use-auth.ts` — Refactor to context provider + consumer
- `app/layout.tsx` — Wrap with AuthProvider
- `components/shell/site-header.tsx` — Add auth awareness
- `components/trading/global-nav-bar.tsx` — Wire logout handler
- `components/shell/require-auth.tsx` — Remove window.location.reload()
- `app/(public)/login/page.tsx` — Remove window.location.reload(), use context
