---
doc_type: issue
title:
  Admin `/api/v1/*` routes need real Firebase Admin credentials for local/CI E2E, and the mock Next dev server crashes
  under sustained Playwright load
summary: >-
  Discovered while repairing the E2E login-helper contract
  (issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md). With the login helper now fixed, two SEPARATE,
  pre-existing, orthogonal gaps block `tests/e2e/user-management.spec.ts` (and likely other admin-CRUD specs) from fully
  exiting 0: (1) `/api/v1/*` admin routes are deliberately passed through to the REAL Next.js server (never mocked, by
  design — see mock-handler.ts's `realRoutePrefixes` comment) and require Firebase Admin credentials
  (`FIREBASE_ADMIN_CREDENTIAL` or emulator env vars) that neither local `pnpm dev:mock` nor `.github/workflows/ci.yml`'s
  `e2e` job provision, so every such call 500s with "insufficient permission" from ADC; (2) the Next dev server (`pnpm
  dev:mock`) becomes unstable and dies (`ERR_CONNECTION_REFUSED`) partway through a ~20-test sequential Playwright run,
  both when self-started and when Playwright's own `webServer` manages it.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [e2e, playwright, testing-infra, firebase-admin, ci, dev-server-stability]
related:
  [
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md,
    unified-trading-system-ui/tests/e2e/user-management.spec.ts,
    unified-trading-system-ui/lib/firebase-admin.ts,
    unified-trading-system-ui/lib/api/mock-handler.ts,
    unified-trading-system-ui/.github/workflows/ci.yml,
  ]
created: "2026-08-09"
author: slot-28 (data_engineering, adopted infra craft per task assigned_role)
parent_epic: infrastructure_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [infra_satellite_ao_dispatch_batch1-fae8df376739]
resolved_by:
locked_by:
context_scope:
  [
    /codex/06-coding-standards/ui-testing-layers.md,
    unified-trading-system-ui/lib/firebase-admin.ts,
    unified-trading-system-ui/lib/api/mock-handler.ts,
    unified-trading-system-ui/app/api/v1/users/route.ts,
    unified-trading-system-ui/.github/workflows/ci.yml,
    unified-trading-system-ui/playwright.config.ts,
  ]
depends_on: []
---

# What I found

While repairing the E2E `loginAsAdmin`/`loginAsClient` helper contract
(`issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md`), I fixed the actual login bug (see that doc's
resolution) and verified login now works end-to-end (persona fast-path auto-fills + auto-submits, and the demo persona
correctly lands on `/dashboard` instead of being misclassified as prod and redirected to UAT). With login genuinely
fixed, running the full `tests/e2e/user-management.spec.ts` suite surfaced two SEPARATE, pre-existing problems that are
NOT part of the login-helper contract and block the suite from fully exiting 0:

## 1. `/api/v1/*` admin routes need real Firebase Admin credentials

`lib/api/mock-handler.ts`'s `realRoutePrefixes` list deliberately includes `"/api/v1/"` (comment: "native admin SDK +
Firestore CRUD surface — replaces retired user-management-api"), so every `/api/v1/*` fetch — including
`GET /api/v1/users` (the admin users list) — bypasses the mock layer and hits the REAL Next.js API route
(`app/api/v1/users/route.ts`), which calls `getAdminApp()` (`lib/firebase-admin.ts`). Locally that function needs either
`FIREBASE_ADMIN_CREDENTIAL` (a service-account JSON) or a running Firebase emulator
(`FIRESTORE_EMULATOR_HOST`/`FIREBASE_AUTH_EMULATOR_HOST`/`FIREBASE_STORAGE_EMULATOR_HOST`, started via
`pnpm emulators:start`) — neither is set by `pnpm dev:mock` or by `playwright.config.ts`'s `webServer` command. Verified
live: direct browser network trace shows `GET /api/v1/users` → `500` with body
`{"error":"Error: Credential implementation provided to initializeApp() via the \"credential\" property has insufficient permission to access the requested resource...`.
`.github/workflows/ci.yml`'s `e2e` job (`pnpm build` then `pnpm exec playwright test --project=chromium`) also never
sets `FIREBASE_ADMIN_CREDENTIAL` or starts the emulator, so CI hits the identical failure — this is not a local-only
gap.

**Impact**: any E2E spec that visits an admin-CRUD page backed by `/api/v1/*` (users list, onboard, modify, offboard,
access-requests, catalogue, etc.) cannot pass in the current local or CI setup. This affects
`tests/e2e/user-management.spec.ts` (19 of 21 tests) and very likely `tests/e2e/admin-strategy-assignments.spec.ts` and
`tests/e2e/permission-catalogue.spec.ts` too (not yet independently verified).

## 2. The mock Next dev server (`pnpm dev:mock`) becomes unstable under a sustained Playwright run

Running the full 21-test `user-management.spec.ts` suite sequentially (`workers: 1`), the dev server the tests point at
starts returning `net::ERR_CONNECTION_REFUSED` partway through (observed after test 4 in one run, after test 10 in
another) — confirmed independent of how the server is started: reproduced both with a manually-started
`next dev --webpack -p <port>` process AND with Playwright's own self-managed `webServer` (which detects the server is
"not up" and respawns it, but subsequent tests still fail near-instantly with connection-refused, suggesting the respawn
itself doesn't recover cleanly under this codebase's dev-server + mock-handler + `next.config.mjs` load). Did NOT
diagnose the exact crash cause (no OOM/dmesg visibility available in this sandboxed session) — this needs a dedicated
investigation with server-log capture across a full run.

# Why it matters

Both gaps mean `npx playwright test --project=chromium tests/e2e/user-management.spec.ts` (the exact command the source
issue doc's own Done-when cites) cannot exit 0 today regardless of the login-helper fix, and CI's `e2e` job is very
likely already red on this same file for the same reason (Firebase Admin credentials) — worth confirming via a fresh
`gh run view --log-failed` on the latest `e2e` job run. This blocks `pw:L2 ✓` evidence for every admin-CRUD UI todo, not
just the ones in `infra_satellite_ao_dispatch_batch1_2026_07_26.md`.

# Recommended decision

1. Provision a `FIREBASE_ADMIN_CREDENTIAL` service-account secret (least-privilege, Firebase Admin SDK only) for CI +
   local dev, OR wire `.github/workflows/ci.yml`'s `e2e` job (and `playwright.config.ts`'s `webServer`) to start the
   Firebase emulator suite (`pnpm emulators:start` + seed) before running tests — an operator/infra decision on which
   approach + who owns provisioning the credential (touches CI secrets).
2. Separately, someone should reproduce and diagnose the dev-server-crash-under-sustained-load issue with server
   stdout/stderr captured across a full run (redirect `next dev`'s own output, not just Playwright's summary) — this is
   orthogonal to (1) and blocks ANY long-running local Playwright suite, not just admin-CRUD ones.

## Todos

- [ ] [INFRA] P2. Decide + provision either a `FIREBASE_ADMIN_CREDENTIAL` CI secret or a Firebase-emulator-backed E2E
      job for `.github/workflows/ci.yml`'s `e2e` job, so `/api/v1/*` admin routes resolve instead of 500ing on missing
      Admin SDK credentials. Verify by re-running `tests/e2e/user-management.spec.ts` in CI and confirming the
      `/api/v1/users` 500 is gone. (repo: unified-trading-system-ui)
- [x] ✅ [INFRA] P2. Diagnose why the `pnpm dev:mock` Next dev server dies (`ERR_CONNECTION_REFUSED`) partway through a
      sustained ~20-test sequential Playwright run against it (reproduced both self-started and Playwright-`webServer`-
      managed) — capture the dev server's own stdout/stderr across a full run to find the crash cause, then fix it.
      (repo: unified-trading-system-ui) — unified-trading-system-ui@1c59c624 (via
      `infra_satellite_ao_dispatch_batch13_2026_08_09.md`). Root cause: shared-host `resource-watchdog.service` SIGTERMs
      `next-server` once RSS crosses its ceiling (`next`/`node` not allowlisted); `next dev --webpack` bundling
      `firebase-admin`'s grpc/google-gax tree per `/api/v1/*` compile drove the spike. Fixed via
      `serverExternalPackages` + a `NODE_OPTIONS` heap cap on `dev:mock`. Verified: full
      `tests/e2e/user-management.spec.ts` (21 tests) completes with zero dev-server-death failures.
- [ ] [TEST] P3. Once both above are resolved, re-run `tests/e2e/user-management.spec.ts`,
      `tests/e2e/admin-strategy-assignments.spec.ts`, and `tests/e2e/permission-catalogue.spec.ts` end-to-end and
      confirm all exit 0; record `pw:L2 ✓` evidence on
      `/plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md`'s item (the
      original ask from `issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md`'s todo 3). (repo:
      unified-trading-system-ui)

## Codex SSOTs

`/codex/06-coding-standards/ui-testing-layers.md`.

## Progress Log

- **2026-08-09 (slot-28)**: Filed while working `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s login-helper-repair
  todo. The login helper itself is fixed and verified (see that plan's Progress Log); these two gaps are separate,
  pre-existing, and orthogonal to the login fix.
- **2026-08-10 (slot-8, reconcile per `infra_satellite_ao_dispatch_batch13_finalize_2026_08_09.md`)**: Flipped todo 2 —
  verified `unified-trading-system-ui@1c59c624` (batch13) directly against the live commit (content-diff matches the
  claim: `next.config.mjs` `serverExternalPackages` + `dev:mock` `NODE_OPTIONS` heap cap). Todos 1 (Firebase Admin
  credential/emulator decision) and 3 (re-run gated on both) remain genuinely open — this doc stays `status: open`, NOT
  an archival candidate.
