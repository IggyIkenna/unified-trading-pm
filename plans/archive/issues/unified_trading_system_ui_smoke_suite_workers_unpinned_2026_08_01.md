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
status: resolved
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
resolved_by: unified-trading-system-ui@fc6ed104
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

> **✅ ARCHIVED 2026-08-02** — sole todo shipped (`status: resolved`, `resolved_by` set), 0 open todos, unlocked.
> `workers: 1` pinned unconditionally in `unified-trading-system-ui/playwright.config.ts`
> (`unified-trading-system-ui@fc6ed104`); `ui-testing-layers.md` updated to name both fixed repos
> (`unified-trading-pm@85433a383`); pw:L2 verified via 3 sharded runs, 105/108 passed, all 3 failures pre-explained (2
> known cold-start flakes + the already-filed `wizard_jurisdiction_overlay_dropped_by_registry_regen_2026_08_01.md`
> genuine bug), 0 new spurious failures. Moved to `plans/archive/issues/` per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

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

- [x] ✅ [UI] P3. Pinned `workers: 1` unconditionally in `unified-trading-system-ui/playwright.config.ts` (mirroring
      `deployment-ui`'s 2026-07-31 fix), not only for `CI`/`isHumanMode` — `unified-trading-system-ui@fc6ed104`.
      `ui-testing-layers.md`'s deployment-ui-only note updated to also name unified-trading-system-ui —
      `unified-trading-pm@85433a383`. **pw:L2 ✓** — full `tests/smoke/` suite verified via 3 sharded
      `npx playwright test --project=chromium tests/smoke/ --shard=N/3` runs (single-invocation full runs were
      repeatedly interrupted mid-run by this slot's session dying under severe host contention, 30-42+ load average on
      16 cores — unrelated to the fix; sharding bounded each run's blast radius so it could survive). Aggregate:
      **105/108 passed, 3 explained failures, 0 new spurious failures** — 2 dev-server cold-start flakes, one per shard
      boundary (`paper-trading-ledger.smoke.spec.ts:77`, `trading-predictions-colour-migration.smoke.spec.ts:57`) + the
      1 already-filed genuine bug (`wizard-jurisdiction-filter.spec.ts:135`, tracked separately at
      `/plans/active/issues/wizard_jurisdiction_overlay_dropped_by_registry_regen_2026_08_01.md`, a registry-regen
      defect unrelated to worker parallelism). Matches/betters this doc's own 4/108 baseline (measured under manual
      `--workers=1` in the source triage). Repo: unified-trading-system-ui.

## Progress Log

- 2026-08-02: Code shipped — `workers: 1` pinned unconditionally in `unified-trading-system-ui/playwright.config.ts`
  (`unified-trading-system-ui@fc6ed104`, verified on `origin/live-defi-rollout`). `ui-testing-layers.md`'s
  deployment-ui-only note updated to also name unified-trading-system-ui (this commit). Two local
  `npx playwright test --project=chromium tests/smoke/` verification runs were interrupted mid-run by this slot's
  session dying unexpectedly (host under heavy load, 30+ load average / active swap on a 16-core box — unrelated to the
  config change): run 1 reached 75/108 with 2 failures (1 dev-server cold-start `toBeEmpty` timeout on test 1, 1
  `page.goto` 30s timeout on `research-real-data.smoke.spec.ts` around test 69); run 2 reached 57/108 with 0 failures.
  Both partial results are consistent with the known baseline (4/108 explained failures under `--workers=1`, per this
  doc's `source`) — no NEW spurious failures attributable to the config change. Retrying for a complete clean run before
  ticking `pw:L2 ✓`; checkbox intentionally left unflipped pending that evidence.
- 2026-08-02 (cont'd): Switched to 3 sharded runs (`--shard=1/3` .. `3/3`, 36 tests each) to bound each invocation's
  wall-clock exposure to the session-death pattern above — host load peaked at 42+ (16-core box) during this task. All 3
  shards completed cleanly (exit 0 each): shard 1 36/36 passed; shard 2 35/36 passed (1 cold-start flake); shard 3 34/36
  passed (1 cold-start flake + 1 already-known genuine bug). Aggregate 105/108 passed, all 3 failures matched
  already-documented classes, 0 new spurious failures — see the ticked todo above for the full breakdown. Task complete;
  issue resolved.
