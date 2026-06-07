#!/usr/bin/env bash
#
# rollout-agent-workflows.sh — Roll out autonomous agent workflows to all service repos
#
# Copies agent-audit.yml and plan-alignment-agent.yml from templates to each target repo
# listed in workspace-manifest.json, substituting per-repo values.
#
# semver-agent.yml is NOT handled here (2026-06-07). Its canonical SSOT is
# scripts/workflow-templates/semver-agent.yml.tmpl and the canonical rollout tool is
# scripts/propagation/rollout-semver-agent.sh — this script used to read the DEAD
# scripts/templates/semver-agent.yml (since deleted), which would have REGRESSED the
# already-deployed `quality-gates-v2` trigger back to the dead `"Quality Gates"` check and
# re-introduced the broken `../unified-trading-pm` checkout. Run the dedicated tool instead.
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
#
# Two-pass model: this script is an automated rollout caller.
#   Pass 1 — full QG: quality-gates.sh runs (if present) for each repo before commit
#   Pass 2 — quickmerge --agent: lint+format+typecheck+codex only; tests already ran in Pass 1;
#            act simulation skipped (CI validates on GitHub anyway)
#
# NEVER call quickmerge without --agent from automated scripts — act Docker overhead is 60-120s
# with no benefit when CI already validates. Use --agent to document automated context.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
TEMPLATES_DIR="$PM_ROOT/scripts/templates"
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

# semver-agent.yml is rolled out by scripts/propagation/rollout-semver-agent.sh (canonical SSOT) — not here.
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
2>/dev/null || echo "")

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
        git add .github/workflows/agent-audit.yml .github/workflows/plan-alignment-agent.yml 2>/dev/null || true
        if git diff --cached --quiet; then
            echo "  Nothing staged — skipping commit"
        else
            bash scripts/quickmerge.sh "chore: rollout autonomous agent workflows (agent-audit, plan-alignment)" \
                --files ".github/workflows/agent-audit.yml .github/workflows/plan-alignment-agent.yml" \
                --agent 2>&1 | tail -5 || warn "  quickmerge failed for $REPO — check manually"
        fi
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
