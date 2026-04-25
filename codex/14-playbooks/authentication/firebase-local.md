---
scope: [engineer, admin]
---

# Firebase local — emulator suite for dev

> **Layer:** Implementation. SSOT for the local-dev branch of the three-environment auth model. Sibling docs:
> [firebase-staging.md](firebase-staging.md), [firebase-production.md](firebase-production.md).

## What it is

Local dev runs against the **Firebase Emulator Suite** — Auth + Firestore + Storage emulators bound to localhost. The
Next.js bundle uses the **same code path** as staging and prod; only the project ID + emulator-host env vars change.
Result: the local dev experience matches staging line-for-line, just with empty (or hydrated) data.

| Aspect      | Local emulator                                                          |
| ----------- | ----------------------------------------------------------------------- |
| Project ID  | `odum-local-dev` (placeholder — never resolves to real GCP)             |
| Auth        | localhost:9099 (Node)                                                   |
| Firestore   | localhost:8080 (Java JAR)                                               |
| Storage     | localhost:9199 (Java JAR)                                               |
| Emulator UI | localhost:4000 (browser inspector — Auth users / docs)                  |
| Hub port    | localhost:4400 (internal coordination)                                  |
| Persistence | `.local-dev-cache/emulator-state/` (gitignored, auto-saved on shutdown) |

## How to start it

```bash
cd unified-trading-system-ui
bash scripts/dev-tiers.sh --tier 0          # UI + emulators (default since 2026-04-25)
bash scripts/dev-tiers.sh --tier 0 --no-firebase-local  # opt-out (rare)
bash scripts/dev-tiers.sh --stop            # kill everything
```

`--firebase-local` is **on by default for every tier** so a developer can never accidentally write drafts / claims /
file uploads to the real `odum-staging` or `central-element-323112` projects from their machine. Opt-out is the rare
case where you want to point local at a real Firebase project to debug a staging-only bug.

### Java requirement

Firestore + Storage emulators are JVM apps. The dev-tiers script auto-locates a brew-installed OpenJDK 21 (Apple Silicon
and Intel paths both probed) and sets `JAVA_HOME`. If neither is installed:

```bash
brew install openjdk@21
```

The macOS `/usr/bin/java` shim is detected and bypassed — it only opens a "Please install Java" dialog and isn't usable.

## Three deviation switches

| Switch                      | What changes                                                                       | When to use                                   |
| --------------------------- | ---------------------------------------------------------------------------------- | --------------------------------------------- |
| `--no-firebase-local`       | Local server talks to a real Firebase project (env-controlled)                     | Reproducing a staging-only bug                |
| `NEXT_PUBLIC_MOCK_API=true` | UI uses client-side mock responses, no Firebase at all                             | Deterministic test runs, no auth              |
| Custom dev seed             | Edit `scripts/admin/seed-firebase-users.dev.mjs`, run `npm run emulators:seed:dev` | Local-only fixtures (edge cases, scale tests) |

## Seeding personas

Default state on first emulator boot is **empty Auth pool**. Two seed paths:

1. **Standard 23 personas** (mirrors what's in `odum-staging`):

   ```bash
   npm run emulators:seed
   ```

   Creates the same email → role → entitlements mapping that staging uses. Single shared password `demo123` (≥ 6 chars
   per Firebase minimum). Run once after first emulator boot; subsequent boots persist the pool via `--export-on-exit`.

2. **Local-only dev personas** for whatever flow you're working on:

   ```bash
   npm run emulators:seed:dev   # reads scripts/admin/seed-firebase-users.dev.mjs
   ```

   Edit the `DEV_PERSONAS` array in that file — it's stub'd by default. Lives separately from the staging seed so weird
   edge-case fixtures never accidentally land on staging.

## Hydrate from staging snapshot

For development that needs **realistic data shape** (apps + groups + entitlements + audit log

- onboarding requests, not just Auth users), pull a snapshot from `odum-staging`:

```bash
npm run emulators:hydrate-from-staging
```

What the script does:

1. `gcloud firestore export gs://odum-staging.firebasestorage.app/firestore-exports/<ts>` — managed export to a temp GCS
   prefix in the staging project.
2. `gsutil cp -r ...` — mirrors the export to `.local-dev-cache/firestore-staging-snapshot/`.
3. `firebase auth:export ...` — dumps the staging Auth pool to `.local-dev-cache/auth-staging-export.json` (Auth has no
   managed export, so this uses firebase CLI + ADC).

Then on next emulator boot, the import dir is auto-loaded via the `--import=.local-dev-cache/emulator-state` flag in
`package.json` `dev:firebase-local`. For the initial load you swap the path:

```bash
firebase emulators:start \
  --only auth,firestore,storage \
  --project=odum-local-dev \
  --import=.local-dev-cache/firestore-staging-snapshot \
  --export-on-exit=.local-dev-cache/emulator-state

firebase auth:import .local-dev-cache/auth-staging-export.json --project=odum-local-dev
```

After that first import, `.local-dev-cache/emulator-state/` becomes the persistent dev pool — edits made in dev (e.g.
creating test users via `/admin/onboard`) save back to it on shutdown and reload on next start.

## Wire shape parity with staging

Every native `/api/v1/*` route uses the same Admin SDK code path locally as on Cloud Run. The only difference: which
project the SDK connects to. See:

- Identity enrichment: `app/api/v1/authorize/route.ts` → `lib/admin/server/auth-context.ts::computeEffectiveAccess`
- Signup: `app/api/v1/signup/route.ts` → Admin SDK `auth.createUser` + `usersCollection().doc().set()`
- Admin CRUD: 54 routes under `app/api/v1/*` → 15 Firestore collections in `lib/admin/server/collections.ts`

A bug reproducible against the local emulator is reproducible against staging (modulo data).

## Persistence model

| State           | Where it lives                                      | Survives emulator stop?   |
| --------------- | --------------------------------------------------- | ------------------------- |
| Auth users      | `.local-dev-cache/emulator-state/auth_export/`      | ✅ via `--export-on-exit` |
| Firestore docs  | `.local-dev-cache/emulator-state/firestore_export/` | ✅                        |
| Storage objects | `.local-dev-cache/emulator-state/storage_export/`   | ✅                        |
| Function logs   | `.local-dev-cache/logs/`                            | ✅ (rolling)              |

Wipe everything: `bash scripts/dev-tiers.sh --reset` (stops emulators, deletes `.local-dev-cache/` entirely, restarts
with empty state).

## Common pitfalls

- **JAR download stalls on first boot** — Firestore + Storage emulators each pull ~50MB JARs to
  `~/.cache/firebase/emulators/` on first run. If your network is flaky, run `firebase setup:emulators:firestore` and
  `firebase setup:emulators:storage` once with a good connection before booting dev-tiers.
- **Port 9099 / 8080 / 9199 / 4000 / 4400 collisions** — Other dev tools (Adminer, Hadoop UI, another Next.js process)
  sometimes camp these. `lsof -ti:9099,8080,9199,4000,4400 | xargs -r kill` clears them. Re-runs of dev-tiers do not
  auto-kill these.
- **Java missing** — emulators die with `Process java -version exited with code 1`. Install via brew (see above); the
  dev-tiers script auto-locates after install.
- **"emulator hub on port 4400"** warning — benign; means a previous boot didn't shut down cleanly. Falls back to 4401
  and recovers.
