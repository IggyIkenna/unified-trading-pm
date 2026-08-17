#!/usr/bin/env bash
# Epic: ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for the LDR<->main promote/backmerge safety nets:
#   (1) "silent-revert-loss" (plans/active/issues/ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29.md)
#   (2) "silent-deletion guard" for collateral frontmatter-key / `- [ ]` todo-line loss
#       (plans/active/issues/main_ldr_backmerge_silently_reapplies_collateral_frontmatter_deletion_2026_08_17.md)
#
# Bug 1 (found 2026-07-29): a squash-promote commit's real git parent is main's PREVIOUS
# tip, never the LDR SHA it actually squashed. If a revert lands on LDR after that LDR
# SHA was read but before/around the squash landing on main, git's own computed
# merge-base(LDR-tip, squash-commit) resolves to a STALE ancestor that predates BOTH the
# original fix and its revert -- so main-backmerge-to-ldr's 3-way merge reads the revert
# as "unchanged since base" and silently re-takes main's stale (pre-revert) content. No
# conflict, no marker: `git log` shows the revert; the file content does not reflect it.
# Confirmed live on instruments-service (fix 2941646c, revert 8df0e94e, stale-squash
# 4fc4900a, backmerge ed04b405 -- exact SHAs in the issue doc).
#
# Fix 1 (2026-07-29): `ldr-to-main-promote-fleet.yml` stamps a `Promoted-From-LDR: <sha>`
# trailer on every squash-promote commit body; `main-backmerge-to-ldr.yml` reads that
# trailer and forces the 3-way merge onto that EXPLICIT base via
# `git merge-tree --write-tree --merge-base=<sha>` instead of git's own (possibly-stale)
# computed one. A `check_no_silent_revert_loss()` safety net additionally catches the
# narrower "did this merge fully discard LDR's own last commit's effect" signature,
# independent of the trailer (defense-in-depth for a genuine main-only revert case too).
#
# Bug 2 / Fix 2 (found + fixed 2026-08-17): a DIFFERENT, more general shape of the same
# "clean auto-merge silently applies a deletion" family -- a frontmatter key or `- [ ]`
# todo line dropped from `main` as pure collateral of some UNRELATED conflict resolution
# round-trips back onto LDR whenever LDR itself hasn't touched that file since the merge
# base (ours-unchanged/theirs-changed is git's own definition of "no conflict, take
# theirs"). `check_no_silent_frontmatter_or_todo_loss()` catches this independent of
# Bug 1's trailer/squash mechanics -- confirmed live on
# plans/active/issues/manifest_hygiene_red_all_2026_08_17.md's `author:` key.
#
# Source location (updated 2026-08-17, main_ldr_backmerge_silently_reapplies_collateral_
# frontmatter_deletion_2026_08_17.md): the fleet_workflow_template_dedup_to_unified_
# trading_ci_2026_08_06 migration moved this workflow's job body OUT of
# unified-trading-pm/scripts/workflow-templates/main-backmerge-to-ldr.yml (deleted) and
# into unified-trading-ci/.github/workflows/main-backmerge-to-ldr.yml as a `workflow_call`
# reusable workflow -- this test's BACKMERGE_WF path was left pointing at the deleted PM
# location and had been silently FATAL-ing since (same failure class already caught once
# for test-ldr-promote-provenance-rearm-gate.sh's PROMOTE_SCRIPT path, 2026-08-02). Fixed
# to resolve the sibling `unified-trading-ci` checkout via the standard multi-repo slot
# layout (`.tabs/<slot>/<repo>` -- every repo is a sibling directory, see
# codex/05-infrastructure/per-tab-worktrees.md) -- and, because a single-repo CI checkout
# of `unified-trading-pm` alone will never have that sibling present, this SKIPS (not
# FATAL) the BACKMERGE_WF-dependent checks when the sibling isn't found, so this stays a
# genuine local/multi-repo regression test rather than crashing PM's own quality gate for
# content that lives in a different repo. PROMOTE_WF (Structural anchor #1) is unaffected
# -- `ldr-to-main-promote-fleet.yml` still lives in PM itself.
#
# Like test-ldr-promote-provenance-rearm-gate.sh, the functional sections below:
#   (a) structurally assert the fix code is actually present and wired into the
#       promote/backmerge workflow files (not just described in a comment);
#   (b) functionally reproduce the CONFIRMED bug shapes with REAL git commands, and prove
#       the EXTRACTED, REAL guard functions (not re-implementations) correctly flag the
#       buggy result and do NOT flag the fixed / unrelated / no-op result.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-backmerge-silent-revert-loss-guard.sh
set -uo pipefail

PASS=0
FAIL=0
SKIP=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }
skip() { echo "SKIP: $*"; SKIP=$((SKIP + 1)); }

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PROMOTE_WF="$REPO_ROOT/.github/workflows/ldr-to-main-promote-fleet.yml"
[ -f "$PROMOTE_WF" ] || { echo "FATAL: ldr-to-main-promote-fleet.yml not found at $PROMOTE_WF"; exit 2; }
# The trailer-stamp sites themselves live in the standalone script, not the workflow file
# -- the 2026-08-01 "extract giant embedded script from ldr-to-main-promote-fleet.yml"
# refactor (unified-trading-pm@468e9413e) moved process_repo()/provenance_check_ok()/the
# Promoted-From-LDR arm sites OUT of the .yml's embedded `run:` block and into
# scripts/cicd/ldr_to_main_fleet_promote.sh (same relocation test-ldr-promote-provenance-
# rearm-gate.sh already had to correct for its own PROMOTE_SCRIPT path). This test still
# grepped the now-relocated-away .yml file for the trailer and had been silently FAILING
# structural anchor #1 ever since -- found while touching this exact test file for the
# 2026-08-17 silent-deletion-guard addition below.
PROMOTE_SCRIPT="$REPO_ROOT/scripts/cicd/ldr_to_main_fleet_promote.sh"
[ -f "$PROMOTE_SCRIPT" ] || { echo "FATAL: ldr_to_main_fleet_promote.sh not found at $PROMOTE_SCRIPT"; exit 2; }

# Sibling multi-repo slot layout: every repo checkout is a sibling directory of
# unified-trading-pm's own repo root (.tabs/<slot>/<repo>). A single-repo CI checkout of
# PM alone will not have this sibling -- that is expected, not a failure.
CI_SIBLING_ROOT="$(cd "$REPO_ROOT/.." 2>/dev/null && pwd)/unified-trading-ci"
BACKMERGE_WF="$CI_SIBLING_ROOT/.github/workflows/main-backmerge-to-ldr.yml"

# ── Structural anchor #1: every squash-merge arm site stamps the trailer ─────────────
TRAILER_STAMP_COUNT=$(grep -c 'Promoted-From-LDR: %s' "$PROMOTE_SCRIPT" || true)
if [ "${TRAILER_STAMP_COUNT:-0}" -ge 3 ]; then
  pass "structural: ldr_to_main_fleet_promote.sh stamps Promoted-From-LDR on all 3 squash-merge arm sites (found ${TRAILER_STAMP_COUNT})"
else
  fail "structural: expected >=3 Promoted-From-LDR trailer stamp sites in ldr_to_main_fleet_promote.sh, found ${TRAILER_STAMP_COUNT:-0} -- a squash arm/re-arm path may be unstamped"
fi

if [ ! -f "$BACKMERGE_WF" ]; then
  skip "sibling unified-trading-ci checkout not found at $CI_SIBLING_ROOT -- BACKMERGE_WF-dependent checks (structural #2/#3, all functional cases) require the multi-repo slot layout; this is expected in a single-repo PM-only CI checkout"
else

# ── Structural anchor #2: the backmerge reads the revert-loss trailer + explicit base ──
case "$(cat "$BACKMERGE_WF")" in
  *"Promoted-From-LDR"*"merge-tree --write-tree --merge-base="*"check_no_silent_revert_loss"*)
    pass "structural: main-backmerge-to-ldr.yml carries the trailer-read + explicit-merge-base + revert-loss safety-net contract" ;;
  *)
    fail "structural: main-backmerge-to-ldr.yml missing an expected fix-1 element (trailer read / explicit merge-base / revert-loss safety net)" ;;
esac

# ── Structural anchor #3: the collateral frontmatter/todo silent-deletion guard is wired in ──
case "$(cat "$BACKMERGE_WF")" in
  *"check_no_silent_frontmatter_or_todo_loss"*"_frontmatter_block"*)
    pass "structural: main-backmerge-to-ldr.yml carries the check_no_silent_frontmatter_or_todo_loss guard" ;;
  *)
    fail "structural: main-backmerge-to-ldr.yml missing the check_no_silent_frontmatter_or_todo_loss guard" ;;
esac
CALL_SITE_COUNT=$(grep -c 'check_no_silent_frontmatter_or_todo_loss "' "$BACKMERGE_WF" || true)
if [ "${CALL_SITE_COUNT:-0}" -ge 2 ]; then
  pass "structural: check_no_silent_frontmatter_or_todo_loss is called from both the explicit-base and default merge paths (found ${CALL_SITE_COUNT} call sites)"
else
  fail "structural: expected >=2 check_no_silent_frontmatter_or_todo_loss call sites (explicit-base + default path), found ${CALL_SITE_COUNT:-0}"
fi

# ── Extract the REAL check_no_silent_revert_loss() function body ─────────────────────
REVERT_FUNC=$(awk '
  /^[[:space:]]+check_no_silent_revert_loss\(\) \{$/ { c = 1 }
  c { print }
  c && $0 ~ /^[[:space:]]+\}$/ { exit }
' "$BACKMERGE_WF")
[ -n "$REVERT_FUNC" ] || { echo "FATAL: could not extract check_no_silent_revert_loss() from $BACKMERGE_WF"; exit 2; }

# ── Extract the REAL _frontmatter_block() + check_no_silent_frontmatter_or_todo_loss() ──
FM_FUNCS=$(awk '
  /^[[:space:]]+_frontmatter_block\(\) \{$/ { c = 1 }
  /^[[:space:]]+check_no_silent_frontmatter_or_todo_loss\(\) \{$/ { c = 1 }
  c { print }
  c && $0 ~ /^[[:space:]]+\}$/ { c = 0; print "" }
' "$BACKMERGE_WF")
[ -n "$FM_FUNCS" ] || { echo "FATAL: could not extract the frontmatter/todo guard functions from $BACKMERGE_WF"; exit 2; }

# ── Functional harness: reproduce the CONFIRMED instruments-service graph shape ───────
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
GIT="git -c user.email=t@t.local -c user.name=test -c commit.gpgsign=false -c init.defaultBranch=main"

REPO_DIR="$WORK/repo"
mkdir -p "$REPO_DIR"
(
  cd "$REPO_DIR"
  $GIT init -q
  printf 'base\n' > Dockerfile
  $GIT add Dockerfile && $GIT commit -qm "base"
  $GIT branch ldr

  # LDR: fix commit adds a block (mirrors instruments-service@2941646c).
  $GIT checkout -q ldr
  printf 'base\nENV UV_EXTRA_INDEX_URL=added\n' > Dockerfile
  $GIT add Dockerfile && $GIT commit -qm "fix(uv): add extra index url"

  # LDR: revert commit removes it (mirrors instruments-service@8df0e94e).
  printf 'base\n' > Dockerfile
  $GIT add Dockerfile && $GIT commit -qm "revert: remove extra index url"

  # main: simulated squash-promote whose PARENT is pre-fix (base) but whose CONTENT
  # includes the fix's block, carrying the Promoted-From-LDR trailer to the FIX sha
  # (mirrors instruments-service@4fc4900a's confirmed single-parent-predates-fix shape).
  $GIT checkout -q main
  FIX_SHA="$($GIT log ldr --format=%H --grep='^fix(uv):')"
  printf 'base\nENV UV_EXTRA_INDEX_URL=added\n' > Dockerfile
  $GIT add Dockerfile
  $GIT commit -qm "chore(promote): LDR → main (Option-B direct)

Promoted-From-LDR: ${FIX_SHA}"
)

REVERT_SHA="$(cd "$REPO_DIR" && $GIT rev-parse ldr)"
SQUASH_SHA="$(cd "$REPO_DIR" && $GIT rev-parse main)"
FIX_SHA="$(cd "$REPO_DIR" && $GIT log ldr --format=%H --grep='^fix(uv):')"

echo "── Case 1 (THE regression, as a control): git's DEFAULT computed merge-base reintroduces the reverted content ──"
(
  cd "$REPO_DIR"
  $GIT checkout -q -B _bm_old "$REVERT_SHA"
  $GIT merge --no-ff --no-edit main >/dev/null 2>&1
)
if grep -q "UV_EXTRA_INDEX_URL" "$REPO_DIR/Dockerfile"; then
  pass "case1 (control): default git merge reproduces the reported bug (reverted block reintroduced)"
else
  fail "case1 (control): expected the bug to reproduce with git's default merge-base -- test fixture may not match the real incident shape"
fi

echo "── Case 2 (the fix): explicit-base merge-tree preserves the revert ──"
NEW_TREE=$(cd "$REPO_DIR" && $GIT merge-tree --write-tree --merge-base="$FIX_SHA" "$REVERT_SHA" "$SQUASH_SHA" 2>/dev/null)
if [ -n "$NEW_TREE" ] && ! (cd "$REPO_DIR" && $GIT show "${NEW_TREE}:Dockerfile") | grep -q "UV_EXTRA_INDEX_URL"; then
  pass "case2 (the fix): explicit-base merge-tree (--merge-base=<Promoted-From-LDR sha>) preserves the revert"
else
  fail "case2 (the fix): explicit-base merge-tree did NOT preserve the revert -- fix regressed"
fi

echo "── Case 3: the EXTRACTED, REAL check_no_silent_revert_loss() flags the buggy result, not the fixed one ──"
run_revert_check() {
  local ldr_tip="$1" result_treeish="$2"
  (
    cd "$REPO_DIR"
    eval "$REVERT_FUNC"
    if check_no_silent_revert_loss "$ldr_tip" "$result_treeish"; then
      echo "RESULT=CLEAN"
    else
      echo "RESULT=FLAGGED"
    fi
  )
}

OUT_BUGGY="$(run_revert_check "$REVERT_SHA" "_bm_old")"
if printf '%s\n' "$OUT_BUGGY" | grep -q '^RESULT=FLAGGED$'; then
  pass "case3a: check_no_silent_revert_loss() correctly FLAGS the buggy (default-merge-base) result"
else
  fail "case3a: expected FLAGGED for the buggy result, got:"; printf '%s\n' "$OUT_BUGGY"
fi

OUT_FIXED="$(run_revert_check "$REVERT_SHA" "$NEW_TREE")"
if printf '%s\n' "$OUT_FIXED" | grep -q '^RESULT=CLEAN$'; then
  pass "case3b: check_no_silent_revert_loss() correctly does NOT flag the fixed (explicit-base) result — no false alarm"
else
  fail "case3b: expected CLEAN for the fixed result, got:"; printf '%s\n' "$OUT_FIXED"
fi

echo "── Case 4: a genuine conflicting main change is still reported as a conflict by merge-tree (rc!=0), never silently resolved ──"
(
  cd "$REPO_DIR"
  $GIT checkout -q main
  printf 'base\nENV UV_EXTRA_INDEX_URL=totally-different-value\n' > Dockerfile
  $GIT add Dockerfile && $GIT commit -qm "conflict: unrelated different edit"
)
CONFLICT_MAIN="$(cd "$REPO_DIR" && $GIT rev-parse main)"
set +e
(cd "$REPO_DIR" && $GIT merge-tree --write-tree --merge-base="$FIX_SHA" "$REVERT_SHA" "$CONFLICT_MAIN" >/dev/null 2>&1)
MT_RC=$?
set -e
if [ "$MT_RC" -ne 0 ]; then
  pass "case4: a genuine conflicting change still exits non-zero from merge-tree (routes to the existing human conflict-PR path, never silently resolved)"
else
  fail "case4: expected merge-tree to report a conflict (rc!=0) for a genuinely conflicting edit, got rc=0"
fi

echo "── Case 5 (the OTHER bug, this doc's own fix): collateral frontmatter/todo deletion is FLAGGED ──"
# Reproduces the exact mechanism table from main_ldr_backmerge_silently_reapplies_collateral_
# frontmatter_deletion_2026_08_17.md: base has the key/todo, ours (LDR) never touches this
# file at all, theirs (main) drops both as collateral of an unrelated resolution.
DOC_DIR="$WORK/docrepo"
mkdir -p "$DOC_DIR"
(
  cd "$DOC_DIR"
  $GIT init -q
  cat > doc.md <<'DOCEOF'
---
title: X
author: "manifest_hygiene_daily.py"
status: open
---

# Doc

- [ ] [SCRIPT] P2. do the thing
DOCEOF
  $GIT add doc.md && $GIT commit -qm "base"
  $GIT branch ldr

  # init.defaultBranch=main means we are ALREADY on "main" here -- no `checkout -b main`
  # (that branch already exists and would fatal); commit "theirs" directly in place.
  cat > doc.md <<'DOCEOF'
---
title: X
status: open
---

# Doc

DOCEOF
  $GIT add doc.md && $GIT commit -qm "unrelated resolution drops author + todo as collateral"
)
DOC_BASE_SHA="$(cd "$DOC_DIR" && $GIT rev-parse ldr)"
DOC_MAIN_SHA="$(cd "$DOC_DIR" && $GIT rev-parse main)"
DOC_MERGED_TREE="$(cd "$DOC_DIR" && $GIT merge-tree --write-tree ldr main 2>&1)"

run_fm_check() {
  local base="$1" ldr_tip="$2" theirs="$3" result="$4"
  (
    cd "$DOC_DIR"
    eval "$FM_FUNCS"
    if check_no_silent_frontmatter_or_todo_loss "$base" "$ldr_tip" "$theirs" "$result"; then
      echo "RESULT=CLEAN"
    else
      echo "RESULT=FLAGGED"
    fi
  )
}

OUT_FM_BUGGY="$(run_fm_check "$DOC_BASE_SHA" "$DOC_BASE_SHA" "$DOC_MAIN_SHA" "$DOC_MERGED_TREE")"
if printf '%s\n' "$OUT_FM_BUGGY" | grep -q '^RESULT=FLAGGED$'; then
  pass "case5: check_no_silent_frontmatter_or_todo_loss() correctly FLAGS a collateral frontmatter-key + todo-line drop"
else
  fail "case5: expected FLAGGED for the collateral-drop result, got:"; printf '%s\n' "$OUT_FM_BUGGY"
fi

echo "── Case 6: a file BOTH sides touched is out of scope for this guard (real conflict, not silent) ──"
(
  cd "$DOC_DIR"
  $GIT checkout -q ldr
  cat > doc.md <<'DOCEOF'
---
title: X
author: "manifest_hygiene_daily.py"
status: open
extra_key: yes
---

# Doc

- [ ] [SCRIPT] P2. do the thing
- [x] done item
DOCEOF
  $GIT add doc.md && $GIT commit -qm "ldr also legitimately edits doc.md"
)
DOC_LDR_SHA2="$(cd "$DOC_DIR" && $GIT rev-parse ldr)"
set +e
DOC_MERGED_TREE2="$(cd "$DOC_DIR" && $GIT merge-tree --write-tree ldr main 2>&1)"
set -e
OUT_FM_BOTH="$(run_fm_check "$DOC_BASE_SHA" "$DOC_LDR_SHA2" "$DOC_MAIN_SHA" "$DOC_MERGED_TREE2")"
if printf '%s\n' "$OUT_FM_BOTH" | grep -q '^RESULT=CLEAN$'; then
  pass "case6: check_no_silent_frontmatter_or_todo_loss() does not false-positive when ours also touched the file (real conflict stays on the normal path)"
else
  fail "case6: expected CLEAN (out-of-scope skip) when both sides touched the file, got:"; printf '%s\n' "$OUT_FM_BOTH"
fi

echo "── Case 7: an unrelated addition with no deletions anywhere is CLEAN (no false positive) ──"
(
  cd "$DOC_DIR"
  $GIT checkout -q -B main2 ldr
  printf 'unrelated new file\n' > other.md
  $GIT add other.md && $GIT commit -qm "theirs adds an unrelated file only, no deletions anywhere"
)
DOC_MAIN_SHA3="$(cd "$DOC_DIR" && $GIT rev-parse main2)"
DOC_MERGED_TREE3="$(cd "$DOC_DIR" && $GIT merge-tree --write-tree ldr "$DOC_MAIN_SHA3" 2>&1)"
OUT_FM_CLEAN="$(run_fm_check "$DOC_BASE_SHA" "$DOC_BASE_SHA" "$DOC_MAIN_SHA3" "$DOC_MERGED_TREE3")"
if printf '%s\n' "$OUT_FM_CLEAN" | grep -q '^RESULT=CLEAN$'; then
  pass "case7: check_no_silent_frontmatter_or_todo_loss() is CLEAN for an unrelated addition with no deletions"
else
  fail "case7: expected CLEAN for a no-deletion change, got:"; printf '%s\n' "$OUT_FM_CLEAN"
fi

fi  # end BACKMERGE_WF-dependent block

echo
echo "── result: ${PASS} passed / ${FAIL} failed / ${SKIP} skipped ──"
[ "$FAIL" -eq 0 ] || exit 1
