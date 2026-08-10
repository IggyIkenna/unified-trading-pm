#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test: `<repo>@PENDING` is resolved by the push that creates the commit.
#
# WHY THE CONVENTION EXISTS. Commit+Push+Flip asks an agent to write the plan checkbox while the
# work is fresh — before a sha exists. The honest options were both bad: write the todo, ship,
# read the landed sha, edit the doc AGAIN, ship the doc (two extra tool calls per flip, paid
# twice in one session on 2026-08-10), or write the sha visible at `git commit` time, which the
# rebase then invalidates. PENDING removes the choice: author once, and the push fills it in.
#
# The safety property under test is as important as the substitution: a PENDING that does NOT
# get resolved must never reach the corpus, because it would read as a completed todo with no
# evidence behind it. That guard lives in run_hygiene_sweep --precommit and is asserted here
# against the same literal the guard greps for.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  # shellcheck source=/dev/null
  source "${REPO_ROOT}/scripts/dev/reconcile-sha-citations.sh"

  WORK="${BATS_TEST_TMPDIR}"
  PM="${WORK}/unified-trading-pm"
  mkdir -p "${PM}/plans/active" "${PM}/plans/epics" "${PM}/plans/archive"
}

@test "PENDING is replaced with the landed sha, in active plans and epics" {
  printf -- '- [x] 1. shipped — market-tick-data-service@PENDING\n' > "${PM}/plans/active/p.md"
  printf -- '- [x] 2. shipped — market-tick-data-service@PENDING\n' > "${PM}/plans/epics/e.md"

  run resolve_pending_citations "market-tick-data-service" "abcdef1234567890abcdef1234567890abcdef12" "$PM"
  [ "$status" -eq 0 ]

  run cat "${PM}/plans/active/p.md"
  [[ "$output" == *"market-tick-data-service@abcdef1234"* ]]
  [[ "$output" != *"PENDING"* ]]
  run cat "${PM}/plans/epics/e.md"
  [[ "$output" == *"market-tick-data-service@abcdef1234"* ]]
}

@test "only the pushing repo's placeholders are touched" {
  printf -- 'a market-tick-data-service@PENDING\nb execution-service@PENDING\n' > "${PM}/plans/active/p.md"

  run resolve_pending_citations "market-tick-data-service" "abcdef1234567890abcdef1234567890abcdef12" "$PM"
  [ "$status" -eq 0 ]

  run cat "${PM}/plans/active/p.md"
  [[ "$output" == *"market-tick-data-service@abcdef1234"* ]]
  # execution-service has not shipped, so its placeholder must survive for ITS push to resolve.
  [[ "$output" == *"execution-service@PENDING"* ]]
}

@test "plans/archive is out of scope — the historical record is not rewritten" {
  printf -- '- [x] old — market-tick-data-service@PENDING\n' > "${PM}/plans/archive/old.md"

  run resolve_pending_citations "market-tick-data-service" "abcdef1234567890abcdef1234567890abcdef12" "$PM"
  [ "$status" -eq 0 ]

  run cat "${PM}/plans/archive/old.md"
  [[ "$output" == *"PENDING"* ]]
}

@test "no placeholders anywhere is a silent no-op" {
  printf -- '- [x] 1. shipped — market-tick-data-service@abcdef1234\n' > "${PM}/plans/active/p.md"

  run resolve_pending_citations "market-tick-data-service" "abcdef1234567890abcdef1234567890abcdef12" "$PM"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "the precommit guard's literal matches what the resolver writes" {
  # The guard greps -F '@PENDING'. If the resolver's token and the guard's literal ever drift,
  # an unresolved placeholder would sail through — so assert they agree on the same string.
  printf -- '- [x] 1. shipped — market-tick-data-service@PENDING\n' > "${PM}/plans/active/p.md"
  run grep -c -F '@PENDING' "${PM}/plans/active/p.md"
  [ "$output" = "1" ]
  run grep -q -F '@PENDING' "${REPO_ROOT}/scripts/plan-hygiene/run_hygiene_sweep.sh"
  [ "$status" -eq 0 ]
}
