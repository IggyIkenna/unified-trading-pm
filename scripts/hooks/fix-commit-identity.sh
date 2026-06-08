#!/usr/bin/env bash
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

# Canonical per-host identity (per-operator). The GitHub-attributed email + name handle DIFFER
# per operator (Ikenna `ikennaigboaka@gmail.com` vs Harsh `harshkantariya@odum-research.com`), so
# they MUST NOT be hardcoded — a hardcoded constant rewrote every non-Ikenna slot's commits to
# Ikenna's identity (the bug that made Harsh's verify-slot-host-symmetry step 4 unachievable).
# Resolution order (host-stable + readable from this per-repo pre-commit hook):
#   1. env override            SLOT_CANON_EMAIL / SLOT_CANON_NAME
#   2. per-machine git config   `git config --global slotIdentity.email` / `slotIdentity.name`
#   3. fleet default            ikennaigboaka@gmail.com / ikennaigboaka  (VMs + Ikenna laptop)
# A non-Ikenna host declares itself ONCE (Harsh's laptop):
#   git config --global slotIdentity.email "harshkantariya@odum-research.com"
#   git config --global slotIdentity.name  "harshkantariya"
# SSOT: CLAUDE.md § "Commit attribution" + codex/05-infrastructure/per-tab-worktrees.md.
CANON_EMAIL="${SLOT_CANON_EMAIL:-$(git config --global slotIdentity.email 2>/dev/null || true)}"
CANON_EMAIL="${CANON_EMAIL:-ikennaigboaka@gmail.com}"
CANON_NAME="${SLOT_CANON_NAME:-$(git config --global slotIdentity.name 2>/dev/null || true)}"
CANON_NAME="${CANON_NAME:-ikennaigboaka}"

# 2) Derive the EXPECTED label: slot-<N> from a tab/<op>/<N> branch, else "main".
#    `symbolic-ref --short` resolves the branch name even on an unborn branch (no commits yet),
#    where `rev-parse --abbrev-ref` would return the literal "HEAD".
branch="$(git symbolic-ref --short HEAD 2>/dev/null || git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '')"
slot="$(printf '%s' "$branch" | sed -nE 's#^tab/[^/]+/([0-9]+)$#\1#p')"
if [ -n "$slot" ]; then label="slot-${slot}"; else label="main"; fi

# 3) Derive host: a fleet VM advertises ORCHESTRATOR_VM_ID (the canonical short registry id,
#    e.g. vm-cefi — same value bootstrap_vm.sh brands the tab branch prefix with), with VM_NAME
#    as a fallback; else this is a laptop. ORCHESTRATOR_VM_ID-first keeps the commit host in
#    agreement with the branch prefix (setup-tab-worktrees.sh resolves both the same way).
host="${ORCHESTRATOR_VM_ID:-${VM_NAME:-laptop}}"

exp_name="${CANON_NAME} [${label}·${host}]"
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
