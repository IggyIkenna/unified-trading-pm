#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's per-slot PREK_HOME scoping on the shared-index
# (non-isolated) path (added 2026-08-16, safe_doc_push_shared_prek_home_across_ao_vm_slots_2026_08_16.md).
#
# THE BUG: PREK_HOME was only ever scoped inside the isolated-worktree branch. The AO VM's own
# 2026-08-10 host gate makes isolation OFF by default for every slot on `planning` (the only
# VM), so on that host every slot's shared-index safe-doc-push.sh invocation fell through to
# prek's own unscoped default (~/.cache/prek) and shared ONE patches/ cache dir with every other
# concurrently-running slot -- confirmed root cause of 10+ documented "orphaned patch from a
# different slot" recurrences (safe_doc_push_cross_slot_prek_patch_orphans_completed_fix_2026_08_16.md).
#
# These tests source ONLY the new PREK_HOME-scoping block out of the script (never execute the
# real git/commit/push path) and simulate two distinct slot identities purely via the cwd path
# slot_identity_resolve derives the label from (".../.tabs/<N>/<repo>" -> slot-N) -- no real
# .tabs checkout needed. HOME is always overridden to a scratch dir so no test ever touches the
# real ~/.cache/prek* directories.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"
  SNIPPET="${BATS_TEST_TMPDIR}/snippet.sh"
  sed -n '/^# ── PER-SLOT PREK_HOME/,/^fi$/p' "$SCRIPT" >"$SNIPPET"
  # Sanity: the extraction actually found something (an empty file would make every test below
  # pass vacuously if the script's own comment marker ever drifts).
  [ -s "$SNIPPET" ]
}

# Runs the snippet from a fake cwd shaped like a real slot checkout, with HOME pointed at a
# private scratch dir, and prints the resulting PREK_HOME (empty line if never set).
run_snippet_in_slot() {
  local slot="$1" home="$2"
  local fake_cwd="${BATS_TEST_TMPDIR}/fakeroot-${slot}/.tabs/${slot}/unified-trading-pm"
  mkdir -p "$fake_cwd"
  (
    cd "$fake_cwd" || exit 1
    _SDP_SELF="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"
    export HOME="$home"
    # Hermeticity: a caller (e.g. quickmerge.sh, which legitimately exports its own
    # PREK_HOME for slot-scoping) may already have PREK_HOME set in the environment this
    # bats process inherited -- the snippet's own `if [[ -z "${PREK_HOME:-}" ]]` guard
    # would then skip recomputation and this simulated invocation would silently return
    # the INHERITED value instead of computing fresh, defeating the isolation this helper
    # promises (see file header). Force a clean slate per invocation.
    unset PREK_HOME
    # shellcheck disable=SC1090
    source "$SNIPPET"
    printf '%s' "${PREK_HOME:-}"
  )
}

@test "two different slot labels resolve to two different, non-colliding PREK_HOME dirs" {
  home="${BATS_TEST_TMPDIR}/home1"
  mkdir -p "$home/.cache/prek"
  run run_snippet_in_slot 14 "$home"
  [ "$status" -eq 0 ]
  p14="$output"
  run run_snippet_in_slot 16 "$home"
  [ "$status" -eq 0 ]
  p16="$output"
  [ -n "$p14" ]
  [ -n "$p16" ]
  [ "$p14" != "$p16" ]
  [ "$p14" = "$home/.cache/prek-slot-14" ]
  [ "$p16" = "$home/.cache/prek-slot-16" ]
}

@test "the concurrent-run scenario: patches/ genuinely cannot collide between two slots" {
  # The exact hazard the bug report describes: two slots committing concurrently must not be
  # able to see or restore-over each other's prek patches/ dir.
  home="${BATS_TEST_TMPDIR}/home2"
  mkdir -p "$home/.cache/prek"
  run run_snippet_in_slot 14 "$home"
  p14="$output"
  run run_snippet_in_slot 16 "$home"
  p16="$output"
  mkdir -p "$p14/patches" "$p16/patches"
  : >"$p14/patches/slot14-only.patch"
  [ ! -e "$p16/patches/slot14-only.patch" ]
}

@test "expensive hook-repo installs stay shared via symlink; patches/scratch are never linked" {
  home="${BATS_TEST_TMPDIR}/home3"
  mkdir -p "$home/.cache/prek/repos" "$home/.cache/prek/hooks" "$home/.cache/prek/tools" "$home/.cache/prek/cache"
  : >"$home/.cache/prek/config-tracking.json"
  run run_snippet_in_slot 14 "$home"
  [ "$status" -eq 0 ]
  prek_home="$output"
  [ -L "$prek_home/repos" ]
  [ -L "$prek_home/hooks" ]
  [ -L "$prek_home/tools" ]
  [ -L "$prek_home/cache" ]
  [ -L "$prek_home/config-tracking.json" ]
  # Never pre-created -- prek creates these fresh per slot, and that privacy is the whole point.
  [ ! -e "$prek_home/patches" ]
  [ ! -e "$prek_home/scratch" ]
}

@test "a shared cache item that doesn't exist yet is simply skipped, not an error" {
  home="${BATS_TEST_TMPDIR}/home4"
  mkdir -p "$home/.cache/prek"
  # No repos/hooks/etc. pre-seeded -- first-ever run on this host shape.
  run run_snippet_in_slot 14 "$home"
  [ "$status" -eq 0 ]
  prek_home="$output"
  [ -d "$prek_home" ]
  [ -z "$(find "$prek_home" -mindepth 1)" ]
}

@test "a non-slot cwd (no .tabs/<N>/ segment) leaves PREK_HOME unset -- no-op outside a slot checkout" {
  home="${BATS_TEST_TMPDIR}/home5"
  mkdir -p "$home/.cache/prek"
  fake_cwd="${BATS_TEST_TMPDIR}/laptop-checkout/unified-trading-pm"
  mkdir -p "$fake_cwd"
  run bash -c "
    cd '$fake_cwd' || exit 1
    _SDP_SELF='${REPO_ROOT}/scripts/dev/safe-doc-push.sh'
    export HOME='$home'
    unset PREK_HOME
    source '$SNIPPET'
    printf '%s' \"\${PREK_HOME:-}\"
  "
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "an already-set PREK_HOME (isolated child, or caller override) is never clobbered" {
  home="${BATS_TEST_TMPDIR}/home6"
  mkdir -p "$home/.cache/prek"
  fake_cwd="${BATS_TEST_TMPDIR}/fakeroot-preset/.tabs/14/unified-trading-pm"
  mkdir -p "$fake_cwd"
  run bash -c "
    cd '$fake_cwd' || exit 1
    _SDP_SELF='${REPO_ROOT}/scripts/dev/safe-doc-push.sh'
    export HOME='$home'
    export PREK_HOME='/already/set/by/isolated/child'
    source '$SNIPPET'
    printf '%s' \"\$PREK_HOME\"
  "
  [ "$status" -eq 0 ]
  [ "$output" = "/already/set/by/isolated/child" ]
}

@test "the same slot label is stable across two invocations (idempotent, not a fresh random dir each time)" {
  home="${BATS_TEST_TMPDIR}/home7"
  mkdir -p "$home/.cache/prek"
  run run_snippet_in_slot 22 "$home"
  first="$output"
  run run_snippet_in_slot 22 "$home"
  second="$output"
  [ "$first" = "$second" ]
}

@test "quickmerge.sh carries the mirrored fix (mirror-if-applicable todo requirement) and still parses" {
  run bash -n "${REPO_ROOT}/scripts/quickmerge.sh"
  [ "$status" -eq 0 ]
  grep -q "PER-SLOT PREK_HOME on the shared checkout" "${REPO_ROOT}/scripts/quickmerge.sh"
}

@test "quickmerge.sh's mirrored snippet also resolves two different slots to two different PREK_HOME dirs" {
  qm_snippet="${BATS_TEST_TMPDIR}/qm_snippet.sh"
  sed -n '/^# ── PER-SLOT PREK_HOME on the shared checkout/,/^fi$/p' "${REPO_ROOT}/scripts/quickmerge.sh" >"$qm_snippet"
  [ -s "$qm_snippet" ]
  home="${BATS_TEST_TMPDIR}/qm_home"
  mkdir -p "$home/.cache/prek"
  fake_cwd_14="${BATS_TEST_TMPDIR}/qm-fakeroot-14/.tabs/14/unified-trading-pm"
  fake_cwd_16="${BATS_TEST_TMPDIR}/qm-fakeroot-16/.tabs/16/unified-trading-pm"
  mkdir -p "$fake_cwd_14" "$fake_cwd_16"
  run bash -c "
    cd '$fake_cwd_14' || exit 1
    _QM_SELF='${REPO_ROOT}/scripts/quickmerge.sh'
    export HOME='$home'
    unset PREK_HOME
    source '$qm_snippet'
    printf '%s' \"\${PREK_HOME:-}\"
  "
  [ "$status" -eq 0 ]
  p14="$output"
  run bash -c "
    cd '$fake_cwd_16' || exit 1
    _QM_SELF='${REPO_ROOT}/scripts/quickmerge.sh'
    export HOME='$home'
    unset PREK_HOME
    source '$qm_snippet'
    printf '%s' \"\${PREK_HOME:-}\"
  "
  [ "$status" -eq 0 ]
  p16="$output"
  [ -n "$p14" ]
  [ "$p14" != "$p16" ]
  [ "$p14" = "$home/.cache/prek-slot-14" ]
  [ "$p16" = "$home/.cache/prek-slot-16" ]
}

@test "script documents the fix and still parses" {
  run bash -n "$SCRIPT"
  [ "$status" -eq 0 ]
  grep -q "PER-SLOT PREK_HOME on the shared-index" "$SCRIPT"
}
