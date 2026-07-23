---
doc_type: codex-ssot
title: Firebase project split — compute on prod, Firebase on staging
summary:
  "UAT (uat.odum-research.com) runs Cloud Run compute on the PROD project (central-element-323112) but Firebase
  (Auth/Firestore/Storage) on the odum-staging project — a deliberate split needing three cross-project IAM bindings
  (datastore.user + storage.admin + firebaseauth.admin) on odum-staging for the prod compute SA. Server-side API routes
  MUST use firebase-admin, never the client SDK (which silently no-ops on API routes, returning 200 + empty
  submissionId)."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [ui, firebase, infrastructure, staging, auth, gcp]
related: [/codex/05-infrastructure/auth-setup.md, /codex/08-workflows/environment-mode-philosophy.md]
created: 2026-05-07
authoritative_for: [firebase project split topology]
referenced_by:
  [/codex/05-infrastructure/deployment-ui-architecture.md, /codex/05-infrastructure/deployment-ui-environment-tiers.md]
owner: ikenna
last_reviewed: 2026-06-25
code_refs:
codified: 2026-05-07
sources:
  [
    plans/archive/_uat_firebase_flip_handover_prompt_2026_04_25.md (prior handover; archived),
    plans/ai/refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md,
    /codex/08-workflows/environment-mode-philosophy.md (Axis 2 — staging vs prod),
  ]
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

## Server-side API routes must use `firebase-admin`, never the client SDK (HARD RULE)

**Rule**: all Next.js API routes (files under `app/api/` or `pages/api/`) that read or write Firebase (Firestore, Auth,
Storage) **must** import from `firebase-admin`, not from the Firebase client SDK (`firebase/app`, `firebase/firestore`,
etc.).

**Why the client SDK silently fails on API routes**: the client SDK is initialised from `NEXT_PUBLIC_FIREBASE_*`
environment variables. On UAT (and in server-side Node.js contexts generally) those variables are either absent or point
at the wrong project, so the SDK initialises against an unreachable or wrong Firebase backend. The call does **not**
throw — it succeeds from the SDK's perspective and returns HTTP 200 to the browser, but **no data is written to
Firestore** and the response body contains an empty `submissionId` (or whichever write-confirmation field the route
returns). This makes the bug almost invisible: the UI shows success, the response is 200, and the failure only surfaces
when a downstream read or an audit finds the expected document is absent.

**Correct pattern** (server-side route):

```ts
// ✅ server-side — uses firebase-admin, reads GCP ADC / service-account credentials
import { getFirestore } from "firebase-admin/firestore";
import { initializeApp, getApps, cert } from "firebase-admin/app";
```

**Banned pattern** (server-side route):

```ts
// ❌ client SDK on an API route — silently no-ops, returns 200 with empty submissionId
import { getFirestore } from "firebase/firestore";
import { initializeApp } from "firebase/app";
```

The client SDK is correct and expected in browser-executed code (React components, client-side hooks). The split is SDK
boundary, not feature boundary — the same Firestore collection can be accessed from both SDKs; what changes is the
authentication path and where credentials live.

**Composes with the cross-project IAM split above**: server-side `firebase-admin` calls authenticate via the compute
service account (ADC), which is why the three cross-project IAM bindings on `odum-staging` are load-bearing — without
them, the correct `firebase-admin` call still fails with `PERMISSION_DENIED`.

## Related docs

- `plans/ai/refactor_g2_6_staging_firebase_provisioning_2026_04_20.plan.md` — the original provisioning plan.
- `/codex/08-workflows/environment-mode-philosophy.md` § Axis 2 (staging vs prod).
- `/codex/05-infrastructure/auth-setup.md` — Firebase Auth patterns.
