---
doc_type: issue
title:
  "unified-trading-system-ui: ~40 tests/e2e/**/*.spec.ts files hardcode :3100/:8030 directly, bypassing the new per-slot
  Playwright port derivation"
summary: >-
  While implementing ao_satellite_ao_dispatch_batch1-005 (derive the Playwright dev-server port per slot instead of a
  shared constant), fixed unified-trading-system-ui's playwright.config.ts + tests/e2e/_shared/config.ts (E2E_CONFIG) to
  slot-derive the Next dev-server port (3100+SLOT) and the mock-API uvicorn port (8030+SLOT), matching the pattern
  already shipped in deployment-ui/playwright.config.ts. That fix is complete and verified for the L2 smoke gate
  (tests/smoke/**, which navigate relatively off Playwright's `baseURL` and are therefore slot-safe). However, ~40 files
  under tests/e2e/**/*.spec.ts (the L3a/L3b layer, NOT part of the pw:L2 gate) hardcode `http://localhost:3100` or
  `http://localhost:8030` as bare string literals — some read `process.env.PLAYWRIGHT_BASE_URL` first with a hardcoded
  fallback, most have no env-var path at all. None of them import `E2E_CONFIG`. So for any slot N != 0, these ~40 specs
  will still attempt to reach the OLD fixed ports (3100/8030) instead of this slot's real dev server (3100+N/8030+N) —
  either connecting to nothing (ERR_CONNECTION_REFUSED) or, worse, silently reusing whichever OTHER slot's server
  happens to be running on the fixed port, which is exactly the false-result hazard the parent fix exists to close.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [playwright, multi-agent, per-slot-worktrees, false-negative, test-isolation, ui-testing-layers]
related:
  [
    plans/archive/issues/playwright_reuse_existing_server_cross_slot_false_results_2026_07_20.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-07-28"
priority: P2
parent_epic: agent_operating_framework_master
source: ao_satellite_ao_dispatch_batch1-005
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
assigned_vm: planning
resolved_by:
---

# unified-trading-system-ui e2e specs hardcode ports, bypassing per-slot derivation

## What I found

`ao_satellite_ao_dispatch_batch1-005`'s scope was exactly `deployment-ui/playwright.config.ts` + "all three `webServer`
blocks of `unified-trading-system-ui/playwright.config.ts`" — both now fixed and shipped. Implementing the
unified-trading-system-ui half required deriving `NEXT_PORT = 3100 + SLOT` and `API_PORT = 8030 + SLOT` in
`tests/e2e/_shared/config.ts` (the repo's own documented "single source of truth for e2e test-run tunables") and wiring
`playwright.config.ts`'s `use.baseURL` + all 3 `webServer` blocks off that.

Auditing for hardcoded ports before shipping (`rg -n "3100|8030" tests/ playwright.config.ts`) surfaced ~40 hits under
`tests/e2e/**/*.spec.ts` of two shapes:

1. **No env-var path at all** (majority): `const API = "http://localhost:8030";` /
   `const BASE_URL = "http://localhost:3100";` — e.g. `tests/e2e/indicators.spec.ts`, `data-freshness.spec.ts`,
   `flows.spec.ts`, `lifecycle.spec.ts`, `responsive.spec.ts`, `instruments.spec.ts`, `reset-demo.spec.ts`,
   `admin-flow.spec.ts`, `org-isolation.spec.ts`, `observe-flow.spec.ts`, `strategy-scale.spec.ts`,
   `reports-flow.spec.ts`, `export-tests.spec.ts`, `research-flow.spec.ts`, `guided-tour.spec.ts`,
   `latency-simulation.spec.ts`, `auth-flow.spec.ts`, `tier-readiness.spec.ts`, `trading-flow.spec.ts`,
   `no-client-mock-data.spec.ts`, `data-flow.spec.ts`, all `tests/e2e/widgets/defi/*.spec.ts`, and all
   `tests/e2e/strategies/**/*.spec.ts`.
2. **Env-var with a hardcoded fallback** (minority, still slot-unsafe when unset):
   `process.env.PLAYWRIGHT_BASE_URL || "http://localhost:3100"` in `permission-catalogue.spec.ts`,
   `user-management.spec.ts`, `admin-strategy-assignments.spec.ts`, `warmup.setup.ts`, `full-site-link-crawler.spec.ts`;
   `process.env.BASE_URL || "http://localhost:3100"` in `regulatory-onboarding.spec.ts`. Setting `E2E_CONFIG.baseURL` in
   code does NOT export `process.env.PLAYWRIGHT_BASE_URL` — Playwright never wires a config's computed `use.baseURL`
   back into the process environment — so these still fall back to the fixed :3100 unless an operator manually exports
   the env var (the "Interim guidance for agents" workaround already documented in the parent issue doc).

None of these files `import { E2E_CONFIG }`.

**Why the L2 gate itself is unaffected**: verified `tests/smoke/**` (the `pw:L2 ✓` gate population) contains zero
hardcoded-port hits — every smoke spec navigates via relative `page.goto("/...")`, which resolves off Playwright's
config-level `use.baseURL` (now correctly slot-derived). Confirmed by running
`npx playwright test --project=chromium tests/smoke/` after the fix: the dev server bound to this slot's derived port
(3115 for slot 15, confirmed via `E2E_CONFIG` dump) and pages rendered; the run's 65 failures were all
`Test timeout of 30000ms exceeded` under measured host load 24-29 on 16 cores (an unrelated, already-documented
environment-blocker class — see `ui_hardcoded_colour_and_localhost_debt_2026_07_21.md` Batches 1/4 for the same
signature), not connection/port errors.

## Why it matters

The parent fix's whole point is that a Playwright run in slot N must never silently attach to a DIFFERENT slot's dev
server (measured 2026-07-20: a false failure from exactly this). The config-level fix closes that hole for the L2 gate
population. But these ~40 L3a/L3b specs are NOT part of the L2 gate and are exactly as exposed to the original bug today
as they were before this fix — worse, in a sense, because an agent citing `E2E_CONFIG`/the new slot-derived defaults in
their reasoning could wrongly assume the whole `tests/e2e/` tree is now slot-safe when only the smoke subtree is.

## Recommended decision

Migrate these ~40 files to import `BASE_URL`/`API` from `E2E_CONFIG` (`tests/e2e/_shared/config.ts`, already exports
`baseURL`/`apiPort`/`nextPort`/`slot`) instead of a literal string, in per-directory batches with a running dev server

- spot-check before/after (same discipline as `ui_hardcoded_colour_and_localhost_debt_2026_07_21.md`'s batching, since a
  blind find-replace risks missing a file that legitimately needs a different port, e.g. a cross-service test). Out of
  scope for `ao_satellite_ao_dispatch_batch1-005` itself — that todo's stated scope was the 2 config files, and 30-40
  file edits is far beyond a same-commit "adjacent" fix.

## Todos

- [x] ✅ [UI] P2. Batch 1 — migrate the "no env-var path" API-only specs (21 files: `indicators.spec.ts`,
      `data-freshness.spec.ts`, `flows.spec.ts`, `lifecycle.spec.ts`, `responsive.spec.ts`, `instruments.spec.ts`,
      `reset-demo.spec.ts`, `admin-flow.spec.ts`, `org-isolation.spec.ts`, `observe-flow.spec.ts`,
      `strategy-scale.spec.ts`, `reports-flow.spec.ts`, `export-tests.spec.ts`, `research-flow.spec.ts`,
      `guided-tour.spec.ts`, `latency-simulation.spec.ts`, `auth-flow.spec.ts`, `tier-readiness.spec.ts`,
      `trading-flow.spec.ts`, `no-client-mock-data.spec.ts`, `data-flow.spec.ts`) to
      `const API = E2E_CONFIG.apiUrl ?? \`http://localhost:${E2E_CONFIG.apiPort}\`;` (add an `apiUrl` convenience field
      to `E2E_CONFIG` alongside `apiPort` if it doesn't already read cleanly). Done-when:
      `rg -n     '"http://localhost:8030"' tests/e2e/*.spec.ts` returns 0 hits for these 21 files; `pw:L2 ✓` unaffected
      (these aren't in the gate population, so cite a manual run of a sample of these specs against this slot's derived
      port instead). — unified-trading-system-ui@db918e1c. Added `E2E_CONFIG.apiUrl` (slot-derived
      `http://localhost:${apiPort}`) in `tests/e2e/_shared/config.ts`; all 21 files now
      `import { E2E_CONFIG } from     "./_shared/config"` and use `const API = E2E_CONFIG.apiUrl;`.
      `rg -n '"http://localhost:8030"'` over the 21 files returns 0 hits. Manual run
      (`npx playwright test --project=chromium tests/e2e/indicators.spec.ts     tests/e2e/reset-demo.spec.ts`) on slot 7
      confirmed the API constant resolves to this slot's derived port (`http://localhost:8037` = 8030+7, per the
      `apiRequestContext.post` connect log) instead of the old fixed `:8030` — the ECONNREFUSED seen is the expected "no
      live uvicorn API for this slot" case (would need `E2E_USE_REAL_API=1`, out of scope for this UI-only todo per the
      ui_developer craft boundary), not a wrong-port or cross-slot-reuse hit. tsc/ESLint/full quality-gates.sh all green
      (sentinel `db918e1c`); quickmerge shipped to `live-defi-rollout`.
- [ ] [UI] P2. Batch 2 — migrate the "no env-var path" BASE_URL-only widget/strategy specs (~19 files under
      `tests/e2e/widgets/defi/*.spec.ts` and `tests/e2e/strategies/**/*.spec.ts`) to import `E2E_CONFIG.baseURL` instead
      of the literal `"http://localhost:3100"`. Same done-when pattern as Batch 1. (repo: unified-trading-system-ui)
- [ ] [UI] P3. Batch 3 — migrate the 6 "env-var with hardcoded fallback" specs (`permission-catalogue.spec.ts`,
      `user-management.spec.ts`, `admin-strategy-assignments.spec.ts`, `warmup.setup.ts`,
      `full-site-link-crawler.spec.ts`, `regulatory-onboarding.spec.ts`) so their fallback reads `E2E_CONFIG.baseURL`
      instead of the literal `"http://localhost:3100"` — keep the `process.env.PLAYWRIGHT_BASE_URL`/`BASE_URL` override
      path (a real operator override should still win), just fix what happens when neither is set. (repo:
      unified-trading-system-ui)

## Codex SSOTs

`/codex/06-coding-standards/ui-testing-layers.md`.
