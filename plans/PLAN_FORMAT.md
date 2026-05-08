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

```yaml
---
name: plan-slug # kebab-case slug, matches filename
overview: One-line description
type: code | deployment | business | infra | mixed

# Which epic this plan belongs to (for INDEX tracking)
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

**Why:** Cursor reads the checkbox from the content; `status:` in YAML alone does not render filled circles. Without
this prefix, done tasks still appear hollow in the UI.

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

---

## Filename convention (codified 2026-05-08)

| Directory                 | Extension       | Why                                                                                          |
| ------------------------- | --------------- | -------------------------------------------------------------------------------------------- |
| `plans/active/`           | `<slug>.md`     | Native markdown preview in Cursor / VS Code / GitHub web UI                                  |
| `plans/epics/` (`*.md`)   | `<slug>.md`     | Same as active                                                                               |
| `plans/epics/` (`*.epic.md`) | `<slug>.epic.md` | Distinguishes May-23 deadline epics from granular masters in the same dir; previewed natively |
| `plans/archive/`          | `<slug>.plan.md` | Frozen historical state — DO NOT rename, breaks archaeology in commit messages + external refs |
| `plans/ai/`               | `<slug>.plan.md` | Same as archive — staging dir; promotion to `active/` renames to `.md`                       |

**Rule.** New plans land in `plans/active/<slug>.md` (or `plans/epics/<slug>.md` for granular masters / `<slug>.epic.md` for May-23 epics). Reviewers reject `.plan.md` filenames in `plans/active/` or `plans/epics/`. The 2026-05-08 sweep (commits `aa72177d` rename + `cca954ff` cross-ref rewrite) is the codifying boundary.

---

## 3-Layer Plan Model (codified 2026-05-08)

```
master_to_live_defi_2026_05_23.md   ← umbrella-of-epics (May-23 cutover master)
        │
        ├── plans/epics/*.epic.md   ← May-23 deadline epics (domain-target wrappers)
        │       │
        │       └─ each references ↓
        │
        └── plans/epics/*.md        ← granular masters (asset_group umbrellas)
                │
                └─ each references ↓
        │
        └── plans/active/*.md       ← granular sub-plans (one workstream each)
                │
                └─ each references ↓
                       (codex/, code, scripts/)
```

- **Epics** orchestrate domain targets for May 23; they consume granular masters + sub-plans.
- **Masters** are asset_group umbrellas (cefi / tradfi / sports / predictions / ml_and_features / etc.); they consume sub-plans.
- **Sub-plans** are single-workstream tactical plans; they own todos.
- None of the layers duplicates content — each adds orchestration above the layer below.

See `plans/epics/README.md` for the canonical epic list and consumed-plans tables.

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

## SSOT References

- This file: `unified-trading-pm/plans/PLAN_FORMAT.md`
- Cursor rule: `unified-trading-pm/cursor-rules/core/plan-readiness-gates.mdc`
- Plan placement: `unified-trading-pm/cursor-rules/core/plan-placement.mdc`
- Workflow: `unified-trading-pm/cursor-rules/workflow/plans-to-deployable-workflow.mdc`
- Sub-agent rules: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` §9
- INDEX: `unified-trading-pm/plans/active/INDEX.md`

```

```
