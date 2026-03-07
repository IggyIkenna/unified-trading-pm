# Claude Code Orchestration Pattern

**Claude Code CLI orchestrates by calling `agent` CLI (instead of Cursor sub-agents)**

---

## 🎯 The Pattern

### Traditional (Cursor Sub-Agents)

```
Master Agent in Cursor
    ↓
Launches: Task tool (Cursor sub-agents)
    ↓
Sub-agents do work
    ↓
Report back to master
```

### New (Claude Code + Agent CLI)

```
Claude Code CLI (terminal)
    ↓
Calls: agent --print --model auto "task"
    ↓
Agent does work
    ↓
Claude Code reads log/output
    ↓
Verifies result
    ↓
Launches next agent or resumes
```

---

## 📋 Task Structure for Claude Code

### TASK: Fix Pyright Errors (Example)

**File**: `CLAUDE_CODE_TASK.md`

```markdown
# Claude Code Task: Fix 24 Repos

**Paste this into Claude Code CLI**

---

## 🚀 PROMPT

\`\`\` I want to fix basedpyright errors in unified-config-interface using agent CLI.

STEP 1: Navigate and check errors cd
/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-config-interface basedpyright --level warning
2>&1 | tail -1

STEP 2: Set up environment variables export PATH="$HOME/.local/bin:$PATH" export CURSOR_API_KEY=$(gcloud secrets
versions access latest --secret=cursor-api-key --project=central-element-323112)

STEP 3: Set workspace and parser paths export
WORKSPACE=/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-config-interface export
PARSER=/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks_claude_code/simple-parser.py

STEP 4: Launch agent CLI with pretty printing (takes 3-5 minutes) agent --api-key
"$CURSOR_API_KEY" --print --model auto --trust --output-format stream-json --stream-partial-output --workspace "$WORKSPACE"
"Fix all basedpyright errors. Apply: 1) No empty fallbacks, 2) No Type Any, 3) No decorators. Target: 0 errors." 2>&1 |
python3 "$PARSER"

STEP 5: Verify basedpyright --level warning 2>&1 | tail -1

STEP 6: Report Show me: Status, errors fixed (66 → X), time taken \`\`\`

---

## 🔄 RESUME PATTERN

If agent doesn't fix all errors:

\`\`\` The agent fixed 66 → 15 errors. Remaining issues:

- Lines 45-67: Still has Type Any
- Lines 89-103: Still has empty fallback

Launch agent again with targeted guidance:

\`\`\`bash

# Set environment if not already set

export WORKSPACE=/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-config-interface export
PARSER=/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks_claude_code/simple-parser.py

agent --api-key
"$CURSOR_API_KEY" --print --model auto --trust --output-format stream-json --stream-partial-output --workspace "$WORKSPACE"
"Fix the remaining 15 basedpyright errors. Focus on: 1) Lines 45-67 in execution_config_schema.py - replace Any with
dict[str, str], 2) Lines 89-103 in loaders.py - remove or {} fallback, fail loud. Target: 0 errors." 2>&1 | python3
"$PARSER" \`\`\` \`\`\`

---

## 💰 TOKEN TRACKING

Claude Code CLI (orchestration):

- Input: ~10K tokens (reading output, generating commands)
- Output: ~5K tokens (commands, verification)
- Cost: ~$0.10 per repo

Agent CLI (execution):

- FREE with Cursor Ultra (model: auto)

Total per repo: ~$0.10 (vs $3-5 if master agent did everything)
```

---

## 📊 Full Workflow for 24 Repos

### In Claude Code CLI Terminal

```bash
claude --model sonnet

> I want to fix pyright errors across all 24 repos using agent CLI.
>
> For each repo:
> 1. Set environment variables (PATH, CURSOR_API_KEY, WORKSPACE, PARSER)
> 2. Launch agent CLI with the fix prompt
> 3. Monitor the pretty-printed output (via simple-parser.py)
> 4. Verify with basedpyright
> 5. If errors remain, launch agent again with targeted guidance
> 6. Track progress (repo X/24, errors fixed, time taken)
>
> Start with unified-config-interface (66 errors).
>
> Use this command pattern:
>
> export PATH="$HOME/.local/bin:$PATH"
> export CURSOR_API_KEY=$(gcloud secrets versions access latest --secret=cursor-api-key --project=central-element-323112)
> export WORKSPACE=/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/REPO_NAME
> export PARSER=/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks_claude_code/simple-parser.py
>
> agent --api-key "$CURSOR_API_KEY" --print --model auto --trust --output-format stream-json --stream-partial-output --workspace "$WORKSPACE" "Fix all basedpyright errors. Apply: 1) No empty fallbacks, 2) No Type Any, 3) No decorators." 2>&1 | python3 "$PARSER"
>
> After each repo, verify and report progress.
```

**Claude Code will**:

- Run the agent command
- Watch the output
- Verify results
- Launch next agent or resume
- Track progress across all 24 repos

---

## 💡 Key Difference

**Old way** (Cursor sub-agents):

- Master in Cursor → Launches Task tool → Cursor sub-agents work
- Cost: Cursor credits

**New way** (Agent CLI):

- Claude Code CLI → Calls agent CLI → Agent works
- Cost: $0 (agent uses model: auto)

**Benefit**: Same orchestration pattern, but FREE execution!

---

## 🎯 Key Points

**Environment Variables**: Breaking long commands into env vars prevents Claude Code from truncating:

- `$WORKSPACE` - repo path
- `$PARSER` - simple-parser.py path
- `$CURSOR_API_KEY` - API key from Secret Manager

**Pretty Printing**: Always pipe through `simple-parser.py` for readable output:

- 💭 Thinking
- 🔍 Searching
- 📖 Reading
- ✏️ Writing
- ✅ Completed

**See**: `CLAUDE_CODE_TASK.md` for the complete, ready-to-paste prompt!
