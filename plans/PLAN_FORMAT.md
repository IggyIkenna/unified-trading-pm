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

```

---

## ai/ vs active/ Directory Rules

### `plans/ai/` — AI-generated, unreviewed

- Plans generated by AI analysis, audit runs, or autonomous agents go here
- **Cannot** be referenced as `blocked_by` in active plans
- **Cannot** influence archive status of active plans
- Must be explicitly promoted to `plans/active/` by the user

### Promotion workflow (ai/ → active/)

1. User reviews the plan in `plans/ai/`
2. Check `plans/active/INDEX.md` for slug conflicts and competing `repo_gates`
3. Resolve conflicts (merge, supersede, or split the plan)
4. Move file to `plans/active/` with `.plan.md` suffix
5. Add to `INDEX.md` under the correct epic section
6. Commit: `chore: promote <slug> from ai/ to active plans`

### `plans/active/` — User-approved

- Only user-approved plans live here
- Every file must use the `.plan.md` suffix
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

## SSOT References

- This file: `unified-trading-pm/plans/PLAN_FORMAT.md`
- Cursor rule: `unified-trading-pm/cursor-rules/core/plan-readiness-gates.mdc`
- Plan placement: `unified-trading-pm/cursor-rules/core/plan-placement.mdc`
- Workflow: `unified-trading-pm/cursor-rules/workflow/plans-to-deployable-workflow.mdc`
- Sub-agent rules: `unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md` §9
- INDEX: `unified-trading-pm/plans/active/INDEX.md`
```
