#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test: uncommitted work OUTSIDE a ship's --files is noticed when a reconcile eats it.
#
# THE INCIDENT THIS REPRODUCES (2026-08-10). Every loss guard built that day fingerprints only the
# files named in `--files`. An edit to `scripts/quickmerge.sh` that was not in that run's --files
# collided with a peer's upstream change to the same file; `git pull --rebase --autostash` stashed
# it, the pop resolved against the incoming version, and the edit vanished. The run reported
# success. Nobody was told. It surfaced by accident.
#
# So the case under test is specifically the NON-named file. The named-file case was already
# covered (quickmerge's _QM_ENTRY_FINGERPRINT, safe-doc-push's exit 10) and is not the gap.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  GUARD="${REPO_ROOT}/scripts/dev/tree-wip-guard.sh"
  WORK="${BATS_TEST_TMPDIR}/repo"
  mkdir -p "$WORK"
  cd "$WORK"
  git init -q .
  git config user.email t@t
  git config user.name t
  printf 'original\n' > shipped.md
  printf 'original\n' > bystander.sh
  git add -A
  git commit -q -m seed
  # shellcheck source=/dev/null
  source "$GUARD"
}

@test "a clobbered NON-named file is reported" {
  printf 'my uncommitted work\n' > bystander.sh   # not in --files
  printf 'my shipped change\n' > shipped.md       # in --files
  snap="$(wip_guard_snapshot)"

  # Simulate the reconcile resolving against someone else's version.
  printf 'peer version\n' > bystander.sh

  run wip_guard_report "$snap" "shipped.md"
  [ "$status" -eq 0 ]                       # advisory: never fails the run itself
  [[ "$output" == *"bystander.sh"* ]]
  [[ "$output" == *"GONE"* ]]
  [[ "$output" == *"stash"* ]]              # must hand over a recovery path
}

@test "the recovery advice warns against a wholesale restore" {
  # The near-miss during the real incident: restoring the whole file from the stash would have
  # silently reverted the peer's change that caused the collision in the first place.
  printf 'mine\n' > bystander.sh
  snap="$(wip_guard_snapshot)"
  printf 'peer\n' > bystander.sh
  run wip_guard_report "$snap" ""
  [[ "$output" == *"BY HAND"* ]]
  [[ "$output" == *"revert THEIR work"* ]]
}

@test "a NAMED file rewritten by the run is NOT reported" {
  # prettier/autofix legitimately rewrite what you are shipping; flagging that would train
  # everyone to ignore the warning.
  printf 'mine\n' > shipped.md
  snap="$(wip_guard_snapshot)"
  printf 'mine, reformatted by prettier\n' > shipped.md
  run wip_guard_report "$snap" "shipped.md"
  [ -z "$output" ]
}

@test "an untouched tree reports nothing" {
  printf 'mine\n' > bystander.sh
  snap="$(wip_guard_snapshot)"
  run wip_guard_report "$snap" ""
  [ -z "$output" ]
}

@test "a DELETED non-named file is reported too" {
  printf 'mine\n' > bystander.sh
  snap="$(wip_guard_snapshot)"
  rm -f bystander.sh
  run wip_guard_report "$snap" ""
  [[ "$output" == *"bystander.sh"* ]]
  [[ "$output" == *"GONE"* ]]
}

@test "untracked scratch files are ignored" {
  # Autostash does not touch untracked files by default; flagging every scratch file would be
  # noise that buries the real signal.
  printf 'scratch\n' > notes.tmp
  snap="$(wip_guard_snapshot)"
  [[ "$snap" != *"notes.tmp"* ]]
}

# ── wip_guard_restore: the mechanical half ──────────────────────────────────────────────────
# The warning text told people not to restore wholesale. These assert the code REFUSES to, so
# the property holds for someone who never reads the warning.

@test "restore is a plain copy when nobody else touched the file" {
  printf 'mine\n' > bystander.sh
  git stash push -q -m parked -- bystander.sh
  run wip_guard_restore "stash@{0}" bystander.sh
  [ "$status" -eq 0 ]
  [[ "$output" == *"nobody else changed it"* ]]
  [ "$(cat bystander.sh)" = "mine" ]
}

@test "a peer's change SURVIVES the restore instead of being clobbered" {
  # The exact 2026-08-10 near-miss: my edit parked, their edit landed, naive restore deletes theirs.
  # The BASE must already hold the shared lines, otherwise both sides rewrite the whole file and
  # every edit is a same-region conflict by construction (this test was wrong that way first).
  # Edits must be in SEPARATE regions. Measured: git merge-file conflicts on ADJACENT lines
  # (rc=1) and merges cleanly when separated (rc=0) — correct, conservative behaviour, but it
  # made the first two versions of this test assert the wrong thing.
  printf 'a\nb\nc\nd\ne\nf\n' > bystander.sh
  git add -A && git -c user.email=t@t -c user.name=t commit -q -m "shared base"
  printf 'a\nMINE\nc\nd\ne\nf\n' > bystander.sh
  git stash push -q -m parked -- bystander.sh
  printf 'a\nb\nc\nd\ne\nTHEIRS\n' > bystander.sh      # peer changed a DIFFERENT region
  git add -A && git -c user.email=t@t -c user.name=t commit -q -m "peer change"

  run wip_guard_restore "stash@{0}" bystander.sh
  [ "$status" -eq 0 ]
  run cat bystander.sh
  [[ "$output" == *"MINE"* ]]      # my parked work is back...
  [[ "$output" == *"THEIRS"* ]]    # ...and theirs was NOT deleted
}

@test "a genuine same-line collision conflicts loudly rather than picking a winner" {
  printf 'shared\nMINE\n' > bystander.sh
  git stash push -q -m parked -- bystander.sh
  printf 'shared\nTHEIRS\n' > bystander.sh
  git add -A && git -c user.email=t@t -c user.name=t commit -q -m "peer change same line"

  run wip_guard_restore "stash@{0}" bystander.sh
  [ "$status" -eq 1 ]
  [[ "$output" == *"conflict markers"* ]]
  run cat bystander.sh
  [[ "$output" == *"THEIRS"* ]]    # their side is still present to resolve against
}

@test "an unresolvable base is refused, not guessed" {
  run wip_guard_restore "stash@{99}" bystander.sh
  [ "$status" -eq 2 ]
  [[ "$output" == *"refusing to guess"* ]]
}
