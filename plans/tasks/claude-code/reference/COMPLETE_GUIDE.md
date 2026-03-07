# Complete Technical Guide

**Everything you need to know in one place**

---

## 🎯 Two Approaches

### Bash Orchestrator

**How it works**:

```
orchestrator-test.sh (bash script)
    ↓
Loops through repos
    ↓
For each repo:
  - Audits (basedpyright)
  - Launches agent CLI
  - Verifies (basedpyright)
    ↓
Reports summary
```

**Features**:

- 10 parallel agents (no race conditions)
- Live pretty printing (simple-parser.py)
- State persistence (resume-able)
- API key from Secret Manager

**Cost**: $0

---

### Claude Code Orchestration

**How it works**:

```
Claude Code CLI (claude-sonnet-4-5-20250929)
    ↓
Runs shell commands
    ↓
Launches: agent CLI
    ↓
Reads output (via simple-parser.py)
    ↓
Verifies (basedpyright)
    ↓
If errors remain: Launches agent again with targeted guidance
    ↓
Moves to next repo
```

**Features**:

- Smart adaptation (analyzes failures)
- Can generate targeted resumes
- Tracks progress intelligently
- Same agent CLI (FREE execution)

**Cost**: $0 (FREE with Claude Pro subscription)

---

## 🔧 Agent CLI Details

**Command** (with environment variables for cleaner syntax):

```bash
# Set environment
export PATH="$HOME/.local/bin:$PATH"
export CURSOR_API_KEY=$(gcloud secrets versions access latest --secret=cursor-api-key --project=central-element-323112)
export WORKSPACE=/path/to/repo
export PARSER=/path/to/simple-parser.py

# Launch agent with pretty printing
agent --api-key "$CURSOR_API_KEY" --print --model auto --trust \
    --output-format stream-json \
    --stream-partial-output \
    --workspace "$WORKSPACE" \
    "Fix all basedpyright errors..." \
    2>&1 | python3 "$PARSER"
```

**Key flags**:

- `--print` - Headless mode (required for scripts)
- `--model auto` - FREE with Cursor Ultra
- `--trust` - Auto-trust workspace (only works with --print)
- `--output-format stream-json` - Structured output
- `--stream-partial-output` - Real-time streaming (requires stream-json)

**Authentication**:

- API key from Secret Manager (works on any machine)
- Or local auth (if already logged in)

**Why environment variables?**:

- Prevents Claude Code from truncating long commands
- Makes commands more readable
- Easier to modify paths
- Standard pattern across all tasks

---

## 🎨 Pretty Printing

**simple-parser.py** converts JSON to clean output:

**Input** (raw JSON):

```json
{"type":"thinking","subtype":"delta","text":"The user wants..."}
{"type":"tool_call","subtype":"started","tool_call":{"readToolCall":...}}
```

**Output** (clean):

```
💭 The user wants me to fix errors
📖 Reading: base_config.py
✏️  Writing: base_config.py
```

---

## 🚨 Repo Naming

**CRITICAL**: Repo folders use DASHES, Python packages use UNDERSCORES

**Repo folder**: `unified-config-interface` (dashes) **Python package**: `unified_config_interface` (underscores)

**For agent CLI**: Always use repo folder path (dashes)

---

## 💰 Cost (Updated - Everything FREE!)

**With your subscriptions**:

- Claude Pro ($20/month) → Claude Code CLI FREE
- Cursor Ultra → Agent CLI FREE
- **Total**: $0 for all 24 repos!

**Rate limits**:

- Claude Code: ~500 messages/day (plenty for 24 repos)
- Agent CLI: Unlimited with Ultra

---

## 🎯 Model Versions

**Claude Code CLI**:

- `--model sonnet` = claude-sonnet-4-5-20250929 (claude-sonnet-4-5-20250929)
- Latest and best coding model
- FREE with Claude Pro

**Agent CLI**:

- `--model auto` = Cursor's included models
- FREE with Cursor Ultra

---

## ✅ Summary

**Everything is FREE** with your subscriptions:

- Claude Code (claude-sonnet-4-5-20250929): FREE
- Agent CLI (auto): FREE
- Total: $0 for 24 repos

**Just choose your approach and run it!** 🚀
