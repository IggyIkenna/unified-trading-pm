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

## Archive Criteria by Plan Type

| Type         | Minimum gate to archive                     | Notes                                                           |
| ------------ | ------------------------------------------- | --------------------------------------------------------------- |
| `code`       | C5 for all repos in `repo_gates`            | Archivable during code-completion epic                          |
| `infra`      | D3 for all repos in `repo_gates`            | Must prove staging integration even during code-completion epic |
| `deployment` | D3 minimum                                  | Same as infra                                                   |
| `business`   | B6 (user approved) + B3 KPIs met            | Unit tests alone are insufficient                               |
| `mixed`      | Highest required gate across declared types | E.g., `code + infra` → D3                                       |

**Archive eligibility rule:** A plan is eligible for archive when ALL repos in `repo_gates` have reached the gate level
in `completion_gates`, AND the plan type's minimum gate is satisfied. A plan is NOT archivable just because the majority
of todos are done — every repo must reach the required level.

---

## YAML Frontmatter Schema

### Active plan / wrapper plan (in `plans/active/`)

```yaml
---
title: <human-readable title>
parent_epic: <epic-slug> # REQUIRED — absence = ORPHAN = review-blocking
priority: P0 | P1 | P2 | P3 # rolls up to epic's priority block
status: active | blocked | paused | complete | cancelled
execution_scope: orchestrator-agent | local-only # FUNDAMENTAL — declare on every plan; absent ⇒ orchestrator-agent
estimate_class: refactor | design | infra | brand-new | research
estimate_baseline_ai_days: <N> # raw estimate
estimate_calibrated_ai_days: <N> # baseline × class multiplier (see codex/08-workflows/estimation-calibration.md)
locked_by: live-defi-rollout
locked_since: YYYY-MM-DD
related_plans:
  - ...
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

### Epic (in `plans/epics/`)

```yaml
---
name: <slug> # kebab-case, matches filename, NO date suffix
type: epic
tier: L0 | L1 | L2 | L3 | L4 | L5 # which layer this epic sits in
status: active | paused | cancelled # NEVER "complete" — epics are everlasting
priority: P0 | P1 | P2 | P3
assigned_vm: vm-<id> # REQUIRED — registry-resolved VM that owns this epic
parent: master_to_live_defi_2026_05_23 # always the cutover master (until cutover ships)
owner: ikenna | harsh | claude-code
created: YYYY-MM-DD
last_updated: YYYY-MM-DD
locked_by: live-defi-rollout
locked_since: YYYY-MM-DD
asset_group: cefi | defi | tradfi | sports | prediction | cross-cutting | infrastructure | meta
related_plans:
  - plans/active/<sub-plan>.md # list grows as audits spawn new active plans
---
```

**Forbidden on epics**: `deadline:`, `estimate_class:`, `estimate_baseline_ai_days:`, `estimate_calibrated_ai_days:`.
Epics are everlasting; estimation lives on the active plans they reference.

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

depends_on: [] # list of plan slugs this plan is blocked by

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
`codex/12-agent-workflow/plan-hygiene.md`

**Closed set of canonical tags** (case-sensitive uppercase; PR to PLAN_FORMAT.md to add a new tag):

```
AGENT | SCRIPT | HUMAN | HUMAN+AGENT | AUDIT | DESIGN | SPEC | VERIFY | CONFIG | IMPLEMENT
DEFERRED | DELEGATED | UI
BLOCKED-CREDENTIALS | BLOCKED-OPERATOR-DECISION | BLOCKED-UPSTREAM-OUTAGE
BLOCKED-PLAYWRIGHT | BLOCKED-OPERATOR | BLOCKED-INFRA
```

**Full hygiene reference**: `codex/12-agent-workflow/plan-hygiene.md` — covers all 4 silent-failure modes, check-vs-fix
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

### 2. Phased Execution DAG

Plans MUST define execution phases with clear dependencies:

- **Phase N** items run in parallel within the phase
- **QG gates** between phases — next phase cannot start until prior phase QG passes
- Mark items as PARALLEL or SEQUENTIAL explicitly
- Draw the dependency graph (ASCII or Mermaid) in the plan context section

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

**Relation to ui-testing-layers.md.** The 8 layers in `codex/06-coding-standards/ui-testing-layers.md` define WHAT
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

Plans MUST follow this section order:

1. **Frontmatter** (name, overview, type, status, completion_gates, depends_on, todos with checkboxes)
2. **Notes / Context** (architecture, mermaid diagrams, references)

**Why:** The conflict-resolution-agent reads `head -250` per plan. If todos are buried after
250 lines of notes, the agent cannot see them during conflict resolution. Keep actionable
content at the top.

**Rule:** ALL todos and completion gates MUST appear in the frontmatter YAML block. Notes,
architecture context, Mermaid diagrams, and references go AFTER the closing `---` of frontmatter.

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

- Codex doc: [`codex/05-infrastructure/per-tab-worktrees.md`](../codex/05-infrastructure/per-tab-worktrees.md) — the
  3-tier hierarchy + fixed-slot model + slot-reset discipline.
- Reconciliation:
  [`codex/05-infrastructure/plan-aware-merge-resolution.md`](../codex/05-infrastructure/plan-aware-merge-resolution.md)
  — slot-master merge resolution protocol.
- Plan that codified it: [`plans/active/per_agent_worktrees_2026_05_10.md`](active/per_agent_worktrees_2026_05_10.md).

Reviewers reject daily work-split plans without the slot↔theme table.

---

## SSOT References

- This file: `unified-trading-pm/plans/PLAN_FORMAT.md`
- Cursor rule: `unified-trading-pm/cursor-rules/core/plan-readiness-gates.mdc`
- Plan placement: `unified-trading-pm/cursor-rules/core/plan-placement.mdc`
- Workflow: `unified-trading-pm/cursor-rules/workflow/plans-to-deployable-workflow.mdc`
- Sub-agent rules: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` §9
- INDEX: `unified-trading-pm/plans/active/INDEX.md`
- Per-tab worktrees: `unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md`
- Plan-aware merge resolution: `unified-trading-pm/codex/05-infrastructure/plan-aware-merge-resolution.md`

```

```
