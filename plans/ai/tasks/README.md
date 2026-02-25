# Tasks Directory - Execute These

**Purpose**: Executable task documents that **MANDATE** sub-agent usage  
**For**: Sonnet 4.5 sessions (preserves context via sub-agents)

**⚠️ CRITICAL: ALL TASKS MUST USE SUB-AGENTS** - No direct execution allowed!

---

## 📁 FILES

**Template**:
- `TEMPLATE.md` - Copy this structure for any new task (SUB-AGENTS MANDATORY)

**Current Tasks** (Execute in order):
1. `TASK_1_ADD_QUALITY_CHECKS.md` - Add checks (30 min, 2 Task sub-agents REQUIRED)
2. `TASK_2_FIX_VIOLATIONS.md` - Fix 24 repos (1-2 hours, 4 Task sub-agents REQUIRED)
3. `TASK_3_TYPE_CLEANUP.md` - Fix type errors (2-3 hours, 3 Task sub-agents REQUIRED)

**Navigation**:
- `START_HERE.md` - How to execute tasks

---

## 🚀 EXECUTION

**Say this**:
```
Execute .cursor/plans/tasks/TASK_1_ADD_QUALITY_CHECKS.md in full
```

**Or**:
```
Open .cursor/plans/tasks/TASK_1_ADD_QUALITY_CHECKS.md and copy the prompt section
```

**Tasks explicitly use Task tool** - sub-agents launch automatically!

---

## 🎯 WHY SUB-AGENTS ARE MANDATORY

**Context Preservation** (CRITICAL):
- Master agent: Stays under 200K tokens → cursor rules NEVER compressed
- Sub-agents: Do heavy lifting in their own 1M contexts
- Result: 7M+ total working memory across all agents

**Cursor Rules Adherence**:
- Master agent: Enforces standards (rules always fresh in context)
- Sub-agents: Execute work (can lose rules, but master reviews)
- Review loop: Master catches violations, resumes sub-agent with corrections

**Watertight Execution**:
- Backup branches (rollback safety)
- NEVER rules enforced (master reviews all changes)
- Standards verification (quality gates + tests)
- Report back (no auto-commit, master approves)

**Cost Efficiency**:
- Sub-agents use fast model (~$0.75/1M tokens)
- Master uses Sonnet 4.5 (~$9/1M tokens)
- Net savings: 70-80% vs master doing all work

---

**Ready to execute!** Open TASK_1 and go! 🚀
