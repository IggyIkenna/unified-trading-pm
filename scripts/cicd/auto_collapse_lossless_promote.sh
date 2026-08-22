#!/usr/bin/env bash
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
#
# Bug 2 (cicd_consolidated_remaining_2026_06_24.md § WS-B): auto-collapse a CONTENT-LOSSLESS
# staging->main divergence that Cure-B's rebase CANNOT resolve — a `dirty` PR whose NET tree delta is
# <= the bumped `version =` line, but whose divergent squash-merge history defeats a commit-by-commit
# rebase (stale merge-base => spurious overlapping-hunk conflicts beyond the version line).
#
# Unlike Cure-B (which REBASES staging's commits onto main and so can conflict per-commit), this takes
# staging's FINAL TREE as ONE clean commit on top of main — which cannot conflict, because it is just a
# content overwrite to the (lossless) target. It then promotes through the SAME v2-gated protected PR
# path as every promotion. It NEVER force-pushes a protected branch and needs NO protection bypass:
# the only push is to an UNPROTECTED `collapse/...` feature branch; `main` is updated by a normal
# auto-merge once its required check passes.
#
# Usage: auto_collapse_lossless_promote.sh OWNER REPO STALE_PR_NUMBER
# Stdout LAST line is the verdict the caller greps:
#   COLLAPSED <new_pr_url>      — lossless; clean v2-gated collapse PR armed, stale PR closed
#   NOT_LOSSLESS files=<csv>    — >1 file changed, a non-version pyproject hunk, OR a version DOWNGRADE;
#                                 caller escalates UNCHANGED (fail safe — never collapse a real diff)
#   ERROR <reason>              — operational failure; caller escalates (FAIL SAFE)
# Requires: GH_TOKEN (repo+workflow scope), git, gh, python3.
set -uo pipefail

OWNER="${1:?owner}"
REPO="${2:?repo}"
STALE_PR="${3:?stale pr number}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

GIT_URL="https://x-access-token:${GH_TOKEN}@github.com/${OWNER}/${REPO}.git"
git clone --quiet --no-tags "$GIT_URL" "$WORK" 2>/dev/null || { echo "ERROR clone-failed"; exit 0; }
cd "$WORK" || { echo "ERROR cd-failed"; exit 0; }

git config user.name "staging-to-main-bot"
git config user.email "staging-to-main-bot@users.noreply.github.com"
git fetch --quiet origin main staging 2>/dev/null || { echo "ERROR fetch-failed"; exit 0; }

# ── LOSSLESS GUARD ─────────────────────────────────────────────────────────────
# Compare the TREES directly (not the squash-inflated compare API). The ONLY file that may differ is
# pyproject.toml, and within it the ONLY changed lines may be `version = `. ANY other delta => NOT
# lossless => bail (caller escalates unchanged). This is the safety property: main's content provably
# changes by ONLY the version line.
CHANGED="$(git diff --name-only origin/main origin/staging 2>/dev/null | sort -u)"
if [ "$CHANGED" != "pyproject.toml" ]; then
  echo "NOT_LOSSLESS files=$(echo "$CHANGED" | paste -sd',' - 2>/dev/null)"
  exit 0
fi
NONVER="$(git diff origin/main origin/staging -- pyproject.toml 2>/dev/null \
  | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' \
  | grep -vE '^[+-][[:space:]]*version[[:space:]]*=' | head -1)"
if [ -n "$NONVER" ]; then
  echo "NOT_LOSSLESS files=pyproject.toml:non-version-line"
  exit 0
fi

# ── DOWNGRADE GUARD (version = max(main, staging)) ──────────────────────────────
# Promotion direction is staging->main, so staging's version is normally the target. Refuse to collapse
# if main's version is HIGHER (would be a downgrade) — fail safe, escalate instead.
MAIN_VER="$(git show origin/main:pyproject.toml 2>/dev/null | sed -nE 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' | head -1)"
STAG_VER="$(git show origin/staging:pyproject.toml 2>/dev/null | sed -nE 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' | head -1)"
if [ -z "$STAG_VER" ] || [ -z "$MAIN_VER" ]; then echo "ERROR version-parse-failed"; exit 0; fi
HIGHER="$(python3 -c "
import sys
def t(v):
    try: return tuple(int(x) for x in v.split('.')[:3])
    except Exception: return None
a, b = t('$MAIN_VER'), t('$STAG_VER')
print('main' if (a is not None and b is not None and a > b) else 'ok')
" 2>/dev/null)"
if [ "$HIGHER" = "main" ]; then
  echo "NOT_LOSSLESS files=pyproject.toml:would-downgrade(main=$MAIN_VER>staging=$STAG_VER)"
  exit 0
fi

# ── BUILD CLEAN RESOLUTION BRANCH (descends from main => PR cannot conflict) ─────
git checkout --quiet -B _collapse origin/main 2>/dev/null || { echo "ERROR checkout-failed"; exit 0; }
# Take staging's ENTIRE tree (lossless guard already proved only the version line moves).
git checkout --quiet origin/staging -- . 2>/dev/null || { echo "ERROR checkout-tree-failed"; exit 0; }
git add -A 2>/dev/null || true
if git diff --cached --quiet 2>/dev/null; then echo "ERROR no-delta-after-checkout"; exit 0; fi
git commit --quiet -m "chore(release): promote staging->main (content-lossless collapse) [skip-cascade]" 2>/dev/null \
  || { echo "ERROR commit-failed"; exit 0; }
BR="collapse/staging-to-main-$(git rev-parse --short HEAD)"
git push --quiet origin "_collapse:refs/heads/${BR}" 2>/dev/null || { echo "ERROR push-failed"; exit 0; }

PR_URL="$(gh pr create --repo "${OWNER}/${REPO}" --base main --head "${BR}" \
  --title "chore(release): promote staging->main (content-lossless collapse)" \
  --body "Bug-2 auto-collapse: the staging->main net tree delta was <= the bumped \`version\` line, but the divergent squash-history defeated Cure-B's rebase. Rebuilt as ONE clean commit on top of main (staging tree; staging version ${STAG_VER} >= main ${MAIN_VER}). NO protected-branch force-push; v2 still gates the merge. Supersedes stuck staging->main PR #${STALE_PR}. SSOT: plans/active/cicd_consolidated_remaining_2026_06_24.md § WS-B." 2>/dev/null)"
[ -n "$PR_URL" ] || { echo "ERROR pr-create-failed"; exit 0; }
gh pr merge "$PR_URL" --repo "${OWNER}/${REPO}" --auto --squash >/dev/null 2>&1 \
  || gh pr merge "$PR_URL" --repo "${OWNER}/${REPO}" --auto --merge >/dev/null 2>&1 || true
gh pr close "$STALE_PR" --repo "${OWNER}/${REPO}" \
  --comment "Superseded by content-lossless collapse promote ${PR_URL} (bug-2 auto-collapse)." >/dev/null 2>&1 || true
echo "COLLAPSED ${PR_URL}"
