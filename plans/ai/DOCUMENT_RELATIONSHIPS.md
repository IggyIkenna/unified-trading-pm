# Document Relationships - Plans Directory

**Purpose**: Visual map of how documents relate to each other  
**Updated**: 2026-02-23

---

## 🗺️ DOCUMENT HIERARCHY

```
📁 .cursor/plans/

├── 📋 AGENT FRAMEWORK (Reusable)
│   ├── AGENT_TASK_TEMPLATE.md ─────┐
│   │   (Generic safeguards)        │
│   │                                ├──► Include in ALL agent prompts
│   └── CODING_STANDARDS_ENFORCEMENT.md ─┘
│       (No empty fallbacks, no Any)
│
├── 🎯 CURRENT TASK (Type Cleanup)
│   ├── TYPE_CLEANUP_AGENT_PROMPT.md ──┐
│   │   (Specific work: 3 agents)      │
│   │   ├── References: AGENT_TASK_TEMPLATE
│   │   ├── References: CODING_STANDARDS_ENFORCEMENT
│   │   └── References: type_cleanup_parallel.plan.md
│   │
│   ├── type_cleanup_parallel.plan.md ─┤
│   │   (Work allocation, patterns)    │
│   │                                   ├──► Type cleanup workflow
│   ├── HANDOFF_FOR_NEXT_AGENT.md ─────┤
│   │   (Quick start)                  │
│   │                                   │
│   └── TYPE_FIXES_EXPLANATION.md ─────┘
│       (How we fixed processors)
│
├── 📊 STATUS & CONTEXT
│   ├── SESSION_2_COMPLETE_SUMMARY.md
│   ├── SESSION_2_FINAL_STATUS.md
│   ├── SESSION_2_COMPLETION_STATUS.md
│   ├── REFACTORING_STATUS_CHECKPOINT.md
│   └── TYPE_FIXING_FINAL_REPORT.md
│
└── 📖 NAVIGATION
    └── README_PLANS.md (this index)
```

---

## 🔗 KEY RELATIONSHIPS

### Template → Standards → Prompt Flow:

```
1. AGENT_TASK_TEMPLATE.md (safeguards)
   ↓ includes
2. CODING_STANDARDS_ENFORCEMENT.md (no empty fallbacks, no Any)
   ↓ both used by
3. TYPE_CLEANUP_AGENT_PROMPT.md (specific task)
   ↓ references
4. type_cleanup_parallel.plan.md (Pattern Library)
```

### Read Order for New Agent:

```
1. HANDOFF_FOR_NEXT_AGENT.md (60 sec) ← START HERE
   ↓
2. TYPE_CLEANUP_AGENT_PROMPT.md (5 min) ← Copy-paste prompt
   ↓ references
3. AGENT_TASK_TEMPLATE.md (5 min) ← Learn safeguards
   ↓ references
4. CODING_STANDARDS_ENFORCEMENT.md (5 min) ← Learn standards
   ↓ optional
5. type_cleanup_parallel.plan.md (10 min) ← Pattern Library
```

**Total**: 15-25 minutes context gathering

---

## 📋 DOCUMENT PURPOSES

### Reusable Templates (Use for ANY task):

| Document | Purpose | Size |
|----------|---------|------|
| **AGENT_TASK_TEMPLATE.md** | Generic safeguards (backup, NEVER rules, return format) | 8.3K |
| **CODING_STANDARDS_ENFORCEMENT.md** | Standards with examples (empty fallbacks, Type Any) | 11K |

**Use**: Copy these into ANY agent prompt (type cleanup, refactoring, feature work, etc.)

### Task-Specific (Type cleanup only):

| Document | Purpose | Size |
|----------|---------|------|
| **TYPE_CLEANUP_AGENT_PROMPT.md** | Specific prompt for type cleanup | 7.8K |
| **type_cleanup_parallel.plan.md** | Work allocation + Pattern Library | 21K |
| **HANDOFF_FOR_NEXT_AGENT.md** | Quick start guide | 4.9K |
| **TYPE_FIXES_EXPLANATION.md** | How we fixed processors | 3.4K |

**Use**: For type cleanup task only

### Status & Context:

| Document | Purpose | Size |
|----------|---------|------|
| **SESSION_2_COMPLETE_SUMMARY.md** | Latest comprehensive summary | 7.7K |
| **TYPE_FIXING_FINAL_REPORT.md** | Type fixing progress | 8.5K |
| **REFACTORING_STATUS_CHECKPOINT.md** | Overall progress tracker | Updated |

---

## 🎯 FOR DIFFERENT USE CASES

### Creating a NEW Agent Task (NOT type cleanup):

**Copy**:
1. `AGENT_TASK_TEMPLATE.md` - Safeguards section
2. `CODING_STANDARDS_ENFORCEMENT.md` - Standards block

**Customize**:
- Task description
- Files to work on
- Success criteria
- Verification commands

**Result**: Safe, standards-compliant agent prompt

### Launching Type Cleanup (Current Task):

**Copy**:
- `TYPE_CLEANUP_AGENT_PROMPT.md` - Already includes both templates + standards

**Read**:
- `HANDOFF_FOR_NEXT_AGENT.md` - Quick start

**Launch**: 3 parallel agents

### Understanding Current Status:

**Read**:
- `SESSION_2_COMPLETE_SUMMARY.md` - Latest status
- `REFACTORING_STATUS_CHECKPOINT.md` - Progress

---

## 🔍 CROSS-REFERENCES

### AGENT_TASK_TEMPLATE.md:
- Uses: CODING_STANDARDS_ENFORCEMENT.md (line 35: "See CODING_STANDARDS_ENFORCEMENT.md")
- Used by: TYPE_CLEANUP_AGENT_PROMPT.md (line 13: "follow AGENT_TASK_TEMPLATE.md")
- Used by: Any future agent tasks

### CODING_STANDARDS_ENFORCEMENT.md:
- Used by: AGENT_TASK_TEMPLATE.md (standards section)
- Used by: TYPE_CLEANUP_AGENT_PROMPT.md (coding standards block)
- References: .cursor/rules/no-empty-fallbacks.mdc
- References: .cursor/rules/no-type-any-use-specific.mdc

### TYPE_CLEANUP_AGENT_PROMPT.md:
- References: AGENT_TASK_TEMPLATE.md (safeguards)
- References: CODING_STANDARDS_ENFORCEMENT.md (standards)
- References: type_cleanup_parallel.plan.md (Pattern Library)
- References: HANDOFF_FOR_NEXT_AGENT.md (quick start)

---

## ✅ NAVIGATION SUMMARY

**Want to launch type cleanup?**
→ Read `HANDOFF_FOR_NEXT_AGENT.md` → Copy `TYPE_CLEANUP_AGENT_PROMPT.md`

**Want to create new agent task?**
→ Copy `AGENT_TASK_TEMPLATE.md` + `CODING_STANDARDS_ENFORCEMENT.md`

**Want to understand standards?**
→ Read `CODING_STANDARDS_ENFORCEMENT.md`

**Want to understand current status?**
→ Read `SESSION_2_COMPLETE_SUMMARY.md`

**All documents now properly cross-referenced** ✅
