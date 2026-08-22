#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Prettier wrapper that auto-stages files prettier modifies.
#
# Why: the upstream mirrors-prettier pre-commit hook runs `prettier --write` on staged
# files, and when prettier reformats anything, pre-commit aborts the commit because
# the working tree no longer matches the staged content. The recovery is manual:
# re-stage + re-commit. This wrapper closes that loop by re-staging modified files
# inside the hook, so the commit completes in one step.
#
# Safety constraints:
# - Only re-stages files prettier just modified (the file list pre-commit hands us).
# - Only re-stages the SUBSET that was already staged (`git diff --cached --name-only`)
#   intersected with the modified files. We never accidentally stage a foreign-dirty
#   file an agent in another slot was holding open per CLAUDE.md "Two teammates ×
#   multiple parallel agents" rule.
# - If prettier itself fails (parse error, syntax error), exits non-zero so the
#   commit aborts. Auto-stage applies only on successful format passes.
#
# Wires from .pre-commit-config.yaml as a local hook:
#   - repo: local
#     hooks:
#       - id: prettier-autostage
#         name: Format with Prettier (auto-stage)
#         entry: bash unified-trading-pm/scripts/hooks/prettier-autostage.sh
#         language: system
#         types_or: [ts, tsx, javascript, jsx, json, markdown, yaml]
#
# Falls back gracefully if prettier isn't installed (e.g. lightweight environment) —
# emits a warning and exits 0 so commit proceeds. CI is the gatekeeper for formatting
# in that case.

set -euo pipefail

# Files this hook was invoked with (from pre-commit framework).
if [ "$#" -eq 0 ]; then
  exit 0
fi

# ── Skip when the branch is BEHIND origin ────────────────────────────────────
# This hook runs BEFORE check-branch-drift.sh in the pre-commit order, so if the
# branch is behind origin the commit will abort on the drift gate — but prettier
# would already have reflowed + re-staged files, leaving that reflow as working-tree
# residue. Accumulated residue makes a slot worktree perpetually dirty, so the
# FF-pull cron skips it and the slot stops syncing (observed 2026-06-02: PM slot,
# 69-file prettier reflow residue from aborted commits). Mirror check-branch-drift.sh's
# condition and no-op early so an about-to-be-blocked commit leaves NO residue.
#
# 2026-08-10 (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md F3): this
# condition must MIRROR check-branch-drift.sh, which is what the paragraph above says it is
# doing — and that gate has since gained an advisory mode, so the mirror had gone stale.
# DRIFT_GATE_ADVISORY=1 means a reconciling wrapper is driving the commit and the drift gate
# will NOT abort it, so the residue scenario this guard protects against cannot occur; skipping
# the format there is pure downside. It was real downside: PM is behind origin almost
# continuously (60-80s commit inter-arrival, measured), so the fast path could essentially
# never self-format, committed unformatted content, the hygiene hook autofixed it, and prek
# then failed the run with "files were modified by this hook" — a closed loop with no exit.
# The residue protection is UNCHANGED for a bare `git commit`, which is the case it was
# written for (2026-06-02, 69-file reflow residue).
if [[ -z "${GITHUB_ACTIONS:-}" && -z "${CI:-}" && "${SKIP_BRANCH_DRIFT:-0}" != "1" &&
  "${DRIFT_GATE_ADVISORY:-0}" != "1" ]]; then
  _PA_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
  if [[ -n "$_PA_BRANCH" && "$_PA_BRANCH" != "HEAD" ]]; then
    git fetch origin "$_PA_BRANCH" --quiet 2>/dev/null || true
    _PA_BEHIND=$(git rev-list "HEAD..origin/$_PA_BRANCH" --count 2>/dev/null || echo 0)
    if [ "${_PA_BEHIND:-0}" -gt 0 ] 2>/dev/null; then
      echo "[prettier-autostage] branch behind origin/$_PA_BRANCH by $_PA_BEHIND — skipping format (the drift gate will block this commit; avoids leaving reflow residue that stops slot FF-sync)."
      exit 0
    fi
  fi
fi

# Locate prettier. Prefer repo-local (node_modules/.bin/prettier), fall back to npx,
# then to a globally-installed prettier on PATH.
#
# MINIMUM VERSION GUARD (2026-07-14): prettier <3.9.5 with this workspace's proseWrap:always
# deterministically CORRUPTS markdown — underscore identifiers rewritten as asterisks
# (data_type -> data*type, LIVE_ -> LIVE*), paragraphs collapsed into blobs. Proven by
# head-to-head repro (3.8.4 mangles, 3.9.5 clean); ~60 docs damaged before detection. SSOT:
# unified-trading-pm/plans/archive/issues/prettier_emphasis_mangling_corpus_corruption_2026_07_14.md
# So: a resolved binary older than $PRETTIER_MIN_VERSION is NEVER used — prefer a pinned npx
# fetch instead, and if npx is unavailable skip the format pass (a skipped format is recoverable;
# corrupted content is not). check_prettier_mangling.sh in the plan-hygiene gate is the backstop.
PRETTIER_MIN_VERSION="3.9.5"

_pa_version_ok() { # $1 = version string; true if >= PRETTIER_MIN_VERSION
  [ "$(printf '%s\n%s\n' "$PRETTIER_MIN_VERSION" "$1" | sort -V | head -1)" = "$PRETTIER_MIN_VERSION" ]
}

PRETTIER=""
if [ -x "./node_modules/.bin/prettier" ] && _pa_version_ok "$(./node_modules/.bin/prettier --version 2>/dev/null || echo 0)"; then
  PRETTIER="./node_modules/.bin/prettier"
elif command -v prettier >/dev/null 2>&1 && _pa_version_ok "$(prettier --version 2>/dev/null || echo 0)"; then
  PRETTIER="prettier"
elif command -v npx >/dev/null 2>&1; then
  # Pinned fetch — npm caches the package, so after the first run this is fast and offline-safe.
  PRETTIER="npx -y prettier@$PRETTIER_MIN_VERSION"
else
  echo "[prettier-autostage] WARN: no prettier >=$PRETTIER_MIN_VERSION available and no npx; skipping format pass (older prettier corrupts markdown — see prettier_emphasis_mangling_corpus_corruption_2026_07_14.md). CI will enforce formatting." >&2
  exit 0
fi

# Snapshot which of the input files were ALREADY in the index before this hook runs.
# Only those are eligible for auto-stage; everything else must remain unstaged so we
# don't accidentally absorb a foreign-agent's dirty working-tree file into our commit.
STAGED_BEFORE="$(git diff --cached --name-only)"

# Run prettier --write on all input files. If prettier fails (e.g. parse error),
# the set -e above will abort the hook with non-zero, so the commit aborts.
# shellcheck disable=SC2086
$PRETTIER --write --log-level warn "$@"

# Prettier's markdown proseWrap printer is non-idempotent for continuation
# paragraphs nested in list items. Repair that whitespace-only corruption after
# each markdown format pass so the staged blob is the same shape the ratchet
# checker validates. The repair is deliberately limited to the hook's named
# markdown inputs and uses the canonical fixer from plan-hygiene.
_PA_WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(git rev-parse --show-toplevel)/.." && pwd)}"
_PA_PROSEWRAP_FIXER="${_PA_WORKSPACE_ROOT}/unified-trading-pm/scripts/plan-hygiene/fix_prosewrap_padding.py"
for f in "$@"; do
  case "$f" in
    *.md)
      if command -v python3 >/dev/null 2>&1 && [ -f "$f" ] && [ -f "$_PA_PROSEWRAP_FIXER" ]; then
        python3 "$_PA_PROSEWRAP_FIXER" "$f" >/dev/null
      fi
      ;;
  esac
done

# Re-stage any input file that prettier modified AND was already in the index.
# `git diff --name-only` shows unstaged changes; intersect with $STAGED_BEFORE.
RESTAGED=0
for f in "$@"; do
  # Was this file already staged before the hook ran?
  if ! echo "$STAGED_BEFORE" | grep -Fxq -- "$f"; then
    continue
  fi
  # Did prettier modify it (creating an unstaged delta)?
  if ! git diff --name-only -- "$f" | grep -Fxq -- "$f"; then
    continue
  fi
  git add -- "$f"
  RESTAGED=$((RESTAGED + 1))
done

if [ "$RESTAGED" -gt 0 ]; then
  echo "[prettier-autostage] Auto-staged $RESTAGED file(s) reformatted by prettier."
fi

exit 0
