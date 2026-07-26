---
doc_type: issue
title:
  ensure_review_agents held the DB write lock across _do_spawn — database-is-locked cascade during the 2026-07-26
  backlog surge
summary:
  Live-diagnosed while investigating why fleet-cap headroom (a free slot) sat unfilled for 4.5+ minutes despite 81
  queued backlog tasks during a ~130-task surge. ensure_review_agents (server/autospawn.py) was not covered by
  orchestrator_spawn_reliability_db_lock_2026_06_10's Phase 2 fix — it still called the slow _do_spawn (up to the ~120s
  boot-readiness ceiling) from inside its own session_scope() transaction, holding the BEGIN-IMMEDIATE write lock and
  causing concurrent loops (AutoSpawnLoop's escalation drain, confirmed live) to hit "database is locked". Fixed with
  the same snapshot-then-spawn-outside-transaction pattern already used for the other three spawn callers.
status: resolved
nature: record
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, autospawn, sqlite, database-locked, dispatch, review-agent]
related:
  [
    /plans/archive/2026_06/orchestrator_spawn_reliability_db_lock_2026_06_10.md,
    /plans/active/ao_backlog_collision_alert_and_remediation_ui_2026_07_26.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
source:
  Diagnosed live via a dispatch-health watcher (dispatch_health_watch.py, deployed to the orchestrator VM this session)
  that flagged fleet headroom opening up (a tmux session freed) while 81 backlog tasks stayed queued for 3+ consecutive
  90s polls — the one signal distinguishing a real dispatch defect from ordinary capacity pressure. journalctl on the VM
  showed the exact traceback at the same moment.
resolved_by: interactive session, 2026-07-26, agent-orchestrator@d86dc8f
locked_by:
supersedes:
superseded_by:
---

> **🟢 RESOLVED 2026-07-26** — the fix shipped and verified in the same session: `agent-orchestrator@d86dc8f`,
> `bash scripts/quality-gates.sh` green, regression test confirmed load-bearing via bug-injection. Archived immediately,
> no deferred work.

# ensure_review_agents held the DB write lock across `_do_spawn`

## What I found

While arming a watcher for the 2026-07-26 ~130-task backlog surge (sports batch5, cefi batch2, the ao_backlog_collision
plan), the watcher's 3-poll grace window fired a confirmed anomaly: 1 free fleet-cap slot sat unfilled for ≥270s while
81 tasks were queued — not capacity pressure (the fleet was measurably below its 10-worker cap at that moment).

Direct `journalctl -u orchestrator` on the VM at that exact timestamp showed:

```
File ".../autospawn.py", line 177, in ensure_review_agents
    slot = session.get(SlotRow, slot_id)
...
sqlite3.OperationalError: database is locked
[SQL: BEGIN IMMEDIATE]
...
2026-07-26 01:48:16,993 ERROR AutoSpawnLoop: queued-escalation retry failed (continuing)
```

`server/db.py`'s `busy_timeout=120000` (120s) is already the widest tolerance this codebase carries for exactly this
class of contention (raised there per the 2026-06-10 incident). Both errors trace back to the same root:
`ensure_review_agents` opens a single `with session_scope()` transaction and, for each review slot needing a fresh
spawn, calls `_do_spawn` — which can hold the boot-readiness wait for up to ~120s — **from inside that same
transaction**. `orchestrator_spawn_reliability_db_lock_2026_06_10` Phase 2 fixed this exact pattern for
`autospawn._run_one_tick`, `escalation.escalate`, and `plan_health.dispatch` ("ALL THREE spawn callers restructured") —
`ensure_review_agents` is a fourth spawn caller that was never included in that refactor's scope, and kept the pre-fix
pattern.

Under the current backlog surge's concurrency (10 workers alive, multiple regen/ escalation/keeper loops ticking), a
review-agent respawn holding the lock for up to 120s was enough to make `AutoSpawnLoop`'s own escalation drain — and,
per the observed symptom, its regular backlog-dispatch tick too — intermittently fail or delay, starving the free slot
of new work despite dispatchable tasks existing.

## Fix

`server/autospawn.py::ensure_review_agents` — restructured into the same three-pass shape as `_run_one_tick`:

1. Short transaction: decide which review slots need a fresh spawn (seed/outage/flap/ cooldown checks,
   heartbeat-refresh-and-skip, heartbeat-silent-kill-then-respawn, account pick), collect a detached `snapshot_slot()` +
   account per candidate. No `_do_spawn` call in this pass.
2. No session held: run `_do_spawn` for each candidate.
3. Short transaction per result: persist the outcome (`log_activity`, flap/failure bookkeeping) and re-attach whatever
   `_do_spawn` wrote onto the detached snapshot (`claude_session_id`/`tmux_session`/`account_id`/`last_spawned_at`) back
   onto the real `SlotRow` — otherwise those writes are lost on a detached object, the same loss `_run_one_tick`'s own
   post-spawn block already guards against.

Regression test `test_ensure_review_agents_spawn_runs_outside_db_session` asserts the exact call ordering (session
closes before `_do_spawn`, reopens only after) via a tracked context manager; bug-injected (reverted the source fix,
kept the test) to confirm it fails at the correct point before restoring. Full `bash scripts/ quality-gates.sh` green
(1738 tests + dashboard tsc/vitest).

- [x] ✅ [BACKEND] P1. Move `ensure_review_agents`'s spawn outside its DB transaction, mirroring `_run_one_tick`'s
      Phase-2 pattern; regression test added + bug-injection-verified. (repo: agent-orchestrator) —
      agent-orchestrator@d86dc8f

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — autospawn/ dispatch model this bug and fix
  both live in.
