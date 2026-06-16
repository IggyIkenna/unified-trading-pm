---
title: Firebase project split — compute on prod, Firebase on staging
scope: [engineer]
owner: ikenna
status: reference
codified: 2026-05-07
sources:
  - plans/archive/_uat_firebase_flip_handover_prompt_2026_04_25.md (prior handover; archived)
  - plans/ai/refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md
  - codex/08-workflows/environment-mode-philosophy.md (Axis 2 — staging vs prod)
last_reviewed: 2026-05-17
---

# Firebase project split — compute on prod, Firebase on staging

The workspace runs UAT (`uat.odum-research.com`) on the **prod** GCP project for compute and the **staging** GCP project
for Firebase. This is intentional and codified here because new agents would otherwise assume the simpler "everything on
one project per environment" model.

## The split

| Concern                                                             | Project                         | Why                                                                                                                                                                                      |
| ------------------------------------------------------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Cloud Run compute (`odum-portal-staging`, the UAT-serving instance) | `central-element-323112` (prod) | Reuse prod's Cloud Build pipeline + image cache + image registry. Avoids duplicate infra-as-code for what's effectively the same Next.js bundle pointed at a different Firebase backend. |
| Firebase project (Auth + Firestore + Storage + Functions)           | `odum-staging`                  | Isolate staging user pool, Firestore documents, and storage from prod. UAT testing creates Firebase data; that must not pollute prod.                                                    |

The UAT bundle's `NEXT_PUBLIC_FIREBASE_PROJECT_ID=odum-staging` (in
`unified-trading-system-ui/config/docker-build.env.uat`) flips the Firebase SDK to talk to `odum-staging`, while the
Cloud Run service still runs on `central-element-323112`.

## Cross-project IAM bindings (the load-bearing detail)

For the prod-compute / staging-Firebase split to work, the prod compute service account needs Firebase access on the
staging project. The bindings live on `odum-staging` IAM:

```
Principal: 1060025368044-compute@developer.gserviceaccount.com  (prod's default compute SA)
Roles on odum-staging:
  - roles/datastore.user           (Firestore reads/writes)
  - roles/storage.admin            (Cloud Storage for Firebase)
  - roles/firebaseauth.admin       (Firebase Auth admin operations)
```

Without these three bindings, server-side Firebase Admin SDK calls from the UAT Cloud Run pod fail with
`PERMISSION_DENIED` even though the bundle is correctly pointing at `odum-staging`.

The bindings are configured operator-side; they're not in any IaC checked into the workspace. **If a fresh staging
Firebase project is provisioned (e.g. for a parallel sandbox), these three role grants must be re-applied** — that's the
part that's easy to miss.

## When to apply this pattern

- **UAT environments** that need isolated Firebase data while reusing prod's compute pipeline. This is the canonical
  case.
- **Per-customer demo environments** where you want one Firebase project per customer (data isolation) but a single
  shared compute pipeline.
- **NOT for prod itself** — prod runs Cloud Run + Firebase both on `central-element-323112`. Splitting prod across
  projects would add latency for no isolation benefit.

## Diagnostic hints when the split fails

| Symptom                                                            | Likely cause                                                                                                                                              |
| ------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `auth/unauthorized-domain` on UAT sign-in                          | `uat.odum-research.com` not added to `odum-staging` Firebase Console → Authentication → Settings → Authorized domains                                     |
| `auth/user-not-found` on demo emails                               | `seed-firebase-users.mjs --env=staging` not run against `odum-staging`                                                                                    |
| Sign-in succeeds but `/authorize` returns empty entitlements       | `user-management-api` /authorize endpoint reads from `odum-staging` Firestore (not prod's), and the demo email row hasn't been seeded into that Firestore |
| Server-side Firebase Admin SDK calls fail with `PERMISSION_DENIED` | One or more of the three cross-project IAM bindings missing on `odum-staging` for `1060025368044-compute@...`                                             |

## Related docs

- `plans/ai/refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md` — the original provisioning plan.
- `codex/08-workflows/environment-mode-philosophy.md` § Axis 2 (staging vs prod).
- `codex/05-infrastructure/auth-setup.md` — Firebase Auth patterns.
