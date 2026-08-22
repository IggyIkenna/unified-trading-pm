#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's rebase-failure classifier (added 2026-08-16,
# safe_doc_push_false_positive_rebase_multiple_branches_2026_08_16.md).
#
# THE BUG: autostash_rebase_reconcile funnelled EVERY `git pull --rebase --autostash` failure
# into "this is a genuine content collision, not contention" and an immediate exit 3 -- even a
# failure that is plainly NOT a content collision, like git's own usage/state error "Cannot
# rebase onto multiple branches", observed live blocking a shippable, non-conflicting doc change
# on what direct inspection showed was an ordinary clean ahead/behind divergence.
#
# rebase_failure_is_content_conflict keys on git's own conflict markers (CONFLICT (content),
# could not apply, unmerged files) to classify a real conflict, and on a short allowlist of
# known NON-content failure signatures (including "Cannot rebase onto multiple branches") to
# classify a retriable non-conflict, so it does not drift if git's wording changes elsewhere.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"
  # Source ONLY the classifier function out of the script, so the test never has to execute
  # the real git/push path.
  HARNESS="${BATS_TEST_TMPDIR}/harness.sh"
  {
    sed -n '/^rebase_failure_is_content_conflict() {/,/^}/p' "$SCRIPT"
    echo 'rebase_failure_is_content_conflict "$1" && echo CONFLICT || echo NOT_CONFLICT'
  } >"$HARNESS"
}

classify() {
  printf '%s' "$1" >"${BATS_TEST_TMPDIR}/err.txt"
  bash "$HARNESS" "${BATS_TEST_TMPDIR}/err.txt"
}

@test "a genuine content conflict classifies as CONFLICT (needs a human, unchanged exit-3 behaviour)" {
  run classify 'Auto-merging f.txt
CONFLICT (content): Merge conflict in f.txt
error: could not apply e35c313... local conflicting change
hint: Resolve all conflicts manually, mark them as resolved with "git add/rm <conflicted_files>"'
  [ "$status" -eq 0 ]
  [ "$output" = "CONFLICT" ]
}

@test "'Cannot rebase onto multiple branches' classifies as NOT_CONFLICT (the exact 2026-08-16 false positive)" {
  run classify 'fatal: Cannot rebase onto multiple branches'
  [ "$status" -eq 0 ]
  [ "$output" = "NOT_CONFLICT" ]
}

@test "an index.lock failure classifies as NOT_CONFLICT (transient contention, retriable)" {
  run classify "fatal: Unable to create '/repo/.git/index.lock': File exists.
Another git process seems to be running in this repository."
  [ "$status" -eq 0 ]
  [ "$output" = "NOT_CONFLICT" ]
}

@test "a stale unmerged-files state classifies as CONFLICT (a real prior conflict, needs a human)" {
  run classify "error: Pulling is not possible because you have unmerged files.
fatal: Exiting because of an unresolved conflict."
  [ "$status" -eq 0 ]
  [ "$output" = "CONFLICT" ]
}

@test "unrecognized text defaults to CONFLICT (safe default -- preserves prior behaviour rather than guessing retriable)" {
  run classify 'some completely unexpected git error nobody has seen before'
  [ "$status" -eq 0 ]
  [ "$output" = "CONFLICT" ]
}

@test "script documents rebase_failure_is_content_conflict's three return codes and still parses" {
  run bash -n "$SCRIPT"
  [ "$status" -eq 0 ]
  grep -q "Returns 2 on a recognized NON-content failure" "$SCRIPT"
  grep -q "rebase_failure_is_content_conflict" "$SCRIPT"
}
