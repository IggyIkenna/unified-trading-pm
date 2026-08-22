#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Regression tests for `_qg_repo_name()` in qg-host-governor.sh — closes
# plans/active/issues/qg_governor_repo_bucketing_falls_back_to_slot_number_2026_08_09.md.
#
# Bug this guards against: `_qg_repo_name()` used to derive the per-repo governor
# bucket key from the caller-populated PROJECT_ROOT/REPO_ROOT env vars. When
# PROJECT_ROOT wasn't populated yet at call time (observed live, sourcing-order gap
# not fully traced) it fell back to REPO_ROOT — this codebase's confusingly-named
# convention for ONE LEVEL ABOVE the repo, i.e. the `.tabs/<slot>` workspace dir —
# whose basename is just the slot NUMBER (e.g. "2"). Two different repos checked out
# under the SAME slot then bucketed under the SAME key, colliding under the per-repo
# sub-cap (cap=1 for every non-PM repo) and starving each other forever even after the
# true competing process had exited.
#
# The fix derives the bucket key from git directly (remote origin URL, or working-tree
# toplevel as a fallback) — it needs no caller-populated env var at all, so it is
# immune to slot number, worktree nesting, AND call-time env-var population order.
# These tests simulate exactly the reported failure condition (PROJECT_ROOT unset /
# PROJECT_ROOT+REPO_ROOT both poisoned to a shared slot-like path) and assert the
# derived name is still correct and two different repos never collide.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-repo-name-slot-agnostic.sh
set -uo pipefail

GOV="$(cd "$(dirname "$0")/.." && pwd)/qg-host-governor.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAILS=0
eq() { if [[ "$2" == "$3" ]]; then echo "PASS: $1 ($3)"; else echo "FAIL: $1 — expected '$2' got '$3'"; FAILS=$((FAILS + 1)); fi; }

# ── fixture repos — two throwaway git repos with DIFFERENT origin remotes, both
#    nested under a SHARED parent dir named "2" (mirrors the real `.tabs/2/<repo>`
#    layout that produced the live collision) ─────────────────────────────────────
SLOT_DIR="$TMP/2"
REPO_A="$SLOT_DIR/market-tick-data-service"
REPO_B="$SLOT_DIR/deployment-service"
mkdir -p "$REPO_A" "$REPO_B"
git -C "$REPO_A" init -q
git -C "$REPO_A" remote add origin "git@github.com:IggyIkenna/market-tick-data-service.git"
git -C "$REPO_B" init -q
git -C "$REPO_B" remote add origin "git@github.com:IggyIkenna/deployment-service.git"

# ── (1) baseline: correct name from within each repo, no env vars poisoned ───────
NAME_A="$(cd "$REPO_A" && bash -c "source '$GOV'; _qg_repo_name")"
NAME_B="$(cd "$REPO_B" && bash -c "source '$GOV'; _qg_repo_name")"
eq "repo A resolves to its own git identity" "market-tick-data-service" "$NAME_A"
eq "repo B resolves to its own git identity" "deployment-service" "$NAME_B"
eq "repo A and repo B never collide (baseline)" "false" "$([[ "$NAME_A" == "$NAME_B" ]] && echo true || echo false)"

# ── (2) THE ORIGINAL BUG, reproduced: PROJECT_ROOT unset (not "populated yet" —
#    the exact reported failure) — must NOT fall through to any slot-scoped value ──
NAME_A_NOPROJROOT="$(cd "$REPO_A" && env -u PROJECT_ROOT -u REPO_ROOT bash -c "source '$GOV'; _qg_repo_name")"
eq "PROJECT_ROOT unset: still resolves to the real repo name" "market-tick-data-service" "$NAME_A_NOPROJROOT"
eq "PROJECT_ROOT unset: does NOT fall back to the slot number" "false" "$([[ "$NAME_A_NOPROJROOT" == "2" ]] && echo true || echo false)"

# ── (3) THE EXACT COLLISION, reproduced: PROJECT_ROOT AND REPO_ROOT both POISONED
#    to the shared slot dir (what REPO_ROOT resolves to in the real per-tab layout) —
#    two different repos must still resolve to two DIFFERENT names, never both "2" ──
NAME_A_POISONED="$(cd "$REPO_A" && bash -c "export PROJECT_ROOT='$SLOT_DIR' REPO_ROOT='$SLOT_DIR'; source '$GOV'; _qg_repo_name")"
NAME_B_POISONED="$(cd "$REPO_B" && bash -c "export PROJECT_ROOT='$SLOT_DIR' REPO_ROOT='$SLOT_DIR'; source '$GOV'; _qg_repo_name")"
eq "poisoned PROJECT_ROOT/REPO_ROOT: repo A still resolves correctly" "market-tick-data-service" "$NAME_A_POISONED"
eq "poisoned PROJECT_ROOT/REPO_ROOT: repo B still resolves correctly" "deployment-service" "$NAME_B_POISONED"
eq "poisoned PROJECT_ROOT/REPO_ROOT: A and B never collide under the slot number" "false" \
    "$([[ "$NAME_A_POISONED" == "$NAME_B_POISONED" ]] && echo true || echo false)"
eq "poisoned case never buckets under the bare slot number \"2\"" "false" \
    "$([[ "$NAME_A_POISONED" == "2" || "$NAME_B_POISONED" == "2" ]] && echo true || echo false)"

# ── (4) nested worktree — a worktree of repo A must resolve to repo A's OWN name,
#    not its own worktree-directory basename (git worktrees share the parent's
#    remotes; a hash/branch-named worktree dir must not look like a different repo) ─
git -C "$REPO_A" commit -q --allow-empty -m "init" 2>/dev/null || true
WT_DIR="$SLOT_DIR/wt-hash-abc123"
if git -C "$REPO_A" worktree add -q -b "wt-test-branch" "$WT_DIR" >/dev/null 2>&1; then
    NAME_WT="$(cd "$WT_DIR" && bash -c "source '$GOV'; _qg_repo_name")"
    eq "worktree of repo A resolves to repo A's identity, not its own dir name" "market-tick-data-service" "$NAME_WT"
else
    echo "SKIP: worktree fixture unavailable in this git version (non-fatal)"
fi

# ── (5) graceful degradation: no origin remote → falls back to toplevel basename ──
REPO_C="$SLOT_DIR/no-origin-repo"
mkdir -p "$REPO_C"
git -C "$REPO_C" init -q
NAME_C="$(cd "$REPO_C" && bash -c "source '$GOV'; _qg_repo_name")"
eq "no origin remote: falls back to working-tree toplevel basename" "no-origin-repo" "$NAME_C"

# ── (6) graceful degradation: not a git tree at all → falls back to PROJECT_ROOT ──
PLAIN_DIR="$TMP/plain-non-git-dir"
mkdir -p "$PLAIN_DIR"
NAME_PLAIN="$(cd "$PLAIN_DIR" && bash -c "export PROJECT_ROOT='/some/fake/repo-x'; source '$GOV'; _qg_repo_name")"
eq "not a git tree: falls back to PROJECT_ROOT basename" "repo-x" "$NAME_PLAIN"

echo "────────────────────────────────────────"
if [[ "$FAILS" -eq 0 ]]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[[ "$FAILS" -eq 0 ]]
