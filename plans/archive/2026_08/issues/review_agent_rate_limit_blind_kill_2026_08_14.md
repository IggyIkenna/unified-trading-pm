---
doc_type: issue
title: Review agent kept getting force-killed as "hung" while correctly waiting on an exhausted account
summary: >-
  Operator reported (2026-08-14, follow-up to the same-day `ao_kick_escalation_rate_limit_blind_force_kill_2026_08_14`
  incident) that review agents were "still going down" after that fix shipped. Live SSM read against AO's `state.db`
  confirmed: the `agents` table shows the review role churning every 30-90 min all day, `exit_reason` cycling through
  `dead-tmux-session` / `stale-no-session` / `superseded-session` / `superseded-review`, with
  `agentkeeper_review_succeeded` firing 118 times in 48h — i.e. a genuine, repeated kill+respawn, not a benign
  bookkeeping artifact. Root-caused to a DISTINCT, previously-unpatched instance of the same bug class:
  `ensure_review_agents()` (`agent-orchestrator/server/autospawn.py`) kills a review session as "hung" whenever its
  `/poll` heartbeat goes silent past `_review_heartbeat_timeout_seconds()` (20min floor), with no check for whether the
  pane is actually sitting on Claude Code's own "Stop and wait for limit to reset" out-of-credits menu first. A review
  agent correctly waiting there is CORRECTLY /poll-silent — not hung — but got killed and respawned on a fresh account
  anyway, which then also ran dry in turn, producing the observed all-day churn. `WorkerLivenessKicker` already carries
  this exact guard (`_ACCOUNT_BLOCKED_RE` + `_handle_account_blocked_pane`, fixed 2026-08-14 for worker slots) and
  explicitly SKIPS review slots entirely (persistent /loop sessions are a different code path); `main_agent_keeper.py`
  has its own equivalent freeze-not-kill handling for the main agent. `ensure_review_agents()` was the one keeper path
  that never got the guard ported to it.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, review, watchdog, rate-limit, kick-escalation, force-kill, root-cause]
related:
  - /plans/archive/2026_08/issues/ao_kick_escalation_rate_limit_blind_force_kill_2026_08_14.md
  - /plans/active/ao_consolidated_closeout_2026_08_12.md
  - /codex/04-architecture/agent-orchestrator-worker-liveness.md
created: "2026-08-14"
author: main (Claude Code, interactive session)
parent_epic: orchestrator_master
resolved_by: agent-orchestrator@f842fe0a5e
locked_by:
locked_since:
source: >-
  Operator chat instruction, 2026-08-14: "also teh review agents keep doing down still we havent fixed that yet please
  do in AO" — a follow-up on the same day's kick-escalation force-kill incident, since that fix explicitly exempts
  review slots and did not itself touch review's own keeper.
assigned_vm: NA
execution_scope: local-only
priority: P1
drift_direction: advance-code
depends_on: []
---

## Fix

`agent-orchestrator/server/autospawn.py`: `ensure_review_agents()` now captures the pane once (already captured for the
`classify_pane` working-check) and, before the heartbeat-silent kill branch, checks it against a local
`_ACCOUNT_BLOCKED_RE` (same banner regex `worker_liveness/__init__.py` and `tmux_pruner.py` each carry their own copy of
— this codebase's existing convention is one small regex per consuming module, not a shared import). On a match: marks
the account rate-limited via `mark_account_rate_limited` (idempotent, same call the worker-kicker guard makes) and
`continue`s instead of falling through to `kill_session`. Once the account frees up, the review agent resumes polling
normally on its own next tick — nothing else changes.

Regression test added: `tests/test_autospawn.py::test_ensure_review_agents_skips_kill_when_account_blocked_pane` —
asserts `kill_session`/`_do_spawn` are NOT called and `mark_account_rate_limited` IS called when the pane shows the
blocked-account banner, even though `_review_agent_heartbeat_silent` reports true (would otherwise look hung).

Full `quality-gates.sh` green (3718 passed / 6 skipped pytest, 0 basedpyright errors, pip-audit clean, dashboard tsc +
vitest 346 passed) in an isolated sibling worktree (`.ao-iso-ship`, detached at origin tip) — the shared checkout had
unrelated foreign uncommitted WIP from a concurrent agent (`unified-trading-library`'s `.github/workflows/**`, plus
`agent-orchestrator/server/model_pricing.py` + its callers mid-refactor), so shipping went through the documented
dirty-deps direct-push carve-out (`Quickmerge: direct-carveout-dirty-deps`) rather than `quickmerge.sh`, which
pre-flight-blocks on any dirty path-dependency. The autostash triggered by an interim `git pull --ff-only` in the shared
checkout produced a real conflict on `model_pricing.py` between the concurrent agent's WIP and a newly-landed commit;
resolved by restoring the peer's stashed version (their WIP stays internally consistent, recoverable via
`git stash list`) and moving the fix to the isolated worktree instead of contesting the shared tree further.

## Todos

- [x] ✅ [MAIN] P1. **Port the `_ACCOUNT_BLOCKED_RE` account-exhaustion guard into `ensure_review_agents()`** so a
      review agent correctly waiting on an out-of-credits/rate-limited account is never misclassified as hung and
      force-killed. `agent-orchestrator/server/autospawn.py` (+ test in `tests/test_autospawn.py`). **Done**: shipped +
      `quality-gates.sh` green. Evidence: commit=agent-orchestrator@f842fe0a5e.
