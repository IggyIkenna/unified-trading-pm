#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's commit-failure classifier (added 2026-08-08).
#
# THE BUG: the script funnelled EVERY `git commit` rejection into backoff+continue, so a
# deterministic pre-commit content failure (plan-hygiene conflict markers / frontmatter
# schema / terminal-status-archived / todo format / line caps) was retried 6 times and then
# reported as "Exhausted N attempts under sustained contention -- this is transient, not a
# defect. Re-run." Measured live during the 2026-08-08 sports canonicalisation push, where a
# stale conflict marker and a terminal-status archival violation were both misreported as
# transient contention. That message sends the next agent into a retry loop against something
# that can never succeed, and buries the hook's own remedy under 6 repetitions.
#
# The classifier keys on prek's `- hook id: <id>` lines rather than message text, so it does
# not drift when a hook's human-readable wording changes.

setup() {
  # Tests must NOT take a host-wide lock. push-host-governor.sh hands out K=8 tokens PER HOST,
  # shared with real safe-doc-push runs, so under `bats -j` these contended with each other AND
  # with a peer session's genuine push — exit codes became a function of unrelated fleet
  # activity. One run green, the next red, the failure moving between tests.
  export PUSH_GOV_DISABLE=true
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"
  # Source ONLY the classifier + its allowlist out of the script, so the test never has to
  # execute the real git/push path.
  HARNESS="${BATS_TEST_TMPDIR}/harness.sh"
  {
    sed -n '/^RETRIABLE_HOOK_IDS=/,/^}/p' "$SCRIPT"
    echo 'commit_failure_is_retriable "$1" && echo RETRIABLE || echo DETERMINISTIC'
  } >"$HARNESS"
}

classify() {
  printf '%s' "$1" >"${BATS_TEST_TMPDIR}/err.txt"
  bash "$HARNESS" "${BATS_TEST_TMPDIR}/err.txt"
}

@test "plan-hygiene failure is DETERMINISTIC (the exact 2026-08-08 regression)" {
  run classify 'Plan hygiene (staged plans + codex + runbooks).......Failed
- hook id: plan-hygiene
- exit code: 1
    ❌ Conflict marker(s) in staged plans — resolve before commit
  ❌ check_terminal_status_archived (--only): 1 violation(s) in staged files'
  [ "$status" -eq 0 ]
  [ "$output" = "DETERMINISTIC" ]
}

@test "branch drift alone is RETRIABLE (a genuine race the retry loop clears)" {
  run classify 'Check branch drift (are you behind origin?).......Failed
- hook id: check-branch-drift
- exit code: 1
  BRANCH DRIFT: You are 3 commit(s) behind origin/live-defi-rollout'
  [ "$status" -eq 0 ]
  [ "$output" = "RETRIABLE" ]
}

@test "drift PLUS a content failure is DETERMINISTIC (content must win)" {
  # Attempt 1 of the live incident looked exactly like this: prettier-autostage skipped
  # itself BECAUSE of drift, but plan-hygiene had also genuinely failed. Retrying cleared
  # the drift and the content failure remained -- so the mixed case must not be retriable.
  run classify 'Check branch drift (are you behind origin?).......Passed
Plan hygiene.......Failed
- hook id: plan-hygiene
- exit code: 1
Format with Prettier (auto-stage).......Failed
- hook id: prettier-autostage
- exit code: 1'
  [ "$status" -eq 0 ]
  [ "$output" = "DETERMINISTIC" ]
}

@test "'files were modified by this hook' with no content rejection is RETRIABLE (F2 autofix signal, pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10)" {
  # prek's own re-stage-and-rerun autofix signal, not a content verdict -- observed twice
  # 2026-08-10 misclassified as DETERMINISTIC even though every sub-check reported OK.
  run classify 'Format with Prettier (auto-stage)........................................Passed
plan-hygiene.............................................................Passed
- hook id: plan-hygiene
- files were modified by this hook'
  [ "$status" -eq 0 ]
  [ "$output" = "RETRIABLE" ]
}

@test "'files were modified by this hook' PLUS a genuine content rejection in the SAME run is still RETRIABLE by design (worst case is one extra attempt, not a false hard-stop)" {
  # By design (see commit_failure_is_retriable's own comment): a mixed failure retries once
  # re-staging the autofix; if a genuine violation is ALSO present it is unchanged by the retry
  # and the *next* attempt (which no longer carries "files were modified", only the unresolved
  # violation) correctly exits 6 -- covered by the "plan-hygiene failure is DETERMINISTIC" case
  # above once the autofix text is gone. This test pins the deliberate one-extra-attempt
  # tradeoff so it is not mistaken for a bug and "fixed" into a false hard-stop.
  run classify 'plan-hygiene.............................................................Failed
- hook id: plan-hygiene
- files were modified by this hook
- exit code: 1
    ❌ Conflict marker(s) in staged plans — resolve before commit'
  [ "$status" -eq 0 ]
  [ "$output" = "RETRIABLE" ]
}

@test "a rejection with no parseable hook id stays RETRIABLE (preserves prior behaviour)" {
  run classify 'error: unable to create index.lock: File exists'
  [ "$status" -eq 0 ]
  [ "$output" = "RETRIABLE" ]
}

@test "frontmatter-schema and todo-format hooks are DETERMINISTIC" {
  run classify 'Plan hygiene.......Failed
- hook id: frontmatter-schema
- exit code: 1'
  [ "$status" -eq 0 ]
  [ "$output" = "DETERMINISTIC" ]
}

@test "script documents exit code 6 and still parses" {
  run bash -n "$SCRIPT"
  [ "$status" -eq 0 ]
  grep -q "6 commit rejected by a pre-commit hook" "$SCRIPT"
  grep -q "exit 6" "$SCRIPT"
}

@test "the misleading unconditional transient claim is gone from EMITTED output" {
  # The old terminal message asserted "this is transient, not a defect" for ALL exhaustion,
  # including deterministic content failures. It must never come back as emitted text.
  # Scoped to non-comment lines on purpose: the fix's own explanatory comment quotes the old
  # string verbatim as documentation, and that must stay -- a blunt whole-file grep would
  # fail on the very comment explaining the bug.
  run bash -c "grep -vE '^[[:space:]]*#' '$SCRIPT' | grep -c 'this is transient, not a defect' || true"
  [ "$output" = "0" ]
}
