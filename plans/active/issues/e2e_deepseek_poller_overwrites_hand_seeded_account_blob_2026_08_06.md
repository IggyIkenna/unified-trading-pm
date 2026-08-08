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
related:
  [
    /plans/active/deepseek_flash_ab_routing_test_2026_08_05.md,
    /plans/active/issues/ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md,
  ]
created: 2026-08-06
author: agent
last_updated: 2026-08-08
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
- [x] 2. [INFRA] P3. ✅ **DIRECTION DECIDED (round5 ao investigation) — option (a): disable `DeepSeekUsagePoller` in the
      e2e backend.** Blast-radius check performed before recommending (the missing input the original "operator call"
      framing lacked): grepped every `dashboard/tests/e2e/*.spec.ts` for any reference to the poller/live sweep behavior
      — `deepseek-per-turn-metrics.spec.ts` (this doc's own failing spec) is the ONLY one that touches it.
      `deepseek-wallet-reconciliation.spec.ts` (the spec the sibling doc's now-superseded "async-poller-vs-test-timeout
      race" hypothesis bundled alongside this one) reads directly from `seed_e2e_state.py`-seeded
      `deepseek_message_usage`/top-up rows, not from a live poller sweep — confirmed by reading its fixture doc-comment
      and assertions directly; it does not need the poller to tick at all. The poller starts unconditionally in
      `server/server.py:234` with no existing e2e-mode gate. So option (a) has zero known cross-spec blast radius, and
      it's also the ONLY option that restores this exact test's own original stated design assumption ("this e2e backend
      has no live DeepSeekUsagePoller tick to derive it from real transcripts") rather than working around its violation
      — option (b) was already self-flagged fragile by this doc's own text, and (c) adds a transcript-file-freshness
      dependency neither existing option carries. **Remaining work** (out of scope for this unified-trading-pm-only
      investigation pass — needs an `agent-orchestrator` code change): add the e2e-mode gate (`run-e2e-backend.sh` env
      var, checked in `server.py` before constructing `DeepSeekUsagePoller`), verify the full spec goes green, ship via
      `agent-orchestrator`'s own quality-gates.sh + quickmerge. Todo 1's per-column blast-radius check WITHIN the
      failing spec itself (which of the 7 hand-seeded columns currently mismatch) is unaffected by this finding and
      remains open below — this decision doesn't need that answer, but the eventual fix-implementer may still want it
      for the regression-test writeup.
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

- **na-eligibility-audit 2026-08-08 (cross-link only, via the sibling doc's conflict-check)**: added
  `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` to `related:` — that doc's own todo 1 (bundling
  `deepseek-per-turn-metrics.spec.ts` + `deepseek-wallet-reconciliation.spec.ts` under an unconfirmed
  async-poller-vs-test-timeout race hypothesis) was found to conflict with THIS doc's already-confirmed, more specific
  root cause (the poller unconditionally overwrites the hand-seeded blob on every tick, not a race) during that doc's
  na-eligibility-audit conflict-check pass. No content change here — this doc's own KEEP-NA verdict (2026-08-07) stands
  unchanged; a future worker on either doc should read both before acting on `deepseek-per-turn-metrics.spec.ts`.
