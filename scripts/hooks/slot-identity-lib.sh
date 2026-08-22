#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# slot-identity-lib.sh — the SINGLE derivation of `<canon> [<label>·<host>]` commit identity.
#
# Sourced by BOTH the fail-closed pre-commit hook (fix-commit-identity.sh) and the
# per-host checker (scripts/dev/check-slot-commit-identity.sh) so the expected-identity
# rule can never drift between enforcement and audit (ao_task_lifecycle plan Phase D,
# 2026-07-09). SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Commit attribution".
#
# Contract:
#   slot_identity_resolve <repo-toplevel-path>
#     → sets SLOT_ID_CANON_NAME, SLOT_ID_CANON_EMAIL, SLOT_ID_LABEL, SLOT_ID_HOST,
#       SLOT_ID_EXPECTED_NAME
#
# Label derivation is PATH-based: `…/.tabs/<N>/<repo>` → slot-<N>; anything else →
# main. The pre-2026-07-09 branch-based rule (`tab/<op>/<N>` → slot-N) is RETIRED with
# the tab-branch model — Path-B slot clones sit on live-defi-rollout, so it resolved
# "main" in EVERY slot and actively REWROTE correct stamped identities away (the
# fleet-wide missing-slot-number bug).

# Canonical per-host identity (per-operator). Resolution order (host-stable + readable
# from a per-repo pre-commit hook):
#   1. env override            SLOT_CANON_EMAIL / SLOT_CANON_NAME
#   2. per-machine git config  `git config --global slotIdentity.email` / `slotIdentity.name`
#   3. fleet default           ikennaigboaka@gmail.com / ikennaigboaka  (VMs + Ikenna laptop)
# A non-Ikenna host declares itself ONCE (e.g. Harsh's laptop):
#   git config --global slotIdentity.email "harshkantariya@odum-research.com"
#   git config --global slotIdentity.name  "harshkantariya"
slot_identity_resolve() {
  local top="${1:-}"
  if [ -z "$top" ]; then
    top="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
  fi

  SLOT_ID_CANON_EMAIL="${SLOT_CANON_EMAIL:-$(git config --global slotIdentity.email 2>/dev/null || true)}"
  SLOT_ID_CANON_EMAIL="${SLOT_ID_CANON_EMAIL:-ikennaigboaka@gmail.com}"
  SLOT_ID_CANON_NAME="${SLOT_CANON_NAME:-$(git config --global slotIdentity.name 2>/dev/null || true)}"
  SLOT_ID_CANON_NAME="${SLOT_ID_CANON_NAME:-ikennaigboaka}"
  # Canon sanitization (2026-07-09 live finding): the planning VM's global
  # slotIdentity.name had been polluted with a label ("ikennaigboaka
  # [slot-0·human-planning]") — every hook rewrite then CONCATENATED another
  # label onto it ("… [slot-0·human-planning] [main·laptop]"). Canon is the bare
  # handle by definition; strip any " [label·host]" suffix defensively.
  SLOT_ID_CANON_NAME="${SLOT_ID_CANON_NAME%% [*}"

  # PATH-based slot label: …/.tabs/<N>/<repo> → slot-<N>; else main.
  local slot
  slot="$(printf '%s' "$top" | sed -nE 's#.*/\.tabs/([0-9]+)/[^/]+$#\1#p')"
  if [ -n "$slot" ]; then SLOT_ID_LABEL="slot-${slot}"; else SLOT_ID_LABEL="main"; fi

  # Host: a fleet VM advertises ORCHESTRATOR_VM_ID (canonical short registry id),
  # VM_NAME as fallback — but those are PROCESS env, absent in interactive shells
  # on the same VM (observed: interactive commits on the planning VM stamped
  # ·laptop). A machine declares its host label ONCE via git config --global
  # slotIdentity.host (e.g. "planning"); env still wins for fleet processes.
  # Final fallback: laptop.
  SLOT_ID_HOST="${ORCHESTRATOR_VM_ID:-${VM_NAME:-$(git config --global slotIdentity.host 2>/dev/null || true)}}"
  SLOT_ID_HOST="${SLOT_ID_HOST:-laptop}"

  SLOT_ID_EXPECTED_NAME="${SLOT_ID_CANON_NAME} [${SLOT_ID_LABEL}·${SLOT_ID_HOST}]"
}
