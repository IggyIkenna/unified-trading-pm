---
doc_type: issue
title: Orphaned prek patch (slot 9 worktree) describes an unshipped CI fix — restoring it verbatim would falsely mark a batch15 todo DONE
summary: >-
  A safe-doc-push.sh run in slot 9's unified-trading-pm worktree hit the known
  "orphaned prek patch not restored on retry success" bug — two identical patches
  survived the run, both touching plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md.
  The patch content flips the "stagger ldr-to-main-promote-fleet.yml fan-out" todo to
  DONE, attributed to slot 20, citing a STAGGER_SECONDS feature in
  scripts/cicd/ldr_to_main_fleet_promote.sh + a new regression test — but neither the
  code change nor the test file exists anywhere in the repo, and the commit sha in the
  patch text is a literal unfilled `\<sha\>` placeholder. Restoring this patch verbatim
  and committing it would check off real infra work that was never actually implemented
  — exactly the false-progress failure mode CLAUDE.md's "Plans run to actual completion"
  rule exists to prevent. Not applied; left for a CI/infra-craft worker to triage.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, safe-doc-push, prek, orphaned-patch, false-progress, batch15]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md,
    /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
  ]
created: "2026-08-17"
author: slot-9 (data_engineering)
last_updated: "2026-08-17"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: infra
drift_direction: none
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source: >-
  Discovered incidentally while shipping an unrelated data_engineering finding
  (defi_dex_swaps_gap_rootcause_ao_dispatch_2026_08_16.md) via safe-doc-push.sh in slot 9;
  the run printed the known orphaned-patch warning
  (safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md's failure mode) for
  two identical patches unrelated to the files being shipped.
context_scope:
  [
    /plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md,
    /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
    scripts/cicd/ldr_to_main_fleet_promote.sh,
  ]
---

# Orphaned prek patch describes an unshipped CI fix — do not restore verbatim

## What I found

While shipping an unrelated finding via `safe-doc-push.sh` from slot 9's `unified-trading-pm` worktree
(2026-08-17), the run printed the known orphaned-prek-patch warning
(`/plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`'s exact
failure signature) for two
byte-identical patches, both mtime'd during that run:

- `/home/ubuntu/.cache/prek/patches/1786945181958-1981556.patch`
- `/home/ubuntu/.cache/prek/patches/1786945200485-1990334.patch`

Both touch `plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md` — a plan slot 9 was never working on.
`git apply --check` confirms the content is genuinely absent from the current working tree (would apply
cleanly). The patch flips this todo:

> `[INFRA] P2. Stagger ldr-to-main-promote-fleet.yml's per-repo fan-out ...`

to `- [x] ✅ ... DONE 2026-08-17 (slot 20) — unified-trading-pm@\<sha\>.` — describing an `STAGGER_SECONDS`
env var added to `scripts/cicd/ldr_to_main_fleet_promote.sh`'s bounded-parallel driver, plus a new regression
test `scripts/quality-gates-base/tests/test-ldr-promote-fanout-stagger.sh` (claimed "6/6 assertions pass").

**Verified against the live repo (2026-08-17): neither exists.** `grep -n "STAGGER_SECONDS"
scripts/cicd/ldr_to_main_fleet_promote.sh` — zero hits. `scripts/quality-gates-base/tests/test-ldr-promote-fanout-stagger.sh`
— does not exist. `git log --all --grep="stagger" -i` — no matching commit. The `\<sha\>` in the patch text is a
literal unfilled placeholder, not a real short-sha — this draft was never actually committed anywhere, by
slot 20 or otherwise.

## Why it matters

If a future sweep (or an agent inheriting slot 9's dirty worktree) blindly `git apply`s this patch and ships
it — the natural reading of the base safe-doc-push runbook's own recovery instruction ("if genuinely missing,
`git apply <patch>` restores it") — it would check off real CI infra work as DONE with a fabricated evidence
sha, when the described code change was never written. That is exactly the false-progress failure mode
CLAUDE.md's "Plans run to actual completion, not smoke-test green" + "Runtime verification — never done
without running the code" rules exist to prevent. Deliberately NOT applying it here.

## Recommended decision

The underlying batch15 todo (stagger the promote-fleet fan-out) is real, well-specified, and still genuinely
open — the patch text is a legitimate DESIGN for it, just never implemented. A CI/infra-craft worker should
either (a) implement the `STAGGER_SECONDS` feature + regression test as specified in the patch text (quoted in
full in `git diff` output of the two patch files above) and then flip the batch15 checkbox for real with an
actual commit sha, or (b) if the design is stale/superseded, leave the batch15 todo open as-is and just note
this patch was discarded as a draft, never shipped. Either way, the two `.patch` files above should stay on
disk until someone completes this triage (do not delete pending resolution).

## Todos

- [ ] [INFRA] P3. Triage the orphaned patch above: either implement the `STAGGER_SECONDS` fan-out-stagger
      feature it specifies in `scripts/cicd/ldr_to_main_fleet_promote.sh` (+ its regression test) and flip
      `ci_satellite_ao_dispatch_batch15_2026_08_16.md`'s stagger todo with a real commit sha, or confirm the
      design is superseded and leave that todo open with a note. Repo: unified-trading-pm. Done when: either
      the feature ships for real, or the batch15 todo carries an explicit note that this draft was discarded.

## Progress Log

- **2026-08-17 (slot 9, data_engineering)**: filed while investigating a safe-doc-push orphaned-patch warning
  incidental to an unrelated task; verified via live grep + git log that the patch's claimed code/test do not
  exist. Not applied. Not my craft (CI/infra) — leaving for the right worker to pick up.
