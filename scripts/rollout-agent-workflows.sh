#!/usr/bin/env bash
#
# rollout-agent-workflows.sh — Roll out autonomous agent workflows to all service repos
#
# Copies agent-audit.yml, semver-agent.yml, and plan-alignment-agent.yml from templates
# to each target repo listed in workspace-manifest.json, substituting per-repo values.
#
# Usage:
#   bash scripts/rollout-agent-workflows.sh [--dry-run] [--repo REPO_NAME] [--secrets]
#
# Options:
#   --dry-run   Show what would be done without writing files or pushing
#   --repo      Rollout to a single repo only (by name in manifest)
#   --secrets   Set ANTHROPIC_API_KEY + GH_PAT secrets on each repo (requires env vars)
#
# Secrets env vars (for --secrets mode):
#   ANTHROPIC_API_KEY_VALUE  — value to set
#   GH_PAT_VALUE             — value to set
#   TELEGRAM_BOT_TOKEN_VALUE — optional
#   TELEGRAM_CHAT_ID_VALUE   — optional
#
# Idempotent: skips repos where all target workflows already match templates.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(dirname "$SCRIPT_DIR")"
TEMPLATES_DIR="$SCRIPT_DIR/templates"
MANIFEST="$PM_ROOT/workspace-manifest.json"
GH_ORG="${GH_ORG:-IggyIkenna}"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(dirname "$PM_ROOT")}"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log_section() { echo -e "\n${BLUE}══ $1 ══${NC}"; }
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }

# ── PARSE ARGS ────────────────────────────────────────────────────────────────
DRY_RUN=false
TARGET_REPO=""
SET_SECRETS=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true ;;
        --repo) TARGET_REPO="$2"; shift ;;
        --secrets) SET_SECRETS=true ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
    shift
done

[ "$DRY_RUN" = true ] && warn "DRY RUN mode — no files will be written or pushed"

# ── VALIDATE TEMPLATES ────────────────────────────────────────────────────────
log_section "Validating templates"
TEMPLATE_AGENT_AUDIT=""
# Agent audit template: use market-tick-data-service's workflow as the source
PROTOTYPE_AUDIT="$WORKSPACE_ROOT/market-tick-data-service/.github/workflows/agent-audit.yml"
if [ -f "$PROTOTYPE_AUDIT" ]; then
    TEMPLATE_AGENT_AUDIT="$PROTOTYPE_AUDIT"
    ok "agent-audit.yml template: $PROTOTYPE_AUDIT"
else
    fail "agent-audit.yml prototype not found at $PROTOTYPE_AUDIT"
    exit 1
fi

[ -f "$TEMPLATES_DIR/semver-agent.yml" ] && ok "semver-agent.yml template found" || { fail "semver-agent.yml template missing at $TEMPLATES_DIR/semver-agent.yml"; exit 1; }
[ -f "$TEMPLATES_DIR/plan-alignment-agent.yml" ] && ok "plan-alignment-agent.yml template found" || { fail "plan-alignment-agent.yml template missing"; exit 1; }

# ── GET TARGET REPOS FROM MANIFEST ───────────────────────────────────────────
log_section "Reading workspace manifest"

# Get service + api repos (the ones that get agent-audit.yml rolled out)
TARGET_REPOS=$(python3 - "$MANIFEST" <<'EOF'
import json, sys
with open(sys.argv[1]) as f:
    m = json.load(f)
repos = m.get("repositories", {})
# Roll out to service, api tiers (not libraries, pm, codex, devops)
ROLLOUT_TIERS = {"service", "api"}
for name, info in repos.items():
    tier = str(info.get("arch_tier", ""))
    if tier in ROLLOUT_TIERS or any(t in tier for t in ROLLOUT_TIERS):
        # Skip PM and codex (they have their own workflows)
        if name not in ("unified-trading-pm", "unified-trading-codex"):
            print(name)
EOF
"$MANIFEST" 2>/dev/null || echo "")

# Fallback to hardcoded list if python parse fails
if [ -z "$TARGET_REPOS" ]; then
    warn "Manifest parse failed — using hardcoded service list"
    TARGET_REPOS="market-tick-data-service market-data-processing-service instruments-service features-calendar-service features-delta-one-service features-volatility-service features-onchain-service features-sports-service execution-service strategy-service ml-inference-service pnl-attribution-service risk-and-exposure-service position-balance-monitor-service"
fi

# Filter to single repo if --repo specified
if [ -n "$TARGET_REPO" ]; then
    TARGET_REPOS="$TARGET_REPO"
    echo "Single repo mode: $TARGET_REPO"
fi

echo "Target repos: $(echo "$TARGET_REPOS" | wc -w)"

# ── ROLLOUT FUNCTION ──────────────────────────────────────────────────────────
rollout_repo() {
    local REPO="$1"
    local REPO_DIR="$WORKSPACE_ROOT/$REPO"

    echo ""
    echo "→ $REPO"

    # Check if repo is cloned locally
    if [ ! -d "$REPO_DIR/.git" ]; then
        warn "  $REPO not cloned locally — cloning..."
        if [ "$DRY_RUN" = true ]; then
            warn "  [DRY RUN] Would clone $GH_ORG/$REPO"
            return 0
        fi
        git clone "https://github.com/$GH_ORG/$REPO.git" "$REPO_DIR" --quiet || {
            fail "  Failed to clone $REPO — skipping"
            return 1
        }
    fi

    local WORKFLOWS_DIR="$REPO_DIR/.github/workflows"
    local CHANGED=false

    # Create .github/workflows if missing
    mkdir -p "$WORKFLOWS_DIR"

    # Get repo-specific values from manifest
    SERVICE_NAME="$REPO"
    SOURCE_DIR=$(python3 -c "
import json
with open('$MANIFEST') as f:
    m = json.load(f)
r = m.get('repositories', {}).get('$REPO', {})
# Infer SOURCE_DIR: replace hyphens with underscores
print('$REPO'.replace('-', '_'))
" 2>/dev/null || echo "${REPO//-/_}")

    # ── agent-audit.yml ──────────────────────────────────────────────────────
    TARGET_AUDIT="$WORKFLOWS_DIR/agent-audit.yml"
    # agent-audit.yml is the same across all service repos (no SERVICE_NAME substitution needed)
    # except the name field — substitute repo name
    NEW_CONTENT=$(sed "s|market-tick-data-service|$SERVICE_NAME|g" "$TEMPLATE_AGENT_AUDIT")
    EXISTING=$(cat "$TARGET_AUDIT" 2>/dev/null || echo "")
    if [ "$NEW_CONTENT" != "$EXISTING" ]; then
        if [ "$DRY_RUN" = true ]; then
            warn "  [DRY RUN] Would update $TARGET_AUDIT"
        else
            echo "$NEW_CONTENT" > "$TARGET_AUDIT"
            ok "  Updated agent-audit.yml"
        fi
        CHANGED=true
    else
        echo "  agent-audit.yml unchanged"
    fi

    # ── semver-agent.yml ─────────────────────────────────────────────────────
    TARGET_SEMVER="$WORKFLOWS_DIR/semver-agent.yml"
    NEW_CONTENT=$(sed "s|{{SERVICE_NAME}}|$SERVICE_NAME|g; s|{{SOURCE_DIR}}|$SOURCE_DIR|g" "$TEMPLATES_DIR/semver-agent.yml")
    EXISTING=$(cat "$TARGET_SEMVER" 2>/dev/null || echo "")
    if [ "$NEW_CONTENT" != "$EXISTING" ]; then
        if [ "$DRY_RUN" = true ]; then
            warn "  [DRY RUN] Would update $TARGET_SEMVER"
        else
            echo "$NEW_CONTENT" > "$TARGET_SEMVER"
            ok "  Updated semver-agent.yml"
        fi
        CHANGED=true
    else
        echo "  semver-agent.yml unchanged"
    fi

    # ── plan-alignment-agent.yml ─────────────────────────────────────────────
    TARGET_PLAN="$WORKFLOWS_DIR/plan-alignment-agent.yml"
    NEW_CONTENT=$(sed "s|{{SERVICE_NAME}}|$SERVICE_NAME|g" "$TEMPLATES_DIR/plan-alignment-agent.yml")
    EXISTING=$(cat "$TARGET_PLAN" 2>/dev/null || echo "")
    if [ "$NEW_CONTENT" != "$EXISTING" ]; then
        if [ "$DRY_RUN" = true ]; then
            warn "  [DRY RUN] Would update $TARGET_PLAN"
        else
            echo "$NEW_CONTENT" > "$TARGET_PLAN"
            ok "  Updated plan-alignment-agent.yml"
        fi
        CHANGED=true
    else
        echo "  plan-alignment-agent.yml unchanged"
    fi

    # ── COMMIT AND PUSH ───────────────────────────────────────────────────────
    if [ "$CHANGED" = true ] && [ "$DRY_RUN" = false ]; then
        pushd "$REPO_DIR" > /dev/null
        BRANCH="chore/rollout-agent-workflows-$(date +%Y%m%d-%H%M%S)"
        # Stash all local changes (avoids quickmerge dep-check; we only want workflow files)
        git stash push --include-untracked -m "rollout-preserve-$REPO" -q 2>/dev/null || true
        git checkout -b "$BRANCH" 2>/dev/null
        # Write workflow files fresh on this branch (re-apply from template)
        mkdir -p .github/workflows
        sed "s|market-tick-data-service|$SERVICE_NAME|g" "$TEMPLATE_AGENT_AUDIT" > .github/workflows/agent-audit.yml
        sed "s|{{SERVICE_NAME}}|$SERVICE_NAME|g; s|{{SOURCE_DIR}}|$SOURCE_DIR|g" "$TEMPLATES_DIR/semver-agent.yml" > .github/workflows/semver-agent.yml
        sed "s|{{SERVICE_NAME}}|$SERVICE_NAME|g" "$TEMPLATES_DIR/plan-alignment-agent.yml" > .github/workflows/plan-alignment-agent.yml
        git add .github/workflows/agent-audit.yml .github/workflows/semver-agent.yml .github/workflows/plan-alignment-agent.yml
        if git diff --cached --quiet; then
            echo "  Nothing staged after stash — skipping"
            git checkout main -q 2>/dev/null || true
        else
            if git commit -m "chore: rollout autonomous agent workflows (agent-audit, semver, plan-alignment)" -q 2>&1; then
                git push -u origin "$BRANCH" -q 2>/dev/null \
                    && gh pr create --title "chore: rollout autonomous agent workflows" \
                        --body "Adds agent-audit.yml (retry+Telegram), semver-agent.yml, plan-alignment-agent.yml" \
                        --base main --head "$BRANCH" 2>/dev/null \
                        | xargs -I{} sh -c "gh pr merge --auto --squash 2>/dev/null; echo '  PR: {}'" \
                    && ok "  PR created and auto-merge enabled" \
                    || warn "  push/PR failed for $REPO — check manually"
            else
                warn "  commit failed for $REPO (pre-commit hook?) — check manually"
            fi
            git checkout main -q 2>/dev/null || true
        fi
        # Restore local changes
        git stash pop -q 2>/dev/null || true
        popd > /dev/null
    fi

    # ── SET SECRETS ───────────────────────────────────────────────────────────
    if [ "$SET_SECRETS" = true ] && [ "$DRY_RUN" = false ]; then
        echo "  Setting secrets on $GH_ORG/$REPO..."
        [ -n "${ANTHROPIC_API_KEY_VALUE:-}" ] && \
            gh secret set ANTHROPIC_API_KEY --repo "$GH_ORG/$REPO" --body "$ANTHROPIC_API_KEY_VALUE" && \
            ok "  ANTHROPIC_API_KEY set" || warn "  Failed to set ANTHROPIC_API_KEY"
        [ -n "${GH_PAT_VALUE:-}" ] && \
            gh secret set GH_PAT --repo "$GH_ORG/$REPO" --body "$GH_PAT_VALUE" && \
            ok "  GH_PAT set" || warn "  Failed to set GH_PAT"
        [ -n "${TELEGRAM_BOT_TOKEN_VALUE:-}" ] && \
            gh secret set TELEGRAM_BOT_TOKEN --repo "$GH_ORG/$REPO" --body "$TELEGRAM_BOT_TOKEN_VALUE" && \
            ok "  TELEGRAM_BOT_TOKEN set"
        [ -n "${TELEGRAM_CHAT_ID_VALUE:-}" ] && \
            gh secret set TELEGRAM_CHAT_ID --repo "$GH_ORG/$REPO" --body "$TELEGRAM_CHAT_ID_VALUE" && \
            ok "  TELEGRAM_CHAT_ID set"
    fi
}

# ── MAIN ROLLOUT LOOP ─────────────────────────────────────────────────────────
log_section "Rolling out workflows"
PASS=0
FAIL=0

for REPO in $TARGET_REPOS; do
    rollout_repo "$REPO" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))
done

echo ""
log_section "Rollout Complete"
ok "Passed: $PASS"
[ "$FAIL" -gt 0 ] && fail "Failed: $FAIL" || true
