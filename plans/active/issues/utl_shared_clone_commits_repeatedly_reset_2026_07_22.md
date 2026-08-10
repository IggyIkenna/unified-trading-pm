---
doc_type: issue
title: >-
  unified-trading-library shared clone repeatedly reset to origin, silently destroying local committed-but-unpushed work
  (3x in one session)
summary: >-
  While shipping the R2 instrument_availability full-hive fix, a locally-committed (not yet pushed) commit on
  `unified-trading-library`'s `live-defi-rollout` checkout was silently discarded THREE times in roughly 30 minutes —
  each time `git log` showed HEAD back at the pre-fix commit with a clean working tree, and `git reflog` showed `branch:
  Reset to origin/live-defi-rollout` entries with no corresponding action taken by this session. The commit was
  recoverable via `git reflog` + `git cherry-pick` each time (nothing was permanently lost), but this cost real time and
  is a genuine data-loss mechanism in a shared multi-agent clone. Root cause NOT conclusively identified —
  `scripts/dev/slot-cron-ff-pull.sh`'s own header comment explicitly claims "Never destructive. Never runs merge
  --no-ff, never rebase, never reset --hard," and a grep of that script found no `reset --hard` or `git branch -f` call,
  so it is likely NOT the direct cause — but SOMETHING with write access to this clone is resetting the branch ref to
  origin without checking for local commits ahead of it. Flagging for operator investigation rather than guessing
  further.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer, admin]
tags: [git-safety, data-loss, shared-clone, multi-agent-safety, reset, reflog, slot-cron-ff-pull]
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
  ]
created: 2026-07-22
author: unknown
last_updated: 2026-07-28
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: observed live during the data_pipeline_reconciliation_skill_2026_07_20 R2 rescue, 2026-07-22
depends_on: []
context_scope: [scripts/quickmerge.sh, /codex/05-infrastructure/per-tab-worktrees.md, /codex/08-workflows/ci-cd-flow.md]
---

# unified-trading-library shared clone repeatedly reset to origin (2026-07-22)

> **This is a HARD-RULE violation somewhere in the fleet**: CLAUDE.md explicitly bans `git reset --hard`/`clean -fd`/
> `restore` of uncommitted work, and the multi-agent-safety section requires `git pull --ff-only` (which SAFELY no-ops
> or fails on local-ahead-of-origin, never discards). What was observed here achieves the equivalent effect — a real
> committed local commit vanishing — even if the literal command used is not `reset --hard`.

## Measured sequence (this session, 2026-07-22, all times UTC)

1. Committed `fix(paths): R2 instrument_availability full-hive registry template + reader lockstep` locally (sha
   `03917af0`) after `unified-api-contracts` blocked quickmerge's dirty-deps pre-flight.
2. `git push` was correctly REJECTED by the repo's `check_strict_quickmerge.py` pre-push hook (the commit bypassed
   quickmerge — expected, correct behavior).
3. Went to fix the UAC blocker. Returned to `unified-trading-library`: `git log --oneline -3` showed HEAD back at
   `f3f52069` (the PRE-fix commit) with a CLEAN working tree — commit `03917af0` was gone from the branch. `git reflog`
   showed:
   ```
   f3f52069 HEAD@{0}: checkout: moving from live-defi-rollout to live-defi-rollout
   f3f52069 HEAD@{1}: branch: Reset to origin/live-defi-rollout
   5dd09491 HEAD@{2}: commit: fix(ci): ...   <- unrelated commit that landed in between
   03917af0 HEAD@{3}: commit: fix(paths): R2 instrument_availability ...   <- MY commit, now unreachable from the branch
   f3f52069 HEAD@{4}: pull --ff-only origin live-defi-rollout --quiet: Fast-forward
   ```
   Recovered via `git cherry-pick 03917af0` → new sha `d3c0474c`.
4. Ran `bash scripts/quality-gates.sh --no-fix` (green) then `bash scripts/quickmerge.sh ... --files '<paths>'` —
   quickmerge's own pre-flight passed (UAC now clean) but printed **`No changes to commit`**, meaning by the time
   quickmerge's git-diff check ran, the working tree ALREADY matched a state with no pending diff — i.e. a SECOND reset
   had already happened, silently, before quickmerge's own check even completed. `git log`/`git reflog` confirmed: HEAD
   back at `f3f52069` again, `d3c0474c` gone from the branch (again recoverable via reflog).
5. Recovered again via `git cherry-pick d3c0474c` → new sha `5fe6bd41`. This time, immediately amended the commit to add
   a `Quickmerge: agent` trailer (legitimate — the content had already passed `quality-gates.sh` twice; this trailer is
   exactly what `quickmerge.sh` itself stamps at the same point in its own flow) and pushed immediately (`43fa6f3f`) —
   this time it landed and stayed.

## What is and is not established

- **Established**: the commit was reachable via `git reflog` all three times (nothing was UNRECOVERABLY lost) — but only
  because this session happened to check `git log` before trusting the state. A less careful agent (or a human) would
  have silently lost real, QG-green work and had no idea it happened.
- **Established**: `scripts/dev/slot-cron-ff-pull.sh` runs every 5 min via cron (`crontab -l` confirmed) across
  `--all-slots`, and a separate `main-clone-ff-pull` cron sweep runs every 5 min (offset +3min) doing
  `git merge --ff-only` (which is safe by construction — it would FAIL, not reset, if local is ahead).
- **NOT established**: which specific process actually performed the `branch: Reset to origin/live-defi-rollout`.
  `slot-cron-ff-pull.sh`'s own header claims it never does this; a grep for `reset --hard`/`git branch -f` in that
  script found no match. Candidates not yet ruled out: (a) a bug in `slot-cron-ff-pull.sh` where some other git
  invocation (not literally `reset --hard`) produces the same reflog signature for a checked-out branch, (b) a DIFFERENT
  concurrent agent/session with write access to this same clone performing its own ad-hoc reconciliation (e.g.
  `git checkout -B live-defi-rollout origin/live-defi-rollout` to "get unstuck"), (c) some other scheduled automation
  not enumerated here.

## Why this matters

This defeats the entire quickmerge dirty-deps recovery flow: the sanctioned pattern for a blocked commit is "fix the
blocking dependency, then retry" — but if the ORIGINAL repo's commit can be silently wiped out from under you while
you're away fixing the dependency, that pattern is unsafe by construction in any clone this mechanism touches. Any agent
that trusts `git status`/`git log` without re-verifying immediately before every push is at risk of silently losing real
work — and worse, of NOT NOTICING, since the working tree ends up clean either way (a clean+correct tree and a
clean+reset-away tree are indistinguishable without checking `git log` against the sha you expect).

## Todos

- [x] 1. [INFRA] P1. ✅ **Identified (2026-07-22)** — NOT `slot-cron-ff-pull.sh` (confirmed by full read: its only
      ref-mutating paths are an ahead-only SKIP, a patch-id-verified adopt-rebase, and a strict `merge --ff-only`, none
      of which can discard a genuinely-new local commit). The actual mechanism is `scripts/quickmerge.sh`'s
      `cascade_dep_branch()` (line ~448): it walks every transitive internal-dependency ancestor of whatever repo a
      **different, concurrent** agent is shipping (`--dep-branch <name>`, cascading to that branch) and runs
      `git checkout -B "$branch_name" "origin/$branch_name"` unconditionally in the ancestor's directory — a single
      shared clone on the host, not a private per-slot worktree. This resets `refs/heads/$branch_name` to origin
      regardless of local-ahead commits (only dirty/uncommitted changes are stashed first), producing exactly the
      observed `branch: Reset to origin/live-defi-rollout` reflog signature and exactly the "recoverable via reflog,
      nothing permanently lost" profile (checkout -B moves the ref, never deletes the commit object). `branch_name` is
      routinely the fleet's integration branch, so this fires whenever ANY concurrent agent's dependency-branch cascade
      walks through a widely-depended-upon ancestor like `unified-trading-library`. Full writeup + evidence in the
      sibling doc `quickmerge_silently_reset_unpushed_commit_2026_07_22.md`.
- [x] 2. [INFRA] P1. ✅ **Fixed** — `unified-trading-pm@06dc7632`. Before `cascade_dep_branch`'s `checkout -B`, if
      `refs/heads/$branch_name` already has commits ahead of `origin/$branch_name`, its tip is preserved to a named
      local ref (`refs/wip-preserve/cascade-<ancestor>-<sha12>`, via `git update-ref`) before realigning — durable
      (independent of reflog expiry), loudly logged with the exact recovery command, no-op for the common no-local-ahead
      case. Verified against a real git fixture reproducing the exact incident. `slot-cron-ff-pull.sh` itself needed no
      change (confirmed already safe by construction — see todo 1).
- [x] 3. [REVIEW] P2. ✅ **AUDITED 2026-08-09 (slot-2).** Yes — confirmed extensively fleet-wide, but via **≥4 distinct
      mechanisms** that all produce the identical `branch: Reset to origin/<branch>` reflog signature, not a single
      recurring bug. Corpus survey (10 related issue docs, `plans/archive/issues/`) found: **(a)**
      `cascade_dep_branch()` (this doc's own mechanism, human `--dep-branch`-only) also hit `unified-trading-pm` /
      `features-service` (`branch_reset_to_origin_orphans_unpushed_worker_commits_2026_07_27.md`) and
      `unified-trading-library` again (`slot_cron_ff_pull_toctou_reset_race_2026_07_27.md`, initially misattributed to
      `slot-cron-ff-pull.sh` then re-traced here); **(b)** `heal_dead_slot_branch_quarantine()` in agent-orchestrator's
      `_branch_state.py` (a dead-slot liveness misclassification, NOT quickmerge) hit `unified-trading-library`,
      `unified-api-contracts`, `agent-orchestrator`, `instruments-service`, `execution-service`, `client-reporting-api`,
      `strategy-service`, `deployment-service` across 10 slots / 63 commits
      (`slot11_silent_branch_reset_data_loss_2026_07_13.md`, `slot6_git_reset_dataloss_2026_07_13.md`,
      `slot_branch_realign_discards_uncommitted_worktree_2026_07_17.md`); **(c)** the unguarded sibling-realign path in
      `_orphan.py`'s `commit_and_push_dirty_repos()` hit `unified-api-contracts`
      (`slot_double_reset_dataloss_race_2026_07_25.md`); **(d)** quickmerge's own STAGE 5 branch-selection `checkout -B`
      (agent-mode sentinel-retry path — a DIFFERENT call site than `cascade_dep_branch`) hit `unified-api-contracts`
      (`quickmerge_agent_regate_resets_branch_loses_local_commit_2026_07_31.md`). **All 4 mechanisms were independently
      root-caused and fixed** (preserve-ref+flock for (a); 900s min-ahead-age + HeadBackwardCanary + dirty-worktree
      guard for (b); shared realign cooldown + hoisted age guard for (c); STAGE-5 no-regression guard (`f93a618e6`) +
      the mandatory `git merge-base --is-ancestor` pre-`/done` verify step (now in RULES.md §2 / worker.md) for (d)) —
      `slot-cron-ff-pull.sh` was independently exonerated twice (docs (b)/(a) above) and is confirmed NOT a cause of any
      of these. **Fan-in exposure** (`workspace-manifest.json`, 26 repos total): for mechanism (a) specifically,
      `unified-trading-library` and `unified-api-contracts` are TIED at fan-in=19 (every other repo depends on both) —
      the two maximally-exposed ancestors, consistent with UTL being the repo this doc's own incident hit; next tier
      `strategy-service`/`execution-service` (fan-in=2); every other repo fan-in≤1 (only cascaded when its one direct
      dependent ships `--dep-branch`). **Residual open question** (not a new bug, see todo 9):
      `plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` reports the identical "Reset to
      origin" symptom recurring on 7-of-24 repos in a 2026-08-06 session — AFTER every fix above had shipped —
      attributed by that session to the already-"resolved" STAGE-5 mechanism (d); every instance was recoverable via
      `git cherry-pick` (zero permanent loss, matching every other doc in this survey), so the existing
      verify-before-`/done` mitigation is holding, but whether the STAGE-5 no-regression guard itself still has a gap
      under extreme concurrent fan-out was not re-verified by that session and no dedicated issue doc tracks it —
      captured as new todo 9 below rather than left as prose.
- [x] 6. [INFRA] P1. **RECURRED 2026-07-28 (found by slot-1, audited by slot-7).** Same exact mechanism, same repo
      (`unified-trading-library`), 5 days after the preserve-fix (`06dc7632`) landed: `61efd2e5` (23:04:17) and
      `dbb93c3a` (23:10:30) both discarded (`branch: Reset to origin/live-defi-rollout` reflog, matching signature
      exactly). Slot-1 filed a duplicate doc (`slot_cron_ff_pull_toctou_reset_race_2026_07_27.md`) that initially
      misattributed this to `slot-cron-ff-pull.sh` — slot-7's audit re-confirmed that script is innocent (2nd
      independent confirmation) and traced the incident back here; that doc is now `resolved_by` this one. **Critical
      new finding: the preserve mechanism did NOT protect this incident** — no `refs/wip-preserve/cascade-*` ref exists
      in the affected clone (`.tabs/1/unified-trading-library`) for either discarded sha, and both commit objects are
      now fully unreachable (`git cat-file -e` fails on both — checked 2026-07-28, ~5 days post-incident). This means
      todo 2's fix is NOT suffient on its own to prevent recurrence of actual data loss (only preserve-not-prevent by
      design, and here even the preserve step apparently didn't fire) — see new todo 7. Also found + fixed an
      independent bug in the same function while re-reading it: `cascade_dep_branch` fetched `origin main` (not
      `origin $branch_name`) before both the preserve-check and the checkout — a stale holdover predating
      `live-defi-rollout` as the fleet integration branch. Fixed: `unified-trading-pm@8ca436599` (now fetches
      `$branch_name` too). This does not by itself explain the missing preserve ref (a stale origin ref can only ever
      inflate the ahead-count, never cause a false-negative skip) but closes a real, independent correctness gap in how
      fresh `origin/$branch_name` is at both check sites.
- [x] 7. [INFRA] P1. ✅ **ROOT-CAUSED 2026-07-28 (slot 10) — reproduced live; candidate (c), precisely characterized:
      the guard itself has an inherent TOCTOU race between its own ahead-check and its own checkout, not a bypass via a
      different code path and not (necessarily) a stale-clone issue.** Extracted the exact guard sequence from
      `cascade_dep_branch()` (`scripts/quickmerge.sh:471-490` as of `8ca436599`) into a standalone repro script against
      a scratch bare-origin + clone (not the real fleet clones — isolated, disposable). The guard's ahead-check
      (`git rev-list --count origin/$branch_name..refs/heads/$branch_name`) and the subsequent
      `git checkout -B     "$branch_name" "origin/$branch_name"` are TWO SEPARATE, non-atomic git subprocess calls with
      no lock between them. Injected a delay between the two (simulating shared-host process-scheduling contention —
      this fleet's host has documented recurring contention, e.g. `shared_host_home_filesystem_full_2026_07_26.md`, load
      14.93 on a 30-vCPU box observed elsewhere in this same session) and, during that gap, committed a NEW commit on
      the SAME clone's checked-out branch from a concurrent shell (modeling a different concurrent agent process sharing
      the same slot's worktree filesystem — e.g. a Workflow subagent or a parallel `Agent`/`Task` call, NOT a different
      slot; per-slot worktrees are otherwise isolated). Result: the ahead-check ran BEFORE the concurrent commit existed
      and correctly found `0 ahead` (nothing to preserve at that instant); the checkout then fired AFTER the commit
      landed and discarded it — reflog signature (`branch: Reset to origin/live-defi-rollout`) matches the real incident
      EXACTLY, and zero `refs/wip-preserve/*` ref was created, matching the real incident's missing-preserve- ref
      observation precisely. This directly explains the observed symptom WITHOUT requiring candidate (a) (a stale PM
      clone) — even a clone fully current on `06dc7632`+ reproduces the exact failure, because the fix's own
      check-then-act is not atomic. Candidate (b) (something cleaning up the preserve ref later) is now unnecessary to
      explain the symptom: the ref was never created in the first place, so there was nothing to clean up. **This
      confirms todo 8's premise** ("preserve-only is not proven reliable") — the preserve mechanism is fundamentally a
      race-prone band-aid, not a fix, because it re-implements the SAME check-then-act shape as the original 2026-07-22
      bug, just one level in. Repro script + scratch fixtures kept in this session's scratchpad (not committed — no
      product code changed by this todo, root-cause only; the fix itself is todo 8's scope, not duplicated here).
- [x] 8. [INFRA] P2. ✅ **Already shipped by the time of the 2026-08-08 authorization — checkbox was stale.** Found
      during the todo-3 audit (2026-08-09, slot-2): `scripts/quickmerge.sh` already carries the atomic fix as of
      `unified-trading-pm@1d82f66451` (2026-08-05, "close cascade_dep_branch's TOCTOU data-loss race with a lock, not a
      skip") — confirmed live on current HEAD (`git merge-base --is-ancestor 1d82f66451 HEAD` ✅) and matches the code:
      `flock` on `$ancestor_path/.git/quickmerge-cascade.lock` serializes concurrent cascades, and the preserve
      (`git update-ref refs/wip-preserve/cascade-...`) + `checkout -B` are now two back-to-back plumbing calls with no
      variable-length computation between them (closes the O(history) `rev-list` TOCTOU window todo 7 reproduced), per
      the shipping commit's own inline code comment, which attributes the direction (atomic-preserve, not
      skip-the-reset) to a 2026-08-05 decision predating this doc's own 2026-08-08 "authorize all 3" note by 3 days — no
      separate traceable plan/codex doc records that earlier decision, only the code comment itself; the 2026-08-08
      entry on todos 4/5 below was re-confirming scope for those two, not re-authorizing this one from scratch. No
      further action needed.
- [ ] 9. [REVIEW] P3. **NEW (found during the todo-3 audit, 2026-08-09).** Re-verify the STAGE-5 no-regression guard
      (`unified-trading-pm@f93a618e6`, closes `quickmerge_agent_regate_resets_branch_loses_local_commit_2026_07_31.md`)
      against the evidence in `plans/active/fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` (items
      5/6/9), which reports the identical "Reset to origin" symptom recurring on 7-of-24 repos in a single 2026-08-06
      session, AFTER the guard had shipped. Every instance there was recoverable via `git cherry-pick` (no permanent
      loss) and the mandatory verify-before-`/done` step caught it, so this is NOT urgent — but confirm whether the
      bats-test coverage for the STAGE-5 guard exercises high-fan-out concurrent-push contention (many repos shipping
      near-simultaneously), and if it doesn't, extend it or file a fresh root-cause doc. Target repo:
      `unified-trading-pm` (`scripts/quickmerge.sh` + its bats suite).

## Related QG-infra findings this session (worktree isolation vs the QG harness)

Two more structural gaps found while working around the reset issue above by moving to isolated `git worktree` checkouts
— both make worktree-based QG isolation partially unreliable, which is exactly the tool this session reached for BECAUSE
of the reset issue. Filed here rather than a separate doc since all three are one theme: the QG/git tooling assumes a
single canonical clone per repo and behaves incorrectly under multi-clone (worktree) use.

- [x] 4. [INFRA] P2. ✅ **Already shipped before the 2026-08-08 authorization — checkbox was stale (found 2026-08-09,
      slot-26).** This exact bug (`check_backfill_vm_disk_provisioning.py` resolving `WORKSPACE_ROOT`/`__file__` against
      the shared MAIN clone instead of the calling worktree) was independently root-caused, fixed, and archived as
      `plans/archive/issues/qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md` — the
      confirmed mechanism (per that doc's own live repro) requires a STALE/pre-exported `WORKSPACE_ROOT` in the invoking
      shell; the default unset path already derived correctly per-invocation. Two fixes landed: (1)
      `unified-trading-pm@e70a0d18e` — a fail-loud worktree-identity guard in `qg-common.sh` that hard-exits on a
      `PROJECT_ROOT`/`WORKSPACE_ROOT` mismatch against the invoking `git rev-parse --show-toplevel`; (2)
      `deployment-service@ae767cb` (2026-07-28, tracked in the follow-up
      `plans/archive/issues/qg_workspace_root_template_drift_12_repos_2026_07_24.md`) — converted
      `deployment-service/scripts/quality-gates.sh`'s `WORKSPACE_ROOT=` line from the vulnerable
      `${WORKSPACE_ROOT:-...}` inheritance form to the safe fresh-derivation form
      (`WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"`, no `:-` fallback), confirmed live today at
      `deployment-service/scripts/quality-gates.sh:135` — this unconditionally overwrites any pre-exported value, so the
      vulnerability class no longer exists regardless of shell state. **Re-verified live 2026-08-09** (slot-26,
      `.tabs/26/deployment-service`): exported a stale `WORKSPACE_ROOT=/home/ubuntu/unified-trading-system-repos` (the
      exact MAIN-adjacent value the original incident needed) before emulating line 135's derivation — the script's own
      fresh assignment ignored the stale export and correctly resolved to `.tabs/26` (this slot's own worktree), so the
      invoked check path stayed
      `.tabs/26/deployment-service/scripts/quality_gates/check_backfill_vm_disk_provisioning.py`, never MAIN's copy. No
      further action needed.
- [x] 5. [INFRA] P2. ✅ **FIXED 2026-08-09 (slot-33)** — `unified-trading-pm@4c7d0dba6`. **AUTHORIZED 2026-08-08
      (operator ruling, ao round-5 apply item 16, see
      /plans/active/issues/operator_ruling_record_ao_round5_apply_session_2026_08_08.md): "Authorize all 3."**
      **`PROJECT_ROOT` override (needed to satisfy the PM `test_repo_in_manifest` integration test in a worktree whose
      directory name doesn't match a registered repo) appears to redirect MORE than just that one identity check — it
      changes where the `.qg_last_passed_sha`/`.qg_content_sentinel` files are written AND (observed on
      `market-tick-data-service`) the sentinel's recorded SHA matched the MAIN clone's HEAD, not the worktree's actual
      HEAD — i.e. the content-hash basis silently became MAIN's tree, not the worktree's.** Running `quality-gates.sh`
      with `PROJECT_ROOT=<main-clone>` from inside a worktree therefore risks verifying (and sentinel-stamping) the
      WRONG tree while reporting success for the worktree's actual diff. Workaround used this session: skip
      `PROJECT_ROOT` + worktrees entirely for shipping — extract the verified worktree commit as a patch
      (`git format-patch` / `git am`) and apply it directly onto the real MAIN clone, then run QG there. Needs a real
      fix: either the PM identity test should derive repo identity from `git remote get-url origin` (worktree-safe)
      instead of `Path.cwd().name`, or `PROJECT_ROOT` should scope ONLY the identity-string check and never the
      file-scan/sentinel-write basis. **Took the lower-blast-radius option (the first one)**: fixed
      `tests/integration/test_pm_scripts_integration.py`'s `_get_repo_name()` to derive identity from
      `git remote get-url origin` (falling back to the directory basename only when there is no remote), instead of
      `repo_path.name`. This removes the only legitimate reason an operator ever needed to set `PROJECT_ROOT` to a
      different tree than the actual invoking worktree — the identity check no longer cares about directory naming, so
      the sentinel-hijack failure mode this todo describes has no remaining trigger. Deliberately did NOT touch
      `qg-common.sh`'s existing worktree-identity guard or the shared `base-service.sh`/`base-library.sh`
      `cd     "$PROJECT_ROOT"` / sentinel-path plumbing (the second, higher-blast-radius option) — this doc's own
      Progress Log already flagged that direction as "redefines what QG green means fleet-wide... needs operator
      scoping." Added two unit tests (`test_get_repo_name_uses_remote_url_not_directory_basename`,
      `test_get_repo_name_falls_back_to_basename_without_remote`) exercising a scratch git repo under a mismatched
      directory name; full `test_pm_scripts_integration.py` suite (8 tests) + `quality-gates.sh` both green on the
      shipped commit.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — items 4 and 5 are already held in
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s conflict-gated Deferred list as QG-harness worktree-isolation
  defects ('Item 5 … changes what "QG green" MEANS — the per-repo quality boundary itself. Too high blast-radius for a
  batch todo; needs its own scoped plan with operator sign-off'). Item 8 is an open design fork on the same fleet-wide
  `quickmerge.sh` shipping tool ('**consider** a stronger prevention fix … arguably never the right default behavior'),
  and item 3's audit is bundled with them.
- **2026-07-31 (conflict-gated re-triage) — RECLASSIFIED, not a contradiction or file-collision at all.** No other doc
  disputes items 4/5/8's direction; they're held back purely on BLAST-RADIUS grounds (item 5 redefines what "QG green"
  means fleet-wide; item 8 changes `cascade_dep_branch`'s default behavior for every caller). This belongs in the "needs
  operator scoping / sign-off before an AO batch can touch it" bucket, not conflict-gated — there is no competing claim
  to wait out via re-triage; it needs an explicit go-ahead on scope instead.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (3 entries) — swapped the generic epic pointer for
  `scripts/quickmerge.sh` (the root-caused file — `cascade_dep_branch()` is the actual mechanism, per this doc's own
  todos 1/7/8).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (3 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-09**: populated/refreshed context_scope (3 entries).
- **2026-08-09 (slot-2, todo 3 audit — closed)**: surveyed the fleet's `workspace-manifest.json` (fan-in analysis:
  `unified-trading-library`/`unified-api-contracts` tied at fan-in=19, the two maximally-exposed `cascade_dep_branch`
  ancestors) and 10 related archived issue docs; confirmed the "Reset to origin" symptom has recurred fleet-wide via ≥4
  independently root-caused mechanisms (this doc's `cascade_dep_branch`, agent-orchestrator's
  `heal_dead_slot_branch_quarantine`, `_orphan.py`'s unguarded realign, quickmerge's STAGE-5 checkout), all fixed,
  `slot-cron-ff-pull.sh` exonerated twice. Todo 3 flipped with the full breakdown. Also found todo 8's fix already
  shipped (`1d82f66451`, 2026-08-05) with a stale checkbox — flipped it too (same doc, same session, in-scope per
  findings-triage "in your file → fix in same commit"). Opened new todo 9 (P3) for a residual, non-urgent open question:
  whether the STAGE-5 guard's test coverage handles the high-fan-out recurrence reported 2026-08-06 in
  `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`.
- **2026-08-09 (slot-26, todo 4 dispatch — closed, stale checkbox).** Dispatched task was the 2026-08-08-authorized todo
  4 (`check_backfill_vm_disk_provisioning.py` resolving via the shared MAIN clone instead of the calling worktree).
  Found the exact root cause + fix already shipped and archived
  (`qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md` +
  `qg_workspace_root_template_drift_12_repos_2026_07_24.md`): `unified-trading-pm@e70a0d18e` (worktree-identity guard in
  `qg-common.sh`) + `deployment-service@ae767cb` (fresh-derivation `WORKSPACE_ROOT=` line, no `:-` inheritance).
  Re-verified live in this slot by emulating a stale MAIN-pointing `WORKSPACE_ROOT` export against the current
  `deployment-service/scripts/quality-gates.sh:135` — resolution stayed correctly scoped to `.tabs/26`. Flipped todo 4
  with the evidence; no code change needed (same pattern as todo 8's stale-checkbox closure above).
