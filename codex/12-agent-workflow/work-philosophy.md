---
doc_type: codex-ssot
title: Work Philosophy — codex-as-target, plan-as-unit, role-per-plan
summary:
  The operating method for how work flows — codex is the target state, the codebase is the current state, an epic is the
  bidirectional gap, and a plan is one small role-homogeneous step a single cheap agent completes start-to-finish; the
  durable SSOT behind plan sizing, role dispatch, and where the expensive judgment lives.
status: current
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [work-philosophy, plan-sizing, role-based-dispatch, drift-closing, codex-target, model-tier, boot-prompts]
related:
  [
    canonical-plan-flow.md,
    ../../plans/epics/README.md,
    ../../plans/PLAN_FORMAT.md,
    ../06-coding-standards/model-tier-selection.md,
  ]
created: 2026-06-26
authoritative_for:
  [
    work-philosophy,
    codex-as-target-state,
    bidirectional-drift,
    plan-as-unit-of-work,
    plan-sizing,
    role-per-plan-dispatch,
    durable-role-boot-prompts,
    judgment-at-authoring,
  ]
referenced_by:
  [../../plans/epics/agent_operating_framework_master.md, ../../plans/epics/README.md, ../../plans/PLAN_FORMAT.md]
owner: ikenna
last_reviewed: 2026-06-26
code_refs: []
---

# Work Philosophy — codex-as-target, plan-as-unit, role-per-plan

> **SSOT for the operating _method_** — how work flows from intent to shipped change so that a _cheap_ agent can execute
> well. The machinery that runs it (registry, retrieval index, dispatch) is `agent_operating_framework_master` +
> `orchestrator_master`; this doc owns the _discipline_. **Throughput and correctness come from the structure of epics
> and plans, not from a smarter model.**

## The core model

```
codex docs  =  TARGET state   (what the system should be)
codebase    =  CURRENT state  (what the system is today)
epic        =  the GAP between them — bidirectional, everlasting
plan        =  ONE small step that closes part of the gap (a single day's work)
agent       =  one role, one cheap model, completes one plan start-to-finish
```

Finishing a plan moves the codebase one step toward the codex-described target. Epics never complete — there is always
more gap as audits surface it.

## The regression this corrects

AO began as a work-dispatcher to get throughput against existing plans. It worked — then plans grew to **1000–2000
lines** and quality regressed. The cause is structural, not model intelligence: a 1000-line plan had **recreated the
epic inside the plan** and handed the whole gap to a single agent. The fix is to restore the epic/plan boundary, size
plans for one cheap agent, and concentrate the expensive reasoning at authoring time.

## Locked decisions (L1–L11)

Read the relevant entry before authoring or executing.

- **L1 — Codex is the target, codebase is the current, epic is the gap, plan is the step.** Plans are the daily
  increments; epics are everlasting drift-closers.

- **L2 — The gap is bidirectional; codex de-staling is emergent, not a project.** An epic tracks both
  _code-behind-codex_ (advance the code) **and** _codex-behind-code_ (the doc is stale; the code is already right).
  Every plan declares its direction. **Why:** codex was written day-one and its update cadence lapsed, so treating it as
  an infallible target would generate wrong work. Modelling both directions lets the same surprise-escalation mechanism
  (L7) catch stale codex, so codex correction happens continuously as plans touch it — never a heroic up-front rewrite
  (which would be the new scope-creep). Codex is taken **at face value now** and corrected incrementally.

- **L3 — The plan is the unit of work, sized so ONE agent completes it start-to-finish.** One plan = one coherent change
  that `quality-gates.sh`-greens and quickmerges as a single unit (~one PR). "One agent" = one logical owner _across
  context resets_ (deterministic `--session-id` + `--resume` supports multi-window plans). **Why:** big plans caused the
  regression; the fix is the epic/plan boundary, not a style preference. **Parallelism granularity = the plan, never
  sub-plan.** Intra-plan item order (`PARALLEL`/`SEQUENTIAL`) is a HINT to that one owning agent (where it may fan out
  _internally_ via sub-agents) — not a cross-worker split; the backend enforces this with **plan-claiming** (a plan's
  tasks pin to the first slot that claims one — `slots.py:_claim_plan_for_slot`). Cross-agent speed comes from **more
  plans** (independent work → separate plans → parallel agents), gated by `prereqs`. Split axis = context-coupling: two
  items doable by strangers who never talk → separate plans; items needing each other's output → same plan. SSOT:
  `plans/PLAN_FORMAT.md` → "Parallelism — two levels".

- **L4 — Role is a plan-level field (`assigned_role`); plans are role-homogeneous.** Cross-role work decomposes into
  _dependent plans_ at the epic level (a backend plan + a UI plan + a dependency edge), integrated by contract per the
  tier architecture — never a half-backend/half-UI plan. **Why:** one agent does the whole plan, so its role, context,
  and model stay constant; mixing roles reintroduces the context bloat removed from CLAUDE.md.

- **L5 — Push judgment to authoring-time; execution is mechanical and checkable.** The expensive reasoning
  (architecture, decomposition, "why A over B") happens at epic→plan authoring (operator / PM role, Opus). The plan
  hands the executor _resolved decisions + an explicit acceptance `Gate:` per task_, so a cheap model executes well.
  Model tier follows: Opus/operator at authoring + hard-verify of risky tasks; **Sonnet for execution.** **Why:**
  generalizes the per-plan model-tier split (D12 of `orchestrator_consolidated_remaining` — "architecture decided → no
  reasoning premium → Sonnet") to the default shape of every plan. Tier SSOT:
  [`../06-coding-standards/model-tier-selection.md`](../06-coding-standards/model-tier-selection.md).

- **L6 — Verification is at the shippable boundary, not per-task.** Agent completes the plan → runs `quality-gates.sh` →
  ships via quickmerge (the enforced workspace gate) → the review agent reviews + checks regression. A green→red QG
  transition **is** a detected regression. **No per-task QG** (overkill) and **no smart "is this what we wanted"**
  detector. **Why:** the workspace already batch-gates ("gate once over a batch → per-unit commits"); a plan sized to
  one pass makes this natural.

- **L7 — Unknowns surfaced during execution escalate by blast radius (agent does NOT judge "correctness").** When an
  agent trips over something the plan didn't anticipate — including "codex says X, the code does Y, and Y is right" — it
  escalates the _surprise_ up a tiered ladder, it does not silently absorb it:
  - **minor + in-scope** → fix in place, same commit.
  - **a work / regression surprise** → hand to the **review agent** (the quality gate closest to the diff).
  - **big blast radius — it would change the PLAN or scope** → **write an issue doc** (so the context is not lost) and
    escalate to the **operator** (human); a plan/scope change is an authoring-time decision (L5), not a worker call.

  This is light escalation (far less than a full escalation-pipeline) and maps onto the workspace findings-triage rule
  ("big finding → NOTIFY OPERATOR + issue doc"). **Why:** discovery without betting on agent cleverness — structure over
  intelligence; the issue doc preserves context across the hand-off.

- **L8 — Two artifact classes; never conflate them.** A **tracker/SSOT doc** (an epic + its living backlog;
  consolidation docs) is _allowed_ to be big. An **executable work-order** (the dispatched plan) MUST be small. The epic
  is the only thing allowed to be big; it _emits_ small plans. **Why:** consolidation passes produced good SSOT
  mega-docs that then got dispatched as if they were work-orders — the direct cause of the 1000-line-plan regression.
  **Split lifecycle + gating (two layers, never conflated):** the small plans a tracker emits are **born `status:
  draft`** (WIP — the backend skips them); when the split is final and the tracker is deleted, **flip them ALL to
  `active`**, gated ones included. Then: **(1) Ingest** — regen pulls every `active` plan matching `assigned_vm` into the
  backlog and **never reads `depends_on`** (by design); **(2) Dispatch** — a queued task is held off workers until its
  **task-level `prereqs`** are satisfied (a `prereqs.prerequisites` flag flipped when the upstream is done +
  review-confirmed, and/or the upstream's task ids in `completed_tasks`). So a gated plan is `active` but its tasks carry
  `prereqs` — it sits ingested-but-undispatched until the gate opens. `draft` is WIP-only and `depends_on` is
  docs+archival-only; **neither is the upstream-gate** — task `prereqs` is. SSOT: `plans/PLAN_FORMAT.md`.

- **L9 — Role boot prompts = lean, durable, role-scoped context.** Each role gets its own long-standing boot prompt
  (`agents/<role>.md`) carrying only what that role needs — generalizing the CLAUDE.md 60 kB→6 kB trim. AO dispatch
  loads a plan's `assigned_role` → that role's durable boot prompt + that role's model. **The minimal cut needs no
  broker / `(role,domain)` routing** — just tag → boot prompt → model. **Why:** a UI agent doesn't need data-pipeline
  context and vice versa; lean context is cheaper and more accurate.

- **L10 — Frontmatter: cheap mechanical now, expensive organic.** Mechanical inserts (`doc_type`, `status`, `nature`
  defaults, empty fields) on remaining docs now; expensive fields (`summary`, `tags`, `nature` judgments, `status`
  normalization) updated _as docs are touched during work_. Plan-frontmatter inserts fold into the plan-format pass; the
  enforcing gate on _active plans_ comes last; codex frontmatter stays lazy. **Why:** the full-corpus sweep is a token
  sink and must not sit on the critical path.

- **L11 — Codex taken at face value now; corrected later, emergently (per L2).** Fix the method first; codex content
  corrections accrue continuously (L7) plus a periodic plan-health/reconciler consolidation. **Why:** a
  codex-rewrite-first is exactly the ambition being cut.

## The three context layers

An executing agent gets exactly three things; only one is per-plan:

1. **Always-on workspace rules** — the trimmed CLAUDE.md (~6 kB). Every agent, every task.
2. **Role boot prompt — DURABLE.** "You are a backend engineer: how we write/ship backend code, what you do and don't
   do, how you escalate." Authored once per role, reused across every plan assigned to that role (L9).
3. **The plan — EPHEMERAL.** The specific tasks, the resolved decisions, the acceptance `Gate:`s, and the codex docs it
   references. The only thing that changes per dispatch.

`agent = always-on rules + durable role boot prompt + one ephemeral plan`. AO reads the plan's `assigned_role`, loads
the durable boot prompt + that role's model, and hands it the one plan.

## Role taxonomy — craft, not domain

Roles are **durable craft/function personas, NOT domain × craft.** A `defi-backend-engineer` per-domain role would be a
combinatorial explosion (domains × crafts) that re-bakes domain context into every persona — recreating the 60 kB
problem. Instead:

- The **durable role** = the craft persona (backend-engineer, data-pipeline-engineer, UI-developer, quant-dev,
  infra/devops,
  - the operational roles main & review). Grown organically, kept small (≤~10–15).
- **Domain specificity is per-plan**, supplied by the plan + the codex docs it references through frontmatter (this is
  what grep-native retrieval is for). The boot prompt carries craft + a _pointer-map_ to domain docs; the plan +
  retrieval fill in which domain.
- **Work-shipper roles only.** These roles _produce code_ and ship plans. A live trading **decision-maker** ("trader")
  is a different category (strategy/`trading_agent_master` runtime), not a plan-executor — excluded from this taxonomy.

## Cross-references

- [`canonical-plan-flow.md`](canonical-plan-flow.md) — the audit→plan→backlog→worker→ship loop this method runs inside.
- [`../../plans/epics/README.md`](../../plans/epics/README.md) — epic/plan-system SSOT (bidirectional gap, plan-as-unit,
  role-per-plan, tracker-vs-work-order).
- [`../../plans/PLAN_FORMAT.md`](../../plans/PLAN_FORMAT.md) — `assigned_role`, the mandatory `Gate:`, the
  drift-direction tag, the sizing rule.
- [`../../plans/epics/agent_operating_framework_master.md`](../../plans/epics/agent_operating_framework_master.md) — the
  machinery (roles, retrieval, dispatch) that implements this method, and the restructure workstreams.
- [`../06-coding-standards/model-tier-selection.md`](../06-coding-standards/model-tier-selection.md) — the model-tier
  rule L5 generalizes.
