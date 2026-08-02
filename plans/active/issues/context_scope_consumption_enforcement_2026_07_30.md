---
doc_type: issue
title: "context_scope is written but not yet READ — worker-boot enforcement is unbuilt"
summary:
  "The context-scout skill shipped the context_scope field, backfilled the corpus, and hardened it as required — but
  nothing yet makes a dispatched worker actually READ a doc's context_scope list before starting its todos. Until this
  ships, the field is a well-maintained but unconsumed index: real value (a human or an agent CAN grep it) but not the
  intended context-window/model-tier-downgrade payoff, which needs mechanical enforcement at dispatch/boot time."
status: open
nature: issue
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [context-scope, context-scout, ao-dispatch, worker-boot, follow-up, deferred-by-operator]
related:
  [
    /cursor-configs/skills/context-scout/SKILL.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-07-30
parent_epic: agent_operating_framework_master
priority: P1
source:
  "operator directive 2026-07-30 — explicitly deferred to the operator's next session ('we can proceed to the rest of
  the work which is ensuring agents read that context file list before continuing to start the plan'). Recovered
  2026-07-30 from an orphaned autostash (stash@{13}/{14}/{15}/{21} in the .tabs/1 unified-trading-pm clone) that never
  landed as a real commit — surfaced by a stash-pile audit (unified_trading_pm_stash_pile_accumulation_2026_07_26.md);
  the related: link to the now-nonexistent context_scope_frontmatter_and_scout_skill_2026_07_30.md plan doc was
  repointed to the shipped cursor-configs/skills/context-scout/SKILL.md — everything else recovered verbatim."
assigned_vm: NA
resolved_by:
locked_by:
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/11-project-management/doc-frontmatter-schema.md,
    /cursor-configs/skills/context-scout/SKILL.md,
    /cursor-configs/AUTONOMOUS_AGENT_RULES.md,
  ]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What's true today (corrected 2026-08-01 — see Progress Log)

`context_scope` is a `plans/active/*.md` + `plans/active/issues/*.md` frontmatter field: the minimal, verified list of
codex SSOTs (+ occasional script paths) that doc's remaining work depends on. **It is ELECTIVE, not required, and the
corpus backfill is still in progress** — the two sentences below correct the two false "done" claims this section
previously made (2026-07-30 version), per the data-correctness contradiction filed in
`/plans/archive/issues/ag_closeout_audit_ao_parked_2026_07_31.md` Finding 1.

1. **Field requirement — ELECTIVE (`Req.E`), not required.** Direct read of `scripts/docs/docspec.py` (2026-08-01,
   post-`uv sync`): `FieldSpec("context_scope", Req.E, "free_list")` at line 139 (doc_type `plan`) and line 163
   (doc_type `issue`, both in the same `.tabs/5/unified-trading-pm` clone at HEAD). `check_frontmatter_schema.py` does
   NOT fail PM QG on a missing `context_scope` — only `Req.R`/`Req.C` fields do.
2. **Corpus backfill — in progress, not complete.** A fresh run of
   `.venv/bin/python scripts/plan-hygiene/generate_context_scope_inventory.py` (2026-08-01, this session) reports: **647
   in-scope docs total — 410 `NEVER_SCOUTED`, 15 `STALE`, 222 `UP_TO_DATE`.** That's ~34% covered (`UP_TO_DATE`), not
   "backfilled" — real, ongoing progress (up from the 2026-07-31 measurement of 626 total / 616 `NEVER_SCOUTED` / 10
   `STALE` / 0 `UP_TO_DATE` cited in the parked-findings doc above), driven by the `/context-scout` skill's incremental
   sweeps, but still a majority-uncovered corpus. Re-run the same command at any later date for the current count — do
   not copy either snapshot forward as if it were current.

**What's NOT built**: nothing in the AO dispatch/worker-boot path reads `context_scope` and does anything with it. A
worker picking up a plan's todo today still gets whatever context its boot prompt/role file already gives it —
`context_scope` sits there, correct and greppable, but nothing forces or even suggests a worker open it before starting.
The operator's stated end goal (cut context burned re-discovering rules per task; eventually make smaller/cheaper models
viable for well-scoped work) needs this consumption side, not just the field existing.

## Why this is a separate doc, not folded into the backfill work

The backfill work (shipped as the `context-scout` skill) is a bounded, already-complete unit: ship the field, backfill
the corpus, harden it, ship the maintenance skill. This follow-up is a genuinely different kind of work — it touches the
AO dispatch/boot pipeline (`server/plan_health.py`, `server/routes/`, worker boot prompt rendering, possibly
`agents/RULES.md` itself), which is a live production path serving real dispatched work right now. Bundling it into the
backfill work would either bloat that unit past a clean single-PR scope or force a premature design decision under time
pressure. The operator explicitly named this as "the rest of the work" for a later session, not a same-session scope.

## Open design questions the next session needs to resolve (none of these are answered here — this doc is the trigger, not the design)

1. **Where does the read happen?** Options include: (a) `regen_backlog_from_plan.py` includes a rendered `context_scope`
   block in the task brief it hands the worker (mechanical, always-on, no worker discretion — but changes what every
   dispatched task brief looks like, fleet-wide); (b) the worker's own boot/RULES.md instructs it to read
   `context_scope` as STEP 0/1 before touching the plan (relies on worker compliance, cheap to ship, no backend change);
   (c) a QG-style gate that checks a worker's FIRST few tool calls included reading every path in `context_scope`
   (enforced, but needs new observability plumbing — likely the heaviest option).
2. **Is this fleet-wide or opt-in first?** A fleet-wide mechanical change to task-brief rendering is exactly the kind of
   "gate you make stricter must be one the WHOLE FLEET already passes" class `AUTONOMOUS_AGENT_RULES.md` rule 11 warns
   about — needs a blast-radius check (every currently-dispatchable plan/issue actually HAS a valid, real
   `context_scope` — true as of 2026-07-30's backfill, but verify freshness before flipping this on) before any
   enforcement ships fleet-wide, not "ship and see what breaks."
3. **What does "smaller/cheaper models eventually" actually require beyond this?** The operator's longer-term goal
   (downgrade model tier once tasks are well-scoped by context) likely needs more than just "the worker read the right
   files" — it needs a way to measure whether a task's context_scope + role boot prompt was SUFFICIENT (no mid-task
   re-discovery/backtracking), which this doc does not attempt to design. Flag as a question for that session, not a
   decision made here.

## Next steps (todos — scope THIS specific follow-up; do not expand beyond what's listed)

- [ ] [INFRA] P1. Design + author a proper plan (LOCAL or AO-dispatched per the ask-before-creating HARD RULE — ask the
      operator which track) covering: the chosen consumption mechanism (design question 1 above), the blast-radius
      verification (design question 2), and a bounded rollout (pilot on one role/plan family before fleet-wide). Source:
      this issue doc.
- [ ] [INFRA] P2. Once the mechanism ships, re-run the `context-scout` skill's freshness check across the corpus once
      more immediately before flipping enforcement on, to catch any doc whose `context_scope` drifted stale in the
      interim.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch/worker-boot architecture this
  follow-up would modify
- `/codex/11-project-management/doc-frontmatter-schema.md` — the `context_scope` field this consumes
- `/cursor-configs/skills/context-scout/SKILL.md` — the shipped producer side (field + backfill + maintenance skill)
- `cursor-configs/AUTONOMOUS_AGENT_RULES.md` rule 11 — the blast-radius-before-tightening-a-gate discipline this
  follow-up's design question 2 must satisfy before any fleet-wide flip

## Progress Log

- **2026-07-30**: recovered from an orphaned autostash during a stash-pile audit of `.tabs/1/unified-trading-pm`
  (`unified_trading_pm_stash_pile_accumulation_2026_07_26.md`). The doc was created 2026-07-30 in that clone but never
  committed — 4 stash entries (stash@{13}/{14}/{15}/{21}) all carried an identical copy, none reapplied cleanly. Filed
  here verbatim (only the dead `related:` link to the never-committed producer-side plan doc was repointed to the
  shipped `context-scout` skill) so the 4 stash entries can now be safely dropped without losing this tracked gap.
- **na-eligibility-audit 2026-07-31**: KEEP-NA, valid (infra tranche, dispatch agt-676f1e) — todo 1 explicitly requires
  an operator pick among 3 named design options (where the consumption read happens) plus a LOCAL-vs-AO-dispatched track
  decision per the ask-before-creating HARD RULE; todo 2 is gated behind todo 1 shipping. Genuine judgment call, not a
  mis-defaulted mechanical task. No other action.
- **2026-08-01** (slot 5, task `ag_closeout_audit_ao_parked-001`): corrected the "What's true today" section per
  `/plans/archive/issues/ag_closeout_audit_ao_parked_2026_07_31.md` Finding 1 — the "now REQUIRED" and "backfilled the
  corpus" claims were false as of 2026-07-31 and remain false today. Verified fresh: `docspec.py` still specs
  `context_scope` as `Req.E` (elective) for both `plan` (line 139) and `issue` (line 163) doc_types; a fresh
  `generate_context_scope_inventory.py` run reports 647 in-scope docs / 410 `NEVER_SCOUTED` / 15 `STALE` / 222
  `UP_TO_DATE` (up from 626/616/10/0 on 2026-07-31 — real progress, still majority-uncovered). This is a prose
  correction only; none of this doc's own open todos (design + rollout, both operator-gated) change.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — 2026-07-31 verdict re-affirmed. Todo
  1 still requires the operator to pick among 3 named design options (where the `context_scope` read happens: task-brief
  rendering / RULES.md STEP 0 / a QG-style first-tool-call gate) AND to answer the ask-before-creating HARD RULE's
  LOCAL-vs-AO track question; todo 2 is gated behind todo 1 shipping. In scope this run only because of the 2026-08-01
  prose correction (`307b55bd8`) and the 2026-08-02 retag sweep — neither changed the open todos.
