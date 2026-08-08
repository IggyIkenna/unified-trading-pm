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
author: unknown
parent_epic: agent_operating_framework_master
priority: P1
source:
  "operator directive 2026-07-30 — explicitly deferred to the operator's next session ('we can proceed to the rest of
  the work which is ensuring agents read that context file list before continuing to start the plan'). Recovered
  2026-07-30 from an orphaned autostash (stash@{13}/{14}/{15}/{21} in the .tabs/1 unified-trading-pm clone) that never
  landed as a real commit — surfaced by a stash-pile audit (unified_trading_pm_stash_pile_accumulation_2026_07_26.md);
  the related: link to the now-nonexistent context_scope_frontmatter_and_scout_skill_2026_07_30.md plan doc was
  repointed to the shipped cursor-configs/skills/context-scout/SKILL.md — everything else recovered verbatim."
assigned_vm: planning
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

- [x] ✅ [INFRA] P1. **DECIDED — operator ruling 2026-08-08** (ao round-5 apply session, item 6 —
      /plans/active/issues/ao_round5_apply_session_operator_qa_index_2026_08_08.md): "AO-dispatched plan (operator
      general preference noted: default to AO-dispatched plans going forward when this LOCAL-vs-AO framing recurs).
      Mechanism choice itself not specified — use engineering judgment among task-brief rendering / RULES.md STEP0 /
      QG-style gate." Track decided: AO-dispatched. Mechanism chosen (engineering judgment): **option (b), worker
      boot/`agents/RULES.md` STEP 0/1 instructing the worker to read its plan's `context_scope` before starting** — not
      (a) task-brief rendering (a fleet-wide mechanical change to `regen_backlog_from_plan.py`'s task-brief output
      touches every dispatched task's brief shape at once, the exact "gate stricter than what the whole fleet already
      passes" blast-radius `AUTONOMOUS_AGENT_RULES.md` rule 11 warns about, and is the highest-blast-radius of the 3
      options for zero extra enforcement benefit over (b)), and not (c) a QG-style first-tool-call gate (needs new
      tool-call observability plumbing that doesn't exist yet — heaviest option, no evidence (b) is insufficient first).
      (b) is cheap, reversible (a RULES.md line, not a backend/DB change), and mirrors this exact codebase's own
      existing convention — `agents/main.md`/`agents/review.md` STEP 2A/2B already carry mechanical "for each X, do Y"
      instructions workers are held to; adding a STEP 0 "read your plan's `context_scope` entries before touching any
      todo" is the same pattern, not a new one. Design + author the AO-dispatched plan covering: the RULES.md STEP 0
      wording, the blast-radius verification (confirm every currently-dispatchable plan/issue has a real, fresh
      `context_scope` before flipping this on — per design question 2, re-run `generate_context_scope_inventory.py`
      first), and a bounded rollout (pilot on one role, e.g. `backend_engineer`, before fleet-wide across all roles). If
      (b) alone proves insufficient in practice (workers still skip the read), escalate to (c) as a follow-up — not a
      reason to hold this off now. Source: this issue doc.
- [ ] [INFRA] P2. **Ship the decided mechanism** — add a STEP 0 instruction to `unified-trading-pm/agents/RULES.md`
      telling a worker to read its plan/issue's `context_scope` entries (when present) before starting any todo, per the
      2026-08-08 operator ruling (option (b), see the checked todo above). Then run
      `scripts/plan-hygiene/generate_context_scope_inventory.py` fresh and confirm the currently-dispatchable
      (`assigned_vm: planning`, active/open) corpus has real, non-stale `context_scope` coverage before treating this as
      safely fleet-wide (last measured 2026-08-01: only 222/647 `UP_TO_DATE`, ~34% — almost certainly still
      majority-uncovered; re-measure, don't assume it closed the gap). This is the actual, currently-open implementation
      step the checked todo above never executed (see Progress Log 2026-08-08 slot-16 note).
- [ ] [INFRA] P2. Once the mechanism above ships, re-run the `context-scout` skill's freshness check across the corpus
      once more immediately before flipping enforcement on, to catch any doc whose `context_scope` drifted stale in the
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
- **context-scout 2026-08-03**: reviewed, still accurate — refreshed marker (4 entries).
- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, valid — re-affirmed. Todo 1 still requires an
  operator pick among the 3 named consumption-mechanism design options plus the ask-before-creating LOCAL-vs-AO track
  call; todo 2 stays gated behind it. Independently cross-validated: the same-day sibling `/ag-closeout-audit ao` batch6
  run (`ao_satellite_ao_dispatch_batch6_2026_08_04.md`) also declined this doc as operator-gated. No content drift.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (4 entries), unchanged.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (4 entries), unchanged — still exactly matches
  this doc's own "Codex SSOTs" list; both todos remain operator-gated design/track calls, nothing new to cite.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **na-eligibility-audit 2026-08-07** (ao tranche, batch3of3): KEEP-NA, valid — re-verified; both open items remain
  operator-gated: todo 1 needs an operator pick among 3 named consumption-mechanism design options plus the
  ask-before-creating LOCAL-vs-AO track call, todo 2 stays gated behind it. Unchanged since the 2026-08-06 marker.
- **2026-08-08 (ao round-5 operator Q&A apply session, item 6)**: operator ruling — track: AO-dispatched (+ general
  preference recorded to default to AO-dispatched when this LOCAL-vs-AO framing recurs, applied to item 5's sibling doc
  too); mechanism: engineering judgment. Chose option (b) (worker boot/`RULES.md` STEP 0 instruction) over (a)
  task-brief rendering (highest blast-radius, touches every dispatched task fleet-wide for no extra benefit over (b))
  and (c) a QG-style gate (needs new observability plumbing, no evidence (b) is insufficient first). Flipped
  `assigned_vm: NA` → `planning` in place (this doc's `execution_scope` was already `orchestrator-agent`, an
  inconsistent combo now corrected) — per this corpus's established convention (`task_template.md` §1: an `assigned_vm`
  reclassification "happens in place," no separate wrapping plan doc needed) rather than authoring a fresh 10-100-todo
  AO plan around a 2-todo scope. Todo 1 closed (design resolved); todo 2 (freshness re-check before flip-on) stays open,
  now dispatch-eligible directly from this doc.
- **2026-08-08 (slot 16)**: dispatched the (then-only) open todo ("once the mechanism ships, re-run..."), but it was not
  actually actionable — grep-verified `agents/RULES.md` has no `context_scope` mention and no new AO plan/commit
  implementing the STEP 0 instruction exists, so the mechanism the todo depends on was never shipped; only the DESIGN
  decision (the checked todo above) was made. Attempted the blast-radius precondition check
  (`generate_context_scope_inventory.py`) directly on this host — it did not complete within 2 minutes (per-doc
  `git log` subprocess over ~650 docs is slow, not a memory issue; no orphan process left running, confirmed via
  `pgrep`). Falling back to the last real measurement cited above (2026-08-01: 222/647 `UP_TO_DATE`, ~34%) is enough on
  its own to show flipping enforcement on now would be premature regardless of whether the RULES.md line ships. Split
  the remaining work into two explicit todos: actually ship the STEP 0 line + re-verify blast-radius coverage (new),
  then the original freshness re-check (unchanged, now correctly gated behind the new one). Skipping this task — the
  original todo still isn't actionable — so the dispatcher can hand out the newly-split, genuinely-ready implementation
  todo instead.
