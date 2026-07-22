---
doc_type: issue
title: E2E `loginAsAdmin`/`loginAsClient` helpers use a stale `?persona=` contract the login page no longer implements
summary: >-
  Discovered while trying to get pw:L2 evidence for a new admin CRUD spec: `app/(public)/login/page.tsx` only handles an
  `?email=`+`#pwd=` fragment handoff — there is no `?persona=` query-param handling anywhere in the file. Every E2E spec
  built on the `loginAsAdmin(page)` / `loginAsClient(page, persona)` helper pattern (`page.goto('/login?persona=admin')`
  then `waitForURL('**/dashboard**')`) times out at login, never reaching the app.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [e2e, playwright, testing-infra, login, regression-risk]
related:
  [
    plans/active/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md,
    tests/e2e/user-management.spec.ts,
  ]
created: "2026-07-22"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [dart_ui_capability_manifest_and_catalogue_formatting_gaps-003]
resolved_by:
locked_by:
depends_on: []
---

# What I found

While implementing the `AdminStrategyAssignment` admin CRUD page (issue doc
`dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md`, item wired 2026-07-22), I wrote a new
lifecycle Playwright spec (`tests/e2e/admin-strategy-assignments.spec.ts`) modeled on the established
`tests/e2e/user-management.spec.ts` pattern:

```ts
async function loginAsAdmin(page: Page) {
  await page.goto(`${BASE}/login?persona=admin`);
  await page.waitForURL("**/dashboard**", { timeout: 10000 });
}
```

It timed out at the `waitForURL` step in every run. To isolate whether this was something I broke, I ran the
**untouched** `tests/e2e/user-management.spec.ts` (a pre-existing spec I never edited) — **all 21/21 tests failed at the
exact same line, same timeout, same symptom.** This proves the break is pre-existing and environment/contract drift, not
a regression from my change.

Root cause: `app/(public)/login/page.tsx` (lines ~85-106) only wires an `?email=`+`#pwd=`-fragment handoff
(`handoffEmail`/`handoffPwd`, sourced from `window.location.search` + `window.location.hash`) — there is **no
`?persona=` query-param handling anywhere in that file** (confirmed via `grep -n "persona" app/(public)/login/page.tsx`
— the only hits are `isDemoPersonaEmail` email-domain classification, unrelated to a query param). `?persona=admin` is
simply ignored; the login form stays empty; nothing ever submits; the page never navigates to `/dashboard`.

I then probed the ACTUAL handoff contract directly: `/login?email=admin%40odum.internal#pwd=demo123`. This did **not**
log in locally either — it redirected externally to
`https://uat.odum-research.com/login?redirect=%2Fdashboard&email=...#pwd=...`, even under `pnpm dev:mock`
(`NEXT_PUBLIC_MOCK_API=true NEXT_PUBLIC_AUTH_PROVIDER=demo`). The login page has a "standing internal email → redirect
to UAT" branch (per its own code comment: "Map of personal-email accounts that previously had admin and have since...
admin role gets moved off a personal email") that appears to now catch `admin@odum.internal` even in mock/demo mode
locally — a second, deeper layer of drift beyond just the `?persona=` convention.

# Why it matters

This is the shared login helper pattern used across the E2E suite for admin/persona-gated specs
(`tests/e2e/user-management.spec.ts` and every spec built the same way) — the `pw:L2`/regression-spec evidence contract
(`codex/06-coding-standards/ui-testing-layers.md` § "Plan-Level Enforcement") requires
`npx playwright test --project=chromium tests/smoke/` (or the relevant spec) to exit 0 before a UI todo can be ticked
`[x]`. If this helper is broken repo-wide, **no admin-gated E2E spec can currently produce that evidence** — every
worker hitting this either (a) silently claims pw:L2 ✓ without it actually passing, or (b) gets stuck
`BLOCKED-PLAYWRIGHT` on unrelated, already-shipped features. Neither is acceptable at scale.

I did NOT chase a full fix — diagnosing the exact demo-login/UAT-redirect branching logic is its own scoped
investigation, outside a single admin-CRUD UI todo's remit, and risks unintended behavior changes to the real prod login
flow if touched carelessly.

# Recommended decision

Someone with context on the login page's demo-vs-UAT redirect design (this looks like an intentional prod-security
feature that leaked into local mock-mode, or a persona registry that drifted out of sync with a login-page refactor)
should either: (a) restore a `?persona=<id>` fast-path in `app/(public)/login/page.tsx` gated to
`NEXT_PUBLIC_AUTH_PROVIDER=demo` + `NEXT_PUBLIC_MOCK_API=true`, matching what every E2E helper already assumes, or (b)
bulk-update every `loginAsAdmin`/`loginAsClient` E2E helper to use the real `?email=`+`#pwd=` contract AND fix whatever
is causing `admin@odum.internal` to hit the UAT-redirect branch under mock mode.

## Todos

- [ ] [UI] P2. Diagnose why `admin@odum.internal` (and likely other demo personas) redirect to
      `https://uat.odum-research.com/login` instead of logging in locally under
      `NEXT_PUBLIC_MOCK_API=true     NEXT_PUBLIC_AUTH_PROVIDER=demo` (`pnpm dev:mock`) — check the "standing internal
      email" redirect branch in `app/(public)/login/page.tsx` against `isDemoPersonaEmail()` (`lib/auth/personas.ts`)
      for a classification bug. (repo: unified-trading-system-ui)
- [ ] [UI] P2. Once (1) is fixed, restore/repair the `?persona=<id>` (or equivalent) fast-path login helper contract
      that `tests/e2e/user-management.spec.ts`, `tests/e2e/admin-flow.spec.ts`-style specs, and every other
      `loginAsAdmin`/`loginAsClient`-based E2E spec assume, and re-verify
      `npx playwright test --project=chromium     tests/e2e/user-management.spec.ts` exits 0 as the regression check.
      (repo: unified-trading-system-ui)
- [ ] [UI] P3. Re-run `tests/e2e/admin-strategy-assignments.spec.ts` (written 2026-07-22 for the
      `AdminStrategyAssignment` admin CRUD feature) once the login helper is fixed, and record the `pw:L2 ✓` evidence
      retroactively on `dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md`'s item. (repo:
      unified-trading-system-ui)

## Codex SSOTs

`codex/06-coding-standards/ui-testing-layers.md`.
