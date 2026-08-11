# Plan Format — SSOT

**Canonical format for all plans in `unified-trading-pm/plans/active/`.**

Every plan that touches code, infrastructure, or business outcomes must declare its readiness gates. This prevents plans
from being arbitrarily marked done when only some repos are complete, or when a plan is blocked by another that owns a
different concern (e.g., deployment infrastructure).

---

## 3-Tier Readiness Model

### Code Readiness (C)

| Gate | Meaning                                                                |
| ---- | ---------------------------------------------------------------------- |
| C0   | Not started                                                            |
| C1   | Implementation complete — code written, not yet tested                 |
| C2   | Unit tests passing — tests written, no regression, coverage maintained |
| C3   | Linter + Codex gates — ruff, basedpyright, no bad practices            |
| C4   | Full `quality-gates.sh` Pass 1 — no hidden issues                      |
| C5   | Quickmerge complete — PR created and merged to staging/main            |

### Deployment Readiness (D)

| Gate | Meaning                                                                                                                                               |
| ---- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1   | Deployable — infra provisioned, configs injected, Docker image builds                                                                                 |
| D2   | CI/GHA smoke tests pass — code-only, emulators + mocks, **no real service calls** (equivalent to `production_mock_e2e` suite green in GitHub Actions) |
| D3   | Staging integration tests pass — **real service and API calls** in staging environment replicating prod (SIT suite, live credentials)                 |
| D4   | Load/performance tests pass in staging                                                                                                                |
| D5   | Production-ready — all security + operational gates green, post-deploy health checks pass                                                             |

### Business Readiness (B)

| Gate | Meaning                                                                                        |
| ---- | ---------------------------------------------------------------------------------------------- |
| B1   | Acceptance criteria defined                                                                    |
| B2   | Scenario analysis complete — edge cases, load tests, adversarial scenarios                     |
| B3   | Performance targets met — domain-specific KPIs declared in the plan (see below)                |
| B4   | Batch vs live validation — t+1 check that batch output matches live run expectations           |
| B5   | Staging vs live parity — replay N minutes of staging calls against prod-equivalent environment |
| B6   | User approved — human sign-off that commercial objective is met                                |

#### B3 KPI examples by domain

| Domain        | Example KPI                                   |
| ------------- | --------------------------------------------- |
| ML prediction | Accuracy ≥ X%, precision/recall thresholds    |
| Strategy      | Minimum backtesting P&L threshold, Sharpe ≥ Y |
| Execution     | Alpha improvement ≥ Z bps vs benchmark        |
| Latency       | P99 < N ms under target load                  |
| Data pipeline | Completeness ≥ 99.9%, staleness < 5 min       |

---

## Archive Criteria (canonical — codified 2026-08-02)

> **RULED 2026-08-02** (operator ruling on `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 2d, option A): the
> `repo_gates`/`completion_gates`-based table this section used to carry is **Legacy schema (pre-2026-05-21)** — no
> current plan carries those fields, so no plan could ever satisfy it. Every real archival in this corpus already uses
> the bar below; this section now states that practice instead of the unsatisfiable legacy one.

**Archive eligibility rule:** a plan is eligible for archive when every todo is `- [x]` (zero open `- [ ]` checkboxes)
with cited evidence (repo@sha, verified reachable on the target branch, or an equivalent verification artifact), and it
is not `locked_by:` an active branch (a locked plan needs an explicit `[unlock-plan]` first). A plan is NOT archivable
just because the majority of todos are done, and it is NOT blocked from archiving by anything beyond these two
conditions. See `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` for the full 6-step ritual
(banner, referrer repoint, `git mv` into the dated `plans/archive/YYYY_MM/` subdir, etc.).

---

## YAML Frontmatter Schema (Canonical SSOT)

**SSOT reference**:
[`/codex/11-project-management/doc-frontmatter-schema.md`](/codex/11-project-management/doc-frontmatter-schema.md)

### Active plan / wrapper plan (in `plans/active/`)

```yaml
---
# Universal core (on EVERY plan)
doc_type: plan
title: <human-readable title>
summary: <one-line "what this plan does">
status: draft | active | blocked | paused | complete | cancelled | superseded
nature: ssot | guideline | process | design | spec | record | notes
asset_group: [cefi, defi, tradfi, sports, prediction, cross-cutting, ao, ci, infrastructure, ui, meta] # list; [] if N/A
stage: [meta] # list; pipeline phase(s): data, features, strategy, backtest, paper, live, execution, reporting, meta
repos: [repo-slug, ...] # list of repos this touches; [] if none / cross-cutting
scope: [engineer, admin] # audience: who this doc is for
tags: [backfill, audit, automation, ...] # open free-list; topical keywords
related: [other-plan-slug, ../epics/epic-slug.md] # list of related docs
created: YYYY-MM-DD

# Plan-specific required
parent_epic: <epic-slug> # REQUIRED — absence = ORPHAN = review-blocking
assigned_vm: planning | NA # dispatch routing: planning = orchestrator VM, NA = not dispatched
execution_scope: orchestrator-agent | local-only # declare on every plan; default orchestrator-agent
priority: P0 | P1 | P2 | P3
estimate_class: refactor | design | infra | brand-new | research
estimate_baseline_ai_days: <N> # raw estimate
estimate_calibrated_ai_days: <N> # baseline × class multiplier

# Plan-specific — work-philosophy (/codex/12-agent-workflow/work-philosophy.md)
assigned_role: backend-engineer | data-pipeline-engineer | ui-developer | infra-engineer | monitor | review
drift_direction: advance-code | correct-codex # which way this plan closes the codex↔codebase gap

# Plan-specific — reasoning-effort override (elective; model-tier-selection.md is the SSOT).
# Absent on BOTH → derived from assigned_role's thinking tier, else (no role either) from open
# todo-count (LARGE_PLAN_TODO_THRESHOLD split: xhigh at/below it, max above) — NEVER a silent
# "medium" default (2026-07-22 ruling). `effort:` wins over `thinking_tier:` when both are set.
effort: low | medium | high | xhigh | max # optional — direct override of the spawn `--effort` flag
thinking_tier: max | high | medium | mechanical | off | none # optional — extended-thinking level;
# max/high also imply effort=max/high unless `effort:` is explicit above; mechanical/off/none is the
# only way to turn thinking OFF (truly rote tasks — rename sweeps, config flips)

# Plan-specific optional
last_updated: YYYY-MM-DD
locked_by: live-defi-rollout | NA
locked_since: YYYY-MM-DD
context_scope: [/codex/path/to/ssot.md, plans/active/related-doc.md] # elective minimal reading-list; see doc-frontmatter-schema.md — populate this YOURSELF at authoring time (task_template.md §2a), don't just leave it for the next /context-scout sweep
depends_on: [epic-slug, plan-slug-YYYY_MM_DD] # prerequisites; enables ordering + gates archival
supersedes: [old-plan-slug] # list of plans made obsolete by this one
superseded_by: [new-plan-slug] # list of plans that replaced this one
entry_point_for:
  [live-plan-slug] # this plan is a curated index/redirect INTO the listed plan(s), which stay the
  # live execution surface — NOT a replacement (codified 2026-07-23, sports_master_closeout precedent). Distinct from
  # supersedes/superseded_by: those signal "safe to archive/deprioritize the old one"; entry_point_for signals
  # "these two plans are intentionally co-live, this one is the reading shortcut." A plan carrying entry_point_for
  # MUST NOT also claim in prose to "supersede" its target — say "is the entry point for" instead.
source: [audit-ref, operator request, ticket URL] # provenance
sequential:
  true # optional — SHIPPED (added 2026-07-14, verify-rerun-2 finding 224: was absent from this list —
  # STRICT serial ordering, task N waits for task N-1 `done`; see task_template.md §4 for full semantics
  # + `ao@ff6100ad` (`_wire_sequential_prereqs`) for the implementation)
plan_order:
  <N> # optional — SHIPPED (added 2026-07-14, verify-rerun-2 finding 224: was absent from this list —
  # same-priority todos dispatch in `(tier, priority, plan_order)` order; see task_template.md §4)
---
```

**`execution_scope`** (fundamental frontmatter field — declare on every plan; closed set of two — codified 2026-06-02)
controls whether the agent-orchestrator ingests the plan's `- [ ]` todos into its backlog:

- **`orchestrator-agent`** (the default when the field is ABSENT — backward-compatible, no backfill of existing plans):
  the orchestrator scans the plan and auto-derives backlog tasks (per `regen_backlog_from_plan.py`), which slots/workers
  pick up.
- **`local-only`**: the orchestrator skips the plan entirely (regardless of `assigned_vm`). Use for coordination /
  design / operator-driven plans whose work is done and verified locally by an operator, not dispatched to a worker.

Enforced in `agent-orchestrator/server/regen_backlog_from_plan.py` (`_parse_frontmatter_execution_scope` → skip on
`local-only`). There is no `hybrid` value.

**`status: draft`** (codified 2026-06-26) — a plan you are still authoring / have not finalised. The orchestrator **does
NOT ingest a `draft` plan's todos** (and prunes any already-queued tasks if you flip `active`→`draft`), so a
half-written plan never dispatches to a worker. **Flip to `status: active` when the plan is finalised** — that one edit
is the green-light. Enforced in `regen_backlog_from_plan.py` (`_parse_frontmatter_status` → skip on `draft`, shared with
`_prune_stale` via `_plan_contributes_briefs` so a flip-to-draft GCs its queued tasks too).

**`assigned_role`, `drift_direction`, plan sizing, and the per-task `Gate:`** (codified 2026-06-26; SSOT
[`/codex/12-agent-workflow/work-philosophy.md`](/codex/12-agent-workflow/work-philosophy.md)):

- **`assigned_role`** — the durable craft role that executes the plan. **Plans are role-homogeneous** (one role per
  plan); AO dispatch loads that role's boot prompt + model. Cross-role work is split into _dependent_ single-role plans
  at the epic level, never one mixed-role plan. The role set is grown organically (work-shipper roles only — a live
  trading decision-maker is not a role here).
- **`drift_direction`** — `advance-code` (the default; implement toward the codex target) or `correct-codex` (the codex
  doc is stale; this plan fixes it toward the codebase). Lets the epic track the gap in both directions.
- **Plan sizing (HARD).** A plan MUST be small enough for **one agent to complete start-to-finish** = one
  `quality-gates.sh`-green quickmerge unit (~one PR). If a plan can't be finished in one pass, the epic decomposition
  was wrong — split it. A tracker/SSOT doc may be big; a _dispatched_ plan may not. Use `estimate_calibrated_ai_days` as
  the sizing signal.
- **Per-task `Gate:` (acceptance criterion).** Every todo SHOULD carry an explicit, checkable `Gate:` (what proves it
  done — the test/command/artifact). Verification is at the shippable boundary (QG + quickmerge + review-agent
  regression check), not per-task; the `Gate:` is how "did we get what we wanted" stays checkable rather than a judgment
  call.
- **Unknowns surfaced mid-plan** → file an issue doc + escalate (worker → review/orchestrator) per the findings-triage
  ladder; do not silently absorb scope the plan didn't anticipate.

### Epic (in `plans/epics/`)

```yaml
---
name: <slug> # kebab-case, matches filename, NO date suffix
type: epic
tier: L0 | L1 | L2 | L3 | L4 | L5 # which layer this epic sits in
status: active | paused | cancelled # NEVER "complete" — epics are everlasting
priority: P0 | P1 | P2 | P3
assigned_vm:
  NA # REQUIRED field (presence; docspec `registry_or_na`) — value is `NA` on every CURRENT epic
  # (epic-owns-VM dispatch DROPPED, D2 2026-06-24 + single-VM architecture 2026-06-27); a legacy
  # `vm-<id>` value still validates but is OPTIONAL-HISTORICAL (archaeology only, never
  # dispatch-resolved) — (was: `vm-<id> # REQUIRED — registry-resolved VM that owns this epic`,
  # finding 220, 2026-07-14)
parent: master_to_live_defi_2026_05_23 # always the cutover master (until cutover ships)
owner: ikenna | harsh | claude-code
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
locked_by: live-defi-rollout
locked_since: YYYY-MM-DD
asset_group: cefi | defi | tradfi | sports | prediction | cross-cutting | ao | ci | infrastructure | ui | meta
related_plans:
  - plans/active/<sub-plan>.md # list grows as audits spawn new active plans
---
```

**Forbidden on epics**: `deadline:`, `estimate_class:`, `estimate_baseline_ai_days:`, `estimate_calibrated_ai_days:`.
Epics are everlasting; estimation lives on the active plans they reference.

**`assigned_vm` on epics — SUPERSEDED value-meaning, field still REQUIRED (synced 2026-07-14, finding 220)**: the
machine truth (`scripts/docs/docspec.py` `PER_TYPE["epic"]`) still requires this field PRESENT (kind `registry_or_na`),
so don't drop it — but the epic-owns-VM ownership meaning it used to carry is dropped. `NA` is the expected value on
every current epic; a legacy `vm-<id>` still validates against `orchestrator_vm_registry.yaml` (which retains the old
ids) but is OPTIONAL-HISTORICAL only — archaeology, never dispatch-resolved. SSOT: operator-locked decision **D2**
(`plans/epics/agent_operating_framework_master.md:129`, 2026-06-24 — "`assigned_vm` is a mandatory **per-plan** field;
epic-to-VM delegation is DROPPED for matching"), the `epics/README.md` supersession banner (lines 23-30), and
`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (single-VM, role-based dispatch, 2026-06-27).

### Legacy schema (active plans pre-2026-05-21 epic-foundation update)

```yaml
---
name: plan-slug # kebab-case slug, matches filename
overview: One-line description
type: code | deployment | business | infra | mixed

# Which epic this plan belongs to (LEGACY field; new plans use parent_epic: above)
epic: epic-code-completion | epic-deployment | epic-business | epic-infra | none

# Optional: paused/blocked by external dependency
status: active | blocked | paused

# Defines what gates ALL repos must reach before this plan is archivable
completion_gates:
  code: C5 # C0-C5 or "none"
  deployment: none # D1-D5 or "none"
  business: none # B1-B6 or "none"

# Per-repo gate progress (only repos this plan directly modifies)
repo_gates:
  - repo: some-repo
    code: C2 # highest code gate currently reached
    deployment: none
    business: none
  - repo: another-repo
    code: C0 # C0 = not started
    deployment: none
    business: none

depends_on: [] # plan slugs this depends on. ALONE it DOCUMENTS ordering + gates ARCHIVAL only and does NOT gate dispatch. WITH `gate_on_depends: true` (below), regen's `_wire_gate_on_depends_prereqs` reads it and makes every task of THIS plan wait on every task of the named upstream plan(s) — that is the author-facing inter-plan gate. NOT draft (draft = WIP only). See task_template.md §4 + "Citadel-Grade Planning Standards".
gate_on_depends: false # optional — set `true` to turn `depends_on` into a real DISPATCH gate (regen wires task-level `prereqs.completed_tasks` to the upstream plans' tasks; `dispatch.py` holds this plan's tasks until they are all `done`). Default false = `depends_on` is documentation-only. This is the ONLY way to express a cross-plan gate from a plan file.

todos:
  - id: task-id
    content: |
      - [ ] [SCRIPT] P0. Description of the task  # Cursor-friendly: [x] done, [ ] pending
    status: todo | in_progress | done | blocked
    blocked_by: other-plan-slug # optional, only if status: blocked
    note: ""
isProject: false
---
```

---

## Cursor-Friendly Todo Checkboxes (MANDATORY)

Cursor Plan Mode renders Markdown checkboxes. Every todo's **first content line** MUST start with a checkbox so Cursor
shows filled vs hollow circles correctly.

| Status                | Checkbox | Example                                           |
| --------------------- | -------- | ------------------------------------------------- |
| `status: done`        | `- [x]`  | `- [x] [SCRIPT] P0. Delete stale branch...`       |
| `status: pending`     | `- [ ]`  | `- [ ] [AGENT] P0. Fix BUG-1...`                  |
| `status: in-progress` | `- [ ]`  | `- [ ] [HUMAN] P1. Create...` (hollow until done) |

**Format:** `- [x]` or `- [ ]` (space inside brackets for pending) followed by the role tag `[SCRIPT]`, `[AGENT]`,
`[HUMAN]`, or `[HUMAN+AGENT]`, then the rest of the description.

**`[UI]` modifier (MANDATORY for UI todos — codified 2026-05-23):** Any todo that creates, modifies, or validates
behaviour in a UI repo (`unified-trading-system-ui`, `deployment-ui`, `user-management-ui`) MUST append `[UI]` to the
role tag — e.g. `[AGENT][UI]`, `[HUMAN][UI]`. This modifier triggers the playwright verification gate (§ 9 below).
Reviewer rejects ✅ ticks on `[UI]`-tagged todos that lack `pw:` evidence.

**Why:** Cursor reads the checkbox from the content; `status:` in YAML alone does not render filled circles. Without
this prefix, done tasks still appear hollow in the UI.

### Canonical form + automated hygiene (codified 2026-05-29)

Canonical form for any unchecked todo:

```
- [ ] [TAG] P<0-3>. <description>
```

Multi-tag is allowed (`[AGENT][UI] P0. ...` per the UI HARD RULE above). Sub-priority allowed (`P0.7.`, `P1.10.`).

**Why this matters for the autonomous loop**: `agent-orchestrator/server/regen_backlog_from_plan.py` ingests every
`- [ ]` line into the dispatcher backlog and extracts priority via `\bP[0-3]\b`. Lines **without a P-tag anywhere** get
priority `None` → dispatcher de-prioritizes → task rots in the queue. Non-canonical bracket placement (`[TAG][P<n>]`,
`[P<n>]` alone, etc.) still ingests but displays inconsistently in the dashboard.

**Two hygiene scripts ship with this convention:**

- `scripts/plan-hygiene/check_todo_format.sh` — HARD check wired into `run_hygiene_sweep.sh`. Flags todos with no
  P-priority (regen assigns `None`) as ❌ FAIL; non-canonical-style with priority present as ⚠️ WARN.
- `scripts/plan-hygiene/fix_todo_format.sh` — mechanical auto-fixer. Rewrites `[TAG][P<n>]`, `[P<n>][TAG]`,
  `[TAG] [P<n>]`, and bare `[P<n>]` (→ `[AGENT] P<n>.` default tag) to canonical. Run with `--apply` to write changes in
  place.

**Full hygiene stack doc** (4 silent-failure modes, severity ladder, cron schedules):
`/codex/12-agent-workflow/plan-hygiene.md`

**Closed set of canonical tags** (case-sensitive uppercase; PR to PLAN_FORMAT.md to add a new tag). **Updated
2026-08-02** (operator ruling on `plan_reconcile_parked_operator_decisions_2026_08_02.md` § 2c, option A): this list had
drifted from live practice — `task_template.md` §"`[TAG]` → craft role" already documented `[INFRA]`/`[DATA]`/
`[BACKEND]`/`[UI]`/`[REVIEW]` as the live per-task role-routing tags, and a corpus-wide count found `[DOC]`/`[DOCS]`/
`[PM]`/`[DIAG]`/`[DEVOPS]`/`[CI]` in active use across dozens to hundreds of docs each. Added below to match reality:

```
AGENT | SCRIPT | HUMAN | HUMAN+AGENT | AUDIT | DESIGN | SPEC | VERIFY | CONFIG | IMPLEMENT
DEFERRED | DELEGATED | UI
INFRA | DATA | BACKEND | REVIEW | CODE | DOC | DOCS | PM | DIAG | DEVOPS | CI
BLOCKED-CREDENTIALS | BLOCKED-OPERATOR-DECISION | BLOCKED-UPSTREAM-OUTAGE
BLOCKED-PLAYWRIGHT | BLOCKED-OPERATOR | BLOCKED-INFRA
```

Role routing for the AO-dispatch tags (per-task craft role, from `task_template.md`): `[INFRA]`→infra ·
`[DATA]`→data_engineering · `[BACKEND]`→backend_engineer · `[UI]`→ui_developer · `[REVIEW]`→review. Generic `[CODE]` /
`[SCRIPT]` / `[DOC]` / `[DOCS]` / `[PM]` / `[DIAG]` / `[DEVOPS]` / `[CI]` route to the plan's own `assigned_role`.

**Full hygiene reference**: `/codex/12-agent-workflow/plan-hygiene.md` — covers all 4 silent-failure modes, check-vs-fix
script pairing, cron schedules (plan-hygiene 05:00 UTC, blocker-reaper 04:00 UTC, orphan-ping every 4h), and the HARD vs
SOFT severity ladder. When in doubt about a format question, read that doc first.

### Sub-bullet checkboxes (explicit allowance, codified 2026-05-12)

Nested checkboxes under a parent todo are **allowed** when they represent atomic sub-tasks that ship together with the
parent (e.g. per-repo or per-asset-group flavours of the same shippable unit):

```markdown
- [x] [SCRIPT] P0. Sweep `category` → `asset_group` across the 5 asset-group repos
  - [x] cefi: instruments-service@<sha>
  - [x] defi: instruments-service@<sha>
  - [x] tradfi: instruments-service@<sha>
  - [ ] sports: blocked on URDI@<sha>
  - [ ] prediction: blocked on URDI@<sha>
```

Sub-bullet checkboxes do not satisfy the "first content line" rule on their own (Cursor renders them as nested items
under the parent's filled/hollow state). They are valid only as children of a parent `- [x]` / `- [ ]` checkbox; a plan
section consisting entirely of nested checkboxes without a parent is rejected.

````

---

## Citadel-Grade Planning Standards

Every plan MUST follow these standards. Agents creating plans that don't meet these standards MUST be corrected.

### 1. Pre-Audit Before Execution

Before writing any code, audit the blast radius:

- Search the entire workspace for every import/reference to symbols being moved, deleted, or renamed
- Build a **pre-audit manifest**: repo, file, line number, import statement, action needed
- Embed the manifest in the plan so executing agents don't need to re-scan
- If working with a subset of repos (background agent), document what you CAN'T verify

### 2. Plans, not phases — the DAG lives BETWEEN plans (updated 2026-06-26)

> **Supersedes the old "phases within a plan" model** per `/codex/12-agent-workflow/work-philosophy.md` L3/L4/L8. A
> **dispatched plan is small + role-homogeneous + one-agent-sized** (one `quality-gates.sh`-green quickmerge unit). The
> place to capture a multi-role / multi-concern effort is **separate small plans gated by dependencies**, NOT big phases
> inside one plan. Authoring flow: write the lengthy multi-phase doc (a *tracker* — L8) to dump everything, then **split
> each phase/concern into its own small plan, ALL born `status: draft`** so the backend never ingests a half-finished
> split. When the split is finalised and the tracker is deleted, **flip them ALL to `active`** — including the gated
> ones. `draft` is **WIP-only**; it is NOT how you express "wait for an upstream plan."
>
> **Two clean layers — never conflate them:**
>
> 1. **Ingest (regen):** every plan with a matching `assigned_vm` + `status: active` has its todos pulled into the
>    backlog. Ingest is dumb and complete — it does NOT decide ordering or parallelism.
> 2. **Dispatch (to a worker):** a queued task is held until its **task-level `prereqs`** are satisfied — a
>    `prereqs.prerequisites` flag (flipped true when the upstream is done + review-confirmed) and/or the upstream's task
>    ids in `prereqs.completed_tasks`. So a "gated" plan is `active` (ingested) but its tasks carry `prereqs`; they sit in
>    the backlog, undispatched, until the gate opens.
>
> **How an author creates those `prereqs`** (regen wires them — you never hand-edit `backlog.yaml`; there is NO per-todo
> prereq syntax): `sequential: true` chains each task to its predecessor (intra-plan serial); `depends_on` +
> `gate_on_depends: true` gates this whole plan on upstream plan(s) (cross-plan). `depends_on` **alone** (without
> `gate_on_depends`) is **documentation + archival only** (the depended-on plan can't archive first) — it does NOT gate
> dispatch. (A dependency is NOT a "blocked-question" and NOT the same as a `prereqs.prerequisites` flag — see
> work-philosophy + the AO blocked-questions contract.)

A **single small plan** still:

- declares clear success `Gate:`s per todo and a workspace-wide QG validation before it ships;
- may have a couple of **sequential steps**, but **no heavy cross-role phases** — if it needs a second role or a second
  shippable unit, that's a second plan with a dependency edge;
- marks any internal items PARALLEL or SEQUENTIAL explicitly.

The big tracker/epic draws the cross-plan dependency graph (ASCII or Mermaid); the small plan just lists its `depends_on`.

#### Parallelism — two levels, never conflated

"One small plan = one agent" and "parallelise for speed" are NOT in tension once you separate two levels:

- **Inside a plan (one agent, always).** Every item in a plan belongs to the **same** agent, which works it end-to-end
  with full context. The `PARALLEL`/`SEQUENTIAL` annotation on items is a **hint to that one owning agent** — it states
  the intra-plan order and where the agent MAY parallelise _internally_ (e.g. spin up its own sub-agents). It is **never**
  a signal to hand items to different workers. The backend enforces this with **plan-claiming**: when a plan's first task
  is dispatched to a slot, the rest of that plan's tasks are pinned to the same slot (`affinity=high`), so a plan's tasks
  never scatter across agents (`server/state_store/slots.py` `_claim_plan_for_slot`).
- **Across plans (where speed comes from).** Parallelism comes from having **more plans**, never from splitting one.
  Independent work → **separate small plans** → the backend dispatches them to **different agents concurrently**.
  Context-coupled-but-too-big sequential work → **multiple plans chained by `prereqs`** (context handed off via the
  codebase + the plan doc).

**The split test (apply when carving a tracker into plans — the axis is context-coupling):**

> _Could two items be done correctly by two strangers who never talk to each other?_ → **separate plans** (parallel
> agents; each loads its own context). _Do they need each other's output/context?_ → **same plan** (one agent, ordered).

Size each plan to one agent's worth (~one PR). **Parallelism granularity = the plan.** More parallelism → more plans;
more context locality → one (still-small) sequential plan. A plan containing parallel-independent items meant for
_different_ agents is mis-split — break it up.

### 3. No Technical Debt

- No backwards compatibility shims, re-exports of old paths, or deprecation wrappers
- Clean breaks: old implementation deleted, new implementation in place, consumers updated
- **Exception**: When working on a single repo without all downstream siblings available, backwards compatibility IS
  allowed temporarily. Document it as a follow-up todo.
- When all 60+ repos are available (full workspace): zero technical debt, update everything

### 4. Parallelization

- Maximize parallel execution. If items have no dependency, they MUST be marked PARALLEL
- Group independent items into parallel batches
- Use separate agents for parallel work where possible
- Document the parallelization strategy in the plan

### 5. Success Criteria

Every plan MUST declare explicit success criteria per phase:

- **Code gates**: quality-gates.sh pass, basedpyright clean, ruff clean
- **Test gates**: unit tests pass, integration tests pass (specify which)
- **Deployment gates**: D1-D5 (if applicable)
- **Business gates**: B1-B6 (if applicable)
- The final phase MUST include workspace-wide QG validation of all affected repos

### 6. Downstream Consumer Updates

When modifying shared libraries (UAC, UIC, UTL, UCI, UEI, UDC):

- Pre-audit identifies EVERY downstream consumer
- Plan includes explicit fix items for each affected repo
- No "fix later" — all consumers updated in the same plan
- Quality gates run on each affected downstream repo

### 7. Single Source of Truth

- Types/schemas belong in ONE place. UAC for external data normalization, UIC for internal.
- No service should self-declare types that exist in contracts libraries
- No re-definition of enums, dataclasses, or Pydantic models that already exist upstream
- Pre-audit should catch self-declared duplicates and include them in the fix manifest

### 8. Full-Execution Criterion (codified 2026-05-08)

Per CLAUDE.md HARD RULE "Plans Run To Actual Completion, Not Smoke-Test Green":

Every Tab in a daily work-split plan + every plan in `plans/active/` whose scope involves real infrastructure (cloud
provisioning, data movement, VM operations, migrations, backfills, reconcilers) MUST list per-phase **full-run**
completion criteria, not just code/test deliverables. Format:

```markdown
**Full-execution criterion** (per CLAUDE.md "Plans Run To Actual Completion" HARD RULE):

- ✅ <full-run criterion — exact data/state on real infra>.
  - **What ran**: <command + machine/VM-name + duration>.
  - **Verification**: <gcloud/aws CLI command + expected output + actual observed>.

**Handoff exception(s)** (if any):

- <criterion> deferred to <downstream-plan-path>:<phase-id>. Justification: <why downstream is right runner>.
```

**Reviewer rejection**: a Done definition with only code/test deliverables but no Full-execution subsection IS REJECTED.
A "Handoff exception" that doesn't name a real plan in `plans/active/` or `plans/epics/` IS REJECTED.

**Hard-stops** (the only legitimate operator-pauses): wallet private keys + custody endpoint approvals, live-trading
kill-switch arming, force-push to main, version 1.0.0 graduation, destructive ops beyond local working tree. Everything
else: agent has ADC admin on GCP `central-element-323112` + AWS `427895769566` and runs to completion.

### 8b. Evidence-backed completion — runtime-green claims cite a VERIFIED build (HARD RULE — codified 2026-06-28)

> **Why:** the recurring "found-green-but-actually-FAILURE" class — an agent flips a todo to `- [x]` claiming a Cloud
> Build / deploy / promote went green from its own self-report, when the OVERALL build was FAILURE. Every such over-claim
> in the CI/CD effort was caught ONLY by an independent Cloud Build API check. This rule makes that check structural.

Any `- [x]` todo whose completion is a **runtime infra claim** — a Cloud Build / image build / cloud deploy / LDR→main
promote went **green / SUCCESS** — MUST cite structured evidence on the checkbox line or its continuation lines:

```markdown
- [x] ✅ ... <the claim> ... Evidence: cloudbuild=<build-id>[,<build-id> ...]
```

- The build-id is the GCP Cloud Build id (a UUID); cite the OVERALL build that is SUCCESS, **not one green step**. Verify
  it yourself: `gcloud builds describe <id> --region=asia-northeast1 --project=central-element-323112 --format='value(status)'`
  must return `SUCCESS`. Multiple ids and other token kinds (e.g. `gha=<run-url>`) are allowed; the gate verifies every
  `cloudbuild=<id>`.
- **Enforced by** `unified-trading-pm/scripts/quality_gates/check_evidence_backed_completion.py` (PM post-gate): sub-rule
  A (strict-0) FAILS the gate if any cited `cloudbuild=<id>` resolves to a terminal NON-success; sub-rule B (baselined
  ratchet) flags a runtime-green claim that cites NO evidence. A code-ship claim (`<repo>@<sha>` + "QG green") is NOT a
  runtime infra claim and needs no build-id — its evidence is the commit + the local QG sentinel.
- The persistent UAT/QA review agent (`unified-trading-pm/agents/review.md`) RUNS this verification (triggers/polls the
  build, then `describe → SUCCESS`) before allowing the checkbox flip — never trust a build-id from an agent self-report.

### 8c. Plan commit-SHA evidence — `<repo>@<sha>` citations must resolve to a REAL commit (codified 2026-07-30)

> **Why:** § 8b explicitly carves a code-ship claim (`<repo>@<sha>`) out of the Cloud Build gate on the theory its
> evidence is "the commit + the local QG sentinel" — but nothing previously verified that commit actually EXISTS. A
> `docs(plans):` flip commit cited `resolved_by: market-tick-data-service@6efb252b` for a SHA that does not exist
> anywhere in that repo's history (not local, not on GitHub) — a fabricated completion-evidence citation. See
> `plans/archive/issues/mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`.

Any `resolved_by:` frontmatter value or `- [x]` todo citation of the form `<repo>@<sha>` — where `<repo>` is the exact
directory name of a repo checked out as a sibling clone — is verified by running `git cat-file -t <sha>` in that repo's
clone, not by trusting the self-report.

- **Enforced by** `unified-trading-pm/scripts/quality_gates/check_plan_commit_sha_evidence.py` (PM post-gate): a
  baselined ratchet (`scripts/quality_gates/plan_commit_sha_evidence_baseline.yaml`) — pre-existing corpus drift is
  grandfathered, a NEW citation that doesn't resolve regresses the gate. Re-baseline with `--baseline-write` only after
  confirming a flagged citation is genuine pre-existing drift, not a fresh fabrication.
- Scope is deliberately narrow: only `<repo>@<sha>` where `<repo>` is an EXACT sibling-clone directory name is checked
  (abbreviated forms like `mtds@...`/`uac@...` are ambiguous and are not matched at all — a soft-skip by construction,
  mirroring § 8b's "can't check it from here" posture for an absent Cloud Build auth).

### 8d. Prod DATA-mutation evidence-backed completion (codified 2026-08-11)

> **Why:** the "found-green-but-actually-not-verified" class also applies to prod data mutations — restamp/backfill
> row counts, manifest backstamps, GCS object renames/deletes, terraform/tofu state ops. A `- [x]` claiming "restamped
> 12,006 rows" or "renamed M GCS objects" without a cited, independently-resolvable artifact is unverifiable — the same
> gap §8b closed for build/deploy claims. Review flagged this class 3 independent times (tofu-state, do_rename
> content-equality, prediction restamp row-counts) before consolidation into the issue doc
> `/plans/active/issues/prod_mutation_evidence_artifact_gap_2026_08_03.md`, whose operator ruling ("YES, extend it,"
> 2026-08-06) this section codifies.

Any `- [x]` todo whose completion is a **prod data-mutation claim** — asserting a specific outcome from a script
that mutated production data (restamp, backfill, GCS rename/delete, manifest rewrite, tofu/terraform state change,
data migration, or similar) — MUST cite structured evidence on the checkbox line or its continuation lines:

```markdown
- [x] ✅ ... restamped 12,006 rows ... Evidence: vm-log=prediction-phantom-fix/run.log
- [x] ✅ ... renamed 42 GCS objects ... Evidence: gcs-op=pred/canonical-cutover/rename-2026-08-01
- [x] ✅ ... removed resource from tofu state ... Evidence: tofu-state=module.defi_warehouse.aws_s3_bucket.raw
```

Accepted evidence artifact types (non-exhaustive — the requirement is a DURABLE, INDEPENDENTLY-RESOLVABLE reference
a reviewer can check against live infra; the exact token form is elective, same as §8b's `cloudbuild=<id>`):

| Artifact type    | Format                               | Example                                                    |
| ---------------- | ------------------------------------ | ---------------------------------------------------------- |
| `vm-log`         | `vm-log=<vm-prefix>/<log-path>`      | `vm-log=pred-phantom-fix/run.log`                          |
| `manifest-delta` | `manifest-delta=<path-or-reference>` | `manifest-delta=pred-prd/_manifest_status/2026-08-01.json` |
| `gcs-op`         | `gcs-op=<operation-reference>`       | `gcs-op=pred/rename-2026-08-01`                            |
| `tofu-state`     | `tofu-state=<resource-reference>`    | `tofu-state=module.defi_warehouse.aws_s3_bucket.raw`       |
| `cloudbuild`     | `cloudbuild=<build-id>`              | (existing §8b convention; use when the mutation ran IN a Cloud Build) |

A data-mutation claim is identified by the co-occurrence of a **mutation verb** (restamp, backfill, rename, delete,
wipe, tofu/terraform state, migrate, regenerate, recompute, etc.) AND an **outcome/quantity signal** (a row count,
"completed", "applied", "processed", "N rows/shards/objects") in the same clause of a `- [x]` todo block.

- **Enforced by** `unified-trading-pm/scripts/quality_gates/check_evidence_backed_completion.py` (PM post-gate):
  sub-rule C (baselined ratchet) flags a data-mutation claim that cites NO `Evidence:` ref. Baselined so legacy plans
  ratchet down; new mutation claims without evidence push the count up → regression. A mutation claim that DOES cite
  an `Evidence:` ref satisfies the gate — the verification of the cited artifact itself is the reviewer's
  responsibility (same posture as §8b's Cloud Build id: the gate checks the citation EXISTS; the reviewer resolves it).
- **Not in scope**: code-ship claims (`<repo>@<sha>` + "QG green") are already covered by §8c's commit-SHA check and
  need no additional evidence. A todo that cites `<repo>@<sha>` AND describes a data mutation is covered by this rule
  — add an `Evidence:` ref for the mutation outcome in addition to the commit citation.

### 9. UI Verification Gate (HARD RULE — codified 2026-05-23)

Any todo tagged `[UI]` (see Cursor-Friendly Todo Checkboxes above) MUST NOT be ticked `- [x] ✅` until **both**
conditions are met and **evidenced in the tick line**:

**Condition 1 — Playwright route smoke passes (pw:L2 ✓)**

```bash
cd <ui-repo> && npx playwright test --project=chromium tests/smoke/
# Must exit 0 — zero console errors, every route loads, auth redirects correct
```

For fleet VM workers where a dev server cannot run: todo stays `- [ ] [BLOCKED-PLAYWRIGHT]` until a slot with UI access
verifies. Do not fake the tick.

**Condition 2 — Regression guard written or updated**

A spec file in one of these paths MUST be written (new feature) or updated (modified feature) to catch reverting the
change:

| Change type                          | Regression guard location                          |
| ------------------------------------ | -------------------------------------------------- |
| New widget / widget behaviour change | `tests/widgets/<widget-id>.test.tsx` (L1.5)        |
| New route or route behaviour change  | `tests/smoke/routes.spec.ts` or new entry (L2)     |
| New playbook scenario / UX flow      | `tests/playbooks/<flow>.spec.ts` (L3a)             |
| Strategy execute / trade history UI  | `tests/e2e/strategies/<archetype>.spec.ts` (L3b)  |
| Visual layout / component snapshot   | `tests/visual/<component>.spec.ts` (L4)            |

The spec file path MUST be cited in the tick evidence. Writing a test that passes vacuously (no assertions) is a
violation — reviewer reads the diff.

**Evidence format (MANDATORY — reviewer rejects without this):**

```markdown
- [x] ✅ [AGENT][UI] P1. Add ManualTradeGateDialog approve/deny flow — unified-trading-system-ui@<sha> | pw:L2 ✓ | regression: tests/e2e/manual_trade_gate.spec.ts
```

Minimal fields: `repo@sha` + `pw:L2 ✓` + `regression: <path>`. Any UI tick missing `pw:` or `regression:` is
**review-blocking** — same weight as a missing `docs(plans):` flip.

**Scope.** This gate applies regardless of whether the change is a new feature, a bug fix, a refactor, or a copy
change. If the file touched is in a UI repo: the gate applies.

**Relation to ui-testing-layers.md.** The 8 layers in `/codex/06-coding-standards/ui-testing-layers.md` define WHAT
each layer tests and WHEN it runs. This section defines the plan-level enforcement: a todo cannot be declared done
until the appropriate layer passes and a regression guard exists. The two documents compose — do not weaken either.

---

## Filename convention (codified 2026-05-08; updated 2026-05-21 epic-foundation model)

| Directory                | Extension                       | Why                                                                                            |
| ------------------------ | ------------------------------- | ---------------------------------------------------------------------------------------------- |
| `plans/epics/`           | `<slug>.md` (NO date suffix)    | Epics are everlasting — no deadline-coupled naming                                              |
| `plans/active/`          | `<slug>_YYYY_MM_DD.md`          | Active plans + wrapper plans are dated work units                                              |
| `plans/active/issues/`   | `<slug>_YYYY_MM_DD.md`          | Issue docs / audit pool — surfaces UNACKED scope                                                |
| `plans/audit/results/`   | `<slug>_YYYY_MM_DD.md`          | Timestamped output of an audit-pool row                                                         |
| `plans/archive/`         | `<slug>.plan.md`                | Frozen historical state — DO NOT rename (breaks archaeology in commit messages + external refs) |
| `plans/ai/`              | `<slug>.plan.md`                | Staging dir; promotion to `active/` renames to `<slug>_YYYY_MM_DD.md`                          |

**Rule.** Epics use plain `.md` with NO date suffix (everlasting). Active plans + wrapper plans use
`<slug>_YYYY_MM_DD.md` (dated). Reviewers reject `.plan.md` filenames in `plans/active/` or `plans/epics/`.

**Deprecated**: `.epic.md` double-extension form was the 2026-05-08 May-23 deadline-specific naming; superseded by
everlasting epic model 2026-05-21. Existing `.epic.md` files rename to plain `.md` during the consolidation sweep. The
2026-05-08 sweep (commits `aa72177d` rename + `cca954ff` cross-ref rewrite) was the original codifying boundary; the
2026-05-21 epic-foundation update is the current boundary.

---

## Epic-foundation model (codified 2026-05-21; supersedes 2026-05-08 3-layer model)

```
master_to_live_defi_2026_05_23.md   ← cutover master (dated, one-shot; archives after May-23)
        │
        ├── plans/epics/<slug>.md            ← EPICS — everlasting planning orchestrators (19 epics × 5 tiers)
        │       │                              Each has assigned_vm + priority blocks of active plans
        │       │
        │       └─ each references ↓
        │
        ├── plans/active/<slug>_YYYY_MM_DD.md ← ACTIVE PLANS — dated work units; carry parent_epic:
        │       │                              Spawned when audits surface gaps
        │       │
        │       └─ each references ↓ (codex/, code, scripts/)
        │
        ├── plans/active/issues/<slug>_YYYY_MM_DD.md  ← AUDIT POOL — UNACKED scope; Ikenna/Harsh pick rows
        │       │
        │       └─ row picked → audit conducted → ↓
        │
        └── plans/audit/results/<slug>_YYYY_MM_DD.md  ← AUDIT DOCS — timestamped review output
                │
                └─ findings → upgrade existing active plans OR spawn new ones → epic absorbs them
```

- **Epics** are everlasting planning orchestrators — one per persistent code surface; no date suffix; no `estimate_*`
  fields; required `assigned_vm` + `tier` + `priority` frontmatter; body has P0/P1/P2/P3 priority blocks of all assigned
  active plans.
- **Active plans** (and wrapper remediation plans) are dated work units — each carries `parent_epic:` frontmatter +
  `estimate_class` + `estimate_baseline_ai_days` + `estimate_calibrated_ai_days`.
- **Audits** are timestamped reviews — produced on the planning VM (Ikenna + Harsh, Opus 4.7 1M); identify gaps that
  spawn new active plans; recurring cadence.
- **No orphan active plans** — every active plan declares `parent_epic:`. Orphans are review-blocking.
- **Cutover master** is NOT an epic — it's a dated one-shot tracking May-23 readiness across all 19 epics.

Full epic-flow SSOT: [`plans/epics/README.md`](epics/README.md). VM topology spec:
[`active/orchestrator_master.md`](active/orchestrator_master.md).

---

## ai/ vs active/ Directory Rules

### `plans/ai/` — AI-generated, unreviewed

- Plans generated by AI analysis, audit runs, or autonomous agents go here
- Files here use `.plan.md` (legacy convention; promotion renames to `.md`)
- **Cannot** be referenced as `blocked_by` in active plans
- **Cannot** influence archive status of active plans
- Must be explicitly promoted to `plans/active/` by the user

### Promotion workflow (ai/ → active/)

1. User reviews the plan in `plans/ai/`
2. Check `plans/active/INDEX.md` for slug conflicts and competing `repo_gates`
3. Resolve conflicts (merge, supersede, or split the plan)
4. `git mv plans/ai/<slug>.plan.md plans/active/<slug>.md` — rename to `.md` on promotion (preserves history via similarity heuristic)
5. Add to `INDEX.md` under the correct epic section
6. Commit: `chore: promote <slug> from ai/ to active plans`

### `plans/active/` — User-approved

- Only user-approved plans live here
- Every file must use the `.md` suffix (post-2026-05-08 sweep)
- Every file must have `completion_gates` and `repo_gates` in YAML frontmatter
- `INDEX.md` must be updated whenever a plan is added or archived

---

## Epic Structure

Plans are grouped into epics representing the current focus of the trading system build.

| Epic ID                | Name                                      | Current?         |
| ---------------------- | ----------------------------------------- | ---------------- |
| `epic-code-completion` | Code Completion — all plans reach C5      | **YES — active** |
| `epic-deployment`      | Deployment Readiness — all plans reach D3 | No               |
| `epic-business`        | Business Readiness — all plans reach B6   | No               |
| `epic-infra`           | Infrastructure hardening (cross-cutting)  | Ongoing          |

Plans that are infra/deployment type always enforce their D-gates regardless of which epic is active.

---

## Structural Order (MANDATORY)

> **Corrected 2026-07-12** (doc-reconciliation autofix, finding 381, `plan_reconciliation_operator_decisions_2026_07_11.md`
> §A2 "50 reclassified" blanket ruling): this section previously described the `todos:`-in-frontmatter-YAML mechanism,
> which only matches the **Legacy schema (pre-2026-05-21)** above — the doc's own canonical Active-plan/wrapper-plan
> schema (§ "YAML Frontmatter Schema (Canonical SSOT)", lines 78–118) has no `todos:` frontmatter field, and the actual
> mechanism is body-markdown `- [ ]`/`- [x]` checkboxes per the "Cursor-Friendly Todo Checkboxes (MANDATORY)" section
> below — matching real practice and what `regen_backlog_from_plan.py` ingests. (was: "ALL todos and completion gates
> MUST appear in the frontmatter YAML block.")

Plans MUST follow this section order:

1. **Frontmatter** (canonical fields per "YAML Frontmatter Schema (Canonical SSOT)" above — `doc_type`, `title`,
   `status`, `parent_epic`, `assigned_vm`, etc.)
2. **Notes / Context** (architecture, mermaid diagrams, references, and the todos themselves as body-markdown
   checkboxes — see "Cursor-Friendly Todo Checkboxes (MANDATORY)" below)

**Why:** The conflict-resolution-agent reads `head -250` per plan. If todos are buried after
250 lines of notes, the agent cannot see them during conflict resolution. Keep actionable
content (including the todo checkboxes) near the top.

**Rule:** Todos are body-markdown `- [ ]`/`- [x]` checkboxes (per "Cursor-Friendly Todo Checkboxes (MANDATORY)"),
kept near the top of the doc, NOT inside the frontmatter YAML block. The frontmatter carries the plan's declared
metadata (status, gates, ownership) per the canonical schema above.

---

## Plan Locking

Plans that are actively being implemented can be locked to prevent premature archival.

### Frontmatter fields:
```yaml
locked_by: live-defi-rollout   # Branch actively implementing this plan
locked_since: 2026-03-16       # ISO date when lock was set
````

### Rules:

- **Agents MUST NOT archive locked plans** even if all todos are done. The plan-health-agent checks `locked_by` and
  skips archival for locked plans.
- **Only a human with `[unlock-plan]` in the commit message** can delete or archive a locked plan. PM's quality-gates.sh
  blocks deletion of locked plans without this tag.
- **Plan-level `depends_on`:** If plan A lists `depends_on: [plan-B-name]`, plan B cannot be archived while plan A is
  active. The plan-health-agent checks this.
- When your implementation is complete, remove `locked_by` and `locked_since` from frontmatter to allow normal archival.
- **Agent unlock protocol:** Agents MAY ask a human to unlock a plan when all todos are genuinely complete: "Plan X is
  locked but all todos are done. Should I unlock it?" If approved, the agent removes `locked_by`/`locked_since` and
  includes `[unlock-plan]` in the commit message. Agents MUST NEVER unlock plans autonomously — always ask first.

---

## Daily Work-Split Plan Shape (codified 2026-05-10)

Every daily work-split plan (`plans/active/work_split_<YYYY_MM_DD>_<operator>.md`) MUST include a **slot↔theme
assignment table** that pins which permanent worktree slot owns which theme today. The slot is the durable identity
(`.tabs/<N>/<repo>/` on branch `tab/<operator>/<N>`); the theme rotates daily per the operator's load-balancing.

Required section in every daily work-split plan:

```markdown
## Today's slot assignments

| Slot | Theme                       | Plan-of-record                                                |
| ---- | --------------------------- | ------------------------------------------------------------- |
| 1    | main orchestrator + on-call | (this LEDGER)                                                 |
| 2    | cefi-master                 | plans/active/cefi_master.md                                   |
| 3    | writegate Wave 4 slice (b)  | plans/active/writegate_honest_coverage_endtoend_2026_05_06.md |
| 4    | (idle)                      | —                                                             |
```

**Slot-reset discipline.** When a slot's theme changes from yesterday's, the operator MUST run
`bash unified-trading-pm/scripts/dev/setup-tab-worktrees.sh --reset-slot <N>` BEFORE work begins, to verify clean state

- rebase the slot's branch onto `origin/live-defi-rollout`. Pinned to the daily work-split plan's "Daily reset"
  checklist.

**Mirror in operator orchestrator LEDGER.** The same slot↔theme table must appear in the operator's
`<operator>_orchestrator/LEDGER.md` "Today's slot assignments" section as the bootstrap-read source for fresh tab
agents.

**Spawn prompts reference the slot path.** Every spawn-prompt block in the work-split plan MUST cite the spawned tab's
worktree path: `Your slot is <N>. Your worktree is at ${WORKSPACE_ROOT}/.tabs/<N>/`.

SSOTs:

- Codex doc: [`/codex/05-infrastructure/per-tab-worktrees.md`](/codex/05-infrastructure/per-tab-worktrees.md) — the
  3-tier hierarchy + fixed-slot model + slot-reset discipline.
- Reconciliation:
  [`/codex/05-infrastructure/plan-aware-merge-resolution.md`](/codex/05-infrastructure/plan-aware-merge-resolution.md) —
  slot-master merge resolution protocol.
- Plan that codified it: [`plans/active/per_agent_worktrees_2026_05_10.md`](active/per_agent_worktrees_2026_05_10.md).

Reviewers reject daily work-split plans without the slot↔theme table.

---

## SSOT References

- This file: `unified-trading-pm/plans/PLAN_FORMAT.md`
- ~~Cursor rule / Plan placement / Workflow~~ — the 3 filenames previously cited here
  (`cursor-rules/core/plan-readiness-gates.mdc`, `cursor-rules/core/plan-placement.mdc`,
  `cursor-rules/workflow/plans-to-deployable-workflow.mdc`) never existed under those names in the tree even before it
  was archived 2026-08-02 (operator ruling on `plan_reconcile_parked_operator_decisions_2026_08_02.md` § docs-reconcile
  item 11) — pre-existing dangling references, not newly broken by the archival. The tree's surviving content is at
  `plans/archive/cursor-rules_2026_08_02/`.
- Sub-agent rules: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` §9
- INDEX: `unified-trading-pm/plans/active/INDEX.md`
- Per-tab worktrees: `unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md`
- Plan-aware merge resolution: `unified-trading-pm/codex/05-infrastructure/plan-aware-merge-resolution.md`

```

```
