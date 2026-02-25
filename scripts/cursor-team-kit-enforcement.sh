#!/bin/bash
# Cursor Team Kit Enforcement
# Shared script to prompt for Cursor Team Kit usage in quickmerge workflows
# Source this script from quickmerge.sh to enable enforcement prompts

# Function: Prompt for deslop (code cleanup)
prompt_deslop() {
    local repo_name="$1"
    echo ""
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│ 🧹 Cursor Team Kit: Optional Code Cleanup                  │"
    echo "│                                                             │"
    echo "│ Before proceeding, consider running:                        │"
    echo "│   /deslop  - Remove AI-generated code slop                 │"
    echo "│                                                             │"
    echo "│ This will clean up:                                         │"
    echo "│   • Unnecessary comments                                    │"
    echo "│   • Verbose code patterns                                   │"
    echo "│   • Redundant error handling                                │"
    echo "│                                                             │"
    echo "│ Press Enter to continue or Ctrl+C to abort...              │"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo ""
    read -t 10 -p "Continue? (auto-continues in 10s): " || true
}

# Function: Prompt for run-smoke-tests (UI repos only)
prompt_smoke_tests() {
    local repo_name="$1"
    
    # Only show for UI repos
    if [[ "$repo_name" == *"-ui" ]]; then
        echo ""
        echo "┌─────────────────────────────────────────────────────────────┐"
        echo "│ 🎭 Cursor Team Kit: UI Validation (Optional)               │"
        echo "│                                                             │"
        echo "│ This is a UI repo. Consider running:                        │"
        echo "│   /run-smoke-tests  - Run Playwright smoke tests           │"
        echo "│                                                             │"
        echo "│ This validates:                                             │"
        echo "│   • Critical user flows                                     │"
        echo "│   • No UI regressions                                       │"
        echo "│   • Key features load properly                              │"
        echo "│                                                             │"
        echo "│ Press Enter to continue or Ctrl+C to abort...              │"
        echo "└─────────────────────────────────────────────────────────────┘"
        echo ""
        read -t 10 -p "Continue? (auto-continues in 10s): " || true
    fi
}

# Function: Show ci-watcher instructions after PR creation
show_ci_watcher_prompt() {
    local repo_name="$1"
    local pr_num="$2"
    local pr_url="$3"
    
    echo ""
    echo "┌─────────────────────────────────────────────────────────────┐"
    echo "│ 🤖 Cursor Team Kit: CI Monitoring (AUTOMATIC)              │"
    echo "│                                                             │"
    echo "│ ✅ PR Created: #$pr_num                                      │"
    echo "│                                                             │"
    echo "│ Next steps for Cursor agent:                                │"
    echo "│   1. AUTOMATICALLY start ci-watcher subagent               │"
    echo "│      (monitors CI and reports results)                      │"
    echo "│                                                             │"
    echo "│   2. If CI fails, use:                                      │"
    echo "│      /fix-ci        - Fix issues                           │"
    echo "│      /loop-on-ci    - Iterate until pass                   │"
    echo "│                                                             │"
    echo "│   3. For review comments:                                   │"
    echo "│      /get-pr-comments - Fetch and address                  │"
    echo "│                                                             │"
    echo "│ PR URL: $pr_url                                            │"
    echo "│                                                             │"
    echo "│ 📋 Agent instruction: Start ci-watcher NOW                 │"
    echo "└─────────────────────────────────────────────────────────────┘"
    echo ""
}

# Export functions so they can be called from quickmerge scripts
export -f prompt_deslop
export -f prompt_smoke_tests
export -f show_ci_watcher_prompt
