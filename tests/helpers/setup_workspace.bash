#!/usr/bin/env bash
# setup_workspace.bash — shared bats helpers for unified-trading-pm tests
# Sourced by each test file via: load "helpers/setup_workspace.bash"

# Creates a realistic fake workspace in $BATS_TMPDIR:
#
#   <tmp>/workspace/
#   ├── .cursor/
#   │   ├── rules/           ← local working copy
#   │   │   └── *.mdc
#   │   └── workspace-configs/
#   ├── .cursorrules
#   ├── unified-trading-pm/  ← fake PM repo (with .git/)
#   │   ├── cursor-rules/
│   │   ├── cursor-configs/
#   │   ├── scripts/ -> symlinked to real scripts (or copied)
#   │   └── workspace-manifest.json
#   ├── unified-trading-codex/   ← sibling (just a dir, no .git needed)
#   └── instruments-service/     ← sibling
#
# Scripts under test are invoked with PM_ROOT / WORKSPACE_ROOT overridden.

setup_fake_workspace() {
    FAKE_WORKSPACE="$BATS_TMPDIR/workspace"
    FAKE_PM="$FAKE_WORKSPACE/unified-trading-pm"
    FAKE_CURSOR_RULES="$FAKE_WORKSPACE/.cursor/rules"
    FAKE_CURSOR_CONFIGS="$FAKE_WORKSPACE/.cursor/workspace-configs"
    FAKE_PM_CURSOR_RULES="$FAKE_PM/cursor-rules"
    FAKE_PM_CURSOR_CONFIGS="$FAKE_PM/cursor-configs"

    rm -rf "$FAKE_WORKSPACE"

    # Workspace root structure
    mkdir -p "$FAKE_CURSOR_RULES"
    mkdir -p "$FAKE_CURSOR_CONFIGS"
    touch "$FAKE_WORKSPACE/.cursorrules"

    # Known sibling repos (just dirs — validation only checks existence)
    mkdir -p "$FAKE_WORKSPACE/unified-trading-codex"
    mkdir -p "$FAKE_WORKSPACE/instruments-service"

    # PM repo with .git
    mkdir -p "$FAKE_PM_CURSOR_RULES"
    mkdir -p "$FAKE_PM_CURSOR_CONFIGS"
    mkdir -p "$FAKE_PM/scripts"
    mkdir -p "$FAKE_PM/.git"  # makes it a "git repo" for validation

    # Minimal workspace-manifest.json
    echo '{"title":"test","repositories":{}}' > "$FAKE_PM/workspace-manifest.json"

    # Seed .cursor/rules with 3 test rules
    echo "# rule one"  > "$FAKE_CURSOR_RULES/rule-one.mdc"
    echo "# rule two"  > "$FAKE_CURSOR_RULES/rule-two.mdc"
    echo "# rule three" > "$FAKE_CURSOR_RULES/rule-three.mdc"

    # Copy real scripts into fake PM so they run with correct relative paths
    REAL_SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)/scripts"
    cp "$REAL_SCRIPTS_DIR/_workspace-lib.sh"     "$FAKE_PM/scripts/"
    cp "$REAL_SCRIPTS_DIR/sync-rules-push.sh"    "$FAKE_PM/scripts/"
    cp "$REAL_SCRIPTS_DIR/sync-rules-pull.sh"    "$FAKE_PM/scripts/"
    cp "$REAL_SCRIPTS_DIR/sync-workspace.sh"     "$FAKE_PM/scripts/"
    chmod +x "$FAKE_PM/scripts/"*.sh

    export FAKE_WORKSPACE FAKE_PM FAKE_CURSOR_RULES FAKE_CURSOR_CONFIGS
    export FAKE_PM_CURSOR_RULES FAKE_PM_CURSOR_CONFIGS
}

teardown_fake_workspace() {
    rm -rf "$FAKE_WORKSPACE"
}

# Seed N rules into repo cursor-rules/ (for pull tests)
seed_repo_rules() {
    local count="${1:-3}"
    for i in $(seq 1 "$count"); do
        echo "# repo rule $i" > "$FAKE_PM_CURSOR_RULES/repo-rule-${i}.mdc"
    done
}

# Count .mdc files in a directory
count_mdc() {
    find "$1" -maxdepth 1 -name "*.mdc" 2>/dev/null | wc -l | tr -d ' '
}
