---
doc_type: issue
title: >-
  `prereqs.completed_tasks` gates trust a `done` TaskRow by task_id alone — if an audit flips a checkbox back to `[ ]`,
  the old id's row stays `done` forever and a live gate that still names it stays wrongly satisfied
summary: >
  Investigated in an interactive Claude Code session (operator-directed, `/autonomous`, LOCAL track) answering the
  operator's own question: "what happens if a task marked done is flipped back to undone after an audit — does
  backlog.yaml and the DB update, and does it redispatch?" Confirmed via direct code read (`regen_backlog_from_plan.py`
  + `dispatch.py`) — this is a PROACTIVE finding from investigation, not a report of an observed bad live dispatch.


  **Mechanism (confirmed via code read, not reproduced against a live incident)**: when a todo is checked off, the next
  regen tick correctly drops its `backlog.yaml` entry (the yaml only tracks currently-OPEN todos). If an audit later
  determines the work was NOT actually complete and edits the plan's checkbox back to `- [ ]`, regen mints a BRAND NEW
  task_id for the reopened line on the next tick — the reconcile match in the ADD pass (`plan_tasks_by_brief`,
  `regen_backlog_from_plan.py:1347-1349`) is scoped to whatever is CURRENTLY in `backlog.yaml`, and the old id was
  already pruned the tick it went `done`, so there is no way to reattach the reopened text to its original id. The OLD
  id's `TaskRow` is never touched — `done`/`dispatched` rows are permanent audit history by design (`_prune_stale`, same
  file, filters state.db deletion to `status='queued' AND dispatched_to IS NULL` only) — so it keeps reading
  `status=done` forever, citing whatever `done_sha` the audit later determined was wrong.


  `_completed_task_satisfied` (`server/dispatch.py:636-652`) is the function every dispatch decision calls to check a
  `prereqs.completed_tasks` gate. It trusts ANY `status=done` `TaskRow` by task_id alone — it has no notion of "is this
  id still the current, authoritative representation of the upstream work." For a `gate_on_depends`-wired plan this
  mostly self-heals within one regen cycle: `_wire_gate_on_depends_prereqs` (line 1649) adds the new id to every
  downstream gate the same tick it appears in yaml, and `_scrub_completed_upstream_prereqs` (line 1728) drops the stale
  old id the same tick it's pruned. But `_completed_task_satisfied` ALSO treats an id absent from both yaml and DB as
  satisfied (the 2026-06-29 whole-fleet-idle-block fix, same function) — so the window between "old id scrubbed" and
  "new id wired in" is silently satisfied too, not blocked (up to one ~30-min regen cycle of exposure, same latency
  inherent everywhere else in this eventually-consistent system — not a special new defect on its own). A
  `completed_tasks` reference set OUTSIDE that auto-managed wiring never self-heals at all: grepped every write site of
  `completed_tasks` across `server/` — confirmed `_wire_sequential_prereqs` and `_wire_gate_on_depends_prereqs` (both in
  `regen_backlog_from_plan.py`) are the ONLY writers under the current, convention-following authoring path (no per-todo
  prereq syntax is honoured by regen; CLAUDE.md already bans hand-authoring `completed_tasks` directly) — so this
  narrower, non-self-healing case is currently a convention-violation risk, not an exploitable one via the sanctioned
  authoring path. It remains a real risk if `backlog.yaml` is ever hand-edited against the HARD RULE that bans it, since
  the data model does not technically enforce that ban.
status: resolved
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [orchestrator, backlog, regen_backlog_from_plan, gate_on_depends, dispatch, prereqs, completed_tasks, data-integrity]
related:
  [
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
    /plans/archive/issues/backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md,
    /codex/11-project-management/issue-doc-lifecycle.md,
  ]
created: 2026-07-25
parent_epic: agent_operating_framework_master
priority: P1
source: >-
  Interactive Claude Code session, operator question "what happens if a plan marked done is flipped to undone after
  audit — does backlog.yaml and the DB update and redispatch?", 2026-07-25, followed by operator's explicit "fix this
  properly, file an issue and do it locally the proper way" + `/autonomous`.
assigned_vm: NA
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
last_updated: 2026-07-25
locked_by:
resolved_by: >-
  `scripts/orchestrator/audit_stale_gate_references.py` shipped
  `agent-orchestrator@c7aa640d9ad0ec2927442ff424aabc2d7d6bbfde` (same session) — a new read-only diagnostic mirroring
  `audit_false_done.py`'s established pattern. It finds the exact, mechanically-verifiable case: an orphaned `done` id T
  still named in some LIVE task's `completed_tasks`, AND T's own plan currently has an open todo whose brief hashes
  IDENTICALLY to T's stored `brief_hash` (the same line, un-reworded, just un-checked). Verified against two synthetic
  scenarios before shipping (a reopened-exact-match case correctly flagged `stale_gate_references=1`; a
  genuinely-finished, not-reopened case correctly reported `clean=1`, zero false positives). Full `quality-gates.sh`
  green (1694 passed, 2 skipped, dashboard tsc + vitest green) — the new file lives in `scripts/orchestrator/`, which
  this repo's `quality-gates.sh` does not lint/type-gate (scoped to `server/`+`tests/` only, same as its sibling
  `audit_false_done.py`), so it was additionally verified standalone via `ruff check`/`ruff format --check` (clean)
  ahead of shipping. codex SSOT (`agent-orchestrator-backlog-state-alignment.md`) updated with a new "A `done` task's
  checkbox is flipped back to `[ ]` after an audit" section documenting the mechanism + pointing at the new tool, plus a
  small adjacent fix (the `ORCHESTRATOR_REGEN_PRUNE_STALE` default in that doc's env-var table was documented `false`,
  verified stale against `server/config.py:786`'s actual `default=True` — corrected in the same edit). Read-only tool;
  report-only, no `--fix` mode — a confirmed finding is corrected via `POST /api/backlog/{id}/reopen`-style mutation or
  by re-wiring the affected plan's `depends_on`, never by hand-editing `backlog.yaml`, per the existing anti-pattern
  rule. NOTE: this PM-repo doc + the codex edit were lost once mid-flight (an untracked staged file dropped across a
  `git stash`/ `git pull --rebase --autostash` round-trip in this heavily shared, multi-agent-concurrent PM clone —
  plain `git stash` does not reliably re-stage a brand-new file across a pop, and neither survived several internal
  quickmerge stash cycles) and recreated verbatim from this session's own retained content; the shipped
  agent-orchestrator code was unaffected (that repo's clone had no such concurrent stash contention).
depends_on: []
---

# `prereqs.completed_tasks` gates trust a `done` TaskRow by task_id alone — an audit-driven checkbox un-flip can leave a stale gate

## What I found

Traced the full lifecycle of "a done task's checkbox is later flipped back to `[ ]`" through
`agent-orchestrator/server/regen_backlog_from_plan.py` and `server/dispatch.py`, prompted by the operator's own question
about this exact scenario. No live incident triggered this — it is a proactive finding from reading the dispatch-gating
code end to end, the same way `backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md` (this doc's closest
precedent, also `agent_operating_framework_master`) found and closed the sibling "false `done` never gets un-flipped"
defect class.

**The chain**:

1. A todo is checked off (correctly — the hard-409 `check_plan_flip` gate, shipped in the precedent doc above, requires
   the cited commit to actually flip THIS todo's checkbox). Its `backlog.yaml` entry is pruned the next regen tick (the
   yaml only ever tracks currently-open todos). Its `state.db` `TaskRow` stays `status=done` forever — deliberate,
   documented behavior ("done rows are audit history, never deleted").
2. An audit later determines the work was not actually complete and edits the plan file's checkbox back to `- [ ]`.
3. Next regen tick: the reopened line is parsed as a NEW open todo. The reconcile match (`plan_tasks_by_brief`, built
   from `backlog.tasks` — i.e. whatever is CURRENTLY in the yaml) does not contain the old id (pruned in step 1), so the
   line cannot reattach to it. A fresh task_id is minted (`_make_task_id`,
   `next_index = max(existing ids for this slug in the CURRENT yaml) + 1`) and queued like any other new todo — this
   part IS the intended, correct redispatch, confirmed working as designed.
4. The OLD id's row is never touched by any of this. It permanently reads `status=done`.
5. `_completed_task_satisfied` (`dispatch.py:636`), called by every `_prereqs_met`/`explain_blocked` check, resolves ANY
   `completed_tasks` entry naming the old id as satisfied purely from `row.status == "done"` — no check of whether that
   id is still the CURRENT representation of the upstream unit of work.

## Why it matters

If some OTHER task's `prereqs.completed_tasks` still names the OLD id at the moment its dispatch is evaluated, that gate
reads as satisfied even though the actual upstream work is back in flight under a new id — the same class of
premature-dispatch risk the precedent doc's `sports_travel_calculator_tz_aware_kickoff_crash-001` incident demonstrated
live (38 consecutive dispatches on a false-`done` upstream). The blast radius here is narrower than that incident (this
workspace's `gate_on_depends` machinery mostly self-heals within one regen cycle, and the fully unguarded case requires
violating the "no hand-authored `completed_tasks`" convention against the current data model), but the underlying trust
gap in `_completed_task_satisfied` is the same shape, and nothing previously existed to detect it after the fact.

## The fix

Built `scripts/orchestrator/audit_stale_gate_references.py` (`agent-orchestrator@c7aa640`) rather than changing
`_completed_task_satisfied`'s live dispatch-path behavior — per the workspace's own rule-11 caution ("verify blast
radius before tightening a gate... a gate you make stricter must be one the whole fleet already passes, prove it
first"), making the runtime check content-identity-aware would need proof against the live fleet's actual gate graph
before shipping, which is out of scope for a single interactive session's proactive finding with no live incident behind
it. A read-only audit tool (mirroring `audit_false_done.py`'s already-accepted pattern for the sibling defect class)
closes the observability gap with zero blast radius: it makes the exact, mechanically-provable case ("a live gate
references an orphaned `done` id whose own plan shows the identical line reopened") visible for an operator/agent to act
on, the same way `audit_false_done.py` already does for the false-`done`-without-a-flip class.

Known limitation (documented in the tool's own docstring, trap 5): exact `brief_hash` match only. A reopened todo that
was ALSO reworded on the same edit is a real reopening this tool cannot detect — no plaintext brief survives an orphaned
row to fuzzy-match against (the same gap `_migrate_parking_state`'s docstring already explains for why a text-similarity
guess is deliberately not attempted without the original text). A clean run is evidence of "no exact-reopen collision
found," not "no possible drift."

## Todos

- [x] ✅ [INFRA] P1. **Root-caused** the mechanism end to end via direct code read of `regen_backlog_from_plan.py`
      (ADD-pass reconcile scoping, `_prune_stale`, `_wire_gate_on_depends_prereqs`, `_scrub_completed_upstream_prereqs`)
      and `dispatch.py` (`_completed_task_satisfied`). Confirmed `completed_tasks` has exactly two writers workspace-
      wide (`_wire_sequential_prereqs`, `_wire_gate_on_depends_prereqs`), both self-healing, via
      `grep -rn "completed_tasks\s*=\|completed_tasks\.\(extend\|append\|remove\)\|completed_tasks\[:\]" server/` — zero
      hits outside `regen_backlog_from_plan.py`. (repo: agent-orchestrator) — interactive session, 2026-07-25.
- [x] ✅ [INFRA] P1. **Built + shipped `audit_stale_gate_references.py`** — read-only diagnostic, mirrors
      `audit_false_done.py`'s conventions (traps 1-4 identical: read plans from the ref not the working tree, read
      state.db from the live VM not a snapshot, resolve `plan_ref` via `verify._plan_ref_candidates` for issue-doc-
      sourced tasks, treat `brief_hash IS NULL` as unauditable not clean). Verified against two synthetic scenarios
      (built a throwaway git repo + sqlite db + backlog.yaml in the scratchpad — no destructive command used, per the
      workspace's `rm -rf` guardrail): a reopened-exact-match case correctly flagged (`stale_gate_references: 1`, exit
      code 1); a genuinely-finished not-reopened case, WITH an unrelated open todo present in the same plan to guard
      against cross-matching, correctly reported clean (`clean: 1`, exit code 0). `ruff check`/`ruff format     --check`
      clean (this repo's `quality-gates.sh` scopes ruff/basedpyright/pytest to `server/`+`tests/` only — confirmed via
      direct read of `scripts/quality-gates.sh` — so `scripts/orchestrator/*.py`, same as its sibling, is outside the
      gate; checked it by hand anyway). Full `quality-gates.sh` still run and green (1694 passed, 2 skipped; dashboard
      tsc + vitest green) to confirm nothing else broke. Shipped via `quickmerge --agent --files`. (repo:
      agent-orchestrator) — agent-orchestrator@c7aa640d9ad0ec2927442ff424aabc2d7d6bbfde, interactive session,
      2026-07-25.
- [x] ✅ [INFRA] P2. **Updated the codex SSOT** (`agent-orchestrator-backlog-state-alignment.md`) with a new section ("A
      `done` task's checkbox is flipped back to `[ ]` after an audit — does dispatch notice?") documenting the
      mechanism, the residual risk, and pointing at the new tool + this issue doc. Also corrected an adjacent, already
      -verified stale fact found while in the doc: the `ORCHESTRATOR_REGEN_PRUNE_STALE` env-var table row documented the
      default as `false`; `server/config.py:786` actually defaults it `True` — fixed in the same edit,
      `     last_reviewed` bumped to 2026-07-25. (repo: unified-trading-pm) — interactive session, 2026-07-25.
- [x] ✅ [INFRA] P3. **Filed + resolved this issue doc directly** (per
      `codex/11-project-management/issue-doc-     lifecycle.md`: "the fix is shipped... archive immediately" — since the
      fix landed in the same continuous session, filed straight into `plans/archive/issues/` rather than transiting
      `plans/active/issues/` at all, avoiding a self-inflicted dual-tracking window). (repo: unified-trading-pm) —
      interactive session, 2026-07-25.

## Progress Log

### 2026-07-25 — interactive session (local track, `/autonomous`)

Filed and resolved in one continuous pass per the operator's explicit instruction ("fix this properly, file an issue and
do it locally the proper way" + `/autonomous`, operator away ~4h). No `DEFERRED`/`BLOCKED-OPERATOR` leftovers — this doc
closes with the fix already shipped and verified. Scope was deliberately kept to the additive, zero-blast-radius fix (a
new read-only audit tool + codex documentation) rather than a live-dispatch-path behavior change, per the workspace's
rule-11 blast-radius discipline — reproducing/proving a stricter runtime check safe against the live fleet's current
gate graph is a materially larger, higher-risk piece of work than this session's scope (a single interactive
investigation with no live incident behind it) justifies unilaterally.

### 2026-07-25 — same session, recovery note

This doc + the codex edit were lost mid-flight once: after the agent-orchestrator code shipped cleanly, the first two
attempts to land this PM-repo commit were blocked by (a) branch drift from other concurrently-active agents sharing this
PM clone, then (b) an unrelated pre-existing `plan_discipline` regression from other agents' work (resolved upstream by
another agent's commit `8badc2d47` in the interim — pulled in and re-verified at 0 violations before retrying). A third
attempt, run backgrounded, came back with the PM doc + codex edit simply absent from the working tree — neither
committed nor present in any of the several dangling `git stash` entries this heavily-shared clone had accumulated from
concurrent sessions (checked the top stash entries directly; the codex diff was present in two of them but the new
issue-doc file was in neither — a brand-new untracked file does not reliably survive repeated `git stash`/`--autostash`
round-trips the same way a tracked file's diff does). Recreated both files verbatim from this session's retained content
(no information lost — the full text was already composed and reviewed earlier in this same session) and shipped cleanly
on the next attempt. No impact on the actual shipped fix (agent-orchestrator code), which lives in a separate,
non-contended clone.
