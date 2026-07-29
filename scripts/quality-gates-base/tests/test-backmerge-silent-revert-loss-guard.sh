#!/usr/bin/env bash
# Epic: ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for the LDR<->main promote/backmerge "silent-revert-loss" fix
# (plans/active/issues/ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29.md).
#
# Bug (found 2026-07-29): a squash-promote commit's real git parent is main's PREVIOUS
# tip, never the LDR SHA it actually squashed. If a revert lands on LDR after that LDR
# SHA was read but before/around the squash landing on main, git's own computed
# merge-base(LDR-tip, squash-commit) resolves to a STALE ancestor that predates BOTH the
# original fix and its revert -- so main-backmerge-to-ldr's 3-way merge reads the revert
# as "unchanged since base" and silently re-takes main's stale (pre-revert) content. No
# conflict, no marker: `git log` shows the revert; the file content does not reflect it.
# Confirmed live on instruments-service (fix 2941646c, revert 8df0e94e, stale-squash
# 4fc4900a, backmerge ed04b405 -- exact SHAs in the issue doc).
#
# Fix (2026-07-29): `ldr-to-main-promote-fleet.yml` stamps a `Promoted-From-LDR: <sha>`
# trailer on every squash-promote commit body; `main-backmerge-to-ldr.yml` reads that
# trailer and forces the 3-way merge onto that EXPLICIT base via
# `git merge-tree --write-tree --merge-base=<sha>` instead of git's own (possibly-stale)
# computed one. A `check_no_silent_revert_loss()` safety net additionally catches the
# narrower "did this merge fully discard LDR's own last commit's effect" signature,
# independent of the trailer (defense-in-depth for a genuine main-only revert case too).
#
# Like test-ldr-promote-provenance-rearm-gate.sh, this test:
#   (a) structurally asserts the trailer-stamp + explicit-base + safety-net code is
#       actually present and wired into the promote/backmerge workflow files (not just
#       described in a comment);
#   (b) functionally reproduces the CONFIRMED instruments-service graph shape (fix ->
#       revert -> stale-squash-with-trailer) with REAL git commands, and proves: the OLD
#       git-computed merge-base reintroduces the reverted content (the bug, as a control);
#       the NEW explicit-base merge-tree path preserves the revert (the fix); and the
#       EXTRACTED, REAL `check_no_silent_revert_loss()` function (not a re-implementation)
#       correctly flags the buggy result and does NOT flag the fixed result.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-backmerge-silent-revert-loss-guard.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PROMOTE_WF="$REPO_ROOT/.github/workflows/ldr-to-main-promote-fleet.yml"
BACKMERGE_WF="$REPO_ROOT/scripts/workflow-templates/main-backmerge-to-ldr.yml"
[ -f "$PROMOTE_WF" ] || { echo "FATAL: ldr-to-main-promote-fleet.yml not found at $PROMOTE_WF"; exit 2; }
[ -f "$BACKMERGE_WF" ] || { echo "FATAL: main-backmerge-to-ldr.yml not found at $BACKMERGE_WF"; exit 2; }

# ── Structural anchor #1: every squash-merge arm site stamps the trailer ─────────────
TRAILER_STAMP_COUNT=$(grep -c 'Promoted-From-LDR: %s' "$PROMOTE_WF" || true)
if [ "${TRAILER_STAMP_COUNT:-0}" -ge 3 ]; then
  pass "structural: ldr-to-main-promote-fleet.yml stamps Promoted-From-LDR on all 3 squash-merge arm sites (found ${TRAILER_STAMP_COUNT})"
else
  fail "structural: expected >=3 Promoted-From-LDR trailer stamp sites in ldr-to-main-promote-fleet.yml, found ${TRAILER_STAMP_COUNT:-0} -- a squash arm/re-arm path may be unstamped"
fi

# ── Structural anchor #2: the backmerge reads the trailer + uses an explicit merge-base ──
case "$(cat "$BACKMERGE_WF")" in
  *"Promoted-From-LDR"*"merge-tree --write-tree --merge-base="*"check_no_silent_revert_loss"*)
    pass "structural: main-backmerge-to-ldr.yml carries the trailer-read + explicit-merge-base + safety-net contract" ;;
  *)
    fail "structural: main-backmerge-to-ldr.yml missing an expected fix element (trailer read / explicit merge-base / safety net)" ;;
esac

# ── Extract the REAL check_no_silent_revert_loss() function body ─────────────────────
FUNC=$(awk '
  /^[[:space:]]+check_no_silent_revert_loss\(\) \{$/ { c = 1 }
  c { print }
  c && $0 ~ /^[[:space:]]+\}$/ { exit }
' "$BACKMERGE_WF")
[ -n "$FUNC" ] || { echo "FATAL: could not extract check_no_silent_revert_loss() from $BACKMERGE_WF"; exit 2; }

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
run_check() {
  local ldr_tip="$1" result_treeish="$2"
  (
    cd "$REPO_DIR"
    eval "$FUNC"
    if check_no_silent_revert_loss "$ldr_tip" "$result_treeish"; then
      echo "RESULT=CLEAN"
    else
      echo "RESULT=FLAGGED"
    fi
  )
}

OUT_BUGGY="$(run_check "$REVERT_SHA" "_bm_old")"
if printf '%s\n' "$OUT_BUGGY" | grep -q '^RESULT=FLAGGED$'; then
  pass "case3a: check_no_silent_revert_loss() correctly FLAGS the buggy (default-merge-base) result"
else
  fail "case3a: expected FLAGGED for the buggy result, got:"; printf '%s\n' "$OUT_BUGGY"
fi

OUT_FIXED="$(run_check "$REVERT_SHA" "$NEW_TREE")"
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

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
