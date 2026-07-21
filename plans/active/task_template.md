---
doc_type: plan
title: Task Template — How to Author a Plan
summary:
  How to author a plan the fleet can execute. Pick a TRACK (LOCAL/human vs AO-dispatched), copy the matching
  frontmatter, follow the todo format, and honour the AO rules (10–20 todos, intra-plan concurrency by default +
  when/how to serialise, split-into-plans for partial parallelism, draft-gated phases, per-task `[TAG]` roles). Read
  this BEFORE writing any plan. Dispatch + prerequisite mechanics (§4) are verified against `regen_backlog_from_plan.py`
  / `dispatch.py` so an author never relies on unbuilt behavior.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [template, format, canonical, agent-task, plan-authoring]
related: [ao_dispatch_correctness_regen_reconcile_2026_07_07.md, PLAN_FORMAT.md]
created: "2026-02-25"
last_updated: 2026-07-14 # was: 2026-07-07 — corrected 2026-07-14, doc-reconciliation vr2#13: body already carried 2026-07-12 inline correction annotations (status-enum fix, sequential:true SHIPPED note) never reflected in frontmatter
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class:
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: infra
drift_direction: advance-code
---

# Task Template — How to Author a Plan

> **READ THIS before writing any plan.** Pick your TRACK (§1), copy the matching frontmatter (§2), follow the todo
> format (§3). AO-dispatched plans have STRICT rules (§4). Editing a plan whose tasks are already live? §5. Canonical
> frontmatter schema: `plans/PLAN_FORMAT.md`. **Never hand-edit `backlog.yaml`** — the backend owns it; you author
> plans.

---

## 1. Pick your track — LOCAL vs AO-DISPATCHED

|                    | **LOCAL / human plan**                                     | **AO-DISPATCHED plan**                   |
| ------------------ | ---------------------------------------------------------- | ---------------------------------------- |
| Who executes       | you / an interactive session                               | background AO fleet workers              |
| `assigned_vm`      | `NA`                                                       | `planning`                               |
| `execution_scope`  | `local-only`                                               | `orchestrator-agent`                     |
| Ingested by regen? | **No** (never)                                             | **Yes** (when `status: active`)          |
| Length             | any (not ingested)                                         | **10–20 todos — STRICT**                 |
| Use when           | operator-only work, design docs, trackers, dispatcher work | autonomous work you want the fleet to do |

**Default is LOCAL** unless you intend the fleet to pick it up. **HARD RULE (CLAUDE.md): ask the operator before
creating an AO plan** — _"agent-orchestrator plan or human plan?"_ A `status: draft` plan is never ingested regardless
of track — flip to `active` to dispatch.

---

## 2. Frontmatter (copy the matching block)

**AO-DISPATCHED** (fleet executes):

```yaml
---
doc_type: plan
title: <concise — what this plan achieves>
summary: <2–4 lines; NO ": " colon-space in unquoted text — use an em-dash —>
status: active # draft (NOT ingested) | active | blocked | paused | complete | cancelled | superseded (was: "active | draft (NOT ingested) | done | blocked" — corrected 2026-07-12, doc-reconciliation autofix finding 382, plan_reconciliation_operator_decisions_2026_07_11.md §A2 "50 reclassified" blanket ruling; PLAN_FORMAT.md:86 + scripts/docs/docspec.py:59 are the enforced enum, which has no "done" value)
nature: process # process | design
asset_group: [<group>] # e.g. [defi] [tradfi] [meta]
stage: [<stage>] # e.g. [data] [meta]
repos: [<repo>, ...]
scope: [engineer]
tags: [<tag>, ...]
related: [<doc>, ...]
created: <YYYY-MM-DD>
last_updated: <YYYY-MM-DD>
parent_epic: <epic-slug> # REQUIRED — absence = orphan = review-blocking
assigned_vm: planning # planning = AO executes | NA = not dispatched
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra # refactor 0.4x | design 0.6x | infra 0.8x | brand-new 1.0x | research 1.2x
estimate_baseline_ai_days: <n>
estimate_calibrated_ai_days: <n × class-multiplier>
assigned_role: <default craft — data_engineering | infra | backend_engineer | ui_developer | review>
# model_tier: opus-required # optional — default sonnet (role-derived); fable-required = OPERATOR-REQUEST-ONLY (§4)
drift_direction: advance-code
depends_on: # optional — upstream plan slugs (documents ordering + gates archival)
# gate_on_depends: true    # optional — machine-hold this plan's tasks until depends_on tasks are done
# sequential: true         # optional — STRICT serial: task N waits for N-1 done — SHIPPED (was: "[ROLLING OUT — see §4]" — corrected 2026-07-12, doc-reconciliation finding 380, §A2 B-queue ruling: ao@ff6100ad shipped `_wire_sequential_prereqs` + `plan_order` with tests, and 3+ production plans/issues already set `sequential: true` in frontmatter, e.g. active/issues/v1_enumerator_dispatch_not_deletable_2026_07_06.md)
---
```

**LOCAL / human** — same block with `assigned_vm: NA` + `execution_scope: local-only`. Length is unconstrained (never
ingested). Use for operator-only work, trackers, design docs, and dispatcher-surgery plans.

---

## 3. Todo format

- Every todo: `- [ ] [TAG] P0. <description>` (open) → `- [x] N. ✅ [TAG] P0. <desc> — <repo>@<sha> + evidence` (done).
- **Keep each todo's load-bearing content on the FIRST physical line** _(verified in `regen_backlog_from_plan.py`
  2026-07-21: `_parse_open_todos` captures only the first line matching `- [ ]`; wrapped/indented continuation lines are
  NOT parsed into the task brief the dispatcher sees)._ The `[TAG]`, `P<n>`, and the essential verb-phrase MUST be on
  line 1; treat continuation lines as human-only notes the worker's brief will not include.
- **Reference SYMBOLS, never line numbers** _(operator rule 2026-07-21)_. A plan out-lives the code it points at — the
  moment any agent edits a file, every `file.tsx:821` / `:256-320` shifts and now points at the WRONG code (exactly what
  happened when one plan extracted shared primitives out of `Deployments.tsx` and every dependent plan's line refs went
  stale). Cite the **function / class / component / type / testid / endpoint** an agent can `grep` for (e.g. "the
  `useColumnSort` hook in `src/hooks/`", not "`Deployments.tsx:888`"); the agent locates the current position itself.
  Same for **counts** ("all N tests") — pin the stable thing ("keep every existing assertion in `foo.spec.ts` green"),
  not a number that a new test invalidates.
- **`[TAG]` → craft role** (per-task, AO): `[INFRA]`→infra · `[DATA]`→data_engineering · `[BACKEND]`→backend_engineer ·
  `[UI]`→ui_developer · `[REVIEW]`→review. Generic `[CODE]` / `[SCRIPT]` → the plan's `assigned_role`.
- **Priority** `P0`–`P3` (P0 = most urgent). Same-priority tasks run in plan-file order (§4).
- **Non-dispatchable** (kept visible, never ingested): a line containing `BLOCKED-<TOKEN>` (e.g. `BLOCKED-CREDENTIALS`,
  `BLOCKED-OPERATOR-DECISION`), `[OPERATOR]` (operator-only action), or a `_(stretch, optional)_` marker.

---

## 4. AO-DISPATCHED plans — STRICT rules

- **10–20 todos, never more.** Fewer is fine; group RELATED items so we don't get hundreds of tiny plans. A 100-todo
  monolith is banned for dispatch — it bloats the backlog and couples unrelated work. _(LOCAL plans are exempt.)_
- **Intra-plan concurrency is REAL and often intended — the plan is your unit of parallelism** _(corrected 2026-07-21,
  verified via code read of `regen_backlog_from_plan.py` + `dispatch.py`: single-agent stickiness is NOT enforced —
  regen sets no slot affinity, `_task_is_routable_to` returns True for any free slot. The old "one plan = one agent /
  split for ALL parallelism" framing was aspirational and is superseded)._ A plan's same-priority todos are each
  **independently dispatchable and run CONCURRENTLY across whatever workers are free** unless you gate them. This is a
  FEATURE — e.g. one plan with 5 independent `[REVIEW]` todos ("babysit this backfill VM", "confirm each un-downloadable
  item is genuinely absent upstream", …) fans out to 5 agents at once. **The one hard rule: concurrent todos MUST touch
  different files** (same file → two workers collide — banned by multi-agent safety). So, per plan:
  - **Independent tasks on different files → leave them ungated** (the default). Free throughput.
  - **A real dependency chain, OR tasks that share a file → `sequential: true`** (serialises the WHOLE plan).
  - **Partial parallelism** (some tasks parallel, THEN a step gated on them) is **NOT expressible inside one plan** —
    **SPLIT**: parallel work in Plan A; the gated step in Plan B with `depends_on: [A]` + `gate_on_depends: true`. Do
    NOT reflexively set `sequential: true` — it forecloses ALL intra-plan parallelism; use it only when tasks genuinely
    chain or share files.
- **An AUDIT is its own plan** (its findings shape later phases — keep it separable).
- **Draft-gated phase chains** — for multi-phase work, ship each phase as a SEPARATE plan: the current phase is
  `status: active`, later phases are `status: draft` (regen skips drafts, so an unfinalised phase never floods the
  backlog); the phase's LAST todo finalises the next phase's todos and flips it `draft`→`active`. _[ACTIVE NOW: draft =
  not ingested; active→draft prunes queued tasks.]_ Distinct from `depends_on` + `gate_on_depends: true`, which INGEST
  the downstream and machine-hold it until upstream is done — use that when the downstream is already finalised.
- **Ordering + how prerequisites ACTUALLY work** _(verified in `regen_backlog_from_plan.py` 2026-07-21)._ Each todo
  becomes backlog task `<plan-slug>-NNN` with `plan_order` = its file position; tasks dispatch by
  `(tier, priority, plan_order)`. **Ordering controls DISPATCH order, NOT completion — same-priority todos still run
  concurrently.** A hard "finish-before" is a **prerequisite**, and there are ONLY TWO ways to create one from a plan —
  **there is NO per-todo prereq syntax; regen never parses prereqs from todo text** (so writing `(prereq: …)` in a todo
  line does nothing — corrected 2026-07-21; the earlier "add explicit `prereqs.completed_tasks`" advice was wrong,
  `RULES.md` confirms regen does not derive per-task prereqs from todos):
  1. **`sequential: true`** → `_wire_sequential_prereqs` sets each task's `completed_tasks` to its immediate predecessor
     by `plan_order` → the whole plan is a serial chain.
  2. **`depends_on: [plan-slugs]` + `gate_on_depends: true`** → `_wire_gate_on_depends_prereqs` makes every task of THIS
     plan wait on every task of the named upstream plan(s). **`depends_on` ALONE does NOT gate dispatch** (documents
     ordering + gates archival only). Enforcement: `dispatch.py::_prereqs_met` holds a `queued` task until all its
     `prereqs.completed_tasks` are `done` (and any named `prereqs.prerequisites` conditions are `true`). NEVER hand-edit
     `backlog.yaml` to add prereqs — author the frontmatter; the backend derives them.
- **Verify an "Ordering note" before asserting it's safe.** For multi-repo/multi-step DAG plans (audit→fix→verify,
  migrations), a note claiming step N can land before step M is a CORRECTNESS CLAIM, not a convenience aside — don't
  reason from the diff's code shape alone (e.g. "this branch doesn't read X" can still break at runtime if a live caller
  feeds it X's current state). Before writing the note, actually make the ISOLATED step-N diff (with M not yet landed)
  and run it through `bash scripts/quality-gates.sh`; only write "safe to land before M" if that run is green. If it
  turns out unsafe, encode the REAL dependency as `sequential: true` (intra-plan) or `depends_on` +
  `gate_on_depends: true` (cross-plan) so the backlog dispatcher enforces it — a human-readable "🔴 BLOCKED, don't
  dispatch" banner is NOT a dispatch gate; a worker picking up the plan cold can still claim the blocked todo before
  ever reading the banner. **Caveat (corrected 2026-07-15, plan-reconcile: confirmed via code read of
  `_parse_open_todos`/`task_still_dispatchable` in `regen_backlog_from_plan.py`, see
  `mtds_available_at_cross_asset_backfill_2026_07_13.md` Progress Log 2026-07-14)**: `sequential: true` only orders
  same-priority **ingested/dispatchable** todos by file position — a todo excluded from ingestion via a
  `BLOCKED-<TOKEN>`/`[OPERATOR]`/`_(stretch, optional)_` marker (§3) does NOT count as "the predecessor," so if that
  excluded todo is first in file order, the next todo dispatches immediately regardless of whether the excluded one is
  actually resolved — so do NOT place a non-dispatchable todo (a `[OPERATOR]` decision, a `BLOCKED-` gate) as the FIRST
  link in a `sequential` chain expecting it to hold the rest; it won't. Restructure so the true gate is a dispatchable
  todo, or move the pre-gate work into its own plan the downstream `gate_on_depends` _(corrected 2026-07-21 — the
  earlier "use `prereqs.completed_tasks` instead" was not actionable: authors cannot write per-task prereqs from a plan
  file; see the Ordering bullet above)_. Case study: `coinbase_bare_name_migration_2026_07_06.md` Step S2's "safe before
  S3" note was disproven by an actual QG run — see
  `plans/active/issues/coinbase_bare_name_migration_s2_ordering_2026_07_10.md` for the failure + the `sequential: true`
  fix.
- **Multi-role in one plan — SHIPPED** _(corrected 2026-07-21, was "[ROLLING OUT: today role is the plan-level
  `assigned_role` for ALL tasks]"; verified via code read of `_TAG_TO_ROLE` + `_task_role_from_tag` in
  `regen_backlog_from_plan.py` — per-task routing is live)._ Each todo routes to the role named by its `[TAG]`
  (`[BACKEND]`→backend_engineer · `[UI]`→ui_developer · `[REVIEW]`→review · `[DATA]`→data_engineering ·
  `[INFRA]`→infra); an unmapped/absent tag falls back to the plan's `assigned_role`. So a mixed backend+UI+review plan
  routes each task to the right role — no need to split by role. _(Dispatch nuance: a generic worker with no declared
  `slot_role` can still claim any task, so role is a correct STAMP but only GUARANTEED off-role where role-declared
  slots exist.)_
- **Model tier — sonnet/opus only (default).** Set `model_tier: opus-required` for hard reasoning; otherwise the role's
  default (sonnet) applies. **`fable-required` (Fable 5) is OPERATOR-REQUEST-ONLY** — never assign it unless the
  operator DIRECTLY asks for Fable (it is for the hardest / longest-running interactive work — overkill for routine
  dispatch). Effort: Haiku has NO effort levels (thinking on/off only); sonnet/opus/fable support `--effort` low→max.
  _[ROLLING OUT: fable spawn + per-model effort.]_
- **NEVER hand-edit `backlog.yaml`.** Author plans; the backend derives the backlog.

---

## 5. Safely editing a plan whose tasks are already assigned to AO

_[SHIPPED 2026-07-07 (was: "ROLLING OUT ... edits to existing todos do NOT propagate" — corrected 2026-07-14,
doc-reconciliation vr2#10): `ao_dispatch_correctness_regen_reconcile_2026_07_07.md` Phases 2-5 all landed
(`ao@ff6100ad`+`c6a31ed6`+`f976b6e4`+`07035aba`), "ALL 3 ROOT CAUSES FIXED (RC-1/RC-2/RC-3)" per that plan's 2026-07-07
Progress Log — the table below is now the LIVE behavior, not a future target. **Caveat (known bug, see
`issues/backlog_regen_drops_handtuned_prereqs_2026_07_12.md` Defect B)**: `_reconcile_task_fields()` re-derives
`priority` from the plan's current `P<n>` tag on every regen tick with no "was this hand-overridden" check, so a
manually-set `priority` override on an already-derived task reverts on the next tick as long as the todo line is still
open — do NOT rely on a hand-tuned field surviving regen; edit the plan's `P<n>` tag itself instead.]_

Current behavior (SHIPPED 2026-07-07) — what the backend does to a task by its state:

| You change…              | `queued` / `blocked`   | `dispatched` (in-flight)                                  | `done` |
| ------------------------ | ---------------------- | --------------------------------------------------------- | ------ |
| **model / role / prio**  | updated in place       | adapt-in-place (retier stop-and-`--resume` if higher)     | no-op  |
| **reword a todo's text** | old removed, new added | old task `cancelled` + scoped-revert; new text = fresh    | no-op  |
| **remove a todo**        | pruned from backlog    | `cancelled` + scoped-revert (NOT deleted); UI shows count | kept   |

Scoped revert = the worker reverts ONLY its own task's touched files (`git restore`) — never whole-branch, never
`reset --hard`.

---

## 6. Safeguards (ALWAYS — these are battle-tested)

**Before you change files** — record what you'll touch and make a reference backup (do NOT switch to it):

```bash
FILES_TO_TOUCH="path/to/file1.py path/to/file2.py"
git branch "backup-before-<task>-$(date +%s)"   # reference point only
# Recovery — ONLY the files you touched:
#   git restore --source=<backup-branch> -- $FILES_TO_TOUCH
```

**NEVER**: `git reset --hard` / `git checkout <branch>` / `git clean -fd` a dirty tree · revert the WHOLE branch (other
agents share the repo — only revert your own files) · skip tests or add `|| true` / `@pytest.mark.skip` without a
documented reason · `# type: ignore` without fixing root cause · `Any` · `.get("k", {})` (fail loud) · hand-edit
`backlog.yaml` · auto-commit from an AO worker without reporting back.

**ALWAYS**: fix root causes, not symptoms · keep the list of files you touched (for a scoped revert) · test frequently ·
commit + push + flip the plan checkbox in the SAME turn (`docs(plans):` prefix) · cite evidence for a done claim
(`<repo>@<sha>` + a resolving build/run).

---

**This template is a LOCAL doc (not ingested). Copy §2 into a new `<slug>_<YYYY_MM_DD>.md` in `plans/active/` to
start.**
