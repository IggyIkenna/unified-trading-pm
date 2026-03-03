# Token Usage Tracking Guide

**⚠️ CRITICAL: TOKEN TRACKING IS MANDATORY** - All tasks MUST report tokens!

**Purpose**: Track costs at master agent and sub-agent levels (REQUIRED)
**Why**: Optimize cost, measure efficiency, compare approaches
**Rule**: Every task completion MUST include token usage from both master and all sub-agents

---

## 📊 PRICING (Current Rates)

### Sonnet 4.5 (Master Agent):

- Input: $3 per 1M tokens
- Output: $15 per 1M tokens
- Typical: 80% input, 20% output

### Fast Model (Sub-Agents):

- Input: $0.30 per 1M tokens (10x cheaper)
- Output: $1.50 per 1M tokens (10x cheaper)
- Typical: 70% input, 30% output

---

## 🎯 HOW TO TRACK

### Master Agent (Sonnet 4.5):

**At Session Start**:

```
Note starting token count from Cursor UI or:
"Current context usage: X tokens"
```

**At Session End**:

```
Note ending token count:
"Current context usage: Y tokens"

Master agent tokens: Y - X = Z tokens used
```

### Sub-Agents (Fast Model):

**⚠️ MANDATORY: Sub-agents MUST report tokens in return format**:

```
💰 TOKENS USED: Check your final context usage and report:
- Input: 45K tokens
- Output: 12K tokens
- Total: 57K tokens
- Cost estimate: $0.036 (fast model ~$0.75/1M)
```

**If sub-agent doesn't report**: Master MUST request token usage before proceeding!

**Resume iterations**: Report incremental tokens only (not cumulative re-counts)

---

## 📋 COST CALCULATION

### Formula:

```
Master Agent Cost:
= (Input tokens × $3/1M) + (Output tokens × $15/1M)
= (80K × $3/1M) + (20K × $15/1M)
= $0.24 + $0.30 = $0.54

Sub-Agent Cost (each):
= (Input × $0.30/1M) + (Output × $1.50/1M)
= (40K × $0.30/1M) + (15K × $1.50/1M)
= $0.012 + $0.023 = $0.035

Total for 4 sub-agents: 4 × $0.035 = $0.14

Session Total: $0.54 + $0.14 = $0.68
```

---

## 📊 SESSION COST REPORT TEMPLATE

**Copy this format for each session**:

```
===== SESSION COST REPORT =====
📅 Date: 2026-02-23
🎯 Task: [Task name]
⏱️ Duration: X hours

💰 MASTER AGENT (Sonnet 4.5):
   Starting tokens: XK
   Ending tokens: YK
   Used: ZK tokens
   Breakdown:
   - Reading tasks: 20K
   - Sub-agent summaries: 30K
   - User conversation: 25K
   - Tool outputs: 15K
   Cost: $X.XX

💰 SUB-AGENTS (Fast Model):
   Agent 1 (orchestrator.py):
   - Tokens: 180K (140K input + 40K output)
   - Cost: $0.102

   Agent 2 (aggregator.py):
   - Tokens: 85K (65K input + 20K output)
   - Cost: $0.049

   Agent 3 (handlers):
   - Tokens: 50K (38K input + 12K output)
   - Cost: $0.029

   Total: 315K tokens, $0.180

📊 SESSION TOTAL:
   Master: ZK tokens ($X.XX)
   Sub-agents: 315K tokens ($0.18)
   GRAND TOTAL: (Z+315)K tokens = $Y.YY

💡 EFFICIENCY:
   - Parallel execution: 7 agents working
   - Effective capacity: 7M+ tokens
   - Master context preserved: 150K/1M (85% free!)
   - Cost per repo improved: $0.XX per repo

🎯 COMPARISON (If done without sub-agents):
   Estimated master tokens: 600K+ (would hit context limit)
   Estimated cost: $X.XX (higher due to Sonnet rate)
   Context: Would need refresh (lose cursor rules)

   SAVINGS with sub-agents: $Y.YY (Z% reduction)
===========================================
```

---

## 📈 TRACKING OVER TIME

### Create Log File:

```bash
# .cursor/plans/token_usage_log.md

## Token Usage History

### 2026-02-23 - Session 2
- Task: CeFi processor + type fixes
- Master: 150K tokens ($X)
- Sub-agents: 0 (did manually)
- Total: 150K, $X

### 2026-02-24 - Type Cleanup
- Task: Fix 396 errors via 3 sub-agents
- Master: 120K tokens ($X)
- Sub-agents: 315K tokens ($Y)
- Total: 435K, $Z
- Efficiency: 93% context savings vs direct

### Running Totals:
- Total tokens: XK
- Total cost: $Y.YY
- Sessions: Z
- Avg per session: $X.XX
```

---

## 🎯 OPTIMIZATION INSIGHTS

### Cost-Effective Patterns:

**Expensive** (Avoid):

- Master agent reading 50+ files
- Master agent doing iterative fixes
- Context refresh (lose rules)

**Cheap** (Use):

- Sub-agents reading files (10x cheaper)
- Sub-agents doing fixes (10x cheaper)
- Master orchestrating (small token usage)

### Sweet Spot:

**Tasks > 100K tokens**: Always use sub-agents
**Tasks < 50K tokens**: Direct execution OK
**Tasks 50-100K**: Use sub-agents if preserving context matters

---

## 📊 EXPECTED COSTS (Estimates)

### Task 1: Add Quality Checks

- Master only: ~50K tokens
- Cost: ~$0.40

### Task 2: Fix Violations (4 sub-agents)

- Master: ~80K tokens ($0.60)
- Sub-agents: ~400K tokens ($0.30 total)
- Cost: ~$0.90

### Task 3: Type Cleanup (3 sub-agents)

- Master: ~100K tokens ($0.75)
- Sub-agents: ~350K tokens ($0.25 total)
- Cost: ~$1.00

### Full Session (All 3 Tasks):

- Master: ~230K tokens ($1.75)
- Sub-agents: ~750K tokens ($0.55)
- **Total: ~980K tokens, ~$2.30**

---

## 🔄 RESUME SAVES EVEN MORE TOKENS

**Without Resume** (Agent gets stuck, launch new agent):

```
Agent 1 (attempt 1): 150K tokens → partial success
Agent 1 (attempt 2): 150K tokens (re-reads everything!)
Total: 300K tokens
```

**With Resume** (Iterative feedback):

```
Agent 1 (initial): 150K tokens → partial success
Resume Agent 1: +30K tokens (incremental, keeps context)
Total: 180K tokens
Savings: 120K tokens (40%!)
```

**Master Agent Benefits**:

- Give targeted feedback (10K tokens)
- vs reading/fixing yourself (100K+ tokens)
- **Savings: 90K tokens per iteration!**

---

## 💡 WHY THIS MATTERS

**Cost Tracking Benefits**:

1. **Know session costs** before starting
2. **Optimize approach** (sub-agents vs direct)
3. **Budget planning** (estimate large refactors)
4. **Prove efficiency** (sub-agent savings visible)
5. **Resume strategy** (saves 40%+ tokens on iterations)

**Example**:

- Without sub-agents: 1 session, 800K Sonnet tokens = $12.50
- With sub-agents: 1 session, 230K Sonnet + 750K fast = $2.30
- **Savings: $10.20 (81% reduction!)**

**With resume iterations**:

- Agent needs 3 iterations: 180K tokens (with resume)
- vs 3 separate agents: 450K tokens (without resume)
- **Additional savings: 270K tokens (60%!)**

---

## 📋 REQUIRED IN ALL SUB-AGENT RETURNS

```
💰 TOKEN USAGE:
   Input: XK tokens
   Output: YK tokens
   Total: ZK tokens
   Model: fast
   Cost estimate: $X.XX
```

**Sub-agents check their context usage at completion and report actual numbers**

---

## 🔧 HOW TO CHECK TOKEN USAGE

### In Cursor:

- Look at status bar (shows current context)
- Or run: Check token count in agent state

### For Sub-Agents:

- Sub-agents report their final context usage
- Include in return format

### Session Summary:

- Add up all sub-agent tokens
- Add master agent tokens (end - start)
- Calculate total cost

---

**Add this tracking to EVERY task execution!** 💰
