# 01: Claude Code Integration

**Status**: ⬜ Not Started
**Priority**: P0 (Immediate cost savings)
**Estimated Time**: 30-60 minutes
**Expected Savings**: 90%+ reduction in orchestration costs

**🎉 BREAKTHROUGH**: Fully automated workflow available using Cursor CLI!

---

## 📖 Overview

Use Claude Code CLI for orchestration + Cursor Ultra's FREE agents for execution = 90%+ cost savings with full automation.

### Current State
- Using Cursor's Claude Sonnet 4.5 for orchestration
- Using Cursor's Composer (cheaper sub-agents) for execution
- Paying Cursor's markup (~20%) + inefficient token usage

### Target State (RECOMMENDED)
- **Orchestration**: Claude Code CLI ($3/1M input, $15/1M output)
- **Execution**: Cursor agents with `model: auto` (FREE with Ultra plan)
- **Automation**: Cursor CLI enables fully automated workflow
- **Total cost**: ~$6-10 for 24 repos (vs $80+ all-Cursor)

### Cost Comparison (Updated)

| Approach | Orchestration | Execution | Total (24 repos) | Savings |
|----------|--------------|-----------|------------------|---------|
| **All-Cursor** | $60+ | $20+ | **$80+** | Baseline |
| **Hybrid (RECOMMENDED)** | Claude Code CLI: $6-10 | Cursor (model: auto): **$0** | **$6-10** | **90%+** |
| Claude Code only | $6-10 | Haiku: $9-10 | $15-20 | 75% |

**Winner**: Hybrid approach (Claude Code CLI + Cursor Ultra `model: auto`)

---

## 🔗 Dependencies

**None** - Can be implemented immediately.

---

## 🚧 Blockers

- [ ] Need Anthropic API key (free to create) - for Claude Code CLI
- [ ] Need to install Claude Code CLI
- [ ] Need to add Cursor CLI to PATH (for automation)
- [ ] Need Cursor Ultra plan (for FREE `model: auto`)

---

## 🛠️ Implementation Steps

### Step 1: Install Claude Code CLI

```bash
# Install Claude Code CLI (if not already installed)
# Visit: https://docs.anthropic.com/en/docs/claude-code

# Verify installation
claude --version
```

### Step 2: Get Anthropic API Key

1. Go to https://console.anthropic.com
2. Sign up or log in
3. Navigate to API Keys section
4. Create new API key
5. Copy the key (starts with `sk-ant-...`)

### Step 3: Add API Key to Environment

```bash
# Add to ~/.zshrc (or ~/.bashrc)
echo 'export ANTHROPIC_API_KEY="sk-ant-your-key-here"' >> ~/.zshrc
source ~/.zshrc

# Verify it's set
echo $ANTHROPIC_API_KEY
```

### Step 4: Add Cursor CLI to PATH (For Automation)

```bash
# Add Cursor CLI to PATH
echo 'export PATH="/Applications/Cursor.app/Contents/Resources/app/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify it works
cursor --version
# Should show: Cursor 2.5.20 (or similar)
```

### Step 5: Test Claude Code CLI

```bash
# Launch Claude Code CLI
claude

# Test basic command
> pwd
> ls -la

# Test reading files
> cat .cursor/plans/code_optimizations_and_ci_cd_alignment/README.md
```

### Step 6: Test Cursor Agent CLI (Automation)

```bash
# Test Cursor agent in print mode
cursor agent --print --model auto "What is 2+2?"

# Should output the answer
# This confirms automation will work!
```

### Step 7: Choose Your Workflow

**Option A: Fully Automated (RECOMMENDED)**
- Claude Code CLI calls `cursor agent` CLI directly
- No manual steps
- See: `.cursor/plans/tasks_claude_code/AUTOMATED_QUICK_START.md`

**Option B: Manual Bridging**
- Claude Code CLI generates prompts
- You copy/paste to Cursor IDE
- Launch agents with `model: auto`
- See: `.cursor/plans/tasks_claude_code/QUICK_START.md`

---

## ✅ Verification

### Check 1: Claude Code CLI Working

```bash
# Test Claude Code CLI
claude

# Should launch interactive session
# Type: exit (to quit)
```

### Check 2: Cursor CLI Working

```bash
# Test Cursor CLI
cursor --version
# Should show: Cursor 2.5.20 (or similar)

# Test Cursor agent
cursor agent --print --model auto "What is 2+2?"
# Should output the answer
```

### Check 3: Cursor Ultra Plan Active

```bash
# In Cursor IDE, check:
# Settings → Account → Plan
# Should show: "Ultra" or "Pro"
```

### Check 4: Model Auto is FREE

```bash
# Launch a test agent
cursor agent --print --model auto "List files in current directory"

# Check Cursor usage (should not charge)
# Settings → Usage
# model: auto should show as included in plan
```

### Check 5: Automation Works

```bash
# Test full automation
claude

> Run this command:
> cursor agent --print --model auto --workspace . "Count Python files in this directory"

# Should execute and show results
# This confirms Claude Code can call Cursor agent!
```

---

## 📊 Success Metrics

- [ ] Claude Code CLI installed and working
- [ ] Anthropic API key configured
- [ ] Cursor CLI added to PATH
- [ ] `cursor agent --print --model auto` works
- [ ] Cursor Ultra plan active (for FREE model: auto)
- [ ] Can run fully automated workflow
- [ ] Total cost: ~$6-10 for 24 repos (vs $80+ all-Cursor)

---

## 🔄 Rollback Plan

If Claude Code integration causes issues:

1. Open Cursor Settings
2. Switch back to Cursor's built-in models
3. Remove Anthropic provider (optional)
4. Continue using Cursor's default pricing

No data loss or workflow disruption.

---

## 📚 Related Documentation

**Automated Workflow (RECOMMENDED)**:
- `.cursor/plans/tasks_claude_code/AUTOMATED_QUICK_START.md` - ⭐ Start here
- `.cursor/plans/tasks_claude_code/AUTOMATED_WORKFLOW.md` - How automation works
- `.cursor/plans/tasks_claude_code/COST_COMPARISON.md` - Detailed cost breakdown

**Manual Workflow (Fallback)**:
- `.cursor/plans/tasks_claude_code/QUICK_START.md` - Manual bridging
- `.cursor/plans/tasks_claude_code/TWO_STEP_WORKFLOW.md` - Understanding manual approach

**General**:
- ChatGPT conversation: `chat-gpt-code-optimizations-llm.md`
- Anthropic API docs: https://docs.anthropic.com/en/api/getting-started
- Cursor CLI docs: `cursor agent --help`

---

## 🐛 Troubleshooting

### Issue: "claude: command not found"

**Solution**:
- Claude Code CLI not installed or not in PATH
- Install from: https://docs.anthropic.com/en/docs/claude-code
- Or add to PATH: `export PATH="~/.local/bin:$PATH"`

### Issue: "cursor: command not found"

**Solution**:
- Cursor CLI not in PATH
- Add to ~/.zshrc: `export PATH="/Applications/Cursor.app/Contents/Resources/app/bin:$PATH"`
- Run: `source ~/.zshrc`

### Issue: "cursor agent" charges money

**Solution**:
- Not using `--model auto`
- Always use: `cursor agent --print --model auto ...`
- Verify Cursor Ultra plan is active

### Issue: "Automation doesn't work"

**Solution**:
- Cursor CLI may need `--trust` flag for workspace
- Add: `cursor agent --print --model auto --trust ...`
- Or approve manually first time

---

## 💡 Tips

1. **Use fully automated workflow**: Cursor CLI enables zero manual steps
2. **Always use `--model auto`**: FREE with Cursor Ultra (never use `--model fast`)
3. **Track costs**: Monitor Anthropic console for Claude Code CLI usage only
4. **Test automation first**: Run `cursor agent --print --model auto "test"` to verify
5. **Use `--trust` flag**: Avoids security prompts in automation

---

## ✏️ Notes

**Key Insights**:
- Cursor Ultra includes unlimited `model: auto` usage (FREE)
- Cursor CLI enables full automation (no manual bridging)
- Claude Code CLI only pays for orchestration (~$6-10 for 24 repos)
- Total savings: 90%+ vs all-Cursor approach ($80+)

**Workflow**:
- Claude Code CLI: Orchestrates, generates prompts, verifies
- Cursor agent CLI: Executes changes (FREE with `--model auto`)
- No manual copy/paste needed (fully automated)

**Expected savings**: $70-74 per 24 repos, or $840-888/year if done monthly
