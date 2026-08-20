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
repos: [unified-trading-pm, deployment-service]
scope: [engineer]
tags: [ci, safe-doc-push, prek, orphaned-patch, false-progress, batch15, dangling-commit]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md,
    /plans/archive/2026_08/issues/safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md,
  ]
created: "2026-08-17"
author: slot-9 (data_engineering)
last_updated: "2026-08-20"
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
    scripts/quality-gates-base/tests/test-ldr-promote-fanout-stagger.sh,
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

## Second occurrence (2026-08-17, same session) — a dangling REAL commit, different failure shape

A second, unrelated safe-doc-push run in the SAME session hit the identical orphaned-patch warning again, for
`/home/ubuntu/.cache/prek/patches/1786946339254-2938102.patch`, touching
`plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md` +
`plans/archive/2026_08/infra_satellite_ao_dispatch_batch18_2026_08_16.md`. This one is a DIFFERENT failure shape — not an
unshipped draft, but real work that WAS shipped and then fell off the branch:

- The patch claims `deployment-service@e631240990` shipped `scripts/measure_shard_duration_p95.py` (229 lines) and
  cites concrete measurement output (a 16-row p95/max shard-duration table) plus a claim that
  `infra_satellite_ao_dispatch_batch18_2026_08_16.md` was "completed + archived 2026-08-17."
- **Verified**: the commit `e631240990` genuinely exists (`ikennaigboaka [slot-27·planning]`, 2026-08-17T05:56:16Z,
  proper `Quickmerge: agent` trailer, real diff adding the 229-line script) — but `git merge-base --is-ancestor
  e631240990 HEAD` returns **false** in slot 9's `deployment-service` clone: it is a dangling commit, not part of
  current `live-defi-rollout` history. The script file does not exist anywhere in the current working tree.
- `infra_satellite_ao_dispatch_batch18_2026_08_16.md` is confirmed still sitting in `plans/active/` — NOT archived,
  contradicting the patch text's own claim (written prematurely, before the archival it describes actually
  landed).
- Not applied here either, for a different reason than occurrence 1: the underlying doc-archival claim in the
  patch text is itself not yet true, so restoring the prose verbatim would misdescribe current state even though
  the CODE commit it cites is real.

This is a more serious variant: a properly quickmerge-trailed commit that landed once (by slot-27) but is now
unreachable from `deployment-service`'s current HEAD is a genuine dropped-work signal, not just an
interrupted-draft signal — worth the infra-craft triage recognizing both shapes exist under this same root cause.

## Todos

- [x] ✅ [INFRA] P3. Triage the orphaned patch above — option (a) confirmed shipped for real, verified 2026-08-19
      (plan_reconciler, cross-cutting tranche): `STAGGER_SECONDS` fan-out-stagger genuinely exists at
      `scripts/cicd/ldr_to_main_fleet_promote.sh:370-372,1400` (env-overridable stagger + the gating `sleep` call)
      and its regression test `scripts/quality-gates-base/tests/test-ldr-promote-fanout-stagger.sh` exists — both
      on `origin/live-defi-rollout` (not the orphaned patch's `<sha>` placeholder).
      `ci_satellite_ao_dispatch_batch15_2026_08_16.md:118` already carries the real matching flip ("DONE
      2026-08-17 (slot 20) — unified-trading-pm@23499c954f"). Done-when satisfied.
- [x] ✅ [INFRA] P2. DONE 2026-08-17 (slot 5, infra) — Investigate the second occurrence: why is
      `deployment-service@e631240990` (a real, properly-trailed commit by slot-27, 2026-08-17T05:56:16Z, adding
      `scripts/measure_shard_duration_p95.py`) NOT an ancestor of current `live-defi-rollout` HEAD? **Resolution:
      it was a stale-clone false alarm, not a dropped commit.** Re-verified live in slot 5's `deployment-service`
      clone: `git fetch origin live-defi-rollout` then `git merge-base --is-ancestor e631240990
      origin/live-defi-rollout` → **true**; `git log --oneline e631240990` shows it in the direct ancestry of
      current `live-defi-rollout` HEAD (`84bfbae4`); `scripts/measure_shard_duration_p95.py` is present on disk
      (229 lines, matches the commit diff). No force-push/reset/rebase occurred — slot 9's original check was
      simply run against a clone that hadn't fetched the commit yet (the commit landed 2026-08-17T05:56:16Z; slot
      9's investigation session was concurrent). Both downstream docs already reflect the true state as of this
      check: `plans/archive/2026_08/infra_satellite_ao_dispatch_batch18_2026_08_16.md` is archived, and
      `plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md`'s Phase 0 measurement todos are
      all closed (line 642: "Phase 0 — preconditions and measurement — DONE — all 7 todos, p95/max shard-duration
      table landed 2026-08-17"). No code change needed; no correction needed to either plan.
- [ ] [INFRA] P3. Re-open or cross-reference `safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`
      (status: resolved) — this exact bug class recurred TWICE in one session on slot 9 within minutes of each
      other, so the fix may not fully hold under the current ~21-entry autostash-pile
      contention level this slot is running under. Repo: unified-trading-pm / agent-orchestrator (wherever
      safe-doc-push.sh's stash/restore logic lives). Done when: either the fix is confirmed still sufficient
      under high-contention load, or a follow-up fix lands.

## Progress Log

- **2026-08-17 (slot 9, data_engineering)**: filed while investigating a safe-doc-push orphaned-patch warning
  incidental to an unrelated task; verified via live grep + git log that the patch's claimed code/test do not
  exist. Not applied. Not my craft (CI/infra) — leaving for the right worker to pick up.
- **2026-08-17 (slot 9, data_engineering), same session, second occurrence**: a second, unrelated safe-doc-push
  run hit the same warning for a different, unrelated doc pair. Investigated and found a materially different
  failure shape (a real dangling commit, not an unshipped draft) — see the new section above. Not applied;
  filed as new todos rather than a separate doc, since it's the same underlying mechanism.
- **2026-08-17 (slot 5, infra)**: picked up the P2 todo re: the "dangling commit" second occurrence. Re-checked
  `deployment-service@e631240990` against a freshly-fetched `origin/live-defi-rollout` — it IS an ancestor, the
  script file is present on disk, and both downstream plans already show the correct completed state. Root cause
  was slot 9's clone being behind at the moment of its check, not a real force-push/reset/rebase drop. Closed the
  todo with no code change required.
- **context-scout 2026-08-17**: refreshed context_scope (3 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries).
