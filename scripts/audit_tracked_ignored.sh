#!/usr/bin/env bash
# =============================================================================
# audit_tracked_ignored.sh
# Find (and optionally remove from index) files tracked by git that are matched
# by the repo's own .gitignore rules.
#
# Usage:
#   bash scripts/audit_tracked_ignored.sh              # dry-run: report only
#   bash scripts/audit_tracked_ignored.sh --apply      # remove from git index
#                                                       # (files stay on disk)
#
# Output:
#   Always prints per-repo summary to stdout.
#   Writes full report to scripts/audit_tracked_ignored_report.txt
#
# NOTE: Uses `git check-ignore --no-index` which evaluates every tracked file
# against .gitignore rules regardless of tracking status. This is the correct
# approach — `git ls-files --ignored` silently skips already-tracked files.
# =============================================================================

set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_FILE="$SCRIPT_DIR/audit_tracked_ignored_report.txt"

APPLY=false
if [ "${1:-}" = "--apply" ]; then
  APPLY=true
fi

# Colours
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# Counters
total_repos=0
repos_with_hits=0
total_files=0

# Start report
{
  echo "audit_tracked_ignored.sh — $(date '+%Y-%m-%d %H:%M:%S')"
  echo "Mode: $([ "$APPLY" = true ] && echo "APPLY (removing from index)" || echo "DRY-RUN (report only)")"
  echo "Workspace: $WORKSPACE_ROOT"
  echo "============================================================"
} > "$REPORT_FILE"

echo ""
echo -e "${BOLD}Scanning all git repos in workspace...${RESET}"
echo -e "Mode: $([ "$APPLY" = true ] && echo -e "${RED}APPLY — will run git rm --cached${RESET}" || echo -e "${CYAN}DRY-RUN — report only${RESET}")"
echo ""

for repo_path in "$WORKSPACE_ROOT"/*/; do
  repo_name="$(basename "$repo_path")"

  if [ ! -d "$repo_path/.git" ]; then
    continue
  fi

  total_repos=$((total_repos + 1))

  # Correct detection: pipe every tracked file through check-ignore --no-index.
  # --no-index is required — without it git skips files that are already tracked.
  hits=$(
    git -C "$repo_path" ls-files 2>/dev/null \
      | git -C "$repo_path" check-ignore --stdin --no-index 2>/dev/null \
      || true
  )

  if [ -z "$hits" ]; then
    echo "CLEAN  $repo_name" >> "$REPORT_FILE"
    echo -e "  ${GREEN}✓${RESET} $repo_name"
    continue
  fi

  file_count=$(echo "$hits" | wc -l | tr -d ' ')
  total_files=$((total_files + file_count))
  repos_with_hits=$((repos_with_hits + 1))

  # Separate .env files (critical — may contain credentials)
  env_files=$(echo "$hits" | grep -E "(^|/)\.env$" || true)
  other_files=$(echo "$hits" | grep -vE "(^|/)\.env$" || true)

  # Print header
  echo ""
  echo -e "  ${YELLOW}!${RESET} ${BOLD}$repo_name${RESET} — ${RED}$file_count tracked file(s) should be ignored${RESET}"

  # Flag .env files with extra severity
  if [ -n "$env_files" ]; then
    echo -e "    ${RED}${BOLD}⚠ CRITICAL — .env file(s) committed (may contain credentials):${RESET}"
    echo "$env_files" | while IFS= read -r f; do
      echo -e "      ${RED}$f${RESET}"
    done
  fi

  # Print other files
  if [ -n "$other_files" ]; then
    other_count=$(echo "$other_files" | wc -l | tr -d ' ')
    echo -e "    ${YELLOW}Other ($other_count):${RESET}"
    echo "$other_files" | head -15 | sed 's/^/      /'
    if [ "$other_count" -gt 15 ]; then
      echo "      ... and $((other_count - 15)) more (see report)"
    fi
  fi

  # Write full list to report
  {
    echo ""
    echo "------------------------------------------------------------"
    echo "REPO: $repo_name  ($file_count tracked-but-ignored files)"
    echo "------------------------------------------------------------"
    if [ -n "$env_files" ]; then
      echo "  [CRITICAL - .env]"
      echo "$env_files" | sed 's/^/    /'
    fi
    if [ -n "$other_files" ]; then
      echo "  [other]"
      echo "$other_files" | sed 's/^/    /'
    fi
  } >> "$REPORT_FILE"

  if [ "$APPLY" = true ]; then
    echo -e "    ${RED}→ Removing $file_count file(s) from git index (keeping on disk)...${RESET}"
    echo "$hits" | tr '\n' '\0' | xargs -0 git -C "$repo_path" rm -r --cached --quiet --
    echo "    → Done."
    echo "  ACTION: git rm --cached applied ($file_count files)" >> "$REPORT_FILE"
  else
    echo "    → Run with --apply to remove from index."
    echo "  ACTION: none (dry-run)" >> "$REPORT_FILE"
  fi
done

echo ""

# Summary
summary=$(cat <<EOF

============================================================
SUMMARY
  Repos scanned:          $total_repos
  Repos with hits:        $repos_with_hits
  Total tracked+ignored:  $total_files
  Mode: $([ "$APPLY" = true ] && echo "APPLIED" || echo "DRY-RUN — run with --apply to remove from index")
============================================================
EOF
)

echo "$summary" | tee -a "$REPORT_FILE"
echo ""
echo -e "Full report: ${CYAN}$REPORT_FILE${RESET}"

if [ "$APPLY" = false ] && [ "$repos_with_hits" -gt 0 ]; then
  echo ""
  echo -e "${YELLOW}Re-run with --apply to remove from git index.${RESET}"
  echo -e "Files will ${BOLD}stay on disk${RESET} — only removed from git tracking."
fi
