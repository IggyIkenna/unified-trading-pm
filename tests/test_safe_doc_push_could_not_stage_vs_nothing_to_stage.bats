#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's staging-failure wording
# (safe_doc_push_reports_success_having_committed_nothing_2026_08_09.md, todo 3).
#
# THE BUG: `git add -- "${FILES[@]}"`'s own exit code was never checked. Under index.lock
# contention (the exact incident mechanism -- a peer session's autostash sweep holding the
# lock while this script's `git add` ran), staging silently failed and the script fell
# straight into "nothing staged for the named files -- checking if content already matches
# HEAD" -- the SAME wording used for the genuinely benign case where staging succeeded but
# there was simply nothing new to add. A human (or a downstream agent trusting the log) reads
# that phrasing as "probably fine, checking a fallback" when it is actually a hard failure to
# stage at all.
#
# THE FIX: `git add`'s exit code is checked explicitly. An index.lock failure there now emits
# a distinct "could not stage named files ... HARD FAILURE" message and retries immediately,
# never reaching the ambiguous branch. Only a successful `git add` with nothing left to commit
# reaches the (now clearly-labeled) "nothing to stage ... staging completed cleanly" message.

setup() {
  # SDP_ISOLATED=0 is REQUIRED, not incidental: this suite asserts on the IN-TREE staging path
  # (it holds the CALLER repo's .git/index.lock and expects a hard failure). Isolated mode --
  # the default -- commits from a separate worktree with its OWN index, so the lock is
  # irrelevant there and the script correctly exits 0. The assertion then reads as
  # "safe-doc-push ignores a held lock", which is not what happened.
  export SDP_ISOLATED=0
  # Tests must NOT take a host-wide lock. push-host-governor.sh hands out K=8 tokens PER HOST,
  # shared with real safe-doc-push runs, so under `bats -j` these contended with each other AND
  # with a peer session's genuine push — exit codes became a function of unrelated fleet
  # activity. One run green, the next red, the failure moving between tests.
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
  echo "initial" > README.md
  git add README.md
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout

  # Fake `sleep` on PATH so the script's retry backoff is instant -- these tests care about
  # the eventual exit code and message, not real wall-clock contention.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"
}

@test "a persistent index.lock during 'git add' is reported as a hard could-not-stage failure, never the benign nothing-to-stage wording" {
  echo "brand new content" > new_doc.md
  # Reproduces the incident mechanism directly: the lock is held for the entire run, so
  # every attempt's `git add` fails.
  touch .git/index.lock

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc" --files "new_doc.md"

  rm -f .git/index.lock

  [ "$status" -ne 0 ]
  [[ "$output" == *"could not stage named files"* ]]
  [[ "$output" == *"HARD FAILURE"* ]]
  # The old unconditional wording must never appear verbatim -- it always carried the
  # "nothing staged" phrasing regardless of whether staging failed or genuinely had nothing
  # to add; the fix replaces it with a "nothing to stage" message reached only when `git add`
  # itself succeeded.
  [[ "$output" != *"nothing staged for the named files"* ]]
  run git log --oneline -- new_doc.md
  [ -z "$output" ]
}

# The two branches of the already-landed-at-entry contract (_sdp_guard_already_landed_claim,
# 2026-08-10). This case USED to exit 0 with a benign "already matches HEAD" message. It no
# longer does, and that is deliberate: when every named file is byte-identical to HEAD *at
# entry*, the script never saw a change to ship, and "a peer landed it first" is indistinguishable
# from "your edit was destroyed before we hashed it". Reporting the benign reading
# unconditionally is exactly what made a real destroyed-work case invisible. So the default is
# now a loud non-zero, and the benign reading requires the caller to assert it explicitly.
@test "already-landed-at-entry without SDP_ALLOW_NOOP fails loudly (cannot distinguish landed-by-peer from destroyed)" {
  echo "shared content" > tracked.md
  git add tracked.md
  git commit -q -m "add tracked.md"
  git push -q origin HEAD:live-defi-rollout

  # Nothing changed on disk since the commit -- staging succeeds but has nothing new to add.
  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: no-op edit" --files "tracked.md"

  [ "$status" -eq 12 ]
  [[ "$output" == *"nothing to stage for the named files"* ]]
  [[ "$output" == *"NOTHING OF YOURS SHIPPED"* ]]
  # It must name BOTH readings rather than picking one -- that is the whole point of the guard.
  [[ "$output" == *"landed your identical content"* ]]
  [[ "$output" == *"reverted before this script hashed it"* ]]
  [[ "$output" != *"could not stage named files"* ]]
}

@test "already-landed-at-entry WITH SDP_ALLOW_NOOP=1 is a deliberate idempotent re-run and exits 0" {
  echo "shared content" > tracked.md
  git add tracked.md
  git commit -q -m "add tracked.md"
  git push -q origin HEAD:live-defi-rollout

  SDP_ALLOW_NOOP=1 PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: no-op edit" --files "tracked.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"deliberate idempotent re-run"* ]]
  [[ "$output" != *"could not stage named files"* ]]
}

@test "could-not-stage and nothing-to-stage produce distinct exit codes for the same script" {
  # could-not-stage: persistent index.lock on a brand-new file -- must not succeed.
  echo "brand new content" > new_doc.md
  touch .git/index.lock
  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc" --files "new_doc.md"
  rm -f .git/index.lock
  stage_fail_status="$status"

  # already-landed-at-entry: must fail loudly (exit 12), NOT succeed silently.
  echo "shared content" > tracked.md
  git add tracked.md
  git commit -q -m "add tracked.md"
  git push -q origin HEAD:live-defi-rollout
  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: no-op edit" --files "tracked.md"
  nothing_to_stage_status="$status"

  # Both are non-zero now, but they must remain DISTINCT: could-not-stage is an infrastructure
  # failure (the index was unwritable), already-landed-at-entry is "nothing of yours shipped and
  # I cannot tell you why". Collapsing them to one code would lose exactly the distinction the
  # caller needs to decide whether to recover work or simply retry.
  [ "$stage_fail_status" -ne 0 ]
  [ "$nothing_to_stage_status" -eq 12 ]
  [ "$stage_fail_status" -ne "$nothing_to_stage_status" ]
}
