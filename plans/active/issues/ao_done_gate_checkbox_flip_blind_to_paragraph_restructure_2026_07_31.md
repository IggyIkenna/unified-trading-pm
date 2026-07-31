---
doc_type: issue
title:
  agent-orchestrator /done cross-repo checkbox-flip verification (`server/verify.py` Mode 2) fails to recognize a
  genuine `[ ]` → `[x]` transition when the surrounding todo paragraph is substantially reworded in the same commit
summary: >-
  `POST /api/slots/<N>/done` 400'd 4 consecutive times with `reason: "cross_repo_pm_file_touched_no_checkbox_flip"` for
  task `deployment_api_qg_size_gate_debt-007`, despite `unified-trading-pm@81370aa29` genuinely containing a `- [ ] ...`
  → `- [x] ✅ ...` transition for the exact todo the task's `plan_ref` names, committed <1 minute before the first
  `/done` call (well inside any timing window), on a clean pushed tree. Tried both the code-repo sha
  (`deployment-api@2efb2a0`) and the PM-repo flip sha (`81370aa29`) as the `sha` param — same rejection either way, and
  the rejection specifically named whichever sha was passed as "not touching the checkbox", proving the check is running
  a content-diff heuristic against that commit rather than a bare `git log --since` presence check. Root-cause
  hypothesis (not confirmed — no server-side access from a worker slot): the same `_mode2_disposition`/`check_plan_flip`
  family already tracked in `ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md` likely expects a
  narrow, near-single-line diff shape (an isolated `- [ ]` line paired with an adjacent `+ [x]` line) to recognize a
  flip. My commit's diff replaced an 18-line paragraph with 21 lines of reworded text (splitting one combined todo into
  two — required because the todo covered 2 files and only one was actually done, following this SAME doc's own "one
  todo per file... split at dispatch time" convention) — the checkbox transition is genuinely present in the diff, just
  not as an isolated single-line change, and the heuristic apparently doesn't recognize it. This is a DIFFERENT failure
  mode than the previously-fixed git-mv-bundled-with-flip incident (RULES.md's documented recovery: commit the flip
  FIRST as a plain edit, THEN `git mv` separately) — no `git mv` was involved here at all, and I already followed the
  "flip first, restructure separately" discipline (two separate commits: `f901b683f` did the wording/framing changes,
  `81370aa29` did the actual split+flip) — the SECOND commit alone still failed the check.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, done-gate, plan-flip-verification, bug, verify-py]
related:
  [
    /plans/active/issues/ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md,
    /plans/archive/issues/deployment_api_qg_size_gate_debt_2026_07_30.md,
  ]
created: 2026-07-31
priority: P2
parent_epic: orchestrator_master
source:
  "worker, slot 2, hit live while closing out deployment_api_qg_size_gate_debt-007 (breakdowns_core.py decomposition)"
assigned_vm: NA
execution_scope: local-only
estimate_class: research
assigned_role: backend_engineer
resolved_by:
locked_by:
depends_on: []
drift_direction: advance-code
---

# agent-orchestrator's plan-flip checker rejects a genuine `[ ]`→`[x]` transition inside a reworded paragraph

## What I found

Working `deployment_api_qg_size_gate_debt-007` (decompose `breakdowns_core.py`'s 6 oversized methods — a todo shared
with `breakdowns_domain.py`, 8 more methods, not done this dispatch). Shipped the code (`deployment-api@2efb2a0`), then
flipped the plan in two PM commits:

1. `f901b683f` — reworded the existing (still-`[ ]`) todo to a "PARTIAL" framing describing what was done vs. what
   remained, matching the `manifest.py` multi-session precedent already in this same doc.
2. `81370aa29` — realized the `/done` `done_definition` ("Checkbox flipped in plan + code shipped") wants an actual
   transition, and this doc's own na-eligibility-audit note says "one todo per file recommended... split at dispatch
   time" — so I REPLACED the single combined todo with two: the `breakdowns_core.py` one flipped `- [x]` with full
   evidence, `breakdowns_domain.py`'s split off as a fresh `- [ ]`.

`git log --since="10 minutes ago" -- plans/active/issues/deployment_api_qg_size_gate_debt_2026_07_30.md` in the exact
worktree the server checks (`.tabs/2/unified-trading-pm/`) shows both commits, seconds old, on a pushed
(`origin/live-defi-rollout`-matching) tree. `grep -n "2efb2a0"` in the doc confirms the evidence sha is cited in the
flipped line.

`POST /api/slots/2/done` rejected 4 times, same `reason: "cross_repo_pm_file_touched_no_checkbox_flip"` every time:

```
{"task_id": "deployment_api_qg_size_gate_debt-007", "sha": "2efb2a0", ...}
  -> "commit '2efb2a0' does not touch the plan checkbox..."
{"task_id": "deployment_api_qg_size_gate_debt-007", "sha": "2efb2a0", ...} (retry, unchanged)
  -> same
{"task_id": "deployment_api_qg_size_gate_debt-007", "sha": "81370aa29", ...} (PM sha instead)
  -> "commit '81370aa29' does not touch the plan checkbox..."
```

The error message ECHOES BACK whichever `sha` I passed as the one that "does not touch the plan checkbox" — proving the
check resolves a specific commit and diffs IT (not a bare `git log --since` presence scan), and that diff-based check
fails to recognize the transition in `81370aa29`'s diff even though the transition is genuinely there (confirmed by
direct `git diff` inspection — old line `- [ ] ... **PARTIAL — ...` removed, new line `- [x] ✅ ... **DONE ...` added,
for the exact same logical todo).

## Why it matters

This is the SAME `server/verify.py` Mode-2 checker family as
`ao_done_gate_no_carveout_for_red_gate_evidence_only_closure_2026_07_28.md`, but a distinct failure mode: that doc is
about legitimately-not-flipped todos having no accepted disposition; this is about a GENUINELY flipped todo not being
recognized because the surrounding paragraph changed substantially in the same commit (a todo-split, not just a bare
`[ ] -> [x]` toggle). Any worker following this doc's own "split at dispatch time" convention for a multi-file todo — or
any worker doing a genuine reword-while-flipping — hits the same wall. No `git mv` was involved (ruling out the
already-documented, already-fixed git-mv-bundled-with-flip incident), so this is a new variant, not a regression of that
fix.

## Recommended next step

Whoever owns `server/verify.py`'s `check_plan_flip`/`_mode2_disposition` (same owner as the linked P2 doc) should: widen
the flip-recognition diff heuristic to tolerate a `[ ]`→`[x]` transition that isn't an isolated single-line change
(e.g., match on "does the pre-image contain this task's identifying text with `[ ]`, and does the post-image contain the
SAME task's identifying anchor with `[x]`" rather than a strict adjacent-line-pair diff pattern) — or, if the true
mechanism differs from this hypothesis, root-cause via actual `server/verify.py` access (unavailable from a worker slot)
and correct the doc above once known.

## Todos

- [ ] [CODE] P2. Root-cause `server/verify.py`'s Mode-2 flip-recognition diff heuristic against the reproduction above
      (`unified-trading-pm@81370aa29`, task `deployment_api_qg_size_gate_debt-007`) and widen it to recognize a genuine
      `[ ]`→`[x]` transition even when the surrounding paragraph is reworded/split in the same commit. Repo:
      agent-orchestrator.

## Progress Log

- 2026-07-31 (slot-2, worker): Filed after 4 rejected `/done` attempts on genuinely-complete, genuinely-flipped work.
  Did not force a workaround (no blind re-flip, no bypass) — the plan doc's content is correct and the code is shipped;
  only the `/done` signal itself is blocked. Ending session without a clean `/done` per the established precedent for
  orchestrator-side `/done` anomalies (see `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md` for the
  sibling precedent on a different `/done` failure class).
