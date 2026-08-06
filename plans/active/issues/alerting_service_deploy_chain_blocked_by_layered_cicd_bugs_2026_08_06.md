---
doc_type: issue
title: >-
  alerting-service's shipped PagerDuty/dedup fix (4e252b4) has been stuck NOT deployed for hours behind THREE
  independently-discovered, layered CI/CD promotion bugs — tracking doc so the chase isn't lost mid-session
summary: >-
  `alerting-service@4e252b4` (fix: PagerDuty secret-lookup crash, missing email fallback, CONSOLIDATOR_DOWN refire storm
  — see archived `alerting_pagerduty_secret_missing_no_email_fallback_2026_08_06.md`, whose own scope — the code fix —
  is DONE and correctly archived) has been sitting on `live-defi-rollout` since ~10:51 UTC without reaching the live
  `dp-alerting-subscriber` Cloud Run service (confirmed running a 2026-07-28 image — 9+ days stale — as late as 16:00
  UTC). Chasing WHY surfaced three separate, previously-undiscovered CI/CD infrastructure bugs in the LDR->main
  promotion chain, each blocking the next attempt:

  1. **Provenance-marker ancestry bug** — `promote_provenance_range.py`'s `commit_reachable()` checked git-object
     EXISTENCE, not ancestry, so a marker orphaned by the 2026-08-05T11:24:53Z history rewrite still "passed" and
     produced a corrupted ~3,701-commit promotion range. **FIXED + verified**:
     `plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md` (status:
     resolved). Also affected instruments-service/unified-trading-library/market-data-processing-service (those 3
     remain separately blocked by genuine unrelated foreign quickmerge-bypass commits now correctly exposed by the
     fixed range — out of scope, needs operator-authorized bulk-bless per that doc's own precedent).
  2. **SIT-stamp skipped on detached-HEAD bug** — `full-workspace-sit.yml`'s SIT_VALIDATED stamping step required the
     literal branch name `live-defi-rollout`, which a pinned-SHA (detached HEAD) re-validation checkout never
     satisfies, even though tests genuinely passed — an infinite fail-closed loop. **FIXED + verified**:
     `plans/active/issues/sit_stamp_skipped_on_detached_head_pinned_sha_2026_08_06.md` (status: resolved,
     `system-integration-tests@0dc3ff1`).
  3. **Backmerge chicken-and-egg** — `main-backmerge-to-ldr.yml` on `main` references `./.github/workflows/
     notify-slack.yml`, which today's shared-CI-repo-extraction work added to `live-defi-rollout` but never
     backmerged to `main` for every repo — and backmerge is the very mechanism that would fix this, so it's
     self-deadlocking. Confirmed for `alerting-service` (main has `image-build-gate.yml` only, missing
     `notify-slack.yml`) and previously documented for `strategy-service` in
     `plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md`. **IN PROGRESS**
     as of this writing — an agent was dispatched to audit the fleet-wide scope and fix via the explicit
     `.github/**`-must-reach-main carve-out (direct push of the missing file, not quickmerge — quickmerge is what's
     broken). Status not yet confirmed at time of this checkpoint; check that doc + this one's Progress Log for the
     outcome.

  A 4th layer is plausible given the pattern (three found in one session) but was deliberately NOT chased preemptively —
  the dispatched agent was told to report a 4th layer as a finding, not chase it autonomously, to keep this converging.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, unified-trading-pm, system-integration-tests, deployment-service, deployment-api]
scope: [engineer, admin]
tags: [ci-cd, promotion-blocked, deploy-chain, alerting-service, cross-repo, session-tracking]
related:
  [
    /plans/archive/issues/alerting_pagerduty_secret_missing_no_email_fallback_2026_08_06.md,
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
    /plans/active/issues/sit_stamp_skipped_on_detached_head_pinned_sha_2026_08_06.md,
    /plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
    /plans/active/issues/agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md,
  ]
created: 2026-08-06
last_updated: "2026-08-06"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: devops
drift_direction: advance-code
depends_on: []
source: "main-session /autonomous loop, chasing why alerting-service@4e252b4 hadn't deployed, 2026-08-06"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md,
    /plans/active/issues/sit_stamp_skipped_on_detached_head_pinned_sha_2026_08_06.md,
    /plans/active/issues/strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md,
  ]
---

# alerting-service deploy chain — three layered CI/CD bugs found chasing one stuck deploy

## Related, separately-owned work in flight at time of this checkpoint

**`service-deployed` dispatch listener** (a DIFFERENT, parallel fix — makes FUTURE deploys automatic once this chain's
promotion actually clears): shipped and independently verified QG-green — `deployment-service@5599bda8` + `@4a69f9d0`,
`deployment-api` `cloud_run_service_name` override fix — allowlist currently contains exactly
`alerting-service -> dp-alerting-subscriber` (deliberately narrow, default-deny, see the docstring in
`deployment_service/auto_deploy_allowlist.py` for the full reasoning). Tracked in
`post_cutover_silent_assumption_sweep_2026_07_23.md`. This listener's own end-to-end verification (does a real dispatch
actually redeploy `dp-alerting-subscriber`) is ALSO blocked on the same 3-layer chain above — once `4e252b4` reaches
`main` and a fresh image builds, both this issue's success criterion AND the listener's own verification complete
together.

## Todos

- [ ] [CICD] P1. Confirm the fleet-wide backmerge chicken-and-egg fix (layer 3 above) actually landed and unblocked
      `alerting-service` PR (check `gh pr list --repo IggyIkenna/alerting-service --state open` — the PR number will
      have changed again if the fleet bot superseded it further; verify
      `git merge-base --is-ancestor 4e252b4     origin/main` in the `alerting-service` repo).
- [ ] [OPS] P1. Once `4e252b4` is on `main`: verify a fresh Cloud Build for `alerting-service` completes
      (`gcloud builds list --project=central-element-323112 --filter="substitutions._SERVICE_NAME=alerting-service"     --limit=3`),
      then verify the `service-deployed` listener actually fires and `dp-alerting-subscriber`'s Cloud Run revision
      `creationTimestamp` updates to after 2026-08-06
      (`gcloud run services describe     dp-alerting-subscriber --region=asia-northeast1 --project=central-element-323112     --format="value(status.latestReadyRevisionName)"`
      then `gcloud run revisions describe <rev>     --format="value(metadata.creationTimestamp)"`). If the listener does
      NOT fire automatically, manually trigger the deploy once (`deployment-api`'s
      `/api/deployments/alerting-service/deploy` or equivalent) to at least get today's fix live, and treat the listener
      not firing as a NEW bug to file separately.
- [ ] [DEVOPS] P2. If a 4th layered CI/CD blocker surfaces, file it as its own dated issue doc (same pattern as the 3
      above) rather than growing this one indefinitely — cross-link back here.

## Progress Log

- **2026-08-06, main-session /autonomous loop**: filed this tracking doc specifically because the connecting narrative
  ("why does a simple alerting fix need 3 unrelated CI bugs fixed first") existed only in chat and would have been lost
  at the next context compaction. All 3 sub-fixes have their own detailed issue docs (linked above) — this doc is the
  index + the still-open completion criterion (a verified-live deploy), not a duplicate of their content. At time of
  writing: layers 1 and 2 confirmed fixed and verified; layer 3's fix agent was dispatched and had not yet reported
  back; the final end-to-end deploy verification had not yet been attempted.
- **2026-08-06 ~16:10 UTC**: layer 3 (backmerge chicken-and-egg) fix agent resolved `alerting-service` PR #345's
  Dockerfile conflict (took-LDR base-image digest; tree now matches LDR exactly incl. `notify-slack.yml`) — PR is
  `mergeable=MERGEABLE` but `mergeStateStatus=BLOCKED` on the required `sit-gate/fleet-green` check. Two consecutive
  `full-workspace-sit` dispatches (runs `31116696092` @15:50-15:53, `31118400832` @16:05-16:09) both failed identically
  on `cross-repo-invariants` / "Set up job" with `Failed to resolve action download info: Service Unavailable` — **not a
  code or invariant failure**. Confirmed via githubstatus.com: GitHub has an active **major** incident ("Incident with
  Actions", status=investigating, created `2026-08-06T15:22:49Z`) — both failure windows fall squarely inside it. Redi
  rected the fix agent to (a) stop blind-retrying SIT dispatches until GitHub reports the incident resolved, (b) instead
  do the other 6 affected repos' `notify-slack.yml` single-file direct-push to `main` (plain git pushes, unaffected by
  the Actions outage) — full list independently derived via a fleet-wide grep for `main-backmerge-to-ldr.yml`
  referencing `notify-slack.yml` with it absent from `main`: `agent-orchestrator`, `alerting-service` (this PR),
  `batch-live-reconciliation-service`, `client-reporting-api`, `features-service`, `instruments-service`,
  `unified-trading-library`. Also corrected early scope creep: the fix agent had started inspecting
  `agent-orchestrator`'s full LDR→main `git merge-tree`, which surfaces real, unrelated content conflicts across 7+
  files (`dashboard/src/layout.tsx`, `dashboard/src/types.ts`, `server/config.py`, `server/context_lifecycle.py`,
  `server/main_agent_keeper.py`, `server/models/agents.py`, `server/routes/agents.py`) — that full-conflict resolution
  is explicitly OUT OF SCOPE for this layer-3 fix (only the single missing workflow file is in scope via the
  `.github/**`-must-reach-main carve-out); redirected to a blob-level single-file push instead, which has zero conflict
  surface. Will re-dispatch `full-workspace-sit` once the GitHub incident clears.
- **2026-08-06 ~17:20 UTC**: fleet-wide audit sub-agent completed and independently verified — actual scope was **10
  repos** (not 7; my earlier grep missed 3 that lack `notify-slack.yml` on LDR itself, not just on main: `e2e-testing`,
  `execution-service`, `market-data-processing-service`). Raw direct-push-to-main was attempted first (per my earlier
  suggested carve-out) and **rejected fleet-wide by branch protection** (`GH013`, reproduced on 8 repos) — no bypass
  actor configured, so the working mechanism ended up being a PR through the same required-check gate
  (`quality-gates-v2` + `sit-gate/fleet-green`), landing the file on each repo's pending/new promote branch rather than
  main directly. 9 of 10 repos now have `notify-slack.yml` on an open, otherwise-mergeable promote PR, blocked only on
  the same GitHub Actions incident above. `agent-orchestrator` (the 10th) has two additional, unrelated, pre-existing
  problems (a dangling reference to the now-deleted PM reusable-CI-workflow copy, and a genuine multi-file code conflict
  vs LDR) that block it independent of this fix — filed separately per this doc's own todo #3:
  `agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md`. `instruments-service` PR #1092 also
  separately genuinely-failed `quality-gates-v2` (pre-existing, matches the known foreign-quickmerge-bypass list, not
  chased here). Full detail in `strategy_service_ldr_qg_infra_flake_and_promotion_deadlock_2026_08_06.md` § "Fleet-wide
  audit" (commit `21a698c09`). Still waiting on the GitHub Actions incident to clear before any of the 9 can actually
  merge.
