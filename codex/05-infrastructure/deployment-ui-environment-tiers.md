---
scope: [engineer, operator]
---

# Deployment-UI environment tiers

## Why

Operators interact with deployment-UI across multiple environments: pure-local development, mock-API-against-emulators,
real-cloud-from-laptop, and full production. Each tier is the same Next.js app + the same React routes; what changes is
the API endpoint resolution, the auth source, and which cloud buckets the UI can reach. This doc names the four tiers
and the boundaries between them.

## The four tiers

| Tier | Name              | Auth source              | API endpoint                                  | Cloud buckets reached         | Use case                                                  |
| ---- | ----------------- | ------------------------ | --------------------------------------------- | ----------------------------- | --------------------------------------------------------- |
| 0    | Mock-only         | None / dev-stub          | `NEXT_PUBLIC_MOCK_API=true` in-repo fixtures  | None                          | Frontend dev without backend                              |
| 1    | Local + Firebase  | Firebase Emulator        | localhost:8004 (deployment-api dev server)    | None (mock) or local Pub/Sub  | Auth-flow testing; mid-fidelity UI dev                    |
| 2    | Real-cloud-laptop | Real Firebase project    | localhost:8004 with `CLOUD_PROVIDER=gcp`      | Real GCS rollup buckets       | Reproduce a prod data-status bug locally                  |
| 3    | Production        | Real Firebase + Cloud Run | shared `uts-shared-deployment-api` Cloud Run  | Real GCS + AWS S3 (dual-cloud) | Operator-facing live dashboard                            |

## Tier-routing in the UI

`deployment-ui/src/contexts/CloudProviderContext.tsx` resolves the API base via `window.location.hostname`:

- `localhost` → port 8004 (Tier 0/1/2 — talk to local deployment-api process).
- everything else → same-origin proxy via Cloud Run (Tier 3).

The hardcoded port 8004 is a Tier 0/1/2 convention; changing it breaks the UI's same-origin proxy in production and
every widget renders "Failed to load".

## Auth boundary

| Tier | Auth path                                                                       |
| ---- | -------------------------------------------------------------------------------- |
| 0    | None — `VITE_SKIP_AUTH=true`                                                     |
| 1    | Firebase Emulator (auto-detected via `FIREBASE_AUTH_EMULATOR_HOST`)              |
| 2    | Real Firebase project — same path as production                                  |
| 3    | Real Firebase + RBAC enforced server-side                                        |

Firebase Local handoff details: [`../14-playbooks/authentication/firebase-local.md`](../14-playbooks/authentication/firebase-local.md).

## Restart command (Tier 0/1/2)

```bash
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh           # restart both api + ui
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --api      # restart deployment-api only
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --ui       # restart deployment-ui only
bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh --stop     # stop both
```

This script is the canonical local restart; supersedes `dev-start.sh --api deployment-api` + `cd deployment-ui && npm
run dev`. Always real cloud-mode (`CLOUD_PROVIDER=gcp`, `CLOUD_MOCK_MODE=false`).

## Cross-references

- Deployment-UI architecture (lifecycle tabs, full UI shape):
  [`deployment-ui-architecture.md`](deployment-ui-architecture.md)
- Runtime tiers (back-end side): [`runtime-tiers-and-deployment.md`](runtime-tiers-and-deployment.md)
- Firebase local: [`../14-playbooks/authentication/firebase-local.md`](../14-playbooks/authentication/firebase-local.md)
- Live deployment monitoring (event verification): [`live-deployment-monitoring.md`](live-deployment-monitoring.md)
