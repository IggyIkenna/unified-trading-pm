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
related:
  [/codex/06-coding-standards/ui-testing-layers.md, /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md]
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

- [ ] [REVIEW] P2. **RULED 2026-08-09 (operator): investigate as a possible real regression FIRST — do NOT re-baseline
      the fixtures yet.** Trace `agent-orchestrator/server/deepseek_usage.py`'s `avg_turns_per_task` aggregation and the
      wallet worker-split computation against `fixtures/seed_e2e_state.py`'s seeded `TaskUsageRow`s: identify whether
      any commit changed the aggregation formula since the specs' `25.0`/`$3.0000` expectations were authored, and state
      whether `9.0`/`$5.0000` is the correct output of the CURRENT formula applied to the seed data — case (a), fixture
      drift, safe to re-baseline — or a mismatch between intended and actual computation — case (b), real regression,
      needs a code fix, not a spec edit. Done when: this todo cites the specific commit/formula evidence for whichever
      case it is. Do not re-baseline the specs or change `deepseek_usage.py` as part of this todo — that is a follow-up
      once the investigation lands, and only if the investigation itself settles which value is authoritative (if it
      stays a genuine semantics call even after tracing the code/history, escalate back to `[OPERATOR]` rather than
      guessing). Repo: agent-orchestrator.
- [ ] [UI] P2. Once the two specs are green again, decide whether the dashboard Playwright suite should run anywhere
      automatically. It is currently in no gate: `scripts/quality-gates.sh` runs `tsc` + Vitest only, and
      `quality-gates-v2` does not invoke Playwright — so these two have been red with nothing reporting it. Reference
      `/codex/06-coding-standards/ui-testing-layers.md` § Gate Enforcement by Branch for where L2/L3 is supposed to run.

## Progress Log

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **2026-08-09 (operator ruling)**: RULED — investigate as a possible real regression FIRST, do NOT re-baseline the
  fixtures yet. Todo 1 retagged `[OPERATOR]` → `[REVIEW]` and reworded into a bounded investigation (trace the
  aggregation formula's history against the seed data, do not touch the specs or the computation as part of it).
  Considered reclassifying `assigned_vm: NA` → `planning` (dispatch-scope-eligibility bar,
  `plans/active/task_template.md` §4): declined for now — this doc's other open todo ([UI] P2, gate the Playwright suite
  into CI) is explicitly sequenced AFTER these specs go green and would be concurrently dispatchable the moment the doc
  goes AO-live (same-priority todos run concurrently by default; nothing here sets `sequential: true`), and
  distinguishing (a) fixture-drift vs (b) real-regression can still terminate in a genuine semantics call the
  investigation alone can't resolve, per the doc's own original framing. Stays `assigned_vm: NA` — revisit if the
  investigation lands a clean, code-only verdict.
- **na-eligibility-audit 2026-08-09 (round9)**: KEEP-NA, valid — re-confirms the same-day operator-ruling entry
  directly above (RECLASSIFY already explicitly considered and declined this session). No new facts change that
  call.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **2**, matching. The 2026-08-09 operator ruling entry explicitly considered `assigned_vm: NA → planning`
  (dispatch-scope-eligibility bar) and declined it for a stated, still-current reason: the `[UI]` item is sequenced
  after the `[REVIEW]` investigation and would become concurrently dispatchable the moment this doc goes AO-live, and
  the investigation can still terminate in a genuine semantics call the investigation alone can't resolve. Explicit
  dated operator consideration-and-decline, not re-litigated.
