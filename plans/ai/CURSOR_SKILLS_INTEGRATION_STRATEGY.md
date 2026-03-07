# Cursor Skills Integration Strategy

**Context:** Vibe coding (prompt-driven), 30+ repos, microservices, 114 rules, 28+ plans. Physical code is minimal;
orchestration via prompts, plans, and rules.

## Goal

Integrate Cursor skills so agents automatically apply the right workflows when plans, rules, and codebase complexity
intersect — without re-prompting or forgetting context.

---

## 1. Plan-to-Skill Mapping

**Pattern:** One skill per plan category (or per high-value workflow).

| Plan category              | Skill name                | Trigger terms                                  |
| -------------------------- | ------------------------- | ---------------------------------------------- |
| Schema normalization       | schema-normalization-plan | schema normalization, output_schemas, Pydantic |
| Quality gates / quickmerge | quickmerge-workflow       | quickmerge, quality gates, merge               |
| Deployment / hardening     | deployment-hardening      | deployment, hardening, phase3                  |
| Lobster multi-repo         | lobster-multi-repo        | lobster, 30 repos, systematic                  |
| Audit remediation          | audit-remediation         | audit, remediation, technical debt             |

**Skill structure:**

- Follow all workspace cursor rules
- Read plan from unified-trading-pm/plans/active/
- Use sub-agents for multi-repo; uv not pip; quickmerge not git push
- For external libs: append "use context7" to prompts

---

## 2. Rule-Aware Skills (Always-On Reminders)

- **workspace-context-inject** — "Follow cursor rules; plans in unified-trading-pm; uv not pip; quickmerge not git push;
  delete deprecated, no parallel paths."
- **sub-agent-reminder** — When launching Task: "Include at TOP: Follow workspace cursor rules; uv not pip; search
  unified libraries before implementing."

---

## 3. Workflow Skills (Chained Actions)

| Workflow       | Key steps                                                                       |
| -------------- | ------------------------------------------------------------------------------- |
| Quickmerge     | Check --dep-branch if deps differ; run quickmerge; never git reset --hard       |
| Quality gates  | Run per-repo; timeout 120 basedpyright source_dir; no standalone basedpyright . |
| Plan execution | Read plan; create todos; launch sub-agents with rule reminder                   |

---

## 4. Discovery and Triggers

Description: Include WHAT + WHEN. Match plan names, rule tags, common prompts (roll out, audit, harden, migrate).

---

## 5. Use Context7

Per context7-usage.mdc: For external libs, append "use context7" to prompts. Skills involving external APIs should
include this.

---

## 6. Placement

- Workspace-wide: .cursor/skills/ in workspace or unified-trading-pm
- Reference plans from unified-trading-pm/plans/active/

---

## 7. Implementation Order

1. workspace-context-inject (lightweight)
2. quickmerge-workflow (high frequency)
3. execute-plan (generic plan executor)
4. Plan-specific skills as plans go live

---

## Reference

- create-skill: ~/.cursor/skills-cursor/create-skill/SKILL.md
- Rules: unified-trading-pm/cursor-rules/
- Plans: unified-trading-pm/plans/active/, plans/ai/
- Sub-agent: cursor-rules/core/sub-agent-workflow-standard.mdc
