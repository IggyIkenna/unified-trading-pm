# Portal — local smoke checklist (public → platform)

Use this after IA / auth / marketing refactors. **Always start Next from `unified-trading-system-ui`**
(`cd … && pnpm dev`).

**Playwright / MCP (`user-playwright`):** The UI repo’s **`pnpm dev`** runs **`next dev --webpack`** so marketing
shadow + client boundaries hydrate reliably. Use **`pnpm dev:turbo`** if you explicitly want Turbopack. For CI-style
checks without dev, **`pnpm build` then `pnpm start -p <port>`** plus `MARKETING_TEST_URL` still works.

## Environment

| Step                            | Command / setting                                                                                                                                                                                                   | Done |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---- |
| API gateway (mock)              | `cd unified-trading-api && CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local DISABLE_AUTH=true .venv/bin/uvicorn unified_trading_api.main:create_app --factory --host 127.0.0.1 --port 8030`                                | ☐    |
| client-reporting-api (mock)     | `cd client-reporting-api && DISABLE_AUTH=true CLOUD_MOCK_MODE=true GCP_PROJECT_ID=test-project .venv/bin/uvicorn client_reporting_api.api.main:app --host 127.0.0.1 --port 8014`                                    | ☐    |
| Portal (rewrites)               | `cd unified-trading-system-ui && NEXT_PUBLIC_MOCK_API=false NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8030 NEXT_PUBLIC_REPORTING_API_URL=http://127.0.0.1:8014 NEXT_PUBLIC_AUTH_PROVIDER=demo pnpm dev --port 3000` | ☐    |
| Portal (mock-only, no backends) | `cd unified-trading-system-ui && NEXT_PUBLIC_MOCK_API=true pnpm dev --port 3000`                                                                                                                                    | ☐    |

## Public & lighter gate (unauthenticated)

| URL                      | Expect                                                | Done |
| ------------------------ | ----------------------------------------------------- | ---- |
| `/`                      | Marketing homepage (`marketing-inner` / shadow ready) | ☐    |
| `/investment-management` | Marketing shell                                       | ☐    |
| `/platform`              | Marketing shell                                       | ☐    |
| `/regulatory`            | Marketing shell                                       | ☐    |
| `/firm`                  | Marketing shell                                       | ☐    |
| `/contact`               | Contact page                                          | ☐    |
| `/docs`                  | Public docs                                           | ☐    |
| `/briefings`             | Hub + pillars                                         | ☐    |
| `/briefings/*`           | Article routes if configured                          | ☐    |

## Auth surfaces

| URL       | Expect                                                  | Done |
| --------- | ------------------------------------------------------- | ---- |
| `/login`  | Demo / Firebase per env                                 | ☐    |
| `/signup` | Signup flow or 404 if disabled — confirm product intent | ☐    |

## Signed-in (demo / Firebase)

| Area               | Path (examples)                         | Done |
| ------------------ | --------------------------------------- | ---- |
| Dashboard          | `/dashboard`                            | ☐    |
| Investor relations | `/investor-relations`, deck routes      | ☐    |
| Strategy catalogue | `/services/research/strategy/catalog`   | ☐    |
| Trading terminal   | `/services/trading/overview`, positions | ☐    |

## Automated

| Check                                                                                   | Command                                                                                                                                               | Done |
| --------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | ---- |
| Marketing static unit/integration                                                       | `cd unified-trading-system-ui && pnpm exec vitest run tests/integration/marketing-static-signin.test.ts`                                              | ☑   |
| Marketing Playwright (server running; use `next start` or webpack dev — see note above) | `MARKETING_TEST_URL=http://127.0.0.1:3014 pnpm exec playwright test tests/e2e/marketing-public-shell.spec.ts --config playwright.marketing.config.ts` | ☑   |
| IR archive API                                                                          | `cd client-reporting-api && .venv/bin/pytest tests/integration/test_api_workflow.py::TestInvestorRelationsArchiveMetadata -q`                         | ☑   |

## Docs SSOT

- `unified-trading-system-ui/docs/DEPLOYMENT.md` — deploy + staging Firebase cutover
- `unified-trading-system-ui/docs/FIREBASE_ENVIRONMENTS.md` — three Firebase projects (Auth web keys)
- `unified-trading-system-ui/docs/SECURITY_AUTH.md` — provisioning + acting user
