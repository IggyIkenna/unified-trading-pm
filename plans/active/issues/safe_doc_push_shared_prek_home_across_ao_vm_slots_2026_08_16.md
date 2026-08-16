---
doc_type: issue
title: >-
  safe-doc-push.sh's PREK_HOME is only ever slot-scoped inside isolated-worktree mode — the AO VM's own host gate
  deliberately disables that mode for every slot, so every slot on `planning` shares ONE host-global
  `~/.cache/prek/patches/` dir, confirmed root cause of the cross-slot "orphaned patch" false-attributions
summary: >-
  Root-caused per the todo in `safe_doc_push_cross_slot_prek_patch_orphans_completed_fix_2026_08_16.md`: whether
  slot-16's recovery of a "slot-14"-attributed patch was a genuine cross-slot PREK_HOME leak or a same-slot
  explanation. Confirmed with direct evidence (not guessed): `scripts/dev/safe-doc-push.sh` only ever sets `PREK_HOME`
  inside its isolated-worktree branch (exactly one assignment, line 502); the AO VM's own host gate
  (`_sdp_isolation_default`, 2026-08-10 operator ruling) makes isolation OFF by DEFAULT whenever
  `_sdp_host_label()` != `"laptop"` — and on this exact host, `ORCHESTRATOR_VM_ID=planning` resolves that label to
  `"planning"`. So on `planning` (the only VM — every slot 1-31+ shares this one host/filesystem), isolation is off by
  design for every slot, PREK_HOME is never scoped, and prek falls back to its own single default `~/.cache/prek`
  (confirmed via the script's own fallback expression, line 698: `${PREK_HOME:-$HOME/.cache/prek}`) — one directory,
  shared by every concurrently-running slot's `safe-doc-push.sh` invocation. This is NOT a defect in the isolated-mode
  PREK_HOME-scoping code itself (that code correctly scopes it whenever isolation IS engaged) — it is a gap in the
  2026-08-10 host-gate's own reasoning, which addressed the git-index/working-tree collision hazard (correctly ruled
  absent on the AO VM, since each slot has its own clone) but never considered prek's OWN cache directory, which is a
  host-filesystem-level shared resource independent of git-clone isolation.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [safe-doc-push, prek, cross-slot, host-gate, root-cause, agent-orchestrator]
related:
  [
    /plans/active/issues/safe_doc_push_cross_slot_prek_patch_orphans_completed_fix_2026_08_16.md,
    /plans/archive/issues/safe_doc_push_false_positive_rebase_multiple_branches_2026_08_16.md,
    /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-16
last_updated: "2026-08-16"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: infra
source: >-
  slot-31 (infra), root-causing the todo in safe_doc_push_cross_slot_prek_patch_orphans_completed_fix_2026_08_16.md,
  2026-08-16.
author: slot-31
resolved_by:
locked_by:
locked_since:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    scripts/dev/safe-doc-push.sh,
    /plans/active/issues/safe_doc_push_cross_slot_prek_patch_orphans_completed_fix_2026_08_16.md,
  ]
---

# safe-doc-push.sh: PREK_HOME is shared host-wide across every AO VM slot — root cause confirmed

## What I found (evidence, not a guess)

Investigating the "genuine cross-slot PREK_HOME leak?" question from
`safe_doc_push_cross_slot_prek_patch_orphans_completed_fix_2026_08_16.md`'s todo 2:

1. `grep -n "PREK_HOME" scripts/dev/safe-doc-push.sh` returns exactly 3 hits: a header comment (line 468), the ONE
   assignment (line 502, inside the isolated-worktree branch only:
   `PREK_HOME="$_sdp_iso_prek_home" SDP_IN_ISOLATION=1 ... bash "$_SDP_SELF" ...`), and a read-only fallback expression
   (line 698: `"${PREK_HOME:-$HOME/.cache/prek}/patches"`). **Outside the isolated branch, `PREK_HOME` is never set by
   this script at all** — prek uses its own unmodified default, `~/.cache/prek`.
2. The isolated branch only executes when `_SDP_ISOLATED_EFFECTIVE != 0`. That value comes from
   `_SDP_ISOLATED_EFFECTIVE="${SDP_ISOLATED:-$(_sdp_isolation_default)}"`, and `_sdp_isolation_default()` is:
   `[[ "$(_sdp_host_label)" == "laptop" ]] && echo 1 || echo 0` — isolated by default ONLY on a host whose label is
   literally `"laptop"`; every other host label defaults to **0 (isolation OFF)**.
3. `_sdp_host_label()` reads `${ORCHESTRATOR_VM_ID:-${VM_NAME:-$(git config --global slotIdentity.host)}}`. Checked
   directly on this session (slot 31, on `planning`): `ORCHESTRATOR_VM_ID=planning` — confirmed set, confirmed
   resolves the label to `"planning"`, not `"laptop"`.
4. Per CLAUDE.md's own System-map section, `planning` is **the only VM** — every worker slot (1 through 31+) runs on
   this exact same host, same `$HOME`, same filesystem.

Putting 1-4 together: **on every slot on `planning`, `SDP_ISOLATED` defaults to 0, PREK_HOME is never scoped, and
every slot's `safe-doc-push.sh` invocation shares the exact same `~/.cache/prek/patches/` directory** whenever it runs
in the (default, on this host) shared-index code path. Any two slots committing concurrently via `safe-doc-push.sh`
share one prek patches cache, full stop — this is deterministic given the current code, not a rare race.

## Why the host gate didn't already prevent this — it wasn't designed to

The host gate (`_sdp_isolation_default`, 2026-08-10 operator ruling, see the script's own header comment at lines
277-289) reasons: "Isolation defends against ONE hazard: two processes sharing a single checkout... That needs a
SHARED INDEX... On the agent-orchestrator VM the dispatcher runs ONE task per slot and each slot is its own clone, so
there is no second writer and isolation buys nothing." That reasoning is **correct** about the git working-tree/index
hazard (each slot genuinely has its own separate git clone under `.tabs/<N>/`, so two slots' `git add`/`git commit`
calls cannot collide on the same index). But `~/.cache/prek/` is not part of any git clone — it is a single
`$HOME`-relative directory every slot process shares regardless of which clone invoked prek. The host gate's stated
justification never addresses this second, independent hazard, so disabling isolation (correctly, for the git-index
reason) also incidentally disabled the ONLY mechanism in this script that happened to scope PREK_HOME — a side effect,
not a deliberate decision.

## Is this "a real residual gap" needing a fix, or already adequately covered?

Both, in different senses:

- **The exposure is real and confirmed** (not a one-off): the archived
  `safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`'s own Progress Log documents this EXACT
  signature — "orphaned patch diffs an UNRELATED file this session never touched" — recurring on at least 10 separate
  occasions across different slots (23, 30 ×2, 18, 20, 17, 22, 6, 8) between 2026-08-10 and 2026-08-11 alone, every
  one correctly identified as "a leftover patch from a DIFFERENT concurrent process/session sharing this host's
  `~/.cache/prek/patches/` cache dir." This is consistent, ongoing behavior directly caused by the mechanism above,
  not a fluke.
- **It has never actually caused silent data loss**, in the sense that matters: `check_orphaned_prek_patches()`
  (added by that same doc's todo 2, `unified-trading-pm@24ac737541`) reliably fires on every occurrence (exit 9, loud
  warning, patch left in place), and in every logged case the responding slot correctly recognized the foreign
  content and left it for its owner. The 2026-08-16 near-miss this follow-up traces back to
  (`safe_doc_push_cross_slot_prek_patch_orphans_completed_fix_2026_08_16.md`) was the safety net working exactly as
  designed — slot-16 caught it, verified it was genuinely unlanded via `git apply --check`, and preserved it in a
  named stash rather than losing it. The "near-miss" framing in that doc is about the cache directory being the ONLY
  copy pending eviction, not about the detection mechanism failing.

So: **no code fix is strictly required for correctness** (the loud-detection safety net has a 100% catch rate across
every documented instance) — but the underlying exposure is real, cheap to close, and its recurrence rate (10+ times
in ~5 weeks of this corpus alone) makes it worth eliminating at the source rather than continuing to rely on every
future slot noticing and handling the warning correctly by hand.

## Recommended fix (cheap, does not reintroduce the worktree cost the host gate was designed to avoid)

Decouple "scope PREK_HOME" from "run the full isolated-worktree copy." The isolated branch already derives a
per-slot path segment via `slot-identity-lib.sh`'s `slot_identity_resolve` (lines 389-397) purely to compute
`_sdp_slot_seg`/`_sdp_iso_prek_home` — that derivation costs nothing (`git config`+regex match, no worktree
operation). A minimal fix:

- When `_SDP_ISOLATED_EFFECTIVE == 0` (the AO-VM default path), still resolve the caller's slot label via the same
  `slot-identity-lib.sh` call, and `export PREK_HOME="$HOME/.cache/prek-slot-<N>"` before invoking prek (mirroring the
  isolated branch's own symlink-shared-subdirs-but-private-patches pattern at lines 480-487, so hook-repo installs
  stay shared/cheap and only the `patches/`/`scratch` dirs are private per slot).
- This adds zero worktree checkout cost (the exact overhead the 2026-08-10 host gate exists to avoid) — just a
  `mkdir -p` + a handful of symlinks + one env var — while eliminating the shared-cache exposure at the root for
  every future AO-VM run.

## Todos

- [ ] [INFRA] P3. Implement the recommended fix above in `scripts/dev/safe-doc-push.sh`: scope `PREK_HOME` per-slot
      in the shared-index (non-isolated) code path too, reusing `slot-identity-lib.sh`'s existing slot-label
      resolution and the isolated branch's shared-subdir-symlink pattern (lines 480-487) so hook-repo installs stay
      cheap/shared while `patches/`/`scratch` become private per slot. Add/extend a regression test confirming two
      concurrent `safe-doc-push.sh` shared-index runs (simulated distinct slot labels) no longer see each other's
      prek patches. Mirror the same fix into `quickmerge.sh` if it has the analogous host-gate/PREK_HOME shape (check
      first — do not assume). Done when: shipped via the full `quality-gates.sh` → `quickmerge` flow (this is a
      `scripts/dev/` code change) and the regression test is green. (repo: unified-trading-pm)

## Progress Log

- **2026-08-16 (slot-31, infra)** — root-caused per
  `safe_doc_push_cross_slot_prek_patch_orphans_completed_fix_2026_08_16.md` todo 2. Confirmed with direct evidence
  (grep + live env check on this exact host) that PREK_HOME is only ever scoped inside the isolated-worktree branch,
  that isolation defaults OFF on `planning` (the only VM) via the 2026-08-10 host gate, and that the host gate's own
  stated justification addresses only the git-index hazard, never prek's separate host-global cache dir. Verdict: a
  real, confirmed, ongoing mechanism (10+ prior documented recurrences), but not itself an active data-loss defect —
  `check_orphaned_prek_patches()` has a 100% catch rate across every logged instance. Filed this follow-up with a
  concrete, cheap fix rather than absorbing the code change into the root-cause task itself (infra.md: shared-tooling
  blast-radius changes are for their own scoped task, not folded into an investigation todo).
