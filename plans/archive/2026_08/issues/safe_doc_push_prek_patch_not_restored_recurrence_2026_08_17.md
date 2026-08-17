---
doc_type: issue
title:
  "safe-doc-push.sh orphaned-prek-patch recurrence — another slot's real code+test work confirmed lost, not just a
  doc checkbox"
summary: >-
  Recurrence of `safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md` (resolved 2026-08-09/10,
  `safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09_finalize_2026_08_10`) — the same "orphaned prek
  patch after a successful retried push" symptom fired again 2026-08-17, but this time the confirmed-lost content is
  a DIFFERENT slot's real shipped-believed work (a code fix + new regression test), not a doc-only checkbox flip like
  the original incident. Found incidentally while shipping an unrelated archival task.
status: resolved
nature: issue
asset_group: [ci, ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [safe-doc-push, prek, precommit, data-loss, ci, plan-hygiene, recurrence]
related:
  [
    /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
    /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09_finalize_2026_08_10.md,
    /scripts/dev/safe-doc-push.sh,
    /plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md,
  ]
created: 2026-08-17
author: data_engineering worker (slot 16)
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: none
depends_on: []
resolved_by: slot-13-2026-08-17
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Found live 2026-08-17 while running `scripts/dev/safe-doc-push.sh` for an unrelated defi-plan archival task
  (`defi_expected_unattempted_backlog_1m_2026_07_03_finalize_2026_08_08.md`'s `[DOC]` todo). The push itself
  succeeded (`7d5e7bd426` -> live-defi-rollout, verified ancestor of origin) but the script exited non-zero (exit 9)
  on 4 orphaned prek patches it detected post-push."
context_scope:
  [
    /scripts/dev/safe-doc-push.sh,
    /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
  ]
---

# safe-doc-push.sh orphaned-prek-patch recurrence — confirmed real code+test loss

> **🟢 ARCHIVED 2026-08-17 — COMPLETE.** Both todos shipped/verified: (1) root-caused + fixed the cross-slot
> orphaned-prek-patch restore gap (`unified-trading-pm@ea2f3ea8c6`); (2) re-verified `ci_satellite_ao_dispatch_batch15_2026_08_16.md`'s
> stagger todo — the previously-lost work was independently redone and landed for real under
> `unified-trading-pm@23499c954f` (confirmed ancestor of origin, regression test passes 6/6 live). No further action.

## What I found

While shipping an unrelated archival commit via `bash scripts/dev/safe-doc-push.sh` (this repo, `unified-trading-pm`),
the push landed successfully (`✅ Pushed 7d5e7bd426 -> live-defi-rollout`, independently verified via
`git merge-base --is-ancestor 7d5e7bd426 origin/live-defi-rollout`) but the script exited non-zero (exit 9), printing
its own "ORPHANED PREK PATCH(ES) DETECTED" warning for 4 patch files under `~/.cache/prek/patches/`, all with mtimes
inside my run's window:

- `1786945181958-1981556.patch`
- `1786945200485-1990334.patch`
- `1786945210194-1997928.patch`
- `1786945212530-2000005.patch`

**All 4 are byte-identical** (`md5sum` confirms one hash across all 4) — a single stash-patch duplicated across my
run's retry loop (the log shows `attempt 1/6` hit an origin-moved reconciliation and retried to `attempt 2/6`), not 4
distinct pieces of content.

**Critically, this patch is NOT mine — it belongs to a different slot's unrelated in-flight work**, confirming the
original 2026-08-09 bug class recurs for ANY concurrent slot's uncommitted edits caught in the stash window, not just
the committing slot's own out-of-scope files. The patch's sole diff hunk is against
`plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md`, flipping an `[INFRA] P2` "Stagger
`ldr-to-main-promote-fleet.yml`'s per-repo fan-out" todo from `- [ ]` to `- [x] ✅ ... DONE 2026-08-17 (slot 20) —
unified-trading-pm@\<sha\>` with a full evidence write-up (an `STAGGER_SECONDS`/`LDR_MAIN_PROMOTE_STAGGER_SECONDS` env
var added to `scripts/cicd/ldr_to_main_fleet_promote.sh`, plus a new regression test
`scripts/quality-gates-base/tests/test-ldr-promote-fanout-stagger.sh`, "6/6 assertions pass").

**Verified this is genuine, not just an unrestored doc edit**:

- The live `ci_satellite_ao_dispatch_batch15_2026_08_16.md` still shows the todo as `- [ ]` (unchecked) — the doc-side
  checkbox flip never landed, matching the original bug's symptom.
- **Neither of the two code artifacts the checkbox's own evidence describes exist anywhere in this checkout**:
  `grep -rn "STAGGER_SECONDS" scripts/cicd/ldr_to_main_fleet_promote.sh` → zero hits;
  `scripts/quality-gates-base/tests/test-ldr-promote-fanout-stagger.sh` → does not exist. The evidence text itself
  even carries a literal unresolved `unified-trading-pm@\<sha\>` placeholder (never substituted with a real SHA),
  suggesting slot 20's own commit attempt may never have completed either — this isn't just an unrestored stash, the
  underlying work was very likely never actually committed to begin with.
- `git status --porcelain` in my own worktree is clean (nothing of mine is dirty/missing) — this is NOT my task's
  content; I did not edit this file or these code paths.

**Did NOT apply the patch myself** — reverse-applying just the doc's checkbox-flip text, without the actual
`ldr_to_main_fleet_promote.sh`/test-file changes it describes, would misrepresent unshipped code as done (the same
"don't stamp incomplete work as complete" principle as the data-pipeline-correctness rule, applied to code work).
Left the 4 patch files in place as evidence (`~/.cache/prek/patches/`, listed above) rather than deleting them — they
are the only surviving record of slot 20's intended fix.

## Why it matters

The 2026-08-09/10 fix (`safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09_finalize_2026_08_10`) closed
the SAME-SLOT case (a committing slot's own earlier-session edits to out-of-scope files). This recurrence shows the
gap also (or still) applies **cross-slot**: another slot's genuinely uncommitted work-in-progress can be silently
swept into an orphaned stash by a DIFFERENT slot's retry-loop prek run and then never restored — meaning any slot
running `safe-doc-push.sh` under contention can silently destroy a sibling slot's real, unshipped code+test work, not
just doc-only edits. This is a bigger blast radius than the original finding.

## Recommended decision

Root-cause why the restore step doesn't fire on a successful retry (the original fix's own mechanism should be
re-examined for why it didn't catch this case — possibly the cross-slot ownership of the stashed patch is what
differs, if the restore logic keys off "patches created by MY invocation" rather than "any patch with mtime inside
my run's window"). Once root-caused: (a) fix the restore gap, (b) separately notify/recover slot 20's actual intended
`ldr_to_main_fleet_promote.sh` stagger fix — that real engineering work (env-var + regression test) needs to be
redone from scratch, since only its DESCRIPTION survived, not its code.

## Todos

- [x] ✅ [CICD] P1. Root-cause why `safe-doc-push.sh`'s prek-patch restore step does not fire for a cross-slot orphaned
      patch (a patch NOT created by the current invocation's own commit attempt) on a successful retried push. Fix so
      every patch with an in-window mtime is either restored or the failure is loud enough to page immediately (not
      just a post-hoc exit-9 warning after the destructive window has already passed). Repo: unified-trading-pm.
      Cite this doc + the 2 patches' md5 (`527608ea9e64b09163217ea7c3f3df46`) as reproduction evidence if the
      `~/.cache/prek/patches/` files are still present on the orchestrator VM's shared filesystem when picked up.
      — unified-trading-pm@ea2f3ea8c6. See Progress Log for the root-cause finding + fix.
- [x] ✅ [INFRA] P2. **DONE 2026-08-17 (slot-13, infra craft)** — Re-verified `ci_satellite_ao_dispatch_batch15_2026_08_16.md`'s
      "Stagger `ldr-to-main-promote-fleet.yml`'s per-repo fan-out" todo. **No redo needed**: the todo is already
      `- [x]` DONE citing a real SHA (`unified-trading-pm@23499c954f`), NOT the unresolved `\<sha\>` placeholder this
      doc's "What I found" section flagged — the work was independently redone (or the original commit completed)
      under a fresh SHA after the original patch-loss. Confirmed genuinely landed, not just doc-side: `git merge-base
      --is-ancestor 23499c954f origin/live-defi-rollout` → ancestor confirmed; `grep -n STAGGER
      scripts/cicd/ldr_to_main_fleet_promote.sh` shows `STAGGER_SECONDS="${LDR_MAIN_PROMOTE_STAGGER_SECONDS:-3}"` +
      the `sleep "$STAGGER_SECONDS"` call site (matches the recovered patch's described spec);
      `scripts/quality-gates-base/tests/test-ldr-promote-fanout-stagger.sh` exists and, run live, passes **6/6**
      (structural: env-overridable + sleep-after-launch; functional: measured inter-launch gap >= stagger,
      stagger=0 opt-out completes in 15ms). Repo: unified-trading-pm (verification only, no code changed).

## Progress log

- 2026-08-17 (slot-16, data_engineering craft): Filed while shipping an unrelated archival task. Confirmed genuine
  cross-slot code+test loss (not just a doc checkbox); did not attempt to reconstruct the lost code myself (out of
  this task's scope); preserved the 4 orphaned patch files as evidence.
- 2026-08-17 (slot-15, infra, todo 1 shipped — `unified-trading-pm@ea2f3ea8c6`): **Root cause**: the 2026-08-16
  per-slot `PREK_HOME` scoping (`safe_doc_push_shared_prek_home_across_ao_vm_slots_2026_08_16.md`) closed the
  shared-`~/.cache/prek/patches` collision ONLY for `scripts/dev/safe-doc-push.sh` and `scripts/quickmerge.sh`'s own
  shared-index code paths. It never covered the **raw `git commit` + `git push`** path — the one `RULES.md` §2 /
  `worker.md` §5-b2 explicitly sanction for a cross-repo PM plan-flip (edit the checkbox in the sibling PM worktree,
  `git add` / `git commit` / `git push origin HEAD:live-defi-rollout` directly, bypassing both wrapper scripts by
  design — it's the single highest-frequency mutation this repo sees, since every worker's `/done` does one). A raw
  commit invokes prek purely through `.git/hooks/pre-commit` (confirmed: that hook is a bare generated shim, `exec
  "$PREK" hook-impl ...`, with no `PREK_HOME` logic at all), so it always fell through to prek's unscoped
  host-global default `~/.cache/prek`. Any two slots landing a raw plan-flip commit at the same moment share that
  one `patches/` cache dir, and prek's own stash/restore of each other's unstaged out-of-scope edits can interleave
  — reproducing, for the raw-commit path specifically, the exact cross-process race
  (`prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md`) the 08-16 fix closed for the two wrapper
  scripts only. This explains why the finder (slot 16, running `safe-doc-push.sh`, which since 08-16 exports its
  own scoped `PREK_HOME=~/.cache/prek-slot-16`) still found a fresh orphan in the OLD global dir: its own run no
  longer writes there at all post-scoping, so the only thing that CAN still land a fresh patch in that global dir is
  a process that isn't going through either wrapper — i.e. a raw commit, consistent with slot 20's plan-flip being
  exactly that shape.
  **Fix** (`unified-trading-pm@ea2f3ea8c6`): (1) `scripts/dev/slot-cron-ff-pull.sh` — added a content-gated
  self-heal (same pattern as the existing pre-push-guard heal in the same loop) that patches every clone's
  prek-generated `.git/hooks/pre-commit` to export a per-slot `PREK_HOME` before `exec`ing prek, mirroring
  `safe-doc-push.sh`/`quickmerge.sh`'s own scoping — converges fleet-wide within one 5-min cron sweep and re-heals
  if a future `prek install` regenerates the hook without it. Verified the injected patch is syntactically valid
  (`bash -n`) and idempotent (marker-gated) against this slot's own live hook before shipping. (2)
  `scripts/dev/safe-doc-push.sh`'s `check_orphaned_prek_patches()` was hardcoded to scan the OLD global
  `~/.cache/prek/patches` unconditionally — a related bug the 08-16 scoping fix introduced without updating this
  checker: post-scoping, THIS run's own orphans land under `$PREK_HOME/patches` (its private per-slot dir), so the
  hardcoded path was checking the wrong directory for a same-slot self-caused orphan. Changed to
  `${PREK_HOME:-$HOME/.cache/prek}/patches` so the safety net covers both shapes again.
  Did not action todo 2 (out of this task's assigned scope — `[INFRA] P2`, a separate re-verify/redo of slot 20's
  lost `ldr_to_main_fleet_promote.sh` work); left it open for its own dispatch.
- 2026-08-17 (slot-13, infra craft, todo 2): Re-verified — no redo needed. `ci_satellite_ao_dispatch_batch15_2026_08_16.md`'s
  stagger todo is already `[x]` DONE under a real SHA (`23499c954f`, confirmed ancestor of origin), distinct from the
  unresolved placeholder this doc originally flagged — someone (slot 20 or a subsequent redo) landed the fix for
  real. Verified live: `STAGGER_SECONDS`/`LDR_MAIN_PROMOTE_STAGGER_SECONDS` present in
  `scripts/cicd/ldr_to_main_fleet_promote.sh`, and the regression test
  (`scripts/quality-gates-base/tests/test-ldr-promote-fanout-stagger.sh`) exists and passes 6/6 when run directly.
  Both todos in this issue doc are now done; no further action needed here.
