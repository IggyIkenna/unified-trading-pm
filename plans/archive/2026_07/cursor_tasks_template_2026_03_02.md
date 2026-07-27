# Task Template - Copy for New Tasks

> **SUPERSEDED (archived 2026-07-27).** A copy-paste template for Cursor-Task-tool sub-agent tasks (no frontmatter,
> resume/token-tracking sections). Current plan-authoring SSOT is `plans/active/task_template.md` under the
> `PLAN_FORMAT.md` frontmatter schema — a differently-shaped, current template.

**⚠️ CRITICAL: ALL TASKS MUST USE SUB-AGENTS** - This is MANDATORY, not optional!

**Use this structure for ANY new task - sub-agents are REQUIRED for context preservation**

---

## Task: [YOUR TASK NAME]

**Goal**: [One sentence goal] **Method**: X fast sub-agents MANDATORY (Task tool) **Time**: X hours

**⚠️ SUB-AGENTS REQUIRED**: Master orchestrates ONLY, never edits directly!

---

## 🚀 PROMPT (Copy-Paste to Execute)

```
Execute task: [Task name]

⚠️ MANDATORY: Use Task tool to launch [X] sub-agents (model: fast, subagent_type: generalPurpose)

MASTER AGENT ROLE (Orchestrate ONLY):
- Launch sub-agents with detailed prompts
- Review ALL changes against cursor rules
- Resume sub-agents if violations detected
- Approve only when standards met
- NEVER edit files directly (breaks context preservation)

SUB-AGENT ROLE (Execute work):
- Read context files provided
- Fix root causes per canonical patterns
- Test frequently (verify at intervals)
- Report back with structured results

CONTEXT (Sub-agents must read):
- .cursor/plans/tasks/TEMPLATE.md (safeguards)
- .cursor/plans/contexts/CODING_STANDARDS.md (standards)
- [Any other context files needed]
- instruments-service/docs/CANONICAL_PATTERNS.md (reference)

SAFEGUARDS (Master enforces):
- Backup branches created before work
- NEVER: Skip tests, add type: ignore without fixing, use .get(x,{}), use Type Any
- MUST: Fix root causes, test frequently, report back
- Master reviews before approval

CRITICAL: SAVE ALL AGENT IDs FROM LAUNCH (needed for resume)

Launch [X] Task sub-agents in parallel:

**Sub-Agent 1**:
```

description: [5-10 word description] model: fast subagent_type: generalPurpose prompt: | [Detailed task for this agent]

Files: [list]

Steps:

1. [Step 1]
2. [Step 2]

Verify: [commands]

RETURN (REQUIRED): ✅ Status: [Success/Issues] 📊 Metrics: Fixed X items, Y tests, Z errors 💰 TOKENS USED: Check your
context at end and report total tokens consumed ⏱️ Time: X minutes 🔒 Backup: [branch name]

Example: ✅ Status: Success 📊 Metrics: Fixed 15 violations, 37 tests pass, 0 errors 💰 TOKENS: 45K input + 12K output =
57K total ⏱️ Time: 25 minutes 🔒 Backup: fix-standards-1708713234

```

**[Repeat for each sub-agent]**

---

## 🔄 RESUME PATTERN (MANDATORY FOR CORRECTIONS)

**⚠️ CRITICAL: If sub-agent needs corrections, MUST use resume (saves 50%+ tokens)**

**When to resume**:
- Sub-agent reports partial success (errors remain)
- Master review finds violations (not matching canonical patterns)
- Tests fail (sub-agent needs guidance)
- Quality gates fail (need targeted fix)

**How to resume**:
```

Resume Task sub-agent [X]:

description: Continue fixing [specific issue] subagent_type: generalPurpose resume: [agent-id-from-initial-launch] ←
MUST use same ID model: fast prompt: | Your previous work: [summary of progress, e.g., 328 → 150 errors]

Issue found in master review: [Specific problem with example]

Solution (explicit guidance):

1. [Exact pattern to use with code snippet]
2. [Verification command]

Target: [Specific metric, e.g., 150 → 0 errors]

RETURN: Progress: [metric before] → [metric after] Tokens this iteration: XK (incremental, not cumulative)

````

**Resume benefits** (vs launching new agent):
- Agent keeps ALL context (no re-reading files)
- Token savings: 50-70% per iteration
- Continuity: Agent remembers previous attempts
- Focused: Master gives targeted feedback

**Resume pattern** (iterative):
1. Launch initial agent → Reports back
2. Master reviews → Finds issues
3. Resume with guidance → Reports back
4. Master reviews → Repeat until success

**Example iteration**:
- Launch: 328 errors → 150 errors (uses 150K tokens)
- Resume 1: 150 → 50 errors (uses 40K tokens, not 150K!)
- Resume 2: 50 → 0 errors (uses 30K tokens)
- Total: 220K tokens (vs 450K for 3 separate agents)

---

## ✅ Success Criteria

**Master must verify ALL criteria before task complete**:

- [ ] All [X] sub-agents launched successfully
- [ ] Master saved all agent IDs (for resume)
- [ ] Master reviewed all sub-agent results (tables/summaries)
- [ ] All changes match canonical patterns (fail loud, specific types, manual retry)
- [ ] [Task-specific criterion 1]
- [ ] [Task-specific criterion 2]
- [ ] Tests passing (sub-agents verified + master spot-checked)
- [ ] Quality gates passing (exit 0, master verified)
- [ ] Resume iterations documented (if used)

---

## 🔍 Verification

```bash
[Commands to verify complete success]
````

---

## 📊 Expected Results

[What you expect to see when done]

---

## 💰 TOKEN USAGE TRACKING

**REQUIRED: Track at Sonnet 4.5 level and sub-agent level**

### Master Agent (Sonnet 4.5):

- Starting tokens: [check at start]
- Ending tokens: [check at end]
- Used: [end - start]
- Cost estimate: $X (at $X per 1M tokens)

### Sub-Agents (Fast Model):

**Sub-Agent 1**:

- Agent ID: [save for resume]
- Initial tokens: XK
- Resume iterations: Y (if any)
- Total tokens: ZK
- Cost: $X

**Sub-Agent 2**:

- Agent ID: [save for resume]
- Tokens used: [from agent report]
- Cost: $X

[Repeat for each sub-agent]

### Total Session:

- Master agent: XK tokens ($Y)
- Sub-agents: XK tokens total ($Y)
- **Grand total: XK tokens ($Z)**

### Cost Breakdown:

- Sonnet 4.5 rate: $X per 1M input, $Y per 1M output
- Fast model rate: $X per 1M input, $Y per 1M output
- Total session cost: **$Z**

**IMPORTANT**: Each sub-agent MUST report token usage in their return format

---

**Delete this template text and fill in your task details**
