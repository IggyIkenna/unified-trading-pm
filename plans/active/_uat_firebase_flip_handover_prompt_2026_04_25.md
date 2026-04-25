---
title: Handover prompt — UAT-to-Firebase flip resumption (revised end-of-day)
status: handover-prompt
created: 2026-04-25
revised: 2026-04-25 (end-of-day — corrected mental model)
---

# Handover prompt — UAT-to-Firebase flip (resumption)

> **Use this when** the operator has confirmed (a) `seed-firebase-users.mjs --env=staging` has been run on
> `odum-staging`, (b) `uat.odum-research.com` is in `odum-staging` Authorized Domains, (c) user-management-api
> `/authorize` Firestore store on `odum-staging` is seeded for the demo emails. Then paste the prompt below into
> a fresh Claude Code session.

> **Important context for the next agent:** the env-file flip is ALREADY committed (UI commit `b5c1c757`). What
> remains is operator-side user seeding + agent-side QG + redeploy + smoke. Don't re-flip the env file.

---

## Prompt to paste into next session

```
I'm resuming the UAT-to-Firebase migration. Background memory:
- project_uat_firebase_flip_handover_2026_04_25.md (this thread's handover)
- project_odum_staging_firebase_isolation_2026_04_25.md (operator-side
  IAM topology + cross-project SA bindings)
- feedback_compute_vs_firebase_project_split.md (the architectural pattern)

Current state on origin/live-defi-rollout:

1. unified-trading-system-ui/config/docker-build.env.uat is already
   flipped (UI commit b5c1c757):
     NEXT_PUBLIC_AUTH_PROVIDER=firebase
     NEXT_PUBLIC_FIREBASE_PROJECT_ID=odum-staging
     (5 other NEXT_PUBLIC_FIREBASE_* values for odum-staging)
   Don't re-flip. Comment block in the env file has the full
   compute-vs-Firebase split explanation.

2. UAT compute still runs on prod GCP project (central-element-323112)
   Cloud Run service odum-portal-staging. Only the Firebase backend is
   on odum-staging. Cross-project IAM bindings already in place: prod
   compute SA 1060025368044-compute@developer.gserviceaccount.com has
   datastore.user + storage.admin + firebaseauth.admin on odum-staging.

3. lib/auth/tier-override.ts ships the provider-agnostic toggle.
   DemoPlanToggle verified across 6 personas in demo mode earlier
   today; should keep working unchanged after the flip lands in
   production deployment.

4. Firebase 6-char password minimum: personas with password "demo" in
   lib/auth/personas.ts get bumped to "demo123" inside
   scripts/admin/seed-firebase-users.mjs at user-creation time. The
   personas.ts file itself stays at "demo" so dev demo-provider keeps
   working (it does string-equality client-side, no policy enforcement).

Please do, in this order:

A. VERIFY operator prereqs are done (ask Ikenna to confirm if unsure):
   - scripts/admin/seed-firebase-users.mjs --env=staging has been run.
     The script's STAGING_USERS list should cover at minimum:
       admin@odum-research.co.uk          / OdumIR2026!
       investor@odum-research.co.uk       / OdumIR2026!
       advisor@odum-research.co.uk        / OdumIR2026!
       desmondhw@gmail.com                / odum-demo-2026
       patrick@bankelysium.com            / demo123  (bumped from demo)
       demo-signals@odum-research.co.uk   / OdumIR2026!
       demo-im@odum-research.co.uk        / OdumIR2026!
     Plus optionally the 5 prospect-*@odum-research.com / demo123.
     If the script is missing entries, patch it (don't run yet).
     If already run, ask operator for the run output / verify via
     Firebase console → odum-staging → Authentication → Users.

   - uat.odum-research.com is in Firebase console → odum-staging →
     Authentication → Settings → Authorized domains. Without this,
     sign-ins from UAT hit auth/unauthorized-domain.

   - user-management-api /authorize returns role + entitlements + org
     for each demo email. The endpoint keys off email; demo emails
     need to be seeded into whatever Firestore collection / admin
     store the API reads from (now living in odum-staging's Firestore,
     not prod's).

B. RUN quality gates:
     cd unified-trading-system-ui && bash scripts/quality-gates.sh

C. DEPLOY UAT (still targets the same Cloud Run service on
   central-element-323112; only the bundle's Firebase config changes):
     bash scripts/deploy-cloud-run.sh --env=uat --cloud
   Wait for completion (typically 5–10 min via Cloud Build with layer
   cache).

D. SMOKE TEST on https://uat.odum-research.com/login. Use a fresh
   browser profile (clear localStorage + cookies; or playwright
   --isolated). For each of the 7 required emails:

   1. Sign-in succeeds (no auth/user-not-found, no
      auth/wrong-password, no auth/unauthorized-domain).
   2. Lands on the right surface (admin-odum → admin-dashboard or
      wherever it routes; investor → /investor-relations; clients →
      /dashboard).
   3. Dashboard renders the persona-appropriate tile shape:
      - admin: all 5 tiles (DART, Odum Signals, Reports, IR, Admin)
      - investor: lands on /investor-relations
      - desmondhw@gmail.com: DART + Reports tiles, DemoPlanToggle
        showing "DART Full" (emerald). Click it — toggle flips to
        "Signals-In" (amber) WITHOUT a re-login. tier-override-v1 in
        localStorage. FOMO grid Signals-In banner re-renders.
      - patrick@bankelysium.com: DART + Reports tiles, toggle
        "DeFi Full" ⇄ "DeFi Base"
      - demo-signals: DART + Reports tiles, no toggle
      - demo-im: Reports tile only ("1 service across 2 lifecycle
        stages"), no toggle
   4. Sign out, sign back in — state persists correctly.

E. COMMIT memory + plan updates after smoke is green:
   - Add a memory entry recording the flip date + verification matrix.
   - Update plans/active/refactor_g2_6_staging_firebase_provisioning_
     2026_04_20.plan.md — mark Phase A operator items [x] and Phase B
     agent items [x]. Status update should reflect the deployed
     reality: separate odum-staging Firebase project + shared prod
     Cloud Run compute (NOT the "shared everything" model some
     intermediate revisions described).
   - Update unified-trading-pm/codex/08-workflows/environment-mode-
     philosophy.md §Axis 2 — staging IS odum-staging Firebase, prod
     IS central-element-323112 Firebase. Cloud Run compute is on
     central-element-323112 for both URLs.

F. If all green, the migration is complete. Plan G2.6 can move to
   plans/archive/ if you have unlock-plan authority (otherwise leave
   locked_by: live-defi-rollout for human review).

Diagnostic guide if something fails:

- auth/user-not-found → seed script missed that email; re-run.
- auth/wrong-password → password mismatch with the bumped value
  (demo → demo123 for short-password personas).
- auth/unauthorized-domain → uat.odum-research.com not in Authorized
  domains for odum-staging.
- AuthUser missing entitlements (sign-in OK but tile-less dashboard) →
  user-management-api /authorize not seeded with persona shape on
  odum-staging Firestore.
- tier-override flag not flipping entitlements after toggle click →
  TIER_OVERRIDE_EVENT not firing or useAuth listener missing; check
  hooks/use-auth.tsx.

Files to read for context:
- unified-trading-system-ui/config/docker-build.env.uat (already
  flipped; comment block has the architecture)
- unified-trading-system-ui/scripts/admin/seed-firebase-users.mjs
  (verify STAGING_USERS list before invoking)
- unified-trading-system-ui/lib/auth/tier-override.ts (TIER_BUNDLES)
- unified-trading-system-ui/lib/auth/personas.ts (definitions)
- unified-trading-system-ui/lib/auth/firebase-provider.ts (login flow)
```

---

## Reference: what's already shipped (DON'T RE-DO)

- `unified-trading-system-ui/config/docker-build.env.uat` flipped to firebase + odum-staging config (UI `b5c1c757`).
- `unified-trading-system-ui/lib/auth/tier-override.ts` — tier-override module + TIER_BUNDLES (Desmond, Patrick).
- `unified-trading-system-ui/components/demo/DemoPlanToggle.tsx` — refactored to write override flag.
- `unified-trading-system-ui/hooks/use-auth.tsx` — applies tier-override at render time.
- `unified-trading-system-ui/lib/auth/personas.ts` — 2 new demo personas (`demo-signals-client`,
  `demo-im-reports-only`).
- Tile shapes + YAML profiles + restriction-profiles sync for the 2 new personas.
- 6-persona end-to-end smoke verified on UAT in demo mode.
- `seed-firebase-users.mjs` STAGING_USERS list with `demo`→`demo123` password bump.
- Cross-project IAM: prod compute SA has `datastore.user` + `storage.admin` + `firebaseauth.admin` on
  `odum-staging`.

## Reference: what's still pending

- Operator: run seed script + confirm Authorized domains + seed user-mgmt-api authorize store on odum-staging.
- Agent (next session): QG + redeploy + 6-persona smoke + commit memory/plan updates.

## Reference: deferred follow-on (when MOCK_API flips to false)

- `unified-trading-api` Firebase ID token verification needs to handle `odum-staging`-issued tokens. Two paths:
  (a) deploy a separate API instance on `odum-staging`, (b) dual-verify on the existing API. Out of scope until
  the day MOCK_API is flipped.
