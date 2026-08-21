---
doc_type: plan
title: unified-trading-ui-auth — Provider-Agnostic OAuth 2.0 PKCE Refactor
summary:
status: completed
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-09
overview: 'unified-trading-ui-auth is currently hardwired to Google''s implicit-flow id_token (no PKCE, no

  refresh). batch-audit-ui uses @okta/okta-auth-js + @okta/okta-react — a provider not used by any

  other UI and now being dropped. This plan refactors unified-trading-ui-auth to export a

  provider-agnostic interface (AuthProvider, useAuthToken, RequireAuth, authFetch) backed by two

  concrete adapters: GoogleAdapter (wraps existing GoogleAuth.ts logic) and CognitoAdapter (AWS

  Cognito Hosted UI, OAuth 2.0 PKCE — authorization_code grant with PKCE, token refresh via

  refresh_token grant). batch-audit-ui drops @okta/* deps and wires in the CognitoAdapter via

  AuthProvider. The three existing consumers (execution-analytics-ui, settlement-ui,

  trading-analytics-ui) migrate from the direct GoogleAuth.ts call-site API to the new

  AuthProvider + config pattern. No @okta/* dependencies anywhere in the workspace after this plan

  completes. Package version bumped (minor) for new public API.

  '
completed: 2026-03-10
updated: 2026-03-10
isProject: false
todos:
- {id: audit-current-api-surface, content: 'Audit the current public API of unified-trading-ui-auth before touching any code. Record every exported symbol from src/index.ts and every import site in the three consumer UIs plus batch-audit-ui. Specifically: (a) execution-analytics-ui imports RequireAuth, clearToken, getStoredToken from App.tsx; getStoredToken from src/api/client.ts; initiateGoogleLogin from src/pages/Login.tsx; (b) settlement-ui imports RequireAuth, clearToken, getStoredToken from App.tsx; initiateGoogleLogin from src/pages/Login.tsx; getStoredToken from src/pages/Positions.tsx; (c) trading-analytics-ui imports RequireAuth, initiateGoogleLogin, getStoredToken, clearToken from App.tsx; (d) batch-audit-ui imports nothing from @unified-trading/ui-auth — it uses @okta/* only. Confirm all symbols are covered in the migration plan before writing any code.', status: done}
- {id: design-provider-agnostic-types, content: 'Design the provider-agnostic TypeScript interfaces before writing implementation code. Create src/types.ts in unified-trading-ui-auth with: (1) Provider enum type — `"google" | "cognito"`; (2) AuthProviderConfig interface — `provider: "google" | "cognito"`, `clientId: string`, `redirectUri: string`, `scopes: string[]`, `cognitoDomain?: string` (required when provider is "cognito" — the Cognito Hosted UI base URL e.g. "https://my-domain.auth.us-east-1.amazoncognito.com"), `googleClientId?: string` (alias for clientId when provider is "google" — optional convenience field), `skipAuth?: boolean` (dev bypass); (3) AuthUser interface — `sub: string`, `email: string`, `name?: string`, `picture?: string`; (4) AuthState interface — `isAuthenticated: boolean`, `isLoading: boolean`, `token: string | null`, `user: AuthUser | null`; (5) AuthAdapter interface (internal) — `login(): void`, `logout(): void`, `handleCallback(): Promise<string | null>`, `getToken():
    string | null`, `refreshToken(): Promise<string | null>`. No `any` types. Export AuthProviderConfig, AuthUser, AuthState from index.ts (not AuthAdapter — internal only).', status: done}
- {id: implement-google-adapter, content: 'Implement src/adapters/GoogleAdapter.ts in unified-trading-ui-auth. This is a refactor of the existing src/GoogleAuth.ts — do NOT delete GoogleAuth.ts yet (backward compat kept until consumers migrate). GoogleAdapter wraps the existing implicit-flow logic as a class implementing the internal AuthAdapter interface from src/types.ts. Methods: `login()` — calls `initiateGoogleLogin()` from GoogleAuth.ts (reuse existing implementation, do not re-implement); `logout()` — calls `clearToken()` from GoogleAuth.ts; `handleCallback()` — parses `id_token` from URL hash fragment (same logic as RequireAuth.tsx lines 31-41), stores in sessionStorage via `sessionStorage.setItem("google_id_token", idToken)`, returns the token; `getToken()` — calls `getStoredToken()` from GoogleAuth.ts; `refreshToken()` — Google implicit flow has no refresh token; return `Promise.resolve(null)`. No new external dependencies. Full TypeScript strict typing, no `any`. Export `GoogleAdapter`
    class (not default export — named).', status: done}
- {id: implement-cognito-adapter, content: 'Implement src/adapters/CognitoAdapter.ts in unified-trading-ui-auth. Implements the internal AuthAdapter interface for AWS Cognito Hosted UI with OAuth 2.0 PKCE (authorization_code grant). No @okta/* dependencies. No new npm packages — use only Web Crypto API (available in all modern browsers) for PKCE. Implementation requirements: (1) PKCE helpers — `generateCodeVerifier(): string` using `crypto.getRandomValues` (43-128 char URL-safe random string); `generateCodeChallenge(verifier: string): Promise<string>` using `crypto.subtle.digest("SHA-256", ...)` then base64url-encode without padding; (2) Storage keys — `"cognito_access_token"`, `"cognito_refresh_token"`, `"cognito_pkce_verifier"` in sessionStorage; (3) `login()` — generates verifier, stores in sessionStorage, computes challenge, redirects to `{cognitoDomain}/oauth2/authorize` with params: `response_type=code`, `client_id`, `redirect_uri`, `scope` (space-joined), `code_challenge`, `code_challenge_method=S256`;
    (4) `handleCallback()` — reads `code` from URL search params, reads stored verifier, POSTs to `{cognitoDomain}/oauth2/token` with `grant_type=authorization_code`, `client_id`, `redirect_uri`, `code`, `code_verifier` (application/x-www-form-urlencoded), stores `access_token` + `refresh_token` in sessionStorage, clears verifier, returns access_token; (5) `getToken()` — reads `"cognito_access_token"` from sessionStorage; (6) `refreshToken()` — POSTs to `{cognitoDomain}/oauth2/token` with `grant_type=refresh_token`, `client_id`, `refresh_token`, updates stored access_token, returns new access_token or null on failure; (7) `logout()` — clears both storage keys, redirects to `{cognitoDomain}/logout?client_id=...&logout_uri={redirectUri}`. Export `CognitoAdapter` class (named). Full TypeScript strict typing, no `any`. The `cognitoDomain` is passed via constructor from AuthProviderConfig.', status: done}
- {id: implement-auth-context, content: 'Implement src/AuthContext.tsx in unified-trading-ui-auth. Creates a React context that holds AuthState and dispatcher functions. Requirements: (1) `AuthContext` — `React.createContext` with default value `null` (context is always provided by AuthProvider, null-default avoids a fake default state); (2) `AuthProvider` component — accepts `config: AuthProviderConfig` + `children: ReactNode`; instantiates the correct adapter (GoogleAdapter or CognitoAdapter) based on `config.provider`; on mount runs `handleCallback()` if URL contains `code` (Cognito) or `id_token` in hash (Google) to finalize login; checks sessionStorage for existing token and populates AuthState.isAuthenticated; exposes `login`, `logout`, `token`, `user`, `isAuthenticated`, `isLoading` via context value; (3) `useAuth()` internal hook — reads context, throws if used outside AuthProvider; (4) Dev bypass — if `config.skipAuth === true`, set `isAuthenticated: true`, `token: "dev_token"`
    immediately without adapter call. No `import.meta.env` access inside this file — skipAuth comes only from config prop (callers pass it from their own env). Export `AuthProvider` (named), `useAuth` (named, internal use by hooks and RequireAuth).', status: done}
- {id: refactor-use-auth-token-hook, content: 'Refactor src/useAuthToken.ts in unified-trading-ui-auth to the new provider-agnostic API. New signature: `useAuthToken(): { token: string | null; user: AuthUser | null; isAuthenticated: boolean }`. Implementation calls `useAuth()` from AuthContext (reads from React context — no direct sessionStorage access). The return value expands on the current `string | null` return: adds `user` and `isAuthenticated` fields. For backward compatibility, keep the old `useAuthToken` calling convention working: if a consumer only destructures `token`, it still works. The old direct sessionStorage listener (`window.addEventListener("storage", handler)`) is removed — state management is now owned by AuthContext. Export remains `useAuthToken` from index.ts. Add JSDoc comment: `@deprecated Direct token import (getStoredToken) — migrate callers to useAuthToken from AuthProvider context.`', status: done}
- {id: refactor-require-auth-component, content: 'Refactor src/RequireAuth.tsx in unified-trading-ui-auth. New implementation reads auth state from `useAuth()` context (from AuthContext.tsx) instead of calling `getStoredToken()` + `initiateGoogleLogin()` directly. Props interface unchanged: `children: ReactNode`, `callbackPath?: string`, `loginPath?: string`. Behavior: (1) while `isLoading: true` render `<div>Loading...</div>`; (2) if `isAuthenticated: true` render `children`; (3) if `isAuthenticated: false` and `loginPath` provided, call `navigate(loginPath)`; (4) if `isAuthenticated: false` and no `loginPath`, call `auth.login()` (provider-agnostic — triggers Google or Cognito flow depending on AuthProvider config). Remove all direct references to `getStoredToken`, `initiateGoogleLogin`, and sessionStorage from this file. RequireAuth must be used inside an AuthProvider — add a runtime error if `useAuth()` returns null (not wrapped in provider).', status: done}
- {id: refactor-auth-fetch-utility, content: 'Refactor src/authFetch.ts in unified-trading-ui-auth. The `authFetch` and `authFetchJson` functions must remain usable both inside and outside React component trees. Provide two variants: (1) `authFetch(input, init?, getToken?: () => string | null)` — if `getToken` callback is provided, use it; otherwise fall back to reading both storage keys in priority order: `sessionStorage.getItem("google_id_token")` first, then `sessionStorage.getItem("cognito_access_token")`. This fallback supports the existing non-context callers (execution-analytics-ui/src/api/client.ts uses axios interceptors calling `getStoredToken()` directly — that pattern migrates to the `getToken` callback). (2) `useAuthFetch()` hook variant — returns an `authFetch`-like function bound to the context token via `useAuth()`. No breaking change to the existing call signature `authFetch(input, init?)` — the third parameter is optional. Export: `authFetch`, `authFetchJson`, `useAuthFetch`
    from index.ts.', status: done}
- {id: update-index-exports, content: 'Update src/index.ts in unified-trading-ui-auth to export the complete new provider-agnostic API. New exports: `AuthProvider` (from AuthContext.tsx), `useAuth` (from AuthContext.tsx), `useAuthToken` (from useAuthToken.ts — refactored), `RequireAuth` (from RequireAuth.tsx — refactored), `authFetch`, `authFetchJson`, `useAuthFetch` (from authFetch.ts — refactored), `GoogleAdapter` (from adapters/GoogleAdapter.ts), `CognitoAdapter` (from adapters/CognitoAdapter.ts). Types: `AuthProviderConfig`, `AuthUser`, `AuthState` (from types.ts). Backward-compat exports kept with deprecation JSDoc: `getStoredToken`, `clearToken`, `initiateGoogleLogin` (from GoogleAuth.ts — these stay until all consumer migrations are committed). Update package.json description: "Provider-agnostic OAuth 2.0 PKCE auth library (Google + AWS Cognito) for Unified Trading UIs".', status: done}
- {id: bump-library-version, content: 'Bump unified-trading-ui-auth version from 0.1.0 to 0.2.0 in /Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-ui-auth/package.json (minor bump — new public API: AuthProvider, CognitoAdapter, useAuthFetch, AuthProviderConfig, AuthUser, AuthState). Run `npm run build` in unified-trading-ui-auth to verify the TypeScript compilation produces dist/index.js + dist/index.d.ts cleanly. Run `npm run typecheck` (tsc --noEmit) — zero type errors. Run `npm test` (vitest run) — all existing tests pass. Commit to unified-trading-ui-auth: `"feat(ui-auth): provider-agnostic OAuth2 PKCE — GoogleAdapter + CognitoAdapter"`.', status: done}
- {id: migrate-batch-audit-ui-drop-okta, content: 'Migrate batch-audit-ui to drop @okta/okta-auth-js and @okta/okta-react. Current state: batch-audit-ui/src/App.tsx imports `Security` from "@okta/okta-react" and `OktaAuth` from "@okta/okta-auth-js"; batch-audit-ui is a stub app (no real pages, just `<h1>batch-audit-ui</h1>`) so auth is not yet load-bearing. Steps: (1) Remove `@okta/okta-auth-js` and `@okta/okta-react` from `dependencies` in batch-audit-ui/package.json; (2) Add `@unified-trading/ui-auth`: `"file:../unified-trading-ui-auth"` to dependencies; (3) Rewrite batch-audit-ui/src/App.tsx to use `AuthProvider` + `RequireAuth` from `@unified-trading/ui-auth` with `provider: "cognito"` config (VITE_COGNITO_DOMAIN, VITE_COGNITO_CLIENT_ID env vars; VITE_SKIP_AUTH bypass); (4) Add env var documentation comment to App.tsx listing required vars: `VITE_COGNITO_DOMAIN`, `VITE_COGNITO_CLIENT_ID`, `VITE_REDIRECT_URI`, `VITE_SKIP_AUTH`; (5) Run `npm install` and `npm run type-check` — zero type
    errors; (6) Verify no @okta reference remains: `grep -r "@okta" batch-audit-ui/src/` must return empty. Commit to batch-audit-ui: `"feat(batch-audit-ui): replace Okta with unified-trading-ui-auth CognitoAdapter"`.', status: completed}
- {id: migrate-execution-analytics-ui, content: 'Migrate execution-analytics-ui from direct GoogleAuth call-site API to the new AuthProvider + config pattern. Files to update: (1) execution-analytics-ui/src/App.tsx — wrap Router with `<AuthProvider config={{ provider: "google", clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID, redirectUri: window.location.origin + "/auth/callback", scopes: ["openid", "email", "profile"], skipAuth: import.meta.env.VITE_SKIP_AUTH === "true" }}>` around the existing `<Router>`; remove direct import of `clearToken` + `getStoredToken` from @unified-trading/ui-auth and replace the `handleLogout` / `isAuthenticated` logic with `useAuth()` hook (`const { logout, isAuthenticated } = useAuth()`); (2) execution-analytics-ui/src/api/client.ts — replace `getStoredToken()` call in axios interceptor with `useAuthFetch` hook or a module-level token accessor (since axios interceptors run outside React tree, keep the fallback `sessionStorage.getItem("google_id_token")` pattern
    from the refactored authFetch.ts — no context needed here); (3) execution-analytics-ui/src/pages/Login.tsx — replace `initiateGoogleLogin()` direct call with `useAuth().login()` (inside Login component). Run `npm run type-check` in execution-analytics-ui — zero errors. Commit: `"feat(execution-analytics-ui): migrate to AuthProvider + GoogleAdapter"`.', status: completed}
- {id: migrate-settlement-ui, content: 'Migrate settlement-ui from direct GoogleAuth call-site API to the new AuthProvider + config pattern. Files to update: (1) settlement-ui/src/App.tsx — wrap with `<AuthProvider config={{ provider: "google", clientId: import.meta.env.VITE_GOOGLE_CLIENT_ID, redirectUri: window.location.origin + "/auth/callback", scopes: ["openid", "email", "profile"], skipAuth: import.meta.env.VITE_SKIP_AUTH === "true" }}>` as outer wrapper; replace direct `clearToken()` / `getStoredToken()` imports with `useAuth()` destructuring (`logout`, `isAuthenticated`); (2) settlement-ui/src/pages/Login.tsx — replace `initiateGoogleLogin()` with `useAuth().login()`; (3) settlement-ui/src/pages/Positions.tsx — replace `getStoredToken()` usage with `useAuth().token` or `useAuthToken().token`. Run `npm run typecheck` in settlement-ui — zero errors. Commit: `"feat(settlement-ui): migrate to AuthProvider + GoogleAdapter"`.', status: completed}
- {id: migrate-trading-analytics-ui, content: 'Migrate trading-analytics-ui from direct GoogleAuth call-site API to the new AuthProvider + config pattern. Files to update: (1) trading-analytics-ui/src/App.tsx — remove direct imports of `initiateGoogleLogin`, `getStoredToken`, `clearToken`; add `AuthProvider` wrapper with Google config (VITE_GOOGLE_CLIENT_ID, VITE_SKIP_AUTH); replace `LoginPage` component''s `initiateGoogleLogin()` button call with `useAuth().login()`; replace `HomePage`''s `getStoredToken()` / `clearToken()` calls with `useAuth()` destructuring; (2) trading-analytics-ui/src/pages/Latency.tsx — check for any direct token reads and replace with context if present. Run `npm run typecheck` — zero errors. Commit: `"feat(trading-analytics-ui): migrate to AuthProvider + GoogleAdapter"`.', status: completed}
- {id: add-unit-tests, content: 'Add unit tests to unified-trading-ui-auth covering the new adapter and context code. Test file locations and coverage targets: (1) src/adapters/GoogleAdapter.test.ts — test `login()` calls window.location redirect with correct params; test `handleCallback()` parses id_token from hash and stores in sessionStorage; test `getToken()` reads from sessionStorage; test `logout()` clears storage; (2) src/adapters/CognitoAdapter.test.ts — test PKCE verifier is 43+ chars and URL-safe; test `login()` redirects to cognitoDomain/oauth2/authorize with code_challenge_method=S256; test `handleCallback()` sends POST to /oauth2/token with code_verifier (mock fetch); test `refreshToken()` POSTs to /oauth2/token with refresh_token grant (mock fetch); test `logout()` clears storage keys; (3) src/AuthContext.test.tsx — test AuthProvider renders children; test skipAuth=true sets isAuthenticated=true immediately; test useAuth() throws outside AuthProvider. Run `npm test` (vitest
    run) — all tests pass. Coverage for new files should be >80%.', status: done}
- {id: verify-no-okta-workspace, content: 'Final verification: confirm no @okta/* references remain anywhere in the workspace (excluding this plan file). Run from workspace root: `grep -r "@okta" /Users/ikennaigboaka/Code/unified-trading-system-repos/ --include="*.ts" --include="*.tsx" --include="*.json" --exclude-dir="node_modules"`. Expected result: zero matches. If any matches remain, trace the file and apply the appropriate migration step. Also confirm the new AuthProvider API is consistently used: `grep -r "getStoredToken\|initiateGoogleLogin\|clearToken" --include="*.ts" --include="*.tsx"` in the three consumer UI src/ directories should return zero results (these calls should all have migrated to AuthProvider context). Confirm batch-audit-ui builds cleanly: `npm run build` in batch-audit-ui from workspace root.', status: completed}
---

# unified-trading-ui-auth — Provider-Agnostic OAuth 2.0 PKCE Refactor

## Objective

Refactor `unified-trading-ui-auth` from a Google-only implicit-flow library to a provider-agnostic OAuth 2.0 PKCE
library exporting `AuthProvider`, `useAuthToken`, `RequireAuth`, and `authFetch` backed by two concrete adapters:
`GoogleAdapter` (existing logic, re-wrapped) and `CognitoAdapter` (AWS Cognito Hosted UI, PKCE). Drop `@okta/*` from
`batch-audit-ui` and wire it to the new `CognitoAdapter`. Migrate the three existing consumers to the `AuthProvider`
config pattern.

## Current State

### unified-trading-ui-auth (v0.1.0)

`src/` contains 5 files:

| File              | Description                                                                        |
| ----------------- | ---------------------------------------------------------------------------------- |
| `GoogleAuth.ts`   | Google implicit flow — `initiateGoogleLogin()`, `getStoredToken()`, `clearToken()` |
| `RequireAuth.tsx` | Directly calls `getStoredToken()` + `initiateGoogleLogin()` — Google-hardwired     |
| `authFetch.ts`    | Calls `getStoredToken()` — Google-hardwired token key                              |
| `useAuthToken.ts` | Calls `getStoredToken()` + window storage listener — Google-hardwired              |
| `index.ts`        | Re-exports all of the above                                                        |

No React context. No PKCE. No token refresh. Provider is hardcoded to Google implicit flow.

### batch-audit-ui — Okta dependency

`batch-audit-ui/package.json` `dependencies`:

- `@okta/okta-auth-js: ^7.4.0`
- `@okta/okta-react: ^6.7.0`

`src/App.tsx` imports `Security` from `@okta/okta-react` and `OktaAuth` from `@okta/okta-auth-js`. The app body is a
stub (`<h1>batch-audit-ui</h1>`) — auth is not load-bearing, making this a clean migration target.

### Consumer UIs (all use `"file:../unified-trading-ui-auth"` local dependency)

| Repo                   | Imports in use                                                                                              |
| ---------------------- | ----------------------------------------------------------------------------------------------------------- |
| execution-analytics-ui | `RequireAuth`, `clearToken`, `getStoredToken` (App.tsx + api/client.ts + Login.tsx + `initiateGoogleLogin`) |
| settlement-ui          | `RequireAuth`, `clearToken`, `getStoredToken` (App.tsx + Positions.tsx + Login.tsx + `initiateGoogleLogin`) |
| trading-analytics-ui   | `RequireAuth`, `initiateGoogleLogin`, `getStoredToken`, `clearToken` (App.tsx)                              |

## Target Architecture

```
unified-trading-ui-auth/src/
  types.ts                        # AuthProviderConfig, AuthUser, AuthState, AuthAdapter (internal)
  adapters/
    GoogleAdapter.ts              # Wraps GoogleAuth.ts — implicit flow
    CognitoAdapter.ts             # AWS Cognito PKCE — no @okta deps
  AuthContext.tsx                 # AuthProvider component + useAuth() internal hook
  useAuthToken.ts                 # Refactored — reads from AuthContext
  RequireAuth.tsx                 # Refactored — reads from AuthContext
  authFetch.ts                    # Refactored — optional getToken callback + useAuthFetch hook
  GoogleAuth.ts                   # KEPT (backward compat) — deprecated exports
  index.ts                        # Updated exports
```

## New Public API

```typescript
// Config
interface AuthProviderConfig {
  provider: "google" | "cognito";
  clientId: string;
  redirectUri: string;
  scopes: string[];
  cognitoDomain?: string;   // required for provider: "cognito"
  googleClientId?: string;  // convenience alias for clientId when provider: "google"
  skipAuth?: boolean;       // dev bypass
}

// Components / hooks
<AuthProvider config={AuthProviderConfig}>...</AuthProvider>
function useAuthToken(): { token: string | null; user: AuthUser | null; isAuthenticated: boolean }
<RequireAuth loginPath="/login">...</RequireAuth>
authFetch(input, init?, getToken?: () => string | null): Promise<Response>
useAuthFetch(): typeof authFetch

// Adapters (for advanced use)
new GoogleAdapter(config: AuthProviderConfig)
new CognitoAdapter(config: AuthProviderConfig)

// Types
AuthUser, AuthState, AuthProviderConfig

// Deprecated (kept for backward compat during migration)
getStoredToken(), clearToken(), initiateGoogleLogin()
```

## Cognito PKCE Flow

```
1. login()
   → generateCodeVerifier() (crypto.getRandomValues, 43-128 chars, URL-safe)
   → generateCodeChallenge(verifier) (SHA-256 via crypto.subtle, base64url)
   → sessionStorage.setItem("cognito_pkce_verifier", verifier)
   → redirect to {cognitoDomain}/oauth2/authorize?response_type=code&...&code_challenge_method=S256

2. handleCallback() [called by AuthProvider on mount when ?code= present]
   → read code from URLSearchParams
   → read verifier from sessionStorage
   → POST {cognitoDomain}/oauth2/token (application/x-www-form-urlencoded)
       grant_type=authorization_code, client_id, redirect_uri, code, code_verifier
   → store access_token + refresh_token in sessionStorage
   → clear verifier

3. refreshToken()
   → POST {cognitoDomain}/oauth2/token
       grant_type=refresh_token, client_id, refresh_token
   → update stored access_token

4. logout()
   → clear sessionStorage keys
   → redirect to {cognitoDomain}/logout?client_id=...&logout_uri=...
```

No external npm packages. Uses only `crypto.getRandomValues` and `crypto.subtle` (Web Crypto API — available in all
modern browsers and in jsdom for tests).

## Removed Dependencies

After plan completion:

| Repo           | Removed                                  |
| -------------- | ---------------------------------------- |
| batch-audit-ui | `@okta/okta-auth-js`, `@okta/okta-react` |

## Standards

- No `any` types — use strict TypeScript generics and interface typing throughout
- No `import.meta.env` access inside library files — env values come through `AuthProviderConfig` props
- Web Crypto API only for PKCE — no crypto npm packages
- Backward-compat exports from `GoogleAuth.ts` kept with `@deprecated` JSDoc until all 3 consumer migrations are
  committed
- `npm run typecheck` (tsc --noEmit) — zero errors after each todo step
- `npm run build` — clean dist output after library bump todo

## Cross-Plan Notes

This plan has no dependency on any active Python-service plans. It is entirely frontend (TypeScript / React). No CI
pipeline changes required — consumer UIs already resolve `@unified-trading/ui-auth` via
`"file:../unified-trading-ui-auth"` local path reference; the version bump does not require publishing to a registry.
