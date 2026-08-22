#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
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

# The guard's detector, extracted verbatim from run_hygiene_sweep.sh. Kept in lockstep by the
# last test in this file, which asserts the sweep still contains this exact expression — if the
# two drift, either an unresolved placeholder sails through or documentation gets blocked again.
_pending_detect() {
  awk '
    { s = $0; gsub(/`[^`]*`/, "", s)
      if (s ~ /[a-z][a-z0-9-][a-z0-9-]+@PENDING/) print FILENAME ":" FNR ": " $0 }
  ' "$@"
}

@test "the guard blocks a REAL unresolved placeholder" {
  printf -- '- [x] 1. shipped — Evidence: market-tick-data-service@PENDING\n' > "${PM}/plans/active/p.md"
  run _pending_detect "${PM}/plans/active/p.md"
  [ -n "$output" ]
}

@test "the guard does NOT block prose that documents the convention" {
  # This is the case that actually happened on 2026-08-10: the first doc the naive `grep -F
  # '@PENDING'` version blocked was the issue doc explaining the convention. A guard that makes
  # its own feature undocumentable is a broken guard.
  cat > "${PM}/plans/active/p.md" <<'EOF'
Write `<repo>@PENDING` and the push fills it in.
PENDING is resolved by the quickmerge push that creates the commit.
A worked example: `market-tick-data-service@PENDING` becomes a real sha.
EOF
  run _pending_detect "${PM}/plans/active/p.md"
  [ -z "$output" ]
}

@test "the extracted detector is still identical to the one in run_hygiene_sweep.sh" {
  run grep -qF 'if (s ~ /[a-z][a-z0-9-][a-z0-9-]+@PENDING/) print FILENAME ":" FNR ": " $0' \
    "${REPO_ROOT}/scripts/plan-hygiene/run_hygiene_sweep.sh"
  [ "$status" -eq 0 ]
}
