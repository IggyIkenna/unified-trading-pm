---
doc_type: issue
title: >-
  Running agent-orchestrator's mock backend locally destructively truncates .github/workflows/*.yml across ~22 repos +
  dashboard e2e ports collide across slots
summary: >-
  Discovered live 2026-08-07 while building/testing the AO dashboard critical-health-visibility feature
  (`ao_dashboard_critical_health_visibility_2026_08_07`, shipped `agent-orchestrator@7daa63e8d`). Two distinct findings,
  both real, both reverted before shipping (no damage landed), neither root-caused yet: (1) running
  `ORCHESTRATOR_MODE=mock` uvicorn locally for Playwright e2e testing triggers some background job (log evidence points
  at "CIReconcile", which scanned "26 repos") that TRUNCATED 5 GitHub Actions workflow files
  (`main-backmerge-to-ldr.yml`, `major-bump-issue-handler.yml`, `request-major-bump.yml`,
  `staging-backmerge-to-ldr.yml`, `update-dependency-version.yml`) by ~85-90% (removed 1400+ lines each) across
  agent-orchestrator itself PLUS 21 sibling repos in the shared workspace (unified-trading-library,
  unified-api-contracts, alerting-service, batch-live-reconciliation-service, client-reporting-api, deployment-api,
  deployment-service, deployment-ui, e2e-testing, execution-service, features-service, fund-administration-service,
  greeks-service, ibkr-gateway-infra, instruments-service, market-data-processing-service, market-tick-data-service,
  ml-service, strategy-service, system-integration-tests, trading-agent-service, unified-trading-api,
  unified-trading-system-ui) — every repo checked except unified-trading-pm. (2) The dashboard's Playwright `webServer`
  port scheme (8790-8794/5198-5202, `dashboard/playwright.config.ts`) is NOT slot-namespaced — running the e2e suite
  from two different `.tabs/N` slots concurrently collides on the SAME ports, and `reuseExistingServer: false` means the
  second invocation's port-clear attempt can kill the FIRST slot's legitimate, in-progress run (confirmed: killed
  `.tabs/3`'s `playwright test tests/e2e/switch-model.spec.ts tests/e2e/edit-agent-modal.spec.ts` run this way).
status: open
nature: issue
asset_group: [ao, cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, ci-cd, workflows, data-loss-near-miss, e2e, playwright, multi-slot, dashboard]
related:
  [/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md, /codex/05-infrastructure/per-tab-worktrees.md]
created: "2026-08-07"
author: ikennaigboaka [interactive session]
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
estimate_class: infra
depends_on: []
parent_epic: infrastructure_master
resolved_by:
source:
  [
    "interactive session 2026-08-07 — building the AO dashboard critical-health-visibility feature, discovered as a side
    effect of running quality-gates.sh + Playwright e2e tests against a local ORCHESTRATOR_MODE=mock instance",
  ]
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/dashboard/playwright.config.ts,
    agent-orchestrator/dashboard/tests/e2e/,
    agent-orchestrator/server/,
  ]
---

# AO local mock-server workflow truncation + dashboard e2e port collision across slots

## Finding 1 (P1 — the bigger one): local mock backend truncates `.github/workflows/*.yml` workspace-wide

**Not root-caused. Reverted, not fixed.** While running `agent-orchestrator`'s dashboard Playwright e2e suite locally
(`ORCHESTRATOR_MODE=mock` uvicorn instances on ports 8790-8794, started repeatedly over ~15 minutes while iterating on a
new e2e spec), `git status` across the workspace afterward showed **5 specific workflow files modified in 22 of 23
checked repos** (every repo under `.tabs/1/` except `unified-trading-pm` itself):

- `main-backmerge-to-ldr.yml`, `major-bump-issue-handler.yml`, `request-major-bump.yml`, `staging-backmerge-to-ldr.yml`,
  `update-dependency-version.yml`

Every one of the 22 shrank by roughly the same amount — agent-orchestrator's own copies went from their real content
down to ~13-15% of their original line count (e.g. `main-backmerge-to-ldr.yml` −450 lines,
`major-bump-issue-handler.yml` −316, `request-major-bump.yml` −203, `staging-backmerge-to-ldr.yml` −207,
`update-dependency-version.yml` −341; `unified-trading-library` and `unified-api-contracts` showed the same pattern
almost line-for-line). This is DESTRUCTIVE — if it had been committed and pushed, it would have broken CI (backmerge,
semver bump, dependency-update automation) on ~22 repos simultaneously.

**Evidence trail (not a full root-cause, just what's known):**

- Server log lines seen during the affected window: `CIReconcile: gh non-200 for unified-trading-ci (status=404)` and
  `CIReconcile: no failing repos on live-defi-rollout or main (26 scanned)` — strongly suggests a background
  "CIReconcile" component IS the actor (26 ≈ the repo count in this workspace), even in `ORCHESTRATOR_MODE=mock` against
  an isolated/empty e2e DB with zero real backlog state.
  - Grep candidates for the next session to start from: `rg -n "CIReconcile" agent-orchestrator/server/`.
- Timing: file mtimes for the truncated copies clustered within the same ~15-minute window as repeated
  `bash tests/e2e/run-e2e-backend-critical-health.sh` + `npx playwright test` invocations (each of which boots a fresh
  `ORCHESTRATOR_MODE=mock` uvicorn instance per `dashboard/playwright.config.ts`'s `webServer` array — up to 5 backend
  instances get started per `npx playwright test` run since the config always starts ALL `webServer` entries regardless
  of `--project` filter).
- All 22 repos' 5 files reverted via `git checkout --` before shipping (`git status --short -- .github/workflows/` clean
  across all of them, re-verified) — **no truncated content was ever committed or pushed.**
- **Not investigated**: what specifically triggers it (every mock boot? only after N boots? only under
  `ADMIN_ENABLED`/mock-mode's "Populate demo" UI being present? something about running FIVE mock backends
  simultaneously — the parked/collision/chat/critical-health projects — vs just one?), what "template" it's syncing FROM
  (if it's a template-sync bug, the SOURCE template file may itself be the actually-truncated one, and this job is
  faithfully propagating that corruption outward — check whatever file/location `CIReconcile` treats as canonical
  first), and whether this can happen in a REAL (non-mock) orchestrator boot too (if `CIReconcile` isn't
  mock-mode-gated, this could be live-orchestrator-reachable, which would be P0 not P1).

### Todos

- [ ] [INFRA] P1. **Find and read `CIReconcile`'s source** (`agent-orchestrator/server/` — grep for the class/function
      and whatever calls it on startup/interval) — confirm it's the actual actor, understand its trigger condition
      (every boot? gated by something?), and whether it's reachable outside `ORCHESTRATOR_MODE=mock`.
- [ ] [INFRA] P1. **Reproduce deliberately** in a disposable/throwaway git worktree (never the operator's real checkout)
      — boot `ORCHESTRATOR_MODE=mock` once, check `.github/workflows/*.yml` diffs immediately after; if clean, boot a
      second/third/fourth/fifth instance (matching the 5-webServer-pair pattern) and re-check after each, to isolate
      whether it's a single-boot bug or a multi-instance race.
- [ ] [INFRA] P1. **If confirmed live-reachable (not mock-gated), treat as P0** — file a follow-up issue doc and notify
      the operator directly; a background job that can silently truncate CI workflows across the whole workspace from
      the LIVE orchestrator is a standing risk to every repo's CI, not just a local-dev annoyance.
- [ ] [INFRA] P2. **Once root-caused, fix at the source** (whatever `CIReconcile` reads as its "canonical" workflow
      content) and add a regression test / guard rail (e.g. a size-sanity check before any workflow-file write — refuse
      to write a workflow file that's <50% the size of what's already there, or require a human-reviewed diff for any
      write to `.github/workflows/` from this component at all).

## Finding 2 (P2 — smaller, but real and reproducible): dashboard e2e ports aren't slot-namespaced

`dashboard/playwright.config.ts` hardcodes 5 backend/dashboard port pairs (8790-8794 backend, 5198-5202 dashboard),
shared across every `.tabs/N` slot's git worktree (each slot has its own clone, but the SAME port numbers). With
`reuseExistingServer: false` on every `webServer` entry, running `npx playwright test` from one slot while ANOTHER
slot's e2e suite is already using those ports doesn't just fail cleanly — clearing the "already used" port (e.g. via
`lsof -ti tcp:$PORT | xargs kill`) kills whichever process is ACTUALLY listening, with no ownership check, which can be
a different slot's legitimate, in-progress test run. Confirmed live 2026-08-07: killed `.tabs/3`'s
`playwright test tests/e2e/switch-model.spec.ts tests/e2e/edit-agent-modal.spec.ts` run this way while debugging a port
conflict for a NEW e2e project (`critical-health`) added to the same config.

### Todos

- [ ] [INFRA] P2. **Slot-namespace the e2e ports** — derive each port from the slot number (e.g. `8790 + slot_number*10`
      or similar) via `scripts/hooks/slot-identity-lib.sh`'s existing slot-N-from-PATH derivation, so two slots running
      the dashboard e2e suite concurrently never collide. Alternatively/additionally, default
      `reuseExistingServer: true` locally (`!process.env.CI`, the standard Playwright convention) so a free/healthy port
      is reused instead of fought over — this alone would have prevented the kill (a healthy existing server would just
      get reused, not need "clearing").
- [ ] [DOC] P3. **Add a CLAUDE.md/codex one-liner** (once fixed) under the per-tab-worktrees SSOT
      (`/codex/05-infrastructure/per-tab-worktrees.md`) noting the dashboard e2e port scheme is slot-safe, so this isn't
      silently re-discovered by the next person who runs two slots' e2e suites at once.

## Why this wasn't chased further this session

Both findings surfaced as a side effect of shipping an unrelated dashboard feature
(`ao_dashboard_critical_health_visibility_2026_08_07`); root-causing `CIReconcile` properly needs isolated reproduction
in a disposable worktree, which is out of scope for that session's actual task. Reverted all live damage before shipping
(verified clean via `git status --short -- .github/workflows/` on all 22 affected repos); no truncated content was ever
committed.
