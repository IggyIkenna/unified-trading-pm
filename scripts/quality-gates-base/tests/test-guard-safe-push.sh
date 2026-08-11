#!/usr/bin/env bash
# Epic: live_defi_rollout_branch_has_no_delete_protection_2026_08_09
# Lifecycle: permanent
# Delete-when: NA
# Regression test for `scripts/dev/guard-safe-push.sh` — the empty-refspec push guard.
#
# Bug class (confirmed near-miss 2026-08-09): the `git commit-tree` fallback pattern
# pushes `git push origin "<sha>:refs/heads/<branch>"`. An unset source variable makes
# the local side empty, collapsing it to `git push origin ":<branch>"` — which DELETES
# the remote branch. The round-9 sweep agent that hit it self-caught + restored the
# branch same-turn, but nothing structurally blocked the deletion. The guard refuses
# any refspec whose source side is empty/unset (and any non-empty source that does not
# resolve to a real git object) BEFORE git push runs; branch protection covers the
# server side, this covers the local accidental form.
#
# This test drives the REAL guard script (not a re-implementation) against scratch
# repos with REAL `git push`es to a local bare remote, asserting:
#   - a valid `<sha>:refs/heads/<b>` push goes through (remote ref created);
#   - the deletion form `:<b>` / `:` is REFUSED (exit 2) and the remote ref SURVIVES;
#   - an unresolvable source is REFUSED;
#   - `HEAD:refs/heads/<b>` is allowed (the ship-scripts' own refspec form);
#   - `--allow-delete` is the explicit escape hatch that passes a deletion through.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-guard-safe-push.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

GUARD="$(cd "$(dirname "$0")/../.." && pwd)/dev/guard-safe-push.sh"
[ -f "$GUARD" ] || { echo "FATAL: guard-safe-push.sh not found at $GUARD"; exit 2; }

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
GIT="git -c user.email=t@t.local -c user.name=test -c commit.gpgsign=false -c init.defaultBranch=main"

# Scaffold: an origin bare repo + a working clone with one committed file.
ORIGIN="$WORK/origin.git"
REPO="$WORK/repo"
$GIT init --bare "$ORIGIN" >/dev/null 2>&1
$GIT init "$REPO" >/dev/null 2>&1
cd "$REPO" || exit 9
$GIT remote add origin "$ORIGIN"
echo "hello" > f.txt
$GIT add f.txt
$GIT commit -m "initial" >/dev/null 2>&1
$GIT push -u origin main >/dev/null 2>&1
SHA="$(git rev-parse HEAD)"

# ── 1. Valid explicit refspec push goes through ─────────────────────────────────────
if bash "$GUARD" --repo "$REPO" -- "origin" "$SHA:refs/heads/test1" >/dev/null 2>&1; then
  if git ls-remote --exit-code "$ORIGIN" refs/heads/test1 >/dev/null 2>&1; then
    pass "valid '<sha>:refs/heads/<b>' push executed and remote ref test1 created"
  else
    fail "valid refspec push exited 0 but remote ref test1 was not created"
  fi
else
  fail "valid '<sha>:refs/heads/<b>' push was refused (exit non-zero)"
fi

# ── 2. Deletion form `:<branch>` is refused AND the remote ref survives ──────────────
git push origin "$SHA:refs/heads/test2" >/dev/null 2>&1   # seed the ref the delete would remove
if bash "$GUARD" --repo "$REPO" -- "origin" ":refs/heads/test2" >/dev/null 2>&1; then
  fail "deletion form ':refs/heads/<b>' was allowed through (should exit 2)"
else
  if git ls-remote --exit-code "$ORIGIN" refs/heads/test2 >/dev/null 2>&1; then
    pass "deletion form ':refs/heads/<b>' refused; remote ref test2 survived"
  else
    fail "deletion form ':refs/heads/<b>' refused BUT remote ref test2 was still deleted"
  fi
fi

# ── 3. Bare `:` (both sides empty) is refused ───────────────────────────────────────
if bash "$GUARD" --repo "$REPO" -- "origin" ":" >/dev/null 2>&1; then
  fail "bare ':' refspec was allowed through (should exit 2)"
else
  pass "bare ':' refspec refused"
fi

# ── 4. Unresolvable (non-empty but bogus) source is refused ─────────────────────────
if bash "$GUARD" --repo "$REPO" -- "origin" "deadbeef:refs/heads/test4" >/dev/null 2>&1; then
  fail "unresolvable source 'deadbeef' was allowed through (should exit 2)"
else
  pass "unresolvable source refused"
fi

# ── 5. HEAD:refs/heads/<b> (the ship-scripts' own refspec form) is allowed ──────────
if bash "$GUARD" --repo "$REPO" -- "origin" "HEAD:refs/heads/test5" >/dev/null 2>&1; then
  if git ls-remote --exit-code "$ORIGIN" refs/heads/test5 >/dev/null 2>&1; then
    pass "HEAD:refs/heads/<b> push executed and remote ref test5 created"
  else
    fail "HEAD refspec push exited 0 but remote ref test5 was not created"
  fi
else
  fail "HEAD:refs/heads/<b> push was refused (should succeed)"
fi

# ── 6. --allow-delete is the explicit escape hatch ──────────────────────────────────
if bash "$GUARD" --repo "$REPO" --allow-delete -- "origin" ":refs/heads/test5" >/dev/null 2>&1; then
  if git ls-remote --exit-code "$ORIGIN" refs/heads/test5 >/dev/null 2>&1; then
    fail "--allow-delete passed the deletion through but remote ref test5 still exists"
  else
    pass "--allow-delete permits the intentional deletion"
  fi
else
  fail "--allow-delete deletion was refused (exit non-zero)"
fi

echo
if [ "$FAIL" -gt 0 ]; then
  echo "RESULT: $FAIL FAIL / $PASS PASS"
  exit 1
else
  echo "RESULT: $PASS PASS / 0 FAIL"
  exit 0
fi
