---
scope: [engineer, admin]
---

<!-- POST_PLAN_BANNER_2026_05_06_FINAL -->

> **Post-2026-05-06** — read [`../POST_PLAN_REALITY_2026_05_06.md`](../POST_PLAN_REALITY_2026_05_06.md) before code/doc
> changes informed by this doc. Active plans: writegate-honest-coverage, predictions-canonical_question_group,
> data-status-multi-axis-shard. If this doc disagrees with active plans, the plans win. Flag conflicts to user.

# Environments — three tiers

> **Layer:** Implementation. Narrative lives in [../experience/](../experience/).

Odum runs in three distinct environments, each with its own domain, Firebase project, and data scope.

| Tier    | Name       | Domain                                           | Auth source                                                        | Data source                                         | Who uses it                    |
| ------- | ---------- | ------------------------------------------------ | ------------------------------------------------------------------ | --------------------------------------------------- | ------------------------------ |
| dev     | Local      | `localhost:3100` (T0) / `localhost:3000` (T1/T2) | Demo provider (localStorage personas) OR local Firebase dev config | Mock data, interactive state in `.local-dev-cache/` | Odum engineers                 |
| staging | Staging    | `odum-research.co.uk`                            | Firebase staging project (target) / demo provider (interim)        | Synthetic + demo data; no real positions            | Demo prospects + Odum internal |
| prod    | Production | `odum-research.com`                              | Firebase production `central-element-323112`                       | Real positions, real capital, real reporting        | Paying clients + Odum internal |

Sibling docs:

- [local-dev.md](local-dev.md)
- [staging-odum-research-co-uk.md](staging-odum-research-co-uk.md)
- [production-odum-research-com.md](production-odum-research-com.md)

## Promotion flow

```
Local dev → tested via quality-gates.sh + Playwright
    ↓ (push to live-defi-rollout branch)
SIT (system integration test) → auto-promote to staging
    ↓ (manual admin approval via GHA workflow)
Staging → prospect demos + internal QA
    ↓ (manual admin approval via GHA workflow)
Production → real clients
```

No direct push from local → staging or staging → prod. All promotions are gated by CI/CD + manual approvals where
listed.

## Env-var differences (UI)

| Env var                            | Local                   | Staging                                | Production                                                      |
| ---------------------------------- | ----------------------- | -------------------------------------- | --------------------------------------------------------------- |
| `NEXT_PUBLIC_AUTH_PROVIDER`        | `demo`                  | `firebase` (target) / `demo` (interim) | `firebase`                                                      |
| `NEXT_PUBLIC_MOCK_API`             | `true`                  | `true` (interim)                       | `false`                                                         |
| `NEXT_PUBLIC_USER_MGMT_API_URL`    | `http://localhost:8017` | staging user-mgmt-api Cloud Run URL    | `https://user-management-api-1060025368044.us-central1.run.app` |
| `NEXT_PUBLIC_BRIEFING_ACCESS_CODE` | optional                | rotating per prospect                  | rotating per prospect                                           |
| `NEXT_PUBLIC_SITE_URL`             | `http://localhost:3000` | `https://odum-research.co.uk`          | `https://odum-research.com`                                     |

Build-time env is injected via `BUILD_ENV_FILE` arg in the Dockerfile. See
[config/docker-build.env.\*](unified-trading-system-ui/config/) for the three build configs.

## Parity requirements

For confidence in staging → prod promotion, the stacks must be as identical as possible apart from the env-var table
above:

- ✅ Same Docker image (different build-env-file)
- ✅ Same Next.js version + pnpm-lock
- ✅ Same component tree (no `process.env.NODE_ENV==='production'` feature gates)
- ✅ Same Playwright test coverage
- ⚠ Different data — unavoidable; but schemas must match exactly
- ⚠ Different Firebase projects — unavoidable; but same auth flow

## Related

- Local dev details (transcluded from 08-workflows): [local-dev.md](local-dev.md)
- Auth per env: [../authentication/](../authentication/)
- Runtime topology and SLA tiers:
  [../../04-architecture/client-isolation-sla-and-runtime-profiles.md](../../04-architecture/client-isolation-sla-and-runtime-profiles.md)
