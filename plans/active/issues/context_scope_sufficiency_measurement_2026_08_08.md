---
doc_type: issue
title: "Measure whether context_scope is SUFFICIENT, not just read — precondition for a future model-tier downgrade"
summary:
  "The context_scope consumption mechanism (RULES.md STEP 0) now makes a dispatched worker READ its plan's context_scope
  list, but nothing measures whether that list plus the role boot prompt was actually SUFFICIENT for the task (no
  mid-task re-discovery/backtracking). The operator's longer-term goal — downgrade model tier once tasks are well-scoped
  by context — needs this measurement side; it was explicitly flagged as an open question, not designed, when the
  consumption mechanism shipped."
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [context-scope, context-scout, ao-dispatch, model-tier, follow-up]
related:
  [
    /plans/archive/2026_08/issues/context_scope_consumption_enforcement_2026_07_30.md,
    /cursor-configs/skills/context-scout/SKILL.md,
    /codex/06-coding-standards/model-tier-selection.md,
  ]
created: 2026-08-08
author: slot-22
parent_epic: agent_operating_framework_master
priority: P3
source:
  "Migrated from design question 3 of /plans/archive/2026_08/issues/context_scope_consumption_enforcement_2026_07_30.md
  ('What does smaller/cheaper models eventually actually require beyond this?') at that doc's archival — per the
  plan-completion-and-archival-discipline HARD RULE (never let a deferral evaporate with the archived doc). Genuinely
  open-ended/design judgment call, not a bounded mechanical task — defaults to a human/LOCAL track per the
  dispatch-scope-eligibility rule, not AO-dispatched."
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/06-coding-standards/model-tier-selection.md,
    cursor-configs/skills/context-scout/SKILL.md,
    /plans/archive/2026_08/issues/context_scope_consumption_enforcement_2026_07_30.md,
  ]
---

## What I found

The `context_scope` consumption-enforcement work
(`/plans/archive/2026_08/issues/context_scope_consumption_enforcement_2026_07_30.md`) shipped the READ side (worker boot
STEP 0 instruction) and confirmed corpus coverage (≈34% `UP_TO_DATE` as of 2026-08-08) is too low for any further
fleet-wide enforcement flip. That doc's own design question 3 named a genuinely separate, unresolved need: the
operator's stated end goal is to eventually make smaller/cheaper models viable for well-scoped work, which requires more
than "the worker read the right files" — it needs a way to MEASURE whether a task's `context_scope` + role boot prompt
was sufficient (no mid-task re-discovery, no backtracking to grep for a rule the scope list should have already
surfaced). Nothing measures this today.

## Why it matters

Without a sufficiency signal, there is no evidence-based way to know when it's safe to attempt a model-tier downgrade on
`context_scope`-covered tasks — the downgrade would be a guess, not a measured decision, which is exactly the kind of
ungated tightening `AUTONOMOUS_AGENT_RULES.md` rule 11 warns against (in the inverse direction: loosening a cost lever
without evidence it's safe).

## Recommended decision

Design (in a future session) what "sufficiency" means operationally — candidates include: counting mid-task grep/Read
calls against paths NOT in `context_scope`, or a lightweight post-task self-report — and whether it's cheap enough to
instrument without adding real overhead to every dispatched task. This doc is the trigger, not the design; scope it
properly (likely via `/plan-brainstorm`) before authoring any implementation work.

## Next steps

- [ ] [INFRA] P3. Design + decide how to measure `context_scope`+role-boot-prompt sufficiency for a dispatched task
      (candidate signals: mid-task reads outside `context_scope`, a post-task self-report), and whether/when that
      unlocks a model-tier downgrade experiment. Genuinely open-ended — resolve via `/plan-brainstorm` before any
      implementation todo is authored.

## Codex SSOTs

- `/codex/06-coding-standards/model-tier-selection.md` — the model-tier axis this would eventually inform
- `cursor-configs/skills/context-scout/SKILL.md` — the producer side this measurement would validate
- `/plans/archive/2026_08/issues/context_scope_consumption_enforcement_2026_07_30.md` — the consumption-side work this
  follows up on (archived; source of this doc)

## Progress Log

- **2026-08-08 (slot-22, infra craft)**: filed at archival of the consumption-enforcement doc, migrating its
  design-question-3 prose into a tracked todo per the archival ritual's "never let a deferral evaporate" step.
- **context-scout 2026-08-09**: populated context_scope (3 entries) — mirrors this doc's own "Codex SSOTs" section (a
  genuinely code-free design/proposal doc, no source paths).
- **na-eligibility-audit 2026-08-09 (round9)**: KEEP-NA, valid — first audit pass on this doc. Sole open item is
  explicitly self-flagged "Genuinely open-ended — resolve via `/plan-brainstorm` before any implementation todo is
  authored." No new facts apply.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of the sole open
  item, self-flagged in its own text as 'genuinely open-ended — resolve via /plan-brainstorm before any implementation
  todo is authored.' No concrete spec exists yet. Agrees with round9 (2026-08-09).
