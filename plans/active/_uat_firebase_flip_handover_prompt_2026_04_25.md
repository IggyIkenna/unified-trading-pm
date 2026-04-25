---
title: Handover prompt — UAT-to-Firebase flip resumption
status: handover-prompt
created: 2026-04-25
---

# Handover prompt — UAT-to-Firebase flip (resumption)

> **How to use:** when the operator (Ikenna) has completed the Firebase user provisioning + domain authorization
> on the shared `central-element-323112` Firebase project, paste the prompt below into a fresh Claude Code session
> to resume the migration.

---

## Prompt to paste into next session

```
I'm resuming the UAT-to-Firebase migration from 2026-04-25. Background memory:
project_uat_firebase_flip_handover_2026_04_25.md.

Operator action confirmed complete (please verify before flipping):

1. uat.odum-research.com is in Firebase Authorized domains for project
   central-element-323112 (Auth → Settings).

2. Real Firebase user records exist on central-element-323112 for these
   demo emails (verify in Firebase console → Authentication → Users):

      admin@odum-research.co.uk          / OdumIR2026!
      investor@odum-research.co.uk       / OdumIR2026!
      advisor@odum-research.co.uk        / OdumIR2026!
      desmondhw@gmail.com                / odum-demo-2026
      patrick@bankelysium.com            / demo
      demo-signals@odum-research.co.uk   / OdumIR2026!
      demo-im@odum-research.co.uk        / OdumIR2026!

   (Plus optionally the prospect-*@odum-research.com emails — see
   plan G2.6 Phase A for the full list.)

3. user-management-api /authorize returns the right role + entitlements +
   org for each demo email (test by hitting the endpoint with a Firebase
   ID token from one of the demo accounts; verify the AuthUser shape
   matches the persona definition in lib/auth/personas.ts).

If all three confirmed, please:

1. Edit unified-trading-system-ui/config/docker-build.env.uat:
   - Change NEXT_PUBLIC_AUTH_PROVIDER=demo → firebase.
   - Paste the 6 NEXT_PUBLIC_FIREBASE_* values from
     docker-build.env.production directly below (apiKey, authDomain,
     projectId, storageBucket, messagingSenderId, appId — same values
     because UAT and prod share the project).
   - Remove the "Migration to firebase auth" comment block (it's no
     longer relevant once the flip lands).

2. Run quality gates:
   cd unified-trading-system-ui && bash scripts/quality-gates.sh

3. Deploy UAT:
   bash scripts/deploy-cloud-run.sh --env=uat --cloud

4. Smoke test on https://uat.odum-research.com/login — log in with each
   of the 7 required emails. Verify:

   a) Sign-in succeeds (no auth/user-not-found / auth/wrong-password).
   b) Dashboard renders the right tile shape per persona.
   c) DemoPlanToggle still flips entitlements without re-login for
      Desmond (DART Full ⇄ Signals-In) and Patrick (DeFi Full ⇄ DeFi
      Base) — the tier-override pattern is provider-agnostic, so this
      should Just Work.
   d) Investor lands on /investor-relations.
   e) demo-im-reports-only sees only the Reports tile (1 service /
      2 lifecycle stages).
   f) Admin sees the admin panel.

5. Commit the env-file change + push. Add a memory entry recording the
   flip date + verification matrix.

6. Update plan G2.6 — mark Phase A operator items [x] and Phase B agent
   items [x]. Move plan to archive once Phase E smoke is green.

If any sign-in fails, do NOT roll back the env file blindly. Diagnose:
- auth/user-not-found → operator missed that email, ask them to add it.
- auth/wrong-password → password mismatch with PERSONAS, ask operator
  to reset to the documented value.
- AuthUser missing entitlements → user-management-api /authorize not
  returning persona shape; check Firestore admin store seeding.

The refactor that unblocked this (lib/auth/tier-override.ts) is
already shipped + verified across all 6 personas in demo mode.
Decoupled from auth provider.
```

---

## Reference: what's already shipped (DON'T RE-DO)

- `unified-trading-system-ui/lib/auth/tier-override.ts` — tier-override module + TIER_BUNDLES (Desmond, Patrick).
- `unified-trading-system-ui/components/demo/DemoPlanToggle.tsx` — refactored to write override flag.
- `unified-trading-system-ui/hooks/use-auth.tsx` — applies tier-override at render time, listens for event.
- 2 new demo personas in `lib/auth/personas.ts`: `demo-signals-client`, `demo-im-reports-only`.
- Tile shapes + YAML profiles + restriction-profiles sync for the 2 new personas.
- All 6 personas verified end-to-end on UAT in demo mode.

## Reference: still operator-blocked

See `plans/active/refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md` Phase A.

## Reference commits

- UI `b18e2947` — `docker-build.env.uat` annotated with migration checklist.
- UI tier-override module shipped via `7aa7f102` (chore-sync absorbed earlier commits).
- UI `a42a9851` — dashboard "{N} services" math fix + per-instance FOMO lock badges.
- PM `fc579c01` — plan G2.6 + env-mode-philosophy retargeted to shared-project model.
