#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's shared-index `git add -- "${FILES[@]}"` step dropping a
# git-mv'd rename (safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md).
#
# THE BUG: `git mv old new` removes `old` from the index outright (folded into `new`'s R100 rename
# pair) -- `old` has NO index entry at all, unlike an ordinary tracked-but-missing file. Naming
# `old` in `--files` and calling `git add -- "${FILES[@]}"` on the combined list therefore hit
# `fatal: pathspec '<old>' did not match any files` -- and that failure is NOT scoped to the one bad
# pathspec: a mixed `git add -- <valid> <goneless>` call stages NONE of its paths. Every one of the
# script's 6 retry attempts hit the identical deterministic failure (not a transient race), so the
# retry loop could never converge -- confirmed by reproduction in the issue doc, including a
# 0-stash-entry control that fails identically to the original 24-stash-pile incident, which
# falsifies the original "extreme-quarantine" hypothesis. That is WHY every test below runs at a
# near-zero stash-pile size on purpose: gating this coverage on a large pile would test the wrong
# variable.
#
# THE FIX (landed unified-trading-pm@7e03ff2f01, slot-14, while this test was in flight --
# see the issue doc's Progress Log): `stage_named_files()` (scripts/dev/safe-doc-push.sh) replaces
# the single combined `git add -- "${FILES[@]}"` with a per-file loop that checks the INDEX
# directly for a missing-from-disk path instead of trusting `git add`'s exit code -- distinguishing
# "tracked but missing, needs staging" (git add stages the deletion) from "absent from disk AND
# the index, but HEAD still has it" (already the desired end state, nothing to do) from "absent
# everywhere, a genuine caller typo" (a real error). This test suite provides END-TO-END coverage
# (a real `bash safe-doc-push.sh` invocation through the full retry loop, ground-truth-verified
# against a real origin) at a LOW stash-pile size, complementing
# test_safe_doc_push_extreme_quarantine_rename_survives.bats's white-box unit coverage of
# stage_named_files() itself.
#
# Hermetic: no network, real local git repos ("origin" is a second local bare repo), mirrors the
# established pattern in test_safe_doc_push_could_not_stage_vs_nothing_to_stage.bats /
# test_safe_doc_push_isolated_deletion_propagates.bats.
#
# Run: bats tests/test_safe_doc_push_rename_source_goneless_add.bats

setup() {
  # SDP_ISOLATED=0 is REQUIRED, not incidental: the bug lives in the shared-index retry loop.
  # Isolated mode's copy loop starts from a fresh origin/$BRANCH checkout where the old path is
  # still a plain tracked file at that point, so it never hits this shape at all.
  export SDP_ISOLATED=0
  # Tests must NOT take a host-wide lock -- push-host-governor.sh hands out K=8 tokens PER HOST,
  # shared with real safe-doc-push runs, so under `bats -j` these would contend with each other AND
  # with a peer session's genuine push.
  export PUSH_GOV_DISABLE=true
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"

  WORK="${BATS_TEST_TMPDIR}"
  git init -q --bare "${WORK}/origin.git"
  git clone -q "${WORK}/origin.git" "${WORK}/work"
  cd "${WORK}/work"
  git config user.email "test@example.com"
  git config user.name "test"
  git checkout -q -B live-defi-rollout
  mkdir -p plans/active plans/archive/2026_08
  echo "active plan content" > plans/active/thing.md
  echo "sibling content" > plans/active/sibling.md
  git add plans/active/thing.md plans/active/sibling.md
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout

  # Fake `sleep` on PATH so any retry backoff is instant.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"

  # Deliberately near-zero: confirms the fix does not depend on autostash_guard_bound_backlog's
  # "10 entries is extreme" quarantine branch. 2 unrelated pre-existing stash entries -- far below
  # that threshold -- so this checkout is not even eligible for the quarantine branch.
  echo "unrelated-1" > scratch_unrelated.txt
  git stash push -q -u -m "safety-snapshot: unrelated pre-existing entry 1"
  echo "unrelated-2" > scratch_unrelated.txt
  git stash push -q -u -m "safety-snapshot: unrelated pre-existing entry 2"
}

@test "a git-mv'd rename's OLD path no longer breaks staging -- lands cleanly at a low (2-entry) stash-pile size" {
  # git does not track empty directories -- the stash pushes above (their -u leg) leave
  # plans/archive/2026_08 pruned since nothing was ever in it. Real callers always mkdir -p the
  # destination immediately before a `git mv` archival (mirrors repro-safe-doc-push-extreme-stash-
  # rename-drop.sh's own setup), so recreate it here too rather than relying on setup() ordering.
  mkdir -p plans/archive/2026_08
  git mv plans/active/thing.md plans/archive/2026_08/thing.md

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs(plans): archive thing.md" \
    --files "plans/active/thing.md plans/archive/2026_08/thing.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  # The pre-fix failure signature must never appear -- this proves the fix actually engaged,
  # not merely that some other path happened to route around it.
  [[ "$output" != *"did not match any files"* ]]
  [[ "$output" != *"could not stage named files"* ]]

  # Ground truth on the bare origin, not the script's own claims.
  run git -C "${WORK}/origin.git" cat-file -e "live-defi-rollout:plans/archive/2026_08/thing.md"
  [ "$status" -eq 0 ]
  run git -C "${WORK}/origin.git" cat-file -e "live-defi-rollout:plans/active/thing.md"
  [ "$status" -ne 0 ]
}

@test "a rename bundled with an unrelated sibling edit in the same --files call lands both" {
  mkdir -p plans/archive/2026_08
  git mv plans/active/thing.md plans/archive/2026_08/thing.md
  echo "sibling content -- edited" > plans/active/sibling.md

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs(plans): archive thing.md + edit sibling" \
    --files "plans/active/thing.md plans/archive/2026_08/thing.md plans/active/sibling.md"

  [ "$status" -eq 0 ]
  [[ "$output" != *"did not match any files"* ]]

  run git -C "${WORK}/origin.git" show "live-defi-rollout:plans/active/sibling.md"
  [ "$status" -eq 0 ]
  [ "$output" = "sibling content -- edited" ]
  run git -C "${WORK}/origin.git" cat-file -e "live-defi-rollout:plans/archive/2026_08/thing.md"
  [ "$status" -eq 0 ]
  run git -C "${WORK}/origin.git" cat-file -e "live-defi-rollout:plans/active/thing.md"
  [ "$status" -ne 0 ]
}

@test "an ordinary tracked-but-missing deletion (no rename) is unaffected -- still stages and lands" {
  # Not a git-mv: the file stays TRACKED in the index, just missing from disk. This is the shape
  # reassert_renames / git's own default deletion-staging behaviour already handled correctly --
  # the new goneless-skip filter must not swallow it too.
  rm -f plans/active/thing.md

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs(plans): remove thing.md" \
    --files "plans/active/thing.md"

  [ "$status" -eq 0 ]
  run git -C "${WORK}/origin.git" cat-file -e "live-defi-rollout:plans/active/thing.md"
  [ "$status" -ne 0 ]
}
