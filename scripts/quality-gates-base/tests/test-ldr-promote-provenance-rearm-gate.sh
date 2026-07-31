#!/usr/bin/env bash
# Epic: cicd_mvp_ldr_to_main_pipeline_2026_06_30
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for the LDR->main fleet promoter's "provenance re-arm leak" fix
# (plans/archive/2026_07/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md, "Operator decisions / notes"
# -- "Provenance-gate leak" -- closed 2026-07-28).
#
# Bug (found 2026-06-30): `.github/workflows/ldr-to-main-promote-fleet.yml` ran the
# strict-quickmerge provenance check ONLY when it first created a promote PR. A LATER
# tick that found an existing PR "clean" (mergeable_state != dirty/blocked) re-armed
# auto-merge WITHOUT re-checking provenance -- exactly how UAC PR #544 self-resolved
# 2026-06-30, landing non-quickmerge commits on main behind the provenance gate's back.
#
# Fix (2026-07-28): the provenance check was factored into a shared `provenance_check_ok()`
# helper, called from THREE sites in `process_repo()`: (1) PR creation, (2) the
# close+reopen stale-check re-arm fallback, (3) the CLEAN-state (re)arm branch -- the
# exact path UAC #544 slipped through.
#
# Like test-quickmerge-blocked-contract.sh / test-quickmerge-untracked-new-file-guard.sh,
# this EXTRACTS the REAL `provenance_check_ok()` function body from the workflow file (not
# a replica) and:
#   (a) structurally asserts it still carries every contract element, and that it is
#       actually CALLED from all 3 re-arm/arm sites (not just defined and orphaned);
#   (b) functionally runs the extracted function against synthesized git fixtures, with
#       `git fetch <https://...github.com/...>` transparently redirected to a LOCAL bare
#       fixture repo (never touches the network) and `gh` stubbed (never touches the real
#       GitHub API) -- proving a genuinely non-quickmerge LDR commit is caught (returns 1,
#       posts the blocking comment) and a clean range passes (returns 0, no comment).
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-ldr-promote-provenance-rearm-gate.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
WF="$REPO_ROOT/.github/workflows/ldr-to-main-promote-fleet.yml"
[ -f "$WF" ] || { echo "FATAL: ldr-to-main-promote-fleet.yml not found at $WF"; exit 2; }

# ── Extract the REAL provenance_check_ok() function body ─────────────────────────
FUNC=$(awk '
  /^[[:space:]]+provenance_check_ok\(\) \{$/ { c = 1 }
  c { print }
  c && $0 ~ /^[[:space:]]+\}$/ { exit }
' "$WF")
[ -n "$FUNC" ] || { echo "FATAL: could not extract provenance_check_ok() from $WF"; exit 2; }

# Structural anchor #1: the function carries every load-bearing contract element.
case "$FUNC" in
  *"promote_provenance_range.py"*"check_strict_quickmerge.py"*"--block"*"bypassed quickmerge"*"gh pr comment"*"return 1"*"return 0"*)
    pass "structural: provenance_check_ok() carries the range-compute + --block check + blocking-comment + return-1/0 contract" ;;
  *)
    fail "structural: provenance_check_ok() missing an expected contract element"; echo "--- function ---"; echo "$FUNC" ;;
esac

# Structural anchor #2 (THE re-arm-leak regression guard): provenance_check_ok must be
# CALLED from all 3 sites -- creation (PR_URL) + the two re-arm paths (PR_NUM). A future
# edit that adds a new re-arm path without gating it, or removes a gate call, must fail here.
CALL_COUNT_URL=$(grep -c 'provenance_check_ok "\$PR_URL"' "$WF" || true)
CALL_COUNT_NUM=$(grep -c 'provenance_check_ok "\$PR_NUM"' "$WF" || true)
if [ "${CALL_COUNT_URL:-0}" -ge 1 ]; then
  pass "structural: PR-creation path calls provenance_check_ok (\$PR_URL) — ${CALL_COUNT_URL} call site(s)"
else
  fail "structural: PR-creation path does NOT call provenance_check_ok — the create-time gate regressed"
fi
if [ "${CALL_COUNT_NUM:-0}" -ge 2 ]; then
  pass "structural (THE re-arm-leak guard): both re-arm paths call provenance_check_ok (\$PR_NUM) — ${CALL_COUNT_NUM} call site(s) (expect 2: close+reopen fallback + CLEAN-state re-arm)"
else
  fail "structural (THE re-arm-leak guard): expected >=2 re-arm-path provenance_check_ok(\$PR_NUM) call sites, found ${CALL_COUNT_NUM:-0} — the 2026-06-30 leak (UAC PR #544 class) may have regressed"
fi

# ── Functional harness: run the extracted function for real, network-free ────────
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
GIT_BIN="$(command -v git)"
GH_TOKEN_STUB="dummy-token-not-real"

STUBBIN="$WORK/stubbin"
mkdir -p "$STUBBIN"

# `git` stub: passthrough to the REAL git for everything, EXCEPT it rewrites any
# `https://x-access-token:...@github.com/...` remote URL arg to the local fixture bare
# repo path set via $FIXTURE_REMOTE — so the function's real `git fetch <https-url> ...`
# line resolves locally, never touching the network.
cat > "$STUBBIN/git" <<EOF
#!/usr/bin/env bash
REAL_GIT="$GIT_BIN"
args=()
for a in "\$@"; do
  case "\$a" in
    https://x-access-token:*@github.com/*) args+=("\${FIXTURE_REMOTE:?FIXTURE_REMOTE not set}") ;;
    *) args+=("\$a") ;;
  esac
done
exec "\$REAL_GIT" "\${args[@]}"
EOF
chmod +x "$STUBBIN/git"

# `gh` stub: `pr list` (called by promote_provenance_range.py to find the last-promoted
# marker) returns an empty list -- no merged promote PR yet -- so the range resolver
# takes its documented FAIL-SAFE fallback (`origin/main..origin/live-defi-rollout`, the
# same default the shell function itself falls back to). `pr comment` records the body
# to $GH_COMMENT_LOG instead of posting to the real GitHub API. Anything else fails loud
# (a stub gap, not a silent real-API call).
cat > "$STUBBIN/gh" <<'EOF'
#!/usr/bin/env bash
if [ "$1 $2" = "pr list" ]; then
  echo "[]"
  exit 0
fi
if [ "$1 $2" = "pr comment" ]; then
  shift 2
  PR_ID="$1"; shift
  BODY=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --body) BODY="$2"; shift 2 ;;
      *) shift ;;
    esac
  done
  printf '%s' "$BODY" > "${GH_COMMENT_LOG:?GH_COMMENT_LOG not set}"
  printf 'PR_ID=%s\n' "$PR_ID" > "${GH_COMMENT_LOG}.meta"
  exit 0
fi
echo "gh stub: unexpected invocation: $*" >&2
exit 1
EOF
chmod +x "$STUBBIN/gh"

GIT="git -c user.email=t@t.local -c user.name=test -c commit.gpgsign=false -c init.defaultBranch=main"

# Fixture bare repo with `main` + `live-defi-rollout` branches -- $1 selects whether LDR
# carries an extra trailer-less *.py commit (the bypass) on top of main.
make_fixture() {
  local label="$1" inject_bypass="$2"
  local rem="$WORK/rem_$label.git" loc="$WORK/loc_$label"
  $GIT init -q --bare "$rem"
  $GIT clone -q "$rem" "$loc" 2>/dev/null
  ( cd "$loc" \
      && printf 'base\n' > README.md && $GIT add README.md && $GIT commit -qm "base" \
      && $GIT push -q origin main )
  if [ "$inject_bypass" = "true" ]; then
    ( cd "$loc" \
        && mkdir -p src \
        && printf 'x = 1\n' > src/bus.py \
        && $GIT add src/bus.py \
        && $GIT commit -qm "fix(kill-switch): guard the bus" )
  fi
  ( cd "$loc" && $GIT push -q origin "HEAD:live-defi-rollout" )
  echo "$rem"
}

run_provenance_check() {
  local fixture_remote="$1" pr_id="$2"
  (
    PATH="$STUBBIN:$PATH"
    export PATH
    FIXTURE_REMOTE="$fixture_remote"
    export FIXTURE_REMOTE
    GH_TOKEN="$GH_TOKEN_STUB"; export GH_TOKEN
    OWNER="TestOwner"; export OWNER
    REPO="test-repo"; export REPO
    GITHUB_WORKSPACE="$REPO_ROOT"; export GITHUB_WORKSPACE
    GH_COMMENT_LOG="$WORK/comment_$pr_id.txt"; export GH_COMMENT_LOG
    rm -f "$GH_COMMENT_LOG" "$GH_COMMENT_LOG.meta"
    eval "$FUNC"
    if provenance_check_ok "$pr_id"; then
      echo "RESULT=CLEAN"
    else
      echo "RESULT=BLOCKED"
    fi
  )
}

echo "── Case 1: clean LDR (no bypass commit) — must return CLEAN, post no comment ──"
rem1=$(make_fixture case1 false)
out1=$(run_provenance_check "$rem1" "111")
if printf '%s\n' "$out1" | grep -q '^RESULT=CLEAN$'; then
  pass "case1: provenance_check_ok returned CLEAN for a genuinely quickmerge-clean range"
else
  fail "case1: expected CLEAN, got:"; printf '%s\n' "$out1"
fi
if [ -s "$WORK/comment_111.txt" ]; then
  fail "case1: a blocking comment was posted despite a clean range"
else
  pass "case1: no blocking comment posted (correct)"
fi

echo "── Case 2 (THE regression this closes): LDR carries a trailer-less *.py bypass commit — must return BLOCKED + post the comment ──"
rem2=$(make_fixture case2 true)
out2=$(run_provenance_check "$rem2" "222")
if printf '%s\n' "$out2" | grep -q '^RESULT=BLOCKED$'; then
  pass "case2: provenance_check_ok returned BLOCKED for a non-quickmerge LDR commit"
else
  fail "case2: expected BLOCKED, got:"; printf '%s\n' "$out2"
fi
if [ -s "$WORK/comment_222.txt" ] && grep -q 'promote:provenance-blocked' "$WORK/comment_222.txt" \
    && grep -q 'NOT (re-)armed' "$WORK/comment_222.txt"; then
  pass "case2: blocking comment posted with the stable marker + (re-)arm-neutral wording"
else
  fail "case2: blocking comment missing or malformed"; cat "$WORK/comment_222.txt" 2>/dev/null || echo "(no comment file)"
fi
if [ -f "$WORK/comment_222.txt.meta" ] && grep -q 'PR_ID=222' "$WORK/comment_222.txt.meta"; then
  pass "case2: comment posted against the caller-supplied PR identifier (proves the re-arm call sites, which pass \$PR_NUM not a PR URL, are wired correctly)"
else
  fail "case2: comment not correctly addressed to the supplied PR identifier"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
