#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for scripts/dev/auto-reconcile-starved-repo.sh, built from the manual reconcile
# session (2026-08-19) that fixed slots 4/5/6's starved unified-trading-pm clones and, in doing
# so, satisfies the open repro todo in
# plans/active/issues/git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md
# ("attempt a clean repro of the stash-pathspec-staleness / silent-loss defect in a scratch
# repo"). Covers, against real local origin/clone pairs (mirrors
# test_safe_doc_push_landed_content_certification.bats's pattern):
#   - the happy path: a starved, colliding-but-non-overlapping dirty file reconciles silently,
#     content from BOTH sides verified present afterward.
#   - the exact bug class found live in slot 6: a dirty file that ALREADY carries raw conflict
#     markers from an earlier, unrelated stash cycle is declined outright, untouched (HEAD does
#     not move), rather than layering another automated cycle on top of already-broken content.
#   - the liveness gate (both halves: a live matching process, and a just-committed HEAD),
#     unit-tested directly against the fixed functions (same harness style as
#     test_slot_cron_ff_pull_venv_resync_liveness.bats).
#   - the content-integrity checker in isolation: content that survives, content that a bug would
#     have silently dropped, and a pure-deletion diff that has nothing to verify.
#   - a not-starved repo produces no output at all (nothing to reconcile, nothing to report).
#
# Run: bats tests/test_auto_reconcile_starved_repo.bats

setup() {
    REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    SCRIPT="${REPO_ROOT}/scripts/dev/auto-reconcile-starved-repo.sh"
    [ -f "$SCRIPT" ]
    WORK="${BATS_TEST_TMPDIR}"
}

# Builds an origin/clone pair on live-defi-rollout with doc.md="line1\nline2\n" committed+pushed,
# and sets upstream tracking (auto-reconcile-starved-repo.sh shells out to
# ff-starvation-detect.sh, which reads origin/<branch> directly — no @{upstream} dependency, but
# tracking is set anyway to mirror a real slot clone).
make_origin_and_clone() {
    git init -q --bare "${WORK}/origin.git"
    git clone -q "${WORK}/origin.git" "${WORK}/clone"
    ( cd "${WORK}/clone" \
        && git config user.email "test@example.com" \
        && git config user.name "test" \
        && git checkout -q -B live-defi-rollout \
        && printf 'line1\nline2\n' > doc.md \
        && git add doc.md \
        && GIT_AUTHOR_DATE="2020-01-01T00:00:00" GIT_COMMITTER_DATE="2020-01-01T00:00:00" \
           git commit -q -m "init" \
        && git push -q origin HEAD:live-defi-rollout \
        && git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout )
}

# Pushes a commit to origin from a SEPARATE clone (never touches $WORK/clone's working tree),
# simulating a peer slot landing work while our clone sits dirty. Appends "peer line" to doc.md.
push_peer_commit_touching_doc() {
    git clone -q "${WORK}/origin.git" "${WORK}/peer"
    ( cd "${WORK}/peer" \
        && git config user.email "peer@example.com" \
        && git config user.name "peer" \
        && git checkout -q -B live-defi-rollout origin/live-defi-rollout \
        && printf 'line1\nline2\npeer line\n' > doc.md \
        && git add doc.md \
        && git commit -q -m "peer: append" \
        && git push -q origin HEAD:live-defi-rollout )
}

@test "happy path: starved + colliding-but-non-overlapping dirty file reconciles silently, both sides survive" {
    make_origin_and_clone
    cd "${WORK}/clone"
    # Local dirty edit at the TOP of the file -- the peer commit below touches the BOTTOM, so git's
    # own 3-way merge resolves this cleanly (file-level collision, line-level clean -- exactly the
    # shape ao_ci_aws_to_ionos_migration.md / client_artefact_remediation_nickai.md hit in slot 6).
    printf 'my local addition\nline1\nline2\n' > doc.md

    push_peer_commit_touching_doc

    run env FF_STARVE_COMMIT_THRESHOLD=1 FF_STARVE_AGE_HOURS=0 \
        bash "$SCRIPT" "${WORK}/clone" --branch live-defi-rollout --slot 99 \
        --workspace "${WORK}"

    [ "$status" -eq 0 ]
    [ -z "$output" ]   # silent success -- caller must NOT page on this

    # "my local addition" was genuinely new, uncommitted content -- it must remain as WIP on top
    # (recover-on-top, never auto-commit), so the tree is expected to still show it as dirty.
    run git -C "${WORK}/clone" diff --stat
    [[ "$output" == *"doc.md"* ]]

    run cat "${WORK}/clone/doc.md"
    [[ "$output" == *"my local addition"* ]]   # ours survived
    [[ "$output" == *"peer line"* ]]           # theirs arrived

    run git -C "${WORK}/clone" log --oneline -1 --format=%H origin/live-defi-rollout
    peer_head="$output"
    run git -C "${WORK}/clone" merge-base --is-ancestor "$peer_head" HEAD
    [ "$status" -eq 0 ]   # HEAD really did advance past the peer's push, not just look clean
}

@test "a file with PRE-EXISTING conflict markers is declined, not touched -- HEAD does not move" {
    make_origin_and_clone
    cd "${WORK}/clone"
    # Simulate the exact slot-6 shape: an earlier, unrelated stash cycle left raw markers baked
    # into a dirty tracked file, uncommitted, long before this script ever runs.
    cat > doc.md <<'EOF'
line1
<<<<<<< Updated upstream
resolved one way
||||||| Stash base
original
=======
resolved the OTHER way
>>>>>>> Stashed changes
line2
EOF
    git add doc.md   # staged dirt is enough to make the repo "dirty" for the starve detector

    push_peer_commit_touching_doc
    head_before="$(git rev-parse HEAD)"

    run env FF_STARVE_COMMIT_THRESHOLD=1 FF_STARVE_AGE_HOURS=0 \
        bash "$SCRIPT" "${WORK}/clone" --branch live-defi-rollout --slot 99 \
        --workspace "${WORK}"

    [ "$status" -eq 0 ]
    [[ "$output" == *"AUTO-RECONCILE: declined"* ]]
    [[ "$output" == *"pre-existing"* ]]
    [[ "$output" == *"doc.md"* ]]

    head_after="$(git -C "${WORK}/clone" rev-parse HEAD)"
    [ "$head_before" = "$head_after" ]   # never fetched/merged -- declined before any git mutation
    run git -C "${WORK}/clone" diff --cached
    [[ "$output" == *"<<<<<<< Updated upstream"* ]]   # the broken content is exactly as we left it
}

@test "not starved -> no output at all" {
    make_origin_and_clone
    run bash "$SCRIPT" "${WORK}/clone" --branch live-defi-rollout --workspace "${WORK}"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "the script still parses" {
    run bash -n "$SCRIPT"
    [ "$status" -eq 0 ]
}

# ── unit tests: liveness gate, both halves, via the lib-only sourcing harness (mirrors
#    test_slot_cron_ff_pull_venv_resync_liveness.bats's own style) ──────────────────────────────

run_liveness_check() {
    # $1 = repo dir, $2 = "pid:cwd pid:cwd ..." to stub pgrep/_cwd_of with (empty = no candidates)
    local repo_dir="$1" pid_cwd_map="$2"
    local harness="${BATS_TEST_TMPDIR}/liveness_harness.sh"
    {
        echo "AUTO_RECONCILE_LIB_ONLY=1"
        echo "source '${SCRIPT}'"
        if [[ -n "${pid_cwd_map}" ]]; then
            echo "pgrep() { printf '%s\n' $(printf '%s' "$pid_cwd_map" | awk '{for(i=1;i<=NF;i++){split($i,a,":");printf "%s ", a[1]}}'); }"
            echo "_cwd_of() {"
            echo "  case \"\$1\" in"
            for pair in $pid_cwd_map; do
                local pid="${pair%%:*}" cwd="${pair#*:}"
                echo "    ${pid}) printf '%s' '${cwd}' ;;"
            done
            echo "  esac"
            echo "}"
        else
            echo "pgrep() { return 1; }"
        fi
        echo "if _is_live_in_repo '${repo_dir}'; then echo LIVE; else echo NOT_LIVE; fi"
    } > "$harness"
    bash "$harness"
}

@test "liveness gate: a stubbed process whose exact cwd matches the repo triggers LIVE" {
    make_origin_and_clone
    run run_liveness_check "${WORK}/clone" "111:${WORK}/clone"
    [[ "$output" == *"LIVE"* ]]
    [[ "$output" != *"NOT_LIVE"* ]]
}

@test "liveness gate: a stubbed process in a sibling dir sharing a path prefix does NOT trigger" {
    make_origin_and_clone
    mkdir -p "${WORK}/clone-other"
    run run_liveness_check "${WORK}/clone" "111:${WORK}/clone-other"
    [[ "$output" == *"NOT_LIVE"* ]]
}

@test "liveness gate: a HEAD commit seconds ago triggers LIVE via the recency half, no process needed" {
    make_origin_and_clone
    cd "${WORK}/clone"
    printf 'line1\nline2\nfresh\n' > doc.md
    git commit -q -am "just now"
    run run_liveness_check "${WORK}/clone" ""
    [[ "$output" == *"LIVE"* ]]
}

@test "liveness gate: no process and an old HEAD -> NOT_LIVE" {
    make_origin_and_clone
    run run_liveness_check "${WORK}/clone" ""
    [[ "$output" == *"NOT_LIVE"* ]]
}

# ── unit tests: content-integrity checker in isolation ─────────────────────────────────────────

run_integrity_check() {
    # $1 = repo dir, $2 = patch file, $3 = repo-relative path
    local harness="${BATS_TEST_TMPDIR}/integrity_harness.sh"
    {
        echo "AUTO_RECONCILE_LIB_ONLY=1"
        echo "source '${SCRIPT}'"
        echo "_check_content_integrity '$1' '$2' '$3'"
    } > "$harness"
    bash "$harness"
}

@test "content-integrity: an added line that survives in the current file is OK" {
    mkdir -p "${WORK}/repo"
    printf 'header\nmy genuine addition that is long enough to count\nfooter\n' > "${WORK}/repo/doc.md"
    cat > "${WORK}/patch.diff" <<'EOF'
diff --git a/doc.md b/doc.md
index 1111111..2222222 100644
--- a/doc.md
+++ b/doc.md
@@ -1,2 +1,3 @@
 header
+my genuine addition that is long enough to count
 footer
EOF
    run run_integrity_check "${WORK}/repo" "${WORK}/patch.diff" "doc.md"
    [ "$status" -eq 0 ]
    [[ "$output" == OK* ]]
}

@test "content-integrity: an added line ABSENT from the current file is flagged SUSPECTED_LOSS (the slot-6 bug class)" {
    mkdir -p "${WORK}/repo"
    # Current file reverted to the stale/pre-fix content -- exactly what slot 6's autostash pop
    # silently produced (the annotation from the patch never made it in).
    printf 'header\nfooter\n' > "${WORK}/repo/doc.md"
    cat > "${WORK}/patch.diff" <<'EOF'
diff --git a/doc.md b/doc.md
index 1111111..2222222 100644
--- a/doc.md
+++ b/doc.md
@@ -1,2 +1,3 @@
 header
+RESOLVED + archived 2026-08-18 annotation that must survive
 footer
EOF
    run run_integrity_check "${WORK}/repo" "${WORK}/patch.diff" "doc.md"
    [ "$status" -eq 1 ]
    [[ "$output" == SUSPECTED_LOSS* ]]
}

@test "content-integrity: a pure-deletion diff (no added lines) has nothing to verify" {
    mkdir -p "${WORK}/repo"
    printf 'header\nfooter\n' > "${WORK}/repo/doc.md"
    cat > "${WORK}/patch.diff" <<'EOF'
diff --git a/doc.md b/doc.md
index 1111111..2222222 100644
--- a/doc.md
+++ b/doc.md
@@ -1,3 +1,2 @@
 header
-a line that was only ever removed, never added
 footer
EOF
    run run_integrity_check "${WORK}/repo" "${WORK}/patch.diff" "doc.md"
    [ "$status" -eq 0 ]
    [[ "$output" == "NO_ADDED_CONTENT" ]]
}
