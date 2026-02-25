# Claude Code Task: Fix 24 Repos (Parallel Execution)

**Claude Code CLI orchestrates up to 4 agent CLI instances in parallel**

---

## ⚡ Quick Reference

**Key Pattern**: Workspace root + target repo restriction

```bash
# Single repo
bash run-agent.sh <repo-name> "<prompt>"

# Parallel (up to 4 repos)
bash run-parallel-agents.sh <repo1> <repo2> <repo3> <repo4> "<prompt>"
```

**Benefits**:
- ✅ Full workspace context (codex, dependencies, workspace rules)
- ✅ Edit restrictions prevent conflicts (each agent edits only its repo)
- ✅ Parallel execution (4x faster!)
- ✅ Pretty-printed output for each agent

---

## Task: Fix Basedpyright Errors Across 24 Repos

**Goal**: Fix all basedpyright errors across 24 repos  
**Method**: Claude Code orchestrates agent CLI in parallel batches  
**Time**: 15-20 minutes (vs 60 minutes sequential)  
**Parallelism**: 4 repos at a time (6 batches total)

**Pattern**: Claude Code → 4 parallel agents → Verify → Next batch

---

## 🚀 PROMPT (Paste into Claude Code CLI)

```
I want to fix basedpyright errors across 24 repos using parallel agent CLI execution.

ORCHESTRATION ROLE (Claude Code):
- Launch up to 4 agent CLI instances in parallel
- Each agent gets full workspace context (codex, dependencies, workspace rules)
- Each agent restricted to edit only its target repo (no conflicts!)
- Monitor all outputs (pretty-printed via simple-parser.py)
- Verify results with basedpyright for each repo
- Resume agents with targeted guidance if errors remain
- Track progress (batch X/6, repos completed, errors fixed)

AGENT ROLE (agent CLI with model: auto):
- Workspace: Full workspace root (can read everything)
- Edit restriction: Only files in target repo directory
- Reads: unified-trading-codex/, workspace .cursorrules, .cursor/rules/*.mdc, path dependencies
- Applies: No empty fallbacks, no Type Any, no decorators
- Tests sparingly: Run basedpyright only 2-3 times total (start, mid-way, end) to avoid hanging

CONTEXT (Agents read automatically):
- Workspace .cursorrules (workspace-level rules)
- .cursor/rules/*.mdc (specific standards)
- unified-trading-codex/06-coding-standards/ (canonical patterns)
- Path dependencies (unified-cloud-services, etc.)

SAFEGUARDS:
- NEVER: Skip tests, add type: ignore, use .get(x,{}), use Type Any
- MUST: Fix root causes, fail loud, use specific types
- EDIT ONLY: Target repo directory (read everything else)
- Verify with basedpyright after each agent run

---

SETUP (One-time):

STEP 0: Kill any existing zombie processes
bash /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks_claude_code/kill-zombies.sh

STEP 1: Get API key (save to temp file for all batches)
gcloud secrets versions access latest --secret=cursor-api-key --project=central-element-323112 > /tmp/cursor_key.txt

STEP 2: Define timeout helper (prevents zombie processes)
run_with_timeout() {
    local timeout=$1
    shift
    perl -e 'alarm shift; exec @ARGV' "$timeout" "$@"
}

---

BATCH 1/6: First 4 repos

STEP 1: Create backup branches for all 4 repos
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos

for repo in unified-config-interface unified-events-interface instruments-service market-tick-data-handler; do
  cd $repo
  git checkout -b fix-basedpyright-$(date +%s)
  git push -u origin HEAD
  cd ..
done

STEP 2: Check current errors for all 4 repos (use timeout to prevent hanging)
for repo in unified-config-interface unified-events-interface instruments-service market-tick-data-handler; do
  echo "$repo:"
  cd $repo && run_with_timeout 30 basedpyright --level warning 2>&1 | tail -1 && cd ..
done

STEP 3: Launch 4 agents in parallel (takes 3-5 minutes)
bash /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.cursor/plans/tasks_claude_code/run-parallel-agents.sh unified-config-interface unified-events-interface instruments-service market-tick-data-handler "Fix all basedpyright errors. Apply: 1) No empty fallbacks - fail loud if config missing, 2) No Type Any - use specific types like dict[str, str], 3) No decorators - use manual retry with for loop. IMPORTANT: Only run basedpyright 2-3 times total (start, mid-way, end) to avoid hanging. Target: 0 errors."

You'll see output from all 4 agents interleaved:
💭 [repo1] Thinking...
🔍 [repo2] Searching...
📖 [repo3] Reading: file.py
✏️  [repo4] Writing: file.py
...

STEP 4: Verify results for all 4 repos (use timeout to prevent hanging)
for repo in unified-config-interface unified-events-interface instruments-service market-tick-data-handler; do
  echo "$repo:"
  cd $repo && run_with_timeout 30 basedpyright --level warning 2>&1 | tail -1 && cd ..
done

Expected: "0 errors, 0 warnings, 0 notes" for each

STEP 5: If any repo has errors, resume individually
# Example: unified-config-interface still has 15 errors
bash run-agent.sh unified-config-interface "Fix the remaining 15 basedpyright errors. Focus on: [specific files/lines from error output]. Target: 0 errors."

STEP 6: Run quality gates for all 4 repos
for repo in unified-config-interface unified-events-interface instruments-service market-tick-data-handler; do
  echo "Quality gates: $repo"
  cd $repo && bash scripts/quality-gates.sh --no-fix && cd ..
done

STEP 7: Report results for batch 1
✅ Repos completed: 4/24
📊 Errors fixed:
  - unified-config-interface: 108 → 0
  - unified-events-interface: 0 → 0 (skipped)
  - instruments-service: X → 0
  - market-tick-data-handler: X → 0
⏱️ Time: X minutes
💰 Cost: $0 (all FREE)

STEP 8: Commit successful repos
for repo in unified-config-interface instruments-service market-tick-data-handler; do
  cd $repo
  bash scripts/quickmerge.sh "Fix basedpyright errors in $repo"
  cd ..
done

---

BATCH 2/6: Next 4 repos

Repeat STEP 1-8 for:
- market-data-processing-service
- features-calendar-service
- features-delta-one-service
- features-volatility-service

---

BATCH 3/6: Next 4 repos

Repeat STEP 1-8 for:
- features-onchain-service
- ml-training-service
- ml-inference-service
- strategy-service

---

BATCH 4/6: Next 4 repos

Repeat STEP 1-8 for:
- execution-service
- post-trade-service
- risk-service
- pnl-service

---

BATCH 5/6: Next 4 repos

Repeat STEP 1-8 for:
- data-status-service
- health-monitor-service
- audit-service
- notification-service

---

BATCH 6/6: Last 4 repos

Repeat STEP 1-8 for:
- unified-cloud-services
- unified-trade-execution-interface
- unified-market-interface
- execution-algo-library

---

FINAL SUMMARY (After all 6 batches):

📊 Overall Metrics:
- Batches completed: 6/6
- Repos processed: 24/24
- Total errors fixed: X
- Total time: 15-20 minutes (vs 60 minutes sequential)
- Repos with remaining errors: X (list them)
- Total cost: $0

🎯 Next Steps:
- Review any repos with remaining errors
- Run cross-repo quality gates check
- Update documentation if patterns changed
```

---

## 🔄 Resume Pattern (For Individual Repos)

**When to resume**:
- Agent reports partial success (errors remain)
- Specific files/lines still have issues
- Need targeted guidance

**How to resume** (single repo, keeps context):
```bash
bash run-agent.sh <repo-name> "Previous progress: X → Y errors. 

Remaining issues:
1. Lines 45-67 in file.py - [specific fix needed]
2. Lines 89-103 in other.py - [specific fix needed]

Target: 0 errors."
```

---

## 💡 Tips for Claude Code

**Launch in batches of 4** - Max parallelism without overwhelming system  
**Stagger launches** - Script adds 2s delay between agents  
**Monitor logs** - Each agent logs to `/tmp/agent-{repo}.log`  
**Verify all repos** - Check basedpyright for each after batch completes  
**Resume individually** - If a repo needs more work, use single-repo script  
**Create backup branches** - Before each batch  
**Commit per batch** - Don't wait until all 24 are done

---

## 🎯 What You'll See

```
$ bash run-parallel-agents.sh repo1 repo2 repo3 repo4 "prompt"

==========================================
Launching 4 agents in parallel
==========================================

🚀 Launching agent for: unified-config-interface
   PID: 12345 | Log: /tmp/agent-unified-config-interface.log

🚀 Launching agent for: unified-events-interface
   PID: 12346 | Log: /tmp/agent-unified-events-interface.log

🚀 Launching agent for: instruments-service
   PID: 12347 | Log: /tmp/agent-instruments-service.log

🚀 Launching agent for: market-tick-data-handler
   PID: 12348 | Log: /tmp/agent-market-tick-data-handler.log

==========================================
All 4 agents launched!
==========================================

Monitor logs:
  tail -f /tmp/agent-unified-config-interface.log
  tail -f /tmp/agent-unified-events-interface.log
  tail -f /tmp/agent-instruments-service.log
  tail -f /tmp/agent-market-tick-data-handler.log

Waiting for all agents to complete...

⏳ Waiting for unified-config-interface (PID: 12345)...
✅ unified-config-interface completed successfully

⏳ Waiting for unified-events-interface (PID: 12346)...
✅ unified-events-interface completed successfully

⏳ Waiting for instruments-service (PID: 12347)...
✅ instruments-service completed successfully

⏳ Waiting for market-tick-data-handler (PID: 12348)...
✅ market-tick-data-handler completed successfully

==========================================
All agents completed!
==========================================
```

---

## ✅ Success Criteria (Per Batch)

- [ ] Backup branches created and pushed for all 4 repos
- [ ] 4 agents launched successfully in parallel
- [ ] All outputs pretty-printed (not raw JSON)
- [ ] All logs saved to /tmp/agent-{repo}.log
- [ ] basedpyright shows 0 errors for each repo
- [ ] Quality gates pass for each repo
- [ ] Changes committed via quickmerge for each repo
- [ ] Resume iterations documented (if used)

---

## 📊 Token Tracking

**Per Batch (4 repos in parallel)**:
- 4 agents (model: auto): FREE with Cursor Ultra
- Claude Code orchestration: ~40-80K tokens
- Cost per batch: $0

**All 6 Batches (24 repos)**:
- Total agent cost: $0 (FREE)
- Total Claude Code: ~240-480K tokens orchestration
- Total cost: $0 (FREE with Claude Pro subscription)

---

## 💰 Cost Summary

**Everything FREE**:
- Claude Code (claude-sonnet-4-5-20250929): FREE with Claude Pro
- Agent CLI (model: auto): FREE with Cursor Ultra
- **Total**: $0 for all 24 repos!

**Time Savings**:
- Sequential: 60 minutes (24 repos × 2.5 min avg)
- Parallel (4 at a time): 15-20 minutes (6 batches × 3 min avg)
- **Savings: 40-45 minutes (67% faster!)**

---

## 🎯 Just Paste and Go!

**Step 1: Launch Claude Code**:
```bash
claude --model claude-sonnet-4-5-20250929
```

**Step 2: Paste the prompt** (lines 57-200 above)

It will orchestrate everything - launching parallel agents, monitoring outputs, verifying results, and tracking progress! 🚀

**Note**: Config file (`~/.claude/config.json`) is set to skip all permissions, so no prompts! Each agent CLI automatically reads cursor rules from the workspace root.
