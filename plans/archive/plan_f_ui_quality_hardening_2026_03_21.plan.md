---
doc_type: plan
title: plan-f-ui-quality-hardening
summary: Harden unified-trading-system-ui to match deployment-ui integration quality. CI/CD pipeline, quality gates script,
  cloud integration, dev scripts, TypeScript strict mode, auth integration, OpenAPI type consumption, and 4-mode startup.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, unified-trading-system-ui]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-21'
type: code
epic: epic-code-completion
locked_by:
locked_since:
completion_gates: {code: C5, deployment: D3, business: none}
repo_gates:
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none}
depends_on: [plan-e-ui-backend-integration]
todos:
- {id: p0-gha-ci-workflow, content: '- [ ] [AGENT] P0. Create GitHub Actions CI workflow for unified-trading-system-ui matching other repos. Jobs: lint (eslint), typecheck (tsc --noEmit), unit tests (vitest), build (vite build), Playwright smoke tests. Trigger on push to staging/main and PR. Use pool: "forks" for vitest to prevent zombie node processes.

    ', status: todo}
- {id: p0-gha-semver-agent, content: '- [ ] [AGENT] P0. Add semver-agent workflow to unified-trading-system-ui. Use PM workflow template with __REPO_NAME__=unified-trading-system-ui, __SOURCE_DIR__=src. Follow `unified-trading-pm/scripts/propagation/rollout-semver-agent.sh` pattern.

    ', status: todo}
- {id: p0-gha-staging-lock, content: '- [ ] [AGENT] P1. Add staging-lock-check workflow from PM canonical template. Prevents direct pushes to staging while SIT is running.

    ', status: todo}
- {id: p1-quality-gates-script, content: '- [ ] [AGENT] P0. Create scripts/quality-gates.sh for unified-trading-system-ui. Steps: lint (eslint --max-warnings=0), typecheck (tsc --noEmit), unit tests (CI=true npx vitest run), build (VITE_MOCK_API=true npx vite build), Playwright smoke tests (npx playwright test). Exit non-zero on any failure. Follow deployment-ui''s quality-gates.sh as reference.

    ', status: todo, blocked_by: p0-gha-ci-workflow}
- {id: p1-qg-gate, content: '- [ ] [SCRIPT] P0. QG gate: run `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — must pass.

    ', status: todo, blocked_by: p1-quality-gates-script}
- {id: p2-remove-ignore-build-errors, content: '- [ ] [AGENT] P0. Remove ignoreBuildErrors: true from next.config.js (or equivalent). Fix all TypeScript errors that surface. No @ts-ignore or @ts-expect-error without a tracking issue reference.

    ', status: todo, blocked_by: p1-qg-gate}
- {id: p2-strict-tsconfig, content: '- [ ] [AGENT] P0. Enable strict mode in tsconfig.json: strict: true, noUncheckedIndexedAccess: true, noImplicitReturns: true. Fix all resulting type errors. This must match the strictness level of deployment-ui.

    ', status: todo, blocked_by: p2-remove-ignore-build-errors}
- {id: p2-qg-gate, content: '- [ ] [SCRIPT] P0. QG gate: run `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — must pass with strict tsconfig.

    ', status: todo, blocked_by: p2-strict-tsconfig}
- {id: p3-env-var-matrix, content: '- [ ] [AGENT] P0. Implement 5-axis mode switching in unified-trading-system-ui. Env vars: VITE_MOCK_API (UI data), VITE_SKIP_AUTH (UI auth), CLOUD_MOCK_MODE (API data via BFF), DISABLE_AUTH (API auth via BFF), MOCK_STATE_MODE (mock state). Document in .env.example with all 4 preset combinations (ci, mock, api-real, real).

    ', status: todo, blocked_by: p2-qg-gate}
- {id: p3-dev-start-integration, content: '- [ ] [AGENT] P0. Integrate unified-trading-system-ui into dev-start.sh / dev-stop.sh / dev-status.sh scripts in unified-trading-pm/scripts/dev/. Add UI to ui-api-mapping.json with correct port. Support: `dev-start.sh --ui trading-system` to start just this UI.

    ', status: todo, blocked_by: p2-qg-gate}
- {id: p3-startup-modes, content: '- [ ] [AGENT] P0. Verify unified-trading-system-ui starts correctly in all 4 modes: ci (deterministic, no cache), mock (interactive, cache persists), api-real (real APIs, mock UI auth), real (full credentials + OAuth). Each mode must render the dashboard page without errors.

    ', status: todo, blocked_by: p3-env-var-matrix}
- {id: p4-auth-hooks, content: '- [ ] [AGENT] P0. Replace client-side persona/mock auth with real OAuth hooks. Use NextAuth.js or equivalent. Support: Google OAuth (production), VITE_SKIP_AUTH=true (local dev/CI). Session token must be forwarded by BFF to backend APIs. Follow deployment-ui auth pattern.

    ', status: todo, blocked_by: p3-startup-modes}
- {id: p4-auth-guard, content: '- [ ] [AGENT] P1. Add route guards — protected pages redirect to login when VITE_SKIP_AUTH is not set and session is missing. Public pages: /login, /health. All other routes require valid session.

    ', status: todo, blocked_by: p4-auth-hooks}
- {id: p4-qg-gate, content: '- [ ] [SCRIPT] P0. QG gate: run `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — auth integration passes in mock mode (VITE_SKIP_AUTH=true).

    ', status: todo, blocked_by: p4-auth-guard}
- {id: p5-import-generated-types, content: '- [ ] [AGENT] P0. Audit all TypeScript files for hand-written API response types. Replace with imports from src/generated/api-types.ts (generated by openapi-typescript in Plan A). No hand-written duplicates of types that exist in the generated file.

    ', status: todo, blocked_by: p4-qg-gate}
- {id: p5-type-safety-hooks, content: '- [ ] [AGENT] P1. Add type parameters to all React Query hooks — useQuery<GeneratedResponseType> and useMutation<GeneratedRequestType, GeneratedResponseType>. Hooks must use generated types, not any or unknown.

    ', status: todo, blocked_by: p5-import-generated-types}
- {id: p5-qg-gate, content: '- [ ] [SCRIPT] P0. QG gate: run `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — zero hand-written API types, all hooks typed.

    ', status: todo, blocked_by: p5-type-safety-hooks}
- {id: p6-playwright-smoke, content: '- [ ] [AGENT] P0. Add Playwright smoke tests for critical pages: dashboard, trading, positions, risk, alerts, config editor, admin/scenario panel. Each test: navigate to page, verify key elements render, verify no console errors. Run in mock mode (VITE_MOCK_API=true, VITE_SKIP_AUTH=true).

    ', status: todo, blocked_by: p5-qg-gate}
- {id: p6-qg-final, content: '- [ ] [SCRIPT] P0. Final QG gate: run `cd unified-trading-system-ui && bash scripts/quality-gates.sh` — full suite green. Verify: zero ignoreBuildErrors, strict tsconfig, all 4 modes start cleanly, auth works in mock mode, Playwright smoke tests pass, all generated types used.

    ', status: todo, blocked_by: p6-playwright-smoke}
- {id: p7-aws-ui-deploy, content: '- [ ] [AGENT] P2. Deploy UI to AWS (S3 + CloudFront). Create deployment script matching the existing Firebase deploy pattern. Ensure NEXT_PUBLIC_API_BASE_URL points to the correct cloud API.

    ', status: todo, blocked_by: p6-qg-final}
- {id: p7-verify-cloud-api, content: '- [ ] [AGENT] P2. Verify UI works against cloud-deployed unified-trading-api (both GCP and AWS).

    ', status: todo, blocked_by: p7-aws-ui-deploy}
isProject: false
---

# Plan F: UI Quality Gate Hardening

## Context

unified-trading-system-ui currently lacks the quality infrastructure that deployment-ui has. This plan brings it up to
parity:

| Capability               | deployment-ui | trading-system-ui (current) | trading-system-ui (target)  |
| ------------------------ | ------------- | --------------------------- | --------------------------- |
| quality-gates.sh         | Yes           | No                          | Yes                         |
| GHA CI workflow          | Yes           | No                          | Yes                         |
| semver-agent             | Yes           | No                          | Yes                         |
| TypeScript strict mode   | Yes           | No (ignoreBuildErrors)      | Yes                         |
| 4-mode startup           | Yes           | Partial (mock only)         | Yes (ci/mock/api-real/real) |
| OAuth integration        | Yes           | No (client-side persona)    | Yes (NextAuth.js)           |
| OpenAPI type consumption | Yes           | No (hand-written types)     | Yes (generated types)       |
| Playwright tests         | Yes           | No                          | Yes                         |
| dev-start.sh support     | Yes           | No                          | Yes                         |

## Execution DAG

```
Phase 0 (CI/CD pipeline — GHA workflows)
    |
    v
Phase 1 (quality-gates.sh script)
    |
    v  [QG gate]
Phase 2 (TypeScript strict mode)
    |
    v  [QG gate]
Phase 3 (PARALLEL — cloud integration + dev scripts)
    |
    v
Phase 4 (auth integration)
    |
    v  [QG gate]
Phase 5 (OpenAPI type consumption)
    |
    v  [QG gate]
Phase 6 (Playwright smoke tests + final validation)
    |
    v  [QG gate]
  DONE
```

## Success Criteria

| Phase | Gate | Criteria                                                                  |
| ----- | ---- | ------------------------------------------------------------------------- |
| 0     | C2   | GHA CI workflow triggers on push, semver-agent installed                  |
| 1     | C4   | quality-gates.sh runs lint+typecheck+test+build+playwright                |
| 2     | C4   | strict tsconfig, zero ignoreBuildErrors, zero ts-ignore without tracking  |
| 3     | C4   | 4-mode startup works, dev-start.sh integration, env var matrix documented |
| 4     | C4   | OAuth hooks replace persona, route guards work, mock mode auth passes     |
| 5     | C4   | All hooks use generated types, zero hand-written API response types       |
| 6     | C5   | Playwright smoke tests green, full quality-gates.sh passes                |

## Reference: deployment-ui Quality Gates

deployment-ui's quality-gates.sh (reference implementation for this plan):

1. `eslint --max-warnings=0 src/`
2. `tsc --noEmit`
3. `CI=true npx vitest run`
4. `VITE_MOCK_API=true npx vite build`
5. `npx playwright test`

unified-trading-system-ui should match this exact sequence.
