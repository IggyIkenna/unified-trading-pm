# Contexts Directory - For Sub-Agents to Read

**Purpose**: Context documents that sub-agents reference  
**Usage**: Task prompts tell sub-agents which files to read here

---

## 📚 FILES

### **CODING_STANDARDS.md** (11K)
**What**: No empty fallbacks, no Type Any, fail loud patterns  
**Used by**: All sub-agents  
**Contains**: Good vs bad examples, quality gate checks

### **SESSION_2_SUMMARY.md** (9K)
**What**: What's been done (processors complete, 90% done)  
**Used by**: Type cleanup agents (understand current state)

### **TYPE_FIXES_EXPLANATION.md** (3.5K)
**What**: How we fixed processors (decorator removal, explicit types)  
**Used by**: Type cleanup agents (proven patterns)

### **TYPE_FIXING_FINAL_REPORT.md** (8.7K)
**What**: Complete type fixing results (39 errors fixed)  
**Used by**: Type cleanup agents (context on what works)

### **PROCESSOR_ANALYSIS.md** (9K)
**What**: Processor separation analysis (CeFi/TradFi/DeFi)  
**Used by**: Understanding processor structure

---

## 🎯 HOW SUB-AGENTS USE THESE

**In Task Prompts, You Write**:
```
Sub-Agent 1 prompt:
"Read .cursor/plans/contexts/CODING_STANDARDS.md for fix patterns"
"Read .cursor/plans/contexts/TYPE_FIXES_EXPLANATION.md for decorator removal example"
"Reference working example: instruments_service/processors/cefi_processor.py"
```

**Sub-Agent Then**:
1. Reads those context files (in their own context window)
2. Applies patterns
3. Returns small summary to you (2-3K tokens)

**You Never Read These Directly** - sub-agents do, you get summaries!

---

## 📖 ACCESSING ROOT PLANS

**Sub-agents can also read root plan files**:

```
"Read full refactoring plan: .cursor/plans/service_structure_standardization_4a4b3ff3.plan.md"
"Check instruments domain decisions: .cursor/plans/INSTRUMENTS_DOMAIN_DECISIONS.md"
```

**Flexibility**: Sub-agents access ANY file, you just specify in their prompt

---

## ✅ CONTEXT BUDGET EXAMPLE

**Bad (Master reads everything)**:
```
You read:
- CODING_STANDARDS.md (11K)
- SESSION_2_SUMMARY.md (9K)
- TYPE_FIXES_EXPLANATION.md (3.5K)
- orchestrator.py (50K)
- aggregator.py (20K)
- Edit files (100K)
Total: 193.5K tokens
```

**Good (Sub-agents read, you get summaries)**:
```
You:
- Task 2 prompt: 5K
- Agent 1 summary: 2K
- Agent 2 summary: 2K
- Agent 3 summary: 2K
- Agent 4 summary: 2K
Total: 13K tokens ✅

Sub-Agent 1 (separate context):
- Reads CODING_STANDARDS.md (11K)
- Reads orchestrator.py (50K)
- Fixes code (100K)
Total: 161K in THEIR context (not yours!)
```

**Savings**: 193K → 13K tokens in your context = **93% reduction!**

**This preserves cursor rules!** 🎯

---

**Sub-agents read these, you orchestrate** ✅
