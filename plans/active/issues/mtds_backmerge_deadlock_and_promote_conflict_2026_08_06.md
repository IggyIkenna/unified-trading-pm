---
doc_type: issue
title:
  market-tick-data-service main quality-gates-v2 red, resolved — same notify-slack.yml backmerge-deadlock class as
  strategy-service, plus a genuine LDR->main promote conflict
summary: >-
  Same day, same root-cause CLASS as
  `plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md`: `notify-slack.yml` was
  added to `live-defi-rollout` on 2026-08-05 but never promoted to `main`, so `main-backmerge-to-ldr.yml`'s
  reusable-workflow reference to it failed validation at 0s on every `main` push -> backmerge dead -> `main->LDR`
  reconcile never ran -> a genuine `pyproject.toml`/dependency-floor conflict on the LDR->main promote PR (#836,
  `mergeStateStatus: DIRTY`) never auto-cleared -> `market-tick-data-service` `main`'s `quality-gates-v2` sat RED,
  triggering the `main_ci_red` escalation `agt-33a744` (which hit its 90-min watchdog deadline and re-escalation cap
  before either fix landed). Two independent fixes closed it: an already-active AO worker (slot-12) landed
  `market-tick-data-service@33eeded3` ("fix(ci): add missing notify-slack.yml to main", 07:12 UTC) fixing the backmerge
  deadlock; a dispatched sub-agent then resolved PR #836's actual dirty conflict directly
  (`market-tick-data-service@c8e5478f`, "chore(promote): resolve LDR->main promote conflict (keep LDR content)", merged
  08:29:27 UTC as PR #836). `main`'s `quality-gates-v2` confirmed GREEN immediately after (run completed
  2026-08-06T08:29:33Z, conclusion=success).
status: resolved
resolved_by: market-tick-data-service@33eeded3 + market-tick-data-service@c8e5478f
nature: issue
asset_group: [ci]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [ci, ci-failures, quality-gates, promotion, backmerge, ldr-main, escalation, notify-slack]
related: [/plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md]
created: 2026-08-06
author: interactive session (operator-triggered CI audit) + dispatched sub-agent
last_updated: 2026-08-06
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: devops_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    "operator-triggered CI audit, 2026-08-06 — escalation agt-33a744 (main_ci_red, market-tick-data-service, unresolved
    at 90min deadline)",
  ]
context_scope:
  [
    market-tick-data-service/.github/workflows/main-backmerge-to-ldr.yml,
    market-tick-data-service/.github/workflows/notify-slack.yml,
    /plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md,
  ]
---

# MTDS main_ci_red: notify-slack.yml backmerge deadlock + a genuine promote conflict

## What happened

Identical failure class to `strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md`, same day,
different repo — `notify-slack.yml` landed on `live-defi-rollout` 2026-08-05 without a matching promotion to `main`,
breaking every repo's `main-backmerge-to-ldr.yml` that references it as a reusable workflow until each repo's `main`
individually got the file. For `market-tick-data-service` this meant the promote PR's own `pyproject.toml` conflict
(same shape as strategy-service's dependency-floor mismatch) never auto-resolved, leaving `main`'s `quality-gates-v2`
stuck red and the `main_ci_red` escalation (`agt-33a744`) unresolved past its 90-minute watchdog deadline.

## Fix (two commits, two different workers)

1. `market-tick-data-service@33eeded3` (slot-12, 07:12 UTC) — added the missing `notify-slack.yml` to `main`, unblocking
   the backmerge.
2. `market-tick-data-service@c8e5478f` (dispatched sub-agent, 08:19-08:29 UTC) — PR #836
   (`promote/market-tick-data-service/513a83dd32b9`) was still `DIRTY` (the backmerge fix alone didn't retroactively
   reconcile an already-open promote PR); resolved the conflict directly on the promote branch, keeping LDR's content,
   merged as PR #836.

Verified: `main`'s `quality-gates-v2` run completed `success` at 2026-08-06T08:29:33Z.

## Remaining housekeeping (not urgent — main is already green)

- [ ] [DEVOPS] P3. PR #835 (`fix/missing-notify-slack`, still OPEN) is now redundant — its fix landed via `33eeded3` on
      a different path. Close it as superseded, or confirm it has zero remaining diff vs `main` and merge it trivially.
      Cosmetic GH housekeeping only; does not affect CI health.
