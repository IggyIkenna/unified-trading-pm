---
doc_type: issue
title: >-
  `reap_orphan_agents`'s singleton-agent-kind dedup falsely archives concurrent tranche-sharded
  `plan_reconciler` workers mid-task, leaving permanently stuck `locked_by:` PM-repo locks
summary: >-
  Discovered while confirming two `plan_reconciler_findings_{ui,sports}_2026_08_19.md` dead-lock clears were safe.
  Direct read-only SQLite query against AO's live `state.db` `agents` table (via AWS SSM) shows the ui-tranche
  dispatch `agt-c82f06` (registered 2026-08-19 19:17:32Z) was archived at `2026-08-19 19:35:34.175624`Z, only 18min
  into its run, with `exit_reason=superseded-plan_reconciler` — NOT `reaped-stale`. A same-window query
  (`agent_kind='plan_reconciler' AND registered_at BETWEEN '2026-08-19 17:00:00' AND '2026-08-19 21:00:00'`) shows a
  SECOND plan_reconciler dispatch (`agt-d46d9a`, a different tranche, registered 19:16:31Z) was archived with the
  IDENTICAL reason at the IDENTICAL microsecond-precision timestamp (`.175602` vs `.175624`) — one single
  `reap_orphan_agents()` sweep tick killed both simultaneously. Root cause:
  `server/state_store/agents.py::_SINGLETON_AGENT_KINDS = frozenset({"review", "plan_health", "plan_reconciler",
  "docs_reconciler"})` treats `plan_reconciler` as a system-wide singleton (`_sessionless_singleton_duplicates`
  archives every same-`agent_kind` record that does not currently "own a live session" the instant ANY sibling
  does) — but `plan_health.dispatch(mode="reconcile", tranche=...)` has deliberately run MULTIPLE concurrent
  `plan_reconciler` instances (one per tranche) as its normal daily design since the 2026-08-06 sharding ruling
  (`plan_health.py`'s own docstring: unsharded runs measured "7 of 8 reaped-stale"). The dedup logic predates or
  never accounted for that sharding: whenever 2+ tranche-sharded `plan_reconciler` workers are concurrently
  registered and the `_owns_live()` `tmux_session` heuristic happens to pick one "winner" at a sweep tick, every
  other concurrently-running (not stale, not done) sibling gets archived mid-task with no path back — the exact
  same doc lock permanently-stuck failure mode `plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` was written to
  fix, but via a termination path (`superseded-{agent_kind}`) that mechanism's own `assess_lock()` does not
  recognize (it only auto-clears `exit_reason=="reaped-stale"`) — so neither of today's two locks would ever have
  self-healed via the existing automated sweep.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    plan_reconciler,
    reap_orphan_agents,
    singleton-agent-kind,
    dead-lock,
    tranche,
    false-positive,
    scheduled-jobs,
  ]
related:
  [
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
    /plans/active/issues/plan_reconciler_findings_ui_2026_08_19.md,
    /plans/active/issues/plan_reconciler_findings_sports_2026_08_19.md,
    /plans/archive/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
created: "2026-08-20"
last_updated: "2026-08-20"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
resolved_by:
source: >-
  Found by ikennaigboaka's interactive session (slot 6) while root-causing two dead `plan_reconciler` PM-repo
  locks (`agt-c82f06` ui-tranche, `agt-07473e` sports-tranche) for the operator-directed
  "clear two dead plan_reconciler locks" task, 2026-08-20. Neither dispatch's `exit_reason` matched the expected
  `reaped-stale` precedent, prompting a direct read-only SQLite query against AO's live state that surfaced this
  systemic bug.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/state_store/agents.py,
    agent-orchestrator/server/plan_reconciler_dead_lock_sweep.py,
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/server/tmux_pruner.py,
    /plans/active/issues/plan_reconciler_findings_ui_2026_08_19.md,
    /plans/active/issues/plan_reconciler_findings_sports_2026_08_19.md,
    /plans/archive/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md,
  ]
---

# `reap_orphan_agents` singleton-agent-kind dedup falsely kills concurrent tranche-sharded plan_reconciler workers

## Evidence

Read-only SQLite query against the live orchestrator VM's `data/state/state.db` `agents` table (AWS SSM
`send-command` → `sqlite3`, no HTTP API involved — `/api/agents?include_finished=true` was tried first and timed
out under load, see Progress Log), scoped to `agent_kind='plan_reconciler'` registered 2026-08-19 17:00-21:00 UTC:

```
agent_id    status    exit_reason                 registered_at               finished_at
agt-f212cb  archived  lifecycle-complete           2026-08-19 18:12:50.452455  2026-08-19 19:16:44.183019
agt-07473e  archived  lifecycle-complete           2026-08-19 18:14:02.126459  2026-08-19 20:20:41.116390
agt-be3ce1  archived  lifecycle-complete           2026-08-19 18:16:15.324326  2026-08-19 19:17:23.066710
agt-b2fcb2  archived  lifecycle-complete           2026-08-19 18:17:26.876235  2026-08-19 19:21:02.216033
agt-d46d9a  archived  superseded-plan_reconciler   2026-08-19 19:16:31.783787  2026-08-19 19:35:34.175602
agt-c82f06  archived  superseded-plan_reconciler   2026-08-19 19:17:32.711027  2026-08-19 19:35:34.175624
```

At 19:35:34 (a single `reap_orphan_agents()` tick — the two `finished_at` values differ by 22 microseconds, well
inside one function call), **three** `plan_reconciler`-kind agents were simultaneously registered+active:
`agt-07473e` (sports tranche, still running — later exits `lifecycle-complete` at 20:20:41), `agt-d46d9a` (a
different tranche), and `agt-c82f06` (ui tranche). Per `_sessionless_singleton_duplicates`
(`server/state_store/agents.py:408-441`), exactly one member of a same-`agent_kind` group survives a sweep tick
once ANY member "owns a live session" (`_owns_live`, keyed on `AgentRow.tmux_session` + `is_session_live()`) — every
other member, regardless of whether it is itself still genuinely working, gets archived with
`exit_reason=f"superseded-{agent_kind}"`. `agt-07473e` evidently owned a live session at that tick (it survived);
`agt-d46d9a` and `agt-c82f06` did not (by whatever heuristic determines `tmux_session` state for these specific
worker registrations) and were both killed — `agt-c82f06` only 18 minutes into a run that its own findings doc
(`plan_reconciler_findings_ui_2026_08_19.md`) shows was still actively fanning out hunters, not winding down.

## Root cause

`_SINGLETON_AGENT_KINDS = frozenset({"review", "plan_health", "plan_reconciler", "docs_reconciler"})`
(`server/state_store/agents.py:405`) predates — or was never updated for — the 2026-08-06 tranche-sharding ruling
that made `mode="reconcile"` (`plan_reconciler`) a routinely-concurrent, multi-instance dispatch (one worker per
tranche, several tranches fired per day; sibling findings docs from the SAME day routinely note "concurrent sibling
runs on cefi/ao/cross-cutting/sports/tradfi today" as normal). The dedup helper's own docstring frames its purpose
as closing gaps from a genuinely SINGLE logical agent re-registering under a new id (backend `--reload` restarts, a
watchdog respawn reusing a session) — it was not designed to distinguish "the same logical worker respawned" from
"N independent, intentionally-concurrent tranche workers of the same kind." Grouping purely on `agent_kind` with no
tranche/label discrimination conflates the two.

Compounding this: the `PlanReconcilerDeadLockSweep` mechanism built specifically to auto-clear stuck PM-repo
`locked_by:` locks (`server/plan_reconciler_dead_lock_sweep.py`, `assess_lock()`) only recognizes
`exit_reason=="reaped-stale"` as "confirmed dead" (2026-08-15 operator ruling,
`/plans/archive/issues/plan_reconciler_dead_run_no_lock_ttl_2026_08_12.md` Option A). Neither
`superseded-plan_reconciler` nor `lifecycle-complete` (the second, unrelated gap this session also found on
`agt-07473e` — see that doc's own Progress Log entry) is recognized, so a lock stuck by either termination path
self-heals NEVER, silently defeating the whole point of the automated sweep for these cases.

## Impact

- Any day 2+ tranche-sharded `plan_reconciler` (or `docs_reconciler`/`plan_health`, which share the same singleton
  set — not independently confirmed vulnerable this session, worth checking) dispatches are concurrently active at
  a `reap_orphan_agents()` tick, one or more legitimate in-progress workers can be killed mid-task, silently
  discarding partial findings and leaving a permanently-stuck `locked_by:` lock on that tranche's findings doc.
  This plausibly explains a nonzero fraction of the "dead lock" incidents already on file across the corpus's
  dated `plan_reconciler_findings_*` docs beyond the two cleared today.
- The automated dead-lock sweep cannot recover from this failure mode at all (narrow `reaped-stale`-only check),
  so every occurrence requires a manual investigation + clear, same as this session did.

## Proposed fix direction

- [x] [BACKEND] P1. In `server/state_store/agents.py::_sessionless_singleton_duplicates`, make the dedup grouping
      tranche-aware for the modes that support concurrent tranche-sharded dispatch (`plan_reconciler`,
      `docs_reconciler` if it shares the same risk, `ag_closeout_auditor`/`na_eligibility_auditor` if they were ever
      added to a similar set) — e.g. group by `(agent_kind, tranche)` parsed from `label`/`current_task`/a new
      column, or exclude tranche-sharded kinds from `_SINGLETON_AGENT_KINDS` entirely and rely on the existing
      `_tranche_dispatch_gate` (`plan_health.py`) same-day same-tranche collision guard instead, which IS
      tranche-aware. Needs a regression test proving 2 concurrent different-tranche `plan_reconciler` registrations
      both survive a `reap_orphan_agents()` tick. — **Done: `agent-orchestrator@e8d83540`.** Went with the
      exclude-from-`_SINGLETON_AGENT_KINDS` option (checked `docs_reconciler`'s own mode `"docs_reconcile"` against
      `plan_health.py`'s `_TRANCHE_GATED_MODES = frozenset({"reconcile", "na_eligibility", "ag_closeout"})` first —
      it is NOT tranche-gated, so it correctly stays a singleton; only `plan_reconciler`'s `"reconcile"` mode both is
      tranche-gated AND was in `_SINGLETON_AGENT_KINDS`, confirming this was the one live collision, not a class of
      several). Added `test_concurrent_tranche_plan_reconciler_not_deduped_as_singleton` (mirrors the existing
      `test_multi_instance_cicd_not_deduped_as_singleton`); all 87 tests in the two affected test files pass.
- [ ] [BACKEND] P2. Investigate why `agt-d46d9a`/`agt-c82f06` did not register as "owning a live session"
      (`_owns_live`/`tmux_session`) while a concurrent sibling did, at the same tick — if tranche-sharded scheduled
      workers structurally don't reliably populate `tmux_session` the same way persistent workers do, that is a
      second, independent contributor worth understanding before the fix above ships. Note (2026-08-20): the P1 fix
      above ships without this — removing `plan_reconciler` from `_SINGLETON_AGENT_KINDS` means the singleton-dedup
      path this question was diagnosing no longer runs for it at all, so this is no longer a blocker for the P1 fix;
      still worth understanding separately for dashboard "who owns this session" display accuracy.
- [x] [BACKEND] P2. Extend `plan_reconciler_dead_lock_sweep.py::assess_lock()` to also recognize
      `exit_reason in ("superseded-plan_reconciler", "lifecycle-complete")` as confirmed-dead for the specific
      `plan_reconciler_findings_*.md` lock class (a worker's own self-stamped progress-lock correlated to a
      dispatch id AO's own state confirms is over, regardless of which specific termination path ended it) — closes
      the gap that made TWO manual investigations necessary today for exactly the failure class the sweep exists to
      auto-heal. Cite this doc + the 2026-08-15 ruling in the follow-up commit. — **Done, partially:
      `agent-orchestrator@e8d83540`** added `superseded-plan_reconciler` (unambiguous once the P1 fix ships — that
      exit_reason can no longer be produced for any NEW dispatch, so any row carrying it is confirmed evidence of the
      historical bug, not a live worker). Deliberately did **not** add `lifecycle-complete` — that's a genuine
      self-reported `/done`, and the P3 finding below raises a real open question about whether it always implies
      the worker reached its own unlock step; auto-clearing on it would risk papering over that exact failure mode
      rather than confirming it. Left as an explicit open policy question rather than silently deciding it.
- [ ] [BACKEND] P3. Separately: `agt-07473e` reached `lifecycle-complete` (a genuine `/done` call) while its own
      findings doc's `locked_by:` was never cleared and its Progress Log's last entry describes ongoing work, not a
      wrap-up — worth checking whether `agents/plan_reconciler.md`'s STEP 7 (unlock) is reliably reached before a
      worker calls `/done`, or whether there's a path (context exhaustion, turn budget, an external nudge) that can
      trigger a clean-looking exit without it.

## Progress Log

- **2026-08-20**: Filed while confirming `plan_reconciler_findings_ui_2026_08_19.md` / `plan_reconciler_findings_sports_2026_08_19.md`'s
  dead-lock clears were safe (see those docs' own Progress Log entries for the clear action itself). Not
  independently reproduced/tested — this is a root-cause writeup from live evidence, not a shipped fix. `assigned_vm`
  left `NA` pending an operator/dispatch decision on scope (touches `agent-orchestrator` core reaper logic used by
  every scheduled-job kind in `_SINGLETON_AGENT_KINDS`).
- **2026-08-20 (same day)**: P1 + one of the two P2 follow-ups shipped — `agent-orchestrator@e8d83540`. Removed
  `plan_reconciler` from `_SINGLETON_AGENT_KINDS`; confirmed via `plan_health.py`'s own `_TRANCHE_GATED_MODES` that
  `docs_reconciler` is NOT tranche-sharded (so correctly stays a singleton) and this was the only live collision.
  Extended `plan_reconciler_dead_lock_sweep.assess_lock()` to recognize `superseded-plan_reconciler` as
  confirmed-dead (not `lifecycle-complete` — left open, see the P3 todo). Added 2 regression tests; 87/87 pass in
  the two affected test files. `tofu validate`/quickmerge full quality-gates all green. The remaining P2
  (`_owns_live`/`tmux_session` investigation) and P3 (STEP 7 unlock reliability) items stay open as genuine
  investigative follow-ups, not blocking.
