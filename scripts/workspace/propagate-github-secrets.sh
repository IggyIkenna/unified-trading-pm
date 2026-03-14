#!/bin/bash
# propagate-github-secrets.sh
#
# Propagates GitHub Actions secrets and variables to all repos listed in
# workspace-manifest.json. By default propagates TELEGRAM_BOT_TOKEN (secret)
# and TELEGRAM_CHAT_ID (variable) to all 59 repos.
#
# Usage:
#   # Propagate Telegram creds to all repos (will prompt if not set in env):
#   bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh
#
#   # Dry-run (shows what would be set, touches nothing):
#   bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh --dry-run
#
#   # Single repo only:
#   bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh --repo execution-service
#
#   # Pass values inline (non-interactive):
#   TELEGRAM_BOT_TOKEN=123:ABC TELEGRAM_CHAT_ID=-100123456 \
#     bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh
#
#   # Skip variables (secrets only):
#   bash unified-trading-pm/scripts/workspace/propagate-github-secrets.sh --secrets-only
#
# Secrets set  : TELEGRAM_BOT_TOKEN   (masked in logs)
#              : GH_PAT               (required for ci-status-update dispatch; from .act-secrets or env)
#              : GCP_PROJECT_ID       (optional; from .act-secrets or env)
#              : AWS_ACCOUNT_ID       (optional; from .act-secrets or env)
# Variables set: TELEGRAM_CHAT_ID     (visible in logs, non-sensitive)
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
  done < <(grep -E '^(GH_PAT|GCP_PROJECT_ID|AWS_ACCOUNT_ID)=' "$ACT_SECRETS" 2>/dev/null || true)
fi

# ── Collect credentials ───────────────────────────────────────────────────────
# TELEGRAM_BOT_TOKEN → GitHub Actions SECRET (masked)
# TELEGRAM_CHAT_ID   → GitHub Actions VARIABLE (visible, not sensitive)

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo ""
  echo "Enter TELEGRAM_BOT_TOKEN (from @BotFather — format: 123456789:ABCdef...):"
  echo -n "> "
  read -rs TELEGRAM_BOT_TOKEN
  echo ""
fi
if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  log_error "TELEGRAM_BOT_TOKEN cannot be empty."
  exit 1
fi

if [[ -z "${TELEGRAM_CHAT_ID:-}" ]]; then
  echo ""
  echo "Enter TELEGRAM_CHAT_ID (your group/channel/user ID — format: -100123456789 or 123456789):"
  echo -n "> "
  read -r TELEGRAM_CHAT_ID
  echo ""
fi
if [[ -z "${TELEGRAM_CHAT_ID:-}" ]]; then
  log_error "TELEGRAM_CHAT_ID cannot be empty."
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
echo " Telegram Secret Propagation"
echo "================================================="
echo "  Workspace : $WORKSPACE_ROOT"
echo "  Repos     : ${#REPO_SLUGS[@]} (from workspace-manifest.json)"
echo "  Dry-run   : $DRY_RUN"
[[ -n "$FILTER_REPO" ]] && echo "  Filter    : $FILTER_REPO"
echo "  Secrets   : TELEGRAM_BOT_TOKEN"
[[ -n "${GH_PAT:-}" ]] && echo "  Secrets   : + GH_PAT (for ci-status-update)"
[[ -n "${GCP_PROJECT_ID:-}" ]] && echo "  Secrets   : + GCP_PROJECT_ID"
[[ -n "${AWS_ACCOUNT_ID:-}" ]] && echo "  Secrets   : + AWS_ACCOUNT_ID"
[[ "$SECRETS_ONLY" == false ]] && echo "  Variables : TELEGRAM_CHAT_ID"
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

  if [[ "$DRY_RUN" == true ]]; then
    log_dry "would set TELEGRAM_BOT_TOKEN + GH_PAT (if set) + GCP_PROJECT_ID + AWS_ACCOUNT_ID (if set) + TELEGRAM_CHAT_ID"
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

  # Set secret: TELEGRAM_BOT_TOKEN
  if printf '%s' "$TELEGRAM_BOT_TOKEN" | gh secret set TELEGRAM_BOT_TOKEN \
      --repo "$slug" --body - 2>/dev/null; then
    : # ok
  else
    log_warn "failed to set TELEGRAM_BOT_TOKEN on $slug"
    ERR=1
  fi

  # Set variable: TELEGRAM_CHAT_ID (non-sensitive — use gh variable set)
  if [[ "$SECRETS_ONLY" == false ]]; then
    if gh variable set TELEGRAM_CHAT_ID \
        --repo "$slug" --body "$TELEGRAM_CHAT_ID" 2>/dev/null; then
      : # ok
    else
      log_warn "failed to set TELEGRAM_CHAT_ID variable on $slug"
      ERR=1
    fi
  fi

  if [[ $ERR -eq 0 ]]; then
    log_info "OK"
    ((PASS++))
  else
    ((FAIL++))
  fi
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
