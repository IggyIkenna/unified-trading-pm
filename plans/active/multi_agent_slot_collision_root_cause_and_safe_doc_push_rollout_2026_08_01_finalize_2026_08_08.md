---
doc_type: plan
title: Multi-agent slot collision + safe-doc-push hardening — finalize
summary: >-
  Gated closeout for `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md` — machine-held via
  `depends_on` + `gate_on_depends: true` until all 4 of that doc's remaining todos (rename-corruption fix, the
  now-unblocked `.agent-claim` heartbeat + session-start collision warning, and the codex/CLAUDE.md fold-in) are done.
  Verifies the live heartbeat + warning mechanism actually reduces collision frequency before archiving.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao, multi-agent-safety, git, close-out, archival, plan-hygiene]
related:
  [
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
    /plans/epics/agent_operating_framework_master.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-09"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/PLAN_FORMAT.md,
    /plans/active/task_template.md,
  ]
supersedes:
superseded_by:
depends_on: [multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01]
gate_on_depends: true
source: >-
  /na-eligibility-audit round7 RECLASSIFY sweep, 2026-08-08 — required companion per `plans/active/task_template.md`
  §4's finalize-plan-coverage rule (every AO plan needs a paired gated finalize).
---

# Multi-agent slot collision + safe-doc-push hardening — finalize

> **Machine-gated on `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md`** (`depends_on`
>
> - `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 4 of the parent doc's remaining
>   todos are `done`.

## Todos

- [x] ✅ [REVIEW] P2. **DONE 2026-08-09 (slot-4, review craft)** — independently re-verified (not the shipping worker's
      claim trusted): built a fresh sandboxed bare-repo + 2-clone rig, replayed the exact collision shape (clone A
      stages an archival `git mv doc.md archive/doc.md`; clone B concurrently commits+pushes a CONTENT edit to the
      rename source `doc.md`, forcing clone A's `safe-doc-push.sh` into the
      `merge-pull can't fast-forward -> rebase+autostash` path). Against the CURRENT (patched, `f76a03a99`) script:
      `reassert_renames()` fired ("re-staging deletion of rename source"), and the resulting commit's
      `git ls-tree -r HEAD` showed the doc at exactly ONE path (`archive/doc.md`), correctly rename-detected
      (`git show -M HEAD` prints a clean `rename from`/`rename to`), content correctly carrying BOTH the rename and
      clone B's concurrent edit. **Negative control**: re-ran the identical scenario from a fresh rig against the
      PRE-FIX script (`f76a03a99~1`) — it reproduced the doc's own reported symptom exactly, `git ls-tree -r HEAD`
      showing the doc at BOTH paths (`doc.md` and `archive/doc.md`, same blob). Confirms the fix's done-when criterion
      holds and that the corruption is real absent the fix. Verification-only (sandboxed, no repo code changed). Repo:
      unified-trading-pm.
- [x] ✅ [REVIEW] P2. **DONE 2026-08-09 (slot-9, review craft)** — no real multi-session collision (and therefore no
      warning firing) has occurred since deploy; stated reason below, not a live-observed event, per the todo's own
      accepted done-when. Evidence: (1) deploy timestamps — heartbeat mechanism `f75e752d80` 2026-08-08 17:00 UTC,
      SessionStart hook `8a57bc9f15` 2026-08-08 21:58 UTC, so only ~14-15h of exposure existed at review time
      (2026-08-09 ~12:20 UTC). (2) Live census of every currently-active `.tabs/<N>` slot's `claude` processes
      (`/proc/<pid>/cwd` scan, same technique the hook itself uses) found several slots with >1 matching PID, but
      ancestry-walked every one back to PPid — all were subprocess children (Bash-tool shells, backgrounded commands) of
      a SINGLE top-level `claude` process, not a second competing session; zero genuine concurrent-occupancy collisions
      exist right now. (3) `.agent-claim` mtimes across live slots (checked 2,3,8,12,14,16) are all within the last ~5
      min of review time, confirming the underlying heartbeat liveness signal candidate-fix-1 depends on is itself
      actively working — the mechanism has a live pulse even though it hasn't had a real collision to react to. (4)
      Searched the orchestrator `/api/activity` feed and local session-transcript storage
      (`~/.claude-configs/*/projects/`) for the hook's literal `"SLOT COLLISION WARNING"` output string — no hits.
      **Caveat worth flagging (not a blocking gap for this todo)**: the SessionStart hook is architecturally
      client-side-only — it returns `hookSpecificOutput.additionalContext` into the _new_ session's own transcript and
      never POSTs to the orchestrator, so a real firing would only ever be discoverable by reading that one session's
      own transcript, not centrally. Absent a fleet-wide transcript grep (not attempted — multi-GB per slot, out of
      scope for this verification), "no evidence found" is a bounded-effort negative, consistent with (but not proof
      beyond) the low-collision-rate conclusion. The original incident's own collision rate ("3 collisions in ~15 min")
      was a specific stress scenario (up to 6 concurrent bare `claude` processes in one slot), not the steady-state
      condition — one clean day post-deploy with zero observed collisions is itself informative of a low baseline rate,
      per the todo's own accepted done-when.
- [ ] [DOCS] P2. **Archive the parent doc per the 6-step ritual, and only then.** Confirm zero open `- [ ]` todos
      remain; add the archival banner + set `status: complete`; grep the corpus for
      `multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01` and repoint every referrer (including
      `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15.md`, which explicitly defers its own mechanism
      build to this doc); clear any lock if set. Then physically move the parent doc under `plans/archive/2026_08/`.
      **Done when**: `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci --no-regen` is 0 hard,
      `check_reference_paths.py` shows no NEW dangling reference above its baseline, and
      `regenerate_active_plan_inventory.py` reports 0 orphans for this doc. Repo: unified-trading-pm.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (6-step ritual) ·
`/codex/05-infrastructure/per-tab-worktrees.md` · `plans/PLAN_FORMAT.md` · `plans/active/task_template.md` §4
(finalize-plan-coverage rule)

## Progress Log

- **2026-08-08**: Drafted alongside the parent doc's `na-eligibility-audit round7 RECLASSIFY` flip from
  `assigned_vm: NA` to `planning`. `status: active` immediately (not `draft`) — machine-held from actually dispatching
  via `depends_on` + `gate_on_depends: true` until the parent doc's 4 remaining todos are done.
- **2026-08-09 (slot-4, review craft)**: Flipped the rename-corruption verification todo (above) — independently
  reproduced the exact forced-retry collision shape in a fresh sandboxed bare-repo + 2-clone rig (not reused state, not
  the shipping worker's own claim trusted). Patched script (`f76a03a99`): single final path, clean rename detected,
  content correctly merged. Pre-fix script (`f76a03a99~1`), same scenario replayed from scratch as a negative control:
  doc landed at both paths, reproducing the original symptom exactly. 2 todos remain open (`.agent-claim`/session-start
  collision-frequency confirmation; the 6-step archival) — doc stays `status: active`.
- **2026-08-09 (slot-9, review craft)**: Flipped the `.agent-claim` heartbeat + session-start collision-warning
  verification todo (above) — no real collision has occurred in the ~14-15h since deploy (checked live process census
  across every active slot, `.agent-claim` heartbeat freshness, the orchestrator activity feed, and local
  session-transcript storage for the hook's warning string; zero hits). Concluded per the todo's own accepted done-when:
  a stated, evidence-backed reason none has occurred is valid closure, not a gap. Flagged one non-blocking caveat
  inline: the hook is client-side-only (no server telemetry), so a future firing is only discoverable in that session's
  own transcript — informational, not actioned as a new todo (out of this plan's scope). 1 todo remains open (the 6-step
  archival, `[DOCS]`) — doc stays `status: active`.
