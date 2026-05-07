---
superseded_by: [five_space_ia_execution_child_plan_2026_04_17.md]
reconciliation_status: superseded
reconciliation_date: 2026-04-25
---

> **SUPERSEDED 2026-04-25 by
> [five_space_ia_execution_child_plan_2026_04_17.md](./five_space_ia_execution_child_plan_2026_04_17.md).** Audit-matrix
> is input worksheet to the child execution plan; child is the canonical delivery plan Original scope retained for
> history. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

# Five-space IA — Phase 0 audit matrix (dev | staging | prod)

This worksheet captures **five engagement spaces** × **environment** for CI/CD, Firebase, mock vs real data, and
taxonomy impact on the **Investment management** catalogue and **Platform** terminal. It is the input to the child
execution plan (`five_space_ia_execution_child_plan_2026_04_17.md`).

## Spaces (canonical)

| Space                     | Primary routes / surfaces                                                                              | Auth model                                                                                                                                       |
| ------------------------- | ------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Public**                | `/`, `/investment-management`, `/platform`, `/regulatory`, `/firm`, `/contact`, legacy `public/*.html` | None                                                                                                                                             |
| **Lighter-gate depth**    | `/briefings`, `/briefings/*` (pre-commitment narrative)                                                | Optional invite code when `NEXT_PUBLIC_BRIEFING_ACCESS_CODE` is set; session key `odum-briefing-session` (distinct from staging gate + app auth) |
| **IR**                    | `/investor-relations/*`                                                                                | Firebase or demo; entitlements `investor-*`, optional `investor-archive`                                                                         |
| **Investment management** | `/services/research/strategy/catalog`, families, detail                                                | Signed-in; strategy catalogue source `NEXT_PUBLIC_STRATEGY_CATALOG_SOURCE` + `NEXT_PUBLIC_MOCK_API`                                              |
| **Platform**              | `/dashboard`, `/services/*` (data, research, build, execution, reports), terminal                      | Signed-in; `NEXT_PUBLIC_MOCK_API`, gateway rewrites                                                                                              |

## Matrix (fill per cell)

Columns: **CI/CD** | **Firebase / Auth** | **Mock vs real** | **Taxonomy / UX (families, archetypes, terminal
visibility)**

### Dev (local)

| Space        | CI/CD                | Firebase                                         | Mock vs real                                                                    | Taxonomy                                                                                      |
| ------------ | -------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Public       | `pnpm dev`; no image | `NEXT_PUBLIC_AUTH_PROVIDER` often `demo` locally | Marketing copy; data service pages may use `orgMode="demo"` for catalogue       | N/A                                                                                           |
| Lighter-gate | Same                 | Same                                             | JSON/MD in repo                                                                 | N/A                                                                                           |
| IR           | Same                 | Demo personas or Firebase if configured          | Static / in-app decks                                                           | N/A                                                                                           |
| IM           | Same                 | Same                                             | Default `STRATEGY_CATALOG_SOURCE`: mock if `MOCK_API=true`, else API to gateway | Mock fixture categories vs API `domain`/`family`; align with architecture-v2 SSOT in PM codex |
| Platform     | Same                 | Same                                             | `MOCK_API`, fixtures in widgets                                                 | Terminal grouping vs service entitlements — audit deltas in child plan                        |

### Staging (e.g. co.uk image)

| Space        | CI/CD                                                                                           | Firebase                                                                                                                                                                                           | Mock vs real                                                                        | Taxonomy                                                                  |
| ------------ | ----------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Public       | `config/docker-build.env.staging` baked at build; `deploy-cloud-run.sh` → `odum-portal-staging` | **Default image:** `NEXT_PUBLIC_AUTH_PROVIDER=demo`, empty Firebase web keys. **Firebase staging:** use `docker-build.env.staging.firebase.example` + `--build-env-file` (see UI `DEPLOYMENT.md`). | `NEXT_PUBLIC_MOCK_API=true`                                                         | Same as dev                                                               |
| Lighter-gate | `PUBLIC_MARKETING_PATHS` includes `/briefings` in `staging-gate.tsx`                            | N/A                                                                                                                                                                                                | Real copy; no market feeds                                                          | N/A                                                                       |
| IR           | Same image as platform                                                                          | Demo / future staging Firebase project                                                                                                                                                             | Decks real; archive gated by `investor-archive`                                     | N/A                                                                       |
| IM           | Same                                                                                            | Same                                                                                                                                                                                               | Staging defaults to mock catalogue unless `NEXT_PUBLIC_STRATEGY_CATALOG_SOURCE=api` | API catalogue from UAC registry when enabled                              |
| Platform     | Same                                                                                            | Same                                                                                                                                                                                               | Mock-leaning staging                                                                | Reporting/terminal mock branches — see mock delta in `docs/DEPLOYMENT.md` |

### Production (.com)

| Space        | CI/CD                                         | Firebase                                                 | Mock vs real                                                  | Taxonomy                                                                                                       |
| ------------ | --------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Public       | `docker-build.env.production` + Hosting → Run | `NEXT_PUBLIC_AUTH_PROVIDER=firebase`, prod web keys only | `NEXT_PUBLIC_MOCK_API=false`                                  | N/A                                                                                                            |
| Lighter-gate | Same                                          | Same                                                     | Same                                                          | N/A                                                                                                            |
| IR           | Same                                          | Prod Firebase + backend capabilities                     | Live entitlements                                             | N/A                                                                                                            |
| IM           | Same                                          | Same                                                     | Catalogue should use **API** unless explicitly forced to mock | Family/domain from `/api/analytics/strategies/catalog`; detail pages still merge with fixtures where IDs match |
| Platform     | Same                                          | Same                                                     | Live APIs; mock only where env forces internal honesty        | Terminal widgets — audit in child plan                                                                         |

## Gaps (tracked)

1. **Dedicated staging Firebase project** — **Repo-ready:**
   `unified-trading-system-ui/config/docker-build.env.staging.firebase.example`
   - `scripts/deploy-cloud-run.sh --build-env-file=…` + `docs/DEPLOYMENT.md` (cutover section). **Ops remaining:**
     create the non-prod Firebase project, add authorized domains, copy filled env to a **gitignored** file, deploy
     staging with that file. Default `docker-build.env.staging` intentionally stays **demo** until you cut over.
2. **Provisioning service** — **In-repo:** `deployment-api` provisioning guards + audit;
   `user-management-ui/server/index.js` mirrors org-owner / privileged app rules + `X-Acting-User-Email` validation.
   **Ops / other repos:** any separate host behind `NEXT_PUBLIC_AUTH_URL` (default rewrite target in `next.config.mjs`)
   must enforce the same policy class if it performs writes (see `unified-trading-system-ui/docs/SECURITY_AUTH.md`).
3. **Taxonomy parity** — IM grid mock categories (DEFI/CEFI/…) vs architecture-v2 families/archetypes: use API + PM
   codex as SSOT; UI filters to evolve in execution plan.
