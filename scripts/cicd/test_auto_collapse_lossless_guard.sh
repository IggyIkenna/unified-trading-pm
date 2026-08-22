#!/usr/bin/env bash
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
#
# Guard test for auto_collapse_lossless_promote.sh (bug-2 auto-collapse). The auto-collapse only fires
# when staging↔main differ by ONLY pyproject.toml's `version =` line (+ never a downgrade). This test
# replicates the script's LOSSLESS-GUARD commands against synthetic local git repos and asserts the
# classification, so a future edit that weakens the guard (and would collapse a REAL diff) fails CI.
#
# Run: bash scripts/cicd/test_auto_collapse_lossless_guard.sh   (exit 0 = all cases pass)
set -uo pipefail

PASS=0; FAIL=0
_repo() {  # $1=dir  — make a repo with main; caller adds a staging branch
  git init -q "$1"; (cd "$1"
    git config user.email t@t; git config user.name t
    printf 'version = "0.80.0"\n[project]\nname = "x"\n' > pyproject.toml
    printf 'print("hi")\n' > app.py
    git add -A && git commit -qm base && git branch -m main && git branch staging)
}

# Replicates the script's LOSSLESS GUARD verdict ("LOSSLESS" / "NOT_LOSSLESS").
_guard() {  # $1=repo dir  -> echoes verdict
  ( cd "$1"
    CHANGED="$(git diff --name-only main staging 2>/dev/null | sort -u)"
    if [ "$CHANGED" != "pyproject.toml" ]; then echo "NOT_LOSSLESS"; return; fi
    NONVER="$(git diff main staging -- pyproject.toml 2>/dev/null \
      | grep -E '^[+-]' | grep -vE '^(\+\+\+|---)' \
      | grep -vE '^[+-][[:space:]]*version[[:space:]]*=' | head -1)"
    [ -n "$NONVER" ] && { echo "NOT_LOSSLESS"; return; }
    echo "LOSSLESS" )
}

_assert() {  # $1=name $2=expected $3=actual
  if [ "$2" = "$3" ]; then PASS=$((PASS+1)); echo "  ok   $1 ($3)";
  else FAIL=$((FAIL+1)); echo "  FAIL $1: expected $2 got $3"; fi
}

T="$(mktemp -d)"; trap 'rm -rf "$T"' EXIT

# Case A — staging differs ONLY in the version line  => LOSSLESS (collapse allowed)
_repo "$T/a"; ( cd "$T/a"; git checkout -q staging
  sed -i 's/0.80.0/0.82.0/' pyproject.toml; git commit -qam bump )
_assert "version-only diff" "LOSSLESS" "$(_guard "$T/a")"

# Case B — staging changes a DIFFERENT file too  => NOT_LOSSLESS (must escalate, never collapse)
_repo "$T/b"; ( cd "$T/b"; git checkout -q staging
  sed -i 's/0.80.0/0.82.0/' pyproject.toml
  printf 'print("changed")\n' > app.py; git commit -qam bump+code )
_assert "extra file changed" "NOT_LOSSLESS" "$(_guard "$T/b")"

# Case C — staging changes pyproject but a NON-version line  => NOT_LOSSLESS
_repo "$T/c"; ( cd "$T/c"; git checkout -q staging
  sed -i 's/name = "x"/name = "y"/' pyproject.toml; git commit -qam rename )
_assert "non-version pyproject hunk" "NOT_LOSSLESS" "$(_guard "$T/c")"

echo "auto-collapse guard: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
