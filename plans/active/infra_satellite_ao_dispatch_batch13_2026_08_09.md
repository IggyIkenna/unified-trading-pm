---
doc_type: plan
title: Infra satellite AO batch 13 — diagnose + fix the unified-trading-system-ui mock dev-server crash under sustained Playwright load
summary: >-
  Thirteenth AO-dispatch batch for the `infra` topic tranche, produced during a round-9 combined
  RECLASSIFY+satellite-extraction sweep (2026-08-09). Single source:
  `issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` todo 2 — a bounded,
  worker-determinable investigation+fix task (capture the `pnpm dev:mock` Next dev server's own stdout/stderr across a
  full sustained Playwright run, find why it dies with `ERR_CONNECTION_REFUSED` partway through, fix the cause). The
  source doc's other 2 items (deciding a Firebase Admin credential/emulator approach for CI, and a downstream re-run
  gated on both) are genuine operator/judgment or dependency-gated calls and are NOT extracted here — only this one
  self-contained diagnostic+fix item clears the bounded-outcome bar.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [infra, ao-dispatch, satellite-docs, batch-13, ui, e2e, playwright, dev-server]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch13_finalize_2026_08_09.md,
    /plans/active/issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md,
    /plans/active/issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md,
    unified-trading-system-ui/playwright.config.ts,
    unified-trading-system-ui/lib/api/mock-handler.ts,
    unified-trading-system-ui/tests/e2e/user-management.spec.ts,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` todo 2, filed
  2026-08-09 (slot-28) while repairing the E2E login-helper contract. Found during the round-9 infra-tranche
  RECLASSIFY+satellite-extraction sweep (candidate list generated from docs edited since their last verdict).
---

# Infra satellite docs — AO dispatch batch 13

## Why this plan exists

`issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` (filed today, slot-28)
found two SEPARATE, orthogonal gaps blocking `tests/e2e/user-management.spec.ts` from exiting 0: (1) `/api/v1/*` admin
routes need real Firebase Admin credentials — an operator/infra decision on approach (real creds vs. emulator, who
provisions the CI secret) and NOT extracted here; (2) the mock Next dev server (`pnpm dev:mock`) becomes unstable and
dies (`ERR_CONNECTION_REFUSED`) partway through a ~20-test sequential Playwright run, reproduced both self-started and
under Playwright's own `webServer` management — a self-contained diagnose-and-fix task with no operator judgment call
embedded in it (capture server logs, find the crash cause, fix it). Only item (2) is extracted here.

## Conflict check (before drafting)

- Grepped `plans/active/*.md` + `plans/active/issues/*.md` for `dev:mock`, `ERR_CONNECTION_REFUSED`, and
  `webServer.*crash`: the only hits besides the source doc itself are an unrelated DONE item in
  `citadel_paper_batch_live_reconciliation_2026_06_19.md` (playwright SMOKE gate self-starting `pnpm dev:mock`, a
  different feature, already shipped) and `issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md` (the source
  doc's own parent — its 1 remaining open item is unrelated, a documentation/primary-record follow-up, not the
  dev-server-stability question). No other active plan claims this delta.
- Grepped every `infra_*batch*`/`*finalize*` doc (active + archived) for `unified-trading-system-ui` + `dev-server`/
  `dev:mock` — no hits.

## Todos

- [ ] [INFRA] P2. **Diagnose + fix why the `pnpm dev:mock` Next dev server dies (`ERR_CONNECTION_REFUSED`) partway
      through a sustained ~20-test sequential Playwright run.** Reproduced both self-started (`next dev --webpack -p
      <port>`) and Playwright-`webServer`-managed (which detects the server is down and respawns it, but subsequent
      tests still fail near-instantly, suggesting the respawn itself doesn't recover cleanly). Capture the dev server's
      OWN stdout/stderr across a full `tests/e2e/user-management.spec.ts` run (redirect `next dev`'s output directly,
      not just Playwright's summary) to find the crash cause (candidates not yet ruled in/out: memory growth under
      `next.config.mjs`'s webpack dev config, an unhandled rejection in `lib/api/mock-handler.ts`'s request
      interception under load, a file-watcher/HMR leak) — then fix it. Done when: `npx playwright test
      --project=chromium tests/e2e/user-management.spec.ts` (or the subset of it that does not depend on Firebase Admin
      credentials — see the source doc's separate, non-extracted item 1) runs the full sequential suite without a
      dev-server connection failure, with the root cause documented. Source:
      `issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` todo 2. Repo:
      unified-trading-system-ui.

## Operator approval gate

**This plan is `status: draft` — awaiting operator review.** Flip to `status: active` only after explicit approval (its
finalize twin is drafted alongside it, gated on this plan per the finalize-plan-coverage rule).

## Codex SSOTs (read before touching a todo)

- `/codex/06-coding-standards/ui-testing-layers.md` — Playwright/E2E gate conventions
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — archival ritual the finalize plan runs
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule

## Progress Log

- **2026-08-09** — Drafted during the round-9 infra-tranche combined RECLASSIFY+satellite-extraction sweep. Paired with
  `infra_satellite_ao_dispatch_batch13_finalize_2026_08_09.md` per the finalize-plan-coverage rule.
