# START HERE - Agent Task Execution

**For**: New Sonnet 4.5 session
**Goal**: Execute work via sub-agents ONLY (context preservation + cursor rules enforcement)
**Structure**: 1 template + 3 executable tasks

**⚠️ CRITICAL: SUB-AGENTS ARE MANDATORY** - Master NEVER edits files directly!

---

## 🎯 WHY SUB-AGENTS ARE MANDATORY (Not Optional!)

**Context Preservation**:
- Without sub-agents: Master reads 30+ files → 500K tokens → starts forgetting cursor rules → violations creep in
- With sub-agents: Sub-agents read files → master gets 2K summaries → stays under 200K → remembers ALL cursor rules

**Cursor Rules Enforcement**:
- Master role: Orchestrate, review, enforce standards (cursor rules ALWAYS fresh in context)
- Sub-agent role: Execute work (may lose rules, but master catches violations in review)
- Review loop: Master reviews ALL changes, resumes sub-agents if violations found

**Cost Efficiency**:
- Sub-agents use fast model (~$0.75/1M tokens)
- Master uses Sonnet 4.5 (~$9/1M tokens) only for orchestration
- Net savings: 70-80% vs master doing all work

**YOU MUST NEVER EDIT FILES DIRECTLY** - Always launch sub-agents!

---

## 📁 DIRECTORY STRUCTURE

```
.cursor/plans/
├── tasks/           ← EXECUTABLE TASKS (you run these)
│   ├── START_HERE.md (this file)
│   ├── TEMPLATE.md (copy for new tasks)
│   ├── TASK_1_ADD_QUALITY_CHECKS.md
│   ├── TASK_2_FIX_VIOLATIONS.md
│   └── TASK_3_TYPE_CLEANUP.md
│
├── contexts/        ← CONTEXT FOR SUB-AGENTS (they read these)
│   ├── CODING_STANDARDS.md (standards reference)
│   ├── SESSION_2_SUMMARY.md (what's been done)
│   ├── TYPE_FIXES_EXPLANATION.md (patterns)
│   └── [Other context files]
│
└── [root plans]     ← HISTORICAL (background reference)
    └── service_structure_standardization_*.plan.md, etc.
```

---

## 🚀 TO EXECUTE (Simple 3-Step - ALL USE SUB-AGENTS)

### Step 1: Add Quality Checks (30 min, 2 sub-agents REQUIRED)
```
Execute .cursor/plans/tasks/TASK_1_ADD_QUALITY_CHECKS.md in full
```
**Master launches 2 agents** (services group + libraries group), reviews results

### Step 2: Fix Violations (1-2 hours, 4 sub-agents REQUIRED)
```
Execute .cursor/plans/tasks/TASK_2_FIX_VIOLATIONS.md in full
```
**Master launches 4 agents** in parallel, reviews all changes, resumes if violations

### Step 3: Type Cleanup (2-3 hours, 3 sub-agents REQUIRED)
```
Execute .cursor/plans/tasks/TASK_3_TYPE_CLEANUP.md in full
```
**Master launches 3 agents** (orchestrator, aggregator, handlers), iterative resume to 0 errors

**That's it!** Each task MANDATES sub-agents. Master orchestrates ONLY, never edits directly.

---

## 🎓 HOW TASKS ACCESS OTHER PLANS

Each task doc explicitly references context:

**Example from TASK_2**:
```
Sub-Agent prompt includes:
"Read .cursor/plans/contexts/CODING_STANDARDS.md for patterns"
"Reference: instruments_service/processors/cefi_processor.py (working example)"
"See .cursor/plans/service_structure_standardization_*.plan.md for full context"
```

**Sub-agents CAN access any plan** - you just tell them which files to read in their prompt!

---

## 📋 TO CREATE NEW TASKS (SUB-AGENTS MANDATORY)

**⚠️ ALL NEW TASKS MUST USE SUB-AGENTS** - Follow TEMPLATE.md structure:

1. Open `tasks/TEMPLATE.md`
2. Copy structure (includes mandatory sub-agent usage)
3. Fill in:
   - Goal
   - **Number of sub-agents required** (minimum 1, recommend 2-4)
   - Sub-agent allocation (which repos/files per agent)
   - Context files they should read
   - Verification commands (master reviews)
   - Resume pattern (for corrections)
4. Save as `tasks/TASK_X_[NAME].md`
5. Execute it!

**NEVER create tasks with direct execution** - sub-agents preserve master context!

---

## 🔒 SAFEGUARDS (Master Enforces for ALL Sub-Agents)

**Every task includes these safeguards**:

**Before launch**:
- Backup branches created (rollback safety)
- Agent IDs saved (for resume)

**Sub-agent execution**:
- NEVER: Skip tests, add type: ignore without fixing, use .get(x,{}), use Type Any
- MUST: Fix root causes, test frequently, report back with structured results

**After completion**:
- Master reviews ALL changes against cursor rules
- Master verifies canonical patterns used (fail loud, specific types, manual retry)
- Master spot-checks tests + quality gates
- Master resumes agents if violations found

**Master approval required** - sub-agents NEVER auto-commit, always report back!

---

## ✅ WATERTIGHT CHECKLIST

- [x] One template (`tasks/TEMPLATE.md`)
- [x] Three executable tasks (TASK_1, TASK_2, TASK_3)
- [x] Clean directory structure (tasks/, contexts/)
- [x] Tasks explicitly use Task tool in prompts
- [x] Tasks reference context docs (sub-agents can read)
- [x] Safeguards built into every task
- [x] Simple execution (copy-paste prompt)

**Ready for new Sonnet 4.5 session!** ✅

---

## 📊 YOUR CONTEXT BUDGET

**Master Agent (You)**:
- Cursor rules: 90K
- Task prompts: 20K (3 tasks)
- Sub-agent summaries: 20K (7 agents × 3K each)
- User conversation: 20K
- **Total: ~150K tokens** ✅ 85% context still available!

**Sub-Agents** (11 total across 3 tasks):
- 4 in Task 2 (fix violations)
- 4 in Task 3 (type cleanup)
- 3 possible resumes (if needed)
- Each gets own 1M context
- Each reads only their files
- You get small summaries back
- **Total working memory: 11M+ tokens!**

**This is why sub-agents are MASSIVELY beneficial!** 🚀

---

**Location**: `/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks/`

**Unified execution plan:** See `.cursor/plans/code_optimizations_and_ci_cd_alignment/UNIFIED-SETUP-AND-EXECUTION-PLAN.md` for canonical order. First run: `TASK_CICD_PHASE1_FOUNDATION.md` (CI/CD Phase 1 — blocks Master Plan).

**Next**: Open `TASK_CICD_PHASE1_FOUNDATION.md` (recommended) or `TASK_1_ADD_QUALITY_CHECKS.md` and execute!
