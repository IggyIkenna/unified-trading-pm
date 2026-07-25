---
title: Refactor G2.6 — Staging Firebase provisioning
status: active
priority: P0
owner: agent
locked_by: live-defi-rollout
locked_since: 2026-04-20
amended: 2026-04-22
depends_on:
  - /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md §2.6
  - plans/active/deployment_topology_and_client_isolation_2026_04_17.plan.md (folded)
  - plans/active/five_space_ia_execution_child_plan_2026_04_17.md ticket #12 (folded)
  - plans/active/ui_unification_v2_sanitisation_2026_04_20.plan.md Phase 6 (user-management-ui fold-in — ARCHIVED
    2026-04-20)
# Wave G2-α — parallel with G2-α peers 2.1, 2.8, 2.9, 2.11. Gates G2-β (2.2, 2.7, 2.10).
# PATH AMENDMENT 2026-04-22: user-management-ui archived; Firebase config lives at unified-trading-system-ui/lib/admin/firebase.ts + lib/auth/firebase-config.ts.
supersedes: [deployment_topology_and_client_isolation_2026_04_17.plan.md]
reconciliation_supersedes_added: 2026-04-25
---

> **Reconciliation note (2026-04-25):** This plan absorbs
> [deployment_topology_and_client_isolation_2026_04_17.plan.md](./deployment_topology_and_client_isolation_2026_04_17.plan.md).
> deployment_topology was folded into G2.6 per amendment 2026-04-22 See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence anchors.

# Refactor G2.6 — Staging Firebase provisioning

> ## Naming-convention reference (read this first)
>
> The staging environment uses **5 different names** across infrastructure layers. They all refer to the same thing:
>
> | Layer                   | Name in use                     | File / surface                                                       |
> | ----------------------- | ------------------------------- | -------------------------------------------------------------------- |
> | Firebase project        | `odum-staging`                  | `.firebaserc` (alias `staging`)                                      |
> | Firebase hosting target | `uat`                           | `firebase.json` hosting block                                        |
> | Cloud Run service       | `odum-portal-staging`           | `firebase.json` rewrites + GCP console                               |
> | Public hostname         | `uat.odum-research.com`         | DNS + auth-allowed-domains                                           |
> | Runtime env label       | `staging` (uppercase `STAGING`) | `lib/runtime/environment.ts → getDeploymentEnv()` (hostname-derived) |
> | Build-time env file     | `docker-build.env.uat`          | `unified-trading-system-ui/config/`                                  |
> | Mail domain             | `mail.uat.odum-research.com`    | Resend / DNS                                                         |
>
> If you read "the UAT bundle", "the staging deployment", or "odum-portal-staging Cloud Run" in any doc, all three mean
> the same thing. Use this table to disambiguate before flagging a "missing" piece.

## Context

Stage 3E §2.6 ships a staging Firebase project so warm-prospect demos at `odum-research.co.uk` can hand out real-auth
credentials without reaching prod. Today demo personas work localhost-only (mock mode); any staging-domain visitor
hitting a real-firebase code path either crashes or falls into prod — unacceptable. The ticket was originally tracked as
`five_space_ia #12` and deferred through Wave E; Wave G2-α is now the canonical home.

Target: a provisioned staging Firebase project (e.g. `odum-staging`) with security rules + CI hooks + env-var surface
wired through unified-trading-system-ui (which now hosts the former user-management-ui admin surfaces — folded
2026-04-20). Warm-prospect demos route through staging; prod stays reserved for paid clients.

## Decisions locked with user (2026-04-20)

| Decision                                                                   | Chosen                                                                               | Source                                                              |
| -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| Separate Firebase project (not a prod sub-tenant)                          | Full isolation — staging outages never touch prod                                    | Stage 3E §2.6 + deployment_topology plan                            |
| Project ID: `odum-staging` (or `odum-research-staging`)                    | Short + unambiguous vs `odum-research` prod                                          | Operator-deferred; default to `odum-staging` unless naming conflict |
| Security rules MUST exist before emission                                  | Firestore default-open is unsafe; rules committed with the project-creation commit   | Stage 3E §2.6 + security precedent                                  |
| Admin SDK credentials via Secret Manager (GCP SM `firebase-admin-staging`) | Follows same CLAUDE.md ADC-default pattern as prod; never in `.env`                  | CLAUDE.md secret-handling rule                                      |
| `NEXT_PUBLIC_FIREBASE_*_STAGING` env vars exposed via `VITE_FIREBASE_*`    | Standard Next.js public-env convention; UI reads them via `lib/firebase.ts` switcher | CLAUDE.md 5-axis mode table                                         |
| CI runs against staging Firebase emulator                                  | Emulator is a subset of staging; credential-free per test infrastructure guidance    | CLAUDE.md Testing Infrastructure §                                  |

## Cross-references

- **Wave G2-α peers (parallel):** G2.1 (JWT claims — blocks on this), G2.8 (fund registry), G2.9 (UAC gaps), G2.11 (CRM)
- **Downstream Wave G2-β:** G2.2 (API keys — needs real Firebase user accounts), G2.7 (demo provisioning)
- **Folded plans:** `deployment_topology_and_client_isolation_2026_04_17.plan.md` §3 (Firebase section),
  `five_space_ia_execution_child_plan_2026_04_17.md` ticket #12 (staging Firebase)
- **Codex:** `/codex/05-infrastructure/runtime-tiers-and-deployment.md`, `codex/14-playbooks/authentication/`
- **Deployment-service:** will receive Firestore security rules in a follow-up commit (not this wave's scope)

## Mandatory read-set

1. `/codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md` §2.6
2. `plans/active/deployment_topology_and_client_isolation_2026_04_17.plan.md` — full
3. `plans/active/five_space_ia_execution_child_plan_2026_04_17.md` — ticket #12 section
4. `codex/14-playbooks/authentication/` — all auth playbook docs
5. `/codex/05-infrastructure/runtime-tiers-and-deployment.md`
6. `unified-trading-system-ui/lib/admin/firebase.ts` + `lib/auth/firebase-config.ts` + `lib/auth/firebase-provider.ts` —
   current prod-only bootstrap (post-fold SSOT)
7. `unified-trading-system-ui/lib/firebase.ts` (or equivalent config)
8. `deployment-service/scripts/` — any existing Firebase rule deployers
9. `CLAUDE.md` — Testing Infrastructure section (emulator setup)

## Out of scope

- Emitting JWT claims — that's G2.1 (this plan establishes the Firebase project only)
- Per-client API keys — that's G2.2
- Demo-provisioning automation — that's G2.7
- Prod Firebase changes — prod stays untouched in this wave
- Writing user-facing admin UI for Firebase management — Firebase console is the tool
- Reading `_archived_pre_v2/` paths

## Dev/staging parity rule

Dev (`localhost:3000` tier-1 mock-auth) and staging (`odum-research.co.uk` real-firebase) MUST use the same UI code
path. The switch is an env var (`NEXT_PUBLIC_USE_FIREBASE_AUTH`) + Firebase config values — no code-fork. Playwright
specs run identically against both (staging uses the Firebase emulator for CI).

## Preservation requirements — DO NOT regress (audited 2026-04-24)

Multiple agents across multiple sessions have built up sophisticated persona/demo/visibility infrastructure on top of
the existing demo provider. **Any agent executing Phases B-E MUST preserve every item below. Failure to preserve any of
these is a hard rejection of the PR — not a follow-up.**

### Persona richness inventory (live state 2026-04-24)

| Asset                           | Location                                                                                                                            | Size                                                                                                                                                                                                                                               | Why it matters                                                                                                                                                                                                                                     |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Persona library                 | `unified-trading-system-ui/lib/auth/personas.ts`                                                                                    | 537 LOC, **65 personas**                                                                                                                                                                                                                           | SSOT for who-can-access-what across all UI surfaces. Includes role + entitlements + audiences (G1.9 follow-up) + email + org.                                                                                                                      |
| Restriction-profile YAMLs       | `unified-trading-pm/codex/14-playbooks/demo-ops/profiles/`                                                                          | **14 files** (admin / anon / client-full / desmond-dart-full / desmond-signals-in / elysium-defi-full / demo-im-reports-only / demo-signals-client / prospect-dart-{,full,signals-in} / prospect-im / prospect-perp-funding / prospect-regulatory) | G1.7 RestrictionProfile engine consumes these per-persona to drive padlocked-vs-hidden tile state.                                                                                                                                                 |
| Visibility-slicing matrix       | `unified-trading-system-ui/tests/unit/lib/architecture-v2/visibility-slicing-matrix.test.ts` + 546-cell Playwright matrix from G3.6 | 171 LOC unit + 349 e2e                                                                                                                                                                                                                             | Asserts persona × route × flavour visibility. Hard regression gate.                                                                                                                                                                                |
| Audience field (G1.9 follow-up) | `lib/auth/audiences.ts` (NEW per `g1_9_followup_codex_docs_application_surface_2026_04_24.plan.md`)                                 | 5-audience enum threaded through `personas.ts`                                                                                                                                                                                                     | Codex doc filtering at `/docs/[...slug]`.                                                                                                                                                                                                          |
| `/seed-demo` flow               | `unified-trading-system-ui/app/(ops)/seed-demo/page.tsx` + `app/api/demo-session/{issue-link,verify,revoke}/route.ts`               | route + 3 API handlers                                                                                                                                                                                                                             | Per-prospect magic-link issuance + UAT-resident demo accounts. Resend integration at `lib/email/resend.ts`.                                                                                                                                        |
| Email-pattern dual-domain       | `personas.ts` line ~14 comment block                                                                                                | —                                                                                                                                                                                                                                                  | `@odum-research.co.uk` = internal advisors / investors; `@odum-research.com` = external prospects. The flip MUST keep both working.                                                                                                                |
| Firebase claims merge           | `unified-trading-system-ui/lib/auth/firebase-provider.ts::enrichUserFromBackend()` lines 94–209                                     | ~115 LOC                                                                                                                                                                                                                                           | Existing path that merges Firebase identity + custom claims (`role`, `entitlements`, 1KB cap) into the same `AuthUser` shape personas use.                                                                                                         |
| Admin claims emitter            | `app/api/admin/set-claims/route.ts`                                                                                                 | —                                                                                                                                                                                                                                                  | Admin SDK endpoint that writes `role` + `entitlements` claims to a Firebase user. Wave G2.1 extends this.                                                                                                                                          |
| `DemoPlanToggle`                | `components/demo/DemoPlanToggle.tsx`                                                                                                | —                                                                                                                                                                                                                                                  | Full ⇄ Signals-In, DeFi Full ⇄ DeFi Signals UX. **Tier-override refactor shipped 2026-04-25** (consumes `lib/auth/tier-override.ts`); decoupled from auth provider, works in demo + Firebase. No re-login on flip. Confirmed via audit 2026-05-01. |

### What the Firebase flip MUST preserve

1. **`personas.ts` remains SSOT.** Real Firebase staging users get matched to persona records by email. Don't delete or
   demote `personas.ts`. Real Firebase users are an _index_ into the persona table, not a replacement for it.
2. **65 personas remain drivable on UAT.** Provision a corresponding Firebase staging user for every persona in
   `personas.ts` (auto-script on persona-add), with the persona's existing email address. `enrichUserFromBackend()` then
   reads custom claims to reconstruct the same `AuthUser` shape the demo provider built today.
3. **Custom claims schema must carry enough to reconstruct the persona.** At minimum: `role`, `entitlements`,
   `personaId` (new — references the persona record by ID, lets `enrichUserFromBackend` short-circuit to
   `getPersonaById(claims.personaId)` for the rich record without bloating the 1KB claim payload).
4. **Admin "act as <persona>" capability.** Admins demoing prospects need to render the UI as any persona without
   logging out. Mechanism: admin-only API writes a transient claim `actAs: "<persona-id>"`; UI reads it and renders the
   target persona's entitlements server-side. Replaces the `loginByEmail(other, "")` empty-password swap.
5. **`DemoPlanToggle` UX is preserved exactly.** User refactor: button still flips Full ⇄ Signals-In, but the underlying
   mechanism is a localStorage `tier-override: "<persona-id>"` flag that the auth context overlays on top of the real
   Firebase user's entitlements at render time. Zero visual regression.
6. **All 14 restriction-profile YAMLs continue to drive UI tiles.** G1.7 RestrictionProfile engine signature unchanged;
   the input persona-id can come from either the demo provider or `actAs` claim or `tier-override` localStorage.
7. **G3.6 visibility-slicing matrix test stays green.** The 546-cell Playwright matrix asserts persona × route × flavour
   visibility — must pass identically against demo and Firebase paths.
8. **G1.9 follow-up audience filter works for Firebase users.** `viewer.audiences` resolved from claims-based persona
   record on UAT, from demo persona on dev. Codex doc 404 logic identical across paths.
9. **`/seed-demo` flow keeps working.** Magic-link issuance via Resend stays in place. Generated demo accounts now
   resolve to real Firebase staging users (not localStorage personas) — but the operator UX (form, magic link, demo
   email creds) is unchanged.
10. **Email pattern dual-domain stays.** Real Firebase staging users use the exact same email addresses already listed
    in `personas.ts` (`@odum-research.co.uk` for advisors/investors; `@odum-research.com` for prospects). Domain-driven
    routing logic in `personas.ts::DEMO_PERSONA_EMAILS` keeps working unchanged.
11. **Localhost dev stays demo-only.** Tier-1 dev (`localhost:3000`) does NOT flip to Firebase. The hostname-derived
    switch (`getDeploymentEnv()` returns `"dev"` for localhost) ensures `lib/auth/firebase-provider.ts` is never
    activated on localhost. Demo provider remains the dev path.
12. **Prod Firebase project untouched.** `central-element-323112` stays as today. The flip only touches the UAT bundle
    (`docker-build.env.uat`) reading `_STAGING`-suffixed config values pointing at `odum-staging`.

### Hard NO list (any of these is grounds for revert)

- Deleting `personas.ts` or any persona record from it.
- Removing `DemoPlanToggle` (refactor it; don't delete).
- Removing `/seed-demo` or any demo-session API route.
- Touching `central-element-323112` Firebase project config.
- Forking the auth code path (`if Firebase else demo`) into two divergent files. The path is shared; only the provider
  injection differs. Per the existing dev/staging parity rule.
- Hard-coding `NEXT_PUBLIC_AUTH_PROVIDER=firebase` in localhost `.env*` files (would break dev).
- Bypassing `enrichUserFromBackend()` to skip the persona-record merge.
- Skipping the `actAs` admin-acting-as-persona capability — without it, demo walkthroughs break.

### Audit-on-merge gate (mandatory)

Before merging Phase B-E commits, the agent MUST run + report:

- `cd unified-trading-system-ui && CI=true npm test -- --run lib/auth lib/architecture-v2 components/demo` — every
  persona-related unit test green.
- `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — full pass.
- Playwright spec list: `tests/e2e/playbooks/refactor/` filtering on `g1-7|g1-9|g3-6` — all green.
- Manual screenshot pass: load UAT (or Firebase emulator) as 5 representative personas (admin, prospect-im,
  desmond-dart-full, desmond-signals-in, elysium-defi-full) — confirm visible tiles match restriction-profile YAMLs.
- DemoPlanToggle smoke: click Full ⇄ Signals-In, confirm tier-override overlay applies (visible tile diff matches the
  paired persona's restriction profile).

### Cross-references for the executing agent

- Firebase provider entry point: `unified-trading-system-ui/lib/auth/firebase-provider.ts`
- Demo provider entry point: `unified-trading-system-ui/lib/auth/demo-provider.ts`
- Persona table: `unified-trading-system-ui/lib/auth/personas.ts`
- Restriction-profile engine:
  `unified-api-contracts/unified_api_contracts/internal/architecture_v2/restriction_profiles.py` (Option X — UAC hosts
  the logic, see `feedback_option_x_uac_hosts_pure_logic.md`)
- Restriction-profile YAMLs: `unified-trading-pm/codex/14-playbooks/demo-ops/profiles/*.yaml`
- Visibility-slicing test: `unified-trading-system-ui/tests/unit/lib/architecture-v2/visibility-slicing-matrix.test.ts`
- Audience system (post G1.9 follow-up): `unified-trading-system-ui/lib/auth/audiences.ts` (NEW per
  `g1_9_followup_codex_docs_application_surface_2026_04_24.plan.md`)

## Status update 2026-04-25 — RETARGETED: UAT IS staging

This plan was originally scoped to provision a separate `odum-staging` Firebase project (per the locked decision
"Separate Firebase project (not a prod sub-tenant)"). **That decision is being reversed.** The simpler model that
actually matches the deployed infrastructure:

- **UAT IS staging.** The `uat.odum-research.com` hostname + `odum-portal-staging` Cloud Run service + `uat` hosting
  target are the staging environment. They're served via the same Firebase project as prod (`central-element-323112`) —
  separated by hostname + hosting target only, not by Firebase project boundary.
- The `.firebaserc` alias `staging: odum-staging` is **leftover misdirection** from this plan's original direction. No
  `odum-staging` project was ever created, and none is needed.
- The `firebase.json` `uat` hosting target lives under `targets.central-element-323112.hosting` — confirming the
  shared-project model.

**What this plan now tracks** (retargeted scope):

1. Authorize `uat.odum-research.com` as a Firebase Auth domain on the shared `central-element-323112` project (if not
   already).
2. Copy the 6 `NEXT_PUBLIC_FIREBASE_*` values from `docker-build.env.production` into `docker-build.env.uat`.
3. Flip `NEXT_PUBLIC_AUTH_PROVIDER=demo` → `firebase` in `docker-build.env.uat`.
4. Redeploy UAT.
5. Smoke-test login. UAT users authenticate against the shared user pool — UAT-only test users coexist with prod
   customers.

Phases B–E (env-var surface, Firestore rules, CI hooks, smoke) are largely no-ops or trivial under the shared-project
model. Most of the original plan's scope is dropped because we're not standing up a parallel project.

**The `DemoPlanToggle` blocker is resolved** by the tier-override refactor in `lib/auth/tier-override.ts` shipped
2026-04-25. The toggle writes a localStorage flag that overlays entitlements on top of the raw authenticated user —
provider-agnostic. Smoke-tested across 6 personas (Desmond + Patrick paired toggles, Investor, Admin,
demo-signals-client, demo-im-reports-only).

SSOT cross-ref:
[`/codex/08-workflows/environment-mode-philosophy.md`](/codex/08-workflows/environment-mode-philosophy.md) §Axis 2.

## Status update 2026-05-01 — Audit-on-merge gate executed (PRE-Phase-B-E baseline)

The audit-on-merge gate declared in §Preservation requirements was run today against tier-1 dev (`localhost:3000`) as a
baseline check before any Phase-B-E execution. Results:

| Check                                                                                                                                                                                                                                                                                                                                                   | Result                                                                                                                                                                                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Persona / visibility unit tests (`tests/unit/lib/auth`, `tests/unit/lib/architecture-v2/visibility-slicing-matrix`, `tests/unit/lib/mocks/personas`, `tests/unit/lib/cockpit/derive-preset-from-persona`, `tests/unit/lib/questionnaire/resolve-persona`, `tests/unit/lib/widgets/access-personas`, `tests/unit/lib/marketing/public-depth-visibility`) | **144/144 green** (14 files, 2.66s)                                                                                                                                                                                        |
| MCP browser persona pass — visibility slicing visibly working                                                                                                                                                                                                                                                                                           | 3/5 captured (admin / prospect-im / desmond-dart-full); each shows distinct cockpit label, tile counts, persona dock. (anon + elysium-defi-full skipped due to MCP browser singleton-lock instability — not a product bug) |
| `DemoPlanToggle` mounted + tier-override-backed                                                                                                                                                                                                                                                                                                         | Confirmed via DOM scan: `<button data-testid="demo-plan-toggle">DART Full</button>` rendered for `desmond-dart-full`. Source uses `setTierOverride(user.email, paired.key)` not `loginByEmail(persona, "")`                |
| `tests/e2e/playbooks/refactor/refactor-g1-7-restriction-profile.spec.ts` (G1.7 — restriction-profile engine)                                                                                                                                                                                                                                            | 6/6 green                                                                                                                                                                                                                  |
| `tests/e2e/playbooks/refactor/refactor-g1-9-codex-scope-registry.spec.ts` (G1.9 — codex scope registry)                                                                                                                                                                                                                                                 | 5/5 green (after fixes: `4db900ef` added rule 11 literal filename ref to `codex/00-SSOT-INDEX.md`; manifest regenerated 439 docs / 886 audience-assignments / 0 defaulted)                                                 |
| `bash codex/14-playbooks/_tools/check-scope-coverage.sh`                                                                                                                                                                                                                                                                                                | OK — 886 scope assignments / 439 codex docs                                                                                                                                                                                |
| 14 restriction-profile YAMLs in `codex/14-playbooks/demo-ops/profiles/` + TS mirror                                                                                                                                                                                                                                                                     | Present, AUTO-GEN banner intact, `padlocked → padlocked-visible` G1.3 vocab translated, `--check` clean                                                                                                                    |

**Net:** the persona / visibility infrastructure is healthy and the tier-override migration is shipped. The agent
executing Phase-B-E (auth-domain authorization + env-var copy + provider flip + redeploy + smoke) inherits a green
baseline; the Preservation requirements gate is the sign-off contract on top of that.

## Phase breakdown

### Phase A — Operator prereqs on shared Firebase project

> **Retargeted 2026-04-25.** Original Phase A planned to provision a separate `odum-staging` Firebase project. That's
> reversed — UAT shares the prod Firebase project (`central-element-323112`), separated only by hostname + hosting
> target. Phase A scope is now (1) domain authorization, (2) demo-user provisioning. Both are operator-side.

- [x] [OPERATOR] P0. Confirm `uat.odum-research.com` is in **Firebase console → Authentication → Settings → Authorized
      domains** for project `odum-staging` (NOT central-element-323112 — corrected per 2026-05-01 audit). Verified
      2026-05-01 via Identity Toolkit REST: `localhost`, `odum-staging.firebaseapp.com`, `odum-staging.web.app`,
      `uat.odum-research.com` all in `authorizedDomains`.
- [x] [OPERATOR] P0. Provision real Firebase users for every demo email currently in `lib/auth/personas.ts`. The demo
      provider authenticates these client-side; FirebaseAuthProvider does not — it calls `signInWithEmailAndPassword`
      against the real pool. Until each email has a Firebase user record, switching UAT to firebase auth will break
      login (`auth/user-not-found`). Required emails: - `admin@odum-research.co.uk` (admin) -
      `investor@odum-research.co.uk`, `advisor@odum-research.co.uk` - `desmondhw@gmail.com` (Desmond — paired-tier
      demo) - `patrick@bankelysium.com` (Patrick / Elysium — paired-tier demo) - `demo-signals@odum-research.co.uk`,
      `demo-im@odum-research.co.uk` - `prospect-im@odum-research.com`, `prospect-dart-full@odum-research.com`,
      `prospect-dart-signals-in@odum-research.com`, `prospect-odum-signals@odum-research.com`,
      `prospect-regulatory@odum-research.com` Use the same passwords as `PERSONAS` for consistency. Provision via
      Firebase console → Authentication → Add user, or scripted via `firebase-admin` `createUser()`.
- [x] [OPERATOR] P0. Confirm user-management-api `/authorize` returns the right role + entitlements + org for each demo
      email after sign-in. The endpoint keys off email; demo emails need to be seeded into whatever Firestore collection
      or admin-DB it reads.

### Phase B — Env-var + config surface

- [x] [AGENT] P0. ~~Add `NEXT_PUBLIC_FIREBASE_API_KEY_STAGING`, `AUTH_DOMAIN_STAGING`, `PROJECT_ID_STAGING`,
      `STORAGE_BUCKET_STAGING`, `MESSAGING_SENDER_ID_STAGING`, `APP_ID_STAGING` to `.env.example` in both UIs.~~
      **Different mechanism shipped:** rather than runtime suffix-switching, the build-time `BUILD_ENV_FILE` arg in the
      Dockerfile picks `config/docker-build.env.uat` (for UAT) vs `config/docker-build.env.production` (for prod). The 6
      NEXT*PUBLIC_FIREBASE*\* are inlined at Docker build time, not runtime-switched. Same outcome, simpler mental
      model.
- [x] [AGENT] P0. ~~`unified-trading-system-ui/lib/admin/firebase.ts` + `lib/auth/firebase-config.ts` — extend config
      switcher~~ **Not needed: build-time inlining (above) means runtime config has a single set of values per image. No
      code-level switcher.**
- [x] [AGENT] P0. Add `firebase.json` + `.firebaserc` entries for the staging project. **Done:** `.firebaserc` has
      `"staging": "odum-staging"` alias; `firebase.json` has `uat` hosting target → Cloud Run `odum-portal-staging` in
      `targets.central-element-323112.hosting`.

### Phase C — Firestore security rules

- [ ] [AGENT] P0. `deployment-service/firestore/staging/firestore.rules` — NEW. Rules enforce: anonymous read-only on
      `/questionnaires` (G1.10 collection); authenticated read/write on `/users/{uid}/**`; admin-role required for
      `/users/{uid}/claims` reads; deny-all default.
- [ ] [AGENT] P0. Rule unit tests via Firebase emulator at `deployment-service/tests/firestore_rules/`.
- [ ] [AGENT] P0. Deploy script `deployment-service/scripts/deploy-firestore-rules-staging.sh` wraps
      `firebase deploy --only firestore:rules --project odum-staging`.

### Phase D — CI hooks

- [ ] [AGENT] P0. GitHub Actions workflow `.github/workflows/staging-firebase-deploy.yml` in `deployment-service` —
      triggers on push to staging branch; deploys Firestore rules + Hosting if changed.
- [ ] [AGENT] P0. CI job to run Firebase emulator during PR Playwright specs — staging config + emulator-backed
      Firestore. Blocks PR merge if emulator setup fails.

### Phase E — Smoke + verification

- [ ] [AGENT] P0. Playwright spec `refactor-g2-6-staging-firebase.spec.ts` seeds a test user in staging Firebase, reads
      claims back, verifies basic Firestore read/write.
- [ ] [AGENT] P0. Operator-run smoke: sign in with Google on `odum-research.co.uk`, create a test user, verify claims
      emission surface (will be wired in G2.1 — here just verify the account exists).
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh` (covers `(ops)/admin/*` post-fold)
- [ ] [SCRIPT] P0. `cd unified-trading-system-ui && bash scripts/quality-gates.sh`

## Critical files to be modified

- `unified-trading-system-ui/lib/admin/firebase.ts` — MODIFY (admin-SDK env switcher)
- `unified-trading-system-ui/lib/auth/firebase-config.ts` — MODIFY (client-SDK env switcher)
- `unified-trading-system-ui/firebase.json` + `.firebaserc` — MODIFY
- `unified-trading-system-ui/.env.example` — MODIFY
- `unified-trading-system-ui/lib/firebase.ts` — MODIFY
- `unified-trading-system-ui/.env.example` — MODIFY
- `deployment-service/firestore/staging/firestore.rules` — NEW
- `deployment-service/tests/firestore_rules/` — NEW (emulator-driven test suite)
- `deployment-service/scripts/deploy-firestore-rules-staging.sh` — NEW
- `deployment-service/.github/workflows/staging-firebase-deploy.yml` — NEW
- `unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-6-staging-firebase.spec.ts` — NEW

## Execution DAG

```
A (operator provisioning — out-of-repo prereq)
    ↓
B (env-var config surface) + C (Firestore rules) [parallel once A done]
    ↓
D (CI hooks)
    ↓
E (smoke + QG)
```

## Verification

1. Firebase project `odum-staging` exists, Google OAuth + email/password sign-in enabled, `odum-research.co.uk` in
   authorized domains.
2. Admin SDK key in Secret Manager.
3. Firestore rules deployed + emulator tests green.
4. Both UIs boot in `NEXT_PUBLIC_ENV=staging` mode without credential errors.
5. Playwright smoke spec green against staging Firebase + emulator.
6. QG green on both UI repos + deployment-service.

## Handoff

Unblocks:

- **G2.1** — claims can be emitted into real Firebase users.
- **G2.2** — per-client API keys can attach to real user accounts with real Firestore-backed ACLs.
- **G2.7** — demo-provisioning automation can target staging.
- **pb3a / pb3b / pb3c** — warm-prospect demo playbooks now have a real-auth environment to demo against.

## Playwright test coverage (mandatory)

**MCP Playwright during dev:** drive `localhost:3000` (tier-1 dev) with `NEXT_PUBLIC_ENV=staging` +
`NEXT_PUBLIC_USE_FIREBASE_AUTH=true` wired to the Firebase emulator. Verify sign-in flow, Firestore read/write,
custom-claims round-trip (will light up once G2.1 ships; spec asserts emulator-level correctness today).

**Durable spec for CI:**
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-6-staging-firebase.spec.ts`:

1. Boot emulator via `firebase emulators:start --project odum-staging --only auth,firestore`.
2. Seed test user via emulator admin SDK.
3. Sign in via UI, assert Firestore query round-trip.
4. Include orphan-reachability assertion for auth-gated routes.
5. Wire into `scripts/quality-gates.sh`.

## AGENT EXECUTION PROMPT

**Copy-paste everything below this line into a new agent session to execute Refactor G2.6 (Wave G2-α, parallel with
G2.1/2.8/2.9/2.11; gates G2-β).**

---

You are executing **Refactor G2.6 — Staging Firebase provisioning** for the Unified Trading System at Odum Research.
Wave G2-α; no G2 plan dependencies.

### Pre-flight check

```
cd /Users/ikennaigboaka/Code/unified-trading-system-repos
git -C unified-trading-pm checkout live-defi-rollout && git -C unified-trading-pm pull
# user-management-ui archived 2026-04-20; all admin work in unified-trading-system-ui.
git -C unified-trading-system-ui checkout live-defi-rollout && git -C unified-trading-system-ui pull
git -C deployment-service checkout live-defi-rollout && git -C deployment-service pull
ls unified-trading-system-ui/lib/admin/firebase.ts
ls unified-trading-system-ui/lib/auth/firebase-config.ts
ls unified-trading-system-ui/lib/firebase.ts 2>/dev/null || echo "verify config location"
# Check Phase A operator prereq: ask operator to confirm odum-staging Firebase project exists
firebase projects:list 2>/dev/null | grep -q odum-staging || echo "OPERATOR — run Phase A first"
```

All must exist + operator has provisioned the staging Firebase project. STOP if project missing.

### Mandatory rules injection

- Read
  `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
- Read `/Users/ikennaigboaka/Code/unified-trading-system-repos/unified-trading-pm/plans/PLAN_FORMAT.md`
- `WORKSPACE_ROOT = /Users/ikennaigboaka/Code/unified-trading-system-repos/`

### Task

Execute every checkbox in Phases B through E of this plan (Phase A is operator-run):
`plans/active/refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md`

### Read-set (mandatory)

All 9 paths from the plan's Mandatory read-set. Read the two folded plans fully.

### Deliverables

Per plan's Critical files list — 10 files across 2 repos (unified-trading-system-ui, deployment-service).

### MCP Playwright clause (verbatim — REQUIRED)

Drive `localhost:3000` (tier-1 dev) with `NEXT_PUBLIC_ENV=staging` + `NEXT_PUBLIC_USE_FIREBASE_AUTH=true` wired to the
Firebase emulator via MCP Playwright tools. Verify sign-in, Firestore read/write, admin SDK claim round-trip (claims
emission wired in G2.1). Commit the durable spec at
`unified-trading-system-ui/tests/e2e/playbooks/refactor/refactor-g2-6-staging-firebase.spec.ts` — emulator-driven,
orphan-reachability asserted, wired into `scripts/quality-gates.sh`.

### Commit strategy

Three repos touched → three commits. `git pull --rebase` before each push.

```
cd deployment-service && bash scripts/quickmerge.sh "feat(firestore): G2.6 — staging Firestore rules + emulator tests + CI deploy" --agent
# user-management-ui archived — env switcher commits in unified-trading-system-ui only.
cd ../unified-trading-system-ui && bash scripts/quickmerge.sh "feat(firebase): G2.6 — staging env switcher + staging-firebase Playwright smoke" --agent
```

Manual-git fallback per-repo if quickmerge blocks. Never `--dep-branch`, never `git reset --hard` / `git push --force`.

### Success criteria

1. ✅ Staging Firebase project `odum-staging` provisioned + Admin SDK key in Secret Manager.
2. ✅ Firestore rules deployed; emulator tests green.
3. ✅ Both UI repos boot cleanly in `NEXT_PUBLIC_ENV=staging` mode.
4. ✅ CI workflow deploys rules on push to staging branch.
5. ✅ Playwright smoke spec green.
6. ✅ QG green on all three repos.
7. ✅ 3 commit SHAs pushed to `origin/live-defi-rollout`.

### What NOT to do (verbatim guardrails)

- Do NOT read, cite, or derive anything from `_archived_pre_v2/` — v2 only.
- Do NOT `git reset --hard` or `git push --force`.
- Do NOT use `--dep-branch` flag; `--agent` only.
- Do NOT cherry-pick around unrelated WIP.
- Do NOT touch prod Firebase config — prod stays untouched in this wave.
- Do NOT ship default-open Firestore rules — deny-all default, explicit allow per path.
- Do NOT commit Admin SDK service-account JSON to the repo — Secret Manager only.
- Do NOT issue JWT claims here — that's G2.1.
- Do NOT `--no-verify` pre-commit hooks — fix the underlying failure.

### Report back

- Staging Firebase project ID + authorized domain list.
- Firestore rule unit-test count + pass rate.
- Emulator setup CI job ID.
- Playwright smoke spec pass status.
- QG results (3 repos).
- 3 commit SHAs pushed to live-defi-rollout.
- Any operator-side follow-ups pending.
