---
doc_type: issue
title:
  unified-trading-system-ui local pw:L2 runs are unbounded-parallel — same false-failure class deployment-ui already
  fixed
summary: >-
  `unified-trading-system-ui/playwright.config.ts` only forces `workers: 1` under `CI`/`human` mode — a local agent `npx
  playwright test --project=chromium tests/smoke/` run (the canonical `pw:L2` evidence-gathering command every UI agent
  runs before shipping) defaults to unbounded parallelism on this shared multi-agent-slot host, reproducing the exact
  false-failure class `deployment-ui` already fixed 2026-07-31 (`issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md`)
  by pinning `workers: 1` unconditionally.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer]
tags: [ui, playwright, smoke, ci, host-contention, flake]
related:
  [
    /plans/active/issues/wizard_smoke_suite_pre_existing_failures_2026_07_28.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: 2026-08-01
parent_epic: agent_operating_framework_master
priority: P3
assigned_vm: planning
resolved_by:
locked_by:
source: [
    "wizard_smoke_suite_pre_existing_failures_2026_07_28.md todo 1 triage session, 2026-08-01: a --workers=1 full\
    tests/smoke/ run reproduced 4/108 failures vs the original 67/108 reported under default (unbounded-parallel)\
    settings on 2026-07-28 — same shared-host-contention pattern ui-testing-layers.md documents for deployment-ui",
  ]
execution_scope: orchestrator-agent
assigned_role: ui_developer
drift_direction: advance-code
depends_on: []
context_scope:
  [
    unified-trading-system-ui/playwright.config.ts,
    /codex/06-coding-standards/ui-testing-layers.md,
    /plans/active/issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md,
  ]
---

# unified-trading-system-ui local pw:L2 runs are unbounded-parallel

## What I found

While triaging `wizard_smoke_suite_pre_existing_failures_2026_07_28.md` todo 1, a clean `--workers=1` full
`tests/smoke/` run reproduced only 4/108 failures (all explained: 3 dev-server cold-start/crash flakes, 1 genuine bug
filed separately). The original 2026-07-28 audit that spawned that doc's ~65 untriaged failures ran under this repo's
DEFAULT settings — `playwright.config.ts`'s `workers: process.env.CI ? 1 : isHumanMode ? 1 : undefined` only forces
single-worker under CI or `--project=human`; a plain local `npx playwright test --project=chromium tests/smoke/` (the
exact canonical `pw:L2 ✓` command every UI agent runs before shipping, per `ui-testing-layers.md`) still defaults to
Playwright's unbounded local parallelism (~8 concurrent chromium instances) on this same shared multi-agent-slot host.

`ui-testing-layers.md` already documents this exact failure class for `deployment-ui` (fixed 2026-07-31,
`issues/deployment_ui_l2_smoke_gate_red_2026_07_17.md`): two back-to-back full-parallel runs on an identical pristine
tree produced 15 and 17 differently-composed "failures"; `--workers=1` reproduced exactly 0, consistently.
`unified-trading-system-ui` was never given the same fix.

## Why it matters

Every future agent that runs the canonical `pw:L2` gate command locally on this host risks the same large,
non-reproducible failure list this doc's parent spent a session (2026-08-01) triaging down to 4 real items — and risks
WRONGLY blocking a shippable change on a phantom regression, or (worse) an agent under time pressure treating a real
failure as "probably just contention" without verifying. Pinning `workers: 1` unconditionally (the same fix already
proven for `deployment-ui`) removes the ambiguity at the source instead of relying on every agent to independently
rediscover "suspect host contention, re-run with --workers=1."

## Recommended decision

- [ ] [UI] P3. Pin `workers: 1` unconditionally in `unified-trading-system-ui/playwright.config.ts` (mirroring
      `deployment-ui`'s 2026-07-31 fix), not only for `CI`/`isHumanMode`. Verify a full
      `npx playwright test --project=chromium tests/smoke/` run stays green (0 spurious failures) on a clean tree
      before/after the change to confirm the fix, then update `ui-testing-layers.md`'s "deployment-ui's `workers` is
      pinned to `1` unconditionally" note to also name `unified-trading-system-ui`. Repo: unified-trading-system-ui.

## Progress Log
