---
doc_type: issue
title: >-
  SIT gate compares sit_validated_tree against the MOVING LDR tip — a breaking-delta repo can block indefinitely; the
  obvious retarget fix is unsafe under squash promotion
summary: >-
  On the SIT-gate fail-closed path the promoter requires sit_validated_tree == the tree of the LIVE live-defi-rollout
  tip, re-read fresh every tick. SIT clones LDR at its own start and stamps that tree, so convergence needs LDR
  quiescent across a ~156-min SIT round-trip; every miss costs another full round and each surviving tick re-dispatches
  SIT. The frozen per-SHA promote ref does NOT mitigate this — it is created ~175 lines and one early-return AFTER the
  gate. LATENT today (agent-orchestrator is non-breaking so it takes the fast path), it bites when a SIT-covered repo
  carries a genuinely breaking delta. The intuitive fix (retarget the promote to the validated ancestor) was designed
  and then REJECTED by adversarial review on two independently-verified fatal grounds — recorded here so it is not
  re-derived and re-attempted.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, system-integration-tests, agent-orchestrator]
scope: [engineer, admin]
tags: [ci-cd, sit, promotion, ldr-main, race-condition, quality-gates]
related:
  [
    /plans/active/issues/uac_value_only_config_change_breaks_utl_untested_2026_07_20.md,
    /plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md,
  ]
created: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  [
    "surfaced 2026-07-20 while fixing the agent-orchestrator promote deadlock (breaking_scan_dir); the treadmill is the
    SECOND half of that gate's problems",
  ]
locked_by:
locked_since:
resolved_by:
---

# The SIT gate races a moving branch

## The defect

`ldr-to-main-promote-fleet.yml` reads the live LDR tip fresh each tick:

```
LDR_COMMIT_JSON=$(gh api "repos/$OWNER/$REPO/commits/live-defi-rollout")   # :459
LDR_TREE=$(... .commit.tree.sha ...)                                        # :461
```

and on the fail-closed path requires strict equality against the SIT stamp:

```
if [ "$SIT_STATUS" != "FAILING" ] && [ -n "$SIT_TREE" ] && [ "$LDR_TREE" = "$SIT_TREE" ]; then   # :606
```

SIT independently clones LDR at ITS start (`full-workspace-sit.yml:72-77`) and stamps whatever tip it saw (`:173`, a git
TREE sha). The dispatch payload carries **no SHA or tree pin** (`:617`), so SIT always validates "whatever LDR is now",
not "the tree the promoter wants gated". Convergence therefore requires LDR to be quiescent from SIT's clone until the
next promoter tick's read.

**The frozen-head ref does not help.** `PROMOTE_HEAD` at `:469` is only a NAME; the ref is POSTed at `:781-787` — after
the gate at `:606` and after the fail-closed `_done BLOCKED; return 0` at `:621`. It is a TOCTOU fix for the window
between gate-pass and async auto-merge, not for the SIT race.

Correction to the original framing: this is **probabilistic, not provably unsatisfiable**. A no-op backmerge pushes
nothing and SIT is 30-min-capped, so a window does exist. But each miss costs a full ~156-min round-trip
(`branch-health.yml:107-110` names agent-orchestrator, 3 rounds on 2026-07-18) and every surviving tick re-dispatches
SIT (`:615-619`).

## Why the intuitive fix is WRONG — do not re-attempt without addressing both

A "validated-ancestor retarget" (promote the validated commit instead of the live tip) was designed and then refuted.
Both objections were independently verified on 2026-07-20:

1. **Squash promotion means the range never shrinks (FATAL).** Promotion squash-merges, so no LDR commit is ever an
   ancestor of `main`. MEASURED on agent-orchestrator: `git rev-list --count origin/main..origin/live-defi-rollout` =
   **189** across 5 consecutive `chore(promote)` squashes, and
   `git merge-base --is-ancestor origin/live-defi-rollout~20 origin/main` returns NOT-ancestor. A retarget resolving via
   `git rev-list origin/main..$LDR_SHA` would therefore re-select an ALREADY-PROMOTED commit on every future tick. The
   tree-equality content gate is what actually detects "already promoted"; commit ancestry cannot.
2. **The required status check would be stranded (FATAL).** `sit-gate/fleet-green` is POSTed against `$LDR_SHA` at
   `:499-506`, ~100 lines BEFORE the gate at `:606`, and it is a REQUIRED branch-protection context for every `ldr_main`
   repo (`scripts/repo-management/pin_branch_protection_rulesets.py:343`). Reassigning `$LDR_SHA` at the gate leaves the
   required check on the wrong SHA, so every retargeted PR blocks on a permanently-missing check — **the exact
   permanent-deadlock class the `breaking_scan_dir` fix removed the same day.** Nine other `$LDR_SHA` references
   downstream would also need auditing.

Any retarget design must move the `sit-gate/fleet-green` POST to after the gate AND use tree-equality (not ancestry) to
decide "already promoted".

## Candidate directions (none adopted yet)

- **Pin the SIT dispatch to a SHA** — make the stamp deterministic (`full-workspace-sit.yml` accepts a sha in
  `client_payload`, clones that sha, stamps its tree). Necessary but NOT sufficient on its own: the gate still re-reads
  the live tip at `:459`, so the race survives unless the gate side changes too.
- **Retire `staging-backmerge-to-ldr` for `ldr_main` repos** — the fleet header lists the staging-lock fold-away as
  still-REMAINING Phase-1 work, so this hourly cron is vestigial for direct-promote repos. Removes churn; **hygiene, not
  the fix** — quickmerge traffic alone can still outpace a 156-min round-trip.
- **Promote lease / enforced quiet window** — hold LDR still while SIT runs. Correct but expensive; contends with the
  multi-slot worker model.
- **Tighten cadence** — does not change the race, only its odds.

## Todos

- [ ] [DEVOPS] P2. Decide the direction (lease vs SIT-sha-pin + gate-side change vs accept-and-monitor) and record the
      ruling here. Do NOT ship a retarget without addressing BOTH fatal objections above.
- [ ] [DEVOPS] P2. If a retarget is chosen: move the `sit-gate/fleet-green` POST (`:497-511`) to after the SIT gate
      closes (after `:622`) so it always lands on the final PR head, and assert the PR head carries that status before
      arming auto-merge.
- [x] ✅ [DEVOPS] P3. Retire `staging-backmerge-to-ldr` for `ldr_main` repos as separate hygiene, explicitly labelled
      NOT the treadmill fix. **SHIPPED (verified 2026-07-25, plan-reconcile)**: `unified-trading-pm@a7b5cc27c` (verified
      ancestor of `origin/live-defi-rollout` via `git merge-base --is-ancestor`) commented out
      `staging-backmerge-to-ldr.yml`'s hourly `schedule: "10 * * * *"` fleet-wide (24 repos), keeping `push:[staging]` +
      `workflow_dispatch` self-resume — via `plans/active/github_actions_staging_machinery_shutdown_2026_07_24.md` (a
      separate, unrelated plan; no cross-reference existed between the two docs until now).
- [ ] [DEVOPS] P3. Add a regression test / monitor that fires when a repo has been SIT-BLOCKED for N consecutive ticks —
      the treadmill is currently only visible as a promotion-lag alert, which reads as slowness rather than a stuck
      gate.
- [ ] [DEVOPS] P2. Distinct sub-finding (2026-07-25, not the moving-tree race itself): when two `SIT-on-LDR` dispatches
      for the same repo overlap (e.g. two promote-fleet ticks within the concurrency-group's cancellation window), the
      OLDER dispatch gets `cancelled` by `system-integration-tests`'s concurrency group, but its `state=failure` status
      can still be POSTED to the LDR commit AFTER a newer, actually-`success` run's own status — clobbering a real green
      result with a stale red one. Live-measured 2026-07-25: run `30158515857` reached `conclusion=success` at
      `12:50:49Z`; run `30158518796` (an older, overlapping dispatch) was `cancelled` but posted `state=failure` to the
      SAME commit at `12:51:02Z`, 13s later, becoming the commit's latest/authoritative status. Fix direction: either
      have the status-posting step no-op when its own run was `cancelled` (a cancelled run has no informative verdict to
      report), or key the posted status's `created_at`-ordering off run START time / a monotonic dispatch counter
      instead of POST-call completion order so a late-posting stale run can't overwrite a fresher good one. (repo:
      unified-trading-pm, `.github/workflows/ldr-to-main-promote-fleet.yml` and/or
      `system-integration-tests/.github/workflows/full-workspace-sit.yml`'s status-post step)

## Progress Log

- **2026-07-25 (later session) — concrete impact confirmed: agent-orchestrator's dashboard has not deployed in ~5
  days.** `agent-orchestrator`'s `live-defi-rollout` was measured 331 commits ahead of `main` (0 behind) with `main`'s
  last commit dated `2026-07-25T11:11:57Z` despite `ldr-to-main-promote-fleet.yml` running successfully every 10-15 min
  in between (confirmed `agent-orchestrator` logged "READY... all deps on main" every tick but the run summary only ever
  lists OTHER repos under "Promoted" — consistent with this doc's own dated comment in the workflow: "Measured
  2026-07-20: agent-orchestrator 25 files / 7 commits un-promoted with NO open PR... tripping branch-health every cycle;
  deployment-ui and unified-trading-system-ui carry the identical latent hole"). Practical consequence:
  `deploy-dashboard.yml` triggers only on push to `main`, so NO dashboard UI change has actually reached production in
  that window — an operator-visible feature (backlog-detail-table columns) landed on LDR the same day and was invisible
  until this was diagnosed. **Workaround used (not a fix for this doc's underlying race)**:
  `gh workflow run deploy-dashboard.yml --ref live-defi-rollout -f target=prod` — dispatches the SAME deploy workflow
  directly against the LDR tip, bypassing the stuck main-promotion gate entirely (the dashboard build/deploy step
  touches only the static frontend bundle, nothing in the SIT-gate/promotion logic itself, so this carries none of the
  risk a code-level workaround would). Confirmed working end-to-end. **This is a safe, repeatable stopgap for
  `agent-orchestrator`/`deployment-ui`/`unified-trading-system-ui` specifically** (the three repos this doc's own
  2026-07-20 comment already names as carrying the identical latent hole) until the direction ruling above is made —
  worth considering as an interim mitigation in its own right (a scheduled `workflow_dispatch` against LDR for
  dashboard-only repos) even independent of fixing the underlying SIT-gate race, since a stale-but-correct dashboard
  deploy is lower-risk than a stuck one.
- **2026-07-20** — Surfaced while fixing the `breaking_scan_dir` deadlock. A separate, INDEPENDENT correctness bug found
  in the same gate was fixed immediately (the AST differ diffed the branch NAME via its own second fetch, so it could
  classify a different tree than the one gated and frozen; now pinned to `$LDR_SHA`, fail-closed if unreachable).
  Demonstrated live: agent-orchestrator at `origin/live-defi-rollout~40` reports `is_breaking=True` (385→375 exports)
  while the live branch reports `is_breaking=False` — the same repo, opposite verdicts, which is exactly the silent
  direction (a breaking delta judged on a snapshot that does not contain it → promoted ungated). The treadmill itself is
  left OPEN pending a direction ruling.
- **2026-07-25 (slot 8, backend_engineer)** — Hit this live while trying to get `deployment-api@3fea307` (the
  wrong-gunicorn-file fix, see `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md` todo 5 part 1)
  promoted LDR→main so its follow-up verification could proceed. Manually dispatched `ldr-to-main-promote-fleet`
  (`workflow_dispatch`) twice, ~5 min apart, to speed past the scheduled cadence. Both times the gate logged
  `SIT GATE BLOCK deployment-api: true-delta not SIT-validated on this tree ... fail-CLOSED. Dispatching SIT-on-LDR`
  with a DIFFERENT `sit_validated_tree` each time even though `deployment-api`'s own LDR tree (`9a9fa61c...`) never
  changed across the whole ~15-min window — confirms the doc's framing: the gate is racing the WHOLE workspace's moving
  state, not just this one repo's delta. Concretely observed the compounding failure mode described above but not
  previously measured: my FIRST manual dispatch's `SIT-on-LDR` re-dispatch produced 3 near-simultaneous
  `full-workspace-sit` runs (`system-integration-tests` concurrency group), 2 of which got `cancelled`; the one that
  actually reached `conclusion=success` (`30158515857`, ~4.5 min runtime) never got its status posted to the LDR commit
  — a _later_-dispatched-but-earlier-CANCELLED run's status (`conclusion=cancelled` → posted as `state=failure`) landed
  on the commit instead, timestamped AFTER the real success (`created_at=12:51:02Z` for the cancelled run's status vs
  the success run completing at `12:50:49Z`). i.e. repeated manual re-dispatch while a validation is already in flight
  doesn't just risk missing the moving-tree window — it can make an already-GOOD result invisible by racing a stale
  status POST over it. Second (cleaner, single, non-overlapping) dispatch cycle DID correctly post
  `sit-gate/fleet-green=success` on the right commit, but the gate still blocked on the SAME tree-mismatch pattern
  immediately after because the workspace digest had already moved again (`712f97a1d9...` at 12:45:56 →
  `c7a8ce88978e...` at 12:58:10, ~12 min apart, no dispatch of mine in between explains the second value). Net: backed
  off from further manual dispatching (each attempt plausibly extends the treadmill under this fleet's churn rate rather
  than shortening it) and is instead waiting for a natural quiet window per the doc's own "a window does exist" framing
  — did NOT attempt the retarget fix (correctly flagged unsafe above) or any other gate-side change; out of
  backend_engineer craft scope regardless. Adds one more concrete data point for whoever takes the P2 DEVOPS ruling: the
  self-inflicted-status-race sub-finding (a cancelled run's status clobbering an already-successful run's status when
  dispatches overlap) is a DISTINCT, independently fixable bug from the moving-tree race itself — worth its own todo
  line rather than folding into "tighten cadence".
