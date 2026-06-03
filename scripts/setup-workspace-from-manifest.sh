#!/usr/bin/env bash
#
# setup-workspace-from-manifest.sh — Manifest-driven workspace bootstrap (SSOT in PM)
#
# Reads workspace-manifest.json to determine direct dependencies for SERVICE_NAME,
# clones them as siblings, runs pre-flight checks, and installs all Python deps.
#
# Usage:
#   bash scripts/setup-workspace-from-manifest.sh <SERVICE_NAME> [--skip-install]
#
# Environment:
#   WORKSPACE_ROOT   Parent dir where sibling repos are cloned (required)
#   GH_TOKEN         GitHub PAT with repo scope (or GITHUB_TOKEN)
#   GH_ORG           GitHub org (default: IggyIkenna)
#   DEP_BRANCH       Branch to try first for each dep (default: main)
#   MANIFEST_PATH    Path to workspace-manifest.json (default: auto-resolved from PM dir)
#
# Pre-flight checks performed after cloning:
#   1. Required dep clone success  → exit 1 on failure
#   2. Optional dep clone failure  → warn, continue
#   3. Dep pyproject.toml version vs manifest constraint → warn if mismatch
#   4. Missing pyproject.toml in dep          → warn
#
set -euo pipefail

SERVICE_NAME="${1:-}"
if [ -z "$SERVICE_NAME" ]; then
    echo "❌ Usage: $0 <SERVICE_NAME> [--skip-install]" >&2
    exit 1
fi

SKIP_INSTALL=false
for arg in "${@:2}"; do
    [[ "$arg" == "--skip-install" ]] && SKIP_INSTALL=true
done

GH_ORG="${GH_ORG:-IggyIkenna}"
DEP_BRANCH="${DEP_BRANCH:-main}"
GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(dirname "$SCRIPT_DIR")"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(dirname "$PM_DIR")}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}" >&2; exit 1; }
info() { echo -e "${BLUE}ℹ️  $1${NC}"; }

PREFLIGHT_ERRORS=0
PREFLIGHT_WARNS=0

# ── MANIFEST LOCATION ────────────────────────────────────────────────────────
MANIFEST_PATH="${MANIFEST_PATH:-$PM_DIR/workspace-manifest.json}"
if [ ! -f "$MANIFEST_PATH" ]; then
    fail "workspace-manifest.json not found at $MANIFEST_PATH — is unified-trading-pm cloned?"
fi

# ── PARSE DEPS FROM MANIFEST ─────────────────────────────────────────────────
# Extracts dependencies for SERVICE_NAME from manifest JSON.
# Outputs lines: "repo_name required/optional constraint"
parse_deps() {
    python3 - "$MANIFEST_PATH" "$SERVICE_NAME" <<'PYEOF'
import json, sys

manifest_path, service_name = sys.argv[1], sys.argv[2]
with open(manifest_path) as f:
    manifest = json.load(f)

repos = manifest.get("repositories", {})
if service_name not in repos:
    # Not fatal — service may not be in manifest yet (new repo)
    print(f"WARN:not_in_manifest", flush=True)
    sys.exit(0)

repo_data = repos[service_name]
deps = repo_data.get("dependencies", [])

for dep in deps:
    if isinstance(dep, dict):
        name       = dep.get("name", "")
        required   = "required" if dep.get("required", True) else "optional"
        constraint = dep.get("version", "any")
    else:
        name, required, constraint = str(dep), "required", "any"
    if name:
        print(f"{name} {required} {constraint}")
PYEOF
}

# ── VERSION CONSTRAINT CHECK ─────────────────────────────────────────────────
# Returns 0 if installed_version satisfies constraint, 1 otherwise.
check_version_constraint() {
    local installed="$1"
    local constraint="$2"
    python3 - "$installed" "$constraint" <<'PYEOF'
import sys
try:
    from packaging.version import Version
    from packaging.specifiers import SpecifierSet
    installed, constraint = sys.argv[1], sys.argv[2]
    if constraint in ("any", "", "latest"):
        sys.exit(0)
    spec = SpecifierSet(constraint)
    sys.exit(0 if Version(installed) in spec else 1)
except Exception:
    sys.exit(0)  # packaging not available — skip constraint check
PYEOF
}

# ── CLONE HELPER ─────────────────────────────────────────────────────────────
clone_repo() {
    local repo="$1"
    local required="$2"   # "required" or "optional"
    local constraint="${3:-any}"
    local dest="$WORKSPACE_ROOT/$repo"

    if [ -d "$dest" ]; then
        info "$repo: already present at $dest"
        preflight_check_version "$repo" "$constraint"
        return 0
    fi

    if [ -z "$GH_TOKEN" ]; then
        warn "GH_TOKEN not set — cloning $repo without auth (may fail for private repos)"
        local url="https://github.com/${GH_ORG}/${repo}.git"
    else
        local url="https://x-access-token:${GH_TOKEN}@github.com/${GH_ORG}/${repo}.git"
    fi

    echo "  Cloning $repo (branch: $DEP_BRANCH)..."
    if git clone --depth=1 -b "$DEP_BRANCH" "$url" "$dest" 2>/dev/null \
        || git clone --depth=1 -b main "$url" "$dest" 2>/dev/null; then
        ok "$repo cloned"
        preflight_check_version "$repo" "$constraint"
    else
        if [ "$required" = "required" ]; then
            echo -e "${RED}❌ PREFLIGHT FAIL: required dep '$repo' failed to clone${NC}" >&2
            PREFLIGHT_ERRORS=$((PREFLIGHT_ERRORS + 1))
        else
            warn "PREFLIGHT WARN: optional dep '$repo' failed to clone (continuing)"
            PREFLIGHT_WARNS=$((PREFLIGHT_WARNS + 1))
        fi
    fi
}

# ── VERSION PREFLIGHT ─────────────────────────────────────────────────────────
preflight_check_version() {
    local repo="$1"
    local constraint="$2"
    local dest="$WORKSPACE_ROOT/$repo"

    [[ "$constraint" == "any" || -z "$constraint" ]] && return 0
    [ -d "$dest" ] || return 0

    local pyproject="$dest/pyproject.toml"
    if [ ! -f "$pyproject" ]; then
        warn "PREFLIGHT WARN: $repo has no pyproject.toml — cannot verify version constraint '$constraint'"
        PREFLIGHT_WARNS=$((PREFLIGHT_WARNS + 1))
        return 0
    fi

    local installed_version
    installed_version=$(python3 -c "
import re, sys
content = open('$pyproject').read()
m = re.search(r'^version\s*=\s*[\"\']([\d.]+)[\"\']\s*$', content, re.MULTILINE)
print(m.group(1) if m else '')
" 2>/dev/null || echo "")

    if [ -z "$installed_version" ]; then
        warn "PREFLIGHT WARN: could not parse version from $repo/pyproject.toml"
        PREFLIGHT_WARNS=$((PREFLIGHT_WARNS + 1))
        return 0
    fi

    if check_version_constraint "$installed_version" "$constraint"; then
        ok "  $repo==$installed_version satisfies $constraint"
    else
        warn "PREFLIGHT WARN: $repo==$installed_version does NOT satisfy manifest constraint $constraint"
        PREFLIGHT_WARNS=$((PREFLIGHT_WARNS + 1))
    fi
}

# ── MAIN ──────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Manifest-driven workspace bootstrap: $SERVICE_NAME"
echo "  WORKSPACE_ROOT: $WORKSPACE_ROOT"
echo "  MANIFEST: $MANIFEST_PATH"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "--- Parsing dependencies from manifest ---"

DEP_LIST=$(parse_deps 2>/dev/null || echo "")

if echo "$DEP_LIST" | grep -q "^WARN:not_in_manifest"; then
    warn "$SERVICE_NAME not found in workspace-manifest.json — cloning tooling repos only"
fi

echo ""
echo "--- Cloning manifest dependencies ---"

INSTALL_DIRS=()

while IFS=' ' read -r dep_name dep_required dep_constraint; do
    [ -z "$dep_name" ] && continue
    [[ "$dep_name" == WARN:* ]] && continue
    clone_repo "$dep_name" "$dep_required" "$dep_constraint"
    if [ -d "$WORKSPACE_ROOT/$dep_name" ]; then
        INSTALL_DIRS+=("$WORKSPACE_ROOT/$dep_name")
    fi
done <<< "$DEP_LIST"

# ── ALWAYS CLONE TOOLING REPOS ────────────────────────────────────────────────
echo ""
echo "--- Cloning tooling repos ---"
if [ ! -d "$WORKSPACE_ROOT/unified-trading-pm" ]; then
    clone_repo "unified-trading-pm" "required" "any"
else
    info "unified-trading-pm: already present"
fi
# codex/ is folded into unified-trading-pm at unified-trading-pm/codex/ — the standalone
# unified-trading-codex repo is ARCHIVED. Do NOT clone it; consumers read from PM/codex/.

# ── AGENT FILES SETUP ────────────────────────────────────────────────────────
# Cursor rules: copied as real files (ephemeral, NOT symlinks, NOT committed).
#   - Per-repo cursor rule symlinks clutter Cursor IDE (it reads all 60+ repos at once).
#   - GHA runners are ephemeral; files vanish after the job.
#   - Cleanup function registered via trap so they are removed before quickmerge
#     if setup-workspace.sh and the agent share a process context; otherwise
#     the GHA runner wipe handles it naturally.
#
# CLAUDE.md: committed symlink in each repo (via rollout-agent-symlinks.sh).
# AGENTS.md: ephemeral — copied to workspace root here, removed by cleanup before quickmerge.
echo ""
echo "--- Setting up agent files ---"

PM_DEST="$WORKSPACE_ROOT/unified-trading-pm"
SERVICE_DIR="$WORKSPACE_ROOT/$SERVICE_NAME"

_symlink() {
    local link_path="$1"
    local target="$2"
    local label="$3"
    mkdir -p "$(dirname "$link_path")"
    ln -sfn "$target" "$link_path"
    ok "  $label"
}

# Workspace-root level symlinks (for Claude Code traversal + IDE at workspace root)
if [ -f "$PM_DEST/cursor-configs/CLAUDE.md" ]; then
    _symlink "$WORKSPACE_ROOT/.claude/CLAUDE.md" "$PM_DEST/cursor-configs/CLAUDE.md" "workspace .claude/CLAUDE.md → PM/cursor-configs/CLAUDE.md"
fi

# Cursor rules: COPY as real files (ephemeral, not committed, not symlinks)
# Written to workspace root so agents and IDE can find them without per-repo noise.
EPHEMERAL_CURSOR_RULES=""
if [ -d "$PM_DEST/.cursor/rules" ]; then
    EPHEMERAL_CURSOR_RULES="$WORKSPACE_ROOT/.cursor/rules"
    mkdir -p "$WORKSPACE_ROOT/.cursor"
    rm -rf "$WORKSPACE_ROOT/.cursor/rules"
    cp -r "$PM_DEST/.cursor/rules" "$WORKSPACE_ROOT/.cursor/rules"
    ok "  workspace .cursor/rules ← copied from PM/.cursor/rules/ (ephemeral)"
fi
if [ -f "$PM_DEST/cursor-configs/cursorrules" ]; then
    cp "$PM_DEST/cursor-configs/cursorrules" "$WORKSPACE_ROOT/.cursorrules"
    ok "  workspace .cursorrules ← copied from PM/cursor-configs/cursorrules (ephemeral)"
fi

# AGENTS.md: COPY as real file (ephemeral, removed by cleanup before quickmerge)
if [ -f "$PM_DEST/AGENTS.md" ]; then
    cp "$PM_DEST/AGENTS.md" "$WORKSPACE_ROOT/AGENTS.md"
    ok "  workspace AGENTS.md ← copied from PM/AGENTS.md (ephemeral)"
fi

# Cleanup function: removes ephemeral cursor files before git operations.
# Call explicitly in run-agent.sh / agent-audit.yml BEFORE quickmerge.
cleanup_ephemeral_cursor_files() {
    rm -rf "$WORKSPACE_ROOT/.cursor/rules" "$WORKSPACE_ROOT/.cursorrules" 2>/dev/null || true
    rm -f "$WORKSPACE_ROOT/AGENTS.md" 2>/dev/null || true
    [ -n "$SERVICE_DIR" ] && rm -rf "$SERVICE_DIR/.cursor/rules" "$SERVICE_DIR/.cursorrules" 2>/dev/null || true
    info "Ephemeral cursor files cleaned up"
}
export -f cleanup_ephemeral_cursor_files 2>/dev/null || true
# Write cleanup script so run-agent.sh / GHA can call it as a step
CLEANUP_SCRIPT="$WORKSPACE_ROOT/.cleanup-cursor-rules.sh"
cat > "$CLEANUP_SCRIPT" <<CLEANUP
#!/usr/bin/env bash
# Auto-generated by setup-workspace-from-manifest.sh — call before quickmerge
rm -rf "$WORKSPACE_ROOT/.cursor/rules" "$WORKSPACE_ROOT/.cursorrules" 2>/dev/null || true
rm -f "$WORKSPACE_ROOT/AGENTS.md" 2>/dev/null || true
rm -rf "$SERVICE_DIR/.cursor/rules" "$SERVICE_DIR/.cursorrules" 2>/dev/null || true
echo "Ephemeral cursor rules and AGENTS.md cleaned up"
CLEANUP
chmod +x "$CLEANUP_SCRIPT"
ok "  cleanup script → $CLEANUP_SCRIPT (call before quickmerge)"

# ── PREFLIGHT SUMMARY ─────────────────────────────────────────────────────────
echo ""
echo "--- Pre-flight summary ---"
if [ "$PREFLIGHT_ERRORS" -gt 0 ]; then
    echo -e "${RED}❌ PREFLIGHT FAILED: $PREFLIGHT_ERRORS required dep(s) could not be cloned${NC}" >&2
    echo -e "${YELLOW}   Warnings: $PREFLIGHT_WARNS${NC}"
    exit 1
elif [ "$PREFLIGHT_WARNS" -gt 0 ]; then
    warn "Pre-flight passed with $PREFLIGHT_WARNS warning(s) — check version constraints above"
else
    ok "All pre-flight checks passed"
fi

# ── INSTALL PYTHON DEPS ───────────────────────────────────────────────────────
if $SKIP_INSTALL; then
    info "Skipping Python install (--skip-install)"
    ok "Workspace bootstrap complete (install skipped): $WORKSPACE_ROOT"
    exit 0
fi

echo ""
echo "--- Installing Python dependencies ---"
command -v uv &>/dev/null || pip install uv --quiet

for dep_dir in "${INSTALL_DIRS[@]}"; do
    dep_name="$(basename "$dep_dir")"
    if [ -f "$dep_dir/pyproject.toml" ]; then
        uv pip install -e "$dep_dir" --quiet 2>/dev/null \
            && ok "installed $dep_name" \
            || warn "install failed for $dep_name (continuing)"
    fi
done

# Install the service itself
SERVICE_DIR="$WORKSPACE_ROOT/$SERVICE_NAME"
if [ -d "$SERVICE_DIR" ] && [ -f "$SERVICE_DIR/pyproject.toml" ]; then
    uv pip install -e "$SERVICE_DIR[dev]" --quiet 2>/dev/null \
        && ok "installed $SERVICE_NAME[dev]" \
        || uv pip install -e "$SERVICE_DIR" --quiet 2>/dev/null \
        && ok "installed $SERVICE_NAME" \
        || { echo -e "${RED}❌ failed to install $SERVICE_NAME${NC}" >&2; exit 1; }
fi

# ── GIT IDENTITY (for agent commit steps) ────────────────────────────────────
git config --global user.email "${GIT_USER_EMAIL:-agent@ci.local}" 2>/dev/null || true
git config --global user.name "${GIT_USER_NAME:-Audit Agent}" 2>/dev/null || true

echo ""
ok "Workspace bootstrap complete: $WORKSPACE_ROOT"
echo "  Service:  $SERVICE_NAME"
echo "  Deps:     ${#INSTALL_DIRS[@]} cloned from manifest"
echo "  Warnings: $PREFLIGHT_WARNS"
