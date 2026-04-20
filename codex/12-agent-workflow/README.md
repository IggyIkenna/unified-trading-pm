---
scope: [engineer]
---

# 12 — Agent Workflow

Agent operating procedures for the Unified Trading System. Authoritative agent rules are in `.cursor/rules/*.mdc`
(synced from `unified-trading-pm/cursor-rules/`).

**For agent rules:** `.cursor/rules/*.mdc` **For active task list:**
`unified-trading-pm/plans/cursor-plans/consolidated_remaining_work.plan.md` **For task templates:**
`unified-trading-pm/plans/tasks/`

---

## Active Guides

| File                        | Purpose                                                                               |
| --------------------------- | ------------------------------------------------------------------------------------- |
| `AGENT-TASKING-GUIDE.md`    | How to assign work to agents via GitHub Issues; priority rules, auto-merge thresholds |
| `FAILURE_RECOVERY.md`       | Recovery procedures when quality gates fail or agent tasks stall                      |
| `HUMAN_REVIEW_CHECKLIST.md` | Detailed review checklist for P0/P1 PRs                                               |

---

## Superseded Content (now in cursor rules)

| Was here                     | Now in                                                                             |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| WORKFLOW_OVERVIEW            | `sub-agent-workflow-standard.mdc` + `agents-follow-cursor-rules.mdc`               |
| TASK_TEMPLATE                | `unified-trading-pm/plans/tasks/cursor/START_HERE.md`                              |
| TASK_CLASSIFICATION          | `ai-task-classification.mdc`                                                       |
| WORKER_AGENT_INSTRUCTIONS    | `agents-follow-cursor-rules.mdc`                                                   |
| LOCAL_VS_CLOUD_ORCHESTRATION | `parallel-agent-execution.mdc`                                                     |
| QUICK_REFERENCE              | `anti-patterns-quick-reference.mdc`                                                |
| cloud-orchestration-spec.md  | Moved to `unified-trading-codex/04-architecture/cloud-agent-orchestration-spec.md` |

---

## Archived

`archived/` — two files retained pending ADR extraction:

- `workflow-design-decisions.md` — rationale for current cursor rules architecture (review for ADRs)
- `TECHNICAL_ARCHITECTURE.md` — original workflow system architecture (review for ADRs)
