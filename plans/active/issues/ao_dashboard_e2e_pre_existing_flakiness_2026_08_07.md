---
doc_type: issue
title: >-
  agent-orchestrator dashboard e2e suite has pre-existing, intermittent failures in 3 specs unrelated to the
  slot-namespaced-ports fix
summary: >-
  Discovered 2026-08-07 while verifying `ao_local_mock_server_workflow_truncation_and_e2e_port_collision_2026_08_07`'s
  Finding 2 fix (slot-namespaced dashboard e2e ports, shipped `agent-orchestrator@5d2ed4b09`). Running the FULL `npx
  playwright test` suite repeatedly surfaced intermittent failures in `deepseek-per-turn-metrics.spec.ts`,
  `deepseek-wallet-reconciliation.spec.ts`, `worker-chat.spec.ts` (both its tests), and `backlog-collision.spec.ts` —
  different subsets failed on different runs, and the SAME failures reproduced identically on the unmodified pre-fix
  baseline (verified via a `git stash`-based control run), confirming these are pre-existing and unrelated to the
  port/CORS changes. Not root-caused or fixed — filed as a separate issue since it's a distinct problem from the
  port-collision work that surfaced it.
status: open
nature: issue
asset_group: [ao, cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, e2e, playwright, flaky-tests, dashboard]
related:
  [
    plans/active/issues/ao_local_mock_server_workflow_truncation_and_e2e_port_collision_2026_08_07.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-08-07"
author: ikennaigboaka [interactive session]
priority: P2
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
estimate_class: infra
depends_on: []
parent_epic: infrastructure_master
resolved_by:
source:
  [
    "interactive session 2026-08-07 — verifying the dashboard e2e slot-namespaced-ports fix, ran the full Playwright
    suite twice post-fix and once more on a stashed (pre-fix) baseline as a control",
  ]
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/dashboard/tests/e2e/deepseek-per-turn-metrics.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/deepseek-wallet-reconciliation.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/worker-chat.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/backlog-collision.spec.ts,
  ]
---

# agent-orchestrator dashboard e2e suite: pre-existing intermittent failures, unrelated to slot-namespacing

## What was observed

Three consecutive full-suite `npx playwright test` runs (one before a `reuseExistingServer` experiment was reverted, one
after, one on a `git stash`-ed pre-fix baseline as a control) produced DIFFERENT subsets of failures each time, drawn
from the same pool of 6 test cases across 4 spec files:

- `deepseek-per-turn-metrics.spec.ts:80` — "DeepSeek V4 Pro (demo) row renders the seeded per-turn/per-task values, not
  blanks" (shared `chromium` project — the default backend/dashboard pair, used by dozens of other passing specs)
- `deepseek-wallet-reconciliation.spec.ts:32` — "renders the worker/orchestrator/review split and residual from the
  seeded fixture" (same shared `chromium` project)
- `worker-chat.spec.ts:48` and `:101` — both of its 2 tests (dedicated `worker-chat` project — the one backend that owns
  a real background tmux session)
- `backlog-collision.spec.ts:53` — "click Fix remints the collision..." (dedicated `backlog-collision` project; failed
  in 2 of 3 runs, passed in the 3rd — genuinely intermittent, not "always fails")

**Confirmed unrelated to the port-collision fix**: with the port/CORS/CIReconcile changes fully `git stash`-ed back to
the untouched baseline, a control run reproduced the SAME 4 of these failures (`deepseek-per-turn-metrics`,
`deepseek-wallet-reconciliation`, `worker-chat` x2) — proving they are pre-existing and were never caused by the
slot-namespacing work. `backlog-collision` passed on that particular control run but had already failed on both prior
runs (before AND after the fix), consistent with genuine intermittency rather than a regression tied to any specific
change.

Since only SOME tests within each shared/dedicated project fail (not the whole project), a systemic
connectivity/CORS/backend-boot problem is ruled out — this is test-specific flakiness, not an infrastructure break.

## Not investigated

- Whether `deepseek-per-turn-metrics` / `deepseek-wallet-reconciliation` depend on an async poller (the backend logs
  show a "deepseek usage poller" / "deepseek balance poller" ticking independently) completing a fetch cycle BEFORE the
  test's assertion runs — a poller-interval-vs-test-timeout race would explain exactly this "sometimes passes, sometimes
  doesn't" pattern.
- Whether `worker-chat.spec.ts`'s real background tmux session (`run-e2e-backend-chat.sh`) has a startup-timing
  dependency that occasionally isn't satisfied within the test's timeout window.
- Whether `backlog-collision.spec.ts`'s "click Fix remints the collision" assertion has a similar async-completion race
  (the "remint" action + "a follow-up API call confirms the new task_id is clean" step suggests a multi-request sequence
  that could race).
- Exact failure-mode detail (timeout vs assertion mismatch vs error) for each — only the summary lines were captured
  during triage; the full per-test error/stack-trace output was not preserved.

Separately, `parked-tasks.spec.ts`'s "Dispatch now clears the park and removes the row from the list" test is ALSO
intermittently flaky, but for an ALREADY-UNDERSTOOD, DIFFERENT reason (not filed here): its "Dispatch" action mutates
the checked-in `dashboard/tests/e2e/fixtures/parked.e2e.yaml` fixture directly on disk instead of an isolated copy, so a
second local run against the already-mutated fixture sees different rows than the test expects. Confirmed via
`git diff`/`git checkout --` during this same session. Not included in this issue's todos since the cause is already
known — see the "Findings triage" note in `CLAUDE.md` if this needs its own tracked fix later.

## Todos

- [ ] [TEST] P2. **Root-cause `deepseek-per-turn-metrics.spec.ts` + `deepseek-wallet-reconciliation.spec.ts`
      intermittent failures** — check for an async-poller-vs-test-timeout race first (most likely candidate given the
      backend's independent usage/balance pollers); add an explicit wait-for-poller-tick or increase the assertion
      timeout if confirmed, per the standard Playwright convention already used in `critical-health.spec.ts`'s own
      cold-start comment.
- [ ] [TEST] P2. **Root-cause `worker-chat.spec.ts`'s 2 intermittent failures** — check the real tmux session's
      startup-timing dependency; this spec is the most operationally distinct (real background process, not just DB
      state) so may need a different fix shape than the others.
- [ ] [TEST] P3. **Root-cause `backlog-collision.spec.ts`'s intermittent "click Fix" failure** — check for an
      async-completion race in the remint→confirm sequence.
- [ ] [DOC] P3. **Once root-caused, note the fix pattern in `/codex/06-coding-standards/ui-testing-layers.md`** if a
      general "async-poller-vs-test" convention emerges, so future specs avoid the same class of flake.

## Why this wasn't chased further this session

Discovered as a side effect of verifying an unrelated fix (dashboard e2e port slot-namespacing); root-causing each of
these 3 specs' timing/race conditions properly needs focused per-spec debugging (adding logging, running each in
isolation repeatedly to find the actual failure mode), which is out of scope for the session that surfaced them.
Confirmed via a stash-based control run that none of it is caused by or blocks the port-collision fix, so that fix
shipped independently or these findings would still be sitting entirely undocumented.
