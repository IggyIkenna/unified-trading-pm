# CI/CD Alignment: Auto-Fix Watcher Add-On

**Status**: ⬜ Optional Enhancement  
**Priority**: P2 (Nice-to-have, improves DX)  
**Estimated Time**: 1-2 hours  
**Expected Benefit**: Automated fixing of CI failures

---

## 📖 Overview

Add LLM-agnostic auto-fix watcher that monitors pre-push hook (act) and automatically fixes failures.

**Inspired by**: Cursor's CI Watcher (watches GitHub Actions)  
**Improvement**: Works locally with pre-push hook, supports any LLM (Cursor, Claude Code, Aider)

---

## 🎯 Value Proposition

**Before (Manual Fix)**:
```bash
bash scripts/quickmerge.sh "fix: update" --no-watch
# ... creates PR, pushes ...
# Pre-push hook fails (act)
# ❌ You manually read errors, fix, re-push
```

**After (Auto-Fix Watcher) - DEFAULT**:
```bash
bash scripts/quickmerge.sh "fix: update"
# Watch mode is DEFAULT
# ... creates PR, pushes ...
# Pre-push hook fails (act)
# 🤖 LLM agent auto-fixes issues
# ✅ Pre-push hook re-runs and passes
# PR created successfully
```

---

## 🏗️ Architecture

### Components

1. **`llm-agent-wrapper.sh`** - Detects and uses best available LLM
   - Preference: Cursor CLI (FREE) > Claude Code > Aider
   - LLM-agnostic (works across Cursor, Claude Code, VS Code + Aider)

2. **`pre-push-watcher.sh`** - Monitors pre-push hook, triggers auto-fix
   - Runs act quality-gates
   - If fails, captures errors
   - Calls LLM agent wrapper
   - Re-runs act to verify
   - Max 3 attempts

3. **`quickmerge.sh --watch`** - Integration point
   - Optional flag: `--watch`
   - Uses pre-push-watcher instead of regular pre-push hook

### Flow Diagram

```
quickmerge.sh --watch
  │
  ├─> Pre-merge checks
  ├─> Create branch, stage, commit
  ├─> Call pre-push-watcher.sh (instead of regular hook)
  │
  └─> pre-push-watcher.sh
        │
        ├─> Run act quality-gates
        ├─> ❌ Fails?
        │
        └─> llm-agent-wrapper.sh
              │
              ├─> Detect LLM (Cursor/Claude/Aider)
              ├─> Feed errors to LLM
              ├─> LLM fixes issues
              │
              └─> Re-run act
                    ├─> ✅ Pass? → Push to GitHub
                    └─> ❌ Fail? → Retry (max 3)
```

---

## 🛠️ Implementation

### Step 1: Create LLM Agent Wrapper

**File**: `.cursor/scripts/llm-agent-wrapper.sh`

✅ Already created (see above)

**Features**:
- Auto-detects Cursor CLI, Claude Code, or Aider
- Passes error context to LLM
- Restricts edits to target repo only
- Uses FREE Cursor agent if available (Ultra plan)

### Step 2: Create Pre-Push Watcher

**File**: `.cursor/scripts/pre-push-watcher.sh`

✅ Already created (see above)

**Features**:
- Runs act quality-gates
- Captures error output
- Calls LLM agent wrapper on failure
- Re-runs act to verify fixes
- Max 3 attempts with clear error messages

### Step 3: Update Quick Merge Template

**File**: `unified-trading-codex/06-coding-standards/quickmerge-template.sh`

Add `--no-watch` flag support (watch is DEFAULT):

```bash
#!/bin/bash
# quickmerge with watch mode enabled by default

# ... existing arg parsing ...

WATCH_MODE=true  # DEFAULT: watch enabled
while [[ $# -gt 0 ]]; do
    case "$1" in
        --no-watch)
            WATCH_MODE=false
            shift
            ;;
        --files)
            FILES_ARG="$2"
            shift 2
            ;;
        *)
            COMMIT_MSG="$1"
            shift
            ;;
    esac
done

# ... existing pre-merge checks, branch creation, staging, commit ...

# Push with watcher (DEFAULT) or regular hook
if [ "$WATCH_MODE" = true ]; then
    echo "[$REPO_NAME] 🔍 Watch mode enabled (default) - will auto-fix pre-push failures"
    
    # Call pre-push watcher instead of regular push
    if ! bash "$WORKSPACE_ROOT/.cursor/scripts/pre-push-watcher.sh"; then
        echo "[$REPO_NAME] ❌ Pre-push watcher failed after max attempts"
        exit 1
    fi
    
    # Watcher passed, now do regular push (hook already satisfied)
    git push --no-verify -u origin "$NEW_BRANCH"
else
    echo "[$REPO_NAME] ⚠️  Watch mode disabled (--no-watch) - using regular pre-push hook"
    # Regular push (pre-push hook runs normally, no auto-fix)
    git push -u origin "$NEW_BRANCH"
fi

# ... rest of PR creation ...
```

### Step 4: Document Usage

**File**: `unified-trading-codex/06-coding-standards/quality-gates.md`

Add section:

```markdown
## Auto-Fix Watcher (Optional)

Automatic fixing of CI failures is **enabled by default**:

```bash
# Quickmerge with watch mode (DEFAULT - auto-fixes pre-push failures)
bash scripts/quickmerge.sh "fix: update"

# Disable watch mode (manual fixes if pre-push hook fails)
bash scripts/quickmerge.sh "fix: update" --no-watch
```

**How it works (default behavior)**:
1. Creates PR branch as usual
2. Runs pre-push hook (act quality-gates)
3. If act fails: captures errors, calls LLM agent to fix
4. Re-runs act to verify fixes (max 3 attempts)
5. Pushes when act passes

**LLM Tool Detection** (auto-selects best available):
- Cursor CLI (FREE with Ultra plan) ← Preferred
- Claude Code CLI (Anthropic API)
- Aider (OpenAI/Anthropic API)

**Setup**:
- Cursor: Already works if `cursor` in PATH
- Claude Code: `export ANTHROPIC_API_KEY=...`
- Aider: `pip install aider-chat && export OPENAI_API_KEY=...`
```

---

## 📊 Success Metrics

- [ ] `llm-agent-wrapper.sh` created and executable
- [ ] `pre-push-watcher.sh` created and executable
- [ ] Quickmerge template supports `--watch` flag
- [ ] Documentation updated in quality-gates.md
- [ ] Tested with Cursor CLI (model: auto)
- [ ] Tested with Claude Code CLI
- [ ] Works across all 32 repos
- [ ] Auto-fix success rate >70% on first attempt

---

## 🔬 Testing

### Test 1: Basic Watcher (No Failures)

```bash
cd instruments-service

# Make a valid change
echo "# test" >> README.md
git add README.md
git commit -m "test: readme update"

# Run watcher (should pass on first try)
bash /path/to/.cursor/scripts/pre-push-watcher.sh
```

**Expected**: Act passes immediately, no LLM agent called

### Test 2: Auto-Fix (Deliberate Failure)

```bash
cd instruments-service

# Introduce a ruff error
echo "import    sys" >> instruments_service/main.py
git add instruments_service/main.py
git commit -m "test: introduce ruff error"

# Run watcher (should auto-fix)
bash /path/to/.cursor/scripts/pre-push-watcher.sh
```

**Expected**:
1. Act fails (ruff error detected)
2. LLM agent called
3. LLM fixes ruff error
4. Act re-runs and passes

### Test 3: Quickmerge with Watch

```bash
cd instruments-service

# Make change
echo "# update" >> README.md

# Quickmerge with watch mode
bash scripts/quickmerge.sh "docs: update readme" --watch
```

**Expected**: Full flow works, PR created successfully

---

## 🔄 Rollback Plan

If auto-fix watcher causes issues:

1. Remove `--watch` flag from quickmerge calls
2. Use regular pre-push hook flow
3. Manual fixes as before

**Scripts remain optional** - default behavior unchanged.

---

## 💡 Tips

1. **Use watch mode selectively**: Not every push needs auto-fix
2. **Cost-effective**: Cursor CLI (model: auto) is FREE on Ultra
3. **Parallel-safe**: Each repo gets its own watcher instance
4. **Debug mode**: Check `/tmp/act-errors-*.log` for error context

---

## 🚀 Future Enhancements

1. **Smart retry**: Different fix strategies on each attempt
2. **Learning mode**: Cache successful fixes for similar errors
3. **Multi-LLM**: Try different LLMs if first one fails
4. **Partial fixes**: Accept partial progress after max attempts
5. **Metrics**: Track auto-fix success rates per error type

---

## ✏️ Notes

- Compatible with existing pre-push hook (opt-in via `--watch`)
- Works with any LLM tool (Cursor, Claude Code, Aider)
- No vendor lock-in (graceful fallback to manual fix)
- Saves 5-10 minutes per failed CI run
