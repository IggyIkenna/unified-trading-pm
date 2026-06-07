#!/bin/bash
# propagate-github-secrets.sh
#
# Propagates GitHub Actions secrets to all repos listed in
# workspace-manifest.json. Propagates SLACK_WEBHOOK_URL + SLACK_CI_WEBHOOK_URL
# (secrets) to all repos so CI alerts route to the right Slack channels:
#   SLACK_WEBHOOK_URL    → #uts-live-alerts   (general fleet alerts)
#   SLACK_CI_WEBHOOK_URL → #ci-failures       (CI failure alerts)
# EXCEPTION (intentional — codified 2026-06-07): agent-orchestrator posts its
# SLACK_WEBHOOK_URL to its OWN channel #agent-orchestrator-alerts (value =
# AGENT_ORCHESTRATOR_SLACK_WEBHOOK), NOT #uts-live-alerts. That is why we keep
# separate channels — do NOT "fix" it to the fleet value.
#
# Usage:
#   # Propagate Slack webhook to all repos (will prompt if not set in env):
#   bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh
#
#   # Dry-run (shows what would be set, touches nothing):
#   bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh --dry-run
#
#   # Single repo only:
#   bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh --repo execution-service
#
#   # Pass values inline (non-interactive):
#   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/... \
#     bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh
#
#   # Secrets only (no variables to set for Slack):
#   bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh --secrets-only
#
# Secrets set  : SLACK_WEBHOOK_URL    (masked — #uts-live-alerts; agent-orchestrator → #agent-orchestrator-alerts)
#              : SLACK_CI_WEBHOOK_URL (masked — #ci-failures, all repos)
#              : GH_PAT               (required for ci-status-update dispatch; from .act-secrets or env)
#              : GCP_PROJECT_ID       (optional; from .act-secrets or env)
#              : AWS_ACCOUNT_ID       (optional; from .act-secrets or env)
#
# GCP_PROJECT_ID / AWS_ACCOUNT_ID: Read from WORKSPACE_ROOT/.act-secrets or env.
# If unset, skipped (CI falls back to test-project / empty).
#
# Prerequisites:
#   gh CLI authenticated: gh auth login
#   jq installed: brew install jq

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info()    { echo -e "${GREEN}[INFO]${NC}  $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
log_dry()     { echo -e "${BLUE}[DRY]${NC}   $1"; }
log_skip()    { echo -e "${YELLOW}[SKIP]${NC}  $1"; }

# ── Resolve workspace root ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# scripts/workspace/ → scripts/ → unified-trading-pm/ → workspace-root
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
MANIFEST="${WORKSPACE_ROOT}/unified-trading-pm/workspace-manifest.json"

# ── Parse flags ───────────────────────────────────────────────────────────────
DRY_RUN=false
FILTER_REPO=""
SECRETS_ONLY=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)       DRY_RUN=true; shift ;;
    --secrets-only)  SECRETS_ONLY=true; shift ;;
    --repo)
      FILTER_REPO="$2"
      shift 2
      ;;
    --help | -h)
      sed -n '2,30p' "$0"
      exit 0
      ;;
    *)
      log_error "Unknown flag: $1  (use --help)"
      exit 1
      ;;
  esac
done

# ── Prereq checks ─────────────────────────────────────────────────────────────
if ! command -v gh &>/dev/null; then
  log_error "gh CLI not found. Install: brew install gh && gh auth login"
  exit 1
fi
if ! command -v jq &>/dev/null; then
  log_error "jq not found. Install: brew install jq"
  exit 1
fi
if ! gh auth status &>/dev/null; then
  log_error "gh not authenticated. Run: gh auth login"
  exit 1
fi
if [[ ! -f "$MANIFEST" ]]; then
  log_error "workspace-manifest.json not found at: $MANIFEST"
  exit 1
fi

# ── Load optional values from .act-secrets ─────────────────────────────────────
ACT_SECRETS="${WORKSPACE_ROOT}/.act-secrets"
if [[ -f "$ACT_SECRETS" ]]; then
  while IFS= read -r line; do
    [[ "$line" =~ ^GH_PAT= ]] && [[ -z "${GH_PAT:-}" ]] && export GH_PAT="${line#GH_PAT=}"
    [[ "$line" =~ ^GCP_PROJECT_ID= ]] && [[ -z "${GCP_PROJECT_ID:-}" ]] && export GCP_PROJECT_ID="${line#GCP_PROJECT_ID=}"
    [[ "$line" =~ ^AWS_ACCOUNT_ID= ]] && [[ -z "${AWS_ACCOUNT_ID:-}" ]] && export AWS_ACCOUNT_ID="${line#AWS_ACCOUNT_ID=}"
    [[ "$line" =~ ^SLACK_WEBHOOK_URL= ]] && [[ -z "${SLACK_WEBHOOK_URL:-}" ]] && export SLACK_WEBHOOK_URL="${line#SLACK_WEBHOOK_URL=}"
    [[ "$line" =~ ^SLACK_CI_WEBHOOK_URL= ]] && [[ -z "${SLACK_CI_WEBHOOK_URL:-}" ]] && export SLACK_CI_WEBHOOK_URL="${line#SLACK_CI_WEBHOOK_URL=}"
    [[ "$line" =~ ^AGENT_ORCHESTRATOR_SLACK_WEBHOOK= ]] && [[ -z "${AGENT_ORCHESTRATOR_SLACK_WEBHOOK:-}" ]] && export AGENT_ORCHESTRATOR_SLACK_WEBHOOK="${line#AGENT_ORCHESTRATOR_SLACK_WEBHOOK=}"
  done < <(grep -E '^(GH_PAT|GCP_PROJECT_ID|AWS_ACCOUNT_ID|SLACK_WEBHOOK_URL|SLACK_CI_WEBHOOK_URL|AGENT_ORCHESTRATOR_SLACK_WEBHOOK)=' "$ACT_SECRETS" 2>/dev/null || true)
fi

# ── Collect credentials ───────────────────────────────────────────────────────
# SLACK_WEBHOOK_URL → GitHub Actions SECRET (masked)

if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
  echo ""
  echo "Enter SLACK_WEBHOOK_URL (Slack incoming webhook — format: https://hooks.slack.com/services/...):"
  echo -n "> "
  read -rs SLACK_WEBHOOK_URL
  echo ""
fi
if [[ -z "${SLACK_WEBHOOK_URL:-}" ]]; then
  log_error "SLACK_WEBHOOK_URL cannot be empty."
  exit 1
fi

# SLACK_CI_WEBHOOK_URL → #ci-failures (all repos)
if [[ -z "${SLACK_CI_WEBHOOK_URL:-}" ]]; then
  echo ""
  echo "Enter SLACK_CI_WEBHOOK_URL (#ci-failures incoming webhook — https://hooks.slack.com/services/...):"
  echo -n "> "
  read -rs SLACK_CI_WEBHOOK_URL
  echo ""
fi
if [[ -z "${SLACK_CI_WEBHOOK_URL:-}" ]]; then
  log_error "SLACK_CI_WEBHOOK_URL cannot be empty."
  exit 1
fi

# ── Build repo list from manifest ─────────────────────────────────────────────
# manifest.repositories is a dict keyed by repo name; each has github_url
# Use process substitution + while (bash 3.2 compatible — no mapfile)
REPO_SLUGS=()
while IFS= read -r slug; do
  [[ -n "$slug" ]] && REPO_SLUGS+=("$slug")
done < <(
  jq -r '.repositories | to_entries[] | .value.github_url | ltrimstr("https://github.com/")' \
    "$MANIFEST"
)

if [[ ${#REPO_SLUGS[@]} -eq 0 ]]; then
  log_error "No repos found in manifest at $MANIFEST"
  exit 1
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "================================================="
echo " Slack Secret Propagation"
echo "================================================="
echo "  Workspace : $WORKSPACE_ROOT"
echo "  Repos     : ${#REPO_SLUGS[@]} (from workspace-manifest.json)"
echo "  Dry-run   : $DRY_RUN"
[[ -n "$FILTER_REPO" ]] && echo "  Filter    : $FILTER_REPO"
echo "  Secrets   : SLACK_WEBHOOK_URL (#uts-live-alerts; agent-orchestrator → #agent-orchestrator-alerts)"
echo "  Secrets   : SLACK_CI_WEBHOOK_URL (#ci-failures)"
[[ -n "${AGENT_ORCHESTRATOR_SLACK_WEBHOOK:-}" ]] && echo "  Override  : agent-orchestrator SLACK_WEBHOOK_URL → its own channel"
[[ -n "${GH_PAT:-}" ]] && echo "  Secrets   : + GH_PAT (for ci-status-update)"
[[ -n "${GCP_PROJECT_ID:-}" ]] && echo "  Secrets   : + GCP_PROJECT_ID"
[[ -n "${AWS_ACCOUNT_ID:-}" ]] && echo "  Secrets   : + AWS_ACCOUNT_ID"
echo "================================================="
echo ""

# ── Propagate ─────────────────────────────────────────────────────────────────
PASS=0
FAIL=0
SKIP=0

for slug in "${REPO_SLUGS[@]}"; do
  repo_name="${slug##*/}"

  # Apply --repo filter
  if [[ -n "$FILTER_REPO" && "$repo_name" != "$FILTER_REPO" ]]; then
    continue
  fi

  echo -n "  [$slug] "

  # Per-repo SLACK_WEBHOOK_URL: agent-orchestrator posts to its OWN channel
  # (#agent-orchestrator-alerts) — intentional exception (see header).
  case "$repo_name" in
    agent-orchestrator) THIS_WEBHOOK="${AGENT_ORCHESTRATOR_SLACK_WEBHOOK:-$SLACK_WEBHOOK_URL}"; WH_CHAN="#agent-orchestrator-alerts" ;;
    *)                  THIS_WEBHOOK="$SLACK_WEBHOOK_URL"; WH_CHAN="#uts-live-alerts" ;;
  esac

  if [[ "$DRY_RUN" == true ]]; then
    log_dry "would set SLACK_WEBHOOK_URL ($WH_CHAN) + SLACK_CI_WEBHOOK_URL (#ci-failures)"
    ((PASS++))
    continue
  fi

  # Check repo exists on GitHub (avoid obscure gh error messages)
  if ! gh repo view "$slug" --json name -q '.name' &>/dev/null; then
    log_warn "repo not found on GitHub — skipping: $slug"
    ((SKIP++))
    continue
  fi

  ERR=0

  # Set secret: SLACK_WEBHOOK_URL (per-repo channel)
  if printf '%s' "$THIS_WEBHOOK" | gh secret set SLACK_WEBHOOK_URL \
      --repo "$slug" --body - 2>/dev/null; then
    : # ok
  else
    log_warn "failed to set SLACK_WEBHOOK_URL on $slug"
    ERR=1
  fi

  # Set secret: SLACK_CI_WEBHOOK_URL (#ci-failures, all repos)
  if printf '%s' "$SLACK_CI_WEBHOOK_URL" | gh secret set SLACK_CI_WEBHOOK_URL \
      --repo "$slug" --body - 2>/dev/null; then
    : # ok
  else
    log_warn "failed to set SLACK_CI_WEBHOOK_URL on $slug"
    ERR=1
  fi

  if [[ $ERR -eq 0 ]]; then
    log_info "OK ($WH_CHAN + #ci-failures)"
    ((PASS++))
  else
    ((FAIL++))
  fi

  # Space out calls — GitHub secondary rate-limits content-mutating bursts.
  # Without this, a full-fleet run (≈50 secret-sets) silently drops the 2nd
  # secret on later repos (observed 2026-06-07). Cheap insurance.
  sleep 0.4
done

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "================================================="
if [[ "$DRY_RUN" == true ]]; then
  echo " DRY-RUN complete — nothing was changed"
else
  echo " Done: ${PASS} OK  |  ${FAIL} FAILED  |  ${SKIP} SKIPPED"
fi
echo "================================================="

if [[ $FAIL -gt 0 ]]; then
  log_error "$FAIL repos failed. Re-run with --repo <name> to retry individually."
  exit 1
fi
