---
doc_type: codex-ssot
title: Plan Completion + Archival Discipline
summary:
  SSOT for two recurring observed failures — (1) a plan whose every todo is checked stays active indefinitely instead of
  being archived immediately, polluting the active corpus (part of why `/ag-closeout-audit`, `/plan-vintage-audit`, and
  `/na-eligibility-audit` exist); (2) a follow-up/deferred action gets written as PROSE (a "next steps" note, a Progress
  Log aside, a chat summary) instead of a canonical `- [ ]` todo, invisible to every mechanical hygiene/backlog check.
  States the archive-immediately rule + the 6-step ritual, and the todos-not-prose rule.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, archival, orchestrator, frontmatter]
related:
  [
    /codex/12-agent-workflow/plan-hygiene.md,
    /codex/12-agent-workflow/canonical-plan-flow.md,
    /codex/12-agent-workflow/pre-task-plan-conflict-check.md,
    plans/PLAN_FORMAT.md,
  ]
created: 2026-07-28
authoritative_for: [plan archival-when-done ritual, todos-not-prose rule]
referenced_by: [CLAUDE.md § "Plans — format + authoring discipline"]
owner:
last_reviewed:
code_refs:
---

# Plan Completion + Archival Discipline

> Operator observation 2026-07-28 (Ikenna): both of the failures below are "happening a lot" — this doc exists so they
> stop being separately re-discovered per plan.

## 1. Archive the moment a plan is genuinely done — don't leave it sitting `active`

A plan with every top-level todo `[x]` and no `locked_by` is DONE. It must be archived in the SAME session/turn that
completes its last todo — not left for a later audit pass to notice. This is precisely the gap `/ag-closeout-audit`,
`/plan-vintage-audit`, and `/na-eligibility-audit` all have to repeatedly clean up; each one existing is evidence this
rule wasn't followed at completion time.

**Locked plans are the one exception, and it's a human-only unlock**: `locked_by:` blocks archival even with all todos
done (see `plans/PLAN_FORMAT.md` § "Plan Locking" for the frontmatter fields and the plan-health-agent's
done/unlocked/no-dependents check). Agents MAY ask a human to unlock a genuinely-complete locked plan ("Plan X is locked
but all todos are done — should I unlock it?") but MUST NEVER unlock autonomously.

**The 6-step archival ritual** (every step required, none optional):

1. Migrate any DEFERRED item into a real tracked `- [ ]` todo somewhere (never let a deferral evaporate with the
   archived plan — see § 2 below on why a prose deferral is itself already a defect).
2. Add the archived-banner + `superseded_by`/pointer per this workspace's archival convention.
3. Run a codex-alignment check — does this plan's completion change or newly establish any contract a codex SSOT should
   reflect? Update the codex doc(s), or stub a new one, before the plan disappears from `plans/active/`.
4. Update `CLAUDE.md`/codex on any genuinely new contract the plan shipped (not just "it happened," but "here's the rule
   going forward").
5. **Update every referrer's path corpus-wide** — grep the whole corpus for the old doc's path and fix each hit (added
   2026-07-23: the prior four steps never actually named this explicitly, so a plan could archive cleanly by its own 4
   steps while every OTHER doc that linked to it silently broke — not a regression to fix, a gap that was simply missing
   from the ritual until then). **If a referrer cites a specific fact or number from the doc being archived (not just
   its path), confirm that fact already lives in a codex SSOT before the archive lands — migrate it there if it doesn't.
   Never just repoint the citation at the archived plan itself**, which quietly turns a plan into the fact's only home
   (near-miss 2026-07-28: a CLAUDE.md bullet citing specific cron-delivery measurements almost got repointed at an
   archived plan instead of confirming the numbers were already recorded in `/codex/04-architecture/ci-alerting.md`,
   where they were).
6. Clear the lock (if one existed) and confirm the move — the doc should now live under `plans/archive/<YYYY_MM>/`, not
   `plans/active/`.

`run_hygiene_sweep.sh` + `regenerate_active_plan_inventory.py` catch a stale-active-but-fully-checked plan on their own
cadence, but that is the SAME "caught later, not at completion time" pattern this doc exists to stop relying on.

## 2. Every follow-up is a canonical `- [ ]` todo — never prose

A "next steps" paragraph, a Progress Log aside that only describes future work in prose, or a chat-summary bullet that
mentions something still to do — none of these are visible to `check_todo_format.sh`, `regen_backlog_from_plan.py`, or
any orphan/hygiene audit. They are invisible follow-ups: real intent that silently never becomes trackable work.

**The rule**: the moment you notice a follow-up/deferred action — while executing a todo, reviewing a plan, or wrapping
a session — write it as a real `- [ ]` [TAG] P<n>. todo in the plan it belongs to (or a new
`plans/active/issues/<slug>_<date>.md` if it fits no existing plan), in the same turn you noticed it. Do not write it as
prose "for later," do not put it only in a chat response, and do not write it to agent memory (memory writes are
separately banned entirely, per `CLAUDE.md`'s memory rules). If you catch yourself typing "we should also…" or "a
follow-up would be…" in prose, stop and add the real todo instead of finishing the sentence.

This is the same principle `plans/active/task_template.md` §3 already states for capturing discoveries mid-plan
("Capture discoveries as plan todos immediately… never auto-memory/chat-summary; every deferral in a summary must
already be a `- [ ]` todo") — this doc exists because that rule, while written down, keeps not being followed in
practice, so it's restated here as its own named failure mode alongside archival, not left as one clause buried in a
plan-authoring template.
