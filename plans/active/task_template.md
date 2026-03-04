# Task Template - Reusable for Any Agent Task

**Copy this structure when creating new tasks**

---

## 🔒 CRITICAL SAFEGUARDS (Always Include)

```bash
# 1. Create backup branch
git checkout -b backup-before-[task]-$(date +%s)
git add -A && git commit -m "Backup before [task]" || echo "Nothing to commit"
BACKUP_BRANCH=$(git branch --show-current)
echo "🔒 BACKUP: $BACKUP_BRANCH"
git checkout main

# 2. Recovery if needed: git checkout $BACKUP_BRANCH
```

### NEVER Rules:

- ❌ NEVER skip tests or add `|| true`
- ❌ NEVER add `@pytest.mark.skip` without documented reason
- ❌ NEVER use `git reset --hard` on conflicts
- ❌ NEVER add type: ignore without fixing root cause first
- ❌ NEVER use `.get("key", {})` or `.get("key", []")` (fail loud!)
- ❌ NEVER use `Type Any` (check source code for actual type)
- ❌ NEVER auto-commit (report back first)

### MUST DO Rules:

- ✅ Fix root causes (not symptoms)
- ✅ Test frequently
- ✅ Document exceptions in QUALITY_GATE_BYPASS_AUDIT.md
- ✅ Report back with structured format

---

## 📋 TASK STRUCTURE

````markdown
# Task: [Task Name]

**Goal**: [One sentence]
**Method**: X fast sub-agents (Task tool)
**Time**: X hours

## Prompt (Copy-Paste to Execute):

[Prompt text that explicitly uses Task tool]

## Sub-Agent Allocation:

Agent 1: [Description]

- Files: [list]
- Task: [specific]

[Repeat for each agent]

## Success Criteria:

- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Verification:

```bash
[Commands to verify success]
```
````

```

---

## ✅ Example Task Doc Structure

See `TASK_1_ADD_QUALITY_CHECKS.md`, `TASK_2_FIX_VIOLATIONS.md`, `TASK_3_TYPE_CLEANUP.md`

---

**Use this template to create new executable task docs**
```
