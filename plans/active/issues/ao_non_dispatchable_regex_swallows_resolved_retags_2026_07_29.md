---
doc_type: issue
title:
  "regen_backlog_from_plan.py's _NON_DISPATCHABLE_RE silently swallows already-ruled todos whose resolution note
  restates the old BLOCKED-* marker in past tense — 27 confirmed cases invisible to AO right now"
summary:
  "Operator question 2026-07-29 -- will orchestrator/workers understand the retagged form vs the canonical tag id, or
  hit the same confusion during a manual corpus grep. Verified against the real parser
  (agent-orchestrator/server/regen_backlog_from_plan.py), not just theorized. Two distinct markers exist and only ONE is
  correctly guarded -- (1) the [OPERATOR] bracket tag: _OPERATOR_TAG_PREFIX_RE anchors to the todo's leading [TAG] P<N>.
  cluster only, so a todo's prose mentioning [OPERATOR] while explaining it is NOT gated (e.g. Retagged from
  [OPERATOR]... RULED) does NOT falsely re-gate it -- confirmed correct, and the code comment at line ~101-106
  explicitly names this exact scenario as the reason the anchor exists. (2) the BLOCKED-CREDENTIALS /
  BLOCKED-OPERATOR-DECISION markers: _NON_DISPATCHABLE_RE.search(todo_block) scans the ENTIRE checkbox + continuation
  block with NO equivalent guard. When this session's 2026-07-28 gate-cleanup/decision-apply pass resolved a todo and
  phrased the resolution note as 'was BLOCKED-OPERATOR-DECISION' / 'no longer BLOCKED-OPERATOR-DECISION' / 'retagged
  from BLOCKED-CREDENTIALS' (restating the literal old marker string in past tense, which reads as resolved to a human),
  the regex still matches on the bare substring and _parse_open_todos drops the todo from the backlog ENTIRELY -- unlike
  [OPERATOR]-tagged todos (which are still ingested as operator_gated=true, visible in the dashboard and surfaced as a
  blocked-queue entry), a BLOCKED-* match is excluded before a BacklogTask is ever created. The todo is not
  deprioritized: it is invisible to AO, the dashboard, and every worker, indefinitely, until someone manually re-reads
  the plan file. Corpus-wide replay of the real regexes across every open todo in plans/active found 2,242 open todos
  total, 93 excluded via the BLOCKED-* path, and 27 of those (across 21 files) also contain RETAGGED/RULED/RESOLVED
  language in the same block -- almost certainly already-actioned-and-ready-to-work todos AO can never see. Full detail
  in the body."
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, backlog-dispatch, regex-parsing, operator-gate-retag, dispatch-correctness, false-exclusion]
related:
  [
    /plans/active/infra_capture_and_devops_leftovers_2026_07_06.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md,
  ]
created: 2026-07-29
priority: P1
parent_epic: agent_operating_framework_master
source:
  "Operator question 2026-07-29 (interactive session), verified against
  agent-orchestrator/server/regen_backlog_from_plan.py"
resolved_by:
locked_by:
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# `_NON_DISPATCHABLE_RE` swallows already-ruled todos that restate the old `BLOCKED-*` marker in past tense

## Evidence (reproduced 2026-07-29)

Confirmed real match on the actual compiled regex from `agent-orchestrator/server/regen_backlog_from_plan.py` (not a
hand-approximation) against real file content:

```
plans/active/infra_capture_and_devops_leftovers_2026_07_06.md:70
  - [ ] [DATA] P1. **RETAGGED 2026-07-28 (was `🚧 BLOCKED-OPERATOR-DECISION`) — RULED, see the 2026-07-28 note
        appended at the end of this task's history below.** Register + launch the ASTER live connector — ...
  _NON_DISPATCHABLE_RE.search() -> MATCH "BLOCKED-OPERATOR-DECISION" -> todo EXCLUDED, never ingested
```

Contrast with the correctly-handled `[OPERATOR]`-tag case (same file family, same 2026-07-28 pass):

```
plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md:395
  - [ ] [DATA] P2. **Retagged from `[OPERATOR]` (2026-07-28 gate-cleanup pass)** — the operator ruling below is
        the standing approval this todo needs...
  _OPERATOR_TAG_PREFIX_RE.match(description) -> "[DATA] P2. " (leading cluster only) -> "[OPERATOR]" NOT in it
  -> operator_gated=False -> todo correctly ingested as a normal dispatchable task
```

Corpus-wide replication (`_parse_open_todos` logic, all of `plans/active/**/*.md`, 2,242 open todos):

| Metric                                                                                   | Count  |
| ---------------------------------------------------------------------------------------- | ------ |
| Total open (`- [ ]`) todos                                                               | 2,242  |
| Excluded as non-dispatchable (any `BLOCKED-*`/stretch marker in block)                   | 93     |
| Of those, block ALSO contains RETAGGED/RULED/RESOLVED language (suspect false-exclusion) | **27** |

The 27 span 21 files across cefi/defi/tradfi/sports/prediction/cross-cutting — this is not localized to one AG's retag
pass; it's a structural gap in the parser that will recur every time a `BLOCKED-*` marker is resolved by restating it in
past tense rather than deleting it outright.

## Why this matters

- `BLOCKED-*` exclusion ≠ `[OPERATOR]`-tag exclusion. An `[OPERATOR]`-tagged todo stays visible (dashboard + operator
  blocked-queue). A `BLOCKED-*`-matched todo is dropped **before a `BacklogTask` object is even constructed** — it does
  not appear anywhere in AO, not even as a gated/blocked item. The only way to discover one is a manual full-corpus grep
  of the plan files themselves (which is how this was found).
- Every one of the 27 already went through an operator ruling. The operator's decision is real and recorded; the work is
  genuinely ready. It just cannot reach a worker through the normal backlog path.
- The gap will keep recurring: nothing in the retag convention (CLAUDE.md's "the moment an `[OPERATOR]`/
  `BLOCKED-OPERATOR` tag resolves, retag to the reflecting tag in the SAME edit") currently says the literal marker
  substring must be _removed_, not _restated in past tense_ — and "was `BLOCKED-X`" reads as perfectly resolved to a
  human reviewer, which is exactly why it wasn't caught until this session's parser-level verification.

## Todos

- [ ] [DATA] P1. **Rephrase the 27 confirmed-affected resolution notes to drop the literal `BLOCKED-CREDENTIALS`/
      `BLOCKED-OPERATOR-DECISION`/`BLOCKED-OPERATOR` substring** (keep the same meaning — e.g. "previously required an
      operator decision, now resolved" instead of "was `BLOCKED-OPERATOR-DECISION`") so these 27 todos become
      immediately dispatchable. Safe, mechanical, no design judgment — confirm each is genuinely resolved (not a false
      positive from this heuristic) before editing. File list: this doc's Evidence section has 3; re-run the corpus-wide
      script above for the full 27/21-file list.
- [ ] [OPERATOR] P1. **Decide the structural fix for `agent-orchestrator/server/regen_backlog_from_plan.py`'s
      `_NON_DISPATCHABLE_RE`** — pick between: (a) add a resolution-language exclusion (negative lookbehind/context
      check for "was", "no longer", "retagged from", "auto-resolved... retagged from" immediately around the marker —
      mirrors the existing `_OPERATOR_TAG_PREFIX_RE` guard, but prose-heuristic regexes on free text risk false
      negatives the other way); (b) codify a hard convention instead — retag workflows/agents MUST NEVER restate the
      literal `BLOCKED-*` token in a resolved todo, full stop (simpler, zero regex risk, but relies on discipline
      instead of enforcement); (c) both — convention as the primary fix, regex guard as defense-in-depth. Needs a design
      call + `agent-orchestrator` QG/tests if (a)/(c) chosen — not a mechanical todo.
- [ ] [DOCS] P2. _*If (b) or (c) above is chosen, add the "never restate the literal BLOCKED-* token past-tense" rule to
      CLAUDE.md's existing resolve-and-retag hard rule_* (Governance + safety HARD RULES § Findings triage) so future
      retag passes don't reintroduce this.

## Progress Log

- 2026-07-29: Filed. Verified via direct regex replication against the live `regen_backlog_from_plan.py` source (not
  assumed) — see Evidence. Corpus-wide count is a point-in-time measurement on a fast-moving branch; re-run before
  treating the 27/21 figures as current beyond this session.
