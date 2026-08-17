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
status: open
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
resolved_by:
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

- [ ] [CICD] P1. Root-cause why `safe-doc-push.sh`'s prek-patch restore step does not fire for a cross-slot orphaned
      patch (a patch NOT created by the current invocation's own commit attempt) on a successful retried push. Fix so
      every patch with an in-window mtime is either restored or the failure is loud enough to page immediately (not
      just a post-hoc exit-9 warning after the destructive window has already passed). Repo: unified-trading-pm.
      Cite this doc + the 2 patches' md5 (`527608ea9e64b09163217ea7c3f3df46`) as reproduction evidence if the
      `~/.cache/prek/patches/` files are still present on the orchestrator VM's shared filesystem when picked up.
- [ ] [INFRA] P2. Re-verify `ci_satellite_ao_dispatch_batch15_2026_08_16.md`'s `[INFRA] P2` "Stagger
      `ldr-to-main-promote-fleet.yml`'s per-repo fan-out" todo — it is still genuinely `- [ ]` open (slot 20's
      believed-complete work never actually landed). Either redo the `STAGGER_SECONDS`
      (`LDR_MAIN_PROMOTE_STAGGER_SECONDS`) fix to `scripts/cicd/ldr_to_main_fleet_promote.sh` + the regression test
      described in the recovered patch text above (available in this doc's "What I found" section as a spec), or
      confirm via `git log` that it landed under a different SHA than the placeholder suggests before assuming a
      full redo is needed. Repo: unified-trading-pm.

## Progress log

- 2026-08-17 (slot-16, data_engineering craft): Filed while shipping an unrelated archival task. Confirmed genuine
  cross-slot code+test loss (not just a doc checkbox); did not attempt to reconstruct the lost code myself (out of
  this task's scope); preserved the 4 orphaned patch files as evidence.
