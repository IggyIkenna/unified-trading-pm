---
doc_type: issue
title:
  A parked backlog task's hand-tune (priority/prereqs gate) was lost after a sibling todo was inserted into the same
  plan doc, causing a wasted redispatch cycle
summary: >-
  `ao_db_lock_storm_and_stuck_shutdown_outage-005/-006` was correctly parked (priority 999 + prereqs.prerequisites gate)
  by slot-15 on 2026-07-30, following the documented recipe exactly (including the 2026-07-12 fix's own lesson: never
  edit the todo's own text, annotate only in the Progress Log). That park held through a live regen tick at the time.
  Later the same day, a genuinely new sibling todo was appended to the SAME plan doc (the "Second, independent
  contributing-latency finding" BACKEND todo, already-shipped/checked). The next regen cycle after that edit minted a
  FRESH id (`-007`) for the still-open REVIEW todo, with `prereqs.prerequisites` reset to `[]` and `priority` reset to
  `50` — the hand-tune did not carry forward, even though the todo's own text was unchanged. This is dispatch-shaped,
  not content-shaped: a park survives an in-place regen tick but not a doc edit that adds/removes a SIBLING todo
  above/around it.
status: open
nature: issue
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, backlog, park, prerequisites, regen, dispatch-thrash]
related:
  [
    /plans/active/issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-30
author: unknown
priority: P2
parent_epic: orchestrator_master
source:
  "slot-8, review — dispatched ao_db_lock_storm_and_stuck_shutdown_outage-007 (the same parked REVIEW todo), found the
  precondition (live systemd unit still carries --reload, confirmed directly via ps on the orchestrator VM) still unmet,
  then found the -005/-006 park itself had silently reverted to a fresh ungated -007 id"
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
context_scope:
  [
    /plans/active/issues/ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md,
    /plans/archive/issues/backlog_regen_drops_handtuned_prereqs_2026_07_12.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
  ]
---

# Backlog park lost across a sibling-todo plan edit — 2026-07-30

## What I found

Direct evidence, all gathered live on the orchestrator VM (`ip-172-31-5-118`, where this session happens to run):

1. **The precondition genuinely still unmet.** `ps` on the running orchestrator process
   (`systemctl status orchestrator.service`) shows the live `ExecStart` STILL includes `--reload --reload-dir server` —
   the `[OPERATOR]` todo (`ao_db_lock_storm_and_stuck_shutdown_outage-004`, "apply `ee98ccb`'s `--reload` removal to the
   live unit") has not been applied. `sudo -n true` still fails with "the 'no new privileges' flag is set" — same
   blocker slot-16 and slot-15 already documented; this session has no more privileged access than they did, despite
   running ON the VM itself.
2. **The park is gone.**
   `grep -n '^- id: ao_db_lock_storm_and_stuck_shutdown_outage' -A 8 agent-orchestrator/data/config/backlog.yaml` (the
   LIVE file, read directly — I have filesystem access on this VM) showed a task id `-007` (not `-005`/`-006`) for the
   still-open `[REVIEW]` todo, with `prereqs.prerequisites: []` and `priority: 50` — slot-15's park (`priority: 999`,
   `prereqs.prerequisites: [ao_orchestrator_reload_removed_live]`) was gone. This produced a wasted redispatch: my
   `/heartbeat` picked up `-007` fresh (as if never checked before), even though the actual state (precondition unmet)
   was already fully known from 3 prior sessions' worth of documentation on the parent issue doc.
3. **Root cause, narrowed but not fully proven.** Between the park (earlier 2026-07-30) and now, a genuinely NEW sibling
   todo was appended to `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md` (the "Second, independent
   contributing-latency finding" `[BACKEND]` todo, itself already shipped+checked the same day). I did NOT trace the
   exact regen code path that reassigns ids, but the timing correlation is exact: the park held through at least one
   regen tick (per slot-15's own verification note) and was gone by the time that sibling todo existed. This is narrower
   than the original `backlog_regen_drops_handtuned_prereqs_2026_07_12` bug (which dropped hand-tunes on an UNCHANGED
   task across a routine regen tick) — **this session's own re-test of the SAME recipe on `-007` survived a real
   `POST /api/backlog/regen` tick cleanly** (verified: `priority: 999` and the prereqs gate were both still present
   immediately after, id unchanged), which rules out a blanket "regen always drops hand-tunes" regression. The gap is
   specifically: **a park does not carry forward across an edit that changes the plan doc's OTHER todos**, even when the
   parked todo's own text is byte-identical.

## Why it matters

- This is the exact "wasteful-not-harmful" thrash class `main`'s 2026-07-25T05:16Z note on the parent doc already
  flagged and the park mechanism exists to bound — but the park's fragility against sibling-todo edits means any active,
  actively-being-worked issue doc (which is precisely where multi-todo, multi-session parks are most likely to be
  needed) is also the most likely to get a sibling todo added mid-park, silently defeating it.
- Each silent revert costs one full worker dispatch cycle re-discovering already-known state (this session's own: ~10
  minutes re-verifying the exact same unmet precondition 3+ prior sessions had already established). At fleet scale this
  compounds.

## Recommended decision

File as its own tracked issue (not folded into the parent doc, which is about the DB-lock/shutdown-hang incident itself,
not the dispatch-tooling gap). Suggested next steps:

## Todos

- [x] ✅ [BACKEND] P2. Trace the exact `regen_backlog_from_plan.py` code path that assigns/reuses task ids across a
      regen cycle when a SIBLING todo (not the parked one itself) is added to/removed from the same plan doc — confirm
      whether id-reuse/hand-tune-carry-forward is keyed on todo TEXT content-hash alone, or also on positional/ordinal
      derivation that a sibling insertion would shift. If positional, that's the root cause; fix by keying hand-tune
      carry-forward on content-hash only (matching how the checkbox-text-edit trap was already fixed for the SAME todo,
      per this doc's `related` link). Add a regression test: park todo A in a 2-todo plan, append a new todo B, regen,
      assert A's id/priority/prereqs survive unchanged. (repo: agent-orchestrator) — agent-orchestrator@727dab3
- [ ] [BACKEND] P3. Consider whether the park mechanism should emit a warning/alert when a parked task's id changes
      across a regen tick (the hand-tune becoming orphaned on the OLD id) — this would make future occurrences
      self-diagnosing instead of requiring a worker to notice the priority/prereqs are missing after the fact. (repo:
      agent-orchestrator)

## Progress Log

- **2026-07-30T12:14Z (slot 8, review)** — Filed while investigating why
  `ao_db_lock_storm_and_stuck_shutdown_outage-007` re-dispatched despite slot-15's documented park on `-005`/`-006`
  earlier the same day. Re-applied the SAME park recipe to `-007` (priority 999,
  `prereqs.prerequisites: [ao_orchestrator_reload_removed_live]`) directly on the live
  `agent-orchestrator/data/config/backlog.yaml` (this session runs on the orchestrator VM with filesystem access) and
  verified it survives BOTH `/api/backlog/reload` AND a real `/api/backlog/regen` tick — the mechanism itself works
  correctly for an in-place re-tune; the gap is specifically that the PRIOR park didn't carry forward across the
  intervening sibling-todo edit. No code shipped this entry (pure diagnosis + a live backlog hand-tune, which is the
  documented sanctioned mechanism, not a code change).

- **2026-07-30T14:20Z (slot 8, backend_engineer)** — Traced todo 1. Read `regen()` / `_reconcile_task_fields()` /
  `_prune_stale()` / `_migrate_parking_state()` in `agent-orchestrator/server/regen_backlog_from_plan.py` end to end:
  the ADD/RECONCILE pass keys an already-derived task's identity purely on `t.brief` (the todo's exact raw checkbox-line
  text) scoped by `t.plan_ref` (`plan_tasks_by_brief: dict[str, BacklogTask]`, built fresh every tick) — a brief match
  reconciles the task IN PLACE (same id; `priority_override` guards `priority`; `prereqs.prerequisites` is never touched
  by reconcile at all) and never falls through to `_make_task_id()`. The orphan/prune path's fallback
  (`_migrate_parking_state`) is likewise content-based: same `plan_ref` + same `_todo_tag_prefix()` + `SequenceMatcher`
  similarity ≥ `_PARKING_MIGRATION_SIMILARITY_THRESHOLD` (0.6) — no ordinal/positional input anywhere in either path.
  **Confirmed empirically, not just by inspection**: added `test_regen_park_survives_sibling_insertion` (parks todo B of
  a 2-todo plan, appends a new todo C after it, regens with `prune_stale=True` matching PlanRegenLoop's production
  default, asserts B's id/priority/prereqs survive 2 ticks) — **passes on current code**. Also hand-verified a THIRD
  variant not written into the suite (sibling inserted BEFORE the parked todo, shifting its list position) — also
  survives, `reconciled=1` in the regen summary confirms the in-place path fired, not a fresh append. **Verdict:
  content-hash-only already, NOT positional** — the specific "sibling insertion breaks the park" mechanism this todo
  asked me to confirm/fix does not reproduce against today's code, so no `regen_backlog_from_plan.py` change was needed;
  the regression test is shipped regardless to lock in the guarantee for the insertion case (previously only covered for
  the sibling _removal_ case, by `test_regen_park_survives_sibling_completion_and_id_shift`, 2026-07-17). **Residual
  open question** (out of this todo's scope — flagging, not fixing): since the mechanism is proven safe against sibling
  insertion, the ORIGINAL `ao_db_lock_storm_and_stuck_shutdown_outage-005/-006→-007` incident's actual trigger remains
  unexplained by this trace. A plausible alternative (unproven): `save_backlog`/ `load_backlog` do a full-file
  read-modify-write with no lock — a hand-edit racing a concurrent `PlanRegenLoop` tick's own load-then-save could
  last-writer-lose the hand-tune independent of any content/position logic. Not chased further here (would be new
  scope); worth a follow-up only if the loss recurs. Shipped: `agent-orchestrator@727dab3` (test only; full local
  `quality-gates.sh` green — 2037 passed, 1 skipped; ruff/basedpyright clean).

- **context-scout 2026-08-01**: populated context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (3 entries, unchanged) — verified all still accurate and
  resolve.
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — first marker on this doc. Sole open
  item is
  `[BACKEND] P3. **Consider whether** the park mechanism should emit a warning/alert when a parked task's id changes across a regen tick`
  — an open design call, not a specified change. Its own todo 1 already disproved the suspected mechanism
  (`test_regen_park_survives_sibling_insertion` passes on current code; matching is content-hash-only, not positional),
  leaving the original incident's trigger unexplained and the alerting question genuinely undecided rather than merely
  unimplemented.
- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, valid — re-affirmed, no content change.
  Cross-validated: the same-day sibling `/ag-closeout-audit ao` batch6 run independently declined this same doc into its
  "too-large/unscoped-design" bucket.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (3 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (3 entries), unchanged.

- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — re-affirmed. Sole open item ([BACKEND] P3, whether the park
  mechanism should emit a warning/alert on id-change) remains an undecided design question, not a specified change; no
  content drift since the last marker.
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — checked against the round7-10 precedent set; none
  apply ("consider whether to build an alerting surface at all" has no stated done-when, a genuine open question, not a
  defaulted judgment call). Corroborated same-day: `/ag-closeout-audit ao` batch12 independently lists this doc under
  genuinely-human-only (4).
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — content unchanged since
  round11. Sole open item ([BACKEND] P3, whether to build a park-id-change alerting surface at all) remains an
  undecided open question with no stated done-when.
