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
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [e2e, playwright, testing-infra, login, regression-risk]
related:
  [
    /plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md,
    unified-trading-system-ui/tests/e2e/user-management.spec.ts,
    /plans/active/issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md,
    /plans/active/e2e_login_persona_handoff_helper_stale_2026_07_22_finalize_2026_08_10.md,
  ]
created: "2026-07-22"
author: unknown
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: ui_developer
drift_direction: advance-code
source: [dart_ui_capability_manifest_and_catalogue_formatting_gaps-003]
resolved_by:
locked_by:
context_scope:
  [
    /codex/06-coding-standards/ui-testing-layers.md,
    unified-trading-system-ui/app/(public)/login/page.tsx,
    unified-trading-system-ui/lib/auth/personas.ts,
    unified-trading-system-ui/tests/e2e/user-management.spec.ts,
    unified-trading-system-ui/tests/e2e/admin-strategy-assignments.spec.ts,
    /plans/active/issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md,
  ]
depends_on: []
---

# What I found

While implementing the `AdminStrategyAssignment` admin CRUD page (issue doc
`/plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md`, item wired 2026-07-22),
I wrote a new lifecycle Playwright spec (`tests/e2e/admin-strategy-assignments.spec.ts`) modeled on the established
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
(`/codex/06-coding-standards/ui-testing-layers.md` § "Plan-Level Enforcement") requires
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

- [x] ✅ Diagnose why `admin@odum.internal` (and likely other demo personas) redirect to
      `https://uat.odum-research.com/login` instead of logging in locally under
      `NEXT_PUBLIC_MOCK_API=true NEXT_PUBLIC_AUTH_PROVIDER=demo` (`pnpm dev:mock`) — check the "standing internal email"
      redirect branch in `app/(public)/login/page.tsx` against `isDemoPersonaEmail()` (`lib/auth/personas.ts`) for a
      classification bug. (repo: unified-trading-system-ui) — unified-trading-system-ui@15e4b4bc (verified ancestor of
      origin/live-defi-rollout). Actual root cause differed from the classification-bug hypothesis: `next.config.mjs`
      unconditionally loaded `.env.production` into `next dev`, wrongly satisfying `login/page.tsx`'s `isProdSite` check
      — the same "standing internal email → UAT redirect" branch this todo names — fixed by making the env-file load
      NODE_ENV-aware. Reconciled via infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md todo 1.
- [x] ✅ Once (1) is fixed, restore/repair the `?persona=<id>` (or equivalent) fast-path login helper contract that
      `tests/e2e/user-management.spec.ts`, `tests/e2e/admin-flow.spec.ts`-style specs, and every other
      `loginAsAdmin`/`loginAsClient`-based E2E spec assume, and re-verify
      `npx playwright test --project=chromium tests/e2e/user-management.spec.ts` exits 0 as the regression check. (repo:
      unified-trading-system-ui) — unified-trading-system-ui@15e4b4bc (verified ancestor of origin/live-defi-rollout).
      `?persona=<id>` fast-path restored in `app/(public)/login/page.tsx`; verified via Playwright that `?persona=admin`
      now logs in locally. Full-suite green is blocked by two separate pre-existing gaps unrelated to this helper, filed
      as issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md. Reconciled
      via infra_satellite_ao_dispatch_batch1_finalize_2026_07_26.md todo 1.
- [x] ✅ [UI] P3. **Re-run verification COMPLETE (slots 20, 6, 4 — 2026-08-10).** Three independent re-runs of
      `tests/e2e/admin-strategy-assignments.spec.ts` all confirm the documented
      Firebase-Admin-creds/dev-server-instability class — NOT a clean pass. Slot-20: 1/3 passed; slot-6: 0/3 passed;
      slot-4: 0/3 passed. All failures trace to `/api/v1/*` routes requiring Firebase Admin credentials the mock dev
      server doesn't provision. Full per-slot breakdowns recorded in the Progress Log below. **No `pw:L2 ✓` can be
      recorded until `ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` is
      fixed.** (repo: unified-trading-system-ui) — PM@2c85d322e0.
- [x] ✅ [UI] P3. BLOCKED-ON:ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09 —
      Once the Firebase Admin credentials / mock dev-server gap is fixed, re-run
      `tests/e2e/admin-strategy-assignments.spec.ts` and record `pw:L2 ✓` evidence retroactively on
      `/plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md`'s item. (repo:
      unified-trading-system-ui) — **Re-ran 2026-08-10 (slot 6, clean run against a fresh slot-6 dev:mock server): 2
      failed / 1 passed — NOT a clean pass, NO `pw:L2 ✓`.** Failures: (a) Tier-1 login `waitForURL("**/dashboard**")`
      10s timeout on cold first navigation (`?persona=admin` auto-fills but never navigates; test 2 logged in fine
      later, so this is first-request dev-server compile latency, not a hard login regression); (b) Tier 2-5
      create→edit→delete: assignment created + listed, but the edit to LOCKED did not persist/render (row shows
      archetype/org/date, no status) — consistent with the documented `/api/v1/*` Firebase-Admin-creds 500 class on the
      status-update call (`ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md`
      todo 1, still `assigned_vm: NA`/open). ORG_CONFLICT test passed. First attempt reused a cross-slot dev server
      (`.tabs/4`) and was discarded as invalid evidence — the recorded result is the fresh-server re-run. Blocker fix is
      that issue doc's scope, not this one.

## Codex SSOTs

`/codex/06-coding-standards/ui-testing-layers.md`.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — All 3 todos require a
  human/design decision on demo-vs-UAT redirect behavior; doc explicitly flags risk of unintended prod login-flow
  changes if touched carelessly.
- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — re-affirmed. All 3 items form a single sequential
  chain gated on a genuine, still-unresolved diagnostic/design call about prod-security-adjacent login redirect
  behavior. Independently re-verified LIVE today against the `unified-trading-system-ui` sibling clone: `?persona=`
  handling is still absent from `app/(public)/login/page.tsx` and `tests/e2e/user-management.spec.ts` still uses the old
  contract — the bug still reproduces 12 days later, not stale.
- **context-scout 2026-08-03**: re-verified context_scope (4 entries) — all four still directly cited by the doc's own
  body; no change needed.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **fixed 2026-08-06 (/plan-reconcile ao)**: frontmatter `related:` cited the bare path
  `tests/e2e/user-management.spec.ts`, which does not resolve from this repo (unified-trading-pm). Repointed to
  `unified-trading-system-ui/tests/e2e/user-management.spec.ts`, matching `context_scope`'s already-correct form.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3) — RECLASSIFY, `assigned_vm: NA` → `planning`.** The
  prior 3 markers (07-30, 08-03, 08-06) correctly kept this whole doc NA while all 3 todos formed one sequential chain
  gated on a genuine, unresolved login-redirect design/diagnostic question. That question is now RESOLVED — todos 1-2
  were flipped `[x]` on 2026-08-09 (`unified-trading-system-ui@15e4b4bc`, independently re-verified as a live
  `origin/live-defi-rollout` ancestor), one day AFTER the last na-eligibility-audit marker, so no prior pass ever
  re-assessed the doc with its prerequisite actually cleared. The sole remaining item (re-run the spec, record `pw:L2 ✓`
  evidence, or record the specific known-blocker failure mode if hit) is now a bounded verification task with a stated
  done-when either way — added an explicit caveat to the todo pointing at
  `ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` (filed 2026-08-09, same
  investigation) since this admin-CRUD spec may hit the same Firebase-Admin-creds gap; the todo's done-when now covers
  both outcomes so a worker can't force a false pass. Conflict-check: grepped every `status: draft`/`active`
  `ao_satellite_ao_dispatch_batch*` (1-16) + finalizes + `ao_open_issues_consolidated_close_out_2026_07_17.md` for
  `admin-strategy-assignments`/`e2e_login_persona_handoff` — zero hits. `assigned_role` set to `ui_developer` (was
  unset) to match the `[UI]` tag. Finalize twin:
  `/plans/active/e2e_login_persona_handoff_helper_stale_2026_07_22_finalize_2026_08_10.md`.

- **worked 2026-08-10 (slot-20, adopted ui_developer craft)**: Re-ran `tests/e2e/admin-strategy-assignments.spec.ts` per
  todo 3's done-when. Hit the documented Firebase-Admin-creds/dev-server-instability class (1 passed / 2 failed) — full
  failure-mode detail appended to the todo itself. Did not attempt the Firebase-creds fix inline (out of this doc's
  scope, per the todo's own instruction); todo stays open. No plan checkbox flip — nothing to flip false.

- **worked 2026-08-10 (slot-4, adopted ui_developer craft)**: Re-ran `tests/e2e/admin-strategy-assignments.spec.ts` per
  todo 3's done-when — 3/3 failed, 0 passed. Same documented Firebase-Admin-creds/dev-server-instability class as
  slot-20 and slot-6. The blocker issue
  (`ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md`) remains
  `assigned_vm: NA` + `status: open` — the underlying gap has not moved across three independent re-runs today (slots
  20, 6, 4). Full failure-mode breakdown appended to todo. Todo stays open per its own instruction — not forcing a false
  `pw:L2 ✓`; not fixing the Firebase-creds gap inline (out of scope).
- **worked 2026-08-10 (slot-6, ui_developer) — TODO 3 FLIPPED `[x]` per the 2026-08-10 na-eligibility-audit done-when
  (covers both outcomes: `pw:L2 ✓` OR the recorded known-blocker failure mode).** Clean re-run of
  `tests/e2e/admin-strategy-assignments.spec.ts` against a FRESH slot-6 `dev:mock` server: **2 failed / 1 passed — NOT a
  clean pass, no `pw:L2 ✓` recorded.** First attempt reused a cross-slot dev server (`.tabs/4` clone via slot-derived
  port reuse) and was discarded as invalid evidence; re-ran once the port was free so the result reflects a genuine
  slot-6 server. Failures: (a) Tier-1 login `waitForURL("**/dashboard**")` 10s timeout on cold first navigation (persona
  auto-fill worked — form shows `admin@odum.internal`/`demo123` — but no navigation; test 2 logged in fine, so this is
  first-request dev-server compile latency, not a login regression); (b) Tier 2-5 create→edit→delete failed at the
  LOCKED assertion — assignment created + listed, but the status edit did not persist/render (row shows
  archetype/org/date with no LOCKED badge), consistent with the documented `/api/v1/*` Firebase-Admin-creds 500 class on
  the status-update call. ORG_CONFLICT test passed (1/3). Underlying blocker
  (`ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` todo 1, Firebase Admin
  creds provisioning, `assigned_vm: NA` + `status: open`) has NOT moved — that issue is the fix owner, and the gated
  finalize plan (`e2e_login_persona_handoff_helper_stale_2026_07_22_finalize_2026_08_10.md`, REVIEW role) independently
  re-verifies this signature before any archival decision. Todo 3 closed with the blocker outcome recorded; the dart_ui
  item gets NO retroactive `pw:L2 ✓`.
- **reconciled 2026-08-10 (slot-22, review craft — finalize
  `e2e_login_persona_handoff_helper_stale_2026_07_22_finalize_2026_08_10.md` todo 2): source-doc todo evidence confirmed
  fully recorded.** Todo 4's `BLOCKED-ON:...Firebase-creds...` flip already carries the slot-6 clean re-run evidence (2
  failed / 1 passed, NO `pw:L2 ✓`, documented blocker signature — full detail inline on the todo). No edit needed to the
  todo itself. The retroactive-`pw:L2` resolution has been reconciled onto
  `/plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md`'s item 3: **NO
  `pw:L2 ✓` is recordable** — three independent re-runs + this finalize's re-verification all confirm the documented
  blocker; the fix owner remains
  `/plans/active/issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md`.
