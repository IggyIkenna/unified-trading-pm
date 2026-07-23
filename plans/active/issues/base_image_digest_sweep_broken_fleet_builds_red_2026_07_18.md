---
doc_type: issue
title:
  "digest-drift-sweep.yml never dispatches (cross-repo Contents API authed with repo-scoped GITHUB_TOKEN) → 11 service
  repos pinned to a stale UTL base-image digest → EVERY service Cloud Build is RED on setuptools PYSEC-2026-3447"
summary: >-
  The PM workflow .github/workflows/digest-drift-sweep.yml (cron 0 */6 * * *) is meant to bump each service's Dockerfile
  BASE_IMAGE_DIGEST pin when the UTL base image republishes. It has NEVER dispatched: it authenticates cross-repo GitHub
  Contents-API reads with secrets.GITHUB_TOKEN (the ambient, repo-scoped token), which cannot read another repo's
  contents, so every one of its 16 IMAGE_REPOS logs "Dockerfile not found — skipping" (verified across 4 runs
  07-14→07-18: No ARG found 16 / Dispatched 0 every time). Consequence: 11 service repos are still pinned to UTL base
  digest sha256:b7e391f8… (uploaded 2026-07-13T18:44 UTC, BEFORE the fleet pip-audit fix landed 07-14), so their
  in-image quality-gates.sh runs a stale qg-common.sh whose pip-audit ignore-list lacks PYSEC-2026-3447 → the in-image
  QG (STEP 5 codex compliance) fails on "setuptools 82.0.1: PYSEC-2026-3447" → the Cloud Build push step never runs →
  the service cannot deploy a fresh image. This blocks the deploy leg of ALL affected services (found while trying to
  redeploy ml-service for bucket_fold_ml Phase D). The fresh UTL base :latest sha256:76a15429… (v0.55.0, 07-18T10:36)
  correctly carries the ignore (grep count 2). ml-service was unblocked with a manual pin bump (this session); the other
  10 repos + the broken sweep remain.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    unified-trading-pm,
    ml-service,
    execution-service,
    strategy-service,
    deployment-service,
    agent-orchestrator,
    alerting-service,
    client-reporting-api,
    fund-administration-service,
    greeks-service,
    market-data-processing-service,
    trading-agent-service,
    deployment-api,
  ]
scope: [engineer, admin]
tags: [ci, cloudbuild, base-image, digest, pip-audit, fleet, p1, deploy-blocker]
related: [bucket_fold_ml_2026_07_17.md]
created: 2026-07-18
parent_epic: infrastructure_master
priority: P1
assigned_vm:
resolved_by:
locked_by:
source:
  "Found 2026-07-18 during /autonomous execution of bucket_fold_ml_2026_07_17 Phase D (redeploy ml-service + cite
  cloudbuild=SUCCESS). The redeploy was blocked by a red ml-service Cloud Build; root-cause investigation (read-only
  sub-agent) traced it to this fleet-wide, silently-broken digest-drift-sweep automation."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# digest-drift-sweep.yml broken → 11 service repos stale-pinned → all service Cloud Builds RED (PYSEC-2026-3447)

> **P1 fleet deploy-blocker. NOT a bucket-fold bug** — surfaced because bucket_fold_ml Phase D needs a green ml-service
> build. ml-service was unblocked in-session (manual pin bump `b7e391f8`→`76a15429`, ml-service@5d05c4c); this doc
> tracks the root cause + the 10 other affected repos so the operator can decide on the fleet fix.

> **🟡 SEVERITY CORRECTION 2026-07-22**: this doc's title/summary ("EVERY service Cloud Build is RED") describes the
> **local-build / AWS-CodeBuild** exposure, not GCP. A fleet-wide GCP Cloud Build sweep run today (14/14 service
> triggers, `test_fleet_image_builds_from_current_code_2026_06_17.md` Phase 2) built every repo in this doc's blast
> radius GREEN — `alerting-service`, `client-reporting-api`, `deployment-service`, `execution-service`,
> `fund-administration-service`, `greeks-service`, `market-data-processing-service`, `strategy-service`,
> `trading-agent-service` all SUCCEEDED. Per `unified-trading-library/cloudbuild.yaml` + this workspace's canonical
> build docs, GCP Cloud Build triggers pass `--build-arg BASE_IMAGE_DIGEST=<current>` explicitly at build time — the
> Dockerfile's hardcoded `ARG` default (this doc's actual concern) is only consulted by **local `docker build`** and
> **AWS CodeBuild** (which, per `deployment-api/Dockerfile`'s own comment, does NOT pass that build-arg). The sweep
> itself is still broken (root cause below unchanged) and the pins are still stale — this note only narrows _which build
> paths_ are actually blocked today. **Also**: `deployment-api`'s pin had drifted AGAIN past this doc's
> `e5de3b29`/"likely unaffected" note — found re-stale at `2854ae3d…` vs current `:latest` `4edb1d8c…`, manually bumped
> `deployment-api@2531d925` (same pattern as the ml-service fix, not a fix to the sweep). Cross-ref:
> `digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md` (same root cause, filed 2 days earlier).

## Root cause (evidence)

1. **The QG base scripts are baked into the UTL base Docker image**, not vendored per-repo. UTL `cloudbuild.yaml`
   `clone-pm-scripts` step (`:161-177`) does
   `git clone --depth=1 --branch live-defi-rollout … unified-trading-pm … /workspace/unified-trading-pm` on every
   base-image bake; `unified-trading-library/Dockerfile:84` `COPY . .` bakes it to `/app/unified-trading-pm/…`. Each
   service's thin `scripts/quality-gates.sh` sources
   `${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh` → resolves to that baked copy
   in-image. So a service's in-image QG runs **whatever qg-common.sh was in the base image it is pinned to**.
2. **The fix landed in PM but not in the pinned base image.** PM `qg-common.sh:106` gained
   `--ignore-vuln PYSEC-2026-3447` in commit `3f4fad383` (2026-07-14 11:32 UTC, on main + live-defi-rollout). The fresh
   UTL base `:latest` = `sha256:76a15429…` (07-18T10:36) carries it (proven:
   `docker run … grep -c PYSEC-2026-3447 /app/unified-trading-pm/scripts/quality-gates-base/qg-common.sh` → **2**). But
   11 repos still pin `sha256:b7e391f8…` (07-13T18:44, pre-fix) → their in-image QG lacks the ignore → pip-audit fails.
3. **The automation that should have bumped the pins is broken.** PM `.github/workflows/digest-drift-sweep.yml` (cron
   `0 */6 * * *`) authenticates its cross-repo Contents-API reads with `secrets.GITHUB_TOKEN` (`:77`), the ambient
   repo-scoped token, which **cannot read another repo's contents**. Every run (checked 07-14→07-18, incl. 07-18 06:38
   UTC) logs `No ARG found: 16 / Already fresh: 0 / Dispatched: 0` — all 16 `IMAGE_REPOS` hit "Dockerfile not found —
   skipping" at the always-failing fetch (`:138-151`). Its last real dispatch to ml-service was 2026-06-28; nothing
   since. Every other cross-repo call in this codebase (UTL `clone-pm-scripts`, `update-repo-version.yml`) uses a real
   cross-repo `GH_PAT`.

## Blast radius (11 repos pinned to stale `b7e391f8`, all will fail identically)

`agent-orchestrator`, `alerting-service`, `client-reporting-api`, `deployment-service`, `execution-service`,
`fund-administration-service`, `greeks-service`, `market-data-processing-service`, `ml-service` (now unblocked),
`strategy-service`, `trading-agent-service`. (`deployment-api` `e5de3b29` and `batch-live-reconciliation-service`
`9594091a` are on post-fix digests → likely unaffected; `features-service`/`instruments-service`/`mtds` on distinct
digests — re-verify at their next deploy.)

**Bucket-fold impact**: Folds C+D (execution-service + strategy-service) and any deployment-service redeploy will hit
the SAME wall at their Phase-D redeploy. Mitigation for each: bump that repo's `BASE_IMAGE_DIGEST` to `sha256:76a15429…`
(or the then-current fresh base) and ship via quickmerge → promote, exactly as done for ml-service.

## Recommended fix (operator decision — options)

A: **Fix the sweep token + backfill the 10 stale pins** — swap `secrets.GITHUB_TOKEN` → a cross-repo `GH_PAT` in
`digest-drift-sweep.yml:77` (matches `update-repo-version.yml`), re-run the sweep; it then auto-bumps every stale pin.
One-line workflow fix + one sweep run fixes the whole fleet and prevents recurrence. **[REC]** B: Manually bump each of
the 10 stale repos' `BASE_IMAGE_DIGEST` (as done for ml-service) — unblocks them now but leaves the sweep broken →
recurs on the next base-image republish. C: Both — A for durability + B for the repos needing a deploy before the next
sweep cycle.

Not fixed autonomously in this session: the token fix is a fleet CI-workflow change outside the bucket-fold dispatch
(rule-11 blast-radius: a shared-workflow change wants its own verify pass across the fleet). Bucket-fold Phase-D
redeploys handle their own repo's pin inline as they are reached.

## Addendum 2026-07-23 — richer diagnosis of the SAME drift the 07-22 correction above already caught + fixed

Found independently while building the `/ops/artifacts` observability page
(`artifact_pipeline_observability_2026_07_17.md`), unaware of this doc until writing this addendum. **On reconstruction,
this is almost certainly the SAME incident the 🟡 2026-07-22 severity-correction note above already fixed**
(`deployment-api@2531d925`, digest `2854ae3d…`→`4edb1d8c…`) — my finding's timestamps (07-21 14:19–15:09 UTC) precede
that note's fix, and the build that finally went green (`1e12246`, 07-23T05:06:47 UTC) is consistent with that bump
reaching the deploy trigger. Recorded here as corroborating detail with the EXACT symptom + root cause, not as a new
open incident:

**What happened**: `deployment-api` commit `ecbe30c` (2026-07-21) added a `run.log`-viewer feature importing
`gcs_read_object_range` from `unified_trading_library`. That symbol landed in UTL source at **13:12 UTC** the same day
(`unified-trading-library@e22e40f1`, exported from `__init__.py`). Both `deployment-api-main-deploy` builds that
followed (14:19 and 15:06 UTC — same commit, re-triggered because the branch-based deploy fire has no
already-failed-this-SHA guard, so it kept rebuilding the stuck commit) failed identically at the operability-probe step:
`ImportError: cannot import name 'gcs_read_object_range' from 'unified_trading_library'`. The image's baked-in UTL was
older than 13:12 — i.e. `deployment-api`'s pinned base-image digest was stale relative to UTL HEAD, the exact failure
mode this doc describes, just triggered by a missing symbol instead of the pip-audit ignore-list gap.

**The genuinely open question, NOT resolved by either note**: `digest-drift-sweep.yml` already uses `GH_PAT` (commit
`f6e98bbdd`, **2026-07-18 11:51:54**, same day as this doc, citing this issue's diagnosis) and `deployment-api` IS in
its `IMAGE_REPOS` list (`:97`) — Option A (the durable fix) had ALREADY landed, and `deployment-api` was in scope, THREE
DAYS before it drifted again on `ecbe30c`. Both the 07-22 note's fix and this addendum's confirmation are manual re-pins
(Option B) — a point-fix, not evidence the sweep is actually preventing drift. Unchecked candidates for why an in-scope,
auth-fixed sweep didn't catch this: its actual run history/dispatch log for `deployment-api` around 07-18→21 (did it
fire? find an `ARG` to bump?); whether `BASE_IMAGE_DIGEST` is set via a Dockerfile `ARG` the sweep's regex can find, or
a Cloud Build trigger substitution it can't see; whether it bumps on every UTL republish or a cadence slower than
`e22e40f1`→`ecbe30c`'s same-day gap. Next session: read the sweep's own run logs before re-diagnosing from scratch, and
check whether `deployment-api` has drifted a THIRD time since — if so, Option A is confirmed not actually working
despite landing.

**One more unverified observation, worth a look, not chased down here**: the live Deploy timeline data (same
`/ops/artifacts` session) showed **`deployment-service`, `trading-agent-service`, `batch-live-reconciliation-service`,
and `fund-administration-service` all failing to deploy within the same ~3-minute window, 2026-07-22 ~04:08–04:10 UTC**
— all four are in THIS doc's original blast-radius list. Could be the same digest-drift class hitting several repos at
once (a scheduled/fleet-wide redeploy sweep landing on a shared stale pin), or could be unrelated. Not investigated —
flagging the timestamp cluster so it isn't lost; `gcp_cloud_run_revisions` /
`/api/artifacts/deploys?days=30&change=fail` is the fastest way to re-pull it.
