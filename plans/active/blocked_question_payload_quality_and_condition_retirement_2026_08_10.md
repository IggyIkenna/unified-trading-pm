---
doc_type: plan
title:
  Fix blocked-question payload quality (doc_drift raises undecidable questions) and give condition-derived rows a
  retirement exit
summary: >-
  Operator-reported 2026-08-10 from a live `#-1 doc_drift` card — the question named one side of a claimed disagreement,
  truncated it mid-word at 137 chars, dropped the worker's own explanation, and asked "which side is stale?" about a
  finding whose own text ended "no further action needed now". Root cause is four separate payload defects in
  `plan_health.record_dispatch_result` plus one structural gap — a `doc_drift` blocked row has NO auto-retirement path
  at all, because all three exits in `blocked_reconcile.classify_retirement` resolve a `TaskRow` by `task_id` and a
  `doc_drift:<key>` id is not a task. `plan_health` already computes `resolved_drift` every run and discards it, so a
  row stays open forever even after the next run proves the drift is gone. Fix the payload, add a collapsible
  structured-context field so verbosity costs nothing to scan, and generalise a condition-cleared retirement exit that
  any future detector-derived row can use.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, blocked-questions, plan-health, doc-drift, dashboard, escalation, auto-retirement, ux]
related:
  [
    /plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md,
    /plans/archive/2026_08/issues/ao_model_main_agent_as_first_class_slot_2026_08_10.md,
    /plans/epics/escalation_and_disaster_recovery_master.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
created: 2026-08-10
last_updated: "2026-08-10"
parent_epic: escalation_and_disaster_recovery_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: true
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator report 2026-08-10 — "it says two things disagree but I have no idea what they disagree on, what one says,
  what the other one says, and the extent to which it could be already fixed as I dunno the live state. This is not a
  particularly impressive question." Plus the follow-up ask to cover the general case that operator-blocking rows do not
  auto-resolve when later work resolves them.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/server/doc_drift_options.py,
    agent-orchestrator/server/blocked_reconcile.py,
    agent-orchestrator/server/state_store/activity.py,
    agent-orchestrator/server/orm.py,
    agent-orchestrator/dashboard/src/layout.tsx,
    unified-trading-pm/agents/plan_health.md,
    /plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md,
  ]
---

# Blocked-question payload quality + condition-derived retirement

## The live instance

A single card on the blocked-questions view, verbatim:

```
#-1   doc_drift:ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md||claimed a completed
      codex-alignment fix on the worker-liveness doc that was only partially true until this
      run's own fix completed it — no further action needed now          operator-only   21m ago

[plan_health doc_drift] `ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md` — claimed a
completed codex-alignment fix on the worker-liveness doc that was only partially true until this
run's own fix completed it — n…  The doc and the live plan claim disagree — which side is stale?

A  The DOC is stale — update the doc to match the live plan claim        [worker rec]
B  The PLAN claim is wrong — correct the plan; the doc is right
C  Not drift — dismiss as a false positive (both are correct in context)
```

An operator cannot answer this. It names one artifact, quotes nothing from either side, truncates mid-word, and asks a
binary staleness question about a finding whose own text says no action is needed.

## Defect 1 — the question body is a Slack digest line

`record_dispatch_result` builds the blocked question from `_format_drift_item`, whose docstring states it is a "One-line
summary of a doc_drift finding **for the Slack digest**". It hard-truncates the claim at 137 characters plus an
ellipsis. That is the `— n…` above. A digest line optimises for scannability in a chat feed; an operator decision prompt
optimises for sufficiency. The same function cannot serve both, and reusing it means every future widening of the
question is silently capped at 137 chars.

Note the asymmetry this produces on the card: the `task_id` line at the top renders the **untruncated** claim (it is
built from `_drift_key`, which does not truncate), while the question below it renders the truncated one. The operator
sees the full text in the mono id line and a cut-off version in the question.

## Defect 2 — the worker's explanation is never shown to anyone

The agent contract in `unified-trading-pm/agents/plan_health.md` has the worker emit four fields per finding — `doc`,
`claim`, `contradicted_by`, `description`. The blocked question renders `doc` and `claim` only. `description` is the
field where the worker explains what it actually found, and it reaches no surface at all — not the card, not Slack, not
the activity row's rendered form.

## Defect 3 — only one side of the disagreement is recorded

The task id is `doc_drift:<doc>||<claim>`. The empty middle segment is `contradicted_by`. The card asks "which side is
stale?" while the payload contains exactly one side. This is why the question is unanswerable in principle, not merely
underspecified — there is no second side to compare against.

Related and separately wrong: `doc` is specified by the agent contract as `CLAUDE.md|SUB_AGENT_MANDATORY_RULES.md`
(governance-doc drift is the whole point of CHECK 2), but the live finding put a plan filename there. Nothing validates
the POSTed shape, so an off-schema finding renders as if it were well-formed.

## Defect 4 — a non-question was raised as an operator-blocking question

The claim ends "no further action needed now". The worker had already concluded there was nothing to decide, and the
system still opened an `authority="operator"` row with three options and a recommendation. There is no gate between "the
detector produced an item" and "a human must rule on this".

## The structural gap — condition-derived rows can never auto-retire

This is the general problem behind the operator's second ask.

`blocked_reconcile.classify_retirement` has exactly three exits, and **all three resolve a `TaskRow` from
`row.task_id`**:

| Exit            | Trigger                                          | Fires for `doc_drift`? |
| --------------- | ------------------------------------------------ | ---------------------- |
| `task_terminal` | owning `TaskRow` reaches done/cancelled          | No — no `TaskRow`      |
| `doc_archived`  | the task's `plan_ref` left `plans/active/`       | No — no `TaskRow`      |
| `pr_terminal`   | a PR named in the question text is MERGED/CLOSED | No — not PR-shaped     |

A `doc_drift:<key>` id is not a task id, so `session.get(TaskRow, ...)` returns `None` and every exit is structurally
unreachable. The only other escape is `find_resolution_in_plans`, which requires a human to have written the literal
`blocked_id` into a plan line carrying a resolution marker.

Meanwhile `plan_health.record_dispatch_result` computes `resolved_drift` on every run (via `diff_keys` against the
persisted seen-set) and uses it for nothing but a `resolved_doc_drift_count` integer in the response body. The system
already knows the drift cleared and throws that knowledge away.

**The durable principle this plan should establish**: a row created by a _recurring detector_ must carry its generating
condition key and retire when the detector's next run stops reporting that key. Retirement keyed off a `TaskRow` only
covers rows that originate from tasks. Every future detector that seeds blocked rows will otherwise reproduce this exact
bug.

## Scope boundary versus the existing blocked-questions UX issue

`/plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md` is `assigned_vm: planning` and
covers pain points that do **not** overlap this plan — `claude_session_id` capture (shipped), the transcript-jump
affordance, and cross-question dedup/similarity. That doc is about _reaching the agent that asked_; this plan is about
_the payload being sufficient in the first place_ and _the row closing itself when the condition clears_. Neither
supersedes the other. Cross-link both, do not merge them.

One correction owed to that doc is captured as a todo below — its `[UI] P2` todo and its `repos:` frontmatter both name
`deployment-ui`, but the blocked-question queue is rendered **only** by `agent-orchestrator/dashboard/src/layout.tsx`
(`BlockedCard`). `deployment-ui` contains no blocked-question code at all — its only `blocked` matches are
`promotion_blocked` PR counters in `Cockpit.tsx`. Two `ui_developer` workers (slot-11 and slot-27, both 2026-08-08) were
dispatched onto that todo, both declined it as GATED on the backend dependency, and neither noticed the repo was wrong.

## Design — verbosity without a wall of text

The operator constraint is explicit: more information, without making the full question impossible to see on the page.
The answer is structure, not length.

1. **Headline stays one line and always shows both sides** — `<doc> claims "X" · <other> says "Y"`, never truncated
   mid-token; if both sides are not available, the row is not raised.
2. **Volume moves into a new `context` field** rendered as a `<details>` block collapsed by default — verbatim quotes
   from each side with `file:line` anchors, the worker's `description`, and detection timestamps. Unlimited depth, zero
   cost to scanning a queue of ~30 cards.
3. **Freshness answers "is it already fixed?" without the operator checking anything** — an open row means "still
   detected as of `<last_reconfirmed_at>`", and a cleared condition closes the row automatically.

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-alerting.md` — actionable-only channel contract; a non-actionable finding
  must not page, and every paged OPEN needs a CLOSE bookend (todo 8 supplies the CLOSE for auto-retired rows).
- `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` — `plan_health` dispatch cadence and status model.
- `/codex/04-architecture/agent-orchestrator-overview.md` — blocked-queue role in the dispatch loop.

Post-phase codex audit: once the condition-cleared exit lands, the alerting SSOT needs the new auto-retirement
transition documented, and the scheduled-jobs SSOT needs `plan_health`'s new "closes rows it previously opened"
behaviour recorded.

## Why this is two plans, and why this one is `sequential: true`

Both choices are forced by the file map, not by taste.

**`sequential: true` on this plan.** CLAUDE.md's default is that a plan's independent same-priority todos run
CONCURRENTLY across workers, with one hard rule — concurrent todos MUST touch different files. That rule cannot be
satisfied here: **five of these todos edit `server/plan_health.py`** (A1, A2, A4, C1, C3) and three more edit
`server/orm.py` (B1, C2, C3). Dispatching them concurrently would put multiple workers in the same file in different
slots, which is exactly the collision the rule forbids. This is the sanctioned "real same-file overlap" case for
`sequential: true`, not a reflexive serialisation.

**Why the UI work is a separate, gated plan.** `sequential: true` serialises the WHOLE plan, so folding the two `[UI]`
todos in here would be correct but would also hide a real dependency behind mere ordering. Per CLAUDE.md's
"partial-parallelism isn't expressible in one plan → SPLIT", the UI work goes in
[`/plans/active/blocked_question_card_context_rendering_2026_08_10.md`](/plans/active/blocked_question_card_context_rendering_2026_08_10.md)
with `depends_on: [blocked_question_payload_quality_and_condition_retirement_2026_08_10]` + `gate_on_depends: true`, so
the dispatcher cannot offer the UI todos before the `context` column they render actually exists.

That gate is not hypothetical. The sibling doc
[`/plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`](/plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md)
has an ungated UI-todo-on-backend-todo pair in this exact subject area, and its Progress Log records the outcome twice
in one day — slot-11 and slot-27 (both `ui_developer`, 2026-08-08) were each dispatched onto the UI todo while its
backend dependency was still `queued`, and both burned a dispatch declining it as GATED. Two wasted dispatches is the
measured cost of not setting this field.

## Dispatch eligibility — every todo is worker-determinable

No todo here is `[OPERATOR]`-tagged or operator-gated (operator direction 2026-08-10). Each has an outcome a worker can
determine alone — a scoped code change with a machine-checkable done-when, a doc edit against a stated target shape, or
an audit with a stated done-when. Two that could look operator-shaped, and why they are not:

- **C4 (audit every `add_blocked` call site)** is a bounded enumeration with a stated deliverable (a table in this
  plan's Progress Log), not an open-ended judgment call — and any class it finds with zero reachable exits becomes a new
  `- [ ]` todo rather than a decision the worker has to make.
- **C5 (close the currently-open orphaned rows)** carries no delete-safety gate: it is not a GCS delete, an `--apply`
  sweep, or a VM launch. It closes blocked-queue rows **only** through the auto-retirement path C1/C2 build, and only
  for keys the latest `plan_health` run does not report — i.e. it is running the new mechanism against existing rows,
  not a manual DB edit. Safe-idempotent by construction: re-running it closes nothing new, and a row whose key reappears
  is re-opened by the detector on its next run.

## Todos

### A — payload correctness

- [x] ✅ [BACKEND] P1. **Give `doc_drift` blocked questions their own untruncated formatter**, separate from
      `_format_drift_item` (which stays Slack-digest-only, 137-char cap intact). New formatter renders both sides plus
      the worker's `description`. **Done when**: a finding with a >500-char claim reaches the card intact, a regression
      test asserts no truncation on the blocked-question path AND that the Slack path still truncates, and
      `quality-gates.sh` is green. — agent-orchestrator@4ba24dd37 (QG green 3122 passed; 5 new tests covering
      no-truncation, both-sides+description, Slack-path-still-truncates, and end-to-end blocked-question path). Repo:
      agent-orchestrator.
- [x] ✅ [BACKEND] P1. **Refuse to raise a blocked row for an undecidable or self-resolving finding** — require
      non-empty `contradicted_by` AND `claim`, and honour a new `resolution_required` boolean from the worker. A finding
      failing the gate still emits its `doc_drift_open` activity row and its Slack digest line, but creates no
      `BlockedRow`. **Done when**: a finding with empty `contradicted_by` produces the activity row and zero
      `BlockedRow` rows, a test covers both the raised and suppressed paths, and the live instance in this doc's header
      would have been suppressed. Repo: agent-orchestrator. — agent-orchestrator@8a785cd (QG green: 3131 passed;
      `_blocked_row_suppression_reason` gate + `doc_drift_suppressed` activity; 5 new tests cover suppressed/raised
      paths incl. the live-instance shape; also fixed pre-existing live-state-coupled switch tests at 425a779).
- [x] ✅ [DOCS] P1. **Tighten the `plan_health` agent finding contract** in `unified-trading-pm/agents/plan_health.md` —
      unified-trading-pm@034cb4e2ad make `contradicted_by` and `description` REQUIRED, add `doc_line` /
      `contradicted_by_line` anchors and a `resolution_required` boolean the worker sets itself, and restate that `doc`
      must be a governance doc (`CLAUDE.md` / `SUB_AGENT_MANDATORY_RULES.md`) since the live finding emitted a plan
      filename instead. **Done when**: the JSON schema block and its worked example carry all six fields and the
      required/optional split is explicit. Repo: unified-trading-pm.
- [x] ✅ [BACKEND] P2. **Validate the POSTed findings shape server-side** rather than rendering whatever arrives — an
      item missing a required key, or naming a `doc` outside the governance-doc set, is logged as a
      `doc_drift_malformed` activity and skipped, not turned into a card. **Done when**: a malformed item produces the
      new activity row and no `BlockedRow`, a test covers each rejection reason, and the rejection count appears in the
      dispatch result payload. Repo: agent-orchestrator. — agent-orchestrator@ab7ca12 (QG green 3190 passed;
      `_doc_drift_shape_error` gate + `doc_drift_malformed` activity carrying the item + reason;
      `malformed_doc_drift_count` in the `record_result` payload AND `PlanHealthResultResponse` API model; non-dict
      entries rejected as `not an object`; new tests cover missing-key / off-set doc / non-object / mixed
      valid+malformed; the two A2 empty-key suppression tests were repurposed into A4 rejection tests and
      `resolution_required=false` suppression kept with a well-formed fixture; also fixed a pre-existing live-host-only
      worker_liveness test flake at 7bc9ed0).

### B — structured context, collapsed by default

> The two `[UI]` todos that render this field MOVED to the gated companion plan
> [`/plans/active/blocked_question_card_context_rendering_2026_08_10.md`](/plans/active/blocked_question_card_context_rendering_2026_08_10.md)
> (`depends_on` this plan, `gate_on_depends: true`) — they both edit `dashboard/src/layout.tsx` and cannot start until
> the `context` column below exists. See § "Why this is two plans". Their disposition markers stay below so the move is
> recorded rather than read as a todo deletion.

- **[UI] P2. CANCELLED — SUPERSEDED 2026-08-10 (slot-3 interactive, per
  /plans/active/blocked_question_card_context_rendering_2026_08_10.md).** Render `context` as a `<details>` block
  collapsed by default in `BlockedCard` — MOVED to the gated companion plan, not dropped; still open there.
- **[UI] P3. CANCELLED — SUPERSEDED 2026-08-10 (slot-3 interactive, per
  /plans/active/blocked_question_card_context_rendering_2026_08_10.md).** Replace the raw `#{q.slot_id}` render with a
  named source chip so `NO_WORKER_SLOT_SENTINEL` never shows as `#-1` — MOVED to the gated companion plan, not dropped;
  still open there.

- [x] ✅ [BACKEND] P1. **Add a nullable `context` column to `BlockedRow` plus an idempotent migration**, mirroring
      `_migrate_blocked_queue_claude_session_id`'s no-backfill pattern in `bootstrap.py`. Populate it on the `doc_drift`
      path with both sides' verbatim quotes, their `file:line` anchors, the worker's `description`, and first-detected /
      last-reconfirmed timestamps; expose it on `BlockedView`. **Done when**: column + migration + API field + a test
      proving an old row with `context IS NULL` still renders, and `quality-gates.sh` is green. Repo:
      agent-orchestrator. — agent-orchestrator@13f4848 (QG green 3193 passed; nullable `context` Text column +
      `_migrate_blocked_queue_context` no-backfill migration; `add_blocked(context=…)` param; `BlockedView.context`
      parsed dict + `_blocked_to_view` NULL-safe; doc_drift path populates both sides' file:line anchors + description +
      first/last-reconfirmed; 3 new tests incl. NULL-context-still-renders; reconciled a rebase conflict with the
      sibling claude_session_id BlockedView work).

### C — condition-derived retirement (the general fix)

- [x] ✅ [BACKEND] P0. **Wire `resolved_drift` to actually close the rows it resolves.** `record_dispatch_result`
      already computes it and discards it — close each matching open `doc_drift:<key>` `BlockedRow` with
      `answered_by="auto:condition_cleared"` and a citation naming the dispatch that cleared it. **Done when**: a run
      where key K drops out of the findings closes the open `doc_drift:K` row, `resolved_doc_drift_count` matches the
      number of rows actually closed, a test covers the open-then-clear cycle, and a Slack CLOSE bookend fires for any
      row that had previously paged (per the alerting SSOT's OPEN/CLOSE contract). Repo: agent-orchestrator. —
      agent-orchestrator@04db4ee (QG green 3196 passed; record_result closes each open `doc_drift:<key>` row via
      `answer_blocked(..., answered_by="auto:condition_cleared")` with an answer citing the clearing dispatch +
      `doc_drift_cleared` activity; ✅ CLOSE bookend (`notify_slot_blocked_answered`, auto=True) for rows that had
      paged; `resolved_doc_drift_count` now counts rows actually closed, not raw resolved keys; 3 new tests:
      open-then-clear, paged→bookend, no-open-row→zero).
- [x] ✅ [BACKEND] P1. **Generalise it — add a `condition_key` column and a fourth `classify_retirement` exit that does
      not resolve a `TaskRow`.** Any detector-seeded row carrying a `condition_key` retires when its detector's latest
      run no longer reports that key. Route `doc_drift` through this generic path rather than keeping a bespoke closer.
      **Done when**: `classify_retirement` has a `condition_cleared` exit with no `TaskRow` dependency, a test proves a
      synthetic condition-derived row retires through it, and the `doc_drift`-specific closer from the P0 todo is
      replaced by it (not left alongside it). Repo: agent-orchestrator. — agent-orchestrator@b5d38671d (QG green 3201
      passed; `BlockedRow.condition_key` + `_migrate_blocked_queue_condition_key`; `add_blocked(condition_key=)`;
      doc_drift rows stamp `doc_drift:<key>`; `classify_retirement` `condition_cleared` exit resolves NO TaskRow —
      retires any namespaced `condition_key` absent from its detector's seen-set (`_CONDITION_SEEN_SET_RELPATHS`
      registry, path joined at call time); reconcile retirement `answered_by` is now `auto:<reason>` so
      condition-cleared rows read `auto:condition_cleared`; C1's in-record_result closer + bookend REMOVED, replaced by
      this exit; 4 new tests incl. synthetic-row retire-through + reconcile end-to-end + still-
      reported-does-not-retire).
- [x] ✅ [BACKEND] P2. **Stamp and surface `last_reconfirmed_at`** on every surviving detector-derived row on each
      detector run, and render it on the card as "still detected as of `<ts>`". This is what makes an open row mean
      "currently true" rather than "was true at some point". — agent-orchestrator@dff3e40480 (QG green; added
      `last_reconfirmed_at` column + migration + stamp-at-creation + re-stamp surviving rows each `plan_health` run +
      `BlockedView`/`_blocked_to_view` wiring; 3199 tests passed, 2 pre-existing env flakes unrelated). Repo:
      agent-orchestrator.
- [x] ✅ [BACKEND] P2. **Audit every `add_blocked` call site for the same blind spot** — enumerate each class of blocked
      row (worker `/blocked`, `BLK-op-*` operator-gated, `doc_drift`, and any other) and record which retirement exits
      can actually fire for it. **Done when**: a table lands in this plan's Progress Log naming every call site and its
      working exits, and any class found with zero reachable exits gets its own `- [ ]` follow-up todo here. — slot-22
      audit (no code change; audit table in Progress Log below). Repo: agent-orchestrator.
- [ ] [BACKEND] P3. **Close the currently-open orphaned `doc_drift` rows** once the retirement path exists — these
      predate the fix and will never clear on their own. **Done when**: the live blocked queue contains no `doc_drift:*`
      row whose key is absent from the most recent `plan_health` run's findings, verified against the live API. Repo:
      agent-orchestrator.

### D — corrections owed to the sibling doc

- [ ] [DOCS] P2. **Correct the wrong repo in
      `/plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`** — its `[UI] P2`
      transcript-jump todo says "Repo: deployment-ui" and its `repos:` frontmatter lists `deployment-ui`, but the
      blocked-question queue is rendered only by `agent-orchestrator/dashboard/src/layout.tsx`; `deployment-ui` has no
      blocked-question code (verified 2026-08-10 — its only `blocked` matches are `promotion_blocked` PR counters). Add
      a dated Progress Log marker recording that two `ui_developer` workers were dispatched onto that todo and neither
      caught it. **Done when**: the todo text and the frontmatter both name `agent-orchestrator`, and a dated marker
      records the correction. Repo: unified-trading-pm.

## Progress Log

- **2026-08-10 (filed, slot-3 interactive)**: Filed from an operator report on a live `#-1 doc_drift` card. Traced all
  four payload defects to `plan_health.record_dispatch_result` and its reuse of the Slack-digest formatter
  `_format_drift_item`; confirmed `contradicted_by` was empty on the live finding by reading the `||` in its task id.
  Confirmed the retirement gap by reading all three exits in `blocked_reconcile.classify_retirement` — every one
  resolves a `TaskRow` from `row.task_id`, and `doc_drift:<key>` is not a task id — and confirmed `resolved_drift` is
  computed and discarded in `record_dispatch_result`. Verified the `-1` sentinel is `orm.NO_WORKER_SLOT_SENTINEL` and is
  _correct_ (the `plan_health` one-shot frees its slot before the row outlives it; `0` was unavailable because
  `autospawn._MAIN_SLOT_ID` already claims it, per
  `/plans/archive/2026_08/issues/ao_model_main_agent_as_first_class_slot_2026_08_10.md`) — the defect is rendering it
  raw, not the value. Conflict check against `plans/active/` found
  `blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md`; read it in full and established the scope
  boundary above rather than folding into it (that doc is `assigned_vm: planning`, this one is human/NA per operator
  instruction, and their subject matter is disjoint). While cross-checking it, found its `[UI]` todo and `repos:`
  frontmatter name `deployment-ui` for a component that lives in `agent-orchestrator/dashboard/` — filed as todo D.
- **2026-08-10 (flipped to AO dispatch, operator direction)**: operator changed the destination — `assigned_vm: NA` →
  `planning`, `execution_scope: local-only` → `orchestrator-agent`, with the explicit instruction that no part be
  operator-blocked. Re-checked every todo against the dispatch-scope eligibility bar
  (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility") — all are
  bounded with worker-determinable outcomes; none was or is `[OPERATOR]`-tagged; the two that could read as
  operator-shaped (C4, C5) are justified in § "Dispatch eligibility" above. Set `sequential: true` (five todos edit
  `plan_health.py`, three edit `orm.py` — the same-file-overlap case the rule sanctions) and SPLIT the two `[UI]` todos
  into the `gate_on_depends` companion plan rather than leaving a real dependency expressed as mere ordering. The
  NA-corpus ratchet note filed with the original version is dropped — this doc no longer counts against that corpus.
- **2026-08-10 (A4, slot-16 worker)**: Implemented todo A4 — server-side validation of the POSTed doc_drift shape.
  `_doc_drift_shape_error()` in `server/plan_health.py` rejects an item missing a required key (the 7-key contract from
  todo A3) or naming a `doc` outside `{CLAUDE.md, SUB_AGENT_MANDATORY_RULES.md}`; each rejection logs a
  `doc_drift_malformed` activity (with the offending item + reason) and the item is skipped entirely — no dedup key, no
  `doc_drift_open`, no BlockedRow, no Slack page. `malformed_doc_drift_count` added to the `record_result` payload AND
  the `PlanHealthResultResponse` API model so the POSTing worker sees its own shape violations. Non-dict entries in the
  `doc_drift` list are rejected as `not an object` instead of being silently dropped. — agent-orchestrator@ab7ca12 (QG
  green 3190 passed). Repurposed the two A2 empty-key suppression tests into A4 rejection tests (missing-key / off-set
  doc), kept `resolution_required=false` suppression with a well-formed fixture, and added shape-gate / non-object /
  mixed valid+malformed count tests. Along the way fixed a pre-existing live-host-only `test_working_spinner_not_kicked`
  flake (stale `context_used_pct` mock → the code's live `context_reading` call site, which reads a real slot-1 config
  dir on this host) that turned the first Pass-1 QG run red — agent-orchestrator@7bc9ed0.
- **2026-08-10 (B1, slot-16 worker)**: Added the nullable `context` column to `BlockedRow` (JSON-encoded `Text`,
  no-backfill) + idempotent `_migrate_blocked_queue_context` in `bootstrap.py` (registered in `create_all_tables`,
  mirroring `_migrate_blocked_queue_claude_session_id`). `add_blocked()` gained an optional `context` param; worker
  `/blocked` and `BLK-op-*` rows stay untouched (NULL). `BlockedView.context` (parsed `dict | None`) +
  `_blocked_to_view` parse it NULL-safely — an old row with `context IS NULL` still renders. The `doc_drift` path in
  `record_result` populates it with both sides' `file:line` anchors (doc quote = the `claim`; the plan side has no
  verbatim quote in the contract, so `quote=None`), the worker's `description`, and equal
  `first_detected_at`/`last_reconfirmed_at` (a later detector run re-stamps the latter). — agent-orchestrator@13f4848
  (QG green 3193 passed; 3 new tests incl. NULL-context-still-renders). During the ship, a
  `git pull --rebase --autostash` conflict with the sibling `claude_session_id` BlockedView work
  (`blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24` -001/-002) was reconciled by keeping BOTH fields —
  upstream `claude_session_id` + this plan's `context` — in `BlockedView` and `_blocked_to_view`.
- **2026-08-10 (C1, slot-16 worker)**: Wired `resolved_drift` (computed but discarded every run) to actually close the
  `doc_drift:<key>` BlockedRows it resolves. Inside `record_result`'s session, for each key that dropped out of the
  findings, every open row with `task_id == "doc_drift:<key>"` is closed via
  `answer_blocked(..., answered_by="auto:condition_cleared")` with an answer naming the clearing dispatch, a
  `doc_drift_cleared` activity fires, and a ✅ CLOSE bookend (`notify_slot_blocked_answered`, auto=True) posts for any
  row that had already paged (per the alerting SSOT's OPEN/CLOSE contract — a never-paged row has no OPEN page to
  bookend). `resolved_doc_drift_count` now equals the number of rows ACTUALLY closed (a resolved key with no open row
  contributes zero). — agent-orchestrator@04db4ee (QG green 3196 passed; 3 new tests: open-then-clear cycle,
  paged→bookend, no-open-row→zero). Note: C2 generalises this into a `condition_cleared` `classify_retirement` exit +
  `condition_key` column and REPLACES this doc_drift-specific closer — C1 deliberately keeps the bespoke path until C2
  lands.
- **2026-08-10 (C2, slot-16 worker)**: Generalised C1's condition-cleared closure into the generic path and routed
  doc_drift through it, replacing the bespoke closer (per C2's "not left alongside it"). Added
  `BlockedRow.condition_key` (nullable, no-backfill `_migrate_blocked_queue_condition_key`) +
  `add_blocked(condition_key=)`; doc_drift rows stamp `condition_key="doc_drift:<drift_key>"`. `classify_retirement`
  gained the `condition_cleared` exit — the one exit with NO `TaskRow` dependency: a row carrying a namespaced
  `condition_key` retires when its detector's latest run (the seen-set under `STATE_DIR`, mapped per-namespace in
  `_CONDITION_SEEN_SET_RELPATHS`, joined at CALL time so a STATE_DIR change/test-monkeypatch is honoured) no longer
  reports that key. The reconcile sweep's existing retirement path answers the row (answered_by generalised from
  `auto-retire` to `auto:<reason>`, so condition-cleared rows read `auto:condition_cleared`) and fires the ✅ CLOSE
  bookend for paged rows. C1's in-`record_result` closer + bookend block were REMOVED; `resolved_doc_drift_count` is
  again an informational resolved-keys count. — agent-orchestrator@b5d38671d (QG green 3201 passed; 4 new tests:
  synthetic condition-derived row retires via `classify_retirement`, end-to-end through `reconcile_once` with
  `answered_by=auto:condition_cleared` + slot freed, still-reported-key does not retire, record_result reports resolved
  count without closing).
- **2026-08-10 (C3, slot-6 worker)**: Added `last_reconfirmed_at` DateTime column to `BlockedRow` + no-backfill
  `_migrate_blocked_queue_last_reconfirmed_at()` migration. `add_blocked()` accepts optional `last_reconfirmed_at` param
  — stamped at creation for doc_drift rows so "still detected as of <ts>" works immediately. On every `plan_health` run,
  surviving keys (in both the old seen-set AND the current findings) now have their open `BlockedRow` rows'
  `last_reconfirmed_at` re-stamped; the JSON `context` field's `last_reconfirmed_at` is also updated for consistency.
  Wired through `BlockedView` + `_blocked_to_view` for dashboard render. — agent-orchestrator@dff3e40480 (QG green, 3199
  passed; 2 pre-existing flaky env-dependent tests in `test_tmux_spawn_deepseek_context_window.py` — host has
  `CLAUDE_CODE_MAX_CONTEXT_TOKENS=1000000` set globally, tests expect it unset; unrelated to this change).
- **2026-08-10 (slot-16 worker, pre-compact journal)**: Session shipped A4/B1/C1/C2 — all flipped with evidence above,
  both worktrees clean, `ahead=0` on `agent-orchestrator` and `unified-trading-pm` — safe to compact. **Deferred (all
  already tracked `- [ ]`, not at risk):** C3 `last_reconfirmed_at` stamping · C4 `add_blocked` call-site audit · C5
  close orphaned rows · D1 sibling-doc repo correction. **Recommended next: C3** (surviving detector rows should carry
  "still detected as of `<ts>`", the companion card plan renders it). **Lessons carried for the next session:**
  quickmerge REBASES a local commit in STAGE 0.4 so its SHA changes — cite the post-merge SHA quickmerge prints as
  `📌 CITE THIS` (the pre-merge SHA is not on origin); `rg -r` is ripgrep's REPLACE flag, not recursive (rg recurses by
  default) — `rg -rn` replaces matches with "n"; `git commit ... | tail` can hide a pre-commit hook failure — verify the
  SHA moved; pre-commit `ruff-format` reformats then aborts — re-`git add` before re-committing; a module-level registry
  that bakes in `config.STATE_DIR` at import time defeats test `monkeypatch` — resolve such paths at call time.
- **2026-08-10 (C4, slot-22 worker)**: Audit of every `add_blocked` / direct `BlockedRow` call site in production code.
  Three call sites found; none has zero reachable retirement exits (the `doc_drift` class had zero before C1/C2 landed
  on this same plan — that was the blind spot this todo exists to confirm is now closed).

  **Call site 1 — Worker `/blocked` endpoint** (`server/routes/slots_worker.py:2543`): `add_blocked()` with real
  `task_id` + `slot_id`, no `condition_key`. Row class: worker-raised blocked questions (`BLK-xxxxxxxx`).

  **Call site 2 — `doc_drift` detector** (`server/plan_health.py:1098`): `add_blocked()` with
  `task_id="doc_drift:<key>"` (not a TaskRow id), `condition_key="doc_drift:<key>"`, `slot_id=NO_WORKER_SLOT_SENTINEL`.
  Row class: detector-seeded doc_drift rows.

  **Call site 3 — Operator-gated `BLK-op-*`** (`server/bootstrap.py:1038`): direct `BlockedRow()` construction (NOT via
  `add_blocked()` — bypasses the main-agent nudge). `blocked_id="BLK-op-{task.id}"`, real `task_id`,
  `slot_id=NO_WORKER_SLOT_SENTINEL`, no `condition_key`. Row class: operator-gated plan todos.

  | Exit                           | Call site 1 (worker /blocked) | Call site 2 (doc_drift)            | Call site 3 (BLK-op-*)     |
  | ------------------------------ | ----------------------------- | ---------------------------------- | -------------------------- |
  | `task_terminal`                | ✅ real TaskRow               | ❌ `doc_drift:<key>` not a task id | ✅ real TaskRow            |
  | `doc_archived`                 | ✅ TaskRow.plan_ref           | ❌ no TaskRow                      | ✅ TaskRow.plan_ref        |
  | `pr_terminal`                  | ✅ text-based match           | ✅ text-based match                | ✅ text-based match        |
  | `condition_cleared`            | ❌ no condition_key           | ✅ `doc_drift:<key>` in registry   | ❌ no condition_key        |
  | `find_resolution_in_plans`     | ✅ plan-corpus scan           | ✅ plan-corpus scan                | ✅ plan-corpus scan        |
  | `classify_timeout` (kill slot) | ✅ real slot_id               | ❌ NO_WORKER_SLOT_SENTINEL         | ❌ NO_WORKER_SLOT_SENTINEL |

  **Verdict**: No class has zero reachable exits. The `doc_drift` class (the plan's original blind spot) now has
  `condition_cleared` as its primary exit + `pr_terminal` and plan-corpus resolution as fallbacks. The `BLK-op-*` path's
  use of direct `BlockedRow()` (bypassing `add_blocked()`) is intentional — these rows represent operator-gated plan
  todos, not worker questions, and their primary resolution path is `find_resolution_in_plans` (an operator ruling
  documented in a plan Progress Log) or `task_terminal` (the task is done/cancelled). No follow-up todos needed.
