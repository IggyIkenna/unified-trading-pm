# Parallel Execution Guide

> **SUPERSEDED (archived 2026-07-27).** Documents a 4-agent-cap Cursor-CLI bash-script parallel-dispatch pattern
> (`run-parallel-agents.sh`, `/tmp` log monitoring). Current parallel-agent model is per-slot git worktrees + Claude
> Code CLI sub-agents (CLAUDE.md 'Agent behavior': max 10 parallel agents) via agent-orchestrator role-based dispatch
> (`codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`) — a different cap and a different mechanism.

## 🚀 The Big Improvement (v10)

**Before**: Sequential, limited context **After**: Parallel (4x), full workspace context

---

## 🎯 Key Innovation: Workspace Root + Edit Restrictions

### The Pattern

```bash
# Each agent gets:
--workspace /path/to/workspace-root  # Full context
"ONLY edit files in repo-name/"      # Edit restriction in prompt
```

### Why This Works

**Full Context**:

- ✅ Agents see `unified-trading-codex/` (canonical patterns)
- ✅ Agents see workspace `.cursorrules` (workspace-level rules)
- ✅ Agents see `.cursor/rules/*.mdc` (all standards)
- ✅ Agents see path dependencies (`unified-trading-library/`, etc.)

**No Conflicts**:

- ✅ Agent 1 edits only `unified-config-interface/`
- ✅ Agent 2 edits only `unified-trading-library/`
- ✅ Agent 3 edits only `instruments-service/`
- ✅ Agent 4 edits only `market-tick-data-handler/`

**Result**: Different repos = zero conflict risk + full context!

---

## 📊 Performance Comparison

| Approach                       | Time      | Context        | Parallelism  | Cost |
| ------------------------------ | --------- | -------------- | ------------ | ---- |
| **Sequential (old)**           | 60 min    | Single repo    | 1 at a time  | $0   |
| **Bash orchestrator**          | 30 min    | Single repo    | 10 at a time | $0   |
| **Claude Code parallel (v10)** | 15-20 min | Full workspace | 4 at a time  | $0   |

**Winner**: Claude Code parallel (v10) - Best of both worlds!

---

## 🔧 How It Works

### Single Repo Script (`run-agent.sh`)

```bash
bash run-agent.sh <repo-name> "<prompt>"
```

**What it does**:

1. Sets workspace to root (full context)
2. Enhances prompt with edit restrictions
3. Launches agent CLI
4. Pretty-prints output

**Usage**:

```bash
bash run-agent.sh unified-config-interface "Fix all basedpyright errors"
```

### Parallel Script (`run-parallel-agents.sh`)

```bash
bash unified-trading-pm/scripts/agents/run-parallel-agents.sh <repo1> <repo2> <repo3> <repo4> "<prompt>"
```

**What it does**:

1. Validates max 4 repos
2. Gets API key (shared across agents)
3. Launches 4 agents in parallel (2s stagger)
4. Each agent: workspace root + edit restriction
5. Waits for all to complete
6. Reports results

**Usage**:

```bash
bash unified-trading-pm/scripts/agents/run-parallel-agents.sh \
    unified-config-interface \
    unified-trading-library \
    instruments-service \
    market-tick-data-handler \
    "Fix all basedpyright errors"
```

---

## 🎯 For Claude Code Orchestration

### Batch Structure (6 batches × 4 repos)

**Batch 1**:

```bash
bash unified-trading-pm/scripts/agents/run-parallel-agents.sh \
    unified-config-interface \
    unified-trading-library \
    instruments-service \
    market-tick-data-handler \
    "Fix all basedpyright errors. Apply: 1) No empty fallbacks, 2) No Type Any, 3) No decorators."
```

**Batch 2**:

```bash
bash unified-trading-pm/scripts/agents/run-parallel-agents.sh \
    market-data-processing-service \
    features-calendar-service \
    features-delta-one-service \
    features-volatility-service \
    "Fix all basedpyright errors. Apply: 1) No empty fallbacks, 2) No Type Any, 3) No decorators."
```

**[Continue for batches 3-6]**

---

## 💡 Why Max 4 Agents?

### Resource Considerations

**Each agent uses**:

- ~2-4 GB RAM
- ~50-100% CPU (during active work)
- Network bandwidth (API calls)

**4 agents in parallel**:

- ~8-16 GB RAM total
- Manageable on most machines
- Good balance of speed vs resources

**More than 4**:

- Risk of OOM (out of memory)
- Slower due to resource contention
- Diminishing returns

### API Rate Limits

With `--model auto` (FREE tier):

- Cursor might have concurrent request limits
- 4 simultaneous seems safe
- 10+ might hit rate limits

---

## 🔍 Monitoring Parallel Execution

### Live Monitoring

**Each agent logs to**:

```bash
/tmp/agent-{repo-name}.log
```

**Monitor in real-time**:

```bash
# Terminal 1
tail -f /tmp/agent-unified-config-interface.log

# Terminal 2
tail -f /tmp/agent-unified-trading-library.log

# Terminal 3
tail -f /tmp/agent-instruments-service.log

# Terminal 4
tail -f /tmp/agent-market-tick-data-handler.log
```

### After Completion

**Check all logs**:

```bash
for repo in unified-config-interface unified-trading-library instruments-service market-tick-data-handler; do
    echo "=== $repo ==="
    tail -20 /tmp/agent-${repo}.log
    echo ""
done
```

---

## ✅ Verification After Batch

### Check All Repos

```bash
cd /path/to/unified-trading-system-repos  # workspace root (varies per machine)

for repo in unified-config-interface unified-trading-library instruments-service market-tick-data-handler; do
    echo "=== $repo ==="
    cd $repo
    basedpyright --level warning 2>&1 | tail -1
    cd ..
    echo ""
done
```

### Expected Output

```
=== unified-config-interface ===
0 errors, 0 warnings, 0 notes

=== unified-trading-library ===
0 errors, 0 warnings, 0 notes

=== instruments-service ===
0 errors, 0 warnings, 0 notes

=== market-tick-data-handler ===
0 errors, 0 warnings, 0 notes
```

---

## 🎯 Complete Workflow for Claude Code

### Phase 1: Setup (One-time)

```bash
# Get API key
gcloud secrets versions access latest --secret=cursor-api-key --project=central-element-323112 > /tmp/cursor_key.txt

# Launch Claude Code
claude --model claude-sonnet-4-5-20250929
```

### Phase 2: Execute (Paste into Claude Code)

Paste the prompt from `CLAUDE_CODE_TASK.md` which includes:

- Read workspace rules first
- Launch 6 batches of 4 repos each
- Verify after each batch
- Resume if needed
- Commit successful repos

### Phase 3: Monitor

Claude Code will show progress for all 4 agents simultaneously.

---

## 💰 Cost & Time Savings

### Sequential (Old)

- Time: 60 minutes (24 repos × 2.5 min)
- Context: Single repo (limited)
- Cost: $0

### Parallel (v10)

- Time: 15-20 minutes (6 batches × 3 min)
- Context: Full workspace (codex, dependencies, rules)
- Cost: $0

**Savings**: 40-45 minutes (67% faster) + Better fixes (full context)!

---

## 🚨 Important Notes

### Edit Restrictions Are Critical

The prompt explicitly tells each agent:

```
"You can ONLY EDIT files in {repo}/ directory"
```

**Why**: Prevents agents from editing:

- Other repos (conflicts)
- Codex (source of truth)
- Shared libraries (breaks other repos)

### Workspace Root Is Critical

Using workspace root gives agents access to:

- `unified-trading-codex/` - Canonical patterns
- Path dependencies - `unified-trading-library/`, etc.
- Workspace rules - `.cursorrules`, `.cursor/rules/*.mdc`

**Without workspace root**: Agents can't see standards or dependencies!

---

## 🎉 Summary

**v10 Innovation**:

- ✅ Parallel execution (4 agents)
- ✅ Full workspace context (codex, dependencies, rules)
- ✅ Edit restrictions (no conflicts)
- ✅ 4x faster (15-20 min vs 60 min)
- ✅ Better fixes (agents see canonical patterns)

**Result**: Best of both worlds - speed AND quality! 🚀
