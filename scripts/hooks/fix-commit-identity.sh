#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# fix-commit-identity.sh — enforce slot+host commit attribution per worktree.
#
# Problem this solves: ~24/25 per-tab worktrees carried a WRONG git author email
# (the `semver-rollout[bot]` email or `agent@ci.local`), so agent commits masqueraded
# as the bot / were unattributed; and the author name was bare `ikennaigboaka`, so CI
# alerts + cross-agent triage could not tell WHICH slot/host produced a commit.
#
# Mechanism: git resolves the commit author BEFORE pre-commit hooks run, so this hook
# CANNOT silently fix the current commit. It is FAIL-CLOSED — on a wrong identity it
# self-heals the per-worktree config and BLOCKS the commit; the re-commit then lands
# with the correct author. When the identity is already correct it is a silent no-op.
#
# Per-worktree config is REQUIRED: `.tabs/<N>/<repo>` are git worktrees sharing the main
# clone's `.git/config`, so plain `git config user.name` is shared across all slots
# (last-writer-wins). We use `extensions.worktreeConfig` + `git config --worktree`.
#
# SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Commit attribution".
set -uo pipefail

# 1) Never enforce in CI — semver-agent + CI runners legitimately commit under their own
#    identity (e.g. the semver-rollout[bot]). The slot/host scheme is for human+agent
#    worktrees only.
if [ -n "${CI:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ]; then
  exit 0
fi

# 2+3) Expected identity — canon (per-operator), label (PATH-based slot-N, ao_task_lifecycle
#      Phase D 2026-07-09: the old tab/<op>/<N> BRANCH derivation is RETIRED — Path-B slots sit
#      on live-defi-rollout, so it resolved "main" in EVERY slot and actively REWROTE correct
#      stamped identities away), host (ORCHESTRATOR_VM_ID → VM_NAME → laptop). Derivation SSOT
#      is the sourced lib — shared verbatim with scripts/dev/check-slot-commit-identity.sh so
#      enforcement and audit can never drift.
# shellcheck source=scripts/hooks/slot-identity-lib.sh
. "$(dirname "${BASH_SOURCE[0]}")/slot-identity-lib.sh"
slot_identity_resolve "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CANON_EMAIL="$SLOT_ID_CANON_EMAIL"
CANON_NAME="$SLOT_ID_CANON_NAME"
exp_name="$SLOT_ID_EXPECTED_NAME"
cur_name="$(git config user.name 2>/dev/null || echo '')"
cur_email="$(git config user.email 2>/dev/null || echo '')"

# 4) Already correct → silent fast no-op (the steady state once provisioned).
if [ "$cur_name" = "$exp_name" ] && [ "$cur_email" = "$CANON_EMAIL" ]; then
  exit 0
fi

# 5) Wrong → self-heal the per-worktree identity (binds the NEXT commit) + block this one.
git config extensions.worktreeConfig true 2>/dev/null || true
git config --worktree user.name "$exp_name" 2>/dev/null || git config user.name "$exp_name"
git config --worktree user.email "$CANON_EMAIL" 2>/dev/null || git config user.email "$CANON_EMAIL"

echo "⚠️  commit identity was '${cur_name} <${cur_email}>'." >&2
echo "    Corrected to '${exp_name} <${CANON_EMAIL}>' for THIS worktree (git config --worktree)." >&2
echo "    git resolves the author BEFORE this hook, so just RE-RUN your commit — it will land correctly." >&2
exit 1
