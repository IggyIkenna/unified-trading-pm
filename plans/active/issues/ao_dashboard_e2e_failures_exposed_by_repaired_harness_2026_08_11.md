---
doc_type: issue
title:
  Two dashboard e2e failures the repaired Playwright harness exposed — DeepSeek wallet spend split, and an intermittent
  parked-tasks row count
summary: >-
  The dashboard e2e suite could not boot at all until 2026-08-10 (see the archived harness issue), so nothing had run it
  in some time. With it working, two failures surface that are NOT harness problems. (1) DETERMINISTIC —
  deepseek-wallet-reconciliation.spec.ts asserts Worker (backlog tasks) spend of $3.0000 and gets $5.0000. The spec was
  last touched 2026-08-08; `server/subscription_value.py` and task_usage attribution both changed 2026-08-10
  (`feat(usage): price Anthropic models` c40d847 and `fix(usage): single-ownership task_usage attribution — partition
  turns across overlapping task windows` 382e278), and re-partitioning turns across overlapping task windows is exactly
  what moves a worker/orchestrator/review split. Deliberately NOT "fixed" by editing the expectation to $5 — that would
  rubber-stamp a possible money-attribution regression as correct. Needs the author of the attribution change to say
  which number is right. (2) INTERMITTENT — parked-tasks.spec.ts's "unpark moves the row from the list" failed once on a
  toHaveCount assertion during a full sequential run, then passed 5/5 twice in isolation.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dashboard, playwright, e2e, usage-attribution, deepseek]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/issues/ao_dashboard_e2e_harness_boot_budget_and_fixture_writeback_2026_08_10.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-08-11"
last_updated: "2026-08-11"
author: slot-2 (interactive)
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: devops
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source: >-
  Full e2e regression run after repairing the harness (slot 2, 2026-08-10/11) — 81/83 green, these two are the residue.
---

# Two e2e failures the repaired harness exposed

Context: the harness itself is fixed and verified (archived issue linked above — boot budget, fixture staging,
slot-blind ports, per-project server scoping). These two failures are what a working suite then found. Neither is a
harness defect and neither should be closed by relaxing an assertion.

## 1. DeepSeek wallet spend split — DETERMINISTIC, needs an owner ruling

```
Locator: .panel …'DeepSeek Wallet Reconciliation' … tr … 'Worker (backlog tasks)'
Expected substring: "$3.0000"
Received string:    "Worker (backlog tasks)$5.0000"
```

Reproduces every run of `npx playwright test --project=chromium deepseek-wallet-reconciliation`. The sibling assertions
in the same test (`Current balance` $70.0000, `Real total spend` $30.0000) pass — only the worker slice of the split is
off, which points at attribution rather than at pricing or the fixture totals.

Timeline that makes this a code-vs-spec question rather than a stale test:

| what                                                                                                              | when       |
| ----------------------------------------------------------------------------------------------------------------- | ---------- |
| `deepseek-wallet-reconciliation.spec.ts` (343501a)                                                                | 2026-08-08 |
| `feat(usage): price Anthropic models …` (c40d847)                                                                 | 2026-08-10 |
| `fix(usage): single-ownership task_usage attribution — partition turns across overlapping task windows` (382e278) | 2026-08-10 |

Partitioning turns across overlapping task windows changes which bucket a turn's spend lands in — precisely a
worker-vs-orchestrator-vs-review reallocation. So either the new attribution is right and the fixture expectation is
stale, or the partition moved
$2 of worker spend somewhere it does not belong. This is money attribution; it is not a
number to guess at, and editing the assertion to `$5.0000`
to get a green suite would destroy the only signal that something moved.

## 2. `parked-tasks.spec.ts` unpark row count — INTERMITTENT

`"Unpark (via the detail panel) moves the row from the list"` failed once on a `toHaveCount` assertion during a full
sequential run, and passed 5/5 on two subsequent isolated runs of the same project. Not reproduced since; recorded
because an intermittent count assertion in a suite nobody could run for weeks is exactly the kind of thing that gets
written off as noise twice and then bites.

## Todos

- [ ] [OPERATOR] P2. Rule on the wallet split: is `$5.0000` for Worker (backlog tasks) the CORRECT post-382e278
      attribution (→ update the fixture expectation, citing why) or a regression from partitioning turns across
      overlapping task windows (→ fix `server/` and leave the spec alone)? Needs whoever owns 382e278 — do not resolve
      by editing the assertion to match observed output.
- [ ] [UI] P3. Reproduce `parked-tasks` "unpark moves the row from the list" under repeated sequential runs
      (`npm run test:e2e:all` in a loop). If it is a real race in the unpark→list-refresh path, fix it; if it is a
      test-side wait, tighten the assertion. Do not add a blanket retry.

## Progress Log

- **2026-08-11** — Found by the first full e2e regression run possible since the harness broke (slot 2, interactive).
  Sequential per-project run: 81 passed, 1 deterministic failure (wallet), 1 intermittent (parked-tasks). Isolated
  re-runs: `parked-tasks` 5/5 twice, `fleet-typed-agent-work` 3/3, `worker-chat` 3/3, `critical-health` 2/2,
  `tier-editor` 4/4, `backlog-collision` 2/2.
