#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test: safe-doc-push isolated-worktree mode preserves the CALLER's slot identity
# (safe_doc_push_isolation_rewrites_slot_commit_identity_2026_08_10.md, confirmed live slot 31).
#
# THE BUG: the isolated commit worktree lives at $TMPDIR/sdp-iso-$$/unified-trading-pm — a path
# with no `.tabs/<N>/` segment — so fix-commit-identity.sh's PATH-derived label resolves `main`
# and actively REWRITES a slot worker's correct `[slot-N·host]` author to `[main·host]`.
#
# THE FIX: before the inner re-exec, resolve the caller's identity against the CALLER repo path
# (scripts/hooks/slot-identity-lib.sh) and pre-stamp the isolated worktree's git config, so the
# commit author carries the caller's `[slot-N·host]` label and the hook no-ops (first-attempt
# commit with correct attribution).
#
# NOTE on verification: the push updates origin (and the caller's origin/<branch> tracking ref),
# NOT the caller's local branch ref, so we assert against the PUSHED commit's author.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"

  WORK="${BATS_TEST_TMPDIR}"
  # Caller checkout lives at a `.tabs/<N>/` path so slot_identity_resolve derives `slot-29`.
  git init -q --bare "${WORK}/origin.git"
  mkdir -p "${WORK}/.tabs/29"
  git clone -q "${WORK}/origin.git" "${WORK}/.tabs/29/unified-trading-pm"
  cd "${WORK}/.tabs/29/unified-trading-pm"
  git config user.email "test@example.com"
  git config user.name "test"
  git checkout -q -B live-defi-rollout
  echo "initial" > README.md
  git add README.md
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout

  # Fast retry backoff.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"

  # Deterministic identity so the expected author is fixed: canon overrides + host.
  export SLOT_CANON_NAME="test"
  export SLOT_CANON_EMAIL="test@example.com"
  export ORCHESTRATOR_VM_ID="planning"
}

@test "isolated-worktree mode preserves the caller's slot-29 identity (not main)" {
  cd "${WORK}/.tabs/29/unified-trading-pm"
  echo "content" > plan.md

  # SDP_ISOLATED=1 is REQUIRED, not incidental. setup() exports ORCHESTRATOR_VM_ID=planning to
  # pin the host label in the expected author string, and isolation now defaults OFF on a named
  # VM — so without this the test quietly stopped exercising isolated mode at all while still
  # claiming to (caught 2026-08-10, the same day the host gate landed).
  PATH="${WORK}/bin:$PATH" SDP_ISOLATED=1 run bash "$SCRIPT" "docs(plans): identity propagation regression" --files "plan.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  # Proves isolation actually engaged; the author assertion below is meaningless otherwise.
  [[ "$output" == *"isolated-worktree mode"* ]]
  # The push updates origin, not the caller's local branch — read the PUSHED commit's author.
  run git ls-remote "${WORK}/origin.git" live-defi-rollout
  pushed_sha="${lines[0]%%$'\t'*}"
  run git show --format='%an <%ae>' --no-patch "$pushed_sha"
  [ "$output" = "test [slot-29·planning] <test@example.com>" ]
}
