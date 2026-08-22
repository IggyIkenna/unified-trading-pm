#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# qg-environment.sh — single source of truth for the branch-conditional ENVIRONMENT
# default, shared by quickmerge.sh AND a standalone quality-gates.sh run (via
# qg-common.sh).
#
# Bug this closes (qg_sentinel_environment_blind_2026_07_23.md item 5): quickmerge.sh
# always resolved ENVIRONMENT=development for any non-main branch (every slot, since
# every slot lives on live-defi-rollout), while a standalone `quality-gates.sh` run left
# ENVIRONMENT unset and downstream resolvers (e.g. UTL's bucket_naming.py) default to
# prod — a silent divergence between the two invocation paths for the SAME tree. Before
# this fix, the two branch-conditional checks were two independently-authored inline
# copies that could (and did) drift apart. Sourcing this ONE file from both call sites
# means there is exactly one branch-check to keep correct.
#
# Deliberately does NOT broaden the branch check itself (main-only vs a wider
# release-branch set) — that is a separate, deferred design question
# (quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md).
#
# Provides: qg_resolve_environment([dir]) — sets/exports ENVIRONMENT if not already
# set. `dir` (default ".") is the git worktree to read the current branch from; pass it
# explicitly when the caller's cwd isn't yet the target repo (e.g. qg-common.sh, which
# resolves PROJECT_ROOT before cwd actually changes there).
qg_resolve_environment() {
    # An explicit caller override (PROD_FLAG-independent — ENVIRONMENT set via .env,
    # shell export, etc.) always wins; never clobber it.
    [ -n "${ENVIRONMENT:-}" ] && return 0
    # CI resolves its own environment posture per-workflow already, and the
    # quality-gates-v2 QG_SLICE-sliced runs never touch the sentinel this fix protects
    # (see .github/workflows/python-quality-gates-v2.yml § SENTINEL) — never override
    # CI's ambient ENVIRONMENT. This function exists for the LOCAL/agent
    # standalone-vs-quickmerge divergence only.
    [ "${GITHUB_ACTIONS:-}" = "true" ] && return 0
    local _qg_branch
    _qg_branch=$(git -C "${1:-.}" branch --show-current 2>/dev/null || echo "main")
    if [ "$_qg_branch" = "main" ] || [ "${PROD_FLAG:-false}" = "true" ]; then
        export ENVIRONMENT="production"
    else
        export ENVIRONMENT="development"
    fi
}
