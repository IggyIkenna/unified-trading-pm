---
doc_type: issue
title:
  "cloud-build-router's shared concurrency group silently CANCELS a repo's build dispatch when multiple repos merge to
  main in a short window — instruments-service's post-merge image build never fired, with no error surfaced anywhere"
summary: >-
  Discovered immediately after unblocking instruments-service PR #983 (sit-gate/fleet-green issue, see
  sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md) — once that PR merged to main (656ac467, 2026-07-27
  13:01:29Z), several OTHER ldr_main repos' promote PRs also merged within the same ~4 min window (the manual fleet-
  promoter trigger processed the whole backlog at once). Each merge's quality-gates-v2 run fires a `repository_dispatch`
  to unified-trading-pm's `cloud-build-router.yml`, which builds the Docker image via Cloud Build. That workflow's
  concurrency group is `${{ github.workflow }}` — a SINGLE shared group across ALL repos, not per-repo — so the flood of
  near-simultaneous dispatches canceled each other's in-progress runs before they reached the `gcloud builds triggers
  run` step. instruments-service's own dispatch (fired ~13:02:00Z) was one of the casualties: `gh run list` showed 6
  cancelled cloud-build-router runs in the 13:01-13:03 window, and NO Cloud Build ever appeared for instruments-service
  (`gcloud builds list` stayed unchanged at the last 2026-07-26 build for ~5 min after the merge, while
  market-tick-data-service, deployment-service, and unified-trading-library — whose dispatches survived the race — DID
  get fresh builds). No error, alert, or PR comment flagged the drop; it is silent by construction (a cancelled workflow
  run is not a failure in GitHub's UI unless someone is watching the Actions tab for that specific repo). Manually
  re-triggered via `gcloud builds triggers run instruments-service-prod --branch=main
  --substitutions=..._SHA=656ac46756a1c38542f81d93751a6381f98aee84...` (build d06da209-8d08-4e77-a64f-ca8a5bdccadb) as
  the unblock.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci-cd, cloud-build-router, concurrency, deployment, silent-failure, fleet-promoter]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/active/issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md,
    /plans/archive/issues/sports_is_daily_enum_backfill_oom_at_32gi_ceiling_2026_07_27.md,
  ]
created: 2026-07-27
priority: P1
parent_epic: infrastructure_master
source:
  [
    "Surfaced while verifying instruments-service's post-merge Cloud Run image deploy (slot-13, 2026-07-27) — the build
    silently never fired after PR #983 merged.",
  ]
execution_scope: orchestrator-agent
drift_direction: none
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# cloud-build-router's fleet-wide concurrency group drops build dispatches under merge-pileup load

## What I found

1. `cloud-build-router.yml` (unified-trading-pm) uses `concurrency: group: ${{ github.workflow }}` — this is a SINGLE
   group name for the whole workflow, shared across every repo that dispatches to it. It is not scoped per-repo (e.g.
   `group: cloud-build-router-${{ github.event.client_payload.repo }}`).
2. When multiple `ldr_main` repos' LDR→main promote PRs merge within the same few minutes (exactly what happens when the
   fleet promoter is run manually and drains its whole backlog, or even under normal `*/5` cron cadence if several repos
   happen to be ready at once), each merge's `quality-gates-v2` fires its own `repository_dispatch` →
   `cloud-build-router` run. Because they share one concurrency group, a LATER dispatch cancels an EARLIER one still in
   progress (`cancel-in-progress` behavior) — before the earlier run reaches its `gcloud builds triggers run` step.
3. Confirmed via `gh run list --repo IggyIkenna/unified-trading-pm --workflow=cloud-build-router.yml` in the
   2026-07-27T13:01-13:05Z window: 6 runs show `conclusion: cancelled`, several before even reaching the "Determine
   build target" log step. `gcloud builds list --project=central-element-323112` confirmed instruments-service got NO
   new build in this window while market-tick-data-service, deployment-service, and unified-trading-library (whose
   dispatches happened to survive) did.
4. This is silent: no Slack alert, no PR comment, no re-queue. The only visible symptom is "the deployed Cloud Run image
   is stale" — which nobody would notice without independently diffing the image's build timestamp against the merge
   timestamp, exactly what this investigation had to do manually.

## Why it matters

Every `ldr_main` repo's post-merge deploy silently depends on being the "last" dispatch in whatever window the shared
concurrency group serializes — under normal single-repo-at-a-time traffic this rarely bites, but the fleet promoter
(this session's manual trigger, or any busy period where several repos' promote PRs go green together) reliably produces
exactly this collision. A repo can sit on a stale deployed image indefinitely with every CI signal green (PR merged,
quality-gates-v2 passed) — this is a bigger blast radius than the sit-gate issue filed alongside this one, because it
affects the LAST mile (does the fix actually run in prod) with zero observability.

## Recommended decision

- [x] [INFRA] P1. ✅ — unified-trading-pm@\<sha\>. RE-DIAGNOSED during implementation: `cloud-build-router.yml`'s own
      top-level `concurrency: group: ${{ github.workflow }}` was ALREADY fixed to
      `cloud-build-router-${{ github.event.client_payload.repo || github.run_id }}` (`cancel-in-progress: false`) back
      on 2026-06-25 (3dadfdbd9) — verified identical on `main` (blob `3f5d0919f` matches live GitHub HEAD). Yet
      `gh run list` confirmed cancellations STILL occurring on 2026-07-27 (e.g. runs 30268363605/30268379563/... in the
      13:01-13:17Z window), and every cancelled run's job list showed ONLY `freeze-check / check` — it never reached
      `route-build`. Root cause: the shared `change-freeze-check.yml` reusable workflow (called via `uses:` by
      `cloud-build-router.yml`, `cloud-build-router-aws.yml`, `freeze-deferred-build-replay.yml`, and
      `overnight-agent-orchestrator.yml`) carried its OWN top-level
      `concurrency: group: ${{ github.workflow }}-${{     github.ref }}` with `cancel-in-progress: true` — since
      `repository_dispatch` always fires against the same default-branch ref, EVERY caller (regardless of which repo's
      build it was gating) collided into ONE shared group (`Change Freeze Check-refs/heads/main`), so any new caller's
      freeze-check cancelled whichever OTHER caller's freeze-check was still in-progress, cancelling that caller's
      entire run (`route-build` needs: freeze-check). This is the actual mechanism that dropped instruments-service's
      dispatch, not the top-level group this todo originally named. Fix: removed the concurrency block from
      `change-freeze-check.yml` entirely — it's a stateless, read-only CSV/time check with no shared state to protect,
      so there is no correctness reason to serialize it, and confirmed no other `workflow_call` reusable in this repo
      shares this footgun (grepped for `group:.*github.workflow.*github.ref` + `workflow_call:` co-occurrence — only
      this file matched with multiple distinct callers). Same-repo dispatches still serialize via
      `cloud-build-router.yml`'s own per-repo group, unaffected by this change.
- [x] [INFRA] P2. ✅ — unified-trading-pm@e617c930b. Added `scripts/cicd/check_image_deploy_staleness.py` +
      `.github/workflows/image-deploy-staleness-check.yml` (schedule `*/30`): compares each fleet repo's `main` HEAD
      commit timestamp against its `:latest` image's push timestamp in Artifact Registry (via
      `gcloud artifacts docker images list --format=json`, the `updateTime` field — `docker images describe` was
      verified live to carry NO timestamp field at all), alarms via `notify-slack.yml` (dedup_key `image-deploy-stale`,
      cooldown 60min, WARNING) when the gap exceeds the expected build+dispatch latency. Fail-open per-repo on
      uncertainty; an all-UNKNOWN run is its own distinct alarm (never silently read as "0 stale"). Verified end-to-end
      live against real `gh`/`gcloud`: corrected two wrong assumptions found during implementation — the real AR docker
      repo is `unified-trading-system` (not `unified-trading` as the `cloud-build-router.yml` substitution name
      implied), and `agent-orchestrator` is excluded from the fleet list (it runs as a VM process, not a Cloud Run
      image, so it has no package in this AR repo — including it would make every run report a permanent false UNKNOWN).

## Codex SSOTs

- `/codex/08-workflows/ci-cd-flow.md` — the documented promote→build→deploy chain this concurrency bug breaks a link in;
  now also carries § "Image-deploy staleness check" documenting the P2 reconciliation check.
