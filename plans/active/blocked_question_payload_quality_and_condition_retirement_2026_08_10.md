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
      unified-trading-pm@0f9b8a65ca make `contradicted_by` and `description` REQUIRED, add `doc_line` /
      `contradicted_by_line` anchors and a `resolution_required` boolean the worker sets itself, and restate that `doc`
      must be a governance doc (`CLAUDE.md` / `SUB_AGENT_MANDATORY_RULES.md`) since the live finding emitted a plan
      filename instead. **Done when**: the JSON schema block and its worked example carry all six fields and the
      required/optional split is explicit. Repo: unified-trading-pm.
- [ ] [BACKEND] P2. **Validate the POSTed findings shape server-side** rather than rendering whatever arrives — an item
      missing a required key, or naming a `doc` outside the governance-doc set, is logged as a `doc_drift_malformed`
      activity and skipped, not turned into a card. **Done when**: a malformed item produces the new activity row and no
      `BlockedRow`, a test covers each rejection reason, and the rejection count appears in the dispatch result payload.
      Repo: agent-orchestrator.

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

- [ ] [BACKEND] P1. **Add a nullable `context` column to `BlockedRow` plus an idempotent migration**, mirroring
      `_migrate_blocked_queue_claude_session_id`'s no-backfill pattern in `bootstrap.py`. Populate it on the `doc_drift`
      path with both sides' verbatim quotes, their `file:line` anchors, the worker's `description`, and first-detected /
      last-reconfirmed timestamps; expose it on `BlockedView`. **Done when**: column + migration + API field + a test
      proving an old row with `context IS NULL` still renders, and `quality-gates.sh` is green. Repo:
      agent-orchestrator.

### C — condition-derived retirement (the general fix)

- [ ] [BACKEND] P0. **Wire `resolved_drift` to actually close the rows it resolves.** `record_dispatch_result` already
      computes it and discards it — close each matching open `doc_drift:<key>` `BlockedRow` with
      `answered_by="auto:condition_cleared"` and a citation naming the dispatch that cleared it. **Done when**: a run
      where key K drops out of the findings closes the open `doc_drift:K` row, `resolved_doc_drift_count` matches the
      number of rows actually closed, a test covers the open-then-clear cycle, and a Slack CLOSE bookend fires for any
      row that had previously paged (per the alerting SSOT's OPEN/CLOSE contract). Repo: agent-orchestrator.
- [ ] [BACKEND] P1. **Generalise it — add a `condition_key` column and a fourth `classify_retirement` exit that does not
      resolve a `TaskRow`.** Any detector-seeded row carrying a `condition_key` retires when its detector's latest run
      no longer reports that key. Route `doc_drift` through this generic path rather than keeping a bespoke closer.
      **Done when**: `classify_retirement` has a `condition_cleared` exit with no `TaskRow` dependency, a test proves a
      synthetic condition-derived row retires through it, and the `doc_drift`-specific closer from the P0 todo is
      replaced by it (not left alongside it). Repo: agent-orchestrator.
- [ ] [BACKEND] P2. **Stamp and surface `last_reconfirmed_at`** on every surviving detector-derived row on each detector
      run, and render it on the card as "still detected as of `<ts>`". This is what makes an open row mean "currently
      true" rather than "was true at some point". **Done when**: the column updates on each `plan_health` run that
      re-reports the key, the value reaches `BlockedView`, and the card renders it. Repo: agent-orchestrator.
- [ ] [BACKEND] P2. **Audit every `add_blocked` call site for the same blind spot** — enumerate each class of blocked
      row (worker `/blocked`, `BLK-op-*` operator-gated, `doc_drift`, and any other) and record which retirement exits
      can actually fire for it. **Done when**: a table lands in this plan's Progress Log naming every call site and its
      working exits, and any class found with zero reachable exits gets its own `- [ ]` follow-up todo here. Repo:
      agent-orchestrator.
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
