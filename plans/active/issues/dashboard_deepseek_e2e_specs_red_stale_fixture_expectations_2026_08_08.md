---
doc_type: issue
title: >-
  Two DeepSeek dashboard e2e specs are red on live-defi-rollout — seeded-fixture expectations no longer match what the
  backend computes (avg_turns_per_task 25.0 vs 9.0, worker split $3.0000 vs $5.0000)
summary: >-
  Found 2026-08-08 while regression-checking the full `chromium` Playwright project after an unrelated
  `playwright.config.ts` change. `deepseek-per-turn-metrics.spec.ts:80` and `deepseek-wallet-reconciliation.spec.ts:32`
  both fail on stale hardcoded fixture expectations: the per-turn spec expects Lifetime `avg_turns_per_task` "25.0" and
  renders "9.0" (the seed literally sets `E2E_DEEPSEEK_ACCT_AVG_TURNS_PER_TASK = 25.0`, so something between the seed
  and the view recomputes/aggregates it — note seed_e2e_state.py's own line-305 comment about a TaskUsageRow whose turns
  "fold into deepseek-per-turn-metrics.spec.ts's hardcoded" values); the wallet spec expects the worker split to contain
  "$3.0000" and renders "Worker (backlog tasks)$5.0000". PROVEN PRE-EXISTING, not caused by the tier-editor work that
  found them — both fail identically at `665e5d0` (the commit immediately before that work's first commit `0cd01aaac`),
  verified by running them in a detached worktree at that commit. Not caught by CI or `quality-gates.sh`: neither runs
  Playwright, so the dashboard e2e suite is only ever exercised by whoever runs it by hand.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dashboard, e2e, playwright, deepseek, test-fixture, ci-gap]
related: [/codex/06-coding-standards/ui-testing-layers.md]
created: 2026-08-08
author: interactive-session (slot 4)
priority: P2
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "discovered 2026-08-08 regression-checking `npx playwright test --project=chromium` (44 passed / 2 failed) after
    adding tier-editor.spec.ts; provenance established by re-running both specs in a detached worktree at 665e5d0",
  ]
context_scope:
  [
    agent-orchestrator/dashboard/tests/e2e/deepseek-per-turn-metrics.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/deepseek-wallet-reconciliation.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/fixtures/seed_e2e_state.py,
    agent-orchestrator/server/deepseek_usage.py,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
---

# DeepSeek dashboard e2e specs red on stale fixture expectations

## Reproduce

```bash
cd agent-orchestrator/dashboard
npx playwright test --project=chromium tests/e2e/deepseek-per-turn-metrics.spec.ts \
                                       tests/e2e/deepseek-wallet-reconciliation.spec.ts
```

## The two failures

| Spec                                        | Assertion                         | Expected  | Rendered                        |
| ------------------------------------------- | --------------------------------- | --------- | ------------------------------- |
| `deepseek-per-turn-metrics.spec.ts:80`      | Lifetime row `avg_turns_per_task` | `25.0`    | `9.0`                           |
| `deepseek-wallet-reconciliation.spec.ts:32` | worker/orchestrator/review split  | `$3.0000` | `Worker (backlog tasks)$5.0000` |

## Why it is NOT the tier-editor change that found it

Both fail identically at `665e5d0` (`0cd01aaac^`), run in a detached worktree at that commit. Neither `0cd01aaac` (tier
editor) nor `95302ff35` (tier-editor e2e suite) touches any `deepseek*` or `seed_e2e_state.py` file.

## Which way to fix — needs the owner's call, hence not auto-fixed

`E2E_DEEPSEEK_ACCT_AVG_TURNS_PER_TASK = 25.0` is set explicitly in the seed, so 9.0 means the value the panel shows is
DERIVED (aggregated across seeded `TaskUsageRow`s), not the seeded scalar. So either:

- **(a) the fixture drifted** — a later commit added task rows that changed the aggregate, and the spec's hardcoded
  numbers simply need re-baselining (cheap, but re-baselining a red assertion is exactly how a real regression gets
  papered over — needs someone who knows the intended semantics); or
- **(b) the aggregation regressed** — the panel is no longer computing what `fff23c5` intended, and 25.0/$3.0000 are
  still the correct expectations.

Distinguishing (a) from (b) requires knowing which number is authoritative for `avg_turns_per_task` — the seeded
per-account scalar or the derived per-task aggregate. That is a semantics question for the deepseek-metrics owner, not a
mechanical fix, which is why this is filed rather than patched.

## Follow-ups

- [ ] [OPERATOR] P2. Decide (a) re-baseline vs (b) real regression for `avg_turns_per_task` (25.0 vs 9.0) and the wallet
      worker split ($3.0000 vs $5.0000), citing which value is authoritative — then fix accordingly in
      `agent-orchestrator`.
- [ ] [UI] P2. Once the two specs are green again, decide whether the dashboard Playwright suite should run anywhere
      automatically. It is currently in no gate: `scripts/quality-gates.sh` runs `tsc` + Vitest only, and
      `quality-gates-v2` does not invoke Playwright — so these two have been red with nothing reporting it. Reference
      `/codex/06-coding-standards/ui-testing-layers.md` § Gate Enforcement by Branch for where L2/L3 is supposed to run.
