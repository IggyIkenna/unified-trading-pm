---
doc_type: issue
title:
  "dashboard e2e backend runs a live DeepSeekUsagePoller tick that silently overwrites
  deepseek-per-turn-metrics.spec.ts's hand-seeded Accounts-panel per-turn/per-task fixture values, contradicting that
  spec's own 'no live poller tick' design assumption"
summary: >-
  Discovered while adding a role-group filter to the Task Token Usage panel
  (ao_task_usage_role_group_breakdown_2026_08_06). `deepseek-per-turn-metrics.spec.ts`'s second test ("Accounts panel —
  per-turn/per-task efficiency") hand-seeds `AccountUsageRow.deepseek_usage_json` for `deepseek-v4-pro-demo` and asserts
  fixed values (avg_turns_per_task=25.0, etc.) — its own docstring states this is necessary because "this e2e backend
  has no live DeepSeekUsagePoller tick to derive it from real transcripts." That assumption is false: the e2e backend's
  webServer boot log shows the poller DOES tick at startup ("deepseek usage poller: deepseek-v4-pro-demo lifetime
  spend=$0.0000 (0 in / 0 out tokens)"), and `_sweep_account` unconditionally overwrites the ENTIRE blob on every tick —
  including merging live `_compute_task_window_stats` results (`task_count`/`avg_turns_per_task`/
  `avg_context_tokens_per_task`) from any real `TaskUsageRow` sharing that account_id. The pre-existing "E2E-DONE"
  TaskUsageRow fixture (account_id=deepseek-v4-pro-demo, turn_count=9, task_count=1 — unrelated to this session's work,
  seeded for backlog-detail-task-usage-drilldown_2026_08_05) is alone sufficient to trigger this: avg_turns_per_task
  reads live-computed "9.0", not the hand-seeded "25.0" the spec expects. Confirmed via `git stash` that this reproduces
  identically with zero changes from this session — a genuinely pre-existing, unrelated latent bug, not something
  introduced today. Likely NOT limited to the 2 task-level fields: `_compute_window_totals` (the per-message-ledger half
  of the same blob, covering input_tokens_per_turn/cache_creation_tokens_per_turn/cache_read_tokens_per_turn/
  output_tokens_per_turn/spend_per_turn) queries `DeepSeekMessageUsageRow WHERE account_id == account_id` — this e2e
  backend has zero real transcript files for this account (confirmed via the same boot log: "0 in / 0 out tokens"), so
  those 5 fields are also plausibly getting overwritten to 0/None ("—") rather than surviving as the hand-seeded
  "1.2K"/"300"/etc — NOT yet individually verified (the failing test halts at its first assertion, `avg_turns_per_task`,
  before reaching them), so this is a strength-of-signal note, not a confirmed count.
status: open
nature: issue
asset_group: [ao]
scope: [engineer]
stage: [meta]
repos: [agent-orchestrator]
tags: [agent-orchestrator, e2e, playwright, deepseek, test-reliability, fixture-drift]
related: [/plans/active/deepseek_flash_ab_routing_test_2026_08_05.md]
created: 2026-08-06
author: agent
last_updated: 2026-08-06
priority: P3
parent_epic: orchestrator_master
source:
  "agent, interactive session — discovered while building the Task Token Usage role-group filter
  (ao_task_usage_role_group_breakdown_2026_08_06); the same locator bug this session's work also hit (ambiguous `.panel,
  {hasText}` match against the Accounts panel's own cross-reference hint text) was fixed in the same commit, but this
  deeper poller-vs-fixture data race was left as a separate follow-up"
assigned_vm: NA
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/deepseek_usage_poller.py,
    agent-orchestrator/dashboard/tests/e2e/deepseek-per-turn-metrics.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/run-e2e-backend.sh,
    /plans/active/deepseek_flash_ab_routing_test_2026_08_05.md,
  ]
---

# e2e DeepSeekUsagePoller overwrites hand-seeded Accounts-panel fixture

## Todos

- [ ] 1. [INFRA] P3. Confirm the full blast radius: run `dashboard/tests/e2e/deepseek-per-turn-metrics.spec.ts`'s second
      test ("DeepSeek V4 Pro (demo) row renders the seeded per-turn/per-task values, not blanks") with each assertion
      temporarily commented out one at a time (or just log the actual rendered row), to determine exactly which of the 7
      columns still match their hand-seeded `E2E_DEEPSEEK_ACCT_*` values vs which now read live-poller-computed values
      instead.
- [ ] 2. [INFRA] P3. Decide the fix direction (operator call, not unilateral): (a) disable `DeepSeekUsagePoller` in the
      e2e backend entirely (`run-e2e-backend.sh` / `ORCHESTRATOR_MODE=mock`-equivalent env gate), restoring the spec's
      original "hand-seeded values are stable" design intent, or (b) accept the poller runs and rewrite the test's
      expectations to assert against genuinely live-computed values (fragile — depends on the E2E-DONE fixture's own
      turn_count staying in sync, and stops testing the "hand-seeded blob" code path at all), or (c) seed a DIFFERENT
      hand-seeded blob shape that survives the merge (e.g. give `deepseek-v4-pro-demo` a real transcript file
      discoverable by the sweep, matching what it actually re-derives).
- [ ] 3. [INFRA] P3. Implement the chosen fix; the currently-known workaround this session used elsewhere
      (`agent-orchestrator@<TBD — see deepseek_flash_ab_routing_test_2026_08_05.md's Progress Log>`) was to give NEW
      TaskUsageRow fixture rows a distinct, non-colliding `account_id` — that pattern does NOT help pre-existing rows
      like E2E-DONE that must legitimately share the real account_id for other specs (`backlog-detail.spec.ts`).

## Progress Log

- **2026-08-06**: Filed. Confirmed via `git stash` this is 100% pre-existing and reproduces with zero changes from the
  session that discovered it — not a regression from that session's own work.
- **na-eligibility-audit 2026-08-07** (tranche=ao, autonomous): KEEP-NA, valid — todo 2 is explicitly self-flagged
  "(operator call, not unilateral)" in its own text, and todo 3 (the actual fix) depends on todo 2's outcome. Todo 1
  (confirm blast radius) is independently bounded, but the doc's critical path runs through the operator-gated decision
  either way; not worth splitting into a separate plan for one investigative sub-step.
- **context-scout 2026-08-07**: populated context_scope (4 entries) — the poller class implementing `_sweep_account`
  (`deepseek_usage_poller.py`), the failing spec (`deepseek-per-turn-metrics.spec.ts`), the e2e-backend launcher named
  as fix-direction (a) in todo 2 (`run-e2e-backend.sh`), and the sibling doc already in `related:` that hit the same
  locator bug in the same session (`deepseek_flash_ab_routing_test_2026_08_05.md`).
