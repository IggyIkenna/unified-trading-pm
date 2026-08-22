#!/usr/bin/env bash
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
#
# Cure B (plans/active/issues/cicd_consolidated_remaining_2026_06_24.md): auto-resolve a
# version-line-only staging->main conflict. Rebases staging onto main with the semver-max merge
# driver for pyproject.toml's `version =` line; on a clean (version-line-only) rebase it promotes via
# a fresh v2-gated PR, otherwise it aborts and signals the caller to escalate to the
# conflict-resolution-agent. No force-push, no protection bypass — main's required check still runs.
#
# Usage: auto_resolve_version_promote.sh OWNER REPO STALE_PR_NUMBER
# Stdout LAST line is the verdict the caller greps:
#   AUTO_RESOLVED <new_pr_url>   — version-line-only conflict resolved + clean v2-gated PR armed
#   GENUINE_CONFLICT files=<csv> — a non-version conflict; caller escalates
#   ERROR <reason>               — operational failure; caller escalates (FAIL SAFE)
# Requires: GH_TOKEN (repo+workflow scope), git, gh, python3.
set -uo pipefail

OWNER="${1:?owner}"
REPO="${2:?repo}"
STALE_PR="${3:?stale pr number}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRIVER="${SCRIPT_DIR}/semver_max_merge_driver.py"
[ -f "$DRIVER" ] || { echo "ERROR driver-missing"; exit 0; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

GIT_URL="https://x-access-token:${GH_TOKEN}@github.com/${OWNER}/${REPO}.git"
git clone --quiet --no-tags "$GIT_URL" "$WORK" 2>/dev/null || { echo "ERROR clone-failed"; exit 0; }
cd "$WORK" || { echo "ERROR cd-failed"; exit 0; }

git config user.name "staging-to-main-bot"
git config user.email "staging-to-main-bot@users.noreply.github.com"
git config merge.semvermax.name "semver-max version-line resolver"
git config merge.semvermax.driver "python3 ${DRIVER} %O %A %B"
printf 'pyproject.toml merge=semvermax\n' > .git/info/attributes

git fetch --quiet origin main staging 2>/dev/null || { echo "ERROR fetch-failed"; exit 0; }
git checkout --quiet -B _autoresolve origin/staging 2>/dev/null || { echo "ERROR checkout-failed"; exit 0; }

# Replay staging's bump commits onto main; the driver auto-resolves the version line, empty
# (already-on-main, via the drain) commits drop. A NON-version conflict leaves the rebase paused.
if git rebase --empty=drop origin/main >/dev/null 2>&1; then
  BR="auto-resolve/version-line-$(git rev-parse --short HEAD)"
  git push --quiet origin "_autoresolve:refs/heads/${BR}" 2>/dev/null || { echo "ERROR push-failed"; exit 0; }
  PR_URL="$(gh pr create --repo "${OWNER}/${REPO}" --base main --head "${BR}" \
    --title "chore(release): promote staging->main (version-line auto-resolved)" \
    --body "Cure B: version-line-only conflict auto-resolved (higher semver wins). Supersedes stuck staging->main PR #${STALE_PR}. SSOT: plans/active/issues/cicd_consolidated_remaining_2026_06_24.md" 2>/dev/null)"
  [ -n "$PR_URL" ] || { echo "ERROR pr-create-failed"; exit 0; }
  gh pr merge "$PR_URL" --repo "${OWNER}/${REPO}" --auto --rebase >/dev/null 2>&1 \
    || gh pr merge "$PR_URL" --repo "${OWNER}/${REPO}" --auto --merge >/dev/null 2>&1 || true
  gh pr close "$STALE_PR" --repo "${OWNER}/${REPO}" \
    --comment "Superseded by version-line-auto-resolved promote ${PR_URL} (cure B)." >/dev/null 2>&1 || true
  echo "AUTO_RESOLVED ${PR_URL}"
else
  UNMERGED="$(git diff --name-only --diff-filter=U 2>/dev/null | sort -u | paste -sd',' -)"
  git rebase --abort >/dev/null 2>&1 || true
  echo "GENUINE_CONFLICT files=${UNMERGED:-unknown}"
fi
