---
doc_type: plan
title: one_shot_complete session-ownership desync — finalize
summary: >-
  Gated closeout for `one_shot_complete_session_ownership_desync_2026_08_08.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until its sole todo (fix idle-reap reclassifying a slot mid-`ScheduleWakeup`-gap) is done.
  Reconciles the shipped fix against the two confirmed live occurrences before archiving.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, one-shot-dispatch, close-out, archival, plan-hygiene]
related:
  [
    /plans/active/issues/one_shot_complete_session_ownership_desync_2026_08_08.md,
    /plans/epics/agent_operating_framework_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/one_shot_complete_session_ownership_desync_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [one_shot_complete_session_ownership_desync_2026_08_08]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# one_shot_complete session-ownership desync — finalize

> **Machine-gated on `one_shot_complete_session_ownership_desync_2026_08_08.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until the parent doc's sole todo is `done`.

## Todos

- [x] ✅ [REVIEW] P1. Reproduced via test-simulation, not a code-review pass. Read the full fix diff
      (agent-orchestrator@43fc142: `slots_worker.py`, `tmux_pruner.py`, `state_store/agents.py`, `orm.py`,
      `bootstrap.py`, `models/worker_api.py`) end-to-end and confirmed the mechanism matches the parent doc's root
      cause: `tmux_pruner` now snapshots `last_tmux_session` before nulling `tmux_session` on a `reaped-stale` archive
      (heuristic `has_session()`-miss, not a genuine completion); `_done_one_off` falls back to
      `find_reaped_stale_agent_for_session` (or a caller-supplied `agent_id`, scoped to
      `tmux_session == this-slot's-session OR last_tmux_session == this-slot's-session` so a stale/foreign `agent_id`
      can't be misapplied) and corrects `exit_reason` to `lifecycle-complete` WITHOUT touching `SlotRow` (avoids
      clobbering a slot already reassigned to unrelated work — exactly occurrence 2's failure mode). Verified the 6 new
      `tests/test_done_one_off.py` tests exercise the EXACT repro recipe: `_seed_reaped_stale()` mirrors `tmux_pruner`'s
      real post-archive state (`status=archived`, `tmux_session=None`, `last_tmux_session=<session>`,
      `exit_reason=reaped-stale`, using the same `kind="cefi_mtds_smoke_tester"` as the live occurrence-2 repro), then
      calls the real `_done_one_off(slot_id, one_shot_complete=True)` handler and asserts `status == "idle"` with no
      `HTTPException` raised (i.e. no 400) — plus recovery-via-`agent_id`, cross-slot `agent_id` rejection, evidence
      persistence, and duplicate-call-409 coverage. Independently re-ran (did not trust the shipping commit's
      self-report per review's evidence-verification rule) `bash scripts/quality-gates.sh` on agent-orchestrator HEAD
      `43fc142` — full green: ruff clean, basedpyright 0 errors, **2768 passed, 2 skipped** (superset of the commit's
      own claimed 2760/2 — consistent with other work landing since), pip-audit cached. Also confirmed `43fc142` is a
      verified ancestor of `origin/live-defi-rollout`. Done-when satisfied: a test-simulated reproduction (independently
      re-executed, not just read) is cited above. Repo: unified-trading-pm.
- [x] ✅ [DOCS] P2. **DONE 2026-08-21 (archival lane, chunk 4).** Confirmed zero open `- [ ]` todos remained on the
      parent doc; added the archival banner + set `status: archived`; grepped the corpus for
      `one_shot_complete_session_ownership_desync_2026_08_08` and confirmed every OTHER referrer's citation was
      prose-only (historical narrative, not a structural `related:` pointer) — no repoint needed per
      `plan-completion-and-archival-discipline.md`'s prose-citation carve-out; this doc's own `related:` + this
      INDEX.md's own entry were the two structural pointers and both are updated in this same commit. Physically
      moved the parent doc to `plans/archive/issues/one_shot_complete_session_ownership_desync_2026_08_08.md` (flat
      path, `doc_type: issue`). This finalize plan itself now has 0 open todos and is archived alongside it (dated
      `plans/archive/2026_08/`, `doc_type: plan`). Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/04-architecture/agent-orchestrator-worker-liveness.md` · `plans/PLAN_FORMAT.md` ·
`plans/active/task_template.md` §4 (finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually dispatching
  via `depends_on` + `gate_on_depends: true` until the parent doc's sole todo is done.
- **2026-08-08 (REVIEW, slot 7)**: `[REVIEW]` todo flipped. Unlike a recent sibling gated-finalize dispatch this session
  (`defi_expected_unattempted_backlog_1m_2026_07_03_finalize`), this gate genuinely held correctly — the parent doc's
  sole `[BACKEND] P1` todo was already `[x]` done with a real, verified-on-origin commit (`agent-orchestrator@43fc142`)
  before this task dispatched. Full evidence in the todo above. `[DOCS]` archival todo intentionally left un-dispatched
  by me (this plan carries no `sequential: true`, so it could in principle be picked up by another slot independently —
  that is a plan-authoring gap outside this task's scope, not touched here).
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- re-verified all 5 still resolve; unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).
